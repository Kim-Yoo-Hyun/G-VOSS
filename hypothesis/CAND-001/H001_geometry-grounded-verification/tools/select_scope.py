#!/usr/bin/env python3
"""Fix the H001 hardened held-out validation scope."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


H001_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]

SUPPORT_CONTACT = {"standing on", "lying on", "supported by"}
PROXIMITY = {"close by"}
RELATIVE_VERTICAL = {"higher than", "lower than"}
ATTACHMENT_DEFERRED = {"attached to", "hanging on", "leaning against", "connected to"}
FAMILY_ORDER = [
    "support_contact",
    "proximity",
    "relative_vertical",
    "attachment_deferred",
    "other",
]
GEOMETRY_FILES = [
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--subset-root",
        type=Path,
        default=REPO_ROOT / "local_dataset" / "3DSSG_subset",
    )
    parser.add_argument(
        "--rscan-root",
        type=Path,
        default=REPO_ROOT / "local_dataset" / "3RScan",
    )
    parser.add_argument(
        "--staged-rscan-root",
        type=Path,
        default=REPO_ROOT
        / "local_dataset"
        / "VLSAT_staged"
        / "CVPR2023-VLSAT"
        / "data"
        / "3RScan",
    )
    parser.add_argument(
        "--mini-scans",
        type=Path,
        default=H001_ROOT / "artifacts" / "subset" / "h001_mini" / "scans.txt",
    )
    parser.add_argument(
        "--pilot-dir",
        type=Path,
        default=H001_ROOT / "artifacts" / "subset" / "h001_calib_pilot",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=H001_ROOT / "artifacts" / "subset" / "h001_validation_hardened",
    )
    parser.add_argument("--updated", default="2026-05-05")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def read_scan_list(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def predicate_family(label: str) -> str:
    if label in SUPPORT_CONTACT:
        return "support_contact"
    if label in PROXIMITY:
        return "proximity"
    if label in RELATIVE_VERTICAL:
        return "relative_vertical"
    if label in ATTACHMENT_DEFERRED:
        return "attachment_deferred"
    return "other"


def build_scan_groups(rscan_json_path: Path) -> dict[str, dict[str, Any]]:
    scan_groups: dict[str, dict[str, Any]] = {}
    for scene in load_json(rscan_json_path):
        group_reference = scene.get("reference")
        if not group_reference:
            continue
        scan_groups[group_reference] = {
            "group_reference": group_reference,
            "is_reference_scan": True,
            "scene_type": scene.get("type"),
        }
        for scan in scene.get("scans", []):
            scan_id = scan.get("reference")
            if scan_id:
                scan_groups[scan_id] = {
                    "group_reference": group_reference,
                    "is_reference_scan": scan_id == group_reference,
                    "scene_type": scene.get("type"),
                }
    return scan_groups


def payload_status(scan_id: str, rscan_root: Path, staged_rscan_root: Path) -> dict[str, Any]:
    source_dir = rscan_root / "scans" / scan_id
    staged_dir = staged_rscan_root / scan_id
    source_geometry = {name: (source_dir / name).exists() for name in GEOMETRY_FILES}
    staged_geometry = {name: (staged_dir / name).exists() for name in GEOMETRY_FILES}
    geometry_ready = all(source_geometry[name] or staged_geometry[name] for name in GEOMETRY_FILES)
    sequence_ready = (
        (source_dir / "sequence.zip").exists()
        or (source_dir / "sequence").is_dir()
        or (staged_dir / "sequence.zip").exists()
        or (staged_dir / "sequence").is_dir()
    )
    aligned_ready = (staged_dir / "labels.instances.align.annotated.v2.ply").exists()
    multi_view_dir = staged_dir / "multi_view"
    multi_view_ready = multi_view_dir.is_dir() and any(multi_view_dir.glob("*.npy"))
    return {
        "source_scan_dir_exists": source_dir.is_dir(),
        "staged_scan_dir_exists": staged_dir.is_dir(),
        "source_geometry_files": source_geometry,
        "staged_geometry_files": staged_geometry,
        "geometry_ready": geometry_ready,
        "sequence_ready": sequence_ready,
        "aligned_ply_ready": aligned_ready,
        "multi_view_ready": multi_view_ready,
        "faithful_vlsat_ready": geometry_ready
        and sequence_ready
        and aligned_ready
        and multi_view_ready,
    }


def summarize_validation_entries(
    entries: list[dict[str, Any]],
    scan_groups: dict[str, dict[str, Any]],
    rscan_root: Path,
    staged_rscan_root: Path,
) -> list[dict[str, Any]]:
    by_scan: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "entry_count": 0,
            "relationship_count": 0,
            "family_counts": Counter(),
            "label_counts": Counter(),
            "subgraphs": [],
        }
    )
    for entry in entries:
        scan_id = str(entry["scan"])
        record = by_scan[scan_id]
        family_counts: Counter[str] = Counter()
        label_counts: Counter[str] = Counter()
        for relation in entry.get("relationships", []):
            label = str(relation[3])
            family_counts[predicate_family(label)] += 1
            label_counts[label] += 1
        record["entry_count"] += 1
        record["relationship_count"] += len(entry.get("relationships", []))
        record["family_counts"].update(family_counts)
        record["label_counts"].update(label_counts)
        record["subgraphs"].append(
            {
                "subset_split_id": entry.get("split"),
                "object_count": len(entry.get("objects", {})),
                "relationship_count": len(entry.get("relationships", [])),
                "family_counts": {key: family_counts.get(key, 0) for key in FAMILY_ORDER},
            }
        )

    rows: list[dict[str, Any]] = []
    for scan_id, record in by_scan.items():
        group = scan_groups.get(scan_id, {})
        family_counts = record["family_counts"]
        score = (
            family_counts["support_contact"]
            + 0.25 * family_counts["proximity"]
            + 0.25 * family_counts["relative_vertical"]
        )
        rows.append(
            {
                "scan_id": scan_id,
                "group_reference": group.get("group_reference", scan_id),
                "is_reference_scan": bool(group.get("is_reference_scan", False)),
                "in_3rscan_metadata": scan_id in scan_groups,
                "scene_type": group.get("scene_type"),
                "entry_count": record["entry_count"],
                "relationship_count": record["relationship_count"],
                "family_counts": {key: family_counts.get(key, 0) for key in FAMILY_ORDER},
                "label_counts": dict(sorted(record["label_counts"].items())),
                "score": score,
                "subgraphs": record["subgraphs"],
                "payload_status": payload_status(scan_id, rscan_root, staged_rscan_root),
            }
        )
    return rows


def count_families(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row["family_counts"])
    return {key: counts.get(key, 0) for key in FAMILY_ORDER}


def count_payload(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "geometry_ready": sum(row["payload_status"]["geometry_ready"] for row in rows),
        "sequence_ready": sum(row["payload_status"]["sequence_ready"] for row in rows),
        "aligned_ply_ready": sum(row["payload_status"]["aligned_ply_ready"] for row in rows),
        "multi_view_ready": sum(row["payload_status"]["multi_view_ready"] for row in rows),
        "faithful_vlsat_ready": sum(row["payload_status"]["faithful_vlsat_ready"] for row in rows),
    }


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    validation_entries = load_json(args.subset_root / "relationships_validation.json")["scans"]
    scan_groups = build_scan_groups(args.rscan_root / "files" / "3RScan.json")
    rows = summarize_validation_entries(
        validation_entries, scan_groups, args.rscan_root, args.staged_rscan_root
    )

    mini_scans = set(read_scan_list(args.mini_scans))
    mini_groups = {scan_groups.get(scan_id, {}).get("group_reference", scan_id) for scan_id in mini_scans}
    train_scans = set(read_scan_list(args.pilot_dir / "train_scans.txt"))
    dev_scans = set(read_scan_list(args.pilot_dir / "dev_scans.txt"))
    calib_groups = {
        scan_groups.get(scan_id, {}).get("group_reference", scan_id)
        for scan_id in sorted(train_scans | dev_scans)
    }

    candidates: list[dict[str, Any]] = []
    selected: list[dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: item["scan_id"]):
        reason = "selected_hardened_validation"
        selected_flag = True
        if row["group_reference"] in mini_groups:
            reason = "excluded_h001_mini_group_previously_inspected"
            selected_flag = False
        elif row["group_reference"] in calib_groups:
            reason = "excluded_calibration_group_conflict"
            selected_flag = False
        candidate = dict(row)
        candidate["selected"] = selected_flag
        candidate["selection_reason"] = reason
        candidates.append(candidate)
        if selected_flag:
            selected.append(row)

    selected_groups = {row["group_reference"] for row in selected}
    total_groups = {row["group_reference"] for row in rows}
    excluded_mini = [row for row in candidates if row["selection_reason"].startswith("excluded_h001_mini")]
    excluded_calib = [row for row in candidates if row["selection_reason"].startswith("excluded_calibration")]

    manifest = {
        "schema_version": "h001_validation_scope_manifest_v1",
        "created_at": args.updated,
        "scope_name": "h001_validation_hardened",
        "source_split": "3DSSG_subset/relationships_validation.json",
        "selection_policy": {
            "decision": "official_validation_minus_h001_mini_groups",
            "select_all_remaining_official_validation_scans": True,
            "exclude_h001_mini_reference_rescan_groups": True,
            "exclude_calibration_reference_rescan_groups": True,
            "minimum_scan_target": 32,
            "no_tuning_rule": (
                "Do not tune thresholds, calibrators, verifier variants, or baseline settings "
                "on selected hardened validation scans before final reportable metrics."
            ),
            "h001_mini_role": "smoke/pilot only; excluded by reference/rescan group",
        },
        "inputs": {
            "subset_root": str(args.subset_root),
            "rscan_root": str(args.rscan_root),
            "staged_rscan_root": str(args.staged_rscan_root),
            "mini_scans_file": str(args.mini_scans),
            "pilot_dir": str(args.pilot_dir),
        },
        "counts": {
            "official_validation_scans": len(rows),
            "official_validation_groups": len(total_groups),
            "selected_scans": len(selected),
            "selected_groups": len(selected_groups),
            "excluded_h001_mini_group_scans": len(excluded_mini),
            "excluded_calibration_group_conflict_scans": len(excluded_calib),
            "selected_subgraph_entries": sum(row["entry_count"] for row in selected),
            "selected_relationships": sum(row["relationship_count"] for row in selected),
            "selected_family_counts": count_families(selected),
            "selected_payload_ready_counts": count_payload(selected),
            "official_validation_family_counts": count_families(rows),
        },
        "runtime_risk": {
            "status": "payload_not_ready",
            "reason": "selected hardened validation scans currently have no faithful VL-SAT payloads staged",
            "required_next_prep": [
                "download raw geometry payloads",
                "download sequence.zip or prepare sequence/",
                "stage aligned PLY",
                "generate multi_view features",
                "run staged layout checker",
            ],
        },
        "final_metric_guardrail": (
            "No final reportable metric generation until this scope is preserved and selected payload "
            "readiness is updated without changing selected scan ids."
        ),
    }

    write_json(args.output_dir / "manifest.json", manifest)
    write_jsonl(args.output_dir / "candidates.jsonl", candidates)
    write_jsonl(
        args.output_dir / "subgraphs.jsonl",
        [
            {
                "scan_id": row["scan_id"],
                "group_reference": row["group_reference"],
                "subgraph": subgraph,
            }
            for row in selected
            for subgraph in row["subgraphs"]
        ],
    )
    (args.output_dir / "scans.txt").write_text(
        "\n".join(row["scan_id"] for row in selected) + "\n", encoding="utf-8"
    )
    report = [
        "# H001 Validation Hardened Scope",
        "",
        f"Last updated: {args.updated}",
        "",
        "## Decision",
        "",
        "Use official `3DSSG_subset` validation scans excluding all H001-Mini reference/rescan groups.",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| official validation scans | {len(rows)} |",
        f"| official validation groups | {len(total_groups)} |",
        f"| selected hardened scans | {len(selected)} |",
        f"| selected hardened groups | {len(selected_groups)} |",
        f"| excluded H001-Mini group scans | {len(excluded_mini)} |",
        f"| excluded calibration conflict scans | {len(excluded_calib)} |",
        f"| selected subgraph entries | {manifest['counts']['selected_subgraph_entries']} |",
        f"| selected relationships | {manifest['counts']['selected_relationships']} |",
        "",
        "## Selected Family Counts",
        "",
        "| Family | Count |",
        "| --- | ---: |",
    ]
    report.extend(
        f"| `{family}` | {count} |"
        for family, count in manifest["counts"]["selected_family_counts"].items()
    )
    report.extend(
        [
            "",
            "## Payload Readiness",
            "",
            "| Item | Ready scans |",
            "| --- | ---: |",
        ]
    )
    report.extend(
        f"| `{key}` | {value} / {len(selected)} |"
        for key, value in manifest["counts"]["selected_payload_ready_counts"].items()
    )
    report.extend(
        [
            "",
            "## No-Tuning Rule",
            "",
            manifest["selection_policy"]["no_tuning_rule"],
            "",
            "## Runtime Risk",
            "",
            "Selected hardened validation scans currently need payload download/staging before final metrics.",
        ]
    )
    (args.output_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(json.dumps(manifest["counts"], indent=2, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
