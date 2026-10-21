# BugTrace

An AI-assisted bug-fix verifier that uses approved tests, sandboxed execution, and automated checks to evaluate proposed code fixes.

## Day 5 - Human Approval and Retry Loop

- Implemented the investigate, approve/edit/reject, repair, verify, retry, and report workflow.
- The approved reproduction test remains frozen across repair attempts.
- Maximum of three patch attempts; retries occur only after a definite FAILED result.
- Stops on INCONCLUSIVE results, including AI/API errors and execution timeouts.
- The repair loop and pipeline have automated test coverage.
- A previous live Gemini conflict experiment (`gemini-3.6-flash`) exercised all three repair attempts.
- Attempts were evaluated using regression tests and the suspicious-code audit.
- The contradictory regression experiment ended in FAILED, as expected.
- Do not interpret a FAILED result as a successful fix.

## Docker Sandbox

- Tests execute inside the `bugtrace-sandbox:latest` Docker image.
- Container restrictions include disabled networking, a read-only root filesystem, dropped Linux capabilities, no-new-privileges, resource limits, and a temporary filesystem.
- Test execution has a timeout; timeout and Docker execution errors return INCONCLUSIVE.
- Docker startup was restored during Day 6 troubleshooting.
- `docker run --rm hello-world` succeeded after the Docker fix.
- A small sandbox integration test passed.
- The full automated test suite passed: **35 passed**.
- Pipeline tests passed separately: **6 passed**.
- These restrictions reduce risk but do not guarantee protection against every container escape or denial-of-service attack.

### Build the sandbox

Build the sandbox image before running BugTrace tests:

```powershell
docker build -t bugtrace-sandbox .
```

If needed, try:

```powershell
docker --context=default buildx build --load -t bugtrace-sandbox .
```

## Day 6 - Web Interface and End-to-End Verification

- Added a browser-based interface using HTML, CSS, and JavaScript.
- Integrated the interface with FastAPI endpoints for investigation and repair.
- Implemented the browser workflow for bug submission, diagnosis, test review, repair, and verification.
- Captured workflow screenshots in `docs/screenshots/`, including form, test review, Verified, Failed, and Inconclusive results.
- The Failed UI demonstration used a locally supplied test patch to avoid calling the AI provider.
- Docker smoke testing and automated tests passed after the startup issue was fixed.
- **Live AI-provider verification remains pending.** An earlier AI API error is documented separately; no current live AI success is claimed.
- A VERIFIED result means the approved tests passed in the sandbox. It does not prove correctness for every possible input.

## Troubleshooting Evidence

- `docs/screenshots/01-form.png` — bug submission form.
- `docs/screenshots/02-review-test.png` — approved test review workflow.
- `docs/screenshots/03-verified.png` — Verified result screen.
- `docs/screenshots/04-failed.png` — Failed result screen from a local test scenario.
- `docs/screenshots/04-inconclusive.png` — Inconclusive result screen.
- `docs/screenshots/inconclusive-api-error.png` — an inconclusive AI API error; not evidence of a successful AI repair.
- `docs/screenshots/verified-incorrect-fix.png` — the test checks only whether an empty list returns 0, so a patch that always returns 0 could pass while calculating normal averages incorrectly.

Verification is only as strong as the tests executed. The audit catches common test-gaming patterns but cannot guarantee that every possible incorrect fix will be detected.
