
import json

from ai_repair import propose_test, propose_patch
from pipeline import run_pipeline

MAX_ATTEMPTS = 3


def investigate(source, error_output, expected_behavior, module="calculator"):
    """Investigate the bug without generating a patch."""
    return propose_test(
        source,
        error_output,
        expected_behavior,
        module,
    )


def repair(
    source,
    approved_test,
    error_output,
    regression_tests="",
    module="calculator",
):
    """Try up to three patches against one frozen, approved test."""
    attempts = []
    latest_error = error_output

    for n in range(1, MAX_ATTEMPTS + 1):
        # Every attempt receives the exact same approved test.
        result = propose_patch(
            source,
            approved_test,
            latest_error,
            module,
            previous_attempts=attempts,
        )

        if not result["ok"]:
            attempts.append({
                "attempt": n,
                "status": "INCONCLUSIVE",
                "stage": "ai",
                "message": result.get("error") or "AI patch generation failed.",
                "details": None,
            })
            break

        patch = result["data"]["patched_source"]

        try:
            verdict = run_pipeline(
                source,
                patch,
                approved_test,
                regression_tests,
                filename=f"{module}.py",
            )
        except Exception as exc:
            attempts.append({
                "attempt": n,
                "patch": patch,
                "status": "INCONCLUSIVE",
                "stage": "pipeline",
                "message": f"Pipeline execution failed: {exc}",
                "details": None,
            })
            break

        details = verdict.get("details")
        status = verdict.get("status", "INCONCLUSIVE")

        attempts.append({
            "attempt": n,
            "patch": patch,
            "status": status,
            "stage": verdict.get("stage", "unknown"),
            "message": verdict.get("message", ""),
            "details": details,
        })

        # Stop on success or any result other than a definite failure.
        if status != "FAILED":
            break

        # Give the next attempt the latest failure output as feedback.
        latest_error = (
            "Latest patch verification failed.\n"
            + json.dumps(details, indent=2, default=str)
        )

    final_status = (
        attempts[-1]["status"] if attempts else "INCONCLUSIVE"
    )

    return {
        "status": final_status,
        "attempts": attempts,
    }
