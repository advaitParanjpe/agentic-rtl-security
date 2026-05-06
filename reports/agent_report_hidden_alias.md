# Simulation Vulnerability Report

- Timestamp: `2026-05-05T18:17:06`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_hidden_alias.json`
- Active bug defines: `BUG_HIDDEN_ALIAS`
- Simulation exit code: `1`
- Result: **FAIL**

## Summary

The simulation detected one or more policy violations.

## Failing Checks

- `[FAIL] READ addr=0x20 priv=  USER expected rdata=0x00000000 error=1, got rdata=0xcafebabe error=0`

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

[TRACE 0] USER reads invalid alias address and should not observe hidden debug state
[FAIL] READ addr=0x20 priv=  USER expected rdata=0x00000000 error=1, got rdata=0xcafebabe error=0

========================================
Test summary: 3 checks, 1 failures
========================================
RESULT: FAIL
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 140000 (1ps)

```
