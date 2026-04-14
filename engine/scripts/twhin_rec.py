"""Cached TWHIN-BERT recommendation system.

Embeds user bios once, new posts incrementally, computes cosine
similarity with numpy. Same quality as the original OASIS paper,
~15 ms per round instead of 200 s.

v0.10.0: model loading moved to a pod-scoped twhin-sidecar container.
This module no longer imports torch/transformers — it makes HTTP
calls to the sidecar at $TWHIN_URL (default http://localhost:7001).

Why: each sim subprocess used to load its own ~1.5 GB copy of TWHIN
locally. With multiple concurrent sims that multiplied linearly and
OOMKilled the pod. The sidecar loads the model exactly once and
serves embeddings to all sims over a same-pod localhost socket.
"""

import os
import time
from typing import List, Optional

import numpy as np

# ──────────────────────────────────────────────────────────────────
# HTTP client
# ──────────────────────────────────────────────────────────────────

_TWHIN_URL = os.environ.get("TWHIN_URL", "http://localhost:7001")
_HTTP_TIMEOUT = float(os.environ.get("TWHIN_HTTP_TIMEOUT", "60"))
_STARTUP_RETRY_SECONDS = float(os.environ.get("TWHIN_STARTUP_RETRY_SECONDS", "120"))


def _post_embed(texts: List[str], log_fn=None) -> Optional[np.ndarray]:
    """POST a batch of texts to the sidecar /embed endpoint.

    Returns an (N, dim) float32 numpy array, or None on failure.
    Single-shot — no retry. Caller decides what to do on None.
    """
    # urllib + json keeps the dependency footprint zero. The backend
    # image no longer carries `requests`, since `requests` was a
    # transitive dep of transformers which is now sidecar-only.
    import json
    import urllib.error
    import urllib.request

    payload = json.dumps({"texts": list(texts)}).encode("utf-8")
    req = urllib.request.Request(
        f"{_TWHIN_URL}/embed",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            body = resp.read()
        data = json.loads(body)
    except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError, TimeoutError) as exc:
        if log_fn:
            log_fn(f"TWHIN sidecar embed failed: {exc}")
        return None
    except Exception as exc:
        if log_fn:
            log_fn(f"TWHIN sidecar embed unexpected error: {exc}")
        return None

    embeddings = data.get("embeddings")
    if not isinstance(embeddings, list) or not embeddings:
        return None
    try:
        return np.asarray(embeddings, dtype=np.float32)
    except Exception as exc:
        if log_fn:
            log_fn(f"TWHIN sidecar returned malformed embeddings: {exc}")
        return None


def _wait_for_sidecar(log_fn=None) -> bool:
    """Block until the sidecar /healthz reports ready, or timeout.

    Called once at sim startup. The sidecar takes 5-15 s to load the
    model on cold pod start; if a sim subprocess starts during that
    window we'd otherwise hammer connection-refused errors. Polls
    /healthz with a short sleep until the model is ready or until
    the global startup retry budget runs out.
    """
    import json
    import urllib.error
    import urllib.request

    deadline = time.time() + _STARTUP_RETRY_SECONDS
    backoff = 0.5
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{_TWHIN_URL}/healthz", timeout=5) as resp:
                if resp.status == 200:
                    body = json.loads(resp.read())
                    if body.get("ready"):
                        if log_fn:
                            log_fn(f"TWHIN sidecar ready at {_TWHIN_URL}")
                        return True
        except (urllib.error.URLError, urllib.error.HTTPError, ConnectionError, TimeoutError):
            pass
        time.sleep(backoff)
        backoff = min(backoff * 1.5, 5.0)
    if log_fn:
        log_fn(
            f"TWHIN sidecar did not become ready within "
            f"{_STARTUP_RETRY_SECONDS}s — recommender will fall back to recent-posts mode"
        )
    return False


def twhin_embed(texts: list, log_fn=None) -> Optional[np.ndarray]:
    """Embed texts via the sidecar. Returns (N, dim) float32 or None on failure."""
    return _post_embed(list(texts), log_fn=log_fn)


