"""TWHIN-BERT sidecar — pod-scoped embedding service.

Loads Twitter/twhin-bert-base exactly once per pod and exposes it
over an internal HTTP endpoint. Every sim subprocess (and the backend
itself, if it ever needs an embed) talks to this service instead of
loading its own copy of the model.

Memory math:
    before: 1.5 GB × N concurrent sim subprocesses
    after:  1.5 GB × 1 sidecar
"""
