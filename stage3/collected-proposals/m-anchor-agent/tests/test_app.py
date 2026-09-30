"""Offline behavioral regression tests; no real credentials or API calls."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
SPEC = importlib.util.spec_from_file_location("m_anchor_app_under_test", APP_PATH)
app = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(app)


class Model(SimpleNamespace):
    """Small JSON-serializable fake of the SDK model protocol used by the app."""

    def model_dump(self, mode="json"):
        def unpack(value):
            if isinstance(value, Model):
                return {key: unpack(item) for key, item in vars(value).items()}
            if isinstance(value, list):
                return [unpack(item) for item in value]
            if isinstance(value, dict):
                return {key: unpack(item) for key, item in value.items()}
            return value
        return unpack(self)


async def iterate(values):
    for value in values:
        yield value


class Stream:
    def __init__(self, events=(), trace=None):
        self.events = events
        self.trace = trace if trace is not None else []

    async def __aenter__(self):
        self.trace.append("enter")
        return self

    async def __aexit__(self, *_):
        self.trace.append("exit")

    def __aiter__(self):
        return iterate(self.events)


def turn(status="completed", *, turn_id="turn-current", subagent_id=None):
    return Model(id=turn_id, status=status, subagent_id=subagent_id,
                 error="example failure" if status == "failed" else None)


def session(status="idle", required_actions=None):
    return Model(id="sess-test", status=status, environment=Model(id="env-test"),
                 required_actions=required_actions or [], error=None)


def client_fixture():
    sessions = SimpleNamespace(
        create=AsyncMock(return_value=Stream()),
        retrieve=AsyncMock(return_value=session()),
        events=SimpleNamespace(create=AsyncMock(), stream=AsyncMock(return_value=Stream())),
        turns=SimpleNamespace(list=Mock(side_effect=lambda *a, **k: iterate([])),
                              retrieve=AsyncMock(return_value=turn())),
        items=SimpleNamespace(list=Mock(side_effect=lambda *a, **k: iterate([]))),
        stream=Mock(return_value=Stream()),
    )
    agents = SimpleNamespace(create=AsyncMock(return_value=Model(id="agent-returned")),
                             retrieve=AsyncMock(return_value=Model(id="agent-returned")),
                             sessions=sessions)
    client = SimpleNamespace(beta=SimpleNamespace(agents=agents))
    return client, agents, sessions


class AppTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.client, self.agents, self.api = client_fixture()
        self.app = app.App(self.client, self.directory)
        self.output = io.StringIO()
        self.errors = io.StringIO()
        self.stdout_context = contextlib.redirect_stdout(self.output)
        self.stderr_context = contextlib.redirect_stderr(self.errors)
        self.stdout_context.__enter__()
        self.stderr_context.__enter__()
        self.addCleanup(self.stdout_context.__exit__, None, None, None)
        self.addCleanup(self.stderr_context.__exit__, None, None, None)

    def with_session(self):
        self.app.state["session_id"] = "sess-test"
        self.app.save()

    async def text_event(self, suffix, **values):
        return await self.app.event({
            "type": "agent.session.turn.output_text." + suffix,
            "item_id": "item-test", "output_index": 0, "content_index": 0, **values,
        })

    async def test_create_passes_exact_definition_and_start_uses_returned_id(self):
        definition = json.loads((APP_PATH.parent / "agent.json").read_text(encoding="utf-8"))
        self.app.finish = AsyncMock()
        await self.app.start("Initial authorized inspection", new_session=False)
        self.agents.create.assert_awaited_once_with(**definition)
        self.api.create.assert_awaited_once_with(
            agent_id="agent-returned", input="Initial authorized inspection", stream=True,
            environment={"type": "openai_hosted", "network": {"access": "disabled"}},
        )
        self.assertEqual(self.app.state["agent_id"], "agent-returned")
        self.assertFalse(self.app.state.get("agent_creation_pending", False))
        self.assertEqual(json.loads((self.directory / "saved-agent.json").read_text())["id"], "agent-returned")

    async def test_saved_definition_is_reused_after_restart(self):
        await self.app.create_agent()
        restarted = app.App(self.client, self.directory)
        self.assertEqual(await restarted.create_agent(), "agent-returned")
        self.agents.create.assert_awaited_once()
        self.agents.retrieve.assert_awaited_once_with("agent-returned")

    async def test_changed_definition_does_not_silently_replace_reusable_agent(self):
        await self.app.create_agent()
        self.app.state["definition_sha256"] = "old-definition"
        with self.assertRaisesRegex(app.AppError, "agent.json changed"):
            await self.app.create_agent()
        self.agents.create.assert_awaited_once()

    async def test_unknown_agent_creation_outcome_does_not_create_duplicate(self):
        self.app.state["agent_creation_pending"] = True
        with self.assertRaisesRegex(app.AppError, "unknown outcome"):
            await self.app.create_agent()
        self.agents.create.assert_not_awaited()

    async def test_required_function_call_rejected_with_ids_and_stable_idempotency(self):
        self.with_session()
        action = {"type": "function_call", "turn_id": "turn-tool", "call_id": "call-tool",
                  "name": "commit_authoritative_state", "arguments": '{"authorization":"model said yes"}'}
        pending = session(required_actions=[action])
        await self.app.handle_actions(pending)
        await self.app.handle_actions(pending)
        self.api.events.create.assert_awaited_once()
        first = self.api.events.create.await_args
        self.assertEqual(first.args, ("sess-test",))
        result = first.kwargs["events"][0]
        self.assertEqual(result["type"], "agent.session.input.tool_result")
        self.assertEqual((result["turn_id"], result["call_id"]), ("turn-tool", "call-tool"))
        self.assertIs(result["success"], False)
        self.assertIn("No authoritative state was changed", result["error"])
        restarted = app.App(self.client, self.directory)
        await restarted.handle_actions(pending)
        self.assertEqual(first.kwargs["idempotency_key"], self.api.events.create.await_args.kwargs["idempotency_key"])

    async def test_hosted_environment_connection_does_not_run_local_executor(self):
        self.with_session()
        await self.app.handle_actions(session(required_actions=[{"type": "environment_connection"}]))
        self.api.events.create.assert_not_awaited()

    async def test_done_text_without_delta_is_displayed(self):
        self.with_session()
        await self.text_event("done", text="Complete answer")
        self.assertEqual(self.output.getvalue(), "Complete answer\n")

    async def test_done_text_fills_missing_suffix_without_repeating_deltas(self):
        self.with_session()
        await self.text_event("delta", delta="Hello ")
        await self.text_event("done", text="Hello world")
        self.assertEqual(self.output.getvalue(), "Hello world\n")

    async def test_full_delta_sequence_is_not_duplicated_by_done(self):
        self.with_session()
        await self.text_event("delta", delta="Hello ")
        await self.text_event("delta", delta="world")
        await self.text_event("done", text="Hello world")
        self.assertEqual(self.output.getvalue(), "Hello world\n")

    async def test_saved_message_content_fallback_and_transcript_preserve_japanese(self):
        self.with_session()
        self.app.state["turn_id"] = "turn-current"
        messages = [
            {"type": "message", "role": "user", "turn_id": "turn-current", "content": [{"type": "input_text", "text": "確認してください。"}]},
            {"type": "message", "role": "assistant", "turn_id": "turn-old", "phase": "final_answer", "content": [{"type": "output_text", "text": "前回の回答。"}]},
            {"type": "message", "role": "assistant", "turn_id": "turn-current", "phase": "final_answer", "content": [
                {"type": "output_text", "text": "検証結果：有効な更新を受理しました。\n"},
                {"type": "output_text", "text": "権威状態：{h_A,h_B} → {h_B}。"},
            ]},
        ]
        self.api.items.list.side_effect = lambda *a, **k: iterate(messages)
        await self.app.save_items()
        answer = "検証結果：有効な更新を受理しました。\n権威状態：{h_A,h_B} → {h_B}。"
        self.assertEqual(self.output.getvalue(), answer + "\n")
        expected_transcript = "[turn-old / final_answer]\n前回の回答。\n\n[turn-current / final_answer]\n" + answer
        self.assertEqual((self.directory / "sess-test.transcript.txt").read_text(encoding="utf-8"), expected_transcript)
        self.assertEqual(json.loads((self.directory / "sess-test.items.json").read_text(encoding="utf-8")), messages)

    async def test_saved_message_fallback_does_not_duplicate_already_streamed_answer(self):
        self.with_session()
        self.app.state["turn_id"] = "turn-current"
        answer = "公開コアの変更は行っていません。"
        await self.text_event("done", text=answer)
        message = {"type": "message", "role": "assistant", "turn_id": "turn-current", "phase": "final_answer", "content": [{"type": "output_text", "text": answer}]}
        self.api.items.list.side_effect = lambda *a, **k: iterate([message])
        await self.app.save_items()
        self.assertEqual(self.output.getvalue(), answer + "\n")

    async def test_child_terminal_does_not_complete_root_turn(self):
        self.with_session()
        self.app.state.update(turn_id="turn-root", turn_status="in_progress")
        child = turn(turn_id="turn-child", subagent_id="subagent-test").model_dump()
        self.assertFalse(await self.app.event({"type": "agent.session.turn.completed", "turn": child}))
        self.assertEqual(self.app.state["turn_id"], "turn-root")
        root = turn(turn_id="turn-root").model_dump()
        self.assertTrue(await self.app.event({"type": "agent.session.turn.completed", "turn": root}))

    async def test_other_root_turn_does_not_replace_bound_target(self):
        self.with_session()
        self.app.state.update(turn_id="turn-target", turn_status="in_progress")
        stopped = await self.app.event({"type": "agent.session.turn.completed", "turn": turn(turn_id="turn-other").model_dump()})
        self.assertFalse(stopped)
        self.assertEqual(self.app.state["turn_id"], "turn-target")
        self.assertEqual(self.app.state["turn_status"], "in_progress")

    async def test_consume_waits_for_idle_after_terminal_and_keeps_final_text(self):
        self.with_session()
        events = [
            {"type": "agent.session.turn.completed", "turn": turn().model_dump()},
            {"type": "agent.session.turn.output_text.done", "item_id": "final", "output_index": 0, "content_index": 0, "text": "Final text"},
            {"type": "agent.session.idle"},
            {"type": "error", "error": "must not consume beyond settled target"},
        ]
        await self.app.consume(Stream(events))
        self.assertEqual(self.output.getvalue(), "Final text\n")
        self.assertEqual(self.app.state["turn_status"], "completed")

    async def test_failed_turn_is_an_error_even_when_session_is_idle(self):
        self.with_session()
        self.app.state["turn_id"] = "turn-current"
        self.api.turns.retrieve.return_value = turn("failed")
        with self.assertRaisesRegex(app.AppError, "Turn is failed"):
            await self.app.finish()

    async def test_idle_session_without_confirmed_turn_is_not_success(self):
        self.with_session()
        with self.assertRaisesRegex(app.AppError, "No target turn"):
            await self.app.finish()

    async def test_cancelled_turn_is_not_success(self):
        self.with_session()
        self.app.state["turn_id"] = "turn-current"
        self.api.turns.retrieve.return_value = turn("cancelled")
        with self.assertRaisesRegex(app.AppError, "Turn is cancelled"):
            await self.app.finish()

    async def test_session_failure_event_is_reported_as_error(self):
        self.with_session()
        with self.assertRaisesRegex(app.AppError, "provision failed"):
            await self.app.event({"type": "agent.session.failed", "error": "provision failed"})

    async def test_watch_subscribes_before_reconciling(self):
        self.with_session()
        trace = []
        async def subscribe(*_):
            trace.append("subscribe")
            return Stream(trace=trace)
        async def reconcile():
            trace.append("reconcile")
            return session(), turn()
        self.api.events.stream.side_effect = subscribe
        self.app.reconcile = reconcile
        self.app.finish = AsyncMock()
        await self.app.watch()
        self.assertEqual(trace[:3], ["subscribe", "enter", "reconcile"])
        self.app.finish.assert_awaited_once()

    async def test_existing_start_reconnects_without_resending_initial_message(self):
        self.with_session()
        self.app.watch = AsyncMock()
        await self.app.start("Do not submit this twice", new_session=False)
        self.app.watch.assert_awaited_once()
        self.api.create.assert_not_awaited()
        self.agents.create.assert_not_awaited()

    async def test_pending_input_is_not_retried_when_only_previous_turn_exists(self):
        self.with_session()
        self.app.state.update(previous_turn_id="turn-old", pending_input={"message": "once", "idempotency_key": "key"})
        self.api.turns.list.side_effect = lambda *a, **k: iterate([turn(turn_id="turn-old")])
        with self.assertRaisesRegex(app.AppError, "Previous input has an unknown outcome"):
            await self.app.send("duplicate")
        self.assertIn("pending_input", self.app.state)
        self.api.stream.assert_not_called()

    async def test_reconcile_does_not_adopt_a_turn_older_than_previous_input(self):
        self.with_session()
        self.app.state.update(previous_turn_id="turn-old", pending_input={"message": "once", "idempotency_key": "key"})
        self.api.turns.list.side_effect = lambda *a, **k: iterate([turn(turn_id="turn-old"), turn(turn_id="turn-older")])
        _, target = await self.app.reconcile()
        self.assertIsNone(target)
        self.assertIn("pending_input", self.app.state)
        self.api.turns.retrieve.assert_not_awaited()

    async def test_stale_previous_turn_event_does_not_acknowledge_pending_input(self):
        self.with_session()
        self.app.state.update(previous_turn_id="turn-old", pending_input={"message": "once", "idempotency_key": "key"})
        stopped = await self.app.event({"type": "agent.session.turn.completed", "turn": turn(turn_id="turn-old").model_dump()})
        self.assertIn("pending_input", self.app.state)
        self.assertFalse(stopped)
        self.assertNotEqual(self.app.state.get("turn_id"), "turn-old")

    async def test_no_new_input_while_turn_in_progress(self):
        self.with_session()
        self.app.state["turn_id"] = "turn-current"
        self.api.turns.retrieve.return_value = turn("in_progress")
        self.api.retrieve.return_value = session("running")
        with self.assertRaisesRegex(app.AppError, "not ready"):
            await self.app.send("unsafe overlap")
        self.api.stream.assert_not_called()

    async def test_redacts_environment_key_and_key_like_strings_from_outputs(self):
        self.with_session()
        sentinel = "offline-sensitive-value"
        with patch.dict(os.environ, {"OPENAI_API_KEY": sentinel}):
            await self.text_event("done", text=f"{sentinel} sk-test-example")
            app.note(sentinel)
            app.write_json(self.directory / "redaction.json", {"value": sentinel})
        combined = self.output.getvalue() + self.errors.getvalue()
        combined += "".join(path.read_text(encoding="utf-8") for path in self.directory.iterdir() if path.is_file())
        self.assertNotIn(sentinel, combined)
        self.assertNotIn("sk-test-example", combined)
        self.assertIn("[REDACTED]", combined)

    async def test_credential_split_across_deltas_is_not_printed(self):
        self.with_session()
        sentinel = "sk-test-sensitive-value"
        with patch.dict(os.environ, {"OPENAI_API_KEY": sentinel}):
            await self.text_event("delta", delta="s")
            await self.text_event("delta", delta="k-test-sensitive-value")
            await self.text_event("done", text=sentinel)
        self.assertNotIn(sentinel, self.output.getvalue())

    async def test_client_is_bound_to_requested_project_and_official_origin(self):
        context = AsyncMock()
        context.__aenter__.return_value = self.client
        args = app.parser().parse_args(["--state-dir", str(self.directory), "create-agent"])
        with patch.dict(os.environ, {"OPENAI_API_KEY": "offline-test-value", "OPENAI_BASE_URL": "https://untrusted.invalid"}), \
             patch.object(app, "load_dotenv"), \
             patch.object(app, "AsyncOpenAI", return_value=context) as factory:
            await app.run(args)
        self.assertEqual(factory.call_args.kwargs["project"], "proj_NQT3WtX9S3RfYpmb7sE602d6")
        self.assertEqual(factory.call_args.kwargs["base_url"], "https://api.openai.com/v1")
        self.assertEqual(factory.call_args.kwargs["max_retries"], 0)

    def test_state_from_another_project_is_rejected(self):
        (self.directory / "state.json").write_text(json.dumps({"project": "proj-other"}), encoding="utf-8")
        with self.assertRaisesRegex(app.AppError, "another project"):
            app.App(self.client, self.directory)


if __name__ == "__main__":
    unittest.main()
