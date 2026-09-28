"""Small, fail-closed P01 HTML pilot; never grants or infers source rights.

gate/collect require --input, --rights-registry and a NEW --output-dir.
gate performs no network requests. collect supports unauthenticated static HTML
only: it is not a NewsStore API adapter. Each redirect target needs its own exact
domain/path rights row and robots approval before it is requested. Unknown
rights, authentication, publication coverage, robots, and paywalls stop collection.
An explicit --research-authorization JSON can authorize only the fixed, at most
39-candidate noncommercial publisher pilot requested on 2026-09-22. It records
user research authorization separately from unresolved source rights. It never
overrides an explicit relevant source denial, robots, paywall, or URL allowlist.

Candidate CSV: candidate_id,source_id,source_url; optional doc_id,event_family_id,
company_id,scope_id,reference_period,publisher_published_raw,provider_published_raw.
Rights CSV: source_id,domain,url_path_prefix,terms_url,terms_checked_at,
rights_status,automated_access,raw_storage,internal_analysis,ai_input,ai_training,
external_transfer,sharing,redistribution,available_from,available_to,authentication.
Verified rows also need authorization_kind (contract/public_permission),
authorization_evidence_ref (URL or existing local file), authorization_valid_from
and authorization_valid_to (ISO dates; the latter may explicitly be unlimited).
Licensed sources additionally need contract_confirmation_status=verified and
contract_evidence_ref. Permissions are allowed/denied/unresolved, rights_status must be verified, dates
are YYYY-MM-DD; authentication=none. available_* concerns article publication,
not event/reference quarters. Optional body_xpath selects a reviewed HTML region.
AI permissions are recorded separately; this program never calls an AI service.

Raw HTML and extracted text stay under output-dir/raw. HTML extraction is always
pending human completeness review; XPath or identity offsets do not constitute
sentence/chunk gold. audit consumes the input manifest, never fixed sample sizes.
"""

import argparse
import csv
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.robotparser import RobotFileParser


SCHEMA_VERSION = "p01-domestic-pilot-0.2"
EXTRACTOR_VERSION = "p01-domestic-html-0.1"
USER_AGENT = "P01ResearchCrawler/0.2"
PERMISSIONS = ("automated_access", "metadata_storage", "raw_storage", "internal_analysis", "ai_input",
               "ai_training", "external_transfer", "embedding_storage", "derived_chunk_storage",
               "sharing", "redistribution")
LOCAL_PERMISSIONS = ("automated_access", "metadata_storage", "raw_storage", "internal_analysis", "derived_chunk_storage")
RESEARCH_SOURCE_IDS = {"HANKYUNG", "ETNEWS", "ZDNET_KR", "NEWSPIM", "EDAILY"}
SECRET_QUERY = re.compile(r"key|token|secret|password|auth|credential|signature|session", re.I)
MANIFEST_FIELDS = [
    "candidate_id", "doc_id", "source_id", "event_family_id", "company_id", "scope_id",
    "reference_period", "source_url", "source_url_sha256", "final_url", "final_url_sha256", "provenance_uri", "observed_at",
    "publisher_published_raw", "provider_published_raw", "published_precision",
    "publisher_date_candidates", "date_review", "rights_status", "rights_reason",
    "execution_basis", "research_authorization_sha256",
    "rights_registry_sha256", "rights_basis_urls", "rights_permissions", "fetch_status",
    "body_attempted", "body_request_count", "http_status", "deferred_until", "revision_id",
    "sha256", "storage_uri", "byte_size", "extraction_attempted", "extraction_status",
    "block_count", "body_chars", "location_status", "human_audit_status",
    "body_complete", "scope_fit", "production_origin", "claim_matching", "missing_reason",
    "schema_version", "extractor_version",
]


def utcnow():
    return datetime.now(timezone.utc)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows, fields):
    with Path(path).open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def safe_url(url):
    """Persist no query values, fragments, or userinfo, including unknown token names."""
    try:
        parts = urllib.parse.urlsplit(url)
        host = parts.hostname or ""
        if parts.port:
            host += ":" + str(parts.port)
        query = "query_values_redacted" if parts.query else ""
        return urllib.parse.urlunsplit((parts.scheme, host, parts.path, query, ""))
    except ValueError:
        return "invalid_url"


def valid_url(url):
    try:
        parts = urllib.parse.urlsplit(url)
        decoded_path = urllib.parse.unquote(parts.path)
        return (parts.scheme in ("http", "https") and bool(parts.hostname)
                and not any(ord(char) < 32 for char in url)
                and not any(segment in (".", "..") for segment in decoded_path.split("/"))
                and "\\" not in decoded_path and "%" not in decoded_path
                and not parts.username and not parts.password
                and parts.port in (None, 80, 443)
                and not any(SECRET_QUERY.search(k) for k, _ in urllib.parse.parse_qsl(parts.query)))
    except ValueError:
        return False


def publication_date(candidate):
    """No provider/system timestamp or reference-quarter substitution."""
    value = candidate.get("publisher_published_raw", "")
    if not re.match(r"^\d{4}-\d{2}-\d{2}(?:$|T| )", value):
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


