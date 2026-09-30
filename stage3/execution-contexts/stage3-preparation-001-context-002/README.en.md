# Stage 3 pre-execution linkage record 002

**Not executed. `execution_ready=false`. The token-counting method is an unadopted candidate; preparation remains incomplete.**

This separate record links the accepted Windows environment receipt to the frozen code, rechecks published generation prices, and selects an absolute output-path plan. It does not amend the conditions, implementation binding or accepted receipt.

## Status

| Item | Recorded status |
|---|---|
| New code under the specified validator | The received Windows execution passed 68 checks. That item remains closed for that execution; no rerun |
| Input cap of 8,192 tokens | Candidate method and request linkage specified; no observed count or verified bound issued |
| Environment | Same received venv, Python, validator and source hashes linked |
| Prices | Published rates rechecked; account access and future billing unverified |
| Storage | An absolute path outside the source kit selected as a plan; local existence, write access and absence of prior outputs unverified |
| Calls | Zero generation calls, zero counting calls, zero extra generations; no GitHub Actions |

## Method and call accounting

The official [token-counting guide](https://developers.openai.com/api/docs/guides/token-counting) describes pre-generation counting that includes request-structure tokens. We have not established a supported offline bound for this complete pinned-model request. Visible-text counts or byte lengths with an undocumented allowance do not supply that evidence.

The frozen form specifies `maximum_total_api_calls=7`, and all seven slots are planned generations. Seven additional counts would make fourteen requests. The current cap cannot silently be reinterpreted as a generation-only cap.

`token-method.candidate.json` makes the alternative reviewable: keep seven generations; allow at most one separate count attempt per trial, seven in total; use a combined cap of fourteen only under a separate conditions revision and run binding. Retries, fallback and extra generations stay at zero. Failed counts consume their attempt. The USD 1 budget stays unchanged; count pricing and its cost bound are unresolved, and are not assumed to be zero. **This alternative is not adopted or authorized by this record.** Keeping the current total-seven condition leaves the token gate open.

## Exact request linkage

Save and hash the full generation-request bytes before counting. Link the trial, case, state version/hash and actual read to both the count request and its raw response.

| Copy unchanged to the count request | Retain only in the generation request |
|---|---|
| `model`, `instructions`, `input`, `reasoning`, `text`, `tools`, `tool_choice`, `truncation` | `max_output_tokens`, `store`, `stream`, `service_tier` |

This is a design derived from the fixed request and the published [count parameter reference](https://developers.openai.com/api/reference/typescript/resources/responses/subresources/input_tokens/methods/count). Unknown fields stop processing. Account/snapshot compatibility has not been exercised.

If separately adopted, the host must retain the authenticated count exchange, validate the result and its origin, require a nonnegative integer at most 8,192, and compare the complete generation-request hash immediately before dispatch. Any request change invalidates the bound and stops the run. R5 requires the actual resumed authoritative read; the comparison store is not a model-input source.

`request-linkage-review.json` projects seven existing, unsent fixture requests from the received ZIP. It records byte hashes and lengths, with every token count and bound set to `null`. These are not new live inputs, a rerun of the 68 checks, or a rerun of schema gate 003's 82 classifications. Neither fixture `usage.input_tokens=900` nor a documentation example is used as token evidence.

Merely supplying the fields accepted by the existing live preflight does not verify a count's origin. Adoption needs a separately bound host implementation that verifies the underlying receipt and linkage. No live sending function is added here.

## Environment, prices and storage

The accepted receipt is `environment-check-20260930T143626Z-f7a97493`: Windows 11, Python 3.13.5, `jsonschema==4.26.0`, `Draft202012Validator`. The exact executable/venv and the 44-file source manifest are linked in `execution-context.record.json`. This record does not newly observe the operator's current process or disk.

The pinned snapshot remains `gpt-5.4-mini-2026-03-17`. The reviewed [model page](https://developers.openai.com/api/docs/models/gpt-5.4-mini) lists standard input USD 0.75 and output USD 4.50 per million tokens, matching the conditions. At the conditional input/output caps of 8,192/2,048, generation arithmetic is USD 0.01536 per call and USD 0.10752 for seven. This does not establish an all-in cost including counts. The documentation check time is recorded in JSON; prices must be rechecked at actual start.

The selected physical root is:

```text
C:\Users\ise\Desktop\m-anchor-gate-executions
```

The frozen logical directory `stage3/runs/stage3-preparation-001/` maps beneath that root. JSON lists absolute plans for authoritative and comparison stores, restart controls, one shared journal, host records and `run-start.json`. No directory or store has been created. At start, resolve and check the paths and create new outputs exclusively; existing outputs stop the run without deletion or overwrite.

A new actual-start record must bind the then-current environment, prices, output paths and adopted token method. If count accounting is revised, its new conditions/run ID need a new linkage; these planned paths must not silently become that revised run's paths.

## Preservation and next decision

Only this new folder is added. Preserve 001–003, frozen conditions/binding, all failures, the accepted receipt, Bundle, collected materials and existing ZIPs. Hashes identify bytes and link records; they do not prove independent reproduction or privileged-write resistance. Evaluation contracts, including D15's distinction between preservation legality and task fulfillment, remain unchanged. Reviewer comments are advisory.

The remaining choice is whether to prepare a separate accounting revision allowing up to seven count requests while keeping seven generations. Even adoption would lead first to the conditions, pricing and implementation binding work, not immediate API execution.

`verify_record.py` performs a local, read-only consistency check of references, received request linkage, arithmetic and path mapping. It does not call a network service, install a validator, validate schemas or write state. A successful `verification.json` concerns this record only; it does not close the token or preparation gate.
