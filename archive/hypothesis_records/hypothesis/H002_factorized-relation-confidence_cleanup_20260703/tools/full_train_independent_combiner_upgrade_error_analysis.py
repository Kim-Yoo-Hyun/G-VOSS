#!/usr/bin/env python3
"""Post-hoc error analysis for H002 combiner upgrade smoke."""

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
DEFAULT_SMOKE_DIR = RGA_ROOT / "independent_combiner_upgrade_smoke_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_combiner_upgrade_error_analysis_codex_ver"

REFERENCE_VIEW = "semantic_plus_geometry"
FOCUS_VIEWS = [
    "C1_residual_logit_calibrator",
    "C2_family_gated_residual",
    "C3_uncertainty_gated_geometry",
]
REPORT_VIEWS = [
    "current_factorized_reliability_posterior",
    "residual_reliability_model",
    *FOCUS_VIEWS,
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-k", type=int, default=20)
    return parser.parse_args()


def safe_float(value: Any, default: float = 0.0) -> float:
    return smoke.safe_float(value, default)


def fixed_bin(value: float, edges: list[float], labels: list[str]) -> str:
    for edge, label in zip(edges, labels):
        if value < edge:
            return label
    return labels[-1]


def semantic_bin(value: float) -> str:
    return fixed_bin(value, [0.5, 0.7, 0.85], ["s<0.50", "0.50<=s<0.70", "0.70<=s<0.85", "s>=0.85"])


def geometry_bin(value: float) -> str:
    return fixed_bin(value, [0.25, 0.5, 0.75], ["g<0.25", "0.25<=g<0.50", "0.50<=g<0.75", "g>=0.75"])


def disagreement_bin(value: float) -> str:
    return fixed_bin(value, [0.1, 0.3, 0.5], ["d<0.10", "0.10<=d<0.30", "0.30<=d<0.50", "d>=0.50"])


def gate_bin(value: float) -> str:
    return fixed_bin(value, [0.35, 0.5, 0.65], ["gate<0.35", "0.35<=gate<0.50", "0.50<=gate<0.65", "gate>=0.65"])


def consistency_bin(value: float) -> str:
    return fixed_bin(value, [0.15, 0.3, 0.5], ["c<0.15", "0.15<=c<0.30", "0.30<=c<0.50", "c>=0.50"])


def direction_bin(semantic: float, geometry: float) -> str:
    gap = semantic - geometry
    if gap >= 0.25:
        return "semantic_high_geometry_low"
    if gap <= -0.25:
        return "semantic_low_geometry_high"
    return "semantic_geometry_close"


def brier(y: int, probability: float) -> float:
    return (probability - y) ** 2


def abs_error(y: int, probability: float) -> float:
    return abs(probability - y)


def correct(y: int, probability: float) -> bool:
    return int(probability >= 0.5) == y


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_predictions(smoke_dir: Path) -> dict[str, dict[str, float]]:
    predictions: dict[str, dict[str, float]] = defaultdict(dict)
    for row in smoke.read_jsonl(smoke_dir / "predictions.jsonl"):
        if row.get("split_eval") != "train_internal_grouped_by_scan":
            continue
        predictions[str(row["prediction_id"])][str(row["view"])] = safe_float(row["probability"], 0.5)
    return predictions


def rank_positions(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]], view: str) -> dict[str, int]:
    ordered = sorted(
        rows,
        key=lambda row: (
            -predictions[str(row["identity"]["prediction_id"])][view],
            str(row["identity"]["prediction_id"]),
        ),
    )
    return {str(row["identity"]["prediction_id"]): rank for rank, row in enumerate(ordered, start=1)}


