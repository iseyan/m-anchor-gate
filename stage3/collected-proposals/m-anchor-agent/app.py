"""M-Anchor Agents API client. The local app never commits M-Anchor state."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import uuid
from contextlib import contextmanager
from typing import Any

from dotenv import load_dotenv
from openai import AsyncOpenAI, APIConnectionError, APIStatusError, APIError

HERE = Path(__file__).resolve().parent
PROJECT = "proj_NQT3WtX9S3RfYpmb7sE602d6"
TERMINAL = {"completed", "failed", "cancelled"}


class AppError(Exception):
    pass


def redact(value: Any) -> str:
    text = str(value)
    key = os.environ.get("OPENAI_API_KEY")
    if key:
        text = text.replace(key, "[REDACTED]")
    return re.sub(r"\bsk-[A-Za-z0-9_-]+", "[REDACTED]", text)


def note(value: Any) -> None:
    print(redact(value), file=sys.stderr, flush=True)


class StreamPrinter:
    """Retain a possible secret prefix across arbitrary event boundaries."""
    def __init__(self):
        self.pending = ""

    def write(self, text: str, final: bool = False):
        self.pending += text
        keep = 0
        if not final:
            tail = re.search(r"(?:sk-[A-Za-z0-9_-]*|sk|s)$", self.pending)
            if tail:
                keep = len(tail.group())
            key = os.environ.get("OPENAI_API_KEY", "")
            for length in range(1, min(len(key), len(self.pending)) + 1):
                if self.pending.endswith(key[:length]):
                    keep = max(keep, length)
        output = self.pending[:-keep] if keep else self.pending
        self.pending = self.pending[-keep:] if keep else ""
        print(redact(output), end="", flush=True)


def obj(value: Any) -> dict:
    return value if isinstance(value, dict) else value.model_dump(mode="json")


def message_text(item: dict) -> str:
    return "".join(part.get("text", "") for part in item.get("content", []) if part.get("type") == "output_text")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(redact(json.dumps(value, ensure_ascii=False, indent=2)), encoding="utf-8")
    temp.replace(path)


@contextmanager
def single_writer(directory: Path):
    """OS-backed lock releases even if the process crashes; no stale lock removal."""
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "writer.lock").open("a+b") as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise AppError("Another app process owns this state directory. Stop it first.") from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


class App:
    def __init__(self, client: AsyncOpenAI, directory: Path):
        self.client = client
        self.api = client.beta.agents.sessions
        self.directory = directory
        self.path = directory / "state.json"
        self.state = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {"project": PROJECT}
        if self.state.get("project") != PROJECT:
            raise AppError("State belongs to another project; use a separate --state-dir.")
        self.parts: dict[tuple, str] = {}
        self.printer = StreamPrinter()
        self.sent_results: set[tuple] = set()

    def save(self):
        write_json(self.path, self.state)

    @property
    def sid(self) -> str:
        sid = self.state.get("session_id")
        if not sid:
            raise AppError("No saved session. Run start first.")
        return sid

    def record(self, event: dict):
        if event.get("type", "").endswith("output_text.delta"):
            # Individual chunks may split credentials. Persist full done/items
            # text with redaction, and retain delta event metadata only.
            event = {**event, "delta": "[streamed; text in output_text.done/items]"}
        sid = self.state.get("session_id", "setup")
        with (self.directory / f"{sid}.events.jsonl").open("a", encoding="utf-8") as file:
            file.write(redact(json.dumps(event, ensure_ascii=False)) + "\n")

    async def create_agent(self) -> str:
        config = json.loads((HERE / "agent.json").read_text(encoding="utf-8"))
        digest = hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
        if self.state.get("agent_id"):
            if self.state.get("definition_sha256") != digest:
                raise AppError("agent.json changed. Use a new --state-dir to create a new definition.")
            # Verify that the reusable definition still exists in this project.
            await self.client.beta.agents.retrieve(self.state["agent_id"])
            note(f"Reusing agent: {self.state['agent_id']}")
            return self.state["agent_id"]
        if self.state.get("agent_creation_pending"):
            raise AppError("Previous agent creation has an unknown outcome. Inspect the Platform before retrying; no duplicate was created.")
        self.state["agent_creation_pending"] = True
        self.save()
        try:
            agent = await self.client.beta.agents.create(**config)
        except APIStatusError as exc:
            if exc.status_code < 500:
                self.state.pop("agent_creation_pending", None)
                self.save()
            raise
        self.state.update(agent_id=agent.id, definition_sha256=digest)
        self.state.pop("agent_creation_pending", None)
        self.save()
        write_json(self.directory / "saved-agent.json", obj(agent))
        note(f"Created reusable agent: {agent.id}")
        return agent.id

    async def handle_actions(self, session=None):
        session = session or await self.api.retrieve(self.sid)
        for action_model in session.required_actions:
            action = obj(action_model)
            if action["type"] == "environment_connection":
                note("Hosted environment connection pending; OpenAI manages its executor.")
                continue
            if action["type"] != "function_call":
                raise AppError(f"Unsupported required action: {action['type']}")
            identity = (action["turn_id"], action["call_id"])
            if identity in self.sent_results:
                continue
            # The supplied definition has tools=[]. Never execute names/arguments
            # supplied by the model as Python, shell, file paths, or authority.
            result = {
                "type": "agent.session.input.tool_result",
                "turn_id": action["turn_id"],
                "call_id": action["call_id"],
                "success": False,
                "error": "No application handler is registered for this tool. No authoritative state was changed.",
            }
            key = hashlib.sha256((self.sid + ":" + ":".join(identity)).encode()).hexdigest()
            await self.api.events.create(self.sid, events=[result], idempotency_key="tool-" + key)
            self.sent_results.add(identity)
            self.record({"type": "app.tool_result_submitted", "name": action["name"], **result})
            note(f"Function rejected (no registered handler): {action['name']}")

    async def event(self, model) -> bool:
        event = obj(model)
        kind = event.get("type", "unknown")
        session = event.get("session")
        if session:
            self.state["session_id"] = session["id"]
            self.state["environment_id"] = session.get("environment", {}).get("id")
            self.state.pop("session_creation_pending", None)
            self.save()
        turn = event.get("turn")
        root_turn = bool(turn and turn.get("subagent_id") is None)
        if root_turn and self.state.get("pending_input") and turn["id"] == self.state.get("previous_turn_id"):
            root_turn = False
        if root_turn and self.state.get("turn_id") and turn["id"] != self.state["turn_id"]:
            root_turn = False
        if root_turn:
            self.state["turn_id"] = turn["id"]
            self.state["turn_status"] = turn["status"]
            self.state.pop("pending_input", None)
            self.save()
        self.record(event)
        if kind.endswith("output_text.delta"):
            key = (event.get("item_id"), event.get("output_index"), event.get("content_index"))
            delta = event.get("delta", "")
            self.parts[key] = self.parts.get(key, "") + delta
            self.printer.write(delta)
        elif kind.endswith("output_text.done"):
            key = (event.get("item_id"), event.get("output_index"), event.get("content_index"))
            text = event.get("text", "")
            previous = self.parts.get(key, "")
            if text.startswith(previous):
                self.printer.write(text[len(previous):], final=True)
            elif text != previous:
                self.printer.write("\n" + text, final=True)
            else:
                self.printer.write("", final=True)
            self.parts[key] = text
            print(flush=True)
        elif not kind.endswith(".delta"):
            note(f"[{kind}]")
        if kind == "agent.session.requires_action":
            await self.handle_actions()
        if kind in {"error", "agent.session.failed", "agent.session.environment.failed"}:
            error = event.get("error") or event.get("message") or (session or {}).get("error") or event.get("environment", {}).get("error")
            raise AppError(f"{kind}: {error or 'see event log'}")
        return bool(root_turn and turn["status"] in TERMINAL)

    async def consume(self, stream):
        terminal = False
        async for event in stream:
            if await self.event(event):
                terminal = True
            if terminal and obj(event).get("type") == "agent.session.idle":
                self.printer.write("", final=True)
                return
        self.printer.write("", final=True)

    async def reconcile(self):
        session = await self.api.retrieve(self.sid)
        self.state["session_status"] = session.status
        self.state["environment_id"] = obj(session.environment).get("id")
        self.state.pop("session_creation_pending", None)
        if not self.state.get("turn_id"):
            async for turn in self.api.turns.list(self.sid, order="desc", limit=100):
                if turn.id == self.state.get("previous_turn_id"):
                    break
                if turn.subagent_id is None:
                    self.state["turn_id"] = turn.id
                    self.state.pop("pending_input", None)
                    break
        turn = None
        if self.state.get("turn_id"):
            turn = await self.api.turns.retrieve(self.state["turn_id"], session_id=self.sid)
            self.state["turn_status"] = turn.status
            write_json(self.directory / f"{turn.id}.turn.json", obj(turn))
        self.save()
        write_json(self.directory / f"{self.sid}.session.json", obj(session))
        if session.status == "failed":
            raise AppError(f"Session failed: {session.error}")
        return session, turn

    async def save_items(self):
        items = [obj(item) async for item in self.api.items.list(self.sid, order="asc", limit=100)]
        write_json(self.directory / f"{self.sid}.items.json", items)
        messages = [item for item in items if item.get("type") == "message" and item.get("role") == "assistant"]
        transcript = "\n\n".join(
            f"[{item.get('turn_id')} / {item.get('phase')}]\n{message_text(item)}"
            for item in messages
        )
        (self.directory / f"{self.sid}.transcript.txt").write_text(redact(transcript), encoding="utf-8")
        if not self.parts:
            for item in messages:
                if item.get("turn_id") == self.state.get("turn_id"):
                    print(redact(message_text(item)), flush=True)

    async def finish(self):
        _, turn = await self.reconcile()
        await self.save_items()
        if turn is None:
            raise AppError("No target turn could be confirmed. Run watch/status; do not resend input blindly.")
        note(f"Session: {self.sid}\nTurn: {turn.id}\nOutcome: {turn.status}")
        if turn.status != "completed":
            raise AppError(f"Turn is {turn.status}: {turn.error or 'run watch/status to inspect; no automatic input retry'}")

    async def watch(self):
        # Streams do not replay. Subscribe BEFORE reconciling to avoid a gap.
        stream = await self.api.events.stream(self.sid)
        async with stream:
            session, turn = await self.reconcile()
            if not turn or turn.status not in TERMINAL:
                await self.handle_actions(session)
                await self.consume(stream)
        await self.finish()

    async def start(self, message: str, new_session: bool):
        if self.state.get("session_creation_pending"):
            raise AppError("Previous session creation outcome is unknown. Inspect sessions in the Platform before retrying.")
        if self.state.get("session_id"):
            if not new_session:
                note("A session already exists. Reconnecting without sending the initial message again.")
                await self.watch()
                return
            session, turn = await self.reconcile()
            if session.status != "idle" or (turn and turn.status not in TERMINAL):
                raise AppError("Existing session is active. Finish/cancel it before --new-session.")
            archive = self.directory / f"{self.sid}.state.json"
            write_json(archive, self.state)
        agent_id = await self.create_agent()
        for field in ("session_id", "turn_id", "turn_status", "session_status", "environment_id", "previous_turn_id", "pending_input"):
            self.state.pop(field, None)
        self.state["session_creation_pending"] = True
        self.save()
        try:
            stream = await self.api.create(
                agent_id=agent_id,
                environment={"type": "openai_hosted", "network": {"access": "disabled"}},
                input=message,
                stream=True,
            )
        except APIStatusError as exc:
            if exc.status_code < 500:
                self.state.pop("session_creation_pending", None)
                self.save()
            raise
        async with stream:
            await self.consume(stream)
        await self.finish()

    async def send(self, message: str):
        session, previous = await self.reconcile()
        if self.state.get("pending_input"):
            raise AppError("Previous input has an unknown outcome. Run watch/status before another input.")
        if session.status != "idle" or (previous and previous.status not in TERMINAL):
            raise AppError("Session is not ready for new input. Run watch or cancel first.")
        key = str(uuid.uuid4())
        self.state["previous_turn_id"] = self.state.pop("turn_id", None)
        self.state.pop("turn_status", None)
        self.state["pending_input"] = {"idempotency_key": key, "message": message}
        self.save()
        # This helper subscribes before sending. One writer is enforced locally.
        async with self.api.stream(self.sid, input=message, idempotency_key=key) as stream:
            await self.consume(stream)
        await self.finish()

    async def cancel(self):
        await self.api.events.create(self.sid, events=[{"type": "agent.session.input.cancel"}])
        note("Cancellation requested. Waiting for the server to settle.")
        for _ in range(20):
            session, turn = await self.reconcile()
            if session.status == "idle" and (not turn or turn.status in TERMINAL):
                await self.save_items()
                note(f"Session settled; turn status: {turn.status if turn else 'none'}")
                return
            await asyncio.sleep(1)
        raise AppError("Cancellation is still pending. Inspect status before deleting.")

    async def delete(self):
        session, turn = await self.reconcile()
        if session.status != "idle" or (turn and turn.status not in TERMINAL):
            raise AppError("Session must settle before deletion. Run cancel/watch first.")
        await self.save_items()
        # The initial runtime probe produces no artifacts. Never discard any
        # later user-created artifacts silently.
        async for artifact in self.api.artifacts.list(self.sid):
            raise AppError(f"Session has artifact {artifact.id}; export and explicitly remove it before deletion (see README).")
        for attempt in range(3):
            try:
                await self.api.delete(self.sid)
                break
            except APIStatusError as exc:
                if exc.status_code != 409 or attempt == 2:
                    raise
                await asyncio.sleep(2)
        note(f"Deleted session: {self.sid}; hosted cleanup is asynchronous. Reusable agent retained.")
        write_json(self.directory / f"{self.sid}.deleted.json", self.state)
        for field in ("session_id", "turn_id", "turn_status", "environment_id", "session_status", "pending_input", "previous_turn_id"):
            self.state.pop(field, None)
        self.save()


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--state-dir", type=Path, default=HERE / ".runtime")
    result.add_argument("--env-file", type=Path)
    result.add_argument("--timeout", type=float, default=300, help="Observer timeout in seconds; does not cancel remote work")
    commands = result.add_subparsers(dest="command")
    commands.add_parser("create-agent")
    start = commands.add_parser("start")
    message = start.add_mutually_exclusive_group()
    message.add_argument("--message")
    message.add_argument("--message-file", type=Path)
    start.add_argument("--new-session", action="store_true")
    commands.add_parser("send").add_argument("message")
    for name in ("watch", "status", "cancel", "delete"):
        commands.add_parser(name)
    return result


async def run(args):
    if args.env_file:
        if not args.env_file.is_file():
            raise AppError("The specified --env-file does not exist.")
        load_dotenv(args.env_file, override=False)
    else:
        for path in (HERE / ".env.local", HERE.parent.parent / ".env.local"):
            if path.is_file():
                load_dotenv(path, override=False)
                break
    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise AppError("OPENAI_API_KEY is missing. Use secure key setup or set the environment variable; see README.")
    if args.timeout <= 0:
        raise AppError("--timeout must be positive.")
    # The credential must never be forwarded to the hosted environment. An
    # explicit API origin also prevents a local OPENAI_BASE_URL overriding it.
    async with AsyncOpenAI(project=PROJECT, base_url="https://api.openai.com/v1", max_retries=0, timeout=60) as client:
        app = App(client, args.state_dir.resolve())
        async with asyncio.timeout(args.timeout):
            command = args.command or "start"
            if command == "create-agent":
                await app.create_agent()
            elif command == "start":
                path = getattr(args, "message_file", None) or HERE / "initial-message.txt"
                message = getattr(args, "message", None) or path.read_text(encoding="utf-8")
                await app.start(message, getattr(args, "new_session", False))
            elif command == "send":
                await app.send(args.message)
            elif command == "watch":
                await app.watch()
            elif command == "status":
                session, turn = await app.reconcile()
                note(f"Agent: {app.state.get('agent_id')}\nSession: {app.sid}\nEnvironment: {app.state.get('environment_id')}\nSession status: {session.status}\nTurn: {turn.id if turn else 'unknown'}\nTurn status: {turn.status if turn else 'unknown'}")
                await app.save_items()
                if turn and turn.status in {"failed", "cancelled"}:
                    raise AppError(f"Turn ended with status {turn.status}: {turn.error}")
            elif command == "cancel":
                await app.cancel()
            elif command == "delete":
                await app.delete()


def main() -> int:
    for output in (sys.stdout, sys.stderr):
        if hasattr(output, "reconfigure"):
            output.reconfigure(encoding="utf-8", errors="replace")
    args = parser().parse_args()
    try:
        with single_writer(args.state_dir.resolve()):
            asyncio.run(run(args))
        return 0
    except APIStatusError as exc:
        tips = {
            400: "Check agent/model/environment configuration against current Agents API docs.",
            401: "Check OPENAI_API_KEY and its expiration (the provisioned key lasts 24 hours).",
            403: "Check project access, Agents API availability, and api.agents.read/write + api.responses.write permissions.",
            404: "Check saved IDs and model access in the specified project.",
            409: "Inspect status; existing work or environment setup may still be running.",
            429: "Check API credits, project spend limits and rate limits before retrying.",
        }
        note(f"OpenAI HTTP {exc.status_code}; request_id={exc.request_id}\n{redact(exc)}\n{tips.get(exc.status_code, 'Inspect status before any retry.')}")
    except (APIConnectionError, TimeoutError) as exc:
        note(f"Connection/observer interrupted ({type(exc).__name__}). Remote work may continue. Run watch/status; input was not automatically resubmitted.")
    except RuntimeError as exc:
        note(f"Stream/runtime error: {exc}. Run watch/status before sending another message.")
    except APIError as exc:
        note(f"OpenAI stream error: {exc}. Run watch/status to inspect the saved turn before retrying.")
    except KeyboardInterrupt:
        note("Observer stopped. Remote work may continue; use watch or cancel explicitly.")
        return 130
    except (AppError, OSError, ValueError) as exc:
        note(f"Error: {exc}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
