
import subprocess
import tempfile
import uuid
from pathlib import Path

DOCKER_IMAGE = "bugtrace-sandbox:latest"


def run_tests(files: dict, timeout: int = 10) -> dict:
    """
    Run pytest in a restricted Docker container.
    Returns PASSED, FAILED, or INCONCLUSIVE.
    """
    container_name = f"bugtrace-test-{uuid.uuid4().hex[:12]}"

    try:
        workspace_root = Path(__file__).resolve().parent / "sandbox_probe"
        workspace_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=workspace_root) as tmp:
            workspace = Path(tmp).resolve()

            for filename, content in files.items():
                relative_path = Path(filename)

                if relative_path.is_absolute() or ".." in relative_path.parts:
                    return {
                        "status": "INCONCLUSIVE",
                        "output": "",
                        "error": "Unsafe test workspace filename.",
                    }

                target = workspace / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

            command = [
                "docker", "run",
                "--name", container_name,
                "--network", "none",
                "--memory", "256m",
                "--cpus", "1",
                "--pids-limit", "64",
                "--security-opt", "no-new-privileges",
                "--cap-drop", "ALL",
                "--read-only",
                "--tmpfs", "/tmp:rw,nosuid,nodev,size=64m",
                "--mount",
                f"type=bind,source={workspace},target=/workspace",
                "--workdir", "/workspace",
                DOCKER_IMAGE,
                "python", "-m", "pytest", "-q", "-p",
                "no:cacheprovider",
            ]

            try:
                with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as log_file:
                    result = subprocess.run(
                        command,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        timeout=timeout + 30,
                    )
                    log_file.seek(0)
                    output = log_file.read().strip()[-5000:]

                if result.returncode == 0:
                    status = "PASSED"
                elif result.returncode == 1:
                    status = "FAILED"
                else:
                    status = "INCONCLUSIVE"

                return {
                    "status": status,
                    "output": output,
                    "error": None if status != "INCONCLUSIVE"
                    else f"Pytest exited with code {result.returncode}.",
                }

            except subprocess.TimeoutExpired:
                try:
                    logs = subprocess.run(
                        ["docker", "logs", container_name],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    output = (logs.stdout + "\n" + logs.stderr).strip()
                except (subprocess.TimeoutExpired, OSError):
                    output = ""

                return {
                    "status": "INCONCLUSIVE",
                    "output": output[-5000:],
                    "error": "Docker test execution timed out.",
                }

            except OSError as exc:
                return {
                    "status": "INCONCLUSIVE",
                    "output": "",
                    "error": f"Docker could not be executed: {exc}",
                }

    except Exception as exc:
        return {
            "status": "INCONCLUSIVE",
            "output": "",
            "error": f"Sandbox setup failed: {exc}",
        }

    finally:
        try:
            subprocess.run(
                ["docker", "rm", "-f", container_name],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (subprocess.TimeoutExpired, OSError):
            pass
