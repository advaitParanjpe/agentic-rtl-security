# Register Map

This document defines the memory-mapped registers for the mini SoC.

| Address | Name | Access | Description |
|---|---|---|---|
| 0x00 | STATUS | User read | General status register |
| 0x04 | CONFIG | User read/write | General configuration register |
| 0x08 | BOOT_LOCK | Secure write, user read | Locks boot/debug configuration |
| 0x0C | DEBUG_CTRL | Secure write, user read | Controls debug enable |
| 0x10 | SECRET_KEY | Secure write only | Protected secret register |
| 0x14 | PUBLIC_DATA | User read/write | Normal public data register |