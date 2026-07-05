#!/usr/bin/env python3
"""Post-hoc error analysis for the H002 controlled posterior smoke."""

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
DEFAULT_SMOKE_DIR = RGA_ROOT / "independent_controlled_posterior_smoke_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_controlled_error_analysis_codex_ver"

PRIMARY_VIEW = "factorized_reliability_posterior"
REFERENCE_VIEW = "semantic_plus_geometry"
SECONDARY_VIEWS = ["semantic_only", "geometry_only", "residual_reliability_model"]
SPLIT_EVAL = "train_internal_grouped_by_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--top-k", type=int, default=20)
    return parser.parse_args()


def safe_float(value: Any, default: float = 0.0) -> float:
    return smoke.safe_float(value, default)


def sigmoid_clip(probability: float) -> float:
    return min(max(probability, 1e-6), 1.0 - 1e-6)


def brier(y: int, probability: float) -> float:
    return (probability - y) ** 2


def nll(y: int, probability: float) -> float:
    probability = sigmoid_clip(probability)
    if y == 1:
        return -math.log(probability)
    return -math.log(1.0 - probability)


def abs_error(y: int, probability: float) -> float:
    return abs(probability - y)


def threshold_correct(y: int, probability: float) -> bool:
    return int(probability >= 0.5) == int(y)


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


def consistency_bin(value: float) -> str:
    return fixed_bin(value, [0.15, 0.3, 0.5], ["c<0.15", "0.15<=c<0.30", "0.30<=c<0.50", "c>=0.50"])


def rank_bin(value: float) -> str:
    return fixed_bin(value, [10, 50, 100], ["rank<10", "10<=rank<50", "50<=rank<100", "rank>=100"])


def direction_bin(semantic: float, geometry: float) -> str:
    gap = semantic - geometry
    if gap >= 0.25:
        return "semantic_high_geometry_low"
    if gap <= -0.25:
        return "semantic_low_geometry_high"
    return "semantic_geometry_close"


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_predictions(smoke_dir: Path) -> dict[str, dict[str, float]]:
    predictions: dict[str, dict[str, float]] = defaultdict(dict)
    for row in smoke.read_jsonl(smoke_dir / "predictions.jsonl"):
        if row.get("split_eval") != SPLIT_EVAL:
            continue
        predictions[str(row["prediction_id"])][str(row["view"])] = safe_float(row["probability"], 0.5)
    return predictions


def row_features(row: dict[str, Any]) -> dict[str, float]:
    features = row["baseline_inputs"]["factorized_reliability_posterior"]
    return {
        "semantic_score_norm": safe_float(features.get("semantic_score_norm")),
        "semantic_score_raw": safe_float(features.get("semantic_score_raw")),
        "semantic_rank": safe_float(features.get("semantic_rank")),
        "semantic_rank_inverse": safe_float(features.get("semantic_rank_inverse")),
        "p_geom_valid": safe_float(features.get("p_geom_valid"), 0.5),
        "consistency_score": safe_float(features.get("consistency_score")),
        "absolute_disagreement": safe_float(features.get("absolute_disagreement")),
        "semantic_minus_geometry": safe_float(features.get("semantic_minus_geometry")),
        "geometry_minus_semantic": safe_float(features.get("geometry_minus_semantic")),
        "underconfidence_score": safe_float(features.get("underconfidence_score")),
        "overconfidence_score": safe_float(features.get("overconfidence_score")),
    }


