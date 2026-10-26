
import ast
import json
import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_KEYS = ("diagnosis", "reproduction_test", "patched_source")
TEST_KEYS = ("diagnosis", "reproduction_test")
PATCH_KEYS = ("patched_source",)

SYSTEM_PROMPT = (
    "You are an expert Python debugging assistant. "
    "Follow the user's requested JSON schema exactly. "
    "Never claim code is verified unless tests have actually run."
)

TEST_PROMPT = """Investigate the bug using the source, error output,
and expected behavior.

Write a pytest test that encodes the expected behavior.
Do not propose or include a source-code patch.

Return JSON with exactly these keys:
- diagnosis
- reproduction_test

The reproduction_test value must contain valid Python test code.
"""

PATCH_PROMPT = """Repair the supplied Python source code.

Return JSON with exactly one key: patched_source.

The test is fixed and must not be changed.
Make the smallest change that makes it pass.
Do not special-case test inputs.
Preserve unrelated behavior and avoid unnecessary changes.

Previous failed attempts and their test output are provided for learning.
Use that evidence to improve the next patch.
"""


def parse_response(text, required_keys=REQUIRED_KEYS):
    """Parse model JSON and validate generated Python code."""
    try:
        text = text.strip()

        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[1].split("```", 1)[0]

        data = json.loads(text.strip())

        if not isinstance(data, dict):
            return None, "Response must be a JSON object"

        for key in required_keys:
            if key not in data:
                return None, f"Missing required key: {key}"

        for key in data:
            if key.endswith("_test") or key.endswith("_source"):
                if not isinstance(data[key], str):
                    return None, f"{key} must be a string"
                try:
                    ast.parse(data[key])
                except SyntaxError as exc:
                    return None, f"Invalid Python in {key}: {exc}"

        return data, None

    except Exception as exc:
        return None, f"Failed to parse JSON: {exc}"


def _call_model(prompt, required_keys):
    """Call the configured model and return a validated response."""
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")

    if not (api_key and base_url and model):
        return {
            "ok": False,
            "error": "Set LLM_API_KEY, LLM_BASE_URL and LLM_MODEL in .env",
            "data": None,
        }

    try:
        import time
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=60.0,
            max_retries=0,
        )

        for attempt in range(2):
            try:
                response = client.chat.completions.create(
                    model=model,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                )
                text = response.choices[0].message.content or ""
                break
            except Exception as exc:
                status_code = getattr(exc, "status_code", None)

                if attempt == 0 and status_code == 503:
                    time.sleep(2)
                    continue
                raise

    except Exception as exc:
        return {
            "ok": False,
            "error": f"API call failed: {exc}",
            "data": None,
        }

    data, error = parse_response(text, required_keys)
    if error:
        return {"ok": False, "error": error, "data": None}

    return {"ok": True, "error": None, "data": data}


def propose_test(source, error_output, expected_behavior, module="calculator"):
    """Investigate a bug and propose a reproduction test, without a patch."""
    prompt = f"""{TEST_PROMPT}

Source code:
{source}

Error output:
{error_output}

Expected behavior:
{expected_behavior}

Module name: {module}
"""
    return _call_model(prompt, TEST_KEYS)


def propose_patch(
    source,
    approved_test,
    error_output,
    module="calculator",
    previous_attempts=None,
):
    """Propose a patch against the approved, unchanged test."""
    history = []

    for attempt in previous_attempts or []:
        history.append(
            f"Attempt: {attempt.get('attempt')}\n"
            f"Patch:\n{attempt.get('patch', '(no patch)')}\n"
            f"Status: {attempt.get('status')}\n"
            f"Stage: {attempt.get('stage')}\n"
            f"Failure details:\n{attempt.get('details', '')}\n"
            f"Message: {attempt.get('message', '')}"
        )

    previous_text = "\n\n".join(history) or "No previous attempts."

    prompt = f"""{PATCH_PROMPT}

Source code:
{source}

Approved reproduction test (DO NOT CHANGE):
{approved_test}

Latest error or failing test output:
{error_output}

Module name: {module}

Previous attempts:
{previous_text}
"""
    return _call_model(prompt, PATCH_KEYS)


# Backward-compatible helpers for existing callers and tests.
def build_prompt(source, error_output, expected_behavior, module="calculator"):
    return f"""{TEST_PROMPT}

Source code:
{source}

Error output:
{error_output}

Expected behavior:
{expected_behavior}

Module name: {module}
"""


def propose_fix(source, error_output, expected_behavior, module="calculator"):
    """Legacy combined operation; new workflows should use separate stages."""
    test_result = propose_test(
        source, error_output, expected_behavior, module
    )
    if not test_result["ok"]:
        return test_result

    patch_result = propose_patch(
        source,
        test_result["data"]["reproduction_test"],
        error_output,
        module,
    )
    if not patch_result["ok"]:
        return patch_result

    return {
        "ok": True,
        "error": None,
        "data": {
            **test_result["data"],
            **patch_result["data"],
        },
    }
