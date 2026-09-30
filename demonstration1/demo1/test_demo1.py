"""Focused checks of persistence and data dependence; no model behavior claim."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from demo1 import checked_save, derive, initialize, resume, save_summary


class DemoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Path(self.temp.name) / "state.sqlite3"
        initialize(self.store, "case")
        self.proposal = {"action_record_id": "action-001", "selected_action": "a_B",
                         "reason": "Provisional choice", "evidence_ids": [], "proposed_K": ["h_A", "h_B"]}

    def save(self):
        checked_save(self.store, "case", self.proposal)
        save_summary(self.store, "case", "暫定対応Bを選択した。", "Provisional response B was selected.")

    def test_interpretation_cannot_be_supplied_by_proposer(self):
        attempt = dict(self.proposal, evidence_ids=["e_B"], proposed_K=["h_B"], compatible=["h_B"])
        audit = checked_save(self.store, "case", attempt)
        self.assertEqual(audit["status"], "rejected")
        self.assertEqual(audit["state_before"], audit["state_after"])

    def test_summary_changes_do_not_change_decision_or_version(self):
        self.save()
        before = resume(self.store, "case")
        with sqlite3.connect(self.store) as con:
            row = con.execute("SELECT payload FROM records WHERE kind='summary'").fetchone()
            summary = json.loads(row[0])
            summary["text_ja"] = "原因Bが確定した。"
            con.execute("UPDATE records SET payload=? WHERE kind='summary'", (json.dumps(summary),))
        after = resume(self.store, "case")
        self.assertEqual(after["decision_ja"], before["decision_ja"])
        self.assertEqual(after["state_sha256"], before["state_sha256"])
        self.assertEqual(after["state_version_read"], 1)

    def test_missing_authoritative_state_does_not_fall_back_to_summary(self):
        self.save()
        with sqlite3.connect(self.store) as con:
            con.execute("DELETE FROM records WHERE kind='state'")
        with self.assertRaisesRegex(ValueError, "Missing authoritative record"):
            resume(self.store, "case")

    def test_failed_audit_insert_rolls_back_state_and_action(self):
        with sqlite3.connect(self.store) as con:
            con.execute("""CREATE TRIGGER fail_audit BEFORE INSERT ON records
                WHEN NEW.kind='audit' BEGIN SELECT RAISE(ABORT,'injected audit failure'); END""")
        with self.assertRaisesRegex(sqlite3.IntegrityError, "injected audit failure"):
            checked_save(self.store, "case", self.proposal)
        with sqlite3.connect(self.store) as con:
            self.assertEqual(con.execute("SELECT version FROM records WHERE kind='state'").fetchall(), [(0,)])
            self.assertEqual(con.execute("SELECT COUNT(*) FROM records WHERE kind='action'").fetchone()[0], 0)

    def test_action_read_affects_unresolved_wording(self):
        self.proposal["selected_action"] = "a_A"
        self.save()
        result = resume(self.store, "case")
        self.assertEqual(result["decision_ja"], "a_Aは選択済み／原因A・Bは未決")
        self.assertEqual(result["decision_inputs"]["selected_action"], "a_A")

    def test_empty_candidates_are_exhaustion(self):
        self.assertEqual(derive([], "a_B")[0], "candidate_exhaustion")


if __name__ == "__main__":
    unittest.main()
