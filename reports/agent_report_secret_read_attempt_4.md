# Simulation Vulnerability Report

- Timestamp: `2026-05-05T18:33:58`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_secret_read_attempt_4.json`
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
- `[PASS] WRITE addr=0x10 data=0xdeadbeef priv=SECURE error=0`
- `[PASS] READ addr=0x10 priv=  USER rdata=0x00000000 error=1`
- `[PASS] READ addr=0x1c priv=  USER rdata=0x00000001 error=0`

## Raw Simulation Log

```text
========================================
Starting mini_soc security testbench
========================================

[TEST] Public register access should work
[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0
[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0

[TEST] Running generated trace

[TRACE 0] SECURE writes a known value into SECRET_KEY
[PASS] WRITE addr=0x10 data=0xdeadbeef priv=SECURE error=0

[TRACE 1] USER attempts to read SECRET_KEY and should be denied
[PASS] READ addr=0x10 priv=  USER rdata=0x00000000 error=1

[TRACE 2] Mutation suffix: USER observes VERSION
[PASS] READ addr=0x1c priv=  USER rdata=0x00000001 error=0

========================================
Test summary: 5 checks, 0 failures
========================================
RESULT: PASS
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 180000 (1ps)

```
