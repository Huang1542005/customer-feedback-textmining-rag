"""Embedding wrappers for Customer Feedback RAG.

Supports:
1. Local HuggingFace sentence-transformers (default: `all-MiniLM-L6-v2`, runs offline).
2. Google Gemini Embeddings (`text-embedding-004`) via `google.genai`.
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Sequence

from dotenv import load_dotenv
import numpy as np

load_dotenv()

logger = logging.getLogger(__name__)


class BaseEmbedder(ABC):
    """Abstract interface for text embedding providers."""

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate embeddings for a list of document texts."""
        pass

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        """Generate embedding for a single query."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimensionality."""
        pass


class SentenceTransformerEmbedder(BaseEmbedder):
    """Local offline embedder using SentenceTransformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", device: str = "cpu"):
        from sentence_transformers import SentenceTransformer

        logger.info("Initializing SentenceTransformer: %s (device=%s)", model_name, device)
        self.model_name = model_name
        self.model = SentenceTransformer(model_name, device=device)
        self._dim = self.model.get_sentence_embedding_dimension() or 384

    def embed_documents(self, texts: Sequence[str], batch_size: int = 64) -> list[list[float]]:
        if not texts:
            return []
        embeddings = self.model.encode(
            list(texts),
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return [vec.tolist() for vec in embeddings]

    def embed_query(self, text: str) -> list[float]:
        vec = self.model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    @property
    def dimension(self) -> int:
        return self._dim


class GeminiEmbedder(BaseEmbedder):
    """Google Gemini API embedder using text-embedding-004."""

    def __init__(self, api_key: str | None = None, model_name: str = "text-embedding-004"):
        from google import genai

        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY environment variable is required for GeminiEmbedder.")

        self.client = genai.Client(api_key=key)
        self.model_name = model_name
        self._dim = 768

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = []
        for text in texts:
            res = self.client.models.embed_content(
                model=self.model_name,
                contents=text,
            )
            vectors.append(res.embedding.values)
        return vectors

    def embed_query(self, text: str) -> list[float]:
        res = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
        )
        return res.embedding.values

    @property
    def dimension(self) -> int:
        return self._dim


def get_embedder(
    provider: str = "local",
    model_name: str = "all-MiniLM-L6-v2",
) -> BaseEmbedder:
    """Factory function to acquire an Embedder instance."""
    if provider.lower() in ("gemini", "google"):
        return GeminiEmbedder(model_name="text-embedding-004")
    return SentenceTransformerEmbedder(model_name=model_name)

