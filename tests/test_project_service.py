import pytest

from backend.core.project_service import analyze_document, get_project_status, resolve_trace_links
from backend.database.db import get_connection, init_db

EXTRACTOR_NAMES = ["risks", "decisions", "requirements", "milestones", "test_results"]


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_rag.db")
    init_db(path)
    return path


@pytest.fixture
def collection_id(db_path):
    connection = get_connection(db_path)
    collection_id = connection.execute("INSERT INTO collections (name) VALUES (?)", ("aeropm",)).lastrowid
    connection.commit()
    connection.close()
    return collection_id


def _insert_document(db_path, collection_id, filename="doc.pdf", doc_category=None):
    connection = get_connection(db_path)
    document_id = connection.execute(
        "INSERT INTO documents (collection_id, filename, file_type, doc_category) VALUES (?, ?, ?, ?)",
        (collection_id, filename, "pdf", doc_category),
    ).lastrowid
    connection.commit()
    connection.close()
    return document_id


def _insert_chunk(db_path, document_id, chunk_index, chunk_text):
    connection = get_connection(db_path)
    connection.execute(
        "INSERT INTO chunks (document_id, chunk_index, chunk_text, start_char, end_char) VALUES (?, ?, ?, ?, ?)",
        (document_id, chunk_index, chunk_text, 0, len(chunk_text)),
    )
    connection.commit()
    connection.close()


def _patch_extractors(monkeypatch, results=None):
    results = results or {}
    calls = {name: 0 for name in EXTRACTOR_NAMES}

    def make_fake(name):
        def fake(chunks):
            calls[name] += 1
            return results.get(name, [])
        return fake

    for name in EXTRACTOR_NAMES:
        monkeypatch.setattr(f"backend.core.project_service.extract_{name}", make_fake(name))
    return calls


def test_analyze_document_only_runs_extractors_for_doc_category(db_path, collection_id, monkeypatch):
    calls = _patch_extractors(monkeypatch)
    document_id = _insert_document(db_path, collection_id, doc_category="risk_register")
    _insert_chunk(db_path, document_id, 0, "Some risk text.")

    analyze_document(document_id, db_path=db_path)

    assert calls["risks"] == 1
    assert calls["decisions"] == 0
    assert calls["requirements"] == 0
    assert calls["milestones"] == 0
    assert calls["test_results"] == 0


def test_analyze_document_invalid_document_id_raises(db_path):
    with pytest.raises(ValueError):
        analyze_document(999, db_path=db_path)


def test_analyze_document_defaults_to_other_category_when_unset(db_path, collection_id, monkeypatch):
    calls = _patch_extractors(monkeypatch)
    document_id = _insert_document(db_path, collection_id, doc_category=None)
    _insert_chunk(db_path, document_id, 0, "some text")

    analyze_document(document_id, db_path=db_path)

    assert all(count == 1 for count in calls.values())


def test_analyze_document_assigns_sequential_refs(db_path, collection_id, monkeypatch):
    _patch_extractors(monkeypatch, results={
        "risks": [
            {"description": "risk one", "evidence_text": "evidence one"},
            {"description": "risk two", "evidence_text": "evidence two"},
        ]
    })
    document_id = _insert_document(db_path, collection_id, doc_category="risk_register")
    _insert_chunk(db_path, document_id, 0, "evidence one and evidence two are both here.")

    analyze_document(document_id, db_path=db_path)

    connection = get_connection(db_path)
    refs = [row["risk_ref"] for row in connection.execute("SELECT risk_ref FROM risks ORDER BY id")]
    connection.close()
    assert refs == ["RISK-001", "RISK-002"]


def test_analyze_document_continues_ref_sequence_across_documents(db_path, collection_id, monkeypatch):
    _patch_extractors(monkeypatch, results={"risks": [{"description": "risk", "evidence_text": "evidence"}]})

    first_document_id = _insert_document(db_path, collection_id, "first.pdf", "risk_register")
    _insert_chunk(db_path, first_document_id, 0, "evidence text here")
    analyze_document(first_document_id, db_path=db_path)

    second_document_id = _insert_document(db_path, collection_id, "second.pdf", "risk_register")
    _insert_chunk(db_path, second_document_id, 0, "evidence text here")
    analyze_document(second_document_id, db_path=db_path)

    connection = get_connection(db_path)
    refs = [row["risk_ref"] for row in connection.execute("SELECT risk_ref FROM risks ORDER BY id")]
    connection.close()
    assert refs == ["RISK-001", "RISK-002"]


def test_analyze_document_resolves_chunk_id_via_evidence_substring_match(db_path, collection_id, monkeypatch):
    _patch_extractors(monkeypatch, results={"risks": [{"description": "risk", "evidence_text": "the exact evidence phrase"}]})
    document_id = _insert_document(db_path, collection_id, doc_category="risk_register")
    _insert_chunk(db_path, document_id, 0, "context before the exact evidence phrase context after")

    analyze_document(document_id, db_path=db_path)

    connection = get_connection(db_path)
    chunk_id = connection.execute("SELECT id FROM chunks WHERE document_id = ?", (document_id,)).fetchone()["id"]
    risk_chunk_id = connection.execute("SELECT chunk_id FROM risks").fetchone()["chunk_id"]
    connection.close()
    assert risk_chunk_id == chunk_id


