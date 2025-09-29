# GMOコインFX自動売買 実装設計書

## 📋 プロジェクト概要

GMOコインの外国為替FX APIを使用した自動売買システムの構築手順とアーキテクチャ設計

---

## 🚀 Phase 1: 口座開設・準備フェーズ（1-2週間）

### 1.1 GMOコイン口座開設
- **対象サービス**: GMOコイン「外国為替FX」
- **必要書類**: 本人確認書類、マイナンバーカード等
- **開設期間**: 通常3-5営業日
- **初回入金**: 最低100,000円（推奨500,000円以上）

### 1.2 API利用申請
```
📝 申請手順:
1. GMOコインにログイン
2. API設定画面へアクセス
3. 利用規約確認・同意
4. API利用申請書提出
5. 審査（通常1-3営業日）
6. APIキー・シークレット発行
```

### 1.3 API利用料金
- **初回30日間**: 無料トライアル
- **以降**: 注文約定時に1通貨あたり0.002円

### 1.4 開発環境セットアップ
```bash
# Python環境構築
python -m venv fx_trading_env
source fx_trading_env/bin/activate  # Windows: fx_trading_env\Scripts\activate

# 必要ライブラリインストール
pip install requests websocket-client pandas numpy python-dotenv schedule
```

---

## 🏗️ Phase 2: システム設計フェーズ（1週間）

### 2.1 システムアーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Layer    │    │  Logic Layer    │    │   API Layer     │
│                 │    │                 │    │                 │
│ • 価格データDB  │◄───┤ • 戦略エンジン  │◄───┤ • GMO API Client│
│ • 取引履歴DB    │    │ • リスク管理    │    │ • WebSocket     │
│ • 設定データ    │    │ • ポジション管理│    │ • 認証管理      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        ▲                       ▲                       ▲
        │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  UI/Monitor     │    │   Scheduler     │    │   Logging       │
│                 │    │                 │    │                 │
│ • ダッシュボード│    │ • 戦略実行      │    │ • 取引ログ      │
│ • アラート機能  │    │ • 定期処理      │    │ • エラーログ    │
│ • 設定画面      │    │ • ヘルスチェック│    │ • パフォーマンス│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 2.2 ディレクトリ構成
```
fx_auto_trading/
├── config/
│   ├── __init__.py
│   ├── settings.py          # 設定管理
│   └── api_config.py        # API設定
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── gmo_client.py    # GMO API クライアント
│   │   └── websocket_client.py # WebSocket管理
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── base_strategy.py # 戦略基底クラス
│   │   ├── time_21_strategy.py # 21時戦略
│   │   └── scalping_strategy.py # スキャルピング戦略
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── position_manager.py # ポジション管理
│   │   └── risk_manager.py  # リスク管理
│   ├── data/
│   │   ├── __init__.py
│   │   ├── database.py      # データベース管理
│   │   └── market_data.py   # 市場データ管理
│   └── utils/
│       ├── __init__.py
│       ├── logger.py        # ログ管理
│       └── notification.py  # 通知機能
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_strategy.py
│   └── test_risk.py
├── logs/
├── data/
├── requirements.txt
├── main.py                  # メインエントリーポイント
└── README.md
```

### 2.3 データベース設計
```sql
-- 取引履歴テーブル
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    symbol VARCHAR(10),
    side VARCHAR(4),  -- BUY/SELL
    size DECIMAL(15,0),
    price DECIMAL(10,5),
    order_type VARCHAR(20),
    status VARCHAR(20),
    strategy VARCHAR(50),
    profit_loss DECIMAL(10,2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ポジションテーブル
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(10),
    side VARCHAR(4),
    size DECIMAL(15,0),
    entry_price DECIMAL(10,5),
    current_price DECIMAL(10,5),
    unrealized_pnl DECIMAL(10,2),
    status VARCHAR(20),  -- OPEN/CLOSED
    opened_at DATETIME,
    closed_at DATETIME
);

-- 市場データテーブル
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(10),
    timestamp DATETIME,
    bid DECIMAL(10,5),
    ask DECIMAL(10,5),
    volume BIGINT
);
```

---

## 🔧 Phase 3: 基盤実装フェーズ（2週間）

### 3.1 GMO API クライアント実装
```python
# 実装要素:
class GMOCoinAPI:
    def __init__(self, api_key, secret_key):
        # 認証情報管理
    
    def get_account_info(self):
        # 口座情報取得 (Private API)
    
    def get_ticker(self, symbol):
        # レート情報取得 (Public API)
    
    def place_order(self, symbol, side, size, order_type):
        # 注文発注 (Private API)
    
    def get_positions(self):
        # ポジション一覧取得 (Private API)
    
    def close_position(self, position_id):
        # ポジション決済 (Private API)
```

### 3.2 WebSocket実装
```python
# リアルタイムデータ取得
class GMOWebSocketClient:
    def __init__(self):
        # WebSocket接続管理
    
    def connect_public_stream(self, symbol):
        # Public WebSocket (レート情報)
    
    def connect_private_stream(self):
        # Private WebSocket (約定通知等)
    
    def on_price_update(self, data):
        # 価格更新イベント処理
```

### 3.3 データ管理システム
```python
class DatabaseManager:
    def save_trade(self, trade_data):
        # 取引記録保存
    
    def save_market_data(self, price_data):
        # 市場データ保存
    
    def get_trade_history(self, start_date, end_date):
        # 取引履歴取得
```

---

## 📈 Phase 4: 戦略実装フェーズ（2週間）