class ResearchAuthorization:
    """An execution boundary for one user-approved sample, never a source license."""

    def __init__(self, path):
        raw = Path(path).read_bytes()
        data = json.loads(raw.decode("utf-8-sig"))
        if (data.get("schema_version") != "p01-research-authorization-0.1"
                or data.get("authorization_date") != "2026-09-22"
                or data.get("execution_basis") != "user_noncommercial_research"
                or data.get("purpose") != "noncommercial_research"
                or data.get("max_candidates") != 39
                or not data.get("authorization_id") or not data.get("user_instruction")):
            raise ValueError("unsupported research authorization")
        sources, candidates = data.get("sources", []), data.get("candidates", [])
        if not 1 <= len(sources) <= 5 or not 1 <= len(candidates) <= 39:
            raise ValueError("research authorization exceeds fixed pilot")
        self.source_domains = set()
        for source in sources:
            domain, source_id = source.get("domain", ""), source.get("source_id", "")
            if (source_id not in RESEARCH_SOURCE_IDS or source.get("source_type") != "direct_publisher_html"
                    or domain != domain.lower() or not valid_url("https://" + domain + "/")
                    or urllib.parse.urlsplit("https://" + domain).hostname != domain):
                raise ValueError("research source is not a direct pilot publisher")
            self.source_domains.add((source_id, domain))
        if len(self.source_domains) != len(sources):
            raise ValueError("duplicate research source domain")
        self.candidates = {}
        for candidate in candidates:
            identifier = candidate.get("candidate_id")
            urls = [candidate.get("source_url", "")] + candidate.get("allowed_redirect_urls", [])
            if not identifier or identifier in self.candidates:
                raise ValueError("missing or repeated research candidate")
            for url in urls:
                if not valid_url(url) or (candidate.get("source_id"), urllib.parse.urlsplit(url).hostname) not in self.source_domains:
                    raise ValueError("research URL outside approved publisher domains")
            self.candidates[identifier] = candidate
        self.sha256, self.execution_basis = digest(raw), data["execution_basis"]

    def check(self, candidate, url, rights):
        approved = self.candidates.get(candidate.get("candidate_id"))
        if (not approved or candidate.get("source_id") != approved["source_id"]
                or candidate.get("source_url") != approved["source_url"]):
            return False, "research_candidate_not_allowlisted"
        if url not in [approved["source_url"]] + approved.get("allowed_redirect_urls", []):
            return False, "research_url_not_allowlisted"
        if (not rights or rights.get("source_type") not in ("direct_publisher_unreviewed", "direct_publisher_html")
                or (candidate["source_id"], urllib.parse.urlsplit(url).hostname) not in self.source_domains):
            return False, "research_requires_exact_direct_publisher_registry"
        if rights.get("rights_status") == "denied":
            return False, "research_source_explicitly_denied"
        for key in LOCAL_PERMISSIONS:
            if rights.get(key) == "denied":
                return False, "research_permission_explicitly_denied_" + key
            if rights.get(key) not in ("allowed", "unresolved"):
                return False, "research_permission_not_recorded_" + key
        if re.search(r"required|authenticated_only", rights.get("authentication", ""), re.I):
            return False, "research_authentication_required"
        return True, "user_research_authorized_source_rights_unresolved"

    def validate_input(self, candidates):
        if len(candidates) > 39:
            raise ValueError("candidate count exceeds research pilot")
        for candidate in candidates:
            approved = self.candidates.get(candidate.get("candidate_id"))
            if (not approved or any(candidate.get(k) != approved.get(k)
                                    for k in ("source_id", "source_url"))):
                raise ValueError("input is outside research authorization")

    def exact_trace_url(self, candidate, hop):
        approved = self.candidates.get(candidate.get("candidate_id"), {})
        urls = [approved.get("source_url", "")] + approved.get("allowed_redirect_urls", [])
        return next((url for url in urls if digest(url.encode()) == hop.get("url_sha256")
                     and safe_url(url) == hop.get("url")), "")


