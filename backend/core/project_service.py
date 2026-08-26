from backend.core.config import DB_PATH, EXTRACTION_CHUNK_BATCH_SIZE, EXTRACTORS_BY_CATEGORY
from backend.core.extractor import (
    extract_decisions,
    extract_milestones,
    extract_requirements,
    extract_risks,
    extract_test_results,
)
from backend.database.db import get_connection

def _run_extractor(name: str, chunks: list[dict]) -> list[dict]:
    # Dispatches by name (rather than a name->function dict built at import
    # time) so tests can monkeypatch backend.core.project_service.extract_*
    # and have analyze_document actually observe the patched function.
    if name == "risks":
        return extract_risks(chunks)
    if name == "decisions":
        return extract_decisions(chunks)
    if name == "requirements":
        return extract_requirements(chunks)
    if name == "milestones":
        return extract_milestones(chunks)
    if name == "test_results":
        return extract_test_results(chunks)
    raise ValueError(f"unknown extractor: {name}")

_RISK_LEVEL_MATRIX = {
    ("high", "high"): "Critical",
    ("high", "medium"): "High",
    ("high", "low"): "Medium",
    ("medium", "high"): "High",
    ("medium", "medium"): "Medium",
    ("medium", "low"): "Low",
    ("low", "high"): "Medium",
    ("low", "medium"): "Low",
    ("low", "low"): "Low",
}

_VALID_RISK_LEVELS = {"Critical", "High", "Medium", "Low"}


def _normalize_risk_level(risk_level, probability, impact) -> str | None:
    if risk_level and risk_level.strip().title() in _VALID_RISK_LEVELS:
        return risk_level.strip().title()
    # The model sometimes omits or corrupts the risk_level field even when it
    # correctly extracts probability/impact; a standard PM risk matrix lets us
    # derive it deterministically from those two fields instead of losing it.
    if probability and impact:
        return _RISK_LEVEL_MATRIX.get((probability.strip().lower(), impact.strip().lower()))
    return None


def _batched(rows: list, size: int) -> list[list]:
    return [rows[i:i + size] for i in range(0, len(rows), size)]


def _resolve_chunk_id(evidence_text: str | None, batch_rows: list) -> int | None:
    if not evidence_text or not evidence_text.strip():
        return None
    for row in batch_rows:
        if evidence_text.strip() in row["chunk_text"]:
            return row["id"]
    return None


def _next_ref_number(connection, table: str, ref_column: str, collection_id: int) -> int:
    rows = connection.execute(
        f"SELECT {ref_column} AS ref FROM {table} WHERE collection_id = ?", (collection_id,)
    ).fetchall()
    max_number = 0
    for row in rows:
        suffix = row["ref"].rsplit("-", 1)[-1]
        if suffix.isdigit():
            max_number = max(max_number, int(suffix))
    return max_number + 1


def _delete_existing_analysis(connection, document_id: int) -> None:
    for table in ("risks", "decisions", "requirements", "milestones", "test_results"):
        connection.execute(f"DELETE FROM {table} WHERE document_id = ?", (document_id,))


def _insert_extracted_item(
    connection, extractor_name: str, ref: str, collection_id: int, document_id: int, chunk_id: int | None, item: dict
) -> bool:
    evidence_text = item.get("evidence_text")
    if not evidence_text:
        return False

    if extractor_name == "risks":
        description = item.get("description")
        if not description:
            return False
        connection.execute(
            "INSERT INTO risks (risk_ref, collection_id, document_id, chunk_id, description, "
            "probability, impact, risk_level, affected_milestone, responsible, evidence_text) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ref, collection_id, document_id, chunk_id, description,
                item.get("probability"), item.get("impact"),
                _normalize_risk_level(item.get("risk_level"), item.get("probability"), item.get("impact")),
                item.get("affected_milestone"), item.get("responsible"), evidence_text,
            ),
        )
    elif extractor_name == "decisions":
        decision_text = item.get("decision_text")
        if not decision_text:
            return False
        connection.execute(
            "INSERT INTO decisions (decision_ref, collection_id, document_id, chunk_id, decision_text, "
            "decision_date, reason, affected_area, evidence_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ref, collection_id, document_id, chunk_id, decision_text,
                item.get("decision_date"), item.get("reason"), item.get("affected_area"), evidence_text,
            ),
        )
    elif extractor_name == "requirements":
        requirement_text = item.get("requirement_text")
        if not requirement_text:
            return False
        connection.execute(
            "INSERT INTO requirements (requirement_ref, collection_id, document_id, chunk_id, "
            "requirement_text, status, evidence_text) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (ref, collection_id, document_id, chunk_id, requirement_text, item.get("status"), evidence_text),
        )
    elif extractor_name == "milestones":
        name = item.get("name")
        if not name:
            return False
        connection.execute(
            "INSERT INTO milestones (milestone_ref, collection_id, document_id, chunk_id, name, "
            "due_date, status, evidence_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ref, collection_id, document_id, chunk_id, name, item.get("due_date"), item.get("status"), evidence_text),
        )
    elif extractor_name == "test_results":
        test_name = item.get("test_name")
        if not test_name:
            return False
        connection.execute(
            "INSERT INTO test_results (test_ref, collection_id, document_id, chunk_id, test_name, "
            "requirement_ref, test_status, evidence_text) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (ref, collection_id, document_id, chunk_id, test_name, item.get("requirement_ref"), item.get("test_status"), evidence_text),
        )
    else:
        return False

    return True


