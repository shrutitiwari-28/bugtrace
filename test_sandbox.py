import subprocess
import sandbox


class FakeResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def mock_docker(monkeypatch, returncode, output):
    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["docker", "run"]:
            kwargs["stdout"].write(output)
            return FakeResult(returncode)
        return FakeResult()

    monkeypatch.setattr(sandbox.subprocess, "run", fake_run)


def test_buggy_code_returns_failed(monkeypatch):
    mock_docker(monkeypatch, 1, "1 failed")

    result = sandbox.run_tests({
        "calculator.py": "def calculate_average(numbers): return sum(numbers) / len(numbers)",
        "test_calculator.py": "def test_example(): assert False",
    })

    assert result["status"] == "FAILED"


def test_fixed_code_returns_passed(monkeypatch):
    mock_docker(monkeypatch, 0, "1 passed")

    result = sandbox.run_tests({
        "calculator.py": "def calculate_average(numbers): return 0 if not numbers else sum(numbers) / len(numbers)",
        "test_calculator.py": "def test_example(): assert True",
    })

    assert result["status"] == "PASSED"


def test_syntax_error_returns_inconclusive(monkeypatch):
    mock_docker(monkeypatch, 2, "SyntaxError: invalid syntax")

    result = sandbox.run_tests({
        "calculator.py": "def broken(:",
        "test_calculator.py": "def test_example(): pass",
    })

    assert result["status"] == "INCONCLUSIVE"


def test_timeout_returns_inconclusive(monkeypatch):
    def fake_run(cmd, **kwargs):
        if cmd[:2] == ["docker", "run"]:
            raise subprocess.TimeoutExpired(cmd, 2)
        return FakeResult()

    monkeypatch.setattr(sandbox.subprocess, "run", fake_run)

    result = sandbox.run_tests({
        "calculator.py": "def calculate_average(numbers): return 0",
        "test_calculator.py": "def test_example(): pass",
    }, timeout=2)

    assert result["status"] == "INCONCLUSIVE"
