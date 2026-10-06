"""Build the provisional P02 schema, synthetic fixtures, and literature tables.

No source bodies are downloaded. Existing outputs require --replace-generated.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "us_equity" / "p1"
VERSION = "0.1.0"


def obj(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": False}


def enum(*values):
    return {"enum": list(values)}


def nullable(schema):
    return {"anyOf": [schema, {"type": "null"}]}


def array(item, minimum=0):
    return {"type": "array", "items": item, "minItems": minimum}


def ref(name):
    return {"$ref": f"#/$defs/{name}"}


def schema():
    text = {"type": "string", "minLength": 1}
    nt = nullable(text)
    decimal = {"type": "string", "pattern": r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$"}
    nd = nullable(decimal)
    date = nullable({"type": "string", "format": "date"})
    instant = nullable({"type": "string", "format": "date-time"})
    reason = enum("not_disclosed", "not_found", "ambiguous", "not_applicable",
                  "parse_failed", "incompatible", "not_yet_checked")
    modalities = enum("actual_reported", "plan", "forecast", "possibility", "denial", "unknown")
    definitions = {
        "missing_reason": reason,
        "missing_reasons": {"type": "object", "additionalProperties": reason},
        "decimal": decimal,
        "period": obj({"period_start": date, "period_end": date, "as_of_date": date,
                       "period_basis": enum("fiscal", "calendar", "other", "unknown", "not_applicable"),
                       "period_kind": enum("quarter", "ytd", "annual", "instant", "other", "unknown", "not_applicable"),
                       "fiscal_year": nullable({"type": "integer", "minimum": 1900, "maximum": 2200}),
                       "fiscal_quarter": nullable({"type": "integer", "minimum": 1, "maximum": 4}),
                       "duration_days": nullable({"type": "integer", "minimum": 1}),
                       "missing_reason": nullable(reason)}),
        "temporal": obj({"published_at": instant, "published_date": date,
                         "time_precision": enum("second", "minute", "date", "unknown"),
                         "timezone": nt, "utc_offset": nullable({"type": "string", "pattern": r"^[+-](?:0[0-9]|1[0-4]):[0-5][0-9]$"}),
                         "publication_evidence_refs": array(text),
                         "reference_period": ref("period"), "effective_period": ref("period"),
                         "observed_at": {"type": "string", "format": "date-time"},
                         "available_at": instant,
                         "availability_policy": enum("publication_verified", "observation_as_of", "date_only_boundary", "unknown"),
                         "availability_evidence_refs": array(text),
                         "date_conflict_status": enum("none_observed", "unresolved", "not_yet_checked")}),
        "evidence": obj({"evidence_id": text, "doc_id": text, "revision_id": text,
                         "block_id": nt,
                         "location_type": enum("xpath", "table_cell", "page", "api_field", "synthetic", "unlocated"),
                         "location": nt,
                         "location_status": enum("verified", "unverified", "unlocated", "synthetic"),
                         "start": nullable({"type": "integer", "minimum": 0}),
                         "end": nullable({"type": "integer", "minimum": 0}),
                         "offset_unit": {"const": "unicode_code_point"},
                         "offset_interval": {"const": "0-based-[start,end)"},
                         "offset_mapping": enum("identity", "verified_mapping", "not_available", "not_applicable"),
                         "selected_text": nt,
                         "table_id": nt, "row_index": nullable({"type": "integer", "minimum": 0}),
                         "col_index": nullable({"type": "integer", "minimum": 0}),
                         "header_refs": array(text), "note_refs": array(text)}),
        "provenance": obj({"doc_id": text, "revision_id": text, "source_id": text,
                           "source_url": {"type": "string", "format": "uri"},
                           "final_url": {"type": "string", "format": "uri"},
                           "rights_basis_ref": text,
                           "rights_check_status": enum("verified_for_this_use", "unresolved", "synthetic"),
                           "storage_policy": enum("allowed", "conditional", "prohibited", "unresolved", "synthetic"),
                           "ai_input_policy": enum("allowed", "conditional", "prohibited", "unresolved", "synthetic"),
                           "external_transfer_policy": enum("allowed", "conditional", "prohibited", "unresolved", "synthetic"),
                           "evidence": array(ref("evidence"), 1)}),
        "raw": obj({"claim_text": nt, "action_raw": nt, "metric_raw": nt, "value_raw": nt,
                    "unit_raw": nt, "line_item_raw": nt, "speaker_raw": nt, "time_raw": array(text)}),
        "financial_context": obj({"statement_type": enum("balance_sheet", "income_statement", "cash_flow", "equity", "note", "md_and_a", "other", "unknown", "not_applicable"),
                                  "balance_or_flow": enum("balance", "flow", "unknown", "not_applicable"),
                                  "period_duration": nullable({"type": "integer", "minimum": 1}),
                                  "note_refs": array(text), "concept_ids": array(text),
                                  "adjustment_component_refs": array(text)}),
        "assessment": nullable(obj({"assessment_id": text, "author_id": text,
                                    "author_kind": enum("agent_draft", "independent_human", "human_review", "adjudicated"),
                                    "created_at": {"type": "string", "format": "date-time"},
                                    "as_of": {"type": "string", "format": "date-time"},
                                    "review_readiness": enum("supported", "needs_review", "not_comparable"),
                                    "readiness_reasons": array(text, 1), "uncertainty_reason": nt,
                                    "questions": array(obj({"question_id": text, "response": text,
                                                             "rationale": text, "evidence_refs": array(text)})),
                                    "business_financial_interpretation": nt})),
        "calculation": obj({"calculation_id": text, "formula_id": text, "formula_version": text,
                            "input_refs": array(text), "output": nd, "output_unit": nt,
                            "calculation_status": enum("computed", "insufficient_inputs", "incompatible_inputs", "invalid_formula", "error"),
                            "missing_inputs": array(text), "rounding_policy": text,
                            "calculated_at": {"type": "string", "format": "date-time"},
                            "prepared_by": text, "reviewed_by": nt,
                            "model_output_seen_before_work": nullable({"type": "boolean"})})
    }
    normalized_common = {
        "company_id": nt, "scope_id": nt, "modality": modalities,
        "negation": nullable({"type": "boolean"}), "conditions": array(text),
        "temporal": ref("temporal"),
        "evidence_status": enum("company_reported", "source_reported", "externally_verified", "unresolved", "synthetic"),
        "extraction_status": enum("complete", "partial", "unresolved"),
        "field_missing_reasons": ref("missing_reasons")
    }
    event = dict(normalized_common)
    event.update({"event_type": text, "product_id": nt, "actor": nt,
                  "entity_refs": array(text), "relation_refs": array(text),
                  "metric_id": nt, "metric_mapping_candidates": array(text),
                  "numeric_value": nd, "value_kind": enum("point", "range", "relative_change", "absolute_change", "rate", "share", "qualitative", "unknown"),
                  "lower": nd, "upper": nd,
                  "missing_reason": nullable(reason),
                  "direction": enum("increase", "decrease", "unchanged", "mixed", "unknown", "not_applicable"),
                  "canonical_unit": nt, "currency": nullable({"type": "string", "pattern": "^[A-Z]{3}$"}), "scale": nd,
                  "accounting_basis": enum("GAAP", "non_GAAP", "other", "unknown", "not_applicable"),
                  "adjustment_definition": nt, "consolidation": enum("consolidated", "separate", "segment", "unknown"),
                  "financial_context": ref("financial_context"),
                  "comparison_basis": enum("yoy", "qoq", "previous_plan", "previous_guidance", "previous_statement", "share_denominator", "none", "unknown"),
                  "denominator": nt, "prior_claim_id": nt,
                  "prior_state_status": enum("not_yet_checked", "prior_not_found", "candidate_found", "comparable_prior", "repeated", "not_applicable")})
    definitions["event_normalized"] = obj(event)
    relation = dict(normalized_common)
    relation.update({"relation_type": enum("supplies_to", "develops", "offers", "partners_with", "competes_with", "belongs_to_industry", "unknown"),
                     "subject_entity_id": nt, "object_entity_id": nt, "subject_role": nt, "object_role": nt,
                     "direction": enum("subject_to_object", "symmetric", "unknown"),
                     "product_service_ids": array(text), "entity_refs": array(text),
                     "valid_from": date, "valid_to": date, "speaker": nt,
                     "prior_relation_id": nt, "uncertainty_reason": nt})
    definitions["relation_normalized"] = obj(relation)
    definitions["temporal"]["allOf"] = [{
        "if": {"properties": {"time_precision": enum("date", "unknown")}, "required": ["time_precision"]},
        "then": {"properties": {"published_at": {"type": "null"}}},
        "else": {"properties": {"published_at": {"type": "string", "format": "date-time"}}}
    }]
    definitions["event_normalized"]["allOf"] = [{
        "if": {"properties": {"numeric_value": {"type": "null"}}, "required": ["numeric_value"]},
        "then": {"properties": {"missing_reason": reason}},
        "else": {"properties": {"missing_reason": {"type": "null"}}}
    }, {
        "if": {"properties": {"value_kind": {"const": "range"}}, "required": ["value_kind"]},
        "then": {"properties": {"lower": decimal, "upper": decimal}},
        "else": {"properties": {"lower": {"type": "null"}, "upper": {"type": "null"}}}
    }]
    definitions["calculation"]["allOf"] = [{
        "if": {"properties": {"calculation_status": {"const": "computed"}}, "required": ["calculation_status"]},
        "then": {"properties": {"output": decimal, "missing_inputs": {"maxItems": 0}}},
        "else": {"properties": {"output": {"type": "null"}}}
    }]
    top = obj({"schema_version": {"const": VERSION},
               "record_kind": enum("event_claim", "business_relation"),
               "record_id": text, "record_revision_id": text,
               "claim_id": text, "claim_revision_id": text,
               "event_id": text, "event_family_id": text,
               "relation_id": nt, "relation_revision_id": nt,
               "example_kind": enum("source_supported", "synthetic"),
               "annotation_status": enum("agent_draft", "independent_human", "adjudicated", "synthetic_fixture"),
               "exposure_status": enum("adaptation", "practice", "train", "dev", "test", "embargo", "unassigned", "synthetic"),
               "registry_version": text, "model_version": nt, "run_id": text,
               "supersedes_record_id": nt, "follow_up_of_family_id": nt,
               "provenance": ref("provenance"), "raw": ref("raw"),
               "normalized": {"type": "object"}, "assessment": ref("assessment"),
               "derived": array(ref("calculation"))})
    top.update({"$schema": "https://json-schema.org/draft/2020-12/schema",
                "$id": "urn:semi-auto-researching-corporate:us-equity:p02:0.1.0",
                "title": "P02 provisional EventClaim and BusinessRelation v0.1.0",
                "description": "DATA_CONTRACTS v1.2 implementation draft; not an independently annotated gold schema.",
                "$defs": definitions,
                "allOf": [
                    {"if": {"properties": {"record_kind": {"const": "event_claim"}}, "required": ["record_kind"]},
                     "then": {"properties": {"normalized": ref("event_normalized"), "relation_id": {"type": "null"}, "relation_revision_id": {"type": "null"}}},
                     "else": {"properties": {"normalized": ref("relation_normalized"), "relation_id": text, "relation_revision_id": text}}},
                    {"if": {"properties": {"example_kind": {"const": "synthetic"}}, "required": ["example_kind"]},
                     "then": {"properties": {"annotation_status": {"const": "synthetic_fixture"}, "exposure_status": {"const": "synthetic"}}}}
                ]})
    return top


def period(kind="unknown", start=None, end=None):
    return {"period_start": start, "period_end": end, "as_of_date": None,
            "period_basis": "unknown", "period_kind": kind, "fiscal_year": None,
            "fiscal_quarter": None, "duration_days": None, "missing_reason": "not_yet_checked"}


def example(label, statement, modality="plan"):
    doc = f"SYN-D-{label}"
    evidence = {"evidence_id": f"SYN-EV-{label}", "doc_id": doc, "revision_id": "synthetic-r1",
                "block_id": f"SYN-B-{label}", "location_type": "synthetic", "location": "synthetic sentence",
                "location_status": "synthetic", "start": 0, "end": len(statement),
                "offset_unit": "unicode_code_point", "offset_interval": "0-based-[start,end)",
                "offset_mapping": "identity", "selected_text": statement,
                "table_id": None, "row_index": None, "col_index": None, "header_refs": [], "note_refs": []}
    temporal = {"published_at": None, "published_date": "2025-01-15", "time_precision": "date",
                "timezone": None, "utc_offset": None, "publication_evidence_refs": [evidence["evidence_id"]],
                "reference_period": period(), "effective_period": period(),
                "observed_at": "2026-10-05T09:00:00+09:00", "available_at": None,
                "availability_policy": "date_only_boundary", "availability_evidence_refs": [],
                "date_conflict_status": "none_observed"}
    normalized = {"company_id": "SYN-CO-A", "scope_id": "SYN-PRODUCT-X", "modality": modality,
                  "negation": False, "conditions": [], "temporal": temporal,
                  "evidence_status": "synthetic", "extraction_status": "partial",
                  "field_missing_reasons": {"metric_id": "not_yet_checked", "canonical_unit": "not_applicable", "currency": "not_applicable", "scale": "not_applicable", "prior_claim_id": "not_found", "temporal.timezone": "not_yet_checked", "temporal.available_at": "not_yet_checked", "raw.metric_raw": "not_applicable", "raw.value_raw": "not_applicable", "raw.unit_raw": "not_applicable", "raw.line_item_raw": "not_applicable"},
                  "event_type": "product_stage", "product_id": "SYN-PRODUCT-X", "actor": "SYN-CO-A",
                  "entity_refs": ["SYN-CO-A", "SYN-PRODUCT-X"], "relation_refs": [],
                  "metric_id": None, "metric_mapping_candidates": [], "numeric_value": None,
                  "value_kind": "qualitative", "lower": None, "upper": None, "missing_reason": "not_applicable",
                  "direction": "not_applicable", "canonical_unit": None, "currency": None, "scale": None,
                  "accounting_basis": "not_applicable", "adjustment_definition": None, "consolidation": "unknown",
                  "financial_context": {"statement_type": "not_applicable", "balance_or_flow": "not_applicable", "period_duration": None, "note_refs": [], "concept_ids": [], "adjustment_component_refs": []},
                  "comparison_basis": "none", "denominator": None, "prior_claim_id": None, "prior_state_status": "prior_not_found"}
    return {"schema_version": VERSION, "record_kind": "event_claim", "record_id": f"SYN-C-{label}", "record_revision_id": "synthetic-r1",
            "claim_id": f"SYN-C-{label}", "claim_revision_id": "synthetic-r1", "event_id": f"SYN-E-{label}", "event_family_id": f"SYN-F-{label}",
            "relation_id": None, "relation_revision_id": None,
            "example_kind": "synthetic", "annotation_status": "synthetic_fixture", "exposure_status": "synthetic",
            "registry_version": "synthetic-only-0.1.0", "model_version": None, "run_id": "P02-synthetic-20261005-001",
            "supersedes_record_id": None, "follow_up_of_family_id": None,
            "provenance": {"doc_id": doc, "revision_id": "synthetic-r1", "source_id": "synthetic",
                           "source_url": f"urn:synthetic:{label}", "final_url": f"urn:synthetic:{label}",
                           "rights_basis_ref": "synthetic-authored-fixture", "rights_check_status": "synthetic",
                           "storage_policy": "synthetic", "ai_input_policy": "synthetic", "external_transfer_policy": "synthetic", "evidence": [evidence]},
            "raw": {"claim_text": statement, "action_raw": "develop", "metric_raw": None, "value_raw": None,
                    "unit_raw": None, "line_item_raw": None, "speaker_raw": "Synthetic Company A", "time_raw": ["2025-01-15"]},
            "normalized": normalized, "assessment": None, "derived": []}


def examples():
    plan = example("plan", "Synthetic Company A plans to develop product X 🚀.")
    actual = example("actual", "Synthetic Company A reports sales of product Y.", "actual_reported")
    actual["event_family_id"] = plan["event_family_id"]
    actual["event_id"] = plan["event_id"]
    actual["raw"]["action_raw"] = "reports sales"
    actual["normalized"]["product_id"] = actual["normalized"]["scope_id"] = "SYN-PRODUCT-Y"
    actual["normalized"]["entity_refs"] = ["SYN-CO-A", "SYN-PRODUCT-Y"]
    actual["normalized"]["event_type"] = "product_sales_report"
    actual["provenance"]["doc_id"] = plan["provenance"]["doc_id"]
    actual["provenance"]["evidence"][0]["doc_id"] = plan["provenance"]["doc_id"]
    actual["normalized"]["temporal"]["reference_period"] = period("quarter", "2024-10-01", "2024-12-31")
    zero = example("zero", "Synthetic Company A reports revenue of USD 0.", "actual_reported")
    zero["raw"].update({"metric_raw": "revenue", "value_raw": "0", "unit_raw": "USD", "line_item_raw": "revenue"})
    zero["raw"]["action_raw"] = "reports revenue"
    zero["normalized"].update({"event_type": "financial_result", "scope_id": "SYN-CO-A-CONSOLIDATED", "product_id": None, "entity_refs": ["SYN-CO-A"], "numeric_value": "0", "value_kind": "point", "missing_reason": None, "canonical_unit": "currency", "currency": "USD", "scale": "1", "accounting_basis": "unknown", "consolidation": "consolidated"})
    zero["normalized"]["field_missing_reasons"].update({"product_id": "not_applicable", "accounting_basis": "not_yet_checked"})
    zero["normalized"]["financial_context"].update({"statement_type": "income_statement", "balance_or_flow": "flow"})
    zero["normalized"]["temporal"]["reference_period"] = period()
    for key in ["canonical_unit", "currency", "scale", "raw.metric_raw", "raw.value_raw", "raw.unit_raw", "raw.line_item_raw"]:
        zero["normalized"]["field_missing_reasons"].pop(key, None)
    increase = example("relative", "Synthetic Company A plans capacity 20% above its previous plan.")
    increase["raw"].update({"metric_raw": "capacity", "value_raw": "20% above its previous plan", "unit_raw": "%"})
    increase["raw"]["action_raw"] = "plans capacity"
    increase["normalized"].update({"event_type": "capacity_plan_revision", "numeric_value": "20", "value_kind": "relative_change", "missing_reason": None, "direction": "increase", "canonical_unit": "percent", "scale": "1", "comparison_basis": "previous_plan"})
    for key in ["canonical_unit", "scale", "raw.metric_raw", "raw.value_raw", "raw.unit_raw"]:
        increase["normalized"]["field_missing_reasons"].pop(key, None)
    increase["derived"] = [{"calculation_id": "SYN-CALC-no-absolute", "formula_id": "synthetic.capacity-from-relative", "formula_version": "0.1.0", "input_refs": [increase["claim_id"]], "output": None, "output_unit": "units", "calculation_status": "insufficient_inputs", "missing_inputs": ["prior absolute capacity"], "rounding_policy": "no computation", "calculated_at": "2026-10-05T09:00:00+09:00", "prepared_by": "Codex", "reviewed_by": None, "model_output_seen_before_work": None}]
    relation = example("relation-plan", "Synthetic Company A plans to supply samples to Company B.")
    relation.update({"record_kind": "business_relation", "relation_id": "SYN-R-1", "relation_revision_id": "synthetic-r1"})
    common = {k: copy.deepcopy(relation["normalized"][k]) for k in ["company_id", "scope_id", "modality", "negation", "conditions", "temporal", "evidence_status", "extraction_status", "field_missing_reasons"]}
    common["field_missing_reasons"] = {"valid_from": "not_disclosed", "valid_to": "not_disclosed", "prior_relation_id": "not_found"}
    common.update({"relation_type": "supplies_to", "subject_entity_id": "SYN-CO-A", "object_entity_id": "SYN-CO-B", "subject_role": "supplier", "object_role": "customer", "direction": "subject_to_object", "product_service_ids": ["SYN-PRODUCT-X"], "entity_refs": ["SYN-CO-A", "SYN-CO-B"], "valid_from": None, "valid_to": None, "speaker": "SYN-CO-A", "prior_relation_id": None, "uncertainty_reason": "Synthetic planned sample supply; no actual sales evidence."})
    relation["normalized"] = common
    relation["raw"]["action_raw"] = "plans to supply samples"
    followup = copy.deepcopy(relation)
    followup.update({"record_id": "SYN-C-relation-executed", "claim_id": "SYN-C-relation-executed", "relation_id": "SYN-R-2", "event_id": "SYN-E-followup", "event_family_id": "SYN-F-followup", "follow_up_of_family_id": relation["event_family_id"]})
    followup["normalized"]["modality"] = "actual_reported"
    followup["normalized"]["prior_relation_id"] = relation["relation_id"]
    followup["normalized"]["field_missing_reasons"].pop("prior_relation_id")
    statement = "Synthetic Company A reports commercial shipments to Company B."
    followup["raw"].update({"claim_text": statement, "action_raw": "reports commercial shipments"})
    followup["provenance"].update({"doc_id": "SYN-D-followup", "source_url": "urn:synthetic:followup", "final_url": "urn:synthetic:followup"})
    followup["provenance"]["evidence"][0].update({"doc_id": "SYN-D-followup", "block_id": "SYN-B-followup", "evidence_id": "SYN-EV-followup", "end": len(statement), "selected_text": statement})
    followup["normalized"]["temporal"]["published_date"] = "2025-02-15"
    followup["normalized"]["temporal"]["publication_evidence_refs"] = ["SYN-EV-followup"]
    followup["normalized"]["uncertainty_reason"] = "Synthetic reported shipment, not independently verified sales."
    return [plan, actual, zero, increase, relation, followup]


def fixtures(records):
    cases = [{"case_id": f"valid-{r['record_id']}", "expected_valid": True, "record": r} for r in records]
    def invalid(label, index, path, value):
        item = copy.deepcopy(records[index])
        cursor = item
        for key in path[:-1]:
            cursor = cursor[key]
        cursor[path[-1]] = value
        cases.append({"case_id": label, "expected_valid": False, "record": item})
    invalid("reject-date-invented-midnight", 0, ["normalized", "temporal", "published_at"], "2025-01-15T00:00:00Z")
    invalid("reject-null-without-reason", 0, ["normalized", "missing_reason"], None)
    invalid("reject-insufficient-input-nonnull-output", 3, ["derived", 0, "output"], "120")
    invalid("reject-binary-float-value", 2, ["normalized", "numeric_value"], 0.0)
    invalid("reject-comma-number", 2, ["normalized", "numeric_value"], "1,000")
    invalid("reject-synthetic-gold", 0, ["annotation_status"], "adjudicated")
    invalid("reject-synthetic-test", 0, ["exposure_status"], "test")
    invalid("reject-unlocated-nonnull-offset", 0, ["provenance", "evidence", 0, "location_status"], "unlocated")
    invalid("reject-end-before-start", 0, ["provenance", "evidence", 0, "start"], 999)
    invalid("reject-utf16-offset-unit", 0, ["provenance", "evidence", 0, "offset_unit"], "utf16")
    invalid("reject-range-missing-endpoints", 2, ["normalized", "value_kind"], "range")
    invalid("reject-future-period-reversed", 0, ["normalized", "temporal", "effective_period"], period("other", "2025-04-01", "2025-01-01"))
    invalid("reject-relation-direction-flipped", 4, ["normalized", "subject_role"], "customer")
    invalid("reject-body-with-unresolved-rights", 0, ["provenance", "rights_check_status"], "unresolved")
    invalid("reject-unknown-field-no-reason", 0, ["normalized", "company_id"], None)
    invalid("reject-product-reference-inconsistent", 1, ["normalized", "entity_refs"], ["SYN-CO-A", "SYN-PRODUCT-X"])
    invalid("reject-financial-flow-marked-nonfinancial", 2, ["normalized", "financial_context", "statement_type"], "not_applicable")
    invalid("reject-stale-missing-reason-for-present-value", 3, ["normalized", "field_missing_reasons", "canonical_unit"], "not_applicable")
    invalid("reject-action-absent-from-raw-claim", 2, ["raw", "action_raw"], "develop")
    invalid("reject-unicode-roundtrip-surface-mismatch", 0, ["provenance", "evidence", 0, "selected_text"], "Synthetic Company A plans to develop product X.")
    guarded = copy.deepcopy(records[0])
    guarded["provenance"]["rights_check_status"] = "unresolved"
    guarded["raw"]["claim_text"] = None
    guarded["raw"]["action_raw"] = None
    cases.append({"case_id": "reject-excerpt-with-unresolved-rights-no-body", "expected_valid": False, "record": guarded})
    invalid("reject-missing-reason-for-array-without-crash", 0, ["normalized", "field_missing_reasons", "entity_refs"], "not_applicable")
    return cases


def literature():
    # Short design notes only; no source full texts are replicated.
    return [
        ("R02", "events", "Doc2EDAG: An End-to-End Document-level Framework for Chinese Financial Event Extraction", "Zheng; Cao; Xu; Bian", "2019", "https://aclanthology.org/D19-1032.pdf", "10.18653/v1/D19-1032", "selected_body_sections", "§3–4 pp.339–340 (PDF pages 3–4); introduction pp.337–338", "Chinese financial announcements; document event table extraction", "RQ1", "P02-001; evidence[]; atomic claim", "Cross-sentence arguments and multiple event records justify document context and separate claims.", "Chinese/DS labels; no transferred English accuracy; no actual correction/followup policy derived from paper", "Read modelling/label unit sections only; not full-paper read"),
        ("R08", "events;metrics", "FinQA: A Dataset of Numerical Reasoning over Financial Data", "Chen et al.", "2021", "https://aclanthology.org/2021.emnlp-main.300.pdf", "10.18653/v1/2021.emnlp-main.300", "selected_body_sections", "§3–4 pp.3699–3700 (PDF pages 3–4)", "English financial report table/text QA and reasoning programs", "RQ2", "P02-002; derived.formula_id; input_refs", "Evidence retrieval and calculation programs are separate; execution/program accuracy have distinct limits.", "Simplifies complex tables; dataset/source report redistribution rights unverified; no event extraction benchmark", "No dataset downloaded; no model adopted"),
        ("R03", "agreement", "Inter-Coder Agreement for Computational Linguistics", "Artstein; Poesio", "2008", "https://aclanthology.org/J08-4004.pdf", "10.1162/coli.07-034-R2", "selected_body_sections", "§2.1 pp.555–556; §2.6 pp.563–565 (PDF pages 2–3,10–12)", "Computational linguistic annotation agreement survey", "RQ5", "Independent labels; field denominators; ordinal/nominal separation", "Reliability is distinct from validity; disagreement distances and missingness affect coefficient choice.", "No local human agreement measured; final coefficient not yet chosen", "Selected assumptions read; whole 42-page paper not read"),
        ("R01", "materiality", "IFRS Practice Statement 2: Making Materiality Judgements", "IFRS Foundation", "2017; current official overview checked", "https://www.ifrs.org/issued-standards/list-of-standards/materiality-practice-statement/", "not_applicable", "official_overview", "About; standard history", "IFRS general-purpose financial statement preparation", "RQ4", "P02-004; accounting vs research action distinction", "Non-mandatory financial-reporting guidance; not a research action label or US rule.", "Full standard paragraphs not read; no US-company legal materiality conclusion", "Public About only"),
        ("R09", "materiality", "Event Studies in Economics and Finance", "MacKinlay", "1997", "https://www.jstor.org/stable/2729691", "10.2307/2729691", "body_unavailable", "Publisher URL returned no readable body", "Finance event-study methodology", "RQ4", "Future method reading; outcome separated from assessment", "No methods adopted from unread body.", "Estimation/event-window procedure not implemented; body access unresolved", "Bibliographic reference retained from REFERENCES, body unread"),
        ("R05", "events", "FinBERT: A Pretrained Language Model for Financial Communications", "Yang; Uy; Huang", "2020", "https://arxiv.org/abs/2006.08097", "10.48550/arXiv.2006.08097", "abstract_metadata", "v2 2020-07-09; title/abstract", "English financial communications; financial sentiment classification", "RQ1", "No model adopted; sentiment not materiality", "The reported task is sentiment classification; event/relation extraction needs separate evidence.", "No body read; no model/data license checked; no local performance", "Abstract only"),
        ("O01", "ontology;metrics", "SKOS Simple Knowledge Organization System Reference", "W3C", "Recommendation 2009-08-18", "https://www.w3.org/TR/skos-reference/", "not_applicable", "selected_standard_sections", "§5 lexical labels; §7 semantic relations; §10 mapping", "Knowledge organization conceptual standard", "RQ3", "concept/metric/alias distinction; cautious exactMatch", "Labels, hierarchy and cross-scheme mapping have different semantics.", "RDF not required; company alias/metric mappings not yet validated", "Selected standard sections"),
        ("O03", "ontology", "PROV-O: The PROV Ontology", "W3C", "Recommendation 2013-04-30", "https://www.w3.org/TR/prov-o/", "not_applicable", "selected_standard_sections", "§3.1 Starting Point; §3.2 Expanded Terms", "Provenance entity/activity/agent and derivation/revision", "RQ3", "doc/revision/run/author/supersedes links", "Track source, extraction activity, authorship and revisions separately.", "No OWL reasoning or graph implementation; attribution not correctness proof", "Selected narrative sections"),
        ("O02", "ontology;metrics", "The Financial Industry Business Ontology", "EDM Council", "Current official introduction checked", "https://spec.edmcouncil.org/fibo/", "not_applicable", "official_overview", "About FIBO", "Financial concepts and relations; OWL", "RQ3", "Candidate term source only; no term adopted", "Official introduction confirms concept/relation scope.", "Specific ontology release/term definitions and reuse rights not checked", "Introduction only"),
        ("FIN01", "financial;metrics", "Integration of Financial Statement Analysis Techniques", "CFA Institute", "2026 Curriculum", "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/integration-financial-statement-analysis-techniques", "not_applicable", "public_framework", "Introduction; Exhibit 1 phases 1–6; public learning outcomes", "Financial statement analysis workflow", "RQ6", "Question/data/process/interpret/report/followup sequence", "Analysis starts with purpose/questions and tracks follow-up.", "Full paid reading not read; no person's analysis proficiency certified", "Public portions only"),
        ("FIN02", "financial;metrics", "Evaluating Quality of Financial Reports", "CFA Institute", "2026 Curriculum", "https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/evaluating-quality-financial-reports", "not_applicable", "public_summary", "Introduction; Learning Outcomes; Summary", "Financial reporting quality vs results quality", "RQ6", "Separate interpretation from raw facts and uncertainty", "Reporting quality and earnings/cash-flow quality are distinct analytical concepts.", "No actual company quality/fraud judgement; full paid reading not read", "Public introduction/summary only"),
        ("FIN03", "financial;metrics", "Beginners' Guide to Financial Statement", "US SEC", "2007-02-04; reviewed 2007-02-05", "https://www.sec.gov/investor/pubs/begfinstmtguide.htm", "not_applicable", "public_body", "Balance Sheets; Income Statements; Cash Flow; Footnotes; MD&A", "Financial statement educational guide", "RQ6", "balance/flow; statement_type; notes; periods", "Balances are point-in-time; income and cash flows cover periods; notes/MD&A give context.", "Educational brochure; not company accounting policy or authoritative GAAP measurement", "Relevant public body sections"),
        ("FIN04", "financial;metrics", "Non-GAAP Financial Measures C&DIs", "US SEC Division of Corporation Finance", "Page updated 2022-12-13; Q102.07 2016-05-17", "https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/non-gaap-financial-measures", "not_applicable", "selected_public_questions", "Q100.02; Q100.05; Q102.07", "SEC staff interpretations of non-GAAP measures", "RQ6", "company adjustment_definition; distinct company/project FCF", "Non-GAAP comparability requires definition; FCF lacks a uniform definition and needs clear calculation/reconciliation.", "Not legal compliance assessment; company reconciliation/input completeness still unverified", "Selected questions only"),
        ("TECH01", "schema", "JSON Schema Draft 2020-12 Core", "JSON Schema project", "2020-12", "https://json-schema.org/draft/2020-12/json-schema-core", "not_applicable", "official_spec_reference", "$defs/$ref and validation reference; conditional schema guide", "Machine-readable JSON schema", "RQ2", "Schema 2020-12; no factual correctness inference", "Structural validation is separate from semantic/source auditing.", "Semantic checks require code and source review", "Official specification/reference checked")
    ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace-generated", action="store_true")
    args = parser.parse_args()
    outputs = ["event_schema_v0.1.json", "schema_examples.jsonl", "schema_validation_cases.json", "literature_map.csv", "literature_matrix.csv", "literature_events.csv", "literature_materiality.csv", "literature_metrics.csv"]
    if not args.replace_generated:
        existing = [str(OUT / name) for name in outputs if (OUT / name).exists()]
        if existing:
            raise SystemExit("Refusing to replace existing generated files: " + ", ".join(existing))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "event_schema_v0.1.json").write_text(json.dumps(schema(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    records = examples()
    (OUT / "schema_examples.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    (OUT / "schema_validation_cases.json").write_text(json.dumps(fixtures(records), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    headers = ["reference_id", "axis", "title", "authors_or_org", "publication_version", "primary_url", "doi", "read_status", "read_sections_pages", "language_domain_task", "research_question", "design_rule", "design_implication", "transfer_limitations", "reading_limitations", "checked_at"]
    data = [list(row) + ["2026-10-05"] for row in literature()]
    for name, subset in [("literature_map.csv", data), ("literature_matrix.csv", data),
                         ("literature_events.csv", [r for r in data if "events" in r[1]]),
                         ("literature_materiality.csv", [r for r in data if "materiality" in r[1]]),
                         ("literature_metrics.csv", [r for r in data if "metrics" in r[1] or "ontology" in r[1]])]:
        with (OUT / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(headers)
            writer.writerows(subset)
    print(json.dumps({"schema_version": VERSION, "synthetic_examples": len(records), "validation_cases": len(fixtures(records)), "literature_rows": len(data), "source_supported_examples": 0, "generated": outputs}, ensure_ascii=False))


if __name__ == "__main__":
    main()
