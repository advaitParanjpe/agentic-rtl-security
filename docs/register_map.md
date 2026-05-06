# Register Map

This document defines the memory-mapped registers for the mini SoC.

All registers are 32 bits wide. Addresses are byte addresses and are word-aligned.

## Privilege Levels

| Value | Name | Meaning |
|---:|---|---|
| 0 | USER | Untrusted normal software |
| 1 | SECURE | Trusted boot/firmware mode |

## Registers

| Address | Name | Reset Value | USER Read | USER Write | SECURE Read | SECURE Write | Description |
|---:|---|---:|---|---|---|---|---|
| 0x00 | STATUS | 0x00000000 | Yes | No | Yes | No | General status register |
| 0x04 | CONFIG | 0x00000000 | Yes | Yes | Yes | Yes | General non-secret configuration |
| 0x08 | BOOT_LOCK | 0x00000000 | Yes | No | Yes | Yes | Locks security-critical configuration |
| 0x0C | DEBUG_CTRL | 0x00000000 | Yes | No | Yes | Yes | Debug enable/control register |
| 0x10 | SECRET_KEY | 0x00000000 | No | No | No | Yes | Protected write-only secret register |
| 0x14 | PUBLIC_DATA | 0x00000000 | Yes | Yes | Yes | Yes | Normal public scratch register |
| 0x18 | HIDDEN_DBG | 0xCAFEBABE | No | No | No | No | Hidden/reserved debug state |
| 0x1C | VERSION | 0x00000001 | Yes | No | Yes | No | Read-only version register |
| 0x20 | AUTH_CHAL | 0x00000000 | Yes | No | Yes | Yes | Authentication challenge value |
| 0x24 | AUTH_RESP | 0x00000000 | No | Yes | No | Yes | Write response to unlock session |
| 0x28 | SESSION_STATUS | 0x00000000 | Yes | No | Yes | No | Bit 0 indicates `session_valid` |
| 0x2C | PROTECTED_DATA | 0xBEEF1234 | Conditional | No | Yes | Yes | Data readable by USER only when `session_valid` is set |

## Address Behavior

- Valid register addresses are `0x00` through `0x2C`.
- Accesses must be word-aligned.
- Reads from invalid addresses must return `0x00000000` and assert `error`.
- Writes to invalid addresses must assert `error` and must not modify state.
- Reads from denied addresses must return `0x00000000` and assert `error`.
- Writes to denied addresses must assert `error` and must not modify state.
- `0x30`, `0x34`, and `0x38` are currently treated as invalid/reserved test addresses.
- Unaligned addresses such as `0x03` and `0x11` are invalid.

## Register Behavior Details

### STATUS `0x00`

`STATUS` is read-only.

- USER may read it.
- SECURE may read it.
- Writes must assert `error`.
- Reset value is `0x00000000`.

### CONFIG `0x04`

`CONFIG` is a normal public configuration register.

- USER may read and write it.
- SECURE may read and write it.
- Reset value is `0x00000000`.

### BOOT_LOCK `0x08`

`BOOT_LOCK[0]` locks security-critical configuration.

- USER may read it.
- USER may not write it.
- SECURE may read and write it.
- Once `BOOT_LOCK[0] == 1`, `DEBUG_CTRL` must not be modified.
- Writing `BOOT_LOCK[0] = 1` clears `SESSION_STATUS[0]`.
- Reset value is `0x00000000`.

### DEBUG_CTRL `0x0C`

`DEBUG_CTRL` controls debug behavior.

- USER may read it.
- USER may not write it.
- SECURE may read and write it only while `BOOT_LOCK[0] == 0`.
- Once `BOOT_LOCK[0] == 1`, writes to `DEBUG_CTRL` must assert `error` and leave it unchanged.
- Reset value is `0x00000000`.

### SECRET_KEY `0x10`

`SECRET_KEY` is a protected write-only secret register.

- USER may not read it.
- USER may not write it.
- SECURE may write it.
- SECURE may not read it back.
- Reads must return `0x00000000` and assert `error`.
- A valid session must not allow USER to read `SECRET_KEY`.
- Reset value is `0x00000000`.

### PUBLIC_DATA `0x14`

`PUBLIC_DATA` is a normal public scratch register.

