import sqlite3

import pytest

from backend.database.db import delete_collection, delete_document, get_connection, init_db


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_rag.db")
    init_db(path)
    return path


def _table_names(connection):
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {row["name"] for row in rows}


def test_init_db_creates_collections_table(db_path):
    connection = get_connection(db_path)
    assert "collections" in _table_names(connection)
    connection.close()


def test_init_db_creates_documents_table(db_path):
    connection = get_connection(db_path)
    assert "documents" in _table_names(connection)
    connection.close()


def test_init_db_creates_chunks_table(db_path):
    connection = get_connection(db_path)
    assert "chunks" in _table_names(connection)
    connection.close()


def test_init_db_creates_chat_history_table(db_path):
    connection = get_connection(db_path)
    assert "chat_history" in _table_names(connection)
    connection.close()


def test_init_db_creates_feedback_table(db_path):
    connection = get_connection(db_path)
    assert "feedback" in _table_names(connection)
    connection.close()


def test_collections_insert_and_select(db_path):
    connection = get_connection(db_path)
    connection.execute("INSERT INTO collections (name) VALUES (?)", ("test koleksiyon",))
    connection.commit()

    row = connection.execute("SELECT * FROM collections WHERE name = ?", ("test koleksiyon",)).fetchone()
    assert row["name"] == "test koleksiyon"
    connection.close()


def test_documents_insert_and_select_with_collection_relation(db_path):
    connection = get_connection(db_path)
    collection_id = connection.execute(
        "INSERT INTO collections (name) VALUES (?)", ("koleksiyon",)
    ).lastrowid
    connection.execute(
        "INSERT INTO documents (collection_id, filename, file_type, char_count, word_count) "
        "VALUES (?, ?, ?, ?, ?)",
        (collection_id, "sample.txt", "txt", 100, 20),
    )
    connection.commit()

    row = connection.execute(
        "SELECT * FROM documents WHERE collection_id = ?", (collection_id,)
    ).fetchone()
    assert row["filename"] == "sample.txt"
    assert row["collection_id"] == collection_id
    connection.close()


def test_chunks_embedding_stored_and_read_as_blob(db_path):
    connection = get_connection(db_path)
    collection_id = connection.execute(
        "INSERT INTO collections (name) VALUES (?)", ("koleksiyon",)
    ).lastrowid
    document_id = connection.execute(
        "INSERT INTO documents (collection_id, filename, file_type) VALUES (?, ?, ?)",
        (collection_id, "sample.txt", "txt"),
    ).lastrowid

    embedding = (1.5, -2.25, 3.0)
    embedding_blob = sqlite3.Binary(bytes(str(embedding), "utf-8"))
    connection.execute(
        "INSERT INTO chunks (document_id, chunk_index, chunk_text, start_char, end_char, embedding) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (document_id, 0, "merhaba dunya", 0, 13, embedding_blob),
    )
    connection.commit()

    row = connection.execute("SELECT * FROM chunks WHERE document_id = ?", (document_id,)).fetchone()
    assert row["chunk_text"] == "merhaba dunya"
    assert isinstance(row["embedding"], bytes)
    assert row["embedding"] == bytes(embedding_blob)
    connection.close()


def test_foreign_key_violation_is_rejected(db_path):
    connection = get_connection(db_path)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO documents (collection_id, filename, file_type) VALUES (?, ?, ?)",
            (999, "sample.txt", "txt"),
        )
    connection.close()


def test_init_db_can_be_called_again_without_error(db_path):
    init_db(db_path)


def test_init_db_creates_risks_table(db_path):
    connection = get_connection(db_path)
    assert "risks" in _table_names(connection)
    connection.close()


def test_init_db_creates_decisions_table(db_path):
    connection = get_connection(db_path)
    assert "decisions" in _table_names(connection)
    connection.close()


def test_init_db_creates_requirements_table(db_path):
    connection = get_connection(db_path)
    assert "requirements" in _table_names(connection)
    connection.close()


def test_init_db_creates_milestones_table(db_path):
    connection = get_connection(db_path)
    assert "milestones" in _table_names(connection)
    connection.close()


def test_init_db_creates_test_results_table(db_path):
    connection = get_connection(db_path)
    assert "test_results" in _table_names(connection)
    connection.close()


def test_init_db_creates_trace_links_table(db_path):
    connection = get_connection(db_path)
    assert "trace_links" in _table_names(connection)
    connection.close()


def test_documents_table_has_doc_category_column(db_path):
    connection = get_connection(db_path)
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(documents)")}
    connection.close()
    assert "doc_category" in columns


def test_doc_category_column_present_after_calling_init_db_twice(db_path):
    init_db(db_path)

    connection = get_connection(db_path)
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(documents)")}
    connection.close()
    assert "doc_category" in columns


