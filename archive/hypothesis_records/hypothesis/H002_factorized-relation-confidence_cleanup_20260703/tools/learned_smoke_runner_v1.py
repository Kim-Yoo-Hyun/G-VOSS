#!/usr/bin/env python3
"""Run train-internal learned smoke baselines for H002.

The runner intentionally uses a small pure-Python logistic model because this
workspace does not assume sklearn/numpy availability. Results are hypothesis
diagnostics only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from smoke_baseline_runner_v1 import (
    auprc,
    auroc,
    binary_metrics,
    multiclass_metrics,
    p_geom_valid,
    q_observability_score,
    rel_path,
    safe_float,
)


H002_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_ROOT = H002_ROOT / "artifacts/prototype_dataset_v1"
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/learned_smoke_v1"


FeatureFn = Callable[[dict[str, Any]], dict[str, float]]
LabelFn = Callable[[dict[str, Any]], int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sigmoid(value: float) -> float:
    if value >= 40:
        return 1.0
    if value <= -40:
        return 0.0
    return 1.0 / (1.0 + math.exp(-value))


def logit_prior(labels: list[int]) -> float:
    pos = sum(labels) + 0.5
    neg = len(labels) - sum(labels) + 0.5
    return math.log(pos / neg)


def one_hot(prefix: str, value: Any) -> dict[str, float]:
    text = str(value) if value is not None and value != "" else "missing"
    text = text.replace(" ", "_").replace("/", "_")
    return {f"{prefix}={text}": 1.0}


def numeric(prefix: str, value: Any, default: float = 0.0) -> dict[str, float]:
    return {prefix: safe_float(value, default)}


def t_features(row: dict[str, Any]) -> dict[str, float]:
    t = row.get("T_e", {})
    out: dict[str, float] = {}
    out.update(one_hot("family", t.get("relation_family")))
    out.update(one_hot("predicate", t.get("predicate_label")))
    out.update(one_hot("subject", t.get("subject_label")))
    out.update(one_hot("object", t.get("object_label")))
    return out


def t_family_predicate_features(row: dict[str, Any]) -> dict[str, float]:
    t = row.get("T_e", {})
    out: dict[str, float] = {}
    out.update(one_hot("family", t.get("relation_family")))
    out.update(one_hot("predicate", t.get("predicate_label")))
    return out


def z_features(row: dict[str, Any]) -> dict[str, float]:
    z = row.get("Z_e", {})
    rank = safe_float(z.get("source_rank"), 999.0)
    score = safe_float(z.get("source_score_normalized"), 0.5)
    out = {
        "source_score_normalized": score,
        "source_score_missing": 0.0 if z.get("source_score_available") else 1.0,
        "source_rank_inverse": 1.0 / (1.0 + max(rank, 0.0)),
        "source_rank_log": math.log1p(max(rank, 0.0)),
    }
    out.update(one_hot("source_id", z.get("source_id")))
    out.update(one_hot("rank_band", z.get("source_rank_band")))
    return out


def z_scalar_features(row: dict[str, Any]) -> dict[str, float]:
    z = row.get("Z_e", {})
    rank = safe_float(z.get("source_rank"), 999.0)
    return {
        "source_score_normalized": safe_float(z.get("source_score_normalized"), 0.5),
        "source_rank_inverse": 1.0 / (1.0 + max(rank, 0.0)),
    }


def g_features(row: dict[str, Any]) -> dict[str, float]:
    features = row.get("G_e", {}).get("geometry_features", {})
    return {f"G.{key}": safe_float(value, 0.0) for key, value in sorted(features.items())}


def p_geom_features(row: dict[str, Any]) -> dict[str, float]:
    pg = p_geom_valid(row)
    return {"p_geom_valid": pg, "p_geom_invalid": 1.0 - pg}


def q_features(row: dict[str, Any]) -> dict[str, float]:
    q = row.get("Q_e", {})
    out: dict[str, float] = {
        "q_proxy": q_observability_score(row),
        "low_coverage": 1.0 if q.get("low_coverage_flag") else 0.0,
        "missing_geometry": 1.0 if q.get("missing_geometry_flag") else 0.0,
        "unsupported_family": 1.0 if q.get("unsupported_family_flag") else 0.0,
        "evidence_conflict": 1.0 if q.get("evidence_conflict_flag") else 0.0,
        "same_frame_visible": 1.0 if q.get("same_frame_visible") is True else 0.0,
        "mesh_available": 1.0 if q.get("mesh_available") is True else 0.0,
        "multi_view_count": safe_float(q.get("multi_view_count"), 0.0),
    }
    out.update(one_hot("asset_tier", q.get("asset_tier")))
    for key, value in sorted((q.get("coverage_features") or {}).items()):
        out[f"Q.coverage.{key}"] = safe_float(value, 0.0)
    return out


def merge_features(*blocks: dict[str, float]) -> dict[str, float]:
    out: dict[str, float] = {}
    for block in blocks:
        out.update(block)
    return out


def model_feature_fns() -> dict[str, FeatureFn]:
    return {
        "M0_intercept": lambda row: {},
        "M1_source_only_Z": z_features,
        "M2_semantic_source_TZ": lambda row: merge_features(t_features(row), z_features(row)),
        "M3_geometry_rule_pgeom": p_geom_features,
        "M4_geometry_only_G": g_features,
        "M5_compatibility_TG": lambda row: merge_features(t_features(row), g_features(row)),
        "M6_factorized_TZGQ": lambda row: merge_features(t_features(row), z_features(row), g_features(row), q_features(row)),
        "S1_predicate_family_shortcut": t_family_predicate_features,
        "S2_source_rank_shortcut": z_scalar_features,
    }


class LogisticModel:
    def __init__(self, feature_names: list[str], means: dict[str, float], stds: dict[str, float], weights: dict[str, float], bias: float):
        self.feature_names = feature_names
        self.means = means
        self.stds = stds
        self.weights = weights
        self.bias = bias

    def transform_value(self, name: str, value: float) -> float:
        return (value - self.means[name]) / self.stds[name]

    def predict_one(self, features: dict[str, float]) -> float:
        total = self.bias
        for name in self.feature_names:
            total += self.weights[name] * self.transform_value(name, features.get(name, 0.0))
        return sigmoid(total)


def build_scaler(feature_dicts: list[dict[str, float]]) -> tuple[list[str], dict[str, float], dict[str, float]]:
    names = sorted({name for feats in feature_dicts for name in feats})
    means: dict[str, float] = {}
    stds: dict[str, float] = {}
    for name in names:
        vals = [feats.get(name, 0.0) for feats in feature_dicts]
        avg = sum(vals) / max(len(vals), 1)
        var = sum((value - avg) ** 2 for value in vals) / max(len(vals), 1)
        std = math.sqrt(var)
        means[name] = avg
        stds[name] = std if std > 1e-8 else 1.0
    return names, means, stds


def class_weights(labels: list[int]) -> dict[int, float]:
    count = Counter(labels)
    total = len(labels)
    return {
        0: total / max(2 * count.get(0, 1), 1),
        1: total / max(2 * count.get(1, 1), 1),
    }


def train_logistic(
    feature_dicts: list[dict[str, float]],
    labels: list[int],
    epochs: int,
    lr: float,
    l2: float,
) -> LogisticModel:
    names, means, stds = build_scaler(feature_dicts)
    weights = {name: 0.0 for name in names}
    bias = logit_prior(labels)
    weights_by_class = class_weights(labels)
    n = max(len(labels), 1)
    for _ in range(epochs):
        grad_w = {name: 0.0 for name in names}
        grad_b = 0.0
        weight_sum = 0.0
        for feats, label in zip(feature_dicts, labels):
            linear = bias
            transformed = {}
            for name in names:
                x = (feats.get(name, 0.0) - means[name]) / stds[name]
                transformed[name] = x
                linear += weights[name] * x
            pred = sigmoid(linear)
            row_weight = weights_by_class[int(label)]
            err = (pred - label) * row_weight
            grad_b += err
            weight_sum += row_weight
            for name in names:
                grad_w[name] += err * transformed[name]
        denom = max(weight_sum, float(n), 1.0)
        bias -= lr * grad_b / denom
        for name in names:
            grad = grad_w[name] / denom + l2 * weights[name]
            weights[name] -= lr * grad
    return LogisticModel(names, means, stds, weights, bias)


def fold_key(row: dict[str, Any], task: str) -> str:
    if task == "task_a":
        return str(row.get("group_id") or row.get("scan_id") or row.get("row_id"))
    return str(row.get("scan_id") or row.get("group_id") or row.get("row_id"))


def stable_hash(text: str) -> int:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def make_folds(rows: list[dict[str, Any]], task: str, fold_count: int) -> list[list[int]]:
    groups: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        groups[fold_key(row, task)].append(idx)
    ordered = sorted(groups.items(), key=lambda item: stable_hash(item[0]))
    folds = [[] for _ in range(max(2, fold_count))]
    for pos, (_, indices) in enumerate(ordered):
        folds[pos % len(folds)].extend(indices)
    return [fold for fold in folds if fold]


def train_eval_cv(
    rows: list[dict[str, Any]],
    labels: list[int],
    feature_fn: FeatureFn,
    task: str,
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> dict[str, Any]:
    folds = make_folds(rows, task, fold_count)
    predictions = [0.5] * len(rows)
    fold_summaries = []
    for fold_idx, test_indices in enumerate(folds):
        test_set = set(test_indices)
        train_indices = [idx for idx in range(len(rows)) if idx not in test_set]
        y_train = [labels[idx] for idx in train_indices]
        y_test = [labels[idx] for idx in test_indices]
        if len(set(y_train)) < 2:
            prior = sum(y_train) / max(len(y_train), 1)
            for idx in test_indices:
                predictions[idx] = prior
            fold_summaries.append({"fold": fold_idx, "train_rows": len(train_indices), "test_rows": len(test_indices), "mode": "prior_only"})
            continue
        train_feats = [feature_fn(rows[idx]) for idx in train_indices]
        model = train_logistic(train_feats, y_train, epochs=epochs, lr=lr, l2=l2)
        for idx in test_indices:
            predictions[idx] = model.predict_one(feature_fn(rows[idx]))
        fold_summaries.append(
            {
                "fold": fold_idx,
                "train_rows": len(train_indices),
                "test_rows": len(test_indices),
                "train_positive": sum(y_train),
                "test_positive": sum(y_test),
                "feature_count": len(model.feature_names),
                "mode": "logistic",
            }
        )
    return {
        "metrics": binary_metrics(labels, predictions),
        "predictions": predictions,
        "folds": fold_summaries,
    }


def task_a_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("counterfactual_axis", {}).get("compatibility_label") in {"positive", "counterfactual_negative"}
    ]


def task_a_labels(rows: list[dict[str, Any]]) -> list[int]:
    return [1 if row["counterfactual_axis"]["compatibility_label"] == "positive" else 0 for row in rows]


def task_b_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("observability_axis", {}).get("observability_label") in {"observable", "limited", "insufficient"}
    ]


def task_b_labels(rows: list[dict[str, Any]]) -> list[int]:
    return [1 if row["observability_axis"]["observability_label"] == "observable" else 0 for row in rows]


def task_c_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("reliability_eval_axis", {}).get("binary_usable")
        and row.get("reliability_eval_axis", {}).get("reliability_label") in {"accept", "reject"}
    ]


def task_c_labels(rows: list[dict[str, Any]]) -> list[int]:
    return [1 if row["reliability_eval_axis"]["reliability_label"] == "accept" else 0 for row in rows]


def eval_task(
    rows: list[dict[str, Any]],
    labels: list[int],
    task_name: str,
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[dict[str, Any], dict[str, list[float]], dict[str, Any]]:
    metrics: dict[str, Any] = {}
    predictions: dict[str, list[float]] = {}
    folds: dict[str, Any] = {}
    for name, feature_fn in model_feature_fns().items():
        result = train_eval_cv(rows, labels, feature_fn, task_name, fold_count, epochs, lr, l2)
        metrics[name] = result["metrics"]
        predictions[name] = result["predictions"]
        folds[name] = result["folds"]
    return metrics, predictions, folds


def group_metrics(
    rows: list[dict[str, Any]],
    labels: list[int],
    predictions: dict[str, list[float]],
    group_fn: Callable[[dict[str, Any]], str],
) -> dict[str, Any]:
    grouped: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        grouped[group_fn(row)].append(idx)
    output: dict[str, Any] = {}
    for group, indices in sorted(grouped.items()):
        if len(indices) < 4:
            continue
        y = [labels[idx] for idx in indices]
        output[group] = {}
        for name, scores in predictions.items():
            output[group][name] = binary_metrics(y, [scores[idx] for idx in indices])
    return output


def multiclass_two_head(
    all_rows: list[dict[str, Any]],
    p_obs_by_row_id: dict[str, float],
    p_rel_by_row_id: dict[str, float],
    threshold_obs: float = 0.5,
    threshold_rel: float = 0.5,
) -> dict[str, Any]:
    labels: list[str] = []
    preds: list[str] = []
    for row in all_rows:
        axis = row.get("reliability_eval_axis", {})
        label = axis.get("reliability_label")
        if label not in {"accept", "reject", "abstain"} or not axis.get("multiclass_usable"):
            continue
        row_id = row["row_id"]
        p_obs = p_obs_by_row_id.get(row_id, 0.5)
        p_rel = p_rel_by_row_id.get(row_id, 0.5)
        if p_obs < threshold_obs:
            pred = "abstain"
        elif p_rel >= threshold_rel:
            pred = "accept"
        else:
            pred = "reject"
        labels.append(label)
        preds.append(pred)
    majority_label = Counter(labels).most_common(1)[0][0] if labels else "reject"
    return {
        "two_head": multiclass_metrics(labels, preds),
        "majority": multiclass_metrics(labels, [majority_label for _ in labels]),
        "majority_label": majority_label,
        "threshold_obs": threshold_obs,
        "threshold_rel": threshold_rel,
    }


def predictions_to_row_map(rows: list[dict[str, Any]], scores: list[float]) -> dict[str, float]:
    return {row["row_id"]: score for row, score in zip(rows, scores)}


def validation_errors(input_root: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    mat_errors = input_root / "validation_errors.jsonl"
    if not mat_errors.exists():
        errors.append({"error_type": "missing_materialization_validation_errors"})
    elif mat_errors.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "materialization_validation_errors_nonempty"})
    for row in rows:
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_id": row.get("row_id")})
        if "Z_e" in row.get("model_views", {}).get("compatibility_main", {}):
            errors.append({"error_type": "Z_e_in_compatibility_main", "row_id": row.get("row_id")})
    return errors


def gate_summary(task_a: dict[str, Any], task_b: dict[str, Any], task_c: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    source = task_a["M1_source_only_Z"]["auroc"]
    t_z = task_a["M2_semantic_source_TZ"]["auroc"]
    g_only = task_a["M4_geometry_only_G"]["auroc"]
    compat = task_a["M5_compatibility_TG"]["auroc"]
    shortcut = task_a["S1_predicate_family_shortcut"]["auroc"]
    obs = task_b["M6_factorized_TZGQ"]["auroc"]
    obs_shortcut = task_b["S1_predicate_family_shortcut"]["auroc"]
    rel = task_c["M6_factorized_TZGQ"]["auroc"]
    rel_source = task_c["M1_source_only_Z"]["auroc"]
    gates = {
        "gate_1_dataset_sanity": {
            "pass": not errors and task_a["M0_intercept"]["positive"] == task_a["M0_intercept"]["negative"],
            "validation_errors": len(errors),
        },
        "gate_2_learned_compatibility_signal": {
            "pass": compat is not None and source is not None and compat > source and compat >= max(g_only or 0.0, source or 0.0),
            "source_auc": source,
            "semantic_source_auc": t_z,
            "geometry_only_auc": g_only,
            "compatibility_TG_auc": compat,
            "predicate_family_shortcut_auc": shortcut,
            "notes": "If predicate/family shortcut is close to compatibility, claim must remain diagnostic.",
        },
        "gate_3_observability_signal": {
            "pass": obs is not None and obs_shortcut is not None and obs > obs_shortcut,
            "factorized_auc": obs,
            "predicate_family_shortcut_auc": obs_shortcut,
        },
        "gate_4_reliability_signal": {
            "pass": rel is not None and rel_source is not None and rel > rel_source,
            "factorized_auc": rel,
            "source_auc": rel_source,
        },
    }
    gates["overall_interpretation"] = (
        "learned_smoke_promising_but_needs_family_shortcut_review"
        if gates["gate_1_dataset_sanity"]["pass"] and gates["gate_2_learned_compatibility_signal"]["pass"]
        else "learned_smoke_diagnostic_only_needs_error_analysis"
    )
    return gates


def error_cases(rows: list[dict[str, Any]], labels: list[int], scores: list[float], model_name: str, max_cases: int = 25) -> list[dict[str, Any]]:
    cases = []
    for row, label, score in zip(rows, labels, scores):
        pred = 1 if score >= 0.5 else 0
        if pred == label:
            continue
        cases.append(
            {
                "row_id": row["row_id"],
                "candidate_relation_text": row["candidate_relation_text"],
                "family": row["T_e"]["relation_family"],
                "predicate": row["T_e"]["predicate_label"],
                "label": label,
                "pred": pred,
                "score": score,
                "model": model_name,
                "source_score": safe_float(row.get("Z_e", {}).get("source_score_normalized"), 0.5),
                "p_geom_valid": p_geom_valid(row),
                "observability": row.get("observability_axis", {}).get("observability_label"),
            }
        )
    return sorted(cases, key=lambda row: abs(row["score"] - 0.5), reverse=True)[:max_cases]


def write_report(path: Path, summary: dict[str, Any], metrics_by_task: dict[str, Any], gates: dict[str, Any]) -> None:
    task_a = metrics_by_task["task_a_compatibility"]
    lines = [
        "# H002 Learned Smoke V1",
        "",
        f"Date: {summary['created_at']}",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Dataset",
        "",
        f"- Task A rows: `{summary['counts']['task_a_rows']}`",
        f"- Task B rows: `{summary['counts']['task_b_rows']}`",
        f"- Task C rows: `{summary['counts']['task_c_rows']}`",
        f"- validation errors: `{summary['counts']['validation_errors']}`",
        "",
        "## Task A Compatibility",
        "",
        "| Model | AUROC | AUPRC |",
        "| --- | ---: | ---: |",
    ]
    for name in [
        "M1_source_only_Z",
        "M2_semantic_source_TZ",
        "M3_geometry_rule_pgeom",
        "M4_geometry_only_G",
        "M5_compatibility_TG",
        "M6_factorized_TZGQ",
        "S1_predicate_family_shortcut",
    ]:
        metric = task_a[name]
        lines.append(f"| `{name}` | {metric['auroc']} | {metric['auprc']} |")
    lines.extend(
        [
            "",
            "## Gates",
            "",
            f"- dataset sanity: `{gates['gate_1_dataset_sanity']['pass']}`",
            f"- learned compatibility signal: `{gates['gate_2_learned_compatibility_signal']['pass']}`",
            f"- observability signal: `{gates['gate_3_observability_signal']['pass']}`",
            f"- reliability signal: `{gates['gate_4_reliability_signal']['pass']}`",
            f"- overall: `{gates['overall_interpretation']}`",
            "",
            "## Boundary",
            "",
            "- train-internal grouped-fold smoke only",
            "- pure-Python small logistic models",
            "- no validation/test usage",
            "- no paper-level evidence",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_root = args.input_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(input_root / "prototype_rows.jsonl")
    materialization_summary = read_json(input_root / "summary.json")
    errors = validation_errors(input_root, rows)

    a_rows = task_a_rows(rows)
    a_labels = task_a_labels(a_rows)
    b_rows = task_b_rows(rows)
    b_labels = task_b_labels(b_rows)
    c_rows = task_c_rows(rows)
    c_labels = task_c_labels(c_rows)

    task_a_metrics, task_a_preds, task_a_folds = eval_task(a_rows, a_labels, "task_a", args.folds, args.epochs, args.lr, args.l2)
    task_b_metrics, task_b_preds, task_b_folds = eval_task(b_rows, b_labels, "task_b", args.folds, args.epochs, args.lr, args.l2)
    task_c_metrics, task_c_preds, task_c_folds = eval_task(c_rows, c_labels, "task_c", args.folds, args.epochs, args.lr, args.l2)

    metrics_by_task = {
        "task_a_compatibility": task_a_metrics,
        "task_b_observability": task_b_metrics,
        "task_c_reliability_binary": task_c_metrics,
    }
    metrics_by_family = {
        "task_a_by_family": group_metrics(
            a_rows,
            a_labels,
            task_a_preds,
            lambda row: str(row["T_e"]["relation_family"]),
        ),
        "task_a_by_predicate": group_metrics(
            a_rows,
            a_labels,
            task_a_preds,
            lambda row: str(row["T_e"]["predicate_label"]),
        ),
    }
    p_obs_map = predictions_to_row_map(b_rows, task_b_preds["M6_factorized_TZGQ"])
    p_rel_map = predictions_to_row_map(c_rows, task_c_preds["M6_factorized_TZGQ"])
    multiclass = multiclass_two_head(rows, p_obs_map, p_rel_map)
    gates = gate_summary(task_a_metrics, task_b_metrics, task_c_metrics, errors)

    prediction_rows = []
    for task_name, task_rows, labels, preds in [
        ("task_a", a_rows, a_labels, task_a_preds),
        ("task_b", b_rows, b_labels, task_b_preds),
        ("task_c", c_rows, c_labels, task_c_preds),
    ]:
        for idx, row in enumerate(task_rows):
            prediction_rows.append(
                {
                    "task": task_name,
                    "row_id": row["row_id"],
                    "label": labels[idx],
                    "family": row["T_e"]["relation_family"],
                    "predicate": row["T_e"]["predicate_label"],
                    "scores": {name: scores[idx] for name, scores in preds.items()},
                }
            )

    cases = []
    cases.extend(error_cases(a_rows, a_labels, task_a_preds["M5_compatibility_TG"], "M5_compatibility_TG"))
    cases.extend(error_cases(c_rows, c_labels, task_c_preds["M6_factorized_TZGQ"], "M6_factorized_TZGQ"))

    summary = {
        "schema_version": "h002_learned_smoke_v1_summary",
        "status": "h002_learned_smoke_v1_completed" if not errors else "h002_learned_smoke_v1_input_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_root": rel_path(input_root),
        "output_dir": rel_path(output_dir),
        "materialization_status": materialization_summary.get("status"),
        "counts": {
            "prototype_rows": len(rows),
            "task_a_rows": len(a_rows),
            "task_a_positive": sum(a_labels),
            "task_a_negative": len(a_labels) - sum(a_labels),
            "task_b_rows": len(b_rows),
            "task_b_observable": sum(b_labels),
            "task_b_not_observable": len(b_labels) - sum(b_labels),
            "task_c_rows": len(c_rows),
            "task_c_accept": sum(c_labels),
            "task_c_reject": len(c_labels) - sum(c_labels),
            "validation_errors": len(errors),
        },
        "training": {
            "folds": args.folds,
            "epochs": args.epochs,
            "lr": args.lr,
            "l2": args.l2,
            "implementation": "pure_python_logistic_regression_grouped_cv",
        },
        "gates": gates,
        "multiclass_two_head": multiclass,
        "boundary": {
            "split": "train_internal_grouped_folds",
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "trains_paper_model": False,
        },
        "next_todo": (
            "learned_smoke_v1_error_analysis"
            if gates["overall_interpretation"] == "learned_smoke_diagnostic_only_needs_error_analysis"
            else "attachment_numeric_geometry_materialization_v1"
        ),
    }

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "metrics_by_task.json", metrics_by_task)
    write_json(output_dir / "metrics_by_family.json", metrics_by_family)
    write_json(output_dir / "multiclass_two_head.json", multiclass)
    write_json(output_dir / "folds.json", {"task_a": task_a_folds, "task_b": task_b_folds, "task_c": task_c_folds})
    write_jsonl(output_dir / "predictions.jsonl", prediction_rows)
    write_jsonl(output_dir / "error_cases.jsonl", cases)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", summary, metrics_by_task, gates)
    return summary


def main() -> int:
    summary = run(parse_args())
    gate = summary["gates"]["gate_2_learned_compatibility_signal"]
    print(
        "status={status} task_a={task_a} compat_auc={compat_auc} source_auc={source_auc} "
        "shortcut_auc={shortcut_auc} gate2={gate2} validation_errors={errors} next={next}".format(
            status=summary["status"],
            task_a=summary["counts"]["task_a_rows"],
            compat_auc=gate["compatibility_TG_auc"],
            source_auc=gate["source_auc"],
            shortcut_auc=gate["predicate_family_shortcut_auc"],
            gate2=gate["pass"],
            errors=summary["counts"]["validation_errors"],
            next=summary["next_todo"],
        )
    )
    return 0 if summary["counts"]["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
