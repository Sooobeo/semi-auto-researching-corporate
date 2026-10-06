"""Independent P04 agent agreement calculation; no project calculation imports.

Reads only the two raw annotation tables and their output contract. This is a
shared-input implementation consistency check, not human IAA or source accuracy.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


AUTHORS = ("AGENT-A", "AGENT-B")
MISSING_LABELS = {"unknown", "not_applicable", "not_assessed", "unable_to_judge", "na", "n/a"}


def encoded(value):
    """Typed JSON equality: zero is not false and numeric strings stay strings."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def missing_state(value):
    if value is None:
        return "null"
    if isinstance(value, str):
        label = value.strip().lower()
        if not label:
            return "empty_string"
        if label in MISSING_LABELS:
            return label
        if label.startswith("unknown_") or label.startswith("unresolved"):
            return "unresolved_or_unknown"
    return None


def rate(numerator, denominator):
    return numerator / denominator if denominator else None


def pair_summary(pairs):
    pairs = list(pairs)
    known = [(a, b) for a, b in pairs if missing_state(a) is None and missing_state(b) is None]
    excluded = Counter(
        f"{missing_state(a) or 'observed'}|{missing_state(b) or 'observed'}"
        for a, b in pairs if missing_state(a) is not None or missing_state(b) is not None
    )
    all_matches = sum(encoded(a) == encoded(b) for a, b in pairs)
    known_matches = sum(encoded(a) == encoded(b) for a, b in known)
    return {
        "all_pairs": len(pairs),
        "all_exact_matches": all_matches,
        "all_exact_rate": rate(all_matches, len(pairs)),
        "observed_pairs": len(known),
        "observed_exact_matches": known_matches,
        "observed_exact_rate": rate(known_matches, len(known)),
        "excluded_pairs": len(pairs) - len(known),
        "excluded_state_pairs": dict(sorted(excluded.items())),
        "missingness_disagreements": sum((missing_state(a) is None) != (missing_state(b) is None) for a, b in pairs),
        "joint_unobserved_pairs": sum(missing_state(a) is not None and missing_state(b) is not None for a, b in pairs),
    }


def interval_counts(start_a, end_a, start_b, end_b, same_context=True):
    for start, end in ((start_a, end_a), (start_b, end_b)):
        if type(start) is not int or type(end) is not int or start < 0 or end <= start:
            raise ValueError("invalid_span_bounds")
    overlap = max(0, min(end_a, end_b) - max(start_a, start_b)) if same_context else 0
    return overlap, end_a - start_a, end_b - start_b


def required_fields(row, fields, label, errors):
    for field in fields:
        if field not in row:
            errors.append(f"missing_field:{label}:{field}")


