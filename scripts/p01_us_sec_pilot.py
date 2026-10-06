"""Small SEC feasibility probe. No issuer/news crawling, LLMs, or silent retries.

API resources, filing documents, and fact records have separate denominators.
Each invocation needs a fresh output directory; downloaded bytes stay ignored.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

VERSION = "sec-pilot-0.1.1"
ROOT = Path(__file__).resolve().parents[1]
UA = "SemiAutoResearchFeasibility/0.1 (+https://github.com/Sooobeo/semi-auto-researching-corporate)"
TERMS = "https://www.sec.gov/about/webmaster-frequently-asked-questions"
COMPANIES = [("US-MSFT", "0000789019"), ("US-NVDA", "0001045810")]
TAGS = [
    ("revenue", ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"]),
    ("operating_income", ["OperatingIncomeLoss"]),
    ("net_income", ["NetIncomeLoss"]),
    ("operating_cash_flow", ["NetCashProvidedByUsedInOperatingActivities"]),
    ("capital_expenditure", ["PaymentsToAcquirePropertyPlantAndEquipment"]),
    ("assets", ["Assets"]),
    ("liabilities", ["Liabilities"]),
    ("cash", ["CashAndCashEquivalentsAtCarryingValue"]),
]


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def csvout(path, rows, fields=None):
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def source_gate(registry, source_id):
    row = registry.get(source_id)
    if row is None:
        return "source_policy_missing"
    for field in ("automated_access", "storage_policy", "internal_analysis_policy"):
        if row.get(field) not in {"allowed", "conditional"}:
            return f"source_policy_{field}_held"
    if not row.get("terms_url") or not row.get("checked_at"):
        return "source_policy_evidence_missing"
    # Conditional SEC permission is limited to the reviewed local factual method.
    if source_id not in {"SEC_SUBMISSIONS_API", "SEC_COMPANYFACTS_API", "SEC_EDGAR_ARCHIVES"}:
        return "source_policy_not_adopted_for_this_parser"
    if "blocked" in row.get("adoption_decision", "") or "blocked" in row.get("local_access_status", ""):
        return "held_by_source_registry_host_block"
    if row.get("status") not in {"allowed", "conditional"}:
        return "source_policy_unresolved"
    return None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Client:
    def __init__(self):
        self.opener = urllib.request.build_opener(NoRedirect())
        self.robots = {}
        self.blocked_hosts = set()
        self.last_request = 0.0
        self.policy_trials = []

    def request(self, url):
        host = urllib.parse.urlsplit(url).netloc
        if host not in {"www.sec.gov", "data.sec.gov"}:
            return None, "redirect_domain_not_adopted", None, url
        if host in self.blocked_hosts:
            return None, "host_blocked_after_403_or_429", None, url
        time.sleep(max(0, 1.0 - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
        try:
            with self.opener.open(req, timeout=30) as resp:
                return resp.read(), "downloaded", resp.status, resp.geturl()
        except urllib.error.HTTPError as e:
            if e.code in {403, 429}:
                self.blocked_hosts.add(host)
            # Do not expose response headers or error body. No retry or alternate UA.
            return None, f"http_{e.code}", e.code, url
        except (urllib.error.URLError, TimeoutError, OSError):
            return None, "network_error", None, url

    def allowed(self, url):
        host = urllib.parse.urlsplit(url).netloc
        if host not in self.robots:
            ru = f"https://{host}/robots.txt"
            body, status, code, _ = self.request(ru)
            if body is not None:
                rp = urllib.robotparser.RobotFileParser()
                rp.parse(body.decode("utf-8", errors="replace").splitlines())
                self.robots[host] = rp
                decision = "parsed"
            elif code == 404:
                self.robots[host] = True
                decision = "no_robots_404"
            else:
                self.robots[host] = False
                decision = "unresolved_fail_closed"
            self.policy_trials.append({"url": ru, "status": status, "http_status": code,
                                       "decision": decision, "observed_at": now()})
        rp = self.robots[host]
        return rp if isinstance(rp, bool) else rp.can_fetch(UA, url)

    def fetch(self, url):
        if not self.allowed(url):
            return None, "robots_denied_or_unresolved", None, url
        # Redirects are stopped. A new final host requires a separate policy review.
        return self.request(url)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    ap.add_argument("--cutoff", default="2026-10-05")
    ap.add_argument("--run-id", default="us-sec-pilot-20261005-001")
    ap.add_argument("--blocked-host", action="append", default=[])
    ap.add_argument("--source-registry", default="artifacts/us_equity/p0/source_registry.csv")
    args = ap.parse_args()
    out = (ROOT / args.output).resolve()
    base = (ROOT / "artifacts/us_equity/p0").resolve()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", args.run_id):
        raise SystemExit("Run ID must contain only letters, digits, underscores, and hyphens.")
    if not out.is_relative_to(base) or out.exists():
        raise SystemExit("Output must be a NEW directory inside artifacts/us_equity/p0.")
    raw = (base / "raw" / args.run_id).resolve()
    if not raw.is_relative_to(base / "raw") or raw.exists():
        raise SystemExit("Raw run directory already exists; select a new run ID.")
    registry_path = (ROOT / args.source_registry).resolve()
    if not registry_path.is_relative_to(base):
        raise SystemExit("Source registry must be inside the active US p0 directory.")
    with registry_path.open(encoding="utf-8-sig", newline="") as f:
        registry_rows = list(csv.DictReader(f))
    registry = {r["source_id"]: r for r in registry_rows}
    if len(registry) != len(registry_rows):
        raise SystemExit("Duplicate source policy IDs.")
    out.mkdir(parents=True)
    raw.mkdir(parents=True)
    started = now()
    cutoff = date.fromisoformat(args.cutoff)
    client = Client()
    client.blocked_hosts.update(args.blocked_host)
    api_manifest, trials, entities, docs, observations, blocks, audits, parsers = [], [], [], [], [], [], [], []
    selected_filings = []

    for company_id, cik in COMPANIES:
        payloads = {}
        for resource, url in [("submissions", f"https://data.sec.gov/submissions/CIK{cik}.json"),
                              ("companyfacts", f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json")]:
            observed = now()
            source_id = "SEC_SUBMISSIONS_API" if resource == "submissions" else "SEC_COMPANYFACTS_API"
            held = source_gate(registry, source_id)
            body, status, code, final = (None, held, None, url) if held else client.fetch(url)
            doc_id = f"SEC-API-{cik}-{resource}"
            row = {"resource_id": doc_id, "company_id": company_id, "resource_kind": resource,
                   "source_id": source_id, "source_url": url, "final_url": final,
                   "observed_at": observed, "http_status": code, "access_status": status,
                   "sha256": None, "revision_id": None, "byte_size": None, "storage_uri": None,
                   "rights_basis_ref": TERMS, "published_at": None,
                   "published_date": None, "time_precision": "unknown", "split_exposure": "adaptation"}
            if body is not None:
                row.update(sha256=sha(body), revision_id=sha(body)[:16], byte_size=len(body))
                file = raw / f"{cik}_{resource}_{sha(body)[:16]}.json"
                file.write_bytes(body)
                row["storage_uri"] = file.relative_to(ROOT).as_posix()
                try:
                    payloads[resource] = json.loads(body)
                    row["access_status"] = "valid_json_payload"
                except (ValueError, UnicodeDecodeError):
                    row["access_status"] = "not_valid_json"
            api_manifest.append(row)
            trials.append({"trial_id": f"{args.run_id}-{doc_id}", "resource_kind": "api_payload",
                           "resource_id": doc_id, "source_url": url, "observed_at": observed,
                           "http_status": code, "status": row["access_status"],
                           "original_filing_body_read": False})
            parsers.append({"resource_id": doc_id, "method": "stdlib_json", "version": VERSION,
                            "attempted": body is not None, "status": row["access_status"],
                            "full_filing_text_extraction": "not_attempted"})
        submissions = payloads.get("submissions")
        facts = payloads.get("companyfacts")
        if not submissions:
            entities.append({"company_id": company_id, "cik_candidate": cik, "mapping_status": "not_verified_access_failed"})
            continue
        entities.append({"company_id": company_id, "entity_id": company_id,
                         "legal_name": submissions["name"], "cik": str(submissions["cik"]).zfill(10),
                         "tickers": json.dumps(submissions.get("tickers", [])),
                         "exchanges": json.dumps(submissions.get("exchanges", [])),
                         "fiscal_year_end_raw": submissions.get("fiscalYearEnd"),
                         "scope_id": company_id + "-CONSOLIDATED", "consolidation": "consolidated",
                         "mapping_status": "SEC_metadata_verified_issuer_cross_check_pending",
                         "evidence_ref": f"SEC-API-{cik}-submissions", "registry_version": VERSION})
        recent = submissions["filings"]["recent"]
        selections = []
        for form in ["10-K", "10-Q"]:
            candidates = [i for i, v in enumerate(recent["form"]) if v == form
                          and recent["filingDate"][i] <= args.cutoff]
            if candidates:
                selections.append(max(candidates, key=lambda i: recent["filingDate"][i]))
        for i in selections:
            accn = recent["accessionNumber"][i]
            doc_id = f"SEC-{cik}-{accn}"
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accn.replace('-', '')}/{recent['primaryDocument'][i]}"
            form, report_end = recent["form"][i], recent["reportDate"][i]
            doc = {"doc_id": doc_id, "company_id": company_id, "source_id": "SEC_EDGAR_ARCHIVES",
                   "source_url": url, "attachment_url": url, "final_url": None,
                   "rights_basis_ref": TERMS, "title": f"{submissions['name']} {form} {report_end}",
                   "language": "en", "published_at": None, "published_date": recent["filingDate"][i],
                   "time_precision": "date", "timezone": "unknown", "observed_at": now(),
                   "sec_acceptance_datetime_raw": recent.get("acceptanceDateTime", [None]*len(recent["form"]))[i],
                   "reference_period_start": None, "reference_period_end": report_end,
                   "period_basis": "fiscal", "fiscal_year": None, "fiscal_quarter": None,
                   "format": "html", "sha256": None, "byte_size": None, "storage_uri": None,
                   "revision_id": None, "parse_status": "not_attempted", "parser_version": VERSION,
                   "split_exposure": "adaptation", "accession_number": accn, "form": form,
                   "source_revision_of": None, "event_family_id": f"FAMILY-{cik}-{accn}",
                   "body_completeness": "not_audited"}
            held = source_gate(registry, "SEC_EDGAR_ARCHIVES")
            body, status, code, final = (None, held, None, url) if held else client.fetch(url)
            doc.update(access_status=status, http_status=code, final_url=final)
            if body is not None:
                file = raw / f"{cik}_{accn}_{sha(body)[:16]}.html"
                file.write_bytes(body)
                doc.update(sha256=sha(body), byte_size=len(body), revision_id=sha(body)[:16],
                           storage_uri=file.relative_to(ROOT).as_posix(), parse_status="stored_not_body_audited")
            docs.append(doc)
            selected_filings.append({"doc_id": doc_id, "accession_number": accn, "company_id": company_id,
                                     "form": form, "report_end": report_end, "source_url": url})
            trials.append({"trial_id": f"{args.run_id}-{doc_id}", "resource_kind": "filing_document",
                           "resource_id": doc_id, "source_url": url, "observed_at": doc["observed_at"],
                           "http_status": code, "status": status, "original_filing_body_read": False})
            if not facts:
                continue
            payload_row = next(r for r in api_manifest if r["resource_id"] == f"SEC-API-{cik}-companyfacts")
            gaap = facts.get("facts", {}).get("us-gaap", {})
            for metric_name, tag_candidates in TAGS:
                found = []
                for tag in tag_candidates:
                    units = gaap.get(tag, {}).get("units", {})
                    entries = units.get("USD", [])
                    matches = [(j, r) for j, r in enumerate(entries)
                               if r.get("accn") == accn and r.get("end") == report_end
                               and r.get("filed", "9999") <= args.cutoff]
                    if matches:
                        found = [(tag, j, r) for j, r in matches]
                        break
                if not found:
                    audits.append({"doc_id": doc_id, "check_type": "tag_coverage", "metric": metric_name,
                                   "status": "not_found", "reason": "selected_standard_tag_or_unit_not_found_not_proof_of_nondisclosure"})
                for tag, j, value in found:
                    pointer = f"/facts/us-gaap/{tag}/units/USD/{j}"
                    source_id = payload_row["resource_id"]
                    obs_id = "OBS-" + sha(f"{cik}|{accn}|{pointer}".encode())[:20]
                    duration = (date.fromisoformat(value["end"]) - date.fromisoformat(value["start"])).days + 1 if value.get("start") else None
                    block_id = obs_id + "-B"
                    raw_text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
                    blocks.append({"block_id": block_id, "doc_id": source_id,
                                   "revision_id": payload_row["revision_id"], "block_type": "structured_fact",
                                   "raw_text": raw_text, "normalized_text": raw_text,
                                   "offset_mapping": "identity_unicode_code_point_0_based_half_open",
                                   "source_json_pointer": pointer, "page_number": None, "header_refs": [],
                                   "extraction_method": "SEC_companyfacts_json_pointer", "extraction_version": VERSION})
                    obs = {"observation_id": obs_id, "doc_id": doc_id, "source_resource_id": source_id,
                           "revision_id": payload_row["revision_id"], "company_id": company_id,
                           "scope_id": company_id + "-CONSOLIDATED", "event_family_id": doc["event_family_id"],
                           "metric_candidate": metric_name, "metric_id": None, "metric_raw": tag,
                           "taxonomy": "us-gaap", "value_raw": str(value["val"]),
                           "numeric_value": str(Decimal(str(value["val"]))), "currency": "USD", "scale": "1",
                           "canonical_unit": "USD", "unit_raw": "USD", "period_start": value.get("start"),
                           "period_end": value["end"], "period_duration_days": duration,
                           "balance_or_flow": "flow" if value.get("start") else "balance",
                           "fiscal_year_filing_context_raw": value.get("fy"), "fiscal_quarter_filing_context_raw": value.get("fp"),
                           "calendar_frame_raw": value.get("frame"), "accession_number": accn,
                           "published_date": value["filed"], "published_at": None, "time_precision": "date",
                           "observed_at": payload_row["observed_at"], "modality": "actual_reported",
                           "evidence_status": "SEC_aggregated_company_reported_fact_original_table_not_audited",
                           "evidence": [{"block_id": block_id, "source_json_pointer": pointer,
                                         "start": 0, "end": len(raw_text)}],
                           "missing_reason": None, "split_exposure": "adaptation", "run_id": args.run_id,
                           "schema_version": "us-observation-0.1.0", "registry_version": VERSION}
                    observations.append(obs)
                    audits.append({"doc_id": doc_id, "check_type": "structured_numeric_round_trip",
                                   "observation_id": obs_id, "metric": metric_name, "status": "passed",
                                   "reason": "JSON_pointer_value_period_USD_match_original_filing_table_cross_check_pending"})

    csvout(out / "api_payload_manifest.csv", api_manifest)
    csvout(out / "access_trials.csv", trials)
    csvout(out / "entities.csv", entities)
    csvout(out / "document_manifest.csv", docs, list(docs[0]) if docs else ["doc_id", "access_status"])
    csvout(out / "parser_trials.csv", parsers)
    csvout(out / "extraction_audit.csv", audits, list(dict.fromkeys(k for r in audits for k in r)) or ["doc_id", "status"])
    csvout(out / "robots_trials.csv", client.policy_trials,
           ["url", "status", "http_status", "decision", "observed_at"])
    dump(out / "selected_filings.json", selected_filings)
    for filename, rows in [("observations.jsonl", observations), ("blocks.jsonl", blocks)]:
        (out / filename).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    summary = {"api_resources_selected": len(api_manifest),
               "api_resources_network_attempted": sum(r["http_status"] is not None or r["access_status"] == "network_error" for r in api_manifest),
               "api_resources_valid_json": sum(r["access_status"] == "valid_json_payload" for r in api_manifest),
               "filing_candidates": len(docs),
               "filing_network_attempted": sum(r["http_status"] is not None or r["access_status"] == "network_error" for r in docs),
               "filing_downloaded": sum(r["sha256"] is not None for r in docs),
               "filing_body_manual_audited": 0, "complete_filing_bodies_verified": 0,
               "structured_observations": len(observations), "business_relations_verified": 0,
               "news_article_candidates": 0, "news_article_bodies_verified": 0,
               "independent_reporting_expressions": 0, "comparable_cross_outlet_pairs": 0,
               "ai_original_text_input_calls": 0, "llm_training_runs": 0}
    dump(out / "summary.json", summary)
    git_revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dump(out / "run_manifest.json", {"run_id": args.run_id, "started_at": started, "completed_at": now(),
         "client_reference_date": args.cutoff, "scope_status": "agent_selected_access_trial_candidates_team_pending",
         "code_revision": git_revision, "script_sha256": sha(Path(__file__).read_bytes()),
         "python_version": platform.python_version(), "parser_version": VERSION,
         "companies_config_sha256": sha(json.dumps(COMPANIES).encode()), "legacy_inputs": [],
         "source_registry_path": registry_path.relative_to(ROOT).as_posix(),
         "source_registry_sha256": sha(registry_path.read_bytes()),
         "rate_policy": "one_request_per_second_sequential_no_retry",
         "redirect_policy": "stop_for_separate_final_domain_review", "ai_processing": "none",
         "blocked_hosts_from_prior_evidence": args.blocked_host,
         "summary": summary})
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
