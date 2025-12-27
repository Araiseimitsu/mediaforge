from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import FileResponse
import uuid
import asyncio
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from app.services.image_converter import ImageConverter
from app.services.video_converter import VideoConverter
from app.services.audio_converter import AudioConverter
from app.utils.file_handler import FileHandler
from app.utils.gcs import (
    get_bucket_name,
    get_signed_url_expiration_minutes,
    get_delete_delay_minutes,
    parse_gcs_uri,
    generate_signed_upload_url,
    generate_signed_download_url,
    download_blob_to_file,
    upload_file_to_blob,
    delete_blob,
    delete_blob_after_delay
)

router = APIRouter(prefix="/api/convert", tags=["conversion"])
logger = logging.getLogger(__name__)

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

class UploadRequest(BaseModel):
    filename: str
    content_type: Optional[str] = None
    size: Optional[int] = None


@router.post("/upload")
async def create_upload_url(payload: UploadRequest):
    try:
        file_type = get_file_type(payload.filename)
        file_id = str(uuid.uuid4())
        file_ext = Path(payload.filename).suffix
        object_name = f"uploads/{file_id}{file_ext}"
        bucket_name = get_bucket_name()
        upload_url = generate_signed_upload_url(
            bucket_name=bucket_name,
            object_name=object_name,
            content_type=payload.content_type
        )

        return {
            "file_id": file_id,
            "file_type": file_type,
            "original_filename": payload.filename,
            "gcs_uri": f"gs://{bucket_name}/{object_name}",
            "object_name": object_name,
            "upload_url": upload_url,
            "expires_in_minutes": get_signed_url_expiration_minutes()
        }
    
    except Exception as e:
        logger.exception("アップロードURL生成エラー: %s", e)
        raise HTTPException(status_code=500, detail="アップロードURL生成エラー")

@router.post("/process")
async def process_conversion(
    gcs_uri: str = Form(...),
    file_id: Optional[str] = Form(None),
    output_format: str = Form(...),
    quality: Optional[str] = Form(None),
    width: Optional[int] = Form(None),
    height: Optional[int] = Form(None)
):
    try:
        logger.info("変換開始: gcs_uri=%s output_format=%s quality=%s width=%s height=%s", gcs_uri, output_format, quality, width, height)
        bucket_name, object_name = parse_gcs_uri(gcs_uri)
        expected_bucket = get_bucket_name()
        if bucket_name != expected_bucket:
            raise HTTPException(status_code=400, detail="無効なGCSバケットです")

        object_path = Path(object_name)
        file_ext = object_path.suffix
        inferred_file_id = object_path.stem
        file_id = file_id or inferred_file_id

        input_path = Path("uploads") / f"{file_id}{file_ext}"
        output_filename = f"{file_id}_converted.{output_format}"
        output_path = Path("downloads") / output_filename

        await asyncio.to_thread(
            download_blob_to_file,
            bucket_name,
            object_name,
            input_path
        )
        logger.info("GCSダウンロード完了: %s -> %s", object_name, input_path)

        file_type = get_file_type(object_name)
        logger.info("ファイルタイプ判定: %s", file_type)

        if file_type == "image":
            converter = ImageConverter()
            await converter.convert(input_path, output_path, output_format, quality, width, height)
        elif file_type == "video":
            try:
                logger.info("動画変換開始: %s -> %s", input_path, output_path)
                converter = VideoConverter()
                await converter.convert(input_path, output_path, output_format, quality)
                logger.info("動画変換完了: %s", output_path)
            except RuntimeError as e:
                logger.exception("動画変換エラー(FFmpeg未検出の可能性): %s", e)
                raise HTTPException(status_code=503, detail=str(e))
            except Exception as e:
                logger.exception("動画変換エラー: %s", e)
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

        output_object_name = f"outputs/{output_filename}"
        await asyncio.to_thread(
            upload_file_to_blob,
            bucket_name,
            output_object_name,
            output_path,
            "application/octet-stream"
        )
        logger.info("GCSアップロード完了: %s", output_object_name)

        try:
            await asyncio.to_thread(delete_blob, bucket_name, object_name)
        except Exception as e:
            logger.warning("入力オブジェクト削除に失敗: %s (%s)", object_name, e)

        delete_delay = get_delete_delay_minutes()
        asyncio.create_task(delete_blob_after_delay(bucket_name, output_object_name, delete_delay))
        logger.info("削除スケジュール: %s を %s 分後に削除", output_object_name, delete_delay)

        download_url = generate_signed_download_url(bucket_name, output_object_name)

        file_handler = FileHandler()
        await file_handler.delete_file(input_path)
        await file_handler.delete_file(output_path)

        return {
            "success": True,
            "download_url": download_url,
            "output_filename": output_filename,
            "expires_in_minutes": get_signed_url_expiration_minutes(),
            "delete_in_minutes": delete_delay
        }
    
    except Exception as e:
        logger.exception("変換エラー: %s", e)
        raise HTTPException(status_code=500, detail="変換エラー")

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
