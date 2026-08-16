import sqlite3

import pytest

from backend.database.db import get_connection, init_db


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
