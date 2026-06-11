# Work Breakdown Structure
## TTB Label Verification System (TTB-LVS)

---

| Field | Value |
|-------|-------|
| Document ID | TTB-LVS-WBS-001 |
| Version | 2.0 |
| Status | Draft |
| Date | 2026-06-11 |
| Prepared By | Matthew Gabriel Sizemore |
| Prepared For | US Department of the Treasury, TTB |
| Assessment Reference | IT Specialist (AI) · 26-DO-12891471-DH |

### Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-06-10 | M.G. Sizemore | Initial release — sequenced implementation plan derived from the architecture evaluation (DevLog §3.6) and system diagrams (DevLog §3.7) |
| 2.0 | 2026-06-11 | M.G. Sizemore | Full re-baseline. Added **Phase 0** (0.1–0.12) covering all completed project-definition and systems-engineering work, for completeness. Rewrote **Phase 1** as a single, dependency-ordered sequence (1.0–21.0) spanning backend coding, backend unit testing, frontend coding, frontend unit testing, integration, integration testing, synthetic test data, localhost testing, deployment, end-to-end testing, and submission collation/submission. Re-scoped the Stage 5 Comparison Engine (7.0) to cover the new FR-066/FR-100–107 (added in PRD v1.3/v1.4). Synthetic test data (2.0) moved earlier so it precedes the unit tests that consume it. **All hour estimates and target dates removed** — this document tracks sequence and dependencies only. |

---

## 1. Phase 0 — Project Definition & Systems Engineering (✅ Complete)

| WBS # | Task | Outcome | Date | Traceability |
|---|---|---|---|---|
| **0.1** | **Project Setup** | Initialized git repo; created public GitHub repo `gratefulgabe5000/ttb-label-verifier`; scaffolded `README.md` and `_DevLog/DevLog.md` | 2026-06-09 | DevLog §7 Session 1 |
| **0.2** | **Problem Identification** | Reviewed assessment notification, submission form, and `_ProblemStatement/3.Assessment_README.txt` (4 stakeholder interviews); framed the COLA label-verification problem and the 5-second per-application processing constraint | 2026-06-09 | DevLog §1; PR-001 |
| **0.3** | **Resource Collection** | Collected the official TTB Form F 5100.31 (`f510031.pdf`); catalogued source documents in DevLog §1 Source Documents table | 2026-06-09 | DevLog §1 |
| **0.4** | **Requirement Extraction** | Derived Req-01–27 from interviews (§2.1); documented Government Warning text/format rules (§2.2), full Form F 5100.31 field reference Items 1–18 (§2.3), application-type/determination logic (§2.4), Parameter Comparison Matrix (§2.5), Section V Allowable Revisions reference (§2.6) | 2026-06-09 | DevLog §2 |
| **0.5** | **Design Brainstorming** | Defined the 6-stage processing pipeline (§3.2), UI architecture/mockups for Dashboard / Detail View / Batch Report (§3.3), 8-table DB schema (§3.4), 10-endpoint API surface (§3.5) | 2026-06-09 | DevLog §3.2–3.5 (v1) |
| **0.6** | **Tech Approach Planning** | Pivoted from Streamlit to React+Vite+TS / FastAPI+SQLAlchemy+SQLite / Claude Sonnet vision (Decisions 1–5) | 2026-06-09 | DevLog §4.2 Decisions 1–5 |
| **0.7** | **PRD Development and Initial Design** | Authored `PRD.md` v1.0 (INCOSE-style: US-001–003, FR/PR/IR/UR/SR/CR requirements, traceability matrix, assumptions, glossary); revised to single-pass extraction (FR-010–016, FR-030–036) and multi-image label processing (FR-030–038, A-10/A-11, IA-18/IA-19) | 2026-06-09 | PRD.md v1.0 |
| **0.8** | **Trade Studies** | TS-01 (tiered form extraction: pypdf → pdfplumber → Claude Vision, FR-017) and TS-02 (OpenCV preprocessing + Tesseract OCR augmentation, FR-039/040); COLA Registry forward-compat reference (§6, FR-018, REF-07–09). PRD → v1.1 | 2026-06-10 | DevLog §3.1, §6; PRD v1.1 |
| **0.9** | **Architecture Evaluation** | End-to-end ideal-scenario walkthrough (§3.6, 15-row executive summary); resolved multi-image tab selector (FR-091), form-panel bbox/location_hint (FR-019, IA-23), Decision 8 (5 refinements). PRD → v1.2 | 2026-06-10 | DevLog §3.6; PRD v1.2 |
| **0.10** | **WBS Development** | System diagrams (§3.7: context, block, sequence with nested concurrency); WBS.md v1.0 (13 top-level items, critical path, risk register) | 2026-06-10 | DevLog §3.7; WBS.md v1.0 |
| **0.11** | **Systems Engineering Review** | Renamed DevLog §5 "Assumptions" → "Initial Assumptions" (IA-01–26) to deconflict with PRD §8 (A-01–14); re-audited and corrected every cross-document A-/IA- reference; fixed 3 broken PRD self-references | 2026-06-10 | DevLog §5; PRD §8 |
| **0.12** | **Documentation Review** | Assumptions-completeness audit → PRD v1.3 (A-15/16/17, FR-066); comparison-matrix completeness audit → PRD v1.4 (FR-100–107); updated DevLog §5 IA cross-references and TODO.md Session 7 | 2026-06-10 | PRD v1.3/v1.4; TODO.md Session 7 |
| **0.13** | **WBS Re-Baseline (v2.0)** | Rewrote `WBS.md` as a single dependency-ordered Phase 1 sequence (1.0–21.0); added Phase 0 (0.1–0.12); re-scoped Stage 5 Comparison Engine to 16 sub-items covering FR-066/FR-100–107; re-sequenced synthetic test data to 2.0; removed hour estimates and target dates | 2026-06-11 | TODO.md Session 8; WBS.md v2.0 |
| **0.14** | **Documentation Consistency Pass (v2.0 Baseline)** | Cross-document review of README/PRD/DevLog/WBS/TODO; corrected footer versions, TOC anchors, section cross-references, and DevLog Engineering Log coverage (Sessions 7–8); bumped PRD to v2.0; synchronized all five documents to a unified v2.0 baseline | 2026-06-11 | TODO.md Session 9; PRD.md v2.0 |

