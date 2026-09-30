# Stage 3 Adapter: development check record v0.1 (review revision 1)

2026-09-29 JST. Implementation preparation against final specification v0.1.1. These are executed fixed-input development checks, not a model-integration evaluation or Stage 3 completion record.

**Current position: fixed-input development checks have been executed. Stage 3 preparation evaluation is incomplete; model-integration evaluation has not been performed.** This revision addresses the supplied Grok review comments in the documentation. It adds no new trial results.

## Implementation scope

The Demonstration 1 candidate guard was copied without changes. The adapter adds fixed-field, case, referenced-version, state-hash and case-admission checks. The host generates authoritative versions and action IDs instead of copying proposed metadata. Accepted state, action and audit records share one SQLite transaction. Rejections retain raw input and reasons without adding state/action records.

This build accepts fixed development fixtures only. No live-model entry point is implemented. Suggested model/count/budget settings remain unadopted, and admission records cover synthetic development fixtures only.

## Fixed-input results

The pre-execution record fixed 15 conditions, expected values and source/input hashes. Model API calls: zero. Identical proposal bytes were replayed into independent checked and comparison stores. All 30 submissions matched the development expectations. The comparison disables only unsupported candidate-removal checking.

| Fixed condition | Checked | Comparison |
| --- | --- | --- |
| D01 preserve without evidence | accepted | accepted |
| D02 unsupported removal | rejected | accepted |
| D03 unknown evidence | rejected | rejected |
| D04 action as evidence | rejected | rejected |
| D05 summary as evidence | rejected | rejected |
| D06 registered case inadmissible | rejected | rejected |
| D07 wrong case | rejected | rejected |
| D08 forged version | rejected | rejected |
| D09 forged hash | rejected | rejected |
| D10 extra authoritative metadata | rejected | rejected |
| D11 malformed json | rejected | rejected |
| D12 valid full incorporation | accepted | accepted |
| D13 reuse existing evidence | accepted | accepted |
| D14 candidate restoration | rejected | rejected |
| D15 valid partial incorporation | accepted | accepted |

The checked path accepted four and rejected eleven conditions. Rejections preserved the full state hash, version and state/action record counts, not just K. D02 was the only commit difference. This is an implementation difference for fixed inputs, not model improvement or a model-output comparison result.

D15 is valid preservation despite partial incorporation. If full incorporation were requested as a task, retaining both would count as unmet task requirements. No model behavior was measured here.

## Fresh-process reads

Each writer terminated before its reader was launched. Readers received only case ID and store path as case information. Every read linked version 2, action records and actual state/input hashes. The downstream assessment was deterministic code, not a model output.

| Condition | Writer PID → reader PID | K read | Action / status |
| --- | --- | --- | --- |
| reference | 6 → 7 | h_A, h_B | a_B / unresolved |
| changed_K | 8 → 9 | h_B | a_B / single_candidate_under_interpretation |
| changed_action_only | 10 → 11 | h_A, h_B | a_A / unresolved |
| changed_summary_only | 12 → 13 | h_A, h_B | a_B / unresolved |

The K variant changed K and its state hash. The action variant changed the action and related hashes. The summary variant changed only summary.text in the exported input, leaving state and assessment identical. Actual difference paths are recorded. Linkage to real API requests and live-model use remain untested.

## External schema gate

Four JSON Schemas were authored for input, state, proposal and decision. Local shape and JSON parsing checks ran; external JSON Schema conformance did not. jsonschema could not be installed, and retrieval of an alternative validator returned 403. The validate_schemas.py command exited with code 2. The schema-gate-001.json report records status=blocked_or_failed and ModuleNotFoundError; that JSON itself has no exit-code field. No failure was replaced with a pass.

The Stage 3 schema entry condition remains unmet. External validation, mandatory runtime schema validation at a future live-model entry point, and freezing the actual model/settings/count/budget/case admissions remain. The partially prepared run form still has execution_ready=false.

## Status and remaining work

The review response is closed. This remains a fixed-input development-check record; the results and their attribution are given above. Stage 3 preparation evaluation remains incomplete, execution_ready=false, and this revision does not advance to Stage 4. The specification is unchanged, and this documentation revision adds no implementation results or integration into the mainline.

Remaining work comprises external JSON Schema validation, finalization of the official run form, and implementation of the live-model entry point with runtime schema validation and actual API-input linkage. Freeze the form before execution with the implementation version, schemas, model/settings, trial count, spending limit and case-specific evidence admissions. Record changes after freezing and freeze a revised form before execution.

The next schema-gate result and any finalized run form must be recorded in new files. Preserve schema-gate-001.json unchanged; do not append those subsequent records to this report.

## Records and limits

results/dev-001 contains raw proposals, SQLite stores, before/after audits, writer/reader outputs, the pre-execution record and blocked schema-gate record. Failed inputs are retained. The original Demonstration 1 and final specification were not edited.

No claims are made about concurrency, real crash recovery, privileged direct writes, prompt-injection resistance, model understanding, Demonstration 1 full schema conformance, partner evaluation, adoption or effectiveness.
