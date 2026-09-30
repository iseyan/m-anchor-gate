# ローカル準備キット v0.1：実行の区切り / Execution boundaries

対象：[schema-gate-003-local-preparation-v0.1.zip](../../distributions/schema-gate-003-local-preparation-v0.1.zip)  
配布コミット：`743679363855d8deff55091627cd47eab6ec4f4d`  
ZIP SHA-256：`d9e2c3647cab4c30bca5704415c2dd80bf709093743855c35570abc15fdec66b`

## 日本語

このZIPはローカル準備キットであり、配布時点ではローカル導入未実施である。GitHub Actions側の導入成功は別経路の記録として扱う。

利用手順の区切りを次のとおり明確にする。

1. キットを展開して準備を実行する。結果は新規の `runs/` 配下に残す。`--inspect-only` の成功は導入成功ではない。
2. 準備結果が `status="installation_and_import_confirmed"`、`installation_confirmed=true`、`exit_code=0` であることを確認する。
3. 次の003本体は、その準備結果の `installed_environment.executable` が指す、**同じvenvのPython**で呼ぶ。準備記録に対応づけた別ID・別出力の検証記録とし、出力先は配布ZIPおよび展開したキットの外に置く。
4. 003の結果をキットへ追記して完成扱いにしない。001・002・Actions準備記録・Bundle・凍結済み資料集・閉じた開発報告にも追記しない。

003の合格条件4項は既存のままである。準備の成功をスキーマ適合やStage 3完了に読み替えない。公式run formは未凍結、`execution_ready=false` を維持する。

査読は参考意見として扱う。実装・ZIPの変更は不要と判断し、同じvenvの使用と出力の分離だけをキット外の利用補足として明記した。この文書による実行結果の追加はない。`schema_gate_003_started=false` のままである。

## English

This ZIP is a local preparation kit. Local installation was unexecuted at distribution time. Installation success recorded through GitHub Actions belongs to a different execution route.

1. Extract the kit and run preparation. Retain each attempt in a new directory under `runs/`. Success with `--inspect-only` is not installation success.
2. Confirm `status="installation_and_import_confirmed"`, `installation_confirmed=true` and `exit_code=0` in the preparation result.
3. Invoke the subsequent schema-gate-003 validation using the Python executable identified by `installed_environment.executable` in that result, within **the same venv**. Give validation a separate ID and output record linked to the preparation attempt. Keep its outputs outside both the distribution ZIP and the extracted kit.
4. Do not append validation results to the kit to imply completion. Do not append them to 001, 002, the Actions preparation record, Bundle, the frozen materials collection or the closed development report.

The four existing schema-gate criteria remain unchanged. Preparation success does not establish schema conformance or Stage 3 completion. The official run form remains unfrozen and `execution_ready=false`.

The review is advisory. No implementation or ZIP revision is needed; this separate usage note clarifies use of the same venv and separation of output records. It adds no execution result. `schema_gate_003_started=false` remains in effect.
