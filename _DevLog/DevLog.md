# DevLog — TTB AI Label Verification Tool

**Assessment:** IT Specialist (AI) · 26-DO-12891471-DH  
**Candidate:** Matthew Gabriel Sizemore  
**Assessment Received:** June 9, 2026, 1458 hrs  
**Deadline:** June 16, 2026, 1458 hrs
**Repository:** https://github.com/gratefulgabe5000/ttb-label-verifier  
**Submission Form:** https://forms.osi.office365.us/r/xWrQGduMw7

---

## Table of Contents

1. [Assessment Overview](#1-assessment-overview)
2. [Requirements Analysis](#2-requirements-analysis)
3. [Technical Approach](#3-technical-approach)
4. [Tools & Technology Rationale](#4-tools--technology-rationale)
5. [Assumptions](#5-assumptions)
6. [Engineering Log](#6-engineering-log)
7. [Chat Artifact Index](#7-chat-artifact-index)

---

## 1. Assessment Overview

**Organization:** US Department of the Treasury, Departmental Offices — Treasury Common Services Center, Office of the Deputy Administrator for Technology Services

**Context:** The TTB (Alcohol and Tobacco Tax and Trade Bureau) processes approximately 150,000 COLA (Certificate of Label Approval) applications per year with a team of 47 compliance agents. A significant portion of each review is routine data-entry verification — confirming that what appears on a label image matches what was submitted in the application form. This process has been largely unchanged since the COLA system went online in 2003.

**Objective:** Design and build a working AI-powered prototype that assists TTB compliance agents by automating label field extraction and comparison against application-submitted data, surfacing mismatches so agents can focus on judgment-intensive cases rather than mechanical verification.

### Source Documents

| File | Description |
|------|-------------|
| `1.Notification - IT Specialist (AI) - 26-DO-12891471-DH.pdf` | Email from USA Staffing Office — assessment delivery notification, deliverable requirements |
| `2.TreasuryTakeHomeTest.pdf` | Microsoft Forms submission page — confirms two deliverables: Source Code Repository + Deployed Application URL |
| `3.Assessment_README.txt` | Primary assessment brief — four stakeholder interview transcripts and TTB technical context |

> **Evaluator note:** These files are in the repository root. They are the primary requirements source and are referenced throughout this DevLog.

---

## 2. Requirements Analysis

Requirements were extracted from all three source documents. Each requirement is tagged with its verbatim source to demonstrate attention to the brief.

### 2.1 Functional Requirements

| ID | Requirement | Source | Priority |
|----|-------------|--------|----------|
| FR-01 | Accept label image upload for analysis | Assessment README — Deliverables section | **MUST** |
| FR-02 | Extract brand name from label image | Assessment README — TTB Label Requirements; Sarah Chen: "Brand name matches? Check." | **MUST** |
| FR-03 | Extract class/type designation from label | Assessment README — TTB Label Requirements | **MUST** |
| FR-04 | Extract alcohol content (ABV) from label | Assessment README; Sarah Chen: "ABV is correct? Check." | **MUST** |
| FR-05 | Extract net contents from label | Assessment README — TTB Label Requirements | **MUST** |
| FR-06 | Extract bottler/producer name and address | Assessment README — TTB Label Requirements | **MUST** |
| FR-07 | Extract country of origin (imports) | Assessment README — TTB Label Requirements | **MUST** |
| FR-08 | Verify Government Health Warning Statement — exact text, "GOVERNMENT WARNING:" in all-caps bold | Jenny Park: "It has to be exact. Like, word-for-word, and the 'GOVERNMENT WARNING:' part has to be in all caps and bold." | **MUST** |
| FR-09 | Accept expected application data from user for comparison | Sarah Chen: "An agent pulls up an application, looks at the label artwork, and checks that what's on the label matches what's in the application." | **MUST** |
| FR-10 | Return per-field pass/fail/mismatch results with explanations | Assessment README — Evaluation Criteria ("Correctness and completeness of core requirements") | **MUST** |
| FR-11 | Apply case/formatting tolerance to brand name matching | Dave Morrison: "'STONE'S THROW' on the label but 'Stone's Throw' in the application. Technically a mismatch? Sure. But it's obviously the same thing." | **SHOULD** |
| FR-12 | Support batch upload of multiple label images | Sarah Chen: "During peak season, we get these big importers who dump 200, 300 label applications on us at once... Janet from our Seattle office has been asking about this for years." | **NICE-TO-HAVE** |
| FR-13 | Handle degraded image quality (angle, glare, bad lighting) | Jenny Park: "It would be amazing if the tool could handle images that aren't perfectly shot... labels photographed at weird angles, or the lighting is bad, or there's glare on the bottle." | **NICE-TO-HAVE** |

### 2.2 Non-Functional Requirements

| ID | Requirement | Source | Priority |
|----|-------------|--------|----------|
| NFR-01 | Response time ≤ 5 seconds per label | Sarah Chen: "If we can't get results back in about 5 seconds, nobody's going to use it. We learned that the hard way." (prior vendor failed at 30–40s per label) | **HARD CONSTRAINT** |
| NFR-02 | UI accessible to non-technical users | Sarah Chen: "We need something my mother could figure out—she's 73 and just learned to video call her grandkids last year... Half our team is over 50." | **MUST** |
| NFR-03 | Clean interface, no hidden controls | Sarah Chen: "Clean, obvious, no hunting for buttons." Dave Morrison: past modernization projects failed due to poor UX. | **MUST** |
| NFR-04 | No persistent storage of sensitive data | Marcus Williams: "There's PII considerations, document retention policies, the usual federal compliance stuff. But for a prototype? Just don't do anything crazy. We're not storing anything sensitive for this exercise." | **MUST** |
| NFR-05 | Standalone POC — no COLA integration | Marcus Williams: "Think of this as a standalone proof-of-concept... For a prototype? [COLA integration is] years away, realistically." | **MUST** |
| NFR-06 | Publicly accessible deployed URL | Assessment README — Deliverables; Email — Deliverable #2 | **MUST** |
| NFR-07 | Minimize dependency on blocked external domains | Marcus Williams: "Our network blocks outbound traffic to a lot of domains... During the scanning vendor pilot, half their features didn't work because our firewall blocked connections to their ML endpoints." Note: prototype exemption implied. | **SHOULD** (prototype) |

### 2.3 Government Warning Statement — Critical Detail

Per Jenny Park's interview, the Government Health Warning is a frequent rejection point with specific, non-negotiable requirements.

**Statutory text (27 CFR § 16.21):**
```
GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink
alcoholic beverages during pregnancy because of the risk of birth defects. (2)
Consumption of alcoholic beverages impairs your ability to drive a car or operate
machinery, and may cause health problems.
```

**Formatting rules extracted from Jenny Park's interview:**
- "GOVERNMENT WARNING:" — must appear in ALL CAPS and BOLD
- Text must be exact — no paraphrasing, no abbreviated wording
- Not buried in disproportionately small font
- Common violations caught: title case ("Government Warning"), modified wording, undersized font

### 2.4 TTB Label Fields — Reference (from Assessment README)

For distilled spirits (example provided in brief):
- Brand Name: `"OLD TOM DISTILLERY"`
- Class/Type: `"Kentucky Straight Bourbon Whiskey"`
- Alcohol Content: `"45% Alc./Vol. (90 Proof)"`
- Net Contents: `"750 mL"`
- Government Warning: [statutory text above]

Beverage types: beer, wine, distilled spirits each have variations. Prototype targets distilled spirits as the primary case; logic generalizes to all three.

### 2.5 Evaluation Criteria (verbatim from Assessment README)

1. Correctness and completeness of core requirements
2. Code quality and organization
3. Appropriate technical choices for the scope
4. User experience and error handling
5. **Attention to requirements**
6. Creative problem-solving

> **Note on criterion 5:** Requirements are embedded in narrative interview transcripts rather than a structured spec sheet. Identifying, extracting, and prioritizing them from the stakeholder context is itself part of the evaluation.

### 2.6 Deliverables Checklist

| Deliverable | Status | Location |
|-------------|--------|----------|
| Source Code Repository (GitHub, public) | ✅ Created | https://github.com/gratefulgabe5000/ttb-label-verifier |
| All source code | ☐ In progress | `app/` |
| README with setup and run instructions | ✅ Done | `README.md` |
| Documentation of approach, tools, assumptions | ✅ Done | `_DevLog/DevLog.md` (this file) |
| Deployed Application URL | ☐ Pending deployment | TBD |

---

## 3. Technical Approach

### 3.1 Problem Decomposition

The core task decomposes into three stages:

```
[1] IMAGE → FIELDS            [2] FIELDS ↔ APPLICATION         [3] RESULTS → USER
─────────────────────         ────────────────────────         ─────────────────────
Label image upload            Compare extracted fields          Display per-field
→ Claude Vision API     →     against user-entered        →    pass / review / fail
→ structured JSON             application data                  with explanation
```

**Stage 1 — Image to Fields:** A vision-capable LLM extracts structured label data from the uploaded image. This approach handles varied image quality, non-standard fonts, and diverse label layouts far better than a traditional OCR + regex pipeline. The model is prompted to return a strict JSON schema.

**Stage 2 — Fields vs. Application:** Pure Python comparison logic with tolerance rules applied per field type:
- Brand name: case-insensitive, punctuation-normalized (handles Dave Morrison's "STONE'S THROW" case)
- ABV: numeric extraction and comparison (handles `"45%"` vs `"45% Alc./Vol. (90 Proof)"`)
- Government Warning: exact text match after normalization; separate formatting flag for all-caps "GOVERNMENT WARNING:"
- All other fields: normalized string comparison with whitespace/case tolerance

**Stage 3 — Results to User:** Clear, color-coded per-field output. ✅ green / ⚠️ yellow / ❌ red. Plain English explanations. No jargon. No hunting for information.

### 3.2 Design Decisions

**Decision 1: Streamlit over custom React/Next.js**
- *Rationale:* Prototype scope; Streamlit delivers a functional, accessible, browser-based UI in significantly less code with no frontend build toolchain; deploys to a public URL in one command.
- *Trade-off:* Less flexibility for future branding or COLA workflow integration. Not production architecture.
- *Alternative considered:* FastAPI + React — adds build complexity with no prototype benefit.

**Decision 2: Claude Vision (claude-sonnet-4-6) for field extraction**
- *Rationale:* Typical response 1–3 seconds — well within the 5-second hard constraint. Handles degraded image quality (Jenny Park's concern) naturally. Returns structured JSON via tool use. Accurate on mixed-font label layouts without pre-training.
- *Trade-off:* Requires an API key and internet access. Acceptable for a prototype; Marcus Williams acknowledged the firewall concern applies to production, not POC.
- *Alternative considered:* Tesseract OCR — offline-friendly but struggles with varied label fonts, angles, and multi-column layouts.

**Decision 3: Stateless / no database**
- *Rationale:* Marcus Williams explicitly stated no sensitive data storage is required for the prototype. Stateless design is simpler, avoids all PII compliance questions, and is appropriate for the POC scope.
- *Trade-off:* No audit history or result persistence.
- *Production note:* A real deployment would require audit logging per federal document retention policy.

**Decision 4: Sequential batch processing (for batch feature)**
- *Rationale:* Process labels one at a time with a progress bar; simpler for prototype scope.
- *Trade-off:* Not parallelized. For 200-label batches, total time would be 200 × ~3s = ~10 minutes. Acceptable as a first version; async worker queue is the production path.

---

## 4. Tools & Technology Rationale

| Tool / Library | Version | Purpose | Rationale |
|----------------|---------|---------|-----------|
| Python | 3.11+ | Primary language | Mature AI/ML ecosystem; standard for rapid prototyping |
| Streamlit | latest | Web UI | Minimal setup; browser-based; designed for data apps and prototypes; accessible to non-technical users |
| Anthropic Python SDK | latest | Claude API client | Official SDK for claude-sonnet-4-6 vision access |
| Claude Sonnet (claude-sonnet-4-6) | claude-sonnet-4-6 | Vision + NLP | Sub-3s response; handles degraded images; structured JSON output via tool use |
| Pillow (PIL) | latest | Image preprocessing | Format normalization, resize before API submission |
| python-dotenv | latest | Environment config | Secure API key management via `.env` |
| pytest | latest | Unit testing | Tests for comparator and validator logic |

---

## 5. Assumptions

| ID | Assumption | Basis / Reasoning |
|----|-----------|-------------------|
| A-01 | Internet access is available for the deployed prototype | Marcus Williams' firewall concern is explicitly about production; prototype scope is exempt |
| A-02 | Anthropic API key provisioned for deployment | Required for Claude Vision; cost is minimal for prototype-level usage |
| A-03 | Application data (expected values) is manually entered by the agent, not pulled from COLA | Marcus Williams: "No COLA integration for this prototype." |
| A-04 | Label images are standard photo formats: JPEG, PNG, WebP | Standard for digital label submissions; Assessment README sample uses this assumption |
| A-05 | Government Warning text is the standard 27 CFR § 16.21 statement | TTB regulation; confirmed by Jenny Park's description of the exact text requirement |
| A-06 | Case and minor punctuation differences in brand names are acceptable matches | Dave Morrison's example: "STONE'S THROW" vs "Stone's Throw" — human judgment call mapped to normalization rule |
| A-07 | Font size of Government Warning cannot be measured programmatically from photos | Vision models describe relative appearance; pixel-level font measurement requires known image scale — flagged as visual observation, not hard measurement |
| A-08 | Batch processing handles labels sequentially with a progress indicator | Prototype scope; parallelization is a production concern |
| A-09 | The prototype does not need user accounts or session persistence | Standalone POC; no authentication infrastructure required |
| A-10 | "Country of Origin" field check applies only when the label explicitly indicates import status | Domestic products are not always required to show country of origin; field is checked when present |

---

## 6. Engineering Log

### 2026-06-09 — Session 1: Assessment Intake & Project Setup

**Completed:**
- Read and analyzed all three assessment source documents
- Extracted and prioritized requirements from four stakeholder interview narratives
- Identified the 5-second response constraint as a hard design driver (informed model selection)
- Identified the Government Warning format check as the highest-precision requirement
- Decided on technical stack: Python + Streamlit + Claude claude-sonnet-4-6 Vision
- Initialized git repository in `projects/1.Active/Treasury_Assessment/`
- Created public GitHub repository: `gratefulgabe5000/ttb-label-verifier`
- Authored `README.md` (setup + run instructions, architecture overview)
- Authored `_DevLog/DevLog.md` (this file — requirements analysis, approach, assumptions)
- Created `.gitignore` for Python/Streamlit project

**Open questions / next session:**
- Confirm Streamlit Community Cloud as deployment target (vs. Railway, Render, HuggingFace Spaces)
- Define the exact JSON schema the extraction prompt will return
- Decide whether to use Claude tool use or structured output mode for extraction
- Write `app/label_extractor.py` — core extraction module
- Write `app/field_comparator.py` — comparison logic with tolerance rules
- Write `app/warning_validator.py` — government warning exact-match validator
- Write `app/main.py` — Streamlit UI
- Create test labels for validation (AI-generated per assessment suggestion)

---

## 7. Chat Artifact Index

This section indexes all development session transcripts exported as artifacts. Files are stored alongside this DevLog in `_DevLog/`.

| File | Date | Session Description |
|------|------|---------------------|
| `2026-06-09_session-01_setup.md` | 2026-06-09 | Assessment intake, requirements analysis, project setup, repo initialization |
| _(future sessions appended here)_ | | |

---

*Maintained by Matthew Gabriel Sizemore — gratefulgabe5000@gmail.com*  
*Assessment: IT Specialist (AI) · 26-DO-12891471-DH · US Department of the Treasury*
