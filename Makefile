# FX取引システム - 開発用Makefile

.PHONY: help build up down logs restart clean test migrate populate frontend backend shell status

# デフォルトターゲット
help:
	@echo "=== FX取引システム 開発コマンド ==="
	@echo "📚 基本操作:"
	@echo "  make build     - Dockerイメージをビルド"
	@echo "  make up        - 全サービスを起動"
	@echo "  make down      - 全サービスを停止"
	@echo "  make restart   - 全サービスを再起動"
	@echo "  make logs      - ログを表示"
	@echo "  make status    - サービス状態を確認"
	@echo ""
	@echo "🛠️  開発用:"
	@echo "  make migrate   - データベースマイグレーション実行"
	@echo "  make populate  - モックデータを投入"
	@echo "  make shell     - Django shellを起動"
	@echo "  make test      - テストを実行"
	@echo "  make clean     - 不要なコンテナとボリュームを削除"
	@echo ""
	@echo "🌐 個別起動:"
	@echo "  make backend   - バックエンドのみ起動"
	@echo "  make frontend  - フロントエンドのみ起動"
	@echo ""
	@echo "📋 その他:"
	@echo "  make logs-backend  - バックエンドログのみ"
	@echo "  make logs-frontend - フロントエンドログのみ"
	@echo "  make logs-db       - データベースログのみ"

# Docker関連コマンド
build:
	@echo "🔨 Dockerイメージをビルド中..."
	docker-compose build

up:
	@echo "🚀 バックエンドサービスを起動中..."
	docker-compose up -d
	@echo "✅ サービス起動完了"
	@echo "🔧 バックエンドAPI: http://localhost:8000"
	@echo "💾 データベース: localhost:5432"
	@echo "📝 フロントエンド起動: make frontend"

down:
	@echo "⏹️  全サービスを停止中..."
	docker-compose down

restart: down up

logs:
	@echo "📋 全サービスのログを表示..."
	docker-compose logs -f

logs-backend:
	@echo "📋 バックエンドログを表示..."
	docker-compose logs -f backend

logs-frontend:
	@echo "📋 フロントエンドログを表示..."
	docker-compose logs -f frontend

logs-db:
	@echo "📋 データベースログを表示..."
	docker-compose logs -f db

status:
	@echo "📊 サービス状態:"
	docker-compose ps

# 開発用コマンド
migrate:
	@echo "🔄 データベースマイグレーション実行中..."
	docker-compose exec backend python manage.py makemigrations
	docker-compose exec backend python manage.py migrate
	@echo "✅ マイグレーション完了"

populate:
	@echo "📊 モックデータを投入中..."
	docker-compose exec backend python manage.py populate_mock_data
	@echo "✅ モックデータ投入完了"

shell:
	@echo "🐍 Django shellを起動..."
	docker-compose exec backend python manage.py shell

test:
	@echo "🧪 テストを実行中..."
	docker-compose exec backend python manage.py test

# 個別サービス起動
backend:
	@echo "🔧 バックエンドサービスのみ起動..."
	docker-compose up -d db backend
	@echo "✅ バックエンド起動完了: http://localhost:8000"

frontend:
	@echo "🌐 フロントエンドを起動中..."
	@echo "📝 注意: フロントエンドはローカルで起動します"
	@echo "🔧 バックエンドが起動していることを確認してください"
	cd frontend && pnpm install && pnpm dev

# メンテナンス
clean:
	@echo "🧹 不要なコンテナとボリュームを削除中..."
	docker-compose down -v
	docker system prune -f
	@echo "✅ クリーンアップ完了"

# 完全セットアップ (初回用)
setup: build up migrate populate
	@echo "🎉 初回セットアップ完了!"
	@echo "🔧 バックエンドAPI: http://localhost:8000"
	@echo "💾 データベース: localhost:5432"
	@echo ""
	@echo "💡 次のステップ:"
	@echo "  make frontend  - フロントエンドを起動"
	@echo "  make logs      - ログを確認"
	@echo "  make help      - 使用可能なコマンドを表示"

# 開発環境リセット
reset: clean setup
	@echo "🔄 開発環境をリセットしました"

# データベースのみリセット
reset-db:
	@echo "💾 データベースをリセット中..."
	docker-compose down
	docker volume rm trades_postgres_data 2>/dev/null || true
	docker-compose up -d db
	@echo "⏳ データベース起動待機中..."
	sleep 5
	docker-compose up -d backend
	make migrate
	make populate
	@echo "✅ データベースリセット完了"

# 依存関係インストール
install-frontend:
	@echo "📦 フロントエンド依存関係をインストール中..."
	cd frontend && pnpm install
	@echo "✅ フロントエンド依存関係インストール完了"

# 本番用ビルド
build-prod:
	@echo "🏭 本番用ビルドを作成中..."
	cd frontend && pnpm build
	@echo "✅ 本番用ビルド完了"

# コードフォーマット (将来用)
format:
	@echo "🎨 コードフォーマット中..."
	@echo "⚠️  フォーマッタ未設定 - 今後実装予定"

# リンター実行 (将来用)
lint:
	@echo "🔍 コード品質チェック中..."
	@echo "⚠️  リンター未設定 - 今後実装予定"