# m-anchor-gate

[English](README.md)

**実証1号以降の、外部状態の検査・永続保存・実装記録を保存するリポジトリ。**

モデルは提案し、ホスト側が検査して保存する。候補集合、選択した対応、採用済み証拠、要約を区別し、提案された遷移を正式な状態ストアへ保存する前に検査する。

概念体系と理論の展開は既存の [m-anchor-framework](https://github.com/iseyan/m-anchor-framework) に置く。本リポジトリは実装とその記録を扱う。各実装が引き継いだ最小Pythonコアは、当時の実装に必要な場所で保持する。

## 記録ごとの位置づけ

| 記録 | 参照先 | 記録上の到達点 |
| --- | --- | --- |
| 実証1号 | [完成確定記録](demonstration1/demo1-finalization-v0.1.ja.md)、[実装・試験記録](demonstration1/demo1/demo1-implementation-and-run-v0.1.ja.md) | 固定入力の実証完了。LLM未使用。記録された実行で四つの受入条件を通過。 |
| 工程3の固定入力開発点検 | [完成英報](stage3/development-report.v0.1.en.md)、[原配布物](stage3/development-snapshot/) | 検査側は受理4・拒否11。比較差はD02のみ。この記録のモデルAPI呼出しは0回。 |
| 収集済み提案の再生評価 | [評価報告](stage3/collected-proposals/m-anchor-stage3/evaluation-report.ja.md)、[コードと記録](stage3/collected-proposals/m-anchor-stage3/) | 別系統の15提案を再生。拒否8・無更新4・正当更新3。不正な確定0、正当更新の誤拒否0という既存記録。 |
| Agents API接続確認 | [実行記録](stage3/collected-proposals/m-anchor-agent/run-report.md)、[アプリ](stage3/collected-proposals/m-anchor-agent/) | API起動、対話、逐次受信、保存済み応答の復元を記録。正式状態ストアとの自動連携とは分ける。 |
| 工程3の公式評価経路 | [仕様v0.1.1](stage3/specification/stage3-integration-evaluation-v0.1.1.ja.md)、[実行フォーム](stage3/run-forms/) | 準備評価と工程全体の完了は別判定。収録した公式票は未凍結。準備票はexecution_ready=false。 |
| 工程4 | [計画草稿](stage4/stage4-productization-plan-v0.1.ja.md)、[入口フォーム](stage4/stage4-productization-entry-form.v0.1.json) | 計画草稿／入口未確認。この計画に基づく実装は未開始、execution_ready=false。 |

各行は収録記録ごとの到達点であり、合算した実験結果ではない。二つの工程3比較と版の扱いの違いは、[記録対応表](docs/record-map.ja-en.md)に示す。

## 構成

- `demonstration1/`：実証1号の原コード、Schema、SQLite状態、監査ログ、完成確定記録。
- `stage3/development-snapshot/`：固定入力開発点検の原配布物。schema-gate-001と失敗入力を含む。
- `stage3/specification/`、`stage3/run-forms/`：確定した評価仕様と未凍結の実行票。
- `stage3/collected-proposals/m-anchor-stage3/`：別系統の決定論的再生実装、正式15提案の原JSON、除外入力、実行済み結果。
- `stage3/collected-proposals/m-anchor-agent/`：別途記録されたAPIアプリと接続確認報告。
- `stage4/`：製品化検討の計画草稿と未記入の開始確認票。
- `reports/collected-materials/`：工程1〜4の英日完成稿PDF。工程1の既刊部分は、確定済み合本内の背景資料として保持する。
- `records/materials-finalization/`：資料集の別紙確定記録。原ZIPやBundle 1.0の中へ追加しない。
- `provenance/`：取り込み元とのファイル対応とチェックサム。

## 完成稿PDF

- [英語正本・83頁](reports/collected-materials/M-Anchor_Stages_1-4_Materials_v0.1.en.pdf)
- [日本語副本・81頁](reports/collected-materials/M-Anchor_Stages_1-4_Materials_v0.1.ja.pdf)

合本PDFは、凍結した資料集合の状態を記載している。収集済み提案の再生評価とAPI接続確認は、今回同じリポジトリに置く別の記録であり、凍結済み台帳を遡って書き換えない。

## ローカルでの利用

二つのローカル再生実装はPython標準ライブラリを使う。それぞれのREADMEと環境条件に従う。リポジトリ直下からの次の例は、既存結果とは別の出力先を指定する。

```sh
# 実証1号
cd demonstration1/demo1
python run_demo.py --output-dir ../../run-output/demo1-new
cd ../..

# 別系統の収集済み提案の再生
cd stage3/collected-proposals/m-anchor-stage3
python -X utf8 replay.py evaluate --out ../../../run-output/collected-replay-new
python -X utf8 restart_check.py --out ../../../run-output/collected-restart-new
cd ../../..
```

実行ごとに新しい出力先を選ぶ。APIアプリの依存パッケージと認証設定は別であり、上記コマンドからは起動しない。この取り込みにAPIキーやローカルの環境ファイルは含めない。

## 由来と範囲

`provenance/import-manifest.json` は、引き継いだ全ファイルを元のZIP内パスまたは確定済み個別ファイルとSHA-256で対応づける。`provenance/SHA256SUMS.txt` は自身を除く収録物を対象とする。記録のバイト列を維持するため、Gitによる改行変換を無効にしている。

今回の取り込みでは、実験の再実行、モデル提案の再生成、未通過のスキーマゲートの合格化、公式run formの凍結、工程4の開始を行わない。失敗、除外試行、無更新、正当更新の既存記録を保持する。ハッシュはバイト列の特定用であり、元のAPI送受信の認証や独立再現の証明にはしない。

schema-gate-001は固定入力開発点検の失敗記録である。別系統の再生評価で検査が通っても、この失敗や仕様v0.1.1の全入口条件を置き換えない。次のスキーマゲート、公式run form、工程4開始判断は、それぞれ別記録に残す。
