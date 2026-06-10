# TTB Label Verification System

**US Department of Treasury — Take-Home Assessment**  
*IT Specialist (AI) · Position 26-DO-12891471-DH*  
*Submitted by: Matthew Gabriel Sizemore*

---

## Overview

An AI-powered web application that automates the review of COLA (Certificate of Label Approval) applications for the TTB (Alcohol and Tobacco Tax and Trade Bureau). Agents upload TTB Form F 5100.31 (PDF) alongside companion label artwork images. The system extracts structured data from both, compares them parameter-by-parameter, and issues determinations — **Approve**, **Deny**, or **Recommend Exemption Review** — which agents can review, annotate, and override.

**Problem:** TTB agents process ~150,000 label applications per year. A significant portion of each review is routine data-entry verification — confirming that a label image matches its application form. The AI handles the comparison; agents handle the judgment.

**Hard constraint:** AI analysis must complete in ≤ 5 seconds per label.

---

## Live Demo

> **Deployed Application:** _(link added upon deployment)_  
> **Repository:** https://github.com/gratefulgabe5000/ttb-label-verifier

---

## Quick Start

### Prerequisites

- Python 3.11+ and Node.js 20+
- An [Anthropic API key](https://console.anthropic.com)

### Backend Setup

```bash
cd app
pip install -r requirements.txt
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env
uvicorn main:app --reload
# API runs at http://localhost:8000
```

### Frontend Setup

```bash
cd web
npm install
npm run dev
# UI runs at http://localhost:5173
```

### First Run

1. Open `http://localhost:5173`
2. Log in as a test agent (credentials in `.env.example`)
3. Upload a TTB F 5100.31 form PDF and a companion label image
4. Click **Process** — results appear in ≤ 5 seconds

---

## Features

### Core Pipeline

1. **Ingest** — Upload TTB Form F 5100.31 (PDF) and one or more companion label artwork images (brand, back, neck, etc.); paired and logged in a local database
2. **Form Assessment** — AI extracts every field on the application form (all 18 Part I items) in one pass
3. **Label Assessment** — Claude Vision independently extracts everything visible from **every** label image submitted — not just a single "primary" label — tagging each element with its source image
4. **Comparison** — Per-field matching against the full set of label images: a required field is satisfied if it's found on *any* of them
5. **Determination** — Issues Approve / Deny / Recommend Exemption Review with per-field breakdown
6. **Override** — Agents can right-click any parameter to override the AI determination with a reason

### Agent Dashboard

- List of pending applications assigned to the agent
- Filter and sort by applicant company name
- Checkbox batch selection → single **Process** click
- Result badges (✅ / ❌ / ⚠️) update automatically after processing
- Batch summary header: X Approvals · Y Denials · Z Exemption Reviews

### Application Detail View

- **Split view:** Form PDF (left) · Label image(s) (right, with selector when multiple images are submitted)
- **Red ellipses** mark mismatched fields on both documents, anchored to whichever label image the field was found on
- **Mouse-over** on any annotation highlights the corresponding element on the opposite panel
- Per-parameter results table with match status and notes
- Right-click any parameter → **Override** with reason
- Override overall recommendation before finalizing

---

## Verified Fields

| Field | Form Item | Comparison Rule |
|-------|-----------|----------------|
| Brand Name | Item 6 | Case/punctuation tolerant; substantive changes = hard failure |
| Fanciful Name | Item 7 | Normalized match (if present on form) |
| Source (Domestic/Imported) | Item 3 | Imported → country of origin required on label |
| Product Type | Item 5 | Must be consistent with class/type on label |
| Applicant Name & Address | Item 8 | Normalized; in-state address changes = allowable |
| Grape Varietals | Item 10 | Wine only — all listed must appear on label |
| Wine Appellation | Item 11 | Must match if stated on form |
| Type 14b — For sale in STATE | Item 14 | "For sale in [STATE] only" must appear on label |
| Government Health Warning | — | Exact 27 CFR § 16.21 text; "GOVERNMENT WARNING:" in ALL CAPS BOLD |
| Alcohol by Volume (ABV) | — | Must be present; consistent with product type |
| Net Contents | — | Must be present |

> Each field above is satisfied if it appears on **any** of the application's submitted label images — e.g., the Government Warning and bottler address are commonly on the back label, not the front/brand label.

### Determination Logic

| Outcome | Condition |
|---------|-----------|
| ✅ **Approve** | All parameters match within tolerance |
| ❌ **Deny** | One or more hard failures (mandatory mismatch not in Allowable Revisions) |
| ⚠️ **Recommend Exemption Review** | Mismatches present but all fall within TTB F 5100.31 Section V Allowable Revisions |

---

## Architecture

```
┌─────────────────────────────────────┐
│        React + Vite Frontend        │
│  Dashboard · Split View · Overrides │
└──────────────┬──────────────────────┘
               │ REST API (JSON)
┌──────────────▼──────────────────────┐
│         FastAPI Backend             │
│  Ingestion · Pipeline · Reports     │
├─────────────────────────────────────┤
│         SQLite (workingfiles DB)    │
│  applications · comparisons ·       │
│  determinations · batches           │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Claude Sonnet Vision API       │
│  Form PDF extraction (Stage 3)      │
│  Label image extraction (Stage 4)   │
└─────────────────────────────────────┘
```

**Stack:**
- Backend: Python · FastAPI · SQLAlchemy · SQLite
- AI: Claude claude-sonnet-4-6 (Anthropic) — vision + structured JSON extraction
- Form extraction: pypdf (AcroForm fields) · pdfplumber (text layer) — tiered fallback before AI vision
- Label preprocessing: OpenCV (deskew, contrast, glare suppression) · Tesseract/pytesseract (OCR bounding-box assist)
- Frontend: React · Vite · TypeScript · Tailwind CSS · react-pdf
- Annotations: Custom SVG overlay for cross-document highlighting
- Deployment: Railway (API) + Netlify (web)

---

## Project Structure

```
ttb-label-verifier/
├── app/                    # FastAPI backend
│   ├── main.py             # App entrypoint
│   ├── routers/            # API route handlers
│   ├── services/           # Pipeline stages (extractor, comparator, reporter)
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic request/response schemas
│   ├── db.py               # Database connection
│   └── requirements.txt
├── web/                    # React frontend
│   ├── src/
│   │   ├── pages/          # Dashboard, ApplicationDetail, BatchReport
│   │   ├── components/     # SplitView, AnnotationOverlay, ParameterTable
│   │   └── api/            # React Query hooks
│   ├── package.json
│   └── vite.config.ts
├── _DevLog/
│   └── DevLog.md           # Engineering log, requirements, architecture
├── f510031.pdf             # TTB Form F 5100.31 (04/2023) reference
├── README.md
└── .gitignore
```

---

## Documentation

- [DevLog — Full Engineering Notes, Requirements Analysis & Architecture](_DevLog/DevLog.md)

---

## License

Copyright (c) 2026 Matthew Gabriel Sizemore. All rights reserved.  
Submitted as a take-home assessment for the US Department of the Treasury.
