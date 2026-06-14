#!/usr/bin/env python3
"""Train-only smoke for H002 redesigned posterior targets."""

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
DEFAULT_TARGET_DIR = RGA_ROOT / "target_redesign"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "redesigned_target_smoke"

TARGET_FILES = {
    "strict_proximity_informativeness": "strict_proximity_informativeness.jsonl",
    "weak_satisfied_actionability": "weak_satisfied_actionability.jsonl",
}

BASELINE_SOURCE = "factorized_reliability_posterior"

DIRECT_IDENTITY_KEYS = {
    "absolute_disagreement",
    "coverage_state",
    "covered_and_uncertain",
    "covered_checkable",
    "geometry_status",
    "geometry_status_is_uncertain",
    "geometry_status_is_unsupported",
    "geometry_status_satisfied",
    "geometry_status_uncertain",
    "geometry_status_unsatisfied",
    "geometry_status_unsupported",
    "missing_geometry",
    "predicate_family",
    "predicate_family_supported",
    "predicate_label",
    "proximity_x_p_geom_valid",
    "relative_vertical_x_p_geom_valid",
    "semantic_geometry_disagreement_score",
    "semantic_score_norm_minus_p_geom_valid",
    "source_id",
    "support_contact_x_p_geom_valid",
    "tail_gt100_and_satisfied",
    "top100_and_unsatisfied",
    "top100_semantic",
    "top50_semantic",
    "underconfidence_score",
    "unsupported_family",
}

RANK_KEYS = {
    "rank_in_context",
    "predicate_rank_for_pair",
    "semantic_score_norm",
}

CONTINUOUS_SAFE_KEYS = {
    "consistency_score",
    "geometry_available",
    "geometry_checkable",
    "geometry_residual_proxy",
    "p_geom_invalid",
    "p_geom_valid_available",
    "p_geom_valid_imputed_neutral",
    "semantic_score_raw",
}

GEOMETRY_CONTINUOUS_KEYS = {
    "consistency_score",
    "geometry_available",
    "geometry_checkable",
    "geometry_residual_proxy",
    "p_geom_invalid",
    "p_geom_valid_available",
    "p_geom_valid_imputed_neutral",
}

SEMANTIC_RAW_KEYS = {
    "semantic_score_raw",
}

VIEW_SPECS = {
    "full_factorized": {
        "mode": "drop",
        "drop_keys": set(),
        "description": "Original factorized view; included only as a leakage-risk diagnostic.",
    },
    "drop_direct_identity": {
        "mode": "drop",
        "drop_keys": DIRECT_IDENTITY_KEYS,
        "description": "Remove direct target identity, RGA bucket, status, family, and interaction features.",
    },
    "drop_direct_identity_rank": {
        "mode": "drop",
        "drop_keys": DIRECT_IDENTITY_KEYS | RANK_KEYS,
        "description": "Remove direct identity plus semantic rank/normalized score fields.",
    },
    "safe_continuous": {
        "mode": "keep",
        "keep_keys": CONTINUOUS_SAFE_KEYS,
        "description": "Use only semantic raw confidence and continuous geometry evidence.",
    },
    "geometry_continuous_only": {
        "mode": "keep",
        "keep_keys": GEOMETRY_CONTINUOUS_KEYS,
        "description": "Use only continuous geometry evidence.",
    },
    "semantic_raw_only": {
        "mode": "keep",
        "keep_keys": SEMANTIC_RAW_KEYS,
        "description": "Use only source semantic raw confidence.",
    },
}

PROBE_NAMES = [
    "semantic_score_raw",
    "semantic_score_norm",
    "negative_semantic_score_norm",
    "p_geom_valid",
    "consistency_score",
    "negative_geometry_residual",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-dir", type=Path, default=DEFAULT_TARGET_DIR)
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


def probe_scores(rows: list[dict[str, Any]], probe_name: str) -> list[float]:
    scores = []
    for row in rows:
        features = row["baseline_inputs"][BASELINE_SOURCE]
        semantic_norm = smoke.safe_float(features.get("semantic_score_norm"), 0.0)
        if probe_name == "semantic_score_raw":
            score = smoke.safe_float(features.get("semantic_score_raw"), 0.0)
        elif probe_name == "semantic_score_norm":
            score = semantic_norm
        elif probe_name == "negative_semantic_score_norm":
            score = 1.0 - semantic_norm
        elif probe_name == "p_geom_valid":
            score = smoke.safe_float(features.get("p_geom_valid_imputed_neutral"), 0.5)
        elif probe_name == "consistency_score":
            score = smoke.safe_float(features.get("consistency_score"), 0.0)
        elif probe_name == "negative_geometry_residual":
            score = 1.0 - smoke.safe_float(features.get("geometry_residual_proxy"), 0.0)
        else:
            raise ValueError(f"unknown probe: {probe_name}")
        scores.append(score)
    return scores


def metric_record(target_mode: str, view_name: str, split_eval: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": "view",
        "target_mode": target_mode,
        "name": view_name,
        "split_eval": split_eval,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


def probe_record(target_mode: str, probe_name: str, rows: list[dict[str, Any]], scores: list[float]) -> dict[str, Any]:
    return {
        "kind": "probe",
        "target_mode": target_mode,
        "name": probe_name,
        "split_eval": "score_probe",
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], scores),
    }


