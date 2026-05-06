#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path
import datetime

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = REPO_ROOT / "build"

RTL_DIR = REPO_ROOT / "rtl"
TB_DIR = REPO_ROOT / "tb"
TRACE_DIR = REPO_ROOT / "traces"

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
    "bug_session_secret_bypass": "BUG_SESSION_SECRET_BYPASS",
    "bug_failed_auth_does_not_clear_session": "BUG_FAILED_AUTH_DOES_NOT_CLEAR_SESSION",
    "bug_boot_lock_session_persist": "BUG_BOOT_LOCK_SESSION_PERSIST",
    "bug_chal_rotate_does_not_clear_session": "BUG_CHAL_ROTATE_DOES_NOT_CLEAR_SESSION",
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
        description="Generate trace, compile, and run the mini_soc SystemVerilog testbench."
    )

    parser.add_argument(
        "--trace",
        type=Path,
        default=TRACE_DIR / "manual_secret_read.json",
        help="Path to JSON trace file.",
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

    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Optional Markdown report path for simulation result.",
    )

    parser.add_argument(
        "--bug-session-secret-bypass",
        action="store_true",
        help="Enable BUG_SESSION_SECRET_BYPASS.",
    )

    parser.add_argument(
        "--bug-failed-auth-does-not-clear-session",
        action="store_true",
        help="Enable BUG_FAILED_AUTH_DOES_NOT_CLEAR_SESSION.",
    )

    parser.add_argument(
        "--bug-boot-lock-session-persist",
        action="store_true",
        help="Enable BUG_BOOT_LOCK_SESSION_PERSIST.",
    )

    parser.add_argument(
        "--bug-chal-rotate-does-not-clear-session",
        action="store_true",
        help="Enable BUG_CHAL_ROTATE_DOES_NOT_CLEAR_SESSION.",
    )

    return parser.parse_args()

def write_report(report_path, trace_path, active_bugs, sim_stdout, sim_exit_code):
    if not report_path.is_absolute():
        report_path = REPO_ROOT / report_path

    report_path.parent.mkdir(parents=True, exist_ok=True)

    result = "FAIL" if "RESULT: FAIL" in sim_stdout else "PASS"

    fail_lines = [
        line for line in sim_stdout.splitlines()
        if "[FAIL]" in line
    ]

    pass_lines = [
        line for line in sim_stdout.splitlines()
        if "[PASS]" in line
    ]

    timestamp = datetime.datetime.now().isoformat(timespec="seconds")

    bug_text = ", ".join(active_bugs) if active_bugs else "None"

    lines = []
    lines.append("# Simulation Vulnerability Report")
    lines.append("")
    lines.append(f"- Timestamp: `{timestamp}`")
    lines.append(f"- Trace: `{trace_path}`")
    lines.append(f"- Active bug defines: `{bug_text}`")
    lines.append(f"- Simulation exit code: `{sim_exit_code}`")
    lines.append(f"- Result: **{result}**")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    if result == "FAIL":
        lines.append("The simulation detected one or more policy violations.")
    else:
        lines.append("The simulation completed without detecting a policy violation.")

    lines.append("")
    lines.append("## Failing Checks")
    lines.append("")

    if fail_lines:
        for line in fail_lines:
            lines.append(f"- `{line}`")
    else:
        lines.append("- None")

    lines.append("")
    lines.append("## Passing Checks")
    lines.append("")

    for line in pass_lines:
        lines.append(f"- `{line}`")

    lines.append("")
    lines.append("## Raw Simulation Log")
    lines.append("")
    lines.append("```text")
    lines.append(sim_stdout)
    lines.append("```")
    lines.append("")

    report_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"[DONE] Wrote report to {report_path}")

def main():
    args = parse_args()

    BUILD_DIR.mkdir(exist_ok=True)

    trace_path = args.trace

    if not trace_path.is_absolute():
        trace_path = REPO_ROOT / trace_path

    if not trace_path.exists():
        print(f"[ERROR] Trace file does not exist: {trace_path}")
        sys.exit(1)
    
    run_cmd(
    [
        sys.executable,
        str(REPO_ROOT / "scripts" / "validate_trace.py"),
        str(trace_path),
    ],
    cwd=REPO_ROOT,
    )

    generated_trace = BUILD_DIR / "generated_trace.svh"

    run_cmd(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "gen_trace.py"),
            str(trace_path),
            "--out",
            str(generated_trace),
        ],
        cwd=REPO_ROOT,
    )

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

    run_cmd(compile_cmd, cwd=REPO_ROOT)

    sim_result = run_cmd(["vvp", str(sim_out)], cwd=REPO_ROOT, allow_fail=True)

    sim_exit_code = 2

    if "RESULT: FAIL" in sim_result.stdout:
        print("[DONE] Simulation completed with test failures.")
        sim_exit_code = 1
    elif "RESULT: PASS" in sim_result.stdout:
        print("[DONE] Simulation completed successfully.")
        sim_exit_code = 0
    else:
        print("[WARN] Simulation completed, but no RESULT line was found.")
        sim_exit_code = 2

    if args.report is not None:
        write_report(
            report_path=args.report,
            trace_path=trace_path,
            active_bugs=active_bugs,
            sim_stdout=sim_result.stdout,
            sim_exit_code=sim_exit_code,
        )

    sys.exit(sim_exit_code)


if __name__ == "__main__":
    main()