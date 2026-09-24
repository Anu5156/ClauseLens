"""
Seed script to populate ClauseLens database with benchmark sample documents.
Runs idempotently: ensures samples exist, parses, classifies, links, analyzes risks,
and stores them in SQLite (clause_lens.db).
"""

import sys
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import SAMPLE_DATA_DIR
from backend.sample_generator import create_all_samples
from backend.ingestion.pipeline import ingest_document
from backend.ingestion.risk_analyzer import analyze_document_risk
from backend.database import init_db, list_documents

def seed_database(verbose: bool = True):
    if verbose:
        print("=" * 65)
        print("ClauseLens: Initializing & Seeding Sample Documents")
        print("=" * 65)

    init_db()

    sample_files = [
        ("residential_lease.pdf", "tenant"),
        ("employment_agreement.docx", "employee"),
        ("saas_terms.pdf", "customer"),
        ("saas_terms_v2.pdf", "customer")
    ]

    # 1. Ensure sample documents exist (only generate if missing)
    if any(not (SAMPLE_DATA_DIR / f).exists() for f, _ in sample_files):
        try:
            create_all_samples()
        except Exception:
            pass

    seeded_docs = []

    for filename, perspective in sample_files:
        file_path = SAMPLE_DATA_DIR / filename
        if not file_path.exists():
            if verbose:
                print(f"[ERROR] Sample file missing: {file_path}")
            continue

        if verbose:
            print(f"--> Ingesting & indexing: {filename}...")
        
        parsed_doc, profile = ingest_document(str(file_path))

        # Precompute risk profile to verify validity
        risk_profile = analyze_document_risk(parsed_doc, perspective=perspective)

        seeded_docs.append((parsed_doc, risk_profile))

    if verbose:
        print("\n" + "=" * 65)
        print("SEEDING COMPLETE. Active Documents in Database:")
        print("=" * 65)
        for doc, risk in seeded_docs:
            print(f"- ID: {doc.id}")
            print(f"  File: {doc.filename} ({doc.file_type.upper()}) | Type: {doc.doc_type}")
            print(f"  Clauses: {len(doc.clauses)} | Crossrefs: {len(doc.crossrefs)} | Defects: {len(doc.defects)}")
            print(f"  Risk Profile ({risk.perspective}): Score {risk.overall_risk_score}/100")
            print("-" * 65)

    return seeded_docs

if __name__ == "__main__":
    seed_database(verbose=True)
