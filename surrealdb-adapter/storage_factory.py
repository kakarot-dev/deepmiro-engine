# SPDX-License-Identifier: AGPL-3.0-only
# Copyright 2026 kakarot-dev
"""
Pluggable storage backend factory.

Select backend via GRAPH_BACKEND env var:
  - "surrealdb" (default) — SurrealDB 3.0
  - "neo4j" — Neo4j Community/Enterprise
  - "custom" — bring your own GraphStorage implementation

To add a custom backend:
  1. Subclass GraphStorage from graph_storage.py
  2. Set GRAPH_BACKEND=custom
  3. Set GRAPH_BACKEND_MODULE=your_module.YourStorageClass
"""

import os
import logging
import importlib

logger = logging.getLogger("mirofish.storage_factory")


def create_storage():
    """
    Create the appropriate storage backend based on GRAPH_BACKEND env var.
    Returns an instance implementing the GraphStorage interface.
    """
    backend = os.environ.get("GRAPH_BACKEND", "surrealdb").lower()

    if backend == "surrealdb":
        from surrealdb_adapter import SurrealDBStorage
        logger.info("Using SurrealDB storage backend")
        return SurrealDBStorage()

    elif backend == "neo4j":
        from neo4j_adapter.neo4j_storage import Neo4jStorage
        logger.info("Using Neo4j storage backend")
        return Neo4jStorage()

    elif backend == "custom":
        module_path = os.environ.get("GRAPH_BACKEND_MODULE", "")
        if not module_path:
            raise ValueError("GRAPH_BACKEND=custom requires GRAPH_BACKEND_MODULE=module.ClassName")
        module_name, class_name = module_path.rsplit(".", 1)
        mod = importlib.import_module(module_name)
        cls = getattr(mod, class_name)
        logger.info("Using custom storage backend: %s", module_path)
        return cls()

    else:
        raise ValueError(f"Unknown GRAPH_BACKEND: {backend}. Use 'surrealdb', 'neo4j', or 'custom'")
