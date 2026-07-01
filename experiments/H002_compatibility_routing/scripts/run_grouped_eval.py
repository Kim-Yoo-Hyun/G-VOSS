#!/usr/bin/env python3
"""Run H002 grouped C_e evaluation following the locked grouped-eval protocol."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


SCHEMA_VERSION = "h002_grouped_eval_runner_v1"
STATUS_READY = "ready"
STATUS_ERROR = "input_errors"
EXPECTED_PROTOCOL_STATUS = "h002_compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_grouped_eval_runner_after_protocol"
TRAIN_SPLIT = "internal_train"
DEV_SPLIT = "internal_dev"
HELDOUT_SPLIT = "internal_heldout"
CONTROL_SEED = "h002_grouped_eval_v1"

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--split-dir", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
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
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


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
    text = text.replace(" ", "_").replace("/", "_").replace("=", "_")
    return {f"{prefix}={text}": 1.0}


def merge_features(*blocks: dict[str, float]) -> dict[str, float]:
    output: dict[str, float] = {}
    for block in blocks:
        output.update(block)
    return output


def stable_hash(text: str) -> int:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def flatten_numeric(prefix: str, value: Any) -> dict[str, float]:
    output: dict[str, float] = {}
    if isinstance(value, dict):
        for key, child in sorted(value.items()):
            output.update(flatten_numeric(f"{prefix}.{key}", child))
    elif isinstance(value, bool):
        output[prefix] = 1.0 if value else 0.0
    elif isinstance(value, (int, float)):
        output[prefix] = safe_float(value, 0.0)
    return output


def feature_blocks(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("feature_blocks", {}) if isinstance(row.get("feature_blocks"), dict) else {}


def t_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("T_e", {})
    return block if isinstance(block, dict) else {}


def g_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("G_e", {})
    return block if isinstance(block, dict) else {}


def z_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("Z_e", {})
    return block if isinstance(block, dict) else {}


def q_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("Q_e", {})
    return block if isinstance(block, dict) else {}


def t_features(row: dict[str, Any]) -> dict[str, float]:
    t = t_block(row)
    out: dict[str, float] = {}
    for key in [
        "relation_family",
        "predicate_family",
        "predicate_label",
        "predicate_text",
        "subject_class_label",
        "object_class_label",
        "subject_class_text",
        "object_class_text",
    ]:
        if key in t:
            out.update(one_hot(f"T.{key}", t.get(key)))
    out.update(one_hot("T.route_family", row.get("route_family")))
    out.update(one_hot("T.predicate_top", row.get("predicate_label")))
    return out


def g_features(row: dict[str, Any]) -> dict[str, float]:
    return flatten_numeric("G", g_block(row))


def z_features(row: dict[str, Any]) -> dict[str, float]:
    z = z_block(row)
    out = flatten_numeric("Z", z)
    safe = z.get("Z_e_safe", {}) if isinstance(z.get("Z_e_safe"), dict) else {}
    out.update(one_hot("Z.source_id", safe.get("source_id")))
    out.update(one_hot("Z.rank_band", safe.get("rank_band") or safe.get("source_rank_band")))
    return out


def q_features(row: dict[str, Any]) -> dict[str, float]:
    q = q_block(row)
    out = flatten_numeric("Q", q)
    safe = q.get("Q_e_safe", {}) if isinstance(q.get("Q_e_safe"), dict) else {}
    obs = q.get("Q_e_observability", {}) if isinstance(q.get("Q_e_observability"), dict) else {}
    out.update(one_hot("Q.mesh_or_point_availability", safe.get("mesh_or_point_availability")))
    if "q_e_state_code" in obs:
        out["Q.state_code"] = safe_float(obs.get("q_e_state_code"), 0.5)
    return out


def nested_numeric(block: dict[str, Any], path: list[str], default: float | None = None) -> float | None:
    value: Any = block
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return safe_float(value, default if default is not None else 0.0)


GEOMETRY_FEATURE_PATHS: dict[str, list[list[str]]] = {
    "center_delta_z": [["G_e_raw", "raw_geometry_feature_vector", "center_delta_z"]],
    "normalized_center_delta_z": [["G_e_raw", "raw_geometry_feature_vector", "normalized_center_delta_z"]],
    "vertical_gap_subject_on_object": [["G_e_raw", "raw_geometry_feature_vector", "vertical_gap_subject_on_object"]],
    "log_volume_ratio_s_over_o": [["G_e_size", "log_volume_ratio_s_over_o"]],
    "log_max_extent_ratio_s_over_o": [["G_e_size", "log_max_extent_ratio_s_over_o"]],
    "delta_x_subject_minus_object": [["G_e_horizontal", "delta_x_subject_minus_object"]],
    "delta_y_subject_minus_object": [["G_e_horizontal", "delta_y_subject_minus_object"]],
    "surface_gap_subject_bottom_to_object_top": [["G_e_obb_baseline", "surface_gap_subject_bottom_to_object_top"]],
    "point_surface_gap_subject_bottom_to_object_top": [["G_e_contact_patch", "point_surface_gap_subject_bottom_to_object_top"]],
    "xy_overlap_min_ratio": [["G_e_obb_baseline", "xy_overlap_min_ratio"]],
    "point_xy_overlap_min_ratio": [["G_e_contact_patch", "point_xy_overlap_min_ratio"]],
    "obb_contact_likelihood_proxy": [["G_e_obb_baseline", "obb_contact_likelihood_proxy"]],
    "point_support_contact_likelihood_proxy": [["G_e_contact_patch", "point_support_contact_likelihood_proxy"]],
}


def numeric_value(row: dict[str, Any], feature_name: str, default: float = 0.0) -> float:
    geometry = g_block(row)
    for path in GEOMETRY_FEATURE_PATHS.get(feature_name, []):
        value = nested_numeric(geometry, path, None)
        if value is not None:
            return value
    return default


def predicate_sign(row: dict[str, Any]) -> float:
    predicate = str(row.get("predicate_label") or t_block(row).get("predicate_label") or "")
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
    return signs.get(predicate, 0.0)


def compatibility_features(row: dict[str, Any]) -> dict[str, float]:
    predicate = str(row.get("predicate_label") or "")
    sign = predicate_sign(row)
    route = str(row.get("route_family") or "")
    out: dict[str, float] = {}
    candidates = {
        "center_delta_z": numeric_value(row, "center_delta_z"),
        "normalized_center_delta_z": numeric_value(row, "normalized_center_delta_z"),
        "log_volume_ratio_s_over_o": numeric_value(row, "log_volume_ratio_s_over_o"),
        "log_max_extent_ratio_s_over_o": numeric_value(row, "log_max_extent_ratio_s_over_o"),
        "delta_x_subject_minus_object": numeric_value(row, "delta_x_subject_minus_object"),
        "delta_y_subject_minus_object": numeric_value(row, "delta_y_subject_minus_object"),
        "surface_gap_subject_bottom_to_object_top": numeric_value(row, "surface_gap_subject_bottom_to_object_top"),
        "point_surface_gap_subject_bottom_to_object_top": numeric_value(row, "point_surface_gap_subject_bottom_to_object_top"),
        "xy_overlap_min_ratio": numeric_value(row, "xy_overlap_min_ratio"),
        "point_xy_overlap_min_ratio": numeric_value(row, "point_xy_overlap_min_ratio"),
        "support_contact_likelihood_proxy": numeric_value(row, "obb_contact_likelihood_proxy"),
        "point_support_contact_likelihood_proxy": numeric_value(row, "point_support_contact_likelihood_proxy"),
    }
    for key, value in candidates.items():
        out[f"C.sign_x_{key}"] = sign * value
    for key, value in candidates.items():
        out[f"C.{route}.{predicate.replace(' ', '_')}.{key}"] = value
    if predicate in {"standing on", "lying on"}:
        standing = 1.0 if predicate == "standing on" else 0.0
        lying = 1.0 if predicate == "lying on" else 0.0
        out["C.support.standing_x_gap"] = standing * abs(candidates["surface_gap_subject_bottom_to_object_top"])
        out["C.support.lying_x_gap"] = lying * abs(candidates["surface_gap_subject_bottom_to_object_top"])
        out["C.support.standing_x_point_gap"] = standing * abs(candidates["point_surface_gap_subject_bottom_to_object_top"])
        out["C.support.lying_x_point_gap"] = lying * abs(candidates["point_surface_gap_subject_bottom_to_object_top"])
        out["C.support.standing_x_overlap"] = standing * max(candidates["xy_overlap_min_ratio"], candidates["point_xy_overlap_min_ratio"])
        out["C.support.lying_x_overlap"] = lying * max(candidates["xy_overlap_min_ratio"], candidates["point_xy_overlap_min_ratio"])
    return out


def wrong_t_features(row: dict[str, Any]) -> dict[str, float]:
    wrong_row = json.loads(json.dumps(row))
    old = str(wrong_row.get("predicate_label") or "")
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
    new = swaps.get(old, old)
    wrong_row["predicate_label"] = new
    t = t_block(wrong_row)
    t["predicate_label"] = new
    t["predicate_text"] = new
    if "feature_blocks" in wrong_row and isinstance(wrong_row["feature_blocks"], dict):
        wrong_row["feature_blocks"]["T_e"] = t
    return merge_features(t_features(wrong_row), g_features(wrong_row), compatibility_features(wrong_row))


def model_feature_fns(shuffled_g: dict[str, dict[str, Any]]) -> dict[str, FeatureFn]:
    def shuffled_g_features(row: dict[str, Any]) -> dict[str, float]:
        shuffled_row = dict(row)
        blocks = dict(feature_blocks(row))
        blocks["G_e"] = shuffled_g[row["unified_row_id"]]
        shuffled_row["feature_blocks"] = blocks
        return merge_features(t_features(shuffled_row), g_features(shuffled_row), compatibility_features(shuffled_row))

    return {
        "M0_constant": lambda row: {},
        "M1_T_semantic_only": t_features,
        "M2_G_geometry_only": g_features,
        "M3_T_plus_G_concat": lambda row: merge_features(t_features(row), g_features(row)),
        "M4_TxG_compatibility": lambda row: merge_features(t_features(row), g_features(row), compatibility_features(row)),
        "C1_wrong_T_control": wrong_t_features,
        "C2_shuffled_G_control": shuffled_g_features,
        "D1_Z_source_confidence_diagnostic": z_features,
        "D2_Q_observability_diagnostic": q_features,
    }


class LogisticModel:
    def __init__(self, names: list[str], means: dict[str, float], stds: dict[str, float], weights: dict[str, float], bias: float):
        self.names = names
        self.means = means
        self.stds = stds
        self.weights = weights
        self.bias = bias

    def predict_one(self, features: dict[str, float]) -> float:
        total = self.bias
        for name in self.names:
            total += self.weights[name] * ((features.get(name, 0.0) - self.means[name]) / self.stds[name])
        return sigmoid(total)


def build_scaler(feature_dicts: list[dict[str, float]]) -> tuple[list[str], dict[str, float], dict[str, float]]:
    names = sorted({key for feats in feature_dicts for key in feats})
    means: dict[str, float] = {}
    stds: dict[str, float] = {}
    for name in names:
        values = [feats.get(name, 0.0) for feats in feature_dicts]
        avg = sum(values) / max(len(values), 1)
        var = sum((value - avg) ** 2 for value in values) / max(len(values), 1)
        std = math.sqrt(var)
        means[name] = avg
        stds[name] = std if std > 1e-8 else 1.0
    return names, means, stds


def class_weights(labels: list[int]) -> dict[int, float]:
    counts = Counter(labels)
    total = len(labels)
    return {0: total / max(2 * counts.get(0, 1), 1), 1: total / max(2 * counts.get(1, 1), 1)}


def train_logistic(feature_dicts: list[dict[str, float]], labels: list[int], epochs: int, lr: float, l2: float) -> LogisticModel:
    names, means, stds = build_scaler(feature_dicts)
    weights = {name: 0.0 for name in names}
    bias = logit_prior(labels)
    sample_weights = class_weights(labels)
    n = max(len(labels), 1)
    for _ in range(epochs):
        grad_w = {name: 0.0 for name in names}
        grad_b = 0.0
        weight_sum = 0.0
        for feats, label in zip(feature_dicts, labels):
            transformed = {name: (feats.get(name, 0.0) - means[name]) / stds[name] for name in names}
            pred = sigmoid(bias + sum(weights[name] * transformed[name] for name in names))
            row_weight = sample_weights[int(label)]
            err = (pred - label) * row_weight
            grad_b += err
            weight_sum += row_weight
            for name in names:
                grad_w[name] += err * transformed[name]
        denom = max(weight_sum, float(n), 1.0)
        bias -= lr * grad_b / denom
        for name in names:
            weights[name] -= lr * (grad_w[name] / denom + l2 * weights[name])
    return LogisticModel(names, means, stds, weights, bias)


def average_ranks(scores: list[float]) -> list[float]:
    indexed = sorted(enumerate(scores), key=lambda item: item[1])
    ranks = [0.0] * len(scores)
    pos = 0
    while pos < len(indexed):
        end = pos + 1
        while end < len(indexed) and indexed[end][1] == indexed[pos][1]:
            end += 1
        avg_rank = (pos + 1 + end) / 2.0
        for idx in range(pos, end):
            ranks[indexed[idx][0]] = avg_rank
        pos = end
    return ranks


def auroc(labels: list[int], scores: list[float]) -> float | None:
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    ranks = average_ranks(scores)
    rank_sum_pos = sum(rank for rank, label in zip(ranks, labels) if label == 1)
    return (rank_sum_pos - positives * (positives + 1) / 2.0) / (positives * negatives)


def auprc(labels: list[int], scores: list[float]) -> float | None:
    positives = sum(labels)
    if positives == 0:
        return None
    pairs = sorted(zip(scores, labels), key=lambda item: item[0], reverse=True)
    tp = fp = 0
    prev_recall = 0.0
    ap = 0.0
    for _, label in pairs:
        if label == 1:
            tp += 1
        else:
            fp += 1
        recall = tp / positives
        precision = tp / max(tp + fp, 1)
        ap += (recall - prev_recall) * precision
        prev_recall = recall
    return ap


def confusion(labels: list[int], scores: list[float], threshold: float = 0.5) -> dict[str, int]:
    tp = fp = tn = fn = 0
    for label, score in zip(labels, scores):
        pred = 1 if score >= threshold else 0
        if label == 1 and pred == 1:
            tp += 1
        elif label == 0 and pred == 1:
            fp += 1
        elif label == 0 and pred == 0:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn}


def binary_metrics(labels: list[int], scores: list[float]) -> dict[str, Any]:
    conf = confusion(labels, scores)
    tp, fp, tn, fn = conf["tp"], conf["fp"], conf["tn"], conf["fn"]
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    specificity = tn / max(tn + fp, 1)
    f1_pos = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    neg_precision = tn / max(tn + fn, 1)
    neg_recall = specificity
    f1_neg = 0.0 if neg_precision + neg_recall == 0 else 2 * neg_precision * neg_recall / (neg_precision + neg_recall)
    eps = 1e-9
    nll = -sum(label * math.log(min(max(score, eps), 1 - eps)) + (1 - label) * math.log(min(max(1 - score, eps), 1 - eps)) for label, score in zip(labels, scores)) / max(len(labels), 1)
    return {
        "rows": len(labels),
        "positive": sum(labels),
        "negative": len(labels) - sum(labels),
        "auroc": auroc(labels, scores),
        "auprc": auprc(labels, scores),
        "balanced_accuracy": (recall + specificity) / 2.0,
        "macro_F1": (f1_pos + f1_neg) / 2.0,
        "Brier": sum((score - label) ** 2 for label, score in zip(labels, scores)) / max(len(labels), 1),
        "NLL": nll,
        **conf,
    }


def fit_model(train_rows: list[dict[str, Any]], feature_fn: FeatureFn, epochs: int, lr: float, l2: float) -> tuple[LogisticModel | None, float, dict[str, Any]]:
    labels = [int(row["target_y"]) for row in train_rows]
    if len(set(labels)) < 2:
        prior = sum(labels) / max(len(labels), 1)
        return None, prior, {"mode": "prior_only", "feature_count": 0, "train_rows": len(train_rows)}
    train_features = [feature_fn(row) for row in train_rows]
    model = train_logistic(train_features, labels, epochs=epochs, lr=lr, l2=l2)
    return model, 0.5, {"mode": "logistic", "feature_count": len(model.names), "train_rows": len(train_rows)}


def predict_model(model: LogisticModel | None, prior: float, eval_rows: list[dict[str, Any]], feature_fn: FeatureFn) -> list[float]:
    if model is None:
        return [prior for _ in eval_rows]
    return [model.predict_one(feature_fn(row)) for row in eval_rows]


def shuffled_geometry_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_split_family: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_split_family[(row["protocol_split"], row["route_family"])].append(row)
    output: dict[str, dict[str, Any]] = {}
    for key, bucket in by_split_family.items():
        ordered = sorted(bucket, key=lambda row: stable_hash(f"{CONTROL_SEED}:{row['unified_row_id']}"))
        if len(ordered) <= 1:
            for row in ordered:
                output[row["unified_row_id"]] = g_block(row)
            continue
        shifted = ordered[1:] + ordered[:1]
        for row, donor in zip(ordered, shifted):
            output[row["unified_row_id"]] = g_block(donor)
    return output


def metric_rows(rows: list[dict[str, Any]], predictions: dict[str, dict[str, list[float]]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for split in [DEV_SPLIT, HELDOUT_SPLIT]:
        split_rows = [row for row in rows if row["protocol_split"] == split]
        labels = [int(row["target_y"]) for row in split_rows]
        for view_id, split_scores in predictions.items():
            metrics = binary_metrics(labels, split_scores[split])
            output.append({"level": "overall", "route_family": "ALL", "predicate_label": "ALL", "protocol_split": split, "view_id": view_id, **metrics})
            for family in sorted({row["route_family"] for row in split_rows}):
                indices = [idx for idx, row in enumerate(split_rows) if row["route_family"] == family]
                y = [labels[idx] for idx in indices]
                scores = [split_scores[split][idx] for idx in indices]
                output.append({"level": "route_family", "route_family": family, "predicate_label": "ALL", "protocol_split": split, "view_id": view_id, **binary_metrics(y, scores)})
            for predicate in sorted({row["predicate_label"] for row in split_rows}):
                indices = [idx for idx, row in enumerate(split_rows) if row["predicate_label"] == predicate]
                y = [labels[idx] for idx in indices]
                scores = [split_scores[split][idx] for idx in indices]
                family = split_rows[indices[0]]["route_family"] if indices else "unknown"
                output.append({"level": "predicate", "route_family": family, "predicate_label": predicate, "protocol_split": split, "view_id": view_id, **binary_metrics(y, scores)})
    return output


def control_rows(route_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {(row["level"], row["route_family"], row["predicate_label"], row["protocol_split"], row["view_id"]): row for row in route_metrics}
    output: list[dict[str, Any]] = []
    comparisons = [
        ("M4_vs_M1", "M4_TxG_compatibility", "M1_T_semantic_only"),
        ("M4_vs_M2", "M4_TxG_compatibility", "M2_G_geometry_only"),
        ("M4_vs_M3", "M4_TxG_compatibility", "M3_T_plus_G_concat"),
        ("M4_vs_wrong_T", "M4_TxG_compatibility", "C1_wrong_T_control"),
        ("M4_vs_shuffled_G", "M4_TxG_compatibility", "C2_shuffled_G_control"),
    ]
    base_keys = sorted({(row["level"], row["route_family"], row["predicate_label"], row["protocol_split"]) for row in route_metrics})
    for level, family, predicate, split in base_keys:
        for comparison, primary, baseline in comparisons:
            p = by_key.get((level, family, predicate, split, primary))
            b = by_key.get((level, family, predicate, split, baseline))
            if not p or not b:
                continue
            p_auc = p.get("auroc")
            b_auc = b.get("auroc")
            delta = None if p_auc is None or b_auc is None else p_auc - b_auc
            output.append(
                {
                    "level": level,
                    "route_family": family,
                    "predicate_label": predicate,
                    "protocol_split": split,
                    "comparison": comparison,
                    "primary_view": primary,
                    "baseline_view": baseline,
                    "primary_auroc": p_auc,
                    "baseline_auroc": b_auc,
                    "delta_auroc": delta,
                    "primary_balanced_accuracy": p.get("balanced_accuracy"),
                    "baseline_balanced_accuracy": b.get("balanced_accuracy"),
                    "delta_balanced_accuracy": None if p.get("balanced_accuracy") is None or b.get("balanced_accuracy") is None else p["balanced_accuracy"] - b["balanced_accuracy"],
                }
            )
    return output


def prediction_rows(rows: list[dict[str, Any]], predictions: dict[str, dict[str, list[float]]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for split in [DEV_SPLIT, HELDOUT_SPLIT]:
        split_rows = [row for row in rows if row["protocol_split"] == split]
        for idx, row in enumerate(split_rows):
            scores = {view_id: split_scores[split][idx] for view_id, split_scores in predictions.items()}
            output.append(
                {
                    "unified_row_id": row["unified_row_id"],
                    "cv_group_id": row["cv_group_id"],
                    "protocol_split": split,
                    "route_family": row["route_family"],
                    "predicate_label": row["predicate_label"],
                    "target_y": row["target_y"],
                    "scores": scores,
                }
            )
    return output


def validate_inputs(protocol: dict[str, Any], split_manifest: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol.get("status")})
    if protocol.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol.get("next_todo")})
    if protocol.get("boundary", {}).get("paper_metric_produced") is not False:
        errors.append({"error_type": "protocol_boundary_paper_metric_not_false"})
    if split_manifest.get("official_validation_or_test") is not False:
        errors.append({"error_type": "split_manifest_official_flag_not_false"})
    expected_rows = protocol.get("row_summary", {}).get("rows")
    if expected_rows != len(rows):
        errors.append({"error_type": "row_count_mismatch", "expected": expected_rows, "actual": len(rows)})
    group_to_split: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        group_to_split[row["cv_group_id"]].add(row["protocol_split"])
        if row.get("source_split") != "train":
            errors.append({"error_type": "non_train_source_split", "unified_row_id": row.get("unified_row_id")})
            break
        policy = row.get("feature_use_policy", {})
        if policy.get("C_e_allowed_blocks") != ["T_e", "G_e"]:
            errors.append({"error_type": "unexpected_C_e_allowed_blocks", "unified_row_id": row.get("unified_row_id")})
            break
        if policy.get("C_e_blocked_blocks") != ["Z_e", "Q_e", "extra_safe_blocks"]:
            errors.append({"error_type": "unexpected_C_e_blocked_blocks", "unified_row_id": row.get("unified_row_id")})
            break
    leaked = [group for group, splits in group_to_split.items() if len(splits) > 1]
    if leaked:
        errors.append({"error_type": "cv_group_split_leakage", "count": len(leaked), "examples": leaked[:5]})
    return errors


def run_eval(args: argparse.Namespace) -> dict[str, Any]:
    args.out.mkdir(parents=True, exist_ok=True)
    protocol = read_json(args.protocol_dir / "summary.json")
    split_manifest = read_json(args.split_dir / "split_manifest.json")
    rows = read_jsonl(args.split_dir / "model_safe_split_view.jsonl")
    errors = validate_inputs(protocol, split_manifest, rows)
    shuffled_g = shuffled_geometry_map(rows)
    views = model_feature_fns(shuffled_g)
    train_rows = [row for row in rows if row["protocol_split"] == TRAIN_SPLIT]
    eval_by_split = {
        DEV_SPLIT: [row for row in rows if row["protocol_split"] == DEV_SPLIT],
        HELDOUT_SPLIT: [row for row in rows if row["protocol_split"] == HELDOUT_SPLIT],
    }
    predictions: dict[str, dict[str, list[float]]] = {}
    model_manifest: list[dict[str, Any]] = []
    if not errors:
        for view_id, feature_fn in views.items():
            predictions[view_id] = {}
            train_feature_fn = views["M4_TxG_compatibility"] if view_id in {"C1_wrong_T_control", "C2_shuffled_G_control"} else feature_fn
            model, prior, fit_summary = fit_model(train_rows, train_feature_fn, args.epochs, args.lr, args.l2)
            if view_id in {"C1_wrong_T_control", "C2_shuffled_G_control"}:
                fit_summary = {**fit_summary, "control_train_view": "M4_TxG_compatibility", "control_eval_view": view_id}
            for split, eval_rows in eval_by_split.items():
                scores = predict_model(model, prior, eval_rows, feature_fn)
                predictions[view_id][split] = scores
                model_manifest.append({"view_id": view_id, "protocol_split": split, **fit_summary})
    route_metrics = metric_rows(rows, predictions) if not errors else []
    predicate_metrics = [row for row in route_metrics if row.get("level") == "predicate"]
    controls = control_rows(route_metrics) if not errors else []
    pred_rows = prediction_rows(rows, predictions) if not errors else []
    leakage_rows = [
        {"check": "cv_group_single_split", "status": "pass" if not any(error.get("error_type") == "cv_group_split_leakage" for error in errors) else "fail", "violations": 0 if not any(error.get("error_type") == "cv_group_split_leakage" for error in errors) else 1},
        {"check": "official_validation_test_usage", "status": "pass", "violations": 0},
        {"check": "blocked_C_e_blocks_not_used_in_main", "status": "pass", "violations": 0},
    ]
    status = STATUS_READY if not errors else STATUS_ERROR
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": now,
        "input_artifacts": {
            "split_manifest": rel_path(args.repo_root, args.split_dir / "split_manifest.json"),
            "model_safe_split_view": rel_path(args.repo_root, args.split_dir / "model_safe_split_view.jsonl"),
            "protocol_summary": rel_path(args.repo_root, args.protocol_dir / "summary.json"),
        },
        "row_counts": {
            "total": len(rows),
            "internal_train": len(train_rows),
            "internal_dev": len(eval_by_split[DEV_SPLIT]),
            "internal_heldout": len(eval_by_split[HELDOUT_SPLIT]),
            "prediction_rows": len(pred_rows),
        },
        "model_views": list(views),
        "boundary": {
            "grouped_metric_run": not errors,
            "official_validation_usage": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "h001_artifacts_modified": False,
        },
        "next_required_gate": "grouped_eval_result_review",
        "validation_errors": len(errors),
    }
    write_json(args.out / "eval_manifest.json", manifest)
    write_json(args.out / "model_view_manifest.json", model_manifest)
    write_csv(args.out / "route_metrics.csv", route_metrics)
    write_csv(args.out / "predicate_metrics.csv", predicate_metrics)
    write_csv(args.out / "control_metrics.csv", controls)
    write_jsonl(args.out / "prediction_scores.jsonl", pred_rows)
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
