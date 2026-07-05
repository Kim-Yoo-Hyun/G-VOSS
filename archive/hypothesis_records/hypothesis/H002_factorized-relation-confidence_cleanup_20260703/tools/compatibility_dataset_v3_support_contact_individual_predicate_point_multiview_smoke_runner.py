#!/usr/bin/env python3
"""Run point/multiview support-contact individual-predicate smoke models."""

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
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan_ready"
)
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner"
EXPECTED_ROW_SCHEMA = "h002_support_contact_individual_predicate_point_multiview_runner_ready_view_v1"
EXPECTED_BLOCKS = {"G_e_contact_patch", "G_e_obb_baseline", "G_e_point_pose", "Q_e_observability", "T_e"}

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner_v1"
)
STATUS_ERRORS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner_input_errors"
)
STATUS_PASSED = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner_passed_controls"
)
STATUS_GEOMETRY_DOMINANCE = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner_geometry_dominance_diagnostic"
)
STATUS_DIAGNOSTIC = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner_diagnostic_only_failed_controls"
)

NEXT_TODO_REVIEW = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_result_review"
NEXT_TODO_FAILURE = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis"

PRIMARY_MODEL = "M8_TG_point_contact_interaction"
FULL_MODEL = "M9_TGQ_factorized_observability"
PRIMARY_AUROC_MIN = 0.70
SHORTCUT_AUROC_MAX = 0.70
PRIMARY_GAIN_OVER_COMPONENTS_MIN = 0.05
POINT_EXPANSION_GAIN_MIN = 0.03
GEOMETRY_DOMINANCE_MARGIN = 0.02
SHUFFLE_CONTROL_MARGIN = 0.05
WRONG_T_DEGRADE_MIN = 0.05

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]

FORBIDDEN_FEATURE_TOKENS = {
    "candidate_role",
    "construction",
    "directed_pair",
    "geometry_status",
    "h001",
    "hidden",
    "label_match",
    "machine_hint",
    "matched",
    "p_geom",
    "prediction_id",
    "queue",
    "rank",
    "route_name",
    "scan_id",
    "semantic_score",
    "source_score",
    "source_id",
    "source",
    "subgraph_id",
    "subject_id",
    "object_id",
    "target_source",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=220)
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
    return (REPO_ROOT / path).resolve()


def block(row: dict[str, Any], name: str) -> dict[str, Any]:
    return dict(row.get("feature_blocks", {}).get(name, {}))


