"""
app.py
------
Main entry point for the Document Analysis & Migration Readiness Tool.
Run with:  streamlit run app.py
"""

import sys
import os
import json
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# ── Add project root to path so imports work cleanly ─────────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser.docx_parser  import parse_docx
from parser.pdf_parser   import parse_pdf
from analysis.metrics    import calculate_metrics
from analysis.ai_analysis import run_ai_analysis
from analysis.scoring    import calculate_score
from utils.helpers       import build_report, report_to_json_string, risk_color, rating_color

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title  = "ShiftDoc — Migration Readiness Tool",
    page_icon   = "📄",
    layout      = "wide",
    initial_sidebar_state = "expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS — Clean dark-accented professional theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Google Font ── */
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght=300;400;500;600;700&family=DM+Mono:wght=400;500&display=swap');

  /* ==========================================
     1. THEME VARIABLES (DYNAMIC CORES)
     ========================================== */
  
  /* DEFAULT: LIGHT MODE CACHING */
  :root {
    --bg-gradient: radial-gradient(circle at 50% 0%, #f4f6fa 0%, #eaeef6 70%);
    --text-main: #1e293b;
    --text-muted: #64748b;
    --card-bg: rgba(255, 255, 255, 0.7);
    --card-border: rgba(226, 232, 240, 0.8);
    --card-hover-border: #4f6ef7;
    --sidebar-bg: #f8fafc;
    --sidebar-border: #e2e8f0;
    --sidebar-text: #334155;
    --header-border: rgba(226, 232, 240, 0.6);
    --header-text: #64748b;
    --code-bg: #f1f5f9;
    --code-text: #db2777;
    --tab-list-bg: #f1f5f9;
    --tab-text: #64748b;
    --score-bg: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
    --score-num-grad: linear-gradient(135deg, #0f172a 0%, #4338ca 100%);
    --issue-bg: rgba(239, 68, 68, 0.08);
    --issue-text: #991b1b;
    --rec-bg: rgba(34, 197, 94, 0.08);
    --rec-text: #166534;
  }

  /* AUTOMATIC DARK MODE ACTIVATION */
  @media (prefers-color-scheme: dark) {
    :root {
      --bg-gradient: radial-gradient(circle at 50% 0%, #1a1f36 0%, #0f1117 70%);
      --text-main: #e8eaf0;
      --text-muted: #9ca3af;
      --card-bg: rgba(26, 31, 46, 0.6);
      --card-border: rgba(42, 47, 62, 0.7);
      --card-hover-border: #4f6ef7;
      --sidebar-bg: #141822;
      --sidebar-border: #222736;
      --sidebar-text: #c1c7da;
      --header-border: rgba(42, 47, 62, 0.4);
      --header-text: #8f97b7;
      --code-bg: #222736;
      --code-text: #f472b6;
      --tab-list-bg: #141822;
      --tab-text: #8f97b7;
      --score-bg: linear-gradient(135deg, #1a1f2e 0%, #131724 100%);
      --score-num-grad: linear-gradient(135deg, #ffffff 0%, #a5b4fc 100%);
      --issue-bg: rgba(231, 76, 60, 0.1);
      --issue-text: #fbcbc7;
      --rec-bg: rgba(39, 174, 96, 0.1);
      --rec-text: #ccefdc;
    }
  }

  /* ==========================================
     2. APPLICATION COMPONENTS HANDLERS
     ========================================== */

  /* ── Base Reset & Inherited Typography ── */
  html, body, [class*="css"], .stMarkdown {
    font-family: 'DM Sans', sans-serif;
    color: var(--text-main);
  }

  /* ── App background ── */
  .stApp {
    background: var(--bg-gradient);
    color: var(--text-main);
  }

  /* ── Fix Streamlit Top Bar Header ── */
  header[data-testid="stHeader"] {
    background-color: transparent !important;
    background-image: none !important;
    border-bottom: 1px solid var(--header-border);
  }
  header[data-testid="stHeader"] * {
    color: var(--header-text) !important;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: var(--sidebar-bg);
    border-right: 1px solid var(--sidebar-border);
  }
  [data-testid="stSidebar"] * {
    color: var(--sidebar-text);
  }

  /* ── Metric cards (Glow & Glassmorphism) ── */
  .metric-card {
    background: var(--card-bg);
    backdrop-filter: blur(8px);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 14px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  }
  .metric-card:hover { 
    border-color: var(--card-hover-border);
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(79, 110, 247, 0.15);
  }
  .metric-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 8px;
  }
  .metric-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-main);
    line-height: 1.1;
  }
  .metric-sub {
    font-size: 12px;
    color: var(--text-muted);
    margin-top: 6px;
  }

  /* ── Section headers ── */
  .section-header {
    font-size: 14px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #4f6ef7;
    border-bottom: 1px solid var(--card-border);
    padding-bottom: 10px;
    margin-bottom: 20px;
  }

  /* ── Rating pill badges ── */
  .badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.04em;
    background: rgba(79, 110, 247, 0.15);
    color: #4f6ef7;
    border: 1px solid rgba(79, 110, 247, 0.25);
  }

  /* ── Pain point / recommendation items ── */
  .issue-item {
    background: var(--issue-bg);
    border-left: 4px solid #e74c3c;
    border-radius: 4px 10px 10px 4px;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-size: 14.5px;
    color: var(--issue-text);
  }
  .rec-item {
    background: var(--rec-bg);
    border-left: 4px solid #27ae60;
    border-radius: 4px 10px 10px 4px;
    padding: 12px 16px;
    margin-bottom: 10px;
    font-size: 14.5px;
    color: var(--rec-text);
  }

  /* ── Score display ── */
  .score-display {
    text-align: center;
    padding: 32px 24px;
    background: var(--score-bg);
    border-radius: 20px;
    border: 1px solid var(--card-border);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.02);
  }
  .score-number {
    font-size: 80px;
    font-weight: 800;
    line-height: 1;
    background: var(--score-num-grad);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
  .score-band {
    font-size: 20px;
    font-weight: 600;
    color: #4f6ef7;
    margin-top: 12px;
  }

  /* ── Page title ── */
  .page-title {
    font-size: 32px;
    font-weight: 700;
    color: var(--text-main);
    letter-spacing: -0.02em;
  }
  .page-subtitle {
    color: var(--text-muted);
    font-size: 15px;
    margin-top: 6px;
    margin-bottom: 24px;
  }

  /* ── Streamlit UI Elements Overrides ── */
  .stButton > button {
    background: #4f6ef7;
    color: white !important;
    border: none;
    border-radius: 10px;
    padding: 12px 28px;
    font-weight: 600;
    font-family: 'DM Sans', sans-serif;
    box-shadow: 0 4px 14px rgba(79, 110, 247, 0.3);
    transition: all 0.2s ease;
  }
  .stButton > button:hover {
    background: #3a5ae0;
    box-shadow: 0 6px 20px rgba(79, 110, 247, 0.4);
    transform: translateY(-1px);
  }

  div[data-testid="stExpander"] {
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
  }

  .stTabs [data-baseweb="tab-list"] {
    background: var(--tab-list-bg);
    border-radius: 12px;
    padding: 6px;
    gap: 6px;
  }
  .stTabs [data-baseweb="tab"] {
    color: var(--tab-text);
    font-weight: 600;
    padding: 10px 16px;
    border-radius: 8px;
  }
  .stTabs [aria-selected="true"] {
    background: #4f6ef7 !important;
    color: white !important;
  }

  code { 
    font-family: 'DM Mono', monospace; 
    background: var(--code-bg);
    color: var(--code-text);
    padding: 2px 6px;
    border-radius: 4px;
  }
</style>""",unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS (UI Rendering)
# ─────────────────────────────────────────────────────────────────────────────

def render_metric_card(label: str, value, sub: str = ""):
    """Render a styled metric card."""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {"<div class='metric-sub'>" + sub + "</div>" if sub else ""}
    </div>
    """, unsafe_allow_html=True)


