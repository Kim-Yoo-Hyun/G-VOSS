#!/usr/bin/env python3
"""Run train-only learned smoke for the repaired independent-validity H002 target."""

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
DEFAULT_PLAN_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan_ready"
)
EXPECTED_PLAN_NEXT = (
    "compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner"
)
EXPECTED_ROW_SCHEMA = "h002_exact_stratum_repaired_independent_validity_sanitized_primary_view_v1"
EXPECTED_TARGET = "C_e_independent_validity_exact_stratum_repaired_primary_binary"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner_v1"
)
STATUS_ERRORS = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner_input_errors"
)
STATUS_PASSED = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner_passed_controls"
)
STATUS_DIAGNOSTIC = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner_diagnostic_only"
)
STATUS_GEOMETRY_DOMINANCE = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner_geometry_dominance_diagnostic"
)

NEXT_TODO_REVIEW = "compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review"
PRIMARY_MODEL = "M6_TG_compatibility_interaction"
FULL_MODEL = "M7_factorized_TZGQ"

NEAR_CHANCE_AUROC_MAX = 0.60
PRIMARY_AUROC_MIN = 0.65
PRIMARY_GAIN_OVER_SEMANTIC_SOURCE_MIN = 0.05
GEOMETRY_DOMINANCE_MARGIN = 0.02
SHUFFLE_CONTROL_MARGIN = 0.05

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]

