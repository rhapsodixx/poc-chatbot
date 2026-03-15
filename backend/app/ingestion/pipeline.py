"""Ingestion pipeline — scrapes sitemap.xml, cleans HTML, chunks text, upserts to ChromaDB.

Usage:
    python -m app.ingestion.pipeline

This module can be run as a standalone script or triggered via the /api/ingest endpoint.
"""

import asyncio
import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import get_settings
from app.services.vectorstore import get_chroma_client, get_collection, delete_by_url, get_all_stored_metadata

logger = logging.getLogger(__name__)


# ── Data Models ──────────────────────────────────────────────


@dataclass
class PageContent:
    """Represents cleaned content extracted from a single page."""

    url: str
    title: str
    text: str
    meta_description: str = ""
    page_type: str = "general"
    image_url: str = ""
    lastmod: str = ""
    content_hash: str = ""


@dataclass
class TextChunk:
    """A semantically meaningful chunk of text with metadata."""

    text: str
    metadata: dict = field(default_factory=dict)
    chunk_id: str = ""

    def __post_init__(self):
        if not self.chunk_id:
            self.chunk_id = hashlib.md5(
                f"{self.metadata.get('url', '')}-{self.text[:50]}".encode()
            ).hexdigest()


# ── Step 1: Sitemap Parser ───────────────────────────────────


async def fetch_sitemap(sitemap_url: str) -> dict[str, str]:
    """Fetch and parse a sitemap.xml to extract all page URLs and their lastmod.

    Supports nested sitemaps (sitemap index files).

    Args:
        sitemap_url: URL to the sitemap.xml file.

    Returns:
        Dict mapping discovered page URLs to their lastmod timestamps.
    """
    urls: dict[str, str] = {}
    namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        response = await client.get(sitemap_url)
        response.raise_for_status()

    root = ET.fromstring(response.text)

    # Check if this is a sitemap index (contains other sitemaps)
    sitemap_refs = root.findall(".//sm:sitemap/sm:loc", namespaces)
    if sitemap_refs:
        logger.info(f"Found sitemap index with {len(sitemap_refs)} sub-sitemaps")
        for ref in sitemap_refs:
            ref_text = ref.text
            if ref_text is not None:
                sub_urls = await fetch_sitemap(ref_text.strip())
                urls.update(sub_urls)
        return urls

    # Regular sitemap — extract <loc> and <lastmod> entries
    url_elements = root.findall(".//sm:url", namespaces)
    if not url_elements:
        # Try without namespace (some sitemaps don't use it)
        url_elements = root.findall(".//url")

    for url_el in url_elements:
        loc = url_el.find(".//sm:loc", namespaces)
        if loc is None:
            loc = url_el.find(".//loc")
            
        if loc is not None and loc.text:
            url = loc.text.strip()
            
            lastmod_el = url_el.find(".//sm:lastmod", namespaces)
            if lastmod_el is None:
                lastmod_el = url_el.find(".//lastmod")
                
            lastmod = lastmod_el.text.strip() if lastmod_el is not None and lastmod_el.text else ""
            urls[url] = lastmod

    logger.info(f"Parsed {len(urls)} URLs from {sitemap_url}")
    return urls


# ── Step 2: Page Fetcher & HTML Cleaner ──────────────────────


from urllib.parse import urljoin

async def fetch_and_clean_page(url: str, client: httpx.AsyncClient, lastmod: str = "") -> PageContent | None:
    """Fetch a page and extract clean text content.

    Strips headers, footers, navbars, scripts, and other non-content HTML.

    Args:
        url: The page URL to fetch.
        client: Shared httpx client for connection reuse.
        lastmod: The last modification date.

    Returns:
        PageContent with cleaned text, or None if fetch fails.
    """
    try:
        response = await client.get(url)
        response.raise_for_status()
        html_text = response.text
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP {e.response.status_code} for {url}, skipping")
        return None
    except httpx.RequestError as e:
        logger.warning(f"Request error for {url}: {e}, skipping")
        return None

    # Offload CPU-bound HTML parsing to a background thread
    return await asyncio.to_thread(_parse_html_and_extract, html_text, url, lastmod)  # type: ignore


