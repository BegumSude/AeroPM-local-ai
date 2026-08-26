import numpy as np
import pytest
from fastapi.testclient import TestClient

import backend.api.main as api_main
from backend.database.db import get_connection, init_db


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    path = str(tmp_path / "test_rag.db")
    init_db(path)
    monkeypatch.setattr(api_main, "DB_PATH", path)
    return path


@pytest.fixture(autouse=True)
def documents_dir(tmp_path, monkeypatch):
    directory = tmp_path / "documents"
    monkeypatch.setattr(api_main, "DOCUMENTS_DIR", directory)
    return directory


@pytest.fixture(autouse=True)
def fake_foundry_local(monkeypatch):
    def fake_embed_texts(texts):
        vectors = [[1.0, 0.0] if i == 0 else [0.0, 1.0] for i in range(len(texts))]
        return np.array(vectors, dtype=np.float32)

    monkeypatch.setattr("backend.core.rag_service.embed_texts", fake_embed_texts)
    monkeypatch.setattr(
        "backend.core.rag_service.generate_answer",
        lambda question, context_chunks: "FAKE_ANSWER",
    )
    for name in ("risks", "decisions", "requirements", "milestones", "test_results"):
        monkeypatch.setattr(f"backend.core.project_service.extract_{name}", lambda chunks: [])


@pytest.fixture
def collection_id(db_path):
    connection = get_connection(db_path)
    collection_id = connection.execute(
        "INSERT INTO collections (name) VALUES (?)", ("koleksiyon",)
    ).lastrowid
    connection.commit()
    connection.close()
    return collection_id


@pytest.fixture
def client(db_path):
    return TestClient(api_main.app)


def _sample_file_bytes():
    return ("sample.txt", ("Bu bir test belgesidir. " * 50).encode("utf-8"), "text/plain")