def normalize_rows(raw_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in raw_rows:
        rows.append(
            {
                "G_e_contact_patch": block(raw, "G_e_contact_patch"),
                "G_e_obb_baseline": block(raw, "G_e_obb_baseline"),
                "G_e_point_pose": block(raw, "G_e_point_pose"),
                "Q_e_observability": block(raw, "Q_e_observability"),
                "T_e": block(raw, "T_e"),
                "group_id": raw.get("cv_group_id"),
                "row_id": raw.get("example_id") or raw.get("row_id"),
                "schema_version": raw.get("schema_version"),
                "split": raw.get("split"),
                "y_compatibility": int(raw.get("target_y")),
            }
        )
    return rows


def subject_object_pair(t: dict[str, Any]) -> str:
    return f"{t.get('subject_class_text')}|{t.get('object_class_text')}"


def numeric_block_features(prefix: str, block_data: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, value in sorted(block_data.items()):
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


def predicate_only_features(row: dict[str, Any]) -> dict[str, float]:
    return one_hot("T.predicate", row.get("T_e", {}).get("predicate_label"))


def class_pair_features(row: dict[str, Any]) -> dict[str, float]:
    t = row.get("T_e", {})
    out: dict[str, float] = {}
    out.update(one_hot("T.subject", t.get("subject_class_text")))
    out.update(one_hot("T.object", t.get("object_class_text")))
    out.update(one_hot("T.subject_object", subject_object_pair(t)))
    return out


def obb_features_from_dict(g: dict[str, Any]) -> dict[str, float]:
    return numeric_block_features("G_obb", g)


def point_pose_features_from_dict(g: dict[str, Any]) -> dict[str, float]:
    return numeric_block_features("G_point", g)


def contact_patch_features_from_dict(g: dict[str, Any]) -> dict[str, float]:
    return numeric_block_features("G_contact", g)


def q_features_from_dict(q: dict[str, Any]) -> dict[str, float]:
    return numeric_block_features("Q", q)


def obb_features(row: dict[str, Any]) -> dict[str, float]:
    return obb_features_from_dict(row.get("G_e_obb_baseline", {}))


def point_pose_features(row: dict[str, Any]) -> dict[str, float]:
    return point_pose_features_from_dict(row.get("G_e_point_pose", {}))


def contact_patch_features(row: dict[str, Any]) -> dict[str, float]:
    return contact_patch_features_from_dict(row.get("G_e_contact_patch", {}))


def point_contact_features_from_dict(point: dict[str, Any], contact: dict[str, Any]) -> dict[str, float]:
    return merge_features(point_pose_features_from_dict(point), contact_patch_features_from_dict(contact))


def point_contact_features(row: dict[str, Any]) -> dict[str, float]:
    return point_contact_features_from_dict(row.get("G_e_point_pose", {}), row.get("G_e_contact_patch", {}))


def q_features(row: dict[str, Any]) -> dict[str, float]:
    return q_features_from_dict(row.get("Q_e_observability", {}))


def predicate_flags(predicate: Any) -> tuple[float, float]:
    text = str(predicate)
    return (1.0 if text == "lying on" else 0.0, 1.0 if text == "standing on" else 0.0)


def safe_ratio(numerator: Any, denominator: Any) -> float:
    den = safe_float(denominator, 0.0)
    if abs(den) < 1e-8:
        return 0.0
    return safe_float(numerator, 0.0) / den


def support_pose_proxies(point: dict[str, Any], contact: dict[str, Any]) -> dict[str, float]:
    gap_abs = safe_float(contact.get("point_abs_surface_gap_subject_bottom_to_object_top"), 0.0)
    overlap = safe_float(contact.get("point_xy_overlap_min_ratio"), 0.0)
    overlap_subject = safe_float(contact.get("point_xy_overlap_subject_ratio"), 0.0)
    overlap_object = safe_float(contact.get("point_xy_overlap_object_ratio"), 0.0)
    contact_proxy = safe_float(contact.get("point_support_contact_likelihood_proxy"), 0.0)
    center_delta_z = safe_float(contact.get("point_center_delta_z"), 0.0)
    subject_flatness = safe_float(point.get("subject_flatness_proxy"), 0.0)
    object_flatness = safe_float(point.get("object_flatness_proxy"), 0.0)
    subject_vertical = safe_float(point.get("subject_vertical_extent_ratio"), 0.0)
    subject_horizontal = safe_float(point.get("subject_horizontal_extent_ratio"), 0.0)
    object_horizontal = safe_float(point.get("object_horizontal_extent_ratio"), 0.0)
    point_count_ratio = safe_ratio(point.get("subject_point_count"), point.get("object_point_count"))
    return {
        "proxy.center_delta_z": center_delta_z,
        "proxy.contact": contact_proxy,
        "proxy.inverse_gap": 1.0 / (1.0 + max(gap_abs, 0.0)),
        "proxy.object_flatness": object_flatness,
        "proxy.object_horizontal_extent": object_horizontal,
        "proxy.overlap": overlap,
        "proxy.overlap_object": overlap_object,
        "proxy.overlap_subject": overlap_subject,
        "proxy.point_count_ratio": point_count_ratio,
        "proxy.subject_flatness": subject_flatness,
        "proxy.subject_horizontal_extent": subject_horizontal,
        "proxy.subject_vertical_extent": subject_vertical,
    }


def compatibility_interactions_from_dict(
    t: dict[str, Any],
    point: dict[str, Any],
    contact: dict[str, Any],
) -> dict[str, float]:
    is_lying, is_standing = predicate_flags(t.get("predicate_label"))
    proxies = support_pose_proxies(point, contact)
    base = point_contact_features_from_dict(point, contact)
    out: dict[str, float] = {
        "C.is_lying": is_lying,
        "C.is_standing": is_standing,
    }
    for key, value in base.items():
        clean_key = key.replace(".", "_")
        out[f"C.lying_x_{clean_key}"] = is_lying * value
        out[f"C.standing_x_{clean_key}"] = is_standing * value
    for key, value in proxies.items():
        clean_key = key.replace("proxy.", "")
        out[f"C.lying_proxy_x_{clean_key}"] = is_lying * value
        out[f"C.standing_proxy_x_{clean_key}"] = is_standing * value
    out["C.lying_pose_proxy"] = is_lying * (
        proxies["proxy.subject_flatness"]
        + proxies["proxy.subject_horizontal_extent"]
        + proxies["proxy.overlap_subject"]
        + proxies["proxy.contact"]
    )
    out["C.standing_pose_proxy"] = is_standing * (
        proxies["proxy.subject_vertical_extent"]
        + proxies["proxy.object_flatness"]
        + proxies["proxy.overlap"]
        + proxies["proxy.inverse_gap"]
        + proxies["proxy.contact"]
    )
    out["C.shared_support_contact_proxy"] = (
        proxies["proxy.contact"]
        + proxies["proxy.overlap"]
        + proxies["proxy.inverse_gap"]
        + proxies["proxy.object_flatness"]
    )
    return out


def compatibility_interaction_features(row: dict[str, Any]) -> dict[str, float]:
    return compatibility_interactions_from_dict(
        row.get("T_e", {}),
        row.get("G_e_point_pose", {}),
        row.get("G_e_contact_patch", {}),
    )


def tg_obb_concat_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), obb_features(row))


