#!/usr/bin/env python3
"""Build and smoke-test stricter rank-matched H002 targets."""

from __future__ import annotations

import argparse
import csv
from copy import deepcopy
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
DEFAULT_OUTPUT_DIR = RGA_ROOT / "rank_matched_target_codex_real_assumption"

TARGET_ROW_FILES = {
    "mined_controlled_codex_ver": "mined_controlled_codex_ver_rows.jsonl",
    "combined_controlled_codex_ver": "combined_controlled_codex_ver_rows.jsonl",
}

VIEWS = [
    "semantic_only",
    "geometry_only",
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
    "negative_rank_only",
    "semantic_plus_geometry_no_rank",
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
    "negative_semantic_score_norm_raw",
    "underconfidence_raw",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--max-rank-gap", type=float, default=50.0)
    parser.add_argument("--tail-max-rank-gap", type=float, default=500.0)
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


def rank_value(row: dict[str, Any]) -> float:
    return smoke.safe_float(
        row["baseline_inputs"]["factorized_reliability_posterior"].get("rank_in_context"),
        0.0,
    )


def semantic_norm(row: dict[str, Any]) -> float:
    return smoke.safe_float(
        row["baseline_inputs"]["factorized_reliability_posterior"].get("semantic_score_norm"),
        0.0,
    )


def match_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    features = row["baseline_inputs"]["factorized_reliability_posterior"]
    return (
        str(row["target"].get("rank_band")),
        str(row["target"].get("predicate_family")),
        str(row["target"].get("predicate_label")),
        str(row["target"].get("geometry_status")),
        str(features.get("coverage_state")),
    )


def raw_pair_score(row: dict[str, Any], view: str) -> float:
    features = row["baseline_inputs"]["factorized_reliability_posterior"]
    if view == "p_geom_valid_raw":
        return smoke.safe_float(features.get("p_geom_valid_imputed_neutral"), 0.5)
    if view == "negative_semantic_score_norm_raw":
        return 1.0 - semantic_norm(row)
    if view == "underconfidence_raw":
        return smoke.safe_float(features.get("underconfidence_score"), 0.0)
    raise KeyError(view)


def grouped_rows(rows: list[dict[str, Any]]) -> dict[tuple[str, str, str, str, str], list[dict[str, Any]]]:
    output: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        output.setdefault(match_key(row), []).append(row)
    return dict(sorted(output.items(), key=lambda item: item[0]))


def pair_scope(rank_band: str, gap: float, *, max_rank_gap: float, tail_max_rank_gap: float) -> str:
    if rank_band == "tail":
        if gap <= tail_max_rank_gap:
            return "tail_exploratory"
        return "rejected_tail_gap"
    if gap <= max_rank_gap:
        return "primary"
    return "rejected_primary_gap"


def gap_label(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value).replace(".", "p")


def update_target_for_pair(
    row: dict[str, Any],
    *,
    new_target_mode: str,
    source_target_mode: str,
    pair_id: str,
    pair_role: str,
    pair_scope_name: str,
    rank_gap_abs: float,
    positive_prediction_id: str,
    negative_prediction_id: str,
    max_rank_gap: float,
    tail_max_rank_gap: float,
) -> dict[str, Any]:
    copied = deepcopy(row)
    target = dict(copied["target"])
    target.update(
        {
            "target_mode": new_target_mode,
            "target_source": "rank_matched_codex_ver_target",
            "source_target_mode": source_target_mode,
            "allowed_use": "train-only rank-matched posterior smoke",
            "rank_matched_pair_id": pair_id,
            "rank_matched_pair_role": pair_role,
            "rank_matched_pair_scope": pair_scope_name,
            "rank_gap_abs": rank_gap_abs,
            "positive_prediction_id": positive_prediction_id,
            "negative_prediction_id": negative_prediction_id,
            "rank_match_policy": {
                "primary_max_rank_gap_abs": max_rank_gap,
                "tail_max_rank_gap_abs": tail_max_rank_gap,
                "match_key": [
                    "rank_band",
                    "predicate_family",
                    "predicate_label",
                    "geometry_status",
                    "coverage_state",
                ],
                "tail_rows_are_exploratory": True,
            },
            "leakage_boundary": (
                "Rank-matched target rows are selected from codex_ver labels under "
                "train-only hypothesis-stage assumptions. Pair id and pair role are "
                "target metadata, not deployable model input."
            ),
        }
    )
    copied["target"] = target
    return copied


def build_rank_matched_targets(
    rows: list[dict[str, Any]],
    source_target_mode: str,
    *,
    max_rank_gap: float,
    tail_max_rank_gap: float,
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    primary_gap = gap_label(max_rank_gap)
    tail_gap = gap_label(tail_max_rank_gap)
    primary_mode = source_target_mode.replace("_controlled_", f"_rank_matched_gap{primary_gap}_")
    tail_mode = source_target_mode.replace("_controlled_", f"_tail_exploratory_gap{tail_gap}_")
    paired_rows: dict[str, list[dict[str, Any]]] = {
        primary_mode: [],
    }
    paired_rows[tail_mode] = []
    pair_records: list[dict[str, Any]] = []

    for key, key_rows in grouped_rows(rows).items():
        rank_band, family, label, geometry_status, coverage_state = key
        positives = sorted([row for row in key_rows if smoke.target_y(row) == 1], key=rank_value)
        negatives = [row for row in key_rows if smoke.target_y(row) == 0]
        unused_negatives = set(range(len(negatives)))
        for positive in positives:
            if not unused_negatives:
                break
            positive_rank = rank_value(positive)
            negative_idx = min(
                unused_negatives,
                key=lambda idx: (
                    abs(rank_value(negatives[idx]) - positive_rank),
                    str(negatives[idx]["identity"]["prediction_id"]),
                ),
            )
            negative = negatives[negative_idx]
            negative_rank = rank_value(negative)
            gap = abs(negative_rank - positive_rank)
            scope = pair_scope(
                rank_band,
                gap,
                max_rank_gap=max_rank_gap,
                tail_max_rank_gap=tail_max_rank_gap,
            )
            included = scope in {"primary", "tail_exploratory"}
            if not included:
                pair_records.append(
                    {
                        "source_target_mode": source_target_mode,
                        "pair_scope": scope,
                        "included_in_output": False,
                        "included_in_smoke": False,
                        "rank_band": rank_band,
                        "predicate_family": family,
                        "predicate_label": label,
                        "geometry_status": geometry_status,
                        "coverage_state": coverage_state,
                        "positive_prediction_id": str(positive["identity"]["prediction_id"]),
                        "negative_prediction_id": str(negative["identity"]["prediction_id"]),
                        "positive_rank_in_context": positive_rank,
                        "negative_rank_in_context": negative_rank,
                        "rank_gap_abs": gap,
                    }
                )
                continue

            unused_negatives.remove(negative_idx)
            target_mode = tail_mode if scope == "tail_exploratory" else primary_mode
            pair_index = sum(1 for item in pair_records if item["source_target_mode"] == source_target_mode and item["pair_scope"] == scope) + 1
            pair_id = f"{target_mode}:{rank_band}:{pair_index:04d}"
            positive_id = str(positive["identity"]["prediction_id"])
            negative_id = str(negative["identity"]["prediction_id"])
            pair_records.append(
                {
                    "source_target_mode": source_target_mode,
                    "target_mode": target_mode,
                    "rank_matched_pair_id": pair_id,
                    "pair_scope": scope,
                    "included_in_output": True,
                    "included_in_smoke": scope == "primary",
                    "rank_band": rank_band,
                    "predicate_family": family,
                    "predicate_label": label,
                    "geometry_status": geometry_status,
                    "coverage_state": coverage_state,
                    "positive_prediction_id": positive_id,
                    "negative_prediction_id": negative_id,
                    "positive_rank_in_context": positive_rank,
                    "negative_rank_in_context": negative_rank,
                    "rank_gap_abs": gap,
                    "positive_semantic_score_norm": semantic_norm(positive),
                    "negative_semantic_score_norm": semantic_norm(negative),
                    "positive_scan_id": str(positive["identity"]["scan_id"]),
                    "negative_scan_id": str(negative["identity"]["scan_id"]),
                }
            )
            paired_rows[target_mode].append(
                update_target_for_pair(
                    positive,
                    new_target_mode=target_mode,
                    source_target_mode=source_target_mode,
                    pair_id=pair_id,
                    pair_role="positive",
                    pair_scope_name=scope,
                    rank_gap_abs=gap,
                    positive_prediction_id=positive_id,
                    negative_prediction_id=negative_id,
                    max_rank_gap=max_rank_gap,
                    tail_max_rank_gap=tail_max_rank_gap,
                )
            )
            paired_rows[target_mode].append(
                update_target_for_pair(
                    negative,
                    new_target_mode=target_mode,
                    source_target_mode=source_target_mode,
                    pair_id=pair_id,
                    pair_role="negative",
                    pair_scope_name=scope,
                    rank_gap_abs=gap,
                    positive_prediction_id=positive_id,
                    negative_prediction_id=negative_id,
                    max_rank_gap=max_rank_gap,
                    tail_max_rank_gap=tail_max_rank_gap,
                )
            )
    return paired_rows, pair_records


def class_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    pos = sum(smoke.target_y(row) for row in rows)
    return {"rows": len(rows), "positive": pos, "negative": len(rows) - pos}


def can_group_eval(rows: list[dict[str, Any]]) -> bool:
    counts = class_counts(rows)
    groups = {str(row["identity"]["scan_id"]) for row in rows}
    return counts["positive"] >= 2 and counts["negative"] >= 2 and len(groups) >= 3


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


def metric_record(target_mode: str, view: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": "rank_matched_grouped",
        "target_mode": target_mode,
        "split_eval": "train_internal_grouped_by_scan_rank_matched",
        "name": view,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


def comparison(metric_rows: list[dict[str, Any]], target_mode: str, left: str, right: str) -> dict[str, Any]:
    by_name = {
        row["name"]: row["metrics"]
        for row in metric_rows
        if row["target_mode"] == target_mode
    }
    left_metrics = by_name.get(left, {})
    right_metrics = by_name.get(right, {})
    return {
        "target_mode": target_mode,
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


def pairwise_accuracy(
    rows: list[dict[str, Any]],
    pair_records: list[dict[str, Any]],
    target_mode: str,
    model_probs_by_view: dict[str, dict[str, float]],
) -> dict[str, Any]:
    row_by_id = {str(row["identity"]["prediction_id"]): row for row in rows}
    target_pairs = [
        record for record in pair_records
        if record.get("target_mode") == target_mode
        and record.get("included_in_smoke") is True
    ]
    accuracy: dict[str, float | None] = {}
    for view in PAIRWISE_VIEWS:
        wins = []
        for record in target_pairs:
            positive_id = str(record["positive_prediction_id"])
            negative_id = str(record["negative_prediction_id"])
            positive = row_by_id[positive_id]
            negative = row_by_id[negative_id]
            if view.endswith("_raw"):
                positive_score = raw_pair_score(positive, view)
                negative_score = raw_pair_score(negative, view)
            else:
                positive_score = model_probs_by_view[view][positive_id]
                negative_score = model_probs_by_view[view][negative_id]
            if positive_score > negative_score:
                wins.append(1.0)
            elif positive_score == negative_score:
                wins.append(0.5)
            else:
                wins.append(0.0)
        accuracy[view] = sum(wins) / len(wins) if wins else None
    gaps = [float(record["rank_gap_abs"]) for record in target_pairs]
    return {
        "target_mode": target_mode,
        "pair_count": len(target_pairs),
        "mean_rank_gap_abs": sum(gaps) / len(gaps) if gaps else None,
        "max_rank_gap_abs": max(gaps) if gaps else None,
        "pairwise_accuracy": accuracy,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Rank-Matched Target",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage check.",
        "- `(codex_ver)` is treated as real label by user-directed assumption.",
        "- No validation/test rows are used.",
        f"- Primary rows require non-tail rank band and `rank_gap_abs <= {fmt(summary['hyperparameters']['max_rank_gap'])}`.",
        f"- Tail rows are written only as exploratory rows when `rank_gap_abs <= {fmt(summary['hyperparameters']['tail_max_rank_gap'])}`; they are not used in smoke metrics.",
        "- Folds are grouped by `scan_id`.",
        "- `V_mv_e` is not used as model input.",
        "",
        "## Target Construction",
        "",
        "| Target | Scope | Rows | Positive | Negative | Pairs | Mean gap | Max gap | Evaluated |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary["target_summaries"]:
        lines.append(
            f"| `{row['target_mode']}` | `{row['scope']}` | {row['rows']} | "
            f"{row['positive']} | {row['negative']} | {row['pairs']} | "
            f"{fmt(row['mean_rank_gap_abs'])} | {fmt(row['max_rank_gap_abs'])} | "
            f"`{row['evaluated']}` |"
        )

    lines.extend(
        [
            "",
            "## Grouped Smoke Metrics",
            "",
            "| Target | View | AUROC | AUPRC | Brier | ECE-5 |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        metrics = row["metrics"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['name']}` | {fmt(metrics['auroc'])} | "
            f"{fmt(metrics['auprc'])} | {fmt(metrics['brier'])} | {fmt(metrics['ece_5bin'])} |"
        )

    lines.extend(
        [
            "",
            "## Key Deltas",
            "",
            "| Target | Left | Right | Delta AUROC | Delta AUPRC | Delta Brier |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["comparisons"]:
        delta = row["delta"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['left']}` | `{row['right']}` | "
            f"{fmt(delta['auroc'])} | {fmt(delta['auprc'])} | {fmt(delta['brier'])} |"
        )

    lines.extend(
        [
            "",
            "## Pairwise Accuracy",
            "",
            "| Target | Pairs | Mean gap | Factorized | Negative rank | Factorized no-rank | P-geom raw |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["pairwise_summaries"]:
        acc = row["pairwise_accuracy"]
        lines.append(
            f"| `{row['target_mode']}` | {row['pair_count']} | {fmt(row['mean_rank_gap_abs'])} | "
            f"{fmt(acc.get('factorized_reliability_posterior'))} | "
            f"{fmt(acc.get('negative_rank_only'))} | "
            f"{fmt(acc.get('factorized_no_rank'))} | "
            f"{fmt(acc.get('p_geom_valid_raw'))} |"
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


def write_outputs(output_dir: Path, summary: dict[str, Any], pair_records: list[dict[str, Any]], target_rows: dict[str, list[dict[str, Any]]]) -> None:
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_jsonl(output_dir / "pair_records.jsonl", pair_records)
    for target_mode, rows in target_rows.items():
        if rows:
            smoke.write_jsonl(output_dir / f"{target_mode}_rows.jsonl", rows)
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
    with (output_dir / "pairwise.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "target_mode",
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
    all_target_rows: dict[str, list[dict[str, Any]]] = {}
    all_pair_records: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    comparisons: list[dict[str, Any]] = []
    pairwise_summaries: list[dict[str, Any]] = []
    target_summaries: list[dict[str, Any]] = []
    feature_summaries: dict[str, Any] = {}

    for source_target_mode, filename in TARGET_ROW_FILES.items():
        rows = rank_debias.add_rank_debias_views(smoke.read_jsonl(input_dir / filename))
        target_rows, pair_records = build_rank_matched_targets(
            rows,
            source_target_mode,
            max_rank_gap=args.max_rank_gap,
            tail_max_rank_gap=args.tail_max_rank_gap,
        )
        all_pair_records.extend(pair_records)
        for target_mode, rows_for_target in target_rows.items():
            all_target_rows[target_mode] = rows_for_target

    for target_mode, rows in sorted(all_target_rows.items()):
        if not rows:
            continue
        pair_scope_name = str(rows[0]["target"].get("rank_matched_pair_scope"))
        gaps = [float(row["target"]["rank_gap_abs"]) for row in rows if row["target"].get("rank_matched_pair_role") == "positive"]
        evaluated = pair_scope_name == "primary" and can_group_eval(rows)
        counts = class_counts(rows)
        target_summaries.append(
            {
                "target_mode": target_mode,
                "scope": pair_scope_name,
                "rows": counts["rows"],
                "positive": counts["positive"],
                "negative": counts["negative"],
                "pairs": counts["positive"],
                "mean_rank_gap_abs": sum(gaps) / len(gaps) if gaps else None,
                "max_rank_gap_abs": max(gaps) if gaps else None,
                "evaluated": evaluated,
            }
        )
        if not evaluated:
            continue
        model_probs_by_view: dict[str, dict[str, float]] = {}
        for view in VIEWS:
            probs, feature_summary = safe_train_predict_grouped(
                rows,
                view,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            feature_summaries[f"{target_mode}:{view}"] = feature_summary
            metric_rows.append(metric_record(target_mode, view, rows, probs))
            model_probs_by_view[view] = {
                str(row["identity"]["prediction_id"]): prob
                for row, prob in zip(rows, probs)
            }
            pred_path = output_dir / f"predictions_{target_mode}_{view}.jsonl"
            smoke.write_jsonl(
                pred_path,
                smoke.build_prediction_rows(
                    rows,
                    target_mode,
                    "train_internal_grouped_by_scan_rank_matched",
                    view,
                    probs,
                ),
            )
        comparisons.extend(
            [
                comparison(metric_rows, target_mode, "factorized_reliability_posterior", "semantic_plus_geometry"),
                comparison(metric_rows, target_mode, "factorized_reliability_posterior", "negative_rank_only"),
                comparison(metric_rows, target_mode, "negative_rank_plus_factorized_no_rank", "negative_rank_only"),
                comparison(metric_rows, target_mode, "negative_rank_plus_disagreement", "negative_rank_only"),
                comparison(metric_rows, target_mode, "factorized_no_rank", "geometry_continuous_only"),
            ]
        )
        pairwise_summaries.append(pairwise_accuracy(rows, all_pair_records, target_mode, model_probs_by_view))

    factorized_beats_rank = [
        row for row in comparisons
        if row["left"] == "factorized_reliability_posterior"
        and row["right"] == "negative_rank_only"
        and row["delta"]["auprc"] is not None
        and row["delta"]["auprc"] >= 0.03
        and (row["delta"]["brier"] is None or row["delta"]["brier"] <= 0.0)
    ]
    rank_plus_nonrank_beats_rank = [
        row for row in comparisons
        if row["left"] == "negative_rank_plus_factorized_no_rank"
        and row["right"] == "negative_rank_only"
        and row["delta"]["auprc"] is not None
        and row["delta"]["auprc"] >= 0.03
        and (row["delta"]["brier"] is None or row["delta"]["brier"] <= 0.0)
    ]
    pairwise_support = [
        row for row in pairwise_summaries
        if row["pairwise_accuracy"].get("factorized_reliability_posterior") is not None
        and row["pairwise_accuracy"].get("negative_rank_only") is not None
        and row["pairwise_accuracy"]["factorized_reliability_posterior"]
        > row["pairwise_accuracy"]["negative_rank_only"]
    ]
    if factorized_beats_rank and rank_plus_nonrank_beats_rank and pairwise_support:
        status = "rank_matched_factorized_support"
        decision = (
            "Rank-matched target provides positive support: factorized posterior and "
            "non-rank evidence improve over the negative-rank proxy under scan-grouped "
            "CV and pairwise checks."
        )
    elif factorized_beats_rank or rank_plus_nonrank_beats_rank or pairwise_support:
        status = "rank_matched_mixed"
        decision = (
            "Rank-matched target is mixed. The stricter target reduces large rank-gap "
            "shortcuts, but support is not jointly stable across grouped metrics, "
            "rank-proxy controls, and pairwise checks."
        )
    else:
        status = "rank_matched_not_supported"
        decision = (
            "Rank-matched target does not support a factorized posterior method claim. "
            "After stricter rank matching, the target is still not explained better "
            "than the rank proxy by deployable non-rank evidence."
        )

    summary = {
        "schema_version": "h002_rank_matched_target_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "input_dir": smoke.rel_path(input_dir),
            **{target_mode: smoke.rel_path(input_dir / filename) for target_mode, filename in TARGET_ROW_FILES.items()},
        },
        "output_dir": smoke.rel_path(output_dir),
        "hyperparameters": {
            "max_rank_gap": args.max_rank_gap,
            "tail_max_rank_gap": args.tail_max_rank_gap,
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
            "validation_usage": False,
            "test_usage": False,
            "vmv_model_input_allowed": False,
            "tail_rows_used_in_smoke_metrics": False,
            "pair_metadata_is_model_input": False,
        },
        "target_summaries": target_summaries,
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "pairwise_summaries": pairwise_summaries,
        "feature_summaries": feature_summaries,
        "pair_record_counts": {
            "total": len(all_pair_records),
            "primary_included": sum(1 for row in all_pair_records if row.get("pair_scope") == "primary"),
            "tail_exploratory_included": sum(1 for row in all_pair_records if row.get("pair_scope") == "tail_exploratory"),
            "rejected_primary_gap": sum(1 for row in all_pair_records if row.get("pair_scope") == "rejected_primary_gap"),
            "rejected_tail_gap": sum(1 for row in all_pair_records if row.get("pair_scope") == "rejected_tail_gap"),
        },
        "decision": decision,
    }
    write_outputs(output_dir, summary, all_pair_records, all_target_rows)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    evaluated = [row for row in summary["target_summaries"] if row["evaluated"]]
    print(
        f"status={summary['status']} evaluated_targets={len(evaluated)} "
        f"metrics={len(summary['metric_rows'])} primary_pairs={summary['pair_record_counts']['primary_included']} "
        f"tail_pairs={summary['pair_record_counts']['tail_exploratory_included']} "
        f"validation_used={summary['hyperparameters']['uses_validation_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
