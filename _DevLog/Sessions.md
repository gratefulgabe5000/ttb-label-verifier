# Sessions — TTB Label Verification System

**Document ID:** TTB-LVS-SESSIONS-001
**Purpose:** Consolidated, chronological session-by-session engineering/narrative log for the TTB Label Verification System assessment. This is the single canonical "historian" record — superseding the per-session entries formerly duplicated across `_DevLog/DevLog.md` §7 (Engineering Log) and the root `TODO.md` ("Daily Chat Summary" and "Next Session" update bullets).

**Related Documents:** [DevLog.md](DevLog.md) (design/requirements/trade-study reference, §1-6) · [PRD.md](PRD.md) (Product Requirements Document, INCOSE-style) · [WBS.md](WBS.md) (Work Breakdown Structure) · [../TODO.md](../TODO.md) (current status & forward plan)

---

## 2026-06-09

### Session 1: Assessment Intake & Initial Setup

**Context:** First session of the assessment. Goal was to understand the take-home assignment materials and stand up the project skeleton.

**Completed:**
- Reviewed and analyzed the Treasury take-home assessment source documents (the assignment prompt, the TTB COLA application form, and supporting reference materials provided with IT Specialist (AI) · 26-DO-12891471-DH).
- Extracted the core requirements from the source documents into a working understanding of the problem: automated verification of TTB Certificate of Label Approval (COLA) applications against submitted label images.
- Made an initial technology-stack decision: Python + Streamlit (frontend/UI) + Claude Vision (label image analysis). This stack was later substantially revised in Session 2 once the full scope (multi-page React frontend, FastAPI backend, persistent database) became clear.
- Initialized the project's git repository.
- Created the GitHub repository `gratefulgabe5000/ttb-label-verifier`.
- Authored the initial `README.md` and `_DevLog/DevLog.md`, establishing the documentation structure that would be built on in later sessions.
- Created the root-level `TODO.md` task-tracking document.

**Outcome:** Project skeleton established (git repo, GitHub remote, initial README/DevLog/TODO). Initial stack choice (Streamlit) flagged for re-evaluation as scope became clearer — addressed in Session 2.

---

### Session 2: Form Analysis & Full Architecture Design

**Context:** Deeper analysis of the COLA form and assessment requirements revealed the system needed to be substantially more capable than a Streamlit script — a full web application with persistent storage, multi-image handling, and a structured comparison workflow.

**Completed:**
- Performed a detailed analysis of the TTB COLA application form structure (Part I fields, Section V revision categories, label image requirements).
- Redesigned the technology stack: pivoted from Python+Streamlit to **React + Vite (frontend) + FastAPI (backend) + SQLite (database)**.
- Designed the 6-stage processing pipeline (ingestion → form extraction → label extraction → comparison → determination → review), which became the backbone of all later architecture documents.
- Defined the 3-outcome determination model: APPROVABLE / POSSIBLE_ALLOWABLE_REVISION / NOT_APPROVABLE.
- Drafted the comparison matrix mapping form fields to label fields and to the relevant TTB regulatory citations.
- Mapped TTB application Section V revision categories to the POSSIBLE_ALLOWABLE_REVISION determination outcome.
- Designed an 8-table database schema (applications, label images, form parameters, label parameters, determinations, comparison results, settings/API keys, and supporting lookup tables).
- Designed an 11-endpoint REST API covering authentication, application upload/listing/detail, settings, and the assessment pipeline stages.
- Designed the 3 primary UI views: a dashboard/list view, a detailed split-view application review screen, and a settings view.
- Elaborated the split-view review UI concept: side-by-side form and label image panels, **red-ellipse annotations** highlighting the specific regions being compared, **cross-highlighting** between corresponding form fields and label regions, and **right-click override** functionality allowing a reviewer to manually adjust a determination.
- Identified open design items to carry into Session 3 (formal requirements documentation, multi-image handling specifics, extraction-tier strategy).

**Outcome:** Full architecture established — pipeline, data model, API surface, and UI concept all defined. Open items (formal PRD authorship, multi-image handling) carried to Session 3.

---

### Session 3: INCOSE PRD & Comprehensive Extraction Revision

**Context:** With the architecture defined, the next step was to formalize requirements in an INCOSE-style Product Requirements Document and resolve open design questions around multi-image label handling.

