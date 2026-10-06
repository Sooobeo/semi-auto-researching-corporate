"""Reserve one preselected source locally without exposing its facts or prose.

The only network candidate is Microsoft FY2026 Q1.  Metadata inspection is not
annotation, a completeness audit, or a parser development opportunity.  Run once;
later verification uses only stored bytes.  Failure records are never overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, parse, request, robotparser

from lxml import html

BASE = Path("artifacts/us_equity/p3/source_reservation")
HOST = "www.microsoft.com"
TERMS = f"https://{HOST}/en-us/legal/terms-of-use"
URL = f"https://{HOST}/en-us/Investor/earnings/FY-2026-Q1/press-release-webcast"
DOC_ID = "US-MSFT-FY2026-Q1-RELEASE"
FAMILY_ID = "US-MSFT-FY2026-Q1-EARNINGS"
UA = "semi-auto-researching-corporate/0.1 (personal noncommercial factual reference)"
VERSION = "p04-reserve-source-1.0"
CLIENT_DATE = "2026-10-06"


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(body):
    return hashlib.sha256(body).hexdigest()


def save_json(name, value):
    path = BASE / name
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def inspect_metadata(body):
    """No labels, values, prose, cell contents, or table counts leave this function."""
    root = html.fromstring(body)
    tree = root.getroottree()
    months = "January|February|March|April|May|June|July|August|September|October|November|December"
    dates = []
    for paragraph in root.xpath("//p"):
        content = " ".join(paragraph.text_content().split())
        if "REDMOND" not in content:
            continue
        match = re.search(rf"\b({months})\s+\d{{1,2}},\s+\d{{4}}\b", content)
        if match:
            dates.append({"date_raw": match.group(),
                          "date_normalized": datetime.strptime(match.group(), "%B %d, %Y").date().isoformat(),
                          "pointer": tree.getpath(paragraph), "origin": "body_dateline"})
    unique_dates = sorted({item["date_normalized"] for item in dates})
    page_dates = []
    for node in root.xpath("//meta[@content]"):
        kind = (node.get("property") or node.get("name") or "").lower()
        if kind in {"date", "dc.date", "article:published_time", "datepublished", "pubdate"}:
            value = node.get("content", "")
            # Never export an arbitrary meta value as if it were safe metadata.
            if re.fullmatch(r"[0-9TtZz:+. /-]{8,40}", value):
                page_dates.append({"value_raw": value, "pointer": tree.getpath(node), "origin": kind})
    return {"html_parsed": True, "has_document_body": bool(root.xpath("//body")),
            "has_tables": bool(root.xpath("//table")),
            "has_release_path_canonical": any(parse.urlsplit(x).path.rstrip("/").lower() ==
                                              parse.urlsplit(URL).path.rstrip("/").lower()
                                              for x in root.xpath("//link[@rel='canonical']/@href")),
            "has_terms_footer_link": any("terms-of-use" in x or "LinkId=521839" in x
                                         for x in root.xpath("//a/@href")),
            "dateline_date_evidence": dates, "page_publication_date_evidence": page_dates,
            "published_date": unique_dates[0] if len(unique_dates) == 1 else None,
            "published_at": None, "time_precision": "date" if len(unique_dates) == 1 else "unknown",
            "date_status": "unique_body_dateline_page_conflict_not_manually_audited" if len(unique_dates) == 1
                           else "unresolved_missing_or_conflicting_dateline",
            "full_body_audited": False, "numeric_extraction_performed": False,
            "source_prose_sent_to_ai": False}


def reserve():
    BASE.mkdir(parents=True, exist_ok=True)
    if (BASE / "access_trials.jsonl").exists() or (BASE / "document_manifest.json").exists():
        raise SystemExit("Existing reservation is immutable; run verify, not reserve.")
    private = BASE / "private"
    private.mkdir(exist_ok=True)
    ignore = subprocess.run(["git", "check-ignore", "-q", (private / "original.html").as_posix()], check=False)
    if ignore.returncode != 0:
        raise SystemExit("Private source path is not ignored by Git; no request made.")
    opener = request.build_opener(NoRedirect())
    trials = []
    last_request_started = None
    interval = 2.0
    stop_host = False

    def record(row):
        trials.append(row)
        with (BASE / "access_trials.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")

    def get(url, filename, kind):
        nonlocal last_request_started, stop_host
        parsed = parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != HOST or parsed.username or parsed.password:
            raise ValueError("Unreviewed URL; request denied.")
        if stop_host:
            record({"url": url, "resource_kind": kind, "attempted": False,
                    "status": "host_stopped_after_prior_failure"})
            return None
        if last_request_started is not None:
            time.sleep(max(0, interval - (time.monotonic() - last_request_started)))
        last_request_started = time.monotonic()
        observed = now()
        try:
            with opener.open(request.Request(url, headers={"User-Agent": UA}), timeout=30) as response:
                body = response.read(8 * 1024 * 1024 + 1)
                final_url = response.url
                mime = response.headers.get_content_type()
                status = response.status
                if len(body) > 8 * 1024 * 1024:
                    raise ValueError("Response exceeded predeclared storage bound.")
                if final_url != url or parse.urlsplit(final_url).hostname != HOST or status != 200:
                    raise ValueError("Unexpected response URL or HTTP status.")
            with (private / filename).open("xb") as stream:
                stream.write(body)
            row = {"url": url, "final_url": final_url, "final_host_verified": True,
                   "resource_kind": kind, "attempted": True, "observed_at": observed,
                   "http_status": status, "mime": mime, "sha256": digest(body),
                   "byte_size": len(body), "storage_uri": (private / filename).as_posix(),
                   "status": "downloaded_private_reference", "error": None,
                   "request_method": "urllib_single_host_no_redirect_no_retry",
                   "minimum_host_interval_seconds": interval}
            record(row)
            return body
        except (error.HTTPError, error.URLError, TimeoutError, OSError, ValueError) as exc:
            # Never log headers, response bodies, exception strings, or credentials.
            stop_host = True
            record({"url": url, "final_url": None, "final_host_verified": False,
                    "resource_kind": kind, "attempted": True, "observed_at": observed,
                    "http_status": getattr(exc, "code", None), "status": "failed_stopped_no_retry",
                    "error": type(exc).__name__, "request_method": "urllib_single_host_no_redirect_no_retry"})
            return None

    def finish_failure(reason):
        if not any(row["resource_kind"] == "earnings_release" for row in trials):
            record({"url": URL, "resource_kind": "earnings_release", "attempted": False,
                    "status": "not_attempted_preflight_failed", "reason": reason})
        save_json("document_manifest.json", {"doc_id": DOC_ID, "event_family_id": FAMILY_ID,
                  "source_url": URL, "status": "reservation_failed", "reason": reason,
                  "split_exposure": "candidate_unlabeled", "metadata_inspector_version": VERSION})
        verify()
        print(json.dumps({"status": "reservation_failed", "doc_id": DOC_ID, "reason": reason}))

    robots = get(f"https://{HOST}/robots.txt", "robots.txt", "robots_policy")
    if robots is None:
        finish_failure("robots_unavailable")
        return
    rp = robotparser.RobotFileParser()
    rp.parse(robots.decode("utf-8", "replace").splitlines())
    interval = max(interval, float(rp.crawl_delay(UA) or rp.crawl_delay("*") or 0))
    rate = rp.request_rate(UA) or rp.request_rate("*")
    if rate:
        interval = max(interval, rate.seconds / rate.requests)
    policy = {"checked_on_client_date": CLIENT_DATE, "checked_at": now(), "robots_url": f"https://{HOST}/robots.txt",
              "robots_sha256": digest(robots), "user_agent": UA,
              "terms_allowed_by_robots": rp.can_fetch(UA, TERMS),
              "candidate_allowed_by_robots": rp.can_fetch(UA, URL),
              "minimum_interval_seconds": interval,
              "robots_does_not_establish_storage_or_ai_rights": True}
    save_json("robots_review.json", policy)
    if not policy["terms_allowed_by_robots"] or not policy["candidate_allowed_by_robots"]:
        finish_failure("robots_disallowed")
        return
    terms = get(TERMS, "microsoft_terms.html", "terms_policy")
    if terms is None:
        finish_failure("terms_unavailable")
        return
    terms_root = html.fromstring(terms)
    headings = terms_root.xpath("//h2[normalize-space(.)='Documents']")
    paras = []
    if len(headings) == 1:
        for sibling in headings[0].itersiblings():
            if sibling.tag == "h2":
                break
            if sibling.tag == "p":
                paras.append(" ".join(sibling.text_content().split()))
    notice = "\n\n".join(paras)
    required_fragments = ["Permission to use Documents", "press releases", "copyright notice",
                          "permission notice", "informational and non-commercial or personal use only",
                          "will not be copied or posted on any network computer", "no modifications"]
    terms_ok = all(fragment in notice for fragment in required_fragments)
    terms_review = {"checked_at": now(), "checked_on_client_date": CLIENT_DATE, "url": TERMS,
                    "sha256": digest(terms), "documents_permission_section_found": len(headings) == 1,
                    "expected_narrow_permission_conditions_found": terms_ok,
                    "review_basis": "official_web_terms_read_and_local_conditions_check",
                    "terms_displayed_update": "2022-02-07", "broad_ai_or_training_permission": "unresolved"}
    save_json("terms_review.json", terms_review)
    if not terms_ok:
        finish_failure("terms_changed_or_narrow_permission_not_verified")
        return
    permission = ("Microsoft Documents permission notice\nSource: " + TERMS + "\n"
                  "Copyright © Microsoft. All rights reserved.\n\n" + notice + "\n\n"
                  "Local personal/noncommercial informational reference only. Original bytes are unmodified. "
                  "Do not share original HTML, page layout, graphics or prose; do not send them to AI services. "
                  "This reservation confers no corpus, training or redistribution permission.\n")
    (private / "permission_notice.txt").write_text(permission, encoding="utf-8")
    body = get(URL, "msft_fy2026_q1.html", "earnings_release")
    if body is None:
        finish_failure("candidate_access_failed_no_substitute")
        return
    trial = trials[-1]
    try:
        metadata = inspect_metadata(body)
    except (ValueError, TypeError, IndexError) as exc:
        metadata = {"html_parsed": False, "metadata_status": "metadata_inspection_failed",
                    "error": type(exc).__name__, "full_body_audited": False, "source_prose_sent_to_ai": False}
    manifest = {"doc_id": DOC_ID, "revision_id": f"{DOC_ID}-R-{digest(body)[:12]}",
                "event_family_id": FAMILY_ID, "source_id": "US-MSFT-IR-P04-RESERVATION",
                "company_id": "US-MSFT", "source_url": URL, "final_url": trial["final_url"],
                "final_host_verified": True, "observed_at": trial["observed_at"],
                "sha256": digest(body), "mime": trial["mime"], "storage_uri": trial["storage_uri"],
                "status": "reserved_document_unlabeled", "split_exposure": "metadata_only_reserved",
                "parser_adaptation_performed": False, "human_annotation_count": 0,
                "gold_status": "not_created", "untouched_test_status": "not_claimed",
                "metadata_inspector_version": VERSION, "rights_ref": "source_conditions.md",
                "data_boundary": "no_facts_labels_or_prose_exposed", **metadata}
    save_json("document_manifest.json", manifest)
    verify()
    print(json.dumps({key: manifest.get(key) for key in ("doc_id", "revision_id", "status", "published_date",
                     "sha256", "observed_at", "mime", "has_document_body", "has_tables",
                     "split_exposure", "source_prose_sent_to_ai")}, ensure_ascii=False))


def verify():
    manifest = json.loads((BASE / "document_manifest.json").read_text(encoding="utf-8"))
    trials = [json.loads(line) for line in (BASE / "access_trials.jsonl").read_text(encoding="utf-8").splitlines()]
    stored = [row for row in trials if row["status"] == "downloaded_private_reference"]
    for row in stored:
        path = Path(row["storage_uri"])
        assert digest(path.read_bytes()) == row["sha256"], "Private stored hash mismatch"
        assert path.resolve().is_relative_to((BASE / "private").resolve()), "Private path escaped reservation"
        assert subprocess.run(["git", "check-ignore", "-q", path.as_posix()], check=False).returncode == 0
    if manifest["status"] == "reserved_document_unlabeled":
        assert not manifest["parser_adaptation_performed"]
        assert not manifest["source_prose_sent_to_ai"]
        assert manifest["gold_status"] == "not_created"
        assert (BASE / "private/permission_notice.txt").is_file()
    result = {"verified_at": now(), "stored_files_hash_verified": len(stored),
              "stored_files_hash_attempted": len(stored), "private_paths_git_ignored": True,
              "candidate_documents": 1,
              "candidate_documents_access_attempted": sum(row["resource_kind"] == "earnings_release" and row.get("attempted", False) for row in trials),
              "candidate_documents_reserved": int(manifest["status"] == "reserved_document_unlabeled"),
              "network_requests_attempted": sum(bool(row.get("attempted")) for row in trials),
              "gold_documents": 0, "full_body_manual_audits": 0, "prose_ai_inputs": 0,
              "status": "passed_metadata_reservation_integrity_only"}
    # Verification runs are append-only so the original evidence remains visible.
    with (BASE / "verification_runs.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False) + "\n")
    if not (BASE / "reservation_summary.json").exists():
        candidate_trial = next(row for row in trials if row["resource_kind"] == "earnings_release")
        rights_review_path = BASE / "terms_review.json"
        rights_verified = (rights_review_path.exists() and
                           json.loads(rights_review_path.read_text(encoding="utf-8"))
                           .get("expected_narrow_permission_conditions_found", False))
        summary = {"schema_version": "p04-reservation-summary-1.0", "candidate_documents": 1,
                   "doc_id": DOC_ID, "revision_id": manifest.get("revision_id"),
                   "event_family_id": FAMILY_ID, "source_url": URL,
                   "final_url": manifest.get("final_url"), "published_date": manifest.get("published_date"),
                   "time_precision": manifest.get("time_precision", "unknown"),
                   "observed_at": manifest.get("observed_at"),
                   "requested": candidate_trial.get("attempted", False),
                   "http_status": candidate_trial.get("http_status"),
                   "status": manifest["status"], "metadata_only": True,
                   "metadata_status": "inspected" if manifest.get("html_parsed") else "unresolved",
                   "rights_status": "conditional_local_personal_noncommercial_reference_only" if rights_verified else "unresolved",
                   "raw_hash_status": "verified" if manifest["status"] == "reserved_document_unlabeled" else "not_available",
                   "sha256": manifest.get("sha256"), "values_exposed": False,
                   "source_prose_exposed": False, "labels_created": False,
                   "untouched_test_claimed": False, "parser_adaptation_performed": False,
                   "rights_ref": "source_conditions.md", "source_registry_ref": "source_registry.csv",
                   "verification_ref": "verification_runs.jsonl", "summary_created_at": now(),
                   "candidate_documents_access_attempted": result["candidate_documents_access_attempted"],
                   "candidate_documents_reserved": result["candidate_documents_reserved"],
                   "human_gold_count": 0, "manual_full_body_audits": 0,
                   "open_items": ["full_body_completeness_not_audited", "source_facts_unlabeled",
                                  "page_date_dateline_conflicts_not_manually_audited",
                                  "AI_input_training_rights_unresolved", "comparison_column_leakage_not_inspected"]}
        save_json("reservation_summary.json", summary)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["reserve", "verify"])
    args = parser.parse_args()
    globals()[args.action]()
