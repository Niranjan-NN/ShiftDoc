"""
analysis/metrics.py
--------------------
Calculates all document metrics from parsed data.
No AI needed here — pure Python logic.
"""

import re
from collections import Counter


def calculate_metrics(parsed_data: dict) -> dict:
    """
    Generate all quantitative metrics from parsed document data.

    Args:
        parsed_data: The dict returned by docx_parser or pdf_parser

    Returns:
        dict with all computed metrics
    """
    headings   = parsed_data.get("headings", [])
    paragraphs = parsed_data.get("paragraphs", [])
    raw_text   = parsed_data.get("raw_text", "")
    word_count = parsed_data.get("word_count", 0)
    char_count = parsed_data.get("char_count", 0)
    pages      = parsed_data.get("page_estimate", parsed_data.get("page_count", 1))

    # ── Basic counts ──────────────────────────────────────────────────────
    heading_count = len(headings)
    para_count    = len(paragraphs)

    # ── Reading time ──────────────────────────────────────────────────────
    # Average adult reads ~238 words per minute
    reading_time_minutes = max(1, round(word_count / 238))

    # ── Average words per paragraph ───────────────────────────────────────
    if para_count > 0:
        para_word_counts = [len(p.split()) for p in paragraphs]
        avg_words_per_para = round(sum(para_word_counts) / para_count, 1)
    else:
        para_word_counts = []
        avg_words_per_para = 0

    # ── Long paragraph detection ──────────────────────────────────────────
    # A paragraph with more than 150 words is considered "long"
    LONG_PARA_THRESHOLD = 150
    long_paragraphs = [
        p for p in paragraphs if len(p.split()) > LONG_PARA_THRESHOLD
    ]
    long_para_count = len(long_paragraphs)

    # ── Duplicate heading detection ───────────────────────────────────────
    heading_texts = [h["text"].lower().strip() for h in headings]
    heading_freq  = Counter(heading_texts)
    duplicate_headings = [
        text for text, count in heading_freq.items() if count > 1
    ]

    # ── Empty section detection ───────────────────────────────────────────
    # A "section" is considered empty if a heading is not followed by any paragraph.
    # We detect this by checking if two consecutive headings appear without paragraphs
    # in between (simple heuristic using the raw text structure).
    empty_sections = _detect_empty_sections(raw_text, headings)

    # ── Short document warning ────────────────────────────────────────────
    is_very_short = word_count < 200

    return {
        "total_pages":           pages,
        "word_count":            word_count,
        "char_count":            char_count,
        "para_count":            para_count,
        "heading_count":         heading_count,
        "avg_words_per_para":    avg_words_per_para,
        "reading_time_minutes":  reading_time_minutes,
        "long_para_count":       long_para_count,
        "long_paragraphs":       long_paragraphs[:3],   # Show max 3 examples
        "duplicate_headings":    duplicate_headings,
        "empty_sections":        empty_sections,
        "is_very_short":         is_very_short,
        "para_word_counts":      para_word_counts,
    }


def _detect_empty_sections(raw_text: str, headings: list) -> list:
    """
    Detect headings that appear to have no content beneath them.
    Strategy: check if two heading texts appear back-to-back with only
    whitespace/newlines between them.
    """
    empty = []
    if len(headings) < 2:
        return empty

    for i in range(len(headings) - 1):
        current_heading = re.escape(headings[i]["text"])
        next_heading    = re.escape(headings[i + 1]["text"])

        # Pattern: current heading → optional whitespace → next heading (nothing in between)
        pattern = rf"{current_heading}\s*\n\s*{next_heading}"
        if re.search(pattern, raw_text, re.IGNORECASE):
            empty.append(headings[i]["text"])

    return empty