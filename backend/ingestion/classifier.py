import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from backend.models import ClauseNode, DocumentParsed
from backend.llm.provider import GeminiProvider, LLMProvider
from backend.config import BASE_DIR, GEMINI_API_KEY

TAXONOMY = [
    "indemnity", "limitation_of_liability", "termination", "auto_renewal",
    "non_compete", "confidentiality", "ip_assignment", "payment_terms",
    "notice_period", "dispute_resolution", "governing_law", "unilateral_amendment",
    "data_privacy", "force_majeure", "other"
]

DOCUMENT_TYPES = ["rental", "employment", "saas_terms", "nda", "service_agreement", "unknown"]

class ClauseCategoryItem(BaseModel):
    clause_id: str
    category: str  # must be in TAXONOMY
    confidence: float

class DocumentClassificationBatch(BaseModel):
    doc_type: str  # must be in DOCUMENT_TYPES
    classifications: List[ClauseCategoryItem]

class DocumentProfile(BaseModel):
    document_id: str
    filename: str
    doc_type: str
    doc_type_name: str
    clause_type_counts: Dict[str, int]
    expected_clauses: List[str]
    present_clauses: List[str]
    missing_clauses: List[str]
    total_clauses: int

def load_document_templates() -> Dict[str, Any]:
    template_path = BASE_DIR / "data" / "templates" / "document_templates.yaml"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

# Fallback heuristic rules for offline / keyless execution
HEURISTIC_RULES = [
    (r'\b(indemnif|hold harmless)\b', "indemnity"),
    (r'\b(limitation of liability|maximum liability|aggregate liability)\b', "limitation_of_liability"),
    (r'\b(terminat|cancel|expiration)\b', "termination"),
    (r'\b(auto-renew|automatically renew|renewal)\b', "auto_renewal"),
    (r'\b(non-compete|competing business|restrictive covenant)\b', "non_compete"),
    (r'\b(confidential|proprietary information|non-disclosure)\b', "confidentiality"),
    (r'\b(intellectual property|ip right|invention|work for hire)\b', "ip_assignment"),
    (r'\b(rent|fee|salary|payment|invoice|deposit)\b', "payment_terms"),
    (r'\b(written notice|days notice|notice period)\b', "notice_period"),
    (r'\b(arbitrat|dispute|mediation|jurisdiction|court)\b', "dispute_resolution"),
    (r'\b(governing law|laws of|construed in accordance with)\b', "governing_law"),
    (r'\b(amend|modify|unilateral)\b', "unilateral_amendment"),
    (r'\b(privacy|gdpr|personal data)\b', "data_privacy"),
    (r'\b(force majeure|act of god)\b', "force_majeure"),
]

def classify_clause_heuristic(clause: ClauseNode) -> str:
    text = (clause.title + " " + clause.text).lower()
    for pattern, category in HEURISTIC_RULES:
        if re.search(pattern, text):
            return category
    return "other"

def classify_doc_type_heuristic(filename: str, clauses: List[ClauseNode]) -> str:
    fname = filename.lower()
    if "lease" in fname or "rental" in fname:
        return "rental"
    if "employ" in fname or "offer" in fname:
        return "employment"
    if "saas" in fname or "tos" in fname or "terms" in fname:
        return "saas_terms"
    if "nda" in fname or "confidential" in fname:
        return "nda"
    if "service" in fname or "msa" in fname:
        return "service_agreement"
    
    # Check title / text content
    full_text = " ".join([c.text[:200] for c in clauses[:5]]).lower()
    if "lease" in full_text or "tenant" in full_text:
        return "rental"
    if "employee" in full_text or "salary" in full_text:
        return "employment"
    if "saas" in full_text or "license grant" in full_text:
        return "saas_terms"
    
    return "unknown"

def classify_and_profile_document(doc: DocumentParsed, provider: Optional[LLMProvider] = None) -> Tuple[DocumentParsed, DocumentProfile]:
    """
    Classifies all clauses in batch, detects document type, identifies missing clauses against YAML templates,
    and returns updated DocumentParsed and DocumentProfile.
    """
    templates = load_document_templates()
    
    doc_type = "unknown"
    clause_category_map: Dict[str, str] = {}

    # Try LLM Classification if API key is provided and provider is available
    if GEMINI_API_KEY and provider is None:
        try:
            provider = GeminiProvider()
        except Exception:
            provider = None

    if provider:
        # Prepare batch prompt
        clauses_summary = "\n".join([
            f"ID: {c.id} | Title: '{c.title}' | Text Snippet: '{c.text[:150]}...'"
            for c in doc.clauses
        ])
        prompt = f"""
Analyze the following document and classify each clause into one of the allowed categories:
Taxonomy: {TAXONOMY}
Allowed Doc Types: {DOCUMENT_TYPES}

Document Filename: {doc.filename}
Clauses:
{clauses_summary}

Classify the doc_type and provide a category for EVERY clause ID.
"""

        try:
            res: DocumentClassificationBatch = provider.generate_structured(
                schema=DocumentClassificationBatch,
                prompt=prompt,
                system_instruction="You are a legal document classifier. Classify clauses accurately into taxonomy."
            )
            doc_type = res.doc_type if res.doc_type in DOCUMENT_TYPES else classify_doc_type_heuristic(doc.filename, doc.clauses)
            for item in res.classifications:
                cat = item.category if item.category in TAXONOMY else "other"
                clause_category_map[item.clause_id] = cat
        except Exception as e:
            # Fall back to heuristic on error
            doc_type = classify_doc_type_heuristic(doc.filename, doc.clauses)
            for c in doc.clauses:
                clause_category_map[c.id] = classify_clause_heuristic(c)
    else:
        # Heuristic classification
        doc_type = classify_doc_type_heuristic(doc.filename, doc.clauses)
        for c in doc.clauses:
            clause_category_map[c.id] = classify_clause_heuristic(c)

    # Count clause types and update clause objects
    type_counts: Dict[str, int] = {cat: 0 for cat in TAXONOMY}
    present_categories = set()

    for c in doc.clauses:
        cat = clause_category_map.get(c.id, "other")
        c.category = cat
        type_counts[cat] = type_counts.get(cat, 0) + 1
        if cat != "other":
            present_categories.add(cat)

    # Missing clause detection using YAML templates
    template_info = templates.get(doc_type, {})
    doc_type_name = template_info.get("name", doc_type.upper().replace("_", " "))
    expected_clauses = template_info.get("expected_clauses", [])

    missing_clauses = [exp for exp in expected_clauses if exp not in present_categories]

    profile = DocumentProfile(
        document_id=doc.id,
        filename=doc.filename,
        doc_type=doc_type,
        doc_type_name=doc_type_name,
        clause_type_counts=type_counts,
        expected_clauses=expected_clauses,
        present_clauses=list(present_categories),
        missing_clauses=missing_clauses,
        total_clauses=len(doc.clauses)
    )

    return doc, profile
