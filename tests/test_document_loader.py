from pathlib import Path

import pytest

from backend.core.document_loader import UnsupportedFileTypeError, load_document

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


def test_load_txt():
    result = load_document(str(SAMPLES_DIR / "sample.txt"))
    assert result["filename"] == "sample.txt"
    assert result["file_type"] == "txt"
    assert "test metin dosyasidir" in result["text"]
    assert result["metadata"]["char_count"] == len(result["text"])
    assert result["metadata"]["word_count"] == len(result["text"].split())


def test_load_markdown():
    result = load_document(str(SAMPLES_DIR / "sample.md"))
    assert result["file_type"] == "md"
    assert "Baslik" in result["text"]
    assert result["metadata"]["word_count"] > 0


def test_load_docx():
    result = load_document(str(SAMPLES_DIR / "sample.docx"))
    assert result["file_type"] == "docx"
    assert "test docx dosyasidir" in result["text"]
    assert result["metadata"]["char_count"] > 0


def test_load_pdf():
    result = load_document(str(SAMPLES_DIR / "sample.pdf"))
    assert result["file_type"] == "pdf"
    assert "test pdf dosyasidir" in result["text"]
    assert result["metadata"]["char_count"] > 0


def test_load_unsupported_file_type_raises(tmp_path):
    unsupported_file = tmp_path / "sample.xyz"
    unsupported_file.write_text("icerik")

    with pytest.raises(UnsupportedFileTypeError):
        load_document(str(unsupported_file))


def test_load_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_document(str(SAMPLES_DIR / "eksik_dosya.txt"))
