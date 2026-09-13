import re
from typing import List, Dict, Any, Optional
from backend.models import ClauseNode, SpanLocation

# Regex patterns for common legal document numbering styles
PATTERNS = [
    # Article: ARTICLE IV, ARTICLE 1
    (r'^(ARTICLE\s+[IVXLCDM\d]+)[\.\:\s]*(.*)$', 1),
    # Section major: Section 3, Section 3.1, SECTION 4 (must be standalone heading or followed by Title)
    (r'^(SECTION\s+\d+(?:\.\d+)*)\.?\s+([A-Z0-9\s\,\-\(\)\'\"]{2,})$', 1),
    # Top-level numbered section: 1. RENT AND DEPOSIT, 2. TERMINATION
    (r'^(\d+)\.\s+([A-Z0-9\s\,\-\(\)\'\"]{2,})$', 1),
    # Decimal numbered section: 1.1, 1.1.1, 2.3.4 (followed by title or text)
    (r'^(\d+\.\d+(?:\.\d+)*)[\.\:\s]*(.*)$', 2),
    # Subclause letter: (a), (b), a., b.
    (r'^(\([a-z]\)|[a-z]\.)[\.\:\s]*(.*)$', 3),
    # Subclause roman: (i), (ii), (iii), i., ii.
    (r'^(\([ivx]+\)|[ivx]+\.)[\.\:\s]*(.*)$', 4),
]

def parse_clause_hierarchy(doc_id: str, line_blocks: List[Dict[str, Any]]) -> List[ClauseNode]:
    """
    Parses line blocks into a hierarchical list of ClauseNode objects.
    """
    clauses: List[ClauseNode] = []
    current_clause: Optional[Dict[str, Any]] = None
    order_index = 0

    def match_heading(line: str):
        line_clean = line.strip()
        for pattern, level in PATTERNS:
            match = re.match(pattern, line_clean, re.IGNORECASE)
            if match:
                num = match.group(1).strip()
                rest = match.group(2).strip() if match.lastindex >= 2 else ""
                title = rest if rest else num
                return num, title, level
        return None

    for block in line_blocks:
        text = block["text"]
        matched = match_heading(text)
        
        span = SpanLocation(
            page=block["page"],
            bbox=block["bbox"],
            char_start=block["char_start"],
            char_end=block["char_end"]
        )

        if matched:
            clause_num, title, level = matched
            
            # Save previous clause if active
            if current_clause:
                clauses.append(ClauseNode(
                    id=f"{doc_id}_clause_{len(clauses)+1}",
                    document_id=doc_id,
                    clause_number=current_clause["number"],
                    title=current_clause["title"],
                    text=current_clause["text"].strip(),
                    level=current_clause["level"],
                    parent_id=None,
                    children_ids=[],
                    spans=current_clause["spans"],
                    order_index=current_clause["order_index"]
                ))
            
            order_index += 1
            current_clause = {
                "number": clause_num,
                "title": title if title else clause_num,
                "text": text,
                "level": level,
                "spans": [span],
                "order_index": order_index
            }
        else:
            if current_clause:
                current_clause["text"] += "\n" + text
                current_clause["spans"].append(span)
            else:
                # Preamble / Unnumbered top header
                order_index += 1
                current_clause = {
                    "number": "Preamble",
                    "title": "Document Title / Preamble",
                    "text": text,
                    "level": 1,
                    "spans": [span],
                    "order_index": order_index
                }

    if current_clause:
        clauses.append(ClauseNode(
            id=f"{doc_id}_clause_{len(clauses)+1}",
            document_id=doc_id,
            clause_number=current_clause["number"],
            title=current_clause["title"],
            text=current_clause["text"].strip(),
            level=current_clause["level"],
            parent_id=None,
            children_ids=[],
            spans=current_clause["spans"],
            order_index=current_clause["order_index"]
        ))

    # Second pass: Compute parent-child pointers based on level hierarchy
    stack: List[ClauseNode] = []
    for clause in clauses:
        while stack and stack[-1].level >= clause.level:
            stack.pop()
        
        if stack:
            clause.parent_id = stack[-1].id
            stack[-1].children_ids.append(clause.id)
            
        stack.append(clause)

    return clauses
