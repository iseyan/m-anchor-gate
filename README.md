# m-anchor-gate

[日本語](README.ja.md)

Deterministic state gate for AI-generated proposals, with implementation code, evaluation records, and reproducible tests. Model proposes; deterministic layer commits.

This repository preserves implementation records from **Demonstration 1 onward**.

**Model proposes; the host validates and commits.** Candidate sets, selected actions, admitted evidence and summaries remain distinct. The implementations check proposed transitions before they reach the authoritative store.

The conceptual framework and its theoretical development remain in [m-anchor-framework](https://github.com/iseyan/m-anchor-framework). This repository records the implementation work and its evidence. The inherited minimal Python core is retained where the recorded implementations require it.

## Read the records separately

| Record | Location | Recorded status |
| --- | --- | --- |
| Demonstration 1 | [Finalization](demonstration1/demo1-finalization-v0.1.en.md), [implementation and run](demonstration1/demo1/demo1-implementation-and-run-v0.1.en.md) | Completed fixed-input demonstration. No LLM; four acceptance conditions passed in the recorded run. |
| Stage 3 fixed-input development checks | [Closed report](stage3/development-report.v0.1.en.md), [original snapshot](stage3/development-snapshot/) | Checked path: 4 accepted, 11 rejected. D02 alone differs from the comparator. Model API calls in this record: 0. |
| Collected-proposal replay | [Report](stage3/collected-proposals/m-anchor-stage3/evaluation-report.ja.md), [code and records](stage3/collected-proposals/m-anchor-stage3/) | Separate replay of 15 collected proposals: 8 rejected, 4 no-ops, 3 valid updates. Recorded unauthorized commits: 0; valid updates blocked: 0. |
| Agents API connection check | [Run report](stage3/collected-proposals/m-anchor-agent/run-report.md), [application](stage3/collected-proposals/m-anchor-agent/) | API startup, interaction, streaming and saved-response recovery were recorded. This is separate from automatic integration with an authoritative state store. |
| Official Stage 3 evaluation route | [Specification v0.1.1](stage3/specification/stage3-integration-evaluation-v0.1.1.en.md), [run forms](stage3/run-forms/) | Preparation and whole-stage completion remain separate decisions. The imported official forms are not frozen; the prepared form has `execution_ready=false`. |
| Stage 4 | [Draft plan](stage4/stage4-productization-plan-v0.1.en.md), [entry form](stage4/stage4-productization-entry-form.v0.1.json) | Draft plan, entry unconfirmed, implementation not started under this plan; `execution_ready=false`. |

These are the statuses in the imported records, not a combined experimental result. See the [record map](docs/record-map.ja-en.md) for the differences between the two Stage 3 comparisons and their version rules.

## Repository layout

- `demonstration1/`: original fixed-input demonstration, source code, schemas, SQLite state, audit logs and finalization records.
- `stage3/development-snapshot/`: original development distribution, including `schema-gate-001.json` and failed inputs.
- `stage3/specification/`, `stage3/run-forms/`: frozen evaluation specification and unfrozen execution forms.
- `stage3/collected-proposals/m-anchor-stage3/`: separate deterministic replay implementation, the 15 original proposal JSONs, excluded input, and saved results.
- `stage3/collected-proposals/m-anchor-agent/`: the separately recorded API application and connection report.
- `stage4/`: draft productization plan and unfilled entry form.
- `reports/collected-materials/`: final English and Japanese reading editions of the Stages 1-4 collection. Their Stage 1 material is retained as background within those already finalized PDFs.
- `records/materials-finalization/`: the separate collection finalization record; it is not inserted into the original ZIP or Bundle 1.0.
- `provenance/`: file-by-file import mapping and checksums.

## Read the completed materials

- [English main edition, 83 pages](reports/collected-materials/M-Anchor_Stages_1-4_Materials_v0.1.en.pdf)
- [Japanese companion edition, 81 pages](reports/collected-materials/M-Anchor_Stages_1-4_Materials_v0.1.ja.pdf)

The reading editions describe their frozen source collection. The collected-proposal replay and API connection records above are separate records now stored alongside it; importing them here does not retrospectively rewrite the frozen ledger.

## Local use

The two local replay implementations use the Python standard library. Follow each implementation's own README and environment requirements. From the repository root, the following commands use a new output directory and leave the recorded runs intact:

```sh
# Demonstration 1
cd demonstration1/demo1
python run_demo.py --output-dir ../../run-output/demo1-new
cd ../..

# Separate collected-proposal replay
cd stage3/collected-proposals/m-anchor-stage3
python -X utf8 replay.py evaluate --out ../../../run-output/collected-replay-new
python -X utf8 restart_check.py --out ../../../run-output/collected-restart-new
cd ../../..
```

Choose a fresh output directory for each run. The API application has separate dependencies and credential requirements; it is not invoked by the commands above. No API key or local environment file is part of this import.

## Provenance and scope

`provenance/import-manifest.json` maps every inherited file to its source archive member or standalone finalized file, with SHA-256. `provenance/SHA256SUMS.txt` covers the repository payload except itself. Git attributes disable line-ending conversion to preserve recorded bytes.

This repository import does not rerun experiments, regenerate model proposals, pass the blocked schema gate, freeze the official run form, or start Stage 4. Earlier failures, excluded trials, no-op results and legitimate updates remain in the record. Checksums identify bytes; they do not authenticate an original model API exchange or constitute an independent reproduction.

The preserved `schema-gate-001` failure belongs to the fixed-input development route. The separate replay's passing checks do not replace it or establish compliance with every entry condition of specification v0.1.1. Future schema-gate results, official run forms and Stage 4 entry decisions require separate records.
