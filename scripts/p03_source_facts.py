"""A narrow, non-AI Microsoft IR factual reference trial.

This does not create a reusable prose corpus. Original copies and the permission
notice remain in a gitignored private directory. No cross-host redirects, retries,
SEC requests, or NVIDIA requests are permitted by this trial.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib import error, parse, request, robotparser

from lxml import html

BASE = Path("artifacts/us_equity/p0/available_20261005")
UA = "semi-auto-researching-corporate/0.1 (personal noncommercial factual reference)"
HOST = "www.microsoft.com"
TERMS = "https://www.microsoft.com/en-us/legal/terms-of-use"
PERMISSION = """Microsoft Terms of Use — Documents permission notice
Source: https://www.microsoft.com/en-us/legal/terms-of-use
© Microsoft. All rights reserved.
Permission to use Documents (such as white papers, press releases, datasheets and FAQs) from the Services is granted, provided that (1) the below copyright notice appears in all copies and that both the copyright notice and this permission notice appear, (2) unless explicitly covered by another license or agreement, use of such Documents from the Services is for informational and non-commercial or personal use only and will not be copied or posted on any network computer or broadcast in any media, and (3) no modifications of any Documents are made.
Accredited educational institutions, such as K-12, universities, private/public colleges, and state community colleges, may download and reproduce the Documents for distribution in the classroom. Distribution outside the classroom requires express written permission. Use for any other purpose is expressly prohibited by law, and may result in severe civil and criminal penalties. Violators will be prosecuted to the maximum extent possible.
This folder is a local, informational, personal/noncommercial reference copy. Original bytes are unmodified. No original prose, layout, logo, or graphics are exported to the agent or shared corpus. This narrow factual-reference trial does not establish corpus storage, raw AI input, model-training, or public-redistribution rights.
"""


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def now():
    return datetime.now(timezone.utc).isoformat()


def collect():
    if (BASE / "access_trials.jsonl").exists():
        raise SystemExit("Refusing to overwrite existing trial records; use a new dated run path.")
    private = BASE / "private"
    private.mkdir(parents=True, exist_ok=True)
    (private / "permission_notice.txt").write_text(PERMISSION, encoding="utf-8")
    opener = request.build_opener(NoRedirect())
    trials = []

    def get(url, name, kind):
        if parse.urlsplit(url).hostname != HOST:
            raise ValueError("Only the reviewed Microsoft host is permitted.")
        started = now()
        try:
            with opener.open(request.Request(url, headers={"User-Agent": UA}), timeout=30) as response:
                body = response.read()
                final = response.url
                mime = response.headers.get_content_type()
                status = response.status
            if parse.urlsplit(final).hostname != HOST:
                raise ValueError("Unreviewed redirect host.")
            path = private / name
            path.write_bytes(body)
            row = dict(url=url, final_url=final, observed_at=started, resource_kind=kind,
                       status="downloaded_private_reference", http_status=status, mime=mime,
                       byte_size=len(body), sha256=hashlib.sha256(body).hexdigest(),
                       storage_uri=path.as_posix(), request_method="urllib_direct_no_redirect",
                       user_agent_category="declared_personal_noncommercial_reference", error=None)
            trials.append(row)
            return body
        except (error.HTTPError, error.URLError, ValueError) as exc:
            trials.append(dict(url=url, observed_at=started, resource_kind=kind,
                               status="failed_stopped_no_retry", http_status=getattr(exc, "code", None),
                               error=type(exc).__name__))
            return None

    robots = get(f"https://{HOST}/robots.txt", "robots.txt", "access_policy")
    if robots is None:
        (BASE / "access_trials.jsonl").write_text("\n".join(json.dumps(x) for x in trials)+"\n", encoding="utf-8")
        raise SystemExit("Microsoft robots inaccessible; stopped.")
    rp = robotparser.RobotFileParser()
    rp.parse(robots.decode("utf-8", "replace").splitlines())
    time.sleep(1.1)
    if not rp.can_fetch(UA, TERMS):
        trials.append(dict(url=TERMS, status="robots_disallowed_unattempted", resource_kind="rights_policy"))
        (BASE / "access_trials.jsonl").write_text("\n".join(json.dumps(x) for x in trials)+"\n", encoding="utf-8")
        raise SystemExit("Terms path blocked; stopped before document requests.")
    terms_body = get(TERMS, "microsoft_terms.html", "rights_policy")
    if terms_body is None:
        (BASE / "access_trials.jsonl").write_text("\n".join(json.dumps(x) for x in trials)+"\n", encoding="utf-8")
        raise SystemExit("Terms inaccessible; stopped before document requests.")
    for fiscal_year in (2024, 2025):
        url = f"https://{HOST}/en-us/Investor/earnings/FY-{fiscal_year}-Q4/press-release-webcast"
        if not rp.can_fetch(UA, url):
            trials.append(dict(url=url, status="robots_disallowed_unattempted", resource_kind="earnings_release"))
            continue
        time.sleep(1.1)
        body = get(url, f"msft_fy{fiscal_year}_q4.html", "earnings_release")
        if body is None and trials[-1].get("http_status") in (403, 429):
            break
    (BASE / "access_trials.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in trials)+"\n", encoding="utf-8")
    print(json.dumps({"trials": [{k: v for k, v in row.items() if k != "storage_uri"} for row in trials]}, ensure_ascii=False))


def inspect_numbers():
    """Export table indices and numeric cells only; never dump source prose."""
    for path in sorted((BASE / "private").glob("msft_*.html")):
        tree = html.fromstring(path.read_bytes())
        print(path.name)
        for i, table in enumerate(tree.xpath("//table")):
            numeric_rows = []
            for j, row in enumerate(table.xpath(".//tr")):
                cells = [" ".join(cell.text_content().split()) for cell in row.xpath("./th|./td")]
                # Narrow references to standard financial rows and numeric headers.
                labels = {"revenue", "operating income", "net income", "cash from operations", "additions to property and equipment", "net cash from operations"}
                if cells and cells[0].lower() in labels and all(re.fullmatch(r"[\s$(),.\d+\-]*", x) for x in cells[1:]):
                    numeric_rows.append({"tr": j, "cells": cells, "cell_xpaths": [tree.getroottree().getpath(x) for x in row.xpath("./th|./td")]})
            if numeric_rows:
                print(json.dumps({"table_index": i, "xpath": tree.getroottree().getpath(table), "rows": numeric_rows}, ensure_ascii=False))


def write_csv(name, rows):
    if not rows:
        return
    with (BASE / name).open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()})


def extract():
    if (BASE / "facts.jsonl").exists():
        raise SystemExit("Refusing to overwrite existing normalized facts.")
    trials = [json.loads(line) for line in (BASE / "access_trials.jsonl").read_text(encoding="utf-8").splitlines()]
    documents, facts, relations, audits = [], [], [], []
    segments = {"Productivity and Business Processes": "PBP", "Intelligent Cloud": "IC", "More Personal Computing": "MPC"}
    for fiscal_year in (2024, 2025):
        path = BASE / "private" / f"msft_fy{fiscal_year}_q4.html"
        if not path.exists():
            continue
        trial = next(x for x in trials if x.get("storage_uri") == path.as_posix())
        original = path.read_bytes()
        root = html.fromstring(original)
        tree = root.getroottree()
        doc_id = f"US-MSFT-FY{fiscal_year}-Q4-RELEASE"
        revision_id = f"{doc_id}-R-{trial['sha256'][:12]}"
        family_id = f"US-MSFT-FY{fiscal_year}-Q4-EARNINGS"
        datelines = [e for e in root.xpath("//p") if "REDMOND" in e.text_content() and re.search(r"July \d{1,2}, \d{4}", e.text_content())]
        assert len(datelines) == 1, "Dateline selection is ambiguous."
        date_raw = re.search(r"July \d{1,2}, \d{4}", datelines[0].text_content()).group()
        published_date = datetime.strptime(date_raw, "%B %d, %Y").date().isoformat()
        documents.append(dict(doc_id=doc_id, revision_id=revision_id, event_family_id=family_id,
                              source_id="US-MSFT-IR-FACTUAL-REFERENCE", company_id="US-MSFT",
                              source_url=trial["url"], final_url=trial["final_url"], language="en",
                              document_kind="earnings_press_release", fiscal_year=fiscal_year,
                              published_date=published_date, published_at=None, time_precision="date",
                              timezone=None, published_date_evidence=tree.getpath(datelines[0]),
                              observed_at=trial["observed_at"], sha256=trial["sha256"], byte_size=len(original),
                              storage_uri=path.as_posix(), storage_policy="local_private_unmodified_notice_retained",
                              parse_status="selected_numeric_cells_only", parser_version="p03-source-facts-0.1",
                              full_body_audited=False, original_prose_sent_to_ai=False,
                              split_exposure="adaptation", rights_basis_ref="source_conditions.md#msft-factual-reference"))

        def table_named(heading):
            matches = [t for t in root.xpath("//table") if heading in [" ".join(p.text_content().split()) for p in t.xpath("./caption/p")]]
            assert len(matches) == 1, (heading, len(matches))
            return matches[0]

        income = table_named("INCOME STATEMENTS")
        cashflow = table_named("CASH FLOWS STATEMENTS")
        balances = table_named("BALANCE SHEETS")
        seg_table = table_named("SEGMENT REVENUE AND OPERATING INCOME")

        def cells(row):
            return row.xpath("./th|./td")

        def row_named(table, name):
            matches = [r for r in table.xpath(".//tr") if cells(r) and " ".join(cells(r)[0].text_content().split()) == name]
            assert len(matches) == 1, (name, len(matches))
            return matches[0]

        def fact(table, row, column, metric, year, period, scope="US-MSFT-CONSOLIDATED", sign_policy="preserve", definition="us-financial-0.1", occurrence_note="current_period"):
            cell = cells(row)[column]
            text_value = cell.text_content()
            value_match = re.search(r"\(?\$?-?\d[\d,]*(?:\.\d+)?\)?", text_value)
            assert value_match, (metric, text_value)
            value_raw = value_match.group()
            numeric = Decimal(value_raw.replace("$", "").replace(",", "").replace("(", "-").replace(")", ""))
            if sign_policy == "outflow_to_positive":
                assert numeric < 0
                numeric = -numeric
            instant = period == "instant"
            end = date(year, 6, 30)
            start = end if instant else date(year if period == "Q4" else year-1, 4 if period == "Q4" else 7, 1)
            duration = 0 if instant else (end-start).days+1
            id_suffix = f"{scope}-{metric}-FY{year}-{period}-{occurrence_note}"
            claim_id = f"{doc_id}-{id_suffix}"
            header_row = table.xpath(".//tr")[0]
            year_row = table.xpath(".//tr")[2 if not instant else 0]
            record = dict(claim_id=claim_id, doc_id=doc_id, revision_id=revision_id, event_family_id=family_id,
                          company_id="US-MSFT", scope_id=scope, product_id=None, metric_id=metric,
                          metric_candidate=metric, definition_version=definition, metric_raw=" ".join(cells(row)[0].text_content().split()),
                          value_raw=value_raw, numeric_value=str(numeric), numeric_value_decimal=str(numeric),
                          numeric_value_base_units=str(numeric*Decimal("1000000")), value_kind="point",
                          canonical_unit="USD", unit_raw="millions", scale="1000000", currency="USD",
                          accounting_basis="GAAP", accounting_basis_evidence="financial_statements_not_non_GAAP_reconciliation",
                          consolidation="consolidated" if scope == "US-MSFT-CONSOLIDATED" else "segment",
                          consolidation_confirmation="corporate_total_assessment_not_explicit_word" if scope == "US-MSFT-CONSOLIDATED" else "segment_table_explicit",
                          fiscal_year=year, fiscal_quarter=4 if period == "Q4" else None, period_label=period,
                          period_start=start.isoformat(), period_end=end.isoformat(), period_basis="fiscal",
                          period_duration_days=duration, balance_or_flow="balance" if instant else "flow",
                          period_start_derivation="instant_end_date" if instant else "calendar_months_from_three_or_twelve_month_header",
                          modality="actual_reported", missing_reason=None, speaker="Microsoft Corporation",
                          evidence_status="company_reported_unaudited", published_date=published_date, published_at=None,
                          observed_at=trial["observed_at"], source_url=trial["url"], final_url=trial["final_url"],
                          evidence_pointer=tree.getpath(cell), evidence_location=tree.getpath(cell),
                          table_xpath=tree.getpath(table), table_row_index=table.xpath(".//tr").index(row), table_col_index=column,
                          period_header_pointer=tree.getpath(header_row), year_header_pointer=tree.getpath(year_row),
                          unit_header_pointer=tree.getpath(table.xpath("./caption")[0]),
                          offset_basis="Unicode code point; 0-based [start,end) within original DOM-cell text",
                          value_span_start=value_match.start(), value_span_end=value_match.end(),
                          sign_policy=sign_policy, occurrence_note=occurrence_note, split_exposure="adaptation",
                          original_prose_ai_input=False, schema_version="p03-factual-reference-0.1")
            assert tree.xpath(record["evidence_pointer"])[0].text_content()[record["value_span_start"]:record["value_span_end"]] == value_raw
            facts.append(record)
            audits.append(dict(audit_id=f"AUDIT-{claim_id}", claim_id=claim_id, doc_id=doc_id,
                               audit_method="deterministic_local_DOM_cell_header_roundtrip", evidence_pointer=record["evidence_pointer"],
                               value_roundtrip=True, number_parsed=True, unit_caption_confirmed="millions" in table.xpath("./caption")[0].text_content().lower(),
                               period_header_confirmed=instant or "Months Ended June 30" in header_row.text_content(),
                               fiscal_year_header_confirmed=str(year) in year_row.text_content(),
                               human_audit_status="waived_by_user_not_observed", body_completeness_audited=False,
                               unresolved="corporate_consolidation_not_explicit_in_release" if scope == "US-MSFT-CONSOLIDATED" else "segment_definition_change_reason_not_yet_audited"))
            return record

        for period, col in (("Q4", 1), ("FY", 5)):
            for label, metric in (("Total revenue", "revenue"), ("Operating income", "operating_income"), ("Net income", "net_income")):
                fact(income, row_named(income, label), col, metric, fiscal_year, period)
            fact(cashflow, row_named(cashflow, "Net cash from operations"), col, "cfo", fiscal_year, period)
            fact(cashflow, row_named(cashflow, "Additions to property and equipment"), col, "positive_cash_capex", fiscal_year, period, sign_policy="outflow_to_positive")
        for label, metric in (("Total assets", "total_assets"), ("Cash and cash equivalents", "cash_and_equivalents")):
            fact(balances, row_named(balances, label), 1, metric, fiscal_year, "instant")
        for name, key in segments.items():
            seg_id = f"US-MSFT-SEG-{key}"
            revenue_row = next(r for r in seg_table.xpath(".//tr") if cells(r) and " ".join(cells(r)[0].text_content().split()) == name)
            current = fact(seg_table, revenue_row, 5, "revenue", fiscal_year, "FY", scope=seg_id,
                           definition=f"msft-segment-presentation-fy{fiscal_year}")
            if fiscal_year == 2025:
                fact(seg_table, revenue_row, 7, "revenue", 2024, "FY", scope=seg_id,
                     definition="msft-segment-presentation-fy2025", occurrence_note="comparative_prior_year")
            relations.append(dict(relation_id=f"{doc_id}-REPORTS-{key}", relation_revision_id=f"{revision_id}-REPORTS-{key}",
                                  relation_type="reports_segment", subject_entity_id="US-MSFT", object_entity_id=seg_id,
                                  object_name=name, subject_role="reporting_company", object_role="reported_segment",
                                  company_id="US-MSFT", scope_id=seg_id, claim_id=current["claim_id"],
                                  event_family_id=family_id, modality="actual_reported", negation=False,
                                  valid_from=None, valid_to=None, effective_period={"start": current["period_start"], "end": current["period_end"]},
                                  published_date=published_date, observed_at=trial["observed_at"],
                                  evidence_refs=[{"doc_id": doc_id, "revision_id": revision_id, "source_url": trial["url"],
                                                  "table_xpath": tree.getpath(seg_table), "row_label_pointer": tree.getpath(cells(revenue_row)[0])}],
                                  evidence_status="company_reported_table", extraction_status="local_table_reference",
                                  uncertainty_reason="reporting_membership_only; not_customer_supply_or_product_relation; no_business_impact_inference",
                                  split_exposure="adaptation", schema_version="p03-factual-reference-0.1"))

    write_csv("document_manifest.csv", documents)
    write_csv("extraction_audit.csv", audits)
    for name, rows in (("facts.jsonl", facts), ("business_relations.jsonl", relations)):
        (BASE / name).write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows)+"\n", encoding="utf-8")
    print(json.dumps({"private_reference_documents":len(documents),"selected_numeric_facts":len(facts),"relation_claims":len(relations),"unique_reporting_relations":len(segments),"full_body_audits":0,"source_prose_ai_inputs":0}))


def verify():
    suffix = "_v0_3" if (BASE / "facts_v0_3.jsonl").exists() else "_v0_2" if (BASE / "facts_v0_2.jsonl").exists() else ""
    facts = [json.loads(line) for line in (BASE / f"facts{suffix}.jsonl").read_text(encoding="utf-8").splitlines()]
    with (BASE / f"document_manifest{suffix}.csv").open(encoding="utf-8", newline="") as stream:
        docs = {r["doc_id"]: r for r in csv.DictReader(stream)}
    roots = {k: html.fromstring(Path(v["storage_uri"]).read_bytes()) for k, v in docs.items()}
    checks, period_header_checks = [], []
    for f in facts:
        cell = roots[f["doc_id"]].xpath(f["evidence_pointer"])[0]
        extracted = cell.text_content()[f["value_span_start"]:f["value_span_end"]]
        assert extracted == f["value_raw"]
        val = Decimal(extracted.replace("$", "").replace(",", "").replace("(", "-").replace(")", ""))
        if f["sign_policy"] == "outflow_to_positive":
            val = -val
        assert val == Decimal(f["numeric_value"])
        assert Decimal(f["numeric_value_base_units"]) == val*Decimal(f["scale"])
        if f["balance_or_flow"] == "flow":
            assert f["period_duration_days"] == (date.fromisoformat(f["period_end"])-date.fromisoformat(f["period_start"])).days+1
        if suffix == "_v0_3":
            header = " ".join(roots[f["doc_id"]].xpath(f["period_header_pointer"])[0].text_content().split())
            year = " ".join(roots[f["doc_id"]].xpath(f["year_header_pointer"])[0].text_content().split())
            expected = "Three Months Ended June 30" if f["period_label"] == "Q4" else "Twelve Months Ended June 30" if f["period_label"] == "FY" else f"June 30, {f['fiscal_year']}"
            assert re.sub(r"\s+", "", expected) in re.sub(r"\s+", "", header), (f["claim_id"], expected, header)
            assert str(f["fiscal_year"]) in year, (f["claim_id"], year)
            period_header_checks.append(f["claim_id"])
        checks.append(f["claim_id"])
    assert len(checks) == len(set(checks))
    integrity = {k: hashlib.sha256(Path(v["storage_uri"]).read_bytes()).hexdigest() == v["sha256"] for k, v in docs.items()}
    assert all(integrity.values())
    report = {"status":"passed", "numeric_cell_value_scale_span_roundtrips_passed":len(checks),
              "numeric_cell_value_scale_span_roundtrips_attempted":len(facts),
              "period_length_arithmetic_passed":len(checks), "period_specific_original_header_passed":len(period_header_checks),
              "period_specific_original_header_attempted":len(facts) if suffix == "_v0_3" else 0,
              "raw_hash_integrity":integrity,
              "human_validation":"waived_by_user_not_observed", "source_prose_ai_inputs":0,
              "full_body_complete_audits":0, "nonempty_independent_gold":False,
              "scope_limit":"current_retrospective_consolidation_corroboration; segment_presentation_definitions_kept_separate" if suffix else "corporate_total_consolidation_assessment; segment_presentation_definitions_kept_separate"}
    (BASE / f"verification_report{suffix}.json").write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


def corroborate():
    """Add evidence from the separately recorded, unmodified annual-report copy.

    Original facts remain available. Only factual booleans and locations are
    exported; the accounting-policy paragraph itself is not exported to AI.
    """
    if (BASE / "facts_v0_2.jsonl").exists():
        raise SystemExit("Refusing to overwrite existing v0.2 normalization.")
    proof = json.loads((BASE / "scope_corroboration.json").read_text(encoding="utf-8"))
    assert proof["status"] == "downloaded_private_reference"
    raw = Path(proof["storage_uri"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == proof["sha256"]
    annual = html.fromstring(raw)
    annual_tree = annual.getroottree()
    heading = annual.xpath("/html/body/main/section[2]/article[18]/p[3]")[0]
    policy = annual.xpath("/html/body/main/section[2]/article[18]/p[4]")[0]
    assert " ".join(heading.text_content().split()) == "Principles of Consolidation"
    statement = " ".join(policy.text_content().split())
    features = dict(states_financial_statement_inclusion=bool(re.search(r"financial statements.{0,100}include", statement, re.I)),
                    states_microsoft_corporation="Microsoft Corporation" in statement,
                    states_subsidiaries="subsidiar" in statement.lower(), states_consolidation="consolidat" in statement.lower())
    assert all(features.values())
    ref = dict(doc_id="US-MSFT-ANNUAL-FY2025-SCOPE-REFERENCE", source_url=proof["url"],
               sha256=proof["sha256"], evidence_pointer=annual_tree.getpath(policy),
               heading_pointer=annual_tree.getpath(heading), observed_at=proof["observed_at"],
               published_date=None, publication_precision="unknown", policy_features=features,
               statement_sha256=hashlib.sha256(statement.encode()).hexdigest(),
               availability_policy="retrospective_corroboration_observed_2026_not_assumed_available_2024")
    with (BASE / "document_manifest.csv").open(encoding="utf-8", newline="") as stream:
        documents = list(csv.DictReader(stream))
    facts = [json.loads(line) for line in (BASE / "facts.jsonl").read_text(encoding="utf-8").splitlines()]
    doc_roots = {d["doc_id"]: html.fromstring(Path(d["storage_uri"]).read_bytes()) for d in documents}
    for fact_record in facts:
        fact_record["normalization_revision_id"] = "p03-factual-reference-0.2"
        fact_record["aggregation_behavior"] = "instant_balance" if fact_record["balance_or_flow"] == "balance" else "additive_flow"
        if fact_record["scope_id"] == "US-MSFT-CONSOLIDATED":
            fact_record["consolidation_confirmation"] = "official_annual_report_principles_of_consolidation_local_fact_corroborated"
            fact_record["scope_evidence_refs"] = [ref]
        else:
            root = doc_roots[fact_record["doc_id"]]
            table = root.xpath(fact_record["table_xpath"])[0]
            row = next(r for r in table.xpath(".//tr") if r.xpath("./td|./th") and " ".join(r.xpath("./td|./th")[0].text_content().split()) == "Revenue")
            fact_record["metric_context_raw"] = "Revenue"
            fact_record["metric_context_pointer"] = root.getroottree().getpath(row)
    (BASE / "facts_v0_2.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in facts)+"\n", encoding="utf-8")
    annual_doc = {k: None for k in documents[0]}
    annual_doc.update(doc_id=ref["doc_id"], revision_id=f"{ref['doc_id']}-R-{proof['sha256'][:12]}",
                      source_id="US-MSFT-IR-FACTUAL-REFERENCE", company_id="US-MSFT", source_url=proof["url"], final_url=proof["final_url"],
                      language="en", document_kind="annual_report_accounting_scope_reference", fiscal_year=2025,
                      time_precision="unknown", observed_at=proof["observed_at"], sha256=proof["sha256"], byte_size=len(raw),
                      storage_uri=proof["storage_uri"], storage_policy="local_private_unmodified_notice_retained",
                      parse_status="accounting_scope_boolean_only", parser_version="p03-source-facts-0.2",
                      full_body_audited=False, original_prose_sent_to_ai=False, split_exposure="adaptation",
                      rights_basis_ref="source_conditions.md#msft-factual-reference")
    documents.append(annual_doc)
    write_csv("document_manifest_v0_2.csv", documents)
    with (BASE / "extraction_audit.csv").open(encoding="utf-8", newline="") as stream:
        audits = list(csv.DictReader(stream))
    for audit in audits:
        if audit["unresolved"] == "corporate_consolidation_not_explicit_in_release":
            audit["unresolved"] = "historical_availability_of_scope_supplement_not_verified; annual_publication_date_unknown"
    write_csv("extraction_audit_v0_2.csv", audits)
    print(json.dumps({"facts":len(facts),"document_references":len(documents),"scope_corroboration_features":features,"prose_ai_inputs":0}))


def refine_headers():
    if (BASE / "facts_v0_3.jsonl").exists():
        raise SystemExit("Refusing to overwrite final v0.3 normalization.")
    with (BASE / "document_manifest_v0_2.csv").open(encoding="utf-8", newline="") as stream:
        documents = list(csv.DictReader(stream))
    roots = {d["doc_id"]: html.fromstring(Path(d["storage_uri"]).read_bytes()) for d in documents}
    facts = [json.loads(line) for line in (BASE / "facts_v0_2.jsonl").read_text(encoding="utf-8").splitlines()]
    for f in facts:
        root = roots[f["doc_id"]]
        table = root.xpath(f["table_xpath"])[0]
        header_row = table.xpath(".//tr")[0]
        year_row = table.xpath(".//tr")[2 if f["balance_or_flow"] == "flow" else 0]
        headers = header_row.xpath("./th|./td")
        if f["balance_or_flow"] == "balance":
            specific_header = headers[f["table_col_index"]]
        else:
            # Match the HTML column spans, including the blank separator at col4.
            cursor = 0
            specific_header = None
            for head in headers:
                span = int(head.get("colspan", "1"))
                if cursor <= f["table_col_index"] < cursor+span:
                    specific_header = head
                    break
                cursor += span
            assert specific_header is not None
        f["period_header_group_pointer_previous"] = f["period_header_pointer"]
        f["year_header_group_pointer_previous"] = f["year_header_pointer"]
        f["period_header_pointer"] = root.getroottree().getpath(specific_header)
        f["year_header_pointer"] = root.getroottree().getpath(year_row.xpath("./th|./td")[f["table_col_index"]])
        f["normalization_revision_id"] = "p03-factual-reference-0.3"
    (BASE / "facts_v0_3.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in facts)+"\n", encoding="utf-8")
    write_csv("document_manifest_v0_3.csv", documents)
    with (BASE / "extraction_audit_v0_2.csv").open(encoding="utf-8", newline="") as stream:
        audits = list(csv.DictReader(stream))
    facts_by_id = {f["claim_id"]: f for f in facts}
    for row in audits:
        f = facts_by_id[row["claim_id"]]
        header = " ".join(roots[f["doc_id"]].xpath(f["period_header_pointer"])[0].text_content().split())
        expected = "Three Months Ended June 30" if f["period_label"] == "Q4" else "Twelve Months Ended June 30" if f["period_label"] == "FY" else f"June 30, {f['fiscal_year']}"
        row["period_header_confirmed"] = re.sub(r"\s+", "", expected) in re.sub(r"\s+", "", header)
        row["period_header_pointer"] = f["period_header_pointer"]
        row["header_audit_revision_reason"] = "normalize_whitespace_and_bind_specific_colspan_group; numeric_values_unchanged"
    write_csv("extraction_audit_v0_3.csv", audits)
    print(json.dumps({"facts":len(facts),"period_specific_headers_bound":len(facts),"scalar_numeric_values_changed":0}))


def metadata():
    registry = [dict(source_id="US-MSFT-IR-FACTUAL-REFERENCE", provider="Microsoft Corporation", source_type="official_ir_factual_reference",
                     landing_url="https://www.microsoft.com/en-us/investor/default", terms_url=TERMS,
                     terms_version="displayed_Last_Updated_2022-02-07", checked_at="2026-10-05",
                     accessible_period="actually_observed_FY2024_Q4_and_FY2025_Q4_releases; scope_reference_FY2025_annual; not_full_history",
                     authentication="none", manual_read="conditional", automated_access="conditional", storage_policy="conditional",
                     internal_analysis_policy="conditional", ai_input_policy="unresolved", ai_training_policy="unresolved",
                     external_transfer_policy="prohibited_for_original_network_copy", sharing_policy="prohibited_for_original_network_copy",
                     redistribution_policy="prohibited_for_original_network_copy", rate_limit_evidence="local_policy_single_request_at_a_time_minimum_1.1_seconds; not_official_numeric_rate_claim",
                     status="adopted_only_for_small_nonexpressive_local_factual_reference",
                     unresolved_reason="raw_AI_input_training_public_corpus_and_commercial_use_not_authorized_by_this_trial",
                     conditions_ref="source_conditions.md#msft-factual-reference", original_prose_ai_input=False,
                     normalized_fact_reference_scope="selected_numbers_periods_locations_standard_labels_reporting_membership_only")]
    write_csv("source_registry.csv", registry)
    outputs = ["facts_v0_3.jsonl", "document_manifest_v0_3.csv", "extraction_audit_v0_3.csv", "verification_report_v0_3.json",
               "business_relations.jsonl", "scope_corroboration.json", "source_registry.csv", "source_conditions.md",
               "access_trials.jsonl", "preflight_access_trials.jsonl"]
    code = Path(__file__).read_bytes()
    manifest = dict(run_id="US-P03-AVAILABLE-20261005", metadata_generated_at=now(),
                    source_policy_version="msft-small-nonexpressive-factual-reference-0.1", normalization_version="p03-factual-reference-0.3",
                    source_code_path=Path(__file__).as_posix(), source_code_sha256=hashlib.sha256(code).hexdigest(),
                    output_sha256={name:hashlib.sha256((BASE/name).read_bytes()).hexdigest() for name in outputs},
                    authoritative_numeric_facts="facts_v0_3.jsonl", authoritative_document_manifest="document_manifest_v0_3.csv",
                    source_data_documents_attempted=3, source_data_documents_private_acquired=3,
                    numeric_documents_attempted=2, numeric_documents_selected=2, scope_corroboration_documents=1,
                    policy_network_requests=3, data_network_requests=3, total_network_requests=6,
                    selected_numeric_occurrences=33, numeric_announcement_families=2,
                    reporting_relation_claims=6, unique_reporting_relations=3,
                    original_prose_ai_inputs=0, full_body_completeness_audits=0,
                    human_validation="waived_by_user_not_observed", gold=False, split_exposure="adaptation",
                    legacy_korean_artifacts_used=False, SEC_blocked_hosts_retried=False, NVIDIA_automated_requests=0)
    (BASE/"source_run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"authoritative_input":manifest["authoritative_numeric_facts"],"facts_sha256":manifest["output_sha256"]["facts_v0_3.jsonl"],"facts":33,"numeric_documents":2,"scope_supplement_documents":1}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("collect", "inspect", "extract", "verify", "corroborate", "refine-headers", "metadata"))
    args = parser.parse_args()
    {"collect": collect, "inspect": inspect_numbers, "extract": extract, "verify": verify, "corroborate": corroborate, "refine-headers": refine_headers, "metadata":metadata}[args.action]()
