#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = REPO_ROOT / "build"
REPORT_DIR = REPO_ROOT / "reports"


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
        print(result.stdout)
        print(f"[ERROR] Command failed with return code {result.returncode}")
        sys.exit(result.returncode)

    return result


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def propose_trace(audit_brief, register_map, model, out_path, attempt, feedback_path=None):
    prompt_out = BUILD_DIR / f"audit_prompt_attempt_{attempt}.md"
    raw_out = BUILD_DIR / f"audit_raw_attempt_{attempt}.txt"

    cmd = [
        sys.executable,
        str(REPO_ROOT / "agent" / "audit_trace_proposer.py"),
        "--audit-brief",
        str(audit_brief),
        "--register-map",
        str(register_map),
        "--model",
        model,
        "--out",
        str(out_path),
        "--prompt-out",
        str(prompt_out),
        "--raw-out",
        str(raw_out),
    ]

    if feedback_path is not None:
        cmd += ["--feedback", str(feedback_path)]

    return run_cmd(cmd, allow_fail=True, quiet=True)


def validate_trace(trace_path):
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "validate_trace.py"),
        str(trace_path),
    ]

    return run_cmd(cmd, allow_fail=True, quiet=True)


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


def extract_fail_lines(sim_stdout):
    return [
        line for line in sim_stdout.splitlines()
        if "[FAIL]" in line
    ]


def extract_pass_fail_summary(sim_stdout):
    interesting = []

    for line in sim_stdout.splitlines():
        if (
            "[TRACE" in line
            or "[PASS]" in line
            or "[FAIL]" in line
            or "RESULT:" in line
            or "Test summary:" in line
        ):
            interesting.append(line)

    return "\n".join(interesting[-80:])


def write_validation_feedback(feedback_path, attempt, validation_stdout):
    lines = []
    lines.append(f"# Attempt {attempt} Feedback")
    lines.append("")
    lines.append("Trace validation failed.")
    lines.append("")
    lines.append("Validation output:")
    lines.append("")
    lines.append("```text")
    lines.append(validation_stdout.strip())
    lines.append("```")
    lines.append("")
    lines.append("Revise the trace so it satisfies the required JSON schema.")
    lines.append("Return only a valid JSON array.")

    feedback_path.write_text("\n".join(lines), encoding="utf-8")


def write_no_bug_feedback(feedback_path, attempt, sim_stdout):
    lines = []
    lines.append(f"# Attempt {attempt} Feedback")
    lines.append("")
    lines.append("The trace was valid, and the simulation completed without detecting a policy violation.")
    lines.append("")
    lines.append("This means the attempted trace did not expose a vulnerability.")
    lines.append("")
    lines.append("Compact simulation summary:")
    lines.append("")
    lines.append("```text")
    lines.append(extract_pass_fail_summary(sim_stdout))
    lines.append("```")
    lines.append("")
    lines.append("Revise the next trace to explore a different or deeper security state.")
    lines.append("")
    lines.append("Suggestions:")
    lines.append("- Try a different access-control strategy.")
    lines.append("- Explore setup followed by USER access.")
    lines.append("- Compare allowed and denied register accesses.")
    lines.append("- Add observation reads after important state changes.")
    lines.append("- Ensure expected_rdata and expected_error describe clean-design behavior.")

    sim_lower = sim_stdout.lower()

    if (
        "addr=0x28" in sim_lower
        and "rdata=0x00000001 error=0" in sim_lower
        and "addr=0x2c" in sim_lower
        and "error=0" in sim_lower
    ):
        lines.append("")
        lines.append("Session-lifecycle feedback:")
        lines.append("- The trace successfully established a valid session and confirmed session-gated access.")
        lines.append("- The next trace should not only test what access is granted.")
        lines.append("- Instead, test whether that access is revoked after a later state transition.")
        lines.append("- A useful pattern is:")
        lines.append("  1. establish a valid session")
        lines.append("  2. confirm SESSION_STATUS is 1")
        lines.append("  3. confirm PROTECTED_DATA is readable")
        lines.append("  4. perform a revocation-related transition")
        lines.append("  5. check that SESSION_STATUS clears")
        lines.append("  6. check that PROTECTED_DATA is denied")
        lines.append("- Possible revocation-related transitions include:")
        lines.append("  - writing an incorrect AUTH_RESP")
        lines.append("  - setting BOOT_LOCK[0]")
        lines.append("  - writing a new AUTH_CHAL value")

    feedback_path.write_text("\n".join(lines), encoding="utf-8")


def write_clean_fail_feedback(feedback_path, attempt, sim_stdout):
    lines = []
    lines.append(f"# Attempt {attempt} Feedback")
    lines.append("")
    lines.append("The trace caused a failure on the clean design.")
    lines.append("")
    lines.append("This usually means the expected clean behavior in the trace is wrong.")
    lines.append("")
    lines.append("Compact simulation summary:")
    lines.append("")
    lines.append("```text")
    lines.append(extract_pass_fail_summary(sim_stdout))
    lines.append("```")
    lines.append("")
    lines.append("Revise the trace so expected_rdata and expected_error match the clean design policy.")

    feedback_path.write_text("\n".join(lines), encoding="utf-8")


