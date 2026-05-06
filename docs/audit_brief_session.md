# Limited Access-Control Audit Brief

You are auditing a small memory-mapped SystemVerilog SoC.

The attacker controls USER-mode MMIO reads and writes.

The trusted environment may perform SECURE-mode setup operations when needed to initialize state.

Your goal is to generate MMIO traces that test whether USER mode can access or modify state beyond its intended permissions.

## Threat Model

- USER-mode software is untrusted.
- USER-mode software may issue arbitrary MMIO reads and writes.
- SECURE-mode operations may be used only for setup when a trace needs trusted initialization.
- The attacker cannot directly modify internal RTL signals.
- The attacker cannot directly force privilege level changes outside the trace operation being issued.

## High-Level Security Goals

- USER mode must not read secret or privileged-only state.
- USER mode must not modify security-critical control state.
- SECURE-only state must remain protected from USER mode.
- Read-only state must not be modified.
- Denied reads should return `0x00000000` and assert `error`.
- Denied writes should assert `error` and leave state unchanged.
- Access-control behavior should remain correct across state changes and operation ordering.

## Audit Strategy Guidance

Generate traces that explore whether USER permissions can be expanded through:

- direct accesses
- invalid or reserved addresses
- setup followed by USER access
- ordering of writes and reads
- state transitions
- privilege-boundary mistakes

Use the register map to understand available registers and expected access behavior.

Do not assume the implementation is correct.

Do not assume the implementation is buggy.

Use simulation feedback to improve future traces.