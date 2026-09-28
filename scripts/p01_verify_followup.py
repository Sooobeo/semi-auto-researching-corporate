"""Read-only P01 follow-up integrity checks, writing one new validation report."""
import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime, timezone


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def main(folder, output):
    if output.exists():
        raise ValueError("validation_output_must_be_new")
    baseline = load(folder / "baseline.json")
    manifest = load(folder / "run_manifest.json")
    checks, details = {}, {}
    checks["previous_120_output_and_code_hashes_unchanged"] = all(sha(Path(item["path"])) == item["sha256"] for item in baseline["protected_inputs"])
    checks["run_script_hashes_match"] = all(sha(Path(item["path"])) == item["sha256"] for item in manifest["scripts"])
    inventory = load(folder / "p01_inventory/summary.json")
    checks["official_evidence_integrity"] = inventory["integrity_error_count"] == 0 and inventory["metadata_files_unchanged"]
    checks["both_company_quarter_coverage_and_numeric_pairs"] = inventory["quarter_slots"] == inventory["quarter_slots_with_both_documents"] == 20 and inventory["numeric_pairs_recalculated"] == inventory["numeric_pairs_passed"] == 20
    body = load(folder / "extraction_review_001/summary.json")
    morph = load(folder / "morphology_001/summary.json")
    claim = load(folder / "claim_diagnostics_002/summary.json")
    meta = load(folder / "metadata_review_001/summary.json")
    integrated = folder / manifest["final_outputs"]["integrated"]
    document_rows = rows(integrated / "document_review_index.csv")
    pair_rows = rows(integrated / "pair_review_index.csv")
    task_rows = rows(integrated / "task_status.csv")
    checks["22_document_pipeline_count_agreement"] = len(document_rows) == body["documents_reviewed"] == morph["documents"] == claim["documents"] == 22
    checks["48_comparison_candidate_count_agreement"] = len(pair_rows) == claim["alignment_candidates"] == 48
    checks["document_and_pair_ids_unique"] = len({r["doc_id"] for r in document_rows}) == len(document_rows) and len({r["alignment_id"] for r in pair_rows}) == len(pair_rows)
    checks["all_pair_document_references_exist"] = all(r[side + "_doc_id"] in {x["doc_id"] for x in document_rows} for r in pair_rows for side in ("left", "right"))
    checks["integrated_boundary_difference_recomputed"] = sum(not(r["left_boundary_agrees"] == "True" and r["right_boundary_agrees"] == "True") for r in pair_rows) == load(integrated / "summary.json")["alignment_candidates_with_boundary_disagreement"]
    checks["no_automatic_claim_or_human_confirmation"] = not any(r["claim_alignment_ready"] == "True" for r in pair_rows) and claim["verified_claim_alignments"] == 0 and morph["human_reviewed_sentences"] == 0
    checks["morphology_body_nonspace_coverage"] = morph["uncovered_nonspace_characters"] == 0
    missing_evidence = []
    for task in task_rows:
        for evidence in task["evidence"].split(";"):
            if not (integrated / evidence).exists():
                missing_evidence.append({"task_id": task["task_id"], "path": evidence})
    checks["task_evidence_links_resolve"] = not missing_evidence
    details["missing_task_evidence"] = missing_evidence
    checks["inventory_summary_points_to_inventory"] = any("../p01_inventory/summary.json" in r["evidence"] for r in task_rows)
    missing_links = []
    permitted_pending = {output.resolve(), (folder / "artifact_checksums.csv").resolve()}
    for doc in [folder / "briefing.md", folder / "handoff_p0.md", folder.parent / "handoff_p0.md"]:
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            if target.startswith(("https:", "http:", "#")):
                continue
            local = (doc.parent / target.split("#")[0]).resolve()
            if not local.exists() and local not in permitted_pending:
                missing_links.append({"document": str(doc), "target": target})
    checks["briefing_handoff_links_resolve"] = not missing_links
    details["missing_document_links"] = missing_links
    raw_paths = [p.as_posix() for p in folder.rglob("*") if p.is_file() and "raw" in p.relative_to(folder).parts]
    ignored = subprocess.run(["git", "check-ignore", "-z", "--stdin"], input=b"\0".join(path.encode("utf-8") for path in raw_paths) + b"\0", capture_output=True, check=False)
    ignored_set = {part.decode("utf-8") for part in ignored.stdout.split(b"\0") if part}
    tracked = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True)
    tracked_set = {part.decode("utf-8") for part in tracked.stdout.split(b"\0") if part}
    checks["all_followup_raw_gitignored"] = set(raw_paths) == ignored_set
    checks["no_followup_raw_tracked"] = not set(raw_paths) & tracked_set
    checks["git_diff_check"] = subprocess.run(["git", "diff", "--check"], capture_output=True).returncode == 0
    details["raw_files_gitchecked"] = len(raw_paths)
    details["metadata_summary_sha256"] = sha(folder / "metadata_review_001/summary.json")
    qa_reports = {}
    for name in manifest["validation_reports"]:
        result = load(folder / name)
        status = result.get("result", result.get("status", result.get("integrity_pass")))
        # Reports use either an overall pass or a list/dictionary of booleans.
        if status in ("pass", "passed", True):
            passed = True
        elif name == manifest["final_outputs"]["image_ocr"] + "/validation.json":
            passed = (result.get("errors") == [] and result.get("source_hashes_unchanged") is True
                      and result.get("all_private_artifacts_git_ignored") is True
                      and result.get("distinct_pages") == result.get("selected_variant_rows") == result.get("selected_nonempty_pages") == 31)
        elif isinstance(result.get("checks"), dict):
            passed = bool(result["checks"]) and all(value is True for value in result["checks"].values())
        else:
            passed = result.get("passed") is True
        qa_reports[name] = {"pass": passed, "sha256": sha(folder / name), "recorded_status": status}
    checks["final_component_validation_reports_pass"] = all(v["pass"] for v in qa_reports.values())
    result = {"version": "p01-followup-final-verifier/0.1", "validated_at": datetime.now(timezone.utc).isoformat(),
              "script_sha256": sha(Path(__file__)), "integrity_pass": all(checks.values()), "checks": checks,
              "details": details, "component_validation_reports": qa_reports,
              "scope": "provenance, count agreement, file references and preservation; no semantic accuracy or human-gold claim",
              "new_network_requests": 0}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"integrity_pass": result["integrity_pass"], "checks": len(checks), "failed_checks": [k for k, v in checks.items() if not v]}, ensure_ascii=True))
    if not result["integrity_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.run_dir, args.output)
