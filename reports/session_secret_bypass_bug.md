# Simulation Vulnerability Report

- Timestamp: `2026-05-05T20:19:53`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/traces/policy_session_secret_bypass.json`
- Active bug defines: `BUG_SESSION_SECRET_BYPASS`
- Simulation exit code: `1`
- Result: **FAIL**

## Summary

The simulation detected one or more policy violations.

## Failing Checks

- `[FAIL] READ addr=0x10 priv=  USER expected rdata=0x00000000 error=1, got rdata=0xdeadbeef error=0`

## Passing Checks

- `[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0`
- `[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0`
- `[PASS] WRITE addr=0x20 data=0x12345678 priv=SECURE error=0`
- `[PASS] WRITE addr=0x24 data=0xb7910c22 priv=  USER error=0`
- `[PASS] READ addr=0x28 priv=  USER rdata=0x00000001 error=0`
- `[PASS] WRITE addr=0x2c data=0xcafe1234 priv=SECURE error=0`
- `[PASS] READ addr=0x2c priv=  USER rdata=0xcafe1234 error=0`
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

[TRACE 0] SECURE initializes AUTH_CHAL
[PASS] WRITE addr=0x20 data=0x12345678 priv=SECURE error=0

[TRACE 1] USER writes AUTH_RESP = AUTH_CHAL ^ AUTH_MAGIC to open session
[PASS] WRITE addr=0x24 data=0xb7910c22 priv=  USER error=0

[TRACE 2] USER confirms session is valid
[PASS] READ addr=0x28 priv=  USER rdata=0x00000001 error=0

[TRACE 3] SECURE writes PROTECTED_DATA
[PASS] WRITE addr=0x2c data=0xcafe1234 priv=SECURE error=0

[TRACE 4] USER reads PROTECTED_DATA because session is valid
[PASS] READ addr=0x2c priv=  USER rdata=0xcafe1234 error=0

[TRACE 5] SECURE initializes SECRET_KEY
[PASS] WRITE addr=0x10 data=0xdeadbeef priv=SECURE error=0

[TRACE 6] USER attempts to read SECRET_KEY despite valid session and should be blocked
[FAIL] READ addr=0x10 priv=  USER expected rdata=0x00000000 error=1, got rdata=0xdeadbeef error=0

========================================
Test summary: 9 checks, 1 failures
========================================
RESULT: FAIL
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:269: $finish called at 260000 (1ps)

```
