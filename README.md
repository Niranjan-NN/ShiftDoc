# 📄 ShiftDoc — Document Analysis & Migration Readiness Tool

> AI-powered document analyzer that tells you: **"Is this document ready for migration?"**

Built as part of a **Migration Specialist coding assessment** — assessing documents for platform migration (e.g., Document360, Confluence, Notion) with real-world business logic.

---

## 🚀 Features

| Feature | Details |
|--------|---------|
| 📂 Multi-format support | Analyze `.docx` and `.pdf` files |
| 📊 Metrics engine | Word count, headings, paragraphs, reading time, and more |
| 🤖 AI analysis | Powered by **Gemini 1.5 Flash** API |
| 🎯 Migration score | 0–100 scoring with `Not Ready / Needs Improvement / Migration Ready` bands |
| ⚠️ Pain detection | Duplicate headings, empty sections, long paragraphs |
| ✅ Recommendations | Actionable steps to fix identified issues |
| 📥 Export | Download JSON report per document |
| 📦 Batch analysis | Analyze multiple documents at once |
| ⚙️ Fallback mode | Works without API key using rule-based analysis |

---

## 🗂️ Project Structure

```
doc_migration_tool/
│
├── app.py                   # Main Streamlit UI application
│
├── parser/
│   ├── __init__.py
│   ├── docx_parser.py       # Extracts content from .docx files
│   └── pdf_parser.py        # Extracts content from .pdf files
│
├── analysis/
│   ├── __init__.py
│   ├── metrics.py           # Quantitative metrics calculation
│   ├── ai_analysis.py       # Gemini API integration + fallback
│   └── scoring.py           # Migration readiness scoring (0–100)
│
├── utils/
│   ├── __init__.py
│   └── helpers.py           # Report building and utilities
│
├── reports/                 # (Optional) Save reports here
├── sample_docs/             # Put test documents here
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation

### 1. Clone or download the project

```bash
git clone https://github.com/YOUR_USERNAME/doc-migration-tool.git
cd doc-migration-tool
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 API Key Setup (Gemini)

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account
3. Click **"Get API Key"** → **"Create API Key"**
4. Copy the key (starts with `AIza...`)
5. Paste it into the **sidebar** when running the app

> **No key? No problem.** The tool runs in rule-based fallback mode without any API key.

---

## ▶️ How to Run

```bash
streamlit run app.py
```
or 

```bash
python -m streamlit run app.py
```
The app opens in your browser at `http://localhost:8501`

---

## 📤 How to Use

1. Open the app in your browser
2. (Optional) Enter your Gemini API key in the sidebar
3. Click **"Browse files"** and upload one or more `.docx` / `.pdf` files
4. View the analysis across 4 tabs:
   - **Overview** — Score gauge + metrics cards + paragraph distribution chart
   - **AI Analysis** — Quality ratings table + AI summary
   - **Issues & Fixes** — Pain points and recommendations
   - **Export** — Download JSON report
5. For multiple files, a **Batch Summary** table appears at the bottom

---

## 📊 Sample JSON Output

```json
{
  "document_name": "Managing articles.docx",
  "analysis_timestamp": "2026-05-18 14:30:00",
  "pages": 4,
  "word_count": 1240,
  "char_count": 7850,
  "paragraphs": 32,
  "headings": 8,
  "avg_words_per_para": 38.8,
  "reading_time_min": 5,
  "long_para_count": 1,
  "duplicate_headings": [],
  "empty_sections": [],
  "readability": "Easy",
  "content_clarity": "High",
  "structural_consistency": "High",
  "documentation_quality": "High",
  "content_reusability": "High",
  "risk_level": "Low",
  "ai_powered": true,
  "migration_score": 88,
  "migration_readiness": "Migration Ready",
  "score_breakdown": {
    "long_paragraphs": "-3 pts: 1 long paragraph(s)"
  },
  "pain_points": [
    "1 long paragraph detected — consider splitting"
  ],
  "recommendations": [
    "Break the long paragraph into 2–3 focused sections"
  ],
  "ai_summary": "This document is well-structured with clear headings..."
}
```

---

## 🧠 Architecture Decisions

| Decision | Reason |
|----------|--------|
| **Modular folder structure** | Each concern is isolated — easy to test or swap components |
| **Gemini 1.5 Flash** | Fast, cheap, free tier available |
| **Fallback rule-based analysis** | App works without any API key |
| **Start-at-100 scoring** | Deductions are transparent and debuggable |
| **pdfplumber + PyPDF2** | pdfplumber is more accurate; PyPDF2 as fallback |
| **Streamlit** | Rapid prototyping, clean UI, no frontend knowledge needed |

---

## 📦 Libraries Used

| Library | Purpose |
|---------|---------|
| `streamlit` | Web UI |
| `python-docx` | DOCX parsing |
| `pdfplumber` | PDF parsing (primary) |
| `PyPDF2` | PDF parsing (fallback) |
| `google-generativeai` | Gemini API client |
| `plotly` | Score gauge chart + bar charts |
| `pandas` | Batch summary table |

---

## 👨‍💻 Author

**Niranjan NN**  
B.Tech Information Technology — SNS College of Engineering  
GitHub: [github.com/Niranjan-NN](https://github.com/Niranjan-NN)  
LinkedIn: [linkedin.com/in/niranjan-nn](https://linkedin.com/in/niranjan-nn)