---

## 2. Phase 1 — Implementation Sequence

| WBS # | Task | Depends On | Traceability |
|---|---|---|---|
| **1.0** | **Backend Scaffolding & Infrastructure** | Phase 0 | DevLog §3.4–3.5 |
| 1.1 | Initialize FastAPI app structure (`app/`: `main.py`, `routers/`, `services/`, `models/`, `schemas/`, dependency injection, error handling, OpenAPI docs) | 1.0 | DevLog §3.5 |
| 1.2 | Configure SQLAlchemy + SQLite (`db.py`: engine, session factory, `Base`, `create_all()` bootstrap) | 1.1 | DevLog §3.4 |
| 1.3 | Define ORM models for all 8 tables (`agents`, `applications` incl. 8 COLA forward-compat columns, `label_images`, `form_parameters` incl. `bbox_json`/`location_hint`, `label_parameters` incl. `bbox_json`/`header_height_ratio`, `comparisons`, `determinations`, `batches`) | 1.2 | FR-018, FR-019, IA-23, DevLog §3.4 |
| 1.4 | Configure environment variables (`.env`: `ANTHROPIC_API_KEY`, JWT secret, DB path, upload volume path) | 1.1 | SR-001, IA-26 |
| 1.5 | Configure CORS middleware | 1.1 | IR-006 |
| 1.6 | Minimal "hello world" smoke-test deploy to Railway — verify Tesseract install path (Aptfile/`nixpacks.toml`), persistent volume mount, and env vars resolve in the deployed environment before feature code depends on them | 1.1, 1.4 | IA-26, Decision 8 (deployment watch-items) |
| **2.0** | **Synthetic Test Data Preparation** *(parallel with 1.0; must complete before the unit/integration tests in 5.7, 6.8, 7.16, 8.5, 9.7, 10.4, 16.x consume it)* | Phase 0 | TS-01, TS-02 |
| 2.1 | Inventory and organize existing `testdata/` into a manifest mapping each set to its expected pass/fail outcome | 2.0 | TS-02 |
| 2.2 | Produce sample F 5100.31 PDFs covering all three TS-01 tiers: (a) filled AcroForm, (b) flattened/text-layer-only, (c) scanned/image-only | 0.3 | TS-01, FR-017 |
| 2.3 | Build "good" (all-fields-match) application + label sets for each product type (wine, spirits, malt beverage) | 2.1, 2.2 | §2.5 Comparison Matrix |
| 2.4 | Build "hard failure" sets — one per comparison rule (brand name, government warning text/format, "for sale in [STATE]", country of origin, fanciful name, product/class-type, applicant name, applicant address, grape varietals, wine appellation, ABV, net contents) | 2.1, 2.2 | FR-050–059, FR-066, FR-100–107 |
| 2.5 | Build "possible allowable revision" sets (case/punctuation brand differences, in-state address change, color/font differences) | 2.1 | §2.6 Allowable Revisions, FR-057/059 |
| 2.6 | Build a small set of degraded-quality images (angle, glare, low light) for OpenCV preprocessing tests | 2.1 | FR-039 |
| 2.7 | Build a Type 14b ("for sale in one state only") application + matching/non-matching label set | 2.1, 2.2 | FR-056 |
| **3.0** | **Backend — Authentication & Authorization** | 1.3 | SR-001, SR-002 |
| 3.1 | `Agent` ORM model + seed script for initial agent accounts (password hashing via passlib) | 1.3 | SR-001, SR-002 |
| 3.2 | `POST /auth/login` (JWT issuance via python-jose) | 3.1 | SR-001, DevLog §3.5 |
| 3.3 | JWT validation dependency (current-agent), applied to all protected routers | 3.2 | SR-002 |
| 3.4 | Unit tests: auth (login success/failure, token validation/expiry) | 3.3 | SR-001, SR-002 |
| **4.0** | **Backend — Stage 1–2: Ingestion** | 1.3, 3.3 | DevLog §3.2 Stages 1–2 |
| 4.1 | `POST /applications` — multipart upload (form PDF + N label images), batch grouping | 1.3, 3.3 | FR-001–006 |
| 4.2 | File validation (file types, size limits, required-field presence) | 4.1 | FR-007, IR-002, IR-003 |
| 4.3 | Persist uploaded files to disk/volume; insert `applications` + `label_images` rows | 4.1, 4.2, 1.6 | IA-26 |
| 4.4 | `GET /applications` (list, filter by applicant) | 4.3 | FR-070–072 |
| 4.5 | `GET /applications/{id}` (full detail incl. associated `label_images`) | 4.3 | DevLog §3.5 |
| 4.6 | Unit tests: ingestion (valid/invalid uploads, batch grouping, listing/filtering) using 2.2 | 4.5, 2.2 | FR-001–007 |
| **5.0** | **Backend — Stage 3: Form Assessment (TS-01 Tiered Extraction)** | 4.5 | TS-01, DevLog §3.2 Stage 3 |
| 5.1 | Tier 1 — `pypdf` AcroForm field reader; map field names to Items 1–18; capture `/Rect` → `bbox_json` | 4.5 | TS-01, FR-017, FR-019, IA-23 |
| 5.2 | Tier 2 — `pdfplumber` text-layer fallback; region mapping; word bbox → `bbox_json` | 5.1 | TS-01, FR-017, FR-019, IA-23 |
| 5.3 | Tier 3 — Claude Vision fallback; prompt design with prompt caching (IA-25); JSON schema for all 18 Part I fields; `location_hint` fallback when no bbox is available | 5.2 | FR-010–016, FR-019, IA-23, IA-25 |
| 5.4 | Field normalization (source/origin, product type, application type 14a–d parsing, grape varietals list) | 5.3 | FR-012–015 |
| 5.5 | Confidence scoring + `extraction_method` recording (which tier resolved each field) | 5.4 | FR-016, FR-017 |
| 5.6 | Persist to `form_parameters` (incl. `bbox_json`/`location_hint`) | 5.5 | DevLog §3.4 |
| 5.7 | Unit tests: Stage 3 — each tier individually, tiered fallback ordering, field normalization, using 2.2's sample PDFs | 5.6, 2.2 | FR-010–019 |
| **6.0** | **Backend — Stage 4: Label Assessment (TS-02)** | 4.5 | TS-02, DevLog §3.2 Stage 4 |
| 6.1 | OpenCV preprocessing pipeline (deskew, contrast/CLAHE, glare suppression) | 4.5 | TS-02, FR-039 |
| 6.2 | Claude Vision label-extraction prompt (mandatory + secondary elements + generic `other_text`) | 6.1 | FR-030–033 |
| 6.3 | Government Warning detection (exact-text + bold/caps check) | 6.2 | FR-034, FR-035 |
| 6.4 | Tesseract OCR pass — text + bbox detection | 6.1 | FR-040 |
| 6.5 | Fuzzy-match Claude-extracted values to OCR bboxes; compute `header_height_ratio` | 6.2, 6.4 | FR-040 |
| 6.6 | Per-image concurrent execution (`asyncio.gather` across an application's label images; Claude-vs-OCR concurrency within each image) | 6.5 | IA-19, DevLog §3.7 sequence diagram |
| 6.7 | Persist to `label_parameters` (one row per `label_image_id` × field_name, incl. `bbox_json`/`header_height_ratio`) | 6.6 | FR-038, DevLog §3.4 |
| 6.8 | Unit tests: Stage 4 — preprocessing on degraded images (2.6), extraction parsing, OCR fuzzy-match, government warning detection, using 2.1/2.4 | 6.7, 2.1, 2.6 | FR-030–040 |
| **7.0** | **Backend — Stage 5: Comparison Engine** *(re-scoped for FR-066, FR-100–107)* | 5.6, 6.7 | DevLog §3.2 Stage 5 |
| 7.1 | Multi-image resolution helper — a form value is "on label" if found on **any** associated label image; shared by every comparison rule below | 5.6, 6.7 | A-10, IA-18, FR-038 |
| 7.2 | Brand Name comparison (case/punctuation-tolerant) | 7.1 | FR-050–052 |
| 7.3 | Government Warning comparison (exact-text + bold/caps via `header_height_ratio`) | 7.1 | FR-053–055 |
| 7.4 | Type 14b "for sale in [STATE]" check | 7.1 | FR-056 |
| 7.5 | Section V Allowable-Revision classification mapping (flags POSSIBLE_ALLOWABLE vs HARD_FAILURE for the rules below) | 7.2, 7.3, 7.4 | FR-057, FR-059, §2.6 |
| 7.6 | Country of Origin comparison (conditional on Item 3 = "imported") | 7.1 | A-17, FR-066 |
| 7.7 | Fanciful Name comparison (Item 7) | 7.1 | FR-100 |
| 7.8 | Product Type / Class-Type consistency (Item 5) | 7.1 | FR-101 |
| 7.9 | Applicant Name comparison (Item 8) | 7.1 | FR-102 |
| 7.10 | Applicant Address comparison (Item 8/8a, incl. in-state Allowable Revision per Section V) | 7.1, 7.5 | FR-103 |
| 7.11 | Grape Varietals comparison (Item 10, Wine only) | 7.1, 5.4 | FR-104 |
| 7.12 | Wine Appellation comparison (Item 11, Wine only, conditional) | 7.1, 5.4 | FR-105 |
| 7.13 | ABV presence + product-type consistency check | 7.1, 5.4 | FR-106 |
| 7.14 | Net Contents presence check | 7.1 | FR-107 |
| 7.15 | Persist all results to `comparisons` table | 7.2–7.14 | FR-058, DevLog §3.4 |
| 7.16 | Unit tests: comparison engine — one test per rule (7.2–7.14) covering MATCH/HARD_FAILURE/POSSIBLE_ALLOWABLE outcomes, plus the multi-image resolution helper (7.1), using 2.3/2.4/2.5/2.7 | 7.15, 2.3, 2.4, 2.5, 2.7 | FR-050–059, FR-066, FR-100–107, A-10, IA-18 |
| **8.0** | **Backend — Stage 6: Determination & Reporting** | 7.15 | DevLog §3.2 Stage 6 |
| 8.1 | Determination logic — APPROVE / DENY / RECOMMEND_EXEMPTION_REVIEW | 7.15 | FR-060–062 |
| 8.2 | Hard-failure list and allowable-revision list generation per application | 8.1 | FR-063, FR-064 |
| 8.3 | Per-application determination report schema | 8.2 | FR-065 |
| 8.4 | Persist to `determinations` table | 8.3 | DevLog §3.4 |
| 8.5 | Unit tests: Stage 6 — all 3 determination outcomes plus edge cases (e.g., no hard failures but unresolved possible-allowables), using 2.3/2.4 | 8.4, 2.3, 2.4 | FR-060–065 |
| **9.0** | **Backend — Pipeline Orchestration & Batch Processing** | 5.6, 6.7, 7.15, 8.4 | DevLog §3.7 sequence/block diagrams |
| 9.1 | Single-application orchestrator — runs Stages 3–6 with concurrent-compute / sequential-persist write pattern | 5.6, 6.7, 7.15, 8.4 | IA-24 |
| 9.2 | `POST /applications/{id}/process` | 9.1 | FR-074 |
| 9.3 | Batch Orchestrator — bounded-concurrency semaphore (3–5 applications in flight) | 9.1 | A-07, IA-17, DevLog §3.7 block diagram |
| 9.4 | `POST /batch/process`; insert `batches` row | 9.3 | DevLog §3.5 |
| 9.5 | `GET /batch/{id}/status` (polling) | 9.4 | FR-075 |
| 9.6 | `GET /applications/{id}/comparisons` | 7.15 | DevLog §3.5 |
| 9.7 | Unit/integration tests: orchestration — concurrency bounds (9.3), status transitions (9.5), per-application timing against PR-001, using 2.3 | 9.6, 2.3 | PR-001, A-07, IA-17, IA-19, IA-24 |
| **10.0** | **Backend — Overrides, Finalization & Batch Report** | 9.6 | FR-086–097 |
| 10.1 | `POST /determinations/{id}/override` — per-parameter and overall overrides with audit fields (agent, timestamp, reason) | 9.6 | FR-086–089, SR-004 |
| 10.2 | `POST /determinations/{id}/finalize` — overrides do not re-run the AI pipeline (A-15); retention through `finalized_at` (A-16, SR-003) | 10.1 | FR-090, A-15, A-16 |
| 10.3 | `GET /batch/{id}/report` — counts by outcome + most common failure type | 10.2 | FR-095–097 |
| 10.4 | Unit tests: overrides, finalize, batch report, using 2.3/2.4 | 10.3, 2.3, 2.4 | FR-086–090, FR-095–097, SR-004 |
| **11.0** | **Frontend Scaffolding & Infrastructure** *(can start in parallel with 1.0)* | Phase 0 | DevLog §4.1 |
| 11.1 | Initialize Vite + React + TS project (`web/`) | 11.0 | DevLog §4.1 |
| 11.2 | Configure Tailwind CSS 4 | 11.1 | DevLog §4.1 |
| 11.3 | Install + configure shadcn/ui (Tabs, Dialog, ContextMenu, Table, Badge) | 11.2 | Decision 8 #5, FR-091 |
| 11.4 | Install react-pdf + React Query | 11.1 | DevLog §4.1 |
| 11.5 | Project structure (`pages/`, `components/`, `hooks/`, `lib/` API client) | 11.1 | — |
| 11.6 | Auth context/hooks + login page | 11.5, 3.2 | SR-001 |
| 11.7 | Typed API client matching backend schemas | 11.5, 4.5, 5.6, 6.7, 7.15, 8.4 | DevLog §3.5 |
| **12.0** | **Frontend — Agent Dashboard** | 11.7, 4.4 | FR-070–077 |
| 12.1 | Application list table (serial #, applicant, type, status) | 11.7, 4.4 | FR-070, FR-071 |
| 12.2 | Filter by applicant | 12.1 | FR-072 |
| 12.3 | Checkbox batch selection | 12.1 | FR-073 |
| 12.4 | "Process Selected" action + progress indicator (polls 9.5) | 12.3, 9.4, 9.5 | FR-074, FR-075, UR-004 |
| 12.5 | Result badges (✅/❌/⚠️) | 12.4, 8.4 | FR-076, UR-002 |
| 12.6 | Batch summary header | 12.4 | FR-077 |
| 12.7 | Upload-new modal (form PDF + N label images) | 12.1, 4.1 | FR-001–006 |
| 12.8 | Unit tests (Vitest): Dashboard — list/filter/selection/badges/upload modal | 12.7 | FR-070–077 |
| **13.0** | **Frontend — Application Detail View** | 11.7, 5.6, 6.7, 7.15 | FR-080–091 |
| 13.1 | Split-view layout (form PDF left / label image(s) right) | 11.7, 4.5 | FR-080, FR-081 |
| 13.2 | react-pdf form renderer | 13.1 | FR-080 |
| 13.3 | Multi-image tab selector with thumbnails | 13.1 | FR-091 |
| 13.4 | SVG annotation overlay — form panel (positioned via `form_parameters.bbox_json`/`location_hint`) | 13.2, 5.6 | FR-019, FR-082, IA-23 |
| 13.5 | SVG annotation overlay — label panel (positioned via `label_parameters.bbox_json`/`header_height_ratio`) | 13.3, 6.7 | FR-083 |
| 13.6 | Mouse-over cross-highlighting between form and label annotations | 13.4, 13.5 | FR-084 |
| 13.7 | Parameter results table (per-field comparison outcomes) | 13.1, 7.15, 9.6 | FR-085 |
| 13.8 | Right-click override context menu + modal (per-parameter) | 13.7, 10.1 | FR-086, FR-087 |
| 13.9 | Overall-determination override control | 13.8, 10.1 | FR-089 |
| 13.10 | Finalize action | 13.9, 10.2 | FR-090 |
| 13.11 | Auto-tab-switch when an annotation references a specific `label_image_id` | 13.3, 13.6 | FR-091 |
| 13.12 | Unit tests (Vitest): Detail View — annotation rendering, tab switching/auto-switch, cross-highlight, override modal, finalize | 13.11 | FR-080–091 |
| **14.0** | **Frontend — Batch Report View** | 11.7, 10.3 | FR-095–097, UR-003 |
| 14.1 | Report layout — counts by outcome | 11.7, 10.3 | FR-095, FR-096 |
| 14.2 | Common-failure-type display | 14.1 | FR-097 |
| 14.3 | CSV export | 14.1 | UR-003 |
| 14.4 | PDF export *(optional / stretch)* | 14.1 | UR-003 |
| 14.5 | Unit tests (Vitest): Batch Report — counts, failure-type display, export | 14.3 | FR-095–097 |
| **15.0** | **Integration — Frontend ↔ Backend Wiring** | 12.8, 13.12, 14.5, 9.5, 10.2, 10.3, 11.6 | — |
| 15.1 | Wire Dashboard (12.0) to `GET /applications`, `POST /batch/process`, `GET /batch/{id}/status` | 12.8, 9.5 | — |
| 15.2 | Wire Detail View (13.0) to `GET /applications/{id}`, `POST /determinations/{id}/override`, `POST /determinations/{id}/finalize` | 13.12, 10.2 | — |
| 15.3 | Wire Batch Report (14.0) to `GET /batch/{id}/report` | 14.5, 10.3 | — |
| 15.4 | Wire auth flow — login → JWT storage → authenticated requests on all endpoints | 11.6, 3.3 | SR-001, SR-002 |
| 15.5 | Plain-English error handling/surfacing across all wired views | 15.1, 15.2, 15.3, 15.4 | UR-003 |
| **16.0** | **Integration Testing** *(localhost, against synthetic data)* | 15.5, 2.0 | PR-001, PR-002, PR-004 |
| 16.1 | End-to-end pipeline test per product type (wine/spirits/malt) using 2.3–2.7 | 15.5, 2.0 | §2.5 Comparison Matrix, FR-050–059, FR-066, FR-100–107 |
| 16.2 | PR-001 timing verification (≤5s/application incl. all label images) | 16.1 | PR-001 |
| 16.3 | Bounded-concurrency batch test | 16.1, 9.3 | A-07, IA-17, PR-002, PR-004 |
| 16.4 | Multi-image resolution test — value present on a non-primary image still satisfies the field | 16.1, 7.1 | A-10, IA-18 |
| 16.5 | Override + finalize flow test — confirm overrides do not re-run the AI pipeline | 16.1, 10.2, 13.10 | A-15 |
| 16.6 | Annotation placement test — `bbox_json` vs `location_hint` fallback on Tier-3/degraded cases | 16.1, 13.4, 13.5, 2.6 | FR-019, FR-036, FR-040 |
| **17.0** | **Localhost End-to-End Manual Testing** | 16.6 | DevLog §3.6 |
| 17.1 | Full user-path walkthrough: login → dashboard → batch select → process → detail view → override → finalize → batch report (mirrors §3.6 ideal-scenario path) | 16.6 | DevLog §3.6 |
| 17.2 | Usability checks — UR-001–006 (≤3 interactions to key actions, color/icon distinctness, plain-English errors, load times, no-scroll primary controls) | 17.1 | UR-001–006 |
| 17.3 | Browser compatibility check (Chrome, Edge, Firefox) | 17.1 | IR-006 |
| 17.4 | Edge-case walkthrough — degraded images, Type 14b, blank Item 7/11, missing optional fields | 17.1, 2.6, 2.7 | FR-039, FR-056, FR-104, FR-105 |
| **18.0** | **Setup & Deployment** | 17.4, 1.6 | IA-26, Decision 8 |
| 18.1 | Railway: deploy backend to the project smoke-tested in 1.6; attach persistent volume for SQLite DB + uploaded files | 17.4, 1.6 | IA-26 |
| 18.2 | Confirm Tesseract OCR binary available in deployed environment (Aptfile/`nixpacks.toml`) | 18.1 | TS-02, Decision 8 |
| 18.3 | Configure production environment variables on Railway | 18.1 | SR-001 |
| 18.4 | Netlify: deploy frontend; configure API base URL env var | 17.4 | — |
| 18.5 | Configure CORS for the deployed cross-origin pair (Netlify ↔ Railway) | 18.1, 18.4 | IR-006 |
| 18.6 | Update `README.md` with the live deployed URL and run instructions | 18.5 | CR-005 |
| **19.0** | **Post-Deployment End-to-End Testing** | 18.6 | CR-004 |
| 19.1 | Re-run the 17.1 user-path walkthrough against the deployed URL (no VPN/special credentials required) | 18.6 | CR-004 |
| 19.2 | Re-verify PR-001/PR-003 timing on deployed infrastructure (network latency may differ from localhost) | 19.1 | PR-001, PR-003 |
| 19.3 | Cross-browser spot-check on the deployed URL | 19.1 | IR-006 |
| **20.0** | **Submission Material Review & Collation** | 19.3 |  |
| 20.1 | Final review of `README.md` (setup/run instructions, live URL, known limitations) | 19.3 | CR-005 |
| 20.2 | Final review of `DevLog.md` — confirm Engineering Log captures all sessions through deployment | 19.3 | DevLog §7 |
| 20.3 | Final consistency check across `PRD.md`/`WBS.md`/`TODO.md` (version numbers, footers, cross-references) | 20.2 | — |
| 20.4 | Export remaining chat session transcripts to `_DevLog/` | 20.3 | NOT REQUIRED — transcripts will not be provided as part of this submission |
| 20.5 | Repository cleanup — verify `.gitignore` covers secrets/`.env`, confirm no exposed API keys in history | 20.4 | — |
| 20.6 | Final lint/format pass on `app/` and `web/` | 20.5 | — |
| **21.0** | **Submission** | 20.6 | — |
| 21.1 | Verify Microsoft Forms submission link and required fields (repo URL, deployed URL) | 20.6 | TODO.md submission link |
| 21.2 | Submit via the assessment submission form (https://forms.osi.office365.us/r/xWrQGduMw7) | 21.1 | — |
| 21.3 | Record submission confirmation/timestamp in `DevLog.md` | 21.2 | — |

---

## 3. Dependency Flow

```
Phase 0 (complete)
   │
   ├─────────────────────────────────┐
   ▼                                  ▼
1.0 Backend Scaffolding         11.0 Frontend Scaffolding
   │                                  │
   ├── 2.0 Synthetic Test Data ───────┤  (parallel; feeds 5.7/6.8/7.16/8.5/9.7/10.4/16.x)
   ▼                                  │
3.0 Auth                              │
   ▼                                  │
4.0 Stage 1–2 Ingestion               │
   ▼                                  │
5.0 Stage 3 Form Assessment           │
   ▼                                  │
6.0 Stage 4 Label Assessment          │
   ▼                                  │
7.0 Stage 5 Comparison Engine         │
   ▼                                  │
8.0 Stage 6 Determination             │
   ▼                                  │
9.0 Orchestration & Batch       12.0 Agent Dashboard
   ▼                            13.0 Application Detail View
10.0 Overrides/Finalize/Report  14.0 Batch Report View
   │                                  │
   └────────────────┬─────────────────┘
                     ▼
             15.0 Integration (FE ↔ BE wiring)
                     ▼
             16.0 Integration Testing
                     ▼
             17.0 Localhost End-to-End Testing
                     ▼
             18.0 Setup & Deployment
                     ▼
             19.0 Post-Deployment End-to-End Testing
                     ▼
             20.0 Submission Material Review & Collation
                     ▼
             21.0 Submission
```

11.0–14.0 (frontend) can begin as soon as 11.7's typed API client has a stable contract to target — in practice this means frontend scaffolding (11.1–11.6) starts immediately alongside 1.0, while 11.7 and the view-specific items (12.0–14.0) wait on the corresponding backend schemas (4.5, 5.6, 6.7, 7.15, 8.4, 9.5, 10.1–10.3) as they land.

---

## 4. Sequencing & Technical Risk Notes

1. **TS-02 OCR bbox uncertainty (6.4–6.5):** if Tesseract fuzzy-matching for `label_parameters.bbox_json` proves unreliable, fall back to Claude-only extraction with `location_hint` (the existing fallback design per IA-13). This degrades 13.5's annotation precision but does not block 7.0/8.0/9.0 — Stage 4's output contract and PR-001 are unaffected either way.

2. **7.1 (multi-image resolution helper) is a single point of shared logic for 13 comparison rules (7.2–7.14).** Validate it thoroughly before fanning out — a defect here would otherwise need to be re-fixed across all 13 call sites and their corresponding unit tests (7.16).

3. **13.0 (Application Detail View) has the most downstream dependents** (15.2, 16.5, 16.6, 17.1, 19.1). If any sub-item slips, 13.3 (multi-image tabs) can ship with a single-image fallback first, per the FR-091 fallback note, deferring full tab UX without blocking 15.0 onward.

4. **14.0 (Batch Report View) has the lowest direct FR traceability** (UR-003 only) and 14.4 (PDF export) is explicitly optional. If a sub-item must be cut, this is the lowest-impact candidate — it does not block 15.0–21.0 for the Dashboard/Detail View, which are the primary graded surfaces.

5. **18.0 (Setup & Deployment) platform risk is front-loaded into 1.6** (smoke-test deploy). Any Railway/Tesseract/persistent-volume issues should surface there, long before 18.0 depends on that configuration working.

6. **2.0 (Synthetic Test Data) is a hard prerequisite for nearly every test item** (5.7, 6.8, 7.16, 8.5, 9.7, 10.4, 16.1–16.6, 17.4). Completing 2.1–2.7 early — in parallel with 1.0 — avoids any backend coding item stalling at its paired unit-test sub-item for lack of fixtures.

---

*Copyright (c) 2026 Matthew Gabriel Sizemore · Assessment submission: IT Specialist (AI) · 26-DO-12891471-DH*
