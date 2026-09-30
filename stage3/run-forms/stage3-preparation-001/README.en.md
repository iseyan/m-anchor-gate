# Stage 3 official run form — frozen conditions

Conditions v0.1 / `stage3-preparation-001` / fixed at `2026-09-30T11:21:01+00:00`

The requested model identity/settings, trial counts, spending limit and case-admitted evidence are fixed here. The earlier optional first-run suggestion becomes the selected plan in this new record. Basis commit: `b2bd9d53c0a387df92c5cb9062f8319f0d805832`.

`conditions_frozen=true`; `execution_ready=false`. These selections are final for this conditions version. The live adapter and remaining execution bindings are unfinished; this is not a fully bound executable form or an execution result.

| Item | Fixed value |
| --- | --- |
| Model | OpenAI `gpt-5.4-mini-2026-03-17`; no model fallback |
| API | Responses, `POST https://api.openai.com/v1/responses` |
| Generation | `reasoning.effort=none`; output cap 2,048; input cap 8,192 tokens |
| Format | `text.format.type=json_object`; retain raw output and validate with the pinned host schemas |
| Other settings | `service_tier=default`, `store=false`, `stream=false`, `truncation=disabled`; timeout 120 seconds |
| Deliberately omitted | temperature, top_p, seed and text.verbosity; provider defaults do not imply deterministic output |
| Tools/history | No tools, previous_response_id or conversation; no inherited conversation |
| Trial counts | One small pass: one call each for R1/R2/R3 and four R5 calls; seven generation calls at most |
| Retries | Zero automatic, manual or SDK retries; zero generation probes or JSON-repair calls |
| Spending ceiling | USD 1.00 for this run; no calls or spending to create this form |
| Validator | `jsonschema==4.26.0`, `Draft202012Validator` |

Published model identity and rates were checked on 2026-09-30 against the [official model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini). Account access remains unverified. [Output-format documentation](https://developers.openai.com/api/docs/guides/structured-outputs) defines the selected JSON mode; [Responses documentation](https://developers.openai.com/api/reference/cli/resources/responses/methods/create) defines the standard service tier. JSON mode is not proof of schema conformance.

At standard global input/output rates of USD 0.75/4.50 per million tokens, the configured token caps imply USD 0.01536 per call and USD 0.10752 for seven calls, without a cache discount. This is arithmetic, not incurred cost. Reserve USD 0.02 before each dispatch and include settled costs plus unresolved reservations in the USD 1.00 cap. Unknown usage keeps its reservation and stops further dispatch. Extra account fees or routing surcharges require a revised cost bound before execution. This budget policy is not yet implemented and is not an account-wide billing cap.

| Path | Case | Admitted and valid evidence | New observations |
| --- | --- | --- | --- |
| R1 | `stage3-preparation-001-r1` | None | None |
| R2 | `stage3-preparation-001-r2` | `e_B` | `e_B` |
| R3 | `stage3-preparation-001-r3` | Existing `e_B` | None |
| R4 | `stage3-preparation-001-r4` | None | None |
| R5 reference/action/summary | Same case as R1; changed controls use separate stores | None | None |
| R5 changed K | Same case as R2 | Existing `e_B` | None |

The registry contains e_B for every case; only the listed cases admit it. Interpretation remains `stage3-synthetic-evidence/v0.1`, with `M(empty)={h_A,h_B}` and `M({e_B})={h_B}`. This is a synthetic fixture, not a causal finding. Actions, summaries, model outputs and unregistered IDs do not become evidence. The model cannot change admission or interpretation. Admission is fixed in this document; loading it into a live store has not occurred.

Replay the same raw outputs from R1–R3 into two stores differing only in the removal check: up to six store submissions, not six API calls. R4 supplements categories not attempted by the model with at most four fixed invalid proposals and eight store submissions, counted separately. Complete fixture bytes/hashes must be bound before the first generation call. Fixed replays are neither model behavior nor prompt-injection resistance tests.

R5 reads the actual checked R1/R2 results in fresh processes and links them to four new API calls, giving three comparisons against the reference. If R2 fails full incorporation, retain task failure and the unavailable contrast; do not insert a successful state. Record version/hash changes accompanying a checked action update. Summary-only saving does not advance state version. Record every actual input difference and read-to-request linkage; a model's version claim is insufficient. Details are fixed in `trial-plan.json`.

Schema gate 003 is referenced as received evidence for four fixed schemas and 82 development-instance classification matches: 81 valid and one expected-invalid D10. D11 malformed raw JSON is outside the 14 parsed proposals. No validator rerun was performed for this form, and future model output conformance is not established. Retain the D15 distinction between preservation-legal partial incorporation and an unmet full-incorporation task.

Next bind live code, input templates, concrete R4 fixtures, evaluator and restart/API trace in a separate pre-execution record referencing this form's hash. Do not append completion to this conditions version. Execution requires the full binding and existing entry checks. Changed conditions or retries require a new revision/run ID. Partner-workflow fields may remain unset until partner evaluation.

Creation used zero model calls and zero state-store writes. No GitHub Actions. No edits to 001/002/003, the preparation kit, Bundle, materials ZIP, closed reports or frozen ledger. No Stage 3 completion or Stage 4 entry. Reviews remain advisory and add no approval authority.

`official-run-form.json` is the machine-readable record; `case-admissions.json` and `trial-plan.json` bind evidence and counts/order. Resolve prose discrepancies against these JSON files. `freeze-manifest.json` and `FILES.sha256` identify bytes; they do not prove execution or independent reproduction.
