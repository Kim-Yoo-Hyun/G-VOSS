#!/usr/bin/env python3
"""Train-only full-train H002 controlled posterior smoke."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_TARGETS = RGA_ROOT / "controlled_label_readiness_codex_ver/binary_targets.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "controlled_posterior_smoke_codex_ver"

TARGET_MODE = "full_train_controlled_codex_ver"

MAIN_VIEWS = [
    "semantic_only",
    "geometry_only",
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
]

DIAGNOSTIC_VIEWS = [
    "residual_reliability_model",
    "continuous_safe",
    "semantic_score_only",
    "geometry_continuous_only",
]

PROXY_VIEWS = [
    "negative_rank_only",
    "rank_band_only",
    "queue_only",
    "candidate_axis_only",
    "family_only",
    "predicate_only",
    "label_status_only",
    "geometry_status_only",
    "proposed_role_only",
    "p_geom_valid_only",
]

PROBE_NAMES = [
    "semantic_score_norm",
    "negative_semantic_score_norm",
    "semantic_rank_inverse",
    "p_geom_valid",
    "negative_p_geom_valid",
    "absolute_disagreement",
    "underconfidence_score",
    "overconfidence_score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def safe_float(value: Any, default: float = 0.0) -> float:
    return smoke.safe_float(value, default)


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def rank_features(rank: int) -> dict[str, float]:
    rank_value = max(rank, 1)
    return {
        "semantic_rank": float(rank_value),
        "semantic_rank_log": math.log1p(rank_value),
        "semantic_rank_inverse": 1.0 / rank_value,
    }


def build_baseline_inputs(target: dict[str, Any]) -> dict[str, dict[str, Any]]:
    semantic = safe_float(target.get("semantic_score_norm"), 0.0)
    p_geom = safe_float(target.get("p_geom_valid"), 0.5)
    rank = safe_int(target.get("semantic_rank"), 0)
    rank_block = rank_features(rank)
    disagreement = abs(semantic - p_geom)
    underconfidence = max(0.0, p_geom - semantic)
    overconfidence = max(0.0, semantic - p_geom)
    common_semantic = {
        "semantic_score_norm": semantic,
        "negative_semantic_score_norm": 1.0 - semantic,
        **rank_block,
    }
    common_geometry = {
        "p_geom_valid": p_geom,
        "p_geom_invalid": 1.0 - p_geom,
    }
    factorized_continuous = {
        **common_semantic,
        **common_geometry,
        "absolute_disagreement": disagreement,
        "semantic_minus_geometry": semantic - p_geom,
        "geometry_minus_semantic": p_geom - semantic,
        "underconfidence_score": underconfidence,
        "overconfidence_score": overconfidence,
    }
    return {
        "semantic_only": dict(common_semantic),
        "geometry_only": dict(common_geometry),
        "semantic_plus_geometry": {**common_semantic, **common_geometry},
        "factorized_reliability_posterior": dict(factorized_continuous),
        "residual_reliability_model": {
            **common_semantic,
            **common_geometry,
            "geometry_minus_semantic": p_geom - semantic,
            "absolute_disagreement": disagreement,
        },
        "continuous_safe": dict(factorized_continuous),
        "semantic_score_only": {
            "semantic_score_norm": semantic,
        },
        "geometry_continuous_only": dict(common_geometry),
        "negative_rank_only": {
            "negative_semantic_score_norm": 1.0 - semantic,
            "semantic_rank_log": math.log1p(max(rank, 1)),
        },
        "rank_band_only": {
            "rank_band": target.get("rank_band"),
        },
        "queue_only": {
            "queue_kind": target.get("queue_kind"),
        },
        "candidate_axis_only": {
            "candidate_axis": target.get("candidate_axis"),
        },
        "family_only": {
            "predicate_family": target.get("predicate_family"),
        },
        "predicate_only": {
            "predicate_label": target.get("predicate_label"),
        },
        "label_status_only": {
            "label_match_status": target.get("label_match_status"),
        },
        "geometry_status_only": {
            "geometry_status": target.get("geometry_status"),
        },
        "proposed_role_only": {
            "proposed_audit_role": target.get("proposed_audit_role"),
        },
        "p_geom_valid_only": {
            "p_geom_valid": p_geom,
        },
    }


def build_rows(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for target in targets:
        row = {
            "schema_version": "h002_full_train_controlled_posterior_smoke_row_v0",
            "record_type": "h002_full_train_controlled_posterior_smoke_row",
            "identity": {
                "prediction_id": target["prediction_id"],
                "scan_id": target["scan_id"],
                "subgraph_id": target["subgraph_id"],
                "subject_id": target["subject_id"],
                "subject_label": target["subject_label"],
                "predicate_label": target["predicate_label"],
                "predicate_family": target["predicate_family"],
                "object_id": target["object_id"],
                "object_label": target["object_label"],
            },
            "baseline_inputs": build_baseline_inputs(target),
            "target": {
                "target_mode": TARGET_MODE,
                "y": int(target["posterior_target"]),
                "sample_weight": 1.0,
                "review_id": target["review_id"],
                "reviewer_id": target["reviewer_id"],
                "confidence": target.get("confidence"),
                "final_controlled_label": target["final_controlled_label"],
                "failure_taxonomy_label": target.get("failure_taxonomy_label"),
                "queue_kind": target.get("queue_kind"),
                "candidate_axis": target.get("candidate_axis"),
                "proposed_audit_role": target.get("proposed_audit_role"),
                "rank_band": target.get("rank_band"),
                "semantic_rank": target.get("semantic_rank"),
                "geometry_status": target.get("geometry_status"),
                "label_match_status": target.get("label_match_status"),
                "predicate_family": target.get("predicate_family"),
                "predicate_label": target.get("predicate_label"),
                "label_source": "codex_ver_full_train_policy_bootstrap",
                "human_confirmed": False,
                "paper_locked": False,
                "allowed_use": "train-only full-train controlled posterior smoke",
            },
            "provenance": {
                "target_source": "controlled_label_readiness_codex_ver/binary_targets.jsonl",
                "feature_source": "compact target row fields",
                "split_policy": "train_full_only",
            },
        }
        rows.append(row)
    return rows


def grouped_folds(rows: list[dict[str, Any]], fold_count: int) -> tuple[list[list[int]], list[dict[str, Any]]]:
    groups: dict[str, list[int]] = {}
    for idx, row in enumerate(rows):
        groups.setdefault(str(row["identity"]["scan_id"]), []).append(idx)
    fold_count = max(2, min(fold_count, len(groups)))
    total_pos = sum(smoke.target_y(row) for row in rows)
    total_neg = len(rows) - total_pos
    target_pos = total_pos / fold_count
    target_neg = total_neg / fold_count
    fold_indices: list[list[int]] = [[] for _ in range(fold_count)]
    fold_pos = [0] * fold_count
    fold_neg = [0] * fold_count
    fold_rows = [0] * fold_count

    def group_key(item: tuple[str, list[int]]) -> tuple[int, int, str]:
        group, indices = item
        pos = sum(smoke.target_y(rows[idx]) for idx in indices)
        neg = len(indices) - pos
        return (len(indices), abs(pos - neg), group)

    target_rows = len(rows) / fold_count
    for order, (_, indices) in enumerate(sorted(groups.items(), key=group_key, reverse=True)):
        pos = sum(smoke.target_y(rows[idx]) for idx in indices)
        neg = len(indices) - pos
        if order < fold_count:
            best_fold = order
        else:
            best_fold = min(
                range(fold_count),
                key=lambda fold: (
                    fold_rows[fold]
                    + 0.01 * abs((fold_rows[fold] + len(indices)) - target_rows)
                    + abs((fold_pos[fold] + pos) - target_pos)
                    + abs((fold_neg[fold] + neg) - target_neg),
                    fold_rows[fold],
                    fold,
                ),
            )
        fold_indices[best_fold].extend(indices)
        fold_pos[best_fold] += pos
        fold_neg[best_fold] += neg
        fold_rows[best_fold] += len(indices)

    summary = []
    for fold, indices in enumerate(fold_indices):
        group_set = {str(rows[idx]["identity"]["scan_id"]) for idx in indices}
        pos = sum(smoke.target_y(rows[idx]) for idx in indices)
        neg = len(indices) - pos
        summary.append(
            {
                "fold": fold,
                "rows": len(indices),
                "groups": len(group_set),
                "positive": pos,
                "negative": neg,
            }
        )
    return fold_indices, summary


def train_predict_grouped(
    rows: list[dict[str, Any]],
    baseline: str,
    *,
    folds: int,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[float], dict[str, Any]]:
    fold_indices, fold_summary = grouped_folds(rows, folds)
    all_probs = [0.5] * len(rows)
    feature_counts = []
    skipped_single_class_train = 0
    for test_indices in fold_indices:
        test_set = set(test_indices)
        train_rows = [row for idx, row in enumerate(rows) if idx not in test_set]
        test_rows = [rows[idx] for idx in test_indices]
        train_labels = {smoke.target_y(row) for row in train_rows}
        if train_labels != {0, 1}:
            skipped_single_class_train += 1
            prior = sum(smoke.target_y(row) for row in train_rows) / max(len(train_rows), 1)
            for idx in test_indices:
                all_probs[idx] = prior
            continue
        schema = smoke.split_feature_types(train_rows, baseline)
        train_raw = smoke.vectorize(train_rows, baseline, schema)
        test_raw = smoke.vectorize(test_rows, baseline, schema)
        means, stds = smoke.fit_scaler(train_raw)
        train_xs = smoke.apply_scaler(train_raw, means, stds)
        test_xs = smoke.apply_scaler(test_raw, means, stds)
        train_ys = [smoke.target_y(row) for row in train_rows]
        train_weights = [smoke.target_weight(row) for row in train_rows]
        weights = smoke.fit_logistic(
            train_xs,
            train_ys,
            train_weights,
            epochs=epochs,
            learning_rate=learning_rate,
            l2=l2,
        )
        probs = smoke.predict_probs(test_xs, weights)
        for idx, prob in zip(test_indices, probs):
            all_probs[idx] = prob
        feature_counts.append(len(smoke.vector_names(schema)))
    return all_probs, {
        "fold_count": len(fold_indices),
        "folds": fold_summary,
        "feature_count_min": min(feature_counts) if feature_counts else 0,
        "feature_count_max": max(feature_counts) if feature_counts else 0,
        "group_key": "scan_id",
        "skipped_single_class_train_folds": skipped_single_class_train,
    }


def target_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    y_counts = Counter(smoke.target_y(row) for row in rows)
    return {
        "rows": len(rows),
        "positive": y_counts[1],
        "negative": y_counts[0],
        "by_queue": dict(sorted(Counter(str(row["target"]["queue_kind"]) for row in rows).items())),
        "by_family": dict(sorted(Counter(str(row["identity"]["predicate_family"]) for row in rows).items())),
        "by_label_status": dict(sorted(Counter(str(row["target"]["label_match_status"]) for row in rows).items())),
        "by_final_label": dict(sorted(Counter(str(row["target"]["final_controlled_label"]) for row in rows).items())),
        "by_taxonomy": dict(sorted(Counter(str(row["target"]["failure_taxonomy_label"]) for row in rows).items())),
    }


def metric_record(kind: str, split_eval: str, name: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": kind,
        "target_mode": TARGET_MODE,
        "split_eval": split_eval,
        "name": name,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


def probe_scores(rows: list[dict[str, Any]], probe_name: str) -> list[float]:
    scores = []
    for row in rows:
        features = row["baseline_inputs"]["factorized_reliability_posterior"]
        if probe_name == "semantic_score_norm":
            score = safe_float(features.get("semantic_score_norm"))
        elif probe_name == "negative_semantic_score_norm":
            score = safe_float(features.get("negative_semantic_score_norm"))
        elif probe_name == "semantic_rank_inverse":
            score = safe_float(features.get("semantic_rank_inverse"))
        elif probe_name == "p_geom_valid":
            score = safe_float(features.get("p_geom_valid"))
        elif probe_name == "negative_p_geom_valid":
            score = safe_float(features.get("p_geom_invalid"))
        elif probe_name == "absolute_disagreement":
            score = safe_float(features.get("absolute_disagreement"))
        elif probe_name == "underconfidence_score":
            score = safe_float(features.get("underconfidence_score"))
        elif probe_name == "overconfidence_score":
            score = safe_float(features.get("overconfidence_score"))
        else:
            raise ValueError(f"unknown probe: {probe_name}")
        scores.append(score)
    return scores


def comparison(metric_rows: list[dict[str, Any]], split_eval: str, left: str, right: str) -> dict[str, Any]:
    by_name = {
        row["name"]: row["metrics"]
        for row in metric_rows
        if row["split_eval"] == split_eval
    }
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


def family_slices(score_by_view: dict[str, list[float]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    families = sorted({str(row["identity"]["predicate_family"]) for row in rows})
    for family in families:
        indices = [idx for idx, row in enumerate(rows) if str(row["identity"]["predicate_family"]) == family]
        family_rows = [rows[idx] for idx in indices]
        y_set = {smoke.target_y(row) for row in family_rows}
        for view_name, scores in score_by_view.items():
            selected_scores = [scores[idx] for idx in indices]
            if y_set == {0, 1}:
                metrics = smoke.metrics([smoke.target_y(row) for row in family_rows], selected_scores)
            else:
                counts = Counter(smoke.target_y(row) for row in family_rows)
                metrics = {
                    "rows": len(family_rows),
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
                    "predicate_family": family,
                    "view": view_name,
                    "split_eval": "train_internal_5fold_slice",
                    "metrics": metrics,
                    "single_class": y_set != {0, 1},
                }
            )
    return outputs


def build_rank_matched_pairs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    used_negatives: set[int] = set()
    rows_by_family: dict[str, list[int]] = {}
    for idx, row in enumerate(rows):
        rows_by_family.setdefault(str(row["identity"]["predicate_family"]), []).append(idx)
    pair_id = 0
    for family, indices in sorted(rows_by_family.items()):
        positives = [idx for idx in indices if smoke.target_y(rows[idx]) == 1]
        negatives = [idx for idx in indices if smoke.target_y(rows[idx]) == 0]
        for pos_idx in sorted(positives, key=lambda idx: safe_float(rows[idx]["target"].get("semantic_rank"), 0.0)):
            available = [idx for idx in negatives if idx not in used_negatives]
            if not available:
                break
            pos_rank = safe_float(rows[pos_idx]["target"].get("semantic_rank"), 0.0)
            neg_idx = min(
                available,
                key=lambda idx: (
                    abs(safe_float(rows[idx]["target"].get("semantic_rank"), 0.0) - pos_rank),
                    str(rows[idx]["identity"]["prediction_id"]),
                ),
            )
            used_negatives.add(neg_idx)
            neg_rank = safe_float(rows[neg_idx]["target"].get("semantic_rank"), 0.0)
            pair_id += 1
            pairs.append(
                {
                    "pair_id": pair_id,
                    "predicate_family": family,
                    "positive_index": pos_idx,
                    "negative_index": neg_idx,
                    "positive_prediction_id": rows[pos_idx]["identity"]["prediction_id"],
                    "negative_prediction_id": rows[neg_idx]["identity"]["prediction_id"],
                    "rank_gap": abs(pos_rank - neg_rank),
                }
            )
    return pairs


def pairwise_metrics(pairs: list[dict[str, Any]], score_by_view: dict[str, list[float]]) -> list[dict[str, Any]]:
    outputs = []
    for view_name, scores in score_by_view.items():
        wins = 0.0
        for pair in pairs:
            pos_score = scores[pair["positive_index"]]
            neg_score = scores[pair["negative_index"]]
            if pos_score > neg_score:
                wins += 1.0
            elif pos_score == neg_score:
                wins += 0.5
        outputs.append(
            {
                "view": view_name,
                "pairs": len(pairs),
                "pairwise_accuracy": wins / len(pairs) if pairs else None,
            }
        )
    return outputs


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
        "# H002 Full Train Controlled Posterior Smoke",
        "",
        f"Created: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage smoke.",
        "- No validation/test rows are used.",
        "- Labels are `(codex_ver_full_train)` bootstrap labels.",
        "- `V_mv_e` is not used as model input.",
        "- Results are not paper-level metrics.",
        "",
        "## Target Counts",
        "",
        "| Rows | Positive | Negative |",
        "| ---: | ---: | ---: |",
        f"| {summary['target_summary']['rows']} | {summary['target_summary']['positive']} | {summary['target_summary']['negative']} |",
        "",
        "## Grouped Main Views",
        "",
        "| View | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["metric_rows"]:
        if row["kind"] != "main" or row["split_eval"] != "train_internal_grouped_by_scan":
            continue
        m = row["metrics"]
        lines.append(
            f"| `{row['name']}` | {fmt(m['auroc'])} | {fmt(m['auprc'])} | "
            f"{fmt(m['brier'])} | {fmt(m['ece_5bin'])} | {fmt(m['accuracy_at_0_5'])} |"
        )
    lines.extend(
        [
            "",
            "## Grouped Proxy Controls",
            "",
            "| View | AUROC | AUPRC | Brier |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["kind"] != "proxy" or row["split_eval"] != "train_internal_grouped_by_scan":
            continue
        m = row["metrics"]
        lines.append(f"| `{row['name']}` | {fmt(m['auroc'])} | {fmt(m['auprc'])} | {fmt(m['brier'])} |")
    lines.extend(
        [
            "",
            "## Key Deltas",
            "",
            "| Eval | Left | Right | Delta AUROC | Delta AUPRC | Delta Brier |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["comparisons"]:
        if row["split_eval"] != "train_internal_grouped_by_scan":
            continue
        d = row["delta"]
        lines.append(
            f"| `{row['split_eval']}` | `{row['left']}` | `{row['right']}` | "
            f"{fmt(d['auroc'])} | {fmt(d['auprc'])} | {fmt(d['brier'])} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_jsonl(output_dir / "full_train_controlled_codex_ver_rows.jsonl", rows)
    with (output_dir / "metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
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
        writer.writeheader()
        for row in summary["metric_rows"]:
            writer.writerow(
                {
                    "kind": row["kind"],
                    "target_mode": row["target_mode"],
                    "split_eval": row["split_eval"],
                    "name": row["name"],
                    **row["metrics"],
                }
            )
    family_csv_rows = []
    for item in summary["family_slices"]:
        family_csv_rows.append(
            {
                "predicate_family": item["predicate_family"],
                "view": item["view"],
                "split_eval": item["split_eval"],
                "single_class": item["single_class"],
                **item["metrics"],
            }
        )
    write_csv(
        output_dir / "family_slices.csv",
        family_csv_rows,
        [
            "predicate_family",
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
    smoke.write_jsonl(output_dir / "matched_pairs.jsonl", summary["matched_pairs"])
    write_csv(output_dir / "pairwise.csv", summary["pairwise_metrics"], ["view", "pairs", "pairwise_accuracy"])
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    targets = smoke.read_jsonl(args.targets)
    rows = build_rows(targets)
    metric_rows = []
    score_by_view_grouped: dict[str, list[float]] = {}
    score_by_view_crossfit: dict[str, list[float]] = {}
    feature_summaries: dict[str, Any] = {}

    view_sets = [
        ("main", MAIN_VIEWS),
        ("diagnostic", DIAGNOSTIC_VIEWS),
        ("proxy", PROXY_VIEWS),
    ]
    for kind, view_names in view_sets:
        for view_name in view_names:
            in_probs, in_summary = smoke.train_predict_in_sample(
                rows,
                view_name,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            cross_probs, cross_summary = smoke.train_predict_crossfit(
                rows,
                view_name,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            grouped_probs, grouped_summary = train_predict_grouped(
                rows,
                view_name,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            feature_summaries[view_name] = {
                "in_sample": in_summary,
                "crossfit": cross_summary,
                "grouped": grouped_summary,
            }
            for split_eval, probs in [
                ("in_sample", in_probs),
                ("train_internal_5fold", cross_probs),
                ("train_internal_grouped_by_scan", grouped_probs),
            ]:
                metric_rows.append(metric_record(kind, split_eval, view_name, rows, probs))
            score_by_view_crossfit[view_name] = cross_probs
            score_by_view_grouped[view_name] = grouped_probs

    for probe_name in PROBE_NAMES:
        scores = probe_scores(rows, probe_name)
        metric_rows.append(metric_record("probe", "score_probe", probe_name, rows, scores))
        score_by_view_crossfit[probe_name] = scores

    comparisons = []
    for split_eval in ["train_internal_5fold", "train_internal_grouped_by_scan"]:
        for left, right in [
            ("factorized_reliability_posterior", "semantic_plus_geometry"),
            ("residual_reliability_model", "semantic_plus_geometry"),
            ("continuous_safe", "semantic_plus_geometry"),
            ("factorized_reliability_posterior", "negative_rank_only"),
            ("factorized_reliability_posterior", "queue_only"),
            ("factorized_reliability_posterior", "proposed_role_only"),
            ("factorized_reliability_posterior", "label_status_only"),
            ("semantic_plus_geometry", "queue_only"),
        ]:
            comparisons.append(comparison(metric_rows, split_eval, left, right))

    pairs = build_rank_matched_pairs(rows)
    pairwise = pairwise_metrics(pairs, score_by_view_crossfit)
    family_slice_rows = family_slices(score_by_view_crossfit, rows)

    def pick_delta(split_eval: str, left: str, right: str) -> dict[str, Any]:
        return next(
            row["delta"]
            for row in comparisons
            if row["split_eval"] == split_eval and row["left"] == left and row["right"] == right
        )

    f_sg_grouped = pick_delta(
        "train_internal_grouped_by_scan",
        "factorized_reliability_posterior",
        "semantic_plus_geometry",
    )
    f_queue_grouped = pick_delta(
        "train_internal_grouped_by_scan",
        "factorized_reliability_posterior",
        "queue_only",
    )
    f_role_grouped = pick_delta(
        "train_internal_grouped_by_scan",
        "factorized_reliability_posterior",
        "proposed_role_only",
    )
    positive_delta = (
        f_sg_grouped.get("auprc") is not None
        and f_sg_grouped["auprc"] >= 0.03
    ) or (
        f_sg_grouped.get("brier") is not None
        and f_sg_grouped["brier"] <= -0.02
    )
    proxy_blocked = any(
        delta.get("auprc") is not None and delta["auprc"] <= 0.0
        for delta in [f_queue_grouped, f_role_grouped]
    )
    if proxy_blocked:
        status = "full_train_posterior_proxy_blocked"
        decision = (
            "Full-train codex_ver labels are executable, but proxy controls such "
            "as queue/proposed-role explain the target at least as well as the "
            "factorized view. This is target-policy evidence, not posterior "
            "method evidence."
        )
    elif positive_delta:
        status = "full_train_posterior_positive_bootstrap_signal"
        decision = (
            "The factorized view improves over semantic_plus_geometry under "
            "train-only grouped folds, but the labels are codex bootstrap labels. "
            "Treat this only as a reason to collect independent labels."
        )
    else:
        status = "full_train_posterior_no_strong_signal"
        decision = (
            "The full-train codex_ver target is executable, but it does not show "
            "a strong factorized posterior advantage over semantic_plus_geometry."
        )

    summary = {
        "schema_version": "h002_full_train_controlled_posterior_smoke_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "targets": smoke.rel_path(args.targets),
        },
        "output_dir": smoke.rel_path(output_dir),
        "hyperparameters": {
            "folds": args.folds,
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "l2": args.l2,
            "tuned_on_validation": False,
            "uses_validation_rows": False,
        },
        "boundary": {
            "split": "train_full_only",
            "label_source": "codex_ver_full_train_policy_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "label_evidence_as_input": False,
            "vmv_model_input_allowed": False,
            "validation_usage": False,
            "test_usage": False,
        },
        "target_summary": target_summary(rows),
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "family_slices": family_slice_rows,
        "matched_pairs": pairs,
        "pairwise_metrics": pairwise,
        "feature_summaries": feature_summaries,
        "quick_deltas": {
            "grouped_factorized_minus_sg": f_sg_grouped,
            "grouped_factorized_minus_queue": f_queue_grouped,
            "grouped_factorized_minus_proposed_role": f_role_grouped,
        },
        "decision": decision,
    }
    write_outputs(output_dir, summary, rows)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    q = summary["quick_deltas"]
    print(
        "status={status} rows={rows} pos={pos} neg={neg} metrics={metrics} "
        "validation_used={validation_used} grouped_factorized_d_auprc={d_auprc:.4f} "
        "grouped_factorized_vs_queue_d_auprc={q_auprc:.4f}".format(
            status=summary["status"],
            rows=summary["target_summary"]["rows"],
            pos=summary["target_summary"]["positive"],
            neg=summary["target_summary"]["negative"],
            metrics=len(summary["metric_rows"]),
            validation_used=summary["hyperparameters"]["uses_validation_rows"],
            d_auprc=q["grouped_factorized_minus_sg"]["auprc"],
            q_auprc=q["grouped_factorized_minus_queue"]["auprc"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
