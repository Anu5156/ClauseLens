from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from backend.models import DocumentParsed
from backend.ingestion.pdf_parser import parse_pdf_spans
from backend.ingestion.docx_parser import parse_docx_spans
from backend.ingestion.clause_parser import parse_clause_hierarchy
from backend.ingestion.crossref_builder import build_cross_reference_graph
from backend.ingestion.flaw_detector import extract_definitions_and_defects
from backend.ingestion.classifier import classify_and_profile_document, DocumentProfile
from backend.database import save_document

def ingest_document(file_path: str) -> tuple[DocumentParsed, DocumentProfile]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    file_ext = path.suffix.lower()
    doc_id = f"doc_{path.stem.lower().replace(' ', '_')}"

    if file_ext == ".pdf":
        raw_text, line_blocks, page_count = parse_pdf_spans(file_path)
        file_type = "pdf"
    elif file_ext in [".docx", ".doc"]:
        raw_text, line_blocks, page_count = parse_docx_spans(file_path)
        file_type = "docx"
    else:
        raise ValueError(f"Unsupported file format: {file_ext}")

    # 1. Hierarchical Clause Parsing
    clauses = parse_clause_hierarchy(doc_id, line_blocks)

    # 2. Cross-Reference Graph
    crossrefs = build_cross_reference_graph(doc_id, clauses)

    # 3. Definitions & Defect Detection
    definitions, defects = extract_definitions_and_defects(doc_id, clauses, crossrefs)

    parsed_doc = DocumentParsed(
        id=doc_id,
        filename=path.name,
        file_type=file_type,
        doc_type="unknown",
        upload_timestamp=datetime.now().isoformat(),
        page_count=page_count,
        raw_text=raw_text,
        clauses=clauses,
        crossrefs=crossrefs,
        definitions=definitions,
        defects=defects
    )

    # 4. Phase 2 Classification & Profiling
    parsed_doc, profile = classify_and_profile_document(parsed_doc)
    parsed_doc.doc_type = profile.doc_type

    # Save to SQLite
    save_document(parsed_doc)

    return parsed_doc, profile
