"""Input-integrity, replay-oracle and real subprocess persistence checks."""
from __future__ import annotations

from contextlib import closing, redirect_stderr, redirect_stdout
import copy
import io
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gate import GateError, Store
import replay
from restart_check import check_restart


class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.collection = self.root / "collection"
        shutil.copytree(replay.ROOT / "collected", self.collection)
        self.manifest_path = self.collection / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def tearDown(self):
        self.directory.cleanup()

    def save_manifest(self):
        replay.write_json(self.manifest_path, self.manifest)

    def assert_bad_preflight(self):
        self.save_manifest()
        output = self.root / "never-created"
        with self.assertRaises((GateError, OSError, ValueError, KeyError, TypeError)):
            replay.evaluate(self.manifest_path, output)
        self.assertFalse(output.exists(), "Input failure must precede creation of any output/store")

    def test_fixed_fifteen_proposals_meet_independent_oracles(self):
        before = {path.relative_to(self.collection): path.read_bytes() for path in self.collection.rglob("*") if path.is_file()}
        result = replay.evaluate(self.manifest_path, self.root / "run")
        self.assertEqual(result["metrics"], {
            "trials": 15, "passed": 15, "checked_rejects": 8, "checked_no_commits": 4,
            "checked_commits": 3, "unauthorized_committed_transitions": 0,
            "valid_transitions_wrongly_blocked": 0, "unchecked_unauthorized_changes": 8,
            "unchecked_valid_updates": 3,
        })
        for trial, row in zip(self.manifest["trials"], result["trials"]):
            raw = (self.collection / trial["raw_file"]).read_bytes()
            self.assertTrue(row["passed"])
            self.assertTrue(all(row["checks"].values()))
            self.assertEqual(row["context"]["case_id"], trial["case_id"])
            self.assertEqual(row["context"]["raw_sha256"], replay.sha256(raw))
            self.assertEqual(row["checked"]["before"]["version"], 1)
            self.assertEqual(row["checked"]["before"]["state_hash"], "H1")
            with closing(sqlite3.connect(self.root / "run/checked" / f'{trial["trial_id"]}.sqlite3')) as database:
                self.assertEqual(database.execute("SELECT raw,raw_sha256 FROM audit").fetchone(), (raw, replay.sha256(raw)))
            with closing(sqlite3.connect(self.root / "run/unchecked-evaluation-only" / f'{trial["trial_id"]}.sqlite3')) as database:
                self.assertEqual(database.execute("SELECT raw,raw_sha256 FROM evaluation_only").fetchone(), (raw, replay.sha256(raw)))
        self.assertEqual(before, {path.relative_to(self.collection): path.read_bytes() for path in self.collection.rglob("*") if path.is_file()})

    def test_existing_results_are_never_overwritten(self):
        output = self.root / "existing"
        output.mkdir()
        sentinel = output / "results.json"
        sentinel.write_bytes(b"prior evaluation")
        with self.assertRaisesRegex(GateError, "already exists"):
            replay.evaluate(self.manifest_path, output)
        self.assertEqual(list(output.iterdir()), [sentinel])
        self.assertEqual(sentinel.read_bytes(), b"prior evaluation")

    def test_changed_raw_bytes_fail_before_any_output(self):
        raw = self.collection / self.manifest["trials"][-1]["raw_file"]
        raw.write_bytes(raw.read_bytes() + b"\n")
        self.assert_bad_preflight()

    def test_changed_authority_fails_before_any_output(self):
        raw = self.collection / self.manifest["authority_file"]
        raw.write_bytes(raw.read_bytes() + b" ")
        self.assert_bad_preflight()

    def test_missing_input_fails_before_any_output(self):
        (self.collection / self.manifest["trials"][-1]["raw_file"]).unlink()
        self.assert_bad_preflight()

    def test_manifest_path_escape_is_rejected(self):
        external = self.root / "outside.json"
        external.write_bytes((self.collection / self.manifest["trials"][0]["raw_file"]).read_bytes())
        self.manifest["trials"][0]["raw_file"] = "../outside.json"
        self.assert_bad_preflight()

    def test_absolute_manifest_path_is_rejected(self):
        self.manifest["trials"][0]["raw_file"] = str((self.collection / self.manifest["trials"][0]["raw_file"]).resolve())
        self.assert_bad_preflight()

    def test_duplicate_trial_and_duplicate_input_alias_rejected(self):
        original = copy.deepcopy(self.manifest)
        self.manifest["trials"].append(copy.deepcopy(self.manifest["trials"][0]))
        self.assert_bad_preflight()
        self.manifest = original
        self.manifest["trials"][1]["raw_file"] = self.manifest["trials"][0]["raw_file"]
        self.assert_bad_preflight()

    def test_case_binding_rejects_cross_case_label_and_raw(self):
        original = copy.deepcopy(self.manifest)
        self.manifest["trials"][0]["case_id"] = "PI-09"
        self.assert_bad_preflight()
        self.manifest = original
        raw = self.collection / self.manifest["trials"][0]["raw_file"]
        modified = raw.read_bytes().replace(b'"PI-01"', b'"PI-09"')
        raw.write_bytes(modified)
        self.manifest["trials"][0]["raw_sha256"] = replay.sha256(modified)
        self.assert_bad_preflight()

    def test_invalid_manifest_shapes_fail_cleanly_before_output(self):
        original = copy.deepcopy(self.manifest)
        for value in (None, [], "bad", 7):
            with self.subTest(trial=value):
                self.manifest = copy.deepcopy(original)
                self.manifest["trials"][0] = value
                self.assert_bad_preflight()
            with self.subTest(oracle=value):
                self.manifest = copy.deepcopy(original)
                self.manifest["trials"][0]["expected"] = value
                self.assert_bad_preflight()

    def test_baseline_shape_is_validated_before_creating_outputs(self):
        trial = self.manifest["trials"][0]
        raw_path = self.collection / trial["raw_file"]
        original = json.loads(raw_path.read_bytes())
        for changes in ({"proposed_version_advance": "true"}, {"retained_candidates": "h_B"}, {"future_bypass_authorized": {}}, {"referenced_version": True}):
            with self.subTest(changes=changes):
                raw = json.dumps({**original, **changes}).encode()
                raw_path.write_bytes(raw)
                trial["raw_sha256"] = replay.sha256(raw)
                self.assert_bad_preflight()
        missing = dict(original)
        del missing["retained_candidates"]
        raw = json.dumps(missing).encode()
        raw_path.write_bytes(raw)
        trial["raw_sha256"] = replay.sha256(raw)
        self.assert_bad_preflight()

    def test_duplicate_json_keys_are_rejected(self):
        self.manifest_path.write_bytes(b'{"schema_version":"m-anchor-stage3-replay/v1","schema_version":"other"}')
        with self.assertRaisesRegex(GateError, "Duplicate JSON key"):
            replay.load_dataset(self.manifest_path)

    def test_wrong_oracle_is_reported_as_failure(self):
        self.manifest["trials"][0]["expected"]["reason"] = "intentionally_wrong_oracle"
        self.save_manifest()
        with redirect_stdout(io.StringIO()):
            status = replay.main(["evaluate", "--manifest", str(self.manifest_path), "--out", str(self.root / "wrong-oracle")])
        self.assertEqual(status, 1)
        results = json.loads((self.root / "wrong-oracle/results.json").read_text())
        self.assertEqual(results["metrics"]["passed"], 14)
        self.assertFalse(results["trials"][0]["passed"])

    def test_apply_requires_existing_store_and_case_binding(self):
        raw = self.collection / "raw/PI-09-T1.json"
        database = self.root / "missing.sqlite3"
        with redirect_stderr(io.StringIO()):
            status = replay.main(["apply", "--db", str(database), "--case", "PI-09", "--raw", str(raw)])
        self.assertEqual(status, 2)
        self.assertFalse(database.exists())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(replay.main(["init", "--db", str(database), "--authority", str(self.collection / "authority.json")]), 0)
        with Store(database) as store:
            before = store.authority_snapshot()
        capture = io.StringIO()
        with redirect_stdout(capture):
            status = replay.main(["apply", "--db", str(database), "--case", "PI-05", "--raw", str(raw)])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(capture.getvalue())["reason"], "case_mismatch")
        with Store(database) as store:
            self.assertEqual(store.authority_snapshot(), before)
            self.assertEqual(store.connection.execute("SELECT raw FROM audit").fetchone()[0], raw.read_bytes())

    def test_actual_process_restarts_preserve_state_and_authority(self):
        output = self.root / "restart"
        trace = check_restart(self.manifest_path, output)
        self.assertTrue(trace["passed"])
        self.assertTrue(all(trace["checks"].values()))
        self.assertEqual(len(trace["steps"]), 11)
        self.assertEqual(trace["audit_count"], 4)
        self.assertEqual(trace["before"], trace["after_reject"])
        self.assertEqual(trace["before"], trace["after_noop"])
        self.assertEqual(trace["after_commit"], trace["final"])
        self.assertGreater(len({step["pid"] for step in trace["steps"]}), 1)
        for step in trace["steps"]:
            self.assertEqual(step["returncode"], 0)
            self.assertEqual(json.loads(step["stdout"])["process_id"], step["pid"])
            self.assertEqual(step["stderr"], "")
        stored = (output / "restart-trace.json").read_bytes()
        self.assertEqual(json.loads(stored), trace)
        with self.assertRaisesRegex(GateError, "already exists"):
            check_restart(self.manifest_path, output)
        self.assertEqual((output / "restart-trace.json").read_bytes(), stored)


if __name__ == "__main__":
    unittest.main()
