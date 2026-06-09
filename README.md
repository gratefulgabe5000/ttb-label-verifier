# TTB AI Label Verification Tool

**US Department of Treasury — Take-Home Assessment**  
*IT Specialist (AI) · Position 26-DO-12891471-DH*  
*Submitted by: Matthew Gabriel Sizemore*

---

## Overview

An AI-powered web application that assists TTB (Alcohol and Tobacco Tax and Trade Bureau) compliance agents in verifying alcohol beverage label applications. The tool uses computer vision to extract structured data from label images, compares it against application-submitted field values, and surfaces mismatches — reducing the manual verification burden on agents processing ~150,000 COLA applications per year.

**Target users:** TTB compliance agents  
**Core problem solved:** Agents spend significant time on routine data-entry verification (confirming that what appears on a label matches what was submitted in the application). The tool automates this step.  
**Hard performance constraint:** Results must return in ≤ 5 seconds per label.

---

## Live Demo

> **Deployed Application:** _(link added upon deployment)_

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- An [Anthropic API key](https://console.anthropic.com)

### Installation

```bash
git clone https://github.com/gratefulgabe5000/ttb-label-verifier.git
cd ttb-label-verifier
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=your_api_key_here
```

### Run Locally

```bash
streamlit run app/main.py
```

Opens at `http://localhost:8501`.

---

## Usage

1. **Upload a label image** — drag-and-drop or click to browse (JPEG, PNG, WebP)
2. **Enter application data** — fill in the expected values from the COLA application form
3. **Verify** — click "Verify Label" to analyze
4. **Review results** — each field shows ✅ Match, ⚠️ Review, or ❌ Mismatch

For bulk processing, use the **Batch** tab to upload multiple labels at once.

---

## Verified Fields

| Field | Requirement |
|-------|-------------|
| Brand Name | Must match application (case/punctuation tolerant) |
| Class / Type Designation | Must match application |
| Alcohol by Volume (ABV) | Must match application |
| Net Contents | Must match application |
| Bottler / Producer Name & Address | Must be present and match |
| Country of Origin | Required for imports |
| Government Health Warning | Exact statutory text; "GOVERNMENT WARNING:" in all-caps bold |

---

## Architecture

```
┌─────────────────────────────────────┐
│         Streamlit Web UI            │
│  (upload · form input · results)    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Verification Engine         │
│  label_extractor.py                 │
│  field_comparator.py                │
│  warning_validator.py               │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      Claude Sonnet Vision API       │
│  (image → structured JSON fields)   │
└─────────────────────────────────────┘
```

**Key design decisions:**
- **Streamlit** — minimal UI complexity, browser-based, accessible to non-technical users, rapid to develop and deploy
- **Claude Vision** — handles varied image quality (angle, lighting, glare) better than traditional OCR; returns structured JSON; typical response is 1–3 seconds
- **Stateless / no database** — images and data are processed in-memory and discarded; no PII stored

---

## Project Documentation

- [DevLog — Engineering Notes, Requirements Analysis & Approach](_DevLog/DevLog.md)

---

## License

Copyright (c) 2026 Matthew Gabriel Sizemore. All rights reserved.  
Submitted as a take-home assessment for the US Department of the Treasury.
