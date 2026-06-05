#!/usr/bin/env python3
"""Prepare an isolated VL-SAT runtime layout for selected H001 scans."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]

DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_ARTIFACT_DIR = H001_ROOT / "artifacts" / "layout" / "vlsat"
DEFAULT_GENERATED_SUBSET_ROOT = DEFAULT_ARTIFACT_DIR / "generated" / "3DSSG_subset"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_mini" / "scans.txt"
DEFAULT_STAGED_ROOT = DEFAULT_DATASET_ROOT / "VLSAT_staged" / "CVPR2023-VLSAT"

SUBSET_OFFICIAL_FILES = (
    "classes.txt",
    "relationships.txt",
    "relationships.json",
    "relationships_train.json",
    "relationships_validation.json",
)
SUBSET_GENERATED_FILES = (
    "relations.txt",
    "train_scans.txt",
    "validation_scans.txt",
)
SCAN_PAYLOAD_FILES = (
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
)
RAW_PLY = "labels.instances.annotated.v2.ply"
ALIGNED_PLY = "labels.instances.align.annotated.v2.ply"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage selected H001 files into a faithful VL-SAT runtime root."
    )
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--generated-subset-root", type=Path, default=DEFAULT_GENERATED_SUBSET_ROOT)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
    parser.add_argument(
        "--link-mode",
        choices=("symlink", "copy"),
        default="symlink",
        help="How to stage large scan payload files when they exist.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace existing staged files, symlinks, or staged directories.",
    )
    parser.add_argument(
        "--no-reference-aligned-copy",
        action="store_true",
        help="Do not create aligned PLY by copying raw PLY for reference scans.",
    )
    parser.add_argument(
        "--reference-aligned-mode",
        choices=("copy", "symlink"),
        default="copy",
        help="Storage mode for identity aligned PLY files on reference scans.",
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def remove_target(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def file_record(
    source: Path,
    target: Path,
    *,
    action: str,
    status: str,
    required: bool,
) -> dict[str, Any]:
    return {
        "source": rel(source),
        "target": rel(target),
        "action": action,
        "status": status,
        "required": required,
        "source_exists": source.exists(),
        "target_exists": target.exists(),
        "source_sha256": sha256(source),
        "target_sha256": sha256(target) if target.exists() and target.is_file() else None,
    }


def stage_file(
    source: Path,
    target: Path,
    *,
    mode: str,
    overwrite: bool,
    required: bool = True,
) -> dict[str, Any]:
    if not source.exists():
        return file_record(source, target, action=mode, status="missing_source", required=required)

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        if not overwrite:
            return file_record(source, target, action=mode, status="already_present", required=required)
        remove_target(target)

    if mode == "copy":
        shutil.copy2(source, target)
    elif mode == "symlink":
        os.symlink(source.resolve(), target)
    else:
        raise ValueError(f"unsupported stage mode: {mode}")

    return file_record(source, target, action=mode, status="staged", required=required)


def stage_dir(
    source: Path,
    target: Path,
    *,
    mode: str,
    overwrite: bool,
    required: bool,
) -> dict[str, Any]:
    if not source.exists():
        target_exists = target.exists() or target.is_symlink()
        return {
            "source": rel(source),
            "target": rel(target),
            "action": mode,
            "status": "target_already_present_missing_source" if target_exists else "missing_source",
            "required": required,
            "source_exists": False,
            "target_exists": target_exists,
            "file_count": count_files(target) if target_exists else 0,
        }

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() or target.is_symlink():
        if not overwrite:
            return {
                "source": rel(source),
                "target": rel(target),
                "action": mode,
                "status": "already_present",
                "required": required,
                "source_exists": True,
                "target_exists": True,
                "file_count": count_files(target),
            }
        remove_target(target)

    if mode == "copy":
        shutil.copytree(source, target)
    elif mode == "symlink":
        os.symlink(source.resolve(), target)
    else:
        raise ValueError(f"unsupported stage mode: {mode}")

    return {
        "source": rel(source),
        "target": rel(target),
        "action": mode,
        "status": "staged",
        "required": required,
        "source_exists": True,
        "target_exists": target.exists(),
        "file_count": count_files(target),
    }


def count_files(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return 1
    if path.is_symlink() and path.resolve().is_dir():
        return sum(1 for p in path.resolve().rglob("*") if p.is_file())
    if path.is_dir():
        return sum(1 for p in path.rglob("*") if p.is_file())
    return 0


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def scan_ids_from_subset_json(path: Path) -> list[str]:
    data = load_json(path)
    return sorted(
        {
            str(entry.get("scan"))
            for entry in data.get("scans", [])
            if entry.get("scan") is not None
        }
    )


def load_scan_metadata(path: Path) -> dict[str, Any]:
    data = load_json(path)
    references: list[str] = []
    rescans: list[str] = []
    group_reference_by_scan: dict[str, str] = {}
    is_reference_scan: dict[str, bool] = {}
    has_transform: dict[str, bool] = {}

    for scene in data:
        reference = str(scene.get("reference", "")).strip()
        if reference:
            references.append(reference)
            group_reference_by_scan[reference] = reference
            is_reference_scan[reference] = True
            has_transform[reference] = False

        for scan in scene.get("scans", []):
            scan_id = str(scan.get("reference", "")).strip()
            if not scan_id:
                continue
            group_reference_by_scan[scan_id] = reference
            is_reference_scan[scan_id] = False
            has_transform[scan_id] = "transform" in scan
            if scan_id != reference:
                rescans.append(scan_id)

    references = unique_preserve_order(references)
    rescans = unique_preserve_order(rescans)
    return {
        "scene_count": len(data),
        "references": references,
        "rescans": rescans,
        "group_reference_by_scan": group_reference_by_scan,
        "is_reference_scan": is_reference_scan,
        "has_transform": has_transform,
    }


def generated_source_for(name: str, dataset_root: Path, generated_subset_root: Path) -> Path:
    generated = generated_subset_root / name
    if generated.exists():
        return generated
    subset_root = dataset_root / "3DSSG_subset"
    if name == "relations.txt":
        return subset_root / "relationships.txt"
    if name == "train_scans.txt":
        return subset_root / "relationships_train.json"
    if name == "validation_scans.txt":
        return subset_root / "relationships_validation.json"
    raise ValueError(name)


def stage_generated_subset_file(
    name: str,
    source: Path,
    target: Path,
    *,
    overwrite: bool,
) -> dict[str, Any]:
    if source.suffix == ".json":
        if not source.exists():
            return file_record(source, target, action="generate", status="missing_source", required=True)
        scan_ids = scan_ids_from_subset_json(source)
        if target.exists() or target.is_symlink():
            if not overwrite:
                return file_record(source, target, action="generate", status="already_present", required=True)
            remove_target(target)
        write_lines(target, scan_ids)
        return file_record(source, target, action="generate", status="staged", required=True) | {
            "generated_count": len(scan_ids)
        }
    return stage_file(source, target, mode="copy", overwrite=overwrite, required=True)


def stage_aligned_for_reference(
    raw_source: Path,
    aligned_target: Path,
    *,
    overwrite: bool,
    mode: str,
) -> dict[str, Any]:
    if not raw_source.exists():
        return file_record(
            raw_source,
            aligned_target,
            action="official_reference_copy",
            status="missing_source",
            required=True,
        )

    if mode == "symlink":
        return stage_file(raw_source, aligned_target, mode="symlink", overwrite=overwrite, required=True) | {
            "action": "official_reference_identity_symlink"
        }
    if mode != "copy":
        raise ValueError(f"unsupported reference aligned mode: {mode}")

    aligned_target.parent.mkdir(parents=True, exist_ok=True)
    if aligned_target.exists() or aligned_target.is_symlink():
        if not overwrite:
            return file_record(
                raw_source,
                aligned_target,
                action="official_reference_copy",
                status="already_present",
                required=True,
            )
        remove_target(aligned_target)

    shutil.copy2(raw_source, aligned_target)
    return file_record(
        raw_source,
        aligned_target,
        action="official_reference_copy",
        status="staged",
        required=True,
    )


def stage_subset(args: argparse.Namespace, staged_subset_root: Path) -> dict[str, Any]:
    dataset_root = args.dataset_root.resolve()
    subset_root = dataset_root / "3DSSG_subset"
    generated_subset_root = args.generated_subset_root.resolve()
    records: dict[str, Any] = {}

    for name in SUBSET_OFFICIAL_FILES:
        records[name] = stage_file(
            subset_root / name,
            staged_subset_root / name,
            mode="copy",
            overwrite=args.overwrite,
            required=True,
        )

    for name in SUBSET_GENERATED_FILES:
        source = generated_source_for(name, dataset_root, generated_subset_root)
        records[name] = stage_generated_subset_file(
            name,
            source,
            staged_subset_root / name,
            overwrite=args.overwrite,
        )

    return records


def stage_files_root(args: argparse.Namespace, staged_files_root: Path) -> dict[str, Any]:
    dataset_root = args.dataset_root.resolve()
    source_files_root = dataset_root / "3RScan" / "files"
    metadata_source = source_files_root / "3RScan.json"
    metadata = load_scan_metadata(metadata_source)
    records: dict[str, Any] = {
        "3RScan.json": stage_file(
            metadata_source,
            staged_files_root / "3RScan.json",
            mode="copy",
            overwrite=args.overwrite,
            required=True,
        )
    }

    for name in ("3RScan.v2 Semantic Classes - Mapping.csv", "classes160.txt"):
        records[name] = stage_file(
            source_files_root / name,
            staged_files_root / name,
            mode="copy",
            overwrite=args.overwrite,
            required=False,
        )

    references_path = staged_files_root / "references.txt"
    rescans_path = staged_files_root / "rescans.txt"
    if references_path.exists() and not args.overwrite:
        references_status = "already_present"
    else:
        if references_path.exists() or references_path.is_symlink():
            remove_target(references_path)
        write_lines(references_path, metadata["references"])
        references_status = "staged"

    if rescans_path.exists() and not args.overwrite:
        rescans_status = "already_present"
    else:
        if rescans_path.exists() or rescans_path.is_symlink():
            remove_target(rescans_path)
        write_lines(rescans_path, metadata["rescans"])
        rescans_status = "staged"

    records["references.txt"] = file_record(
        metadata_source,
        references_path,
        action="generate_reference_scan_ids",
        status=references_status,
        required=True,
    ) | {"generated_count": len(metadata["references"])}
    records["rescans.txt"] = file_record(
        metadata_source,
        rescans_path,
        action="generate_rescan_ids",
        status=rescans_status,
        required=True,
    ) | {"generated_count": len(metadata["rescans"])}
    records["metadata_summary"] = {
        "scene_count": metadata["scene_count"],
        "reference_count": len(metadata["references"]),
        "rescan_count": len(metadata["rescans"]),
        "source_sha256": sha256(metadata_source),
    }
    records["_metadata"] = metadata
    return records


def stage_selected_scan(
    scan_id: str,
    args: argparse.Namespace,
    staged_scan_root: Path,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    dataset_root = args.dataset_root.resolve()
    source_dir = dataset_root / "3RScan" / "scans" / scan_id
    target_dir = staged_scan_root / scan_id
    target_dir.mkdir(parents=True, exist_ok=True)

    file_records = {
        name: stage_file(
            source_dir / name,
            target_dir / name,
            mode=args.link_mode,
            overwrite=args.overwrite,
            required=True,
        )
        for name in SCAN_PAYLOAD_FILES
    }
    sequence_dir = stage_dir(
        source_dir / "sequence",
        target_dir / "sequence",
        mode=args.link_mode,
        overwrite=args.overwrite,
        required=False,
    )
    sequence_zip = stage_file(
        source_dir / "sequence.zip",
        target_dir / "sequence.zip",
        mode=args.link_mode,
        overwrite=args.overwrite,
        required=True,
    )
    multi_view = stage_dir(
        source_dir / "multi_view",
        target_dir / "multi_view",
        mode=args.link_mode,
        overwrite=args.overwrite,
        required=True,
    )

    source_aligned = source_dir / ALIGNED_PLY
    target_aligned = target_dir / ALIGNED_PLY
    is_reference = bool(metadata["is_reference_scan"].get(scan_id, False))
    has_transform = bool(metadata["has_transform"].get(scan_id, False))
    if source_aligned.exists():
        aligned = stage_file(
            source_aligned,
            target_aligned,
            mode=args.link_mode,
            overwrite=args.overwrite,
            required=True,
        )
    elif is_reference and not args.no_reference_aligned_copy:
        aligned = stage_aligned_for_reference(
            source_dir / RAW_PLY,
            target_aligned,
            overwrite=args.overwrite,
            mode=args.reference_aligned_mode,
        )
    elif has_transform:
        aligned = file_record(
            source_dir / RAW_PLY,
            target_aligned,
            action="pending_official_transform_ply",
            status="pending",
            required=True,
        )
    else:
        aligned = file_record(
            source_dir / RAW_PLY,
            target_aligned,
            action="pending_scan_payload_or_transform",
            status="missing_source",
            required=True,
        )

    required_payload_ready = all(record["target_exists"] for record in file_records.values())
    sequence_ready = sequence_dir["target_exists"]
    multi_view_ready = multi_view["target_exists"] and multi_view["file_count"] > 0
    sequence_zip_ready = sequence_zip["target_exists"]
    return {
        "scan_id": scan_id,
        "source_dir": rel(source_dir),
        "target_dir": rel(target_dir),
        "in_3rscan_metadata": scan_id in metadata["group_reference_by_scan"],
        "group_reference": metadata["group_reference_by_scan"].get(scan_id),
        "is_reference_scan": is_reference,
        "has_rescan_transform": has_transform,
        "files": file_records,
        "sequence": sequence_dir,
        "sequence_zip": sequence_zip,
        "aligned_ply": aligned,
        "multi_view": multi_view,
        "required_payload_ready": required_payload_ready,
        "sequence_zip_ready": sequence_zip_ready,
        "sequence_ready": sequence_ready,
        "aligned_ply_ready": aligned["target_exists"],
        "multi_view_ready": multi_view_ready,
        "ready_for_faithful_vlsat": required_payload_ready and aligned["target_exists"] and multi_view_ready,
    }


def build_report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    blockers = manifest["blockers"]
    lines = [
        "# VL-SAT Stage Prep",
        "",
        f"Generated: {manifest['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- status: `{manifest['status']}`",
        f"- staged root: `{manifest['staged_root']}`",
        f"- source dataset mutated: `{str(manifest['source_dataset_mutated']).lower()}`",
        "",
        "## Counts",
        "",
        f"- selected scans: `{counts['selected_scans']}`",
        f"- scan dirs staged: `{counts['scan_dirs_staged']}`",
        f"- required payload ready scans: `{counts['required_payload_ready_scans']}`",
        f"- sequence.zip ready scans: `{counts['sequence_zip_ready_scans']}`",
        f"- aligned PLY ready scans: `{counts['aligned_ply_ready_scans']}`",
        f"- multi_view ready scans: `{counts['multi_view_ready_scans']}`",
        f"- faithful VL-SAT ready scans: `{counts['faithful_vlsat_ready_scans']}`",
        f"- references.txt scan ids: `{counts['references']}`",
        f"- rescans.txt scan ids: `{counts['rescans']}`",
        "",
        "## Blockers",
        "",
    ]
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- none")

    lines.extend(["", "## Selected Scan Status", ""])
    for scan in manifest["selected_scan_records"]:
        lines.append(
            "- `{scan_id}`: payload=`{payload}`, sequence_zip=`{sequence_zip}`, aligned=`{aligned}`, multi_view=`{multi}`".format(
                scan_id=scan["scan_id"],
                payload=str(scan["required_payload_ready"]).lower(),
                sequence_zip=str(scan["sequence_zip_ready"]).lower(),
                aligned=str(scan["aligned_ply_ready"]).lower(),
                multi=str(scan["multi_view_ready"]).lower(),
            )
        )

    lines.extend(
        [
            "",
            "## Next",
            "",
            "1. Resolve any blockers listed above.",
            "2. If status is `ready`, re-run the layout checker against the staged runtime root.",
            "3. Then proceed to prediction export or evaluation readiness gates.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    dataset_root = args.dataset_root.resolve()
    artifact_dir = args.artifact_dir.resolve()
    staged_root = args.staged_root.resolve()
    staged_subset_root = staged_root / "data" / "3DSSG_subset"
    staged_scan_root = staged_root / "data" / "3RScan"
    staged_files_root = staged_root / "files"
    selected_scans = read_lines(args.selected_scans.resolve())

    subset_records = stage_subset(args, staged_subset_root)
    file_root_records = stage_files_root(args, staged_files_root)
    metadata = file_root_records.pop("_metadata")
    selected_scan_records = [
        stage_selected_scan(scan_id, args, staged_scan_root, metadata)
        for scan_id in selected_scans
    ]

    counts = {
        "selected_scans": len(selected_scans),
        "scan_dirs_staged": sum(1 for scan in selected_scan_records if (staged_scan_root / scan["scan_id"]).is_dir()),
        "required_payload_ready_scans": sum(1 for scan in selected_scan_records if scan["required_payload_ready"]),
        "sequence_zip_ready_scans": sum(1 for scan in selected_scan_records if scan["sequence_zip_ready"]),
        "aligned_ply_ready_scans": sum(1 for scan in selected_scan_records if scan["aligned_ply_ready"]),
        "multi_view_ready_scans": sum(1 for scan in selected_scan_records if scan["multi_view_ready"]),
        "faithful_vlsat_ready_scans": sum(1 for scan in selected_scan_records if scan["ready_for_faithful_vlsat"]),
        "references": file_root_records["references.txt"]["generated_count"],
        "rescans": file_root_records["rescans.txt"]["generated_count"],
    }

    blockers: list[str] = []
    if counts["required_payload_ready_scans"] < counts["selected_scans"]:
        blockers.append("selected scan payloads are missing or incomplete")
    if counts["sequence_zip_ready_scans"] < counts["selected_scans"]:
        blockers.append("sequence.zip is not staged for every selected scan")
    if counts["aligned_ply_ready_scans"] < counts["selected_scans"]:
        blockers.append("aligned PLY is not ready for every selected scan")
    if counts["multi_view_ready_scans"] < counts["selected_scans"]:
        blockers.append("multi_view features are not ready for every selected scan")

    status = "ready" if not blockers else "blocked"
    manifest = {
        "generated_at": now_iso(),
        "stage_version": "vlsat-stage-v1",
        "status": status,
        "source_dataset_root": str(dataset_root),
        "source_dataset_mutated": False,
        "staged_root": str(staged_root),
        "staged_subset_root": str(staged_subset_root),
        "staged_scan_root": str(staged_scan_root),
        "staged_files_root": str(staged_files_root),
        "selected_scans_file": rel(args.selected_scans.resolve()),
        "selected_scans": selected_scans,
        "link_mode": args.link_mode,
        "reference_aligned_copy_enabled": not args.no_reference_aligned_copy,
        "reference_aligned_mode": args.reference_aligned_mode,
        "official_vlsat_source": {
            "repository": "https://github.com/wz7in/CVPR2023-VLSAT",
            "reference_transform_behavior": "reference scans use identity aligned PLY from raw annotated PLY; full-validation Docker staging may symlink this identity file to avoid duplicate storage",
            "rescan_transform_behavior": "rescans require transform_ply.py with 3RScan.json transforms",
        },
        "subset_records": subset_records,
        "file_root_records": file_root_records,
        "selected_scan_records": selected_scan_records,
        "counts": counts,
        "blockers": blockers,
    }

    write_json(artifact_dir / "stage_manifest.json", manifest)
    write_text(artifact_dir / "stage_report.md", build_report(manifest))

    print(f"status={status}")
    print(f"staged_root={staged_root}")
    print(f"selected_scans={counts['selected_scans']}")
    print(f"faithful_vlsat_ready_scans={counts['faithful_vlsat_ready_scans']}")
    print(f"manifest={rel(artifact_dir / 'stage_manifest.json')}")
    print(f"report={rel(artifact_dir / 'stage_report.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
