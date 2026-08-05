import os
import uuid
from pathlib import Path
from typing import BinaryIO

from app.core.errors import AppError


class LocalStorageProvider:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def generate_safe_storage_key(
        self, assessment_id: uuid.UUID, evidence_request_id: uuid.UUID, extension: str
    ) -> str:
        safe_extension = extension.lower().lstrip(".")
        if safe_extension not in {"jpg", "jpeg", "png", "webp", "pdf"}:
            raise AppError("invalid_file_extension", "Unsupported file extension.", 415)
        return f"{assessment_id}/{evidence_request_id}/{uuid.uuid4().hex}.{safe_extension}"

    def resolve_path(self, storage_key: str) -> Path:
        if Path(storage_key).is_absolute() or ".." in Path(storage_key).parts:
            raise AppError("invalid_storage_key", "Invalid storage key.", 400)
        path = (self.root / storage_key).resolve()
        try:
            path.relative_to(self.root)
        except ValueError as exc:
            raise AppError("invalid_storage_key", "Invalid storage key.", 400) from exc
        return path

    def save_file(self, storage_key: str, source: BinaryIO) -> int:
        path = self.resolve_path(storage_key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".part")
        size = 0
        try:
            with temporary.open("wb") as destination:
                while chunk := source.read(1024 * 1024):
                    size += len(chunk)
                    destination.write(chunk)
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
        return size

    def open_file(self, storage_key: str) -> BinaryIO:
        return self.resolve_path(storage_key).open("rb")

    def delete_file(self, storage_key: str) -> None:
        path = self.resolve_path(storage_key)
        if path.exists():
            path.unlink()
