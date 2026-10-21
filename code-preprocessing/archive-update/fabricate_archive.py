#!/usr/bin/env python3
"""Fabricate COCO's C core and build the cocoprep Cython archive extension.

Example:
    python fabricate_archive.py --coco-experiment /path/to/coco-experiment --editable

This is an adapter to COCO's *own* scripts/fabricate, not a substitute for it.
The extension compiles the freshly generated C core into a separate Python
module, so it does not depend on private symbols in an installed cocoex wheel.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def _run(command: list[str], cwd: Path) -> None:
    print("+ " + " ".join(command), flush=True)
    subprocess.run(command, cwd=str(cwd), check=True)


def _find_c_core(experiment: Path) -> tuple[Path, Path]:
    """Locate the amalgamated C artifacts emitted by upstream fabricate."""
    for relative in ("build/c", "build/python/cython"):
        build = experiment / relative
        c_file = build / "coco.c"
        h_file = build / "coco.h"
        if c_file.is_file() and h_file.is_file():
            return c_file, h_file
    raise FileNotFoundError(
        "COCO's generated coco.c and coco.h were not found in build/c/ "
        "or build/python/cython/. Check the output of scripts/fabricate."
    )


def stage_archive_core(experiment: Path, run_fabricate: bool = True) -> tuple[Path, Path]:
    experiment = experiment.expanduser().resolve()
    if not experiment.is_dir():
        raise FileNotFoundError(f"COCO experiment checkout not found: {experiment}")
    upstream = experiment / "scripts" / "fabricate"
    if run_fabricate:
        if not upstream.is_file():
            raise FileNotFoundError(f"COCO fabricate script not found: {upstream}")
        _run([sys.executable, str(upstream)], experiment)

    core_c, core_h = _find_c_core(experiment)
    # Fail early with a useful diagnostic when the upstream API changes.
    header = core_h.read_text(encoding="utf-8", errors="replace")
    symbols = (
        "coco_archive_t", "coco_archive(", "coco_archive_add_solution(",
        "coco_archive_get_number_of_solutions(",
        "coco_archive_get_hypervolume(",
        "coco_archive_get_next_solution_text(", "coco_archive_free(",
        "coco_set_log_level(",
    )
    missing = [name for name in symbols if name not in header]
    if missing:
        raise RuntimeError(
            f"Generated COCO header {core_h} lacks expected archive C API: {missing}. "
            "Check for API changes in your coco-experiment version."
        )

    target = HERE / "interface"
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(core_c, target / "coco.c")
    shutil.copy2(core_h, target / "coco.h")
    print(f"Staged {core_c} and {core_h} into {target}", flush=True)
    return target / "coco.c", target / "coco.h"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--coco-experiment", type=Path, required=True,
        help="path to the current numbbo/coco-experiment checkout",
    )
    parser.add_argument(
        "--prepare-only", action="store_true",
        help="run fabricate and stage sources, but do not build/install the extension",
    )
    parser.add_argument(
        "--editable", action="store_true",
        help="install cocoprep in editable mode (for development)",
    )
    parser.add_argument(
        "--no-build-isolation", action="store_true",
        help="use already installed setuptools, wheel and Cython (offline builds)",
    )
    parser.add_argument(
        "--skip-fabricate", action="store_true",
        help="reuse pre-generated COCO C core; useful for CI only",
    )
    args = parser.parse_args(argv)
    stage_archive_core(args.coco_experiment, run_fabricate=not args.skip_fabricate)

    if not args.prepare_only:
        command = [sys.executable, "-m", "pip", "install"]
        if args.no_build_isolation:
            command.append("--no-build-isolation")
        if args.editable:
            command.append("--editable")
        command.append(".")
        _run(command, HERE)
        print("Installed cocoprep (compiled C-backed archive).", flush=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (FileNotFoundError, RuntimeError, subprocess.CalledProcessError) as exc:
        sys.exit(f"ERROR: {exc}")
