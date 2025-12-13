from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
import os
import uuid
import aiofiles
from pathlib import Path
from typing import Optional

from app.services.image_converter import ImageConverter
from app.services.video_converter import VideoConverter
from app.services.audio_converter import AudioConverter
from app.utils.file_handler import FileHandler

router = APIRouter(prefix="/api/convert", tags=["conversion"])

# サポートされるファイル形式
IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.svg'}
VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
AUDIO_FORMATS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'}

def get_file_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext in IMAGE_FORMATS:
        return "image"
    elif ext in VIDEO_FORMATS:
        return "video"
    elif ext in AUDIO_FORMATS:
        return "audio"
    else:
        raise HTTPException(status_code=400, detail="サポートされていないファイル形式です")

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # ファイルタイプの検証
        file_type = get_file_type(file.filename)
        
        # 一意のファイル名を生成
        file_id = str(uuid.uuid4())
        file_ext = Path(file.filename).suffix
        filename = f"{file_id}{file_ext}"
        file_path = Path("uploads") / filename
        
        # ファイルを保存
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "file_type": file_type,
            "file_path": str(file_path),
            "size": len(content)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ファイルアップロードエラー: {str(e)}")

@router.post("/process")
async def process_conversion(
    file_id: str = Form(...),
    output_format: str = Form(...),
    quality: Optional[str] = Form(None),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None)
):
    try:
        # 入力ファイルの検索
        input_files = list(Path("uploads").glob(f"{file_id}.*"))
        if not input_files:
            raise HTTPException(status_code=404, detail="ファイルが見つかりません")
        
        input_path = input_files[0]
        file_type = get_file_type(str(input_path))
        
        # 出力ファイルパスの生成
        output_filename = f"{file_id}_converted.{output_format}"
        output_path = Path("downloads") / output_filename
        
        # 変換処理
        if file_type == "image":
            converter = ImageConverter()
            await converter.convert(input_path, output_path, output_format, quality, width, height)
        elif file_type == "video":
            try:
                converter = VideoConverter()
                await converter.convert(input_path, output_path, output_format, quality)
            except RuntimeError as e:
                # FFmpegがインストールされていない場合
                raise HTTPException(status_code=503, detail=str(e))
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"動画変換エラー: {str(e)}")
        elif file_type == "audio":
            try:
                converter = AudioConverter()
                await converter.convert(input_path, output_path, output_format, quality)
            except Exception as e:
                import traceback
                error_detail = traceback.format_exc()
                print(f"音声変換エラーの詳細:\n{error_detail}")
                raise HTTPException(status_code=500, detail=f"音声変換エラー: {str(e)}")

        # 変換完了後、元のアップロードファイルを削除
        file_handler = FileHandler()
        await file_handler.delete_file(input_path)

        return {
            "success": True,
            "download_url": f"/api/convert/download/{output_filename}",
            "output_filename": output_filename
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"変換エラー: {str(e)}")

@router.get("/download/{filename}")
async def download_file(filename: str):
    file_path = Path("downloads") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="ファイルが見つかりません")

    # ダウンロード後にファイルを削除するためのバックグラウンドタスクを追加
    from fastapi import BackgroundTasks
    from starlette.background import BackgroundTask

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream',
        background=BackgroundTask(cleanup_downloaded_file, file_path)
    )

async def cleanup_downloaded_file(file_path: Path):
    """
    ダウンロード完了後にファイルを削除
    """
    try:
        if file_path.exists():
            file_path.unlink()
            print(f"ダウンロード済みファイルを削除しました: {file_path}")
    except Exception as e:
        print(f"ダウンロード済みファイルの削除エラー: {e}")

@router.get("/formats/{file_type}")
async def get_supported_formats(file_type: str):
    if file_type == "image":
        return {"formats": ["jpeg", "png", "webp", "gif", "bmp", "tiff"]}
    elif file_type == "video":
        return {"formats": ["mp4", "avi", "mov", "mkv", "webm", "gif"]}
    elif file_type == "audio":
        return {"formats": ["mp3", "wav", "flac", "aac", "ogg"]}
    else:
        raise HTTPException(status_code=400, detail="無効なファイルタイプです")
