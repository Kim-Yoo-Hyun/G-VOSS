#!/usr/bin/env python3
"""Error analysis for H002 revised-sampling controlled posterior smoke."""

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

DEFAULT_SMOKE_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke_all_label_ready"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_controlled_error_analysis_all_label_ready"

REFERENCE_VIEW = "semantic_plus_geometry"
PRIMARY_VIEW = "factorized_reliability_posterior"
ANALYSIS_VIEWS = [
    "semantic_only",
    "geometry_only",
    "semantic_geometry_coverage",
    "factorized_reliability_posterior",
    "residual_reliability_model",
]
DIAGNOSTIC_VIEWS = [
    "semantic_score_only",
    "rank_only",
    "p_geom_valid_only",
    "coverage_only",
]
SLICE_KEYS = [
    "predicate_family",
    "predicate_label",
    "quadrant_bin",
    "mismatch_direction",
    "disagreement_bin",
    "p_geom_valid_bin",
    "semantic_score_bin",
    "consistency_bin",
    "rank_bin",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def safe_float(value: Any, default: float = 0.0) -> float:
    return smoke.safe_float(value, default)


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


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


def load_predictions(smoke_dir: Path) -> dict[str, dict[str, float]]:
    predictions: dict[str, dict[str, float]] = defaultdict(dict)
    for row in smoke.read_jsonl(smoke_dir / "predictions.jsonl"):
        if row.get("split_eval") != "train_internal_grouped_by_scan":
            continue
        predictions[str(row["prediction_id"])][str(row["view"])] = safe_float(row.get("probability"), 0.5)
    return dict(predictions)


def metrics_or_none(labels: list[int], scores: list[float]) -> dict[str, Any] | None:
    if len(set(labels)) != 2:
        return None
    return smoke.metrics(labels, scores)


def brier(y: int, probability: float) -> float:
    return (probability - y) ** 2


def correct(y: int, probability: float) -> bool:
    return int(probability >= 0.5) == int(y)


def numeric_bin(value: float, cuts: list[float], labels: list[str]) -> str:
    for cut, label in zip(cuts, labels):
        if value < cut:
            return label
    return labels[-1]


def feature_row(row: dict[str, Any]) -> dict[str, Any]:
    return row["baseline_inputs"][PRIMARY_VIEW]


def rank_value(row: dict[str, Any]) -> float:
    return safe_float(row["baseline_inputs"]["semantic_only"].get("semantic_rank"), 9999.0)


def bins(row: dict[str, Any]) -> dict[str, str]:
    feat = feature_row(row)
    semantic = safe_float(feat.get("semantic_score_norm"))
    geom = safe_float(feat.get("p_geom_valid"), 0.5)
    consistency = safe_float(feat.get("consistency_score"), 0.5)
    disagreement = abs(semantic - geom)
    rank = rank_value(row)

    if semantic >= 0.75 and geom >= 0.75:
        quadrant = "HH_high_semantic_high_geometry"
    elif semantic >= 0.75 and geom < 0.75:
        quadrant = "HL_high_semantic_low_geometry"
    elif semantic < 0.75 and geom >= 0.75:
        quadrant = "LH_low_semantic_high_geometry"
    else:
        quadrant = "LL_low_semantic_low_geometry"

    gap = semantic - geom
    if gap >= 0.25:
        direction = "semantic_higher_than_geometry"
    elif gap <= -0.25:
        direction = "geometry_higher_than_semantic"
    else:
        direction = "semantic_geometry_close"

    return {
        "quadrant_bin": quadrant,
        "mismatch_direction": direction,
        "disagreement_bin": numeric_bin(
            disagreement,
            [0.15, 0.35, 0.65],
            ["disagreement_lt_0_15", "disagreement_0_15_0_35", "disagreement_0_35_0_65", "disagreement_ge_0_65"],
        ),
        "p_geom_valid_bin": numeric_bin(
            geom,
            [0.25, 0.50, 0.75],
            ["p_geom_lt_0_25", "p_geom_0_25_0_50", "p_geom_0_50_0_75", "p_geom_ge_0_75"],
        ),
        "semantic_score_bin": numeric_bin(
            semantic,
            [0.50, 0.75, 0.90],
            ["semantic_lt_0_50", "semantic_0_50_0_75", "semantic_0_75_0_90", "semantic_ge_0_90"],
        ),
        "consistency_bin": numeric_bin(
            consistency,
            [0.25, 0.50, 0.75],
            ["consistency_lt_0_25", "consistency_0_25_0_50", "consistency_0_50_0_75", "consistency_ge_0_75"],
        ),
        "rank_bin": numeric_bin(rank, [50, 100, 200], ["rank_lt_50", "rank_50_99", "rank_100_199", "rank_ge_200"]),
    }


def rank_positions(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]], view: str) -> dict[str, int]:
    ordered = sorted(
        rows,
        key=lambda row: (
            -predictions[str(row["identity"]["prediction_id"])].get(view, 0.5),
            str(row["identity"]["prediction_id"]),
        ),
    )
    return {str(row["identity"]["prediction_id"]): rank for rank, row in enumerate(ordered, start=1)}


