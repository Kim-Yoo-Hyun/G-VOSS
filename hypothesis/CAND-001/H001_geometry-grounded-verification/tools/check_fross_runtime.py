#!/usr/bin/env python3
"""Check whether local files are ready for a FROSS-to-H001 adapter smoke."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]

DEFAULT_LOCAL_DATASET = REPO_ROOT / "local_dataset"
DEFAULT_RAW_3RSCAN = DEFAULT_LOCAL_DATASET / "3RScan" / "scans"
DEFAULT_STAGED_ROOT = DEFAULT_LOCAL_DATASET / "FROSS_staged" / "3RScan"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_validation_hardened" / "scans.txt"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "fross_scannet20" / "runtime"
DEFAULT_FROSS_SOURCE = Path("/tmp/fross_source")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dataset", type=Path, default=DEFAULT_LOCAL_DATASET)
    parser.add_argument("--raw-3rscan-root", type=Path, default=DEFAULT_RAW_3RSCAN)
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--fross-source", type=Path, default=DEFAULT_FROSS_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


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


def count_scan_files(scan_root: Path, scans: list[str], pattern: str) -> tuple[int, int]:
    scans_with = 0
    total = 0
    for scan_id in scans:
        seq = scan_root / scan_id / "sequence"
        files = list(seq.glob(pattern)) if seq.exists() else []
        if files:
            scans_with += 1
            total += len(files)
    return scans_with, total


def find_pickles(local_dataset: Path) -> list[str]:
    if not local_dataset.exists():
        return []
    return sorted(relpath(path) for path in local_dataset.rglob("predictions_gaussian*.pkl"))


def git_head(path: Path) -> str | None:
    if not (path / ".git").exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def required_staged_files(staged_root: Path) -> dict[str, bool]:
    required = {
        "3DSSG/objects.json": staged_root / "3DSSG" / "objects.json",
        "3DSSG_subset/relationships.json": staged_root / "3DSSG_subset" / "relationships.json",
        "3DSSG_subset/relationships20.json": staged_root / "3DSSG_subset" / "relationships20.json",
        "3DSSG_subset/3dssg_to_scannet.json": staged_root / "3DSSG_subset" / "3dssg_to_scannet.json",
        "3DSSG_subset/validation_scans.txt": staged_root / "3DSSG_subset" / "validation_scans.txt",
        "2DSG20/val.json": staged_root / "2DSG20" / "val.json",
        "2DSG20/rel.json": staged_root / "2DSG20" / "rel.json",
    }
    return {name: path.exists() for name, path in required.items()}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    checks = manifest["checks"]
    lines = [
        "# FROSS Runtime Readiness",
        "",
        f"Date: {manifest['date_checked']}",
        f"Status: `{manifest['status']}`",
        "",
        "## Summary",
        "",
        f"- Selected scans: `{checks['selected_scan_count']}`",
        f"- FROSS source commit: `{manifest.get('fross_source_commit')}`",
        f"- Prediction pickles found: `{len(checks['prediction_pickles'])}`",
        f"- Raw sequence scans: `{checks['raw_sequence_scans']}`",
        f"- Raw rendered-depth scans: `{checks['raw_rendered_depth_scans']}`",
        f"- Raw GT-pose scans: `{checks['raw_gt_pose_scans']}`",
        f"- Raw SLAM-pose scans: `{checks['raw_slam_pose_scans']}`",
        f"- Raw bbox scans: `{checks['raw_bbox_scans']}`",
        f"- Raw visibility scans: `{checks['raw_visibility_scans']}`",
        "",
        "## Blockers",
        "",
    ]
    if manifest["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Staged Files", ""])
    for name, exists in checks["staged_required_files"].items():
        lines.append(f"- `{name}`: `{exists}`")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    scans = read_scans(args.selected_scans)

    raw_sequence_scans = sum(1 for scan in scans if (args.raw_3rscan_root / scan / "sequence").exists())
    raw_rendered_depth_scans, raw_rendered_depth_files = count_scan_files(
        args.raw_3rscan_root, scans, "*.rendered.depth.png"
    )
    raw_depth_scans, raw_depth_files = count_scan_files(args.raw_3rscan_root, scans, "*.depth.pgm")
    raw_color_scans, raw_color_files = count_scan_files(args.raw_3rscan_root, scans, "*.color.jpg")
    raw_gt_pose_scans, raw_gt_pose_files = count_scan_files(args.raw_3rscan_root, scans, "*.pose.txt")
    raw_slam_pose_scans, raw_slam_pose_files = count_scan_files(args.raw_3rscan_root, scans, "*.slam.pose.txt")
    raw_bbox_scans, raw_bbox_files = count_scan_files(args.raw_3rscan_root, scans, "*.bb.txt")
    raw_visibility_scans, raw_visibility_files = count_scan_files(args.raw_3rscan_root, scans, "*.visibility.txt")

    staged_data_root = args.staged_root / "data"
    staged_sequence_scans = sum(1 for scan in scans if (staged_data_root / scan / "sequence").exists())
    staged_rendered_depth_scans, staged_rendered_depth_files = count_scan_files(
        staged_data_root, scans, "*.rendered.depth.png"
    )

    checks: dict[str, Any] = {
        "selected_scan_count": len(scans),
        "selected_scans_file": relpath(args.selected_scans),
        "prediction_pickles": find_pickles(args.local_dataset),
        "raw_3rscan_root": relpath(args.raw_3rscan_root),
        "raw_sequence_scans": raw_sequence_scans,
        "raw_color_scans": raw_color_scans,
        "raw_color_files": raw_color_files,
        "raw_depth_scans": raw_depth_scans,
        "raw_depth_files": raw_depth_files,
        "raw_rendered_depth_scans": raw_rendered_depth_scans,
        "raw_rendered_depth_files": raw_rendered_depth_files,
        "raw_gt_pose_scans": raw_gt_pose_scans,
        "raw_gt_pose_files": raw_gt_pose_files,
        "raw_slam_pose_scans": raw_slam_pose_scans,
        "raw_slam_pose_files": raw_slam_pose_files,
        "raw_bbox_scans": raw_bbox_scans,
        "raw_bbox_files": raw_bbox_files,
        "raw_visibility_scans": raw_visibility_scans,
        "raw_visibility_files": raw_visibility_files,
        "staged_root": relpath(args.staged_root),
        "staged_root_exists": args.staged_root.exists(),
        "staged_sequence_scans": staged_sequence_scans,
        "staged_rendered_depth_scans": staged_rendered_depth_scans,
        "staged_rendered_depth_files": staged_rendered_depth_files,
        "staged_required_files": required_staged_files(args.staged_root),
    }

    blockers: list[str] = []
    if not checks["prediction_pickles"]:
        blockers.append("missing_fross_prediction_pickle")
    if not checks["staged_root_exists"]:
        blockers.append("missing_fross_staged_root")
    if not checks["staged_required_files"]["3DSSG_subset/relationships20.json"]:
        blockers.append("missing_relationships20_json")
    if not checks["staged_required_files"]["3DSSG_subset/3dssg_to_scannet.json"]:
        blockers.append("missing_3dssg_to_scannet_mapping")
    if raw_rendered_depth_scans == 0 and staged_rendered_depth_scans == 0:
        blockers.append("missing_rendered_depth_for_scannet_loader")
    if raw_bbox_scans == 0 and not checks["staged_required_files"]["2DSG20/val.json"]:
        blockers.append("missing_2dsg20_or_bbox_visibility_for_gt2dsg")

    if checks["prediction_pickles"]:
        status = "ready_for_adapter"
    elif len(blockers) == 0:
        status = "ready_for_fross_run"
    else:
        status = "blocked_runtime_artifact"

    manifest = {
        "schema_version": "h001_fross_runtime_readiness_v1",
        "date_checked": date.today().isoformat(),
        "status": status,
        "fross_source": relpath(args.fross_source),
        "fross_source_commit": git_head(args.fross_source),
        "checks": checks,
        "blockers": blockers,
    }

    if not args.dry_run:
        write_json(args.output_dir / "manifest.json", manifest)
        write_report(args.output_dir / "report.md", manifest)

    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status != "ready_for_adapter" else 0


if __name__ == "__main__":
    raise SystemExit(main())
