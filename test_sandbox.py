
from sandbox import run_tests

# 1. Test with buggy source code + failing import test
source_buggy = """
def calculate_average(numbers):
    return sum(numbers) / len(numbers)
"""

test_code = """
from calculator import calculate_average

def test_empty():
    assert calculate_average([]) == 0
"""

print("--- TESTING BUGGY CODE ---")
print(run_tests(source_buggy, test_code))

# 2. Test with fixed source code
source_fixed = """
def calculate_average(numbers):
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)
"""

print("\n--- TESTING FIXED CODE ---")
print(run_tests(source_fixed, test_code))

