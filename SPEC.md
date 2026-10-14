# BugTrace Technical Spec

## Core Objective
To take a buggy Python function and a failing test, automatically generate a fix and a reproduction test, run them inside a secure sandbox, verify that the test turns from RED to GREEN, perform a regression check, and output a strict verification status.

## Inputs
1. **Source Code**: A Python file containing the buggy function.
2. **Reproduction Test**: A pytest file that currently fails because of the bug.
3. **Regression Tests (Optional)**: Existing test suites to ensure the fix introduces no regressions.

## Outputs
BugTrace must output exactly one of three status results:
- **VERIFIED**: The patch was applied, the reproduction test now passes, and all existing regression tests pass.
- **FAILED**: The patch failed to make the reproduction test pass, or it broke existing regression tests.
- **INCONCLUSIVE**: The patch could not be applied cleanly or execution timed out/errored in the sandbox.

## Key Pipeline Stages
1. **Analysis**: Parse error message, stack trace, and surrounding code.
2. **Generation**: AI generates a reproduction test + code patch (JSON format).
3. **Sandbox Execution**: Run tests in an isolated Docker container with strict resource limits and a 10s timeout.
4. **Verification**: Check test results (Red -> Green transition).
