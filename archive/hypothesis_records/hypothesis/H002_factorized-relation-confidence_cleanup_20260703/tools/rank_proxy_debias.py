#!/usr/bin/env python3
"""Rank-proxy debias check for H002 controlled posterior."""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import controlled_posterior_smoke as controlled
import factor_smoke as smoke
import grouped_control_smoke as grouped


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_INPUT_DIR = RGA_ROOT / "controlled_posterior_smoke_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "rank_proxy_debias_codex_real_assumption"

TARGET_ROW_FILES = {
    "mined_controlled_codex_ver": "mined_controlled_codex_ver_rows.jsonl",
    "combined_controlled_codex_ver": "combined_controlled_codex_ver_rows.jsonl",
}

RANK_KEYS = {
    "rank_in_context",
    "predicate_rank_for_pair",
    "semantic_score_norm",
    "top100_semantic",
    "top50_semantic",
    "top100_and_unsatisfied",
    "tail_gt100_and_satisfied",
}

RANK_DERIVED_UNCERTAINTY_KEYS = {
    "absolute_disagreement",
    "semantic_geometry_disagreement_score",
    "semantic_score_norm_minus_p_geom_valid",
    "underconfidence_score",
}

DIRECT_IDENTITY_KEYS = {
    "predicate_family",
    "predicate_label",
    "source_id",
    "coverage_state",
    "geometry_status",
}

