# Codeium Copilot 使用ガイド

## プロジェクト固有の指示

このプロジェクトでCodeium Copilotを使用する際の指示です。

### コーディングスタイル

1. **日本語コメント**
   - コメントは日本語で記述
   - docstringも日本語で記述

2. **型ヒント**
   - 関数の引数と戻り値には型ヒントを使用
   - `from typing import` を適切に使用

3. **非同期処理**
   - FastAPIのエンドポイントは `async def` を使用
   - ファイルI/Oは `aiofiles` を使用
   - ブロッキング処理は `asyncio.to_thread()` でラップ

### アーキテクチャパターン

1. **サービス層**
   - ビジネスロジックは `app/services/` に配置
   - 各サービスはクラスとして実装

2. **ルーター層**
   - APIエンドポイントは `app/routers/` に配置
   - FastAPIの `APIRouter` を使用

3. **ユーティリティ**
   - 共通機能は `app/utils/` に配置

### エラーハンドリング

1. **例外処理**
   - 適切な例外を補足
   - ユーザーフレンドリーなエラーメッセージ
   - ログ出力を忘れずに

2. **HTTPException**
   - FastAPIの `HTTPException` を使用
   - 適切なステータスコードを設定

### 推奨パターン

```python
# 非同期関数の例
async def convert_media(
    input_path: Path,
    output_path: Path,
    format: str
) -> None:
    """
    メディアファイルを変換する

    Args:
        input_path: 入力ファイルパス
        output_path: 出力ファイルパス
        format: 出力形式
    """
    try:
        # 処理
        pass
    except Exception as e:
        logger.error(f"変換エラー: {str(e)}")
        raise
```

### 避けるべきパターン

1. **同期的なファイルI/O**
   - `open()` の代わりに `aiofiles.open()` を使用

2. **ブロッキング処理**
   - 重い処理は `asyncio.to_thread()` でラップ

3. **ハードコーディング**
   - 設定値は環境変数または設定ファイルから読み込む

## 依存関係の追加

新しいパッケージを追加する場合：

1. `requirements.txt` に追加
2. バージョンは `>=` を使用（厳密なバージョン固定は避ける）
3. Python 3.8以上との互換性を確認
