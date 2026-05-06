# Simulation Vulnerability Report

- Timestamp: `2026-05-05T20:24:52`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_session_secret_bypass_attempt_1.json`
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
- `[PASS] WRITE addr=0x20 data=0x13579bdf priv=SECURE error=0`
- `[PASS] WRITE addr=0x24 data=0xb6f2c185 priv=  USER error=0`
- `[PASS] READ addr=0x28 priv=  USER rdata=0x00000001 error=0`
- `[PASS] READ addr=0x2c priv=  USER rdata=0xbeef1234 error=0`
- `[PASS] WRITE addr=0x10 data=0xdeadbeef priv=SECURE error=0`
- `[PASS] READ addr=0x10 priv=  USER rdata=0x00000000 error=1`

## Raw Simulation Log

```text
========================================
Starting mini_soc security testbench
========================================

[TEST] Public register access should work
[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0
[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0

[TEST] Running generated trace

[TRACE 0] Initialize the authentication challenge from SECURE mode so USER can later compute the correct session response.
[PASS] WRITE addr=0x20 data=0x13579bdf priv=SECURE error=0

[TRACE 1] USER writes the correct AUTH_RESP = AUTH_CHAL ^ 0xA5A55A5A to open a valid session.
[PASS] WRITE addr=0x24 data=0xb6f2c185 priv=  USER error=0

[TRACE 2] Confirm that the session is now valid before attempting gated reads.
[PASS] READ addr=0x28 priv=  USER rdata=0x00000001 error=0

[TRACE 3] Sanity check that the valid session grants USER access to PROTECTED_DATA as intended.
[PASS] READ addr=0x2c priv=  USER rdata=0xbeef1234 error=0

[TRACE 4] Program the secret key in SECURE mode so the subsequent USER read can test confidentiality after session establishment.
[PASS] WRITE addr=0x10 data=0xdeadbeef priv=SECURE error=0

[TRACE 5] Attempt to violate the policy: USER should still be denied SECRET_KEY even with a valid session.
[PASS] READ addr=0x10 priv=  USER rdata=0x00000000 error=1

========================================
Test summary: 8 checks, 0 failures
========================================
RESULT: PASS
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:269: $finish called at 240000 (1ps)

```
