"""Network-free SEC policy boundaries. Payloads, rights, and workspaces are synthetic.

These tests measure observable requests/storage/reporting; passing them does not
verify an issuer document, fiscal-period comparison, or collection permission.
"""
import argparse
import contextlib
import csv
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import Mock, patch


REPO = Path(__file__).resolve().parents[1]


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


pilot = load_script("p01_us_sec_pilot")
verifier = load_script("p01_us_verify")


def policy(source_id="SEC_SUBMISSIONS_API", **changes):
    row = {"source_id": source_id, "terms_url": pilot.TERMS,
           "checked_at": "2026-10-05T00:00:00Z", "status": "conditional",
           "unresolved_reason": "Synthetic local-factual-method fixture; no AI-source grant.",
           "adoption_decision": "conditional_local_factual_fixture",
           "local_access_status": "fixture_not_networked"}
    for field in verifier.RIGHTS:
        row[field] = "conditional" if field in {
            "automated_access", "storage_policy", "internal_analysis_policy"
        } else "unresolved"
    row.update(changes)
    return row


def write_registry(path, rows):
    fields = list(dict.fromkeys(key for row in rows for key in row)) or list(policy())
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


class NoLiveNetwork(unittest.TestCase):
    def setUp(self):
        # Any overlooked urllib network request fails, without sending traffic.
        self.guard = patch.object(urllib.request.OpenerDirector, "open",
                                  side_effect=AssertionError("Live network forbidden in unit tests"))
        self.guard.start()
        self.addCleanup(self.guard.stop)


class PolicyGateTests(NoLiveNetwork):
    def test_missing_or_unreviewed_rights_are_held(self):
        self.assertIsNotNone(pilot.source_gate({}, "SEC_SUBMISSIONS_API"))
        for field in ("automated_access", "storage_policy", "internal_analysis_policy"):
            for value in (None, "", "unresolved", "prohibited"):
                with self.subTest(field=field, value=value):
                    row = policy(**{field: value})
                    self.assertIsNotNone(pilot.source_gate({row["source_id"]: row}, row["source_id"]))

    def test_unresolved_status_and_missing_evidence_are_held(self):
        for changes in ({"status": "unresolved"}, {"status": "prohibited"},
                        {"terms_url": ""}, {"checked_at": ""}):
            with self.subTest(changes=changes):
                row = policy(**changes)
                self.assertIsNotNone(pilot.source_gate({row["source_id"]: row}, row["source_id"]))

    def test_prior_host_blocks_and_nonadopted_source_are_held(self):
        for changes in ({"adoption_decision": "blocked_host_no_endpoint_attempt"},
                        {"local_access_status": "blocked_unattempted"}):
            row = policy(**changes)
            self.assertIsNotNone(pilot.source_gate({row["source_id"]: row}, row["source_id"]))
        row = policy("NVDA_IR_WEB")
        self.assertIsNotNone(pilot.source_gate({row["source_id"]: row}, row["source_id"]))

    def test_raw_ai_unresolved_does_not_invent_or_deny_factual_method_permission(self):
        row = policy(ai_input_policy="unresolved", ai_training_policy="unresolved")
        self.assertIsNone(pilot.source_gate({row["source_id"]: row}, row["source_id"]))


