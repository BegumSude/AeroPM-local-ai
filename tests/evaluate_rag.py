import json
import sys
import time
from pathlib import Path

from backend.core.config import DB_PATH
from backend.core.rag_service import ask_question

QUESTIONS_PATH = Path(__file__).resolve().parent / "test_questions.json"
RESULTS_PATH = Path(__file__).resolve().parent / "evaluation_results.json"


def load_questions(path: Path = QUESTIONS_PATH) -> list[dict]:
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def evaluate_question(question_item: dict, collection_id: int, top_k: int = 5, db_path: str = DB_PATH) -> dict:
    question = question_item["question"]
    category = question_item["category"]

    if not question or not question.strip():
        return {
            "question": question,
            "category": category,
            "answer": None,
            "source_found": False,
            "chunks_used": [],
            "response_time_ms": None,
            "error": "question bos oldugu icin calistirilamadi",
        }

    start_time = time.perf_counter()
    result = ask_question(question, collection_id, top_k=top_k, db_path=db_path)
    response_time_ms = (time.perf_counter() - start_time) * 1000

    return {
        "question": question,
        "category": category,
        "answer": result["answer"],
        "source_found": len(result["sources"]) > 0,
        "chunks_used": result["sources"],
        "response_time_ms": response_time_ms,
        "error": None,
    }


def run_evaluation(
    collection_id: int, top_k: int = 5, questions_path: Path = QUESTIONS_PATH, db_path: str = DB_PATH
) -> list[dict]:
    questions = load_questions(questions_path)
    return [evaluate_question(item, collection_id, top_k, db_path) for item in questions]


def save_results(results: list[dict], path: Path = RESULTS_PATH) -> None:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(results, file, ensure_ascii=False, indent=2)


def main() -> None:
    if len(sys.argv) < 2:
        print("Kullanim: python3 tests/evaluate_rag.py <collection_id> [top_k]")
        sys.exit(1)

    collection_id = int(sys.argv[1])
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else 5

    results = run_evaluation(collection_id, top_k)
    save_results(results)
    print(f"{len(results)} soru degerlendirildi, sonuclar {RESULTS_PATH} dosyasina yazildi.")


if __name__ == "__main__":
    main()
