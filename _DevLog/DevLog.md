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
3. [System Design & Trade Studies](#3-system-design--trade-studies)
4. [Tools & Technology Rationale](#4-tools--technology-rationale)
5. [Assumptions](#5-assumptions)
6. [COLA Registry & Future Integration Reference](#6-cola-registry--future-integration-reference)
7. [Engineering Log](#7-engineering-log)
8. [Chat Artifact Index](#8-chat-artifact-index)

---

## 1. Assessment Overview

**Organization:** US Department of the Treasury, Departmental Offices — Treasury Common Services Center, Office of the Deputy Administrator for Technology Services

**Context:** The TTB (Alcohol and Tobacco Tax and Trade Bureau) processes approximately 150,000 COLA (Certificate of Label Approval) applications per year using TTB Form F 5100.31. A team of 47 compliance agents manually reviews each application by comparing the submitted form data against affixed label artwork. This verification is largely routine data-entry matching that consumes agent capacity that could otherwise be directed at judgment-intensive cases.

**Objective:** Build a working AI-powered prototype that automates the extraction, comparison, and determination workflow for COLA applications — allowing agents to review AI recommendations rather than perform the comparisons manually. The system ingests the application form (TTB F 5100.31 as PDF) and companion label artwork (images), extracts structured parameters from both, compares them, and issues per-parameter and overall determinations (Approve / Deny / Recommend Exemption Review) which agents can override.

### Source Documents

| File | Description |
|------|-------------|
| `1.Notification - IT Specialist (AI) - 26-DO-12891471-DH.pdf` | USA Staffing Office notification — assessment delivery and deliverable requirements |
| `2.TreasuryTakeHomeTest.pdf` | Microsoft Forms submission page — confirms two required deliverables |
| `3.Assessment_README.txt` | Primary assessment brief — four stakeholder interviews + TTB technical context |
| `f510031.pdf` | Official TTB Form F 5100.31 (04/2023) — application form agents process; primary data source |

---

## 2. Requirements Analysis

### 2.1 Functional Requirements

Requirements extracted from stakeholder interviews and the assessment brief. Each requirement is tagged with its verbatim source.

| ID | Requirement | Source | Priority |
|----|-------------|--------|----------|
| FR-01 | Ingest application form (TTB F 5100.31 PDF) and log in workingfiles DB | Design session | **MUST** |
| FR-02 | Ingest companion label artwork image(s) and pair with application in DB | Design session | **MUST** |
| FR-03 | Extract all structured parameters from the application form | Design session; Sarah Chen: "checks that what's on the label matches what's in the application" | **MUST** |
| FR-04 | Extract all structured parameters from the label image(s) via AI vision | Design session; Sarah Chen: "ABV is correct? Check. Government warning is there? Check." | **MUST** |
| FR-05 | Compare form parameters vs label parameters, per field | Design session | **MUST** |
| FR-06 | Issue per-parameter determination: Match / Mismatch | Design session | **MUST** |
| FR-07 | Issue overall determination: Approve / Deny / Recommend Exemption Review | Design session | **MUST** |
| FR-08 | Verify Government Warning Statement — exact statutory text; "GOVERNMENT WARNING:" in all-caps bold | Jenny Park: "It has to be exact. Like, word-for-word, and the 'GOVERNMENT WARNING:' part has to be in all caps and bold." | **MUST** |
| FR-09 | Apply case/punctuation tolerance to brand name matching | Dave Morrison: "'STONE'S THROW' on the label but 'Stone's Throw' in the application. Technically a mismatch? Sure. But it's obviously the same thing." | **MUST** |
| FR-10 | Flag mismatches that fall within Allowable Revisions (F 5100.31 Section V) as "Recommend Exemption Review" rather than hard denial | Design session | **MUST** |
| FR-11 | Agent dashboard: list pending applications assigned to agent | Design session | **MUST** |
| FR-12 | Batch selection: checkboxes on dashboard to select multiple applications | Design session; Sarah Chen: "If there was some way to handle batch uploads, that would be huge." | **MUST** |
| FR-13 | Batch processing: process all selected applications in a single action | Design session | **MUST** |
| FR-14 | Batch summary report: header count of Approvals / Denials / Exemption Reviews, plus per-application result | Design session | **MUST** |
| FR-15 | Application detail view: split view — form PDF (left) + label image (right) | Design session | **MUST** |
| FR-16 | Visual annotations: red ellipses on mismatched elements in both form and label views | Design session | **SHOULD** |
| FR-17 | Mouse-over on annotation: highlight corresponding element on opposite document | Design session | **SHOULD** |
| FR-18 | Agent override: right-click any parameter to override AI determination with reason | Design session | **MUST** |
| FR-19 | Agent override: override overall determination | Design session | **MUST** |
| FR-20 | Support batch upload of forms and label images | Design session | **NICE-TO-HAVE** |
| FR-21 | Handle degraded label image quality (angle, glare, bad lighting) | Jenny Park: "It would be amazing if the tool could handle images that aren't perfectly shot." | **NICE-TO-HAVE** |

### 2.2 Non-Functional Requirements

| ID | Requirement | Source | Priority |
|----|-------------|--------|----------|
| NFR-01 | Response time ≤ 5 seconds per label (AI extraction + comparison) | Sarah Chen: "If we can't get results back in about 5 seconds, nobody's going to use it. We learned that the hard way." | **HARD CONSTRAINT** |
| NFR-02 | UI accessible to non-technical users | Sarah Chen: "We need something my mother could figure out—she's 73 and just learned to video call her grandkids last year... Half our team is over 50." | **MUST** |
| NFR-03 | Clean interface — no hunting for buttons | Sarah Chen: "Clean, obvious, no hunting for buttons." Dave Morrison: prior modernization failures cited. | **MUST** |
| NFR-04 | No persistent storage of sensitive data beyond prototype scope | Marcus Williams: "We're not storing anything sensitive for this exercise." | **MUST** |
| NFR-05 | Standalone POC — no COLA system integration | Marcus Williams: "Think of this as a standalone proof-of-concept... that's years away, realistically." | **MUST** |
| NFR-06 | Publicly accessible deployed URL | Assessment README — Deliverables; Email notification | **MUST** |

### 2.3 Government Warning Statement — Critical Detail

Per Jenny Park's interview, the Government Health Warning is a frequent rejection point. The AI validator must check for both exact text and formatting.

**Statutory text per 27 CFR § 16.21:**
```
GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink
alcoholic beverages during pregnancy because of the risk of birth defects. (2)
Consumption of alcoholic beverages impairs your ability to drive a car or operate
machinery, and may cause health problems.
```

**Mandatory formatting:**
- "GOVERNMENT WARNING:" — must be **ALL CAPS** and **BOLD**
- Wording must be exact — no paraphrasing, abbreviation, or reordering
- Must not be buried in disproportionately small font

**Common violations (per Jenny Park):**
- Title case: "Government Warning" (should be "GOVERNMENT WARNING:")
- Missing colon after "WARNING"
- Abbreviated or paraphrased text
- Undersized font

### 2.4 Form F 5100.31 — Complete Field Reference

Source: `f510031.pdf` — TTB Form F 5100.31 (04/2023)

#### Part I — Application Fields

| Item | Field Name | Required | Notes |
|------|-----------|----------|-------|
| 1 | Representative ID No. | Optional | Third-party filer ID |
| 2 | Plant Registry / Basic Permit / Brewer's Notice No. | **Required** | BW-, TPWBH-, DSP-, or permit number; multiple locations possible |
| 3 | Source of Product | **Required** | Domestic ☐ / Imported ☐ |
| 4 | Serial Number | **Required** | Format: YY-N (last 2 digits of year + sequential, max 6 chars); e.g., 26-1 |
| 5 | Type of Product | **Required** | Wine ☐ / Distilled Spirits ☐ / Malt Beverages ☐ |
| 6 | Brand Name | **Required** | Name under which product is sold; if no brand name, use bottler/packer/importer name |
| 7 | Fanciful Name | Optional | Required for some specialty products; further identifies product |
| 8 | Name and Address of Applicant | **Required** | Exactly as on plant registry/permit; include DBA/tradename if used on label |
| 8a | Mailing Address | Optional | If different from Item 8 |
| 9 | Formula | Conditional | TTB Formula ID or lab number; required when product formula approval was needed |
| 10 | Grape Varietal(s) | Wine only | List all varietals appearing on label |
| 11 | Wine Appellation | Conditional | Fill in only if appellation of origin stated on label |
| 12 | Phone Number | — | Person responsible for application |
| 13 | Email Address | — | For TTB response |
| 14 | Type of Application | **Required (a OR b)** | See Application Types below |
| 15 | Embossed/Blown Container Info | Conditional | Info on container not on labels; foreign language translations |
| 16 | Date of Application | — | Date prepared or submitted |
| 17 | Signature | — | Applicant or authorized agent |
| 18 | Print Name | — | Signer's printed name |

#### Part III — TTB Certificate (TTB Use Only)

| Item | Field Name | Notes |
|------|-----------|-------|
| 19 | Date Issued | TTB completion |
| 20 | Authorized TTB Signature | TTB completion |
| — | Qualifications | TTB notes/conditions |
| — | Expiration Date | If any |
| — | Label Affixing Area | Applicant affixes complete label set |

### 2.5 Application Types and Determination Routing

Item 14 determines the processing path:

| Type | Description | Key Constraints | Processing Impact |
|------|-------------|----------------|-------------------|
| **14a** | Certificate of Label Approval | Standard path | Full comparison; Approve or Deny |
| **14b** | Certificate of Exemption From Label Approval | Product sold ONLY within bottling state; NOT available for imports or malt beverages | If 14b checked: label MUST contain "For sale in [STATE] only"; flag if product is imported or malt |
| **14c** | Distinctive Liquor Bottle Approval | Must include bottle capacity | Additional check: bottle capacity field |
| **14d** | Resubmission After Rejection | Must include TTB ID of rejected application | Note prior rejection in report |

**Three-Outcome Determination Logic:**

| Outcome | Condition |
|---------|-----------|
| **APPROVE** | All mandatory parameters match; no hard failures |
| **DENY** | One or more hard failures (mandatory field mismatch not in Allowable Revisions) |
| **RECOMMEND EXEMPTION REVIEW** | Mismatches present, but all fall within Allowable Revisions (Section V of F 5100.31); OR application is Type 14b |

### 2.6 Parameter Comparison Matrix

The core of the verification engine. Each form field maps to a label element, with specific comparison rules. **Per FR-038, "label" below means the union of ALL of the application's label images** — every image is extracted independently (Stage 4), and a field is considered present if it appears on any one of them, with the source `label_image_id` retained for annotation placement.

| Form Field (Item #) | Label Element | Comparison Rule | Failure Type |
|--------------------|---------------|----------------|-------------|
| Brand Name (6) | Brand Name on label | Normalized: case-insensitive, punctuation-tolerant; reject only if substantive difference | Hard failure if substantive; Allowable if case/punct only |
| Fanciful Name (7) | Fanciful Name on label | If present on form, must appear on label (normalized match) | Hard failure |
| Source: Imported (3) | Country of Origin on label | If "Imported" checked, label MUST show country of origin | Hard failure |
| Product Type (5) | Class/Type Designation | Must be consistent with checked type | Hard failure |
| Applicant Name/Address (8) | Bottler/Producer name/address on label | Normalized match; must include DBA if DBA used on label | Hard failure if name wrong; Allowable if address change in-state |
| Grape Varietals (10) | Varietals on label (Wine) | All listed varietals must appear on label | Hard failure |
| Wine Appellation (11) | Appellation on label (Wine) | If listed on form, must match label | Hard failure |
| Type 14b checked | "For sale in [STATE] only" text | Must appear on label; state abbreviation must match | Hard failure |
| *(all products)* | Government Warning Statement | Exact 27 CFR § 16.21 text; "GOVERNMENT WARNING:" in ALL CAPS BOLD | Hard failure |
| *(all products)* | Alcohol by Volume (ABV) | Must be present on label; must be consistent with product type | Hard failure |
| *(all products)* | Net Contents | Must be present on label | Allowable if change complies with standards (Section V, item 10) |

### 2.7 Allowable Revisions — Exemption Criteria Reference

Section V of TTB F 5100.31 lists 41 revision types that may be made to an approved label WITHOUT resubmission. When the AI identifies a mismatch, it cross-references this list to determine if the discrepancy is a **hard failure** (requires denial) or an **allowable revision** (triggers Recommend Exemption Review).

**Key allowable revision categories that affect comparison logic:**

| Section V Item | Revision Type | Applies To |
|----------------|---------------|-----------|
| 1 | Delete any non-mandatory information | All |
| 2 | Reposition any label information | All |
| 3a | Change colors, shape, proportionate size of labels | All |
| 3b | Change type size, font, spelling/case/punctuation | All — "mandatory info must remain legible and on contrasting background" |
| 3c | Change from adhesive to etched/printed or vice versa | All |
| 3d/3e | Divide or combine approved labels | All |
| 10 | Change net contents statement | All (must comply with standards of fill) |
| 11 | Change mandatory ABV (if consistent with class/type) | All |
| 14 | Change/delete age statement | Distilled Spirits |
| 17 | Add/change Serving Facts / average analysis statement | All |
| 18 | Add/change bottling date, production date, freshness info | All |
| 19 | Change name/trade name (already approved); address change within same state | All |
| 20 | Change foreign producer/bottler/shipper name & address | All (same country) |
| 22–41 | UPC barcodes, web addresses, awards, logos, seasonal graphics, etc. | Varies |

> **Implementation note:** The AI cannot evaluate all 41 revision types from image inspection alone. The engine will flag any mismatch as one of: `HARD_FAILURE`, `POSSIBLE_ALLOWABLE` (cross-reference Section V), or `MATCH`. The determination engine upgrades `POSSIBLE_ALLOWABLE` applications to "Recommend Exemption Review" rather than "Deny."

### 2.8 Evaluation Criteria (verbatim from Assessment README)

1. Correctness and completeness of core requirements
2. Code quality and organization
3. Appropriate technical choices for the scope
4. User experience and error handling
5. **Attention to requirements**
6. Creative problem-solving

> **Note on criterion 5:** Requirements are embedded in narrative interview transcripts rather than a structured spec sheet. Extracting all requirements from the stakeholder context — including the 5-second constraint, the Government Warning formatting rules, and the case-tolerance requirement — is itself part of the evaluation. This DevLog demonstrates that all requirements have been identified and traced to their source.

### 2.9 Deliverables Checklist

| Deliverable | Status | Location |
|-------------|--------|----------|
| Source Code Repository (GitHub, public) | ✅ Created | https://github.com/gratefulgabe5000/ttb-label-verifier |
| All source code | ☐ In progress | `app/` (backend), `web/` (frontend) |
| README with setup and run instructions | ✅ | `README.md` |
| Documentation of approach, tools, assumptions | ✅ | `_DevLog/DevLog.md` (this file) |
| Deployed Application URL | ☐ Pending | TBD — Railway (API) + Netlify (web) |

---

## 3. System Design & Trade Studies

### 3.1 Trade Studies

Before finalizing the architecture, two trade studies were conducted to test whether the "AI for everything" extraction approach implied by the original design is actually the most effective use of AI — both for staying within the PR-001 5-second budget and for extraction accuracy. The guiding principle: **AI is a hard requirement and remains the system's semantic core (Stage 4 label understanding, and the comparison/determination logic built on top of it) — but AI should not be used where a deterministic method is strictly faster and more accurate.**

#### TS-01: Form Data Extraction Method (Stage 3)

**Question:** Should Stage 3 rely solely on Claude Vision for form-field extraction (original design), or can a more direct method improve speed, cost, and accuracy — given NFR-01's 5-second budget is shared with Stage 4's per-image vision calls?

**Finding:** Direct inspection of `f510031.pdf` (the official TTB Form F 5100.31, 04/2023, included in this repo) shows it is a **fillable AcroForm PDF containing 44 named form fields**, mapping to Part I items 1, 2, 6, 7, 8, 8a, 9, 10, 11, 12, 13, 14a–d (including the 14b state-abbreviation field and serial number/year components), 15, 16, 18, 19, plus checkbox widgets for Domestic/Imported and application type. Applications submitted through TTB's COLAs Online system are completed digitally, so a substantial share of real-world submissions will retain these field values intact.

| Option | Method | Speed | Cost/app | Accuracy | Handles scanned PDFs? |
|--------|--------|-------|----------|----------|----------------------|
| A (original) | Claude Vision, full PDF, single pass | 1–3s | 1 API call | High, but probabilistic (OCR-style errors possible on names/numbers) | Yes |
| B | `pdfplumber` text-layer extraction only | <200ms | $0 | Medium — reading-order and checkbox-state ambiguity on a multi-column form | No |
| C | AcroForm field read (`pypdf`) | <10ms | $0 | Exact — 100% (verbatim submitted values, real checkbox booleans) | No — fields are empty/absent if the PDF was flattened or scanned |
| **D — chosen** | **Tiered: C → B → A** | <10ms typical, up to 1–3s on fallback | $0 typical; A only as fallback | Best of all — exact when possible, AI only when necessary | Yes — graceful fallback to A |

**Decision:** Adopt Option D. Each form field is resolved by the first tier that returns a usable (non-null) value: (1) AcroForm field read, (2) `pdfplumber` text-layer extraction mapped to known field regions for the F 5100.31 (04/2023) layout, (3) Claude Vision (current Stage 3 design, unchanged as the universal fallback). The extraction method used for each field is recorded alongside its confidence score (FR-016): Tier 1 → 1.0, Tier 2 → ~0.90–0.95 (typical OCR/text-layer reliability), Tier 3 → Claude's self-reported confidence.

**Impact:** Frees nearly all of the PR-001 5-second budget for Stage 4, since the common case (digitally-filled PDF) resolves Stage 3 in single-digit milliseconds. Stage 3's *output* schema (Section 3.2) is unchanged — every Part I field is still extracted, null-handled, and confidence-scored — only the extraction *method* varies per field. Adds `pypdf` as a new dependency (Section 4.1) and new assumption A-20 (Section 5). Guarantees the system still works end-to-end on any submitted PDF, including fully scanned applications, via the Tier 3 fallback.

#### TS-02: Label Image Extraction Method (Stage 4)

**Question:** Should Stage 4 rely solely on Claude Vision (original design), or can local computer vision/OCR complement it — specifically to address FR-21 (degraded label images: angle, glare, lighting — currently an unaddressed "nice-to-have") and the annotation-precision limitation noted in A-13 (location hints are coarse, exact pixel coordinates deferred to "production, needs Azure Document Intelligence")?

| Option | Method | Semantic field identification | Annotation precision | Degraded-image handling | Cost/latency |
|--------|--------|-------------------------------|----------------------|--------------------------|--------------|
| A (original) | Claude Vision only | Excellent — understands layout, distinguishes brand vs. fanciful name vs. marketing copy | Coarse — qualitative `location_hint` strings only | None — raw image sent as-is | 1 API call/image |
| B | OCR/CV only, no AI | Poor — produces a bag of text with no semantic labels; fails on stylized/decorative label fonts and logos | Good — pixel bounding boxes from OCR | Possible with preprocessing | $0, but **rejected** — AI vision is a hard requirement and is genuinely better at semantic categorization |
| **C — chosen** | **Claude Vision (semantic, unchanged) + OpenCV preprocessing + OCR bounding-box assist, run concurrently** | Excellent (Claude, unchanged) | Precise — OCR-detected pixel bounding boxes fuzzy-matched to Claude's extracted field values | OpenCV deskew/perspective-correction/CLAHE contrast/glare reduction applied before the Claude call | 1 API call/image + local CPU pass (<1s, run in parallel — does not add to wall-clock time) |

**Decision:** Adopt Option C. Three additions to the existing Stage 4 design, all running locally and concurrently with the per-image Claude Vision call (so PR-001's 5-second budget, and A-19's per-application concurrency model, are unaffected):

1. **OpenCV preprocessing** (deskew via contour/perspective correction, CLAHE contrast normalization, glare suppression) is applied to every label image *before* it is sent to Claude — directly addresses FR-21, which previously had no concrete implementation plan.
2. **OCR bounding-box assist** (`pytesseract`/Tesseract) runs in parallel with the Claude Vision call, producing raw text plus pixel bounding boxes. Post-processing fuzzy-matches each of Claude's extracted field values against the OCR text to recover a real pixel-coordinate `bbox` for that element — resolving A-13's annotation-precision gap **in the prototype**, without Azure Document Intelligence.
3. **Government Warning size/weight corroboration:** OCR-measured text height of "GOVERNMENT WARNING:" relative to surrounding body text provides an objective ratio that corroborates Claude's qualitative `header_caps_bold` assessment (FR-035) — strengthening the highest-stakes compliance check (Jenny Park's top concern), partially resolving A-07.

**Impact:** Adds `opencv-python` and `pytesseract` (+ Tesseract OCR engine binary) as new dependencies (Section 4.1). Stage 4's per-element output schema (Section 3.2) gains an optional `bbox` field (pixel rect: `{x, y, w, h}`), populated when OCR finds a confident match; when it doesn't, the frontend falls back to the existing qualitative `location_hint`. New assumption A-21 (Section 5). A-07 and A-13 are updated from "deferred to production" to "addressed in prototype, with stated limits" (Section 5).

---

### 3.2 Six-Stage Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AGENT DASHBOARD                                  │
│  Application Queue → Batch Select → [Process] → Results View       │
└──────────────────┬──────────────────────────────┬───────────────────┘
                   │                              │
         ┌─────────▼──────────┐        ┌─────────▼──────────┐
         │   STAGE 1 & 2      │        │    STAGE 6         │
         │   Ingestion        │        │    Reports         │
         │  form PDF + image  │        │ Approve/Deny/Exempt │
         │  → workingfiles DB │        │  batch summary     │
         └─────────┬──────────┘        └─────────▲──────────┘
                   │                              │
         ┌─────────▼──────────┐        ┌─────────┴──────────┐
         │   STAGE 3          │        │    STAGE 5         │
         │   Form Assessment  │        │    Comparison      │
         │  Claude Text API   │        │  form params vs    │
         │  → form_parameters │        │  label params      │
         └─────────┬──────────┘        └─────────▲──────────┘
                   │                              │
         ┌─────────▼──────────────────────────────┴──────────┐
         │                    STAGE 4                         │
         │              Label Assessment                      │
         │         Claude Vision API (image)                  │
         │              → label_parameters                    │
         └────────────────────────────────────────────────────┘
```

---

#### Stage 1 — Ingest Application Form

- Accept TTB F 5100.31 PDF upload (single or batch)
- Record in `applications` table: file path, upload timestamp, status = `PENDING`
- Accept manual metadata override (serial number, applicant name) for dashboard display before extraction completes

#### Stage 2 — Ingest Label Artwork

- Accept image upload(s), associated with an application by serial number or UI pairing
- One application may have multiple label images (brand label, back label, neck label)
- Store in `label_images` table: image path, application_id, upload timestamp
- Status → `PENDING_ASSESSMENT`

#### Stage 3 — Form Assessment

**Method (per TS-01, Section 3.1):** Each of the 18 Part I fields (Items 1–18, including 8a) is resolved by the first applicable tier, not a single Claude pass:

1. **Tier 1 — AcroForm field read (`pypdf`, <10ms, $0, confidence 1.0):** `f510031.pdf` is a fillable AcroForm with 44 named fields (TS-01 finding). If the submitted PDF retains these fields with non-empty values — the case for applications completed via TTB's COLAs Online — read them directly.
2. **Tier 2 — `pdfplumber` text-layer extraction (<200ms, $0, confidence ≈0.90–0.95):** For fields not resolved in Tier 1 (flattened PDFs, or scans that retain a text layer), extract the text layer and map known regions of the F 5100.31 (04/2023) layout to fields.
3. **Tier 3 — Claude Vision (1–3s, fallback only, confidence = Claude's self-reported value):** For fields still unresolved (fully scanned/image-only PDFs, or ambiguous text-layer regions), send the form PDF to Claude, prompting for structured JSON extraction of every Part I field in a single pass (FR-010).

Fields blank on the form are extracted as `null`, never omitted (FR-011), regardless of which tier resolves them. The tier that resolved each field is recorded as its `extraction_method` (FR-017).

**Output schema (per application):**
```json
{
  "representative_id": "...",
  "plant_registry_number": "BW-...",
  "source": "domestic|imported",
  "serial_number": "26-1",
  "product_type": "wine|distilled_spirits|malt_beverages",
  "brand_name": "...",
  "fanciful_name": "...",
  "applicant_name": "...",
  "applicant_address": "...",
  "mailing_address": "...",
  "formula_id": "...",
  "grape_varietals": [...],
  "wine_appellation": "...",
  "phone_number": "...",
  "email_address": "...",
  "application_type": {
    "checked": ["14a"],
    "exemption_state": null,
    "container_capacity": null,
    "prior_ttb_id": null
  },
  "embossed_info": "...",
  "foreign_translations": "...",
  "date_of_application": "...",
  "signature_present": true,
  "applicant_printed_name": "...",
  "confidence_scores": {
    "plant_registry_number": 0.97,
    "brand_name": 0.99,
    "...": "one entry per field above (FR-016)"
  },
  "extraction_methods": {
    "plant_registry_number": "acroform",
    "brand_name": "acroform",
    "...": "one entry per field above — acroform | pdftext | ai_vision (TS-01, A-20, FR-017)"
  }
}
```

Store in `form_parameters`, including each field's `extraction_method` (Section 3.4). Status → `FORM_ASSESSED`.

#### Stage 4 — Label Assessment

**Method (per TS-02, Section 3.1):** For **every label image** associated with the application (FR-030) — brand, back, neck, or other — three things happen per image, with the local CV/OCR work running concurrently with the Claude call so neither adds wall-clock time:

1. **OpenCV preprocessing** (deskew/perspective correction, CLAHE contrast normalization, glare suppression) is applied to the raw image first — addresses FR-039's degraded-image scenarios (angle, glare, lighting), the formalized successor to the original FR-21 "nice-to-have" (Section 2.1).
2. The preprocessed image is sent to **Claude Vision API** independently, prompted for structured JSON extraction of **everything visible on that image** in a single pass — all TTB-required mandatory elements (FR-031), all comparison-relevant secondary elements (FR-032), and any remaining text as a generic catch-all (FR-033) — not just the fields used in comparison.
3. **In parallel**, OCR (`pytesseract`/Tesseract, FR-040) runs against the preprocessed image, producing raw text plus pixel bounding boxes. Each of Claude's extracted field values is fuzzy-matched against the OCR text to recover a pixel `bbox` for that element, and the OCR-measured text height of "GOVERNMENT WARNING:" relative to surrounding body text is recorded as `header_height_ratio`, corroborating Claude's `header_caps_bold` assessment (FR-035, A-07).

Per A-11/A-19, the per-image Claude Vision calls for one application are issued concurrently to stay within the PR-001 5-second budget; the OpenCV/OCR pass for each image runs locally and concurrently with that image's Claude call.

**Per-image output schema:**
```json
{
  "label_image_id": 42,
  "label_type": "brand|back|neck|other",
  "brand_name": {"value": "...", "confidence": 0.98, "location_hint": "top-center", "bbox": {"x": 120, "y": 40, "w": 300, "h": 60}},
  "fanciful_name": {"value": "...", "confidence": 0.95, "location_hint": "...", "bbox": null},
  "class_type_designation": {"value": "...", "confidence": 0.97, "location_hint": "...", "bbox": {"x": 80, "y": 200, "w": 250, "h": 30}},
  "alcohol_content": {"value": "...", "confidence": 0.99, "location_hint": "...", "bbox": {"x": 80, "y": 240, "w": 100, "h": 24}},
  "net_contents": {"value": "...", "confidence": 0.99, "location_hint": "...", "bbox": {"x": 300, "y": 240, "w": 90, "h": 24}},
  "bottler_name": {"value": "...", "confidence": 0.96, "location_hint": "...", "bbox": {"x": 60, "y": 420, "w": 280, "h": 22}},
  "bottler_address": {"value": "...", "confidence": 0.94, "location_hint": "...", "bbox": {"x": 60, "y": 444, "w": 280, "h": 22}},
  "country_of_origin": {"value": "...", "confidence": 0.97, "location_hint": "...", "bbox": null},
  "government_warning": {
    "text_present": true,
    "header_caps_bold": true,
    "header_height_ratio": 1.05,
    "text_exact_match": true,
    "text_found": "GOVERNMENT WARNING: ...",
    "confidence": 0.99,
    "location_hint": "bottom",
    "bbox": {"x": 30, "y": 480, "w": 440, "h": 90}
  },
  "grape_varietals": {"value": [...], "confidence": 0.95, "location_hint": "...", "bbox": null},
  "wine_appellation": {"value": "...", "confidence": 0.94, "location_hint": "...", "bbox": null},
  "vintage_date": {"value": "...", "confidence": 0.93, "location_hint": "...", "bbox": null},
  "age_statement": {"value": "...", "confidence": 0.92, "location_hint": "...", "bbox": null},
  "for_sale_in_state": {"value": "...", "confidence": 0.98, "location_hint": "...", "bbox": null},
  "other_text": [
    {"value": "UPC: 012345678905", "confidence": 0.90, "location_hint": "bottom", "bbox": {"x": 200, "y": 510, "w": 120, "h": 18}},
    {"value": "Drink Responsibly", "confidence": 0.92, "location_hint": "center", "bbox": null}
  ]
}
```

`bbox` is populated when OCR finds a confident fuzzy-match for that element's extracted text on the preprocessed image; when it doesn't (e.g., logos or stylized brand marks with no OCR-readable text), `bbox` is `null` and the frontend falls back to the qualitative `location_hint` for annotation placement (A-13). `header_height_ratio` is only meaningful on `government_warning` and is `null` if OCR could not isolate the header text.

Fields with no corresponding element on this image are returned with `"value": null` rather than omitted, mirroring FR-011 on the form side. `other_text` may be an empty array. Every field is written to `label_parameters` as one row per `(label_image_id, field_name)`, so the same field may have multiple rows across images (FR-038).

**Aggregation:** once all of an application's images have been extracted, Stage 5 queries `label_parameters` across all `label_image_id`s for the application — there is no separate merge step or table; "does the label set contain X" is simply "does any row for this application have `field_name = X` and a non-null value."

Store in `label_parameters`. Status → `LABEL_ASSESSED` once all images for the application have been processed.

#### Stage 5 — Comparison

Apply comparison matrix (Section 2.6) to each field pair. For each form field, search `label_parameters` across **all** of the application's `label_image_id`s (FR-038) — a field is "on the label" if any image reports a non-null value for it.

Per-field result:
```
MATCH            — a value agreeing with the form (within tolerance) is found on at least one label image
HARD_FAILURE     — mandatory mismatch not in Allowable Revisions, on every image where the field appears (or absent from all)
POSSIBLE_ALLOWABLE — mismatch present but falls within Section V revision types
MISSING_FROM_LABEL — field required but not found on ANY of the application's label images
MISSING_FROM_FORM  — field not present on form (N/A or optional)
```

**Multi-image resolution (A-10):** if any image's value matches the form → `MATCH`, with `label_image_id` set to that image (used for annotation placement). If the field appears on one or more images but none match → classify the mismatch (`HARD_FAILURE`/`POSSIBLE_ALLOWABLE`) using the highest-confidence non-null candidate, with `label_image_id` set accordingly. If no image reports the field at all → `MISSING_FROM_LABEL`.

Government Warning check:
1. Is the warning present on any label image? → if not: HARD_FAILURE
2. On the image where it is found, is "GOVERNMENT WARNING:" in ALL CAPS and BOLD? → if not: HARD_FAILURE
3. Does its text match statutory 27 CFR § 16.21 text? → if not: HARD_FAILURE

Brand name check:
1. Normalize: strip whitespace, lowercase, collapse punctuation
2. If any image's normalized value matches the form → MATCH
3. If no image matches → evaluate the closest candidate: is it a case/punctuation-only difference → POSSIBLE_ALLOWABLE; otherwise HARD_FAILURE

Type 14b check:
- If 14b checked and product_type is "malt_beverages" → HARD_FAILURE (exemptions not issued for malt)
- If 14b checked and source is "imported" → HARD_FAILURE (exemptions not issued for imports)
- If 14b checked → at least one label image must contain "For sale in [STATE] only"

Store all results in `comparisons`. Status → `COMPARED`.

#### Stage 6 — Determination Report

**Logic:**
```
if any HARD_FAILURE → recommendation = DENY
  → list all hard failures with field names and values
else if any POSSIBLE_ALLOWABLE → recommendation = RECOMMEND_EXEMPTION_REVIEW
  → list allowable-revision candidates with applicable Section V item numbers
else → recommendation = APPROVE
```

**Report structure per application:**
```json
{
  "application_id": "...",
  "serial_number": "...",
  "brand_name": "...",
  "recommendation": "APPROVE|DENY|RECOMMEND_EXEMPTION_REVIEW",
  "parameter_results": [
    {
      "field": "brand_name",
      "form_value": "OLD TOM DISTILLERY",
      "label_value": "Old Tom Distillery",
      "result": "POSSIBLE_ALLOWABLE",
      "section_v_reference": "3b",
      "note": "Case difference only — Allowable Revision per F 5100.31 Section V item 3b"
    },
    ...
  ],
  "hard_failures": [...],
  "allowable_revisions_flagged": [...],
  "overall_confidence": 0.97,
  "processed_at": "2026-06-09T14:58:00Z"
}
```

**Batch summary report:**
- Total processed, Approved count, Denied count, Exemption Review count
- Sorted list of applications with individual results
- Common failure types across batch (for pattern detection)

Store in `determinations`. Status → `COMPLETE`.

---

### 3.3 UI Architecture

#### Agent Dashboard

```
┌──────────────────────────────────────────────────────────────────┐
│  TTB Label Verification System           [Agent: Sarah Chen ▾]   │
├──────────────────────────────────────────────────────────────────┤
│  Pending Applications (47)                        [Upload New +] │
├──────────────────────────────────────────────────────────────────┤
│  ☐  Filter by applicant: [________________]  Sort: [Date ▾]     │
├─────┬──────────────────┬──────────┬──────────┬──────────────────┤
│  ☑  │ Old Tom Distillery│ 26-1    │ Spirits  │ ● Pending        │
│  ☑  │ Old Tom Distillery│ 26-2    │ Spirits  │ ● Pending        │
│  ☐  │ Blue Ridge Winery │ 26-14   │ Wine     │ ● Pending        │
│  ☐  │ Blue Ridge Winery │ 26-15   │ Wine     │ ● Pending        │
│  ☐  │ Metro Brewing Co  │ 26-8    │ Malt     │ ✅ Approved      │
├─────┴──────────────────┴──────────┴──────────┴──────────────────┤
│  [☑ Process Selected (2)]                                        │
└──────────────────────────────────────────────────────────────────┘
```

#### Batch Processing State

While processing, a progress panel replaces the button:
- Progress bar: "Processing 2 of 2..."
- Individual application spinners
- On completion: dashboard refreshes with result badges

#### Application Detail View (Post-Processing)

```
┌──────────────────────────────────────────────────────────────────┐
│  App 26-1 · Old Tom Distillery · Spirits   [ ❌ DENY ]  [< Back]│
├────────────────────────────────┬─────────────────────────────────┤
│  TTB FORM F 5100.31            │  LABEL ARTWORK                  │
│  ┌──────────────────────────┐  │  ┌───────────────────────────┐  │
│  │  Brand: OLD TOM DIST...  │  │  │                           │  │
│  │  [red ellipse on field]  │  │  │   [image with red ellipse │  │
│  │  Type: Distilled Spirits │  │  │    on brand name area]    │  │
│  │  ABV: 45% Alc./Vol.      │  │  │                           │  │
│  │  ...                     │  │  └───────────────────────────┘  │
│  └──────────────────────────┘  │                                 │
├────────────────────────────────┴─────────────────────────────────┤
│  PARAMETER RESULTS                                               │
│  ✅ Brand Name      MATCH       "Old Tom Distillery" (case ok)   │
│  ✅ Product Type    MATCH       Distilled Spirits                │
│  ✅ ABV             MATCH       45% Alc./Vol.                    │
│  ❌ Govt Warning    HARD FAIL   Header not in ALL CAPS BOLD      │
│  ✅ Net Contents    MATCH       750 mL                           │
│  ✅ Bottler Address MATCH       123 Main St, Louisville KY       │
├──────────────────────────────────────────────────────────────────┤
│  SUMMARY: 1 hard failure · Recommendation: DENY                  │
│  [Override Recommendation ▾]   [Finalize]                       │
└──────────────────────────────────────────────────────────────────┘
```

**Annotation behavior:**
- Red ellipses rendered as SVG overlays on both the PDF renderer and the image viewer
- SVG overlay coordinates derived from `location_hint` values in `label_parameters` (relative: top/bottom/left/center/etc.) and from form field bounding boxes
- Mouse-over on a red ellipse: corresponding ellipse on opposite panel glows yellow (cross-document highlight)
- Right-click on any parameter row: context menu → "Override this determination" → modal with reason field

#### Batch Report View

```
┌──────────────────────────────────────────────────────────────────┐
│  Batch Report · Processed 2026-06-09 14:58                       │
│  ✅ Approved: 0  ❌ Denied: 2  ⚠️ Exemption Review: 0            │
├──────────────────────────────────────────────────────────────────┤
│  App 26-1 · Old Tom Distillery    ❌ DENY   [View Details]       │
│  App 26-2 · Old Tom Distillery    ❌ DENY   [View Details]       │
├──────────────────────────────────────────────────────────────────┤
│  Common failures: Government Warning format (2 apps)             │
│  [Export CSV]  [Export PDF Report]                               │
└──────────────────────────────────────────────────────────────────┘
```

---

### 3.4 Database Schema (SQLite — workingfiles DB)

```sql
-- Agents (simple auth for prototype)
CREATE TABLE agents (
    id          INTEGER PRIMARY KEY,
    username    TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Applications (one per TTB F 5100.31 form)
CREATE TABLE applications (
    id              INTEGER PRIMARY KEY,
    serial_number   TEXT,
    year            TEXT,
    form_path       TEXT,
    product_type    TEXT,   -- wine|distilled_spirits|malt_beverages
    source          TEXT,   -- domestic|imported
    brand_name      TEXT,
    applicant_name  TEXT,
    application_type TEXT,  -- 14a|14b|14c|14d
    assigned_agent_id INTEGER REFERENCES agents(id),
    status          TEXT DEFAULT 'PENDING',  -- PENDING|FORM_ASSESSED|LABEL_ASSESSED|COMPARED|COMPLETE
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at    DATETIME,
    -- COLA Public Registry forward-compat fields (Section 6, A-22) — populated from the
    -- form/label extraction where derivable; not validated against any live registry
    ttb_id              TEXT,   -- 14-digit TTB ID (Section 6.2)
    vendor_code         TEXT,   -- portion of TTB ID identifying the submitting vendor
    class_type_code     TEXT,   -- COLA Class/Type Code (Section 6.2)
    origin_code         TEXT,   -- COLA Origin Code (Section 6.2)
    registry_status     TEXT,   -- approved|expired|surrendered|revoked (Section 6.2) — N/A for a not-yet-submitted application
    total_bottle_capacity TEXT, -- COLA "Total Bottle Capacity" field
    for_sale_in_state   TEXT,   -- registry-level "For Sale In" state, distinct from the per-image label_parameters.for_sale_in_state used in Stage 5 comparison
    qualifications      TEXT    -- COLA "Qualifications" free text (distinct from the AcroForm "FOR TTB USE ONLY - QUALIFICATIONS" field, which is captured via form_parameters)
);

-- Label images (multiple per application)
CREATE TABLE label_images (
    id              INTEGER PRIMARY KEY,
    application_id  INTEGER REFERENCES applications(id),
    image_path      TEXT,
    label_type      TEXT,   -- brand|back|neck|other
    uploaded_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Extracted form parameters
CREATE TABLE form_parameters (
    id              INTEGER PRIMARY KEY,
    application_id  INTEGER REFERENCES applications(id),
    field_name      TEXT,
    field_value     TEXT,
    confidence      REAL,
    extraction_method TEXT,  -- acroform|pdftext|ai_vision (TS-01, A-20) — which tier resolved this field
    extracted_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Extracted label parameters
CREATE TABLE label_parameters (
    id              INTEGER PRIMARY KEY,
    application_id  INTEGER REFERENCES applications(id),
    label_image_id  INTEGER REFERENCES label_images(id),
    field_name      TEXT,
    field_value     TEXT,
    confidence      REAL,
    location_hint   TEXT,  -- relative position for annotation placement (fallback, A-13)
    bbox_json       TEXT,  -- {"x":.., "y":.., "w":.., "h":..} from OCR fuzzy-match (TS-02, A-13/A-21); NULL if no confident match
    header_height_ratio REAL, -- government_warning only: OCR text-height ratio corroborating header_caps_bold (TS-02 #3, A-07); NULL otherwise
    extracted_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Per-field comparison results
CREATE TABLE comparisons (
    id              INTEGER PRIMARY KEY,
    application_id  INTEGER REFERENCES applications(id),
    field_name      TEXT,
    form_value      TEXT,
    label_value     TEXT,
    result          TEXT,  -- MATCH|HARD_FAILURE|POSSIBLE_ALLOWABLE|MISSING_FROM_LABEL|MISSING_FROM_FORM
    section_v_ref   TEXT,  -- e.g., "3b" if allowable revision applies
    note            TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Overall determinations (one per application)
CREATE TABLE determinations (
    id                  INTEGER PRIMARY KEY,
    application_id      INTEGER REFERENCES applications(id),
    recommendation      TEXT,  -- APPROVE|DENY|RECOMMEND_EXEMPTION_REVIEW
    hard_failures_json  TEXT,
    allowable_json      TEXT,
    agent_override      TEXT,  -- null|APPROVE|DENY|RECOMMEND_EXEMPTION_REVIEW
    override_by         INTEGER REFERENCES agents(id),
    override_reason     TEXT,
    override_at         DATETIME,
    finalized_at        DATETIME,
    created_at          DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Batch processing runs
CREATE TABLE batches (
    id              INTEGER PRIMARY KEY,
    name            TEXT,
    application_ids TEXT,  -- JSON array
    approved_count  INTEGER DEFAULT 0,
    denied_count    INTEGER DEFAULT 0,
    exemption_count INTEGER DEFAULT 0,
    summary_json    TEXT,
    created_by      INTEGER REFERENCES agents(id),
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME
);
```

---

### 3.5 API Surface (FastAPI)

```
POST   /auth/login                          → JWT token
GET    /applications                         → paginated list (filtered by agent)
POST   /applications/upload                  → upload form PDF + label images
GET    /applications/{id}                    → full application detail
GET    /applications/{id}/comparisons        → per-field results
POST   /applications/{id}/process            → trigger single-app pipeline
POST   /batch/process                        → { application_ids: [...] }
GET    /batch/{id}/status                    → processing status + results
GET    /batch/{id}/report                    → batch summary report
POST   /determinations/{id}/override         → { field, override_value, reason }
POST   /determinations/{id}/finalize         → save final agent determination
```

---

## 4. Tools & Technology Rationale

### 4.1 Technology Stack

| Layer | Tool / Library | Version | Purpose | Rationale |
|-------|----------------|---------|---------|-----------|
| **Backend** | Python | 3.11+ | Primary language | Mature AI/data ecosystem; fast to prototype |
| **Backend** | FastAPI | latest | REST API server | Async, fast, auto-generates OpenAPI docs |
| **Backend** | SQLAlchemy | 2.x | ORM | Clean DB access; easy migration to PostgreSQL |
| **Backend** | SQLite | built-in | Database | Zero-setup for prototype; file-based persistence |
| **Backend** | Anthropic Python SDK | latest | Claude API client | Official SDK |
| **Backend** | Claude Sonnet (claude-sonnet-4-6) | claude-sonnet-4-6 | Form + label AI extraction | Sub-3s response; handles degraded images; structured JSON output via tool use |
| **Backend** | pypdf | latest | AcroForm field extraction | Tier 1 of TS-01's tiered Stage 3 extraction — reads the F 5100.31's 44 named form fields directly when populated |
| **Backend** | pdfplumber | latest | PDF text extraction | Tier 2 of TS-01's tiered Stage 3 extraction — text-layer fallback for flattened PDFs |
| **Backend** | Pillow | latest | Image preprocessing | Format normalization before API submission |
| **Backend** | opencv-python | latest | Label image preprocessing | TS-02 — deskew/perspective correction, CLAHE contrast normalization, glare suppression before Stage 4's Claude Vision call (FR-039) |
| **Backend** | pytesseract + Tesseract OCR | latest | Label OCR bounding-box assist | TS-02 — produces text + pixel bboxes, fuzzy-matched to Claude's extracted fields for annotation placement (FR-040) and Government Warning size corroboration |
| **Backend** | python-jose + passlib | latest | JWT auth | Simple agent authentication |
| **Backend** | pytest | latest | Unit tests | Comparator and validator logic |
| **Frontend** | React + Vite | 18+ / 5+ | UI framework | Component model handles split-view, annotations, state; TypeScript support |
| **Frontend** | TypeScript | 5+ | Type safety | Prevents runtime errors in complex UI state |
| **Frontend** | Tailwind CSS | 4.x | Styling | Utility-first; fast to build clean government-appropriate UI |
| **Frontend** | react-pdf | latest | PDF rendering | Render F 5100.31 form in-browser for split view |
| **Frontend** | React Query | latest | API state management | Handles polling for batch job completion |
| **Frontend** | SVG overlay | (custom) | Visual annotations | Red ellipses over PDF and image; cross-document hover highlighting |
| **Frontend** | Vitest | latest | Frontend unit tests | Component and logic testing |
| **Deployment** | Railway | — | Backend hosting | Free tier; FastAPI + SQLite file; auto-deploy from GitHub |
| **Deployment** | Netlify | — | Frontend hosting | Free tier; static React SPA; auto-deploy from GitHub |

### 4.2 Key Design Decisions

**Decision 1: React + FastAPI over Streamlit**
- *Original choice:* Streamlit (rapid prototype)
- *Revised to:* React + FastAPI
- *Rationale:* The required UI — split-view PDF/image rendering, SVG annotation overlays, mouse-over cross-document highlighting, right-click context menus — is not achievable in Streamlit. React's component model makes these features straightforward. FastAPI provides the async processing needed for batch operations.
- *Trade-off:* More initial setup; mitigated by Vite scaffolding.

**Decision 2: Claude Vision for both form and label extraction**
- *Rationale:* F 5100.31 forms submitted as scanned PDFs may not have reliable machine-readable text. Claude Vision handles both digitally-generated and scanned PDFs as images, extracting structured data reliably. Label artwork requires vision regardless. Using one model for both simplifies the pipeline and keeps latency predictable.
- *Fallback:* pdfplumber extracts text from digitally-generated PDFs as a faster, cheaper first pass; Claude is the fallback for scanned/unclear forms.
- *Performance:* Claude typically returns in 1–3 seconds per document. Form + label extraction for one application: ~3–5 seconds total — within the hard constraint.

**Decision 3: SQLite for prototype database**
- *Rationale:* Zero setup, file-based, fully capable for prototype scale. SQLAlchemy ORM means migrating to PostgreSQL for production is a single config change.
- *Trade-off:* Not suitable for concurrent write-heavy production use.

**Decision 4: Location hints rather than pixel coordinates for annotations**
- *Rationale:* Claude Vision returns semantic location descriptions ("top-center", "bottom-left", "center") rather than exact pixel coordinates. The frontend maps these to SVG overlay regions. Exact pixel mapping would require a secondary computer-vision pass and is out of scope for prototype.
- *Production path:* Integrate a dedicated OCR engine (e.g., Azure Document Intelligence) to return exact bounding boxes.

**Decision 5: Three-tier determination (Approve / Deny / Recommend Exemption Review)**
- *Rationale:* The F 5100.31 form's Section V lists 41 types of allowable revisions. A binary Approve/Deny would over-deny legitimate applications with cosmetic differences. Mapping mismatches to Section V items enables the system to flag applications that might qualify for approval without resubmission, routing them to agent judgment rather than blanket denial.

**Decision 6: Tiered form extraction (AcroForm → pdfplumber → Claude Vision)**
- *Origin:* TS-01 (Section 3.1)
- *Rationale:* `f510031.pdf` is a 44-field fillable AcroForm, and applications submitted via TTB's COLAs Online retain those field values. Reading them directly (`pypdf`) is exact, free, and effectively instant — far better than asking a vision model to re-read values that are already present as structured data in the file. `pdfplumber` text-layer extraction covers flattened PDFs that lost their form fields but kept selectable text. Claude Vision remains the universal fallback for fully scanned, image-only submissions.
- *Trade-off:* Three extraction code paths to maintain instead of one, and the `pdfplumber`/AcroForm field-name mappings are tied to the F 5100.31 (04/2023) layout (A-20) — a future form revision would require remapping. Mitigated by Claude Vision always being available as a correctness backstop.

**Decision 7: OpenCV preprocessing + OCR bounding-box assist for label images**
- *Origin:* TS-02 (Section 3.1)
- *Rationale:* Claude Vision remains the sole source of *semantic* label understanding (brand vs. fanciful name vs. marketing copy) — OCR alone cannot do this reliably on stylized label fonts and logos. But OCR run alongside Claude, on an OpenCV-preprocessed image, gives the system two things it lacked: (1) a concrete handling of degraded images (deskew, glare, contrast) that FR-21 had previously left as an unaddressed nice-to-have, and (2) real pixel bounding boxes for SVG annotations, fuzzy-matched to Claude's field values, instead of the coarse `location_hint` strings.
- *Trade-off:* Adds two new dependencies (`opencv-python`, `pytesseract` + the Tesseract binary) and a fuzzy-matching step that can fail to find a `bbox` for some elements (logos, decorative text) — handled by falling back to `location_hint` (A-13) rather than blocking on a match.

---

## 5. Assumptions

| ID | Assumption | Basis |
|----|-----------|-------|
| A-01 | Internet access available for the deployed prototype | Marcus Williams: firewall concern is for production; prototype is standalone |
| A-02 | Anthropic API key provisioned for deployment | Required for Claude Vision; cost negligible at prototype usage |
| A-03 | No COLA system integration | Marcus Williams: explicitly out of scope for prototype |
| A-04 | Label images are JPEG, PNG, or WebP | Standard format for digital label submissions |
| A-05 | Government Warning text is 27 CFR § 16.21 statutory statement | TTB regulation; confirmed by Jenny Park |
| A-06 | Case/punctuation brand name differences are POSSIBLE_ALLOWABLE, not hard failures | Dave Morrison's "STONE'S THROW" example; Section V item 3b |
| A-07 | Font size/weight of "GOVERNMENT WARNING:" is assessed primarily by Claude's qualitative `header_caps_bold` judgment, corroborated (not replaced) by an OCR-measured `header_height_ratio` (TS-02 #3) — a definitive px measurement still requires a known physical-to-pixel scale, which the prototype does not have | Vision models describe relative appearance reliably; OCR adds an objective height-ratio signal for the highest-stakes check (Jenny Park's top concern) without claiming exact px measurement |
| A-08 | Application forms are submitted as PDF files in TTB F 5100.31 format | f510031.pdf provided as the source form |
| A-09 | Label images are paired with application forms by manual association in the upload UI | No automatic barcode-based pairing in prototype |
| A-10 | One application may have multiple label images (brand/back/neck) | Common in practice; per FR-030/FR-038, ALL images are extracted independently and a required field is satisfied if found on ANY image — there is no single "primary" comparison image |
| A-11 | Agent authentication is username/password (no SSO/LDAP for prototype) | Marcus Williams: standalone POC; complex auth is production concern |
| A-12 | Exemption logic is based on Section V Allowable Revisions and Type 14b applications | F 5100.31 form instructions |
| A-13 | SVG annotation locations use an OCR-derived pixel `bbox` (TS-02 #2) when a confident fuzzy-match exists between Claude's extracted field value and the OCR text; otherwise they fall back to AI `location_hint` strings (approximate region only) | OCR bounding-box assist resolves the precision gap for most printed text in the prototype; logos, decorative fonts, and stylized brand marks have no OCR-readable text and still rely on `location_hint`. A production system handling 100% of cases would still benefit from a dedicated service like Azure Document Intelligence |
| A-14 | Agent override is recorded with reason but does not re-run the AI pipeline | Override is a manual correction layer on top of AI output |
| A-15 | Country of origin check applies only when Item 3 is checked "Imported" | Domestic products not required to show country of origin |
| A-16 | The prototype handles Type 14a and 14b applications; 14c (distinctive bottle) and 14d (resubmission) are noted but not fully validated | Time-constraint prioritization; 14c/14d are edge cases |
| A-17 | Batch processing is sequential (one application at a time) with a progress indicator | Prototype scope; production would use async task queue (Celery/RQ) |
| A-18 | When a required field's value is found on multiple label images with differing values, any image whose value matches the form satisfies the requirement (MATCH); only when no image matches is a discrepancy reported, using the highest-confidence non-null candidate for the failure report and annotation | Real labels legitimately repeat (or vary) text across front/back/neck panels — penalizing an application because one panel differs while another matches would be a false failure |
| A-19 | Within a single application, the per-image Stage 4 vision calls are issued concurrently (not sequentially) so total label-extraction time stays within the PR-001 5-second budget regardless of image count | Sequential per-image calls would multiply latency linearly with the number of label images submitted |
| A-20 | The AcroForm field-name mapping (TS-01 Tier 1) and the `pdfplumber` region mapping (TS-01 Tier 2) are maintained for the F 5100.31 (04/2023) revision specifically; a future form revision with renamed/relocated fields would require updating both mappings, with Claude Vision (Tier 3) covering the gap until they're updated | `f510031.pdf` (04/2023) is the only form revision provided for this assessment |
| A-21 | The OpenCV preprocessing and OCR bounding-box pass (TS-02) run locally on the backend, concurrently with each image's Claude Vision call, and do not themselves call any external API | Keeps PR-001's 5-second budget and A-19's concurrency model unaffected — these are additive local CPU passes, not additional network round-trips |
| A-22 | The `applications` table carries TTB COLA Public Registry fields (TTB ID, Vendor Code, Class/Type Code, Origin Code, registry status, etc., Section 6) so that data extracted in this prototype is structurally compatible with a future COLAs Online integration, but no live connection to `ttbonline.gov` exists or is attempted | Per A-03/NFR-05/CR-001 (no COLA integration in prototype); forward-compatible schema reduces future integration effort without expanding current scope |

---

## 6. COLA Registry & Future Integration Reference

**Per A-03/NFR-05/CR-001, this prototype does NOT connect to the TTB COLA Public Registry or COLAs Online — no network calls to `ttbonline.gov` are made anywhere in this system.** This section exists purely as a forward-compatibility reference: applicants complete F 5100.31 submissions through COLAs Online, and a production version of TTB-LVS would plausibly *receive* applications from, or *query*, that system. Documenting its data model now lets the prototype's database schema (Section 3.4) capture the same fields without loss, so a future integration is a matter of wiring a connection — not redesigning the schema.

**Sources** (publicly accessible, no login required):
- TTB COLA Public Registry overview — https://www.ttb.gov/regulated-commodities/labeling/cola-public-registry
- Public COLA Search (basic) — https://www.ttbonline.gov/colasonline/publicSearchColasBasic.do
- Example COLA record (Budweiser, TTB ID 25211001000227) — https://ttbonline.gov/colasonline/viewColaDetails.do?action=publicDisplaySearchBasic&ttbid=25211001000227

### 6.1 COLA Record Data Model

Fields observed on a COLA registry detail record (`viewColaDetails.do`):

| Field | Example value | Description |
|-------|---------------|-------------|
| TTB ID | `25211001000227` | 14-digit unique identifier assigned by TTB on submission. Encodes submission year/date and a sequence number. |
| Status | `APPROVED` | Registry lifecycle state. Observed values include `APPROVED`, `EXPIRED`, `SURRENDERED`, `REVOKED`. |
| Vendor Code | `17931` | Numeric code identifying the submitting vendor/permittee in COLAs Online. |
| Serial # | `25B003` | Applicant-assigned serial number — same value as F 5100.31 Item 2. |
| Class/Type Code | `BEER` | TTB class/type classification (numeric code + description in the full registry; the public detail view shows the description). |
| Origin Code | `MISSOURI` | State of production for domestic products, or country of origin for imports. |
| Brand Name | `BUDWEISER` | Same as F 5100.31 Item 6. |
| Fanciful Name | *(blank in example)* | Same as F 5100.31 Item 7. |
| Type of Application | `LABEL APPROVAL` | Descriptive form of F 5100.31's 14a–d application type checkboxes. |
| For Sale In | *(blank in example)* | State restriction, populated when Item 14b ("for sale in [STATE] only") applies. |
| Total Bottle Capacity | *(blank in example)* | Container size declared on the application. |
| Formula | *(blank in example)* | Formula ID — same concept as F 5100.31 Item 9 (`formula_id`). |
| Approval Date | `07/31/2025` | Date TTB approved the COLA. |
| Qualifications | `EACH CONTAINER MUST BE CODED TO INDICATE ACTUAL PLACE OF BOTTLING.` | Free-text conditions attached to the approval. |
| Plant Registry/Basic Permit/Brewer's No. (Principal Place of Business) | `BR-MO-20000`, Anheuser-Busch LLC, 1 Busch Pl, Saint Louis, MO 63118 | Permit number + name + address for the primary production location — same concept as F 5100.31 Item 8. |
| Plant Registry/Basic Permit/Brewer's No. (Other) | 11 additional `BR-XX-#####` entries with name + address, in the example record | **Repeating** group of additional production/bottling locations covered by the same approval. |
| Contact Information | Name + `(314) 577-2693` | Contact person and phone number for the application — same concept as F 5100.31 Items 12/13. |

### 6.2 Public Search Interface

Fields available on the public basic search (`publicSearchColasBasic.do`), useful as a model for a future "look up related COLA" feature:

| Field | Type |
|-------|------|
| Date Completed (From / To) | Date range |
| Product or Fanciful Name | Text, with radio: Brand Name / Fanciful Name / Either |
| Class/Type (From / To) | Range, with a "Lookup Class Type" code picker |
| Origin Code | Text, with a "Lookup Origin" code picker |

(TTB ID and Serial Number lookups exist as separate basic-search modes on `ttbonline.gov` but were not captured in this reference pass — out of scope since no integration is planned.)

### 6.3 Forward-Compatibility Mapping (TTB-LVS Schema ↔ COLA Registry)

| COLA Registry Field | TTB-LVS Location | Status |
|---|---|---|
| TTB ID | `applications.ttb_id` | **New** (Section 3.4) |
| Status | `applications.registry_status` | **New** — not populated by this prototype (no live registry to query); reserved for future integration |
| Vendor Code | `applications.vendor_code` | **New** |
| Serial # | `applications.serial_number` | Already existed — F 5100.31 Item 2 |
| Class/Type Code | `applications.class_type_code` | **New** |
| Origin Code | `applications.origin_code` | **New** |
| Brand Name | `applications.brand_name`, `form_parameters('brand_name')` | Already existed — Item 6 |
| Fanciful Name | `form_parameters('fanciful_name')` | Already existed — Item 7 (EAV) |
| Type of Application | `applications.application_type` | Already existed — 14a–d |
| For Sale In | `applications.for_sale_in_state` (registry-level), `label_parameters('for_sale_in_state')` (per-image, used in Stage 5 comparison) | **New** column added for the registry-level value; per-image value already existed |
| Total Bottle Capacity | `applications.total_bottle_capacity` | **New** |
| Formula | `form_parameters('formula_id')` | Already existed — Item 9 (EAV) |
| Approval Date | *not mapped* | The prototype has no "TTB approval" concept; `determinations.finalized_at` is the agent's review timestamp, a different fact |
| Qualifications | `applications.qualifications` | **New** |
| Plant Registry/Permit (Principal) | `form_parameters('plant_registry_number')`, `form_parameters('applicant_address')` | Already existed — Item 8 (EAV) |
| Plant Registry/Permit (Other, repeating) | Additional `form_parameters` rows (e.g., `plant_registry_number_2`, `plant_registry_address_2`, ...) | Captured **without a schema change** if present on the form/label — `form_parameters` is an EAV table, so repeating groups need only additional `field_name` values, not new columns |
| Contact Name + Phone | `applicant_name`, `form_parameters('phone_number')`/`form_parameters('email_address')` | Already existed — Items 12/13 |

The EAV design of `form_parameters`/`label_parameters` (Section 3.4) is what makes "without loss" practical here: most COLA registry fields already have a home as a `field_name`/`field_value` pair, and repeating groups (multiple plant locations) extend naturally as additional rows. The eight new `applications` columns (Section 3.4) cover only the registry "headline" fields — TTB ID, status, codes — that a future integration would index/search/display directly, rather than every field needing its own column.

### 6.4 Future Integration Path (Out of Scope for Prototype)

A production TTB-LVS would plausibly:
1. Accept F 5100.31 submissions directly from COLAs Online (the applicant-facing system), receiving `ttb_id` and `vendor_code` at ingestion rather than deriving them.
2. Query the COLA Registry by `ttb_id` to pre-populate `registry_status`/`approval_date`/`qualifications`, and to cross-check the submitted form against the registry's record of the same application.
3. Offer a "find related COLAs" lookup using the Section 6.2 search fields (date range, brand/fanciful name, class/type code, origin code) — e.g., to surface a prior approval being revised under Section V.

None of this is implemented, called, or stubbed in the prototype — A-03/A-22 hold. This section exists solely so the schema additions in Section 3.4 are traceable to a real data model.

---

## 7. Engineering Log

### 2026-06-09 — Session 1: Assessment Intake & Initial Setup

**Completed:**
- Analyzed all three initial source documents (notification email, submission form, assessment README)
- Extracted and prioritized requirements from four stakeholder interview transcripts
- Decided initial tech stack: Python + Streamlit + Claude Vision (later revised)
- Initialized git repository: `projects/1.Active/Treasury_Assessment/`
- Created public GitHub repo: `gratefulgabe5000/ttb-label-verifier`
- Authored initial `README.md` and `_DevLog/DevLog.md`

---

### 2026-06-09 — Session 2: Form Analysis & Full Architecture Design

**New source analyzed:**
- `f510031.pdf` — TTB Form F 5100.31 (04/2023): complete field reference, application types, conditions, instructions, and Allowable Revisions table (Section V, 41 items)

**Architecture decisions made:**
- Revised tech stack from Streamlit → React + Vite + FastAPI + SQLite
  - Reason: split-view UI, SVG annotations, right-click overrides require full React frontend
- Defined 6-stage processing pipeline (Ingest Form → Ingest Label → Form Assessment → Label Assessment → Compare → Determine)
- Defined three-outcome determination logic (Approve / Deny / Recommend Exemption Review)
- Mapped all Form F 5100.31 fields to label elements (comparison matrix)
- Mapped Section V Allowable Revisions to `POSSIBLE_ALLOWABLE` classification
- Designed database schema (8 tables)
- Designed REST API surface (10 endpoints)
- Designed all three UI views (Dashboard, Detail, Batch Report)
- Updated DevLog and README to reflect revised design

**Open items for next session:**
- Scaffold React + Vite frontend project (`web/`)
- Scaffold FastAPI backend project (`app/`)
- Implement Stage 3: form assessment (Claude prompt + parser)
- Implement Stage 4: label assessment (Claude vision prompt + parser)
- Implement Stage 5: comparison engine
- Create synthetic test data: sample F 5100.31 PDFs + label images
- Write unit tests for comparison logic and government warning validator

---

### 2026-06-09 — Session 3: INCOSE PRD & Comprehensive Extraction Revision

**Completed:**
- Authored `_DevLog/PRD.md`, an INCOSE-style Product Requirements Document (Document ID `TTB-LVS-PRD-001`), covering product description, operational concept, stakeholder needs and user stories (US-001–003), system boundary, 68 SHALL requirements (FR/PR/IR/UR/SR/CR), traceability matrix, assumptions, and glossary
- **Design correction (extraction scope):** initial draft of FR-010–020 (Form Assessment) and FR-030–040 (Label Assessment) only specified extraction of the subset of fields used directly in comparison — Items 12 (Phone) and 13 (Email) were absent entirely, and several other Part I items (1, 4, 8a, 9, 15–18) were not covered
- Replaced FR-010–020 with FR-010–016: a single comprehensive-extraction requirement covering all 18 Part I items (FR-010), explicit null-handling for blank fields (FR-011), normalization/parsing requirements for fields needing structured handling (FR-012–015), and confidence scoring (FR-016)
- Replaced FR-030–040 with FR-030–036 on the same principle: one extraction pass covering all mandatory label elements (FR-030), comparison-relevant secondary elements (FR-031), and a generic `other_text` catch-all for anything else visible on the label (FR-032), plus the existing government-warning formatting checks, location hints, and confidence scoring
- Updated traceability matrix entries to `FR-010–016` and `FR-030–036`
- Updated Stage 3 and Stage 4 output schemas (Section 3.1 above) to match: Stage 3 now lists all 18 Part I fields plus a `confidence_scores` map; Stage 4 adds `grape_varietals`, `wine_appellation`, `vintage_date`, `age_statement`, and `other_text`

**Rationale:** a single comprehensive extraction pass per document — rather than re-querying for additional fields later — is both more efficient (fewer AI calls against the 5-second budget) and produces a complete digital record of each application for audit purposes, independent of which fields happen to be used in today's comparison logic.

**Design correction (multi-image label processing):** the original design treated one label image as the "primary" comparison source per application (A-10, prior wording). Corrected so that:
- FR-030–038 (Label Assessment) now require Stage 4 extraction to run independently for **every** label image associated with an application, with each extracted element tagged by its source `label_image_id`
- A required form field is satisfied if a matching value is found on **any** of the application's label images — the other images exist precisely to satisfy requirements the primary/front label doesn't carry (e.g., Government Warning and bottler address are commonly back-label content)
- FR-050, FR-053–056 (Comparison) reworded to search across the full image set rather than "the label" (singular)
- Added A-18 (multi-image value-conflict resolution: any matching image satisfies the requirement) and A-19 (per-image Stage 4 calls run concurrently to preserve the PR-001 5-second budget)
- Updated Stage 4/5 pipeline description (Section 3.1): Stage 4 now produces one extraction result per label image; Stage 5 queries across all of an application's `label_image_id`s rather than a single label dataset
- Traceability matrix updated to `FR-030–038`

**Open design question carried to Session 4 (systems engineering pass):** the Application Detail View (FR-080–090) was designed around a single form-panel/label-panel split view. With multiple label images per application, the UI needs a way to display/select among them (tabs, thumbnail strip, or stacked panels) so the agent can see which image a given annotation refers to. To be resolved during tomorrow's architecture review.

---

### 2026-06-10 — Session 4: Trade Studies & COLA Registry Reference

**Context:** Before proceeding to the planned systems-engineering pass (architecture evaluation, Mermaid diagrams, WBS), conducted two trade studies to test whether "Claude Vision for everything" — the original Stage 3/4 design — is the most effective use of AI given NFR-01's 5-second budget, or whether parts of the extraction pipeline are better served by deterministic local methods. **AI remains a hard requirement and the system's semantic core; the question was whether AI is the *best* tool for every sub-task, not whether to remove it.**

**Completed:**
- **TS-01 (Stage 3 — Form Data Extraction):** Inspected `f510031.pdf` directly and found it is a **44-field fillable AcroForm**. Adopted a tiered extraction strategy — (1) AcroForm field read via `pypdf`, (2) `pdfplumber` text-layer extraction, (3) Claude Vision as universal fallback — each field resolved by the first tier that returns a usable value, with the resolving tier recorded as `extraction_method` (FR-017). Frees nearly all of the 5-second budget for Stage 4 in the common case (digitally-completed COLAs Online submissions).
- **TS-02 (Stage 4 — Label Image Extraction):** Adopted OpenCV preprocessing (deskew, CLAHE contrast, glare suppression) before every Claude Vision call — addressing FR-21/FR-39's previously-unimplemented degraded-image handling — plus a parallel OCR (`pytesseract`/Tesseract) pass that fuzzy-matches Claude's extracted field values to recover pixel `bbox`es for SVG annotations, and computes a `header_height_ratio` for "GOVERNMENT WARNING:" as an objective corroboration of Claude's `header_caps_bold` judgment. Both additions run locally and concurrently with the per-image Claude call — A-19's concurrency model and PR-001's budget are unaffected.
- Restructured DevLog Section 3 into "System Design & Trade Studies" with both trade studies written up in full (options tables, decisions, impacts) in new **Section 3.1**; renumbered the former 3.1–3.4 to 3.2–3.5.
- Updated the Stage 3 and Stage 4 descriptions and output schemas (Section 3.2) to reflect the tiered extraction (`extraction_methods` map) and OpenCV/OCR augmentation (`bbox` and `header_height_ratio` fields).
- Updated the tech stack table (4.1) with `pypdf`, `opencv-python`, and `pytesseract` + Tesseract, and added **Decision 6** (tiered form extraction) and **Decision 7** (OpenCV/OCR label augmentation) to 4.2.
- Resolved **A-07** (Government Warning size assessment now corroborated by OCR `header_height_ratio`, not purely qualitative) and **A-13** (SVG annotations now use OCR-derived `bbox` when a confident match exists, falling back to `location_hint`); added **A-20** (form mapping is specific to F 5100.31 04/2023), **A-21** (OpenCV/OCR run locally/concurrently, no PR-001 impact), and **A-22** (COLA registry forward-compat schema, no live integration).
- Updated the `applications`, `form_parameters`, and `label_parameters` table definitions (Section 3.4) with the new columns above plus eight COLA-registry forward-compatibility columns on `applications` (`ttb_id`, `vendor_code`, `class_type_code`, `origin_code`, `registry_status`, `total_bottle_capacity`, `for_sale_in_state`, `qualifications`).

**COLA Registry research (new Section 6):** At the user's request, researched the TTB COLA Public Registry / COLAs Online data model (via the public search page and an example record, TTB ID `25211001000227`) to ensure the database schema captures registry fields — TTB ID, Vendor Code, Serial #, Class/Type Code, Origin Code, registry Status, Type of Application, For Sale In, Total Bottle Capacity, Formula, Approval Date, Qualifications, repeating Plant Registry/Permit locations, and Contact info — **without loss**, for forward-compatibility only. **No live connection to `ttbonline.gov` exists or is planned for this prototype** (A-03/CR-001 unchanged) — Section 6 is a reference document plus a field-mapping table showing each registry field's home in the TTB-LVS schema (new `applications` columns, or existing/new EAV rows in `form_parameters`/`label_parameters`).

**Open items for next session:** Apply the corresponding updates to `_DevLog/PRD.md` (revision history, REF-07–09 for the COLA registry sources, new FR-017/018/039/040, traceability matrix, assumptions A-12–14, glossary terms), update `README.md`'s tech stack list, then proceed with the original Session 4 plan: architecture evaluation, Mermaid diagrams (system context, block diagram, concurrency sequence diagram), alternatives brainstorm, and WBS.

---

## 8. Chat Artifact Index

Development session transcripts are stored in `_DevLog/` alongside this DevLog.

| File | Date | Description |
|------|------|-------------|
| `2026-06-09_session-01_setup.md` | 2026-06-09 | Assessment intake, initial requirements extraction, repo initialization |
| `2026-06-09_session-02_architecture.md` | 2026-06-09 | Form F 5100.31 analysis, full architecture design, DB schema, API design |
| _(future sessions appended here)_ | | |

---

*Maintained by Matthew Gabriel Sizemore — gratefulgabe5000@gmail.com*  
*Assessment: IT Specialist (AI) · 26-DO-12891471-DH · US Department of the Treasury*
