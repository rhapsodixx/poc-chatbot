# 🎫 satusatu.com — RAG Customer Support Chatbot

A Retrieval-Augmented Generation (RAG) chatbot for [satusatu.com](https://satusatu.com), an attraction & ticketing platform. The chatbot answers customer queries about products, itineraries, and tickets using knowledge scraped directly from the website, with strict domain confinement and graceful human handoff.

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐
│   Next.js   │────▶│   FastAPI        │────▶│   ChromaDB   │
│   Frontend  │◀────│   Backend        │◀────│   (Vectors)  │
│   :3000     │     │   :8000          │     │   :8001      │
└─────────────┘     │                  │     └──────────────┘
                    │   ┌──────────┐   │
                    │   │OpenRouter│   │
                    │   │ Gemini   │   │
                    │   │ GPT-4o   │   │
                    │   └──────────┘   │
                    └─────────────────┘
```

## ⚡ Quick Start

### Prerequisites

- **Docker** (v20+) or **Podman** (v4+) with `podman-compose`
- **Node.js** 20+ (for local frontend development)
- An [OpenRouter](https://openrouter.ai/) API key

### 1. Clone & Configure

```bash
git clone <repo-url> poc-chatbot-satusatu
cd poc-chatbot-satusatu

# Copy the sample env file and add your API key
cp .env.sample .env
# Edit .env and set OPENROUTER_API_KEY=your-key-here
```

### 2. Build & Run

```bash
# Docker
docker compose up --build

# Podman
podman-compose up --build
```

### 3. Verify

| Service      | URL                                  | Health Check                |
| :----------- | :----------------------------------- | :-------------------------- |
| **Backend**  | http://localhost:8000                 | `GET /health` → `{"status": "ok"}` |
| **ChromaDB** | http://localhost:8001                 | `GET /api/v1/heartbeat`     |
| **Frontend** | http://localhost:3000 *(Phase 4)*     | —                           |
| **API Docs** | http://localhost:8000/docs            | Swagger UI                  |

```bash
# Quick health checks
curl http://localhost:8000/health
curl http://localhost:8001/api/v1/heartbeat
```

---

## 📁 Project Structure

```
poc-chatbot-satusatu/
├── backend/                    # FastAPI Python backend
│   ├── app/
│   │   ├── main.py             # App entry point & factory
│   │   ├── config.py           # Environment-based settings
│   │   ├── routers/
│   │   │   └── chat.py         # POST /api/chat endpoint
│   │   ├── services/
│   │   │   ├── llm.py          # OpenRouter LLM client
│   │   │   └── vectorstore.py  # ChromaDB client
│   │   └── ingestion/
│   │       └── pipeline.py     # Sitemap scraping pipeline
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── frontend/                   # Next.js chat UI (Phase 4)
├── docs/                       # Project documentation
├── docker-compose.yml          # Orchestration (Docker/Podman)
├── .env.sample                 # Environment variable template
└── chatbot_architecture_proposal.md
```

---

## 🏗️ Architecture

The system implements a **3-step guardrail RAG pipeline**:

1. **Intent Router** — Classifies if the query is about satusatu.com products/services. Off-topic queries receive a polite redirect.
2. **Semantic Confidence** — Retrieves relevant chunks from ChromaDB and checks similarity scores against a threshold. Low-confidence matches trigger human handoff.
3. **Conditioned Generation** — Sends context + query to the LLM with strict system prompts. If the LLM cannot answer from context, it returns `TRIGGER_HANDOFF`.

**LLM Strategy:** Primary model is **Google Gemini 1.5 Flash** via OpenRouter, with automatic fallback to **GPT-4o-mini**.

---

## 🔧 Development

### Backend Only (without Docker)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Environment Variables

See [`.env.sample`](.env.sample) for all configurable variables. Key ones:

| Variable                     | Description                          | Default                       |
| :--------------------------- | :----------------------------------- | :---------------------------- |
| `OPENROUTER_API_KEY`         | Your OpenRouter API key              | *(required)*                  |
| `OPENROUTER_PRIMARY_MODEL`   | Primary LLM model                    | `google/gemini-flash-1.5`     |
| `OPENROUTER_FALLBACK_MODEL`  | Fallback LLM model                   | `openai/gpt-4o-mini`          |
| `CHROMA_HOST`                | ChromaDB host                        | `chromadb`                    |
| `CHROMA_PORT`                | ChromaDB port                        | `8000`                        |
| `SIMILARITY_THRESHOLD`       | Minimum cosine similarity for chunks | `0.35`                        |

---

## 📝 License

Private — satusatu.com internal project.