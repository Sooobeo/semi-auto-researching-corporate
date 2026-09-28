"""Network-free boundary tests; all article text and rights are synthetic fixtures."""

import csv
import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "p01_domestic_pilot.py"
spec = importlib.util.spec_from_file_location("p01_domestic_pilot", SCRIPT)
pilot = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pilot
spec.loader.exec_module(pilot)


def candidate(url="https://a.example/article"):
    return {"candidate_id": "C1", "source_id": "S1", "source_url": url,
            "doc_id": "D1", "event_family_id": "F1", "publisher_published_raw": "2025-02-03"}


def rights(domain="a.example", **updates):
    row = {"source_id": "S1", "domain": domain, "url_path_prefix": "/",
           "terms_url": "https://a.example/terms", "terms_checked_at": "2026-09-21",
           "rights_status": "verified", "available_from": "2024-01-01", "available_to": "2026-09-21",
           "authentication": "none", "body_xpath": "//article", "source_type": "publisher_web",
           "authorization_kind": "public_permission", "authorization_evidence_ref": "https://a.example/permission",
           "authorization_valid_from": "2024-01-01", "authorization_valid_to": "2099-01-01"}
    row.update({key: "allowed" for key in pilot.PERMISSIONS})
    row.update(updates)
    return row


ROBOTS = pilot.Reply(200, {"content-type": "text/plain"}, b"User-agent: *\nAllow: /\n")
HTML = b'<html><head><meta property="article:published_time" content="2025-02-03"></head><body><article><p>Synthetic text 123.</p></article></body></html>'
ARTICLE = pilot.Reply(200, {"content-type": "text/html; charset=utf-8"}, HTML)


class FakeNetwork:
    def __init__(self, replies):
        self.replies, self.calls = replies, []
        self.clock = 100.0

    def __call__(self, url, limit):
        self.calls.append(url)
        if url not in self.replies:
            raise AssertionError("Unexpected network request")
        return self.replies[url]

    def sleep(self, seconds):
        self.clock += seconds


def collector(rows, replies):
    net = FakeNetwork(replies)
    result = pilot.Collector(pilot.RightsRegistry(rows), request=net, sleep=net.sleep,
                             monotonic=lambda: net.clock,
                             now=lambda: datetime(2026, 9, 21, tzinfo=timezone.utc))
    return result, net


