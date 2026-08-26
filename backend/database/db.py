import sqlite3

from backend.core.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    char_count INTEGER,
    word_count INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (collection_id) REFERENCES collections(id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    embedding BLOB,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT,
    sources TEXT,
    response_time_ms REAL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (collection_id) REFERENCES collections(id)
);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_history_id INTEGER NOT NULL,
    is_helpful INTEGER,
    comment TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (chat_history_id) REFERENCES chat_history(id)
);

CREATE TABLE IF NOT EXISTS risks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_ref TEXT NOT NULL,
    collection_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,
    description TEXT NOT NULL,
    probability TEXT,
    impact TEXT,
    risk_level TEXT,
    affected_milestone TEXT,
    responsible TEXT,
    evidence_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (collection_id) REFERENCES collections(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_ref TEXT NOT NULL,
    collection_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,
    decision_text TEXT NOT NULL,
    decision_date TEXT,
    reason TEXT,
    affected_area TEXT,
    evidence_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (collection_id) REFERENCES collections(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);

CREATE TABLE IF NOT EXISTS requirements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    requirement_ref TEXT NOT NULL,
    collection_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,
    requirement_text TEXT NOT NULL,
    status TEXT,
    evidence_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (collection_id) REFERENCES collections(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);

CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    milestone_ref TEXT NOT NULL,
    collection_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,
    name TEXT NOT NULL,
    due_date TEXT,
    status TEXT,
    evidence_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (collection_id) REFERENCES collections(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);

CREATE TABLE IF NOT EXISTS test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_ref TEXT NOT NULL,
    collection_id INTEGER NOT NULL,
    document_id INTEGER NOT NULL,
    chunk_id INTEGER,
    test_name TEXT NOT NULL,
    requirement_ref TEXT,
    test_status TEXT,
    evidence_text TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (collection_id) REFERENCES collections(id),
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);

CREATE TABLE IF NOT EXISTS trace_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,
    source_id INTEGER NOT NULL,
    target_type TEXT NOT NULL,
    target_id INTEGER NOT NULL,
    match_basis TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (collection_id) REFERENCES collections(id)
);
"""


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.row_factory = sqlite3.Row
    return connection


def _ensure_doc_category_column(connection: sqlite3.Connection) -> None:
    columns = {row["name"] for row in connection.execute("PRAGMA table_info(documents)")}
    if "doc_category" not in columns:
        connection.execute("ALTER TABLE documents ADD COLUMN doc_category TEXT")


def init_db(db_path: str = DB_PATH) -> None:
    connection = get_connection(db_path)
    connection.executescript(SCHEMA)
    _ensure_doc_category_column(connection)
    connection.commit()
    connection.close()


_TRACE_LINK_TYPE_BY_TABLE = {
    "risks": "risk",
    "decisions": "decision",
    "requirements": "requirement",
    "milestones": "milestone",
    "test_results": "test",
}


def _delete_trace_links_for_rows(connection: sqlite3.Connection, table: str, row_ids: list[int]) -> None:
    link_type = _TRACE_LINK_TYPE_BY_TABLE[table]
    for row_id in row_ids:
        connection.execute(
            "DELETE FROM trace_links WHERE (source_type = ? AND source_id = ?) "
            "OR (target_type = ? AND target_id = ?)",
            (link_type, row_id, link_type, row_id),
        )


def delete_document(document_id: int, db_path: str = DB_PATH) -> None:
    connection = get_connection(db_path)
    try:
        document = connection.execute("SELECT id FROM documents WHERE id = ?", (document_id,)).fetchone()
        if document is None:
            raise ValueError(f"document not found: {document_id}")

        for table in _TRACE_LINK_TYPE_BY_TABLE:
            row_ids = [
                row["id"] for row in connection.execute(f"SELECT id FROM {table} WHERE document_id = ?", (document_id,))
            ]
            _delete_trace_links_for_rows(connection, table, row_ids)
            connection.execute(f"DELETE FROM {table} WHERE document_id = ?", (document_id,))

        connection.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
        connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        connection.commit()
    finally:
        connection.close()


def delete_collection(collection_id: int, db_path: str = DB_PATH) -> None:
    connection = get_connection(db_path)
    try:
        collection = connection.execute("SELECT id FROM collections WHERE id = ?", (collection_id,)).fetchone()
        if collection is None:
            raise ValueError(f"collection bulunamadi: {collection_id}")

        connection.execute("DELETE FROM trace_links WHERE collection_id = ?", (collection_id,))
        for table in _TRACE_LINK_TYPE_BY_TABLE:
            connection.execute(f"DELETE FROM {table} WHERE collection_id = ?", (collection_id,))

        chat_history_ids = [
            row["id"]
            for row in connection.execute("SELECT id FROM chat_history WHERE collection_id = ?", (collection_id,))
        ]
        for chat_history_id in chat_history_ids:
            connection.execute("DELETE FROM feedback WHERE chat_history_id = ?", (chat_history_id,))
        connection.execute("DELETE FROM chat_history WHERE collection_id = ?", (collection_id,))

        connection.execute(
            "DELETE FROM chunks WHERE document_id IN (SELECT id FROM documents WHERE collection_id = ?)",
            (collection_id,),
        )
        connection.execute("DELETE FROM documents WHERE collection_id = ?", (collection_id,))
        connection.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
        connection.commit()
    finally:
        connection.close()
