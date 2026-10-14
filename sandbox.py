
import subprocess
import sys

def run_tests(source_code: str, test_code: str, timeout: int = 10) -> dict:
    # Write source code
    with open("calculator.py", "w", encoding="utf-8") as f:
        f.write(source_code)

    # Write test code
    with open("test_calculator.py", "w", encoding="utf-8") as f:
        f.write(test_code)

    try:
        # Run pytest securely via subprocess
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "test_calculator.py", "-v"],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        passed = (result.returncode == 0)
        output = result.stdout + "\n" + result.stderr
        
        return {
            "status": "PASSED" if passed else "FAILED",
            "output": output,
            "error": None
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "INCONCLUSIVE",
            "output": "",
            "error": "Execution timed out (possible infinite loop)."
        }
    except Exception as e:
        return {
            "status": "INCONCLUSIVE",
            "output": "",
            "error": str(e)
        }

