# Stage 4 — local API prototype

Started 1 October 2026 (JST), following the user's instruction to begin Stage 4 while keeping Stage 3 incomplete. English first; Japanese follows.

## Purpose and decision

Make the preservation mechanism usable from another local process: read state, submit a JSON proposal, retrieve the outcome and audit, and read the saved distinction after restart. This first prototype uses the two-candidate demonstration and synthetic evidence `e_B`.

Stage 3's official integration evaluation remains incomplete and stopped. Its completion is not a prerequisite for this prototype work. The older productization plan and entry-form template are historical drafts; their entry conditions have not been declared satisfied. This starts productization work, not deployment or a claim of product readiness. Demand, paying users and real workflow effectiveness remain undecided.

The prototype is separate from the app and public-game projects. No live model connection, provider inquiry, token-counting request or GitHub Actions run is part of this start.

## Run locally

Python 3.10 or later and the standard library are sufficient. Keep the repository layout: the prototype imports the unchanged guard from `demonstration1/demo1/m_anchor_minimal.py`.

Run these commands from the repository root. Choose unused database and proposal paths. `init` and `template --output` refuse to overwrite an existing file.

```sh
python stage4/prototype/cli.py --db run-output/stage4-demo.sqlite3 init demo-local
python stage4/prototype/cli.py --db run-output/stage4-demo.sqlite3 template demo-local --output run-output/stage4-proposal.json
python stage4/prototype/cli.py --db run-output/stage4-demo.sqlite3 submit demo-local --file run-output/stage4-proposal.json
python stage4/prototype/cli.py --db run-output/stage4-demo.sqlite3 assess demo-local
python stage4/prototype/cli.py --db run-output/stage4-demo.sqlite3 audit demo-local
```

The template selects provisional action B and retains both candidates. After submission, the stored version is 1. The later `assess` process reads that version and returns that action B was selected while causes A/B remain unresolved. The template is deterministic local data; it is not model output. External proposal files can be submitted through the same command, without authenticating their stated model origin.

To exercise the synthetic evidence control, initialize a separate store with `init demo-local --admit e_B`. In its new proposal template, set `evidence_ids` to `["e_B"]` and `proposed_K` to `["h_B"]`, then submit it. Without admission at initialization, the same evidence request is rejected. Admission and interpretation are host setup, not proposal fields.

## Interface

| Operation | Python method | CLI |
| --- | --- | --- |
| Create a new case store | `GateAPI.initialize(path, case_id, admitted_evidence=())` | `init CASE [--admit e_B]` |
| Read state and its related records | `GateAPI(path).read(case_id)` | `read CASE` |
| Submit original proposal bytes | `submit(case_id, raw_bytes)` | `submit CASE --file proposal.json` |
| Save an untrusted summary | `save_summary(case_id, text)` | `summary CASE --text TEXT` |
| Retrieve the audit history | `history(case_id)` | `audit CASE` |
| Use saved candidates and action | `assess(case_id)` | `assess CASE` |

Every CLI command takes `--db PATH` before the operation. Output is UTF-8 JSON. Successful commands exit 0; a recorded proposal rejection exits 2; a store/file error exits 1. Invalid command syntax also exits 2. `template` creates a starting proposal from the current state, with a fresh proposal ID and its actual version/hash.

Proposal fields are exactly `proposal_id`, `case_id`, `expected_version`, `expected_state_sha256`, `proposed_K`, `selected_action`, `evidence_ids`, and `reason`. Candidate IDs are `h_A`, `h_B`; actions are `a_A`, `a_B`. The only evidence fixture is `e_B`, interpreted as permitting `h_B` when admitted for that case.

A checked save commits state, action and audit together and advances the version, including when candidates are unchanged. Rejections preserve state and action and retain the submitted bytes in the audit. Summaries and reads do not advance the state version. Partial incorporation remains legal under the guard; this prototype does not score whether a separate task demanded full incorporation. An empty candidate set is distinct from ordinary uncertainty.

This is a local Python/CLI interface with one case per SQLite store. It has no HTTP server, model credentials or real-world action execution. Evidence truth, privileged direct file writes, production access control, concurrent workloads and crash recovery have not been evaluated. Gate 003 does not establish schema conformance of this new prototype.

## Checks

```sh
python -B -m unittest discover -s stage4/prototype/tests -v
```

The seven tests passed locally on Python 3.12.14 / Linux on 1 October 2026. The five commands above also ran successfully with a new temporary store. Windows execution of this prototype has not been checked.

The tests use disposable stores to check candidate preservation, admitted evidence, invalid proposal recording, state references, summary separation, fresh-process reads, rollback on an audit-write error and protection against overwriting unrelated stores. They are implementation checks for this prototype, not Stage 3 evaluation results. Existing records and the published guard are unchanged.

## 日本語

**工程3を未完のまま、工程4のローカル共通API試作を開始した。** 2026年10月1日の利用者の指示に基づく。旧計画の「工程3完了後」という順序を、この試作の開始条件にはしない。旧計画・入口フォームは当時の草稿として保持し、入口条件を満たしたことにはしない。製品化の作業開始であり、提供可能・需要あり・有効性確認済みという判定ではない。

最初の用途は、他のローカルプロセスからJSON提案を提出し、保存状態・検査結果・監査を取得できることとする。実証1号の二候補と合成証拠 `e_B` に範囲を絞る。別途のアプリや公開ゲームとは統合しない。

上のコマンドをリポジトリ直下で実行する。Python 3.10以降の標準ライブラリだけを使い、既存の保存則コードを未改変で読み込む。新しい保存先を指定すること。最初の例は、暫定対応Bを保存しても両候補が残り、別プロセスの `assess` が版1を読んで判断する流れである。`template` は固定の提案例を作る機能であり、モデル生成ではない。別途得たJSON提案も提出できるが、その出所を認証する機能ではない。

証拠対照を試す場合は、別ストアを `init demo-local --admit e_B` で作る。そのストアから作った提案の `evidence_ids` を `["e_B"]`、`proposed_K` を `["h_B"]` に変更して提出する。初期化で受理していないケースでは拒否する。受理資格と解釈を提案から書き換える入口は設けない。

検査済み保存は状態・対応・監査をまとめて確定し、候補が同じでも版を進める。拒否では状態と対応を維持し、生の提案バイトを監査に残す。要約保存と読出しだけでは版を進めない。部分取り込みの保存合法性は、完全取り込みを求める課題の達成と分ける。候補枯渇も通常の未決と分ける。

HTTPサーバー、モデル接続、計数API、実世界への行為は実装しない。証拠の真偽、特権的な直接書込、製品向け権限管理、並行負荷、クラッシュ復旧は未評価である。003をこの新コードのスキーマ適合へ読み替えない。

2026年10月1日、Python 3.12.14／Linuxで7件の実装検査が通過した。掲載した5コマンドも新規の一時ストアで確認した。この試作のWindows実行は未確認である。

検査は上記の `unittest` コマンドで、使い捨ての保存先に対して行う。監査書込エラー時の一括ロールバックも確認する。この試作の実装確認として扱い、Stage 3の完了記録には加算しない。今後の注意は既存の[補遺](../docs/research-scope-and-process-note.ja-en.md)を引き継ぎ、追加の閉鎖文書は作らない。
