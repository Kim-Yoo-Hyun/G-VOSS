#!/usr/bin/env python3
"""Train-only posterior smoke on H002 independent controlled target slices."""

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
DEFAULT_TARGET_SLICE = (
    RGA_ROOT
    / "independent_target_independence_audit_codex_ver/target_slices/proposed_role_balanced_codex_ver.jsonl"
)
DEFAULT_REFERENCE_TARGET = (
    RGA_ROOT
    / "independent_target_independence_audit_codex_ver/target_slices/original_independent_codex_ver.jsonl"
)
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_controlled_posterior_smoke_codex_ver"

TARGET_MODE = "proposed_role_balanced_codex_ver"

MAIN_VIEWS = [
    "semantic_only",
    "geometry_only",
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
]

DIAGNOSTIC_VIEWS = [
    "residual_reliability_model",
    "semantic_score_only",
    "geometry_continuous_only",
    "rank_only",
    "p_geom_valid_only",
]

PROBE_NAMES = [
    "semantic_score_norm",
    "negative_semantic_score_norm",
    "semantic_rank_inverse",
    "p_geom_valid",
    "negative_p_geom_valid",
    "consistency_score",
    "absolute_disagreement",
    "underconfidence_score",
    "overconfidence_score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-slice", type=Path, default=DEFAULT_TARGET_SLICE)
    parser.add_argument("--reference-target", type=Path, default=DEFAULT_REFERENCE_TARGET)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def safe_float(value: Any, default: float = 0.0) -> float:
    return smoke.safe_float(value, default)


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def rank_block(rank_value: float) -> dict[str, float]:
    rank = max(float(rank_value), 1.0)
    return {
        "semantic_rank": rank,
        "semantic_rank_log": math.log1p(rank),
        "semantic_rank_inverse": 1.0 / rank,
    }


def build_baseline_inputs(source: dict[str, Any]) -> dict[str, dict[str, Any]]:
    evidence = source["deployable_evidence_after_label_lock"]
    semantic = safe_float(evidence.get("semantic_score_norm"), 0.0)
    semantic_raw = safe_float(evidence.get("semantic_score_raw"), semantic)
    rank = safe_float(evidence.get("semantic_rank"), 0.0)
    p_geom = safe_float(evidence.get("p_geom_valid"), 0.5)
    consistency = safe_float(evidence.get("consistency_score"), 0.0)
    disagreement = abs(semantic - p_geom)
    underconfidence = max(0.0, p_geom - semantic)
    overconfidence = max(0.0, semantic - p_geom)
    raw_disagreement = safe_float(evidence.get("disagreement_score"), disagreement)
    rank_features = rank_block(rank)

    semantic_block = {
        "semantic_score_raw": semantic_raw,
        "semantic_score_norm": semantic,
        "negative_semantic_score_norm": 1.0 - semantic,
        **rank_features,
    }
    geometry_block = {
        "p_geom_valid": p_geom,
        "p_geom_invalid": 1.0 - p_geom,
        "consistency_score": consistency,
    }
    factorized = {
        **semantic_block,
        **geometry_block,
        "absolute_disagreement": disagreement,
        "reported_disagreement_score": raw_disagreement,
        "semantic_minus_geometry": semantic - p_geom,
        "geometry_minus_semantic": p_geom - semantic,
        "underconfidence_score": underconfidence,
        "overconfidence_score": overconfidence,
        "semantic_x_geometry": semantic * p_geom,
        "semantic_x_consistency": semantic * consistency,
        "geometry_x_consistency": p_geom * consistency,
    }
    return {
        "semantic_only": semantic_block,
        "geometry_only": geometry_block,
        "semantic_plus_geometry": {**semantic_block, **geometry_block},
        "factorized_reliability_posterior": factorized,
        "residual_reliability_model": {
            **semantic_block,
            **geometry_block,
            "semantic_minus_geometry": semantic - p_geom,
            "geometry_minus_semantic": p_geom - semantic,
            "absolute_disagreement": disagreement,
        },
        "semantic_score_only": {"semantic_score_norm": semantic},
        "geometry_continuous_only": dict(geometry_block),
        "rank_only": {
            **rank_features,
            "negative_semantic_score_norm": 1.0 - semantic,
        },
        "p_geom_valid_only": {"p_geom_valid": p_geom},
    }


