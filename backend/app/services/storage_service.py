from pathlib import Path, PurePosixPath
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings


class StorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self.root = settings.storage_root
        self.root.mkdir(parents=True, exist_ok=True)
        self.max_size = settings.max_upload_size
        self.allowed_extensions = {item.strip().lower() for item in settings.allowed_upload_extensions.split(",") if item.strip()}

    def validate(self, file: UploadFile) -> None:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in self.allowed_extensions:
            raise ValueError("Unsupported file type")
        if file.size and file.size > self.max_size:
            raise ValueError("File exceeds MAX_UPLOAD_SIZE")

    def resolve(self, storage_key: str) -> Path:
        key = PurePosixPath(storage_key.replace("\\", "/"))
        if key.is_absolute() or ".." in key.parts:
            raise ValueError("Invalid storage key")
        path = (self.root / Path(*key.parts)).resolve()
        if path != self.root and self.root not in path.parents:
            raise ValueError("Invalid storage key")
        return path

    def save(self, file: UploadFile, prefix: str = "evidence") -> tuple[str, str]:
        self.validate(file)
        suffix = Path(file.filename or "").suffix.lower()
        content = file.file.read(self.max_size + 1)
        if not content or len(content) > self.max_size:
            raise ValueError("File is empty or exceeds MAX_UPLOAD_SIZE")
        unique_name = f"{uuid4().hex}{suffix}"
        key = f"{prefix.strip('/')}/{unique_name}"
        destination = self.resolve(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        return key, unique_name

    def remove(self, storage_key: str) -> None:
        path = self.resolve(storage_key)
        if path.is_file():
            path.unlink()
