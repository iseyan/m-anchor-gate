# schema-gate-001／002 取りまとめ / Status summary

v0.1 | 2026-09-30 JST  
参照コミット / Source commit: `4f27fde082e56920f7e86e40d5486cfd28b73348`

## 日本語

**001と002は、検証器を利用できなかった試行の記録として一旦閉じる。適合性は未評価のまま保持する。** この取りまとめは新しい実行記録ではなく、過去の失敗を合格へ変更するものでもない。

| 試行 | 記録日（JST） | 保存された結果 | スキーマ適合性 |
| --- | --- | --- | --- |
| [schema-gate-001](../../stage3/development-snapshot/results/dev-001/schema-gate-001.json) | 2026-09-29 | `blocked_or_failed`、`ModuleNotFoundError: No module named 'jsonschema'` | 未評価 |
| [schema-gate-002](../../stage3/schema-gates/schema-gate-002/report.ja.md) | 2026-09-30 | 指定検証器の取得に失敗。検証コマンドは同例外で停止、exit 2 | 未評価 |

両記録とも、スキーマとインスタンスの検証結果は空である。対象は4スキーマ・82件だが、実検証0件を不適合率・合格率として読まない。002の取得失敗は記録された環境での観測であり、指定版の不存在を意味しない。

001の結果ファイルと、[002の確定記録](../schema-gate-closures/schema-gate-002-closure.v0.1.ja-en.md)が識別する17ファイルは、保存済みハッシュと一致した。結果JSONのSHA-256は次のとおり。

- 001：`b2ed49af861d3c8728939fa021358e5d46ad55a4062e8b88c57f366971715260`
- 002：`49539ff9b04acc9d743dbd0eb2fcbf268407af17c5de9376c50c392ae79e8eb8`

ハッシュはファイルの同一性の確認用であり、適合性や再現性の証明ではない。

### 次の003との区切り

その後の[Actions準備記録](../../stage3/schema-gates/schema-gate-003-preparation/results/gha-36680116525-attempt-1/report.ja.md)は、その別環境での導入・import確認に限る。[ローカル準備キット](../../distributions/schema-gate-003-local-preparation-v0.1.zip)は配布時点で導入未実施であり、両者を001／002の成功や003の合格へ読み替えない。

次の003は、ローカル準備が成功した**同じvenv**で、別ID・別出力として実行する。出力はキットの外に置き、[利用補足](../local-preparation-notes/schema-gate-003-local-kit-v0.1.ja-en.md)に従って準備記録と対応づける。既存の合格条件4項は変更しない。

この取りまとめ時点では `schema_gate_003_started=false`、公式run formは未凍結、`execution_ready=false`。新たな導入・検証結果の追加はなく、Stage 3完了・Stage 4開始には進めない。

本書は既存記録の外に置く。001／002、Actions準備記録、ローカルZIP、Bundle、凍結済み資料集、閉じた開発報告には追記しない。査読は参考意見として扱い、決裁権限や合格条件を追加しない。

## English

**Close the documentation work on 001 and 002 for now, retaining them as attempts blocked by an unavailable validator. Schema conformance remains unevaluated.** This summary adds no execution result and does not replace either failed attempt with a pass.

Record 001, dated 29 September 2026 JST, retains `blocked_or_failed` and `ModuleNotFoundError: No module named 'jsonschema'`. Record 002, dated 30 September, retains unsuccessful acquisition of the specified validator, the same import error and validation-command exit 2.

Both records contain empty schema and instance results. The target is four schemas and 82 instances; zero checked instances is neither a failure rate nor a pass rate. Acquisition failure was observed in the recorded environment and does not establish that the specified package version does not exist.

Record 001 and the 17 files identified by the existing 002 closure match their saved hashes. The two result-JSON hashes are listed above. They identify file contents and do not establish conformance or reproducibility.

Later Actions preparation confirms installation and import only in that separate environment. The local preparation kit was distributed without a local installation run. Neither record changes 001 or 002, nor establishes a schema-gate-003 pass.

For the next validation, use the **same venv** that passed local preparation, assign a separate ID and output, and keep validation outputs outside the kit. Link them to the preparation record as specified in the separate usage note. The four existing gate criteria remain unchanged.

At this summary, `schema_gate_003_started=false`; the official run form remains unfrozen and `execution_ready=false`. No new installation or validation result is added, and neither Stage 3 completion nor Stage 4 entry is claimed.

This summary is outside all existing records. It does not modify or extend 001, 002, Actions preparation, the local ZIP, Bundle, frozen materials or the closed development report. Review comments remain advisory and add neither approval authority nor acceptance criteria.