def test_create_collection_success(client):
    response = client.post("/collections", json={"name": "koleksiyon"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "koleksiyon"
    assert isinstance(body["id"], int)


def test_create_collection_empty_name_returns_400(client):
    response = client.post("/collections", json={"name": "   "})

    assert response.status_code == 400


def test_list_collections_returns_created_collections(client):
    client.post("/collections", json={"name": "a"})
    client.post("/collections", json={"name": "b"})

    response = client.get("/collections")

    assert response.status_code == 200
    names = [item["name"] for item in response.json()]
    assert names == ["a", "b"]


def test_delete_collection_success(client):
    collection_id = client.post("/collections", json={"name": "koleksiyon"}).json()["id"]

    response = client.delete(f"/collections/{collection_id}")

    assert response.status_code == 200
    assert client.get("/collections").json() == []


def test_delete_collection_invalid_id_returns_404(client):
    response = client.delete("/collections/999")

    assert response.status_code == 404


def test_delete_document_removes_it_from_list(client, collection_id, documents_dir):
    upload_response = client.post(
        "/documents/upload", data={"collection_id": collection_id}, files={"file": _sample_file_bytes()}
    )
    document_id = upload_response.json()["document_id"]

    response = client.delete(f"/documents/{document_id}")

    assert response.status_code == 200
    documents = client.get("/documents", params={"collection_id": collection_id}).json()
    assert documents == []


def test_delete_document_invalid_id_returns_404(client):
    response = client.delete("/documents/999")

    assert response.status_code == 404


def test_upload_document_success(client, collection_id, documents_dir):
    response = client.post(
        "/documents/upload",
        data={"collection_id": collection_id},
        files={"file": _sample_file_bytes()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "sample.txt"
    assert body["chunk_count"] > 0
    assert (documents_dir / "sample.txt").exists()


def test_upload_document_unsupported_type_returns_400(client, collection_id):
    response = client.post(
        "/documents/upload",
        data={"collection_id": collection_id},
        files={"file": ("sample.xyz", b"icerik", "application/octet-stream")},
    )

    assert response.status_code == 400


def test_upload_document_invalid_collection_returns_404(client):
    response = client.post(
        "/documents/upload",
        data={"collection_id": 999},
        files={"file": _sample_file_bytes()},
    )

    assert response.status_code == 404


def test_list_documents_filtered_by_collection(client, db_path):
    connection = get_connection(db_path)
    collection_a = connection.execute("INSERT INTO collections (name) VALUES (?)", ("a",)).lastrowid
    collection_b = connection.execute("INSERT INTO collections (name) VALUES (?)", ("b",)).lastrowid
    connection.commit()
    connection.close()

    client.post("/documents/upload", data={"collection_id": collection_a}, files={"file": _sample_file_bytes()})
    client.post(
        "/documents/upload",
        data={"collection_id": collection_b},
        files={"file": ("other.txt", b"baska bir belge", "text/plain")},
    )

    response = client.get("/documents", params={"collection_id": collection_a})

    assert response.status_code == 200
    documents = response.json()
    assert len(documents) == 1
    assert documents[0]["filename"] == "sample.txt"


def test_list_documents_without_filter_returns_all(client, collection_id):
    client.post("/documents/upload", data={"collection_id": collection_id}, files={"file": _sample_file_bytes()})

    response = client.get("/documents")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_chat_ask_returns_answer_and_sources(client, collection_id):
    client.post("/documents/upload", data={"collection_id": collection_id}, files={"file": _sample_file_bytes()})

    response = client.post(
        "/chat/ask", json={"collection_id": collection_id, "question": "test sorusu", "top_k": 2}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "FAKE_ANSWER"
    assert len(body["sources"]) > 0


def test_chat_ask_empty_question_returns_400(client, collection_id):
    response = client.post("/chat/ask", json={"collection_id": collection_id, "question": "   "})

    assert response.status_code == 400


def test_chat_ask_invalid_collection_returns_404(client):
    response = client.post("/chat/ask", json={"collection_id": 999, "question": "soru"})

    assert response.status_code == 404


def test_chat_history_returns_previous_questions(client, collection_id):
    client.post("/documents/upload", data={"collection_id": collection_id}, files={"file": _sample_file_bytes()})
    client.post("/chat/ask", json={"collection_id": collection_id, "question": "test sorusu"})

    response = client.get("/chat/history", params={"collection_id": collection_id})

    assert response.status_code == 200
    history = response.json()
    assert len(history) == 1
    assert history[0]["question"] == "test sorusu"
    assert history[0]["answer"] == "FAKE_ANSWER"
    assert isinstance(history[0]["sources"], list)


def test_feedback_creates_record(client, collection_id, db_path):
    client.post("/documents/upload", data={"collection_id": collection_id}, files={"file": _sample_file_bytes()})
    client.post("/chat/ask", json={"collection_id": collection_id, "question": "test sorusu"})

    history_response = client.get("/chat/history", params={"collection_id": collection_id})
    chat_history_id = history_response.json()[0]["id"]

    response = client.post(
        "/feedback", json={"chat_history_id": chat_history_id, "is_helpful": True, "comment": "iyi"}
    )

    assert response.status_code == 200
    connection = get_connection(db_path)
    row = connection.execute(
        "SELECT * FROM feedback WHERE chat_history_id = ?", (chat_history_id,)
    ).fetchone()
    connection.close()
    assert row["is_helpful"] == 1
    assert row["comment"] == "iyi"


def test_feedback_invalid_chat_history_id_returns_404(client):
    response = client.post("/feedback", json={"chat_history_id": 999, "is_helpful": True})

    assert response.status_code == 404


def test_stats_returns_counts(client, collection_id):
    client.post("/documents/upload", data={"collection_id": collection_id}, files={"file": _sample_file_bytes()})
    client.post("/chat/ask", json={"collection_id": collection_id, "question": "test sorusu"})

    response = client.get("/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["collection_count"] == 1
    assert body["document_count"] == 1
    assert body["chunk_count"] > 0
    assert body["chat_history_count"] == 1


def test_upload_document_persists_doc_category(client, collection_id):
    response = client.post(
        "/documents/upload",
        data={"collection_id": collection_id, "doc_category": "risk_register"},
        files={"file": _sample_file_bytes()},
    )

    assert response.status_code == 200
    assert response.json()["doc_category"] == "risk_register"

    documents = client.get("/documents", params={"collection_id": collection_id}).json()
    assert documents[0]["doc_category"] == "risk_register"


def test_upload_document_defaults_doc_category_to_other(client, collection_id):
    response = client.post(
        "/documents/upload", data={"collection_id": collection_id}, files={"file": _sample_file_bytes()}
    )

    assert response.json()["doc_category"] == "other"


def test_analyze_document_returns_extraction_counts(client, collection_id, monkeypatch):
    upload_response = client.post(
        "/documents/upload",
        data={"collection_id": collection_id, "doc_category": "risk_register"},
        files={"file": _sample_file_bytes()},
    )
    document_id = upload_response.json()["document_id"]

    monkeypatch.setattr(
        "backend.core.project_service.extract_risks",
        lambda chunks: [{"description": "risk", "evidence_text": "Bu bir test belgesidir."}],
    )

    response = client.post(f"/documents/{document_id}/analyze")

    assert response.status_code == 200
    body = response.json()
    assert body["document_id"] == document_id
    assert body["risks"] == 1


def test_analyze_document_invalid_document_id_returns_404(client):
    response = client.post("/documents/999/analyze")

    assert response.status_code == 404


def test_list_risks_reflects_analyzed_document(client, collection_id, monkeypatch):
    upload_response = client.post(
        "/documents/upload",
        data={"collection_id": collection_id, "doc_category": "risk_register"},
        files={"file": _sample_file_bytes()},
    )
    document_id = upload_response.json()["document_id"]
    monkeypatch.setattr(
        "backend.core.project_service.extract_risks",
        lambda chunks: [{"description": "risk", "evidence_text": "Bu bir test belgesidir."}],
    )
    client.post(f"/documents/{document_id}/analyze")

    response = client.get("/risks", params={"collection_id": collection_id})

    assert response.status_code == 200
    risks = response.json()
    assert len(risks) == 1
    assert risks[0]["risk_ref"] == "RISK-001"
    assert risks[0]["description"] == "risk"


def test_list_decisions_returns_empty_list_for_collection_without_decisions(client, collection_id):
    response = client.get("/decisions", params={"collection_id": collection_id})

    assert response.status_code == 200
    assert response.json() == []


def test_list_requirements_returns_empty_list_for_collection_without_requirements(client, collection_id):
    response = client.get("/requirements", params={"collection_id": collection_id})

    assert response.status_code == 200
    assert response.json() == []


def test_list_milestones_returns_empty_list_for_collection_without_milestones(client, collection_id):
    response = client.get("/milestones", params={"collection_id": collection_id})

    assert response.status_code == 200
    assert response.json() == []


def test_list_test_results_returns_empty_list_for_collection_without_test_results(client, collection_id):
    response = client.get("/test-results", params={"collection_id": collection_id})

    assert response.status_code == 200
    assert response.json() == []


def test_trace_links_returns_empty_list_for_collection_without_links(client, collection_id):
    response = client.get("/trace-links", params={"collection_id": collection_id})

    assert response.status_code == 200
    assert response.json() == []


def test_project_status_returns_expected_shape(client, collection_id):
    response = client.get("/project-status", params={"collection_id": collection_id})

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "health", "risk_summary", "status_summary", "recent_decisions", "upcoming_milestones"
    }
    assert body["health"]["requirements"] == 0.0
    assert body["risk_summary"] == {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
