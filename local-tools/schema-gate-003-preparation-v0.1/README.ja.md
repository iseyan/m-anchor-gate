# 準備導入確認：ローカル実行版 v0.1

GitHub Actionsを使わず、手元のPythonで `jsonschema==4.26.0` の導入と `Draft202012Validator` のimport・版番号を確認する実行一式。
Git、GitHubアカウント、APIキーは不要。指定パッケージと依存パッケージの取得にはPyPIへの接続が必要である。

## Windowsでの実行

ZIP全体を任意の書込可能なフォルダへ展開し、`run-preparation.cmd` をダブルクリックする。Python 3.13と `py` ランチャーを使う。

ターミナルから実行する場合は、展開先で次を実行する。

```powershell
py -3.13 prepare_local.py
```

`py` がない場合は、導入済みのPython 3.10以上で `python prepare_local.py` を実行する。macOS/Linuxでは `python3 prepare_local.py` を使う。

## 何を行うか

1. 同梱した4スキーマ・既存検証コード・82件の固定入力ファイルのSHA-256を確認する。
2. `environments/` の下に、今回専用のvenvを作る。既存のPython環境へパッケージを追加しない。
3. `jsonschema==4.26.0` を導入し、importと版番号を確認する。
4. 観測した依存版、各コマンド、標準出力・標準エラー、終了値を保存する。

結果は `runs/local-preparation-日時-ID/` に保存される。成功時の `preparation-result.json` は、`status="installation_and_import_confirmed"`、`installation_confirmed=true`、`exit_code=0` となる。
失敗時も別フォルダに記録を残す。再実行は新規IDで行い、以前の結果を上書きしない。空のstderrだけを成功の根拠にしない。

## 範囲

このローカル版での導入実行は、配布時点では未実施である。既存の別環境での成功記録を、手元のPCでの成功に読み替えない。

本スクリプトは準備確認だけを行う。`check_schema`、82件のスキーマ分類、モデルAPI呼出し、状態ストアへの書込みは行わない。82件中81件が期待適合、1件が期待不適合という値は保存済み期待値の内訳であり、今回の検証結果ではない。

003本体の合格条件は、指定検証器、4スキーマの `check_schema` 成功、82件の分類一致、検証コマンドのexit 0の4項のまま。この準備のexit 0を003本体の合格にはしない。公式run formは未凍結、`execution_ready=false`。Stage 3完了・Stage 4開始には進めない。

001・002・既存の準備記録・Bundle・資料集ZIP・閉じた開発報告は同梱せず、変更しない。同梱対象は既存ソースの同一バイトのコピーで、対応は `preparation-plan.json` に残す。

対象ファイルの確認だけを行う場合は、次の任意コマンドを使う。このモードはパッケージを導入せず、成功しても `installation_confirmed=false` である。

```powershell
py -3.13 prepare_local.py --inspect-only
```
