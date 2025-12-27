import os
import asyncio
import logging
from datetime import timedelta
from pathlib import Path
from typing import Tuple, Optional

import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request
from google.cloud import storage

logger = logging.getLogger(__name__)


def get_bucket_name() -> str:
    bucket = os.getenv("GCS_BUCKET")
    if not bucket:
        raise ValueError("GCS_BUCKET が設定されていません")
    return bucket


def get_signed_url_expiration_minutes() -> int:
    return int(os.getenv("SIGNED_URL_EXPIRATION_MINUTES", "10"))


def get_delete_delay_minutes() -> int:
    return int(os.getenv("DELETE_DELAY_MINUTES", "5"))


def create_storage_client() -> storage.Client:
    credentials, project = google.auth.default()
    return storage.Client(credentials=credentials, project=project)


def get_service_account_email(credentials) -> str:
    email = getattr(credentials, "service_account_email", None)
    if not email:
        email = os.getenv("GOOGLE_SERVICE_ACCOUNT_EMAIL")
    if not email:
        raise ValueError("サービスアカウントのメールアドレスを特定できません")
    return email


def get_signing_credentials() -> impersonated_credentials.Credentials:
    source_credentials, _ = google.auth.default()
    if not source_credentials.valid:
        source_credentials.refresh(Request())
    target_principal = get_service_account_email(source_credentials)
    return impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=target_principal,
        target_scopes=["https://www.googleapis.com/auth/devstorage.read_write"],
        lifetime=3600
    )


def parse_gcs_uri(gcs_uri: str) -> Tuple[str, str]:
    if not gcs_uri.startswith("gs://"):
        raise ValueError("gcs_uri の形式が不正です")
    parts = gcs_uri[5:].split("/", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError("gcs_uri の形式が不正です")
    return parts[0], parts[1]


def generate_signed_upload_url(
    bucket_name: str,
    object_name: str,
    content_type: Optional[str] = None
) -> str:
    client = create_storage_client()
    blob = client.bucket(bucket_name).blob(object_name)
    signing_credentials = get_signing_credentials()
    expiration = timedelta(minutes=get_signed_url_expiration_minutes())
    return blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method="PUT",
        content_type=content_type or "application/octet-stream",
        credentials=signing_credentials
    )


def generate_signed_download_url(bucket_name: str, object_name: str) -> str:
    client = create_storage_client()
    blob = client.bucket(bucket_name).blob(object_name)
    signing_credentials = get_signing_credentials()
    expiration = timedelta(minutes=get_signed_url_expiration_minutes())
    return blob.generate_signed_url(
        version="v4",
        expiration=expiration,
        method="GET",
        credentials=signing_credentials
    )


def download_blob_to_file(
    bucket_name: str,
    object_name: str,
    destination_path: Path
) -> None:
    client = create_storage_client()
    blob = client.bucket(bucket_name).blob(object_name)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    blob.download_to_filename(str(destination_path))


def upload_file_to_blob(
    bucket_name: str,
    object_name: str,
    source_path: Path,
    content_type: Optional[str] = None
) -> None:
    client = create_storage_client()
    blob = client.bucket(bucket_name).blob(object_name)
    blob.upload_from_filename(
        str(source_path),
        content_type=content_type or "application/octet-stream"
    )


def delete_blob(bucket_name: str, object_name: str) -> None:
    client = create_storage_client()
    blob = client.bucket(bucket_name).blob(object_name)
    blob.delete()


async def delete_blob_after_delay(
    bucket_name: str,
    object_name: str,
    delay_minutes: int
) -> None:
    if delay_minutes <= 0:
        delay_minutes = 0
    if delay_minutes:
        await asyncio.sleep(delay_minutes * 60)
    await asyncio.to_thread(delete_blob, bucket_name, object_name)
