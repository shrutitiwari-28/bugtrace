
import repair_loop


SOURCE = "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)"
APPROVED_TEST = "def test_empty_list():\n    assert calculate_average([]) == 0"


def make_verdict(status, stage="reproduction", message="Test result"):
    return {
        "status": status,
        "stage": stage,
        "message": message,
        "details": {"output": message},
    }


def test_verified_on_first_attempt(monkeypatch):
    calls = []

    def fake_patch(*args, **kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "error": None,
            "data": {"patched_source": "def calculate_average(numbers):\n    return 0"},
        }

    monkeypatch.setattr(repair_loop, "propose_patch", fake_patch)
    monkeypatch.setattr(
        repair_loop,
        "run_pipeline",
        lambda *args, **kwargs: make_verdict("VERIFIED"),
    )

    result = repair_loop.repair(SOURCE, APPROVED_TEST, "ZeroDivisionError")

    assert result["status"] == "VERIFIED"
    assert len(result["attempts"]) == 1
    assert len(calls) == 1


def test_retry_then_verified(monkeypatch):
    patches = iter([
        "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)",
        "def calculate_average(numbers):\n    return 0",
    ])
    verdicts = iter([
        make_verdict("FAILED", message="ZeroDivisionError"),
        make_verdict("VERIFIED"),
    ])
    calls = []

    def fake_patch(*args, **kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "error": None,
            "data": {"patched_source": next(patches)},
        }

    monkeypatch.setattr(repair_loop, "propose_patch", fake_patch)
    monkeypatch.setattr(
        repair_loop,
        "run_pipeline",
        lambda *args, **kwargs: next(verdicts),
    )

    result = repair_loop.repair(SOURCE, APPROVED_TEST, "ZeroDivisionError")

    assert result["status"] == "VERIFIED"
    assert len(result["attempts"]) == 2
    assert calls[1]["previous_attempts"][0]["status"] == "FAILED"
    assert "ZeroDivisionError" in calls[1]["previous_attempts"][0]["message"]


def test_stops_after_three_failed_attempts(monkeypatch):
    calls = []

    def fake_patch(*args, **kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "error": None,
            "data": {"patched_source": "def calculate_average(numbers):\n    return 1"},
        }

    monkeypatch.setattr(repair_loop, "propose_patch", fake_patch)
    monkeypatch.setattr(
        repair_loop,
        "run_pipeline",
        lambda *args, **kwargs: make_verdict("FAILED"),
    )

    result = repair_loop.repair(SOURCE, APPROVED_TEST, "ZeroDivisionError")

    assert result["status"] == "FAILED"
    assert len(result["attempts"]) == 3
    assert len(calls) == 3


def test_inconclusive_stops_without_retry(monkeypatch):
    calls = []

    def fake_patch(*args, **kwargs):
        calls.append(kwargs)
        return {
            "ok": True,
            "error": None,
            "data": {"patched_source": "while True:\n    pass"},
        }

    monkeypatch.setattr(repair_loop, "propose_patch", fake_patch)
    monkeypatch.setattr(
        repair_loop,
        "run_pipeline",
        lambda *args, **kwargs: make_verdict(
            "INCONCLUSIVE", stage="reproduction", message="Execution timed out"
        ),
    )

    result = repair_loop.repair(SOURCE, APPROVED_TEST, "Timeout")

    assert result["status"] == "INCONCLUSIVE"
    assert len(result["attempts"]) == 1
    assert len(calls) == 1


def test_ai_error_stops_without_retry(monkeypatch):
    calls = []

    def fake_patch(*args, **kwargs):
        calls.append(kwargs)
        return {"ok": False, "error": "API unavailable", "data": None}

    monkeypatch.setattr(repair_loop, "propose_patch", fake_patch)
    monkeypatch.setattr(
        repair_loop,
        "run_pipeline",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("Pipeline should not run after an AI error")
        ),
    )

    result = repair_loop.repair(SOURCE, APPROVED_TEST, "Error")

    assert result["status"] == "INCONCLUSIVE"
    assert len(result["attempts"]) == 1
    assert result["attempts"][0]["message"] == "API unavailable"
    assert len(calls) == 1


def test_approved_test_stays_frozen(monkeypatch):
    received_tests = []

    def fake_patch(source, approved_test, *args, **kwargs):
        received_tests.append(approved_test)
        return {
            "ok": True,
            "error": None,
            "data": {"patched_source": "def calculate_average(numbers):\n    return 0"},
        }

    monkeypatch.setattr(repair_loop, "propose_patch", fake_patch)
    monkeypatch.setattr(
        repair_loop,
        "run_pipeline",
        lambda *args, **kwargs: make_verdict("FAILED"),
    )

    repair_loop.repair(SOURCE, APPROVED_TEST, "Initial failure")

    assert len(received_tests) == 3
    assert all(test == APPROVED_TEST for test in received_tests)
