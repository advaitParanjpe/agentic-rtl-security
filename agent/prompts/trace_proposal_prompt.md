# Trace Proposal Prompt

You are generating MMIO security test traces for a small SystemVerilog SoC.

Your task is to propose a JSON trace that attempts to violate the target security property.

The trace must be a JSON list of operations.

Each operation must be one of:

```json
{
  "op": "write",
  "addr": "0x10",
  "data": "0xDEADBEEF",
  "priv": "secure",
  "expected_error": 0,
  "comment": "Explain why this operation is included"
}
```

or:

```json
{
  "op": "read",
  "addr": "0x10",
  "priv": "user",
  "expected_rdata": "0x00000000",
  "expected_error": 1,
  "comment": "Explain why this operation is included"
}
```

Rules:

- Use only valid JSON.
- Do not include Markdown fences.
- Use addresses from the register map.
- Expected values must describe the clean design behavior.
- The trace should be short but sufficient.
- The trace should start from reset state.
- Use `priv` values `"user"` or `"secure"` only.

Target security property:

{{TARGET}}

Security policy:

{{SECURITY_POLICY}}

Register map:

{{REGISTER_MAP}}