def tg_point_contact_concat_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), point_contact_features(row))


def tg_point_contact_interaction_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_features(row), point_contact_features(row), compatibility_interaction_features(row))


def tgq_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(tg_point_contact_interaction_features(row), q_features(row))


def wrong_predicate(value: Any) -> str:
    if value == "lying on":
        return "standing on"
    if value == "standing on":
        return "lying on"
    return f"wrong_{value}"


def wrong_t(row: dict[str, Any]) -> dict[str, Any]:
    t = dict(row.get("T_e", {}))
    t["predicate_label"] = wrong_predicate(t.get("predicate_label"))
    t["predicate_text"] = t["predicate_label"]
    return t


def wrong_t_same_g_features(row: dict[str, Any]) -> dict[str, float]:
    t = wrong_t(row)
    point = row.get("G_e_point_pose", {})
    contact = row.get("G_e_contact_patch", {})
    return merge_features(
        t_features_from_dict(t),
        point_contact_features_from_dict(point, contact),
        compatibility_interactions_from_dict(t, point, contact),
    )


def stable_order(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: str(row.get("row_id")))


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
        ordered = stable_order(group_rows)
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


def shuffled_tg_point_contact_features(
    row: dict[str, Any],
    geometry_map: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, float]:
    t = row.get("T_e", {})
    donor = geometry_map[str(row["row_id"])]
    point = donor.get("G_e_point_pose", {})
    contact = donor.get("G_e_contact_patch", {})
    return merge_features(
        t_features(row),
        point_contact_features_from_dict(point, contact),
        compatibility_interactions_from_dict(t, point, contact),
    )


def shuffled_tgq_features(
    row: dict[str, Any],
    q_map: dict[str, dict[str, dict[str, Any]]],
) -> dict[str, float]:
    donor = q_map[str(row["row_id"])]
    return merge_features(tg_point_contact_interaction_features(row), q_features_from_dict(donor.get("Q_e_observability", {})))


