import json

import pytest

from backend.core.embedder import FOUNDRY_LOCAL_AVAILABLE
from backend.database.db import get_connection, init_db
from tests.evaluate_rag import evaluate_question, load_questions, run_evaluation, save_results

requires_foundry_local = pytest.mark.skipif(
    not FOUNDRY_LOCAL_AVAILABLE, reason="foundry-local-sdk kurulu degil"
)

REQUIRED_CATEGORIES = {
    "cevabi_belgede_var",
    "cevabi_belgede_yok",
    "belirsiz_genel",
    "bos_soru",
}


def test_questions_file_covers_required_categories():
    questions = load_questions()
    categories = {item["category"] for item in questions}
    assert REQUIRED_CATEGORIES.issubset(categories)


def test_load_questions_returns_list_of_dicts_with_question_and_category():
    questions = load_questions()
    assert len(questions) > 0
    for item in questions:
        assert "question" in item
        assert "category" in item


def test_evaluate_question_skips_ask_question_for_empty_question(monkeypatch):
    calls = []
    monkeypatch.setattr("tests.evaluate_rag.ask_question", lambda *args, **kwargs: calls.append(1))

    result = evaluate_question({"question": "", "category": "bos_soru"}, collection_id=1)

    assert calls == []
    assert result["answer"] is None
    assert result["source_found"] is False
    assert result["chunks_used"] == []
    assert result["response_time_ms"] is None
    assert result["error"] is not None


def test_evaluate_question_maps_ask_question_result_correctly(monkeypatch):
    fake_sources = [{"document_name": "a.txt", "chunk_index": 0, "similarity_score": 0.9}]
    monkeypatch.setattr(
        "tests.evaluate_rag.ask_question",
        lambda question, collection_id, top_k, db_path: {"answer": "cevap", "sources": fake_sources},
    )

    result = evaluate_question({"question": "soru", "category": "cevabi_belgede_var"}, collection_id=1)

    assert result["answer"] == "cevap"
    assert result["source_found"] is True
    assert result["chunks_used"] == fake_sources
    assert result["response_time_ms"] >= 0
    assert result["error"] is None


def test_run_evaluation_produces_one_result_per_question(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "tests.evaluate_rag.ask_question",
        lambda question, collection_id, top_k, db_path: {"answer": "cevap", "sources": []},
    )

    questions_path = tmp_path / "questions.json"
    questions_path.write_text(
        json.dumps(
            [
                {"question": "soru 1", "category": "cevabi_belgede_var"},
                {"question": "", "category": "bos_soru"},
            ]
        )
    )

    results = run_evaluation(collection_id=1, questions_path=questions_path)

    assert len(results) == 2


def test_save_results_writes_valid_json(tmp_path):
    results = [{"question": "soru", "category": "cevabi_belgede_var", "answer": "cevap"}]
    output_path = tmp_path / "evaluation_results.json"

    save_results(results, path=output_path)

    with open(output_path, encoding="utf-8") as file:
        saved_results = json.load(file)
    assert saved_results == results


@requires_foundry_local
def test_run_evaluation_end_to_end_with_real_foundry_local(tmp_path):
    from backend.core.rag_service import index_document

    db_path = str(tmp_path / "rag.db")
    init_db(db_path)

    connection = get_connection(db_path)
    collection_id = connection.execute(
        "INSERT INTO collections (name) VALUES (?)", ("evaluation",)
    ).lastrowid
    connection.commit()
    connection.close()

    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("Bu bir test belgesidir. Chunk boyutu 800 karakterdir.")
    index_document(str(sample_file), collection_id, db_path=db_path)

    results = run_evaluation(collection_id, db_path=db_path)

    assert len(results) == len(load_questions())
