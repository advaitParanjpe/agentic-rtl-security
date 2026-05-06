#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
import os
import re
from openai import OpenAI


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
PROMPT_PATH = REPO_ROOT / "agent" / "prompts" / "trace_proposal_prompt.md"


MOCK_LLM_TRACES = {
    "secret_read": [
        {
            "op": "write",
            "addr": "0x10",
            "data": "0xDEADBEEF",
            "priv": "secure",
            "expected_error": 0,
            "comment": "SECURE writes a known value into SECRET_KEY"
        },
        {
            "op": "read",
            "addr": "0x10",
            "priv": "user",
            "expected_rdata": "0x00000000",
            "expected_error": 1,
            "comment": "USER attempts to read SECRET_KEY and should be denied"
        }
    ],

    "user_debug_write": [
        {
            "op": "write",
            "addr": "0x0C",
            "data": "0x00000001",
            "priv": "user",
            "expected_error": 1,
            "comment": "USER attempts to enable DEBUG_CTRL"
        },
        {
            "op": "read",
            "addr": "0x0C",
            "priv": "user",
            "expected_rdata": "0x00000000",
            "expected_error": 0,
            "comment": "USER checks that DEBUG_CTRL remained disabled"
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
            "comment": "SECURE attempts to modify DEBUG_CTRL after BOOT_LOCK"
        },
        {
            "op": "read",
            "addr": "0x0C",
            "priv": "user",
            "expected_rdata": "0x00000001",
            "expected_error": 0,
            "comment": "USER observes that DEBUG_CTRL preserved its locked value"
        }
    ],

    "ro_write": [
        {
            "op": "write",
            "addr": "0x1C",
            "data": "0xFFFFFFFF",
            "priv": "user",
            "expected_error": 1,
            "comment": "USER attempts to overwrite VERSION"
        },
        {
            "op": "read",
            "addr": "0x1C",
            "priv": "user",
            "expected_rdata": "0x00000001",
            "expected_error": 0,
            "comment": "USER checks VERSION still has reset value"
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


def render_prompt(target):
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    security_policy = (DOCS_DIR / "security_policy.md").read_text(encoding="utf-8")
    register_map = (DOCS_DIR / "register_map.md").read_text(encoding="utf-8")

    return (
        prompt_template
        .replace("{{TARGET}}", target)
        .replace("{{SECURITY_POLICY}}", security_policy)
        .replace("{{REGISTER_MAP}}", register_map)
    )

def extract_json_array(text):
    text = text.strip()

    if text.startswith("[") and text.endswith("]"):
        return text

    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        raise ValueError("Could not find a JSON array in model output")

    return match.group(0)


def call_openai_for_trace(target, model):
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set")

    client = OpenAI()
    prompt = render_prompt(target)

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "You generate strict JSON MMIO traces for RTL security testing. "
                    "Return only a JSON array. Do not include Markdown fences."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    raw_text = response.output_text
    json_text = extract_json_array(raw_text)
    return json.loads(json_text)

def main():
    parser = argparse.ArgumentParser(
        description="LLM trace proposer for MMIO security traces."
    )

    parser.add_argument(
        "--target",
        choices=MOCK_LLM_TRACES.keys(),
        required=True,
        help="Target security property / bug class.",
    )

    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output JSON trace path.",
    )

    parser.add_argument(
        "--prompt-out",
        type=Path,
        default=None,
        help="Optional path to save the rendered prompt.",
    )

    parser.add_argument(
        "--mode",
        choices=["mock", "openai"],
        default="mock",
        help="Trace proposal mode. 'mock' uses built-in traces; 'openai' calls the OpenAI API.",
    )

    parser.add_argument(
        "--model",
        default="gpt-5.4-mini",
        help="Model to use for --mode openai.",
    )

    args = parser.parse_args()

    out_path = args.out
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path

    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.mode == "mock":
        trace = MOCK_LLM_TRACES[args.target]

    elif args.mode == "openai":
        trace = call_openai_for_trace(
            target=args.target,
            model=args.model,
        )

    else:
        raise ValueError(f"Unknown mode: {args.mode}")

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2)

    if args.prompt_out is not None:
        prompt_path = args.prompt_out
        if not prompt_path.is_absolute():
            prompt_path = REPO_ROOT / prompt_path

        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(render_prompt(args.target), encoding="utf-8")

        print(f"[DONE] Wrote rendered prompt to {prompt_path}")

    print(f"[DONE] Wrote {args.mode} LLM trace to {out_path}")
    print(f"[INFO] target={args.target}")
    print(f"[INFO] mode={args.mode}")


if __name__ == "__main__":
    main()