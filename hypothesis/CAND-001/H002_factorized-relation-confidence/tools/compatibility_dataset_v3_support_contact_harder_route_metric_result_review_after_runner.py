#!/usr/bin/env python3
"""Review support/contact hard-route metric results after the Docker runner."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_REVIEW_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment"
)
DEFAULT_RUNTIME_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest"
DEFAULT_TRAIN_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze"
)
DEFAULT_OFFICIAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/support_contact_harder_materialization/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / (
    "artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_result_review_after_runner"
)

EXPECTED_RUNNER_REVIEW_STATUS = "h002_support_contact_harder_route_metric_runner_after_train_eval_alignment_ready"
EXPECTED_RUNNER_REVIEW_NEXT = "compatibility_dataset_v3_support_contact_harder_route_metric_result_review_after_runner"

SCHEMA_VERSION = "h002_support_contact_harder_route_metric_result_review_after_runner_v1"
STATUS_READY = "h002_support_contact_harder_route_metric_result_review_after_runner_ready"
STATUS_ERRORS = "h002_support_contact_harder_route_metric_result_review_after_runner_input_errors"
SELECTED_PATH = "freeze_support_contact_harder_route_as_diagnostic_failure_taxonomy"
NEXT_TODO = "compatibility_dataset_v3_support_contact_harder_route_path_decision_after_result_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-review-dir", type=Path, default=DEFAULT_RUNNER_REVIEW_DIR)
    parser.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME_DIR)
    parser.add_argument("--train-dir", type=Path, default=DEFAULT_TRAIN_DIR)
    parser.add_argument("--official-dir", type=Path, default=DEFAULT_OFFICIAL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def target(row: dict[str, Any]) -> int:
    return int(row.get("target_y", row.get("labels", {}).get("C_e", 0)))


def predicate(row: dict[str, Any]) -> str:
    return str(row.get("predicate_label") or row.get("feature_blocks", {}).get("T_e", {}).get("predicate_label") or "")


def g_value(row: dict[str, Any], key: str) -> float | None:
    value = (
        row.get("feature_blocks", {})
        .get("G_e", {})
        .get("g_e_feature_vector", {})
        .get(key)
    )
    return as_float(value)


def metric_lookup(rows: list[dict[str, str]], view_id: str, level: str | None = "overall") -> dict[str, str]:
    for row in rows:
        if row.get("view_id") != view_id:
            continue
        if level is None or row.get("level", "overall") == level:
            return row
    return {}


def count_targets(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter((predicate(row), target(row)) for row in rows)
    out: list[dict[str, Any]] = []
    for pred in ["standing on", "lying on"]:
        for y in [1, 0]:
            out.append({"predicate_label": pred, "target_y": y, "rows": counts.get((pred, y), 0)})
    return out


def score_direction_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    views = ["M4_TxG_compatibility", "C1_wrong_T_same_route", "A1_class_ablation", "M2_geometry_only"]
    buckets: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    for row in score_rows:
        pred = str(row.get("predicate_label"))
        y = int(row.get("target_y", 0))
        scores = row.get("scores", {})
        for view in views:
            value = as_float(scores.get(view))
            if value is not None:
                buckets[(view, pred, y)].append(value)
    for view in views:
        for pred in ["standing on", "lying on"]:
            pos = buckets.get((view, pred, 1), [])
            neg = buckets.get((view, pred, 0), [])
            rows.append(
                {
                    "view_id": view,
                    "predicate_label": pred,
                    "positive_rows": len(pos),
                    "positive_mean_score": sum(pos) / len(pos) if pos else None,
                    "negative_rows": len(neg),
                    "negative_mean_score": sum(neg) / len(neg) if neg else None,
                    "positive_minus_negative": (sum(pos) / len(pos) - sum(neg) / len(neg)) if pos and neg else None,
                }
            )
    return rows


def feature_mean_rows(train_rows: list[dict[str, Any]], official_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    features = [
        "subject_vertical_extent_ratio",
        "subject_principal_axis_upness",
        "subject_normal_upness",
        "support_contact_likelihood_proxy",
        "xy_overlap_min_ratio",
        "surface_gap_subject_bottom_to_object_top",
        "center_delta_z",
    ]
    rows: list[dict[str, Any]] = []
    for dataset_name, source_rows in [("train_aligned", train_rows), ("official_validation", official_rows)]:
        values: dict[tuple[str, int, str], list[float]] = defaultdict(list)
        for row in source_rows:
            pred = predicate(row)
            y = target(row)
            for feature in features:
                value = g_value(row, feature)
                if value is not None:
                    values[(pred, y, feature)].append(value)
        for pred in ["standing on", "lying on"]:
            for y in [1, 0]:
                for feature in features:
                    arr = values.get((pred, y, feature), [])
                    rows.append(
                        {
                            "dataset": dataset_name,
                            "predicate_label": pred,
                            "target_y": y,
                            "feature": feature,
                            "rows": len(arr),
                            "mean": sum(arr) / len(arr) if arr else None,
                            "min": min(arr) if arr else None,
                            "max": max(arr) if arr else None,
                        }
                    )
    return rows


def root_cause_rows(
    official_m4: float | None,
    official_wrong_t: float | None,
    official_m2: float | None,
    paired_m4: float | None,
    paired_wrong_t: float | None,
    drift_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    drift_lookup = {row.get("feature"): row for row in drift_rows}
    support_drift = as_float(drift_lookup.get("support_contact_likelihood_proxy", {}).get("official_outside_train_range_rate"))
    overlap_drift = as_float(drift_lookup.get("xy_overlap_min_ratio", {}).get("official_outside_train_range_rate"))
    rows = [
        {
            "cause": "wrong_T_inversion",
            "severity": "high",
            "evidence": f"M4 AUROC={official_m4}, wrong-T AUROC={official_wrong_t}, paired M4={paired_m4}, paired wrong-T={paired_wrong_t}",
            "interpretation": "The official validation score direction is effectively inverted; correct-T does worse than wrong-T.",
            "decision": "blocks_support_contact_success_claim",
        },
        {
            "cause": "train_official_feature_distribution_shift",
            "severity": "high",
            "evidence": f"support_contact_likelihood_proxy outside train range={support_drift}; xy_overlap_min_ratio outside train range={overlap_drift}",
            "interpretation": "Train-aligned support/contact rows and official validation rows are not drawn from the same G_e distribution.",
            "decision": "requires_feature_target_contract_redesign_before_any_retry",
        },
        {
            "cause": "official_counterfactual_target_semantics",
            "severity": "medium_high",
            "evidence": "Official rows pair GT support/contact predicate with the same-geometry opposite predicate; train rows came from prior point/multiview hard-route materialization.",
            "interpretation": "The learned train convention does not transfer to the official GT-counterfactual convention.",
            "decision": "do_not_flip_scores_post_hoc; inspect target semantics instead",
        },
        {
            "cause": "geometry_only_not_enough",
            "severity": "medium",
            "evidence": f"official geometry-only AUROC={official_m2}",
            "interpretation": "The richer G_e does not by itself solve support/contact on official validation.",
            "decision": "support_contact_remains_hard_route_diagnostic",
        },
    ]
    return rows


def validate_inputs(runner_summary: dict[str, Any], runtime_dir: Path, train_rows: list[dict[str, Any]], official_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if runner_summary.get("status") != EXPECTED_RUNNER_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_runner_review_status", "actual": runner_summary.get("status")})
    if runner_summary.get("next_todo") != EXPECTED_RUNNER_REVIEW_NEXT:
        errors.append({"error_type": "unexpected_runner_review_next_todo", "actual": runner_summary.get("next_todo")})
    if runner_summary.get("validation_errors") != 0:
        errors.append({"error_type": "runner_review_validation_errors", "actual": runner_summary.get("validation_errors")})
    if line_count(runtime_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "runtime_validation_errors_file_not_empty"})
    if len(train_rows) != 640:
        errors.append({"error_type": "unexpected_train_aligned_rows", "actual": len(train_rows), "expected": 640})
    if len(official_rows) != 3178:
        errors.append({"error_type": "unexpected_official_rows", "actual": len(official_rows), "expected": 3178})
    return errors


def run(args: argparse.Namespace) -> dict[str, Any]:
    out_dir = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    runner_summary = read_json(args.runner_review_dir / "summary.json")
    runtime_manifest = read_json(args.runtime_dir / "eval_manifest.json")
    official_metrics = read_csv(args.runtime_dir / "official_metrics.csv")
    dev_metrics = read_csv(args.runtime_dir / "dev_metrics.csv")
    paired_metrics = read_csv(args.runtime_dir / "paired_group_metrics.csv")
    control_metrics = read_csv(args.runtime_dir / "control_metrics.csv")
    feature_drift = read_csv(args.runner_review_dir / "feature_drift.csv")
    train_rows = read_jsonl(args.train_dir / "model_safe_no_class_train_dev.jsonl")
    official_rows = read_jsonl(args.official_dir / "model_safe_main_no_class.jsonl")
    score_rows = read_jsonl(args.runtime_dir / "prediction_scores.jsonl")

    errors = validate_inputs(runner_summary, args.runtime_dir, train_rows, official_rows)

    m4 = metric_lookup(official_metrics, "M4_TxG_compatibility")
    m2 = metric_lookup(official_metrics, "M2_geometry_only")
    wrong_t = metric_lookup(official_metrics, "C1_wrong_T_same_route")
    dev_m4 = metric_lookup(dev_metrics, "M4_TxG_compatibility")
    paired_m4 = metric_lookup(paired_metrics, "M4_TxG_compatibility", level=None)
    paired_wrong_t = metric_lookup(paired_metrics, "C1_wrong_T_same_route", level=None)

    official_m4_auroc = as_float(m4.get("auroc"))
    official_wrong_t_auroc = as_float(wrong_t.get("auroc"))
    official_m2_auroc = as_float(m2.get("auroc"))
    paired_m4_acc = as_float(paired_m4.get("paired_group_accuracy"))
    paired_wrong_t_acc = as_float(paired_wrong_t.get("paired_group_accuracy"))

    target_rows = []
    for dataset_name, rows in [("train_aligned", train_rows), ("official_validation", official_rows)]:
        for row in count_targets(rows):
            row["dataset"] = dataset_name
            target_rows.append(row)

    score_rows_out = score_direction_rows(score_rows)
    feature_rows = feature_mean_rows(train_rows, official_rows)
    root_causes = root_cause_rows(
        official_m4_auroc,
        official_wrong_t_auroc,
        official_m2_auroc,
        paired_m4_acc,
        paired_wrong_t_acc,
        feature_drift,
    )

    gate_rows = [
        {
            "gate": "official_M4_beats_geometry_only",
            "status": "fail" if official_m4_auroc is not None and official_m2_auroc is not None and official_m4_auroc <= official_m2_auroc else "pass",
            "evidence": f"M4={official_m4_auroc}, M2={official_m2_auroc}",
        },
        {
            "gate": "wrong_T_control_degrades",
            "status": "fail" if official_wrong_t_auroc is not None and official_m4_auroc is not None and official_wrong_t_auroc >= official_m4_auroc else "pass",
            "evidence": f"M4={official_m4_auroc}, wrong_T={official_wrong_t_auroc}",
        },
        {
            "gate": "paired_group_correct_T_preferred",
            "status": "fail" if paired_m4_acc is not None and paired_m4_acc < 0.5 else "pass",
            "evidence": f"paired_M4={paired_m4_acc}, paired_wrong_T={paired_wrong_t_acc}",
        },
        {
            "gate": "support_contact_paper_success",
            "status": "fail",
            "evidence": "support/contact hard route is inverted on official validation and remains diagnostic only",
        },
    ]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "validation_errors": len(errors),
        "selected_path": SELECTED_PATH if not errors else "blocked_fix_inputs",
        "next_todo": NEXT_TODO if not errors else "fix_support_contact_harder_route_metric_review_inputs",
        "input_artifacts": {
            "runner_review_summary": rel_path(args.runner_review_dir / "summary.json"),
            "runtime_manifest": rel_path(args.runtime_dir / "eval_manifest.json"),
            "train_aligned_view": rel_path(args.train_dir / "model_safe_no_class_train_dev.jsonl"),
            "official_validation_view": rel_path(args.official_dir / "model_safe_main_no_class.jsonl"),
        },
        "primary_findings": {
            "internal_dev_m4_auroc": as_float(dev_m4.get("auroc")),
            "official_m4_auroc": official_m4_auroc,
            "official_geometry_only_auroc": official_m2_auroc,
            "official_wrong_t_auroc": official_wrong_t_auroc,
            "paired_m4_accuracy": paired_m4_acc,
            "paired_wrong_t_accuracy": paired_wrong_t_acc,
            "official_m4_inverted_auc": 1.0 - official_m4_auroc if official_m4_auroc is not None else None,
        },
        "decision": {
            "current_direction_wrong": False,
            "support_contact_harder_route_success": False,
            "support_contact_solved_claim_allowed": False,
            "paper_metric_promoted": False,
            "official_test_usage": False,
            "do_not_posthoc_flip_scores": True,
            "keep_h002_core_routes": True,
            "freeze_support_contact_harder_route_as_diagnostic": True,
            "requires_target_feature_contract_redesign_for_retry": True,
        },
        "reasoning": {
            "why_not_wrong_direction": (
                "The failure is localized to the support/contact hard route transfer. It does not invalidate "
                "the broader H002 principle that T_e and G_e must be separated and tested with controls."
            ),
            "what_failed": (
                "The current support/contact hard-route train target and official validation GT-counterfactual "
                "target are not aligned; the model prefers the wrong predicate on official validation."
            ),
            "what_to_do_next": (
                "Do not promote support/contact. Lock it as diagnostic/failure taxonomy, and decide whether to "
                "redesign its target/feature contract or keep the paper claim scoped to the cleaner routes."
            ),
        },
        "output_artifacts": {
            "summary": rel_path(out_dir / "summary.json"),
            "validation_errors": rel_path(out_dir / "validation_errors.jsonl"),
            "gate_review": rel_path(out_dir / "gate_review.csv"),
            "root_cause_review": rel_path(out_dir / "root_cause_review.csv"),
            "target_distribution": rel_path(out_dir / "target_distribution.csv"),
            "score_direction_diagnostic": rel_path(out_dir / "score_direction_diagnostic.csv"),
            "feature_label_means": rel_path(out_dir / "feature_label_means.csv"),
            "next_contract": rel_path(out_dir / "next_contract.json"),
            "report": rel_path(out_dir / "report.md"),
        },
    }

    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_path_decision" if not errors else "blocked",
        "next_todo": summary["next_todo"],
        "recommended_path": "freeze_support_contact_harder_route_as_diagnostic_before_any_retry",
        "allowed_next_options": [
            "freeze_support_contact_as_failure_taxonomy_and_scope_H002_to_clean_routes",
            "redesign_support_contact_target_feature_contract_from_scratch",
        ],
        "disallowed_next_options": [
            "posthoc_flip_M4_scores_on_official_validation",
            "promote_support_contact_as_solved",
            "run_official_test_before_claim_boundary_lock",
            "source_reranking_before_support_contact_path_decision",
        ],
    }

    report_lines = [
        "# Support/Contact Harder Route Metric Result Review",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"validation_errors = {summary['validation_errors']}",
        f"selected_path = {summary['selected_path']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Purpose",
        "",
        "Review why support/contact hard route shows an internal-dev M4 signal but fails on official validation.",
        "",
        "## Result",
        "",
        f"- internal dev M4 AUROC: `{summary['primary_findings']['internal_dev_m4_auroc']}`",
        f"- official validation M4 AUROC: `{official_m4_auroc}`",
        f"- official validation wrong-T AUROC: `{official_wrong_t_auroc}`",
        f"- paired M4 accuracy: `{paired_m4_acc}`",
        f"- paired wrong-T accuracy: `{paired_wrong_t_acc}`",
        "",
        "The support/contact harder route is not promotable. The result is inverted on official validation, so this branch must remain diagnostic/failure-taxonomy evidence.",
        "",
        "## Decision",
        "",
        "- H002 direction is not rejected globally.",
        "- Current support/contact hard-route implementation fails official validation transfer.",
        "- Do not flip scores post hoc.",
        "- Do not use support/contact as a solved paper claim.",
        "- Next step is a path decision: freeze as diagnostic or redesign the target/feature contract from scratch.",
    ]

    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "next_contract.json", next_contract)
    write_jsonl(out_dir / "validation_errors.jsonl", errors)
    write_csv(out_dir / "gate_review.csv", gate_rows)
    write_csv(out_dir / "root_cause_review.csv", root_causes)
    write_csv(out_dir / "target_distribution.csv", target_rows)
    write_csv(out_dir / "score_direction_diagnostic.csv", score_rows_out)
    write_csv(out_dir / "feature_label_means.csv", feature_rows)
    (out_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return summary


def main() -> int:
    summary = run(parse_args())
    return 1 if summary["validation_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
