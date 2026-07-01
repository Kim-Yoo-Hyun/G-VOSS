#!/usr/bin/env python3
"""Run attachment-specific learned smoke baselines for H002.

This is a train-only hypothesis diagnostic over
artifacts/attachment_numeric_geometry_v1. It checks whether attachment
predicate-geometry compatibility has signal beyond source-only and shortcut
probes. Hidden construction probes are reported only as audit controls.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from learned_smoke_runner_v1 import (
    binary_metrics,
    error_cases,
    g_features,
    group_metrics,
    merge_features,
    q_features,
    read_json,
    read_jsonl,
    safe_float,
    t_family_predicate_features,
    t_features,
    train_eval_cv,
    write_json,
    write_jsonl,
    z_features,
    z_scalar_features,
)
from smoke_baseline_runner_v1 import rel_path


H002_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_ROOT = H002_ROOT / "artifacts/attachment_numeric_geometry_v1"
DEFAULT_OUTPUT_DIR = H002_ROOT / "artifacts/attachment_numeric_geometry_smoke_v1"

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


def one_hot(prefix: str, value: Any) -> dict[str, float]:
    text = str(value) if value is not None and value != "" else "missing"
    text = text.replace(" ", "_").replace("/", "_")
    return {f"{prefix}={text}": 1.0}


def hidden_construction_features(row: dict[str, Any]) -> dict[str, float]:
    hidden = row.get("hidden_control", {})
    out: dict[str, float] = {}
    for key in [
        "cell_id_hidden",
        "machine_hint_hidden",
        "geometry_status_hidden",
        "provisional_status_hidden",
        "reason_family_hidden",
        "source_geometry_family_hidden",
        "source_geometry_predicate_hidden",
    ]:
        out.update(one_hot(f"H.{key}", hidden.get(key)))
    return out


def hidden_witness_score_features(row: dict[str, Any]) -> dict[str, float]:
    hidden = row.get("hidden_control", {})
    return {
        "H.attachment_witness_support_score": safe_float(hidden.get("attachment_witness_support_score_hidden"), 0.0),
        "H.attachment_witness_contradiction_score": safe_float(hidden.get("attachment_witness_contradiction_score_hidden"), 0.0),
    }


def attachment_model_feature_fns() -> dict[str, FeatureFn]:
    return {
        "M0_intercept": lambda row: {},
        "M1_source_only_Z": z_features,
        "M2_semantic_source_TZ": lambda row: merge_features(t_features(row), z_features(row)),
        "M3_geometry_only_G": g_features,
        "M4_compatibility_TG": lambda row: merge_features(t_features(row), g_features(row)),
        "M5_factorized_TZGQ": lambda row: merge_features(t_features(row), z_features(row), g_features(row), q_features(row)),
        "S1_predicate_family_shortcut": t_family_predicate_features,
        "S2_source_rank_shortcut": z_scalar_features,
        "H1_hidden_construction_probe": hidden_construction_features,
        "H2_hidden_witness_score_probe": hidden_witness_score_features,
    }


def task_a_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("counterfactual_axis", {}).get("compatibility_label") in {"positive", "counterfactual_negative"}
    ]


def task_a_labels(rows: list[dict[str, Any]]) -> list[int]:
    return [1 if row["counterfactual_axis"]["compatibility_label"] == "positive" else 0 for row in rows]


def task_b_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("observability_axis", {}).get("observability_label") in {"observable", "limited", "insufficient"}
    ]


def task_b_labels(rows: list[dict[str, Any]]) -> list[int]:
    return [1 if row["observability_axis"]["observability_label"] == "observable" else 0 for row in rows]


def task_c_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("reliability_eval_axis", {}).get("binary_usable")
        and row.get("reliability_eval_axis", {}).get("reliability_label") in {"accept", "reject"}
    ]


def task_c_labels(rows: list[dict[str, Any]]) -> list[int]:
    return [1 if row["reliability_eval_axis"]["reliability_label"] == "accept" else 0 for row in rows]


def task_d_connected_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed = {"diagnostic_connected_possible", "diagnostic_connected_ambiguous"}
    return [
        row
        for row in rows
        if row.get("reliability_eval_axis", {}).get("reliability_label") in allowed
    ]


def task_d_connected_labels(rows: list[dict[str, Any]]) -> list[int]:
    return [1 if row["reliability_eval_axis"]["reliability_label"] == "diagnostic_connected_possible" else 0 for row in rows]


def eval_task(
    rows: list[dict[str, Any]],
    labels: list[int],
    task_name: str,
    folds: int,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[dict[str, Any], dict[str, list[float]], dict[str, Any]]:
    metrics: dict[str, Any] = {}
    predictions: dict[str, list[float]] = {}
    fold_records: dict[str, Any] = {}
    for model_name, feature_fn in attachment_model_feature_fns().items():
        result = train_eval_cv(rows, labels, feature_fn, task_name, folds, epochs, lr, l2)
        metrics[model_name] = result["metrics"]
        predictions[model_name] = result["predictions"]
        fold_records[model_name] = result["folds"]
    return metrics, predictions, fold_records


def validation_errors(input_root: Path, rows: list[dict[str, Any]], materialization_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    materialization_errors = input_root / "validation_errors.jsonl"
    if not materialization_errors.exists():
        errors.append({"error_type": "missing_materialization_validation_errors"})
    elif materialization_errors.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "materialization_validation_errors_nonempty"})
    if materialization_summary.get("status") != "h002_attachment_numeric_geometry_v1_ready":
        errors.append({"error_type": "unexpected_materialization_status", "status": materialization_summary.get("status")})
    for row in rows:
        row_id = row.get("row_id")
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_id": row_id, "split": row.get("split")})
        if "Z_e" in row.get("model_views", {}).get("compatibility_main", {}):
            errors.append({"error_type": "Z_e_in_compatibility_main", "row_id": row_id})
        if not row.get("G_e", {}).get("geometry_features"):
            errors.append({"error_type": "missing_numeric_G_e", "row_id": row_id})
    return errors


def count_labels(rows: list[dict[str, Any]], labels: list[int]) -> dict[str, int]:
    return {
        "rows": len(rows),
        "positive": sum(labels),
        "negative": len(labels) - sum(labels),
    }


def metrics_by_hidden_group(
    rows: list[dict[str, Any]],
    labels: list[int],
    predictions: dict[str, list[float]],
    hidden_key: str,
) -> dict[str, Any]:
    return group_metrics(
        rows,
        labels,
        predictions,
        lambda row: str(row.get("hidden_control", {}).get(hidden_key, "missing")),
    )


def gate_summary(task_a: dict[str, Any], errors: list[dict[str, Any]], a_counts: dict[str, int]) -> dict[str, Any]:
    source = task_a["M1_source_only_Z"]["auroc"]
    geometry = task_a["M3_geometry_only_G"]["auroc"]
    compat = task_a["M4_compatibility_TG"]["auroc"]
    factorized = task_a["M5_factorized_TZGQ"]["auroc"]
    shortcut = task_a["S1_predicate_family_shortcut"]["auroc"]
    hidden = task_a["H1_hidden_construction_probe"]["auroc"]
    witness = task_a["H2_hidden_witness_score_probe"]["auroc"]
    hidden_best = max(value for value in [hidden, witness] if value is not None)
    gate_1 = not errors and a_counts["positive"] >= 20 and a_counts["negative"] >= 20
    gate_2 = compat is not None and source is not None and shortcut is not None and compat > source and compat > shortcut
    gate_3 = geometry is not None and source is not None and geometry > source
    severe_hidden_shortcut = hidden_best is not None and compat is not None and hidden_best >= compat - 0.02
    return {
        "gate_1_dataset_sanity": {
            "pass": gate_1,
            "validation_errors": len(errors),
            "task_a_counts": a_counts,
            "note": "Attachment target is imbalanced; gate requires minimum class mass, not exact balance.",
        },
        "gate_2_compatibility_signal": {
            "pass": gate_2,
            "source_auc": source,
            "predicate_family_shortcut_auc": shortcut,
            "compatibility_TG_auc": compat,
            "factorized_TZGQ_auc": factorized,
        },
        "gate_3_geometry_signal": {
            "pass": gate_3,
            "source_auc": source,
            "geometry_only_G_auc": geometry,
        },
        "gate_4_hidden_shortcut_audit": {
            "pass": not severe_hidden_shortcut,
            "hidden_construction_auc": hidden,
            "hidden_witness_score_auc": witness,
            "hidden_best_auc": hidden_best,
            "note": "Hidden probes are not deployable inputs; high hidden score means target construction needs stricter controls.",
        },
        "overall_interpretation": (
            "attachment_smoke_promising_but_requires_hidden_shortcut_review"
            if gate_1 and gate_2 and gate_3
            else "attachment_smoke_diagnostic_only_needs_target_or_feature_repair"
        ),
    }


def predictions_to_jsonl(
    task_name: str,
    rows: list[dict[str, Any]],
    labels: list[int],
    predictions: dict[str, list[float]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        output.append(
            {
                "task": task_name,
                "row_id": row["row_id"],
                "candidate_relation_text": row["candidate_relation_text"],
                "predicate": row["T_e"]["predicate_label"],
                "label": labels[idx],
                "scores": {name: scores[idx] for name, scores in predictions.items()},
            }
        )
    return output


def write_report(path: Path, summary: dict[str, Any], metrics_by_task: dict[str, Any], gates: dict[str, Any]) -> None:
    task_a = metrics_by_task["task_a_attachment_compatibility"]
    rows = [
        "# H002 Attachment Numeric Geometry Smoke V1",
        "",
        f"Date: {summary['created_at']}",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Dataset",
        "",
        f"- attachment rows: `{summary['counts']['attachment_rows']}`",
        f"- Task A compatibility rows: `{summary['counts']['task_a_rows']}`",
        f"- Task A positive/negative: `{summary['counts']['task_a_positive']}` / `{summary['counts']['task_a_negative']}`",
        f"- connected diagnostic rows: `{summary['counts']['task_d_connected_rows']}`",
        f"- validation errors: `{summary['counts']['validation_errors']}`",
        "",
        "## Task A Compatibility",
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
        "H1_hidden_construction_probe",
        "H2_hidden_witness_score_probe",
    ]:
        metric = task_a[model]
        rows.append(f"| `{model}` | {metric['auroc']} | {metric['auprc']} |")
    rows.extend(
        [
            "",
            "## Gates",
            "",
            f"- dataset sanity: `{gates['gate_1_dataset_sanity']['pass']}`",
            f"- compatibility signal: `{gates['gate_2_compatibility_signal']['pass']}`",
            f"- geometry signal: `{gates['gate_3_geometry_signal']['pass']}`",
            f"- hidden shortcut audit pass: `{gates['gate_4_hidden_shortcut_audit']['pass']}`",
            f"- overall: `{gates['overall_interpretation']}`",
            "",
            "## Boundary",
            "",
            "- train-only hypothesis smoke",
            "- pure-Python grouped-fold logistic models",
            "- hidden probes are audit controls only",
            "- no validation/test usage",
            "- no paper-level evidence",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(rows), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    input_root = args.input_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = read_jsonl(input_root / "attachment_rows.jsonl")
    materialization_summary = read_json(input_root / "summary.json")
    errors = validation_errors(input_root, rows, materialization_summary)

    a_rows = task_a_rows(rows)
    a_labels = task_a_labels(a_rows)
    b_rows = task_b_rows(rows)
    b_labels = task_b_labels(b_rows)
    c_rows = task_c_rows(rows)
    c_labels = task_c_labels(c_rows)
    d_rows = task_d_connected_rows(rows)
    d_labels = task_d_connected_labels(d_rows)

    task_a_metrics, task_a_preds, task_a_folds = eval_task(a_rows, a_labels, "task_a", args.folds, args.epochs, args.lr, args.l2)
    task_b_metrics, task_b_preds, task_b_folds = eval_task(b_rows, b_labels, "task_b", args.folds, args.epochs, args.lr, args.l2)
    task_c_metrics, task_c_preds, task_c_folds = eval_task(c_rows, c_labels, "task_c", args.folds, args.epochs, args.lr, args.l2)
    task_d_metrics, task_d_preds, task_d_folds = eval_task(d_rows, d_labels, "task_d", args.folds, args.epochs, args.lr, args.l2)

    metrics_by_task = {
        "task_a_attachment_compatibility": task_a_metrics,
        "task_b_observability": task_b_metrics,
        "task_c_reliability_binary": task_c_metrics,
        "task_d_connected_diagnostic": task_d_metrics,
    }
    metrics_by_group = {
        "task_a_by_predicate": group_metrics(
            a_rows,
            a_labels,
            task_a_preds,
            lambda row: str(row["T_e"]["predicate_label"]),
        ),
        "task_a_by_hidden_cell": metrics_by_hidden_group(a_rows, a_labels, task_a_preds, "cell_id_hidden"),
        "task_a_by_hidden_machine_hint": metrics_by_hidden_group(a_rows, a_labels, task_a_preds, "machine_hint_hidden"),
    }
    a_counts = count_labels(a_rows, a_labels)
    gates = gate_summary(task_a_metrics, errors, a_counts)

    prediction_rows: list[dict[str, Any]] = []
    prediction_rows.extend(predictions_to_jsonl("task_a", a_rows, a_labels, task_a_preds))
    prediction_rows.extend(predictions_to_jsonl("task_b", b_rows, b_labels, task_b_preds))
    prediction_rows.extend(predictions_to_jsonl("task_c", c_rows, c_labels, task_c_preds))
    prediction_rows.extend(predictions_to_jsonl("task_d", d_rows, d_labels, task_d_preds))

    cases = []
    cases.extend(error_cases(a_rows, a_labels, task_a_preds["M4_compatibility_TG"], "M4_compatibility_TG"))
    cases.extend(error_cases(a_rows, a_labels, task_a_preds["M3_geometry_only_G"], "M3_geometry_only_G"))

    summary = {
        "schema_version": "h002_attachment_numeric_geometry_smoke_v1_summary",
        "status": "h002_attachment_numeric_geometry_smoke_v1_completed" if not errors else "h002_attachment_numeric_geometry_smoke_v1_input_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_root": rel_path(input_root),
        "output_dir": rel_path(output_dir),
        "materialization_status": materialization_summary.get("status"),
        "counts": {
            "attachment_rows": len(rows),
            "task_a_rows": len(a_rows),
            "task_a_positive": sum(a_labels),
            "task_a_negative": len(a_labels) - sum(a_labels),
            "task_b_rows": len(b_rows),
            "task_b_observable": sum(b_labels),
            "task_b_not_observable": len(b_labels) - sum(b_labels),
            "task_c_rows": len(c_rows),
            "task_c_accept": sum(c_labels),
            "task_c_reject": len(c_labels) - sum(c_labels),
            "task_d_connected_rows": len(d_rows),
            "task_d_connected_possible": sum(d_labels),
            "task_d_connected_ambiguous": len(d_labels) - sum(d_labels),
            "validation_errors": len(errors),
        },
        "training": {
            "folds": args.folds,
            "epochs": args.epochs,
            "lr": args.lr,
            "l2": args.l2,
            "implementation": "pure_python_logistic_regression_grouped_cv",
        },
        "gates": gates,
        "boundary": {
            "split": "train_internal_grouped_folds",
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "hidden_probes_are_model_inputs": False,
        },
        "next_todo": (
            "attachment_smoke_shortcut_error_analysis_v1"
            if gates["overall_interpretation"] == "attachment_smoke_diagnostic_only_needs_target_or_feature_repair"
            else "attachment_smoke_path_decision_v1"
        ),
    }

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "metrics_by_task.json", metrics_by_task)
    write_json(output_dir / "metrics_by_group.json", metrics_by_group)
    write_json(
        output_dir / "folds.json",
        {
            "task_a": task_a_folds,
            "task_b": task_b_folds,
            "task_c": task_c_folds,
            "task_d": task_d_folds,
        },
    )
    write_jsonl(output_dir / "predictions.jsonl", prediction_rows)
    write_jsonl(output_dir / "error_cases.jsonl", cases)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", summary, metrics_by_task, gates)
    return summary


def main() -> int:
    summary = run(parse_args())
    gate = summary["gates"]["gate_2_compatibility_signal"]
    hidden = summary["gates"]["gate_4_hidden_shortcut_audit"]
    print(
        "status={status} task_a={task_a} pos={pos} neg={neg} compat_auc={compat_auc} "
        "geom_auc={geom_auc} source_auc={source_auc} shortcut_auc={shortcut_auc} hidden_auc={hidden_auc} "
        "errors={errors} next={next}".format(
            status=summary["status"],
            task_a=summary["counts"]["task_a_rows"],
            pos=summary["counts"]["task_a_positive"],
            neg=summary["counts"]["task_a_negative"],
            compat_auc=gate["compatibility_TG_auc"],
            geom_auc=summary["gates"]["gate_3_geometry_signal"]["geometry_only_G_auc"],
            source_auc=gate["source_auc"],
            shortcut_auc=gate["predicate_family_shortcut_auc"],
            hidden_auc=hidden["hidden_best_auc"],
            errors=summary["counts"]["validation_errors"],
            next=summary["next_todo"],
        )
    )
    return 0 if summary["counts"]["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
