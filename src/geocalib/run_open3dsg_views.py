#!/usr/bin/env python3
"""Run/audit Open3DSG view pickle generation for selected H001 scans."""

from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import importlib
import json
import os
import pickle
import shutil
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT

DEFAULT_LOCAL_DATASET = REPO_ROOT / "local_dataset"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_validation_hardened" / "scans.txt"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "open3dsg_ov" / "views"
DEFAULT_SOURCE = Path("/tmp/open3dsg_source")
DEFAULT_STAGED_ROOT = DEFAULT_LOCAL_DATASET / "Open3DSG_staged" / "h001_runtime"
DEFAULT_WORK_SOURCE = DEFAULT_STAGED_ROOT / "source" / "open3dsg_source"


PATCHED_CONFIG = '''# Copyright (c) 2024 Robert Bosch GmbH
# SPDX-License-Identifier: AGPL-3.0

"""H001 runtime-patched Open3DSG path config."""

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
'''


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open3dsg-source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--work-source", type=Path, default=DEFAULT_WORK_SOURCE)
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--mode", default="validation", choices=("train", "test", "validation"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--scan-id", action="append", default=None)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--refresh-source", action="store_true")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_scans(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def selected_scans(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    all_scans = unique_preserve_order(args.scan_id or read_scans(args.selected_scans))
    if args.scan_id:
        return all_scans, all_scans
    start = max(args.offset, 0)
    end = None if args.limit is None else start + max(args.limit, 0)
    return all_scans, all_scans[start:end]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def install_numpy_pickle_compat() -> None:
    try:
        import numpy.core as np_core  # type: ignore
        import numpy.core.multiarray as np_multiarray  # type: ignore
        import numpy.core.numeric as np_numeric  # type: ignore
    except Exception:
        return
    sys.modules.setdefault("numpy._core", np_core)
    sys.modules.setdefault("numpy._core.multiarray", np_multiarray)
    sys.modules.setdefault("numpy._core.numeric", np_numeric)


def copy_open3dsg_source(source: Path, work_source: Path, refresh: bool) -> None:
    source_pkg = source / "open3dsg"
    if not source_pkg.exists():
        raise FileNotFoundError(f"missing Open3DSG package: {source_pkg}")
    if refresh and work_source.exists():
        shutil.rmtree(work_source)
    work_source.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_pkg, work_source / "open3dsg", dirs_exist_ok=True)
    for name in ("README.md", "requirements.txt", "pyproject.toml", "LICENSE.md", "NOTICE"):
        src = source / name
        if src.exists():
            shutil.copy2(src, work_source / name)


def patch_config(source: Path, work_source: Path, output_dir: Path) -> str:
    src_config = source / "open3dsg" / "config" / "config.py"
    dst_config = work_source / "open3dsg" / "config" / "config.py"
    original = src_config.read_text(encoding="utf-8")
    dst_config.write_text(PATCHED_CONFIG, encoding="utf-8")
    patch = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            PATCHED_CONFIG.splitlines(keepends=True),
            fromfile=relpath(src_config),
            tofile=relpath(dst_config),
        )
    )
    patch_path = output_dir / "config_patch.diff"
    patch_path.parent.mkdir(parents=True, exist_ok=True)
    patch_path.write_text(patch, encoding="utf-8")
    return relpath(patch_path)


