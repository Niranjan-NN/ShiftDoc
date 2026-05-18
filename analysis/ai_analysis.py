"""
analysis/ai_analysis.py
-----------------------
Uses Gemini API to generate qualitative analysis of the document.
Returns structured ratings, pain points, and recommendations.

FIX NOTES (Pylance errors resolved):
- All import variables pre-initialized to None before try/except blocks.
  This tells Pylance the names are ALWAYS bound, never "possibly unbound".
- Every usage site guards with `is not None` before calling methods,
  so Pylance won't complain about "strip is not a known attribute of None".
- type: ignore comments suppress the stubs-missing warnings for
  google packages that don't ship full type stubs.
"""

import json
import re
from typing import Optional, Any

# ── Pre-initialize BEFORE try/except ─────────────────────────────────────────
# Pylance error "possibly unbound" happens because if the import fails,
# the variable was never assigned. Setting to None first guarantees the
# name is always defined in this module's scope.

new_genai: Optional[Any] = None    # google-genai >= 1.0 (new SDK)
legacy_genai: Optional[Any] = None # google-generativeai (old SDK)

USE_NEW_SDK = False
USE_LEGACY_SDK = False

try:
    from google import genai as _new_genai          # type: ignore[attr-defined]
    new_genai = _new_genai
    USE_NEW_SDK = True
except ImportError:
    pass  # new_genai stays None — guarded before every use below

try:
    import google.generativeai as _legacy_genai     # type: ignore[import-untyped]
    legacy_genai = _legacy_genai
    USE_LEGACY_SDK = True
except ImportError:
    pass  # legacy_genai stays None — guarded before every use below


# ── Prompt template ───────────────────────────────────────────────────────────
ANALYSIS_PROMPT = """
You are a Migration Specialist expert analyzing a document for platform migration readiness (e.g., migrating to Document360 or similar knowledge base platforms).

Analyze the following document content and metrics, then return a JSON response ONLY (no markdown, no explanation text).

--- DOCUMENT CONTENT SAMPLE (first 3000 characters) ---
{content_sample}

--- DOCUMENT METRICS ---
- Total Pages: {pages}
- Word Count: {word_count}
- Paragraph Count: {para_count}
- Heading Count: {heading_count}
- Average Words Per Paragraph: {avg_words_per_para}
- Long Paragraphs Detected: {long_para_count}
- Duplicate Headings Found: {duplicate_headings}
- Empty Sections Found: {empty_sections}

Return ONLY a valid JSON object with this exact structure:
{{
  "readability_level": "Easy" or "Medium" or "Complex",
  "content_clarity": "High" or "Medium" or "Low",
  "structural_consistency": "High" or "Medium" or "Low",
  "migration_readiness": "Migration Ready" or "Needs Improvement" or "Not Ready",
  "documentation_quality": "High" or "Medium" or "Low",
  "content_reusability": "High" or "Medium" or "Low",
  "risk_level": "Low" or "Medium" or "High",
  "pain_points": [
    "string describing pain point 1",
    "string describing pain point 2"
  ],
  "recommendations": [
    "string describing recommendation 1",
    "string describing recommendation 2"
  ],
  "ai_summary": "A 2-3 sentence professional summary of the document's migration readiness."
}}
"""


def _call_new_sdk(api_key: str, prompt: str) -> str:
    """
    Call the new google-genai SDK (>= 1.0).
    Isolated into its own function so Pylance can narrow the type:
    the `assert` below proves to the type checker that new_genai is not None
    inside this function's scope.
    """
    assert new_genai is not None, "new_genai SDK not available"
    client = new_genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    raw: Optional[str] = response.text
    return raw.strip() if raw is not None else ""


def _call_legacy_sdk(api_key: str, prompt: str) -> str:
    """
    Call the legacy google-generativeai SDK.
    Isolated so Pylance can narrow legacy_genai to non-None via assert.
    """
    assert legacy_genai is not None, "legacy_genai SDK not available"
    legacy_genai.configure(api_key=api_key)
    model = legacy_genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    raw: Optional[str] = response.text
    return raw.strip() if raw is not None else ""


