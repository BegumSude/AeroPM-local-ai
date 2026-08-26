import json
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.config import DB_PATH
from backend.core.document_loader import UnsupportedFileTypeError
from backend.core.project_service import analyze_document, get_project_status, resolve_trace_links
from backend.core.rag_service import ask_question, index_document
from backend.database.db import delete_collection, delete_document, get_connection, init_db

DOCUMENTS_DIR = Path("data/documents")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(DB_PATH)
    yield


app = FastAPI(title="local-rag-application-foundry-local", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateCollectionRequest(BaseModel):
    name: str


class AskQuestionRequest(BaseModel):
    collection_id: int
    question: str
    top_k: int = 5


class FeedbackRequest(BaseModel):
    chat_history_id: int
    is_helpful: bool
    comment: str | None = None


_NOT_FOUND_PREFIXES = ("collection bulunamadi", "document not found")


def _raise_from_value_error(error: ValueError) -> None:
    if str(error).startswith(_NOT_FOUND_PREFIXES):
        raise HTTPException(status_code=404, detail=str(error)) from error
    raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/collections")
def create_collection(request: CreateCollectionRequest) -> dict:
    if not request.name or not request.name.strip():
        raise HTTPException(status_code=400, detail="name bos olamaz")

    connection = get_connection(DB_PATH)
    try:
        collection_id = connection.execute(
            "INSERT INTO collections (name) VALUES (?)", (request.name,)
        ).lastrowid
        connection.commit()
        row = connection.execute(
            "SELECT id, name, created_at FROM collections WHERE id = ?", (collection_id,)
        ).fetchone()
        return dict(row)
    finally:
        connection.close()


@app.get("/collections")
def list_collections() -> list[dict]:
    connection = get_connection(DB_PATH)
    try:
        rows = connection.execute("SELECT id, name, created_at FROM collections ORDER BY id").fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


@app.delete("/collections/{collection_id}")
def delete_collection_endpoint(collection_id: int) -> dict:
    try:
        delete_collection(collection_id, db_path=DB_PATH)
    except ValueError as error:
        _raise_from_value_error(error)
    return {"deleted": True}


@app.post("/documents/upload")
async def upload_document(
    collection_id: int = Form(...), file: UploadFile = File(...), doc_category: str = Form("other")
) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="dosya adi gerekli")

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    destination = DOCUMENTS_DIR / Path(file.filename).name
    destination.write_bytes(await file.read())

    try:
        result = index_document(str(destination), collection_id, db_path=DB_PATH)
    except UnsupportedFileTypeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        _raise_from_value_error(error)

    connection = get_connection(DB_PATH)
    try:
        connection.execute(
            "UPDATE documents SET doc_category = ? WHERE id = ?", (doc_category, result["document_id"])
        )
        connection.commit()
    finally:
        connection.close()

    return {**result, "doc_category": doc_category}


@app.get("/documents")
def list_documents(collection_id: int | None = None) -> list[dict]:
    connection = get_connection(DB_PATH)
    try:
        query = (
            "SELECT id, collection_id, filename, file_type, doc_category, char_count, word_count, created_at "
            "FROM documents"
        )
        if collection_id is not None:
            rows = connection.execute(query + " WHERE collection_id = ? ORDER BY id", (collection_id,)).fetchall()
        else:
            rows = connection.execute(query + " ORDER BY id").fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


@app.delete("/documents/{document_id}")
def delete_document_endpoint(document_id: int) -> dict:
    try:
        delete_document(document_id, db_path=DB_PATH)
    except ValueError as error:
        _raise_from_value_error(error)
    return {"deleted": True}


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


def _list_rows(table: str, columns: str, collection_id: int) -> list[dict]:
    connection = get_connection(DB_PATH)
    try:
        rows = connection.execute(
            f"SELECT {columns} FROM {table} WHERE collection_id = ? ORDER BY id", (collection_id,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


@app.post("/documents/{document_id}/analyze")
def analyze_document_endpoint(document_id: int) -> dict:
    try:
        return analyze_document(document_id, db_path=DB_PATH)
    except ValueError as error:
        _raise_from_value_error(error)


@app.get("/risks")
def list_risks(collection_id: int) -> list[dict]:
    return _list_rows(
        "risks",
        "id, risk_ref, document_id, chunk_id, description, probability, impact, risk_level, "
        "affected_milestone, responsible, evidence_text, created_at",
        collection_id,
    )


@app.get("/decisions")
def list_decisions(collection_id: int) -> list[dict]:
    return _list_rows(
        "decisions",
        "id, decision_ref, document_id, chunk_id, decision_text, decision_date, reason, "
        "affected_area, evidence_text, created_at",
        collection_id,
    )


@app.get("/requirements")
def list_requirements(collection_id: int) -> list[dict]:
    return _list_rows(
        "requirements",
        "id, requirement_ref, document_id, chunk_id, requirement_text, status, evidence_text, created_at",
        collection_id,
    )


@app.get("/milestones")
def list_milestones(collection_id: int) -> list[dict]:
    return _list_rows(
        "milestones",
        "id, milestone_ref, document_id, chunk_id, name, due_date, status, evidence_text, created_at",
        collection_id,
    )


@app.get("/test-results")
def list_test_results(collection_id: int) -> list[dict]:
    return _list_rows(
        "test_results",
        "id, test_ref, document_id, chunk_id, test_name, requirement_ref, test_status, evidence_text, created_at",
        collection_id,
    )


@app.get("/trace-links")
def list_trace_links(collection_id: int) -> list[dict]:
    resolve_trace_links(collection_id, db_path=DB_PATH)
    return _list_rows(
        "trace_links", "id, source_type, source_id, target_type, target_id, match_basis, created_at", collection_id
    )


@app.get("/project-status")
def project_status(collection_id: int) -> dict:
    return get_project_status(collection_id, db_path=DB_PATH)