def _parse_html_and_extract(html_text: str, url: str, lastmod: str) -> PageContent | None:
    soup = BeautifulSoup(html_text, "lxml")

    # Extract main image before decomposing tags
    image_url = ""
    meta_img = soup.find("meta", property="og:image")
    if meta_img and meta_img.get("content"):
        image_url = meta_img["content"]
        if image_url.startswith("/"):
            image_url = urljoin(url, image_url)
    else:
        # Fallback to first large image
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            image_url = urljoin(url, img_tag["src"])

    # Remove non-content elements
    for tag in soup.find_all(
        ["script", "style", "nav", "header", "footer", "aside", "noscript", "iframe"]
    ):
        tag.decompose()

    # Extract title
    title = ""
    title_tag = soup.find("title")
    if title_tag:
        title = title_tag.get_text(strip=True)

    # Extract meta description
    meta_desc = ""
    meta_tag = soup.find("meta", attrs={"name": "description"})
    if meta_tag and meta_tag.get("content"):
        meta_desc = meta_tag["content"]

    # Extract main content (prefer <main> or <article>, fallback to <body>)
    main_content = soup.find("main") or soup.find("article") or soup.find("body")
    if not main_content:
        logger.warning(f"No body content found for {url}, skipping")
        return None

    # Clean whitespace
    text = main_content.get_text(separator="\n", strip=True)
    text = re.sub(r"\n{3,}", "\n\n", text)  # Collapse excessive newlines
    text = re.sub(r" {2,}", " ", text)  # Collapse excessive spaces

    cleaned_text = text.strip()
    if len(cleaned_text) < 50:
        logger.info(f"Skipping {url} — too little content ({len(cleaned_text)} chars)")
        return None

    # Infer page type from URL path
    page_type = _infer_page_type(url)
    
    content_hash = hashlib.md5(cleaned_text.encode()).hexdigest()

    return PageContent(
        url=url,
        title=title,
        text=cleaned_text,
        meta_description=meta_desc,
        page_type=page_type,
        image_url=image_url,
        lastmod=lastmod,
        content_hash=content_hash,
    )


def _infer_page_type(url: str) -> str:
    """Heuristic to classify page type from its URL path."""
    path = urlparse(url).path.lower()

    type_patterns = {
        "attraction": ["/attraction", "/place", "/destination", "/thing"],
        "itinerary": ["/itinerary", "/tour", "/package", "/trip"],
        "ticket": ["/ticket", "/booking", "/buy"],
        "blog": ["/blog", "/article", "/news", "/story"],
        "faq": ["/faq", "/help", "/support"],
        "about": ["/about", "/contact", "/team"],
    }

    for page_type, patterns in type_patterns.items():
        if any(p in path for p in patterns):
            return page_type

    return "general"


# ── Step 3: Semantic Chunker ─────────────────────────────────


