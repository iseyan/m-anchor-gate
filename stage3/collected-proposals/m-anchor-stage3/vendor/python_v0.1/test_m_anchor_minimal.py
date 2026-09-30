"""Local guard tests; these are not LLM behavior experiments."""

import json
import unittest
from dataclasses import FrozenInstanceError

from m_anchor_minimal import MAnchor


class MAnchorTests(unittest.TestCase):
    def test_action_only_keeps_both_candidates(self):
        state = MAnchor({"h_A", "h_B"})
        for action in ("a_A", "a_B", "approve", "stop"):
            with self.subTest(action=action):
                after, record = state.step(action, "Interface requires a selection")
                self.assertEqual(after.candidates, {"h_A", "h_B"})
                self.assertEqual(record["audit"]["removed"], [])
                self.assertEqual(record["action"]["value"], action)
                self.assertEqual(json.loads(json.dumps(record)), record)

    def test_action_cannot_overwrite_unresolved_state(self):
        state = MAnchor({"h_A", "h_B"})
        with self.assertRaisesRegex(ValueError, "Unsupported removal"):
            state.step("a_B", "Forced choice", proposed={"h_B"})
        self.assertEqual(state.candidates, {"h_A", "h_B"})

    def test_full_incorporation_records_its_basis(self):
        state = MAnchor({"h_A", "h_B"})
        after, record = state.step(
            "a_B", "Policy chooses B", evidence={"observation-1@v1"},
            compatible={"h_B"}, map_version="fixture/v1",
        )
        self.assertEqual(after.candidates, {"h_B"})
        self.assertEqual(record["audit"]["evidence"], ["observation-1@v1"])
        self.assertEqual(record["audit"]["removed"], ["h_A"])
        self.assertEqual(record["action"]["candidates"], ["h_A", "h_B"])
        self.assertEqual(state.candidates, {"h_A", "h_B"})

    def test_partial_incorporation_and_reuse_of_old_evidence(self):
        state = MAnchor({"h_A", "h_B", "h_C"})
        basis = dict(evidence={"old-record@v1"}, compatible={"h_A"}, map_version="rule/v1")
        partial, _ = state.step("wait", "Partial incorporation", proposed={"h_A", "h_B"}, **basis)
        self.assertEqual(partial.candidates, {"h_A", "h_B"})
        retained, _ = partial.step("wait", "No evidence applied")
        self.assertEqual(retained.candidates, partial.candidates)
        complete, _ = retained.step("continue", "Reapply the still-valid record", **basis)
        self.assertEqual(complete.candidates, {"h_A"})

    def test_mixed_removal_is_rejected(self):
        state = MAnchor({"h_A", "h_B", "h_C"})
        with self.assertRaisesRegex(ValueError, "Unsupported removal"):
            state.step("a_C", "Proposed selection", evidence={"record@v1"},
                       compatible={"h_A"}, map_version="rule/v1", proposed={"h_C"})
        self.assertEqual(state.candidates, {"h_A", "h_B", "h_C"})

    def test_evidence_and_interpretation_must_be_supplied_together(self):
        state = MAnchor({"h_A", "h_B"})
        invalid = (
            {"compatible": {"h_B"}, "map_version": "rule/v1"},
            {"evidence": {"record@v1"}},
            {"evidence": {"record@v1"}, "compatible": {"h_B"}},
            {"evidence": {"record@v1"}, "compatible": {"outside"}, "map_version": "rule/v1"},
        )
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                state.step("a_B", "Proposed update", **kwargs)

    def test_empty_state_is_exhaustion_and_cannot_reopen(self):
        state = MAnchor({"h_A", "h_B"})
        exhausted, record = state.step("stop", "No candidates remain", evidence={"record@v1"},
                                       compatible=set(), map_version="rule/v1")
        self.assertEqual(exhausted.candidates, set())
        self.assertEqual(record["audit"]["after"], [])
        unchanged, _ = exhausted.step("stop", "Await separate diagnosis")
        self.assertEqual(unchanged.candidates, set())
        with self.assertRaisesRegex(ValueError, "cannot add or restore"):
            exhausted.step("continue", "Attempted reopening", proposed={"h_A"})

    def test_input_and_output_aliases_cannot_mutate_state(self):
        source = {"h_A", "h_B"}
        state = MAnchor(source)
        source.clear()
        after, record = state.step("a_B", "Forced choice")
        record["audit"]["after"].clear()
        self.assertEqual(after.candidates, {"h_A", "h_B"})
        with self.assertRaises(FrozenInstanceError):
            state.candidates = frozenset({"h_B"})

    def test_initial_scope_and_identifier_validation(self):
        for omega, candidates in ((set(), None), ({"h_A"}, {"h_B"}), ("h_A", None), ({""}, None)):
            with self.subTest(omega=omega), self.assertRaises(ValueError):
                MAnchor(omega, candidates)
        state = MAnchor({"h_A", "h_B"}, {"h_A"})
        with self.assertRaisesRegex(ValueError, "cannot add or restore"):
            state.step("a_B", "Attempted expansion", proposed={"h_B"})


if __name__ == "__main__":
    unittest.main()
