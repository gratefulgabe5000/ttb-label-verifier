"""Re-sweep apps 6-23 against test_sets.json expected_outcome, post B1-B7/FR-106 fixes."""
import json

import httpx

BASE_URL = "http://localhost:8000"

data = json.load(open("testdata/test_sets.json", encoding="utf-8"))
sets = data["sets"]

with httpx.Client(timeout=30.0, base_url=BASE_URL) as client:
    token = client.post("/auth/login", json={"username": "agent1", "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    fails = []
    for i, ts in enumerate(sets):
        app_id = i + 6
        expected = ts["expected_outcome"]
        d = client.get(f"/applications/{app_id}", headers=headers).json()
        actual = d.get("recommendation")
        det = d.get("determination") or {}
        det_rec = det.get("recommendation")
        status = "PASS" if actual == expected else "FAIL"
        if status == "FAIL":
            fails.append((app_id, ts["set_id"], expected, actual, det_rec))
        print(f"app{app_id:>2} {ts['set_id']:<32} expected={expected:<26} actual={actual!s:<26} det={det_rec}  {status}")

    print(f"\n{len(sets) - len(fails)}/{len(sets)} PASS")
    if fails:
        print("\nFAILURES:")
        for app_id, set_id, expected, actual, det_rec in fails:
            print(f"  app{app_id} ({set_id}): expected={expected}, actual={actual}, determination.recommendation={det_rec}")
