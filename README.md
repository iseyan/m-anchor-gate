# m-anchor-gate

[日本語](README.ja.md)

Implementation records from **Demonstration 1 onward** for a state-preservation principle: selecting an action or producing a summary must not, by itself, eliminate unresolved candidates.

The recorded design separates model proposals from host validation and authoritative storage. The conceptual framework and formal work remain in [m-anchor-framework](https://github.com/iseyan/m-anchor-framework).

## Current scope — 1 October 2026 (JST)

**The official Stage 3 integration evaluation remains stopped and incomplete. Stage 4 has started with a local API prototype, following the user's instruction.** The results and current work are listed below; they are not one combined proof.

| Stage | Result retained | Evidence and limit |
| --- | --- | --- |
| 1 — Formal note | Conditional mathematical result | Preservation under the stated transition assumptions; an empty evidence basis leaves the candidate set unchanged. The [finalized materials](reports/collected-materials/M-Anchor_Stages_1-4_Materials_v0.1.en.pdf) retain this background. |
| 2 — Demonstration 1 | Completed fixed-input demonstration | [Implementation and run](demonstration1/demo1/demo1-implementation-and-run-v0.1.en.md): a fresh process used the saved version, candidates and selected action. No LLM. |
| 3 — Development and schema checks | Fixed-input checks and schema gate 003 completed within their recorded scope | [Development report](stage3/development-report.v0.1.en.md): D02 alone differs under the removal check. [003 receipt report](stage3/schema-gates/schema-gate-003/report.en.md): four schemas checked; 82 classifications matched, including 81 valid instances and D10's expected invalid instance. The receipt is not an independent rerun. Preparation and live integration evaluation remain incomplete. |
| 4 — Productization | Local prototype started / entry conditions unmet | [Scope, code and local instructions](stage4/README.md). The user chose to begin this work while Stage 3 stays incomplete; the old draft's entry conditions are not declared satisfied. Product readiness remains unestablished. |

Start with Demonstration 1 for the observable result. The [English](reports/collected-materials/M-Anchor_Stages_1-4_Materials_v0.1.en.pdf) and [Japanese](reports/collected-materials/M-Anchor_Stages_1-4_Materials_v0.1.ja.pdf) collected PDFs remain historical reading editions, unchanged by this scope decision.

### Where work stops

Current `stage3-preparation-001` retains its total cap of seven API calls. Its input bound of 8,192 tokens is unestablished, so generation does not proceed. Proposed `stage3-preparation-002` remains unadopted and is not an execution path. Neither run is ready; no first counting request is authorized. Conditions and implementation bindings already frozen remain historical records; they do not amount to a fully frozen execution form.

The official Stage 3 live API preparation, count-pricing research, provider inquiry and full run-form freezing remain stopped. Stage 4's local prototype starts separately from that evaluation route. Stopping Stage 3 does not pass an unmet gate or change an earlier result.

The [process appendix](docs/research-scope-and-process-note.ja-en.md) records how preparation and documentation grew beyond the research question. Its cautions remain applicable; its then-unstarted Stage 4 status precedes the [subsequent start decision](stage4/README.md).

## Supporting records

These records remain available for inspection. They are not a queue of work to resume or substitutes for the unfinished official evaluation.

- [Official specification](stage3/specification/stage3-integration-evaluation-v0.1.1.en.md), [run forms and candidate](stage3/run-forms/), [implementation binding](stage3/execution-bindings/), [environment receipt](stage3/environment-checks/) and [pricing review](stage3/pricing-reviews/count-endpoint-pricing-001/README.en.md).
- [Separate collected-proposal replay](stage3/collected-proposals/m-anchor-stage3/evaluation-report.ja.md): 15 proposals; 8 rejected, 4 no-ops, 3 valid updates. These results belong to that replay.
- [Separate Agents API connection record](stage3/collected-proposals/m-anchor-agent/run-report.md): connection and interaction checks, not completion of the official store-integration evaluation.
- [Historical record map](docs/record-map.ja-en.md): explains differences between implementations, comparators and version histories.

## Local reproduction

The [Demonstration 1 README](demonstration1/demo1/README.md) and [separate replay README](stage3/collected-proposals/m-anchor-stage3/README.md) provide their own local instructions. Use a new output directory and preserve the recorded runs. These local reproductions do not require starting the stopped official API route.

## Provenance and limits

Historical specifications, code, run records, failures, receipts, candidate files and finalized materials are retained. New prototype code and its implementation checks are under `stage4/prototype/`; they do not complete Stage 3. Schema gates 001–002 are not rewritten as successes, and 003 is not extended to new code or model outputs.

`provenance/import-manifest.json` and `provenance/SHA256SUMS.txt` describe the original import, including the then-current root READMEs. They do not describe every later addition or the revised navigation. The [pre-revision snapshot](https://github.com/iseyan/m-anchor-gate/tree/64d8280203d4d8f38d6fda816c8e39ed482e367a) retains those README bytes. Git history records subsequent changes. Checksums identify bytes; they do not prove an authenticated API exchange or independent reproduction.

The evidence here does not establish model understanding, the truth of evidence, general authorization security, prompt-injection resistance, accident prevention or product effectiveness.
