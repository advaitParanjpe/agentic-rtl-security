#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path
import json

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = REPO_ROOT / "build"
FUZZ_TRACE = BUILD_DIR / "random_fuzz_trace.json"


BUG_CONFIGS = {
    "secret_read": "--bug-secret-read",
    "user_debug_write": "--bug-user-debug-write",
    "debug_unlock": "--bug-debug-unlock",
    "stale_rdata": "--bug-stale-rdata",
    "hidden_alias": "--bug-hidden-alias",
    "ro_write": "--bug-ro-write",
    "session_secret_bypass": "--bug-session-secret-bypass",
}


def run_cmd(cmd, quiet=False):
    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if not quiet:
        print(result.stdout)

    return result


def generate_random_trace(seed, ops):
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "gen_random_trace.py"),
        "--ops",
        str(ops),
        "--seed",
        str(seed),
        "--out",
        str(FUZZ_TRACE),
    ]

    result = run_cmd(cmd, quiet=True)

    if result.returncode != 0:
        print(result.stdout)
        raise RuntimeError(f"Trace generation failed for seed {seed}")


def run_bug_sim(bug_flag):
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_sim.py"),
        "--trace",
        str(FUZZ_TRACE),
        bug_flag,
    ]

    result = run_cmd(cmd, quiet=True)

    # run_sim.py returns:
    # 0 -> no failure observed
    # 1 -> testbench failure observed
    # For fuzzing a buggy design, returncode 1 means the bug was detected.
    detected = result.returncode == 1

    return detected, result.stdout


def main():
    parser = argparse.ArgumentParser(
        description="Run random MMIO fuzzing over many seeds."
    )

    parser.add_argument(
        "--bug",
        choices=BUG_CONFIGS.keys(),
        required=True,
        help="Bug configuration to fuzz.",
    )

    parser.add_argument(
        "--seeds",
        type=int,
        default=20,
        help="Number of random seeds to run.",
    )

    parser.add_argument(
        "--ops",
        type=int,
        default=50,
        help="Number of operations per random trace.",
    )

    parser.add_argument(
        "--start-seed",
        type=int,
        default=1,
        help="First seed value.",
    )

    parser.add_argument(
        "--show-detected-log",
        action="store_true",
        help="Print the full simulation log for detected cases.",
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional JSON output report path.",
    )

    args = parser.parse_args()

    BUILD_DIR.mkdir(exist_ok=True)

    bug_flag = BUG_CONFIGS[args.bug]

    detected_seeds = []
    missed_seeds = []

    print("=" * 80)
    print("RANDOM FUZZ RUN")
    print("=" * 80)
    print(f"Bug:          {args.bug}")
    print(f"Bug flag:     {bug_flag}")
    print(f"Seeds:        {args.seeds}")
    print(f"Ops/trace:    {args.ops}")
    print(f"Start seed:   {args.start_seed}")
    print("=" * 80)

    for i in range(args.seeds):
        seed = args.start_seed + i

        generate_random_trace(seed=seed, ops=args.ops)
        detected, sim_log = run_bug_sim(bug_flag)

        if detected:
            detected_seeds.append(seed)
            status = "DETECTED"
        else:
            missed_seeds.append(seed)
            status = "missed"

        print(f"seed={seed:<5} {status}")

        if detected and args.show_detected_log:
            print("\n" + "-" * 80)
            print(sim_log)
            print("-" * 80 + "\n")

    total = args.seeds
    found = len(detected_seeds)
    missed = len(missed_seeds)
    rate = 100.0 * found / total if total else 0.0

    print("\n" + "=" * 80)
    print("FUZZ SUMMARY")
    print("=" * 80)
    print(f"Bug:              {args.bug}")
    print(f"Ops per trace:    {args.ops}")
    print(f"Seeds tested:     {total}")
    print(f"Detected:         {found}")
    print(f"Missed:           {missed}")
    print(f"Detection rate:   {rate:.1f}%")
    print(f"Detected seeds:   {detected_seeds}")
    print(f"Missed seeds:     {missed_seeds}")
    print("=" * 80)

    report = {
        "bug": args.bug,
        "bug_flag": bug_flag,
        "ops_per_trace": args.ops,
        "seeds_tested": total,
        "start_seed": args.start_seed,
        "detected": found,
        "missed": missed,
        "detection_rate_percent": rate,
        "detected_seeds": detected_seeds,
        "missed_seeds": missed_seeds,
    }

    if args.out is not None:
        out_path = args.out

        if not out_path.is_absolute():
            out_path = REPO_ROOT / out_path

        out_path.parent.mkdir(parents=True, exist_ok=True)

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print(f"[DONE] Wrote fuzz report to {out_path}")

    # This script succeeds as long as the fuzz experiment ran.
    # It does not fail just because some seeds missed the bug.
    sys.exit(0)


if __name__ == "__main__":
    main()