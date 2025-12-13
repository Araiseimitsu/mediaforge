"""
一時ファイルのクリーンアップユーティリティ

Cloud Runのエフェメラルストレージを効率的に使用するため、
古い一時ファイルを定期的にクリーンアップします。
"""
import os
import time
import asyncio
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class FileCleanupManager:
    """一時ファイルのクリーンアップを管理するクラス"""

    def __init__(self, max_age_seconds: int = 3600):
        """
        Args:
            max_age_seconds: ファイルの最大保持時間（秒）デフォルト1時間
        """
        self.max_age_seconds = max_age_seconds
        self.directories = ["uploads", "downloads"]

    async def cleanup_old_files(self) -> dict:
        """
        古いファイルをクリーンアップする

        Returns:
            削除されたファイルの情報
        """
        deleted_files = []
        current_time = time.time()

        for directory in self.directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue

            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    try:
                        # ファイルの最終更新時刻を取得
                        file_age = current_time - file_path.stat().st_mtime

                        # 指定時間より古いファイルを削除
                        if file_age > self.max_age_seconds:
                            file_path.unlink()
                            deleted_files.append({
                                "path": str(file_path),
                                "age_seconds": int(file_age)
                            })
                            logger.info(f"古いファイルを削除: {file_path} (経過時間: {int(file_age)}秒)")
                    except Exception as e:
                        logger.error(f"ファイル削除エラー: {file_path} - {e}")

        return {
            "deleted_count": len(deleted_files),
            "deleted_files": deleted_files
        }

    async def cleanup_all_temp_files(self) -> dict:
        """
        すべての一時ファイルを削除する（緊急時用）

        Returns:
            削除されたファイルの情報
        """
        deleted_files = []

        for directory in self.directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                continue

            for file_path in dir_path.iterdir():
                if file_path.is_file():
                    try:
                        file_path.unlink()
                        deleted_files.append(str(file_path))
                        logger.info(f"一時ファイルを削除: {file_path}")
                    except Exception as e:
                        logger.error(f"ファイル削除エラー: {file_path} - {e}")

        return {
            "deleted_count": len(deleted_files),
            "deleted_files": deleted_files
        }

    async def get_temp_files_status(self) -> dict:
        """
        一時ファイルの状態を取得

        Returns:
            一時ファイルの統計情報
        """
        status = {}
        total_size = 0
        total_files = 0

        for directory in self.directories:
            dir_path = Path(directory)
            if not dir_path.exists():
                status[directory] = {
                    "exists": False,
                    "file_count": 0,
                    "total_size_mb": 0
                }
                continue

            files = list(dir_path.iterdir())
            dir_size = sum(f.stat().st_size for f in files if f.is_file())
            file_count = len([f for f in files if f.is_file()])

            status[directory] = {
                "exists": True,
                "file_count": file_count,
                "total_size_mb": round(dir_size / (1024 * 1024), 2)
            }

            total_size += dir_size
            total_files += file_count

        status["total"] = {
            "file_count": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }

        return status


async def periodic_cleanup_task(interval_seconds: int = 1800):
    """
    定期的にクリーンアップを実行するバックグラウンドタスク

    Args:
        interval_seconds: クリーンアップ実行間隔（秒）デフォルト30分
    """
    cleanup_manager = FileCleanupManager(max_age_seconds=3600)

    while True:
        try:
            logger.info("定期クリーンアップを開始")
            result = await cleanup_manager.cleanup_old_files()
            logger.info(f"定期クリーンアップ完了: {result['deleted_count']}ファイルを削除")

            # ステータスをログ出力
            status = await cleanup_manager.get_temp_files_status()
            logger.info(f"一時ファイルステータス: {status}")

        except Exception as e:
            logger.error(f"定期クリーンアップエラー: {e}")

        # 次の実行まで待機
        await asyncio.sleep(interval_seconds)
