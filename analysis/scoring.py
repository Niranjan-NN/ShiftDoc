"""
analysis/scoring.py
-------------------
Calculates the final Migration Readiness Score (0–100).
Combines metrics-based deductions with AI analysis results.

Score bands:
  0–40  → Not Ready
  41–70 → Needs Improvement
  71–100 → Migration Ready
"""


def calculate_score(metrics: dict, ai_result: dict) -> dict:
    """
    Compute a 0–100 migration readiness score.

    We start at 100 and subtract points for detected problems.
    This makes the scoring logic easy to read and debug.

    Args:
        metrics:   Output from metrics.py
        ai_result: Output from ai_analysis.py

    Returns:
        dict with score (int), band (str), and breakdown (dict)
    """
    score = 100
    breakdown = {}  # Records why points were deducted (for transparency)

    # ── Metrics-based deductions ──────────────────────────────────────────

    # 1. No headings at all → big structural problem
    heading_count = metrics.get("heading_count", 0)
    if heading_count == 0:
        deduction = 25
        score -= deduction
        breakdown["no_headings"] = f"-{deduction} pts: No headings found"
    elif heading_count < 3:
        deduction = 10
        score -= deduction
        breakdown["few_headings"] = f"-{deduction} pts: Very few headings ({heading_count})"

    # 2. Long paragraphs (each long para costs some points, capped)
    long_para_count = metrics.get("long_para_count", 0)
    if long_para_count > 0:
        deduction = min(long_para_count * 3, 15)  # max 15 pts
        score -= deduction
        breakdown["long_paragraphs"] = f"-{deduction} pts: {long_para_count} long paragraph(s)"

    # 3. Duplicate headings (confuses navigation in knowledge bases)
    duplicates = metrics.get("duplicate_headings", [])
    if duplicates:
        deduction = min(len(duplicates) * 5, 15)
        score -= deduction
        breakdown["duplicate_headings"] = f"-{deduction} pts: {len(duplicates)} duplicate heading(s)"

    # 4. Empty sections
    empty_sections = metrics.get("empty_sections", [])
    if empty_sections:
        deduction = min(len(empty_sections) * 4, 12)
        score -= deduction
        breakdown["empty_sections"] = f"-{deduction} pts: {len(empty_sections)} empty section(s)"

    # 5. Very short document
    if metrics.get("is_very_short", False):
        deduction = 10
        score -= deduction
        breakdown["short_doc"] = f"-{deduction} pts: Document is very short (<200 words)"

    # ── AI-based deductions ───────────────────────────────────────────────

    # 6. Risk level from AI
    risk_level = ai_result.get("risk_level", "Low")
    if risk_level == "High":
        deduction = 20
        score -= deduction
        breakdown["high_risk"] = f"-{deduction} pts: AI flagged High risk level"
    elif risk_level == "Medium":
        deduction = 10
        score -= deduction
        breakdown["medium_risk"] = f"-{deduction} pts: AI flagged Medium risk level"

    # 7. Structural consistency from AI
    structural = ai_result.get("structural_consistency", "High")
    if structural == "Low":
        deduction = 10
        score -= deduction
        breakdown["low_structure"] = f"-{deduction} pts: Low structural consistency"
    elif structural == "Medium":
        deduction = 5
        score -= deduction
        breakdown["med_structure"] = f"-{deduction} pts: Medium structural consistency"

    # 8. Content clarity from AI
    clarity = ai_result.get("content_clarity", "High")
    if clarity == "Low":
        deduction = 8
        score -= deduction
        breakdown["low_clarity"] = f"-{deduction} pts: Low content clarity"

    # ── Clamp score to valid range ────────────────────────────────────────
    score = max(0, min(100, score))

    # ── Determine band ────────────────────────────────────────────────────
    if score <= 40:
        band = "Not Ready"
        band_color = "#e74c3c"   # Red
        band_emoji = "🔴"
    elif score <= 70:
        band = "Needs Improvement"
        band_color = "#f39c12"   # Orange
        band_emoji = "🟡"
    else:
        band = "Migration Ready"
        band_color = "#27ae60"   # Green
        band_emoji = "🟢"

    return {
        "score":       score,
        "band":        band,
        "band_color":  band_color,
        "band_emoji":  band_emoji,
        "breakdown":   breakdown,
    }