# Work Breakdown Structure
## TTB Label Verification System (TTB-LVS)

---

| Field | Value |
|-------|-------|
| Document ID | TTB-LVS-WBS-001 |
| Version | 2.10 |
| Status | Draft |
| Date | 2026-06-14 |
| Prepared By | Matthew Gabriel Sizemore |
| Prepared For | US Department of the Treasury, TTB |
| Assessment Reference | IT Specialist (AI) · 26-DO-12891471-DH |

### Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0 | 2026-06-10 | M.G. Sizemore | Initial release — sequenced implementation plan derived from the architecture evaluation (DevLog §3.6) and system diagrams (DevLog §3.7) |
| 2.0 | 2026-06-11 | M.G. Sizemore | Full re-baseline. Added **Phase 0** (0.1–0.12) covering all completed project-definition and systems-engineering work, for completeness. Rewrote **Phase 1** as a single, dependency-ordered sequence (1.0–21.0) spanning backend coding, backend unit testing, frontend coding, frontend unit testing, integration, integration testing, synthetic test data, localhost testing, deployment, end-to-end testing, and submission collation/submission. Re-scoped the Stage 5 Comparison Engine (7.0) to cover the new FR-066/FR-100–107 (added in PRD v1.3/v1.4). Synthetic test data (2.0) moved earlier so it precedes the unit tests that consume it. **All hour estimates and target dates removed** — this document tracks sequence and dependencies only. |
| 2.1 | 2026-06-11 | M.G. Sizemore | Re-sequenced execution order: pulled **WBS 12.0** (Agent Dashboard) and **13.0** (Application Detail View) forward, ahead of 6.0–10.0, to enable incremental manual UI verification as backend stages land. Split each into **Pass 1** (sub-items buildable now against completed 1.0/3.0/4.0/5.0/11.0 — annotated below) and **Pass 2** (sub-items requiring 6.0–10.0 — deferred and revisited after 10.0, before 14.0). Dependency graph (§2) unchanged; §3 and §4 updated with the new execution order and rationale (§4 Note 7). |
| 2.2 | 2026-06-12 | M.G. Sizemore | Updated Sections 1 and 2 to include a status column |
| 2.3 | 2026-06-12 | M.G. Sizemore | Marked WBS 12.0/13.0 (all sub-items, 12.4–12.6/12.8/13.5–13.12) complete — Pass 2 implementation finished (Session 21) |
| 2.4 | 2026-06-12 | M.G. Sizemore | Session 22 refinements within already-complete 6.2/7.3/7.9/7.10 — Government Warning 3-way split with case/punctuation-tolerant MATCH, importer-vs-bottler matching for Item 8 with ZIP+4-tolerant address comparison; no new line items. Added §4 Note 8 (open product question: importer vs. manufacturer for Item 8 on imported products) |
| 2.5 | 2026-06-12 | M.G. Sizemore | Marked WBS 14.0 (Frontend — Batch Report View, 14.1–14.5) complete |
| 2.6 | 2026-06-12 | M.G. Sizemore | Marked WBS 15.0 (Integration — Frontend ↔ Backend Wiring, 15.1–15.5) complete |
| 2.7 | 2026-06-12 | M.G. Sizemore | Session 26 refinements within already-complete 4.0/5.0/6.1/6.8/7.2/7.9/7.10/7.13/12.0 — diacritic-folding text normalization, `suppress_glare` area-fraction cap (FR-039), importer-only Item 8 matching for imports (closes §4 Note 8), §1.A.5.64 brand-name fallback + ABV approved-phrasing check + new `compare_field_of_vision` rule (new DevLog §7), and Dashboard registry-field/auto-TTB-ID/Delete-All updates; no new line items. Added §4 Note 10 |
| 2.8 | 2026-06-13 | M.G. Sizemore | Marked WBS 18.0 (Setup & Deployment, 18.1–18.6) complete — Session 27. Per Gabe's direction, executed ahead of 16.0/17.0 (§4 Note 11). Backend deployed to Railway (Tesseract via Nixpacks, persistent `/data` volume, `SEED_DEMO_AGENTS` auto-seed); frontend deployed to Netlify (`netlify.toml`, SPA `_redirects`); CORS configured; `README.md` updated with live URLs |
| 2.9 | 2026-06-14 | M.G. Sizemore | Session 28 — Marked **16.1** complete. FR-106 simplified to an ABV presence-only check (removed `ABV_RANGES`); 7 comparison-engine match-fallback fixes within already-complete 7.2/7.7/7.8/7.9/7.12 (EU wine-designation keywords, German umlaut-transliteration appellation match, period-tolerant state-code parsing, fanciful-name/applicant-name/brand-name "contains" fallbacks, brand_name↔fanciful_name field-swap fallback); 18-app re-sweep (13/18 PASS, same 5 pre-fix failures, all 7 remaining mismatches incl. app17/app18 root-caused as test-data/AcroForm issues, not code defects); CRITICAL 9.1 hardening fix — `/reprocess/form`/`/reprocess/label` no longer overwrite good data with an all-null FR-011/IA-02 skeleton. 224/224 pytest. New §4 Note 12 |
| 2.10 | 2026-06-14 | M.G. Sizemore | Session 29 refinements within already-complete 7.9/7.10/8.4/10.2 — Item 8 City+State interim address-matching policy (`_find_state_span`/`_extract_city_state`, `address_matches`/`classify_address_mismatch`, +3 net `TestApplicantAddress` tests), and `persist_determination` now clears `finalized_at` on reprocess (+3 `test_reprocess_reverts_finalized_status` parametrizations). 230/230 pytest. Plus frontend-only UX additions with no FR/WBS traceability: a new 9-step interactive tutorial/onboarding system, API-key gating (red-glow + tooltip) on Process/Reprocess/Process Selected, `RecommendationBadge` past-tense labels for finalized rows, and a Dashboard column rework (10→6). 32/32 Vitest. New §4 Note 13 |

---

## 1. Phase 0 — Project Definition & Systems Engineering (✅ Complete)

