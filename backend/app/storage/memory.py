import io
import uuid
from pathlib import Path
from typing import BinaryIO

from app.core.errors import AppError


class MemoryStorageProvider:
    """Small deterministic storage provider for unit and integration tests."""

    def __init__(self) -> None:
        self._files: dict[str, bytes] = {}

    def generate_safe_storage_key(
        self, assessment_id: uuid.UUID, evidence_request_id: uuid.UUID, extension: str
    ) -> str:
        safe_extension = extension.lower().lstrip(".")
        if safe_extension not in {"jpg", "jpeg", "png", "webp", "pdf"}:
            raise AppError("invalid_file_extension", "Unsupported file extension.", 415)
        return f"{assessment_id}/{evidence_request_id}/{uuid.uuid4().hex}.{safe_extension}"

    def save_file(self, storage_key: str, source: BinaryIO) -> int:
        data = source.read()
        self._files[storage_key] = data
        return len(data)

    def open_file(self, storage_key: str) -> BinaryIO:
        try:
            return io.BytesIO(self._files[storage_key])
        except KeyError as exc:
            raise FileNotFoundError(storage_key) from exc

    def delete_file(self, storage_key: str) -> None:
        self._files.pop(storage_key, None)

    def resolve_path(self, storage_key: str) -> Path:
        return Path(storage_key)
