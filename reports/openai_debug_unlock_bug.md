# Simulation Vulnerability Report

- Timestamp: `2026-05-05T19:02:40`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/openai_debug_unlock.json`
- Active bug defines: `BUG_DEBUG_UNLOCK`
- Simulation exit code: `1`
- Result: **FAIL**

## Summary

The simulation detected one or more policy violations.

## Failing Checks

- `[FAIL] WRITE addr=0x0c expected error=1, got 0`
- `[FAIL] READ addr=0x0c priv=SECURE expected rdata=0x00000000 error=0, got rdata=0xa5a5a5a5 error=0`

## Passing Checks

- `[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0`
- `[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0`
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

[TRACE 0] Set BOOT_LOCK[0] to 1 from a clean reset state so later DEBUG_CTRL writes should be blocked by policy.
[PASS] WRITE addr=0x08 data=0x00000001 priv=SECURE error=0

[TRACE 1] Attempt to modify DEBUG_CTRL after boot lock is asserted; clean design must reject this and leave DEBUG_CTRL unchanged.
[FAIL] WRITE addr=0x0c expected error=1, got 0

[TRACE 2] Confirm the prior blocked write did not change DEBUG_CTRL; after reset and failed write, the register should remain at its reset value.
[FAIL] READ addr=0x0c priv=SECURE expected rdata=0x00000000 error=0, got rdata=0xa5a5a5a5 error=0

========================================
Test summary: 5 checks, 2 failures
========================================
RESULT: FAIL
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 180000 (1ps)

```
