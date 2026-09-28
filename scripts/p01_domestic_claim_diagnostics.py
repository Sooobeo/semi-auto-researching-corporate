"""Offline, provisional claim signals; source text remains only in ignored raw/.

No network, model, ontology or gold labels. Same-sentence evidence is co-occurrence,
not semantic argument binding. Numeric differences never establish contradiction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

VERSION = "p01-domestic-claim-diagnostics/0.1"
PRODUCTS = {
    "HBM4E": r"HBM\s*4E", "HBM4": r"HBM\s*4(?![A-Z0-9])",
    "HBM3E": r"HBM\s*3E", "HBM3": r"HBM\s*3(?![A-Z0-9])",
    "HBM": r"HBM(?!\s*\d)", "DDR5": r"DDR\s*5", "LPDDR5X": r"LPDDR\s*5X",
    "DRAM": r"D램|DRAM|D-RAM|디램", "NAND": r"낸드|NAND",
    "V_NAND": r"V[- ]?NAND|V[- ]?낸드", "QLC": r"QLC", "TLC": r"TLC",
    "SSD": r"SSD", "CXL": r"CXL", "GPU": r"GPU",
}
SCOPES = {
    "company_samsung_electronics": r"삼성전자|Samsung Electronics",
    "company_sk_hynix": r"SK\s*하이닉스|SK\s*hynix",
    "memory_business": r"메모리\s*(?:사업|부문)|메모리반도체",
    "ds_segment": r"DS\s*(?:부문|사업)|반도체\(DS\)",
    "consolidated": r"연결\s*(?:기준|재무|실적)", "company_wide": r"전사\s*(?:실적|매출|기준)",
}
ACTIONS = {
    "development": r"개발", "validation": r"검증|인증|평가|테스트",
    "mass_production": r"양산", "shipment": r"출하|공급",
    "sales": r"판매", "investment": r"투자|증설|건설",
}
MODALITIES = {
    "plan": r"계획|예정|목표|추진|방침|예고",
    "forecast": r"전망|예상|예측|기대|추정",
    "actual_reported": r"기록했|달성했|달성한|완료했|완료한|시작했|개발했|개발한|양산했|양산한|출하했|출하한|발표했|공개했|공급했|판매했|투자했|돌입했|돌입한|성공했|성공한",
}
ATTRIBUTION = {"reporting_verb": r"밝혔|말했|설명했|전했|발표했|강조했|덧붙였",
               "speaker_role": r"관계자|대변인|대표이사|부사장|사장|연구원|교수"}
PERIOD = re.compile(r"20\d{2}\s*년\s*[1-4]\s*분기|20\d{2}\s*Q[1-4]|20\d{2}\s*년|20\d{2}[-./]\d{1,2}[-./]\d{1,2}|[1-4]\s*분기|\d{1,2}\s*월(?:\s*\d{1,2}\s*일)?|상반기|하반기|전년\s*동기|전년|전분기|올해|내년|지난해|금년|작년|이달|다음\s*달|지난\s*달|최근")
# Case matters for bit/byte units. Longest units precede prefixes.
QUANTITY = re.compile(r"(?<![\w.])(?P<value>[+-]?\d[\d,]*(?:\.\d+)?)\s*(?P<scale>조|억|만|천)?\s*(?P<unit>달러|원|퍼센트포인트|%포인트|%p|퍼센트|%|Gbps|Mbps|GB/s|TB/s|GB|TB|Gb|Tb|nm|나노미터|나노|단|층|개월|개|배|명|대|건|장|평|제곱미터|㎡|mm2|mm²)?")
UNIT_MAP = {"원": "KRW", "달러": "USD", "%": "percent", "퍼센트": "percent",
            "%p": "percentage_point", "%포인트": "percentage_point", "퍼센트포인트": "percentage_point",
            "GB": "gigabyte", "TB": "terabyte", "Gb": "gigabit", "Tb": "terabit",
            "Gbps": "gigabit_per_second", "Mbps": "megabit_per_second",
            "GB/s": "gigabyte_per_second", "TB/s": "terabyte_per_second",
            "nm": "nanometer", "나노미터": "nanometer", "나노": "nanometer",
            "단": "stack_layer_candidate", "층": "layer_candidate", "개월": "month_duration", "개": "count",
            "배": "multiple", "명": "person_count", "대": "machine_count", "건": "case_count",
            "장": "sheet_count", "평": "pyeong", "제곱미터": "square_meter", "㎡": "square_meter",
            "mm2": "square_millimeter", "mm²": "square_millimeter"}
SCALE = {None: 1, "천": 1000, "만": 10000, "억": 100000000, "조": 1000000000000}


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


def jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def write_jsonl(path, records):
    with path.open("x", encoding="utf-8", newline="\n") as out:
        for record in records:
            out.write(json.dumps(record, ensure_ascii=False) + "\n")


def overlap(a, b):
    return a[0] < b[1] and a[1] > b[0]


def decimal_text(value):
    number = Decimal(value)
    return "0" if number == 0 else format(number.normalize(), "f")


def locations(start, end, atoms):
    return [{"source_xpath": a["source_xpath"], "source_start": max(start, a["body_start"]) - a["body_start"],
             "source_end": min(end, a["body_end"]) - a["body_start"],
             "body_start": max(start, a["body_start"]), "body_end": min(end, a["body_end"])}
            for a in atoms if overlap((start, end), (a["body_start"], a["body_end"]))]


def period_value(surface):
    compact = re.sub(r"\s+", "", surface)
    year = re.search(r"20\d{2}", compact)
    quarter = re.search(r"([1-4])분기|Q([1-4])", compact)
    if year and quarter:
        return {"kind": "explicit_year_quarter", "year": int(year.group()), "quarter": int(quarter.group(1) or quarter.group(2)), "anchored": True}
    if year:
        if re.fullmatch(r"20\d{2}[-./]\d{1,2}[-./]\d{1,2}", compact):
            candidate = re.sub(r"[./]", "-", compact)
            try:
                date = datetime.strptime(candidate, "%Y-%m-%d").date().isoformat()
            except ValueError:
                return {"kind": "invalid_explicit_date", "date": candidate, "anchored": False}
            return {"kind": "explicit_date", "date": date, "anchored": True}
        return {"kind": "explicit_year", "year": int(year.group()), "anchored": True}
    if quarter:
        return {"kind": "quarter_without_year", "quarter": int(quarter.group(1) or quarter.group(2)), "anchored": False}
    if re.match(r"\d", compact):
        return {"kind": "month_or_day_without_year", "calendar_surface": compact, "anchored": False}
    mapping = {"상반기": "first_half", "하반기": "second_half", "전년동기": "prior_year_same_period",
               "전년": "prior_year", "지난해": "prior_year", "작년": "prior_year", "전분기": "prior_quarter",
               "올해": "current_year", "금년": "current_year", "내년": "next_year", "이달": "current_month",
               "다음달": "next_month", "지난달": "prior_month", "최근": "recent_unspecified"}
    return {"kind": mapping.get(compact, "relative_period"), "anchored": False}


def signal_candidates(text):
    found = []
    for kind, mapping in [("product", PRODUCTS), ("scope", SCOPES), ("action", ACTIONS), ("modality", MODALITIES), ("attribution", ATTRIBUTION)]:
        for label, pattern in mapping.items():
            for match in re.finditer(pattern, text, re.I):
                found.append((match.start(), match.end(), kind, {"label": label}))
    for match in PERIOD.finditer(text):
        found.append((match.start(), match.end(), "period", period_value(match.group())))
    reserved = [(a, b) for a, b, k, _ in found if k in {"product", "period"}]
    for match in QUANTITY.finditer(text):
        a, b = match.start(), match.end()
        while b > a and text[b - 1].isspace():
            b -= 1
        if any(overlap((a, b), r) for r in reserved):
            continue
        value = match.group("value").replace(",", "")
        scale, unit = match.group("scale"), match.group("unit")
        # A component beside another numeral is not a complete compound amount.
        adjacent = bool(re.match(r"\s*\d", text[b:])) or (a > 0 and bool(re.search(r"\d[\d,.]*\s*[조억만천]\s*$", text[:a])))
        normalized = {"value": decimal_text(value), "unit": UNIT_MAP.get(unit, "unknown"),
                      "scale_multiplier": SCALE[scale], "compound_amount_component": adjacent,
                      "base_value": decimal_text(Decimal(value) * SCALE[scale]) if unit and not adjacent else None,
                      "normalization_status": "simple_explicit_unit" if unit and not adjacent else "compound_requires_review" if adjacent else "unit_missing"}
        found.append((a, b, "quantity", normalized))
    for match in re.finditer(r'“[^”\n]{1,2000}”|"[^"\n]{1,2000}"|‘[^’\n]{1,1000}’', text):
        found.append((match.start(), match.end(), "quote", {"label": "quotation_boundary_candidate"}))
    for match in re.finditer(r"않|못|아니|미정|불확실|취소|중단", text):
        found.append((match.start(), match.end(), "negation_or_uncertainty", {"label": "local_negation_or_uncertainty_cue"}))
    return sorted(found, key=lambda v: (v[0], v[1], v[2]))


def quantity_key(signal):
    n = signal["normalized"]
    if n["normalization_status"] != "simple_explicit_unit":
        return None
    return n["base_value"], n["unit"]


def diagnostic(left, right):
    def sets(records, kind):
        return {json.dumps(r["normalized"], sort_keys=True, ensure_ascii=False) for r in records if r["kind"] == kind}
    lq, rq = {quantity_key(s) for s in left if s["kind"] == "quantity"}, {quantity_key(s) for s in right if s["kind"] == "quantity"}
    lq.discard(None); rq.discard(None)
    shared = sorted(lq & rq)
    context = {}
    for kind in ["period", "scope", "product", "action", "modality", "attribution"]:
        a, b = sets(left, kind), sets(right, kind)
        context[kind] = {"common": [json.loads(v) for v in sorted(a & b)],
                         "left_only": [json.loads(v) for v in sorted(a - b)],
                         "right_only": [json.loads(v) for v in sorted(b - a)]}
    common_period = any(x.get("anchored") for x in context["period"]["common"])
    # Company mention alone is not business scope. Product is evidence, not confirmed numeric scope.
    common_scope = any(x["label"] not in {"company_samsung_electronics", "company_sk_hynix"} for x in context["scope"]["common"])
    reasons = ["anchor_proposition_not_aligned", "numeric_argument_binding_unverified", "speaker_identity_unverified", "human_semantic_review_required"]
    if not shared: reasons.append("no_common_explicit_value_unit")
    if not common_period: reasons.append("no_common_explicit_anchored_period")
    if not common_scope: reasons.append("no_common_business_scope_signal")
    if not context["action"]["common"]: reasons.append("no_common_action_signal")
    if any(s["kind"] == "quantity" and s["normalized"]["normalization_status"] != "simple_explicit_unit" for s in left + right): reasons.append("unitless_or_compound_number_requires_review")
    if any(s["kind"] == "period" and not s["normalized"]["anchored"] for s in left + right): reasons.append("relative_or_partial_period_requires_resolution")
    if context["modality"]["left_only"] or context["modality"]["right_only"]: reasons.append("modality_surface_sets_differ")
    if any(s["kind"] == "negation_or_uncertainty" for s in left + right): reasons.append("negation_or_uncertainty_scope_requires_review")
    surface_ready = bool(shared and common_period and common_scope and context["action"]["common"])
    return {"common_quantity_value_unit": [{"base_value": v, "unit": u} for v, u in shared],
            "left_only_quantity_value_unit": [{"base_value": v, "unit": u} for v, u in sorted(lq - rq)],
            "right_only_quantity_value_unit": [{"base_value": v, "unit": u} for v, u in sorted(rq - lq)],
            "quantity_surface_sets_differ": lq != rq, "context_surface_evidence": context,
            "numeric_surface_prerequisites_present": surface_ready,
            "review_priority": "contextual_numeric_review" if surface_ready else "value_unit_review" if shared else "context_completion_review",
            "claim_alignment_ready": False, "readiness_blockers": reasons,
            "claim_relation": "unassessed", "contradiction_status": "not_inferred_from_surface_difference",
            "context_binding": "same_sentence_cooccurrence_only"}


def run(audit_dir, comparison_dir, output):
    if output.exists():
        raise ValueError("output_directory_must_be_new")
    paths = [audit_dir / "raw/documents.jsonl", audit_dir / "raw/sentences.jsonl", audit_dir / "raw/atoms.jsonl", comparison_dir / "raw/alignment_cards.jsonl"]
    input_hashes = {str(p): sha(p.read_bytes()) for p in paths}
    documents = {r["doc_id"]: r for r in jsonl(paths[0])}
    sentences = jsonl(paths[1]); atoms = defaultdict(list)
    for a in jsonl(paths[2]): atoms[a["doc_id"]].append(a)
    cards = jsonl(paths[3]); signals, private, sentence_records = [], [], []
    sentence_signals = defaultdict(list); sentence_map = {s["sentence_id"]: s for s in sentences}
    for sentence in sentences:
        doc = documents[sentence["doc_id"]]; text = sentence["text"]
        assert doc["canonical_body_raw"][sentence["start"]:sentence["end"]] == text
        local = []
        for i, (a, b, kind, value) in enumerate(signal_candidates(text), 1):
            start, end = sentence["start"] + a, sentence["start"] + b
            source_text = text[a:b]
            assert doc["canonical_body_raw"][start:end] == source_text
            record = {"signal_id": sentence["sentence_id"] + f":C{i:04d}", "doc_id": sentence["doc_id"],
                      "revision_id": sentence["revision_id"], "sentence_id": sentence["sentence_id"],
                      "kind": kind, "normalized": value, "start": start, "end": end,
                      "offset_basis": "canonical_body_raw", "offset_unit": "unicode_codepoint", "raw_sha256": sha(source_text),
                      "source_segments": locations(start, end, atoms[sentence["doc_id"]]),
                      "assessment": "provisional_rule_signal", "semantic_binding": "unverified", "roundtrip": True}
            local.append(record); private.append(record | {"raw_text": source_text})
        for record in local:
            record["same_sentence_context_signal_ids"] = [v["signal_id"] for v in local if v["signal_id"] != record["signal_id"] and v["kind"] in {"period", "scope", "product", "action", "modality", "attribution", "quote", "negation_or_uncertainty"}]
            record["overlapping_quote_signal_ids"] = [v["signal_id"] for v in local if v["kind"] == "quote" and v["start"] <= record["start"] and v["end"] >= record["end"]]
        signals.extend(local); sentence_signals[sentence["sentence_id"]] = local
        modal = sorted({s["normalized"]["label"] for s in local if s["kind"] == "modality"})
        sentence_records.append({"sentence_id": sentence["sentence_id"], "doc_id": sentence["doc_id"], "revision_id": sentence["revision_id"],
                                 "start": sentence["start"], "end": sentence["end"], "text_sha256": sha(text),
                                 "source_segments": sentence["source_segments"], "signal_ids": [s["signal_id"] for s in local],
                                 "signal_counts": dict(Counter(s["kind"] for s in local)), "modality_candidates": modal,
                                 "modality_assignment": "mixed_cues_unbound" if len(modal) > 1 else "single_cue_unbound" if modal else "unknown",
                                 "speech_candidate": sentence["speech_candidate"], "speaker_candidate": sentence["speaker_candidate"],
                                 "speaker_identity": "unknown", "actual_event_verified": False, "claim_alignment_ready": False})
    pairs = []
    for card in cards:
        left, right = sentence_map[card["left_sentence_id"]], sentence_map[card["right_sentence_id"]]
        assert card["left_text_sha256"] == sha(left["text"]) and card["right_text_sha256"] == sha(right["text"])
        identity = {k: card[k] for k in ["alignment_id", "pair_id", "event_family_id", "left_doc_id", "right_doc_id", "left_sentence_id", "right_sentence_id", "left_start", "left_end", "right_start", "right_end", "left_text_sha256", "right_text_sha256", "position_candidate", "speech_candidate"]}
        pairs.append(identity | diagnostic(sentence_signals[left["sentence_id"]], sentence_signals[right["sentence_id"]]) |
                     {"left_signal_ids": [s["signal_id"] for s in sentence_signals[left["sentence_id"]]],
                      "right_signal_ids": [s["signal_id"] for s in sentence_signals[right["sentence_id"]]],
                      "left_source_segments": left["source_segments"], "right_source_segments": right["source_segments"]})
    assert all(sha(p.read_bytes()) == h for p, h in [(Path(p), h) for p, h in input_hashes.items()])
    output.mkdir(parents=True); (output / "raw").mkdir(); (output / "raw/.gitignore").write_text("*\n", encoding="utf-8")
    write_jsonl(output / "claim_signals.jsonl", signals); write_jsonl(output / "sentence_diagnostics.jsonl", sentence_records)
    write_jsonl(output / "pair_diagnostics.jsonl", pairs); write_jsonl(output / "raw/signal_spans.jsonl", private)
    summary = {"version": VERSION, "completed_at": datetime.now(timezone.utc).isoformat(), "script_sha256": sha(Path(__file__).read_bytes()),
               "input_sha256": input_hashes, "network_requests": 0, "model_calls": 0, "documents": len(documents), "sentences": len(sentences),
               "signals": len(signals), "signals_by_kind": dict(Counter(s["kind"] for s in signals)), "alignment_candidates": len(pairs),
               "pairs_with_common_explicit_value_unit": sum(bool(p["common_quantity_value_unit"]) for p in pairs),
               "pairs_with_differing_quantity_surface_sets": sum(p["quantity_surface_sets_differ"] for p in pairs),
               "pairs_with_numeric_surface_prerequisites": sum(p["numeric_surface_prerequisites_present"] for p in pairs),
               "readiness_blocker_counts": dict(Counter(v for p in pairs for v in p["readiness_blockers"])),
               "verified_claim_alignments": 0, "verified_contradictions": 0, "human_review": "pending",
               "limitations": ["Rules have not been measured for precision or recall; missed and false-positive signals are possible.",
                               "Sentence context links are co-occurrence, not argument binding; relative periods are not resolved from publication dates.",
                               "Company mention is not business scope. Product mentions do not establish the scope of a number.",
                               "Simple unit values only; compound amounts, range operators, comparisons and denominators need review.",
                               "An actual_reported cue is a reporting-language cue, not independent confirmation that an event occurred.",
                               "Quote and speaker-role cues do not identify the speaker; source article completeness remains unverified.",
                               "No semantic same-claim, contradiction, linguistic gold, ontology or new rights determination."]}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ["documents", "sentences", "signals", "signals_by_kind", "alignment_candidates", "pairs_with_common_explicit_value_unit", "pairs_with_numeric_surface_prerequisites"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-dir", type=Path, required=True)
    parser.add_argument("--comparison-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    run(args.audit_dir, args.comparison_dir, args.output_dir)
