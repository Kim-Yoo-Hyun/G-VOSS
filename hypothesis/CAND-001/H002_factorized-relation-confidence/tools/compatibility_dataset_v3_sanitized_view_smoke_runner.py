#!/usr/bin/env python3
"""Run train-only learned smoke on the H002 v3 smoke-ready view."""

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

from learned_smoke_runner_v1 import (
    binary_metrics,
    group_metrics,
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
DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_sanitized_view_smoke_runner"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_sanitized_view_smoke_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_sanitized_view_smoke_runner"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_sanitized_view_smoke_runner_v1"
STATUS_ERRORS = "h002_compatibility_dataset_v3_sanitized_view_smoke_runner_input_errors"
STATUS_PASSED = "h002_compatibility_dataset_v3_sanitized_view_smoke_runner_passed_controls"
STATUS_DIAGNOSTIC = "h002_compatibility_dataset_v3_sanitized_view_smoke_runner_diagnostic_only_failed_controls"
NEXT_TODO_PASSED = "compatibility_dataset_v3_result_review_and_family_extension_decision"
NEXT_TODO_DIAGNOSTIC = "compatibility_dataset_v3_failure_analysis"

PRIMARY_MODEL = "M5b_compatibility_TG_interaction"
PRIMARY_AUROC_MIN = 0.90
NEAR_CHANCE_AUROC_MAX = 0.60
PRIMARY_GAIN_MIN = 0.30
CONCAT_GAIN_MIN = 0.20

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]

FORBIDDEN_FEATURE_KEYS = {
    "geometry_feature_hash",
    "labels",
    "controls_hidden",
    "row_id",
    "geometry_group_id",
    "raw_source_predicate",
    "source_prediction_id",
    "positive_predicate",
    "direction_bucket",
    "visible_pair",
    "endpoint_state",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=120)
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
    return (H2_ROOT.parents[2] / path).resolve()


def block(row: dict[str, Any], name: str) -> dict[str, Any]:
    return row.get("feature_blocks", {}).get(name, {})


def t_block(row: dict[str, Any]) -> dict[str, Any]:
    return block(row, "T_e")


def z_block(row: dict[str, Any]) -> dict[str, Any]:
    return block(row, "Z_e_safe")


def g_block(row: dict[str, Any]) -> dict[str, Any]:
    return block(row, "G_e_numeric")


def q_block(row: dict[str, Any]) -> dict[str, Any]:
    return block(row, "Q_e_safe")


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["row_id"] = row.get("example_id")
        item["group_id"] = row.get("cv_group_id")
        item["T_e"] = dict(t_block(row))
        item["Z_e_safe"] = dict(z_block(row))
        item["G_e_numeric"] = dict(g_block(row))
        item["Q_e_safe"] = dict(q_block(row))
        item["y_compatibility"] = int(row.get("target_y"))
        item["split"] = "train"
        normalized.append(item)
    return normalized


