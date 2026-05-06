# Agentic RTL Security Verification

This project explores whether an agentic AI system can discover intentionally seeded security vulnerabilities in a small SystemVerilog SoC.

The design is a simple memory-mapped mini SoC with protected registers, privilege modes, a boot lock, and debug-control logic. Security bugs are deliberately inserted into the RTL, and an agent generates MMIO read/write traces to try to expose violations.

## Project Goals

- Build a small security-focused RTL SoC in SystemVerilog.
- Define clear security policies for protected registers and debug behavior.
- Seed known RTL security bugs into the design.
- Generate MMIO traces that attempt to violate the security policy.
- Compare random fuzzing, directed tests, and agentic AI-generated traces.
- Produce human-readable vulnerability reports.

## Planned Structure

```text
rtl/       SystemVerilog design files
tb/        Testbenches and security checkers
scripts/   Python scripts for simulation and trace generation
traces/    MMIO trace files
docs/      Security policy and register map
reports/   Generated vulnerability reports
agent/     Agentic AI loop and prompting code
sim/       Simulator support files
build/     Generated simulation outputs