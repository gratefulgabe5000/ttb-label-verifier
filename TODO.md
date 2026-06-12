# TODO — TTB Label Verification System

**Assessment:** IT Specialist (AI) · 26-DO-12891471-DH
**Received:** June 9, 2026, 1458 hrs · **Deadline:** June 16, 2026, 1458 hrs
**Repo:** https://github.com/gratefulgabe5000/ttb-label-verifier
**Documentation Baseline:** v2.0 — README, PRD (v2.0), DevLog, and TODO are mutually consistent as of Session 9 (2026-06-11); WBS bumped to v2.1 same day for the 12.0/13.0 re-sequencing (§4 Note 7)

---

## Status at a Glance

| Deliverable | Status |
|---|---|
| Public GitHub repo | ✅ Created |
| `README.md` (setup/run instructions) | ✅ Drafted (no runnable code yet) |
| `_DevLog/DevLog.md` (approach, tools, assumptions, design) | ✅ Comprehensive |
| `_DevLog/PRD.md` (INCOSE-style PRD + user stories + traceability) | ✅ Drafted, revised v1.1–v1.4 (2026-06-10), v2.0 (2026-06-11) |
| Trade studies (TS-01 form extraction tiering, TS-02 label OpenCV/OCR augmentation) + COLA registry forward-compat reference | ✅ Complete (2026-06-10) |
| Architecture evaluation (DevLog §3.6) + alternatives brainstorm | ✅ Complete (2026-06-10) |
| Mermaid diagrams (system context, block diagram, concurrency sequence) | ✅ Complete (2026-06-10) — DevLog §3.7 |
| Work Breakdown Structure | ✅ Complete, re-baselined to v2.0 (2026-06-11) — [`WBS.md` v2.0](_DevLog/WBS.md) |
| Backend (`app/`) | 🔶 Scaffolding + Auth + Ingestion + Form Assessment + Label Assessment complete (WBS 1.0, 3.0, 4.0, 5.0, 6.0; 81/81 pytest passing, Railway config) — WBS 7.0–10.0 remaining |
| Frontend (`web/`) | 🔶 Scaffolding complete (WBS 11.0 + Settings/API-key UI, build & lint passing). **12.0/13.0 re-sequenced ahead of 6.0 (WBS.md v2.1)** — Pass 1 (12.1–12.3, 12.7, 13.1–13.4) ✅ done, incl. Vitest setup + tests (12.8/13.12 partial); Pass 2 (12.4–12.6, 13.5–13.11) and 14.0 remain |
| Synthetic test data (sample forms + multi-image label sets) | ✅ 2.1–2.7 complete — ALL OF WBS 2.0 DONE (`testdata/manifest.json` — 45 products / 88 images; `testdata/forms/sample_creek_*.pdf` — TS-01 3-tier fixtures; `testdata/forms/good_*.pdf` + `testdata/forms/hf_*.pdf` + `testdata/forms/ar_*.pdf` + `testdata/forms/type14b_*.pdf` + `testdata/test_sets.json` — 2.3 "good" sets + 2.4 "hard failure" sets + 2.5 "possible allowable revision" sets + 2.7 Type 14b set; `testdata/degraded/*.jpg` + `testdata/degraded_images.json` — 2.6 degraded-image fixtures for FR-039; `testdata/synthetic/*.jpg` — synthetic statement-label fixture for FR-056) |
| Deployed application URL | ☐ Pending — WBS 18.0 |

---

## Next Session — WBS 7.0: Backend Stage 5 — Comparison Engine

> See [`_DevLog/Sessions.md`](_DevLog/Sessions.md) for the full session-by-session narrative (Sessions 1-14), including Sessions 10-14's completion of WBS 1.0, 11.0, 2.0, 3.0, 4.0, and 5.0.

**Session 15 completed WBS 12.0/13.0 Pass 1** (re-sequenced ahead of 6.0 per [`WBS.md` v2.1](_DevLog/WBS.md) §4 Note 7):

1. **Backend fix** (`app/routers/applications.py`): `_to_detail()` now queries persisted `FormParameter`/`LabelParameter`/`Determination` rows so `GET /applications/{id}` returns real `form_parameters`/`label_parameters`/`determination`.
2. **WBS 12.2** — Filter by applicant (`DashboardPage.tsx`)
3. **WBS 12.3** — Checkbox batch selection (`DashboardPage.tsx`)
4. **WBS 13.1/13.2** — Split-view layout + react-pdf form renderer in `ApplicationDetailPage.tsx`, backed by two new file-serving endpoints (`GET /applications/{id}/form`, `GET /applications/{id}/label-images/{image_id}`) needed because uploaded files were stored on disk but never exposed over HTTP
5. **WBS 13.3** — Multi-image tab selector with thumbnails (`LabelImagesPanel.tsx`)
6. **WBS 13.4** — SVG annotation overlay on the form panel, positioned via `form_parameters.bbox_json`
7. **WBS 12.8/13.12 (partial)** — Vitest configured in `web/`; unit tests covering 12.1–12.3/12.7 and 13.1–13.4 (6 tests, all passing)

