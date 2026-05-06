# Simulation Vulnerability Report

- Timestamp: `2026-05-05T18:17:05`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_user_debug_write.json`
- Active bug defines: `BUG_USER_DEBUG_WRITE`
- Simulation exit code: `1`
- Result: **FAIL**

## Summary

The simulation detected one or more policy violations.

## Failing Checks

- `[FAIL] WRITE addr=0x0c expected error=1, got 0`
- `[FAIL] READ addr=0x0c priv=  USER expected rdata=0x00000000 error=0, got rdata=0x00000001 error=0`

## Passing Checks

- `[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0`
- `[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0`

## Raw Simulation Log

```text
========================================
Starting mini_soc security testbench
========================================

[TEST] Public register access should work
[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0
[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0

[TEST] Running generated trace

[TRACE 0] USER attempts to enable DEBUG_CTRL and should be blocked
[FAIL] WRITE addr=0x0c expected error=1, got 0

[TRACE 1] USER reads DEBUG_CTRL and should see it remains disabled
[FAIL] READ addr=0x0c priv=  USER expected rdata=0x00000000 error=0, got rdata=0x00000001 error=0

========================================
Test summary: 4 checks, 2 failures
========================================
RESULT: FAIL
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 160000 (1ps)

```
