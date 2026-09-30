# schema-gate-003 準備導入確認

**指定版の導入・import・版番号確認は成功した。schema-gate-003 本体は未実行である。**

2026年9月30日、GitHub Actionsの別環境で新規venvを作成し、`jsonschema==4.26.0` を導入した。`Draft202012Validator` のimportと配布版番号の一致を確認した。この記録の exit 0 は準備コマンドの終了値であり、スキーマゲートの合格を示さない。

## 実行の対応

| 項目 | 記録 |
| --- | --- |
| 実行 | [36680116525 / attempt 1](https://github.com/iseyan/m-anchor-gate/actions/runs/36680116525) |
| ソースコミット | `7135d8725dd5b6f12f557284e077cf136e40cfb9` |
| 準備コマンド開始・終了（UTC） | `2026-09-30T06:47:53.313107+00:00` → `2026-09-30T06:47:57.566544+00:00` |
| 別環境 | GitHub-hosted `ubuntu-24.04`、image `20260920.314.1`、新規venv |
| Python | `3.12.14` |
| 検証器 | `jsonschema==4.26.0` / `jsonschema.validators.Draft202012Validator` |
| 準備処理 | venv作成、導入、import・版確認、依存版記録の4コマンドが各 exit 0 |
| 取得成果物 | ID `11081871547`、13ファイル |

Workflow、準備コード、実行前の[対象指定](../../preparation-plan.v0.1.json)は、実行コミットに固定している。実行記録の `GITHUB_SHA` とcheckoutされたコミットは一致する。API応答に基づく実行対応は [github-actions-receipt.json](github-actions-receipt.json)、コマンド・PID・開始終了時刻・終了値は [preparation-result.json](artifact/preparation-result.json) に保持した。

## 確認した範囲

対象は既存の4スキーマ、検証コード、82件の固定入力を収めたファイルである。この6ファイルのSHA-256は事前指定値と一致し、準備処理の前後で変化していない。82件（期待適合81件、期待不適合1件）は保存済み対象の件数確認であり、今回の検証結果ではない。

`check_schema`、インスタンス検証、既存の `validate_schemas.py` は実行していない。スキーマ検証件数は0、インスタンス検証件数は0、モデルAPI呼出しは0、状態ストア書込みは0である。空のstderrを成功根拠にはせず、導入の終了値とimportプローブの実出力・版番号を照合した。

観測された依存版は [requirements-observed.txt](artifact/requirements-observed.txt) に残す。これは実行後の観測値であり、事前にすべての依存版を凍結していたという意味ではない。導入元と配布物のハッシュは [pip-install-report.json](artifact/pip-install-report.json) に残す。

取得したZIPのSHA-256はGitHubの成果物digestと一致した。展開した13ファイルはそのまま保存し、うち12ファイルは成果物内の `SHA256SUMS.txt` と照合した。ハッシュは記録の同一性を確認するもので、スキーマ適合や再現性の証明ではない。ZIP自体はリポジトリへ追加していない。

## 位置づけと次作業

今回解消したのは、別環境で指定検証器を導入・importできるかという準備上の未確認点である。実行環境はジョブ終了後に破棄される。003本体の新しい実行では、導入確認を先に行い、その同じ環境で検証器を呼ぶ必要がある。

003の既存の合格条件は変更しない。

1. 指定版 `jsonschema==4.26.0` / `Draft202012Validator` を使用する。
2. 対象4スキーマの `check_schema` が成功する。
3. 82件の分類が保存済み期待値とすべて一致する。
4. 検証コマンドが exit 0 で終了する。

この準備記録は2～4を評価していない。公式run formは未凍結、`execution_ready=false` のままであり、Stage 3準備評価の完了・Stage 3完了・Stage 4開始を意味しない。

準備ソースコミットは、それ以前の246ファイルを同じGit blobのまま保持している。001・002・確定記録・Bundle・資料集ZIP・閉じた開発報告への変更や追記は行っていない。003本体は別ID・別出力の新記録とする。