**Manual verification:** open the "Test Upload" application from Session 13's WBS 4.0 manual test (1 PDF + 2 label images) at `/applications/{id}` — the form PDF and label images should render in a split view with tabs. The SVG overlay will show "no extracted fields yet" until Stage 3 extraction (wired up as part of 6.0+) populates `form_parameters` for an application.

**This session completed WBS 6.0 — Backend Stage 4: Label Assessment (TS-02)** (`app/services/label_extraction.py`, `app/tests/test_label_extraction.py`):

1. **6.1** — OpenCV preprocessing pipeline: `deskew()` (Otsu threshold + `minAreaRect` skew estimation/correction), `normalize_contrast()` (CLAHE on the LAB L-channel), `suppress_glare()` (highlight mask + `inpaint`), composed in `preprocess_image()`.
2. **6.2/6.3** — `STAGE4_SYSTEM_PROMPT` (cached) drives `extract_label_fields()`: the 8 mandatory + 5 secondary fields, `government_warning` (presence/header caps/bold + `text_exact_match` against the statutory 27 CFR § 16.21 text), and a generic `other_text` catch-all.
3. **6.4** — `run_ocr()` (pytesseract `image_to_data`); degrades gracefully to `[]` per §4 Note 7 contingency #1 (Tesseract binary not installed in this environment — covered by a dedicated test).
4. **6.5** — `fuzzy_match_bbox()` (difflib `SequenceMatcher` over OCR word windows) and `compute_header_height_ratio()` (FR-040 acceptance case validated at exactly 2.0).
5. **6.6** — `run_stage4_extraction()`: `asyncio.gather` across an application's label images, with Claude-vs-OCR concurrency within each image.
6. **6.7** — `persist_label_parameters()`: one `LabelParameter` row per `label_image_id` × field_name (incl. `bbox_json`/`header_height_ratio`), sets `application.status = "LABEL_ASSESSED"`.
7. **6.8** — 22 new tests (preprocessing against the WBS 2.6 degraded fixtures, extraction parsing incl. government warning, OCR fuzzy-match, orchestration, persistence) — **81/81 pytest passing** (was 59/59).

Proceed to **WBS 7.0 — Backend Stage 5: Comparison Engine** (`app/`, re-scoped for FR-066/FR-100–107): multi-image resolution helper — a form value is "on label" if found on *any* associated label image (7.1); Brand Name (7.2), Government Warning (7.3), and Type 14b "for sale in [STATE]" (7.4) comparisons; Section V Allowable-Revision classification mapping (7.5); Country of Origin (7.6), Fanciful Name (7.7), Product Type/Class-Type (7.8), Applicant Name (7.9), Applicant Address (7.10), Grape Varietals (7.11), Wine Appellation (7.12), ABV (7.13), and Net Contents (7.14) comparisons; persistence to `comparisons` (7.15); unit tests — one per rule covering MATCH/HARD_FAILURE/POSSIBLE_ALLOWABLE outcomes using 2.3/2.4/2.5/2.7 (7.16).

After WBS 7.0–10.0 land, return to **WBS 12.0/13.0 Pass 2** (12.4–12.6, 13.5–13.11, remaining 12.8/13.12 coverage) per [`WBS.md` v2.1](_DevLog/WBS.md) §4 Note 7, before proceeding to 14.0.

---

## Remaining Implementation Work (post-architecture-review)

> Sequencing, dependencies, and traceability for all items below are in [`WBS.md` v2.1 — Work Breakdown Structure](_DevLog/WBS.md) §2.
>
> **Execution order override (v2.1, 2026-06-11):** WBS 12.0/13.0 pulled forward — Pass 1 (12.1–12.3, 12.7, 13.1–13.4) ✅ complete (Session 15), ahead of 6.0; Pass 2 (12.4–12.6, 13.5–13.11) executes after 10.0, before 14.0. See [`WBS.md`](_DevLog/WBS.md) §4 Note 7.

