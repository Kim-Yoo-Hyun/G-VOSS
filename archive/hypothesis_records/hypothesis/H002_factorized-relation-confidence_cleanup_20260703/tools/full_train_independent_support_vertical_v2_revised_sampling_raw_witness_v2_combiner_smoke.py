#!/usr/bin/env python3
"""Combiner smoke for H002 raw-witness v2 posterior candidates."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke
import full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke as base


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INPUT_ROWS = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/posterior_ready_rows.jsonl"
)
DEFAULT_FEATURE_JOIN_SUMMARY = (
    RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/summary.json"
)
DEFAULT_PLAN_SUMMARY = (
    RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_repair_plan_all_label_ready/summary.json"
)
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_all_label_ready"

TARGET_MODE = "rank_band_balanced_revised_sampling"
LEGACY_REFERENCE = "C0_semantic_plus_geometry_legacy"
PRIMARY_REFERENCE = "C3_linear_v2"
NEW_CANDIDATES = [
    "C4_calibrated_linear_v2",
    "C5_constrained_monotonic_additive",
    "C6_family_gated_calibrated_mixture",
    "C7_limited_interaction_model",
]
MAIN_VIEWS = [
    LEGACY_REFERENCE,
    "C1_raw_witness_only_v2",
    "C2_semantic_plus_raw_witness_v2",
    PRIMARY_REFERENCE,
    *NEW_CANDIDATES,
    "C8_endpoint_type_ablation_only",
]
CONTROL_VIEWS = [
    "K0_global_raw_witness_shuffle",
    "K1_within_family_raw_witness_shuffle",
    "K2_wrong_pair_raw_witness",
    "K3_family_only_offset",
    "K4_no_family_local_normalization",
    "K5_endpoint_type_only",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-rows", type=Path, default=DEFAULT_INPUT_ROWS)
    parser.add_argument("--feature-join-summary", type=Path, default=DEFAULT_FEATURE_JOIN_SUMMARY)
    parser.add_argument("--plan-summary", type=Path, default=DEFAULT_PLAN_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
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


def sf(features: dict[str, Any], key: str, default: float = 0.0) -> float:
    return smoke.safe_float(features.get(key), default)


def subset(features: dict[str, Any], keys: list[str]) -> dict[str, float]:
    return {key: sf(features, key) for key in keys}


def rename(prefix: str, features: dict[str, Any], keys: list[str]) -> dict[str, float]:
    return {f"{prefix}_{key}": sf(features, key) for key in keys}


def build_calibrated_linear(row: dict[str, Any]) -> dict[str, float]:
    linear = row["baseline_inputs"]["factorized_reliability_posterior_v2_linear"]
    raw = row["baseline_inputs"]["raw_witness_only_v2"]
    features = subset(
        linear,
        [
            "semantic_score_norm",
            "negative_semantic_score_norm",
            "semantic_rank_inverse",
            "semantic_rank_log",
            "p_geom_valid",
            "p_geom_invalid",
            "consistency_score",
            "strong_raw_witness_score",
            "weak_raw_witness_score",
            "semantic_minus_geometry",
            "geometry_minus_semantic",
            "semantic_geometry_gap_abs",
            "semantic_geometry_gap_abs_local_z",
            "raw_witness_missing_flag",
            "support_contact_gate",
            "relative_vertical_gate",
            "support_contact_boundary_flag",
            "vertical_boundary_flag",
            "underconfidence_score",
            "overconfidence_score",
        ],
    )
    features.update(
        {
            "raw_minus_p_geom": sf(raw, "strong_raw_witness_score", 0.5) - sf(linear, "p_geom_valid", 0.5),
            "raw_present": 1.0 - sf(raw, "raw_witness_missing_flag"),
            "support_nonboundary": 1.0 - sf(raw, "support_contact_boundary_flag"),
            "vertical_nonboundary": 1.0 - sf(raw, "vertical_boundary_flag"),
        }
    )
    return features


def build_monotonic_additive(row: dict[str, Any]) -> dict[str, float]:
    raw = row["baseline_inputs"]["raw_witness_only_v2"]
    semantic = row["baseline_inputs"]["semantic_only"]
    support_score = (
        sf(raw, "support_gap_closeness")
        + sf(raw, "support_distance_closeness")
        + sf(raw, "support_xy_overlap_max")
        + sf(raw, "support_iou_xy")
    ) / 4.0
    vertical_score = (
        sf(raw, "vertical_sign_agreement")
        + sf(raw, "vertical_interval_overlap")
        + (1.0 / (1.0 + sf(raw, "vertical_margin_abs")))
    ) / 3.0
    support_gate = sf(raw, "support_contact_gate")
    vertical_gate = sf(raw, "relative_vertical_gate")
    return {
        "semantic_score_norm": sf(semantic, "semantic_score_norm"),
        "semantic_rank_inverse": sf(semantic, "semantic_rank_inverse"),
        "semantic_rank_log_inverse": 1.0 / (1.0 + sf(semantic, "semantic_rank_log")),
        "strong_raw_witness_score": sf(raw, "strong_raw_witness_score"),
        "weak_raw_witness_score": sf(raw, "weak_raw_witness_score"),
        "typed_support_score": support_gate * support_score,
        "typed_vertical_score": vertical_gate * vertical_score,
        "support_contact_gate": support_gate,
        "relative_vertical_gate": vertical_gate,
        "raw_present": 1.0 - sf(raw, "raw_witness_missing_flag"),
        "support_nonboundary": 1.0 - sf(raw, "support_contact_boundary_flag"),
        "vertical_nonboundary": 1.0 - sf(raw, "vertical_boundary_flag"),
        "coverage_evidence_ready": sf(raw, "coverage_evidence_ready"),
        "semantic_raw_agreement": 1.0 - abs(sf(semantic, "semantic_score_norm") - sf(raw, "strong_raw_witness_score")),
    }


def build_family_gated_mixture(row: dict[str, Any]) -> dict[str, float]:
    raw = row["baseline_inputs"]["raw_witness_only_v2"]
    linear = row["baseline_inputs"]["factorized_reliability_posterior_v2_linear"]
    semantic = row["baseline_inputs"]["semantic_only"]
    support_gate = sf(raw, "support_contact_gate")
    vertical_gate = sf(raw, "relative_vertical_gate")
    features = {
        "semantic_score_norm": sf(semantic, "semantic_score_norm"),
        "semantic_rank_inverse": sf(semantic, "semantic_rank_inverse"),
        "raw_present": 1.0 - sf(raw, "raw_witness_missing_flag"),
        "support_gate": support_gate,
        "vertical_gate": vertical_gate,
        "support_semantic_score": support_gate * sf(semantic, "semantic_score_norm"),
        "support_p_geom_valid": support_gate * sf(linear, "p_geom_valid", 0.5),
        "support_strong_raw": support_gate * sf(raw, "strong_raw_witness_score"),
        "support_gap_closeness": support_gate * sf(raw, "support_gap_closeness"),
        "support_distance_closeness": support_gate * sf(raw, "support_distance_closeness"),
        "support_iou_xy": support_gate * sf(raw, "support_iou_xy"),
        "support_overlap_max": support_gate * sf(raw, "support_xy_overlap_max"),
        "support_gap_abs_local_z": support_gate * sf(raw, "support_gap_abs_local_z"),
        "support_nonboundary": support_gate * (1.0 - sf(raw, "support_contact_boundary_flag")),
        "vertical_semantic_score": vertical_gate * sf(semantic, "semantic_score_norm"),
        "vertical_p_geom_valid": vertical_gate * sf(linear, "p_geom_valid", 0.5),
        "vertical_strong_raw": vertical_gate * sf(raw, "strong_raw_witness_score"),
        "vertical_sign_agreement": vertical_gate * sf(raw, "vertical_sign_agreement"),
        "vertical_interval_overlap": vertical_gate * sf(raw, "vertical_interval_overlap"),
        "vertical_margin_abs_local_z": vertical_gate * sf(raw, "vertical_margin_abs_local_z"),
        "vertical_signed_margin_local_z": vertical_gate * sf(raw, "vertical_signed_margin_local_z"),
        "vertical_nonboundary": vertical_gate * (1.0 - sf(raw, "vertical_boundary_flag")),
    }
    return features


def build_limited_interaction(row: dict[str, Any]) -> dict[str, float]:
    features = build_family_gated_mixture(row)
    raw = row["baseline_inputs"]["raw_witness_only_v2"]
    linear = row["baseline_inputs"]["factorized_reliability_posterior_v2_linear"]
    semantic = row["baseline_inputs"]["semantic_only"]
    semantic_score = sf(semantic, "semantic_score_norm")
    strong_raw = sf(raw, "strong_raw_witness_score")
    support_gate = sf(raw, "support_contact_gate")
    vertical_gate = sf(raw, "relative_vertical_gate")
    features.update(
        {
            "semantic_x_raw": semantic_score * strong_raw,
            "semantic_x_p_geom": semantic_score * sf(linear, "p_geom_valid", 0.5),
            "raw_x_consistency": strong_raw * sf(linear, "consistency_score", 0.5),
            "support_gate_x_gap_closeness": support_gate * sf(raw, "support_gap_closeness"),
            "support_gate_x_distance_closeness": support_gate * sf(raw, "support_distance_closeness"),
            "support_gate_x_iou": support_gate * sf(raw, "support_iou_xy"),
            "support_gate_x_overconfidence": support_gate * sf(linear, "overconfidence_score"),
            "vertical_gate_x_sign": vertical_gate * sf(raw, "vertical_sign_agreement"),
            "vertical_gate_x_margin_abs": vertical_gate * sf(raw, "vertical_margin_abs_local_z"),
            "vertical_gate_x_underconfidence": vertical_gate * sf(linear, "underconfidence_score"),
            "raw_minus_p_geom": strong_raw - sf(linear, "p_geom_valid", 0.5),
        }
    )
    return features


def build_endpoint_only(row: dict[str, Any]) -> dict[str, float]:
    endpoint = row["baseline_inputs"]["endpoint_type_ablation"]
    return subset(
        endpoint,
        [
            "endpoint_object_floor_like_flag",
            "endpoint_object_support_surface_like_flag",
            "endpoint_object_wall_like_flag",
            "endpoint_subject_room_surface_flag",
            "support_contact_gate",
            "relative_vertical_gate",
        ],
    )


def extend_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    extended = json.loads(json.dumps(rows))
    for row in extended:
        base_inputs = row["baseline_inputs"]
        base_inputs[LEGACY_REFERENCE] = dict(base_inputs["semantic_plus_geometry"])
        base_inputs["C1_raw_witness_only_v2"] = dict(base_inputs["raw_witness_only_v2"])
        base_inputs["C2_semantic_plus_raw_witness_v2"] = dict(base_inputs["semantic_plus_raw_witness_v2"])
        base_inputs[PRIMARY_REFERENCE] = dict(base_inputs["factorized_reliability_posterior_v2_linear"])
        base_inputs["C4_calibrated_linear_v2"] = build_calibrated_linear(row)
        base_inputs["C5_constrained_monotonic_additive"] = build_monotonic_additive(row)
        base_inputs["C6_family_gated_calibrated_mixture"] = build_family_gated_mixture(row)
        base_inputs["C7_limited_interaction_model"] = build_limited_interaction(row)
        base_inputs["C8_endpoint_type_ablation_only"] = dict(base_inputs["endpoint_type_ablation"])
        base_inputs["K0_global_raw_witness_shuffle"] = dict(base_inputs["raw_witness_shuffle_global"])
        base_inputs["K1_within_family_raw_witness_shuffle"] = dict(base_inputs["raw_witness_shuffle_within_family"])
        base_inputs["K2_wrong_pair_raw_witness"] = dict(base_inputs["wrong_pair_raw_witness"])
        base_inputs["K3_family_only_offset"] = dict(base_inputs["family_only_offset"])
        base_inputs["K4_no_family_local_normalization"] = dict(base_inputs["no_family_local_normalization"])
        base_inputs["K5_endpoint_type_only"] = build_endpoint_only(row)
    return extended


def target_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(smoke.target_y(row) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "by_family": dict(sorted(Counter(str(row["identity"]["predicate_family"]) for row in rows).items())),
        "by_predicate": dict(sorted(Counter(str(row["identity"]["predicate_label"]) for row in rows).items())),
        "by_scan_rows": dict(sorted(Counter(str(row["identity"]["scan_id"]) for row in rows).items())),
    }


def metric_record(kind: str, split_eval: str, name: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": kind,
        "target_mode": TARGET_MODE,
        "split_eval": split_eval,
        "name": name,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


def comparison(metric_rows: list[dict[str, Any]], split_eval: str, left: str, right: str) -> dict[str, Any]:
    by_name = {row["name"]: row["metrics"] for row in metric_rows if row["split_eval"] == split_eval}
    left_metrics = by_name.get(left, {})
    right_metrics = by_name.get(right, {})
    delta = {}
    for key in ["auroc", "auprc", "brier", "ece_5bin", "accuracy_at_0_5"]:
        if left_metrics.get(key) is None or right_metrics.get(key) is None:
            delta[key] = None
        else:
            delta[key] = left_metrics[key] - right_metrics[key]
    return {"split_eval": split_eval, "left": left, "right": right, "delta": delta}


def transfer_summary(rows: list[dict[str, Any]], score_by_view: dict[str, list[float]], reference: str) -> list[dict[str, Any]]:
    outputs = []
    ref_scores = score_by_view[reference]
    for view, scores in score_by_view.items():
        if view == reference:
            continue
        counts = Counter()
        for row, score, ref_score in zip(rows, scores, ref_scores):
            y = smoke.target_y(row)
            view_correct = int(score >= 0.5) == y
            ref_correct = int(ref_score >= 0.5) == y
            if view_correct and not ref_correct:
                counts["view_fixes_reference_error"] += 1
            elif ref_correct and not view_correct:
                counts["view_adds_error"] += 1
            elif view_correct and ref_correct:
                counts["both_correct"] += 1
            else:
                counts["both_wrong"] += 1
        outputs.append(
            {
                "view": view,
                "reference_view": reference,
                "rows": len(rows),
                "view_fixes_reference_error": counts["view_fixes_reference_error"],
                "view_adds_error": counts["view_adds_error"],
                "both_correct": counts["both_correct"],
                "both_wrong": counts["both_wrong"],
                "new_errors_minus_fixes": counts["view_adds_error"] - counts["view_fixes_reference_error"],
            }
        )
    return outputs


def family_delta_rows(family_slices: list[dict[str, Any]], left: str, right: str) -> list[dict[str, Any]]:
    by_key = {(row["predicate_family"], row["view"]): row for row in family_slices}
    outputs = []
    for family in sorted({row["predicate_family"] for row in family_slices}):
        left_row = by_key.get((family, left))
        right_row = by_key.get((family, right))
        if not left_row or not right_row:
            continue
        left_metrics = left_row["metrics"]
        right_metrics = right_row["metrics"]
        output = {
            "predicate_family": family,
            "left": left,
            "right": right,
            "delta_auroc": None,
            "delta_auprc": None,
            "delta_brier": None,
            "delta_ece_5bin": None,
            "delta_accuracy_at_0_5": None,
        }
        for metric, key in [
            ("auroc", "delta_auroc"),
            ("auprc", "delta_auprc"),
            ("brier", "delta_brier"),
            ("ece_5bin", "delta_ece_5bin"),
            ("accuracy_at_0_5", "delta_accuracy_at_0_5"),
        ]:
            if left_metrics.get(metric) is not None and right_metrics.get(metric) is not None:
                output[key] = left_metrics[metric] - right_metrics[metric]
        outputs.append(output)
    return outputs


def validate_inputs(
    rows: list[dict[str, Any]],
    feature_join_summary: dict[str, Any],
    plan_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    errors = []
    boundary = feature_join_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "review_fields_as_model_input",
        "hidden_metadata_as_model_input",
        "target_labels_as_model_input",
        "packet_paths_as_model_input",
        "multi_view_as_model_input",
        "geometry_status_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "feature_join_boundary_not_false", "field": key, "value": boundary.get(key)})
    if feature_join_summary.get("validation_error_count") != 0:
        errors.append({"error_type": "feature_join_validation_errors_present", "count": feature_join_summary.get("validation_error_count")})
    if feature_join_summary.get("feature_leakage_count") != 0:
        errors.append({"error_type": "feature_join_leakage_present", "count": feature_join_summary.get("feature_leakage_count")})
    if plan_summary.get("next_todo") != "revised_sampling_all_label_ready_raw_witness_v2_combiner_smoke":
        errors.append({"error_type": "unexpected_plan_next_todo", "value": plan_summary.get("next_todo")})
    if plan_summary.get("boundary", {}).get("validation_usage") is not False:
        errors.append({"error_type": "plan_uses_validation"})
    required_original = {
        "semantic_plus_geometry",
        "raw_witness_only_v2",
        "semantic_plus_raw_witness_v2",
        "factorized_reliability_posterior_v2_linear",
        "endpoint_type_ablation",
        "raw_witness_shuffle_global",
        "raw_witness_shuffle_within_family",
        "wrong_pair_raw_witness",
        "family_only_offset",
        "no_family_local_normalization",
    }
    for idx, row in enumerate(rows, start=1):
        if row.get("record_type") != "h002_support_vertical_v2_revised_sampling_raw_witness_posterior_ready_row":
            errors.append({"error_type": "unexpected_record_type", "row_number": idx, "record_type": row.get("record_type")})
        missing = required_original - set(row.get("baseline_inputs", {}))
        if missing:
            errors.append({"error_type": "missing_required_original_views", "row_number": idx, "missing": sorted(missing)})
        provenance = row.get("provenance", {})
        if provenance.get("validation_usage") is not False or provenance.get("test_usage") is not False:
            errors.append({"error_type": "row_split_boundary_violation", "row_number": idx})
    return errors


def pick_delta(comparisons: list[dict[str, Any]], split_eval: str, left: str, right: str) -> dict[str, Any]:
    for row in comparisons:
        if row["split_eval"] == split_eval and row["left"] == left and row["right"] == right:
            return row["delta"]
    raise KeyError(f"missing comparison: {split_eval} {left} {right}")


def pick_transfer(transfers: list[dict[str, Any]], view: str, reference: str) -> dict[str, Any]:
    for row in transfers:
        if row["view"] == view and row["reference_view"] == reference:
            return row
    raise KeyError(f"missing transfer: {view} vs {reference}")


def pick_family_delta(family_deltas: list[dict[str, Any]], family: str, left: str, right: str) -> dict[str, Any]:
    for row in family_deltas:
        if row["predicate_family"] == family and row["left"] == left and row["right"] == right:
            return row
    return {}


def evaluate_gates(
    comparisons: list[dict[str, Any]],
    transfers_vs_linear: list[dict[str, Any]],
    family_deltas: list[dict[str, Any]],
) -> dict[str, Any]:
    candidate_results = []
    for candidate in NEW_CANDIDATES:
        delta = pick_delta(comparisons, "train_internal_grouped_by_scan", candidate, PRIMARY_REFERENCE)
        transfer = pick_transfer(transfers_vs_linear, candidate, PRIMARY_REFERENCE)
        support_vs_legacy = pick_family_delta(family_deltas, "support_contact", candidate, LEGACY_REFERENCE)
        vertical_vs_legacy = pick_family_delta(family_deltas, "relative_vertical", candidate, LEGACY_REFERENCE)
        gate_pass = (
            delta.get("auprc") is not None
            and delta["auprc"] >= 0.0
            and delta.get("brier") is not None
            and delta["brier"] <= 0.0
            and delta.get("ece_5bin") is not None
            and delta["ece_5bin"] <= 0.0
            and transfer["new_errors_minus_fixes"] <= 0
            and support_vs_legacy.get("delta_auprc") is not None
            and support_vs_legacy["delta_auprc"] >= 0.10
            and support_vs_legacy.get("delta_brier") is not None
            and support_vs_legacy["delta_brier"] <= 0.0
            and vertical_vs_legacy.get("delta_auprc") is not None
            and vertical_vs_legacy["delta_auprc"] >= 0.0
            and vertical_vs_legacy.get("delta_brier") is not None
            and vertical_vs_legacy["delta_brier"] <= 0.0
        )
        fallback_pass = (
            delta.get("auprc") is not None
            and delta["auprc"] >= -0.01
            and (
                (delta.get("brier") is not None and delta["brier"] <= 0.0)
                or (delta.get("ece_5bin") is not None and delta["ece_5bin"] <= 0.0)
                or transfer["new_errors_minus_fixes"] <= 0
            )
        )
        candidate_results.append(
            {
                "candidate": candidate,
                "delta_vs_linear": delta,
                "transfer_vs_linear": transfer,
                "support_vs_legacy": support_vs_legacy,
                "vertical_vs_legacy": vertical_vs_legacy,
                "primary_gate_pass": gate_pass,
                "fallback_calibration_gate_pass": fallback_pass,
            }
        )
    primary_passes = [row for row in candidate_results if row["primary_gate_pass"]]
    fallback_passes = [row for row in candidate_results if row["fallback_calibration_gate_pass"]]
    best_by_auprc = max(
        candidate_results,
        key=lambda row: (
            row["delta_vs_linear"].get("auprc") if row["delta_vs_linear"].get("auprc") is not None else -999.0,
            -(row["delta_vs_linear"].get("brier") if row["delta_vs_linear"].get("brier") is not None else 999.0),
        ),
    )
    return {
        "candidate_results": candidate_results,
        "primary_gate_passes": [row["candidate"] for row in primary_passes],
        "fallback_calibration_gate_passes": [row["candidate"] for row in fallback_passes],
        "best_by_grouped_auprc_delta_vs_linear": best_by_auprc["candidate"],
    }


def classify_status(validation_errors: list[dict[str, Any]], gate_eval: dict[str, Any]) -> tuple[str, str, str]:
    if validation_errors:
        return (
            "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_input_errors",
            "Fix combiner smoke input contract errors before interpreting metrics.",
            "fix_revised_sampling_all_label_ready_raw_witness_v2_combiner_smoke_inputs",
        )
    if gate_eval["primary_gate_passes"]:
        return (
            "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_primary_pass",
            "At least one repaired combiner passes the train-only primary gate against C3_linear_v2. Treat this as hypothesis-stage evidence only.",
            "revised_sampling_all_label_ready_raw_witness_v2_combiner_error_analysis",
        )
    if gate_eval["fallback_calibration_gate_passes"]:
        return (
            "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_calibration_candidate",
            "No repaired combiner passes the full primary gate, but at least one candidate is close enough to linear while improving calibration/threshold behavior. Analyze it as calibration repair, not ranking improvement.",
            "revised_sampling_all_label_ready_raw_witness_v2_combiner_error_analysis",
        )
    return (
        "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_smoke_no_new_primary",
        "No repaired combiner beats or calibrates against C3_linear_v2 under the predeclared train-only gates. Keep C3_linear_v2 as the current reference and diagnose candidate failures.",
        "revised_sampling_all_label_ready_raw_witness_v2_combiner_error_analysis",
    )


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Raw-Witness V2 Combiner Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage combiner smoke.",
        "- No validation/test rows are used.",
        "- Review fields, hidden audit metadata, target labels, packet paths, multi-view evidence, and geometry_status are not model inputs.",
        "- Results are not paper-level metrics.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Grouped Main Views",
        "",
        "| View | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["metric_rows"]:
        if row["kind"] != "main" or row["split_eval"] != "train_internal_grouped_by_scan":
            continue
        metrics = row["metrics"]
        lines.append(
            f"| `{row['name']}` | {fmt(metrics['auroc'])} | {fmt(metrics['auprc'])} | "
            f"{fmt(metrics['brier'])} | {fmt(metrics['ece_5bin'])} | {fmt(metrics['accuracy_at_0_5'])} |"
        )
    lines.extend(
        [
            "",
            "## Candidate Deltas Vs C3 Linear",
            "",
            "| Candidate | dAUROC | dAUPRC | dBrier | dECE | dAcc | New-Fix | Primary Gate | Fallback |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in summary["gate_evaluation"]["candidate_results"]:
        delta = row["delta_vs_linear"]
        transfer = row["transfer_vs_linear"]
        lines.append(
            f"| `{row['candidate']}` | {fmt(delta['auroc'])} | {fmt(delta['auprc'])} | "
            f"{fmt(delta['brier'])} | {fmt(delta['ece_5bin'])} | {fmt(delta['accuracy_at_0_5'])} | "
            f"{transfer['new_errors_minus_fixes']} | `{row['primary_gate_pass']}` | "
            f"`{row['fallback_calibration_gate_pass']}` |"
        )
    lines.extend(
        [
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


def write_outputs(output_dir: Path, summary: dict[str, Any], rows: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> None:
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "combiner_rows.jsonl", rows)
    write_jsonl(output_dir / "predictions.jsonl", predictions)
    write_csv(
        output_dir / "metrics.csv",
        [
            {
                "kind": row["kind"],
                "target_mode": row["target_mode"],
                "split_eval": row["split_eval"],
                "name": row["name"],
                **row["metrics"],
            }
            for row in summary["metric_rows"]
        ],
    )
    write_csv(
        output_dir / "comparisons.csv",
        [
            {
                "split_eval": row["split_eval"],
                "left": row["left"],
                "right": row["right"],
                **{f"delta_{key}": value for key, value in row["delta"].items()},
            }
            for row in summary["comparisons"]
        ],
    )
    family_rows = []
    for item in summary["family_slices"]:
        family_rows.append(
            {
                "predicate_family": item["predicate_family"],
                "view": item["view"],
                "split_eval": item["split_eval"],
                "single_class": item["single_class"],
                **item["metrics"],
            }
        )
    write_csv(output_dir / "family_slices.csv", family_rows)
    write_csv(output_dir / "family_deltas.csv", summary["family_deltas"])
    write_csv(output_dir / "transfer_vs_linear.csv", summary["transfer_vs_linear"])
    write_csv(output_dir / "transfer_vs_legacy.csv", summary["transfer_vs_legacy"])
    gate_rows = []
    for row in summary["gate_evaluation"]["candidate_results"]:
        gate_rows.append(
            {
                "candidate": row["candidate"],
                **{f"delta_vs_linear_{key}": value for key, value in row["delta_vs_linear"].items()},
                "new_errors_minus_fixes_vs_linear": row["transfer_vs_linear"]["new_errors_minus_fixes"],
                "support_delta_auprc_vs_legacy": row["support_vs_legacy"].get("delta_auprc"),
                "support_delta_brier_vs_legacy": row["support_vs_legacy"].get("delta_brier"),
                "vertical_delta_auprc_vs_legacy": row["vertical_vs_legacy"].get("delta_auprc"),
                "vertical_delta_brier_vs_legacy": row["vertical_vs_legacy"].get("delta_brier"),
                "primary_gate_pass": row["primary_gate_pass"],
                "fallback_calibration_gate_pass": row["fallback_calibration_gate_pass"],
            }
        )
    write_csv(output_dir / "gate_evaluation.csv", gate_rows)
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_rows = smoke.read_jsonl(args.input_rows)
    rows = extend_rows(raw_rows)
    feature_join_summary = read_json(args.feature_join_summary)
    plan_summary = read_json(args.plan_summary)
    validation_errors = validate_inputs(raw_rows, feature_join_summary, plan_summary)

    metric_rows: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    feature_summaries: dict[str, Any] = {}
    grouped_scores: dict[str, list[float]] = {}
    all_views = MAIN_VIEWS + CONTROL_VIEWS

    for kind, views in [("main", MAIN_VIEWS), ("control", CONTROL_VIEWS)]:
        for view in views:
            in_probs, in_summary = smoke.train_predict_in_sample(
                rows,
                view,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            cross_probs, cross_summary = smoke.train_predict_crossfit(
                rows,
                view,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            grouped_probs, grouped_summary = base.train_predict_grouped(
                rows,
                view,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            feature_summaries[view] = {
                "in_sample": in_summary,
                "crossfit": cross_summary,
                "grouped": grouped_summary,
            }
            for split_eval, probs in [
                ("in_sample", in_probs),
                ("train_internal_3fold", cross_probs),
                ("train_internal_grouped_by_scan", grouped_probs),
            ]:
                metric_rows.append(metric_record(kind, split_eval, view, rows, probs))
            grouped_scores[view] = grouped_probs
            for row, prob in zip(rows, grouped_probs):
                predictions.append(
                    {
                        "prediction_id": row["identity"]["prediction_id"],
                        "view": view,
                        "split_eval": "train_internal_grouped_by_scan",
                        "target_y": smoke.target_y(row),
                        "probability": prob,
                    }
                )

    comparison_pairs = []
    for view in all_views:
        if view != PRIMARY_REFERENCE:
            comparison_pairs.append((view, PRIMARY_REFERENCE))
        if view != LEGACY_REFERENCE:
            comparison_pairs.append((view, LEGACY_REFERENCE))
    for control in CONTROL_VIEWS:
        comparison_pairs.append((PRIMARY_REFERENCE, control))
    seen_pairs = set()
    comparisons = []
    for split_eval in ["train_internal_3fold", "train_internal_grouped_by_scan"]:
        for left, right in comparison_pairs:
            if (split_eval, left, right) in seen_pairs:
                continue
            seen_pairs.add((split_eval, left, right))
            comparisons.append(comparison(metric_rows, split_eval, left, right))

    family_slices = base.family_slices(grouped_scores, rows)
    family_deltas = []
    for view in MAIN_VIEWS:
        if view != LEGACY_REFERENCE:
            family_deltas.extend(family_delta_rows(family_slices, view, LEGACY_REFERENCE))
        if view != PRIMARY_REFERENCE:
            family_deltas.extend(family_delta_rows(family_slices, view, PRIMARY_REFERENCE))

    transfer_vs_linear = transfer_summary(rows, {view: grouped_scores[view] for view in MAIN_VIEWS}, PRIMARY_REFERENCE)
    transfer_vs_legacy = transfer_summary(rows, {view: grouped_scores[view] for view in MAIN_VIEWS}, LEGACY_REFERENCE)
    gate_eval = evaluate_gates(comparisons, transfer_vs_linear, family_deltas)
    status, decision, next_todo = classify_status(validation_errors, gate_eval)

    summary = {
        "schema_version": "h002_raw_witness_v2_combiner_smoke_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "input_rows": rel_path(args.input_rows),
            "feature_join_summary": rel_path(args.feature_join_summary),
            "plan_summary": rel_path(args.plan_summary),
        },
        "output_dir": rel_path(output_dir),
        "hyperparameters": {
            "folds": args.folds,
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "l2": args.l2,
            "tuned_on_validation": False,
            "uses_validation_rows": False,
        },
        "boundary": {
            "split": "train_only",
            "target_mode": TARGET_MODE,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "review_fields_as_model_input": False,
            "hidden_metadata_as_model_input": False,
            "target_labels_as_model_input": False,
            "packet_paths_as_model_input": False,
            "multi_view_as_model_input": False,
            "geometry_status_as_model_input": False,
            "raw_witness_as_model_input": True,
            "validation_usage": False,
            "test_usage": False,
        },
        "target_summary": target_summary(rows),
        "main_views": MAIN_VIEWS,
        "control_views": CONTROL_VIEWS,
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "family_slices": family_slices,
        "family_deltas": family_deltas,
        "transfer_vs_linear": transfer_vs_linear,
        "transfer_vs_legacy": transfer_vs_legacy,
        "feature_summaries": feature_summaries,
        "gate_evaluation": gate_eval,
        "validation_errors": validation_errors,
        "decision": decision,
        "claim_boundary": {
            "allowed": "Train-only combiner diagnostic only.",
            "blocked": "No paper-level posterior method claim; no held-out generalization claim.",
        },
        "next_todo": next_todo,
    }
    write_outputs(output_dir, summary, rows, predictions)
    return summary


def main() -> int:
    summary = run(parse_args())
    gate = summary["gate_evaluation"]
    best = gate["best_by_grouped_auprc_delta_vs_linear"]
    best_delta = next(row["delta_vs_linear"] for row in gate["candidate_results"] if row["candidate"] == best)
    print(
        "status={status} rows={rows} pos={pos} neg={neg} validation_used={validation_used} "
        "best_candidate={best} best_d_auprc_vs_linear={d_auprc:.4f} "
        "primary_passes={primary_passes} fallback_passes={fallback_passes} next={next_todo}".format(
            status=summary["status"],
            rows=summary["target_summary"]["rows"],
            pos=summary["target_summary"]["positive"],
            neg=summary["target_summary"]["negative"],
            validation_used=summary["boundary"]["validation_usage"],
            best=best,
            d_auprc=best_delta["auprc"],
            primary_passes=len(gate["primary_gate_passes"]),
            fallback_passes=len(gate["fallback_calibration_gate_passes"]),
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
