#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

TARGETS = [
    "secret_read",
    "user_debug_write",
    "debug_unlock",
    "ro_write",
    "hidden_alias",
]


def run_target(target, clean=False):
    cmd = [
        sys.executable,
        str(REPO_ROOT / "agent" / "trace_agent.py"),
        "--target",
        target,
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
    results = []

    print("=" * 80)
    print("AGENT REGRESSION")
    print("=" * 80)

    for target in TARGETS:
        print(f"\n[BUG MODE] target={target}")
        bug_result = run_target(target, clean=False)
        bug_ok = bug_result.returncode == 0

        print(f"returncode={bug_result.returncode}")
        print("status=" + ("DETECTED" if bug_ok else "MISSED"))

        print(f"\n[CLEAN MODE] target={target}")
        clean_result = run_target(target, clean=True)
        clean_ok = clean_result.returncode == 0

        print(f"returncode={clean_result.returncode}")
        print("status=" + ("PASS" if clean_ok else "UNEXPECTED_FAIL"))

        results.append(
            {
                "target": target,
                "bug_detected": bug_ok,
                "clean_passed": clean_ok,
            }
        )

    print("\n" + "=" * 80)
    print("AGENT REGRESSION SUMMARY")
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

    print("=" * 80)

    if all_ok:
        print("AGENT REGRESSION RESULT: PASS")
        sys.exit(0)

    print("AGENT REGRESSION RESULT: FAIL")
    sys.exit(1)


if __name__ == "__main__":
    main()