import numpy as np

from backend.core.config import DB_PATH
from backend.database.db import get_connection


def find_relevant_chunks(question_embedding, collection_id, top_k: int = 5, db_path: str = DB_PATH) -> list[dict]:
    if top_k <= 0:
        raise ValueError("top_k pozitif bir tam sayi olmalidir")

    question_vector = np.asarray(question_embedding, dtype=np.float32)

    connection = get_connection(db_path)
    try:
        rows = connection.execute(
            """
            SELECT chunks.chunk_index, chunks.chunk_text, chunks.embedding, documents.filename
            FROM chunks
            JOIN documents ON documents.id = chunks.document_id
            WHERE documents.collection_id = ?
            """,
            (collection_id,),
        ).fetchall()
    finally:
        connection.close()

    scored_chunks = []
    for row in rows:
        chunk_vector = np.frombuffer(row["embedding"], dtype=np.float32)
        scored_chunks.append({
            "document_name": row["filename"],
            "chunk_index": row["chunk_index"],
            "chunk_text": row["chunk_text"],
            "similarity_score": _cosine_similarity(question_vector, chunk_vector),
        })

    scored_chunks.sort(key=lambda chunk: chunk["similarity_score"], reverse=True)
    return scored_chunks[:top_k]


def _cosine_similarity(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    norm_a = np.linalg.norm(vector_a)
    norm_b = np.linalg.norm(vector_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vector_a, vector_b) / (norm_a * norm_b))
