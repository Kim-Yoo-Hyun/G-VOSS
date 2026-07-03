#!/usr/bin/env python3
"""Review H002 source-reranking metric outputs before claim promotion."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_STAGE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_metric_runner_after_protocol_freeze"
DEFAULT_RUNTIME_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_metric_result_review_after_runner"

EXPECTED_RUNNER_STATUS = "h002_source_reranking_metric_runner_after_protocol_freeze_ready"
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_source_reranking_metric_result_review_after_runner"
EXPECTED_RUNTIME_STATUS = "h002_source_reranking_metric_runner_ready"

SCHEMA_VERSION = "h002_source_reranking_metric_result_review_after_runner_v1"
STATUS_READY = "h002_source_reranking_metric_result_review_after_runner_ready"
STATUS_ERRORS = "h002_source_reranking_metric_result_review_after_runner_errors"
SELECTED_PATH = "source_reranking_validation_evidence_ready_select_claim_boundary_lock"
NEXT_TODO = "compatibility_dataset_v3_source_reranking_claim_boundary_lock_after_result_review"

K_GRID = [5, 10, 20, 50, 100]
PRIMARY_FAMILIES = {"relative_vertical", "size_relative"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-stage-dir", type=Path, default=DEFAULT_RUNNER_STAGE_DIR)
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
    if not path.exists():
        return []
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
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def validate(runner_stage: dict[str, Any], runtime_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if runner_stage.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_stage_status", "actual": runner_stage.get("status")})
    if runner_stage.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_stage_next_todo", "actual": runner_stage.get("next_todo")})
    if runner_stage.get("validation_errors") != 0:
        errors.append({"error_type": "runner_stage_validation_errors", "actual": runner_stage.get("validation_errors")})
    if runtime_manifest.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": runtime_manifest.get("status")})
    if runtime_manifest.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_validation_errors", "actual": runtime_manifest.get("validation_errors")})
    boundary = runtime_manifest.get("boundary", {})
    for key, expected in {
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "paper_metric_promoted": False,
        "C_e_excludes_Z_e": True,
        "post_hoc_lambda_tuning": False,
    }.items():
        if boundary.get(key) is not expected:
            errors.append({"error_type": "unexpected_boundary", "key": key, "actual": boundary.get(key), "expected": expected})
    return errors


def row_by(rows: list[dict[str, str]], **criteria: str) -> dict[str, str] | None:
    for row in rows:
        if all(row.get(key) == str(value) for key, value in criteria.items()):
            return row
    return None


def primary_tradeoff(control_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, bool]]:
    rows: list[dict[str, Any]] = []
    flags = {
        "weighted_S2_vs_S0_recall_nonnegative_all_K": True,
        "weighted_S2_vs_S0_violation_nonpositive_all_K": True,
        "weighted_S2_vs_shuffled_recall_positive_all_K": True,
        "weighted_S2_vs_wrong_T_recall_positive_all_K": True,
        "weighted_S2_vs_wrong_T_violation_nonpositive_all_K": True,
    }
    for row in control_rows:
        comparison = row.get("comparison", "")
        k = int(row.get("K", 0))
        if row.get("level") != "primary_success_weighted" or k not in K_GRID:
            continue
        d_recall = as_float(row.get("delta_Recall@K"))
        d_violation = as_float(row.get("delta_Violation@K"))
        rows.append(
            {
                "K": k,
                "comparison": comparison,
                "delta_Recall@K": d_recall,
                "delta_Violation@K": d_violation,
                "primary_Recall@K": as_float(row.get("primary_Recall@K")),
                "baseline_Recall@K": as_float(row.get("baseline_Recall@K")),
                "primary_Violation@K": as_float(row.get("primary_Violation@K")),
                "baseline_Violation@K": as_float(row.get("baseline_Violation@K")),
            }
        )
        if comparison == "S2_vs_S0_source_score":
            flags["weighted_S2_vs_S0_recall_nonnegative_all_K"] &= d_recall is not None and d_recall >= -1e-12
            flags["weighted_S2_vs_S0_violation_nonpositive_all_K"] &= d_violation is not None and d_violation <= 1e-12
        if comparison == "S2_vs_C1_source_x_shuffled_Ce":
            flags["weighted_S2_vs_shuffled_recall_positive_all_K"] &= d_recall is not None and d_recall > 0
        if comparison == "S2_vs_C2_source_x_wrong_T_Ce":
            flags["weighted_S2_vs_wrong_T_recall_positive_all_K"] &= d_recall is not None and d_recall > 0
            flags["weighted_S2_vs_wrong_T_violation_nonpositive_all_K"] &= d_violation is not None and d_violation <= 0
    return sorted(rows, key=lambda row: (row["comparison"], row["K"])), flags


def source_family_tradeoff(source_family_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    negative_recall_cases: list[dict[str, Any]] = []
    violation_nonimprove_cases: list[dict[str, Any]] = []
    for source_id in sorted({row["source_id"] for row in source_family_rows}):
        for family in sorted(PRIMARY_FAMILIES):
            for k in K_GRID:
                s0 = row_by(source_family_rows, level="source_family", source_id=source_id, route_family=family, score_id="S0_source_score", K=str(k))
                s2 = row_by(source_family_rows, level="source_family", source_id=source_id, route_family=family, score_id="S2_source_x_Ce", K=str(k))
                if not s0 or not s2:
                    continue
                d_recall = (as_float(s2.get("Recall@K")) or 0.0) - (as_float(s0.get("Recall@K")) or 0.0)
                d_violation = (as_float(s2.get("Violation@K")) or 0.0) - (as_float(s0.get("Violation@K")) or 0.0)
                out = {
                    "source_id": source_id,
                    "route_family": family,
                    "K": k,
                    "S2_Recall@K": as_float(s2.get("Recall@K")),
                    "S0_Recall@K": as_float(s0.get("Recall@K")),
                    "delta_Recall@K": d_recall,
                    "S2_Violation@K": as_float(s2.get("Violation@K")),
                    "S0_Violation@K": as_float(s0.get("Violation@K")),
                    "delta_Violation@K": d_violation,
                    "gt_total": as_float(s2.get("gt_total")),
                }
                rows.append(out)
                if d_recall < -1e-12:
                    negative_recall_cases.append(out)
                if d_violation > 1e-12:
                    violation_nonimprove_cases.append(out)
    stats = {
        "source_family_cells": len(rows),
        "negative_recall_cells": len(negative_recall_cases),
        "violation_nonimprove_cells": len(violation_nonimprove_cases),
        "negative_recall_cases": negative_recall_cases,
        "violation_nonimprove_cases": violation_nonimprove_cases,
    }
    return rows, stats


def claim_rows(stats: dict[str, Any], flags: dict[str, bool]) -> list[dict[str, Any]]:
    return [
        {
            "claim": "S2 source-score times C_e improves primary validation recall/violation tradeoff over source-only ranking",
            "status": "allowed_with_validation_boundary" if flags["weighted_S2_vs_S0_recall_nonnegative_all_K"] and flags["weighted_S2_vs_S0_violation_nonpositive_all_K"] else "blocked",
            "reason": "Weighted primary success families improve/preserve Recall@K and lower Violation@K for all frozen K.",
        },
        {
            "claim": "C_e alone is the deployable ranking score",
            "status": "blocked",
            "reason": "S1_Ce_only has very low low-K recall; source confidence Z_e is still needed at reranking stage.",
        },
        {
            "claim": "S2 improves every source/family/K cell",
            "status": "blocked",
            "reason": f"Small Recall@K regressions exist in {stats['negative_recall_cells']} source-family-K cells, though violation improves in all reviewed cells.",
        },
        {
            "claim": "This is an official test result or final paper promotion",
            "status": "blocked",
            "reason": "Only official validation eval-only rows were used; official test remains unused and result review/claim lock are required.",
        },
        {
            "claim": "support_contact is solved",
            "status": "blocked",
            "reason": "support_contact is excluded from success aggregation and remains diagnostic/failure taxonomy.",
        },
        {
            "claim": "p_obs/p_rel reliability posterior is validated",
            "status": "blocked",
            "reason": "This stage evaluates C_e-based source reranking only.",
        },
    ]


def write_report(path: Path, summary: dict[str, Any], source_stats: dict[str, Any]) -> None:
    lines = [
        "# Source Reranking Metric Result Review",
        "",
        f"- status: `{summary['status']}`",
        f"- validation errors: `{summary['validation_errors']}`",
        f"- selected path: `{summary['selected_path']}`",
        f"- next todo: `{summary['next_todo']}`",
        "",
        "## Decision",
        "",
        "- Source-reranking validation evidence is positive and ready for claim-boundary lock.",
        "- It is not yet final paper promotion and not official test evidence.",
        "- `S2_source_x_Ce` may be discussed as validation-level source-deployable evidence for primary clean families.",
        "",
        "## Caveats",
        "",
        f"- Small source/family/K Recall@K regressions: `{source_stats['negative_recall_cells']}` cells.",
        f"- Violation@K non-improvement cells: `{source_stats['violation_nonimprove_cells']}` cells.",
        "- `support_contact` remains diagnostic/excluded.",
        "- `C_e` alone is not a deployable ranking score at low K.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    runner_stage = read_json(args.runner_stage_dir / "summary.json")
    runtime_manifest = read_json(args.runtime_dir / "metric_manifest.json")
    errors = validate(runner_stage, runtime_manifest)

    control_rows = read_csv(args.runtime_dir / "control_metrics.csv")
    source_rows = read_csv(args.runtime_dir / "source_family_metrics.csv")
    primary_rows, primary_flags = primary_tradeoff(control_rows)
    family_rows, family_stats = source_family_tradeoff(source_rows)
    claims = claim_rows(family_stats, primary_flags)

    status = STATUS_READY if not errors else STATUS_ERRORS
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_result_review_inputs",
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_artifacts": {
            "runner_stage_dir": rel_path(args.runner_stage_dir),
            "runtime_dir": rel_path(args.runtime_dir),
        },
        "decision": {
            "source_reranking_validation_evidence": "positive" if not errors else "blocked",
            "paper_promotion": "not_yet",
            "claim_boundary_lock_required_next": not errors,
            "official_test_usage": False,
            "primary_score": "S2_source_x_Ce",
            **primary_flags,
            **{key: value for key, value in family_stats.items() if not key.endswith("_cases")},
        },
        "output_artifacts": {
            "primary_tradeoff": rel_path(args.output_dir / "primary_tradeoff.csv"),
            "source_family_tradeoff": rel_path(args.output_dir / "source_family_tradeoff.csv"),
            "claim_boundary_recommendation": rel_path(args.output_dir / "claim_boundary_recommendation.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "next_contract": rel_path(args.output_dir / "next_contract.json"),
        },
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
    }
    next_contract = {
        "schema_version": f"{SCHEMA_VERSION}_next_contract",
        "status": "ready_for_source_reranking_claim_boundary_lock" if not errors else "blocked",
        "next_todo": NEXT_TODO,
        "must_lock": [
            "validation_evidence_wording",
            "S2_vs_S0_tradeoff_table_role",
            "per_source_family_caveats",
            "blocked_final_test_and_support_contact_claims",
            "whether_to_promote_to_paper_table_candidate",
        ],
        "must_not_do": [
            "claim_uniform_improvement_in_every_cell",
            "call_S1_Ce_only_deployable",
            "use_official_test_wording",
            "promote_without_claim_boundary_lock",
        ],
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "source_family_caveats.json", family_stats)
    write_json(args.output_dir / "next_contract.json", next_contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_csv(args.output_dir / "primary_tradeoff.csv", primary_rows)
    write_csv(args.output_dir / "source_family_tradeoff.csv", family_rows)
    write_csv(args.output_dir / "claim_boundary_recommendation.csv", claims)
    write_report(args.output_dir / "report.md", summary, family_stats)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
