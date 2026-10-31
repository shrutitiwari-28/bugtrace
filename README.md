# BugTrace

**BugTrace checks AI-generated bug fixes before you trust them.**

An AI tool can suggest a fix, but a suggestion is not proof. BugTrace runs an approved test on your original code and on the fix, inside an isolated Docker container, and reports one of three results: `VERIFIED`, `FAILED` or `INCONCLUSIVE`.

| Review the test | Verified, with before and after | A sneaky fix rejected by the audit |
|---|---|---|
| ![Review](docs/screenshots/02-review-test.png) | ![Verified](docs/screenshots/live-ai-verified.png) | ![Audit](docs/screenshots/06-audit-rejected.png) |

## The problem

AI assistants write plausible fixes quickly. Checking them is still manual: does the fix really solve the bug, did it break something else, and did it only pass because it was written around the test? BugTrace turns those questions into an automatic check with a human in control of what "fixed" means.

## How it works

1. **Describe the bug.** Paste the code, the error and what it should do.
2. **The AI proposes a test.** You read it, edit it if needed, and approve it. This test defines "fixed" and stays frozen from then on.
3. **The AI proposes a fix** (up to three attempts, only retried after a definite `FAILED`).
4. **BugTrace verifies it** in a Docker sandbox:
   - *Baseline:* the approved test must fail on your original code.
   - *Audit:* the fix is scanned for test-gaming tricks, such as inspecting the call stack.
   - *Reproduction:* the approved test must pass on the fix.
   - *Regression:* your existing tests must still pass.

| Result | Meaning |
|---|---|
| `VERIFIED` | The approved test failed before, passes now, and existing tests still pass. |
| `FAILED` | The fix did not pass every check. Your original code is not changed. |
| `INCONCLUSIVE` | The check could not finish (timeout, Docker or AI error). Never treated as a pass or a fail. |

The AI never decides the verdict. The sandbox does. See [docs/architecture.md](docs/architecture.md).

## What makes it different

- **A human approves the test.** The AI cannot grade its own work against a test it wrote and you never saw.
- **Test-gaming is checked.** In a live run, the model tried to detect which test was running by reading the call stack. The audit rejected it. Another attempt used a hidden call counter and was caught by a regression test.
- **A timeout is never a success.** If Docker or the AI provider fails, the answer is `INCONCLUSIVE`.
- **Sandboxed execution.** Each run uses a fresh container with no network, a read-only root filesystem, dropped Linux capabilities, `no-new-privileges`, 256 MB memory, 1 CPU, a 64-process limit and a timeout.

## Quick start

You need Python 3.12 or newer (developed on 3.14) and Docker Desktop running.

```powershell
git clone https://github.com/shrutitiwari-28/bugtrace.git
cd bugtrace
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
docker build -t bugtrace-sandbox .
Copy-Item .env.example .env           # macOS/Linux: cp .env.example .env
```

Edit `.env` with any OpenAI-compatible provider. Example for Google Gemini:

```
LLM_API_KEY=your_key_here
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_MODEL=your_model_name
```

Never commit `.env`. It is already in `.gitignore`.

```powershell
python -m uvicorn api:app --reload
```

Open http://127.0.0.1:8000. To try it without an AI key, choose **Check a correct fix (no AI)** from the example list, or tick *I already have a fix to check*.

If the build command fails on Windows, try `docker --context=default buildx build --load -t bugtrace-sandbox .`.

## Check a fix from any tool

`POST /verify` checks a fix you already have, with no AI involved:

```python
import httpx

r = httpx.post("http://127.0.0.1:8000/verify", timeout=120, json={
    "source": "def first_n(items, n):\n    return items[:n - 1]\n",
    "patched_source": "def first_n(items, n):\n    return items[:n]\n",
    "approved_test": "from calculator import first_n\n\ndef test_two():\n    assert first_n([1, 2, 3], 2) == [1, 2]\n",
    "regression_tests": "",
})
print(r.json()["status"])
```

Other endpoints: `GET /health`, `POST /investigate` (diagnosis and proposed test) and `POST /repair` (the full repair loop). Code is saved as `calculator.py` in the sandbox, so tests import from `calculator`.

## Benchmark

15 small single-function Python bugs (empty input, off-by-one, wrong key, None handling, wrong condition, boundary error, and more). Each has a fixed approved test, regression tests and a reference fix used only to prove the bug is valid. The AI never sees the reference fix.

- **Tuning set (B01 to B10):** [10]/10 verified.
- **Held-out set (B11 to B15):** [5]/5 verified. The code was frozen at commit `bc2c42c` (tag `benchmark-freeze`) before this run.
- **Model:** [Gemini 3.6 Flash]. Attempts: [15] of [15] verified on the first attempt.


How to read this: the bugs are small and the approved tests were written by the project author, so this shows the pipeline works on simple cases. It is not an accuracy figure for real codebases, and the held-out bugs were visible to the author, who did not tune on them. Full results are in [benchmark/results](benchmark/results). Run `python benchmark/run_benchmark.py validate` to check the bugs yourself without any AI.

## Limitations

- `VERIFIED` means the approved tests passed. It does not prove the code is correct for every input.
- The audit catches common test-gaming tricks, not all of them. A weak test can still accept a wrong fix.
- Python only, and small single-file projects.
- Docker reduces risk but does not guarantee protection against every possible attack. Do not expose this app to untrusted users on the public internet.
- Free AI providers have daily limits and can time out. Those cases show as `INCONCLUSIVE`.

## Tests

```powershell
python -m pytest -q
```

46 tests. Several start Docker containers, so a full run takes a few minutes.

## Project layout

```
api.py            FastAPI app and endpoints
pipeline.py       baseline, audit, reproduction, regression
repair_loop.py    up to 3 attempts with a frozen test
ai_repair.py      AI calls and response validation
audit.py          test-gaming checks
sandbox.py        Docker runner
web/              browser interface
benchmark/        15 bugs, runner and results
docs/             architecture and screenshots
```

## Impact and what's next

Anyone who accepts AI-written fixes, from solo developers to teams reviewing pull requests, needs a cheap way to ask "does this really work?". Next steps: a pytest plugin and a CI check that run the same verification on a pull request, support for more languages, stronger checks against weak tests, and hosting with stronger isolation.

## Progress log

The day-by-day build notes are in [docs/progress-log.md](docs/progress-log.md).

## License

MIT. See [LICENSE](LICENSE).
