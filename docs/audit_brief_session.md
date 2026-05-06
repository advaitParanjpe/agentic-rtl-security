# Access-Control Audit Brief

You are auditing a small memory-mapped SystemVerilog SoC.

The attacker controls USER-mode MMIO reads and writes.

The trusted environment may perform SECURE-mode setup operations when needed to initialize state.

Your goal is to generate MMIO traces that test whether USER mode can access or modify state beyond its intended permissions.

Focus area: access control, privilege boundaries, temporary access mechanisms, and session lifecycle behavior.

## Threat Model

- USER-mode software is untrusted.
- USER-mode software may issue arbitrary MMIO reads and writes.
- SECURE-mode operations may be used only for trusted setup when a trace needs initialization.
- The attacker cannot directly modify internal RTL signals.
- The attacker cannot directly force privilege level changes outside the trace operation being issued.
- The attacker can exploit ordering, repeated accesses, invalid accesses, and state transitions.

## High-Level Security Goals

- USER mode must not read secret or privileged-only state.
- USER mode must not modify security-critical control state.
- SECURE-only state must remain protected from USER mode.
- Read-only state must not be modified.
- Invalid, reserved, or unaligned addresses must not expose internal state.
- Denied reads should return `0x00000000` and assert `error`.
- Denied writes should assert `error` and leave state unchanged.
- Temporary access mechanisms should grant only the minimum intended access.
- Temporary access mechanisms should revoke access when their enabling condition is no longer valid.

## Session / Temporary Access Guidance

Some registers may implement a temporary access mechanism.

A temporary access mechanism may allow USER mode to access specific gated data after a valid setup or authentication sequence.

However, temporary access must not become a broad privilege escalation.

A good audit should test both:

1. **Grant behavior** — whether access is granted only when intended.
2. **Revocation behavior** — whether access is removed when the enabling condition changes or becomes invalid.

Do not only test whether access can be opened. Also test whether access is correctly closed.

## Arithmetic Guidance

When using a documented formula to compute a register value, double-check the hexadecimal arithmetic before emitting the trace.

For example, if a response is defined as:

```text
AUTH_RESP = AUTH_CHAL ^ 0xA5A55A5A
```

compute the exact 32-bit XOR result carefully.

If the trace expects a session or temporary access state to become valid, include an observation read to confirm that the state actually became valid before continuing.

When possible, prefer simple deterministic challenge values that make expected responses easy to verify, such as `0x00000000`, before using more complex values.

For example:

```text
0x00000000 ^ 0xA5A55A5A = 0xA5A55A5A

## Recommended Audit Patterns

Use the register map to understand available registers and expected access behavior.

Useful trace patterns include:

- Direct USER access to protected or privileged-only registers.
- USER writes to control or read-only registers.
- Invalid, reserved, or unaligned address accesses.
- Trusted setup followed by USER access.
- Successful temporary-access setup followed by allowed gated access.
- Successful temporary-access setup followed by attempted access to unrelated privileged state.
- Successful temporary-access setup followed by a later transition that should revoke access.
- Observation reads after important state changes.

## Lifecycle / Revocation Patterns

When a register or state transition grants temporary access, test whether later state transitions correctly revoke that access.

A good revocation test has this shape:

```text
1. Establish temporary access.
2. Confirm the access is active.
3. Confirm the intended gated resource is accessible.
4. Perform a transition that should revoke or invalidate the access.
5. Confirm the access state is cleared.
6. Confirm the gated resource is no longer accessible.
```

For session-style or challenge-response mechanisms, useful lifecycle cases include:

- Invalid response from reset should keep the session invalid.
- Valid response should make the session valid.
- Valid session should allow only the documented gated access.
- Valid session should not allow access to unrelated secret or privileged state.
- Incorrect response after a valid session should revoke access.
- Lock, reset-like, or security-state transitions should revoke temporary access.
- Challenge, credential, or setup-value rotation should revoke temporary access.
- After revocation, USER reads of gated data should return `0x00000000` and assert `error`.

For challenge-response mechanisms, also test whether changing or rotating the challenge after a session is established invalidates the old session.

A good challenge-rotation test has this shape:

```text
1. Establish a valid session using the current challenge.
2. Confirm the session is valid.
3. Confirm the session-gated resource is readable.
4. Change or rotate the challenge.
5. Confirm the old session is invalidated.
6. Confirm the session-gated resource is no longer readable.
```

## Expected Behavior Discipline

Expected values in traces must represent clean-design behavior.

Before claiming a vulnerability, the same trace should pass on the clean RTL and fail on the bug-enabled RTL.

When writing expected values:

- If a USER read is allowed, set the expected data and `expected_error = 0`.
- If a USER read is denied, set `expected_rdata = "0x00000000"` and `expected_error = 1`.
- If a write is denied, set `expected_error = 1`.
- If a write is allowed, set `expected_error = 0`.
- If a state bit is expected to change, include a readback to confirm it.
- If a setup step is needed before a security check, include the setup and confirmation steps.

## General Strategy

Do not assume the implementation is correct.

Do not assume the implementation is buggy.

Avoid repeatedly testing the same successful pattern if it does not expose a violation.

If a trace successfully establishes temporary access and all checks pass, the next trace should explore revocation or a different state transition rather than simply repeating the same grant/access test.

Use simulation feedback to improve future traces.