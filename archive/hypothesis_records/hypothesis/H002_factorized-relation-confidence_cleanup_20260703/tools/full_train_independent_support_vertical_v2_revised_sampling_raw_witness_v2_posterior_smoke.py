#!/usr/bin/env python3
"""Raw-witness v2 posterior smoke for revised all-label-ready H002 rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke
import full_train_independent_support_vertical_v2_revised_sampling_controlled_posterior_smoke as base


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INPUT_ROWS = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/posterior_ready_rows.jsonl"
)
DEFAULT_FEATURE_JOIN_SUMMARY = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/summary.json"
)
DEFAULT_INPUT_CONTRACT = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready/input_contract_v2.json"
)
DEFAULT_OUTPUT_DIR = (
    RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_all_label_ready"
)

TARGET_MODE = "rank_band_balanced_revised_sampling"

MAIN_VIEWS = [
    "semantic_only",
    "legacy_geometry_only",
    "semantic_plus_geometry",
    "raw_witness_only_v2",
    "semantic_plus_raw_witness_v2",
    "factorized_reliability_posterior_v2_linear",
    "factorized_reliability_posterior_v2_family_shrinkage",
]

CONTROL_VIEWS = [
    "raw_witness_shuffle_global",
    "raw_witness_shuffle_within_family",
    "wrong_pair_raw_witness",
    "family_only_offset",
    "no_family_local_normalization",
    "legacy_p_geom_only",
]

ABLATION_VIEWS = [
    "endpoint_type_ablation",
]

PROBE_NAMES = [
    "semantic_score_norm",
    "semantic_rank_inverse",
    "p_geom_valid",
    "consistency_score",
    "strong_raw_witness_score",
    "weak_raw_witness_score",
    "support_contact_gate",
    "relative_vertical_gate",
    "support_gap_closeness",
    "support_distance_closeness",
    "support_iou_xy",
    "vertical_sign_agreement",
    "raw_witness_missing_flag",
]

COMPARISON_PAIRS = [
    ("factorized_reliability_posterior_v2_family_shrinkage", "semantic_plus_geometry"),
    ("factorized_reliability_posterior_v2_family_shrinkage", "factorized_reliability_posterior_v2_linear"),
    ("factorized_reliability_posterior_v2_family_shrinkage", "semantic_plus_raw_witness_v2"),
    ("factorized_reliability_posterior_v2_linear", "semantic_plus_geometry"),
    ("semantic_plus_raw_witness_v2", "semantic_plus_geometry"),
    ("raw_witness_only_v2", "legacy_geometry_only"),
    ("legacy_p_geom_only", "legacy_geometry_only"),
    ("factorized_reliability_posterior_v2_family_shrinkage", "raw_witness_shuffle_global"),
    ("factorized_reliability_posterior_v2_family_shrinkage", "raw_witness_shuffle_within_family"),
    ("factorized_reliability_posterior_v2_family_shrinkage", "wrong_pair_raw_witness"),
    ("factorized_reliability_posterior_v2_family_shrinkage", "family_only_offset"),
    ("factorized_reliability_posterior_v2_family_shrinkage", "no_family_local_normalization"),
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


def metric_record(kind: str, split_eval: str, name: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": kind,
        "target_mode": TARGET_MODE,
        "split_eval": split_eval,
        "name": name,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


def validate_inputs(
    rows: list[dict[str, Any]],
    feature_join_summary: dict[str, Any],
    input_contract: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    boundary = feature_join_summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "review_fields_as_model_input",
        "hidden_metadata_as_model_input",
        "target_labels_as_model_input",
        "packet_paths_as_model_input",
        "multi_view_as_model_input",
        "geometry_status_as_model_input",
        "free_family_or_predicate_categorical_input",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "feature_join_boundary_not_false", "field": key, "value": boundary.get(key)})
    if boundary.get("raw_witness_as_model_input") is not True:
        errors.append({"error_type": "raw_witness_input_not_enabled", "value": boundary.get("raw_witness_as_model_input")})
    if feature_join_summary.get("validation_error_count") != 0:
        errors.append(
            {
                "error_type": "feature_join_validation_errors_present",
                "count": feature_join_summary.get("validation_error_count"),
            }
        )
    if feature_join_summary.get("feature_leakage_count") != 0:
        errors.append(
            {
                "error_type": "feature_join_leakage_present",
                "count": feature_join_summary.get("feature_leakage_count"),
            }
        )

    expected_views = set(MAIN_VIEWS + CONTROL_VIEWS + ABLATION_VIEWS)
    contract_views = set(input_contract.get("main_views", [])) | set(input_contract.get("control_views", []))
    missing_contract_views = sorted(expected_views - contract_views)
    if missing_contract_views:
        errors.append({"error_type": "input_contract_missing_expected_views", "views": missing_contract_views})

    forbidden_roots = [
        "audit_only_user_confirmed_review_fields",
        "hidden_audit_metadata_post_label_only",
        "audit_packet_paths_not_model_input",
    ]
    for row_number, row in enumerate(rows, start=1):
        if row.get("record_type") != "h002_support_vertical_v2_revised_sampling_raw_witness_posterior_ready_row":
            errors.append(
                {"error_type": "unexpected_record_type", "row_number": row_number, "record_type": row.get("record_type")}
            )
        row_boundary = row.get("provenance", {})
        for key in expected_false:
            if row_boundary.get(key) is not False:
                errors.append({"error_type": "row_boundary_not_false", "row_number": row_number, "field": key})
        if row_boundary.get("raw_witness_as_model_input") is not True:
            errors.append({"error_type": "row_raw_witness_input_not_true", "row_number": row_number})
        if set(row.get("baseline_inputs", {})) != expected_views:
            errors.append(
                {
                    "error_type": "row_view_set_mismatch",
                    "row_number": row_number,
                    "missing": sorted(expected_views - set(row.get("baseline_inputs", {}))),
                    "extra": sorted(set(row.get("baseline_inputs", {})) - expected_views),
                }
            )
        for field in forbidden_roots:
            if field in row:
                errors.append({"error_type": "forbidden_root_present", "row_number": row_number, "field": field})
    return errors


def probe_scores(rows: list[dict[str, Any]], probe_name: str) -> list[float]:
    outputs = []
    for row in rows:
        semantic = row["baseline_inputs"]["semantic_only"]
        legacy_geometry = row["baseline_inputs"]["legacy_geometry_only"]
        raw_witness = row["baseline_inputs"]["raw_witness_only_v2"]
        if probe_name == "semantic_score_norm":
            score = smoke.safe_float(semantic.get("semantic_score_norm"))
        elif probe_name == "semantic_rank_inverse":
            score = smoke.safe_float(semantic.get("semantic_rank_inverse"))
        elif probe_name == "p_geom_valid":
            score = smoke.safe_float(legacy_geometry.get("p_geom_valid"))
        elif probe_name == "consistency_score":
            score = smoke.safe_float(legacy_geometry.get("consistency_score"))
        elif probe_name == "strong_raw_witness_score":
            score = smoke.safe_float(raw_witness.get("strong_raw_witness_score"))
        elif probe_name == "weak_raw_witness_score":
            score = smoke.safe_float(raw_witness.get("weak_raw_witness_score"))
        elif probe_name == "support_contact_gate":
            score = smoke.safe_float(raw_witness.get("support_contact_gate"))
        elif probe_name == "relative_vertical_gate":
            score = smoke.safe_float(raw_witness.get("relative_vertical_gate"))
        elif probe_name == "support_gap_closeness":
            score = smoke.safe_float(raw_witness.get("support_gap_closeness"))
        elif probe_name == "support_distance_closeness":
            score = smoke.safe_float(raw_witness.get("support_distance_closeness"))
        elif probe_name == "support_iou_xy":
            score = smoke.safe_float(raw_witness.get("support_iou_xy"))
        elif probe_name == "vertical_sign_agreement":
            score = smoke.safe_float(raw_witness.get("vertical_sign_agreement"))
        elif probe_name == "raw_witness_missing_flag":
            score = 1.0 - smoke.safe_float(raw_witness.get("raw_witness_missing_flag"))
        else:
            raise ValueError(f"unsupported probe: {probe_name}")
        outputs.append(score)
    return outputs


def pick_delta(comparisons: list[dict[str, Any]], split_eval: str, left: str, right: str) -> dict[str, Any]:
    for item in comparisons:
        if item["split_eval"] == split_eval and item["left"] == left and item["right"] == right:
            return item["delta"]
    raise KeyError(f"missing comparison {split_eval}: {left} vs {right}")


def family_delta_rows(family_slices: list[dict[str, Any]], left: str, right: str) -> list[dict[str, Any]]:
    by_key = {(row["predicate_family"], row["view"]): row for row in family_slices}
    outputs = []
    for family in sorted({row["predicate_family"] for row in family_slices}):
        left_row = by_key.get((family, left))
        right_row = by_key.get((family, right))
        if left_row is None or right_row is None:
            continue
        left_metrics = left_row["metrics"]
        right_metrics = right_row["metrics"]
        outputs.append(
            {
                "predicate_family": family,
                "left": left,
                "right": right,
                "delta_auroc": (
                    left_metrics.get("auroc") - right_metrics.get("auroc")
                    if left_metrics.get("auroc") is not None and right_metrics.get("auroc") is not None
                    else None
                ),
                "delta_auprc": (
                    left_metrics.get("auprc") - right_metrics.get("auprc")
                    if left_metrics.get("auprc") is not None and right_metrics.get("auprc") is not None
                    else None
                ),
                "delta_brier": (
                    left_metrics.get("brier") - right_metrics.get("brier")
                    if left_metrics.get("brier") is not None and right_metrics.get("brier") is not None
                    else None
                ),
            }
        )
    return outputs


def classify_status(validation_errors: list[dict[str, Any]], quick_deltas: dict[str, dict[str, Any]]) -> tuple[str, str, str]:
    if validation_errors:
        return (
            "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_input_errors",
            "Fix raw-witness v2 posterior smoke input contract errors before interpreting metrics.",
            "fix_revised_sampling_all_label_ready_raw_witness_v2_posterior_smoke_inputs",
        )

    shrinkage_vs_sg = quick_deltas["grouped_shrinkage_minus_semantic_plus_geometry"]
    shrinkage_vs_global_shuffle = quick_deltas["grouped_shrinkage_minus_raw_witness_shuffle_global"]
    shrinkage_vs_wrong_pair = quick_deltas["grouped_shrinkage_minus_wrong_pair_raw_witness"]
    semantic_raw_vs_sg = quick_deltas["grouped_semantic_plus_raw_witness_v2_minus_semantic_plus_geometry"]
    raw_vs_legacy = quick_deltas["grouped_raw_witness_only_v2_minus_legacy_geometry_only"]

    positive_factorized = (
        shrinkage_vs_sg.get("auprc") is not None
        and shrinkage_vs_sg["auprc"] >= 0.02
        and shrinkage_vs_sg.get("brier") is not None
        and shrinkage_vs_sg["brier"] <= 0.0
        and shrinkage_vs_global_shuffle.get("auprc") is not None
        and shrinkage_vs_global_shuffle["auprc"] >= 0.01
        and shrinkage_vs_wrong_pair.get("auprc") is not None
        and shrinkage_vs_wrong_pair["auprc"] >= 0.01
    )
    raw_witness_partial = (
        semantic_raw_vs_sg.get("auprc") is not None
        and semantic_raw_vs_sg["auprc"] >= 0.01
        and raw_vs_legacy.get("auprc") is not None
        and raw_vs_legacy["auprc"] >= 0.01
    )

    if positive_factorized:
        return (
            "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_positive_smoke",
            (
                "Typed raw witness improves the grouped factorized posterior over the legacy semantic+geometry baseline, "
                "and the global/wrong-pair controls reduce the gain. Treat this as hypothesis-stage evidence only."
            ),
            "revised_sampling_all_label_ready_raw_witness_v2_error_analysis",
        )
    if raw_witness_partial:
        return (
            "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_partial_raw_signal",
            (
                "Typed raw witness shows some signal over legacy geometry, but the full shrinkage posterior does not pass "
                "the factorized positive-signal gate. Inspect family and row-level errors before changing combiners."
            ),
            "revised_sampling_all_label_ready_raw_witness_v2_error_analysis",
        )
    return (
        "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_no_strong_signal",
        (
            "The v2 raw-witness smoke is executable, but it does not establish a strong grouped-fold advantage over the "
            "legacy semantic+geometry baseline under required controls. Diagnose feature/target/family failures before "
            "claiming posterior improvement."
        ),
        "revised_sampling_all_label_ready_raw_witness_v2_error_analysis",
    )


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Raw-Witness V2 Posterior Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage posterior smoke.",
        "- No validation/test rows are used.",
        "- Active target slice is `rank_band_balanced_revised_sampling`.",
        "- Review fields, hidden audit metadata, target labels, packet paths, multi-view evidence, "
        "`geometry_status`, and free predicate/family categorical shortcuts are not model inputs.",
        "- Typed raw witness is allowed as model input because this is the v2 feature contract under test.",
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
    lines.extend(
        [
            "",
            "## Family Deltas",
            "",
            "| Family | Left | Right | Delta AUROC | Delta AUPRC | Delta Brier |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["family_deltas"]:
        lines.append(
            f"| `{row['predicate_family']}` | `{row['left']}` | `{row['right']}` | "
            f"{fmt(row['delta_auroc'])} | {fmt(row['delta_auprc'])} | {fmt(row['delta_brier'])} |"
        )
    lines.extend(["", "## Decision", "", summary["decision"], "", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any], rows: list[dict[str, Any]], predictions: list[dict[str, Any]]) -> None:
    base.write_json(output_dir / "summary.json", summary)
    base.write_jsonl(output_dir / "posterior_rows.jsonl", rows)
    base.write_jsonl(output_dir / "predictions.jsonl", predictions)
    base.write_jsonl(output_dir / "matched_pairs.jsonl", summary["matched_pairs"])
    base.write_csv(
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
    base.write_csv(
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
    base.write_csv(output_dir / "pairwise.csv", summary["pairwise_metrics"], ["view", "pairs", "pairwise_accuracy"])
    base.write_csv(
        output_dir / "family_deltas.csv",
        summary["family_deltas"],
        ["predicate_family", "left", "right", "delta_auroc", "delta_auprc", "delta_brier"],
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
    base.write_csv(
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
    rows = smoke.read_jsonl(args.input_rows)
    feature_join_summary = read_json(args.feature_join_summary)
    input_contract = read_json(args.input_contract)
    validation_errors = validate_inputs(rows, feature_join_summary, input_contract)

    metric_rows: list[dict[str, Any]] = []
    predictions: list[dict[str, Any]] = []
    feature_summaries: dict[str, Any] = {}
    score_by_view_grouped: dict[str, list[float]] = {}
    score_by_view_crossfit: dict[str, list[float]] = {}

    for kind, views in [("main", MAIN_VIEWS), ("control", CONTROL_VIEWS), ("ablation", ABLATION_VIEWS)]:
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
            grouped_probs, grouped_summary = base.train_predict_grouped(
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
            comparisons.append(base.comparison(metric_rows, split_eval, left, right))

    pairs = base.matched_pairs(rows)
    pairwise = base.pairwise_metrics(pairs, score_by_view_crossfit)
    family_slice_rows = base.family_slices(score_by_view_grouped, rows)
    family_deltas = []
    family_deltas.extend(
        family_delta_rows(
            family_slice_rows,
            "factorized_reliability_posterior_v2_family_shrinkage",
            "semantic_plus_geometry",
        )
    )
    family_deltas.extend(family_delta_rows(family_slice_rows, "semantic_plus_raw_witness_v2", "semantic_plus_geometry"))
    family_deltas.extend(family_delta_rows(family_slice_rows, "raw_witness_only_v2", "legacy_geometry_only"))

    quick_deltas = {
        "grouped_shrinkage_minus_semantic_plus_geometry": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "factorized_reliability_posterior_v2_family_shrinkage",
            "semantic_plus_geometry",
        ),
        "grouped_shrinkage_minus_linear": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "factorized_reliability_posterior_v2_family_shrinkage",
            "factorized_reliability_posterior_v2_linear",
        ),
        "grouped_shrinkage_minus_semantic_plus_raw_witness_v2": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "factorized_reliability_posterior_v2_family_shrinkage",
            "semantic_plus_raw_witness_v2",
        ),
        "grouped_linear_minus_semantic_plus_geometry": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "factorized_reliability_posterior_v2_linear",
            "semantic_plus_geometry",
        ),
        "grouped_semantic_plus_raw_witness_v2_minus_semantic_plus_geometry": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "semantic_plus_raw_witness_v2",
            "semantic_plus_geometry",
        ),
        "grouped_raw_witness_only_v2_minus_legacy_geometry_only": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "raw_witness_only_v2",
            "legacy_geometry_only",
        ),
        "grouped_shrinkage_minus_raw_witness_shuffle_global": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "factorized_reliability_posterior_v2_family_shrinkage",
            "raw_witness_shuffle_global",
        ),
        "grouped_shrinkage_minus_raw_witness_shuffle_within_family": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "factorized_reliability_posterior_v2_family_shrinkage",
            "raw_witness_shuffle_within_family",
        ),
        "grouped_shrinkage_minus_wrong_pair_raw_witness": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "factorized_reliability_posterior_v2_family_shrinkage",
            "wrong_pair_raw_witness",
        ),
        "grouped_shrinkage_minus_family_only_offset": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "factorized_reliability_posterior_v2_family_shrinkage",
            "family_only_offset",
        ),
        "grouped_shrinkage_minus_no_family_local_normalization": pick_delta(
            comparisons,
            "train_internal_grouped_by_scan",
            "factorized_reliability_posterior_v2_family_shrinkage",
            "no_family_local_normalization",
        ),
    }
    status, decision, next_todo = classify_status(validation_errors, quick_deltas)

    summary = {
        "schema_version": "h002_support_vertical_v2_revised_sampling_raw_witness_v2_posterior_smoke_summary_v1",
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
            "geometry_status_as_model_input": False,
            "raw_witness_as_model_input": True,
            "validation_usage": False,
            "test_usage": False,
        },
        "target_summary": target_summary(rows),
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "family_slices": family_slice_rows,
        "family_deltas": family_deltas,
        "matched_pairs": pairs,
        "pairwise_metrics": pairwise,
        "feature_summaries": feature_summaries,
        "input_contract": input_contract,
        "validation_errors": validation_errors,
        "quick_deltas": quick_deltas,
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
        "validation_used={validation_used} "
        "d_auprc_shrinkage_vs_sg={d_sg:.4f} d_brier_shrinkage_vs_sg={b_sg:.4f} "
        "d_auprc_sem_raw_vs_sg={d_sem_raw:.4f} d_auprc_raw_vs_legacy={d_raw:.4f} "
        "d_auprc_shrinkage_vs_shuffle={d_shuffle:.4f} d_auprc_shrinkage_vs_wrong_pair={d_wrong:.4f} "
        "next={next_todo}".format(
            status=summary["status"],
            rows=summary["target_summary"]["rows"],
            pos=summary["target_summary"]["positive"],
            neg=summary["target_summary"]["negative"],
            metrics=len(summary["metric_rows"]),
            validation_used=summary["hyperparameters"]["uses_validation_rows"],
            d_sg=deltas["grouped_shrinkage_minus_semantic_plus_geometry"]["auprc"],
            b_sg=deltas["grouped_shrinkage_minus_semantic_plus_geometry"]["brier"],
            d_sem_raw=deltas["grouped_semantic_plus_raw_witness_v2_minus_semantic_plus_geometry"]["auprc"],
            d_raw=deltas["grouped_raw_witness_only_v2_minus_legacy_geometry_only"]["auprc"],
            d_shuffle=deltas["grouped_shrinkage_minus_raw_witness_shuffle_global"]["auprc"],
            d_wrong=deltas["grouped_shrinkage_minus_wrong_pair_raw_witness"]["auprc"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
