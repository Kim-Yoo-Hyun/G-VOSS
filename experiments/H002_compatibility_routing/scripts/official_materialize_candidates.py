#!/usr/bin/env python3
"""Materialize official validation H002 candidates without running metrics."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h002_official_candidate_materialization_v1"
EXPECTED_PROTOCOL_STATUS = "h002_compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory_ready"

FAMILY_PREDICATES = {
    "relative_horizontal": ["left", "right", "front", "behind"],
    "relative_vertical": ["higher than", "lower than"],
    "size_relative": ["bigger than", "smaller than"],
    "support_contact": ["standing on", "lying on"],
}
PREDICATE_TO_FAMILY = {
    predicate: family
    for family, predicates in FAMILY_PREDICATES.items()
    for predicate in predicates
}
PROMOTED_PREDICATES = set(PREDICATE_TO_FAMILY)

BLOCKED_MODEL_SAFE_KEYS = {
    "source_score",
    "ranking_score",
    "semantic_rank",
    "source_id",
    "h001_p_geom_valid",
    "h001_verification_status",
    "label_match_status",
    "geometry_status",
    "candidate_bucket",
    "construction_bucket",
    "distance_bucket",
    "rank_band",
    "gt_exact_match_flag",
    "counterfactual_type",
    "target_generation_rule",
    "old_proxy_label",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--protocol-dir",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "compatibility_dataset_v3_official_candidate_materialization_protocol_after_source_inventory"
        ),
    )
    parser.add_argument("--subset-dir", type=Path, default=Path("local_dataset/3DSSG_subset"))
    parser.add_argument("--scan-dir", type=Path, default=Path("local_dataset/3RScan/scans"))
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve_under_repo(repo_root: Path, path: Path) -> Path:
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


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


def relationship_predicate_id(rel: Any) -> int | None:
    if isinstance(rel, list) and len(rel) >= 3:
        return int(rel[2])
    if isinstance(rel, dict):
        value = rel.get("predicate_id") or rel.get("relationship_id")
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


def object_label(objects: Any, object_id: int | None) -> str:
    if object_id is None:
        return "unknown_object"
    if isinstance(objects, dict):
        return str(objects.get(str(object_id)) or objects.get(object_id) or "unknown_object")
    return "unknown_object"


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if math.isfinite(out) else default


def vector3(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) < 3:
        return None
    return [safe_float(value[0]), safe_float(value[1]), safe_float(value[2])]


def obb_record(group: dict[str, Any]) -> dict[str, Any] | None:
    obb = group.get("obb")
    if not isinstance(obb, dict):
        return None
    centroid = vector3(obb.get("centroid"))
    lengths = vector3(obb.get("axesLengths"))
    if centroid is None or lengths is None:
        return None
    axes_raw = obb.get("normalizedAxes")
    axes: list[list[float]] = []
    if isinstance(axes_raw, list) and len(axes_raw) >= 9:
        axes = [
            [safe_float(axes_raw[0]), safe_float(axes_raw[1]), safe_float(axes_raw[2])],
            [safe_float(axes_raw[3]), safe_float(axes_raw[4]), safe_float(axes_raw[5])],
            [safe_float(axes_raw[6]), safe_float(axes_raw[7]), safe_float(axes_raw[8])],
        ]
    else:
        axes = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
    half_extents = []
    for coord in range(3):
        half = sum(abs(axes[axis_index][coord]) * max(lengths[axis_index], 1e-9) / 2.0 for axis_index in range(3))
        half_extents.append(half)
    mins = [centroid[i] - half_extents[i] for i in range(3)]
    maxs = [centroid[i] + half_extents[i] for i in range(3)]
    return {
        "centroid": centroid,
        "axes_lengths": lengths,
        "normalized_axes": axes,
        "aabb_half_extents": half_extents,
        "aabb_min": mins,
        "aabb_max": maxs,
        "volume": max(lengths[0] * lengths[1] * lengths[2], 1e-9),
    }


def semseg_object_map(scan_dir: Path, scan_id: str) -> dict[int, dict[str, Any]]:
    path = scan_dir / scan_id / "semseg.v2.json"
    data = read_json(path)
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
        "subject_bottom_z": sz0,
        "subject_top_z": sz1,
        "object_bottom_z": oz0,
        "object_top_z": oz1,
        "surface_gap_subject_bottom_to_object_top": sz0 - oz1,
        "abs_surface_gap_subject_bottom_to_object_top": abs(sz0 - oz1),
        "subject_height": subject_height,
        "object_height": object_height,
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
    if family == "relative_horizontal":
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


def source_bridge_by_family(protocol_dir: Path) -> dict[str, list[dict[str, Any]]]:
    rows = read_csv(protocol_dir / "source_bridge_contract.csv")
    out: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        family = row.get("route_family", "")
        out[family].append(
            {
                "source_id": row.get("source_id"),
                "source_prediction_rows": int(float(row.get("source_prediction_rows", 0))),
                "bridge_use_policy": row.get("bridge_use_policy"),
                "source_score_policy": row.get("source_score_policy"),
                "p_geom_valid_policy": row.get("p_geom_valid_policy"),
                "read_only_requirement": row.get("read_only_requirement"),
            }
        )
    return out


def flatten_keys(value: Any, prefix: str = "") -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield child_prefix
            yield from flatten_keys(child, child_prefix)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_prefix = f"{prefix}[{index}]"
            yield from flatten_keys(child, child_prefix)


def model_safe_blocked_hits(row: dict[str, Any]) -> list[str]:
    hits: list[str] = []
    for path in flatten_keys(row):
        leaf = path.split(".")[-1]
        if leaf in BLOCKED_MODEL_SAFE_KEYS:
            hits.append(path)
    return hits


def make_rows(repo_root: Path, subset_dir: Path, scan_dir: Path, protocol_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    data = read_json(subset_dir / "relationships_validation.json")
    source_bridge = source_bridge_by_family(protocol_dir)
    candidate_rows: list[dict[str, Any]] = []
    model_safe_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    seen_candidate_ids: set[str] = set()

    for scan in scan_relationships(data):
        scan_id = str(scan.get("scan"))
        objects = scan.get("objects", {})
        try:
            obbs = semseg_object_map(scan_dir, scan_id)
        except Exception as exc:  # noqa: BLE001 - materialization should record and continue.
            errors.append({"error_type": "semseg_read_error", "scan_id": scan_id, "message": str(exc)})
            continue

        pair_family_true: dict[tuple[int, int, str], set[str]] = defaultdict(set)
        promoted_relations: list[dict[str, Any]] = []
        for rel_index, rel in enumerate(scan.get("relationships", [])):
            predicate = relationship_predicate(rel)
            if predicate not in PROMOTED_PREDICATES:
                continue
            subject_id = relationship_subject(rel)
            object_id = relationship_object(rel)
            if subject_id is None or object_id is None:
                errors.append({"error_type": "missing_relation_endpoint", "scan_id": scan_id, "rel_index": rel_index})
                continue
            family = PREDICATE_TO_FAMILY[predicate]
            pair_family_true[(subject_id, object_id, family)].add(predicate)
            promoted_relations.append(
                {
                    "rel_index": rel_index,
                    "predicate_label": predicate,
                    "predicate_id": relationship_predicate_id(rel),
                    "subject_id": subject_id,
                    "object_id": object_id,
                    "route_family": family,
                }
            )

        for relation in promoted_relations:
            subject_id = relation["subject_id"]
            object_id = relation["object_id"]
            family = relation["route_family"]
            true_predicates = sorted(pair_family_true[(subject_id, object_id, family)])
            if subject_id not in obbs or object_id not in obbs:
                errors.append(
                    {
                        "error_type": "missing_obb_for_promoted_relation",
                        "scan_id": scan_id,
                        "subject_id": subject_id,
                        "object_id": object_id,
                        "route_family": family,
                    }
                )
                continue
            geometry = pair_geometry(obbs[subject_id], obbs[object_id])
            policy, feature_names, feature_vector = family_g_e(family, geometry)
            candidate_specs = [
                {
                    "predicate_label": relation["predicate_label"],
                    "target_y": 1,
                    "candidate_origin": "official_gt_positive",
                    "counterfactual_from_predicate": None,
                }
            ]
            for predicate in FAMILY_PREDICATES[family]:
                if predicate == relation["predicate_label"] or predicate in true_predicates:
                    continue
                candidate_specs.append(
                    {
                        "predicate_label": predicate,
                        "target_y": 0,
                        "candidate_origin": "official_same_pair_predicate_counterfactual",
                        "counterfactual_from_predicate": relation["predicate_label"],
                    }
                )

            for local_index, spec in enumerate(candidate_specs):
                candidate_id = (
                    f"official_validation::{scan_id}::{subject_id}->{object_id}::"
                    f"{family}::{relation['rel_index']}::{spec['predicate_label'].replace(' ', '_')}::{local_index}"
                )
                if candidate_id in seen_candidate_ids:
                    errors.append({"error_type": "duplicate_candidate_id", "candidate_id": candidate_id})
                    continue
                seen_candidate_ids.add(candidate_id)
                subject_label = object_label(objects, subject_id)
                object_label_text = object_label(objects, object_id)
                cv_group_key = f"official_validation::{scan_id}::{subject_id}->{object_id}::{family}"
                feature_blocks = {
                    "T_e": {
                        "predicate_label": spec["predicate_label"],
                        "predicate_text": spec["predicate_label"],
                        "route_family": family,
                        "subject_class_label": subject_label,
                        "object_class_label": object_label_text,
                        "predicate_family_embedding_key": family,
                    },
                    "G_e": {
                        "g_e_available": True,
                        "g_e_feature_names": feature_names,
                        "g_e_feature_vector": feature_vector,
                        "g_e_feature_mask": {name: True for name in feature_names},
                        "geometry_reference_policy": policy,
                    },
                    "Q_e": {
                        "geometry_observable": True,
                        "geometry_quality_flag": "semseg_obb_pair_available",
                        "object_obb_available": True,
                        "mesh_or_semseg_available": True,
                    },
                    "Z_e": {},
                    "extra_safe_blocks": {},
                }
                base_row = {
                    "schema_version": SCHEMA_VERSION,
                    "candidate_id": candidate_id,
                    "split": "validation",
                    "scan_id": scan_id,
                    "subject_id": subject_id,
                    "object_id": object_id,
                    "predicate_label": spec["predicate_label"],
                    "route_family": family,
                    "target_y": spec["target_y"],
                    "cv_or_group_key": cv_group_key,
                    "paper_metric_ready": False,
                    "official_validation_metric_ready": False,
                    "feature_use_policy": {
                        "main_C_e_allowed_blocks": ["T_e", "G_e"],
                        "diagnostic_only_blocks": ["Q_e", "Z_e"],
                        "row_identity_not_features": [
                            "candidate_id",
                            "scan_id",
                            "subject_id",
                            "object_id",
                            "cv_or_group_key",
                        ],
                    },
                    "feature_blocks": feature_blocks,
                }
                hits = model_safe_blocked_hits(base_row)
                if hits:
                    errors.append({"error_type": "model_safe_blocked_field_hit", "candidate_id": candidate_id, "hits": hits})
                model_safe_rows.append(base_row)
                candidate_rows.append(
                    {
                        **base_row,
                        "candidate_origin": spec["candidate_origin"],
                        "compatibility_label": "compatible" if spec["target_y"] else "incompatible_counterfactual",
                        "compatibility_label_source": "official_validation_gt_counterfactual_protocol",
                        "hidden_manifest_ref": candidate_id,
                        "candidate_row_note": "full candidate row; use model_safe_view for main C_e inputs",
                    }
                )
                hidden_rows.append(
                    {
                        "candidate_id": candidate_id,
                        "schema_version": f"{SCHEMA_VERSION}_hidden_manifest",
                        "scan_id": scan_id,
                        "subject_id": subject_id,
                        "object_id": object_id,
                        "route_family": family,
                        "target_generation_rule": "official_gt_positive" if spec["target_y"] else "same_pair_predicate_flip_excluding_existing_gt_predicates",
                        "counterfactual_type": None if spec["target_y"] else "same_pair_predicate_flip",
                        "gt_exact_match_flag": bool(spec["target_y"]),
                        "gt_relation_index": relation["rel_index"],
                        "gt_predicate_id": relation["predicate_id"],
                        "gt_predicate_label": relation["predicate_label"],
                        "candidate_predicate_label": spec["predicate_label"],
                        "counterfactual_from_predicate": spec["counterfactual_from_predicate"],
                        "true_predicates_for_directed_pair_family": true_predicates,
                        "source_bridge": source_bridge.get(family, []),
                        "h001_p_geom_valid_policy": "hidden_or_diagnostic_only_not_main_G_e",
                        "h001_verification_status_policy": "hidden_or_diagnostic_only_not_main_C_e",
                        "geometry_status": "not_precomputed_in_materializer",
                    }
                )
    return candidate_rows, model_safe_rows, hidden_rows, errors


def validate_protocol(protocol_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    summary_path = protocol_dir / "summary.json"
    if not summary_path.exists():
        return [{"error_type": "missing_protocol_summary", "path": str(summary_path)}]
    summary = read_json(summary_path)
    if summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": summary.get("status")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "protocol_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    for key in ["candidate_rows_materialized", "official_validation_metric_produced", "official_test_usage", "paper_metric_produced"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "unexpected_protocol_boundary", "key": key, "actual": boundary.get(key)})
    return errors


def summarize(
    repo_root: Path,
    out: Path,
    protocol_dir: Path,
    candidate_rows: list[dict[str, Any]],
    model_safe_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    validation_errors: list[dict[str, Any]],
) -> dict[str, Any]:
    family_counts: Counter[str] = Counter(row["route_family"] for row in model_safe_rows)
    predicate_counts: Counter[tuple[str, str]] = Counter((row["route_family"], row["predicate_label"]) for row in model_safe_rows)
    label_counts: Counter[tuple[str, int]] = Counter((row["route_family"], int(row["target_y"])) for row in model_safe_rows)
    origins: Counter[str] = Counter(row["candidate_origin"] for row in candidate_rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "h002_official_candidate_materialization_ready" if not validation_errors else "h002_official_candidate_materialization_errors",
        "validation_errors": len(validation_errors),
        "paper_metric_produced": False,
        "official_validation_metric_produced": False,
        "official_test_usage": False,
        "p_rel_claim_enabled": False,
        "p_obs_claim_enabled": False,
        "input_artifacts": {
            "protocol_dir": repo_rel(repo_root, protocol_dir),
            "relationships_validation": "local_dataset/3DSSG_subset/relationships_validation.json",
            "scan_dir": "local_dataset/3RScan/scans",
        },
        "output_artifacts": {
            "candidate_rows": repo_rel(repo_root, out / "candidate_rows.jsonl"),
            "model_safe_view": repo_rel(repo_root, out / "model_safe_view.jsonl"),
            "hidden_manifest": repo_rel(repo_root, out / "hidden_manifest.jsonl"),
            "row_manifest": repo_rel(repo_root, out / "row_manifest.json"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
        },
        "row_counts": {
            "candidate_rows": len(candidate_rows),
            "model_safe_view": len(model_safe_rows),
            "hidden_manifest": len(hidden_rows),
            "candidate_origin_counts": dict(sorted(origins.items())),
            "family_counts": dict(sorted(family_counts.items())),
            "family_label_counts": {f"{family}|{label}": count for (family, label), count in sorted(label_counts.items())},
            "predicate_counts": {f"{family}|{predicate}": count for (family, predicate), count in sorted(predicate_counts.items())},
        },
        "boundary": {
            "model_safe_blocks": ["T_e", "G_e", "Q_e", "Z_e", "extra_safe_blocks"],
            "main_C_e_allowed_blocks": ["T_e", "G_e"],
            "diagnostic_only_blocks": ["Q_e", "Z_e"],
            "h001_artifacts_modified": False,
            "h001_artifacts_read_only_bridge_only": True,
        },
        "next_todo": "compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation",
    }


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    protocol_dir = resolve_under_repo(repo_root, args.protocol_dir)
    subset_dir = resolve_under_repo(repo_root, args.subset_dir)
    scan_dir = resolve_under_repo(repo_root, args.scan_dir)
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    validation_errors = validate_protocol(protocol_dir)
    candidate_rows: list[dict[str, Any]] = []
    model_safe_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    if not validation_errors:
        candidate_rows, model_safe_rows, hidden_rows, row_errors = make_rows(repo_root, subset_dir, scan_dir, protocol_dir)
        validation_errors.extend(row_errors)
    if not model_safe_rows and not validation_errors:
        validation_errors.append({"error_type": "no_model_safe_rows_materialized"})

    write_jsonl(out / "candidate_rows.jsonl", candidate_rows)
    write_jsonl(out / "model_safe_view.jsonl", model_safe_rows)
    write_jsonl(out / "hidden_manifest.jsonl", hidden_rows)
    summary = summarize(repo_root, out, protocol_dir, candidate_rows, model_safe_rows, hidden_rows, validation_errors)
    write_json(out / "row_manifest.json", summary)
    write_jsonl(out / "validation_errors.jsonl", validation_errors)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
