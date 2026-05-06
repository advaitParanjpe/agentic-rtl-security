# Simulation Vulnerability Report

- Timestamp: `2026-05-05T18:17:05`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_secret_read.json`
- Active bug defines: `BUG_SECRET_READ`
- Simulation exit code: `1`
- Result: **FAIL**

## Summary

The simulation detected one or more policy violations.

## Failing Checks

- `[FAIL] READ addr=0x10 priv=  USER expected rdata=0x00000000 error=1, got rdata=0xdeadbeef error=0`

## Passing Checks

- `[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0`
- `[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0`
- `[PASS] WRITE addr=0x10 data=0xdeadbeef priv=SECURE error=0`

## Raw Simulation Log

```text
========================================
Starting mini_soc security testbench
========================================

[TEST] Public register access should work
[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0
[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0

[TEST] Running generated trace

[TRACE 0] SECURE initializes SECRET_KEY
[PASS] WRITE addr=0x10 data=0xdeadbeef priv=SECURE error=0

[TRACE 1] USER attempts to read SECRET_KEY and should be blocked
[FAIL] READ addr=0x10 priv=  USER expected rdata=0x00000000 error=1, got rdata=0xdeadbeef error=0

========================================
Test summary: 4 checks, 1 failures
========================================
RESULT: FAIL
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 160000 (1ps)

```
