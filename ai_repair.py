import ast
import json
import os
from dotenv import load_dotenv

load_dotenv()

REQUIRED_KEYS = ("diagnosis", "reproduction_test", "patched_source")

SYSTEM_PROMPT = """You are an expert AI software engineer. You diagnose bugs, write reproduction tests, and patch Python source code.
You must respond with valid JSON matching the required keys: diagnosis, reproduction_test, patched_source."""

def build_prompt(source, error_output, expected_behavior, module="calculator"):
    return f"""Source code:
{source}

Error output:
{error_output}

Expected behavior:
{expected_behavior}

Module name: {module}

Return a JSON object with keys: diagnosis, reproduction_test, patched_source."""

def parse_response(text):
    try:
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        data = json.loads(text.strip())
        for key in REQUIRED_KEYS:
            if key not in data:
                return None, f"Missing required key: {key}"
        return data, None
    except Exception as e:
        return None, f"Failed to parse JSON: {e}"

def propose_fix(source, error_output, expected_behavior, module="calculator"):
    """Ask the model for a diagnosis, test, and patch. Never raises."""
    api_key = os.getenv("LLM_API_KEY")
    base_url = os.getenv("LLM_BASE_URL")
    model = os.getenv("LLM_MODEL")
    if not (api_key and base_url and model):
        return {"ok": False, "error": "Set LLM_API_KEY, LLM_BASE_URL and LLM_MODEL in .env", "data": None}
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_prompt(source, error_output, expected_behavior, module)},
            ],
        )
        text = response.choices[0].message.content or ""
    except Exception as e:
        return {"ok": False, "error": f"API call failed: {e}", "data": None}
    
    data, err = parse_response(text)
    if err:
        return {"ok": False, "error": err, "data": None}
    return {"ok": True, "error": None, "data": data}