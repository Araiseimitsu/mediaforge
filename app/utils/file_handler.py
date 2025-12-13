import os
import shutil
import asyncio
from pathlib import Path
from typing import List, Optional
import aiofiles

class FileHandler:
    def __init__(self, upload_dir: str = "uploads", download_dir: str = "downloads"):
        self.upload_dir = Path(upload_dir)
        self.download_dir = Path(download_dir)
        
        # ディレクトリが存在しない場合は作成
        self.upload_dir.mkdir(exist_ok=True)
        self.download_dir.mkdir(exist_ok=True)
    
    async def cleanup_old_files(self, max_age_hours: int = 24):
        """
        指定時間より古いファイルをクリーンアップする
        """
        import time
        
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for directory in [self.upload_dir, self.download_dir]:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        try:
                            file_path.unlink()
                            print(f"削除: {file_path}")
                        except Exception as e:
                            print(f"ファイル削除エラー {file_path}: {e}")
    
    async def get_file_size(self, file_path: Path) -> int:
        """
        ファイルサイズを取得（バイト単位）
        """
        try:
            return file_path.stat().st_size
        except Exception:
            return 0
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        ファイルサイズを人間が読める形式にフォーマット
        """
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"
    
    async def validate_file_type(self, filename: str, allowed_extensions: List[str]) -> bool:
        """
        ファイルタイプを検証
        """
        file_ext = Path(filename).suffix.lower()
        return file_ext in [ext.lower() for ext in allowed_extensions]
    
    async def get_unique_filename(self, directory: Path, filename: str) -> str:
        """
        ディレクトリ内で一意のファイル名を生成
        """
        base_name = Path(filename).stem
        extension = Path(filename).suffix
        counter = 1
        
        unique_filename = filename
        while (directory / unique_filename).exists():
            unique_filename = f"{base_name}_{counter}{extension}"
            counter += 1
        
        return unique_filename
    
    def is_image_file(self, filename: str) -> bool:
        """
        画像ファイルかどうかを判定
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
        return Path(filename).suffix.lower() in image_extensions
    
    def is_video_file(self, filename: str) -> bool:
        """
        動画ファイルかどうかを判定
        """
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
        return Path(filename).suffix.lower() in video_extensions
    
    def is_audio_file(self, filename: str) -> bool:
        """
        音声ファイルかどうかを判定
        """
        audio_extensions = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}
        return Path(filename).suffix.lower() in audio_extensions
    
    async def copy_file(self, source: Path, destination: Path) -> bool:
        """
        ファイルを非同期でコピー
        """
        try:
            async with aiofiles.open(source, 'rb') as src:
                async with aiofiles.open(destination, 'wb') as dst:
                    while True:
                        chunk = await src.read(8192)
                        if not chunk:
                            break
                        await dst.write(chunk)
            return True
        except Exception as e:
            print(f"ファイルコピーエラー: {e}")
            return False
    
    async def move_file(self, source: Path, destination: Path) -> bool:
        """
        ファイルを移動
        """
        try:
            shutil.move(str(source), str(destination))
            return True
        except Exception as e:
            print(f"ファイル移動エラー: {e}")
            return False
    
    def get_mime_type(self, filename: str) -> str:
        """
        ファイル名からMIMEタイプを取得
        """
        import mimetypes
        
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or 'application/octet-stream'