class ClientSafetyTests(NoLiveNetwork):
    def client(self):
        result = pilot.Client()
        result.opener = Mock()
        return result

    def test_403_and_429_stop_host_without_second_request(self):
        for code in (403, 429):
            with self.subTest(code=code):
                client = self.client()
                url = "https://data.sec.gov/submissions/CIK0000000001.json"
                client.opener.open.side_effect = urllib.error.HTTPError(
                    url, code, "synthetic blocked", {"Retry-After": "600"}, None)
                with patch.object(pilot.time, "sleep"):
                    first = client.request(url)
                    second = client.request("https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json")
                self.assertEqual(first[2], code)
                self.assertIsNone(first[0])
                self.assertIsNone(second[0])
                self.assertEqual(second[1], "host_blocked_after_403_or_429")
                self.assertEqual(client.opener.open.call_count, 1)

    def test_robots_failure_blocks_body_and_is_not_retried(self):
        client = self.client()
        url = "https://data.sec.gov/submissions/CIK0000000001.json"
        client.opener.open.side_effect = urllib.error.HTTPError(
            "https://data.sec.gov/robots.txt", 403, "synthetic blocked", {}, None)
        with patch.object(pilot.time, "sleep"):
            for _ in range(2):
                result = client.fetch(url)
                self.assertIsNone(result[0])
        self.assertEqual(client.opener.open.call_count, 1)
        attempted = client.opener.open.call_args.args[0].full_url
        self.assertEqual(attempted, "https://data.sec.gov/robots.txt")
        self.assertEqual(len(client.policy_trials), 1)
        self.assertEqual(client.policy_trials[0]["decision"], "unresolved_fail_closed")

    def test_nonadopted_host_never_opens_connection(self):
        client = self.client()
        result = client.request("https://external.example/filing")
        self.assertIsNone(result[0])
        self.assertEqual(result[1], "redirect_domain_not_adopted")
        client.opener.open.assert_not_called()

    def test_redirect_does_not_request_target(self):
        client = self.client()
        url = "https://www.sec.gov/Archives/edgar/data/1/fixture.html"
        target = "https://external.example/fixture.html"
        client.opener.open.side_effect = urllib.error.HTTPError(
            url, 302, "synthetic redirect", {"Location": target}, None)
        with patch.object(pilot.time, "sleep"):
            result = client.request(url)
        self.assertIsNone(result[0])
        self.assertEqual(result[2], 302)
        self.assertEqual(client.opener.open.call_count, 1)
        self.assertEqual(client.opener.open.call_args.args[0].full_url, url)
        # The installed handler refuses even an approved-host redirect.
        opener = pilot.Client().opener
        handlers = [h for h in opener.handlers if isinstance(h, urllib.request.HTTPRedirectHandler)]
        self.assertEqual(len(handlers), 1)
        self.assertIsInstance(handlers[0], pilot.NoRedirect)
        self.assertIsNone(handlers[0].redirect_request(
            urllib.request.Request(url), None, 302, "redirect", {}, target))


