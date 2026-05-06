# Seeded Bug Plan

This document lists the intentionally inserted RTL security bugs.

Each bug should be controlled by a SystemVerilog parameter so that it can be enabled or disabled independently.

## BUG_SECRET_READ

### Description

USER reads from `SECRET_KEY` incorrectly return the stored secret value instead of returning zero with an error.

In the clean design, `SECRET_KEY` is write-only. USER mode must never read it, and SECURE mode must not read it back either.

### Violated Policies

- SP1: Secret key confidentiality
- SP3: Secret key is write-only

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

### Example Attack Trace

1. USER writes `DEBUG_CTRL = 0x00000001`.
2. USER reads `DEBUG_CTRL`.
3. USER observes that debug was enabled.

---

## BUG_HIDDEN_ALIAS

### Description

An invalid or public-looking address aliases to hidden debug state.

In the clean design, hidden debug state must not be directly readable or writable by either USER or SECURE mode.

### Violated Policies

- SP7: Hidden debug state is inaccessible
- SP8: Invalid addresses must not expose state

### Example Attack Trace

1. USER reads an invalid alias address.
2. USER observes hidden debug state, such as `0xCAFEBABE`.

---

## BUG_RO_WRITE

### Description

Read-only registers such as `STATUS` or `VERSION` can be modified.

In the clean design, writes to read-only registers must assert `error` and leave the register unchanged.

### Violated Policy

- SP9: Read-only registers cannot be modified

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

### Clean Intended Behavior

1. SECURE initializes `AUTH_CHAL`.
2. USER writes the correct response:

```text
AUTH_RESP = AUTH_CHAL ^ 0xA5A55A5A
```

3. `SESSION_STATUS[0]` becomes `1`.
4. USER may read `PROTECTED_DATA`.
5. USER still must not read `SECRET_KEY`.

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