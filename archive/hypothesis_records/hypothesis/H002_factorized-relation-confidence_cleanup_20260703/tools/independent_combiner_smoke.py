#!/usr/bin/env python3
"""Train-only independent-label combiner smoke for H002."""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke
import redesigned_target_smoke as redesigned


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_FEATURES = RGA_ROOT / "factor_dataset/deployable_features_all.jsonl"
DEFAULT_TARGETS = RGA_ROOT / "independent_label_ingestion_codex_ver/binary_targets.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_combiner_smoke_codex_ver"

TARGET_MODE = "independent_codex_ver_blind"

MAIN_VIEWS = [
    "semantic_only",
    "geometry_only",
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
    "residual_reliability_model",
    "gated_evidence_model",
]

FACTOR_ABLATION_VIEWS = [
    "semantic_geometry_coverage",
    "semantic_geometry_uncertainty",
    "semantic_geometry_coverage_uncertainty",
]

CONTROL_VIEWS = [
    "drop_direct_identity",
    "drop_direct_identity_rank",
    "safe_continuous",
    "geometry_continuous_only",
    "semantic_raw_only",
]

PROXY_VIEWS = [
    "rank_only",
    "negative_rank_only",
    "rank_band_only",
    "family_only",
    "predicate_only",
    "p_geom_valid_only",
]

PROBE_NAMES = [
    "semantic_score_raw",
    "semantic_score_norm",
    "negative_semantic_score_norm",
    "p_geom_valid",
    "consistency_score",
    "negative_geometry_residual",
]

COVERAGE_KEYS = {
    "coverage_state",
    "covered_and_uncertain",
    "covered_checkable",
    "geometry_available",
    "geometry_checkable",
    "missing_geometry",
    "p_geom_valid_available",
    "predicate_family_supported",
    "unsupported_family",
}