def write_csv(path, rows, fields=None):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class FetchBoundaries(unittest.TestCase):
    def attempt(self, engine, item=None):
        item = item or candidate()
        row = pilot.base_row(item, 1, "fixture-hash")
        return item, row

    def test_missing_rights_never_requests_even_robots(self):
        engine, net = collector([], {})
        item, row = self.attempt(engine)
        with self.assertRaises(pilot.StopFetch) as result:
            engine.fetch(item, row)
        self.assertIn("deferred_rights", result.exception.reason)
        self.assertEqual([], net.calls)
        self.assertEqual("false", row["body_attempted"])

    def test_redirect_target_without_rights_not_requested(self):
        engine, net = collector([rights()], {
            "https://a.example/robots.txt": ROBOTS,
            "https://a.example/article": pilot.Reply(302, {"location": "https://b.example/private"}),
        })
        item, row = self.attempt(engine)
        with self.assertRaises(pilot.StopFetch) as result:
            engine.fetch(item, row)
        self.assertIn("deferred_rights", result.exception.reason)
        self.assertEqual(["https://a.example/robots.txt", "https://a.example/article"], net.calls)
        self.assertEqual(1, row["body_request_count"])
        self.assertEqual("missing_or_ambiguous_domain_path_rights", row["_trace"][-1]["rights_decision"])

    def test_redirect_target_robots_denied_before_target_body_request(self):
        engine, net = collector([rights(), rights("b.example")], {
            "https://a.example/robots.txt": ROBOTS,
            "https://a.example/article": pilot.Reply(302, {"location": "https://b.example/private"}),
            "https://b.example/robots.txt": pilot.Reply(200, {}, b"User-agent: *\nDisallow: /\n"),
        })
        item, row = self.attempt(engine)
        with self.assertRaises(pilot.StopFetch) as result:
            engine.fetch(item, row)
        self.assertEqual("robots_denied", result.exception.reason)
        self.assertNotIn("https://b.example/private", net.calls)

    def test_same_host_redirect_outside_path_scope_is_denied(self):
        engine, net = collector([rights(url_path_prefix="/article")], {
            "https://a.example/robots.txt": ROBOTS,
            "https://a.example/article": pilot.Reply(302, {"location": "/private"}),
        })
        item, row = self.attempt(engine)
        with self.assertRaises(pilot.StopFetch):
            engine.fetch(item, row)
        self.assertEqual(2, len(net.calls))

    def test_robots_redirect_never_followed(self):
        engine, net = collector([rights()], {
            "https://a.example/robots.txt": pilot.Reply(302, {"location": "https://b.example/robots.txt"}),
        })
        item, row = self.attempt(engine)
        with self.assertRaises(pilot.StopFetch) as result:
            engine.fetch(item, row)
        self.assertEqual("robots_unverified_http_302", result.exception.reason)
        self.assertEqual(["https://a.example/robots.txt"], net.calls)
        self.assertEqual("false", row["body_attempted"])

    def test_429_retry_after_defers_host_without_wait_or_retry(self):
        engine, net = collector([rights()], {
            "https://a.example/robots.txt": ROBOTS,
            "https://a.example/article": pilot.Reply(429, {"retry-after": "3600"}),
        })
        item, row = self.attempt(engine)
        with self.assertRaises(pilot.StopFetch) as result:
            engine.fetch(item, row)
        self.assertEqual("2026-09-21T01:00:00+00:00", result.exception.until)
        self.assertEqual(2, len(net.calls))
        second = candidate("https://a.example/second")
        other = pilot.base_row(second, 2, "fixture-hash")
        with self.assertRaises(pilot.StopFetch) as result:
            engine.fetch(second, other)
        self.assertEqual("deferred_host_retry_after", result.exception.reason)
        self.assertEqual("false", other["body_attempted"])
        self.assertEqual(2, len(net.calls))

    def test_robots_429_has_no_body_attempt(self):
        engine, net = collector([rights()], {
            "https://a.example/robots.txt": pilot.Reply(429, {"retry-after": "Mon, 21 Sep 2026 02:00:00 GMT"}),
        })
        item, row = self.attempt(engine)
        with self.assertRaises(pilot.StopFetch) as result:
            engine.fetch(item, row)
        self.assertEqual("2026-09-21T02:00:00+00:00", result.exception.until)
        self.assertEqual("false", row["body_attempted"])

    def test_403_never_retried(self):
        engine, net = collector([rights()], {"https://a.example/robots.txt": ROBOTS,
                                             "https://a.example/article": pilot.Reply(403)})
        item, row = self.attempt(engine)
        with self.assertRaises(pilot.StopFetch) as result:
            engine.fetch(item, row)
        self.assertEqual("http_403", result.exception.reason)
        self.assertEqual(2, len(net.calls))

    def test_long_crawl_delay_deferred_not_counted_as_body_attempt(self):
        engine, net = collector([rights()], {"https://a.example/robots.txt": pilot.Reply(
            200, {}, b"User-agent: *\nAllow: /\nCrawl-delay: 600\n")})
        item, row = self.attempt(engine)
        with self.assertRaises(pilot.StopFetch) as result:
            engine.fetch(item, row)
        self.assertEqual("deferred_host_interval", result.exception.reason)
        self.assertEqual("false", row["body_attempted"])

    def test_paywall_not_extracted(self):
        engine, net = collector([rights()], {"https://a.example/robots.txt": ROBOTS,
            "https://a.example/article": pilot.Reply(200, {"content-type": "text/html"}, b'{"isAccessibleForFree":false}')})
        item, row = self.attempt(engine)
        with self.assertRaises(pilot.StopFetch) as result:
            engine.fetch(item, row)
        self.assertEqual("paywall_declared", result.exception.reason)

    def test_period_reference_never_substitutes_publication_date(self):
        item = candidate()
        item.pop("publisher_published_raw")
        item.update(reference_period="2025Q1", provider_published_raw="2025-02-03")
        result = pilot.RightsRegistry([rights()]).check(item, item["source_url"])
        self.assertFalse(result[0])
        self.assertEqual("publisher_date_unknown_for_coverage", result[1])

    def test_licensed_contract_must_be_verified_and_current(self):
        item = candidate()
        policy = rights(source_type="licensed_api_candidate", authorization_kind="contract",
                        contract_confirmation_status="not_inspected", contract_evidence_ref="not_provided")
        result = pilot.RightsRegistry([policy]).check(item, item["source_url"])
        self.assertEqual("contract_not_verified", result[1])
        policy.update(contract_confirmation_status="verified", contract_evidence_ref="https://a.example/signed-contract",
                      authorization_valid_to="2020-01-01")
        result = pilot.RightsRegistry([policy]).check(item, item["source_url"])
        self.assertEqual("authorization_not_currently_valid", result[1])

    def test_derived_storage_needs_permission_even_if_html_storage_allowed(self):
        item = candidate()
        result = pilot.RightsRegistry([rights(derived_chunk_storage="unresolved")]).check(item, item["source_url"])
        self.assertEqual("permission_not_allowed_derived_chunk_storage", result[1])

    def test_query_values_and_userinfo_never_persisted(self):
        saved = pilot.safe_url("https://user:password@a.example/x?random_name=SECRET#SECRET")
        self.assertNotIn("SECRET", saved)
        self.assertNotIn("password", saved)
        self.assertFalse(pilot.valid_url("https://a.example/x?token=secret"))
        self.assertFalse(pilot.valid_url("https://a.example/allowed/%2e%2e/private"))


class RunAndAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.input, self.registry = self.base / "input.csv", self.base / "rights.csv"
        write_csv(self.input, [candidate()])
        write_csv(self.registry, [rights()])

    def tearDown(self):
        self.temp.cleanup()

    def test_overwrite_refused_before_network(self):
        output = self.base / "already-exists"
        output.mkdir()
        marker = output / "existing.txt"
        marker.write_text("keep", encoding="utf-8")
        engine, net = collector([rights()], {})
        with self.assertRaises(FileExistsError):
            pilot.run(self.input, self.registry, output, "collect", engine)
        self.assertEqual("keep", marker.read_text(encoding="utf-8"))
        self.assertEqual([], net.calls)

    def test_36_unresolved_candidates_preserved_no_body_denominator(self):
        items = [dict(candidate(f"https://a.example/article/{i}"), candidate_id=f"C{i}", doc_id=f"D{i}") for i in range(36)]
        write_csv(self.input, items)
        write_csv(self.registry, [rights(rights_status="unresolved")])
        engine, net = collector([], {})
        rows = pilot.run(self.input, self.registry, self.base / "gate", "gate", engine)
        self.assertEqual(36, len(rows))
        self.assertTrue(all(row["fetch_status"].startswith("deferred_rights") for row in rows))
        self.assertEqual([], net.calls)
        report = pilot.audit(self.input, self.base / "gate/manifest.csv", self.registry, self.base / "audit")
        self.assertTrue(report["integrity_pass"], report["errors"])
        self.assertEqual(0, report["stages"]["complete_body"]["denominator"])
        self.assertIsNone(report["stages"]["complete_body"]["rate"])

    def test_empty_input_reports_na_and_writes_headers(self):
        write_csv(self.input, [], list(candidate()))
        pilot.run(self.input, self.registry, self.base / "gate")
        report = pilot.audit(self.input, self.base / "gate/manifest.csv", self.registry, self.base / "audit")
        self.assertTrue(report["integrity_pass"])
        self.assertEqual(0, report["candidate_rows"])
        self.assertEqual("NA_zero_denominator", report["stages"]["body_attempt"]["status"])

    def test_extracted_article_is_not_complete_or_human_audited(self):
        engine, net = collector([rights()], {"https://a.example/robots.txt": ROBOTS,
                                             "https://a.example/article": ARTICLE})
        rows = pilot.run(self.input, self.registry, self.base / "collect", "collect", engine)
        self.assertEqual("extracted_pending_audit", rows[0]["extraction_status"])
        self.assertEqual("unknown", rows[0]["body_complete"])
        report = pilot.audit(self.input, self.base / "collect/manifest.csv", self.registry, self.base / "audit")
        self.assertTrue(report["integrity_pass"], report["errors"])
        self.assertEqual(1, report["stages"]["automatic_extraction"]["numerator"])
        self.assertEqual(0, report["stages"]["complete_body"]["numerator"])
        self.assertEqual(0, report["human_audit_complete_docs"])

    def test_query_url_reproducible_only_in_private_provenance(self):
        original = candidate("https://a.example/article?no=123")
        write_csv(self.input, [original])
        final = "https://a.example/final?newsId=456"
        engine, net = collector([rights()], {"https://a.example/robots.txt": ROBOTS,
            original["source_url"]: pilot.Reply(302, {"location": final}), final: ARTICLE})
        rows = pilot.run(self.input, self.registry, self.base / "collect", "collect", engine)
        row = rows[0]
        self.assertNotIn("456", row["final_url"])
        self.assertEqual(pilot.digest(final.encode()), row["final_url_sha256"])
        private = json.loads((self.base / "collect" / row["provenance_uri"]).read_text(encoding="utf-8"))
        self.assertEqual(final, private["final_url"])
        self.assertEqual(original["source_url"], private["source_url"])
        report = pilot.audit(self.input, self.base / "collect/manifest.csv", self.registry, self.base / "audit")
        self.assertTrue(report["integrity_pass"], report["errors"])

    def test_audit_rejects_forged_final_rights_and_attempt_flags(self):
        engine, net = collector([rights()], {"https://a.example/robots.txt": ROBOTS,
                                             "https://a.example/article": ARTICLE})
        rows = pilot.run(self.input, self.registry, self.base / "collect", "collect", engine)
        row = rows[0]
        private_path = self.base / "collect" / row["provenance_uri"]
        private = json.loads(private_path.read_text(encoding="utf-8"))
        private["final_url"] = "https://unlicensed.example/article"
        private_path.write_text(json.dumps(private), encoding="utf-8")
        row.update(final_url=private["final_url"], final_url_sha256=pilot.digest(private["final_url"].encode()), body_attempted="false")
        write_csv(self.base / "collect/manifest.csv", rows, pilot.MANIFEST_FIELDS)
        report = pilot.audit(self.input, self.base / "collect/manifest.csv", self.registry, self.base / "audit")
        self.assertFalse(report["integrity_pass"])
        self.assertIn("C1:stored_body_without_attempt_flags", report["errors"])
        self.assertIn("C1:stored_final_url_without_verified_rights", report["errors"])
        self.assertIn("C1:request_trace_attempt_flag_mismatch", report["errors"])

    def test_audit_rechecks_each_requested_redirect_hop(self):
        engine, net = collector([rights()], {"https://a.example/robots.txt": ROBOTS,
                                             "https://a.example/article": ARTICLE})
        rows = pilot.run(self.input, self.registry, self.base / "collect", "collect", engine)
        trace_path = self.base / "collect/request_trace.jsonl"
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        trace["hops"][0]["url"] = "https://unlicensed.example/redirect"
        trace_path.write_text(json.dumps(trace) + "\n", encoding="utf-8")
        report = pilot.audit(self.input, self.base / "collect/manifest.csv", self.registry, self.base / "audit")
        self.assertFalse(report["integrity_pass"])
        self.assertIn("C1:redirect_hop_requested_without_verified_rights", report["errors"])

    def test_exact_duplicate_candidate_preserved(self):
        write_csv(self.input, [candidate(), dict(candidate(), candidate_id="C2")])
        rows = pilot.run(self.input, self.registry, self.base / "gate")
        self.assertEqual(2, len(rows))
        self.assertEqual("duplicate_candidate_preserved", rows[1]["fetch_status"])

    def test_location_and_unicode_offsets_round_trip(self):
        raw = "<html><article><p>한😀글 123</p></article></html>".encode()
        block = {"raw_text": "한😀글 123", "normalized_text": "한😀글 123", "source_xpath": "/html/body/article/p",
                 "location_status": "source_xpath_pending_audit", "evidence_eligible": False,
                 "offset_mapping": {"status": "identity", "unit": "unicode_codepoint"},
                 "spans": [{"start": 1, "end": 2, "text": "😀"}]}
        # Explicit UTF-8 declaration ensures parser decoding is source-grounded.
        raw = b'<html><head><meta charset="utf-8"></head><body><article><p>' + "한😀글 123".encode() + b'</p></article></body></html>'
        self.assertEqual([], pilot.validate_block(block, raw))
        block["spans"][0]["end"] = 3
        self.assertIn("span_round_trip_failed", pilot.validate_block(block, raw))
        block["source_xpath"] = "/html/body/missing"
        self.assertIn("source_xpath_round_trip_failed", pilot.validate_block(block, raw))
        block["normalized_text"] = "changed"
        self.assertIn("identity_round_trip_failed", pilot.validate_block(block, raw))

    def test_unlocated_fallback_cannot_be_evidence(self):
        block = {"raw_text": "text", "normalized_text": "text", "source_xpath": None,
                 "location_status": "text_only_unlocated", "evidence_eligible": True,
                 "offset_mapping": {"status": "not_available", "unit": "unicode_codepoint"}}
        self.assertIn("unlocated_or_unmapped_evidence_forbidden", pilot.validate_block(block, HTML))


