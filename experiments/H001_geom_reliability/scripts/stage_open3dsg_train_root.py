#!/usr/bin/env python3
"""Stage the Open3DSG training_repro root for the H001 second-source track."""

from __future__ import annotations

import argparse
import json
import os
import shutil
from datetime import date
from pathlib import Path
from typing import Any


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

SEQUENCE_FILES = (
    "sequence/_info.txt",
    "sequence/frame-000000.color.jpg",
    "sequence/frame-000000.depth.pgm",
    "sequence/frame-000000.pose.txt",
)

R3SCAN_METADATA_FILES = (
    "3RScan.json",
    "3RScan.v2 Semantic Classes - Mapping.csv",
    "attributes.txt",
    "affordances.txt",
    "classes.txt",
    "objects.json",
    "relationships.json",
    "relationships.txt",
    "wordnet_attributes.txt",
)

MODEL_ARTIFACTS = (
    "blip2_positional_embedding.pt",
    "pointnet.pth",
    "pointnet2_ulip.pt",
    "openseg",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--staged-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/training_repro"),
    )
    parser.add_argument(
        "--source-runtime-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/training_repro"),
    )
    return parser.parse_args()


def resolve_under_repo(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    abs_path = path if path.is_absolute() else Path.cwd() / path
    try:
        return str(abs_path.relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def copy_file(repo_root: Path, src: Path, dst: Path) -> dict[str, Any]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return {"src": relpath(repo_root, src), "dst": relpath(repo_root, dst), "bytes": dst.stat().st_size}


def safe_symlink(repo_root: Path, src: Path, dst: Path, target_is_directory: bool) -> dict[str, Any]:
    record: dict[str, Any] = {"src": relpath(repo_root, src), "dst": relpath(repo_root, dst)}
    if not src.exists():
        record["status"] = "missing_source"
        return record
    relative_target = os.path.relpath(src.resolve(), dst.parent.resolve())
    if dst.is_symlink():
        existing_target = os.readlink(dst)
        existing_path = Path(existing_target)
        if existing_path.is_absolute() and str(existing_path).startswith("/workspace/"):
            workspace_relative = existing_path.relative_to("/workspace")
            resolved_existing = (repo_root / workspace_relative).resolve()
        elif existing_path.is_absolute():
            resolved_existing = existing_path.resolve()
        else:
            resolved_existing = (dst.parent / existing_path).resolve()
        if resolved_existing == src.resolve():
            if existing_target != relative_target:
                dst.unlink()
                dst.symlink_to(relative_target, target_is_directory=target_is_directory)
                record["status"] = "normalized_symlink"
            else:
                record["status"] = "ready_symlink"
        else:
            record["status"] = "blocked_existing_symlink_to_other_target"
            record["existing_target"] = existing_target
        return record
    if dst.exists():
        record["status"] = "ready_existing_path"
        return record
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.symlink_to(relative_target, target_is_directory=target_is_directory)
    record["status"] = "created_symlink"
    return record


def relationship_stats(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "subgraphs": len(rows),
        "unique_scans": len({row.get("scan") for row in rows if row.get("scan")}),
        "relations": sum(len(row.get("relationships", [])) for row in rows),
    }


def count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def data_dict_name(split: Any) -> str:
    return f"data_dict_{str(hex(int(split)))[-1]}.pkl"


def expected_preprocessed(rows: list[dict[str, Any]], root: Path) -> dict[str, int]:
    expected: list[Path] = []
    for row in rows:
        scan = row.get("scan")
        split = row.get("split")
        if scan is None or split is None:
            continue
        expected.append(root / scan / data_dict_name(split))
    ready = sum(1 for path in expected if path.exists())
    return {"expected": len(expected), "ready": ready, "missing": len(expected) - ready}


def file_count(scans_root: Path, scan_ids: set[str], filename: str) -> int:
    return sum(1 for scan_id in scan_ids if (scans_root / scan_id / filename).exists())


def sequence_count(scans_root: Path, scan_ids: set[str], filename: str) -> int:
    return sum(1 for scan_id in scan_ids if (scans_root / scan_id / filename).exists())


def scan_payload_summary(scans_root: Path, scan_ids: set[str]) -> dict[str, Any]:
    existing = {scan_id for scan_id in scan_ids if (scans_root / scan_id).is_dir()}
    return {
        "expected_scans": len(scan_ids),
        "existing_scan_dirs": len(existing),
        "missing_scan_dirs": len(scan_ids - existing),
        "raw_files": {name: file_count(scans_root, scan_ids, name) for name in RAW_SCAN_FILES},
        "open3dsg_files": {name: file_count(scans_root, scan_ids, name) for name in OPEN3DSG_SCAN_FILES},
        "sequence_files": {name: sequence_count(scans_root, scan_ids, name) for name in SEQUENCE_FILES},
    }


def status_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in records:
        status = str(record.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    return counts


def scan_record(scans_root: Path, scan_id: str, roles: list[str], link_status: str) -> dict[str, Any]:
    scan_dir = scans_root / scan_id
    return {
        "scan": scan_id,
        "roles": sorted(roles),
        "link_status": link_status,
        "source_exists": scan_dir.is_dir(),
        "raw_ready": {name: (scan_dir / name).exists() for name in RAW_SCAN_FILES},
        "open3dsg_ready": {name: (scan_dir / name).exists() for name in OPEN3DSG_SCAN_FILES},
        "sequence_ready": {name: (scan_dir / name).exists() for name in SEQUENCE_FILES},
    }


def build_stage(repo_root: Path, staged_root: Path, source_runtime_root: Path, out_dir: Path) -> dict[str, Any]:
    local_dataset = repo_root / "local_dataset"
    subset_root = local_dataset / "3DSSG_subset"
    raw_scans_root = local_dataset / "3RScan" / "scans"
    h001_scans_file = (
        repo_root
        / "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/subset/h001_validation_hardened/scans.txt"
    )

    train_rows = load_json(subset_root / "relationships_train.json")["scans"]
    official_validation_rows = load_json(subset_root / "relationships_validation.json")["scans"]
    h001_scans = {
        line.strip()
        for line in h001_scans_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    train_scan_ids = {row["scan"] for row in train_rows}
    train_dev_rows = [row for row in official_validation_rows if row.get("scan") not in h001_scans]
    train_dev_scan_ids = {row["scan"] for row in train_dev_rows}
    target_scan_ids = train_scan_ids | train_dev_scan_ids

    data_root = staged_root / "data"
    staged_r3scan = data_root / "3RScan"
    staged_subset = staged_r3scan / "3DSSG_subset"
    output_root = staged_root / "output"
    preprocessed_root = output_root / "datasets/OpenSG_3RScan/preprocessed"
    views_root = output_root / "datasets/OpenSG_3RScan/views"

    dirs = [
        staged_root,
        data_root,
        staged_r3scan,
        staged_subset,
        data_root / "SCANNET/scannet_3d/data",
        data_root / "SCANNET/scannet_2d",
        output_root / "datasets/OpenSG_3RScan/views",
        output_root / "datasets/OpenSG_3RScan/preprocessed",
        output_root / "datasets/OpenSG_ScanNet/subgraphs",
        output_root / "datasets/OpenSG_ScanNet/views",
        output_root / "datasets/OpenSG_ScanNet/preprocessed",
        output_root / "datasets/OpenSG_ScanNet/instance2labels",
        output_root / "checkpoints",
        output_root / "features",
        staged_root / "mlops/opensg/mlflow",
        staged_root / "mlops/opensg/tensorboards",
        staged_root / "source",
    ]
    for directory in dirs:
        directory.mkdir(parents=True, exist_ok=True)

    copied_files: list[dict[str, Any]] = []
    for filename in ("classes.txt", "relationships.txt"):
        src = subset_root / filename
        copied_files.append(copy_file(repo_root, src, staged_r3scan / filename))
        copied_files.append(copy_file(repo_root, src, staged_subset / filename))

    r3scan_files = local_dataset / "3RScan" / "files"
    for filename in R3SCAN_METADATA_FILES:
        src = r3scan_files / filename
        if src.exists():
            copied_files.append(copy_file(repo_root, src, staged_r3scan / filename))

    relationships_text = (subset_root / "relationships.txt").read_text(encoding="utf-8")
    if not relationships_text.endswith("\n"):
        relationships_text += "\n"
    write_text(staged_r3scan / "relationships_custom.txt", relationships_text)

    empty_payload = {"scans": []}
    write_json(staged_subset / "relationships_train.json", {"scans": train_rows})
    write_json(staged_subset / "relationships_validation.json", {"scans": train_dev_rows})
    write_json(staged_subset / "relationships_test.json", empty_payload)
    write_json(staged_subset / "relationships.json", {"scans": train_rows + train_dev_rows})
    write_text(staged_subset / "train_scans.txt", "\n".join(sorted(train_scan_ids)) + "\n")
    write_text(staged_subset / "validation_scans.txt", "\n".join(sorted(train_dev_scan_ids)) + "\n")
    write_text(staged_subset / "test_scans.txt", "")

    write_json(staged_r3scan / "obj_boxes_train_refined.json", {})
    write_json(staged_r3scan / "obj_boxes_val_refined.json", {})
    scannet_subgraphs = output_root / "datasets/OpenSG_ScanNet/subgraphs"
    write_json(scannet_subgraphs / "relationships_train.json", empty_payload)
    write_json(scannet_subgraphs / "relationships_validation.json", empty_payload)
    write_text(scannet_subgraphs / "train_scans.txt", "")
    write_text(scannet_subgraphs / "validation_scans.txt", "")

    source_link = safe_symlink(
        repo_root,
        source_runtime_root / "source/open3dsg_source",
        staged_root / "source/open3dsg_source",
        target_is_directory=True,
    )
    source_package_link = safe_symlink(
        repo_root,
        source_runtime_root / "source/open3dsg_source/open3dsg",
        staged_root / "open3dsg",
        target_is_directory=True,
    )

    model_links = []
    for name in MODEL_ARTIFACTS:
        src = source_runtime_root / "output/checkpoints" / name
        model_links.append(safe_symlink(repo_root, src, output_root / "checkpoints" / name, src.is_dir()))

    scan_links = []
    link_status_by_scan: dict[str, str] = {}
    for scan_id in sorted(target_scan_ids):
        record = safe_symlink(repo_root, raw_scans_root / scan_id, staged_r3scan / scan_id, target_is_directory=True)
        scan_links.append({"scan": scan_id, **record})
        link_status_by_scan[scan_id] = str(record.get("status", "unknown"))

    roles_by_scan: dict[str, list[str]] = {}
    for scan_id in train_scan_ids:
        roles_by_scan.setdefault(scan_id, []).append("train")
    for scan_id in train_dev_scan_ids:
        roles_by_scan.setdefault(scan_id, []).append("train_dev_no_h001")
    scan_records = [
        scan_record(raw_scans_root, scan_id, roles_by_scan.get(scan_id, []), link_status_by_scan.get(scan_id, "unknown"))
        for scan_id in sorted(target_scan_ids)
    ]

    train_payload = scan_payload_summary(raw_scans_root, train_scan_ids)
    train_dev_payload = scan_payload_summary(raw_scans_root, train_dev_scan_ids)
    target_payload = scan_payload_summary(raw_scans_root, target_scan_ids)
    train_preprocessed = expected_preprocessed(train_rows, preprocessed_root)
    train_dev_preprocessed = expected_preprocessed(train_dev_rows, preprocessed_root)
    train_views_ready = sum(1 for scan_id in train_scan_ids if (views_root / f"{scan_id}_object2image.pkl").exists())
    train_dev_views_ready = sum(1 for scan_id in train_dev_scan_ids if (views_root / f"{scan_id}_object2image.pkl").exists())

    leakage = {
        "train_h001_overlap": sorted(train_scan_ids & h001_scans),
        "train_dev_h001_overlap": sorted(train_dev_scan_ids & h001_scans),
        "official_validation_h001_overlap_count": len({row["scan"] for row in official_validation_rows} & h001_scans),
        "policy": "relationships_validation.json excludes H001 held-out scans; relationships_test.json is empty in training_repro.",
    }

    blockers: list[str] = []
    if leakage["train_h001_overlap"] or leakage["train_dev_h001_overlap"]:
        blockers.append("h001_heldout_leakage")
    if train_payload["existing_scan_dirs"] < train_payload["expected_scans"]:
        blockers.append(
            f"missing_train_scan_dirs:{train_payload['existing_scan_dirs']}/{train_payload['expected_scans']}"
        )
    for filename, count in train_payload["open3dsg_files"].items():
        if count < train_payload["expected_scans"]:
            blockers.append(f"missing_train_open3dsg_file:{filename}:{count}/{train_payload['expected_scans']}")
    for filename, count in train_payload["sequence_files"].items():
        if count < train_payload["expected_scans"]:
            blockers.append(f"missing_train_sequence_file:{filename}:{count}/{train_payload['expected_scans']}")

    if train_payload["existing_scan_dirs"] == train_payload["expected_scans"] and not blockers:
        status = "training_repro_staged_root_ready_for_view_preprocess"
        next_gate = "Open3DSG Docker env image build/import check"
    elif blockers == ["h001_heldout_leakage"]:
        status = "training_repro_blocked_by_leakage"
        next_gate = "Fix split leakage before any training"
    else:
        status = "training_repro_metadata_ready_payload_incomplete"
        next_gate = "Acquire or stage missing 3RScan full-train payload before view/preprocess generation"

    manifest = {
        "schema_version": "h001_open3dsg_training_repro_stage_v1",
        "date_checked": date.today().isoformat(),
        "status": status,
        "staged_root": relpath(repo_root, staged_root),
        "source_runtime_root": relpath(repo_root, source_runtime_root),
        "official_train": relationship_stats(train_rows),
        "train_dev_without_h001": relationship_stats(train_dev_rows),
        "h001_eval_heldout_scans": len(h001_scans),
        "target_payload": target_payload,
        "train_payload": train_payload,
        "train_dev_payload": train_dev_payload,
        "train_views": {"ready": train_views_ready, "expected": len(train_scan_ids)},
        "train_dev_views": {"ready": train_dev_views_ready, "expected": len(train_dev_scan_ids)},
        "train_preprocessed": train_preprocessed,
        "train_dev_preprocessed": train_dev_preprocessed,
        "leakage": leakage,
        "class_label_count": count_lines(subset_root / "classes.txt"),
        "relationship_label_count": count_lines(subset_root / "relationships.txt"),
        "created_directories": [relpath(repo_root, directory) for directory in dirs],
        "copied_files": copied_files,
        "source_link": source_link,
        "source_package_link": source_package_link,
        "model_artifact_links": model_links,
        "scan_link_status_counts": status_counts(scan_links),
        "scan_records": relpath(repo_root, out_dir / "records.jsonl"),
        "missing_train_scans_file": relpath(repo_root, out_dir / "missing_train_scans.txt"),
        "missing_train_dev_scans_file": relpath(repo_root, out_dir / "missing_train_dev_scans.txt"),
        "blockers": blockers,
        "next_gate": next_gate,
        "claim_limit": "No Open3DSG checkpoint, raw dump, prediction JSONL, geometry join, or metric exists after training_repro staging.",
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "manifest.json", manifest)
    write_jsonl(out_dir / "records.jsonl", scan_records)
    write_text(out_dir / "missing_train_scans.txt", "\n".join(sorted(train_scan_ids - {p.name for p in raw_scans_root.iterdir() if p.is_dir()})) + "\n")
    write_text(out_dir / "missing_train_dev_scans.txt", "\n".join(sorted(train_dev_scan_ids - {p.name for p in raw_scans_root.iterdir() if p.is_dir()})) + "\n")
    write_report(out_dir / "report.md", manifest)

    status_path = out_dir.parent / "status.json"
    previous_status: dict[str, Any] = {}
    if status_path.exists():
        previous_status = load_json(status_path)
    previous_status.update(
        {
            "schema_version": "h001_open3dsg_source_status_v4",
            "status": status,
            "training_repro": "training_repro/manifest.json",
            "next_gate": next_gate,
        }
    )
    write_json(status_path, previous_status)
    return manifest


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Open3DSG Training Repro Staged Root",
        "",
        f"Date: `{manifest['date_checked']}`",
        f"Status: `{manifest['status']}`",
        f"Staged root: `{manifest['staged_root']}`",
        "",
        "## Split",
        "",
        f"- Official train: {manifest['official_train']['unique_scans']} scans, {manifest['official_train']['subgraphs']} subgraphs, {manifest['official_train']['relations']} relations.",
        f"- Train-dev without H001 held-out: {manifest['train_dev_without_h001']['unique_scans']} scans, {manifest['train_dev_without_h001']['subgraphs']} subgraphs, {manifest['train_dev_without_h001']['relations']} relations.",
        f"- H001 held-out scan overlap in train: {len(manifest['leakage']['train_h001_overlap'])}.",
        f"- H001 held-out scan overlap in train-dev: {len(manifest['leakage']['train_dev_h001_overlap'])}.",
        "",
        "## Payload Readiness",
        "",
        f"- Train scan dirs ready: {manifest['train_payload']['existing_scan_dirs']} / {manifest['train_payload']['expected_scans']}.",
        f"- Train-dev scan dirs ready: {manifest['train_dev_payload']['existing_scan_dirs']} / {manifest['train_dev_payload']['expected_scans']}.",
        f"- Train views ready: {manifest['train_views']['ready']} / {manifest['train_views']['expected']}.",
        f"- Train preprocessed ready: {manifest['train_preprocessed']['ready']} / {manifest['train_preprocessed']['expected']}.",
        "",
        "## Train Open3DSG Files",
        "",
        "| File | Ready |",
        "| --- | ---: |",
    ]
    for name, count in manifest["train_payload"]["open3dsg_files"].items():
        lines.append(f"| `{name}` | {count}/{manifest['train_payload']['expected_scans']} |")
    lines.extend(["", "## Train Sequence Files", "", "| File | Ready |", "| --- | ---: |"])
    for name, count in manifest["train_payload"]["sequence_files"].items():
        lines.append(f"| `{name}` | {count}/{manifest['train_payload']['expected_scans']} |")
    lines.extend(["", "## Blockers", ""])
    if manifest["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Next Gate", "", manifest["next_gate"], "", "## Claim Limit", "", manifest["claim_limit"], ""])
    write_text(path, "\n".join(lines))


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    staged_root = resolve_under_repo(repo_root, args.staged_root).resolve()
    source_runtime_root = resolve_under_repo(repo_root, args.source_runtime_root).resolve()
    out_dir = resolve_under_repo(repo_root, args.out).resolve()
    manifest = build_stage(repo_root, staged_root, source_runtime_root, out_dir)
    print(json.dumps({"status": manifest["status"], "out": str(out_dir)}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
