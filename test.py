"""
Aether — End-to-End Smoke Test
------------------------------------------------
Exercises the full user journey against a running Flask server:
  create user -> birth details -> janampatri -> chat -> recommendations
  -> experts -> booking -> journal -> dashboard

Usage:
    1. Start the app in one terminal:  python app.py
    2. In another terminal:            python smoke_test.py

Requires `requests` (pip install requests).
"""

import sys
import requests

BASE = "http://127.0.0.1:5000"
FAILURES = []


def check(label, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    if not condition:
        FAILURES.append(label)


def main():
    session = requests.Session()

    # 1. Create user
    r = session.post(f"{BASE}/api/users", json={
        "name": "Smoke Test",
        "email": f"smoketest+{__import__('time').time()}@example.com",
        "gender": "other",
    })
    check("create user", r.status_code in (200, 201), r.text)
    user = r.json()
    user_id = user.get("id")
    check("user has id", bool(user_id))

    # 2. Birth details -> triggers janampatri generation
    r = session.post(f"{BASE}/api/users/{user_id}/birth-details", json={
        "date_of_birth": "1996-06-21",
        "time_of_birth": "09:15",
        "place_of_birth": "Delhi, India",
    })
    check("submit birth details", r.status_code == 201, r.text)

    # 3. Fetch janampatri, confirm planets are NOT all identical
    r = session.get(f"{BASE}/api/users/{user_id}/janampatri")
    check("fetch janampatri", r.status_code == 200, r.text)
    chart = r.json()
    signs = [p["sign"] for p in chart.get("planetary_positions", [])]
    check("janampatri has 9 planets", len(signs) == 9, f"got {len(signs)}")
    check("planet signs are not all identical", len(set(signs)) > 1, f"signs: {signs}")

    # 4. Start chat
    r = session.post(f"{BASE}/api/chat/start", json={"user_id": user_id})
    check("start chat", r.status_code == 201, r.text)
    chat_data = r.json()
    session_id = chat_data.get("session_id")
    check("chat has session_id", bool(session_id))

    # 5. Send messages until ready_for_analysis or a safety cap
    ready = chat_data.get("ready_for_analysis", False)
    turns = 0
    while not ready and turns < 15:
        r = session.post(f"{BASE}/api/chat/message", json={
            "user_id": user_id,
            "session_id": session_id,
            "content": "Work has felt heavy lately and I haven't been sleeping well.",
        })
        check(f"chat message turn {turns + 1}", r.status_code == 201, r.text)
        ready = r.json().get("ready_for_analysis", False)
        turns += 1
    check("chat reached ready_for_analysis", ready, f"after {turns} turns")

    # 6. Chat history
    r = session.get(f"{BASE}/api/chat/{session_id}/history")
    check("fetch chat history", r.status_code == 200 and len(r.json()) > 0, r.text)

    # 7. Generate recommendations
    r = session.post(f"{BASE}/api/recommendations/generate", json={
        "user_id": user_id,
        "session_id": session_id,
    })
    check("generate recommendations", r.status_code == 201, r.text)
    recs = r.json()
    check("recommendations non-empty", len(recs) > 0, f"got {len(recs)}")

    # 8. Save first recommendation
    if recs:
        rec_id = recs[0]["id"]
        r = session.post(f"{BASE}/api/recommendations/{rec_id}/save")
        check("toggle save recommendation", r.status_code == 200, r.text)

    # 9. List experts
    r = session.get(f"{BASE}/api/experts")
    check("list experts", r.status_code == 200 and len(r.json()) > 0, r.text)
    experts = r.json()

    # 10. Book an expert
    if experts:
        expert_id = experts[0]["id"]
        r = session.post(f"{BASE}/api/experts/{expert_id}/book", json={
            "user_id": user_id,
            "session_datetime": "2026-08-01 10:00",
        })
        check("book expert", r.status_code == 201, r.text)

    # 11. Journal entry
    r = session.post(f"{BASE}/api/journal", json={
        "user_id": user_id,
        "content": "Feeling reflective after that conversation.",
        "mood": "calm",
    })
    check("create journal entry", r.status_code == 201, r.text)

    # 12. Dashboard aggregation
    r = session.get(f"{BASE}/api/users/{user_id}/dashboard")
    check("fetch dashboard", r.status_code == 200, r.text)
    dash = r.json()
    check("dashboard shows janampatri ready", dash.get("has_janampatri") is True)
    check("dashboard shows saved recommendation", len(dash.get("saved_recommendations", [])) > 0)
    check("dashboard shows upcoming booking", len(dash.get("upcoming_bookings", [])) > 0)

    # --- Summary ---
    print("\n" + "=" * 50)
    if FAILURES:
        print(f"{len(FAILURES)} CHECK(S) FAILED:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED ✔")
        sys.exit(0)


if __name__ == "__main__":
    main()