def t_features_from_dict(t: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    out.update(one_hot("T.family", t.get("relation_family")))
    out.update(one_hot("T.predicate", t.get("predicate_label")))
    out.update(one_hot("T.subject", t.get("subject_class_label")))
    out.update(one_hot("T.object", t.get("object_class_label")))
    out.update(one_hot("T.subject_object", t.get("subject_object_text")))
    return out


def t_features(row: dict[str, Any]) -> dict[str, float]:
    return t_features_from_dict(row.get("T_e", {}))


def predicate_only_features(row: dict[str, Any]) -> dict[str, float]:
    return one_hot("T.predicate", row.get("T_e", {}).get("predicate_label"))


def object_pair_features(row: dict[str, Any]) -> dict[str, float]:
    t = row.get("T_e", {})
    out: dict[str, float] = {}
    out.update(one_hot("T.subject", t.get("subject_class_label")))
    out.update(one_hot("T.object", t.get("object_class_label")))
    out.update(one_hot("T.subject_object", t.get("subject_object_text")))
    return out


def z_features(row: dict[str, Any]) -> dict[str, float]:
    z = row.get("Z_e_safe", {})
    rank = max(safe_float(z.get("source_rank"), 999.0), 0.0)
    out: dict[str, float] = {
        "Z.source_score_normalized": safe_float(z.get("source_score_normalized"), 0.5),
        "Z.source_score_raw": safe_float(z.get("source_score_raw"), 0.0),
        "Z.source_score_missing": 0.0 if z.get("source_score_available") else 1.0,
        "Z.source_rank": rank,
        "Z.source_rank_log": math.log1p(rank),
        "Z.source_rank_inverse": 1.0 / (1.0 + rank),
    }
    out.update(one_hot("Z.source_id", z.get("source_id")))
    out.update(one_hot("Z.rank_band", z.get("source_rank_band")))
    return out


def z_scalar_features(row: dict[str, Any]) -> dict[str, float]:
    z = row.get("Z_e_safe", {})
    rank = max(safe_float(z.get("source_rank"), 999.0), 0.0)
    return {
        "Z.source_score_normalized": safe_float(z.get("source_score_normalized"), 0.5),
        "Z.source_rank": rank,
        "Z.source_rank_inverse": 1.0 / (1.0 + rank),
    }


def g_features_from_dict(g: dict[str, Any]) -> dict[str, float]:
    return {f"G.{key}": safe_float(value, 0.0) for key, value in sorted(g.items())}


def g_features(row: dict[str, Any]) -> dict[str, float]:
    return g_features_from_dict(row.get("G_e_numeric", {}))


def q_features(row: dict[str, Any]) -> dict[str, float]:
    q = row.get("Q_e_safe", {})
    out: dict[str, float] = {
        "Q.evidence_availability_count": safe_float(q.get("evidence_availability_count"), 0.0),
        "Q.geometry_available": 1.0 if q.get("geometry_available") else 0.0,
        "Q.mesh_available": 1.0 if q.get("mesh_available") else 0.0,
        "Q.obb_available": 1.0 if q.get("obb_available") else 0.0,
        "Q.view_packet_available": 1.0 if q.get("view_packet_available") else 0.0,
    }
    for value in q.get("missing_evidence_types", []) or []:
        out.update(one_hot("Q.missing_evidence", value))
    return out


def expected_z_sign(predicate: Any) -> float:
    if predicate == "higher than":
        return 1.0
    if predicate == "lower than":
        return -1.0
    return 0.0


def compatibility_interactions_from_dict(t: dict[str, Any], g: dict[str, Any]) -> dict[str, float]:
    sign = expected_z_sign(t.get("predicate_label"))
    center = safe_float(g.get("center_delta_z_m"), 0.0)
    norm = safe_float(g.get("normalized_center_delta_z"), 0.0)
    subject_center = safe_float(g.get("subject_center_z"), 0.0)
    object_center = safe_float(g.get("object_center_z"), 0.0)
    return {
        "C.sign_center_delta_z_m": sign * center,
        "C.sign_normalized_center_delta_z": sign * norm,
        "C.sign_subject_minus_object_center_z": sign * (subject_center - object_center),
        "C.margin_center_delta_z_m_0p10": sign * center - 0.10,
        "C.margin_normalized_center_delta_z_0p20": sign * norm - 0.20,
    }


def compatibility_interaction_features(row: dict[str, Any]) -> dict[str, float]:
    return compatibility_interactions_from_dict(row.get("T_e", {}), row.get("G_e_numeric", {}))


def compatibility_tg_concat_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), g_features(row))


def compatibility_tg_interaction_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), g_features(row), compatibility_interaction_features(row))


def factorized_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(compatibility_tg_interaction_features(row), z_features(row), q_features(row))


def wrong_predicate(value: Any) -> str:
    if value == "higher than":
        return "lower than"
    if value == "lower than":
        return "higher than"
    return f"wrong_{value}"


