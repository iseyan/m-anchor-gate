# M-Anchor Stage 3 Adapter development v0.1

文書改訂1（2026-09-29 JST、Grok査読反映）。固定入力の開発点検記録です。Stage 3準備評価は未完了、モデル統合評価は未実施です。実行票はexecution_ready=falseです。

Documentation revision 1 (2026-09-29 JST, incorporating the supplied Grok review). This records fixed-input development checks. Stage 3 preparation evaluation is incomplete; model-integration evaluation has not been performed. The run form remains execution_ready=false.

固定入力の開発試験：15条件×2ストア、別プロセス読出し4条件。モデルAPI呼出し0回。Stage 3本試験ではありません。

Fixed-input development checks: 15 conditions into two stores; four fresh-process reads; zero model API calls. Not a Stage 3 evaluation run.

## 内容 / Contents

- adapter.py：ローカル構造検査、ケース・版・ハッシュ・証拠受理と保存の検査。Local shape, case/version/hash/admission and persistence checks.
- m_anchor_minimal.py：実証1号から無変更で継承した保存則。Unchanged preservation guard from Demonstration 1.
- schemas/：4種類の未検証Schema。Four schemas pending external validation.
- fixtures/・evaluator/：実行前に固定した入力と独立した期待値。Fixed development inputs and separate expectations.
- results/dev-001/：今回の実測記録。Observed development records, including the blocked schema gate.
- development-report.v0.1.ja.md・en.md：英日報告。Bilingual reports.
- review-response-001.ja-en.md：査読への対応、未達項目と原記録保持。Review response, remaining entry conditions and preservation of original records.
- stage3-prepared-run-form.v0.1.json：判明した準備項目を反映した将来用実行票。Partially prepared future run form; not execution-ready.
- references/：基準となる仕様確定稿v0.1.1。Final specification reference.

## 再現 / Reproduction

Python 3.10以降で、展開したディレクトリから実行します。既存の結果ディレクトリは上書きできません。

Use Python 3.10+ from the extracted directory. Existing result directories are never overwritten.

```bash
python3 run_development.py --output results/dev-002
```

外部Schema検証器は今回の環境では導入できませんでした。許可された検証環境で導入した後、別名の結果ファイルへ検証記録を作成します。下のコマンドが成功したことは本記録では主張していません。

The external validator could not be installed here. In an environment where it is available, retain a new report without replacing the blocked one. Success of the commands below is not claimed by this record.

```bash
python3 -m pip install -r requirements.txt
python3 validate_schemas.py --instances results/dev-001/schema-instances.json --report results/dev-001/schema-gate-002.json
```

検証対象は列挙したSchema・器具に限ります。実モデル出力の入口へ外部検証器を組み込み、実行フォームを固定する作業が別途必要です。この版にはモデルAPI接続口がありません。未採用のモデルや予算を採用済みとはしません。

Validation covers the listed schemas and fixture instances only. Mandatory validation of actual model outputs and a frozen live run form are still required. This build has no model API entry point and adopts no suggested model or budget.

## 完了の範囲 / Completion boundary

開発試験の通過、Stage 3準備評価の完了、企業側でのStage 3評価完了、採用・有効性は別です。現状は最初の開発確認のみを記録しています。

Passing development checks, completing Stage 3 preparation, completing partner evaluation and demonstrating adoption/effectiveness are distinct. Only the first is recorded here.

次は外部Schemaゲートの通過と公式フォームの凍結です。実モデル入口への検証器組込みと実API入力への結合も未完了です。schema-gate-001.jsonは保持し、再試行は別記録へ残します。現状から工程4へは進みません。

Next are the external schema gate and freezing the official form. Runtime validation at the live-model entry and actual API-input linkage also remain incomplete. Keep schema-gate-001.json and record retries separately. This state does not advance to Stage 4.