def render_badge(text: str, color: str):
    """Render a colored badge."""
    return f'<span class="badge" style="background:{color}20; color:{color}; border:1px solid {color}40">{text}</span>'


def render_score_gauge(score: int, band: str, color: str, chart_key: str):
    """Render a Plotly gauge chart for the migration score."""

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,

        domain={"x": [0, 1], "y": [0, 1]},

        gauge={
            "axis": {
                "range": [0, 100],
                "tickcolor": "#000000",
                "tickfont": {"color": "#000000"}
            },

            "bar": {
                "color": color,
                "thickness": 0.25
            },

            "bgcolor": "#000000",

            "bordercolor": "#2a2f3e",

            "steps": [
                {"range": [0, 40], "color": "#2a1a1a"},
                {"range": [40, 70], "color": "#2a2a1a"},
                {"range": [70, 100], "color": "#1a2a1a"},
            ],

            "threshold": {
                "line": {
                    "color": color,
                    "width": 3
                },

                "thickness": 0.75,
                "value": score
            }
        },

        number={
            "font": {
                "size": 48,
                "color": "#000000",
                "family": "DM Sans"
            }
        }
    ))

    fig.update_layout(
        height=280,

        margin=dict(
            t=20,
            b=10,
            l=20,
            r=20
        ),

        paper_bgcolor="rgba(0,0,0,0)",

        font={
            "color": "#000000"
        }
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key=chart_key
    )

    """Render a Plotly gauge chart for the migration score."""
    fig = go.Figure(go.Indicator(
        mode  = "gauge+number",
        value = score,
        domain = {"x": [0, 1], "y": [0, 1]},
        gauge = {
            "axis":  {"range": [0, 100], "tickcolor": "#000000", "tickfont": {"color": "#000000"}},
            "bar":   {"color": color, "thickness": 0.25},
            "bgcolor": "#000000",
            "bordercolor": "#2a2f3e",
            "steps": [
                {"range": [0, 40],  "color": "#2a1a1a"},
                {"range": [40, 70], "color": "#2a2a1a"},
                {"range": [70, 100], "color": "#1a2a1a"},
            ],
            "threshold": {
                "line": {"color": color, "width": 3},
                "thickness": 0.75,
                "value": score
            }
        },
        number = {"font": {"size": 48, "color": "#000000", "family": "DM Sans"}}
    ))
    fig.update_layout(
        height    = 280,
        margin    = dict(t=20, b=10, l=20, r=20),
        paper_bgcolor = "rgba(0,0,0,0)",
        font = {"color": "#000000"},
    )
    st.plotly_chart(
    fig,
    use_container_width=True,
    key=f"score_gauge_{score}"
)


