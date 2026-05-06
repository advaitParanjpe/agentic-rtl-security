# Security Policy

This document defines the intended security behavior of the mini SoC.

The verification environment, fuzzers, and agentic AI should try to generate MMIO traces that violate these rules.

## Threat Model

The attacker controls software running in USER mode.

The attacker can issue arbitrary MMIO reads and writes as USER mode.

The attacker may choose any address and write data.

The attacker may repeat accesses, use invalid addresses, access reserved regions, and try unusual ordering of operations.

The attacker cannot directly force internal RTL signals.

The attacker cannot directly change the external `priv` input except through the privilege level assigned to each trace operation.

## Privilege Model

There are two privilege levels:

| Value | Name | Meaning |
|---:|---|---|
| 0 | USER | Untrusted software |
| 1 | SECURE | Trusted boot/firmware software |

## Security Rules

### SP1: Secret key confidentiality

USER mode must never observe the value stored in `SECRET_KEY`.

A USER read from `SECRET_KEY` must return `0x00000000` and assert `error`.

### SP2: Secret key write protection

USER mode must never modify `SECRET_KEY`.

A USER write to `SECRET_KEY` must assert `error` and leave the previous secret value unchanged.

### SP3: Secret key is write-only

Even SECURE mode must not read back `SECRET_KEY`.

A SECURE read from `SECRET_KEY` must return `0x00000000` and assert `error`.

### SP4: Denied reads must not leak stale data

Any denied read must return `0x00000000`.

Denied reads must not return:
- the previous successful read value
- the previous write data
- any secret value
- any hidden debug value

### SP5: Boot lock protects debug control

Once `BOOT_LOCK[0]` is set to `1`, `DEBUG_CTRL` must not be modified.

Any later write to `DEBUG_CTRL` must assert `error` and leave `DEBUG_CTRL` unchanged.

### SP6: USER cannot enable debug

USER mode must never modify `DEBUG_CTRL`.

A USER write to `DEBUG_CTRL` must assert `error` and leave `DEBUG_CTRL` unchanged.

### SP7: Hidden debug state is inaccessible

`HIDDEN_DBG` must not be readable or writable by USER or SECURE mode.

Any access to `HIDDEN_DBG` must return `0x00000000` on reads and assert `error`.

### SP8: Invalid addresses must not expose state

Reads from invalid or unaligned addresses must return `0x00000000` and assert `error`.

Writes to invalid or unaligned addresses must assert `error` and must not modify any register.

### SP9: Read-only registers cannot be modified

Writes to `STATUS` or `VERSION` must assert `error` and leave the register unchanged.

### SP10: Clean design must satisfy all policies

With all bug parameters disabled, the RTL must satisfy every security rule above.

With individual bug parameters enabled, the testbench/fuzzer/agent should be able to generate traces that violate at least one corresponding security rule.