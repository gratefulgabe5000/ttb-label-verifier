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

### Session 15: Frontend — Agent Dashboard & Detail View, Pass 1 (12.1-12.3, 12.7, 13.1-13.4)

**Context:** Per the WBS v2.1 re-sequencing (§4 Note 7), WBS 12.0 (Agent Dashboard) and 13.0 (Application Detail View) were pulled forward ahead of 6.0-10.0 so the buildable frontend surfaces — those depending only on the already-complete 1.0/3.0/4.0/5.0/11.0 — could be manually verified as each backend stage lands.

**Completed — Backend fix (prerequisite for 13.4):**
- `app/routers/applications.py`: `_to_detail()` now queries persisted `FormParameter`/`LabelParameter`/`Determination` rows so `GET /applications/{id}` returns real `form_parameters`/`label_parameters`/`determination`.

**Completed — 12.2/12.3 (Dashboard, Pass 1):**
- **12.2** — Filter by applicant (`DashboardPage.tsx`).
- **12.3** — Checkbox batch selection (`DashboardPage.tsx`).

**Completed — 13.1-13.4 (Detail View, Pass 1):**
- **13.1/13.2** — Split-view layout + react-pdf form renderer in `ApplicationDetailPage.tsx`, backed by two new file-serving endpoints (`GET /applications/{id}/form`, `GET /applications/{id}/label-images/{image_id}`) needed because uploaded files were stored on disk but never exposed over HTTP.
- **13.3** — Multi-image tab selector with thumbnails (`LabelImagesPanel.tsx`).
- **13.4** — SVG annotation overlay on the form panel, positioned via `form_parameters.bbox_json`.

**Completed — 12.8/13.12 (partial — Vitest setup):**
- Vitest configured in `web/`; unit tests covering 12.1-12.3/12.7 and 13.1-13.4 (6 tests, all passing).

**Outcome:** WBS 12.0/13.0 Pass 1 complete — Dashboard filter/batch-select, Detail View split layout with form renderer, multi-image tabs, and form-panel annotation overlay, plus the `_to_detail()` fix and two new file-serving endpoints that made the overlay possible. Manually verified against the "Test Upload" application from Session 13's WBS 4.0 manual test (1 PDF + 2 label images) at `/applications/{id}` — the form PDF and label images render in a split view with tabs; the SVG overlay shows "no extracted fields yet" until Stage 3 extraction (wired up as part of 6.0+) populates `form_parameters`. Pass 2 (12.4-12.6, 13.5-13.11, remaining 12.8/13.12 coverage) deferred until after WBS 10.0 per §4 Note 7.

---

### Session 16: Backend — Stage 4 Label Assessment (TS-02) — completes WBS 6.0

**Context:** With Stage 3 (form assessment) complete, this session implemented Stage 4 of the pipeline — extracting and assessing label-image fields using the TS-02 OpenCV/OCR augmentation strategy designed back in Session 4, in `app/services/label_extraction.py`.

**Completed — 6.1 (OpenCV preprocessing pipeline):**
- `deskew()` (Otsu threshold + `minAreaRect` skew estimation/correction), `normalize_contrast()` (CLAHE on the LAB L-channel), `suppress_glare()` (highlight mask + `inpaint`), composed in `preprocess_image()`.

**Completed — 6.2/6.3 (Claude Vision label extraction + Government Warning detection):**
- `STAGE4_SYSTEM_PROMPT` (cached) drives `extract_label_fields()`: the 8 mandatory + 5 secondary fields, `government_warning` (presence/header caps/bold + `text_exact_match` against the statutory 27 CFR § 16.21 text), and a generic `other_text` catch-all.

**Completed — 6.4/6.5 (OCR + bbox fuzzy-matching):**
- `run_ocr()` (pytesseract `image_to_data`); degrades gracefully to `[]` per §4 Note 7 contingency #1 (Tesseract binary not installed in this environment — covered by a dedicated test).
- `fuzzy_match_bbox()` (difflib `SequenceMatcher` over OCR word windows) and `compute_header_height_ratio()` (FR-040 acceptance case validated at exactly 2.0).

**Completed — 6.6/6.7 (Orchestration & persistence):**
- `run_stage4_extraction()`: `asyncio.gather` across an application's label images, with Claude-vs-OCR concurrency within each image.
- `persist_label_parameters()`: one `LabelParameter` row per `label_image_id` × field_name (incl. `bbox_json`/`header_height_ratio`), sets `application.status = "LABEL_ASSESSED"`.

**Completed — 6.8 (Unit tests):**
- Created `app/tests/test_label_extraction.py` with 22 new tests (preprocessing against the WBS 2.6 degraded fixtures, extraction parsing incl. government warning, OCR fuzzy-match, orchestration, persistence) — **81/81 pytest passing** (was 59/59).

**Outcome:** WBS 6.0 complete — full OpenCV preprocessing pipeline, Claude Vision label extraction with Government Warning compliance check, graceful OCR degradation, fuzzy bbox-matching, per-image concurrent orchestration, and persistence with `LABEL_ASSESSED` status transition. 81/81 tests passing. Pending approval.

---

### Session 17: Backend — Stage 5 Comparison Engine (7.1-7.16) — completes WBS 7.0

