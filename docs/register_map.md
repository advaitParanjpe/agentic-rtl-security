# Register Map

The mini SoC exposes a simple 32-bit memory-mapped register interface.

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
| 0x18 | HIDDEN_DBG | 0x00000000 | No | No | No | No | Hidden/reserved debug state |
| 0x1C | VERSION | 0x00000001 | Yes | No | Yes | No | Read-only version register |

## Address Behavior

- Valid register addresses are `0x00` through `0x1C`.
- Accesses must be word-aligned.
- Reads from invalid addresses must return `0x00000000` and assert `error`.
- Writes to invalid addresses must assert `error` and must not modify state.
- Reads from denied addresses must return `0x00000000` and assert `error`.
- Writes to denied addresses must assert `error` and must not modify state.