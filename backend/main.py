import shutil
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from backend.config import SAMPLE_DATA_DIR
from backend.ingestion.pipeline import ingest_document
from backend.ingestion.classifier import classify_and_profile_document, DocumentProfile
from backend.ingestion.risk_analyzer import analyze_document_risk, DocumentRiskProfile
from backend.models import (
    QARequest, QAResponse, CompareRequest, DocumentComparisonResult,
    DeadlineExport, LawyerPrepPack, RewriteRequest, RewriteResult, NegotiationProposal
)
from backend.qa.engine import answer_question
from backend.comparison.aligner import compare_documents
from backend.actionable.deadlines import extract_deadlines
from backend.actionable.lawyer_prep import build_lawyer_prep_pack
from backend.actionable.rewriter import generate_document_rewrite
from backend.actionable.negotiation import generate_negotiation_proposals
from backend.database import get_document, list_documents, save_document

app = FastAPI(title="ClauseLens API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "ClauseLens Backend", "phase": "Phase 6 - Actionable outputs"}

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
    if not file.filename.endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    
    upload_dir = Path("data/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / file.filename

    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        parsed_doc, profile = ingest_document(str(temp_path))
        return {"document": parsed_doc, "profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest document: {str(e)}")

# Mount frontend single page application
from fastapi.staticfiles import StaticFiles
from backend.config import BASE_DIR

frontend_dir = BASE_DIR / "frontend"
frontend_dir.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

