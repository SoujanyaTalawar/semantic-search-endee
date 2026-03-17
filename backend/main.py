"""
Semantic Search Engine - FastAPI Backend
Uses Endee Vector DB + sentence-transformers for local embeddings
"""

import os
import time
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from .embedder import Embedder
from .vector_store import VectorStore

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Globals ────────────────────────────────────────────────────────────────────
embedder: Optional[Embedder] = None
vector_store: Optional[VectorStore] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global embedder, vector_store
    logger.info("🚀 Starting up — loading embedder & connecting to Endee...")
    embedder = Embedder()
    vector_store = VectorStore()
    vector_store.ensure_index()
    logger.info("✅ Ready.")
    yield
    logger.info("🛑 Shutting down.")


app = FastAPI(
    title="Semantic Search Engine",
    description="AI-powered semantic search using Endee Vector DB",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ──────────────────────────────────────────────────
class Document(BaseModel):
    id: str
    title: str
    content: str
    category: Optional[str] = "general"
    url: Optional[str] = None


class BulkIngestRequest(BaseModel):
    documents: list[Document]


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    category: Optional[str] = None


class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    category: str
    url: Optional[str]
    similarity: float
    snippet: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_found: int
    search_time_ms: float


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "endee_url": os.getenv("ENDEE_BASE_URL")}


@app.get("/stats")
def stats():
    info = vector_store.index_info()
    return {
        "index_name": os.getenv("INDEX_NAME"),
        "vector_dimension": int(os.getenv("VECTOR_DIMENSION", 384)),
        "embedding_model": os.getenv("EMBEDDING_MODEL"),
        **info,
    }


@app.post("/ingest", summary="Add documents to the search index")
def ingest(request: BulkIngestRequest):
    docs = request.documents
    if not docs:
        raise HTTPException(status_code=400, detail="No documents provided")

    texts = [f"{d.title}. {d.content}" for d in docs]
    vectors = embedder.encode(texts)

    items = []
    for doc, vec in zip(docs, vectors):
        items.append({
            "id": doc.id,
            "vector": vec.tolist(),
            "meta": {
                "title": doc.title,
                "content": doc.content,
                "category": doc.category or "general",
                "url": doc.url or "",
            },
        })

    vector_store.upsert(items)
    return {"message": f"Indexed {len(items)} documents successfully", "count": len(items)}


@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    t0 = time.perf_counter()
    query_vec = embedder.encode([request.query])[0]
    raw = vector_store.query(query_vec.tolist(), top_k=request.top_k)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    results = []
    for r in raw:
        meta = r.get("meta", {})
        category = meta.get("category", "general")
        # Optional category filter
        if request.category and category != request.category:
            continue
        content = meta.get("content", "")
        snippet = _make_snippet(content, request.query)
        results.append(SearchResult(
            id=r["id"],
            title=meta.get("title", r["id"]),
            content=content,
            category=category,
            url=meta.get("url") or None,
            similarity=round(r.get("similarity", 0.0), 4),
            snippet=snippet,
        ))

    return SearchResponse(
        query=request.query,
        results=results,
        total_found=len(results),
        search_time_ms=round(elapsed_ms, 2),
    )


@app.get("/search", response_model=SearchResponse, summary="GET version of search")
def search_get(
    q: str = Query(..., description="Search query"),
    top_k: int = Query(5, ge=1, le=20),
    category: Optional[str] = Query(None),
):
    return search(SearchRequest(query=q, top_k=top_k, category=category))


@app.delete("/index", summary="Clear all documents from the index")
def clear_index():
    vector_store.delete_index()
    vector_store.ensure_index()
    return {"message": "Index cleared and recreated"}


# ── Helpers ────────────────────────────────────────────────────────────────────
def _make_snippet(content: str, query: str, max_len: int = 200) -> str:
    """Return a short snippet from content, centred around query terms."""
    if not content:
        return ""
    lower = content.lower()
    words = query.lower().split()
    best_pos = 0
    for w in words:
        pos = lower.find(w)
        if pos != -1:
            best_pos = max(0, pos - 60)
            break
    snippet = content[best_pos : best_pos + max_len]
    if best_pos > 0:
        snippet = "…" + snippet
    if best_pos + max_len < len(content):
        snippet += "…"
    return snippet