def wrong_t(row: dict[str, Any]) -> dict[str, Any]:
    t = dict(row.get("T_e", {}))
    t["predicate_label"] = wrong_predicate(t.get("predicate_label"))
    t["predicate_text"] = t["predicate_label"]
    return t


def wrong_t_same_g_features(row: dict[str, Any]) -> dict[str, float]:
    t = wrong_t(row)
    g = row.get("G_e_numeric", {})
    return merge_features(t_features_from_dict(t), g_features_from_dict(g), compatibility_interactions_from_dict(t, g))


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
        if not ordered:
            continue
        if len(ordered) == 1:
            out[str(ordered[0]["row_id"])] = dict(ordered[0].get("G_e_numeric", {}))
            continue
        shift = max(1, len(ordered) // 2 + 1)
        for idx, row in enumerate(ordered):
            donor = ordered[(idx + shift) % len(ordered)]
            if donor.get("group_id") == row.get("group_id") and len(ordered) > 1:
                donor = ordered[(idx + shift + 1) % len(ordered)]
            out[str(row["row_id"])] = dict(donor.get("G_e_numeric", {}))
    return out


def shuffled_tg_interaction_features(row: dict[str, Any], geometry_map: dict[str, dict[str, Any]]) -> dict[str, float]:
    t = row.get("T_e", {})
    g = geometry_map[str(row["row_id"])]
    return merge_features(t_features(row), g_features_from_dict(g), compatibility_interactions_from_dict(t, g))


def model_feature_fns(rows: list[dict[str, Any]]) -> dict[str, tuple[FeatureFn, FeatureFn]]:
    global_g = shifted_geometry_map(rows)
    within_predicate_g = shifted_geometry_map(rows, lambda row: str(row.get("T_e", {}).get("predicate_label")))
    primary = compatibility_tg_interaction_features
    return {
        "M0_intercept": (lambda row: {}, lambda row: {}),
        "M1_source_only_Z_safe": (z_features, z_features),
        "M2_semantic_only_T": (t_features, t_features),
        "M3_semantic_source_TZ_safe": (lambda row: merge_features(t_features(row), z_features(row)), lambda row: merge_features(t_features(row), z_features(row))),
        "M4_geometry_only_G": (g_features, g_features),
        "M5a_compatibility_TG_concat": (compatibility_tg_concat_features, compatibility_tg_concat_features),
        PRIMARY_MODEL: (primary, primary),
        "M6_factorized_sanitized_TZGQ_interaction": (factorized_features, factorized_features),
        "S1_predicate_label_shortcut": (predicate_only_features, predicate_only_features),
        "S2_object_pair_shortcut": (object_pair_features, object_pair_features),
        "S3_source_score_rank_shortcut": (z_scalar_features, z_scalar_features),
        "C1_wrong_T_same_G_control": (primary, wrong_t_same_g_features),
        "C2_shuffled_G_global_control": (primary, lambda row: shuffled_tg_interaction_features(row, global_g)),
        "C3_shuffled_G_within_predicate_control": (primary, lambda row: shuffled_tg_interaction_features(row, within_predicate_g)),
    }


def labels(rows: list[dict[str, Any]]) -> list[int]:
    return [int(row["y_compatibility"]) for row in rows]


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
            fold_summaries.append(
                {
                    "fold": fold_idx,
                    "train_rows": len(train_indices),
                    "test_rows": len(test_indices),
                    "mode": "prior_only",
                }
            )
            continue
        train_feats = [train_feature_fn(rows[idx]) for idx in train_indices]
        model = train_logistic(train_feats, y_train, epochs=epochs, lr=lr, l2=l2)
        for idx in test_indices:
            predictions[idx] = model.predict_one(eval_feature_fn(rows[idx]))
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
        "metrics": augment_binary_metrics(y, predictions),
        "predictions": predictions,
        "folds": fold_summaries,
    }


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