FORBIDDEN_FEATURE_TOKENS = {
    "geometry_status",
    "p_geom_valid",
    "label_match",
    "target_pool",
    "construction_proxy",
    "machine_hint",
    "hidden_manifest",
    "gt_relation_id",
    "source_prediction_id",
    "validity_bucket",
    "satisfied",
    "unsatisfied",
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


def raw_geometry_vector(g: dict[str, Any]) -> dict[str, Any]:
    vector = g.get("raw_geometry_feature_vector")
    if isinstance(vector, dict):
        return vector
    return {}


def normalize_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in raw_rows:
        item = {
            "row_id": row.get("example_id"),
            "group_id": row.get("cv_group_id"),
            "family": row.get("family"),
            "split": row.get("split"),
            "target_name": row.get("target_name"),
            "schema_version": row.get("schema_version"),
            "T_e": dict(block(row, "T_e")),
            "Z_e_safe": dict(block(row, "Z_e_safe")),
            "G_e_raw": dict(block(row, "G_e_raw")),
            "Q_e_safe": dict(block(row, "Q_e_safe")),
            "y_compatibility": int(row.get("target_y")),
            "text": dict(row.get("text") or {}),
        }
        normalized.append(item)
    return normalized


def subject_object_pair(t: dict[str, Any]) -> str:
    return f"{t.get('subject_class_label')}|{t.get('object_class_label')}"


def t_features_from_dict(t: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    out.update(one_hot("T.family", t.get("relation_family")))
    out.update(one_hot("T.predicate", t.get("predicate_label")))
    out.update(one_hot("T.subject", t.get("subject_class_label")))
    out.update(one_hot("T.object", t.get("object_class_label")))
    out.update(one_hot("T.subject_object", subject_object_pair(t)))
    return out


def t_features(row: dict[str, Any]) -> dict[str, float]:
    return t_features_from_dict(row.get("T_e", {}))


def predicate_class_pair_features(row: dict[str, Any]) -> dict[str, float]:
    t = row.get("T_e", {})
    predicate = str(t.get("predicate_label"))
    pair = subject_object_pair(t)
    return {f"S1.predicate_pair={predicate}::{pair}".replace(" ", "_").replace("/", "_"): 1.0}


def z_features(row: dict[str, Any]) -> dict[str, float]:
    z = row.get("Z_e_safe", {})
    rank = max(safe_float(z.get("semantic_rank"), 999.0), 0.0)
    out: dict[str, float] = {
        "Z.semantic_score_norm": safe_float(z.get("semantic_score_norm"), 0.5),
        "Z.semantic_score_raw": safe_float(z.get("semantic_score_raw"), 0.0),
        "Z.semantic_rank": rank,
        "Z.semantic_rank_log": math.log1p(rank),
        "Z.semantic_rank_inverse": 1.0 / (1.0 + rank),
    }
    out.update(one_hot("Z.rank_band", z.get("rank_band")))
    out.update(one_hot("Z.source_id", z.get("source_id")))
    return out


def z_scalar_features(row: dict[str, Any]) -> dict[str, float]:
    z = row.get("Z_e_safe", {})
    rank = max(safe_float(z.get("semantic_rank"), 999.0), 0.0)
    return {
        "Z.semantic_score_norm": safe_float(z.get("semantic_score_norm"), 0.5),
        "Z.semantic_score_raw": safe_float(z.get("semantic_score_raw"), 0.0),
        "Z.semantic_rank": rank,
        "Z.semantic_rank_inverse": 1.0 / (1.0 + rank),
    }


def g_features_from_dict(g: dict[str, Any]) -> dict[str, float]:
    vector = raw_geometry_vector(g)
    out: dict[str, float] = {}
    mask = g.get("raw_geometry_feature_available_mask") or {}
    for key, value in sorted(vector.items()):
        out[f"G.{key}"] = safe_float(value, 0.0)
        out[f"G.{key}.available"] = 1.0 if mask.get(key, value is not None) else 0.0
    return out


def g_features(row: dict[str, Any]) -> dict[str, float]:
    return g_features_from_dict(row.get("G_e_raw", {}))


def q_features(row: dict[str, Any]) -> dict[str, float]:
    q = row.get("Q_e_safe", {})
    out: dict[str, float] = {
        "Q.object_pair_feature_coverage": safe_float(q.get("object_pair_feature_coverage"), 0.0),
        "Q.raw_geometry_available": 1.0 if q.get("raw_geometry_available") else 0.0,
        "Q.raw_geometry_feature_count": safe_float(q.get("raw_geometry_feature_count"), 0.0),
    }
    out.update(one_hot("Q.mesh_or_point_availability", q.get("mesh_or_point_availability")))
    return out


def expected_z_sign(predicate: Any) -> float:
    text = str(predicate)
    if text == "higher than":
        return 1.0
    if text == "lower than":
        return -1.0
    return 0.0


def support_contact_flag(predicate: Any) -> float:
    return 1.0 if str(predicate) in {"lying on", "standing on", "supported by"} else 0.0


def compatibility_interactions_from_dict(t: dict[str, Any], g: dict[str, Any]) -> dict[str, float]:
    vector = raw_geometry_vector(g)
    predicate = str(t.get("predicate_label"))
    family = str(t.get("relation_family"))
    sign = expected_z_sign(predicate)
    center = safe_float(vector.get("center_delta_z"), 0.0)
    norm_center = safe_float(vector.get("normalized_center_delta_z"), 0.0)
    gap = safe_float(vector.get("vertical_gap_subject_on_object"), 0.0)
    distance = safe_float(vector.get("normalized_distance_3d"), 0.0)
    xy_distance = safe_float(vector.get("normalized_distance_xy"), 0.0)
    overlap = safe_float(vector.get("projected_iou_xy"), 0.0)
    subj_overlap = safe_float(vector.get("projected_subject_overlap_ratio"), 0.0)
    obj_overlap = safe_float(vector.get("projected_object_overlap_ratio"), 0.0)
    support_flag = support_contact_flag(predicate)

    out: dict[str, float] = {
        "C.expected_center_delta_z": sign * center,
        "C.expected_normalized_center_delta_z": sign * norm_center,
        "C.expected_center_delta_positive_margin_0p05": sign * center - 0.05,
        "C.expected_center_delta_positive_margin_0p10": sign * center - 0.10,
        "C.support_flag_x_inverse_gap": support_flag / (1.0 + abs(gap)),
        "C.support_flag_x_overlap": support_flag * overlap,
        "C.support_flag_x_subject_overlap": support_flag * subj_overlap,
        "C.support_flag_x_object_overlap": support_flag * obj_overlap,
        "C.support_flag_x_inverse_distance": support_flag / (1.0 + max(distance, 0.0)),
        "C.support_flag_x_inverse_xy_distance": support_flag / (1.0 + max(xy_distance, 0.0)),
    }
    for key, value in sorted(vector.items()):
        val = safe_float(value, 0.0)
        safe_key = key.replace(" ", "_").replace("/", "_")
        safe_predicate = predicate.replace(" ", "_").replace("/", "_")
        safe_family = family.replace(" ", "_").replace("/", "_")
        out[f"C.predicate={safe_predicate}.G.{safe_key}"] = val
        out[f"C.family={safe_family}.G.{safe_key}"] = val
    return out


def compatibility_interaction_features(row: dict[str, Any]) -> dict[str, float]:
    return compatibility_interactions_from_dict(row.get("T_e", {}), row.get("G_e_raw", {}))


def compatibility_tg_concat_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), g_features(row))


