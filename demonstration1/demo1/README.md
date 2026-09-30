# Demonstration 1: use retained distinctions after restart v0.1

A fixed-input example selects response B while retaining candidate causes A/B, then uses the authoritative stored state in a separate process.

The primary decision remains:

> a_B was selected; causes A/B remain unresolved.

[日本語](README.ja.md)

The governing scope and scenario sheets are included unchanged in `specs/`. The 77-line Python v0.1 guard and its nine original tests are also unchanged. This demonstration has a separate version from Bundle 1.0.

## Run

From this extracted folder:

```bash
python run_demo.py --output-dir results/new-run
python -m unittest discover -v
```

Use a new output directory; existing results are not overwritten. The runtime needs only the Python standard library and no API key. Python 3.10+ is intended; this run used Linux and Python 3.12.14. On Windows, `py -3.13` may replace `python` to select the installed interpreter; Windows / 3.13 execution is not part of the reported verification.

## Components

| File | Role |
| --- | --- |
| `m_anchor_minimal.py` | Unmodified Python v0.1 candidate-preservation guard |
| `demo1.py` | Fixed evidence interpretation, checked updates, SQLite persistence, deterministic decisions |
| `writer.py` | Replay fixed proposals, save response and summary, then exit normally |
| `reader.py` | Separate process receiving only case ID and store location |
| `run_demo.py` | Start the reader after writer exit; evaluate expected values outside the reader |
| `schemas/` | JSON Schemas for state and resumption-decision records |
| `results/observed-2026-09-29/` | Observed database, records, process lifecycle, verdicts, environment and source hashes |

A checked save advances state version 0 to 1 and commits the state, response and acceptance audit in one SQLite transaction. Summary saves, rejected proposals and decision records do not advance the state version. Earlier state versions remain available.

The evidence registry is fixed on the checking side: `e_B` permits `{h_B}`; an empty basis permits Ω. Proposals cannot supply their own compatible set or interpretation rule. Evidence truth is not evaluated.

The reader loads authoritative state, its linked response record and the summary. The decision function takes only the read K and response value. One decision record links the state version, actual inputs, rule, result, process identities and state/response hashes. Hashes identify matching records; they provide no tamper-resistance guarantee.

## Verification boundary

The runner checks preservation, rejection and logging, use after restart, and an evidence-bearing control. Main and control use the same reader. Six additional tests cover summary substitution, missing authoritative state, changed response value, rollback when audit insertion fails, caller-supplied interpretations, and candidate exhaustion.

This is a deterministic implementation demonstration using fixed inputs. It does not measure LLM comprehension, reasoning or improvement. B is fixture input; no external form is submitted and no real-world action occurs. Model internals, evidence truth, authorization, concurrency, crash recovery and privileged direct writes are excluded.

The JSON Schemas define record formats; they are not a runtime general-purpose input validator. The recorded schema check covers JSON syntax and exact top-level field sets only, without an external JSON Schema validator. The original guard checks candidate preservation; `run_demo.py` checks scenario acceptance.

See the [English run report](demo1-implementation-and-run-v0.1.en.md) or [Japanese report](demo1-implementation-and-run-v0.1.ja.md).