def test_analyze_document_chunk_id_is_none_when_no_match(db_path, collection_id, monkeypatch):
    _patch_extractors(monkeypatch, results={"risks": [{"description": "risk", "evidence_text": "text that does not appear anywhere"}]})
    document_id = _insert_document(db_path, collection_id, doc_category="risk_register")
    _insert_chunk(db_path, document_id, 0, "completely unrelated chunk content")

    analyze_document(document_id, db_path=db_path)

    connection = get_connection(db_path)
    risk_chunk_id = connection.execute("SELECT chunk_id FROM risks").fetchone()["chunk_id"]
    connection.close()
    assert risk_chunk_id is None


def test_analyze_document_re_analyze_does_not_duplicate_rows(db_path, collection_id, monkeypatch):
    _patch_extractors(monkeypatch, results={"risks": [{"description": "risk", "evidence_text": "evidence"}]})
    document_id = _insert_document(db_path, collection_id, doc_category="risk_register")
    _insert_chunk(db_path, document_id, 0, "evidence text here")

    analyze_document(document_id, db_path=db_path)
    analyze_document(document_id, db_path=db_path)

    connection = get_connection(db_path)
    count = connection.execute(
        "SELECT COUNT(*) AS count FROM risks WHERE document_id = ?", (document_id,)
    ).fetchone()["count"]
    connection.close()
    assert count == 1


def test_analyze_document_skips_items_missing_required_fields(db_path, collection_id, monkeypatch):
    _patch_extractors(monkeypatch, results={"risks": [{"probability": "High"}]})
    document_id = _insert_document(db_path, collection_id, doc_category="risk_register")
    _insert_chunk(db_path, document_id, 0, "chunk text")

    result = analyze_document(document_id, db_path=db_path)

    assert result["risks"] == 0


def test_analyze_document_infers_risk_level_from_probability_and_impact(db_path, collection_id, monkeypatch):
    _patch_extractors(monkeypatch, results={
        "risks": [{"description": "risk", "evidence_text": "evidence", "probability": "High", "impact": "High"}]
    })
    document_id = _insert_document(db_path, collection_id, doc_category="risk_register")
    _insert_chunk(db_path, document_id, 0, "evidence text here")

    analyze_document(document_id, db_path=db_path)

    connection = get_connection(db_path)
    risk_level = connection.execute("SELECT risk_level FROM risks").fetchone()["risk_level"]
    connection.close()
    assert risk_level == "Critical"


def test_analyze_document_uses_model_risk_level_when_valid(db_path, collection_id, monkeypatch):
    _patch_extractors(monkeypatch, results={
        "risks": [{"description": "risk", "evidence_text": "evidence", "probability": "Low", "impact": "Low", "risk_level": "High"}]
    })
    document_id = _insert_document(db_path, collection_id, doc_category="risk_register")
    _insert_chunk(db_path, document_id, 0, "evidence text here")

    analyze_document(document_id, db_path=db_path)

    connection = get_connection(db_path)
    risk_level = connection.execute("SELECT risk_level FROM risks").fetchone()["risk_level"]
    connection.close()
    assert risk_level == "High"


def test_resolve_trace_links_matches_requirement_and_test_by_ref(db_path, collection_id):
    connection = get_connection(db_path)
    document_id = connection.execute(
        "INSERT INTO documents (collection_id, filename, file_type) VALUES (?, ?, ?)",
        (collection_id, "doc.pdf", "pdf"),
    ).lastrowid
    requirement_id = connection.execute(
        "INSERT INTO requirements (requirement_ref, collection_id, document_id, requirement_text, evidence_text) "
        "VALUES (?, ?, ?, ?, ?)",
        ("REQ-001", collection_id, document_id, "requirement text", "evidence"),
    ).lastrowid
    test_id = connection.execute(
        "INSERT INTO test_results (test_ref, collection_id, document_id, test_name, requirement_ref, "
        "test_status, evidence_text) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("TC-001", collection_id, document_id, "test name", "REQ-001", "pass", "evidence"),
    ).lastrowid
    connection.commit()
    connection.close()

    result = resolve_trace_links(collection_id, db_path=db_path)

    assert result["links_created"] == 1
    connection = get_connection(db_path)
    link = connection.execute("SELECT * FROM trace_links WHERE collection_id = ?", (collection_id,)).fetchone()
    connection.close()
    assert link["source_type"] == "requirement"
    assert link["source_id"] == requirement_id
    assert link["target_type"] == "test"
    assert link["target_id"] == test_id


