import pytest
from ai_repair import parse_response, build_prompt, REQUIRED_KEYS

def test_parse_response_valid():
    valid_json = '{"diagnosis": "bug found", "reproduction_test": "def test_foo(): pass", "patched_source": "x = 1"}'
    data, err = parse_response(valid_json)
    assert err is None
    assert data["diagnosis"] == "bug found"
    assert data["reproduction_test"] == "def test_foo(): pass"
    assert data["patched_source"] == "x = 1"

def test_parse_response_markdown_block():
    wrapped_json = '```json\n{"diagnosis": "bug", "reproduction_test": "test", "patched_source": "code"}\n```'
    data, err = parse_response(wrapped_json)
    assert err is None
    assert data["diagnosis"] == "bug"

def test_parse_response_missing_key():
    invalid_json = '{"diagnosis": "bug"}'
    data, err = parse_response(invalid_json)
    assert data is None
    assert "Missing required key" in err

def test_parse_response_bad_json():
    bad_json = 'not json at all'
    data, err = parse_response(bad_json)
    assert data is None
    assert "Failed to parse JSON" in err

def test_build_prompt():
    prompt = build_prompt("print('hello')", "NameError", "Should print hello")
    assert "print('hello')" in prompt
    assert "NameError" in prompt
    assert "Should print hello" in prompt

def test_required_keys_count():
    assert len(REQUIRED_KEYS) == 3