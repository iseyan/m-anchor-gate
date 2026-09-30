# Record map / 記録対応表

2026-09-30 JST | Repository import guide

## 日本語

このファイルは登録時の案内であり、既存の評価仕様・実行結果・完成確定記録を改訂しない。

| 区別 | 実証1号 | 工程3の固定入力開発点検 | 収集済み提案の再生評価 |
| --- | --- | --- | --- |
| 入力 | 固定した対応・更新提案 | D01〜D15の固定した開発用提案 | 共有会話から転記済みの15提案のJSON部分 |
| 再開時の版 | 主場面は版1・action-001 | 別の入力例で版2・action-002 | PI-05の無更新とPI-09の版1→2を独立したCLIプロセスで確認した記録 |
| 比較 | 証拠なし／証拠あり等の対照 | 除去検査だけを外した比較。D02のみコミット差 | 参照版・ハッシュ・証拠受理・除去検査をまとめて外した比較。除去検査単独の効果ではない |
| 版の進行 | 候補が同じでも、検査済み保存で0→1 | ホストが正式な版と対応IDを生成 | 実質的変更のない提案では版・ハッシュを進めない。PI-09の正当更新で1→2 |
| 部分取り込み | 保存条件に従う | D15は合法。完全取り込みを課題が求めるなら未達と分ける | コアは部分取り込みを許す。PI-09は外部のケース規則で完全取り込みを要求 |
| モデルとの関係 | LLM未使用 | API呼出し0回 | 再生のための追加モデル呼出しなし。元のAPI送受信を認証した記録ではない |

Agents APIアプリの起動・対話確認は、上の三つとも別の記録である。モデル識別子やセッション記録が存在することを、公式の工程3 run formが凍結済みであることや、正本ストアとの自動接続が評価済みであることへ読み替えない。

固定入力開発点検には、元の配布時点の英報がdevelopment-snapshot内に残る。査読対応を短縮して閉じた英報はstage3直下のdevelopment-report.v0.1.en.mdである。原配布物を後から一致させる編集はしていない。

既存資料の相対パス、当時のローカルパス、ハッシュ、時刻は由来の一部として維持する。本リポジトリの起点と読順はルートREADMEを用いる。機械可読データは再整形せず、JSONの改行も保持する。どの経路が現在の製品版であるかという採用判断は、この取り込みでは行わない。

## English

This guide accompanies the repository import. It does not revise an existing evaluation specification, run record or finalization decision.

Demonstration 1's main reader consumed version 1 and action-001. The development check used a separate fixture with version 2 and action-002. The collected-proposal replay has its own cases and records actual CLI-process restarts. These versions are not one continuous state history.

The development comparator disables candidate-removal checking only; D02 is its sole commit difference. The collected-proposal comparator trusts proposed state and reference metadata and omits several checks together. Its difference cannot be attributed to the removal guard alone.

Version rules also differ by recorded adapter. Demonstration 1 increments the version on the checked save even with unchanged candidates. The collected-proposal implementation leaves version and hash unchanged for a no-op proposal. Preserve these as distinct implementations; this import does not silently reconcile them.

D15 in the development record is legal partial incorporation. Failure to satisfy a task requiring full incorporation is a separate assessment. The collected-proposal replay retains the core's partial-incorporation semantics while requiring full incorporation for PI-09 under that case's external policy.

The Agents API startup and interaction record is separate from the three records above. Its model/session identifiers do not freeze the official Stage 3 run form or demonstrate an automatic authoritative-store integration. The raw proposal JSONs preserve copied shared-conversation transcripts, not authenticated original API wire payloads.

The older development report remains inside the unchanged development snapshot. The shortened, closed report is stage3/development-report.v0.1.en.md. Historical paths, timestamps and hashes remain part of their source records; use the root README for the current repository's reading order. No product implementation is selected by this archival import.
