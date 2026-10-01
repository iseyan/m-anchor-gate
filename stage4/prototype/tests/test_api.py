"""Behavior checks for the local API, using only disposable stores."""

import base64
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import uuid

PROTOTYPE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROTOTYPE))
from gate_api import GateAPI


class LocalAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / "state.sqlite3"
        self.api = GateAPI.initialize(self.db, "case-1")

    def proposal(self, api=None, **changes):
        api = api or self.api
        view = api.read("case-1")
        proposal = {
            "proposal_id": str(uuid.uuid4()), "case_id": "case-1",
            "expected_version": view["state"]["version"],
            "expected_state_sha256": view["state_sha256"],
            "proposed_K": view["state"]["K"], "selected_action": "a_B",
            "evidence_ids": [], "reason": "Provisional response.",
        }
        proposal.update(changes)
        return json.dumps(proposal).encode()

    def test_action_save_and_summary_preserve_unresolved_candidates(self):
        result = self.api.submit("case-1", self.proposal())
        self.assertEqual(result["status"], "accepted")
        before = self.api.read("case-1")
        self.assertEqual(before["state"]["version"], 1)
        self.assertEqual(before["state"]["K"], ["h_A", "h_B"])
        self.api.save_summary("case-1", "Cause B is certain; discard A.")
        after = self.api.read("case-1")
        self.assertEqual(after["state_sha256"], before["state_sha256"])
        self.assertEqual(after["action"], before["action"])
        decision = self.api.assess("case-1")
        self.assertFalse(decision["summary_used_for_decision"])

    def test_rejections_preserve_state_and_record_original_bytes(self):
        before = self.api.read("case-1")
        inputs = [
            self.proposal(proposed_K=["h_B"]),
            self.proposal(proposed_K=["h_B"], evidence_ids=["e_B"]),
            self.proposal(evidence_ids=["action-001"]),
            self.proposal(evidence_ids=["summary-001"]),
            self.proposal(case_id="another-case"),
            self.proposal(expected_version=True),
            self.proposal(expected_state_sha256="0" * 64),
            b'{"proposal_id":"x","proposal_id":"y"}',
            b'{"broken":',
        ]
        for raw in inputs:
            with self.subTest(raw=raw):
                result = self.api.submit("case-1", raw)
                self.assertEqual(result["status"], "rejected")
                self.assertEqual(base64.b64decode(result["raw_base64"]), raw)
                self.assertEqual(self.api.read("case-1")["state"], before["state"])
                self.assertEqual(self.api.read("case-1")["action"], before["action"])
        audits = self.api.history("case-1")
        self.assertGreaterEqual(sum(a.get("status") == "rejected" for a in audits), len(inputs))

    def test_admitted_evidence_allows_reduction_and_old_reference_is_rejected(self):
        api = GateAPI.initialize(Path(self.temp.name) / "admitted.sqlite3", "case-1", ["e_B"])
        raw = self.proposal(api, proposed_K=["h_B"], evidence_ids=["e_B"])
        self.assertEqual(api.submit("case-1", raw)["status"], "accepted")
        self.assertEqual(api.read("case-1")["state"]["K"], ["h_B"])
        self.assertEqual(api.submit("case-1", raw)["status"], "rejected")
        self.assertEqual(api.read("case-1")["state"]["version"], 1)
        self.assertEqual(api.submit("case-1", self.proposal(api, proposed_K=["h_A", "h_B"]))["status"], "rejected")

    def test_partial_incorporation_is_legal(self):
        api = GateAPI.initialize(Path(self.temp.name) / "partial.sqlite3", "case-1", ["e_B"])
        result = api.submit("case-1", self.proposal(api, evidence_ids=["e_B"]))
        self.assertEqual(result["status"], "accepted")
        self.assertEqual(api.read("case-1")["state"]["K"], ["h_A", "h_B"])

    def test_cli_fresh_process_uses_saved_state(self):
        script = str(PROTOTYPE / "cli.py")
        proposal_file = Path(self.temp.name) / "proposal.json"
        commands = [
            ["template", "case-1", "--output", str(proposal_file)],
            ["submit", "case-1", "--file", str(proposal_file)],
            ["assess", "case-1"],
        ]
        outputs = []
        for command in commands:
            completed = subprocess.run([sys.executable, "-B", script, "--db", str(self.db), *command], capture_output=True, encoding="utf-8", check=True)
            outputs.append(json.loads(completed.stdout))
        self.assertEqual(outputs[1]["status"], "accepted")
        self.assertEqual(self.api.read("case-1")["state"]["K"], ["h_A", "h_B"])
        self.assertFalse(outputs[2]["summary_used_for_decision"])
        self.assertNotEqual(outputs[1]["pid"], outputs[2]["pid"])
        self.assertEqual(outputs[2]["version"], 1)
        self.assertEqual(outputs[2]["state_sha256"], outputs[1]["state_sha256_after"])
        self.assertEqual(outputs[2]["candidates"], ["h_A", "h_B"])
        self.assertEqual(outputs[2]["action"], outputs[1]["action_after"])
        self.assertEqual(outputs[2]["assessment_ja"], "a_Bは選択済み／原因A・Bは未決")

    def test_audit_write_error_rolls_back_state_and_action(self):
        before = self.api.read("case-1")
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("CREATE TRIGGER fail_audit BEFORE INSERT ON audit BEGIN SELECT RAISE(ABORT, 'test write failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.api.submit("case-1", self.proposal())
        self.assertEqual(self.api.read("case-1"), before)
        self.assertEqual(self.api.history("case-1"), [])
        with closing(sqlite3.connect(self.db)) as connection, connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM actions").fetchone()[0], 0)

    def test_existing_or_foreign_store_is_not_overwritten(self):
        before = self.db.read_bytes()
        with self.assertRaises((ValueError, FileExistsError)):
            GateAPI.initialize(self.db, "case-1")
        self.assertEqual(self.db.read_bytes(), before)
        foreign = Path(self.temp.name) / "other.sqlite3"
        with closing(sqlite3.connect(foreign)) as connection, connection:
            connection.execute("CREATE TABLE example(value TEXT)")
        before = foreign.read_bytes()
        with self.assertRaises((ValueError, sqlite3.Error)):
            GateAPI(foreign)
        self.assertEqual(foreign.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
