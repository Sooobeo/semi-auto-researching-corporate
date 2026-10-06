"""Independently audit P04 split lineage without opening reserved source content.

No project audit imports, network calls, source HTML reads, or gold creation.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path


SPLIT_FIELDS = "row_id row_kind item_id item_type doc_id revision_id event_family_id event_id company_id leakage_group_id split exposure_status published_date time_precision observed_at source_hash human_gold test_eligible annotation_ids exclusion_reason split_version".split()
AUTHORS = {"AGENT-A", "AGENT-B"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def is_iso_date(value):
    try:
        return isinstance(value, str) and date.fromisoformat(value).isoformat() == value
    except (ValueError, TypeError):
        return False


def connected_components(nodes, edges):
    adjacency = {node: set() for node in nodes}
    for left, right in edges:
        if left in adjacency and right in adjacency:
            adjacency[left].add(right)
            adjacency[right].add(left)
    unseen, components = set(nodes), []
    while unseen:
        pending, component = [min(unseen)], set()
        while pending:
            node = pending.pop()
            if node in component:
                continue
            component.add(node)
            unseen.discard(node)
            pending.extend(adjacency[node] - component)
        components.append(sorted(component))
    return sorted(components, key=lambda values: (-len(values), values))


def audit(bundle):
    rows, policy = bundle["split"], bundle["policy"]
    source_docs, exposure, families = bundle["source_docs"], bundle["exposure"], bundle["families"]
    links, dependencies = bundle["links"], bundle["dependencies"]
    reserved, reservation = bundle["reserved"], bundle["reservation"]
    annotations = bundle["annotations"]
    errors = []

    def require(condition, code, detail=""):
        if not condition:
            errors.append(code + (":" + str(detail) if detail else ""))

    docs = {row["doc_id"]: row for row in source_docs}
    require(len(docs) == len(source_docs), "duplicate_source_document")
    reserved_id = reserved["doc_id"]
    require(reserved_id not in docs, "reservation_already_development_document")
    all_docs = {**docs, reserved_id: reserved}
    exposed_docs = {row["doc_id"] for row in exposure}
    require(exposed_docs == set(docs), "exposure_document_set_mismatch")
    for row in exposure:
        original = docs.get(row["doc_id"], {})
        require(row.get("source_hash") == original.get("sha256") and row.get("revision_id") == original.get("revision_id") and row.get("event_family_id") == original.get("event_family_id"), "exposure_source_identity_mismatch", row["doc_id"])
    support_ids = {row["doc_id"] for row in exposure if row["support_only"] == "true"}
    require(len(support_ids) == 1, "unexpected_support_document_count")
    support_id = next(iter(support_ids), "")
    expected_links = {row["item_id"]: row for row in links}
    require(len(expected_links) == len(links), "duplicate_event_claim_link")
    family_map = {row["event_family_id"]: row for row in families}
    source_groups = {row["leakage_group_id"] for row in families}
    require(len(source_groups) == 1, "development_family_group_lineage_mismatch")
    development_group = next(iter(source_groups), "")
    require(policy.get("development_leakage_group") == development_group, "group_id_changed_without_lineage")
    require(policy.get("reserved_group_status") == "provisional_not_proof_of_independence", "reserved_group_certified_independent")

    by_id, document_rows, item_rows = {}, {}, {}
    for row in rows:
        row_id = row.get("row_id", "MISSING")
        require(all(field in row for field in SPLIT_FIELDS), "missing_split_field", row_id)
        require(row_id not in by_id, "duplicate_split_row", row_id)
        by_id[row_id] = row
        require(row.get("split") in {"adaptation", "reserved_unlabeled"}, "evaluation_allocation_without_independent_gold", row_id)
        require(row.get("human_gold") == "false", "unsupported_human_gold", row_id)
        require(row.get("test_eligible") == "false", "unsupported_test_eligibility", row_id)
        require(row.get("exclusion_reason") not in {None, ""}, "missing_exclusion_reason", row_id)
        require(row.get("split_version") == policy.get("version"), "split_version_mismatch", row_id)
        require(row.get("company_id") == "US-MSFT", "nonselected_or_legacy_company", row_id)
        doc_id = row.get("doc_id")
        if doc_id not in all_docs:
            require(False, "unknown_source_document", row_id)
            continue
        source = all_docs[doc_id]
        for field, source_field in (("revision_id", "revision_id"), ("source_hash", "sha256"), ("published_date", "published_date"), ("time_precision", "time_precision"), ("observed_at", "observed_at")):
            require(row.get(field) == (source.get(source_field) or ""), "source_metadata_mismatch", row_id + "." + field)
        if source.get("time_precision") == "unknown":
            require(not row.get("published_date"), "unknown_publication_imputed", row_id)
        elif source.get("time_precision") == "date":
            require(is_iso_date(row.get("published_date")), "invalid_date_precision", row_id)
        if doc_id in exposed_docs:
            require(row.get("split") == "adaptation", "exposed_document_outside_adaptation", row_id)
            require(row.get("exposure_status") == "development_exposed", "exposure_erased", row_id)
            require(row.get("leakage_group_id") == development_group, "development_group_mismatch", row_id)
        if doc_id == reserved_id:
            require(row.get("split") == "reserved_unlabeled", "reservation_promoted", row_id)
            require(row.get("exposure_status") == "metadata_only_inspected", "reserved_exposure_misrepresented", row_id)
            require(row.get("leakage_group_id") == policy.get("reserved_leakage_group"), "reserved_group_mismatch", row_id)
            require(row.get("row_kind") == "document" and not row.get("annotation_ids"), "reserved_labels_created", row_id)
        if row.get("row_kind") == "document":
            require(doc_id not in document_rows, "duplicate_document_row", doc_id)
            document_rows[doc_id] = row
            require(row_id == "DOC:" + doc_id, "document_row_identity_mismatch", row_id)
            require(not row.get("item_id") and not row.get("item_type") and not row.get("annotation_ids"), "document_claim_count_inflation", row_id)
            expected_family = source.get("event_family_id") or ""
            require(row.get("event_family_id") == expected_family, "document_family_mismatch", row_id)
            require(row.get("event_id") == expected_family, "document_anchor_mismatch", row_id)
        elif row.get("row_kind") == "annotation_item":
            item = row.get("item_id")
            require(item not in item_rows, "duplicate_annotation_item_row", item)
            item_rows[item] = row
            require(row_id == "ITEM:" + str(item), "item_row_identity_mismatch", row_id)
            if item not in expected_links:
                require(False, "unknown_annotation_item", item)
            else:
                for field in ("item_type", "doc_id", "event_id", "event_family_id"):
                    require(row.get(field) == expected_links[item].get(field), "event_claim_link_mismatch", str(item) + "." + field)
        else:
            require(False, "unknown_row_kind", row_id)
    require(set(document_rows) == set(all_docs), "document_coverage_mismatch")
    require(set(item_rows) == set(expected_links), "annotation_item_coverage_mismatch")
    require(len(rows) == len(all_docs) + len(expected_links), "row_denominator_mismatch")

    ann_by_item, ann_ids = defaultdict(list), {}
    for row in annotations:
        annotation_id, item = row["annotation_id"], row["item_id"]
        require(annotation_id not in ann_ids, "duplicate_annotation_id", annotation_id)
        ann_ids[annotation_id] = row
        ann_by_item[item].append(row)
        require(row.get("annotator_kind") == "agent", "annotation_author_kind_changed", annotation_id)
        require(row.get("facts", {}).get("doc_id") != reserved_id, "reserved_annotation_discovered", annotation_id)
    require(set(ann_by_item) == set(expected_links), "raw_annotation_item_set_mismatch")
    for item, row in item_rows.items():
        paired = ann_by_item.get(item, [])
        require(len(paired) == 2 and {a["annotator_id"] for a in paired} == AUTHORS, "independent_agent_pair_missing", item)
        expected_ids = {a["annotation_id"] for a in paired}
        listed_ids = row.get("annotation_ids", "").split(";")
        require(set(listed_ids) == expected_ids and len(listed_ids) == len(expected_ids), "annotation_id_reference_mismatch", item)
        for annotation in paired:
            facts = annotation["facts"]
            for field in ("doc_id", "revision_id", "event_id", "event_family_id", "company_id"):
                require(row.get(field) == facts.get(field), "annotation_metadata_link_mismatch", item + "." + field)
            if annotation["item_type"] == "numeric_claim":
                require(facts.get("source_claim_id") == item, "numeric_source_claim_identity_mismatch", item)
                if facts.get("period_kind") == "duration":
                    start, end = facts.get("period_start"), facts.get("period_end")
                    valid = is_iso_date(start) and is_iso_date(end) and start <= end
                    require(valid, "unknown_or_invalid_reference_period", item)
                    if valid:
                        require(facts.get("duration_days") == (date.fromisoformat(end) - date.fromisoformat(start)).days + 1, "duration_period_mismatch", item)
                    require(facts.get("as_of_date") is None, "duration_instant_period_mixed", item)
                elif facts.get("period_kind") == "instant":
                    require(is_iso_date(facts.get("as_of_date")), "unknown_instant_reference_date", item)
                    require(facts.get("period_start") is None and facts.get("period_end") is None, "instant_duration_period_mixed", item)
                else:
                    require(False, "unknown_period_kind", item)
            else:
                linked_claim = facts.get("source_claim_id")
                peers = [a for a in ann_by_item.get(linked_claim, []) if a["annotator_id"] == annotation["annotator_id"] and a["item_type"] == "numeric_claim"]
                require(len(peers) == 1, "relation_claim_reference_missing", item)
                if peers:
                    numeric = peers[0]["facts"]
                    for field in ("doc_id", "event_id", "event_family_id", "company_id", "scope_id"):
                        require(facts.get(field) == numeric.get(field), "relation_claim_identity_mismatch", item + "." + field)
                    require(facts.get("reference_period_start") == numeric.get("period_start") and facts.get("reference_period_end") == numeric.get("period_end"), "relation_claim_period_mismatch", item)
                require(all(facts.get(field) is None for field in ("effective_period_start", "effective_period_end", "valid_from", "valid_to")), "reporting_period_promoted_to_business_validity", item)
    graph_edges = []
    logical_rows = {doc_id: row for doc_id, row in document_rows.items()}
    logical_rows.update(item_rows)
    for item, row in item_rows.items():
        graph_edges.append((item, row["doc_id"]))
    family_members = defaultdict(list)
    for logical_id, row in logical_rows.items():
        if row["event_family_id"]:
            family_members[row["event_family_id"]].append(logical_id)
    for members in family_members.values():
        graph_edges.extend((members[0], node) for node in members[1:])
    scope_targets, overlap_count, overlap_pairs = set(), 0, set()
    seen_edge_ids = set()
    for edge in dependencies:
        left, right = edge["from_id"], edge["to_id"]
        require(edge["edge_id"] not in seen_edge_ids, "duplicate_dependency_edge_id", edge["edge_id"])
        seen_edge_ids.add(edge["edge_id"])
        require(left in logical_rows and right in logical_rows, "dependency_endpoint_missing", edge["edge_id"])
        graph_edges.append((left, right))
        if edge["edge_type"] == "retrospective_scope_dependency":
            scope_targets.add(right)
            require(left == support_id, "unexpected_scope_support_document", edge["edge_id"])
            require("exclude_dependency_from_2024_2025_asof_packets" in edge.get("consequence", ""), "future_scope_dependency_allowed", edge["edge_id"])
            for annotation in ann_by_item.get(right, []):
                require(annotation["facts"].get("scope_status_as_of") == "unresolved_retrospective_dependency", "future_scope_asof_fact_leak", annotation["annotation_id"])
                require(support_id in annotation.get("provenance", {}).get("availability_dependency_refs", []), "scope_dependency_lineage_dropped", annotation["annotation_id"])
        elif edge["edge_type"] == "representation_overlap":
            overlap_count += 1
            overlap_pairs.add(tuple(sorted((left, right))))
            require(edge.get("same_family") == "false", "independent_release_families_merged", edge["edge_id"])
        else:
            require(False, "unsupported_dependency_edge_type", edge["edge_id"])
    numeric_records = {
        item: paired[0] for item, paired in ann_by_item.items()
        if paired and paired[0]["item_type"] == "numeric_claim"
    }
    expected_scope_targets = {
        item for item, annotation in numeric_records.items()
        if support_id in annotation.get("provenance", {}).get("availability_dependency_refs", [])
    }
    require(scope_targets == expected_scope_targets, "scope_dependency_edge_coverage_mismatch")
    expected_overlap_pairs = set()
    numeric_items = sorted(numeric_records)
    for position, left in enumerate(numeric_items):
        a = numeric_records[left]["facts"]
        for right in numeric_items[position + 1:]:
            b = numeric_records[right]["facts"]
            if (a.get("doc_id") != b.get("doc_id")
                    and a.get("definition_version") != b.get("definition_version")
                    and all(a.get(field) == b.get(field) for field in ("company_id", "scope_id", "metric_id", "period_kind", "period_start", "period_end", "as_of_date"))):
                expected_overlap_pairs.add((left, right))
    require(overlap_pairs == expected_overlap_pairs and overlap_count == len(overlap_pairs), "representation_overlap_edge_coverage_mismatch")
    for component in connected_components(logical_rows, graph_edges):
        split_set = {logical_rows[node]["split"] for node in component}
        group_set = {logical_rows[node]["leakage_group_id"] for node in component}
        require(len(split_set) == 1, "connected_lineage_crosses_splits", component[0])
        require(len(group_set) == 1, "connected_lineage_crosses_groups", component[0])
    for family, members in family_members.items():
        require(len({logical_rows[node]["split"] for node in members}) == 1, "family_crosses_splits", family)

    support_policy, reserved_policy = policy.get("support_document", {}), policy.get("reserved_document", {})
    require(support_policy.get("doc_id") == support_id and support_policy.get("historical_eligible") is False, "support_historical_eligibility_invalid")
    require(support_policy.get("published_date") is None and support_policy.get("time_precision") == "unknown", "support_unknown_publication_imputed")
    require(support_policy.get("event_family_id") is None and support_policy.get("event_quota") == 0, "support_counted_as_announcement")
    for field in ("labels_created", "test_eligible", "source_prose_exposed", "numeric_values_exposed", "parser_adaptation_performed", "untouched_test_claimed", "comparison_overlap_audited"):
        require(reserved_policy.get(field) is False, "reserved_policy_unjustified_promotion", field)
    require(reserved_policy.get("doc_id") == reserved_id, "reserved_policy_doc_mismatch")
    require(reserved_policy.get("summary_sha256") == bundle["reservation_sha256"], "reservation_summary_hash_mismatch")
    for field in ("values_exposed", "source_prose_exposed", "labels_created", "untouched_test_claimed", "parser_adaptation_performed"):
        require(reservation.get(field) is False, "reservation_exposure_state_changed", field)
    require(reservation.get("doc_id") == reserved_id and reservation.get("sha256") == reserved.get("sha256"), "reservation_identity_mismatch")
    chronology = policy.get("chronology", {})
    release_dates = sorted(row["published_date"] for row in source_docs if row.get("event_family_id"))
    require(chronology.get("development_release_dates") == release_dates, "development_chronology_mismatch")
    boundary = max(release_dates) if release_dates else None
    require(chronology.get("candidate_boundary_after") == boundary, "candidate_boundary_mismatch")
    require(chronology.get("candidate_published_date") == reserved.get("published_date"), "candidate_publication_mismatch")
    require(is_iso_date(reserved.get("published_date")) and bool(boundary) and reserved["published_date"] > boundary, "candidate_not_after_development")
    require(chronology.get("train_dev_test_boundaries") is None, "evaluation_boundaries_unjustifiably_fixed")
    require(policy.get("legacy_korean_inputs") == [], "legacy_korean_inputs_present")
    require(not any(bundle["gold_line_counts"].values()), "unsupported_gold_rows_present")
    counts = {
        "rows": len(rows), "annotation_items": len(item_rows),
        "source_numeric_claims": len({a["facts"]["source_claim_id"] for a in annotations}),
        "reporting_relations": sum(row["item_type"] == "reporting_relation" for row in item_rows.values()),
        "documents": len(document_rows), "adaptation_rows": sum(row.get("split") == "adaptation" for row in rows),
        "reserved_rows": sum(row.get("split") == "reserved_unlabeled" for row in rows),
        "adaptation_documents": sum(row["split"] == "adaptation" for row in document_rows.values()),
        "reserved_documents": sum(row["split"] == "reserved_unlabeled" for row in document_rows.values()),
        "labeled_development_families": len({row["event_family_id"] for row in item_rows.values()}),
        "reserved_unlabeled_families": len({row["event_family_id"] for row in document_rows.values() if row["split"] == "reserved_unlabeled"}),
        "human_gold": sum(bundle["gold_line_counts"].values()),
        "train_items": sum(row["split"] == "train" for row in item_rows.values()),
        "dev_items": sum(row["split"] == "dev" for row in item_rows.values()),
        "test_items": sum(row["split"] == "test" for row in item_rows.values()),
    }
    require(policy.get("counts") == counts, "policy_count_mismatch")
    components = connected_components(logical_rows, graph_edges)
    return {
        "errors": sorted(set(errors)), "counts": counts,
        "lineage_components": [{"node_count": len(nodes), "splits": sorted({logical_rows[node]["split"] for node in nodes}), "groups": sorted({logical_rows[node]["leakage_group_id"] for node in nodes}), "nodes": nodes} for nodes in components],
        "scope_dependency_claims": len(scope_targets), "representation_overlap_edges": overlap_count,
        "relation_source_claim_links": sum(a["item_type"] == "reporting_relation" for a in annotations) // 2,
        "candidate_boundary_after": boundary, "candidate_published_date": reserved.get("published_date"),
        "gold_file_line_counts": bundle["gold_line_counts"],
    }


def negative_checks(bundle):
    checks = []

    def run(name, mutation, expected_prefix):
        altered = copy.deepcopy(bundle)
        mutation(altered)
        errors = audit(altered)["errors"]
        checks.append({"name": name, "passed": any(error.startswith(expected_prefix) for error in errors), "expected_error": expected_prefix})

    def item_row(data):
        return next(row for row in data["split"] if row["row_kind"] == "annotation_item")

    def support_row(data):
        return next(row for row in data["split"] if row["doc_id"] == data["policy"]["support_document"]["doc_id"])

    def reserved_row(data):
        return next(row for row in data["split"] if row["doc_id"] == data["reserved"]["doc_id"])

    run("duplicate_manifest_row_rejected", lambda d: d["split"].append(copy.deepcopy(d["split"][0])), "duplicate_split_row")
    run("missing_manifest_item_rejected", lambda d: d["split"].remove(item_row(d)), "annotation_item_coverage_mismatch")
    run("exposed_item_in_test_rejected", lambda d: item_row(d).__setitem__("split", "test"), "exposed_document_outside_adaptation")
    run("family_cross_split_rejected", lambda d: item_row(d).__setitem__("split", "test"), "family_crosses_splits")
    run("graph_group_split_rejected", lambda d: item_row(d).__setitem__("leakage_group_id", "UNRELATED"), "connected_lineage_crosses_groups")
    run("exposure_status_erasure_rejected", lambda d: item_row(d).__setitem__("exposure_status", "untouched"), "exposure_erased")
    run("agent_label_marked_human_gold_rejected", lambda d: item_row(d).__setitem__("human_gold", "true"), "unsupported_human_gold")
    run("invented_gold_file_row_rejected", lambda d: d["gold_line_counts"].__setitem__("gold_events.jsonl", 1), "unsupported_gold_rows_present")
    run("reserved_candidate_promoted_to_test_rejected", lambda d: reserved_row(d).__setitem__("split", "test"), "reservation_promoted")
    run("reserved_candidate_test_eligible_rejected", lambda d: reserved_row(d).__setitem__("test_eligible", "true"), "unsupported_test_eligibility")
    run("false_overlap_audit_claim_rejected", lambda d: d["policy"]["reserved_document"].__setitem__("comparison_overlap_audited", True), "reserved_policy_unjustified_promotion")
    run("unknown_source_publication_imputed_rejected", lambda d: support_row(d).__setitem__("published_date", "2025-07-30"), "unknown_publication_imputed")
    run("support_source_asof_eligibility_rejected", lambda d: d["policy"]["support_document"].__setitem__("historical_eligible", True), "support_historical_eligibility_invalid")
    run("future_scope_as_current_fact_rejected", lambda d: d["annotations"][0]["facts"].__setitem__("scope_status_as_of", "verified"), "future_scope_asof_fact_leak")
    run("future_scope_lineage_dropped_rejected", lambda d: d["annotations"][0]["provenance"].__setitem__("availability_dependency_refs", []), "scope_dependency_lineage_dropped")
    run("missing_scope_dependency_edge_rejected", lambda d: d["dependencies"].remove(next(e for e in d["dependencies"] if e["edge_type"] == "retrospective_scope_dependency")), "scope_dependency_edge_coverage_mismatch")
    run("missing_representation_overlap_edge_rejected", lambda d: d["dependencies"].remove(next(e for e in d["dependencies"] if e["edge_type"] == "representation_overlap")), "representation_overlap_edge_coverage_mismatch")
    run("duplicate_dependency_edge_rejected", lambda d: d["dependencies"].append(copy.deepcopy(d["dependencies"][0])), "duplicate_dependency_edge_id")
    run("missing_duration_period_rejected", lambda d: d["annotations"][0]["facts"].__setitem__("period_start", None), "unknown_or_invalid_reference_period")
    run("wrong_duration_length_rejected", lambda d: d["annotations"][0]["facts"].__setitem__("duration_days", 1), "duration_period_mismatch")

    def wrong_relation_claim(data):
        relation = next(a for a in data["annotations"] if a["item_type"] == "reporting_relation")
        relation["facts"]["source_claim_id"] = data["annotations"][0]["item_id"]

    run("relation_link_to_wrong_scope_claim_rejected", wrong_relation_claim, "relation_claim_identity_mismatch")
    run("relation_link_missing_claim_rejected", lambda d: next(a for a in d["annotations"] if a["item_type"] == "reporting_relation")["facts"].__setitem__("source_claim_id", "ABSENT"), "relation_claim_reference_missing")
    run("reporting_period_as_actual_validity_rejected", lambda d: next(a for a in d["annotations"] if a["item_type"] == "reporting_relation")["facts"].__setitem__("valid_from", "2023-07-01"), "reporting_period_promoted_to_business_validity")
    run("annotation_answer_id_dropped_rejected", lambda d: item_row(d).__setitem__("annotation_ids", ""), "annotation_id_reference_mismatch")
    run("source_hash_tampering_rejected", lambda d: item_row(d).__setitem__("source_hash", "0" * 64), "source_metadata_mismatch")
    run("candidate_boundary_before_development_rejected", lambda d: d["policy"]["chronology"].__setitem__("candidate_boundary_after", "2024-07-30"), "candidate_boundary_mismatch")
    run("legacy_korean_input_rejected", lambda d: d["policy"].__setitem__("legacy_korean_inputs", ["KR-example"]), "legacy_korean_inputs_present")
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts/us_equity/p3"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/us_equity/p3/stage_reviews/stage_05_independent.json"))
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if args.output.exists() and not args.replace:
        parser.error("output exists; use a new path or explicitly --replace")
    paths = {
        "split": args.root / "split_manifest.csv", "policy": args.root / "split_policy.json",
        "source_docs": args.root.parent / "p0/available_20261005/document_manifest_v0_3.csv",
        "exposure": args.root / "exposure_manifest.csv", "families": args.root / "event_families.csv",
        "links": args.root / "event_claim_links.csv", "dependencies": args.root / "dependency_edges.csv",
        "reserved": args.root / "source_reservation/document_manifest.json",
        "reservation": args.root / "source_reservation/reservation_summary.json",
        "annotations": args.root / "annotations_raw.jsonl",
    }
    gold_paths = {name: args.root / name for name in ("gold_events.jsonl", "gold_relations.jsonl")}
    if args.output.resolve() in {path.resolve() for path in list(paths.values()) + list(gold_paths.values())}:
        parser.error("output must not overwrite inputs")
    all_paths = {**paths, **gold_paths}
    absent = [str(path) for path in all_paths.values() if not path.exists()]
    if absent:
        parser.error("required files absent: " + "; ".join(absent))
    hashes_before = {str(path).replace("\\", "/"): sha256(path) for path in all_paths.values()}
    bundle = {}
    for name, path in paths.items():
        if path.suffix == ".csv":
            bundle[name] = read_csv(path)
        elif path.suffix == ".jsonl":
            bundle[name] = read_jsonl(path)
        else:
            bundle[name] = json.loads(path.read_text(encoding="utf-8-sig"))
    bundle["gold_line_counts"] = {name: sum(bool(line.strip()) for line in path.read_text(encoding="utf-8-sig").splitlines()) for name, path in gold_paths.items()}
    bundle["reservation_sha256"] = sha256(paths["reservation"])
    result = audit(bundle)
    checks = negative_checks(bundle)
    hashes_after = {str(path).replace("\\", "/"): sha256(path) for path in all_paths.values()}
    passed = not result["errors"] and all(check["passed"] for check in checks) and hashes_before == hashes_after
    report = {
        "stage": 5, "checked_at": datetime.now(timezone.utc).isoformat(),
        "reviewer": "independent_agent_metadata_lineage_graph_audit",
        "gate": "passed_with_explicit_limitations" if passed else "failed",
        "source_input_hashes": hashes_before, "inputs_unchanged": hashes_before == hashes_after,
        "code_sha256": sha256(Path(__file__)), "result": result,
        "negative_checks": {"passed": sum(check["passed"] for check in checks), "total": len(checks), "cases": checks},
        "method": "Standard-library independent reconstruction from source metadata, exposure, event/claim links and dependency edges; connected-component grouping; source annotation reference checks. Root split implementation not imported or read.",
        "scope": "43 manifest rows are metadata/development lineage, not 43 independent events or evaluation examples.",
        "limitations": [
            "Reserved FY2026 Q1 body, numbers and private source were not opened; overlap remains unaudited",
            "A later publication date and provisional group do not establish independent test eligibility",
            "Human gold, train, dev and test allocations remain zero",
            "Support publication is unknown; the 24 retrospective scope dependencies cannot serve as historical facts",
            "Reservation separation is procedural; no OS access-control isolation verified",
            "No network access or source-rights expansion performed",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": report["gate"], "errors": result["errors"], "counts": result["counts"], "components": [c["node_count"] for c in result["lineage_components"]], "negative_checks": f"{report['negative_checks']['passed']}/{len(checks)}", "output": str(args.output)}, ensure_ascii=False))
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
