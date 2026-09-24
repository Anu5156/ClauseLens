from __future__ import annotations

import sys
import traceback
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from backend.main import app
except Exception as exc:
    _err_tb = traceback.format_exc()
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
    async def catch_all_error(path: str):
        contents = [p.name for p in ROOT_DIR.iterdir()] if ROOT_DIR.exists() else []
        return JSONResponse(
            status_code=500,
            content={
                "error": "Startup Exception in api/index.py",
                "detail": str(exc),
                "traceback": _err_tb.splitlines(),
                "sys_path": sys.path,
                "root_dir": str(ROOT_DIR),
                "root_dir_contents": contents,
            }
        )