def _seed_full_graph(db_path):
    connection = get_connection(db_path)
    collection_id = connection.execute("INSERT INTO collections (name) VALUES (?)", ("koleksiyon",)).lastrowid
    document_id = connection.execute(
        "INSERT INTO documents (collection_id, filename, file_type, doc_category) VALUES (?, ?, ?, ?)",
        (collection_id, "doc.pdf", "pdf", "risk_register"),
    ).lastrowid
    chunk_id = connection.execute(
        "INSERT INTO chunks (document_id, chunk_index, chunk_text, start_char, end_char) VALUES (?, ?, ?, ?, ?)",
        (document_id, 0, "chunk text", 0, 10),
    ).lastrowid
    risk_id = connection.execute(
        "INSERT INTO risks (risk_ref, collection_id, document_id, chunk_id, description, evidence_text) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("RISK-001", collection_id, document_id, chunk_id, "risk", "evidence"),
    ).lastrowid
    milestone_id = connection.execute(
        "INSERT INTO milestones (milestone_ref, collection_id, document_id, name, evidence_text) "
        "VALUES (?, ?, ?, ?, ?)",
        ("MS-001", collection_id, document_id, "milestone", "evidence"),
    ).lastrowid
    connection.execute(
        "INSERT INTO trace_links (collection_id, source_type, source_id, target_type, target_id, match_basis) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (collection_id, "risk", risk_id, "milestone", milestone_id, "test"),
    )
    chat_history_id = connection.execute(
        "INSERT INTO chat_history (collection_id, question, answer) VALUES (?, ?, ?)",
        (collection_id, "soru", "cevap"),
    ).lastrowid
    connection.execute(
        "INSERT INTO feedback (chat_history_id, is_helpful) VALUES (?, ?)", (chat_history_id, 1)
    )
    connection.commit()
    connection.close()
    return collection_id, document_id


def test_delete_document_removes_document_and_dependent_rows(db_path):
    collection_id, document_id = _seed_full_graph(db_path)

    delete_document(document_id, db_path=db_path)

    connection = get_connection(db_path)
    assert connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone() is None
    assert connection.execute("SELECT * FROM chunks WHERE document_id = ?", (document_id,)).fetchone() is None
    assert connection.execute("SELECT * FROM risks WHERE document_id = ?", (document_id,)).fetchone() is None
    assert connection.execute("SELECT * FROM milestones WHERE document_id = ?", (document_id,)).fetchone() is None
    assert connection.execute(
        "SELECT * FROM trace_links WHERE collection_id = ?", (collection_id,)
    ).fetchone() is None
    # the collection itself and its chat_history must survive a document deletion
    assert connection.execute("SELECT * FROM collections WHERE id = ?", (collection_id,)).fetchone() is not None
    assert connection.execute("SELECT * FROM chat_history WHERE collection_id = ?", (collection_id,)).fetchone() is not None
    connection.close()


def test_delete_document_invalid_id_raises(db_path):
    with pytest.raises(ValueError):
        delete_document(999, db_path=db_path)


def test_delete_collection_removes_everything(db_path):
    collection_id, document_id = _seed_full_graph(db_path)

    delete_collection(collection_id, db_path=db_path)

    connection = get_connection(db_path)
    assert connection.execute("SELECT * FROM collections WHERE id = ?", (collection_id,)).fetchone() is None
    assert connection.execute("SELECT * FROM documents WHERE id = ?", (document_id,)).fetchone() is None
    assert connection.execute("SELECT * FROM chunks WHERE document_id = ?", (document_id,)).fetchone() is None
    assert connection.execute("SELECT * FROM risks WHERE collection_id = ?", (collection_id,)).fetchone() is None
    assert connection.execute(
        "SELECT * FROM milestones WHERE collection_id = ?", (collection_id,)
    ).fetchone() is None
    assert connection.execute(
        "SELECT * FROM trace_links WHERE collection_id = ?", (collection_id,)
    ).fetchone() is None
    assert connection.execute(
        "SELECT * FROM chat_history WHERE collection_id = ?", (collection_id,)
    ).fetchone() is None
    assert connection.execute("SELECT * FROM feedback").fetchone() is None
    connection.close()


def test_delete_collection_invalid_id_raises(db_path):
    with pytest.raises(ValueError):
        delete_collection(999, db_path=db_path)


def test_risks_foreign_key_violation_is_rejected(db_path):
    connection = get_connection(db_path)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            "INSERT INTO risks (risk_ref, collection_id, document_id, description, evidence_text) "
            "VALUES (?, ?, ?, ?, ?)",
            ("RISK-001", 1, 999, "test risk", "evidence"),
        )
    connection.close()
