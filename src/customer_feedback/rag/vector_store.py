"""ChromaDB Vector Store management for reviews and policy documents."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Sequence

import chromadb
from chromadb.config import Settings

from customer_feedback.rag.document_loader import Document
from customer_feedback.rag.embeddings import BaseEmbedder

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DB_PATH = ROOT / "data/vector_store"


class ChromaVectorStore:
    """Persistent Vector Store backed by ChromaDB."""

    def __init__(
        self,
        persist_dir: str | Path = DEFAULT_DB_PATH,
        embedder: BaseEmbedder | None = None,
    ):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder

        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )

    def get_or_create_collection(self, collection_name: str = "feedback_reviews"):
        """Get or initialize a named collection."""
        return self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_documents(
        self,
        documents: Sequence[Document],
        collection_name: str = "feedback_reviews",
        batch_size: int = 100,
    ) -> int:
        """Embed and insert documents into the specified collection in batches."""
        if not documents:
            return 0

        if self.embedder is None:
            raise ValueError("An embedder must be provided to add documents to the vector store.")

        collection = self.get_or_create_collection(collection_name)
        total_added = 0

        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            ids = [doc.doc_id for doc in batch]
            texts = [doc.text for doc in batch]
            metas = []

            for doc in batch:
                # Sanitize metadata for Chroma (strings, ints, floats, bools only)
                clean_meta: dict[str, Any] = {}
                for k, v in doc.metadata.items():
                    if v is not None and not (isinstance(v, float) and v != v):
                        if isinstance(v, (str, int, float, bool)):
                            clean_meta[k] = v
                        else:
                            clean_meta[k] = str(v)
                metas.append(clean_meta)

            vectors = self.embedder.embed_documents(texts)

            collection.upsert(
                ids=ids,
                embeddings=vectors,
                metadatas=metas,
                documents=texts,
            )
            total_added += len(batch)
            logger.debug("Indexed batch %d/%d into %s", total_added, len(documents), collection_name)

        logger.info("Successfully added %d documents to collection '%s'", total_added, collection_name)
        return total_added

    def query(
        self,
        query_text: str | None = None,
        query_vector: list[float] | None = None,
        collection_name: str = "feedback_reviews",
        n_results: int = 5,
        where: dict[str, Any] | None = None,
    ) -> list[Document]:
        """Query similar documents using dense vector similarity."""
        collection = self.get_or_create_collection(collection_name)

        if collection.count() == 0:
            return []

        if query_vector is None:
            if query_text is None:
                raise ValueError("Must provide either query_text or query_vector.")
            if self.embedder is None:
                raise ValueError("Embedder required to encode query_text.")
            query_vector = self.embedder.embed_query(query_text)

        kwargs: dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": min(n_results, collection.count()),
        }
        if where:
            kwargs["where"] = where

        results = collection.query(**kwargs)

        docs: list[Document] = []
        ids = results.get("ids", [[]])[0]
        texts = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for idx in range(len(ids)):
            meta = dict(metadatas[idx]) if metadatas and idx < len(metadatas) else {}
            if distances and idx < len(distances):
                # Cosine distance to similarity: 1 - distance
                meta["similarity_score"] = round(1.0 - float(distances[idx]), 4)

            docs.append(
                Document(
                    doc_id=ids[idx],
                    text=texts[idx] if texts else "",
                    metadata=meta,
                )
            )

        return docs

    def count(self, collection_name: str) -> int:
        """Return the number of items in a collection."""
        try:
            return self.client.get_collection(collection_name).count()
        except Exception:
            return 0

