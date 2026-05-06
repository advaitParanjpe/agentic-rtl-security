# Simulation Vulnerability Report

- Timestamp: `2026-05-05T21:29:36`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/traces/policy_chal_rotate_does_not_clear_session.json`
- Active bug defines: `BUG_CHAL_ROTATE_DOES_NOT_CLEAR_SESSION`
- Simulation exit code: `1`
- Result: **FAIL**

## Summary

The simulation detected one or more policy violations.

## Failing Checks

- `[FAIL] READ addr=0x28 priv=  USER expected rdata=0x00000000 error=0, got rdata=0x00000001 error=0`
- `[FAIL] READ addr=0x2c priv=  USER expected rdata=0x00000000 error=1, got rdata=0xbeef1234 error=0`

## Passing Checks

- `[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0`
- `[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0`
- `[PASS] WRITE addr=0x20 data=0x12345678 priv=SECURE error=0`
- `[PASS] WRITE addr=0x24 data=0xb7910c22 priv=  USER error=0`
- `[PASS] READ addr=0x28 priv=  USER rdata=0x00000001 error=0`
- `[PASS] READ addr=0x2c priv=  USER rdata=0xbeef1234 error=0`
- `[PASS] WRITE addr=0x20 data=0xaabbccdd priv=SECURE error=0`

## Raw Simulation Log

```text
========================================
Starting mini_soc security testbench
========================================

[TEST] Public register access should work
[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0
[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0

[TEST] Running generated trace

[TRACE 0] SECURE initializes AUTH_CHAL
[PASS] WRITE addr=0x20 data=0x12345678 priv=SECURE error=0

[TRACE 1] USER writes correct AUTH_RESP to establish session
[PASS] WRITE addr=0x24 data=0xb7910c22 priv=  USER error=0

[TRACE 2] USER confirms session is valid
[PASS] READ addr=0x28 priv=  USER rdata=0x00000001 error=0

[TRACE 3] USER confirms PROTECTED_DATA is readable while session is valid
[PASS] READ addr=0x2c priv=  USER rdata=0xbeef1234 error=0

[TRACE 4] SECURE rotates AUTH_CHAL, which should invalidate the existing session
[PASS] WRITE addr=0x20 data=0xaabbccdd priv=SECURE error=0

[TRACE 5] USER confirms session was cleared after AUTH_CHAL rotation
[FAIL] READ addr=0x28 priv=  USER expected rdata=0x00000000 error=0, got rdata=0x00000001 error=0

[TRACE 6] USER should no longer read PROTECTED_DATA after challenge rotation clears session
[FAIL] READ addr=0x2c priv=  USER expected rdata=0x00000000 error=1, got rdata=0xbeef1234 error=0

========================================
Test summary: 9 checks, 2 failures
========================================
RESULT: FAIL
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:284: $finish called at 260000 (1ps)

```
