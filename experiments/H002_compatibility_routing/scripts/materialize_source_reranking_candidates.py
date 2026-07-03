#!/usr/bin/env python3
"""Materialize source-wide H002 views for source reranking.

This script writes source-wide C_e inputs for VL-SAT/Open3DSG validation source
predictions. It does not score C_e and does not run reranking metrics.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_source_reranking_materialization_v1"
EXPECTED_PROTOCOL_STATUS = (
    "h002_compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory_ready"
)
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_source_reranking_docker_materialization_after_protocol"

FAMILY_PREDICATES = {
    "proximity": ["close by"],
    "relative_horizontal": ["left", "right", "front", "behind"],
    "relative_vertical": ["higher than", "lower than"],
    "size_relative": ["bigger than", "smaller than"],
    "support_contact": ["standing on", "lying on", "supported by"],
}
PREDICATE_TO_FAMILY = {
    predicate: family
    for family, predicates in FAMILY_PREDICATES.items()
    for predicate in predicates
}
PRIMARY_SUCCESS_FAMILIES = {"relative_vertical", "size_relative"}
DIAGNOSTIC_FAMILIES = {"support_contact"}

BLOCKED_MODEL_SAFE_FEATURE_KEYS = {
    "candidate_bucket",
    "construction_bucket",
    "counterfactual",
    "distance_bucket",
    "exact_match",
    "geometry_status",
    "gt_match",
    "h001",
    "p_geom_valid",
    "rank",
    "score",
    "source_score",
    "target_y",
    "verification_status",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--protocol-dir",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "compatibility_dataset_v3_source_reranking_materialization_protocol_after_source_inventory"
        ),
    )
    parser.add_argument(
        "--inventory-dir",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "compatibility_dataset_v3_source_reranking_source_inventory_after_protocol_plan"
        ),
    )
    parser.add_argument("--subset-dir", type=Path, default=Path("local_dataset/3DSSG_subset"))
    parser.add_argument("--scan-dir", type=Path, default=Path("local_dataset/3RScan/scans"))
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def vector3(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) < 3:
        return None
    return [float(safe_float(value[0], 0.0)), float(safe_float(value[1], 0.0)), float(safe_float(value[2], 0.0))]


def relationship_predicate(rel: Any) -> str:
    if isinstance(rel, list) and len(rel) >= 4:
        return str(rel[3])
    if isinstance(rel, dict):
        return str(rel.get("predicate") or rel.get("relationship") or rel.get("relation") or "unknown")
    return "unknown"


def relationship_subject(rel: Any) -> int | None:
    if isinstance(rel, list) and len(rel) >= 2:
        return int(rel[0])
    if isinstance(rel, dict):
        value = rel.get("subject_id") or rel.get("subject") or rel.get("source_id")
        return int(value) if value is not None else None
    return None


def relationship_object(rel: Any) -> int | None:
    if isinstance(rel, list) and len(rel) >= 2:
        return int(rel[1])
    if isinstance(rel, dict):
        value = rel.get("object_id") or rel.get("object") or rel.get("target_id")
        return int(value) if value is not None else None
    return None


def scan_relationships(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        scans = data.get("scans", [])
    elif isinstance(data, list):
        scans = data
    else:
        scans = []
    return scans if isinstance(scans, list) else []


def build_gt_index(subset_dir: Path) -> tuple[set[tuple[str, int, int, str]], dict[tuple[str, int, int, str], set[str]]]:
    data = read_json(subset_dir / "relationships_validation.json")
    exact: set[tuple[str, int, int, str]] = set()
    by_family: dict[tuple[str, int, int, str], set[str]] = defaultdict(set)
    for scan in scan_relationships(data):
        scan_id = str(scan.get("scan"))
        for rel in scan.get("relationships", []):
            predicate = relationship_predicate(rel)
            family = PREDICATE_TO_FAMILY.get(predicate)
            subject_id = relationship_subject(rel)
            object_id = relationship_object(rel)
            if family is None or subject_id is None or object_id is None:
                continue
            exact.add((scan_id, subject_id, object_id, predicate))
            by_family[(scan_id, subject_id, object_id, family)].add(predicate)
    return exact, by_family


def obb_record(group: dict[str, Any]) -> dict[str, Any] | None:
    obb = group.get("obb")
    if not isinstance(obb, dict):
        return None
    centroid = vector3(obb.get("centroid"))
    lengths = vector3(obb.get("axesLengths"))
    if centroid is None or lengths is None:
        return None
    axes_raw = obb.get("normalizedAxes")
    if isinstance(axes_raw, list) and len(axes_raw) >= 9:
        axes = [
            [float(safe_float(axes_raw[0], 0.0)), float(safe_float(axes_raw[1], 0.0)), float(safe_float(axes_raw[2], 0.0))],
            [float(safe_float(axes_raw[3], 0.0)), float(safe_float(axes_raw[4], 0.0)), float(safe_float(axes_raw[5], 0.0))],
            [float(safe_float(axes_raw[6], 0.0)), float(safe_float(axes_raw[7], 0.0)), float(safe_float(axes_raw[8], 0.0))],
        ]
    else:
        axes = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    half_extents = [
        sum(abs(axes[axis_index][coord]) * max(lengths[axis_index], 1e-9) / 2.0 for axis_index in range(3))
        for coord in range(3)
    ]
    mins = [centroid[i] - half_extents[i] for i in range(3)]
    maxs = [centroid[i] + half_extents[i] for i in range(3)]
    return {
        "centroid": centroid,
        "axes_lengths": lengths,
        "aabb_min": mins,
        "aabb_max": maxs,
        "volume": max(lengths[0] * lengths[1] * lengths[2], 1e-9),
    }


def semseg_object_map(scan_dir: Path, scan_id: str) -> dict[int, dict[str, Any]]:
    data = read_json(scan_dir / scan_id / "semseg.v2.json")
    out: dict[int, dict[str, Any]] = {}
    for group in data.get("segGroups", []):
        object_id = group.get("objectId", group.get("id"))
        if object_id is None:
            continue
        record = obb_record(group)
        if record is not None:
            out[int(object_id)] = record
    return out


def interval_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))


def pair_geometry(subject: dict[str, Any], obj: dict[str, Any]) -> dict[str, float]:
    sc = subject["centroid"]
    oc = obj["centroid"]
    sx0, sy0, sz0 = subject["aabb_min"]
    sx1, sy1, sz1 = subject["aabb_max"]
    ox0, oy0, oz0 = obj["aabb_min"]
    ox1, oy1, oz1 = obj["aabb_max"]

    dx = sc[0] - oc[0]
    dy = sc[1] - oc[1]
    dz = sc[2] - oc[2]
    xy_distance = math.sqrt(dx * dx + dy * dy)
    center_distance = math.sqrt(dx * dx + dy * dy + dz * dz)

    subject_width = max(sx1 - sx0, 1e-9)
    subject_depth = max(sy1 - sy0, 1e-9)
    subject_height = max(sz1 - sz0, 1e-9)
    object_width = max(ox1 - ox0, 1e-9)
    object_depth = max(oy1 - oy0, 1e-9)
    object_height = max(oz1 - oz0, 1e-9)
    subject_area = max(subject_width * subject_depth, 1e-9)
    object_area = max(object_width * object_depth, 1e-9)
    pair_scale = max(subject_width, subject_depth, subject_height, object_width, object_depth, object_height, 1e-9)

    overlap_x = interval_overlap(sx0, sx1, ox0, ox1)
    overlap_y = interval_overlap(sy0, sy1, oy0, oy1)
    overlap_z = interval_overlap(sz0, sz1, oz0, oz1)
    overlap_xy_area = overlap_x * overlap_y
    min_area = max(min(subject_area, object_area), 1e-9)
    max_area = max(max(subject_area, object_area), 1e-9)
    min_height = max(min(subject_height, object_height), 1e-9)

    return {
        "center_delta_x": dx,
        "center_delta_y": dy,
        "center_delta_z": dz,
        "abs_center_delta_x": abs(dx),
        "abs_center_delta_y": abs(dy),
        "abs_center_delta_z": abs(dz),
        "xy_center_distance": xy_distance,
        "center_distance_3d": center_distance,
        "normalized_center_delta_x": dx / max(subject_width, object_width, 1e-9),
        "normalized_center_delta_y": dy / max(subject_depth, object_depth, 1e-9),
        "normalized_center_delta_z": dz / max(subject_height, object_height, 1e-9),
        "normalized_xy_center_distance": xy_distance / pair_scale,
        "normalized_center_distance_3d": center_distance / pair_scale,
        "subject_bottom_z": sz0,
        "subject_top_z": sz1,
        "object_bottom_z": oz0,
        "object_top_z": oz1,
        "surface_gap_subject_bottom_to_object_top": sz0 - oz1,
        "abs_surface_gap_subject_bottom_to_object_top": abs(sz0 - oz1),
        "subject_height": subject_height,
        "object_height": object_height,
        "subject_width": subject_width,
        "object_width": object_width,
        "subject_depth": subject_depth,
        "object_depth": object_depth,
        "subject_footprint_area": subject_area,
        "object_footprint_area": object_area,
        "subject_volume": subject["volume"],
        "object_volume": obj["volume"],
        "log_volume_ratio_s_over_o": math.log(max(subject["volume"], 1e-9) / max(obj["volume"], 1e-9)),
        "log_height_ratio_s_over_o": math.log(subject_height / object_height),
        "log_footprint_area_ratio_s_over_o": math.log(subject_area / object_area),
        "xy_overlap_area": overlap_xy_area,
        "xy_overlap_min_ratio": overlap_xy_area / min_area,
        "xy_overlap_max_ratio": overlap_xy_area / max_area,
        "vertical_overlap_ratio": overlap_z / min_height,
        "support_contact_likelihood_proxy": (overlap_xy_area / min_area) / (1.0 + abs(sz0 - oz1)),
        "subject_vertical_extent_ratio": subject_height / max(subject_width, subject_depth, subject_height, 1e-9),
        "object_vertical_extent_ratio": object_height / max(object_width, object_depth, object_height, 1e-9),
    }


def family_g_e(family: str, geometry: dict[str, float]) -> tuple[str, list[str], dict[str, float]]:
    if family == "proximity":
        names = [
            "xy_center_distance",
            "center_distance_3d",
            "normalized_xy_center_distance",
            "normalized_center_distance_3d",
            "subject_volume",
            "object_volume",
        ]
        policy = "predicate_independent_proximity_from_3rscan_obb_centroids"
    elif family == "relative_horizontal":
        names = [
            "center_delta_x",
            "center_delta_y",
            "abs_center_delta_x",
            "abs_center_delta_y",
            "xy_center_distance",
            "normalized_center_delta_x",
            "normalized_center_delta_y",
        ]
        policy = "dataset_world_xy_reference_frame_from_3rscan_obb_centroids"
    elif family == "relative_vertical":
        names = [
            "center_delta_z",
            "abs_center_delta_z",
            "normalized_center_delta_z",
            "subject_bottom_z",
            "subject_top_z",
            "object_bottom_z",
            "object_top_z",
        ]
        policy = "dataset_world_z_signed_vertical_from_3rscan_obb_aabb"
    elif family == "size_relative":
        names = [
            "log_volume_ratio_s_over_o",
            "log_height_ratio_s_over_o",
            "log_footprint_area_ratio_s_over_o",
            "subject_volume",
            "object_volume",
            "subject_height",
            "object_height",
            "subject_footprint_area",
            "object_footprint_area",
        ]
        policy = "predicate_independent_size_ratios_from_3rscan_obb"
    else:
        names = [
            "surface_gap_subject_bottom_to_object_top",
            "abs_surface_gap_subject_bottom_to_object_top",
            "xy_overlap_min_ratio",
            "xy_overlap_max_ratio",
            "support_contact_likelihood_proxy",
            "center_delta_z",
            "subject_vertical_extent_ratio",
            "object_vertical_extent_ratio",
        ]
        policy = "obb_support_contact_proxy_from_gap_overlap_vertical_order_and_pose"
    return policy, names, {name: geometry[name] for name in names}


def h2_relation_status(family: str, predicate: str, geometry: dict[str, float]) -> tuple[str, str]:
    eps = 1e-6
    if family == "relative_vertical":
        dz = geometry["center_delta_z"]
        if abs(dz) <= eps:
            return "uncertain", "vertical_delta_near_zero"
        ok = (predicate == "higher than" and dz > 0) or (predicate == "lower than" and dz < 0)
        return ("satisfied" if ok else "violated"), "signed_center_delta_z"
    if family == "size_relative":
        ratio = geometry["log_volume_ratio_s_over_o"]
        if abs(ratio) <= 0.05:
            return "uncertain", "volume_ratio_near_tie"
        ok = (predicate == "bigger than" and ratio > 0) or (predicate == "smaller than" and ratio < 0)
        return ("satisfied" if ok else "violated"), "signed_log_volume_ratio"
    if family == "relative_horizontal":
        dx = geometry["center_delta_x"]
        dy = geometry["center_delta_y"]
        if predicate in {"left", "right"}:
            if abs(dx) <= eps:
                return "uncertain", "x_delta_near_zero"
            ok = (predicate == "right" and dx > 0) or (predicate == "left" and dx < 0)
            return ("satisfied" if ok else "violated"), "dataset_world_x_sign_caveated"
        if abs(dy) <= eps:
            return "uncertain", "y_delta_near_zero"
        ok = (predicate == "front" and dy > 0) or (predicate == "behind" and dy < 0)
        return ("satisfied" if ok else "violated"), "dataset_world_y_sign_caveated"
    if family == "proximity":
        d = geometry["normalized_center_distance_3d"]
        if d <= 1.0:
            return "satisfied", "normalized_distance_threshold_proxy"
        if d <= 1.5:
            return "uncertain", "normalized_distance_mid_band_proxy"
        return "violated", "normalized_distance_threshold_proxy"
    return "diagnostic_only", "support_contact_hidden_h001_or_diagnostic_only"


def load_source_paths(inventory_dir: Path) -> list[dict[str, Any]]:
    rows = read_csv(inventory_dir / "join_key_audit.csv")
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("adapter_predictions_exists") != "True" or row.get("geometry_verification_exists") != "True":
            continue
        out.append(
            {
                "source_id": row["source_id"],
                "adapter_predictions": Path(row["adapter_predictions"]),
                "geometry_verification": Path(row["geometry_verification"]),
                "expected_rows_in_scope": int(float(row.get("source_prediction_rows_in_scope", 0))),
            }
        )
    return out


def validate_protocol(protocol_dir: Path, inventory_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    summary_path = protocol_dir / "summary.json"
    if not summary_path.exists():
        return [{"error_type": "missing_protocol_summary", "path": str(summary_path)}]
    summary = read_json(summary_path)
    if summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "protocol_validation_errors_present", "actual": summary.get("validation_errors")})
    decision = summary.get("decision", {})
    for key in ["metrics_run", "official_test_usage", "paper_metric_promoted"]:
        if decision.get(key) is not False:
            errors.append({"error_type": "unexpected_protocol_boundary", "key": key, "actual": decision.get(key)})
    if not (inventory_dir / "join_key_audit.csv").exists():
        errors.append({"error_type": "missing_inventory_join_key_audit", "path": str(inventory_dir / "join_key_audit.csv")})
    return errors


def blocked_feature_hits(row: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    stack: list[tuple[str, Any]] = [("feature_blocks", row.get("feature_blocks", {}))]
    while stack:
        prefix, value = stack.pop()
        if isinstance(value, dict):
            for key, child in value.items():
                path = f"{prefix}.{key}"
                lower = key.lower()
                if any(token in lower for token in BLOCKED_MODEL_SAFE_FEATURE_KEYS):
                    hits.append(path)
                stack.append((path, child))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                stack.append((f"{prefix}[{index}]", child))
    return hits


def get_edge(prediction: dict[str, Any]) -> tuple[int, int, str, str]:
    edge = prediction.get("edge", {})
    predicate = prediction.get("predicate", {})
    subject_id = int(edge.get("subject_id"))
    object_id = int(edge.get("object_id"))
    subject_label = str(edge.get("subject_label") or "unknown_subject")
    object_label = str(edge.get("object_label") or "unknown_object")
    _ = predicate
    return subject_id, object_id, subject_label, object_label


def materialize(
    repo_root: Path,
    source_paths: list[dict[str, Any]],
    subset_dir: Path,
    scan_dir: Path,
    out: Path,
) -> dict[str, Any]:
    exact_gt, family_gt = build_gt_index(subset_dir)
    semseg_cache: dict[str, dict[int, dict[str, Any]]] = {}
    errors: list[dict[str, Any]] = []
    counts = Counter()
    family_counts = Counter()
    predicate_counts = Counter()
    source_family_counts = Counter()
    gt_exact_counts = Counter()
    h2_status_counts = Counter()
    h001_status_counts = Counter()
    source_expected: dict[str, int] = {}

    paths = {
        "source_candidates": out / "source_candidates.jsonl",
        "model_safe_ce_view": out / "model_safe_ce_view.jsonl",
        "model_safe_geometry_only_view": out / "model_safe_geometry_only_view.jsonl",
        "source_rank_view": out / "source_rank_view.jsonl",
        "hidden_metric_manifest": out / "hidden_metric_manifest.jsonl",
    }
    handles = {name: path.open("w", encoding="utf-8") for name, path in paths.items()}
    seen_candidate_ids: set[str] = set()

    try:
        for source in source_paths:
            source_id = str(source["source_id"])
            adapter_path = resolve(repo_root, source["adapter_predictions"])
            geometry_path = resolve(repo_root, source["geometry_verification"])
            source_expected[source_id] = int(source["expected_rows_in_scope"])
            source_in_scope = 0
            with adapter_path.open("r", encoding="utf-8") as pred_handle, geometry_path.open("r", encoding="utf-8") as geom_handle:
                for line_number, (pred_line, geom_line) in enumerate(zip(pred_handle, geom_handle), start=1):
                    prediction = json.loads(pred_line)
                    verification = json.loads(geom_line)
                    if prediction.get("prediction_id") != verification.get("prediction_id"):
                        errors.append(
                            {
                                "error_type": "prediction_geometry_id_mismatch",
                                "source_id": source_id,
                                "line": line_number,
                                "prediction_id": prediction.get("prediction_id"),
                                "geometry_prediction_id": verification.get("prediction_id"),
                            }
                        )
                        continue
                    predicate = str(prediction.get("predicate", {}).get("predicate_label") or "")
                    family = PREDICATE_TO_FAMILY.get(predicate)
                    if family is None:
                        continue

                    scan_id = str(prediction.get("scan_id"))
                    subject_id, object_id, subject_label, object_label = get_edge(prediction)
                    if scan_id not in semseg_cache:
                        try:
                            semseg_cache[scan_id] = semseg_object_map(scan_dir, scan_id)
                        except Exception as exc:  # noqa: BLE001
                            errors.append({"error_type": "semseg_read_error", "scan_id": scan_id, "message": str(exc)})
                            semseg_cache[scan_id] = {}
                    obbs = semseg_cache[scan_id]
                    if subject_id not in obbs or object_id not in obbs:
                        errors.append(
                            {
                                "error_type": "missing_obb_for_source_prediction",
                                "source_id": source_id,
                                "prediction_id": prediction.get("prediction_id"),
                                "scan_id": scan_id,
                                "subject_id": subject_id,
                                "object_id": object_id,
                            }
                        )
                        continue

                    geometry = pair_geometry(obbs[subject_id], obbs[object_id])
                    policy, feature_names, feature_vector = family_g_e(family, geometry)
                    h2_status, h2_status_source = h2_relation_status(family, predicate, geometry)
                    scores = prediction.get("scores", {})
                    ranks = prediction.get("ranks", {})
                    calibration = verification.get("calibration", {})
                    h001_verification = verification.get("verification", {})
                    h001_status = str(verification.get("verification_status") or h001_verification.get("verification_status") or "missing")
                    h001_p_geom_valid = calibration.get("p_geom_valid")
                    h001_consistency = verification.get("consistency_score")
                    candidate_id = f"source_reranking::{source_id}::{prediction.get('prediction_id')}"
                    if candidate_id in seen_candidate_ids:
                        errors.append({"error_type": "duplicate_candidate_id", "candidate_id": candidate_id})
                        continue
                    seen_candidate_ids.add(candidate_id)

                    exact_match = (scan_id, subject_id, object_id, predicate) in exact_gt
                    same_family_gt = sorted(family_gt.get((scan_id, subject_id, object_id, family), set()))
                    candidate_role = (
                        "primary_success" if family in PRIMARY_SUCCESS_FAMILIES
                        else "diagnostic" if family in DIAGNOSTIC_FAMILIES
                        else "control_or_caveated"
                    )
                    row_identity = {
                        "candidate_id": candidate_id,
                        "source_id": source_id,
                        "prediction_id": prediction.get("prediction_id"),
                        "scan_id": scan_id,
                        "subgraph_id": prediction.get("subgraph_id"),
                        "subject_id": subject_id,
                        "object_id": object_id,
                        "predicate_label": predicate,
                        "route_family": family,
                        "split": "official_validation",
                    }
                    t_e = {
                        "predicate_text": predicate,
                        "predicate_label": predicate,
                        "route_family": family,
                        "subject_class_label": subject_label,
                        "object_class_label": object_label,
                        "predicate_family_embedding_key": family,
                    }
                    g_e = {
                        "g_e_available": True,
                        "g_e_feature_names": feature_names,
                        "g_e_feature_vector": feature_vector,
                        "g_e_feature_mask": {name: True for name in feature_names},
                        "geometry_reference_policy": policy,
                    }
                    ce_row = {
                        "schema_version": SCHEMA_VERSION,
                        **row_identity,
                        "candidate_role": candidate_role,
                        "feature_use_policy": {
                            "main_C_e_allowed_blocks": ["T_e", "G_e"],
                            "disallowed_for_C_e": ["Z_e", "hidden_metric_labels", "H001_p_geom_valid"],
                            "row_identity_not_features": [
                                "candidate_id",
                                "source_id",
                                "prediction_id",
                                "scan_id",
                                "subgraph_id",
                                "subject_id",
                                "object_id",
                                "predicate_label",
                                "route_family",
                            ],
                        },
                        "feature_blocks": {
                            "T_e": t_e,
                            "G_e": g_e,
                        },
                    }
                    hits = blocked_feature_hits(ce_row)
                    if hits:
                        errors.append({"error_type": "model_safe_ce_blocked_feature_hit", "candidate_id": candidate_id, "hits": hits})

                    source_candidate = {
                        "schema_version": f"{SCHEMA_VERSION}_source_candidate",
                        **row_identity,
                        "candidate_role": candidate_role,
                        "predicate_vocab": prediction.get("predicate", {}).get("predicate_vocab"),
                        "task_mode": prediction.get("task_mode"),
                        "baseline_name": prediction.get("baseline_name"),
                        "baseline_run_id": prediction.get("baseline_run_id"),
                        "record_type": "source_candidate_identity_only",
                    }
                    geometry_only = {
                        "schema_version": f"{SCHEMA_VERSION}_geometry_only",
                        **row_identity,
                        "candidate_role": candidate_role,
                        "feature_use_policy": {
                            "allowed_blocks": ["G_e"],
                            "diagnostic_only": True,
                        },
                        "feature_blocks": {"G_e": g_e},
                    }
                    source_rank = {
                        "schema_version": f"{SCHEMA_VERSION}_source_rank",
                        **row_identity,
                        "candidate_role": candidate_role,
                        "Z_e": {
                            "source_id": source_id,
                            "ranking_score": safe_float(scores.get("ranking_score"), None),
                            "predicate_score": safe_float(scores.get("predicate_score"), None),
                            "predicate_rank_for_pair": ranks.get("predicate_rank_for_pair"),
                            "semantic_rank_in_subgraph": ranks.get("semantic_rank_in_subgraph"),
                            "ranking_score_type": scores.get("ranking_score_type"),
                            "predicate_score_type": scores.get("predicate_score_type"),
                        },
                        "feature_use_policy": {
                            "allowed_stage": "reranking_only",
                            "disallowed_stage": "C_e_scoring",
                        },
                    }
                    hidden = {
                        "schema_version": f"{SCHEMA_VERSION}_hidden_metric",
                        **row_identity,
                        "candidate_role": candidate_role,
                        "gt_exact_match": exact_match,
                        "gt_family_match": bool(same_family_gt),
                        "gt_predicates_for_directed_pair_family": same_family_gt,
                        "h2_violation_checkable": family not in DIAGNOSTIC_FAMILIES,
                        "h2_relation_status": h2_status,
                        "h2_relation_status_source": h2_status_source,
                        "h001_geometry_checkable": bool(verification.get("quality", {}).get("geometry_checkable")),
                        "h001_verification_status": h001_status,
                        "h001_p_geom_valid": safe_float(h001_p_geom_valid, None),
                        "h001_consistency_score": safe_float(h001_consistency, None),
                        "h001_reason_codes": h001_verification.get("reason_codes", []),
                        "metric_only": True,
                    }

                    handles["source_candidates"].write(json.dumps(source_candidate, ensure_ascii=False, sort_keys=True) + "\n")
                    handles["model_safe_ce_view"].write(json.dumps(ce_row, ensure_ascii=False, sort_keys=True) + "\n")
                    handles["model_safe_geometry_only_view"].write(json.dumps(geometry_only, ensure_ascii=False, sort_keys=True) + "\n")
                    handles["source_rank_view"].write(json.dumps(source_rank, ensure_ascii=False, sort_keys=True) + "\n")
                    handles["hidden_metric_manifest"].write(json.dumps(hidden, ensure_ascii=False, sort_keys=True) + "\n")

                    source_in_scope += 1
                    counts["rows"] += 1
                    counts[f"source::{source_id}"] += 1
                    family_counts[family] += 1
                    predicate_counts[f"{family}|{predicate}"] += 1
                    source_family_counts[f"{source_id}|{family}"] += 1
                    gt_exact_counts[f"{family}|{int(exact_match)}"] += 1
                    h2_status_counts[f"{family}|{h2_status}"] += 1
                    h001_status_counts[f"{family}|{h001_status}"] += 1

            if source_in_scope != source_expected[source_id]:
                errors.append(
                    {
                        "error_type": "source_in_scope_count_mismatch",
                        "source_id": source_id,
                        "actual": source_in_scope,
                        "expected": source_expected[source_id],
                    }
                )
    finally:
        for handle in handles.values():
            handle.close()

    primary_rows = sum(count for family, count in family_counts.items() if family in PRIMARY_SUCCESS_FAMILIES)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "h002_source_reranking_materialization_ready" if not errors else "h002_source_reranking_materialization_errors",
        "validation_errors": len(errors),
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "source_reranking_metrics_run": False,
        "paper_metric_produced": False,
        "paper_metric_promoted": False,
        "source_wide_Ce_materialization_done": not errors,
        "input_artifacts": {
            "source_inventory": repo_rel(repo_root, source_paths[0]["adapter_predictions"].parent if source_paths else out),
            "validation_gt": repo_rel(repo_root, subset_dir / "relationships_validation.json"),
            "scan_dir": repo_rel(repo_root, scan_dir),
        },
        "output_artifacts": {name: repo_rel(repo_root, path) for name, path in paths.items()},
        "row_counts": {
            "total_rows": counts["rows"],
            "primary_success_family_rows": primary_rows,
            "source_counts": {key.removeprefix("source::"): value for key, value in sorted(counts.items()) if key.startswith("source::")},
            "family_counts": dict(sorted(family_counts.items())),
            "predicate_counts": dict(sorted(predicate_counts.items())),
            "source_family_counts": dict(sorted(source_family_counts.items())),
            "gt_exact_counts": dict(sorted(gt_exact_counts.items())),
            "h2_status_counts": dict(sorted(h2_status_counts.items())),
            "h001_status_counts": dict(sorted(h001_status_counts.items())),
        },
        "boundary": {
            "model_safe_ce_allowed_blocks": ["T_e", "G_e"],
            "source_rank_view_stage": "reranking_only",
            "hidden_metric_manifest_stage": "metric_only",
            "support_contact_success_aggregation": "excluded_diagnostic",
            "h001_p_geom_valid_stage": "hidden_metric_or_control_only",
            "C_e_uses_Z_e": False,
        },
        "next_todo": "compatibility_dataset_v3_source_reranking_docker_materialization_schema_audit_after_materialization",
    }
    write_json(out / "row_manifest.json", manifest)
    write_jsonl(out / "validation_errors.jsonl", errors)
    return manifest


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    protocol_dir = resolve(repo_root, args.protocol_dir)
    inventory_dir = resolve(repo_root, args.inventory_dir)
    subset_dir = resolve(repo_root, args.subset_dir)
    scan_dir = resolve(repo_root, args.scan_dir)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    validation_errors = validate_protocol(protocol_dir, inventory_dir)
    source_paths = load_source_paths(inventory_dir)
    if not source_paths:
        validation_errors.append({"error_type": "no_source_paths_loaded"})
    if validation_errors:
        write_json(out / "row_manifest.json", {"schema_version": SCHEMA_VERSION, "status": "h002_source_reranking_materialization_errors", "validation_errors": len(validation_errors)})
        write_jsonl(out / "validation_errors.jsonl", validation_errors)
        print(json.dumps({"status": "errors", "validation_errors": len(validation_errors)}, ensure_ascii=False, indent=2))
        return 1

    manifest = materialize(repo_root, source_paths, subset_dir, scan_dir, out)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if manifest.get("validation_errors") == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
