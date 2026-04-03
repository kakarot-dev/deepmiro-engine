# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 kakarot-dev
# GraphStorage interface originally from MiroShark (https://github.com/aaronjmars/MiroShark)

"""
MiroFish SurrealDB Adapter

Self-contained graph storage layer backed by SurrealDB 3.0.
Provides: graph CRUD, NER/RE text ingestion, hybrid search (vector + BM25),
graph reasoning queries, and Agent Virtual Memory (AVM).

Replaces the Neo4j adapter with a single-binary database that combines
graph, vector, and document storage.

Supported LLM/embedding providers (OpenAI-compatible):
  - Fireworks AI (default)
  - OpenRouter
  - OpenAI
  - Ollama (local)

Environment variables:
  SURREAL_URL, SURREAL_NAMESPACE, SURREAL_DATABASE,
  SURREAL_USER, SURREAL_PASSWORD                    -- SurrealDB connection
  LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME        -- LLM for NER extraction
  EMBEDDING_PROVIDER, EMBEDDING_MODEL,
  EMBEDDING_BASE_URL, EMBEDDING_API_KEY,
  EMBEDDING_DIMENSIONS                              -- Embedding configuration
"""

from .config import Config
from .graph_storage import GraphStorage
from .surrealdb_storage import SurrealDBStorage
from .embedding_service import EmbeddingService, EmbeddingError
from .search_service import SurrealSearchService
from .ner_extractor import NERExtractor
from .llm_client import LLMClient, create_llm_client
from .avm import AgentVirtualMemory
from .zep_shim import ZepSurrealShim

__all__ = [
    "Config",
    "GraphStorage",
    "SurrealDBStorage",
    "EmbeddingService",
    "EmbeddingError",
    "SurrealSearchService",
    "NERExtractor",
    "LLMClient",
    "create_llm_client",
    "AgentVirtualMemory",
    "ZepSurrealShim",
]
