#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TRACE_DIR = REPO_ROOT / "traces"


TRACE_TEMPLATES = {
    "secret_read": [
        {
            "op": "write",
            "addr": "0x10",
            "data": "0xDEADBEEF",
            "priv": "secure",
            "expected_error": 0,
            "comment": "SECURE initializes SECRET_KEY"
        },
        {
            "op": "read",
            "addr": "0x10",
            "priv": "user",
            "expected_rdata": "0x00000000",
            "expected_error": 1,
            "comment": "USER attempts to read SECRET_KEY and should be blocked"
        }
    ],

    "user_debug_write": [
        {
            "op": "write",
            "addr": "0x0C",
            "data": "0x00000001",
            "priv": "user",
            "expected_error": 1,
            "comment": "USER attempts to enable DEBUG_CTRL and should be blocked"
        },
        {
            "op": "read",
            "addr": "0x0C",
            "priv": "user",
            "expected_rdata": "0x00000000",
            "expected_error": 0,
            "comment": "USER reads DEBUG_CTRL and should see it remains disabled"
        }
    ],

    "debug_unlock": [
        {
            "op": "write",
            "addr": "0x0C",
            "data": "0x00000001",
            "priv": "secure",
            "expected_error": 0,
            "comment": "SECURE enables DEBUG_CTRL before BOOT_LOCK"
        },
        {
            "op": "write",
            "addr": "0x08",
            "data": "0x00000001",
            "priv": "secure",
            "expected_error": 0,
            "comment": "SECURE sets BOOT_LOCK"
        },
        {
            "op": "write",
            "addr": "0x0C",
            "data": "0x00000000",
            "priv": "secure",
            "expected_error": 1,
            "comment": "SECURE attempts to modify DEBUG_CTRL after BOOT_LOCK and should be blocked"
        },
        {
            "op": "read",
            "addr": "0x0C",
            "priv": "user",
            "expected_rdata": "0x00000001",
            "expected_error": 0,
            "comment": "USER reads DEBUG_CTRL and should see original value preserved"
        }
    ],

    "ro_write": [
        {
            "op": "write",
            "addr": "0x1C",
            "data": "0xFFFFFFFF",
            "priv": "user",
            "expected_error": 1,
            "comment": "USER attempts to modify read-only VERSION register"
        },
        {
            "op": "read",
            "addr": "0x1C",
            "priv": "user",
            "expected_rdata": "0x00000001",
            "expected_error": 0,
            "comment": "USER reads VERSION and should see reset value preserved"
        }
    ],

    "hidden_alias": [
        {
            "op": "read",
            "addr": "0x20",
            "priv": "user",
            "expected_rdata": "0x00000000",
            "expected_error": 1,
            "comment": "USER reads invalid alias address and should not observe hidden debug state"
        }
    ],

    "session_secret_bypass": [
        {
            "op": "write",
            "addr": "0x20",
            "data": "0x12345678",
            "priv": "secure",
            "expected_error": 0,
            "comment": "SECURE initializes AUTH_CHAL"
        },
        {
            "op": "write",
            "addr": "0x24",
            "data": "0xB7910C22",
            "priv": "user",
            "expected_error": 0,
            "comment": "USER writes AUTH_RESP = AUTH_CHAL ^ AUTH_MAGIC to open session"
        },
        {
            "op": "read",
            "addr": "0x28",
            "priv": "user",
            "expected_rdata": "0x00000001",
            "expected_error": 0,
            "comment": "USER confirms session is valid"
        },
        {
            "op": "write",
            "addr": "0x2C",
            "data": "0xCAFE1234",
            "priv": "secure",
            "expected_error": 0,
            "comment": "SECURE writes PROTECTED_DATA"
        },
        {
            "op": "read",
            "addr": "0x2C",
            "priv": "user",
            "expected_rdata": "0xCAFE1234",
            "expected_error": 0,
            "comment": "USER reads PROTECTED_DATA because session is valid"
        },
        {
            "op": "write",
            "addr": "0x10",
            "data": "0xDEADBEEF",
            "priv": "secure",
            "expected_error": 0,
            "comment": "SECURE initializes SECRET_KEY"
        },
        {
            "op": "read",
            "addr": "0x10",
            "priv": "user",
            "expected_rdata": "0x00000000",
            "expected_error": 1,
            "comment": "USER attempts to read SECRET_KEY despite valid session and should be blocked"
        }
    ],
}


def main():
    parser = argparse.ArgumentParser(
        description="Generate a policy-guided MMIO JSON trace."
    )

    parser.add_argument(
        "--target",
        choices=TRACE_TEMPLATES.keys(),
        required=True,
        help="Security target / bug class to generate a trace for.",
    )

    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSON trace path.",
    )

    args = parser.parse_args()

    trace = TRACE_TEMPLATES[args.target]

    if args.out is None:
        out_path = TRACE_DIR / f"policy_{args.target}.json"
    else:
        out_path = args.out

    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2)

    print(f"[DONE] Wrote policy-guided trace to {out_path}")
    print(f"[INFO] target={args.target}")


if __name__ == "__main__":
    main()