def build_error_rows(rows: list[dict[str, Any]], predictions: dict[str, dict[str, float]]) -> list[dict[str, Any]]:
    outputs = []
    for row in rows:
        identity = row["identity"]
        target = row["target"]
        prediction_id = str(identity["prediction_id"])
        probs = predictions.get(prediction_id, {})
        if PRIMARY_VIEW not in probs or REFERENCE_VIEW not in probs:
            raise ValueError(f"missing primary/reference prediction for {prediction_id}")
        y = smoke.target_y(row)
        features = row_features(row)
        primary_prob = probs[PRIMARY_VIEW]
        reference_prob = probs[REFERENCE_VIEW]
        primary_brier = brier(y, primary_prob)
        reference_brier = brier(y, reference_prob)
        primary_nll = nll(y, primary_prob)
        reference_nll = nll(y, reference_prob)
        primary_abs = abs_error(y, primary_prob)
        reference_abs = abs_error(y, reference_prob)
        primary_correct = threshold_correct(y, primary_prob)
        reference_correct = threshold_correct(y, reference_prob)

        if primary_correct and not reference_correct:
            correctness_case = "factorized_correct_sg_wrong"
        elif reference_correct and not primary_correct:
            correctness_case = "factorized_wrong_sg_correct"
        elif primary_correct and reference_correct:
            correctness_case = "both_correct"
        else:
            correctness_case = "both_wrong"

        delta_brier = primary_brier - reference_brier
        if delta_brier < -1e-9:
            brier_case = "factorized_better"
        elif delta_brier > 1e-9:
            brier_case = "semantic_plus_geometry_better"
        else:
            brier_case = "tie"

        hidden = target
        row_out = {
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
            "relation_validity_label": target.get("relation_validity_label"),
            "confidence": target.get("confidence"),
            "label_use": target.get("label_use"),
            "semantic_score_norm": features["semantic_score_norm"],
            "semantic_rank": features["semantic_rank"],
            "p_geom_valid": features["p_geom_valid"],
            "consistency_score": features["consistency_score"],
            "absolute_disagreement": features["absolute_disagreement"],
            "underconfidence_score": features["underconfidence_score"],
            "overconfidence_score": features["overconfidence_score"],
            "direction_bin": direction_bin(features["semantic_score_norm"], features["p_geom_valid"]),
            "semantic_bin": semantic_bin(features["semantic_score_norm"]),
            "geometry_bin": geometry_bin(features["p_geom_valid"]),
            "disagreement_bin": disagreement_bin(features["absolute_disagreement"]),
            "consistency_bin": consistency_bin(features["consistency_score"]),
            "rank_bin": rank_bin(features["semantic_rank"]),
            "queue_kind_hidden_posthoc": hidden.get("queue_kind_hidden"),
            "proposed_audit_role_hidden_posthoc": hidden.get("proposed_audit_role_hidden"),
            "label_match_status_hidden_posthoc": hidden.get("label_match_status_hidden"),
            "geometry_status_hidden_posthoc": hidden.get("geometry_status_hidden"),
            "rank_band_hidden_posthoc": hidden.get("rank_band_hidden"),
            "prob_factorized": primary_prob,
            "prob_semantic_plus_geometry": reference_prob,
            "prob_semantic_only": probs.get("semantic_only"),
            "prob_geometry_only": probs.get("geometry_only"),
            "prob_residual": probs.get("residual_reliability_model"),
            "brier_factorized": primary_brier,
            "brier_semantic_plus_geometry": reference_brier,
            "brier_delta_factorized_minus_sg": delta_brier,
            "nll_factorized": primary_nll,
            "nll_semantic_plus_geometry": reference_nll,
            "nll_delta_factorized_minus_sg": primary_nll - reference_nll,
            "abs_error_factorized": primary_abs,
            "abs_error_semantic_plus_geometry": reference_abs,
            "abs_error_delta_factorized_minus_sg": primary_abs - reference_abs,
            "correct_factorized": primary_correct,
            "correct_semantic_plus_geometry": reference_correct,
            "correctness_case": correctness_case,
            "brier_case": brier_case,
            "prob_delta_factorized_minus_sg": primary_prob - reference_prob,
        }
        outputs.append(row_out)
    return outputs


