
from pipeline import run_pipeline


BUGGY_CODE = """def calculate_average(numbers):
    return sum(numbers) / len(numbers)
"""

REPRO_TEST = """from calculator import calculate_average

def test_empty():
    assert calculate_average([]) == 0
"""

REGRESSION_TEST = """from calculator import calculate_average

def test_normal():
    assert calculate_average([2, 4, 6]) == 4
"""


def test_valid_patch_verifies():
    good_patch = """def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
"""
    result = run_pipeline(
        BUGGY_CODE, good_patch, REPRO_TEST, REGRESSION_TEST
    )
    assert result["status"] == "VERIFIED"


def test_bad_patch_fails_regression():
    bad_patch = """def calculate_average(numbers):
    return 0
"""
    result = run_pipeline(
        BUGGY_CODE, bad_patch, REPRO_TEST, REGRESSION_TEST
    )
    assert result["status"] == "FAILED"
    assert result["stage"] == "regression"


def test_passing_baseline_is_inconclusive():
    passing_test = """from calculator import calculate_average

def test_normal():
    assert calculate_average([10, 20]) == 15
"""
    good_patch = """def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
"""
    result = run_pipeline(
        BUGGY_CODE, good_patch, passing_test, REGRESSION_TEST
    )
    assert result["status"] == "INCONCLUSIVE"
    assert result["stage"] == "baseline"


def test_infinite_loop_times_out():
    infinite_patch = """def calculate_average(numbers):
    while True:
        pass
"""
    result = run_pipeline(
        BUGGY_CODE, infinite_patch, REPRO_TEST, REGRESSION_TEST
    )
    assert result["status"] == "INCONCLUSIVE"
    assert result["stage"] == "reproduction"


def test_contradictory_requirements_are_rejected():
    contradictory_repro = """from calculator import calculate_average

def test_empty_returns_none():
    assert calculate_average([]) is None
"""

    contradictory_regression = """from calculator import calculate_average

def test_empty_returns_zero():
    assert calculate_average([]) == 0
"""

    contradictory_patch = """def calculate_average(numbers):
    if not numbers:
        return None
    return sum(numbers) / len(numbers)
"""

    result = run_pipeline(
        BUGGY_CODE,
        contradictory_patch,
        contradictory_repro,
        contradictory_regression,
    )
    assert result["status"] == "FAILED"
    assert result["stage"] == "regression"
def test_suspicious_patch_is_rejected_by_audit():
    suspicious_patch = """import inspect

def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
"""

    result = run_pipeline(
        BUGGY_CODE,
        suspicious_patch,
        REPRO_TEST,
        REGRESSION_TEST,
    )

    assert result["status"] == "FAILED"
    assert result["stage"] == "audit"
    assert "inspect" in result["details"]["output"]