- USER may read and write it.
- SECURE may read and write it.
- Reset value is `0x00000000`.

### HIDDEN_DBG `0x18`

`HIDDEN_DBG` models hidden debug/internal state.

- USER may not read or write it.
- SECURE may not read or write it directly.
- Reads must return `0x00000000` and assert `error`.
- Writes must assert `error` and leave it unchanged.
- Reset value is `0xCAFEBABE`.

### VERSION `0x1C`

`VERSION` is read-only.

- USER may read it.
- SECURE may read it.
- Writes must assert `error`.
- Reset value is `0x00000001`.

## Session Authentication Registers

The mini SoC includes a simple session mechanism.

The session is intended to grant USER mode temporary access to `PROTECTED_DATA` only. It must not grant access to `SECRET_KEY`.

The authentication response is:

```text
AUTH_RESP = AUTH_CHAL ^ 0xA5A55A5A
```

### AUTH_CHAL `0x20`

`AUTH_CHAL` stores the authentication challenge.

- USER may read it.
- USER may not write it.
- SECURE may read and write it.
- Reset value is `0x00000000`.

### AUTH_RESP `0x24`

`AUTH_RESP` accepts the authentication response.

- USER may write it.
- SECURE may write it.
- USER may not read it.
- SECURE may not read it.
- Reads must return `0x00000000` and assert `error`.
- If the written value equals `AUTH_CHAL ^ 0xA5A55A5A`, then `SESSION_STATUS[0]` becomes `1`.
- If the written value is incorrect, then `SESSION_STATUS[0]` becomes `0`.
- Reset value is `0x00000000`.

### SESSION_STATUS `0x28`

`SESSION_STATUS[0]` indicates whether the authenticated session is valid.

- USER may read it.
- USER may not write it.
- SECURE may read it.
- SECURE may not write it directly.
- `SESSION_STATUS[0] == 1` means the session is valid.
- `SESSION_STATUS[0] == 0` means the session is invalid.
- Writing the correct `AUTH_RESP` sets `SESSION_STATUS[0]`.
- Writing an incorrect `AUTH_RESP` clears `SESSION_STATUS[0]`.
- Writing `BOOT_LOCK[0] = 1` clears `SESSION_STATUS[0]`.
- Reset value is `0x00000000`.

### PROTECTED_DATA `0x2C`

`PROTECTED_DATA` is session-gated data.

- USER may read it only when `SESSION_STATUS[0] == 1`.
- USER may not write it.
- SECURE may read and write it.
- If USER reads it while `SESSION_STATUS[0] == 0`, the read must return `0x00000000` and assert `error`.
- Reset value is `0xBEEF1234`.

## Access Summary

| Register | USER Read | USER Write | SECURE Read | SECURE Write |
|---|---|---|---|---|
| STATUS | Yes | No | Yes | No |
| CONFIG | Yes | Yes | Yes | Yes |
| BOOT_LOCK | Yes | No | Yes | Yes |
| DEBUG_CTRL | Yes | No | Yes | Yes, if boot unlocked |
| SECRET_KEY | No | No | No | Yes |
| PUBLIC_DATA | Yes | Yes | Yes | Yes |
| HIDDEN_DBG | No | No | No | No |
| VERSION | Yes | No | Yes | No |
| AUTH_CHAL | Yes | No | Yes | Yes |
| AUTH_RESP | No | Yes | No | Yes |
| SESSION_STATUS | Yes | No | Yes | No |
| PROTECTED_DATA | Yes, if session valid | No | Yes | Yes |

## New Harder Bug Target

The new harder seeded bug is:

```text
BUG_SESSION_SECRET_BYPASS
```

In the clean design, a valid session lets USER read `PROTECTED_DATA`, but it does not let USER read `SECRET_KEY`.

In the buggy design, `SESSION_STATUS[0] == 1` incorrectly allows USER to read `SECRET_KEY`.

This requires a multi-step trace:

1. Initialize `AUTH_CHAL`.
2. Write the correct `AUTH_RESP`.
3. Confirm `SESSION_STATUS[0] == 1`.
4. Optionally read `PROTECTED_DATA` to confirm session-gated access works.
5. Initialize `SECRET_KEY`.
6. Attempt a USER read from `SECRET_KEY`.