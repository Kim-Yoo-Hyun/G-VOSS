#!/usr/bin/env python3
"""Controlled posterior smoke for revised all-label-ready H002 strict slice."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INPUT_ROWS = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/posterior_ready_rows.jsonl"
)
DEFAULT_FEATURE_JOIN_SUMMARY = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/summary.json"
)
DEFAULT_INPUT_CONTRACT = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_source_feature_join_all_label_ready/input_contract.json"
)
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready"

TARGET_MODE = "rank_band_balanced_revised_sampling"

MAIN_VIEWS = [
    "semantic_only",
    "geometry_only",
    "semantic_plus_geometry",
    "semantic_geometry_coverage",
    "factorized_reliability_posterior",
]

DIAGNOSTIC_VIEWS = [
    "coverage_only",
    "semantic_score_only",
    "rank_only",
    "p_geom_valid_only",
    "residual_reliability_model",
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
    "coverage_evidence_ready",
]

COMPARISON_PAIRS = [
    ("factorized_reliability_posterior", "semantic_plus_geometry"),
    ("factorized_reliability_posterior", "semantic_geometry_coverage"),
    ("factorized_reliability_posterior", "semantic_only"),
    ("factorized_reliability_posterior", "geometry_only"),
    ("semantic_plus_geometry", "semantic_only"),
    ("semantic_plus_geometry", "geometry_only"),
    ("semantic_geometry_coverage", "semantic_plus_geometry"),
    ("residual_reliability_model", "semantic_plus_geometry"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-rows", type=Path, default=DEFAULT_INPUT_ROWS)
    parser.add_argument("--feature-join-summary", type=Path, default=DEFAULT_FEATURE_JOIN_SUMMARY)
    parser.add_argument("--input-contract", type=Path, default=DEFAULT_INPUT_CONTRACT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=3)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return smoke.read_jsonl(path)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def target_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(smoke.target_y(row) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "by_family": dict(sorted(Counter(str(row["identity"]["predicate_family"]) for row in rows).items())),
        "by_predicate": dict(sorted(Counter(str(row["identity"]["predicate_label"]) for row in rows).items())),
        "by_scan_rows": dict(sorted(Counter(str(row["identity"]["scan_id"]) for row in rows).items())),
    }


def grouped_folds(rows: list[dict[str, Any]], fold_count: int) -> tuple[list[list[int]], list[dict[str, Any]]]:
    groups: dict[str, list[int]] = {}
    for idx, row in enumerate(rows):
        groups.setdefault(str(row["identity"]["scan_id"]), []).append(idx)
    fold_count = max(2, min(fold_count, len(groups)))
    folds: list[list[int]] = [[] for _ in range(fold_count)]
    fold_pos = [0] * fold_count
    fold_neg = [0] * fold_count
    fold_rows = [0] * fold_count

    def order_key(item: tuple[str, list[int]]) -> tuple[int, int, str]:
        group, indices = item
        pos = sum(smoke.target_y(rows[idx]) for idx in indices)
        neg = len(indices) - pos
        return (len(indices), abs(pos - neg), group)

    total_pos = sum(smoke.target_y(row) for row in rows)
    total_neg = len(rows) - total_pos
    target_pos = total_pos / fold_count
    target_neg = total_neg / fold_count
    target_rows = len(rows) / fold_count

    for order, (_, indices) in enumerate(sorted(groups.items(), key=order_key, reverse=True)):
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
            score = smoke.safe_float(features.get("semantic_score_norm"))
        elif probe_name == "negative_semantic_score_norm":
            score = smoke.safe_float(features.get("negative_semantic_score_norm"))
        elif probe_name == "semantic_rank_inverse":
            score = smoke.safe_float(features.get("semantic_rank_inverse"))
        elif probe_name == "p_geom_valid":
            score = smoke.safe_float(features.get("p_geom_valid"))
        elif probe_name == "negative_p_geom_valid":
            score = smoke.safe_float(features.get("p_geom_invalid"))
        elif probe_name == "consistency_score":
            score = smoke.safe_float(features.get("consistency_score"))
        elif probe_name == "absolute_disagreement":
            score = smoke.safe_float(features.get("absolute_disagreement"))
        elif probe_name == "underconfidence_score":
            score = smoke.safe_float(features.get("underconfidence_score"))
        elif probe_name == "overconfidence_score":
            score = smoke.safe_float(features.get("overconfidence_score"))
        elif probe_name == "coverage_evidence_ready":
            score = smoke.safe_float(features.get("coverage_evidence_ready"))
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
                    "split_eval": "train_internal_grouped_by_scan",
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
        for pos_idx in sorted(positives, key=lambda idx: smoke.safe_float(rows[idx]["baseline_inputs"]["semantic_only"].get("semantic_rank"))):
            available = [idx for idx in negatives if idx not in used_negatives]
            if not available:
                break
            pos_rank = smoke.safe_float(rows[pos_idx]["baseline_inputs"]["semantic_only"].get("semantic_rank"))
            neg_idx = min(
                available,
                key=lambda idx: (
                    abs(smoke.safe_float(rows[idx]["baseline_inputs"]["semantic_only"].get("semantic_rank")) - pos_rank),
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
                        smoke.safe_float(rows[pos_idx]["baseline_inputs"]["semantic_only"].get("semantic_rank"))
                        - smoke.safe_float(rows[neg_idx]["baseline_inputs"]["semantic_only"].get("semantic_rank"))
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


def validate_inputs(rows: list[dict[str, Any]], feature_join_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if feature_join_summary.get("boundary", {}).get("validation_usage") is not False:
        errors.append({"error_type": "feature_join_summary_uses_validation"})
    if feature_join_summary.get("boundary", {}).get("test_usage") is not False:
        errors.append({"error_type": "feature_join_summary_uses_test"})
    for row_number, row in enumerate(rows, start=1):
        if row.get("record_type") != "h002_support_vertical_v2_revised_sampling_posterior_ready_row":
            errors.append({"error_type": "unexpected_record_type", "row_number": row_number, "record_type": row.get("record_type")})
        if row.get("provenance", {}).get("hidden_metadata_as_model_input") is not False:
            errors.append({"error_type": "hidden_metadata_input_not_false", "row_number": row_number})
        if row.get("provenance", {}).get("review_fields_as_model_input") is not False:
            errors.append({"error_type": "review_fields_input_not_false", "row_number": row_number})
        for field in ["audit_only_user_confirmed_review_fields", "hidden_audit_metadata_post_label_only", "audit_packet_paths_not_model_input"]:
            if field in row:
                errors.append({"error_type": "forbidden_field_present", "row_number": row_number, "field": field})
    return errors


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Revised Sampling Controlled Posterior Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage posterior smoke.",
        "- No validation/test rows are used.",
        "- Active target slice is `rank_band_balanced_revised_sampling`.",
        "- Review fields, hidden audit metadata, target labels, packet paths, and multi-view evidence are not model inputs.",
        "- Results are not paper-level metrics.",
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
        metrics = row["metrics"]
        lines.append(
            f"| `{row['name']}` | {fmt(metrics['auroc'])} | {fmt(metrics['auprc'])} | "
            f"{fmt(metrics['brier'])} | {fmt(metrics['ece_5bin'])} | {fmt(metrics['accuracy_at_0_5'])} |"
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
        delta = row["delta"]
        lines.append(
            f"| `{row['split_eval']}` | `{row['left']}` | `{row['right']}` | "
            f"{fmt(delta['auroc'])} | {fmt(delta['auprc'])} | {fmt(delta['brier'])} |"
        )
    lines.extend(["", "## Decision", "", summary["decision"], "", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any], rows: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> None:
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "posterior_rows.jsonl", rows)
    write_jsonl(output_dir / "predictions.jsonl", predictions)
    write_jsonl(output_dir / "matched_pairs.jsonl", summary["matched_pairs"])
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
    write_csv(output_dir / "pairwise.csv", summary["pairwise_metrics"], ["view", "pairs", "pairwise_accuracy"])
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
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    rows = read_jsonl(args.input_rows)
    feature_join_summary = read_json(args.feature_join_summary)
    input_contract = read_json(args.input_contract)
    validation_errors = validate_inputs(rows, feature_join_summary)

    metric_rows: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    feature_summaries: dict[str, Any] = {}
    score_by_view_grouped: dict[str, list[float]] = {}
    score_by_view_crossfit: dict[str, list[float]] = {}

    for kind, views in [("main", MAIN_VIEWS), ("diagnostic", DIAGNOSTIC_VIEWS)]:
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
                        "target_y": smoke.target_y(row),
                        "probability": prob,
                    }
                )

    for probe_name in PROBE_NAMES:
        scores = probe_scores(rows, probe_name)
        metric_rows.append(metric_record("probe", "score_probe", probe_name, rows, scores))
        score_by_view_crossfit[probe_name] = scores

    comparisons = []
    for split_eval in ["train_internal_3fold", "train_internal_grouped_by_scan"]:
        for left, right in COMPARISON_PAIRS:
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
    grouped_factorized_minus_sgc = pick_delta(
        "train_internal_grouped_by_scan",
        "factorized_reliability_posterior",
        "semantic_geometry_coverage",
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

    if validation_errors:
        status = "full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_input_errors"
        decision = "Fix posterior smoke input contract errors before interpreting metrics."
        next_todo = "fix_revised_sampling_all_label_ready_controlled_posterior_smoke_inputs"
    elif positive_signal:
        status = "full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_positive_smoke"
        decision = (
            "On the train-only strict relation slice, the factorized view shows a positive diagnostic signal "
            "over simpler semantic/geometry baselines. Treat this as hypothesis-stage evidence only."
        )
        next_todo = "revised_sampling_all_label_ready_controlled_error_analysis"
    else:
        status = "full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_no_strong_signal"
        decision = (
            "The strict slice is executable, but the factorized view does not show a strong grouped-fold "
            "advantage over simpler baselines. Inspect errors and feature definitions before expanding claims."
        )
        next_todo = "revised_sampling_all_label_ready_controlled_error_analysis"

    summary = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_controlled_posterior_smoke_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "input_rows": rel_path(args.input_rows),
            "feature_join_summary": rel_path(args.feature_join_summary),
            "input_contract": rel_path(args.input_contract),
        },
        "output_dir": rel_path(output_dir),
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
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "review_fields_as_model_input": False,
            "hidden_metadata_as_model_input": False,
            "target_labels_as_model_input": False,
            "packet_paths_as_model_input": False,
            "multi_view_as_model_input": False,
            "predicate_label_as_model_input": False,
            "predicate_family_as_model_input": False,
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
        "input_contract": input_contract,
        "validation_errors": validation_errors,
        "quick_deltas": {
            "grouped_factorized_minus_semantic_plus_geometry": grouped_factorized_minus_sg,
            "grouped_factorized_minus_semantic_geometry_coverage": grouped_factorized_minus_sgc,
            "grouped_factorized_minus_semantic_only": grouped_factorized_minus_semantic,
            "grouped_factorized_minus_geometry_only": grouped_factorized_minus_geometry,
        },
        "decision": decision,
        "next_todo": next_todo,
    }
    write_outputs(output_dir, summary, rows, predictions)
    return summary


def main() -> int:
    summary = run(parse_args())
    deltas = summary["quick_deltas"]
    print(
        "status={status} rows={rows} pos={pos} neg={neg} metrics={metrics} "
        "validation_used={validation_used} d_auprc_factorized_vs_sg={d_sg:.4f} "
        "d_auprc_factorized_vs_sgc={d_sgc:.4f} d_auprc_factorized_vs_semantic={d_sem:.4f} "
        "d_auprc_factorized_vs_geometry={d_geom:.4f} next={next_todo}".format(
            status=summary["status"],
            rows=summary["target_summary"]["rows"],
            pos=summary["target_summary"]["positive"],
            neg=summary["target_summary"]["negative"],
            metrics=len(summary["metric_rows"]),
            validation_used=summary["hyperparameters"]["uses_validation_rows"],
            d_sg=deltas["grouped_factorized_minus_semantic_plus_geometry"]["auprc"],
            d_sgc=deltas["grouped_factorized_minus_semantic_geometry_coverage"]["auprc"],
            d_sem=deltas["grouped_factorized_minus_semantic_only"]["auprc"],
            d_geom=deltas["grouped_factorized_minus_geometry_only"]["auprc"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
