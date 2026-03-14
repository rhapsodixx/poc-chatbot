"""Ingestion pipeline — scrapes sitemap, chunks content, and upserts to ChromaDB.

Implemented in Phase 2.
"""


async def run_ingestion():
    """Execute the full ingestion pipeline.

    Steps (Phase 2):
      1. Fetch and parse sitemap.xml
      2. Crawl each URL and extract clean text
      3. Semantically chunk the content
      4. Tag metadata (url, type, location)
      5. Embed and upsert into ChromaDB
    """
    raise NotImplementedError("Ingestion pipeline will be implemented in Phase 2.")
