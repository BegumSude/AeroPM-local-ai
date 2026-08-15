from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_FILE_TYPES = {"pdf", "docx", "txt", "md"}


class UnsupportedFileTypeError(ValueError):
    pass


def load_document(file_path: str) -> dict:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dosya bulunamadi: {file_path}")

    file_type = path.suffix.lower().lstrip(".")
    if file_type not in SUPPORTED_FILE_TYPES:
        raise UnsupportedFileTypeError(f"Desteklenmeyen dosya turu: .{file_type}")

    if file_type == "pdf":
        text = _read_pdf(path)
    elif file_type == "docx":
        text = _read_docx(path)
    else:
        text = _read_text(path)

    return {
        "filename": path.name,
        "file_type": file_type,
        "text": text,
        "metadata": {
            "char_count": len(text),
            "word_count": len(text.split()),
        },
    }


def _read_pdf(path: Path) -> str:
    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages).strip()


def _read_docx(path: Path) -> str:
    document = Document(str(path))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    return "\n".join(paragraphs).strip()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()
