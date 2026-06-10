# TODO — TTB Label Verification System

**Assessment:** IT Specialist (AI) · 26-DO-12891471-DH
**Received:** June 9, 2026, 1458 hrs · **Deadline:** June 16, 2026, 1458 hrs
**Repo:** https://github.com/gratefulgabe5000/ttb-label-verifier

---

## Status at a Glance

| Deliverable | Status |
|---|---|
| Public GitHub repo | ✅ Created |
| `README.md` (setup/run instructions) | ✅ Drafted (no runnable code yet) |
| `_DevLog/DevLog.md` (approach, tools, assumptions, design) | ✅ Comprehensive |
| `_DevLog/PRD.md` (INCOSE-style PRD + user stories + traceability) | ✅ Drafted, revised twice today, plus v1.1 (2026-06-10) |
| Trade studies (TS-01 form extraction tiering, TS-02 label OpenCV/OCR augmentation) + COLA registry forward-compat reference | ✅ Complete (2026-06-10) |
| Systems engineering review (architecture, block diagram, alternatives) | ☐ Next session |
| Work Breakdown Structure | ☐ Pending systems engineering review |
| Backend (`app/`) | ☐ Not started |
| Frontend (`web/`) | ☐ Not started |
| Synthetic test data (sample forms + multi-image label sets) | ☐ Not started |
| Deployed application URL | ☐ Pending |

---

## Next Session (2026-06-10) — Systems Engineering Pass

> **Update:** Trade studies (TS-01, TS-02) and the COLA registry reference were completed in Session 4 (2026-06-10) — see Daily Chat Summary below and DevLog §3.1/§6. The architecture evaluation, diagrams, and WBS below remain pending for the next session.

Per plan: before writing a WBS, revisit the architecture from a systems-engineering lens.

1. **Architecture evaluation** — review the React+Vite / FastAPI / SQLite / Claude design against alternatives; confirm it still holds given today's PRD revisions (comprehensive single-pass extraction + per-image label processing increase the number of AI calls per application)
2. **Mermaid diagrams** — produce:
   - System context diagram
   - System block diagram (components + data flow, Stages 1–6)
   - Sequence diagram for single-application processing (concurrent per-image label extraction, per A-19)
3. **Brainstorm vs. alternatives** — sanity-check current choices before locking in (e.g., one combined extraction call vs. separate form/label calls, sync vs. async batch processing, SQLite vs. alternatives)
4. **Work Breakdown Structure (WBS)** — once architecture is confirmed, itemize remaining work into a sequenced WBS with estimates against the June 16 deadline

### Open design question carried from today
Application Detail View (PRD FR-080–090) was designed around a single form-panel/label-panel split view. With multiple label images per application now in scope (FR-030–038), the UI needs a way to present/select among them (tabs, thumbnail strip, or stacked panels) so the agent can see which image a given annotation refers to.

---

## Remaining Implementation Work (post-architecture-review)

- [ ] Scaffold `app/` (FastAPI backend): routers, services, models, schemas, `db.py`
- [ ] Scaffold `web/` (React + Vite frontend): pages, components, API hooks
- [ ] Implement Stage 1–2: ingestion endpoints + DB writes (form + N label images)
- [ ] Implement Stage 3: form assessment (Claude prompt + parser, all 18 Part I fields)
- [ ] Implement Stage 4: label assessment (Claude Vision prompt + parser, run per image, all elements + `other_text`)
- [ ] Implement Stage 5: comparison engine (multi-image resolution per A-10/A-18)
- [ ] Implement Stage 6: determination + report generation
- [ ] Build Agent Dashboard (list, filter, batch select, process, badges)
- [ ] Build Application Detail View (split view w/ multi-image selector, annotations, overrides)
- [ ] Build Batch Report view
- [ ] Create synthetic test data: sample F 5100.31 PDFs + multi-image label sets
- [ ] Unit tests: comparison logic, government warning validator, multi-image resolution
- [ ] Deploy: Railway (API) + Netlify (web); update README with live URL
- [ ] Export chat session transcripts into `_DevLog/` per the Chat Artifact Index

---

## Daily Chat Summary

### 2026-06-09

- **Session 1 — Assessment Intake & Setup.** Reviewed all source documents (USA Staffing notification, submission form, `Assessment_README.txt` with 4 stakeholder interviews). Extracted initial functional/non-functional requirements. Initialized the git repo and created the public GitHub repo `gratefulgabe5000/ttb-label-verifier`. Drafted initial `README.md` and `_DevLog/DevLog.md` around a Streamlit-based plan.

- **Session 2 — Form Analysis & Architecture Redesign.** Added `f510031.pdf` (official TTB Form F 5100.31) to the project. Walked through the full intended UI/workflow: agent dashboard with batch checkbox selection, split-view detail page (form left / label right) with red-ellipse mismatch annotations, mouse-over cross-highlighting between panels, and right-click overrides per parameter or overall. Pivoted the stack from Streamlit to React + Vite + TypeScript + Tailwind (frontend) / FastAPI + SQLAlchemy + SQLite (backend) / Claude Sonnet vision (AI). Defined the 6-stage processing pipeline, the complete Form F 5100.31 field reference, application-type/determination logic, the parameter comparison matrix, the Section V Allowable Revisions reference, an 8-table DB schema, and a 10-endpoint API surface. Rewrote `DevLog.md` and `README.md` to match.

