"""
VectorStore — thin wrapper around the Endee Python SDK.
Handles index lifecycle, upsert, and nearest-neighbour queries.
"""

import os
import logging
from typing import Any

from endee import Endee
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

ENDEE_BASE_URL  = os.getenv("ENDEE_BASE_URL", "http://localhost:8080/api/v1")
ENDEE_AUTH_TOKEN = os.getenv("ENDEE_AUTH_TOKEN", "")
INDEX_NAME      = os.getenv("INDEX_NAME", "semantic_search_index")
VECTOR_DIM      = int(os.getenv("VECTOR_DIMENSION", 384))


class VectorStore:
    def __init__(self):
        token = ENDEE_AUTH_TOKEN or None
        self.client = Endee(token) if token else Endee()
        self.client.set_base_url(ENDEE_BASE_URL)
        self._index = None
        logger.info(f"Connected to Endee at {ENDEE_BASE_URL}")

    # ── Index management ────────────────────────────────────────────────────────
    def ensure_index(self):
        """Create the index if it doesn't already exist."""
        try:
            self.client.create_index(
                name=INDEX_NAME,
                dimension=VECTOR_DIM,
                space_type="cosine",
            )
            logger.info(f"Created index '{INDEX_NAME}'")
        except Exception as e:
            logger.info(f"Index '{INDEX_NAME}' already exists — reusing. ({e})")
        self._index = self.client.get_index(name=INDEX_NAME)

    def delete_index(self):
        """Drop and remove the index (for reset)."""
        try:
            self.client.delete_index(name=INDEX_NAME)
            logger.info(f"Index '{INDEX_NAME}' deleted.")
        except Exception as e:
            logger.warning(f"Could not delete index: {e}")
        self._index = None

    def index_info(self) -> dict:
        """Return basic stats about the current index."""
        try:
            info = self.client.describe_index(name=INDEX_NAME)
            return {
                "vector_count": getattr(info, "vector_count", "n/a"),
                "space_type": getattr(info, "space_type", "cosine"),
                "precision": getattr(info, "precision", "INT8"),
            }
        except Exception:
            return {"vector_count": "n/a", "space_type": "cosine", "precision": "INT8"}

    # ── Data operations ─────────────────────────────────────────────────────────
    def upsert(self, items: list[dict[str, Any]]):
        """
        items = [{"id": str, "vector": list[float], "meta": dict}, ...]
        """
        if self._index is None:
            self.ensure_index()
        self._index.upsert(items)
        logger.info(f"Upserted {len(items)} vectors into '{INDEX_NAME}'")

    def query(self, vector: list[float], top_k: int = 5) -> list[dict]:
        """
        Returns list of dicts: {"id", "similarity", "meta"}
        """
        if self._index is None:
            self.ensure_index()

        results = self._index.query(vector=vector, top_k=top_k)
        output = []

        for r in results:
            # Handle both object and dict style responses
            if isinstance(r, dict):
                output.append({
                    "id": r.get("id", ""),
                    "similarity": r.get("similarity", r.get("score", 0.0)),
                    "meta": r.get("meta", r.get("metadata", {})),
                })
            else:
                output.append({
                    "id": getattr(r, "id", ""),
                    "similarity": getattr(r, "similarity", getattr(r, "score", 0.0)),
                    "meta": getattr(r, "meta", getattr(r, "metadata", {})) or {},
                })

        return output