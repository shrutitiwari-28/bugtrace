from audit import audit_patch
from sandbox import run_tests

def run_pipeline(
    original_source: str,
    patched_source: str,
    reproduction_test: str,
    regression_tests: str = "",
    filename: str = "calculator.py"
) -> dict:
    baseline_result = run_tests({
        filename: original_source,
        "test_calculator.py": reproduction_test
    })

    if baseline_result["status"] == "PASSED":
        return {
            "status": "INCONCLUSIVE",
            "stage": "baseline",
            "message": "Baseline test already passed on original code.",
            "details": baseline_result
        }
    elif baseline_result["status"] == "INCONCLUSIVE":
        return {
            "status": "INCONCLUSIVE",
            "stage": "baseline",
            "message": "Baseline test execution resulted in syntax error or timeout.",
            "details": baseline_result
        }

    problems = audit_patch(patched_source)
    if problems:
        return {
            "status": "FAILED",
            "stage": "audit",
            "message": "Patch rejected by the suspicious-code audit.",
            "details": {
                "status": "FAILED",
                "output": "; ".join(problems),
                "error": None,
            },
        }

    repro_result = run_tests({
        filename: patched_source,
        "test_calculator.py": reproduction_test
    })

    if repro_result["status"] != "PASSED":
        return {
            "status": "FAILED" if repro_result["status"] == "FAILED" else "INCONCLUSIVE",
            "stage": "reproduction",
            "message": "Patch failed to make the reproduction test pass." if repro_result["status"] == "FAILED" else "Reproduction run could not complete.",
            "details": repro_result
        }

    regression_result = None
    if regression_tests:
        regression_result = run_tests({
            filename: patched_source,
            "test_regression.py": regression_tests
        })

        if regression_result["status"] != "PASSED":
            return {
                "status": "FAILED" if regression_result["status"] == "FAILED" else "INCONCLUSIVE",
                "stage": "regression",
                "message": "Patch broke regression tests." if regression_result["status"] == "FAILED" else "Regression run could not complete.",
                "details": regression_result
            }

    return {
        "status": "VERIFIED",
        "stage": "regression" if regression_tests else "reproduction",
        "message": "Patch successfully verified across all stages.",
        "details": {
            "baseline": baseline_result,
            "reproduction": repro_result,
            "regression": regression_result
        }
    }