def render_rating_table(ai_result: dict):
    """Render a table of AI quality ratings."""
    ratings = {
        "Readability Level":       ai_result.get("readability_level", "—"),
        "Content Clarity":         ai_result.get("content_clarity", "—"),
        "Structural Consistency":  ai_result.get("structural_consistency", "—"),
        "Documentation Quality":   ai_result.get("documentation_quality", "—"),
        "Content Reusability":     ai_result.get("content_reusability", "—"),
        "Risk Level":              ai_result.get("risk_level", "—"),
    }

    html = '<table style="width:100%; border-collapse:collapse;">'
    html += '<tr style="border-bottom:1px solid #2a2f3e;"><th style="text-align:left; padding:8px; color:#7b82a0; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em;">Dimension</th><th style="text-align:right; padding:8px; color:#7b82a0; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.06em;">Rating</th></tr>'

    for label, value in ratings.items():
        if label == "Risk Level":
            color = risk_color(value)
        elif value in ("High", "Easy"):
            color = "#27ae60"
        elif value == "Medium":
            color = "#f39c12"
        else:
            color = "#e74c3c"

        badge = f'<span style="background:{color}20; color:{color}; border:1px solid {color}40; padding:2px 10px; border-radius:999px; font-size:12px; font-weight:600;">{value}</span>'
        html += f'<tr style="border-bottom:1px solid #1e2332;"><td style="padding:10px 8px; font-size:14px;">{label}</td><td style="text-align:right; padding:10px 8px;">{badge}</td></tr>'

    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)


