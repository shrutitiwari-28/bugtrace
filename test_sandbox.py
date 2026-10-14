from sandbox import run_tests

# 1. Test Buggy Code
files_buggy = {
    "calculator.py": "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)",
    "test_calculator.py": "from calculator import calculate_average\ndef test_empty():\n    assert calculate_average([]) == 0"
}
print("BUGGY CODE RESULT:", run_tests(files_buggy))

# 2. Test Infinite Loop (Should return INCONCLUSIVE via timeout)
files_infinite = {
    "calculator.py": "def calculate_average(numbers):\n    while True: pass\n    return 0",
    "test_calculator.py": "from calculator import calculate_average\ndef test_empty():\n    assert calculate_average([]) == 0"
}
print("INFINITE LOOP RESULT:", run_tests(files_infinite, timeout=2))

# 3. Test Syntax Error (Should return INCONCLUSIVE)
files_syntax = {
    "calculator.py": "def calculate_average(numbers)\n    return 0", # Missing colon
    "test_calculator.py": "from calculator import calculate_average\ndef test_empty():\n    assert calculate_average([]) == 0"
}
print("SYNTAX ERROR RESULT:", run_tests(files_syntax))