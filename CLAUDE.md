# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

GMOコインFX自動売買システム - Django + Next.js + PostgreSQL + Docker構成
モックデータを使用した開発環境（本番API契約待ち）

## 重要な開発ルール

### 📝 コメント・説明ルール
1. **Python初心者向け対応**: 全ての技術用語は初回使用時に詳細説明する
2. **日本語コメント必須**: 実装したコードには必ず日本語でコメントアウトを追加し、何をしているか補足する
3. **細かい説明**: ライブラリやパッケージの説明は逐一行う（例：psycopg2の説明等）

### 🏗️ アーキテクチャ

```
backend/               # Django REST API サーバー
├── fx_trading/       # Django プロジェクト設定
├── api/              # GMO API関連・市場データ管理
├── trading/          # 取引ロジック・ストラテジー
├── core/             # 基本モデル（通貨ペア等）
└── mock_data/        # モックデータ（GMO API代替）

frontend/             # Next.js React フロントエンド（未実装）
docker-compose.yml    # PostgreSQL + Redis + Django の統合環境
```

## 📊 データベース設計

### 主要モデル関係
- **Currency** (core) → 通貨ペア定義（USD_JPY等）
- **MarketData** (api) → リアルタイム価格データ
- **Strategy** (trading) → 取引戦略設定
- **Position** (trading) → 現在ポジション（損益自動計算）
- **Trade** (trading) → 取引履歴

### PostgreSQL特化機能
- JSONB型でGMO APIレスポンス保存
- インデックス最適化（currency + timestamp）
- 損益計算メソッド内蔵

## 🐳 Docker開発環境

### 基本コマンド
```bash
# 全サービス起動（PostgreSQL + Django）
docker-compose up -d

# バックエンドのみ起動
docker-compose up -d db
cd backend && source venv/bin/activate && python manage.py runserver

# マイグレーション実行
cd backend && source venv/bin/activate
python manage.py makemigrations  # モデル変更の検出
python manage.py migrate         # データベース反映

# PostgreSQL接続確認
docker-compose exec db psql -U fx_user -d fx_trading
```

### 重要な技術用語解説
- **psycopg2**: PythonからPostgreSQLに接続するためのライブラリ
- **makemigrations**: Djangoモデルの変更をマイグレーションファイルに変換
- **migrate**: マイグレーションファイルをデータベースに適用

## 🔧 開発フロー

### 1. モデル変更時
```bash
# 1. models.pyを編集
# 2. マイグレーション作成
python manage.py makemigrations
# 3. データベース反映
python manage.py migrate
```

### 2. API開発時
- DRF（Django REST Framework）使用
- CORS設定済み（Next.jsアクセス用）
- 認証は現在AllowAny（開発用）

### 3. モックデータ活用
- GMO API未契約のため mock_data/ でデータ生成
- リアルタイム価格シミュレーション
- WebSocket代替実装

## 📋 現在の開発状況

### ✅ 完了
- Django プロジェクト基盤
- PostgreSQL Docker環境
- 基本モデル設計（Currency, MarketData, Position, Trade等）
- CORS・DRF設定

### 🚧 進行中
- Django モデルマイグレーション実行
- REST API エンドポイント作成
- モックGMO APIクライアント

### ⏳ 予定
- Next.js フロントエンド構築
- リアルタイムチャート表示
- 取引戦略フレームワーク
- WebSocket実装

## 🎯 FX取引システム特有の考慮事項

### データ精度
- 価格データ：小数点5桁（0.00001）
- 損益計算：JPY建て vs その他通貨ペア対応
- スプレッド自動計算

### パフォーマンス
- 時系列データのインデックス最適化
- バックグラウンドタスク用Redis準備
- 大量データ処理対応

### リスク管理
- ポジションサイズ制限
- 損切り・利確設定
- 戦略別パフォーマンス追跡