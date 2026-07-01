#!/usr/bin/env python3
"""Run train-only grouped-CV smoke for size-relative compatibility."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from learned_smoke_runner_v1 import (
    binary_metrics,
    make_folds,
    merge_features,
    one_hot,
    rel_path,
    safe_float,
    train_logistic,
    write_json,
    write_jsonl,
)


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_plan_after_schema_audit_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan"
EXPECTED_ROW_SCHEMA = "h002_size_relative_runner_ready_view_v1"
EXPECTED_BLOCKS = {"G_e_size", "T_e"}

SCHEMA_VERSION = "h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan_v1"
STATUS_ERRORS = "h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan_input_errors"
STATUS_PASSED = "h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan_passed_controls"
STATUS_CONCAT_CAVEAT = "h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan_passed_but_concat_solves"
STATUS_DIAGNOSTIC = "h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan_diagnostic_only_failed_controls"

NEXT_TODO_PASSED = "compatibility_dataset_v3_size_relative_smoke_result_review_after_runner"
NEXT_TODO_DIAGNOSTIC = "compatibility_dataset_v3_size_relative_smoke_failure_analysis_after_runner"

PRIMARY_MODEL = "M4_TG_size_interaction"
NEAR_CHANCE_AUROC_MAX = 0.60
PRIMARY_AUROC_MIN = 0.95
PRIMARY_GAIN_OVER_SINGLE_FACTOR_MIN = 0.30
CONCAT_AUROC_CAVEAT_MIN = 0.90
CONTROL_AUROC_MAX = 0.60
PAIRED_SCORE_MARGIN_PASS_RATE_MIN = 0.90

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]

FORBIDDEN_FEATURE_TOKENS = {
    "anchor",
    "candidate_component",
    "class",
    "construction",
    "direction_by",
    "directed_pair",
    "gt_",
    "object_id",
    "scan_id",
    "source",
    "subgraph",
    "subject_id",
    "volume_ratio_band",
    "z_e",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=160)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def block(row: dict[str, Any], name: str) -> dict[str, Any]:
    return dict(row.get("feature_blocks", {}).get(name, {}))


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        normalized.append(
            {
                "G_e_size": block(row, "G_e_size"),
                "T_e": block(row, "T_e"),
                "group_id": str(row.get("cv_group_id")),
                "row_id": str(row.get("example_id") or row.get("row_id")),
                "schema_version": row.get("schema_version"),
                "split": row.get("split"),
                "y_compatibility": int(row.get("target_y")),
            }
        )
    return normalized


def t_features_from_dict(t: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    out.update(one_hot("T.family", t.get("relation_family")))
    out.update(one_hot("T.predicate", t.get("predicate_label")))
    return out


def t_features(row: dict[str, Any]) -> dict[str, float]:
    return t_features_from_dict(row.get("T_e", {}))


def predicate_only_features(row: dict[str, Any]) -> dict[str, float]:
    return one_hot("T.predicate", row.get("T_e", {}).get("predicate_label"))


def g_features_from_dict(g: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, value in sorted(g.items()):
        out[f"G.{key}"] = safe_float(value, 0.0)
    return out


def g_features(row: dict[str, Any]) -> dict[str, float]:
    return g_features_from_dict(row.get("G_e_size", {}))


def geometry_exact_tuple_features(row: dict[str, Any]) -> dict[str, float]:
    g = row.get("G_e_size", {})
    key = "|".join(f"{name}={safe_float(value, 0.0):.8f}" for name, value in sorted(g.items()))
    return one_hot("G_tuple", key)


def geometry_exact_tuple_key(row: dict[str, Any]) -> str:
    g = row.get("G_e_size", {})
    return "|".join(f"{name}={safe_float(value, 0.0):.8f}" for name, value in sorted(g.items()))


def expected_size_sign(predicate: Any) -> float:
    if predicate == "bigger than":
        return 1.0
    if predicate == "smaller than":
        return -1.0
    return 0.0


def compatibility_interactions_from_dict(t: dict[str, Any], g: dict[str, Any]) -> dict[str, float]:
    sign = expected_size_sign(t.get("predicate_label"))
    out: dict[str, float] = {"C.expected_size_sign": sign}
    for key, value in sorted(g.items()):
        clean_key = str(key).replace(".", "_")
        val = safe_float(value, 0.0)
        out[f"C.sign_x_{clean_key}"] = sign * val
        out[f"C.abs_{clean_key}"] = abs(val)
    volume = safe_float(g.get("log_volume_ratio_s_over_o"), 0.0)
    footprint = safe_float(g.get("log_footprint_area_ratio_s_over_o"), 0.0)
    max_extent = safe_float(g.get("log_max_extent_ratio_s_over_o"), 0.0)
    vertical_extent = safe_float(g.get("log_vertical_extent_ratio_s_over_o"), 0.0)
    out["C.sign_x_mean_size_ratio"] = sign * ((volume + footprint + max_extent + vertical_extent) / 4.0)
    out["C.sign_x_volume_minus_footprint"] = sign * (volume - footprint)
    return out


def compatibility_interaction_features(row: dict[str, Any]) -> dict[str, float]:
    return compatibility_interactions_from_dict(row.get("T_e", {}), row.get("G_e_size", {}))


def tg_concat_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), g_features(row))


def tg_interaction_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), g_features(row), compatibility_interaction_features(row))


def wrong_predicate(value: Any) -> str:
    if value == "bigger than":
        return "smaller than"
    if value == "smaller than":
        return "bigger than"
    return f"wrong_{value}"


def wrong_t(row: dict[str, Any]) -> dict[str, Any]:
    t = dict(row.get("T_e", {}))
    t["predicate_label"] = wrong_predicate(t.get("predicate_label"))
    t["predicate_text"] = t["predicate_label"]
    return t


def wrong_t_same_g_features(row: dict[str, Any]) -> dict[str, float]:
    t = wrong_t(row)
    g = row.get("G_e_size", {})
    return merge_features(t_features_from_dict(t), g_features_from_dict(g), compatibility_interactions_from_dict(t, g))


def sign_flipped_g(row: dict[str, Any]) -> dict[str, Any]:
    return {key: -safe_float(value, 0.0) for key, value in row.get("G_e_size", {}).items()}


def sign_flipped_g_features(row: dict[str, Any]) -> dict[str, float]:
    t = row.get("T_e", {})
    g = sign_flipped_g(row)
    return merge_features(t_features(row), g_features_from_dict(g), compatibility_interactions_from_dict(t, g))


def stable_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(row.get("row_id")))


def shifted_geometry_map(rows: list[dict[str, Any]], group_fn: Callable[[dict[str, Any]], str] | None = None) -> dict[str, dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if group_fn is None:
        groups["__all__"] = list(rows)
    else:
        for row in rows:
            groups[group_fn(row)].append(row)

    out: dict[str, dict[str, Any]] = {}
    for group_rows in groups.values():
        ordered = stable_order(group_rows)
        if len(ordered) <= 1:
            for row in ordered:
                out[str(row["row_id"])] = dict(row.get("G_e_size", {}))
            continue
        shift = max(1, len(ordered) // 2 + 1)
        for idx, row in enumerate(ordered):
            donor = ordered[(idx + shift) % len(ordered)]
            if donor.get("group_id") == row.get("group_id"):
                donor = ordered[(idx + shift + 1) % len(ordered)]
            out[str(row["row_id"])] = dict(donor.get("G_e_size", {}))
    return out


def shuffled_tg_interaction_features(row: dict[str, Any], geometry_map: dict[str, dict[str, Any]]) -> dict[str, float]:
    t = row.get("T_e", {})
    g = geometry_map[str(row["row_id"])]
    return merge_features(t_features(row), g_features_from_dict(g), compatibility_interactions_from_dict(t, g))


def model_feature_fns(rows: list[dict[str, Any]]) -> dict[str, tuple[FeatureFn, FeatureFn]]:
    global_g = shifted_geometry_map(rows)
    within_predicate_g = shifted_geometry_map(rows, lambda row: str(row.get("T_e", {}).get("predicate_label")))
    primary = tg_interaction_features
    return {
        "M0_intercept": (lambda row: {}, lambda row: {}),
        "M1_semantic_only_T": (t_features, t_features),
        "M2_geometry_only_G_size": (g_features, g_features),
        "M3_TG_concat_no_interaction": (tg_concat_features, tg_concat_features),
        PRIMARY_MODEL: (primary, primary),
        "S1_predicate_label_shortcut": (predicate_only_features, predicate_only_features),
        "C1_wrong_T_same_G": (primary, wrong_t_same_g_features),
        "C2_shuffled_G_global": (primary, lambda row: shuffled_tg_interaction_features(row, global_g)),
        "C3_shuffled_G_within_predicate": (primary, lambda row: shuffled_tg_interaction_features(row, within_predicate_g)),
        "C4_sign_flipped_G_control": (primary, sign_flipped_g_features),
    }


def labels(rows: list[dict[str, Any]]) -> list[int]:
    return [int(row["y_compatibility"]) for row in rows]


def balanced_accuracy(y: list[int], scores: list[float]) -> float:
    tp = fp = tn = fn = 0
    for label, score in zip(y, scores):
        pred = 1 if score >= 0.5 else 0
        if label == 1 and pred == 1:
            tp += 1
        elif label == 1 and pred == 0:
            fn += 1
        elif label == 0 and pred == 0:
            tn += 1
        else:
            fp += 1
    tpr = tp / max(tp + fn, 1)
    tnr = tn / max(tn + fp, 1)
    return (tpr + tnr) / 2.0


def ece(y: list[int], scores: list[float], bins: int = 10) -> float:
    total = len(y)
    if total == 0:
        return 0.0
    err = 0.0
    for bin_idx in range(bins):
        lo = bin_idx / bins
        hi = (bin_idx + 1) / bins
        indices = [
            idx
            for idx, score in enumerate(scores)
            if (lo <= score < hi) or (bin_idx == bins - 1 and lo <= score <= hi)
        ]
        if not indices:
            continue
        conf = sum(scores[idx] for idx in indices) / len(indices)
        acc = sum(1 for idx in indices if (scores[idx] >= 0.5) == bool(y[idx])) / len(indices)
        err += (len(indices) / total) * abs(acc - conf)
    return err


def augment_binary_metrics(y: list[int], scores: list[float]) -> dict[str, Any]:
    metrics = binary_metrics(y, scores)
    metrics["balanced_accuracy_at_0_5"] = balanced_accuracy(y, scores)
    metrics["ece_10"] = ece(y, scores)
    return metrics


def train_eval_cv_dual(
    rows: list[dict[str, Any]],
    y: list[int],
    train_feature_fn: FeatureFn,
    eval_feature_fn: FeatureFn,
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> dict[str, Any]:
    folds = make_folds(rows, "task_a", fold_count)
    predictions = [0.5] * len(rows)
    fold_summaries: list[dict[str, Any]] = []
    for fold_idx, test_indices in enumerate(folds):
        test_set = set(test_indices)
        train_indices = [idx for idx in range(len(rows)) if idx not in test_set]
        y_train = [y[idx] for idx in train_indices]
        y_test = [y[idx] for idx in test_indices]
        if len(set(y_train)) < 2:
            prior = sum(y_train) / max(len(y_train), 1)
            for idx in test_indices:
                predictions[idx] = prior
            fold_summaries.append({"fold": fold_idx, "mode": "prior_only", "test_rows": len(test_indices), "train_rows": len(train_indices)})
            continue
        train_feats = [train_feature_fn(rows[idx]) for idx in train_indices]
        model = train_logistic(train_feats, y_train, epochs=epochs, lr=lr, l2=l2)
        for idx in test_indices:
            predictions[idx] = model.predict_one(eval_feature_fn(rows[idx]))
        fold_summaries.append(
            {
                "feature_count": len(model.feature_names),
                "fold": fold_idx,
                "mode": "logistic",
                "test_positive": sum(y_test),
                "test_rows": len(test_indices),
                "train_positive": sum(y_train),
                "train_rows": len(train_indices),
            }
        )
    return {"folds": fold_summaries, "metrics": augment_binary_metrics(y, predictions), "predictions": predictions}


def eval_exact_tuple_shortcut(rows: list[dict[str, Any]], y: list[int], fold_count: int) -> dict[str, Any]:
    folds = make_folds(rows, "task_a", fold_count)
    predictions = [0.5] * len(rows)
    fold_summaries: list[dict[str, Any]] = []
    for fold_idx, test_indices in enumerate(folds):
        test_set = set(test_indices)
        train_indices = [idx for idx in range(len(rows)) if idx not in test_set]
        prior = sum(y[idx] for idx in train_indices) / max(len(train_indices), 1)
        by_key: dict[str, list[int]] = defaultdict(list)
        for idx in train_indices:
            by_key[geometry_exact_tuple_key(rows[idx])].append(y[idx])
        prevalences = {key: sum(vals) / len(vals) for key, vals in by_key.items()}
        for idx in test_indices:
            predictions[idx] = prevalences.get(geometry_exact_tuple_key(rows[idx]), prior)
        fold_summaries.append(
            {
                "fold": fold_idx,
                "mode": "categorical_majority_cv",
                "seen_tuple_count": len(prevalences),
                "test_rows": len(test_indices),
                "train_rows": len(train_indices),
            }
        )
    return {"folds": fold_summaries, "metrics": augment_binary_metrics(y, predictions), "predictions": predictions}


def eval_models(rows: list[dict[str, Any]], fold_count: int, epochs: int, lr: float, l2: float) -> tuple[dict[str, Any], dict[str, list[float]], dict[str, Any]]:
    y = labels(rows)
    metrics: dict[str, Any] = {}
    predictions: dict[str, list[float]] = {}
    folds: dict[str, Any] = {}
    for name, (train_fn, eval_fn) in model_feature_fns(rows).items():
        result = train_eval_cv_dual(rows, y, train_fn, eval_fn, fold_count, epochs, lr, l2)
        metrics[name] = result["metrics"]
        predictions[name] = result["predictions"]
        folds[name] = result["folds"]
    result = eval_exact_tuple_shortcut(rows, y, fold_count)
    metrics["S2_geometry_exact_tuple_shortcut"] = result["metrics"]
    predictions["S2_geometry_exact_tuple_shortcut"] = result["predictions"]
    folds["S2_geometry_exact_tuple_shortcut"] = result["folds"]
    return metrics, predictions, folds


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    y = labels(rows)
    groups: dict[str, list[int]] = defaultdict(list)
    predicate_counts: Counter[str] = Counter()
    predicate_label_counts: Counter[str] = Counter()
    for row, label in zip(rows, y):
        groups[str(row.get("group_id"))].append(label)
        predicate = str(row.get("T_e", {}).get("predicate_label"))
        predicate_counts[predicate] += 1
        predicate_label_counts[f"{predicate}|{'positive' if label else 'negative'}"] += 1
    return {
        "groups": len(groups),
        "negative": len(y) - sum(y),
        "paired_groups_with_one_positive_one_negative": sum(1 for vals in groups.values() if sorted(vals) == [0, 1]),
        "positive": sum(y),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "predicate_label_counts": dict(sorted(predicate_label_counts.items())),
        "rows": len(rows),
        "two_row_groups": sum(1 for vals in groups.values() if len(vals) == 2),
    }


def validate(
    plan_dir: Path,
    plan_summary: dict[str, Any],
    plan: dict[str, Any],
    manifest: dict[str, Any],
    raw_rows: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan_summary.get("next_todo")})
    if int(plan_summary.get("validation_errors", -1)) != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan_summary.get("validation_errors")})
    if (plan_dir / "validation_errors.jsonl").exists() and (plan_dir / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "plan_validation_errors_nonempty"})

    input_path = resolve_repo_path(plan["input_contract"]["input_file"])
    input_sha = sha256_file(input_path)
    if input_sha != plan["input_contract"]["input_sha256"]:
        errors.append({"error_type": "input_sha256_mismatch", "path": str(input_path)})
    if input_sha != manifest.get("input_sha256"):
        errors.append({"error_type": "manifest_input_sha256_mismatch", "path": str(input_path)})

    counts = count_summary(rows)
    if counts["rows"] != 2400 or counts["positive"] != 1200 or counts["negative"] != 1200:
        errors.append({"error_type": "unexpected_counts", **counts})
    if counts["groups"] != 1200 or counts["two_row_groups"] != 1200 or counts["paired_groups_with_one_positive_one_negative"] != 1200:
        errors.append({"error_type": "unexpected_group_profile", **counts})
    if counts["predicate_counts"] != {"bigger than": 1200, "smaller than": 1200}:
        errors.append({"error_type": "unexpected_predicate_counts", **counts})

    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw, row in zip(raw_rows, rows):
        row_id = row.get("row_id")
        if raw.get("schema_version") != EXPECTED_ROW_SCHEMA:
            errors.append({"error_type": "unexpected_row_schema", "row_id": row_id, "actual": raw.get("schema_version")})
        if set(raw.get("feature_blocks", {})) != EXPECTED_BLOCKS:
            errors.append({"error_type": "unexpected_feature_blocks", "row_id": row_id, "blocks": sorted(raw.get("feature_blocks", {}))})
        feature_text = json.dumps(raw.get("feature_blocks", {}), ensure_ascii=False).lower()
        for token in FORBIDDEN_FEATURE_TOKENS:
            if token in feature_text:
                errors.append({"error_type": "forbidden_feature_token", "row_id": row_id, "token": token})
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_id": row_id})
        by_group[str(row.get("group_id"))].append(row)

    for group_id, group_rows in by_group.items():
        if len(group_rows) != 2:
            errors.append({"error_type": "group_size_not_two", "group_id": group_id, "size": len(group_rows)})
            continue
        if sorted(row["y_compatibility"] for row in group_rows) != [0, 1]:
            errors.append({"error_type": "group_not_one_pos_one_neg", "group_id": group_id})
        predicates = sorted(str(row.get("T_e", {}).get("predicate_label")) for row in group_rows)
        if predicates != ["bigger than", "smaller than"]:
            errors.append({"error_type": "group_predicates_not_bigger_smaller", "group_id": group_id, "predicates": predicates})
        g_values = {json.dumps(row.get("G_e_size", {}), sort_keys=True) for row in group_rows}
        if len(g_values) != 1:
            errors.append({"error_type": "group_geometry_not_identical", "group_id": group_id})
    return errors


def value_or_zero(metrics: dict[str, Any], name: str) -> float:
    value = metrics.get(name, {}).get("auroc")
    return 0.0 if value is None else float(value)


def paired_margins(rows: list[dict[str, Any]], predictions: dict[str, list[float]]) -> dict[str, Any]:
    group_indices: dict[str, list[int]] = defaultdict(list)
    y = labels(rows)
    for idx, row in enumerate(rows):
        group_indices[str(row.get("group_id"))].append(idx)
    output: dict[str, Any] = {}
    for model_name, scores in predictions.items():
        margins: list[float] = []
        for indices in group_indices.values():
            pos = [idx for idx in indices if y[idx] == 1]
            neg = [idx for idx in indices if y[idx] == 0]
            for pos_idx in pos:
                for neg_idx in neg:
                    margins.append(scores[pos_idx] - scores[neg_idx])
        output[model_name] = {
            "contrast_pairs": len(margins),
            "max_positive_minus_negative": round(max(margins), 6) if margins else None,
            "mean_positive_minus_negative": round(mean(margins), 6) if margins else None,
            "min_positive_minus_negative": round(min(margins), 6) if margins else None,
            "positive_margin_fraction": round(sum(1 for value in margins if value > 0.0) / len(margins), 6) if margins else None,
        }
    return output


def gate_summary(metrics: dict[str, Any], margins: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    m1 = value_or_zero(metrics, "M1_semantic_only_T")
    m2 = value_or_zero(metrics, "M2_geometry_only_G_size")
    m3 = value_or_zero(metrics, "M3_TG_concat_no_interaction")
    m4 = value_or_zero(metrics, PRIMARY_MODEL)
    s1 = value_or_zero(metrics, "S1_predicate_label_shortcut")
    s2 = value_or_zero(metrics, "S2_geometry_exact_tuple_shortcut")
    c1 = value_or_zero(metrics, "C1_wrong_T_same_G")
    c2 = value_or_zero(metrics, "C2_shuffled_G_global")
    c3 = value_or_zero(metrics, "C3_shuffled_G_within_predicate")
    c4 = value_or_zero(metrics, "C4_sign_flipped_G_control")
    single_factor_best = max(m1, m2, s1, s2)
    best_shuffle = max(c2, c3)
    primary_margin = margins.get(PRIMARY_MODEL, {})
    margin_fraction = primary_margin.get("positive_margin_fraction") or 0.0
    mean_margin = primary_margin.get("mean_positive_minus_negative") or 0.0

    gate_data = len(errors) == 0
    gate_single_factor = single_factor_best <= NEAR_CHANCE_AUROC_MAX
    gate_primary = m4 >= PRIMARY_AUROC_MIN
    gate_gain = (m4 - single_factor_best) >= PRIMARY_GAIN_OVER_SINGLE_FACTOR_MIN
    gate_wrong_t = c1 <= CONTROL_AUROC_MAX
    gate_shuffle = best_shuffle <= CONTROL_AUROC_MAX
    gate_sign_flip = c4 <= CONTROL_AUROC_MAX
    gate_margin = mean_margin > 0.0 and margin_fraction >= PAIRED_SCORE_MARGIN_PASS_RATE_MIN
    concat_caveat = m3 >= CONCAT_AUROC_CAVEAT_MIN
    overall = gate_data and gate_single_factor and gate_primary and gate_gain and gate_wrong_t and gate_shuffle and gate_sign_flip and gate_margin

    return {
        "gate_data_integrity": {"pass": gate_data, "validation_errors": len(errors)},
        "gate_single_factor_shortcuts_near_chance": {
            "pass": gate_single_factor,
            "max_allowed": NEAR_CHANCE_AUROC_MAX,
            "auroc": {
                "M1_semantic_only_T": m1,
                "M2_geometry_only_G_size": m2,
                "S1_predicate_label_shortcut": s1,
                "S2_geometry_exact_tuple_shortcut": s2,
            },
        },
        "gate_primary_interaction_signal": {"pass": gate_primary, PRIMARY_MODEL: m4, "min_required": PRIMARY_AUROC_MIN},
        "gate_primary_gain_over_single_factor": {
            "pass": gate_gain,
            PRIMARY_MODEL: m4,
            "single_factor_best": single_factor_best,
            "required_gain": PRIMARY_GAIN_OVER_SINGLE_FACTOR_MIN,
            "actual_gain": m4 - single_factor_best,
        },
        "gate_plain_concat_boundary": {
            "M3_TG_concat_no_interaction": m3,
            "concat_caveat": concat_caveat,
            "interpretation": "If true, explicit interaction is less necessary for this family than expected.",
        },
        "gate_wrong_T_same_G_degradation": {"pass": gate_wrong_t, "C1_wrong_T_same_G": c1, "max_allowed": CONTROL_AUROC_MAX},
        "gate_shuffled_G_degradation": {
            "pass": gate_shuffle,
            "C2_shuffled_G_global": c2,
            "C3_shuffled_G_within_predicate": c3,
            "best_shuffle": best_shuffle,
            "max_allowed": CONTROL_AUROC_MAX,
        },
        "gate_sign_flipped_G_control": {"pass": gate_sign_flip, "C4_sign_flipped_G_control": c4, "max_allowed": CONTROL_AUROC_MAX},
        "gate_paired_score_margin": {
            "pass": gate_margin,
            "mean_positive_minus_negative": mean_margin,
            "positive_margin_fraction": margin_fraction,
            "min_required_fraction": PAIRED_SCORE_MARGIN_PASS_RATE_MIN,
        },
        "overall_pass": overall,
        "overall_interpretation": (
            "size_relative_smoke_passed_but_concat_solves"
            if overall and concat_caveat
            else "size_relative_smoke_passed_controls"
            if overall
            else "size_relative_smoke_diagnostic_only_failed_controls"
        ),
    }


def prediction_rows(rows: list[dict[str, Any]], predictions: dict[str, list[float]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        item = {
            "row_id": row.get("row_id"),
            "group_id": row.get("group_id"),
            "label": row.get("y_compatibility"),
            "predicate": row.get("T_e", {}).get("predicate_label"),
            "log_volume_ratio_s_over_o": row.get("G_e_size", {}).get("log_volume_ratio_s_over_o"),
            "log_footprint_area_ratio_s_over_o": row.get("G_e_size", {}).get("log_footprint_area_ratio_s_over_o"),
            "log_max_extent_ratio_s_over_o": row.get("G_e_size", {}).get("log_max_extent_ratio_s_over_o"),
            "log_vertical_extent_ratio_s_over_o": row.get("G_e_size", {}).get("log_vertical_extent_ratio_s_over_o"),
        }
        for model, scores in predictions.items():
            item[model] = scores[idx]
        output.append(item)
    return output


def error_cases(rows: list[dict[str, Any]], scores: list[float], max_cases: int = 30) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for row, score in zip(rows, scores):
        label = int(row["y_compatibility"])
        pred = 1 if score >= 0.5 else 0
        if pred == label:
            continue
        cases.append(
            {
                "row_id": row.get("row_id"),
                "group_id": row.get("group_id"),
                "predicate": row.get("T_e", {}).get("predicate_label"),
                "label": label,
                "prediction": pred,
                "score": round(score, 6),
                "G_e_size": row.get("G_e_size", {}),
            }
        )
    return sorted(cases, key=lambda item: abs(float(item["score"]) - 0.5), reverse=True)[:max_cases]


def write_report(path: Path, summary: dict[str, Any], metrics: dict[str, Any], gates: dict[str, Any]) -> None:
    order = [
        "M0_intercept",
        "M1_semantic_only_T",
        "M2_geometry_only_G_size",
        "M3_TG_concat_no_interaction",
        PRIMARY_MODEL,
        "S1_predicate_label_shortcut",
        "S2_geometry_exact_tuple_shortcut",
        "C1_wrong_T_same_G",
        "C2_shuffled_G_global",
        "C3_shuffled_G_within_predicate",
        "C4_sign_flipped_G_control",
    ]
    lines = [
        "# H002 Size-Relative Sanitized View Smoke Runner",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"positive / negative = {summary['counts']['positive']} / {summary['counts']['negative']}",
        f"paired_groups = {summary['counts']['paired_groups_with_one_positive_one_negative']}",
        f"validation_errors = {summary['validation_errors']}",
        f"overall = {gates['overall_interpretation']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Metrics",
        "",
        "| Model | AUROC | AUPRC | Accuracy | Balanced Acc. | ECE-10 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in order:
        metric = metrics[name]
        lines.append(
            f"| `{name}` | {metric.get('auroc')} | {metric.get('auprc')} | "
            f"{metric.get('accuracy_at_0_5')} | {metric.get('balanced_accuracy_at_0_5')} | {metric.get('ece_10')} |"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            f"- data integrity: `{gates['gate_data_integrity']['pass']}`",
            f"- single-factor shortcuts near chance: `{gates['gate_single_factor_shortcuts_near_chance']['pass']}`",
            f"- primary interaction signal: `{gates['gate_primary_interaction_signal']['pass']}`",
            f"- primary gain over single factor: `{gates['gate_primary_gain_over_single_factor']['pass']}`",
            f"- plain concat caveat: `{gates['gate_plain_concat_boundary']['concat_caveat']}`",
            f"- wrong-T degradation: `{gates['gate_wrong_T_same_G_degradation']['pass']}`",
            f"- shuffled-G degradation: `{gates['gate_shuffled_G_degradation']['pass']}`",
            f"- sign-flipped-G control: `{gates['gate_sign_flipped_G_control']['pass']}`",
            f"- paired score margin: `{gates['gate_paired_score_margin']['pass']}`",
            "",
            "## Interpretation",
            "",
            "This is a train-only hypothesis smoke. Passing controls means this row design",
            "supports the `size_relative` predicate-geometry compatibility route. It is not",
            "paper evidence until reproduced under the experiment workflow.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    plan = read_json(args.plan_dir / "smoke_plan.json")
    manifest = read_json(args.plan_dir / "input_manifest.json")
    input_path = resolve_repo_path(plan["input_contract"]["input_file"])
    raw_rows = read_jsonl(input_path)
    rows = normalize_rows(raw_rows)
    errors = validate(args.plan_dir, plan_summary, plan, manifest, raw_rows, rows)

    metrics, predictions, folds = eval_models(rows, args.folds, args.epochs, args.lr, args.l2)
    margins = paired_margins(rows, predictions)
    gates = gate_summary(metrics, margins, errors)

    if errors:
        status = STATUS_ERRORS
        next_todo = EXPECTED_PLAN_NEXT
    elif gates["overall_pass"] and gates["gate_plain_concat_boundary"]["concat_caveat"]:
        status = STATUS_CONCAT_CAVEAT
        next_todo = NEXT_TODO_PASSED
    elif gates["overall_pass"]:
        status = STATUS_PASSED
        next_todo = NEXT_TODO_PASSED
    else:
        status = STATUS_DIAGNOSTIC
        next_todo = NEXT_TODO_DIAGNOSTIC

    pred_rows = prediction_rows(rows, predictions)
    primary_errors = error_cases(rows, predictions[PRIMARY_MODEL])
    output_paths = {
        "artifact_root": rel_path(args.output_dir),
        "error_cases": rel_path(args.output_dir / "error_cases.jsonl"),
        "folds": rel_path(args.output_dir / "folds.json"),
        "gate_summary": rel_path(args.output_dir / "gate_summary.json"),
        "metrics": rel_path(args.output_dir / "metrics.json"),
        "metrics_table": rel_path(args.output_dir / "metrics_table.csv"),
        "paired_margins": rel_path(args.output_dir / "paired_margins.json"),
        "predictions": rel_path(args.output_dir / "predictions.jsonl"),
        "report": rel_path(args.output_dir / "report.md"),
        "summary": rel_path(args.output_dir / "summary.json"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
    }
    counts = count_summary(rows)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "validation_errors": len(errors),
        "counts": counts,
        "config": {"folds": args.folds, "epochs": args.epochs, "lr": args.lr, "l2": args.l2},
        "input_paths": {
            "plan_dir": rel_path(args.plan_dir),
            "input_file": rel_path(input_path),
            "input_sha256": sha256_file(input_path),
        },
        "output_paths": output_paths,
        "primary_model": PRIMARY_MODEL,
        "primary_metrics": metrics[PRIMARY_MODEL],
        "gate_summary": gates,
        "learned_smoke_executed": True,
        "paper_evidence_allowed": False,
        "boundary": {
            "split": "train_only_grouped_cv_smoke",
            "runs_learned_smoke": True,
            "trains_new_model": True,
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "source_score_used": False,
            "q_e_used_as_truth": False,
        },
    }

    write_json(args.output_dir / "metrics.json", metrics)
    write_csv(
        args.output_dir / "metrics_table.csv",
        [
            {
                "model": name,
                "auroc": metric.get("auroc"),
                "auprc": metric.get("auprc"),
                "accuracy_at_0_5": metric.get("accuracy_at_0_5"),
                "balanced_accuracy_at_0_5": metric.get("balanced_accuracy_at_0_5"),
                "brier": metric.get("brier"),
                "ece_10": metric.get("ece_10"),
            }
            for name, metric in metrics.items()
        ],
    )
    write_json(args.output_dir / "folds.json", folds)
    write_json(args.output_dir / "gate_summary.json", gates)
    write_json(args.output_dir / "paired_margins.json", margins)
    write_jsonl(args.output_dir / "predictions.jsonl", pred_rows)
    write_jsonl(args.output_dir / "error_cases.jsonl", primary_errors)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, metrics, gates)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
