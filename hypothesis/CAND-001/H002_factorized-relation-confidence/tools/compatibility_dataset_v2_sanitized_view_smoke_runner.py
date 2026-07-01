#!/usr/bin/env python3
"""Run train-only learned smoke on H002 compatibility dataset v2 smoke-ready view."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from learned_smoke_runner_v1 import (
    binary_metrics,
    group_metrics,
    merge_features,
    one_hot,
    rel_path,
    safe_float,
    train_eval_cv,
    write_json,
    write_jsonl,
)


H2_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_sanitized_view_smoke_plan"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_sanitized_view_smoke_runner"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v2_sanitized_view_smoke_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v2_sanitized_view_smoke_runner"

SCHEMA_VERSION = "h002_compatibility_dataset_v2_sanitized_view_smoke_runner_v1"
STATUS_ERRORS = "h002_compatibility_dataset_v2_sanitized_view_smoke_runner_input_errors"
STATUS_PASSED = "h002_compatibility_dataset_v2_sanitized_view_smoke_runner_passed_controls"
STATUS_DIAGNOSTIC = "h002_compatibility_dataset_v2_sanitized_view_smoke_runner_diagnostic_only_failed_controls"
NEXT_TODO_PASSED = "compatibility_dataset_v2_result_review_and_failure_analysis"
NEXT_TODO_DIAGNOSTIC = "compatibility_dataset_v2_failure_analysis"

FeatureFn = Callable[[dict[str, Any]], dict[str, float]]

BLOCKED_TOKENS = [
    "source_score_inherited_for_counterfactual",
    "generated_counterfactual",
    "evidence_conflict_flag",
    "geometry_source",
    "counterfactual_type",
    "relation_source",
    "geometry_status_baseline",
    "hidden_control",
    "row_role",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=500)
    parser.add_argument("--lr", type=float, default=0.08)
    parser.add_argument("--l2", type=float, default=0.001)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def t_features(row: dict[str, Any]) -> dict[str, float]:
    t = row.get("T_e", {})
    out: dict[str, float] = {}
    out.update(one_hot("T.family", t.get("relation_family")))
    out.update(one_hot("T.predicate", t.get("predicate_label")))
    out.update(one_hot("T.subject", t.get("subject_label")))
    out.update(one_hot("T.object", t.get("object_label")))
    return out


def t_family_predicate_features(row: dict[str, Any]) -> dict[str, float]:
    t = row.get("T_e", {})
    out: dict[str, float] = {}
    out.update(one_hot("T.family", t.get("relation_family")))
    out.update(one_hot("T.predicate", t.get("predicate_label")))
    return out


def object_pair_features(row: dict[str, Any]) -> dict[str, float]:
    t = row.get("T_e", {})
    out: dict[str, float] = {}
    out.update(one_hot("T.subject", t.get("subject_label")))
    out.update(one_hot("T.object", t.get("object_label")))
    out.update(one_hot("T.subject_object", t.get("subject_object_text")))
    return out


def z_features(row: dict[str, Any]) -> dict[str, float]:
    z = row.get("Z_e_safe", {})
    rank = safe_float(z.get("source_rank"), 999.0)
    score = safe_float(z.get("source_score_normalized"), 0.5)
    out: dict[str, float] = {
        "Z.source_score_normalized": score,
        "Z.source_score_raw": safe_float(z.get("source_score_raw"), 0.0),
        "Z.source_score_missing": 0.0 if z.get("source_score_available") else 1.0,
        "Z.source_rank_inverse": 1.0 / (1.0 + max(rank, 0.0)),
        "Z.source_rank": max(rank, 0.0),
    }
    out.update(one_hot("Z.source_id", z.get("source_id")))
    out.update(one_hot("Z.rank_band", z.get("source_rank_band")))
    return out


def z_scalar_features(row: dict[str, Any]) -> dict[str, float]:
    z = row.get("Z_e_safe", {})
    rank = safe_float(z.get("source_rank"), 999.0)
    return {
        "Z.source_score_normalized": safe_float(z.get("source_score_normalized"), 0.5),
        "Z.source_rank_inverse": 1.0 / (1.0 + max(rank, 0.0)),
        "Z.source_rank": max(rank, 0.0),
    }


def g_features_from_dict(features: dict[str, Any]) -> dict[str, float]:
    return {f"G.{key}": safe_float(value, 0.0) for key, value in sorted(features.items())}


def g_features(row: dict[str, Any]) -> dict[str, float]:
    return g_features_from_dict(row.get("G_e_numeric", {}))


def q_features(row: dict[str, Any]) -> dict[str, float]:
    q = row.get("Q_e_safe", {})
    out: dict[str, float] = {
        "Q.missing_geometry": 1.0 if q.get("missing_geometry_flag") else 0.0,
        "Q.low_coverage": 1.0 if q.get("low_coverage_flag") else 0.0,
        "Q.unsupported_family": 1.0 if q.get("unsupported_family_flag") else 0.0,
        "Q.raw_feature_missing_count": safe_float(q.get("raw_feature_missing_count"), 0.0),
        "Q.geometry_available": 1.0 if q.get("geometry_available") else 0.0,
        "Q.geometry_checkable": 1.0 if q.get("geometry_checkable") else 0.0,
    }
    out.update(one_hot("Q.asset_tier", q.get("asset_tier")))
    for key, value in sorted((q.get("coverage_features") or {}).items()):
        out[f"Q.coverage.{key}"] = safe_float(value, 0.0)
    return out


def wrong_predicate(value: str) -> str:
    if value == "higher than":
        return "lower than"
    if value == "lower than":
        return "higher than"
    order = ["lying on", "standing on", "supported by"]
    if value in order:
        return order[(order.index(value) + 1) % len(order)]
    return f"wrong_{value}"


def wrong_t_features(row: dict[str, Any]) -> dict[str, float]:
    t = dict(row.get("T_e", {}))
    t["predicate_label"] = wrong_predicate(str(t.get("predicate_label") or ""))
    out: dict[str, float] = {}
    out.update(one_hot("T.family", t.get("relation_family")))
    out.update(one_hot("T.predicate", t.get("predicate_label")))
    out.update(one_hot("T.subject", t.get("subject_label")))
    out.update(one_hot("T.object", t.get("object_label")))
    return out


def stable_order_key(row: dict[str, Any]) -> tuple[str, str]:
    return (str(row.get("T_e", {}).get("relation_family")), str(row.get("row_id")))


def shuffled_g_by_row(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_family[str(row.get("T_e", {}).get("relation_family"))].append(row)
    out: dict[str, dict[str, Any]] = {}
    for _, family_rows in by_family.items():
        ordered = sorted(family_rows, key=stable_order_key)
        if len(ordered) == 1:
            out[str(ordered[0]["row_id"])] = dict(ordered[0].get("G_e_numeric", {}))
            continue
        shift = max(1, len(ordered) // 2 + 1)
        for idx, row in enumerate(ordered):
            donor = ordered[(idx + shift) % len(ordered)]
            if donor["row_id"] == row["row_id"]:
                donor = ordered[(idx + 1) % len(ordered)]
            out[str(row["row_id"])] = dict(donor.get("G_e_numeric", {}))
    return out


def model_feature_fns(rows: list[dict[str, Any]]) -> dict[str, FeatureFn]:
    shuffled_g = shuffled_g_by_row(rows)
    return {
        "M0_intercept": lambda row: {},
        "M1_source_only_Z_safe": z_features,
        "M2_semantic_only_T": t_features,
        "M3_semantic_source_TZ_safe": lambda row: merge_features(t_features(row), z_features(row)),
        "M4_geometry_numeric_G": g_features,
        "M5_compatibility_TG_numeric": lambda row: merge_features(t_features(row), g_features(row)),
        "M6_factorized_sanitized_TZGQ": lambda row: merge_features(t_features(row), z_features(row), g_features(row), q_features(row)),
        "S1_predicate_family_shortcut": t_family_predicate_features,
        "S2_source_score_rank_shortcut": z_scalar_features,
        "S3_object_label_pair_shortcut": object_pair_features,
        "C1_shuffled_G_within_family_control": lambda row: merge_features(
            t_features(row),
            g_features_from_dict(shuffled_g[str(row["row_id"])]),
        ),
        "C2_wrong_T_same_G_control": lambda row: merge_features(wrong_t_features(row), g_features(row)),
    }


def labels(rows: list[dict[str, Any]]) -> list[int]:
    return [int(row["y_compatibility"]) for row in rows]


def eval_models(
    rows: list[dict[str, Any]],
    fold_count: int,
    epochs: int,
    lr: float,
    l2: float,
) -> tuple[dict[str, Any], dict[str, list[float]], dict[str, Any]]:
    y = labels(rows)
    metrics: dict[str, Any] = {}
    predictions: dict[str, list[float]] = {}
    folds: dict[str, Any] = {}
    for name, feature_fn in model_feature_fns(rows).items():
        result = train_eval_cv(rows, y, feature_fn, "task_a", fold_count, epochs, lr, l2)
        metrics[name] = result["metrics"]
        predictions[name] = result["predictions"]
        folds[name] = result["folds"]
    return metrics, predictions, folds


def paired_score_drop(rows: list[dict[str, Any]], predictions: dict[str, list[float]]) -> dict[str, Any]:
    group_indices: dict[str, list[int]] = defaultdict(list)
    y = labels(rows)
    for idx, row in enumerate(rows):
        group_indices[str(row.get("group_id"))].append(idx)
    out: dict[str, Any] = {}
    for model_name, scores in predictions.items():
        drops: list[float] = []
        for indices in group_indices.values():
            pos = [idx for idx in indices if y[idx] == 1]
            neg = [idx for idx in indices if y[idx] == 0]
            if len(pos) == 1 and len(neg) == 1:
                drops.append(scores[pos[0]] - scores[neg[0]])
        out[model_name] = {
            "groups": len(drops),
            "mean_positive_minus_negative": round(mean(drops), 6) if drops else None,
            "positive_drop_fraction": round(sum(1 for value in drops if value > 0.0) / len(drops), 6) if drops else None,
        }
    return out


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    y = labels(rows)
    by_group: dict[str, list[int]] = defaultdict(list)
    for row, label in zip(rows, y):
        by_group[str(row.get("group_id"))].append(label)
    by_family = Counter()
    by_predicate = Counter()
    for row, label in zip(rows, y):
        family = row.get("T_e", {}).get("relation_family")
        predicate = row.get("T_e", {}).get("predicate_label")
        name = "positive" if label else "negative"
        by_family[f"{family}|{name}"] += 1
        by_predicate[f"{family}|{predicate}|{name}"] += 1
    return {
        "rows": len(rows),
        "positive": sum(y),
        "negative": len(y) - sum(y),
        "groups": len(by_group),
        "paired_groups_with_one_positive_one_negative": sum(1 for vals in by_group.values() if sorted(vals) == [0, 1]),
        "by_family_label": dict(sorted(by_family.items())),
        "by_predicate_label": dict(sorted(by_predicate.items())),
    }


def validate(plan_dir: Path, plan_summary: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan_summary.get("validation_errors")})
    if (plan_dir / "validation_errors.jsonl").exists() and (plan_dir / "validation_errors.jsonl").read_text(encoding="utf-8").strip():
        errors.append({"error_type": "plan_validation_errors_nonempty"})
    counts = count_summary(rows)
    if counts["rows"] != 400 or counts["positive"] != 200 or counts["negative"] != 200:
        errors.append({"error_type": "unexpected_counts", **counts})
    if counts["paired_groups_with_one_positive_one_negative"] != 200:
        errors.append({"error_type": "unexpected_group_pairing", **counts})
    for row in rows:
        row_id = row.get("row_id")
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_row", "row_id": row_id})
        text = json.dumps(row.get("model_views", {}), ensure_ascii=False)
        for token in BLOCKED_TOKENS:
            if token in text:
                errors.append({"error_type": "blocked_token_in_model_views", "row_id": row_id, "token": token})
        if "source_score_inherited_for_counterfactual" in row.get("Z_e_safe", {}):
            errors.append({"error_type": "inherited_flag_in_Z_e_safe", "row_id": row_id})
    return errors


def gate_summary(metrics: dict[str, Any], drops: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    def auc(name: str) -> float:
        value = metrics.get(name, {}).get("auroc")
        return 0.0 if value is None else float(value)

    m5 = auc("M5_compatibility_TG_numeric")
    m1 = auc("M1_source_only_Z_safe")
    m2 = auc("M2_semantic_only_T")
    m3 = auc("M3_semantic_source_TZ_safe")
    m4 = auc("M4_geometry_numeric_G")
    m6 = auc("M6_factorized_sanitized_TZGQ")
    s1 = auc("S1_predicate_family_shortcut")
    s2 = auc("S2_source_score_rank_shortcut")
    s3 = auc("S3_object_label_pair_shortcut")
    c1 = auc("C1_shuffled_G_within_family_control")
    c2 = auc("C2_wrong_T_same_G_control")
    best_non_geometry_shortcut = max(m1, m2, m3, s1, s2, s3)
    best_primary_control = max(c1, c2)
    m5_drop = drops.get("M5_compatibility_TG_numeric", {}).get("mean_positive_minus_negative") or 0.0
    gate_dataset = not errors
    gate_shortcut = m5 > best_non_geometry_shortcut + 0.03
    gate_predicate_conditioning = m5 > m4 + 0.03
    gate_corruption = m5 > best_primary_control + 0.03 and m5_drop > 0.0
    gate_family_reported = True
    passed = gate_dataset and gate_shortcut and gate_predicate_conditioning and gate_corruption and gate_family_reported
    return {
        "gate_dataset_sanity": {
            "pass": gate_dataset,
            "validation_errors": len(errors),
        },
        "gate_against_source_semantic_shortcuts": {
            "pass": gate_shortcut,
            "M5_compatibility_TG_numeric": m5,
            "best_non_geometry_shortcut": best_non_geometry_shortcut,
            "source_only": m1,
            "semantic_only": m2,
            "semantic_source": m3,
            "predicate_family_shortcut": s1,
            "source_score_rank_shortcut": s2,
            "object_pair_shortcut": s3,
        },
        "gate_predicate_conditioning_over_geometry_only": {
            "pass": gate_predicate_conditioning,
            "M5_compatibility_TG_numeric": m5,
            "M4_geometry_numeric_G": m4,
        },
        "gate_corruption_controls": {
            "pass": gate_corruption,
            "M5_compatibility_TG_numeric": m5,
            "C1_shuffled_G_within_family_control": c1,
            "C2_wrong_T_same_G_control": c2,
            "M5_mean_positive_minus_negative": m5_drop,
        },
        "factorized_not_primary": {
            "M6_factorized_sanitized_TZGQ": m6,
            "interpretation": "M6 is an ablation in this v2 smoke because Q_e_safe is mostly constant coverage.",
        },
        "overall_pass": passed,
        "overall_interpretation": (
            "sanitized_view_smoke_passed_controls"
            if passed
            else "sanitized_view_smoke_diagnostic_only_failed_controls"
        ),
    }


def prediction_rows(rows: list[dict[str, Any]], predictions: dict[str, list[float]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        item = {
            "row_id": row.get("row_id"),
            "group_id": row.get("group_id"),
            "label": row.get("y_compatibility"),
            "family": row.get("T_e", {}).get("relation_family"),
            "predicate": row.get("T_e", {}).get("predicate_label"),
        }
        for model, scores in predictions.items():
            item[model] = scores[idx]
        out.append(item)
    return out


def error_cases(rows: list[dict[str, Any]], scores: list[float], max_cases: int = 30) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for row, score in zip(rows, scores):
        label = int(row["y_compatibility"])
        pred = 1 if score >= 0.5 else 0
        if pred == label:
            continue
        cases.append(
            {
                "row_id": row.get("row_id"),
                "group_id": row.get("group_id"),
                "family": row.get("T_e", {}).get("relation_family"),
                "predicate": row.get("T_e", {}).get("predicate_label"),
                "subject": row.get("T_e", {}).get("subject_label"),
                "object": row.get("T_e", {}).get("object_label"),
                "label": label,
                "prediction": pred,
                "score": round(score, 6),
                "source_score": row.get("Z_e_safe", {}).get("source_score_normalized"),
                "source_rank_band": row.get("Z_e_safe", {}).get("source_rank_band"),
            }
        )
    return sorted(cases, key=lambda item: abs(float(item["score"]) - 0.5), reverse=True)[:max_cases]


def write_report(path: Path, summary: dict[str, Any], metrics: dict[str, Any], gates: dict[str, Any]) -> None:
    order = [
        "M1_source_only_Z_safe",
        "M2_semantic_only_T",
        "M3_semantic_source_TZ_safe",
        "M4_geometry_numeric_G",
        "M5_compatibility_TG_numeric",
        "M6_factorized_sanitized_TZGQ",
        "S1_predicate_family_shortcut",
        "S2_source_score_rank_shortcut",
        "S3_object_label_pair_shortcut",
        "C1_shuffled_G_within_family_control",
        "C2_wrong_T_same_G_control",
    ]
    lines = [
        "# Compatibility Dataset V2 Sanitized View Smoke Runner",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v2_sanitized_view_smoke_runner/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"positive / negative = {summary['counts']['positive']} / {summary['counts']['negative']}",
        f"validation_errors = {summary['validation_errors']}",
        f"overall = {gates['overall_interpretation']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Task A Metrics",
        "",
        "| Model | AUROC | AUPRC | Accuracy |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name in order:
        metric = metrics[name]
        lines.append(f"| `{name}` | {metric.get('auroc')} | {metric.get('auprc')} | {metric.get('accuracy_at_0_5')} |")
    lines.extend(
        [
            "",
            "## Gates",
            "",
            f"- dataset sanity: `{gates['gate_dataset_sanity']['pass']}`",
            f"- against source/semantic shortcuts: `{gates['gate_against_source_semantic_shortcuts']['pass']}`",
            f"- predicate conditioning over geometry-only: `{gates['gate_predicate_conditioning_over_geometry_only']['pass']}`",
            f"- corruption controls: `{gates['gate_corruption_controls']['pass']}`",
            "",
            "## Interpretation",
            "",
            "This is train-only hypothesis evidence. It is not paper-level evidence and does not train a",
            "deployable model. The result is promotable only if the primary compatibility model beats",
            "source/semantic shortcuts and degrades under shuffled-geometry and wrong-predicate controls.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    rows = read_jsonl(args.plan_dir / "smoke_ready_view.jsonl")
    errors = validate(args.plan_dir, plan_summary, rows)
    metrics, predictions, folds = eval_models(rows, args.folds, args.epochs, args.lr, args.l2)
    drops = paired_score_drop(rows, predictions)
    y = labels(rows)
    metrics_by_family = group_metrics(rows, y, predictions, lambda row: str(row.get("T_e", {}).get("relation_family")))
    metrics_by_predicate = group_metrics(rows, y, predictions, lambda row: str(row.get("T_e", {}).get("predicate_label")))
    gates = gate_summary(metrics, drops, errors)

    status = STATUS_ERRORS if errors else (STATUS_PASSED if gates["overall_pass"] else STATUS_DIAGNOSTIC)
    next_todo = NEXT_TODO_PASSED if gates["overall_pass"] else NEXT_TODO_DIAGNOSTIC
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "plan_root": rel_path(args.plan_dir),
        "output_root": rel_path(args.output_dir),
        "counts": count_summary(rows),
        "validation_errors": len(errors),
        "folds": args.folds,
        "epochs": args.epochs,
        "lr": args.lr,
        "l2": args.l2,
        "learned_smoke_executed": True,
        "paper_evidence_allowed": False,
        "boundary": {
            "split": "train_internal_grouped_by_group_id",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "raw_construction_metadata_used_as_feature": False,
        },
        "key_metrics": {
            name: metrics[name]
            for name in [
                "M1_source_only_Z_safe",
                "M2_semantic_only_T",
                "M3_semantic_source_TZ_safe",
                "M4_geometry_numeric_G",
                "M5_compatibility_TG_numeric",
                "M6_factorized_sanitized_TZGQ",
                "S1_predicate_family_shortcut",
                "S2_source_score_rank_shortcut",
                "S3_object_label_pair_shortcut",
                "C1_shuffled_G_within_family_control",
                "C2_wrong_T_same_G_control",
            ]
        },
        "gates": gates,
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "metrics": rel_path(args.output_dir / "metrics.json"),
            "metrics_by_family": rel_path(args.output_dir / "metrics_by_family.json"),
            "paired_score_drop": rel_path(args.output_dir / "paired_score_drop.json"),
            "folds": rel_path(args.output_dir / "folds.json"),
            "predictions": rel_path(args.output_dir / "predictions.jsonl"),
            "error_cases": rel_path(args.output_dir / "error_cases_m5.jsonl"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "metrics.json", metrics)
    write_json(args.output_dir / "metrics_by_family.json", {"family": metrics_by_family, "predicate": metrics_by_predicate})
    write_json(args.output_dir / "paired_score_drop.json", drops)
    write_json(args.output_dir / "folds.json", folds)
    write_jsonl(args.output_dir / "predictions.jsonl", prediction_rows(rows, predictions))
    write_jsonl(args.output_dir / "error_cases_m5.jsonl", error_cases(rows, predictions["M5_compatibility_TG_numeric"]))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, metrics, gates)


if __name__ == "__main__":
    main()
