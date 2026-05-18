"""
parser/pdf_parser.py
--------------------
Handles extraction of content from .pdf files using pdfplumber (primary)
with PyPDF2 as a fallback.
"""

import re
from typing import Tuple, List, Any

# ─────────────────────────────────────────────────────────────
# Initialize first (Fixes Pylance warnings)
# ─────────────────────────────────────────────────────────────
pdfplumber: Any = None
PdfReader: Any = None

PDFPLUMBER_AVAILABLE = False
PYPDF2_AVAILABLE = False

# ─────────────────────────────────────────────────────────────
# pdfplumber import
# ─────────────────────────────────────────────────────────────
try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    pass

# ─────────────────────────────────────────────────────────────
# PyPDF2 import
# ─────────────────────────────────────────────────────────────
try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
except ImportError:
    pass


def _looks_like_heading(line: str) -> bool:
    """
    Heuristic to detect if a line is likely a heading.
    Rules: short line (< 80 chars), starts with capital, no period at end,
           or looks like a numbered section (1.2 Introduction).
    """
    line = line.strip()
    if not line:
        return False

    is_short = len(line) < 80
    starts_capital = line[0].isupper()
    no_period_end = not line.endswith(".")
    numbered = bool(re.match(r"^\d+(\.\d+)*\s+\w", line))  # e.g. "1.2 Overview"
    all_caps = line.isupper() and len(line) > 3

    return (is_short and starts_capital and no_period_end) or numbered or all_caps


def _extract_with_pdfplumber(file) -> Tuple[int, List[str]]:
    """Use pdfplumber to extract text page by page."""
    pages_text = []

    if pdfplumber is None:
        raise ImportError("pdfplumber is not installed")

    with pdfplumber.open(file) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)

    return page_count, pages_text


def _extract_with_pypdf2(file) -> Tuple[int, List[str]]:
    """Fallback: use PyPDF2 to extract text."""
    if PdfReader is None:
        raise ImportError("PyPDF2 is not installed")

    reader = PdfReader(file)
    page_count = len(reader.pages)
    pages_text = []

    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages_text.append(text)

    return page_count, pages_text


def parse_pdf(file) -> dict:
    """
    Parse a .pdf file and extract structured content.

    Args:
        file: A file-like object from Streamlit's file_uploader

    Returns:
        dict with keys: headings, paragraphs, raw_text, word_count,
                        char_count, page_count, heading_count, para_count
    """
    page_count = 0
    pages_text = []

    # Try pdfplumber first; fall back to PyPDF2
    try:
        if PDFPLUMBER_AVAILABLE:
            page_count, pages_text = _extract_with_pdfplumber(file)
        elif PYPDF2_AVAILABLE:
            page_count, pages_text = _extract_with_pypdf2(file)
        else:
            return {"error": "No PDF library available. Install pdfplumber or PyPDF2."}
    except Exception as e:
        # If pdfplumber fails, try PyPDF2
        try:
            if PYPDF2_AVAILABLE:
                file.seek(0)  # Reset file pointer
                page_count, pages_text = _extract_with_pypdf2(file)
            else:
                return {"error": f"PDF parsing failed: {str(e)}"}
        except Exception as e2:
            return {"error": f"Both PDF parsers failed: {str(e2)}"}

    # ── Process extracted text ─────────────────────────────────────────────
    raw_text = "\n".join(pages_text)
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

    headings = []
    paragraphs = []

    # Group lines into paragraphs and detect headings
    current_para_lines = []

    for line in lines:
        if _looks_like_heading(line):
            # Save any accumulated paragraph first
            if current_para_lines:
                para_text = " ".join(current_para_lines)
                paragraphs.append(para_text)
                current_para_lines = []
            headings.append({
                "level": "Detected Heading",
                "text": line
            })
        else:
            current_para_lines.append(line)
            # If line ends with a period, treat accumulated lines as one paragraph
            if line.endswith(".") or line.endswith("?") or line.endswith("!"):
                para_text = " ".join(current_para_lines)
                paragraphs.append(para_text)
                current_para_lines = []

    # Flush remaining lines as a paragraph
    if current_para_lines:
        paragraphs.append(" ".join(current_para_lines))

    words = raw_text.split()
    word_count = len(words)
    char_count = len(raw_text)

    return {
        "headings": headings,
        "paragraphs": [p for p in paragraphs if p.strip()],
        "raw_text": raw_text,
        "word_count": word_count,
        "char_count": char_count,
        "page_count": page_count,
        "page_estimate": page_count,
        "heading_count": len(headings),
        "para_count": len([p for p in paragraphs if p.strip()]),
        "error": None
    }