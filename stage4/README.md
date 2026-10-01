# Stage 4 — local API prototype

Started 1 October 2026 (JST), following the user's instruction to begin Stage 4 while keeping Stage 3 incomplete. English first; Japanese follows.

## Purpose and decision

Make the preservation mechanism usable from another local process: read state, submit a JSON proposal, retrieve the outcome and audit, and read the saved distinction after restart. This first prototype uses the two-candidate demonstration and synthetic evidence `e_B`.

Stage 3's official integration evaluation remains incomplete and stopped. Its completion is not a prerequisite for this prototype work. The older productization plan and entry-form template are historical drafts; their entry conditions have not been declared satisfied. This starts productization work, not deployment or a claim of product readiness. Demand, paying users and real workflow effectiveness remain undecided.

The prototype is separate from the app and public-game projects. No live model connection, provider inquiry, token-counting request or GitHub Actions run is part of this start.

## Run locally

Python 3.10 or later and the standard library are sufficient. Keep the repository layout: the prototype imports the unchanged guard from `demonstration1/demo1/m_anchor_minimal.py`.

### Windows launcher

Download and extract the complete repository ZIP, then double-click [`run-demo.cmd`](run-demo.cmd) inside `stage4`. The launcher uses an already installed Python 3.10 or later; it does not install packages or contact a provider. The CMD entry point has been checked in the limited Windows environment described below; Explorer double-click execution remains unverified.

The fixed local demo runs four examples: provisional B with a fresh-process read, unsupported removal rejected, a changed summary that leaves the assessment unchanged, and an update using host-admitted synthetic evidence. Every run creates a new `run-output/stage4-demo-...` folder. Open its `summary.txt` for the short result. The same folder retains the two stores, proposal files, command output and `demo-result.json`. Expected rejection is a normal example outcome; an unexpected failure is retained and stops the demo without retry.

On any supported Python environment, the same runner can be started with:

```sh
python stage4/prototype/run_demo.py
```

### Individual commands

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

The nine tests (seven API checks and two runner checks) at `d4f8c29` passed locally on Python 3.12.14 / Linux on 1 October 2026. The runner checks include a path with Japanese characters, spaces and an exclamation mark.

On the same date, Windows 11 (build 26200) with Codex's bundled Python 3.12.14 exposed two test-cleanup errors: test-owned SQLite connections remained open. The tests now close those connections explicitly, preserving commit/rollback behavior, and all nine tests passed in that Windows environment. The prototype, guard and demo code are unchanged; the earlier Linux result is not a rerun of this test correction.

The complete fixed-commit ZIP at `d4f8c29` was also extracted and its unchanged `stage4/run-demo.cmd` invoked through `cmd.exe`. Only that process's `PATH` was prepended with the bundled Python directory, and standard input was redirected from `NUL` for the final pause. The generated `summary.txt` and `demo-result.json` showed all four examples completed: ten steps exited 0, the intended rejection exited 2, and the launcher exited 0. Saved state, version and action survived rejection and summary replacement, and the fresh-process read matched the saved state/action. Ordinary installed-Python and Explorer double-click execution remain unverified. These checks complete neither Stage 3 nor Stage 4 and do not establish product readiness.

The tests use disposable stores to check candidate preservation, admitted evidence, invalid proposal recording, state references, summary separation, fresh-process reads, rollback on an audit-write error and protection against overwriting unrelated stores. They are implementation checks for this prototype, not Stage 3 evaluation results. Existing records and the published guard are unchanged.

## 日本語

**工程3を未完のまま、工程4のローカル共通API試作を開始した。** 2026年10月1日の利用者の指示に基づく。旧計画の「工程3完了後」という順序を、この試作の開始条件にはしない。旧計画・入口フォームは当時の草稿として保持し、入口条件を満たしたことにはしない。製品化の作業開始であり、提供可能・需要あり・有効性確認済みという判定ではない。

最初の用途は、他のローカルプロセスからJSON提案を提出し、保存状態・検査結果・監査を取得できることとする。実証1号の二候補と合成証拠 `e_B` に範囲を絞る。別途のアプリや公開ゲームとは統合しない。