UNCERTAINTY_KEYS = {
    "absolute_disagreement",
    "covered_and_uncertain",
    "geometry_status_is_uncertain",
    "geometry_status_is_unsupported",
    "geometry_status_uncertain",
    "geometry_status_unsupported",
    "semantic_geometry_disagreement_score",
    "semantic_score_norm_minus_p_geom_valid",
    "underconfidence_score",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def load_features(path: Path) -> dict[str, dict[str, Any]]:
    rows = smoke.read_jsonl(path)
    by_id = {}
    for row in rows:
        prediction_id = str(row["identity"]["prediction_id"])
        if prediction_id in by_id:
            raise ValueError(f"duplicate feature prediction_id: {prediction_id}")
        by_id[prediction_id] = row
    return by_id


def rank_band(rank: Any) -> str:
    rank_value = int(smoke.safe_float(rank, 0.0))
    if rank_value <= 50:
        return "rank_1_50"
    if rank_value <= 100:
        return "rank_51_100"
    if rank_value <= 200:
        return "rank_101_200"
    if rank_value <= 500:
        return "rank_201_500"
    if rank_value <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def target_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    y_counts = Counter(smoke.target_y(row) for row in rows)
    label_counts = Counter(str(row["target"].get("relation_validity_label")) for row in rows)
    family_counts = Counter(str(row["identity"].get("predicate_family")) for row in rows)
    family_y_counts = Counter(
        (str(row["identity"].get("predicate_family")), smoke.target_y(row))
        for row in rows
    )
    return {
        "rows": len(rows),
        "positive": y_counts[1],
        "negative": y_counts[0],
        "relation_validity_labels": dict(sorted(label_counts.items())),
        "predicate_families": dict(sorted(family_counts.items())),
        "predicate_family_y_counts": [
            {"predicate_family": key[0], "y": key[1], "rows": value}
            for key, value in sorted(family_y_counts.items())
        ],
    }


def build_rows(
    targets: list[dict[str, Any]],
    features_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    missing = []
    for target in targets:
        prediction_id = str(target["prediction_id"])
        feature = features_by_id.get(prediction_id)
        if feature is None:
            missing.append(prediction_id)
            continue
        row = deepcopy(feature)
        row.pop("feature_blocks", None)
        row.pop("leakage_boundary", None)
        fact = row["baseline_inputs"]["factorized_reliability_posterior"]
        row["schema_version"] = "h002_independent_combiner_smoke_row_v0"
        row["record_type"] = "h002_independent_combiner_smoke_row"
        row["provenance"] = {
            "feature_source": "factor_dataset/deployable_features_all.jsonl",
            "target_source": "independent_label_ingestion_codex_ver/binary_targets.jsonl",
            "split_policy": "train_only",
        }
        row["target"] = {
            "target_mode": TARGET_MODE,
            "y": int(target["posterior_target"]),
            "sample_weight": 1.0,
            "blind_review_id": target.get("blind_review_id"),
            "relation_validity_label": target.get("relation_validity_label"),
            "label_use": target.get("label_use"),
            "reviewer_id": target.get("reviewer_id"),
            "confidence": target.get("confidence"),
            "predicate_family": target.get("predicate_family"),
            "predicate_label": target.get("predicate_label"),
            "rank_band": rank_band(fact.get("rank_in_context")),
            "geometry_status": fact.get("geometry_status"),
            "label_source": "codex_ver_blind_visible_metadata_bootstrap",
            "human_confirmed": False,
            "paper_locked": False,
            "target_source": "independent_codex_ver_blind_binary_target",
            "allowed_use": "train-only independent combiner smoke",
            "leakage_boundary": (
                "Targets are rank-hidden Codex bootstrap labels. Hidden provenance "
                "is joined after labeling for analysis only, not used as target input."
            ),
        }
        rows.append(row)
    if missing:
        raise ValueError(f"missing deployable feature rows for {len(missing)} targets")
    return rows


def add_combiner_views(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        copied = deepcopy(row)
        baseline_inputs = copied["baseline_inputs"]
        semantic = baseline_inputs["semantic_only"]
        geometry = baseline_inputs["geometry_only"]
        sg = baseline_inputs["semantic_plus_geometry"]
        factorized = baseline_inputs["factorized_reliability_posterior"]
        semantic_norm = smoke.safe_float(factorized.get("semantic_score_norm"), 0.0)
        p_geom = smoke.safe_float(factorized.get("p_geom_valid_imputed_neutral"), 0.5)
        residual_delta = p_geom - semantic_norm
        checkable = smoke.safe_float(factorized.get("geometry_checkable"), 0.0)
        supported = smoke.safe_float(factorized.get("predicate_family_supported"), 0.0)
        uncertain = smoke.safe_float(factorized.get("geometry_status_is_uncertain"), 0.0)
        unsupported = smoke.safe_float(factorized.get("geometry_status_is_unsupported"), 0.0)

        coverage = {key: factorized.get(key) for key in sorted(COVERAGE_KEYS) if key in factorized}
        uncertainty = {key: factorized.get(key) for key in sorted(UNCERTAINTY_KEYS) if key in factorized}
        baseline_inputs["semantic_geometry_coverage"] = {**sg, **coverage}
        baseline_inputs["semantic_geometry_uncertainty"] = {**sg, **uncertainty}
        baseline_inputs["semantic_geometry_coverage_uncertainty"] = {**sg, **coverage, **uncertainty}
        baseline_inputs["residual_reliability_model"] = {
            "semantic_score_raw": semantic.get("semantic_score_raw"),
            "semantic_score_norm": semantic_norm,
            "rank_in_context": semantic.get("rank_in_context"),
            "predicate_rank_for_pair": semantic.get("predicate_rank_for_pair"),
            "p_geom_valid_imputed_neutral": p_geom,
            "geometry_residual_proxy": geometry.get("geometry_residual_proxy"),
            "consistency_score": geometry.get("consistency_score"),
            "residual_p_geom_minus_semantic_norm": residual_delta,
            "abs_residual_p_geom_minus_semantic_norm": abs(residual_delta),
            "underconfidence_score": factorized.get("underconfidence_score"),
            "absolute_disagreement": factorized.get("absolute_disagreement"),
            "geometry_checkable": checkable,
            "predicate_family_supported": supported,
            "geometry_status_is_uncertain": uncertain,
            "geometry_status_is_unsupported": unsupported,
        }
        baseline_inputs["gated_evidence_model"] = {
            "semantic_score_raw": semantic.get("semantic_score_raw"),
            "semantic_score_norm": semantic_norm,
            "rank_in_context": semantic.get("rank_in_context"),
            "p_geom_valid_if_checkable": p_geom * checkable,
            "p_geom_valid_if_supported": p_geom * supported,
            "p_geom_valid_if_not_uncertain": p_geom * (1.0 - uncertain),
            "p_geom_valid_if_not_unsupported": p_geom * (1.0 - unsupported),
            "consistency_if_checkable": smoke.safe_float(geometry.get("consistency_score"), 0.0) * checkable,
            "residual_if_checkable": smoke.safe_float(geometry.get("geometry_residual_proxy"), 0.0) * checkable,
            "disagreement_if_checkable": abs(residual_delta) * checkable,
            "coverage_state": factorized.get("coverage_state"),
            "geometry_status": factorized.get("geometry_status"),
        }
        baseline_inputs["rank_only"] = {
            "rank_in_context": factorized.get("rank_in_context"),
            "predicate_rank_for_pair": factorized.get("predicate_rank_for_pair"),
            "semantic_score_norm": semantic_norm,
        }
        baseline_inputs["negative_rank_only"] = {
            "negative_semantic_score_norm": 1.0 - semantic_norm,
        }
        baseline_inputs["rank_band_only"] = {
            "rank_band": copied["target"].get("rank_band"),
        }
        baseline_inputs["family_only"] = {
            "predicate_family": factorized.get("predicate_family"),
        }
        baseline_inputs["predicate_only"] = {
            "predicate_label": factorized.get("predicate_label"),
        }
        baseline_inputs["p_geom_valid_only"] = {
            "p_geom_valid_imputed_neutral": p_geom,
        }
        output.append(copied)
    return output


def grouped_folds(rows: list[dict[str, Any]], fold_count: int) -> tuple[list[list[int]], list[dict[str, Any]]]:
    groups: dict[str, list[int]] = {}
    for idx, row in enumerate(rows):
        group = str(row["identity"]["scan_id"])
        groups.setdefault(group, []).append(idx)
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
        return (abs(pos - neg), len(indices), group)

    for _, indices in sorted(groups.items(), key=group_key, reverse=True):
        pos = sum(smoke.target_y(rows[idx]) for idx in indices)
        neg = len(indices) - pos
        best_fold = min(
            range(fold_count),
            key=lambda fold: (
                abs((fold_pos[fold] + pos) - target_pos)
                + abs((fold_neg[fold] + neg) - target_neg)
                + 0.05 * (fold_rows[fold] + len(indices)),
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


def metric_record(kind: str, split_eval: str, name: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": kind,
        "target_mode": TARGET_MODE,
        "split_eval": split_eval,
        "name": name,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


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


def family_slices(metric_scores: dict[str, list[float]], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    families = sorted({str(row["identity"]["predicate_family"]) for row in rows})
    for family in families:
        indices = [idx for idx, row in enumerate(rows) if str(row["identity"]["predicate_family"]) == family]
        family_rows = [rows[idx] for idx in indices]
        y_set = {smoke.target_y(row) for row in family_rows}
        for view_name, scores in metric_scores.items():
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
        for pos_idx in sorted(positives, key=lambda idx: smoke.safe_float(rows[idx]["baseline_inputs"]["factorized_reliability_posterior"].get("rank_in_context"), 0.0)):
            if not negatives:
                continue
            pos_rank = smoke.safe_float(rows[pos_idx]["baseline_inputs"]["factorized_reliability_posterior"].get("rank_in_context"), 0.0)
            available = [idx for idx in negatives if idx not in used_negatives]
            if not available:
                break
            neg_idx = min(
                available,
                key=lambda idx: (
                    abs(smoke.safe_float(rows[idx]["baseline_inputs"]["factorized_reliability_posterior"].get("rank_in_context"), 0.0) - pos_rank),
                    str(rows[idx]["identity"]["prediction_id"]),
                ),
            )
            used_negatives.add(neg_idx)
            neg_rank = smoke.safe_float(rows[neg_idx]["baseline_inputs"]["factorized_reliability_posterior"].get("rank_in_context"), 0.0)
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
        family_counts: dict[str, list[float]] = {}
        for pair in pairs:
            pos_score = scores[pair["positive_index"]]
            neg_score = scores[pair["negative_index"]]
            if pos_score > neg_score:
                win = 1.0
            elif pos_score == neg_score:
                win = 0.5
            else:
                win = 0.0
            wins += win
            family_counts.setdefault(pair["predicate_family"], []).append(win)
        outputs.append(
            {
                "view": view_name,
                "pairs": len(pairs),
                "pairwise_accuracy": wins / len(pairs) if pairs else None,
                "by_family": {
                    family: {
                        "pairs": len(values),
                        "pairwise_accuracy": sum(values) / len(values) if values else None,
                    }
                    for family, values in sorted(family_counts.items())
                },
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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Independent Combiner Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage smoke.",
        "- No validation/test rows are used.",
        "- Labels are `(codex_ver_blind)` bootstrap labels from sanitized blind sheets.",
        "- `V_mv_e` is not used as model input.",
        "- Results are not paper-level metrics.",
        "",
        "## Target Counts",
        "",
        "| Rows | Positive | Negative |",
        "| ---: | ---: | ---: |",
        f"| {summary['target_summary']['rows']} | {summary['target_summary']['positive']} | {summary['target_summary']['negative']} |",
        "",
        "## Main Views",
        "",
        "| Eval | View | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["metric_rows"]:
        if row["kind"] != "main":
            continue
        metrics = row["metrics"]
        lines.append(
            f"| `{row['split_eval']}` | `{row['name']}` | {fmt(metrics['auroc'])} | "
            f"{fmt(metrics['auprc'])} | {fmt(metrics['brier'])} | "
            f"{fmt(metrics['ece_5bin'])} | {fmt(metrics['accuracy_at_0_5'])} |"
        )
    lines.extend(
        [
            "",
            "## Factor / Proxy Controls",
            "",
            "| Eval | Kind | View | AUROC | AUPRC | Brier |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["kind"] not in {"factor_ablation", "control", "proxy", "probe"}:
            continue
        metrics = row["metrics"]
        lines.append(
            f"| `{row['split_eval']}` | `{row['kind']}` | `{row['name']}` | "
            f"{fmt(metrics['auroc'])} | {fmt(metrics['auprc'])} | {fmt(metrics['brier'])} |"
        )
    lines.extend(
        [
            "",
            "## Deltas",
            "",
            "| Eval | Left | Right | Delta AUROC | Delta AUPRC | Delta Brier |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["comparisons"]:
        delta = row["delta"]
        lines.append(
            f"| `{row['split_eval']}` | `{row['left']}` | `{row['right']}` | "
            f"{fmt(delta['auroc'])} | {fmt(delta['auprc'])} | {fmt(delta['brier'])} |"
        )
    lines.extend(
        [
            "",
            "## Pairwise Rank-Matched Diagnostic",
            "",
            "| View | Pairs | Accuracy |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in summary["pairwise_metrics"]:
        lines.append(f"| `{row['view']}` | {row['pairs']} | {fmt(row['pairwise_accuracy'])} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    features_by_id = load_features(args.features)
    targets = smoke.read_jsonl(args.targets)
    rows = add_combiner_views(build_rows(targets, features_by_id))
    target_summary = target_counts(rows)
    target_rows_path = output_dir / "independent_codex_ver_blind_rows.jsonl"
    smoke.write_jsonl(target_rows_path, rows)

    metric_rows = []
    prediction_paths: dict[str, str] = {"target_rows": smoke.rel_path(target_rows_path) or str(target_rows_path)}
    feature_summaries: dict[str, Any] = {}
    score_by_view_crossfit: dict[str, list[float]] = {}
    score_by_view_grouped: dict[str, list[float]] = {}

    view_sets = [
        ("main", MAIN_VIEWS, rows),
        ("factor_ablation", FACTOR_ABLATION_VIEWS, rows),
        ("proxy", PROXY_VIEWS, rows),
    ]
    control_rows_by_name = {}
    for view_name in CONTROL_VIEWS:
        view_rows, view_summary = redesigned.build_view_rows(rows, view_name)
        control_rows_by_name[view_name] = view_rows
        feature_summaries[f"{view_name}:view"] = view_summary
    view_sets.append(("control", CONTROL_VIEWS, None))

    for kind, view_names, base_rows in view_sets:
        for view_name in view_names:
            current_rows = control_rows_by_name[view_name] if kind == "control" else base_rows
            if current_rows is None:
                raise RuntimeError("missing view rows")
            in_probs, in_summary = smoke.train_predict_in_sample(
                current_rows,
                view_name,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            cross_probs, cross_summary = smoke.train_predict_crossfit(
                current_rows,
                view_name,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            grouped_probs, grouped_summary = train_predict_grouped(
                current_rows,
                view_name,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            feature_summaries[f"{view_name}:model"] = {
                "in_sample": in_summary,
                "crossfit": cross_summary,
                "grouped": grouped_summary,
            }
            for split_eval, probs in [
                ("in_sample", in_probs),
                ("train_internal_5fold", cross_probs),
                ("train_internal_grouped_by_scan", grouped_probs),
            ]:
                metric_rows.append(metric_record(kind, split_eval, view_name, current_rows, probs))
                pred_path = output_dir / f"predictions_{split_eval}_{view_name}.jsonl"
                smoke.write_jsonl(pred_path, smoke.build_prediction_rows(current_rows, TARGET_MODE, split_eval, view_name, probs))
                prediction_paths[f"{split_eval}:{view_name}"] = smoke.rel_path(pred_path) or str(pred_path)
            score_by_view_crossfit[view_name] = cross_probs
            score_by_view_grouped[view_name] = grouped_probs

    for probe_name in PROBE_NAMES:
        scores = redesigned.probe_scores(rows, probe_name)
        metric_rows.append(metric_record("probe", "score_probe", probe_name, rows, scores))
        score_by_view_crossfit[probe_name] = scores

    comparisons = []
    for split_eval in ["train_internal_5fold", "train_internal_grouped_by_scan"]:
        comparisons.extend(
            [
                comparison(metric_rows, split_eval, "factorized_reliability_posterior", "semantic_plus_geometry"),
                comparison(metric_rows, split_eval, "residual_reliability_model", "semantic_plus_geometry"),
                comparison(metric_rows, split_eval, "gated_evidence_model", "semantic_plus_geometry"),
                comparison(metric_rows, split_eval, "factorized_reliability_posterior", "negative_rank_only"),
                comparison(metric_rows, split_eval, "residual_reliability_model", "negative_rank_only"),
                comparison(metric_rows, split_eval, "gated_evidence_model", "negative_rank_only"),
                comparison(metric_rows, split_eval, "semantic_geometry_uncertainty", "semantic_plus_geometry"),
            ]
        )

    family_slice_rows = family_slices(score_by_view_crossfit, rows)
    family_slice_csv_rows = []
    for item in family_slice_rows:
        metrics = item["metrics"]
        family_slice_csv_rows.append(
            {
                "predicate_family": item["predicate_family"],
                "view": item["view"],
                "split_eval": item["split_eval"],
                "single_class": item["single_class"],
                **metrics,
            }
        )
    write_csv(
        output_dir / "family_slices.csv",
        family_slice_csv_rows,
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

    pairs = build_rank_matched_pairs(rows)
    smoke.write_jsonl(output_dir / "matched_pairs.jsonl", pairs)
    pairwise = pairwise_metrics(pairs, score_by_view_crossfit)
    pairwise_csv_rows = [
        {
            "view": item["view"],
            "pairs": item["pairs"],
            "pairwise_accuracy": item["pairwise_accuracy"],
        }
        for item in pairwise
    ]
    write_csv(output_dir / "pairwise.csv", pairwise_csv_rows, ["view", "pairs", "pairwise_accuracy"])

    def pick_delta(split_eval: str, left: str, right: str) -> dict[str, Any]:
        return next(
            row["delta"]
            for row in comparisons
            if row["split_eval"] == split_eval and row["left"] == left and row["right"] == right
        )

    f_sg_grouped = pick_delta("train_internal_grouped_by_scan", "factorized_reliability_posterior", "semantic_plus_geometry")
    residual_sg_grouped = pick_delta("train_internal_grouped_by_scan", "residual_reliability_model", "semantic_plus_geometry")
    gated_sg_grouped = pick_delta("train_internal_grouped_by_scan", "gated_evidence_model", "semantic_plus_geometry")
    f_rank_grouped = pick_delta("train_internal_grouped_by_scan", "factorized_reliability_posterior", "negative_rank_only")

    rank_proxy_blocks = (
        f_rank_grouped["auprc"] is not None
        and f_rank_grouped["auprc"] <= 0.0
    )
    combiner_positive = any(
        delta.get("auprc") is not None and delta["auprc"] >= 0.03
        for delta in [f_sg_grouped, residual_sg_grouped, gated_sg_grouped]
    )
    if rank_proxy_blocks:
        status = "independent_combiner_rank_proxy_blocked"
        decision = (
            "Independent codex_ver_blind targets are now usable, but the grouped "
            "combiner signal is still not safely separated from rank proxy controls. "
            "Do not claim factorized posterior advantage; inspect family slices and "
            "label policy dependence next."
        )
    elif combiner_positive:
        status = "independent_combiner_positive_bootstrap_signal"
        decision = (
            "Independent codex_ver_blind targets show a positive train-only bootstrap "
            "combiner signal under grouped folds. This supports continuing with "
            "human-confirmed labels and targeted ablations, but not paper-level claims."
        )
    else:
        status = "independent_combiner_no_strong_signal"
        decision = (
            "Independent codex_ver_blind targets are usable, but grouped combiner "
            "deltas are not strong enough to support the posterior method direction. "
            "Treat H002 as RGA benchmark/failure-analysis unless label policy or "
            "family-specific evidence improves."
        )

    summary = {
        "schema_version": "h002_independent_combiner_smoke_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "features": smoke.rel_path(args.features),
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
            "split": "train_only",
            "label_source": "codex_ver_blind_visible_metadata_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "label_evidence_as_input": False,
            "vmv_model_input_allowed": False,
            "validation_usage": False,
            "test_usage": False,
        },
        "target_summary": target_summary,
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "family_slices": family_slice_rows,
        "pairwise_metrics": pairwise,
        "feature_summaries": feature_summaries,
        "prediction_paths": prediction_paths,
        "quick_deltas": {
            "grouped_factorized_minus_sg": f_sg_grouped,
            "grouped_residual_minus_sg": residual_sg_grouped,
            "grouped_gated_minus_sg": gated_sg_grouped,
            "grouped_factorized_minus_negative_rank": f_rank_grouped,
        },
        "decision": decision,
    }
    smoke.write_json(output_dir / "summary.json", summary)
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
        for row in metric_rows:
            writer.writerow(
                {
                    "kind": row["kind"],
                    "target_mode": row["target_mode"],
                    "split_eval": row["split_eval"],
                    "name": row["name"],
                    **row["metrics"],
                }
            )
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    q = summary["quick_deltas"]
    print(
        f"status={summary['status']} rows={summary['target_summary']['rows']} "
        f"binary_pos={summary['target_summary']['positive']} binary_neg={summary['target_summary']['negative']} "
        f"metrics={len(summary['metric_rows'])} validation_used={summary['hyperparameters']['uses_validation_rows']} "
        f"grouped_factorized_d_auprc={q['grouped_factorized_minus_sg']['auprc']:.4f} "
        f"grouped_residual_d_auprc={q['grouped_residual_minus_sg']['auprc']:.4f} "
        f"grouped_gated_d_auprc={q['grouped_gated_minus_sg']['auprc']:.4f} "
        f"grouped_factorized_vs_rank_d_auprc={q['grouped_factorized_minus_negative_rank']['auprc']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
