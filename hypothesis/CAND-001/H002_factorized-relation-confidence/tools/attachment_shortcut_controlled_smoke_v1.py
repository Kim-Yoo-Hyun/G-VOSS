#!/usr/bin/env python3
"""Run strict within-cell controlled smoke for attachment H002.

This runner uses the attachment numeric geometry artifact, builds a small
within-hidden-cell balanced Task-A slice, and checks whether T+G compatibility
survives after the strongest construction-cell shortcut is controlled.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from attachment_numeric_geometry_smoke_v1 import (
    attachment_model_feature_fns,
    hidden_construction_features,
    hidden_witness_score_features,
)
from learned_smoke_runner_v1 import (
    binary_metrics,
    error_cases,
    group_metrics,
    read_json,
    read_jsonl,
    train_eval_cv,
    write_json,
    write_jsonl,
)
from smoke_baseline_runner_v1 import rel_path


H002_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_ROOT = H002_ROOT / "artifacts/attachment_numeric_geometry_v1"
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/attachment_shortcut_controlled_smoke_v1"

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def stable_hash(text: str) -> int:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def task_label(row: dict[str, Any]) -> str:
    return str(row.get("counterfactual_axis", {}).get("compatibility_label"))


def task_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if task_label(row) in {"positive", "counterfactual_negative"}]


def task_labels(rows: list[dict[str, Any]]) -> list[int]:
    return [1 if task_label(row) == "positive" else 0 for row in rows]


def hidden_cell(row: dict[str, Any]) -> str:
    return str(row.get("hidden_control", {}).get("cell_id_hidden", "missing"))


def hidden_cell_only_features(row: dict[str, Any]) -> dict[str, float]:
    cell = hidden_cell(row).replace(" ", "_").replace("/", "_")
    return {f"H.cell_id_hidden={cell}": 1.0}


def model_feature_fns() -> dict[str, FeatureFn]:
    fns = dict(attachment_model_feature_fns())
    fns["H0_hidden_cell_only_probe"] = hidden_cell_only_features
    fns["H1_hidden_construction_probe"] = hidden_construction_features
    fns["H2_hidden_witness_score_probe"] = hidden_witness_score_features
    return fns


def select_within_cell_balanced(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"positive": [], "counterfactual_negative": []})
    for row in task_rows(rows):
        grouped[hidden_cell(row)][task_label(row)].append(row)

    selected: list[dict[str, Any]] = []
    groups: list[dict[str, Any]] = []
    cell_summary: dict[str, Any] = {}
    pair_idx = 0
    for cell, by_label in sorted(grouped.items()):
        positives = sorted(by_label["positive"], key=lambda row: stable_hash(str(row.get("row_id"))))
        negatives = sorted(by_label["counterfactual_negative"], key=lambda row: stable_hash(str(row.get("row_id"))))
        take = min(len(positives), len(negatives))
        cell_summary[cell] = {
            "available_positive": len(positives),
            "available_negative": len(negatives),
            "selected_positive": take,
            "selected_negative": take,
            "selected_rows": 2 * take,
            "included": take > 0,
        }
        for pos, neg in zip(positives[:take], negatives[:take]):
            group_id = f"h002_attach_ctrl_v1_pair_{pair_idx:04d}"
            pair_idx += 1
            pos_copy = copy.deepcopy(pos)
            neg_copy = copy.deepcopy(neg)
            for item in [pos_copy, neg_copy]:
                item["group_id"] = group_id
                item["controlled_axis"] = {
                    "control_name": "within_hidden_cell_balanced",
                    "hidden_cell": cell,
                    "pair_group_id": group_id,
                    "selection_policy": "stable_hash_row_id_downsample_to_min_class_per_cell",
                }
            pos_copy["counterfactual_axis"]["anchor_row_id"] = pos_copy["row_id"]
            neg_copy["counterfactual_axis"]["anchor_row_id"] = pos_copy["row_id"]
            selected.extend([pos_copy, neg_copy])
            groups.append(
                {
                    "group_id": group_id,
                    "hidden_cell": cell,
                    "positive_row_id": pos_copy["row_id"],
                    "negative_row_id": neg_copy["row_id"],
                    "matching_fields": {
                        "hidden_cell": cell,
                        "compatibility_positive": 1,
                        "compatibility_negative": 1,
                    },
                }
            )
    return selected, groups, cell_summary


def eval_models(
    rows: list[dict[str, Any]],
    labels: list[int],
    folds: int,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[dict[str, Any], dict[str, list[float]], dict[str, Any]]:
    metrics: dict[str, Any] = {}
    predictions: dict[str, list[float]] = {}
    fold_records: dict[str, Any] = {}
    for model_name, feature_fn in model_feature_fns().items():
        result = train_eval_cv(rows, labels, feature_fn, "task_a", folds, epochs, lr, l2)
        metrics[model_name] = result["metrics"]
        predictions[model_name] = result["predictions"]
        fold_records[model_name] = result["folds"]
    return metrics, predictions, fold_records


def validation_errors(input_root: Path, rows: list[dict[str, Any]], selected: list[dict[str, Any]], materialization_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    materialization_errors = input_root / "validation_errors.jsonl"
    if not materialization_errors.exists():
        errors.append({"error_type": "missing_materialization_validation_errors"})
    elif materialization_errors.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "materialization_validation_errors_nonempty"})
    if materialization_summary.get("status") != "h002_attachment_numeric_geometry_v1_ready":
        errors.append({"error_type": "unexpected_materialization_status", "status": materialization_summary.get("status")})
    labels = task_labels(selected)
    if sum(labels) != len(labels) - sum(labels):
        errors.append({"error_type": "controlled_slice_not_balanced", "positive": sum(labels), "negative": len(labels) - sum(labels)})
    if len(selected) < 20:
        errors.append({"error_type": "controlled_slice_too_small", "rows": len(selected)})
    for row in selected:
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_id": row.get("row_id")})
        if "Z_e" in row.get("model_views", {}).get("compatibility_main", {}):
            errors.append({"error_type": "Z_e_in_compatibility_main", "row_id": row.get("row_id")})
        if not row.get("G_e", {}).get("geometry_features"):
            errors.append({"error_type": "missing_numeric_G_e", "row_id": row.get("row_id")})
    return errors


def gate_summary(metrics: dict[str, Any], errors: list[dict[str, Any]], selected: list[dict[str, Any]]) -> dict[str, Any]:
    source = metrics["M1_source_only_Z"]["auroc"]
    geometry = metrics["M3_geometry_only_G"]["auroc"]
    compat = metrics["M4_compatibility_TG"]["auroc"]
    factorized = metrics["M5_factorized_TZGQ"]["auroc"]
    shortcut = metrics["S1_predicate_family_shortcut"]["auroc"]
    hidden_cell = metrics["H0_hidden_cell_only_probe"]["auroc"]
    hidden_construct = metrics["H1_hidden_construction_probe"]["auroc"]
    hidden_witness = metrics["H2_hidden_witness_score_probe"]["auroc"]
    hidden_values = [value for value in [hidden_cell, hidden_construct, hidden_witness] if value is not None]
    hidden_best = max(hidden_values) if hidden_values else None
    labels = task_labels(selected)
    pos = sum(labels)
    neg = len(labels) - pos
    cell_counts = Counter(hidden_cell_fn(row) for row in selected)
    dataset_pass = not errors and pos == neg and len(selected) >= 20 and len(cell_counts) >= 3
    signal_pass = compat is not None and source is not None and shortcut is not None and compat > source and compat > shortcut
    geometry_pass = geometry is not None and source is not None and geometry > source
    hidden_pass = hidden_best is not None and compat is not None and compat > hidden_best
    return {
        "gate_1_controlled_dataset": {
            "pass": dataset_pass,
            "rows": len(selected),
            "positive": pos,
            "negative": neg,
            "hidden_cells": dict(sorted(cell_counts.items())),
            "validation_errors": len(errors),
        },
        "gate_2_compatibility_signal": {
            "pass": signal_pass,
            "source_auc": source,
            "predicate_family_shortcut_auc": shortcut,
            "compatibility_TG_auc": compat,
            "factorized_TZGQ_auc": factorized,
        },
        "gate_3_geometry_signal": {
            "pass": geometry_pass,
            "source_auc": source,
            "geometry_only_G_auc": geometry,
        },
        "gate_4_hidden_control": {
            "pass": hidden_pass,
            "hidden_cell_auc": hidden_cell,
            "hidden_construction_auc": hidden_construct,
            "hidden_witness_score_auc": hidden_witness,
            "hidden_best_auc": hidden_best,
            "compatibility_TG_auc": compat,
        },
        "overall_interpretation": (
            "attachment_controlled_smoke_passed_promote_to_larger_controlled_mining"
            if dataset_pass and signal_pass and geometry_pass and hidden_pass
            else "attachment_controlled_smoke_diagnostic_only_needs_larger_or_cleaner_target"
        ),
    }


def hidden_cell_fn(row: dict[str, Any]) -> str:
    return hidden_cell(row)


def prediction_rows(rows: list[dict[str, Any]], labels: list[int], preds: dict[str, list[float]]) -> list[dict[str, Any]]:
    output = []
    for idx, row in enumerate(rows):
        output.append(
            {
                "row_id": row["row_id"],
                "group_id": row.get("group_id"),
                "hidden_cell": hidden_cell(row),
                "predicate": row["T_e"]["predicate_label"],
                "label": labels[idx],
                "candidate_relation_text": row["candidate_relation_text"],
                "scores": {name: scores[idx] for name, scores in preds.items()},
            }
        )
    return output


def write_report(path: Path, summary: dict[str, Any], metrics: dict[str, Any], gates: dict[str, Any]) -> None:
    lines = [
        "# H002 Attachment Shortcut-Controlled Smoke V1",
        "",
        f"Date: {summary['created_at']}",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Controlled Slice",
        "",
        f"- rows: `{summary['counts']['controlled_rows']}`",
        f"- positive/negative: `{summary['counts']['controlled_positive']}` / `{summary['counts']['controlled_negative']}`",
        f"- pair groups: `{summary['counts']['controlled_pair_groups']}`",
        f"- validation errors: `{summary['counts']['validation_errors']}`",
        "",
        "## Task A Metrics",
        "",
        "| Model | AUROC | AUPRC |",
        "| --- | ---: | ---: |",
    ]
    for model in [
        "M1_source_only_Z",
        "M2_semantic_source_TZ",
        "M3_geometry_only_G",
        "M4_compatibility_TG",
        "M5_factorized_TZGQ",
        "S1_predicate_family_shortcut",
        "S2_source_rank_shortcut",
        "H0_hidden_cell_only_probe",
        "H1_hidden_construction_probe",
        "H2_hidden_witness_score_probe",
    ]:
        metric = metrics[model]
        lines.append(f"| `{model}` | {metric['auroc']} | {metric['auprc']} |")
    lines.extend(
        [
            "",
            "## Gates",
            "",
            f"- controlled dataset: `{gates['gate_1_controlled_dataset']['pass']}`",
            f"- compatibility signal: `{gates['gate_2_compatibility_signal']['pass']}`",
            f"- geometry signal: `{gates['gate_3_geometry_signal']['pass']}`",
            f"- hidden control: `{gates['gate_4_hidden_control']['pass']}`",
            f"- overall: `{gates['overall_interpretation']}`",
            "",
            "## Boundary",
            "",
            "- train-only controlled diagnostic",
            "- small within-cell balanced slice, not paper evidence",
            "- no validation/test usage",
            "- no paper model trained",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_root = args.input_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(input_root / "attachment_rows.jsonl")
    materialization_summary = read_json(input_root / "summary.json")
    selected, groups, cell_summary = select_within_cell_balanced(rows)
    labels = task_labels(selected)
    errors = validation_errors(input_root, rows, selected, materialization_summary)
    metrics, preds, folds = eval_models(selected, labels, args.folds, args.epochs, args.lr, args.l2)
    gates = gate_summary(metrics, errors, selected)
    by_cell = group_metrics(selected, labels, preds, hidden_cell_fn)
    by_predicate = group_metrics(selected, labels, preds, lambda row: str(row["T_e"]["predicate_label"]))
    cases = []
    cases.extend(error_cases(selected, labels, preds["M4_compatibility_TG"], "M4_compatibility_TG"))
    cases.extend(error_cases(selected, labels, preds["H1_hidden_construction_probe"], "H1_hidden_construction_probe"))

    summary = {
        "schema_version": "h002_attachment_shortcut_controlled_smoke_v1_summary",
        "status": "h002_attachment_shortcut_controlled_smoke_v1_completed" if not errors else "h002_attachment_shortcut_controlled_smoke_v1_input_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_root": rel_path(input_root),
        "output_dir": rel_path(output_dir),
        "materialization_status": materialization_summary.get("status"),
        "counts": {
            "source_attachment_rows": len(rows),
            "source_task_a_rows": len(task_rows(rows)),
            "controlled_rows": len(selected),
            "controlled_positive": sum(labels),
            "controlled_negative": len(labels) - sum(labels),
            "controlled_pair_groups": len(groups),
            "controlled_hidden_cells": len({hidden_cell(row) for row in selected}),
            "validation_errors": len(errors),
        },
        "cell_selection_summary": cell_summary,
        "training": {
            "folds": args.folds,
            "epochs": args.epochs,
            "lr": args.lr,
            "l2": args.l2,
            "implementation": "pure_python_logistic_regression_grouped_cv_within_cell_balanced",
        },
        "gates": gates,
        "boundary": {
            "split": "train_internal_grouped_folds",
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "small_controlled_slice": True,
        },
        "next_todo": (
            "attachment_controlled_expansion_plan_v1"
            if gates["overall_interpretation"] == "attachment_controlled_smoke_passed_promote_to_larger_controlled_mining"
            else "attachment_controlled_failure_analysis_v1"
        ),
    }

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "metrics_by_task.json", {"task_a_controlled_attachment_compatibility": metrics})
    write_json(output_dir / "metrics_by_group.json", {"task_a_by_hidden_cell": by_cell, "task_a_by_predicate": by_predicate})
    write_json(output_dir / "folds.json", {"task_a": folds})
    write_jsonl(output_dir / "controlled_rows.jsonl", selected)
    write_jsonl(output_dir / "controlled_groups.jsonl", groups)
    write_jsonl(output_dir / "predictions.jsonl", prediction_rows(selected, labels, preds))
    write_jsonl(output_dir / "error_cases.jsonl", cases)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", summary, metrics, gates)
    return summary


def main() -> int:
    summary = run(parse_args())
    gates = summary["gates"]
    print(
        "status={status} rows={rows} pos={pos} neg={neg} compat_auc={compat_auc} geom_auc={geom_auc} "
        "source_auc={source_auc} hidden_best_auc={hidden_auc} hidden_pass={hidden_pass} errors={errors} next={next}".format(
            status=summary["status"],
            rows=summary["counts"]["controlled_rows"],
            pos=summary["counts"]["controlled_positive"],
            neg=summary["counts"]["controlled_negative"],
            compat_auc=gates["gate_2_compatibility_signal"]["compatibility_TG_auc"],
            geom_auc=gates["gate_3_geometry_signal"]["geometry_only_G_auc"],
            source_auc=gates["gate_2_compatibility_signal"]["source_auc"],
            hidden_auc=gates["gate_4_hidden_control"]["hidden_best_auc"],
            hidden_pass=gates["gate_4_hidden_control"]["pass"],
            errors=summary["counts"]["validation_errors"],
            next=summary["next_todo"],
        )
    )
    return 0 if summary["counts"]["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