**Completed:**
- Authored the INCOSE-style Product Requirements Document, `_DevLog/PRD.md` (document ID **TTB-LVS-PRD-001**), establishing the formal requirements baseline (functional requirements, interface requirements, assumptions) referenced by all later sessions.
- **Design correction (extraction scope):** revised the form/label extraction requirements, adding **FR-010 through FR-016** (form-side extraction requirements) and **FR-030 through FR-036** (label-side extraction requirements), replacing an earlier, less granular extraction requirement set.
- **Design correction (multi-image label processing):** extended the requirements to properly handle applications with multiple label images (front/back/neck labels, multiple bottle sizes, etc.), adding **FR-030 through FR-038** and interface assumptions **IA-18** and **IA-19** covering multi-image upload, storage, and per-image processing.
- Updated `README.md` to reflect the PRD's existence and the revised extraction scope.
- Identified an open design question — how the UI should let a reviewer select among multiple label images for a single application (tabs vs. thumbnails vs. another pattern) — carried forward to Session 4 (ultimately resolved in Session 5 as a tabs+thumbnails design, FR-091).

**Outcome:** Formal requirements baseline established (PRD v1.0, TTB-LVS-PRD-001). Multi-image label handling formalized (FR-030-038, IA-18/IA-19). Open item: multi-image selector UI pattern, carried to Session 4/5.

---

## 2026-06-10

### Session 4: Trade Studies & COLA Registry Reference

**Context:** Two open technical questions from the PRD needed formal trade studies: how to extract data from the various tiers of COLA application PDF (fillable AcroForm vs. flattened vs. scanned), and how to improve OCR accuracy on label images.

**Completed:**
- Authored **Trade Study TS-01** (tiered form extraction strategy, supporting **FR-017**): evaluated approaches for extracting Part I data from PDF applications across three tiers — fillable AcroForm fields, flattened PDF text layers, and fully scanned/image-only PDFs — establishing the Tier 1/Tier 2/Tier 3 extraction cascade later implemented in WBS 5.0.
- Authored **Trade Study TS-02** (OpenCV + OCR label image augmentation, supporting **FR-040**): evaluated image pre-processing techniques (deskew, contrast enhancement, glare removal) to improve OCR accuracy on physical label photographs.
- Restructured `_DevLog/DevLog.md` to add a new **§3.1 Trade Studies** section, housing TS-01 and TS-02 and establishing the pattern for future trade studies (TS-03+ added in later sessions).
- Resolved **IA-07** and **IA-13** (initial assumptions regarding form format handling and label image quality), and added new initial assumptions **IA-20 through IA-22** covering the trade-study conclusions.
- Conducted research into the public **TTB COLA Registry**, using a real-world example (TTB ID **25211001000227**) as a reference. This research produced reference notes **REF-07 through REF-09** and identified **8 new `applications` table columns** needed to capture COLA-registry-equivalent metadata (added to the data model).
- Added a new **§6 COLA Registry research** section to DevLog documenting these findings.
- Identified open items for Session 5: resolve the multi-image selector UI pattern (carried from Session 3), and continue refining the architecture based on the trade-study conclusions.

**Outcome:** TS-01 and TS-02 trade studies complete, DevLog restructured with §3.1 Trade Studies and §6 COLA Registry research. Data model expanded with 8 COLA-registry-aligned columns. Open items carried to Session 5.

---

### Session 5: Architecture Evaluation

**Context:** With trade studies and registry research complete, this session consolidated everything into a formal architecture evaluation and resolved the remaining open design questions.

