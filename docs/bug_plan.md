# Seeded Bug Plan

This document lists the intentionally inserted RTL security bugs.

Each bug should be controlled by a SystemVerilog parameter so that it can be enabled or disabled independently.

## Design Intent

The mini SoC models a small memory-mapped security-sensitive peripheral with:

- public configuration/status registers
- secure-only secret storage
- debug/boot-lock controls
- hidden internal debug state
- a simple challenge-response session mechanism
- session-gated protected data

The goal is to seed realistic access-control and lifecycle bugs that can be found by directed traces, fuzzing, or agentic AI-generated MMIO tests.

---

## BUG_SECRET_READ

### Description

Reads from `SECRET_KEY` incorrectly return the stored secret value instead of returning zero with an error.

In the clean design, `SECRET_KEY` is write-only. USER mode must never read it, and SECURE mode must not read it back either.

### Violated Policies

- SP1: Secret key confidentiality
- SP3: Secret key is write-only

### Expected Clean Behavior

1. SECURE writes `SECRET_KEY`.
2. USER reads `SECRET_KEY`.
3. Read returns `0x00000000`.
4. `error` is asserted.

### Buggy Behavior

1. SECURE writes `SECRET_KEY`.
2. USER reads `SECRET_KEY`.
3. Read returns the secret value.
4. `error` is not asserted.

### Example Attack Trace

1. SECURE writes `0xDEADBEEF` to `SECRET_KEY`.
2. USER reads `SECRET_KEY`.
3. USER observes `0xDEADBEEF`.

---

## BUG_STALE_RDATA

### Description

Denied reads return the previous value on the read-data bus instead of returning zero.

This can leak values from earlier successful reads or writes, especially if the previous transaction involved sensitive or privileged state.

### Violated Policy

- SP4: Denied reads must not leak stale data

### Expected Clean Behavior

1. A valid read places some value on `rdata`.
2. USER performs a denied read.
3. Denied read returns `0x00000000`.
4. `error` is asserted.

### Buggy Behavior

1. A valid read places some value on `rdata`.
2. USER performs a denied read.
3. Denied read returns stale previous data.
4. `error` may still be asserted, but data has leaked.

### Example Attack Trace

1. A valid read places a sensitive or useful value on `rdata`.
2. USER performs a denied read.
3. USER observes stale nonzero data instead of `0x00000000`.

---

## BUG_DEBUG_UNLOCK

### Description

`DEBUG_CTRL` can still be modified after `BOOT_LOCK[0]` is set.

In the clean design, once boot lock is active, debug configuration must be frozen.

### Violated Policy

- SP5: Boot lock protects debug control

### Expected Clean Behavior

1. SECURE writes `DEBUG_CTRL`.
2. SECURE writes `BOOT_LOCK[0] = 1`.
3. Any later write to `DEBUG_CTRL` is denied.
4. `DEBUG_CTRL` remains unchanged.

### Buggy Behavior

1. SECURE writes `DEBUG_CTRL`.
2. SECURE writes `BOOT_LOCK[0] = 1`.
3. A later write to `DEBUG_CTRL` is incorrectly accepted.
4. `DEBUG_CTRL` changes after boot lock.

### Example Attack Trace

1. SECURE writes `DEBUG_CTRL = 0x00000001`.
2. SECURE writes `BOOT_LOCK = 0x00000001`.
3. SECURE attempts to write `DEBUG_CTRL = 0x00000000`.
4. Clean RTL should reject the write and preserve the old debug value.
5. Buggy RTL accepts the write and changes `DEBUG_CTRL`.

---

## BUG_USER_DEBUG_WRITE

### Description

USER mode is incorrectly allowed to write `DEBUG_CTRL`.

In the clean design, only SECURE mode may modify `DEBUG_CTRL`, and only before boot lock is set.

### Violated Policy

- SP6: USER cannot enable debug

### Expected Clean Behavior

