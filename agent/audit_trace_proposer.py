#!/usr/bin/env python3

import argparse
import json
import os
import re
from pathlib import Path

from openai import OpenAI


REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = REPO_ROOT / "agent" / "prompts" / "audit_trace_prompt.md"
REGISTER_MAP_PATH = REPO_ROOT / "docs" / "register_map.md"


def extract_json_array(text):
    """
    Extract a JSON array from model output.

    The prompt asks for raw JSON only, but this gives us some robustness if the
    model accidentally adds short text or Markdown fences.
    """
    text = text.strip()

    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    if text.startswith("[") and text.endswith("]"):
        return text

    match = re.search(r"$begin:math:display$\[\\s\\S\]\*$end:math:display$", text)
    if not match:
        raise ValueError("Could not find a JSON array in model output")

    return match.group(0)


def render_prompt(audit_brief_path, feedback_path=None):
    prompt_template = PROMPT_PATH.read_text(encoding="utf-8")
    audit_brief = audit_brief_path.read_text(encoding="utf-8")
    register_map = REGISTER_MAP_PATH.read_text(encoding="utf-8")

    if feedback_path is not None:
        feedback = feedback_path.read_text(encoding="utf-8")
    else:
        feedback = "No previous feedback. This is the first attempt."

    return (
        prompt_template
        .replace("{{AUDIT_BRIEF}}", audit_brief)
        .replace("{{REGISTER_MAP}}", register_map)
        .replace("{{FEEDBACK}}", feedback)
    )


def call_openai(prompt, model):
    if not os.environ.get("OPENAI_API_KEY"):
        raise EnvironmentError("OPENAI_API_KEY is not set")

    client = OpenAI()

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": (
                    "You generate strict JSON MMIO traces for RTL security auditing. "
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
    trace = json.loads(json_text)

    return trace, raw_text


def main():
    parser = argparse.ArgumentParser(
        description="Limited-knowledge OpenAI audit trace proposer."
    )

    parser.add_argument(
        "--audit-brief",
        type=Path,
        required=True,
        help="Path to limited audit brief markdown file.",
    )

    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Output JSON trace path.",
    )

    parser.add_argument(
        "--model",
        default="gpt-5.4-mini",
        help="OpenAI model to use.",
    )

    parser.add_argument(
        "--feedback",
        type=Path,
        default=None,
        help="Optional feedback file from previous attempt.",
    )

    parser.add_argument(
        "--prompt-out",
        type=Path,
        default=None,
        help="Optional path to save rendered prompt.",
    )

    parser.add_argument(
        "--raw-out",
        type=Path,
        default=None,
        help="Optional path to save raw model output.",
    )

    args = parser.parse_args()

    audit_brief_path = args.audit_brief
    if not audit_brief_path.is_absolute():
        audit_brief_path = REPO_ROOT / audit_brief_path

    feedback_path = args.feedback
    if feedback_path is not None and not feedback_path.is_absolute():
        feedback_path = REPO_ROOT / feedback_path

    out_path = args.out
    if not out_path.is_absolute():
        out_path = REPO_ROOT / out_path

    prompt = render_prompt(
        audit_brief_path=audit_brief_path,
        feedback_path=feedback_path,
    )

    if args.prompt_out is not None:
        prompt_out = args.prompt_out
        if not prompt_out.is_absolute():
            prompt_out = REPO_ROOT / prompt_out

        prompt_out.parent.mkdir(parents=True, exist_ok=True)
        prompt_out.write_text(prompt, encoding="utf-8")
        print(f"[DONE] Wrote rendered prompt to {prompt_out}")

    trace, raw_text = call_openai(prompt=prompt, model=args.model)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(trace, f, indent=2)

    if args.raw_out is not None:
        raw_out = args.raw_out
        if not raw_out.is_absolute():
            raw_out = REPO_ROOT / raw_out

        raw_out.parent.mkdir(parents=True, exist_ok=True)
        raw_out.write_text(raw_text, encoding="utf-8")
        print(f"[DONE] Wrote raw model output to {raw_out}")

    print(f"[DONE] Wrote audit trace to {out_path}")
    print(f"[INFO] model={args.model}")


if __name__ == "__main__":
    main()