# ──────────────────────────────────────────────────────────────────
# Per-platform rec updater (unchanged math, only the embed call swapped)
# ──────────────────────────────────────────────────────────────────


def create_twhin_rec_updater(platform, log_fn, suffix=""):
    """Create a cached TWHIN-BERT rec update function for a platform.

    Args:
        platform: OASIS Platform object (has db_cursor, max_rec_post_len)
        log_fn: logging function (e.g. log_info)
        suffix: identifier for logging ("" for Twitter, "Reddit" for Reddit)

    Returns:
        async function to replace platform.update_rec_table
    """
    max_rec = getattr(platform, 'max_rec_post_len', 20)
    last_post_id = [0]
    user_embs = [None]   # mutable container for numpy array
    post_embs = [None]
    post_ids = []
    user_ids = []
    sidecar_ready = [False]

    async def _rec_update():
        try:
            cursor = platform.db_cursor

            # Wait for sidecar on first call. If it never comes up we
            # fall back to the "recent posts" path below — sims keep
            # running with degraded recommendations rather than
            # crashing.
            if not sidecar_ready[0]:
                sidecar_ready[0] = _wait_for_sidecar(log_fn=log_fn)

            # 1. One-time: embed all user bios
            if user_embs[0] is None and sidecar_ready[0]:
                cursor.execute("SELECT user_id, bio FROM user ORDER BY user_id")
                rows = cursor.fetchall()
                user_ids.clear()
                bios = []
                for uid, bio in rows:
                    user_ids.append(uid)
                    bios.append(bio if bio else "user")
                if bios:
                    embedded = twhin_embed(bios, log_fn=log_fn)
                    if embedded is not None:
                        user_embs[0] = embedded
                        log_fn(f"TWHIN rec{suffix}: embedded {len(bios)} users")

            # 2. Embed only new posts
            if sidecar_ready[0]:
                cursor.execute(
                    "SELECT post_id, content FROM post WHERE post_id > ? ORDER BY post_id",
                    (last_post_id[0],),
                )
                new_posts = [(pid, c) for pid, c in cursor.fetchall() if c]
                if new_posts:
                    new_ids = [p[0] for p in new_posts]
                    new_vecs = twhin_embed([p[1] for p in new_posts], log_fn=log_fn)
                    if new_vecs is not None:
                        post_ids.extend(new_ids)
                        if post_embs[0] is None:
                            post_embs[0] = new_vecs
                        else:
                            post_embs[0] = np.vstack([post_embs[0], new_vecs])
                        last_post_id[0] = new_ids[-1]

            # 3. Compute similarity & build rec table
            cursor.execute("DELETE FROM rec")
            insert_values = []

            u = user_embs[0]
            p = post_embs[0]
            if u is not None and p is not None and len(p) > 0 and len(u) > 0:
                u_norm = u / (np.linalg.norm(u, axis=1, keepdims=True) + 1e-8)
                p_norm = p / (np.linalg.norm(p, axis=1, keepdims=True) + 1e-8)
                sim = u_norm @ p_norm.T
                k = min(max_rec, sim.shape[1])
                top_k = np.argpartition(-sim, k, axis=1)[:, :k]
                for i, uid in enumerate(user_ids):
                    for j in top_k[i]:
                        insert_values.append((uid, post_ids[j]))

            # Fallback: recent posts (used when sidecar is unavailable
            # or hasn't seen any posts yet).
            if not insert_values:
                cursor.execute(
                    "SELECT post_id FROM post ORDER BY created_at DESC LIMIT ?",
                    (min(200, max_rec * 3),),
                )
                all_posts = [r[0] for r in cursor.fetchall()]
                if all_posts:
                    cursor.execute("SELECT user_id FROM user")
                    for uid, in cursor.fetchall():
                        for pid in all_posts[:max_rec]:
                            insert_values.append((uid, pid))

            if insert_values:
                cursor.executemany(
                    "INSERT INTO rec (user_id, post_id) VALUES (?, ?)",
                    insert_values,
                )
                cursor.connection.commit()
        except Exception as exc:
            log_fn(f"TWHIN rec{suffix} error: {exc}")

    return _rec_update
