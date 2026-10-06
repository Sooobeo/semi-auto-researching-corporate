"""Offline, manifest-driven P01 QA. Never fetches URLs or prints source bodies.

Empty corpora validate metadata only. Unexercised content checks are reported
explicitly; this agent check cannot satisfy the human audit/annotation gates.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
VERSION = "us-p01-offline-verify-0.1.0"
RIGHTS = ["manual_read", "automated_access", "storage_policy", "internal_analysis_policy",
          "ai_input_policy", "ai_training_policy", "external_transfer_policy", "sharing_policy",
          "redistribution_policy"]
RIGHT_VALUES = {"allowed", "conditional", "prohibited", "unresolved"}
NETWORK_ERROR = {"network_error"}
TRUE = {True, "True", "true", "1"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        if any(None in row for row in rows):
            raise ValueError("CSV row has more fields than its header")
        return reader.fieldnames or [], rows


def read_jsonl(path):
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            raise ValueError(f"Blank JSONL line {number}")
        obj = json.loads(line)
        if not isinstance(obj, dict):
            raise ValueError(f"JSONL line {number} is not an object")
        rows.append(obj)
    return rows


def dateparse(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def network_attempted(row, key="access_status"):
    return bool(row.get("http_status")) or row.get(key) in NETWORK_ERROR


def local_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to((ROOT / "artifacts/us_equity").resolve()):
        raise ValueError("Stored source path leaves the active US artifact directory")
    return path


def ignored(path):
    result = subprocess.run(["git", "check-ignore", "--quiet", str(path)], cwd=ROOT,
                            capture_output=True, text=True)
    return result.returncode == 0


def pointer_get(obj, pointer):
    if pointer == "":
        return obj
    if not pointer.startswith("/"):
        raise ValueError("JSON pointer is not RFC 6901 absolute syntax")
    for part in pointer[1:].split("/"):
        part = part.replace("~1", "/").replace("~0", "~")
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


class Audit:
    def __init__(self):
        self.checks = []

    def check(self, name, errors=(), tested=None, note=None):
        errors = list(errors)
        status = "failed" if errors else "not_exercised" if tested == 0 else "passed"
        entry = {"check": name, "status": status, "tested_records": tested,
                 "findings": errors}
        if note:
            entry["note"] = note
        self.checks.append(entry)


def unique(rows, key):
    ids = [row.get(key) for row in rows]
    return [f"Missing or duplicate {key}"] if any(not value for value in ids) or len(ids) != len(set(ids)) else []


def verify(args):
    target = (ROOT / (args.manifest or args.manifest_dir)).resolve()
    run_dir = target.parent if args.manifest else target
    if args.manifest and (target.name != "api_payload_manifest.csv" or not target.is_file()):
        raise ValueError("--manifest must point to an existing api_payload_manifest.csv")
    if not run_dir.is_relative_to((ROOT / "artifacts/us_equity").resolve()):
        raise ValueError("Manifest directory must be inside artifacts/us_equity")
    registry_path = (ROOT / args.source_registry).resolve()
    audit = Audit()
    inventory, tables, jsonls, objects = [], {}, {}, {}
    files = list(run_dir.glob("*.csv")) + list(run_dir.glob("*.jsonl")) + list(run_dir.glob("*.json"))
    for path in sorted(files):
        item = {"path": path.relative_to(ROOT).as_posix(), "sha256": sha(path.read_bytes()),
                "bytes": path.stat().st_size, "format": path.suffix.lstrip(".")}
        try:
            if path.suffix == ".csv":
                headers, rows = read_csv(path)
                tables[path.name] = rows
                item.update(rows=len(rows), headers=headers)
            elif path.suffix == ".jsonl":
                rows = read_jsonl(path)
                jsonls[path.name] = rows
                item["rows"] = len(rows)
            else:
                obj = json.loads(path.read_text(encoding="utf-8-sig"))
                objects[path.name] = obj
                item["items"] = len(obj) if isinstance(obj, list) else None
            item["parse_status"] = "passed"
        except (ValueError, UnicodeError) as error:
            item["parse_status"] = "failed"
            item["error"] = str(error)
        inventory.append(item)
    required = {"api_payload_manifest.csv", "access_trials.csv", "entities.csv", "document_manifest.csv",
                "parser_trials.csv", "extraction_audit.csv", "robots_trials.csv", "blocks.jsonl",
                "observations.jsonl", "selected_filings.json", "summary.json", "run_manifest.json"}
    names = {Path(item["path"]).name for item in inventory}
    audit.check("artifact_parse_and_required_inventory",
                [f"Missing {name}" for name in sorted(required - names)] +
                [f"Parse failure: {item['path']}" for item in inventory if item["parse_status"] == "failed"],
                len(inventory))
    headers, sources = read_csv(registry_path)
    source_map = {row["source_id"]: row for row in sources}
    registry_errors = unique(sources, "source_id")
    for source in sources:
        for field in RIGHTS:
            if source.get(field) not in RIGHT_VALUES:
                registry_errors.append(f"{source['source_id']}: invalid/missing {field}")
        if not source.get("terms_url") or not source.get("checked_at"):
            registry_errors.append(f"{source['source_id']}: policy reference/date missing")
        if source.get("status") in {"unresolved", "conditional"} and not source.get("unresolved_reason"):
            registry_errors.append(f"{source['source_id']}: unresolved reason missing")
    audit.check("source_registry_independent_rights_fields", registry_errors, len(sources))
    inventory.append({"path": registry_path.relative_to(ROOT).as_posix(), "format": "csv",
                      "sha256": sha(registry_path.read_bytes()), "rows": len(sources), "headers": headers,
                      "bytes": registry_path.stat().st_size, "parse_status": "passed"})
    p0_table_errors, supporting_tables = [], {}
    for path in sorted(run_dir.parent.glob("*.csv")):
        if path == registry_path:
            continue
        try:
            header, rows = read_csv(path)
            supporting_tables[path.name] = rows
            inventory.append({"path": path.relative_to(ROOT).as_posix(), "format": "csv",
                              "sha256": sha(path.read_bytes()), "rows": len(rows), "headers": header,
                              "bytes": path.stat().st_size, "parse_status": "passed"})
        except (ValueError, UnicodeError) as error:
            p0_table_errors.append(f"{path.name}: {type(error).__name__}")
    audit.check("p0_supporting_csv_inventory_parse", p0_table_errors,
                sum(Path(item["path"]).parent == run_dir.parent.relative_to(ROOT) for item in inventory))
    api = tables.get("api_payload_manifest.csv", [])
    docs = tables.get("document_manifest.csv", [])
    trials = tables.get("access_trials.csv", [])
    parsers = tables.get("parser_trials.csv", [])
    robots = tables.get("robots_trials.csv", [])
    entities = tables.get("entities.csv", [])
    observations = jsonls.get("observations.jsonl", [])
    blocks = jsonls.get("blocks.jsonl", [])
    run = objects.get("run_manifest.json", {})
    summary = objects.get("summary.json", {})
    apimap = {row.get("resource_id"): row for row in api}
    docmap = {row.get("doc_id"): row for row in docs}
    entitymap = {row.get("company_id"): row for row in entities}
    blockmap = {row.get("block_id"): row for row in blocks}
    supporting_errors = []
    for filename, rows in supporting_tables.items():
        for row in rows:
            if row.get("source_id") and row["source_id"] not in source_map:
                supporting_errors.append(f"{filename}: unknown source_id")
            if row.get("company_id") and row["company_id"] not in entitymap:
                supporting_errors.append(f"{filename}: unknown candidate company_id")
            if row.get("coverage_status") in {"not_tested", "held_rights_review"} and not row.get("reason"):
                supporting_errors.append(f"{filename}: hold/not-tested reason missing")
    audit.check("supporting_table_source_and_candidate_company_foreign_keys", supporting_errors,
                sum(len(rows) for rows in supporting_tables.values()))
    ids = unique(api, "resource_id") + unique(docs, "doc_id") + unique(trials, "trial_id")
    ids += unique(entities, "company_id") + unique(observations, "observation_id") + unique(blocks, "block_id")
    for row in api + docs:
        key = row.get("resource_id") or row.get("doc_id")
        source = source_map.get(row.get("source_id"))
        if not source:
            ids.append(f"{key}: unknown source_id")
            continue
        refs = {source.get("terms_url")} | set(source.get("evidence_urls", "").split("|"))
        if row.get("rights_basis_ref") not in refs:
            ids.append(f"{key}: rights_basis_ref not linked to registry evidence")
        if row.get("company_id") not in entitymap:
            ids.append(f"{key}: unknown candidate company_id")
        if row.get("storage_uri") and any(source.get(field) not in {"allowed", "conditional"}
                                          for field in ["automated_access", "storage_policy", "internal_analysis_policy"]):
            ids.append(f"{key}: source bytes stored while registry access/storage/analysis policy is held")
    for trial in trials:
        target = apimap if trial.get("resource_kind") == "api_payload" else docmap
        row = target.get(trial.get("resource_id"))
        if not row:
            ids.append(f"{trial.get('trial_id')}: unknown resource foreign key")
        elif row.get("access_status") != trial.get("status") or row.get("http_status", "") != trial.get("http_status", ""):
            ids.append(f"{trial.get('trial_id')}: status does not match manifest")
    for block in blocks:
        if block.get("doc_id") not in apimap and block.get("doc_id") not in docmap:
            ids.append(f"{block.get('block_id')}: unknown source document/resource")
    for obs in observations:
        if obs.get("doc_id") not in docmap or obs.get("source_resource_id") not in apimap:
            ids.append(f"{obs.get('observation_id')}: unknown filing/API foreign key")
        for evidence in obs.get("evidence", []):
            if evidence.get("block_id") not in blockmap:
                ids.append(f"{obs.get('observation_id')}: unknown evidence block")
    audit.check("unique_ids_and_source_rights_foreign_keys", ids, len(api) + len(docs) + len(trials) + len(blocks) + len(observations))
    stored = [row for row in api + docs if row.get("storage_uri")]
    hashes, payloads = [], {}
    for row in stored:
        key = row.get("resource_id") or row.get("doc_id")
        try:
            path = local_path(row["storage_uri"])
            data = path.read_bytes()
            if not ignored(path):
                hashes.append(f"{key}: raw source is not Git ignored")
            if sha(data) != row.get("sha256") or len(data) != int(row.get("byte_size") or -1):
                hashes.append(f"{key}: hash/size does not match stored bytes")
            if not row.get("revision_id"):
                hashes.append(f"{key}: stored revision ID missing")
            if key in apimap:
                payloads[key] = json.loads(data)
        except (ValueError, OSError) as error:
            hashes.append(f"{key}: stored object invalid ({type(error).__name__})")
    audit.check("stored_bytes_hash_revision_and_ignored_path", hashes, len(stored))
    sentinel = ROOT / "artifacts/us_equity/p0/raw/offline-qa-sentinel.json"
    ignored_errors = [] if ignored(sentinel) else ["US raw path is not ignored"]
    if (run_dir / "blocks.jsonl").exists() and not ignored(run_dir / "blocks.jsonl"):
        ignored_errors.append("Source blocks path is not ignored")
    audit.check("raw_and_blocks_git_exclusion_rules", ignored_errors, 2)
    failure_errors = []
    for row in api + docs:
        key = row.get("resource_id") or row.get("doc_id")
        status = row.get("access_status")
        if not status:
            failure_errors.append(f"{key}: empty access status hides untested/failed state")
        if not row.get("storage_uri") and any(row.get(k) for k in ["sha256", "revision_id", "byte_size"]):
            failure_errors.append(f"{key}: invented storage metadata without source bytes")
        if status in {"robots_denied_or_unresolved", "host_blocked_after_403_or_429", "blocked_unattempted",
                      "held_by_source_registry_host_block"} or str(status).startswith("source_policy_"):
            if row.get("http_status") or row.get("sha256"):
                failure_errors.append(f"{key}: blocked unattempted candidate reported as endpoint request/download")
        if row.get("published_at") and row.get("time_precision") in {"date", "date_only", "unknown"}:
            failure_errors.append(f"{key}: exact timestamp manufactured from date/unknown precision")
        if row.get("http_status"):
            try:
                if not 100 <= int(row["http_status"]) <= 599:
                    raise ValueError()
            except ValueError:
                failure_errors.append(f"{key}: invalid HTTP status; missing must remain empty with reason")
        try:
            if dateparse(row["observed_at"]).tzinfo is None:
                failure_errors.append(f"{key}: observed time lacks UTC offset")
        except (KeyError, ValueError, TypeError):
            failure_errors.append(f"{key}: observed timestamp missing/invalid")
    for parser in parsers:
        if parser.get("attempted") in TRUE and parser.get("resource_id") not in payloads:
            failure_errors.append(f"{parser.get('resource_id')}: extraction attempt claims absent payload")
    for trial in trials:
        if trial.get("original_filing_body_read") in TRUE:
            failure_errors.append(f"{trial.get('trial_id')}: human original-body read lacks audit record in this verifier's contract")
    audit.check("failed_or_unattempted_states_not_hidden_as_success", failure_errors, len(api) + len(docs) + len(parsers))
    actual = {"api_resources_selected": len(api), "api_resources_network_attempted": sum(network_attempted(row) for row in api),
              "api_resources_valid_json": sum(row.get("access_status") == "valid_json_payload" for row in api),
              "filing_candidates": len(docs), "filing_network_attempted": sum(network_attempted(row) for row in docs),
              "filing_downloaded": sum(bool(row.get("sha256")) for row in docs),
              "filing_body_manual_audited": 0, "complete_filing_bodies_verified": 0,
              "structured_observations": len(observations), "business_relations_verified": 0,
              "news_article_candidates": 0, "news_article_bodies_verified": 0,
              "independent_reporting_expressions": 0, "comparable_cross_outlet_pairs": 0,
              "ai_original_text_input_calls": 0, "llm_training_runs": 0}
    counts = [f"{field}: expected {value}, reported {summary.get(field)!r}" for field, value in actual.items() if summary.get(field) != value]
    if run.get("summary") != summary:
        counts.append("Embedded run summary differs from summary.json")
    if len(objects.get("selected_filings.json", [])) != len(docs):
        counts.append("selected_filings count differs from document manifest")
    audit.check("manifest_recomputed_counts_separate_api_and_filings", counts, len(actual))
    network = {"robots_log_rows": len(robots),
               "robots_actual_network_attempts_in_run": sum(network_attempted(row, "status") for row in robots),
               "robots_prior_evidence_hosts": run.get("blocked_hosts_from_prior_evidence", []),
               "api_endpoint_network_attempts": actual["api_resources_network_attempted"],
               "filing_endpoint_network_attempts": actual["filing_network_attempted"]}
    policy_probes = supporting_tables.get("network_probe_trials.csv", [])
    probe_errors = []
    if policy_probes:
        try:
            network["policy_probe_actual_requests_all_recorded_evidence"] = sum(int(row["request_count"]) for row in policy_probes)
            network["policy_probe_http403_rows"] = sum(row.get("http_status") == "403" for row in policy_probes)
            network["policy_probe_retries"] = sum(int(row["retry_count"]) for row in policy_probes)
            network["probe_timestamp_unknown_rows"] = sum(not row.get("observed_at") for row in policy_probes)
            for row in policy_probes:
                if row.get("http_status") in {"403", "429"} and (int(row["retry_count"]) or int(row["endpoint_requests_after_failure"])):
                    probe_errors.append(f"{row.get('trial_id')}: requests after host denial")
                if not row.get("observed_at") and row.get("observation_precision") != "run_trace_only":
                    probe_errors.append(f"{row.get('trial_id')}: missing timestamp precision/reason")
        except (ValueError, KeyError):
            probe_errors.append("Policy probe count is malformed/missing")
    audit.check("policy_probe_denial_stop_and_request_denominators", probe_errors, len(policy_probes),
                "Historical probes are distinct from this run's endpoint requests; unknown probe timestamp retained.")
    legacy_errors = []
    if run.get("legacy_inputs") != []:
        legacy_errors.append("Run legacy_inputs is nonempty or unspecified")
    if run.get("ai_processing") != "none":
        legacy_errors.append("Raw AI processing requires a different verified contract")
    for row in api + docs + blocks + observations:
        if row.get("storage_uri") and not str(row["storage_uri"]).replace("\\", "/").startswith("artifacts/us_equity/"):
            legacy_errors.append("Stored input references a legacy/non-US artifact")
        if row.get("company_id") and not str(row["company_id"]).startswith("US-"):
            legacy_errors.append("Non-US internal company ID used")
    audit.check("legacy_exclusion_and_raw_ai_hold", legacy_errors, len(api) + len(docs) + len(observations))
    pointers, spans, numbers = [], [], []
    for obs in observations:
        key = obs["observation_id"]
        try:
            payload = payloads[obs["source_resource_id"]]
            for evidence in obs.get("evidence", []):
                block = blockmap[evidence["block_id"]]
                fact = pointer_get(payload, evidence["source_json_pointer"])
                if json.loads(block["raw_text"]) != fact:
                    pointers.append(f"{key}: pointer and block differ")
                start, end, text = evidence["start"], evidence["end"], block["raw_text"]
                if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start <= end <= len(text):
                    spans.append(f"{key}: invalid code-point half-open boundaries")
                elif text[start:end] != block["normalized_text"] or block.get("offset_mapping") != "identity_unicode_code_point_0_based_half_open":
                    spans.append(f"{key}: identity round-trip mismatch/unimplemented normalization mapping")
                if Decimal(obs["numeric_value"]) != Decimal(str(fact["val"])):
                    numbers.append(f"{key}: numeric value differs from API fact")
                if obs.get("period_start") != fact.get("start") or obs.get("period_end") != fact.get("end") or obs.get("unit_raw") != "USD":
                    numbers.append(f"{key}: period/unit differs from pointer context")
                if obs.get("scope_id") != obs.get("company_id", "") + "-CONSOLIDATED":
                    numbers.append(f"{key}: API entity-wide scope was changed")
            if obs.get("numeric_value") is None and not obs.get("missing_reason"):
                numbers.append(f"{key}: null numeric without missing_reason")
            if obs.get("numeric_value") is not None and obs.get("missing_reason"):
                numbers.append(f"{key}: present numeric has contradictory missing_reason")
        except (KeyError, TypeError, ValueError, InvalidOperation):
            pointers.append(f"{key}: source pointer/value unavailable or malformed")
    audit.check("json_pointer_source_round_trip", pointers, len(observations))
    audit.check("unicode_code_point_offsets_and_normalization_round_trip", spans, len(observations))
    audit.check("structured_numbers_units_periods_scope_and_nulls", numbers, len(observations),
                "Structured API checks do not replace original filing table/header audit.")
    for name in ["original_filing_body_completeness", "filing_table_headers_and_scope_manual_audit",
                 "fiscal_vs_calendar_and_period_length_comparability", "duplicate_recollection_and_follow_up_examples",
                 "human_independent_annotation_and_handoff"]:
        audit.check(name, tested=0, note="No source specimen or independent human audit supplied; not passed.")
    provenance = []
    script = ROOT / "scripts/p01_us_sec_pilot.py"
    if script.exists() and run.get("script_sha256") != sha(script.read_bytes()):
        provenance.append("Collector has changed since this run; recorded execution hash retained, original byte-identical source reproduction not established.")
    if not run.get("code_revision") or not run.get("script_sha256") or not (run.get("companies_config_sha256") or run.get("input_manifest_hash")):
        provenance.append("Run source/input version metadata incomplete.")
    if run.get("source_registry_sha256") and run["source_registry_sha256"] != sha(registry_path.read_bytes()):
        provenance.append("Source registry has changed since the executed run; exact policy input reproduction not established.")
    if run.get("companies_config_sha256") and script.exists():
        tree = ast.parse(script.read_text(encoding="utf-8"))
        config = next((ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                       and any(isinstance(name, ast.Name) and name.id == "COMPANIES" for name in node.targets)), None)
        if config is None or sha(json.dumps(config).encode()) != run["companies_config_sha256"]:
            provenance.append("Company input config does not match the recorded hash.")
    try:
        if dateparse(run["completed_at"]) < dateparse(run["started_at"]):
            provenance.append("Completion precedes start")
    except (KeyError, ValueError, TypeError):
        provenance.append("Run timestamps malformed/missing")
    audit.check("run_versions_and_timestamp_order", [x for x in provenance if not x.startswith("Collector has changed")], 1)
    report = {"verifier_version": VERSION, "verified_at": datetime.now(timezone.utc).isoformat(),
              "manifest_directory": run_dir.relative_to(ROOT).as_posix(), "review_kind": "independent_agent_offline_reproduction_not_human_audit",
              "run_id": run.get("run_id"), "counts": actual, "network_denominators": network,
              "rates": {"api_endpoint_access": {"numerator": actual["api_resources_valid_json"], "denominator": actual["api_resources_network_attempted"], "rate": None if not actual["api_resources_network_attempted"] else actual["api_resources_valid_json"] / actual["api_resources_network_attempted"]},
                        "filing_body_access": {"numerator": 0, "denominator": actual["filing_network_attempted"], "rate": None},
                        "automatic_text_extraction": {"numerator": 0, "denominator": 0, "rate": None}},
              "artifact_inventory": inventory, "checks": audit.checks, "provenance_notes": provenance,
              "human_phase_completion": "not_established",
              "overall_status": "failed" if any(c["status"] == "failed" for c in audit.checks) else "metadata_valid_content_not_exercised" if not observations and not stored else "offline_checks_valid_human_audit_pending"}
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--manifest-dir")
    target.add_argument("--manifest")
    parser.add_argument("--source-registry", default="artifacts/us_equity/p0/source_registry.csv")
    parser.add_argument("--output", "--report", dest="output", default="artifacts/us_equity/p0/validation_report.json")
    args = parser.parse_args()
    report = verify(args)
    output = (ROOT / args.output).resolve()
    if not output.is_relative_to((ROOT / "artifacts/us_equity").resolve()):
        raise ValueError("Report output must remain within US artifacts")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"overall_status": report["overall_status"], "counts": report["counts"],
                      "check_status_counts": {status: sum(c["status"] == status for c in report["checks"]) for status in ["passed", "failed", "not_exercised"]},
                      "report": output.relative_to(ROOT).as_posix()}, ensure_ascii=False))
    raise SystemExit(1 if report["overall_status"] == "failed" else 0)


if __name__ == "__main__":
    main()
