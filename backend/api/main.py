import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.config import DB_PATH
from backend.core.document_loader import UnsupportedFileTypeError
from backend.core.rag_service import ask_question, index_document
from backend.database.db import get_connection

DOCUMENTS_DIR = Path("data/documents")

app = FastAPI(title="local-rag-application-foundry-local")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskQuestionRequest(BaseModel):
    collection_id: int
    question: str
    top_k: int = 5


class FeedbackRequest(BaseModel):
    chat_history_id: int
    is_helpful: bool
    comment: str | None = None


def _raise_from_value_error(error: ValueError) -> None:
    if str(error).startswith("collection bulunamadi"):
        raise HTTPException(status_code=404, detail=str(error)) from error
    raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/documents/upload")
async def upload_document(collection_id: int = Form(...), file: UploadFile = File(...)) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="dosya adi gerekli")

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    destination = DOCUMENTS_DIR / Path(file.filename).name
    destination.write_bytes(await file.read())

    try:
        return index_document(str(destination), collection_id, db_path=DB_PATH)
    except UnsupportedFileTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        _raise_from_value_error(error)


@app.get("/documents")
def list_documents(collection_id: int | None = None) -> list[dict]:
    connection = get_connection(DB_PATH)
    try:
        query = (
            "SELECT id, collection_id, filename, file_type, char_count, word_count, created_at "
            "FROM documents"
        )
        if collection_id is not None:
            rows = connection.execute(query + " WHERE collection_id = ? ORDER BY id", (collection_id,)).fetchall()
        else:
            rows = connection.execute(query + " ORDER BY id").fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


@app.post("/chat/ask")
def chat_ask(request: AskQuestionRequest) -> dict:
    try:
        return ask_question(request.question, request.collection_id, request.top_k, db_path=DB_PATH)
    except ValueError as error:
        _raise_from_value_error(error)


@app.get("/chat/history")
def chat_history(collection_id: int) -> list[dict]:
    connection = get_connection(DB_PATH)
    try:
        rows = connection.execute(
            "SELECT id, collection_id, question, answer, sources, response_time_ms, created_at "
            "FROM chat_history WHERE collection_id = ? ORDER BY id",
            (collection_id,),
        ).fetchall()
        history = []
        for row in rows:
            entry = dict(row)
            entry["sources"] = json.loads(entry["sources"]) if entry["sources"] else []
            history.append(entry)
        return history
    finally:
        connection.close()


@app.post("/feedback")
def submit_feedback(request: FeedbackRequest) -> dict:
    connection = get_connection(DB_PATH)
    try:
        try:
            feedback_id = connection.execute(
                "INSERT INTO feedback (chat_history_id, is_helpful, comment) VALUES (?, ?, ?)",
                (request.chat_history_id, int(request.is_helpful), request.comment),
            ).lastrowid
        except sqlite3.IntegrityError as error:
            raise HTTPException(status_code=404, detail="chat_history bulunamadi") from error
        connection.commit()
        return {"feedback_id": feedback_id}
    finally:
        connection.close()


@app.get("/stats")
def stats() -> dict:
    connection = get_connection(DB_PATH)
    try:
        def _count(table: str) -> int:
            return connection.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]

        return {
            "collection_count": _count("collections"),
            "document_count": _count("documents"),
            "chunk_count": _count("chunks"),
            "chat_history_count": _count("chat_history"),
        }
    finally:
        connection.close()
