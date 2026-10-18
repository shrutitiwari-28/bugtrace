
from ai_repair import propose_fix
from pipeline import run_pipeline

SOURCE = "def calculate_average(numbers):\n    return sum(numbers) / len(numbers)\n"
ERROR = "ZeroDivisionError: division by zero (calculator.py, line 2)"
EXPECTED = "calculate_average([]) should return 0. Normal lists must still return their mean."
REGRESSION = """from calculator import calculate_average

def test_normal():
    assert calculate_average([2, 4, 6]) == 4
"""

print("Asking the model for a fix...", flush=True)

result = propose_fix(SOURCE, ERROR, EXPECTED)

if not result["ok"]:
    print("AI STEP FAILED:", result["error"])
    raise SystemExit(1)

data = result["data"]

print("\n--- DIAGNOSIS ---\n" + data["diagnosis"])
print("\n--- GENERATED TEST ---\n" + data["reproduction_test"])
print("\n--- PROPOSED PATCH ---\n" + data["patched_source"])

verdict = run_pipeline(
    SOURCE,
    data["patched_source"],
    data["reproduction_test"],
    REGRESSION
)

print("\nSTATUS:", verdict["status"], "| stage:", verdict["stage"])
print("MESSAGE:", verdict["message"])
