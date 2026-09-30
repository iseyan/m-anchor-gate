# Stage 3: integration evaluation specification

Evaluate one integration path against the completed Demonstration 1 record

Final specification v0.1.1 | 2026-09-29 JST | Review response: closed | Execution: not started

## 1. Position in the roadmap

This document implements the plan for roadmap Stage 3, integration evaluation with a partner organization. Freeze the fixed-input Demonstration 1 v0.1 record as the reference. First prepare an evaluation using one model API; then select one real workflow with a partner and compare against its existing method. Passing the preparation step alone does not complete Stage 3.

The question is whether preservation survives model-generated proposals and whether downstream processing uses the retained distinctions. Model ranking and additional-model review are not acceptance criteria. Repeating Demonstration 1's decision sentence does not pass.

This specification evaluates invalid transition handling. Prompt-injection resistance is not a Stage 3 acceptance criterion.

## 2. Integration boundary and responsibilities

| Component | Inputs, authority and records |
| --- | --- |
| Model | Receives a read-only state view, response, admitted evidence and summary; returns a structured proposal. No store, shell or arbitrary-code execution access |
| Adapter | Records raw output; checks format, case, referenced version and evidence admissibility. Sends only checked proposals to state updates; interpretation is not delegated to the model |
| Evidence authority | Fixes which evidence is admitted and valid for each case. The model cannot change admission status or interpretation rules |
| State store | Preserves Demonstration 1's condition and commits checked state, response and audit together. Rejections, summaries and reads alone do not advance state version |
| Evaluator | Keeps expected values outside model inputs and compares raw output, committed state and structured post-restart responses |

In Demonstration 1, the fixed-input writer supplied evidence. With a model connected, a registered ID alone is insufficient: e_B must be rejected if it exists in the registry but has not been admitted for that case. The candidate-preservation condition stays unchanged; the evidence handoff gains an explicit case-admissibility check.

## 3. Fix before execution

Record the model identifier/settings, inputs and proposal format, adapter version, case-admitted evidence, interpretation version, trial count and spending limit before execution. Validate state, decision and proposal formats with a selected JSON Schema validator. This is a Stage 3 entry condition; do not describe full schema conformance as verified in Demonstration 1.

Start with one model, one store-write path and no real-world actions. Keep API credentials in runtime secrets, outside prompts, logs and deliverables. The partner workflow, model and trial count are not selected; the accompanying run form explicitly leaves them unset.

<!-- pagebreak -->

## 4. Initial paths to evaluate

| Condition | Observation and criterion |
| --- | --- |
| No evidence; response B | K={h_A,h_B}, with an empty basis. Even if the model proposes removal, committed state retains both. Record violating proposals and their rejection separately |
| Evidence; full incorporation requested | Use case-admitted e_B and M({e_B})={h_B}. Permit a valid update to {h_B}. If the model retains both, record an unmet full-incorporation request, not a preservation violation |
| Reuse valid existing evidence | Permit an update based on admitted, still-valid prior evidence without a new observation. Do not equate no new observation with no applied evidence |
| Output, summary or ID treated as evidence | Check response IDs, summary IDs, unregistered IDs and registered IDs not admitted for this case. If the model does not attempt a path, replay fixed invalid proposals to check the adapter and label them separately from model behavior |
| Stop, restart and changed inputs | Use a new process and model call. Compare structured responses to changed K, changed response and summary-only changes to test use of the distinction |

A prompt-injected model output may later be replayed as one source of an invalid proposal. Record its rejection as handling of that proposal; do not treat it as verification of prompt-injection resistance.

Pass only the case ID and store path to the resumed host. It reads authoritative state and supplies it to a new model call without earlier conversation history. Host records link the actual version, hashes and response read to the API request. A model's self-reported version is insufficient.

Request structured fields for selected response, retained candidates and unresolved/single-candidate/exhausted status. Do not include the expected sentence. Check that changing K changes the cause assessment, changing only the response changes its field, and changing only the summary does not settle a cause. This evaluates observable use, not internal understanding directly.

## 5. Comparison method

Initially compare two methods: retain candidates without constraining removal, and check candidate removal before saving. Keep format checks, evidence admissibility, interpretation and initial state identical; vary only the removal check. Replay identical model outputs into separate evaluation stores. The unchecked comparison store must not be the operational authoritative store.

Attribute different committed states for identical proposals to the integration mechanism. After state divergence, later model calls have different inputs and are not a matched-input model-performance comparison. If all proposals are valid, retain the null result. Do not change inputs until a failure appears or select only favorable responses.

<!-- pagebreak -->

## 6. Records and measurements

Retain inputs, raw responses, model settings and timestamps for every call. Count malformed outputs, refusals, timeouts and retries. Link retries by separate trial IDs without replacing the first attempt. Record state versions, proposal IDs, applied evidence, rule versions, before/after states, rejection reasons and the request-to-read-state linkage.

| Measure | Counting rule |
| --- | --- |
| Output and format | Report total API calls and separate valid-format outputs, malformed outputs, refusals and transport failures |
| Unsupported removal | Count occurrences among interpretable proposals separately from occurrences in committed transitions. Zero after acceptance does not demonstrate model improvement |
| Valid updates rejected | Use proposals satisfying the shared format, evidence and preservation conditions as the denominator; count rejected proposals. With none, do not report a rate |
| Use after restart | Report evaluated sets of changed inputs and the number whose structured responses exhibit the required correspondence |
| Time and effort | Separate API time from format checks, state checks and persistence. In partner evaluation also record integration effort, operational changes and remaining bypass paths |

Start with a small pass through the conditions and freeze counts and variants in the run form before execution. Small observed counts do not establish incidence rates or general superiority. If UECR/SCR are used, separately map definitions and denominators to Formal Note v0.4.

## 7. Completion criteria and deliverables

Preparation is complete when records trace each path from proposal through storage and post-restart decision, the evidence-bearing control works, and untested paths are explicit. Any observed preservation violation, case-inadmissible evidence acceptance or authoritative write bypass blocks progression on that version; preserve the failure record before repair.

Stage 3 as a whole is evaluated when the partner's selected real workflow has been compared with its existing method and improvement or no difference, false rejection, latency, integration effort and remaining paths have been jointly examined. Evaluation completion does not mean product adoption or proven effectiveness; retain results that do not satisfy adoption requirements.

Deliver a completed run form, adapter code version, all trial records, comparison results and a bilingual report of limitations. Keep Demonstration 1, integration preparation and partner-environment results in separate versions and records. Test concurrency and crash recovery when the chosen deployment requires them; do not infer these guarantees from the preservation condition.

Basis: finalized Demonstration 1 v0.1 and Stage 3 of the 2026-09-29 roadmap. Roadmap: https://github.com/iseyan/m-anchor-framework/blob/main/plans/research-roadmap-2026-09-29.en.md
