#!/usr/bin/env python3
"""Select H001-Mini validation scans from official 3DSSG_subset."""

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

PAYLOAD_FILES = [
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
    "sequence.zip",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select a small validation scan set for H001 support/contact evaluation."
    )
    parser.add_argument(
        "--subset-root",
        type=Path,
        default=REPO_ROOT / "local_dataset" / "3DSSG_subset",
        help="Path to local 3DSSG_subset.",
    )
    parser.add_argument(
        "--rscan-root",
        type=Path,
        default=REPO_ROOT / "local_dataset" / "3RScan",
        help="Path to local 3RScan root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=H001_ROOT / "artifacts" / "subset" / "h001_mini",
        help="Output artifact directory.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=8,
        help="Number of validation scans to select.",
    )
    parser.add_argument(
        "--min-scan-support",
        type=int,
        default=15,
        help="Minimum scan-level support/contact edge count.",
    )
    parser.add_argument(
        "--min-subgraph-support",
        type=int,
        default=5,
        help="Minimum support/contact edge count in at least one subgraph.",
    )
    parser.add_argument(
        "--updated",
        default="2026-05-03",
        help="Date string written into reports.",
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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


def payload_status(scan_dir: Path) -> dict[str, Any]:
    files = {name: (scan_dir / name).exists() for name in PAYLOAD_FILES}
    sequence_dir = scan_dir / "sequence"
    multi_view_dir = scan_dir / "multi_view"
    status = {
        "scan_dir_exists": scan_dir.exists(),
        "files": files,
        "sequence_dir_exists": sequence_dir.is_dir(),
        "aligned_ply_exists": (scan_dir / "labels.instances.align.annotated.v2.ply").exists(),
        "multi_view_dir_exists": multi_view_dir.is_dir(),
        "multi_view_file_count": (
            len(list(multi_view_dir.glob("*.npy"))) if multi_view_dir.is_dir() else 0
        ),
    }
    status["payload_ready_for_download_stage"] = all(files[name] for name in PAYLOAD_FILES[:3]) and (
        files["sequence.zip"] or status["sequence_dir_exists"]
    )
    return status


def summarize_scan_entries(scans: list[dict[str, Any]], scan_groups: dict[str, dict[str, Any]], rscan_root: Path) -> list[dict[str, Any]]:
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

    for entry in scans:
        scan_id = str(entry["scan"])
        relationships = entry.get("relationships", [])
        family_counts, label_counts = relation_counts(relationships)
        subgraph_score = (
            family_counts["support_contact"]
            + 0.25 * family_counts["proximity"]
            + 0.25 * family_counts["relative_vertical"]
        )
        objects = entry.get("objects", {})
        record = by_scan[scan_id]
        record["entry_count"] += 1
        record["relationship_count"] += len(relationships)
        record["object_labels"].update(str(value) for value in objects.values())
        record["family_counts"].update(family_counts)
        record["label_counts"].update(label_counts)
        record["subgraphs"].append(
            {
                "split": entry.get("split"),
                "relationship_count": len(relationships),
                "object_count": len(objects),
                "family_counts": {key: family_counts.get(key, 0) for key in FAMILY_ORDER},
                "score": subgraph_score,
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
        scan_dir = rscan_root / "scans" / scan_id
        rows.append(
            {
                "scan_id": scan_id,
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
                    subgraph["family_counts"]["support_contact"] for subgraph in record["subgraphs"]
                ),
                "score": score,
                "subgraphs": sorted(
                    record["subgraphs"],
                    key=lambda item: (item["score"], item["family_counts"]["support_contact"]),
                    reverse=True,
                ),
                "payload_status": payload_status(scan_dir),
            }
        )
    return rows


def candidate_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    family_counts = row["family_counts"]
    return (
        row["score"],
        family_counts["support_contact"],
        family_counts["relative_vertical"],
        family_counts["proximity"],
        row["relationship_count"],
        row["entry_count"],
        row["scan_id"],
    )


def select_scans(
    rows: list[dict[str, Any]], limit: int, min_scan_support: int, min_subgraph_support: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    selected_groups: set[str] = set()
    annotated: list[dict[str, Any]] = []

    for rank, row in enumerate(sorted(rows, key=candidate_sort_key, reverse=True), start=1):
        reason = "not_selected_after_limit"
        is_selected = False
        if row["family_counts"]["support_contact"] < min_scan_support:
            reason = "below_min_scan_support"
        elif row["max_subgraph_support_contact"] < min_subgraph_support:
            reason = "below_min_subgraph_support"
        elif row["group_reference"] in selected_groups:
            reason = "duplicate_3rscan_group"
        elif len(selected) < limit:
            reason = "selected"
            is_selected = True
            selected_groups.add(row["group_reference"])
            selected.append(row)
        row_with_status = dict(row)
        row_with_status["candidate_rank"] = rank
        row_with_status["selected"] = is_selected
        row_with_status["selection_reason"] = reason
        annotated.append(row_with_status)

    selected_ids = {row["scan_id"] for row in selected}
    for index, row in enumerate(selected, start=1):
        row["selected_rank"] = index
        row["selected"] = True
        row["selection_reason"] = "selected"
    for row in annotated:
        if row["scan_id"] in selected_ids:
            row["selected_rank"] = next(
                selected_row["selected_rank"]
                for selected_row in selected
                if selected_row["scan_id"] == row["scan_id"]
            )
    return selected, annotated


def total_family_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row["family_counts"])
    return {key: counts.get(key, 0) for key in FAMILY_ORDER}


def report_lines(manifest: dict[str, Any], selected: list[dict[str, Any]], candidates: list[dict[str, Any]]) -> list[str]:
    selected_totals = manifest["selected_totals"]
    lines = [
        "# H001-Mini Scan Selection",
        "",
        f"Last updated: {manifest['updated']}",
        "",
        "This artifact fixes the first H001-Mini validation scan list before any `VL-SAT` prediction failures are inspected.",
        "",
        "## Selection Policy",
        "",
        "- Source split: official `3DSSG_subset` validation split.",
        "- Primary target: `support_contact` relation coverage.",
        "- Secondary coverage: `proximity` and `relative_vertical`.",
        "- Duplicate control: select at most one scan per 3RScan reference/rescan group.",
        "- Score: `support_contact + 0.25 * proximity + 0.25 * relative_vertical`.",
        "",
        "## Parameters",
        "",
        f"- selected scans: {len(selected)}",
        f"- candidate scans: {manifest['candidate_scan_count']}",
        f"- min scan-level support/contact: {manifest['parameters']['min_scan_support']}",
        f"- min best-subgraph support/contact: {manifest['parameters']['min_subgraph_support']}",
        "",
        "## Selected Scans",
        "",
        "| Rank | Scan | Group | Score | Entries | Relations | Objects | Support/contact | Proximity | Vertical | Attachment | Local payload |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in selected:
        family_counts = row["family_counts"]
        payload = row["payload_status"]
        payload_label = "ready" if payload["payload_ready_for_download_stage"] else "missing"
        lines.append(
            "| {rank} | `{scan}` | `{group}` | {score:.2f} | {entries} | {relations} | {objects} | {support} | {proximity} | {vertical} | {attachment} | {payload} |".format(
                rank=row["selected_rank"],
                scan=row["scan_id"],
                group=row["group_reference"],
                score=row["score"],
                entries=row["entry_count"],
                relations=row["relationship_count"],
                objects=row["object_label_count"],
                support=family_counts["support_contact"],
                proximity=family_counts["proximity"],
                vertical=family_counts["relative_vertical"],
                attachment=family_counts["attachment_deferred"],
                payload=payload_label,
            )
        )
    lines.extend(
        [
            "",
            "## Coverage Totals",
            "",
            f"- entries: {selected_totals['entry_count']}",
            f"- relationships: {selected_totals['relationship_count']}",
            f"- support/contact: {selected_totals['family_counts']['support_contact']}",
            f"- proximity: {selected_totals['family_counts']['proximity']}",
            f"- relative vertical: {selected_totals['family_counts']['relative_vertical']}",
            f"- deferred attachment/contact: {selected_totals['family_counts']['attachment_deferred']}",
            "",
            "## Payload Status",
            "",
            "Current local payload status is checked only under `local_dataset/3RScan/scans/<scan_id>/`.",
            "",
            "Required per selected scan:",
            "",
            "```text",
            "labels.instances.annotated.v2.ply",
            "semseg.v2.json",
            "mesh.refined.0.010000.segs.v2.json",
            "sequence.zip",
            "```",
            "",
            "Download pattern:",
            "",
            "```text",
            "python local_dataset/3RScan/download_3rscan.py -o local_dataset/3RScan/scans --id <scan_id> --type <file_type>",
            "```",
            "",
            "## Candidate Files",
            "",
            "- `manifest.json`: selected list, parameters, totals, payload status.",
            "- `scans.txt`: selected scan ids for download/prep scripts.",
            "- `candidates.jsonl`: all validation scan candidates with selection reason.",
            "- `subgraphs.jsonl`: selected subgraph summaries.",
            "",
            "## Next",
            "",
            "1. Download or stage required payloads for the selected scan ids.",
            "2. Implement staged-root prep for `VL-SAT` annotations, scan files, `references.txt`, and `rescans.txt`.",
            "3. Generate aligned PLY for selected scans.",
            "4. Generate `multi_view` features for selected scans.",
        ]
    )

    duplicate_skips = [
        row
        for row in candidates
        if row["selection_reason"] == "duplicate_3rscan_group"
    ][:5]
    if duplicate_skips:
        lines.extend(["", "## Duplicate Group Skips", ""])
        for row in duplicate_skips:
            lines.append(
                "- `{scan}` skipped because group `{group}` was already selected.".format(
                    scan=row["scan_id"], group=row["group_reference"]
                )
            )
    return lines


def main() -> None:
    args = parse_args()
    validation_path = args.subset_root / "relationships_validation.json"
    rscan_json_path = args.rscan_root / "files" / "3RScan.json"

    validation = load_json(validation_path)
    scans = validation["scans"]
    scan_groups = build_scan_groups(rscan_json_path)
    rows = summarize_scan_entries(scans, scan_groups, args.rscan_root)
    selected, candidates = select_scans(
        rows,
        limit=args.limit,
        min_scan_support=args.min_scan_support,
        min_subgraph_support=args.min_subgraph_support,
    )

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    selected_totals = {
        "entry_count": sum(row["entry_count"] for row in selected),
        "relationship_count": sum(row["relationship_count"] for row in selected),
        "family_counts": total_family_counts(selected),
    }
    manifest = {
        "updated": args.updated,
        "source": {
            "subset_root": str(args.subset_root),
            "validation_file": str(validation_path),
            "rscan_json": str(rscan_json_path),
        },
        "parameters": {
            "limit": args.limit,
            "min_scan_support": args.min_scan_support,
            "min_subgraph_support": args.min_subgraph_support,
            "score_formula": "support_contact + 0.25 * proximity + 0.25 * relative_vertical",
            "duplicate_policy": "at most one selected scan per 3RScan reference/rescan group",
        },
        "candidate_scan_count": len(rows),
        "validation_subgraph_count": len(scans),
        "selected_scan_count": len(selected),
        "selected_totals": selected_totals,
        "selected_scans": selected,
    }

    write_json(output_dir / "manifest.json", manifest)
    (output_dir / "scans.txt").write_text(
        "".join(f"{row['scan_id']}\n" for row in selected), encoding="utf-8"
    )
    with (output_dir / "candidates.jsonl").open("w", encoding="utf-8") as handle:
        for row in candidates:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
    with (output_dir / "subgraphs.jsonl").open("w", encoding="utf-8") as handle:
        for row in selected:
            for subgraph in row["subgraphs"]:
                payload = {
                    "scan_id": row["scan_id"],
                    "selected_rank": row["selected_rank"],
                    "split": subgraph["split"],
                    "relationship_count": subgraph["relationship_count"],
                    "object_count": subgraph["object_count"],
                    "family_counts": subgraph["family_counts"],
                    "score": subgraph["score"],
                }
                handle.write(json.dumps(payload, sort_keys=True) + "\n")
    (output_dir / "report.md").write_text(
        "\n".join(report_lines(manifest, selected, candidates)) + "\n", encoding="utf-8"
    )

    print(f"selected_scans={len(selected)}")
    print(f"candidate_scans={len(rows)}")
    print(f"output_dir={output_dir}")


if __name__ == "__main__":
    main()
