#!/usr/bin/env python3
"""Train-only smoke using H002 strict `(codex_ver)` labels."""

from __future__ import annotations

import argparse
import csv
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke
import redesigned_target_smoke as redesigned


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_STRICT_TARGET = RGA_ROOT / "target_redesign/strict_proximity_informativeness.jsonl"
DEFAULT_CODEX_TARGETS = RGA_ROOT / "human_confirmation_protocol/strict_codex_ver_binary_targets.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "codex_label_smoke"

TARGET_MODE = "strict_codex_ver"
BASELINES = [
    "semantic_only",
    "geometry_only",
    "semantic_plus_geometry",
    "factorized_reliability_posterior",
]
CONTROL_VIEWS = [
    "drop_direct_identity",
    "drop_direct_identity_rank",
    "safe_continuous",
    "geometry_continuous_only",
    "semantic_raw_only",
]
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
    parser.add_argument("--strict-target", type=Path, default=DEFAULT_STRICT_TARGET)
    parser.add_argument("--codex-targets", type=Path, default=DEFAULT_CODEX_TARGETS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def load_codex_targets(path: Path) -> dict[str, dict[str, Any]]:
    rows = smoke.read_jsonl(path)
    by_id = {}
    for row in rows:
        prediction_id = str(row["prediction_id"])
        if prediction_id in by_id:
            raise ValueError(f"duplicate codex target prediction_id: {prediction_id}")
        by_id[prediction_id] = row
    return by_id


def build_codex_rows(strict_rows: list[dict[str, Any]], codex_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    output = []
    missing = []
    for row in strict_rows:
        prediction_id = str(row["prediction_id"])
        codex = codex_by_id.get(prediction_id)
        if codex is None:
            missing.append(prediction_id)
            continue
        copied = deepcopy(row)
        copied["target_mode"] = TARGET_MODE
        copied["target"]["y"] = int(codex["posterior_target"])
        copied["target"]["final_human_label"] = codex["final_human_label"]
        copied["target"]["label_source"] = codex["label_source"]
        copied["target"]["reviewer_id"] = codex["reviewer_id"]
        copied["target"]["confidence"] = codex["confidence"]
        copied["target"]["human_confirmed"] = False
        copied["target"]["paper_locked"] = False
        copied["target"]["target_source"] = "codex_ver_strict_binary_target"
        copied["target"]["allowed_use"] = "train-only posterior plumbing smoke"
        copied["target"]["leakage_boundary"] = (
            "Codex bootstrap labels mirror the strict target-v2 mapping. "
            "Use only for plumbing; do not claim posterior advantage."
        )
        output.append(copied)
    extra = sorted(set(codex_by_id) - {str(row["prediction_id"]) for row in strict_rows})
    if missing or extra:
        raise ValueError(f"codex/strict target join mismatch missing={len(missing)} extra={len(extra)}")
    return output


def target_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {0: 0, 1: 0}
    final_labels: dict[str, int] = {}
    working_labels: dict[str, int] = {}
    families: dict[str, int] = {}
    for row in rows:
        counts[smoke.target_y(row)] += 1
        final_label = str(row["target"].get("final_human_label"))
        working_label = str(row["target"].get("working_label"))
        family = str(row["target"].get("predicate_family"))
        final_labels[final_label] = final_labels.get(final_label, 0) + 1
        working_labels[working_label] = working_labels.get(working_label, 0) + 1
        families[family] = families.get(family, 0) + 1
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "final_labels": dict(sorted(final_labels.items())),
        "working_labels": dict(sorted(working_labels.items())),
        "families": dict(sorted(families.items())),
    }


def metric_record(kind: str, split_eval: str, name: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": kind,
        "target_mode": TARGET_MODE,
        "split_eval": split_eval,
        "name": name,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


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


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Codex Label Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only plumbing smoke.",
        "- No validation/test rows are used.",
        "- `(codex_ver)` labels are not human-confirmed labels.",
        "- Results are not paper-level metrics.",
        "- Posterior advantage claims remain blocked.",
        "",
        "## Target Counts",
        "",
        "| Rows | Positive | Negative |",
        "| ---: | ---: | ---: |",
        f"| {summary['target_summary']['rows']} | {summary['target_summary']['positive']} | {summary['target_summary']['negative']} |",
        "",
        "## Main Baselines",
        "",
        "| Baseline | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["metric_rows"]:
        if row["kind"] != "baseline" or row["split_eval"] != "train_internal_5fold":
            continue
        metrics = row["metrics"]
        lines.append(
            f"| `{row['name']}` | {fmt(metrics['auroc'])} | {fmt(metrics['auprc'])} | {fmt(metrics['brier'])} | {fmt(metrics['ece_5bin'])} | {fmt(metrics['accuracy_at_0_5'])} |"
        )
    lines.extend(
        [
            "",
            "## Controlled Views",
            "",
            "| View | AUROC | AUPRC | Brier | Accuracy@0.5 |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["kind"] != "control_view" or row["split_eval"] != "train_internal_5fold":
            continue
        metrics = row["metrics"]
        lines.append(
            f"| `{row['name']}` | {fmt(metrics['auroc'])} | {fmt(metrics['auprc'])} | {fmt(metrics['brier'])} | {fmt(metrics['accuracy_at_0_5'])} |"
        )
    lines.extend(
        [
            "",
            "## Probe Metrics",
            "",
            "| Probe | AUROC | AUPRC |",
            "| --- | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["kind"] != "probe":
            continue
        metrics = row["metrics"]
        lines.append(f"| `{row['name']}` | {fmt(metrics['auroc'])} | {fmt(metrics['auprc'])} |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This confirms that `(codex_ver)` labels can be consumed by the H002 posterior pipeline.",
            "- Because the labels are a controlled mapping from target-v2 working labels, the smoke mostly mirrors the redesigned strict target.",
            "- This is a plumbing and leakage-boundary check, not method evidence.",
            "",
            "Next gate: multi-view audit protocol or independent human label collection before any posterior claim.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    strict_rows = smoke.read_jsonl(args.strict_target)
    codex_by_id = load_codex_targets(args.codex_targets)
    rows = build_codex_rows(strict_rows, codex_by_id)
    created_at = datetime.now(timezone.utc).isoformat()
    metric_rows = []
    prediction_paths: dict[str, str] = {}
    feature_summaries: dict[str, Any] = {}
    view_summaries: dict[str, Any] = {}

    for baseline in BASELINES:
        in_probs, in_summary = smoke.train_predict_in_sample(
            rows,
            baseline,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            l2=args.l2,
        )
        cross_probs, cross_summary = smoke.train_predict_crossfit(
            rows,
            baseline,
            folds=args.folds,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            l2=args.l2,
        )
        feature_summaries[baseline] = {"in_sample": in_summary, "crossfit": cross_summary}
        for split_eval, probs in [("in_sample", in_probs), ("train_internal_5fold", cross_probs)]:
            metric_rows.append(metric_record("baseline", split_eval, baseline, rows, probs))
            pred_path = output_dir / f"predictions_{split_eval}_{baseline}.jsonl"
            smoke.write_jsonl(pred_path, smoke.build_prediction_rows(rows, TARGET_MODE, split_eval, baseline, probs))
            prediction_paths[f"{split_eval}:{baseline}"] = smoke.rel_path(pred_path) or str(pred_path)

    for view_name in CONTROL_VIEWS:
        view_rows, view_summary = redesigned.build_view_rows(rows, view_name)
        view_summaries[view_name] = view_summary
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
        view_summaries[view_name]["model_features"] = {"in_sample": in_summary, "crossfit": cross_summary}
        for split_eval, probs in [("in_sample", in_probs), ("train_internal_5fold", cross_probs)]:
            metric_rows.append(metric_record("control_view", split_eval, view_name, view_rows, probs))
            pred_path = output_dir / f"predictions_{split_eval}_{view_name}.jsonl"
            smoke.write_jsonl(pred_path, smoke.build_prediction_rows(view_rows, TARGET_MODE, split_eval, view_name, probs))
            prediction_paths[f"{split_eval}:{view_name}"] = smoke.rel_path(pred_path) or str(pred_path)

    for probe_name in PROBE_NAMES:
        metric_rows.append(
            metric_record("probe", "score_probe", probe_name, rows, redesigned.probe_scores(rows, probe_name))
        )

    summary = {
        "schema_version": "h002_codex_label_smoke_v0",
        "status": "ready_plumbing_only_codex_labels",
        "created_at": created_at,
        "input_paths": {
            "strict_target": smoke.rel_path(args.strict_target),
            "codex_targets": smoke.rel_path(args.codex_targets),
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
            "human_confirmed": False,
            "label_source": "codex_ver_not_human_confirmed",
            "label_evidence_as_input": False,
            "posterior_claim_allowed": False,
            "small_n_warning": True,
        },
        "target_summary": target_counts(rows),
        "metric_rows": metric_rows,
        "feature_summaries": feature_summaries,
        "view_summaries": view_summaries,
        "prediction_paths": prediction_paths,
        "interpretation": {
            "primary": "codex_ver labels are consumable by the posterior pipeline",
            "claim": "plumbing only; no posterior advantage claim",
            "next": "independent human/multiview audit before method evidence",
        },
    }
    write_outputs(output_dir, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} rows={summary['target_summary']['rows']} "
        f"positive={summary['target_summary']['positive']} negative={summary['target_summary']['negative']} "
        f"metrics={len(summary['metric_rows'])} validation_used={summary['hyperparameters']['uses_validation_rows']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
