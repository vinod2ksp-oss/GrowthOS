from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import get_settings

settings = get_settings()


class StorageService:
    def __init__(self) -> None:
        self.root = Path(settings.upload_dir)
        self.root.mkdir(parents=True, exist_ok=True)
        self.allowed_extensions = {
            item.strip().lower() for item in settings.allowed_upload_extensions.split(",") if item.strip()
        }

    def validate(self, file: UploadFile) -> None:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in self.allowed_extensions:
            raise ValueError("不支持该文件类型")
        if file.size and file.size > settings.max_upload_size:
            raise ValueError("文件过大")

    def save(self, file: UploadFile) -> tuple[str, str]:
        self.validate(file)
        extension = Path(file.filename or "").suffix.lower()
        unique_name = f"{uuid4()}{extension}"
        destination = self.root / unique_name
        contents = file.file.read()
        destination.write_bytes(contents)
        return destination.as_posix(), unique_name

    def remove(self, file_path: str) -> None:
        path = Path(file_path)
        if path.exists():
            path.unlink()
