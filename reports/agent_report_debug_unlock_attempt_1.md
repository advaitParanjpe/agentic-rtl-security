# Simulation Vulnerability Report

- Timestamp: `2026-05-05T18:25:13`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_debug_unlock_attempt_1.json`
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
- `[PASS] WRITE addr=0x0c data=0x00000001 priv=SECURE error=0`
- `[PASS] WRITE addr=0x08 data=0x00000001 priv=SECURE error=0`
- `[PASS] WRITE addr=0x0c data=0x00000000 priv=SECURE error=1`
- `[PASS] READ addr=0x0c priv=  USER rdata=0x00000001 error=0`

## Raw Simulation Log

```text
========================================
Starting mini_soc security testbench
========================================

[TEST] Public register access should work
[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0
[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0

[TEST] Running generated trace

[TRACE 0] SECURE enables DEBUG_CTRL before BOOT_LOCK
[PASS] WRITE addr=0x0c data=0x00000001 priv=SECURE error=0

[TRACE 1] SECURE sets BOOT_LOCK
[PASS] WRITE addr=0x08 data=0x00000001 priv=SECURE error=0

[TRACE 2] SECURE attempts to modify DEBUG_CTRL after BOOT_LOCK and should be blocked
[PASS] WRITE addr=0x0c data=0x00000000 priv=SECURE error=1

[TRACE 3] USER reads DEBUG_CTRL and should see original value preserved
[PASS] READ addr=0x0c priv=  USER rdata=0x00000001 error=0

========================================
Test summary: 6 checks, 0 failures
========================================
RESULT: PASS
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 200000 (1ps)

```
