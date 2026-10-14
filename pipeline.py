
from sandbox import run_tests

def run_pipeline(source_code: str, test_code: str, filename: str = "calculator.py") -> dict:
    """
    Orchestrates the BugTrace verification pipeline:
    1. Prepares the files dictionary.
    2. Executes them via the sandbox runner.
    3. Evaluates test results into VERIFIED, FAILED, or INCONCLUSIVE statuses.
    """
    files = {
        filename: source_code,
        "test_calculator.py": test_code
    }
    
    print(f"[Pipeline] Running verification for {filename}...")
    result = run_tests(files)
    
    status = result["status"]
    
    if status == "PASSED":
        return {
            "status": "VERIFIED",
            "message": "Patch successfully turned the reproduction test GREEN!",
            "details": result
        }
    elif status == "FAILED":
        return {
            "status": "FAILED",
            "message": "Patch failed; reproduction test remains RED.",
            "details": result
        }
    else:
        return {
            "status": "INCONCLUSIVE",
            "message": "Execution encountered a syntax error, import crash, or timeout.",
            "details": result
        }

