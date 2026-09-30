# テスト用 M-Anchor Minimal — Python実装 v0.1

数理稿v0.4の候補保存条件を、モデル外で保持する候補集合に適用する小さな実装です。本体は `m_anchor_minimal.py` の1ファイル。Python 3.10以降の標準ライブラリだけを使用します。

## 最小の使用例

```python
from m_anchor_minimal import MAnchor

state = MAnchor({"h_A", "h_B"})

# Bを選んでも、証拠を適用していないので候補は両方残る。
state, record = state.step("a_B", "二値の提出を要求された")
print(state.candidates)  # frozenset({'h_A', 'h_B'})：表示順は不定
```

`step()` は、新しい状態と記録を返します。元の状態は不変なので、次の遷移には返された状態を渡してください。LLMから得た行為トークンを `action` に渡して利用できます。行為の実行やAPI接続は、呼び出し側で扱います。

## 証拠に基づく更新

```python
state, record = state.step(
    "a_B",
    "適用する方針に従ってBを選択",
    evidence={"observation-001@v1"},
    compatible={"h_B"},
    map_version="causal-assessment/v1",
)
print(state.candidates)  # frozenset({'h_B'})
```

| 引数 | 意味 |
| --- | --- |
| `omega` | 固定した仮説空間。候補のIDは空でない文字列 |
| `candidates` | 現在保持する候補。初期値を省略すると `omega` 全体 |
| `action`, `reason` | 選択した行為と、その選択理由。証拠とは別に記録 |
| `evidence` | この遷移に適用する、受理済みで現在も有効な証拠のID。版を特定できるIDを渡す |
| `compatible` | その証拠解釈が許す候補集合 $M(D_t)$ |
| `map_version` | 証拠を解釈した規則・処理の識別子と版 |
| `proposed` | 検査する遷移後候補。省略すると $K_t\cap M(D_t)$ を採用 |

`evidence`、`compatible`、`map_version` は一緒に指定します。証拠が空なら後二つは省略し、内部で $M(\varnothing)=\Omega$ とします。`compatible=set()` は「証拠を適用した結果、両立する候補がない」という意味であり、証拠なしとは異なります。

証拠の受理・現在の有効性・解釈の正しさは、呼び出し側の責任です。コードは渡されたIDの実在や内容を照会しません。再現可能なテストでは、証拠と両立集合をあらかじめ定めたテストデータから渡し、その内容をIDで参照できるようにしてください。

## 不正な除去の検出

```python
state = MAnchor({"h_A", "h_B"})
try:
    state.step("a_B", "強制選択", proposed={"h_B"})
except ValueError as error:
    print(error)  # Unsupported removal: ['h_A']
print(state.candidates)  # 両方残る
```

検査する条件は次の二つです。

$$
K_{t+1}\subseteq K_t,
\qquad
(K_t\setminus K_{t+1})\cap M(D_t)=\varnothing.
$$

両立する候補の除去、候補の追加・復元、証拠基底のない解釈指定は `ValueError` になります。状態は変更されません。判定には `assert` を使用していないため、Pythonの最適化オプションでも検査は残ります。

`proposed` を渡せば部分取り込みも許されます。既存証拠の再適用では、同じ証拠ID・解釈・版を再度渡します。新しい観察がなくても、適用した証拠が除去を支持すれば更新できます。

## 記録とテスト

返された `record` はJSONに変換できます。`action` に行為と遷移前候補、`audit` に遷移前後候補・除去集合・適用証拠・解釈の版と結果が入ります。

```python
import json

with open("transitions.jsonl", "a", encoding="utf-8") as log:
    log.write(json.dumps(record, ensure_ascii=False) + "\n")
```

同じフォルダに検証ファイルを置き、次のコマンドで実行します。

```sh
python -m unittest -v test_m_anchor_minimal.py
```

検証対象は、無証拠での保持、不正な上書き、完全取り込み、部分取り込みと再適用、支持された除去と不正除去の混在、証拠指定の整合、候補枯渇、参照経由の意図しない変更、初期状態と拡張の制限です。これはコードの単体検証であり、LLMの行動実験ではありません。

## この最小実装の範囲

保持するのは外部の候補集合です。LLMの隠れた内部状態の保存を測るものではありません。対象は、世界・仮説空間を固定し、前提を撤回しない通常遷移です。空集合は候補の枯渇として保持します。訂正や仮説の再導入は別の更新手続きが必要です。

`proposed` 省略時の完全取り込みは実装上の既定動作です。保存条件自体は、支持された除去をすべて直ちに行うことまでは要求しません。

テストで `proposed` を常に省略すれば、ガードは自ら適合する更新を構成します。モデルが提案する候補除去を評価したい場合は、明示的な構造化出力を `proposed` に渡し、拒否された提案も入力・例外とともに別途記録してください。受理された遷移だけを数えて「モデルの不正除去率がゼロ」と評価しないでください。証拠による正当な除去を伴う試験も必要です。

単一プロセスで順番に呼び出す試験向けです。永続化、同時更新制御、権限管理、出力形式の検査は呼び出し側で扱います。公開欄が事実の断言を意味する場合、その断言の妥当性は候補保存とは別に確認します。搭載時は候補の変更を `step()` に集約してください。
