#!/usr/bin/env python3
"""Error analysis for H002 raw-witness v2 posterior smoke."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_SMOKE_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_all_label_ready"

REFERENCE_VIEW = "semantic_plus_geometry"
PRIMARY_VIEW = "factorized_reliability_posterior_v2_family_shrinkage"
LINEAR_VIEW = "factorized_reliability_posterior_v2_linear"
SEMANTIC_RAW_VIEW = "semantic_plus_raw_witness_v2"
RAW_ONLY_VIEW = "raw_witness_only_v2"
LEGACY_GEOM_VIEW = "legacy_geometry_only"

ANALYSIS_VIEWS = [
    "semantic_only",
    LEGACY_GEOM_VIEW,
    REFERENCE_VIEW,
    RAW_ONLY_VIEW,
    SEMANTIC_RAW_VIEW,
    LINEAR_VIEW,
    PRIMARY_VIEW,
    "no_family_local_normalization",
    "endpoint_type_ablation",
]

CONTROL_VIEWS = [
    "raw_witness_shuffle_global",
    "raw_witness_shuffle_within_family",
    "wrong_pair_raw_witness",
    "family_only_offset",
    "legacy_p_geom_only",
]

SLICE_KEYS = [
    "predicate_family",
    "predicate_label",
    "semantic_score_bin",
    "rank_bin",
    "p_geom_valid_bin",
    "strong_raw_witness_bin",
    "raw_vs_pgeom_gap_bin",
    "support_gate_bin",
    "support_iou_bin",
    "support_gap_bin",
    "vertical_gate_bin",
    "vertical_sign_bin",
    "vertical_margin_bin",
    "target_reason",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
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


def safe_float(value: Any, default: float = 0.0) -> float:
    return smoke.safe_float(value, default)


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def brier(y: int, prob: float) -> float:
    return (prob - y) ** 2


def correct(y: int, prob: float) -> bool:
    return int(prob >= 0.5) == int(y)


def numeric_bin(value: float, cuts: list[float], labels: list[str]) -> str:
    for cut, label in zip(cuts, labels):
        if value < cut:
            return label
    return labels[-1]


def signed_bin(value: float, negative_cut: float, positive_cut: float, prefix: str) -> str:
    if value <= negative_cut:
        return f"{prefix}_negative"
    if value >= positive_cut:
        return f"{prefix}_positive"
    return f"{prefix}_near_zero"


def load_predictions(smoke_dir: Path) -> dict[str, dict[str, float]]:
    predictions: dict[str, dict[str, float]] = defaultdict(dict)
    for row in smoke.read_jsonl(smoke_dir / "predictions.jsonl"):
        if row.get("split_eval") != "train_internal_grouped_by_scan":
            continue
        predictions[str(row["prediction_id"])][str(row["view"])] = safe_float(row.get("probability"), 0.5)
    return dict(predictions)


def metric_lookup(smoke_summary: dict[str, Any], split_eval: str, view: str) -> dict[str, Any]:
    for row in smoke_summary["metric_rows"]:
        if row["split_eval"] == split_eval and row["name"] == view:
            return row["metrics"]
    return {}


def comparison_lookup(smoke_summary: dict[str, Any], split_eval: str, left: str, right: str) -> dict[str, Any]:
    for row in smoke_summary["comparisons"]:
        if row["split_eval"] == split_eval and row["left"] == left and row["right"] == right:
            return row["delta"]
    left_metrics = metric_lookup(smoke_summary, split_eval, left)
    right_metrics = metric_lookup(smoke_summary, split_eval, right)
    return metric_delta(left_metrics, right_metrics)


def metric_delta(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    output = {}
    for key in ["auroc", "auprc", "brier", "ece_5bin", "accuracy_at_0_5"]:
        if left.get(key) is None or right.get(key) is None:
            output[key] = None
        else:
            output[key] = left[key] - right[key]
    return output


def metrics_or_none(labels: list[int], scores: list[float]) -> dict[str, Any] | None:
    if len(set(labels)) != 2:
        return None
    return smoke.metrics(labels, scores)


def rank_positions(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]], view: str) -> dict[str, int]:
    ordered = sorted(
        rows,
        key=lambda row: (
            -predictions[str(row["identity"]["prediction_id"])].get(view, 0.5),
            str(row["identity"]["prediction_id"]),
        ),
    )
    return {str(row["identity"]["prediction_id"]): rank for rank, row in enumerate(ordered, start=1)}


def feature_bundle(row: dict[str, Any]) -> dict[str, Any]:
    identity = row["identity"]
    primary = row["baseline_inputs"][PRIMARY_VIEW]
    raw = row["baseline_inputs"][RAW_ONLY_VIEW]
    semantic = row["baseline_inputs"]["semantic_only"]
    legacy = row["baseline_inputs"][LEGACY_GEOM_VIEW]
    strong = safe_float(raw.get("strong_raw_witness_score"), 0.5)
    weak = safe_float(raw.get("weak_raw_witness_score"), 0.5)
    p_geom = safe_float(legacy.get("p_geom_valid"), 0.5)
    semantic_norm = safe_float(semantic.get("semantic_score_norm"), 0.0)
    semantic_rank = safe_float(semantic.get("semantic_rank"), 9999.0)
    support_iou = safe_float(raw.get("support_iou_xy"), 0.0)
    support_gap = safe_float(raw.get("support_gap_abs"), 9999.0)
    support_gap_local = safe_float(raw.get("support_gap_abs_local_z"), 0.0)
    vertical_sign = safe_float(raw.get("vertical_sign_agreement"), 0.0)
    vertical_margin = safe_float(raw.get("vertical_signed_margin"), 0.0)
    vertical_margin_local = safe_float(raw.get("vertical_signed_margin_local_z"), 0.0)

    return {
        "prediction_id": str(identity["prediction_id"]),
        "scan_id": identity.get("scan_id"),
        "subgraph_id": identity.get("subgraph_id"),
        "subject_id": identity.get("subject_id"),
        "subject_label": identity.get("subject_label"),
        "predicate_label": identity.get("predicate_label"),
        "predicate_family": identity.get("predicate_family"),
        "object_id": identity.get("object_id"),
        "object_label": identity.get("object_label"),
        "target": smoke.target_y(row),
        "target_reason": row.get("target", {}).get("target_reason"),
        "semantic_score_norm": semantic_norm,
        "semantic_rank": semantic_rank,
        "p_geom_valid": p_geom,
        "consistency_score": safe_float(legacy.get("consistency_score"), 0.5),
        "strong_raw_witness_score": strong,
        "weak_raw_witness_score": weak,
        "raw_minus_pgeom": strong - p_geom,
        "semantic_minus_raw": semantic_norm - strong,
        "semantic_minus_pgeom": semantic_norm - p_geom,
        "normalized_vertical_signed_margin": safe_float(raw.get("normalized_vertical_signed_margin"), 0.0),
        "semantic_geometry_gap_abs_local_z": safe_float(raw.get("semantic_geometry_gap_abs_local_z"), 0.0),
        "support_contact_gate": safe_float(raw.get("support_contact_gate"), 0.0),
        "support_distance_closeness": safe_float(raw.get("support_distance_closeness"), 0.0),
        "support_gap_closeness": safe_float(raw.get("support_gap_closeness"), 0.0),
        "support_iou_xy": support_iou,
        "support_gap_abs": support_gap,
        "support_gap_abs_local_z": support_gap_local,
        "support_distance_xy": safe_float(raw.get("support_distance_xy"), 0.0),
        "relative_vertical_gate": safe_float(raw.get("relative_vertical_gate"), 0.0),
        "vertical_sign_agreement": vertical_sign,
        "vertical_signed_margin": vertical_margin,
        "vertical_signed_margin_local_z": vertical_margin_local,
        "vertical_margin_abs": safe_float(raw.get("vertical_margin_abs"), 0.0),
        "vertical_interval_overlap": safe_float(raw.get("vertical_interval_overlap"), 0.0),
        "overconfidence_score": safe_float(primary.get("overconfidence_score"), 0.0),
        "underconfidence_score": safe_float(primary.get("underconfidence_score"), 0.0),
        "raw_witness_missing_flag": safe_float(raw.get("raw_witness_missing_flag"), 0.0),
    }


def bin_bundle(features: dict[str, Any]) -> dict[str, str]:
    return {
        "semantic_score_bin": numeric_bin(
            safe_float(features["semantic_score_norm"]),
            [0.50, 0.75, 0.90],
            ["semantic_lt_0_50", "semantic_0_50_0_75", "semantic_0_75_0_90", "semantic_ge_0_90"],
        ),
        "rank_bin": numeric_bin(
            safe_float(features["semantic_rank"], 9999.0),
            [50, 100, 200],
            ["rank_lt_50", "rank_50_99", "rank_100_199", "rank_ge_200"],
        ),
        "p_geom_valid_bin": numeric_bin(
            safe_float(features["p_geom_valid"], 0.5),
            [0.25, 0.50, 0.75],
            ["p_geom_lt_0_25", "p_geom_0_25_0_50", "p_geom_0_50_0_75", "p_geom_ge_0_75"],
        ),
        "strong_raw_witness_bin": numeric_bin(
            safe_float(features["strong_raw_witness_score"], 0.5),
            [0.25, 0.50, 0.75],
            ["raw_lt_0_25", "raw_0_25_0_50", "raw_0_50_0_75", "raw_ge_0_75"],
        ),
        "raw_vs_pgeom_gap_bin": signed_bin(safe_float(features["raw_minus_pgeom"]), -0.20, 0.20, "raw_minus_pgeom"),
        "support_gate_bin": "support_gate_on" if safe_float(features["support_contact_gate"]) >= 0.5 else "support_gate_off",
        "support_iou_bin": numeric_bin(
            safe_float(features["support_iou_xy"], 0.0),
            [0.01, 0.05, 0.15],
            ["support_iou_lt_0_01", "support_iou_0_01_0_05", "support_iou_0_05_0_15", "support_iou_ge_0_15"],
        ),
        "support_gap_bin": numeric_bin(
            safe_float(features["support_gap_abs"], 9999.0),
            [0.10, 0.50, 1.00],
            ["support_gap_lt_0_10", "support_gap_0_10_0_50", "support_gap_0_50_1_00", "support_gap_ge_1_00"],
        ),
        "vertical_gate_bin": "vertical_gate_on" if safe_float(features["relative_vertical_gate"]) >= 0.5 else "vertical_gate_off",
        "vertical_sign_bin": "vertical_sign_agree" if safe_float(features["vertical_sign_agreement"]) >= 0.5 else "vertical_sign_not_agree",
        "vertical_margin_bin": signed_bin(
            safe_float(features["vertical_signed_margin"]),
            -0.10,
            0.10,
            "vertical_signed_margin",
        ),
    }


def row_error_table(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    all_views = ANALYSIS_VIEWS + CONTROL_VIEWS
    rank_by_view = {view: rank_positions(rows, predictions, view) for view in all_views}
    outputs = []
    for row in rows:
        features = feature_bundle(row)
        row_id = features["prediction_id"]
        y = int(features["target"])
        reference_prob = predictions[row_id][REFERENCE_VIEW]
        primary_prob = predictions[row_id][PRIMARY_VIEW]
        linear_prob = predictions[row_id][LINEAR_VIEW]

        view_fields: dict[str, Any] = {}
        for view in all_views:
            prob = predictions[row_id][view]
            view_fields[f"prob_{view}"] = prob
            view_fields[f"brier_{view}"] = brier(y, prob)
            view_fields[f"correct_{view}"] = correct(y, prob)
            view_fields[f"rank_{view}"] = rank_by_view[view][row_id]

        primary_correct = correct(y, primary_prob)
        reference_correct = correct(y, reference_prob)
        linear_correct = correct(y, linear_prob)
        if primary_correct and not reference_correct:
            primary_transfer = "primary_fixes_reference_error"
        elif reference_correct and not primary_correct:
            primary_transfer = "primary_adds_error"
        elif primary_correct and reference_correct:
            primary_transfer = "both_correct"
        else:
            primary_transfer = "both_wrong"

        if linear_correct and not primary_correct:
            linear_transfer = "linear_fixes_primary_error"
        elif primary_correct and not linear_correct:
            linear_transfer = "linear_adds_error"
        elif linear_correct and primary_correct:
            linear_transfer = "both_correct"
        else:
            linear_transfer = "both_wrong"

        outputs.append(
            {
                **features,
                **bin_bundle(features),
                **view_fields,
                "prob_delta_primary_minus_sg": primary_prob - reference_prob,
                "prob_delta_linear_minus_primary": linear_prob - primary_prob,
                "brier_delta_primary_minus_sg": brier(y, primary_prob) - brier(y, reference_prob),
                "brier_delta_linear_minus_primary": brier(y, linear_prob) - brier(y, primary_prob),
                "rank_delta_primary_minus_sg": rank_by_view[PRIMARY_VIEW][row_id] - rank_by_view[REFERENCE_VIEW][row_id],
                "rank_delta_linear_minus_primary": rank_by_view[LINEAR_VIEW][row_id] - rank_by_view[PRIMARY_VIEW][row_id],
                "transfer_primary_vs_sg": primary_transfer,
                "transfer_linear_vs_primary": linear_transfer,
                "primary_error_direction": (
                    "false_positive"
                    if y == 0 and primary_prob >= 0.5
                    else "false_negative"
                    if y == 1 and primary_prob < 0.5
                    else "correct"
                ),
            }
        )
    return outputs


def summarize_transfer(row_errors: list[dict[str, Any]], view: str, reference: str) -> dict[str, Any]:
    counts = Counter()
    for row in row_errors:
        y = int(row["target"])
        prob = safe_float(row[f"prob_{view}"], 0.5)
        ref = safe_float(row[f"prob_{reference}"], 0.5)
        view_correct = correct(y, prob)
        ref_correct = correct(y, ref)
        if view_correct and not ref_correct:
            counts["view_fixes_reference_error"] += 1
        elif ref_correct and not view_correct:
            counts["view_adds_error"] += 1
        elif view_correct and ref_correct:
            counts["both_correct"] += 1
        else:
            counts["both_wrong"] += 1
    return {
        "view": view,
        "reference_view": reference,
        "rows": len(row_errors),
        "view_fixes_reference_error": counts["view_fixes_reference_error"],
        "view_adds_error": counts["view_adds_error"],
        "both_correct": counts["both_correct"],
        "both_wrong": counts["both_wrong"],
        "new_errors_minus_fixes": counts["view_adds_error"] - counts["view_fixes_reference_error"],
    }


def aggregate_slice(row_errors: list[dict[str, Any]], slice_name: str, slice_value: str, view: str, reference: str) -> dict[str, Any]:
    labels = [int(row["target"]) for row in row_errors]
    scores = [safe_float(row[f"prob_{view}"], 0.5) for row in row_errors]
    ref_scores = [safe_float(row[f"prob_{reference}"], 0.5) for row in row_errors]
    metrics = metrics_or_none(labels, scores)
    ref_metrics = metrics_or_none(labels, ref_scores)
    transfers = Counter()
    for row, score, ref in zip(row_errors, scores, ref_scores):
        view_correct = correct(int(row["target"]), score)
        ref_correct = correct(int(row["target"]), ref)
        if view_correct and not ref_correct:
            transfers["view_fixes_reference_error"] += 1
        elif ref_correct and not view_correct:
            transfers["view_adds_error"] += 1
        elif view_correct and ref_correct:
            transfers["both_correct"] += 1
        else:
            transfers["both_wrong"] += 1
    delta = metric_delta(metrics or {}, ref_metrics or {})
    return {
        "view": view,
        "reference_view": reference,
        "slice_name": slice_name,
        "slice_value": slice_value,
        "rows": len(row_errors),
        "positive": sum(labels),
        "negative": len(labels) - sum(labels),
        "view_fixes_reference_error": transfers["view_fixes_reference_error"],
        "view_adds_error": transfers["view_adds_error"],
        "new_errors_minus_fixes": transfers["view_adds_error"] - transfers["view_fixes_reference_error"],
        "mean_prob_delta_view_minus_ref": sum(score - ref for score, ref in zip(scores, ref_scores)) / len(scores),
        "mean_brier_delta_view_minus_ref": sum(
            brier(y, score) - brier(y, ref) for y, score, ref in zip(labels, scores, ref_scores)
        )
        / len(scores),
        "view_auroc": metrics.get("auroc") if metrics else None,
        "view_auprc": metrics.get("auprc") if metrics else None,
        "view_brier": metrics.get("brier") if metrics else None,
        "ref_auroc": ref_metrics.get("auroc") if ref_metrics else None,
        "ref_auprc": ref_metrics.get("auprc") if ref_metrics else None,
        "ref_brier": ref_metrics.get("brier") if ref_metrics else None,
        "delta_auroc_view_minus_ref": delta.get("auroc"),
        "delta_auprc_view_minus_ref": delta.get("auprc"),
        "delta_brier_view_minus_ref": delta.get("brier"),
        "delta_ece_view_minus_ref": delta.get("ece_5bin"),
        "delta_accuracy_view_minus_ref": delta.get("accuracy_at_0_5"),
    }


def build_slice_deltas(row_errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    for reference in [REFERENCE_VIEW, PRIMARY_VIEW]:
        views = [view for view in ANALYSIS_VIEWS + CONTROL_VIEWS if view != reference]
        for view in views:
            for key in SLICE_KEYS:
                groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
                for row in row_errors:
                    groups[str(row.get(key, "missing"))].append(row)
                for value, group_rows in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
                    outputs.append(aggregate_slice(group_rows, key, value, view, reference))
    return outputs


def feature_label_summary(row_errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    slice_specs = [("all", "all")]
    slice_specs.extend(("predicate_family", family) for family in sorted({str(row["predicate_family"]) for row in row_errors}))
    for slice_name, slice_value in slice_specs:
        selected = row_errors if slice_name == "all" else [row for row in row_errors if str(row[slice_name]) == slice_value]
        for target in [0, 1]:
            rows = [row for row in selected if int(row["target"]) == target]
            if not rows:
                continue
            outputs.append(
                {
                    "slice_name": slice_name,
                    "slice_value": slice_value,
                    "target": target,
                    "rows": len(rows),
                    "mean_semantic_score_norm": sum(safe_float(row["semantic_score_norm"]) for row in rows) / len(rows),
                    "mean_p_geom_valid": sum(safe_float(row["p_geom_valid"]) for row in rows) / len(rows),
                    "mean_strong_raw_witness_score": sum(safe_float(row["strong_raw_witness_score"]) for row in rows)
                    / len(rows),
                    "mean_raw_minus_pgeom": sum(safe_float(row["raw_minus_pgeom"]) for row in rows) / len(rows),
                    "mean_support_iou_xy": sum(safe_float(row["support_iou_xy"]) for row in rows) / len(rows),
                    "mean_support_gap_abs": sum(safe_float(row["support_gap_abs"]) for row in rows) / len(rows),
                    "mean_vertical_sign_agreement": sum(safe_float(row["vertical_sign_agreement"]) for row in rows)
                    / len(rows),
                    "mean_vertical_signed_margin": sum(safe_float(row["vertical_signed_margin"]) for row in rows)
                    / len(rows),
                    "mean_prob_semantic_plus_geometry": sum(safe_float(row[f"prob_{REFERENCE_VIEW}"]) for row in rows)
                    / len(rows),
                    "mean_prob_primary": sum(safe_float(row[f"prob_{PRIMARY_VIEW}"]) for row in rows) / len(rows),
                    "mean_prob_linear": sum(safe_float(row[f"prob_{LINEAR_VIEW}"]) for row in rows) / len(rows),
                    "primary_accuracy": sum(1 for row in rows if bool(row[f"correct_{PRIMARY_VIEW}"])) / len(rows),
                    "linear_accuracy": sum(1 for row in rows if bool(row[f"correct_{LINEAR_VIEW}"])) / len(rows),
                }
            )
    return outputs


def pick_slice(slice_deltas: list[dict[str, Any]], view: str, reference: str, slice_name: str, slice_value: str) -> dict[str, Any] | None:
    for row in slice_deltas:
        if (
            row["view"] == view
            and row["reference_view"] == reference
            and row["slice_name"] == slice_name
            and row["slice_value"] == slice_value
        ):
            return row
    return None


def build_diagnosis(smoke_summary: dict[str, Any], slice_deltas: list[dict[str, Any]]) -> list[str]:
    diagnosis = []
    primary_vs_sg = comparison_lookup(smoke_summary, "train_internal_grouped_by_scan", PRIMARY_VIEW, REFERENCE_VIEW)
    linear_vs_sg = comparison_lookup(smoke_summary, "train_internal_grouped_by_scan", LINEAR_VIEW, REFERENCE_VIEW)
    shrinkage_vs_linear = comparison_lookup(smoke_summary, "train_internal_grouped_by_scan", PRIMARY_VIEW, LINEAR_VIEW)
    primary_vs_shuffle = comparison_lookup(
        smoke_summary,
        "train_internal_grouped_by_scan",
        PRIMARY_VIEW,
        "raw_witness_shuffle_global",
    )
    primary_vs_wrong = comparison_lookup(
        smoke_summary,
        "train_internal_grouped_by_scan",
        PRIMARY_VIEW,
        "wrong_pair_raw_witness",
    )
    primary_vs_no_local = comparison_lookup(
        smoke_summary,
        "train_internal_grouped_by_scan",
        PRIMARY_VIEW,
        "no_family_local_normalization",
    )

    if safe_float(primary_vs_sg.get("auprc")) > 0.10 and safe_float(primary_vs_sg.get("brier")) < 0.0:
        diagnosis.append("typed_raw_witness_v2_adds_stable_signal_over_semantic_plus_geometry")
    if safe_float(primary_vs_shuffle.get("auprc")) > 0.05 and safe_float(primary_vs_wrong.get("auprc")) > 0.05:
        diagnosis.append("raw_witness_controls_reduce_gain")
    if safe_float(shrinkage_vs_linear.get("auprc")) < 0.0 or safe_float(shrinkage_vs_linear.get("brier")) > 0.0:
        diagnosis.append("family_shrinkage_not_best_combiner_for_ranking_or_brier")
    if safe_float(linear_vs_sg.get("auprc")) >= safe_float(primary_vs_sg.get("auprc")):
        diagnosis.append("linear_v2_is_current_strongest_simple_posterior")
    if abs(safe_float(primary_vs_no_local.get("auprc"))) < 0.02 and safe_float(primary_vs_no_local.get("brier")) < 0.0:
        diagnosis.append("family_local_normalization_mainly_improves_calibration_not_ranking")

    support = pick_slice(slice_deltas, PRIMARY_VIEW, REFERENCE_VIEW, "predicate_family", "support_contact")
    vertical = pick_slice(slice_deltas, PRIMARY_VIEW, REFERENCE_VIEW, "predicate_family", "relative_vertical")
    if support and safe_float(support.get("delta_auprc_view_minus_ref")) > 0.10:
        diagnosis.append("support_contact_drives_positive_signal")
    if vertical and safe_float(vertical.get("delta_brier_view_minus_ref")) > 0.0:
        diagnosis.append("relative_vertical_has_calibration_regression")
    if support and vertical and safe_float(support.get("delta_auprc_view_minus_ref")) > safe_float(
        vertical.get("delta_auprc_view_minus_ref")
    ) + 0.10:
        diagnosis.append("family_effect_is_heterogeneous")

    endpoint = comparison_lookup(smoke_summary, "train_internal_grouped_by_scan", "endpoint_type_ablation", REFERENCE_VIEW)
    if safe_float(endpoint.get("auprc")) > 0.10:
        diagnosis.append("endpoint_type_ablation_has_nontrivial_signal_and_needs_shortcut_control")
    return diagnosis or ["no_dominant_error_pattern_detected"]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Raw-Witness V2 Error Analysis",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only post-hoc analysis of grouped-by-scan smoke predictions.",
        "- No validation/test rows are used.",
        "- No new model is trained in this analysis.",
        "- Review fields, target labels, hidden audit metadata, packet paths, and multi-view evidence are not model inputs.",
        "- Results are hypothesis-stage diagnostics, not paper-level metrics.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Diagnosis",
        "",
    ]
    lines.extend(f"- `{item}`" for item in summary["diagnosis"])
    lines.extend(
        [
            "",
            "## Global Transfer Against Semantic+Geometry",
            "",
            "| View | Fixes SG Errors | Adds Errors | Both Correct | Both Wrong | New-Fix |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["transfer_vs_semantic_plus_geometry"]:
        lines.append(
            f"| `{row['view']}` | {row['view_fixes_reference_error']} | {row['view_adds_error']} | "
            f"{row['both_correct']} | {row['both_wrong']} | {row['new_errors_minus_fixes']} |"
        )
    lines.extend(
        [
            "",
            "## Linear Vs Family Shrinkage",
            "",
            "| View | Fixes Primary Errors | Adds Errors | Both Correct | Both Wrong | New-Fix |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["transfer_vs_primary"]:
        lines.append(
            f"| `{row['view']}` | {row['view_fixes_reference_error']} | {row['view_adds_error']} | "
            f"{row['both_correct']} | {row['both_wrong']} | {row['new_errors_minus_fixes']} |"
        )
    lines.extend(
        [
            "",
            "## Key Family Slices",
            "",
            "| Family | View | Ref | Rows | Pos | Neg | dAUPRC | dBrier | New-Fix |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["key_family_slices"]:
        lines.append(
            f"| `{row['slice_value']}` | `{row['view']}` | `{row['reference_view']}` | {row['rows']} | "
            f"{row['positive']} | {row['negative']} | {fmt(row['delta_auprc_view_minus_ref'])} | "
            f"{fmt(row['delta_brier_view_minus_ref'])} | {row['new_errors_minus_fixes']} |"
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


def write_outputs(output_dir: Path, summary: dict[str, Any], row_errors: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "row_errors.jsonl", row_errors)
    write_jsonl(
        output_dir / "top_primary_losses_vs_sg.jsonl",
        sorted(row_errors, key=lambda row: safe_float(row["brier_delta_primary_minus_sg"]), reverse=True)[:25],
    )
    write_jsonl(
        output_dir / "top_primary_wins_vs_sg.jsonl",
        sorted(row_errors, key=lambda row: safe_float(row["brier_delta_primary_minus_sg"]))[:25],
    )
    write_jsonl(
        output_dir / "top_linear_wins_vs_primary.jsonl",
        sorted(row_errors, key=lambda row: safe_float(row["brier_delta_linear_minus_primary"]))[:25],
    )
    write_jsonl(
        output_dir / "top_linear_losses_vs_primary.jsonl",
        sorted(row_errors, key=lambda row: safe_float(row["brier_delta_linear_minus_primary"]), reverse=True)[:25],
    )
    write_csv(output_dir / "slice_deltas.csv", summary["slice_deltas"])
    write_csv(output_dir / "transfer_vs_semantic_plus_geometry.csv", summary["transfer_vs_semantic_plus_geometry"])
    write_csv(output_dir / "transfer_vs_primary.csv", summary["transfer_vs_primary"])
    write_csv(output_dir / "feature_label_summary.csv", summary["feature_label_summary"])
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    smoke_dir = as_abs(args.smoke_dir)
    output_dir = as_abs(args.output_dir)
    smoke_summary = read_json(smoke_dir / "summary.json")
    rows = smoke.read_jsonl(smoke_dir / "posterior_rows.jsonl")
    predictions = load_predictions(smoke_dir)
    required_views = set(ANALYSIS_VIEWS + CONTROL_VIEWS)
    missing = [
        str(row["identity"]["prediction_id"])
        for row in rows
        if required_views - set(predictions.get(str(row["identity"]["prediction_id"]), {}))
    ]
    if missing:
        raise ValueError(f"missing grouped predictions for {len(missing)} rows; first={missing[0]}")

    row_errors = row_error_table(rows, predictions)
    slice_deltas = build_slice_deltas(row_errors)
    transfer_vs_sg = [summarize_transfer(row_errors, view, REFERENCE_VIEW) for view in ANALYSIS_VIEWS if view != REFERENCE_VIEW]
    transfer_vs_primary = [summarize_transfer(row_errors, view, PRIMARY_VIEW) for view in [LINEAR_VIEW, SEMANTIC_RAW_VIEW, RAW_ONLY_VIEW]]
    feature_summary = feature_label_summary(row_errors)
    diagnosis = build_diagnosis(smoke_summary, slice_deltas)

    key_family_slices = [
        row
        for row in slice_deltas
        if row["slice_name"] == "predicate_family"
        and row["slice_value"] in {"support_contact", "relative_vertical"}
        and (
            (row["reference_view"] == REFERENCE_VIEW and row["view"] in {PRIMARY_VIEW, LINEAR_VIEW, SEMANTIC_RAW_VIEW, RAW_ONLY_VIEW})
            or (row["reference_view"] == PRIMARY_VIEW and row["view"] == LINEAR_VIEW)
        )
    ]
    primary_vs_sg = comparison_lookup(smoke_summary, "train_internal_grouped_by_scan", PRIMARY_VIEW, REFERENCE_VIEW)
    linear_vs_sg = comparison_lookup(smoke_summary, "train_internal_grouped_by_scan", LINEAR_VIEW, REFERENCE_VIEW)
    shrinkage_vs_linear = comparison_lookup(smoke_summary, "train_internal_grouped_by_scan", PRIMARY_VIEW, LINEAR_VIEW)

    status = "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_ready_support_driven_linear_gap"
    decision = (
        "Raw-witness v2 provides a real train-only signal over semantic+geometry, but the evidence is support_contact-driven "
        "and the current family-shrinkage combiner is not the best ranking/Brier choice. The next step should freeze a "
        "combiner repair plan: keep typed raw witness as the main geometry evidence, compare linear against constrained "
        "monotonic/family-gated variants, and repair relative_vertical calibration before any higher-capacity model."
    )
    next_todo = "revised_sampling_all_label_ready_raw_witness_v2_combiner_repair_plan"

    summary = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_raw_witness_v2_error_analysis_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "smoke_dir": rel_path(smoke_dir),
            "smoke_status": smoke_summary.get("status"),
            "rows": len(rows),
            "positive": sum(smoke.target_y(row) for row in rows),
            "negative": len(rows) - sum(smoke.target_y(row) for row in rows),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "post_hoc_only": True,
            "trains_new_model": False,
            "review_fields_as_model_input": False,
            "hidden_metadata_as_model_input": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
            "posterior_performance_claim_allowed": False,
        },
        "reference_view": REFERENCE_VIEW,
        "primary_view": PRIMARY_VIEW,
        "linear_view": LINEAR_VIEW,
        "quick_deltas": {
            "primary_vs_semantic_plus_geometry": primary_vs_sg,
            "linear_vs_semantic_plus_geometry": linear_vs_sg,
            "primary_vs_linear": shrinkage_vs_linear,
        },
        "diagnosis": diagnosis,
        "transfer_vs_semantic_plus_geometry": transfer_vs_sg,
        "transfer_vs_primary": transfer_vs_primary,
        "slice_deltas": slice_deltas,
        "key_family_slices": key_family_slices,
        "feature_label_summary": feature_summary,
        "decision": decision,
        "claim_boundary": {
            "allowed": (
                "Train-only diagnostics support typed raw witness as a stronger geometry evidence axis than legacy p_geom_valid."
            ),
            "blocked": (
                "Do not claim the family-shrinkage posterior is final or paper-level superior; linear currently wins AUPRC/Brier."
            ),
        },
        "next_todo": next_todo,
    }
    write_outputs(output_dir, summary, row_errors)
    return summary


def main() -> int:
    summary = run(parse_args())
    deltas = summary["quick_deltas"]
    print(
        "status={status} rows={rows} validation_used={validation_used} "
        "d_auprc_primary_vs_sg={d_primary:.4f} d_brier_primary_vs_sg={b_primary:.4f} "
        "d_auprc_linear_vs_sg={d_linear:.4f} d_auprc_primary_vs_linear={d_pl:.4f} "
        "diagnoses={diagnoses} next={next_todo}".format(
            status=summary["status"],
            rows=summary["input"]["rows"],
            validation_used=summary["boundary"]["validation_usage"],
            d_primary=safe_float(deltas["primary_vs_semantic_plus_geometry"].get("auprc")),
            b_primary=safe_float(deltas["primary_vs_semantic_plus_geometry"].get("brier")),
            d_linear=safe_float(deltas["linear_vs_semantic_plus_geometry"].get("auprc")),
            d_pl=safe_float(deltas["primary_vs_linear"].get("auprc")),
            diagnoses=len(summary["diagnosis"]),
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
