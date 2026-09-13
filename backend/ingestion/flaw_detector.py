import re
from typing import List, Tuple
from backend.models import ClauseNode, CrossRefEdge, DefinedTerm, DefectItem

# Common legal terms that are capitalized but not specific contract terms
STANDARD_EXCEPTIONS = {
    "Agreement", "Party", "Parties", "Section", "Clause", "Article", "Schedule", "Exhibit",
    "Landlord", "Tenant", "Employer", "Employee", "Company", "Customer", "Vendor",
    "State", "Law", "Court", "Act", "GST", "VAT", "USD", "INR", "Monday", "Tuesday",
    "Wednesday", "Thursday", "Friday", "Saturday", "Sunday", "January", "February",
    "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"
}

def extract_definitions_and_defects(
    doc_id: str,
    clauses: List[ClauseNode],
    crossrefs: List[CrossRefEdge]
) -> Tuple[List[DefinedTerm], List[DefectItem]]:
    """
    Extracts defined terms, checks for undefined capitalized terms,
    dangling references, and conflicting notice periods.
    """
    definitions: List[DefinedTerm] = []
    defects: List[DefectItem] = []
    def_count = 0
    defect_count = 0

    defined_term_set = set()

    # 1. Extract Definitions from "Definitions" clauses or quote patterns
    for clause in clauses:
        is_def_clause = "definition" in clause.title.lower() or "definitions" in clause.text[:100].lower()
        
        # Match patterns like "Term" means / "Term" shall mean / "Term": definition
        matches = re.findall(r'["“]([A-Z][A-Za-z0-9\s\-_]{2,30})["”]\s*(?:means|shall mean|\:)', clause.text)
        for term in matches:
            term_clean = term.strip()
            if term_clean not in defined_term_set:
                def_count += 1
                defined_term_set.add(term_clean)
                definitions.append(DefinedTerm(
                    id=f"{doc_id}_def_{def_count}",
                    document_id=doc_id,
                    term=term_clean,
                    definition=clause.text[:200],  # snippet
                    clause_id=clause.id
                ))

    # 2. Flag Dangling Cross-References
    for ref in crossrefs:
        if ref.is_dangling:
            defect_count += 1
            defects.append(DefectItem(
                id=f"{doc_id}_defect_{defect_count}",
                document_id=doc_id,
                defect_type="dangling_crossref",
                description=f"Dangling reference '{ref.target_label}' in Clause {ref.from_clause_number} points to a non-existent clause.",
                clause_id=ref.from_clause_id,
                severity="high"
            ))

    # 3. Detect Undefined Capitalized Terms in Document Body
    body_text = "\n".join([c.text for c in clauses])
    # Match Title Case multi-word or quoted capitalized terms: "Restricted Territory" or 'Restricted Territory'
    capitalized_candidates = set(re.findall(r'["“]([A-Z][A-Za-z0-9\s]{2,30})["”]', body_text))
    # Also find occurrences of Capitalized Phrase in body
    title_case_words = set(re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', body_text))
    
    candidates = capitalized_candidates.union(title_case_words)
    
    for candidate in candidates:
        cand_clean = candidate.strip()
        words = cand_clean.split()
        if cand_clean not in defined_term_set and cand_clean not in STANDARD_EXCEPTIONS:
            # Check if all words are standard exceptions
            if all(w in STANDARD_EXCEPTIONS for w in words):
                continue
            # Make sure it actually appears in body text
            if len(cand_clean) > 3:
                defect_count += 1
                # Find associated clause
                target_clause_id = None
                for c in clauses:
                    if cand_clean in c.text and "definition" not in c.title.lower():
                        target_clause_id = c.id
                        break
                defects.append(DefectItem(
                    id=f"{doc_id}_defect_{defect_count}",
                    document_id=doc_id,
                    defect_type="undefined_term",
                    description=f"Capitalized term '{cand_clean}' is used in the document body but never defined in the Definitions section.",
                    clause_id=target_clause_id,
                    severity="medium"
                ))

    # 4. Detect Conflicting Notice Periods
    notice_periods = []
    for clause in clauses:
        # Match "X days notice" or "X days' notice" or "X-day notice"
        matches = re.findall(r'(\d+)\s*(?:-\s*day|day|days|\'s|\s+days)\s*(?:written\s+)?notice', clause.text, re.IGNORECASE)
        for m in matches:
            days = int(m)
            notice_periods.append((days, clause))

    if len(notice_periods) >= 2:
        distinct_days = set(d[0] for d in notice_periods)
        if len(distinct_days) > 1:
            days_str = " vs ".join([f"{d[0]} days (Clause {d[1].clause_number})" for d in notice_periods])
            defect_count += 1
            defects.append(DefectItem(
                id=f"{doc_id}_defect_{defect_count}",
                document_id=doc_id,
                defect_type="conflicting_notice",
                description=f"Inconsistent notice period detected across clauses: {days_str}.",
                clause_id=notice_periods[0][1].id,
                severity="high"
            ))

    # 5. Detect Governing Law vs Arbitration Seat Mismatch
    gov_law = None
    arb_seat = None
    gov_clause_id = None

    for clause in clauses:
        text_lower = clause.text.lower()
        if "governing law" in text_lower or "laws of" in text_lower:
            m = re.search(r'(?:laws of|governed by the laws of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', clause.text)
            if m:
                gov_law = m.group(1).strip()
                gov_clause_id = clause.id
        if "arbitration" in text_lower or "arbitral seat" in text_lower or "venue" in text_lower:
            m = re.search(r'(?:seat of arbitration|arbitration in|venue shall be|held in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', clause.text)
            if m:
                arb_seat = m.group(1).strip()

    if gov_law and arb_seat and gov_law.lower() != arb_seat.lower():
        if gov_law.lower() not in arb_seat.lower() and arb_seat.lower() not in gov_law.lower():
            defect_count += 1
            defects.append(DefectItem(
                id=f"{doc_id}_defect_{defect_count}",
                document_id=doc_id,
                defect_type="governing_law_mismatch",
                description=f"Jurisdiction mismatch detected: Governing law specifies '{gov_law}' while arbitration venue specifies '{arb_seat}'.",
                clause_id=gov_clause_id,
                severity="medium"
            ))

    # 6. Detect Numbering Gaps in Hierarchy
    numbers = []
    number_clause_map = {}
    for clause in clauses:
        num_match = re.match(r'^(\d+)(?:\.|\b)', clause.clause_number)
        if num_match:
            try:
                n = int(num_match.group(1))
                if n not in number_clause_map:
                    numbers.append(n)
                    number_clause_map[n] = clause
            except ValueError:
                pass

    if len(numbers) > 1:
        sorted_nums = sorted(list(set(numbers)))
        for i in range(len(sorted_nums) - 1):
            curr, nxt = sorted_nums[i], sorted_nums[i+1]
            if 1 < (nxt - curr) <= 3:
                missing = [str(x) for x in range(curr + 1, nxt)]
                defect_count += 1
                defects.append(DefectItem(
                    id=f"{doc_id}_defect_{defect_count}",
                    document_id=doc_id,
                    defect_type="numbering_gap",
                    description=f"Hierarchy numbering gap detected: Section(s) {', '.join(missing)} missing between Section {curr} and Section {nxt}.",
                    clause_id=number_clause_map[nxt].id,
                    severity="medium"
                ))

    # 7. Detect Timeline / Date Contradictions
    for clause in clauses:
        text_lower = clause.text.lower()
        if "cure" in text_lower and "notice" in text_lower:
            cure_m = re.search(r'cure\s+(?:period\s+of\s+)?(\d+)\s*days', text_lower)
            notice_m = re.search(r'notice\s+(?:period\s+of\s+)?(\d+)\s*days', text_lower)
            if cure_m and notice_m:
                cure_days = int(cure_m.group(1))
                notice_days = int(notice_m.group(1))
                if cure_days > notice_days:
                    defect_count += 1
                    defects.append(DefectItem(
                        id=f"{doc_id}_defect_{defect_count}",
                        document_id=doc_id,
                        defect_type="timeline_contradiction",
                        description=f"Cure period ({cure_days} days) exceeds notice period ({notice_days} days) in Clause {clause.clause_number}.",
                        clause_id=clause.id,
                        severity="high"
                    ))

    return definitions, defects
