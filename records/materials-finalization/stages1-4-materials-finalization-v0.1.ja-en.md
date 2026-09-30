# 工程1〜4 資料一式 v0.1 — 編集確定記録

2026-09-30 JST | Finalized collection / 資料集として確定・凍結

`M-Anchor_Stages_1-4_Materials_v0.1.zip` を工程1〜4の資料一式の完成稿として確定する。表紙の「Stages 1–4 materials」と、中の「Progress ledger / 到達点 v0.1」を維持する。確定対象は資料集と台帳であり、工程1〜4全体の実行完了ではない。

| 工程 | 凍結時点の位置づけ |
| --- | --- |
| 1 | 通常遷移の仮定の下でのMECCの同値条件と、空の適用証拠基底による恒等保存の紙上証明 |
| 2 | 宣言された条件下での固定入力の実証完了 |
| 3 | 固定入力の開発点検済み。準備評価・モデル接続評価は未完 |
| 4 | 計画草稿／入口未凍結。実装未開始、`execution_ready=false` |

この状態表示は、本資料集に収録した記録の範囲に適用する。工程2の版1・`action-001` と、工程3の開発点検の版2・`action-002` は、READMEの読順で対応づけた別の実行記録である。

編集判断として、根拠と到達点を工程ごとに区別できているため、一式資料として閉じる。Grokの査読は編集判断への参考として扱い、合格条件や決裁権限を追加しない。この版の査読対応は完了とする。対外名称も「Progress ledger」とし、「Experimental Proof 1／実験第1証明」とは呼ばない。

本確定記録はZIPの外に置く。受理済みの台帳・README・原資料は変更せず、追加の実行結果も含めない。Bundle 1.0、閉じた開発報告、Stage 4草稿、`schema-gate-001` はそのまま保持する。本線・Gradio・Zenodoへの統合や公開操作は行っていない。

次の作業は、スキーマゲートの新記録または公式run formの確定を、別ファイルで扱う。この台帳への追記で後続工程の完了を作らない。

凍結対象のSHA-256：

```text
dc63d53361903b198998db037f748d743cb236fa97f949c1a2ca6b5804cef2f6  M-Anchor_Stages_1-4_Materials_v0.1.zip
```

このハッシュは資料集のバイト列を特定するものであり、過去の実行の独立再現や新たな実験結果を示さない。

**English record.** The Stages 1–4 materials v0.1 collection is finalized and editorially frozen at the archive hash above. Its internal title remains *Progress ledger*. The collection preserves four distinct statuses: a conditional proof in Stage 1; a completed fixed-input demonstration in Stage 2; completed development checks with integration evaluation incomplete in Stage 3; and an unfrozen draft plan with implementation not started in Stage 4. These statuses concern the records included in this collection.

Stage 2 version 1 / `action-001` and Stage 3 development version 2 / `action-002` remain separate execution records, linked through the README reading order. External review is advisory; this closure adds no acceptance criteria, combined-proof claim, execution results or project-wide completion claim. The archive and its source documents remain unchanged. Subsequent schema-gate records and the official run form belong in separate files; they must not be appended to this ledger to manufacture completion. This finalization record is kept outside the frozen archive.
