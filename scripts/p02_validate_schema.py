"""P02 structural and semantic contract verification; never certifies gold.

Install jsonschema in an isolated environment and execute from any cwd.
Actual evidence round-trip requires --blocks, and source rights require human review.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.metadata
import json
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "artifacts" / "us_equity" / "p1"


def semantic_errors(record, blocks):
    errors = []
    norm = record.get("normalized", {})
    provenance = record.get("provenance", {})
    synthetic = record.get("example_kind") == "synthetic"
    reasons = norm.get("field_missing_reasons", {})
    for path in reasons:
        cursor = record.get("raw", {}) if path.startswith("raw.") else norm
        keys = path.split(".")[1:] if path.startswith("raw.") else path.split(".")
        for key in keys:
            cursor = cursor.get(key) if isinstance(cursor, dict) else None
        if cursor is not None and cursor != "unknown" and cursor != "not_applicable":
            errors.append(f"{path}: missing reason attached to a present value")
    for key in ["company_id", "scope_id"]:
        if norm.get(key) is None and key not in reasons:
            errors.append(f"{key}: null without explicit missing reason")
    if provenance.get("rights_check_status") == "unresolved" and record.get("raw", {}).get("claim_text"):
        errors.append("raw.claim_text: body must not be copied with unresolved rights")
    if provenance.get("rights_check_status") == "unresolved":
        if any(evidence.get("selected_text") for evidence in provenance.get("evidence", [])):
            errors.append("evidence.selected_text: excerpt must not be copied with unresolved rights")
        if record.get("raw", {}).get("action_raw"):
            errors.append("raw.action_raw: body-derived expression must not be copied with unresolved rights")
    for evidence in provenance.get("evidence", []):
        if evidence.get("doc_id") != provenance.get("doc_id") or evidence.get("revision_id") != provenance.get("revision_id"):
            errors.append("evidence document/revision mismatch")
        start, end = evidence.get("start"), evidence.get("end")
        if (start is None) != (end is None):
            errors.append("span endpoints must both be null or both be integers")
        if evidence.get("location_status") in {"unlocated", "unverified"} and start is not None:
            errors.append("unverified/unlocated evidence cannot assert verified offsets")
        if start is not None:
            if start > end:
                errors.append("span end before start")
            block = blocks.get(evidence.get("block_id"))
            surface = record.get("raw", {}).get("claim_text") if synthetic else (block or {}).get("raw_text")
            if surface is not None:
                if end > len(surface) or surface[start:end] != evidence.get("selected_text"):
                    errors.append("Unicode code-point span round-trip mismatch")
            elif evidence.get("location_status") == "verified":
                errors.append("verified source span cannot be checked without original block")
        if evidence.get("location_type") == "table_cell" and not evidence.get("header_refs"):
            errors.append("table evidence lacks unit/period/scope header refs")
        if not synthetic and evidence.get("location_status") == "synthetic":
            errors.append("source-supported record has synthetic location")
    temporal = norm.get("temporal", {})
    if temporal.get("time_precision") == "date" and temporal.get("published_date") is None:
        errors.append("date precision requires published_date")
    if temporal.get("published_at") and temporal.get("published_date"):
        if temporal["published_at"][:10] != temporal["published_date"]:
            errors.append("published_at local date disagrees with published_date")
    for period_key in ["reference_period", "effective_period"]:
        period = temporal.get(period_key, {})
        start, end = period.get("period_start"), period.get("period_end")
        if start and end and start > end:
            errors.append(f"{period_key}: period ends before start")
        if period.get("period_kind") == "instant" and not period.get("as_of_date"):
            errors.append(f"{period_key}: instant balance requires as_of_date")
        if period.get("duration_days") and start and end:
            calculated = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days + 1
            if period["duration_days"] != calculated:
                errors.append(f"{period_key}: duration_days inconsistent with dates")
    if record.get("record_kind") == "event_claim":
        if norm.get("product_id") and norm["product_id"] not in norm.get("entity_refs", []):
            errors.append("product_id missing from entity_refs")
        if norm.get("company_id") and norm["company_id"] not in norm.get("entity_refs", []):
            errors.append("company_id missing from entity_refs")
        if norm.get("event_type") == "financial_result":
            context = norm.get("financial_context", {})
            if context.get("statement_type") == "not_applicable" or context.get("balance_or_flow") == "not_applicable":
                errors.append("financial_result cannot have nonfinancial context")
        if synthetic and record.get("raw", {}).get("action_raw") and record.get("raw", {}).get("claim_text"):
            if record["raw"]["action_raw"] not in record["raw"]["claim_text"]:
                errors.append("synthetic action_raw is not supported by claim_text")
        if norm.get("value_kind") == "range" and norm.get("lower") is not None and norm.get("upper") is not None:
            if Decimal(norm["lower"]) > Decimal(norm["upper"]):
                errors.append("range lower exceeds upper")
        if norm.get("prior_state_status") in {"comparable_prior", "repeated"} and norm.get("prior_claim_id") is None:
            errors.append("comparable/repeated requires actual prior claim ID")
        if norm.get("prior_state_status") in {"prior_not_found", "not_applicable", "not_yet_checked"} and norm.get("prior_claim_id"):
            errors.append("prior status conflicts with populated prior claim ID")
    if record.get("record_kind") == "business_relation":
        for key in ["subject_entity_id", "object_entity_id", "subject_role", "object_role"]:
            if norm.get(key) is None and key not in reasons:
                errors.append(f"{key}: null without explicit missing reason")
        if norm.get("relation_type") == "supplies_to":
            if norm.get("subject_role") != "supplier" or norm.get("object_role") != "customer" or norm.get("direction") != "subject_to_object":
                errors.append("supplies_to requires supplier→customer direction and roles")
    for calc in record.get("derived", []):
        if calc.get("calculation_status") == "computed" and not calc.get("input_refs"):
            errors.append("computed requires input refs")
        if calc.get("calculation_status") == "insufficient_inputs" and not calc.get("missing_inputs"):
            errors.append("insufficient_inputs requires named missing inputs")
    if not synthetic and provenance.get("rights_check_status") == "synthetic":
        errors.append("source-supported record cannot have synthetic rights basis")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, default=DEFAULT / "event_schema_v0.1.json")
    parser.add_argument("--examples", type=Path, default=DEFAULT / "schema_examples.jsonl")
    parser.add_argument("--cases", type=Path, default=DEFAULT / "schema_validation_cases.json")
    parser.add_argument("--blocks", type=Path)
    parser.add_argument("--dependency-path", type=Path)
    parser.add_argument("--report", type=Path, default=DEFAULT / "schema_validation_report.json")
    args = parser.parse_args()
    if args.dependency_path:
        sys.path.insert(0, str(args.dependency_path.resolve()))
    try:
        from jsonschema import Draft202012Validator, FormatChecker
    except ImportError:
        raise SystemExit("jsonschema is required. Install into an isolated environment; no partial verification reported.")
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    blocks = {}
    if args.blocks:
        blocks = {row["block_id"]: row for row in [json.loads(line) for line in args.blocks.read_text(encoding="utf-8").splitlines() if line.strip()]}
    def errors(record):
        structural = [f"{'/'.join(str(p) for p in error.path)}: {error.message}" for error in validator.iter_errors(record)]
        # Do not run arithmetic/semantic routines on ill-typed values.
        return structural or semantic_errors(record, blocks)
    records = [json.loads(line) for line in args.examples.read_text(encoding="utf-8").splitlines() if line.strip()]
    example_results = [{"record_id": record["record_id"], "errors": errors(record)} for record in records]
    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    case_results = []
    for case in cases:
        found = errors(case["record"])
        valid = not found
        case_results.append({"case_id": case["case_id"], "expected_valid": case["expected_valid"], "observed_valid": valid,
                             "passed": valid == case["expected_valid"], "errors": found})
    report = {"checked_at_date": "2026-10-05", "schema_version": schema["properties"]["schema_version"]["const"],
              "schema_sha256": hashlib.sha256(args.schema.read_bytes()).hexdigest(),
              "jsonschema_version": importlib.metadata.version("jsonschema"), "schema_check": "passed",
              "source_supported_examples": sum(r["example_kind"] == "source_supported" for r in records),
              "synthetic_examples": sum(r["example_kind"] == "synthetic" for r in records),
              "examples_valid": sum(not row["errors"] for row in example_results), "examples_total": len(example_results),
              "negative_cases": sum(not row["expected_valid"] for row in case_results),
              "cases_passed": sum(row["passed"] for row in case_results), "cases_total": len(case_results),
              "human_independent_annotations": 0, "gold_events": 0,
              "source_audit_status": "not_performed_by_this_validator", "rights_audit_status": "not_certified_by_this_validator",
              "example_results": example_results, "case_results": case_results,
              "limitations": ["Synthetic regression checks are not empirical English extraction accuracy.", "External IDs and actual rights require P01 registries and source review.", "Human independent pilot and adjudication remain incomplete."]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"example_results", "case_results"}}, ensure_ascii=False))
    if any(row["errors"] for row in example_results) or not all(row["passed"] for row in case_results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
