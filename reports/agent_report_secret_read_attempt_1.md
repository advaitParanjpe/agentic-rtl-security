# Simulation Vulnerability Report

- Timestamp: `2026-05-05T19:58:26`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_secret_read_attempt_1.json`
- Active bug defines: `BUG_SECRET_READ`
- Simulation exit code: `1`
- Result: **FAIL**

## Summary

The simulation detected one or more policy violations.

## Failing Checks

- `[FAIL] READ addr=0x10 priv=  USER expected rdata=0x00000000 error=1, got rdata=0x00000000 error=0`
- `[FAIL] READ addr=0x10 priv=SECURE expected rdata=0x00000000 error=1, got rdata=0x00000000 error=0`

## Passing Checks

- `[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0`
- `[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0`
- `[PASS] WRITE addr=0x10 data=0xa5a5a5a5 priv=  USER error=1`

## Raw Simulation Log

```text
========================================
Starting mini_soc security testbench
========================================

[TEST] Public register access should work
[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0
[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0

[TEST] Running generated trace

[TRACE 0] Attempt to read SECRET_KEY from USER mode; clean design must deny access and return zero without leaking any secret.
[FAIL] READ addr=0x10 priv=  USER expected rdata=0x00000000 error=1, got rdata=0x00000000 error=0

[TRACE 1] Attempt to write SECRET_KEY from USER mode; clean design must reject the write and preserve the protected value.
[PASS] WRITE addr=0x10 data=0xa5a5a5a5 priv=  USER error=1

[TRACE 2] Attempt to read SECRET_KEY from SECURE mode; clean design must also deny readback because the secret is write-only.
[FAIL] READ addr=0x10 priv=SECURE expected rdata=0x00000000 error=1, got rdata=0x00000000 error=0

========================================
Test summary: 5 checks, 2 failures
========================================
RESULT: FAIL
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 180000 (1ps)

```
