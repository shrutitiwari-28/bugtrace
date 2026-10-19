# BugTrace
An AI-assisted bug-fix verifier that proves a fix works using sandboxed execution and automated test generation.

## Day 5 — Human Approval and Retry Loop

- Implemented the investigate, approve/edit/reject, repair, verify, retry, and report workflow.
- The approved reproduction test remains frozen across repair attempts.
- Maximum of three patch attempts; retries occur only after a definite FAILED result.
- Stops on INCONCLUSIVE results, including AI/API errors and execution timeouts.
- Automated test suite: 25 passed.
- Live Gemini conflict experiment: BLOCKED by API HTTP 503 errors and request timeouts; live-model behavior has not been verified.

## Sandbox limitation

Tests currently run in a subprocess with a timeout. Docker isolation is planned and is not yet implemented.
