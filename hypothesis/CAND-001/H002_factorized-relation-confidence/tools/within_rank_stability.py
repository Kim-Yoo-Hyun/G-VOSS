#!/usr/bin/env python3
"""Within-rank stability check for H002 controlled posterior labels."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import controlled_posterior_smoke as controlled
import factor_smoke as smoke
import grouped_control_smoke as grouped
import rank_proxy_debias as rank_debias


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_INPUT_DIR = RGA_ROOT / "controlled_posterior_smoke_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "within_rank_stability_codex_real_assumption"

TARGET_ROW_FILES = {
    "mined_controlled_codex_ver": "mined_controlled_codex_ver_rows.jsonl",
    "combined_controlled_codex_ver": "combined_controlled_codex_ver_rows.jsonl",
}

VIEWS = [
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
    "negative_rank_only",
    "factorized_no_rank",
    "negative_rank_plus_factorized_no_rank",
    "negative_rank_plus_disagreement",
    "geometry_continuous_only",
]

PAIRWISE_VIEWS = [
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
    "negative_rank_only",
    "factorized_no_rank",
    "negative_rank_plus_factorized_no_rank",
    "negative_rank_plus_disagreement",
    "p_geom_valid_raw",
    "semantic_score_norm_raw",
    "negative_semantic_score_norm_raw",
    "underconfidence_raw",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def metric_record(
    target_mode: str,
    rank_band: str,
    view: str,
    rows: list[dict[str, Any]],
    probs: list[float],
) -> dict[str, Any]:
    return {
        "kind": "within_rank_grouped",
        "target_mode": target_mode,
        "rank_band": rank_band,
        "split_eval": "train_internal_grouped_by_scan_within_rank_band",
        "name": view,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


def comparison(
    metric_rows: list[dict[str, Any]],
    target_mode: str,
    rank_band: str,
    left: str,
    right: str,
) -> dict[str, Any]:
    by_name = {
        row["name"]: row["metrics"]
        for row in metric_rows
        if row["target_mode"] == target_mode and row["rank_band"] == rank_band
    }
    left_metrics = by_name.get(left, {})
    right_metrics = by_name.get(right, {})
    return {
        "target_mode": target_mode,
        "rank_band": rank_band,
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


def rank_band_order(rank_band: str) -> tuple[int, str]:
    order = {
        "rank_1_50": 0,
        "rank_51_100": 1,
        "rank_101_200": 2,
        "rank_201_500": 3,
        "rank_501_1000": 4,
        "rank_gt1000": 5,
        "tail": 6,
    }
    return (order.get(rank_band, 99), rank_band)


def rows_by_rank_band(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    bands: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        band = str(row["target"].get("rank_band"))
        bands.setdefault(band, []).append(row)
    return dict(sorted(bands.items(), key=lambda item: rank_band_order(item[0])))


def class_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    pos = sum(smoke.target_y(row) for row in rows)
    return {"rows": len(rows), "positive": pos, "negative": len(rows) - pos}


def group_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[int]] = {}
    for idx, row in enumerate(rows):
        groups.setdefault(str(row["identity"]["scan_id"]), []).append(idx)
    both = 0
    pos_only = 0
    neg_only = 0
    for indices in groups.values():
        labels = {smoke.target_y(rows[idx]) for idx in indices}
        if labels == {0, 1}:
            both += 1
        elif labels == {1}:
            pos_only += 1
        else:
            neg_only += 1
    return {
        "groups": len(groups),
        "groups_with_both_classes": both,
        "positive_only_groups": pos_only,
        "negative_only_groups": neg_only,
    }


def can_evaluate(rows: list[dict[str, Any]]) -> bool:
    counts = class_counts(rows)
    groups = group_counts(rows)
    return (
        counts["positive"] >= 2
        and counts["negative"] >= 2
        and groups["groups"] >= 3
    )


def safe_train_predict_grouped(
    rows: list[dict[str, Any]],
    view: str,
    *,
    folds: int,
    epochs: int,
    learning_rate: float,
    l2: float,
) -> tuple[list[float], dict[str, Any]]:
    max_folds = min(folds, len({str(row["identity"]["scan_id"]) for row in rows}))
    errors = []
    for fold_count in range(max_folds, 1, -1):
        try:
            probs, summary = grouped.train_predict_grouped(
                rows,
                view,
                folds=fold_count,
                epochs=epochs,
                learning_rate=learning_rate,
                l2=l2,
            )
            summary["requested_folds"] = folds
            return probs, summary
        except ValueError as exc:
            errors.append({"folds": fold_count, "error": str(exc)})
    raise ValueError(f"unable to build grouped folds for {view}: {errors}")


def raw_pair_score(row: dict[str, Any], view: str) -> float:
    features = row["baseline_inputs"]["factorized_reliability_posterior"]
    semantic_norm = smoke.safe_float(features.get("semantic_score_norm"), 0.0)
    if view == "p_geom_valid_raw":
        return smoke.safe_float(features.get("p_geom_valid_imputed_neutral"), 0.5)
    if view == "semantic_score_norm_raw":
        return semantic_norm
    if view == "negative_semantic_score_norm_raw":
        return 1.0 - semantic_norm
    if view == "underconfidence_raw":
        return smoke.safe_float(features.get("underconfidence_score"), 0.0)
    raise KeyError(view)


def matched_pairs(
    rows: list[dict[str, Any]],
    target_mode: str,
    rank_band: str,
    model_probs_by_view: dict[str, dict[str, float]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    positives = [row for row in rows if smoke.target_y(row) == 1]
    negatives = [row for row in rows if smoke.target_y(row) == 0]
    unused_negatives = set(range(len(negatives)))
    records = []
    for positive in sorted(
        positives,
        key=lambda row: smoke.safe_float(
            row["baseline_inputs"]["factorized_reliability_posterior"].get("rank_in_context"),
            0.0,
        ),
    ):
        positive_rank = smoke.safe_float(
            positive["baseline_inputs"]["factorized_reliability_posterior"].get("rank_in_context"),
            0.0,
        )
        if not unused_negatives:
            break
        best_idx = min(
            unused_negatives,
            key=lambda idx: (
                abs(
                    smoke.safe_float(
                        negatives[idx]["baseline_inputs"]["factorized_reliability_posterior"].get("rank_in_context"),
                        0.0,
                    )
                    - positive_rank
                ),
                str(negatives[idx]["identity"]["prediction_id"]),
            ),
        )
        unused_negatives.remove(best_idx)
        negative = negatives[best_idx]
        negative_rank = smoke.safe_float(
            negative["baseline_inputs"]["factorized_reliability_posterior"].get("rank_in_context"),
            0.0,
        )
        record = {
            "target_mode": target_mode,
            "rank_band": rank_band,
            "positive_prediction_id": str(positive["identity"]["prediction_id"]),
            "negative_prediction_id": str(negative["identity"]["prediction_id"]),
            "positive_scan_id": str(positive["identity"]["scan_id"]),
            "negative_scan_id": str(negative["identity"]["scan_id"]),
            "positive_relation": {
                "subject": positive["identity"].get("subject_label"),
                "predicate": positive["target"].get("predicate_label"),
                "object": positive["identity"].get("object_label"),
            },
            "negative_relation": {
                "subject": negative["identity"].get("subject_label"),
                "predicate": negative["target"].get("predicate_label"),
                "object": negative["identity"].get("object_label"),
            },
            "positive_rank_in_context": positive_rank,
            "negative_rank_in_context": negative_rank,
            "rank_gap_abs": abs(positive_rank - negative_rank),
            "view_scores": {},
        }
        for view in PAIRWISE_VIEWS:
            if view.endswith("_raw"):
                positive_score = raw_pair_score(positive, view)
                negative_score = raw_pair_score(negative, view)
            else:
                positive_score = model_probs_by_view[view][str(positive["identity"]["prediction_id"])]
                negative_score = model_probs_by_view[view][str(negative["identity"]["prediction_id"])]
            if positive_score > negative_score:
                win = 1.0
            elif positive_score == negative_score:
                win = 0.5
            else:
                win = 0.0
            record["view_scores"][view] = {
                "positive_score": positive_score,
                "negative_score": negative_score,
                "positive_beats_negative": win,
            }
        records.append(record)

    pair_count = len(records)
    gaps = [row["rank_gap_abs"] for row in records]
    accuracy_by_view = {}
    for view in PAIRWISE_VIEWS:
        wins = [row["view_scores"][view]["positive_beats_negative"] for row in records]
        accuracy_by_view[view] = sum(wins) / len(wins) if wins else None
    summary = {
        "target_mode": target_mode,
        "rank_band": rank_band,
        "pair_count": pair_count,
        "mean_rank_gap_abs": sum(gaps) / len(gaps) if gaps else None,
        "max_rank_gap_abs": max(gaps) if gaps else None,
        "pairwise_accuracy": accuracy_by_view,
    }
    return records, summary


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Within-Rank Stability",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage check.",
        "- `(codex_ver)` is treated as real label by user-directed assumption.",
        "- Folds are grouped by `scan_id` inside each rank band.",
        "- Positive/negative pairs are greedily matched by `rank_in_context` inside each rank band.",
        "- No validation/test rows are used.",
        "- `V_mv_e` is not used as model input.",
        "",
        "## Rank Band Coverage",
        "",
        "| Target | Rank band | Rows | Positive | Negative | Groups | Both-class groups | Evaluated |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary["rank_band_summaries"]:
        counts = row["counts"]
        groups = row["groups"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['rank_band']}` | {counts['rows']} | "
            f"{counts['positive']} | {counts['negative']} | {groups['groups']} | "
            f"{groups['groups_with_both_classes']} | `{row['evaluated']}` |"
        )

    lines.extend(
        [
            "",
            "## Grouped Metrics",
            "",
            "| Target | Rank band | View | AUROC | AUPRC | Brier | ECE-5 |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        metrics = row["metrics"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['rank_band']}` | `{row['name']}` | "
            f"{fmt(metrics['auroc'])} | {fmt(metrics['auprc'])} | "
            f"{fmt(metrics['brier'])} | {fmt(metrics['ece_5bin'])} |"
        )

    lines.extend(
        [
            "",
            "## Key Deltas",
            "",
            "| Target | Rank band | Left | Right | Delta AUROC | Delta AUPRC | Delta Brier |",
            "| --- | --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["comparisons"]:
        delta = row["delta"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['rank_band']}` | `{row['left']}` | `{row['right']}` | "
            f"{fmt(delta['auroc'])} | {fmt(delta['auprc'])} | {fmt(delta['brier'])} |"
        )

    lines.extend(
        [
            "",
            "## Rank-Matched Pairwise Accuracy",
            "",
            "| Target | Rank band | Pairs | Mean rank gap | Factorized | Negative rank | Factorized no-rank | P-geom raw | Underconfidence raw |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["pairwise_summaries"]:
        acc = row["pairwise_accuracy"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['rank_band']}` | {row['pair_count']} | "
            f"{fmt(row['mean_rank_gap_abs'])} | "
            f"{fmt(acc.get('factorized_reliability_posterior'))} | "
            f"{fmt(acc.get('negative_rank_only'))} | "
            f"{fmt(acc.get('factorized_no_rank'))} | "
            f"{fmt(acc.get('p_geom_valid_raw'))} | "
            f"{fmt(acc.get('underconfidence_raw'))} |"
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
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any], pair_records: list[dict[str, Any]]) -> None:
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_jsonl(output_dir / "matched_pairs.jsonl", pair_records)
    with (output_dir / "metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "kind",
                "target_mode",
                "rank_band",
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
                    "rank_band": row["rank_band"],
                    "split_eval": row["split_eval"],
                    "name": row["name"],
                    **row["metrics"],
                }
            )
    with (output_dir / "pairwise.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "target_mode",
                "rank_band",
                "pair_count",
                "mean_rank_gap_abs",
                "max_rank_gap_abs",
                *[f"{view}_accuracy" for view in PAIRWISE_VIEWS],
            ],
        )
        writer.writeheader()
        for row in summary["pairwise_summaries"]:
            writer.writerow(
                {
                    "target_mode": row["target_mode"],
                    "rank_band": row["rank_band"],
                    "pair_count": row["pair_count"],
                    "mean_rank_gap_abs": row["mean_rank_gap_abs"],
                    "max_rank_gap_abs": row["max_rank_gap_abs"],
                    **{
                        f"{view}_accuracy": row["pairwise_accuracy"].get(view)
                        for view in PAIRWISE_VIEWS
                    },
                }
            )
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_dir = smoke.as_abs(args.input_dir)
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    metric_rows: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    feature_summaries: dict[str, Any] = {}
    target_summaries: dict[str, Any] = {}
    rank_band_summaries: list[dict[str, Any]] = []
    pairwise_summaries: list[dict[str, Any]] = []
    pair_records: list[dict[str, Any]] = []

    for target_mode, filename in TARGET_ROW_FILES.items():
        rows = rank_debias.add_rank_debias_views(smoke.read_jsonl(input_dir / filename))
        target_summaries[target_mode] = controlled.target_counts(rows)
        for rank_band, band_rows in rows_by_rank_band(rows).items():
            counts = class_counts(band_rows)
            groups = group_counts(band_rows)
            evaluated = can_evaluate(band_rows)
            rank_band_summaries.append(
                {
                    "target_mode": target_mode,
                    "rank_band": rank_band,
                    "counts": counts,
                    "groups": groups,
                    "evaluated": evaluated,
                }
            )
            if not evaluated:
                continue

            model_probs_by_view: dict[str, dict[str, float]] = {}
            for view in VIEWS:
                probs, feature_summary = safe_train_predict_grouped(
                    band_rows,
                    view,
                    folds=args.folds,
                    epochs=args.epochs,
                    learning_rate=args.learning_rate,
                    l2=args.l2,
                )
                feature_summaries[f"{target_mode}:{rank_band}:{view}"] = feature_summary
                metric_rows.append(metric_record(target_mode, rank_band, view, band_rows, probs))
                model_probs_by_view[view] = {
                    str(row["identity"]["prediction_id"]): prob
                    for row, prob in zip(band_rows, probs)
                }
                pred_path = output_dir / f"predictions_{target_mode}_{rank_band}_{view}.jsonl"
                smoke.write_jsonl(
                    pred_path,
                    smoke.build_prediction_rows(
                        band_rows,
                        target_mode,
                        "train_internal_grouped_by_scan_within_rank_band",
                        view,
                        probs,
                    ),
                )

            comparisons.extend(
                [
                    comparison(
                        metric_rows,
                        target_mode,
                        rank_band,
                        "factorized_reliability_posterior",
                        "semantic_plus_geometry",
                    ),
                    comparison(
                        metric_rows,
                        target_mode,
                        rank_band,
                        "factorized_reliability_posterior",
                        "negative_rank_only",
                    ),
                    comparison(
                        metric_rows,
                        target_mode,
                        rank_band,
                        "negative_rank_plus_factorized_no_rank",
                        "negative_rank_only",
                    ),
                    comparison(
                        metric_rows,
                        target_mode,
                        rank_band,
                        "negative_rank_plus_disagreement",
                        "negative_rank_only",
                    ),
                    comparison(
                        metric_rows,
                        target_mode,
                        rank_band,
                        "factorized_no_rank",
                        "geometry_continuous_only",
                    ),
                ]
            )

            pairs, pair_summary = matched_pairs(band_rows, target_mode, rank_band, model_probs_by_view)
            pair_records.extend(pairs)
            pairwise_summaries.append(pair_summary)

    primary_rank_bands = {
        "rank_201_500",
        "rank_501_1000",
        "rank_gt1000",
    }
    factorized_beats_rank = [
        row for row in comparisons
        if row["left"] == "factorized_reliability_posterior"
        and row["right"] == "negative_rank_only"
        and row["rank_band"] in primary_rank_bands
        and row["delta"]["auprc"] is not None
        and row["delta"]["auprc"] >= 0.03
        and (row["delta"]["brier"] is None or row["delta"]["brier"] <= 0.0)
    ]
    rank_plus_nonrank_beats_rank = [
        row for row in comparisons
        if row["left"] == "negative_rank_plus_factorized_no_rank"
        and row["right"] == "negative_rank_only"
        and row["rank_band"] in primary_rank_bands
        and row["delta"]["auprc"] is not None
        and row["delta"]["auprc"] >= 0.03
        and (row["delta"]["brier"] is None or row["delta"]["brier"] <= 0.0)
    ]
    pairwise_factorized_wins = [
        row for row in pairwise_summaries
        if row["rank_band"] in primary_rank_bands
        and row["mean_rank_gap_abs"] is not None
        and row["mean_rank_gap_abs"] <= 100.0
        if row["pairwise_accuracy"].get("factorized_reliability_posterior") is not None
        and row["pairwise_accuracy"].get("negative_rank_only") is not None
        and row["pairwise_accuracy"]["factorized_reliability_posterior"]
        > row["pairwise_accuracy"]["negative_rank_only"]
    ]

    primary_grouped_support = bool(factorized_beats_rank and rank_plus_nonrank_beats_rank)
    primary_pairwise_support = bool(pairwise_factorized_wins)

    if primary_grouped_support and primary_pairwise_support:
        status = "within_rank_factorized_support"
        decision = (
            "Within-rank stability provides positive support: factorized evidence and "
            "non-rank factors retain signal beyond the negative-rank proxy inside "
            "primary fixed rank bands and on rank-matched pairs."
        )
    elif primary_grouped_support or primary_pairwise_support:
        status = "within_rank_mixed"
        decision = (
            "Within-rank stability is mixed. Some rank-band or pairwise checks favor "
            "factorized evidence, but grouped primary-band metrics do not consistently "
            "beat the negative-rank proxy. This is not enough to claim that the "
            "current target is rank-independent."
        )
    else:
        status = "within_rank_not_stable"
        decision = (
            "Within-rank stability does not support a factorized posterior claim yet. "
            "The current controlled-label signal remains largely explainable by "
            "rank-derived underconfidence, and non-rank evidence is not stable inside "
            "fixed rank bands."
        )

    summary = {
        "schema_version": "h002_within_rank_stability_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "input_dir": smoke.rel_path(input_dir),
            **{target_mode: smoke.rel_path(input_dir / filename) for target_mode, filename in TARGET_ROW_FILES.items()},
        },
        "output_dir": smoke.rel_path(output_dir),
        "hyperparameters": {
            "folds": args.folds,
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "l2": args.l2,
            "uses_validation_rows": False,
            "tuned_on_validation": False,
        },
        "boundary": {
            "split": "train_only",
            "codex_ver_treated_as_real_label_by_user_assumption": True,
            "group_key": "scan_id",
            "within_rank_band": True,
            "pair_matching_key": "rank_in_context",
            "validation_usage": False,
            "test_usage": False,
            "vmv_model_input_allowed": False,
        },
        "target_summaries": target_summaries,
        "rank_band_summaries": rank_band_summaries,
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "pairwise_summaries": pairwise_summaries,
        "feature_summaries": feature_summaries,
        "decision": decision,
    }
    write_outputs(output_dir, summary, pair_records)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    bands = sum(1 for row in summary["rank_band_summaries"] if row["evaluated"])
    pair_count = sum(row["pair_count"] for row in summary["pairwise_summaries"])
    print(
        f"status={summary['status']} bands={bands} metrics={len(summary['metric_rows'])} "
        f"pairs={pair_count} validation_used={summary['hyperparameters']['uses_validation_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