def write_final_finding(out_path, audit_name, trace_path, sim_report_path, sim_stdout):
    fail_lines = extract_fail_lines(sim_stdout)
    trace = load_json(trace_path)

    lines = []
    lines.append(f"# Vulnerability Finding: {audit_name}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(
        "The audit agent generated a trace that exposed a mismatch between "
        "expected clean security behavior and the simulated RTL behavior."
    )
    lines.append("")
    lines.append("## Failing Checks")
    lines.append("")

    if fail_lines:
        for line in fail_lines:
            lines.append(f"- `{line}`")
    else:
        lines.append("- No explicit `[FAIL]` lines were found, but the simulation returned a failing result.")

    lines.append("")
    lines.append("## Minimal Reproducing Trace")
    lines.append("")

    for idx, op in enumerate(trace):
        comment = op.get("comment", "")
        op_type = op.get("op")
        addr = op.get("addr")
        priv = op.get("priv")

        if op_type == "write":
            data = op.get("data")
            exp_err = op.get("expected_error")
            lines.append(
                f"{idx + 1}. WRITE addr `{addr}`, data `{data}`, priv `{priv}`, "
                f"expected_error `{exp_err}` — {comment}"
            )
        elif op_type == "read":
            exp_data = op.get("expected_rdata")
            exp_err = op.get("expected_error")
            lines.append(
                f"{idx + 1}. READ addr `{addr}`, priv `{priv}`, "
                f"expected_rdata `{exp_data}`, expected_error `{exp_err}` — {comment}"
            )
        else:
            lines.append(f"{idx + 1}. Unknown operation — {op}")

    lines.append("")
    lines.append("## Simulation Report")
    lines.append("")
    lines.append(f"- Detailed report: `{sim_report_path}`")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Review the failing checks above to identify which security property was violated. "
        "For access-control bugs, the key evidence is usually a read or write that should "
        "have been denied but was accepted by the RTL."
    )
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Limited-knowledge reflective RTL security audit agent."
    )

    parser.add_argument(
        "--audit-brief",
        type=Path,
        required=True,
        help="Limited audit brief shown to the LLM.",
    )

    parser.add_argument(
        "--register-map",
        type=Path,
        default=REPO_ROOT / "docs" / "register_map.md",
        help="Register map shown to the LLM.",
    )

    parser.add_argument(
        "--audit-name",
        default="session_access_control",
        help="Name used for report files.",
    )

    parser.add_argument(
        "--model",
        default="gpt-5.4-mini",
        help="OpenAI model to use.",
    )

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=5,
        help="Maximum number of trace proposal attempts.",
    )

    parser.add_argument(
        "--bug-flag",
        default=None,
        help="Simulator bug flag to enable, e.g. --bug-session-secret-bypass. Hidden from the LLM.",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Run against clean RTL. Overrides --bug-flag.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print full validation/simulation logs.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    audit_brief = args.audit_brief
    if not audit_brief.is_absolute():
        audit_brief = REPO_ROOT / audit_brief

    register_map = args.register_map
    if not register_map.is_absolute():
        register_map = REPO_ROOT / register_map

    bug_flag = None if args.clean else args.bug_flag

    print("=" * 80)
    print("LIMITED-KNOWLEDGE AUDIT AGENT")
    print("=" * 80)
    print(f"Audit name:     {args.audit_name}")
    print(f"Audit brief:    {audit_brief}")
    print(f"Register map:   {register_map}")
    print(f"Mode:           {'clean' if args.clean else 'bug-enabled'}")
    print(f"Bug flag:       {bug_flag if bug_flag else 'None'}")
    print(f"Model:          {args.model}")
    print(f"Max attempts:   {args.max_attempts}")
    print("=" * 80)
    print("Note: bug flag is used only by the simulator and is not shown to the LLM.")
    print("=" * 80)

    previous_feedback_path = None
    attempts = []
    detected = False
    final_finding_path = None

    for attempt in range(1, args.max_attempts + 1):
        trace_path = BUILD_DIR / f"audit_{args.audit_name}_attempt_{attempt}.json"
        feedback_path = BUILD_DIR / f"audit_feedback_{args.audit_name}_attempt_{attempt}.md"
        sim_report_path = REPORT_DIR / f"audit_{args.audit_name}_attempt_{attempt}.md"

        print(f"\n[ATTEMPT {attempt}] proposing trace")

        proposal_result = propose_trace(
            audit_brief=audit_brief,
            register_map=register_map,
            model=args.model,
            out_path=trace_path,
            attempt=attempt,
            feedback_path=previous_feedback_path,
        )

        if proposal_result.returncode != 0:
            print("[RESULT] Trace proposal failed.")
            if args.verbose:
                print(proposal_result.stdout)

            attempts.append(
                {
                    "attempt": attempt,
                    "proposal_ok": False,
                    "valid_trace": False,
                    "sim_returncode": None,
                    "detected": False,
                    "trace": str(trace_path),
                    "feedback": str(feedback_path),
                }
            )

            feedback_path.write_text(
                "# Attempt Feedback\n\nTrace proposal failed before validation.\n",
                encoding="utf-8",
            )
            previous_feedback_path = feedback_path
            continue

        print(f"[TRACE] {trace_path}")

        validation_result = validate_trace(trace_path)

        if validation_result.returncode != 0:
            print("[RESULT] Trace validation failed.")
            if args.verbose:
                print(validation_result.stdout)

            write_validation_feedback(
                feedback_path=feedback_path,
                attempt=attempt,
                validation_stdout=validation_result.stdout,
            )

            attempts.append(
                {
                    "attempt": attempt,
                    "proposal_ok": True,
                    "valid_trace": False,
                    "validation_returncode": validation_result.returncode,
                    "sim_returncode": None,
                    "detected": False,
                    "trace": str(trace_path),
                    "feedback": str(feedback_path),
                }
            )

            previous_feedback_path = feedback_path
            continue

        print("[RESULT] Trace validation passed.")
        print("[SIM] Running simulation")

        sim_result = run_sim(
            trace_path=trace_path,
            report_path=sim_report_path,
            bug_flag=bug_flag,
        )

        if args.verbose:
            print(sim_result.stdout)

        sim_failed = sim_result.returncode == 1
        sim_passed = sim_result.returncode == 0

        attempt_record = {
            "attempt": attempt,
            "proposal_ok": True,
            "valid_trace": True,
            "validation_returncode": validation_result.returncode,
            "sim_returncode": sim_result.returncode,
            "detected": False,
            "clean_passed": False,
            "trace": str(trace_path),
            "sim_report": str(sim_report_path),
            "feedback": str(feedback_path),
        }

        if args.clean:
            if sim_passed:
                print("[RESULT] Clean design passed this attempt.")
                attempt_record["clean_passed"] = True
                attempts.append(attempt_record)
                break

            print("[RESULT] Clean design failed unexpectedly.")
            write_clean_fail_feedback(
                feedback_path=feedback_path,
                attempt=attempt,
                sim_stdout=sim_result.stdout,
            )
            attempts.append(attempt_record)
            previous_feedback_path = feedback_path
            break

        if sim_failed:
            print("[CHECK] Bug-enabled RTL failed. Confirming against clean RTL...")

            clean_confirm_report_path = (
                REPORT_DIR / f"audit_{args.audit_name}_attempt_{attempt}_clean_confirm.md"
            )

            clean_confirm_result = run_sim(
                trace_path=trace_path,
                report_path=clean_confirm_report_path,
                bug_flag=None,
            )

            attempt_record["clean_confirm_returncode"] = clean_confirm_result.returncode
            attempt_record["clean_confirm_report"] = str(clean_confirm_report_path)

            if clean_confirm_result.returncode == 0:
                print("[RESULT] Confirmed vulnerability: clean passes, buggy RTL fails.")

                detected = True
                attempt_record["detected"] = True
                attempts.append(attempt_record)

                final_finding_path = REPORT_DIR / f"audit_{args.audit_name}_finding.md"
                write_final_finding(
                    out_path=final_finding_path,
                    audit_name=args.audit_name,
                    trace_path=trace_path,
                    sim_report_path=sim_report_path,
                    sim_stdout=sim_result.stdout,
                )

                break

            print("[RESULT] Trace also fails on clean RTL. Treating as invalid expectation, not a confirmed vulnerability.")

            write_clean_fail_feedback(
                feedback_path=feedback_path,
                attempt=attempt,
                sim_stdout=clean_confirm_result.stdout,
            )

            attempts.append(attempt_record)
            previous_feedback_path = feedback_path
            continue

        print("[RESULT] No vulnerability detected on this attempt.")
        write_no_bug_feedback(
            feedback_path=feedback_path,
            attempt=attempt,
            sim_stdout=sim_result.stdout,
        )

        attempts.append(attempt_record)
        previous_feedback_path = feedback_path

    summary = {
        "audit_name": args.audit_name,
        "audit_brief": str(audit_brief),
        "register_map": str(register_map),
        "mode": "clean" if args.clean else "bug-enabled",
        "bug_flag_hidden_from_llm": bug_flag,
        "model": args.model,
        "max_attempts": args.max_attempts,
        "detected": detected,
        "final_finding": str(final_finding_path) if final_finding_path else None,
        "attempts": attempts,
    }

    summary_path = REPORT_DIR / f"audit_{args.audit_name}_summary.json"
    write_json(summary_path, summary)

    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print("=" * 80)

    if args.clean:
        clean_ok = any(a.get("clean_passed") for a in attempts)
        print(f"Clean mode result: {'PASS' if clean_ok else 'FAIL'}")
        print(f"Summary: {summary_path}")
        print("=" * 80)
        sys.exit(0 if clean_ok else 1)

    if detected:
        print("Vulnerability detected.")
        print(f"Finding: {final_finding_path}")
        print(f"Summary: {summary_path}")
        print("=" * 80)
        sys.exit(0)

    print("No vulnerability detected within attempt budget.")
    print(f"Summary: {summary_path}")
    print("=" * 80)
    sys.exit(1)


if __name__ == "__main__":
    main()