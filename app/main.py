from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import HTMLResponse
import os
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager

from app.routers import convert
from app.utils.cleanup import FileCleanupManager, periodic_cleanup_task

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# バックグラウンドタスク用の変数
cleanup_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーションのライフサイクル管理
    起動時と終了時の処理を定義
    """
    global cleanup_task

    # 起動時の処理
    logging.info("MediaForgeアプリケーションを起動中...")

    # 必要なディレクトリの作成
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)

    # 定期クリーンアップタスクを開始（30分ごと）
    cleanup_task = asyncio.create_task(periodic_cleanup_task(interval_seconds=1800))
    logging.info("定期クリーンアップタスクを開始しました")

    yield

    # 終了時の処理
    logging.info("MediaForgeアプリケーションを終了中...")

    # クリーンアップタスクをキャンセル
    if cleanup_task:
        cleanup_task.cancel()
        try:
            await cleanup_task
        except asyncio.CancelledError:
            logging.info("定期クリーンアップタスクを停止しました")

    # 最終クリーンアップを実行
    cleanup_manager = FileCleanupManager()
    result = await cleanup_manager.cleanup_all_temp_files()
    logging.info(f"最終クリーンアップ完了: {result['deleted_count']}ファイルを削除")


app = FastAPI(
    title="MediaForge",
    description="メディアファイル変換アプリケーション",
    version="1.0.0",
    lifespan=lifespan
)

# 静的ファイルとテンプレートの設定
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ルーターの登録
app.include_router(convert.router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}


@app.get("/api/cleanup/status")
async def get_cleanup_status():
    """一時ファイルのステータスを取得"""
    cleanup_manager = FileCleanupManager()
    status = await cleanup_manager.get_temp_files_status()
    return status


@app.post("/api/cleanup/run")
async def run_cleanup():
    """手動でクリーンアップを実行（古いファイルのみ）"""
    cleanup_manager = FileCleanupManager(max_age_seconds=3600)
    result = await cleanup_manager.cleanup_old_files()
    return result

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