**Completed:**
- Authored new **§3.6 Architecture Evaluation** in DevLog: a 15-row evaluation table comparing architectural options against requirements, identifying an "ideal scenario" implementation path, and formally resolving several previously-open items.
- Resolved the multi-image selector UI question (open since Session 3): adopted **FR-091** — a **tabs + thumbnails** pattern for selecting among multiple label images within an application's review screen.
- Added new form-panel data model fields **`bbox_json`** and **`location_hint`** (supporting **FR-019** / **IA-23**), enabling the UI to draw bounding boxes / location hints over form fields even when exact coordinates aren't available (e.g., for AI-vision-extracted fields).
- Evaluated and **rejected** a "combined multi-image prompt" approach (sending all label images to Claude in a single prompt) in favor of per-image prompts.
- Added **IA-25** (prompt caching): Claude API calls use `cache_control: ephemeral` to cache the (large, static) system prompt across repeated per-image/per-field calls, reducing cost and latency. This assumption was later implemented directly in Session 14's Tier 3 extraction code.
- Recorded **Decision 8**, comprising 5 architectural refinements consolidating the session's resolutions.
- Added **shadcn/ui** as the frontend component library decision (later scaffolded in Session 10's WBS 11.0).
- Revised **IA-17** and added **IA-23 through IA-26**, capturing the session's new assumptions.
- Bumped the PRD to **v1.2** to reflect FR-091, IA-23-26, and the architecture evaluation outcomes.
- Identified open items for Session 6: produce formal system diagrams and a Work Breakdown Structure.

**Outcome:** Architecture evaluation complete (§3.6, 15-row table). Multi-image selector resolved (FR-091). PRD → v1.2. Open items (diagrams, WBS) carried to Session 6.

---

### Session 6: Diagrams & Work Breakdown Structure

**Context:** The architecture was now stable enough to produce formal systems-engineering diagrams and an initial project plan/WBS — completing the Systems Engineering Pass requested for this assessment.

**Completed:**
- Authored new **§3.7 System Diagrams** in DevLog, containing **3 Mermaid diagrams**: a context diagram (system boundary and external actors), a block diagram (major components and data stores), and a sequence diagram (end-to-end pipeline flow for a single application).
- Authored the initial standalone **`_DevLog/WBS.md`** (Work Breakdown Structure, **v1.0**): 13 top-level work items, an estimated **~75 hours / 6-day** schedule, a critical-path analysis, and risk notes. (This was originally drafted as a DevLog §9 section before being split out into its own document.)
- Added a **"Related Documents"** line to the DevLog header, linking to the new standalone `WBS.md` (and, from Session 3 onward, `PRD.md`).
- Completed the **Systems Engineering Pass** for the assessment — architecture, requirements, diagrams, and an initial project plan were all now in place.

**Outcome:** Systems Engineering Pass complete. New artifacts: DevLog §3.7 (3 Mermaid diagrams), standalone `WBS.md` v1.0 (13 items, ~75hr/6-day estimate). DevLog header now links to WBS.md.

---

### Session 7: Documentation Consistency & Requirements Completeness Pass

**Context:** With the core systems-engineering artifacts in place, this session focused on tightening internal consistency across the documentation suite and closing requirements-completeness gaps identified during review.

**Completed:**
- Renamed DevLog **§5 "Assumptions"** to **"Initial Assumptions"**, distinguishing DevLog's working assumptions (**IA-01 through IA-26**) from the PRD's formal assumptions (**A-01 through A-14**) — these are two related but distinct numbering series.
- Re-audited and re-pointed all `A-\d+` cross-references across all 4 documentation files (README, DevLog, PRD, WBS) to ensure each reference correctly targeted either an `IA-*` (DevLog) or `A-*` (PRD) assumption as appropriate.
- Fixed **3 broken PRD self-references** discovered during the audit.
- Bumped PRD to **v1.3**: added new formal assumptions **A-15**, **A-16**, **A-17**, and new functional requirement **FR-066**.
- Bumped PRD to **v1.4**: added **FR-100 through FR-107**, formalizing **8 previously-unformalized comparison-matrix rows** (rows in the form/label comparison matrix from Session 2 that described comparison logic but had no corresponding numbered functional requirement).
- Identified an open item: the WBS's item **6.0 / 6.1** estimates needed to be re-evaluated in light of the requirements growth (FR-066, FR-100-107) before implementation could begin — resolved in Session 8 via the full WBS re-baseline.

**Outcome:** Documentation suite internally consistent — IA-* vs A-* numbering clarified, all cross-references repointed, 3 broken self-references fixed. PRD → v1.4 (FR-066, FR-100-107 added). Open item (WBS re-estimate) carried to Session 8.

---

## 2026-06-11

### Session 8: WBS Re-Baseline (v2.0)

**Context:** Requirements growth across Sessions 5-7 (FR-091, FR-100-107, multi-image handling, architecture evaluation) had outpaced the original 13-item WBS v1.0. This session produced a full re-baseline.

**Completed:**
- Rewrote `_DevLog/WBS.md` as **v2.0**:
  - New **Phase 0** (items **0.1-0.12**), retroactively mapping all prior systems-engineering work (Sessions 1-7) onto explicit WBS items — giving the WBS a complete record of work already done, not just work remaining.
  - Rewrote **Phase 1** as a dependency-ordered sequence of **21 top-level items (1.0-21.0)**, comprising roughly **140 sub-items** total.
  - Re-scoped the **Comparison Engine** to **WBS 7.0** with **16 sub-items**, resolving the open item from Session 7 (the FR-100-107 comparison-matrix rows are now each traceable to a specific WBS 7.0 sub-item).
  - Re-sequenced **synthetic test-data generation** to **WBS 2.0** (previously scattered across other items), consolidating all test-fixture work into one phase.
  - Added new explicit phases: **3.0** (auth), **9.0**, **10.0**, **15.0**, **17.0**, **19.0**, **20.0**, and **21.0**.
  - Per Gabe's direction, **removed all hour estimates and target dates** from the WBS — the document now tracks dependency order and completion status only, not a schedule.
- Updated `TODO.md`: refreshed the "Status at a Glance" table, rewrote the "Next Session" plan section, and replaced the old WBS-derived checklist with a new **21-item checklist** matching WBS v2.0's top-level items.

**Outcome:** WBS re-baselined to v2.0 — 0.1-0.12 (retrospective Phase 0) + 1.0-21.0 (~140 sub-items, dependency-ordered, no dates/estimates). TODO.md status table and checklist updated to match. This is the WBS version all subsequent implementation sessions (10-14+) are tracked against.

---

### Session 9: Documentation Consistency Pass (v2.0 Baseline)

**Context:** The WBS re-baseline (Session 8) and the accumulated changes from Sessions 1-8 needed a final consistency sweep before implementation could begin, to ensure the documentation suite was internally coherent at a single version baseline.

**Completed:**
- Fixed the PRD footer version marker (was showing **v1.2**, corrected to **v1.4** to match the actual current content established across Sessions 5-7).
- Fixed a stale DevLog **§5 TOC anchor** (left over from the Session 7 "Assumptions" → "Initial Assumptions" rename).
- Fixed `TODO.md`'s WBS section cross-references, which pointed to **§3/§4** of WBS.md — corrected to **§2/§3** to match the actual WBS v2.0 structure.
- Added **Sessions 7 and 8** to the DevLog **§7 Engineering Log** (these had been completed but not yet logged).
- Fixed the **README.md "Project Structure"** tree, which had drifted from the actual repository layout.
- Fixed **WBS.md item 0.13** (incorrect description) and added a new **item 0.14**, completing the Phase 0 retrospective mapping.
- Bumped the **PRD to v2.0**.
- Added a **"Documentation Suite Version: 2.0"** marker to DevLog, README, and TODO — establishing a single shared version baseline across the entire documentation suite.

**Outcome:** Documentation suite fully consistent at v2.0 (PRD v2.0, "Documentation Suite Version: 2.0" marker in DevLog/README/TODO, all cross-references and TOC anchors verified). **Implementation work (WBS 1.0+) could now begin** — Session 10 was the first implementation session.

---

### Session 10: Implementation Start — Backend Scaffolding (1.0), Frontend Scaffolding (11.0), Test-Data Inventory (2.1)

**Context:** First implementation session. Three parallel scaffolding efforts: backend API skeleton, frontend app skeleton, and an inventory of the available test-data images to plan synthetic test-fixture generation (WBS 2.0).

**Completed — WBS 1.0 (Backend scaffolding):**
- Created the FastAPI project structure under `app/`.
- Set up **SQLAlchemy + SQLite** as the database layer.
- Implemented **8 ORM models**, including the COLA-registry forward-compatibility columns identified in Session 4, plus a new **Settings/API-key model (item 1.4)**.
- Item 1.4 (Settings/API-key): implemented `GET`/`PUT`/`DELETE /settings/api-key` endpoints that read/write **`os.environ["ANTHROPIC_API_KEY"]`** only (not persisted to the database) — responses return a **masked key** plus a **connection-test result**.
- Configured **CORS** for the FastAPI app.
- Wrote **4/4 passing pytest** tests for the scaffolding.
- Added **Railway deployment config (item 1.6)**: `nixpacks.toml` and `railway.json`.
- Updated `.gitignore` and `README.md` to reflect the new backend structure.

**Completed — WBS 11.0 (Frontend scaffolding):**
- Created the **Vite + React 19 + TypeScript + Tailwind CSS 4** project.
- Installed **shadcn/ui** using the **"base-nova"** style/theme.
- Installed `react-pdf`, `@tanstack/react-query` (v5), and `react-router` (v7).
- Established the project structure with a **`@/*`** path alias.
- Scaffolded **JWT-based authentication** (context/provider, token storage).
- Built a **typed API client** with a clear split between **implemented** endpoints and **forward-declared** (not-yet-built) endpoints, so the frontend type system stays accurate as the backend grows.
- Added a **Settings gear icon → `SettingsDialog`** component (wired to the WBS 1.0 API-key endpoints).
- Fixed several specific build/lint issues:
  - Removed the deprecated `baseUrl` TS config option (was causing **TS5101**).
  - Fixed a `toQueryString` parameter type mismatch (**TS2345**).
  - Resolved a `react-refresh/only-export-components` lint violation by splitting `AuthContext.tsx` into `contexts/auth-context.ts` (context/types/hooks) and `AuthContext.tsx` (the provider component).
- Confirmed lint and build both pass.
- Ran an **end-to-end smoke test** against the live (locally running) backend, confirming frontend ↔ backend connectivity.

**Completed — WBS 2.1 (Test-data inventory):**
- Per Gabe's mid-session redirection, **flattened** the test-data source images into an **88-image, 6-subfolder structure**.
- Wrote `testdata/build_manifest.py`, which generates `testdata/manifest.json`.
- The manifest catalogs **45 product-level label sets**: **39 distilled-spirits sets (78 images)**, **4 wine sets (7 images)**, and **2 malt-beverage sets (3 images)**.
- Flagged a **"Forte Masso" anomaly** in the source data for follow-up in WBS 2.4.
- Identified an open item: reconcile the wording of **WBS.md item 2.1** with the actual flattened-structure approach taken — to be addressed in a later pass.

**Outcome:** WBS 1.0 (backend scaffold, 4/4 tests passing, Railway config) and WBS 11.0 (frontend scaffold, lint/build passing, e2e smoke test passing) both complete. WBS 2.1 (test-data inventory) complete — 45 product-level sets cataloged in `testdata/manifest.json`. Open items: WBS 2.1 wording reconciliation (minor), Forte Masso anomaly (for WBS 2.4).

---

### Session 11: Synthetic Test Data — Sample Forms (2.2), Good Sets (2.3), Hard Failure Sets (2.4), Allowable Revision Sets (2.5), Degraded Images (2.6) & Type 14b Set (2.7) — completes WBS 2.0

**Context:** With the test-data inventory complete (Session 10, WBS 2.1), this session built out the full suite of synthetic test fixtures needed to exercise every extraction tier and comparison-outcome path — completing WBS 2.0 in its entirety.

**Completed — 2.2 (TS-01 tier sample forms):**
- Wrote `testdata/build_sample_forms.py`, generating a **"Sample Creek Distillery"** fixture as three PDFs representing the three TS-01 extraction tiers:
  - `sample_creek_acroform.pdf` (fillable AcroForm — Tier 1)
  - `sample_creek_flattened.pdf` (flattened text layer — Tier 2)
  - `sample_creek_scanned.pdf` (scanned/image-only — Tier 3)
- **Debugging note:** an initial hand-rolled PDF-flattening approach was broken; replaced with **PyMuPDF's `Document.bake()`** method, which correctly bakes form field values into the page content while preserving the visual layout.

**Completed — 2.3 ("Good" comparison sets):**
- Wrote `testdata/build_good_sets.py` and a new shared helper module `testdata/formlib.py`.
- Generated **3 "good" sets** (form + label data that should compare cleanly, producing an APPROVABLE outcome): `good_spirits_woodford.pdf`, `good_wine_lenzmoser.pdf`, `good_malt_barrilito.pdf`.
- Created `testdata/test_sets.json` to catalog all synthetic test sets with metadata (set name, files, expected outcome, WBS reference).

**Completed — 2.4 ("Hard failure" sets):**
- Wrote `testdata/build_hard_failure_sets.py`, generating **12 `hf_*.pdf` sets** designed to produce a **NOT_APPROVABLE** determination:
  - **8 Woodford Reserve variants** (each introducing a different hard-failure mismatch between form and label).
  - **2 Rosso Veneto / "Duo" wine variants**.
  - **1 Forte Masso variant** (resolving the anomaly flagged in Session 10).
  - **1 Twelv3 liqueur variant**, which includes a **documented secondary co-failure** (two independent mismatches in the same set, intentionally, to test multi-failure handling).
- Updated `test_sets.json` — `wbs_ref` for these entries set to **"2.3-2.4"**.

**Completed — 2.5 ("Possible allowable revision" sets):**
- Wrote `testdata/build_allowable_revision_sets.py`, generating **2 `ar_*.pdf` sets** designed to produce a **POSSIBLE_ALLOWABLE_REVISION** determination:
  - `ar_brandname_fortemasso.pdf` — exercises **Section V item 3b** (brand name revision).
  - `ar_address_barrilito.pdf` — exercises **Section V item 19** (address revision).
- A third candidate example ("color/font differences") was **deliberately scoped out** — it isn't expressible within the current comparison schema (which compares discrete field values, not visual/typographic properties).
- Updated `test_sets.json` — `wbs_ref` for the 2.3-2.5 entries set to **"2.3-2.5"**.

**Completed — 2.6 (Degraded images):**
- Wrote `testdata/build_degraded_images.py`, generating **4 degraded variants** of `woodford_front.jpg` (e.g., blur, rotation/skew, low contrast, glare) into `testdata/degraded/`.
- **Tuning note:** the glare-overlay effect's opacity was tuned from an initial **255/255 (fully opaque)** down to **175/255**, since full opacity made the underlying label completely illegible (defeating the purpose of a "degraded but still partially readable" test case).
- Created `testdata/degraded_images.json` cataloging the 4 degraded variants.

**Completed — 2.7 (Type 14b matching set):**
- Wrote `testdata/build_type14b_sets.py`, generating `type14b_match_stollwolfe.pdf` plus a synthetic label image `testdata/synthetic/stollwolfe_for_sale_pa.jpg`.
- **Fix:** the synthetic label image's canvas size was corrected from **600×180** to **700×180** (the original size clipped part of the generated label text).
- Updated `test_sets.json` — `wbs_ref` for the full 2.2-2.7 family of entries set to **"2.3-2.5, 2.7"**.
- `test_sets.json` now catalogs **18 total synthetic test sets**.

**Open item flagged for Gabe (not yet addressed):** Several already-approved WBS 2.4 `comparison_expectations` notes cite **FR-051-055** as the relevant requirements, but the correct references should be **FR-100-104 / FR-066 / FR-053-056** (per the PRD v1.4 renumbering from Session 7). This is a **documentation-accuracy issue only** — the test fixtures themselves are correct — flagged for a possible future cleanup pass.

**Outcome:** WBS 2.0 **complete in full** — 18 total synthetic test sets across `testdata/`, covering all 3 TS-01 extraction tiers, good/hard-failure/allowable-revision comparison outcomes, degraded image quality, and the Type 14b matching scenario. **Approved by Gabe.**

---

### Session 12: Backend Auth — Agent Model & Seed (3.1), JWT Login (3.2), Current-Agent Dependency (3.3), Unit Tests (3.4) — completes WBS 3.0

**Context:** With test data complete, implementation moved to the backend authentication layer — required by SR-002 (per-agent application scoping) before the ingestion endpoints (WBS 4.0) could be built.

**Completed — 3.1 (Agent model, password hashing, JWT, seed data):**
- Created `app/services/auth_service.py`: password hashing via **passlib/bcrypt**, JWT issuance/verification via **python-jose**. JWT payload carries `sub`, `agent_id`, `display_name`, and `exp` claims.
- **Dependency fix:** pinned **`bcrypt==4.0.1`** in `requirements.txt`. Without the pin, **passlib 1.7.4** is incompatible with **bcrypt 5.0.0**, causing an `__about__` `AttributeError` and a 72-byte password `ValueError`.
- Created `app/seed.py`, seeding two test agents: **`agent1`** and **`agent2`**, both with password **`password123`**. Documented these seed credentials in `.env.example` and `README.md`.

**Completed — 3.2 (Login endpoint):**
- Created `app/schemas/auth.py` and `app/routers/auth.py`, implementing **`POST /auth/login`**.
- The endpoint returns a **generic 401** for both an unknown username and a correct-username-but-wrong-password case, to avoid leaking which usernames exist (enumeration protection).

**Completed — 3.3 (Current-agent dependency):**
- Created `app/dependencies.py` with **`get_current_agent`**, implemented via `HTTPBearer(auto_error=False)` (so a missing/invalid token can be handled with a custom error rather than FastAPI's default).
- Applied this dependency at the **router level** to `app/routers/settings.py`, protecting the WBS 1.0 settings/API-key endpoints behind authentication.

**Completed — 3.4 (Unit tests):**
- Created `app/tests/test_auth.py` with **8 tests**, plus `conftest.py` fixtures `test_agent` and `auth_headers` (reusable across future test modules).
- Updated `app/tests/test_settings.py` to use the new `auth_headers` fixture (since settings endpoints are now protected).
- **`StaticPool` fix** in `app/db.py`: the in-memory SQLite database (`:memory:`) was being recreated per-connection, causing cross-thread `TestClient` failures — fixed by using SQLAlchemy's `StaticPool` so all connections in a test share the same in-memory database.
- Added `Base.metadata.drop_all()` teardown to ensure test isolation between test runs.
- **12/12 tests pass.**

**Outcome:** WBS 3.0 **complete** — agent model, seeded credentials, JWT login (enumeration-safe), `get_current_agent` dependency applied to settings router, 12/12 tests passing. **Approved by Gabe** after an end-to-end login test.

---

### Session 13: Backend — Stage 1-2 Ingestion (4.1-4.6, completes WBS 4.0) + Frontend WBS 12.7 Pulled Forward (Upload-New Modal)

**Context:** With auth in place, this session built the application-ingestion endpoints (upload, list, detail) required for SR-002-scoped access, and — at Gabe's request — pulled forward the frontend upload-modal work (originally WBS 12.7) so the new endpoints could be exercised end-to-end immediately.

**Completed — 4.1-4.3 (Schemas & ingestion service):**
- Created `app/schemas/application.py`: `ApplicationOut`, `LabelImageOut`, `ApplicationDetailOut`, plus placeholder schemas `FormParameterOut`, `LabelParameterOut`, and `DeterminationOut` (for fields populated by later WBS items 5.0+).
- Created `app/services/application_service.py`:
  - **Magic-byte file validation** (verifies uploaded files are genuinely PDF/JPEG/PNG regardless of claimed content-type), raising a custom `FileValidationError` on mismatch.
  - `create_application()`: persists the uploaded application PDF and label images to `data/uploads/{id}/` and creates the corresponding database records.

**Completed — 4.4-4.5 (Endpoints):**
- Created `app/routers/applications.py`:
  - **`POST /applications/upload`** — accepts the application PDF plus one or more label images, validates them, and creates the application record.
  - **`GET /applications`** — returns the list of applications, **scoped per SR-002** (an agent only sees their own applications), with an optional `applicant_name` **ILIKE** filter.
  - **`GET /applications/{id}`** — returns full application detail via a `_to_detail()` helper. Returns **404 (not 403)** when an agent requests an application belonging to a different agent, avoiding leaking the existence of other agents' records.

**Completed — 4.6 (Unit tests & verification):**
- Created `app/tests/test_applications.py` with **11 tests**, plus new `second_agent` / `second_auth_headers` fixtures (for testing cross-agent isolation).
- **23/23 tests passing** (total across all test modules).
- **Verification:** killed an orphaned uvicorn worker process, ran an end-to-end smoke test against the live backend, and cleaned up the test rows created during the smoke test.

**Known discrepancy (non-blocking):** the frontend's `applicationsApi.list()` is currently typed as returning `ApplicationDetail[]`, but the actual `GET /applications` endpoint returns the lighter `ApplicationOut[]`. Flagged for correction during **WBS 12.0** (frontend application list/detail wiring) — no frontend changes were made for this in Session 13.

**Completed — WBS 12.7 pulled forward (Upload-new modal):**
- Created `web/src/components/applications/UploadApplicationDialog.tsx`: a shadcn `Dialog` containing applicant-name and serial-number text fields, a PDF file input for the application form, and **repeatable label-image inputs**, each paired with a `LabelType` `<select>` (per **FR-004**).
- The dialog submits via `applicationsApi.upload(formData)` using a React Query `useMutation`, which **invalidates the `["applications"]`** query on success, and shows **`sonner`** toast notifications for success/failure.
- Wired the dialog into `DashboardPage.tsx` as a **"New Upload"** button in the page header.
- Replaced the previous **"not available yet (WBS 4.0+)"** placeholder error message (now obsolete since uploads work) with the new dialog, and added an **empty-state message** for when an agent has no applications yet.
- Verified `npx tsc -b` and `npx eslint` both pass, and manually verified the upload flow on the dev server.

**Outcome:** WBS 4.0 **complete** — upload/list/detail endpoints, magic-byte validation, SR-002 scoping, 404-not-403 cross-agent behavior, 23/23 tests passing. WBS 12.7 (Upload-new modal) also complete and wired into the dashboard, ahead of the rest of WBS 12.0. Pending approval. Known discrepancy (`applicationsApi.list()` typing) flagged for WBS 12.0.

---

### Session 14: Backend — Stage 3 Form Assessment — Tier 1 AcroForm (5.1), Tier 2 pdfplumber (5.2), Tier 3 Claude Vision (5.3), Normalization (5.4), Orchestration & Persistence (5.5-5.6), Unit Tests (5.7) — completes WBS 5.0

**Context:** With ingestion complete, this session implemented Stage 3 of the pipeline — extracting Part I form-field data from the uploaded application PDF using the tiered TS-01 strategy designed back in Session 4, and persisting the results.

**Completed — 5.1 (Tier 1: pypdf AcroForm extraction):**
- Created `app/services/form_extraction.py`.
- Defined **`PART_I_FIELDS`** — the 21 Part I fields to extract.
- Defined `FIELD_NAME_MAP` (maps PDF AcroForm field names to `PART_I_FIELDS` names), `FIELD_RECTS` (known bounding-box rectangles per field), and `_rect_to_bbox()` (converts a PDF rect to the `{page, x, y, w, h}` bbox format used by the frontend).
- Implemented `extract_tier1()` using **`pypdf.get_fields()`**, with **4 special-case handlers**, including `_split_name_address()` (splits a combined "name\naddress" AcroForm field into separate `applicant_name` and `applicant_address` values).

**Completed — 5.2 (Tier 2: pdfplumber text-layer extraction):**
- Implemented `extract_tier2()` using **pdfplumber**, for PDFs with a flattened text layer but no AcroForm fields.
- `_filter_value_chars()`: filters extracted characters by font size to distinguish field **values** from field **labels** (labels and values often share the same text block but differ in font size).
- `_is_label_text()`: uses Python's `difflib` to detect when extracted text is actually a field's printed label (not its value) by fuzzy-matching against known label strings.
- Defined `TIER2_GENERIC_FIELDS` — the subset of `PART_I_FIELDS` extractable via this approach (checkbox/signature fields are excluded — see `test_never_attempts_checkbox_or_signature_fields`).

**Completed — 5.3 (Tier 3: Claude Vision extraction):**
- Implemented `extract_tier3()` using **pypdfium2** (to rasterize PDF pages to images) and the **Claude Vision API** (model **`claude-sonnet-4-6`**).
- Defined **`STAGE3_SYSTEM_PROMPT`**, sent with **`cache_control: ephemeral`** (per **IA-25** from Session 5) so repeated calls across multiple fields/images reuse the cached system prompt.
- `_parse_json_response()`: parses Claude's JSON response, handling both raw JSON and markdown-fenced (```json ... ```) responses.
- Null values returned by Claude are treated as **unresolved** (not included in results), distinguishing "Claude looked and found nothing" from "field not requested."

**Completed — 5.4 (Normalization helpers):**
- `normalize_source()`, `normalize_product_type()`, `normalize_serial_number()` (e.g., `"260001"` → `"26-1"`), `normalize_grape_varietals()` (splits on commas/semicolons/newlines into a list), and `_split_name_address()` (shared with Tier 1).

**Completed — 5.5-5.6 (Tiered orchestration & persistence):**
- `run_stage3_extraction()`: orchestrates the Tier 1 → Tier 2 → Tier 3 cascade — for each of the 21 `PART_I_FIELDS`, attempts Tier 1 first, falls back to Tier 2 if unresolved, and falls back to Tier 3 (one batched Claude Vision call requesting all still-unresolved fields) if needed. Fields that remain unresolved after all three tiers carry a `location_hint` (from `LOCATION_HINTS`) so the UI can still indicate where on the form a reviewer should look.
- `persist_form_parameters()`: persists each field's extraction result to the `FormParameter` table (value, confidence, extraction method, bbox/location hint), updates the corresponding **denormalized columns** on the `Application` record (e.g., `brand_name`, `applicant_name`, `product_type`, `source`, `serial_number`, `year`, `application_type`), and transitions the application's status to **`FORM_ASSESSED`**. Re-running persistence replaces (rather than duplicates) the existing `FormParameter` rows, and fields left unresolved by extraction do **not** overwrite values already present from upload time.

**Completed — 5.7 (Unit tests):**
- Created `app/tests/test_form_extraction.py` with **31 tests** covering normalization, all three extraction tiers (including mocked Claude responses for Tier 3), the tiered fallback orchestration, and persistence (including the "replace existing parameters" and "preserve upload-time values when unresolved" cases).
- **54/54 tests pass** (total across all test modules).

**Note on Tier 2 standalone behavior:** Tier 2 (`extract_tier2`) deliberately **never attempts** checkbox-derived or signature fields (`source`, `product_type`, `application_type`, `signature_present`, `foreign_translations`) — these require either AcroForm field state (Tier 1) or visual inspection (Tier 3), since a flattened text layer alone can't distinguish a checked box from an unchecked one.

**Outcome:** WBS 5.0 **complete** — full Tier 1/2/3 cascade implemented and orchestrated, normalization helpers, persistence with `FORM_ASSESSED` status transition, 54/54 tests passing. Pending approval.

---

**TTB Label Verification System**
*Copyright (c) 2026 Matthew Gabriel Sizemore · Assessment submission: IT Specialist (AI) · 26-DO-12891471-DH*
