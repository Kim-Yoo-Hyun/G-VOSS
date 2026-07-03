#!/usr/bin/env python3
"""Run support/contact hard-route metrics after train/eval alignment."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from run_grouped_eval import (
    binary_metrics,
    fit_model,
    merge_features,
    one_hot,
    predict_model,
    safe_float,
    stable_hash,
    write_csv,
    write_json,
    write_jsonl,
)


SCHEMA_VERSION = "h002_support_contact_harder_metric_runner_v1"
STATUS_READY = "h002_support_contact_harder_metric_runner_ready"
STATUS_ERRORS = "h002_support_contact_harder_metric_runner_input_errors"
EXPECTED_ALIGNMENT_STATUS = "h002_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze_ready"
EXPECTED_ALIGNMENT_NEXT = "compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment"
EXPECTED_PROTOCOL_STATUS = "h002_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit_ready"
EXPECTED_TRAIN_ROWS = 640
EXPECTED_OFFICIAL_ROWS = 3178
TRAIN_SPLIT = "internal_train"
DEV_SPLIT = "internal_dev"
CONTROL_SEED = "h002_support_contact_harder_metric_v1"

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--alignment-dir", type=Path, required=True)
    parser.add_argument("--official-materialization-dir", type=Path, required=True)
    parser.add_argument("--protocol-dir", type=Path, required=True)
    parser.add_argument("--train-materialization-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def rel_path(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def target(row: dict[str, Any]) -> int:
    return int(row.get("target_y", row.get("labels", {}).get("C_e", 0)))


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["target_y"] = target(row)
    return output


def feature_blocks(row: dict[str, Any]) -> dict[str, Any]:
    return row.get("feature_blocks", {}) if isinstance(row.get("feature_blocks"), dict) else {}


def t_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("T_e", {})
    return block if isinstance(block, dict) else {}


def g_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("G_e", {})
    return block if isinstance(block, dict) else {}


def q_block(row: dict[str, Any]) -> dict[str, Any]:
    block = feature_blocks(row).get("Q_e", {})
    return block if isinstance(block, dict) else {}


def flatten_numeric(prefix: str, value: Any) -> dict[str, float]:
    out: dict[str, float] = {}
    if isinstance(value, dict):
        for key, child in sorted(value.items()):
            out.update(flatten_numeric(f"{prefix}.{key}", child))
    elif isinstance(value, bool):
        out[prefix] = 1.0 if value else 0.0
    elif isinstance(value, (int, float)):
        out[prefix] = safe_float(value, 0.0)
    elif isinstance(value, str):
        out.update(one_hot(prefix, value))
    return out


def t_predicate_features(row: dict[str, Any]) -> dict[str, float]:
    t = t_block(row)
    out: dict[str, float] = {}
    for key in ["predicate_label", "predicate_text", "route_family", "predicate_family_embedding_key"]:
        out.update(one_hot(f"T.{key}", t.get(key) or row.get(key)))
    return out


def t_class_features(row: dict[str, Any]) -> dict[str, float]:
    t = t_block(row)
    out = t_predicate_features(row)
    for key in ["subject_class_text", "object_class_text", "subject_class_label", "object_class_label"]:
        if key in t:
            out.update(one_hot(f"T.{key}", t.get(key)))
    return out


def g_vector(row: dict[str, Any]) -> dict[str, float]:
    vector = g_block(row).get("g_e_feature_vector", {})
    return vector if isinstance(vector, dict) else {}


def g_features(row: dict[str, Any]) -> dict[str, float]:
    vector = g_vector(row)
    out = {f"G.{key}": safe_float(value, 0.0) for key, value in sorted(vector.items())}
    mask = g_block(row).get("g_e_feature_mask", {})
    if isinstance(mask, dict):
        for key, value in sorted(mask.items()):
            out[f"Gmask.{key}"] = 1.0 if value else 0.0
    return out


def q_features(row: dict[str, Any]) -> dict[str, float]:
    return flatten_numeric("Q", q_block(row))


def predicate_value(row: dict[str, Any]) -> str:
    return str(row.get("predicate_label") or t_block(row).get("predicate_label") or "")


def predicate_sign(row: dict[str, Any]) -> float:
    return 1.0 if predicate_value(row) == "standing on" else -1.0 if predicate_value(row) == "lying on" else 0.0


def compatibility_features_from_g(row: dict[str, Any], g_feats: dict[str, float]) -> dict[str, float]:
    predicate = predicate_value(row).replace(" ", "_")
    sign = predicate_sign(row)
    out: dict[str, float] = {}
    for key, value in g_feats.items():
        if not key.startswith("G."):
            continue
        name = key[2:]
        out[f"C.pred={predicate}.{name}"] = value
        out[f"C.sign_x_{name}"] = sign * value
    return out


def compatibility_features(row: dict[str, Any]) -> dict[str, float]:
    return compatibility_features_from_g(row, g_features(row))


def mutate_predicate(row: dict[str, Any]) -> dict[str, Any]:
    output = json.loads(json.dumps(row))
    old = predicate_value(output)
    new = {"standing on": "lying on", "lying on": "standing on"}.get(old, old)
    output["predicate_label"] = new
    blocks = feature_blocks(output)
    t = blocks.get("T_e", {}) if isinstance(blocks.get("T_e"), dict) else {}
    t["predicate_label"] = new
    t["predicate_text"] = new
    blocks["T_e"] = t
    output["feature_blocks"] = blocks
    return output


def m1_features(row: dict[str, Any]) -> dict[str, float]:
    return t_predicate_features(row)


def m2_features(row: dict[str, Any]) -> dict[str, float]:
    return g_features(row)


def m3_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_predicate_features(row), g_features(row))


def m4_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_predicate_features(row), g_features(row), compatibility_features(row))


def class_ablation_features(row: dict[str, Any]) -> dict[str, float]:
    return merge_features(t_class_features(row), g_features(row), compatibility_features(row))


def wrong_t_features(row: dict[str, Any]) -> dict[str, float]:
    return m4_features(mutate_predicate(row))


def shuffled_maps(rows: list[dict[str, Any]], hidden_by_id: dict[str, dict[str, Any]]) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    global_order = sorted(rows, key=lambda row: stable_hash(f"{CONTROL_SEED}:global:{row['candidate_id']}"))
    global_shift = global_order[1:] + global_order[:1] if len(global_order) > 1 else global_order
    global_map = {row["candidate_id"]: g_features(donor) for row, donor in zip(global_order, global_shift)}

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        hidden = hidden_by_id.get(row["candidate_id"], {})
        buckets[str(hidden.get("class_pair", "missing"))].append(row)
    within_map: dict[str, dict[str, float]] = {}
    for class_pair, bucket in buckets.items():
        ordered = sorted(bucket, key=lambda row: stable_hash(f"{CONTROL_SEED}:class_pair:{class_pair}:{row['candidate_id']}"))
        shifted = ordered[1:] + ordered[:1] if len(ordered) > 1 else ordered
        for row, donor in zip(ordered, shifted):
            within_map[row["candidate_id"]] = g_features(donor)
    return global_map, within_map


def shuffled_feature_fn(source: dict[str, dict[str, float]]) -> FeatureFn:
    def fn(row: dict[str, Any]) -> dict[str, float]:
        g = source.get(row["candidate_id"], g_features(row))
        return merge_features(t_predicate_features(row), g, compatibility_features_from_g(row, g))

    return fn


def load_q_train_rows(train_materialization_dir: Path, aligned_hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    original_rows = {row.get("row_id"): row for row in read_jsonl(train_materialization_dir / "model_safe_view.jsonl")}
    split_by_source = {row.get("source_row_id"): row.get("split") for row in aligned_hidden_rows}
    out: list[dict[str, Any]] = []
    for source_row_id, split in split_by_source.items():
        row = original_rows.get(source_row_id)
        if not row:
            continue
        row = normalize_row(row)
        row["candidate_id"] = f"q_train::{source_row_id}"
        row["split"] = split
        out.append(row)
    return out


def validate_inputs(
    *,
    alignment_summary: dict[str, Any],
    protocol_summary: dict[str, Any],
    runner_contract: dict[str, Any],
    train_rows: list[dict[str, Any]],
    official_rows: list[dict[str, Any]],
    official_hidden_rows: list[dict[str, Any]],
    validation_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = list(validation_errors)
    if alignment_summary.get("status") != EXPECTED_ALIGNMENT_STATUS:
        errors.append({"error_type": "unexpected_alignment_status", "actual": alignment_summary.get("status")})
    if alignment_summary.get("next_todo") != EXPECTED_ALIGNMENT_NEXT:
        errors.append({"error_type": "unexpected_alignment_next_todo", "actual": alignment_summary.get("next_todo")})
    if alignment_summary.get("validation_errors") != 0:
        errors.append({"error_type": "alignment_validation_errors", "actual": alignment_summary.get("validation_errors")})
    if protocol_summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol_summary.get("status")})
    if runner_contract.get("status") != "runner_input_ready":
        errors.append({"error_type": "runner_input_contract_not_ready", "actual": runner_contract.get("status")})
    if len(train_rows) != EXPECTED_TRAIN_ROWS:
        errors.append({"error_type": "unexpected_train_rows", "actual": len(train_rows), "expected": EXPECTED_TRAIN_ROWS})
    if len(official_rows) != EXPECTED_OFFICIAL_ROWS:
        errors.append({"error_type": "unexpected_official_rows", "actual": len(official_rows), "expected": EXPECTED_OFFICIAL_ROWS})
    if len(official_hidden_rows) != EXPECTED_OFFICIAL_ROWS:
        errors.append({"error_type": "unexpected_official_hidden_rows", "actual": len(official_hidden_rows), "expected": EXPECTED_OFFICIAL_ROWS})
    if not any(row.get("split") == TRAIN_SPLIT for row in train_rows):
        errors.append({"error_type": "missing_internal_train"})
    if not any(row.get("split") == DEV_SPLIT for row in train_rows):
        errors.append({"error_type": "missing_internal_dev"})
    for row in train_rows[:20] + official_rows[:20]:
        blocks = set(feature_blocks(row))
        if blocks != {"T_e", "G_e"}:
            errors.append({"error_type": "primary_row_has_unexpected_blocks", "candidate_id": row.get("candidate_id"), "blocks": sorted(blocks)})
            break
        t = t_block(row)
        if any(key in t for key in ["subject_class_text", "object_class_text", "subject_class_label", "object_class_label"]):
            errors.append({"error_type": "primary_row_has_class_label", "candidate_id": row.get("candidate_id")})
            break
    if alignment_summary.get("leakage_audit", {}).get("scan_overlap") != 0:
        errors.append({"error_type": "scan_overlap_nonzero"})
    if alignment_summary.get("leakage_audit", {}).get("endpoint_overlap") != 0:
        errors.append({"error_type": "endpoint_overlap_nonzero"})
    return errors


def split_rows(rows: list[dict[str, Any]], split: str) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("split") == split]


def train_and_eval(
    view_id: str,
    train_rows: list[dict[str, Any]],
    dev_rows: list[dict[str, Any]],
    official_rows: list[dict[str, Any]],
    train_fn: FeatureFn,
    eval_fn: FeatureFn | None,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[dict[str, Any], list[float], list[float]]:
    eval_fn = eval_fn or train_fn
    model, prior, fit_summary = fit_model(train_rows, train_fn, epochs, lr, l2)
    dev_scores = predict_model(model, prior, dev_rows, eval_fn)
    official_scores = predict_model(model, prior, official_rows, eval_fn)
    return {"view_id": view_id, **fit_summary}, dev_scores, official_scores


def metric_row(eval_split: str, view_id: str, rows: list[dict[str, Any]], scores: list[float], level: str = "overall") -> dict[str, Any]:
    labels = [target(row) for row in rows]
    return {
        "eval_split": eval_split,
        "view_id": view_id,
        "level": level,
        "route_family": "support_contact",
        "predicate_label": "ALL",
        **binary_metrics(labels, scores),
    }


def predicate_metric_rows(eval_split: str, view_id: str, rows: list[dict[str, Any]], scores: list[float]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for predicate in sorted({predicate_value(row) for row in rows}):
        indices = [idx for idx, row in enumerate(rows) if predicate_value(row) == predicate]
        subset = [rows[idx] for idx in indices]
        subset_scores = [scores[idx] for idx in indices]
        row = metric_row(eval_split, view_id, subset, subset_scores, level="predicate")
        row["predicate_label"] = predicate
        out.append(row)
    return out


def paired_group_accuracy(rows: list[dict[str, Any]], scores: list[float], hidden_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[tuple[dict[str, Any], float]]] = defaultdict(list)
    for row, score in zip(rows, scores):
        group = hidden_by_id.get(row["candidate_id"], {}).get("cv_or_group_key") or row["candidate_id"]
        buckets[str(group)].append((row, score))
    usable = 0
    decisive = 0
    tied_top = 0
    correct_decisive = 0
    half_credit_correct = 0.0
    for group_rows in buckets.values():
        labels = {target(row) for row, _ in group_rows}
        if len(group_rows) < 2 or labels != {0, 1}:
            continue
        usable += 1
        top_score = max(score for _, score in group_rows)
        winners = [(row, score) for row, score in group_rows if abs(score - top_score) <= 1e-12]
        if len(winners) > 1:
            tied_top += 1
            positive_tied = sum(target(row) for row, _ in winners)
            half_credit_correct += positive_tied / len(winners)
            continue
        decisive += 1
        if target(winners[0][0]) == 1:
            correct_decisive += 1
            half_credit_correct += 1.0
    return {
        "paired_groups": usable,
        "paired_group_decisive": decisive,
        "paired_group_tied_top": tied_top,
        "paired_group_correct_decisive": correct_decisive,
        "paired_group_accuracy_decisive": correct_decisive / decisive if decisive else None,
        "paired_group_accuracy_half_credit": half_credit_correct / usable if usable else None,
        "paired_group_accuracy": half_credit_correct / usable if usable else None,
    }


def comparison_rows(official_metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_view = {row["view_id"]: row for row in official_metrics if row["level"] == "overall"}
    comparisons = [
        ("M4_vs_M1", "M4_TxG_compatibility", "M1_predicate_only", "expect_positive_delta"),
        ("M4_vs_M2", "M4_TxG_compatibility", "M2_geometry_only", "expect_positive_delta"),
        ("M4_vs_M3", "M4_TxG_compatibility", "M3_T_plus_G_concat", "expect_positive_delta"),
        ("M4_vs_wrong_T", "M4_TxG_compatibility", "C1_wrong_T_same_route", "expect_control_degrade"),
        ("M4_vs_shuffled_G_global", "M4_TxG_compatibility", "C2_shuffled_G_global", "expect_control_degrade"),
        ("M4_vs_shuffled_G_class_pair", "M4_TxG_compatibility", "C3_shuffled_G_within_class_pair", "expect_control_degrade"),
        ("M4_vs_class_ablation", "M4_TxG_compatibility", "A1_class_ablation", "diagnostic_only"),
        ("M4_vs_Q_e", "M4_TxG_compatibility", "D1_Q_e_diagnostic", "diagnostic_only"),
    ]
    out: list[dict[str, Any]] = []
    for comparison, primary, baseline, expectation in comparisons:
        p = by_view.get(primary)
        b = by_view.get(baseline)
        if not p or not b:
            continue
        p_auc = p.get("auroc")
        b_auc = b.get("auroc")
        out.append(
            {
                "comparison": comparison,
                "expectation": expectation,
                "primary_view": primary,
                "baseline_view": baseline,
                "primary_auroc": p_auc,
                "baseline_auroc": b_auc,
                "delta_auroc": None if p_auc is None or b_auc is None else p_auc - b_auc,
                "primary_balanced_accuracy": p.get("balanced_accuracy"),
                "baseline_balanced_accuracy": b.get("balanced_accuracy"),
            }
        )
    return out


def failure_rows(rows: list[dict[str, Any]], scores: list[float], hidden_by_id: dict[str, dict[str, Any]], limit: int = 80) -> list[dict[str, Any]]:
    mistakes: list[dict[str, Any]] = []
    for row, score in zip(rows, scores):
        label = target(row)
        predicted = 1 if score >= 0.5 else 0
        if predicted == label:
            continue
        confidence = score if predicted == 1 else 1 - score
        hidden = hidden_by_id.get(row["candidate_id"], {})
        mistakes.append(
            {
                "candidate_id": row["candidate_id"],
                "predicate_label": predicate_value(row),
                "target_y": label,
                "score": score,
                "predicted": predicted,
                "error_confidence": confidence,
                "scan_id": hidden.get("scan_id"),
                "subject_id": hidden.get("subject_id"),
                "object_id": hidden.get("object_id"),
                "class_pair": hidden.get("class_pair"),
            }
        )
    return sorted(mistakes, key=lambda row: row["error_confidence"], reverse=True)[:limit]


def run(args: argparse.Namespace) -> dict[str, Any]:
    args.out.mkdir(parents=True, exist_ok=True)

    alignment_summary = read_json(args.alignment_dir / "summary.json")
    protocol_summary = read_json(args.protocol_dir / "summary.json")
    runner_contract = read_json(args.alignment_dir / "runner_input_contract.json")
    alignment_errors = read_jsonl(args.alignment_dir / "validation_errors.jsonl")

    train_rows = [normalize_row(row) for row in read_jsonl(args.alignment_dir / "model_safe_no_class_train_dev.jsonl")]
    class_train_rows = [normalize_row(row) for row in read_jsonl(args.alignment_dir / "class_ablation_train_dev.jsonl")]
    hidden_train_rows = read_jsonl(args.alignment_dir / "hidden_train_dev_manifest.jsonl")
    official_rows = [normalize_row(row) for row in read_jsonl(args.official_materialization_dir / "model_safe_main_no_class.jsonl")]
    official_class_rows = [normalize_row(row) for row in read_jsonl(args.official_materialization_dir / "model_safe_main_with_class_ablation.jsonl")]
    official_q_rows = [normalize_row(row) for row in read_jsonl(args.official_materialization_dir / "model_safe_qe_diagnostic.jsonl")]
    official_hidden_rows = read_jsonl(args.official_materialization_dir / "hidden_manifest.jsonl")
    hidden_by_id = {row["candidate_id"]: row for row in official_hidden_rows}
    hidden_train_by_source = {row.get("source_row_id"): row for row in hidden_train_rows}
    q_train_rows = load_q_train_rows(args.train_materialization_dir, hidden_train_rows)

    errors = validate_inputs(
        alignment_summary=alignment_summary,
        protocol_summary=protocol_summary,
        runner_contract=runner_contract,
        train_rows=train_rows,
        official_rows=official_rows,
        official_hidden_rows=official_hidden_rows,
        validation_errors=alignment_errors,
    )

    train_split = split_rows(train_rows, TRAIN_SPLIT)
    dev_split = split_rows(train_rows, DEV_SPLIT)
    class_train_split = split_rows(class_train_rows, TRAIN_SPLIT)
    class_dev_split = split_rows(class_train_rows, DEV_SPLIT)
    q_train_split = split_rows(q_train_rows, TRAIN_SPLIT)
    q_dev_split = split_rows(q_train_rows, DEV_SPLIT)

    view_manifest: list[dict[str, Any]] = []
    dev_metrics: list[dict[str, Any]] = []
    official_metrics: list[dict[str, Any]] = []
    predicate_metrics: list[dict[str, Any]] = []
    paired_metrics: list[dict[str, Any]] = []
    prediction_score_rows: list[dict[str, Any]] = []
    failure_output: list[dict[str, Any]] = []
    official_scores_by_view: dict[str, list[float]] = {}
    dev_scores_by_view: dict[str, list[float]] = {}

    if not errors:
        global_shuffle, class_pair_shuffle = shuffled_maps(official_rows, hidden_by_id)
        views: list[tuple[str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], FeatureFn, FeatureFn | None, str]] = [
            ("M0_constant", train_split, dev_split, official_rows, lambda row: {}, None, "sanity"),
            ("M1_predicate_only", train_split, dev_split, official_rows, m1_features, None, "primary_baseline"),
            ("M2_geometry_only", train_split, dev_split, official_rows, m2_features, None, "primary_baseline"),
            ("M3_T_plus_G_concat", train_split, dev_split, official_rows, m3_features, None, "primary_baseline"),
            ("M4_TxG_compatibility", train_split, dev_split, official_rows, m4_features, None, "primary"),
            ("A1_class_ablation", class_train_split, class_dev_split, official_class_rows, class_ablation_features, None, "diagnostic"),
            ("D1_Q_e_diagnostic", q_train_split, q_dev_split, official_q_rows, q_features, None, "diagnostic"),
        ]

        # Fit M4 once for no-refit controls.
        m4_model, m4_prior, m4_fit = fit_model(train_split, m4_features, args.epochs, args.lr, args.l2)
        for view_id, tr, dv, off, train_fn, eval_fn, role in views:
            if view_id == "M4_TxG_compatibility":
                fit_summary = {"view_id": view_id, **m4_fit, "role": role}
                dev_scores = predict_model(m4_model, m4_prior, dv, m4_features)
                official_scores = predict_model(m4_model, m4_prior, off, m4_features)
            else:
                fit_summary, dev_scores, official_scores = train_and_eval(
                    view_id, tr, dv, off, train_fn, eval_fn, args.epochs, args.lr, args.l2
                )
                fit_summary["role"] = role
            view_manifest.append(fit_summary)
            dev_scores_by_view[view_id] = dev_scores
            official_scores_by_view[view_id] = official_scores
            dev_metrics.append(metric_row("internal_dev", view_id, dv, dev_scores))
            official_metrics.append(metric_row("official_validation", view_id, off, official_scores))
            predicate_metrics.extend(predicate_metric_rows("official_validation", view_id, off, official_scores))
            paired = paired_group_accuracy(off, official_scores, hidden_by_id)
            paired_metrics.append({"eval_split": "official_validation", "view_id": view_id, **paired})

        control_views: list[tuple[str, FeatureFn]] = [
            ("C1_wrong_T_same_route", wrong_t_features),
            ("C2_shuffled_G_global", shuffled_feature_fn(global_shuffle)),
            ("C3_shuffled_G_within_class_pair", shuffled_feature_fn(class_pair_shuffle)),
        ]
        for view_id, feature_fn in control_views:
            official_scores = predict_model(m4_model, m4_prior, official_rows, feature_fn)
            official_scores_by_view[view_id] = official_scores
            view_manifest.append({"view_id": view_id, "mode": "no_refit_m4_control", "feature_count": m4_fit.get("feature_count"), "train_rows": len(train_split), "role": "control"})
            official_metrics.append(metric_row("official_validation", view_id, official_rows, official_scores))
            predicate_metrics.extend(predicate_metric_rows("official_validation", view_id, official_rows, official_scores))
            paired = paired_group_accuracy(official_rows, official_scores, hidden_by_id)
            paired_metrics.append({"eval_split": "official_validation", "view_id": view_id, **paired})

        for idx, row in enumerate(official_rows):
            prediction_score_rows.append(
                {
                    "candidate_id": row["candidate_id"],
                    "route_family": row.get("route_family"),
                    "predicate_label": predicate_value(row),
                    "target_y": target(row),
                    "scores": {view_id: scores[idx] for view_id, scores in official_scores_by_view.items() if idx < len(scores)},
                }
            )
        failure_output = failure_rows(official_rows, official_scores_by_view["M4_TxG_compatibility"], hidden_by_id)

    controls = comparison_rows(official_metrics)
    status = STATUS_READY if not errors else STATUS_ERRORS
    primary = next((row for row in official_metrics if row["view_id"] == "M4_TxG_compatibility" and row["level"] == "overall"), {})
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "validation_errors": len(errors),
        "selected_path": "support_contact_harder_metric_ready_select_result_review" if not errors else "blocked_fix_metric_inputs",
        "next_todo": "compatibility_dataset_v3_support_contact_harder_route_metric_result_review_after_runner" if not errors else "fix_support_contact_metric_runner_inputs",
        "input_artifacts": {
            "alignment_summary": rel_path(args.repo_root, args.alignment_dir / "summary.json"),
            "runner_input_contract": rel_path(args.repo_root, args.alignment_dir / "runner_input_contract.json"),
            "protocol_summary": rel_path(args.repo_root, args.protocol_dir / "summary.json"),
            "official_materialization": rel_path(args.repo_root, args.official_materialization_dir),
            "train_materialization": rel_path(args.repo_root, args.train_materialization_dir),
        },
        "row_counts": {
            "train_rows": len(train_rows),
            "internal_train_rows": len(train_split),
            "internal_dev_rows": len(dev_split),
            "official_validation_rows": len(official_rows),
            "q_train_rows": len(q_train_rows),
        },
        "primary_official_metric": primary,
        "control_summary": controls,
        "decision": {
            "metric_runner_completed": not bool(errors),
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "support_contact_solved_claim_allowed": False,
            "result_review_next": not bool(errors),
            "feature_map_provenance_required": True,
        },
        "output_artifacts": {
            "eval_manifest": rel_path(args.repo_root, args.out / "eval_manifest.json"),
            "model_view_manifest": rel_path(args.repo_root, args.out / "model_view_manifest.csv"),
            "dev_metrics": rel_path(args.repo_root, args.out / "dev_metrics.csv"),
            "official_metrics": rel_path(args.repo_root, args.out / "official_metrics.csv"),
            "predicate_metrics": rel_path(args.repo_root, args.out / "predicate_metrics.csv"),
            "paired_group_metrics": rel_path(args.repo_root, args.out / "paired_group_metrics.csv"),
            "control_metrics": rel_path(args.repo_root, args.out / "control_metrics.csv"),
            "prediction_scores": rel_path(args.repo_root, args.out / "prediction_scores.jsonl"),
            "failure_rows": rel_path(args.repo_root, args.out / "failure_rows.jsonl"),
            "validation_errors": rel_path(args.repo_root, args.out / "validation_errors.jsonl"),
            "report": rel_path(args.repo_root, args.out / "report.md"),
        },
    }

    write_json(args.out / "eval_manifest.json", summary)
    write_jsonl(args.out / "validation_errors.jsonl", errors)
    write_csv(args.out / "model_view_manifest.csv", view_manifest)
    write_csv(args.out / "dev_metrics.csv", dev_metrics)
    write_csv(args.out / "official_metrics.csv", official_metrics)
    write_csv(args.out / "predicate_metrics.csv", predicate_metrics)
    write_csv(args.out / "paired_group_metrics.csv", paired_metrics)
    write_csv(args.out / "control_metrics.csv", controls)
    write_jsonl(args.out / "prediction_scores.jsonl", prediction_score_rows)
    write_jsonl(args.out / "failure_rows.jsonl", failure_output)
    report = [
        "# Support/Contact Harder Route Metric Runner",
        "",
        "```text",
        f"status = {status}",
        f"validation_errors = {len(errors)}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "Official validation is eval-only. No official test was used. No paper result is promoted here.",
        "",
        "Primary official metric:",
        "",
        "```json",
        json.dumps(primary, ensure_ascii=False, indent=2, sort_keys=True),
        "```",
    ]
    (args.out / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    return 1 if summary["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
