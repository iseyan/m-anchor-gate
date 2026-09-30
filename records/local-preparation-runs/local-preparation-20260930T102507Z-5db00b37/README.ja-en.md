# ローカル準備の受領確認 / Local preparation receipt

Run ID: `local-preparation-20260930T102507Z-5db00b37`  
実行時刻 / Execution: 2026-09-30 19:25:07–19:25:26 JST (10:25:07–10:25:26 UTC)

## 日本語

ユーザーのWindows上で実行した準備記録を受領した。受領記録の判定は `installation_and_import_confirmed`、終了コードは0。Windows 11、Python 3.13.5の新規venvで `jsonschema==4.26.0` と `jsonschema.validators.Draft202012Validator` の読み込みが記録されている。4コマンドはいずれも終了コード0、タイムアウトなし。

`uploaded/` に受領した8ファイルをバイト単位で保存した。内訳はマニフェスト1件と、その掲載ファイル7件。掲載ファイル7件のSHA-256は一致する。マニフェストの残る5件は未添付であり、空ファイルのハッシュが記載されていることだけを確認した。受領したことにせず、空ファイルも再作成しない。マニフェスト自身のハッシュは受領ファイルの特定用であり、独立した照合値ではない。

import出力は結果JSONの環境情報と一致し、freeze出力は依存版一覧と一致する。4スキーマ・82件の固定入力ファイル・検証スクリプトの計6ファイルについて、報告された導入前後のハッシュは、002で固定したリポジトリ内の対象と一致する。先に受領した計画と準備スクリプトも配布版と一致する。

これは準備の成功である。スキーマ検証は0件、003本体は未実行。公式run formは未凍結、`execution_ready=false`、Stage 3未完、Stage 4未開始。001・002・Actions準備記録・配布ZIP・Bundle・凍結資料・閉じた報告は変更しない。

次は `installed_environment.executable` が指す同じvenvで003を呼ぶ。別ID・別出力とし、結果は展開キットの外へ保存する。四つの合格条件は既存のまま。添付の確認はPC上での再実行や、環境全体の独立監査を意味しない。

## English

The user supplied preparation records produced on Windows. They report `installation_and_import_confirmed`, exit code 0, Windows 11 and Python 3.13.5 in a fresh venv, with `jsonschema==4.26.0` and `jsonschema.validators.Draft202012Validator` imported. All four recorded commands exited with code 0 without timeouts.

Eight received files are retained byte-for-byte in `uploaded/`: the manifest and seven listed files. All seven received manifest entries match their SHA-256 values. Five listed files were not uploaded; the manifest declares the empty-file digest for each. They have not been received or recreated. The manifest's own digest identifies the received file and is not an independent expected value.

The import output matches the environment in the result JSON; the freeze output matches the dependency list. The reported before/after hashes for the four schemas, the file containing 82 fixtures and the validator script match the six repository targets fixed for 002. The previously supplied plan and preparation script also match the distributed source.

This confirms preparation as recorded, not schema conformance. Zero schemas or instances were validated; schema-gate-003 remains unexecuted. The official run form is unfrozen, `execution_ready=false`, Stage 3 is incomplete and Stage 4 has not started. Existing frozen records and distributions remain unchanged.

The next validation must use the same venv identified by `installed_environment.executable`, with a separate ID and outputs outside the extracted kit. The existing four acceptance criteria are unchanged. Reviewing uploaded records is not a rerun on the user PC or an independent audit of the entire environment.
