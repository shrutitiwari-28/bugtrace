
from pipeline import run_pipeline

buggy_code = "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)"
repro_test = "from calculator import calculate_average\ndef test_empty():\n    assert calculate_average([]) == 0"
regression_tests = "from calculator import calculate_average\ndef test_normal():\n    assert calculate_average([2, 4, 6]) == 4"

good_patch = "def calculate_average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)"
res1 = run_pipeline(buggy_code, good_patch, repro_test, regression_tests)
assert res1["status"] == "VERIFIED", f"Expected VERIFIED, got {res1[\"status\"]}"
print("TEST 1 PASSED")

cheat_patch = "def calculate_average(numbers):\n    return 0"
res2 = run_pipeline(buggy_code, cheat_patch, repro_test, regression_tests)
assert res2["status"] == "FAILED" and res2["stage"] == "regression", f"Expected FAILED, got {res2}"
print("TEST 2 PASSED")

bad_repro_test = "from calculator import calculate_average\ndef test_something():\n    assert calculate_average([10, 20]) == 15"
res3 = run_pipeline(buggy_code, good_patch, bad_repro_test, regression_tests)
assert res3["status"] == "INCONCLUSIVE" and res3["stage"] == "baseline", f"Expected INCONCLUSIVE, got {res3}"
print("TEST 3 PASSED")

infinite_patch = "def calculate_average(numbers):\n    while True: pass\n    return 0"
res4 = run_pipeline(buggy_code, infinite_patch, repro_test, regression_tests)
assert res4["status"] == "INCONCLUSIVE" and res4["stage"] == "reproduction", f"Expected INCONCLUSIVE timeout, got {res4}"
print("TEST 4 PASSED")

print("\nALL PIPELINE TESTS PASSED")

