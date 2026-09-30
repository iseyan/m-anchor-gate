# 計数料金の根拠確認 001

**結論：確認した公式資料からは、計数1回の料金上界を確定できませんでした。** 候補は未採用です。現行run 001と候補run 002は、どちらも `execution_ready=false` のままです。

確認時刻：2026-09-30T16:24:55.322271+00:00（UTC）。対象は `POST https://api.openai.com/v1/responses/input_tokens`、固定モデルは `gpt-5.4-mini-2026-03-17` です。この記録は料金根拠の調査だけを扱います。

## 確認範囲

| 公式資料 | 確認できた内容と限界 |
|---|---|
| [計数ガイド](https://developers.openai.com/api/docs/guides/token-counting) | 生成前の計数方法と、要求の構造に伴うトークンを説明。計数要求の課金条件は確定できない。 |
| [計数API仕様](https://developers.openai.com/api/reference/typescript/resources/responses/subresources/input_tokens/methods/count) | 要求・応答の形式を確認。返される `input_tokens` を課金数量とみなす根拠は得られない。 |
| [一般料金表](https://developers.openai.com/api/docs/pricing) | API一般の料金説明とモデル料金はあるが、計数要求に適用する課金数量・上界を確定できない。 |
| [計数リソース](https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens) | 旧platform URLからの転送先。同じ仕様群であり、独立した料金根拠ではない。 |
| [更新履歴](https://developers.openai.com/api/docs/changelog) | 取得した本文で `input_tokens`、`token count` は一致なし。料金根拠は得られない。 |
| [使用量仕様](https://developers.openai.com/api/reference/resources/admin/subresources/organization/subresources/usage) | 集計用の使用量項目を確認。当該計数エンドポイントの課金条件は確定できない。 |

検索語・参照URL・観測内容は [pricing-evidence.json](pricing-evidence.json) に記録しました。これは記載した資料の範囲での確認です。料金情報の不存在を証明するものではありません。アカウント固有の契約・請求情報は確認していません。

## 判断と保持する状態

一般料金表から「計数は無料」「生成入力と同じ単価で課金される」とは推定しません。応答の計数値があることも、課金数量や料金上界の根拠にはなりません。

候補にある `0.14 + 7c ≤ 1.00` は予算条件です。残額から `c` の値を決めることはできないため、計数の料金根拠・1回上界・予約額・合計上界は `null` を維持します。料金上界が未確定のまま、最初の計数要求を送りません。

現行 `stage3-preparation-001` の総枠は7のままです。入力8,192以下の根拠も未確立なので、生成へ進みません。候補 `stage3-preparation-002` は未採用・未凍結・未実行です。候補フォルダを001の実行パスにはしません。

査読は参考です。私の判断も、今回の資料では送信前の費用上界を支えられないため、実行条件を変更しない、というものです。

## この記録で行ったこと

料金資料の確認と、この別記録の作成だけです。実験の生成0回・計数0回・正本状態書込0回。提供元への問い合わせは未送信です。コード変更・実行検査・GitHub Actionsは行っていません。

基点はコミット `0e07c135202114191cc873f14825c344a00b3b0b`。既存417ファイルは保持し、このフォルダだけを追加します。001–003、条件版、結び付け001、環境受領記録、候補、Bundle・資料集・閉じた報告は変更しません。旧ケースID・旧R4ハッシュ・69／68／003を新runの検証結果へ移しません。

次に必要なのは、候補が既に求めている**当該エンドポイントの適用料金条件**です。入力長への依存、8,192超過、エラー・タイムアウト・到達不明を含む料金の扱いと、送信前に確保できる上界が対象です。新しい合格条件は追加していません。後日根拠を得た場合は別記録に置きます。

`FILES.sha256` はこの記録の3ファイルを特定するものです。公式ページの真正性や実行再現性の証明ではありません。

