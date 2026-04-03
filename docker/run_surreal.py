"""MiroFish Backend — SurrealDB + English + Dual Model (Docker entrypoint)"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("USE_SURREALDB", "true")
import surrealdb_adapter.patch_mirofish

from app import create_app
from app.config import Config
from surrealdb_adapter.llm_patch import patch_llm_client
from surrealdb_adapter.i18n_patch import apply_i18n_patch
from surrealdb_adapter.boost_patch import apply_boost_patch

patch_llm_client()
apply_i18n_patch()
apply_boost_patch()

def main():
    errors = Config.validate()
    if errors:
        [print(f"  - {e}") for e in errors]
        sys.exit(1)
    app = create_app()
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 5001))
    print(f"MiroFish (SurrealDB) starting on {host}:{port}")
    app.run(host=host, port=port, debug=False, threaded=True)

if __name__ == "__main__":
    main()
