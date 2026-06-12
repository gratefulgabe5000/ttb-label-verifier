# TODO — TTB Label Verification System

**Assessment:** IT Specialist (AI) · 26-DO-12891471-DH
**Received:** June 9, 2026, 1458 hrs · **Deadline:** June 16, 2026, 1458 hrs
**Repo:** https://github.com/gratefulgabe5000/ttb-label-verifier
**Documentation Baseline:** v2.0 — README, PRD (v2.0), DevLog, WBS (v2.0), and TODO are mutually consistent as of Session 9 (2026-06-11)

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
| Backend (`app/`) | 🔶 Scaffolding + Auth + Ingestion + Form Assessment complete (WBS 1.0, 3.0, 4.0, 5.0; 54/54 pytest passing, Railway config) — WBS 6.0–10.0 remaining |
| Frontend (`web/`) | 🔶 Scaffolding complete (WBS 11.0 + Settings/API-key UI, build & lint passing); 12.7 Upload-new modal pulled forward & done — WBS 12.0 (remaining items)–14.0 remaining |
| Synthetic test data (sample forms + multi-image label sets) | ✅ 2.1–2.7 complete — ALL OF WBS 2.0 DONE (`testdata/manifest.json` — 45 products / 88 images; `testdata/forms/sample_creek_*.pdf` — TS-01 3-tier fixtures; `testdata/forms/good_*.pdf` + `testdata/forms/hf_*.pdf` + `testdata/forms/ar_*.pdf` + `testdata/forms/type14b_*.pdf` + `testdata/test_sets.json` — 2.3 "good" sets + 2.4 "hard failure" sets + 2.5 "possible allowable revision" sets + 2.7 Type 14b set; `testdata/degraded/*.jpg` + `testdata/degraded_images.json` — 2.6 degraded-image fixtures for FR-039; `testdata/synthetic/*.jpg` — synthetic statement-label fixture for FR-056) |
| Deployed application URL | ☐ Pending — WBS 18.0 |

---

## Next Session — Label Assessment Backend (6.0)

> See [`_DevLog/Sessions.md`](_DevLog/Sessions.md) for the full session-by-session narrative (Sessions 1-14), including Sessions 10-14's completion of WBS 1.0, 11.0, 2.0, 3.0, 4.0, and 5.0.

1. **WBS 6.0 — Backend Stage 4: Label Assessment (TS-02)** (`app/`): OpenCV preprocessing pipeline — deskew, contrast/CLAHE, glare suppression (6.1), Claude Vision label-extraction prompt covering mandatory + secondary elements plus a generic `other_text` catch-all (6.2), Government Warning detection via exact-text + bold/caps check (6.3), Tesseract OCR pass for text + bbox detection (6.4), fuzzy-match Claude-extracted values to OCR bboxes and compute `header_height_ratio` (6.5), per-image concurrent execution via `asyncio.gather` across an application's label images with Claude-vs-OCR concurrency within each image (6.6), persist to `label_parameters` — one row per `label_image_id` × field_name including `bbox_json`/`header_height_ratio` (6.7), unit tests for Stage 4 preprocessing on the 2.6 degraded images, extraction parsing, OCR fuzzy-match, and government warning detection using 2.1/2.4 (6.8).

---

## Remaining Implementation Work (post-architecture-review)

> Sequencing, dependencies, and traceability for all items below are in [`WBS.md` v2.0 — Work Breakdown Structure](_DevLog/WBS.md) §2.

- [x] WBS 1.0 — Backend scaffolding (`app/`): FastAPI structure, SQLAlchemy models for all 8 tables, env config, CORS, early Railway smoke-test deploy (Session 10)
- [x] WBS 2.0 — Synthetic test data (parallel w/ 1.0): sample F 5100.31 PDFs across all 3 TS-01 tiers + multi-image label sets (good / hard-failure / allowable / degraded / 14b) — **2.1–2.7 done, ALL COMPLETE** (`testdata/manifest.json`, Session 10; `testdata/forms/sample_creek_*.pdf`, Session 11; `testdata/forms/good_*.pdf` + `testdata/forms/hf_*.pdf` + `testdata/forms/ar_*.pdf` + `testdata/forms/type14b_*.pdf` + `testdata/test_sets.json`, Session 11; `testdata/degraded/*.jpg` + `testdata/degraded_images.json` + `testdata/synthetic/*.jpg`, Session 11)
- [x] WBS 3.0 — Auth: agent model + seed, JWT login, current-agent dependency, unit tests — **COMPLETE** (`app/services/auth_service.py`, `app/routers/auth.py`, `app/dependencies.py`, `app/seed.py`, `app/tests/test_auth.py`; 12/12 pytest passing, Session 12)
- [x] WBS 4.0 — Stage 1–2: ingestion endpoints, file validation, persistence, list/detail endpoints, unit tests — **COMPLETE** (`app/schemas/application.py`, `app/services/application_service.py`, `app/routers/applications.py`, `app/tests/test_applications.py`; 23/23 pytest passing, Session 13)
- [x] WBS 5.0 — Stage 3: form assessment (tiered TS-01 extraction, all 18 Part I fields, normalization, confidence scoring, unit tests) — **COMPLETE** (`app/services/form_extraction.py`, `app/tests/test_form_extraction.py`; 54/54 pytest passing, Session 14)
- [ ] WBS 6.0 — Stage 4: label assessment (TS-02 — OpenCV + Claude Vision + Tesseract OCR, per-image concurrency, unit tests)
- [ ] WBS 7.0 — Stage 5: comparison engine (multi-image resolution + 13 comparison rules incl. new FR-066/FR-100–107, unit tests)
- [ ] WBS 8.0 — Stage 6: determination logic + report schema, unit tests
- [ ] WBS 9.0 — Pipeline orchestration + Batch Orchestrator (bounded concurrency), unit/integration tests
- [ ] WBS 10.0 — Overrides, finalize, batch report endpoints, unit tests
- [x] WBS 11.0 — Frontend scaffolding (`web/`): Vite + React + TS + Tailwind + shadcn/ui + react-pdf + API client, plus new Settings/API-key UI (Session 10)
- [ ] WBS 12.0 — Agent Dashboard (list, filter, batch select, process, badges, upload modal, unit tests) — **12.7 (upload modal) pulled forward & complete (Session 13)**; 12.1-12.6, 12.8 remaining
- [ ] WBS 13.0 — Application Detail View (split view, multi-image tabs, annotation overlays, cross-highlight, overrides, finalize, unit tests) — **13.1 (split-view form/label rendering, FR-080/081) is the planned UI for viewing an application's uploaded files; once built, use it to verify the "Test Upload" application (created during Session 13's WBS 4.0 manual test, 1 PDF + 2 label images) renders correctly**
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
