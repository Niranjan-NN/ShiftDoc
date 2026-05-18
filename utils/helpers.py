"""
utils/helpers.py
----------------
Shared utility functions used across the project.
"""

import json
import re
from datetime import datetime


def build_report(
    file_name: str,
    parsed_data: dict,
    metrics: dict,
    ai_result: dict,
    score_result: dict
) -> dict:
    """
    Assemble the final JSON report from all analysis stages.

    Args:
        file_name:   Original uploaded filename
        parsed_data: Output from parser
        metrics:     Output from metrics.py
        ai_result:   Output from ai_analysis.py
        score_result: Output from scoring.py

    Returns:
        A complete report dict ready for JSON serialization
    """
    return {
        # ── Identity ──────────────────────────────────────────────────────
        "document_name":       file_name,
        "analysis_timestamp":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

        # ── Quantitative metrics ──────────────────────────────────────────
        "pages":               metrics.get("total_pages", 1),
        "word_count":          metrics.get("word_count", 0),
        "char_count":          metrics.get("char_count", 0),
        "paragraphs":          metrics.get("para_count", 0),
        "headings":            metrics.get("heading_count", 0),
        "avg_words_per_para":  metrics.get("avg_words_per_para", 0),
        "reading_time_min":    metrics.get("reading_time_minutes", 1),
        "long_para_count":     metrics.get("long_para_count", 0),
        "duplicate_headings":  metrics.get("duplicate_headings", []),
        "empty_sections":      metrics.get("empty_sections", []),

        # ── AI qualitative ratings ─────────────────────────────────────────
        "readability":            ai_result.get("readability_level", "Unknown"),
        "content_clarity":        ai_result.get("content_clarity", "Unknown"),
        "structural_consistency": ai_result.get("structural_consistency", "Unknown"),
        "documentation_quality":  ai_result.get("documentation_quality", "Unknown"),
        "content_reusability":    ai_result.get("content_reusability", "Unknown"),
        "risk_level":             ai_result.get("risk_level", "Unknown"),
        "ai_powered":             ai_result.get("ai_powered", False),

        # ── Migration decision ────────────────────────────────────────────
        "migration_score":      score_result.get("score", 0),
        "migration_readiness":  score_result.get("band", "Unknown"),
        "score_breakdown":      score_result.get("breakdown", {}),

        # ── Actionable items ──────────────────────────────────────────────
        "pain_points":      ai_result.get("pain_points", []),
        "recommendations":  ai_result.get("recommendations", []),
        "ai_summary":       ai_result.get("ai_summary", ""),
    }


def report_to_json_string(report: dict) -> str:
    """Convert a report dict to a pretty-printed JSON string."""
    return json.dumps(report, indent=2, ensure_ascii=False)


def sanitize_filename(name: str) -> str:
    """Remove unsafe characters from a filename."""
    return re.sub(r"[^\w\-_\. ]", "_", name)


def rating_color(value: str) -> str:
    """
    Return a hex color for a rating string.
    Used for coloring metric cards in the UI.
    """
    high_green  = {"High", "Easy", "Low"}       # Low risk → green
    med_yellow  = {"Medium"}
    low_red     = {"Low", "Complex", "High"}     # High risk → red

    # "Low" is ambiguous (good for risk, bad for quality), handled by caller
    color_map = {
        "High":    "#27ae60",   # green
        "Medium":  "#f39c12",   # amber
        "Low":     "#e74c3c",   # red  (for quality metrics)
        "Easy":    "#27ae60",
        "Complex": "#e74c3c",
    }
    return color_map.get(value, "#7f8c8d")


def risk_color(risk: str) -> str:
    """Special handler for risk level where Low = good (green)."""
    return {
        "Low":    "#27ae60",
        "Medium": "#f39c12",
        "High":   "#e74c3c",
    }.get(risk, "#7f8c8d")