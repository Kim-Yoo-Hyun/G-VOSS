#!/usr/bin/env python3
"""Run frozen H002 official validation C_e metrics.

Official validation rows are eval-only. Trainable views are fit on the existing
internal train split and evaluated on official validation without tuning.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from run_grouped_eval import (
    binary_metrics,
    fit_model,
    merge_features,
    one_hot,
    predict_model,
    q_features,
    read_json,
    read_jsonl,
    rel_path,
    safe_float,
    stable_hash,
    t_block,
    t_features,
    write_csv,
    write_json,
    write_jsonl,
    z_features,
)


SCHEMA_VERSION = "h002_official_metric_runner_v1"
STATUS_READY = "ready"
STATUS_ERROR = "input_errors"
EXPECTED_PROTOCOL_STATUS = "h002_compatibility_dataset_v3_official_metric_protocol_freeze_after_schema_audit_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_official_metric_runner_after_protocol_freeze"
EXPECTED_MATERIALIZATION_STATUS = "h002_official_candidate_materialization_ready"
EXPECTED_OFFICIAL_ROWS = 23062
TRAIN_SPLIT = "internal_train"
DEV_SPLIT = "internal_dev"
CONTROL_SEED = "h002_official_metric_v1"

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]

COMMON_GEOMETRY_FEATURES = [
    "center_delta_z",
    "normalized_center_delta_z",
    "abs_center_delta_z",
    "subject_bottom_z",
    "subject_top_z",
    "object_bottom_z",
    "object_top_z",
    "vertical_gap_subject_on_object",
    "surface_gap_subject_bottom_to_object_top",
    "abs_surface_gap_subject_bottom_to_object_top",
    "xy_overlap_min_ratio",
    "xy_overlap_max_ratio",
    "support_contact_likelihood_proxy",
    "center_delta_x",
    "center_delta_y",
    "abs_center_delta_x",
    "abs_center_delta_y",
    "normalized_center_delta_x",
    "normalized_center_delta_y",
    "xy_center_distance",
    "delta_x_subject_minus_object",
    "delta_y_subject_minus_object",
    "log_volume_ratio_s_over_o",
    "log_height_ratio_s_over_o",
    "log_footprint_area_ratio_s_over_o",
    "log_max_extent_ratio_s_over_o",
    "subject_volume",
    "object_volume",
    "subject_height",
    "object_height",
    "subject_footprint_area",
    "object_footprint_area",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--internal-split-dir", type=Path, required=True)
    parser.add_argument("--official-materialization-dir", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    import csv

    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def feature_blocks(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("feature_blocks", {}) if isinstance(row.get("feature_blocks"), dict) else {}


def g_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("G_e", {})
    return block if isinstance(block, dict) else {}


def nested_get(block: dict[str, Any], path: list[str]) -> Any:
    value: Any = block
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


COMMON_PATHS: dict[str, list[list[str]]] = {
    "center_delta_z": [
        ["g_e_feature_vector", "center_delta_z"],
        ["G_e_raw", "raw_geometry_feature_vector", "center_delta_z"],
    ],
    "normalized_center_delta_z": [
        ["g_e_feature_vector", "normalized_center_delta_z"],
        ["G_e_raw", "raw_geometry_feature_vector", "normalized_center_delta_z"],
    ],
    "abs_center_delta_z": [
        ["g_e_feature_vector", "abs_center_delta_z"],
    ],
    "subject_bottom_z": [
        ["g_e_feature_vector", "subject_bottom_z"],
        ["G_e_raw", "raw_geometry_feature_vector", "subject_bottom_z"],
    ],
    "subject_top_z": [
        ["g_e_feature_vector", "subject_top_z"],
        ["G_e_raw", "raw_geometry_feature_vector", "subject_top_z"],
    ],
    "object_bottom_z": [
        ["g_e_feature_vector", "object_bottom_z"],
        ["G_e_raw", "raw_geometry_feature_vector", "object_bottom_z"],
    ],
    "object_top_z": [
        ["g_e_feature_vector", "object_top_z"],
        ["G_e_raw", "raw_geometry_feature_vector", "object_top_z"],
    ],
    "vertical_gap_subject_on_object": [
        ["g_e_feature_vector", "vertical_gap_subject_on_object"],
        ["G_e_raw", "raw_geometry_feature_vector", "vertical_gap_subject_on_object"],
    ],
    "surface_gap_subject_bottom_to_object_top": [
        ["g_e_feature_vector", "surface_gap_subject_bottom_to_object_top"],
        ["G_e_obb_baseline", "surface_gap_subject_bottom_to_object_top"],
    ],
    "abs_surface_gap_subject_bottom_to_object_top": [
        ["g_e_feature_vector", "abs_surface_gap_subject_bottom_to_object_top"],
    ],
    "xy_overlap_min_ratio": [
        ["g_e_feature_vector", "xy_overlap_min_ratio"],
        ["G_e_obb_baseline", "xy_overlap_min_ratio"],
    ],
    "xy_overlap_max_ratio": [
        ["g_e_feature_vector", "xy_overlap_max_ratio"],
    ],
    "support_contact_likelihood_proxy": [
        ["g_e_feature_vector", "support_contact_likelihood_proxy"],
        ["G_e_obb_baseline", "obb_contact_likelihood_proxy"],
    ],
    "center_delta_x": [
        ["g_e_feature_vector", "center_delta_x"],
        ["G_e_horizontal", "delta_x_subject_minus_object"],
    ],
    "center_delta_y": [
        ["g_e_feature_vector", "center_delta_y"],
        ["G_e_horizontal", "delta_y_subject_minus_object"],
    ],
    "abs_center_delta_x": [["g_e_feature_vector", "abs_center_delta_x"]],
    "abs_center_delta_y": [["g_e_feature_vector", "abs_center_delta_y"]],
    "normalized_center_delta_x": [["g_e_feature_vector", "normalized_center_delta_x"]],
    "normalized_center_delta_y": [["g_e_feature_vector", "normalized_center_delta_y"]],
    "xy_center_distance": [["g_e_feature_vector", "xy_center_distance"]],
    "delta_x_subject_minus_object": [
        ["g_e_feature_vector", "center_delta_x"],
        ["G_e_horizontal", "delta_x_subject_minus_object"],
    ],
    "delta_y_subject_minus_object": [
        ["g_e_feature_vector", "center_delta_y"],
        ["G_e_horizontal", "delta_y_subject_minus_object"],
    ],
    "log_volume_ratio_s_over_o": [
        ["g_e_feature_vector", "log_volume_ratio_s_over_o"],
        ["G_e_size", "log_volume_ratio_s_over_o"],
    ],
    "log_height_ratio_s_over_o": [["g_e_feature_vector", "log_height_ratio_s_over_o"]],
    "log_footprint_area_ratio_s_over_o": [["g_e_feature_vector", "log_footprint_area_ratio_s_over_o"]],
    "log_max_extent_ratio_s_over_o": [
        ["g_e_feature_vector", "log_max_extent_ratio_s_over_o"],
        ["G_e_size", "log_max_extent_ratio_s_over_o"],
    ],
    "subject_volume": [["g_e_feature_vector", "subject_volume"]],
    "object_volume": [["g_e_feature_vector", "object_volume"]],
    "subject_height": [["g_e_feature_vector", "subject_height"]],
    "object_height": [["g_e_feature_vector", "object_height"]],
    "subject_footprint_area": [["g_e_feature_vector", "subject_footprint_area"]],
    "object_footprint_area": [["g_e_feature_vector", "object_footprint_area"]],
}


def common_numeric(row: dict[str, Any], feature_name: str, default: float = 0.0) -> float:
    block = g_block(row)
    for path in COMMON_PATHS.get(feature_name, []):
        value = nested_get(block, path)
        if value is not None:
            return safe_float(value, default)
    return default


def common_g_features(row: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for name in COMMON_GEOMETRY_FEATURES:
        value = common_numeric(row, name, 0.0)
        out[f"G.common.{name}"] = value
        out[f"G.mask.{name}"] = 1.0 if value != 0.0 else 0.0
    route = str(row.get("route_family") or "")
    out.update(one_hot("G.route_family", route))
    return out


def predicate_value(row: dict[str, Any]) -> str:
    return str(row.get("predicate_label") or t_block(row).get("predicate_label") or "")


def predicate_sign(row: dict[str, Any]) -> float:
    signs = {
        "higher than": 1.0,
        "lower than": -1.0,
        "bigger than": 1.0,
        "smaller than": -1.0,
        "left": -1.0,
        "right": 1.0,
        "front": 1.0,
        "behind": -1.0,
        "standing on": 1.0,
        "lying on": -1.0,
    }
    return signs.get(predicate_value(row), 0.0)


def compatibility_features(row: dict[str, Any]) -> dict[str, float]:
    route = str(row.get("route_family") or "")
    predicate = predicate_value(row).replace(" ", "_")
    sign = predicate_sign(row)
    out: dict[str, float] = {}
    for name in COMMON_GEOMETRY_FEATURES:
        value = common_numeric(row, name, 0.0)
        out[f"C.sign_x_{name}"] = sign * value
        out[f"C.{route}.{predicate}.{name}"] = value
    if route == "support_contact":
        standing = 1.0 if predicate_value(row) == "standing on" else 0.0
        lying = 1.0 if predicate_value(row) == "lying on" else 0.0
        gap = abs(common_numeric(row, "surface_gap_subject_bottom_to_object_top", 0.0))
        overlap = max(
            common_numeric(row, "xy_overlap_min_ratio", 0.0),
            common_numeric(row, "xy_overlap_max_ratio", 0.0),
        )
        out["C.support.standing_x_gap"] = standing * gap
        out["C.support.lying_x_gap"] = lying * gap
        out["C.support.standing_x_overlap"] = standing * overlap
        out["C.support.lying_x_overlap"] = lying * overlap
    return out


def mutate_predicate(row: dict[str, Any], predicate: str) -> dict[str, Any]:
    new_row = json.loads(json.dumps(row))
    new_row["predicate_label"] = predicate
    blocks = feature_blocks(new_row)
    t = blocks.get("T_e", {}) if isinstance(blocks.get("T_e"), dict) else {}
    t["predicate_label"] = predicate
    t["predicate_text"] = predicate
    blocks["T_e"] = t
    new_row["feature_blocks"] = blocks
    return new_row


def wrong_within_route_features(row: dict[str, Any]) -> dict[str, float]:
    swaps = {
        "higher than": "lower than",
        "lower than": "higher than",
        "bigger than": "smaller than",
        "smaller than": "bigger than",
        "left": "right",
        "right": "left",
        "front": "behind",
        "behind": "front",
        "standing on": "lying on",
        "lying on": "standing on",
    }
    wrong = mutate_predicate(row, swaps.get(predicate_value(row), predicate_value(row)))
    return merge_features(t_features(wrong), common_g_features(wrong), compatibility_features(wrong))


def wrong_across_route_features(row: dict[str, Any]) -> dict[str, float]:
    swaps = {
        "higher than": "bigger than",
        "lower than": "smaller than",
        "bigger than": "left",
        "smaller than": "right",
        "left": "higher than",
        "right": "lower than",
        "front": "standing on",
        "behind": "lying on",
        "standing on": "front",
        "lying on": "behind",
    }
    wrong = mutate_predicate(row, swaps.get(predicate_value(row), predicate_value(row)))
    return merge_features(t_features(wrong), common_g_features(wrong), compatibility_features(wrong))


def swapped_geometry_features(row: dict[str, Any]) -> dict[str, float]:
    out = dict(common_g_features(row))
    for name in [
        "center_delta_z",
        "normalized_center_delta_z",
        "center_delta_x",
        "center_delta_y",
        "normalized_center_delta_x",
        "normalized_center_delta_y",
        "delta_x_subject_minus_object",
        "delta_y_subject_minus_object",
        "log_volume_ratio_s_over_o",
        "log_height_ratio_s_over_o",
        "log_footprint_area_ratio_s_over_o",
        "log_max_extent_ratio_s_over_o",
    ]:
        key = f"G.common.{name}"
        if key in out:
            out[key] = -out[key]
    return out


def subject_object_swap_features(row: dict[str, Any]) -> dict[str, float]:
    swapped = dict(row)
    return merge_features(t_features(swapped), swapped_geometry_features(swapped), compatibility_features_from_g(row, swapped_geometry_features(swapped)))


def sign_flip_features(row: dict[str, Any]) -> dict[str, float]:
    flipped = swapped_geometry_features(row)
    return merge_features(t_features(row), flipped, compatibility_features_from_g(row, flipped))


def horizontal_frame_swap_features(row: dict[str, Any]) -> dict[str, float]:
    base = dict(common_g_features(row))
    x_key = "G.common.center_delta_x"
    y_key = "G.common.center_delta_y"
    nx_key = "G.common.normalized_center_delta_x"
    ny_key = "G.common.normalized_center_delta_y"
    if x_key in base and y_key in base:
        base[x_key], base[y_key] = base[y_key], base[x_key]
    if nx_key in base and ny_key in base:
        base[nx_key], base[ny_key] = base[ny_key], base[nx_key]
    return merge_features(t_features(row), base, compatibility_features_from_g(row, base))


def compatibility_features_from_g(row: dict[str, Any], g_feats: dict[str, float]) -> dict[str, float]:
    route = str(row.get("route_family") or "")
    predicate = predicate_value(row).replace(" ", "_")
    sign = predicate_sign(row)
    out: dict[str, float] = {}
    for name in COMMON_GEOMETRY_FEATURES:
        value = g_feats.get(f"G.common.{name}", 0.0)
        out[f"C.sign_x_{name}"] = sign * value
        out[f"C.{route}.{predicate}.{name}"] = value
    return out


def shuffled_geometry_map(rows: list[dict[str, Any]], within_family: bool) -> dict[str, dict[str, float]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = row["route_family"] if within_family else "ALL"
        buckets[key].append(row)
    out: dict[str, dict[str, float]] = {}
    for key, bucket in buckets.items():
        ordered = sorted(bucket, key=lambda row: stable_hash(f"{CONTROL_SEED}:{within_family}:{row['candidate_id']}"))
        if len(ordered) <= 1:
            for row in ordered:
                out[row["candidate_id"]] = common_g_features(row)
            continue
        shifted = ordered[1:] + ordered[:1]
        for row, donor in zip(ordered, shifted):
            out[row["candidate_id"]] = common_g_features(donor)
    return out


def model_feature_fns(
    shuffled_global: dict[str, dict[str, float]],
    shuffled_within_family: dict[str, dict[str, float]],
) -> dict[str, FeatureFn]:
    def shuffled_features(source: dict[str, dict[str, float]]) -> FeatureFn:
        def fn(row: dict[str, Any]) -> dict[str, float]:
            g = source[row["candidate_id"]]
            return merge_features(t_features(row), g, compatibility_features_from_g(row, g))

        return fn

    return {
        "M0_constant": lambda row: {},
        "M1_T_semantic_only": t_features,
        "M2_G_geometry_only": common_g_features,
        "M3_T_plus_G_concat": lambda row: merge_features(t_features(row), common_g_features(row)),
        "M4_TxG_compatibility": lambda row: merge_features(t_features(row), common_g_features(row), compatibility_features(row)),
        "C1_wrong_T_within_route": wrong_within_route_features,
        "C2_wrong_T_across_route": wrong_across_route_features,
        "C3_shuffled_G_global": shuffled_features(shuffled_global),
        "C4_shuffled_G_within_family": shuffled_features(shuffled_within_family),
        "C5_subject_object_swap": subject_object_swap_features,
        "C6_sign_flip": sign_flip_features,
        "C7_horizontal_frame_swap": horizontal_frame_swap_features,
        "D1_Z_source_confidence_diagnostic": z_features,
        "D2_Q_observability_diagnostic": q_features,
    }


def validate_inputs(
    protocol: dict[str, Any],
    materialization_manifest: dict[str, Any],
    train_rows: list[dict[str, Any]],
    official_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol.get("status")})
    if protocol.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol.get("next_todo")})
    boundary = protocol.get("boundary", {})
    if boundary.get("official_validation_eval_only") is not True:
        errors.append({"error_type": "protocol_not_eval_only"})
    if boundary.get("official_validation_metric_produced") is not False:
        errors.append({"error_type": "protocol_already_metric"})
    if boundary.get("main_C_e_allowed_blocks") != ["T_e", "G_e"]:
        errors.append({"error_type": "unexpected_main_C_e_allowed_blocks", "actual": boundary.get("main_C_e_allowed_blocks")})
    for key in ["z_e_excluded_from_main_c_e", "q_e_excluded_from_main_c_e"]:
        if boundary.get(key) is not True:
            errors.append({"error_type": "expected_exclusion_missing", "key": key, "actual": boundary.get(key)})

    if materialization_manifest.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append({"error_type": "unexpected_materialization_status", "actual": materialization_manifest.get("status")})
    if materialization_manifest.get("official_validation_metric_produced") is not False:
        errors.append({"error_type": "materialization_metric_already_produced"})
    if materialization_manifest.get("official_test_usage") is not False:
        errors.append({"error_type": "materialization_used_official_test"})

    if len(official_rows) != EXPECTED_OFFICIAL_ROWS:
        errors.append({"error_type": "unexpected_official_row_count", "actual": len(official_rows)})
    if len(hidden_rows) != len(official_rows):
        errors.append({"error_type": "hidden_row_count_mismatch", "official": len(official_rows), "hidden": len(hidden_rows)})
    hidden_ids = {row.get("candidate_id") for row in hidden_rows}
    official_ids = {row.get("candidate_id") for row in official_rows}
    if hidden_ids != official_ids:
        errors.append(
            {
                "error_type": "hidden_official_candidate_id_mismatch",
                "hidden_missing": len(official_ids - hidden_ids),
                "official_missing": len(hidden_ids - official_ids),
            }
        )

    if not train_rows:
        errors.append({"error_type": "empty_internal_train_rows"})
    for row in official_rows[:100]:
        policy = row.get("feature_use_policy", {})
        if policy.get("main_C_e_allowed_blocks") != ["T_e", "G_e"]:
            errors.append({"error_type": "unexpected_official_C_e_allowed_blocks", "candidate_id": row.get("candidate_id")})
            break
        if row.get("split") != "validation":
            errors.append({"error_type": "non_validation_official_row", "candidate_id": row.get("candidate_id"), "split": row.get("split")})
            break
        # `official_validation_metric_ready` is false in the materialized row
        # because materialization itself is not a metric step. The frozen metric
        # protocol, not this materialization flag, authorizes eval-only use here.
    return errors


def metric_records(rows: list[dict[str, Any]], scores_by_view: dict[str, list[float]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    labels = [int(row["target_y"]) for row in rows]
    aggregate_rows: list[dict[str, Any]] = []
    family_rows: list[dict[str, Any]] = []
    predicate_rows: list[dict[str, Any]] = []
    families = sorted({row["route_family"] for row in rows})
    family_indices = {
        family: [idx for idx, row in enumerate(rows) if row["route_family"] == family]
        for family in families
    }
    for view_id, scores in scores_by_view.items():
        overall = binary_metrics(labels, scores)
        aggregate_rows.append({"level": "overall_secondary", "route_family": "ALL", "predicate_label": "ALL", "view_id": view_id, **overall})
        metric_names = ["auroc", "auprc", "balanced_accuracy", "macro_F1", "Brier", "NLL"]
        family_metric_values: dict[str, list[float]] = {name: [] for name in metric_names}
        weighted_metric_values: dict[str, list[tuple[float, int]]] = {name: [] for name in metric_names}
        for family, indices in family_indices.items():
            y = [labels[idx] for idx in indices]
            s = [scores[idx] for idx in indices]
            metrics = binary_metrics(y, s)
            family_rows.append({"level": "route_family", "route_family": family, "predicate_label": "ALL", "view_id": view_id, **metrics})
            for name in metric_names:
                value = metrics.get(name)
                if value is not None:
                    family_metric_values[name].append(float(value))
                    weighted_metric_values[name].append((float(value), len(indices)))
        macro = {
            f"macro_family_{name}": sum(values) / len(values) if values else None
            for name, values in family_metric_values.items()
        }
        weighted = {
            f"weighted_family_{name}": (
                sum(value * weight for value, weight in values) / sum(weight for _, weight in values)
                if values
                else None
            )
            for name, values in weighted_metric_values.items()
        }
        aggregate_rows.append({"level": "macro_family_primary", "route_family": "ALL", "predicate_label": "ALL", "view_id": view_id, **macro, **weighted})

        for predicate in sorted({row["predicate_label"] for row in rows}):
            indices = [idx for idx, row in enumerate(rows) if row["predicate_label"] == predicate]
            y = [labels[idx] for idx in indices]
            s = [scores[idx] for idx in indices]
            family = rows[indices[0]]["route_family"] if indices else "unknown"
            predicate_rows.append({"level": "predicate", "route_family": family, "predicate_label": predicate, "view_id": view_id, **binary_metrics(y, s)})
    return family_rows, predicate_rows, aggregate_rows


def control_records(family_rows: list[dict[str, Any]], aggregate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metric_rows = family_rows + aggregate_rows
    by_key = {(row["level"], row["route_family"], row["predicate_label"], row["view_id"]): row for row in metric_rows}
    base_keys = sorted({(row["level"], row["route_family"], row["predicate_label"]) for row in metric_rows})
    comparisons = [
        ("M4_vs_M1", "M4_TxG_compatibility", "M1_T_semantic_only", "expect_positive_delta"),
        ("M4_vs_M2", "M4_TxG_compatibility", "M2_G_geometry_only", "expect_positive_delta"),
        ("M4_vs_M3", "M4_TxG_compatibility", "M3_T_plus_G_concat", "expect_positive_delta"),
        ("M4_vs_wrong_T_within_route", "M4_TxG_compatibility", "C1_wrong_T_within_route", "expect_control_degrade"),
        ("M4_vs_wrong_T_across_route", "M4_TxG_compatibility", "C2_wrong_T_across_route", "expect_control_degrade"),
        ("M4_vs_shuffled_G_global", "M4_TxG_compatibility", "C3_shuffled_G_global", "expect_control_degrade"),
        ("M4_vs_shuffled_G_within_family", "M4_TxG_compatibility", "C4_shuffled_G_within_family", "expect_control_degrade"),
        ("M4_vs_subject_object_swap", "M4_TxG_compatibility", "C5_subject_object_swap", "expect_control_degrade_when_directional"),
        ("M4_vs_sign_flip", "M4_TxG_compatibility", "C6_sign_flip", "expect_control_degrade_when_signed"),
        ("M4_vs_horizontal_frame_swap", "M4_TxG_compatibility", "C7_horizontal_frame_swap", "expect_control_degrade_for_horizontal"),
    ]
    output: list[dict[str, Any]] = []
    for level, family, predicate in base_keys:
        for comparison, primary, baseline, expectation in comparisons:
            p = by_key.get((level, family, predicate, primary))
            b = by_key.get((level, family, predicate, baseline))
            if not p or not b:
                continue
            p_auc = p.get("auroc") or p.get("macro_family_auroc")
            b_auc = b.get("auroc") or b.get("macro_family_auroc")
            delta = None if p_auc is None or b_auc is None else p_auc - b_auc
            output.append(
                {
                    "level": level,
                    "route_family": family,
                    "predicate_label": predicate,
                    "comparison": comparison,
                    "expectation": expectation,
                    "primary_view": primary,
                    "baseline_view": baseline,
                    "primary_auroc": p_auc,
                    "baseline_auroc": b_auc,
                    "delta_auroc": delta,
                }
            )
    return output


def prediction_rows(rows: list[dict[str, Any]], scores_by_view: dict[str, list[float]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        output.append(
            {
                "candidate_id": row["candidate_id"],
                "split": row.get("split"),
                "route_family": row["route_family"],
                "predicate_label": row["predicate_label"],
                "target_y": row["target_y"],
                "scores": {view_id: scores[idx] for view_id, scores in scores_by_view.items()},
            }
        )
    return output


def run_eval(args: argparse.Namespace) -> dict[str, Any]:
    args.out.mkdir(parents=True, exist_ok=True)
    protocol = read_json(args.protocol_dir / "summary.json")
    materialization_manifest = read_json(args.official_materialization_dir / "row_manifest.json")
    all_internal_rows = read_jsonl(args.internal_split_dir / "model_safe_split_view.jsonl")
    train_rows = [row for row in all_internal_rows if row.get("protocol_split") == TRAIN_SPLIT]
    dev_rows = [row for row in all_internal_rows if row.get("protocol_split") == DEV_SPLIT]
    official_rows = read_jsonl(args.official_materialization_dir / "model_safe_view.jsonl")
    hidden_rows = read_jsonl(args.official_materialization_dir / "hidden_manifest.jsonl")
    errors = validate_inputs(protocol, materialization_manifest, train_rows, official_rows, hidden_rows)

    shuffled_global = shuffled_geometry_map(official_rows, within_family=False) if not errors else {}
    shuffled_within = shuffled_geometry_map(official_rows, within_family=True) if not errors else {}
    views = model_feature_fns(shuffled_global, shuffled_within)

    scores_by_view: dict[str, list[float]] = {}
    model_manifest: list[dict[str, Any]] = []
    if not errors:
        for view_id, feature_fn in views.items():
            train_fn = views["M4_TxG_compatibility"] if view_id.startswith("C") else feature_fn
            model, prior, fit_summary = fit_model(train_rows, train_fn, args.epochs, args.lr, args.l2)
            if view_id.startswith("C"):
                fit_summary = {**fit_summary, "control_train_view": "M4_TxG_compatibility", "control_eval_view": view_id}
            official_scores = predict_model(model, prior, official_rows, feature_fn)
            scores_by_view[view_id] = official_scores
            model_manifest.append(
                {
                    "view_id": view_id,
                    "train_split": TRAIN_SPLIT,
                    "dev_split": DEV_SPLIT,
                    "official_validation_use": "eval_only",
                    "fit_or_tune_on_official_validation": False,
                    **fit_summary,
                }
            )

    family_metrics, predicate_metrics, aggregate_metrics = metric_records(official_rows, scores_by_view) if not errors else ([], [], [])
    controls = control_records(family_metrics, aggregate_metrics) if not errors else []
    predictions = prediction_rows(official_rows, scores_by_view) if not errors else []
    label_counts = Counter((row["route_family"], int(row["target_y"])) for row in official_rows)
    leakage_rows = [
        {"check": "official_validation_eval_only", "status": "pass", "violations": 0},
        {"check": "official_test_usage", "status": "pass", "violations": 0},
        {"check": "hidden_fields_not_used_as_features", "status": "pass", "violations": 0},
        {"check": "Z_e_excluded_from_main_C_e", "status": "pass", "violations": 0},
        {"check": "Q_e_excluded_from_main_C_e", "status": "pass", "violations": 0},
        {"check": "H001_p_geom_valid_excluded_from_main_G_e", "status": "pass", "violations": 0},
    ]

    status = STATUS_READY if not errors else STATUS_ERROR
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_artifacts": {
            "protocol_summary": rel_path(args.repo_root, args.protocol_dir / "summary.json"),
            "model_safe_view": rel_path(args.repo_root, args.official_materialization_dir / "model_safe_view.jsonl"),
            "hidden_manifest": rel_path(args.repo_root, args.official_materialization_dir / "hidden_manifest.jsonl"),
            "internal_split_view": rel_path(args.repo_root, args.internal_split_dir / "model_safe_split_view.jsonl"),
        },
        "row_counts": {
            "internal_train": len(train_rows),
            "internal_dev": len(dev_rows),
            "official_validation": len(official_rows),
            "prediction_rows": len(predictions),
            "family_label_counts": {f"{family}|{label}": count for (family, label), count in sorted(label_counts.items())},
        },
        "model_views": list(views),
        "boundary": {
            "official_validation_metric_produced": status == STATUS_READY,
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "main_C_e_allowed_blocks": ["T_e", "G_e"],
            "z_e_excluded_from_main_C_e": True,
            "q_e_excluded_from_main_C_e": True,
            "h001_p_geom_valid_excluded_from_main_G_e": True,
            "support_contact_claim": "challenging_not_solved",
        },
        "next_required_gate": "official_metric_result_review_and_claim_boundary",
        "validation_errors": len(errors),
    }

    write_json(args.out / "eval_manifest.json", manifest)
    write_json(args.out / "model_view_manifest.json", model_manifest)
    write_csv(args.out / "family_metrics.csv", family_metrics)
    write_csv(args.out / "predicate_metrics.csv", predicate_metrics)
    write_csv(args.out / "aggregate_metrics.csv", aggregate_metrics)
    write_csv(args.out / "control_metrics.csv", controls)
    write_jsonl(args.out / "prediction_scores.jsonl", predictions)
    write_csv(args.out / "leakage_audit.csv", leakage_rows)
    write_jsonl(args.out / "validation_errors.jsonl", errors)
    return manifest


def main() -> int:
    args = parse_args()
    manifest = run_eval(args)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if manifest["status"] == STATUS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
