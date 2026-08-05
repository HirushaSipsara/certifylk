import uuid
from pathlib import Path
from typing import BinaryIO

from app.core.errors import ConfigurationError


class S3StorageProvider:
    """Future provider boundary; Phase 1 deliberately contains no AWS calls."""

    def _unavailable(self) -> ConfigurationError:
        return ConfigurationError("S3 storage is outside the Phase 1 local MVP.")

    def generate_safe_storage_key(
        self, assessment_id: uuid.UUID, evidence_request_id: uuid.UUID, extension: str
    ) -> str:
        raise self._unavailable()

    def save_file(self, storage_key: str, source: BinaryIO) -> int:
        raise self._unavailable()

    def open_file(self, storage_key: str) -> BinaryIO:
        raise self._unavailable()

    def delete_file(self, storage_key: str) -> None:
        raise self._unavailable()

    def resolve_path(self, storage_key: str) -> Path:
        raise self._unavailable()
