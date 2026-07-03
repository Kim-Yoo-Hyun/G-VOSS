#!/usr/bin/env python3
"""Create bounded validation-table skeletons for H002 source reranking."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_LOCK_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review"
DEFAULT_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_metric_result_review_after_runner"
DEFAULT_RUNTIME_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock"

EXPECTED_LOCK_STATUS = "h002_source_reranking_claim_boundary_lock_after_result_review_locked"
EXPECTED_LOCK_NEXT = "compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock"
EXPECTED_RUNTIME_STATUS = "h002_source_reranking_metric_runner_ready"

SCHEMA_VERSION = "h002_source_reranking_validation_table_skeleton_after_claim_boundary_lock_v1"
STATUS_READY = "h002_source_reranking_validation_table_skeleton_after_claim_boundary_lock_ready"
STATUS_ERRORS = "h002_source_reranking_validation_table_skeleton_after_claim_boundary_lock_input_errors"
SELECTED_PATH = "source_reranking_validation_table_skeleton_ready_select_table_review"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_validation_table_review_after_skeleton"

K_GRID = [5, 10, 20, 50, 100]
PRIMARY_FAMILIES = ["relative_vertical", "size_relative"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock-dir", type=Path, default=DEFAULT_LOCK_DIR)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--runtime-dir", type=Path, default=DEFAULT_RUNTIME_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
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
    with path.open("w", newline="", encoding="utf-8") as handle:
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
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.6f}"


def row_lookup(rows: list[dict[str, str]], **filters: str) -> dict[str, str] | None:
    for row in rows:
        if all(row.get(key) == str(value) for key, value in filters.items()):
            return row
    return None


def validate_inputs(lock_summary: dict[str, Any], runtime_manifest: dict[str, Any], lock_dir: Path, review_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if lock_summary.get("status") != EXPECTED_LOCK_STATUS:
        errors.append({"error_type": "unexpected_lock_status", "actual": lock_summary.get("status")})
    if lock_summary.get("next_todo") != EXPECTED_LOCK_NEXT:
        errors.append({"error_type": "unexpected_lock_next_todo", "actual": lock_summary.get("next_todo")})
    if lock_summary.get("validation_errors") != 0:
        errors.append({"error_type": "lock_validation_errors", "actual": lock_summary.get("validation_errors")})
    if line_count(lock_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "lock_validation_errors_file_not_empty"})
    if line_count(review_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "review_validation_errors_file_not_empty"})

    decision = lock_summary.get("decision", {})
    if decision.get("source_reranking_claim_boundary_locked") is not True:
        errors.append({"error_type": "source_reranking_claim_boundary_not_locked"})
    if decision.get("source_reranking_table_role") != "secondary_validation_table_candidate_or_appendix":
        errors.append({"error_type": "unexpected_table_role", "actual": decision.get("source_reranking_table_role")})
    if decision.get("final_paper_result_promotion") != "not_yet":
        errors.append({"error_type": "unexpected_final_paper_result_promotion", "actual": decision.get("final_paper_result_promotion")})
    if decision.get("official_test_usage") is not False:
        errors.append({"error_type": "unexpected_official_test_usage", "actual": decision.get("official_test_usage")})
    if decision.get("primary_score") != "S2_source_x_Ce":
        errors.append({"error_type": "unexpected_primary_score", "actual": decision.get("primary_score")})
    if decision.get("baseline") != "S0_source_score":
        errors.append({"error_type": "unexpected_baseline", "actual": decision.get("baseline")})

    if runtime_manifest.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": runtime_manifest.get("status")})
    if runtime_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_validation_errors", "actual": runtime_manifest.get("validation_errors")})

    boundary = runtime_manifest.get("boundary", {})
    required_boundary = {
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "paper_metric_promoted": False,
        "source_reranking_metric_produced": True,
        "C_e_excludes_Z_e": True,
        "Z_e_combined_only_after_C_e": True,
        "post_hoc_lambda_tuning": False,
    }
    for key, expected in required_boundary.items():
        if boundary.get(key) != expected:
            errors.append({"error_type": "unexpected_runtime_boundary", "key": key, "actual": boundary.get(key), "expected": expected})
    return errors


def primary_tradeoff_rows(control_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for k in K_GRID:
        row = row_lookup(control_rows, level="primary_success_weighted", comparison="S2_vs_S0_source_score", K=str(k))
        if not row:
            continue
        rows.append(
            {
                "K": k,
                "scope": "primary_success_weighted",
                "families": "relative_vertical + size_relative",
                "score": "S2_source_x_Ce",
                "baseline": "S0_source_score",
                "S2_Recall@K": fmt(as_float(row.get("primary_Recall@K"))),
                "S0_Recall@K": fmt(as_float(row.get("baseline_Recall@K"))),
                "delta_Recall@K": fmt(as_float(row.get("delta_Recall@K"))),
                "S2_Violation@K": fmt(as_float(row.get("primary_Violation@K"))),
                "S0_Violation@K": fmt(as_float(row.get("baseline_Violation@K"))),
                "delta_Violation@K": fmt(as_float(row.get("delta_Violation@K"))),
                "paper_role": "secondary_validation_table_candidate",
                "required_caveat": "validation-only; not uniform across all source/family/K cells",
            }
        )
    return rows


def control_table_rows(control_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    labels = {
        "S2_vs_S1_Ce_only": ("C_e only", "negative ablation: explains why source confidence Z_e remains needed"),
        "S2_vs_C1_source_x_shuffled_Ce": ("source x shuffled C_e", "geometry-compatibility control"),
        "S2_vs_C2_source_x_wrong_T_Ce": ("source x wrong-T C_e", "predicate-compatibility control"),
    }
    for k in K_GRID:
        for comparison, (label, role) in labels.items():
            row = row_lookup(control_rows, level="primary_success_weighted", comparison=comparison, K=str(k))
            if not row:
                continue
            rows.append(
                {
                    "K": k,
                    "comparison": comparison,
                    "control": label,
                    "control_role": role,
                    "S2_Recall@K": fmt(as_float(row.get("primary_Recall@K"))),
                    "control_Recall@K": fmt(as_float(row.get("baseline_Recall@K"))),
                    "delta_Recall@K": fmt(as_float(row.get("delta_Recall@K"))),
                    "S2_Violation@K": fmt(as_float(row.get("primary_Violation@K"))),
                    "control_Violation@K": fmt(as_float(row.get("baseline_Violation@K"))),
                    "delta_Violation@K": fmt(as_float(row.get("delta_Violation@K"))),
                    "paper_role": "supporting_control_row" if comparison != "S2_vs_S1_Ce_only" else "diagnostic_ablation_row",
                }
            )
    return rows


def source_family_rows(source_family_metrics: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    caveats: list[dict[str, Any]] = []
    source_ids = sorted({row["source_id"] for row in source_family_metrics if row.get("level") == "source_family"})
    for source_id in source_ids:
        for family in PRIMARY_FAMILIES:
            for k in K_GRID:
                s0 = row_lookup(source_family_metrics, level="source_family", source_id=source_id, route_family=family, score_id="S0_source_score", K=str(k))
                s2 = row_lookup(source_family_metrics, level="source_family", source_id=source_id, route_family=family, score_id="S2_source_x_Ce", K=str(k))
                if not s0 or not s2:
                    continue
                d_recall = (as_float(s2.get("Recall@K")) or 0.0) - (as_float(s0.get("Recall@K")) or 0.0)
                d_violation = (as_float(s2.get("Violation@K")) or 0.0) - (as_float(s0.get("Violation@K")) or 0.0)
                row = {
                    "source_id": source_id,
                    "route_family": family,
                    "K": k,
                    "S2_Recall@K": fmt(as_float(s2.get("Recall@K"))),
                    "S0_Recall@K": fmt(as_float(s0.get("Recall@K"))),
                    "delta_Recall@K": fmt(d_recall),
                    "S2_Violation@K": fmt(as_float(s2.get("Violation@K"))),
                    "S0_Violation@K": fmt(as_float(s0.get("Violation@K"))),
                    "delta_Violation@K": fmt(d_violation),
                    "gt_total": fmt(as_float(s2.get("gt_total"))),
                    "recall_regression": str(d_recall < -1e-12).lower(),
                    "violation_nonimprovement": str(d_violation > 1e-12).lower(),
                }
                rows.append(row)
                if d_recall < -1e-12 or d_violation > 1e-12:
                    caveats.append(row)
    return rows, caveats


def table_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "table_component": "primary_tradeoff",
            "locked_position": "secondary validation table candidate",
            "include_main_text": "conditional",
            "include_appendix": "yes",
            "blocked_position": "final official-test result",
            "reason": "positive weighted validation tradeoff, but 3/20 source-family-K recall regressions",
        },
        {
            "table_component": "controls",
            "locked_position": "supporting control rows",
            "include_main_text": "yes_if_space",
            "include_appendix": "yes",
            "blocked_position": "SOTA evidence",
            "reason": "controls show compatibility sensitivity, not full benchmark superiority",
        },
        {
            "table_component": "source_family_caveats",
            "locked_position": "required caveat table or footnote",
            "include_main_text": "short caveat",
            "include_appendix": "yes",
            "blocked_position": "hide or omit",
            "reason": "uniform improvement is explicitly blocked",
        },
        {
            "table_component": "C_e_only",
            "locked_position": "negative ablation",
            "include_main_text": "only_to_explain_factor_separation",
            "include_appendix": "yes",
            "blocked_position": "deployable ranking score",
            "reason": "low-K recall is poor when source confidence Z_e is removed",
        },
    ]


def write_markdown_report(
    path: Path,
    summary: dict[str, Any],
    primary_rows: list[dict[str, Any]],
    controls: list[dict[str, Any]],
    caveats: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 Source Reranking Validation Table Skeleton",
        "",
        "## Status",
        "",
        "```text",
        f"artifact_root = {summary['output_artifacts']['artifact_root']}",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Table Skeleton Decision",
        "",
        "- This is a bounded validation-table skeleton, not final paper-result promotion.",
        "- The table tests source-level reranking with `S2_source_x_Ce` against `S0_source_score`.",
        "- It is limited to official validation source candidates and clean comparison families.",
        "- It must include the 3/20 source-family-K recall-regression caveat.",
        "",
        "## Primary Tradeoff Skeleton",
        "",
        "| K | S2 Recall | S0 Recall | Delta Recall | S2 Violation | S0 Violation | Delta Violation |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in primary_rows:
        lines.append(
            "| {K} | {S2_Recall@K} | {S0_Recall@K} | {delta_Recall@K} | {S2_Violation@K} | {S0_Violation@K} | {delta_Violation@K} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Control Skeleton",
            "",
            "| K | Control | Delta Recall | Delta Violation | Role |",
            "| ---: | --- | ---: | ---: | --- |",
        ]
    )
    for row in controls:
        lines.append(
            "| {K} | {control} | {delta_Recall@K} | {delta_Violation@K} | {control_role} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Required Caveat Rows",
            "",
            "| Source | Family | K | Delta Recall | Delta Violation |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for row in caveats:
        lines.append(
            "| `{source_id}` | `{route_family}` | {K} | {delta_Recall@K} | {delta_Violation@K} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Draft Caption",
            "",
            "Official-validation source-reranking evidence for H002. `S2_source_x_Ce` combines "
            "source confidence with predicate-geometry compatibility after `C_e` has been computed "
            "from `T_e` and `G_e` without `Z_e`. The table reports clean comparison families "
            "(`relative_vertical`, `size_relative`) only. It does not use official test data, does "
            "not claim uniform improvement across every source/family/K cell, and does not evaluate "
            "`p_obs`, `p_rel`, `support_contact`, SOTA, or full 3DSSG performance.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    lock_summary = read_json(args.lock_dir / "summary.json")
    runtime_manifest = read_json(args.runtime_dir / "metric_manifest.json")
    control_rows = read_csv(args.runtime_dir / "control_metrics.csv")
    source_family_metrics = read_csv(args.runtime_dir / "source_family_metrics.csv")

    errors = validate_inputs(lock_summary, runtime_manifest, args.lock_dir, args.review_dir)
    primary_rows = primary_tradeoff_rows(control_rows)
    control_table = control_table_rows(control_rows)
    source_family_table, caveat_rows = source_family_rows(source_family_metrics)
    decisions = table_decision_rows()

    if len(primary_rows) != len(K_GRID):
        errors.append({"error_type": "missing_primary_tradeoff_rows", "actual": len(primary_rows), "expected": len(K_GRID)})
    if len(caveat_rows) != 3:
        errors.append({"error_type": "unexpected_caveat_row_count", "actual": len(caveat_rows), "expected": 3})
    if len(source_family_table) != 20:
        errors.append({"error_type": "unexpected_source_family_row_count", "actual": len(source_family_table), "expected": 20})

    status = STATUS_ERRORS if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "source_reranking_validation_table_skeleton_blocked_by_input_errors",
        "validation_errors": len(errors),
        "input_artifacts": {
            "claim_boundary_lock": rel_path(args.lock_dir / "summary.json"),
            "metric_manifest": rel_path(args.runtime_dir / "metric_manifest.json"),
            "control_metrics": rel_path(args.runtime_dir / "control_metrics.csv"),
            "source_family_metrics": rel_path(args.runtime_dir / "source_family_metrics.csv"),
        },
        "decision": {
            "validation_table_skeleton_ready": not errors,
            "table_role": "secondary_validation_table_candidate_or_appendix",
            "main_text_allowed": "conditional_validation_only",
            "final_paper_result_promotion": "not_yet",
            "official_test_usage": False,
            "primary_score": "S2_source_x_Ce",
            "baseline": "S0_source_score",
            "primary_success_families": PRIMARY_FAMILIES,
            "primary_tradeoff_rows": len(primary_rows),
            "source_family_rows": len(source_family_table),
            "required_caveat_rows": len(caveat_rows),
            "controls_rows": len(control_table),
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "primary_tradeoff_table": rel_path(args.output_dir / "primary_tradeoff_table.csv"),
            "control_table": rel_path(args.output_dir / "control_table.csv"),
            "source_family_caveat_table": rel_path(args.output_dir / "source_family_caveat_table.csv"),
            "source_family_full_table": rel_path(args.output_dir / "source_family_full_table.csv"),
            "table_position_lock": rel_path(args.output_dir / "table_position_lock.csv"),
            "paper_table_skeleton": rel_path(args.output_dir / "paper_table_skeleton.md"),
            "report": rel_path(args.output_dir / "report.md"),
        },
        "next_todo": NEXT_TODO if not errors else EXPECTED_LOCK_NEXT,
    }

    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "primary_tradeoff_table.csv", primary_rows)
    write_csv(args.output_dir / "control_table.csv", control_table)
    write_csv(args.output_dir / "source_family_caveat_table.csv", caveat_rows)
    write_csv(args.output_dir / "source_family_full_table.csv", source_family_table)
    write_csv(args.output_dir / "table_position_lock.csv", decisions)
    write_markdown_report(args.output_dir / "paper_table_skeleton.md", summary, primary_rows, control_table, caveat_rows)
    write_markdown_report(args.output_dir / "report.md", summary, primary_rows, control_table, caveat_rows)

    print(json.dumps({"status": status, "validation_errors": len(errors), "next_todo": summary["next_todo"]}, ensure_ascii=False, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
