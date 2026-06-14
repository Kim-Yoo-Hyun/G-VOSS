#!/usr/bin/env python3
"""Stage Open3DSG metadata/root files for H001 without large downloads."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT

DEFAULT_LOCAL_DATASET = REPO_ROOT / "local_dataset"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_validation_hardened" / "scans.txt"
DEFAULT_STAGED_ROOT = DEFAULT_LOCAL_DATASET / "Open3DSG_staged" / "h001_runtime"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "open3dsg_ov" / "staged_root"

RAW_SCAN_FILES = (
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
)

OPEN3DSG_SCAN_FILES = (
    "mesh.refined.v2.obj",
    "mesh.refined.mtl",
    "mesh.refined_0.png",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dataset", type=Path, default=DEFAULT_LOCAL_DATASET)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
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


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_file(src: Path, dst: Path) -> dict[str, Any]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {"src": relpath(src), "dst": relpath(dst), "bytes": dst.stat().st_size}


def line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len([line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()])


def stage_scan_link(src_root: Path, dst_root: Path, scan_id: str) -> dict[str, Any]:
    src = src_root / scan_id
    dst = dst_root / scan_id
    record: dict[str, Any] = {"scan": scan_id, "src": relpath(src), "dst": relpath(dst)}
    if not src.exists():
        record["status"] = "missing_source"
        return record
    if dst.is_symlink():
        target = dst.resolve()
        if target == src.resolve():
            record["status"] = "ready_symlink"
        else:
            record["status"] = "blocked_existing_symlink_to_other_target"
            record["existing_target"] = str(target)
        return record
    if dst.exists():
        record["status"] = "ready_existing_directory" if dst.is_dir() else "blocked_existing_non_directory"
        return record
    dst.symlink_to(src.resolve(), target_is_directory=True)
    record["status"] = "created_symlink"
    return record


def filter_validation_relationships(subset_root: Path, selected_scans: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    selected = set(selected_scans)
    validation = load_json(subset_root / "relationships_validation.json")["scans"]
    rows = [row for row in validation if row.get("scan") in selected]
    present = {row.get("scan") for row in rows}
    missing = sorted(selected - present)
    return rows, missing


def count_scan_files(scan_root: Path, scans: list[str], filenames: tuple[str, ...]) -> dict[str, int]:
    return {
        name: sum(1 for scan_id in scans if (scan_root / scan_id / name).exists())
        for name in filenames
    }


def build_manifest(args: argparse.Namespace) -> dict[str, Any]:
    local_dataset = args.local_dataset
    selected_scans = read_scans(args.selected_scans)
    subset_root = local_dataset / "3DSSG_subset"
    source_scan_root = local_dataset / "3RScan" / "scans"
    staged_root = args.staged_root
    staged_data_root = staged_root / "data"
    staged_r3scan = staged_data_root / "3RScan"
    staged_subset = staged_r3scan / "3DSSG_subset"
    staged_output = staged_root / "output"
    staged_scannet = staged_output / "datasets" / "OpenSG_ScanNet"
    staged_r3scan_out = staged_output / "datasets" / "OpenSG_3RScan"

    validation_rows, missing_selected = filter_validation_relationships(subset_root, selected_scans)
    validation_scans = sorted({row["scan"] for row in validation_rows})
    validation_payload = {"scans": validation_rows}
    empty_payload = {"scans": []}

    dirs = [
        staged_root,
        staged_data_root,
        staged_r3scan,
        staged_subset,
        staged_data_root / "SCANNET" / "scannet_3d" / "data",
        staged_data_root / "SCANNET" / "scannet_2d",
        staged_r3scan_out / "views",
        staged_r3scan_out / "preprocessed",
        staged_scannet / "subgraphs",
        staged_scannet / "views",
        staged_scannet / "preprocessed",
        staged_scannet / "instance2labels",
        staged_output / "checkpoints",
        staged_output / "features",
        staged_root / "mlops" / "opensg" / "mlflow",
        staged_root / "mlops" / "opensg" / "tensorboards",
    ]

    copied_files: list[dict[str, Any]] = []
    written_files: list[str] = []
    scan_links: list[dict[str, Any]] = []

    if not args.dry_run:
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)

        for filename in ("classes.txt", "relationships.txt"):
            src = subset_root / filename
            copied_files.append(copy_file(src, staged_r3scan / filename))
            copied_files.append(copy_file(src, staged_subset / filename))

        relationships_text = (subset_root / "relationships.txt").read_text(encoding="utf-8")
        if not relationships_text.endswith("\n"):
            relationships_text += "\n"
        write_text(staged_r3scan / "relationships_custom.txt", relationships_text)
        written_files.append(relpath(staged_r3scan / "relationships_custom.txt"))

        write_json(staged_subset / "relationships_train.json", empty_payload)
        write_json(staged_subset / "relationships_validation.json", validation_payload)
        write_json(staged_subset / "relationships_test.json", validation_payload)
        write_json(staged_subset / "relationships.json", validation_payload)
        written_files.extend(
            relpath(staged_subset / name)
            for name in (
                "relationships_train.json",
                "relationships_validation.json",
                "relationships_test.json",
                "relationships.json",
            )
        )

        write_text(staged_subset / "train_scans.txt", "")
        write_text(staged_subset / "validation_scans.txt", "\n".join(validation_scans) + "\n")
        write_text(staged_subset / "test_scans.txt", "\n".join(validation_scans) + "\n")
        written_files.extend(
            relpath(staged_subset / name)
            for name in ("train_scans.txt", "validation_scans.txt", "test_scans.txt")
        )

        write_json(staged_r3scan / "obj_boxes_train_refined.json", {})
        write_json(staged_r3scan / "obj_boxes_val_refined.json", {})
        written_files.extend(
            relpath(staged_r3scan / name)
            for name in ("obj_boxes_train_refined.json", "obj_boxes_val_refined.json")
        )

        write_json(staged_scannet / "subgraphs" / "relationships_train.json", empty_payload)
        write_json(staged_scannet / "subgraphs" / "relationships_validation.json", empty_payload)
        write_text(staged_scannet / "subgraphs" / "train_scans.txt", "")
        write_text(staged_scannet / "subgraphs" / "validation_scans.txt", "")
        written_files.extend(
            relpath(staged_scannet / "subgraphs" / name)
            for name in (
                "relationships_train.json",
                "relationships_validation.json",
                "train_scans.txt",
                "validation_scans.txt",
            )
        )

        for scan_id in selected_scans:
            scan_links.append(stage_scan_link(source_scan_root, staged_r3scan, scan_id))

    raw_counts = count_scan_files(source_scan_root, selected_scans, RAW_SCAN_FILES)
    open3dsg_counts = count_scan_files(source_scan_root, selected_scans, OPEN3DSG_SCAN_FILES)
    staged_open3dsg_counts = count_scan_files(staged_r3scan, selected_scans, OPEN3DSG_SCAN_FILES)

    link_status_counts: dict[str, int] = {}
    for record in scan_links:
        status = record.get("status", "unknown")
        link_status_counts[status] = link_status_counts.get(status, 0) + 1

    blockers: list[str] = []
    if missing_selected:
        blockers.append(f"missing_selected_scans_in_validation_json:{len(missing_selected)}")
    for name, count in open3dsg_counts.items():
        if count < len(selected_scans):
            blockers.append(f"missing_scan_file:{name}:{count}/{len(selected_scans)}")
    if any(record.get("status", "").startswith("blocked") or record.get("status") == "missing_source" for record in scan_links):
        blockers.append("scan_symlink_blocker")

    config_values = {
        "CONF.PATH.HOME": str(Path.home()),
        "CONF.PATH.BASE": str(staged_root.resolve()),
        "CONF.PATH.DATA": str((staged_root / "data").resolve()),
        "CONF.PATH.DATA_OUT": str((staged_root / "output").resolve()),
        "note": "These values are for a local Open3DSG config-path patch; this script does not patch source files.",
    }
    if not args.dry_run:
        write_json(args.output_dir / "config_paths.json", config_values)

    mesh_texture_ready = bool(selected_scans) and all(
        open3dsg_counts.get(name, 0) == len(selected_scans)
        and staged_open3dsg_counts.get(name, 0) == len(selected_scans)
        for name in OPEN3DSG_SCAN_FILES
    )

    remaining_external_blockers = [
        "Open3DSG checkpoint",
        "blip2_positional_embedding.pt",
        "OpenSeg SavedModel",
        "view pickles",
        "preprocessed pickles",
    ]
    if not mesh_texture_ready:
        remaining_external_blockers.insert(
            0,
            "mesh.refined.v2.obj / mesh.refined.mtl / mesh.refined_0.png for selected scans",
        )

    status = "staged_metadata_root_ready_mesh_texture_ready_external_artifacts_missing"
    if not mesh_texture_ready:
        status = "staged_metadata_root_ready_external_artifacts_missing"
    if missing_selected or any(record.get("status", "").startswith("blocked") for record in scan_links):
        status = "staged_metadata_root_blocked"

    next_action = "Run Open3DSG view pickle generation, then preprocessed pickle generation."
    if not mesh_texture_ready:
        next_action = "Download or acquire Open3DSG mesh/texture files for the selected scans."

    return {
        "schema_version": "h001_open3dsg_staged_root_v1",
        "date_checked": date.today().isoformat(),
        "status": status,
        "staged_root": relpath(staged_root),
        "staged_data_root": relpath(staged_data_root),
        "staged_output_root": relpath(staged_output),
        "selected_scans_file": relpath(args.selected_scans),
        "selected_scan_count": len(selected_scans),
        "validation_subgraphs": len(validation_rows),
        "validation_unique_scans": len(validation_scans),
        "validation_relations": sum(len(row.get("relationships", [])) for row in validation_rows),
        "missing_selected_scans_in_validation_json": missing_selected,
        "relationship_label_count": line_count(subset_root / "relationships.txt"),
        "class_label_count": line_count(subset_root / "classes.txt"),
        "relationships_custom_policy": {
            "source": "3DSSG_subset/relationships.txt",
            "status": "smoke_only_nonfinal_without_official_open3dsg_additional_metadata",
            "line_count": line_count(staged_r3scan / "relationships_custom.txt"),
        },
        "train_split_policy": {
            "relationships_train_json": "empty",
            "reason": "H001 Open3DSG smoke is inference-only; keeping train empty prevents preprocess_3rscan.py from processing the full train split.",
        },
        "written_files": sorted(written_files),
        "copied_files": copied_files,
        "created_directories": [relpath(path) for path in dirs],
        "scan_link_status_counts": link_status_counts,
        "scan_links": scan_links,
        "source_raw_file_counts": raw_counts,
        "source_open3dsg_file_counts": open3dsg_counts,
        "staged_open3dsg_file_counts": staged_open3dsg_counts,
        "scannet_placeholder_policy": "empty train/validation subgraph JSONs plus raw ScanNet placeholder directories for config import",
        "obj_box_policy": "empty smoke-only JSON stubs; current preprocess_3rscan.py branch recomputes axis-aligned boxes with test=True",
        "config_values": config_values,
        "blockers": blockers,
        "mesh_texture_ready": mesh_texture_ready,
        "remaining_external_blockers": remaining_external_blockers,
        "next_action": next_action,
        "claim_limit": "No Open3DSG raw dump, JSONL export, geometry join, metric, or improvement claim exists after metadata/root and mesh/texture staging.",
    }


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    total = manifest["selected_scan_count"]
    lines = [
        "# Open3DSG Staged Root",
        "",
        f"Date: `{manifest['date_checked']}`",
        f"Status: `{manifest['status']}`",
        f"Staged root: `{manifest['staged_root']}`",
        "",
        "## H001 Subset",
        "",
        f"- selected scans: `{total}`",
        f"- validation/test subgraphs: `{manifest['validation_subgraphs']}`",
        f"- validation/test unique scans: `{manifest['validation_unique_scans']}`",
        f"- validation/test relations: `{manifest['validation_relations']}`",
        f"- train split policy: `{manifest['train_split_policy']['relationships_train_json']}`",
        "",
        "## Metadata",
        "",
        f"- classes: `{manifest['class_label_count']}`",
        f"- relationships: `{manifest['relationship_label_count']}`",
        f"- relationships_custom source: `{manifest['relationships_custom_policy']['source']}`",
        f"- relationships_custom status: `{manifest['relationships_custom_policy']['status']}`",
        f"- obj boxes: `{manifest['obj_box_policy']}`",
        f"- ScanNet placeholders: `{manifest['scannet_placeholder_policy']}`",
        "",
        "## Scan Links",
        "",
    ]
    for status, count in sorted(manifest["scan_link_status_counts"].items()):
        lines.append(f"- `{status}`: `{count}`")

    lines.extend(["", "## Open3DSG-Specific Scan Files", "", "| File | Source ready | Staged ready |", "| --- | --- | --- |"])
    for name, count in manifest["source_open3dsg_file_counts"].items():
        staged_count = manifest["staged_open3dsg_file_counts"].get(name, 0)
        lines.append(f"| `{name}` | `{count}/{total}` | `{staged_count}/{total}` |")

    lines.extend(["", "## Remaining Blockers", ""])
    for blocker in manifest["remaining_external_blockers"]:
        lines.append(f"- {blocker}")

    lines.extend(["", "## Claim Limit", "", manifest["claim_limit"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    manifest = build_manifest(args)
    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "manifest.json", manifest)
        write_report(args.output_dir / "report.md", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