- **Session 3 — INCOSE PRD.** Authored `_DevLog/PRD.md`, an INCOSE-style PRD (`TTB-LVS-PRD-001`) with product description, operational concept, three user stories (US-001–003), system boundary, a full SHALL-requirements set (FR/PR/IR/UR/SR/CR), traceability matrix, assumptions, and glossary.

- **Session 3 (cont.) — Comprehensive Extraction Revision.** Flagged that the original FR-010–020 only extracted the subset of form fields needed for comparison — Items 12 (Phone) and 13 (Email) were missing entirely, along with several others. Generalized to an "extract everything in one pass" principle: replaced FR-010–020 → **FR-010–016** (all 18 Part I form items in a single pass, with null-handling, normalization, and confidence scoring) and FR-030–040 → **FR-030–036** (all mandatory + secondary label elements, plus a generic `other_text` catch-all). Updated the Stage 3/4 output schemas and traceability matrix to match.

- **Session 3 (cont.) — Multi-Image Label Processing.** Clarified that **all** label images (not just a "primary" brand label) must be processed and compared — companion labels (back, neck, etc.) exist specifically to satisfy requirements the front label doesn't carry, and provenance (which image) must be tracked. Revised Label Assessment to **FR-030–038** (9 reqs): Stage 4 now runs independently per label image with each element tagged by `label_image_id`, and a form field is satisfied if a matching value is found on **any** image. Updated FR-038/FR-050/FR-053–056 (comparison) accordingly, and PR-001 so the 5-second budget covers concurrent extraction of all of an application's label images. Added assumptions A-10/A-11 (PRD) and A-18/A-19 (DevLog) covering multi-image conflict resolution and concurrency. Updated `README.md` (pipeline steps, Verified Fields note, Detail View description). Flagged the multi-image split-view UI design as an open question for the next systems-engineering session, and created this `TODO.md`.

---

### 2026-06-10

- **Session 4 — Trade Studies & COLA Registry Reference.** Before starting the architecture evaluation, conducted two trade studies to test whether "AI for everything" extraction is the most effective design given the 5-second budget — **AI remains a hard requirement and the system's semantic core; the question was whether AI is the best tool for every sub-task, not whether to remove it.**
  - **TS-01 (Stage 3 — Form extraction):** Found `f510031.pdf` is a 44-field fillable AcroForm. Adopted a tiered strategy — AcroForm field read (`pypdf`) → `pdfplumber` text-layer → Claude Vision fallback — with the resolving tier recorded as `extraction_method` (new **FR-017**). Frees most of the 5-second budget for Stage 4 in the common case.
  - **TS-02 (Stage 4 — Label extraction):** Added OpenCV preprocessing (deskew, contrast, glare suppression) before every Claude Vision call, addressing the previously-unimplemented degraded-image requirement (new **FR-039**), plus a parallel OCR (`pytesseract`/Tesseract) pass that fuzzy-matches Claude's extracted values to recover pixel `bbox`es for SVG annotations and computes a `header_height_ratio` corroborating the Government Warning bold/caps check (new **FR-040**). Both run locally and concurrently — no impact to PR-001 or the per-image concurrency model (A-11/A-19).
  - **COLA Registry reference (new FR-018, DevLog §6):** At the user's request, researched the TTB COLA Public Registry / COLAs Online data model (TTB ID, Vendor Code, Serial #, Class/Type Code, Origin Code, registry status, Total Bottle Capacity, Formula, Approval Date, Qualifications, repeating Plant Registry/Permit locations, Contact info — REF-07–09) and added 8 forward-compatibility columns to the `applications` table, plus a field-mapping table showing the rest are already covered by the existing EAV `form_parameters`/`label_parameters` tables. **No live connection to ttbonline.gov exists or is planned** — schema-only forward-compatibility (A-03/A-12 unchanged).
  - Updated `_DevLog/DevLog.md` (new §3.1 Trade Studies, renumbered 3.2–3.5, updated Stage 3/4 schemas, tech stack + Decisions 6/7, resolved A-07/A-13, added A-20–A-22, updated DB schema, new §6 COLA reference, Session 4 engineering log entry, renumbered §6→7 and §7→8) and `_DevLog/PRD.md` (v1.1: revision history, REF-07–09, FR-017/018/039/040, updated FR-010/FR-036, traceability matrix + TS/COLA source codes, A-12–14, updated A-05, glossary terms). Updated `README.md` stack list.
  - **Open items for next session:** the original Session 4 plan (architecture evaluation, Mermaid diagrams, alternatives brainstorm, WBS) remains pending — the trade-study findings (tiered extraction, OpenCV/OCR augmentation, multi-table EAV schema) now feed directly into that evaluation.

---

*Maintained by Matthew Gabriel Sizemore — gratefulgabe5000@gmail.com*