class RightsRegistry:
    def __init__(self, rows, research_authorization=None):
        self.rows, self.research = rows, research_authorization

    def check(self, candidate, url):
        allowed, reason, row = self._strict_check(candidate, url)
        if self.research:
            research_allowed, research_reason = self.research.check(candidate, url, row)
            if not research_allowed:
                return False, research_reason, row
            if not allowed and row.get("rights_status") == "unresolved":
                return True, research_reason, row
        return allowed, reason, row

    def _strict_check(self, candidate, url):
        if not valid_url(url):
            return False, "invalid_or_credentialed_url", None
        parts = urllib.parse.urlsplit(url)
        matches = []
        for row in self.rows:
            prefix = row.get("url_path_prefix", "")
            path = urllib.parse.unquote(parts.path or "/")
            if (row.get("source_id") == candidate.get("source_id")
                    and row.get("domain", "").lower() == parts.hostname.lower()
                    and prefix.startswith("/") and path.startswith(prefix)):
                matches.append(row)
        if len(matches) != 1:
            return False, "missing_or_ambiguous_domain_path_rights", None
        row = matches[0]
        if row.get("rights_status") != "verified":
            return False, "rights_not_verified", row
        kind = row.get("authorization_kind")
        if kind not in ("contract", "public_permission"):
            return False, "authorization_kind_unverified", row
        def concrete_evidence(value):
            if not value:
                return False
            return valid_url(value) or Path(value).is_file()
        if not concrete_evidence(row.get("authorization_evidence_ref", "")):
            return False, "authorization_evidence_missing", row
        if row.get("source_type", "").startswith("licensed") and kind != "contract":
            return False, "licensed_source_requires_contract", row
        if kind == "contract" and (row.get("contract_confirmation_status") != "verified"
                                   or not concrete_evidence(row.get("contract_evidence_ref", ""))):
            return False, "contract_not_verified", row
        try:
            valid_from = date.fromisoformat(row.get("authorization_valid_from", ""))
            end_raw = row.get("authorization_valid_to", "")
            valid_to = date.max if end_raw == "unlimited" else date.fromisoformat(end_raw)
        except ValueError:
            return False, "authorization_validity_unknown", row
        if not valid_from <= utcnow().date() <= valid_to:
            return False, "authorization_not_currently_valid", row
        if not valid_url(row.get("terms_url", "")):
            return False, "missing_terms_basis", row
        try:
            date.fromisoformat(row.get("terms_checked_at", "")[:10])
        except ValueError:
            return False, "missing_terms_check_date", row
        for key in PERMISSIONS:
            if row.get(key) not in ("allowed", "denied", "unresolved"):
                return False, "unrecorded_permission_" + key, row
        for key in LOCAL_PERMISSIONS:
            if row.get(key) != "allowed":
                return False, "permission_not_allowed_" + key, row
        if row.get("authentication") != "none":
            return False, "authentication_requires_provider_adapter", row
        published = publication_date(candidate)
        if published is None:
            return False, "publisher_date_unknown_for_coverage", row
        try:
            start = date.fromisoformat(row.get("available_from", ""))
            end = date.fromisoformat(row.get("available_to", ""))
        except ValueError:
            return False, "publication_coverage_unknown", row
        if not start <= published <= end:
            return False, "publication_outside_verified_coverage", row
        return True, "verified_local_collection_only", row


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass
class Reply:
    status: int
    headers: dict = field(default_factory=dict)
    body: bytes = b""


def transport(url, limit):
    """No automatic redirect, response/error header logging, or ambient cookies."""
    opener = urllib.request.build_opener(NoRedirect())
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "text/html,text/plain"})
    try:
        response = opener.open(request, timeout=25)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        # Never read a redirect/error/paywall body into the corpus.
        body = response.read(limit + 1) if response.status == 200 else b""
        headers = {k.lower(): v for k, v in response.headers.items()
                   if k.lower() in ("location", "retry-after", "content-type")}
        return Reply(response.status, headers, body)


class StopFetch(Exception):
    def __init__(self, reason, until="", status=""):
        self.reason, self.until, self.status = reason, until, status


