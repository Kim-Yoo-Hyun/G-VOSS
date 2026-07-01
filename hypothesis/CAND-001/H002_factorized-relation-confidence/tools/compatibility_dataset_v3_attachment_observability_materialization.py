#!/usr/bin/env python3
"""Materialize model-safe R7 attachment observability rows."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_materialization_plan"
DEFAULT_SOURCE_INVENTORY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_source_inventory"
DEFAULT_INGESTION_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_label_ingestion_v1"
DEFAULT_PACKET_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_packet_materialization_v1"
DEFAULT_CANDIDATE_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_candidate_mining_v1"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_materialization"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_attachment_observability_materialization_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_attachment_observability_materialization"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_attachment_observability_materialization_v1"
STATUS_READY = "h002_compatibility_dataset_v3_attachment_observability_materialization_ready_for_schema_shortcut_audit"
STATUS_ERROR = "h002_compatibility_dataset_v3_attachment_observability_materialization_input_errors"
SELECTED_PATH = "materialized_r7_gq_separated_source_target_hidden_control_views"
NEXT_TODO = "compatibility_dataset_v3_attachment_observability_schema_shortcut_audit"

PRIMARY_PREDICATES = {"attached to", "hanging on"}
DIAGNOSTIC_PREDICATES = {"connected to"}
TARGET_PREDICATES = PRIMARY_PREDICATES | DIAGNOSTIC_PREDICATES

ANCHOR_SURFACE_LABELS = {
    "wall",
    "ceiling",
    "shelf",
    "cabinet",
    "door",
    "window",
    "rack",
    "rail",
    "curtain",
    "blinds",
}
DEVICE_CONNECTOR_LABELS = {
    "cable",
    "cord",
    "wire",
    "pipe",
    "hose",
    "plug",
    "socket",
    "outlet",
    "switch",
    "lamp",
    "light",
    "heater",
    "radiator",
    "sink",
    "faucet",
    "shower",
    "toilet",
    "tv",
    "television",
    "monitor",
}
FORBIDDEN_MODEL_SAFE_KEYS = {
    "candidate_id",
    "packet_request_id",
    "packet_id",
    "query_id",
    "query_id_hidden",
    "scan_id",
    "subgraph_id",
    "subject_id",
    "object_id",
    "directed_pair_id",
    "prediction_id",
    "source_score",
    "source_rank",
    "semantic_score_norm_hidden",
    "semantic_rank_hidden",
    "rank_band_hidden",
    "label_match_status_hidden",
    "matched_predicates_hidden",
    "selection_proxy_role_hidden",
    "selection_route_hidden",
    "cell_id_hidden",
    "review_relation_reliability",
    "review_geometry_support",
    "review_coverage",
    "review_endpoint_identity",
    "review_uncertainty",
    "review_notes",
    "p_obs_target",
    "p_rel_target",
    "primary_relation_binary_target",
    "compatibility_binary_target",
    "geometry_support_binary_target",
    "p_geom_valid",
}
FORBIDDEN_MODEL_SAFE_SUBSTRINGS = (
    "_hidden",
    "_target",
    "review_",
    "packet_",
    "query_",
    "source_",
    "scan_id",
    "subject_id",
    "object_id",
    "path",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not rows:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def bool01(value: Any) -> int:
    return 1 if bool(value) else 0


def finite(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(out):
        return default
    return out


def contains_any(label: str | None, words: set[str]) -> bool:
    text = (label or "").lower()
    return any(word in text for word in words)


def validate_inputs(plan_summary: dict[str, Any], source_summary: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})
    if source_summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_inventory_validation_errors_present", "actual": source_summary.get("validation_errors")})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_model", "posterior_smoke_allowed"]:
        if plan_summary.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": plan_summary.get("boundary", {}).get(key)})
    required = [
        args.source_inventory_dir / "packet_reuse_inventory_rows.jsonl",
        args.ingestion_dir / "ingested_rows.jsonl",
        args.packet_dir / "label_ready_manifest.jsonl",
        args.candidate_dir / "candidate_rows_internal.jsonl",
    ]
    for path in required:
        if not path.exists():
            errors.append({"error_type": "missing_required_input", "path": rel_path(path)})
    return errors


def semseg_objects(scan_id: str, scan_root: Path, cache: dict[str, dict[int, dict[str, Any]]]) -> dict[int, dict[str, Any]]:
    if scan_id in cache:
        return cache[scan_id]
    path = scan_root / scan_id / "semseg.v2.json"
    objects: dict[int, dict[str, Any]] = {}
    if not path.exists():
        cache[scan_id] = objects
        return objects
    payload = read_json(path)
    for group in payload.get("segGroups", []):
        oid = group.get("objectId", group.get("id"))
        if oid is None:
            continue
        try:
            object_id = int(oid)
        except (TypeError, ValueError):
            continue
        objects[object_id] = group
    cache[scan_id] = objects
    return objects


def obb_aabb(group: dict[str, Any] | None) -> dict[str, Any]:
    if not group:
        return {"available": False}
    obb = group.get("obb") or {}
    center = obb.get("centroid") or []
    lengths = obb.get("axesLengths") or []
    axes = obb.get("normalizedAxes") or []
    if len(center) != 3 or len(lengths) != 3:
        return {"available": False}
    if len(axes) != 9:
        axes = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    half = [0.0, 0.0, 0.0]
    # 3RScan stores three normalized axes flattened as x,y,z triples.
    for axis_idx in range(3):
        length = abs(finite(lengths[axis_idx]))
        axis = [finite(axes[axis_idx * 3 + dim]) for dim in range(3)]
        for dim in range(3):
            half[dim] += 0.5 * abs(axis[dim]) * length
    c = [finite(value) for value in center]
    mins = [c[dim] - half[dim] for dim in range(3)]
    maxs = [c[dim] + half[dim] for dim in range(3)]
    ext = [maxs[dim] - mins[dim] for dim in range(3)]
    normal = group.get("dominantNormal") or []
    normal_z_abs = abs(finite(normal[2])) if len(normal) >= 3 else 0.0
    xy_area = max(ext[0], 0.0) * max(ext[1], 0.0)
    volume = xy_area * max(ext[2], 0.0)
    return {
        "available": True,
        "center": c,
        "min": mins,
        "max": maxs,
        "extent": ext,
        "xy_area": xy_area,
        "volume": volume,
        "normal_z_abs": normal_z_abs,
        "thinness": min(ext) / max(max(ext), 1e-9),
        "vertical_plane_proxy": 1 if normal_z_abs < 0.35 else 0,
        "horizontal_plane_proxy": 1 if normal_z_abs > 0.75 else 0,
        "segment_count": len(group.get("segments") or []),
    }


def interval_gap(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    if a_max < b_min:
        return b_min - a_max
    if b_max < a_min:
        return a_min - b_max
    return 0.0


def interval_overlap(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))


def geometry_features(subject_group: dict[str, Any] | None, object_group: dict[str, Any] | None) -> dict[str, Any]:
    subj = obb_aabb(subject_group)
    obj = obb_aabb(object_group)
    if not subj.get("available") or not obj.get("available"):
        return {
            "g_geometry_available": 0,
            "g_center_distance_3d": 0.0,
            "g_center_distance_xy": 0.0,
            "g_aabb_gap_3d": 0.0,
            "g_aabb_gap_xy": 0.0,
            "g_aabb_overlap_xy_area": 0.0,
            "g_aabb_overlap_xy_ratio_min": 0.0,
            "g_z_delta_subject_minus_object": 0.0,
            "g_abs_z_delta": 0.0,
            "g_subject_below_object": 0,
            "g_subject_above_object": 0,
            "g_vertical_surface_proxy_object": 0,
            "g_horizontal_surface_proxy_object": 0,
            "g_subject_volume_proxy": 0.0,
            "g_object_volume_proxy": 0.0,
            "g_subject_object_volume_ratio": 0.0,
            "g_floor_support_confound_proxy": 0,
        }
    sc = subj["center"]
    oc = obj["center"]
    dx = sc[0] - oc[0]
    dy = sc[1] - oc[1]
    dz = sc[2] - oc[2]
    gaps = [interval_gap(subj["min"][dim], subj["max"][dim], obj["min"][dim], obj["max"][dim]) for dim in range(3)]
    overlap_x = interval_overlap(subj["min"][0], subj["max"][0], obj["min"][0], obj["max"][0])
    overlap_y = interval_overlap(subj["min"][1], subj["max"][1], obj["min"][1], obj["max"][1])
    overlap_z = interval_overlap(subj["min"][2], subj["max"][2], obj["min"][2], obj["max"][2])
    overlap_xy_area = overlap_x * overlap_y
    min_xy_area = max(min(subj["xy_area"], obj["xy_area"]), 1e-9)
    min_volume = max(min(subj["volume"], obj["volume"]), 1e-9)
    gap_xy = math.sqrt(gaps[0] * gaps[0] + gaps[1] * gaps[1])
    gap_3d = math.sqrt(gap_xy * gap_xy + gaps[2] * gaps[2])
    volume_ratio = subj["volume"] / max(obj["volume"], 1e-9)
    return {
        "g_geometry_available": 1,
        "g_center_distance_3d": math.sqrt(dx * dx + dy * dy + dz * dz),
        "g_center_distance_xy": math.sqrt(dx * dx + dy * dy),
        "g_aabb_gap_3d": gap_3d,
        "g_aabb_gap_xy": gap_xy,
        "g_aabb_gap_z": gaps[2],
        "g_aabb_overlap_xy_area": overlap_xy_area,
        "g_aabb_overlap_xy_ratio_min": overlap_xy_area / min_xy_area,
        "g_aabb_overlap_z": overlap_z,
        "g_aabb_overlap_volume_proxy_ratio_min": (overlap_xy_area * overlap_z) / min_volume,
        "g_z_delta_subject_minus_object": dz,
        "g_abs_z_delta": abs(dz),
        "g_subject_below_object": 1 if sc[2] < oc[2] else 0,
        "g_subject_above_object": 1 if sc[2] > oc[2] else 0,
        "g_vertical_surface_proxy_object": int(obj["vertical_plane_proxy"]),
        "g_horizontal_surface_proxy_object": int(obj["horizontal_plane_proxy"]),
        "g_subject_normal_z_abs": finite(subj.get("normal_z_abs")),
        "g_object_normal_z_abs": finite(obj.get("normal_z_abs")),
        "g_subject_thinness": finite(subj.get("thinness")),
        "g_object_thinness": finite(obj.get("thinness")),
        "g_subject_volume_proxy": finite(subj.get("volume")),
        "g_object_volume_proxy": finite(obj.get("volume")),
        "g_subject_object_volume_ratio": volume_ratio,
        "g_subject_segment_count": float(subj.get("segment_count") or 0),
        "g_object_segment_count": float(obj.get("segment_count") or 0),
        "g_floor_support_confound_proxy": 0,
    }


def q_features(inventory: dict[str, Any]) -> dict[str, Any]:
    visual_context = inventory.get("visual_context_state")
    audit_state = inventory.get("audit_ready_state")
    return {
        "q_mesh_evidence_ready": bool01(inventory.get("mesh_packet_ready")),
        "q_multiview_evidence_ready": bool01(inventory.get("multiview_packet_ready")),
        "q_contact_sheet_ready": bool01(inventory.get("contact_sheet_ready")),
        "q_subject_image_count": float(inventory.get("subject_image_count") or 0),
        "q_object_image_count": float(inventory.get("object_image_count") or 0),
        "q_subject_scan_crop_count": float(inventory.get("subject_scan_crop_count") or 0),
        "q_object_scan_crop_count": float(inventory.get("object_scan_crop_count") or 0),
        "q_shared_origin_frame_count": float(inventory.get("shared_origin_frame_count") or 0),
        "q_shared_view_rank_count": float(inventory.get("shared_view_rank_count") or 0),
        "q_same_frame_covisible": 1 if visual_context == "same_frame_covisible_strong" else 0,
        "q_same_view_weak": 1 if visual_context == "same_view_rank_weak_proxy" else 0,
        "q_individual_visual_plus_mesh": 1 if audit_state == "individual_visual_plus_mesh_audit_ready" else 0,
        "q_strong_pair_visual_ready": bool01(inventory.get("strong_pair_visual_ready")),
        "q_scan_mesh_ready": bool01(inventory.get("scan_mesh_ready")),
        "q_scan_point_mesh_ready": bool01(inventory.get("scan_point_mesh_ready")),
        "q_scan_multi_view_exists": bool01(inventory.get("scan_multi_view_exists")),
        "q_scan_sequence_dir_exists": bool01(inventory.get("scan_sequence_dir_exists")),
        "q_connected_topology_available": bool01(inventory.get("explicit_topology_source_available")),
        "q_visual_evidence_tier": 2 if visual_context == "same_frame_covisible_strong" else 1 if visual_context == "same_view_rank_weak_proxy" else 0,
    }


def semantic_features(row: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    predicate = row.get("predicate_label")
    subject_label = row.get("subject_label")
    object_label = row.get("object_label")
    return {
        "t_predicate_label": predicate,
        "t_predicate_family": "attachment_observability",
        "t_subject_label": subject_label,
        "t_object_label": object_label,
        "t_subject_object_pair": f"{subject_label}|{object_label}",
        "t_subject_family": candidate.get("subject_family", "unknown"),
        "t_object_family": candidate.get("object_family", "unknown"),
        "t_is_attached_to": 1 if predicate == "attached to" else 0,
        "t_is_hanging_on": 1 if predicate == "hanging on" else 0,
        "t_is_connected_to": 1 if predicate == "connected to" else 0,
        "t_object_anchor_surface_label_hint": 1 if contains_any(object_label, ANCHOR_SURFACE_LABELS) else 0,
        "t_endpoint_connector_label_hint": 1
        if contains_any(subject_label, DEVICE_CONNECTOR_LABELS) or contains_any(object_label, DEVICE_CONNECTOR_LABELS)
        else 0,
    }


def model_safe_row(source_row: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {"schema_version": f"{SCHEMA_VERSION}_model_safe"}
    for block in ["T_e", "G_e_attachment", "Q_e_observability"]:
        for key, value in source_row[block].items():
            safe[key] = value
    return safe


def validate_model_safe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        for key in row:
            if key in FORBIDDEN_MODEL_SAFE_KEYS or any(fragment in key for fragment in FORBIDDEN_MODEL_SAFE_SUBSTRINGS):
                errors.append({"error_type": "forbidden_model_safe_key", "row_index": idx, "key": key})
    return errors


def build_rows(args: argparse.Namespace) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any], list[dict[str, Any]]]:
    inventory_rows = read_jsonl(args.source_inventory_dir / "packet_reuse_inventory_rows.jsonl")
    ingested_rows = read_jsonl(args.ingestion_dir / "ingested_rows.jsonl")
    label_ready_rows = read_jsonl(args.packet_dir / "label_ready_manifest.jsonl")
    candidate_rows = read_jsonl(args.candidate_dir / "candidate_rows_internal.jsonl")
    ingested_by_id = {row["candidate_id"]: row for row in ingested_rows}
    label_by_id = {row["candidate_id"]: row for row in label_ready_rows}
    candidate_by_id = {row["candidate_id"]: row for row in candidate_rows}
    semseg_cache: dict[str, dict[int, dict[str, Any]]] = {}

    source_rows: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []
    target_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    control_rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for idx, inventory in enumerate(inventory_rows):
        candidate_id = inventory["candidate_id"]
        ingested = ingested_by_id.get(candidate_id)
        label_ready = label_by_id.get(candidate_id)
        candidate = candidate_by_id.get(candidate_id, {})
        if ingested is None or label_ready is None:
            errors.append({"error_type": "missing_joined_row", "candidate_id": candidate_id})
            continue
        predicate = inventory["predicate_label"]
        if predicate not in TARGET_PREDICATES:
            errors.append({"error_type": "unexpected_predicate", "candidate_id": candidate_id, "predicate": predicate})
            continue
        scan_id = inventory["scan_id"]
        subject_id = int(label_ready["subject_id"])
        object_id = int(label_ready["object_id"])
        objects = semseg_objects(scan_id, args.scan_root, semseg_cache)
        g = geometry_features(objects.get(subject_id), objects.get(object_id))
        if (inventory.get("subject_label") or "").lower() == "floor" or (inventory.get("object_label") or "").lower() == "floor":
            g["g_floor_support_confound_proxy"] = 1
        t = semantic_features(inventory, candidate)
        q = q_features(inventory)
        route_role = (
            "primary_observability_then_reliability"
            if predicate in PRIMARY_PREDICATES
            else "diagnostic_observability_then_topology"
        )
        source = {
            "schema_version": f"{SCHEMA_VERSION}_source_row",
            "row_uid": f"r7_attach_obs_{idx:04d}",
            "route_id": "R7",
            "route_role": route_role,
            "split": "train",
            "T_e": t,
            "G_e_attachment": g,
            "Q_e_observability": q,
            "model_input_allowed": True,
            "target_included": False,
            "hidden_included": False,
        }
        target = {
            "schema_version": f"{SCHEMA_VERSION}_target_manifest",
            "row_uid": source["row_uid"],
            "candidate_id": candidate_id,
            "predicate_label": predicate,
            "route_role": route_role,
            "p_obs_target": ingested.get("p_obs_target"),
            "p_rel_observable_target": ingested.get("p_rel_target") if predicate in PRIMARY_PREDICATES and ingested.get("p_obs_target") == 1 else None,
            "p_rel_observable_usable": bool(predicate in PRIMARY_PREDICATES and ingested.get("p_obs_target") == 1),
            "primary_relation_binary_target": ingested.get("primary_relation_binary_target"),
            "primary_relation_binary_usable": ingested.get("primary_relation_binary_usable"),
            "multiclass_relation_reliability_hidden": ingested.get("review_relation_reliability"),
            "geometry_support_hidden": ingested.get("review_geometry_support"),
            "connected_to_diagnostic_only": predicate in DIAGNOSTIC_PREDICATES,
            "model_input_allowed": False,
        }
        hidden = {
            "schema_version": f"{SCHEMA_VERSION}_hidden_manifest",
            "row_uid": source["row_uid"],
            "candidate_id": candidate_id,
            "scan_id": scan_id,
            "subgraph_id": label_ready.get("subgraph_id"),
            "subject_id": subject_id,
            "object_id": object_id,
            "directed_pair_id": label_ready.get("directed_pair_id"),
            "prediction_id": label_ready.get("prediction_id"),
            "packet_request_id": label_ready.get("packet_request_id"),
            "packet_dir_hidden": label_ready.get("packet_dir_hidden"),
            "mesh_packet_hidden": label_ready.get("mesh_packet_hidden"),
            "multiview_packet_hidden": label_ready.get("multiview_packet_hidden"),
            "contact_or_context_sheet_hidden": label_ready.get("contact_or_context_sheet_hidden"),
            "query_id_hidden": label_ready.get("query_id"),
            "selection_proxy_role_hidden": label_ready.get("selection_proxy_role_hidden"),
            "selection_route_hidden": label_ready.get("selection_route"),
            "cell_id_hidden": label_ready.get("cell_id_hidden"),
            "rank_band_hidden": label_ready.get("rank_band_hidden"),
            "semantic_rank_hidden": label_ready.get("semantic_rank_hidden"),
            "semantic_score_norm_hidden": label_ready.get("semantic_score_norm_hidden"),
            "label_match_status_hidden": label_ready.get("label_match_status_hidden"),
            "matched_predicates_hidden": label_ready.get("matched_predicates_hidden"),
            "review_relation_reliability": ingested.get("review_relation_reliability"),
            "review_geometry_support": ingested.get("review_geometry_support"),
            "review_coverage": ingested.get("review_coverage"),
            "review_endpoint_identity": ingested.get("review_endpoint_identity"),
            "review_uncertainty": ingested.get("review_uncertainty"),
            "review_notes": ingested.get("review_notes"),
            "model_input_allowed": False,
        }
        source_rows.append(source)
        model_rows.append(model_safe_row(source))
        target_rows.append(target)
        hidden_rows.append(hidden)

    control_rows.extend(control_manifest(source_rows))
    rows = {
        "source_rows": source_rows,
        "model_safe_view": model_rows,
        "target_manifest": target_rows,
        "hidden_manifest": hidden_rows,
        "control_manifest": control_rows,
    }
    errors.extend(validate_model_safe(model_rows))
    summary = build_counts(rows)
    return rows, summary, errors


def control_manifest(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    row_uids = [row["row_uid"] for row in source_rows]
    primary = [row["row_uid"] for row in source_rows if row["route_role"] == "primary_observability_then_reliability"]
    connected = [row["row_uid"] for row in source_rows if row["route_role"] == "diagnostic_observability_then_topology"]
    return [
        {
            "control_id": "wrong_T_predicate_swap",
            "control_type": "row_level_transform",
            "applies_to_rows": len(primary),
            "row_uids_preview": primary[:20],
            "purpose": "test predicate-conditioned compatibility",
            "model_input_allowed": False,
        },
        {
            "control_id": "shuffled_G_same_predicate",
            "control_type": "feature_shuffle",
            "applies_to_rows": len(primary),
            "row_uids_preview": primary[:20],
            "purpose": "test geometry-specific signal",
            "model_input_allowed": False,
        },
        {
            "control_id": "shuffled_Q_same_predicate",
            "control_type": "feature_shuffle",
            "applies_to_rows": len(row_uids),
            "row_uids_preview": row_uids[:20],
            "purpose": "test observability shortcut dependence",
            "model_input_allowed": False,
        },
        {
            "control_id": "no_view_low_evidence_mask",
            "control_type": "feature_mask",
            "applies_to_rows": len(row_uids),
            "row_uids_preview": row_uids[:20],
            "purpose": "test p_obs abstention behavior",
            "model_input_allowed": False,
        },
        {
            "control_id": "class_pair_only_probe",
            "control_type": "schema_audit_probe",
            "applies_to_rows": len(row_uids),
            "row_uids_preview": row_uids[:20],
            "purpose": "detect semantic class-pair shortcut",
            "model_input_allowed": False,
        },
        {
            "control_id": "hidden_query_rank_packet_probe",
            "control_type": "hidden_leakage_probe",
            "applies_to_rows": len(row_uids),
            "row_uids_preview": row_uids[:20],
            "purpose": "audit blocked construction/source leakage",
            "model_input_allowed": False,
        },
        {
            "control_id": "connected_to_diagnostic_probe",
            "control_type": "diagnostic_route_probe",
            "applies_to_rows": len(connected),
            "row_uids_preview": connected[:20],
            "purpose": "keep connected-to outside primary p_rel",
            "model_input_allowed": False,
        },
    ]


def build_counts(rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    source_rows = rows["source_rows"]
    targets = rows["target_manifest"]
    model_rows = rows["model_safe_view"]
    predicate_counts = Counter(row["T_e"]["t_predicate_label"] for row in source_rows)
    route_counts = Counter(row["route_role"] for row in source_rows)
    p_obs_counts = Counter(str(row.get("p_obs_target")) for row in targets)
    p_rel_counts = Counter(str(row.get("p_rel_observable_target")) for row in targets)
    geometry_available = sum(1 for row in source_rows if row["G_e_attachment"].get("g_geometry_available") == 1)
    strong_visual = sum(1 for row in source_rows if row["Q_e_observability"].get("q_strong_pair_visual_ready") == 1)
    same_view = sum(1 for row in source_rows if row["Q_e_observability"].get("q_same_view_weak") == 1)
    p_rel_usable = sum(1 for row in targets if row.get("p_rel_observable_usable"))
    return {
        "rows": len(source_rows),
        "model_safe_rows": len(model_rows),
        "target_rows": len(targets),
        "hidden_rows": len(rows["hidden_manifest"]),
        "control_rows": len(rows["control_manifest"]),
        "rows_by_predicate": dict(predicate_counts),
        "rows_by_route_role": dict(route_counts),
        "geometry_available_rows": geometry_available,
        "strong_pair_visual_rows": strong_visual,
        "same_view_weak_rows": same_view,
        "p_obs_target": dict(p_obs_counts),
        "p_rel_observable_target": dict(p_rel_counts),
        "p_rel_observable_usable_rows": p_rel_usable,
        "model_safe_field_count": len(model_rows[0]) if model_rows else 0,
        "model_safe_fields": sorted(model_rows[0].keys()) if model_rows else [],
    }


def schema_audit_inputs(summary_counts: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_schema_audit_inputs",
        "next_todo": NEXT_TODO,
        "model_safe_feature_whitelist": summary_counts["model_safe_fields"],
        "blocked_key_exact": sorted(FORBIDDEN_MODEL_SAFE_KEYS),
        "blocked_key_substrings": list(FORBIDDEN_MODEL_SAFE_SUBSTRINGS),
        "required_probe_families": [
            "class_pair_only_probe",
            "predicate_only_probe",
            "q_only_probe",
            "g_only_probe",
            "t_plus_g_probe",
            "wrong_T_predicate_swap",
            "shuffled_G_same_predicate",
            "shuffled_Q_same_predicate",
            "hidden_query_rank_packet_probe",
            "connected_to_diagnostic_probe",
        ],
        "target_fields": [
            "p_obs_target",
            "p_rel_observable_target",
            "primary_relation_binary_target",
            "multiclass_relation_reliability_hidden",
        ],
        "grouping_recommendations": [
            "predicate_label",
            "t_subject_object_pair",
            "q_visual_evidence_tier",
        ],
        "known_risks": [
            "p_rel positives are sparse",
            "class pair and predicate may be predictive",
            "Q_e can dominate p_obs by design but must not solve p_rel alone",
            "connected-to has no primary p_rel target",
        ],
    }


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    lines = [
        "# Attachment Observability Materialization",
        "",
        f"Created: `{summary['created_at_utc']}`",
        "",
        "## Result",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Counts",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"rows_by_predicate = {counts['rows_by_predicate']}",
        f"rows_by_route_role = {counts['rows_by_route_role']}",
        f"geometry_available_rows = {counts['geometry_available_rows']}",
        f"strong_pair_visual_rows = {counts['strong_pair_visual_rows']}",
        f"same_view_weak_rows = {counts['same_view_weak_rows']}",
        f"p_obs_target = {counts['p_obs_target']}",
        f"p_rel_observable_target = {counts['p_rel_observable_target']}",
        f"p_rel_observable_usable_rows = {counts['p_rel_observable_usable_rows']}",
        f"model_safe_field_count = {counts['model_safe_field_count']}",
        "```",
        "",
        "## Boundary",
        "",
        "- This stage materializes rows only.",
        "- It does not run learned smoke.",
        "- It does not use validation/test data.",
        "- Review labels, source rank/score, query id, packet id, scan/object ids, and targets are excluded from `model_safe_view.jsonl`.",
        "- `connected to` is diagnostic and has no primary `p_rel` target.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}` must run before any learned smoke.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    plan_summary = read_json(args.plan_dir / "summary.json")
    source_summary = read_json(args.source_inventory_dir / "summary.json")
    errors = validate_inputs(plan_summary, source_summary, args)
    rows, counts, row_errors = build_rows(args)
    errors.extend(row_errors)
    status = STATUS_ERROR if errors else STATUS_READY
    selected_path = "input_or_schema_errors_block_attachment_materialization" if errors else SELECTED_PATH
    next_todo = "fix_attachment_observability_materialization" if errors else NEXT_TODO

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = {
        "summary": output_dir / "summary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "report": output_dir / "report.md",
        "source_rows": output_dir / "source_rows.jsonl",
        "model_safe_view": output_dir / "model_safe_view.jsonl",
        "target_manifest": output_dir / "target_manifest.jsonl",
        "hidden_manifest": output_dir / "hidden_manifest.jsonl",
        "control_manifest": output_dir / "control_manifest.jsonl",
        "schema_audit_inputs": output_dir / "schema_audit_inputs.json",
        "model_safe_feature_manifest": output_dir / "model_safe_feature_manifest.csv",
        "target_distribution": output_dir / "target_distribution.csv",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(errors),
        "next_todo": next_todo,
        "input_paths": {
            "plan": rel_path(args.plan_dir / "summary.json"),
            "source_inventory": rel_path(args.source_inventory_dir / "summary.json"),
            "ingested_rows": rel_path(args.ingestion_dir / "ingested_rows.jsonl"),
            "label_ready_manifest": rel_path(args.packet_dir / "label_ready_manifest.jsonl"),
            "candidate_internal": rel_path(args.candidate_dir / "candidate_rows_internal.jsonl"),
            "scan_root": rel_path(args.scan_root),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "counts": counts,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "runs_model": False,
            "trains_new_model": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "materializes_rows": True,
            "learned_smoke_executed": False,
            "multi_view_as_raw_model_input": False,
            "mesh_as_raw_model_input": False,
            "model_safe_view_excludes_hidden_and_targets": len([e for e in errors if e.get("error_type") == "forbidden_model_safe_key"]) == 0,
        },
    }
    audit_inputs = schema_audit_inputs(counts)
    feature_rows = [{"feature": key, "allowed_in_model_safe_view": True} for key in counts["model_safe_fields"]]
    target_dist_rows = [
        {"target": "p_obs_target", "value": key, "rows": value} for key, value in counts["p_obs_target"].items()
    ] + [
        {"target": "p_rel_observable_target", "value": key, "rows": value}
        for key, value in counts["p_rel_observable_target"].items()
    ]

    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], errors)
    write_jsonl(output_paths["source_rows"], rows["source_rows"])
    write_jsonl(output_paths["model_safe_view"], rows["model_safe_view"])
    write_jsonl(output_paths["target_manifest"], rows["target_manifest"])
    write_jsonl(output_paths["hidden_manifest"], rows["hidden_manifest"])
    write_jsonl(output_paths["control_manifest"], rows["control_manifest"])
    write_json(output_paths["schema_audit_inputs"], audit_inputs)
    write_csv(output_paths["model_safe_feature_manifest"], feature_rows)
    write_csv(output_paths["target_distribution"], target_dist_rows)
    output_paths["report"].write_text(report_text(summary), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
