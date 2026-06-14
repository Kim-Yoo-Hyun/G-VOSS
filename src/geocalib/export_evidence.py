#!/usr/bin/env python3
"""Export one-scan H001 geometry evidence records.

Phase A only: this script exports inspectable geometry evidence for 3DSSG
relation tuples. It does not apply verifier decisions.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_THRESHOLDS = {
    "rule_version": "h001-rules-v0",
    "z_gap_abs_max_m": 0.10,
    "z_order_margin_m": 0.02,
    "xy_overlap_subject_min": 0.05,
    "xy_overlap_object_min": 0.01,
    "near_distance_norm_max": 1.50,
    "relative_z_margin_norm": 0.10,
    "relative_xy_margin_norm": 0.10,
    "geometry_score_pass_min": 0.60,
    "frame_assumption": "scene_xyz_v0",
    "z_axis_assumption": "scene_z_up_v0",
}

SUPPORT_CONTACT = {"standing on", "lying on", "supported by"}
PROXIMITY = {"close by"}
RELATIVE_VERTICAL = {"higher than", "lower than"}
RELATIVE_HORIZONTAL = {"left", "right", "front", "behind"}
ATTACHMENT_DEFERRED = {"attached to", "hanging on", "leaning against", "connected to"}
SIZE_COMPARISON_DEFERRED = {"bigger than", "smaller than"}
P0_FAMILIES = {
    "support_contact",
    "proximity",
    "relative_vertical",
    "relative_horizontal",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Phase A geometry evidence for one H001 sample scan."
    )
    parser.add_argument("--scan-id", required=True)
    parser.add_argument("--dataset-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--rule-version", default="h001-rules-v0")
    parser.add_argument("--geometry-source", default="semseg_obb_v0", choices=["semseg_obb_v0"])
    parser.add_argument(
        "--include-horizontal-diagnostic",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--fail-on-validation-warning", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def find_scan_entry(data: dict[str, Any], scan_id: str, source_name: str) -> dict[str, Any]:
    matches = [entry for entry in data.get("scans", []) if entry.get("scan") == scan_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one {source_name} entry for {scan_id}, found {len(matches)}")
    return matches[0]


def as_float_list(values: list[Any] | None, expected_len: int) -> list[float] | None:
    if values is None or len(values) != expected_len:
        return None
    return [float(v) for v in values]


def vector_sub(a: list[float], b: list[float]) -> list[float]:
    return [a[i] - b[i] for i in range(3)]


def euclidean(values: list[float]) -> float:
    return math.sqrt(sum(v * v for v in values))


def safe_div(num: float, den: float) -> float | None:
    if den <= 0:
        return None
    return num / den


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def derive_aabb_from_obb(obb: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    warnings: list[str] = []
    centroid = as_float_list(obb.get("centroid"), 3)
    axes_lengths = as_float_list(obb.get("axesLengths"), 3)
    normalized_axes = as_float_list(obb.get("normalizedAxes"), 9)

    if centroid is None:
        return None, ["missing_or_invalid_centroid"]
    if axes_lengths is None:
        return None, ["missing_or_invalid_axes_lengths"]
    if normalized_axes is None:
        return None, ["missing_or_invalid_normalized_axes"]
    if any(length <= 0 for length in axes_lengths):
        return None, ["non_positive_axes_length"]

    rows = [normalized_axes[0:3], normalized_axes[3:6], normalized_axes[6:9]]
    for idx, row in enumerate(rows):
        norm = euclidean(row)
        if abs(norm - 1.0) > 0.05:
            warnings.append(f"obb_axis_{idx}_norm_{norm:.4f}")
    for i in range(3):
        for j in range(i + 1, 3):
            axis_dot = abs(dot(rows[i], rows[j]))
            if axis_dot > 0.05:
                warnings.append(f"obb_axes_{i}_{j}_dot_{axis_dot:.4f}")

    half_lengths = [length / 2.0 for length in axes_lengths]
    half_extent_world = [
        sum(abs(rows[i][j]) * half_lengths[j] for j in range(3))
        for i in range(3)
    ]
    aabb_min = [centroid[i] - half_extent_world[i] for i in range(3)]
    aabb_max = [centroid[i] + half_extent_world[i] for i in range(3)]
    size_xyz = [aabb_max[i] - aabb_min[i] for i in range(3)]
    if any(size <= 0 for size in size_xyz):
        return None, warnings + ["non_positive_aabb_extent"]

    diag_3d = euclidean(size_xyz)
    diag_xy = math.sqrt(size_xyz[0] * size_xyz[0] + size_xyz[1] * size_xyz[1])
    return {
        "center_xyz": centroid,
        "axes_lengths": axes_lengths,
        "obb_normalized_axes": normalized_axes,
        "aabb_min_xyz": aabb_min,
        "aabb_max_xyz": aabb_max,
        "size_xyz": size_xyz,
        "height_z": size_xyz[2],
        "diag_3d": diag_3d,
        "diag_xy": diag_xy,
    }, warnings


def parse_ply_header(path: Path) -> dict[str, int | None]:
    vertex_count = None
    face_count = None
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("element vertex"):
                vertex_count = int(stripped.split()[-1])
            elif stripped.startswith("element face"):
                face_count = int(stripped.split()[-1])
            elif stripped == "end_header":
                break
    return {"vertices": vertex_count, "faces": face_count}


def interval_intersection(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))


def volume(aabb_min: list[float], aabb_max: list[float], dims: tuple[int, ...] = (0, 1, 2)) -> float:
    result = 1.0
    for dim in dims:
        result *= max(0.0, aabb_max[dim] - aabb_min[dim])
    return result


def intersection_volume(
    a_min: list[float],
    a_max: list[float],
    b_min: list[float],
    b_max: list[float],
    dims: tuple[int, ...],
) -> float:
    result = 1.0
    for dim in dims:
        result *= interval_intersection(a_min[dim], a_max[dim], b_min[dim], b_max[dim])
    return result


def iou(
    a_min: list[float],
    a_max: list[float],
    b_min: list[float],
    b_max: list[float],
    dims: tuple[int, ...],
) -> float | None:
    inter = intersection_volume(a_min, a_max, b_min, b_max, dims)
    a_vol = volume(a_min, a_max, dims)
    b_vol = volume(b_min, b_max, dims)
    union = a_vol + b_vol - inter
    return safe_div(inter, union) if union > 0 else None


def predicate_family(label: str) -> str:
    if label in SUPPORT_CONTACT:
        return "support_contact"
    if label in PROXIMITY:
        return "proximity"
    if label in RELATIVE_VERTICAL:
        return "relative_vertical"
    if label in RELATIVE_HORIZONTAL:
        return "relative_horizontal"
    if label in ATTACHMENT_DEFERRED:
        return "attachment_deferred"
    if label in SIZE_COMPARISON_DEFERRED:
        return "size_comparison_deferred"
    return "unsupported_first_pass"


def compact_geometry(geometry: dict[str, Any], semseg_obj: dict[str, Any]) -> dict[str, Any]:
    return {
        "center_xyz": geometry["center_xyz"],
        "axes_lengths": geometry["axes_lengths"],
        "aabb_min_xyz": geometry["aabb_min_xyz"],
        "aabb_max_xyz": geometry["aabb_max_xyz"],
        "size_xyz": geometry["size_xyz"],
        "height_z": geometry["height_z"],
        "diag_3d": geometry["diag_3d"],
        "diag_xy": geometry["diag_xy"],
        "segment_count": len(semseg_obj.get("segments", [])),
        "dominant_normal": semseg_obj.get("dominantNormal"),
    }


def compute_edge_evidence(
    subject_geom: dict[str, Any],
    object_geom: dict[str, Any],
    thresholds: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    s_min = subject_geom["aabb_min_xyz"]
    s_max = subject_geom["aabb_max_xyz"]
    o_min = object_geom["aabb_min_xyz"]
    o_max = object_geom["aabb_max_xyz"]
    s_center = subject_geom["center_xyz"]
    o_center = object_geom["center_xyz"]
    delta = vector_sub(s_center, o_center)

    distance_3d = euclidean(delta)
    distance_xy = math.sqrt(delta[0] * delta[0] + delta[1] * delta[1])
    mean_diag_3d = (subject_geom["diag_3d"] + object_geom["diag_3d"]) / 2.0
    mean_diag_xy = (subject_geom["diag_xy"] + object_geom["diag_xy"]) / 2.0
    mean_height = (subject_geom["height_z"] + object_geom["height_z"]) / 2.0

    inter_3d = intersection_volume(s_min, s_max, o_min, o_max, (0, 1, 2))
    inter_xy = intersection_volume(s_min, s_max, o_min, o_max, (0, 1))
    subject_vol = volume(s_min, s_max, (0, 1, 2))
    object_vol = volume(o_min, o_max, (0, 1, 2))
    subject_xy_area = volume(s_min, s_max, (0, 1))
    object_xy_area = volume(o_min, o_max, (0, 1))

    normalized_distance_3d = safe_div(distance_3d, mean_diag_3d)
    normalized_distance_xy = safe_div(distance_xy, mean_diag_xy)
    normalized_center_delta_z = safe_div(delta[2], mean_height)

    relative_margin_xy = thresholds["relative_xy_margin_norm"] * mean_diag_xy

    evidence = {
        "centers": {
            "subject_center_xyz": s_center,
            "object_center_xyz": o_center,
            "delta_xyz": delta,
        },
        "distances": {
            "distance_3d": distance_3d,
            "distance_xy": distance_xy,
            "normalized_distance_3d": normalized_distance_3d,
            "normalized_distance_xy": normalized_distance_xy,
        },
        "vertical": {
            "subject_bottom_z": s_min[2],
            "subject_top_z": s_max[2],
            "object_bottom_z": o_min[2],
            "object_top_z": o_max[2],
            "vertical_gap_subject_on_object": s_min[2] - o_max[2],
            "center_delta_z": delta[2],
            "normalized_center_delta_z": normalized_center_delta_z,
        },
        "overlap": {
            "aabb_iou_3d": iou(s_min, s_max, o_min, o_max, (0, 1, 2)),
            "projected_iou_xy": iou(s_min, s_max, o_min, o_max, (0, 1)),
            "projected_subject_overlap_ratio": safe_div(inter_xy, subject_xy_area),
            "projected_object_overlap_ratio": safe_div(inter_xy, object_xy_area),
        },
        "containment": {
            "subject_aabb_in_object_aabb_ratio": safe_div(inter_3d, subject_vol),
            "object_aabb_in_subject_aabb_ratio": safe_div(inter_3d, object_vol),
        },
        "diagnostic": {
            "frame_assumption": thresholds["frame_assumption"],
            "z_axis_assumption": thresholds["z_axis_assumption"],
            "horizontal_axis_delta": {"delta_x": delta[0], "delta_y": delta[1]},
        },
    }

    rule_inputs = {
        "is_subject_above_object": s_center[2] > o_center[2] + thresholds["z_order_margin_m"],
        "small_vertical_gap_candidate": abs(s_min[2] - o_max[2]) <= thresholds["z_gap_abs_max_m"],
        "has_projected_overlap_candidate": (
            evidence["overlap"]["projected_subject_overlap_ratio"] is not None
            and evidence["overlap"]["projected_subject_overlap_ratio"] >= thresholds["xy_overlap_subject_min"]
        ),
        "near_by_normalized_distance_candidate": (
            normalized_distance_xy is not None
            and normalized_distance_xy <= thresholds["near_distance_norm_max"]
        ),
        "higher_than_candidate": (
            normalized_center_delta_z is not None
            and normalized_center_delta_z >= thresholds["relative_z_margin_norm"]
        ),
        "lower_than_candidate": (
            normalized_center_delta_z is not None
            and normalized_center_delta_z <= -thresholds["relative_z_margin_norm"]
        ),
        "left_candidate": delta[0] <= -relative_margin_xy,
        "right_candidate": delta[0] >= relative_margin_xy,
        "front_candidate": delta[1] <= -relative_margin_xy,
        "behind_candidate": delta[1] >= relative_margin_xy,
    }
    return evidence, rule_inputs


def warning_summary(prefix: str, count: int, examples: list[str]) -> str:
    sample = ", ".join(examples[:5])
    if count > len(examples[:5]):
        sample += ", ..."
    return f"{prefix}: {count} ({sample})"


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def make_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Evidence Export",
        "",
        f"Created at: `{summary['created_at']}`",
        f"Scan id: `{summary['scan_id']}`",
        f"Geometry source: `{summary['geometry_source']}`",
        f"Rule version: `{summary['rule_version']}`",
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

    lines.extend(["", "## Predicate Families", ""])
    for key, value in sorted(summary["predicate_family_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Top Predicates", ""])
    for key, value in sorted(summary["predicate_counts"].items(), key=lambda item: (-item[1], item[0]))[:12]:
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Geometry Availability", ""])
    for key, value in sorted(summary["geometry_available_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Next Action", ""])
    lines.append("Review `edges.jsonl`, then run the `h001-rules-v0` verifier application.")
    lines.append("")
    lines.append("This is Phase A output only; it is not prediction-level H001 evidence.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    thresholds = dict(DEFAULT_THRESHOLDS)
    thresholds["rule_version"] = args.rule_version

    dataset_root = args.dataset_root
    scan_id = args.scan_id
    output_dir = args.output_root / scan_id
    output_dir.mkdir(parents=True, exist_ok=True)

    paths = {
        "objects": dataset_root / "3DSSG" / "objects.json",
        "relationships": dataset_root / "3DSSG" / "relationships.json",
        "classes": dataset_root / "3DSSG" / "classes.txt",
        "relationships_txt": dataset_root / "3DSSG" / "relationships.txt",
        "semseg": dataset_root / "3RScan" / "scans" / scan_id / "semseg.v2.json",
        "ply": dataset_root / "3RScan" / "scans" / scan_id / "labels.instances.annotated.v2.ply",
        "segments": dataset_root / "3RScan" / "scans" / scan_id / "mesh.refined.0.010000.segs.v2.json",
    }

    errors: list[str] = []
    warnings: list[str] = []
    for name, path in paths.items():
        if not path.exists():
            errors.append(f"missing_input_file:{name}:{path}")
    if errors:
        raise SystemExit("\n".join(errors))

    objects_data = load_json(paths["objects"])
    relationships_data = load_json(paths["relationships"])
    semseg_data = load_json(paths["semseg"])
    segments_data = load_json(paths["segments"])
    ply_header = parse_ply_header(paths["ply"])

    objects_entry = find_scan_entry(objects_data, scan_id, "objects")
    relationships_entry = find_scan_entry(relationships_data, scan_id, "relationships")
    object_rows = objects_entry.get("objects", [])
    relation_rows = relationships_entry.get("relationships", [])
    semseg_rows = semseg_data.get("segGroups", [])

    if not relation_rows:
        errors.append("zero_relation_tuples")
    if not semseg_rows:
        errors.append("zero_seggroups")

    objects_by_id = {int(obj["id"]): obj for obj in object_rows}
    semseg_by_id = {int(obj["objectId"]): obj for obj in semseg_rows}

    semseg_geometries: dict[int, dict[str, Any]] = {}
    obb_warning_examples: list[str] = []
    invalid_obb_ids: set[int] = set()
    for object_id, semseg_obj in semseg_by_id.items():
        geometry, obb_warnings = derive_aabb_from_obb(semseg_obj.get("obb", {}))
        if geometry is None:
            invalid_obb_ids.add(object_id)
        else:
            semseg_geometries[object_id] = geometry
        for warning in obb_warnings:
            obb_warning_examples.append(f"{object_id}:{warning}")

    if obb_warning_examples:
        warnings.append(warning_summary("obb_axis_validation_warnings", len(obb_warning_examples), obb_warning_examples))

    seg_indices_len = len(segments_data.get("segIndices", []))
    if ply_header["vertices"] != seg_indices_len:
        warnings.append(f"ply_vertex_count_differs_from_segindices:{ply_header['vertices']}!={seg_indices_len}")

    relation_endpoint_ids = sorted({int(row[0]) for row in relation_rows} | {int(row[1]) for row in relation_rows})
    missing_object_ids = [object_id for object_id in relation_endpoint_ids if object_id not in objects_by_id]
    missing_semseg_ids = [object_id for object_id in relation_endpoint_ids if object_id not in semseg_by_id]
    if missing_object_ids:
        errors.append(f"relation_endpoint_missing_3dssg_objects:{missing_object_ids}")
    if missing_semseg_ids:
        errors.append(f"relation_endpoint_missing_semseg_objects:{missing_semseg_ids}")

    p0_endpoint_ids = {
        int(endpoint)
        for row in relation_rows
        if predicate_family(str(row[3])) in P0_FAMILIES
        for endpoint in (row[0], row[1])
    }
    invalid_p0_obb_ids = sorted(object_id for object_id in p0_endpoint_ids if object_id in invalid_obb_ids)
    if invalid_p0_obb_ids:
        errors.append(f"invalid_or_missing_obb_for_p0_endpoint:{invalid_p0_obb_ids}")

    label_mismatch_examples: list[str] = []
    for object_id in relation_endpoint_ids:
        if object_id in objects_by_id and object_id in semseg_by_id:
            label_3dssg = str(objects_by_id[object_id].get("label", "")).strip().lower()
            label_semseg = str(semseg_by_id[object_id].get("label", "")).strip().lower()
            if label_3dssg and label_semseg and label_3dssg != label_semseg:
                label_mismatch_examples.append(f"{object_id}:{label_3dssg}!={label_semseg}")
    if label_mismatch_examples:
        warnings.append(warning_summary("label_mismatches", len(label_mismatch_examples), label_mismatch_examples))

    edge_records: list[dict[str, Any]] = []
    predicate_counts: Counter[str] = Counter()
    predicate_family_counts: Counter[str] = Counter()
    geometry_available_counts: Counter[str] = Counter()

    for row_index, row in enumerate(relation_rows):
        subject_id = int(row[0])
        object_id = int(row[1])
        relationship_id = int(row[2])
        predicate_label = str(row[3])
        family = predicate_family(predicate_label)
        predicate_counts[predicate_label] += 1
        predicate_family_counts[family] += 1

        missing_fields: list[str] = []
        subject_obj = objects_by_id.get(subject_id)
        object_obj = objects_by_id.get(object_id)
        subject_semseg = semseg_by_id.get(subject_id)
        object_semseg = semseg_by_id.get(object_id)
        subject_geom = semseg_geometries.get(subject_id)
        object_geom = semseg_geometries.get(object_id)

        if subject_obj is None:
            missing_fields.append("subject_3dssg_object")
        if object_obj is None:
            missing_fields.append("object_3dssg_object")
        if subject_semseg is None:
            missing_fields.append("subject_semseg_object")
        if object_semseg is None:
            missing_fields.append("object_semseg_object")
        if subject_geom is None:
            missing_fields.append("subject_geometry")
        if object_geom is None:
            missing_fields.append("object_geometry")

        geometry_available = subject_geom is not None and object_geom is not None
        geometry_available_counts[str(geometry_available).lower()] += 1

        if geometry_available and subject_semseg is not None and object_semseg is not None:
            geometry_evidence, rule_inputs = compute_edge_evidence(subject_geom, object_geom, thresholds)
            object_geometry = {
                "subject": compact_geometry(subject_geom, subject_semseg),
                "object": compact_geometry(object_geom, object_semseg),
            }
        else:
            geometry_evidence = {}
            rule_inputs = {}
            object_geometry = {}

        notes: list[str] = []
        if family == "relative_horizontal":
            notes.append("diagnostic_only_until_coordinate_frame_validation")
        if family == "support_contact":
            notes.append("support_contact_diagnostic_until_z_axis_and_obb_aabb_manual_inspection")
        if family == "unsupported_first_pass":
            notes.append("unsupported_relation_is_not_a_failure")

        edge_id = f"{scan_id}:{row_index}:{subject_id}:{predicate_label}:{object_id}"
        edge_records.append(
            {
                "edge_id": edge_id,
                "scan_id": scan_id,
                "row_index": row_index,
                "subject_id": subject_id,
                "object_id": object_id,
                "subject_label": subject_obj.get("label") if subject_obj else None,
                "object_label": object_obj.get("label") if object_obj else None,
                "relationship_id": relationship_id,
                "predicate_label": predicate_label,
                "predicate_family": family,
                "geometry_source": args.geometry_source,
                "geometry_available": geometry_available,
                "missing_fields": missing_fields,
                "object_geometry": object_geometry,
                "geometry_evidence": geometry_evidence,
                "rule_inputs": rule_inputs,
                "notes": notes,
            }
        )

    unsupported_labels = [
        f"{label}:{count}"
        for label, count in predicate_counts.items()
        if predicate_family(label) == "unsupported_first_pass"
    ]
    if unsupported_labels:
        warnings.append(warning_summary("unsupported_predicate_labels", len(unsupported_labels), unsupported_labels))
    if predicate_family_counts.get("relative_horizontal", 0):
        warnings.append("relative_horizontal_is_diagnostic_only")
    if predicate_family_counts.get("support_contact", 0):
        warnings.append("support_contact_requires_manual_z_axis_and_obb_aabb_inspection")

    if args.fail_on_validation_warning and warnings:
        errors.append("fail_on_validation_warning_enabled")

    output_paths = {
        "edges": output_dir / "edges.jsonl",
        "summary": output_dir / "export_summary.json",
        "report": output_dir / "export_report.md",
        "thresholds": output_dir / "thresholds.json",
    }

    summary = {
        "scan_id": scan_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "script_name": Path(__file__).name,
        "rule_version": thresholds["rule_version"],
        "geometry_source": args.geometry_source,
        "phase": "Phase A: evidence export sanity check",
        "input_paths": {key: str(path) for key, path in paths.items()},
        "output_paths": {key: str(path) for key, path in output_paths.items()},
        "counts": {
            "objects_3dssg": len(objects_by_id),
            "objects_semseg": len(semseg_by_id),
            "relation_tuples": len(relation_rows),
            "unique_relation_endpoint_ids": len(relation_endpoint_ids),
            "missing_object_joins": len(missing_object_ids),
            "missing_semseg_joins": len(missing_semseg_ids),
            "invalid_obb_objects": len(invalid_obb_ids),
            "edges_exported": len(edge_records),
            "ply_vertices": ply_header["vertices"],
            "ply_faces": ply_header["faces"],
            "seg_indices": seg_indices_len,
        },
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "predicate_family_counts": dict(sorted(predicate_family_counts.items())),
        "geometry_available_counts": dict(sorted(geometry_available_counts.items())),
        "validation": {
            "passed": not errors,
            "warnings": warnings,
            "errors": errors,
        },
        "threshold_config": thresholds,
    }

    write_jsonl(output_paths["edges"], edge_records)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(make_report(summary), encoding="utf-8")
    write_json(output_paths["thresholds"], thresholds)

    if errors:
        print(f"Export completed with validation errors. Output: {output_dir}")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"Export completed. Output: {output_dir}")
    print(f"Edges exported: {len(edge_records)}")
    print(f"Warnings: {len(warnings)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
