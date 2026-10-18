
from audit import audit_patch


def test_clean_patch_returns_no_problems():
    source = """def calculate_average(numbers):
    if not numbers:
        return None
    return sum(numbers) / len(numbers)
"""
    assert audit_patch(source) == []


def test_inspect_import_is_flagged():
    source = """import inspect

def calculate_average(numbers):
    return None if not numbers else sum(numbers) / len(numbers)
"""
    problems = audit_patch(source)
    assert any("inspect" in problem for problem in problems)


def test_sys_getframe_is_flagged():
    source = """import sys

def calculate_average(numbers):
    frame = sys._getframe()
    return None if not numbers else sum(numbers) / len(numbers)
"""
    problems = audit_patch(source)
    assert any("_getframe" in problem for problem in problems)
