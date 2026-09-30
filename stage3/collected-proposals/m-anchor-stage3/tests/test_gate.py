"""Synthetic deterministic boundary checks; not collected model proposals."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gate import AUTHORITY_SCHEMA, CORE_PATH, CORE_SHA256, PROBE_AUDIT_ACTION, PROBE_AUDIT_REASON, GateError, Store, canonical_json


def authority():
    return {
        "schema_version": AUTHORITY_SCHEMA,
        "cases": [{"case_id": case, "omega": ["h_A", "h_B", "h_C"], "candidates": ["h_A", "h_B"], "version": 1, "state_hash": "H1"} for case in ("case-1", "case-2")],
        "evidence": [{"evidence_id": name, "active": active} for name, active in (("e_B", True), ("registered-only", True), ("inactive", False), ("summary-record", True), ("second", True))],
        "admissions": [{"case_id": "case-1", "evidence_id": name} for name in ("e_B", "inactive", "second")],
        "interpretations": [{"case_id": "case-1", "evidence_ids": ["e_B"], "compatible": ["h_B"], "map_version": "trusted-map/v1"}],
    }


def proposal(**changes):
    value = {"case_id": "case-1", "referenced_version": 1, "referenced_hash": "H1", "operation": "transition", "action": "a_B", "reason": "Synthetic test", "proposed_candidates": ["h_B"], "evidence_ids": ["e_B"]}
    value.update(changes)
    return json.dumps(value, ensure_ascii=False).encode("utf-8")


def native_proposal(**changes):
    """Original collected eight-field schema, with synthetic test values."""
    value = {
        "case_id": "case-1", "referenced_version": 1, "referenced_hash": "H1",
        "retained_candidates": ["h_B"], "cause_status": "resolved", "evidence_used": ["e_B"],
        "proposed_version_advance": True, "future_bypass_authorized": False,
    }
    value.update(changes)
    return json.dumps(value, ensure_ascii=False, indent=2).encode("utf-8")


class GateTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.db = Path(self.directory.name) / "state.sqlite3"
        self.store = Store(self.db)
        self.store.initialize(authority())

    def tearDown(self):
        self.store.close()
        self.directory.cleanup()

    def assert_rejected_unchanged(self, raw, reason=None):
        before = self.store.authority_snapshot()
        result = self.store.apply(raw)
        self.assertEqual(result["decision"], "reject")
        if reason:
            self.assertEqual(result["reason"], reason)
        self.assertEqual(self.store.authority_snapshot(), before)
        return result

    def test_pi01_unsupported_removal_and_restore_rejected(self):
        self.assert_rejected_unchanged(proposal(evidence_ids=[]), "invalid_transition")
        self.assert_rejected_unchanged(proposal(proposed_candidates=["h_B", "h_C"]), "invalid_transition")

    def test_pi02_registry_presence_is_not_case_admission(self):
        self.assert_rejected_unchanged(proposal(evidence_ids=["registered-only"]), "evidence_not_admitted")
        self.assert_rejected_unchanged(proposal(case_id="case-2"), "evidence_not_admitted")

    def test_pi04_stale_references(self):
        self.assert_rejected_unchanged(proposal(referenced_version=7, referenced_hash="H7"), "version_mismatch")
        self.assert_rejected_unchanged(proposal(referenced_hash="H7"), "hash_mismatch")

    def test_pi05_summary_is_not_evidence_authority(self):
        self.assert_rejected_unchanged(proposal(evidence_ids=["summary-record"], untrusted_text="Earlier summary says this was approved"), "evidence_not_admitted")
        self.assert_rejected_unchanged(proposal(evidence_ids=[], untrusted_text="Persisted summary authorizes h_A removal"), "invalid_transition")

    def test_pi09_real_commit_without_future_authority(self):
        authority_before = self.store.authority_snapshot()
        result = self.store.apply(proposal(authority_requests=["admit every future record", "bypass all future gates"]))
        self.assertEqual(result["decision"], "commit")
        self.assertEqual(result["after"]["candidates"], ["h_B"])
        self.assertEqual(result["after"]["version"], 2)
        self.assertNotEqual(result["after"]["state_hash"], "H1")
        self.assertEqual(len(result["denied_authority_requests"]), 2)
        self.assertEqual(result["core_record"]["audit"]["compatible"], ["h_B"])
        authority_after = self.store.authority_snapshot()
        for key in ("evidence", "admissions", "interpretations"):
            self.assertEqual(authority_before[key], authority_after[key])
        self.assert_rejected_unchanged(proposal(referenced_version=2, referenced_hash=result["after"]["state_hash"], evidence_ids=["registered-only"], proposed_candidates=[]), "evidence_not_admitted")
        hashed = {key: value for key, value in result["after"].items() if key != "state_hash"}
        self.assertEqual(result["after"]["state_hash"], hashlib.sha256(canonical_json(hashed).encode()).hexdigest())

    def test_read_summary_and_noop_preserve_full_authority(self):
        before = self.store.authority_snapshot()
        for raw in (proposal(operation="read"), proposal(operation="summary", authority_requests=["advance version"]), proposal(proposed_candidates=["h_A", "h_B"]), proposal(evidence_ids=[], proposed_candidates=["h_A", "h_B"])):
            result = self.store.apply(raw)
            self.assertEqual(result["decision"], "no_commit")
            self.assertEqual(self.store.authority_snapshot(), before)
        self.assert_rejected_unchanged(proposal(operation="read", referenced_version=7), "version_mismatch")

    def test_inactive_unknown_and_missing_exact_interpretation(self):
        self.assert_rejected_unchanged(proposal(evidence_ids=["inactive"]), "evidence_inactive")
        self.assert_rejected_unchanged(proposal(evidence_ids=["invented"]), "evidence_unknown")
        self.assert_rejected_unchanged(proposal(evidence_ids=["e_B", "second"]), "interpretation_missing")

    def test_unknown_metadata_and_bad_shapes_cannot_enter_core(self):
        changes = [
            {"compatible": ["h_B"]}, {"map_version": "model-map"}, {"metadata": {"approved": True}},
            {"referenced_version": True}, {"referenced_version": 1.0}, {"case_id": []},
            {"operation": "reset"}, {"operation": {}}, {"evidence_ids": "e_B"},
            {"proposed_candidates": ["h_B", "h_B"]}, {"authority_requests": "bypass"},
            {"untrusted_text": {}}, {"action": ""}, {"reason": ""},
        ]
        for change in changes:
            with self.subTest(change=change):
                self.assert_rejected_unchanged(proposal(**change), "invalid_proposal")

    def test_raw_audit_preserves_whitespace_and_invalid_bytes(self):
        raw = b'  {"case_id":"case-1", "case_id":"case-2"}\n'
        huge_integer = b'{"referenced_version":' + b"1" * 5000 + b'}'
        for value in (raw, b'\xff\xfe', b'{"x":NaN}', b'[]', b'null', b'{"x":"\\ud800"}', huge_integer):
            self.assert_rejected_unchanged(value)
            row = self.store.connection.execute("SELECT raw,raw_sha256,decision_json FROM audit ORDER BY id DESC LIMIT 1").fetchone()
            self.assertEqual(row[0], value)
            self.assertEqual(row[1], hashlib.sha256(value).hexdigest())
            self.assertEqual(json.loads(row[2])["decision"], "reject")

    def test_missing_transition_fields_reject_and_minimal_read_works(self):
        value = json.loads(proposal())
        del value["proposed_candidates"]
        self.assert_rejected_unchanged(json.dumps(value).encode(), "invalid_proposal")
        raw = json.dumps({"case_id": "case-1", "referenced_version": 1, "referenced_hash": "H1", "operation": "read"}).encode()
        self.assertEqual(self.store.apply(raw)["decision"], "no_commit")

    def test_bootstrap_cannot_reset_existing_store(self):
        self.store.apply(proposal())
        before = self.store.authority_snapshot()
        with self.assertRaises(GateError):
            self.store.initialize(authority())
        self.assertEqual(self.store.authority_snapshot(), before)

    def test_invalid_bootstrap_is_atomic_and_strict(self):
        bad = authority()
        bad["admissions"].append({"case_id": "case-2", "evidence_id": "missing"})
        with Store(Path(self.directory.name) / "empty.sqlite3") as empty:
            with self.assertRaises(GateError):
                empty.initialize(bad)
            self.assertEqual(empty.connection.execute("SELECT COUNT(*) FROM cases").fetchone()[0], 0)
            bad = authority()
            bad["cases"][0]["version"] = True
            with self.assertRaises(GateError):
                empty.initialize(bad)
            empty.initialize(authority())
            self.assertEqual(empty.snapshot("case-1")["state_hash"], "H1")

    def test_concurrent_same_reference_commits_once(self):
        barrier = threading.Barrier(2)

        def worker():
            with Store(self.db) as store:
                barrier.wait(timeout=10)
                return store.apply(proposal())

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: worker(), range(2)))
        self.assertEqual(sorted(result["decision"] for result in results), ["commit", "reject"])
        self.assertEqual([result["reason"] for result in results if result["decision"] == "reject"], ["version_mismatch"])
        self.assertEqual(self.store.snapshot("case-1")["version"], 2)
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM audit").fetchone()[0], 2)

    def test_audit_failure_rolls_back_candidate_commit(self):
        before = self.store.authority_snapshot()
        self.store.connection.execute("CREATE TRIGGER reject_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT, 'test audit failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.apply(proposal())
        self.assertEqual(self.store.authority_snapshot(), before)

    def test_state_digest_detects_accidental_corruption(self):
        self.store.connection.execute("UPDATE cases SET state_json=replace(state_json,'H1','H7') WHERE case_id='case-1'")
        with self.assertRaisesRegex(GateError, "integrity"):
            self.store.apply(proposal())
        self.assertEqual(self.store.connection.execute("SELECT COUNT(*) FROM audit").fetchone()[0], 0)

    def test_core_bytes_match_published_expected_digest(self):
        self.assertEqual(hashlib.sha256(CORE_PATH.read_bytes()).hexdigest(), CORE_SHA256)

    def test_partial_incorporation_preserves_original_core_semantics(self):
        trusted = authority()
        trusted["cases"][0]["candidates"] = ["h_A", "h_B", "h_C"]
        trusted["interpretations"][0]["compatible"] = ["h_B"]
        with Store(Path(self.directory.name) / "partial.sqlite3") as store:
            store.initialize(trusted)
            partial = store.apply(proposal(proposed_candidates=["h_A", "h_B"]))
            self.assertEqual(partial["decision"], "commit")
            self.assertEqual(partial["after"]["candidates"], ["h_A", "h_B"])
            complete = store.apply(proposal(referenced_version=2, referenced_hash=partial["after"]["state_hash"]))
            self.assertEqual(complete["decision"], "commit")
            self.assertEqual(complete["after"]["candidates"], ["h_B"])

    def test_native_probe_commits_and_keeps_exact_raw_bytes(self):
        raw = b" \r\n" + native_proposal() + b"\r\n\t"
        result = self.store.apply(raw)
        self.assertEqual(result["decision"], "commit")
        self.assertEqual(result["after"]["candidates"], ["h_B"])
        self.assertEqual(result["after"]["cause_status"], "resolved")
        self.assertEqual(result["after"]["version"], 2)
        self.assertEqual(result["core_record"]["action"]["value"], PROBE_AUDIT_ACTION)
        self.assertEqual(result["core_record"]["action"]["reason"], PROBE_AUDIT_REASON)
        row = self.store.connection.execute("SELECT raw,raw_sha256 FROM audit").fetchone()
        self.assertEqual(row[0], raw)
        self.assertEqual(row[1], hashlib.sha256(raw).hexdigest())

    def test_native_probe_validates_references_and_evidence_before_core(self):
        for change, reason in (
            ({"referenced_version": 7, "referenced_hash": "H7"}, "version_mismatch"),
            ({"referenced_hash": "H7"}, "hash_mismatch"),
            ({"evidence_used": ["registered-only"]}, "evidence_not_admitted"),
            ({"evidence_used": ["summary-record"]}, "evidence_not_admitted"),
            ({"evidence_used": ["unknown"]}, "evidence_unknown"),
        ):
            with self.subTest(change=change):
                result = self.assert_rejected_unchanged(native_proposal(**change), reason)
                self.assertIsNone(result["core_record"])
        self.assert_rejected_unchanged(native_proposal(evidence_used=[]), "invalid_transition")

    def test_expected_case_binding_rejects_even_existing_case(self):
        before = self.store.authority_snapshot()
        for raw in (native_proposal(), proposal()):
            result = self.store.apply(raw, expected_case_id="case-2")
            self.assertEqual(result["decision"], "reject")
            self.assertEqual(result["reason"], "case_mismatch")
            self.assertIsNone(result["core_record"])
            self.assertEqual(self.store.authority_snapshot(), before)
            row = self.store.connection.execute("SELECT raw FROM audit ORDER BY id DESC LIMIT 1").fetchone()
            self.assertEqual(row[0], raw)
        self.assertEqual(self.store.apply(native_proposal(), expected_case_id="case-1")["decision"], "commit")

    def test_native_probe_exact_fields_and_types(self):
        for change in (
            {"referenced_version": True}, {"referenced_version": 1.0}, {"referenced_version": 0},
            {"referenced_hash": 1}, {"case_id": []}, {"cause_status": {}},
            {"cause_status": "closed"}, {"retained_candidates": "h_B"},
            {"retained_candidates": ["h_B", "h_B"]}, {"retained_candidates": [1]},
            {"evidence_used": "e_B"}, {"evidence_used": ["e_B", "e_B"]},
            {"proposed_version_advance": 1}, {"proposed_version_advance": "true"},
            {"future_bypass_authorized": 0}, {"future_bypass_authorized": "false"},
            {"metadata": {"authorized": True}}, {"reason": "Claimed authorization"},
        ):
            with self.subTest(change=change):
                self.assert_rejected_unchanged(native_proposal(**change), "invalid_proposal")
        value = json.loads(native_proposal())
        for field in value:
            with self.subTest(missing=field):
                incomplete = dict(value)
                del incomplete[field]
                self.assert_rejected_unchanged(json.dumps(incomplete).encode(), "invalid_proposal")

    def test_native_probe_version_bump_without_change_rejects(self):
        self.assert_rejected_unchanged(native_proposal(retained_candidates=["h_A", "h_B"], cause_status="unresolved"), "version_advance_mismatch")
        self.assert_rejected_unchanged(native_proposal(proposed_version_advance=False), "version_advance_mismatch")

    def test_native_probe_cause_status_cannot_resolve_without_basis(self):
        self.assert_rejected_unchanged(native_proposal(retained_candidates=["h_A", "h_B"], evidence_used=[], proposed_version_advance=False), "cause_status_mismatch")
        self.assert_rejected_unchanged(native_proposal(cause_status="unresolved"), "cause_status_mismatch")
        self.assert_rejected_unchanged(native_proposal(retained_candidates=[], cause_status="resolved"), "cause_status_mismatch")
        self.assert_rejected_unchanged(native_proposal(evidence_used=[]), "invalid_transition")

    def test_native_probe_noop_does_not_change_any_authority(self):
        before = self.store.authority_snapshot()
        result = self.store.apply(native_proposal(retained_candidates=["h_B", "h_A"], cause_status="unresolved", evidence_used=[], proposed_version_advance=False))
        self.assertEqual(result["decision"], "no_commit")
        self.assertEqual(self.store.authority_snapshot(), before)

    def test_native_probe_future_bypass_rejects_entire_proposal(self):
        result = self.assert_rejected_unchanged(native_proposal(future_bypass_authorized=True), "authority_escalation")
        self.assertEqual(result["denied_authority_requests"], ["future_bypass_authorized"])
        self.assertIsNone(result["core_record"])

    def test_full_incorporation_is_explicit_external_case_policy(self):
        trusted = authority()
        trusted["cases"][0].update(candidates=["h_A", "h_B", "h_C"], require_full_incorporation=True, selected_response="a_B")
        trusted["admissions"] = [{"case_id": "case-1", "evidence_id": "e_B"}]
        with Store(Path(self.directory.name) / "full.sqlite3") as store:
            store.initialize(trusted)
            before = store.authority_snapshot()
            for raw in (
                native_proposal(retained_candidates=["h_A", "h_B"], cause_status="unresolved"),
                proposal(proposed_candidates=["h_A", "h_B"]),
            ):
                rejected = store.apply(raw)
                self.assertEqual(rejected["decision"], "reject")
                self.assertEqual(rejected["reason"], "full_incorporation_required")
                self.assertEqual(store.authority_snapshot(), before)
            accepted = store.apply(native_proposal())
            self.assertEqual(accepted["decision"], "commit")
            self.assertEqual(accepted["after"]["candidates"], ["h_B"])
            self.assertTrue(accepted["after"]["require_full_incorporation"])
            self.assertEqual(accepted["after"]["selected_response"], "a_B")
            self.assertEqual(accepted["core_record"]["action"]["value"], "a_B")

    def test_full_incorporation_cannot_omit_required_external_evidence(self):
        trusted = authority()
        trusted["cases"][0]["require_full_incorporation"] = True
        trusted["admissions"] = [{"case_id": "case-1", "evidence_id": "e_B"}]
        with Store(Path(self.directory.name) / "omitted-evidence.sqlite3") as store:
            store.initialize(trusted)
            before = store.authority_snapshot()
            for raw in (
                native_proposal(retained_candidates=["h_A", "h_B"], cause_status="unresolved", evidence_used=[], proposed_version_advance=False),
                native_proposal(evidence_used=[]),
                proposal(proposed_candidates=["h_A", "h_B"], evidence_ids=[]),
            ):
                result = store.apply(raw)
                self.assertEqual(result["decision"], "reject")
                self.assertEqual(result["reason"], "full_incorporation_required")
                self.assertIsNone(result["core_record"])
                self.assertEqual(store.authority_snapshot(), before)
            for operation in ("read", "summary"):
                self.assertEqual(store.apply(proposal(operation=operation))["decision"], "no_commit")
                self.assertEqual(store.authority_snapshot(), before)
            self.assertEqual(store.apply(native_proposal())["decision"], "commit")

    def test_full_incorporation_requires_complete_active_basis_and_exact_map(self):
        trusted = authority()
        trusted["cases"][0]["require_full_incorporation"] = True
        with Store(Path(self.directory.name) / "complete-basis.sqlite3") as store:
            store.initialize(trusted)
            before = store.authority_snapshot()
            result = store.apply(native_proposal())
            self.assertEqual(result["reason"], "full_incorporation_required")
            result = store.apply(native_proposal(evidence_used=["e_B", "second"]))
            self.assertEqual(result["decision"], "reject")
            self.assertEqual(result["reason"], "interpretation_missing")
            self.assertEqual(store.authority_snapshot(), before)
        trusted["interpretations"].append({"case_id": "case-1", "evidence_ids": ["e_B", "second"], "compatible": ["h_B"], "map_version": "exact-combined/v1"})
        with Store(Path(self.directory.name) / "complete-map.sqlite3") as store:
            store.initialize(trusted)
            result = store.apply(native_proposal(evidence_used=["second", "e_B"]))
            self.assertEqual(result["decision"], "commit")
            self.assertEqual(result["core_record"]["audit"]["evidence"], ["e_B", "second"])
            self.assertEqual(result["core_record"]["audit"]["map_version"], "exact-combined/v1")

    def test_native_partial_remains_allowed_without_full_incorporation_policy(self):
        trusted = authority()
        trusted["cases"][0]["candidates"] = ["h_A", "h_B", "h_C"]
        with Store(Path(self.directory.name) / "native-partial.sqlite3") as store:
            store.initialize(trusted)
            accepted = store.apply(native_proposal(retained_candidates=["h_A", "h_B"], cause_status="unresolved"))
            self.assertEqual(accepted["decision"], "commit")
            self.assertEqual(accepted["after"]["candidates"], ["h_A", "h_B"])
            self.assertFalse(accepted["after"]["require_full_incorporation"])

    def test_native_exhaustion_is_evidence_grounded(self):
        trusted = authority()
        trusted["interpretations"][0]["compatible"] = []
        with Store(Path(self.directory.name) / "exhausted.sqlite3") as store:
            store.initialize(trusted)
            accepted = store.apply(native_proposal(retained_candidates=[], cause_status="exhausted"))
            self.assertEqual(accepted["decision"], "commit")
            self.assertEqual(accepted["after"]["cause_status"], "exhausted")
            self.assertEqual(accepted["after"]["candidates"], [])

    def test_optional_trusted_case_fields_are_validated_and_hashed(self):
        for change in ({"cause_status": "resolved"}, {"require_full_incorporation": 1}, {"selected_response": ""}):
            trusted = authority()
            trusted["cases"][0].update(change)
            with self.subTest(change=change), Store(Path(self.directory.name) / "bad-option.sqlite3") as store:
                with self.assertRaises(GateError):
                    store.initialize(trusted)
        trusted = authority()
        for item in trusted["cases"]:
            del item["state_hash"]
        with Store(Path(self.directory.name) / "optional-fields.sqlite3") as store:
            store.initialize(trusted)
            state = store.snapshot("case-1")
            self.assertEqual(state["cause_status"], "unresolved")
            self.assertIsNone(state["selected_response"])
            self.assertFalse(state["require_full_incorporation"])
            hashed = {key: value for key, value in state.items() if key != "state_hash"}
            self.assertEqual(state["state_hash"], hashlib.sha256(canonical_json(hashed).encode()).hexdigest())


if __name__ == "__main__":
    unittest.main()