| ✅ | WBS # | Task | Outcome | Date | Traceability |
|---|---|---|---|---|---|
| ✅ | **0.1** | **Project Setup** | Initialized git repo; created public GitHub repo `gratefulgabe5000/ttb-label-verifier`; scaffolded `README.md` and `_DevLog/DevLog.md` | 2026-06-09 | DevLog §7 Session 1 |
| ✅ | **0.2** | **Problem Identification** | Reviewed assessment notification, submission form, and `_ProblemStatement/3.Assessment_README.txt` (4 stakeholder interviews); framed the COLA label-verification problem and the 5-second per-application processing constraint | 2026-06-09 | DevLog §1; PR-001 |
| ✅ | **0.3** | **Resource Collection** | Collected the official TTB Form F 5100.31 (`f510031.pdf`); catalogued source documents in DevLog §1 Source Documents table | 2026-06-09 | DevLog §1 |
| ✅ | **0.4** | **Requirement Extraction** | Derived Req-01–27 from interviews (§2.1); documented Government Warning text/format rules (§2.2), full Form F 5100.31 field reference Items 1–18 (§2.3), application-type/determination logic (§2.4), Parameter Comparison Matrix (§2.5), Section V Allowable Revisions reference (§2.6) | 2026-06-09 | DevLog §2 |
| ✅ | **0.5** | **Design Brainstorming** | Defined the 6-stage processing pipeline (§3.2), UI architecture/mockups for Dashboard / Detail View / Batch Report (§3.3), 8-table DB schema (§3.4), 10-endpoint API surface (§3.5) | 2026-06-09 | DevLog §3.2–3.5 (v1) |
| ✅ | **0.6** | **Tech Approach Planning** | Pivoted from Streamlit to React+Vite+TS / FastAPI+SQLAlchemy+SQLite / Claude Sonnet vision (Decisions 1–5) | 2026-06-09 | DevLog §4.2 Decisions 1–5 |
| ✅ | **0.7** | **PRD Development and Initial Design** | Authored `PRD.md` v1.0 (INCOSE-style: US-001–003, FR/PR/IR/UR/SR/CR requirements, traceability matrix, assumptions, glossary); revised to single-pass extraction (FR-010–016, FR-030–036) and multi-image label processing (FR-030–038, A-10/A-11, IA-18/IA-19) | 2026-06-09 | PRD.md v1.0 |
| ✅ | **0.8** | **Trade Studies** | TS-01 (tiered form extraction: pypdf → pdfplumber → Claude Vision, FR-017) and TS-02 (OpenCV preprocessing + Tesseract OCR augmentation, FR-039/040); COLA Registry forward-compat reference (§6, FR-018, REF-07–09). PRD → v1.1 | 2026-06-10 | DevLog §3.1, §6; PRD v1.1 |
| ✅ | **0.9** | **Architecture Evaluation** | End-to-end ideal-scenario walkthrough (§3.6, 15-row executive summary); resolved multi-image tab selector (FR-091), form-panel bbox/location_hint (FR-019, IA-23), Decision 8 (5 refinements). PRD → v1.2 | 2026-06-10 | DevLog §3.6; PRD v1.2 |
| ✅ | **0.10** | **WBS Development** | System diagrams (§3.7: context, block, sequence with nested concurrency); WBS.md v1.0 (13 top-level items, critical path, risk register) | 2026-06-10 | DevLog §3.7; WBS.md v1.0 |
| ✅ | **0.11** | **Systems Engineering Review** | Renamed DevLog §5 "Assumptions" → "Initial Assumptions" (IA-01–26) to deconflict with PRD §8 (A-01–14); re-audited and corrected every cross-document A-/IA- reference; fixed 3 broken PRD self-references | 2026-06-10 | DevLog §5; PRD §8 |
| ✅ | **0.12** | **Documentation Review** | Assumptions-completeness audit → PRD v1.3 (A-15/16/17, FR-066); comparison-matrix completeness audit → PRD v1.4 (FR-100–107); updated DevLog §5 IA cross-references and TODO.md Session 7 | 2026-06-10 | PRD v1.3/v1.4; TODO.md Session 7 |
| ✅ | **0.13** | **WBS Re-Baseline (v2.0)** | Rewrote `WBS.md` as a single dependency-ordered Phase 1 sequence (1.0–21.0); added Phase 0 (0.1–0.12); re-scoped Stage 5 Comparison Engine to 16 sub-items covering FR-066/FR-100–107; re-sequenced synthetic test data to 2.0; removed hour estimates and target dates | 2026-06-11 | TODO.md Session 8; WBS.md v2.0 |
| ✅ | **0.14** | **Documentation Consistency Pass (v2.0 Baseline)** | Cross-document review of README/PRD/DevLog/WBS/TODO; corrected footer versions, TOC anchors, section cross-references, and DevLog Engineering Log coverage (Sessions 7–8); bumped PRD to v2.0; synchronized all five documents to a unified v2.0 baseline | 2026-06-11 | TODO.md Session 9; PRD.md v2.0 |

---

## 2. Phase 1 — Implementation Sequence

| ✅ | WBS # | Task | Depends On | Traceability |
|---|---|---|---|---|
| ✅ | **1.0** | **Backend Scaffolding & Infrastructure** | Phase 0 | DevLog §3.4–3.5 |
| ✅ | 1.1 | Initialize FastAPI app structure (`app/`: `main.py`, `routers/`, `services/`, `models/`, `schemas/`, dependency injection, error handling, OpenAPI docs) | 1.0 | DevLog §3.5 |
| ✅ | 1.2 | Configure SQLAlchemy + SQLite (`db.py`: engine, session factory, `Base`, `create_all()` bootstrap) | 1.1 | DevLog §3.4 |
| ✅ | 1.3 | Define ORM models for all 8 tables (`agents`, `applications` incl. 8 COLA forward-compat columns, `label_images`, `form_parameters` incl. `bbox_json`/`location_hint`, `label_parameters` incl. `bbox_json`/`header_height_ratio`, `comparisons`, `determinations`, `batches`) | 1.2 | FR-018, FR-019, IA-23, DevLog §3.4 |
| ✅ | 1.4 | Configure environment variables (`.env`: `ANTHROPIC_API_KEY`, JWT secret, DB path, upload volume path) | 1.1 | SR-001, IA-26 |
| ✅ | 1.5 | Configure CORS middleware | 1.1 | IR-006 |
| ✅ | 1.6 | Minimal "hello world" smoke-test deploy to Railway — verify Tesseract install path (Aptfile/`nixpacks.toml`), persistent volume mount, and env vars resolve in the deployed environment before feature code depends on them | 1.1, 1.4 | IA-26, Decision 8 (deployment watch-items) |

