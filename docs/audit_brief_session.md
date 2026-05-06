# Session Access-Control Audit Brief

You are auditing a small memory-mapped SystemVerilog SoC.

The attacker controls USER-mode MMIO reads and writes.

The trusted environment may perform SECURE-mode setup operations when needed to initialize state.

Your goal is to generate MMIO traces that test whether USER mode can access data beyond its intended permissions.

Focus area: session access control.

## Key Security Goals

- USER mode must never read `SECRET_KEY`.
- `SECRET_KEY` is SECURE-write-only.
- A valid session may allow USER mode to read `PROTECTED_DATA`.
- A valid session must not allow USER mode to read `SECRET_KEY`.
- Denied reads should return `0x00000000` and assert `error`.
- Denied writes should assert `error` and leave state unchanged.

## Session Authentication Rules

The session mechanism uses:

- `AUTH_CHAL`
- `AUTH_RESP`
- `SESSION_STATUS`
- `PROTECTED_DATA`

A session becomes valid when:

```text
AUTH_RESP = AUTH_CHAL ^ 0xA5A55A5A
```

When a correct response is written, `SESSION_STATUS[0]` should become `1`.

When an incorrect response is written, `SESSION_STATUS[0]` should become `0`.

When `SESSION_STATUS[0] == 1`, USER mode may read `PROTECTED_DATA`.

Even when `SESSION_STATUS[0] == 1`, USER mode must still not read `SECRET_KEY`.

Writing `BOOT_LOCK[0] = 1` clears the active session.

## Audit Strategy Guidance

Generate traces that explore whether session authentication expands USER permissions too far.

Useful things to test may include:

- direct USER reads from protected registers
- USER reads after a valid session is established
- USER reads after an invalid session response
- USER reads after boot lock clears the session
- differences between `PROTECTED_DATA` and `SECRET_KEY`
- whether denied reads correctly return zero and assert error

Do not assume the implementation is correct.

Do not assume the implementation is buggy.

Use simulation feedback to improve future traces.