# Simulation Vulnerability Report

- Timestamp: `2026-05-05T18:40:33`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_user_debug_write_attempt_1.json`
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
- `[PASS] WRITE addr=0x0c data=0x00000001 priv=  USER error=1`
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

[TRACE 0] USER attempts to enable DEBUG_CTRL
[PASS] WRITE addr=0x0c data=0x00000001 priv=  USER error=1

[TRACE 1] USER checks that DEBUG_CTRL remained disabled
[PASS] READ addr=0x0c priv=  USER rdata=0x00000000 error=0

========================================
Test summary: 4 checks, 0 failures
========================================
RESULT: PASS
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 160000 (1ps)

```
