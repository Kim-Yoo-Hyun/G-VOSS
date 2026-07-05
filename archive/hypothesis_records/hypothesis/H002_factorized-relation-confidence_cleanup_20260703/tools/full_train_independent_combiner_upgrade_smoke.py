#!/usr/bin/env python3
"""Train-only smoke for H002 upgraded reliability combiners."""

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
DEFAULT_ROWS = RGA_ROOT / "independent_controlled_posterior_smoke_codex_ver/controlled_posterior_rows.jsonl"
DEFAULT_DESIGN = RGA_ROOT / "independent_combiner_upgrade_design_codex_ver/summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_combiner_upgrade_smoke_codex_ver"

TARGET_MODE = "proposed_role_balanced_codex_ver"
BASE_VIEW = "semantic_plus_geometry"

BASELINE_VIEWS = [
    "semantic_only",
    "geometry_only",
    "semantic_plus_geometry",
    "current_factorized_reliability_posterior",
    "residual_reliability_model",
]

BASELINE_VIEW_ALIASES = {
    "current_factorized_reliability_posterior": "factorized_reliability_posterior",
}

UPGRADED_VIEWS = [
    "C1_residual_logit_calibrator",
    "C2_family_gated_residual",
    "C3_uncertainty_gated_geometry",
]

CANDIDATE_L2 = {
    "C1_residual_logit_calibrator": 0.08,
    "C2_family_gated_residual": 0.15,
    "C3_uncertainty_gated_geometry": 0.10,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN)
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


def sigmoid(value: float) -> float:
    return smoke.sigmoid(value)


def base_features(row: dict[str, Any]) -> dict[str, float]:
    features = row["baseline_inputs"]["factorized_reliability_posterior"]
    semantic = safe_float(features.get("semantic_score_norm"))
    p_geom = safe_float(features.get("p_geom_valid"), 0.5)
    consistency = safe_float(features.get("consistency_score"))
    disagreement = abs(semantic - p_geom)
    rank = max(safe_float(features.get("semantic_rank"), 1.0), 1.0)
    return {
        "semantic_score_norm": semantic,
        "negative_semantic_score_norm": 1.0 - semantic,
        "semantic_rank": rank,
        "semantic_rank_log": math.log1p(rank),
        "semantic_rank_inverse": 1.0 / rank,
        "p_geom_valid": p_geom,
        "p_geom_invalid": 1.0 - p_geom,
        "consistency_score": consistency,
        "absolute_disagreement": disagreement,
        "semantic_minus_geometry": semantic - p_geom,
        "geometry_minus_semantic": p_geom - semantic,
        "underconfidence_score": max(0.0, p_geom - semantic),
        "overconfidence_score": max(0.0, semantic - p_geom),
        "semantic_x_geometry": semantic * p_geom,
        "semantic_x_consistency": semantic * consistency,
        "geometry_x_consistency": p_geom * consistency,
    }


def family_terms(row: dict[str, Any], features: dict[str, float]) -> dict[str, float | str]:
    family = str(row["identity"]["predicate_family"])
    terms: dict[str, float | str] = {"predicate_family": family}
    for candidate in ["support_contact", "relative_vertical", "proximity"]:
        value = 1.0 if family == candidate else 0.0
        prefix = f"family_{candidate}"
        terms[prefix] = value
        terms[f"{prefix}_x_abs_disagreement"] = value * features["absolute_disagreement"]
        terms[f"{prefix}_x_underconfidence"] = value * features["underconfidence_score"]
        terms[f"{prefix}_x_overconfidence"] = value * features["overconfidence_score"]
        terms[f"{prefix}_x_p_geom_valid"] = value * features["p_geom_valid"]
        terms[f"{prefix}_x_consistency"] = value * features["consistency_score"]
    return terms


