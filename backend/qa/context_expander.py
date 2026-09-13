from typing import List, Dict, Set, Any
from backend.models import ClauseNode, DocumentParsed, DefinedTerm

def expand_clause_context(
    target_clauses: List[ClauseNode],
    doc: DocumentParsed
) -> Dict[str, Any]:
    """
    Expands candidate clauses with:
    - Parent hierarchy nodes
    - Cross-referenced target clauses
    - Applicable defined terms from doc.definitions
    """
    clause_map: Dict[str, ClauseNode] = {c.id: c for c in doc.clauses}
    
    expanded_clause_ids: Set[str] = set()
    parent_clauses: List[ClauseNode] = []
    crossref_clauses: List[ClauseNode] = []
    applicable_definitions: List[DefinedTerm] = []

    # Map of cross-references by from_clause_id
    crossref_map = {}
    for ref in doc.crossrefs:
        crossref_map.setdefault(ref.from_clause_id, []).append(ref)

    for c in target_clauses:
        expanded_clause_ids.add(c.id)

        # 1. Expand parent
        if c.parent_id and c.parent_id in clause_map:
            parent = clause_map[c.parent_id]
            if parent.id not in expanded_clause_ids:
                expanded_clause_ids.add(parent.id)
                parent_clauses.append(parent)

        # 2. Expand cross-references
        refs = crossref_map.get(c.id, [])
        for ref in refs:
            if ref.to_clause_id and ref.to_clause_id in clause_map:
                target_node = clause_map[ref.to_clause_id]
                if target_node.id not in expanded_clause_ids:
                    expanded_clause_ids.add(target_node.id)
                    crossref_clauses.append(target_node)

        # 3. Expand applicable definitions
        clause_text_lower = (c.title + " " + c.text).lower()
        for def_item in doc.definitions:
            if def_item.term.lower() in clause_text_lower:
                if def_item not in applicable_definitions:
                    applicable_definitions.append(def_item)

    return {
        "primary_clauses": target_clauses,
        "parent_clauses": parent_clauses,
        "crossref_clauses": crossref_clauses,
        "definitions": applicable_definitions,
        "all_expanded_ids": list(expanded_clause_ids)
    }