1. USER writes `DEBUG_CTRL`.
2. Write is denied.
3. `DEBUG_CTRL` remains unchanged.

### Buggy Behavior

1. USER writes `DEBUG_CTRL`.
2. Write is accepted.
3. USER changes debug state.

### Example Attack Trace

1. USER writes `DEBUG_CTRL = 0x00000001`.
2. USER reads `DEBUG_CTRL`.
3. USER observes that debug was enabled.

---

## BUG_HIDDEN_ALIAS

### Description

An invalid or reserved address aliases to hidden debug state.

In the clean design, hidden debug state must not be directly readable or writable by either USER or SECURE mode.

After the session registers were added, `0x20` became a valid address for `AUTH_CHAL`. The hidden alias bug now uses reserved invalid address `0x30`.

### Violated Policies

- SP7: Hidden debug state is inaccessible
- SP8: Invalid addresses must not expose state

### Expected Clean Behavior

1. USER reads reserved address `0x30`.
2. Read returns `0x00000000`.
3. `error` is asserted.

### Buggy Behavior

1. USER reads reserved address `0x30`.
2. RTL aliases the access to hidden debug state.
3. USER observes hidden value such as `0xCAFEBABE`.

### Example Attack Trace

1. USER reads address `0x30`.
2. Clean RTL returns `0x00000000` with `error = 1`.
3. Buggy RTL returns hidden debug state with `error = 0`.

---

## BUG_RO_WRITE

### Description

Read-only registers such as `STATUS` or `VERSION` can be modified.

In the clean design, writes to read-only registers must assert `error` and leave the register unchanged.

### Violated Policy

- SP9: Read-only registers cannot be modified

### Expected Clean Behavior

1. USER or SECURE writes a read-only register.
2. Write is denied.
3. Register remains unchanged.

### Buggy Behavior

1. USER or SECURE writes a read-only register.
2. Write is accepted.
3. Register changes.

### Example Attack Trace

1. USER writes `VERSION = 0xFFFFFFFF`.
2. USER reads `VERSION`.
3. USER observes that `VERSION` changed from its reset value.

---

## BUG_SESSION_SECRET_BYPASS

### Description

When `SESSION_STATUS[0]` is set, USER mode is incorrectly allowed to read `SECRET_KEY`.

The intended behavior is that the authenticated session only grants USER access to `PROTECTED_DATA`. It must not grant access to `SECRET_KEY`.

This is a harder bug because the attacker must first establish a valid session before attempting the forbidden secret read.

### Violated Policies

- SP1: Secret key confidentiality
- SP11: Session unlock grants limited access only

### Expected Clean Behavior

1. SECURE initializes `AUTH_CHAL`.
2. USER writes the correct response:

```text
AUTH_RESP = AUTH_CHAL ^ 0xA5A55A5A
```

3. `SESSION_STATUS[0]` becomes `1`.
4. USER may read `PROTECTED_DATA`.
5. USER reads `SECRET_KEY`.
6. Read returns `0x00000000`.
7. `error` is asserted.

### Buggy Behavior

1. USER opens a valid session.
2. USER reads `SECRET_KEY`.
3. Buggy RTL incorrectly treats `SESSION_STATUS[0] == 1` as permission to read `SECRET_KEY`.
4. `SECRET_KEY` leaks.

### Example Attack Trace

1. SECURE writes `AUTH_CHAL = 0x12345678`.
2. USER writes `AUTH_RESP = 0xB7910C22`.

```text
0x12345678 ^ 0xA5A55A5A = 0xB7910C22
```

3. USER reads `SESSION_STATUS` and observes `0x00000001`.
4. SECURE writes `SECRET_KEY = 0xDEADBEEF`.
5. USER reads `SECRET_KEY`.
6. Clean RTL should return `0x00000000` with `error = 1`.
7. Buggy RTL returns `0xDEADBEEF` with `error = 0`.