class ExplicitResearchPilot(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.input, self.registry, self.authorization = (self.base / name for name in ("input.csv", "rights.csv", "research.json"))
        self.item = dict(candidate("https://a.example/article?no=123"), source_id="ETNEWS", publisher_published_raw="")
        self.policy = rights(source_id="ETNEWS", source_type="direct_publisher_html", rights_status="unresolved",
                             available_from="unresolved", available_to="unresolved", authentication="unresolved")
        self.policy.update({key: "unresolved" for key in pilot.PERMISSIONS})
        self.approval = {"schema_version": "p01-research-authorization-0.1", "authorization_id": "SYNTHETIC-TEST",
                         "authorization_date": "2026-09-22", "execution_basis": "user_noncommercial_research",
                         "purpose": "noncommercial_research", "max_candidates": 39, "user_instruction": "Synthetic explicit approval",
                         "sources": [{"source_id": "ETNEWS", "domain": "a.example", "source_type": "direct_publisher_html"}],
                         "candidates": [{k: self.item[k] for k in ("candidate_id", "source_id", "source_url")}]}
        self.approval["candidates"][0]["allowed_redirect_urls"] = []
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        write_csv(self.input, [self.item])
        write_csv(self.registry, [self.policy])
        self.authorization.write_text(json.dumps(self.approval), encoding="utf-8")

    def engine(self, final=ARTICLE):
        return collector([self.policy], {"https://a.example/robots.txt": ROBOTS, self.item["source_url"]: final})

    def test_explicit_research_keeps_rights_unresolved_and_date_unknown(self):
        engine, net = self.engine()
        rows = pilot.run(self.input, self.registry, self.base / "collect", "collect", engine, self.authorization)
        self.assertEqual("extracted_pending_audit", rows[0]["extraction_status"])
        self.assertEqual("unresolved", rows[0]["rights_status"])
        self.assertEqual("user_noncommercial_research", rows[0]["execution_basis"])
        self.assertEqual("", rows[0]["publisher_published_raw"])
        report = pilot.audit(self.input, self.base / "collect/manifest.csv", self.registry, self.base / "audit", self.authorization)
        self.assertTrue(report["integrity_pass"], report["errors"])
        strict = pilot.audit(self.input, self.base / "collect/manifest.csv", self.registry, self.base / "strict-audit")
        self.assertFalse(strict["integrity_pass"])
        self.assertIn("run_research_authorization_hash_mismatch", strict["errors"])

    def test_no_explicit_research_remains_strict(self):
        engine, net = self.engine()
        rows = pilot.run(self.input, self.registry, self.base / "collect", "collect", engine)
        self.assertEqual("false", rows[0]["body_attempted"])
        self.assertEqual([], net.calls)

    def test_every_relevant_explicit_denial_precedes_research_approval(self):
        for key in pilot.LOCAL_PERMISSIONS:
            with self.subTest(permission=key):
                self.policy[key] = "denied"
                self.save()
                engine, net = self.engine()
                rows = pilot.run(self.input, self.registry, self.base / key, "collect", engine, self.authorization)
                self.assertEqual([], net.calls)
                self.assertIn("explicitly_denied_" + key, rows[0]["fetch_status"])
                self.policy[key] = "unresolved"

    def test_unused_redistribution_denial_is_recorded_without_redistributing(self):
        self.policy["redistribution"] = "denied"
        self.save()
        engine, net = self.engine()
        rows = pilot.run(self.input, self.registry, self.base / "collect", "collect", engine, self.authorization)
        self.assertEqual("extracted_pending_audit", rows[0]["extraction_status"])
        self.assertEqual("denied", json.loads(rows[0]["rights_permissions"])[0]["redistribution"])

    def test_licensed_or_official_registry_cannot_use_research_route(self):
        for source_type in ("licensed_api_candidate", "official_anchor"):
            self.policy["source_type"] = source_type
            self.save()
            engine, net = self.engine()
            rows = pilot.run(self.input, self.registry, self.base / source_type, "collect", engine, self.authorization)
            self.assertEqual([], net.calls)
            self.assertIn("exact_direct_publisher_registry", rows[0]["fetch_status"])

    def test_fixed_candidate_id_source_url_and_count_are_enforced(self):
        for key in ("candidate_id", "source_id", "source_url"):
            changed = dict(self.item, **{key: "not-approved"})
            write_csv(self.input, [changed])
            with self.assertRaises(ValueError):
                pilot.run(self.input, self.registry, self.base / key, "collect", research_authorization=self.authorization)
        write_csv(self.input, [self.item] * 40)
        with self.assertRaises(ValueError):
            pilot.run(self.input, self.registry, self.base / "too-many", "collect", research_authorization=self.authorization)

    def test_unapproved_redirect_not_requested_even_same_domain(self):
        engine, net = self.engine(pilot.Reply(302, {"location": "/unapproved"}))
        rows = pilot.run(self.input, self.registry, self.base / "collect", "collect", engine, self.authorization)
        self.assertIn("research_url_not_allowlisted", rows[0]["fetch_status"])
        self.assertEqual(["https://a.example/robots.txt", self.item["source_url"]], net.calls)

    def test_approved_redirect_exact_query_url_revalidated_by_audit(self):
        target = "https://a.example/final?articleId=456"
        self.approval["candidates"][0]["allowed_redirect_urls"] = [target]
        self.save()
        engine, net = self.engine(pilot.Reply(302, {"location": target}))
        net.replies[target] = ARTICLE
        rows = pilot.run(self.input, self.registry, self.base / "collect", "collect", engine, self.authorization)
        self.assertEqual(2, rows[0]["body_request_count"])
        report = pilot.audit(self.input, self.base / "collect/manifest.csv", self.registry, self.base / "audit", self.authorization)
        self.assertTrue(report["integrity_pass"], report["errors"])
        self.authorization.write_text(self.authorization.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        changed = pilot.audit(self.input, self.base / "collect/manifest.csv", self.registry, self.base / "changed", self.authorization)
        self.assertFalse(changed["integrity_pass"])
        self.assertIn("run_research_authorization_hash_mismatch", changed["errors"])

    def test_redirect_url_requires_approved_domain_as_well(self):
        self.approval["candidates"][0]["allowed_redirect_urls"] = ["https://unknown.example/article"]
        self.save()
        with self.assertRaises(ValueError):
            pilot.ResearchAuthorization(self.authorization)

    def test_research_does_not_override_robots_or_403(self):
        engine, net = self.engine()
        net.replies["https://a.example/robots.txt"] = pilot.Reply(200, {}, b"User-agent: *\nDisallow: /\n")
        rows = pilot.run(self.input, self.registry, self.base / "robots", "collect", engine, self.authorization)
        self.assertEqual("robots_denied", rows[0]["fetch_status"])
        self.assertEqual("false", rows[0]["body_attempted"])
        engine, net = self.engine(pilot.Reply(403))
        rows = pilot.run(self.input, self.registry, self.base / "403", "collect", engine, self.authorization)
        self.assertEqual("http_403", rows[0]["fetch_status"])
        self.assertEqual(2, len(net.calls))


if __name__ == "__main__":
    unittest.main()
