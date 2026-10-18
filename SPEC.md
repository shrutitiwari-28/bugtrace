# BugTrace Technical Spec

## 1. Core Objective

BugTrace takes buggy Python source code and an error report, investigates the bug, asks a human to approve a reproduction test, proposes a fix, and verifies it through a controlled testing pipeline.

The human decides the expected behavior. AI-generated tests and patches must not be trusted without verification.

## 2. Inputs

1. **Source Code:** Python code containing the bug.
2. **Error Output:** The error message, traceback, or failing test output.
3. **Expected Behavior:** The behavior intended by the user.
4. **Approved Reproduction Test:** A pytest test approved or edited by the human.
5. **Regression Tests (Optional):** Existing tests used to detect unintended changes.

## 3. Outputs

BugTrace returns exactly one final status:

- **VERIFIED:** The approved reproduction test passes and regression tests pass.
- **FAILED:** A patch fails verification or breaks regression tests after the allowed attempts are exhausted.
- **INCONCLUSIVE:** The AI cannot produce a valid response, or execution times out or encounters a verification error.

The report includes the final status and the details of every patch attempt.

## 4. Human-in-the-Loop Repair Flow

### Stage 1: Investigate

AI analyzes the source code, error output, and expected behavior. It returns a diagnosis and a proposed reproduction test. It does not generate or apply a patch at this stage.

### Stage 2: Approve

The human reviews the diagnosis and proposed test.

- **Approve:** Continue with the test as written.
- **Edit:** Allow the human to modify the test, then validate its Python syntax.
- **Reject:** Stop the workflow without generating a patch.

The approved test defines the expected behavior and remains frozen throughout the repair loop.

### Stage 3: Repair

AI proposes a source-code patch against the approved test. It must return the patched source in the required JSON format.

The AI must not modify the approved test or special-case individual test inputs merely to pass the test.

### Stage 4: Verify

The pipeline checks the patch using the approved test and regression tests. Verification includes the existing pipeline's baseline, reproduction, and regression stages.

### Stage 5: Retry

- Maximum **3 patch attempts total**: one initial attempt and at most two retries.
- Retry only when the verification status is **FAILED**.
- Include the latest failing test output and previous patch attempts in the next AI prompt.
- Stop immediately if the status is **VERIFIED** or **INCONCLUSIVE**.
- Never request a fourth patch attempt.

### Stage 6: Report

Display the final status and a record of each attempt, including its patch, verification stage, result, and relevant output.

## 5. Safety and Integrity Rules

1. The human-approved reproduction test is immutable during automatic retries.
2. The human owns the expected-behavior decision.
3. AI-generated source code must pass verification before it is considered fixed.
4. A failed patch must not silently replace the original source code.
5. Execution timeouts or verification errors must not be reported as successful fixes.
6. The workflow must stop after three patch attempts.
7. AI responses must follow the required JSON structure and pass syntax validation.

## 6. Core Pipeline Stages

1. **Baseline:** Establish the original code's behavior using the existing pipeline.
2. **Reproduction:** Check the approved test against the proposed patch.
3. **Regression:** Run existing regression tests, when provided.
4. **Final Decision:** Return VERIFIED, FAILED, or INCONCLUSIVE based on the pipeline results.
