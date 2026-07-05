#!/usr/bin/env python3
"""Prepare a clean Open3DSG baseline-reproduction root.

This utility intentionally separates the baseline-reproduction route from the
H001 Open3DSG runtime roots. It materializes the public Open3DSG source at a
fixed commit and stages a data root that uses the unfiltered 3DSSG train/dev
metadata where available.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_REPO_URL = "https://github.com/kochsebastian/Open3DSG.git"
DEFAULT_COMMIT = "a568358d6bb718929aa9ff67b2dfdecc4a4c3261"


def run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def rel_symlink(src: Path, dst: Path) -> None:
    if dst.exists() or dst.is_symlink():
        return
    ensure_dir(dst.parent)
    dst.symlink_to(os.path.relpath(src, dst.parent), target_is_directory=src.is_dir())


def copy_text(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)


def count_scans(json_path: Path) -> tuple[int, int, int]:
    data = json.loads(json_path.read_text())
    scans = data.get("scans", [])
    objects = sum(len(scan.get("objects", [])) for scan in scans)
    rels = sum(len(scan.get("relationships", [])) for scan in scans)
    return len(scans), objects, rels


def materialize_source(root: Path, repo_url: str, commit: str) -> dict[str, str]:
    source_root = root / "source" / "open3dsg_public"
    ensure_dir(source_root.parent)
    if not source_root.exists():
        run(["git", "clone", repo_url, str(source_root)])
    run(["git", "fetch", "--all", "--tags"], cwd=source_root)
    run(["git", "checkout", "--detach", commit], cwd=source_root)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source_root, text=True).strip()
    return {"source_root": str(source_root), "repo_url": repo_url, "commit": actual}


def patch_path_config(source_root: Path) -> None:
    config_path = source_root / "open3dsg" / "config" / "config.py"
    config_path.write_text(
        '''# Copyright (c) 2024 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

"""Environment-driven path config for baseline reproduction."""

import os
import sys
from easydict import EasyDict

CONF = EasyDict()

CONF.PATH = EasyDict()
CONF.PATH.HOME = os.environ.get("OPEN3DSG_HOME", os.path.expanduser("~"))
CONF.PATH.BASE = os.environ["OPEN3DSG_BASE"]
CONF.PATH.DATA = os.environ["OPEN3DSG_DATA"]

for _, path in CONF.PATH.items():
    if path not in sys.path:
        sys.path.append(path)

CONF.PATH.R3SCAN_RAW = os.path.join(CONF.PATH.DATA, "3RScan")
CONF.PATH.SCANNET_RAW = os.path.join(CONF.PATH.DATA, "SCANNET")
CONF.PATH.SCANNET_RAW3D = os.path.join(CONF.PATH.SCANNET_RAW, "scannet_3d", "data")
CONF.PATH.SCANNET_RAW2D = os.path.join(CONF.PATH.SCANNET_RAW, "scannet_2d")

CONF.PATH.DATA_OUT = os.environ["OPEN3DSG_DATA_OUT"]
CONF.PATH.R3SCAN = os.path.join(CONF.PATH.DATA_OUT, "datasets", "OpenSG_3RScan")
CONF.PATH.SCANNET = os.path.join(CONF.PATH.DATA_OUT, "datasets", "OpenSG_ScanNet")
CONF.PATH.CHECKPOINTS = os.path.join(CONF.PATH.DATA_OUT, "checkpoints")
CONF.PATH.FEATURES = os.path.join(CONF.PATH.DATA_OUT, "features")

CONF.PATH.MLOPS = os.path.join(CONF.PATH.BASE, "mlops")
CONF.PATH.MLFLOW = os.path.join(CONF.PATH.MLOPS, "opensg", "mlflow")
CONF.PATH.TENSORBOARD = os.path.join(CONF.PATH.MLOPS, "opensg", "tensorboards")

for name, path in CONF.PATH.items():
    assert os.path.exists(path), f"{name}={path} does not exist"
''',
        encoding="utf-8",
    )


def materialize_data(root: Path, source_data: Path) -> dict[str, object]:
    data_root = root / "data"
    dst_3rscan = data_root / "3RScan"
    src_3rscan = source_data / "3RScan"
    src_subset = src_3rscan / "3DSSG_subset"
    dst_subset = dst_3rscan / "3DSSG_subset"

    for directory in (data_root, dst_3rscan, dst_subset):
        ensure_dir(directory)

    for item in src_3rscan.iterdir():
        if item.name in {"3DSSG_subset", "classes.txt", "relationships.txt"}:
            continue
        rel_symlink(item, dst_3rscan / item.name)

    copy_text(src_subset / "classes.txt", dst_3rscan / "classes.txt")
    copy_text(src_subset / "relationships.txt", dst_3rscan / "relationships.txt")

    subset_overrides = {
        "relationships_train.json": "relationships_train.unfiltered.json",
        "relationships_validation.json": "relationships_validation.unfiltered.json",
        "train_scans.txt": "train_scans.unfiltered.txt",
        "validation_scans.txt": "validation_scans.unfiltered.txt",
    }
    for item in src_subset.iterdir():
        target = dst_subset / item.name
        if item.name in subset_overrides.values():
            rel_symlink(item, target)
        elif item.name in subset_overrides:
            src_name = subset_overrides[item.name]
            src_override = src_subset / src_name
            rel_symlink(src_override if src_override.exists() else item, target)
        else:
            rel_symlink(item, target)

    if (source_data / "SCANNET").exists():
        rel_symlink(source_data / "SCANNET", data_root / "SCANNET")

    output_root = root / "output"
    for directory in (
        output_root,
        output_root / "datasets" / "OpenSG_3RScan" / "views",
        output_root / "datasets" / "OpenSG_3RScan" / "preprocessed",
        output_root / "datasets" / "OpenSG_ScanNet",
        output_root / "features",
        output_root / "checkpoints",
        root / "mlops" / "opensg" / "mlflow",
        root / "mlops" / "opensg" / "tensorboards",
    ):
        ensure_dir(directory)

    train_count = count_scans(dst_subset / "relationships_train.json")
    val_count = count_scans(dst_subset / "relationships_validation.json")
    return {
        "data_root": str(data_root),
        "r3scan_root": str(dst_3rscan),
        "train_subgraphs": train_count[0],
        "train_objects": train_count[1],
        "train_relationships": train_count[2],
        "validation_subgraphs": val_count[0],
        "validation_objects": val_count[1],
        "validation_relationships": val_count[2],
    }


def write_manifest(root: Path, source_info: dict[str, str], data_info: dict[str, object]) -> Path:
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "prepared",
        "baseline_root": str(root),
        "source": source_info,
        "data": data_info,
        "notes": [
            "This root is for Open3DSG baseline paper-table reproduction, not H001 GeoCalib evaluation.",
            "3DSSG train/validation metadata uses unfiltered files when the staged source provides them.",
            "Root classes.txt and relationships.txt are aligned to the 3DSSG subset label spaces for paper-style 160-object/27-relation evaluation.",
        ],
    }
    path = root / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--baseline-root", type=Path, default=Path("local_dataset/Open3DSG_staged/baseline_repro"))
    parser.add_argument("--source-data", type=Path, default=Path("local_dataset/Open3DSG_staged/training_repro/data"))
    parser.add_argument("--repo-url", default=DEFAULT_REPO_URL)
    parser.add_argument("--commit", default=DEFAULT_COMMIT)
    parser.add_argument("--skip-source", action="store_true")
    parser.add_argument("--patch-path-config", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    baseline_root = (repo_root / args.baseline_root).resolve()
    source_data = (repo_root / args.source_data).resolve()

    if not source_data.exists():
        raise FileNotFoundError(f"source data root not found: {source_data}")
    ensure_dir(baseline_root)

    if args.skip_source:
        source_root = baseline_root / "source" / "open3dsg_public"
        source_info = {"source_root": str(source_root), "repo_url": args.repo_url, "commit": args.commit}
    else:
        source_info = materialize_source(baseline_root, args.repo_url, args.commit)

    if args.patch_path_config:
        patch_path_config(Path(source_info["source_root"]))
        source_info["path_config_patch"] = "env_path_config_only"

    data_info = materialize_data(baseline_root, source_data)
    manifest_path = write_manifest(baseline_root, source_info, data_info)
    print(json.dumps(json.loads(manifest_path.read_text()), indent=2))


if __name__ == "__main__":
    main()
