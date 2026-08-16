import numpy as np
import pytest

from backend.core.retriever import find_relevant_chunks
from backend.database.db import get_connection, init_db


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_rag.db")
    init_db(path)
    return path


def _insert_collection(connection, name="koleksiyon"):
    return connection.execute("INSERT INTO collections (name) VALUES (?)", (name,)).lastrowid


def _insert_document(connection, collection_id, filename="sample.txt"):
    return connection.execute(
        "INSERT INTO documents (collection_id, filename, file_type) VALUES (?, ?, ?)",
        (collection_id, filename, "txt"),
    ).lastrowid


def _insert_chunk(connection, document_id, chunk_index, chunk_text, embedding):
    embedding_blob = np.asarray(embedding, dtype=np.float32).tobytes()
    connection.execute(
        "INSERT INTO chunks (document_id, chunk_index, chunk_text, start_char, end_char, embedding) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (document_id, chunk_index, chunk_text, 0, len(chunk_text), embedding_blob),
    )


def test_most_similar_chunk_is_ranked_first(db_path):
    connection = get_connection(db_path)
    collection_id = _insert_collection(connection)
    document_id = _insert_document(connection, collection_id)
    _insert_chunk(connection, document_id, 0, "alakasiz metin", [0.0, 1.0])
    _insert_chunk(connection, document_id, 1, "alakali metin", [1.0, 0.0])
    connection.commit()
    connection.close()

    results = find_relevant_chunks([1.0, 0.0], collection_id, top_k=5, db_path=db_path)

    assert results[0]["chunk_text"] == "alakali metin"


def test_similarity_score_is_correct(db_path):
    connection = get_connection(db_path)
    collection_id = _insert_collection(connection)
    document_id = _insert_document(connection, collection_id)
    _insert_chunk(connection, document_id, 0, "ayni yon", [1.0, 0.0])
    connection.commit()
    connection.close()

    results = find_relevant_chunks([1.0, 0.0], collection_id, top_k=5, db_path=db_path)

    assert results[0]["similarity_score"] == pytest.approx(1.0)


def test_top_k_limits_results(db_path):
    connection = get_connection(db_path)
    collection_id = _insert_collection(connection)
    document_id = _insert_document(connection, collection_id)
    for i in range(5):
        _insert_chunk(connection, document_id, i, f"metin {i}", [float(i), 1.0])
    connection.commit()
    connection.close()

    results = find_relevant_chunks([1.0, 1.0], collection_id, top_k=2, db_path=db_path)

    assert len(results) == 2


def test_collection_id_filters_chunks(db_path):
    connection = get_connection(db_path)
    collection_a = _insert_collection(connection, "a")
    collection_b = _insert_collection(connection, "b")
    document_a = _insert_document(connection, collection_a, "a.txt")
    document_b = _insert_document(connection, collection_b, "b.txt")
    _insert_chunk(connection, document_a, 0, "koleksiyon a metni", [1.0, 0.0])
    _insert_chunk(connection, document_b, 0, "koleksiyon b metni", [1.0, 0.0])
    connection.commit()
    connection.close()

    results = find_relevant_chunks([1.0, 0.0], collection_a, top_k=5, db_path=db_path)

    assert len(results) == 1
    assert results[0]["chunk_text"] == "koleksiyon a metni"


def test_no_chunks_returns_empty_list(db_path):
    connection = get_connection(db_path)
    collection_id = _insert_collection(connection)
    connection.commit()
    connection.close()

    results = find_relevant_chunks([1.0, 0.0], collection_id, top_k=5, db_path=db_path)

    assert results == []


def test_invalid_top_k_raises(db_path):
    with pytest.raises(ValueError):
        find_relevant_chunks([1.0, 0.0], 1, top_k=0, db_path=db_path)


def test_results_are_sorted_by_similarity_descending(db_path):
    connection = get_connection(db_path)
    collection_id = _insert_collection(connection)
    document_id = _insert_document(connection, collection_id)
    _insert_chunk(connection, document_id, 0, "dusuk benzerlik", [0.0, 1.0])
    _insert_chunk(connection, document_id, 1, "orta benzerlik", [0.7, 0.7])
    _insert_chunk(connection, document_id, 2, "yuksek benzerlik", [1.0, 0.0])
    connection.commit()
    connection.close()

    results = find_relevant_chunks([1.0, 0.0], collection_id, top_k=5, db_path=db_path)

    scores = [chunk["similarity_score"] for chunk in results]
    assert scores == sorted(scores, reverse=True)


def test_zero_vector_chunk_does_not_crash_and_scores_zero(db_path):
    connection = get_connection(db_path)
    collection_id = _insert_collection(connection)
    document_id = _insert_document(connection, collection_id)
    _insert_chunk(connection, document_id, 0, "sifir vektor", [0.0, 0.0])
    connection.commit()
    connection.close()

    results = find_relevant_chunks([1.0, 0.0], collection_id, top_k=5, db_path=db_path)

    assert results[0]["similarity_score"] == 0.0