def eval_models(
    rows: list[dict[str, Any]],
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[dict[str, Any], dict[str, list[float]], dict[str, Any]]:
    y = labels(rows)
    metrics: dict[str, Any] = {}
    predictions: dict[str, list[float]] = {}
    folds: dict[str, Any] = {}
    for name, (train_fn, eval_fn) in model_feature_fns(rows).items():
        result = train_eval_cv_dual(rows, y, train_fn, eval_fn, fold_count, epochs, lr, l2)
        metrics[name] = result["metrics"]
        predictions[name] = result["predictions"]
        folds[name] = result["folds"]
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
        "rows": len(rows),
        "positive": sum(y),
        "negative": len(y) - sum(y),
        "groups": len(groups),
        "paired_groups_with_one_positive_one_negative": sum(1 for vals in groups.values() if sorted(vals) == [0, 1]),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "predicate_label_counts": dict(sorted(predicate_label_counts.items())),
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
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan_summary.get("validation_errors")})
    if (plan_dir / "validation_errors.jsonl").exists() and (plan_dir / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "plan_validation_errors_nonempty"})

    input_path = resolve_repo_path(plan["input_contract"]["input_file"])
    if sha256_file(input_path) != plan["input_contract"]["input_sha256"]:
        errors.append({"error_type": "input_sha256_mismatch", "path": str(input_path)})
    if sha256_file(input_path) != manifest.get("smoke_ready_view_sha256"):
        errors.append({"error_type": "manifest_input_sha256_mismatch", "path": str(input_path)})

    counts = count_summary(rows)
    if counts["rows"] != 400 or counts["positive"] != 200 or counts["negative"] != 200:
        errors.append({"error_type": "unexpected_counts", **counts})
    if counts["groups"] != 200 or counts["paired_groups_with_one_positive_one_negative"] != 200:
        errors.append({"error_type": "unexpected_group_pairing", **counts})

    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for raw, row in zip(raw_rows, rows):
        row_id = row.get("row_id")
        if raw.get("schema_version") != "h002_compatibility_dataset_v3_smoke_ready_view_v1":
            errors.append({"error_type": "unexpected_row_schema", "row_id": row_id, "actual": raw.get("schema_version")})
        if raw.get("target_name") != "C_e_predicate_geometry_compatibility":
            errors.append({"error_type": "unexpected_target_name", "row_id": row_id, "actual": raw.get("target_name")})
        if set(raw.get("feature_blocks", {})) != {"T_e", "Z_e_safe", "G_e_numeric", "Q_e_safe"}:
            errors.append({"error_type": "unexpected_feature_blocks", "row_id": row_id, "actual": sorted(raw.get("feature_blocks", {}))})
        feature_text = json.dumps(raw.get("feature_blocks", {}), ensure_ascii=False)
        for token in FORBIDDEN_FEATURE_KEYS:
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
        if predicates != ["higher than", "lower than"]:
            errors.append({"error_type": "group_predicates_not_higher_lower", "group_id": group_id, "predicates": predicates})
        g_values = {json.dumps(row.get("G_e_numeric", {}), sort_keys=True) for row in group_rows}
        if len(g_values) != 1:
            errors.append({"error_type": "group_geometry_not_identical", "group_id": group_id})
    return errors


def value_or_zero(metrics: dict[str, Any], name: str) -> float:
    value = metrics.get(name, {}).get("auroc")
    return 0.0 if value is None else float(value)


