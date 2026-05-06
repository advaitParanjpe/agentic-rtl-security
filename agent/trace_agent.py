#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = REPO_ROOT / "build"
REPORT_DIR = REPO_ROOT / "reports"


TARGET_CONFIGS = {
    "secret_read": {
        "bug_flag": "--bug-secret-read",
        "trace_target": "secret_read",
    },
    "user_debug_write": {
        "bug_flag": "--bug-user-debug-write",
        "trace_target": "user_debug_write",
    },
    "debug_unlock": {
        "bug_flag": "--bug-debug-unlock",
        "trace_target": "debug_unlock",
    },
    "ro_write": {
        "bug_flag": "--bug-ro-write",
        "trace_target": "ro_write",
    },
    "hidden_alias": {
        "bug_flag": "--bug-hidden-alias",
        "trace_target": "hidden_alias",
    },
}


def run_cmd(cmd, allow_fail=False):
    print(f"\n[CMD] {' '.join(str(x) for x in cmd)}")

    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    print(result.stdout)

    if result.returncode != 0 and not allow_fail:
        print(f"[ERROR] Command failed with return code {result.returncode}")
        sys.exit(result.returncode)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Lightweight policy-guided trace agent."
    )

    parser.add_argument(
        "--target",
        choices=TARGET_CONFIGS.keys(),
        required=True,
        help="Security target to attack.",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Run against clean design instead of enabling the matching bug.",
    )

    args = parser.parse_args()

    config = TARGET_CONFIGS[args.target]

    trace_path = BUILD_DIR / f"agent_trace_{args.target}.json"
    report_path = REPORT_DIR / f"agent_report_{args.target}.md"

    print("=" * 80)
    print("TRACE AGENT RUN")
    print("=" * 80)
    print(f"Target:      {args.target}")
    print(f"Trace path:  {trace_path}")
    print(f"Report path: {report_path}")
    print(f"Mode:        {'clean' if args.clean else 'bug-enabled'}")
    print("=" * 80)

    # Step 1: generate a policy-guided candidate trace.
    run_cmd(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "gen_policy_trace.py"),
            "--target",
            config["trace_target"],
            "--out",
            str(trace_path),
        ]
    )

    # Step 2: run simulation and write report.
    sim_cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_sim.py"),
        "--trace",
        str(trace_path),
        "--report",
        str(report_path),
    ]

    if not args.clean:
        sim_cmd.append(config["bug_flag"])

    sim_result = run_cmd(sim_cmd, allow_fail=True)

    detected = sim_result.returncode == 1

    print("=" * 80)
    print("AGENT SUMMARY")
    print("=" * 80)

    if args.clean:
        if sim_result.returncode == 0:
            print("Clean design passed as expected.")
        else:
            print("Clean design failed unexpectedly. Check the report.")
    else:
        if detected:
            print("Potential vulnerability detected.")
            print(f"Report: {report_path}")
        else:
            print("No vulnerability detected for this target.")
            print("This may mean the trace is insufficient or the bug is not exposed.")

    print("=" * 80)

    # For bug-enabled mode, return 0 if vulnerability was detected.
    # For clean mode, return 0 if clean design passed.
    if args.clean:
        sys.exit(0 if sim_result.returncode == 0 else 1)

    sys.exit(0 if detected else 1)


if __name__ == "__main__":
    main()