def row_features(row: dict[str, Any]) -> dict[str, float]:
    base = row["baseline_inputs"]["factorized_reliability_posterior"]
    c3 = row["baseline_inputs"].get("C3_uncertainty_gated_geometry", {})
    semantic = safe_float(base.get("semantic_score_norm"))
    geom = safe_float(base.get("p_geom_valid"), 0.5)
    consistency = safe_float(base.get("consistency_score"))
    disagreement = abs(semantic - geom)
    return {
        "semantic_score_norm": semantic,
        "semantic_rank": safe_float(base.get("semantic_rank"), 0.0),
        "p_geom_valid": geom,
        "consistency_score": consistency,
        "absolute_disagreement": disagreement,
        "underconfidence_score": max(0.0, geom - semantic),
        "overconfidence_score": max(0.0, semantic - geom),
        "gate_proxy": safe_float(c3.get("gate_proxy"), 0.0),
        "semantic_uncertainty": safe_float(c3.get("semantic_uncertainty"), 0.0),
        "rank_uncertainty": safe_float(c3.get("rank_uncertainty"), 0.0),
        "low_consistency_proxy": safe_float(c3.get("low_consistency_proxy"), 0.0),
    }


def build_row_errors(
    rows: list[dict[str, Any]],
    predictions: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    ranks_by_view = {view: rank_positions(rows, predictions, view) for view in [REFERENCE_VIEW, *REPORT_VIEWS]}
    outputs = []
    for row in rows:
        identity = row["identity"]
        prediction_id = str(identity["prediction_id"])
        y = smoke.target_y(row)
        features = row_features(row)
        reference_prob = predictions[prediction_id][REFERENCE_VIEW]
        reference_rank = ranks_by_view[REFERENCE_VIEW][prediction_id]
        common = {
            "prediction_id": prediction_id,
            "scan_id": identity["scan_id"],
            "subgraph_id": identity["subgraph_id"],
            "subject_id": identity["subject_id"],
            "subject_label": identity["subject_label"],
            "predicate_label": identity["predicate_label"],
            "predicate_family": identity["predicate_family"],
            "object_id": identity["object_id"],
            "object_label": identity["object_label"],
            "target": y,
            "semantic_score_norm": features["semantic_score_norm"],
            "semantic_rank": features["semantic_rank"],
            "p_geom_valid": features["p_geom_valid"],
            "consistency_score": features["consistency_score"],
            "absolute_disagreement": features["absolute_disagreement"],
            "underconfidence_score": features["underconfidence_score"],
            "overconfidence_score": features["overconfidence_score"],
            "gate_proxy": features["gate_proxy"],
            "semantic_uncertainty": features["semantic_uncertainty"],
            "rank_uncertainty": features["rank_uncertainty"],
            "low_consistency_proxy": features["low_consistency_proxy"],
            "direction_bin": direction_bin(features["semantic_score_norm"], features["p_geom_valid"]),
            "semantic_bin": semantic_bin(features["semantic_score_norm"]),
            "geometry_bin": geometry_bin(features["p_geom_valid"]),
            "disagreement_bin": disagreement_bin(features["absolute_disagreement"]),
            "gate_bin": gate_bin(features["gate_proxy"]),
            "consistency_bin": consistency_bin(features["consistency_score"]),
            "prob_semantic_plus_geometry": reference_prob,
            "rank_semantic_plus_geometry": reference_rank,
            "brier_semantic_plus_geometry": brier(y, reference_prob),
            "abs_error_semantic_plus_geometry": abs_error(y, reference_prob),
            "correct_semantic_plus_geometry": correct(y, reference_prob),
        }
        for view in REPORT_VIEWS:
            prob = predictions[prediction_id][view]
            view_rank = ranks_by_view[view][prediction_id]
            view_brier = brier(y, prob)
            ref_brier = brier(y, reference_prob)
            view_correct = correct(y, prob)
            ref_correct = correct(y, reference_prob)
            if view_correct and not ref_correct:
                transfer_case = "view_correct_reference_wrong"
            elif ref_correct and not view_correct:
                transfer_case = "view_wrong_reference_correct"
            elif view_correct and ref_correct:
                transfer_case = "both_correct"
            else:
                transfer_case = "both_wrong"
            outputs.append(
                {
                    **common,
                    "view": view,
                    "prob_view": prob,
                    "rank_view": view_rank,
                    "prob_delta_view_minus_sg": prob - reference_prob,
                    "rank_delta_view_minus_sg": view_rank - reference_rank,
                    "brier_view": view_brier,
                    "brier_delta_view_minus_sg": view_brier - ref_brier,
                    "abs_error_view": abs_error(y, prob),
                    "abs_error_delta_view_minus_sg": abs_error(y, prob) - abs_error(y, reference_prob),
                    "correct_view": view_correct,
                    "transfer_case": transfer_case,
                    "brier_case": (
                        "view_brier_better"
                        if view_brier < ref_brier - 1e-12
                        else "reference_brier_better"
                        if ref_brier < view_brier - 1e-12
                        else "tie"
                    ),
                    "positive_rank_improved": y == 1 and view_rank < reference_rank,
                    "negative_rank_demoted": y == 0 and view_rank > reference_rank,
                }
            )
    return outputs


def aggregate_slice(slice_name: str, slice_value: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [int(row["target"]) for row in rows]
    probs = [safe_float(row["prob_view"], 0.5) for row in rows]
    ref_probs = [safe_float(row["prob_semantic_plus_geometry"], 0.5) for row in rows]
    metrics = smoke.metrics(labels, probs) if len(set(labels)) == 2 else None
    ref_metrics = smoke.metrics(labels, ref_probs) if len(set(labels)) == 2 else None
    transfer_counts = Counter(str(row["transfer_case"]) for row in rows)
    brier_counts = Counter(str(row["brier_case"]) for row in rows)
    positives = [row for row in rows if int(row["target"]) == 1]
    negatives = [row for row in rows if int(row["target"]) == 0]
    mean_brier_delta = sum(safe_float(row["brier_delta_view_minus_sg"]) for row in rows) / len(rows)
    mean_prob_delta = sum(safe_float(row["prob_delta_view_minus_sg"]) for row in rows) / len(rows)
    mean_rank_delta_pos = (
        sum(safe_float(row["rank_delta_view_minus_sg"]) for row in positives) / len(positives)
        if positives
        else None
    )
    mean_rank_delta_neg = (
        sum(safe_float(row["rank_delta_view_minus_sg"]) for row in negatives) / len(negatives)
        if negatives
        else None
    )
    return {
        "view": rows[0]["view"],
        "slice_name": slice_name,
        "slice_value": slice_value,
        "rows": len(rows),
        "positive": sum(labels),
        "negative": len(labels) - sum(labels),
        "view_correct_reference_wrong": transfer_counts["view_correct_reference_wrong"],
        "view_wrong_reference_correct": transfer_counts["view_wrong_reference_correct"],
        "both_correct": transfer_counts["both_correct"],
        "both_wrong": transfer_counts["both_wrong"],
        "new_mistakes_minus_fixes": transfer_counts["view_wrong_reference_correct"]
        - transfer_counts["view_correct_reference_wrong"],
        "view_brier_better": brier_counts["view_brier_better"],
        "reference_brier_better": brier_counts["reference_brier_better"],
        "mean_brier_delta_view_minus_sg": mean_brier_delta,
        "mean_prob_delta_view_minus_sg": mean_prob_delta,
        "mean_positive_rank_delta_view_minus_sg": mean_rank_delta_pos,
        "mean_negative_rank_delta_view_minus_sg": mean_rank_delta_neg,
        "positive_rank_improved": sum(1 for row in positives if row["positive_rank_improved"]),
        "negative_rank_demoted": sum(1 for row in negatives if row["negative_rank_demoted"]),
        "view_auroc": metrics.get("auroc") if metrics else None,
        "sg_auroc": ref_metrics.get("auroc") if ref_metrics else None,
        "delta_auroc_view_minus_sg": (
            metrics.get("auroc") - ref_metrics.get("auroc")
            if metrics and metrics.get("auroc") is not None and ref_metrics and ref_metrics.get("auroc") is not None
            else None
        ),
        "view_auprc": metrics.get("auprc") if metrics else None,
        "sg_auprc": ref_metrics.get("auprc") if ref_metrics else None,
        "delta_auprc_view_minus_sg": (
            metrics.get("auprc") - ref_metrics.get("auprc")
            if metrics and metrics.get("auprc") is not None and ref_metrics and ref_metrics.get("auprc") is not None
            else None
        ),
        "view_brier": metrics.get("brier") if metrics else None,
        "sg_brier": ref_metrics.get("brier") if ref_metrics else None,
        "delta_brier_view_minus_sg": (
            metrics.get("brier") - ref_metrics.get("brier")
            if metrics and ref_metrics and metrics.get("brier") is not None and ref_metrics.get("brier") is not None
            else None
        ),
    }


def build_slice_rows(row_errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slice_keys = [
        "predicate_family",
        "predicate_label",
        "direction_bin",
        "semantic_bin",
        "geometry_bin",
        "disagreement_bin",
        "gate_bin",
        "consistency_bin",
    ]
    outputs = []
    by_view: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in row_errors:
        by_view[str(row["view"])].append(row)
    for view, view_rows in sorted(by_view.items()):
        for key in slice_keys:
            groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for row in view_rows:
                groups[str(row[key])].append(row)
            for value, rows in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
                outputs.append(aggregate_slice(key, value, rows))
    return outputs


def rank_summary(row_errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    by_view: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in row_errors:
        by_view[str(row["view"])].append(row)
    for view, rows in sorted(by_view.items()):
        positives = [row for row in rows if int(row["target"]) == 1]
        negatives = [row for row in rows if int(row["target"]) == 0]
        outputs.append(
            {
                "view": view,
                "rows": len(rows),
                "positive": len(positives),
                "negative": len(negatives),
                "positive_rank_improved": sum(1 for row in positives if row["positive_rank_improved"]),
                "positive_rank_worsened": sum(1 for row in positives if safe_float(row["rank_delta_view_minus_sg"]) > 0),
                "negative_rank_demoted": sum(1 for row in negatives if row["negative_rank_demoted"]),
                "negative_rank_promoted": sum(1 for row in negatives if safe_float(row["rank_delta_view_minus_sg"]) < 0),
                "mean_positive_rank_delta": sum(safe_float(row["rank_delta_view_minus_sg"]) for row in positives)
                / len(positives),
                "mean_negative_rank_delta": sum(safe_float(row["rank_delta_view_minus_sg"]) for row in negatives)
                / len(negatives),
                "mean_positive_prob_delta": sum(safe_float(row["prob_delta_view_minus_sg"]) for row in positives)
                / len(positives),
                "mean_negative_prob_delta": sum(safe_float(row["prob_delta_view_minus_sg"]) for row in negatives)
                / len(negatives),
            }
        )
    return outputs


def diagnose(summary: dict[str, Any], slice_rows: list[dict[str, Any]], ranks: list[dict[str, Any]]) -> list[str]:
    diagnoses = []
    by_view = {row["view"]: row for row in summary["threshold_transfer"]}
    if by_view.get("C2_family_gated_residual", {}).get("new_mistakes_minus_fixes", 0) > 0:
        diagnoses.append("C2_ranking_gain_is_not_calibrated_safe")
    if by_view.get("C3_uncertainty_gated_geometry", {}).get("new_mistakes_minus_fixes", 1) <= 0:
        diagnoses.append("C3_threshold_transfer_is_safer_than_C2")
    grouped_metrics = {
        row["name"]: row["metrics"]
        for row in summary["metric_rows"]
        if row["split_eval"] == "train_internal_grouped_by_scan"
    }
    if grouped_metrics["C3_uncertainty_gated_geometry"]["auprc"] < grouped_metrics[REFERENCE_VIEW]["auprc"]:
        diagnoses.append("C3_calibration_gain_trades_off_ranking")
    c2_support = [
        row
        for row in slice_rows
        if row["view"] == "C2_family_gated_residual"
        and row["slice_name"] == "predicate_family"
        and row["slice_value"] == "support_contact"
    ]
    if c2_support and safe_float(c2_support[0]["mean_brier_delta_view_minus_sg"]) > 0:
        diagnoses.append("C2_family_gate_overcorrects_support_contact")
    c3_vertical = [
        row
        for row in slice_rows
        if row["view"] == "C3_uncertainty_gated_geometry"
        and row["slice_name"] == "predicate_family"
        and row["slice_value"] == "relative_vertical"
    ]
    if c3_vertical and safe_float(c3_vertical[0]["delta_auprc_view_minus_sg"]) > 0:
        diagnoses.append("C3_is_promising_for_relative_vertical_not_global")
    if any(row["view"] == "C2_family_gated_residual" and row["positive_rank_improved"] > row["positive_rank_worsened"] for row in ranks):
        diagnoses.append("C2_moves_some_positives_up_but_probability_scale_is_bad")
    return diagnoses


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Independent Combiner Upgrade Error Analysis",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only post-hoc analysis on combiner upgrade smoke outputs.",
        "- No validation/test rows are used.",
        "- No new model is trained here.",
        "- Hidden audit metadata is not used.",
        "- Multi-view is not used.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Main Diagnosis",
        "",
    ]
    for item in summary["diagnosis"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Rank/Probability Movement",
            "",
            "| View | Pos Rank Improved | Pos Rank Worsened | Neg Demoted | Neg Promoted | Mean Pos Prob Delta | Mean Neg Prob Delta |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["rank_summary"]:
        if row["view"] not in FOCUS_VIEWS:
            continue
        lines.append(
            f"| `{row['view']}` | {row['positive_rank_improved']} | {row['positive_rank_worsened']} | "
            f"{row['negative_rank_demoted']} | {row['negative_rank_promoted']} | "
            f"{fmt(row['mean_positive_prob_delta'])} | {fmt(row['mean_negative_prob_delta'])} |"
        )
    lines.extend(
        [
            "",
            "## Key Slice Deltas",
            "",
            "| View | Slice | Value | Rows | Delta AUPRC | Delta Brier | New-Fix |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["important_slices"]:
        lines.append(
            f"| `{row['view']}` | `{row['slice_name']}` | `{row['slice_value']}` | {row['rows']} | "
            f"{fmt(row['delta_auprc_view_minus_sg'])} | {fmt(row['mean_brier_delta_view_minus_sg'])} | "
            f"{row['new_mistakes_minus_fixes']} |"
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
    for view in FOCUS_VIEWS:
        view_rows = [row for row in row_errors if row["view"] == view]
        smoke.write_jsonl(
            output_dir / f"top_{view}_losses.jsonl",
            sorted(view_rows, key=lambda row: safe_float(row["brier_delta_view_minus_sg"]), reverse=True)[:20],
        )
        smoke.write_jsonl(
            output_dir / f"top_{view}_wins.jsonl",
            sorted(view_rows, key=lambda row: safe_float(row["brier_delta_view_minus_sg"]))[:20],
        )
    write_csv(
        output_dir / "slice_deltas.csv",
        summary["slice_deltas"],
        [
            "view",
            "slice_name",
            "slice_value",
            "rows",
            "positive",
            "negative",
            "view_correct_reference_wrong",
            "view_wrong_reference_correct",
            "both_correct",
            "both_wrong",
            "new_mistakes_minus_fixes",
            "view_brier_better",
            "reference_brier_better",
            "mean_brier_delta_view_minus_sg",
            "mean_prob_delta_view_minus_sg",
            "mean_positive_rank_delta_view_minus_sg",
            "mean_negative_rank_delta_view_minus_sg",
            "positive_rank_improved",
            "negative_rank_demoted",
            "view_auroc",
            "sg_auroc",
            "delta_auroc_view_minus_sg",
            "view_auprc",
            "sg_auprc",
            "delta_auprc_view_minus_sg",
            "view_brier",
            "sg_brier",
            "delta_brier_view_minus_sg",
        ],
    )
    write_csv(
        output_dir / "rank_summary.csv",
        summary["rank_summary"],
        [
            "view",
            "rows",
            "positive",
            "negative",
            "positive_rank_improved",
            "positive_rank_worsened",
            "negative_rank_demoted",
            "negative_rank_promoted",
            "mean_positive_rank_delta",
            "mean_negative_rank_delta",
            "mean_positive_prob_delta",
            "mean_negative_prob_delta",
        ],
    )
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    smoke_dir = smoke.as_abs(args.smoke_dir)
    output_dir = smoke.as_abs(args.output_dir)
    smoke_summary = read_json(smoke_dir / "summary.json")
    rows = smoke.read_jsonl(smoke_dir / "combiner_rows.jsonl")
    predictions = load_predictions(smoke_dir)
    row_errors = build_row_errors(rows, predictions)
    slice_rows = build_slice_rows(row_errors)
    ranks = rank_summary(row_errors)
    important_slices = [
        row
        for row in slice_rows
        if row["view"] in {"C2_family_gated_residual", "C3_uncertainty_gated_geometry"}
        and row["slice_name"] in {"predicate_family", "direction_bin"}
    ]
    important_slices = sorted(
        important_slices,
        key=lambda row: (row["view"], row["slice_name"], -abs(safe_float(row["mean_brier_delta_view_minus_sg"]))),
    )
    diagnosis = diagnose(smoke_summary, slice_rows, ranks)
    summary = {
        "schema_version": "h002_full_train_independent_combiner_upgrade_error_analysis_summary_v0",
        "status": "full_train_independent_combiner_upgrade_error_analysis_ready_for_decision",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "smoke_summary": smoke.rel_path(smoke_dir / "summary.json"),
            "smoke_status": smoke_summary.get("status"),
        },
        "output_dir": smoke.rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_model": False,
            "hidden_metadata_used": False,
            "multi_view_used": False,
            "paper_evidence_allowed": False,
        },
        "threshold_transfer": smoke_summary["threshold_transfer"],
        "rank_summary": ranks,
        "slice_deltas": slice_rows,
        "important_slices": important_slices,
        "diagnosis": diagnosis,
        "decision": (
            "C2 and C3 expose different partial benefits, but neither supports a global "
            "posterior claim. C2 is a ranking-oriented family gate with calibration damage; "
            "C3 is a safer threshold/calibration gate that loses ranking. The next step "
            "should decide whether to revise factors/target or keep the result as a "
            "negative boundary before adding model capacity."
        ),
        "next_todo": "full_train_independent_combiner_path_decision",
    }
    write_outputs(output_dir, summary, row_errors)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    c2 = next(row for row in summary["rank_summary"] if row["view"] == "C2_family_gated_residual")
    c3 = next(row for row in summary["rank_summary"] if row["view"] == "C3_uncertainty_gated_geometry")
    print(
        "status={status} validation_used={validation_used} hidden_used={hidden_used} "
        "c2_pos_rank_improved={c2_pos} c3_new_fix={c3_new_fix} next={next_todo}".format(
            status=summary["status"],
            validation_used=summary["boundary"]["validation_usage"],
            hidden_used=summary["boundary"]["hidden_metadata_used"],
            c2_pos=c2["positive_rank_improved"],
            c3_new_fix=next(
                row["new_mistakes_minus_fixes"]
                for row in summary["threshold_transfer"]
                if row["view"] == "C3_uncertainty_gated_geometry"
            ),
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
