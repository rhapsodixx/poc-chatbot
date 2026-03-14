# Ingestion Pipeline Guide

How to populate the chatbot's knowledge base by scraping [satusatu.com](https://satusatu.com).

## Overview

The ingestion pipeline runs through 4 stages:

```
sitemap.xml → Fetch Pages → Clean HTML → Chunk Text → ChromaDB
```

1. **Sitemap Parser** — Fetches `sitemap.xml` and extracts all page URLs (supports nested sitemap indexes)
2. **Page Fetcher & Cleaner** — Downloads each page, strips non-content elements (nav, header, footer, scripts), extracts clean text from `<main>`, `<article>`, or `<body>`
3. **Semantic Chunker** — Splits text into ~512-word chunks by paragraph/heading boundaries with 50-word overlap
4. **ChromaDB Upsert** — Stores chunks with metadata (`url`, `title`, `page_type`) in batches of 50

## How to Trigger

### Option A: API Endpoint (Recommended)

With the services running (`docker compose up`):

```bash
# Start ingestion (runs in background)
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{}'

# Check status
curl http://localhost:8000/api/ingest/status
```

**Custom sitemap URL:**
```bash
curl -X POST http://localhost:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"sitemap_url": "https://satusatu.com/sitemap.xml", "max_concurrent": 10}'
```

### Option B: CLI Script

```bash
# From Docker
docker compose exec backend python -m app.ingestion.pipeline

# From local virtualenv
cd backend
python -m app.ingestion.pipeline
```

## Verifying Data in ChromaDB

### Check collection exists

```bash
curl http://localhost:8001/api/v1/collections
```

### Count documents

```bash
curl http://localhost:8001/api/v1/collections/satusatu_knowledge/count
```

### Query with text

```bash
curl -X POST http://localhost:8001/api/v1/collections/satusatu_knowledge/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_texts": ["things to do in Bali"],
    "n_results": 3
  }'
```

## Page Type Classification

URLs are auto-classified by path patterns:

| Type | Path patterns |
|:-----|:-------------|
| `attraction` | `/attraction`, `/place`, `/destination` |
| `itinerary` | `/itinerary`, `/tour`, `/package`, `/trip` |
| `ticket` | `/ticket`, `/booking`, `/buy` |
| `blog` | `/blog`, `/article`, `/news` |
| `faq` | `/faq`, `/help`, `/support` |
| `general` | Everything else |

## Configuration

All settings are in `.env`:

| Variable | Default | Description |
|:---------|:--------|:------------|
| `SITEMAP_URL` | `https://satusatu.com/sitemap.xml` | Target sitemap |
| `CHROMA_COLLECTION_NAME` | `satusatu_knowledge` | ChromaDB collection name |
| `CHROMA_HOST` | `chromadb` | ChromaDB host |
| `CHROMA_PORT` | `8000` | ChromaDB internal port |

## Troubleshooting

| Issue | Fix |
|:------|:----|
| `ConnectionError` to ChromaDB | Ensure `docker compose up chromadb` is running |
| Sitemap returns 403 | Check `User-Agent` in `pipeline.py` |
| Too many requests / rate limiting | Lower `max_concurrent` (default: 5) |
| Empty collection after ingestion | Check logs for "too little content" warnings |
