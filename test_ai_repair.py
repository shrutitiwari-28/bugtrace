
import ai_repair
from ai_repair import (
    REQUIRED_KEYS,
    TEST_KEYS,
    PATCH_KEYS,
    parse_response,
    build_prompt,
    propose_test,
    propose_patch,
)


def test_parse_response_valid():
    valid_json = (
        '{"diagnosis": "bug found", '
        '"reproduction_test": "def test_foo():\\n    assert True", '
        '"patched_source": "x = 1"}'
    )
    data, err = parse_response(valid_json)

    assert err is None
    assert data["diagnosis"] == "bug found"
    assert "def test_foo" in data["reproduction_test"]
    assert data["patched_source"] == "x = 1"


def test_parse_response_markdown_block():
    wrapped_json = (
        '```json\n'
        '{"diagnosis": "bug", '
        '"reproduction_test": "def test_ok():\\n    assert True", '
        '"patched_source": "code = 1"}\n'
        '```'
    )
    data, err = parse_response(wrapped_json)

    assert err is None
    assert data["diagnosis"] == "bug"


def test_parse_response_missing_key():
    data, err = parse_response('{"diagnosis": "bug"}')

    assert data is None
    assert "Missing required key" in err


def test_parse_response_bad_json():
    data, err = parse_response("not json at all")

    assert data is None
    assert "Failed to parse JSON" in err


def test_parse_response_invalid_python():
    invalid_json = (
        '{"diagnosis": "bug", '
        '"reproduction_test": "def test_broken(:", '
        '"patched_source": "x = 1"}'
    )
    data, err = parse_response(invalid_json)

    assert data is None
    assert "Invalid Python in reproduction_test" in err


def test_build_prompt():
    prompt = build_prompt(
        "print('hello')",
        "NameError",
        "Should print hello",
    )

    assert "print('hello')" in prompt
    assert "NameError" in prompt
    assert "Should print hello" in prompt


def test_required_keys_count():
    assert len(REQUIRED_KEYS) == 3


def test_stage_specific_keys():
    assert TEST_KEYS == ("diagnosis", "reproduction_test")
    assert PATCH_KEYS == ("patched_source",)


def test_propose_test_uses_investigation_schema(monkeypatch):
    captured = {}

    def fake_call(prompt, required_keys):
        captured["prompt"] = prompt
        captured["keys"] = required_keys
        return {"ok": True, "error": None, "data": {
            "diagnosis": "empty list causes division by zero",
            "reproduction_test": "def test_empty():\n    assert True",
        }}

    monkeypatch.setattr(ai_repair, "_call_model", fake_call)

    result = propose_test(
        "def average(numbers): return sum(numbers) / len(numbers)",
        "ZeroDivisionError",
        "Return zero for an empty list",
    )

    assert result["ok"] is True
    assert captured["keys"] == TEST_KEYS
    assert "Return zero for an empty list" in captured["prompt"]
    assert "patched_source" not in result["data"]


def test_propose_patch_uses_frozen_test_and_patch_schema(monkeypatch):
    captured = {}

    def fake_call(prompt, required_keys):
        captured["prompt"] = prompt
        captured["keys"] = required_keys
        return {
            "ok": True,
            "error": None,
            "data": {"patched_source": "def average(numbers):\n    return 0"},
        }

    monkeypatch.setattr(ai_repair, "_call_model", fake_call)

    approved_test = "def test_empty():\n    assert average([]) == 0"
    result = propose_patch(
        "def average(numbers): return sum(numbers) / len(numbers)",
        approved_test,
        "ZeroDivisionError",
        previous_attempts=[
            {
                "attempt": 1,
                "patch": "return sum(numbers) / len(numbers)",
                "status": "FAILED",
                "stage": "reproduction",
                "details": "ZeroDivisionError",
                "message": "Test failed",
            }
        ],
    )

    assert result["ok"] is True
    assert captured["keys"] == PATCH_KEYS
    assert approved_test in captured["prompt"]
    assert "ZeroDivisionError" in captured["prompt"]
    assert "Previous attempts" in captured["prompt"]
    assert "Test failed" in captured["prompt"]
    assert set(result["data"]) == {"patched_source"}
from types import SimpleNamespace
import pytest


@pytest.mark.parametrize("status_code", [429, 503])
def test_call_model_retries_temporary_api_error(monkeypatch, status_code):
    import sys
    import time

    calls = {"count": 0}

    class FakeAPIError(Exception):
        def __init__(self, code):
            super().__init__(f"Temporary HTTP {code} error")
            self.status_code = code

    class FakeOpenAI:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(
                completions=SimpleNamespace(create=self.create)
            )

        def create(self, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                raise FakeAPIError(status_code)

            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content='{"diagnosis": "ok", "reproduction_test": "def test_ok():\\n    assert True"}'
                        )
                    )
                ]
            )

    monkeypatch.setenv("LLM_API_KEY", "fake-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://example.invalid/v1")
    monkeypatch.setenv("LLM_MODEL", "fake-model")
    monkeypatch.setattr(time, "sleep", lambda _: None)
    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=FakeOpenAI),
    )

    result = ai_repair._call_model("test prompt", TEST_KEYS)

    assert result["ok"] is True
    assert result["data"]["diagnosis"] == "ok"
    assert calls["count"] == 2
