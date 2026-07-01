#!/usr/bin/env python3
"""Run train-only grouped-CV smoke for R6 supported-by decomposition."""

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
from smoke_baseline_runner_v1 import auroc, multiclass_metrics


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_plan"
DEFAULT_HIDDEN_MANIFEST = H2_ROOT / "artifacts/route_specific_targets/r6_superordinate_support/hidden_manifest.jsonl"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_supported_by_decomposition_smoke_runner"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_supported_by_decomposition_smoke_runner"
EXPECTED_ROW_SCHEMA = "h002_r6_supported_by_decomposition_runner_ready_view_v1"
EXPECTED_BLOCKS = {"G_e_mesh_pose_contact", "Q_e", "T_e"}

SCHEMA_VERSION = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_runner_v1"
STATUS_ERRORS = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_runner_input_errors"
STATUS_PROMISING = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_runner_promising_diagnostic"
STATUS_Q_OBSERVABILITY_DIAGNOSTIC = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_runner_q_observability_diagnostic"
STATUS_DIAGNOSTIC = "h002_compatibility_dataset_v3_supported_by_decomposition_smoke_runner_diagnostic_only_failed_controls"

NEXT_TODO_REVIEW = "compatibility_dataset_v3_supported_by_decomposition_smoke_result_review"
NEXT_TODO_FAILURE = "compatibility_dataset_v3_supported_by_decomposition_failure_analysis_after_smoke_runner"

PRIMARY_MODEL = "M6_TGQ_factorized_route"
PRIMARY_OBS_AUROC_MIN = 0.80
PRIMARY_REL_AUROC_MIN = 0.65
PRIMARY_GAIN_MIN = 0.03
MEDIUM_SHORTCUT_MAX = 0.90
SHUFFLED_MARGIN = 0.05
Q_ONLY_REL_MAX = 0.75

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--hidden-manifest", type=Path, default=DEFAULT_HIDDEN_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=5)
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
    if not fields:
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


def normalize_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        rows.append(
            {
                "G_e_mesh_pose_contact": block(raw, "G_e_mesh_pose_contact"),
                "Q_e": block(raw, "Q_e"),
                "T_e": block(raw, "T_e"),
                "group_id": raw.get("split_metadata", {}).get("cv_group_id"),
                "row_id": raw.get("row_id"),
                "schema_version": raw.get("schema_version"),
                "split": raw.get("split"),
                "target_decomposition_id": raw.get("target_decomposition_id"),
                "target_decomposition_label": raw.get("target_decomposition_label"),
                "target_p_obs_y": raw.get("target_p_obs_y"),
                "target_p_rel_3way_id": raw.get("target_p_rel_3way_id"),
                "target_p_rel_3way_label": raw.get("target_p_rel_3way_label"),
                "target_p_rel_binary_y": raw.get("target_p_rel_binary_y"),
            }
        )
    return rows


def subject_object_pair(t: dict[str, Any]) -> str:
    return f"{t.get('subject_class_text')}|{t.get('object_class_text')}"


def numeric_block_features(prefix: str, block_data: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, value in sorted(block_data.items()):
        if isinstance(value, bool):
            out[f"{prefix}.{key}"] = 1.0 if value else 0.0
            continue
        if isinstance(value, (int, float)) or value is None or value == "":
            out[f"{prefix}.{key}"] = safe_float(value, 0.0)
            out[f"{prefix}.{key}.missing"] = 1.0 if value is None or value == "" else 0.0
    return out


def t_features_from_dict(t: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    out.update(one_hot("T.family", t.get("predicate_family")))
    out.update(one_hot("T.predicate", t.get("predicate_label")))
    out.update(one_hot("T.subject", t.get("subject_class_text")))
    out.update(one_hot("T.object", t.get("object_class_text")))
    out.update(one_hot("T.subject_object", subject_object_pair(t)))
    return out


def t_features(row: dict[str, Any]) -> dict[str, float]:
    return t_features_from_dict(row.get("T_e", {}))


def class_pair_features(row: dict[str, Any]) -> dict[str, float]:
    t = row.get("T_e", {})
    out: dict[str, float] = {}
    out.update(one_hot("T.subject", t.get("subject_class_text")))
    out.update(one_hot("T.object", t.get("object_class_text")))
    out.update(one_hot("T.subject_object", subject_object_pair(t)))
    return out


def g_features_from_dict(g: dict[str, Any]) -> dict[str, float]:
    return numeric_block_features("G", g)


def q_features_from_dict(q: dict[str, Any]) -> dict[str, float]:
    out = numeric_block_features("Q", q)
    out.update(one_hot("Q.evidence_axis", q.get("evidence_axis")))
    out.update(one_hot("Q.observability_status", q.get("observability_status")))
    out.update(one_hot("Q.missing_fields", tuple(q.get("missing_g_e_fields") or [])))
    return out


def g_features(row: dict[str, Any]) -> dict[str, float]:
    return g_features_from_dict(row.get("G_e_mesh_pose_contact", {}))


def q_features(row: dict[str, Any]) -> dict[str, float]:
    return q_features_from_dict(row.get("Q_e", {}))


def tg_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), g_features(row))