### 4.1 戦略基底クラス
```python
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, config):
        self.config = config
        self.positions = []
    
    @abstractmethod
    def should_enter(self, market_data):
        # エントリー判定
        pass
    
    @abstractmethod
    def should_exit(self, position, market_data):
        # エグジット判定
        pass
    
    def execute(self, market_data):
        # 戦略実行メインロジック
        pass
```

### 4.2 21時戦略実装
```python
class Time21Strategy(BaseStrategy):
    def should_enter(self, market_data):
        # 21:00の価格変動をチェック
        # エントリー条件判定
        
    def should_exit(self, position, market_data):
        # 損切り・利確判定
        # 時間による決済判定
```

### 4.3 リスク管理システム
```python
class RiskManager:
    def __init__(self, max_risk_percent, max_positions):
        self.max_risk_percent = max_risk_percent
        self.max_positions = max_positions
    
    def calculate_position_size(self, account_balance, stop_loss_pips):
        # ポジションサイズ計算
        
    def check_risk_limits(self, account_info, positions):
        # リスク制限チェック
        
    def should_close_all_positions(self, account_info):
        # 緊急決済判定
```

---

## 🔄 Phase 5: 統合・テストフェーズ（2週間）

### 5.1 バックテストシステム
```python
class BacktestEngine:
    def __init__(self, strategy, historical_data):
        self.strategy = strategy
        self.historical_data = historical_data
    
    def run_backtest(self, start_date, end_date):
        # 過去データでの戦略検証
        
    def generate_report(self):
        # パフォーマンスレポート生成
```

### 5.2 テスト項目
- **Unit Test**: 各モジュール個別テスト
- **Integration Test**: API連携テスト
- **Strategy Test**: 戦略ロジックテスト
- **Risk Test**: リスク管理テスト
- **Performance Test**: 負荷テスト

### 5.3 デモ環境テスト
```python
# デモ口座での実地テスト（1週間以上）
- 実際のAPIでの動作確認
- 戦略パフォーマンス評価
- エラーハンドリング確認
- ログ・監視機能確認
```

---

## 🚀 Phase 6: 本番稼働フェーズ（1週間）

### 6.1 本番環境セットアップ
```bash
# サーバー設定（VPS推奨）
- Ubuntu 20.04+ または CentOS 8+
- Python 3.9+
- SQLite/PostgreSQL
- Nginx（Webダッシュボード用）
- SSL証明書設定
```

### 6.2 監視・アラート設定
```python
class MonitoringSystem:
    def __init__(self):
        # 監視設定
    
    def check_system_health(self):
        # システムヘルスチェック
    
    def send_alert(self, message, level):
        # アラート送信（メール/Slack等）
    
    def log_performance_metrics(self):
        # パフォーマンス指標記録
```

### 6.3 運用手順
1. **起動前チェック**
   - API接続確認
   - 残高・ポジション確認
   - 戦略パラメータ確認

2. **稼働中監視**
   - リアルタイム損益監視
   - エラーログ監視
   - ポジション状況監視

3. **定期メンテナンス**
   - ログローテーション
   - データベース最適化
   - パフォーマンス分析

---

## ⚠️ リスク管理・注意事項

### セキュリティ対策
- APIキーの暗号化保存
- 通信のSSL/TLS暗号化
- アクセス制限設定
- 定期的なパスワード変更

### 金銭リスク管理
- 最大損失額の設定（口座残高の2-5%以下）
- ドローダウン制限
- 強制ロスカット設定
- 緊急停止機能

### システムリスク対策
- 冗長化設計
- 自動復旧機能
- バックアップシステム
- 手動介入機能

### 法的・規制対応
- 金融商品取引法遵守
- 税務申告準備
- 取引記録の適切な保管

---

## 📊 期待される成果物

### 最終成果物
1. **自動売買システム** - 完全自動化されたFX取引システム
2. **Webダッシュボード** - リアルタイム監視・操作画面
3. **バックテストツール** - 戦略検証・最適化ツール
4. **レポートシステム** - 取引分析・パフォーマンスレポート
5. **運用ドキュメント** - 操作マニュアル・保守手順書

### パフォーマンス目標
- **稼働率**: 99%以上
- **レスポンス時間**: 1秒以内
- **月間収益率**: 2-5%（リスクに応じて）
- **最大ドローダウン**: 5%以内

---

## 🗓️ 全体スケジュール（約8-10週間）

| Phase | 期間 | 主要タスク |
|-------|------|-----------|
| Phase 1 | 1-2週 | 口座開設・API申請・環境構築 |
| Phase 2 | 1週 | システム設計・アーキテクチャ決定 |
| Phase 3 | 2週 | API実装・WebSocket・DB構築 |
| Phase 4 | 2週 | 戦略実装・リスク管理実装 |
| Phase 5 | 2週 | 統合テスト・バックテスト |
| Phase 6 | 1週 | 本番稼働・監視体制構築 |

**総投資時間**: 約200-300時間
**推奨開発体制**: 1-2名（Python経験者）
**初期投資額**: 500,000円〜1,000,000円（取引資金含む）

---

## 📚 参考資料・学習リソース

### GMOコイン公式
- [GMOコイン外国為替FX API仕様書](https://api.coin.z.com/docs/)
- [APIトライアル申し込み](https://coin.z.com/jp/forex/api/)

### 技術資料
- Python WebSocket Client
- pandas データ分析
- SQLAlchemy ORM
- Flask/FastAPI Web Framework

### FX・金融知識
- テクニカル分析基礎
- リスク管理理論
- アルゴリズム取引基礎
- 金融法規制