def model_feature_fns(rows: list[dict[str, Any]]) -> dict[str, tuple[FeatureFn, FeatureFn]]:
    global_g = shifted_map(rows, ("G_e_point_pose", "G_e_contact_patch"))
    within_predicate_g = shifted_map(
        rows,
        ("G_e_point_pose", "G_e_contact_patch"),
        lambda row: str(row.get("T_e", {}).get("predicate_label")),
    )
    global_q = shifted_map(rows, ("Q_e_observability",))
    return {
        "M0_intercept": (lambda row: {}, lambda row: {}),
        "M1_semantic_only_T": (t_features, t_features),
        "M2_obb_geometry_only": (obb_features, obb_features),
        "M3_point_pose_only": (point_pose_features, point_pose_features),
        "M4_contact_patch_only": (contact_patch_features, contact_patch_features),
        "M5_point_contact_geometry": (point_contact_features, point_contact_features),
        "M6_TG_obb_concat": (tg_obb_concat_features, tg_obb_concat_features),
        "M7_TG_point_contact_concat": (tg_point_contact_concat_features, tg_point_contact_concat_features),
        PRIMARY_MODEL: (tg_point_contact_interaction_features, tg_point_contact_interaction_features),
        FULL_MODEL: (tgq_features, tgq_features),
        "S1_predicate_label_shortcut": (predicate_only_features, predicate_only_features),
        "S2_class_pair_shortcut": (class_pair_features, class_pair_features),
        "S3_quality_only_shortcut": (q_features, q_features),
        "C1_wrong_T_same_G": (tg_point_contact_interaction_features, wrong_t_same_g_features),
        "C2_shuffled_G_global": (
            tg_point_contact_interaction_features,
            lambda row: shuffled_tg_point_contact_features(row, global_g),
        ),
        "C3_shuffled_G_within_predicate": (
            tg_point_contact_interaction_features,
            lambda row: shuffled_tg_point_contact_features(row, within_predicate_g),
        ),
        "C4_shuffled_Q": (tgq_features, lambda row: shuffled_tgq_features(row, global_q)),
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


def brier(y: list[int], scores: list[float]) -> float:
    return sum((score - label) ** 2 for label, score in zip(y, scores)) / max(len(y), 1)


def augment_binary_metrics(y: list[int], scores: list[float]) -> dict[str, Any]:
    metrics = binary_metrics(y, scores)
    metrics["balanced_accuracy_at_0_5"] = balanced_accuracy(y, scores)
    metrics["brier"] = brier(y, scores)
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
    predicate_counts: Counter[str] = Counter()
    predicate_label_counts: Counter[str] = Counter()
    q_profile: Counter[str] = Counter()
    for row, label in zip(rows, y):
        groups[str(row.get("group_id"))].append(label)
        predicate = str(row.get("T_e", {}).get("predicate_label"))
        predicate_counts[predicate] += 1
        predicate_label_counts[f"{predicate}|{'positive' if label else 'negative'}"] += 1
        q = row.get("Q_e_observability", {})
        q_profile[
            f"sufficient={int(safe_float(q.get('q_e_state_sufficient'), 0.0))}|"
            f"limited={int(safe_float(q.get('q_e_state_limited'), 0.0))}|"
            f"uncertain={int(safe_float(q.get('q_e_state_uncertain'), 0.0))}"
        ] += 1
    return {
        "groups": len(groups),
        "mixed_label_groups": sum(1 for vals in groups.values() if len(set(vals)) > 1),
        "negative": len(y) - sum(y),
        "positive": sum(y),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "predicate_label_counts": dict(sorted(predicate_label_counts.items())),
        "q_profile": dict(sorted(q_profile.items())),
        "rows": len(rows),
        "single_label_groups": sum(1 for vals in groups.values() if len(set(vals)) == 1),
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
    if counts["rows"] != 640 or counts["positive"] != 320 or counts["negative"] != 320:
        errors.append({"error_type": "unexpected_counts", **counts})
    if counts["predicate_counts"] != {"lying on": 320, "standing on": 320}:
        errors.append({"error_type": "unexpected_predicate_counts", **counts})
    if counts["groups"] != 258 or counts["mixed_label_groups"] != 155:
        errors.append({"error_type": "unexpected_group_profile", **counts})

    for raw, row in zip(raw_rows, rows):
        row_id = row.get("row_id")
        if raw.get("schema_version") != EXPECTED_ROW_SCHEMA:
            errors.append({"error_type": "unexpected_row_schema", "row_id": row_id, "actual": raw.get("schema_version")})
        actual_blocks = set(raw.get("feature_blocks", {}))
        if actual_blocks != EXPECTED_BLOCKS:
            errors.append({"error_type": "unexpected_feature_blocks", "row_id": row_id, "actual": sorted(actual_blocks)})
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


def group_contrast_margins(rows: list[dict[str, Any]], predictions: dict[str, list[float]]) -> dict[str, Any]:
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
    m2 = value_or_zero(metrics, "M2_obb_geometry_only")
    m3 = value_or_zero(metrics, "M3_point_pose_only")
    m4 = value_or_zero(metrics, "M4_contact_patch_only")
    m5 = value_or_zero(metrics, "M5_point_contact_geometry")
    m6 = value_or_zero(metrics, "M6_TG_obb_concat")
    m7 = value_or_zero(metrics, "M7_TG_point_contact_concat")
    m8 = value_or_zero(metrics, PRIMARY_MODEL)
    m9 = value_or_zero(metrics, FULL_MODEL)
    s1 = value_or_zero(metrics, "S1_predicate_label_shortcut")
    s2 = value_or_zero(metrics, "S2_class_pair_shortcut")
    s3 = value_or_zero(metrics, "S3_quality_only_shortcut")
    c1 = value_or_zero(metrics, "C1_wrong_T_same_G")
    c2 = value_or_zero(metrics, "C2_shuffled_G_global")
    c3 = value_or_zero(metrics, "C3_shuffled_G_within_predicate")
    c4 = value_or_zero(metrics, "C4_shuffled_Q")

    component_best = max(m1, m2, m3, m4, m5)
    best_shuffle = max(c2, c3)
    primary_margin = margins.get(PRIMARY_MODEL, {})
    mean_margin = primary_margin.get("mean_positive_minus_negative") or 0.0
    margin_fraction = primary_margin.get("positive_margin_fraction") or 0.0

    gate_data = len(errors) == 0
    gate_semantic_shortcuts = max(m1, s1, s2) <= SHORTCUT_AUROC_MAX
    gate_quality_shortcut = s3 <= SHORTCUT_AUROC_MAX
    gate_primary_signal = m8 >= PRIMARY_AUROC_MIN
    gate_compatibility_gain = (m8 - component_best) >= PRIMARY_GAIN_OVER_COMPONENTS_MIN
    gate_point_expansion = (m8 - m6) >= POINT_EXPANSION_GAIN_MIN
    gate_not_geometry_dominant = (m8 - m5) > GEOMETRY_DOMINANCE_MARGIN
    gate_interaction_over_concat = m8 >= m7
    gate_shuffle = best_shuffle <= max(m1, m5) + SHUFFLE_CONTROL_MARGIN
    gate_wrong_t = c1 <= (m8 - WRONG_T_DEGRADE_MIN)
    gate_margin = mean_margin > 0.0 and margin_fraction >= 0.55
    q_rescue_risk = m9 >= PRIMARY_AUROC_MIN and m8 < PRIMARY_AUROC_MIN

    hard_fail = not (
        gate_data
        and gate_semantic_shortcuts
        and gate_quality_shortcut
        and gate_primary_signal
        and gate_shuffle
        and gate_wrong_t
    )
    geometry_dominance = (
        not hard_fail
        and not gate_not_geometry_dominant
        and gate_interaction_over_concat
        and gate_point_expansion
    )
    overall = (
        not hard_fail
        and not geometry_dominance
        and gate_compatibility_gain
        and gate_point_expansion
        and gate_interaction_over_concat
        and gate_margin
        and not q_rescue_risk
    )

    return {
        "gate_compatibility_gain": {
            "actual_gain": m8 - component_best,
            "best_component": component_best,
            "pass": gate_compatibility_gain,
            "required_gain": PRIMARY_GAIN_OVER_COMPONENTS_MIN,
        },
        "gate_data_integrity": {"pass": gate_data, "validation_errors": len(errors)},
        "gate_geometry_dominance_check": {
            "M5_point_contact_geometry": m5,
            "actual_margin": m8 - m5,
            "interpretation_if_fail": "point/contact geometry-only explains target nearly as well as predicate-conditioned compatibility",
            "margin": GEOMETRY_DOMINANCE_MARGIN,
            "pass": gate_not_geometry_dominant,
            "primary": m8,
        },
        "gate_group_contrast_score_direction": {
            "mean_positive_minus_negative": mean_margin,
            "pass": gate_margin,
            "positive_margin_fraction": margin_fraction,
        },
        "gate_interaction_over_plain_concat": {
            "M7_TG_point_contact_concat": m7,
            PRIMARY_MODEL: m8,
            "actual_gain": m8 - m7,
            "pass": gate_interaction_over_concat,
        },
        "gate_point_contact_expansion_gain": {
            "M6_TG_obb_concat": m6,
            PRIMARY_MODEL: m8,
            "actual_gain": m8 - m6,
            "pass": gate_point_expansion,
            "required_gain": POINT_EXPANSION_GAIN_MIN,
        },
        "gate_primary_predictive_signal": {
            "min_required": PRIMARY_AUROC_MIN,
            "pass": gate_primary_signal,
            "primary_auroc": m8,
        },
        "gate_quality_shortcut_control": {
            "S3_quality_only_shortcut": s3,
            "max_allowed": SHORTCUT_AUROC_MAX,
            "pass": gate_quality_shortcut,
        },
        "gate_q_boundary": {
            "C4_shuffled_Q": c4,
            FULL_MODEL: m9,
            PRIMARY_MODEL: m8,
            "q_gain_over_primary": m9 - m8,
            "q_rescue_risk": q_rescue_risk,
        },
        "gate_semantic_shortcut_control": {
            "auroc": {
                "M1_semantic_only_T": m1,
                "S1_predicate_label_shortcut": s1,
                "S2_class_pair_shortcut": s2,
            },
            "max_allowed": SHORTCUT_AUROC_MAX,
            "pass": gate_semantic_shortcuts,
        },
        "gate_shuffled_G_degradation": {
            "C2_shuffled_G_global": c2,
            "C3_shuffled_G_within_predicate": c3,
            "allowed_max": max(m1, m5) + SHUFFLE_CONTROL_MARGIN,
            "best_shuffle": best_shuffle,
            "pass": gate_shuffle,
        },
        "gate_wrong_T_same_G_degradation": {
            "C1_wrong_T_same_G": c1,
            "required_max": m8 - WRONG_T_DEGRADE_MIN,
            "pass": gate_wrong_t,
        },
        "geometry_dominance_diagnostic": geometry_dominance,
        "hard_fail": hard_fail,
        "model_auroc_snapshot": {
            "C1_wrong_T_same_G": c1,
            "C2_shuffled_G_global": c2,
            "C3_shuffled_G_within_predicate": c3,
            "C4_shuffled_Q": c4,
            "M1_semantic_only_T": m1,
            "M2_obb_geometry_only": m2,
            "M3_point_pose_only": m3,
            "M4_contact_patch_only": m4,
            "M5_point_contact_geometry": m5,
            "M6_TG_obb_concat": m6,
            "M7_TG_point_contact_concat": m7,
            PRIMARY_MODEL: m8,
            FULL_MODEL: m9,
            "S1_predicate_label_shortcut": s1,
            "S2_class_pair_shortcut": s2,
            "S3_quality_only_shortcut": s3,
        },
        "overall_interpretation": (
            "support_contact_point_multiview_smoke_passed_controls"
            if overall
            else (
                "support_contact_point_multiview_smoke_geometry_dominance_diagnostic"
                if geometry_dominance
                else "support_contact_point_multiview_smoke_diagnostic_only_failed_controls"
            )
        ),
        "overall_pass": overall,
    }


def prediction_rows(rows: list[dict[str, Any]], predictions: dict[str, list[float]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        item = {
            "group_id": row.get("group_id"),
            "label": row.get("y_compatibility"),
            "object": row.get("T_e", {}).get("object_class_text"),
            "predicate": row.get("T_e", {}).get("predicate_label"),
            "row_id": row.get("row_id"),
            "subject": row.get("T_e", {}).get("subject_class_text"),
        }
        for model, scores in predictions.items():
            item[model] = scores[idx]
        output.append(item)
    return output


def error_cases(rows: list[dict[str, Any]], scores: list[float], max_cases: int = 50) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for row, score in zip(rows, scores):
        label = int(row["y_compatibility"])
        pred = 1 if score >= 0.5 else 0
        if pred == label:
            continue
        point = row.get("G_e_point_pose", {})
        contact = row.get("G_e_contact_patch", {})
        cases.append(
            {
                "label": label,
                "object": row.get("T_e", {}).get("object_class_text"),
                "point_contact_proxy": contact.get("point_support_contact_likelihood_proxy"),
                "point_gap_abs": contact.get("point_abs_surface_gap_subject_bottom_to_object_top"),
                "point_xy_overlap_min_ratio": contact.get("point_xy_overlap_min_ratio"),
                "prediction": pred,
                "predicate": row.get("T_e", {}).get("predicate_label"),
                "row_id": row.get("row_id"),
                "score": round(score, 6),
                "subject": row.get("T_e", {}).get("subject_class_text"),
                "subject_flatness_proxy": point.get("subject_flatness_proxy"),
                "subject_vertical_extent_ratio": point.get("subject_vertical_extent_ratio"),
            }
        )
    return sorted(cases, key=lambda item: abs(float(item["score"]) - 0.5), reverse=True)[:max_cases]


def metric_text(metric: dict[str, Any], key: str) -> Any:
    value = metric.get(key)
    return "None" if value is None else value


def write_report(path: Path, summary: dict[str, Any], metrics: dict[str, Any], gates: dict[str, Any]) -> None:
    order = [
        "M0_intercept",
        "M1_semantic_only_T",
        "M2_obb_geometry_only",
        "M3_point_pose_only",
        "M4_contact_patch_only",
        "M5_point_contact_geometry",
        "M6_TG_obb_concat",
        "M7_TG_point_contact_concat",
        PRIMARY_MODEL,
        FULL_MODEL,
        "S1_predicate_label_shortcut",
        "S2_class_pair_shortcut",
        "S3_quality_only_shortcut",
        "C1_wrong_T_same_G",
        "C2_shuffled_G_global",
        "C3_shuffled_G_within_predicate",
        "C4_shuffled_Q",
    ]
    lines = [
        "# H002 Support/Contact Individual Predicate Point/Multiview Smoke Runner",
        "",
        "## Status",
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
        "| Model | AUROC | AUPRC | Accuracy | Balanced Acc. | Brier | ECE-10 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name in order:
        metric = metrics[name]
        lines.append(
            f"| `{name}` | {metric_text(metric, 'auroc')} | {metric_text(metric, 'auprc')} | "
            f"{metric_text(metric, 'accuracy_at_0_5')} | {metric_text(metric, 'balanced_accuracy_at_0_5')} | "
            f"{metric_text(metric, 'brier')} | {metric_text(metric, 'ece_10')} |"
        )
    lines.extend(
        [
            "",
            "## Gates",
            "",
            f"- data integrity: `{gates['gate_data_integrity']['pass']}`",
            f"- semantic shortcut control: `{gates['gate_semantic_shortcut_control']['pass']}`",
            f"- quality shortcut control: `{gates['gate_quality_shortcut_control']['pass']}`",
            f"- primary predictive signal: `{gates['gate_primary_predictive_signal']['pass']}`",
            f"- compatibility gain: `{gates['gate_compatibility_gain']['pass']}`",
            f"- point/contact expansion gain: `{gates['gate_point_contact_expansion_gain']['pass']}`",
            f"- geometry dominance check: `{gates['gate_geometry_dominance_check']['pass']}`",
            f"- interaction over plain concat: `{gates['gate_interaction_over_plain_concat']['pass']}`",
            f"- wrong-T same-G degradation: `{gates['gate_wrong_T_same_G_degradation']['pass']}`",
            f"- shuffled-G degradation: `{gates['gate_shuffled_G_degradation']['pass']}`",
            f"- group contrast margin: `{gates['gate_group_contrast_score_direction']['pass']}`",
            f"- Q boundary q_rescue_risk: `{gates['gate_q_boundary']['q_rescue_risk']}`",
            "",
            "## Interpretation",
            "",
            "This train-only smoke tests whether point-derived pose/contact `G_e` plus predicate-conditioned",
            "`C_e` improves support/contact compatibility beyond semantic-only, OBB-only, and geometry-only",
            "baselines. `Q_e` is treated as observability/evidence-quality metadata, not as a truth signal.",
            "",
            "Wrong-T and shuffled-G/Q rows are inference-time corruptions of the clean trained views.",
            "The artifact is not paper evidence and does not use validation or test rows.",
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
    y = labels(rows)
    margins = group_contrast_margins(rows, predictions)
    metrics_by_predicate = group_metrics(rows, y, predictions, lambda row: str(row.get("T_e", {}).get("predicate_label")))
    metrics_by_pair_text = group_metrics(
        rows,
        y,
        predictions,
        lambda row: f"{row.get('T_e', {}).get('subject_class_text')}|{row.get('T_e', {}).get('object_class_text')}",
    )
    gates = gate_summary(metrics, margins, errors)

    if errors:
        status = STATUS_ERRORS
        next_todo = NEXT_TODO_FAILURE
    elif gates["overall_pass"]:
        status = STATUS_PASSED
        next_todo = NEXT_TODO_REVIEW
    elif gates["geometry_dominance_diagnostic"]:
        status = STATUS_GEOMETRY_DOMINANCE
        next_todo = NEXT_TODO_REVIEW
    else:
        status = STATUS_DIAGNOSTIC
        next_todo = NEXT_TODO_FAILURE

    summary = {
        "boundary": {
            "corruption_controls_train_on_clean_features": True,
            "h001_artifacts_modified": False,
            "multiview_used_as_learned_visual_feature": False,
            "paper_evidence_allowed": False,
            "raw_candidate_rows_used_as_model_input": False,
            "split": "train_internal_grouped_by_cv_group_id",
            "test_usage": False,
            "validation_usage": False,
        },
        "counts": count_summary(rows),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "epochs": args.epochs,
        "folds": args.folds,
        "gates": gates,
        "input_file": rel_path(input_path),
        "input_sha256": sha256_file(input_path),
        "key_metrics": {name: metrics[name] for name in sorted(metrics)},
        "l2": args.l2,
        "learned_smoke_executed": True,
        "lr": args.lr,
        "next_todo": next_todo,
        "output_paths": {
            "error_cases": rel_path(args.output_dir / "error_cases_m8.jsonl"),
            "folds": rel_path(args.output_dir / "folds.json"),
            "gate_results": rel_path(args.output_dir / "gate_results.json"),
            "group_contrast_margins": rel_path(args.output_dir / "group_contrast_margins.json"),
            "metrics": rel_path(args.output_dir / "metrics.json"),
            "metrics_by_predicate": rel_path(args.output_dir / "metrics_by_predicate.json"),
            "predictions": rel_path(args.output_dir / "predictions.jsonl"),
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

    write_json(args.output_dir / "metrics.json", metrics)
    write_json(args.output_dir / "metrics_by_predicate.json", {"predicate": metrics_by_predicate, "subject_object_text": metrics_by_pair_text})
    write_json(args.output_dir / "group_contrast_margins.json", margins)
    write_json(args.output_dir / "folds.json", folds)
    write_json(args.output_dir / "gate_results.json", gates)
    write_jsonl(args.output_dir / "predictions.jsonl", prediction_rows(rows, predictions))
    write_jsonl(args.output_dir / "error_cases_m8.jsonl", error_cases(rows, predictions[PRIMARY_MODEL]))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, metrics, gates)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
