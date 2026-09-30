# M-Anchor Stage 3 Integration Agent

OpenAI Agents API で再利用可能なエージェントを作成し、その ID を使ってセッションを開始・継続する Python アプリです。応答とイベントを逐次表示し、セッション ID、ターン ID、履歴をローカルに保存します。

| 設定 | 値 |
| --- | --- |
| OpenAI プロジェクト | `proj_NQT3WtX9S3RfYpmb7sE602d6` |
| エージェント名 | `M-Anchor Stage 3 Integration Agent` |
| モデル | `gpt-5.6-sol` |
| 実行環境 | `openai_hosted` |
| SDK | 公式 `openai==3.20.0` / `AsyncOpenAI` |
| 再利用する定義 | `agent.json` |

提供された指示、推論設定、テキスト設定、`tools: []` を `agent.json` に保存しています。モデルを別のものに自動変更しません。

## このプロジェクトで起動する

PowerShell で、この README と同じフォルダーに移動して実行します。

```powershell
.\run.ps1 start
```

引数なしの `.\run.ps1` も `start` と同じです。ランチャーはプロジェクトの `work/.venv` を優先し、なければこのフォルダーの `.venv` を使います。パッケージのインストールや更新は自動では行いません。

PowerShell の実行ポリシーでスクリプトを起動できない場合は、Python を直接実行できます。

```powershell
..\..\work\.venv\Scripts\python.exe -X utf8 .\app.py start
```

API キーの設定が必要です。以下の設定手順を確認してください。

このワークスペースでは安全な設定画面でキーを作成し、プロジェクトルートの `.env.local` に保存済みです。キーの有効期限は作成時から **24時間**です。期限後は有効なキーに更新してください。実接続の結果と保存された ID は [実行記録](run-report.md) にあります。

## 別の場所でセットアップする

このフォルダー一式と Python 3.11 以上が必要です。Windows ではこのフォルダー内で実行します。

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\run.ps1 --help
```

macOS / Linux では次の手順です。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py --help
```

以降の例の `.\run.ps1` は、必要に応じて `.venv/bin/python app.py` に置き換えてください。

## API キーを設定する

