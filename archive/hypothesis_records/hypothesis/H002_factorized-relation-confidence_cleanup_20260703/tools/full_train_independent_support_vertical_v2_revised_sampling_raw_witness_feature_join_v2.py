#!/usr/bin/env python3
"""Join typed raw-witness features for H002 revised all-label-ready slice."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INPUT_ROWS = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/posterior_ready_rows.jsonl"
)
DEFAULT_REPAIR_PLAN = (
    RGA_ROOT / "independent_support_vertical_v2_revised_sampling_factor_definition_repair_plan_all_label_ready/summary.json"
)
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready"

TARGET_MODE = "rank_band_balanced_revised_sampling"

MAIN_V2_VIEWS = [
    "semantic_only",
    "legacy_geometry_only",
    "semantic_plus_geometry",
    "raw_witness_only_v2",
    "semantic_plus_raw_witness_v2",
    "factorized_reliability_posterior_v2_linear",
    "factorized_reliability_posterior_v2_family_shrinkage",
    "endpoint_type_ablation",
]

CONTROL_VIEWS = [
    "raw_witness_shuffle_global",
    "raw_witness_shuffle_within_family",
    "wrong_pair_raw_witness",
    "family_only_offset",
    "no_family_local_normalization",
    "legacy_p_geom_only",
]

FORBIDDEN_MODEL_INPUT_FRAGMENTS = [
    "review",
    "hidden",
    "packet",
    "path",
    "target",
    "label",
    "role",
    "queue",
    "rank_band",
    "geometry_status",
    "match_status",
    "audit",
]

RAW_FIELDS = [
    "center_delta_z",
    "distance_3d",
    "distance_xy",
    "normalized_center_delta_z",
    "normalized_distance_3d",
    "normalized_distance_xy",
    "object_bottom_z",
    "object_top_z",
    "projected_iou_xy",
    "projected_object_overlap_ratio",
    "projected_subject_overlap_ratio",
    "subject_bottom_z",
    "subject_top_z",
    "vertical_gap_subject_on_object",
]

LOCAL_Z_KEYS = [
    "support_gap_abs",
    "support_distance_xy",
    "support_xy_overlap_max",
    "support_xy_overlap_min",
    "support_iou_xy",
    "vertical_signed_margin",
    "vertical_margin_abs",
    "vertical_interval_overlap",
    "vertical_xy_context",
    "semantic_geometry_gap_abs",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-rows", type=Path, default=DEFAULT_INPUT_ROWS)
    parser.add_argument("--repair-plan", type=Path, default=DEFAULT_REPAIR_PLAN)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        output = float(value)
    except (TypeError, ValueError):
        return default
    if math.isnan(output) or math.isinf(output):
        return default
    return output


def clip(value: float, left: float = 0.0, right: float = 1.0) -> float:
    return min(max(value, left), right)


def rank_block(rank_value: Any) -> dict[str, float]:
    rank = max(safe_float(rank_value, 1.0), 1.0)
    return {
        "semantic_rank": rank,
        "semantic_rank_log": math.log1p(rank),
        "semantic_rank_inverse": 1.0 / rank,
    }


def load_raw_witness(match_rows: Path, prediction_ids: set[str]) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    raw_by_prediction: dict[str, dict[str, float]] = {}
    rows_scanned = 0
    relevant_family_counts = Counter()
    with as_abs(match_rows).open("r", encoding="utf-8") as handle:
        for line in handle:
            rows_scanned += 1
            row = json.loads(line)
            prediction_id = str(row.get("identity", {}).get("prediction_id") or "")
            if prediction_id not in prediction_ids:
                continue
            raw = row.get("geometry", {}).get("raw_features") or {}
            raw_by_prediction[prediction_id] = {field: safe_float(raw.get(field)) for field in RAW_FIELDS}
            relevant_family_counts[str(row.get("predicate", {}).get("predicate_family"))] += 1
            if len(raw_by_prediction) == len(prediction_ids):
                break
    return raw_by_prediction, {
        "match_rows": rel_path(match_rows),
        "rows_scanned_until_complete": rows_scanned,
        "requested_prediction_ids": len(prediction_ids),
        "matched_prediction_ids": len(raw_by_prediction),
        "matched_by_family": dict(sorted(relevant_family_counts.items())),
        "raw_fields": RAW_FIELDS,
    }


def semantic_block(row: dict[str, Any]) -> dict[str, float]:
    old = row["baseline_inputs"]["semantic_only"]
    semantic = safe_float(old.get("semantic_score_norm"))
    return {
        "semantic_score_raw": safe_float(old.get("semantic_score_raw"), semantic),
        "semantic_score_norm": semantic,
        "negative_semantic_score_norm": 1.0 - semantic,
        **rank_block(old.get("semantic_rank")),
    }


def legacy_geometry_block(row: dict[str, Any]) -> dict[str, float]:
    old = row["baseline_inputs"]["geometry_only"]
    p_geom = safe_float(old.get("p_geom_valid"), 0.5)
    return {
        "p_geom_valid": p_geom,
        "p_geom_invalid": 1.0 - p_geom,
        "consistency_score": safe_float(old.get("consistency_score"), p_geom),
    }


def coverage_block(row: dict[str, Any], raw_present: bool) -> dict[str, float]:
    old = row["baseline_inputs"].get("coverage_only", {})
    return {
        "coverage_evidence_ready": safe_float(old.get("coverage_evidence_ready")),
        "coverage_has_source_features": safe_float(old.get("coverage_has_source_features"), 1.0),
        "coverage_has_semantic_score": safe_float(old.get("coverage_has_semantic_score"), 1.0),
        "coverage_has_geometry_score": safe_float(old.get("coverage_has_geometry_score"), 1.0),
        "coverage_has_consistency_score": safe_float(old.get("coverage_has_consistency_score"), 1.0),
        "coverage_has_raw_witness": 1.0 if raw_present else 0.0,
        "raw_witness_missing_flag": 0.0 if raw_present else 1.0,
    }


def expected_z_sign(predicate_label: str) -> float:
    if predicate_label == "higher than":
        return 1.0
    if predicate_label == "lower than":
        return -1.0
    return 0.0


def vertical_interval_overlap(raw: dict[str, float]) -> float:
    subject_bottom = raw["subject_bottom_z"]
    subject_top = raw["subject_top_z"]
    object_bottom = raw["object_bottom_z"]
    object_top = raw["object_top_z"]
    overlap = max(0.0, min(subject_top, object_top) - max(subject_bottom, object_bottom))
    subject_height = max(subject_top - subject_bottom, 1e-6)
    object_height = max(object_top - object_bottom, 1e-6)
    return clip(overlap / max(min(subject_height, object_height), 1e-6), 0.0, 1.0)


def witness_features(row: dict[str, Any], raw: dict[str, float]) -> dict[str, float]:
    identity = row["identity"]
    family = str(identity["predicate_family"])
    predicate = str(identity["predicate_label"])
    support_gate = 1.0 if family == "support_contact" else 0.0
    vertical_gate = 1.0 if family == "relative_vertical" else 0.0
    z_sign = expected_z_sign(predicate)
    support_gap = raw["vertical_gap_subject_on_object"]
    support_gap_abs = abs(support_gap)
    support_xy_max = max(raw["projected_subject_overlap_ratio"], raw["projected_object_overlap_ratio"])
    support_xy_min = min(raw["projected_subject_overlap_ratio"], raw["projected_object_overlap_ratio"])
    support_distance = raw["normalized_distance_xy"]
    support_gap_closeness = 1.0 / (1.0 + support_gap_abs)
    support_distance_closeness = 1.0 / (1.0 + abs(support_distance))
    vertical_signed_margin = z_sign * raw["center_delta_z"]
    normalized_vertical_signed_margin = z_sign * raw["normalized_center_delta_z"]
    vertical_margin_abs = abs(raw["normalized_center_delta_z"])
    vertical_sign_agreement = 1.0 if vertical_gate and vertical_signed_margin >= 0.0 else 0.0
    vertical_overlap = vertical_interval_overlap(raw)
    vertical_xy_context = max(raw["projected_iou_xy"], support_xy_max)
    support_boundary = support_gate * (1.0 if support_gap_abs <= 0.10 or support_distance <= 0.10 else 0.0)
    vertical_boundary = vertical_gate * (1.0 if abs(normalized_vertical_signed_margin) <= 0.10 else 0.0)
    strong_support = support_gate * support_gap_closeness * max(support_xy_max, raw["projected_iou_xy"])
    strong_vertical = vertical_gate * vertical_sign_agreement * clip(vertical_margin_abs, 0.0, 1.0)
    return {
        "support_contact_gate": support_gate,
        "relative_vertical_gate": vertical_gate,
        "support_gap_abs": support_gap_abs,
        "support_gap_signed": support_gap,
        "support_gap_closeness": support_gap_closeness,
        "support_distance_xy": support_distance,
        "support_distance_closeness": support_distance_closeness,
        "support_xy_overlap_max": support_xy_max,
        "support_xy_overlap_min": support_xy_min,
        "support_iou_xy": raw["projected_iou_xy"],
        "support_contact_boundary_flag": support_boundary,
        "expected_z_sign": z_sign,
        "vertical_signed_margin": vertical_signed_margin,
        "normalized_vertical_signed_margin": normalized_vertical_signed_margin,
        "vertical_sign_agreement": vertical_sign_agreement,
        "vertical_margin_abs": vertical_margin_abs,
        "vertical_interval_overlap": vertical_overlap,
        "vertical_xy_context": vertical_xy_context,
        "vertical_boundary_flag": vertical_boundary,
        "strong_raw_witness_score": max(strong_support, strong_vertical),
        "weak_raw_witness_score": 1.0 - max(strong_support, strong_vertical),
    }


def disagreement_features(semantic: dict[str, float], geometry: dict[str, float]) -> dict[str, float]:
    semantic_value = semantic["semantic_score_norm"]
    geom_value = geometry["p_geom_valid"]
    consistency = geometry["consistency_score"]
    semantic_minus_geometry = semantic_value - geom_value
    geometry_minus_semantic = geom_value - semantic_value
    return {
        "semantic_minus_geometry": semantic_minus_geometry,
        "geometry_minus_semantic": geometry_minus_semantic,
        "semantic_geometry_gap_abs": abs(semantic_minus_geometry),
        "underconfidence_score": max(0.0, geometry_minus_semantic),
        "overconfidence_score": max(0.0, semantic_minus_geometry),
        "semantic_x_geometry": semantic_value * geom_value,
        "semantic_x_consistency": semantic_value * consistency,
        "geometry_x_consistency": geom_value * consistency,
    }


def endpoint_type_features(row: dict[str, Any]) -> dict[str, float]:
    subject = str(row["identity"]["subject_label"]).lower()
    obj = str(row["identity"]["object_label"]).lower()
    support_terms = ["floor", "table", "desk", "shelf", "cabinet", "bed", "chair", "sofa", "couch", "counter", "stand"]
    room_surface_terms = ["floor", "wall", "ceiling", "door", "window"]
    return {
        "endpoint_object_floor_like_flag": 1.0 if "floor" in obj else 0.0,
        "endpoint_object_wall_like_flag": 1.0 if "wall" in obj else 0.0,
        "endpoint_object_support_surface_like_flag": 1.0 if any(term in obj for term in support_terms) else 0.0,
        "endpoint_subject_room_surface_flag": 1.0 if any(term in subject for term in room_surface_terms) else 0.0,
    }


def mean_stdev(values: list[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 1.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    stdev = math.sqrt(variance)
    return mean, stdev if stdev > 1e-9 else 1.0


def family_stats(prepared: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, float]]]:
    values: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for row in prepared:
        family = str(row["identity"]["predicate_family"])
        combined = {**row["witness"], **row["disagreement"]}
        for key in LOCAL_Z_KEYS:
            values[family][key].append(safe_float(combined.get(key)))
    output: dict[str, dict[str, dict[str, float]]] = {}
    for family, by_key in values.items():
        output[family] = {}
        for key, vals in by_key.items():
            mean, stdev = mean_stdev(vals)
            output[family][key] = {"mean": mean, "stdev": stdev, "rows": len(vals)}
    return output


def add_local_z(prepared: list[dict[str, Any]], stats: dict[str, dict[str, dict[str, float]]]) -> None:
    for row in prepared:
        family = str(row["identity"]["predicate_family"])
        combined = {**row["witness"], **row["disagreement"]}
        local = {}
        for key in LOCAL_Z_KEYS:
            stat = stats[family][key]
            local[f"{key}_local_z"] = (safe_float(combined.get(key)) - stat["mean"]) / stat["stdev"]
        row["family_local"] = local


def rotate_indices(indices: list[int]) -> dict[int, int]:
    if not indices:
        return {}
    ordered = sorted(indices)
    return {idx: ordered[(pos + 1) % len(ordered)] for pos, idx in enumerate(ordered)}


def shuffled_sources(prepared: list[dict[str, Any]]) -> dict[str, dict[int, int]]:
    all_indices = list(range(len(prepared)))
    by_family: dict[str, list[int]] = defaultdict(list)
    by_scan: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(prepared):
        by_family[str(row["identity"]["predicate_family"])].append(idx)
        by_scan[str(row["identity"]["scan_id"])].append(idx)
    within_family: dict[int, int] = {}
    wrong_pair: dict[int, int] = {}
    for indices in by_family.values():
        within_family.update(rotate_indices(indices))
    global_map = rotate_indices(all_indices)
    for indices in by_scan.values():
        if len(indices) > 1:
            wrong_pair.update(rotate_indices(indices))
    for idx in all_indices:
        wrong_pair.setdefault(idx, global_map[idx])
    return {
        "raw_witness_shuffle_global": global_map,
        "raw_witness_shuffle_within_family": within_family,
        "wrong_pair_raw_witness": wrong_pair,
    }


def raw_witness_view(row: dict[str, Any], include_local_z: bool = True) -> dict[str, float]:
    features = {
        **row["coverage"],
        **row["witness"],
    }
    if include_local_z:
        features.update(row["family_local"])
    return features


def factorized_linear_view(row: dict[str, Any], include_local_z: bool = True) -> dict[str, float]:
    features = {
        **row["semantic"],
        **row["legacy_geometry"],
        **row["coverage"],
        **row["witness"],
        **row["disagreement"],
    }
    if include_local_z:
        features.update(row["family_local"])
    return features


def family_shrinkage_features(row: dict[str, Any]) -> dict[str, float]:
    witness = row["witness"]
    local = row["family_local"]
    support_gate = witness["support_contact_gate"]
    vertical_gate = witness["relative_vertical_gate"]
    return {
        "support_gate_x_gap_abs_local_z": support_gate * local["support_gap_abs_local_z"],
        "support_gate_x_xy_overlap_local_z": support_gate * local["support_xy_overlap_max_local_z"],
        "support_gate_x_distance_local_z": support_gate * local["support_distance_xy_local_z"],
        "vertical_gate_x_signed_margin_local_z": vertical_gate * local["vertical_signed_margin_local_z"],
        "vertical_gate_x_margin_abs_local_z": vertical_gate * local["vertical_margin_abs_local_z"],
        "vertical_gate_x_interval_overlap_local_z": vertical_gate * local["vertical_interval_overlap_local_z"],
        "support_gate_x_overconfidence": support_gate * row["disagreement"]["overconfidence_score"],
        "vertical_gate_x_underconfidence": vertical_gate * row["disagreement"]["underconfidence_score"],
    }


def build_views(prepared: list[dict[str, Any]]) -> None:
    shuffle_maps = shuffled_sources(prepared)
    for idx, row in enumerate(prepared):
        semantic = row["semantic"]
        legacy_geometry = row["legacy_geometry"]
        raw_only = raw_witness_view(row)
        semantic_raw = {**semantic, **raw_only}
        linear = factorized_linear_view(row)
        shrinkage = {**linear, **family_shrinkage_features(row)}
        endpoint = {**shrinkage, **endpoint_type_features(row)}
        baseline_inputs = {
            "semantic_only": semantic,
            "legacy_geometry_only": legacy_geometry,
            "semantic_plus_geometry": {**semantic, **legacy_geometry},
            "raw_witness_only_v2": raw_only,
            "semantic_plus_raw_witness_v2": semantic_raw,
            "factorized_reliability_posterior_v2_linear": linear,
            "factorized_reliability_posterior_v2_family_shrinkage": shrinkage,
            "endpoint_type_ablation": endpoint,
            "family_only_offset": {
                "support_contact_gate": row["witness"]["support_contact_gate"],
                "relative_vertical_gate": row["witness"]["relative_vertical_gate"],
            },
            "no_family_local_normalization": factorized_linear_view(row, include_local_z=False),
            "legacy_p_geom_only": legacy_geometry,
        }
        for view_name, index_map in shuffle_maps.items():
            source = prepared[index_map[idx]]
            shuffled = {
                **semantic,
                **legacy_geometry,
                **row["coverage"],
                **source["witness"],
                **source["family_local"],
                **row["disagreement"],
            }
            baseline_inputs[view_name] = shuffled
        row["baseline_inputs"] = baseline_inputs


def prepare_rows(rows: list[dict[str, Any]], raw_by_prediction: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    prepared = []
    for row in rows:
        prediction_id = str(row["identity"]["prediction_id"])
        raw = raw_by_prediction.get(prediction_id)
        raw_present = raw is not None
        if raw is None:
            raw = {field: 0.0 for field in RAW_FIELDS}
        semantic = semantic_block(row)
        legacy = legacy_geometry_block(row)
        coverage = coverage_block(row, raw_present)
        witness = witness_features(row, raw)
        disagreement = disagreement_features(semantic, legacy)
        prepared.append(
            {
                "source_row": row,
                "identity": row["identity"],
                "target": row["target"],
                "raw": raw,
                "semantic": semantic,
                "legacy_geometry": legacy,
                "coverage": coverage,
                "witness": witness,
                "disagreement": disagreement,
            }
        )
    stats = family_stats(prepared)
    add_local_z(prepared, stats)
    build_views(prepared)
    for row in prepared:
        row["family_stats"] = stats[str(row["identity"]["predicate_family"])]
    return prepared


def output_rows(prepared: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    for row in prepared:
        source = row["source_row"]
        outputs.append(
            {
                "schema_version": "h002_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_row_v1",
                "record_type": "h002_support_vertical_v2_revised_sampling_raw_witness_posterior_ready_row",
                "identity": source["identity"],
                "baseline_inputs": row["baseline_inputs"],
                "target": {
                    **source["target"],
                    "allowed_use": "train-only raw-witness v2 posterior smoke",
                },
                "provenance": {
                    **source["provenance"],
                    "source_feature_pool": "match_rows.geometry.raw_features + source_feature_join_v1",
                    "raw_witness_join_v2": True,
                    "raw_witness_as_model_input": True,
                    "geometry_status_as_model_input": False,
                    "free_family_or_predicate_categorical_input": False,
                    "validation_usage": False,
                    "test_usage": False,
                    "target_labels_as_model_input": False,
                    "review_fields_as_model_input": False,
                    "hidden_metadata_as_model_input": False,
                    "packet_paths_as_model_input": False,
                    "multi_view_as_model_input": False,
                },
            }
        )
    return outputs


def feature_leakage_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    leakage: list[dict[str, Any]] = []
    for row_index, row in enumerate(rows, start=1):
        for view_name, features in row.get("baseline_inputs", {}).items():
            for feature_name in features:
                lowered = feature_name.lower()
                for fragment in FORBIDDEN_MODEL_INPUT_FRAGMENTS:
                    if fragment in lowered:
                        leakage.append(
                            {
                                "row_index": row_index,
                                "prediction_id": row["identity"]["prediction_id"],
                                "view": view_name,
                                "feature_name": feature_name,
                                "forbidden_fragment": fragment,
                            }
                        )
    return leakage


def validate_rows(rows: list[dict[str, Any]], raw_summary: dict[str, Any], leakage: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if raw_summary["requested_prediction_ids"] != raw_summary["matched_prediction_ids"]:
        errors.append(
            {
                "error_type": "raw_witness_match_count_mismatch",
                "requested": raw_summary["requested_prediction_ids"],
                "matched": raw_summary["matched_prediction_ids"],
            }
        )
    if leakage:
        errors.append({"error_type": "feature_leakage_hits", "count": len(leakage)})
    seen = set()
    required_views = [*MAIN_V2_VIEWS, *CONTROL_VIEWS]
    for row_number, row in enumerate(rows, start=1):
        prediction_id = row.get("identity", {}).get("prediction_id")
        if prediction_id in seen:
            errors.append({"error_type": "duplicate_prediction_id", "row_number": row_number, "prediction_id": prediction_id})
        seen.add(prediction_id)
        if row.get("target", {}).get("y") not in {0, 1}:
            errors.append({"error_type": "non_binary_target", "row_number": row_number, "prediction_id": prediction_id})
        baseline_inputs = row.get("baseline_inputs", {})
        for view in required_views:
            if view not in baseline_inputs:
                errors.append({"error_type": "missing_input_view", "row_number": row_number, "prediction_id": prediction_id, "view": view})
        for forbidden_top in [
            "audit_only_user_confirmed_review_fields",
            "hidden_audit_metadata_post_label_only",
            "audit_packet_paths_not_model_input",
        ]:
            if forbidden_top in row:
                errors.append({"error_type": "forbidden_top_level_field_present", "row_number": row_number, "field": forbidden_top})
    return errors


def target_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(int(row["target"]["y"]) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "by_family": dict(sorted(Counter(str(row["identity"]["predicate_family"]) for row in rows).items())),
        "by_predicate": dict(sorted(Counter(str(row["identity"]["predicate_label"]) for row in rows).items())),
    }


def feature_ranges(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    values_by_name: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        for view, features in row["baseline_inputs"].items():
            for name, value in features.items():
                values_by_name.setdefault((view, name), []).append(safe_float(value))
    outputs = []
    for (view, name), values in sorted(values_by_name.items()):
        outputs.append(
            {
                "view": view,
                "feature": name,
                "rows": len(values),
                "min": min(values),
                "max": max(values),
                "mean": sum(values) / len(values),
            }
        )
    return outputs


def family_stats_rows(prepared: list[dict[str, Any]]) -> list[dict[str, Any]]:
    emitted = set()
    rows = []
    for row in prepared:
        family = str(row["identity"]["predicate_family"])
        if family in emitted:
            continue
        emitted.add(family)
        for feature, stat in sorted(row["family_stats"].items()):
            rows.append(
                {
                    "predicate_family": family,
                    "feature": feature,
                    "rows": stat["rows"],
                    "mean": stat["mean"],
                    "stdev": stat["stdev"],
                }
            )
    return rows


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Raw-Witness Feature Join V2",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only feature-join step.",
        "- No validation/test rows are used.",
        "- No posterior model is trained in this step.",
        "- Review fields, target labels, hidden construction axes, packet paths, multi-view evidence, and `geometry_status` shortcuts are not model inputs.",
        "- Results are hypothesis-stage artifacts, not paper-level metrics.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Target",
        "",
        "| Rows | Positive | Negative |",
        "| ---: | ---: | ---: |",
        f"| {summary['target_summary']['rows']} | {summary['target_summary']['positive']} | {summary['target_summary']['negative']} |",
        "",
        "## Raw Witness Join",
        "",
        f"- Requested prediction ids: `{summary['raw_witness_join']['requested_prediction_ids']}`",
        f"- Matched prediction ids: `{summary['raw_witness_join']['matched_prediction_ids']}`",
        f"- Match rows scanned: `{summary['raw_witness_join']['rows_scanned_until_complete']}`",
        f"- Raw fields: `{len(summary['raw_witness_join']['raw_fields'])}`",
        "",
        "## Views",
        "",
        "Main views:",
        "",
    ]
    for view in summary["input_contract_v2"]["main_views"]:
        lines.append(f"- `{view}`")
    lines.extend(["", "Control views:", ""])
    for view in summary["input_contract_v2"]["control_views"]:
        lines.append(f"- `{view}`")
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- validation errors: `{summary['validation_error_count']}`",
            f"- feature leakage hits: `{summary['feature_leakage_count']}`",
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    input_rows = read_jsonl(args.input_rows)
    repair_plan = read_json(args.repair_plan)
    prediction_ids = {str(row["identity"]["prediction_id"]) for row in input_rows}
    raw_by_prediction, raw_summary = load_raw_witness(args.match_rows, prediction_ids)
    prepared = prepare_rows(input_rows, raw_by_prediction)
    rows = output_rows(prepared)
    leakage = feature_leakage_rows(rows)
    validation_errors = validate_rows(rows, raw_summary, leakage)
    summary = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_summary_v1",
        "status": (
            "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_ready"
            if not validation_errors
            else "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_has_validation_errors"
        ),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "input_rows": rel_path(args.input_rows),
            "repair_plan": rel_path(args.repair_plan),
            "repair_plan_status": repair_plan.get("status"),
            "match_rows": rel_path(args.match_rows),
        },
        "output_dir": rel_path(output_dir),
        "target_mode": TARGET_MODE,
        "target_summary": target_summary(rows),
        "raw_witness_join": raw_summary,
        "input_contract_v2": {
            "schema_version": "h002_support_vertical_v2_revised_sampling_raw_witness_input_contract_v2",
            "allowed_model_input_root": "baseline_inputs",
            "main_views": MAIN_V2_VIEWS,
            "control_views": CONTROL_VIEWS,
            "raw_feature_source": "match_rows.geometry.raw_features",
            "allowed_inputs": [
                "source semantic score/rank after label lock",
                "legacy p_geom_valid as baseline/auxiliary scalar",
                "raw geometry witness values keyed by prediction_id",
                "deterministic typed witness gates",
                "train-only family-local raw residual normalization",
                "coverage/missingness indicators",
                "endpoint type ablation flags only in endpoint_type_ablation",
            ],
            "forbidden_as_model_input": [
                "review fields",
                "target labels",
                "hidden audit metadata",
                "packet paths",
                "multi-view evidence",
                "queue/role/rank-band construction axes",
                "geometry_status satisfied/unsatisfied shortcut",
                "free predicate/family categorical shortcut",
                "validation/test rows",
            ],
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_model": False,
            "raw_witness_as_model_input": True,
            "geometry_status_as_model_input": False,
            "free_family_or_predicate_categorical_input": False,
            "review_fields_as_model_input": False,
            "target_labels_as_model_input": False,
            "hidden_metadata_as_model_input": False,
            "packet_paths_as_model_input": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
        },
        "feature_leakage_count": len(leakage),
        "validation_error_count": len(validation_errors),
        "decision": (
            "Raw-witness v2 feature rows are ready for train-only posterior smoke. "
            "The artifact replaces collapsed geometry evidence with typed support/vertical witness blocks while "
            "preserving p_geom_valid as legacy geometry evidence."
        ),
        "claim_boundary": {
            "allowed": "Feature contract is ready for a v2 train-only posterior smoke.",
            "blocked": "No posterior performance claim is allowed until the v2 smoke and controls pass.",
        },
        "next_todo": "revised_sampling_all_label_ready_raw_witness_v2_posterior_smoke",
    }
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "input_contract_v2.json", summary["input_contract_v2"])
    write_jsonl(output_dir / "posterior_ready_rows.jsonl", rows)
    write_jsonl(output_dir / "feature_leakage.jsonl", leakage)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(output_dir / "feature_ranges.csv", feature_ranges(rows))
    write_csv(output_dir / "family_local_stats.csv", family_stats_rows(prepared))
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        "status={status} rows={rows} pos={pos} neg={neg} raw_matches={raw_matches}/{raw_requested} "
        "validation_errors={errors} leakage={leakage} validation_used={validation_used} next={next_todo}".format(
            status=summary["status"],
            rows=summary["target_summary"]["rows"],
            pos=summary["target_summary"]["positive"],
            neg=summary["target_summary"]["negative"],
            raw_matches=summary["raw_witness_join"]["matched_prediction_ids"],
            raw_requested=summary["raw_witness_join"]["requested_prediction_ids"],
            errors=summary["validation_error_count"],
            leakage=summary["feature_leakage_count"],
            validation_used=summary["boundary"]["validation_usage"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
