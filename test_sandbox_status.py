import sandbox


class _R:
    def __init__(self, rc):
        self.returncode = rc
        self.stdout = ""
        self.stderr = ""


def test_docker_outage_is_inconclusive(monkeypatch):
    def fake_run(cmd, **kw):
        if cmd[:2] == ["docker", "run"]:
            kw["stdout"].write(
                "failed to connect to the docker API at "
                "npipe:////./pipe/dockerDesktopLinuxEngine"
            )
            return _R(1)
        return _R(0)

    monkeypatch.setattr(sandbox.subprocess, "run", fake_run)

    result = sandbox.run_tests({"test_x.py": "def test_x(): pass"})

    assert result["status"] == "INCONCLUSIVE"
