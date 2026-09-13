import re
from typing import List, Dict, Optional
from backend.models import ClauseNode, CrossRefEdge

# Regex pattern for legal cross-references
CROSSREF_PATTERNS = [
    r'(?:subject to|pursuant to|in accordance with|as set forth in|under|defined in|see)\s+((?:Section|Clause|Article)\s+[\d\.\(a-z\)]+)',
    r'((?:Section|Clause|Article)\s+\d+(?:\.\d+)*(?:\([a-z]\))?)',
]

def clean_target_label(label: str) -> str:
    """Normalizes target labels for matching (e.g. 'Section 9.2' -> '9.2', 'Article IV' -> 'ARTICLE IV')"""
    cleaned = re.sub(r'^(Section|Clause|Article)\s+', '', label, flags=re.IGNORECASE).strip()
    return cleaned

def build_cross_reference_graph(doc_id: str, clauses: List[ClauseNode]) -> List[CrossRefEdge]:
    """
    Scans clause text for cross-references, matches against known clauses,
    and returns a list of CrossRefEdge items flagging dangling references.
    """
    edges: List[CrossRefEdge] = []
    
    # Map clause numbers & titles for fast resolution
    clause_num_map: Dict[str, str] = {}
    for c in clauses:
        num = c.clause_number.strip().lower()
        clause_num_map[num] = c.id
        # Also map stripped prefix if any (e.g., '1.1' from 'Section 1.1')
        num_clean = re.sub(r'^(Section|Clause|Article)\s+', '', num, flags=re.IGNORECASE)
        clause_num_map[num_clean] = c.id

    edge_counter = 0
    for clause in clauses:
        text = clause.text
        found_matches = []
        for pattern in CROSSREF_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for m in matches:
                if isinstance(m, tuple):
                    m = m[0]
                if m and m not in found_matches:
                    found_matches.append(m)

        for match_text in found_matches:
            target_clean = clean_target_label(match_text).lower()
            
            # Resolve target clause ID
            to_clause_id = clause_num_map.get(target_clean)
            is_dangling = to_clause_id is None
            
            # Don't self-reference identical clause number string
            if target_clean == clause.clause_number.lower():
                continue

            edge_counter += 1
            edges.append(CrossRefEdge(
                id=f"{doc_id}_ref_{edge_counter}",
                document_id=doc_id,
                from_clause_id=clause.id,
                from_clause_number=clause.clause_number,
                target_label=match_text,
                to_clause_id=to_clause_id,
                reference_text=match_text,
                is_dangling=is_dangling
            ))

    return edges
