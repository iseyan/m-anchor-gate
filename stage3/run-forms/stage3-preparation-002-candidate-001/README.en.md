# Stage 3 conditions revision candidate 002

**Proposed new run ID: `stage3-preparation-002`. Not adopted, frozen or executed.**

`adopted=false`, `conditions_frozen=false`, `implementation_binding_frozen=false`, `execution_ready=false`.

This candidate retains seven generation trials and proposes at most one separate count request per trial. It materializes the revised form, proposed case admissions and trial plan under a new namespace, with a cost review and implementation-binding plan. Existing context 002 is unchanged. This candidate does not approve fourteen calls.

## Proposed change

| Item | Current run 001 | Proposed run 002 |
|---|---|---|
| Generation | At most seven | At most seven, same trials |
| Separate counting | No additional slots | At most one per trial, seven total |
| All API requests | At most seven | Fourteen proposed |
| Retries, fallback, extra generations | Zero | Zero |
| Spending limit | USD 1 | USD 1 retained |
| Count cost bound | Unresolved | Unresolved, `null` |
| Freeze and execution | As historically recorded | Neither performed |

Generation IDs remain P001–P003 and A001–A004. Proposed count IDs are `C-P001`, etc. Endpoint counts remain separate while sharing an aggregate cap and budget. A timeout or uncertain delivery consumes its reserved attempt; there is no recount or replacement. Failed or over-8,192 counts stop before generation. Caps are not completion quotas.

The R1–R5 questions, model/settings, evidence semantics, matched proposal replays, and D15 legality/task distinction are inherited. New case IDs change state and input hashes, so old initial inputs and R4 hashes cannot be carried forward as new-run artifacts.

## Cost review

`pricing-bound.review.json` records the review time in UTC. The [model documentation](https://developers.openai.com/api/docs/models/gpt-5.4-mini) lists standard input USD 0.75 and output USD 4.50 per million tokens for the pinned `gpt-5.4-mini-2026-03-17`, consistent with the earlier conditions.

Conditional on input/output caps of 8,192/2,048, generation arithmetic is USD 0.01536 per call and USD 0.10752 for seven. Existing generation reservations of USD 0.02 per call total USD 0.14.

The reviewed [pricing page](https://developers.openai.com/api/docs/pricing), [counting guide](https://developers.openai.com/api/docs/guides/token-counting) and [endpoint reference](https://developers.openai.com/api/reference/typescript/resources/responses/subresources/input_tokens/methods/count) did not establish a count-endpoint cost bound in this review. General Responses pricing does not justify assuming that counting is free or billed as generation input.

If `c` is an independently supported upper reservation per count attempt, budget feasibility requires:

```text
0.14 + 7 × c ≤ 1.00
```

This expression does not establish `c`. The count bound, count reservation and combined bound remain `null`. **Unknown count pricing blocks the first count request.** If billing depends on input size, the cost bound must also cover requests whose count exceeds 8,192, before that count is known. Applicable error and timeout billing must be addressed. A provider-question draft is included in JSON; it has not been sent.

## Implementation-binding plan

`implementation-binding.plan.json` links the old source hashes to required changes. It is a plan, with no new live runtime code or runtime manifest.

1. Bind the adopted new form, admissions and trials in a new implementation directory. Do not overwrite the old contract pins.
2. Keep endpoint-specific attempt/reservation accounting and enforce both aggregate caps and the unchanged USD 1 budget.
3. Verify host count-exchange provenance, raw bytes, adopted method hash and all case/version/read/request links. An `origin` string is insufficient.
4. In each fresh R5 process, read the authoritative store, fix request bytes, count, verify, then generate using those identical bytes. Handoff remains case ID and store path only.
5. Regenerate initial state/input and R4 bytes/hashes for new case IDs before execution. Old 69/68 checks and schema gate 003 do not verify the new code.

The candidate guard and checked commit route remain the inherited core. No claim is extended to real evidence truth, general authorization or prompt-injection resistance.

## Contents and limits

| File | Role |
|---|---|
| `run-form.candidate.json` | Unadopted conditions revision |
| `case-admissions.candidate.json` | Proposed admissions for new case IDs |
| `trial-plan.candidate.json` | Seven generations and up to seven paired counts |
| `pricing-bound.review.json` | Published rates, conditional arithmetic, unresolved count costs |
| `implementation-binding.plan.json` | Source references and planned implementation changes |
| `change-register.json` | Complete JSON Pointer differences from the old conditions |
| `verify_candidate.py` / `verification.json` | Local reference, difference and inheritance checks |

The planned output directory is `C:\Users\ise\Desktop\m-anchor-gate-executions\stage3\runs\stage3-preparation-002`. It has not been created or checked on the operator's machine. There are no new-run initial states or live outputs.

The consistency check is neither external JSON Schema validation nor token counting. Preserve all earlier failures and successes, conditions, binding 001, context 002, 001–003, Bundle, collected materials and ZIPs.

Our engineering judgment is that separating count and generation accounting makes the added traffic and costs traceable. The unresolved cost bound and unimplemented binding prevent freezing these conditions. Reviewer comments remain advisory and do not make the adoption decision.

The next concrete missing item is **pricing evidence for the count endpoint**. Adoption, supported costs and a checked new implementation must precede a separate execution-start record. This work made zero generation calls, zero count calls and zero authoritative-state writes; Stage 3 preparation remains incomplete.
