#!/usr/bin/env python3
"""Train-only controlled posterior smoke for H002 controlled labels."""

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
DEFAULT_FEATURES = RGA_ROOT / "factor_dataset/deployable_features_all.jsonl"
DEFAULT_READINESS_DIR = RGA_ROOT / "controlled_label_readiness_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "controlled_posterior_smoke_codex_ver"

TARGET_FILES = {
    "mined_controlled_codex_ver": "mined_binary_targets.jsonl",
    "combined_controlled_codex_ver": "combined_binary_targets.jsonl",
}
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
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--readiness-dir", type=Path, default=DEFAULT_READINESS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=1500)
    parser.add_argument("--learning-rate", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.03)
    return parser.parse_args()


def load_features(path: Path) -> dict[str, dict[str, Any]]:
    rows = smoke.read_jsonl(path)
    by_id = {}
    for row in rows:
        prediction_id = str(row["identity"]["prediction_id"])
        if prediction_id in by_id:
            raise ValueError(f"duplicate feature prediction_id: {prediction_id}")
        by_id[prediction_id] = row
    return by_id


def target_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {0: 0, 1: 0}
    final_labels: dict[str, int] = {}
    strata: dict[str, int] = {}
    rank_bands: dict[str, int] = {}
    families: dict[str, int] = {}
    statuses: dict[str, int] = {}
    for row in rows:
        y = smoke.target_y(row)
        counts[y] += 1
        final_label = str(row["target"].get("final_controlled_label"))
        stratum = str(row["target"].get("proposed_review_stratum"))
        rank_band = str(row["target"].get("rank_band"))
        family = str(row["target"].get("predicate_family"))
        status = str(row["target"].get("geometry_status"))
        final_labels[final_label] = final_labels.get(final_label, 0) + 1
        strata[stratum] = strata.get(stratum, 0) + 1
        rank_bands[rank_band] = rank_bands.get(rank_band, 0) + 1
        families[family] = families.get(family, 0) + 1
        statuses[status] = statuses.get(status, 0) + 1
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "final_labels": dict(sorted(final_labels.items())),
        "proposed_review_strata": dict(sorted(strata.items())),
        "rank_bands": dict(sorted(rank_bands.items())),
        "predicate_families": dict(sorted(families.items())),
        "geometry_statuses": dict(sorted(statuses.items())),
    }


def build_rows(
    targets: list[dict[str, Any]],
    features_by_id: dict[str, dict[str, Any]],
    target_mode: str,
) -> list[dict[str, Any]]:
    rows = []
    missing = []
    for target in targets:
        prediction_id = str(target["prediction_id"])
        feature = features_by_id.get(prediction_id)
        if feature is None:
            missing.append(prediction_id)
            continue
        row = deepcopy(feature)
        row.pop("feature_blocks", None)
        row.pop("leakage_boundary", None)
        row["schema_version"] = "h002_controlled_posterior_smoke_row_v0"
        row["record_type"] = "h002_controlled_posterior_smoke_row"
        row["provenance"] = {
            "feature_source": "factor_dataset/deployable_features_all.jsonl",
            "target_source": "controlled_label_readiness_codex_ver",
            "split_policy": "train_only",
        }
        row["target"] = {
            "target_mode": target_mode,
            "y": int(target["posterior_target"]),
            "sample_weight": 1.0,
            "final_controlled_label": target["final_controlled_label"],
            "reviewer_id": target["reviewer_id"],
            "confidence": target.get("confidence"),
            "review_id": target.get("review_id"),
            "rank_band": target.get("rank_band"),
            "predicate_family": target.get("predicate_family"),
            "predicate_label": target.get("predicate_label"),
            "geometry_status": target.get("geometry_status"),
            "proposed_review_stratum": target.get("proposed_review_stratum"),
            "label_source": "codex_ver_sampling_prior_bootstrap",
            "human_confirmed": False,
            "paper_locked": False,
            "target_source": "controlled_codex_ver_binary_target",
            "allowed_use": "train-only controlled posterior plumbing smoke",
            "leakage_boundary": (
                "Targets are Codex bootstrap labels from controlled sampling strata. "
                "They are not human-confirmed and cannot support posterior claims."
            ),
        }
        rows.append(row)
    if missing:
        raise ValueError(f"missing deployable feature rows for {len(missing)} targets")
    return rows


