#!/usr/bin/env python3
"""Fit per-family H001 p_geom_valid calibration models."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from fit_calibration import (
    DEFAULT_FAMILIES,
    DEFAULT_INPUT_DIR,
    DEFAULT_PILOT_ROOT,
    H001_ROOT,
    average_precision,
    auroc,
    brier_score,
    build_model_spec,
    count_by_role,
    fit_logistic,
    load_json,
    load_jsonl,
    log_loss,
    predict,
    prepare_rows,
    read_scan_list,
    relpath,
    summarize_predictions,
    vectorize,
    write_json,
    write_jsonl,
)


DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "calibration" / "p_geom_valid_family"
MODEL_SCHEMA_VERSION = "h001_p_geom_valid_family_model_v1"
METRICS_SCHEMA_VERSION = "h001_p_geom_valid_family_metrics_v1"
SCORE_SCHEMA_VERSION = "h001_p_geom_valid_family_score_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fit H001 family-specific p_geom_valid calibrators."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--pilot-root", type=Path, default=DEFAULT_PILOT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--families", nargs="+", default=list(DEFAULT_FAMILIES))
    parser.add_argument("--epochs", type=int, default=800)
    parser.add_argument("--learning-rate", type=float, default=0.2)
    parser.add_argument("--l2", type=float, default=1e-4)
    parser.add_argument("--bins", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def write_family_scores(
    rows: list[dict[str, Any]],
    probabilities: list[float],
    model_id: str,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row, probability in zip(rows, probabilities):
        output.append(
            {
                "schema_version": SCORE_SCHEMA_VERSION,
                "model_id": model_id,
                "candidate_id": row["candidate_id"],
                "role": row["_role"],
                "scan_id": row["scan_id"],
                "subset_split_id": row["subset_split_id"],
                "subgraph_id": row["subgraph_id"],
                "edge": row["edge"],
                "predicate": row["predicate"],
                "label": row["label"],
                "p_geom_valid_family_specific": probability,
                "p_geom_invalid_family_specific": 1.0 - probability,
            }
        )
    return output


def binary_label_guard(rows: list[dict[str, Any]]) -> bool:
    return {row["_label"] for row in rows} == {0, 1}


def baseline_summary(rows: list[dict[str, Any]], probabilities: list[float]) -> dict[str, Any]:
    labels = [row["_label"] for row in rows]
    return {
        "rows": len(rows),
        "positives": sum(labels),
        "negatives": len(labels) - sum(labels),
        "brier": brier_score(probabilities, labels),
        "nll": log_loss(probabilities, labels) if labels else None,
        "auroc_valid": auroc(probabilities, labels),
        "auprc_valid": average_precision(probabilities, labels),
    }


def make_report(metrics: dict[str, Any]) -> str:
    lines = [
        "# Family P-Geom Calibration",
        "",
        f"Created at: `{metrics['created_at']}`",
        f"Status: `{metrics['status']}`",
        f"Model id: `{metrics['model_id']}`",
        "",
        "## Inputs",
        "",
        f"- Calibration table: `{metrics['inputs']['table_jsonl']}`",
        f"- Pilot root: `{metrics['inputs']['pilot_root']}`",
        "",
        "## Family Dev Metrics",
        "",
    ]
    for family, result in metrics["conditions"]["family_logistic"].items():
        dev = result["dev"]
        lines.append(
            f"- `{family}`: rows `{dev['rows']}`, Brier `{dev['brier']}`, "
            f"NLL `{dev['nll']}`, AUROC `{dev['auroc_valid']}`, AUPRC `{dev['auprc_valid']}`"
        )
    if metrics["warnings"]:
        lines.extend(["", "## Warnings", ""])
        for warning in metrics["warnings"]:
            lines.append(f"- `{warning}`")
    lines.extend(["", "## Notes", ""])
    for note in metrics["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    table_jsonl = args.input_dir / "table.jsonl"
    manifest_json = args.input_dir / "manifest.json"
    train_scans_path = args.pilot_root / "train_scans.txt"
    dev_scans_path = args.pilot_root / "dev_scans.txt"
    for name, path in {
        "table_jsonl": table_jsonl,
        "manifest_json": manifest_json,
        "train_scans": train_scans_path,
        "dev_scans": dev_scans_path,
    }.items():
        if not path.exists():
            errors.append(f"missing_input:{name}:{relpath(path)}")
    if errors:
        print(json.dumps({"status": "blocked", "errors": errors}, sort_keys=True))
        return 2

    source_manifest = load_json(manifest_json)
    if source_manifest.get("status") != "ready":
        errors.append(f"input_manifest_not_ready:{source_manifest.get('status')}")
    if source_manifest.get("validation", {}).get("errors"):
        errors.append("input_manifest_has_validation_errors")
    if errors:
        print(json.dumps({"status": "blocked", "errors": errors}, sort_keys=True))
        return 2

    rows = load_jsonl(table_jsonl)
    train_scans = read_scan_list(train_scans_path)
    dev_scans = read_scan_list(dev_scans_path)
    if train_scans & dev_scans:
        errors.append(f"train_dev_scan_overlap:{sorted(train_scans & dev_scans)[:10]}")
    prepared, prep_warnings = prepare_rows(rows, train_scans, dev_scans, set(args.families))
    warnings.extend(prep_warnings)
    train_rows = [row for row in prepared if row["_role"] == "train"]
    dev_rows = [row for row in prepared if row["_role"] == "dev"]
    if not train_rows:
        errors.append("zero_train_rows")
    if not dev_rows:
        errors.append("zero_dev_rows")
    if errors:
        print(json.dumps({"status": "blocked", "errors": errors}, sort_keys=True))
        return 2

    model_id = "h001-p-geom-valid-family-v1"
    model_family_entries: dict[str, Any] = {}
    metric_family_entries: dict[str, Any] = {}
    scores: list[dict[str, Any]] = []
    skipped_families: dict[str, str] = {}
    for family in args.families:
        family_train = [row for row in train_rows if row["predicate"]["predicate_family"] == family]
        family_dev = [row for row in dev_rows if row["predicate"]["predicate_family"] == family]
        if not family_train or not family_dev:
            skipped_families[family] = "missing_train_or_dev_rows"
            continue
        if not binary_label_guard(family_train):
            skipped_families[family] = "train_missing_binary_labels"
            continue
        if not binary_label_guard(family_dev):
            skipped_families[family] = "dev_missing_binary_labels"
            continue

        spec = build_model_spec(family_train)
        train_vectors = [vectorize(row, spec) for row in family_train]
        dev_vectors = [vectorize(row, spec) for row in family_dev]
        train_labels = [row["_label"] for row in family_train]
        weights, trace = fit_logistic(
            train_vectors,
            train_labels,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            l2=args.l2,
        )
        train_prob = predict(train_vectors, weights)
        dev_prob = predict(dev_vectors, weights)
        train_prior = sum(train_labels) / len(train_labels)

        model_family_entries[family] = {
            "feature_names": spec["feature_names"],
            "numeric_features": spec["numeric_features"],
            "numeric_stats": spec["numeric_stats"],
            "families": spec["families"],
            "predicates": spec["predicates"],
            "weights": weights,
            "train_prior": train_prior,
            "training_trace": trace,
            "counts": {
                "train_rows": len(family_train),
                "dev_rows": len(family_dev),
                "train_label_counts": dict(sorted(Counter(train_labels).items())),
                "dev_label_counts": dict(sorted(Counter(row["_label"] for row in family_dev).items())),
            },
        }
        metric_family_entries[family] = {
            "train": summarize_predictions(family_train, train_prob, args.bins),
            "dev": summarize_predictions(family_dev, dev_prob, args.bins),
            "constant_family_train_prior_dev": baseline_summary(
                family_dev, [train_prior] * len(family_dev)
            ),
        }
        scores.extend(write_family_scores(family_train, train_prob, model_id))
        scores.extend(write_family_scores(family_dev, dev_prob, model_id))

    if skipped_families:
        for family, reason in sorted(skipped_families.items()):
            warnings.append(f"skipped_family:{family}:{reason}")
    missing_models = sorted(set(args.families) - set(model_family_entries))
    if missing_models:
        errors.append(f"missing_family_models:{missing_models}")
    status = "ready" if not errors else "blocked"

    notes = [
        "This is a train/dev family-specific calibration artifact, not source-metric-tuned evidence.",
        "Each predicate family is fit with its own logistic model using only train_dev_calib rows from that family.",
        "The artifact tests whether the pooled p_geom_valid result depends on pooling across predicate families.",
        "Semantic scores are not used during calibration fitting.",
    ]
    created_at = date.today().isoformat()
    metrics = {
        "schema_version": METRICS_SCHEMA_VERSION,
        "created_at": created_at,
        "status": status,
        "model_id": model_id,
        "inputs": {
            "table_jsonl": relpath(table_jsonl),
            "manifest_json": relpath(manifest_json),
            "pilot_root": relpath(args.pilot_root),
            "train_scans": relpath(train_scans_path),
            "dev_scans": relpath(dev_scans_path),
        },
        "hyperparameters": {
            "epochs": args.epochs,
            "learning_rate": args.learning_rate,
            "l2": args.l2,
            "bins": args.bins,
        },
        "counts": {
            "input_rows": len(rows),
            "used_rows": len(prepared),
            "by_role": count_by_role(prepared),
        },
        "conditions": {
            "family_logistic": metric_family_entries,
        },
        "warnings": warnings,
        "errors": errors,
        "notes": notes,
    }
    model = {
        "schema_version": MODEL_SCHEMA_VERSION,
        "created_at": created_at,
        "model_id": model_id,
        "source_split": "train_dev_calib",
        "family_models": model_family_entries,
        "hyperparameters": metrics["hyperparameters"],
        "warnings": warnings,
        "notes": notes,
    }
    manifest = {
        "schema_version": "h001_p_geom_valid_family_manifest_v1",
        "created_at": created_at,
        "status": status,
        "model_id": model_id,
        "source_calibration_split": "train_dev_calib",
        "model_file": "model.json",
        "scores_file": "scores.jsonl",
        "metrics_file": "metrics.json",
        "report_file": "report.md",
        "inputs": metrics["inputs"],
        "counts": metrics["counts"],
        "warnings": warnings,
        "errors": errors,
        "notes": notes,
    }

    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "manifest.json", manifest)
        write_json(args.output_dir / "model.json", model)
        write_json(args.output_dir / "metrics.json", metrics)
        write_jsonl(args.output_dir / "scores.jsonl", scores)
        (args.output_dir / "report.md").write_text(make_report(metrics), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "output_dir": relpath(args.output_dir),
                "families": sorted(model_family_entries),
                "warnings": len(warnings),
                "errors": errors,
                "dry_run": args.dry_run,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
