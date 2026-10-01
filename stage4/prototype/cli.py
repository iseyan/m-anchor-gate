"""Local JSON interface for the Stage 4 prototype. No model or network calls."""

import argparse
import json
from pathlib import Path
import sqlite3
import sys
import uuid

from gate_api import GateAPI


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True, help="Path to a prototype SQLite store")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "read", "template", "submit", "summary", "audit", "assess"):
        command = commands.add_parser(name)
        command.add_argument("case_id")
        if name == "init":
            command.add_argument("--admit", action="append", default=[], choices=["e_B"])
        elif name == "template":
            command.add_argument("--action", default="a_B", choices=["a_A", "a_B"])
            command.add_argument("--output", help="Create a new UTF-8 JSON file; never overwrite")
        elif name == "submit":
            command.add_argument("--file", required=True, help="Raw UTF-8 proposal JSON")
        elif name == "summary":
            command.add_argument("--text", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            api = GateAPI.initialize(args.db, args.case_id, admitted_evidence=args.admit)
            result = api.read(args.case_id)
        else:
            api = GateAPI(args.db)
            if args.command == "read":
                result = api.read(args.case_id)
            elif args.command == "template":
                view = api.read(args.case_id)
                result = {
                    "proposal_id": str(uuid.uuid4()),
                    "case_id": args.case_id,
                    "expected_version": view["state"]["version"],
                    "expected_state_sha256": view["state_sha256"],
                    "proposed_K": view["state"]["K"],
                    "selected_action": args.action,
                    "evidence_ids": [],
                    "reason": "Provisional action; preserve the current candidates.",
                }
                if args.output:
                    with Path(args.output).open("x", encoding="utf-8", newline="\n") as stream:
                        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            elif args.command == "submit":
                result = api.submit(args.case_id, Path(args.file).read_bytes())
            elif args.command == "summary":
                result = api.save_summary(args.case_id, args.text)
            elif args.command == "audit":
                result = api.history(args.case_id)
            else:
                result = api.assess(args.case_id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if args.command == "submit" and result["status"] == "rejected" else 0
    except (ValueError, OSError, sqlite3.Error) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
