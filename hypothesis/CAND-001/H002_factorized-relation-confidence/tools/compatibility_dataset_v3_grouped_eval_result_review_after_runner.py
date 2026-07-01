#!/usr/bin/env python3
"""Review grouped H002 evaluation results and decide family-level claim status."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_runner_after_protocol"
DEFAULT_EVAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_result_review_after_runner"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_grouped_eval_result_review_after_runner_v1"
STATUS_READY = "h002_compatibility_dataset_v3_grouped_eval_result_review_after_runner_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_grouped_eval_result_review_after_runner_input_errors"
EXPECTED_RUNNER_STATUS = "h002_compatibility_dataset_v3_grouped_eval_runner_after_protocol_ready"
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_grouped_eval_result_review_after_runner"
SELECTED_PATH = "grouped_review_ready_after_feature_repair_select_claim_boundary_review"
NEXT_TODO = "compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-dir", type=Path, default=DEFAULT_RUNNER_DIR)
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def metric_row(
    rows: list[dict[str, str]],
    *,
    level: str,
    route_family: str,
    predicate_label: str,
    protocol_split: str,
    view_id: str,
) -> dict[str, str] | None:
    for row in rows:
        if (
            row.get("level") == level
            and row.get("route_family") == route_family
            and row.get("predicate_label") == predicate_label
            and row.get("protocol_split") == protocol_split
            and row.get("view_id") == view_id
        ):
            return row
    return None


def control_row(
    rows: list[dict[str, str]],
    *,
    level: str,
    route_family: str,
    predicate_label: str,
    protocol_split: str,
    comparison: str,
) -> dict[str, str] | None:
    for row in rows:
        if (
            row.get("level") == level
            and row.get("route_family") == route_family
            and row.get("predicate_label") == predicate_label
            and row.get("protocol_split") == protocol_split
            and row.get("comparison") == comparison
        ):
            return row
    return None


def extract_metrics(row: dict[str, str] | None) -> dict[str, Any]:
    if row is None:
        return {}
    out: dict[str, Any] = {}
    for key, value in row.items():
        parsed = as_float(value)
        out[key] = parsed if parsed is not None else value
    return out


def validate_inputs(
    runner_summary: dict[str, Any],
    eval_manifest: dict[str, Any],
    route_rows: list[dict[str, str]],
    control_rows: list[dict[str, str]],
    runner_errors: list[dict[str, Any]],
    eval_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if runner_summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": runner_summary.get("status")})
    if runner_summary.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_next_todo", "actual": runner_summary.get("next_todo")})
    if runner_summary.get("validation_errors") != 0:
        errors.append({"error_type": "runner_summary_validation_errors", "actual": runner_summary.get("validation_errors")})
    if runner_errors:
        errors.append({"error_type": "runner_validation_error_rows_present", "rows": len(runner_errors)})
    if eval_manifest.get("status") != "ready":
        errors.append({"error_type": "unexpected_eval_manifest_status", "actual": eval_manifest.get("status")})
    if eval_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "eval_manifest_validation_errors", "actual": eval_manifest.get("validation_errors")})
    if eval_errors:
        errors.append({"error_type": "eval_validation_error_rows_present", "rows": len(eval_errors)})
    if not route_rows:
        errors.append({"error_type": "missing_route_metrics"})
    if not control_rows:
        errors.append({"error_type": "missing_control_metrics"})

    boundary = eval_manifest.get("boundary", {})
    expected_false = [
        "h001_artifacts_modified",
        "official_test_usage",
        "official_validation_usage",
        "p_obs_claim_enabled",
        "p_rel_claim_enabled",
        "paper_metric_produced",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("grouped_metric_run") is not True:
        errors.append({"error_type": "grouped_metric_run_not_true", "actual": boundary.get("grouped_metric_run")})
    return errors


def family_decisions(route_rows: list[dict[str, str]], control_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    families = ["relative_horizontal", "relative_vertical", "size_relative", "support_contact"]
    decisions: list[dict[str, Any]] = []
    for family in families:
        m4 = extract_metrics(
            metric_row(
                route_rows,
                level="route_family",
                route_family=family,
                predicate_label="ALL",
                protocol_split="internal_heldout",
                view_id="M4_TxG_compatibility",
            )
        )
        comparison_values: dict[str, float | None] = {}
        for comparison in ["M4_vs_M1", "M4_vs_M2", "M4_vs_M3", "M4_vs_wrong_T", "M4_vs_shuffled_G"]:
            row = control_row(
                control_rows,
                level="route_family",
                route_family=family,
                predicate_label="ALL",
                protocol_split="internal_heldout",
                comparison=comparison,
            )
            comparison_values[comparison] = as_float(row.get("delta_auroc")) if row else None

        auroc = m4.get("auroc")
        balanced_accuracy = m4.get("balanced_accuracy")
        rows = m4.get("rows")

        auroc_value = float(auroc) if isinstance(auroc, (int, float)) else 0.0
        ba_value = float(balanced_accuracy) if isinstance(balanced_accuracy, (int, float)) else 0.0
        deltas = [comparison_values[key] for key in ["M4_vs_M1", "M4_vs_M2", "M4_vs_M3"]]
        control_deltas = [comparison_values[key] for key in ["M4_vs_wrong_T", "M4_vs_shuffled_G"]]
        min_baseline_delta = min(delta for delta in deltas if delta is not None) if all(delta is not None for delta in deltas) else 0.0
        min_control_delta = min(delta for delta in control_deltas if delta is not None) if all(delta is not None for delta in control_deltas) else 0.0

        if auroc_value >= 0.90 and ba_value >= 0.85 and min_baseline_delta >= 0.25 and min_control_delta >= 0.25:
            status = "claim_supporting"
            role = "main_compatibility_route_evidence"
            action = "keep_for_claim_review"
            reason = "heldout M4 is strong and wrong-T/shuffled-G controls collapse"
        elif auroc_value >= 0.60 and min_baseline_delta >= 0.10 and min_control_delta >= 0.10:
            status = "partial"
            role = "challenging_compatibility_route_evidence"
            action = "keep_as_partial_evidence_with_predicate_breakdown"
            reason = "heldout M4 improves over semantic, geometry, concat, and controls but absolute performance is modest or unstable"
        else:
            status = "failed"
            role = "do_not_promote_without_repair"
            action = "run_failure_analysis_before_claim_lock"
            reason = "heldout M4 and controls do not establish a usable compatibility signal"

        decisions.append(
            {
                "route_family": family,
                "status": status,
                "paper_role_now": role,
                "recommended_action": action,
                "reason": reason,
                "heldout_rows": rows,
                "heldout_M4_auroc": auroc,
                "heldout_M4_balanced_accuracy": balanced_accuracy,
                "delta_vs_M1": comparison_values["M4_vs_M1"],
                "delta_vs_M2": comparison_values["M4_vs_M2"],
                "delta_vs_M3": comparison_values["M4_vs_M3"],
                "delta_vs_wrong_T": comparison_values["M4_vs_wrong_T"],
                "delta_vs_shuffled_G": comparison_values["M4_vs_shuffled_G"],
            }
        )
    return decisions


def predicate_review(route_rows: list[dict[str, str]], control_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    predicates = [
        ("relative_horizontal", "behind"),
        ("relative_horizontal", "front"),
        ("relative_horizontal", "left"),
        ("relative_horizontal", "right"),
        ("relative_vertical", "higher than"),
        ("relative_vertical", "lower than"),
        ("size_relative", "bigger than"),
        ("size_relative", "smaller than"),
        ("support_contact", "lying on"),
        ("support_contact", "standing on"),
    ]
    for family, predicate in predicates:
        m4 = extract_metrics(
            metric_row(
                route_rows,
                level="predicate",
                route_family=family,
                predicate_label=predicate,
                protocol_split="internal_heldout",
                view_id="M4_TxG_compatibility",
            )
        )
        wrong = control_row(
            control_rows,
            level="predicate",
            route_family=family,
            predicate_label=predicate,
            protocol_split="internal_heldout",
            comparison="M4_vs_wrong_T",
        )
        shuffled = control_row(
            control_rows,
            level="predicate",
            route_family=family,
            predicate_label=predicate,
            protocol_split="internal_heldout",
            comparison="M4_vs_shuffled_G",
        )
        rows.append(
            {
                "route_family": family,
                "predicate_label": predicate,
                "rows": m4.get("rows"),
                "positive": m4.get("positive"),
                "negative": m4.get("negative"),
                "M4_auroc": m4.get("auroc"),
                "M4_balanced_accuracy": m4.get("balanced_accuracy"),
                "delta_vs_wrong_T": as_float(wrong.get("delta_auroc")) if wrong else None,
                "delta_vs_shuffled_G": as_float(shuffled.get("delta_auroc")) if shuffled else None,
            }
        )
    return rows


def overall_summary(route_rows: list[dict[str, str]], control_rows: list[dict[str, str]]) -> dict[str, Any]:
    views = [
        "M1_T_semantic_only",
        "M2_G_geometry_only",
        "M3_T_plus_G_concat",
        "M4_TxG_compatibility",
        "C1_wrong_T_control",
        "C2_shuffled_G_control",
        "D1_Z_source_confidence_diagnostic",
        "D2_Q_observability_diagnostic",
    ]
    metrics = {
        view: extract_metrics(
            metric_row(
                route_rows,
                level="overall",
                route_family="ALL",
                predicate_label="ALL",
                protocol_split="internal_heldout",
                view_id=view,
            )
        )
        for view in views
    }
    controls = {
        comparison: extract_metrics(
            control_row(
                control_rows,
                level="overall",
                route_family="ALL",
                predicate_label="ALL",
                protocol_split="internal_heldout",
                comparison=comparison,
            )
        )
        for comparison in ["M4_vs_M1", "M4_vs_M2", "M4_vs_M3", "M4_vs_wrong_T", "M4_vs_shuffled_G"]
    }
    return {"metrics": metrics, "controls": controls}


def write_report(
    path: Path,
    *,
    summary: dict[str, Any],
    decisions: list[dict[str, Any]],
    predicates: list[dict[str, Any]],
) -> None:
    claim_supporting = [item["route_family"] for item in decisions if item["status"] == "claim_supporting"]
    partial = [item["route_family"] for item in decisions if item["status"] == "partial"]
    failed = [item["route_family"] for item in decisions if item["status"] == "failed"]
    lines = [
        "# H002 Grouped Evaluation Result Review",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Verdict",
        "",
        "The grouped runner supports an aggregate `T_e x G_e` compatibility signal, with family-level boundaries still required.",
        "",
        f"- Claim-supporting families: {', '.join(f'`{name}`' for name in claim_supporting) if claim_supporting else 'none'}.",
        f"- Partial/challenging families: {', '.join(f'`{name}`' for name in partial) if partial else 'none'}.",
        f"- Failed families: {', '.join(f'`{name}`' for name in failed) if failed else 'none'}.",
        "- This remains internal H002 candidate-pool evidence, not official validation/test or paper-level evidence.",
        "",
        "## Family Decisions",
        "",
        "| Family | Status | Heldout AUROC | Delta vs M1 | Delta vs M2 | Delta vs M3 | Delta vs wrong-T | Delta vs shuffled-G | Role |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for item in decisions:
        lines.append(
            "| {route_family} | {status} | {heldout_M4_auroc:.6f} | {delta_vs_M1:.6f} | {delta_vs_M2:.6f} | {delta_vs_M3:.6f} | {delta_vs_wrong_T:.6f} | {delta_vs_shuffled_G:.6f} | {paper_role_now} |".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "## Predicate Review",
            "",
            "| Family | Predicate | Rows | M4 AUROC | Delta vs wrong-T | Delta vs shuffled-G |",
            "| --- | --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in predicates:
        lines.append(
            "| {route_family} | `{predicate_label}` | {rows:.0f} | {M4_auroc:.6f} | {delta_vs_wrong_T:.6f} | {delta_vs_shuffled_G:.6f} |".format(
                **item
            )
        )
    lines.extend(
        [
            "",
            "## Next",
            "",
            "The next required step is claim-boundary review: decide which repaired grouped-eval results can support the H002 paper framing and which families remain diagnostic or partial.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    runner_summary = read_json(args.runner_dir / "summary.json")
    eval_manifest = read_json(args.eval_dir / "eval_manifest.json")
    route_rows = read_csv(args.eval_dir / "route_metrics.csv")
    control_rows = read_csv(args.eval_dir / "control_metrics.csv")
    runner_errors = read_jsonl(args.runner_dir / "validation_errors.jsonl")
    eval_errors = read_jsonl(args.eval_dir / "validation_errors.jsonl")

    validation_errors = validate_inputs(
        runner_summary,
        eval_manifest,
        route_rows,
        control_rows,
        runner_errors,
        eval_errors,
    )

    decisions = family_decisions(route_rows, control_rows)
    predicates = predicate_review(route_rows, control_rows)
    overall = overall_summary(route_rows, control_rows)

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "fix_inputs_before_review",
        "next_todo": NEXT_TODO if not validation_errors else "fix_grouped_eval_result_review_inputs",
        "validation_errors": len(validation_errors),
        "input_artifacts": {
            "runner_summary": rel_path(args.runner_dir / "summary.json"),
            "eval_manifest": rel_path(args.eval_dir / "eval_manifest.json"),
            "route_metrics": rel_path(args.eval_dir / "route_metrics.csv"),
            "control_metrics": rel_path(args.eval_dir / "control_metrics.csv"),
        },
        "boundary": {
            "official_validation_usage": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "h001_artifacts_modified": False,
        },
        "overall": overall,
        "family_decisions": decisions,
        "next_required_analysis": "claim-boundary review after repaired grouped evaluation",
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "next_contract.json", {"next_todo": summary["next_todo"], "selected_path": summary["selected_path"]})
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "family_decisions.csv", decisions)
    write_csv(args.output_dir / "predicate_review.csv", predicates)
    write_report(args.output_dir / "report.md", summary=summary, decisions=decisions, predicates=predicates)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
