import uuid
from pathlib import Path
from typing import BinaryIO, Protocol


class StorageProvider(Protocol):
    def generate_safe_storage_key(
        self, assessment_id: uuid.UUID, evidence_request_id: uuid.UUID, extension: str
    ) -> str: ...

    def save_file(self, storage_key: str, source: BinaryIO) -> int: ...

    def open_file(self, storage_key: str) -> BinaryIO: ...

    def delete_file(self, storage_key: str) -> None: ...

    def resolve_path(self, storage_key: str) -> Path: ...
