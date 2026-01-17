# Python 3.12をベースイメージとして使用
FROM python:3.12-slim

# 作業ディレクトリを設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt .

# Python依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションファイルをコピー
COPY app/ ./app/
COPY static/ ./static/
COPY templates/ ./templates/

# ポート8080を公開（Cloud Runのデフォルト）
EXPOSE 8080

# 環境変数の設定
ENV PYTHONUNBUFFERED=1

# アプリケーションを起動
CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