class Collector:
    def __init__(self, registry, request=transport, delay=3.0, max_wait=10.0,
                 now=utcnow, monotonic=time.monotonic, sleep=time.sleep):
        if not 2 <= delay <= 5:
            raise ValueError("delay must be between 2 and 5 seconds")
        self.registry, self.request = registry, request
        self.delay, self.max_wait = delay, max_wait
        self.now, self.monotonic, self.sleep = now, monotonic, sleep
        self.last, self.retry_until, self.robots = {}, {}, {}

    def _request(self, url, limit, gap=None):
        host = urllib.parse.urlsplit(url).hostname
        if host in self.retry_until and self.now() < self.retry_until[host]:
            raise StopFetch("deferred_host_retry_after", self.retry_until[host].isoformat())
        remaining = max(self.delay, gap or 0) - (self.monotonic() - self.last.get(host, -1e20))
        if remaining > self.max_wait:
            raise StopFetch("deferred_host_interval", (self.now() + timedelta(seconds=remaining)).isoformat())
        if remaining > 0:
            self.sleep(remaining)
        self.last[host] = self.monotonic()
        try:
            result = self.request(url, limit)
        except Exception as error:
            raise StopFetch("network_error_" + type(error).__name__) from None
        if result.status in (429, 503):
            raw = result.headers.get("retry-after", "")
            try:
                seconds = int(raw)
                until = self.now() + timedelta(seconds=max(seconds, 0))
            except ValueError:
                try:
                    until = parsedate_to_datetime(raw)
                    if until.tzinfo is None:
                        until = until.replace(tzinfo=timezone.utc)
                except (TypeError, ValueError, OverflowError):
                    until = self.now() + timedelta(hours=1)
            # A single request per candidate; no automatic retry even for short delays.
            until = max(until, self.now() + timedelta(seconds=self.delay))
            self.retry_until[host] = until
            raise StopFetch("deferred_http_" + str(result.status), until.isoformat(), result.status)
        return result

    def robots_check(self, url):
        parsed = urllib.parse.urlsplit(url)
        origin = parsed.scheme + "://" + parsed.netloc
        if origin not in self.robots:
            response = self._request(origin + "/robots.txt", 256000)
            if response.status != 200 or len(response.body) > 256000:
                # Including robots redirects and 404: fail closed, no target request.
                raise StopFetch("robots_unverified_http_" + str(response.status), status=response.status)
            text = response.body.decode("utf-8", "replace")
            if re.search(r"<\s*(?:html|!doctype)", text, re.I):
                raise StopFetch("robots_html_instead_of_rules")
            policy = RobotFileParser()
            policy.parse(text.splitlines())
            self.robots[origin] = policy
        policy = self.robots[origin]
        if not policy.can_fetch(USER_AGENT, url):
            raise StopFetch("robots_denied")
        delay = policy.crawl_delay(USER_AGENT) or 0
        rate = policy.request_rate(USER_AGENT)
        if rate and rate.requests:
            delay = max(delay, rate.seconds / rate.requests)
        return delay

    def fetch(self, candidate, row):
        current, seen = candidate.get("source_url", ""), set()
        trace, rights_rows = [], []
        row["_trace"] = trace
        for _ in range(6):
            allowed, reason, rights = self.registry.check(candidate, current)
            trace.append({"url": safe_url(current), "url_sha256": digest(current.encode()),
                          "rights_decision": reason,
                          "source_rights_status": rights.get("rights_status", "unresolved") if rights else "unresolved",
                          "execution_basis": row.get("execution_basis", "")})
            row["final_url"] = safe_url(current)
            row["final_url_sha256"] = digest(current.encode())
            if not allowed:
                row.update(rights_status=rights.get("rights_status", "unresolved") if rights else "unresolved", rights_reason=reason)
                raise StopFetch("deferred_rights_" + reason)
            rights_rows.append(rights)
            row["rights_basis_urls"] = json.dumps([safe_url(r["terms_url"]) for r in rights_rows])
            row["rights_permissions"] = json.dumps([{k: r[k] for k in PERMISSIONS} for r in rights_rows])
            if current in seen:
                raise StopFetch("redirect_loop")
            seen.add(current)
            gap = self.robots_check(current)
            # Count actual article request attempts, excluding robots and deferred queues.
            host = urllib.parse.urlsplit(current).hostname
            if host in self.retry_until and self.now() < self.retry_until[host]:
                raise StopFetch("deferred_host_retry_after", self.retry_until[host].isoformat())
            remaining = max(self.delay, gap) - (self.monotonic() - self.last.get(host, -1e20))
            if remaining > self.max_wait:
                raise StopFetch("deferred_host_interval", (self.now() + timedelta(seconds=remaining)).isoformat())
            row["body_attempted"] = "true"
            row["body_request_count"] += 1
            trace[-1]["body_requested"] = True
            response = self._request(current, 5_000_000, gap)
            row["http_status"] = response.status
            trace[-1]["http_status"] = response.status
            row["_trace"] = trace
            if response.status in (301, 302, 303, 307, 308):
                location = response.headers.get("location", "")
                if not location:
                    raise StopFetch("redirect_without_location")
                target = urllib.parse.urljoin(current, location)
                if urllib.parse.urlsplit(current).scheme == "https" and urllib.parse.urlsplit(target).scheme != "https":
                    raise StopFetch("redirect_scheme_downgrade")
                current = target
                continue
            if response.status != 200:
                raise StopFetch("http_" + str(response.status), status=response.status)
            if len(response.body) > 5_000_000:
                raise StopFetch("response_over_5mb")
            mime = response.headers.get("content-type", "").split(";")[0].strip().lower()
            if mime not in ("text/html", "application/xhtml+xml"):
                raise StopFetch("unsupported_content_type")
            # Recognized access gates are not parsed as article text or bypassed.
            if re.search(rb'"isAccessibleForFree"\s*:\s*(?:false|"false")', response.body, re.I):
                raise StopFetch("paywall_declared")
            return response.body, current, rights
        raise StopFetch("redirect_limit")


