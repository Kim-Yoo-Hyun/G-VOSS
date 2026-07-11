#!/usr/bin/env python3
"""Stage the frozen SGFN full_l160 source, data links, and checkpoint."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_COMMIT = "4b783ecdc6caba1515b361f8a0643d0c2d568f52"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--stage-root", type=Path, required=True)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def link(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink():
        if target.resolve() == source.resolve():
            return
        target.unlink()
    elif target.exists():
        raise FileExistsError(f"refusing_to_replace:{target}")
    target.symlink_to(source.resolve(), target_is_directory=source.is_dir())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    stage = args.stage_root if args.stage_root.is_absolute() else root / args.stage_root
    manifest_path = stage / "runtime_manifest.json"
    source = root / "local_dataset/SceneGraphFusion_code/3DSSG"
    if manifest_path.exists():
        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing.get("status") == "sgfn_runtime_staged":
            link(source / "configs", stage / "runtime/configs")
            existing.setdefault("runtime_links", {})["source_configs"] = relpath(
                root, stage / "runtime/configs"
            )
            current_config = root / "configs/h001/sgfn_full_l160_confirmatory.yaml"
            existing["config"] = {
                "path": relpath(root, current_config),
                "sha256": sha256_file(current_config),
            }
            write_json(manifest_path, existing)
            print(json.dumps({"status": "sgfn_runtime_staged_existing", "stage": relpath(root, stage)}))
            return 0
        raise FileExistsError(f"nonready_existing_manifest:{manifest_path}")

    scan_root = root / "local_dataset/3RScan/scans"
    subset_root = root / "local_dataset/3DSSG_subset"
    metadata_root = root / "local_dataset/3RScan/files"
    checkpoint_archive = root / "local_dataset/SceneGraphFusion_checkpoints/SGFN_full_l160.zip"
    target_manifest = root / "experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v3/manifest.json"
    checkpoint_audit = root / "experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v3/checkpoint_audit.json"
    config = root / "configs/h001/sgfn_full_l160_confirmatory.yaml"
    required = [source, scan_root, subset_root, metadata_root, checkpoint_archive, target_manifest, checkpoint_audit, config]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_inputs:{missing}")

    commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    target = json.loads(target_manifest.read_text(encoding="utf-8"))
    audit = json.loads(checkpoint_audit.read_text(encoding="utf-8"))
    test_file = source / "files/cvpr/test_scans.txt"
    scans = read_lines(test_file)
    validations = {
        "source_commit_matches": commit == EXPECTED_COMMIT,
        "target_v3_ready": target.get("status") == "target_v3_frozen_pre_correct_checkpoint_pre_inference",
        "checkpoint_audit_passed": audit.get("status") == "checkpoint_compatible_full_l160",
        "checkpoint_sha_matches_audit": sha256_file(checkpoint_archive) == audit.get("archive", {}).get("sha256"),
        "test_scan_count_157": len(scans) == 157 and len(set(scans)) == 157,
        "all_test_scan_directories_present": all((scan_root / scan).is_dir() for scan in scans),
        "all_test_aligned_ply_present": all((scan_root / scan / "labels.instances.align.annotated.v2.ply").is_file() for scan in scans),
        "all_test_semseg_present": all((scan_root / scan / "semseg.v2.json").is_file() for scan in scans),
    }
    if not all(validations.values()):
        raise ValueError(f"runtime_stage_validation_failed:{validations}")

    runtime = stage / "runtime"
    raw = runtime / "raw_test"
    files = runtime / "files"
    for scan in scans:
        link(scan_root / scan, raw / scan)
    link(metadata_root / "relationships.json", raw / "relationships.json")
    link(source / "files/3RScan.v2 Semantic Classes - Mapping.csv", files / "3RScan.v2 Semantic Classes - Mapping.csv")
    link(subset_root / "classes.txt", files / "classes160.txt")
    link(subset_root / "relationships.txt", files / "relationships.txt")
    for split in ("train", "validation", "test"):
        link(source / f"files/cvpr/{split}_scans.txt", files / "cvpr" / f"{split}_scans.txt")
    link(source / "configs", runtime / "configs")

    checkpoint_dir = stage / "checkpoint"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_out = checkpoint_dir / "model_best.pt"
    with zipfile.ZipFile(checkpoint_archive) as bundle:
        member = "SGFN_full_l160/model_best.pt"
        if member not in bundle.namelist():
            raise FileNotFoundError(f"missing_checkpoint_member:{member}")
        with bundle.open(member) as source_handle, checkpoint_out.open("wb") as target_handle:
            shutil.copyfileobj(source_handle, target_handle)

    manifest = {
        "schema_version": "h001_sgfn_runtime_stage_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "sgfn_runtime_staged",
        "source": {"path": relpath(root, source), "commit": commit},
        "stage_root": relpath(root, stage),
        "scan_count": len(scans),
        "checkpoint": {
            "archive": relpath(root, checkpoint_archive),
            "archive_sha256": sha256_file(checkpoint_archive),
            "extracted": relpath(root, checkpoint_out),
            "extracted_sha256": sha256_file(checkpoint_out),
        },
        "config": {"path": relpath(root, config), "sha256": sha256_file(config)},
        "validations": validations,
        "runtime_links": {
            "raw_scan_links": len(scans),
            "relationships_json": relpath(root, raw / "relationships.json"),
            "files_root": relpath(root, files),
            "source_configs": relpath(root, runtime / "configs"),
        },
        "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_runtime_stage",
    }
    write_json(manifest_path, manifest)
    print(json.dumps({"status": manifest["status"], "scan_count": len(scans), "stage": relpath(root, stage)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