def uncertainty_terms(features: dict[str, float]) -> dict[str, float]:
    semantic = features["semantic_score_norm"]
    p_geom = features["p_geom_valid"]
    consistency = features["consistency_score"]
    rank = features["semantic_rank"]
    semantic_uncertainty = 1.0 - 2.0 * abs(semantic - 0.5)
    rank_uncertainty = clip(math.log1p(rank) / math.log1p(1000.0))
    low_consistency = 1.0 - clip(consistency)
    disagreement = features["absolute_disagreement"]
    gate_proxy = clip((clip(semantic_uncertainty) + rank_uncertainty + disagreement + low_consistency) / 4.0)
    geometry_delta = p_geom - semantic
    return {
        "semantic_uncertainty": clip(semantic_uncertainty),
        "rank_uncertainty": rank_uncertainty,
        "low_consistency_proxy": low_consistency,
        "gate_proxy": gate_proxy,
        "gate_x_geometry_delta": gate_proxy * geometry_delta,
        "gate_x_abs_disagreement": gate_proxy * disagreement,
        "gate_x_underconfidence": gate_proxy * features["underconfidence_score"],
        "gate_x_overconfidence": gate_proxy * features["overconfidence_score"],
        "gate_x_p_geom_valid": gate_proxy * p_geom,
        "gate_x_consistency": gate_proxy * consistency,
        "coverage_missing_proxy": 1.0,
    }


def direction_bin(row: dict[str, Any]) -> str:
    features = base_features(row)
    gap = features["semantic_score_norm"] - features["p_geom_valid"]
    if gap >= 0.25:
        return "semantic_high_geometry_low"
    if gap <= -0.25:
        return "semantic_low_geometry_high"
    return "semantic_geometry_close"


def enrich_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = []
    for row in rows:
        row = dict(row)
        baseline_inputs = dict(row["baseline_inputs"])
        features = base_features(row)
        c1 = {
            "semantic_score_norm": features["semantic_score_norm"],
            "semantic_rank_log": features["semantic_rank_log"],
            "semantic_rank_inverse": features["semantic_rank_inverse"],
            "p_geom_valid": features["p_geom_valid"],
            "p_geom_invalid": features["p_geom_invalid"],
            "consistency_score": features["consistency_score"],
            "absolute_disagreement": features["absolute_disagreement"],
            "semantic_minus_geometry": features["semantic_minus_geometry"],
            "geometry_minus_semantic": features["geometry_minus_semantic"],
            "underconfidence_score": features["underconfidence_score"],
            "overconfidence_score": features["overconfidence_score"],
        }
        c2 = {**c1, **family_terms(row, features)}
        c3 = {
            "semantic_score_norm": features["semantic_score_norm"],
            "semantic_rank_log": features["semantic_rank_log"],
            "p_geom_valid": features["p_geom_valid"],
            "consistency_score": features["consistency_score"],
            "absolute_disagreement": features["absolute_disagreement"],
            "underconfidence_score": features["underconfidence_score"],
            "overconfidence_score": features["overconfidence_score"],
            **uncertainty_terms(features),
        }
        baseline_inputs["C1_residual_logit_calibrator"] = c1
        baseline_inputs["C2_family_gated_residual"] = c2
        baseline_inputs["C3_uncertainty_gated_geometry"] = c3
        row["baseline_inputs"] = baseline_inputs
        enriched.append(row)
    return enriched


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


def train_base_model(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    *,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[float], list[float], dict[str, Any]]:
    schema = smoke.split_feature_types(train_rows, BASE_VIEW)
    train_raw = smoke.vectorize(train_rows, BASE_VIEW, schema)
    test_raw = smoke.vectorize(test_rows, BASE_VIEW, schema)
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
    return smoke.predict_probs(train_xs, weights), smoke.predict_probs(test_xs, weights), {
        "base_feature_count": len(smoke.vector_names(schema)),
    }


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
            pred = sigmoid(score)
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
        probs.append(sigmoid(score))
    return probs