_REF_PREFIX = {
    "risks": ("risks", "risk_ref", "RISK"),
    "decisions": ("decisions", "decision_ref", "DEC"),
    "requirements": ("requirements", "requirement_ref", "REQ"),
    "milestones": ("milestones", "milestone_ref", "MS"),
    "test_results": ("test_results", "test_ref", "TC"),
}


def analyze_document(document_id: int, db_path: str = DB_PATH) -> dict:
    connection = get_connection(db_path)
    try:
        document = connection.execute(
            "SELECT id, collection_id, filename, doc_category FROM documents WHERE id = ?", (document_id,)
        ).fetchone()
        if document is None:
            raise ValueError(f"document not found: {document_id}")

        collection_id = document["collection_id"]
        doc_category = document["doc_category"] or "other"
        extractor_names = EXTRACTORS_BY_CATEGORY.get(doc_category, EXTRACTORS_BY_CATEGORY["other"])

        _delete_existing_analysis(connection, document_id)

        chunk_rows = connection.execute(
            "SELECT id, chunk_index, chunk_text FROM chunks WHERE document_id = ? ORDER BY chunk_index",
            (document_id,),
        ).fetchall()

        counts = {name: 0 for name in extractor_names}
        next_ref_numbers = {
            name: _next_ref_number(connection, *_REF_PREFIX[name][:2], collection_id) for name in extractor_names
        }

        for batch_rows in _batched(chunk_rows, EXTRACTION_CHUNK_BATCH_SIZE):
            batch_chunks = [
                {"document_name": document["filename"], "chunk_index": row["chunk_index"], "chunk_text": row["chunk_text"]}
                for row in batch_rows
            ]
            for extractor_name in extractor_names:
                items = _run_extractor(extractor_name, batch_chunks)
                _, _, prefix = _REF_PREFIX[extractor_name]
                for item in items:
                    ref = f"{prefix}-{next_ref_numbers[extractor_name]:03d}"
                    chunk_id = _resolve_chunk_id(item.get("evidence_text"), batch_rows)
                    inserted = _insert_extracted_item(
                        connection, extractor_name, ref, collection_id, document_id, chunk_id, item
                    )
                    if inserted:
                        next_ref_numbers[extractor_name] += 1
                        counts[extractor_name] += 1

        connection.commit()
        return {"document_id": document_id, "doc_category": doc_category, **counts}
    finally:
        connection.close()


def _insert_trace_link(connection, collection_id, source_type, source_id, target_type, target_id, match_basis) -> None:
    connection.execute(
        "INSERT INTO trace_links (collection_id, source_type, source_id, target_type, target_id, match_basis) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (collection_id, source_type, source_id, target_type, target_id, match_basis),
    )


def _names_match(a: str, b: str) -> bool:
    a, b = a.strip().lower(), b.strip().lower()
    return bool(a) and bool(b) and (a in b or b in a)


