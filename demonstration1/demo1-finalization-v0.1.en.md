# Demonstration 1 v0.1: finalization record

2026-09-29 JST / completed fixed-input execution record

Demonstration 1 v0.1 is finalized as a completed record of preservation, rejection, use after restart and the evidence-bearing control under its declared state contract. The governing specifications, code, observed logs and implementation/run reports remain unchanged. Extensions and subsequent runs receive separate versions and records.

The primary decision remains “a_B was selected; causes A/B remain unresolved.” The established result is that externally stored candidate distinctions were used as decision inputs in a separate process after normal termination. The existing record of nine original tests, six additional tests and four passing acceptance criteria supports this finalization. No additional model experiment or test rerun was performed to finalize the record.

No LLM was used. Model understanding, performance gains from M-Anchor instructions and general prompt-injection resistance were not measured. e_B is a preregistered control fixture. Concurrency, actual crash recovery, resistance to privileged direct writes and full schema conformance using an external validator remain unverified.

## Materials available for independent comparison

The governing text and source hash list are already in the distributed ZIP. A reviewer receiving only the standalone implementation report cannot inspect those sources, so the finalized handoff provides the complete set.

| Material | Path within the demonstration folder |
| --- | --- |
| Governing scope, both languages | `specs/M-Anchor_Demo1_Scope_and_Success_Criteria_v0.1.{ja,en}.md` |
| Scenario, both languages | `specs/demo1-scenario-v0.1.{ja,en}.md` |
| Executed-source hashes | `results/observed-2026-09-29/source-hashes.json` |
| State, proposal, audit and decision records | `results/observed-2026-09-29/records.jsonl` |
| Acceptance and process records | `acceptance.json` and `process-lifecycle.json` in the same folder |
| Original distribution file hashes | `SHA256SUMS.txt` |

The original archive is `M-Anchor_Demo1_v0.1.zip`, SHA-256 `3ce69bb44803846edf0c0de4c27edb33443a3bbb2aac6e1d186eb8d93783602b`. The executed-source hash-list SHA-256 is `ec9ffeefbd9fea4c8b08b22ea4c4863e052a05cc0478f2c5c5421d50429b111c`.

The new handoff includes all 29 original files at their original relative paths with unchanged bytes. Finalization records, a comparison script and the Stage 3 specification are separate additions. The script checks the original file manifest, executed-source hashes and the governing hashes quoted in the scenario sheets. This permits independent recalculation of consistency; it does not establish authenticity of the original execution or constitute an independent reproduction.

## Stage numbering and handoff

Stage 2 in the published roadmap is the minimal executable example, Demonstration 1; that scope is now complete. The separate working sequence of scenario definition, implementation and testing uses different numbering from the roadmap. Roadmap Stage 3 is integration evaluation with a partner organization. The attached Stage 3 specification is an unexecuted plan. Demonstration 1's result is not reclassified as an enterprise or LLM evaluation result.
