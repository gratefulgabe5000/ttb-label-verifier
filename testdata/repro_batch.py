"""WBS 16.3 repro: POST /batch/process with 6 existing applications (apps 6-23)
to investigate the httpx.ReadError [WinError 10054] reported during a prior
Phase C run of run_integration_tests.py. Reuses already-uploaded apps instead
of re-running Phase A (which would create 18 new applications)."""
import json
import time

import httpx

BASE_URL = "http://localhost:8000"
APP_IDS = [6, 7, 8, 10, 11, 21]

with httpx.Client(timeout=300.0, base_url=BASE_URL) as client:
    token = client.post("/auth/login", json={"username": "agent1", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    print(f"POSTing /batch/process with application_ids={APP_IDS}")
    start = time.perf_counter()
    try:
        resp = client.post("/batch/process", headers=headers, json={"application_ids": APP_IDS})
        elapsed = time.perf_counter() - start
        print(f"status={resp.status_code} elapsed={elapsed:.2f}s")
        print(json.dumps(resp.json(), indent=2)[:3000])
    except Exception as exc:
        elapsed = time.perf_counter() - start
        print(f"EXCEPTION after {elapsed:.2f}s: {type(exc).__name__}: {exc}")
        raise
