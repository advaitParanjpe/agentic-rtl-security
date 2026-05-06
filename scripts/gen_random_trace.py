#!/usr/bin/env python3

import argparse
import json
import random
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = REPO_ROOT / "traces"


REGISTERS = {
    "STATUS": 0x00,
    "CONFIG": 0x04,
    "BOOT_LOCK": 0x08,
    "DEBUG_CTRL": 0x0C,
    "SECRET_KEY": 0x10,
    "PUBLIC_DATA": 0x14,
    "HIDDEN_DBG": 0x18,
    "VERSION": 0x1C,
}

INVALID_ADDRS = [
    0x20,
    0x24,
    0x28,
    0x03,  # unaligned
    0x11,  # unaligned secret-ish
]

PRIVS = ["user", "secure"]
OPS = ["read", "write"]


def rand_data():
    return random.getrandbits(32)


def hex32(value):
    return f"0x{value:08X}"


def hex8(value):
    return f"0x{value:02X}"


def expected_behavior(op, addr, priv, data=None, model=None):
    """
    Small software model of the clean RTL's expected behavior.

    This gives each random operation expected_rdata / expected_error so the
    existing testbench can automatically detect when buggy RTL diverges.
    """

    if model is None:
        raise ValueError("model must be provided")

    aligned = (addr % 4) == 0

    if not aligned:
        if op == "read":
            return 0, 1
        return None, 1

    valid_addrs = set(REGISTERS.values())

    if addr not in valid_addrs:
        if op == "read":
            return 0, 1
        return None, 1

    # -------------------------
    # Write behavior
    # -------------------------
    if op == "write":
        assert data is not None

        if addr == REGISTERS["STATUS"]:
            return None, 1

        if addr == REGISTERS["CONFIG"]:
            model["CONFIG"] = data
            return None, 0

        if addr == REGISTERS["BOOT_LOCK"]:
            if priv == "secure":
                model["BOOT_LOCK"] = data
                return None, 0
            return None, 1

        if addr == REGISTERS["DEBUG_CTRL"]:
            if priv == "secure" and (model["BOOT_LOCK"] & 0x1) == 0:
                model["DEBUG_CTRL"] = data
                return None, 0
            return None, 1

        if addr == REGISTERS["SECRET_KEY"]:
            if priv == "secure":
                model["SECRET_KEY"] = data
                return None, 0
            return None, 1

        if addr == REGISTERS["PUBLIC_DATA"]:
            model["PUBLIC_DATA"] = data
            return None, 0

        if addr == REGISTERS["HIDDEN_DBG"]:
            return None, 1

        if addr == REGISTERS["VERSION"]:
            return None, 1

    # -------------------------
    # Read behavior
    # -------------------------
    if op == "read":
        if addr == REGISTERS["STATUS"]:
            return model["STATUS"], 0

        if addr == REGISTERS["CONFIG"]:
            return model["CONFIG"], 0

        if addr == REGISTERS["BOOT_LOCK"]:
            return model["BOOT_LOCK"], 0

        if addr == REGISTERS["DEBUG_CTRL"]:
            return model["DEBUG_CTRL"], 0

        if addr == REGISTERS["SECRET_KEY"]:
            return 0, 1

        if addr == REGISTERS["PUBLIC_DATA"]:
            return model["PUBLIC_DATA"], 0

        if addr == REGISTERS["HIDDEN_DBG"]:
            return 0, 1

        if addr == REGISTERS["VERSION"]:
            return model["VERSION"], 0

    raise RuntimeError(f"Unhandled operation: op={op}, addr=0x{addr:02X}, priv={priv}")


def initial_model():
    return {
        "STATUS": 0x00000000,
        "CONFIG": 0x00000000,
        "BOOT_LOCK": 0x00000000,
        "DEBUG_CTRL": 0x00000000,
        "SECRET_KEY": 0x00000000,
        "PUBLIC_DATA": 0x00000000,
        "HIDDEN_DBG": 0xCAFE_BABE,
        "VERSION": 0x00000001,
    }


def generate_trace(num_ops, seed):
    random.seed(seed)

    model = initial_model()
    trace = []

    all_addrs = list(REGISTERS.values()) + INVALID_ADDRS

    for i in range(num_ops):
        op = random.choice(OPS)
        addr = random.choice(all_addrs)
        priv = random.choice(PRIVS)

        entry = {
            "op": op,
            "addr": hex8(addr),
            "priv": priv,
            "comment": f"Random op {i}: {op} addr={hex8(addr)} priv={priv}",
        }

        if op == "write":
            data = rand_data()
            _, expected_error = expected_behavior(
                op=op,
                addr=addr,
                priv=priv,
                data=data,
                model=model,
            )

            entry["data"] = hex32(data)
            entry["expected_error"] = expected_error

        else:
            expected_rdata, expected_error = expected_behavior(
                op=op,
                addr=addr,
                priv=priv,
                model=model,
            )

            entry["expected_rdata"] = hex32(expected_rdata)
            entry["expected_error"] = expected_error

        trace.append(entry)

    return trace


def main():
    parser = argparse.ArgumentParser(
        description="Generate a random MMIO JSON trace."
    )

    parser.add_argument(
        "--ops",
        type=int,
        default=20,
        help="Number of operations in the trace.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Random seed.",
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=TRACE_DIR / "random_trace.json",
        help="Output JSON trace path.",
    )

    args = parser.parse_args()

    out_path = args.out

    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)

    trace = generate_trace(num_ops=args.ops, seed=args.seed)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2)

    print(f"[DONE] Wrote random trace to {out_path}")
    print(f"[INFO] ops={args.ops} seed={args.seed}")


if __name__ == "__main__":
    main()