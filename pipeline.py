
from sandbox import run_tests

def run_pipeline(
    original_source: str, 
    patched_source: str, 
    reproduction_test: str, 
    regression_tests: str = "", 
    filename: str = "calculator.py"
) -> dict:
    """
    Orchestrates the full BugTrace verification pipeline:
    1. Baseline Check: Verifies the reproduction test FAILS on original buggy code (Red).
    2. Patch Check: Verifies the reproduction test PASSES on patched code (Green).
    3. Regression Check: Verifies all existing regression tests still pass.
    """
    
    # Stage 1: Confirm reproduction test fails on original code (Baseline Red)
    print("[Pipeline] Stage 1: Verifying baseline failure on original code...")
    baseline_result = run_tests({
        filename: original_source,
        "test_calculator.py": reproduction_test
    })
    
    if baseline_result["status"] == "PASSED":
        return {
            "status": "INCONCLUSIVE",
            "message": "Baseline test already passed on original code. The bug might not exist or the test is invalid.",
            "details": baseline_result
        }
    elif baseline_result["status"] == "INCONCLUSIVE":
        return {
            "status": "INCONCLUSIVE",
            "message": "Baseline test execution resulted in a syntax error or timeout.",
            "details": baseline_result
        }

    # Stage 2: Run reproduction test on patched code
    print("[Pipeline] Stage 2: Running reproduction test on patched code...")
    repro_result = run_tests({
        filename: patched_source,
        "test_calculator.py": reproduction_test
    })
    
    if repro_result["status"] != "PASSED":
        return {
            "status": "FAILED",
            "message": "Patch failed to make the reproduction test pass (still RED).",
            "details": repro_result
        }

    # Stage 3: Run regression tests if provided
    if regression_tests:
        print("[Pipeline] Stage 3: Running regression test suite...")
        regression_result = run_tests({
            filename: patched_source,
            "test_regression.py": regression_tests
        })
        
        if regression_result["status"] != "PASSED":
            return {
                "status": "FAILED",
                "message": "Patch passed the reproduction test but broke regression tests.",
                "details": regression_result
            }

    return {
        "status": "VERIFIED",
        "message": "Patch successfully verified (Baseline failed -> Patch passed -> Regressions passed).",
        "details": {
            "baseline": baseline_result,
            "reproduction": repro_result
        }
    }

