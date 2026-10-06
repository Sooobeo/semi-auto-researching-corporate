"""Independent, offline P03 registry and adversarial engine verification.

No network requests or original source text are emitted. Synthetic engine probes
are implementation checks, not source accuracy, human agreement, or gold.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import Counter
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "us-p03-independent-qa-0.1.0"
EMPTY_REFS = {"", "not_applicable", "null", "None"}
TABLES = {
    "metric_catalog.csv": ("metric_id", ["definition", "canonical_unit", "definition_version", "selection_status", "interpretation_limits"]),
    "accounting_concept_catalog.csv": ("concept_id", ["definition", "related_metric_ids", "counterexamples", "interpretation_limits"]),
    "entity_catalog.csv": ("entity_id", ["entity_type", "definition", "evidence_refs", "registry_version"]),
    "relation_catalog.csv": ("relation_type", ["definition", "direction_rule", "evidence_requirements", "counterexamples"]),
    "alias_registry.csv": ("alias_id", ["metric_id", "scope_constraints", "mapping_status"]),
    "unit_rules.csv": ("rule_id", ["input_unit", "output_unit", "multiplier", "required_inputs", "failure_reason", "version"]),
    "definition_history.csv": ("definition_change_id", ["record_id", "new_version", "retroactive_policy"]),
    "driver_edges.csv": ("edge_id", ["source_metric_ids", "target_metric_id", "evidence_kind", "additional_assumptions", "interpretation_limits", "status"]),
}


def csv_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        if any(None in row for row in rows):
            raise ValueError("CSV contains overflow fields")
        return reader.fieldnames or [], rows


def jsonl_rows(path):
    rows = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError("JSONL item is not an object")
            rows.append(item)
    return rows


def refs(value):
    if value in EMPTY_REFS or value is None:
        return []
    if isinstance(value, list):
        return value
    return [item.strip() for item in value.replace("|", ";").split(";") if item.strip() not in EMPTY_REFS]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Audit:
    def __init__(self):
        self.checks = []

    def add(self, name, findings=(), tested=1, note=None):
        findings = list(findings)
        item = {"check": name, "status": "failed" if findings else "not_exercised" if tested == 0 else "passed",
                "tested_records": tested, "findings": findings}
        if note:
            item["note"] = note
        self.checks.append(item)


def base_claim(identity="QA-PRIOR", value="100"):
    return {"claim_id": identity, "numeric_value": value, "missing_reason": None,
            "company_id": "US-MSFT", "scope_id": "US-MSFT-CONSOLIDATED", "scope_level": "company",
            "product_id": None, "metric_id": "revenue", "definition_version": "0.1.0",
            "accounting_basis": "GAAP", "adjustment_definition": None,
            "consolidation": "consolidated", "canonical_unit": "USD", "currency": "USD", "scale": "1",
            "value_kind": "point", "denominator": None, "sign_convention": "source sign",
            "balance_or_flow": "flow", "statement_type": "income_statement", "aggregation_behavior": "additive_flow",
            "period_basis": "fiscal", "period_kind": "quarter", "fiscal_year": 2024,
            "fiscal_quarter": 4, "period_start": "2024-04-01", "period_end": "2024-06-30",
            "period_duration_days": 91, "modality": "actual_reported", "published_date": "2024-07-30"}


def engine_probes(artifact_dir, audit):
    engine_path = ROOT / "scripts/p03_comparability.py"
    if not engine_path.exists():
        audit.add("independent_engine_probes", ["comparability engine is absent"])
        return
    spec = importlib.util.spec_from_file_location("qa_p03_engine", engine_path)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    probes = []

    def probe(name, run, predicate):
        try:
            result = run()
            passed = bool(predicate(result))
            probes.append({"case": name, "passed": passed, "observed": result})
        except Exception as exc:
            probes.append({"case": name, "passed": False, "error": type(exc).__name__ + ": " + str(exc)})

    prior, new = base_claim(), base_claim("QA-NEW", "105")
    probe("same_period_delta", lambda: engine.compare_claims(new, prior),
          lambda x: x["decision"] == "comparable" and x["delta"] == "5")
    for field, value in [("scope_id", "US-MSFT-SEGMENT-X"), ("company_id", "US-NVDA"),
                         ("accounting_basis", "non_GAAP"), ("definition_version", "0.2.0"),
                         ("currency", "EUR"), ("canonical_unit", "percent_point"),
                         ("modality", "forecast"), ("consolidation", "separate"),
                         ("period_kind", "ytd"), ("period_basis", "calendar"),
                         ("value_kind", "share"), ("period_duration_days", 90)]:
        mutated = dict(new, **{field: value})
        probe("block_" + field, lambda m=mutated: engine.compare_claims(m, prior),
              lambda x: x["decision"] != "comparable" and x["delta"] is None)
    for field in ["company_id", "scope_id", "metric_id", "definition_version", "accounting_basis",
                  "currency", "value_kind", "modality", "period_start", "period_duration_days"]:
        mutated = dict(new, **{field: None})
        probe("missing_" + field, lambda m=mutated: engine.compare_claims(m, prior),
              lambda x: x["decision"] != "comparable" and x["delta"] is None)
    probe("real_zero_prior", lambda: engine.compare_claims(new, dict(prior, numeric_value="0")),
          lambda x: x["decision"] == "comparable" and x["delta"] == "105" and x["relative_delta"] is None and x["relative_delta_missing_reason"])
    probe("missing_value_is_not_zero", lambda: engine.compare_claims(dict(new, numeric_value=None, missing_reason="not_disclosed"), prior),
          lambda x: x["decision"] != "comparable" and x["delta"] is None)
    probe("no_future_information", lambda: engine.compare_claims(new, prior, as_of="2024-07-01"),
          lambda x: x["decision"] != "comparable" and "future_information_after_cutoff" in x["reasons"])
    probe("date_only_intraday_boundary", lambda: engine.compare_claims(new, prior, as_of="2024-07-30T12:00:00Z"),
          lambda x: x["decision"] != "comparable" and x["delta"] is None)
    dependency = {"record_type": "scope_corroboration", "record_id": "QA-SCOPE-POLICY",
                  "published_date": None, "observed_at": "2026-10-05T12:00:00Z",
                  "availability_basis": "observed_conservative"}
    dependent = dict(new, availability_dependencies=[dependency])
    probe("future_scope_dependency_is_not_historical_evidence", lambda: engine.compare_claims(dependent, prior, as_of="2025-07-30"),
          lambda x: x["decision"] != "comparable" and x["delta"] is None and any("future_information_after_cutoff" in reason for reason in x["reasons"]))
    probe("current_scope_dependency_is_available", lambda: engine.compare_claims(dependent, prior, as_of="2026-10-05"),
          lambda x: x["decision"] == "comparable")
    probe("source_scale_requires_explicit_normalization", lambda: engine.compare_claims(dict(new, scale="1000000"), dict(prior, scale="1000000")),
          lambda x: x["decision"] != "comparable" and x["delta"] is None)
    yoy_new = dict(new, fiscal_year=2025, period_start="2025-04-01", period_end="2025-06-30", published_date="2025-07-30")
    probe("explicit_YoY_calendar_quarter", lambda: engine.compare_claims(yoy_new, prior, "yoy"),
          lambda x: x["decision"] == "comparable" and x["delta"] == "5")
    annual_new = dict(new, fiscal_year=2024, fiscal_quarter=None, period_kind="annual", period_start="2024-01-01", period_end="2024-12-31", period_duration_days=366)
    annual_prior = dict(prior, fiscal_year=2023, fiscal_quarter=None, period_kind="annual", period_start="2023-01-01", period_end="2023-12-31", period_duration_days=365)
    probe("leap_year_calendar_anniversary_is_explained", lambda: engine.compare_claims(annual_new, annual_prior, "yoy"),
          lambda x: x["decision"] == "comparable" and x["checks"]["calendar_anniversary_length_guard"])
    weeks_new = dict(new, fiscal_year=2024, fiscal_quarter=None, period_kind="annual", period_start="2023-12-31", period_end="2025-01-04", period_duration_days=371)
    weeks_prior = dict(prior, fiscal_year=2023, fiscal_quarter=None, period_kind="annual", period_start="2023-01-01", period_end="2023-12-30", period_duration_days=364)
    probe("53_week_fiscal_year_is_not_silent_calendar_YoY", lambda: engine.compare_claims(weeks_new, weeks_prior, "yoy"),
          lambda x: x["decision"] != "comparable" and x["delta"] is None)
    for label in ["non-GAAP", "non_GAAP", "non_gaap", "non_GAAP_company"]:
        a, b = dict(new, accounting_basis=label), dict(prior, accounting_basis=label)
        probe("missing_adjustment_" + label, lambda a=a, b=b: engine.compare_claims(a, b),
              lambda x: x["decision"] != "comparable")
    rules = artifact_dir / "unit_rules.csv"
    for value, unit, currency, output in [("5", "USD_million", "USD", "5000000"),
                                         ("-25", "USD_thousand", "USD", "-25000"),
                                         ("0", "USD", "USD", "0")]:
        probe("scale_" + unit + "_" + value, lambda v=value, u=unit, c=currency: engine.normalize_amount(v, u, c, rules),
              lambda x, o=output: x["calculation_status"] == "computed" and x["output"] == o)
    for value, unit, currency in [("1", "USD_million", "EUR"), ("1", "percent", "USD"),
                                  ("1", "percent_point", "USD"), ("NaN", "USD", "USD"),
                                  (None, "USD", "USD")]:
        probe("blocked_normalization_" + str(value) + "_" + unit + "_" + currency,
              lambda v=value, u=unit, c=currency: engine.normalize_amount(v, u, c, rules),
              lambda x: x["calculation_status"] != "computed" and x["output"] is None)
    longer = dict(new, period_kind="ytd", period_start="2024-01-01", period_end="2024-06-30",
                  period_duration_days=182, fiscal_quarter=2, numeric_value="80")
    shorter = dict(prior, period_kind="ytd", period_start="2024-01-01", period_end="2024-03-31",
                   period_duration_days=91, fiscal_quarter=1, numeric_value="30")
    probe("compatible_YTD_difference", lambda: engine.difference_ytd(longer, shorter),
          lambda x: x["calculation_status"] == "computed" and x["output"] == "50" and x["period_start"] == "2024-04-01" and x["input_refs"] == ["QA-NEW", "QA-PRIOR"])
    for field, value in [("period_start", "2023-10-01"), ("scope_id", "OTHER-SCOPE"),
                         ("metric_id", "net_income"), ("currency", "EUR"),
                         ("definition_version", "0.2.0"), ("fiscal_year", 2023),
                         ("numeric_value", None), ("claim_id", None)]:
        m = dict(shorter, **{field: value})
        probe("block_YTD_" + field, lambda m=m: engine.difference_ytd(longer, m),
              lambda x: x["calculation_status"] != "computed" and x["output"] is None)
    for kind in ["rate", "share", "relative_change"]:
        a = dict(longer, value_kind=kind, metric_id="operating_margin", canonical_unit="percent", denominator="revenue")
        b = dict(shorter, value_kind=kind, metric_id="operating_margin", canonical_unit="percent", denominator="revenue")
        probe("nonadditive_YTD_" + kind, lambda a=a, b=b: engine.difference_ytd(a, b),
              lambda x: x["calculation_status"] != "computed" and x["output"] is None)
    for unit in ["percent_point", "percentage_point"]:
        a, b = dict(longer, canonical_unit=unit), dict(shorter, canonical_unit=unit)
        probe("nonadditive_YTD_unit_" + unit, lambda a=a, b=b: engine.difference_ytd(a, b),
              lambda x: x["calculation_status"] != "computed" and x["output"] is None)
    audit.add("independent_adversarial_engine_probes", [p["case"] for p in probes if not p["passed"]], len(probes),
              "Synthetic implementation probes; no extraction accuracy or human agreement claim.")
    return probes


def source_checks(artifact_dir, tables, audit, source_manifest=None, source_facts=None, source_audit=None):
    """Read private originals locally for hashes and numeric spans, without emitting prose."""
    source_dir = ROOT / "artifacts/us_equity/p0/available_20261005"
    run_manifest_path = source_dir / "source_run_manifest.json"
    run_manifest = json.loads(run_manifest_path.read_text(encoding="utf-8-sig")) if run_manifest_path.exists() else {}
    revision = "v0_3" if (source_dir / "facts_v0_3.jsonl").exists() else "original"
    suffix = "_" + revision if revision != "original" else ""
    manifest = source_manifest or source_dir / run_manifest.get("authoritative_document_manifest", "document_manifest" + suffix + ".csv")
    facts_path = source_facts or source_dir / run_manifest.get("authoritative_numeric_facts", "facts" + suffix + ".jsonl")
    source_dir = manifest.resolve().parent
    if not manifest.exists() or not facts_path.exists():
        audit.add("source_numeric_span_and_provenance", tested=0,
                  note="No source documents available; content validation not exercised.")
        return {"status": "not_exercised", "source_documents": 0, "source_numeric_occurrences": 0}
    from lxml import html
    _, docs = csv_rows(manifest)
    facts = jsonl_rows(facts_path)
    doc_by_id = {d["doc_id"]: d for d in docs}
    trees, errors = {}, []
    for name, expected_hash in run_manifest.get("output_sha256", {}).items():
        path = (source_dir / name).resolve()
        if not path.is_relative_to(source_dir.resolve()) or not path.exists() or sha(path) != expected_hash:
            errors.append(name + ": source run output hash mismatch")
    if len(doc_by_id) != len(docs):
        errors.append("duplicate source document IDs")
    for doc in docs:
        original = (ROOT / doc["storage_uri"]).resolve()
        if not original.is_relative_to(source_dir.resolve()):
            errors.append(doc["doc_id"] + ": original path outside source run")
            continue
        if not original.exists() or sha(original) != doc["sha256"]:
            errors.append(doc["doc_id"] + ": raw hash mismatch")
            continue
        trees[doc["doc_id"]] = html.fromstring(original.read_bytes()).getroottree()
        if doc.get("time_precision") == "date" and doc.get("published_at"):
            errors.append(doc["doc_id"] + ": manufactured publication timestamp")
        if doc.get("split_exposure") != "adaptation":
            errors.append(doc["doc_id"] + ": development source not marked adaptation")
        if doc.get("original_prose_sent_to_ai") not in {"False", "false", "0"}:
            errors.append(doc["doc_id"] + ": original prose AI input claimed")
    ids = [f.get("claim_id") for f in facts]
    if len(ids) != len(set(ids)) or any(not identifier for identifier in ids):
        errors.append("duplicate or missing source occurrence IDs")
    for fact in facts:
        identity, doc_id = fact.get("claim_id"), fact.get("doc_id")
        if doc_id not in doc_by_id or doc_id not in trees:
            errors.append(str(identity) + ": missing source document")
            continue
        doc = doc_by_id[doc_id]
        if fact.get("revision_id") != doc["revision_id"] or fact.get("event_family_id") != doc["event_family_id"]:
            errors.append(str(identity) + ": revision/family provenance mismatch")
        try:
            selected = trees[doc_id].xpath(fact["evidence_pointer"])
            if len(selected) != 1:
                raise ValueError("numeric XPath does not select one cell")
            text = selected[0].text_content()
            start, end = fact["value_span_start"], fact["value_span_end"]
            if not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(text):
                raise ValueError("invalid code point span")
            if text[start:end] != fact["value_raw"]:
                raise ValueError("numeric code point span roundtrip mismatch")
            numeric_value = Decimal(fact["numeric_value"])
            raw_number = fact["value_raw"].replace(",", "").strip()
            if "$" in raw_number:
                if fact.get("currency") != "USD":
                    raise ValueError("dollar symbol conflicts with normalized currency")
                raw_number = raw_number.replace("$", "").strip()
            raw_negative = raw_number.startswith("(") and raw_number.endswith(")")
            source_number = -Decimal(raw_number[1:-1]) if raw_negative else Decimal(raw_number)
            if fact.get("sign_policy") == "outflow_to_positive":
                if fact.get("metric_id") != "positive_cash_capex" or not raw_negative or numeric_value != -source_number:
                    raise ValueError("unconfirmed cash outflow sign normalization")
            elif numeric_value != source_number:
                raise ValueError("source numeric sign changed without registered policy")
            scale = Decimal(fact["scale"])
            if not numeric_value.is_finite() or not scale.is_finite() or scale <= 0:
                raise ValueError("nonfinite number or invalid scale")
            if numeric_value * scale != Decimal(fact["numeric_value_base_units"]):
                raise ValueError("normalized base amount mismatch")
            if fact.get("missing_reason") is not None:
                raise ValueError("observed number has stale missing reason")
            reference_end = date.fromisoformat(fact["period_end"])
            if fact.get("balance_or_flow") == "flow":
                reference_start = date.fromisoformat(fact["period_start"])
                duration = (reference_end - reference_start).days + 1
                if duration != fact["period_duration_days"] or duration <= 0:
                    raise ValueError("reference period duration mismatch")
            period_headers = trees[doc_id].xpath(fact["period_header_pointer"])
            year_headers = trees[doc_id].xpath(fact["year_header_pointer"])
            unit_headers = trees[doc_id].xpath(fact["unit_header_pointer"])
            if len(period_headers) != 1 or len(year_headers) != 1 or len(unit_headers) != 1:
                raise ValueError("period/year/unit XPath does not select one header")
            period_text = "".join(period_headers[0].text_content().lower().split())
            year_text = "".join(year_headers[0].text_content().split())
            end_month_day = reference_end.strftime("%B").lower() + str(reference_end.day)
            if fact.get("balance_or_flow") == "flow":
                month_count = (reference_end.year - reference_start.year) * 12 + reference_end.month - reference_start.month + 1
                month_names = {3: "three", 6: "six", 9: "nine", 12: "twelve"}
                if month_count not in month_names or month_names[month_count] + "monthsended" + end_month_day not in period_text:
                    raise ValueError("selected column period header does not match duration")
            elif end_month_day not in period_text:
                raise ValueError("selected balance header date does not match observation")
            if str(fact["fiscal_year"]) not in year_text or "millions" not in unit_headers[0].text_content().lower():
                raise ValueError("source year or unit header mismatch")
            if fact.get("original_prose_ai_input") is not False:
                raise ValueError("original prose AI input claimed")
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            errors.append(str(identity) + ": " + str(exc))
    audit.add("source_numeric_span_hash_scale_and_provenance", errors, len(facts),
              "Private local DOM numeric-cell checks; no complete-body or human audit certification.")
    audit_file = source_audit or source_dir / ("extraction_audit" + suffix + ".csv")
    period_confirmed = 0
    if audit_file.exists():
        _, source_audits = csv_rows(audit_file)
        period_confirmed = sum(row.get("period_header_confirmed") in {"True", "true", "1"} for row in source_audits)
        unresolved = sum(bool(row.get("unresolved")) for row in source_audits)
        audit.add("source_period_header_confirmation", tested=period_confirmed,
                  note=f"Confirmed {period_confirmed}/{len(source_audits)} numeric occurrence period headers; unresolved audit rows {unresolved}.")
    occurrences_path = artifact_dir / "metric_occurrences.csv"
    if occurrences_path.exists():
        _, occurrences = csv_rows(occurrences_path)
        by_metric = {}
        for item in occurrences:
            by_metric.setdefault(item["metric_id"], []).append(item)
        errors = []
        for item in occurrences:
            if item.get("exposure_status") != "adaptation" or item.get("annotation_status") != "agent_draft":
                errors.append(item["occurrence_id"] + ": source extraction is promoted to independent evaluation/gold")
        for metric in tables.get("metric_catalog.csv", []):
            group = by_metric.get(metric["metric_id"], [])
            def unique_count(field):
                return len({item[field] for item in group if item.get(field) not in EMPTY_REFS and item.get(field)})
            expected = {"occurrence_docs": unique_count("doc_id"), "occurrence_families": unique_count("event_family_id"),
                        "company_count": unique_count("company_id"),
                        "period_count": len({(item.get("period_start"), item.get("period_end"), item.get("balance_or_flow")) for item in group})}
            for field, expected_value in expected.items():
                if int(metric[field]) != expected_value:
                    errors.append(metric["metric_id"] + ": " + field + " differs from occurrence manifest")
            if int(metric["company_denominator"]) != len({d["company_id"] for d in docs}):
                errors.append(metric["metric_id"] + ": selected company denominator differs from source manifest")
        audit.add("catalog_occurrence_denominators", errors, len(tables.get("metric_catalog.csv", [])))
    else:
        audit.add("catalog_occurrence_denominators", ["metric_occurrences.csv is absent"])
    applied_runs = sorted(path for path in artifact_dir.glob("applied_*") if (path / "run_manifest.json").exists())
    normalized_path = applied_runs[-1] / "normalized_claims.jsonl" if applied_runs else artifact_dir / "normalized_claims.jsonl"
    if normalized_path.exists():
        normalized = jsonl_rows(normalized_path)
        fact_by_id = {fact["claim_id"]: fact for fact in facts}
        errors = []
        for item in normalized:
            identity = item.get("claim_id")
            source = fact_by_id.get(identity)
            if source is None:
                errors.append(str(identity) + ": normalized record has no source occurrence")
                continue
            if item.get("scale") != "1" or item.get("numeric_value") != source["numeric_value_base_units"]:
                errors.append(str(identity) + ": source-scale amount used as normalized base amount")
            if not any(key in item for key in ["conversion_provenance", "normalization_provenance", "source_value", "source_numeric_value"]):
                errors.append(str(identity) + ": base normalization has no conversion provenance")
            if item.get("scope_evidence_refs") and not item.get("availability_dependencies"):
                errors.append(str(identity) + ": supplemental scope evidence has no availability dependency")
        audit.add("base_unit_normalization_provenance", errors, len(normalized))
    else:
        audit.add("base_unit_normalization_provenance", tested=0, note="Normalized comparison inputs not yet generated.")
    relation_path = artifact_dir / "business_relations.jsonl"
    if relation_path.exists():
        relations = jsonl_rows(relation_path)
        entity_ids = {r["entity_id"] for r in tables.get("entity_catalog.csv", [])}
        types = {r["relation_type"] for r in tables.get("relation_catalog.csv", [])}
        errors = []
        for row in relations:
            for field in ["subject_entity_id", "object_entity_id"]:
                if row.get(field) not in entity_ids:
                    errors.append(row["relation_id"] + ": unregistered " + field)
            if row.get("relation_type") not in types:
                errors.append(row["relation_id"] + ": unregistered relation type")
            if not row.get("evidence_refs"):
                errors.append(row["relation_id"] + ": source relation lacks evidence")
            if row.get("split_exposure") != "adaptation":
                errors.append(row["relation_id"] + ": development relation not adaptation")
        audit.add("actual_relation_entities_and_source_layer", errors, len(relations),
                  "Reporting membership is preserved separately from customer/supply/product and financial impact claims.")
    return {"status": "failed" if any(check["status"] == "failed" and check["check"] in {
                "source_numeric_span_hash_scale_and_provenance", "catalog_occurrence_denominators",
                "base_unit_normalization_provenance", "actual_relation_entities_and_source_layer"} for check in audit.checks)
            else "numeric_spans_verified_with_stated_limits", "source_revision": revision,
            "source_files": [manifest.relative_to(ROOT).as_posix(), facts_path.relative_to(ROOT).as_posix(), audit_file.relative_to(ROOT).as_posix()],
            "source_documents": len(docs), "selected_numeric_documents": len({f["doc_id"] for f in facts}),
            "scope_corroboration_documents": len(docs) - len({f["doc_id"] for f in facts}),
            "source_numeric_occurrences": len(facts),
            "source_families": len({d["event_family_id"] for d in docs}),
            "selected_numeric_families": len({f["event_family_id"] for f in facts}),
            "source_companies": len({d["company_id"] for d in docs}),
            "period_headers_confirmed": period_confirmed, "full_bodies_verified": 0,
            "original_prose_ai_inputs": 0, "human_annotations": 0}


def applied_result_checks(artifact_dir, audit):
    runs = sorted(path for path in artifact_dir.glob("applied_*") if (path / "run_manifest.json").exists())
    if not runs:
        audit.add("actual_comparison_recalculation_and_counts", tested=0, note="Source comparisons have not been generated yet.")
        return
    run_dir = runs[-1]
    manifest = json.loads((run_dir / "run_manifest.json").read_text(encoding="utf-8-sig"))
    pairs = jsonl_rows(run_dir / "comparison_inputs.jsonl")
    results = jsonl_rows(run_dir / "comparability_results.jsonl")
    normalized = jsonl_rows(run_dir / "normalized_claims.jsonl")
    errors = []
    paths = {"facts_sha256": ROOT / manifest["facts_path"], "audit_sha256": ROOT / manifest["audit_path"],
             "metric_catalog_sha256": artifact_dir / "metric_catalog.csv", "unit_rules_sha256": artifact_dir / "unit_rules.csv",
             "occurrences_sha256": artifact_dir / "metric_occurrences.csv"}
    if "scope_corroboration_path" in manifest:
        paths["scope_corroboration_sha256"] = ROOT / manifest["scope_corroboration_path"]
    paths["script_sha256"] = ROOT / "scripts/p03_apply_registry.py"
    paths["comparability_engine_sha256"] = ROOT / "scripts/p03_comparability.py"
    for field, path in paths.items():
        if sha(path) != manifest.get(field):
            errors.append(field + ": application input changed since run")
    if manifest.get("normalized_claims") != len(normalized) or manifest.get("comparison_pairs") != len(pairs) or len(pairs) != len(results):
        errors.append("Application record counts differ from manifests")
    decisions = dict(Counter(item["decision"] for item in results))
    if decisions != manifest.get("comparison_decisions"):
        errors.append("Reported comparable/not-comparable counts differ from result rows")
    if manifest.get("mode") != "retrospective_current_only" or manifest.get("human_records") != 0 or manifest.get("gold_records") != 0:
        errors.append("Retrospective agent application is represented as historical or human gold")
    engine_path = ROOT / "scripts/p03_comparability.py"
    spec = importlib.util.spec_from_file_location("qa_p03_actual_engine", engine_path)
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    normalized_ids = {item["claim_id"] for item in normalized}
    by_pair = {item["pair_id"]: item for item in results}
    if len(by_pair) != len(results):
        errors.append("Duplicate comparison pair IDs")
    for pair in pairs:
        result = by_pair.get(pair["pair_id"])
        if result is None:
            errors.append(pair["pair_id"] + ": missing result")
            continue
        expected = engine.compare_claims(pair["new"], pair["prior"], pair.get("comparison_kind", "same_period"), manifest["as_of"])
        for field in ["decision", "reasons", "delta", "relative_delta", "delta_unit"]:
            if result.get(field) != expected.get(field):
                errors.append(pair["pair_id"] + ": recorded " + field + " differs from independent recalculation")
        if {pair["new"]["claim_id"], pair["prior"]["claim_id"]} - normalized_ids:
            errors.append(pair["pair_id"] + ": source normalized claim absent")
        if result.get("calculation_layer") != "derived" or result.get("exposure_status") != "adaptation":
            errors.append(pair["pair_id"] + ": derived comparison promoted to source or independent test")
        if result["decision"] != "comparable" and result.get("delta") is not None:
            errors.append(pair["pair_id"] + ": blocked comparison has a computed delta")
    audit.add("actual_comparison_recalculation_and_counts", errors, len(pairs),
              "Recalculated current retrospective pairs; comparative success is not extraction accuracy or holdout performance.")


def freeze_and_exposure_checks(artifact_dir, tables, audit):
    manifests = [artifact_dir / "baseline_registry_0.1.0/manifest.json", artifact_dir / "registry_v0.1_manifest.json"]
    for manifest_path in manifests:
        if not manifest_path.exists():
            audit.add("frozen_hashes_" + manifest_path.parent.name, tested=0,
                      note="Registry manifest not generated yet.")
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        errors = []
        for entry in manifest.get("files", []):
            path = (manifest_path.parent / entry["path"]).resolve()
            if not path.is_relative_to(artifact_dir.resolve()) or not path.exists() or sha(path) != entry["sha256"]:
                errors.append(entry["path"] + ": frozen file hash mismatch or invalid path")
        if manifest.get("independent_human_annotation_count", 0) != 0 or manifest.get("human_agreement") is not None:
            errors.append("Human waiver has been represented as observed annotation/agreement")
        audit.add("frozen_hashes_" + manifest_path.parent.name, errors, len(manifest.get("files", [])))
    transfer_path, cases_path = artifact_dir / "transfer_manifest.csv", artifact_dir / "transfer_cases.jsonl"
    if transfer_path.exists() and cases_path.exists():
        _, transfer = csv_rows(transfer_path)
        cases = jsonl_rows(cases_path)
        errors = []
        transfer_ids = {row["transfer_id"] for row in transfer}
        case_ids = {row["transfer_id"] for row in cases}
        if transfer_ids != case_ids or len(transfer_ids) != len(transfer) or len(case_ids) != len(cases):
            errors.append("Transfer manifest/case IDs differ or are duplicated")
        for item in transfer:
            if item.get("split") != "adaptation":
                errors.append(item["transfer_id"] + ": transfer development data is not adaptation")
        for item in cases:
            if item.get("exposure_status") != "adaptation" or item.get("annotation_status") != "agent_draft":
                errors.append(item["transfer_id"] + ": adaptation is promoted to independent annotation")
            if not item.get("frozen_registry_ref"):
                errors.append(item["transfer_id"] + ": pre-application registry is missing")
        audit.add("transfer_ids_and_adaptation_exposure", errors, len(cases),
                  "Retrospective same-company reapplication; no blind-company or cross-sector performance claim.")
    p3 = artifact_dir.parent / "p3"
    split_path = p3 / "split_manifest.csv"
    if split_path.exists():
        _, splits = csv_rows(split_path)
        families = {}
        errors = []
        for item in splits:
            families.setdefault(item["event_family_id"], set()).add(item["split"])
            if item.get("exposure_status") not in {"untouched", "unseen", "not_exposed"} and item.get("split") == "test":
                errors.append(item["item_id"] + ": exposed development material enters untouched test")
        for family, group in families.items():
            if "test" in group and group & {"train", "dev", "adaptation", "practice"}:
                errors.append(family + ": family straddles development and test")
        audit.add("future_independent_evaluation_split_leakage", errors, len(splits))
    else:
        audit.add("future_independent_evaluation_split_leakage", tested=0,
                  note="P04 is outside this P03 execution scope. Current source occurrences and transfer cases are adaptation; reserved untouched evaluation cases are declared as zero.")
    gold_count = 0
    for filename in ["gold_events.jsonl", "gold_relations.jsonl"]:
        path = p3 / filename
        if path.exists():
            gold_count += len(jsonl_rows(path))
    audit.add("human_waiver_does_not_fabricate_gold", ["Human waiver has been promoted to nonempty independent gold"] if gold_count else [],
              tested=1, note="Observed independent human annotations and agreement remain unmeasured.")
    authorization_path = artifact_dir / "progression_authorization.json"
    if authorization_path.exists():
        authorization = json.loads(authorization_path.read_text(encoding="utf-8-sig"))
        errors = []
        if authorization.get("human_review_records_created") != 0 or authorization.get("inter_annotator_agreement_computed") is not False:
            errors.append("Waived progress gate is represented as observed human review/agreement")
        if authorization.get("gold_status") != "not_created" or authorization.get("legacy_inputs") != []:
            errors.append("Human waiver imports gold or legacy evidence")
        audit.add("user_progression_waiver_provenance", errors)
    aliases = tables.get("alias_registry.csv", [])
    keys = {}
    for alias in aliases:
        key = tuple(alias.get(field) for field in ["alias_raw", "language", "scope_constraints", "unit_constraints"])
        keys.setdefault(key, []).append(alias)
    errors = []
    for group in keys.values():
        if len({row["metric_id"] for row in group}) > 1 and any(row.get("mapping_status") not in {"ambiguous", "conditional", "unknown"} for row in group):
            errors.append("Ambiguous alias is unconditionally mapped: " + group[0]["alias_id"])
    audit.add("alias_scope_ambiguity", errors, len(aliases))


def verify(artifact_dir, source_manifest=None, source_facts=None, source_audit=None):
    audit, tables = Audit(), {}
    for filename, (identity, required) in TABLES.items():
        path = artifact_dir / filename
        if not path.exists():
            audit.add(filename, ["required table absent"])
            continue
        header, rows = csv_rows(path)
        tables[filename] = rows
        errors = ["missing field " + field for field in [identity] + required if field not in header]
        ids = [row.get(identity) for row in rows]
        if any(not identity for identity in ids) or len(ids) != len(set(ids)):
            errors.append("missing or duplicate primary ID")
        for row in rows:
            errors += [str(row.get(identity)) + ": empty " + field for field in required if not row.get(field)]
        audit.add("contract_" + filename, errors, len(rows), "Empty table is not evidence of completed annotation or source coverage.")
    metrics = {r["metric_id"] for r in tables.get("metric_catalog.csv", [])}
    concepts = {r["concept_id"] for r in tables.get("accounting_concept_catalog.csv", [])}
    entities = {r["entity_id"] for r in tables.get("entity_catalog.csv", [])}
    errors = []
    for row in tables.get("metric_catalog.csv", []):
        errors += [row["metric_id"] + ": unknown concept " + ref for ref in refs(row.get("concept_ids")) if ref not in concepts]
        errors += [row["metric_id"] + ": unknown input metric " + ref for ref in refs(row.get("input_metric_ids")) if ref not in metrics]
    for row in tables.get("accounting_concept_catalog.csv", []):
        errors += [row["concept_id"] + ": unknown metric " + ref for ref in refs(row.get("related_metric_ids")) if ref not in metrics]
    for row in tables.get("entity_catalog.csv", []):
        errors += [row["entity_id"] + ": unknown parent " + ref for ref in refs(row.get("parent_entity_id")) if ref not in entities]
    for row in tables.get("alias_registry.csv", []):
        if row["metric_id"] not in metrics:
            errors.append(row["alias_id"] + ": unknown metric")
    for row in tables.get("driver_edges.csv", []):
        errors += [row["edge_id"] + ": unknown metric " + ref for ref in refs(row["source_metric_ids"]) + [row["target_metric_id"]] if ref not in metrics]
        if row["evidence_kind"] == "research_assumption" and not row["status"].startswith("proposed"):
            errors.append(row["edge_id"] + ": unobserved research assumption is promoted to fact")
    audit.add("registry_foreign_keys_and_driver_layer", errors, sum(map(len, tables.values())))
    errors = []
    for row in tables.get("unit_rules.csv", []):
        if row.get("rule_kind") in {"scale", "identity"}:
            try:
                n = Decimal(row["multiplier"])
                if not n.is_finite() or n <= 0:
                    errors.append(row["rule_id"] + ": multiplier must be finite and positive")
            except (InvalidOperation, ValueError):
                errors.append(row["rule_id"] + ": invalid Decimal multiplier")
        if {row["input_unit"], row["output_unit"]} == {"percent", "percent_point"}:
            errors.append(row["rule_id"] + ": percent and percentage points cannot be scaled into each other")
    audit.add("unit_rule_guard_contract", errors, len(tables.get("unit_rules.csv", [])))
    probes = engine_probes(artifact_dir, audit) or []
    source_validation = source_checks(artifact_dir, tables, audit, source_manifest, source_facts, source_audit)
    applied_result_checks(artifact_dir, audit)
    freeze_and_exposure_checks(artifact_dir, tables, audit)
    counts = Counter(check["status"] for check in audit.checks)
    return {"validator_version": VERSION, "checked_at": datetime.now(timezone.utc).isoformat(),
            "artifact_directory": artifact_dir.relative_to(ROOT).as_posix(),
            "checks": audit.checks, "status_counts": dict(counts),
            "engine_probes": probes, "human_validation": "waived_by_user; not performed by this validator",
            "human_agreement": None, "gold_certification": False,
            "source_content_validation": source_validation,
            "table_row_counts": {name: len(rows) for name, rows in tables.items()},
            "input_hashes": {name: sha(artifact_dir / name) for name in tables}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-dir", type=Path, default=ROOT / "artifacts/us_equity/p2")
    parser.add_argument("--report", type=Path, default=ROOT / "artifacts/us_equity/p2/independent_validation.json")
    parser.add_argument("--source-manifest", type=Path)
    parser.add_argument("--source-facts", type=Path)
    parser.add_argument("--source-audit", type=Path)
    parser.add_argument("--replace-report", action="store_true")
    args = parser.parse_args()
    if args.report.exists() and not args.replace_report:
        raise SystemExit("Report already exists; choose a new revision path or use --replace-report after review.")
    report = verify(args.artifact_dir.resolve(), args.source_manifest, args.source_facts, args.source_audit)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status_counts": report["status_counts"], "engine_probes": len(report["engine_probes"]),
                      "report": str(args.report)}, ensure_ascii=False))
    raise SystemExit(1 if report["status_counts"].get("failed") else 0)


if __name__ == "__main__":
    main()