**Context:** With Stage 4 (label assessment) complete, this session implemented Stage 5 — comparing the persisted `form_parameters` against `label_parameters` (across all of an application's label images) to produce per-field `MATCH` / `HARD_FAILURE` / `POSSIBLE_ALLOWABLE` comparison results, per the re-scoped 16-sub-item WBS 7.0 (FR-050-059, FR-066, FR-100-107).

**Completed — 7.1 (Multi-image resolution helper):**
- Shared helper in `app/services/comparison_engine.py` resolving whether a form value is "on label" if found on **any** of the application's label images — used by every comparison rule below (A-10, IA-18, FR-038).

**Completed — 7.2-7.4 (Brand Name, Government Warning, Type 14b):**
- Brand Name comparison (case/punctuation-tolerant, FR-050-052).
- Government Warning comparison (exact-text + bold/caps via `header_height_ratio`, FR-053-055).
- Type 14b "for sale in [STATE]" check (FR-056).
- **Fix:** removed an errant `.capitalize()` call when building the Government Warning failure note — it was lowercasing the statutory "GOVERNMENT WARNING:" header text in the reported message.

**Completed — 7.5 (Section V Allowable-Revision mapping):**
- Classification mapping flagging `POSSIBLE_ALLOWABLE` vs `HARD_FAILURE` outcomes for the Brand Name and Applicant Address rules, per §2.6 Allowable Revisions (FR-057, FR-059).

**Completed — 7.6-7.14 (Remaining comparison rules):**
- Country of Origin (conditional on Item 3 = "imported", A-17/FR-066), Fanciful Name (Item 7, FR-100), Product Type/Class-Type consistency (Item 5, FR-101), Applicant Name (Item 8, FR-102), Applicant Address (Item 8/8a, incl. in-state Allowable Revision, FR-103), Grape Varietals (Item 10, Wine only, FR-104), Wine Appellation (Item 11, Wine only, conditional, FR-105), ABV presence + product-type consistency (FR-106), Net Contents presence (FR-107).

**Completed — 7.15 (Persistence):**
- `app/models/comparison.py`: added a `label_image_id` foreign-key column to `Comparison`, so each comparison result can record which label image (if any) it was resolved against.
- `app/services/application_service.py`: added `list_comparisons()`.
- All 12 rule results persisted to the `comparisons` table (FR-058).

**Completed — 7.16 (Unit tests):**
- Created `app/tests/test_comparison_engine.py` — 47 new tests covering all 12 comparison rules (MATCH/HARD_FAILURE/POSSIBLE_ALLOWABLE outcomes), the multi-image resolution helper (7.1), and persistence, using 2.3/2.4/2.5/2.7.
- **129/129 pytest passing** (was 81/81).

**Outcome:** WBS 7.0 complete — `app/services/comparison_engine.py` (430 lines: 12 rule functions, multi-image resolution helper, Section V mapping, orchestration, persistence), `label_image_id` added to `Comparison`, `list_comparisons()` added to `application_service.py`, 129/129 tests passing. `TODO.md` updated (status table, checklist, "Next Session" reoriented to WBS 8.0). Pending approval.

---

### Session 18: Backend — Stage 6 Determination & Reporting — completes WBS 8.0

**Context:** With Stage 5 (comparison engine) complete, this session implemented Stage 6 — turning the persisted `comparisons` rows for an application into an overall recommendation, the FR-063/064 supporting lists, a per-application determination report, and persistence to `determinations`, per WBS 8.0 (FR-060-065).

**Completed — 8.1 (Determination logic):**
- `app/services/determination_engine.py`: `determine_recommendation()` — DENY if any comparison is `HARD_FAILURE` (FR-061, takes precedence), else RECOMMEND_EXEMPTION_REVIEW if any `POSSIBLE_ALLOWABLE` (FR-062), else APPROVE (FR-060, including the vacuous case of no comparisons at all).

**Completed — 8.2 (Hard-failure / allowable-revision lists):**
- `build_hard_failures()` (FR-063): one entry per `HARD_FAILURE` comparison with `field_name`/`form_value`/`label_value` plus a plain-English `description` — uses the comparison's existing `note` where present, and falls back to a generated description (via a `FIELD_LABELS` lookup) for the plain-text-mismatch rules (brand name, fanciful name, applicant name/address, wine appellation) that leave `note` empty.
- `build_allowable_revisions()` (FR-064): one entry per `POSSIBLE_ALLOWABLE` comparison with `field_name`, `discrepancy` (from `note`), and `section_v_ref`.
- `run_determination()` combines both into a `DeterminationResult`.

**Completed — 8.3 (Determination report schema):**
- `build_confidence_scores()`: per-field extraction confidence merging Stage 4 (`label_parameters`) values as a base with Stage 3 (`form_parameters`) values taking precedence where the form supplied the field.
- `build_determination_report()` / `DeterminationReport` dataclass assembles all FR-065 components: `application_id`, `recommendation`, `comparisons`, `hard_failures`, `allowable_revisions`, `confidence_scores`, `processed_at`.
- `app/schemas/application.py`: added `ComparisonOut`, `HardFailureOut`, `AllowableRevisionOut`, and `DeterminationReportOut` Pydantic schemas for the eventual API surface (WBS 9.0).

**Completed — 8.4 (Persistence):**
- `persist_determination()`: upserts the `determinations` row (`recommendation`, `hard_failures_json`, `allowable_json`), sets `application.status = "DETERMINED"` and `application.processed_at`.

**Completed — 8.5 (Unit tests):**
- Created `app/tests/test_determination_engine.py` — 21 new tests covering all 3 determination outcomes (incl. HARD_FAILURE-takes-precedence-over-POSSIBLE_ALLOWABLE and the no-comparisons-at-all edge case), FR-063/064 list generation (including the generated-description fallback), the confidence-score merge, the full report assembly, and persistence (insert + upsert).
- **150/150 pytest passing** (was 129/129).

**Outcome:** WBS 8.0 complete — `app/services/determination_engine.py` (determination logic, FR-063/064 list builders, report assembly, persistence), four new Pydantic schemas in `app/schemas/application.py`, 150/150 tests passing. `TODO.md` updated (status table, checklist, "Next Session" reoriented to WBS 9.0). Pending approval.

---

### Session 19: Backend — Pipeline Orchestration & Batch Processing — completes WBS 9.0

**Context:** With Stages 3-6 implemented as standalone services (WBS 5.0-8.0), this session wires them together into the actual request-handling pipeline — a single-application orchestrator (9.1-9.2), a bounded-concurrency batch orchestrator (9.3-9.5), and the comparisons read endpoint (9.6) — per WBS 9.0 (FR-074-077, A-07, IA-17, IA-24).

**Completed — 9.1 (Single-application orchestrator):**
- `app/services/pipeline.py`: `run_extraction()` runs Stage 3 (form, via `asyncio.to_thread`) and Stage 4 (label) concurrently via `asyncio.gather` (IA-24 concurrent-compute). `persist_extraction_and_run_stages_5_6()` persists the Stage 3/4 results, then runs and persists Stage 5 (comparison) and Stage 6 (determination) against the persisted rows (IA-24 sequential-persist). `process_application()` ties both together, setting `status = "PROCESSING"` at the start and `status = "ERROR"` if Stage 3/4 extraction raises.

**Completed — 9.2 (`POST /applications/{id}/process`):**
- `app/routers/applications.py`: new `process_application` endpoint (FR-074) — 404s for applications not owned by the calling agent, otherwise runs `pipeline.process_application()` and returns the full `ApplicationDetailOut`.
- Removed the TEMPORARY `/debug/extract` endpoint and its test (`test_applications.py`), now superseded by `/process`.

**Completed — 9.3 (Batch Orchestrator — bounded concurrency):**
- `app/services/batch_service.py`: `run_batch()` — sets all applications to `"PROCESSING"`, then runs each application's Stage 3/4 extraction (`pipeline.run_extraction`) concurrently bounded by an `asyncio.Semaphore` (`DEFAULT_BATCH_CONCURRENCY = 4`, within the 3-5 range of A-07/IA-17). Persistence (`pipeline.persist_extraction_and_run_stages_5_6`, status updates, batch finalization) happens sequentially on a single shared `db: Session` as each application's extraction resolves via `asyncio.as_completed` — completion order may differ from selection order (A-07).

**Completed — 9.4 (`POST /batch/process` + `batches` row):**
- `app/models/batch.py` (`Batch` model), `app/schemas/batch.py` (`BatchProcessIn`, `BatchStatusOut`, `BatchApplicationStatusOut`), `app/routers/batch.py`: `create_batch()` inserts the `batches` row (`application_ids` as JSON); the endpoint 404s if any requested application isn't owned by the calling agent, runs the batch synchronously, and returns the resulting `BatchStatusOut`.
- `_finalize_batch()` (FR-077): tallies `approved_count`/`denied_count`/`exemption_count` from each application's `Determination.recommendation`, persists them plus `summary_json` and `completed_at` on the `Batch` row.

**Completed — 9.5 (`GET /batch/{id}/status`):**
- `batch_service.get_batch_status()` (FR-075/076): per-application status + recommendation, `total`/`completed` counts (`TERMINAL_STATUSES = ("DETERMINED", "ERROR")`), and the same summary counts as 9.4; overall `status` is `"COMPLETE"` once `completed == total`, else `"PROCESSING"`. Endpoint 404s for batches not created by the calling agent.

**Completed — 9.6 (`GET /applications/{id}/comparisons`):**
- `app/routers/applications.py`: new `get_application_comparisons` endpoint returns `list[ComparisonOut]` via `application_service.list_comparisons()`; 404s for applications not owned by the calling agent; returns `[]` before processing.

**Completed — 9.7 (Unit/integration tests):**
- `app/tests/test_pipeline.py` (6 tests): end-to-end `/process` reaches `DETERMINED` with all Stage 3/4/5/6 outputs populated, persisted comparisons retrievable via 9.6, 404 ownership checks for both endpoints, empty comparisons before processing, and a PR-001 timing test (single application, Stage 3+4 concurrent, completes well under 5s).
- `app/tests/test_batch.py` (5 tests): `test_run_batch_bounds_concurrent_extraction` monkeypatches `pipeline.run_extraction` with an instrumented coroutine to assert the semaphore caps concurrent extractions at exactly the configured `concurrency` (A-07/IA-17), then verifies all applications reach `DETERMINED` and the batch summary counts sum correctly; HTTP-level tests cover `POST /batch/process` → `BatchStatusOut` with `status="COMPLETE"` and summary counts, `GET /batch/{id}/status` returning the same summary, and 404s for unowned applications/batches.
- **161/161 pytest passing** (was 150/150).

**Outcome:** WBS 9.0 complete — `app/services/pipeline.py` (single-application orchestration, IA-24), `app/services/batch_service.py` (bounded-concurrency batch orchestration, A-07/IA-17, batch summary), `app/models/batch.py`, `app/schemas/batch.py`, `app/routers/batch.py`, two new endpoints on `app/routers/applications.py` (9.2, 9.6) replacing the temporary `/debug/extract` endpoint, 161/161 tests passing. `TODO.md` updated (status table, checklist, "Next Session" reoriented to WBS 10.0). Pending approval.

---

### Session 20: Backend — Overrides, Finalization & Batch Report — completes WBS 10.0

**Context:** With the pipeline and batch orchestrators in place (WBS 9.0), this session adds the agent-facing review actions on top of a completed determination: per-parameter and overall determination overrides with an audit trail (10.1), a finalize action (10.2), and a batch report including the most common failure type (10.3), per WBS 10.0 (FR-086-097, A-15, SR-004).

**Completed — 10.1 (`POST /determinations/{id}/override`):**
- `app/models/comparison.py`: added `agent_override`/`override_by`/`override_reason`/`override_at` columns, mirroring the existing overall-override fields already on `determinations` (FR-086-088, SR-004) — `result`/`recommendation` retain the original AI determination; the override fields record the audit trail alongside it.
- `app/schemas/determination.py` (new): `OverrideIn` (`field: str | None`, `override_value`, `reason` — `field_validator` rejects a blank/whitespace-only `reason`, FR-087) and `OverrideOut` (the FR-088/SR-004 audit record: `application_id`, `field`, `original_value`, `override_value`, `override_by`, `override_reason`, `override_at`).
- `app/services/override_service.py` (new): `apply_override()` — when `field` is `None`, records an overall-determination override (FR-089) on `determinations`; otherwise looks up the matching `comparisons` row by `field_name` for a per-parameter override (FR-086-088), raising `FieldNotFoundError` if none exists.
- `app/routers/determinations.py` (new): `POST /{id}/override` — 404s if the determination doesn't exist or its application isn't owned by the calling agent, 404s for an unknown `field`, 422s for a blank `reason`.
- `app/schemas/application.py`: added the four new override fields to `ComparisonOut`.

**Completed — 10.2 (`POST /determinations/{id}/finalize`):**
- `override_service.finalize_determination()` sets `determinations.finalized_at` (FR-090); per A-15, does not re-run the Stage 3-6 pipeline. `app/routers/determinations.py`: `POST /{id}/finalize` returns the updated `DeterminationOut`, with the same ownership-based 404s as override.
- A-16/SR-003 file-retention window (`finalized_at`) is a persistent-storage/deployment requirement (already covered by the Railway volume, IA-26) — no file-deletion logic added, since FR-080/FR-081 still need to render the source files in the Detail View after finalization.

**Completed — 10.3 (`GET /batch/{id}/report`):**
- `app/schemas/batch.py`: `BatchReportOut(BatchStatusOut)` adds `most_common_failure: str | None`.
- `app/services/batch_service.py`: `get_batch_report()` (FR-095-097) reuses `get_batch_status()` for the summary counts and per-application list (FR-096), then tallies `HARD_FAILURE` comparisons across the batch's applications by field name (using `determination_engine.FIELD_LABELS` for human-readable names, FR-097) to find the most common failure type.
- `app/routers/batch.py`: `GET /{batch_id}/report`, 404 for batches not created by the calling agent.

**Completed — 10.4 (Unit tests):**
- `app/tests/test_determinations.py` (8 tests): per-parameter override records the audit trail while leaving `comparisons.result` (the original AI determination) untouched; overall-determination override likewise leaves `recommendation` untouched; blank `reason` → 422; unknown `field` → 404; ownership 404s for both override and finalize; finalize sets `finalized_at`.
- `app/tests/test_batch.py` (+3 tests): `GET /batch/{id}/report` returns the same summary counts as `/batch/process`/`/batch/{id}/status` plus `most_common_failure`, and 404s for batches owned by another agent or that don't exist.
- **172/172 pytest passing** (was 161/161).

**Outcome:** WBS 10.0 complete — `app/services/override_service.py`, `app/routers/determinations.py`, `app/schemas/determination.py`, override columns on `app/models/comparison.py`, `BatchReportOut`/`get_batch_report()`/`GET /batch/{id}/report` for the batch report, 172/172 tests passing. This completes all of WBS Phase 1's backend work (1.0, 3.0-10.0). `TODO.md` updated (status table, checklist, "Next Session" reoriented to WBS 12.0/13.0 Pass 2 per WBS v2.1 §4 Note 7). Pending approval.

---

## 2026-06-12

### Session 21: Frontend — WBS 12.0/13.0 Pass 2 (Dashboard Process/Badges/Summary, Detail View Overlays/Cross-Highlight/Results Table/Overrides/Finalize) — completes WBS 12.0 and 13.0

**Context:** With WBS 10.0 complete (Session 20), this session executed Pass 2 of the 12.0/13.0 re-sequencing (WBS v2.1 §4 Note 7) — completing the Agent Dashboard and Application Detail View against the now-complete backend (`/batch/process`, `/batch/{id}/status`, `/applications/{id}/comparisons`, `/determinations/{id}/override`, `/determinations/{id}/finalize`, `/batch/{id}/report`).

**Completed — Shared frontend updates (prerequisite):**
- `lib/types.ts`/`lib/api-client.ts`: replaced the placeholder `BatchStatus`/`Batch`/`debugApi` shapes with types matching the actual WBS 9.0/10.0 schemas — `BatchStatus` (`total`/`completed`/`approved_count`/`denied_count`/`exemption_count`/`applications: BatchApplicationStatus[]`), new `BatchReport extends BatchStatus` (`most_common_failure`), `OverrideDeterminationRequest.field` made optional/nullable (overall vs. per-parameter override per FR-086/089), new `OverrideResult` type, and `Comparison` extended with `label_image_id`/`agent_override`/`override_by`/`override_reason`/`override_at`. Removed the TEMPORARY `debugApi`/`/debug/extract` client (superseded by WBS 9.0's `/process`).
- New `lib/field-labels.ts`: shared `FIELD_LABELS` map + `fieldLabel()` helper, mirroring `app/services/determination_engine.py`'s `FIELD_LABELS` (FR-085/097), used by the Detail View results table and override dialogs.
- Removed `DebugParametersDialog.tsx` (the TEMPORARY Stage 3/4 manual-run UI from Sessions 15/19) and its usage in `ApplicationDetailPage.tsx`, replaced by the new `DeterminationPanel`.

**Completed — 12.4/12.5/12.6 (Dashboard — Process Selected, badges, batch summary):**
- `DashboardPage.tsx`: "Process Selected" button calls `batchApi.process()` (FR-074), then polls `batchApi.status(batchId)` via a React Query `refetchInterval` (1s, until `status === "COMPLETE"`, FR-075).
- New `RecommendationBadge.tsx` — color-coded APPROVE/DENY/RECOMMEND_EXEMPTION_REVIEW badge, added as a "Result" column on the dashboard table (FR-076).
- Batch summary header: shows live progress ("Processing batch #N: X of Y...") while running, then final approved/denied/exemption-review counts once complete (FR-077).

**Completed — 13.5/13.6/13.11 (Detail View — label panel overlay, cross-highlight, auto-tab-switch):**
- `LabelImagesPanel.tsx`: added an SVG annotation overlay per label image, positioned via `label_parameters.bbox_json` (FR-083), with hover-driven cross-highlight color (`#2563eb` when hovered, `#d97706` otherwise) shared with the form-panel overlay via `hoveredField`/`onHoverField` (FR-084).
- `ApplicationDetailPage.tsx`: computes an `effectiveLabelImageId` during render — when the hovered field has a matching comparison with a `label_image_id`, that image's tab becomes active; otherwise falls back to the agent's last manually-selected tab (FR-091/13.11).

**Completed — 13.7/13.8/13.9 (Detail View — results table, per-field override, overall override):**
- New `ParameterResultsTable.tsx`: renders `comparisons` (FR-085) with a new `ComparisonResultBadge`, a combined section-V-reference/note column, and hover-driven cross-highlight; when `determinationId !== null && !finalized`, each row is wrapped in a `ContextMenu` with an "Override result..." item opening a shared `OverrideDialog` (FR-086/087).
- New `OverrideDialog.tsx` (shared by per-field and overall overrides): select-new-value + required-reason form, posts to `determinationsApi.override()` (FR-088, SR-004 audit trail), invalidates `["application", id]`/`["comparisons", id]` on success.
- New `DeterminationPanel.tsx`: shows the overall recommendation (`RecommendationBadge`, with an "overridden from ..." note when `agent_override` is set), an "Override" button opening `OverrideDialog` with `field: null` (FR-089), and a "Finalize" button.

**Completed — 13.10 (Detail View — finalize):**
- `DeterminationPanel.tsx`: "Finalize" button calls `determinationsApi.finalize(determination.id)` (FR-090); on success swaps the "Override"/"Finalize" buttons for a "Finalized" badge.

**Completed — 12.8/13.12 (Vitest coverage):**
- `DashboardPage.test.tsx`: +2 tests — "processes selected applications and shows the batch summary header" (12.4/12.6) and "shows recommendation result badges for applications in the batch result" (12.5).
- `ApplicationDetailPage.test.tsx`: +5 tests — label-panel SVG overlay (13.5), parameter results table from comparisons (13.7), cross-highlight + auto-tab-switch (13.6/13.11), overall override + finalize (13.9/13.10), and context-menu per-field override (13.8). **13/13 tests passing** across both files (~3.9s).

**Bug fixes found via the new tests (real bugs, not test-only):**
- `FormPdfPanel.tsx`: inline `onLoadSuccess` handlers passed to `<Document>`/`<Page>` got a new function reference every render; combined with `setPageSize({...newObject})` always producing a new object reference, this created an infinite render→effect→setState loop (530s OOM in the test runner). Fixed by memoizing both handlers with `useCallback(fn, [])`.
- `LabelImagesPanel.tsx`: the `<img onLoad>` handler read `event.currentTarget.naturalWidth`/`naturalHeight` inside a deferred functional `setState` updater — React nulls `currentTarget` after the synchronous handler returns, causing `TypeError: Cannot read properties of null`. Fixed by destructuring `naturalWidth`/`naturalHeight` synchronously before constructing the updater.
- `OverrideDialog.tsx` / `ApplicationDetailPage.tsx`: ESLint's `react-hooks/set-state-in-effect` flagged two `useEffect`s that called `setState` synchronously on mount/prop-change. `OverrideDialog` now resets `overrideValue`/`reason` via the React-recommended "adjust state during render" pattern (compares `open` against a `prevOpen` state); `ApplicationDetailPage`'s hover→auto-tab-switch logic was removed entirely in favor of the `effectiveLabelImageId` render-time computation above (also resolved a `react-hooks/exhaustive-deps` warning).

**Verification:**
- `npx vitest run` — 13/13 passing (~3.9s, no hangs/OOM).
- `npm run build` — clean (`tsc -b && vite build`).
- `npm run lint` — clean (0 errors, 0 warnings).

**Outcome:** WBS 12.0 and 13.0 **complete in full** (all sub-items, including 12.8/13.12 unit-test coverage) — WBS → v2.3. This completes the 12.0/13.0 re-sequencing from WBS v2.1 §4 Note 7. `TODO.md` updated (status table, checklist, "Next Session" reoriented to WBS 14.0, Batch Report View). Pending approval.

---

### Session 22: Backend — Government Warning 3-way refinement, Importer-vs-bottler matching, AI key status banner (post-12.0/13.0 polish)

**Context:** With WBS 12.0/13.0 complete (Session 21), this session made a set of Stage 5 comparison-engine refinements within already-complete sub-items (7.3, 7.9, 7.10, 6.2) plus two small frontend additions, driven by review of real Claude Vision output for `application_id=2` and direct user feedback on the Government Warning rule.

**Completed — Government Warning 3-way split + case/punctuation-tolerant MATCH (7.3 refinement, FR-053-055):**
- `compare_government_warning()` now returns `list[FieldComparison]` (3 rows: `government_warning_text`, `government_warning_caps`, `government_warning_bold`) instead of one combined row, so a header-formatting issue no longer obscures an otherwise-correct statement (or vice versa). `run_comparisons()` already handled list-returning rules via `isinstance(outcome, list)`.
- `_compare_government_warning_text()`: per user direction, label text that differs from 27 CFR § 16.21 only in letter case and/or punctuation (e.g. ALL CAPS rendering, a comma instead of a period before "(2)", a missing trailing period) is now a full **MATCH**, not `POSSIBLE_ALLOWABLE`/Sec. V 3b — collapsed from a two-tier check to a single `_strip_punctuation()` equality check.
- New `FIELD_LABELS` entries (`app/services/determination_engine.py` + `web/src/lib/field-labels.ts`): "Government Warning — statement text (27 CFR § 16.21)", "— header in ALL CAPS", "— header in bold type". `ParameterResultsTable.tsx`'s Field column switched to `whitespace-normal` to accommodate the longer labels.
- Tests: renamed `test_possible_allowable_on_punctuation_only_text_difference` → `test_match_on_punctuation_only_text_difference`; added `test_match_on_all_caps_and_punctuation_difference` (real-world case: ALL CAPS + comma + missing trailing period → MATCH).

**Completed — Importer-vs-bottler matching for Item 8 (7.9/7.10 refinement, FR-102/103):**
- `resolve_multi_image()`'s `field_name` parameter now accepts `str | list[str]`. `compare_applicant_name()`/`compare_applicant_address()` check Item 8 (Applicant Name/Address) against `["bottler_name", "importer_name"]` / `["bottler_address", "importer_address"]` — for imported products, Item 8 is filled in by the U.S. importer, but the label's bottler/producer fields usually identify the foreign manufacturer.
- New `address_matches()` + `_normalize_address_for_match()` + `_ZIP_PLUS4_RE`: case/punctuation-insensitive address comparison that also treats a ZIP+4 as equivalent to its 5-digit ZIP.
- `label_extraction.py`: new `importer_name`/`importer_address` SECONDARY_FIELDS, `LOCATION_HINTS`, and Claude Vision prompt schema entries ("back label, near 'Imported by'").
- Tests: `test_match_against_importer_for_imported_product` (×2, name + address) and `test_match_ignores_case_punctuation_and_zip4`.
- New "About..." section in `SettingsDialog.tsx` flags this as an open product question — not yet confirmed whether Item 8 should match the importer, the manufacturer, or either, for imported-item applications.

**Completed — AI API key status banner + Windows Tesseract config:**
- New `ApiKeyStatusBanner.tsx`, wired into `AppShell.tsx` between the header and `<main>`; new `API_KEY_QUERY_KEY` export in `api-client.ts` (shared with `SettingsDialog.tsx`).
- New optional `tesseract_cmd` setting (`app/config.py`, `app/.env.example`) for Windows dev machines where pytesseract's binary isn't on PATH; `label_extraction.py` sets `pytesseract.pytesseract.tesseract_cmd` from it at import time if configured.

**Verification:**
- `app/.venv/Scripts/python.exe -m pytest -q` — **177/177 passing** (was 172/172), +5 new tests above.
- `npx vitest run` (web/) — 13/13 passing (~3.8s, no OOM) — confirms Session 21's `FormPdfPanel`/`LabelImagesPanel` OOM fixes hold.
- `npm run build` / `npm run lint` (web/) — clean.
- Re-ran Stage 5/6 for `application_id=2` against its already-persisted Stage 3/4 results (no new Claude Vision calls): `government_warning_text` flipped `POSSIBLE_ALLOWABLE` (Sec. V 3b) → `MATCH`; overall recommendation flipped `RECOMMEND_EXEMPTION_REVIEW` → `APPROVE`.

**Outcome:** Refinements to already-complete WBS items 6.2/7.3/7.9/7.10 — no new WBS line items, but WBS → v2.4 (revision history note + new §4 Note 8 on the open importer-vs-manufacturer question for Item 8). `TODO.md` pytest count updated to 177/177. Pending approval.

---

### Session 23: Government Warning Bold Corroboration (6.2/6.8 refinement) & Detail View Results Sidebar (13.0 polish)

**Context:** Continuing Session 22's Government Warning refinements, re-processing `application_id=2` exposed a separate issue: Claude Vision's `header_bold` flag for the same label image flip-flopped between runs — `True` on an earlier run, `False` on a re-run — flipping `government_warning_bold` to `HARD_FAILURE` even though the header is genuinely bold. Once that was fixed and confirmed, the session moved on to UI feedback on the Application Detail View's visual clutter and information layout (post-WBS 13.0).

**Completed — Government Warning bold-detection corroboration (6.2/6.8 refinement):**
- `app/services/label_extraction.py`: added `temperature=0` to the Stage 4 `client.messages.create()` call in `extract_label_fields()`, reducing run-to-run non-determinism in Claude's `header_bold` flag.
- New OCR-based corroboration for when Claude still reports `header_bold: False`: `_word_stroke_weight()` (distance-transform-based stroke-width/height ratio for a single OCR word) and `compute_header_stroke_ratio()` (ratio of the "GOVERNMENT WARNING" header's mean stroke weight to the body text's median stroke weight). New constant `HEADER_BOLD_STROKE_RATIO_THRESHOLD = 0.9`.
- In `_process_label_image`, when Claude's `header_bold` is not already `True`, the stroke ratio is computed and `header_bold` is promoted to `True` if the ratio meets the threshold — i.e., OCR shows the header isn't lighter-weight than the body, contradicting Claude's "not bold" call.
- Verified against the real `application_id=2` label image (`image_id=3`): `stroke_ratio = 1.026` ≥ 0.9 → would promote `header_bold` False→True.
- Tests: `app/tests/test_label_extraction.py` — added a `temperature=0` assertion to `test_parses_simple_fields`; new `TestHeaderStrokeRatio` (4 tests, synthetic thick/thin-stroke canvases) and `TestHeaderBoldCorroboration` (4 tests, via `_process_label_image` with monkeypatched `run_ocr`/`compute_header_stroke_ratio`) — **198/198 pytest passing**.
- **Confirmed by Gabe**: "it seems to process Application 2 correctly now!"

**Completed — Detail View Results Sidebar (13.0 polish, per Gabe's UI feedback):**
- `FormPdfPanel.tsx` / `LabelImagesPanel.tsx`: the SVG bounding-box overlay `<rect>`s are now invisible (`fill="transparent"`, `stroke="none"`) by default, becoming visible (blue highlight) only when the corresponding field is hovered or pinned — the form/label panels now render "without embellishment" until a reviewer actively inspects a field. The label panel's red cross-highlight ellipse was already conditional on hover/pin.
- New `ResultsSidebar.tsx`: a right-hand sidebar (320px) whose top section holds a compact "Application #N — Applicant" title plus `DeterminationPanel` (Approve/Deny/Exemption-Review badge, Override button, Finalize button — moved here from the removed top section), and below it a Field | Status table — one row per comparison, hover/click wired to the same `hoveredField`/`pinnedField` state as the form/label panels (bidirectional cross-highlight + click-to-pin), plus the per-field "Override result..." context menu (moved here from the results table).
- `ParameterResultsTable.tsx` (bottom table, kept): trimmed from 5 columns to 3 — Form Value | Label Value | Reference/Note. The Field and Result/status columns (and the override context menu) moved to `ResultsSidebar` per Gabe's direction, eliminating duplicate field-name/badge text between the two tables.
- `DeterminationPanel.tsx`: root `flex items-center gap-2` → `flex flex-wrap items-center gap-2` so the badge/buttons wrap inside the narrow sidebar.
- `ApplicationDetailPage.tsx`: removed the old top `Card` (the "Application #N — Applicant" title, the `status` outline badge, and `DeterminationPanel` — the status badge dropped entirely, the rest redistributed into the sidebar above). New layout is a `grid-cols-1 lg:grid-cols-[1fr_1fr_320px]` row of Form | Label | `ResultsSidebar`, with the trimmed `ParameterResultsTable` Card retained below.

**Verification:**
- `npx vitest run` (web/) — **15/15 passing**, no test edits required (the existing 13.x tests' "Application #1" / field-label / badge / `tr` assertions all still resolve correctly against the new sidebar).
- `npx tsc --noEmit` (web/) — clean.
- Dev servers (frontend :5173, backend :8000) were already running; `/applications/2` returns 200. No browser-automation tool was available this session to visually confirm hover/pin/cross-highlight behavior in-browser — flagged for Gabe to eyeball before considering this final.

**Outcome:** Government Warning bold-detection now corroborated via OCR stroke-ratio (198/198 pytest, confirmed against real application 2 data). Detail View restructured per Gabe's UI feedback — overlays hidden until hover/pin, new `ResultsSidebar.tsx` consolidating field/status + determination controls, top section removed, `ParameterResultsTable` trimmed to avoid duplication (15/15 Vitest, `tsc` clean). No new WBS line items (refinements within already-complete 6.2/6.8 and 13.0). Pending Gabe's manual browser verification of the new sidebar/overlay behavior.

---

### Session 24: Frontend — WBS 14.0 Batch Report View, plus a UI Polish Round (API Key Badge, Reprocess Controls, Zoom Panels, Finalize-Aware Dashboard)

**Context:** With WBS 13.0 complete (Session 23) and the Detail View restructured into a Results Sidebar, this session implemented the last unbuilt frontend view — the Batch Report (WBS 14.0) — then continued with a round of UI polish across the Dashboard and Detail View that had accumulated as "nice to have" items during Sessions 21–23.

**Completed — 14.1-14.5 (Batch Report View, completes WBS 14.0):**
- New `web/src/pages/BatchReportPage.tsx`: summary stat cards (total/approved/denied/exemption-review) plus a processing indicator while the batch is incomplete (14.1); `most_common_failure` display beneath the cards, showing "None" when absent (14.2).
- New `web/src/lib/csv.ts` (`toCsv`/`downloadCsv`): "Export CSV" writes one row per application — applicant, serial #, status, recommendation (14.3).
- "Print / Save as PDF" via `window.print()`, with `print:hidden` added to `AppShell`'s header/API-key banner and the report's action buttons for a clean printout (14.4).
- `DashboardPage.tsx`: added a "View Report" link in the completed-batch summary, routing to `/batches/{id}`.
- `web/src/pages/BatchReportPage.test.tsx` (5 new tests) plus one new Dashboard wiring test — 21/21 Vitest passing (14.5).
- Verified live against the real backend: `GET /batch/{id}/report` returns the exact `BatchReport` shape the page consumes (confirmed via `curl` against batches #9/#11 in the dev DB).
- `WBS.md` → v2.5 (14.0-14.5 marked complete); `TODO.md` updated.

**Completed — UI polish round (no new WBS items):**
- New `ApiKeyStatusBadge.tsx` replaces the full-width `ApiKeyStatusBanner` in `AppShell.tsx`'s header, left of the Settings gear.
- `ResultsSidebar.tsx`: dropped the applicant name from the card title, added a "Reprocess" button (full pipeline re-run) in the card header and a circular reprocess button on the Results card (comparison-only re-run).
- `DeterminationPanel.tsx`: added a "Recommended action:" label, restructured into a `justify-between` row with the badge left and Override/Finalize (or a "Finalized" badge) right-aligned.
- `FormPdfPanel.tsx` / `LabelImagesPanel.tsx`: each now owns its own `Card`, scales to container width (`useContainerWidth`), supports mousewheel zoom (`useWheelZoom`), and has a circular reprocess button in the header; `LabelImagesPanel` moved thumbnails into the header as a right-justified `CardAction` and introduced a `LabelImageContent` subcomponent for per-tab zoom.
- `ApplicationDetailPage.tsx`: removed the redundant outer `Card` wrappers now that the panels own their own cards.
- Dashboard now reflects finalization: `finalize_determination` (`override_service.py`) sets `application.status = "FINALIZED"`; `TERMINAL_STATUSES` now includes `"FINALIZED"`; `ApplicationOut` gained `recommendation`/`finalized_at` (via a new `_application_out` helper, batch-loading determinations for the list endpoint); `DashboardPage.tsx`'s Status column shows a `RecommendationBadge` once `finalized_at` is set, else the raw status string.
- New `ApiKeyStatusBadge.test.tsx` plus 5 new `ApplicationDetailPage.test.tsx` tests covering "Recommended action:" and all four reprocess buttons.

**Verification:** backend pytest 204/204; frontend `tsc --noEmit` clean, `npm run lint` clean, `npx vitest run` 28/28, `npm run build` succeeds. Fixed 3 test fixtures (`DashboardPage.test.tsx`, `BatchReportPage.test.tsx`, `ApplicationDetailPage.test.tsx`) missing the new `recommendation`/`finalized_at` fields.

**Outcome:** WBS 14.0 complete in full (`WBS.md` → v2.5), plus a substantial UI polish pass across the Dashboard and Detail View — no new WBS line items. `TODO.md` updated, "Next Session" pointed at WBS 15.0.

---

### Session 25: WBS 15.0 — Integration Audit & Error-State Surfacing — completes WBS 15.0

**Context:** With WBS 11.0-14.0 all complete, this session closed out WBS 15.0 (Integration: Frontend ↔ Backend Wiring) — an audit of whether the Dashboard, Detail View, Batch Report, and auth flow were genuinely wired to the live API (15.1-15.4), plus the remaining plain-English error-handling gaps (15.5, UR-003).

**Completed — 15.1-15.4 (audit, no code changes):**
- Confirmed the Dashboard (12.0) already calls `GET /applications`, `POST /batch/process`, `GET /batch/{id}/status` as part of 12.4-12.6.
- Confirmed the Detail View (13.0) already calls `GET /applications/{id}`, `POST /determinations/{id}/override`, `POST /determinations/{id}/finalize` as part of 13.8-13.10.
- Confirmed the Batch Report (14.0) already calls `GET /batch/{id}/report` as part of 14.1.
- Confirmed the auth flow (login → JWT storage → authenticated requests) is already wired via `AuthContext`/`apiFetch`/`ProtectedRoute`.
- All four were already complete because 12.0-14.0 were built directly against the live typed API client rather than mocked data — no changes needed.

**Completed — 15.5 (plain-English error surfacing, UR-003):**
- `ApplicationDetailPage.tsx` + `ResultsSidebar.tsx` + `ParameterResultsTable.tsx`: a failed comparisons fetch now shows "Failed to load comparison results. Please try again." in both the Results sidebar and the Parameter Results table (previously silently rendered the empty state).
- `DashboardPage.tsx`: a failed batch-status poll now shows a dismissible error banner ("Failed to load status for batch #{id}...") with Retry and Dismiss buttons, instead of leaving the batch silently stuck "processing" forever.
- 2 new Vitest tests covering both cases.

**Verification:** `npm run build` clean, `npm run lint` clean, `npx vitest run` → 30/30 passing, backend pytest → 204/204 (untouched, re-run for safety).

**Outcome:** WBS 15.0 complete (`WBS.md` → v2.6, §4 Note 9). `TODO.md` updated, "Next Session" pointed at WBS 16.0 (Integration Testing against synthetic data). Caveat: verified via build/lint/test only — no browser-based UI testing performed for the new error banners.

---

### Session 26: Pending Applications List Rework & Auto-TTB-ID Ingestion, Diacritic/Glare/Importer Comparison Fixes, and DevLog §7 Regulatory Reference (Mandatory Elements, Brand-Name Fallback, Field of Vision, ABV Phrasing)

**Context:** With WBS 1.0-15.0 all complete, this session was a mixed refinement pass driven by Gabe's review of the running application against real data: a Pending Applications List rework surfacing registry-style fields, a simplification of the upload/ingestion flow, two comparison-engine bugs found via real label data (diacritics, glare-suppression eating legible label backgrounds, importer-vs-bottler matching), and — at Gabe's explicit request, citing a dense block of 27 CFR sections — a new DevLog §7 documenting mandatory-label-element requirements plus three new/refined comparison-engine rules implementing them.

**Completed — Pending Applications List rework (refinements within WBS 4.0/5.0/12.0, no new line items):**
- `app/models/application.py`: added `permit_no` (Item 2) and `fanciful_name` (Item 7) columns.
- `app/services/form_extraction.py::persist_form_parameters`: now populates `permit_no`, `fanciful_name`, and `ttb_id` (from `application_type.prior_ttb_id`) during Stage 3.
- `app/services/pipeline.py`: new `_resolve_label_field()` / `_update_registry_fields()`, called from `run_stages_5_6()` on every process/reprocess path, populating `class_type_code` (from the label's `class_type_designation`) and `origin_code` (US state for domestic via `_extract_state`, or the label's `country_of_origin` for imported) as soon as processing completes.
- `app/db.py`: new `_add_missing_columns()` lightweight SQLite `ALTER TABLE` migration, run from `init_db()`.
- New `DELETE /applications` endpoint (`application_service.delete_all_applications()`), cascading through `comparisons`/`determinations`/`label_parameters`/`form_parameters`/`label_images`/`applications`/`batches` plus removing uploaded files on disk.
- Frontend: `DashboardPage.tsx` reworked to 10 columns (TTB ID, Permit No., Serial Number, Upload Date, Completed Date, Fanciful Name, Brand Name, Origin Desc, Class/Type Desc, Status) with a merged Status column (finalized badge → batch-result badge → raw status) and a `formatDate()` helper; `SettingsDialog.tsx` gained a "Danger Zone" section with a two-step-confirm "Delete All Applications" button.
- Verification: backend 204/204 pytest, frontend build/lint clean, 30/30 Vitest.

**Completed — Ingestion stage update (refinements within WBS 4.0/5.0/12.0):**
- Upload modal no longer asks for Applicant Name / Serial Number — these now come from Stage 3 form extraction.
- `POST /applications/upload` now runs Stage 3 immediately (`pipeline.process_new_upload`), so the Pending Applications list is populated right away with TTB ID, Permit No., Serial Number, names, and origin.
- New `_next_ttb_id`: auto-assigns a 14-digit TTB ID (year + Julian day + "001" + daily sequence) when the form doesn't already have one, applied uniformly across upload, reprocess, and full pipeline runs.
- All 10 Dashboard columns are now sortable (asc/desc toggle via a new `SortableHead`); the filter input is now a global client-side filter matching any column (TTB ID, permit/serial numbers, names, origin/class-type, status, dates).
- Verification: backend 206/206 pytest (+3 new TTB-ID auto-assignment tests; fixed a byte-offset bug in the upload test's TTB-ID method-code assertion, `ttb_id[5:8]` not `[8:11]`); frontend 32/32 Vitest, lint clean, build succeeds.

**Completed — Comparison-engine fixes from real-label review (refinements within 6.1/6.8/7.2/7.9/7.10):**
- **Diacritics (fanciful name HARD_FAILURE → MATCH):** `_normalize_for_comparison()` in `label_extraction.py` now folds diacritics via Unicode NFKD decomposition before lowercasing/whitespace-collapsing, so "Fete Rose" (form) and "Fête Rosé" (label) normalize to the same string. Previously `_strip_punctuation` dropped the accented characters entirely, producing two different strings ("fteros" vs "feterose") and a HARD_FAILURE. Benefits every text comparison (brand name, fanciful name, applicant name/address, OCR fuzzy-matching).
- **`suppress_glare` area-fraction cap (FR-039, 6.1):** new `MAX_GLARE_AREA_FRACTION = 0.05` — real photographic glare is a small, localized hot-spot, but most labels have a plain white/light background that also reads as ≥235; inpainting over that destroys legible text. `suppress_glare()` now skips inpainting entirely when the ≥235 mask covers more than 5% of the image.
- **Importer-vs-bottler matching for Item 8 (FR-102/103, 7.9/7.10):** new `_applicant_label_field()` — for `application.source == "imported"`, Applicant Name/Address (Item 8) is now compared only against the label's `importer_name`/`importer_address`, never the foreign `bottler_name`/`bottler_address`. Previously both fields were pooled and `resolve_multi_image` picked whichever had higher OCR/Vision confidence when neither matched exactly, which is why "Niche Import Co." was being compared against "WEINKELLEREI LENZ MOSER AG" (the Austrian bottler, 0.98 confidence) instead of "Niche W. & S." (the actual importer, 0.95 confidence). After the fix, `applicant_name` correctly compares against the importer (still HARD_FAILURE on text content, but now comparing the right two values); `applicant_address` was already resolving correctly by luck of confidence ordering and is now correct by design. **This resolves the open product question from Session 22's §4 Note 8** — Item 8 is now defined to match the importer for imported products.
- 4 new tests (diacritic match, import-vs-bottler confidence tiebreak for name + address, missing-importer fallback). Full suite: 211/211 passed.

**Completed — DevLog §7 Regulatory Reference & new comparison rules** (per Gabe's direct citation of 27 CFR §§1.A.5.64, 1.A.7.63(a), 1.A.4.32(a)/(b), 1.A.5.63(a)/(b)/5.7, 4.38, 5.63(a), 7.63(a), 5.65/7.65/4.36):
- New `_DevLog/DevLog.md` §7 (5 subsections, ~70 lines, plus a TOC entry): documents the §1.A.5.64 brand-name fallback, mandatory-label-element tables per product type (malt/wine/spirits) with a coverage/gap analysis against the existing comparison rules, the "same field of vision" requirement (Brand Name/Class-Type/ABV must share a label panel), and the four ABV-approved-phrasing formats.
- `compare_brand_name` (7.2) now falls back to the bottler/importer name-and-address statement when no `brand_name` is found on the label (27 CFR §1.A.5.64 and analogues) — via new `_brand_name_fallback_matches()` helper reusing `_applicant_label_field()`. **Live-verified against application #1 (Woodford Reserve)**: `brand_name` now resolves MATCH ("Woodford Reserve" found within "THE WOODFORD RESERVE DISTILLERY") instead of HARD_FAILURE — exactly the scenario Gabe described.
- `compare_abv` (7.13) now validates ABV phrasing against the four approved formats of 27 CFR §§5.65/7.65/4.36 ("X% Alcohol by Volume", "X% alc/vol", "Alc. X percent by vol.", "Alc X% by vol") via new `ABV_APPROVED_PHRASING_RE` + `_abv_phrasing_ok()`; a numerically-correct value in non-conforming phrasing now downgrades to POSSIBLE_ALLOWABLE (Sec. V item 3b) instead of silently passing MATCH. Also fixed `_extract_abv`'s regex to recognize "X percent" in addition to "X%" — a real bug caught by the new parametrized phrasing test.
- New rule `compare_field_of_vision` checks that Brand Name, Class/Type, and ABV co-occur on at least one label image (27 CFR §§4.38/5.63(a)/7.63(a)) — MATCH if they share an image, POSSIBLE_ALLOWABLE (no Section V ref) if each is present individually but never together, and silent (`None`) if any element is missing entirely (already covered by existing hard-failure rules). Added to `COMPARISON_RULES`.
- New `label_field_of_vision` entry in `FIELD_LABELS` (`determination_engine.py` + `web/src/lib/field-labels.ts`); `ParameterResultsTable.tsx` and `field-mappings.ts` confirmed to need no changes (generic rendering / graceful fallback for unmapped field names).
- 11 new tests (3 brand-name fallback, 1 parametrized ×4 ABV phrasings + 1 non-conforming-phrasing, 3 field-of-vision) — full suite **222/222 backend passing**, **32/32 frontend passing**, lint clean.
- Deliberately did **not** add new PRD.md FR-108/109/110 entries or a new WBS 7.x sub-item for `compare_field_of_vision`, to stay within the explicit scope of "append to DevLog + implement in comparisons" — flagged as an optional follow-up if formal traceability is desired.

**Outcome:** Dashboard now surfaces TTB ID/Permit No./Fanciful Name/registry fields with sortable/filterable columns and a Delete-All admin action; uploads auto-run Stage 3 and auto-assign TTB IDs; three real-data comparison bugs fixed (diacritics, glare-suppression over-eager on light backgrounds, importer-vs-bottler for Item 8 — closing §4 Note 8); new DevLog §7 plus three new/refined comparison rules implementing 27 CFR §§1.A.5.64, 4.38/5.63(a)/7.63(a), and 5.65/7.65/4.36. Backend 222/222 pytest, frontend 32/32 Vitest, lint clean. No new WBS line items — refinements within already-complete 4.0/5.0/6.1/6.8/7.2/7.9/7.10/7.13/12.0; `WBS.md` → v2.7 (new §4 Note 10). `TODO.md` updated. Note: application #1's `alcohol_content`/`net_contents` are still `null` from before the `suppress_glare` fix, so `compare_field_of_vision` returns `None` for it until it is reprocessed.

---

**TTB Label Verification System**
*Copyright (c) 2026 Matthew Gabriel Sizemore · Assessment submission: IT Specialist (AI) · 26-DO-12891471-DH*
