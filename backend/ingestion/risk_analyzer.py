import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from backend.config import BASE_DIR, GEMINI_API_KEY
from backend.models import ClauseNode, DocumentParsed, DefectItem, RiskItem, DocumentRiskProfile
from backend.llm.provider import GeminiProvider, LLMProvider

def load_reference_clauses() -> Dict[str, List[Dict[str, Any]]]:
    ref_path = BASE_DIR / "data" / "reference_clauses" / "reference_clauses.json"
    if ref_path.exists():
        with open(ref_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

class ClauseDeviationSchema(BaseModel):
    deviation_rating: str  # standard, aggressive, unusual
    rationale: str
    driving_span: str

PERSPECTIVE_ROLES = {
    "rental": ("tenant", "landlord"),
    "employment": ("employee", "employer"),
    "saas_terms": ("customer", "vendor"),
    "service_agreement": ("customer", "vendor"),
    "nda": ("disclosing_party", "receiving_party"),
    "unknown": ("party_a", "party_b")
}

AGGRESSIVE_KEYWORDS = [
    "unconditionally", "regardless of fault", "$100", "5 years", "in perpetuity",
    "3 days notice", "180 days", "immediately without cause", "without notice",
    "15% flat", "waives all rights", "sole discretion", "unilateral", "strictly limited to"
]

UNUSUAL_KEYWORDS = [
    "bank guarantee", "forfeit", "30 days of the event", "liquidated damages of $500,000",
    "irrevocable"
]

def analyze_clause_heuristic(clause: ClauseNode, ref_list: List[Dict[str, Any]]) -> tuple[str, str, str, str, str]:
    """
    Offline/heuristic analysis comparing clause against reference library.
    Returns (deviation_rating, rationale, driving_span, closest_ref_text, closest_ref_rating)
    """
    text_lower = clause.text.lower()
    
    # 1. Match driving keywords
    driving_span = ""
    for kw in AGGRESSIVE_KEYWORDS:
        if kw in text_lower:
            driving_span = kw
            break
            
    if not driving_span:
        for kw in UNUSUAL_KEYWORDS:
            if kw in text_lower:
                driving_span = kw
                break

    # 2. Rating & Rationale
    deviation_rating = "standard"
    rationale = "Clause aligns with standard commercial market baseline provisions."
    
    if any(kw in text_lower for kw in AGGRESSIVE_KEYWORDS):
        deviation_rating = "aggressive"
        rationale = f"Clause contains aggressive, highly one-sided terms around '{driving_span or 'unilateral obligations'}'."
    elif any(kw in text_lower for kw in UNUSUAL_KEYWORDS):
        deviation_rating = "unusual"
        rationale = f"Clause contains non-standard legal provisions regarding '{driving_span or 'atypical covenants'}'."

    # 3. Find closest reference variant
    closest_ref_text = ""
    closest_ref_rating = "standard"
    
    if ref_list:
        # Match by rating
        match = next((r for r in ref_list if r.get("rating") == deviation_rating), ref_list[0])
        closest_ref_text = match.get("text", "")
        closest_ref_rating = match.get("rating", "standard")
    
    if not driving_span:
        driving_span = clause.text[:60] + "..." if len(clause.text) > 60 else clause.text

    return deviation_rating, rationale, driving_span, closest_ref_text, closest_ref_rating

def calculate_perspective_risk(
    category: str,
    deviation_rating: str,
    perspective: str,
    doc_type: str
) -> str:
    """
    Calculates perspective risk level (low, medium, high, critical) based on party role.
    """
    perspective = perspective.lower()
    
    if deviation_rating == "standard":
        return "low"

    # Define weaker/vulnerable party roles for aggressive terms
    vulnerable_roles = {"tenant", "employee", "customer", "receiving_party"}
    protected_roles = {"landlord", "employer", "vendor", "disclosing_party"}

    if deviation_rating == "aggressive":
        if perspective in vulnerable_roles:
            return "critical" if category in ["limitation_of_liability", "indemnity", "termination", "non_compete"] else "high"
        elif perspective in protected_roles:
            return "low"
        else:
            return "high"

    if deviation_rating == "unusual":
        return "high" if perspective in vulnerable_roles else "medium"

    return "medium"

def analyze_document_risk(
    doc: DocumentParsed,
    perspective: Optional[str] = None,
    provider: Optional[LLMProvider] = None
) -> DocumentRiskProfile:
    """
    Generates a full DocumentRiskProfile for a document given a party perspective.
    """
    ref_library = load_reference_clauses()

    # Determine perspective role
    valid_roles = PERSPECTIVE_ROLES.get(doc.doc_type, ("party_a", "party_b"))
    if not perspective or perspective.lower() not in [r.lower() for r in valid_roles]:
        perspective = valid_roles[0]  # default to primary/vulnerable role

    risk_items: List[RiskItem] = []
    
    for clause in doc.clauses:
        cat = clause.category if hasattr(clause, "category") and clause.category else "other"
        category_refs = ref_library.get(cat, [])
        
        # Analyze clause
        deviation_rating, rationale, driving_span, ref_text, ref_type = analyze_clause_heuristic(clause, category_refs)
        
        # Determine perspective risk level
        perspective_risk = calculate_perspective_risk(cat, deviation_rating, perspective, doc.doc_type)

        risk_items.append(RiskItem(
            id=f"{doc.id}_risk_{clause.id}",
            clause_id=clause.id,
            clause_number=clause.clause_number,
            category=cat,
            deviation_rating=deviation_rating,
            perspective_risk=perspective_risk,
            rationale=rationale,
            driving_span=driving_span,
            closest_reference_text=ref_text,
            closest_reference_type=ref_type
        ))

    # Calculate overall document risk score (0 - 100)
    score_weights = {
        "low": 2,
        "medium": 10,
        "high": 25,
        "critical": 45
    }
    
    total_weighted_points = sum(score_weights.get(item.perspective_risk, 5) for item in risk_items)
    
    # Add points for detected inconsistencies / defects
    defect_weights = {"low": 5, "medium": 15, "high": 30}
    for defect in doc.defects:
        total_weighted_points += defect_weights.get(defect.severity, 15)

    # Normalize to 0 - 100 range
    risk_score = round(min(100.0, total_weighted_points * 0.85), 1)

    return DocumentRiskProfile(
        document_id=doc.id,
        perspective=perspective,
        overall_risk_score=risk_score,
        risk_items=risk_items,
        inconsistencies=doc.defects
    )