def test_resolve_trace_links_matches_risk_to_milestone_by_name(db_path, collection_id):
    connection = get_connection(db_path)
    document_id = connection.execute(
        "INSERT INTO documents (collection_id, filename, file_type) VALUES (?, ?, ?)",
        (collection_id, "doc.pdf", "pdf"),
    ).lastrowid
    connection.execute(
        "INSERT INTO risks (risk_ref, collection_id, document_id, description, affected_milestone, evidence_text) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("RISK-001", collection_id, document_id, "risk", "Integration Testing", "evidence"),
    )
    connection.execute(
        "INSERT INTO milestones (milestone_ref, collection_id, document_id, name, evidence_text) "
        "VALUES (?, ?, ?, ?, ?)",
        ("MS-001", collection_id, document_id, "Integration Testing", "evidence"),
    )
    connection.commit()
    connection.close()

    result = resolve_trace_links(collection_id, db_path=db_path)

    assert result["links_created"] == 1


def test_resolve_trace_links_clears_previous_links_before_recomputing(db_path, collection_id):
    connection = get_connection(db_path)
    document_id = connection.execute(
        "INSERT INTO documents (collection_id, filename, file_type) VALUES (?, ?, ?)",
        (collection_id, "doc.pdf", "pdf"),
    ).lastrowid
    connection.execute(
        "INSERT INTO requirements (requirement_ref, collection_id, document_id, requirement_text, evidence_text) "
        "VALUES (?, ?, ?, ?, ?)",
        ("REQ-001", collection_id, document_id, "requirement", "evidence"),
    )
    connection.execute(
        "INSERT INTO test_results (test_ref, collection_id, document_id, test_name, requirement_ref, "
        "test_status, evidence_text) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("TC-001", collection_id, document_id, "test", "REQ-001", "pass", "evidence"),
    )
    connection.commit()
    connection.close()

    resolve_trace_links(collection_id, db_path=db_path)
    result = resolve_trace_links(collection_id, db_path=db_path)

    assert result["links_created"] == 1
    connection = get_connection(db_path)
    count = connection.execute(
        "SELECT COUNT(*) AS count FROM trace_links WHERE collection_id = ?", (collection_id,)
    ).fetchone()["count"]
    connection.close()
    assert count == 1


def test_get_project_status_handles_empty_collection(db_path, collection_id):
    status = get_project_status(collection_id, db_path=db_path)

    assert status["health"]["requirements"] == 0.0
    assert status["health"]["schedule"] == 0.0
    assert status["health"]["integration"] == 0.0
    assert status["risk_summary"] == {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    assert status["recent_decisions"] == []
    assert status["upcoming_milestones"] == []


def test_get_project_status_computes_health_formulas(db_path, collection_id):
    connection = get_connection(db_path)
    document_id = connection.execute(
        "INSERT INTO documents (collection_id, filename, file_type, doc_category) VALUES (?, ?, ?, ?)",
        (collection_id, "doc.pdf", "pdf", "requirements"),
    ).lastrowid

    requirement_id = connection.execute(
        "INSERT INTO requirements (requirement_ref, collection_id, document_id, requirement_text, evidence_text) "
        "VALUES (?, ?, ?, ?, ?)",
        ("REQ-001", collection_id, document_id, "req 1", "evidence"),
    ).lastrowid
    connection.execute(
        "INSERT INTO requirements (requirement_ref, collection_id, document_id, requirement_text, evidence_text) "
        "VALUES (?, ?, ?, ?, ?)",
        ("REQ-002", collection_id, document_id, "req 2", "evidence"),
    )

    test_id = connection.execute(
        "INSERT INTO test_results (test_ref, collection_id, document_id, test_name, requirement_ref, "
        "test_status, evidence_text) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("TC-001", collection_id, document_id, "test 1", "REQ-001", "Pass", "evidence"),
    ).lastrowid
    connection.execute(
        "INSERT INTO trace_links (collection_id, source_type, source_id, target_type, target_id, match_basis) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (collection_id, "requirement", requirement_id, "test", test_id, "test"),
    )

    connection.execute(
        "INSERT INTO milestones (milestone_ref, collection_id, document_id, name, status, evidence_text) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("MS-001", collection_id, document_id, "Integration Testing", "on_track", "evidence"),
    )
    connection.execute(
        "INSERT INTO milestones (milestone_ref, collection_id, document_id, name, status, evidence_text) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("MS-002", collection_id, document_id, "Final Delivery", "delayed", "evidence"),
    )

    connection.execute(
        "INSERT INTO risks (risk_ref, collection_id, document_id, description, risk_level, evidence_text) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        ("RISK-001", collection_id, document_id, "risk", "Critical", "evidence"),
    )

    connection.commit()
    connection.close()

    status = get_project_status(collection_id, db_path=db_path)

    assert status["health"]["requirements"] == 50.0
    assert status["health"]["schedule"] == 50.0
    assert status["health"]["integration"] == 100.0
    assert status["health"]["documentation"] == 12.5
    assert status["risk_summary"]["Critical"] == 1
    assert status["status_summary"]["milestones_delayed"] == 1
    assert status["status_summary"]["milestones_on_track"] == 1
