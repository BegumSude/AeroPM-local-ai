import json

import numpy as np
import pytest

from backend.core.chunker import chunk_text
from backend.core.rag_service import ask_question, index_document
from backend.database.db import get_connection, init_db


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_rag.db")
    init_db(path)
    return path


@pytest.fixture
def sample_file(tmp_path):
    path = tmp_path / "sample.txt"
    path.write_text("Bu bir test belgesidir. " * 100)
    return str(path)


@pytest.fixture
def collection_id(db_path):
    connection = get_connection(db_path)
    collection_id = connection.execute(
        "INSERT INTO collections (name) VALUES (?)", ("koleksiyon",)
    ).lastrowid
    connection.commit()
    connection.close()
    return collection_id


def _fake_embed_texts(call_log=None):
    def fake(texts):
        if call_log is not None:
            call_log.append(list(texts))
        vectors = [[1.0, 0.0] if i == 0 else [0.0, 1.0] for i in range(len(texts))]
        return np.array(vectors, dtype=np.float32)

    return fake


def test_index_document_follows_loader_chunker_embedder_order(monkeypatch, db_path, sample_file, collection_id):
    call_log = []
    monkeypatch.setattr("backend.core.rag_service.embed_texts", _fake_embed_texts(call_log))

    index_document(sample_file, collection_id, db_path=db_path)

    with open(sample_file, encoding="utf-8") as file:
        document_text = file.read().strip()
    expected_texts = [chunk["chunk_text"] for chunk in chunk_text(document_text)]
    assert call_log == [expected_texts]


def test_document_and_chunks_are_saved_to_sqlite(monkeypatch, db_path, sample_file, collection_id):
    monkeypatch.setattr("backend.core.rag_service.embed_texts", _fake_embed_texts())

    result = index_document(sample_file, collection_id, db_path=db_path)

    connection = get_connection(db_path)
    document_row = connection.execute(
        "SELECT * FROM documents WHERE id = ?", (result["document_id"],)
    ).fetchone()
    chunk_rows = connection.execute(
        "SELECT * FROM chunks WHERE document_id = ? ORDER BY chunk_index", (result["document_id"],)
    ).fetchall()
    connection.close()

    assert document_row["filename"] == "sample.txt"
    assert document_row["collection_id"] == collection_id
    assert len(chunk_rows) == result["chunk_count"]
    assert chunk_rows[0]["chunk_index"] == 0


def test_embeddings_are_stored_as_blob(monkeypatch, db_path, sample_file, collection_id):
    monkeypatch.setattr("backend.core.rag_service.embed_texts", _fake_embed_texts())

    result = index_document(sample_file, collection_id, db_path=db_path)

    connection = get_connection(db_path)
    chunk_rows = connection.execute(
        "SELECT embedding FROM chunks WHERE document_id = ? ORDER BY chunk_index", (result["document_id"],)
    ).fetchall()
    connection.close()

    assert isinstance(chunk_rows[0]["embedding"], bytes)
    first_embedding = np.frombuffer(chunk_rows[0]["embedding"], dtype=np.float32)
    assert list(first_embedding) == [1.0, 0.0]


def test_index_document_return_value(monkeypatch, db_path, sample_file, collection_id):
    monkeypatch.setattr("backend.core.rag_service.embed_texts", _fake_embed_texts())

    result = index_document(sample_file, collection_id, db_path=db_path)

    assert result["filename"] == "sample.txt"
    assert result["chunk_count"] > 1
    assert isinstance(result["document_id"], int)


def test_ask_question_follows_embed_retrieve_generate_order(monkeypatch, db_path, sample_file, collection_id):
    monkeypatch.setattr("backend.core.rag_service.embed_texts", _fake_embed_texts())
    index_document(sample_file, collection_id, db_path=db_path)

    received_context = []

    def fake_generate_answer(question, context_chunks):
        received_context.append((question, context_chunks))
        return "FAKE_ANSWER"

    monkeypatch.setattr("backend.core.rag_service.generate_answer", fake_generate_answer)

    ask_question("test sorusu", collection_id, top_k=2, db_path=db_path)

    assert len(received_context) == 1
    question, context_chunks = received_context[0]
    assert question == "test sorusu"
    assert len(context_chunks) == 2
    assert context_chunks[0]["similarity_score"] >= context_chunks[1]["similarity_score"]


def test_ask_question_returns_answer_and_sources(monkeypatch, db_path, sample_file, collection_id):
    monkeypatch.setattr("backend.core.rag_service.embed_texts", _fake_embed_texts())
    index_document(sample_file, collection_id, db_path=db_path)
    monkeypatch.setattr("backend.core.rag_service.generate_answer", lambda question, context_chunks: "FAKE_ANSWER")

    result = ask_question("test sorusu", collection_id, top_k=3, db_path=db_path)

    assert result["answer"] == "FAKE_ANSWER"
    assert len(result["sources"]) == 3
    for source in result["sources"]:
        assert set(source.keys()) == {"document_name", "chunk_index", "similarity_score"}
    assert result["sources"][0]["similarity_score"] == pytest.approx(1.0)


def test_ask_question_saves_chat_history(monkeypatch, db_path, sample_file, collection_id):
    monkeypatch.setattr("backend.core.rag_service.embed_texts", _fake_embed_texts())
    index_document(sample_file, collection_id, db_path=db_path)
    monkeypatch.setattr("backend.core.rag_service.generate_answer", lambda question, context_chunks: "FAKE_ANSWER")

    ask_question("test sorusu", collection_id, top_k=2, db_path=db_path)

    connection = get_connection(db_path)
    row = connection.execute(
        "SELECT * FROM chat_history WHERE collection_id = ?", (collection_id,)
    ).fetchone()
    connection.close()

    assert row["question"] == "test sorusu"
    assert row["answer"] == "FAKE_ANSWER"
    assert row["response_time_ms"] >= 0
    assert len(json.loads(row["sources"])) == 2


def test_index_document_invalid_collection_id_raises(monkeypatch, db_path, sample_file):
    monkeypatch.setattr("backend.core.rag_service.embed_texts", _fake_embed_texts())

    with pytest.raises(ValueError):
        index_document(sample_file, 999, db_path=db_path)


def test_ask_question_invalid_collection_id_raises(monkeypatch, db_path):
    monkeypatch.setattr("backend.core.rag_service.embed_texts", _fake_embed_texts())

    with pytest.raises(ValueError):
        ask_question("soru", 999, db_path=db_path)


def test_ask_question_empty_question_raises(db_path, collection_id):
    with pytest.raises(ValueError):
        ask_question("   ", collection_id, db_path=db_path)


def test_duplicate_document_is_not_reindexed(monkeypatch, db_path, sample_file, collection_id):
    call_log = []
    monkeypatch.setattr("backend.core.rag_service.embed_texts", _fake_embed_texts(call_log))

    first_result = index_document(sample_file, collection_id, db_path=db_path)
    second_result = index_document(sample_file, collection_id, db_path=db_path)

    assert second_result == first_result
    assert len(call_log) == 1

    connection = get_connection(db_path)
    document_count = connection.execute(
        "SELECT COUNT(*) AS count FROM documents WHERE collection_id = ?", (collection_id,)
    ).fetchone()["count"]
    connection.close()

    assert document_count == 1
