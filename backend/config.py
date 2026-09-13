import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DATABASE_PATH = os.getenv("DATABASE_PATH", str(BASE_DIR / "clause_lens.db"))
RETRIEVAL_CONFIDENCE_THRESHOLD = float(os.getenv("RETRIEVAL_CONFIDENCE_THRESHOLD", "0.45"))
SAMPLE_DATA_DIR = Path(os.getenv("SAMPLE_DATA_DIR", str(BASE_DIR / "data" / "samples")))

# Ensure sample dir exists
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
