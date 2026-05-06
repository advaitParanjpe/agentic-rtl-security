# Seeded Bug Plan

This document lists the intentionally inserted RTL security bugs.

Each bug should be controlled by a SystemVerilog parameter so that it can be enabled or disabled independently.

## BUG_SECRET_READ

### Description

USER reads from `SECRET_KEY` incorrectly return the stored secret value instead of returning zero with an error.

### Violated Policy

- SP1: Secret key confidentiality

### Example Attack Trace

1. SECURE writes `0xDEADBEEF` to `SECRET_KEY`.
2. USER reads `SECRET_KEY`.
3. USER observes `0xDEADBEEF`.

## BUG_STALE_RDATA

### Description

Denied reads return the previous value on the read-data bus instead of returning zero.

### Violated Policy

- SP4: Denied reads must not leak stale data

### Example Attack Trace

1. SECURE reads or writes sensitive/internal state.
2. USER performs a denied read.
3. USER observes stale nonzero data.

## BUG_DEBUG_UNLOCK

### Description

`DEBUG_CTRL` can still be modified after `BOOT_LOCK[0]` is set.

### Violated Policy

- SP5: Boot lock protects debug control

### Example Attack Trace

1. SECURE writes `BOOT_LOCK = 1`.
2. USER or SECURE attempts to modify `DEBUG_CTRL`.
3. `DEBUG_CTRL` changes even though boot lock is active.

## BUG_USER_DEBUG_WRITE

### Description

USER mode is incorrectly allowed to write `DEBUG_CTRL`.

### Violated Policy

- SP6: USER cannot enable debug

### Example Attack Trace

1. USER writes `DEBUG_CTRL = 1`.
2. USER reads `DEBUG_CTRL`.
3. `DEBUG_CTRL[0]` is observed as enabled.

## BUG_HIDDEN_ALIAS

### Description

An invalid or public-looking address aliases to hidden debug state.

### Violated Policy

- SP7: Hidden debug state is inaccessible
- SP8: Invalid addresses must not expose state

### Example Attack Trace

1. USER reads an alias address.
2. USER observes hidden debug state.

## BUG_RO_WRITE

### Description

Read-only registers such as `VERSION` can be modified.

### Violated Policy

- SP9: Read-only registers cannot be modified

### Example Attack Trace

1. USER writes `VERSION = 0xFFFFFFFF`.
2. USER reads `VERSION`.
3. `VERSION` has changed from its reset value.