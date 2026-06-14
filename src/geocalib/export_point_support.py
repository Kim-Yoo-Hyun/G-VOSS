#!/usr/bin/env python3
"""Export PLY point-level support/contact evidence for H001.

Phase C smoke test: compare OBB-only support/contact decisions against
point/local-surface evidence from labels.instances.annotated.v2.ply.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_POINT_THRESHOLDS = {
    "point_rule_version": "ply_points_v1",
    "local_vertical_gap_abs_max_m": 0.10,
    "local_vertical_gap_abs_relaxed_m": 0.15,
    "min_support_points_under_subject": 10,
    "max_expansion_for_primary_m": 0.10,
    "xy_expansion_steps_m": [0.00, 0.05, 0.10, 0.20],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export point-level support/contact evidence for one H001 scan."
    )
    parser.add_argument("--scan-id", required=True)
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--artifact-dir", required=True, type=Path)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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
            if stripped.startswith("format"):
                if stripped != "format ascii 1.0":
                    raise ValueError(f"unsupported_ply_format:{stripped}")
            elif stripped.startswith("element vertex"):
                vertex_count = int(stripped.split()[-1])
                in_vertex = True
            elif stripped.startswith("element face"):
                face_count = int(stripped.split()[-1])
                in_vertex = False
            elif stripped.startswith("property") and in_vertex:
                parts = stripped.split()
                properties.append(parts[-1])
            elif stripped == "end_header":
                break
    if vertex_count is None:
        raise ValueError("missing_vertex_count")
    return {
        "vertex_count": vertex_count,
        "face_count": face_count,
        "properties": properties,
    }, header_lines


def read_target_points(
    path: Path,
    target_object_ids: set[int],
) -> tuple[dict[int, dict[str, list[float]]], dict[str, Any]]:
    header, _header_lines = parse_ply_header(path)
    properties = header["properties"]
    for required in ("x", "y", "z", "objectId"):
        if required not in properties:
            raise ValueError(f"missing_ply_property:{required}")

    x_idx = properties.index("x")
    y_idx = properties.index("y")
    z_idx = properties.index("z")
    object_id_idx = properties.index("objectId")

    points: dict[int, dict[str, list[float]]] = {
        object_id: {"x": [], "y": [], "z": []} for object_id in target_object_ids
    }
    rows_read = 0
    rows_kept = 0
    max_idx = max(x_idx, y_idx, z_idx, object_id_idx)

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
            object_id = int(parts[object_id_idx])
            if object_id not in target_object_ids:
                continue
            points[object_id]["x"].append(float(parts[x_idx]))
            points[object_id]["y"].append(float(parts[y_idx]))
            points[object_id]["z"].append(float(parts[z_idx]))
            rows_kept += 1

    stats = {
        "ply_vertex_count_header": header["vertex_count"],
        "ply_face_count_header": header["face_count"],
        "ply_vertex_rows_read": rows_read,
        "target_object_ids": sorted(target_object_ids),
        "target_vertex_rows_kept": rows_kept,
        "properties": properties,
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


def axis_stats(values: list[float], percentiles: tuple[int, ...]) -> dict[str, float | None]:
    if not values:
        return {f"p{pct:02d}": None for pct in percentiles} | {"min": None, "max": None}
    sorted_values = sorted(values)
    stats: dict[str, float | None] = {
        "min": sorted_values[0],
        "max": sorted_values[-1],
    }
    for pct in percentiles:
        stats[f"p{pct:02d}"] = percentile(sorted_values, pct)
    return stats


def compute_object_stats(points: dict[str, list[float]]) -> dict[str, Any]:
    x_stats = axis_stats(points["x"], (5, 95))
    y_stats = axis_stats(points["y"], (5, 95))
    z_stats = axis_stats(points["z"], (1, 5, 50, 95, 99))

    def area(x_key_low: str, x_key_high: str, y_key_low: str, y_key_high: str) -> float | None:
        x_low = x_stats[x_key_low]
        x_high = x_stats[x_key_high]
        y_low = y_stats[y_key_low]
        y_high = y_stats[y_key_high]
        if None in (x_low, x_high, y_low, y_high):
            return None
        return max(0.0, float(x_high) - float(x_low)) * max(0.0, float(y_high) - float(y_low))

    return {
        "point_count": len(points["x"]),
        "x_min": x_stats["min"],
        "x_max": x_stats["max"],
        "y_min": y_stats["min"],
        "y_max": y_stats["max"],
        "z_min": z_stats["min"],
        "z_max": z_stats["max"],
        "x_p05": x_stats["p05"],
        "x_p95": x_stats["p95"],
        "y_p05": y_stats["p05"],
        "y_p95": y_stats["p95"],
        "z_p01": z_stats["p01"],
        "z_p05": z_stats["p05"],
        "z_p50": z_stats["p50"],
        "z_p95": z_stats["p95"],
        "z_p99": z_stats["p99"],
        "xy_footprint_area_p05_p95": area("p05", "p95", "p05", "p95"),
        "xy_footprint_area_min_max": area("min", "max", "min", "max"),
    }


def local_support_stats(
    subject_stats: dict[str, Any],
    support_points: dict[str, list[float]],
    thresholds: dict[str, Any],
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if any(subject_stats.get(key) is None for key in ("x_p05", "x_p95", "y_p05", "y_p95")):
        return results

    for expansion in thresholds["xy_expansion_steps_m"]:
        x_min = float(subject_stats["x_p05"]) - float(expansion)
        x_max = float(subject_stats["x_p95"]) + float(expansion)
        y_min = float(subject_stats["y_p05"]) - float(expansion)
        y_max = float(subject_stats["y_p95"]) + float(expansion)
        local_z: list[float] = []
        for x, y, z in zip(support_points["x"], support_points["y"], support_points["z"]):
            if x_min <= x <= x_max and y_min <= y <= y_max:
                local_z.append(z)
        local_z_sorted = sorted(local_z)
        support_z_p50 = percentile(local_z_sorted, 50)
        support_z_p95 = percentile(local_z_sorted, 95)
        support_z_p99 = percentile(local_z_sorted, 99)
        subject_z_p05 = subject_stats.get("z_p05")
        subject_z_p01 = subject_stats.get("z_p01")
        gap_p05_p95 = (
            float(subject_z_p05) - float(support_z_p95)
            if subject_z_p05 is not None and support_z_p95 is not None
            else None
        )
        gap_p01_p99 = (
            float(subject_z_p01) - float(support_z_p99)
            if subject_z_p01 is not None and support_z_p99 is not None
            else None
        )
        results.append(
            {
                "xy_expansion_m": expansion,
                "support_points_under_subject_count": len(local_z),
                "support_points_under_subject_z_p50": support_z_p50,
                "support_points_under_subject_z_p95": support_z_p95,
                "support_points_under_subject_z_p99": support_z_p99,
                "local_vertical_gap_p05_p95": gap_p05_p95,
                "local_vertical_gap_p01_p99": gap_p01_p99,
            }
        )
    return results


def assign_point_status(
    local_evidence: list[dict[str, Any]],
    thresholds: dict[str, Any],
) -> tuple[str, list[str], dict[str, Any] | None]:
    min_points = int(thresholds["min_support_points_under_subject"])
    max_primary_expansion = float(thresholds["max_expansion_for_primary_m"])
    max_gap = float(thresholds["local_vertical_gap_abs_max_m"])
    relaxed_gap = float(thresholds["local_vertical_gap_abs_relaxed_m"])

    enough_points = [
        record
        for record in local_evidence
        if int(record["support_points_under_subject_count"]) >= min_points
        and record["local_vertical_gap_p05_p95"] is not None
    ]
    if not enough_points:
        return "point_uncertain", ["sparse_local_support_points"], None

    best = enough_points[0]
    gap = abs(float(best["local_vertical_gap_p05_p95"]))
    expansion = float(best["xy_expansion_m"])
    if expansion <= max_primary_expansion and gap <= max_gap:
        return "point_satisfied", ["local_support_gap_within_threshold"], best
    if expansion <= max_primary_expansion and gap <= relaxed_gap:
        return "point_uncertain", ["local_support_gap_relaxed_band"], best
    if expansion > max_primary_expansion and gap <= max_gap:
        return "point_uncertain", ["support_points_only_after_large_expansion"], best
    return "point_violated", ["local_support_gap_too_large"], best


def transition(old_status: str, point_status: str) -> str:
    return f"obb_{old_status}_to_{point_status}"


def manual_labels_by_edge(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(record["edge_id"]): record for record in records}


def make_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Point Support Evidence",
        "",
        f"Created at: `{summary['created_at']}`",
        f"Scan id: `{summary['scan_id']}`",
        f"Point rule version: `{summary['point_rule_version']}`",
        "",
        "## Validation",
        "",
        f"- Passed: `{summary['validation']['passed']}`",
        f"- Errors: `{len(summary['validation']['errors'])}`",
        f"- Warnings: `{len(summary['validation']['warnings'])}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in summary["counts"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Point Status Counts", ""])
    for key, value in summary["point_status_counts"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Status Transitions", ""])
    for key, value in summary["status_transition_counts"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Manual Label To Point Status", ""])
    for label, counts in summary["manual_label_to_point_status_counts"].items():
        text = ", ".join(f"{status}={count}" for status, count in counts.items())
        lines.append(f"- `{label}`: {text}")

    lines.extend(["", "## Headline Metrics", ""])
    for key, value in summary["headline_metrics"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a support/contact smoke test, not benchmark evidence.",
            "- The key question is whether point/local-surface evidence recovers OBB-only support/contact failures.",
            "- If many floor-support edges remain uncertain, the next refinement should use a stronger local plane or support surface estimator.",
            "",
            "## Next Action",
            "",
            "Compare `point_comparison.jsonl` against the OBB-only verifier output and decide whether to revise the support/contact rule.",
            "",
        ]
    )
    return "\n".join(lines)


def count_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: value for key, value in sorted(counter.items())}


def nested_count_dict(counter: dict[str, Counter[str]]) -> dict[str, dict[str, int]]:
    return {key: count_dict(value) for key, value in sorted(counter.items())}


def main() -> int:
    args = parse_args()
    scan_id = args.scan_id
    artifact_dir = args.artifact_dir
    ply_path = (
        args.dataset_root
        / "3RScan"
        / "scans"
        / scan_id
        / "labels.instances.annotated.v2.ply"
    )
    paths = {
        "ply": ply_path,
        "decisions": artifact_dir / "decisions.jsonl",
        "manual_labels": artifact_dir / "review_labels.jsonl",
        "thresholds": artifact_dir / "thresholds.json",
        "phase_a_summary": artifact_dir / "export_summary.json",
    }
    missing = [f"{name}:{path}" for name, path in paths.items() if not path.exists()]
    if missing:
        raise SystemExit("missing_input_file:" + ",".join(missing))

    thresholds = dict(DEFAULT_POINT_THRESHOLDS)
    thresholds["source_threshold_config"] = load_json(paths["thresholds"])
    phase_a_summary = load_json(paths["phase_a_summary"])
    verifier_records = read_jsonl(paths["decisions"])
    manual_labels = manual_labels_by_edge(read_jsonl(paths["manual_labels"]))
    support_edges = [
        record for record in verifier_records if record.get("predicate_family") == "support_contact"
    ]
    target_object_ids = {
        int(endpoint)
        for record in support_edges
        for endpoint in (record["subject_id"], record["object_id"])
    }

    points_by_object, ply_stats = read_target_points(ply_path, target_object_ids)
    object_stats = {
        object_id: compute_object_stats(points)
        for object_id, points in sorted(points_by_object.items())
    }

    missing_point_object_ids = [
        object_id
        for object_id in sorted(target_object_ids)
        if object_stats.get(object_id, {}).get("point_count", 0) == 0
    ]

    evidence_records: list[dict[str, Any]] = []
    comparison_records: list[dict[str, Any]] = []
    for edge in support_edges:
        subject_id = int(edge["subject_id"])
        object_id = int(edge["object_id"])
        subject_stats = object_stats.get(subject_id, {})
        object_point_group = points_by_object.get(object_id, {"x": [], "y": [], "z": []})
        object_stats_record = object_stats.get(object_id, {})
        local_evidence = []
        point_status = "point_uncertain"
        point_reason_codes = ["missing_endpoint_points"]
        best_local_evidence = None
        if subject_stats.get("point_count", 0) and object_stats_record.get("point_count", 0):
            local_evidence = local_support_stats(subject_stats, object_point_group, thresholds)
            point_status, point_reason_codes, best_local_evidence = assign_point_status(
                local_evidence, thresholds
            )

        manual_label = manual_labels.get(edge["edge_id"], {})
        old_status = edge["verification"]["status"]
        point_evidence_available = best_local_evidence is not None
        evidence_record = {
            "edge_id": edge["edge_id"],
            "scan_id": scan_id,
            "subject_id": subject_id,
            "object_id": object_id,
            "subject_label": edge.get("subject_label"),
            "predicate_label": edge.get("predicate_label"),
            "object_label": edge.get("object_label"),
            "point_rule_version": thresholds["point_rule_version"],
            "old_status": old_status,
            "old_reason_codes": edge["verification"].get("reason_codes", []),
            "manual_review_label": manual_label.get("review_label"),
            "subject_point_stats": subject_stats,
            "object_point_stats": object_stats_record,
            "local_support_evidence": local_evidence,
            "point_status": point_status,
            "point_reason_codes": point_reason_codes,
            "best_local_support_evidence": best_local_evidence,
            "point_evidence_available": point_evidence_available,
        }
        evidence_records.append(evidence_record)

        comparison_records.append(
            {
                "edge_id": edge["edge_id"],
                "subject_label": edge.get("subject_label"),
                "predicate_label": edge.get("predicate_label"),
                "object_label": edge.get("object_label"),
                "old_status": old_status,
                "old_reason_codes": edge["verification"].get("reason_codes", []),
                "manual_review_label": manual_label.get("review_label"),
                "point_status": point_status,
                "point_reason_codes": point_reason_codes,
                "status_transition": transition(old_status, point_status),
                "subject_point_count": subject_stats.get("point_count", 0),
                "object_point_count": object_stats_record.get("point_count", 0),
                "best_expansion_m": (
                    best_local_evidence.get("xy_expansion_m") if best_local_evidence else None
                ),
                "support_points_under_subject_count": (
                    best_local_evidence.get("support_points_under_subject_count")
                    if best_local_evidence
                    else None
                ),
                "local_vertical_gap_p05_p95": (
                    best_local_evidence.get("local_vertical_gap_p05_p95")
                    if best_local_evidence
                    else None
                ),
                "local_vertical_gap_p01_p99": (
                    best_local_evidence.get("local_vertical_gap_p01_p99")
                    if best_local_evidence
                    else None
                ),
                "point_evidence_available": point_evidence_available,
            }
        )

    point_status_counts = Counter(record["point_status"] for record in evidence_records)
    transition_counts = Counter(record["status_transition"] for record in comparison_records)
    manual_to_point: dict[str, Counter[str]] = defaultdict(Counter)
    for record in comparison_records:
        label = record["manual_review_label"] or "not_in_manual_review"
        manual_to_point[label][record["point_status"]] += 1

    floor_support_edges = [
        record for record in comparison_records if str(record["object_label"]).lower() == "floor"
    ]
    floor_recovered = [
        record for record in floor_support_edges if record["point_status"] == "point_satisfied"
    ]
    obb_failure_recovered = [
        record
        for record in comparison_records
        if record["old_status"] in {"uncertain", "violated"}
        and record["point_status"] == "point_satisfied"
    ]
    errors: list[str] = []
    warnings: list[str] = ["ply_points_v1_smoke_test_only_not_benchmark_evidence"]
    expected_vertices = phase_a_summary.get("counts", {}).get("ply_vertices")
    if expected_vertices is not None and int(expected_vertices) != ply_stats["ply_vertex_rows_read"]:
        errors.append(f"ply_vertex_rows_read_mismatch:{expected_vertices}!={ply_stats['ply_vertex_rows_read']}")
    if missing_point_object_ids:
        errors.append(f"support_contact_endpoint_ids_missing_point_groups:{missing_point_object_ids}")
    if point_status_counts.get("point_uncertain", 0):
        warnings.append(f"point_uncertain_edges:{point_status_counts['point_uncertain']}")

    output_paths = {
        "evidence": artifact_dir / "point_evidence.jsonl",
        "comparison": artifact_dir / "point_comparison.jsonl",
        "summary": artifact_dir / "point_summary.json",
        "report": artifact_dir / "point_report.md",
    }
    summary = {
        "scan_id": scan_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "script_name": Path(__file__).name,
        "point_rule_version": thresholds["point_rule_version"],
        "phase": "Phase C: ply_points_v1 support/contact smoke test",
        "input_paths": {key: str(path) for key, path in paths.items()},
        "output_paths": {key: str(path) for key, path in output_paths.items()},
        "ply_stats": ply_stats,
        "counts": {
            "support_contact_edges_total": len(support_edges),
            "target_object_ids": len(target_object_ids),
            "missing_point_object_ids": len(missing_point_object_ids),
            "point_evidence_available_count": sum(
                1 for record in evidence_records if record["point_evidence_available"]
            ),
            "floor_support_edges": len(floor_support_edges),
            "floor_support_recovered_edges": len(floor_recovered),
            "manual_labels_loaded": len(manual_labels),
        },
        "point_status_counts": count_dict(point_status_counts),
        "status_transition_counts": count_dict(transition_counts),
        "manual_label_to_point_status_counts": nested_count_dict(manual_to_point),
        "headline_metrics": {
            "floor_support_recovery_rate": (
                len(floor_recovered) / len(floor_support_edges) if floor_support_edges else None
            ),
            "point_uncertain_rate": (
                point_status_counts.get("point_uncertain", 0) / len(evidence_records)
                if evidence_records
                else None
            ),
            "obb_failure_to_point_satisfied_count": len(obb_failure_recovered),
        },
        "missing_point_object_ids": missing_point_object_ids,
        "threshold_config": thresholds,
        "validation": {
            "passed": not errors,
            "warnings": warnings,
            "errors": errors,
        },
    }

    write_jsonl(output_paths["evidence"], evidence_records)
    write_jsonl(output_paths["comparison"], comparison_records)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(make_report(summary), encoding="utf-8")

    if errors:
        print(f"PLY points v1 export completed with validation errors. Output: {artifact_dir}")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"PLY points v1 export completed. Output: {artifact_dir}")
    print(f"Support/contact edges: {len(support_edges)}")
    print(f"Point status counts: {dict(sorted(point_status_counts.items()))}")
    print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
