"""WBS 16.0 -- Integration Testing (Synthetic Data, Localhost Backend).

Drives the 18 synthetic test sets (test_sets.json), the Tier 1/2/3 form
extraction fixtures (forms/sample_creek_*.pdf), and a degraded label image
(degraded/woodford_front_combined.jpg) through the live local backend over
HTTP, exercising:

  - 16.1 End-to-end pipeline per product type (wine/spirits/malt)
  - 16.2 PR-001 timing (<=5s per application, including all label images)
  - 16.3 Bounded-concurrency batch processing (A-07, DEFAULT_BATCH_CONCURRENCY=4)
  - 16.4 Multi-image field resolution (FR-038/A-10)
  - 16.5 Override + finalize flow (FR-086-090, A-15 -- no AI re-run)
  - 16.6 Annotation placement (bbox_json vs location_hint, A-05)

Requires:
  - Backend running on http://localhost:8000 (uvicorn main:app --reload)
  - ANTHROPIC_API_KEY already configured in the backend process via the
    Settings panel -- this script never reads, sets, or transmits the key.

Run with the backend's venv (httpx is a backend dependency):
    app/.venv/Scripts/python.exe testdata/run_integration_tests.py

Writes testdata/integration_results.json and prints a summary to stdout.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

BASE_URL = "http://localhost:8000"
USERNAME = "agent1"
PASSWORD = "password123"
TESTDATA = Path(__file__).resolve().parent
RESULTS_PATH = TESTDATA / "integration_results.json"

TIMEOUT = httpx.Timeout(120.0)


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def login(client: httpx.Client) -> str:
    resp = client.post(f"{BASE_URL}/auth/login", json={"username": USERNAME, "password": PASSWORD})
    resp.raise_for_status()
    return resp.json()["access_token"]


def upload(client: httpx.Client, token: str, form_pdf: Path, label_images: list[tuple[Path, str]]) -> dict:
    files = [("form_file", (form_pdf.name, form_pdf.read_bytes(), "application/pdf"))]
    label_types = []
    for path, label_type in label_images:
        files.append(("label_images", (path.name, path.read_bytes(), "image/jpeg")))
        label_types.append(label_type)
    data = {"label_types": label_types} if label_types else None
    resp = client.post(f"{BASE_URL}/applications/upload", headers=auth_headers(token), files=files, data=data)
    resp.raise_for_status()
    return resp.json()


def process(client: httpx.Client, token: str, app_id: int) -> tuple[dict, float]:
    start = time.perf_counter()
    resp = client.post(f"{BASE_URL}/applications/{app_id}/process", headers=auth_headers(token), timeout=TIMEOUT)
    elapsed = time.perf_counter() - start
    resp.raise_for_status()
    return resp.json(), elapsed


def get_detail(client: httpx.Client, token: str, app_id: int) -> dict:
    resp = client.get(f"{BASE_URL}/applications/{app_id}", headers=auth_headers(token), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_comparisons(client: httpx.Client, token: str, app_id: int) -> list[dict]:
    resp = client.get(f"{BASE_URL}/applications/{app_id}/comparisons", headers=auth_headers(token), timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Phase A -- 16.1 / 16.2: all 18 synthetic sets through Stage 3-6
# ---------------------------------------------------------------------------


def phase_a(client: httpx.Client, token: str, sets: list[dict]) -> dict:
    results = {}
    for s in sets:
        set_id = s["set_id"]
        form_path = TESTDATA / s["form_pdf"]
        label_specs = [(TESTDATA / li["filename"], li.get("label_type") or "other") for li in s.get("label_images", [])]
        try:
            uploaded = upload(client, token, form_path, label_specs)
            app_id = uploaded["id"]
            detail, elapsed = process(client, token, app_id)
        except httpx.HTTPStatusError as exc:
            print(f"  [ERR ] {set_id:35} HTTP error: {exc}")
            results[set_id] = {"error": str(exc)}
            continue

        actual = detail.get("recommendation")
        expected = s["expected_outcome"]
        ok = actual == expected
        pr001_ok = elapsed <= 5.0
        results[set_id] = {
            "app_id": app_id,
            "expected": expected,
            "actual": actual,
            "outcome_match": ok,
            "elapsed_s": round(elapsed, 2),
            "pr001_pass": pr001_ok,
            "application_status": detail.get("status"),
        }
        mark = "PASS" if ok else "FAIL"
        timing = "OK  " if pr001_ok else "SLOW"
        print(f"  [{mark}] {set_id:35} expected={expected:28} actual={str(actual):28} {elapsed:5.2f}s [{timing}]")
    return results


# ---------------------------------------------------------------------------
# Phase B -- 16.4: multi-image field resolution
# ---------------------------------------------------------------------------


def phase_b_multiimage(client: httpx.Client, token: str, a_results: dict) -> dict:
    entry = a_results.get("good_spirits_woodford", {})
    if "app_id" not in entry:
        print("  SKIP: good_spirits_woodford not available from Phase A")
        return {}

    app_id = entry["app_id"]
    detail = get_detail(client, token, app_id)
    images = {img["id"]: img for img in detail["label_images"]}
    comps = get_comparisons(client, token, app_id)

    findings = []
    for c in comps:
        if c["result"] == "MATCH" and c.get("label_image_id"):
            img = images.get(c["label_image_id"])
            findings.append(
                {
                    "field_name": c["field_name"],
                    "result": c["result"],
                    "resolved_from_label_type": img["label_type"] if img else None,
                    "resolved_from_image": Path(img["image_path"]).name if img and img["image_path"] else None,
                }
            )

    back_resolved = [f["field_name"] for f in findings if f["resolved_from_label_type"] == "back"]
    distinct_images = {f["resolved_from_image"] for f in findings}

    print(f"  good_spirits_woodford (app {app_id}): {len(findings)} MATCH fields with image attribution")
    for f in findings:
        print(f"    {f['field_name']:28} <- {f['resolved_from_label_type']:6} ({f['resolved_from_image']})")
    print(f"  Fields resolved from the BACK label: {back_resolved}")
    print(f"  Multi-image resolution exercised: {len(distinct_images) > 1} ({len(distinct_images)} distinct source images)")

    return {
        "app_id": app_id,
        "findings": findings,
        "back_resolved_fields": back_resolved,
        "multi_image_resolution_exercised": len(distinct_images) > 1,
    }


# ---------------------------------------------------------------------------
# Phase C -- 16.3: bounded-concurrency batch (DEFAULT_BATCH_CONCURRENCY=4)
# ---------------------------------------------------------------------------


def phase_c_batch(client: httpx.Client, token: str, a_results: dict) -> dict:
    candidate_set_ids = [
        "good_spirits_woodford",
        "good_wine_lenzmoser",
        "good_malt_barrilito",
        "hf_fancifulname_woodford",
        "hf_countryoforigin_woodford",
        "ar_brandname_fortemasso",
    ]
    candidate_ids = [a_results[s]["app_id"] for s in candidate_set_ids if "app_id" in a_results.get(s, {})]

    start = time.perf_counter()
    resp = client.post(
        f"{BASE_URL}/batch/process", headers=auth_headers(token), json={"application_ids": candidate_ids}, timeout=300
    )
    elapsed = time.perf_counter() - start
    resp.raise_for_status()
    status_data = resp.json()
    batch_id = status_data["id"]

    report = client.get(f"{BASE_URL}/batch/{batch_id}/report", headers=auth_headers(token), timeout=TIMEOUT).json()

    naive_sequential_estimate = len(candidate_ids) * 5.0
    print(f"  Batch {batch_id}: {len(candidate_ids)} applications, DEFAULT_BATCH_CONCURRENCY=4")
    print(f"  Total wall time: {elapsed:.2f}s  (naive sequential @5s/app would be ~{naive_sequential_estimate:.0f}s)")
    print(f"  status={status_data['status']} completed={status_data['completed']}/{status_data['total']}")
    print(
        f"  approved={status_data['approved_count']} denied={status_data['denied_count']} "
        f"exemption={status_data['exemption_count']}"
    )
    print(f"  most_common_failure={report.get('most_common_failure')}")
    for app_row in status_data["applications"]:
        print(f"    app {app_row['id']:4} -> status={app_row['status']:12} recommendation={app_row['recommendation']}")

    return {
        "batch_id": batch_id,
        "application_ids": candidate_ids,
        "elapsed_s": round(elapsed, 2),
        "naive_sequential_estimate_s": naive_sequential_estimate,
        "status": status_data,
        "report": report,
    }


# ---------------------------------------------------------------------------
# Phase D -- 16.5: override + finalize (FR-086-090, A-15)
# ---------------------------------------------------------------------------


def phase_d_override(client: httpx.Client, token: str, a_results: dict) -> dict:
    entry = a_results.get("hf_brandname_woodford", {})
    if "app_id" not in entry:
        print("  SKIP: hf_brandname_woodford not available from Phase A")
        return {}

    app_id = entry["app_id"]
    before = get_detail(client, token, app_id)
    determination_id = before["determination"]["id"]
    processed_at_before = before["processed_at"]
    recommendation_before = before["recommendation"]

    # Per-parameter override (FR-086-088): brand_name HARD_FAILURE -> MATCH
    r1 = client.post(
        f"{BASE_URL}/determinations/{determination_id}/override",
        headers=auth_headers(token),
        json={
            "field": "brand_name",
            "override_value": "MATCH",
            "reason": "WBS 16.5 integration test: agent reviewed and confirms brand name is acceptable.",
        },
    )
    r1.raise_for_status()
    field_override = r1.json()

    # Overall determination override (FR-089): DENY -> APPROVE
    r2 = client.post(
        f"{BASE_URL}/determinations/{determination_id}/override",
        headers=auth_headers(token),
        json={
            "field": None,
            "override_value": "APPROVE",
            "reason": "WBS 16.5 integration test: overall recommendation overridden after field-level review.",
        },
    )
    r2.raise_for_status()
    overall_override = r2.json()

    # Finalize (FR-090/A-15) -- must not re-run the AI pipeline
    r3 = client.post(f"{BASE_URL}/determinations/{determination_id}/finalize", headers=auth_headers(token))
    r3.raise_for_status()
    finalized = r3.json()

    after = get_detail(client, token, app_id)
    no_ai_rerun = after["processed_at"] == processed_at_before

    print(f"  Application {app_id} (hf_brandname_woodford), determination {determination_id}")
    print(f"  Before:  recommendation={recommendation_before}")
    print(f"  Field override (brand_name): {field_override['original_value']} -> {field_override['override_value']}")
    print(f"  Overall override: -> {overall_override['override_value']}")
    print(f"  Finalized at: {finalized['finalized_at']}")
    print(f"  After:   recommendation={after['recommendation']}  status={after['status']}")
    print(f"  A-15 check (processed_at unchanged, no AI re-run): {no_ai_rerun}")

    return {
        "app_id": app_id,
        "determination_id": determination_id,
        "recommendation_before": recommendation_before,
        "recommendation_after": after["recommendation"],
        "status_after": after["status"],
        "field_override": field_override,
        "overall_override": overall_override,
        "finalized_at": finalized["finalized_at"],
        "no_ai_rerun": no_ai_rerun,
    }


# ---------------------------------------------------------------------------
# Phase E -- 16.6: annotation placement (bbox_json vs location_hint, A-05)
# ---------------------------------------------------------------------------


def phase_e_annotation(client: httpx.Client, token: str) -> dict:
    results: dict = {"tiers": {}, "degraded": {}}

    tier_forms = {
        "sample_creek_acroform.pdf": "acroform",
        "sample_creek_flattened.pdf": "pdftext",
        "sample_creek_scanned.pdf": "ai_vision",
    }
    for filename, expected_method in tier_forms.items():
        form_path = TESTDATA / "forms" / filename
        uploaded = upload(client, token, form_path, [])
        app_id = uploaded["id"]
        detail, elapsed = process(client, token, app_id)

        methods: dict = {}
        for fp in detail["form_parameters"]:
            method = fp["extraction_method"]
            stats = methods.setdefault(method, {"count": 0, "bbox": 0, "hint": 0})
            stats["count"] += 1
            if fp["bbox_json"]:
                stats["bbox"] += 1
            if fp["location_hint"]:
                stats["hint"] += 1

        dominant = max(methods.items(), key=lambda kv: kv[1]["count"])[0] if methods else None
        print(f"  {filename:30} app={app_id} elapsed={elapsed:.2f}s  dominant_method={dominant} (expected~{expected_method})")
        for method, stats in methods.items():
            print(f"      method={str(method):10} fields={stats['count']:3}  bbox_json={stats['bbox']:3}  location_hint={stats['hint']:3}")

        results["tiers"][filename] = {
            "app_id": app_id,
            "elapsed_s": round(elapsed, 2),
            "expected_method": expected_method,
            "dominant_method": dominant,
            "methods": methods,
        }

    # Degraded label image -- annotation fallback (FR-039/FR-040/A-05)
    degraded_path = TESTDATA / "degraded" / "woodford_front_combined.jpg"
    form_path = TESTDATA / "forms" / "good_spirits_woodford.pdf"
    uploaded = upload(client, token, form_path, [(degraded_path, "brand")])
    app_id = uploaded["id"]
    detail, elapsed = process(client, token, app_id)

    lp_stats = {"count": 0, "bbox": 0, "hint": 0, "neither": 0}
    for lp in detail["label_parameters"]:
        lp_stats["count"] += 1
        if lp["bbox_json"]:
            lp_stats["bbox"] += 1
        if lp["location_hint"]:
            lp_stats["hint"] += 1
        if not lp["bbox_json"] and not lp["location_hint"]:
            lp_stats["neither"] += 1

    print(f"  woodford_front_combined.jpg (degraded) app={app_id} elapsed={elapsed:.2f}s")
    print(
        f"      label_parameters={lp_stats['count']}  bbox_json={lp_stats['bbox']}  "
        f"location_hint={lp_stats['hint']}  neither={lp_stats['neither']}"
    )

    results["degraded"]["woodford_front_combined"] = {
        "app_id": app_id,
        "elapsed_s": round(elapsed, 2),
        "stats": lp_stats,
    }
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    with httpx.Client(timeout=TIMEOUT) as client:
        token = login(client)
        sets = json.loads((TESTDATA / "test_sets.json").read_text(encoding="utf-8"))["sets"]

        print("=== Phase A: WBS 16.1/16.2 -- 18 synthetic sets through Stage 3-6 ===", flush=True)
        a_results = phase_a(client, token, sets)

        print("\n=== Phase B: WBS 16.4 -- multi-image field resolution ===", flush=True)
        b_results = phase_b_multiimage(client, token, a_results)

        print("\n=== Phase C: WBS 16.3 -- bounded-concurrency batch ===", flush=True)
        c_results = phase_c_batch(client, token, a_results)

        print("\n=== Phase D: WBS 16.5 -- override + finalize ===", flush=True)
        d_results = phase_d_override(client, token, a_results)

        print("\n=== Phase E: WBS 16.6 -- annotation placement ===", flush=True)
        e_results = phase_e_annotation(client, token)

        all_results = {
            "phase_a": a_results,
            "phase_b": b_results,
            "phase_c": c_results,
            "phase_d": d_results,
            "phase_e": e_results,
        }
        RESULTS_PATH.write_text(json.dumps(all_results, indent=2, default=str), encoding="utf-8")

        total = len(a_results)
        passed = sum(1 for r in a_results.values() if r.get("outcome_match"))
        slow = [sid for sid, r in a_results.items() if r.get("pr001_pass") is False]
        print("\n=== Summary ===")
        print(f"Phase A outcome match: {passed}/{total}")
        print(f"PR-001 violations (>5s): {slow or 'none'}")
        print(f"Results written to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
