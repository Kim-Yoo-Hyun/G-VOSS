#!/usr/bin/env python3
"""Audit coordinate-frame semantics for relative-horizontal GT labels.

This gate checks whether held-out 3DSSG `left/right/front/behind` labels are
stable under a deterministic geometry frame before any metric promotion. It is
not a verifier, does not score source predictions, and does not alter the
current H001 paper claim.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_REL

import numpy as np


HYPOTHESIS_ROOT = H001_HYPOTHESIS_REL
HARDENED_ROOT = HYPOTHESIS_ROOT / "artifacts/evaluation/vlsat_closed_set/hardened"
EXPERIMENT_ROOT = Path("experiments/H001_geom_reliability")

TARGET_FAMILY = "relative_horizontal"
TARGET_LABELS = ("left", "right", "front", "behind")
INVERSE_LABEL = {
    "left": "right",
    "right": "left",
    "front": "behind",
    "behind": "front",
}
CURRENT_FAMILIES = ("support_contact", "proximity", "relative_vertical")

MIN_MARGIN_M = 0.15
MARGIN_SCALE = 0.10
MAX_MARGIN_M = 0.50
STRONG_OVERLAP_RATIO = 0.75
CONFLICTING_AXIS_RATIO = 1.50
MIN_MACRO_PURITY = 0.80
MIN_PER_LABEL_PURITY = 0.75
MIN_INVERSE_CONSISTENCY = 0.85
MIN_STRICT_ELIGIBLE_SHARE = 0.50
MIN_WRONG_FRAME_GAP = 0.05


@dataclass(frozen=True)
class FrameSpec:
    name: str
    frame_family: str
    left_axis: tuple[float, float]
    front_axis: tuple[float, float]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    yield line_no, json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid_jsonl:{path}:{line_no}:{exc}") from exc


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def as_float_list(value: Any, expected_len: int) -> list[float] | None:
    if not isinstance(value, list) or len(value) != expected_len:
        return None
    result: list[float] = []
    for item in value:
        number = finite_float(item)
        if number is None:
            return None
        result.append(number)
    return result


def euclidean(values: list[float] | tuple[float, ...]) -> float:
    return math.sqrt(sum(value * value for value in values))


def interval_intersection(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))


def area_xy(geom: dict[str, Any]) -> float:
    aabb_min = geom["aabb_min_xyz"]
    aabb_max = geom["aabb_max_xyz"]
    return max(0.0, aabb_max[0] - aabb_min[0]) * max(0.0, aabb_max[1] - aabb_min[1])


def intersection_xy(subject: dict[str, Any], obj: dict[str, Any]) -> float:
    s_min = subject["aabb_min_xyz"]
    s_max = subject["aabb_max_xyz"]
    o_min = obj["aabb_min_xyz"]
    o_max = obj["aabb_max_xyz"]
    return interval_intersection(s_min[0], s_max[0], o_min[0], o_max[0]) * interval_intersection(
        s_min[1], s_max[1], o_min[1], o_max[1]
    )


def derive_aabb_from_obb(obb: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    centroid = as_float_list(obb.get("centroid"), 3)
    axes_lengths = as_float_list(obb.get("axesLengths"), 3)
    normalized_axes = as_float_list(obb.get("normalizedAxes"), 9)
    warnings: list[str] = []
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

    return {
        "center_xyz": centroid,
        "aabb_min_xyz": aabb_min,
        "aabb_max_xyz": aabb_max,
        "size_xyz": size_xyz,
        "diag_xy": math.sqrt(size_xyz[0] * size_xyz[0] + size_xyz[1] * size_xyz[1]),
    }, warnings


def load_scan_geometries(dataset_root: Path, scan_id: str) -> tuple[dict[int, dict[str, Any]], list[str], list[str]]:
    semseg_path = dataset_root / "3RScan" / "scans" / scan_id / "semseg.v2.json"
    if not semseg_path.exists():
        return {}, [], [f"missing_semseg:{scan_id}:{semseg_path}"]
    payload = read_json(semseg_path)
    geometries: dict[int, dict[str, Any]] = {}
    warnings: list[str] = []
    errors: list[str] = []
    for item in payload.get("segGroups", []):
        object_id = int(item["objectId"])
        geom, geom_warnings = derive_aabb_from_obb(item.get("obb", {}))
        if geom is None:
            warnings.append(f"invalid_obb:{scan_id}:{object_id}:{','.join(geom_warnings)}")
            continue
        geom["object_label"] = item.get("label")
        geometries[object_id] = geom
        for warning in geom_warnings:
            warnings.append(f"obb_warning:{scan_id}:{object_id}:{warning}")
    if not geometries:
        errors.append(f"zero_valid_geometries:{scan_id}")
    return geometries, warnings, errors


def gt_row_key(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (
        str(row["scan_id"]),
        int(row["subset_split_id"]),
        int(row["subject_id"]),
        int(row["object_id"]),
        str(row["predicate_label"]),
    )


def load_relative_horizontal_gt(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for _, row in iter_jsonl(path):
        if row.get("predicate_family") == TARGET_FAMILY and row.get("predicate_label") in TARGET_LABELS:
            rows.append(row)
    rows.sort(key=gt_row_key)
    return rows


def normalize_axis(axis: tuple[float, float]) -> tuple[float, float]:
    norm = math.sqrt(axis[0] * axis[0] + axis[1] * axis[1])
    if norm <= 0:
        return (1.0, 0.0)
    return (axis[0] / norm, axis[1] / norm)


def scan_frame_specs() -> list[FrameSpec]:
    axis_map = {
        "pos_x": (1.0, 0.0),
        "neg_x": (-1.0, 0.0),
        "pos_y": (0.0, 1.0),
        "neg_y": (0.0, -1.0),
    }
    specs: list[FrameSpec] = []
    for left_name, left_axis in axis_map.items():
        front_names = ("pos_y", "neg_y") if left_name.endswith("_x") else ("pos_x", "neg_x")
        for front_name in front_names:
            specs.append(
                FrameSpec(
                    name=f"scan_left_{left_name}_front_{front_name}",
                    frame_family="scan_xy",
                    left_axis=axis_map[left_name],
                    front_axis=axis_map[front_name],
                )
            )
    return specs


def pca_axes(geometries: dict[int, dict[str, Any]], object_ids: set[int]) -> tuple[tuple[float, float], tuple[float, float]] | None:
    centers = [
        geometries[object_id]["center_xyz"][:2]
        for object_id in sorted(object_ids)
        if object_id in geometries
    ]
    if len(centers) < 2:
        return None
    values = np.asarray(centers, dtype=float)
    values = values - np.mean(values, axis=0, keepdims=True)
    covariance = np.cov(values.T)
    if not np.all(np.isfinite(covariance)):
        return None
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    primary = eigenvectors[:, int(np.argmax(eigenvalues))]
    axis0 = normalize_axis((float(primary[0]), float(primary[1])))
    axis1 = normalize_axis((-axis0[1], axis0[0]))
    return axis0, axis1


def pca_frame_specs(scan_id: str, geometries: dict[int, dict[str, Any]], object_ids: set[int]) -> list[FrameSpec]:
    axes = pca_axes(geometries, object_ids)
    if axes is None:
        return []
    axis0, axis1 = axes
    axis_map = {
        "pos_p0": axis0,
        "neg_p0": (-axis0[0], -axis0[1]),
        "pos_p1": axis1,
        "neg_p1": (-axis1[0], -axis1[1]),
    }
    specs: list[FrameSpec] = []
    for left_name, left_axis in axis_map.items():
        front_names = ("pos_p1", "neg_p1") if left_name.endswith("_p0") else ("pos_p0", "neg_p0")
        for front_name in front_names:
            specs.append(
                FrameSpec(
                    name=f"room_pca_left_{left_name}_front_{front_name}",
                    frame_family="room_pca",
                    left_axis=axis_map[left_name],
                    front_axis=axis_map[front_name],
                )
            )
    return specs


def pair_geometry(subject: dict[str, Any], obj: dict[str, Any]) -> dict[str, Any]:
    s_center = subject["center_xyz"]
    o_center = obj["center_xyz"]
    delta = [s_center[i] - o_center[i] for i in range(3)]
    mean_diag_xy = max(1e-6, (float(subject["diag_xy"]) + float(obj["diag_xy"])) / 2.0)
    inter_xy = intersection_xy(subject, obj)
    subject_area = area_xy(subject)
    object_area = area_xy(obj)
    subject_overlap = inter_xy / subject_area if subject_area > 0 else 0.0
    object_overlap = inter_xy / object_area if object_area > 0 else 0.0
    return {
        "center_delta_x": delta[0],
        "center_delta_y": delta[1],
        "center_delta_z": delta[2],
        "distance_xy": math.sqrt(delta[0] * delta[0] + delta[1] * delta[1]),
        "mean_diag_xy": mean_diag_xy,
        "normalized_delta_x": delta[0] / mean_diag_xy,
        "normalized_delta_y": delta[1] / mean_diag_xy,
        "margin_m": min(MAX_MARGIN_M, max(MIN_MARGIN_M, MARGIN_SCALE * mean_diag_xy)),
        "projected_subject_overlap_ratio": subject_overlap,
        "projected_object_overlap_ratio": object_overlap,
        "projected_overlap_max_ratio": max(subject_overlap, object_overlap),
    }


def project(delta_x: float, delta_y: float, axis: tuple[float, float]) -> float:
    return delta_x * axis[0] + delta_y * axis[1]


def evaluate_row_with_frame(row: dict[str, Any], pair: dict[str, Any], frame: FrameSpec) -> dict[str, Any]:
    label = row["predicate_label"]
    left_projection = project(pair["center_delta_x"], pair["center_delta_y"], frame.left_axis)
    front_projection = project(pair["center_delta_x"], pair["center_delta_y"], frame.front_axis)
    if label in {"left", "right"}:
        target_projection = left_projection
        other_projection = front_projection
        expected_positive = label == "left"
        target_axis = "left_axis"
    else:
        target_projection = front_projection
        other_projection = left_projection
        expected_positive = label == "front"
        target_axis = "front_axis"

    flags: list[str] = []
    if abs(target_projection) <= float(pair["margin_m"]):
        flags.append("axis_margin_ambiguous")
    if float(pair["projected_overlap_max_ratio"]) >= STRONG_OVERLAP_RATIO:
        flags.append("strong_projected_overlap")
    if abs(other_projection) >= max(float(pair["margin_m"]), CONFLICTING_AXIS_RATIO * abs(target_projection)):
        flags.append("conflicting_axis_dominates")

    sign_matches = target_projection > 0 if expected_positive else target_projection < 0
    strict_status = "uncertain" if flags else ("match" if sign_matches else "contradiction")
    sign_only_status = (
        "uncertain" if "axis_margin_ambiguous" in flags else ("match" if sign_matches else "contradiction")
    )
    return {
        "label": label,
        "target_axis": target_axis,
        "left_projection_m": left_projection,
        "front_projection_m": front_projection,
        "target_projection_m": target_projection,
        "other_projection_m": other_projection,
        "margin_m": pair["margin_m"],
        "ambiguity_flags": flags,
        "sign_matches": sign_matches,
        "strict_status": strict_status,
        "sign_only_status": sign_only_status,
    }


def empty_metric() -> dict[str, Any]:
    return {
        "total": 0,
        "missing_geometry": 0,
        "strict": {
            "eligible": 0,
            "match": 0,
            "contradiction": 0,
            "uncertain": 0,
            "purity": None,
            "eligible_share": None,
        },
        "sign_only": {
            "eligible": 0,
            "match": 0,
            "contradiction": 0,
            "uncertain": 0,
            "purity": None,
            "eligible_share": None,
        },
    }


def update_metric(metric: dict[str, Any], status: str, mode: str) -> None:
    bucket = metric[mode]
    if status == "uncertain":
        bucket["uncertain"] += 1
    else:
        bucket["eligible"] += 1
        bucket[status] += 1


def finalize_metric(metric: dict[str, Any]) -> None:
    total = int(metric["total"])
    for mode in ("strict", "sign_only"):
        bucket = metric[mode]
        eligible = int(bucket["eligible"])
        bucket["purity"] = round(bucket["match"] / eligible, 4) if eligible else None
        bucket["eligible_share"] = round(eligible / total, 4) if total else None


def summarize_frame(
    frame: FrameSpec,
    gt_rows: list[dict[str, Any]],
    geometries_by_scan: dict[str, dict[int, dict[str, Any]]],
    pca_specs_by_scan: dict[str, dict[str, FrameSpec]],
) -> tuple[dict[str, Any], list[dict[str, Any]], Counter[str]]:
    frame_metrics = empty_metric()
    per_label = {label: empty_metric() for label in TARGET_LABELS}
    ambiguity_counter: Counter[str] = Counter()
    row_records: list[dict[str, Any]] = []

    for row in gt_rows:
        scan_id = str(row["scan_id"])
        subject_id = int(row["subject_id"])
        object_id = int(row["object_id"])
        label = str(row["predicate_label"])
        frame_to_use = frame
        if frame.frame_family == "room_pca":
            frame_to_use = pca_specs_by_scan.get(scan_id, {}).get(frame.name, frame)
        geometries = geometries_by_scan.get(scan_id, {})
        subject = geometries.get(subject_id)
        obj = geometries.get(object_id)

        frame_metrics["total"] += 1
        per_label[label]["total"] += 1
        if subject is None or obj is None:
            frame_metrics["missing_geometry"] += 1
            per_label[label]["missing_geometry"] += 1
            ambiguity_counter["missing_geometry"] += 1
            continue

        pair = pair_geometry(subject, obj)
        outcome = evaluate_row_with_frame(row, pair, frame_to_use)
        for flag in outcome["ambiguity_flags"]:
            ambiguity_counter[flag] += 1
        update_metric(frame_metrics, outcome["strict_status"], "strict")
        update_metric(frame_metrics, outcome["sign_only_status"], "sign_only")
        update_metric(per_label[label], outcome["strict_status"], "strict")
        update_metric(per_label[label], outcome["sign_only_status"], "sign_only")

        row_records.append(
            {
                "gt_id": row.get("gt_id"),
                "scan_id": scan_id,
                "subset_split_id": int(row["subset_split_id"]),
                "subgraph_id": row.get("subgraph_id"),
                "subject_id": subject_id,
                "object_id": object_id,
                "subject_label": row.get("subject_label"),
                "object_label": row.get("object_label"),
                "predicate_label": label,
                "frame_name": frame.name,
                "frame_family": frame.frame_family,
                "left_axis": [round(value, 6) for value in frame_to_use.left_axis],
                "front_axis": [round(value, 6) for value in frame_to_use.front_axis],
                "geometry": {
                    "center_delta_x": pair["center_delta_x"],
                    "center_delta_y": pair["center_delta_y"],
                    "distance_xy": pair["distance_xy"],
                    "mean_diag_xy": pair["mean_diag_xy"],
                    "projected_overlap_max_ratio": pair["projected_overlap_max_ratio"],
                },
                "outcome": outcome,
            }
        )

    finalize_metric(frame_metrics)
    for metric in per_label.values():
        finalize_metric(metric)

    strict_purities = [
        payload["strict"]["purity"]
        for payload in per_label.values()
        if payload["strict"]["purity"] is not None
    ]
    sign_only_purities = [
        payload["sign_only"]["purity"]
        for payload in per_label.values()
        if payload["sign_only"]["purity"] is not None
    ]
    frame_summary = {
        "frame_name": frame.name,
        "frame_family": frame.frame_family,
        "left_axis": [round(value, 6) for value in frame.left_axis],
        "front_axis": [round(value, 6) for value in frame.front_axis],
        "overall": frame_metrics,
        "by_label": per_label,
        "macro_strict_purity": round(sum(strict_purities) / len(strict_purities), 4)
        if strict_purities
        else None,
        "macro_sign_only_purity": round(sum(sign_only_purities) / len(sign_only_purities), 4)
        if sign_only_purities
        else None,
        "ambiguity_counts": dict(sorted(ambiguity_counter.items())),
    }
    return frame_summary, row_records, ambiguity_counter


def selected_frame_key(frame: dict[str, Any]) -> tuple[float, float, float, str]:
    macro = frame.get("macro_strict_purity")
    eligible = frame["overall"]["strict"]["eligible_share"]
    sign_macro = frame.get("macro_sign_only_purity")
    return (
        float(macro) if macro is not None else -1.0,
        float(eligible) if eligible is not None else -1.0,
        float(sign_macro) if sign_macro is not None else -1.0,
        str(frame["frame_name"]),
    )


def inverse_pair_consistency(gt_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_directed: dict[tuple[str, int, int, int], set[str]] = defaultdict(set)
    for row in gt_rows:
        rows_by_directed[
            (
                str(row["scan_id"]),
                int(row["subset_split_id"]),
                int(row["subject_id"]),
                int(row["object_id"]),
            )
        ].add(str(row["predicate_label"]))

    label_counts: dict[str, Counter[str]] = {label: Counter() for label in TARGET_LABELS}
    reverse_any = 0
    expected_inverse = 0
    inconsistent_examples: list[dict[str, Any]] = []
    for row in gt_rows:
        label = str(row["predicate_label"])
        reverse_key = (
            str(row["scan_id"]),
            int(row["subset_split_id"]),
            int(row["object_id"]),
            int(row["subject_id"]),
        )
        reverse_labels = rows_by_directed.get(reverse_key, set())
        if not reverse_labels:
            label_counts[label]["no_reverse_annotation"] += 1
            continue
        reverse_any += 1
        label_counts[label]["reverse_annotation_exists"] += 1
        expected = INVERSE_LABEL[label]
        if expected in reverse_labels:
            expected_inverse += 1
            label_counts[label]["expected_inverse_found"] += 1
        else:
            label_counts[label]["reverse_without_expected_inverse"] += 1
            if len(inconsistent_examples) < 25:
                inconsistent_examples.append(
                    {
                        "gt_id": row.get("gt_id"),
                        "scan_id": row["scan_id"],
                        "subset_split_id": row["subset_split_id"],
                        "subject_id": row["subject_id"],
                        "object_id": row["object_id"],
                        "predicate_label": label,
                        "reverse_labels": sorted(reverse_labels),
                        "expected_inverse_label": expected,
                    }
                )
    consistency = expected_inverse / reverse_any if reverse_any else None
    return {
        "rows": len(gt_rows),
        "rows_with_reverse_annotation": reverse_any,
        "rows_with_expected_inverse": expected_inverse,
        "inverse_consistency": round(consistency, 4) if consistency is not None else None,
        "by_label": {label: dict(sorted(counts.items())) for label, counts in label_counts.items()},
        "inconsistent_examples": inconsistent_examples,
    }


def build_frame_specs(
    gt_rows: list[dict[str, Any]],
    geometries_by_scan: dict[str, dict[int, dict[str, Any]]],
) -> tuple[list[FrameSpec], dict[str, dict[str, FrameSpec]], dict[str, Any]]:
    specs = scan_frame_specs()
    pca_template_names: list[str] = []
    pca_specs_by_scan: dict[str, dict[str, FrameSpec]] = {}
    object_ids_by_scan: dict[str, set[int]] = defaultdict(set)
    for row in gt_rows:
        scan_id = str(row["scan_id"])
        object_ids_by_scan[scan_id].add(int(row["subject_id"]))
        object_ids_by_scan[scan_id].add(int(row["object_id"]))

    for scan_id, object_ids in object_ids_by_scan.items():
        scan_specs = pca_frame_specs(scan_id, geometries_by_scan.get(scan_id, {}), object_ids)
        pca_specs_by_scan[scan_id] = {spec.name: spec for spec in scan_specs}
        if scan_specs and not pca_template_names:
            pca_template_names = [spec.name for spec in scan_specs]

    for name in pca_template_names:
        representative = next(
            (scan_specs[name] for scan_specs in pca_specs_by_scan.values() if name in scan_specs),
            None,
        )
        if representative is not None:
            specs.append(
                FrameSpec(
                    name=name,
                    frame_family="room_pca",
                    left_axis=representative.left_axis,
                    front_axis=representative.front_axis,
                )
            )

    pca_ready_scans = sum(1 for scan_specs in pca_specs_by_scan.values() if scan_specs)
    return specs, pca_specs_by_scan, {
        "scan_count": len(object_ids_by_scan),
        "pca_ready_scans": pca_ready_scans,
        "pca_missing_scans": len(object_ids_by_scan) - pca_ready_scans,
    }


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def write_report(path: Path, manifest: dict[str, Any], frame_metrics: list[dict[str, Any]]) -> None:
    selected = manifest["selected_frame"]
    gate = manifest["gate"]
    inverse = manifest["inverse_pair_consistency"]
    lines = [
        "# Relative Horizontal Coordinate Audit",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This is a coordinate-frame semantics gate for the optional "
        "`relative_horizontal` expansion track. It is not source-prediction "
        "metric evidence and does not change the current H001 paper claim.",
        "",
        "## Selected Candidate Frame",
        "",
        markdown_table(
            ["Field", "Value"],
            [
                ["frame", selected["frame_name"]],
                ["family", selected["frame_family"]],
                ["macro strict purity", selected["macro_strict_purity"]],
                ["strict eligible share", selected["strict_eligible_share"]],
                ["macro sign-only purity", selected["macro_sign_only_purity"]],
                ["wrong-frame gap", gate["wrong_frame_gap"]],
            ],
        ),
        "",
        "## Per-Label Strict Purity",
        "",
        markdown_table(
            ["Label", "Purity", "Eligible", "Uncertain", "Contradiction"],
            [
                [
                    label,
                    selected["by_label"][label]["strict"]["purity"],
                    selected["by_label"][label]["strict"]["eligible"],
                    selected["by_label"][label]["strict"]["uncertain"],
                    selected["by_label"][label]["strict"]["contradiction"],
                ]
                for label in TARGET_LABELS
            ],
        ),
        "",
        "## Inverse-Pair Consistency",
        "",
        markdown_table(
            ["Item", "Value"],
            [
                ["rows with reverse annotation", inverse["rows_with_reverse_annotation"]],
                ["rows with expected inverse", inverse["rows_with_expected_inverse"]],
                ["inverse consistency", inverse["inverse_consistency"]],
            ],
        ),
        "",
        "## Gate Decision",
        "",
        markdown_table(
            ["Check", "Passed"],
            [[name, str(value).lower()] for name, value in gate["checks"].items()],
        ),
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    lines.extend(
        [
            "",
            "## Top Frame Candidates",
            "",
            markdown_table(
                [
                    "Rank",
                    "Frame",
                    "Family",
                    "Macro strict",
                    "Eligible share",
                    "Macro sign-only",
                ],
                [
                    [
                        idx + 1,
                        frame["frame_name"],
                        frame["frame_family"],
                        frame["macro_strict_purity"],
                        frame["overall"]["strict"]["eligible_share"],
                        frame["macro_sign_only_purity"],
                    ]
                    for idx, frame in enumerate(frame_metrics[:8])
                ],
            ),
            "",
            "## Interpretation",
            "",
        ]
    )
    if manifest["gate"]["passed"]:
        lines.append(
            "- The coordinate-frame gate passes as an audit result only; the next step is verifier policy and calibration design."
        )
    else:
        lines.append(
            "- The coordinate-frame gate does not yet support promoting `relative_horizontal` into the main claim."
        )
    lines.append(
        "- A failed or partial gate is useful: it prevents a broader claim from being built on coordinate convention artifacts."
    )
    lines.append("")
    ensure_dir(path.parent)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--dataset-root", type=Path, default=Path("local_dataset"))
    parser.add_argument(
        "--ground-truth-jsonl",
        type=Path,
        default=HARDENED_ROOT / "ground_truth.jsonl",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=EXPERIMENT_ROOT / "sources/relative_horizontal/coordinate_audit",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    dataset_root = args.dataset_root if args.dataset_root.is_absolute() else repo_root / args.dataset_root
    gt_path = args.ground_truth_jsonl if args.ground_truth_jsonl.is_absolute() else repo_root / args.ground_truth_jsonl
    out = args.out if args.out.is_absolute() else repo_root / args.out

    if not gt_path.exists():
        raise FileNotFoundError(f"missing_ground_truth_jsonl:{gt_path}")
    if not dataset_root.exists():
        raise FileNotFoundError(f"missing_dataset_root:{dataset_root}")

    gt_rows = load_relative_horizontal_gt(gt_path)
    scans = sorted({str(row["scan_id"]) for row in gt_rows})
    object_ids_by_scan: dict[str, set[int]] = defaultdict(set)
    for row in gt_rows:
        object_ids_by_scan[str(row["scan_id"])].add(int(row["subject_id"]))
        object_ids_by_scan[str(row["scan_id"])].add(int(row["object_id"]))

    geometries_by_scan: dict[str, dict[int, dict[str, Any]]] = {}
    geometry_warnings: list[str] = []
    geometry_errors: list[str] = []
    for scan_id in scans:
        geometries, warnings, errors = load_scan_geometries(dataset_root, scan_id)
        geometries_by_scan[scan_id] = geometries
        geometry_warnings.extend(warnings[:10])
        geometry_errors.extend(errors)

    frame_specs, pca_specs_by_scan, pca_summary = build_frame_specs(gt_rows, geometries_by_scan)
    frame_summaries: list[dict[str, Any]] = []
    selected_records: list[dict[str, Any]] = []
    aggregate_ambiguity: Counter[str] = Counter()
    records_by_frame_name: dict[str, list[dict[str, Any]]] = {}
    for frame in frame_specs:
        summary, records, ambiguity = summarize_frame(frame, gt_rows, geometries_by_scan, pca_specs_by_scan)
        frame_summaries.append(summary)
        records_by_frame_name[frame.name] = records
        aggregate_ambiguity.update(ambiguity)

    frame_summaries.sort(key=selected_frame_key, reverse=True)
    selected = frame_summaries[0]
    selected_records = records_by_frame_name[selected["frame_name"]]
    runner_up = frame_summaries[1] if len(frame_summaries) > 1 else None
    wrong_frame_gap = None
    if runner_up is not None and selected.get("macro_strict_purity") is not None:
        wrong_frame_gap = round(
            float(selected["macro_strict_purity"]) - float(runner_up["macro_strict_purity"]),
            4,
        )

    inverse = inverse_pair_consistency(gt_rows)
    per_label_purity = {
        label: selected["by_label"][label]["strict"]["purity"] for label in TARGET_LABELS
    }
    checks = {
        "macro_strict_purity_ge_0_80": bool(
            selected.get("macro_strict_purity") is not None
            and float(selected["macro_strict_purity"]) >= MIN_MACRO_PURITY
        ),
        "per_label_strict_purity_ge_0_75": all(
            value is not None and float(value) >= MIN_PER_LABEL_PURITY
            for value in per_label_purity.values()
        ),
        "strict_eligible_share_ge_0_50": bool(
            selected["overall"]["strict"]["eligible_share"] is not None
            and float(selected["overall"]["strict"]["eligible_share"]) >= MIN_STRICT_ELIGIBLE_SHARE
        ),
        "inverse_consistency_ge_0_85_when_available": bool(
            inverse["inverse_consistency"] is None
            or float(inverse["inverse_consistency"]) >= MIN_INVERSE_CONSISTENCY
        ),
        "wrong_frame_gap_ge_0_05": bool(
            wrong_frame_gap is not None and wrong_frame_gap >= MIN_WRONG_FRAME_GAP
        ),
        "geometry_inputs_complete": not geometry_errors,
    }
    blockers = [
        name
        for name, passed in checks.items()
        if not passed
    ]
    if blockers:
        blockers.extend(
            [
                "relative_horizontal_verifier_policy_not_frozen",
                "train_dev_calibration_not_built",
                "source_metrics_not_run",
                "bootstrap_ci_not_run",
                "failure_analysis_and_visual_audit_not_run",
            ]
        )
    status = (
        "relative_horizontal_coordinate_audit_passed_no_metric_execution"
        if not blockers
        else "relative_horizontal_coordinate_audit_blocked_no_metric_execution"
    )

    selected_payload = {
        "frame_name": selected["frame_name"],
        "frame_family": selected["frame_family"],
        "left_axis": selected["left_axis"],
        "front_axis": selected["front_axis"],
        "macro_strict_purity": selected["macro_strict_purity"],
        "macro_sign_only_purity": selected["macro_sign_only_purity"],
        "strict_eligible_share": selected["overall"]["strict"]["eligible_share"],
        "sign_only_eligible_share": selected["overall"]["sign_only"]["eligible_share"],
        "by_label": selected["by_label"],
        "ambiguity_counts": selected["ambiguity_counts"],
        "runner_up_frame_name": runner_up["frame_name"] if runner_up else None,
        "runner_up_macro_strict_purity": runner_up["macro_strict_purity"] if runner_up else None,
    }
    manifest = {
        "schema_version": "h001_relative_horizontal_coordinate_audit_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "current_families": list(CURRENT_FAMILIES),
            "candidate_family": TARGET_FAMILY,
            "metric_evidence": False,
            "paper_claim_promotion_allowed": False,
        },
        "inputs": {
            "ground_truth_jsonl": str(gt_path),
            "dataset_root": str(dataset_root),
            "geometry_source": "semseg_v2_obb_centroid_aabb",
        },
        "thresholds": {
            "min_margin_m": MIN_MARGIN_M,
            "margin_scale_of_mean_diag_xy": MARGIN_SCALE,
            "max_margin_m": MAX_MARGIN_M,
            "strong_overlap_ratio": STRONG_OVERLAP_RATIO,
            "conflicting_axis_ratio": CONFLICTING_AXIS_RATIO,
            "min_macro_purity": MIN_MACRO_PURITY,
            "min_per_label_purity": MIN_PER_LABEL_PURITY,
            "min_inverse_consistency": MIN_INVERSE_CONSISTENCY,
            "min_strict_eligible_share": MIN_STRICT_ELIGIBLE_SHARE,
            "min_wrong_frame_gap": MIN_WRONG_FRAME_GAP,
        },
        "scope": {
            "gt_rows": len(gt_rows),
            "scans": len(scans),
            "labels": dict(sorted(Counter(str(row["predicate_label"]) for row in gt_rows).items())),
            "frames_evaluated": len(frame_summaries),
            "pca_summary": pca_summary,
        },
        "selected_frame": selected_payload,
        "gate": {
            "passed": not blockers,
            "checks": checks,
            "wrong_frame_gap": wrong_frame_gap,
        },
        "inverse_pair_consistency": inverse,
        "ambiguity_counts_selected_frame": selected["ambiguity_counts"],
        "ambiguity_counts_all_frames": dict(sorted(aggregate_ambiguity.items())),
        "geometry": {
            "errors": geometry_errors,
            "warning_sample": geometry_warnings[:50],
        },
        "blockers": blockers,
        "next_gate_if_passed": "G1_geometry_status_policy_and_calibration_route",
        "next_gate_if_blocked": "Keep current three-family paper claim unchanged; inspect label/frame ambiguity before any broader claim.",
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "frame_metrics.json", {"frames": frame_summaries})
    write_json(
        out / "ambiguity_buckets.json",
        {
            "selected_frame": selected["ambiguity_counts"],
            "all_frames": dict(sorted(aggregate_ambiguity.items())),
            "inverse_pair_consistency": inverse,
        },
    )
    write_jsonl(out / "records.jsonl", selected_records)
    write_report(out / "report.md", manifest, frame_summaries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
