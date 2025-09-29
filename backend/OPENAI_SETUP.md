# OpenAI API LLM分析 再有効化手順

## 概要
マルチタイムフレーム分析システムにOpenAI APIによるLLM分析機能が実装済みです。
コスト削減のため一時的に無効化していますが、以下の手順で簡単に再有効化できます。

## 🔧 再有効化手順

### 1. APIキーの確認
`.env`ファイルのOpenAI APIキーが有効であることを確認
```bash
# .envファイル内
OPENAI_API_KEY=sk-proj-xxxxx...
```

### 2. コードの修正

#### ファイル: `analysis/multi_timeframe_analyzer.py`

**65行目付近を修正:**
```python
# 現在（無効化）
self.llm_enabled = False  # bool(self.openai_api_key)

# 再有効化する場合
self.llm_enabled = bool(self.openai_api_key)
```

**67-70行目のコメントアウトを解除:**
```python
# 現在（無効化）
# if self.llm_enabled:
#     from openai import OpenAI
#     self.openai_client = OpenAI(api_key=self.openai_api_key)

# 再有効化する場合
if self.llm_enabled:
    from openai import OpenAI
    self.openai_client = OpenAI(api_key=self.openai_api_key)
```

**136-138行目のコメントアウトを解除:**
```python
# 現在（無効化）
# if self.llm_enabled:
#     llm_result = self._llm_analysis(result, symbol)
#     result["llm_analysis"] = llm_result

# 再有効化する場合
if self.llm_enabled:
    llm_result = self._llm_analysis(result, symbol)
    result["llm_analysis"] = llm_result
```

### 3. サーバー再起動
```bash
source venv/bin/activate
python manage.py runserver 8000
```

## 💰 コスト管理

### APIコスト目安
- **gpt-3.5-turbo**: 約$0.002/1000トークン
- **1回の分析**: 約1000-1500トークン（$0.002-0.003程度）
- **月間使用量**: 100回分析で約$0.20-0.30

### コスト削減Tips
1. **モデル選択**: `gpt-3.5-turbo`（安価）vs `gpt-4`（高品質・高価格）
2. **max_tokens制限**: 現在1000トークンに制限済み
3. **分析頻度制御**: 必要時のみ実行

## 🎯 LLM分析で得られる機能

再有効化すると以下の高度な分析が追加されます：

### 1. 市場心理の解釈
テクニカル指標の背景にある市場参加者の心理状況

### 2. ファンダメンタル要因
経済指標や地政学的リスクの影響分析

### 3. リスク要因の特定
```json
"risk_factors": [
  "重要経済指標発表前の不確実性",
  "中央銀行政策変更リスク",
  "地政学的緊張の高まり"
]
```

### 4. 戦略的推奨
```json
"strategic_recommendations": [
  "段階的なポジション構築を推奨",
  "損切りレベルの厳守",
  "経済指標発表時の注意"
]
```

### 5. 代替シナリオ
メインシナリオが外れた場合の対応策

## 📊 フロントエンド表示

LLM分析が有効な場合、フロントエンドに以下が追加表示されます：
- 市場心理の解釈セクション
- AI推奨エントリータイミング
- リスク警告表示
- 代替戦略提案

## ⚠️ 注意事項

1. **APIキーの保護**: `.env`ファイルをGitにコミットしない
2. **使用量監視**: OpenAI Platformで使用量を定期チェック
3. **エラーハンドリング**: API制限時はアルゴリズム分析のみ実行
4. **本番環境**: 本格運用時は課金プランの検討を推奨

## 🔄 無効化手順

再度無効化する場合は上記手順を逆に実行：
1. `self.llm_enabled = False`に設定
2. LLM関連コードをコメントアウト
3. サーバー再起動