# Demonstration 1: implementation and run record v0.1

2026-09-29 JST / fixed-input execution record / versioned separately from Bundle 1.0

The frozen primary scenario was implemented and executed across separate processes. All four governing acceptance criteria passed for the procedure that reads stored state and response records and uses those values in a decision. No LLM API was used.

## Inherited specification

Both language editions of Guarantee scope and success criteria v0.1 and Stage 2: Fixed scenario v0.1 are included unchanged. The governing source, unavailable to the external reviewer, was checked in this run and matched the hash stated in the scenario sheet.

The primary decision wording remains unchanged:

> a_B was selected; causes A/B remain unresolved.

## Observed results

| Criterion | Observation | Verdict |
| --- | --- | --- |
| 1 Preserve | `demo1-main` advanced from version 0 to 1 with K = `{h_A,h_B}` and an empty evidence basis. Both candidates remained after response B and the summary were saved | Pass |
| 2 Reject and log | A separate case rejected four proposals: unsupported `{h_B}` without evidence, an unregistered ID, and response/summary IDs used as evidence. Each logged the proposal, reason, evidence IDs, rule version and unchanged before/after state at version 1 | Pass |
| 3 Use after restart | After normal writer exit, a separate reader loaded version 1, both candidates and `action-001`, then produced the fixed decision. One record linked the read state/response hashes and version to the actual decision inputs | Pass |
| 4 Evidence control | A separate case fully incorporated registered evidence `e_B`, saved `{h_B}`, and used the same reader to conclude “only B is retained under this evidence interpretation” | Pass |

The main writer PID was 5 and reader PID 6; control writer PID was 9 and reader PID 10. Distinct process-instance UUIDs and start times were also recorded. The parent waited for writer exit and passed only the case ID and store path to the reader. Standard input was closed; case data and expected results were not supplied through environment variables.

The reader does not reconstruct K from the summary. It reads the summary but supplies only stored K and the response value to the decision function. Summary saves, rejection logs, reads and decision logs do not advance the state version.

The same procedure produced different judgments for unresolved and evidence-bearing states. Additional tests showed that changing the read response to `a_A` changes the unresolved wording, while changing only the summary does not change the decision. These checks establish the declared deterministic rule's dependence on read values, beyond matching a fixed sentence.

## Tests and environment

- Original guard tests: 9 passed.
- Additional persistence/resumption tests: 6 passed.
- Scenario acceptance: all 4 criteria passed.
- Environment: Linux x86_64, Python 3.12.14, SQLite 3.53.1.
- End-to-end run completed: 2026-09-29 13:38:11 JST.

The six additional tests cover rejecting caller-supplied evidence interpretations, invariance under summary substitution, refusing to replace missing authoritative state with a summary, rollback of state/response when audit insertion fails, dependence on the read response, and explicit candidate exhaustion.

```bash
python run_demo.py --output-dir results/new-run
python -m unittest discover -v
```

Observed artifacts are in `results/observed-2026-09-29/`: `acceptance.json` contains the four verdicts and detailed checks; `records.jsonl` contains state, response, audit, summary and decision records; `process-lifecycle.json` records launch/exit order; and `unit-tests.txt` contains all 15 test outputs. The SQLite database and individual decision JSON files are also included.

`source-hashes.json` identifies the executed sources, schemas and specifications. Its SHA-256 is `ec9ffeefbd9fea4c8b08b22ea4c4863e052a05cc0478f2c5c5421d50429b111c`. The original guard hash is `0f9551e8d00cd4408441944d9067cfe9bce7d5653019a5af27738fb5895f58c9`, matching the Bundle version.

## Interpretation boundary

The observations concern preservation and reuse under fixed candidates, evidence interpretation, one checked storage path and an explicit decision rule. They do not measure a model's ability to understand or use distinctions in natural language, or performance gains from M-Anchor instructions. Evidence `e_B` is a preregistered control fixture, not a real-world causal finding.

Transactional state/audit saving was checked; concurrency, real crash recovery and resistance to privileged direct writes remain excluded. The included JSON Schemas were checked for JSON syntax and matching top-level field sets. Full conformance testing with an external schema validator was not performed.

The implementation and observed run now accompany the Stage 2 planned scenario. Model connections and additional-model review can be considered later against this fixed record.
