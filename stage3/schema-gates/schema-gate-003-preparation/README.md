# Schema gate 003: environment preparation

Installation and import were confirmed in [run 36680116525, attempt 1](https://github.com/iseyan/m-anchor-gate/actions/runs/36680116525).
Reports: [English](results/gha-36680116525-attempt-1/report.en.md) / [日本語](results/gha-36680116525-attempt-1/report.ja.md).
This is preparation only; schema-gate-003 validation remains unstarted.

This directory prepares a separate execution environment for a future `schema-gate-003`.
It contains no schema-gate-003 validation result. Preparation checks install `jsonschema==4.26.0`,
import `Draft202012Validator`, verify its distribution version and retain the observed dependency versions.
The existing four schemas and 82 fixture instances are identified by hashes; they are not validated by this job.

The workflow runs on GitHub-hosted `ubuntu-24.04` with Python 3.12 and a fresh venv.
It has repository read permission only. Results are uploaded under a unique run-ID/attempt artifact name;
they are not committed by the runner. Failed installation and probe outputs are retained.
The runner is ephemeral, so a future validation job must confirm installation again before invoking validation.

The four schema-gate acceptance conditions remain unchanged: the specified validator, four successful
`check_schema` calls, all 82 classifications matching saved expectations, and exit code 0.
Preparation success does not mean those conditions have passed. The official run form remains unfrozen,
`execution_ready=false`, and Stage 3 completion and Stage 4 entry are not claimed.

## 日本語

このディレクトリは、未開始の `schema-gate-003` に向けた別環境の準備用である。
GitHub Actionsの新しい環境で `jsonschema==4.26.0` を導入し、`Draft202012Validator` のimportと版番号を確認する。
対象4スキーマ・82件はハッシュで対応づけるが、この準備ジョブではスキーマ検証を行わない。

実行環境はGitHub-hosted `ubuntu-24.04`、Python 3.12、新規venv。
結果は実行ID・試行番号別の成果物として保持する。実行側にリポジトリ書込権限を与えず、ログを含めた結果を別途記録する。
失敗した導入・importの出力も保持する。実行環境はジョブ終了後に破棄されるため、003本体の実行時にも導入確認を先に行う。

準備確認の成功は003の合格ではない。合格条件4項は変更せず、公式run formは未凍結、`execution_ready=false` を維持する。
001・002・その確定記録・Bundle・凍結済み資料集・閉じた開発報告には追記しない。