def validate(annotations, assessments, contract):
    errors = []
    grouped = {author: {} for author in AUTHORS}
    annotation_ids = {}
    fact_fields = {
        "numeric_claim": contract["numeric_fact_fields"],
        "reporting_relation": contract["relation_fact_fields"],
    }
    for index, row in enumerate(annotations):
        tag = str(row.get("annotation_id", f"row_{index}"))
        required_fields(row, contract["required_top_level"], tag, errors)
        author, item = row.get("annotator_id"), row.get("item_id")
        if author not in grouped:
            errors.append(f"unexpected_author:{tag}:{author}")
            continue
        if not isinstance(item, str) or not item:
            errors.append(f"invalid_item_id:{tag}")
            continue
        if item in grouped[author]:
            errors.append(f"duplicate_item:{author}:{item}")
        grouped[author][item] = row
        ann_id = row.get("annotation_id")
        if ann_id in annotation_ids:
            errors.append(f"duplicate_annotation_id:{ann_id}")
        annotation_ids[ann_id] = row
        if row.get("annotator_kind") != "agent":
            errors.append(f"nonagent_record:{tag}")
        if row.get("guide_version") != contract["guide_version"]:
            errors.append(f"guide_mismatch:{tag}")
        item_type, facts = row.get("item_type"), row.get("facts")
        if item_type not in fact_fields or not isinstance(facts, dict):
            errors.append(f"invalid_item_type_or_facts:{tag}")
            continue
        required_fields(facts, fact_fields[item_type], tag + ".facts", errors)
        own_id = "source_claim_id" if item_type == "numeric_claim" else "source_relation_id"
        if facts.get(own_id) != item:
            errors.append(f"item_source_identity_mismatch:{tag}")
        doc_id = facts.get("doc_id")
        if isinstance(doc_id, str) and not item.startswith(doc_id + "-"):
            errors.append(f"item_document_identity_mismatch:{tag}")
        provenance = row.get("provenance", {})
        if not isinstance(provenance, dict):
            errors.append(f"invalid_provenance:{tag}")
        else:
            required_fields(provenance, contract.get("provenance_required_fields", []), tag + ".provenance", errors)
            source_ref = provenance.get("source_record_ref", "")
            if not isinstance(source_ref, str) or not source_ref.endswith("#" + item):
                errors.append(f"provenance_identity_mismatch:{tag}")
        if item_type == "numeric_claim" and "value_span_start" in facts and "value_span_end" in facts:
            try:
                interval_counts(facts["value_span_start"], facts["value_span_end"], facts["value_span_start"], facts["value_span_end"])
            except ValueError:
                errors.append(f"invalid_span_bounds:{tag}")

    left_items, right_items = set(grouped[AUTHORS[0]]), set(grouped[AUTHORS[1]])
    if left_items != right_items:
        errors.append("unequal_item_sets")
        for author, other in ((AUTHORS[0], right_items), (AUTHORS[1], left_items)):
            for item in sorted(other - set(grouped[author])):
                errors.append(f"missing_peer:{author}:{item}")
    for item in sorted(left_items & right_items):
        left, right = (grouped[author][item] for author in AUTHORS)
        for field in ("item_type", "guide_version", "registry_version"):
            if left.get(field) != right.get(field):
                errors.append(f"pair_identity_mismatch:{item}:{field}")

    assessments_grouped = {author: {} for author in AUTHORS}
    assessment_ids = set()
    question_ids = set(contract["assessment_response_enums"])
    for index, row in enumerate(assessments):
        tag = str(row.get("assessment_id", f"assessment_row_{index}"))
        required_fields(row, contract["assessment_file_required_top_level"], tag, errors)
        if row.get("assessment_id") in assessment_ids:
            errors.append(f"duplicate_assessment_id:{tag}")
        assessment_ids.add(row.get("assessment_id"))
        author, item = row.get("annotator_id"), row.get("item_id")
        if author not in assessments_grouped:
            errors.append(f"unexpected_assessment_author:{tag}")
            continue
        if item in assessments_grouped[author]:
            errors.append(f"duplicate_assessment_item:{author}:{item}")
        assessments_grouped[author][item] = row
        parent = annotation_ids.get(row.get("annotation_id"))
        if parent is None:
            errors.append(f"missing_annotation_parent:{tag}")
        elif parent.get("annotator_id") != author or parent.get("item_id") != item:
            errors.append(f"assessment_parent_identity_mismatch:{tag}")
        if row.get("annotator_kind") != "agent":
            errors.append(f"nonagent_assessment:{tag}")
        if row.get("guide_version") != contract["guide_version"]:
            errors.append(f"assessment_guide_mismatch:{tag}")
        questions = row.get("questions", [])
        if not isinstance(questions, list) or any(not isinstance(q, dict) for q in questions):
            errors.append(f"invalid_questions:{tag}")
            continue
        ids = [q.get("question_id") for q in questions]
        if set(ids) != question_ids or len(ids) != len(set(ids)):
            errors.append(f"missing_or_duplicate_questions:{tag}")
        for q in questions:
            if "response" not in q:
                errors.append(f"missing_question_response:{tag}:{q.get('question_id')}")
            elif q.get("response") not in contract["assessment_response_enums"].get(q.get("question_id"), []):
                errors.append(f"invalid_question_response:{tag}:{q.get('question_id')}")
    for author in AUTHORS:
        if set(assessments_grouped[author]) != set(grouped[author]):
            errors.append(f"assessment_item_set_mismatch:{author}")
    return sorted(set(errors)), grouped, assessments_grouped


def confusion(pairs):
    counts = Counter((encoded(a), encoded(b)) for a, b in pairs)
    return [{"a": json.loads(a), "b": json.loads(b), "count": n} for (a, b), n in sorted(counts.items())]


