
from pipeline import run_pipeline

# 1. Test Buggy Code (Expect FAILED)
buggy_code = "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)"
test_code = "from calculator import calculate_average\ndef test_empty():\n    assert calculate_average([]) == 0"

print("--- TESTING PIPELINE WITH BUGGY CODE ---")
print(run_pipeline(buggy_code, test_code))

# 2. Test Fixed Code (Expect VERIFIED)
fixed_code = "def calculate_average(numbers):\n    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)"

print("\n--- TESTING PIPELINE WITH FIXED CODE ---")
print(run_pipeline(fixed_code, test_code))

