"""TWHIN-BERT embedding sidecar service.

Single FastAPI process per pod that loads Twitter/twhin-bert-base
once at startup and serves cosine-rankable 768-dim embeddings to
the simulation subprocesses over HTTP.

Endpoints:
    GET  /healthz   — liveness/readiness probe (returns 200 once
                      the model is loaded; 503 while loading)
    POST /embed     — body {"texts": [...]}, returns
                      {"embeddings": [[768 floats]...]}

Why a separate service:
    Each sim subprocess used to call get_twhin_bert() locally,
    loading ~1.5 GB into its own RSS. With N concurrent sims that
    multiplied linearly and OOMKilled the pod. Pulling the model
    into a sidecar makes it pod-scoped — load cost is paid once,
    every sim is just an HTTP client.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import List, Optional, Tuple

import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("twhin_sidecar")
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(message)s",
)


# ─────────────────────────────────────────────────────────────────
# Model singleton
# ─────────────────────────────────────────────────────────────────

_MODEL: Optional["object"] = None
_TOKENIZER: Optional["object"] = None
_DEVICE: Optional["object"] = None
_READY: bool = False
_MODEL_NAME: str = os.environ.get("TWHIN_MODEL", "Twitter/twhin-bert-base")
_MAX_SEQ_LENGTH: int = int(os.environ.get("TWHIN_MAX_SEQ", "512"))


def _load_model() -> Tuple[object, object, object]:
    """Load TWHIN-BERT into memory. Called exactly once at app startup.

    Returns (model, tokenizer, device). The model is .eval()-ed
    because we never train here.
    """
    import torch
    from transformers import AutoModel, AutoTokenizer

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Loading TWHIN-BERT model=%s on device=%s", _MODEL_NAME, device)
    tokenizer = AutoTokenizer.from_pretrained(
        _MODEL_NAME, model_max_length=_MAX_SEQ_LENGTH
    )
    model = AutoModel.from_pretrained(_MODEL_NAME).to(device).eval()
    logger.info("TWHIN-BERT ready (model_max_length=%d)", _MAX_SEQ_LENGTH)
    return model, tokenizer, device


def _embed(texts: List[str]) -> np.ndarray:
    """Embed a batch of texts. Returns (N, 768) float32 numpy array.

    Uses the model's pooler_output, which is what the original
    cached recommender used (see engine/scripts/twhin_rec.py).
    """
    import torch

    if _MODEL is None or _TOKENIZER is None:
        raise RuntimeError("model not loaded yet")

    with torch.no_grad():
        inputs = _TOKENIZER(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )
        inputs = {k: v.to(_DEVICE) for k, v in inputs.items()}
        outputs = _MODEL(**inputs)
    return outputs.pooler_output.cpu().numpy()


# ─────────────────────────────────────────────────────────────────
# FastAPI app + lifecycle
# ─────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model at startup, mark ready when done."""
    global _MODEL, _TOKENIZER, _DEVICE, _READY
    _MODEL, _TOKENIZER, _DEVICE = _load_model()
    _READY = True
    yield
    # No teardown — model is freed when the process exits.


app = FastAPI(
    title="TWHIN-BERT Sidecar",
    description="Pod-scoped Twitter/twhin-bert-base embedding service.",
    version="0.1.0",
    lifespan=lifespan,
)


class EmbedRequest(BaseModel):
    texts: List[str] = Field(
        ..., min_length=1, max_length=512,
        description="Batch of strings to embed. Empty strings allowed (substituted with 'user').",
    )


class EmbedResponse(BaseModel):
    embeddings: List[List[float]]
    dim: int
    count: int


@app.get("/healthz")
async def healthz():
    if not _READY:
        raise HTTPException(status_code=503, detail="model loading")
    return {"status": "ok", "model": _MODEL_NAME, "ready": True}


@app.post("/embed", response_model=EmbedResponse)
async def embed(req: EmbedRequest) -> EmbedResponse:
    if not _READY:
        raise HTTPException(status_code=503, detail="model still loading")
    # Substitute empty strings with a placeholder so the tokenizer
    # never sees zero-length input (matches old twhin_rec.py behavior
    # where empty bios got "user" as a default).
    texts = [t if t and t.strip() else "user" for t in req.texts]
    try:
        vectors = _embed(texts)
    except Exception as exc:
        logger.exception("embed failed")
        raise HTTPException(status_code=500, detail=f"embed failed: {exc}")
    return EmbedResponse(
        embeddings=vectors.tolist(),
        dim=int(vectors.shape[1]),
        count=int(vectors.shape[0]),
    )