def aggregate_slice(name: str, value: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [int(row["target"]) for row in rows]
    primary = [safe_float(row["prob_factorized"], 0.5) for row in rows]
    reference = [safe_float(row["prob_semantic_plus_geometry"], 0.5) for row in rows]
    primary_metrics = smoke.metrics(labels, primary) if len(set(labels)) == 2 else None
    reference_metrics = smoke.metrics(labels, reference) if len(set(labels)) == 2 else None
    case_counts = Counter(str(row["correctness_case"]) for row in rows)
    brier_counts = Counter(str(row["brier_case"]) for row in rows)
    mean_delta_brier = sum(safe_float(row["brier_delta_factorized_minus_sg"]) for row in rows) / len(rows)
    mean_delta_nll = sum(safe_float(row["nll_delta_factorized_minus_sg"]) for row in rows) / len(rows)
    mean_delta_abs = sum(safe_float(row["abs_error_delta_factorized_minus_sg"]) for row in rows) / len(rows)
    mean_prob_delta = sum(safe_float(row["prob_delta_factorized_minus_sg"]) for row in rows) / len(rows)
    mean_semantic = sum(safe_float(row["semantic_score_norm"]) for row in rows) / len(rows)
    mean_geom = sum(safe_float(row["p_geom_valid"]) for row in rows) / len(rows)
    mean_disagreement = sum(safe_float(row["absolute_disagreement"]) for row in rows) / len(rows)

    return {
        "slice_name": name,
        "slice_value": value,
        "rows": len(rows),
        "positive": sum(labels),
        "negative": len(rows) - sum(labels),
        "mean_semantic_score_norm": mean_semantic,
        "mean_p_geom_valid": mean_geom,
        "mean_absolute_disagreement": mean_disagreement,
        "factorized_correct_sg_wrong": case_counts["factorized_correct_sg_wrong"],
        "factorized_wrong_sg_correct": case_counts["factorized_wrong_sg_correct"],
        "both_correct": case_counts["both_correct"],
        "both_wrong": case_counts["both_wrong"],
        "factorized_brier_better_rows": brier_counts["factorized_better"],
        "sg_brier_better_rows": brier_counts["semantic_plus_geometry_better"],
        "mean_brier_delta_factorized_minus_sg": mean_delta_brier,
        "mean_nll_delta_factorized_minus_sg": mean_delta_nll,
        "mean_abs_error_delta_factorized_minus_sg": mean_delta_abs,
        "mean_prob_delta_factorized_minus_sg": mean_prob_delta,
        "factorized_auroc": primary_metrics.get("auroc") if primary_metrics else None,
        "sg_auroc": reference_metrics.get("auroc") if reference_metrics else None,
        "delta_auroc_factorized_minus_sg": (
            primary_metrics.get("auroc") - reference_metrics.get("auroc")
            if primary_metrics and primary_metrics.get("auroc") is not None and reference_metrics.get("auroc") is not None
            else None
        ),
        "factorized_auprc": primary_metrics.get("auprc") if primary_metrics else None,
        "sg_auprc": reference_metrics.get("auprc") if reference_metrics else None,
        "delta_auprc_factorized_minus_sg": (
            primary_metrics.get("auprc") - reference_metrics.get("auprc")
            if primary_metrics and primary_metrics.get("auprc") is not None and reference_metrics.get("auprc") is not None
            else None
        ),
        "factorized_brier": primary_metrics.get("brier") if primary_metrics else None,
        "sg_brier": reference_metrics.get("brier") if reference_metrics else None,
        "delta_brier_metric_factorized_minus_sg": (
            primary_metrics.get("brier") - reference_metrics.get("brier")
            if primary_metrics and primary_metrics.get("brier") is not None and reference_metrics.get("brier") is not None
            else None
        ),
    }


def slice_error_rows(error_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slice_keys = [
        "predicate_family",
        "predicate_label",
        "relation_validity_label",
        "confidence",
        "label_use",
        "direction_bin",
        "semantic_bin",
        "geometry_bin",
        "disagreement_bin",
        "consistency_bin",
        "rank_bin",
        "queue_kind_hidden_posthoc",
        "geometry_status_hidden_posthoc",
        "rank_band_hidden_posthoc",
        "label_match_status_hidden_posthoc",
        "proposed_audit_role_hidden_posthoc",
    ]
    outputs = []
    for key in slice_keys:
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in error_rows:
            groups[str(row.get(key))].append(row)
        for value, rows in sorted(groups.items(), key=lambda item: (-len(item[1]), item[0])):
            outputs.append(aggregate_slice(key, value, rows))
    return outputs


def view_metrics_from_errors(error_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    labels = [int(row["target"]) for row in error_rows]
    for view, key in [
        ("semantic_only", "prob_semantic_only"),
        ("geometry_only", "prob_geometry_only"),
        ("semantic_plus_geometry", "prob_semantic_plus_geometry"),
        ("factorized_reliability_posterior", "prob_factorized"),
        ("residual_reliability_model", "prob_residual"),
    ]:
        probs = [safe_float(row.get(key), 0.5) for row in error_rows]
        outputs.append({"view": view, **smoke.metrics(labels, probs)})
    return outputs


def feature_summary(error_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    outputs = []
    for key in [
        "semantic_score_norm",
        "semantic_rank",
        "p_geom_valid",
        "consistency_score",
        "absolute_disagreement",
        "underconfidence_score",
        "overconfidence_score",
    ]:
        positives = [safe_float(row[key]) for row in error_rows if int(row["target"]) == 1]
        negatives = [safe_float(row[key]) for row in error_rows if int(row["target"]) == 0]
        outputs.append(
            {
                "feature": key,
                "positive_mean": sum(positives) / len(positives) if positives else None,
                "negative_mean": sum(negatives) / len(negatives) if negatives else None,
                "positive_minus_negative": (
                    (sum(positives) / len(positives)) - (sum(negatives) / len(negatives))
                    if positives and negatives
                    else None
                ),
            }
        )
    return outputs


def summarize(error_rows: list[dict[str, Any]], smoke_summary: dict[str, Any]) -> dict[str, Any]:
    view_metrics = view_metrics_from_errors(error_rows)
    by_view = {row["view"]: row for row in view_metrics}
    primary = by_view[PRIMARY_VIEW]
    reference = by_view[REFERENCE_VIEW]
    semantic = by_view["semantic_only"]
    geometry = by_view["geometry_only"]
    case_counts = Counter(str(row["correctness_case"]) for row in error_rows)
    brier_counts = Counter(str(row["brier_case"]) for row in error_rows)
    slice_rows = slice_error_rows(error_rows)

    family_rows = [row for row in slice_rows if row["slice_name"] == "predicate_family"]
    helpful_families = [
        row["slice_value"]
        for row in family_rows
        if row["delta_auprc_factorized_minus_sg"] is not None and row["delta_auprc_factorized_minus_sg"] > 0.0
    ]
    harmful_families = [
        row["slice_value"]
        for row in family_rows
        if row["delta_auprc_factorized_minus_sg"] is not None and row["delta_auprc_factorized_minus_sg"] <= 0.0
    ]
    diagnosis = []
    if primary["auprc"] < reference["auprc"]:
        diagnosis.append("factorized_underperforms_semantic_plus_geometry_grouped")
    if primary["brier"] > reference["brier"]:
        diagnosis.append("factorized_calibration_worse_than_semantic_plus_geometry")
    if semantic["auprc"] > geometry["auprc"]:
        diagnosis.append("semantic_signal_stronger_than_geometry_signal")
    if len(helpful_families) > 0 and len(harmful_families) > 0:
        diagnosis.append("family_dependent_fusion_needed")
    if case_counts["factorized_wrong_sg_correct"] > case_counts["factorized_correct_sg_wrong"]:
        diagnosis.append("factorized_creates_more_threshold_errors_than_it_fixes")
    if brier_counts["semantic_plus_geometry_better"] > brier_counts["factorized_better"]:
        diagnosis.append("row_level_brier_losses_exceed_wins")

    combiner_recommendation = [
        {
            "priority": 1,
            "name": "family_gated_calibrated_fusion",
            "reason": (
                "Family slices behave differently; a single global factorized posterior "
                "averages incompatible relation geometry regimes."
            ),
            "candidate_methods": [
                "family-conditioned logistic calibration",
                "mixture-of-experts with relation-family gate",
                "hierarchical Bayesian/logistic calibration with shared global prior",
            ],
        },
        {
            "priority": 2,
            "name": "residual_correction_over_semantic_plus_geometry",
            "reason": (
                "Semantic+geometry is the strongest simple baseline, so the upgraded model "
                "should learn only a residual reliability correction instead of replacing it."
            ),
            "candidate_methods": [
                "calibrated residual model",
                "stacked logistic meta-calibrator",
                "isotonic or beta calibration on base posterior bins",
            ],
        },
        {
            "priority": 3,
            "name": "uncertainty_gated_geometry_use",
            "reason": (
                "Geometry-only is weak globally but can help in selected regimes; geometry "
                "should be gated by family, coverage, disagreement, and confidence."
            ),
            "candidate_methods": [
                "soft gating over semantic confidence and coverage",
                "abstention-aware reliability posterior",
                "monotonic GBDT-style combiner if sample size increases",
            ],
        },
    ]

    return {
        "schema_version": "h002_full_train_independent_controlled_error_analysis_summary_v0",
        "status": "full_train_independent_controlled_error_analysis_ready_for_combiner_design",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "smoke_dir": smoke.rel_path(DEFAULT_SMOKE_DIR),
            "split_eval": SPLIT_EVAL,
            "primary_view": PRIMARY_VIEW,
            "reference_view": REFERENCE_VIEW,
            "upstream_smoke_status": smoke_summary.get("status"),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "label_source": "codex_ver_full_train_independent_visible_surface_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "hidden_metadata_as_model_input": False,
            "hidden_metadata_posthoc_diagnostic_only": True,
            "trains_new_combiner": False,
            "model_selection_claim_allowed": False,
        },
        "overall": {
            "rows": len(error_rows),
            "positive": sum(int(row["target"]) for row in error_rows),
            "negative": len(error_rows) - sum(int(row["target"]) for row in error_rows),
            "correctness_case_counts": dict(sorted(case_counts.items())),
            "brier_case_counts": dict(sorted(brier_counts.items())),
            "mean_brier_delta_factorized_minus_sg": sum(
                safe_float(row["brier_delta_factorized_minus_sg"]) for row in error_rows
            )
            / len(error_rows),
            "mean_nll_delta_factorized_minus_sg": sum(
                safe_float(row["nll_delta_factorized_minus_sg"]) for row in error_rows
            )
            / len(error_rows),
            "mean_abs_error_delta_factorized_minus_sg": sum(
                safe_float(row["abs_error_delta_factorized_minus_sg"]) for row in error_rows
            )
            / len(error_rows),
        },
        "view_metrics": view_metrics,
        "slice_errors": slice_rows,
        "feature_summary": feature_summary(error_rows),
        "diagnosis": diagnosis,
        "combiner_recommendation": combiner_recommendation,
        "next_todo": "full_train_independent_combiner_upgrade_design",
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def flatten_metric_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return rows


def write_report(path: Path, summary: dict[str, Any]) -> None:
    view_metrics = summary["view_metrics"]
    family_rows = [row for row in summary["slice_errors"] if row["slice_name"] == "predicate_family"]
    direction_rows = [row for row in summary["slice_errors"] if row["slice_name"] == "direction_bin"]
    lines = [
        "# H002 Full Train Independent Controlled Error Analysis",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only post-hoc analysis on the controlled posterior smoke output.",
        "- No validation/test rows are used.",
        "- No new combiner is trained here.",
        "- Hidden audit metadata is post-hoc diagnostic only, not model input.",
        "- Labels are Codex bootstrap labels, not human-confirmed paper evidence.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Overall",
        "",
        "| Rows | Positive | Negative | Mean Brier Delta F-SG | Mean NLL Delta F-SG | Mean AbsErr Delta F-SG |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| {summary['overall']['rows']} | {summary['overall']['positive']} | "
            f"{summary['overall']['negative']} | "
            f"{fmt(summary['overall']['mean_brier_delta_factorized_minus_sg'])} | "
            f"{fmt(summary['overall']['mean_nll_delta_factorized_minus_sg'])} | "
            f"{fmt(summary['overall']['mean_abs_error_delta_factorized_minus_sg'])} |"
        ),
        "",
        "Correctness cases:",
        "",
    ]
    for key, value in summary["overall"]["correctness_case_counts"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(
        [
            "",
            "## View Metrics",
            "",
            "| View | AUROC | AUPRC | Brier | Accuracy |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in view_metrics:
        lines.append(
            f"| `{row['view']}` | {fmt(row['auroc'])} | {fmt(row['auprc'])} | "
            f"{fmt(row['brier'])} | {fmt(row['accuracy_at_0_5'])} |"
        )
    lines.extend(
        [
            "",
            "## Family Slices",
            "",
            "| Family | Rows | Pos | Neg | Delta AUPRC F-SG | Mean Brier Delta F-SG | F Wrong SG Correct | F Correct SG Wrong |",
            "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in family_rows:
        lines.append(
            f"| `{row['slice_value']}` | {row['rows']} | {row['positive']} | {row['negative']} | "
            f"{fmt(row['delta_auprc_factorized_minus_sg'])} | "
            f"{fmt(row['mean_brier_delta_factorized_minus_sg'])} | "
            f"{row['factorized_wrong_sg_correct']} | {row['factorized_correct_sg_wrong']} |"
        )
    lines.extend(
        [
            "",
            "## Direction Slices",
            "",
            "| Direction | Rows | Pos | Neg | Delta AUPRC F-SG | Mean Brier Delta F-SG |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in direction_rows:
        lines.append(
            f"| `{row['slice_value']}` | {row['rows']} | {row['positive']} | {row['negative']} | "
            f"{fmt(row['delta_auprc_factorized_minus_sg'])} | "
            f"{fmt(row['mean_brier_delta_factorized_minus_sg'])} |"
        )
    lines.extend(
        [
            "",
            "## Diagnosis",
            "",
        ]
    )
    for item in summary["diagnosis"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Combiner Implication", ""])
    for item in summary["combiner_recommendation"]:
        lines.append(f"{item['priority']}. `{item['name']}`: {item['reason']}")
    lines.extend(["", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_outputs(
    output_dir: Path,
    summary: dict[str, Any],
    error_rows: list[dict[str, Any]],
    *,
    top_k: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_jsonl(output_dir / "row_errors.jsonl", error_rows)
    smoke.write_jsonl(
        output_dir / "top_factorized_losses.jsonl",
        sorted(error_rows, key=lambda row: safe_float(row["brier_delta_factorized_minus_sg"]), reverse=True)[:top_k],
    )
    smoke.write_jsonl(
        output_dir / "top_factorized_wins.jsonl",
        sorted(error_rows, key=lambda row: safe_float(row["brier_delta_factorized_minus_sg"]))[:top_k],
    )
    write_csv(
        output_dir / "view_metrics.csv",
        flatten_metric_rows(summary["view_metrics"]),
        [
            "view",
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
        output_dir / "slice_errors.csv",
        summary["slice_errors"],
        [
            "slice_name",
            "slice_value",
            "rows",
            "positive",
            "negative",
            "mean_semantic_score_norm",
            "mean_p_geom_valid",
            "mean_absolute_disagreement",
            "factorized_correct_sg_wrong",
            "factorized_wrong_sg_correct",
            "both_correct",
            "both_wrong",
            "factorized_brier_better_rows",
            "sg_brier_better_rows",
            "mean_brier_delta_factorized_minus_sg",
            "mean_nll_delta_factorized_minus_sg",
            "mean_abs_error_delta_factorized_minus_sg",
            "mean_prob_delta_factorized_minus_sg",
            "factorized_auroc",
            "sg_auroc",
            "delta_auroc_factorized_minus_sg",
            "factorized_auprc",
            "sg_auprc",
            "delta_auprc_factorized_minus_sg",
            "factorized_brier",
            "sg_brier",
            "delta_brier_metric_factorized_minus_sg",
        ],
    )
    write_csv(
        output_dir / "feature_summary.csv",
        summary["feature_summary"],
        ["feature", "positive_mean", "negative_mean", "positive_minus_negative"],
    )
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    smoke_dir = smoke.as_abs(args.smoke_dir)
    output_dir = smoke.as_abs(args.output_dir)
    smoke_summary = read_json(smoke_dir / "summary.json")
    rows = smoke.read_jsonl(smoke_dir / "controlled_posterior_rows.jsonl")
    predictions = load_predictions(smoke_dir)
    error_rows = build_error_rows(rows, predictions)
    summary = summarize(error_rows, smoke_summary)
    summary["input"]["smoke_dir"] = smoke.rel_path(smoke_dir)
    summary["output_dir"] = smoke.rel_path(output_dir)
    write_outputs(output_dir, summary, error_rows, top_k=args.top_k)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    overall = summary["overall"]
    print(
        "status={status} rows={rows} validation_used={validation_used} "
        "f_wrong_sg_correct={f_wrong_sg_correct} f_correct_sg_wrong={f_correct_sg_wrong} "
        "mean_brier_delta={mean_brier_delta:.4f} next={next_todo}".format(
            status=summary["status"],
            rows=overall["rows"],
            validation_used=summary["boundary"]["validation_usage"],
            f_wrong_sg_correct=overall["correctness_case_counts"].get("factorized_wrong_sg_correct", 0),
            f_correct_sg_wrong=overall["correctness_case_counts"].get("factorized_correct_sg_wrong", 0),
            mean_brier_delta=overall["mean_brier_delta_factorized_minus_sg"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
