#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = REPO_ROOT / "reports"

TARGETS = [
    "secret_read",
    "user_debug_write",
    "debug_unlock",
    "ro_write",
    "hidden_alias",
]


def run_target(target, clean=False, max_attempts=4):
    cmd = [
        sys.executable,
        str(REPO_ROOT / "agent" / "trace_agent.py"),
        "--target",
        target,
        "--max-attempts",
        str(max_attempts),
    ]

    if clean:
        cmd.append("--clean")

    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    return result


def main():
    max_attempts = 4
    results = []

    print("=" * 80)
    print("ITERATIVE AGENT REGRESSION")
    print("=" * 80)
    print(f"Max attempts per target: {max_attempts}")
    print("=" * 80)

    for target in TARGETS:
        print(f"\n[BUG MODE] target={target}")
        bug_result = run_target(target, clean=False, max_attempts=max_attempts)
        bug_ok = bug_result.returncode == 0

        print(f"returncode={bug_result.returncode}")
        print("status=" + ("DETECTED" if bug_ok else "MISSED"))

        print(f"\n[CLEAN MODE] target={target}")
        clean_result = run_target(target, clean=True, max_attempts=max_attempts)
        clean_ok = clean_result.returncode == 0

        print(f"returncode={clean_result.returncode}")
        print("status=" + ("PASS" if clean_ok else "UNEXPECTED_FAIL"))

        results.append(
            {
                "target": target,
                "bug_detected": bug_ok,
                "clean_passed": clean_ok,
                "bug_returncode": bug_result.returncode,
                "clean_returncode": clean_result.returncode,
            }
        )

    print("\n" + "=" * 80)
    print("ITERATIVE AGENT REGRESSION SUMMARY")
    print("=" * 80)

    all_ok = True

    for r in results:
        ok = r["bug_detected"] and r["clean_passed"]
        all_ok = all_ok and ok

        status = "PASS" if ok else "FAIL"

        print(
            f"{status:4} | {r['target']:20} | "
            f"bug_detected={r['bug_detected']} clean_passed={r['clean_passed']}"
        )

    summary = {
        "max_attempts": max_attempts,
        "results": results,
        "all_passed": all_ok,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = REPORT_DIR / "agent_regression_summary.json"

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=" * 80)
    print(f"Summary JSON: {summary_path}")

    if all_ok:
        print("ITERATIVE AGENT REGRESSION RESULT: PASS")
        sys.exit(0)

    print("ITERATIVE AGENT REGRESSION RESULT: FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()