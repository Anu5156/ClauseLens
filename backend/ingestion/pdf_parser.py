from __future__ import annotations

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PDFSpanBlock:
    def __init__(self, text: str, page: int, bbox: List[float], char_start: int, char_end: int):
        self.text = text
        self.page = page
        self.bbox = bbox  # [x0, y0, x1, y1]
        self.char_start = char_start
        self.char_end = char_end

def parse_pdf_spans(file_path: str) -> tuple[str, List[Dict[str, Any]], int]:
    """
    Parses a PDF file using PyMuPDF (fitz) if available, with pypdf fallback.
    Returns (raw_text, line_blocks, page_count).
    Each line_block has text, page, bbox, char_start, char_end.
    """
    fitz = None
    try:
        import pymupdf as fitz
    except Exception:
        try:
            import fitz
        except Exception:
            fitz = None

    if fitz is not None:
        full_text = ""
        blocks = []
        current_char_offset = 0

        with fitz.open(file_path) as doc:
            page_count = len(doc)

        for page_num, page in enumerate(doc, start=1):
            # Extract page layout dictionary
            page_dict = page.get_text("dict")
            for block in page_dict.get("blocks", []):
                if block.get("type") != 0:  # 0 is text block
                    continue
                for line in block.get("lines", []):
                    line_text = ""
                    line_bbox = list(line.get("bbox", [0, 0, 0, 0]))
                    for span in line.get("spans", []):
                        line_text += span.get("text", "")
                    
                    stripped = line_text.strip()
                    if not stripped:
                        continue

                    char_start = current_char_offset
                    char_end = current_char_offset + len(line_text)
                    
                    blocks.append({
                        "text": stripped,
                        "raw_line": line_text,
                        "page": page_num,
                        "bbox": [round(c, 2) for c in line_bbox],
                        "char_start": char_start,
                        "char_end": char_end
                    })
                    
                    full_text += line_text + "\n"
                    current_char_offset += len(line_text) + 1

        return full_text, blocks, page_count

    # Pure Python fallback using pypdf
    logger.info("fitz unavailable, using pypdf fallback for PDF parsing")
    from pypdf import PdfReader
    reader = PdfReader(file_path)
    page_count = len(reader.pages)
    full_text = ""
    blocks = []
    current_char_offset = 0

    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        for line in page_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            char_start = current_char_offset
            char_end = current_char_offset + len(line)
            blocks.append({
                "text": stripped,
                "raw_line": line,
                "page": page_num,
                "bbox": [54.0, 54.0, 500.0, 700.0],
                "char_start": char_start,
                "char_end": char_end
            })
            full_text += line + "\n"
            current_char_offset += len(line) + 1

    return full_text, blocks, page_count

