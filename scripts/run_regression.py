#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


TEST_CASES = [
    {
        "name": "clean_secret_read_trace",
        "trace": "traces/manual_secret_read.json",
        "bug_flags": [],
        "expected_exit": 0,
        "description": "Clean design should block SECRET_KEY reads.",
    },
    {
        "name": "bug_secret_read_trace",
        "trace": "traces/manual_secret_read.json",
        "bug_flags": ["--bug-secret-read"],
        "expected_exit": 1,
        "description": "BUG_SECRET_READ should leak SECRET_KEY and fail.",
    },
    {
        "name": "clean_user_debug_write_trace",
        "trace": "traces/user_debug_write.json",
        "bug_flags": [],
        "expected_exit": 0,
        "description": "Clean design should block USER writes to DEBUG_CTRL.",
    },
    {
        "name": "bug_user_debug_write_trace",
        "trace": "traces/user_debug_write.json",
        "bug_flags": ["--bug-user-debug-write"],
        "expected_exit": 1,
        "description": "BUG_USER_DEBUG_WRITE should allow USER debug enable and fail.",
    },
        {
        "name": "clean_debug_unlock_trace",
        "trace": "traces/debug_unlock_after_boot_lock.json",
        "bug_flags": [],
        "expected_exit": 0,
        "description": "Clean design should block DEBUG_CTRL changes after BOOT_LOCK.",
    },
    {
        "name": "bug_debug_unlock_trace",
        "trace": "traces/debug_unlock_after_boot_lock.json",
        "bug_flags": ["--bug-debug-unlock"],
        "expected_exit": 1,
        "description": "BUG_DEBUG_UNLOCK should allow DEBUG_CTRL changes after BOOT_LOCK and fail.",
    },
]


def run_case(case):
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_sim.py"),
        "--trace",
        case["trace"],
        *case["bug_flags"],
    ]

    print("=" * 80)
    print(f"[CASE] {case['name']}")
    print(f"[DESC] {case['description']}")
    print(f"[CMD]  {' '.join(cmd)}")
    print("=" * 80)

    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    print(result.stdout)

    passed_expectation = result.returncode == case["expected_exit"]

    if passed_expectation:
        print(f"[CASE RESULT] PASS expectation met, exit={result.returncode}")
    else:
        print(
            f"[CASE RESULT] FAIL expectation not met, "
            f"expected exit={case['expected_exit']}, got exit={result.returncode}"
        )

    return passed_expectation, result.returncode


def main():
    total = 0
    passed = 0

    results = []

    for case in TEST_CASES:
        total += 1
        ok, exit_code = run_case(case)

        if ok:
            passed += 1

        results.append(
            {
                "name": case["name"],
                "ok": ok,
                "expected_exit": case["expected_exit"],
                "actual_exit": exit_code,
            }
        )

    print("\n" + "=" * 80)
    print("REGRESSION SUMMARY")
    print("=" * 80)

    for result in results:
        status = "PASS" if result["ok"] else "FAIL"
        print(
            f"{status:4} | {result['name']:32} | "
            f"expected_exit={result['expected_exit']} actual_exit={result['actual_exit']}"
        )

    print("=" * 80)
    print(f"TOTAL: {passed}/{total} expectations met")

    if passed == total:
        print("REGRESSION RESULT: PASS")
        sys.exit(0)

    print("REGRESSION RESULT: FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()