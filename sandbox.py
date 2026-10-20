import os
import subprocess
import tempfile
import uuid

DOCKER_IMAGE = "bugtrace-sandbox:latest"


def run_tests(files: dict, timeout: int = 10) -> dict:
    container_name = f"bugtrace-test-{uuid.uuid4().hex[:12]}"

    with tempfile.TemporaryDirectory() as tmp:
        tmp_abs = os.path.abspath(tmp)
        container_created = False

        try:
            for name, content in files.items():
                file_path = os.path.abspath(os.path.join(tmp_abs, name))

                if os.path.commonpath([tmp_abs, file_path]) != tmp_abs:
                    return {
                        "status": "INCONCLUSIVE",
                        "output": "",
                        "error": f"Invalid test filename: {name}",
                    }

                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            create_cmd = [
                "docker", "create",
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
                f"type=bind,source={tmp_abs},target=/workspace",
                "--workdir", "/workspace",
                DOCKER_IMAGE,
            ]

            created = subprocess.run(
                create_cmd, capture_output=True, text=True, timeout=30
            )
            if created.returncode != 0:
                return {
                    "status": "INCONCLUSIVE",
                    "output": (created.stdout + created.stderr)[:5000],
                    "error": "Docker could not create the test container.",
                }

            container_created = True

            started = subprocess.run(
                ["docker", "start", container_name],
                capture_output=True, text=True, timeout=30
            )
            if started.returncode != 0:
                return {
                    "status": "INCONCLUSIVE",
                    "output": (started.stdout + started.stderr)[:5000],
                    "error": "Docker could not start the test container.",
                }

            try:
                waited = subprocess.run(
                    ["docker", "wait", container_name],
                    capture_output=True, text=True, timeout=timeout
                )
            except subprocess.TimeoutExpired:
                subprocess.run(
                    ["docker", "kill", container_name],
                    capture_output=True, text=True, timeout=10
                )
                logs = subprocess.run(
                    ["docker", "logs", container_name],
                    capture_output=True, text=True, timeout=10
                )
                return {
                    "status": "INCONCLUSIVE",
                    "output": (logs.stdout + logs.stderr)[:5000],
                    "error": "Test execution timed out; the container was stopped.",
                }

            logs = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True, text=True, timeout=10
            )
            output = (logs.stdout + logs.stderr)[:5000]

            if waited.returncode != 0:
                return {
                    "status": "INCONCLUSIVE",
                    "output": output,
                    "error": "Docker failed while waiting for the test container.",
                }

            try:
                exit_code = int(waited.stdout.strip())
            except ValueError:
                return {
                    "status": "INCONCLUSIVE",
                    "output": output,
                    "error": "Docker returned an invalid container exit code.",
                }

            status = {0: "PASSED", 1: "FAILED"}.get(
                exit_code, "INCONCLUSIVE"
            )

            return {
                "status": status,
                "output": output,
                "error": None if status != "INCONCLUSIVE"
                else f"Test process exited unexpectedly with code {exit_code}.",
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "INCONCLUSIVE",
                "output": "",
                "error": "Docker operation timed out.",
            }
        except Exception as e:
            return {
                "status": "INCONCLUSIVE",
                "output": "",
                "error": str(e),
            }
        finally:
            if container_created:
                subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True, text=True, timeout=10
                )
