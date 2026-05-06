# Simulation Vulnerability Report

- Timestamp: `2026-05-05T19:56:00`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_secret_read_attempt_1.json`
- Active bug defines: `None`
- Simulation exit code: `0`
- Result: **PASS**

## Summary

The simulation completed without detecting a policy violation.

## Failing Checks

- None

## Passing Checks

- `[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0`
- `[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0`
- `[PASS] WRITE addr=0x10 data=0xa5a5a5a5 priv=  USER error=1`
- `[PASS] READ addr=0x10 priv=  USER rdata=0x00000000 error=1`
- `[PASS] WRITE addr=0x08 data=0x00000001 priv=SECURE error=0`
- `[PASS] WRITE addr=0x0c data=0x00000001 priv=SECURE error=1`
- `[PASS] READ addr=0x0c priv=  USER rdata=0x00000000 error=0`

## Raw Simulation Log

```text
========================================
Starting mini_soc security testbench
========================================

[TEST] Public register access should work
[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0
[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0

[TEST] Running generated trace

[TRACE 0] USER attempts to write SECRET_KEY; clean design must deny the write and keep the secret unchanged.
[PASS] WRITE addr=0x10 data=0xa5a5a5a5 priv=  USER error=1

[TRACE 1] USER attempts to read SECRET_KEY after a denied write; clean design must not leak the secret or stale write data.
[PASS] READ addr=0x10 priv=  USER rdata=0x00000000 error=1

[TRACE 2] SECURE sets BOOT_LOCK[0] to 1 to activate the lockout condition for DEBUG_CTRL.
[PASS] WRITE addr=0x08 data=0x00000001 priv=SECURE error=0

[TRACE 3] After boot lock is set, SECURE attempts to modify DEBUG_CTRL; clean design must reject the write and leave DEBUG_CTRL unchanged.
[PASS] WRITE addr=0x0c data=0x00000001 priv=SECURE error=1

[TRACE 4] USER reads DEBUG_CTRL to confirm denied write did not modify it; since read access is allowed, the reset value should remain visible.
[PASS] READ addr=0x0c priv=  USER rdata=0x00000000 error=0

========================================
Test summary: 7 checks, 0 failures
========================================
RESULT: PASS
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 220000 (1ps)

```
