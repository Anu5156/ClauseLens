import pymupdf as fitz
from typing import List, Dict, Any

class PDFSpanBlock:
    def __init__(self, text: str, page: int, bbox: List[float], char_start: int, char_end: int):
        self.text = text
        self.page = page
        self.bbox = bbox  # [x0, y0, x1, y1]
        self.char_start = char_start
        self.char_end = char_end

def parse_pdf_spans(file_path: str) -> tuple[str, List[Dict[str, Any]], int]:
    """
    Parses a PDF file using PyMuPDF (fitz).
    Returns (raw_text, line_blocks, page_count).
    Each line_block has text, page, bbox, char_start, char_end.
    """
    doc = fitz.open(file_path)
    full_text = ""
    blocks = []
    current_char_offset = 0

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

    page_count = len(doc)
    doc.close()
    return full_text, blocks, page_count