| ✅ | **2.0** | **Synthetic Test Data Preparation** *(parallel with 1.0; must complete before the unit/integration tests in 5.7, 6.8, 7.16, 8.5, 9.7, 10.4, 16.x consume it)* | Phase 0 | TS-01, TS-02 |
| ✅ | 2.1 | Inventory and organize existing `testdata/` into a manifest mapping each set to its expected pass/fail outcome | 2.0 | TS-02 |
| ✅ | 2.2 | Produce sample F 5100.31 PDFs covering all three TS-01 tiers: (a) filled AcroForm, (b) flattened/text-layer-only, (c) scanned/image-only | 0.3 | TS-01, FR-017 |
| ✅ | 2.3 | Build "good" (all-fields-match) application + label sets for each product type (wine, spirits, malt beverage) | 2.1, 2.2 | §2.5 Comparison Matrix |
| ✅ | 2.4 | Build "hard failure" sets — one per comparison rule (brand name, government warning text/format, "for sale in [STATE]", country of origin, fanciful name, product/class-type, applicant name, applicant address, grape varietals, wine appellation, ABV, net contents) | 2.1, 2.2 | FR-050–059, FR-066, FR-100–107 |
| ✅ | 2.5 | Build "possible allowable revision" sets (case/punctuation brand differences, in-state address change, color/font differences) | 2.1 | §2.6 Allowable Revisions, FR-057/059 |
| ✅ | 2.6 | Build a small set of degraded-quality images (angle, glare, low light) for OpenCV preprocessing tests | 2.1 | FR-039 |
| ✅ | 2.7 | Build a Type 14b ("for sale in one state only") application + matching/non-matching label set | 2.1, 2.2 | FR-056 |

| ✅ | **3.0** | **Backend — Authentication & Authorization** | 1.3 | SR-001, SR-002 |
| ✅ | 3.1 | `Agent` ORM model + seed script for initial agent accounts (password hashing via passlib) | 1.3 | SR-001, SR-002 |
| ✅ | 3.2 | `POST /auth/login` (JWT issuance via python-jose) | 3.1 | SR-001, DevLog §3.5 |
| ✅ | 3.3 | JWT validation dependency (current-agent), applied to all protected routers | 3.2 | SR-002 |
| ✅ | 3.4 | Unit tests: auth (login success/failure, token validation/expiry) | 3.3 | SR-001, SR-002 |

| ✅ | **4.0** | **Backend — Stage 1–2: Ingestion** | 1.3, 3.3 | DevLog §3.2 Stages 1–2 |
| ✅ | 4.1 | `POST /applications` — multipart upload (form PDF + N label images), batch grouping | 1.3, 3.3 | FR-001–006 |
| ✅ | 4.2 | File validation (file types, size limits, required-field presence) | 4.1 | FR-007, IR-002, IR-003 |
| ✅ | 4.3 | Persist uploaded files to disk/volume; insert `applications` + `label_images` rows | 4.1, 4.2, 1.6 | IA-26 |
| ✅ | 4.4 | `GET /applications` (list, filter by applicant) | 4.3 | FR-070–072 |
| ✅ | 4.5 | `GET /applications/{id}` (full detail incl. associated `label_images`) | 4.3 | DevLog §3.5 |
| ✅ | 4.6 | Unit tests: ingestion (valid/invalid uploads, batch grouping, listing/filtering) using 2.2 | 4.5, 2.2 | FR-001–007 |

| ✅ | **5.0** | **Backend — Stage 3: Form Assessment (TS-01 Tiered Extraction)** | 4.5 | TS-01, DevLog §3.2 Stage 3 |
| ✅ | 5.1 | Tier 1 — `pypdf` AcroForm field reader; map field names to Items 1–18; capture `/Rect` → `bbox_json` | 4.5 | TS-01, FR-017, FR-019, IA-23 |
| ✅ | 5.2 | Tier 2 — `pdfplumber` text-layer fallback; region mapping; word bbox → `bbox_json` | 5.1 | TS-01, FR-017, FR-019, IA-23 |
| ✅ | 5.3 | Tier 3 — Claude Vision fallback; prompt design with prompt caching (IA-25); JSON schema for all 18 Part I fields; `location_hint` fallback when no bbox is available | 5.2 | FR-010–016, FR-019, IA-23, IA-25 |
| ✅ | 5.4 | Field normalization (source/origin, product type, application type 14a–d parsing, grape varietals list) | 5.3 | FR-012–015 |
| ✅ | 5.5 | Confidence scoring + `extraction_method` recording (which tier resolved each field) | 5.4 | FR-016, FR-017 |
| ✅ | 5.6 | Persist to `form_parameters` (incl. `bbox_json`/`location_hint`) | 5.5 | DevLog §3.4 |
| ✅ | 5.7 | Unit tests: Stage 3 — each tier individually, tiered fallback ordering, field normalization, using 2.2's sample PDFs | 5.6, 2.2 | FR-010–019 |

