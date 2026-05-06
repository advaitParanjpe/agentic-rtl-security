# Simulation Vulnerability Report

- Timestamp: `2026-05-05T18:29:42`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/mock_llm_debug_unlock.json`
- Active bug defines: `BUG_DEBUG_UNLOCK`
- Simulation exit code: `1`
- Result: **FAIL**

## Summary

The simulation detected one or more policy violations.

## Failing Checks

- `[FAIL] WRITE addr=0x0c expected error=1, got 0`
- `[FAIL] READ addr=0x0c priv=  USER expected rdata=0x00000001 error=0, got rdata=0x00000000 error=0`

## Passing Checks

- `[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0`
- `[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0`
- `[PASS] WRITE addr=0x0c data=0x00000001 priv=SECURE error=0`
- `[PASS] WRITE addr=0x08 data=0x00000001 priv=SECURE error=0`

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

[TRACE 2] SECURE attempts to modify DEBUG_CTRL after BOOT_LOCK
[FAIL] WRITE addr=0x0c expected error=1, got 0

[TRACE 3] USER observes that DEBUG_CTRL preserved its locked value
[FAIL] READ addr=0x0c priv=  USER expected rdata=0x00000001 error=0, got rdata=0x00000000 error=0

========================================
Test summary: 6 checks, 2 failures
========================================
RESULT: FAIL
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 200000 (1ps)

```
