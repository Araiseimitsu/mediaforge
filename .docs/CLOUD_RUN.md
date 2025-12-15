# Cloud Run デプロイガイド

このドキュメントでは、MediaForgeアプリケーションをGoogle Cloud Runへデプロイする手順を説明します。

## 前提条件

1.  **Google Cloud SDK (gcloud CLI)** がインストールされ、設定されていること。
    - `gcloud init` を実行して、プロジェクトと認証情報を設定してください。
2.  **Docker** がインストールされていること（ローカルビルドを行う場合）。
    - Cloud Runへのソースデプロイ機能を使用する場合、ローカルのDockerは必須ではありませんが、動作確認のために推奨されます。

## デプロイ手順

### 方法 1: 自動スクリプトを使用する (推奨)

プロジェクトのルートディレクトリで以下のスクリプトを実行してください。

**Windowsの場合:**
```cmd
deploy.bat
```

**Mac/Linuxの場合:**
```bash
./deploy.sh
```

これらのスクリプトは以下の操作を自動的に行います：
1.  現在設定されているGoogle Cloudプロジェクトの確認
2.  Cloud Runへのデプロイ（ソースコードから直接ビルド・デプロイ）

### 方法 2: 手動でコマンドを実行する

以下のコマンドを使用してデプロイできます。

```bash
gcloud run deploy mediaforge \
  --source . \
  --region asia-northeast1 \
  --allow-unauthenticated
```

*   `--source .`: カレントディレクトリのコードを使用します（Dockerfileが参照されます）。
*   `--region asia-northeast1`: 東京リージョンを指定しています。必要に応じて変更してください。
*   `--allow-unauthenticated`: 未認証のアクセスを許可します（Webアプリとして公開する場合）。

## 設定の確認

### 環境変数
Cloud Runのコンソール画面で、以下の環境変数が設定されているか確認（または追加）できますが、基本設定は `Dockerfile` 内とデフォルト値で動作するように設計されています。

*   `PORT`: Cloud Runによって自動的に `8080` が設定されます。

### メモリとCPU
デフォルトの設定で動作しない場合、メモリを増やす必要があるかもしれません。
その場合は、以下のフラグをデプロイコマンドに追加してください。
`--memory 2Gi`

## トラブルシューティング

*   **デプロイが失敗する場合**:
    *   `gcloud auth login` で再ログインを試してください。
    *   `gcloud config set project [PROJECT_ID]` で正しいプロジェクトが選択されているか確認してください。
*   **「Service not found」などのエラー**:
    *   Cloud Run API が有効になっているか確認してください。
    
    ```bash
    gcloud services enable run.googleapis.com
    gcloud services enable cloudbuild.googleapis.com
    ```
