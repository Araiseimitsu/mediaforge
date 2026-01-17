# MediaForge - メディアファイル変換アプリ

画像、動画、音声ファイルをブラウザ内で変換し、ローカル保存できるWebアプリケーションです。

## 特徴

- 多形式対応: 画像/動画/音声を一括で変換
- ドラッグ＆ドロップ: 直感的なファイル選択
- ブラウザ内変換: 変換処理は端末内で完結（ffmpeg.wasm）
- ローカル保存のみ: 変換後はそのまま保存
- レスポンシブ: PC/タブレットに対応

## ブラウザ内変換モード（Cloud Run運用）

- 変換処理はブラウザ内で実行（ffmpeg.wasm）
- 変換後ファイルはローカル保存のみ
- GCS設定は不要

## サポート形式

### 画像ファイル
- 入力: JPG, JPEG, PNG, GIF, BMP, TIFF, WebP, SVG
- 出力: JPEG, PNG, WebP, GIF, BMP, TIFF

### 動画ファイル
- 入力: MP4, AVI, MOV, MKV, WMV, FLV, WebM
- 出力: MP4, AVI, MOV, MKV, WebM, GIF

### 音声ファイル
- 入力: MP3, WAV, FLAC, AAC, OGG, M4A
- 出力: MP3, WAV, FLAC, AAC, OGG

## 技術スタック

- バックエンド: Python + FastAPI（テンプレート/静的配信）
- フロントエンド: Vanilla JS + Tailwind CSS
- 変換処理: ffmpeg.wasm（ブラウザ内）

## インストール方法

### 前提条件

- Python 3.8+

### セットアップ

1. リポジトリをクローン
```bash
git clone <repository-url>
cd mediaforge
```

2. 仮想環境を作成
```bash
py -3.12 -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

3. 依存関係をインストール
```bash
py -3.12 -m pip install -r requirements.txt
```

4. アプリケーションを起動
```bash
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

5. ブラウザでアクセス
```
http://localhost:8000
```

## プロジェクト構造

```
mediaforge/
├── app/
│   ├── __init__.py
│   └── main.py              # FastAPIアプリケーション
├── static/
│   ├── css/
│   │   └── style.css        # スタイル
│   ├── js/
│   │   └── app.js           # フロントエンド
│   └── vendor/
│       └── ffmpeg/          # ffmpeg.wasm関連モジュール
├── templates/
│   └── index.html           # メインHTML
├── requirements.txt         # Python依存関係
└── README.md                # ドキュメント
```

## デプロイ

### Google Cloud Run

1. Google Cloud CLIの認証
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

2. Dockerイメージのビルドとプッシュ
```bash
gcloud builds submit --tag asia-northeast1-docker.pkg.dev/YOUR_PROJECT_ID/mediaforge-repo/mediaforge:latest
```

3. Cloud Runにデプロイ
```bash
gcloud run deploy mediaforge \
  --image asia-northeast1-docker.pkg.dev/YOUR_PROJECT_ID/mediaforge-repo/mediaforge:latest \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated
```

## ライセンス

MIT
