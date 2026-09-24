import sys
import traceback
from pathlib import Path

# Add project root directory to sys.path so backend modules can be imported
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

try:
    from backend.main import app
    handler = app
except Exception as exc:
    err_tb = traceback.format_exc()
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    app = FastAPI(title="ClauseLens Startup Diagnostic")

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"])
    async def catch_all_error(path: str):
        contents = [p.name for p in ROOT_DIR.iterdir()] if ROOT_DIR.exists() else []
        return JSONResponse(
            status_code=500,
            content={
                "error": "Startup Exception in api/index.py",
                "detail": str(exc),
                "traceback": err_tb.splitlines(),
                "sys_path": sys.path,
                "root_dir": str(ROOT_DIR),
                "root_dir_contents": contents,
            }
        )
    handler = app
