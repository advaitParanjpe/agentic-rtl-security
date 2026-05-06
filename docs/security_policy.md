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

SECURE-mode operations may appear in verification traces only as trusted setup actions, such as initializing a secret, configuring a challenge value, or entering a locked state.

## Privilege Model

There are two privilege levels:

| Value | Name | Meaning |
|---:|---|---|
| 0 | USER | Untrusted software |
| 1 | SECURE | Trusted boot/firmware software |

## Core Security Rules

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
- any protected session-gated value unless access is currently permitted

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

Reads from invalid, reserved, or unaligned addresses must return `0x00000000` and assert `error`.

Writes to invalid, reserved, or unaligned addresses must assert `error` and must not modify any register.

Reserved invalid test addresses include:

```text
0x30
0x34
0x38
```

Unaligned test addresses include:

```text
0x03
0x11
```

### SP9: Read-only registers cannot be modified

Writes to `STATUS`, `VERSION`, or `SESSION_STATUS` must assert `error` and leave the register unchanged.

### SP10: Clean design must satisfy all policies

With all bug parameters disabled, the RTL must satisfy every security rule above.

With individual bug parameters enabled, the testbench, fuzzer, or agent should be able to generate traces that violate at least one corresponding security rule.

## Session Authentication Rules

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

### SP12: Authentication challenge access

SECURE mode may write `AUTH_CHAL`.

USER mode may read `AUTH_CHAL`.

USER mode must not write `AUTH_CHAL`.

Writing a new `AUTH_CHAL` value must clear `SESSION_STATUS[0]`.

This prevents an authenticated session from surviving challenge rotation.

### SP13: Authentication response access

USER mode and SECURE mode may write `AUTH_RESP`.

`AUTH_RESP` is write-only.

Reads from `AUTH_RESP` must return `0x00000000` and assert `error`.

Writing a correct `AUTH_RESP` must set `SESSION_STATUS[0]`.

Writing an incorrect `AUTH_RESP` must clear `SESSION_STATUS[0]`.

This remains true even if a valid session was already active.

### SP14: Session revocation on boot lock

Writing `BOOT_LOCK[0] = 1` must clear `SESSION_STATUS[0]`.

After boot lock clears the session, USER mode must no longer be able to read `PROTECTED_DATA`.

Boot lock must not leave temporary access permissions active.

### SP15: Session revocation after failed authentication

After a valid session is established, any later incorrect write to `AUTH_RESP` must clear `SESSION_STATUS[0]`.

After this failed authentication attempt, USER mode must no longer be able to read `PROTECTED_DATA`.

A failed authentication attempt must not preserve or extend a previous valid session.

### SP16: Session revocation after challenge rotation

After a valid session is established, any later SECURE write to `AUTH_CHAL` must clear `SESSION_STATUS[0]`.

After challenge rotation, USER mode must no longer be able to read `PROTECTED_DATA` until a new valid authentication response is written.

A session authenticated against an old challenge must not remain valid after the challenge changes.

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
| `BUG_FAILED_AUTH_DOES_NOT_CLEAR_SESSION` | SP13, SP15 |
| `BUG_BOOT_LOCK_SESSION_PERSIST` | SP14 |
| `BUG_CHAL_ROTATE_DOES_NOT_CLEAR_SESSION` | SP12, SP16 |

## Harder Session Bypass Scenario

The harder target bug `BUG_SESSION_SECRET_BYPASS` tests whether session-based access accidentally expands USER permissions too far.

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

## Session Lifecycle Bug Scenarios

The session lifecycle bugs test whether temporary access is revoked correctly after important state transitions.

### Failed authentication revocation

The intended clean behavior is:

1. USER establishes a valid session.
2. USER can read `PROTECTED_DATA`.
3. USER writes an incorrect `AUTH_RESP`.
4. `SESSION_STATUS[0]` becomes `0`.
5. USER can no longer read `PROTECTED_DATA`.

The buggy behavior is:

1. USER establishes a valid session.
2. USER writes an incorrect `AUTH_RESP`.
3. RTL incorrectly preserves `SESSION_STATUS[0] == 1`.
4. USER can still read `PROTECTED_DATA`.

### Boot lock session revocation

The intended clean behavior is:

1. USER establishes a valid session.
2. USER can read `PROTECTED_DATA`.
3. SECURE writes `BOOT_LOCK[0] = 1`.
4. `SESSION_STATUS[0]` becomes `0`.
5. USER can no longer read `PROTECTED_DATA`.

The buggy behavior is:

1. USER establishes a valid session.
2. SECURE writes `BOOT_LOCK[0] = 1`.
3. RTL incorrectly preserves `SESSION_STATUS[0] == 1`.
4. USER can still read `PROTECTED_DATA`.

### Challenge rotation session revocation

The intended clean behavior is:

1. USER establishes a valid session.
2. USER can read `PROTECTED_DATA`.
3. SECURE writes a new value to `AUTH_CHAL`.
4. `SESSION_STATUS[0]` becomes `0`.
5. USER can no longer read `PROTECTED_DATA`.

The buggy behavior is:

1. USER establishes a valid session.
2. SECURE rotates `AUTH_CHAL`.
3. RTL incorrectly preserves `SESSION_STATUS[0] == 1`.
4. USER can still read `PROTECTED_DATA`.