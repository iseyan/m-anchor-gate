# 工程3 スキーマゲート新記録 — schema-gate-002

[English](report.en.md)

文書完成稿 v0.1 | 2026-09-30 JST | 実行結果：環境条件未充足、適合判定は未実施

## 結果

**検証コマンドは実行したが、指定検証器を導入できず、スキーマ検証の開始前に停止した。** 終了コードは `2`、結果は `blocked_or_failed`、例外は `ModuleNotFoundError: No module named 'jsonschema'`。対象は4スキーマ・82件の保存済みインスタンスであり、今回の実検証件数はいずれも0である。対象データの不適合を検出した結果ではなく、適合性をまだ判定できていない結果である。

これは新しい実行記録である。前回の `schema-gate-001.json` を成功へ書き換えず、閉じた開発点検報告・仕様・実行票・資料集を変更していない。実行前から存在した227ファイルの前後ハッシュはすべて一致した。

## 検証器と実行環境

| 項目 | 指定・観測内容 |
| --- | --- |
| 記録ID | `schema-gate-002` |
| 基準コミット | [`be9d97a24ea7`](https://github.com/iseyan/m-anchor-gate/commit/be9d97a24ea7b5bbab4800a18af7965b28721d46) |
| 指定検証器 | `jsonschema.Draft202012Validator` |
| 指定パッケージ | `jsonschema==4.26.0` |
| 導入結果 | 未導入。検証器のimportに失敗 |
| 方言 | JSON Schema Draft 2020-12 |
| オプション | 元の検証プログラムの既定値。拡張なし、`format_checker=None`。今回はimport前後の停止により検査処理に到達していない |
| `format` の扱い | 対象4スキーマには `format` キーワードがない。ID等には明示的な `pattern` を使用 |
| 対象内の外部参照 | `$ref` / `$dynamicRef` なし |
| Python | 3.12.14、独立したvenv |
| OS | `Linux-6.18.44-x86_64-with-glibc2.39` |
| 実行開始 | `2026-09-30T14:10:26.795816+09:00` |
| 検証プロセスPID | `7` |
| モデルAPI呼出し／状態ストア書込 | 0回／0回 |

`4.26.0` は前回の検証計画と元プログラムが要求する版を引き継いだ。実行環境に存在した版として記載してはいない。依存パッケージの解決も完了しておらず、環境を完全固定できたとは扱わない。指定版は [requirements.txt](requirements.txt)、実測した環境情報は [environment.json](environment.json) に記録した。

## 対象と実行前の固定

対象は `stage3/development-snapshot/` に保存されたスキーマと固定入力である。Demonstration 1のスキーマや、別系統の収集済み提案再生実装を今回の適合対象に混ぜていない。実行前の [pre-execution.json](pre-execution.json) に、スキーマ・入力・検証プログラムのハッシュ、82件のIDと既存期待値、実行コマンドを記録した。この記録は公式モデル評価のrun formの凍結ではない。

| 対象スキーマ（`stage3/development-snapshot/schemas/`） | SHA-256 |
| --- | --- |
| `decision.schema.json` | `6ed201e6d3e6b731ae861f3ba041415b2f1085f7e6308b71eff4a5303f9fb81d` |
| `input.schema.json` | `a301da3af83adefd8932a4786045351ebf8e3a03a5d1273d3c8a792546afb5d1` |
| `proposal.schema.json` | `e1f4e6ed2143e6691963af81426c8497c492ab6e7b9578bb7d9d37daaf227176` |
| `state.schema.json` | `5da9fc4feb447f6e724c52f2e72e161c4a567671385a6b9845a334615be0a934` |

| インスタンスの種類 | 対象件数 | 既存の適合期待 | 既存の不適合期待 | 今回の実検証 |
| --- | ---: | ---: | ---: | ---: |
| 状態 `state` | 60 | 60 | 0 | 0 |
| 提案 `proposal` | 14 | 13 | 1 | 0 |
| 入力 `input` | 4 | 4 | 0 | 0 |
| 判断 `decision` | 4 | 4 | 0 | 0 |
| 合計 | **82** | **81** | **1** | **0** |

入力一覧は [schema-instances.json](../../development-snapshot/results/dev-001/schema-instances.json)、SHA-256は `146461c25fedd2f2d584c430c6f9e8a83b074f45d4ab31c949755d6c1d8f5f06`。期待値はその保存済みファイルから引き継ぎ、今回の結果に合わせて変更していない。

不適合期待の1件は `D10-proposal` であり、許可されていない `version` と `state_sha256` の追加を含む。`D11` の壊れた生JSONは、元の生成プログラムが解析済み提案として一覧へ含めていないため、提案14件の分母に入らない。D11の前後状態は状態60件の内数である。この扱いは既存入力一覧の範囲説明であり、今回D11の構文検査を再実行したという意味ではない。

## 実行経路と保存結果

1. 独立したvenvの作成は終了コード0で完了した。
2. `pip install --index-url https://pypi.org/simple --only-binary=:all: jsonschema==4.26.0` は終了コード1で失敗した。出力は `No matching distribution found` だった。
3. 取得状況を切り分けるため同環境から `https://pypi.org/simple/jsonschema/` を照会したところ、HTTP 403を受けた。PyPIの公開ページには4.26.0の配布が掲載されているため、「その版が存在しない」とは解釈しない。記録はこの環境からの取得失敗までであり、一般的な配布障害を示さない。
4. 元の [validate_schemas.py](../../development-snapshot/validate_schemas.py) を改変せず、新しい出力先で1回実行した。SHA-256は `d13701ac713323c58b7d809a273f2e2df48f54b24efc24c7460d1b52e2115230`。
5. importで停止し、[schema-gate-002.json](schema-gate-002.json) を生成した。終了コード2、検証済みスキーマ0、検証済みインスタンス0を [execution.json](execution.json) に記録した。

元プログラムの結果と標準出力はそのまま保持した。[stdout.txt](stdout.txt) に結果JSONがあり、[stderr.txt](stderr.txt) は空である。元プログラム自身が例外を結果JSONへ記録しているため、空のstderrを成功の根拠にはしない。環境準備の各試行、標準出力・標準エラー、403の確認は [setup/](setup/) に保存した。失敗した準備試行を削除していない。

## 旧記録の保持と今回の到達点

前回の [schema-gate-001.json](../../development-snapshot/results/dev-001/schema-gate-001.json) のSHA-256は、実行前後とも `b2ed49af861d3c8728939fa021358e5d46ad55a4062e8b88c57f366971715260` だった。今回の `schema-gate-002` は別の試行であり、001の内容・判定を置き換えない。

今回確定したのは、指定検証器、対象4スキーマ、既存82件の期待値、実行環境、取得失敗と検証コマンドの停止結果である。**外部JSON Schema適合は未確認のまま**である。Schemaに適合しても、ケース別の証拠受理、参照版と実状態の一致、保存則、保存経路の検査は別途必要であり、今回それらを追加評価していない。

公式run formは未凍結、`execution_ready=false` を維持する。モデル接続の準備評価・工程3全体の完了・工程4開始へ判定を進めない。ライブ入口への必須Schema検査組込みと実API入力との対応づけ、実ワークフロー比較も、この記録で完了扱いにしない。

## 次の実行

取得可能な環境で指定版を導入し、対象ハッシュと環境・期待値を実行前に記録してから、新しいIDと出力先で再実行する。次が `schema-gate-003` なら、リポジトリ直下から次のコマンドを使える。独立環境のPythonを用い、最初の導入が成功したことを確認してから検証を実行する。

```sh
python -m pip install -r stage3/schema-gates/schema-gate-002/requirements.txt
python stage3/development-snapshot/validate_schemas.py --instances stage3/development-snapshot/results/dev-001/schema-instances.json --report stage3/schema-gates/schema-gate-003/schema-gate-003.json
```

元プログラムは既存の出力ファイルを上書きしない。次回も標準出力・標準エラー・終了コードを別途保存する。合格判定には、指定版で4スキーマの `check_schema` が通り、全82件の判定が既存期待値と一致し、終了コード0になることが必要である。その場合も、記載したスキーマと入力に限定した確認として扱う。スキーマや入力を修正する場合は、対象版と新記録を分ける。

このディレクトリの [SHA256SUMS.txt](SHA256SUMS.txt) は、この新記録のファイルを自身を除いて特定する。ハッシュは内容照合のためのものであり、適合性や再現成功の証明を代替しない。Bundle 1.0・凍結済み資料集ZIP・閉じた報告への追記は行っていない。

## 参照

- [工程3仕様 v0.1.1](../../specification/stage3-integration-evaluation-v0.1.1.ja.md)、§3の検証条件。
- [閉じた開発点検英報](../../development-report.v0.1.en.md)、旧失敗と新記録の分離。
- [jsonschema公式文書：Schema Validation](https://python-jsonschema.readthedocs.io/en/stable/validate/)、`check_schema` と形式検査の指定方法。
- [PyPI：jsonschema 4.26.0](https://pypi.org/project/jsonschema/4.26.0/)、指定版の公開配布情報。外部参照の確認日：2026-09-30 JST。
