import docx
from typing import List, Dict, Any

def parse_docx_spans(file_path: str) -> tuple[str, List[Dict[str, Any]], int]:
    """
    Parses a DOCX file using python-docx.
    Returns (raw_text, line_blocks, estimated_pages).
    """
    doc = docx.Document(file_path)
    full_text = ""
    blocks = []
    current_char_offset = 0
    y_offset = 54.0
    page_num = 1
    lines_on_page = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue

        char_start = current_char_offset
        char_end = current_char_offset + len(text)
        
        # Estimate page boundaries (approx 35 paragraphs/lines per page)
        lines_on_page += 1
        if lines_on_page > 35:
            page_num += 1
            lines_on_page = 1
            y_offset = 54.0

        bbox = [54.0, round(y_offset, 2), 558.0, round(y_offset + 16.0, 2)]
        y_offset += 20.0

        blocks.append({
            "text": text,
            "raw_line": para.text,
            "page": page_num,
            "bbox": bbox,
            "char_start": char_start,
            "char_end": char_end
        })

        full_text += text + "\n"
        current_char_offset += len(text) + 1

    return full_text, blocks, page_num