### Why This Bug Is Harder

Random fuzzing is unlikely to find this bug quickly because it must generate a meaningful ordered sequence:

1. Set or observe the challenge.
2. Compute the correct response using `AUTH_CHAL ^ 0xA5A55A5A`.
3. Open a valid session.
4. Initialize the secret.
5. Attempt the forbidden USER read from `SECRET_KEY`.

A policy-guided or LLM-guided agent should perform better because it can use the register map and security policy to intentionally construct the required sequence.

---

## BUG_FAILED_AUTH_DOES_NOT_CLEAR_SESSION

### Description

After a valid session is established, writing an incorrect `AUTH_RESP` should clear `SESSION_STATUS[0]`.

The bug incorrectly preserves the active session after a failed authentication attempt.

This models a revocation/lifecycle bug: authentication failure should remove temporary access, but the session remains valid.

### Violated Policies

- SP13: Authentication response access
- SP15: Session revocation after failed authentication

### Expected Clean Behavior

1. SECURE initializes `AUTH_CHAL`.
2. USER writes the correct `AUTH_RESP`.
3. `SESSION_STATUS[0]` becomes `1`.
4. USER may read `PROTECTED_DATA`.
5. USER writes an incorrect `AUTH_RESP`.
6. `SESSION_STATUS[0]` becomes `0`.
7. USER can no longer read `PROTECTED_DATA`.

### Buggy Behavior

1. USER establishes a valid session.
2. USER writes an incorrect `AUTH_RESP`.
3. RTL incorrectly preserves `SESSION_STATUS[0] == 1`.
4. USER can still read `PROTECTED_DATA`.

### Example Attack Trace

1. SECURE writes `AUTH_CHAL = 0x12345678`.
2. USER writes `AUTH_RESP = 0xB7910C22`, opening a valid session.
3. USER reads `PROTECTED_DATA` successfully.
4. USER writes incorrect `AUTH_RESP = 0x00000000`.
5. Clean RTL clears `SESSION_STATUS[0]`.
6. Buggy RTL leaves `SESSION_STATUS[0] = 1`.
7. USER reads `PROTECTED_DATA` again and observes `0xBEEF1234`.

### Why This Bug Is Useful

This is a good agentic-verification target because it requires the trace to test a lifecycle transition:

```text
valid auth -> access granted -> failed auth -> access should be revoked
```

A human may test valid authentication and invalid authentication separately, but miss the ordered case where a failed authentication occurs after a previously valid session.

---

## BUG_BOOT_LOCK_SESSION_PERSIST

### Description

Setting `BOOT_LOCK[0] = 1` should clear any active session.

The bug incorrectly allows the authenticated session to persist after boot lock is set.

This models a security-state transition bug: entering a locked-down state should revoke temporary access permissions.

### Violated Policies

- SP14: Session revocation on boot lock

### Expected Clean Behavior

1. SECURE initializes `AUTH_CHAL`.
2. USER writes the correct `AUTH_RESP`.
3. `SESSION_STATUS[0]` becomes `1`.
4. USER may read `PROTECTED_DATA`.
5. SECURE writes `BOOT_LOCK[0] = 1`.
6. `SESSION_STATUS[0]` becomes `0`.
7. USER can no longer read `PROTECTED_DATA`.

### Buggy Behavior

1. USER establishes a valid session.
2. SECURE writes `BOOT_LOCK[0] = 1`.
3. RTL incorrectly preserves `SESSION_STATUS[0] == 1`.
4. USER can still read `PROTECTED_DATA`.

### Example Attack Trace

1. SECURE writes `AUTH_CHAL = 0x12345678`.
2. USER writes `AUTH_RESP = 0xB7910C22`, opening a valid session.
3. USER reads `PROTECTED_DATA` successfully.
4. SECURE writes `BOOT_LOCK = 0x00000001`.
5. Clean RTL clears `SESSION_STATUS[0]`.
6. Buggy RTL leaves `SESSION_STATUS[0] = 1`.
7. USER reads `PROTECTED_DATA` again and observes `0xBEEF1234`.

