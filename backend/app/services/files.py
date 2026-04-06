from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from pypdf import PdfReader

from ..database import UPLOADS_DIR


def slugify(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-").lower() or "file"


def save_upload(upload: UploadFile, category: str) -> tuple[str, str]:
    suffix = Path(upload.filename or "").suffix or ".bin"
    file_name = f"{slugify(Path(upload.filename or 'upload').stem)}-{uuid4().hex[:8]}{suffix}"
    target_dir = UPLOADS_DIR / category
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / file_name

    upload.file.seek(0)
    with target_path.open("wb") as handle:
        handle.write(upload.file.read())
    upload.file.seek(0)
    return target_path.as_posix(), file_name


def extract_text_from_path(file_path: str) -> str:
    path = Path(file_path)
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    if path.suffix.lower() in {".txt", ".md"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    return ""
