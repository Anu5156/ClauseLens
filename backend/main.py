import os
import re
import logging
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import SAMPLE_DATA_DIR, BASE_DIR
from backend.ingestion.pipeline import ingest_document
from backend.ingestion.classifier import classify_and_profile_document, DocumentProfile
from backend.ingestion.risk_analyzer import analyze_document_risk, DocumentRiskProfile
from backend.models import (
    QARequest, QAResponse, CompareRequest, DocumentComparisonResult,
    DeadlineExport, LawyerPrepPack, RewriteRequest, RewriteResult, NegotiationProposal,
)
from backend.qa.engine import answer_question
from backend.comparison.aligner import compare_documents
from backend.actionable.deadlines import extract_deadlines
from backend.actionable.lawyer_prep import build_lawyer_prep_pack
from backend.actionable.rewriter import generate_document_rewrite
from backend.actionable.negotiation import generate_negotiation_proposals
from backend.database import get_document, list_documents, save_document

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("clauselens.api")

# ─── Constants ────────────────────────────────────────────────────────────────
MAX_UPLOAD_SIZE_BYTES: int = 25 * 1024 * 1024   # 25 MB hard limit
ALLOWED_EXTENSIONS: tuple[str, ...] = (".pdf", ".docx", ".doc")

# ─── Application ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="ClauseLens API",
    version="1.0.0",
    description="Advanced legal document intelligence: clause extraction, risk analysis, grounded QA, and semantic diff.",
)

# CORS: restrict to same-origin in production; override via ALLOWED_ORIGINS env var.
_cors_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

@app.get("/api/health")
def health_check():
    logger.info("Health check called")
    return {"status": "ok", "service": "ClauseLens Backend", "version": "1.0.0"}

@app.get("/api/documents")
def get_documents():
    return list_documents()

@app.get("/api/documents/{doc_id}")
def get_document_by_id(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@app.get("/api/documents/{doc_id}/profile", response_model=DocumentProfile)
def get_document_profile(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    _, profile = classify_and_profile_document(doc)
    return profile

@app.get("/api/documents/{doc_id}/risk", response_model=DocumentRiskProfile)
def get_document_risk(doc_id: str, perspective: Optional[str] = None):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    risk_profile = analyze_document_risk(doc, perspective=perspective)
    return risk_profile

@app.post("/api/documents/{doc_id}/qa", response_model=QAResponse)
def ask_document_question(doc_id: str, request: QARequest):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    response = answer_question(doc, request.question)
    return response

@app.post("/api/documents/compare", response_model=DocumentComparisonResult)
def compare_documents_endpoint(request: CompareRequest):
    doc_a = get_document(request.doc_id_a)
    if not doc_a:
        raise HTTPException(status_code=404, detail=f"Document A not found: {request.doc_id_a}")
    doc_b = get_document(request.doc_id_b)
    if not doc_b:
        raise HTTPException(status_code=404, detail=f"Document B not found: {request.doc_id_b}")
    return compare_documents(doc_a, doc_b)

@app.get("/api/documents/{doc_id}/actionable/deadlines", response_model=DeadlineExport)
def get_document_deadlines(doc_id: str, effective_date: Optional[str] = None):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return extract_deadlines(doc, effective_date_str=effective_date)

@app.get("/api/documents/{doc_id}/actionable/deadlines/ics")
def download_deadlines_ics(doc_id: str, effective_date: Optional[str] = None):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    deadline_export = extract_deadlines(doc, effective_date_str=effective_date)
    return Response(
        content=deadline_export.ics_content,
        media_type="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={doc_id}_deadlines.ics"}
    )

@app.get("/api/documents/{doc_id}/actionable/lawyer-prep", response_model=LawyerPrepPack)
def get_document_lawyer_prep(doc_id: str):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return build_lawyer_prep_pack(doc)

@app.post("/api/documents/{doc_id}/actionable/rewrite", response_model=RewriteResult)
def rewrite_document_endpoint(doc_id: str, request: RewriteRequest):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return generate_document_rewrite(doc, level=request.level, language=request.language)

@app.get("/api/documents/{doc_id}/actionable/negotiations", response_model=List[NegotiationProposal])
def get_negotiation_proposals(doc_id: str, perspective: Optional[str] = None):
    doc = get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return generate_negotiation_proposals(doc, perspective=perspective)

@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    """Ingest a PDF or DOCX contract. Max size: 25 MB."""
    raw_name = file.filename or "uploaded_contract.pdf"
    # Strip any path component and sanitise the filename
    clean_filename = re.sub(r"[^a-zA-Z0-9_.-]", "_", os.path.basename(raw_name))

    if not clean_filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds the {MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB upload limit.",
        )

    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / clean_filename

    temp_path.write_bytes(contents)
    logger.info("Received upload: %s (%d bytes)", clean_filename, len(contents))

    try:
        parsed_doc, profile = ingest_document(str(temp_path))
        logger.info("Ingested document: %s → %s clauses", parsed_doc.id, len(parsed_doc.clauses))
        return {"document": parsed_doc, "profile": profile}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Ingestion failed for %s", clean_filename)
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {exc}") from exc

# ─── Static Frontend (SPA) ────────────────────────────────────────────────────
frontend_dir = BASE_DIR / "frontend"
frontend_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
