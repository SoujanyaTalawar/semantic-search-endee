"""
Embedder — wraps sentence-transformers to produce dense vectors.
Uses all-MiniLM-L6-v2 (384-dim) by default; fully local, no API key needed.
"""

import os
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class Embedder:
    def __init__(self):
        model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.dimension}")

    def encode(self, texts: list[str]) -> np.ndarray:
        """
        Encode a list of strings into L2-normalised float32 vectors.
        Returns shape (N, dimension).
        """
        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=False,
            batch_size=64,
        )
        return vectors.astype(np.float32)
