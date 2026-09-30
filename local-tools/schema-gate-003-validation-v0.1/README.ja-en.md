# schema-gate-003 ローカル実行用 / Local validation launcher v0.1

状態：実行用ファイルの作成のみ。003の実行結果ではない。

## 日本語

対象は `local-preparation-20260930T102507Z-5db00b37` で導入が確認されたWindows環境。GitHub Actionsは使用しない。

1. `run-schema-gate-003.cmd` と `run_schema_gate_003.py` を同じフォルダー（例：デスクトップ）に保存する。
2. 展開済みの `C:\Users\ise\Desktop\schema-gate-003-local-preparation-v0.1` は移動せず、`run-schema-gate-003.cmd` をダブルクリックする。
3. 結果フォルダーが開いたら、新しくできたZIPを添付する。失敗時も同じ記録を残す。

既存の準備結果のハッシュ、同じvenv、固定6ファイルのハッシュを確認した後、未改変の `validate_schemas.py` を呼ぶ。`-I -B -X utf8` で環境を隔離し、バイトコード書き込みを抑止し、UTF-8で入出力する。導入やモデル呼び出しは行わない。

四つの既存条件（指定版、4スキーマのcheck_schema、82件の期待分類一致、検証コマンドexit 0）をそのまま記録する。前提となる環境・対象の確認を、この四項の変更とは扱わない。

出力はキットの外にある `C:\Users\ise\Desktop\schema-gate-003-results` の新しいIDのフォルダーとZIP。既存結果を上書きせず、実行前記録・実コマンド・PID・stdout/stderr・検証器の原出力・判定・SHA-256を保存する。中断や失敗も保持する。ZIPは提出を簡単にするための担体であり、それ自体が再現証明ではない。

作成環境では構文と固定パス・ハッシュの整合を確認した。Windows上でのランチャー実行および003検証は未実施。最初の実行結果はユーザーのPC上で作成される。合格してもStage 3全体の完了とはせず、公式run formは未凍結、`execution_ready=false` を維持する。

## English

Status: launcher preparation only; this is not a schema-gate-003 execution record.

This launcher is linked to the Windows venv confirmed by `local-preparation-20260930T102507Z-5db00b37`. Save the CMD and Python files together, keep the extracted preparation kit at its recorded location, and double-click the CMD file. Submit the new output ZIP, including any failed attempt.

It verifies the linked preparation record, the same venv and the six fixed source hashes before invoking the unchanged `validate_schemas.py`. The Python switches `-I -B -X utf8` isolate execution, suppress bytecode writes and select UTF-8. It performs no installation or model call and uses no GitHub Actions.

The four existing acceptance criteria remain unchanged: the specified validator version, four successful check_schema calls, all 82 saved classifications matched, and validation command exit 0. Environment and source checks establish the inputs to that validation.

Each attempt receives a new ID and an output directory and ZIP under `C:\Users\ise\Desktop\schema-gate-003-results`, outside the preparation kit. The launcher retains the pre-execution record, actual command, PID, stdout/stderr, original validator output, assessment and hashes. Earlier outputs are not replaced. The ZIP is a submission container, not a reproducibility proof.

Authoring checks cover syntax and consistency of pinned paths and hashes. The Windows launcher and schema-gate-003 have not been executed by the authoring environment. Passing the listed schema gate will not complete Stage 3; the official run form remains unfrozen and `execution_ready=false`.
