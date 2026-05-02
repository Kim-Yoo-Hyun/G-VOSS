#!/usr/bin/env python3
"""Check local dataset compatibility with the VL-SAT layout."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "layout" / "vlsat"

SUBSET_FILES = {
    "classes": "classes.txt",
    "relationships": "relationships.txt",
    "relations_alias": "relations.txt",
    "relationships_all": "relationships.json",
    "relationships_train": "relationships_train.json",
    "relationships_validation": "relationships_validation.json",
    "train_scans": "train_scans.txt",
    "validation_scans": "validation_scans.txt",
}

H001_SCAN_FILES = (
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
)

VLSAT_SCAN_FILES = (
    "labels.instances.align.annotated.v2.ply",
    "labels.instances.align.annotated.ply",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check local 3DSSG_subset / 3RScan layout against VL-SAT expectations."
    )
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--fail-on-blockers",
        action="store_true",
        help="Exit non-zero when VL-SAT default-layout blockers are found.",
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


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


def scan_ids_from_subset_json(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = load_json(path)
    scan_ids = {
        str(entry.get("scan"))
        for entry in data.get("scans", [])
        if entry.get("scan") is not None
    }
    return sorted(scan_ids)


def count_entries(path: Path) -> int | None:
    if not path.exists():
        return None
    data = load_json(path)
    scans = data.get("scans")
    return len(scans) if isinstance(scans, list) else None


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def file_record(path: Path, required_for: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "required_for": required_for,
    }


def compare_scan_list_file(path: Path, expected_scan_ids: list[str]) -> dict[str, Any]:
    actual = read_lines(path)
    expected = set(expected_scan_ids)
    actual_set = set(actual)
    return {
        "path": rel(path),
        "exists": path.exists(),
        "actual_count": len(actual),
        "expected_count": len(expected_scan_ids),
        "missing_from_file": sorted(expected - actual_set)[:20],
        "extra_in_file": sorted(actual_set - expected)[:20],
        "matches_expected": path.exists() and actual_set == expected,
    }


def inspect_scan(scan_dir: Path, dataset_root: Path) -> dict[str, Any]:
    h001_files = {name: (scan_dir / name).exists() for name in H001_SCAN_FILES}
    aligned_candidates = {name: (scan_dir / name).exists() for name in VLSAT_SCAN_FILES}
    return {
        "scan_id": scan_dir.name,
        "path": rel(scan_dir),
        "h001_files": h001_files,
        "h001_ready": all(h001_files.values()),
        "vlsat_aligned_ply_ready": any(aligned_candidates.values()),
        "vlsat_aligned_ply_candidates": aligned_candidates,
        "multi_view_ready": (scan_dir / "multi_view").is_dir(),
        "direct_vlsat_root_style": (dataset_root / "3RScan" / scan_dir.name).is_dir(),
    }


def build_report(summary: dict[str, Any]) -> str:
    blockers = summary["blockers"]
    warnings = summary["warnings"]
    counts = summary["counts"]
    status = summary["status"]

    lines = [
        "# VL-SAT Layout Check",
        "",
        f"Generated: {summary['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- status: `{status}`",
        f"- default VL-SAT ready: `{str(summary['default_vlsat_ready']).lower()}`",
        f"- H001 one-scan geometry ready scans: `{counts['h001_ready_scan_dirs']}`",
        "",
        "## Counts",
        "",
        f"- subset all entries: `{counts['relationships_all_entries']}`",
        f"- subset all unique scans: `{counts['relationships_all_unique_scans']}`",
        f"- train entries: `{counts['relationships_train_entries']}`",
        f"- train unique scans: `{counts['relationships_train_unique_scans']}`",
        f"- validation entries: `{counts['relationships_validation_entries']}`",
        f"- validation unique scans: `{counts['relationships_validation_unique_scans']}`",
        f"- train/validation overlap: `{counts['train_validation_overlap']}`",
        f"- local 3RScan scan dirs: `{counts['local_scan_dirs']}`",
        "",
        "## Blockers",
        "",
    ]
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- none")

    lines.extend(["", "## Warnings", ""])
    if warnings:
        lines.extend(f"- {item}" for item in warnings)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Missing Generated Annotation Files",
            "",
        ]
    )
    for key in ("relations_alias", "train_scans", "validation_scans"):
        record = summary["subset_files"][key]
        lines.append(f"- `{record['path']}`: {'present' if record['exists'] else 'missing'}")

    lines.extend(
        [
            "",
            "## Local Scan Coverage",
            "",
        ]
    )
    for scan in summary["scan_checks"]:
        lines.append(
            "- `{scan_id}`: h001_ready=`{h001}`, aligned_ply=`{aligned}`, multi_view=`{multi}`".format(
                scan_id=scan["scan_id"],
                h001=str(scan["h001_ready"]).lower(),
                aligned=str(scan["vlsat_aligned_ply_ready"]).lower(),
                multi=str(scan["multi_view_ready"]).lower(),
            )
        )

    lines.extend(
        [
            "",
            "## Next",
            "",
            "1. Generate or stage `relations.txt`, `train_scans.txt`, and `validation_scans.txt` outside source dataset mutation.",
            "2. Decide faithful aligned+`multi_view` route vs 3D-only plumbing route.",
            "3. Download selected H001-Mini scan payloads before prediction-level evaluation.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    dataset_root = args.dataset_root.resolve()
    subset_root = dataset_root / "3DSSG_subset"
    rscan_root = dataset_root / "3RScan"
    local_scan_root = rscan_root / "scans"

    subset_files = {
        key: file_record(subset_root / filename, "vlsat_layout")
        for key, filename in SUBSET_FILES.items()
    }

    train_json = subset_root / SUBSET_FILES["relationships_train"]
    validation_json = subset_root / SUBSET_FILES["relationships_validation"]
    all_json = subset_root / SUBSET_FILES["relationships_all"]
    train_scans = scan_ids_from_subset_json(train_json)
    validation_scans = scan_ids_from_subset_json(validation_json)
    all_scans = scan_ids_from_subset_json(all_json)
    overlap = sorted(set(train_scans) & set(validation_scans))

    train_scan_list = compare_scan_list_file(subset_root / "train_scans.txt", train_scans)
    validation_scan_list = compare_scan_list_file(
        subset_root / "validation_scans.txt", validation_scans
    )

    relationships_txt = subset_root / "relationships.txt"
    relations_txt = subset_root / "relations.txt"
    relation_alias_matches = None
    if relationships_txt.exists() and relations_txt.exists():
        relation_alias_matches = read_lines(relationships_txt) == read_lines(relations_txt)

    scan_dirs = sorted(p for p in local_scan_root.iterdir() if p.is_dir()) if local_scan_root.exists() else []
    scan_checks = [inspect_scan(scan_dir, dataset_root) for scan_dir in scan_dirs]
    scan_counter = Counter()
    for scan in scan_checks:
        scan_counter["h001_ready"] += int(scan["h001_ready"])
        scan_counter["aligned_ply_ready"] += int(scan["vlsat_aligned_ply_ready"])
        scan_counter["multi_view_ready"] += int(scan["multi_view_ready"])
        scan_counter["direct_vlsat_root_style"] += int(scan["direct_vlsat_root_style"])

    available_scan_ids = {scan["scan_id"] for scan in scan_checks}
    available_train_scan_ids = sorted(available_scan_ids & set(train_scans))
    available_validation_scan_ids = sorted(available_scan_ids & set(validation_scans))

    blockers: list[str] = []
    warnings: list[str] = []

    for key in ("classes", "relationships", "relationships_all", "relationships_train", "relationships_validation"):
        if not subset_files[key]["exists"]:
            blockers.append(f"missing required subset file: {subset_files[key]['path']}")

    if not subset_files["relations_alias"]["exists"]:
        blockers.append("missing VL-SAT config relation label file: local_dataset/3DSSG_subset/relations.txt")
    elif relation_alias_matches is False:
        blockers.append("relations.txt exists but does not match relationships.txt ordering")

    if not train_scan_list["exists"]:
        blockers.append("missing train_scans.txt required by VL-SAT dataset loader")
    elif not train_scan_list["matches_expected"]:
        blockers.append("train_scans.txt does not match unique scans from relationships_train.json")

    if not validation_scan_list["exists"]:
        blockers.append("missing validation_scans.txt required by VL-SAT dataset loader")
    elif not validation_scan_list["matches_expected"]:
        blockers.append("validation_scans.txt does not match unique scans from relationships_validation.json")

    if overlap:
        blockers.append(f"train/validation scan overlap detected: {len(overlap)} scans")

    if not scan_dirs:
        blockers.append("no local 3RScan scan payload directories found under local_dataset/3RScan/scans")

    if scan_counter["aligned_ply_ready"] < len(scan_checks):
        blockers.append("aligned PLY missing for at least one local scan")

    if scan_counter["multi_view_ready"] < len(scan_checks):
        blockers.append("multi_view features missing for at least one local scan while VL-SAT default uses 2D features")

    if scan_counter["direct_vlsat_root_style"] < len(scan_checks):
        warnings.append("local 3RScan root uses local_dataset/3RScan/scans/<scan_id>, not direct 3RScan/<scan_id>")

    if not available_validation_scan_ids:
        warnings.append("no downloaded local scan payload currently belongs to official validation split")

    if len(scan_checks) < 2:
        warnings.append("only one local 3RScan scan payload is available; multi-scan evaluation remains blocked")

    default_vlsat_ready = not blockers
    status = "ready" if default_vlsat_ready else "blocked"

    prep_manifest = {
        "do_not_mutate_source_dataset_by_default": True,
        "generated_annotation_files": {
            "relations.txt": {
                "source": rel(relationships_txt),
                "target": rel(relations_txt),
                "action": "copy_or_stage_exact_contents",
                "needed": not relations_txt.exists() or relation_alias_matches is False,
            },
            "train_scans.txt": {
                "source": rel(train_json),
                "target": rel(subset_root / "train_scans.txt"),
                "action": "write_sorted_unique_scan_ids_from_relationships_train_json",
                "count": len(train_scans),
                "needed": not train_scan_list["matches_expected"],
            },
            "validation_scans.txt": {
                "source": rel(validation_json),
                "target": rel(subset_root / "validation_scans.txt"),
                "action": "write_sorted_unique_scan_ids_from_relationships_validation_json",
                "count": len(validation_scans),
                "needed": not validation_scan_list["matches_expected"],
            },
        },
        "path_strategy_needed": scan_counter["direct_vlsat_root_style"] < len(scan_checks),
        "aligned_ply_needed": scan_counter["aligned_ply_ready"] < len(scan_checks),
        "multi_view_needed": scan_counter["multi_view_ready"] < len(scan_checks),
    }

    summary = {
        "generated_at": now_iso(),
        "checker_version": "vlsat-layout-check-v1",
        "dataset_root": str(dataset_root),
        "output_dir": str(args.output_dir.resolve()),
        "status": status,
        "default_vlsat_ready": default_vlsat_ready,
        "subset_files": subset_files,
        "train_scan_list": train_scan_list,
        "validation_scan_list": validation_scan_list,
        "relation_alias_matches": relation_alias_matches,
        "counts": {
            "relationships_all_entries": count_entries(all_json),
            "relationships_all_unique_scans": len(all_scans),
            "relationships_train_entries": count_entries(train_json),
            "relationships_train_unique_scans": len(train_scans),
            "relationships_validation_entries": count_entries(validation_json),
            "relationships_validation_unique_scans": len(validation_scans),
            "train_validation_overlap": len(overlap),
            "local_scan_dirs": len(scan_checks),
            "h001_ready_scan_dirs": scan_counter["h001_ready"],
            "aligned_ply_ready_scan_dirs": scan_counter["aligned_ply_ready"],
            "multi_view_ready_scan_dirs": scan_counter["multi_view_ready"],
            "direct_vlsat_root_style_scan_dirs": scan_counter["direct_vlsat_root_style"],
            "available_train_scan_payloads": len(available_train_scan_ids),
            "available_validation_scan_payloads": len(available_validation_scan_ids),
        },
        "available_train_scan_ids": available_train_scan_ids,
        "available_validation_scan_ids": available_validation_scan_ids,
        "blockers": blockers,
        "warnings": warnings,
        "scan_checks": scan_checks,
        "prep_manifest": prep_manifest,
    }

    output_dir = args.output_dir.resolve()
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "prep_manifest.json", prep_manifest)
    write_text(output_dir / "report.md", build_report(summary))

    print(f"status={status}")
    print(f"default_vlsat_ready={str(default_vlsat_ready).lower()}")
    print(f"blockers={len(blockers)} warnings={len(warnings)}")
    print(f"report={rel(output_dir / 'report.md')}")

    if args.fail_on_blockers and blockers:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
