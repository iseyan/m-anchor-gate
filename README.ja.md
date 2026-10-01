# m-anchor-gate

[English](README.md)

**実証1号以降の、状態保存原理の実装と記録。** 対応の選択や要約の生成だけを理由に、未決の候補を消さないことを扱う。

記録した設計では、モデルの提案、ホストの検査、正本ストアへの保存を分ける。概念体系と形式的な展開は [m-anchor-framework](https://github.com/iseyan/m-anchor-framework) に置く。

## 現在の範囲 — 2026年10月1日（日本時間）

**公式のStage 3統合評価は、未完のまま停止を維持する。Stage 4は利用者の指示により、ローカル共通APIの試作から開始した。** 成果と現在の作業は次のとおりであり、一本の証明には束ねない。

| 工程 | 保持する成果 | 根拠と範囲 |
| --- | --- | --- |
| 1 — 形式ノート | 条件付きの数学的結果 | 明示した遷移の仮定の下での保存則。証拠の基底が空なら候補集合は変わらない。[確定済み資料集](reports/collected-materials/M-Anchor_Stages_1-4_Materials_v0.1.ja.pdf)に背景資料を収録。 |
| 2 — 実証1号 | 固定入力の実証完了 | [実装・試験記録](demonstration1/demo1/demo1-implementation-and-run-v0.1.ja.md)：別プロセスが保存版・候補・選択対応を読んで判断に使った。LLM未使用。 |
| 3 — 開発・スキーマ点検 | 記録された範囲で固定入力点検とスキーマゲート003を完了 | [開発報告](stage3/development-report.v0.1.en.md)：除去検査による差はD02のみ。[003受領報告](stage3/schema-gates/schema-gate-003/report.ja.md)：4スキーマを検査、82件の分類一致（81件適合・D10は期待不適合）。受領照合であり独立再実行ではない。準備評価とライブ統合評価は未完。 |
| 4 — 製品化 | ローカル試作を開始／入口条件は未充足 | [範囲・コード・実行手順](stage4/README.md)。工程3を未完のまま開始する利用者の判断に基づく。旧草稿の入口条件を満たしたとは扱わず、製品提供可能かは未判定。 |

観測された結果を読む入口は実証1号とする。[英語正本](reports/collected-materials/M-Anchor_Stages_1-4_Materials_v0.1.en.pdf)・[日本語副本](reports/collected-materials/M-Anchor_Stages_1-4_Materials_v0.1.ja.pdf)の資料集PDFは、当時の状態を記した資料として保持し、今回の方針変更で改訂しない。

### 今回の停止線

現行 `stage3-preparation-001` のAPI総枠は7のまま。入力8,192トークン以下の根拠は未確立なので、生成しない。`stage3-preparation-002` は未採用の候補として残し、実行パスにしない。両方とも実行準備未完であり、最初の計数要求も出さない。条件版・実装結び付け版の既存の凍結は保持するが、公式実行フォーム全体の凍結とはしない。

公式Stage 3経路のライブAPI準備、計数料金の調査、プロバイダ照会、公式フォーム全体の凍結は停止を維持する。Stage 4のローカル試作は、この評価経路と分けて開始する。工程3の停止によって未達の条件を合格にしたり、過去の結果を変更したりはしない。

準備と文書が研究の問いを超えて増えた経緯は[補遺](docs/research-scope-and-process-note.ja-en.md)に残す。その注意事項は引き継ぐ。補遺の「工程4未開始」は当時の状態であり、その後の[開始判断](stage4/README.md)と区別する。

## 補助資料

以下は照合のために保持する記録である。再開すべき作業の一覧でも、未完の公式評価を代替する成果でもない。

- [公式仕様](stage3/specification/stage3-integration-evaluation-v0.1.1.ja.md)、[実行フォームと候補](stage3/run-forms/)、[実装結び付け](stage3/execution-bindings/)、[環境受領](stage3/environment-checks/)、[料金レビュー](stage3/pricing-reviews/count-endpoint-pricing-001/README.ja.md)。
- [別系統の収集済み提案再生](stage3/collected-proposals/m-anchor-stage3/evaluation-report.ja.md)：15提案、拒否8・無更新4・正当更新3。その再生実行の結果として保持する。
- [別系統のAgents API接続記録](stage3/collected-proposals/m-anchor-agent/run-report.md)：接続・対話等の確認であり、公式経路の正本ストア統合評価の完了ではない。
- [登録時の記録対応表](docs/record-map.ja-en.md)：実装・比較器・版履歴の違いを説明する当時の案内。

## ローカルでの再現

[実証1号のREADME](demonstration1/demo1/README.ja.md)と[別系統の再生README](stage3/collected-proposals/m-anchor-stage3/README.md)に、それぞれの手順がある。出力先を新規にし、保存済みの実行記録を維持する。これらのローカル再現に、停止した公式API経路の開始は必要ない。

## 由来と限界

過去の仕様、コード、実行記録、失敗、受領、候補、完成資料は保持する。新しい試作コードと実装検査は `stage4/prototype/` に置き、Stage 3の完了には加算しない。スキーマゲート001・002を合格へ書き換えず、003を新コードやモデル出力に拡張しない。

`provenance/import-manifest.json` と `provenance/SHA256SUMS.txt` は、当時のルートREADMEを含む元の取り込みを記録する。後日の全追加物や現在の案内を覆うものではない。[今回の改訂前スナップショット](https://github.com/iseyan/m-anchor-gate/tree/64d8280203d4d8f38d6fda816c8e39ed482e367a)には、そのREADMEのバイト列が残る。後続の変更はGit履歴で確認できる。ハッシュはバイト列の特定用であり、元のAPI送受信の認証や独立再現の証明ではない。

ここにある根拠は、モデルの理解、証拠の真偽、権限一般、プロンプトインジェクション耐性、事故防止、製品の有効性を保証しない。
