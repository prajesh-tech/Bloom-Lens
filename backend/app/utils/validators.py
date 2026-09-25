import os
import re
import zipfile
from io import BytesIO
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings
from app.core.errors import raise_api_error


SUPPORTED_EXAM_TYPES = [
    "Mid-Term",
    "Internal",
    "Unit Test",
    "End-Semester",
    "Model Examination",
    "Quiz",
    "Other",
]

ALLOWED_MIME_TYPES = {
    ".pdf": {"application/pdf", "application/x-pdf"},
    ".docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
}


def validate_paper_upload(
    file: UploadFile, maximum_marks: float, examination_type: str
) -> Tuple[str, str]:
    """
    Validates uploaded question paper file format, size, maximum marks, and exam type.
    Returns (filename, extension). Raises HTTPException on failure.
    """
    if maximum_marks <= 0:
        raise_api_error(status.HTTP_400_BAD_REQUEST, "InvalidMaximumMarks", "Maximum marks must be greater than 0.")

    if not examination_type or not examination_type.strip():
        raise_api_error(status.HTTP_400_BAD_REQUEST, "InvalidExamType", "Examination type cannot be empty.")

    normalized_exam_type = examination_type.strip()
    if normalized_exam_type not in SUPPORTED_EXAM_TYPES:
        raise_api_error(
            status.HTTP_400_BAD_REQUEST,
            "UnsupportedExamType",
            f"Unsupported examination type '{normalized_exam_type}'. Supported types: {', '.join(SUPPORTED_EXAM_TYPES)}",
        )

    if not file.filename:
        raise_api_error(status.HTTP_400_BAD_REQUEST, "EmptyFilename", "Filename cannot be empty.")

    orig_filename = safe_filename(file.filename)
    ext = os.path.splitext(orig_filename)[1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise_api_error(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "UnsupportedFileExtension",
            f"Unsupported file format '{ext}'. Only .pdf and .docx files are supported.",
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_MIME_TYPES.get(ext, set()):
        raise_api_error(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "UnsupportedMimeType",
            f"Unsupported MIME type for {ext} upload.",
        )

    # File size validation (convert MB to bytes)
    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise_api_error(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "FileTooLarge",
            f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    if file_size == 0:
        raise_api_error(status.HTTP_400_BAD_REQUEST, "EmptyUpload", "Uploaded file is empty (0 bytes).")

    return orig_filename, ext


async def read_and_validate_upload(file: UploadFile, maximum_marks: float, examination_type: str) -> Tuple[str, str, bytes]:
    """Validates metadata, size, MIME type, and magic bytes, returning safe filename and content."""
    orig_filename, ext = validate_paper_upload(file, maximum_marks, examination_type)
    content = await file.read()

    if not content:
        raise_api_error(status.HTTP_400_BAD_REQUEST, "EmptyUpload", "Uploaded file is empty (0 bytes).")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise_api_error(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "FileTooLarge",
            f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB.",
        )

    if ext == ".pdf" and not content.startswith(b"%PDF-"):
        raise_api_error(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "InvalidFileSignature", "PDF content signature is invalid.")

    if ext == ".docx":
        try:
            with zipfile.ZipFile(BytesIO(content)) as archive:
                names = set(archive.namelist())
                if "[Content_Types].xml" not in names or "word/document.xml" not in names:
                    raise zipfile.BadZipFile
        except zipfile.BadZipFile:
            raise_api_error(
                status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                "InvalidFileSignature",
                "DOCX content signature is invalid.",
            )

    await file.seek(0)
    return orig_filename, ext, content


def safe_filename(filename: str) -> str:
    """Returns a basename-only, filesystem-safe upload filename while preserving extension."""
    basename = os.path.basename(filename).strip().replace("\x00", "")
    root, ext = os.path.splitext(basename)
    cleaned_root = re.sub(r"[^A-Za-z0-9._-]+", "_", root).strip("._")
    cleaned_ext = re.sub(r"[^A-Za-z0-9.]+", "", ext).strip()

    if not cleaned_root and not cleaned_ext:
        raise_api_error(status.HTTP_400_BAD_REQUEST, "EmptyFilename", "Filename cannot be empty.")

    if not cleaned_root:
        cleaned_root = "upload"

    max_root_len = max(1, 180 - len(cleaned_ext))
    cleaned_root = cleaned_root[:max_root_len]
    return f"{cleaned_root}{cleaned_ext}"


def safe_upload_path(upload_dir: str, filename: str) -> str:
    """Builds an upload path guaranteed to stay under upload_dir."""
    base_dir = os.path.abspath(upload_dir)
    os.makedirs(base_dir, exist_ok=True)
    path = os.path.abspath(os.path.join(base_dir, filename))
    if os.path.commonpath([base_dir, path]) != base_dir:
        raise_api_error(status.HTTP_400_BAD_REQUEST, "UnsafeUploadPath", "Unsafe upload filename.")
    return path