def resolve_trace_links(collection_id: int, db_path: str = DB_PATH) -> dict:
    connection = get_connection(db_path)
    try:
        connection.execute("DELETE FROM trace_links WHERE collection_id = ?", (collection_id,))

        requirements = connection.execute(
            "SELECT id, requirement_ref FROM requirements WHERE collection_id = ?", (collection_id,)
        ).fetchall()
        tests = connection.execute(
            "SELECT id, requirement_ref FROM test_results WHERE collection_id = ?", (collection_id,)
        ).fetchall()
        risks = connection.execute(
            "SELECT id, affected_milestone FROM risks WHERE collection_id = ?", (collection_id,)
        ).fetchall()
        decisions = connection.execute(
            "SELECT id, affected_area FROM decisions WHERE collection_id = ?", (collection_id,)
        ).fetchall()
        milestones = connection.execute(
            "SELECT id, name FROM milestones WHERE collection_id = ?", (collection_id,)
        ).fetchall()

        links_created = 0

        for test in tests:
            if not test["requirement_ref"]:
                continue
            for requirement in requirements:
                if requirement["requirement_ref"] and requirement["requirement_ref"] == test["requirement_ref"]:
                    _insert_trace_link(
                        connection, collection_id, "requirement", requirement["id"], "test", test["id"],
                        "requirement_ref match",
                    )
                    links_created += 1

        for risk in risks:
            if not risk["affected_milestone"]:
                continue
            for milestone in milestones:
                if milestone["name"] and _names_match(risk["affected_milestone"], milestone["name"]):
                    _insert_trace_link(
                        connection, collection_id, "risk", risk["id"], "milestone", milestone["id"],
                        "affected_milestone name match",
                    )
                    links_created += 1

        for decision in decisions:
            if not decision["affected_area"]:
                continue
            for milestone in milestones:
                if milestone["name"] and _names_match(decision["affected_area"], milestone["name"]):
                    _insert_trace_link(
                        connection, collection_id, "decision", decision["id"], "milestone", milestone["id"],
                        "affected_area name match",
                    )
                    links_created += 1

        connection.commit()
        return {"links_created": links_created}
    finally:
        connection.close()


def _percentage(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100, 1)


def get_project_status(collection_id: int, db_path: str = DB_PATH) -> dict:
    connection = get_connection(db_path)
    try:
        requirements_total = connection.execute(
            "SELECT COUNT(*) AS count FROM requirements WHERE collection_id = ?", (collection_id,)
        ).fetchone()["count"]
        requirements_verified = connection.execute(
            "SELECT COUNT(DISTINCT tl.source_id) AS count FROM trace_links tl "
            "JOIN test_results t ON tl.target_type = 'test' AND tl.target_id = t.id "
            "WHERE tl.collection_id = ? AND tl.source_type = 'requirement' AND LOWER(t.test_status) = 'pass'",
            (collection_id,),
        ).fetchone()["count"]

        milestones_total = connection.execute(
            "SELECT COUNT(*) AS count FROM milestones WHERE collection_id = ?", (collection_id,)
        ).fetchone()["count"]
        milestones_on_track = connection.execute(
            "SELECT COUNT(*) AS count FROM milestones WHERE collection_id = ? "
            "AND (status IS NULL OR LOWER(status) != 'delayed')",
            (collection_id,),
        ).fetchone()["count"]

        tests_total = connection.execute(
            "SELECT COUNT(*) AS count FROM test_results WHERE collection_id = ?", (collection_id,)
        ).fetchone()["count"]
        tests_passed = connection.execute(
            "SELECT COUNT(*) AS count FROM test_results WHERE collection_id = ? AND LOWER(test_status) = 'pass'",
            (collection_id,),
        ).fetchone()["count"]

        doc_categories_present = connection.execute(
            "SELECT COUNT(DISTINCT doc_category) AS count FROM documents "
            "WHERE collection_id = ? AND doc_category IS NOT NULL AND doc_category != 'other'",
            (collection_id,),
        ).fetchone()["count"]

        risk_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for row in connection.execute(
            "SELECT risk_level, COUNT(*) AS count FROM risks WHERE collection_id = ? GROUP BY risk_level",
            (collection_id,),
        ):
            if row["risk_level"] in risk_counts:
                risk_counts[row["risk_level"]] = row["count"]

        milestones_delayed = milestones_total - milestones_on_track

        recent_decisions = [
            dict(row)
            for row in connection.execute(
                "SELECT decision_ref, decision_text, decision_date, created_at FROM decisions "
                "WHERE collection_id = ? ORDER BY id DESC LIMIT 5",
                (collection_id,),
            )
        ]
        upcoming_milestones = [
            dict(row)
            for row in connection.execute(
                "SELECT milestone_ref, name, due_date, status FROM milestones "
                "WHERE collection_id = ? AND (status IS NULL OR LOWER(status) != 'completed') "
                "ORDER BY due_date IS NULL, due_date LIMIT 5",
                (collection_id,),
            )
        ]

        return {
            "health": {
                "requirements": _percentage(requirements_verified, requirements_total),
                "schedule": _percentage(milestones_on_track, milestones_total),
                "integration": _percentage(tests_passed, tests_total),
                "documentation": _percentage(doc_categories_present, 8),
            },
            "risk_summary": risk_counts,
            "status_summary": {
                "milestones_on_track": milestones_on_track,
                "milestones_delayed": milestones_delayed,
                "tests_passed": tests_passed,
                "tests_total": tests_total,
            },
            "recent_decisions": recent_decisions,
            "upcoming_milestones": upcoming_milestones,
        }
    finally:
        connection.close()