def fit_predict_offset(
    train_rows: list[dict[str, Any]],
    test_rows: list[dict[str, Any]],
    candidate: str,
    *,
    epochs: int,
    learning_rate: float,
    base_l2: float,
) -> tuple[list[float], list[float], dict[str, Any]]:
    train_base_probs, test_base_probs, base_summary = train_base_model(
        train_rows,
        test_rows,
        epochs=epochs,
        learning_rate=learning_rate,
        l2=base_l2,
    )
    schema = smoke.split_feature_types(train_rows, candidate)
    train_raw = smoke.vectorize(train_rows, candidate, schema)
    test_raw = smoke.vectorize(test_rows, candidate, schema)
    means, stds = smoke.fit_scaler(train_raw)
    train_xs = smoke.apply_scaler(train_raw, means, stds)
    test_xs = smoke.apply_scaler(test_raw, means, stds)
    weights = fit_logistic_with_offset(
        train_xs,
        [logit(prob) for prob in train_base_probs],
        [smoke.target_y(row) for row in train_rows],
        [smoke.target_weight(row) for row in train_rows],
        epochs=epochs,
        learning_rate=learning_rate,
        l2=CANDIDATE_L2[candidate],
    )
    train_probs = predict_with_offset(train_xs, [logit(prob) for prob in train_base_probs], weights)
    test_probs = predict_with_offset(test_xs, [logit(prob) for prob in test_base_probs], weights)
    return train_probs, test_probs, {
        **base_summary,
        "residual_feature_count": len(smoke.vector_names(schema)),
        "numeric_feature_count": len(schema["numeric"]),
        "categorical_feature_count": sum(len(values) for values in schema["categorical"].values()),
        "residual_l2": CANDIDATE_L2[candidate],
    }


def train_predict_in_sample_offset(
    rows: list[dict[str, Any]],
    candidate: str,
    *,
    epochs: int,
    learning_rate: float,
    base_l2: float,
) -> tuple[list[float], dict[str, Any]]:
    _, probs, summary = fit_predict_offset(
        rows,
        rows,
        candidate,
        epochs=epochs,
        learning_rate=learning_rate,
        base_l2=base_l2,
    )
    return probs, summary


def train_predict_crossfit_offset(
    rows: list[dict[str, Any]],
    candidate: str,
    *,
    folds: int,
    epochs: int,
    learning_rate: float,
    base_l2: float,
) -> tuple[list[float], dict[str, Any]]:
    fold_indices = smoke.stratified_folds(rows, folds)
    probs_all = [0.5] * len(rows)
    feature_counts = []
    for test_indices in fold_indices:
        test_set = set(test_indices)
        train_rows = [row for idx, row in enumerate(rows) if idx not in test_set]
        test_rows = [rows[idx] for idx in test_indices]
        if {smoke.target_y(row) for row in train_rows} != {0, 1}:
            prior = sum(smoke.target_y(row) for row in train_rows) / max(len(train_rows), 1)
            for idx in test_indices:
                probs_all[idx] = prior
            continue
        _, probs, summary = fit_predict_offset(
            train_rows,
            test_rows,
            candidate,
            epochs=epochs,
            learning_rate=learning_rate,
            base_l2=base_l2,
        )
        for idx, prob in zip(test_indices, probs):
            probs_all[idx] = prob
        feature_counts.append(summary["residual_feature_count"])
    return probs_all, {
        "fold_count": len(fold_indices),
        "fold_sizes": [len(indices) for indices in fold_indices],
        "feature_count_min": min(feature_counts) if feature_counts else 0,
        "feature_count_max": max(feature_counts) if feature_counts else 0,
    }


