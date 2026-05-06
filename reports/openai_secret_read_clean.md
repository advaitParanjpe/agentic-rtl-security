# Simulation Vulnerability Report

- Timestamp: `2026-05-05T19:02:07`
- Trace: `/Users/advaitparanjpe/Desktop/agentic-rtl-security/build/openai_secret_read.json`
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
- `[PASS] WRITE addr=0x10 data=0xa5a5a5a5 priv=SECURE error=0`
- `[PASS] READ addr=0x10 priv=  USER rdata=0x00000000 error=1`
- `[PASS] WRITE addr=0x14 data=0x11223344 priv=  USER error=0`

## Raw Simulation Log

```text
========================================
Starting mini_soc security testbench
========================================

[TEST] Public register access should work
[PASS] WRITE addr=0x14 data=0x1234abcd priv=  USER error=0
[PASS] READ addr=0x14 priv=  USER rdata=0x1234abcd error=0

[TEST] Running generated trace

[TRACE 0] Initialize SECRET_KEY in secure mode so a later denied read can verify confidentiality and that the register holds a non-reset value.
[PASS] WRITE addr=0x10 data=0xa5a5a5a5 priv=SECURE error=0

[TRACE 1] Attempt to violate secret confidentiality by reading SECRET_KEY from user mode; clean behavior must block the access and return zero.
[PASS] READ addr=0x10 priv=  USER rdata=0x00000000 error=1

[TRACE 2] Perform a benign user write to a public register to ensure the trace includes a normal access and to help detect stale-data leakage on the denied read above.
[PASS] WRITE addr=0x14 data=0x11223344 priv=  USER error=0

========================================
Test summary: 5 checks, 0 failures
========================================
RESULT: PASS
/Users/advaitparanjpe/Desktop/agentic-rtl-security/tb/tb_mini_soc.sv:264: $finish called at 180000 (1ps)

```