def chunk_text(
    page: PageContent,
    max_chunk_size: int = 256,
    overlap: int = 32,
) -> list[TextChunk]:
    """Split page content into semantically meaningful chunks.

    Strategy:
      1. First try to split by markdown-style headings or double newlines
      2. If a section is too large, split by sentences
      3. Apply overlap between chunks for context continuity

    Args:
        page: The cleaned page content.
        max_chunk_size: Maximum number of words per chunk.
        overlap: Number of words to overlap between chunks.

    Returns:
        List of TextChunks with metadata.
    """
    # Split by natural boundaries (double newlines, headings)
    sections = re.split(r"\n{2,}|(?=^#{1,3}\s)", page.text, flags=re.MULTILINE)
    sections = [s.strip() for s in sections if s.strip()]

    chunks: list[TextChunk] = []
    current_section = ""

    for section in sections:
        words_in_section = len(section.split())

        # If adding this section exceeds max, flush current and start new
        if len(current_section.split()) + words_in_section > max_chunk_size:
            if current_section.strip():
                chunks.append(
                    TextChunk(
                        text=current_section.strip(),
                        metadata={
                            "url": page.url,
                            "title": page.title,
                            "page_type": page.page_type,
                            "meta_description": page.meta_description,
                            "image_url": page.image_url,
                            "lastmod": page.lastmod,
                            "content_hash": page.content_hash,
                        },
                    )
                )
            # If section itself is too big, split by sentences
            if words_in_section > max_chunk_size:
                sentence_chunks = _split_by_sentences(section, max_chunk_size, overlap)
                for sc in sentence_chunks:
                    chunks.append(
                        TextChunk(
                            text=sc,
                            metadata={
                                "url": page.url,
                                "title": page.title,
                                "page_type": page.page_type,
                                "meta_description": page.meta_description,
                                "image_url": page.image_url,
                                "lastmod": page.lastmod,
                                "content_hash": page.content_hash,
                            },
                        )
                    )
                current_section = ""
            else:
                current_section = section
        else:
            current_section = f"{current_section}\n\n{section}" if current_section else section

    # Flush remaining
    if current_section.strip():
        chunks.append(
            TextChunk(
                text=current_section.strip(),
                metadata={
                    "url": page.url,
                    "title": page.title,
                    "page_type": page.page_type,
                    "meta_description": page.meta_description,
                    "image_url": page.image_url,
                    "lastmod": page.lastmod,
                    "content_hash": page.content_hash,
                },
            )
        )

    logger.info(f"Chunked {page.url} → {len(chunks)} chunks")
    return chunks