def train_predict_grouped_offset(
    rows: list[dict[str, Any]],
    candidate: str,
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
        _, probs, summary = fit_predict_offset(
            train_rows,
            test_rows,
            candidate,
            epochs=epochs,
            learning_rate=learning_rate,
            base_l2=base_l2,
        )
        for idx, prob in zip(test_indices, probs):
            probs_all[idx] = prob
        feature_counts.append(summary["residual_feature_count"])
    return probs_all, {
        "fold_count": len(fold_indices),
        "folds": fold_summary,
        "feature_count_min": min(feature_counts) if feature_counts else 0,
        "feature_count_max": max(feature_counts) if feature_counts else 0,
        "group_key": "scan_id",
        "skipped_single_class_train_folds": skipped,
    }


def train_predict_grouped_baseline(
    rows: list[dict[str, Any]],
    view: str,
    *,
    folds: int,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[float], dict[str, Any]]:
    actual_view = BASELINE_VIEW_ALIASES.get(view, view)
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
        schema = smoke.split_feature_types(train_rows, actual_view)
        train_raw = smoke.vectorize(train_rows, actual_view, schema)
        test_raw = smoke.vectorize(test_rows, actual_view, schema)
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
        probs = smoke.predict_probs(test_xs, weights)
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


def train_predict_baseline(
    rows: list[dict[str, Any]],
    view: str,
    split_eval: str,
    *,
    folds: int,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[float], dict[str, Any]]:
    actual_view = BASELINE_VIEW_ALIASES.get(view, view)
    if split_eval == "in_sample":
        return smoke.train_predict_in_sample(
            rows,
            actual_view,
            epochs=epochs,
            learning_rate=learning_rate,
            l2=l2,
        )
    if split_eval == "train_internal_3fold":
        return smoke.train_predict_crossfit(
            rows,
            actual_view,
            folds=folds,
            epochs=epochs,
            learning_rate=learning_rate,
            l2=l2,
        )
    if split_eval == "train_internal_grouped_by_scan":
        return train_predict_grouped_baseline(
            rows,
            view,
            folds=folds,
            epochs=epochs,
            learning_rate=learning_rate,
            l2=l2,
        )
    raise ValueError(f"unsupported split_eval: {split_eval}")


def train_predict_upgraded(
    rows: list[dict[str, Any]],
    view: str,
    split_eval: str,
    *,
    folds: int,
    epochs: int,
    learning_rate: float,
    base_l2: float,
) -> tuple[list[float], dict[str, Any]]:
    if split_eval == "in_sample":
        return train_predict_in_sample_offset(
            rows,
            view,
            epochs=epochs,
            learning_rate=learning_rate,
            base_l2=base_l2,
        )
    if split_eval == "train_internal_3fold":
        return train_predict_crossfit_offset(
            rows,
            view,
            folds=folds,
            epochs=epochs,
            learning_rate=learning_rate,
            base_l2=base_l2,
        )
    if split_eval == "train_internal_grouped_by_scan":
        return train_predict_grouped_offset(
            rows,
            view,
            folds=folds,
            epochs=epochs,
            learning_rate=learning_rate,
            base_l2=base_l2,
        )
    raise ValueError(f"unsupported split_eval: {split_eval}")


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
    return {
        "split_eval": split_eval,
        "left": left,
        "right": right,
        "delta": {
            "auroc": (
                left_metrics.get("auroc") - right_metrics.get("auroc")
                if left_metrics.get("auroc") is not None and right_metrics.get("auroc") is not None
                else None
            ),
            "auprc": (
                left_metrics.get("auprc") - right_metrics.get("auprc")
                if left_metrics.get("auprc") is not None and right_metrics.get("auprc") is not None
                else None
            ),
            "brier": (
                left_metrics.get("brier") - right_metrics.get("brier")
                if left_metrics.get("brier") is not None and right_metrics.get("brier") is not None
                else None
            ),
        },
    }


def slice_metrics(
    rows: list[dict[str, Any]],
    score_by_view: dict[str, list[float]],
    *,
    slice_name: str,
) -> list[dict[str, Any]]:
    def value_for(row: dict[str, Any]) -> str:
        if slice_name == "predicate_family":
            return str(row["identity"]["predicate_family"])
        if slice_name == "direction_bin":
            return direction_bin(row)
        raise ValueError(f"unsupported slice_name: {slice_name}")

    outputs = []
    values = sorted({value_for(row) for row in rows})
    for value in values:
        indices = [idx for idx, row in enumerate(rows) if value_for(row) == value]
        selected_rows = [rows[idx] for idx in indices]
        labels = {smoke.target_y(row) for row in selected_rows}
        for view, scores in score_by_view.items():
            selected_scores = [scores[idx] for idx in indices]
            if labels == {0, 1}:
                metrics = smoke.metrics([smoke.target_y(row) for row in selected_rows], selected_scores)
            else:
                counts = Counter(smoke.target_y(row) for row in selected_rows)
                metrics = {
                    "rows": len(selected_rows),
                    "positive": counts[1],
                    "negative": counts[0],
                    "auroc": None,
                    "auprc": None,
                    "brier": None,
                    "ece_5bin": None,
                    "nll": None,
                    "accuracy_at_0_5": None,
                }
            outputs.append(
                {
                    "slice_name": slice_name,
                    "slice_value": value,
                    "view": view,
                    "split_eval": "train_internal_grouped_by_scan_slice",
                    "single_class": labels != {0, 1},
                    "metrics": metrics,
                }
            )
    return outputs


def threshold_transfer(
    rows: list[dict[str, Any]],
    score_by_view: dict[str, list[float]],
    *,
    reference_view: str = BASE_VIEW,
) -> list[dict[str, Any]]:
    reference_scores = score_by_view[reference_view]
    outputs = []
    for view, scores in score_by_view.items():
        counts = Counter()
        brier_counts = Counter()
        for row, score, reference_score in zip(rows, scores, reference_scores):
            y = smoke.target_y(row)
            view_correct = int(score >= 0.5) == y
            ref_correct = int(reference_score >= 0.5) == y
            if view_correct and not ref_correct:
                counts["view_correct_reference_wrong"] += 1
            elif ref_correct and not view_correct:
                counts["view_wrong_reference_correct"] += 1
            elif view_correct and ref_correct:
                counts["both_correct"] += 1
            else:
                counts["both_wrong"] += 1
            view_brier = (score - y) ** 2
            ref_brier = (reference_score - y) ** 2
            if view_brier < ref_brier - 1e-12:
                brier_counts["view_brier_better"] += 1
            elif ref_brier < view_brier - 1e-12:
                brier_counts["reference_brier_better"] += 1
            else:
                brier_counts["brier_tie"] += 1
        outputs.append(
            {
                "view": view,
                "reference_view": reference_view,
                "rows": len(rows),
                "view_correct_reference_wrong": counts["view_correct_reference_wrong"],
                "view_wrong_reference_correct": counts["view_wrong_reference_correct"],
                "both_correct": counts["both_correct"],
                "both_wrong": counts["both_wrong"],
                "view_brier_better": brier_counts["view_brier_better"],
                "reference_brier_better": brier_counts["reference_brier_better"],
                "brier_tie": brier_counts["brier_tie"],
                "new_mistakes_minus_fixes": counts["view_wrong_reference_correct"]
                - counts["view_correct_reference_wrong"],
            }
        )
    return outputs


def target_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(smoke.target_y(row) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "by_family": dict(sorted(Counter(str(row["identity"]["predicate_family"]) for row in rows).items())),
        "by_predicate": dict(sorted(Counter(str(row["identity"]["predicate_label"]) for row in rows).items())),
        "by_label": dict(sorted(Counter(str(row["target"]["relation_validity_label"]) for row in rows).items())),
    }


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
        "# H002 Full Train Independent Combiner Upgrade Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage smoke.",
        "- Active target is `proposed_role_balanced_codex_ver`.",
        "- No validation/test rows are used.",
        "- New combiners are trained only inside train-only folds.",
        "- Hidden audit metadata is not model input.",
        "- Multi-view is not model input.",
        "- Labels are Codex bootstrap labels, not paper-locked human labels.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Grouped Metrics",
        "",
        "| View | Kind | AUROC | AUPRC | Brier | ECE-5 | Accuracy |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["metric_rows"]:
        if row["split_eval"] != "train_internal_grouped_by_scan":
            continue
        m = row["metrics"]
        lines.append(
            f"| `{row['name']}` | `{row['kind']}` | {fmt(m['auroc'])} | {fmt(m['auprc'])} | "
            f"{fmt(m['brier'])} | {fmt(m['ece_5bin'])} | {fmt(m['accuracy_at_0_5'])} |"
        )
    lines.extend(
        [
            "",
            "## Deltas vs Semantic+Geometry",
            "",
            "| View | Delta AUROC | Delta AUPRC | Delta Brier |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["comparisons"]:
        if row["split_eval"] != "train_internal_grouped_by_scan" or row["right"] != BASE_VIEW:
            continue
        d = row["delta"]
        lines.append(f"| `{row['left']}` | {fmt(d['auroc'])} | {fmt(d['auprc'])} | {fmt(d['brier'])} |")
    lines.extend(
        [
            "",
            "## Threshold Transfer",
            "",
            "| View | Fixes | New Mistakes | Both Correct | Both Wrong | New-Fix |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["threshold_transfer"]:
        lines.append(
            f"| `{row['view']}` | {row['view_correct_reference_wrong']} | "
            f"{row['view_wrong_reference_correct']} | {row['both_correct']} | {row['both_wrong']} | "
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


def write_outputs(
    output_dir: Path,
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_jsonl(output_dir / "combiner_rows.jsonl", rows)
    smoke.write_jsonl(output_dir / "predictions.jsonl", predictions)
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
        [
            "kind",
            "target_mode",
            "split_eval",
            "name",
            "rows",
            "positive",
            "negative",
            "auroc",
            "auprc",
            "brier",
            "ece_5bin",
            "nll",
            "accuracy_at_0_5",
        ],
    )
    write_csv(
        output_dir / "comparisons.csv",
        [
            {
                "split_eval": row["split_eval"],
                "left": row["left"],
                "right": row["right"],
                "delta_auroc": row["delta"]["auroc"],
                "delta_auprc": row["delta"]["auprc"],
                "delta_brier": row["delta"]["brier"],
            }
            for row in summary["comparisons"]
        ],
        ["split_eval", "left", "right", "delta_auroc", "delta_auprc", "delta_brier"],
    )
    flat_slices = []
    for item in summary["slice_metrics"]:
        flat_slices.append(
            {
                "slice_name": item["slice_name"],
                "slice_value": item["slice_value"],
                "view": item["view"],
                "split_eval": item["split_eval"],
                "single_class": item["single_class"],
                **item["metrics"],
            }
        )
    write_csv(
        output_dir / "slice_metrics.csv",
        flat_slices,
        [
            "slice_name",
            "slice_value",
            "view",
            "split_eval",
            "single_class",
            "rows",
            "positive",
            "negative",
            "auroc",
            "auprc",
            "brier",
            "ece_5bin",
            "nll",
            "accuracy_at_0_5",
        ],
    )
    write_csv(
        output_dir / "threshold_transfer.csv",
        summary["threshold_transfer"],
        [
            "view",
            "reference_view",
            "rows",
            "view_correct_reference_wrong",
            "view_wrong_reference_correct",
            "both_correct",
            "both_wrong",
            "view_brier_better",
            "reference_brier_better",
            "brier_tie",
            "new_mistakes_minus_fixes",
        ],
    )
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = smoke.as_abs(args.output_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    design = json.loads(smoke.as_abs(args.design).read_text(encoding="utf-8"))
    rows = enrich_rows(smoke.read_jsonl(args.rows))
    split_evals = ["in_sample", "train_internal_3fold", "train_internal_grouped_by_scan"]

    metric_rows = []
    predictions = []
    feature_summaries: dict[str, Any] = {}
    grouped_scores: dict[str, list[float]] = {}

    for view in BASELINE_VIEWS:
        for split_eval in split_evals:
            probs, feature_summary = train_predict_baseline(
                rows,
                view,
                split_eval,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.base_l2,
            )
            metric_rows.append(metric_record("baseline", split_eval, view, rows, probs))
            feature_summaries[f"{view}/{split_eval}"] = feature_summary
            if split_eval == "train_internal_grouped_by_scan":
                grouped_scores[view] = probs
                for row, prob in zip(rows, probs):
                    predictions.append(
                        {
                            "prediction_id": row["identity"]["prediction_id"],
                            "split_eval": split_eval,
                            "view": view,
                            "kind": "baseline",
                            "posterior_target": smoke.target_y(row),
                            "probability": prob,
                        }
                    )

    for view in UPGRADED_VIEWS:
        for split_eval in split_evals:
            probs, feature_summary = train_predict_upgraded(
                rows,
                view,
                split_eval,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                base_l2=args.base_l2,
            )
            metric_rows.append(metric_record("upgraded", split_eval, view, rows, probs))
            feature_summaries[f"{view}/{split_eval}"] = feature_summary
            if split_eval == "train_internal_grouped_by_scan":
                grouped_scores[view] = probs
                for row, prob in zip(rows, probs):
                    predictions.append(
                        {
                            "prediction_id": row["identity"]["prediction_id"],
                            "split_eval": split_eval,
                            "view": view,
                            "kind": "upgraded",
                            "posterior_target": smoke.target_y(row),
                            "probability": prob,
                        }
                    )

    comparisons = []
    for split_eval in split_evals:
        for left in [
            "current_factorized_reliability_posterior",
            "residual_reliability_model",
            *UPGRADED_VIEWS,
        ]:
            comparisons.append(comparison(metric_rows, split_eval, left, BASE_VIEW))
        for left in UPGRADED_VIEWS:
            comparisons.append(comparison(metric_rows, split_eval, left, "current_factorized_reliability_posterior"))

    family_slices = slice_metrics(rows, grouped_scores, slice_name="predicate_family")
    direction_slices = slice_metrics(rows, grouped_scores, slice_name="direction_bin")
    transfers = threshold_transfer(rows, grouped_scores, reference_view=BASE_VIEW)

    grouped_comparisons = {
        item["left"]: item["delta"]
        for item in comparisons
        if item["split_eval"] == "train_internal_grouped_by_scan" and item["right"] == BASE_VIEW
    }
    transfer_by_view = {item["view"]: item for item in transfers}
    progress_views = []
    for view in UPGRADED_VIEWS:
        delta = grouped_comparisons[view]
        transfer = transfer_by_view[view]
        auprc_ok = delta.get("auprc") is not None and delta["auprc"] >= 0.01
        brier_ok = delta.get("brier") is not None and delta["brier"] <= -0.005
        transfer_ok = transfer["new_mistakes_minus_fixes"] <= 0
        if (auprc_ok or brier_ok) and transfer_ok:
            progress_views.append(view)

    if progress_views:
        status = "full_train_independent_combiner_upgrade_positive_smoke"
        next_todo = "full_train_independent_combiner_upgrade_error_analysis"
        decision = (
            "At least one upgraded combiner passes the train-only progression threshold "
            "against semantic_plus_geometry. Treat this as bootstrap hypothesis-stage "
            "evidence only and inspect errors before any broader claim."
        )
    else:
        status = "full_train_independent_combiner_upgrade_no_safe_gain"
        next_todo = "full_train_independent_combiner_upgrade_error_analysis"
        decision = (
            "The upgraded combiners do not pass the safe progression threshold against "
            "semantic_plus_geometry under grouped train-only folds. Inspect slice-level "
            "errors before adding capacity or changing the target."
        )

    summary = {
        "schema_version": "h002_full_train_independent_combiner_upgrade_smoke_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "rows": smoke.rel_path(args.rows),
            "design": smoke.rel_path(args.design),
        },
        "output_dir": smoke.rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "target_mode": TARGET_MODE,
            "label_source": "codex_ver_full_train_independent_visible_surface_bootstrap",
            "trains_new_combiner": True,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "hidden_metadata_as_model_input": False,
            "validation_usage": False,
            "test_usage": False,
            "multi_view_as_model_input": False,
            "upgraded_combiner_is_offset_over_semantic_plus_geometry": True,
        },
        "hyperparameters": {
            "folds": args.folds,
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "base_l2": args.base_l2,
            "candidate_l2": CANDIDATE_L2,
            "tuned_on_validation": False,
        },
        "design_status": design.get("status"),
        "target_summary": target_summary(rows),
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "slice_metrics": family_slices + direction_slices,
        "threshold_transfer": transfers,
        "feature_summaries": feature_summaries,
        "progress_views": progress_views,
        "decision": decision,
        "next_todo": next_todo,
    }
    write_outputs(output_dir, summary, rows, predictions)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    grouped = {
        row["name"]: row["metrics"]
        for row in summary["metric_rows"]
        if row["split_eval"] == "train_internal_grouped_by_scan"
    }
    base = grouped[BASE_VIEW]
    best_view = max(UPGRADED_VIEWS, key=lambda view: grouped[view]["auprc"])
    best = grouped[best_view]
    print(
        "status={status} rows={rows} validation_used={validation_used} "
        "best_upgraded={best_view} d_auprc_vs_sg={d_auprc:.4f} "
        "d_brier_vs_sg={d_brier:.4f} progress_views={progress_views} next={next_todo}".format(
            status=summary["status"],
            rows=summary["target_summary"]["rows"],
            validation_used=summary["boundary"]["validation_usage"],
            best_view=best_view,
            d_auprc=best["auprc"] - base["auprc"],
            d_brier=best["brier"] - base["brier"],
            progress_views=",".join(summary["progress_views"]) if summary["progress_views"] else "none",
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