def extract_html(raw, row, rights):
    """Local parsing only. An extractor result is never a completeness assessment."""
    from importlib.metadata import version
    from lxml import html

    root = html.fromstring(raw)
    date_nodes = root.xpath('//meta[@property="article:published_time" or @name="date" or @itemprop="datePublished"] | //time[@datetime]')
    dates = [{"value": node.get("content") or node.get("datetime"),
              "xpath": node.getroottree().getpath(node)} for node in date_nodes]
    row["publisher_date_candidates"] = json.dumps(dates, ensure_ascii=False)
    distinct_dates = {d["value"] for d in dates}
    if row.get("publisher_published_raw"):
        distinct_dates.add(row["publisher_published_raw"])
    row["date_review"] = "pending_conflict_review" if len(distinct_dates) > 1 else "pending_original_comparison"
    xpath = rights.get("body_xpath", "")
    blocks = []
    if xpath:
        selected = root.xpath(xpath)
        if len(selected) != 1 or not hasattr(selected[0], "itertext"):
            raise ValueError("body_xpath_must_select_one_element")
        region = selected[0]
        nodes = region.xpath('.//*[self::h1 or self::h2 or self::h3 or self::p or self::li or self::table][not(ancestor::table)]')
        if not nodes:
            nodes = [region]
        for node in nodes:
            text = "".join(node.itertext())
            if not text.strip():
                continue
            blocks.append({"raw_text": text, "normalized_text": text,
                           "source_xpath": node.getroottree().getpath(node),
                           "location_status": "source_xpath_pending_audit",
                           "offset_mapping": {"status": "identity", "unit": "unicode_codepoint",
                                              "basis": "raw_block_text"},
                           "extraction_method": "registry_body_xpath",
                           "dependency_version": "lxml/" + version("lxml")})
    else:
        import trafilatura
        text = trafilatura.extract(raw, include_comments=False, include_tables=True) or ""
        if text:
            blocks.append({"raw_text": text, "normalized_text": text, "source_xpath": None,
                           "location_status": "text_only_unlocated",
                           "offset_mapping": {"status": "not_available", "unit": "unicode_codepoint",
                                              "basis": "raw_block_text"},
                           "extraction_method": "trafilatura_fallback",
                           "dependency_version": "trafilatura/" + version("trafilatura")})
    for index, block in enumerate(blocks, 1):
        block.update(block_id=f"{row['doc_id']}:{row['revision_id']}:B{index:05d}",
                     doc_id=row["doc_id"], revision_id=row["revision_id"],
                     extraction_version=EXTRACTOR_VERSION, schema_version=SCHEMA_VERSION,
                     evidence_eligible=False, human_audit_status="pending")
    row.update(extraction_status="extracted_pending_audit" if blocks else "no_text_extracted",
               block_count=len(blocks), body_chars=sum(len(b["raw_text"]) for b in blocks),
               location_status=blocks[0]["location_status"] if blocks else "not_available")
    return blocks


def base_row(candidate, index, registry_hash):
    url = candidate.get("source_url", "")
    row = dict.fromkeys(MANIFEST_FIELDS, "")
    for key in ("candidate_id", "doc_id", "source_id", "event_family_id", "company_id", "scope_id",
                "reference_period", "publisher_published_raw", "provider_published_raw"):
        row[key] = candidate.get(key, "")
    row.update(candidate_id=row["candidate_id"] or f"MISSING-ID-ROW-{index}",
               doc_id=row["doc_id"] or "NEWS-" + digest(url.encode())[:20],
               source_url=safe_url(url), source_url_sha256=digest(url.encode()),
               observed_at=utcnow().isoformat(), rights_registry_sha256=registry_hash,
               published_precision="date_only" if re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["publisher_published_raw"]) else "unverified",
               body_attempted="false", body_request_count=0, extraction_attempted="false",
               extraction_status="not_attempted", human_audit_status="not_started",
               body_complete="unknown", scope_fit="unknown", production_origin="unknown",
               claim_matching="unknown", location_status="not_available",
               schema_version=SCHEMA_VERSION, extractor_version=EXTRACTOR_VERSION)
    return row


def new_output(path):
    path = Path(path).resolve()
    # Refuse even an existing empty directory. No raw/revision/run can be overwritten.
    path.mkdir(parents=True, exist_ok=False)
    return path