VIEWS = [
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
    "negative_rank_only",
    "semantic_plus_geometry_no_rank",
    "factorized_no_rank",
    "disagreement_only",
    "negative_rank_plus_semantic_geometry_no_rank",
    "negative_rank_plus_factorized_no_rank",
    "negative_rank_plus_disagreement",
    "geometry_continuous_only",
    "semantic_raw_only",
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


def negative_rank_feature(features: dict[str, Any]) -> dict[str, float]:
    semantic_norm = smoke.safe_float(features.get("semantic_score_norm"), 0.0)
    return {"negative_semantic_score_norm": 1.0 - semantic_norm}


def drop_keys(features: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    return {key: value for key, value in features.items() if key not in keys}


def keep_keys(features: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    return {key: features.get(key) for key in sorted(keys) if key in features}


def add_rank_debias_views(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    rank_and_identity = RANK_KEYS | DIRECT_IDENTITY_KEYS
    rank_derived_and_identity = RANK_KEYS | RANK_DERIVED_UNCERTAINTY_KEYS | DIRECT_IDENTITY_KEYS
    for row in rows:
        copied = deepcopy(row)
        inputs = copied["baseline_inputs"]
        sg = inputs["semantic_plus_geometry"]
        factorized = inputs["factorized_reliability_posterior"]
        sg_no_rank = drop_keys(sg, rank_and_identity)
        factorized_no_rank = drop_keys(factorized, rank_derived_and_identity)
        disagreement = keep_keys(factorized, RANK_DERIVED_UNCERTAINTY_KEYS)
        negative_rank = negative_rank_feature(factorized)
        inputs["negative_rank_only"] = negative_rank
        inputs["semantic_plus_geometry_no_rank"] = sg_no_rank
        inputs["factorized_no_rank"] = factorized_no_rank
        inputs["disagreement_only"] = disagreement
        inputs["negative_rank_plus_semantic_geometry_no_rank"] = {**negative_rank, **sg_no_rank}
        inputs["negative_rank_plus_factorized_no_rank"] = {**negative_rank, **factorized_no_rank}
        inputs["negative_rank_plus_disagreement"] = {**negative_rank, **disagreement}
        inputs["geometry_continuous_only"] = {
            key: factorized.get(key)
            for key in [
                "consistency_score",
                "geometry_available",
                "geometry_checkable",
                "geometry_residual_proxy",
                "p_geom_invalid",
                "p_geom_valid_available",
                "p_geom_valid_imputed_neutral",
            ]
            if key in factorized
        }
        inputs["semantic_raw_only"] = {"semantic_score_raw": factorized.get("semantic_score_raw")}
        output.append(copied)
    return output


def metric_record(target_mode: str, view: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": "rank_debias",
        "target_mode": target_mode,
        "split_eval": "train_internal_grouped_by_scan",
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


def numeric_pass(delta: dict[str, Any]) -> bool:
    auroc = delta.get("auroc")
    auprc = delta.get("auprc")
    brier = delta.get("brier")
    auroc_ok = auroc is None or auroc >= -0.02
    auprc_ok = auprc is not None and auprc >= 0.03
    brier_ok = brier is not None and brier <= -0.02
    return auroc_ok and (auprc_ok or brier_ok)


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Rank Proxy Debias",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage check.",
        "- `(codex_ver)` is treated as real label by user-directed assumption.",
        "- Folds are grouped by `scan_id`.",
        "- No validation/test rows are used.",
        "- `V_mv_e` is not used as model input.",
        "",
        "## Views",
        "",
        "| Target | View | AUROC | AUPRC | Brier | ECE-5 |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["metric_rows"]:
        metrics = row["metrics"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['name']}` | {fmt(metrics['auroc'])} | "
            f"{fmt(metrics['auprc'])} | {fmt(metrics['brier'])} | {fmt(metrics['ece_5bin'])} |"
        )
    lines.extend(
        [
            "",
            "## Key Comparisons",
            "",
            "| Target | Left | Right | Delta AUROC | Delta AUPRC | Delta Brier | Numeric pass |",
            "| --- | --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    pass_by_key = {
        (item["target_mode"], item["left"], item["right"]): numeric_pass(item["delta"])
        for item in summary["comparisons"]
    }
    for item in summary["comparisons"]:
        delta = item["delta"]
        passed = pass_by_key[(item["target_mode"], item["left"], item["right"])]
        lines.append(
            f"| `{item['target_mode']}` | `{item['left']}` | `{item['right']}` | "
            f"{fmt(delta['auroc'])} | {fmt(delta['auprc'])} | {fmt(delta['brier'])} | `{passed}` |"
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


def write_outputs(output_dir: Path, summary: dict[str, Any]) -> None:
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
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_dir = smoke.as_abs(args.input_dir)
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    metric_rows = []
    feature_summaries: dict[str, Any] = {}
    target_summaries: dict[str, Any] = {}

    for target_mode, filename in TARGET_ROW_FILES.items():
        rows = add_rank_debias_views(smoke.read_jsonl(input_dir / filename))
        target_summaries[target_mode] = controlled.target_counts(rows)
        for view in VIEWS:
            probs, feature_summary = grouped.train_predict_grouped(
                rows,
                view,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            feature_summaries[f"{target_mode}:{view}"] = feature_summary
            metric_rows.append(metric_record(target_mode, view, rows, probs))
            pred_path = output_dir / f"predictions_{target_mode}_grouped_{view}.jsonl"
            smoke.write_jsonl(
                pred_path,
                smoke.build_prediction_rows(
                    rows,
                    target_mode,
                    "train_internal_grouped_by_scan",
                    view,
                    probs,
                ),
            )

    comparisons = []
    for target_mode in TARGET_ROW_FILES:
        comparisons.extend(
            [
                comparison(metric_rows, target_mode, "factorized_reliability_posterior", "negative_rank_only"),
                comparison(metric_rows, target_mode, "factorized_no_rank", "semantic_plus_geometry_no_rank"),
                comparison(metric_rows, target_mode, "negative_rank_plus_factorized_no_rank", "negative_rank_only"),
                comparison(metric_rows, target_mode, "negative_rank_plus_semantic_geometry_no_rank", "negative_rank_only"),
                comparison(metric_rows, target_mode, "negative_rank_plus_disagreement", "negative_rank_only"),
                comparison(metric_rows, target_mode, "factorized_no_rank", "geometry_continuous_only"),
                comparison(metric_rows, target_mode, "disagreement_only", "negative_rank_only"),
            ]
        )

    rank_plus_passes = [
        item for item in comparisons
        if item["left"] == "negative_rank_plus_factorized_no_rank"
        and item["right"] == "negative_rank_only"
        and numeric_pass(item["delta"])
    ]
    full_beats_rank = [
        item for item in comparisons
        if item["left"] == "factorized_reliability_posterior"
        and item["right"] == "negative_rank_only"
        and numeric_pass(item["delta"])
    ]
    if full_beats_rank and rank_plus_passes:
        decision = (
            "Rank-debias check provides positive support: factorized evidence beats "
            "negative-rank proxy and non-rank features add signal beyond rank."
        )
        status = "rank_debias_support"
    elif rank_plus_passes:
        decision = (
            "Rank-debias check is mixed: non-rank evidence adds signal beyond rank, "
            "but the full factorized posterior does not consistently beat the rank proxy."
        )
        status = "rank_debias_mixed"
    else:
        decision = (
            "Rank-debias check does not support a factorized-posterior method claim yet. "
            "The current controlled-label signal is still explainable by semantic rank / "
            "underconfidence proxy, and non-rank evidence does not add enough over "
            "negative_rank_only under scan-grouped CV."
        )
        status = "rank_proxy_not_debiased"

    summary = {
        "schema_version": "h002_rank_proxy_debias_v0",
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
            "validation_usage": False,
            "test_usage": False,
            "vmv_model_input_allowed": False,
        },
        "rank_debias_policy": {
            "dropped_rank_keys": sorted(RANK_KEYS),
            "dropped_rank_derived_uncertainty_keys": sorted(RANK_DERIVED_UNCERTAINTY_KEYS),
            "dropped_direct_identity_keys": sorted(DIRECT_IDENTITY_KEYS),
            "primary_rank_proxy": "negative_rank_only",
        },
        "target_summaries": target_summaries,
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "feature_summaries": feature_summaries,
        "decision": decision,
    }
    write_outputs(output_dir, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    brief = []
    for item in summary["comparisons"]:
        if item["left"] == "negative_rank_plus_factorized_no_rank" and item["right"] == "negative_rank_only":
            delta = item["delta"]
            brief.append(f"{item['target_mode']}:rankplus_d_auprc={delta['auprc']:.4f}:rankplus_d_brier={delta['brier']:.4f}")
    print(
        f"status={summary['status']} metrics={len(summary['metric_rows'])} "
        f"validation_used={summary['hyperparameters']['uses_validation_rows']} "
        + " ".join(brief)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