def compatibility_tg_interaction_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), g_features(row), compatibility_interaction_features(row))


def factorized_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(compatibility_tg_interaction_features(row), z_features(row), q_features(row))


def wrong_predicate(value: Any) -> str:
    text = str(value)
    if text == "higher than":
        return "lower than"
    if text == "lower than":
        return "higher than"
    if text == "lying on":
        return "standing on"
    if text == "standing on":
        return "lying on"
    return f"wrong_{text}"


def wrong_t(row: dict[str, Any]) -> dict[str, Any]:
    t = dict(row.get("T_e", {}))
    t["predicate_label"] = wrong_predicate(t.get("predicate_label"))
    t["predicate_text"] = t["predicate_label"]
    if t["predicate_label"] in {"higher than", "lower than"}:
        t["relation_family"] = "relative_vertical"
    elif t["predicate_label"] in {"lying on", "standing on"}:
        t["relation_family"] = "support_contact_pose_conditioned"
    return t


def wrong_t_same_g_features(row: dict[str, Any]) -> dict[str, float]:
    t = wrong_t(row)
    g = row.get("G_e_raw", {})
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
        if len(ordered) <= 1:
            for row in ordered:
                out[str(row["row_id"])] = dict(row.get("G_e_raw", {}))
            continue
        shift = max(1, len(ordered) // 2 + 1)
        for idx, row in enumerate(ordered):
            donor = ordered[(idx + shift) % len(ordered)]
            if donor.get("group_id") == row.get("group_id") and len(ordered) > 1:
                donor = ordered[(idx + shift + 1) % len(ordered)]
            out[str(row["row_id"])] = dict(donor.get("G_e_raw", {}))
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
        "M1_semantic_only_T": (t_features, t_features),
        "M2_source_only_Z": (z_features, z_features),
        "M3_semantic_source_TZ": (
            lambda row: merge_features(t_features(row), z_features(row)),
            lambda row: merge_features(t_features(row), z_features(row)),
        ),
        "M4_geometry_only_G": (g_features, g_features),
        "M5_TG_concat": (compatibility_tg_concat_features, compatibility_tg_concat_features),
        PRIMARY_MODEL: (primary, primary),
        FULL_MODEL: (factorized_features, factorized_features),
        "S1_predicate_x_class_pair_shortcut": (predicate_class_pair_features, predicate_class_pair_features),
        "S2_source_rank_score_shortcut": (z_scalar_features, z_scalar_features),
        "C1_shuffled_G_global": (primary, lambda row: shuffled_tg_interaction_features(row, global_g)),
        "C2_shuffled_G_within_predicate": (
            primary,
            lambda row: shuffled_tg_interaction_features(row, within_predicate_g),
        ),
        "C3_wrong_predicate_family_control": (primary, wrong_t_same_g_features),
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
            fold_summaries.append(
                {
                    "fold": fold_idx,
                    "mode": "prior_only",
                    "test_rows": len(test_indices),
                    "train_rows": len(train_indices),
                }
            )
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
    return {
        "folds": fold_summaries,
        "metrics": augment_binary_metrics(y, predictions),
        "predictions": predictions,
    }


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
    family_counts: Counter[str] = Counter()
    family_label_counts: Counter[str] = Counter()
    predicate_counts: Counter[str] = Counter()
    predicate_label_counts: Counter[str] = Counter()
    for row, label in zip(rows, y):
        groups[str(row.get("group_id"))].append(label)
        family = str(row.get("T_e", {}).get("relation_family"))
        predicate = str(row.get("T_e", {}).get("predicate_label"))
        label_name = "positive" if label else "negative"
        family_counts[family] += 1
        family_label_counts[f"{family}|{label_name}"] += 1
        predicate_counts[predicate] += 1
        predicate_label_counts[f"{predicate}|{label_name}"] += 1
    return {
        "rows": len(rows),
        "positive": sum(y),
        "negative": len(y) - sum(y),
        "groups": len(groups),
        "mixed_label_groups": sum(1 for vals in groups.values() if len(set(vals)) > 1),
        "single_label_groups": sum(1 for vals in groups.values() if len(set(vals)) == 1),
        "family_counts": dict(sorted(family_counts.items())),
        "family_label_counts": dict(sorted(family_label_counts.items())),
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
    input_sha = sha256_file(input_path)
    if input_sha != plan["input_contract"]["input_sha256"]:
        errors.append({"error_type": "input_sha256_mismatch", "path": str(input_path)})
    if input_sha != manifest.get("smoke_ready_view_sha256"):
        errors.append({"error_type": "manifest_input_sha256_mismatch", "path": str(input_path)})

    counts = count_summary(rows)
    if counts["rows"] != 1600 or counts["positive"] != 800 or counts["negative"] != 800:
        errors.append({"error_type": "unexpected_counts", **counts})
    if counts["groups"] != 1097 or counts["mixed_label_groups"] != 491:
        errors.append({"error_type": "unexpected_group_profile", **counts})
    if counts["family_counts"] != {"relative_vertical": 1512, "support_contact_pose_conditioned": 88}:
        errors.append({"error_type": "unexpected_family_counts", **counts})

    for raw, row in zip(raw_rows, rows):
        row_id = row.get("row_id")
        if raw.get("schema_version") != EXPECTED_ROW_SCHEMA:
            errors.append({"error_type": "unexpected_row_schema", "row_id": row_id, "actual": raw.get("schema_version")})
        if raw.get("target_name") != EXPECTED_TARGET:
            errors.append({"error_type": "unexpected_target_name", "row_id": row_id, "actual": raw.get("target_name")})
        if set(raw.get("feature_blocks", {})) != {"T_e", "Z_e_safe", "G_e_raw", "Q_e_safe"}:
            errors.append({"error_type": "unexpected_feature_blocks", "row_id": row_id, "actual": sorted(raw.get("feature_blocks", {}))})
        feature_text = json.dumps(raw.get("feature_blocks", {}), ensure_ascii=False)
        for token in FORBIDDEN_FEATURE_TOKENS:
            if token in feature_text:
                errors.append({"error_type": "forbidden_feature_token", "row_id": row_id, "token": token})
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_id": row_id})
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
            for pos_idx in pos:
                for neg_idx in neg:
                    drops.append(scores[pos_idx] - scores[neg_idx])
        out[model_name] = {
            "contrast_pairs": len(drops),
            "max_positive_minus_negative": round(max(drops), 6) if drops else None,
            "mean_positive_minus_negative": round(mean(drops), 6) if drops else None,
            "min_positive_minus_negative": round(min(drops), 6) if drops else None,
            "positive_drop_fraction": round(sum(1 for value in drops if value > 0.0) / len(drops), 6) if drops else None,
        }
    return out


def gate_summary(metrics: dict[str, Any], drops: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    m1 = value_or_zero(metrics, "M1_semantic_only_T")
    m2 = value_or_zero(metrics, "M2_source_only_Z")
    m3 = value_or_zero(metrics, "M3_semantic_source_TZ")
    m4 = value_or_zero(metrics, "M4_geometry_only_G")
    m5 = value_or_zero(metrics, "M5_TG_concat")
    m6 = value_or_zero(metrics, PRIMARY_MODEL)
    m7 = value_or_zero(metrics, FULL_MODEL)
    s1 = value_or_zero(metrics, "S1_predicate_x_class_pair_shortcut")
    s2 = value_or_zero(metrics, "S2_source_rank_score_shortcut")
    c1 = value_or_zero(metrics, "C1_shuffled_G_global")
    c2 = value_or_zero(metrics, "C2_shuffled_G_within_predicate")
    c3 = value_or_zero(metrics, "C3_wrong_predicate_family_control")

    semantic_source_aucs = {
        "M1_semantic_only_T": m1,
        "M2_source_only_Z": m2,
        "M3_semantic_source_TZ": m3,
        "S1_predicate_x_class_pair_shortcut": s1,
        "S2_source_rank_score_shortcut": s2,
    }
    primary_aucs = {
        PRIMARY_MODEL: m6,
        FULL_MODEL: m7,
    }
    best_semantic_source = max(semantic_source_aucs.values())
    best_primary = max(primary_aucs.values())
    best_shuffle = max(c1, c2)
    primary_drop = drops.get(PRIMARY_MODEL, {})
    mean_drop = primary_drop.get("mean_positive_minus_negative") or 0.0
    drop_fraction = primary_drop.get("positive_drop_fraction") or 0.0

    gate_data = len(errors) == 0
    gate_semantic_source = best_semantic_source <= NEAR_CHANCE_AUROC_MAX
    gate_primary_signal = best_primary >= PRIMARY_AUROC_MIN
    gate_gain = (best_primary - best_semantic_source) >= PRIMARY_GAIN_OVER_SEMANTIC_SOURCE_MIN
    gate_geometry_dominance = (best_primary - m4) > GEOMETRY_DOMINANCE_MARGIN
    gate_shuffle = best_shuffle <= best_semantic_source + SHUFFLE_CONTROL_MARGIN
    gate_wrong_t = c3 <= best_semantic_source + SHUFFLE_CONTROL_MARGIN
    gate_paired = mean_drop > 0.0 and (drop_fraction or 0.0) >= 0.60
    gate_support_contact_scope = True

    hard_fail = not (gate_data and gate_semantic_source and gate_primary_signal and gate_gain and gate_shuffle and gate_wrong_t)
    geometry_dominance = not gate_geometry_dominance and not hard_fail
    overall = not hard_fail and not geometry_dominance and gate_paired

    return {
        "gate_data_integrity": {
            "pass": gate_data,
            "validation_errors": len(errors),
        },
        "gate_semantic_source_shortcuts": {
            "pass": gate_semantic_source,
            "max_allowed": NEAR_CHANCE_AUROC_MAX,
            "auroc": semantic_source_aucs,
            "best_semantic_source": best_semantic_source,
        },
        "gate_primary_predictive_signal": {
            "pass": gate_primary_signal,
            "primary_auroc_min": PRIMARY_AUROC_MIN,
            "primary_auroc": primary_aucs,
            "best_primary": best_primary,
        },
        "gate_gain_over_semantic_source": {
            "pass": gate_gain,
            "required_gain": PRIMARY_GAIN_OVER_SEMANTIC_SOURCE_MIN,
            "actual_gain": best_primary - best_semantic_source,
            "best_primary": best_primary,
            "best_semantic_source": best_semantic_source,
        },
        "gate_geometry_dominance_check": {
            "pass": gate_geometry_dominance,
            "margin": GEOMETRY_DOMINANCE_MARGIN,
            "actual_margin": best_primary - m4,
            "M4_geometry_only_G": m4,
            "best_primary": best_primary,
            "interpretation_if_fail": "geometry-only evidence explains the target nearly as well as factorized compatibility",
        },
        "gate_shuffle_controls": {
            "pass": gate_shuffle,
            "allowed_max": best_semantic_source + SHUFFLE_CONTROL_MARGIN,
            "C1_shuffled_G_global": c1,
            "C2_shuffled_G_within_predicate": c2,
            "best_shuffle": best_shuffle,
        },
        "gate_wrong_predicate_control": {
            "pass": gate_wrong_t,
            "allowed_max": best_semantic_source + SHUFFLE_CONTROL_MARGIN,
            "C3_wrong_predicate_family_control": c3,
        },
        "gate_group_contrast_score_direction": {
            "pass": gate_paired,
            "mean_positive_minus_negative": mean_drop,
            "positive_drop_fraction": drop_fraction,
            "note": "Diagnostic only because this target has mixed-size CV groups, not strict one-positive-one-negative pairs.",
        },
        "gate_family_scope": {
            "pass": gate_support_contact_scope,
            "relative_vertical_primary": True,
            "support_contact_diagnostic_rows": 88,
        },
        "overall_pass": overall,
        "geometry_dominance_diagnostic": geometry_dominance,
        "hard_fail": hard_fail,
        "overall_interpretation": (
            "stratum_repair_smoke_passed_controls"
            if overall
            else (
                "stratum_repair_smoke_geometry_dominance_diagnostic"
                if geometry_dominance
                else "stratum_repair_smoke_diagnostic_only_failed_controls"
            )
        ),
        "model_auroc_snapshot": {
            "M1_semantic_only_T": m1,
            "M2_source_only_Z": m2,
            "M3_semantic_source_TZ": m3,
            "M4_geometry_only_G": m4,
            "M5_TG_concat": m5,
            PRIMARY_MODEL: m6,
            FULL_MODEL: m7,
            "S1_predicate_x_class_pair_shortcut": s1,
            "S2_source_rank_score_shortcut": s2,
            "C1_shuffled_G_global": c1,
            "C2_shuffled_G_within_predicate": c2,
            "C3_wrong_predicate_family_control": c3,
        },
    }


def prediction_rows(rows: list[dict[str, Any]], predictions: dict[str, list[float]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        item = {
            "row_id": row.get("row_id"),
            "group_id": row.get("group_id"),
            "label": row.get("y_compatibility"),
            "family": row.get("T_e", {}).get("relation_family"),
            "predicate": row.get("T_e", {}).get("predicate_label"),
            "subject": row.get("T_e", {}).get("subject_class_label"),
            "object": row.get("T_e", {}).get("object_class_label"),
        }
        for model, scores in predictions.items():
            item[model] = scores[idx]
        out.append(item)
    return out


def error_cases(rows: list[dict[str, Any]], scores: list[float], max_cases: int = 40) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for row, score in zip(rows, scores):
        label = int(row["y_compatibility"])
        pred = 1 if score >= 0.5 else 0
        if pred == label:
            continue
        vector = raw_geometry_vector(row.get("G_e_raw", {}))
        cases.append(
            {
                "row_id": row.get("row_id"),
                "group_id": row.get("group_id"),
                "family": row.get("T_e", {}).get("relation_family"),
                "predicate": row.get("T_e", {}).get("predicate_label"),
                "subject": row.get("T_e", {}).get("subject_class_label"),
                "object": row.get("T_e", {}).get("object_class_label"),
                "label": label,
                "prediction": pred,
                "score": round(score, 6),
                "semantic_score_norm": row.get("Z_e_safe", {}).get("semantic_score_norm"),
                "semantic_rank": row.get("Z_e_safe", {}).get("semantic_rank"),
                "center_delta_z": vector.get("center_delta_z"),
                "normalized_center_delta_z": vector.get("normalized_center_delta_z"),
                "distance_3d": vector.get("distance_3d"),
                "projected_iou_xy": vector.get("projected_iou_xy"),
            }
        )
    return sorted(cases, key=lambda item: abs(float(item["score"]) - 0.5), reverse=True)[:max_cases]


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                keys.append(key)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(",".join(keys) + "\n")
        for row in rows:
            values = []
            for key in keys:
                value = row.get(key, "")
                text = json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
                values.append('"' + text.replace('"', '""') + '"')
            handle.write(",".join(values) + "\n")


def metrics_csv_rows(metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, metric in metrics.items():
        rows.append(
            {
                "model": name,
                "auroc": metric.get("auroc"),
                "auprc": metric.get("auprc"),
                "accuracy_at_0_5": metric.get("accuracy_at_0_5"),
                "balanced_accuracy_at_0_5": metric.get("balanced_accuracy_at_0_5"),
                "brier": metric.get("brier"),
                "ece_10": metric.get("ece_10"),
                "positive": metric.get("positive"),
                "negative": metric.get("negative"),
            }
        )
    return rows


def gate_csv_rows(gates: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in gates.items():
        if not isinstance(value, dict) or "pass" not in value:
            continue
        row = {"gate": key, "pass": value.get("pass")}
        for sub_key, sub_value in value.items():
            if sub_key != "pass":
                row[sub_key] = sub_value
        rows.append(row)
    return rows


def write_report(path: Path, summary: dict[str, Any], metrics: dict[str, Any], gates: dict[str, Any]) -> None:
    order = [
        "M0_intercept",
        "M1_semantic_only_T",
        "M2_source_only_Z",
        "M3_semantic_source_TZ",
        "M4_geometry_only_G",
        "M5_TG_concat",
        PRIMARY_MODEL,
        FULL_MODEL,
        "S1_predicate_x_class_pair_shortcut",
        "S2_source_rank_score_shortcut",
        "C1_shuffled_G_global",
        "C2_shuffled_G_within_predicate",
        "C3_wrong_predicate_family_control",
    ]
    lines = [
        "# Compatibility Dataset V3 Independent Validity Stratum Repair Smoke Runner",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"positive / negative = {summary['counts']['positive']} / {summary['counts']['negative']}",
        f"groups = {summary['counts']['groups']}",
        f"mixed_label_groups = {summary['counts']['mixed_label_groups']}",
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
            f"- semantic/source shortcuts: `{gates['gate_semantic_source_shortcuts']['pass']}`",
            f"- primary predictive signal: `{gates['gate_primary_predictive_signal']['pass']}`",
            f"- gain over semantic/source: `{gates['gate_gain_over_semantic_source']['pass']}`",
            f"- geometry dominance check: `{gates['gate_geometry_dominance_check']['pass']}`",
            f"- shuffled-G controls: `{gates['gate_shuffle_controls']['pass']}`",
            f"- wrong predicate control: `{gates['gate_wrong_predicate_control']['pass']}`",
            f"- group contrast score direction: `{gates['gate_group_contrast_score_direction']['pass']}`",
            "",
            "## Interpretation",
            "",
            "This runner tests the repaired independent-validity target using only sanitized",
            "`feature_blocks`. The key comparison is whether `T_e`-conditioned geometry",
            "compatibility (`M6`) or the full factorized representation (`M7`) beats semantic/source",
            "shortcuts without collapsing into a geometry-only result.",
            "",
            "The shuffled-G and wrong-predicate controls are inference-time corruptions of the clean",
            "primary model view. They check whether the model uses aligned predicate-geometry evidence,",
            "not just target construction residue.",
            "",
            "## Boundary",
            "",
            "- train-only grouped-CV hypothesis smoke",
            "- no validation/test usage",
            "- no paper-level evidence",
            "- no H001 artifact modification",
            "- support/contact rows remain diagnostic because only 88 rows are available here",
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
    metrics_by_family = group_metrics(rows, y, predictions, lambda row: str(row.get("T_e", {}).get("relation_family")))
    metrics_by_predicate = group_metrics(rows, y, predictions, lambda row: str(row.get("T_e", {}).get("predicate_label")))
    metrics_by_pair = group_metrics(rows, y, predictions, lambda row: subject_object_pair(row.get("T_e", {})))
    gates = gate_summary(metrics, drops, errors)

    status = STATUS_ERRORS
    if not errors:
        if gates["overall_pass"]:
            status = STATUS_PASSED
        elif gates["geometry_dominance_diagnostic"]:
            status = STATUS_GEOMETRY_DOMINANCE
        else:
            status = STATUS_DIAGNOSTIC

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO_REVIEW,
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
        "full_factorized_model": FULL_MODEL,
        "paper_evidence_allowed": False,
        "boundary": {
            "split": "train_internal_grouped_by_cv_group_id",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "raw_candidate_rows_used_as_model_input": False,
            "corruption_controls_train_on_clean_features": True,
            "only_sanitized_feature_blocks_used": True,
        },
        "key_metrics": {name: metrics[name] for name in sorted(metrics)},
        "gates": gates,
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "metrics": rel_path(args.output_dir / "metrics.json"),
            "metrics_csv": rel_path(args.output_dir / "metrics.csv"),
            "metrics_by_family": rel_path(args.output_dir / "metrics_by_family.json"),
            "paired_score_drop": rel_path(args.output_dir / "paired_score_drop.json"),
            "folds": rel_path(args.output_dir / "folds.json"),
            "predictions": rel_path(args.output_dir / "predictions.jsonl"),
            "error_cases": rel_path(args.output_dir / "error_cases_m6.jsonl"),
            "gate_results_csv": rel_path(args.output_dir / "gate_results.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "metrics.json", metrics)
    write_csv(args.output_dir / "metrics.csv", metrics_csv_rows(metrics))
    write_json(
        args.output_dir / "metrics_by_family.json",
        {"family": metrics_by_family, "predicate": metrics_by_predicate, "subject_object_pair": metrics_by_pair},
    )
    write_json(args.output_dir / "paired_score_drop.json", drops)
    write_json(args.output_dir / "folds.json", folds)
    write_jsonl(args.output_dir / "predictions.jsonl", prediction_rows(rows, predictions))
    write_jsonl(args.output_dir / "error_cases_m6.jsonl", error_cases(rows, predictions[PRIMARY_MODEL]))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "gate_results.csv", gate_csv_rows(gates))
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, metrics, gates)

    print(
        "status={status} rows={rows} M1={m1:.6f} M2={m2:.6f} M4={m4:.6f} M6={m6:.6f} "
        "M7={m7:.6f} overall={overall} next={next_todo}".format(
            status=status,
            rows=summary["counts"]["rows"],
            m1=value_or_zero(metrics, "M1_semantic_only_T"),
            m2=value_or_zero(metrics, "M2_source_only_Z"),
            m4=value_or_zero(metrics, "M4_geometry_only_G"),
            m6=value_or_zero(metrics, PRIMARY_MODEL),
            m7=value_or_zero(metrics, FULL_MODEL),
            overall=gates["overall_interpretation"],
            next_todo=NEXT_TODO_REVIEW,
        )
    )


if __name__ == "__main__":
    main()