Windows向けには、リポジトリのZIP全体を展開し、`stage4` 内の [`run-demo.cmd`](run-demo.cmd) をダブルクリックする起動方法を用意した。既存のPython 3.10以降を使い、追加インストールやプロバイダ通信は行わない。CMDからの起動は後述する限定したWindows環境で確認した。エクスプローラーでのダブルクリック実行は未確認である。

実演は、暫定対応Bの保存と別プロセス読出し、根拠なし削除の拒否、要約変更後の判定維持、受理済み合成証拠による更新の4例。毎回、新しい `run-output/stage4-demo-...` フォルダを作る。その中の `summary.txt` で短い結果を読める。ストア・提案ファイル・コマンド出力・`demo-result.json` も同じフォルダに残る。意図した拒否は正常な実演結果であり、想定外の失敗では記録を残して再試行せず停止する。

上のコマンドをリポジトリ直下で実行する。Python 3.10以降の標準ライブラリだけを使い、既存の保存則コードを未改変で読み込む。新しい保存先を指定すること。最初の例は、暫定対応Bを保存しても両候補が残り、別プロセスの `assess` が版1を読んで判断する流れである。`template` は固定の提案例を作る機能であり、モデル生成ではない。別途得たJSON提案も提出できるが、その出所を認証する機能ではない。

証拠対照を試す場合は、別ストアを `init demo-local --admit e_B` で作る。そのストアから作った提案の `evidence_ids` を `["e_B"]`、`proposed_K` を `["h_B"]` に変更して提出する。初期化で受理していないケースでは拒否する。受理資格と解釈を提案から書き換える入口は設けない。

検査済み保存は状態・対応・監査をまとめて確定し、候補が同じでも版を進める。拒否では状態と対応を維持し、生の提案バイトを監査に残す。要約保存と読出しだけでは版を進めない。部分取り込みの保存合法性は、完全取り込みを求める課題の達成と分ける。候補枯渇も通常の未決と分ける。

HTTPサーバー、モデル接続、計数API、実世界への行為は実装しない。証拠の真偽、特権的な直接書込、製品向け権限管理、並行負荷、クラッシュ復旧は未評価である。003をこの新コードのスキーマ適合へ読み替えない。

2026年10月1日、`d4f8c29` の9件（APIの7件と実演スクリプトの2件）の検査がPython 3.12.14／Linuxで通過した。日本語・空白・感嘆符を含む保存先も含めた。

同日、Windows 11（ビルド26200）とCodex同梱のPython 3.12.14では、テスト側で開いたSQLite接続が閉じられていないため、後片付けで2件のエラーが出た。確定・ロールバックの動作を維持して接続を明示的に閉じるようテストを修正し、このWindows環境で9件すべてが通過した。試作本体・保存則・実演コードは未改変であり、先のLinux結果は今回のテスト修正後の再実行ではない。

また、固定コミット `d4f8c29` のリポジトリ全体ZIPを展開し、未改変の `stage4/run-demo.cmd` を `cmd.exe` から実行した。そのプロセスだけの `PATH` の先頭に同梱Pythonの場所を加え、末尾の一時停止には `NUL` から標準入力を渡した。生成された `summary.txt` と `demo-result.json` で4例の完了を確認した。10ステップは終了コード0、予定された拒否は2、起動ファイル全体は0だった。拒否と要約変更で保存状態・版・対応は維持され、別プロセスの読出しも保存状態・対応と一致した。通常インストールされたPythonによる実演と、エクスプローラーでのダブルクリック実行は未確認である。これらの確認を工程3完了・工程4完了・製品提供可能とは扱わない。

検査は上記の `unittest` コマンドで、使い捨ての保存先に対して行う。監査書込エラー時の一括ロールバックも確認する。この試作の実装確認として扱い、Stage 3の完了記録には加算しない。今後の注意は既存の[補遺](../docs/research-scope-and-process-note.ja-en.md)を引き継ぎ、追加の閉鎖文書は作らない。