### Why This Bug Is Useful

This bug checks whether session state is revoked when the system enters a locked configuration.

It is easy to miss if testing focuses only on debug-lock behavior and does not check whether unrelated temporary access state is also cleared.

---

## BUG_CHAL_ROTATE_DOES_NOT_CLEAR_SESSION

### Description

Rotating `AUTH_CHAL` should invalidate any existing session.

The bug incorrectly leaves the old session active after the challenge is changed.

This models a credential-rotation bug: a session authenticated against an old challenge should not remain valid once a new challenge is installed.

### Violated Policies

- SP12: Authentication challenge access
- SP16: Session revocation after challenge rotation

### Expected Clean Behavior

1. SECURE initializes `AUTH_CHAL`.
2. USER writes the correct `AUTH_RESP`.
3. `SESSION_STATUS[0]` becomes `1`.
4. USER may read `PROTECTED_DATA`.
5. SECURE writes a new `AUTH_CHAL`.
6. `SESSION_STATUS[0]` becomes `0`.
7. USER can no longer read `PROTECTED_DATA`.

### Buggy Behavior

1. USER establishes a valid session.
2. SECURE rotates `AUTH_CHAL`.
3. RTL incorrectly preserves `SESSION_STATUS[0] == 1`.
4. USER can still read `PROTECTED_DATA`.

### Example Attack Trace

1. SECURE writes `AUTH_CHAL = 0x12345678`.
2. USER writes `AUTH_RESP = 0xB7910C22`, opening a valid session.
3. USER reads `PROTECTED_DATA` successfully.
4. SECURE writes new `AUTH_CHAL = 0xAABBCCDD`.
5. Clean RTL clears `SESSION_STATUS[0]`.
6. Buggy RTL leaves `SESSION_STATUS[0] = 1`.
7. USER reads `PROTECTED_DATA` again and observes `0xBEEF1234`.

### Why This Bug Is Useful

This is a realistic lifecycle bug that checks whether temporary access survives credential or challenge rotation.

It is discoverable from the policy and register map, but not obvious from a single direct access. It requires a multi-step ordered trace:

```text
valid auth -> access granted -> challenge rotation -> access should be revoked
```

---

## Summary of Seeded Bugs

| Bug Parameter | Main Theme | Requires Ordered Sequence? |
|---|---|---|
| `BUG_SECRET_READ` | Secret confidentiality | No |
| `BUG_STALE_RDATA` | Denied-read leakage | Sometimes |
| `BUG_DEBUG_UNLOCK` | Boot-lock enforcement | Yes |
| `BUG_USER_DEBUG_WRITE` | Privilege bypass | No |
| `BUG_HIDDEN_ALIAS` | Invalid-address aliasing | No |
| `BUG_RO_WRITE` | Read-only integrity | No |
| `BUG_SESSION_SECRET_BYPASS` | Session over-permission | Yes |
| `BUG_FAILED_AUTH_DOES_NOT_CLEAR_SESSION` | Failed-auth revocation | Yes |
| `BUG_BOOT_LOCK_SESSION_PERSIST` | Lockdown revocation | Yes |
| `BUG_CHAL_ROTATE_DOES_NOT_CLEAR_SESSION` | Challenge-rotation revocation | Yes |

## Evaluation Notes

The session lifecycle bugs are intended to be painful but discoverable.

They avoid relying on hidden, impossible-to-guess secrets. Instead, they require reasoning about state transitions and revocation:

- Does access get granted correctly?
- Does access get revoked correctly?
- Does temporary access survive after it should be invalidated?

These bugs are better suited for evaluating an agentic verification flow than bugs that require guessing an undocumented 32-bit authentication transform.