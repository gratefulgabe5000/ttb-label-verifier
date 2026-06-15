"""Quick ad-hoc inspector: print non-MATCH/NOT_APPLICABLE comparison rows for a list of app ids."""
import sys
import httpx

BASE_URL = "http://localhost:8000"

with httpx.Client(timeout=30.0) as client:
    token = client.post(
        f"{BASE_URL}/auth/login",
        json={"username": "agent1", "password": "password123"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for app_id in [int(a) for a in sys.argv[1:]]:
        comps = client.get(f"{BASE_URL}/applications/{app_id}/comparisons", headers=headers).json()
        print(f"\n=== App {app_id} ===")
        for c in comps:
            if c["result"] in ("MATCH", "NOT_APPLICABLE"):
                continue
            print(f"  [{c['result']}] {c['field_name']}")
            print(f"      form_value:  {c['form_value']!r}")
            print(f"      label_value: {c['label_value']!r}")
            print(f"      section_v_ref: {c['section_v_ref']!r}")
            print(f"      note: {c['note']!r}")
