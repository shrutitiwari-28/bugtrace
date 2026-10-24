
import ast

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from repair_loop import investigate, repair
from pipeline import run_pipeline

app = FastAPI(title="BugTrace API", version="1.0.0")

from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

web_dir = Path(__file__).resolve().parent / "web"
app.mount("/web", StaticFiles(directory=web_dir), name="web")

@app.get("/")
def home():
    return FileResponse(web_dir / "index.html")

MAX_SOURCE = 50_000
MAX_ERROR = 20_000
MAX_EXPECTED = 10_000
MAX_TEST = 20_000
MAX_REGRESSION = 50_000
MAX_MODULE = 100


class InvestigateRequest(BaseModel):
    source: str = Field(max_length=MAX_SOURCE)
    error_output: str = Field(max_length=MAX_ERROR)
    expected_behavior: str = Field(max_length=MAX_EXPECTED)
    module: str = Field(default="calculator", max_length=MAX_MODULE)


class VerifyRequest(BaseModel):
    source: str = Field(max_length=MAX_SOURCE)
    patched_source: str = Field(max_length=MAX_SOURCE)
    approved_test: str = Field(max_length=MAX_TEST)
    regression_tests: str = Field(default="", max_length=MAX_REGRESSION)
    module: str = Field(default="calculator", max_length=MAX_MODULE)

class RepairRequest(BaseModel):
    source: str = Field(max_length=MAX_SOURCE)
    approved_test: str = Field(max_length=MAX_TEST)
    error_output: str = Field(max_length=MAX_ERROR)
    regression_tests: str = Field(default="", max_length=MAX_REGRESSION)
    module: str = Field(default="calculator", max_length=MAX_MODULE)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/investigate")
def investigate_endpoint(request: InvestigateRequest):
    validate_module(request.module)

    try:
        result = investigate(
            request.source,
            request.error_output,
            request.expected_behavior,
            request.module,
        )
        return result
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Investigation failed unexpectedly.",
        )


@app.post("/repair")
def repair_endpoint(request: RepairRequest):
    validate_module(request.module)

    try:
        ast.parse(request.approved_test)
    except SyntaxError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Approved test has invalid Python syntax: {exc.msg}",
        )

    try:
        ast.parse(request.source)
    except SyntaxError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Source code has invalid Python syntax: {exc.msg}",
        )

    try:
        result = repair(
            request.source,
            request.approved_test,
            request.error_output,
            request.regression_tests,
            request.module,
        )
        return result
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Repair failed unexpectedly.",
        )


@app.post("/verify")
def verify_endpoint(request: VerifyRequest):
    validate_module(request.module)
    for label, code in (("Approved test", request.approved_test), ("Source code", request.source)):
        try:
            ast.parse(code)
        except SyntaxError as exc:
            raise HTTPException(status_code=400, detail=f"{label} has invalid Python syntax: {exc.msg}")
    try:
        v = run_pipeline(request.source, request.patched_source, request.approved_test,
                         request.regression_tests, filename=f"{request.module}.py")
    except Exception:
        raise HTTPException(status_code=500, detail="Verification failed unexpectedly.")
    return {
        "status": v.get("status", "INCONCLUSIVE"),
        "attempts": [{
            "attempt": 1, "patch": request.patched_source, "status": v.get("status", "INCONCLUSIVE"),
            "stage": v.get("stage", "unknown"), "message": v.get("message", ""), "details": v.get("details"),
        }],
    }

def validate_module(module: str):
    if not module.isidentifier() or module.startswith("_"):
        raise HTTPException(
            status_code=400,
            detail="Module must be a valid Python identifier.",
        )