def render_paragraph_distribution(para_word_counts: list):
    """Bar chart showing paragraph length distribution."""
    if not para_word_counts:
        return

    df = pd.DataFrame({
        "Paragraph": [f"P{i+1}" for i in range(len(para_word_counts))],
        "Words": para_word_counts
    })

    colors = ["#e74c3c" if w > 150 else "#4f6ef7" for w in para_word_counts]

    fig = go.Figure(go.Bar(
        x     = df["Paragraph"],
        y     = df["Words"],
        marker_color = colors,
        hovertemplate = "Para %{x}: %{y} words<extra></extra>",
    ))
    fig.add_hline(
        y=150, line_dash="dash", line_color="#f39c12",
        annotation_text="150-word threshold", annotation_font_color="#f39c12"
    )
    fig.update_layout(
        height    = 240,
        margin    = dict(t=10, b=10, l=10, r=10),
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
        xaxis = {"showticklabels": False, "gridcolor": "#2a2f3e"},
        yaxis = {"gridcolor": "#2a2f3e", "color": "#7b82a0"},
        font  = {"color": "#7b82a0"},
    )
    st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Configuration")
    st.markdown("---")

    gemini_key = st.text_input(
        "AIzaSyCrHVuFgqAWJZE_SUGlB0Y7KK6M1zHn5sc",
        type     = "password",
        help     = "Get your free key at https://aistudio.google.com/",
        placeholder = "AIza..."
    )

    if gemini_key:
        st.success(" API key provided — AI analysis enabled")
    else:
        st.info("No key? Rule-based analysis will run instead")

    st.markdown("---")
    st.markdown("### Score Guide")
    st.markdown("""
    | Score | Status |
    |-------|--------|
    | 🟢 71–100 | Migration Ready |
    | 🟡 41–70 | Needs Improvement |
    | 🔴 0–40 | Not Ready |
    """)

    st.markdown("---")
    st.markdown("### Supported Files")
    st.markdown("- `.docx` — Word documents\n- `.pdf` — PDF documents")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────────────────────────────────────
