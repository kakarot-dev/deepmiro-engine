"""
Pluggable graph storage layer.

Replaces direct Zep Cloud dependency with a backend-agnostic interface.
Use ``get_storage()`` from ``factory.py`` to obtain the configured backend.
"""

from .base import GraphStorage
from .factory import get_storage
from .avm import AgentVirtualMemory

__all__ = [
    "GraphStorage",
    "get_storage",
    "AgentVirtualMemory",
]
