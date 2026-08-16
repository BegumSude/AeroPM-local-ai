import json
import time

import numpy as np

from backend.core.chunker import chunk_text
from backend.core.config import DB_PATH
from backend.core.document_loader import load_document
from backend.core.embedder import embed_texts
from backend.core.generator import generate_answer
from backend.core.retriever import find_relevant_chunks
from backend.database.db import get_connection


def _ensure_collection_exists(connection, collection_id) -> None:
    row = connection.execute(
        "SELECT id FROM collections WHERE id = ?", (collection_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"collection bulunamadi: {collection_id}")


def _find_existing_document(connection, collection_id, filename):
    return connection.execute(
        "SELECT id FROM documents WHERE collection_id = ? AND filename = ?",
        (collection_id, filename),
    ).fetchone()


def index_document(file_path: str, collection_id: int, db_path: str = DB_PATH) -> dict:
    connection = get_connection(db_path)
    try:
        _ensure_collection_exists(connection, collection_id)

        document = load_document(file_path)

        existing = _find_existing_document(connection, collection_id, document["filename"])
        if existing is not None:
            document_id = existing["id"]
            chunk_count = connection.execute(
                "SELECT COUNT(*) AS count FROM chunks WHERE document_id = ?", (document_id,)
            ).fetchone()["count"]
            return {
                "document_id": document_id,
                "filename": document["filename"],
                "chunk_count": chunk_count,
            }

        chunks = chunk_text(document["text"])
        embeddings = embed_texts([chunk["chunk_text"] for chunk in chunks])

        document_id = connection.execute(
            "INSERT INTO documents (collection_id, filename, file_type, char_count, word_count) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                collection_id,
                document["filename"],
                document["file_type"],
                document["metadata"]["char_count"],
                document["metadata"]["word_count"],
            ),
        ).lastrowid

        for chunk, embedding in zip(chunks, embeddings):
            connection.execute(
                "INSERT INTO chunks (document_id, chunk_index, chunk_text, start_char, end_char, embedding) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    document_id,
                    chunk["chunk_index"],
                    chunk["chunk_text"],
                    chunk["start_char"],
                    chunk["end_char"],
                    np.asarray(embedding, dtype=np.float32).tobytes(),
                ),
            )

        connection.commit()

        return {
            "document_id": document_id,
            "filename": document["filename"],
            "chunk_count": len(chunks),
        }
    finally:
        connection.close()


def ask_question(question: str, collection_id: int, top_k: int = 5, db_path: str = DB_PATH) -> dict:
    if not question or not question.strip():
        raise ValueError("question bos olamaz")

    connection = get_connection(db_path)
    try:
        _ensure_collection_exists(connection, collection_id)

        start_time = time.perf_counter()
        question_embedding = embed_texts([question])[0]
        context_chunks = find_relevant_chunks(question_embedding, collection_id, top_k, db_path=db_path)
        answer = generate_answer(question, context_chunks)
        response_time_ms = (time.perf_counter() - start_time) * 1000

        sources = [
            {
                "document_name": chunk["document_name"],
                "chunk_index": chunk["chunk_index"],
                "similarity_score": chunk["similarity_score"],
            }
            for chunk in context_chunks
        ]

        connection.execute(
            "INSERT INTO chat_history (collection_id, question, answer, sources, response_time_ms) "
            "VALUES (?, ?, ?, ?, ?)",
            (collection_id, question, answer, json.dumps(sources), response_time_ms),
        )
        connection.commit()
    finally:
        connection.close()

    return {"answer": answer, "sources": sources}
