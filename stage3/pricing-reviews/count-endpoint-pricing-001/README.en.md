# Count-endpoint pricing review 001

**Finding: the inspected official sources did not establish a per-request cost upper bound for counting.** The candidate remains unadopted. Both current run 001 and proposed run 002 remain `execution_ready=false`.

Checked at 2026-09-30T16:24:55.322271+00:00 (UTC). Target: `POST https://api.openai.com/v1/responses/input_tokens`, pinned model `gpt-5.4-mini-2026-03-17`. This record covers pricing evidence only.

## Sources and limits

| Official source | Observation |
|---|---|
| [Counting guide](https://developers.openai.com/api/docs/guides/token-counting) | Explains pre-generation counting and request-formatting tokens; no applicable count charge established. |
| [Count API reference](https://developers.openai.com/api/reference/typescript/resources/responses/subresources/input_tokens/methods/count) | Defines request and response fields; returned `input_tokens` does not establish billed quantity. |
| [General pricing](https://developers.openai.com/api/docs/pricing) | Gives general API pricing and model rates; this review could not establish billed quantity or a bound for count requests. |
| [Count resource](https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens) | Redirect target of the old platform URL; part of the same reference family, not independent pricing evidence. |
| [Changelog](https://developers.openai.com/api/docs/changelog) | Neither `input_tokens` nor `token count` matched the retrieved text; no pricing basis obtained. |
| [Usage reference](https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage) | Describes aggregate usage fields; no endpoint-specific billing basis established. |

[pricing-evidence.json](pricing-evidence.json) records source URLs, queries and observations. This bounded review does not prove that pricing information does not exist. Account-specific terms and bills were not accessed.

## Disposition

No free-count assumption or substitution of generation input rates is made. A returned count alone does not establish billing quantity. The inherited expression `0.14 + 7c <= 1.00` tests budget feasibility; it does not determine `c`. Count pricing basis, per-attempt bound, reservation and combined bound remain `null`. No first count request may be dispatched without the required bound.

Current `stage3-preparation-001` retains its total cap of seven calls. Its 8,192-token input bound is still unestablished, so generation does not proceed. Proposed `stage3-preparation-002` remains unadopted, unfrozen and unexecuted. Its candidate folder is not an execution path for 001.

Grok's review is advisory. The author's judgment is that these sources cannot support a pre-dispatch cost bound, so execution conditions remain unchanged.

## Work and preservation

Only public pricing research and this separate record were produced: zero experimental generation calls, count calls and authoritative state writes. No provider inquiry was sent. No live code, runtime check or GitHub Actions run was performed.

The baseline is commit `0e07c135202114191cc873f14825c344a00b3b0b`. All 417 existing files are retained; only this folder is added. Records 001–003, the condition form, binding 001, environment receipt, candidate, Bundle, materials and closed reports remain unchanged. Old case IDs, R4 hashes and 69/68/003 results are not transferred as validation of a new run.

The next evidence remains the applicable count-endpoint pricing terms already required by the candidate: quantity dependence, over-8,192 inputs, errors, timeouts and uncertain delivery, sufficient to establish a pre-dispatch bound. No acceptance condition is added. Later evidence belongs in a new record.

`FILES.sha256` identifies these three record files; it does not authenticate provider pages or prove runtime reproducibility.