def run(input_path, registry_path, output_dir, mode="gate", collector=None, research_authorization=None):
    if mode not in ("gate", "collect"):
        raise ValueError("unsupported mode")
    candidates, rights = read_csv(input_path), read_csv(registry_path)
    registry_hash = digest(Path(registry_path).read_bytes())
    research = ResearchAuthorization(research_authorization) if research_authorization else None
    if research:
        research.validate_input(candidates)
    registry = RightsRegistry(rights, research)
    output = new_output(output_dir)
    (output / "raw").mkdir()
    collector = collector or Collector(registry)
    collector.registry = registry
    rows, seen_ids, seen_docs, seen_urls = [], set(), set(), set()
    with (output / "raw" / "blocks.jsonl").open("x", encoding="utf-8") as block_stream, \
         (output / "request_trace.jsonl").open("x", encoding="utf-8") as trace_stream, \
         (output / "manifest.csv").open("x", encoding="utf-8", newline="") as manifest_stream:
        manifest_writer = csv.DictWriter(manifest_stream, fieldnames=MANIFEST_FIELDS)
        manifest_writer.writeheader()
        manifest_stream.flush()
        for index, candidate in enumerate(candidates, 1):
            row = base_row(candidate, index, registry_hash)
            url = candidate.get("source_url", "")
            allowed, reason, policy = registry.check(candidate, url)
            row.update(rights_status=policy.get("rights_status", "unresolved") if policy else "unresolved", rights_reason=reason,
                       execution_basis=research.execution_basis if research else ("verified_source_rights" if allowed else "not_authorized"),
                       research_authorization_sha256=research.sha256 if research else "")
            if policy:
                row["rights_basis_urls"] = json.dumps([safe_url(policy.get("terms_url", ""))])
                row["rights_permissions"] = json.dumps([{k: policy.get(k, "unresolved") for k in PERMISSIONS}])
            try:
                if not candidate.get("candidate_id") or not candidate.get("source_id"):
                    raise StopFetch("invalid_candidate_missing_id")
                if row["candidate_id"] in seen_ids or row["doc_id"] in seen_docs or url in seen_urls:
                    raise StopFetch("duplicate_candidate_preserved")
                seen_ids.add(row["candidate_id"])
                seen_docs.add(row["doc_id"])
                seen_urls.add(url)
                if not allowed:
                    raise StopFetch("deferred_rights_" + reason)
                if mode == "gate":
                    raise StopFetch("ready_not_fetched_gate_only")
                raw, final_url, policy = collector.fetch(candidate, row)
                sha = digest(raw)
                filename = digest(row["doc_id"].encode())[:20] + "-" + sha + ".html"
                path = output / "raw" / filename
                with path.open("xb") as raw_stream:
                    raw_stream.write(raw)
                row.update(fetch_status="downloaded_pending_audit", final_url=safe_url(final_url),
                           final_url_sha256=digest(final_url.encode()),
                           revision_id=sha, sha256=sha, storage_uri="raw/" + filename,
                           byte_size=len(raw), extraction_attempted="true", human_audit_status="pending",
                           missing_reason="human_completeness_scope_origin_claim_review_pending")
                # Exact query-bearing final URLs remain reproducible without
                # exposing any query values in public logs or manifest fields.
                provenance_name = filename + ".provenance.json"
                provenance = {"source_url": url, "final_url": final_url,
                              "doc_id": row["doc_id"], "revision_id": sha,
                              "observed_at": row["observed_at"], "rights_status": row["rights_status"],
                              "execution_basis": row["execution_basis"],
                              "research_authorization_sha256": row["research_authorization_sha256"]}
                with (output / "raw" / provenance_name).open("x", encoding="utf-8") as stream:
                    json.dump(provenance, stream, ensure_ascii=False, indent=2)
                row["provenance_uri"] = "raw/" + provenance_name
                try:
                    for block in extract_html(raw, row, policy):
                        block_stream.write(json.dumps(block, ensure_ascii=False) + "\n")
                except Exception as error:
                    row["extraction_status"] = "extraction_failed_" + type(error).__name__
            except StopFetch as error:
                row.update(fetch_status=error.reason, missing_reason=error.reason,
                           deferred_until=error.until)
                if error.status:
                    row["http_status"] = error.status
            except Exception as error:
                # Preserve the failed candidate and all prior rows without logging
                # exception messages, which can contain credentialed URLs.
                row.update(fetch_status="candidate_error_" + type(error).__name__,
                           missing_reason="candidate_processing_failed")
            trace = row.pop("_trace", [])
            trace_stream.write(json.dumps({"candidate_id": row["candidate_id"], "hops": trace}) + "\n")
            manifest_writer.writerow(row)
            block_stream.flush()
            trace_stream.flush()
            manifest_stream.flush()
            rows.append(row)
    metadata = {"schema_version": SCHEMA_VERSION, "mode": mode,
                "input_sha256": digest(Path(input_path).read_bytes()),
                "rights_registry_sha256": registry_hash, "script_sha256": digest(Path(__file__).read_bytes()),
                "candidate_rows": len(rows), "completed_at": utcnow().isoformat(),
                "execution_basis": research.execution_basis if research else "strict_source_rights",
                "research_authorization_sha256": research.sha256 if research else "",
                "ai_calls": 0, "network_body_requests": sum(r["body_request_count"] for r in rows)}
    with (output / "run.json").open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream, ensure_ascii=False, indent=2)
    return rows


def validate_block(block, raw):
    """Returns error codes, never source text. Identity offsets mean block text only."""
    errors = []
    original, normalized = block.get("raw_text", ""), block.get("normalized_text", "")
    mapping = block.get("offset_mapping", {})
    if mapping.get("unit") != "unicode_codepoint":
        errors.append("offset_unit_invalid")
    if mapping.get("status") == "identity" and original != normalized:
        errors.append("identity_round_trip_failed")
    for span in block.get("spans", []):
        start, end = span.get("start"), span.get("end")
        if (not isinstance(start, int) or not isinstance(end, int)
                or not 0 <= start <= end <= len(original)
                or original[start:end] != span.get("text")):
            errors.append("span_round_trip_failed")
    xpath = block.get("source_xpath")
    if xpath:
        try:
            from lxml import html
            selected = html.fromstring(raw).xpath(xpath)
            if len(selected) != 1 or "".join(selected[0].itertext()) != original:
                errors.append("source_xpath_round_trip_failed")
        except Exception:
            errors.append("source_xpath_invalid")
    elif block.get("location_status") != "text_only_unlocated":
        errors.append("missing_source_location")
    if block.get("evidence_eligible") and (not xpath or mapping.get("status") == "not_available"):
        errors.append("unlocated_or_unmapped_evidence_forbidden")
    return errors


def ratio(numerator, denominator):
    return {"numerator": numerator, "denominator": denominator,
            "rate": numerator / denominator if denominator else None,
            "status": "measured" if denominator else "NA_zero_denominator"}


