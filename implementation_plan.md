# Phase 1: Foundation & Orchestration — Implementation Plan

Build the monorepo skeleton, Docker orchestration, and project scaffolding for the satusatu.com RAG chatbot MVP.

## Proposed Changes

### Monorepo Directory Structure

Create the following directory layout at the project root:

```
poc-chatbot-satusatu/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Settings via pydantic-settings
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── chat.py          # Chat endpoint (stub)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── llm.py           # OpenRouter client (stub)
│   │   │   └── vectorstore.py   # ChromaDB client (stub)
│   │   └── ingestion/
│   │       ├── __init__.py
│   │       └── pipeline.py      # Ingestion pipeline (stub)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── frontend/                    # Next.js app (Phase 4)
│   └── .gitkeep
├── docs/
│   └── .gitkeep
├── docker-compose.yml
├── .env.sample
├── README.md
└── chatbot_architecture_proposal.md  (existing)
```

---

### Docker & Orchestration

#### [NEW] [docker-compose.yml](file:///Users/panji.gautama/Documents/Project/poc-chatbot-satusatu/docker-compose.yml)

Three services, Podman-compatible (no Docker-specific features):
- **backend**: FastAPI app on port `8000`, depends on ChromaDB
- **chromadb**: Official `chromadb/chroma` image on port `8001`
- **frontend**: Placeholder service (Next.js, port `3000`) — will be fleshed out in Phase 4

Uses named volumes for ChromaDB persistence. Environment variables loaded from `.env`.

#### [NEW] [.env.sample](file:///Users/panji.gautama/Documents/Project/poc-chatbot-satusatu/.env.sample)

All required env vars with placeholder values:
- `OPENROUTER_API_KEY`
- `OPENROUTER_PRIMARY_MODEL` (default: `google/gemini-flash-1.5`)
- `OPENROUTER_FALLBACK_MODEL` (default: `openai/gpt-4o-mini`)
- `CHROMA_HOST`, `CHROMA_PORT`
- `CHROMA_COLLECTION_NAME`
- `SITE_URL` (target sitemap URL)

---

### Backend Skeleton

#### [NEW] [Dockerfile](file:///Users/panji.gautama/Documents/Project/poc-chatbot-satusatu/backend/Dockerfile)

Multi-stage Python 3.12-slim image. Installs `requirements.txt`, copies app code, runs uvicorn.

#### [NEW] [requirements.txt](file:///Users/panji.gautama/Documents/Project/poc-chatbot-satusatu/backend/requirements.txt)

Core dependencies: `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `httpx`, `chromadb`, `beautifulsoup4`, `lxml`.

#### [NEW] [main.py](file:///Users/panji.gautama/Documents/Project/poc-chatbot-satusatu/backend/app/main.py)

FastAPI app with CORS middleware, health check endpoint (`/health`), and router inclusion for `/api/chat`.

#### [NEW] [config.py](file:///Users/panji.gautama/Documents/Project/poc-chatbot-satusatu/backend/app/config.py)

Pydantic `BaseSettings` loading all env vars with sensible defaults.

#### [NEW] Stubs for `routers/chat.py`, `services/llm.py`, `services/vectorstore.py`, `ingestion/pipeline.py`

Minimal placeholder files with docstrings and `pass` bodies — to be implemented in Phases 2 & 3.

---

### Documentation

#### [MODIFY] [README.md](file:///Users/panji.gautama/Documents/Project/poc-chatbot-satusatu/README.md)

Comprehensive README with:
1. Project overview & architecture diagram (ASCII)
2. Prerequisites (Docker/Podman, Node.js)
3. Quick start: `cp .env.sample .env` → `docker compose up --build`
4. Service URLs table
5. Project structure overview
6. Development workflow tips

---

### Gitignore Updates

#### [MODIFY] [.gitignore](file:///Users/panji.gautama/Documents/Project/poc-chatbot-satusatu/.gitignore)

Add Python-specific ignores (`__pycache__`, `*.pyc`, `.venv`, `*.egg-info`), Docker volumes, and ChromaDB data directory.

---

## Verification Plan

### Automated Tests

1. **Docker Compose validation** — `docker compose config` (or `podman-compose config`) should parse without errors
2. **Backend container build** — `docker compose build backend` should complete successfully
3. **Health check** — After `docker compose up -d`, `curl http://localhost:8000/health` should return `{"status": "ok"}`
4. **ChromaDB connectivity** — `curl http://localhost:8001/api/v1/heartbeat` should return a valid response

### Manual Verification

1. Run `docker compose up --build` from the project root and confirm all 3 services start without errors in the logs
2. Verify the `.env.sample` contains all documented variables
3. Confirm the README instructions can be followed end-to-end by a new developer
