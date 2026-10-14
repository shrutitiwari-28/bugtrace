
from pipeline import run_pipeline

buggy_code = "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)"
repro_test = "from calculator import calculate_average\ndef test_empty():\n    assert calculate_average([]) == 0"
regression_tests = "from calculator import calculate_average\ndef test_normal():\n    assert calculate_average([2, 4, 6]) == 4"

# 1. Good Patch
good_patch = "def calculate_average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)"
print("--- 1. TESTING GOOD PATCH ---")
print(run_pipeline(buggy_code, good_patch, repro_test, regression_tests))

# 2. Cheating Patch (Regression failure)
cheat_patch = "def calculate_average(numbers):\n    return 0"
print("\n--- 2. TESTING CHEATING PATCH ---")
print(run_pipeline(buggy_code, cheat_patch, repro_test, regression_tests))

# 3. Inconclusive Baseline
bad_repro_test = "from calculator import calculate_average\ndef test_something():\n    assert calculate_average([10, 20]) == 15"
print("\n--- 3. TESTING INCONCLUSIVE BASELINE ---")
print(run_pipeline(buggy_code, good_patch, bad_repro_test, regression_tests))

# 4. Infinite Loop Patch (Timeout -> INCONCLUSIVE)
infinite_patch = "def calculate_average(numbers):\n    while True: pass\n    return 0"
print("\n--- 4. TESTING INFINITE LOOP PATCH ---")
print(run_pipeline(buggy_code, infinite_patch, repro_test, regression_tests))

