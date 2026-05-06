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

This remains true even if USER has a valid authenticated session.

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

Writes to `STATUS`, `VERSION`, or `SESSION_STATUS` must assert `error` and leave the register unchanged.

### SP10: Clean design must satisfy all policies

With all bug parameters disabled, the RTL must satisfy every security rule above.

With individual bug parameters enabled, the testbench, fuzzer, or agent should be able to generate traces that violate at least one corresponding security rule.

### SP11: Session unlock grants limited access only

The mini SoC includes a simple authenticated session mechanism.

The session mechanism uses:

| Register | Purpose |
|---|---|
| `AUTH_CHAL` | Stores a 32-bit authentication challenge |
| `AUTH_RESP` | Accepts a 32-bit authentication response |
| `SESSION_STATUS` | Indicates whether a session is valid |
| `PROTECTED_DATA` | Data that USER may read only during a valid session |

A session becomes valid only when software writes:

```text
AUTH_RESP = AUTH_CHAL ^ 0xA5A55A5A
```

When the response is correct, `SESSION_STATUS[0]` becomes `1`.

When the response is incorrect, `SESSION_STATUS[0]` becomes `0`.

USER mode may read `PROTECTED_DATA` only when `SESSION_STATUS[0] == 1`.

USER mode must not write `PROTECTED_DATA`.

SECURE mode may read and write `PROTECTED_DATA`.

USER mode must never read `SECRET_KEY`, even when `SESSION_STATUS[0] == 1`.

Setting `BOOT_LOCK[0] = 1` must clear `SESSION_STATUS[0]`.

### SP12: Authentication challenge access

SECURE mode may write `AUTH_CHAL`.

USER mode may read `AUTH_CHAL`.

USER mode must not write `AUTH_CHAL`.

### SP13: Authentication response access

USER mode and SECURE mode may write `AUTH_RESP`.

`AUTH_RESP` is write-only.

Reads from `AUTH_RESP` must return `0x00000000` and assert `error`.

## Current Seeded Bug Targets

The currently planned or implemented bug classes are:

| Bug Parameter | Violated Policy |
|---|---|
| `BUG_SECRET_READ` | SP1, SP3 |
| `BUG_STALE_RDATA` | SP4 |
| `BUG_DEBUG_UNLOCK` | SP5 |
| `BUG_USER_DEBUG_WRITE` | SP6 |
| `BUG_HIDDEN_ALIAS` | SP7, SP8 |
| `BUG_RO_WRITE` | SP9 |
| `BUG_SESSION_SECRET_BYPASS` | SP1, SP11 |

## Harder Session Bypass Scenario

The harder target bug is `BUG_SESSION_SECRET_BYPASS`.

The intended clean behavior is:

1. SECURE initializes `AUTH_CHAL`.
2. USER writes the correct `AUTH_RESP`.
3. `SESSION_STATUS[0]` becomes `1`.
4. USER may now read `PROTECTED_DATA`.
5. USER still must not read `SECRET_KEY`.

The buggy behavior is:

1. USER opens a valid session.
2. USER reads `SECRET_KEY`.
3. RTL incorrectly treats `SESSION_STATUS[0] == 1` as permission to read `SECRET_KEY`.
4. `SECRET_KEY` leaks.