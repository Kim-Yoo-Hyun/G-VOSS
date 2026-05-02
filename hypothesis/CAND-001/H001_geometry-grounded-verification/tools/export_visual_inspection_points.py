#!/usr/bin/env python3
"""Export small colored PLY files for H001 visual inspection cases."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROLE_COLORS = {
    "subject": (235, 80, 65),
    "object_context": (80, 135, 245),
    "local_support": (245, 205, 65),
}

ROLE_IDS = {
    "subject": 1,
    "object_context": 2,
    "local_support": 3,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export colored PLY point subsets for H001 visual inspection."
    )
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    parser.add_argument("--queue", default="visual_inspection_queue.jsonl")
    parser.add_argument("--output-dir", default="visual_inspection")
    parser.add_argument("--local-expansion-m", default=0.20, type=float)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "case"


def parse_ply_header(path: Path) -> tuple[dict[str, Any], int]:
    properties: list[str] = []
    vertex_count: int | None = None
    face_count: int | None = None
    header_lines = 0
    in_vertex = False
    with path.open("r", encoding="utf-8", errors="replace") as f:
        first_line = f.readline().strip()
        header_lines += 1
        if first_line != "ply":
            raise ValueError(f"expected ply header, found {first_line!r}")
        for line in f:
            header_lines += 1
            stripped = line.strip()
            if stripped.startswith("format") and stripped != "format ascii 1.0":
                raise ValueError(f"unsupported_ply_format:{stripped}")
            if stripped.startswith("element vertex"):
                vertex_count = int(stripped.split()[-1])
                in_vertex = True
            elif stripped.startswith("element face"):
                face_count = int(stripped.split()[-1])
                in_vertex = False
            elif stripped.startswith("property") and in_vertex:
                properties.append(stripped.split()[-1])
            elif stripped == "end_header":
                break
    if vertex_count is None:
        raise ValueError("missing_vertex_count")
    return {
        "vertex_count": vertex_count,
        "face_count": face_count,
        "properties": properties,
    }, header_lines


def load_points_by_object(path: Path, object_ids: set[int]) -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
    header, _ = parse_ply_header(path)
    properties = header["properties"]
    for required in ("x", "y", "z", "red", "green", "blue", "objectId"):
        if required not in properties:
            raise ValueError(f"missing_ply_property:{required}")

    idx = {name: properties.index(name) for name in properties}
    max_idx = max(idx[name] for name in ("x", "y", "z", "red", "green", "blue", "objectId"))
    points: dict[int, list[dict[str, Any]]] = {object_id: [] for object_id in object_ids}
    rows_read = 0
    rows_kept = 0

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip() == "end_header":
                break
        for _ in range(int(header["vertex_count"])):
            line = f.readline()
            if not line:
                break
            rows_read += 1
            parts = line.split()
            if len(parts) <= max_idx:
                continue
            object_id = int(parts[idx["objectId"]])
            if object_id not in object_ids:
                continue
            points[object_id].append(
                {
                    "x": float(parts[idx["x"]]),
                    "y": float(parts[idx["y"]]),
                    "z": float(parts[idx["z"]]),
                    "source_rgb": (
                        int(parts[idx["red"]]),
                        int(parts[idx["green"]]),
                        int(parts[idx["blue"]]),
                    ),
                    "object_id": object_id,
                }
            )
            rows_kept += 1

    stats = {
        "ply_vertex_count_header": header["vertex_count"],
        "ply_face_count_header": header["face_count"],
        "ply_vertex_rows_read": rows_read,
        "target_vertex_rows_kept": rows_kept,
        "target_object_ids": sorted(object_ids),
    }
    return points, stats


def percentile(sorted_values: list[float], pct: float) -> float | None:
    if not sorted_values:
        return None
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = (len(sorted_values) - 1) * pct / 100.0
    low = int(pos)
    high = min(low + 1, len(sorted_values) - 1)
    frac = pos - low
    return sorted_values[low] * (1.0 - frac) + sorted_values[high] * frac


def axis_stats(points: list[dict[str, Any]], key: str, percentiles: tuple[int, ...]) -> dict[str, float | None]:
    values = sorted(float(point[key]) for point in points)
    if not values:
        return {"min": None, "max": None} | {f"p{pct:02d}": None for pct in percentiles}
    stats: dict[str, float | None] = {"min": values[0], "max": values[-1]}
    for pct in percentiles:
        stats[f"p{pct:02d}"] = percentile(values, pct)
    return stats


def object_stats(points: list[dict[str, Any]]) -> dict[str, Any]:
    x = axis_stats(points, "x", (5, 95))
    y = axis_stats(points, "y", (5, 95))
    z = axis_stats(points, "z", (1, 5, 50, 95, 99))
    return {
        "point_count": len(points),
        "x_min": x["min"],
        "x_max": x["max"],
        "x_p05": x["p05"],
        "x_p95": x["p95"],
        "y_min": y["min"],
        "y_max": y["max"],
        "y_p05": y["p05"],
        "y_p95": y["p95"],
        "z_min": z["min"],
        "z_max": z["max"],
        "z_p01": z["p01"],
        "z_p05": z["p05"],
        "z_p50": z["p50"],
        "z_p95": z["p95"],
        "z_p99": z["p99"],
    }


def is_local_support_point(
    point: dict[str, Any],
    subject_stats: dict[str, Any],
    expansion: float,
) -> bool:
    required = ("x_p05", "x_p95", "y_p05", "y_p95")
    if any(subject_stats.get(key) is None for key in required):
        return False
    return (
        float(subject_stats["x_p05"]) - expansion
        <= float(point["x"])
        <= float(subject_stats["x_p95"]) + expansion
        and float(subject_stats["y_p05"]) - expansion
        <= float(point["y"])
        <= float(subject_stats["y_p95"]) + expansion
    )


def make_case_filename(record: dict[str, Any]) -> str:
    relation = f"{record['subject_label']}_{record['predicate_label']}_{record['object_label']}"
    return f"{record['inspection_id']}_{slugify(relation)}.ply"


def write_case_ply(
    path: Path,
    subject_points: list[dict[str, Any]],
    object_points: list[dict[str, Any]],
    subject_stats: dict[str, Any],
    expansion: float,
) -> dict[str, int]:
    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()

    for point in subject_points:
        rows.append({**point, "role": "subject"})
        counts["subject"] += 1

    for point in object_points:
        role = "local_support" if is_local_support_point(point, subject_stats, expansion) else "object_context"
        rows.append({**point, "role": role})
        counts[role] += 1

    with path.open("w", encoding="utf-8") as f:
        f.write("ply\n")
        f.write("format ascii 1.0\n")
        f.write(f"comment H001 visual inspection subset: {path.name}\n")
        f.write("comment color roles: subject=red, object_context=blue, local_support=yellow\n")
        f.write(f"element vertex {len(rows)}\n")
        f.write("property float x\n")
        f.write("property float y\n")
        f.write("property float z\n")
        f.write("property uchar red\n")
        f.write("property uchar green\n")
        f.write("property uchar blue\n")
        f.write("property ushort objectId\n")
        f.write("property uchar roleId\n")
        f.write("end_header\n")
        for row in rows:
            red, green, blue = ROLE_COLORS[row["role"]]
            f.write(
                f"{row['x']:.6f} {row['y']:.6f} {row['z']:.6f} "
                f"{red} {green} {blue} {row['object_id']} {ROLE_IDS[row['role']]}\n"
            )

    return {
        "total_points": len(rows),
        "subject_points": counts["subject"],
        "object_context_points": counts["object_context"],
        "local_support_points": counts["local_support"],
    }


def labels_template(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "inspection_id": record["inspection_id"],
            "edge_id": record["edge_id"],
            "relation_visually_plausible": None,
            "local_surface_correct": None,
            "segmentation_or_instance_issue": None,
            "rule_subtype_needed": None,
            "inspection_label": None,
            "note": "",
        }
        for record in records
    ]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Visual Inspection Artifacts",
        "",
        f"Created at: `{summary['created_at']}`",
        f"Scan id: `{summary['scan_id']}`",
        "",
        "## Role",
        "",
        "These files prepare the selected v1 review cases for manual visual inspection.",
        "They are point-subset artifacts, not benchmark evidence.",
        "",
        "## Color Legend",
        "",
        "| Role | Color | Meaning |",
        "| --- | --- | --- |",
        "| subject | red | Relation subject object points |",
        "| object_context | blue | Relation object/support points outside the local footprint |",
        "| local_support | yellow | Relation object/support points under the subject footprint with expansion |",
        "",
        "## Cases",
        "",
        "| ID | Relation | Triage | PLY | Points |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for case in summary["cases"]:
        relation = (
            f"{case['subject_label']} --{case['predicate_label']}--> "
            f"{case['object_label']}"
        )
        points = case["point_counts"]["total_points"]
        lines.append(
            f"| `{case['inspection_id']}` | `{relation}` | "
            f"`{case['triage_label']}` | `{case['ply_file']}` | {points} |"
        )
    lines.extend(
        [
            "",
            "## Inspection Questions",
            "",
            "- Is the relation visually plausible?",
            "- Is the local support surface selected correctly?",
            "- Is there a segmentation or instance geometry issue?",
            "- Does this relation need a separate rule subtype?",
            "",
            "## Outputs To Fill",
            "",
            "`template.jsonl` contains empty labels for the selected cases.",
            "After inspection, fill or copy it to `labels.jsonl`.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    artifact_dir = args.artifact_dir
    queue_path = artifact_dir / args.queue
    records = read_jsonl(queue_path)
    if not records:
        raise ValueError(f"empty_queue:{queue_path}")

    scan_ids = {record["scan_id"] for record in records}
    if len(scan_ids) != 1:
        raise ValueError(f"expected_single_scan_id:{sorted(scan_ids)}")
    scan_id = next(iter(scan_ids))

    ply_path = args.dataset_root / "3RScan" / "scans" / scan_id / "labels.instances.annotated.v2.ply"
    object_ids = {
        int(record["subject_id"]) for record in records
    } | {
        int(record["object_id"]) for record in records
    }
    points_by_object, ply_stats = load_points_by_object(ply_path, object_ids)

    output_dir = artifact_dir / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    cases: list[dict[str, Any]] = []
    errors: list[str] = []
    for record in records:
        subject_id = int(record["subject_id"])
        object_id = int(record["object_id"])
        subject_points = points_by_object.get(subject_id, [])
        object_points = points_by_object.get(object_id, [])
        if not subject_points:
            errors.append(f"missing_subject_points:{record['inspection_id']}:{subject_id}")
        if not object_points:
            errors.append(f"missing_object_points:{record['inspection_id']}:{object_id}")

        stats = object_stats(subject_points)
        ply_name = make_case_filename(record)
        point_counts = write_case_ply(
            output_dir / ply_name,
            subject_points,
            object_points,
            stats,
            args.local_expansion_m,
        )
        cases.append(
            {
                **record,
                "ply_file": ply_name,
                "point_counts": point_counts,
                "local_expansion_m": args.local_expansion_m,
                "subject_point_stats": stats,
            }
        )

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "script_name": Path(__file__).name,
        "scan_id": scan_id,
        "artifact_dir": str(artifact_dir),
        "output_dir": str(output_dir),
        "source_ply": str(ply_path),
        "queue_path": str(queue_path),
        "local_expansion_m": args.local_expansion_m,
        "case_count": len(cases),
        "cases": cases,
        "ply_stats": ply_stats,
        "validation": {
            "passed": not errors,
            "errors": errors,
            "warnings": [
                "visual_inspection_artifacts_are_qualitative_not_benchmark_evidence"
            ],
        },
        "output_paths": {
            "summary": str(output_dir / "summary.json"),
            "report": str(output_dir / "README.md"),
            "labels_template": str(output_dir / "template.jsonl"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "template.jsonl", labels_template(records))
    write_report(output_dir / "README.md", summary)

    if errors:
        raise SystemExit(f"validation_failed:{errors}")


if __name__ == "__main__":
    main()