def paired_score_drop(rows: list[dict[str, Any]], predictions: dict[str, list[float]]) -> dict[str, Any]:
    group_indices: dict[str, list[int]] = defaultdict(list)
    y = labels(rows)
    for idx, row in enumerate(rows):
        group_indices[str(row.get("group_id"))].append(idx)
    out: dict[str, Any] = {}
    for model_name, scores in predictions.items():
        drops: list[float] = []
        for indices in group_indices.values():
            pos = [idx for idx in indices if y[idx] == 1]
            neg = [idx for idx in indices if y[idx] == 0]
            if len(pos) == 1 and len(neg) == 1:
                drops.append(scores[pos[0]] - scores[neg[0]])
        out[model_name] = {
            "groups": len(drops),
            "mean_positive_minus_negative": round(mean(drops), 6) if drops else None,
            "positive_drop_fraction": round(sum(1 for value in drops if value > 0.0) / len(drops), 6) if drops else None,
            "min_positive_minus_negative": round(min(drops), 6) if drops else None,
            "max_positive_minus_negative": round(max(drops), 6) if drops else None,
        }
    return out


def gate_summary(metrics: dict[str, Any], drops: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    m1 = value_or_zero(metrics, "M1_source_only_Z_safe")
    m2 = value_or_zero(metrics, "M2_semantic_only_T")
    m3 = value_or_zero(metrics, "M3_semantic_source_TZ_safe")
    m4 = value_or_zero(metrics, "M4_geometry_only_G")
    m5a = value_or_zero(metrics, "M5a_compatibility_TG_concat")
    m5b = value_or_zero(metrics, PRIMARY_MODEL)
    m6 = value_or_zero(metrics, "M6_factorized_sanitized_TZGQ_interaction")
    s1 = value_or_zero(metrics, "S1_predicate_label_shortcut")
    s2 = value_or_zero(metrics, "S2_object_pair_shortcut")
    s3 = value_or_zero(metrics, "S3_source_score_rank_shortcut")
    c1 = value_or_zero(metrics, "C1_wrong_T_same_G_control")
    c2 = value_or_zero(metrics, "C2_shuffled_G_global_control")
    c3 = value_or_zero(metrics, "C3_shuffled_G_within_predicate_control")

    shortcut_aucs = {
        "M1_source_only_Z_safe": m1,
        "M2_semantic_only_T": m2,
        "M3_semantic_source_TZ_safe": m3,
        "M4_geometry_only_G": m4,
        "S1_predicate_label_shortcut": s1,
        "S2_object_pair_shortcut": s2,
        "S3_source_score_rank_shortcut": s3,
    }
    best_noncompat = max(m1, m2, m3, m4)
    best_shuffle = max(c2, c3)
    primary_drop = drops.get(PRIMARY_MODEL, {})
    mean_drop = primary_drop.get("mean_positive_minus_negative") or 0.0
    drop_fraction = primary_drop.get("positive_drop_fraction") or 0.0

    gate_data = len(errors) == 0
    gate_shortcut = max(shortcut_aucs.values()) <= NEAR_CHANCE_AUROC_MAX
    gate_primary = m5b >= PRIMARY_AUROC_MIN and (m5b - best_noncompat) >= PRIMARY_GAIN_MIN
    gate_concat = m5a <= NEAR_CHANCE_AUROC_MAX or (m5b - m5a) >= CONCAT_GAIN_MIN
    gate_wrong_t = c1 <= NEAR_CHANCE_AUROC_MAX and (m5b - c1) >= PRIMARY_GAIN_MIN
    gate_shuffle = best_shuffle <= NEAR_CHANCE_AUROC_MAX and (m5b - best_shuffle) >= PRIMARY_GAIN_MIN
    gate_paired = mean_drop > 0.0 and drop_fraction >= 0.90
    overall = gate_data and gate_shortcut and gate_primary and gate_concat and gate_wrong_t and gate_shuffle and gate_paired

    return {
        "gate_data_integrity": {
            "pass": gate_data,
            "validation_errors": len(errors),
        },
        "gate_shortcut_baselines_near_chance": {
            "pass": gate_shortcut,
            "max_allowed": NEAR_CHANCE_AUROC_MAX,
            "auroc": shortcut_aucs,
        },
        "gate_primary_compatibility_success": {
            "pass": gate_primary,
            PRIMARY_MODEL: m5b,
            "min_required": PRIMARY_AUROC_MIN,
            "best_M1_to_M4": best_noncompat,
            "required_gain": PRIMARY_GAIN_MIN,
            "actual_gain": m5b - best_noncompat,
        },
        "gate_interaction_over_plain_concat": {
            "pass": gate_concat,
            PRIMARY_MODEL: m5b,
            "M5a_compatibility_TG_concat": m5a,
            "required_gain_if_concat_above_near_chance": CONCAT_GAIN_MIN,
            "actual_gain": m5b - m5a,
        },
        "gate_wrong_T_same_G_degradation": {
            "pass": gate_wrong_t,
            PRIMARY_MODEL: m5b,
            "C1_wrong_T_same_G_control": c1,
            "actual_gain": m5b - c1,
        },
        "gate_shuffled_G_degradation": {
            "pass": gate_shuffle,
            PRIMARY_MODEL: m5b,
            "C2_shuffled_G_global_control": c2,
            "C3_shuffled_G_within_predicate_control": c3,
            "best_shuffle": best_shuffle,
            "actual_gain": m5b - best_shuffle,
        },
        "gate_paired_score_drop": {
            "pass": gate_paired,
            "mean_positive_minus_negative": mean_drop,
            "positive_drop_fraction": drop_fraction,
        },
        "factorized_not_primary": {
            "M6_factorized_sanitized_TZGQ_interaction": m6,
            "interpretation": "M6 is an ablation because this v3 smoke primarily tests C_e, not final p_rel/p_obs.",
        },
        "overall_pass": overall,
        "overall_interpretation": (
            "v3_sanitized_view_smoke_passed_controls"
            if overall
            else "v3_sanitized_view_smoke_diagnostic_only_failed_controls"
        ),
    }


def prediction_rows(rows: list[dict[str, Any]], predictions: dict[str, list[float]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        item = {
            "row_id": row.get("row_id"),
            "group_id": row.get("group_id"),
            "label": row.get("y_compatibility"),
            "predicate": row.get("T_e", {}).get("predicate_label"),
            "subject": row.get("T_e", {}).get("subject_class_label"),
            "object": row.get("T_e", {}).get("object_class_label"),
        }
        for model, scores in predictions.items():
            item[model] = scores[idx]
        out.append(item)
    return out


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
                "subject": row.get("T_e", {}).get("subject_class_label"),
                "object": row.get("T_e", {}).get("object_class_label"),
                "label": label,
                "prediction": pred,
                "score": round(score, 6),
                "source_score": row.get("Z_e_safe", {}).get("source_score_normalized"),
                "source_rank_band": row.get("Z_e_safe", {}).get("source_rank_band"),
                "center_delta_z_m": row.get("G_e_numeric", {}).get("center_delta_z_m"),
                "normalized_center_delta_z": row.get("G_e_numeric", {}).get("normalized_center_delta_z"),
            }
        )
    return sorted(cases, key=lambda item: abs(float(item["score"]) - 0.5), reverse=True)[:max_cases]


def write_report(path: Path, summary: dict[str, Any], metrics: dict[str, Any], gates: dict[str, Any]) -> None:
    order = [
        "M1_source_only_Z_safe",
        "M2_semantic_only_T",
        "M3_semantic_source_TZ_safe",
        "M4_geometry_only_G",
        "M5a_compatibility_TG_concat",
        PRIMARY_MODEL,
        "M6_factorized_sanitized_TZGQ_interaction",
        "S1_predicate_label_shortcut",
        "S2_object_pair_shortcut",
        "S3_source_score_rank_shortcut",
        "C1_wrong_T_same_G_control",
        "C2_shuffled_G_global_control",
        "C3_shuffled_G_within_predicate_control",
    ]
    lines = [
        "# Compatibility Dataset V3 Sanitized View Smoke Runner",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v3_sanitized_view_smoke_runner/",
        "```",
        "",
        "Status:",
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
            f"- shortcut baselines near chance: `{gates['gate_shortcut_baselines_near_chance']['pass']}`",
            f"- primary compatibility success: `{gates['gate_primary_compatibility_success']['pass']}`",
            f"- interaction over plain concat: `{gates['gate_interaction_over_plain_concat']['pass']}`",
            f"- wrong-T same-G degradation: `{gates['gate_wrong_T_same_G_degradation']['pass']}`",
            f"- shuffled-G degradation: `{gates['gate_shuffled_G_degradation']['pass']}`",
            f"- paired score drop: `{gates['gate_paired_score_drop']['pass']}`",
            "",
            "## Interpretation",
            "",
            "This smoke tests whether the same predicate-independent `G_e` is interpreted differently",
            "when paired with different semantic relation content `T_e`. The primary result is",
            "`M5b_compatibility_TG_interaction`; `M6` is reported only as a factorized ablation.",
            "",
            "The wrong-T and shuffled-G rows are inference-time corruptions of the primary trained",
            "view, not separately re-trained corrupted models.",
            "",
            "## Boundary",
            "",
            "- train-only grouped-CV hypothesis smoke",
            "- no validation/test usage",
            "- no paper-level evidence",
            "- no H001 artifact modification",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
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
    y = labels(rows)
    drops = paired_score_drop(rows, predictions)
    metrics_by_predicate = group_metrics(rows, y, predictions, lambda row: str(row.get("T_e", {}).get("predicate_label")))
    metrics_by_pair_text = group_metrics(rows, y, predictions, lambda row: str(row.get("T_e", {}).get("subject_object_text")))
    gates = gate_summary(metrics, drops, errors)

    status = STATUS_ERRORS if errors else (STATUS_PASSED if gates["overall_pass"] else STATUS_DIAGNOSTIC)
    next_todo = NEXT_TODO_PASSED if gates["overall_pass"] else NEXT_TODO_DIAGNOSTIC
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "plan_root": rel_path(args.plan_dir),
        "input_file": rel_path(input_path),
        "input_sha256": sha256_file(input_path),
        "output_root": rel_path(args.output_dir),
        "counts": count_summary(rows),
        "validation_errors": len(errors),
        "folds": args.folds,
        "epochs": args.epochs,
        "lr": args.lr,
        "l2": args.l2,
        "learned_smoke_executed": True,
        "primary_model": PRIMARY_MODEL,
        "paper_evidence_allowed": False,
        "boundary": {
            "split": "train_internal_grouped_by_cv_group_id",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "raw_candidate_rows_used_as_model_input": False,
            "corruption_controls_train_on_clean_features": True,
        },
        "key_metrics": {name: metrics[name] for name in sorted(metrics)},
        "gates": gates,
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "metrics": rel_path(args.output_dir / "metrics.json"),
            "metrics_by_predicate": rel_path(args.output_dir / "metrics_by_predicate.json"),
            "paired_score_drop": rel_path(args.output_dir / "paired_score_drop.json"),
            "folds": rel_path(args.output_dir / "folds.json"),
            "predictions": rel_path(args.output_dir / "predictions.jsonl"),
            "error_cases": rel_path(args.output_dir / "error_cases_m5b.jsonl"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "metrics.json", metrics)
    write_json(args.output_dir / "metrics_by_predicate.json", {"predicate": metrics_by_predicate, "subject_object_text": metrics_by_pair_text})
    write_json(args.output_dir / "paired_score_drop.json", drops)
    write_json(args.output_dir / "folds.json", folds)
    write_jsonl(args.output_dir / "predictions.jsonl", prediction_rows(rows, predictions))
    write_jsonl(args.output_dir / "error_cases_m5b.jsonl", error_cases(rows, predictions[PRIMARY_MODEL]))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, metrics, gates)


if __name__ == "__main__":
    main()
