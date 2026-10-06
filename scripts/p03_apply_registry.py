"""Apply the P03 registry to audited numerical cells, retaining source records.

This creates current retrospective comparisons, not a historical backtest or gold.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from p03_comparability import compare_claims, normalize_amount, numeric

ROOT = Path(__file__).resolve().parents[1]
VERSION = "p03-apply-0.1.1"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csvrows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def jsonrows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def jsonl(path, rows):
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--facts", type=Path, required=True)
    ap.add_argument("--audit", type=Path, required=True)
    ap.add_argument("--registry", type=Path, default=ROOT / "artifacts/us_equity/p2")
    ap.add_argument("--output-dir", type=Path, required=True)
    ap.add_argument("--as-of", default="2026-10-05")
    args = ap.parse_args()
    out = args.output_dir.resolve()
    if not out.is_relative_to((ROOT / "artifacts/us_equity/p2").resolve()) or out.exists():
        raise SystemExit("Use a new output directory inside the active US p2 tree.")
    facts = jsonrows(args.facts)
    audits = {r["claim_id"]: r for r in csvrows(args.audit)}
    metrics = {r["metric_id"]: r for r in csvrows(args.registry / "metric_catalog.csv")}
    occurrences = {r["claim_id"]: r for r in csvrows(args.registry / "metric_occurrences.csv")}
    scope_path = args.facts.parent / "scope_corroboration.json"
    scope = json.loads(scope_path.read_text(encoding="utf-8"))
    claims, conversions = [], []
    for source in facts:
        audit = audits.get(source["claim_id"], {})
        for key in ["value_roundtrip", "number_parsed", "unit_caption_confirmed", "period_header_confirmed", "fiscal_year_header_confirmed"]:
            if audit.get(key, "").lower() != "true":
                raise SystemExit(f"Required source audit {key} not passed: {source['claim_id']}")
        metric = metrics[source["metric_id"]]
        occurrence = occurrences[source["claim_id"]]
        source_scale = source["scale"]
        unit = {"1": "USD", "1000": "USD_thousand", "1000000": "USD_million", "1000000000": "USD_billion"}.get(source_scale)
        if unit is None:
            raise SystemExit("Unregistered source scale")
        conversion = normalize_amount(source["numeric_value"], unit, source["currency"], args.registry / "unit_rules.csv")
        if conversion["calculation_status"] != "computed" or numeric(conversion["output"]) != numeric(source["numeric_value_base_units"]):
            raise SystemExit("Source/base unit normalization does not round-trip")
        conversion.update(claim_id=source["claim_id"], source_scale=source_scale,
                          source_record_ref=args.facts.as_posix() + "#" + source["claim_id"])
        conversions.append(conversion)
        claim = dict(source)
        claim.update(numeric_value=conversion["output"], scale="1", source_scale=source_scale,
                     source_numeric_value=source["numeric_value"], normalization_rule_id=conversion["rule_id"],
                     source_extractor_definition_version=source["definition_version"],
                     definition_version=occurrence["definition_version"],
                     aggregation_behavior=metric["aggregation_behavior"],
                     statement_type=metric["level"], sign_convention=source["sign_policy"],
                     period_kind={"FY": "annual", "Q4": "quarter", "instant": "instant"}[source["period_label"]],
                     scope_level="company" if source["scope_id"].endswith("-CONSOLIDATED") else "reporting_segment",
                     product_id_missing_reason="not_applicable", adjustment_definition=None,
                     denominator=None, registry_version="us-p2-0.1.0",
                     transformation_layer="normalized", exposure_status="adaptation",
                     human_review="waived_by_user_for_progression", available_at=source["published_date"])
        if claim["scope_level"] == "company":
            claim["availability_dependencies"] = [{"record_type": "scope_corroboration",
                "record_id": "US-MSFT-ANNUAL-FY2025-SCOPE-REFERENCE", "source_url": scope["url"],
                "published_date": None, "available_at": scope["observed_at"],
                "observed_at": scope["observed_at"], "availability_basis": "observed_conservative",
                "reason": "Annual report publication date not verified; this supplemental scope evidence is current-only."}]
        else:
            claim["availability_dependencies"] = []
        claims.append(claim)
    pairs = []
    # Financial totals: same kind of Q4/annual/instant at the next fiscal year.
    corporate = [c for c in claims if c["scope_level"] == "company"]
    for new in corporate:
        if new["fiscal_year"] != 2025:
            continue
        prior = next((p for p in corporate if p["fiscal_year"] == 2024
                      and p["metric_id"] == new["metric_id"] and p["period_label"] == new["period_label"]), None)
        if prior:
            pairs.append({"pair_id": "YOY-" + new["metric_id"] + "-" + new["period_label"],
                          "comparison_kind": "yoy", "new": new, "prior": prior})
    segments = [c for c in claims if c["scope_level"] == "reporting_segment"]
    for segment_scope in sorted({c["scope_id"] for c in segments}):
        items = [c for c in segments if c["scope_id"] == segment_scope]
        old = next(c for c in items if "FY2024-Q4-RELEASE" in c["doc_id"])
        current = next(c for c in items if c["fiscal_year"] == 2025)
        revised_prior = next(c for c in items if c["fiscal_year"] == 2024 and "FY2025-Q4-RELEASE" in c["doc_id"])
        pairs += [
            {"pair_id": "SEG-OLD-TO-NEW-" + segment_scope, "comparison_kind": "yoy", "new": current, "prior": old},
            {"pair_id": "SEG-OLD-TO-REVISED-PRIOR-" + segment_scope, "comparison_kind": "same_period", "new": revised_prior, "prior": old},
            {"pair_id": "SEG-ALIGNED-PRESENTATION-" + segment_scope, "comparison_kind": "yoy", "new": current, "prior": revised_prior},
        ]
    results = []
    for pair in pairs:
        result = compare_claims(pair["new"], pair["prior"], pair["comparison_kind"], args.as_of)
        result.update(pair_id=pair["pair_id"], evidence_claim_refs=[pair["new"]["claim_id"], pair["prior"]["claim_id"]],
                      source_supported=True, exposure_status="adaptation", as_of=args.as_of,
                      audit_scope="audited_numeric_cells_not_complete_body_or_independent_gold")
        results.append(result)
    out.mkdir(parents=True)
    jsonl(out / "normalized_claims.jsonl", claims)
    jsonl(out / "unit_conversions.jsonl", conversions)
    jsonl(out / "comparison_inputs.jsonl", pairs)
    jsonl(out / "comparability_results.jsonl", results)
    report = {"version": VERSION, "completed_at": datetime.now(timezone.utc).isoformat(),
              "as_of": args.as_of, "mode": "retrospective_current_only",
              "facts_path": args.facts.as_posix(), "facts_sha256": sha(args.facts),
              "audit_path": args.audit.as_posix(), "audit_sha256": sha(args.audit),
              "metric_catalog_sha256": sha(args.registry / "metric_catalog.csv"),
              "unit_rules_sha256": sha(args.registry / "unit_rules.csv"),
              "occurrences_sha256": sha(args.registry / "metric_occurrences.csv"),
              "scope_corroboration_path": scope_path.as_posix(),
              "scope_corroboration_sha256": sha(scope_path),
              "script_sha256": sha(Path(__file__)),
              "comparability_engine_sha256": sha(Path(__file__).with_name("p03_comparability.py")),
              "normalized_claims": len(claims), "conversions_computed": len(conversions),
              "source_documents_for_numeric_facts": len({c["doc_id"] for c in claims}),
              "numeric_publication_families": len({c["event_family_id"] for c in claims}),
              "comparison_pairs": len(results), "comparison_decisions": dict(Counter(r["decision"] for r in results)),
              "human_records": 0, "human_gate": "waived_by_user_for_progression", "gold_records": 0,
              "source_prose_ai_inputs": 0, "legacy_inputs": [],
              "limitations": ["Supplemental corporate scope evidence is available conservatively from observation in 2026.",
                              "Numeric-cell audit does not certify complete body extraction.",
                              "Same-company retrospective application is not a blind company/sector holdout."]}
    (out / "run_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["normalized_claims", "conversions_computed", "comparison_pairs", "comparison_decisions"]}))


if __name__ == "__main__":
    main()
