# MediaForge - メディアファイル変換アプリ

画像、動画、音声ファイルの形式変換を簡単に行えるWebアプリケーションです。

## 🚀 特徴

- **多形式対応**: 画像、動画、音声ファイルの主要な形式に対応
- **ドラッグ＆ドロップ**: 直感的なファイルアップロード
- **Apple風デザイン**: モダンで美しいUI/UX
- **リアルタイム進捗**: 変換状況をリアルタイムで表示
- **品質調整**: 高品質・標準・低品質から選択可能
- **画像リサイズ**: 幅・高さの指定に対応
- **レスポンシブ**: モバイル端末でも快適に動作

## 📋 サポート形式

### 画像ファイル
- **入力**: JPG, JPEG, PNG, GIF, BMP, TIFF, WebP, SVG
- **出力**: JPEG, PNG, WebP, GIF, BMP, TIFF

### 動画ファイル
- **入力**: MP4, AVI, MOV, MKV, WMV, FLV, WebM
- **出力**: MP4, AVI, MOV, MKV, WebM, GIF

### 音声ファイル
- **入力**: MP3, WAV, FLAC, AAC, OGG, M4A
- **出力**: MP3, WAV, FLAC, AAC, OGG

## 🛠️ 技術スタック

- **バックエンド**: Python 3.8+ + FastAPI
- **フロントエンド**: HTMX + Tailwind CSS
- **画像処理**: Pillow (PIL)
- **動画・音声処理**: FFmpeg + Pydub
- **非同期処理**: aiofiles

## 📦 インストール方法

### 前提条件

- Python 3.8以上

**注意**: FFmpegは `imageio-ffmpeg` パッケージとして自動的にインストールされるため、システムレベルでのインストールは不要です。

#### （オプション）システムレベルのFFmpegインストール

システムレベルのFFmpegを使用したい場合は、以下の手順でインストールできます：

**Windows:**
```bash
# Chocolateyを使用
choco install ffmpeg
```

**macOS:**
```bash
# Homebrewを使用
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

### アプリケーションのセットアップ

1. リポジトリをクローン
```bash
git clone <repository-url>
cd mediaforge
```

2. 仮想環境を作成
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

3. 依存関係をインストール
```bash
pip install -r requirements.txt
```

4. アプリケーションを起動
```bash
# 方法1: uvicornを使用（推奨）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 方法2: main.pyから直接起動
python app/main.py
```

5. ブラウザでアクセス
```
http://localhost:8000
```

6. （オプション）動画変換機能のテスト
```bash
python test_video_converter.py
```

## 🏗️ プロジェクト構造

```
mediaforge/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPIメインアプリケーション
│   ├── routers/
│   │   ├── __init__.py
│   │   └── convert.py       # 変換APIルーター
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_converter.py    # 画像変換サービス
│   │   ├── video_converter.py    # 動画変換サービス
│   │   └── audio_converter.py    # 音声変換サービス
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py       # ファイル操作ユーティリティ
├── static/
│   ├── css/
│   │   └── style.css        # カスタムスタイルシート
│   └── js/
│       └── app.js           # フロントエンドJavaScript
├── templates/
│   └── index.html           # メインHTMLテンプレート
├── uploads/                 # アップロード一時ディレクトリ
├── downloads/               # 変換後ファイル保存先
├── requirements.txt         # Python依存関係
├── README.md               # プロジェクトドキュメント
└── .gitignore              # Git無視ファイル
```

## 🔧 APIエンドポイント

### ファイルアップロード
```
POST /api/convert/upload
```
ファイルをアップロードし、ファイルIDを取得します。

### 変換処理
```
POST /api/convert/process
```
アップロードされたファイルを変換します。

### サポート形式取得
```
GET /api/convert/formats/{file_type}
```
指定されたファイルタイプでサポートされている出力形式を取得します。

### ファイルダウンロード
```
GET /api/convert/download/{filename}
```
変換済みファイルをダウンロードします。

## 🎨 カスタマイズ

### テーマカスタマイズ
`static/css/style.css` を編集してカラーテーマやスタイルを変更できます。

### 新しい形式の追加
各コンバータークラスの `supported_formats` を編集して新しい形式を追加できます。

### 品質設定の調整
各コンバーターの品質設定パラメータを調整して、出力品質をカスタマイズできます。

## 🔒 セキュリティ

- ファイルタイプの検証
- ファイルサイズ制限
- 一時ファイルの自動クリーンアップ
- 安全なファイル名生成

## 🚀 デプロイ

### Dockerを使用したデプロイ

1. `Dockerfile` を作成
2. `docker-compose.yml` を作成
3. `docker-compose up -d` で起動

### 本番環境での考慮事項

- HTTPSの設定
- ファイルストレージの設定（S3など）
- ログの設定
- 監視とアラート

## 🤝 貢献

1. フォークを作成
2. 機能ブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを作成

## 📝 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。

## 🐛 トラブルシューティング

### FFmpegが見つからない場合

まず、テストスクリプトを実行してFFmpegが正しく検出されるか確認:
```bash
python test_video_converter.py
```

**imageio-ffmpegが正しくインストールされているか確認:**
```bash
python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"
```

**システムのFFmpegを使用したい場合:**
```bash
# FFmpegが正しくインストールされているか確認
ffmpeg -version

# パスを確認（Unix/Linux/macOS）
which ffmpeg

# パスを確認（Windows）
where ffmpeg
```

### ファイルが変換されない場合
- `python test_video_converter.py` を実行してFFmpegが検出されるか確認
- ファイル形式がサポートされているか確認
- アプリケーションのログを確認
- エラーメッセージを確認

### パフォーマンスの問題
- 大きなファイルの処理には時間がかかる場合があります
- サーバーのスペックを確認
- 一時ファイルのクリーンアップを確認

## 📞 サポート

問題が発生した場合は、GitHub Issuesで報告してください。

---

**MediaForge** - あなたのメディアファイルを簡単に変形するツール 🚀