def target_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {0: 0, 1: 0}
    working_labels: dict[str, int] = {}
    families: dict[str, int] = {}
    for row in rows:
        counts[smoke.target_y(row)] += 1
        label = str(row["target"].get("working_label"))
        family = str(row["target"].get("predicate_family"))
        working_labels[label] = working_labels.get(label, 0) + 1
        families[family] = families.get(family, 0) + 1
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "working_labels": working_labels,
        "families": families,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    target_dir = smoke.as_abs(args.target_dir)
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    metric_rows = []
    prediction_paths: dict[str, str] = {}
    view_summaries: dict[str, Any] = {}
    target_summaries: dict[str, Any] = {}

    for target_mode, filename in TARGET_FILES.items():
        rows = smoke.read_jsonl(target_dir / filename)
        target_summaries[target_mode] = target_counts(rows)
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
        for probe_name in PROBE_NAMES:
            metric_rows.append(probe_record(target_mode, probe_name, rows, probe_scores(rows, probe_name)))

    summary = {
        "schema_version": "h002_redesigned_target_smoke_v0",
        "status": "ready_plumbing_only",
        "created_at": created_at,
        "input_paths": {
            target_mode: smoke.rel_path(target_dir / filename) for target_mode, filename in TARGET_FILES.items()
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
            "small_n_warning": True,
            "posterior_claim_allowed": False,
        },
        "target_summaries": target_summaries,
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
            "primary": "strict target is less shortcut-prone but too small for posterior claim",
            "sensitivity": "weak target remains family-confounded",
            "claim": "human-confirmed labels are required before method evidence",
        },
    }
    write_outputs(output_dir, summary)
    return summary


def write_outputs(output_dir: Path, summary: dict[str, Any]) -> None:
    summary_path = output_dir / "summary.json"
    metrics_path = output_dir / "metrics.csv"
    report_path = output_dir / "report.md"
    smoke.write_json(summary_path, summary)
    with metrics_path.open("w", newline="", encoding="utf-8") as handle:
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
    write_report(report_path, summary)


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Redesigned Target Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only plumbing smoke.",
        "- No validation/test rows are used.",
        "- Working labels are machine-assisted, not human-confirmed.",
        "- Results are not paper-level metrics.",
        "",
        "## Target Counts",
        "",
        "| Target | Rows | Positive | Negative |",
        "| --- | ---: | ---: | ---: |",
    ]
    for target_mode, counts in summary["target_summaries"].items():
        lines.append(f"| `{target_mode}` | {counts['rows']} | {counts['positive']} | {counts['negative']} |")
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
        if row["kind"] != "view" or row["split_eval"] != "train_internal_5fold":
            continue
        metrics = row["metrics"]
        lines.append(
            f"| `{row['target_mode']}` | `{row['name']}` | {fmt(metrics['auroc'])} | {fmt(metrics['auprc'])} | {fmt(metrics['brier'])} | {fmt(metrics['ece_5bin'])} | {fmt(metrics['accuracy_at_0_5'])} |"
        )
    lines.extend(
        [
            "",
            "## Probe Metrics",
            "",
            "| Target | Probe | AUROC | AUPRC |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["kind"] != "probe":
            continue
        metrics = row["metrics"]
        lines.append(f"| `{row['target_mode']}` | `{row['name']}` | {fmt(metrics['auroc'])} | {fmt(metrics['auprc'])} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- `strict_proximity_informativeness` is the least-confounded target but has only 27 rows.",
            "- `weak_satisfied_actionability` is larger but remains family-confounded.",
            "- Any high number here is a signal for whether the target is worth human confirmation, not a posterior performance claim.",
            "",
            "Next gate: `31_human_confirmation_protocol.md`.",
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
