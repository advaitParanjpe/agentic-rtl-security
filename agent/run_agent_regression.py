#!/usr/bin/env python3

import argparse
import json
import os
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

DEFAULT_PROPOSAL_MODES = [
    "policy",
    "mock-llm",
]


def run_target(target, proposal_mode, clean=False, max_attempts=4, model=None):
    cmd = [
        sys.executable,
        str(REPO_ROOT / "agent" / "trace_agent.py"),
        "--target",
        target,
        "--proposal-mode",
        proposal_mode,
        "--max-attempts",
        str(max_attempts),
    ]

    if proposal_mode == "openai" and model is not None:
        cmd += ["--model", model]

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


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run iterative trace-agent regression across proposal modes."
    )

    parser.add_argument(
        "--include-openai",
        action="store_true",
        help="Include OpenAI proposal mode. Requires OPENAI_API_KEY.",
    )

    parser.add_argument(
        "--model",
        default="gpt-5.4-mini",
        help="OpenAI model to use when --include-openai is set.",
    )

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=4,
        help="Max attempts per target.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    proposal_modes = list(DEFAULT_PROPOSAL_MODES)

    if args.include_openai:
        if not os.environ.get("OPENAI_API_KEY"):
            print("[ERROR] --include-openai requires OPENAI_API_KEY to be set.")
            sys.exit(1)

        proposal_modes.append("openai")

    results = []

    print("=" * 80)
    print("ITERATIVE AGENT REGRESSION")
    print("=" * 80)
    print(f"Max attempts per target: {args.max_attempts}")
    print(f"Proposal modes: {', '.join(proposal_modes)}")
    if args.include_openai:
        print(f"OpenAI model: {args.model}")
    print("=" * 80)

    for proposal_mode in proposal_modes:
        print("\n" + "#" * 80)
        print(f"PROPOSAL MODE: {proposal_mode}")
        print("#" * 80)

        for target in TARGETS:
            print(f"\n[BUG MODE] target={target} proposal_mode={proposal_mode}")
            bug_result = run_target(
                target=target,
                proposal_mode=proposal_mode,
                clean=False,
                max_attempts=args.max_attempts,
                model=args.model,
            )
            bug_ok = bug_result.returncode == 0

            print(f"returncode={bug_result.returncode}")
            print("status=" + ("DETECTED" if bug_ok else "MISSED"))

            print(f"\n[CLEAN MODE] target={target} proposal_mode={proposal_mode}")
            clean_result = run_target(
                target=target,
                proposal_mode=proposal_mode,
                clean=True,
                max_attempts=args.max_attempts,
                model=args.model,
            )
            clean_ok = clean_result.returncode == 0

            print(f"returncode={clean_result.returncode}")
            print("status=" + ("PASS" if clean_ok else "UNEXPECTED_FAIL"))

            results.append(
                {
                    "proposal_mode": proposal_mode,
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
            f"{status:4} | {r['proposal_mode']:8} | {r['target']:20} | "
            f"bug_detected={r['bug_detected']} clean_passed={r['clean_passed']}"
        )

    summary = {
        "max_attempts": args.max_attempts,
        "proposal_modes": proposal_modes,
        "include_openai": args.include_openai,
        "openai_model": args.model if args.include_openai else None,
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