from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

# Ensure project root is first in sys.path
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

_startup_error = None
try:
    from backend.main import app as _actual_app
    app = _actual_app
except Exception as e:
    _startup_error = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="ClauseLens Error Interceptor")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    async def interceptor_fallback(path: str):
        files_at_root = [p.name for p in _ROOT.iterdir()] if _ROOT.exists() else []
        backend_dir = _ROOT / "backend"
        files_in_backend = [p.name for p in backend_dir.iterdir()] if backend_dir.exists() else []
        return JSONResponse(
            status_code=500,
            content={
                "error": "Startup / Import Error in ClauseLens",
                "detail": str(e),
                "traceback": _startup_error.splitlines(),
                "path_requested": path,
                "sys_path": sys.path,
                "root_dir": str(_ROOT),
                "files_at_root": files_at_root,
                "files_in_backend": files_in_backend,
            }
        )
