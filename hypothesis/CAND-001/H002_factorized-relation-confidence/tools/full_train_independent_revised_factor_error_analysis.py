#!/usr/bin/env python3
"""Post-hoc error/shortcut analysis for H002 revised factor smoke."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_SMOKE_DIR = RGA_ROOT / "independent_revised_factor_smoke_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_revised_factor_error_analysis_codex_ver"

REFERENCE_VIEW = "semantic_plus_geometry"
FOCUS_VIEWS = [
    "D1_revised_residual_base",
    "D2_support_contact_split_residual",
    "D3_relative_vertical_order_residual",
    "D4_coverage_uncertainty_shrinkage",
]
REPORT_VIEWS = [
    "current_factorized_reliability_posterior",
    "residual_reliability_model",
    *FOCUS_VIEWS,
]
CONTROL_VIEWS = [
    "family_only_offset_control",
    "raw_only_offset_control",
]
CONTROL_L2 = {
    "family_only_offset_control": 0.30,
    "raw_only_offset_control": 0.30,
}
RAW_PREFIX = "raw_"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--base-l2", type=float, default=0.03)
    return parser.parse_args()


def safe_float(value: Any, default: float = 0.0) -> float:
    return smoke.safe_float(value, default)


def clip(value: float, left: float = 0.0, right: float = 1.0) -> float:
    return min(max(value, left), right)


def logit(probability: float) -> float:
    probability = clip(probability, 1e-6, 1.0 - 1e-6)
    return math.log(probability / (1.0 - probability))


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def direction_bin(row: dict[str, Any]) -> str:
    features = row["baseline_inputs"]["factorized_reliability_posterior"]
    semantic = safe_float(features.get("semantic_score_norm"))
    geom = safe_float(features.get("p_geom_valid"), 0.5)
    gap = semantic - geom
    if gap >= 0.25:
        return "semantic_high_geometry_low"
    if gap <= -0.25:
        return "semantic_low_geometry_high"
    return "semantic_geometry_close"


def coverage_bin(row: dict[str, Any]) -> str:
    features = row["baseline_inputs"]["D4_coverage_uncertainty_shrinkage"]
    coverage = safe_float(features.get("coverage_flag"), 0.0)
    missing = safe_float(features.get("raw_geometry_missing_flag"), 0.0)
    if coverage >= 0.5:
        return "covered_raw_geometry"
    if missing >= 0.5:
        return "missing_raw_geometry"
    return "partial_or_unknown_coverage"


def contact_gap_bin(row: dict[str, Any]) -> str:
    value = abs(safe_float(row["baseline_inputs"]["D1_revised_residual_base"].get("raw_vertical_gap_subject_on_object")))
    if value < 0.05:
        return "gap<0.05"
    if value < 0.25:
        return "0.05<=gap<0.25"
    if value < 1.0:
        return "0.25<=gap<1.0"
    return "gap>=1.0"


def vertical_sign_bin(row: dict[str, Any]) -> str:
    features = row["baseline_inputs"]["D3_relative_vertical_order_residual"]
    if safe_float(features.get("relative_vertical_gate")) < 0.5:
        return "not_relative_vertical"
    if safe_float(features.get("relative_vertical_x_sign_agreement")) > 0.5:
        return "vertical_sign_agree"
    return "vertical_sign_conflict"


def load_predictions(smoke_dir: Path) -> dict[str, dict[str, float]]:
    predictions: dict[str, dict[str, float]] = defaultdict(dict)
    for row in smoke.read_jsonl(smoke_dir / "predictions.jsonl"):
        if row.get("split_eval") != "train_internal_grouped_by_scan":
            continue
        predictions[str(row["prediction_id"])][str(row["view"])] = safe_float(row["probability"], 0.5)
    return predictions


def grouped_folds(rows: list[dict[str, Any]], fold_count: int) -> tuple[list[list[int]], list[dict[str, Any]]]:
    groups: dict[str, list[int]] = {}
    for idx, row in enumerate(rows):
        groups.setdefault(str(row["identity"]["scan_id"]), []).append(idx)
    fold_count = max(2, min(fold_count, len(groups)))
    total_pos = sum(smoke.target_y(row) for row in rows)
    total_neg = len(rows) - total_pos
    target_pos = total_pos / fold_count
    target_neg = total_neg / fold_count
    target_rows = len(rows) / fold_count
    folds: list[list[int]] = [[] for _ in range(fold_count)]
    fold_pos = [0] * fold_count
    fold_neg = [0] * fold_count
    fold_rows = [0] * fold_count

    def group_order(item: tuple[str, list[int]]) -> tuple[int, int, str]:
        group, indices = item
        pos = sum(smoke.target_y(rows[idx]) for idx in indices)
        neg = len(indices) - pos
        return (len(indices), abs(pos - neg), group)

    for order, (_, indices) in enumerate(sorted(groups.items(), key=group_order, reverse=True)):
        pos = sum(smoke.target_y(rows[idx]) for idx in indices)
        neg = len(indices) - pos
        if order < fold_count:
            fold_idx = order
        else:
            fold_idx = min(
                range(fold_count),
                key=lambda idx: (
                    abs((fold_rows[idx] + len(indices)) - target_rows)
                    + abs((fold_pos[idx] + pos) - target_pos)
                    + abs((fold_neg[idx] + neg) - target_neg),
                    fold_rows[idx],
                    idx,
                ),
            )
        folds[fold_idx].extend(indices)
        fold_pos[fold_idx] += pos
        fold_neg[fold_idx] += neg
        fold_rows[fold_idx] += len(indices)

    summary = []
    for fold_idx, indices in enumerate(folds):
        summary.append(
            {
                "fold": fold_idx,
                "rows": len(indices),
                "groups": len({str(rows[idx]["identity"]["scan_id"]) for idx in indices}),
                "positive": sum(smoke.target_y(rows[idx]) for idx in indices),
                "negative": len(indices) - sum(smoke.target_y(rows[idx]) for idx in indices),
            }
        )
    return folds, summary


def add_control_views(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for row in rows:
        row = json.loads(json.dumps(row))
        identity = row["identity"]
        d1 = row["baseline_inputs"]["D1_revised_residual_base"]
        raw_only = {
            key: value
            for key, value in d1.items()
            if key.startswith(RAW_PREFIX)
            or key
            in {
                "geometry_available_flag",
                "geometry_checkable_flag",
                "raw_feature_present",
                "near_boundary_uncertainty",
                "unsupported_family_flag",
            }
        }
        row["baseline_inputs"]["family_only_offset_control"] = {
            "predicate_family": str(identity["predicate_family"]),
        }
        row["baseline_inputs"]["raw_only_offset_control"] = raw_only
        enriched.append(row)
    return enriched


def train_base_probs(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    *,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[float], list[float]]:
    schema = smoke.split_feature_types(train_rows, REFERENCE_VIEW)
    train_raw = smoke.vectorize(train_rows, REFERENCE_VIEW, schema)
    test_raw = smoke.vectorize(test_rows, REFERENCE_VIEW, schema)
    means, stds = smoke.fit_scaler(train_raw)
    train_xs = smoke.apply_scaler(train_raw, means, stds)
    test_xs = smoke.apply_scaler(test_raw, means, stds)
    weights = smoke.fit_logistic(
        train_xs,
        [smoke.target_y(row) for row in train_rows],
        [smoke.target_weight(row) for row in train_rows],
        epochs=epochs,
        learning_rate=learning_rate,
        l2=l2,
    )
    return smoke.predict_probs(train_xs, weights), smoke.predict_probs(test_xs, weights)


def fit_logistic_with_offset(
    xs: list[list[float]],
    offsets: list[float],
    ys: list[int],
    sample_weights: list[float],
    *,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> list[float]:
    if not xs:
        raise ValueError("empty training matrix")
    dims = len(xs[0])
    weights = [0.0] * (dims + 1)
    weight_sum = sum(sample_weights) or float(len(xs))
    for epoch in range(epochs):
        rate = learning_rate / math.sqrt(1.0 + epoch / 200.0)
        gradients = [0.0] * (dims + 1)
        for row, offset, y, sample_weight in zip(xs, offsets, ys, sample_weights):
            score = offset + weights[0]
            for idx, value in enumerate(row):
                score += weights[idx + 1] * value
            pred = smoke.sigmoid(score)
            error = (pred - y) * sample_weight
            gradients[0] += error
            for idx, value in enumerate(row):
                gradients[idx + 1] += error * value
        gradients[0] /= weight_sum
        for idx in range(dims):
            gradients[idx + 1] = gradients[idx + 1] / weight_sum + l2 * weights[idx + 1]
        for idx, gradient in enumerate(gradients):
            weights[idx] -= rate * gradient
    return weights


def predict_with_offset(xs: list[list[float]], offsets: list[float], weights: list[float]) -> list[float]:
    probs = []
    for row, offset in zip(xs, offsets):
        score = offset + weights[0]
        for idx, value in enumerate(row):
            score += weights[idx + 1] * value
        probs.append(smoke.sigmoid(score))
    return probs


def train_predict_grouped_offset_control(
    rows: list[dict[str, Any]],
    view: str,
    *,
    folds: int,
    epochs: int,
    learning_rate: float,
    base_l2: float,
) -> tuple[list[float], dict[str, Any]]:
    fold_indices, fold_summary = grouped_folds(rows, folds)
    probs_all = [0.5] * len(rows)
    feature_counts = []
    skipped = 0
    for test_indices in fold_indices:
        test_set = set(test_indices)
        train_rows = [row for idx, row in enumerate(rows) if idx not in test_set]
        test_rows = [rows[idx] for idx in test_indices]
        if {smoke.target_y(row) for row in train_rows} != {0, 1}:
            skipped += 1
            prior = sum(smoke.target_y(row) for row in train_rows) / max(len(train_rows), 1)
            for idx in test_indices:
                probs_all[idx] = prior
            continue
        train_base, test_base = train_base_probs(
            train_rows,
            test_rows,
            epochs=epochs,
            learning_rate=learning_rate,
            l2=base_l2,
        )
        schema = smoke.split_feature_types(train_rows, view)
        train_raw = smoke.vectorize(train_rows, view, schema)
        test_raw = smoke.vectorize(test_rows, view, schema)
        means, stds = smoke.fit_scaler(train_raw)
        train_xs = smoke.apply_scaler(train_raw, means, stds)
        test_xs = smoke.apply_scaler(test_raw, means, stds)
        weights = fit_logistic_with_offset(
            train_xs,
            [logit(prob) for prob in train_base],
            [smoke.target_y(row) for row in train_rows],
            [smoke.target_weight(row) for row in train_rows],
            epochs=epochs,
            learning_rate=learning_rate,
            l2=CONTROL_L2[view],
        )
        probs = predict_with_offset(test_xs, [logit(prob) for prob in test_base], weights)
        for idx, prob in zip(test_indices, probs):
            probs_all[idx] = prob
        feature_counts.append(len(smoke.vector_names(schema)))
    return probs_all, {
        "fold_count": len(fold_indices),
        "folds": fold_summary,
        "feature_count_min": min(feature_counts) if feature_counts else 0,
        "feature_count_max": max(feature_counts) if feature_counts else 0,
        "group_key": "scan_id",
        "skipped_single_class_train_folds": skipped,
    }


def rank_positions(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]], view: str) -> dict[str, int]:
    ordered = sorted(
        rows,
        key=lambda row: (
            -predictions[str(row["identity"]["prediction_id"])][view],
            str(row["identity"]["prediction_id"]),
        ),
    )
    return {str(row["identity"]["prediction_id"]): rank for rank, row in enumerate(ordered, start=1)}


def brier(y: int, probability: float) -> float:
    return (probability - y) ** 2


def correct(y: int, probability: float) -> bool:
    return int(probability >= 0.5) == y


def row_errors(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    views = [REFERENCE_VIEW, *REPORT_VIEWS]
    ranks_by_view = {view: rank_positions(rows, predictions, view) for view in views}
    outputs = []
    for row in rows:
        identity = row["identity"]
        row_id = str(identity["prediction_id"])
        y = smoke.target_y(row)
        ref_prob = predictions[row_id][REFERENCE_VIEW]
        ref_rank = ranks_by_view[REFERENCE_VIEW][row_id]
        d4 = row["baseline_inputs"]["D4_coverage_uncertainty_shrinkage"]
        d3 = row["baseline_inputs"]["D3_relative_vertical_order_residual"]
        common = {
            "prediction_id": row_id,
            "scan_id": identity["scan_id"],
            "subgraph_id": identity["subgraph_id"],
            "subject_id": identity["subject_id"],
            "subject_label": identity["subject_label"],
            "predicate_label": identity["predicate_label"],
            "predicate_family": identity["predicate_family"],
            "object_id": identity["object_id"],
            "object_label": identity["object_label"],
            "target": y,
            "direction_bin": direction_bin(row),
            "coverage_bin": coverage_bin(row),
            "contact_gap_bin": contact_gap_bin(row),
            "vertical_sign_bin": vertical_sign_bin(row),
            "semantic_score_norm": safe_float(d4.get("semantic_score_norm")),
            "p_geom_valid": safe_float(d4.get("p_geom_valid"), 0.5),
            "absolute_disagreement": safe_float(d4.get("absolute_disagreement")),
            "raw_vertical_gap_subject_on_object": safe_float(d4.get("raw_vertical_gap_subject_on_object")),
            "raw_normalized_distance_xy": safe_float(d4.get("raw_normalized_distance_xy")),
            "raw_projected_iou_xy": safe_float(d4.get("raw_projected_iou_xy")),
            "relative_vertical_sign_agreement": safe_float(d3.get("relative_vertical_x_sign_agreement")),
            "prob_semantic_plus_geometry": ref_prob,
            "rank_semantic_plus_geometry": ref_rank,
            "brier_semantic_plus_geometry": brier(y, ref_prob),
            "correct_semantic_plus_geometry": correct(y, ref_prob),
        }
        for view in REPORT_VIEWS:
            prob = predictions[row_id][view]
            view_correct = correct(y, prob)
            ref_correct = correct(y, ref_prob)
            if view_correct and not ref_correct:
                transfer_case = "view_correct_reference_wrong"
            elif ref_correct and not view_correct:
                transfer_case = "view_wrong_reference_correct"
            elif view_correct and ref_correct:
                transfer_case = "both_correct"
            else:
                transfer_case = "both_wrong"
            outputs.append(
                {
                    **common,
                    "view": view,
                    "prob_view": prob,
                    "rank_view": ranks_by_view[view][row_id],
                    "prob_delta_view_minus_sg": prob - ref_prob,
                    "rank_delta_view_minus_sg": ranks_by_view[view][row_id] - ref_rank,
                    "brier_view": brier(y, prob),
                    "brier_delta_view_minus_sg": brier(y, prob) - brier(y, ref_prob),
                    "correct_view": view_correct,
                    "transfer_case": transfer_case,
                    "positive_rank_improved": y == 1 and ranks_by_view[view][row_id] < ref_rank,
                    "negative_rank_demoted": y == 0 and ranks_by_view[view][row_id] > ref_rank,
                }
            )
    return outputs


def aggregate_slice(slice_name: str, slice_value: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [int(row["target"]) for row in rows]
    probs = [safe_float(row["prob_view"], 0.5) for row in rows]
    ref_probs = [safe_float(row["prob_semantic_plus_geometry"], 0.5) for row in rows]
    metrics = smoke.metrics(labels, probs) if len(set(labels)) == 2 else None
    ref_metrics = smoke.metrics(labels, ref_probs) if len(set(labels)) == 2 else None
    transfers = Counter(str(row["transfer_case"]) for row in rows)
    positives = [row for row in rows if int(row["target"]) == 1]
    negatives = [row for row in rows if int(row["target"]) == 0]
    return {
        "view": rows[0]["view"],
        "slice_name": slice_name,
        "slice_value": slice_value,
        "rows": len(rows),
        "positive": sum(labels),
        "negative": len(labels) - sum(labels),
        "view_correct_reference_wrong": transfers["view_correct_reference_wrong"],
        "view_wrong_reference_correct": transfers["view_wrong_reference_correct"],
        "new_mistakes_minus_fixes": transfers["view_wrong_reference_correct"] - transfers["view_correct_reference_wrong"],
        "positive_rank_improved": sum(1 for row in positives if row["positive_rank_improved"]),
        "negative_rank_demoted": sum(1 for row in negatives if row["negative_rank_demoted"]),
        "mean_brier_delta_view_minus_sg": sum(safe_float(row["brier_delta_view_minus_sg"]) for row in rows) / len(rows),
        "view_auprc": metrics.get("auprc") if metrics else None,
        "sg_auprc": ref_metrics.get("auprc") if ref_metrics else None,
        "delta_auprc_view_minus_sg": (
            metrics.get("auprc") - ref_metrics.get("auprc")
            if metrics and ref_metrics and metrics.get("auprc") is not None and ref_metrics.get("auprc") is not None
            else None
        ),
        "view_brier": metrics.get("brier") if metrics else None,
        "sg_brier": ref_metrics.get("brier") if ref_metrics else None,
        "delta_brier_view_minus_sg": (
            metrics.get("brier") - ref_metrics.get("brier")
            if metrics and ref_metrics and metrics.get("brier") is not None and ref_metrics.get("brier") is not None
            else None
        ),
    }


def build_slice_rows(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keys = [
        "predicate_family",
        "predicate_label",
        "direction_bin",
        "coverage_bin",
        "contact_gap_bin",
        "vertical_sign_bin",
    ]
    outputs = []
    by_view: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in errors:
        by_view[str(row["view"])].append(row)
    for _, view_rows in sorted(by_view.items()):
        for key in keys:
            groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in view_rows:
                groups[str(row[key])].append(row)
            for value, rows in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
                outputs.append(aggregate_slice(key, value, rows))
    return outputs


def rank_summary(errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    by_view: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in errors:
        by_view[str(row["view"])].append(row)
    for view, rows in sorted(by_view.items()):
        positives = [row for row in rows if int(row["target"]) == 1]
        negatives = [row for row in rows if int(row["target"]) == 0]
        outputs.append(
            {
                "view": view,
                "rows": len(rows),
                "positive": len(positives),
                "negative": len(negatives),
                "positive_rank_improved": sum(1 for row in positives if row["positive_rank_improved"]),
                "positive_rank_worsened": sum(1 for row in positives if safe_float(row["rank_delta_view_minus_sg"]) > 0),
                "negative_rank_demoted": sum(1 for row in negatives if row["negative_rank_demoted"]),
                "negative_rank_promoted": sum(1 for row in negatives if safe_float(row["rank_delta_view_minus_sg"]) < 0),
                "mean_positive_prob_delta": sum(safe_float(row["prob_delta_view_minus_sg"]) for row in positives)
                / len(positives),
                "mean_negative_prob_delta": sum(safe_float(row["prob_delta_view_minus_sg"]) for row in negatives)
                / len(negatives),
            }
        )
    return outputs


def threshold_transfer_from_predictions(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]], views: list[str]) -> list[dict[str, Any]]:
    outputs = []
    for view in views:
        counts = Counter()
        for row in rows:
            row_id = str(row["identity"]["prediction_id"])
            y = smoke.target_y(row)
            score = predictions[row_id][view]
            ref = predictions[row_id][REFERENCE_VIEW]
            view_correct = int(score >= 0.5) == y
            ref_correct = int(ref >= 0.5) == y
            if view_correct and not ref_correct:
                counts["view_correct_reference_wrong"] += 1
            elif ref_correct and not view_correct:
                counts["view_wrong_reference_correct"] += 1
            elif view_correct and ref_correct:
                counts["both_correct"] += 1
            else:
                counts["both_wrong"] += 1
        outputs.append(
            {
                "view": view,
                "reference_view": REFERENCE_VIEW,
                "rows": len(rows),
                "view_correct_reference_wrong": counts["view_correct_reference_wrong"],
                "view_wrong_reference_correct": counts["view_wrong_reference_correct"],
                "both_correct": counts["both_correct"],
                "both_wrong": counts["both_wrong"],
                "new_mistakes_minus_fixes": counts["view_wrong_reference_correct"] - counts["view_correct_reference_wrong"],
            }
        )
    return outputs


def control_metrics(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]], args: argparse.Namespace) -> dict[str, Any]:
    control_rows = add_control_views(rows)
    controls = []
    for view in CONTROL_VIEWS:
        probs, feature_summary = train_predict_grouped_offset_control(
            control_rows,
            view,
            folds=args.folds,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            base_l2=args.base_l2,
        )
        for row, prob in zip(control_rows, probs):
            predictions[str(row["identity"]["prediction_id"])][view] = prob
        labels = [smoke.target_y(row) for row in control_rows]
        metrics = smoke.metrics(labels, probs)
        ref_metrics = smoke.metrics(labels, [predictions[str(row["identity"]["prediction_id"])][REFERENCE_VIEW] for row in control_rows])
        controls.append(
            {
                "view": view,
                "kind": "train_only_offset_control",
                "metrics": metrics,
                "delta_vs_semantic_plus_geometry": {
                    "auroc": metrics["auroc"] - ref_metrics["auroc"] if metrics["auroc"] is not None else None,
                    "auprc": metrics["auprc"] - ref_metrics["auprc"] if metrics["auprc"] is not None else None,
                    "brier": metrics["brier"] - ref_metrics["brier"],
                },
                "feature_summary": feature_summary,
            }
        )
    return {
        "controls": controls,
        "threshold_transfer": threshold_transfer_from_predictions(control_rows, predictions, CONTROL_VIEWS),
    }


def diagnose(smoke_summary: dict[str, Any], slices: list[dict[str, Any]], controls: dict[str, Any]) -> list[str]:
    diagnoses = []
    by_name = {
        row["left"]: row["delta"]
        for row in smoke_summary["comparisons"]
        if row["right"] == REFERENCE_VIEW and row["split_eval"] == "train_internal_grouped_by_scan"
    }
    if all(by_name.get(view, {}).get("auprc", 0.0) > 0.05 for view in FOCUS_VIEWS):
        diagnoses.append("all_revised_views_improve_global_ranking")
    if all(by_name.get(view, {}).get("brier", 1.0) < -0.03 for view in FOCUS_VIEWS):
        diagnoses.append("all_revised_views_improve_global_calibration")
    d1_delta = by_name.get("D1_revised_residual_base", {})
    d4_delta = by_name.get("D4_coverage_uncertainty_shrinkage", {})
    if d1_delta.get("auprc", 0.0) > 0.05:
        diagnoses.append("family_categorical_not_sole_gain_source")
    if d4_delta.get("auprc", 0.0) > d1_delta.get("auprc", 0.0):
        diagnoses.append("family_interactions_add_ranking_gain_beyond_d1")
    d4_prox = [
        row
        for row in slices
        if row["view"] == "D4_coverage_uncertainty_shrinkage"
        and row["slice_name"] == "predicate_family"
        and row["slice_value"] == "proximity"
    ]
    if d4_prox and safe_float(d4_prox[0]["delta_auprc_view_minus_sg"]) < 0:
        diagnoses.append("proximity_ranking_regresses_despite_brier_gain")
    family_control = next((row for row in controls["controls"] if row["view"] == "family_only_offset_control"), None)
    if family_control and safe_float(family_control["delta_vs_semantic_plus_geometry"]["auprc"]) > 0.02:
        diagnoses.append("family_only_control_has_nontrivial_signal")
    raw_control = next((row for row in controls["controls"] if row["view"] == "raw_only_offset_control"), None)
    if raw_control and safe_float(raw_control["delta_vs_semantic_plus_geometry"]["auprc"]) > 0.05:
        diagnoses.append("raw_witness_control_has_strong_signal")
    return diagnoses


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Independent Revised Factor Error Analysis",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only post-hoc analysis.",
        "- No validation/test rows are used.",
        "- Control probes are trained only inside train-only grouped folds.",
        "- Hidden audit metadata, `geometry_status`, and multi-view are not model inputs.",
        "- Positive smoke remains bootstrap hypothesis-stage evidence only.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Diagnosis",
        "",
    ]
    for item in summary["diagnosis"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Shortcut Controls",
            "",
            "| Control | AUROC | AUPRC | Brier | dAUPRC vs SG | dBrier vs SG | New-Fix |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    transfer_by_view = {row["view"]: row for row in summary["control_threshold_transfer"]}
    for row in summary["shortcut_controls"]:
        m = row["metrics"]
        d = row["delta_vs_semantic_plus_geometry"]
        t = transfer_by_view[row["view"]]
        lines.append(
            f"| `{row['view']}` | {fmt(m['auroc'])} | {fmt(m['auprc'])} | {fmt(m['brier'])} | "
            f"{fmt(d['auprc'])} | {fmt(d['brier'])} | {t['new_mistakes_minus_fixes']} |"
        )
    lines.extend(
        [
            "",
            "## Key D4 Slices",
            "",
            "| Slice | Value | Rows | dAUPRC | dBrier | New-Fix |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["key_slices"]:
        lines.append(
            f"| `{row['slice_name']}` | `{row['slice_value']}` | {row['rows']} | "
            f"{fmt(row['delta_auprc_view_minus_sg'])} | {fmt(row['delta_brier_view_minus_sg'])} | "
            f"{row['new_mistakes_minus_fixes']} |"
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


def write_outputs(output_dir: Path, summary: dict[str, Any], errors: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_jsonl(output_dir / "row_errors.jsonl", errors)
    for view in FOCUS_VIEWS:
        view_rows = [row for row in errors if row["view"] == view]
        smoke.write_jsonl(
            output_dir / f"top_{view}_wins.jsonl",
            sorted(view_rows, key=lambda row: safe_float(row["brier_delta_view_minus_sg"]))[:20],
        )
        smoke.write_jsonl(
            output_dir / f"top_{view}_losses.jsonl",
            sorted(view_rows, key=lambda row: safe_float(row["brier_delta_view_minus_sg"]), reverse=True)[:20],
        )
    write_csv(
        output_dir / "slice_deltas.csv",
        summary["slice_deltas"],
        [
            "view",
            "slice_name",
            "slice_value",
            "rows",
            "positive",
            "negative",
            "view_correct_reference_wrong",
            "view_wrong_reference_correct",
            "new_mistakes_minus_fixes",
            "positive_rank_improved",
            "negative_rank_demoted",
            "mean_brier_delta_view_minus_sg",
            "view_auprc",
            "sg_auprc",
            "delta_auprc_view_minus_sg",
            "view_brier",
            "sg_brier",
            "delta_brier_view_minus_sg",
        ],
    )
    write_csv(
        output_dir / "rank_summary.csv",
        summary["rank_summary"],
        [
            "view",
            "rows",
            "positive",
            "negative",
            "positive_rank_improved",
            "positive_rank_worsened",
            "negative_rank_demoted",
            "negative_rank_promoted",
            "mean_positive_prob_delta",
            "mean_negative_prob_delta",
        ],
    )
    write_csv(
        output_dir / "shortcut_controls.csv",
        [
            {
                "view": row["view"],
                "kind": row["kind"],
                **row["metrics"],
                "delta_auroc_vs_sg": row["delta_vs_semantic_plus_geometry"]["auroc"],
                "delta_auprc_vs_sg": row["delta_vs_semantic_plus_geometry"]["auprc"],
                "delta_brier_vs_sg": row["delta_vs_semantic_plus_geometry"]["brier"],
            }
            for row in summary["shortcut_controls"]
        ],
        [
            "view",
            "kind",
            "rows",
            "positive",
            "negative",
            "auroc",
            "auprc",
            "brier",
            "ece_5bin",
            "nll",
            "accuracy_at_0_5",
            "delta_auroc_vs_sg",
            "delta_auprc_vs_sg",
            "delta_brier_vs_sg",
        ],
    )
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    smoke_dir = smoke.as_abs(args.smoke_dir)
    output_dir = smoke.as_abs(args.output_dir)
    smoke_summary = read_json(smoke_dir / "summary.json")
    rows = smoke.read_jsonl(smoke_dir / "revised_factor_rows.jsonl")
    predictions = load_predictions(smoke_dir)
    controls = control_metrics(rows, predictions, args)
    errors = row_errors(rows, predictions)
    slices = build_slice_rows(errors)
    ranks = rank_summary(errors)
    key_slices = [
        row
        for row in slices
        if row["view"] == "D4_coverage_uncertainty_shrinkage"
        and (
            (row["slice_name"] == "predicate_family" and row["slice_value"] in {"support_contact", "relative_vertical", "proximity"})
            or (row["slice_name"] == "direction_bin")
        )
    ]
    diagnosis = diagnose(smoke_summary, slices, controls)
    summary = {
        "schema_version": "h002_full_train_independent_revised_factor_error_analysis_summary_v0",
        "status": "full_train_independent_revised_factor_error_analysis_ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "smoke_dir": smoke.rel_path(smoke_dir),
            "smoke_status": smoke_summary.get("status"),
            "rows": len(rows),
        },
        "output_dir": smoke.rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "trains_control_probes": True,
            "validation_usage": False,
            "test_usage": False,
            "hidden_metadata_as_model_input": False,
            "geometry_status_as_model_input": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
            "posterior_performance_claim_allowed": False,
        },
        "diagnosis": diagnosis,
        "rank_summary": ranks,
        "slice_deltas": slices,
        "key_slices": key_slices,
        "shortcut_controls": controls["controls"],
        "control_threshold_transfer": controls["threshold_transfer"],
        "decision": (
            "The positive revised-factor smoke is not explained solely by the family categorical "
            "feature because D1, which has no family categorical feature, already gives a large "
            "gain and the family-only offset control is weak. However, the raw-only offset "
            "control has strong train-only signal, so the next step must run raw-witness "
            "shortcut-controlled ablations before any stronger claim."
        ),
        "claim_boundary": {
            "allowed": (
                "Revised raw-witness factorization is promising under train-only bootstrap labels, "
                "with gains concentrated in support_contact, relative_vertical, and both mismatch directions."
            ),
            "blocked": (
                "Paper-level posterior improvement claim remains blocked until shortcut-controlled "
                "ablation and stronger labels are available."
            ),
        },
        "next_todo": "full_train_independent_revised_factor_shortcut_controls",
    }
    write_outputs(output_dir, summary, errors)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    controls = {row["view"]: row for row in summary["shortcut_controls"]}
    fam = controls["family_only_offset_control"]["delta_vs_semantic_plus_geometry"]
    raw = controls["raw_only_offset_control"]["delta_vs_semantic_plus_geometry"]
    print(
        "status={status} validation_used={validation_used} diagnoses={diagnoses} "
        "family_only_d_auprc={family_auprc:.4f} raw_only_d_auprc={raw_auprc:.4f} "
        "next={next_todo}".format(
            status=summary["status"],
            validation_used=summary["boundary"]["validation_usage"],
            diagnoses=len(summary["diagnosis"]),
            family_auprc=fam["auprc"],
            raw_auprc=raw["auprc"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
