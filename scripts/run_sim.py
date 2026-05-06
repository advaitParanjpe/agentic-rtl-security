#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = REPO_ROOT / "build"

RTL_DIR = REPO_ROOT / "rtl"
TB_DIR = REPO_ROOT / "tb"

TOP_TB = "tb_mini_soc"

SOURCES = [
    RTL_DIR / "soc_pkg.sv",
    RTL_DIR / "mini_soc.sv",
    TB_DIR / "tb_mini_soc.sv",
]


BUG_DEFINES = {
    "bug_secret_read": "BUG_SECRET_READ",
    "bug_stale_rdata": "BUG_STALE_RDATA",
    "bug_debug_unlock": "BUG_DEBUG_UNLOCK",
    "bug_user_debug_write": "BUG_USER_DEBUG_WRITE",
    "bug_hidden_alias": "BUG_HIDDEN_ALIAS",
    "bug_ro_write": "BUG_RO_WRITE",
}


def run_cmd(cmd, cwd=None, allow_fail=False):
    print(f"\n[CMD] {' '.join(str(x) for x in cmd)}")

    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    print(result.stdout)

    if result.returncode != 0 and not allow_fail:
        print(f"[ERROR] Command failed with return code {result.returncode}")
        sys.exit(result.returncode)

    return result


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compile and run the mini_soc SystemVerilog testbench."
    )

    parser.add_argument(
        "--bug-secret-read",
        action="store_true",
        help="Enable BUG_SECRET_READ.",
    )

    parser.add_argument(
        "--bug-stale-rdata",
        action="store_true",
        help="Enable BUG_STALE_RDATA.",
    )

    parser.add_argument(
        "--bug-debug-unlock",
        action="store_true",
        help="Enable BUG_DEBUG_UNLOCK.",
    )

    parser.add_argument(
        "--bug-user-debug-write",
        action="store_true",
        help="Enable BUG_USER_DEBUG_WRITE.",
    )

    parser.add_argument(
        "--bug-hidden-alias",
        action="store_true",
        help="Enable BUG_HIDDEN_ALIAS.",
    )

    parser.add_argument(
        "--bug-ro-write",
        action="store_true",
        help="Enable BUG_RO_WRITE.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    BUILD_DIR.mkdir(exist_ok=True)

    active_bugs = [
        define_name
        for arg_name, define_name in BUG_DEFINES.items()
        if getattr(args, arg_name)
    ]

    if active_bugs:
        print("[INFO] Active bug defines:")
        for bug in active_bugs:
            print(f"  - {bug}")
    else:
        print("[INFO] No bug defines enabled. Running clean design.")

    sim_out = BUILD_DIR / f"{TOP_TB}.vvp"

    compile_cmd = [
        "iverilog",
        "-g2012",
        "-Wall",
        "-I",
        str(RTL_DIR),
        "-s",
        TOP_TB,
        "-o",
        str(sim_out),
    ]

    for bug in active_bugs:
        compile_cmd.append(f"-D{bug}=1")

    compile_cmd += [str(src) for src in SOURCES]

    compile_result = run_cmd(compile_cmd, cwd=REPO_ROOT)

    sim_result = run_cmd(["vvp", str(sim_out)], cwd=REPO_ROOT, allow_fail=True)

    if "RESULT: FAIL" in sim_result.stdout:
        print("[DONE] Simulation completed with test failures.")
        sys.exit(1)

    if "RESULT: PASS" in sim_result.stdout:
        print("[DONE] Simulation completed successfully.")
        sys.exit(0)

    print("[WARN] Simulation completed, but no RESULT line was found.")
    sys.exit(2)


if __name__ == "__main__":
    main()