class MainBoundaryTests(NoLiveNetwork):
    def setUp(self):
        super().setUp()
        self.temp = tempfile.TemporaryDirectory(prefix="sec-pilot-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root / "artifacts/us_equity/p0"
        self.base.mkdir(parents=True)
        self.registry = self.base / "source_registry.csv"
        self.output = self.base / "synthetic-output"
        self.run_id = "synthetic-no-network-001"
        write_registry(self.registry, [policy(source_id) for source_id in (
            "SEC_SUBMISSIONS_API", "SEC_COMPANYFACTS_API", "SEC_EDGAR_ARCHIVES")])

    def execute(self, overrides=(), fetch=None):
        args = ["pilot", "--output", str(self.output), "--run-id", self.run_id,
                "--source-registry", str(self.registry), *overrides]
        with patch.object(pilot, "ROOT", self.root), patch.object(sys, "argv", args), \
                patch.object(pilot.Client, "fetch", fetch or Mock(side_effect=AssertionError("fetch forbidden"))), \
                patch.object(pilot.subprocess, "run", return_value=Mock(stdout="fixture-revision\n")), \
                contextlib.redirect_stdout(io.StringIO()):
            pilot.main()

    def test_held_sources_preserve_candidates_without_requests_or_raw_bytes(self):
        variants = ([],
                    [policy(source_id, automated_access="unresolved") for source_id in (
                        "SEC_SUBMISSIONS_API", "SEC_COMPANYFACTS_API")],
                    [policy(source_id, storage_policy="prohibited") for source_id in (
                        "SEC_SUBMISSIONS_API", "SEC_COMPANYFACTS_API")],
                    [policy(source_id, adoption_decision="blocked_host_no_endpoint_attempt") for source_id in (
                        "SEC_SUBMISSIONS_API", "SEC_COMPANYFACTS_API")])
        for i, rows in enumerate(variants):
            with self.subTest(variant=i):
                self.output = self.base / f"synthetic-output-{i}"
                self.run_id = f"synthetic-no-network-{i}"
                write_registry(self.registry, rows)
                fetch = Mock(side_effect=AssertionError("Policy must gate before fetch"))
                self.execute(fetch=fetch)
                fetch.assert_not_called()
                summary = json.loads((self.output / "summary.json").read_text(encoding="utf-8"))
                self.assertEqual(summary["api_resources_selected"], 4)
                self.assertEqual(summary["api_resources_network_attempted"], 0)
                self.assertEqual(summary["api_resources_valid_json"], 0)
                self.assertEqual(summary["structured_observations"], 0)
                self.assertEqual(summary["filing_downloaded"], 0)
                self.assertEqual(list((self.base / "raw" / self.run_id).iterdir()), [])
                self.assertEqual((self.output / "observations.jsonl").read_text(encoding="utf-8"), "")
                with (self.output / "api_payload_manifest.csv").open(encoding="utf-8", newline="") as stream:
                    manifests = list(csv.DictReader(stream))
                self.assertTrue(all(row["access_status"] and not row["storage_uri"] for row in manifests))

    def test_run_ids_cannot_escape_or_create_paths(self):
        for run_id in ("../outside", "name/child", "name\\child", ".", "", "x" * 101):
            with self.subTest(run_id=run_id):
                with self.assertRaises(SystemExit):
                    self.execute(["--run-id", run_id])
                self.assertFalse(self.output.exists())
                self.assertFalse((self.base / "raw").exists())

    def test_output_paths_must_be_new_and_inside_active_p0(self):
        existing = self.base / "existing"
        existing.mkdir()
        marker = existing / "keep.txt"
        marker.write_text("existing fixture survives", encoding="utf-8")
        for output in (self.root / "outside", self.base / ".." / "escape", existing):
            with self.subTest(output=str(output)):
                with self.assertRaises(SystemExit):
                    self.execute(["--output", str(output)])
        self.assertEqual(marker.read_text(encoding="utf-8"), "existing fixture survives")
        self.assertFalse((self.root / "outside").exists())
        self.assertFalse((self.base.parent / "escape").exists())

    def test_registry_outside_active_p0_is_rejected_before_output_creation(self):
        external = self.root / "external-registry.csv"
        write_registry(external, [policy()])
        with self.assertRaises(SystemExit):
            self.execute(["--source-registry", str(external)])
        self.assertFalse(self.output.exists())
        self.assertFalse((self.base / "raw").exists())

    def test_existing_raw_run_is_preserved(self):
        raw = self.base / "raw" / self.run_id
        raw.mkdir(parents=True)
        marker = raw / "keep.txt"
        marker.write_text("preserve revision", encoding="utf-8")
        with self.assertRaises(SystemExit):
            self.execute()
        self.assertEqual(marker.read_text(encoding="utf-8"), "preserve revision")
        self.assertFalse(self.output.exists())

    def test_empty_run_never_passes_fiscal_or_normalization_content_checks(self):
        write_registry(self.registry, [policy(source_id, adoption_decision="blocked_host_no_endpoint_attempt")
                                      for source_id in ("SEC_SUBMISSIONS_API", "SEC_COMPANYFACTS_API", "SEC_EDGAR_ARCHIVES")])
        self.execute()
        args = argparse.Namespace(manifest=None, manifest_dir=str(self.output), source_registry=str(self.registry))
        with patch.object(verifier, "ROOT", self.root), patch.object(verifier, "ignored", return_value=True):
            report = verifier.verify(args)
        checks = {item["check"]: item for item in report["checks"]}
        for name in ("json_pointer_source_round_trip",
                     "unicode_code_point_offsets_and_normalization_round_trip",
                     "structured_numbers_units_periods_scope_and_nulls",
                     "fiscal_vs_calendar_and_period_length_comparability"):
            with self.subTest(check=name):
                self.assertEqual(checks[name]["tested_records"], 0)
                self.assertEqual(checks[name]["status"], "not_exercised")
        self.assertEqual(report["human_phase_completion"], "not_established")
        self.assertEqual(report["rates"]["api_endpoint_access"]["denominator"], 0)
        self.assertIsNone(report["rates"]["api_endpoint_access"]["rate"])


if __name__ == "__main__":
    unittest.main()
