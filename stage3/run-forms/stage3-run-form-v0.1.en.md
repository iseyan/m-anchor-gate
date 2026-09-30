# Stage 3: pre-execution run form

Keep the unfilled official form separate from an optional first-run proposal

Run form v0.1 | Specification v0.1.1 | 2026-09-29 JST | Not frozen; not executed

## 1. Official values to fill

This form covers integration preparation, not observed results. Unset values correspond to JSON null. Only specification requirements are inherited. Do not automatically adopt the suggestions below. Fix values, files and hashes before execution.

| Field | Official value / information required |
| --- | --- |
| Run identity | Unset: run ID, form revision, responsible operator and freeze timestamp |
| Model identity | Unset: provider, API identifier, pinned version and endpoint. Also retain the identifier returned during execution |
| Model settings | Unset: reasoning, output cap, explicit and omitted settings, request timeout. No tools and no inherited conversation are fixed |
| Trial counts | Unset: API calls per path, restart variants, fixed proposal replays, total call limit and retry policy |
| Spending limit | Unset: currency, amount, pricing check date and pre-call budget check, including unresolved usage after transport failure |
| Evidence and rules | Unset: case-admission manifest, authority and timestamp, interpretation version and file SHA-256 values |
| Adapter and formats | Unset: adapter revision/hash; input, state, decision and proposal formats/hashes; location of evaluator-only expected values |
| Schema validation | Unset: validator/version, dialect, options, command and result file. Validation has not been performed |

## 2. Optional first-run proposal (not adopted)

The separate proposal JSON suggests OpenAI gpt-5.4-mini-2026-03-17 via Responses, reasoning.effort=none and max_output_tokens=2048. Limit each input to 8192 tokens; provide no tools or earlier-response references. Published identifiers were checked, but account access and successful integration were not.[1]

The proposed small pass uses 7 API calls, no retries and a USD 1.00 ceiling. The validator suggestion is Python jsonschema 4.26.0, Draft202012Validator.[2] These are new suggestions, not selected settings. Adapter code, schemas and actual inputs/hashes remain unresolved, so the proposal is not execution-ready.

<!-- pagebreak -->

## 3. Case-specific evidence admission

e_B is a registered synthetic control fixture, not a real-world causal finding. Keep the registry separate from case admission. The following are conditions to prepare, not records of admission already performed by an authority.

| Path | Case and basis to prepare before execution |
| --- | --- |
| R1: no evidence; B | K={h_A,h_B}, selected a_B, no admitted evidence and empty applied basis. Registered e_B is still inadmissible in this case |
| R2: full incorporation | e_B admitted and valid for this case; M({e_B})={h_B}. Keep the task request separate from evaluator-only expected values |
| R3: reuse evidence | e_B already admitted and valid before the call. No new observation still permits applied D={e_B} |
| R4: invalid references | Response ID, summary ID, unregistered ID, and registered e_B not admitted for the case. Fix each invalid proposal, hash and origin |
| R5: restart/input changes | Prepare a reference, changed K, response-only change and summary-only change. Preserve state provenance, versions and evidence basis; record actual input differences |

R2 retaining both candidates is an unmet full-incorporation request, not a preservation violation. Do not count fixed R4 replays as observed model behavior. Case-inadmissible e_B is rejected in both comparison stores.

## 4. Proposed calls and replays

| Target | First-pass suggestion; official values remain unset |
| --- | --- |
| R1 / R2 / R3 | One call each, three total. Replay each identical proposal into two independent stores. Do not call the model again for each comparison method |
| R4 | No additional model call. Cover unobserved violation types with fixed invalid proposals: at most four proposals into two stores. Count model-generated and fixed inputs separately |
| R5 | Four calls: reference plus three changes. Score three pairs against the reference. Each uses a fresh process/request. Do not commit read-only assessments as update proposals |
| Total | Seven API calls; no automatic or manual retries. Do not replace failures with successes. Corrections and reruns require a separately frozen form |

Count API calls, store replays and validator operations separately. If every model proposal is valid, retain the null model-output comparison. Fixed replay results do not replace it.

<!-- pagebreak -->

## 5. Pre-execution checks to complete

| Check | Current status / required record |
| --- | --- |
| Freeze official settings | Not done: complete required fields, counts, budget and input/proposal formats; record the form hash and freeze timestamp |
| Admission and interpretation | Not done: bind admission, validity and interpretation rules to case IDs outside the model |
| Schema conformance | Not done: validate schemas and target state, decision, proposal and input data; retain format-checking options |
| Write/expectation separation | Not done: verify one checked write path, independent comparison stores and evaluator expectations excluded from model inputs |
| Restart trace | Not done: link host PID, case, actual read version, state/action/input hashes, request ID, raw output and downstream assessment |

Separate schema/type validation from semantic checks of admission, referenced version and preservation. Do not relabel Demonstration 1 checks as Stage 3 schema validation. Filling every field does not itself pass preparation evaluation.

## 6. Retention, stops and completion

Retain every API request, raw response, malformed output, refusal, timeout, failure and usage record. Include trial/proposal IDs, applied evidence, rule version, before/after states, rejection reasons and timestamps. A future form permitting retries must still preserve the first attempt.

An observed preservation violation on the checked authoritative path, acceptance of case-inadmissible evidence, or authoritative write bypass stops progression on that version. Preserve failure records before linking a correction to a new run ID. Intentionally observed unsupported removal in the unchecked comparison store is a separate comparison result.

Track preparation completion, partner Stage 3 evaluation completion and adoption decisions separately. Partner organization, real workflow, existing method, evaluation window and adoption criteria remain unset until fixed before partner evaluation. They do not have to be selected before this preparation run starts.

## 7. References and files

Official form: stage3-run-form.v0.1.json. Optional suggestion: stage3-first-run-proposal.v0.1.json. The latter is not a result, access grant or authorization to incur spending. Neither file contains credentials.

[1] OpenAI GPT-5.4 Mini model documentation, checked 2026-09-29. Source for published identifiers, reasoning settings and prices. https://developers.openai.com/api/docs/models/gpt-5.4-mini

[2] jsonschema 4.26.0 Schema Validation, checked 2026-09-29. Validator-selection reference; not evidence that validation ran in this environment. https://python-jsonschema.readthedocs.io/en/stable/validate/
