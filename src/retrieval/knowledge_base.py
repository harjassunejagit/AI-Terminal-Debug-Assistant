"""
Retrieval Layer — ChromaDB-backed local error knowledge base.
Stores past fixes and retrieves similar errors to augment AI prompts.
"""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Optional

DB_PATH = Path.home() / ".debugai" / "chromadb"


class ErrorKnowledgeBase:
    """
    Stores resolved errors in ChromaDB for semantic retrieval.
    Falls back gracefully if ChromaDB is not installed.
    """

    def __init__(self):
        self._client = None
        self._collection = None
        self._available = self._try_init()

    def _try_init(self) -> bool:
        try:
            import chromadb
            DB_PATH.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(DB_PATH))
            self._collection = self._client.get_or_create_collection(
                name="debug_errors",
                metadata={"hnsw:space": "cosine"},
            )
            return True
        except ImportError:
            return False
        except Exception:
            return False

    @property
    def available(self) -> bool:
        return self._available

    def add_resolution(
        self,
        error_text: str,
        error_type: str,
        language: str,
        fix: str,
        explanation: str,
    ):
        """Store a resolved error for future retrieval."""
        if not self._available:
            return

        doc_id = hashlib.md5(error_text.encode()).hexdigest()
        metadata = {
            "error_type": error_type,
            "language": language,
            "fix": fix,
        }
        self._collection.upsert(
            ids=[doc_id],
            documents=[error_text[:1000]],
            metadatas=[metadata],
        )

    def find_similar(self, error_text: str, n_results: int = 3) -> list[dict]:
        """Find similar past errors and their fixes."""
        if not self._available or self._collection.count() == 0:
            return []

        try:
            results = self._collection.query(
                query_texts=[error_text[:500]],
                n_results=min(n_results, self._collection.count()),
            )
            similar = []
            if results["documents"]:
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                ):
                    if dist < 0.5:  # Only return sufficiently similar results
                        similar.append({
                            "error_snippet": doc[:200],
                            "fix": meta.get("fix", ""),
                            "error_type": meta.get("error_type", ""),
                            "language": meta.get("language", ""),
                            "similarity": round(1 - dist, 2),
                        })
            return similar
        except Exception:
            return []

    def count(self) -> int:
        if not self._available:
            return 0
        try:
            return self._collection.count()
        except Exception:
            return 0

    def status(self) -> dict:
        return {
            "available": self._available,
            "entries": self.count(),
            "path": str(DB_PATH),
            "install_hint": "pip install chromadb" if not self._available else None,
        }
