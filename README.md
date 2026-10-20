# BugTrace

An AI-assisted bug-fix verifier that proves a fix works using sandboxed execution and automated test generation.

## Day 5 — Human Approval and Retry Loop

* Implemented the investigate, approve/edit/reject, repair, verify, retry, and report workflow.
* The approved reproduction test remains frozen across repair attempts.
* Maximum of three patch attempts; retries occur only after a definite FAILED result.
* Stops on INCONCLUSIVE results, including AI/API errors and execution timeouts.
* Automated test suite: 25 passed.
* \- Live Gemini conflict experiment (gemini-3.6-flash): Attempt 1 generated a patch returning `None` for empty input, but the contradictory regression test expected `0`. The regression tests correctly caught the conflict (1 failed, 2 passed).
* \- Attempt 2 returned HTTP 503, so the repair loop stopped as INCONCLUSIVE. Regression protection was demonstrated for the observed patch; a complete three-attempt live-model run and explicit audit rejection remain unverified.

## Sandbox limitation

Tests currently run in a subprocess with a timeout. Docker isolation is planned and is not yet implemented.

