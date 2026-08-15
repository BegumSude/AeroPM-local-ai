import pytest

from backend.core.chunker import chunk_text


def test_long_text_splits_into_multiple_chunks():
    text = "a" * 2000
    chunks = chunk_text(text, chunk_size=800, overlap=150)

    assert len(chunks) == 3
    assert all(len(chunk["chunk_text"]) <= 800 for chunk in chunks)


def test_consecutive_chunks_share_expected_overlap():
    text = "a" * 2000
    chunk_size, overlap = 800, 150
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

    for previous, current in zip(chunks, chunks[1:]):
        assert previous["end_char"] - current["start_char"] == overlap


def test_start_and_end_char_positions_are_correct():
    text = "0123456789" * 100
    chunks = chunk_text(text, chunk_size=800, overlap=150)

    for chunk in chunks:
        assert chunk["chunk_text"] == text[chunk["start_char"]:chunk["end_char"]]


def test_chunk_index_is_sequential():
    text = "a" * 2000
    chunks = chunk_text(text, chunk_size=800, overlap=150)

    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))


def test_short_text_returns_single_chunk():
    text = "kisa bir metin"
    chunks = chunk_text(text, chunk_size=800, overlap=150)

    assert len(chunks) == 1
    assert chunks[0] == {
        "chunk_index": 0,
        "chunk_text": text,
        "start_char": 0,
        "end_char": len(text),
    }


def test_text_ending_exactly_on_chunk_boundary_has_no_empty_chunk():
    text = "a" * 1300
    chunks = chunk_text(text, chunk_size=800, overlap=150)

    assert len(chunks) == 2
    assert chunks[-1]["end_char"] == len(text)
    assert all(len(chunk["chunk_text"]) > 0 for chunk in chunks)


def test_overlap_greater_or_equal_to_chunk_size_raises():
    with pytest.raises(ValueError):
        chunk_text("herhangi bir metin", chunk_size=800, overlap=800)


def test_negative_chunk_size_raises():
    with pytest.raises(ValueError):
        chunk_text("herhangi bir metin", chunk_size=-10, overlap=0)


def test_negative_overlap_raises():
    with pytest.raises(ValueError):
        chunk_text("herhangi bir metin", chunk_size=800, overlap=-10)


def test_empty_text_returns_empty_list():
    assert chunk_text("", chunk_size=800, overlap=150) == []