def run_ai_analysis(parsed_data: dict, metrics: dict, api_key: str) -> dict:
    """
    Send document data to Gemini and get back qualitative analysis.

    Args:
        parsed_data: Output from the document parser
        metrics:     Output from metrics.py
        api_key:     Gemini API key entered by the user in the sidebar

    Returns:
        dict with AI-generated analysis fields, or fallback rule-based result
    """
    if not api_key or not api_key.strip():
        return _fallback_analysis(metrics)

    clean_key = api_key.strip()

    try:
        raw_text = parsed_data.get("raw_text", "")
        content_sample = raw_text[:3000]

        prompt = ANALYSIS_PROMPT.format(
            content_sample     = content_sample,
            pages              = metrics.get("total_pages", 1),
            word_count         = metrics.get("word_count", 0),
            para_count         = metrics.get("para_count", 0),
            heading_count      = metrics.get("heading_count", 0),
            avg_words_per_para = metrics.get("avg_words_per_para", 0),
            long_para_count    = metrics.get("long_para_count", 0),
            duplicate_headings = metrics.get("duplicate_headings", []),
            empty_sections     = metrics.get("empty_sections", []),
        )

        # ── Choose SDK ─────────────────────────────────────────────────────
        # Guard with `is not None` so Pylance sees the variable is safe to use.
        # The helper functions further narrow via assert for extra safety.
        if USE_NEW_SDK and new_genai is not None:
            response_text = _call_new_sdk(clean_key, prompt)
        elif USE_LEGACY_SDK and legacy_genai is not None:
            response_text = _call_legacy_sdk(clean_key, prompt)
        else:
            raise ImportError(
                "No Gemini SDK found. Install with: pip install google-genai"
            )

        # Strip markdown fences Gemini sometimes adds despite the prompt
        response_text = re.sub(r"```json|```", "", response_text).strip()

        result: dict = json.loads(response_text)
        result["ai_powered"] = True
        return result

    except json.JSONDecodeError as e:
        return {
            **_fallback_analysis(metrics),
            "ai_powered": False,
            "ai_error": f"Could not parse AI response as JSON: {e}",
        }
    except Exception as e:
        return {
            **_fallback_analysis(metrics),
            "ai_powered": False,
            "ai_error": f"AI analysis failed: {e}",
        }


def _fallback_analysis(metrics: dict) -> dict:
    """
    Rule-based fallback when no API key is provided or the API call fails.
    Derives all ratings purely from document metrics — no AI needed.
    """
    word_count      = metrics.get("word_count", 0)
    heading_count   = metrics.get("heading_count", 0)
    para_count      = metrics.get("para_count", 0)
    long_para_count = metrics.get("long_para_count", 0)
    duplicates      = metrics.get("duplicate_headings", [])
    empty_sections  = metrics.get("empty_sections", [])
    avg_words       = metrics.get("avg_words_per_para", 0)

    pain_points: list = []
    recommendations: list = []

    # ── Build pain points list ─────────────────────────────────────────────
    if long_para_count > 0:
        pain_points.append(f"{long_para_count} long paragraph(s) detected (>150 words each)")
        recommendations.append("Break long paragraphs into smaller, focused sections")

    if duplicates:
        pain_points.append(f"Duplicate headings found: {', '.join(duplicates[:3])}")
        recommendations.append("Remove or rename duplicate headings for clarity")

    if empty_sections:
        pain_points.append(f"{len(empty_sections)} empty section(s) with no content")
        recommendations.append("Add content to empty sections or remove them")

    if heading_count == 0:
        pain_points.append("No headings detected — document lacks structure")
        recommendations.append("Add a proper heading hierarchy (H1, H2, H3)")

    if word_count < 200:
        pain_points.append("Document is very short; may lack sufficient content")
        recommendations.append("Expand document content with more detail")

    if avg_words > 120:
        pain_points.append("Average paragraph length is high — readability may suffer")
        recommendations.append("Aim for paragraphs of 50–100 words for better readability")

    if not pain_points:
        pain_points.append("No major structural issues detected")

    if not recommendations:
        recommendations.append("Document structure looks acceptable for migration")

    # ── Derive quality ratings ─────────────────────────────────────────────
    structure_ok = heading_count > 0 and not empty_sections

    if avg_words < 80 and heading_count > 2:
        readability = "Easy"
    elif avg_words > 150 or heading_count == 0:
        readability = "Complex"
    else:
        readability = "Medium"

    if len(pain_points) >= 4 or heading_count == 0:
        risk_level = "High"
    elif len(pain_points) >= 2:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    content_clarity        = "High" if heading_count > 3 and not duplicates else "Medium"
    structural_consistency = "High" if structure_ok else "Low"
    content_reusability    = "High" if heading_count > 5 else "Medium"

    summary = (
        f"This document contains {word_count} words across {para_count} paragraphs. "
        f"The structural analysis (rule-based) suggests a {risk_level.lower()} risk level "
        f"for migration. Provide your Gemini API key for a more detailed AI analysis."
    )

    return {
        "readability_level":       readability,
        "content_clarity":         content_clarity,
        "structural_consistency":  structural_consistency,
        "migration_readiness":     "Needs Improvement" if risk_level != "Low" else "Migration Ready",
        "documentation_quality":   "Medium",
        "content_reusability":     content_reusability,
        "risk_level":              risk_level,
        "pain_points":             pain_points,
        "recommendations":         recommendations,
        "ai_summary":              summary,
        "ai_powered":              False,
    }
