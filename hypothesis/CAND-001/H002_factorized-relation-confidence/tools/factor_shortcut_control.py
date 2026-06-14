#!/usr/bin/env python3
"""Shortcut-controlled train-only H002 factor smoke."""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_DATASET_DIR = RGA_ROOT / "factor_dataset"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "factor_shortcut_control"

TARGET_FILES = {
    "strict": "strict_smoke.jsonl",
    "weak": "weak_smoke.jsonl",
}

BASELINE_SOURCE = "factorized_reliability_posterior"

DIRECT_RGA_SHORTCUT_KEYS = {
    "top100_and_unsatisfied",
    "tail_gt100_and_satisfied",
    "semantic_geometry_disagreement_score",
    "underconfidence_score",
    "absolute_disagreement",
    "semantic_score_norm_minus_p_geom_valid",
}

RANK_BUCKET_KEYS = {
    "rank_in_context",
    "predicate_rank_for_pair",
    "top50_semantic",
    "top100_semantic",
    "semantic_score_norm",
}

GEOMETRY_STATUS_KEYS = {
    "geometry_status",
    "geometry_status_satisfied",
    "geometry_status_unsatisfied",
    "geometry_status_uncertain",
    "geometry_status_unsupported",
    "geometry_status_is_uncertain",
    "geometry_status_is_unsupported",
}

CATEGORICAL_SEMANTIC_KEYS = {
    "predicate_label",
    "predicate_family",
    "source_id",
}

COVERAGE_STATUS_KEYS = {
    "coverage_state",
    "covered_checkable",
    "covered_and_uncertain",
    "predicate_family_supported",
    "unsupported_family",
    "missing_geometry",
}

CONTINUOUS_CORE_KEYS = {
    "semantic_score_raw",
    "p_geom_valid_imputed_neutral",
    "p_geom_invalid",
    "consistency_score",
    "geometry_residual_proxy",
    "p_geom_valid_available",
    "geometry_available",
    "geometry_checkable",
}

SEMANTIC_RAW_KEYS = {
    "semantic_score_raw",
}

GEOMETRY_CONTINUOUS_KEYS = {
    "p_geom_valid_imputed_neutral",
    "p_geom_invalid",
    "consistency_score",
    "geometry_residual_proxy",
    "p_geom_valid_available",
    "geometry_available",
    "geometry_checkable",
}

