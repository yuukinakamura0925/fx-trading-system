# Python 3.11ベースイメージ
FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージ更新（PostgreSQL接続用）
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Pythonライブラリインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# ポート8000を公開
EXPOSE 8000

# Django開発サーバー起動
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]