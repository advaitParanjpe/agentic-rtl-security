#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_DIR = REPO_ROOT / "build"

RTL_DIR = REPO_ROOT / "rtl"
TB_DIR = REPO_ROOT / "tb"

TOP_TB = "tb_mini_soc"

SOURCES = [
    RTL_DIR / "soc_pkg.sv",
    RTL_DIR / "mini_soc.sv",
    TB_DIR / "tb_mini_soc.sv",
]


def run_cmd(cmd, cwd=None):
    print(f"\n[CMD] {' '.join(str(x) for x in cmd)}")

    result = subprocess.run(
        cmd,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    print(result.stdout)

    if result.returncode != 0:
        print(f"[ERROR] Command failed with return code {result.returncode}")
        sys.exit(result.returncode)

    return result


def main():
    BUILD_DIR.mkdir(exist_ok=True)

    sim_out = BUILD_DIR / f"{TOP_TB}.vvp"

    compile_cmd = [
        "iverilog",
        "-g2012",
        "-Wall",
        "-I",
        str(RTL_DIR),
        "-s",
        TOP_TB,
        "-o",
        str(sim_out),
    ] + [str(src) for src in SOURCES]

    run_cmd(compile_cmd, cwd=REPO_ROOT)

    run_cmd(["vvp", str(sim_out)], cwd=REPO_ROOT)

    print("\n[DONE] Simulation completed.")


if __name__ == "__main__":
    main()