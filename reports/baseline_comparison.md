# Baseline Comparison: Random Fuzzing vs Policy-Guided Agent

This document summarizes the current baseline results for the mini SoC RTL security project.

## Setup

The design under test is a small memory-mapped SystemVerilog SoC with protected registers, privilege checks, debug-control logic, boot-lock behavior, and intentionally seeded security bugs.

The current evaluated bug classes are:

| Bug | Description |
|---|---|
| `BUG_SECRET_READ` | Protected secret register becomes readable |
| `BUG_USER_DEBUG_WRITE` | USER mode can modify debug control |
| `BUG_DEBUG_UNLOCK` | Debug control can be modified after boot lock |
| `BUG_RO_WRITE` | Read-only register can be modified |
| `BUG_HIDDEN_ALIAS` | Invalid address aliases hidden debug state |

## Random Fuzzing Results

Random fuzzing generates random MMIO read/write traces using a clean software reference model for expected behavior.

Current observed results:

| Bug | Ops per Trace | Seeds | Detected | Missed | Detection Rate |
|---|---:|---:|---:|---:|---:|
| `BUG_SECRET_READ` | 50 | 20 | 16 | 4 | 80% |
| `BUG_SECRET_READ` | 100 | 20 | 20 | 0 | 100% |
| `BUG_USER_DEBUG_WRITE` | 50 | 20 | 12 | 8 | 60% |
| `BUG_USER_DEBUG_WRITE` | 100 | 20 | 16 | 4 | 80% |
| `BUG_DEBUG_UNLOCK` | 50 | 20 | 3 | 17 | 15% |
| `BUG_DEBUG_UNLOCK` | 1000 | 20 | 20 | 0 | 100% |
| `BUG_SESSION_SECRET_BYPASS` | 100 | 20 | 0 | 20 | 0% |
| `BUG_SESSION_SECRET_BYPASS` | 1000 | 20 | 0 | 20 | 0% |

## Interpretation

The random fuzzer can find simple bugs with enough operations. For example, `BUG_SECRET_READ` reaches 100% detection with 100-operation traces.

However, sequence-dependent bugs are much harder. `BUG_DEBUG_UNLOCK` only reached 15% detection with 50-operation traces because the fuzzer must accidentally generate the right ordering:

1. Write `DEBUG_CTRL` before boot lock.
2. Set `BOOT_LOCK`.
3. Attempt to modify `DEBUG_CTRL` after lock.
4. Observe that the state changed or that the write was incorrectly accepted.

This motivates a more guided trace-generation approach.

`BUG_SESSION_SECRET_BYPASS` was not detected by random fuzzing in either 100-operation or 1000-operation traces across 20 seeds. This is expected because detection requires a semantically meaningful sequence: initialize or observe `AUTH_CHAL`, compute `AUTH_RESP = AUTH_CHAL ^ 0xA5A55A5A`, establish a valid session, and then attempt a forbidden USER read from `SECRET_KEY`.

The OpenAI-guided agent generated this sequence directly in one attempt, including a correct authentication response and a final policy-violating secret read. This is the strongest evidence so far that policy/LLM-guided trace generation can outperform unguided random fuzzing on ordered security properties.

## Policy-Guided Agent Results

The lightweight policy-guided agent uses the security target to generate a short directed trace, runs simulation, and emits a Markdown vulnerability report.

Current agent regression result:

| Target | Bug Detected | Clean Design Passed |
|---|---|---|
| `secret_read` | Yes | Yes |
| `user_debug_write` | Yes | Yes |
| `debug_unlock` | Yes | Yes |
| `ro_write` | Yes | Yes |
| `hidden_alias` | Yes | Yes |

## Key Takeaway

Random fuzzing is useful as a baseline, but it wastes many traces on irrelevant behavior and struggles with ordered security properties.

The policy-guided agent finds the targeted vulnerabilities with short, meaningful traces because it uses the register map and security policy to construct attack sequences intentionally.

This creates the foundation for the next step: replacing the deterministic policy templates with an LLM-based agent that reads the policy/register map, proposes candidate traces, runs simulation, observes failures, and iterates.