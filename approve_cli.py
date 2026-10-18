
import ast
from pathlib import Path

from repair_loop import investigate, repair


SOURCE = """def calculate_average(numbers):
    return sum(numbers) / len(numbers)
"""

ERROR_OUTPUT = "ZeroDivisionError: division by zero for an empty list"

EXPECTED_BEHAVIOR = (
    "calculate_average should return None when given an empty list. "
    "For non-empty lists, it should return the arithmetic average."
)


REGRESSION_TESTS = """from calculator import calculate_average

def test_normal_average():
    assert calculate_average([2, 4, 6]) == 4

def test_single_number():
    assert calculate_average([5]) == 5
"""



def get_approved_test():
    print("\nInvestigating the bug...")

    result = investigate(
        SOURCE,
        ERROR_OUTPUT,
        EXPECTED_BEHAVIOR,
        module="calculator",
    )

    if not result["ok"]:
        print(f"\nInvestigation failed: {result['error']}")
        return None

    data = result["data"]
    print("\nDiagnosis:")
    print(data["diagnosis"])
    print("\nProposed reproduction test:")
    print(data["reproduction_test"])

    while True:
        choice = input(
            "\n[a]pprove, [e]dit, or [r]eject? "
        ).strip().lower()

        if choice == "a":
            test_code = data["reproduction_test"]

        elif choice == "e":
            path = Path("edited_test.py")
            path.write_text(
                data["reproduction_test"],
                encoding="utf-8",
            )
            print(
                "\nOpen edited_test.py in VS Code and edit the test."
                "\nSave it, then return here."
            )
            input("Press Enter when you have finished editing... ")

            try:
                test_code = path.read_text(encoding="utf-8")
                ast.parse(test_code)
            except (SyntaxError, OSError) as exc:
                print(f"\nThe edited test is invalid: {exc}")
                print("Please choose edit again and correct it.")
                continue

        elif choice == "r":
            print("\nTest rejected. No patch was generated.")
            return None

        else:
            print("Please enter a, e, or r.")
            continue

        try:
            ast.parse(test_code)
        except SyntaxError as exc:
            print(f"\nThe test has invalid Python syntax: {exc}")
            continue

        if not test_code.strip():
            print("The test cannot be empty.")
            continue

        confirmation = input(
            "\nApprove this exact test and begin repair? [y/n]: "
        ).strip().lower()

        if confirmation == "y":
            return test_code

        print("Approval cancelled. Choose approve, edit, or reject.")


def main():
    approved_test = get_approved_test()

    if approved_test is None:
        return

    print("\nApproved test is frozen for all repair attempts.")
    print("Starting repair loop...\n")

    result = repair(
        SOURCE,
        approved_test,
        ERROR_OUTPUT,
        regression_tests=REGRESSION_TESTS,
        module="calculator",
    )

    print("\n========== REPAIR REPORT ==========")

    for attempt in result["attempts"]:
        print(
            f"\nAttempt {attempt['attempt']}: "
            f"{attempt['status']}"
        )
        print(f"Stage: {attempt.get('stage', 'unknown')}")
        print(f"Message: {attempt.get('message', '')}")

        if attempt.get("details") is not None:
            print(f"Details: {attempt['details']}")

    print("\nFinal status:", result["status"])
    print("===================================")


if __name__ == "__main__":
    main()
