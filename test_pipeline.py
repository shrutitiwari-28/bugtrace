
from pipeline import run_pipeline

# Original buggy code
buggy_code = """
def calculate_average(numbers):
    return sum(numbers) / len(numbers)
"""

# Reproduction test (fails on empty list)
repro_test = """
from calculator import calculate_average

def test_empty():
    assert calculate_average([]) == 0
"""

# Regression tests (normal averages should work)
regression_tests = """
from calculator import calculate_average

def test_normal():
    assert calculate_average([2, 4, 6]) == 4
"""

# 1. Test Good Patch (Should return VERIFIED)
good_patch = """
def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
"""
print("--- 1. TESTING GOOD PATCH ---")
print(run_pipeline(buggy_code, good_patch, repro_test, regression_tests))

# 2. Test Cheating Patch (Always returns 0 - passes repro, fails regression)
cheat_patch = """
def calculate_average(numbers):
    return 0
"""
print("\n--- 2. TESTING CHEATING PATCH (Regression failure) ---")
print(run_pipeline(buggy_code, cheat_patch, repro_test, regression_tests))