1. [OpenAI Platform の API キー設定](https://platform.openai.com/api-keys)を開き、対象プロジェクトが `proj_NQT3WtX9S3RfYpmb7sE602d6` であることを確認します。
2. アプリケーション用のキーを作成します。Agents API の操作には `api.agents.read` と `api.agents.write`、モデル実行には `api.responses.write` が必要です。
3. キーを環境変数 `OPENAI_API_KEY` に設定して起動します。キーをチャット、ソースコード、コマンド履歴、共有するログに貼り付けないでください。

Windows PowerShell で今回のターミナルだけに設定する例です。入力内容は画面に表示されません。

```powershell
$secureApiKey = Read-Host 'OpenAI API key' -AsSecureString
$keyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureApiKey)
try {
    $env:OPENAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($keyPointer)
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($keyPointer)
    Remove-Variable secureApiKey, keyPointer
}
.\run.ps1 start
```

終了後に環境変数を外す場合は `Remove-Item Env:OPENAI_API_KEY` を実行します。アプリ実行中のプロセスには通常の環境変数として渡されます。

安全なキー設定機能で `.env.local` に保存済みの場合は、そのファイルも利用できます。読み込み順は次のとおりです。

1. 起動元に既に設定された `OPENAI_API_KEY`
2. `--env-file` で指定したファイル
3. このアプリフォルダーの `.env.local`
4. このプロジェクトのルートにある `.env.local`

キーを含むファイルを配布物やバージョン管理に含めないでください。API キーはローカルのクライアントだけが使用し、エージェントのサンドボックスには渡しません。

キーを作成できても、指定プロジェクトの Agents API・モデル利用権限や課金設定が利用可能であるとは限りません。実際の API 応答で確認します。[公式クイックスタート](https://developers.openai.com/api/docs/guides/agents-api/quickstart)

## セッションを操作する

共通オプションは **コマンドより前**に指定します。

```powershell
.\run.ps1 --timeout 300 start
.\run.ps1 --state-dir .\another-session start
.\run.ps1 --env-file .\.env.local status
```

| コマンド | 操作 |
| --- | --- |
| `create-agent` | `agent.json` の定義から再利用可能なエージェントを用意する |
| `start` | 保存済みの状態を確認し、セッションの開始または継続に進む |
| `start --new-session` | 再利用するエージェント ID で新しいセッションを開始する |
| `start --message "本文"` | 初期メッセージを直接指定する |
| `start --message-file PATH` | UTF-8 ファイルを初期メッセージに使う |
| `send "本文"` | 保存済みのセッションにメッセージを送る |
| `watch` | 新しいメッセージを送らずに既存セッションを観察する |
| `status` | セッションとターンの保存済み結果・現在の状態を確認する |
| `cancel` | 現在実行中のターンのキャンセルを要求する |
| `delete` | 現在保存されているセッションを削除する |

最初は `start` を使えば、定義作成からセッション開始まで進みます。`--new-session` は前のセッションを削除するコマンドではありません。複数のセッションを別々に管理する場合は `--state-dir` を使い分けてください。

標準の初期メッセージは `initial-message.txt` です。ホスト環境で Python のバージョンと現在のフォルダーを読み取り、未提供の資料を確認するところまでを依頼します。M-Anchor のコード、正本状態、証拠レジストリ、収集済み提案を変更する指示は含みません。

```powershell
.\run.ps1 start
.\run.ps1 send '不足している資料と、受領後に最初に確認する内容を日本語で列挙してください。'
.\run.ps1 status
```

## 実行環境とツール

`openai_hosted` は OpenAI が用意・接続する Linux サンドボックスです。Python、Node.js、コマンドラインツールが用意され、作業フォルダーは `/workspace` です。独自のサーバー、ランタイムプロバイダー、実行用の別キーや executor をセットアップする必要はありません。ローカルのファイルは自動でサンドボックスへ渡されません。[ホスト環境の説明](https://developers.openai.com/api/docs/guides/agents-api/environments/openai-hosted)

このアプリはホスト環境のネットワークを `disabled` にして起動します。その環境から Zenodo や GitHub の資料を直接取得することはできません。評価資料は別途取得・検証してから、明示的に環境へ渡す必要があります。ローカルのクライアントから OpenAI API への接続にはインターネット接続が必要です。

アプリケーション独自の関数ツールは `tools: []` のままです。未登録の関数呼び出しには失敗結果を返し、任意のローカルコードを実行しません。M-Anchor の権威的状態を変更する決定論的なコミット関数は、このアプリには実装していません。エージェントの自然言語の説明やログは、証拠の外部承認や状態更新の権限になりません。

## ログと再接続

標準の保存先は、このアプリフォルダー内の `.runtime` です。`state.json` に ID を保存し、イベントを JSONL、永続化された項目を JSON、読みやすい応答をテキストで記録します。ログには会話内容が含まれるため、共有前に内容を確認してください。

テキストはコンソールへ逐次表示します。断片に分かれたキーがログへ残ることを避けるため、JSONL の `output_text.delta` は本文を省いてイベント情報を記録し、完成した本文を `output_text.done` と永続化された項目に保存します。これらのログは、Stage 3 で再生する収集済みの生の提案データとは別のものです。

同じ保存先を複数のプロセスから操作しないよう、単一書き込み用のロックを使用します。前のプロセスが動いている間は、同じ保存先で別の操作を起動しないでください。

ストリームを閉じる、タイムアウトになる、または **Ctrl+C を押すだけでは、サーバー側のターンはキャンセルされません**。再開時はまず次を使います。

```powershell
.\run.ps1 status
.\run.ps1 watch
```

停止したい場合は明示的に `.\run.ps1 cancel` を実行し、その後 `status` で結果を確認します。API ストリームは過去のイベントを再送しません。再接続時には永続化された項目と対象ターンの状態を使って補います。入力メッセージを自動で再送しないため、接続エラー後は同じ入力を送る前に結果を確認してください。`idle` やストリーム終了だけを成功とは扱いません。[イベントと項目](https://developers.openai.com/api/docs/guides/agents-api/sessions/events)

`delete` はセッション履歴とホスト環境を削除するための操作です。必要な結果を先に取得してください。実行中や環境の準備中には削除が拒否される場合があります。実行を止め、状態が落ち着いてから再実行します。OpenAI 側の物理的な後片付けは非同期で進む場合があります。[セッション管理](https://developers.openai.com/api/docs/guides/agents-api/sessions/manage)

このアプリの `delete` は、リモートに保存された成果物が一つでもある場合には停止します。ダウンロードしただけではこの保護は解除されません。成果物は公式 SDK の `client.beta.agents.sessions.artifacts.content(artifact_id, session_id=session_id)` で取得し、保存した内容を確認した後、必要に応じて `artifacts.delete(artifact_id, session_id=session_id)` でリモートの成果物を明示的に削除してください。その後にアプリの `delete` を再実行できます。アプリ自体には成果物のダウンロード・個別削除コマンドはありません。セッションを削除しても、再利用するエージェント定義とローカルのログは残ります。

## Stage 3 評価への接続

APIアプリの起動確認後、提供された `Bundle_1.0.zip` と共有会話の収集済み15提案を使い、隣の [Stage 3 再生評価アプリ](../m-anchor-stage3/README.md) を作成しました。現在の評価結果と由来の限界は、そちらの評価報告を参照してください。APIアプリはモデルによる提案の生成・対話、Stage 3 アプリは既存提案の決定論的な検査・保存を担当します。

このAPIアプリ単体の起動確認は、Stage 3 評価の合否を示しません。新しいケースの統合・評価では、以下を外部で固定します。

- 正本となる Zenodo 公開 Python v0.1 の正確なレコード、ソース、バージョン識別情報
- 公開実装の既存テスト
- 変更・再生成していない、収集済みの生の提案
- ケースごとの `case_id`、初期状態、権威的なバージョンとハッシュ
- 証拠レジストリ、およびケースごとの外部承認・証拠採用の記録
- 公開コアを呼び出す最小のアダプター、リプレイ、状態ストアの境界を確定するための仕様

資料の内容を推測して埋めません。公開コアと既存テストを先に確認し、拒否された提案が状態・バージョン・ハッシュ・証拠権限を変えないこと、PI-09 の正当に採用された証拠による `{h_A, h_B} -> {h_B}` 更新を妨げないことを検証する必要があります。プローブ結果を一般的なプロンプトインジェクションの失敗率として報告しません。

## エラーが出た場合

| 症状 | 確認すること |
| --- | --- |
| `OPENAI_API_KEY` が未設定 | 上の環境変数または `.env.local` の読み込み設定 |
| 認証エラー | 対象プロジェクトの有効なキーか、失効していないか |
| 権限エラー | Agents API と `gpt-5.6-sol` のプロジェクト利用権限、必要スコープ |
| 利用上限・レート制限 | Platform の利用枠・課金設定。結果確認前に入力を重複送信しない |
| タイムアウト・通信切断 | `status` と `watch` で既存ターンを確認。`--timeout` は秒単位 |
| ツール・環境・ターンの失敗 | 表示されたエラーと保存されたイベントを確認。成功したとみなして先へ進めない |

## 実装の参照先

API 接続なしの検証は、このフォルダーで次のように実行できます。

```powershell
..\..\work\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

別の場所にセットアップした場合は `.venv` 内の Python を使ってください。

再利用する定義は `client.beta.agents.create`、最初の入力とストリームは `client.beta.agents.sessions.create(..., agent_id=..., input=..., stream=True)` を利用します。既存セッションの観察、関数結果の送信、保存済みの項目・ターン取得も同じ `client.beta.agents` 名前空間で行います。SDK が `OpenAI-Beta: agents=v1` ヘッダーを付与します。

- [Agents API 概要](https://developers.openai.com/api/docs/guides/agents-api/overview)
- [エージェント定義](https://developers.openai.com/api/docs/guides/agents-api/configuration)
- [セッションの開始と継続](https://developers.openai.com/api/docs/guides/agents-api/sessions)
- [関数呼び出しと結果の返却](https://developers.openai.com/api/docs/guides/agents-api/tools/functions)
- [公式 Python SDK](https://github.com/openai/openai-python)
