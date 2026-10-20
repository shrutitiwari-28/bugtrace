# BugTrace

An AI-assisted bug-fix verifier that proves a fix works using sandboxed execution and automated test generation.

## Day 5 - Human Approval and Retry Loop

- Implemented the investigate, approve/edit/reject, repair, verify, retry, and report workflow.
- The approved reproduction test remains frozen across repair attempts.
- Maximum of three patch attempts; retries occur only after a definite FAILED result.
- Stops on INCONCLUSIVE results, including AI/API errors and execution timeouts.
- Automated test suite: 25 passed.
- Live Gemini conflict experiment (`gemini-3.6-flash`): all three repair attempts completed.
- Attempts 1 and 3 were caught by contradictory regression tests; attempt 2 was rejected by the suspicious-code audit for blocked `sys` import and `_getframe` introspection.
- Final experiment status: FAILED, as expected for the deliberately contradictory regression requirement.

## Docker Sandbox

### Build the sandbox

Build the sandbox image before running BugTrace tests:

```powershell
docker build -t bugtrace-sandbox .
```

If the default build command fails, try:

```powershell
docker --context=default buildx build --load -t bugtrace-sandbox .
```

Verification is only as strong as the tests. The audit catches common test-gaming, not every trick.

- Tests run inside the existing `bugtrace-sandbox:latest` Docker image.
- Container restrictions include disabled networking, read-only root filesystem, dropped Linux capabilities, no-new-privileges, memory/CPU/PID limits, and a temporary filesystem.
- Test execution has a timeout; timeout and Docker execution errors return INCONCLUSIVE.
- Full automated suite verified: 25 passed.
- These restrictions reduce risk but do not guarantee protection against every container escape or denial-of-service attack.
