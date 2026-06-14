#!/usr/bin/env python3
"""Stage H001 held-out 3RScan scan symlinks for Open3DSG eval feature dumping."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_eval_payload_stage_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime"),
    )
    parser.add_argument("--raw-scans-root", type=Path, default=Path("local_dataset/3RScan/scans"))
    parser.add_argument(
        "--selected-scans",
        type=Path,
        default=Path(
            "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/subset/"
            "h001_validation_hardened/scans.txt"
        ),
    )
    parser.add_argument(
        "--relationships-validation",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime/data/3RScan/3DSSG_subset/relationships_validation.json"),
    )
    parser.add_argument(
        "--subset-root",
        type=Path,
        default=Path("local_dataset/3DSSG_subset"),
        help="Source 3DSSG_subset root for classes/relationships files.",
    )
    parser.add_argument(
        "--source-template-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source"),
        help="Existing patched Open3DSG source root to link into the runtime root.",
    )
    parser.add_argument(
        "--checkpoint-template-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime/output/checkpoints"),
        help="Existing Open3DSG checkpoint/cache root to link into the runtime output root.",
    )
    parser.add_argument(
        "--runtime-template-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime"),
        help="Existing Open3DSG runtime root used for shared SCANNET and 3RScan metadata.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/h001_eval_payload"),
    )
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_scan_ids(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")


def symlink_record(repo_root: Path, src: Path, dst: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "src": relpath(repo_root, src),
        "dst": relpath(repo_root, dst),
        "src_exists": src.is_dir(),
    }
    if not src.is_dir():
        record["status"] = "missing_source"
        return record
    dst.parent.mkdir(parents=True, exist_ok=True)
    relative_target = os.path.relpath(src.resolve(), dst.parent.resolve())
    if dst.is_symlink():
        current = os.readlink(dst)
        if current == relative_target:
            record["status"] = "ready_symlink"
        else:
            dst.unlink()
            dst.symlink_to(relative_target, target_is_directory=True)
            record["status"] = "normalized_symlink"
        return record
    if dst.exists():
        record["status"] = "ready_existing_path" if dst.is_dir() else "blocked_existing_non_dir"
        return record
    dst.symlink_to(relative_target, target_is_directory=True)
    record["status"] = "created_symlink"
    return record


def symlink_path(repo_root: Path, src: Path, dst: Path, *, is_dir: bool = True) -> dict[str, Any]:
    record: dict[str, Any] = {
        "src": relpath(repo_root, src),
        "dst": relpath(repo_root, dst),
        "src_exists": src.is_dir() if is_dir else src.is_file(),
    }
    if not record["src_exists"]:
        record["status"] = "missing_source"
        return record
    dst.parent.mkdir(parents=True, exist_ok=True)
    relative_target = os.path.relpath(src.resolve(), dst.parent.resolve())
    if dst.is_symlink():
        current = os.readlink(dst)
        if current == relative_target:
            record["status"] = "ready_symlink"
        else:
            dst.unlink()
            dst.symlink_to(relative_target, target_is_directory=is_dir)
            record["status"] = "normalized_symlink"
        return record
    if dst.exists():
        record["status"] = "ready_existing_path" if (dst.is_dir() if is_dir else dst.is_file()) else "blocked_existing_wrong_type"
        return record
    dst.symlink_to(relative_target, target_is_directory=is_dir)
    record["status"] = "created_symlink"
    return record


def copy_file_if_needed(src: Path, dst: Path) -> dict[str, Any]:
    record = {
        "src": str(src),
        "dst": str(dst),
        "src_exists": src.is_file(),
    }
    if not src.is_file():
        record["status"] = "missing_source"
        return record
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dst.resolve() if dst.exists() else False:
        record["status"] = "same_path"
        return record
    shutil.copy2(src, dst)
    record["status"] = "copied"
    record["bytes"] = dst.stat().st_size
    return record


def write_lines_if_needed(path: Path, lines: list[str]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(f"{line}\n" for line in lines)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return {"path": str(path), "status": "ready_existing", "lines": len(lines)}
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "status": "written", "lines": len(lines)}


def write_empty_relationships(path: Path) -> dict[str, Any]:
    payload = {"scans": []}
    content = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return {"path": str(path), "status": "ready_existing", "contexts": 0}
    path.write_text(content, encoding="utf-8")
    return {"path": str(path), "status": "written", "contexts": 0}


def stage_subset_files(
    *,
    repo_root: Path,
    runtime_root: Path,
    subset_root: Path,
    relationships_validation: Path,
    selected_scan_ids: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    out_root = runtime_root / "data/3RScan/3DSSG_subset"
    records: list[dict[str, Any]] = []
    blockers: list[str] = []
    for filename in ("classes.txt", "relationships.txt", "relationships.json"):
        src = subset_root / filename
        dst = out_root / filename
        record = copy_file_if_needed(src, dst)
        record["dst"] = relpath(repo_root, dst)
        records.append(record)
        if record["status"] == "missing_source":
            blockers.append(f"missing_subset_file:{filename}")

    for filename in ("relationships_validation.json", "relationships_test.json"):
        dst = out_root / filename
        record = copy_file_if_needed(relationships_validation, dst)
        record["dst"] = relpath(repo_root, dst)
        records.append(record)
        if record["status"] == "missing_source":
            blockers.append(f"missing_relationships_validation:{relationships_validation}")

    train_record = write_empty_relationships(out_root / "relationships_train.json")
    train_record["path"] = relpath(repo_root, out_root / "relationships_train.json")
    records.append(train_record)

    for filename in ("validation_scans.txt", "test_scans.txt"):
        path = out_root / filename
        record = write_lines_if_needed(path, selected_scan_ids)
        record["path"] = relpath(repo_root, path)
        records.append(record)

    train_scans = write_lines_if_needed(out_root / "train_scans.txt", [])
    train_scans["path"] = relpath(repo_root, out_root / "train_scans.txt")
    records.append(train_scans)
    return records, blockers


def stage_runtime_metadata(
    *,
    repo_root: Path,
    runtime_root: Path,
    runtime_template_root: Path,
) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    blockers: list[str] = []
    scannet_record = symlink_path(
        repo_root,
        runtime_template_root / "data/SCANNET",
        runtime_root / "data/SCANNET",
        is_dir=True,
    )
    records.append({"name": "SCANNET", **scannet_record})
    if scannet_record["status"] == "missing_source" or scannet_record["status"].startswith("blocked"):
        blockers.append(f"runtime_metadata:SCANNET:{scannet_record['status']}")

    for filename in (
        "classes.txt",
        "relationships.txt",
        "relationships_custom.txt",
        "obj_boxes_train_refined.json",
        "obj_boxes_val_refined.json",
    ):
        src = runtime_template_root / "data/3RScan" / filename
        dst = runtime_root / "data/3RScan" / filename
        record = copy_file_if_needed(src, dst)
        record["name"] = filename
        record["dst"] = relpath(repo_root, dst)
        records.append(record)
        if record["status"] == "missing_source":
            blockers.append(f"runtime_metadata:{filename}:missing_source")

    for dirname in ("subgraphs", "views", "instance2labels", "preprocessed"):
        src = runtime_template_root / "output/datasets/OpenSG_ScanNet" / dirname
        dst = runtime_root / "output/datasets/OpenSG_ScanNet" / dirname
        record = symlink_path(repo_root, src, dst, is_dir=True)
        record["name"] = f"OpenSG_ScanNet/{dirname}"
        records.append(record)
        if record["status"] == "missing_source" or record["status"].startswith("blocked"):
            blockers.append(f"runtime_metadata:OpenSG_ScanNet/{dirname}:{record['status']}")
    return records, blockers


def ensure_runtime_dirs(repo_root: Path, runtime_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in (
        runtime_root / "output/datasets/OpenSG_3RScan",
        runtime_root / "output/datasets/OpenSG_3RScan/views",
        runtime_root / "output/datasets/OpenSG_3RScan/preprocessed",
        runtime_root / "output/datasets/OpenSG_ScanNet",
        runtime_root / "output/features",
        runtime_root / "mlops/opensg/mlflow",
        runtime_root / "mlops/opensg/tensorboards",
    ):
        path.mkdir(parents=True, exist_ok=True)
        records.append({"path": relpath(repo_root, path), "status": "ready_dir"})
    return records


def sequence_summary(scan_dir: Path) -> dict[str, Any]:
    sequence_dir = scan_dir / "sequence"
    color_count = len(list(sequence_dir.glob("*.color.jpg"))) if sequence_dir.is_dir() else 0
    return {
        "sequence_dir_exists": sequence_dir.is_dir(),
        "color_frames": color_count,
        "info_exists": (sequence_dir / "_info.txt").is_file(),
        "frame_000000_color": (sequence_dir / "frame-000000.color.jpg").is_file(),
    }


def make_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG H001 Eval Payload",
        "",
        f"Created at: `{payload['created_at']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Counts",
        "",
        f"- selected scans: `{payload['counts']['selected_scans']}`",
        f"- validation contexts: `{payload['counts']['validation_contexts']}`",
        f"- linked scans: `{payload['counts']['linked_scans']}`",
        f"- sequence-ready scans: `{payload['counts']['sequence_ready_scans']}`",
        "",
        "## Paths",
        "",
        f"- runtime 3RScan root: `{payload['paths']['runtime_r3scan_root']}`",
        f"- raw scans root: `{payload['paths']['raw_scans_root']}`",
        f"- records: `{payload['paths']['records']}`",
    ]
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in payload["blockers"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    runtime_root = resolve(repo_root, args.runtime_root).resolve()
    raw_scans_root = resolve(repo_root, args.raw_scans_root).resolve()
    selected_scans_path = resolve(repo_root, args.selected_scans)
    relationships_path = resolve(repo_root, args.relationships_validation)
    subset_root = resolve(repo_root, args.subset_root)
    source_template_root = resolve(repo_root, args.source_template_root)
    checkpoint_template_root = resolve(repo_root, args.checkpoint_template_root)
    runtime_template_root = resolve(repo_root, args.runtime_template_root)
    out_dir = resolve(repo_root, args.out)

    selected_scans = read_scan_ids(selected_scans_path)
    validation_rows = load_json(relationships_path).get("scans", [])
    validation_scans = {str(row.get("scan")) for row in validation_rows if row.get("scan")}
    target_scans = sorted(selected_scans & validation_scans)
    selected_scan_ids = sorted(selected_scans)
    runtime_r3scan_root = runtime_root / "data/3RScan"

    records: list[dict[str, Any]] = []
    for scan_id in target_scans:
        src = raw_scans_root / scan_id
        dst = runtime_r3scan_root / scan_id
        record = {"scan_id": scan_id, **symlink_record(repo_root, src, dst)}
        record.update(sequence_summary(dst))
        records.append(record)

    status_counts = Counter(record["status"] for record in records)
    linked = sum(1 for record in records if record["status"] in {"created_symlink", "ready_symlink", "normalized_symlink", "ready_existing_path"})
    sequence_ready = sum(1 for record in records if record["sequence_dir_exists"] and record["color_frames"] > 0)

    blockers: list[str] = []
    if len(target_scans) != len(selected_scans):
        blockers.append(f"selected_validation_scan_mismatch:{len(target_scans)}/{len(selected_scans)}")
    if linked != len(target_scans):
        blockers.append(f"linked_scans:{linked}/{len(target_scans)}")
    if sequence_ready != len(target_scans):
        blockers.append(f"sequence_ready_scans:{sequence_ready}/{len(target_scans)}")

    subset_records, subset_blockers = stage_subset_files(
        repo_root=repo_root,
        runtime_root=runtime_root,
        subset_root=subset_root,
        relationships_validation=relationships_path,
        selected_scan_ids=selected_scan_ids,
    )
    blockers.extend(subset_blockers)

    metadata_records, metadata_blockers = stage_runtime_metadata(
        repo_root=repo_root,
        runtime_root=runtime_root,
        runtime_template_root=runtime_template_root,
    )
    blockers.extend(metadata_blockers)
    runtime_dir_records = ensure_runtime_dirs(repo_root, runtime_root)

    source_link = symlink_path(
        repo_root,
        source_template_root,
        runtime_root / "source/open3dsg_source",
        is_dir=True,
    )
    checkpoint_link = symlink_path(
        repo_root,
        checkpoint_template_root,
        runtime_root / "output/checkpoints",
        is_dir=True,
    )
    for name, record in {"source_root": source_link, "checkpoint_root": checkpoint_link}.items():
        if record["status"] == "missing_source" or record["status"].startswith("blocked"):
            blockers.append(f"{name}:{record['status']}")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "ready" if not blockers else "blocked",
        "paths": {
            "runtime_r3scan_root": relpath(repo_root, runtime_r3scan_root),
            "raw_scans_root": relpath(repo_root, raw_scans_root),
            "selected_scans": relpath(repo_root, selected_scans_path),
            "relationships_validation": relpath(repo_root, relationships_path),
            "subset_root": relpath(repo_root, subset_root),
            "source_template_root": relpath(repo_root, source_template_root),
            "checkpoint_template_root": relpath(repo_root, checkpoint_template_root),
            "runtime_template_root": relpath(repo_root, runtime_template_root),
            "runtime_subset_root": relpath(repo_root, runtime_root / "data/3RScan/3DSSG_subset"),
            "runtime_source_root": relpath(repo_root, runtime_root / "source/open3dsg_source"),
            "runtime_checkpoint_root": relpath(repo_root, runtime_root / "output/checkpoints"),
            "runtime_scannet_root": relpath(repo_root, runtime_root / "data/SCANNET"),
            "records": relpath(repo_root, out_dir / "records.jsonl"),
            "subset_records": relpath(repo_root, out_dir / "subset_records.jsonl"),
            "metadata_records": relpath(repo_root, out_dir / "metadata_records.jsonl"),
            "runtime_dir_records": relpath(repo_root, out_dir / "runtime_dir_records.jsonl"),
        },
        "counts": {
            "selected_scans": len(selected_scans),
            "validation_scan_ids": len(validation_scans),
            "validation_contexts": len(validation_rows),
            "target_scans": len(target_scans),
            "linked_scans": linked,
            "sequence_ready_scans": sequence_ready,
        },
        "link_status_counts": dict(status_counts),
        "subset_records_status_counts": dict(Counter(str(record.get("status")) for record in subset_records)),
        "metadata_records_status_counts": dict(Counter(str(record.get("status")) for record in metadata_records)),
        "runtime_dir_status_counts": dict(Counter(str(record.get("status")) for record in runtime_dir_records)),
        "source_link": source_link,
        "checkpoint_link": checkpoint_link,
        "blockers": blockers,
        "next_action": "Run dump_features_h001_eval after status is ready.",
    }

    if args.write:
        write_json(out_dir / "manifest.json", payload)
        write_jsonl(out_dir / "records.jsonl", records)
        write_jsonl(out_dir / "subset_records.jsonl", subset_records)
        write_jsonl(out_dir / "metadata_records.jsonl", metadata_records)
        write_jsonl(out_dir / "runtime_dir_records.jsonl", runtime_dir_records)
        (out_dir / "report.md").write_text(make_report(payload), encoding="utf-8")

    print(json.dumps({"status": payload["status"], "blockers": blockers}, sort_keys=True))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
