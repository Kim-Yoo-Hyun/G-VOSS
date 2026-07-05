#!/usr/bin/env python3
"""Scan-grouped controlled posterior smoke for H002."""

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
import redesigned_target_smoke as redesigned


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_INPUT_DIR = RGA_ROOT / "controlled_posterior_smoke_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "grouped_control_smoke_codex_real_assumption"

TARGET_ROW_FILES = {
    "mined_controlled_codex_ver": "mined_controlled_codex_ver_rows.jsonl",
    "combined_controlled_codex_ver": "combined_controlled_codex_ver_rows.jsonl",
}

MAIN_VIEWS = [
    "semantic_only",
    "geometry_only",
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
]

FACTOR_VIEWS = [
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
    "p_geom_valid_only",
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
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def add_factor_and_proxy_views(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    for row in rows:
        copied = deepcopy(row)
        baseline_inputs = copied["baseline_inputs"]
        sg = dict(baseline_inputs["semantic_plus_geometry"])
        factorized = baseline_inputs["factorized_reliability_posterior"]
        coverage = {key: factorized.get(key) for key in sorted(COVERAGE_KEYS) if key in factorized}
        uncertainty = {key: factorized.get(key) for key in sorted(UNCERTAINTY_KEYS) if key in factorized}
        baseline_inputs["semantic_geometry_coverage"] = {**sg, **coverage}
        baseline_inputs["semantic_geometry_uncertainty"] = {**sg, **uncertainty}
        baseline_inputs["semantic_geometry_coverage_uncertainty"] = {**sg, **coverage, **uncertainty}
        semantic_norm = smoke.safe_float(factorized.get("semantic_score_norm"), 0.0)
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
        baseline_inputs["p_geom_valid_only"] = {
            "p_geom_valid_imputed_neutral": factorized.get("p_geom_valid_imputed_neutral"),
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
        _, indices = item
        pos = sum(smoke.target_y(rows[idx]) for idx in indices)
        neg = len(indices) - pos
        return (abs(pos - neg), len(indices), item[0])

    for group, indices in sorted(groups.items(), key=group_key, reverse=True):
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
    for test_indices in fold_indices:
        test_set = set(test_indices)
        train_rows = [row for idx, row in enumerate(rows) if idx not in test_set]
        test_rows = [rows[idx] for idx in test_indices]
        train_labels = {smoke.target_y(row) for row in train_rows}
        if train_labels != {0, 1}:
            raise ValueError(f"grouped fold has single-class train set for {baseline}: {train_labels}")
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
        "feature_count_min": min(feature_counts),
        "feature_count_max": max(feature_counts),
        "group_key": "scan_id",
    }


def metric_record(kind: str, target_mode: str, name: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": kind,
        "target_mode": target_mode,
        "split_eval": "train_internal_grouped_by_scan",
        "name": name,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


def comparison(metric_rows: list[dict[str, Any]], target_mode: str, left: str, right: str) -> dict[str, Any]:
    by_name = {
        row["name"]: row["metrics"]
        for row in metric_rows
        if row["target_mode"] == target_mode
        and row["split_eval"] == "train_internal_grouped_by_scan"
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


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Grouped Control Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage check.",
        "- `(codex_ver)` is treated as real label by user-directed assumption.",
        "- No validation/test rows are used.",
        "- Folds are grouped by `scan_id`.",
        "- `V_mv_e` is not used as model input.",
        "",
        "## Main Views",
        "",
        "| Target | View | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["metric_rows"]:
        if row["kind"] != "main":
            continue
        metrics = row["metrics"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['name']}` | {fmt(metrics['auroc'])} | "
            f"{fmt(metrics['auprc'])} | {fmt(metrics['brier'])} | "
            f"{fmt(metrics['ece_5bin'])} | {fmt(metrics['accuracy_at_0_5'])} |"
        )
    lines.extend(
        [
            "",
            "## Factor Ablations",
            "",
            "| Target | View | AUROC | AUPRC | Brier |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["kind"] != "factor_ablation":
            continue
        metrics = row["metrics"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['name']}` | {fmt(metrics['auroc'])} | "
            f"{fmt(metrics['auprc'])} | {fmt(metrics['brier'])} |"
        )
    lines.extend(
        [
            "",
            "## Proxy / Control Views",
            "",
            "| Target | Kind | View | AUROC | AUPRC | Brier |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["kind"] not in {"control", "proxy"}:
            continue
        metrics = row["metrics"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['kind']}` | `{row['name']}` | "
            f"{fmt(metrics['auroc'])} | {fmt(metrics['auprc'])} | {fmt(metrics['brier'])} |"
        )
    lines.extend(
        [
            "",
            "## Deltas",
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
        rows = add_factor_and_proxy_views(smoke.read_jsonl(input_dir / filename))
        target_summaries[target_mode] = controlled.target_counts(rows)
        view_sets = [
            ("main", MAIN_VIEWS, rows),
            ("factor_ablation", FACTOR_VIEWS, rows),
            ("proxy", PROXY_VIEWS, rows),
        ]
        control_rows_by_name = {}
        for view_name in CONTROL_VIEWS:
            view_rows, view_summary = redesigned.build_view_rows(rows, view_name)
            control_rows_by_name[view_name] = view_rows
            feature_summaries[f"{target_mode}:{view_name}:view"] = view_summary
        view_sets.append(("control", CONTROL_VIEWS, None))

        for kind, view_names, base_rows in view_sets:
            for view_name in view_names:
                current_rows = control_rows_by_name[view_name] if kind == "control" else base_rows
                if current_rows is None:
                    raise RuntimeError("missing rows")
                probs, feature_summary = train_predict_grouped(
                    current_rows,
                    view_name,
                    folds=args.folds,
                    epochs=args.epochs,
                    learning_rate=args.learning_rate,
                    l2=args.l2,
                )
                feature_summaries[f"{target_mode}:{view_name}:grouped"] = feature_summary
                metric_rows.append(metric_record(kind, target_mode, view_name, current_rows, probs))
                pred_path = output_dir / f"predictions_{target_mode}_grouped_{view_name}.jsonl"
                smoke.write_jsonl(
                    pred_path,
                    smoke.build_prediction_rows(
                        current_rows,
                        target_mode,
                        "train_internal_grouped_by_scan",
                        view_name,
                        probs,
                    ),
                )

    comparisons = []
    for target_mode in TARGET_ROW_FILES:
        comparisons.extend(
            [
                comparison(metric_rows, target_mode, "factorized_reliability_posterior", "semantic_plus_geometry"),
                comparison(metric_rows, target_mode, "semantic_geometry_coverage", "semantic_plus_geometry"),
                comparison(metric_rows, target_mode, "semantic_geometry_uncertainty", "semantic_plus_geometry"),
                comparison(metric_rows, target_mode, "semantic_geometry_coverage_uncertainty", "semantic_plus_geometry"),
                comparison(metric_rows, target_mode, "factorized_reliability_posterior", "rank_only"),
            ]
        )

    mined_delta = next(
        item for item in comparisons
        if item["target_mode"] == "mined_controlled_codex_ver"
        and item["left"] == "factorized_reliability_posterior"
        and item["right"] == "semantic_plus_geometry"
    )["delta"]
    combined_delta = next(
        item for item in comparisons
        if item["target_mode"] == "combined_controlled_codex_ver"
        and item["left"] == "factorized_reliability_posterior"
        and item["right"] == "semantic_plus_geometry"
    )["delta"]
    decision = (
        "Grouped scan-level smoke does not provide strong H002 posterior support yet. "
        "Treating codex_ver as real labels, factorized must retain a positive and "
        "stable advantage over semantic_plus_geometry under grouped folds and factor "
        "ablations. This remains unresolved until grouped deltas, factor ablations, "
        "proxy baselines, and calibration are jointly favorable."
    )
    summary = {
        "schema_version": "h002_grouped_control_smoke_v0",
        "status": "ready_grouped_control_smoke_codex_real_assumption",
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
        "target_summaries": target_summaries,
        "metric_rows": metric_rows,
        "comparisons": comparisons,
        "feature_summaries": feature_summaries,
        "quick_deltas": {
            "mined_factorized_minus_sg": mined_delta,
            "combined_factorized_minus_sg": combined_delta,
        },
        "decision": decision,
        "method_notes": {
            "grouped_cv_reference": "GroupKFold-style non-overlapping group evaluation by scan_id.",
            "calibration_reference": "Brier/ECE remain important because H002 is a reliability posterior.",
        },
    }
    write_outputs(output_dir, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    md = summary["quick_deltas"]["mined_factorized_minus_sg"]
    cd = summary["quick_deltas"]["combined_factorized_minus_sg"]
    print(
        f"status={summary['status']} metrics={len(summary['metric_rows'])} validation_used={summary['hyperparameters']['uses_validation_rows']} "
        f"mined_d_auprc={md['auprc']:.4f} mined_d_brier={md['brier']:.4f} "
        f"combined_d_auprc={cd['auprc']:.4f} combined_d_brier={cd['brier']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