def metric_record(kind: str, target_mode: str, split_eval: str, name: str, rows: list[dict[str, Any]], probs: list[float]) -> dict[str, Any]:
    return {
        "kind": kind,
        "target_mode": target_mode,
        "split_eval": split_eval,
        "name": name,
        "metrics": smoke.metrics([smoke.target_y(row) for row in rows], probs),
    }


def comparison(metric_rows: list[dict[str, Any]], target_mode: str) -> dict[str, Any]:
    by_name = {
        row["name"]: row["metrics"]
        for row in metric_rows
        if row["kind"] == "baseline"
        and row["target_mode"] == target_mode
        and row["split_eval"] == "train_internal_5fold"
    }
    factorized = by_name.get("factorized_reliability_posterior", {})
    simple = by_name.get("semantic_plus_geometry", {})
    auroc_delta = None
    if factorized.get("auroc") is not None and simple.get("auroc") is not None:
        auroc_delta = factorized["auroc"] - simple["auroc"]
    return {
        "target_mode": target_mode,
        "factorized_minus_semantic_plus_geometry": {
            "auroc": auroc_delta,
            "auprc": (
                factorized.get("auprc") - simple.get("auprc")
                if factorized.get("auprc") is not None and simple.get("auprc") is not None
                else None
            ),
            "brier": (
                factorized.get("brier") - simple.get("brier")
                if factorized.get("brier") is not None and simple.get("brier") is not None
                else None
            ),
        },
        "acceptance_rule_met_as_numeric_plumbing_only": bool(
            factorized
            and simple
            and (
                (
                    factorized.get("auprc") is not None
                    and simple.get("auprc") is not None
                    and factorized["auprc"] - simple["auprc"] >= 0.03
                )
                or (
                    factorized.get("brier") is not None
                    and simple.get("brier") is not None
                    and simple["brier"] - factorized["brier"] >= 0.02
                )
            )
            and (
                auroc_delta is None
                or auroc_delta >= -0.02
            )
        ),
    }