col_title, col_badge = st.columns([3, 1])
with col_title:
    st.markdown("""
    <div class="page-title">ShiftDoc</div>
    <div class="page-subtitle">Document Analysis & Migration Readiness Tool — powered by Gemini AI</div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# FILE UPLOAD
# ─────────────────────────────────────────────────────────────────────────────
uploaded_files = st.file_uploader(
    "Upload documents to analyze",
    type           = ["docx", "pdf"],
    accept_multiple_files = True,
    help           = "Supports .docx and .pdf files. Upload one or many."
)

if not uploaded_files:
    # ── Landing / empty state ─────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center; padding:60px 20px; color:#7b82a0;">
        <div style="font-size:48px; margin-bottom:16px;">📂</div>
        <div style="font-size:16px; font-weight:500; margin-bottom:8px;">Upload a document to get started</div>
        <div style="font-size:13px;">Supports Word (.docx) and PDF (.pdf) files</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# PROCESS EACH FILE
# ─────────────────────────────────────────────────────────────────────────────
all_reports = []

for uploaded_file in uploaded_files:
    file_name = uploaded_file.name
    file_ext  = file_name.rsplit(".", 1)[-1].lower()

    st.markdown(f"---\n### `{file_name}`")

    # ── 1. PARSE ──────────────────────────────────────────────────────────
    with st.spinner(f"Parsing {file_name}..."):
        if file_ext == "docx":
            parsed = parse_docx(uploaded_file)
        elif file_ext == "pdf":
            parsed = parse_pdf(uploaded_file)
        else:
            st.error(f"Unsupported file type: .{file_ext}")
            continue

    # Check for parser errors
    if parsed.get("error"):
        st.error(f" Parse error: {parsed['error']}")
        continue

    if parsed.get("word_count", 0) == 0:
        st.warning(" Document appears to be empty or has no extractable text.")
        continue

    # ── 2. METRICS ────────────────────────────────────────────────────────
    with st.spinner("Calculating metrics..."):
        metrics = calculate_metrics(parsed)

    # ── 3. AI ANALYSIS ────────────────────────────────────────────────────
    with st.spinner("Running AI analysis... (this may take a few seconds)"):
        ai_result = run_ai_analysis(parsed, metrics, gemini_key)

    # ── 4. SCORING ────────────────────────────────────────────────────────
    score_result = calculate_score(metrics, ai_result)

    # ── 5. BUILD REPORT ───────────────────────────────────────────────────
    report = build_report(file_name, parsed, metrics, ai_result, score_result)
    all_reports.append(report)

    # ── Show API key warning if needed ────────────────────────────────────
    if not ai_result.get("ai_powered"):
        if ai_result.get("ai_error"):
            st.warning(f" AI API error: {ai_result['ai_error']} — using rule-based fallback.")
        else:
            st.info(" Rule-based analysis active. Add a Gemini API key in the sidebar for deeper AI insights.")

    # ═════════════════════════════════════════════════════════════════════
    # DASHBOARD TABS
    # ═════════════════════════════════════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs([
        " Overview",
        " AI Analysis",
        " Issues & Fixes",
        " Export"
    ])

    # ── TAB 1: OVERVIEW ───────────────────────────────────────────────────
    with tab1:
        col_score, col_metrics = st.columns([1, 2])

        with col_score:
            st.markdown('<div class="section-header">Migration Score</div>', unsafe_allow_html=True)
            render_score_gauge(
                score_result["score"],
                score_result["band"],
                score_result["band_color"],
                chart_key=f"score_chart_{file_name}"
            )
            st.markdown(f"""
            <div style="text-align:center; margin-top:-10px;">
                <span style="font-size:18px; font-weight:700; color:{score_result['band_color']}">
                    {score_result['band_emoji']} {score_result['band']}
                </span>
            </div>
            """, unsafe_allow_html=True)

        with col_metrics:
            st.markdown('<div class="section-header">Document Metrics</div>', unsafe_allow_html=True)
            r1c1, r1c2, r1c3 = st.columns(3)
            with r1c1:
                render_metric_card("Pages",      metrics["total_pages"])
                render_metric_card("Headings",   metrics["heading_count"])
            with r1c2:
                render_metric_card("Words",      f"{metrics['word_count']:,}")
                render_metric_card("Paragraphs", metrics["para_count"])
            with r1c3:
                render_metric_card("Reading Time", f"{metrics['reading_time_minutes']} min")
                render_metric_card("Avg Words/Para", metrics["avg_words_per_para"])

        # ── Paragraph distribution chart ──────────────────────────────────
        if metrics.get("para_word_counts"):
            st.markdown('<div class="section-header" style="margin-top:20px;">Paragraph Length Distribution</div>', unsafe_allow_html=True)
            st.caption("🔴 Red bars exceed the 150-word long-paragraph threshold")
            render_paragraph_distribution(metrics["para_word_counts"])

        # ── Score breakdown ───────────────────────────────────────────────
        if score_result.get("breakdown"):
            with st.expander(" Score Breakdown (why points were deducted)"):
                for key, reason in score_result["breakdown"].items():
                    st.markdown(f'<div class="issue-item">{reason}</div>', unsafe_allow_html=True)

    # ── TAB 2: AI ANALYSIS ────────────────────────────────────────────────
    with tab2:
        ai_label = " Gemini AI" if ai_result.get("ai_powered") else "⚙️ Rule-Based"
        st.caption(f"Analysis mode: **{ai_label}**")

        if ai_result.get("ai_summary"):
            st.markdown(f"""
            <div style="background:#1a1f2e; border:1px solid #2a2f3e; border-radius:10px; padding:16px; margin-bottom:20px; font-size:14px; line-height:1.7; color:#c8cad8;">
                 {ai_result['ai_summary']}
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-header">Quality Ratings</div>', unsafe_allow_html=True)
        render_rating_table(ai_result)

    # ── TAB 3: ISSUES & RECOMMENDATIONS ──────────────────────────────────
    with tab3:
        col_issues, col_recs = st.columns(2)

        with col_issues:
            st.markdown('<div class="section-header"> Pain Points</div>', unsafe_allow_html=True)
            pain_points = ai_result.get("pain_points", [])
            if pain_points:
                for issue in pain_points:
                    st.markdown(f'<div class="issue-item"> {issue}</div>', unsafe_allow_html=True)
            else:
                st.success("No major pain points detected.")

        with col_recs:
            st.markdown('<div class="section-header"> Recommendations</div>', unsafe_allow_html=True)
            recommendations = ai_result.get("recommendations", [])
            if recommendations:
                for rec in recommendations:
                    st.markdown(f'<div class="rec-item"> {rec}</div>', unsafe_allow_html=True)
            else:
                st.success("No critical recommendations.")

        # ── Detailed metric flags ─────────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-header">Detailed Flags</div>', unsafe_allow_html=True)

        flag_cols = st.columns(3)
        with flag_cols[0]:
            dup = metrics.get("duplicate_headings", [])
            if dup:
                with st.expander(f" Duplicate Headings ({len(dup)})"):
                    for h in dup:
                        st.code(h)
            else:
                st.success(" No duplicate headings")

        with flag_cols[1]:
            empty = metrics.get("empty_sections", [])
            if empty:
                with st.expander(f" Empty Sections ({len(empty)})"):
                    for s in empty:
                        st.code(s)
            else:
                st.success(" No empty sections")

        with flag_cols[2]:
            long_p = metrics.get("long_para_count", 0)
            if long_p > 0:
                with st.expander(f" Long Paragraphs ({long_p})"):
                    for i, p in enumerate(metrics.get("long_paragraphs", [])[:3]):
                        st.caption(f"Example {i+1} ({len(p.split())} words):")
                        st.markdown(f"> {p[:200]}...")
            else:
                st.success(" No long paragraphs")

    # ── TAB 4: EXPORT ─────────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="section-header">Download Report</div>', unsafe_allow_html=True)

        report_json = report_to_json_string(report)

        st.download_button(
            label    = " Download JSON Report",
            data     = report_json,
            file_name = f"migration_report_{file_name.rsplit('.', 1)[0]}.json",
            mime     = "application/json",
        )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("**Preview of JSON Report:**")
        st.code(report_json, language="json")


# ─────────────────────────────────────────────────────────────────────────────
# BATCH SUMMARY (if multiple files uploaded)
# ─────────────────────────────────────────────────────────────────────────────
if len(all_reports) > 1:
    st.markdown("---")
    st.markdown("##  Batch Summary")

    summary_data = []
    for r in all_reports:
        summary_data.append({
            "Document":            r["document_name"],
            "Score":               r["migration_score"],
            "Readiness":           r["migration_readiness"],
            "Words":               r["word_count"],
            "Risk":                r["risk_level"],
            "Readability":         r["readability"],
        })

    df_summary = pd.DataFrame(summary_data)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)

    # Batch JSON download
    all_json = json.dumps(all_reports, indent=2)

    st.download_button(
        label     = " Download All Reports (JSON)",
        data      = all_json,
        file_name = "migration_reports_batch.json",
        mime      = "application/json",
    )
