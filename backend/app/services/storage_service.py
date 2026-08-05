import re
import uuid
from pathlib import Path
from typing import BinaryIO

from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.models.enums import EvidenceKind
from app.storage import LocalStorageProvider, StorageProvider

IMAGE_MIME_EXTENSIONS = {
    "image/jpeg": {"jpg", "jpeg"},
    "image/png": {"png"},
    "image/webp": {"webp"},
}
DOCUMENT_MIME_EXTENSIONS = {"application/pdf": {"pdf"}}


def get_storage_provider(settings: Settings | None = None) -> StorageProvider:
    return LocalStorageProvider((settings or get_settings()).upload_dir)


def sanitize_original_filename(filename: str) -> str:
    name = Path(filename).name
    name = re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "_", name).strip(" .")
    return (name or "upload")[:200]


def validate_upload(
    *,
    filename: str,
    content_type: str,
    data: bytes,
    kind: EvidenceKind,
    settings: Settings | None = None,
) -> str:
    config = settings or get_settings()
    extension = Path(filename).suffix.lower().lstrip(".")
    allowed = IMAGE_MIME_EXTENSIONS if kind == EvidenceKind.PHOTO else DOCUMENT_MIME_EXTENSIONS
    if content_type not in allowed or extension not in allowed[content_type]:
        raise AppError(
            "unsupported_file_type",
            "Photos must be JPEG, PNG, or WebP; documents must be PDF.",
            415,
        )
    limit_mb = config.max_image_mb if kind == EvidenceKind.PHOTO else config.max_pdf_mb
    if len(data) > limit_mb * 1024 * 1024:
        raise AppError("file_too_large", f"File exceeds the {limit_mb} MB limit.", 413)
    signatures = {
        "image/jpeg": data.startswith(b"\xff\xd8\xff"),
        "image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        "image/webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
        "application/pdf": data.startswith(b"%PDF-"),
    }
    if not signatures.get(content_type, False):
        raise AppError(
            "file_content_mismatch", "File content does not match its declared type.", 415
        )
    return extension


def generate_safe_storage_key(
    provider: StorageProvider,
    assessment_id: uuid.UUID,
    evidence_request_id: uuid.UUID,
    extension: str,
) -> str:
    return provider.generate_safe_storage_key(assessment_id, evidence_request_id, extension)


def save_file(provider: StorageProvider, storage_key: str, source: BinaryIO) -> int:
    return provider.save_file(storage_key, source)


def open_file(provider: StorageProvider, storage_key: str) -> BinaryIO:
    return provider.open_file(storage_key)


def delete_file(provider: StorageProvider, storage_key: str) -> None:
    provider.delete_file(storage_key)
