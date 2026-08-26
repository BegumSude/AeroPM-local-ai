# AeroPM — Local AI-Powered Project Intelligence

A fully local, offline document intelligence application for aviation
project management. Upload project documents (PDF/DOCX/TXT/MD) and it
answers questions grounded in their content, and automatically extracts
structured risks, decisions, requirements, milestones and test results —
all powered by **Microsoft Foundry Local**, with no cloud LLM, no external
vector database, and no data ever leaving your machine.

## What it does

- **Document Q&A (RAG)** — ask questions about uploaded documents and get
  answers grounded only in their content, with cited sources.
- **Structured extraction** — reads a document and pulls out risks,
  decisions, requirements, milestones and test results as structured
  records, based on the document's category.
- **Traceability** — automatically links requirements to the tests that
  verify them, and risks/decisions to the milestones they affect.
- **Project health dashboard** — an overview of requirement coverage,
  schedule health, test pass rate, documentation completeness and risk
  distribution, computed from the extracted data.

## Why it's local

Every model call — embeddings, chat answers, and structured JSON
extraction — runs through **Microsoft Foundry Local**. No OpenAI, no
ChromaDB/Pinecone, no other cloud LLM. Vectors are stored as BLOBs in a
single SQLite database; there is no separate vector store.

## Architecture

```
                 ┌────────────────────────┐
  PDF/DOCX/TXT   │   backend/core/         │
  /MD upload ───▶│   document_loader.py    │
                 │   chunker.py            │──▶ embedder.py ──▶ SQLite (chunks + embeddings)
                 └────────────────────────┘         │
                                                     │  (Foundry Local: qwen3-embedding-0.6b)
        ┌────────────────────────────────────────────┘
        ▼
  retriever.py (cosine similarity) ──▶ generator.py ──▶ answer + cited sources
                                          │
                                          │  (Foundry Local: phi-3.5-mini)
                                          ▼
                                    extractor.py ──▶ project_service.py ──▶ risks / decisions /
                                 (structured JSON)     (trace links, health)   requirements / milestones /
                                                                               test results
```

- `backend/core/` — framework-free Python business logic (document
  loading, chunking, embedding, retrieval, generation, extraction).
  Every function here is independently unit-tested.
- `backend/database/db.py` — single SQLite schema: collections,
  documents, chunks, chat history, feedback, plus risks, decisions,
  requirements, milestones, test results and trace links.
- `backend/prompts/system_prompts.py` — the single source of truth for
  every prompt used by the app (RAG answering + one extraction prompt
  per entity type).
- `backend/api/main.py` — FastAPI layer exposing the above over REST.
- `react_frontend/` — React + TypeScript dashboard (Overview, Documents,
  Risks, Decisions, Requirements, Project Q&A).

## Tech stack

| Layer | Technology |
|---|---|
| Local AI runtime | Microsoft Foundry Local (`foundry-local-sdk`) |
| Chat / structured extraction model | `phi-3.5-mini` |
| Embedding model | `qwen3-embedding-0.6b` |
| Backend | Python 3.11+, FastAPI, SQLite |
| Document parsing | pypdf, python-docx |
| Numerics | NumPy |
| Frontend | React 19, TypeScript, Vite, React Router |
| Tests | pytest |

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for the frontend)
- [Microsoft Foundry Local](https://github.com/microsoft/Foundry-Local)
  installed, with the `phi-3.5-mini` and `qwen3-embedding-0.6b` models
  available in its catalog (they are downloaded automatically on first
  use).

### Backend

```bash
pip install -r requirements.txt
uvicorn backend.api.main:app --reload
```

The API starts on `http://localhost:8000` and initializes the SQLite
database on first run.

### Frontend

```bash
cd react_frontend
npm install
cp .env.example .env   # set VITE_API_BASE_URL if the backend isn't on :8000
npm run dev
```

The dashboard opens on `http://localhost:5173`.

### Try it with sample data

`data/samples/aviation/` contains a set of synthetic but realistic
aviation project documents (charter, requirements, risk register,
meeting minutes, test report, change requests, lessons learned) for
exercising the full pipeline without needing your own documents.
Regenerate or extend them with:

```bash
python3 scripts/generate_aviation_samples.py
```

### Basic workflow

1. Create a collection in the sidebar.
2. Go to **Documents**, pick a category, and upload a file.
3. Click **Analyze** to extract risks/decisions/requirements/milestones/
   test results from it.
4. Browse the **Risks**, **Decisions** and **Requirements** pages, or ask
   a question in **Project Q&A**.
5. Check **Overview** for the aggregated project health snapshot.

## Testing

```bash
pytest tests/
```

## Project rules

- `backend/core/` contains only pure, testable Python — no framework or
  UI code.
- All embedding, chat and extraction calls go through Microsoft Foundry
  Local; no cloud LLMs.
- Vectors live in SQLite; no separate vector database.
- Every model answer is grounded in the retrieved document context —
  the model is instructed not to invent information that isn't there.
