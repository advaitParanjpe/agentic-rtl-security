# Simulation Vulnerability Report

- Timestamp: `2026-05-05T18:40:35`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_ro_write_attempt_3.json`
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
- `[PASS] READ addr=0x20 priv=  USER rdata=0x00000000 error=1`
- `[PASS] WRITE addr=0x24 data=0x11111111 priv=SECURE error=1`
- `[PASS] WRITE addr=0x1c data=0xffffffff priv=  USER error=1`
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

[TRACE 0] Mutation prefix: USER reads invalid address
[PASS] READ addr=0x20 priv=  USER rdata=0x00000000 error=1

[TRACE 1] Mutation prefix: SECURE writes invalid address
[PASS] WRITE addr=0x24 data=0x11111111 priv=SECURE error=1

[TRACE 2] USER attempts to overwrite VERSION
[PASS] WRITE addr=0x1c data=0xffffffff priv=  USER error=1

[TRACE 3] USER checks VERSION still has reset value
[PASS] READ addr=0x1c priv=  USER rdata=0x00000001 error=0

========================================
Test summary: 6 checks, 0 failures
========================================
RESULT: PASS
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 200000 (1ps)

```