- [x] WBS 1.0 — Backend scaffolding (`app/`): FastAPI structure, SQLAlchemy models for all 8 tables, env config, CORS, early Railway smoke-test deploy (Session 10)
- [x] WBS 2.0 — Synthetic test data (parallel w/ 1.0): sample F 5100.31 PDFs across all 3 TS-01 tiers + multi-image label sets (good / hard-failure / allowable / degraded / 14b) — **2.1–2.7 done, ALL COMPLETE** (`testdata/manifest.json`, Session 10; `testdata/forms/sample_creek_*.pdf`, Session 11; `testdata/forms/good_*.pdf` + `testdata/forms/hf_*.pdf` + `testdata/forms/ar_*.pdf` + `testdata/forms/type14b_*.pdf` + `testdata/test_sets.json`, Session 11; `testdata/degraded/*.jpg` + `testdata/degraded_images.json` + `testdata/synthetic/*.jpg`, Session 11)
- [x] WBS 3.0 — Auth: agent model + seed, JWT login, current-agent dependency, unit tests — **COMPLETE** (`app/services/auth_service.py`, `app/routers/auth.py`, `app/dependencies.py`, `app/seed.py`, `app/tests/test_auth.py`; 12/12 pytest passing, Session 12)
- [x] WBS 4.0 — Stage 1–2: ingestion endpoints, file validation, persistence, list/detail endpoints, unit tests — **COMPLETE** (`app/schemas/application.py`, `app/services/application_service.py`, `app/routers/applications.py`, `app/tests/test_applications.py`; 23/23 pytest passing, Session 13)
- [x] WBS 5.0 — Stage 3: form assessment (tiered TS-01 extraction, all 18 Part I fields, normalization, confidence scoring, unit tests) — **COMPLETE** (`app/services/form_extraction.py`, `app/tests/test_form_extraction.py`; 54/54 pytest passing, Session 14)
- [x] WBS 6.0 — Stage 4: label assessment (TS-02 — OpenCV + Claude Vision + Tesseract OCR, per-image concurrency, unit tests) — **COMPLETE** (`app/services/label_extraction.py`, `app/tests/test_label_extraction.py`; 81/81 pytest passing, Session 16)
- [ ] WBS 7.0 — Stage 5: comparison engine (multi-image resolution + 13 comparison rules incl. new FR-066/FR-100–107, unit tests)
- [ ] WBS 8.0 — Stage 6: determination logic + report schema, unit tests
- [ ] WBS 9.0 — Pipeline orchestration + Batch Orchestrator (bounded concurrency), unit/integration tests
- [ ] WBS 10.0 — Overrides, finalize, batch report endpoints, unit tests
- [x] WBS 11.0 — Frontend scaffolding (`web/`): Vite + React + TS + Tailwind + shadcn/ui + react-pdf + API client, plus new Settings/API-key UI (Session 10)
- [ ] WBS 12.0 — Agent Dashboard (list, filter, batch select, process, badges, upload modal, unit tests) — **Pass 1 (12.1-12.3, 12.7) ✅ complete**, incl. 12.8 partial (Vitest); Pass 2 (after 10.0): 12.4-12.6, remaining 12.8
- [ ] WBS 13.0 — Application Detail View (split view, multi-image tabs, annotation overlays, cross-highlight, overrides, finalize, unit tests) — **Pass 1 (13.1-13.4) ✅ complete**, incl. 13.12 partial (Vitest) — verified against the "Test Upload" application from Session 13's WBS 4.0 manual test (1 PDF + 2 label images); Pass 2 (after 10.0): 13.5-13.11, remaining 13.12
- [ ] WBS 14.0 — Batch Report view (counts, common failure type, CSV/PDF export, unit tests)
- [ ] WBS 15.0 — Integration: wire frontend to backend (Dashboard, Detail View, Batch Report, auth, error handling)
- [ ] WBS 16.0 — Integration testing against synthetic data (per-product-type pipeline, PR-001 timing, batch concurrency, multi-image resolution, override/finalize, annotation placement)
- [ ] WBS 17.0 — Localhost end-to-end manual testing (full user path, usability UR-001–006, browser compat, edge cases)
- [ ] WBS 18.0 — Setup & deployment: Railway (API + volume + Tesseract) + Netlify (web), CORS, README live URL
- [ ] WBS 19.0 — Post-deployment end-to-end testing (re-run user path, timing, cross-browser on deployed URL)
- [ ] WBS 20.0 — Submission material review & collation: README/DevLog/PRD/WBS consistency, export chat transcripts, repo cleanup, lint/format
- [ ] WBS 21.0 — Submission: verify form fields, submit, record confirmation in DevLog

---

**TTB Label Verification System**  
*Copyright (c) 2026 Matthew Gabriel Sizemore · Assessment submission: IT Specialist (AI) · 26-DO-12891471-DH*