| ✅ | **6.0** | **Backend — Stage 4: Label Assessment (TS-02)** | 4.5 | TS-02, DevLog §3.2 Stage 4 |
| ✅ | 6.1 | OpenCV preprocessing pipeline (deskew, contrast/CLAHE, glare suppression) | 4.5 | TS-02, FR-039 |
| ✅ | 6.2 | Claude Vision label-extraction prompt (mandatory + secondary elements + generic `other_text`) | 6.1 | FR-030–033 |
| ✅ | 6.3 | Government Warning detection (exact-text + bold/caps check) | 6.2 | FR-034, FR-035 |
| ✅ | 6.4 | Tesseract OCR pass — text + bbox detection | 6.1 | FR-040 |
| ✅ | 6.5 | Fuzzy-match Claude-extracted values to OCR bboxes; compute `header_height_ratio` | 6.2, 6.4 | FR-040 |
| ✅ | 6.6 | Per-image concurrent execution (`asyncio.gather` across an application's label images; Claude-vs-OCR concurrency within each image) | 6.5 | IA-19, DevLog §3.7 sequence diagram |
| ✅ | 6.7 | Persist to `label_parameters` (one row per `label_image_id` × field_name, incl. `bbox_json`/`header_height_ratio`) | 6.6 | FR-038, DevLog §3.4 |
| ✅ | 6.8 | Unit tests: Stage 4 — preprocessing on degraded images (2.6), extraction parsing, OCR fuzzy-match, government warning detection, using 2.1/2.4 | 6.7, 2.1, 2.6 | FR-030–040 |

| ✅ | **7.0** | **Backend — Stage 5: Comparison Engine** *(re-scoped for FR-066, FR-100–107)* | 5.6, 6.7 | DevLog §3.2 Stage 5 |
| ✅ | 7.1 | Multi-image resolution helper — a form value is "on label" if found on **any** associated label image; shared by every comparison rule below | 5.6, 6.7 | A-10, IA-18, FR-038 |
| ✅ | 7.2 | Brand Name comparison (case/punctuation-tolerant) | 7.1 | FR-050–052 |
| ✅ | 7.3 | Government Warning comparison (exact-text + bold/caps via `header_height_ratio`) | 7.1 | FR-053–055 |
| ✅ | 7.4 | Type 14b "for sale in [STATE]" check | 7.1 | FR-056 |
| ✅ | 7.5 | Section V Allowable-Revision classification mapping (flags POSSIBLE_ALLOWABLE vs HARD_FAILURE for the rules below) | 7.2, 7.3, 7.4 | FR-057, FR-059, §2.6 |
| ✅ | 7.6 | Country of Origin comparison (conditional on Item 3 = "imported") | 7.1 | A-17, FR-066 |
| ✅ | 7.7 | Fanciful Name comparison (Item 7) | 7.1 | FR-100 |
| ✅ | 7.8 | Product Type / Class-Type consistency (Item 5) | 7.1 | FR-101 |
| ✅ | 7.9 | Applicant Name comparison (Item 8) | 7.1 | FR-102 |
| ✅ | 7.10 | Applicant Address comparison (Item 8/8a, incl. in-state Allowable Revision per Section V) | 7.1, 7.5 | FR-103 |
| ✅ | 7.11 | Grape Varietals comparison (Item 10, Wine only) | 7.1, 5.4 | FR-104 |
| ✅ | 7.12 | Wine Appellation comparison (Item 11, Wine only, conditional) | 7.1, 5.4 | FR-105 |
| ✅ | 7.13 | ABV presence check | 7.1 | FR-106 |
| ✅ | 7.14 | Net Contents presence check | 7.1 | FR-107 |
| ✅ | 7.15 | Persist all results to `comparisons` table | 7.2–7.14 | FR-058, DevLog §3.4 |
| ✅ | 7.16 | Unit tests: comparison engine — one test per rule (7.2–7.14) covering MATCH/HARD_FAILURE/POSSIBLE_ALLOWABLE outcomes, plus the multi-image resolution helper (7.1), using 2.3/2.4/2.5/2.7 | 7.15, 2.3, 2.4, 2.5, 2.7 | FR-050–059, FR-066, FR-100–107, A-10, IA-18 |

| ✅ | **8.0** | **Backend — Stage 6: Determination & Reporting** | 7.15 | DevLog §3.2 Stage 6 |
| ✅ | 8.1 | Determination logic — APPROVE / DENY / RECOMMEND_EXEMPTION_REVIEW | 7.15 | FR-060–062 |
| ✅ | 8.2 | Hard-failure list and allowable-revision list generation per application | 8.1 | FR-063, FR-064 |
| ✅ | 8.3 | Per-application determination report schema | 8.2 | FR-065 |
| ✅ | 8.4 | Persist to `determinations` table | 8.3 | DevLog §3.4 |
| ✅ | 8.5 | Unit tests: Stage 6 — all 3 determination outcomes plus edge cases (e.g., no hard failures but unresolved possible-allowables), using 2.3/2.4 | 8.4, 2.3, 2.4 | FR-060–065 |

| ✅ | **9.0** | **Backend — Pipeline Orchestration & Batch Processing** | 5.6, 6.7, 7.15, 8.4 | DevLog §3.7 sequence/block diagrams |
| ✅ | 9.1 | Single-application orchestrator — runs Stages 3–6 with concurrent-compute / sequential-persist write pattern | 5.6, 6.7, 7.15, 8.4 | IA-24 |
| ✅ | 9.2 | `POST /applications/{id}/process` | 9.1 | FR-074 |
| ✅ | 9.3 | Batch Orchestrator — bounded-concurrency semaphore (3–5 applications in flight) | 9.1 | A-07, IA-17, DevLog §3.7 block diagram |
| ✅ | 9.4 | `POST /batch/process`; insert `batches` row | 9.3 | DevLog §3.5 |
| ✅ | 9.5 | `GET /batch/{id}/status` (polling) | 9.4 | FR-075 |
| ✅ | 9.6 | `GET /applications/{id}/comparisons` | 7.15 | DevLog §3.5 |
| ✅ | 9.7 | Unit/integration tests: orchestration — concurrency bounds (9.3), status transitions (9.5), per-application timing against PR-001, using 2.3 | 9.6, 2.3 | PR-001, A-07, IA-17, IA-19, IA-24 |

| ✅ | **10.0** | **Backend — Overrides, Finalization & Batch Report** | 9.6 | FR-086–097 |
| ✅ | 10.1 | `POST /determinations/{id}/override` — per-parameter and overall overrides with audit fields (agent, timestamp, reason) | 9.6 | FR-086–089, SR-004 |
| ✅ | 10.2 | `POST /determinations/{id}/finalize` — overrides do not re-run the AI pipeline (A-15); retention through `finalized_at` (A-16, SR-003) | 10.1 | FR-090, A-15, A-16 |
| ✅ | 10.3 | `GET /batch/{id}/report` — counts by outcome + most common failure type | 10.2 | FR-095–097 |
| ✅ | 10.4 | Unit tests: overrides, finalize, batch report, using 2.3/2.4 | 10.3, 2.3, 2.4 | FR-086–090, FR-095–097, SR-004 |

| ✅ | **11.0** | **Frontend Scaffolding & Infrastructure** *(can start in parallel with 1.0)* | Phase 0 | DevLog §4.1 |
| ✅ | 11.1 | Initialize Vite + React + TS project (`web/`) | 11.0 | DevLog §4.1 |
| ✅ | 11.2 | Configure Tailwind CSS 4 | 11.1 | DevLog §4.1 |
| ✅ | 11.3 | Install + configure shadcn/ui (Tabs, Dialog, ContextMenu, Table, Badge) | 11.2 | Decision 8 #5, FR-091 |
| ✅ | 11.4 | Install react-pdf + React Query | 11.1 | DevLog §4.1 |
| ✅ | 11.5 | Project structure (`pages/`, `components/`, `hooks/`, `lib/` API client) | 11.1 | — |
| ✅ | 11.6 | Auth context/hooks + login page | 11.5, 3.2 | SR-001 |
| ✅ | 11.7 | Typed API client matching backend schemas | 11.5, 4.5, 5.6, 6.7, 7.15, 8.4 | DevLog §3.5 |

| ✅ | **12.0** | **Frontend — Agent Dashboard** *(re-sequenced ahead of 6.0 — §4 Note 7)* | 11.7, 4.4 | FR-070–077 |
| ✅ | 12.1 | Application list table (serial #, applicant, type, status) | 11.7, 4.4 | FR-070, FR-071 |
| ✅ | 12.2 | Filter by applicant *(Pass 1)* | 12.1 | FR-072 |
| ✅ | 12.3 | Checkbox batch selection *(Pass 1)* | 12.1 | FR-073 |
| ✅ | 12.4 | "Process Selected" action + progress indicator (polls 9.5) *(Pass 2)* | 12.3, 9.4, 9.5 | FR-074, FR-075, UR-004 |
| ✅ | 12.5 | Result badges (✅/❌/⚠️) *(Pass 2)* | 12.4, 8.4 | FR-076, UR-002 |
| ✅ | 12.6 | Batch summary header *(Pass 2)* | 12.4 | FR-077 |
| ✅ | 12.7 | Upload-new modal (form PDF + N label images) | 12.1, 4.1 | FR-001–006 |
| ✅ | 12.8 | Unit tests (Vitest): Dashboard — list/filter/selection/badges/upload modal *(covers 12.1–12.3/12.7 from Pass 1, plus 12.4–12.6 from Pass 2 — 13/13 tests passing)* | 12.7 | FR-070–077 |

| ✅ | **13.0** | **Frontend — Application Detail View** *(re-sequenced ahead of 6.0 — §4 Note 7)* | 11.7, 5.6, 6.7, 7.15 | FR-080–091 |
| ✅ | 13.1 | Split-view layout (form PDF left / label image(s) right) *(Pass 1)* | 11.7, 4.5 | FR-080, FR-081 |
| ✅ | 13.2 | react-pdf form renderer *(Pass 1)* | 13.1 | FR-080 |
| ✅ | 13.3 | Multi-image tab selector with thumbnails *(Pass 1)* | 13.1 | FR-091 |
| ✅ | 13.4 | SVG annotation overlay — form panel (positioned via `form_parameters.bbox_json`/`location_hint`) *(Pass 1 — requires `_to_detail()` fix to surface persisted `form_parameters`)* | 13.2, 5.6 | FR-019, FR-082, IA-23 |
| ✅ | 13.5 | SVG annotation overlay — label panel (positioned via `label_parameters.bbox_json`/`header_height_ratio`) *(Pass 2)* | 13.3, 6.7 | FR-083 |
| ✅ | 13.6 | Mouse-over cross-highlighting between form and label annotations *(Pass 2)* | 13.4, 13.5 | FR-084 |
| ✅ | 13.7 | Parameter results table (per-field comparison outcomes) *(Pass 2)* | 13.1, 7.15, 9.6 | FR-085 |
| ✅ | 13.8 | Right-click override context menu + modal (per-parameter) *(Pass 2)* | 13.7, 10.1 | FR-086, FR-087 |
| ✅ | 13.9 | Overall-determination override control *(Pass 2)* | 13.8, 10.1 | FR-089 |
| ✅ | 13.10 | Finalize action *(Pass 2)* | 13.9, 10.2 | FR-090 |
| ✅ | 13.11 | Auto-tab-switch when an annotation references a specific `label_image_id` *(Pass 2)* | 13.3, 13.6 | FR-091 |
| ✅ | 13.12 | Unit tests (Vitest): Detail View — annotation rendering, tab switching/auto-switch, cross-highlight, override modal, finalize *(covers 13.1–13.4 from Pass 1, plus 13.5–13.11 from Pass 2 — 13/13 tests passing)* | 13.11 | FR-080–091 |

| ✅ | **14.0** | **Frontend — Batch Report View** — **COMPLETE** (Session 24, `BatchReportPage.tsx`, wired live to `GET /batch/{id}/report`) | 11.7, 10.3 | FR-095–097, UR-003 |
| ✅ | 14.1 | Report layout — counts by outcome *(summary stat cards: total/approved/denied/exemption review, plus a processing indicator while incomplete)* | 11.7, 10.3 | FR-095, FR-096 |
| ✅ | 14.2 | Common-failure-type display *(`most_common_failure` shown beneath the summary cards, "None" when absent)* | 14.1 | FR-097 |
| ✅ | 14.3 | CSV export *(`lib/csv.ts` — `toCsv`/`downloadCsv`; "Export CSV" button writes one row per application incl. applicant, serial #, status, recommendation)* | 14.1 | UR-003 |
| ✅ | 14.4 | PDF export *(optional / stretch)* — *("Print / Save as PDF" via `window.print()`; `print:hidden` added to AppShell header/API-key banner and the report's action buttons for a clean printout)* | 14.1 | UR-003 |
| ✅ | 14.5 | Unit tests (Vitest): Batch Report — counts, failure-type display, export *(`BatchReportPage.test.tsx`, 5 tests, plus a Dashboard "View Report" wiring test — 21/21 Vitest passing)* | 14.3 | FR-095–097 |

| ✅ | **15.0** | **Integration — Frontend ↔ Backend Wiring** — **COMPLETE** (Session 25 — 15.1–15.4 confirmed already wired via 12.0–14.0; 15.5 added the two remaining plain-English error states) | 12.8, 13.12, 14.5, 9.5, 10.2, 10.3, 11.6 | — |
| ✅ | 15.1 | Wire Dashboard (12.0) to `GET /applications`, `POST /batch/process`, `GET /batch/{id}/status` *(already wired as part of 12.4–12.6; confirmed by audit, no changes needed)* | 12.8, 9.5 | — |
| ✅ | 15.2 | Wire Detail View (13.0) to `GET /applications/{id}`, `POST /determinations/{id}/override`, `POST /determinations/{id}/finalize` *(already wired as part of 13.8–13.10; confirmed by audit, no changes needed)* | 13.12, 10.2 | — |
| ✅ | 15.3 | Wire Batch Report (14.0) to `GET /batch/{id}/report` *(already wired as part of 14.1; confirmed by audit, no changes needed)* | 14.5, 10.3 | — |
| ✅ | 15.4 | Wire auth flow — login → JWT storage → authenticated requests on all endpoints *(already wired via `AuthContext`/`apiFetch`/`ProtectedRoute`; confirmed by audit, no changes needed)* | 11.6, 3.3 | SR-001, SR-002 |
| ✅ | 15.5 | Plain-English error handling/surfacing across all wired views *(audit found two gaps: `comparisonsQuery.isError` was unhandled in `ResultsSidebar`/`ParameterResultsTable` — "Failed to load comparison results. Please try again."; `batchStatusQuery.isError` was unhandled in `DashboardPage` — added a dismissible retry banner "Failed to load status for batch #{id}...". 2 new Vitest tests, 30/30 passing)* | 15.1, 15.2, 15.3, 15.4 | UR-003 |

| ❌ | **16.0** | **Integration Testing** *(localhost, against synthetic data)* | 15.5, 2.0 | PR-001, PR-002, PR-004 |
| ✅ | 16.1 | End-to-end pipeline test per product type (wine/spirits/malt) using 2.3–2.7 *(Session 28 — 18-app re-sweep, `testdata/resweep.py`: 13/18 PASS; all 5 remaining mismatches plus app17/app18 root-caused as test-data/AcroForm issues, not code defects — §4 Note 12)* | 15.5, 2.0 | §2.5 Comparison Matrix, FR-050–059, FR-066, FR-100–107 |
| ❌ | 16.2 | PR-001 timing verification (≤5s/application incl. all label images) | 16.1 | PR-001 |
| ❌ | 16.3 | Bounded-concurrency batch test | 16.1, 9.3 | A-07, IA-17, PR-002, PR-004 |
| ❌ | 16.4 | Multi-image resolution test — value present on a non-primary image still satisfies the field | 16.1, 7.1 | A-10, IA-18 |
| ❌ | 16.5 | Override + finalize flow test — confirm overrides do not re-run the AI pipeline | 16.1, 10.2, 13.10 | A-15 |
| ❌ | 16.6 | Annotation placement test — `bbox_json` vs `location_hint` fallback on Tier-3/degraded cases | 16.1, 13.4, 13.5, 2.6 | FR-019, FR-036, FR-040 |

| ❌ | **17.0** | **Localhost End-to-End Manual Testing** | 16.6 | DevLog §3.6 |
| ❌ | 17.1 | Full user-path walkthrough: login → dashboard → batch select → process → detail view → override → finalize → batch report (mirrors §3.6 ideal-scenario path) | 16.6 | DevLog §3.6 |
| ❌ | 17.2 | Usability checks — UR-001–006 (≤3 interactions to key actions, color/icon distinctness, plain-English errors, load times, no-scroll primary controls) | 17.1 | UR-001–006 |
| ❌ | 17.3 | Browser compatibility check (Chrome, Edge, Firefox) | 17.1 | IR-006 |
| ❌ | 17.4 | Edge-case walkthrough — degraded images, Type 14b, blank Item 7/11, missing optional fields | 17.1, 2.6, 2.7 | FR-039, FR-056, FR-104, FR-105 |

| ✅ | **18.0** | **Setup & Deployment** — **COMPLETE** (Session 27, executed ahead of 16.0/17.0 per §4 Note 11) | 17.4, 1.6 | IA-26, Decision 8 |
| ✅ | 18.1 | Railway: deploy backend to the project smoke-tested in 1.6; attach persistent volume for SQLite DB + uploaded files *(volume mounted at `/data`; live at https://ttb-label-verifier-production-c816.up.railway.app)* | 17.4, 1.6 | IA-26 |
| ✅ | 18.2 | Confirm Tesseract OCR binary available in deployed environment (Aptfile/`nixpacks.toml`) *(confirmed in Nixpacks build log — `apt-get install -y tesseract-ocr`)* | 18.1 | TS-02, Decision 8 |
| ✅ | 18.3 | Configure production environment variables on Railway *(DATABASE_URL, UPLOAD_DIR, JWT_SECRET/ALGORITHM/EXPIRE_MINUTES, CORS_ORIGINS, new `SEED_DEMO_AGENTS=true`)* | 18.1 | SR-001 |
| ✅ | 18.4 | Netlify: deploy frontend; configure API base URL env var *(`netlify.toml` + `web/public/_redirects` added; `VITE_API_BASE_URL` set to the Railway URL; live at https://ttb-labelverificationsystem.netlify.app)* | 17.4 | — |
| ✅ | 18.5 | Configure CORS for the deployed cross-origin pair (Netlify ↔ Railway) *(`CORS_ORIGINS=https://ttb-labelverificationsystem.netlify.app`; verified end-to-end login)* | 18.1, 18.4 | IR-006 |
| ✅ | 18.6 | Update `README.md` with the live deployed URL and run instructions *(Live Demo section + Deployment section updated with both URLs and demo credentials)* | 18.5 | CR-005 |

| ❌ | **19.0** | **Post-Deployment End-to-End Testing** | 18.6 | CR-004 |
| ❌ | 19.1 | Re-run the 17.1 user-path walkthrough against the deployed URL (no VPN/special credentials required) | 18.6 | CR-004 |
| ❌ | 19.2 | Re-verify PR-001/PR-003 timing on deployed infrastructure (network latency may differ from localhost) | 19.1 | PR-001, PR-003 |
| ❌ | 19.3 | Cross-browser spot-check on the deployed URL | 19.1 | IR-006 |

| ❌ | **20.0** | **Submission Material Review & Collation** | 19.3 |  |
| ❌ | 20.1 | Final review of `README.md` (setup/run instructions, live URL, known limitations) | 19.3 | CR-005 |
| ❌ | 20.2 | Final review of `DevLog.md` — confirm Engineering Log captures all sessions through deployment | 19.3 | DevLog §7 |
| ❌ | 20.3 | Final consistency check across `PRD.md`/`WBS.md`/`TODO.md` (version numbers, footers, cross-references) | 20.2 | — |
| ❌ | 20.4 | Export remaining chat session transcripts to `_DevLog/` | 20.3 | NOT REQUIRED — transcripts will not be provided as part of this submission |
| ❌ | 20.5 | Repository cleanup — verify `.gitignore` covers secrets/`.env`, confirm no exposed API keys in history | 20.4 | — |
| ❌ | 20.6 | Final lint/format pass on `app/` and `web/` | 20.5 | — |

| ❌ | **21.0** | **Submission** | 20.6 | — |
| ❌ | 21.1 | Verify Microsoft Forms submission link and required fields (repo URL, deployed URL) | 20.6 | TODO.md submission link |
| ❌ | 21.2 | Submit via the assessment submission form (https://forms.osi.office365.us/r/xWrQGduMw7) | 21.1 | — |
| ❌ | 21.3 | Record submission confirmation/timestamp in `DevLog.md` | 21.2 | — |

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

**Execution Order Override (v2.1, 2026-06-11):** Per user direction, WBS 12.0 and 13.0 are pulled forward and executed in two passes:

- **Pass 1** (now, before 6.0): 12.2, 12.3, 13.1–13.4, plus a small backend fix to `applications.py::_to_detail()` so `GET /applications/{id}` returns persisted `form_parameters` rows (needed for 13.4), and two new file-serving endpoints — `GET /applications/{id}/form` and `GET /applications/{id}/label-images/{image_id}` — required by 13.2/13.3 since uploaded files were previously stored on disk but never exposed over HTTP. All build against the already-complete 1.0/3.0/4.0/5.0/11.0.
- **6.0 → 10.0**: backend stages proceed as originally sequenced.
- **Pass 2** (after 10.0, before 14.0): 12.4–12.6, 13.5–13.11, plus the remaining 12.8/13.12 unit-test coverage — completing 12.0/13.0 into their finished UI. ✅ **Complete (Session 21, 2026-06-12)**.
- 14.0 onward proceeds unchanged.

Rationale: front-loading the buildable frontend surfaces lets the user manually verify Dashboard and Detail View behavior as each backend stage lands, rather than waiting until 10.0 completes before any UI is testable. Note: 13.4's SVG overlay renders correctly against an empty `form_parameters` array (shows a "no extracted fields yet" message) since no endpoint yet triggers Stage 3 extraction (`run_stage3_extraction`/`persist_form_parameters` — wired up as part of 6.0+). See §4 Note 7.

---

## 4. Sequencing & Technical Risk Notes

1. **TS-02 OCR bbox uncertainty (6.4–6.5):** if Tesseract fuzzy-matching for `label_parameters.bbox_json` proves unreliable, fall back to Claude-only extraction with `location_hint` (the existing fallback design per IA-13). This degrades 13.5's annotation precision but does not block 7.0/8.0/9.0 — Stage 4's output contract and PR-001 are unaffected either way.

2. **7.1 (multi-image resolution helper) is a single point of shared logic for 13 comparison rules (7.2–7.14).** Validate it thoroughly before fanning out — a defect here would otherwise need to be re-fixed across all 13 call sites and their corresponding unit tests (7.16).

3. **13.0 (Application Detail View) has the most downstream dependents** (15.2, 16.5, 16.6, 17.1, 19.1). If any sub-item slips, 13.3 (multi-image tabs) can ship with a single-image fallback first, per the FR-091 fallback note, deferring full tab UX without blocking 15.0 onward.

4. **14.0 (Batch Report View) has the lowest direct FR traceability** (UR-003 only) and 14.4 (PDF export) is explicitly optional. If a sub-item must be cut, this is the lowest-impact candidate — it does not block 15.0–21.0 for the Dashboard/Detail View, which are the primary graded surfaces.

5. **18.0 (Setup & Deployment) platform risk is front-loaded into 1.6** (smoke-test deploy). Any Railway/Tesseract/persistent-volume issues should surface there, long before 18.0 depends on that configuration working.

6. **2.0 (Synthetic Test Data) is a hard prerequisite for nearly every test item** (5.7, 6.8, 7.16, 8.5, 9.7, 10.4, 16.1–16.6, 17.4). Completing 2.1–2.7 early — in parallel with 1.0 — avoids any backend coding item stalling at its paired unit-test sub-item for lack of fixtures.

7. **(v2.1) 12.0/13.0 re-sequencing:** WBS 12.0 and 13.0 were pulled forward ahead of 6.0–10.0 (Pass 1: 12.2, 12.3, 13.1–13.4 + `_to_detail()` fix), with the remainder (Pass 2: 12.4–12.6, 13.5–13.11) deferred until 6.0–10.0 land. This is safe because Pass 1 items depend only on 1.0/3.0/4.0/5.0/11.0 (all complete) — the dependency graph in §2 is unchanged, only the execution order. Pass 2 items retain their original dependencies (9.4/9.5, 8.4, 6.7, 7.15/9.6, 10.1/10.2) and cannot start until those land regardless of this re-sequencing.

8. **(v2.4) Open product question — importer vs. manufacturer for Item 8 on imported products:** For "Imported" applications, Item 8 (Applicant Name/Address) is filled in by the U.S. importer, but the label's bottler/producer fields usually identify the foreign manufacturer. 7.9/7.10 now check Item 8 against both the label's bottler and importer fields (`compare_applicant_name`/`compare_applicant_address`, OR-match across `["bottler_name","importer_name"]` / `["bottler_address","importer_address"]`), but it is not yet confirmed whether Item 8 should always be expected to match the importer, the manufacturer, or either. Flagged in the frontend Settings dialog ("About..." section) for end-user/product-team resolution before relying on automated determinations for imported-product applications — relevant to 16.1 (per-product-type pipeline test) and 17.4 (edge-case walkthrough).

9. **(v2.6) 15.0 closeout — 15.1–15.4 required no code changes:** because 12.0–14.0 were built directly against the live typed API client (`lib/api-client.ts`) rather than mocked data, the Dashboard/Detail View/Batch Report/auth wiring was already complete by the time 15.0 started. The Session 25 audit confirmed this against the code (queries/mutations call `applicationsApi`/`batchApi`/`determinationsApi`/`authApi`, `AuthContext` listens for `AUTH_UNAUTHORIZED_EVENT` and `ProtectedRoute` redirects to `/login`) and made no changes for 15.1–15.4. The only substantive 15.0 work was 15.5: two views had query-error states that were silently swallowed (`comparisonsQuery.isError` in the Detail View results panels, `batchStatusQuery.isError` in the Dashboard's batch-status poll) — both now surface a `text-destructive` plain-English message per UR-003, and the Dashboard's also offers Retry/Dismiss so the agent isn't left staring at a stuck "processing" state.

10. **(v2.7) Session 26 — real-data comparison fixes, ingestion/dashboard refinements, and DevLog §7 regulatory reference:** Reviewing the running application against real label data surfaced three comparison-engine fixes, all within already-complete items: (a) `_normalize_for_comparison()` (6.1/6.8, used by every text rule in 7.0) now folds diacritics via Unicode NFKD decomposition before stripping punctuation, so accented label text (e.g., "Fête Rosé") matches its unaccented form on the application form; (b) `suppress_glare()` (6.1, FR-039) now skips inpainting when the ≥235-brightness mask covers more than 5% of the image (`MAX_GLARE_AREA_FRACTION`), since a large bright area is usually a plain light label background rather than a glare hot-spot, and inpainting over it was destroying legible text; (c) for imported products, 7.9/7.10 now compare Item 8 (Applicant Name/Address) only against the label's `importer_name`/`importer_address`, never the foreign `bottler_name`/`bottler_address` — **this resolves the open product question in §4 Note 8** in favor of "importer." Separately, per Gabe's direct citation of 27 CFR §§1.A.5.64, 1.A.7.63(a), 1.A.4.32(a)/(b), 1.A.5.63(a)/(b)/5.7, 4.38, 5.63(a), 7.63(a), and 5.65/7.65/4.36, a new DevLog §7 documents mandatory-label-element coverage per product type, and three rule changes were made within 7.0: 7.2 (`compare_brand_name`) now falls back to the bottler/importer name-and-address statement when no Brand Name is on the label (§1.A.5.64 — live-verified against application #1, Woodford Reserve, MATCH instead of HARD_FAILURE); 7.13 (`compare_abv`) now checks ABV phrasing against the four approved formats of §§5.65/7.65/4.36, downgrading non-conforming phrasing to POSSIBLE_ALLOWABLE (Sec. V item 3b); and a new rule `compare_field_of_vision` (field_name `label_field_of_vision`, added to `COMPARISON_RULES`) checks that Brand Name, Class/Type, and ABV co-occur on one label image per §§4.38/5.63(a)/7.63(a). Outside the comparison engine, 4.0/5.0/12.0 gained `permit_no`/`fanciful_name`/`ttb_id`/`class_type_code`/`origin_code` registry fields (auto-populated on upload via `_resolve_label_field()`/`_update_registry_fields()`, with TTB IDs auto-assigned via `_next_ttb_id`), a sortable/filterable 10-column Dashboard, and a `DELETE /applications` "Delete All" admin action. No new WBS line items or PRD FR numbers were added for `compare_field_of_vision` — flagged as an optional follow-up if formal traceability is desired. 222/222 backend pytest, 32/32 frontend Vitest, lint clean.

11. **(v2.8) Execution-order override — WBS 18.0 completed ahead of 16.0/17.0 (Session 27):** Per Gabe's direction ("get this deployed and live now — we'll come back to 16.0 after"), WBS 18.0 (Setup & Deployment) was executed immediately following 15.0, ahead of its nominal §3 predecessors 16.0 (Integration Testing) and 17.0 (Localhost E2E Testing). This is safe because 18.0's actual prerequisites — a working backend/frontend pair plus the 1.6 Railway smoke-test deploy — were already satisfied by 1.0–15.0; 16.0/17.0 validate *correctness* of the already-built pipeline, not *deployability*. The app is now live end-to-end: **frontend** https://ttb-labelverificationsystem.netlify.app, **backend** https://ttb-label-verifier-production-c816.up.railway.app (Tesseract installed via Nixpacks per 18.2; persistent `/data` volume for SQLite DB + uploads; new `SEED_DEMO_AGENTS=true` env flag auto-creates the `agent1`/`agent2` demo accounts on boot so the documented credentials work without shell access). Login verified end-to-end (Netlify → Railway, JWT issued). 16.0 and 17.0 remain pending and are next up — once complete, 19.0 (Post-Deployment E2E Testing) can run directly against these live URLs without any further deployment work.

12. **(v2.9) Session 28 — FR-106 simplification, 7 comparison-engine match-fallback fixes, 18-app re-sweep (16.1 complete), and a CRITICAL reprocess data-loss fix:** Resuming 16.0, running the 18 synthetic test sets (apps 6–23) against the live backend surfaced seven real-data comparison gaps, all fixed within already-complete 7.2/7.7/7.8/7.9/7.12/7.13: (a) FR-106 (`compare_abv`) is now a presence-only check — `ABV_RANGES` (a hardcoded per-product-type plausible-range table with no basis in Form F 5100.31, which has no ABV field) is removed; (b) 7.8 (`compare_class_type`) recognizes EU/Italian wine-designation terms (rosso/bianco/igt/doc/docg/etc.); (c) 7.12 (`compare_wine_appellation`) gains a German umlaut-transliteration match (`_german_transliteration_matches`/`_GERMAN_DIGRAPHS`, e.g. "Niederösterreich" vs "Niederoesterreich"); (d) `_extract_state` now recognizes period-formatted state codes (e.g. "P.A."); (e)–(g) 7.2/7.7/7.9 (`compare_brand_name`/`compare_fanciful_name`/`compare_applicant_name`) gain a shared `_contains_match` fallback (form value found as a substring of a longer label value), and 7.2 additionally gains a brand_name↔fanciful_name field-swap fallback for labels where Stage 4 extracts a stylized brand name into `fanciful_name` and a separate producer name into `brand_name`. A re-sweep of all 18 sets (new `testdata/resweep.py`) confirmed **13/18 PASS — the same 5 failures as the pre-fix baseline** (no regressions), and **16.1 is marked complete**: all 5 remaining mismatches (app6, app7, app15, app20, app23) share one root cause — a correct `applicant_address` POSSIBLE_ALLOWABLE finding (FR-103/Sec. V item 19, in-state address change) that prevents `recommendation` from ever equalling `expected_outcome` for those sets, a test-data design limitation rather than a code defect — and the two AcroForm anomalies (app17 `wine_appellation`="Chianti Classico", app18 `product_type`="malt_beverages", both confidence=1.0 baked into the test PDFs) are confirmed test-PDF errors, not fixable via re-extraction. Separately, while investigating these mismatches, found and fixed a **CRITICAL data-loss bug** in 9.1: `/reprocess/form` and `/reprocess/label` could overwrite good Stage 3/4 data with the FR-011/IA-02 all-null skeleton if extraction returned nothing on reprocess (e.g. API key unconfigured) — both endpoints now detect this case via new `_form_results_are_empty`/`_label_results_are_empty`/`_is_blank_label_parameter` helpers and refuse to persist, marking the application `ERROR` instead. 2 new tests; full suite 224/224.

13. **(v2.10) Session 29 — Item 8 City+State interim policy, `finalized_at` reset on reprocess, and frontend UX additions (tutorial system, API-key gating, Dashboard column rework):** Two backend refinements within already-complete items: (a) 7.9/7.10 — implementing the City+State interim policy already documented in the Settings → About panel (§4 Note 8), new `_find_state_span`/`_extract_city_state` extract a normalized (city, state) pair from a free-form address, and `address_matches` now treats a City+State match as a full MATCH even when the street address differs entirely or is absent (the label frequently gives only "City, State" for the importer/bottler); `classify_address_mismatch` now only handles genuine city/state differences. `TestApplicantAddress` goes from 6 to 9 tests (net +3). (b) 8.4/10.2 — `persist_determination` now clears `determination.finalized_at` whenever Stage 5/6 is recomputed (process or any `/reprocess/{form,label,comparison}`), so a stale "Finalized" status no longer survives a reprocess; new parametrized `test_reprocess_reverts_finalized_status` (3 cases) confirms this for all three reprocess stages. Full suite **230/230**. Separately, four frontend UX items with **no PRD FR or WBS line item** (loosely anchored to UR-001/UR-005, optional follow-up for formal traceability if desired): a new 9-step interactive tutorial/onboarding system (`TutorialProvider`/`useTutorialAnchor`/`TutorialPopup`, anchored across `LoginPage`/`AppShell`/`UploadApplicationDialog`/`DashboardPage`/`ResultsSidebar`/`ApplicationDetailPage`/`DeterminationPanel`, with a "Reset Tutorial" action in Settings); API-key gating (red-glow border + tooltip) on the Process/Reprocess and Process Selected buttons via `useApiKeyConfigured()`; a `RecommendationBadge` `tense="past"` variant for finalized Dashboard rows ("Approved"/"Denied"/"Recommended for Exemption Review"); and a Dashboard column rework dropping Serial Number/Upload Date/Completed Date/Origin Desc (10 → 6 columns: TTB ID, Permit No., Brand Name, Fanciful Name, Class/Type Desc, Status). A `useTutorialAnchor`/`useApiKeyConfigured` regression in `DashboardPage.test.tsx`/`ApplicationDetailPage.test.tsx` (missing `TutorialProvider`/`settingsApi` mocks) was fixed; **32/32 Vitest**, lint clean.

---

**TTB Label Verification System**  
*Copyright (c) 2026 Matthew Gabriel Sizemore · Assessment submission: IT Specialist (AI) · 26-DO-12891471-DH*
