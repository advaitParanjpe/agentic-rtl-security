#!/usr/bin/env python3

import argparse
import json
import sys
from pathlib import Path


VALID_OPS = {"read", "write"}
VALID_PRIVS = {"user", "secure"}

VALID_ADDRS = {
    0x00,
    0x04,
    0x08,
    0x0C,
    0x10,
    0x14,
    0x18,
    0x1C,
    0x20,
    0x24,
    0x28,
    0x2C,
    0x30,
    0x34,
    0x38,
    0x03,
    0x11,
}


def parse_int(value, field_name, index):
    if isinstance(value, int):
        return value

    if isinstance(value, str):
        try:
            return int(value, 16)
        except ValueError:
            raise ValueError(
                f"op[{index}].{field_name} must be hex string or int, got {value!r}"
            )

    raise ValueError(
        f"op[{index}].{field_name} must be hex string or int, got {type(value).__name__}"
    )


def validate_entry(entry, index):
    errors = []

    if not isinstance(entry, dict):
        return [f"op[{index}] must be an object/dict"]

    op = entry.get("op")
    if op not in VALID_OPS:
        errors.append(f"op[{index}].op must be one of {sorted(VALID_OPS)}, got {op!r}")

    priv = entry.get("priv")
    if priv not in VALID_PRIVS:
        errors.append(f"op[{index}].priv must be one of {sorted(VALID_PRIVS)}, got {priv!r}")

    if "addr" not in entry:
        errors.append(f"op[{index}] missing required field: addr")
    else:
        try:
            addr = parse_int(entry["addr"], "addr", index)
            if addr not in VALID_ADDRS:
                errors.append(
                    f"op[{index}].addr 0x{addr:02X} is not in known test address set"
                )
        except ValueError as e:
            errors.append(str(e))

    if "comment" not in entry:
        errors.append(f"op[{index}] missing recommended field: comment")

    expected_error = entry.get("expected_error")
    if expected_error not in (0, 1, False, True):
        errors.append(
            f"op[{index}].expected_error must be 0 or 1, got {expected_error!r}"
        )

    if op == "write":
        if "data" not in entry:
            errors.append(f"op[{index}] write missing required field: data")
        else:
            try:
                data = parse_int(entry["data"], "data", index)
                if data < 0 or data > 0xFFFF_FFFF:
                    errors.append(f"op[{index}].data out of 32-bit range")
            except ValueError as e:
                errors.append(str(e))

        if "expected_rdata" in entry:
            errors.append(f"op[{index}] write should not include expected_rdata")

    if op == "read":
        if "data" in entry:
            errors.append(f"op[{index}] read should not include data")

        if "expected_rdata" not in entry:
            errors.append(f"op[{index}] read missing required field: expected_rdata")
        else:
            try:
                rdata = parse_int(entry["expected_rdata"], "expected_rdata", index)
                if rdata < 0 or rdata > 0xFFFF_FFFF:
                    errors.append(f"op[{index}].expected_rdata out of 32-bit range")
            except ValueError as e:
                errors.append(str(e))

    return errors


def validate_trace(trace):
    errors = []

    if not isinstance(trace, list):
        return ["Trace must be a JSON list"]

    if len(trace) == 0:
        errors.append("Trace must contain at least one operation")

    for index, entry in enumerate(trace):
        errors.extend(validate_entry(entry, index))

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate an MMIO JSON trace before simulation."
    )

    parser.add_argument(
        "trace",
        type=Path,
        help="Path to JSON trace file.",
    )

    args = parser.parse_args()

    if not args.trace.exists():
        print(f"[ERROR] Trace does not exist: {args.trace}")
        sys.exit(1)

    try:
        with args.trace.open("r", encoding="utf-8") as f:
            trace = json.load(f)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}")
        sys.exit(1)

    errors = validate_trace(trace)

    if errors:
        print("[FAIL] Trace validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

    print(f"[PASS] Trace validation passed: {args.trace}")
    sys.exit(0)


if __name__ == "__main__":
    main()