import os
import sys
import shutil
import tempfile
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Detect Vercel / serverless environment
IS_VERCEL = bool(os.getenv("VERCEL"))

if IS_VERCEL:
    # On Vercel, the application directory (/var/task) is read-only.
    # Writable operations (SQLite, uploads) must use /tmp.
    TMP_DIR = Path(tempfile.gettempdir())
    db_file_name = "clause_lens.db"
    dest_db = TMP_DIR / db_file_name
    src_db = BASE_DIR / db_file_name

    # If seeded database exists in deployment package, copy to /tmp if not already present
    if src_db.exists() and not dest_db.exists():
        try:
            shutil.copy2(src_db, dest_db)
        except Exception:
            pass

    DATABASE_PATH = os.getenv("DATABASE_PATH", str(dest_db))
    UPLOAD_DIR = TMP_DIR / "uploads"
else:
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "clause_lens.db"))
    UPLOAD_DIR = BASE_DIR / "data" / "uploads"

try:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

RETRIEVAL_CONFIDENCE_THRESHOLD = float(os.getenv("RETRIEVAL_CONFIDENCE_THRESHOLD", "0.45"))
SAMPLE_DATA_DIR = Path(os.getenv("SAMPLE_DATA_DIR", str(BASE_DIR / "data" / "samples")))

try:
    SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass

