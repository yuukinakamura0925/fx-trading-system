# 🚀 FX取引システム

Django + Next.js で構築されたモダンなFX取引システムです。GMO証券のAPIを使用した自動取引機能とリアルタイム市場データ表示を提供します。

![Dashboard Preview](docs/images/dashboard-preview.png)

## 📋 目次

- [概要](#概要)
- [技術スタック](#技術スタック)
- [機能](#機能)
- [セットアップ](#セットアップ)
- [使用方法](#使用方法)
- [API仕様](#api仕様)
- [開発](#開発)
- [トラブルシューティング](#トラブルシューティング)

## 🎯 概要

このシステムは個人用FX取引の自動化とポートフォリオ管理を目的として開発されました。モックデータを使用した開発環境と、実際のGMO証券API連携に対応しています。

### 主な特徴
- 📊 リアルタイム市場データ表示
- 🤖 自動取引戦略の実装
- 📈 ポジション管理とP&L計算
- 🎨 モダンなレスポンシブUI
- 🐳 Docker環境での簡単デプロイ

## 🛠️ 技術スタック

### バックエンド
- **Django 4.2** - Webフレームワーク
- **Django REST Framework** - API開発
- **PostgreSQL** - メインデータベース
- **Redis** - キャッシュ・セッション管理

### フロントエンド
- **Next.js 14** - Reactフレームワーク
- **React 18** - UIライブラリ
- **TypeScript** - 型安全な開発
- **Tailwind CSS** - スタイリング
- **Recharts** - チャート表示
- **Lucide React** - アイコン

### インフラ
- **Docker & Docker Compose** - コンテナ化
- **Nginx** - リバースプロキシ（本番環境）

## ✨ 機能

### 📊 ダッシュボード
- リアルタイム価格表示（6通貨ペア）
- ポジションサマリー
- 損益グラフ
- 市場データチャート

### 🎯 取引機能
- 手動ポジション作成
- 自動取引戦略
- ストップロス・利確設定
- リスク管理

### 📈 分析機能
- P&L計算
- 取引履歴
- パフォーマンス分析
- レポート生成

### 🔧 管理機能
- 通貨ペア管理
- 戦略設定
- システム監視
- バックアップ

## 🚀 セットアップ

### 前提条件
- Docker & Docker Compose
- pnpm (フロントエンド開発用)
- Make (オプション：コマンド実行を簡素化)

### 1. リポジトリクローン
```bash
git clone <repository-url>
cd trades
```

### 2. 初回セットアップ（推奨）
```bash
make setup
```

または手動で：
```bash
# Dockerイメージビルド
docker-compose build

# サービス起動
docker-compose up -d

# データベースマイグレーション
docker-compose exec backend python manage.py migrate

# モックデータ投入
docker-compose exec backend python manage.py populate_mock_data
```

### 3. フロントエンド起動
```bash
make frontend
```

または：
```bash
cd frontend
pnpm install
pnpm dev
```

## 📱 使用方法

### アクセス
- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **管理画面**: http://localhost:8000/admin

### 基本操作

#### システム起動
```bash
make up          # バックエンドサービス起動（Django + PostgreSQL）
make frontend    # フロントエンド起動（別ターミナルで実行）
```

#### 開発
```bash
make logs        # ログ確認
make shell       # Django shell起動
make migrate     # マイグレーション
make populate    # テストデータ投入
```

#### メンテナンス
```bash
make restart     # 再起動
make clean       # クリーンアップ
make reset       # 完全リセット
```

## 🔌 API仕様

### 認証
現在は認証なしで動作します（開発環境用）。本番環境では認証機能の実装が必要です。

### エンドポイント

#### 市場データ
- `GET /api/market-data/latest/` - 最新価格取得
- `GET /api/market-data/history/` - 履歴データ取得

#### ポジション管理
- `GET /api/positions/open/` - オープンポジション一覧
- `POST /api/positions/` - ポジション作成
- `GET /api/positions/summary/` - ポジションサマリー

#### 戦略
- `GET /api/strategies/` - 戦略一覧
- `POST /api/strategies/` - 戦略作成

詳細なAPI仕様は `/docs/api/` を参照してください。

## 🧪 開発

### 開発環境
```bash
# バックエンド開発
make up          # Django + PostgreSQL起動
make shell       # Django shell起動

# フロントエンド開発（別ターミナル）
make frontend    # Next.js開発サーバー起動

# ログ監視
make logs        # 全ログ確認
make logs-backend # バックエンドログのみ
```

### データベース操作
```bash
# マイグレーション作成・適用
make migrate

# テストデータ投入
make populate

# データベースリセット
make reset-db
```

### コード品質
```bash
# テスト実行
make test

# フォーマット（今後実装）
make format

# リンター（今後実装）
make lint
```

## 📂 プロジェクト構成

```
trades/
├── backend/                 # Django バックエンド
│   ├── fx_trading/         # プロジェクト設定
│   ├── api/                # REST API
│   ├── core/               # 基本モデル
│   ├── trading/            # 取引ロジック
│   └── mock_data/          # モックデータ
├── frontend/               # Next.js フロントエンド
│   ├── src/
│   │   ├── app/           # App Router
│   │   ├── components/    # React コンポーネント
│   │   └── lib/           # ユーティリティ
│   └── public/            # 静的ファイル
├── docs/                   # ドキュメント
├── docker-compose.yml      # Docker構成
├── Makefile               # 開発コマンド
└── README.md              # このファイル
```

## 🔧 設定

### 環境変数
| 変数名 | デフォルト値 | 説明 |
|--------|-------------|------|
| `POSTGRES_DB` | `fx_trading` | データベース名 |
| `POSTGRES_USER` | `fx_user` | データベースユーザー |
| `POSTGRES_PASSWORD` | `fx_password123` | データベースパスワード |
| `DB_HOST` | `db` | データベースホスト |
| `DEBUG` | `True` | Djangoデバッグモード |

### 本番環境設定
本番環境では以下の設定を変更してください：
- `DEBUG = False`
- セキュアなパスワード設定
- SSL証明書の配置
- 適切なCORS設定

## 🐛 トラブルシューティング

### よくある問題

#### コンテナが起動しない
```bash
# ログを確認
make logs

# 完全リセット
make reset
```

#### データベース接続エラー
```bash
# データベースサービス確認
docker-compose ps db

# データベースリセット
make reset-db
```

#### フロントエンドが表示されない
```bash
# 依存関係再インストール
cd frontend
rm -rf node_modules
pnpm install

# 開発サーバー再起動
pnpm dev
```

#### ポート競合
デフォルトポートが使用中の場合：
- 3000: フロントエンド
- 8000: バックエンド  
- 5432: PostgreSQL

`docker-compose.yml`でポートを変更してください。

### ログ確認
```bash
# 全体ログ
make logs

# 個別サービス
make logs-backend  # Django APIサーバー
make logs-db       # PostgreSQLデータベース
```

### パフォーマンス最適化
- メモリ使用量の監視
- データベースインデックスの最適化
- フロントエンドバンドルサイズの確認

## 📚 参考資料

- [Django公式ドキュメント](https://docs.djangoproject.com/)
- [Next.js公式ドキュメント](https://nextjs.org/docs)
- [Docker Compose](https://docs.docker.com/compose/)
- [GMO証券API仕様](https://api.coin.z.com/docs/)

## 🤝 コントリビューション

1. Forkしてください
2. Feature branchを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. Branchにプッシュ (`git push origin feature/AmazingFeature`)
5. Pull Requestを作成

## 📄 ライセンス

このプロジェクトは個人用途として開発されています。

## 📞 サポート

問題や質問がある場合：
1. まず[トラブルシューティング](#トラブルシューティング)を確認
2. Issueを作成
3. ログファイルを添付

---

**⚠️ 重要な注意事項**
- このシステムは教育・学習目的で開発されています
- 実際の取引には十分なテストとリスク管理が必要です
- 投資は自己責任で行ってください