def _split_by_sentences(text: str, max_words: int, overlap: int) -> list[str]:
    """Split text by sentence boundaries with word-count limits."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current: list[str] = []
    word_count = 0

    for sentence in sentences:
        s_words = len(sentence.split())
        if word_count + s_words > max_words and current:
            chunks.append(" ".join(current))
            # Keep some overlap
            overlap_sentences = []
            overlap_count = 0
            for s in reversed(current):
                overlap_count += len(s.split())
                if overlap_count > overlap:
                    break
                overlap_sentences.insert(0, s)
            current = overlap_sentences
            word_count = sum(len(s.split()) for s in current)

        current.append(sentence)
        word_count += s_words

    if current:
        chunks.append(" ".join(current))

    return chunks


# ── Step 4: ChromaDB Upsert ──────────────────────────────────


import time

def upsert_chunks(chunks: list[TextChunk]) -> int:
    """Upsert text chunks into ChromaDB collection.

    ChromaDB will handle embedding generation via its default model.

    Args:
        chunks: List of TextChunks to upsert.

    Returns:
        Number of chunks upserted.
    """
    if not chunks:
        return 0

    client = get_chroma_client()
    collection = get_collection(client)

    # Batch upsert (ChromaDB supports batch operations)
    batch_size = 50
    total_upserted = 0

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        collection.upsert(
            ids=[c.chunk_id for c in batch],
            documents=[c.text for c in batch],
            metadatas=[c.metadata for c in batch],
        )
        total_upserted += len(batch)
        logger.info(f"Upserted batch {i // batch_size + 1} ({len(batch)} chunks)")
        time.sleep(0.01)  # Yield slightly if running synchronously, though inside to_thread this just slows the thread

    logger.info(f"Total upserted component: {total_upserted} chunks")
    return total_upserted


# ── Orchestrator ─────────────────────────────────────────────


async def run_ingestion(
    sitemap_url: str | None = None,
    max_concurrent: int = 5,
) -> dict:
    """Execute the full ingestion pipeline.

    Steps:
      1. Fetch and parse sitemap.xml
      2. Crawl each URL and extract clean text
      3. Semantically chunk the content
      4. Upsert into ChromaDB

    Args:
        sitemap_url: Override the default sitemap URL.
        max_concurrent: Max concurrent page fetches.

    Returns:
        Summary dict with stats.
    """
    settings = get_settings()
    sitemap = sitemap_url or settings.sitemap_url

    logger.info(f"=== Starting ingestion from {sitemap} ===")

    # Step 1: Discover URLs
    url_manifest = await fetch_sitemap(sitemap)
    logger.info(f"Discovered {len(url_manifest)} URLs")
    
    # Get existing URLs sequentially
    stored_metadata = get_all_stored_metadata()
    
    # We will process all URLs but skip embeddings if the content hash matches
    urls_to_process = []
    for url, current_lastmod in url_manifest.items():
        urls_to_process.append((url, current_lastmod, stored_metadata.get(url, {}).get("content_hash")))

    logger.info(f"Queued {len(urls_to_process)} URLs for content-hash diffing.")

    # Step 2 & 3: Fetch, clean, and chunk pages (with concurrency limit)
    semaphore = asyncio.Semaphore(max_concurrent)

    total_urls = len(urls_to_process)
    progress = {"count": 0, "pages_skipped": 0, "pages_processed": 0, "total_chunks": 0, "chunks_upserted": 0}

    async def process_url(url: str, lastmod: str, stored_hash: str | None, client: httpx.AsyncClient):
        async with semaphore:
            try:
                page = await fetch_and_clean_page(url, client, lastmod)
                if page:
                    if stored_hash and page.content_hash == stored_hash:
                        logger.debug(f"Skipping {url} — content hash unchanged")
                        progress["pages_skipped"] += 1
                        return url, []

                    # Offload regex chunking to background thread
                    chunks = await asyncio.to_thread(chunk_text, page)  # type: ignore
                    
                    if chunks:
                        progress["pages_processed"] += 1
                        progress["total_chunks"] += len(chunks)
                        
                    return url, chunks
                return url, []
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                return e
            finally:
                progress["count"] += 1
                left = total_urls - progress["count"]
                logger.info(f"[{progress['count']}/{total_urls}] Processed {url} — {left} URLs left to fetch")

    async with httpx.AsyncClient(
        follow_redirects=True, timeout=30.0, headers={"User-Agent": "satusatu-ingestion/1.0"}
    ) as client:
        tasks = [process_url(url, lastmod, stored_hash, client) for url, lastmod, stored_hash in urls_to_process]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    pages_failed = 0
    all_chunks = []
    urls_to_update = set()
    
    for r in results:
        if isinstance(r, Exception):
            pages_failed += 1
            logger.error(f"Page processing failed: {r}")
        else:
            url, chunks = r
            if chunks:
                all_chunks.extend(chunks)
                urls_to_update.add(url)
                
    if all_chunks:
        logger.info(f"Globally batch-updating {len(urls_to_update)} URLs with {len(all_chunks)} chunks total...")
        
        # 1. Delete old chunks for updated URLs
        for url in urls_to_update:
            delete_by_url(url)
            
        # 2. Globally upsert all new chunks
        upserted_count = upsert_chunks(all_chunks)
        progress["chunks_upserted"] = upserted_count

    # Step 5: Clean up stale URLs
    discovered_urls = set(url_manifest.keys())
    stale_urls = set(stored_metadata.keys()) - discovered_urls
    
    stale_deleted = 0
    if stale_urls:
        logger.info(f"Found {len(stale_urls)} stale URLs not in sitemap. Cleaning up...")
        for stale_url in stale_urls:
            # We can delete sequentially at the end
            delete_by_url(stale_url)
            stale_deleted += 1
        logger.info(f"Cleaned up {stale_deleted} stale URLs.")

    summary = {
        "sitemap_url": sitemap,
        "urls_discovered": len(url_manifest),
        "urls_skipped_unmodified": progress["pages_skipped"],
        "pages_processed": progress["pages_processed"],
        "pages_failed": pages_failed,
        "total_chunks": progress["total_chunks"],
        "chunks_upserted": progress["chunks_upserted"],
        "stale_urls_removed": stale_deleted,
    }

    logger.info(f"=== Ingestion complete: {summary} ===")
    return summary


# ── CLI Entry Point ──────────────────────────────────────────

if __name__ == "__main__":
    result = asyncio.run(run_ingestion())
    print("\n📊 Ingestion Summary:")
    for k, v in result.items():
        print(f"   {k}: {v}")
