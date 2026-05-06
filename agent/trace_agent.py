#!/usr/bin/env python3

import argparse
import json
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


def run_cmd(cmd, allow_fail=False, quiet=False):
    if not quiet:
        print(f"\n[CMD] {' '.join(str(x) for x in cmd)}")

    result = subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    if not quiet:
        print(result.stdout)

    if result.returncode != 0 and not allow_fail:
        print(f"[ERROR] Command failed with return code {result.returncode}")
        sys.exit(result.returncode)

    return result


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def generate_base_policy_trace(target, out_path):
    run_cmd(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "gen_policy_trace.py"),
            "--target",
            target,
            "--out",
            str(out_path),
        ],
        quiet=True,
    )


def mutate_trace(base_trace, attempt):
    """
    Generate small deterministic variants of the base trace.

    This is deliberately simple for now. Later, this mutation function can be
    replaced by an LLM-based trace proposal step.
    """

    trace = json.loads(json.dumps(base_trace))

    if attempt == 1:
        return trace, "base_policy_trace"

    if attempt == 2:
        # Add a harmless public register access before the attack.
        prefix = [
            {
                "op": "write",
                "addr": "0x14",
                "data": "0xA5A5A5A5",
                "priv": "user",
                "expected_error": 0,
                "comment": "Mutation prefix: USER writes PUBLIC_DATA",
            },
            {
                "op": "read",
                "addr": "0x14",
                "priv": "user",
                "expected_rdata": "0xA5A5A5A5",
                "expected_error": 0,
                "comment": "Mutation prefix: USER reads PUBLIC_DATA",
            },
        ]

        return prefix + trace, "prefix_public_access"

    if attempt == 3:
        # Add invalid accesses before the attack.
        prefix = [
            {
                "op": "read",
                "addr": "0x20",
                "priv": "user",
                "expected_rdata": "0x00000000",
                "expected_error": 1,
                "comment": "Mutation prefix: USER reads invalid address",
            },
            {
                "op": "write",
                "addr": "0x24",
                "data": "0x11111111",
                "priv": "secure",
                "expected_error": 1,
                "comment": "Mutation prefix: SECURE writes invalid address",
            },
        ]

        return prefix + trace, "prefix_invalid_accesses"

    if attempt == 4:
        # Add only a stable VERSION read. This should be safe across targets
        # because VERSION is read-only and should remain 0x00000001.
        suffix = [
            {
                "op": "read",
                "addr": "0x1C",
                "priv": "user",
                "expected_rdata": "0x00000001",
                "expected_error": 0,
                "comment": "Mutation suffix: USER observes VERSION",
            },
        ]

        return trace + suffix, "suffix_version_read"

    # Final fallback: return base trace again.
    return trace, "fallback_base_policy_trace"


def run_sim(trace_path, report_path, bug_flag=None):
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "run_sim.py"),
        "--trace",
        str(trace_path),
        "--report",
        str(report_path),
    ]

    if bug_flag is not None:
        cmd.append(bug_flag)

    return run_cmd(cmd, allow_fail=True, quiet=True)


def main():
    parser = argparse.ArgumentParser(
        description="Iterative lightweight policy-guided trace agent."
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

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=4,
        help="Maximum number of candidate traces to try.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full simulation output for each attempt.",
    )

    args = parser.parse_args()

    config = TARGET_CONFIGS[args.target]

    base_trace_path = BUILD_DIR / f"agent_base_trace_{args.target}.json"
    final_report_path = REPORT_DIR / f"agent_report_{args.target}.md"

    bug_flag = None if args.clean else config["bug_flag"]

    print("=" * 80)
    print("ITERATIVE TRACE AGENT RUN")
    print("=" * 80)
    print(f"Target:        {args.target}")
    print(f"Mode:          {'clean' if args.clean else 'bug-enabled'}")
    print(f"Max attempts:  {args.max_attempts}")
    print(f"Bug flag:      {bug_flag if bug_flag else 'None'}")
    print("=" * 80)

    # Step 1: generate the base policy trace.
    generate_base_policy_trace(
        target=config["trace_target"],
        out_path=base_trace_path,
    )

    base_trace = load_json(base_trace_path)

    attempt_results = []
    detected = False
    best_report_path = None

    for attempt in range(1, args.max_attempts + 1):
        candidate_trace, strategy = mutate_trace(base_trace, attempt)

        trace_path = BUILD_DIR / f"agent_trace_{args.target}_attempt_{attempt}.json"
        report_path = REPORT_DIR / f"agent_report_{args.target}_attempt_{attempt}.md"

        write_json(trace_path, candidate_trace)

        print(f"\n[ATTEMPT {attempt}] strategy={strategy}")
        print(f"[TRACE] {trace_path}")
        print(f"[REPORT] {report_path}")

        sim_result = run_sim(
            trace_path=trace_path,
            report_path=report_path,
            bug_flag=bug_flag,
        )

        if args.verbose:
            print(sim_result.stdout)

        attempt_detected = sim_result.returncode == 1
        attempt_clean_passed = sim_result.returncode == 0

        attempt_results.append(
            {
                "attempt": attempt,
                "strategy": strategy,
                "trace": str(trace_path),
                "report": str(report_path),
                "returncode": sim_result.returncode,
                "detected": attempt_detected,
                "clean_passed": attempt_clean_passed,
            }
        )

        if args.clean:
            if not attempt_clean_passed:
                print("[RESULT] Clean design failed unexpectedly.")
                best_report_path = report_path
                break

            print("[RESULT] Clean design passed this attempt.")

        else:
            if attempt_detected:
                print("[RESULT] Vulnerability detected.")
                detected = True
                best_report_path = report_path
                break

            print("[RESULT] No vulnerability detected on this attempt.")

    # Write agent summary JSON.
    summary_path = REPORT_DIR / f"agent_summary_{args.target}.json"

    summary = {
        "target": args.target,
        "mode": "clean" if args.clean else "bug-enabled",
        "max_attempts": args.max_attempts,
        "bug_flag": bug_flag,
        "detected": detected,
        "best_report": str(best_report_path) if best_report_path else None,
        "attempts": attempt_results,
    }

    write_json(summary_path, summary)

    print("\n" + "=" * 80)
    print("AGENT SUMMARY")
    print("=" * 80)

    if args.clean:
        all_clean_passed = all(r["clean_passed"] for r in attempt_results)

        if all_clean_passed:
            print("Clean design passed all attempted traces.")
        else:
            print("Clean design failed at least one attempted trace.")

        print(f"Summary: {summary_path}")
        print("=" * 80)
        sys.exit(0 if all_clean_passed else 1)

    if detected:
        print("Potential vulnerability detected.")
        print(f"Best report: {best_report_path}")
        print(f"Summary:     {summary_path}")
        print("=" * 80)
        sys.exit(0)

    print("No vulnerability detected within attempt budget.")
    print(f"Summary: {summary_path}")
    print("=" * 80)
    sys.exit(1)


if __name__ == "__main__":
    main()