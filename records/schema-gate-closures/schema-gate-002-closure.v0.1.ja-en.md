# schema-gate-002 確定記録 / Closure record

完成稿 v0.1 / Final v0.1 | 2026-09-30 JST

## 日本語

**schema-gate-002を、環境条件未充足による失敗試行の記録としてクローズする。** 文書対応は完了とし、スキーマ適合性は未評価のまま保持する。本文を修正する必要はないと判断した。この別紙は002の実行結果を追加・変更するものではない。

確定対象はコミット [`e48e32471539`](https://github.com/iseyan/m-anchor-gate/commit/e48e32471539d68d892d0b1599bc793344a8b8d5) の [schema-gate-002記録一式](../../stage3/schema-gates/schema-gate-002/)（17ファイル）。本確定記録はそのディレクトリの外に置く。001と002、Bundle 1.0、凍結済み資料集ZIP、閉じた開発報告への追記は行わない。

| 維持する判定 | 内容 |
| --- | --- |
| 002の実行結果 | `blocked_or_failed`、終了コード2、`ModuleNotFoundError` |
| 適合性 | 未評価。4スキーマ・82件を対象としたが、実検証は0件。0/82を不適合率や合格率として扱わない |
| 指定検証器 | `jsonschema==4.26.0`、`jsonschema.Draft202012Validator`、Draft 2020-12 |
| 環境の観測 | この実行環境では指定版を取得できなかった。パッケージの不存在や一般的な配布障害は示さない |
| 実行範囲 | モデル呼出し0、状態ストア書込0。今回の文書対応にも新しい実行結果はない |
| 工程の状態 | 公式run formは未凍結。`execution_ready=false`。準備評価・Stage 3全体は未完、Stage 4は開始しない |

D10の1件は保存済み期待値での不適合期待である。D11の壊れた生JSONを提案14件の分母に含めない説明は、既存対象範囲の説明として残す。002での再検証結果には読み替えない。期待値ファイルは変更しない。空のstderrも成功の根拠にはしない。

001のSHA-256は `b2ed49af861d3c8728939fa021358e5d46ad55a4062e8b88c57f366971715260`、002の結果JSONのSHA-256は `49539ff9b04acc9d743dbd0eb2fcbf268407af17c5de9376c50c392ae79e8eb8`。001は002実行の前後で一致しており、今回も同じ値を確認した。002一式のファイル識別情報は [機械可読確定記録](schema-gate-002-closure.v0.1.json) に収録する。ハッシュは内容の同一性確認に使い、適合性や独立再現の証明にはしない。

Grokの査読は参考意見として検討した。保存された実行結果との整合を確認し、このクローズ判断を記録する。査読者を決裁者とせず、査読から新しい合格条件を追加しない。

### 次の試行

`schema-gate-003` は未開始。指定版を取得できる別環境を用い、導入成功と版を確認してから検証器を呼ぶ。別ID・別出力先を使い、対象ハッシュ、環境、期待値を実行前に記録する。合格条件は既存の次の4項のままとする。

1. 指定検証器 `jsonschema==4.26.0` / `Draft202012Validator` を使う。
2. 対象4スキーマの `check_schema` がすべて通る。
3. 保存済み82件の分類が既存の期待値と一致する。
4. 検証コマンドが終了コード0で終わる。

その合格は、指定スキーマと入力の適合確認に限る。証拠受理、参照版と実状態の対応、保存則、確定経路の検査を代替せず、準備評価全体の完了にも読み替えない。003の結果は新記録へ残し、002へ追記しない。

## English

**Close schema-gate-002 as the record of an unsuccessful attempt caused by an unmet environment prerequisite.** The documentation response is complete; schema conformance remains unevaluated. No revision of the existing report is needed. This separate closure record adds no execution results and changes none.

The closed material is the 17-file [schema-gate-002 record](../../stage3/schema-gates/schema-gate-002/) at commit [`e48e32471539`](https://github.com/iseyan/m-anchor-gate/commit/e48e32471539d68d892d0b1599bc793344a8b8d5). This closure is stored outside that directory. Records 001 and 002, Bundle 1.0, the frozen materials ZIP and the closed development report are not extended.

The retained outcome is `blocked_or_failed`, exit code 2 and `ModuleNotFoundError`. Four schemas and 82 instances were targeted; none was checked. The ratio 0/82 is not a conformance failure rate or a pass rate. The specified validator remains `jsonschema==4.26.0`, `Draft202012Validator`, Draft 2020-12. Acquisition failed in the recorded environment; this does not establish that the package is nonexistent or generally unavailable.

Model calls and state-store writes were both zero. This documentation action adds no validation attempt. The official run form remains unfrozen, `execution_ready=false`, preparation and whole-stage completion remain outstanding, and Stage 4 is not started.

D10 is the one expected-invalid fixture. Excluding D11's malformed raw JSON from the 14 parsed proposals describes the inherited target scope; it is not a new validation result. Saved expectations remain unchanged. Empty stderr is not interpreted as success.

The SHA-256 of record 001 remains `b2ed49af861d3c8728939fa021358e5d46ad55a4062e8b88c57f366971715260`; the SHA-256 of the record 002 result JSON is `49539ff9b04acc9d743dbd0eb2fcbf268407af17c5de9376c50c392ae79e8eb8`. Record 001 matched before and after attempt 002, and its unchanged value was confirmed again for this closure. [The machine-readable closure](schema-gate-002-closure.v0.1.json) identifies all 17 files. Hashes identify bytes and do not establish conformance or independent reproduction.

The user-supplied Grok review was considered as advisory commentary and checked against the stored execution evidence. It creates neither approval authority nor additional acceptance criteria.

### Next attempt

`schema-gate-003` has not started. Use a different environment able to obtain the specified package, confirm successful installation and version before invoking validation, and use a new ID and output path. Fix the target hashes, environment and expectations before execution. The four existing acceptance conditions remain:

1. Use the specified `jsonschema==4.26.0` / `Draft202012Validator`.
2. Pass `check_schema` for all four target schemas.
3. Match the saved expected classifications for all 82 instances.
4. Finish the validation command with exit code 0.

A pass applies only to those schemas and instances. It does not replace evidence-admission checks, actual-state/version correspondence, preservation rules or commit-path checks, and does not complete the preparation evaluation. Record attempt 003 separately; do not append its results to 002.