def gq_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(g_features(row), q_features(row))


def tgq_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), g_features(row), q_features(row))


def single_g_best_proxy_features(row: dict[str, Any]) -> dict[str, float]:
    g = row.get("G_e_mesh_pose_contact", {})
    return {
        "G.center_delta_z": safe_float(g.get("center_delta_z"), 0.0),
        "G.obb_contact_likelihood_proxy": safe_float(g.get("obb_contact_likelihood_proxy"), 0.0),
        "G.support_area_proxy": safe_float(g.get("support_area_proxy"), 0.0),
        "G.xy_overlap_min_ratio": safe_float(g.get("xy_overlap_min_ratio"), 0.0),
    }


def shifted_map(
    rows: list[dict[str, Any]],
    block_names: tuple[str, ...],
    group_fn: Callable[[dict[str, Any]], str] | None = None,
) -> dict[str, dict[str, dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    if group_fn is None:
        groups["__all__"] = list(rows)
    else:
        for row in rows:
            groups[group_fn(row)].append(row)
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for group_rows in groups.values():
        ordered = sorted(group_rows, key=lambda row: str(row.get("row_id")))
        if len(ordered) <= 1:
            for row in ordered:
                out[str(row["row_id"])] = {name: dict(row.get(name, {})) for name in block_names}
            continue
        shift = max(1, len(ordered) // 2 + 1)
        for idx, row in enumerate(ordered):
            donor = ordered[(idx + shift) % len(ordered)]
            if donor.get("group_id") == row.get("group_id"):
                donor = ordered[(idx + shift + 1) % len(ordered)]
            out[str(row["row_id"])] = {name: dict(donor.get(name, {})) for name in block_names}
    return out


def shuffled_g_tgq_features(row: dict[str, Any], g_map: dict[str, dict[str, dict[str, Any]]]) -> dict[str, float]:
    donor = g_map[str(row["row_id"])]
    return merge_features(t_features(row), g_features_from_dict(donor.get("G_e_mesh_pose_contact", {})), q_features(row))


def shuffled_q_tgq_features(row: dict[str, Any], q_map: dict[str, dict[str, dict[str, Any]]]) -> dict[str, float]:
    donor = q_map[str(row["row_id"])]
    return merge_features(t_features(row), g_features(row), q_features_from_dict(donor.get("Q_e", {})))


def model_feature_fns(rows: list[dict[str, Any]]) -> dict[str, tuple[FeatureFn, FeatureFn]]:
    global_g = shifted_map(rows, ("G_e_mesh_pose_contact",))
    within_class_pair_g = shifted_map(
        rows,
        ("G_e_mesh_pose_contact",),
        lambda row: subject_object_pair(row.get("T_e", {})),
    )
    global_q = shifted_map(rows, ("Q_e",))
    return {
        "M0_prior": (lambda row: {}, lambda row: {}),
        "M1_T_class_only": (t_features, t_features),
        "M2_G_geometry_only": (g_features, g_features),
        "M3_Q_observability_only": (q_features, q_features),
        "M4_TG_concat": (tg_features, tg_features),
        "M5_GQ_route": (gq_features, gq_features),
        PRIMARY_MODEL: (tgq_features, tgq_features),
        "S1_subject_object_class_pair": (class_pair_features, class_pair_features),
        "S2_single_G_e_best_feature": (single_g_best_proxy_features, single_g_best_proxy_features),
        "S3_Q_only_for_p_rel": (q_features, q_features),
        "C1_shuffled_G_global": (tgq_features, lambda row: shuffled_g_tgq_features(row, global_g)),
        "C2_shuffled_G_within_class_pair": (tgq_features, lambda row: shuffled_g_tgq_features(row, within_class_pair_g)),
        "C3_shuffled_Q_global": (tgq_features, lambda row: shuffled_q_tgq_features(row, global_q)),
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


def task_rows(rows: list[dict[str, Any]], task: str) -> tuple[list[dict[str, Any]], list[int] | list[str]]:
    if task == "T0_decomposition_4way":
        return rows, [str(row["target_decomposition_label"]) for row in rows]
    if task == "T1_p_obs_binary":
        return rows, [int(row["target_p_obs_y"]) for row in rows]
    observable = [row for row in rows if row.get("target_p_rel_binary_y") is not None]
    if task == "T2_p_rel_binary_observable":
        return observable, [int(row["target_p_rel_binary_y"]) for row in observable]
    if task == "T3_p_rel_3way_observable":
        return observable, [str(row["target_p_rel_3way_label"]) for row in observable]
    raise ValueError(f"unknown task: {task}")


def class_scores_to_preds(score_by_class: dict[str, list[float]], classes: list[str]) -> list[str]:
    n = len(next(iter(score_by_class.values()))) if score_by_class else 0
    preds: list[str] = []
    for idx in range(n):
        preds.append(max(classes, key=lambda klass: score_by_class[klass][idx]))
    return preds


def one_vs_rest_metrics(labels: list[str], score_by_class: dict[str, list[float]], classes: list[str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    aucs: list[float] = []
    for klass in classes:
        y = [1 if label == klass else 0 for label in labels]
        score = score_by_class[klass]
        auc = auroc(y, score)
        out[klass] = auc
        if auc is not None:
            aucs.append(float(auc))
    return {
        "macro_one_vs_rest_auroc": sum(aucs) / max(len(aucs), 1) if aucs else None,
        "one_vs_rest_auroc": out,
    }


def train_eval_multiclass_cv(
    rows: list[dict[str, Any]],
    labels: list[str],
    feature_fn: FeatureFn,
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> dict[str, Any]:
    classes = sorted(set(labels))
    folds = make_folds(rows, "task_a", fold_count)
    score_by_class = {klass: [0.0] * len(rows) for klass in classes}
    fold_summaries: list[dict[str, Any]] = []
    for fold_idx, test_indices in enumerate(folds):
        test_set = set(test_indices)
        train_indices = [idx for idx in range(len(rows)) if idx not in test_set]
        train_feats = [feature_fn(rows[idx]) for idx in train_indices]
        for klass in classes:
            y_train = [1 if labels[idx] == klass else 0 for idx in train_indices]
            if len(set(y_train)) < 2:
                prior = sum(y_train) / max(len(y_train), 1)
                for idx in test_indices:
                    score_by_class[klass][idx] = prior
                continue
            model = train_logistic(train_feats, y_train, epochs=epochs, lr=lr, l2=l2)
            for idx in test_indices:
                score_by_class[klass][idx] = model.predict_one(feature_fn(rows[idx]))
        fold_summaries.append(
            {
                "classes": classes,
                "fold": fold_idx,
                "mode": "one_vs_rest_logistic",
                "test_rows": len(test_indices),
                "train_rows": len(train_indices),
            }
        )
    preds = class_scores_to_preds(score_by_class, classes)
    metrics = multiclass_metrics(labels, preds)
    metrics.update(one_vs_rest_metrics(labels, score_by_class, classes))
    return {"folds": fold_summaries, "metrics": metrics, "pred_labels": preds, "score_by_class": score_by_class}


def eval_binary_models(
    rows: list[dict[str, Any]],
    labels: list[int],
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[dict[str, Any], dict[str, list[float]], dict[str, Any]]:
    metrics: dict[str, Any] = {}
    predictions: dict[str, list[float]] = {}
    folds: dict[str, Any] = {}
    for name, (train_fn, eval_fn) in model_feature_fns(rows).items():
        result = train_eval_cv_dual(rows, labels, train_fn, eval_fn, fold_count, epochs, lr, l2)
        metrics[name] = result["metrics"]
        predictions[name] = result["predictions"]
        folds[name] = result["folds"]
    return metrics, predictions, folds


def eval_multiclass_models(
    rows: list[dict[str, Any]],
    labels: list[str],
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[dict[str, Any], dict[str, list[str]], dict[str, Any], dict[str, Any]]:
    metrics: dict[str, Any] = {}
    pred_labels: dict[str, list[str]] = {}
    score_by_class: dict[str, Any] = {}
    folds: dict[str, Any] = {}
    allowed_models = [
        "M0_prior",
        "M1_T_class_only",
        "M2_G_geometry_only",
        "M3_Q_observability_only",
        "M4_TG_concat",
        "M5_GQ_route",
        PRIMARY_MODEL,
        "S1_subject_object_class_pair",
        "S2_single_G_e_best_feature",
    ]
    model_fns = model_feature_fns(rows)
    for name in allowed_models:
        train_fn, _ = model_fns[name]
        result = train_eval_multiclass_cv(rows, labels, train_fn, fold_count, epochs, lr, l2)
        metrics[name] = result["metrics"]
        pred_labels[name] = result["pred_labels"]
        score_by_class[name] = result["score_by_class"]
        folds[name] = result["folds"]
    return metrics, pred_labels, score_by_class, folds


def eval_task(
    rows: list[dict[str, Any]],
    labels: list[int] | list[str],
    task: str,
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> dict[str, Any]:
    if task in {"T1_p_obs_binary", "T2_p_rel_binary_observable"}:
        metrics, predictions, folds = eval_binary_models(rows, [int(label) for label in labels], fold_count, epochs, lr, l2)
        return {"folds": folds, "metrics": metrics, "predictions": predictions, "task_type": "binary"}
    metrics, pred_labels, score_by_class, folds = eval_multiclass_models(rows, [str(label) for label in labels], fold_count, epochs, lr, l2)
    return {
        "folds": folds,
        "metrics": metrics,
        "pred_labels": pred_labels,
        "score_by_class": score_by_class,
        "task_type": "multiclass",
    }


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("group_id"))].append(str(row.get("target_decomposition_label")))
    return {
        "decomposition_label_counts": dict(sorted(Counter(str(row["target_decomposition_label"]) for row in rows).items())),
        "groups": len(groups),
        "mixed_label_groups": sum(1 for vals in groups.values() if len(set(vals)) > 1),
        "p_obs_counts": dict(sorted(Counter(int(row["target_p_obs_y"]) for row in rows).items())),
        "p_rel_3way_counts": dict(sorted(Counter(str(row["target_p_rel_3way_label"]) for row in rows if row["target_p_rel_3way_label"] is not None).items())),
        "p_rel_binary_counts": dict(sorted(Counter(int(row["target_p_rel_binary_y"]) for row in rows if row["target_p_rel_binary_y"] is not None).items())),
        "rows": len(rows),
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
    if counts["rows"] != 320:
        errors.append({"error_type": "unexpected_row_count", **counts})
    if counts["decomposition_label_counts"] != {"abstain": 80, "accept_broad_support": 80, "reject_no_support": 80, "relabel_to_subtype": 80}:
        errors.append({"error_type": "unexpected_decomposition_counts", **counts})
    if counts["p_obs_counts"] != {0: 80, 1: 240}:
        errors.append({"error_type": "unexpected_p_obs_counts", **counts})
    if counts["p_rel_binary_counts"] != {0: 80, 1: 160}:
        errors.append({"error_type": "unexpected_p_rel_binary_counts", **counts})
    if counts["p_rel_3way_counts"] != {"accept_broad_support": 80, "reject_no_support": 80, "relabel_to_subtype": 80}:
        errors.append({"error_type": "unexpected_p_rel_3way_counts", **counts})

    for raw, row in zip(raw_rows, rows):
        row_id = row.get("row_id")
        if raw.get("schema_version") != EXPECTED_ROW_SCHEMA:
            errors.append({"error_type": "unexpected_row_schema", "row_id": row_id, "actual": raw.get("schema_version")})
        actual_blocks = set(raw.get("feature_blocks", {}))
        if actual_blocks != EXPECTED_BLOCKS:
            errors.append({"error_type": "unexpected_feature_blocks", "row_id": row_id, "actual": sorted(actual_blocks)})
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_id": row_id})
    return errors


def value_or_zero(metrics: dict[str, Any], model: str, key: str = "auroc") -> float:
    value = metrics.get(model, {}).get(key)
    return 0.0 if value is None else float(value)


def gate_summary(results_by_task: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    t1 = results_by_task["T1_p_obs_binary"]["metrics"]
    t2 = results_by_task["T2_p_rel_binary_observable"]["metrics"]
    t3 = results_by_task["T3_p_rel_3way_observable"]["metrics"]

    t1_primary = value_or_zero(t1, PRIMARY_MODEL)
    t1_q = value_or_zero(t1, "M3_Q_observability_only")
    t2_primary = value_or_zero(t2, PRIMARY_MODEL)
    t2_t = value_or_zero(t2, "M1_T_class_only")
    t2_g = value_or_zero(t2, "M2_G_geometry_only")
    t2_q = value_or_zero(t2, "M3_Q_observability_only")
    t2_tg = value_or_zero(t2, "M4_TG_concat")
    t2_gq = value_or_zero(t2, "M5_GQ_route")
    t2_s1 = value_or_zero(t2, "S1_subject_object_class_pair")
    t2_s2 = value_or_zero(t2, "S2_single_G_e_best_feature")
    t2_shuffle_g = max(value_or_zero(t2, "C1_shuffled_G_global"), value_or_zero(t2, "C2_shuffled_G_within_class_pair"))
    t2_shuffle_q = value_or_zero(t2, "C3_shuffled_Q_global")
    t3_primary = t3.get(PRIMARY_MODEL, {}).get("macro_one_vs_rest_auroc") or 0.0

    component_best = max(t2_t, t2_g, t2_q, t2_tg, t2_gq)
    shortcut_best = max(t2_s1, t2_s2)
    p_obs_pass = t1_primary >= PRIMARY_OBS_AUROC_MIN
    p_rel_pass = t2_primary >= PRIMARY_REL_AUROC_MIN
    p_rel_gain = (t2_primary - component_best) >= PRIMARY_GAIN_MIN
    q_boundary = t2_q <= Q_ONLY_REL_MAX
    shortcut_boundary = max(shortcut_best, t2_g, t2_q) <= MEDIUM_SHORTCUT_MAX
    shuffled_g_pass = t2_shuffle_g <= max(t2_primary - SHUFFLED_MARGIN, component_best + SHUFFLED_MARGIN)
    shuffled_q_pass = t2_shuffle_q <= max(t2_primary, component_best) + SHUFFLED_MARGIN
    diagnostic_q_obs = t1_q >= t1_primary - 0.02 and p_obs_pass
    overall_promising = (
        len(errors) == 0
        and p_obs_pass
        and p_rel_pass
        and q_boundary
        and shortcut_boundary
        and shuffled_g_pass
        and shuffled_q_pass
    )
    return {
        "gate_data_integrity": {"pass": len(errors) == 0, "validation_errors": len(errors)},
        "gate_p_obs_signal": {"pass": p_obs_pass, "primary_auroc": t1_primary, "q_only_auroc": t1_q, "min_required": PRIMARY_OBS_AUROC_MIN},
        "gate_p_rel_signal": {"pass": p_rel_pass, "primary_auroc": t2_primary, "min_required": PRIMARY_REL_AUROC_MIN},
        "gate_p_rel_gain": {
            "actual_gain": t2_primary - component_best,
            "best_component": component_best,
            "pass": p_rel_gain,
            "required_gain": PRIMARY_GAIN_MIN,
        },
        "gate_q_boundary_on_observable_p_rel": {"M3_Q_observability_only": t2_q, "max_allowed": Q_ONLY_REL_MAX, "pass": q_boundary},
        "gate_shortcut_boundary": {"best_shortcut_or_single_factor": max(shortcut_best, t2_g, t2_q), "max_allowed": MEDIUM_SHORTCUT_MAX, "pass": shortcut_boundary},
        "gate_shuffled_G_degradation": {"best_shuffled_G": t2_shuffle_g, "pass": shuffled_g_pass},
        "gate_shuffled_Q_boundary": {"C3_shuffled_Q_global": t2_shuffle_q, "pass": shuffled_q_pass},
        "model_auroc_snapshot": {
            "T1_p_obs_M6": t1_primary,
            "T1_p_obs_Q_only": t1_q,
            "T2_p_rel_M1_T": t2_t,
            "T2_p_rel_M2_G": t2_g,
            "T2_p_rel_M3_Q": t2_q,
            "T2_p_rel_M4_TG": t2_tg,
            "T2_p_rel_M5_GQ": t2_gq,
            "T2_p_rel_M6_TGQ": t2_primary,
            "T2_p_rel_S1_class_pair": t2_s1,
            "T2_p_rel_S2_single_G": t2_s2,
            "T2_p_rel_shuffled_G": t2_shuffle_g,
            "T2_p_rel_shuffled_Q": t2_shuffle_q,
            "T3_p_rel_3way_M6_macro_ovr_auroc": t3_primary,
        },
        "overall_interpretation": (
            "r6_supported_by_smoke_promising_diagnostic"
            if overall_promising and p_rel_gain
            else "r6_supported_by_smoke_q_observability_diagnostic"
            if diagnostic_q_obs and not p_rel_gain
            else "r6_supported_by_smoke_diagnostic_only_failed_controls"
        ),
        "overall_promising": overall_promising and p_rel_gain,
    }


def hidden_probe_features(hidden: dict[str, Any], mode: str) -> dict[str, float]:
    out: dict[str, float] = {}
    if mode == "source_rank":
        out["hidden.semantic_score_norm"] = safe_float(hidden.get("semantic_score_norm"), 0.0)
        out["hidden.semantic_score_raw"] = safe_float(hidden.get("semantic_score_raw"), 0.0)
        out["hidden.rank_inv"] = 1.0 / (1.0 + max(safe_float(hidden.get("semantic_rank"), 9999.0), 0.0))
        out["hidden.p_geom_valid"] = safe_float(hidden.get("p_geom_valid"), 0.5)
        out.update(one_hot("hidden.rank_band", hidden.get("rank_band")))
        return out
    for key in ["label_match_status", "candidate_role", "machine_hint", "matched_predicates", "evidence_reason", "subtype_relabel_target"]:
        out.update(one_hot(f"hidden.{key}", hidden.get(key)))
    return out


def eval_hidden_binary_probe(
    rows: list[dict[str, Any]],
    labels: list[int],
    hidden_by_id: dict[str, dict[str, Any]],
    mode: str,
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> dict[str, Any]:
    def feat(row: dict[str, Any]) -> dict[str, float]:
        return hidden_probe_features(hidden_by_id.get(str(row.get("row_id")), {}), mode)

    return train_eval_cv_dual(rows, labels, feat, feat, fold_count, epochs, lr, l2)


def hidden_probe_audit(
    rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> dict[str, Any]:
    hidden_by_id = {str(row.get("row_id")): row for row in hidden_rows}
    obs_rows, obs_labels = task_rows(rows, "T1_p_obs_binary")
    rel_rows, rel_labels = task_rows(rows, "T2_p_rel_binary_observable")
    assert isinstance(obs_labels, list) and isinstance(rel_labels, list)
    output: dict[str, Any] = {}
    for mode in ["source_rank", "construction"]:
        output[f"{mode}_p_obs"] = eval_hidden_binary_probe(obs_rows, [int(x) for x in obs_labels], hidden_by_id, mode, fold_count, epochs, lr, l2)["metrics"]
        output[f"{mode}_p_rel"] = eval_hidden_binary_probe(rel_rows, [int(x) for x in rel_labels], hidden_by_id, mode, fold_count, epochs, lr, l2)["metrics"]
    return output


def predictions_rows(task: str, rows: list[dict[str, Any]], result: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if result["task_type"] == "binary":
        labels = [int(x) for x in task_rows(rows, task)[1]]
        task_specific_rows = task_rows(rows, task)[0]
        for idx, row in enumerate(task_specific_rows):
            item = {
                "group_id": row.get("group_id"),
                "label": labels[idx],
                "row_id": row.get("row_id"),
                "target_decomposition_label": row.get("target_decomposition_label"),
                "task": task,
            }
            for model, scores in result["predictions"].items():
                item[model] = scores[idx]
            out.append(item)
    return out


def error_cases(rows: list[dict[str, Any]], scores: list[float], max_cases: int = 40) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    rel_rows, rel_labels_any = task_rows(rows, "T2_p_rel_binary_observable")
    rel_labels = [int(x) for x in rel_labels_any]
    for row, label, score in zip(rel_rows, rel_labels, scores):
        pred = 1 if score >= 0.5 else 0
        if pred == label:
            continue
        g = row.get("G_e_mesh_pose_contact", {})
        q = row.get("Q_e", {})
        t = row.get("T_e", {})
        cases.append(
            {
                "center_delta_z": g.get("center_delta_z"),
                "geometry_contradiction": q.get("geometry_contradiction"),
                "label": label,
                "object": t.get("object_class_text"),
                "observability_status": q.get("observability_status"),
                "prediction": pred,
                "row_id": row.get("row_id"),
                "score": round(score, 6),
                "subject": t.get("subject_class_text"),
                "support_area_proxy": g.get("support_area_proxy"),
                "target_decomposition_label": row.get("target_decomposition_label"),
                "xy_overlap_min_ratio": g.get("xy_overlap_min_ratio"),
            }
        )
    return sorted(cases, key=lambda item: abs(float(item["score"]) - 0.5), reverse=True)[:max_cases]


def write_report(path: Path, summary: dict[str, Any], results_by_task: dict[str, Any], hidden: dict[str, Any], gates: dict[str, Any]) -> None:
    t1 = results_by_task["T1_p_obs_binary"]["metrics"]
    t2 = results_by_task["T2_p_rel_binary_observable"]["metrics"]
    t3 = results_by_task["T3_p_rel_3way_observable"]["metrics"]
    lines = [
        "# H002 R6 Supported-By Decomposition Smoke Runner",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"validation_errors = {summary['validation_errors']}",
        f"overall = {gates['overall_interpretation']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## T1 p_obs Binary",
        "",
        "| Model | AUROC | AUPRC | Accuracy | Balanced Acc. | ECE-10 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in ["M1_T_class_only", "M2_G_geometry_only", "M3_Q_observability_only", "M5_GQ_route", PRIMARY_MODEL]:
        metric = t1[name]
        lines.append(
            f"| `{name}` | {metric.get('auroc')} | {metric.get('auprc')} | {metric.get('accuracy_at_0_5')} | "
            f"{metric.get('balanced_accuracy_at_0_5')} | {metric.get('ece_10')} |"
        )
    lines.extend(["", "## T2 Observable p_rel Binary", "", "| Model | AUROC | AUPRC | Accuracy | Balanced Acc. | ECE-10 |", "| --- | ---: | ---: | ---: | ---: | ---: |"])
    for name in [
        "M1_T_class_only",
        "M2_G_geometry_only",
        "M3_Q_observability_only",
        "M4_TG_concat",
        "M5_GQ_route",
        PRIMARY_MODEL,
        "S1_subject_object_class_pair",
        "S2_single_G_e_best_feature",
        "C1_shuffled_G_global",
        "C2_shuffled_G_within_class_pair",
        "C3_shuffled_Q_global",
    ]:
        metric = t2[name]
        lines.append(
            f"| `{name}` | {metric.get('auroc')} | {metric.get('auprc')} | {metric.get('accuracy_at_0_5')} | "
            f"{metric.get('balanced_accuracy_at_0_5')} | {metric.get('ece_10')} |"
        )
    lines.extend(
        [
            "",
            "## T3 Observable p_rel 3-Way",
            "",
            f"- `M6_TGQ_factorized_route` macro one-vs-rest AUROC: `{t3[PRIMARY_MODEL].get('macro_one_vs_rest_auroc')}`",
            f"- `M6_TGQ_factorized_route` macro F1: `{t3[PRIMARY_MODEL].get('macro_f1')}`",
            "",
            "## Hidden Audit Probes",
            "",
            f"- source/rank/p_geom on p_rel AUROC: `{hidden['source_rank_p_rel'].get('auroc')}`",
            f"- construction fields on p_rel AUROC: `{hidden['construction_p_rel'].get('auroc')}`",
            "",
            "## Gates",
            "",
            f"- data integrity: `{gates['gate_data_integrity']['pass']}`",
            f"- p_obs signal: `{gates['gate_p_obs_signal']['pass']}`",
            f"- p_rel signal: `{gates['gate_p_rel_signal']['pass']}`",
            f"- p_rel gain: `{gates['gate_p_rel_gain']['pass']}`",
            f"- Q boundary on observable p_rel: `{gates['gate_q_boundary_on_observable_p_rel']['pass']}`",
            f"- shortcut boundary: `{gates['gate_shortcut_boundary']['pass']}`",
            f"- shuffled-G degradation: `{gates['gate_shuffled_G_degradation']['pass']}`",
            f"- shuffled-Q boundary: `{gates['gate_shuffled_Q_boundary']['pass']}`",
            "",
            "## Interpretation",
            "",
            "This is a train-only hypothesis smoke. `Q_e` is allowed to dominate `p_obs`,",
            "but if `Q_e` alone solves observable `p_rel`, the result must be interpreted",
            "as an observability/target-construction diagnostic rather than a reliability",
            "claim. Hidden source and construction probes are audit-only and not model inputs.",
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
    hidden_rows = read_jsonl(args.hidden_manifest) if args.hidden_manifest.exists() else []
    errors = validate(args.plan_dir, plan_summary, plan, manifest, raw_rows, rows)

    results_by_task: dict[str, Any] = {}
    for task in ["T0_decomposition_4way", "T1_p_obs_binary", "T2_p_rel_binary_observable", "T3_p_rel_3way_observable"]:
        task_specific_rows, labels = task_rows(rows, task)
        results_by_task[task] = eval_task(task_specific_rows, labels, task, args.folds, args.epochs, args.lr, args.l2)

    hidden_probe_results = hidden_probe_audit(rows, hidden_rows, args.folds, args.epochs, args.lr, args.l2) if hidden_rows else {}
    gates = gate_summary(results_by_task, errors)

    if errors:
        status = STATUS_ERRORS
        next_todo = NEXT_TODO_FAILURE
    elif gates["overall_promising"]:
        status = STATUS_PROMISING
        next_todo = NEXT_TODO_REVIEW
    elif gates["overall_interpretation"] == "r6_supported_by_smoke_q_observability_diagnostic":
        status = STATUS_Q_OBSERVABILITY_DIAGNOSTIC
        next_todo = NEXT_TODO_REVIEW
    else:
        status = STATUS_DIAGNOSTIC
        next_todo = NEXT_TODO_FAILURE

    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "hidden_probes_model_input_allowed": False,
            "paper_evidence_allowed": False,
            "split": "train_internal_grouped_by_cv_group_id",
            "test_usage": False,
            "validation_usage": False,
        },
        "counts": count_summary(rows),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "epochs": args.epochs,
        "folds": args.folds,
        "gates": gates,
        "hidden_probe_results": hidden_probe_results,
        "input_file": rel_path(input_path),
        "input_sha256": sha256_file(input_path),
        "key_metrics": {
            task: results_by_task[task]["metrics"]
            for task in sorted(results_by_task)
        },
        "l2": args.l2,
        "learned_smoke_executed": True,
        "lr": args.lr,
        "next_todo": next_todo,
        "output_paths": {
            "error_cases_t2_m6": rel_path(args.output_dir / "error_cases_t2_m6.jsonl"),
            "folds": rel_path(args.output_dir / "folds.json"),
            "gate_results": rel_path(args.output_dir / "gate_results.json"),
            "hidden_probe_results": rel_path(args.output_dir / "hidden_probe_results.json"),
            "metrics_by_task": rel_path(args.output_dir / "metrics_by_task.json"),
            "predictions_t1": rel_path(args.output_dir / "predictions_t1.jsonl"),
            "predictions_t2": rel_path(args.output_dir / "predictions_t2.jsonl"),
            "report": rel_path(args.output_dir / "report.md"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "output_root": rel_path(args.output_dir),
        "paper_evidence_allowed": False,
        "plan_root": rel_path(args.plan_dir),
        "primary_model": PRIMARY_MODEL,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "validation_errors": len(errors),
    }

    write_json(args.output_dir / "metrics_by_task.json", {task: results_by_task[task]["metrics"] for task in sorted(results_by_task)})
    write_json(args.output_dir / "folds.json", {task: results_by_task[task]["folds"] for task in sorted(results_by_task)})
    write_json(args.output_dir / "gate_results.json", gates)
    write_json(args.output_dir / "hidden_probe_results.json", hidden_probe_results)
    write_jsonl(args.output_dir / "predictions_t1.jsonl", predictions_rows("T1_p_obs_binary", rows, results_by_task["T1_p_obs_binary"]))
    write_jsonl(args.output_dir / "predictions_t2.jsonl", predictions_rows("T2_p_rel_binary_observable", rows, results_by_task["T2_p_rel_binary_observable"]))
    write_jsonl(args.output_dir / "error_cases_t2_m6.jsonl", error_cases(rows, results_by_task["T2_p_rel_binary_observable"]["predictions"][PRIMARY_MODEL]))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, results_by_task, hidden_probe_results, gates)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
