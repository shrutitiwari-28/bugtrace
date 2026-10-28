# BugTrace Architecture



## Overview



BugTrace is an AI-assisted bug-fix verification system. It uses an approved test, an AI-proposed patch, code auditing, and sandboxed execution to determine whether a proposed fix passes the required checks.



## System Flow



```mermaid

flowchart TD

&#x20;   A\[User] --> B\[Web Interface]

&#x20;   B --> C\[FastAPI API]

&#x20;   C --> D\[Investigation]

&#x20;   C --> E\[Repair Loop]

&#x20;   D --> F\[AI Provider]

&#x20;   E --> F

&#x20;   E --> G\[Code Audit]

&#x20;   G --> H\[Baseline Test]

&#x20;   H --> I\[Reproduction Test]

&#x20;   I --> J\[Regression Test]

&#x20;   J --> K\[Docker Sandbox]

&#x20;   K --> L\[Verification Result]

&#x20;   L --> B

```



## Main Components



\- \*\*Web interface (`web/`)\*\* â€” lets users submit a bug, review the proposed test, and view the verification result.

\- \*\*API (`api.py`)\*\* â€” provides the FastAPI endpoints `/`, `/health`, `/investigate`, `/repair`, and `/verify`.

\- \*\*AI repair (`ai\_repair.py`, `ai\_run.py`)\*\* â€” communicates with the configured AI provider to propose tests and code patches.

\- \*\*Audit (`audit.py`)\*\* â€” checks proposed code for suspicious patterns before execution.

\- \*\*Pipeline (`pipeline.py`)\*\* â€” coordinates baseline, reproduction, audit, and regression checks.

\- \*\*Repair loop (`repair\_loop.py`)\*\* â€” manages approved tests and retries, with a maximum of three patch attempts.

\- \*\*Sandbox (`sandbox.py`)\*\* â€” executes tests inside the Docker sandbox with resource and filesystem restrictions.

\- \*\*Tests and benchmark (`test\_\*.py`, `benchmark/`)\*\* â€” check component behavior and evaluate the system against benchmark cases.



## Verification Outcomes



\- \*\*VERIFIED\*\* â€” the required checks passed.

\- \*\*FAILED\*\* â€” a definite check failed.

\- \*\*INCONCLUSIVE\*\* â€” verification could not complete reliably, for example because of an AI/API error, timeout, or sandbox execution problem.



## Limitations



A VERIFIED result means the approved tests passed; it does not prove that the patch is correct for every possible input. The audit and sandbox reduce risk but do not guarantee detection of every incorrect patch or prevention of every security issue.



