import re
from typing import List, Dict, Any
from backend.models import DocumentParsed, LawyerQuestion, LawyerPrepPack
from backend.ingestion.classifier import classify_and_profile_document
from backend.ingestion.risk_analyzer import analyze_document_risk

def build_lawyer_prep_pack(doc: DocumentParsed) -> LawyerPrepPack:
    """
    Generates a structured, printable Lawyer Consultation Brief with:
    - Structured Fact Summary
    - Document Integrity Checklist
    - Prioritized Questions linked to specific clauses
    """
    _, profile = classify_and_profile_document(doc)
    risk_profile = analyze_document_risk(doc)

    # 1. Fact Summary
    # Extract parties from defined terms
    parties = [d.term for d in doc.definitions if d.term.lower() in {"landlord", "tenant", "company", "customer", "employer", "employee", "vendor"}]
    
    # Extract governing law
    gov_law = "Not specified"
    for c in doc.clauses:
        m = re.search(r'(?:laws of|governed by the laws of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', c.text)
        if m:
            gov_law = m.group(1).strip()
            break

    fact_summary = {
        "document_name": doc.filename,
        "contract_type": profile.doc_type_name,
        "total_clauses": len(doc.clauses),
        "page_count": doc.page_count,
        "identified_parties": parties or ["Standard Commercial Contracting Parties"],
        "governing_law": gov_law,
        "overall_risk_score": f"{risk_profile.overall_risk_score}/100"
    }

    # 2. Document Checklist
    dangling_count = sum(1 for r in doc.crossrefs if r.is_dangling)
    undefined_count = sum(1 for d in doc.defects if d.defect_type == "undefined_term")
    conflicts_count = sum(1 for d in doc.defects if d.defect_type == "conflicting_notice")

    checklist = [
        {
            "item": "Internal Cross-References Verified",
            "passed": dangling_count == 0,
            "details": f"{dangling_count} dangling reference(s) detected pointing to missing sections" if dangling_count > 0 else "All cross-references resolve properly."
        },
        {
            "item": "Capitalized Term Definitions Complete",
            "passed": undefined_count == 0,
            "details": f"{undefined_count} capitalized term(s) used in body without definitions" if undefined_count > 0 else "All capitalized terms are defined in definitions section."
        },
        {
            "item": "Notice Period Consistency",
            "passed": conflicts_count == 0,
            "details": "Inconsistent notice periods found across termination and renewal sections" if conflicts_count > 0 else "Notice periods are consistent across all clauses."
        },
        {
            "item": "Standard Industry Clause Coverage",
            "passed": len(profile.missing_clauses) == 0,
            "details": f"Missing expected clauses: {', '.join(profile.missing_clauses)}" if profile.missing_clauses else "Document contains complete standard clause coverage."
        }
    ]

    # 3. Prioritized Questions to Ask Lawyer
    questions: List[LawyerQuestion] = []
    
    # Generate from defects
    for d in doc.defects:
        target_clause_num = "General"
        if d.clause_id:
            c_node = next((c for c in doc.clauses if c.id == d.clause_id), None)
            if c_node:
                target_clause_num = c_node.clause_number

        if d.defect_type == "dangling_crossref":
            questions.append(LawyerQuestion(
                priority="critical",
                question=f"Clause {target_clause_num} references an absent or misnumbered clause ({d.description.split('reference ')[-1].split(' in')[0]}). How does this drafting defect impact enforceability?",
                clause_id=d.clause_id or doc.clauses[0].id,
                clause_number=target_clause_num,
                context_reason="Dangling reference defect creates ambiguous contractual condition."
            ))
        elif d.defect_type == "conflicting_notice":
            questions.append(LawyerQuestion(
                priority="critical",
                question=f"The contract prescribes conflicting notice periods across sections ({d.description.split(': ')[-1]}). In the event of dispute, which timeframe prevails under {gov_law} law?",
                clause_id=d.clause_id or doc.clauses[0].id,
                clause_number=target_clause_num,
                context_reason="Contradictory operational timelines across termination/renewal provisions."
            ))
        elif d.defect_type == "undefined_term":
            term_name = d.description.split("'")[1] if "'" in d.description else "Undefined Term"
            if len(questions) < 6:
                questions.append(LawyerQuestion(
                    priority="medium",
                    question=f"The term '{term_name}' is capitalized in Clause {target_clause_num} but never defined. Should we request an express definition to prevent adverse interpretation?",
                    clause_id=d.clause_id or doc.clauses[0].id,
                    clause_number=target_clause_num,
                    context_reason="Undefined capitalized phrase risks statutory or common-law default interpretation."
                ))

    # Generate from aggressive risk items
    for item in risk_profile.risk_items:
        if item.deviation_rating == "aggressive":
            questions.append(LawyerQuestion(
                priority="high",
                question=f"Clause {item.clause_number} ({item.category.upper()}) contains aggressive terms ('{item.driving_span}'). What standard carve-outs or reciprocal language should we propose?",
                clause_id=item.clause_id,
                clause_number=item.clause_number,
                context_reason=f"Aggressive deviation from commercial standard: {item.rationale}"
            ))

    # Fallback general question if clean
    if not questions:
        questions.append(LawyerQuestion(
            priority="medium",
            question=f"Are the dispute resolution and governing law provisions in Clause {doc.clauses[-1].clause_number} standard and favorable for our jurisdiction?",
            clause_id=doc.clauses[-1].id,
            clause_number=doc.clauses[-1].clause_number,
            context_reason="Standard baseline legal verification."
        ))

    # Sort questions: critical first, then high, then medium
    priority_order = {"critical": 0, "high": 1, "medium": 2}
    questions.sort(key=lambda q: priority_order.get(q.priority, 3))

    return LawyerPrepPack(
        document_id=doc.id,
        fact_summary=fact_summary,
        checklist=checklist,
        prioritized_questions=questions
    )