def row_error_table(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    rank_by_view = {view: rank_positions(rows, predictions, view) for view in [REFERENCE_VIEW, *ANALYSIS_VIEWS, *DIAGNOSTIC_VIEWS]}
    outputs = []
    for row in rows:
        identity = row["identity"]
        row_id = str(identity["prediction_id"])
        y = smoke.target_y(row)
        feat = feature_row(row)
        ref = predictions[row_id][REFERENCE_VIEW]
        primary = predictions[row_id][PRIMARY_VIEW]
        row_bins = bins(row)
        common = {
            "prediction_id": row_id,
            "blind_review_id": identity.get("blind_review_id"),
            "scan_id": identity.get("scan_id"),
            "subgraph_id": identity.get("subgraph_id"),
            "subject_id": identity.get("subject_id"),
            "subject_label": identity.get("subject_label"),
            "predicate_label": identity.get("predicate_label"),
            "predicate_family": identity.get("predicate_family"),
            "object_id": identity.get("object_id"),
            "object_label": identity.get("object_label"),
            "target": y,
            "target_reason": row.get("target", {}).get("target_reason"),
            "semantic_score_norm": safe_float(feat.get("semantic_score_norm")),
            "semantic_rank": rank_value(row),
            "p_geom_valid": safe_float(feat.get("p_geom_valid"), 0.5),
            "consistency_score": safe_float(feat.get("consistency_score"), 0.5),
            "absolute_disagreement": safe_float(feat.get("absolute_disagreement")),
            "underconfidence_score": safe_float(feat.get("underconfidence_score")),
            "overconfidence_score": safe_float(feat.get("overconfidence_score")),
            **row_bins,
        }
        view_fields: dict[str, Any] = {}
        for view in [REFERENCE_VIEW, *ANALYSIS_VIEWS, *DIAGNOSTIC_VIEWS]:
            if view in predictions[row_id]:
                view_fields[f"prob_{view}"] = predictions[row_id][view]
                view_fields[f"brier_{view}"] = brier(y, predictions[row_id][view])
                view_fields[f"correct_{view}"] = correct(y, predictions[row_id][view])
                view_fields[f"rank_{view}"] = rank_by_view[view][row_id]
        ref_correct = correct(y, ref)
        primary_correct = correct(y, primary)
        if primary_correct and not ref_correct:
            transfer = "factorized_fixes_sg_error"
        elif ref_correct and not primary_correct:
            transfer = "factorized_adds_error"
        elif primary_correct and ref_correct:
            transfer = "both_correct"
        else:
            transfer = "both_wrong"
        outputs.append(
            {
                **common,
                **view_fields,
                "prob_delta_factorized_minus_sg": primary - ref,
                "rank_delta_factorized_minus_sg": rank_by_view[PRIMARY_VIEW][row_id] - rank_by_view[REFERENCE_VIEW][row_id],
                "brier_delta_factorized_minus_sg": brier(y, primary) - brier(y, ref),
                "transfer_factorized_vs_sg": transfer,
                "primary_error_direction": (
                    "false_positive"
                    if y == 0 and primary >= 0.5
                    else "false_negative"
                    if y == 1 and primary < 0.5
                    else "correct"
                ),
            }
        )
    return outputs


def summarize_view_transfer(row_errors: list[dict[str, Any]], view: str) -> dict[str, Any]:
    counts = Counter()
    for row in row_errors:
        y = int(row["target"])
        ref = safe_float(row[f"prob_{REFERENCE_VIEW}"], 0.5)
        prob = safe_float(row[f"prob_{view}"], 0.5)
        view_correct = correct(y, prob)
        ref_correct = correct(y, ref)
        if view_correct and not ref_correct:
            counts["view_fixes_reference_error"] += 1
        elif ref_correct and not view_correct:
            counts["view_adds_error"] += 1
        elif view_correct and ref_correct:
            counts["both_correct"] += 1
        else:
            counts["both_wrong"] += 1
    return {
        "view": view,
        "reference_view": REFERENCE_VIEW,
        "rows": len(row_errors),
        "view_fixes_reference_error": counts["view_fixes_reference_error"],
        "view_adds_error": counts["view_adds_error"],
        "both_correct": counts["both_correct"],
        "both_wrong": counts["both_wrong"],
        "new_errors_minus_fixes": counts["view_adds_error"] - counts["view_fixes_reference_error"],
    }


def aggregate_slice(row_errors: list[dict[str, Any]], slice_name: str, slice_value: str, view: str) -> dict[str, Any]:
    labels = [int(row["target"]) for row in row_errors]
    scores = [safe_float(row[f"prob_{view}"], 0.5) for row in row_errors]
    ref_scores = [safe_float(row[f"prob_{REFERENCE_VIEW}"], 0.5) for row in row_errors]
    metrics = metrics_or_none(labels, scores)
    ref_metrics = metrics_or_none(labels, ref_scores)
    transfers = Counter()
    for row, score, ref in zip(row_errors, scores, ref_scores):
        view_correct = correct(int(row["target"]), score)
        ref_correct = correct(int(row["target"]), ref)
        if view_correct and not ref_correct:
            transfers["view_fixes_reference_error"] += 1
        elif ref_correct and not view_correct:
            transfers["view_adds_error"] += 1
        elif view_correct and ref_correct:
            transfers["both_correct"] += 1
        else:
            transfers["both_wrong"] += 1
    return {
        "view": view,
        "reference_view": REFERENCE_VIEW,
        "slice_name": slice_name,
        "slice_value": slice_value,
        "rows": len(row_errors),
        "positive": sum(labels),
        "negative": len(labels) - sum(labels),
        "view_fixes_reference_error": transfers["view_fixes_reference_error"],
        "view_adds_error": transfers["view_adds_error"],
        "new_errors_minus_fixes": transfers["view_adds_error"] - transfers["view_fixes_reference_error"],
        "mean_prob_delta_view_minus_sg": sum(score - ref for score, ref in zip(scores, ref_scores)) / len(scores),
        "mean_brier_delta_view_minus_sg": sum(
            brier(y, score) - brier(y, ref) for y, score, ref in zip(labels, scores, ref_scores)
        )
        / len(scores),
        "view_auroc": metrics.get("auroc") if metrics else None,
        "view_auprc": metrics.get("auprc") if metrics else None,
        "view_brier": metrics.get("brier") if metrics else None,
        "sg_auroc": ref_metrics.get("auroc") if ref_metrics else None,
        "sg_auprc": ref_metrics.get("auprc") if ref_metrics else None,
        "sg_brier": ref_metrics.get("brier") if ref_metrics else None,
        "delta_auroc_view_minus_sg": (
            metrics.get("auroc") - ref_metrics.get("auroc")
            if metrics and ref_metrics and metrics.get("auroc") is not None and ref_metrics.get("auroc") is not None
            else None
        ),
        "delta_auprc_view_minus_sg": (
            metrics.get("auprc") - ref_metrics.get("auprc")
            if metrics and ref_metrics and metrics.get("auprc") is not None and ref_metrics.get("auprc") is not None
            else None
        ),
        "delta_brier_view_minus_sg": (
            metrics.get("brier") - ref_metrics.get("brier")
            if metrics and ref_metrics and metrics.get("brier") is not None and ref_metrics.get("brier") is not None
            else None
        ),
    }


def build_slice_deltas(row_errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    for view in ANALYSIS_VIEWS:
        for key in SLICE_KEYS:
            groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in row_errors:
                groups[str(row[key])].append(row)
            for value, group_rows in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
                outputs.append(aggregate_slice(group_rows, key, value, view))
    return outputs


def feature_label_summary(row_errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    keys = [("all", "all"), *[("predicate_family", family) for family in sorted({str(row["predicate_family"]) for row in row_errors})]]
    for key, value in keys:
        selected = row_errors if key == "all" else [row for row in row_errors if str(row[key]) == value]
        for target in [0, 1]:
            rows = [row for row in selected if int(row["target"]) == target]
            if not rows:
                continue
            outputs.append(
                {
                    "slice_name": key,
                    "slice_value": value,
                    "target": target,
                    "rows": len(rows),
                    "mean_semantic_score_norm": sum(safe_float(row["semantic_score_norm"]) for row in rows) / len(rows),
                    "mean_p_geom_valid": sum(safe_float(row["p_geom_valid"]) for row in rows) / len(rows),
                    "mean_consistency_score": sum(safe_float(row["consistency_score"]) for row in rows) / len(rows),
                    "mean_absolute_disagreement": sum(safe_float(row["absolute_disagreement"]) for row in rows) / len(rows),
                    "mean_prob_semantic_plus_geometry": sum(safe_float(row[f"prob_{REFERENCE_VIEW}"]) for row in rows) / len(rows),
                    "mean_prob_factorized": sum(safe_float(row[f"prob_{PRIMARY_VIEW}"]) for row in rows) / len(rows),
                    "factorized_accuracy": sum(1 for row in rows if bool(row[f"correct_{PRIMARY_VIEW}"])) / len(rows),
                }
            )
    return outputs


def metric_lookup(smoke_summary: dict[str, Any], split_eval: str, name: str) -> dict[str, Any]:
    for row in smoke_summary["metric_rows"]:
        if row["split_eval"] == split_eval and row["name"] == name:
            return row["metrics"]
    return {}


def comparison_lookup(smoke_summary: dict[str, Any], split_eval: str, left: str, right: str) -> dict[str, Any]:
    for row in smoke_summary["comparisons"]:
        if row["split_eval"] == split_eval and row["left"] == left and row["right"] == right:
            return row["delta"]
    return {}


def key_slice(slice_deltas: list[dict[str, Any]], slice_name: str, slice_value: str) -> dict[str, Any] | None:
    for row in slice_deltas:
        if row["view"] == PRIMARY_VIEW and row["slice_name"] == slice_name and row["slice_value"] == slice_value:
            return row
    return None


def build_diagnosis(smoke_summary: dict[str, Any], slice_deltas: list[dict[str, Any]], transfer_rows: list[dict[str, Any]]) -> list[str]:
    diagnosis = []
    grouped_delta = comparison_lookup(smoke_summary, "train_internal_grouped_by_scan", PRIMARY_VIEW, REFERENCE_VIEW)
    in_delta = comparison_lookup(smoke_summary, "in_sample", PRIMARY_VIEW, REFERENCE_VIEW)
    coverage_delta = comparison_lookup(
        smoke_summary,
        "train_internal_grouped_by_scan",
        "semantic_geometry_coverage",
        REFERENCE_VIEW,
    )
    factor_transfer = next(row for row in transfer_rows if row["view"] == PRIMARY_VIEW)

    if safe_float(grouped_delta.get("auprc")) <= 0.0 and safe_float(grouped_delta.get("brier"), 1.0) >= 0.0:
        diagnosis.append("factorized_does_not_add_stable_signal_over_semantic_plus_geometry")
    if safe_float(in_delta.get("auprc")) > 0.02 and safe_float(grouped_delta.get("auprc")) <= 0.0:
        diagnosis.append("in_sample_gain_collapses_under_grouped_scan_split")
    if all(abs(safe_float(coverage_delta.get(metric))) < 1e-9 for metric in ["auroc", "auprc", "brier"]):
        diagnosis.append("coverage_factor_is_constant_or_noninformative_in_all_label_ready_slice")
    if factor_transfer["new_errors_minus_fixes"] > 0:
        diagnosis.append("factorized_threshold_adds_more_errors_than_it_fixes")
    elif factor_transfer["view_fixes_reference_error"] == 0 and factor_transfer["view_adds_error"] == 0:
        diagnosis.append("factorized_threshold_decision_identical_to_semantic_plus_geometry")

    rel = key_slice(slice_deltas, "predicate_family", "relative_vertical")
    support = key_slice(slice_deltas, "predicate_family", "support_contact")
    if rel and safe_float(rel.get("delta_auprc_view_minus_sg")) < -0.03:
        diagnosis.append("relative_vertical_loses_ranking_signal_after_factorization")
    if support and safe_float(support.get("delta_auprc_view_minus_sg")) > 0.0 and safe_float(support.get("delta_brier_view_minus_sg")) > 0.0:
        diagnosis.append("support_contact_has_weak_ranking_gain_but_worse_calibration")
    if rel and support and safe_float(rel.get("delta_auprc_view_minus_sg")) * safe_float(support.get("delta_auprc_view_minus_sg")) < 0:
        diagnosis.append("family_effects_have_opposite_directions")

    hh = key_slice(slice_deltas, "quadrant_bin", "HH_high_semantic_high_geometry")
    hl = key_slice(slice_deltas, "quadrant_bin", "HL_high_semantic_low_geometry")
    if hh and hl and safe_float(hh.get("delta_brier_view_minus_sg")) > 0.0 and safe_float(hl.get("delta_brier_view_minus_sg")) > 0.0:
        diagnosis.append("factorized_brier_regresses_in_both_agreement_and_mismatch_quadrants")
    return diagnosis or ["no_single_dominant_error_pattern_detected"]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Revised Sampling Controlled Error Analysis",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only post-hoc analysis of grouped-by-scan smoke predictions.",
        "- No validation/test rows are used.",
        "- No new model is trained in this analysis.",
        "- Review fields, target labels, hidden audit metadata, packet paths, and multi-view evidence are not model inputs.",
        "- Results are hypothesis-stage diagnostics, not paper-level metrics.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Diagnosis",
        "",
    ]
    lines.extend(f"- `{item}`" for item in summary["diagnosis"])
    lines.extend(
        [
            "",
            "## Global Transfer",
            "",
            "| View | Fixes SG Errors | Adds Errors | Both Correct | Both Wrong | New-Fix |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["transfer_summary"]:
        lines.append(
            f"| `{row['view']}` | {row['view_fixes_reference_error']} | {row['view_adds_error']} | "
            f"{row['both_correct']} | {row['both_wrong']} | {row['new_errors_minus_fixes']} |"
        )
    lines.extend(
        [
            "",
            "## Key Family Slices",
            "",
            "| Family | Rows | Pos | Neg | dAUPRC | dBrier | New-Fix |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["key_family_slices"]:
        lines.append(
            f"| `{row['slice_value']}` | {row['rows']} | {row['positive']} | {row['negative']} | "
            f"{fmt(row['delta_auprc_view_minus_sg'])} | {fmt(row['delta_brier_view_minus_sg'])} | "
            f"{row['new_errors_minus_fixes']} |"
        )
    lines.extend(
        [
            "",
            "## Key Quadrant Slices",
            "",
            "| Quadrant | Rows | Pos | Neg | dAUPRC | dBrier | New-Fix |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["key_quadrant_slices"]:
        lines.append(
            f"| `{row['slice_value']}` | {row['rows']} | {row['positive']} | {row['negative']} | "
            f"{fmt(row['delta_auprc_view_minus_sg'])} | {fmt(row['delta_brier_view_minus_sg'])} | "
            f"{row['new_errors_minus_fixes']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any], row_errors: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_jsonl(output_dir / "row_errors.jsonl", row_errors)
    smoke.write_jsonl(
        output_dir / "top_factorized_losses.jsonl",
        sorted(row_errors, key=lambda row: safe_float(row["brier_delta_factorized_minus_sg"]), reverse=True)[:25],
    )
    smoke.write_jsonl(
        output_dir / "top_factorized_wins.jsonl",
        sorted(row_errors, key=lambda row: safe_float(row["brier_delta_factorized_minus_sg"]))[:25],
    )
    write_csv(output_dir / "slice_deltas.csv", summary["slice_deltas"])
    write_csv(output_dir / "transfer_summary.csv", summary["transfer_summary"])
    write_csv(output_dir / "feature_label_summary.csv", summary["feature_label_summary"])
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    smoke_dir = as_abs(args.smoke_dir)
    output_dir = as_abs(args.output_dir)
    smoke_summary = read_json(smoke_dir / "summary.json")
    rows = smoke.read_jsonl(smoke_dir / "posterior_rows.jsonl")
    predictions = load_predictions(smoke_dir)
    missing = [
        str(row["identity"]["prediction_id"])
        for row in rows
        if any(view not in predictions.get(str(row["identity"]["prediction_id"]), {}) for view in [REFERENCE_VIEW, *ANALYSIS_VIEWS])
    ]
    if missing:
        raise ValueError(f"missing grouped predictions for {len(missing)} rows; first={missing[0]}")

    row_errors = row_error_table(rows, predictions)
    slice_deltas = build_slice_deltas(row_errors)
    transfer_summary = [summarize_view_transfer(row_errors, view) for view in ANALYSIS_VIEWS]
    feature_summary = feature_label_summary(row_errors)
    diagnosis = build_diagnosis(smoke_summary, slice_deltas, transfer_summary)
    grouped_delta = comparison_lookup(smoke_summary, "train_internal_grouped_by_scan", PRIMARY_VIEW, REFERENCE_VIEW)
    in_sample_delta = comparison_lookup(smoke_summary, "in_sample", PRIMARY_VIEW, REFERENCE_VIEW)
    key_family_slices = [
        row
        for row in slice_deltas
        if row["view"] == PRIMARY_VIEW and row["slice_name"] == "predicate_family"
    ]
    key_quadrant_slices = [
        row
        for row in slice_deltas
        if row["view"] == PRIMARY_VIEW and row["slice_name"] == "quadrant_bin"
    ]

    summary = {
        "schema_version": "h002_full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis_summary_v1",
        "status": "full_train_independent_support_vertical_v2_revised_sampling_controlled_error_analysis_ready_feature_family_misalignment",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "smoke_dir": rel_path(smoke_dir),
            "smoke_status": smoke_summary.get("status"),
            "rows": len(rows),
            "positive": sum(smoke.target_y(row) for row in rows),
            "negative": len(rows) - sum(smoke.target_y(row) for row in rows),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "post_hoc_only": True,
            "trains_new_model": False,
            "review_fields_as_model_input": False,
            "hidden_metadata_as_model_input": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
            "posterior_performance_claim_allowed": False,
        },
        "reference_view": REFERENCE_VIEW,
        "primary_view": PRIMARY_VIEW,
        "grouped_factorized_minus_semantic_plus_geometry": grouped_delta,
        "in_sample_factorized_minus_semantic_plus_geometry": in_sample_delta,
        "diagnosis": diagnosis,
        "transfer_summary": transfer_summary,
        "slice_deltas": slice_deltas,
        "key_family_slices": key_family_slices,
        "key_quadrant_slices": key_quadrant_slices,
        "feature_label_summary": feature_summary,
        "decision": (
            "The current failure is best treated as feature/family alignment failure, not as a reason "
            "to immediately replace the posterior combiner. Factorized features overfit in sample, lose "
            "their advantage under grouped-by-scan evaluation, and behave differently for support_contact "
            "and relative_vertical. The next step should repair typed factor definitions and family-specific "
            "normalization before trying higher-capacity SOTA combiners."
        ),
        "claim_boundary": {
            "allowed": (
                "Train-only diagnostics show that semantic score, p_geom_valid, and simple interaction terms "
                "are not yet sufficient to form a stable relation reliability posterior on the revised all-label-ready slice."
            ),
            "blocked": (
                "Do not claim factorized posterior improvement, held-out generalization, or paper-level reliability "
                "gain from this smoke."
            ),
        },
        "next_todo": "revised_sampling_all_label_ready_factor_definition_repair_plan",
    }
    write_outputs(output_dir, summary, row_errors)
    return summary


def main() -> int:
    summary = run(parse_args())
    d = summary["grouped_factorized_minus_semantic_plus_geometry"]
    transfer = next(row for row in summary["transfer_summary"] if row["view"] == PRIMARY_VIEW)
    print(
        "status={status} rows={rows} validation_used={validation_used} "
        "d_auprc_factorized_vs_sg={d_auprc:.4f} d_brier_factorized_vs_sg={d_brier:.4f} "
        "new_errors_minus_fixes={new_minus_fix} diagnoses={diagnoses} next={next_todo}".format(
            status=summary["status"],
            rows=summary["input"]["rows"],
            validation_used=summary["boundary"]["validation_usage"],
            d_auprc=safe_float(d.get("auprc")),
            d_brier=safe_float(d.get("brier")),
            new_minus_fix=transfer["new_errors_minus_fixes"],
            diagnoses=len(summary["diagnosis"]),
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
