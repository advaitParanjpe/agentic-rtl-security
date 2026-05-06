# Simulation Vulnerability Report

- Timestamp: `2026-05-05T18:25:14`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/agent_trace_hidden_alias_attempt_2.json`
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
- `[PASS] WRITE addr=0x14 data=0xa5a5a5a5 priv=  USER error=0`
- `[PASS] READ addr=0x14 priv=  USER rdata=0xa5a5a5a5 error=0`
- `[PASS] READ addr=0x20 priv=  USER rdata=0x00000000 error=1`

## Raw Simulation Log

```text
========================================
Starting mini_soc security testbench
========================================

[TEST] Public register access should work
[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0
[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0

[TEST] Running generated trace

[TRACE 0] Mutation prefix: USER writes PUBLIC_DATA
[PASS] WRITE addr=0x14 data=0xa5a5a5a5 priv=  USER error=0

[TRACE 1] Mutation prefix: USER reads PUBLIC_DATA
[PASS] READ addr=0x14 priv=  USER rdata=0xa5a5a5a5 error=0

[TRACE 2] USER reads invalid alias address and should not observe hidden debug state
[PASS] READ addr=0x20 priv=  USER rdata=0x00000000 error=1

========================================
Test summary: 5 checks, 0 failures
========================================
RESULT: PASS
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 180000 (1ps)

```