def audit(input_path, manifest_path, registry_path, output_dir, research_authorization=None):
    candidates, manifest = read_csv(input_path), read_csv(manifest_path)
    research = ResearchAuthorization(research_authorization) if research_authorization else None
    if research:
        research.validate_input(candidates)
    output = new_output(output_dir)
    errors = []
    if len(candidates) != len(manifest):
        errors.append("candidate_manifest_row_count_mismatch")
    if [r.get("candidate_id") for r in candidates] != [r.get("candidate_id") for r in manifest]:
        errors.append("candidate_manifest_order_or_id_mismatch")
    registry_hash = digest(Path(registry_path).read_bytes())
    raw_by_revision, block_counts = {}, Counter()
    manifest_dir = Path(manifest_path).resolve().parent
    registry = RightsRegistry(read_csv(registry_path), research)
    original_by_id = {r.get("candidate_id"): r for r in candidates}
    def audit_candidate(row):
        return {**row, "source_url": original_by_id.get(row.get("candidate_id"), {}).get("source_url", "")}
    run_path = manifest_dir / "run.json"
    if run_path.is_file():
        run_metadata = json.loads(run_path.read_text(encoding="utf-8"))
        if run_metadata.get("research_authorization_sha256", "") != (research.sha256 if research else ""):
            errors.append("run_research_authorization_hash_mismatch")
    trace_path = manifest_dir / "request_trace.jsonl"
    traces = []
    if trace_path.is_file():
        with trace_path.open(encoding="utf-8") as stream:
            traces = [json.loads(line) for line in stream]
    if len(traces) != len(manifest):
        errors.append("request_trace_row_count_mismatch")
    for row in manifest:
        identifier = row.get("candidate_id", "unknown")
        if row.get("rights_registry_sha256") != registry_hash:
            errors.append(identifier + ":rights_registry_changed")
        if row.get("research_authorization_sha256", "") != (research.sha256 if research else ""):
            errors.append(identifier + ":research_authorization_hash_mismatch")
        if research and row.get("execution_basis") != research.execution_basis:
            errors.append(identifier + ":research_execution_basis_mismatch")
        if row.get("storage_uri"):
            if row.get("body_attempted") != "true" or row.get("extraction_attempted") != "true":
                errors.append(identifier + ":stored_body_without_attempt_flags")
            path = (manifest_dir / row["storage_uri"]).resolve()
            if not path.is_relative_to(manifest_dir / "raw"):
                errors.append(identifier + ":raw_path_outside_run")
                continue
            if not path.is_file():
                errors.append(identifier + ":raw_file_missing")
                continue
            raw = path.read_bytes()
            if digest(raw) != row["sha256"] or row["revision_id"] != row["sha256"]:
                errors.append(identifier + ":raw_hash_or_revision_mismatch")
            raw_by_revision[(row["doc_id"], row["revision_id"])] = raw
            provenance_path = (manifest_dir / row.get("provenance_uri", "")).resolve()
            if not provenance_path.is_relative_to(manifest_dir / "raw") or not provenance_path.is_file():
                errors.append(identifier + ":private_provenance_missing_or_outside_run")
            else:
                provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
                if (digest(provenance.get("final_url", "").encode()) != row.get("final_url_sha256")
                        or digest(provenance.get("source_url", "").encode()) != row.get("source_url_sha256")
                        or provenance.get("revision_id") != row["revision_id"]):
                    errors.append(identifier + ":private_provenance_mismatch")
                allowed, _, final_rights = registry.check(audit_candidate(row), provenance.get("final_url", ""))
                if not allowed:
                    errors.append(identifier + ":stored_final_url_without_verified_rights")
                if final_rights and row.get("rights_status") != final_rights.get("rights_status"):
                    errors.append(identifier + ":source_rights_status_mismatch")
                if provenance.get("research_authorization_sha256", "") != (research.sha256 if research else ""):
                    errors.append(identifier + ":private_research_authorization_hash_mismatch")
        elif row.get("extraction_attempted") == "true":
            errors.append(identifier + ":extraction_without_stored_source")
        if row.get("body_complete") == "pass" and row.get("human_audit_status") != "complete":
            errors.append(identifier + ":completeness_without_human_audit")
    for candidate, row in zip(candidates, manifest):
        identifier = row.get("candidate_id", "unknown")
        if digest(candidate.get("source_url", "").encode()) != row.get("source_url_sha256"):
            errors.append(identifier + ":candidate_source_url_changed")
        if candidate.get("source_id") != row.get("source_id"):
            errors.append(identifier + ":candidate_source_id_changed")
        if row.get("body_attempted") == "true":
            allowed, _, _ = registry.check(candidate, candidate.get("source_url", ""))
            if not allowed:
                errors.append(identifier + ":initial_body_request_without_verified_rights")
    for row, trace in zip(manifest, traces):
        identifier = row.get("candidate_id", "unknown")
        if trace.get("candidate_id") != identifier:
            errors.append(identifier + ":request_trace_id_mismatch")
        requested = [hop for hop in trace.get("hops", []) if hop.get("body_requested")]
        if len(requested) != int(row.get("body_request_count") or 0):
            errors.append(identifier + ":request_trace_attempt_count_mismatch")
        if bool(requested) != (row.get("body_attempted") == "true"):
            errors.append(identifier + ":request_trace_attempt_flag_mismatch")
        for hop in requested:
            item = audit_candidate(row)
            url = research.exact_trace_url(item, hop) if research else hop.get("url", "")
            allowed, _, _ = registry.check(item, url)
            if not allowed:
                errors.append(identifier + ":redirect_hop_requested_without_verified_rights")
    blocks_path = manifest_dir / "raw" / "blocks.jsonl"
    if blocks_path.is_file():
        with blocks_path.open(encoding="utf-8") as stream:
            for line in stream:
                block = json.loads(line)
                key = (block.get("doc_id"), block.get("revision_id"))
                block_counts[key] += 1
                if key not in raw_by_revision:
                    errors.append(block.get("block_id", "unknown") + ":orphan_block")
                else:
                    errors.extend(block["block_id"] + ":" + e for e in validate_block(block, raw_by_revision[key]))
    for row in manifest:
        if row.get("block_count") and int(row["block_count"]) != block_counts[(row["doc_id"], row["revision_id"])]:
            errors.append(row["candidate_id"] + ":block_count_mismatch")
    docs = lambda predicate: {r["doc_id"] for r in manifest if predicate(r)}
    attempted = docs(lambda r: r.get("body_attempted") == "true")
    stored = docs(lambda r: bool(r.get("storage_uri")))
    extracted = docs(lambda r: r.get("extraction_status") == "extracted_pending_audit")
    complete = docs(lambda r: r.get("body_complete") == "pass" and r.get("human_audit_status") == "complete")
    scope = docs(lambda r: r["doc_id"] in complete and r.get("scope_fit") == "pass")
    independent = docs(lambda r: r["doc_id"] in scope and r.get("production_origin") in ("reporter_original", "wire_original"))
    matched = docs(lambda r: r["doc_id"] in independent and r.get("claim_matching") == "pass")
    report = {"schema_version": SCHEMA_VERSION, "integrity_pass": not errors, "errors": errors,
              "candidate_rows": len(candidates),
              "candidate_unique_urls": len({r.get("source_url") for r in candidates if r.get("source_url")}),
              "candidate_unique_doc_ids": len(docs(lambda r: True)),
              "candidate_family_count": len({r.get("event_family_id") for r in candidates if r.get("event_family_id")}),
              "stages": {"body_attempt": ratio(len(attempted), len(docs(lambda r: True))),
                         "stored_response": ratio(len(stored), len(attempted)),
                         "automatic_extraction": ratio(len(extracted), len(docs(lambda r: r.get("extraction_attempted") == "true"))),
                         "complete_body": ratio(len(complete), len(attempted)),
                         "scope_fit": ratio(len(scope), len(complete)),
                         "independent_origin": ratio(len(independent), len(scope)),
                         "claim_matching": ratio(len(matched), len(independent))},
              "human_audit_complete_docs": len(docs(lambda r: r.get("human_audit_status") == "complete")),
              "comparability_pairs": None, "comparability_status": "not_assessed_requires_aligned_claim_speaker_position",
              "fetch_statuses": dict(Counter(r.get("fetch_status") for r in manifest)),
              "source_rights_statuses": dict(Counter(r.get("rights_status") for r in manifest)),
              "execution_bases": dict(Counter(r.get("execution_basis", "legacy_strict") for r in manifest)),
              "research_authorization_sha256": research.sha256 if research else "",
              "complete_body_note": "HTTP 200, stored HTML, text length and XPath checks do not establish completeness",
              "ontology_status": "deferred_out_of_scope"}
    with (output / "audit.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("gate", "collect", "audit"))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--rights-registry", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--manifest", type=Path, help="required by audit")
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--research-authorization", type=Path,
                        help="explicit fixed noncommercial pilot authorization JSON; default remains strict")
    args = parser.parse_args()
    try:
        if args.command == "audit":
            if args.manifest is None:
                parser.error("audit requires --manifest")
            report = audit(args.input, args.manifest, args.rights_registry, args.output_dir, args.research_authorization)
            print(json.dumps({k: report[k] for k in ("integrity_pass", "candidate_rows", "stages")}, ensure_ascii=False))
            return 0 if report["integrity_pass"] else 1
        collector = Collector(RightsRegistry(read_csv(args.rights_registry)), delay=args.delay)
        rows = run(args.input, args.rights_registry, args.output_dir, args.command, collector, args.research_authorization)
        print(json.dumps({"candidate_rows": len(rows), "statuses": dict(Counter(r["fetch_status"] for r in rows))}))
        return 0
    except (FileExistsError, ValueError) as error:
        # Deliberately omit exception messages: paths/URLs may contain private data.
        parser.exit(2, "Run refused: " + type(error).__name__ + "; check input and use a new output directory.\n")


if __name__ == "__main__":
    raise SystemExit(main())
