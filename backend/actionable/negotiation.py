from typing import List, Dict, Any, Optional
from backend.models import DocumentParsed, NegotiationProposal
from backend.ingestion.risk_analyzer import analyze_document_risk, load_reference_clauses

STANDARD_COUNTER_TEMPLATES = {
    "unilateral_amendment": {
        "text": "No amendment, supplement, or modification of this Agreement shall be binding unless executed in writing and signed by an authorized representative of each party.",
        "rationale": "Prevents unilateral changes to pricing or service levels by requiring mutual written consent."
    },
    "payment_terms": {
        "text": "Customer shall pay all undisputed invoices within thirty (30) days of receipt. Late payments shall bear interest at 1.5% per month or the maximum rate permitted by law.",
        "rationale": "Replaces punitive compounding weekly penalties with standard commercial Net-30 terms and reasonable interest."
    },
    "auto_renewal": {
        "text": "This Agreement shall automatically renew for successive one (1) year periods unless either party provides written notice of non-renewal at least thirty (30) days prior to the expiration of the current term.",
        "rationale": "Eliminates multi-year lock-in and extends a fair 30-day non-renewal notification window."
    },
    "termination": {
        "text": "Either party may terminate this Agreement without cause upon thirty (30) days written notice, or immediately for material breach if uncured after fifteen (15) days written notice.",
        "rationale": "Restores bilateral termination parity and ensures an equitable notice period."
    },
    "limitation_of_liability": {
        "text": "Except for gross negligence or willful misconduct, each party's aggregate liability shall be limited to the total fees paid or payable by Customer in the preceding twelve (12) months.",
        "rationale": "Replaces nominal or one-sided liability waivers with a balanced, reciprocal 12-month contract value cap."
    },
    "indemnity": {
        "text": "Each party shall indemnify and defend the other party against third-party claims arising directly from its gross negligence, willful misconduct, or material breach of this Agreement.",
        "rationale": "Replaces unilateral, uncapped indemnity with mutual indemnification scoped to gross negligence and breach."
    },
    "non_compete": {
        "text": "During the term and for six (6) months following termination, Employee shall not perform competing services within the specific metropolitan area of employment.",
        "rationale": "Narrows post-termination non-compete to standard geographical and temporal limits."
    }
}

def generate_negotiation_proposals(
    doc: DocumentParsed,
    perspective: Optional[str] = None
) -> List[NegotiationProposal]:
    """
    Identifies aggressive clauses in document and proposes balanced, market-standard
    counter-proposals along with concise negotiation rationales.
    """
    risk_profile = analyze_document_risk(doc, perspective=perspective)
    ref_library = load_reference_clauses()
    proposals: List[NegotiationProposal] = []

    for item in risk_profile.risk_items:
        # Generate counter-proposal for aggressive clauses or critical/high risk items
        if item.deviation_rating == "aggressive" or item.perspective_risk in {"critical", "high"}:
            c_node = next((c for c in doc.clauses if c.id == item.clause_id), None)
            orig_text = c_node.text if c_node else item.driving_span

            # Find matching counter-proposal
            cat = item.category.lower()
            if cat in STANDARD_COUNTER_TEMPLATES:
                alt_text = STANDARD_COUNTER_TEMPLATES[cat]["text"]
                rationale = STANDARD_COUNTER_TEMPLATES[cat]["rationale"]
            else:
                # Retrieve from standard reference clauses
                cat_refs = ref_library.get(cat, [])
                std_ref = next((r for r in cat_refs if r.get("rating") == "standard"), None)
                if std_ref:
                    alt_text = std_ref.get("text", "")
                    rationale = f"Replaces aggressive deviation with market-standard {cat.replace('_', ' ')} provision."
                else:
                    alt_text = "The parties agree to mutual, commercially reasonable terms consistent with standard industry practice."
                    rationale = "Replaces one-sided language with reciprocal obligations."

            proposals.append(NegotiationProposal(
                clause_id=item.clause_id,
                clause_number=item.clause_number,
                category=item.category,
                original_text=orig_text.strip(),
                proposed_alternative_text=alt_text,
                one_line_rationale=rationale
            ))

    return proposals
