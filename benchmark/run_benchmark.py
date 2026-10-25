"""BugTrace benchmark runner. Run from the project folder (bugtrace/).

  python benchmark/run_benchmark.py validate             # no AI: proves the bugs themselves are valid
  python benchmark/run_benchmark.py run --split tuning   # real AI repair runs (10 bugs)
  python benchmark/run_benchmark.py run --split heldout  # real AI repair runs (5 bugs), run once
  python benchmark/run_benchmark.py reproduce            # optional: can the AI write a valid test?
  python benchmark/run_benchmark.py report               # writes benchmark/results/RESULTS.md

Results are saved after every bug. If the AI quota runs out, just run the
same command again later: bugs that already have a VERIFIED/FAILED result are skipped.
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RESULTS = ROOT / "benchmark" / "results"

from benchmark.bugs import BUGS  # noqa: E402

COUNTED = ("VERIFIED", "FAILED")


def pick(split, ids):
    bugs = [b for b in BUGS if split == "all" or b["split"] == split]
    if ids:
        wanted = set(ids.split(","))
        bugs = [b for b in bugs if b["id"] in wanted]
    return bugs


def load(path):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def validate(bugs):
    from pipeline import run_pipeline
    from sandbox import run_tests

    bad = 0
    for b in bugs:
        r1 = run_tests({"calculator.py": b["source"], "test_calculator.py": b["test"]})
        r2 = run_tests({"calculator.py": b["source"], "test_regression.py": b["regression"]})
        r3 = run_pipeline(b["source"], b["reference"], b["test"], b["regression"])
        ok = r1["status"] == "FAILED" and r2["status"] == "PASSED" and r3["status"] == "VERIFIED"
        bad += not ok
        print(
            f"{'OK  ' if ok else 'BAD '}{b['id']} {b['category']}: "
            f"test on bug={r1['status']} (want FAILED), "
            f"regression on bug={r2['status']} (want PASSED), "
            f"reference fix={r3['status']} (want VERIFIED)"
        )
    print("\nAll bugs are valid." if not bad else f"\n{bad} bug(s) need fixing before any AI run.")
    return bad


def run(bugs, out, sleep):
    from repair_loop import repair  # importing this also loads your .env

    results = load(out)
    for b in bugs:
        old = results.get(b["id"])
        if old and old["status"] in COUNTED:
            print(f"skip {b['id']} (already {old['status']})")
            continue
        start = time.time()
        r = repair(b["source"], b["test"], b["error"], b["regression"], "calculator")
        attempts = r["attempts"]
        last = attempts[-1] if attempts else {}
        results[b["id"]] = {
            "id": b["id"],
            "split": b["split"],
            "category": b["category"],
            "status": r["status"],
            "stage": last.get("stage"),
            "attempts": len(attempts),
            "first_attempt_verified": bool(attempts) and attempts[0]["status"] == "VERIFIED",
            "seconds": round(time.time() - start, 1),
            "message": last.get("message", ""),
            "final_patch": last.get("patch"),
            "model": os.getenv("LLM_MODEL"),
            "ran_at": now(),
        }
        save(out, results)
        print(f"{b['id']} {b['category']}: {r['status']} (stage {last.get('stage')}, {len(attempts)} attempt(s))")
        if last.get("stage") == "ai" and "429" in str(last.get("message")):
            print("AI quota reached. Stop here and run the same command again later.")
            break
        time.sleep(sleep)


def reproduce(bugs, out, sleep):
    from ai_repair import propose_test
    from sandbox import run_tests

    results = load(out)
    for b in bugs:
        old = results.get(b["id"])
        if old and old["outcome"] != "api_error":
            print(f"skip {b['id']} (already {old['outcome']})")
            continue
        res = propose_test(b["source"], b["error"], b["expected"], "calculator")
        if not res["ok"]:
            outcome, note = "api_error", str(res["error"])[:200]
        else:
            t = res["data"]["reproduction_test"]
            on_bug = run_tests({"calculator.py": b["source"], "test_calculator.py": t})
            on_ref = run_tests({"calculator.py": b["reference"], "test_calculator.py": t})
            if on_bug["status"] == "FAILED" and on_ref["status"] == "PASSED":
                outcome, note = "valid", ""
            elif on_bug["status"] == "PASSED":
                outcome, note = "misses_bug", "generated test passes on the buggy code"
            elif on_ref["status"] == "FAILED":
                outcome, note = "different_expectation", "generated test fails on the reference fix"
            else:
                outcome, note = "inconclusive", f"bug={on_bug['status']} ref={on_ref['status']}"
        results[b["id"]] = {"id": b["id"], "split": b["split"], "outcome": outcome, "note": note,
                            "model": os.getenv("LLM_MODEL"), "ran_at": now()}
        save(out, results)
        print(f"{b['id']}: {outcome} {note}")
        time.sleep(sleep)


def report():
    rows = []
    for p in sorted(RESULTS.glob("*.json")):
        if p.stem != "reproduce":
            rows += list(load(p).values())
    lines = [
        "| ID | Category | Set | Result | Stopped at | Attempts | Seconds |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in sorted(rows, key=lambda r: r["id"]):
        lines.append(
            f"| {r['id']} | {r['category']} | {r['split']} | {r['status']} | "
            f"{r['stage']} | {r['attempts']} | {r['seconds']} |"
        )
    lines.append("")
    for split, label in (("tuning", "Tuning set"), ("heldout", "Held-out set")):
        sub = [r for r in rows if r["split"] == split]
        counted = [r for r in sub if r["status"] in COUNTED]
        verified = sum(r["status"] == "VERIFIED" for r in counted)
        first = sum(r["first_attempt_verified"] for r in counted)
        lines.append(
            f"- {label}: {verified}/{len(counted)} verified within 3 attempts; "
            f"{first}/{len(counted)} on the first attempt; "
            f"{len(sub) - len(counted)} not counted (API or Docker errors, rerun needed)."
        )
    models = sorted({r["model"] for r in rows if r.get("model")})
    lines.append(f"- Model(s) used: {', '.join(models) or 'unknown'}")

    rep = load(RESULTS / "reproduce.json")
    if rep:
        valid = sum(v["outcome"] == "valid" for v in rep.values())
        lines.append(f"- AI-written tests: {valid}/{len(rep)} were valid (fail on the bug, pass on the reference fix).")
        for v in rep.values():
            if v["outcome"] != "valid":
                lines.append(f"  - {v['id']}: {v['outcome']} {v['note']}")

    text = "\n".join(lines) + "\n"
    (RESULTS / "RESULTS.md").write_text(text, encoding="utf-8")
    print(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["validate", "run", "reproduce", "report"])
    ap.add_argument("--split", choices=["tuning", "heldout", "all"], default="tuning")
    ap.add_argument("--ids", help="comma-separated, for example B01,B02")
    ap.add_argument("--out", help="results file (default: benchmark/results/<split>.json)")
    ap.add_argument("--sleep", type=float, default=3, help="seconds to wait between bugs")
    a = ap.parse_args()

    if a.command == "report":
        report()
        return
    bugs = pick(a.split, a.ids)
    if a.command == "validate":
        sys.exit(1 if validate(bugs) else 0)
    if a.command == "run":
        run(bugs, Path(a.out) if a.out else RESULTS / f"{a.split}.json", a.sleep)
    if a.command == "reproduce":
        reproduce(bugs, Path(a.out) if a.out else RESULTS / "reproduce.json", a.sleep)


if __name__ == "__main__":
    main()
