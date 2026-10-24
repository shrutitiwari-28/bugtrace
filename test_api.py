from fastapi.testclient import TestClient
import api

client = TestClient(api.app)

OK_TEST = """
from calculator import f

def test_x():
    assert f() == 1
"""


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_home_serves_ui():
    response = client.get("/")
    assert response.status_code == 200
    assert "BugTrace" in response.text


def test_static_files():
    response = client.get("/web/app.js")
    assert response.status_code == 200


def test_repair_rejects_bad_test():
    response = client.post("/repair", json={
        "source": "def f():\n    return 1\n",
        "approved_test": "def test_x(:\n",
        "error_output": "e",
    })
    assert response.status_code == 400


def test_repair_rejects_bad_source():
    response = client.post("/repair", json={
        "source": "def f(:\n",
        "approved_test": OK_TEST,
        "error_output": "e",
    })
    assert response.status_code == 400


def test_rejects_bad_module_name():
    response = client.post("/repair", json={
        "source": "x = 1\n",
        "approved_test": OK_TEST,
        "error_output": "e",
        "module": "1bad",
    })
    assert response.status_code == 400


def test_rejects_oversized_input():
    response = client.post("/investigate", json={
        "source": "x" * 60000,
        "error_output": "e",
        "expected_behavior": "b",
    })
    assert response.status_code == 422


def test_repair_returns_attempts(monkeypatch):
    fake = {
        "status": "VERIFIED",
        "attempts": [{
            "attempt": 1,
            "status": "VERIFIED",
            "stage": "reproduction",
            "message": "ok",
            "patch": "x = 1\n",
            "details": None,
        }],
    }

    monkeypatch.setattr(api, "repair", lambda *args, **kwargs: fake)

    response = client.post("/repair", json={
        "source": "x = 0\n",
        "approved_test": OK_TEST,
        "error_output": "e",
    })

    assert response.status_code == 200
    assert response.json()["status"] == "VERIFIED"


def test_verify_returns_attempt(monkeypatch):
    monkeypatch.setattr(api, "run_pipeline", lambda *a, **k: {
        "status": "FAILED", "stage": "audit", "message": "m", "details": {"output": "x"}})
    r = client.post("/verify", json={
        "source": "x = 0\n",
        "patched_source": "x = 1\n",
        "approved_test": OK_TEST,
    })
    assert r.status_code == 200
    assert r.json()["status"] == "FAILED"
    assert r.json()["attempts"][0]["stage"] == "audit"


def test_verify_rejects_bad_test():
    r = client.post("/verify", json={
        "source": "x = 0\n",
        "patched_source": "x = 1\n",
        "approved_test": "def test_x(:\n",
    })
    assert r.status_code == 400
