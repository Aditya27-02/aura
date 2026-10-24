"""Integration tests for the AURA API — complete learning loop coverage."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["engine"] == "AURA"


def test_domains():
    r = client.get("/api/domains")
    assert r.status_code == 200
    names = [d["name"] for d in r.json()["domains"]]
    assert "DSA" in names
    assert "Biology" in names


def test_invalid_domain():
    r = client.post("/api/session/start", json={"domain": "nonexistent"})
    assert r.status_code == 400


def test_session_not_found():
    r = client.get("/api/session/fake-id/state")
    assert r.status_code == 404


def test_complete_dsa_loop():
    r = client.post("/api/session/start", json={"domain": "DSA"})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    assert r.json()["seeded_events"] == 2

    r = client.get(f"/api/session/{sid}/state")
    assert r.status_code == 200
    concepts = r.json()["concepts"]
    assert "binary_search" in concepts

    r = client.post(f"/api/session/{sid}/observe", json={
        "evidence": {
            "timestamp": "2026-08-17T22:10:00+05:30",
            "concept": "binary_search",
            "secondary_concepts": ["boundary_handling"],
            "test_results": {"passed": ["normal_asc", "normal_desc"], "failed": ["left_boundary", "single_element"]},
            "failure_classes": ["left_boundary", "single_element"],
            "static_pattern": "low_mid_no_increment",
            "recurrence": True,
            "code": "while low < high:\n    mid = (low + high) // 2\n    if arr[mid] < target:\n        low = mid\n    else:\n        high = mid",
        }
    })
    assert r.status_code == 200

    r = client.get(f"/api/session/{sid}/diagnose")
    assert r.status_code == 200
    snap = r.json()
    assert "entropy" in snap
    assert len(snap["hypotheses"]) > 0

    q = snap.get("selected_question")
    if q:
        q_id = q["id"]
        r = client.post(f"/api/session/{sid}/answer", json={
            "question_id": q_id,
            "option_index": 2,
        })
        assert r.status_code == 200

    r = client.post(f"/api/session/{sid}/decide")
    assert r.status_code == 200

    r = client.get(f"/api/session/{sid}/retrieve", params={"target": "binary_search", "query": "boundary interval shrink"})
    assert r.status_code == 200

    r = client.post(f"/api/session/{sid}/teach", json={"target": "binary_search"})
    assert r.status_code == 200

    r = client.post(f"/api/session/{sid}/verify-transfer", json={"passed": True, "note": "all transfer tests passed"})
    assert r.status_code == 200
    vr = r.json()
    assert vr["gap"]["transfer_verified"] is True

    r = client.get(f"/api/session/{sid}/map")
    assert r.status_code == 200

    r = client.get(f"/api/session/{sid}/privacy")
    assert r.status_code == 200

    r = client.post(f"/api/session/{sid}/close")
    assert r.status_code == 200


def test_complete_biology_loop():
    r = client.post("/api/session/start", json={"domain": "Biology"})
    assert r.status_code == 200
    sid = r.json()["session_id"]

    r = client.post(f"/api/session/{sid}/observe", json={
        "evidence": {
            "timestamp": "2026-08-17T13:00:00+05:30",
            "concept": "golgi",
            "secondary_concepts": ["rough_er"],
            "question_id": "scan_42",
            "selected_option": 1,
            "correct_option": 0,
            "distractor_pattern": "attributed_packaging_to_rer",
            "recurrence": True,
            "input_mode": "voice",
        }
    })
    assert r.status_code == 200

    r = client.get(f"/api/session/{sid}/diagnose")
    assert r.status_code == 200
    snap = r.json()

    q = snap.get("selected_question")
    if q:
        r = client.post(f"/api/session/{sid}/answer", json={
            "question_id": q["id"],
            "option_index": 1,
        })
        assert r.status_code == 200

    r = client.post(f"/api/session/{sid}/decide")
    assert r.status_code == 200

    r = client.get(f"/api/session/{sid}/retrieve", params={"target": "golgi", "query": "golgi packaging proteins"})
    assert r.status_code == 200

    r = client.post(f"/api/session/{sid}/teach", json={"target": "golgi"})
    assert r.status_code == 200

    r = client.post(f"/api/session/{sid}/verify-transfer", json={"passed": True})
    assert r.status_code == 200

    r = client.post(f"/api/session/{sid}/close")
    assert r.status_code == 200
