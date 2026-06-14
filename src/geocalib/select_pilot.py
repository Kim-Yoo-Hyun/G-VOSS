#!/usr/bin/env python3
"""Select H001-Calib-Pilot train/dev scans from official 3DSSG_subset."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


REPO_ROOT = Path(__file__).resolve().parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT

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
FAITHFUL_VLSAT_FILES = [*GEOMETRY_FILES, "sequence.zip"]
DEFAULT_EXCLUDED_SCANS = {"f62fd5fd-9a3f-2f44-883a-1e5cf819608e"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select H001-Calib-Pilot train/dev scans without using validation failures."
    )
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
        "--mini-dir",
        type=Path,
        default=H001_ROOT / "artifacts" / "subset" / "h001_mini",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=H001_ROOT / "artifacts" / "subset" / "h001_calib_pilot",
    )
    parser.add_argument("--train-limit", type=int, default=24)
    parser.add_argument("--dev-limit", type=int, default=8)
    parser.add_argument("--min-scan-support", type=int, default=15)
    parser.add_argument("--min-subgraph-support", type=int, default=5)
    parser.add_argument("--updated", default="2026-05-04")
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


def relation_counts(relationships: list[list[Any]]) -> tuple[Counter[str], Counter[str]]:
    family_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    for row in relationships:
        label = str(row[3])
        family_counts[predicate_family(label)] += 1
        label_counts[label] += 1
    return family_counts, label_counts


def build_scan_groups(rscan_json_path: Path) -> dict[str, dict[str, Any]]:
    scenes = load_json(rscan_json_path)
    scan_groups: dict[str, dict[str, Any]] = {}
    for scene in scenes:
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
            if not scan_id:
                continue
            scan_groups[scan_id] = {
                "group_reference": group_reference,
                "is_reference_scan": scan_id == group_reference,
                "scene_type": scene.get("type"),
            }
    return scan_groups


def payload_status(scan_id: str, rscan_root: Path, staged_rscan_root: Path) -> dict[str, Any]:
    source_dir = rscan_root / "scans" / scan_id
    staged_dir = staged_rscan_root / scan_id
    source_files = {name: (source_dir / name).exists() for name in FAITHFUL_VLSAT_FILES}
    staged_files = {name: (staged_dir / name).exists() for name in FAITHFUL_VLSAT_FILES}
    source_sequence = (source_dir / "sequence").is_dir()
    staged_sequence = (staged_dir / "sequence").is_dir()
    staged_multi_view = staged_dir / "multi_view"
    source_geometry_ready = all(source_files[name] for name in GEOMETRY_FILES)
    staged_geometry_ready = all(staged_files[name] for name in GEOMETRY_FILES)
    source_vlsat_ready = source_geometry_ready and (source_files["sequence.zip"] or source_sequence)
    staged_vlsat_ready = staged_geometry_ready and (staged_files["sequence.zip"] or staged_sequence)
    required_missing = [
        name
        for name in FAITHFUL_VLSAT_FILES
        if not source_files[name] and not staged_files[name]
    ]
    return {
        "source_scan_dir_exists": source_dir.is_dir(),
        "staged_scan_dir_exists": staged_dir.is_dir(),
        "source_files": source_files,
        "staged_files": staged_files,
        "source_sequence_dir_exists": source_sequence,
        "staged_sequence_dir_exists": staged_sequence,
        "staged_aligned_ply_exists": (staged_dir / "labels.instances.align.annotated.v2.ply").exists(),
        "staged_multi_view_dir_exists": staged_multi_view.is_dir(),
        "staged_multi_view_file_count": (
            len(list(staged_multi_view.glob("*.npy"))) if staged_multi_view.is_dir() else 0
        ),
        "source_geometry_ready": source_geometry_ready,
        "staged_geometry_ready": staged_geometry_ready,
        "source_faithful_vlsat_ready": source_vlsat_ready,
        "staged_faithful_vlsat_ready": staged_vlsat_ready,
        "download_or_stage_needed_files": required_missing,
    }


def summarize_entries(
    entries: list[dict[str, Any]],
    scan_groups: dict[str, dict[str, Any]],
    rscan_root: Path,
    staged_rscan_root: Path,
    source_split: str,
) -> list[dict[str, Any]]:
    by_scan: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "entry_count": 0,
            "relationship_count": 0,
            "object_labels": set(),
            "family_counts": Counter(),
            "label_counts": Counter(),
            "subgraphs": [],
        }
    )
    for entry in entries:
        scan_id = str(entry["scan"])
        relationships = entry.get("relationships", [])
        family_counts, label_counts = relation_counts(relationships)
        score = (
            family_counts["support_contact"]
            + 0.25 * family_counts["proximity"]
            + 0.25 * family_counts["relative_vertical"]
        )
        record = by_scan[scan_id]
        record["entry_count"] += 1
        record["relationship_count"] += len(relationships)
        record["object_labels"].update(str(value) for value in entry.get("objects", {}).values())
        record["family_counts"].update(family_counts)
        record["label_counts"].update(label_counts)
        record["subgraphs"].append(
            {
                "split": entry.get("split"),
                "relationship_count": len(relationships),
                "object_count": len(entry.get("objects", {})),
                "family_counts": {key: family_counts.get(key, 0) for key in FAMILY_ORDER},
                "score": score,
            }
        )

    rows: list[dict[str, Any]] = []
    for scan_id, record in by_scan.items():
        family_counts = record["family_counts"]
        score = (
            family_counts["support_contact"]
            + 0.25 * family_counts["proximity"]
            + 0.25 * family_counts["relative_vertical"]
        )
        group_info = scan_groups.get(scan_id, {})
        subgraphs = sorted(
            record["subgraphs"],
            key=lambda item: (item["score"], item["family_counts"]["support_contact"]),
            reverse=True,
        )
        rows.append(
            {
                "scan_id": scan_id,
                "source_split": source_split,
                "group_reference": group_info.get("group_reference", scan_id),
                "is_reference_scan": bool(group_info.get("is_reference_scan", False)),
                "in_3rscan_metadata": scan_id in scan_groups,
                "scene_type": group_info.get("scene_type"),
                "entry_count": record["entry_count"],
                "relationship_count": record["relationship_count"],
                "object_label_count": len(record["object_labels"]),
                "family_counts": {key: family_counts.get(key, 0) for key in FAMILY_ORDER},
                "label_counts": dict(sorted(record["label_counts"].items())),
                "max_subgraph_support_contact": max(
                    subgraph["family_counts"]["support_contact"] for subgraph in subgraphs
                ),
                "score": score,
                "subgraphs": subgraphs,
                "payload_status": payload_status(scan_id, rscan_root, staged_rscan_root),
            }
        )
    return rows


def candidate_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    counts = row["family_counts"]
    return (
        row["score"],
        counts["support_contact"],
        counts["relative_vertical"],
        counts["proximity"],
        row["relationship_count"],
        row["entry_count"],
        row["scan_id"],
    )


def annotate_and_select(
    rows: list[dict[str, Any]],
    train_limit: int,
    dev_limit: int,
    min_scan_support: int,
    min_subgraph_support: int,
    blocked_scan_ids: set[str],
    blocked_group_refs: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    selected_train: list[dict[str, Any]] = []
    selected_dev: list[dict[str, Any]] = []
    selected_group_refs: set[str] = set()
    annotated: list[dict[str, Any]] = []

    for rank, row in enumerate(sorted(rows, key=candidate_sort_key, reverse=True), start=1):
        role = None
        reason = "not_selected_after_limit"
        if row["scan_id"] in blocked_scan_ids:
            reason = "excluded_scan"
        elif row["group_reference"] in blocked_group_refs:
            reason = "blocked_validation_or_excluded_group"
        elif row["family_counts"]["support_contact"] < min_scan_support:
            reason = "below_min_scan_support"
        elif row["max_subgraph_support_contact"] < min_subgraph_support:
            reason = "below_min_subgraph_support"
        elif row["group_reference"] in selected_group_refs:
            reason = "duplicate_selected_group"
        elif len(selected_train) < train_limit:
            role = "train"
            reason = "selected_train"
            selected_train.append(row)
            selected_group_refs.add(row["group_reference"])
        elif len(selected_dev) < dev_limit:
            role = "dev"
            reason = "selected_dev"
            selected_dev.append(row)
            selected_group_refs.add(row["group_reference"])

        annotated_row = dict(row)
        annotated_row["candidate_rank"] = rank
        annotated_row["selected_role"] = role
        annotated_row["selection_reason"] = reason
        annotated.append(annotated_row)

    for index, row in enumerate(selected_train, start=1):
        row["selected_role"] = "train"
        row["selected_rank"] = index
        row["selection_reason"] = "selected_train"
    for index, row in enumerate(selected_dev, start=1):
        row["selected_role"] = "dev"
        row["selected_rank"] = index
        row["selection_reason"] = "selected_dev"

    selected_by_id = {row["scan_id"]: row for row in [*selected_train, *selected_dev]}
    for row in annotated:
        selected = selected_by_id.get(row["scan_id"])
        if selected:
            row["selected_role"] = selected["selected_role"]
            row["selected_rank"] = selected["selected_rank"]
            row["selection_reason"] = selected["selection_reason"]

    return selected_train, selected_dev, annotated


def total_family_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row["family_counts"])
    return {key: counts.get(key, 0) for key in FAMILY_ORDER}


def role_totals(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scan_count": len(rows),
        "entry_count": sum(row["entry_count"] for row in rows),
        "relationship_count": sum(row["relationship_count"] for row in rows),
        "family_counts": total_family_counts(rows),
        "source_geometry_ready_scans": sum(
            1 for row in rows if row["payload_status"]["source_geometry_ready"]
        ),
        "staged_faithful_vlsat_ready_scans": sum(
            1 for row in rows if row["payload_status"]["staged_faithful_vlsat_ready"]
        ),
    }


def selected_subgraph_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    subgraphs: list[dict[str, Any]] = []
    for row in rows:
        for subgraph in row["subgraphs"]:
            subgraphs.append(
                {
                    "scan_id": row["scan_id"],
                    "role": row["selected_role"],
                    "selected_rank": row["selected_rank"],
                    "source_split": row["source_split"],
                    "split": subgraph["split"],
                    "relationship_count": subgraph["relationship_count"],
                    "object_count": subgraph["object_count"],
                    "family_counts": subgraph["family_counts"],
                    "score": subgraph["score"],
                }
            )
    return subgraphs


def make_report(manifest: dict[str, Any]) -> str:
    params = manifest["parameters"]
    roles = manifest["roles"]
    lines = [
        "# H001-Calib-Pilot",
        "",
        f"Last updated: {manifest['updated']}",
        "",
        "This artifact fixes the first train/dev scan split for H001 calibration fitting.",
        "No payload download, baseline inference, or `p_geom_valid` fitting is performed here.",
        "",
        "## Selection Policy",
        "",
        "- Source split for train/dev: official `3DSSG_subset/relationships_train.json`.",
        "- Held-out validation: existing H001-Mini validation scans.",
        "- Primary target: `support_contact` coverage.",
        "- Secondary coverage: `proximity` and `relative_vertical`.",
        "- Duplicate control: at most one scan per 3RScan reference/rescan group across train, dev, and validation.",
        "- Exclusion: the old one-scan smoke case is not used for train/dev calibration fitting.",
        "- Score: `support_contact + 0.25 * proximity + 0.25 * relative_vertical`.",
        "",
        "## Parameters",
        "",
        f"- train scans: {params['train_limit']}",
        f"- dev scans: {params['dev_limit']}",
        f"- validation scans: {len(roles['validation']['scan_ids'])}",
        f"- min scan-level support/contact: {params['min_scan_support']}",
        f"- min best-subgraph support/contact: {params['min_subgraph_support']}",
        "",
        "## Totals",
        "",
        "| Role | Scans | Entries | Relations | Support/contact | Proximity | Vertical | Geometry ready | Staged VL-SAT ready |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for role_name in ["train", "dev", "validation"]:
        totals = roles[role_name]["totals"]
        families = totals["family_counts"]
        lines.append(
            "| {role} | {scans} | {entries} | {relations} | {support} | {proximity} | {vertical} | {geom} | {vlsat} |".format(
                role=role_name,
                scans=totals["scan_count"],
                entries=totals["entry_count"],
                relations=totals["relationship_count"],
                support=families["support_contact"],
                proximity=families["proximity"],
                vertical=families["relative_vertical"],
                geom=totals["source_geometry_ready_scans"],
                vlsat=totals["staged_faithful_vlsat_ready_scans"],
            )
        )

    for role_name in ["train", "dev"]:
        lines.extend(["", f"## {role_name.title()} Scans", ""])
        lines.append("| Rank | Scan | Group | Score | Entries | Relations | Support/contact | Proximity | Vertical | Local payload |")
        lines.append("| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
        for row in roles[role_name]["scans"]:
            families = row["family_counts"]
            payload = row["payload_status"]
            payload_label = "ready" if payload["source_geometry_ready"] else "missing"
            lines.append(
                "| {rank} | `{scan}` | `{group}` | {score:.2f} | {entries} | {relations} | {support} | {proximity} | {vertical} | {payload} |".format(
                    rank=row["selected_rank"],
                    scan=row["scan_id"],
                    group=row["group_reference"],
                    score=row["score"],
                    entries=row["entry_count"],
                    relations=row["relationship_count"],
                    support=families["support_contact"],
                    proximity=families["proximity"],
                    vertical=families["relative_vertical"],
                    payload=payload_label,
                )
            )

    lines.extend(
        [
            "",
            "## Payload Plan",
            "",
            "Required for `train_dev_calib` geometry export:",
            "",
            "```text",
            "labels.instances.annotated.v2.ply",
            "semseg.v2.json",
            "mesh.refined.0.010000.segs.v2.json",
            "```",
            "",
            "Required later for faithful `VL-SAT` prediction export:",
            "",
            "```text",
            "sequence.zip",
            "labels.instances.align.annotated.v2.ply",
            "sequence/",
            "multi_view/",
            "```",
            "",
            "Do not use H001-Mini validation scans for fitting or threshold tuning.",
            "",
            "## Files",
            "",
            "- `manifest.json`: role lists, totals, payload status, and leakage checks.",
            "- `train_scans.txt`: selected train scan ids.",
            "- `dev_scans.txt`: selected dev scan ids.",
            "- `validation_scans.txt`: fixed H001-Mini validation scan ids.",
            "- `scans.txt`: all pilot scan ids grouped train, dev, validation.",
            "- `candidates.jsonl`: all train-split candidate scans and selection reasons.",
            "- `subgraphs.jsonl`: selected train/dev/validation subgraph summaries.",
            "",
            "## Next",
            "",
            "1. Download or stage required train/dev geometry payloads.",
            "2. Run `tools/export_calibration.py` on the train/dev split as `train_dev_calib`.",
            "3. Fit/evaluate the first `p_geom_valid` calibrator only after `train_dev_calib` exists.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    train_path = args.subset_root / "relationships_train.json"
    validation_path = args.subset_root / "relationships_validation.json"
    rscan_json_path = args.rscan_root / "files" / "3RScan.json"
    mini_scans_path = args.mini_dir / "scans.txt"

    missing = [
        path
        for path in [train_path, validation_path, rscan_json_path, mini_scans_path]
        if not path.exists()
    ]
    if missing:
        for path in missing:
            print(f"missing_input:{path}")
        return 2

    scan_groups = build_scan_groups(rscan_json_path)
    validation_scan_ids = read_scan_list(mini_scans_path)
    validation_group_refs = {
        scan_groups.get(scan_id, {}).get("group_reference", scan_id)
        for scan_id in validation_scan_ids
    }
    excluded_group_refs = {
        scan_groups.get(scan_id, {}).get("group_reference", scan_id)
        for scan_id in DEFAULT_EXCLUDED_SCANS
    }

    train_data = load_json(train_path)
    validation_data = load_json(validation_path)
    train_rows = summarize_entries(
        train_data["scans"],
        scan_groups,
        args.rscan_root,
        args.staged_rscan_root,
        source_split="train",
    )
    validation_rows_all = summarize_entries(
        [
            entry
            for entry in validation_data["scans"]
            if str(entry["scan"]) in set(validation_scan_ids)
        ],
        scan_groups,
        args.rscan_root,
        args.staged_rscan_root,
        source_split="validation",
    )
    validation_rows_by_id = {row["scan_id"]: row for row in validation_rows_all}
    validation_rows = [validation_rows_by_id[scan_id] for scan_id in validation_scan_ids]
    for index, row in enumerate(validation_rows, start=1):
        row["selected_role"] = "validation"
        row["selected_rank"] = index
        row["selection_reason"] = "fixed_h001_mini_validation"

    selected_train, selected_dev, candidates = annotate_and_select(
        train_rows,
        train_limit=args.train_limit,
        dev_limit=args.dev_limit,
        min_scan_support=args.min_scan_support,
        min_subgraph_support=args.min_subgraph_support,
        blocked_scan_ids=set(validation_scan_ids) | DEFAULT_EXCLUDED_SCANS,
        blocked_group_refs=validation_group_refs | excluded_group_refs,
    )

    selected_all = [*selected_train, *selected_dev, *validation_rows]
    selected_group_roles: dict[str, list[str]] = defaultdict(list)
    for row in selected_all:
        selected_group_roles[row["group_reference"]].append(row["selected_role"])
    group_conflicts = {
        group: roles
        for group, roles in selected_group_roles.items()
        if len(set(roles)) > 1 or len(roles) > 1
    }

    manifest = {
        "updated": args.updated,
        "artifact": "h001_calib_pilot",
        "status": "ready"
        if len(selected_train) == args.train_limit
        and len(selected_dev) == args.dev_limit
        and not group_conflicts
        else "blocked",
        "source": {
            "train_file": str(train_path),
            "validation_file": str(validation_path),
            "rscan_json": str(rscan_json_path),
            "mini_scans": str(mini_scans_path),
        },
        "parameters": {
            "train_limit": args.train_limit,
            "dev_limit": args.dev_limit,
            "min_scan_support": args.min_scan_support,
            "min_subgraph_support": args.min_subgraph_support,
            "score_formula": "support_contact + 0.25 * proximity + 0.25 * relative_vertical",
            "duplicate_policy": "at most one selected scan per 3RScan reference/rescan group across train/dev/validation",
            "excluded_scans": sorted(DEFAULT_EXCLUDED_SCANS),
        },
        "candidate_train_scan_count": len(train_rows),
        "train_subgraph_count": len(train_data["scans"]),
        "validation_subgraph_count": len(validation_data["scans"]),
        "roles": {
            "train": {
                "scan_ids": [row["scan_id"] for row in selected_train],
                "totals": role_totals(selected_train),
                "scans": selected_train,
            },
            "dev": {
                "scan_ids": [row["scan_id"] for row in selected_dev],
                "totals": role_totals(selected_dev),
                "scans": selected_dev,
            },
            "validation": {
                "scan_ids": validation_scan_ids,
                "totals": role_totals(validation_rows),
                "scans": validation_rows,
            },
        },
        "leakage_checks": {
            "train_dev_validation_scan_overlap": sorted(
                (
                    set(row["scan_id"] for row in selected_train)
                    & set(row["scan_id"] for row in selected_dev)
                )
                | (
                    set(row["scan_id"] for row in selected_train)
                    & set(validation_scan_ids)
                )
                | (
                    set(row["scan_id"] for row in selected_dev)
                    & set(validation_scan_ids)
                )
            ),
            "group_conflicts": group_conflicts,
            "validation_blocked_group_count": len(validation_group_refs),
            "excluded_group_count": len(excluded_group_refs),
        },
        "notes": [
            "This artifact selects train/dev scans only; it does not download or stage payloads.",
            "H001-Mini validation scans remain held out and are not used for fitting.",
            "The one-scan smoke case is excluded from train/dev calibration fitting.",
        ],
    }

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "manifest.json", manifest)
    (output_dir / "train_scans.txt").write_text(
        "".join(f"{scan_id}\n" for scan_id in manifest["roles"]["train"]["scan_ids"]),
        encoding="utf-8",
    )
    (output_dir / "dev_scans.txt").write_text(
        "".join(f"{scan_id}\n" for scan_id in manifest["roles"]["dev"]["scan_ids"]),
        encoding="utf-8",
    )
    (output_dir / "validation_scans.txt").write_text(
        "".join(f"{scan_id}\n" for scan_id in manifest["roles"]["validation"]["scan_ids"]),
        encoding="utf-8",
    )
    (output_dir / "scans.txt").write_text(
        "\n".join(
            [
                "# train",
                *manifest["roles"]["train"]["scan_ids"],
                "# dev",
                *manifest["roles"]["dev"]["scan_ids"],
                "# validation",
                *manifest["roles"]["validation"]["scan_ids"],
                "",
            ]
        ),
        encoding="utf-8",
    )
    write_jsonl(output_dir / "candidates.jsonl", candidates)
    write_jsonl(output_dir / "subgraphs.jsonl", selected_subgraph_rows(selected_all))
    (output_dir / "report.md").write_text(make_report(manifest), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "train_scans": len(selected_train),
                "dev_scans": len(selected_dev),
                "validation_scans": len(validation_scan_ids),
                "group_conflicts": len(group_conflicts),
                "output_dir": str(output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if manifest["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