def build_rows(targets: list[dict[str, Any]], target_mode: str) -> list[dict[str, Any]]:
    rows = []
    for target in targets:
        hidden = target.get("hidden_audit_metadata_post_label_only", {})
        row = {
            "schema_version": "h002_full_train_independent_controlled_posterior_row_v0",
            "record_type": "h002_full_train_independent_controlled_posterior_row",
            "identity": {
                "prediction_id": target["prediction_id"],
                "blind_review_id": target["blind_review_id"],
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
                "target_mode": target_mode,
                "y": int(target["posterior_target"]),
                "sample_weight": 1.0,
                "relation_validity_label": target.get("independent_relation_label"),
                "label_use": target.get("label_use"),
                "reviewer_id": target.get("reviewer_id"),
                "confidence": target.get("confidence"),
                "predicate_family": target.get("predicate_family"),
                "predicate_label": target.get("predicate_label"),
                "semantic_rank": target.get("deployable_evidence_after_label_lock", {}).get("semantic_rank"),
                "balanced_keys": target.get("balanced_keys", []),
                "target_slice_reason": target.get("target_slice_reason"),
                "audit_selection_only": bool(target.get("audit_selection_only")),
                "queue_kind_hidden": hidden.get("queue_kind_hidden"),
                "proposed_audit_role_hidden": hidden.get("proposed_audit_role_hidden"),
                "label_match_status_hidden": hidden.get("label_match_status_hidden"),
                "geometry_status_hidden": hidden.get("geometry_status_hidden"),
                "rank_band_hidden": hidden.get("rank_band_hidden"),
                "label_source": "codex_ver_full_train_independent_visible_surface_bootstrap",
                "human_confirmed": False,
                "paper_locked": False,
                "allowed_use": "train-only controlled posterior smoke",
            },
            "provenance": {
                "target_source": "independent_target_independence_audit_codex_ver/target_slices",
                "split_policy": "train_only",
                "hidden_metadata_as_model_input": False,
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
        schema = smoke.split_feature_types(train_rows, baseline)
        train_raw = smoke.vectorize(train_rows, baseline, schema)
        test_raw = smoke.vectorize(test_rows, baseline, schema)
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


def target_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(smoke.target_y(row) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "by_family": dict(sorted(Counter(str(row["identity"]["predicate_family"]) for row in rows).items())),
        "by_predicate": dict(sorted(Counter(str(row["identity"]["predicate_label"]) for row in rows).items())),
        "by_label": dict(sorted(Counter(str(row["target"]["relation_validity_label"]) for row in rows).items())),
        "by_confidence": dict(sorted(Counter(str(row["target"]["confidence"]) for row in rows).items())),
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
        elif probe_name == "consistency_score":
            score = safe_float(features.get("consistency_score"))
        elif probe_name == "absolute_disagreement":
            score = safe_float(features.get("absolute_disagreement"))
        elif probe_name == "underconfidence_score":
            score = safe_float(features.get("underconfidence_score"))
        elif probe_name == "overconfidence_score":
            score = safe_float(features.get("overconfidence_score"))
        else:
            raise ValueError(f"unsupported probe: {probe_name}")
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
    for family in sorted({str(row["identity"]["predicate_family"]) for row in rows}):
        indices = [idx for idx, row in enumerate(rows) if str(row["identity"]["predicate_family"]) == family]
        family_rows = [rows[idx] for idx in indices]
        labels = {smoke.target_y(row) for row in family_rows}
        for view, scores in score_by_view.items():
            selected = [scores[idx] for idx in indices]
            if labels == {0, 1}:
                metrics = smoke.metrics([smoke.target_y(row) for row in family_rows], selected)
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
                    "view": view,
                    "split_eval": "train_internal_grouped_by_scan_slice",
                    "single_class": labels != {0, 1},
                    "metrics": metrics,
                }
            )
    return outputs


def matched_pairs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs = []
    used_negatives: set[int] = set()
    rows_by_family: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        rows_by_family[str(row["identity"]["predicate_family"])].append(idx)
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
            pair_id += 1
            pairs.append(
                {
                    "pair_id": pair_id,
                    "predicate_family": family,
                    "positive_index": pos_idx,
                    "negative_index": neg_idx,
                    "positive_prediction_id": rows[pos_idx]["identity"]["prediction_id"],
                    "negative_prediction_id": rows[neg_idx]["identity"]["prediction_id"],
                    "rank_gap": abs(
                        safe_float(rows[pos_idx]["target"].get("semantic_rank"), 0.0)
                        - safe_float(rows[neg_idx]["target"].get("semantic_rank"), 0.0)
                    ),
                }
            )
    return pairs


def pairwise_metrics(pairs: list[dict[str, Any]], score_by_view: dict[str, list[float]]) -> list[dict[str, Any]]:
    output = []
    for view, scores in score_by_view.items():
        wins = 0.0
        for pair in pairs:
            pos_score = scores[pair["positive_index"]]
            neg_score = scores[pair["negative_index"]]
            if pos_score > neg_score:
                wins += 1.0
            elif pos_score == neg_score:
                wins += 0.5
        output.append({"view": view, "pairs": len(pairs), "pairwise_accuracy": wins / len(pairs) if pairs else None})
    return output


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
        "# H002 Full Train Independent Controlled Posterior Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage posterior smoke.",
        "- The original 283-row target is not used as the claim target.",
        "- The active target is `proposed_role_balanced_codex_ver`.",
        "- No validation/test rows are used.",
        "- Hidden audit metadata is not used as model input.",
        "- Labels are Codex bootstrap labels, not human-confirmed paper evidence.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Target",
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
            f"| `{row['name']}` | {fmt(m['auroc'])} | {fmt(m['auprc'])} | {fmt(m['brier'])} | "
            f"{fmt(m['ece_5bin'])} | {fmt(m['accuracy_at_0_5'])} |"
        )
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
    lines.extend(["", "## Decision", "", summary["decision"], "", "## Next TODO", "", summary["next_todo"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any], rows: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> None:
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_jsonl(output_dir / "controlled_posterior_rows.jsonl", rows)
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
    family_rows = []
    for item in summary["family_slices"]:
        family_rows.append(
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
        family_rows,
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
    write_csv(output_dir / "pairwise.csv", summary["pairwise_metrics"], ["view", "pairs", "pairwise_accuracy"])
    smoke.write_jsonl(output_dir / "matched_pairs.jsonl", summary["matched_pairs"])
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    targets = smoke.read_jsonl(args.target_slice)
    reference_targets = smoke.read_jsonl(args.reference_target) if smoke.as_abs(args.reference_target).exists() else []
    rows = build_rows(targets, TARGET_MODE)

    metric_rows = []
    feature_summaries: dict[str, Any] = {}
    score_by_view_grouped: dict[str, list[float]] = {}
    score_by_view_crossfit: dict[str, list[float]] = {}
    predictions: list[dict[str, Any]] = []

    view_sets = [
        ("main", MAIN_VIEWS),
        ("diagnostic", DIAGNOSTIC_VIEWS),
    ]
    for kind, views in view_sets:
        for view in views:
            in_probs, in_summary = smoke.train_predict_in_sample(
                rows,
                view,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            cross_probs, cross_summary = smoke.train_predict_crossfit(
                rows,
                view,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            grouped_probs, grouped_summary = train_predict_grouped(
                rows,
                view,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            feature_summaries[view] = {
                "in_sample": in_summary,
                "crossfit": cross_summary,
                "grouped": grouped_summary,
            }
            for split_eval, probs in [
                ("in_sample", in_probs),
                ("train_internal_3fold", cross_probs),
                ("train_internal_grouped_by_scan", grouped_probs),
            ]:
                metric_rows.append(metric_record(kind, split_eval, view, rows, probs))
            score_by_view_crossfit[view] = cross_probs
            score_by_view_grouped[view] = grouped_probs
            for row, prob in zip(rows, grouped_probs):
                predictions.append(
                    {
                        "prediction_id": row["identity"]["prediction_id"],
                        "view": view,
                        "split_eval": "train_internal_grouped_by_scan",
                        "posterior_target": smoke.target_y(row),
                        "probability": prob,
                    }
                )

    for probe_name in PROBE_NAMES:
        scores = probe_scores(rows, probe_name)
        metric_rows.append(metric_record("probe", "score_probe", probe_name, rows, scores))
        score_by_view_crossfit[probe_name] = scores

    comparisons = []
    for split_eval in ["train_internal_3fold", "train_internal_grouped_by_scan"]:
        for left, right in [
            ("factorized_reliability_posterior", "semantic_plus_geometry"),
            ("factorized_reliability_posterior", "semantic_only"),
            ("factorized_reliability_posterior", "geometry_only"),
            ("semantic_plus_geometry", "semantic_only"),
            ("semantic_plus_geometry", "geometry_only"),
            ("residual_reliability_model", "semantic_plus_geometry"),
        ]:
            comparisons.append(comparison(metric_rows, split_eval, left, right))

    pairs = matched_pairs(rows)
    pairwise = pairwise_metrics(pairs, score_by_view_crossfit)
    family_slice_rows = family_slices(score_by_view_grouped, rows)

    def pick_delta(split_eval: str, left: str, right: str) -> dict[str, Any]:
        return next(
            item["delta"]
            for item in comparisons
            if item["split_eval"] == split_eval and item["left"] == left and item["right"] == right
        )

    grouped_factorized_minus_sg = pick_delta(
        "train_internal_grouped_by_scan",
        "factorized_reliability_posterior",
        "semantic_plus_geometry",
    )
    grouped_factorized_minus_semantic = pick_delta(
        "train_internal_grouped_by_scan",
        "factorized_reliability_posterior",
        "semantic_only",
    )
    grouped_factorized_minus_geometry = pick_delta(
        "train_internal_grouped_by_scan",
        "factorized_reliability_posterior",
        "geometry_only",
    )

    positive_signal = (
        grouped_factorized_minus_sg.get("auprc") is not None
        and grouped_factorized_minus_sg["auprc"] >= 0.02
        and grouped_factorized_minus_semantic.get("auprc") is not None
        and grouped_factorized_minus_semantic["auprc"] >= 0.02
        and grouped_factorized_minus_geometry.get("auprc") is not None
        and grouped_factorized_minus_geometry["auprc"] >= 0.02
    ) or (
        grouped_factorized_minus_sg.get("brier") is not None
        and grouped_factorized_minus_sg["brier"] <= -0.02
    )
    if positive_signal:
        status = "full_train_independent_controlled_posterior_positive_smoke"
        decision = (
            "On the proposed-role-balanced train-only slice, the factorized view "
            "shows a positive diagnostic signal over simpler baselines. Treat this "
            "as hypothesis-stage evidence only because labels are Codex bootstrap labels."
        )
        next_todo = "full_train_independent_controlled_error_analysis"
    else:
        status = "full_train_independent_controlled_posterior_no_strong_signal"
        decision = (
            "The controlled slice is executable, but factorized reliability does not "
            "show a strong advantage over semantic_plus_geometry under grouped folds. "
            "Inspect errors and feature definitions before expanding claims."
        )
        next_todo = "full_train_independent_controlled_error_analysis"

    summary = {
        "schema_version": "h002_full_train_independent_controlled_posterior_smoke_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "target_slice": smoke.rel_path(args.target_slice),
            "reference_target": smoke.rel_path(args.reference_target),
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
            "split": "train_only",
            "target_mode": TARGET_MODE,
            "reference_target_rows": len(reference_targets),
            "label_source": "codex_ver_full_train_independent_visible_surface_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_metadata_as_model_input": False,
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
            "grouped_factorized_minus_semantic_plus_geometry": grouped_factorized_minus_sg,
            "grouped_factorized_minus_semantic_only": grouped_factorized_minus_semantic,
            "grouped_factorized_minus_geometry_only": grouped_factorized_minus_geometry,
        },
        "decision": decision,
        "next_todo": next_todo,
    }
    write_outputs(output_dir, summary, rows, predictions)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    deltas = summary["quick_deltas"]
    print(
        "status={status} rows={rows} pos={pos} neg={neg} metrics={metrics} "
        "validation_used={validation_used} d_auprc_factorized_vs_sg={d_sg:.4f} "
        "d_auprc_factorized_vs_semantic={d_sem:.4f} d_auprc_factorized_vs_geometry={d_geom:.4f}".format(
            status=summary["status"],
            rows=summary["target_summary"]["rows"],
            pos=summary["target_summary"]["positive"],
            neg=summary["target_summary"]["negative"],
            metrics=len(summary["metric_rows"]),
            validation_used=summary["hyperparameters"]["uses_validation_rows"],
            d_sg=deltas["grouped_factorized_minus_semantic_plus_geometry"]["auprc"],
            d_sem=deltas["grouped_factorized_minus_semantic_only"]["auprc"],
            d_geom=deltas["grouped_factorized_minus_geometry_only"]["auprc"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