def calculate(annotations, assessments, contract):
    errors, groups, assessment_groups = validate(annotations, assessments, contract)
    if errors:
        raise ValueError("\n".join(errors))
    items = sorted(groups[AUTHORS[0]])
    result = {"fact_groups": {}, "assessment_questions": {}, "disagreements": []}
    for item_type, field_key in (("numeric_claim", "numeric_fact_fields"), ("reporting_relation", "relation_fact_fields")):
        type_items = [i for i in items if groups[AUTHORS[0]][i]["item_type"] == item_type]
        fields = contract[field_key]
        field_pairs = {field: [] for field in fields}
        whole_exact = known_projection_exact = fully_observed = fully_observed_exact = 0
        any_observed_items = 0
        for item in type_items:
            left, right = (groups[author][item]["facts"] for author in AUTHORS)
            pairs = [(left[field], right[field]) for field in fields]
            whole_exact += all(encoded(a) == encoded(b) for a, b in pairs)
            known_pairs = [(a, b) for a, b in pairs if missing_state(a) is None and missing_state(b) is None]
            any_observed_items += bool(known_pairs)
            known_projection_exact += bool(known_pairs) and all(encoded(a) == encoded(b) for a, b in known_pairs)
            complete = all(missing_state(a) is None and missing_state(b) is None for a, b in pairs)
            fully_observed += complete
            fully_observed_exact += complete and all(encoded(a) == encoded(b) for a, b in pairs)
            for field, (a, b) in zip(fields, pairs):
                field_pairs[field].append((a, b))
                if encoded(a) != encoded(b):
                    result["disagreements"].append({"item_id": item, "field": "facts." + field, "a": a, "b": b})
        result["fact_groups"][item_type] = {
            "item_pairs": len(type_items),
            "field_count": len(fields),
            "fields": {field: pair_summary(pairs) for field, pairs in field_pairs.items()},
            "micro_fields": pair_summary(pair for pairs in field_pairs.values() for pair in pairs),
            "whole_tuple_including_missing": {"matches": whole_exact, "denominator": len(type_items), "rate": rate(whole_exact, len(type_items))},
            "observed_projection_tuple": {"matches": known_projection_exact, "denominator": any_observed_items, "rate": rate(known_projection_exact, any_observed_items), "policy": "Only fields observed on both sides; not a fully observed tuple; asymmetric missingness remains separately reported."},
            "fully_observed_tuple": {"matches": fully_observed_exact, "denominator": fully_observed, "rate": rate(fully_observed_exact, fully_observed), "excluded_incomplete_items": len(type_items) - fully_observed},
        }

    span_rows = []
    for item in items:
        left, right = (groups[author][item] for author in AUTHORS)
        if left["item_type"] != "numeric_claim":
            continue
        a, b = left["facts"], right["facts"]
        same_context = (
            all(a[field] == b[field] for field in ("source_claim_id", "doc_id", "revision_id"))
            and left["provenance"]["doc_sha256"] == right["provenance"]["doc_sha256"]
            and left["provenance"]["offset_basis"] == right["provenance"]["offset_basis"]
            and set(left["evidence_refs"]) == set(right["evidence_refs"])
        )
        overlap, length_a, length_b = interval_counts(a["value_span_start"], a["value_span_end"], b["value_span_start"], b["value_span_end"], same_context)
        span_rows.append({"item_id": item, "same_context": same_context, "exact": same_context and (a["value_span_start"], a["value_span_end"]) == (b["value_span_start"], b["value_span_end"]), "intersection_code_points": overlap, "a_code_points": length_a, "b_code_points": length_b, "character_overlap_f1": rate(2 * overlap, length_a + length_b)})
    overlap = sum(row["intersection_code_points"] for row in span_rows)
    length_a = sum(row["a_code_points"] for row in span_rows)
    length_b = sum(row["b_code_points"] for row in span_rows)
    result["spans"] = {
        "denominator": len(span_rows), "exact_matches": sum(row["exact"] for row in span_rows),
        "exact_rate": rate(sum(row["exact"] for row in span_rows), len(span_rows)),
        "context_mismatches": sum(not row["same_context"] for row in span_rows),
        "intersection_code_points": overlap, "a_code_points": length_a, "b_code_points": length_b,
        "micro_character_overlap_f1": rate(2 * overlap, length_a + length_b),
        "macro_character_overlap_f1": rate(sum(row["character_overlap_f1"] for row in span_rows), len(span_rows)),
        "policy": "Paired numeric value spans within a shared source item, revision, hash, evidence set and Unicode code-point basis; no source HTML reread or span truth validation.",
        "items": span_rows,
    }
    for question_id in sorted(contract["assessment_response_enums"]):
        pairs = []
        for item in items:
            rows = [assessment_groups[author][item] for author in AUTHORS]
            a, b = [next(q["response"] for q in row["questions"] if q["question_id"] == question_id) for row in rows]
            pairs.append((a, b))
            if encoded(a) != encoded(b):
                result["disagreements"].append({"item_id": item, "field": question_id, "a": a, "b": b})
        result["assessment_questions"][question_id] = {**pair_summary(pairs), "confusion": confusion(pairs)}
    readiness = [(assessment_groups[AUTHORS[0]][i]["review_readiness"], assessment_groups[AUTHORS[1]][i]["review_readiness"]) for i in items]
    result["review_readiness"] = {**pair_summary(readiness), "confusion": confusion(readiness)}
    result["counts"] = {
        "annotation_rows": len(annotations), "assessment_rows": len(assessments), "paired_items": len(items),
        "numeric_claim_items": sum(groups[AUTHORS[0]][i]["item_type"] == "numeric_claim" for i in items),
        "relation_items": sum(groups[AUTHORS[0]][i]["item_type"] == "reporting_relation" for i in items),
        "unique_source_claim_ids": len({groups[AUTHORS[0]][i]["facts"]["source_claim_id"] for i in items}),
        "documents": len({groups[AUTHORS[0]][i]["facts"]["doc_id"] for i in items}),
        "events": len({groups[AUTHORS[0]][i]["facts"]["event_id"] for i in items}),
        "families": len({groups[AUTHORS[0]][i]["facts"]["event_family_id"] for i in items}),
        "human_annotation_rows": sum(row.get("annotator_kind") == "human" for row in annotations),
        "human_paired_items": 0,
    }
    return result