VIEW_SPECS = {
    "full_factorized": {
        "mode": "drop",
        "drop_keys": set(),
        "description": "Original factorized feature view from 27_factor_smoke.",
    },
    "drop_direct_rga_shortcuts": {
        "mode": "drop",
        "drop_keys": DIRECT_RGA_SHORTCUT_KEYS,
        "description": "Remove explicit RGA shortcut/interactions but keep rank and geometry status.",
    },
    "drop_direct_and_status": {
        "mode": "drop",
        "drop_keys": DIRECT_RGA_SHORTCUT_KEYS | GEOMETRY_STATUS_KEYS | COVERAGE_STATUS_KEYS,
        "description": "Remove direct shortcuts and deterministic geometry/coverage status fields.",
    },
    "drop_direct_status_rank": {
        "mode": "drop",
        "drop_keys": DIRECT_RGA_SHORTCUT_KEYS | GEOMETRY_STATUS_KEYS | COVERAGE_STATUS_KEYS | RANK_BUCKET_KEYS,
        "description": "Remove direct shortcuts, deterministic status, and semantic rank/top-K fields.",
    },
    "drop_direct_status_rank_category": {
        "mode": "drop",
        "drop_keys": (
            DIRECT_RGA_SHORTCUT_KEYS
            | GEOMETRY_STATUS_KEYS
            | COVERAGE_STATUS_KEYS
            | RANK_BUCKET_KEYS
            | CATEGORICAL_SEMANTIC_KEYS
        ),
        "description": "Remove shortcut, status, rank/top-K, predicate label/family/source categorical fields.",
    },
    "continuous_core": {
        "mode": "keep",
        "keep_keys": CONTINUOUS_CORE_KEYS,
        "description": "Use only continuous semantic raw score and continuous geometry evidence.",
    },
    "semantic_raw_only": {
        "mode": "keep",
        "keep_keys": SEMANTIC_RAW_KEYS,
        "description": "Use only source semantic raw confidence.",
    },
    "geometry_continuous_only": {
        "mode": "keep",
        "keep_keys": GEOMETRY_CONTINUOUS_KEYS,
        "description": "Use only continuous geometry evidence without deterministic geometry status.",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def filter_features(features: dict[str, Any], view_name: str) -> tuple[dict[str, Any], list[str]]:
    spec = VIEW_SPECS[view_name]
    if spec["mode"] == "drop":
        drop_keys = spec["drop_keys"]
        kept = {key: value for key, value in features.items() if key not in drop_keys}
        removed = sorted(key for key in features if key in drop_keys)
    elif spec["mode"] == "keep":
        keep_keys = spec["keep_keys"]
        kept = {key: features.get(key) for key in sorted(keep_keys) if key in features}
        removed = sorted(key for key in features if key not in keep_keys)
    else:
        raise ValueError(f"unknown view mode: {spec['mode']}")
    return kept, removed


def build_view_rows(rows: list[dict[str, Any]], view_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    output = []
    removed_counter: dict[str, int] = {}
    feature_counts = []
    for row in rows:
        copied = deepcopy(row)
        source_features = copied["baseline_inputs"][BASELINE_SOURCE]
        filtered, removed = filter_features(source_features, view_name)
        copied["baseline_inputs"][view_name] = filtered
        output.append(copied)
        feature_counts.append(len(filtered))
        for key in removed:
            removed_counter[key] = removed_counter.get(key, 0) + 1
    return output, {
        "view_name": view_name,
        "description": VIEW_SPECS[view_name]["description"],
        "feature_count_min": min(feature_counts) if feature_counts else 0,
        "feature_count_max": max(feature_counts) if feature_counts else 0,
        "removed_keys": sorted(removed_counter),
    }


def metric_record(target_mode: str, view_name: str, split_eval: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "target_mode": target_mode,
        "view": view_name,
        "split_eval": split_eval,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_dir = smoke.as_abs(args.dataset_dir)
    created_at = datetime.now(timezone.utc).isoformat()
    metric_rows = []
    view_summaries: dict[str, Any] = {}
    prediction_paths: dict[str, str] = {}

    for target_mode, filename in TARGET_FILES.items():
        rows = smoke.read_jsonl(dataset_dir / filename)
        for view_name in VIEW_SPECS:
            view_rows, view_summary = build_view_rows(rows, view_name)
            view_summaries[f"{target_mode}:{view_name}"] = view_summary
            in_probs, in_summary = smoke.train_predict_in_sample(
                view_rows,
                view_name,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            cross_probs, cross_summary = smoke.train_predict_crossfit(
                view_rows,
                view_name,
                folds=args.folds,
                epochs=args.epochs,
                learning_rate=args.learning_rate,
                l2=args.l2,
            )
            view_summaries[f"{target_mode}:{view_name}"]["model_features"] = {
                "in_sample": in_summary,
                "crossfit": cross_summary,
            }
            for split_eval, probs in [("in_sample", in_probs), ("train_internal_5fold", cross_probs)]:
                metric_rows.append(metric_record(target_mode, view_name, split_eval, view_rows, probs))
                pred_path = output_dir / f"predictions_{target_mode}_{split_eval}_{view_name}.jsonl"
                smoke.write_jsonl(
                    pred_path,
                    smoke.build_prediction_rows(view_rows, target_mode, split_eval, view_name, probs),
                )
                prediction_paths[f"{target_mode}:{split_eval}:{view_name}"] = smoke.rel_path(pred_path) or str(pred_path)

    summary = {
        "schema_version": "h002_shortcut_control_v0",
        "status": "ready_target_not_independent",
        "created_at": created_at,
        "input_paths": {
            target_mode: smoke.rel_path(dataset_dir / filename) for target_mode, filename in TARGET_FILES.items()
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
            "not_paper_result": True,
            "target_labels_are_machine_assisted": True,
            "human_confirmed": False,
            "label_evidence_as_input": False,
            "shortcut_controlled": True,
        },
        "view_specs": {
            name: {
                "description": spec["description"],
                "mode": spec["mode"],
                "keys": sorted(spec.get("drop_keys", spec.get("keep_keys", set()))),
            }
            for name, spec in VIEW_SPECS.items()
        },
        "metric_rows": metric_rows,
        "view_summaries": view_summaries,
        "prediction_paths": prediction_paths,
        "interpretation": {
            "strict_target": "not independent; remains easy under continuous-only views",
            "weak_target": "more useful but still strongly explained by semantic/geometry construction signals",
            "posterior_claim": "blocked until independent/human-confirmed target or stronger control design",
        },
    }
    summary_path = output_dir / "summary.json"
    metrics_path = output_dir / "metrics.csv"
    report_path = output_dir / "report.md"
    smoke.write_json(summary_path, summary)
    write_metrics_csv(metrics_path, metric_rows)
    write_report(report_path, summary)
    return summary


def write_metrics_csv(path: Path, metric_rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "target_mode",
                "view",
                "split_eval",
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
            writer.writerow({"target_mode": row["target_mode"], "view": row["view"], "split_eval": row["split_eval"], **row["metrics"]})


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Shortcut Control",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage control.",
        "- No validation/test rows are used.",
        "- Working labels are machine-assisted, not paper-locked human labels.",
        "- Results are not paper-level metrics.",
        "",
        "## Feature Views",
        "",
        "| View | Control |",
        "| --- | --- |",
    ]
    for name, spec in summary["view_specs"].items():
        lines.append(f"| `{name}` | {spec['description']} |")
    lines.extend(
        [
            "",
            "## Train-Internal 5-Fold Metrics",
            "",
            "| Target | View | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["split_eval"] != "train_internal_5fold":
            continue
        m = row["metrics"]
        lines.append(
            f"| {row['target_mode']} | `{row['view']}` | {fmt(m['auroc'])} | {fmt(m['auprc'])} | {fmt(m['brier'])} | {fmt(m['ece_5bin'])} | {fmt(m['accuracy_at_0_5'])} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Strict target remains too easy even after removing explicit shortcuts.",
            "- Weak target becomes less trivial but still shows high train-internal performance.",
            "- Current targets are useful for debugging representation plumbing, not for a posterior novelty claim.",
            "",
            "Next gate: `29_target_redesign.md`.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} output={summary['output_dir']} "
        f"metrics={len(summary['metric_rows'])} validation_used={summary['hyperparameters']['uses_validation_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