def fmt(value: Any) -> str:
    if value is None:
        return "nan"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Controlled Posterior Smoke",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only plumbing smoke.",
        "- No validation/test rows are used.",
        "- Labels are `(codex_ver)` bootstrap labels from controlled sampling strata.",
        "- Results are not paper-level metrics.",
        "- Posterior advantage claims remain blocked.",
        "",
        "## Target Counts",
        "",
        "| Target | Rows | Positive | Negative |",
        "| --- | ---: | ---: | ---: |",
    ]
    for target_mode, counts in summary["target_summaries"].items():
        lines.append(
            f"| `{target_mode}` | {counts['rows']} | {counts['positive']} | {counts['negative']} |"
        )
    lines.extend(
        [
            "",
            "## Main Baselines",
            "",
            "| Target | Baseline | AUROC | AUPRC | Brier | ECE-5 | Accuracy@0.5 |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in summary["metric_rows"]:
        if row["kind"] != "baseline" or row["split_eval"] != "train_internal_5fold":
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
            "## Factorized Delta",
            "",
            "| Target | Delta AUROC | Delta AUPRC | Delta Brier | Numeric rule met |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    for item in summary["comparisons"]:
        delta = item["factorized_minus_semantic_plus_geometry"]
        lines.append(
            f"| `{item['target_mode']}` | {fmt(delta['auroc'])} | {fmt(delta['auprc'])} | "
            f"{fmt(delta['brier'])} | `{item['acceptance_rule_met_as_numeric_plumbing_only']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This verifies that the controlled target can be joined to deployable features and consumed by the four baseline views.",
            "- Because the labels are Codex bootstrap labels derived from sampling priors, any numeric gain is plumbing-only.",
            "- The human/independent label requirement remains open before H002 can claim factorized posterior support.",
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
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    readiness_dir = smoke.as_abs(args.readiness_dir)
    features_by_id = load_features(args.features)
    created_at = datetime.now(timezone.utc).isoformat()
    metric_rows = []
    prediction_paths: dict[str, str] = {}
    target_summaries: dict[str, Any] = {}
    feature_summaries: dict[str, Any] = {}
    view_summaries: dict[str, Any] = {}

    for target_mode, target_file in TARGET_FILES.items():
        targets = smoke.read_jsonl(readiness_dir / target_file)
        rows = build_rows(targets, features_by_id, target_mode)
        target_summaries[target_mode] = target_counts(rows)
        target_rows_path = output_dir / f"{target_mode}_rows.jsonl"
        smoke.write_jsonl(target_rows_path, rows)
        prediction_paths[f"{target_mode}:target_rows"] = smoke.rel_path(target_rows_path) or str(target_rows_path)

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
            feature_summaries[f"{target_mode}:{baseline}"] = {
                "in_sample": in_summary,
                "crossfit": cross_summary,
            }
            for split_eval, probs in [("in_sample", in_probs), ("train_internal_5fold", cross_probs)]:
                metric_rows.append(metric_record("baseline", target_mode, split_eval, baseline, rows, probs))
                pred_path = output_dir / f"predictions_{target_mode}_{split_eval}_{baseline}.jsonl"
                smoke.write_jsonl(pred_path, smoke.build_prediction_rows(rows, target_mode, split_eval, baseline, probs))
                prediction_paths[f"{target_mode}:{split_eval}:{baseline}"] = smoke.rel_path(pred_path) or str(pred_path)

        for view_name in CONTROL_VIEWS:
            view_rows, view_summary = redesigned.build_view_rows(rows, view_name)
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
                metric_rows.append(metric_record("control_view", target_mode, split_eval, view_name, view_rows, probs))
                pred_path = output_dir / f"predictions_{target_mode}_{split_eval}_{view_name}.jsonl"
                smoke.write_jsonl(pred_path, smoke.build_prediction_rows(view_rows, target_mode, split_eval, view_name, probs))
                prediction_paths[f"{target_mode}:{split_eval}:{view_name}"] = smoke.rel_path(pred_path) or str(pred_path)

        for probe_name in PROBE_NAMES:
            metric_rows.append(
                metric_record(
                    "probe",
                    target_mode,
                    "score_probe",
                    probe_name,
                    rows,
                    redesigned.probe_scores(rows, probe_name),
                )
            )

    summary = {
        "schema_version": "h002_controlled_posterior_smoke_v0",
        "status": "ready_plumbing_only_controlled_codex_labels",
        "created_at": created_at,
        "input_paths": {
            "features": smoke.rel_path(args.features),
            "readiness_dir": smoke.rel_path(readiness_dir),
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
            "label_source": "codex_ver_sampling_prior_bootstrap",
            "human_confirmed": False,
            "label_evidence_as_input": False,
            "posterior_claim_allowed": False,
            "vmv_model_input_allowed": False,
        },
        "target_summaries": target_summaries,
        "metric_rows": metric_rows,
        "comparisons": [comparison(metric_rows, target_mode) for target_mode in TARGET_FILES],
        "feature_summaries": feature_summaries,
        "view_summaries": view_summaries,
        "prediction_paths": prediction_paths,
        "interpretation": {
            "primary": "controlled codex_ver labels are consumable by the posterior pipeline",
            "claim": "plumbing only; no posterior advantage claim",
            "next": "replace codex_ver labels with human/independent labels before hypothesis support",
        },
    }
    write_outputs(output_dir, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    brief = []
    for comparison_row in summary["comparisons"]:
        delta = comparison_row["factorized_minus_semantic_plus_geometry"]
        brief.append(
            f"{comparison_row['target_mode']}:d_auprc={delta['auprc']:.4f}:d_brier={delta['brier']:.4f}"
        )
    print(
        f"status={summary['status']} targets={len(summary['target_summaries'])} "
        f"metrics={len(summary['metric_rows'])} validation_used={summary['hyperparameters']['uses_validation_rows']} "
        + " ".join(brief)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
