# Security Policy

This document defines the intended security behavior of the mini SoC.

The agent and testbench should try to find traces that violate these rules.

## Initial Policies

1. User mode must not be able to read the secret key register.

2. User mode must not be able to write the secret key register.

3. Denied reads must return zero and assert an error.

4. Secure mode may write the secret key before the boot lock is set.

5. Once the boot lock is set, debug mode must not be enabled.

6. Hidden or reserved addresses must not expose protected state.