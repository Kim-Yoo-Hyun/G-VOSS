#!/usr/bin/env python3
"""Docker wrapper for Open3DSG train/validation-split view pickle generation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def repo_root() -> Path:
    path = Path(__file__).resolve()
    for parent in path.parents:
        if (parent / "README.md").is_file() and (parent / "TODO.md").is_file():
            return parent
    raise RuntimeError(f"could not locate repo root from {path}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    staged_root = root / "local_dataset/Open3DSG_staged/training_repro"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staged-root", type=Path, default=staged_root)
    parser.add_argument("--open3dsg-source", type=Path, default=staged_root / "source/open3dsg_source")
    parser.add_argument("--work-source", type=Path, default=staged_root / "work/open3dsg_train_source")
    parser.add_argument("--split", default="train", choices=("train", "validation", "test"))
    parser.add_argument("--selected-scans", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--scan-id", action="append", default=None)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--refresh-source", action="store_true")
    args = parser.parse_args()
    if args.selected_scans is None:
        args.selected_scans = (
            args.staged_root / "data/3RScan/3DSSG_subset" / f"{args.split}_scans.txt"
        )
    if args.output_dir is None:
        label = "train_views" if args.split == "train" else f"{args.split}_views"
        args.output_dir = root / "experiments/H001_geom_reliability/sources/open3dsg" / label
    return args


def main() -> int:
    root = repo_root()
    tools_dir = root / "hypothesis/CAND-001/H001_geometry-grounded-verification/tools"
    sys.path.insert(0, str(tools_dir))
    import run_open3dsg_views  # noqa: PLC0415

    args = parse_args()
    forwarded = [
        "run_open3dsg_views.py",
        "--open3dsg-source",
        str(args.open3dsg_source),
        "--work-source",
        str(args.work_source),
        "--staged-root",
        str(args.staged_root),
        "--selected-scans",
        str(args.selected_scans),
        "--output-dir",
        str(args.output_dir),
        "--mode",
        args.split,
        "--workers",
        str(args.workers),
        "--offset",
        str(args.offset),
    ]
    if args.limit is not None:
        forwarded.extend(["--limit", str(args.limit)])
    for scan_id in args.scan_id or []:
        forwarded.extend(["--scan-id", scan_id])
    if args.audit_only:
        forwarded.append("--audit-only")
    if args.refresh_source:
        forwarded.append("--refresh-source")

    sys.argv = forwarded
    return run_open3dsg_views.main()


if __name__ == "__main__":
    raise SystemExit(main())
