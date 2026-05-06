# Limited Register Map

All registers are 32 bits wide. Addresses are byte addresses and are word-aligned.

There are two privilege levels:

| Value | Name | Meaning |
|---:|---|---|
| 0 | USER | Untrusted normal software |
| 1 | SECURE | Trusted setup/firmware mode |

## Registers

| Address | Name | Reset Value | USER Read | USER Write | SECURE Read | SECURE Write | Description |
|---:|---|---:|---|---|---|---|---|
| 0x00 | REG_STATUS | 0x00000000 | Yes | No | Yes | No | General status |
| 0x04 | REG_CONFIG | 0x00000000 | Yes | Yes | Yes | Yes | General configuration |
| 0x08 | REG_LOCK | 0x00000000 | Yes | No | Yes | Yes | Locks selected security-relevant state |
| 0x0C | REG_CTRL | 0x00000000 | Yes | No | Yes | Conditional | Security/control register |
| 0x10 | REG_SECRET | 0x00000000 | No | No | No | Yes | Sensitive write-only data |
| 0x14 | REG_PUBLIC | 0x00000000 | Yes | Yes | Yes | Yes | Public scratch data |
| 0x18 | REG_INTERNAL | 0xCAFEBABE | No | No | No | No | Internal/reserved state |
| 0x1C | REG_ID | 0x00000001 | Yes | No | Yes | No | Read-only identifier |
| 0x20 | REG_CHAL | 0x00000000 | Yes | No | Yes | Yes | Challenge-like setup register |
| 0x24 | REG_RESP | 0x00000000 | No | Yes | No | Yes | Response-like setup register |
| 0x28 | REG_STATE | 0x00000000 | Yes | No | Yes | No | State/status for a temporary access mechanism |
| 0x2C | REG_GATED_DATA | 0xBEEF1234 | Conditional | No | Yes | Yes | Data gated by temporary access state |

## General Access Rules

- Invalid or unaligned accesses should assert `error`.
- Denied reads should return `0x00000000` and assert `error`.
- Denied writes should assert `error` and leave state unchanged.
- Read-only registers should not be modified.
- USER mode should not access sensitive or internal state.
- Temporary access state may grant access to gated data, but should not broadly disable access control.

## Notes

- `REG_STATE[0]` indicates whether the temporary access state is active.
- `REG_RESP` is used to attempt to activate the temporary access state.
- The exact response behavior is intentionally not fully described in this limited audit map.
- Use simulation feedback to determine whether a proposed setup sequence reached an interesting state.
- Reserved test addresses include `0x30`, `0x34`, and `0x38`.