def self_checks(annotations, assessments, contract):
    checks = []

    def check(name, passed):
        checks.append({"name": name, "passed": bool(passed)})

    def rejected(name, mutate, error_prefix):
        a, s = copy.deepcopy(annotations), copy.deepcopy(assessments)
        mutate(a, s)
        errors, _, _ = validate(a, s, contract)
        check(name, any(error.startswith(error_prefix) for error in errors))

    rejected("duplicate_annotation_is_rejected", lambda a, s: a.append(copy.deepcopy(a[0])), "duplicate_item:")
    rejected("missing_peer_is_rejected", lambda a, s: a.pop(), "missing_peer:")

    def swap_items(a, _):
        a[0]["item_id"], a[1]["item_id"] = a[1]["item_id"], a[0]["item_id"]

    rejected("swapped_item_ids_are_rejected", swap_items, "item_source_identity_mismatch:")
    rejected("dropped_fact_field_is_rejected", lambda a, s: a[0]["facts"].pop("numeric_value"), "missing_field:")
    rejected("dropped_top_level_field_is_rejected", lambda a, s: a[0].pop("evidence_refs"), "missing_field:")
    rejected("missing_assessment_peer_is_rejected", lambda a, s: s.pop(), "assessment_item_set_mismatch:")
    rejected("duplicate_assessment_is_rejected", lambda a, s: s.append(copy.deepcopy(s[0])), "duplicate_assessment_item:")

    def swap_parents(_, s):
        s[0]["annotation_id"], s[1]["annotation_id"] = s[1]["annotation_id"], s[0]["annotation_id"]

    rejected("swapped_assessment_parents_are_rejected", swap_parents, "assessment_parent_identity_mismatch:")
    rejected("dropped_question_is_rejected", lambda a, s: s[0]["questions"].pop(), "missing_or_duplicate_questions:")
    rejected("duplicate_question_is_rejected", lambda a, s: s[0]["questions"].append(copy.deepcopy(s[0]["questions"][0])), "missing_or_duplicate_questions:")
    rejected("missing_question_response_is_rejected", lambda a, s: s[0]["questions"][0].pop("response"), "missing_question_response:")
    summary = pair_summary([(None, None), ("unknown", "unknown"), ("unresolved_scope", "unresolved_scope"), (0, 0), (False, False), ("1", "2"), (None, "known")])
    check("null_unknown_unresolved_excluded_but_zero_false_observed", summary["all_pairs"] == 7 and summary["all_exact_matches"] == 5 and summary["observed_pairs"] == 3 and summary["observed_exact_matches"] == 2 and summary["missingness_disagreements"] == 1)
    undefined = pair_summary([(None, None), ("unknown", "unknown")])
    check("all_missing_has_null_observed_score", undefined["observed_pairs"] == 0 and undefined["observed_exact_rate"] is None)
    check("typed_zero_and_false_differ", pair_summary([(0, False)])["all_exact_matches"] == 0)
    check("decimal_representation_not_silently_coerced", pair_summary([("1.0", "1.00")])["all_exact_matches"] == 0)
    check("partial_span_overlap_half", interval_counts(0, 4, 2, 6) == (2, 4, 4))
    check("disjoint_span_overlap_zero", interval_counts(0, 2, 2, 5) == (0, 2, 3))
    check("wrong_source_context_has_zero_overlap", interval_counts(0, 4, 0, 4, False) == (0, 4, 4))
    try:
        interval_counts(0, 0, 0, 1)
    except ValueError:
        check("empty_span_rejected", True)
    else:
        check("empty_span_rejected", False)
    try:
        interval_counts(False, 1, 0, 1)
    except ValueError:
        check("boolean_offset_rejected", True)
    else:
        check("boolean_offset_rejected", False)
    known_summary = pair_summary([("yes", "yes"), ("yes", "no"), ("no", "no")])
    check("ordinary_mismatch_score_two_thirds", known_summary["observed_exact_matches"] == 2 and known_summary["observed_pairs"] == 3 and known_summary["observed_exact_rate"] == 2 / 3)
    check("confusion_preserves_off_diagonal", confusion([("yes", "yes"), ("yes", "no")]) == [{"a": "yes", "b": "no", "count": 1}, {"a": "yes", "b": "yes", "count": 1}])
    return checks


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, default=Path("artifacts/us_equity/p3/annotations_raw.jsonl"))
    parser.add_argument("--assessments", type=Path, default=Path("artifacts/us_equity/p3/assessments_raw.jsonl"))
    parser.add_argument("--contract", type=Path, default=Path("artifacts/us_equity/p3/annotation_output_contract_v1_2.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/us_equity/p3/stage_reviews/stage_04_independent.json"))
    parser.add_argument("--replace", action="store_true", help="Explicitly replace this script's existing report only.")
    args = parser.parse_args()
    if args.output.exists() and not args.replace:
        parser.error("output exists; choose a new output or explicitly use --replace")
    inputs = [args.annotations, args.assessments, args.contract]
    if args.output.resolve() in {p.resolve() for p in inputs}:
        parser.error("output must not overwrite an input")
    hashes_before = {str(path).replace("\\", "/"): digest(path) for path in inputs}
    annotations, assessments = read_jsonl(args.annotations), read_jsonl(args.assessments)
    contract = json.loads(args.contract.read_text(encoding="utf-8-sig"))
    errors, _, _ = validate(annotations, assessments, contract)
    checks = self_checks(annotations, assessments, contract)
    result = calculate(annotations, assessments, contract) if not errors else None
    hashes_after = {str(path).replace("\\", "/"): digest(path) for path in inputs}
    passed = not errors and all(check["passed"] for check in checks) and hashes_before == hashes_after
    report = {
        "stage": 4, "reviewer": "independent_agent_standard_library_implementation",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "gate": "passed_with_explicit_limitations" if passed else "failed",
        "source_input_hashes": hashes_before, "inputs_unchanged": hashes_before == hashes_after,
        "code_sha256": digest(Path(__file__)),
        "implementation_independence": "No imports from the project's agreement/annotation implementation and no root agreement results read before this calculation.",
        "validation_errors": errors,
        "self_checks": {"passed": sum(c["passed"] for c in checks), "total": len(checks), "cases": checks},
        "result": result,
        "human_iaa": {"annotation_rows": 0, "paired_items": 0, "score": None, "reason": "No independent human annotations; agent outputs cannot estimate human IAA."},
        "interpretation": "Agreement of agent-authored deterministic outputs on the same preselected packets, guide and curator metadata; implementation consistency only, not extraction accuracy, independent human agreement, or external fact verification.",
        "missing_policy": "All-state exact is descriptive only. Observed exact excludes either-side null, empty, unknown, not_applicable, not_assessed, unable_to_judge, and unresolved-prefixed labels. Empty lists and false/zero remain observed selected-table assertions. Fully observed tuples require every contract fact field observed on both sides.",
        "limitations": ["Adaptation data with disclosed future-context guide exposure", "Original DOM not reopened; paired span agreement does not establish source truth", "Constant-label fields and MQ responses cannot establish discriminative annotation quality", "No kappa/alpha inferred from deterministic shared-input outputs; no human coefficients", "Practice-exposed items are not independent test samples"],
        "next_stage_authorized_by_this_report": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": report["gate"], "self_checks": report["self_checks"]["passed"], "self_check_total": len(checks), "counts": result["counts"] if result else None, "output": str(args.output)}, ensure_ascii=False))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
