import subprocess
import sys
import tempfile
import os

def run_tests(files: dict, timeout: int = 10) -> dict:
    """
    Runs pytest inside an isolated temporary directory with a strict timeout.
    Takes a dictionary of {filename: file_content}.
    Returns PASSED, FAILED, or INCONCLUSIVE based on pytest exit codes.
    """
    with tempfile.TemporaryDirectory() as tmp:
        # Write all required files to the temporary directory
        for name, content in files.items():
            file_path = os.path.join(tmp, name)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        
        try:
            # Run pytest quietly in the temp directory
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=timeout
            )
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

        # Pytest exit codes: 0 = all passed, 1 = tests failed, 2/3/etc = error/interrupted/syntax error
        status_map = {0: "PASSED", 1: "FAILED"}
        status = status_map.get(r.returncode, "INCONCLUSIVE")
        
        output = (r.stdout + r.stderr)[:5000] # Cap output to 5000 chars

        return {
            "status": status,
            "output": output,
            "error": None if status != "INCONCLUSIVE" else "Sandbox execution error or syntax/import crash."
        }