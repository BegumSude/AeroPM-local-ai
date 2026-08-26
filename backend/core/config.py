CHUNK_SIZE = 800
CHUNK_OVERLAP = 150

DB_PATH = "backend/database/rag.db"

EMBEDDING_MODEL_ALIAS = "qwen3-embedding-0.6b"

CHAT_MODEL_ALIAS = "phi-3.5-mini"

EXTRACTION_CHUNK_BATCH_SIZE = 4

DOC_CATEGORIES = [
    "project_charter",
    "requirements",
    "project_plan",
    "risk_register",
    "meeting_minutes",
    "test_report",
    "change_requests",
    "lessons_learned",
    "other",
]

EXTRACTORS_BY_CATEGORY = {
    "project_charter": [],
    "requirements": ["requirements"],
    "project_plan": ["milestones"],
    "risk_register": ["risks"],
    "meeting_minutes": ["decisions", "risks"],
    "test_report": ["test_results"],
    "change_requests": ["decisions"],
    "lessons_learned": ["risks", "decisions"],
    "other": ["risks", "decisions", "requirements", "milestones", "test_results"],
}