def runtime_env(staged_root: Path, work_source: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["OPEN3DSG_HOME"] = str(Path.home())
    env["OPEN3DSG_BASE"] = str(staged_root.resolve())
    env["OPEN3DSG_DATA"] = str((staged_root / "data").resolve())
    env["OPEN3DSG_DATA_OUT"] = str((staged_root / "output").resolve())
    current_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(work_source.resolve()) if not current_pythonpath else f"{work_source.resolve()}:{current_pythonpath}"
    return env


def configure_import(staged_root: str, work_source: str) -> None:
    os.environ["OPEN3DSG_HOME"] = str(Path.home())
    os.environ["OPEN3DSG_BASE"] = staged_root
    os.environ["OPEN3DSG_DATA"] = str(Path(staged_root) / "data")
    os.environ["OPEN3DSG_DATA_OUT"] = str(Path(staged_root) / "output")
    if work_source not in sys.path:
        sys.path.insert(0, work_source)


def view_path(staged_root: Path, scan_id: str) -> Path:
    return staged_root / "output" / "datasets" / "OpenSG_3RScan" / "views" / f"{scan_id}_object2image.pkl"


def inspect_view_pickle(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"exists": False, "valid_pickle": False, "object_count": 0, "frame_ref_count": 0, "size_bytes": 0}
    size = path.stat().st_size
    try:
        install_numpy_pickle_compat()
        with path.open("rb") as handle:
            payload = pickle.load(handle)
        object_count = len(payload) if isinstance(payload, dict) else 0
        frame_ref_count = sum(len(value) for value in payload.values()) if isinstance(payload, dict) else 0
        return {
            "exists": True,
            "valid_pickle": True,
            "object_count": object_count,
            "frame_ref_count": frame_ref_count,
            "size_bytes": size,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "exists": True,
            "valid_pickle": False,
            "object_count": 0,
            "frame_ref_count": 0,
            "size_bytes": size,
            "error": f"{type(exc).__name__}:{exc}",
        }


def run_one(scan_id: str, staged_root: str, work_source: str, mode: str, audit_only: bool) -> dict[str, Any]:
    configure_import(staged_root, work_source)
    out_path = view_path(Path(staged_root), scan_id)
    before = inspect_view_pickle(out_path)
    action = "already_ready" if before["valid_pickle"] and before["object_count"] > 0 else "audit_missing"
    error = None
    traceback_text = None
    after = before

    if not audit_only and action != "already_ready":
        try:
            module = importlib.import_module("open3dsg.data.get_object_frame")
            root = Path(staged_root) / "data" / "3RScan" / "3DSSG_subset"
            scene_data, _ = module.read_json(str(root), mode)
            if scan_id not in scene_data:
                raise KeyError(f"{scan_id} not in staged relationships_{mode}.json")
            export_path = Path(staged_root) / "output" / "datasets" / "OpenSG_3RScan" / "views"
            module.run(scan_id, scene_data=scene_data, export_path=str(export_path), dataset="R3SCAN")
            action = "generated"
        except Exception as exc:  # noqa: BLE001
            action = "failed"
            error = f"{type(exc).__name__}:{exc}"
            traceback_text = traceback.format_exc(limit=20)
        after = inspect_view_pickle(out_path)

    if action in {"generated", "already_ready"} and not (after["valid_pickle"] and after["object_count"] > 0):
        action = "missing_output"

    return {
        "scan_id": scan_id,
        "path": relpath(out_path),
        "before": before,
        "after": after,
        "action": action,
        "error": error,
        "traceback": traceback_text,
    }


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    actions = Counter(record["action"] for record in records)
    ready = [record for record in records if record["after"]["valid_pickle"] and record["after"]["object_count"] > 0]
    failed = [record for record in records if record["action"] in {"failed", "missing_output"}]
    return {
        "processed_scan_count": len(records),
        "ready_scan_count": len(ready),
        "missing_scan_count": len(records) - len(ready),
        "actions": dict(sorted(actions.items())),
        "failed_records": failed,
        "total_size_bytes": sum(record["after"]["size_bytes"] for record in ready),
        "total_object_count": sum(record["after"]["object_count"] for record in ready),
        "total_frame_ref_count": sum(record["after"]["frame_ref_count"] for record in ready),
    }


def build_manifest(
    args: argparse.Namespace,
    all_scans: list[str],
    scans: list[str],
    records: list[dict[str, Any]],
    config_patch: str,
) -> dict[str, Any]:
    summary = summarize(records)
    ready = summary["missing_scan_count"] == 0 and bool(scans)
    status = "views_ready" if ready else "views_blocked"
    if args.audit_only and not ready:
        status = "views_audit_missing"
    blockers = []
    if summary["missing_scan_count"]:
        blockers.append(f"missing_view_pickles:{summary['ready_scan_count']}/{len(scans)}")
    return {
        "schema_version": "h001_open3dsg_views_v1",
        "date_checked": now_iso(),
        "status": status,
        "mode": args.mode,
        "audit_only": args.audit_only,
        "workers": max(1, args.workers),
        "open3dsg_source": relpath(args.open3dsg_source),
        "work_source": relpath(args.work_source),
        "staged_root": relpath(args.staged_root),
        "view_root": relpath(args.staged_root / "output" / "datasets" / "OpenSG_3RScan" / "views"),
        "config_patch": config_patch,
        "selected_scans_file": relpath(args.selected_scans),
        "all_selected_scan_count": len(all_scans),
        "processed_scan_count": len(scans),
        "offset": args.offset,
        "limit": args.limit,
        "summary": summary,
        "blockers": blockers,
        "claim_limit": "No Open3DSG raw dump, prediction JSONL, geometry join, metric, or improvement claim exists after view pickle generation.",
        "next_action": "Run Open3DSG preprocess generation after view pickles are ready.",
    }


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    summary = manifest["summary"]
    lines = [
        "# Open3DSG View Pickle Generation",
        "",
        f"Date: `{manifest['date_checked']}`",
        f"Status: `{manifest['status']}`",
        f"Mode: `{manifest['mode']}`",
        f"Processed scans: `{manifest['processed_scan_count']}`",
        f"Workers: `{manifest['workers']}`",
        f"View root: `{manifest['view_root']}`",
        "",
        "## Readiness",
        "",
        f"- ready scans: `{summary['ready_scan_count']}/{manifest['processed_scan_count']}`",
        f"- missing scans: `{summary['missing_scan_count']}`",
        f"- total object entries: `{summary['total_object_count']}`",
        f"- total frame references: `{summary['total_frame_ref_count']}`",
        "",
        "## Actions",
        "",
    ]
    for action, count in summary["actions"].items():
        lines.append(f"- `{action}`: `{count}`")
    lines.extend(["", "## Blockers", ""])
    if manifest["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Claim Limit", "", manifest["claim_limit"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    all_scans, scans = selected_scans(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    copy_open3dsg_source(args.open3dsg_source, args.work_source, args.refresh_source)
    config_patch = patch_config(args.open3dsg_source, args.work_source, args.output_dir)
    env = runtime_env(args.staged_root, args.work_source)
    os.environ.update({key: value for key, value in env.items() if key.startswith("OPEN3DSG_")})
    if str(args.work_source.resolve()) not in sys.path:
        sys.path.insert(0, str(args.work_source.resolve()))

    records: list[dict[str, Any]] = []
    workers = max(1, args.workers)
    if workers == 1:
        for idx, scan_id in enumerate(scans, start=1):
            record = run_one(scan_id, str(args.staged_root.resolve()), str(args.work_source.resolve()), args.mode, args.audit_only)
            records.append(record)
            print(f"[{idx}/{len(scans)}] {scan_id} {record['action']} ready={record['after']['valid_pickle']} objects={record['after']['object_count']}")
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(run_one, scan_id, str(args.staged_root.resolve()), str(args.work_source.resolve()), args.mode, args.audit_only)
                for scan_id in scans
            ]
            for idx, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                record = future.result()
                records.append(record)
                print(f"[{idx}/{len(scans)}] {record['scan_id']} {record['action']} ready={record['after']['valid_pickle']} objects={record['after']['object_count']}")

    records.sort(key=lambda item: item["scan_id"])
    manifest = build_manifest(args, all_scans, scans, records, config_patch)
    write_json(args.output_dir / "manifest.json", manifest)
    write_jsonl(args.output_dir / "records.jsonl", records)
    write_report(args.output_dir / "report.md", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if manifest["status"] == "views_ready" or args.audit_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
