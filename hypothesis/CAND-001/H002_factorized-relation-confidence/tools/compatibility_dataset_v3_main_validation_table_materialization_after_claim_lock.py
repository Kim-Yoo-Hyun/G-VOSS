#!/usr/bin/env python3
"""Materialize caption-ready H002 main validation table rows after claim lock."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_CLAIM_LOCK_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_main_validation_claim_table_lock_after_path_decision"
DEFAULT_SKELETON_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_source_reranking_validation_table_skeleton_after_claim_boundary_lock"
DEFAULT_RUNTIME_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/source_reranking_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock"

EXPECTED_CLAIM_STATUS = "h002_main_validation_claim_table_lock_after_path_decision_ready"
EXPECTED_CLAIM_NEXT = "compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock"
EXPECTED_SKELETON_STATUS = "h002_source_reranking_validation_table_skeleton_after_claim_boundary_lock_ready"
EXPECTED_RUNTIME_STATUS = "h002_source_reranking_metric_runner_ready"

SCHEMA_VERSION = "h002_main_validation_table_materialization_after_claim_lock_v1"
STATUS_READY = "h002_main_validation_table_materialization_after_claim_lock_ready"
STATUS_ERRORS = "h002_main_validation_table_materialization_after_claim_lock_input_errors"
SELECTED_PATH = "main_validation_table_materialized_select_review"
NEXT_TODO = "compatibility_dataset_v3_main_validation_table_review_after_materialization"

K_GRID = [5, 10, 20, 50, 100]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-lock-dir", type=Path, default=DEFAULT_CLAIM_LOCK_DIR)
    parser.add_argument("--skeleton-dir", type=Path, default=DEFAULT_SKELETON_DIR)
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


def fmt(value: Any) -> str:
    value_float = as_float(value)
    if value_float is None:
        return ""
    return f"{value_float:.6f}"


def validate_inputs(claim: dict[str, Any], skeleton: dict[str, Any], runtime: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if claim.get("status") != EXPECTED_CLAIM_STATUS:
        errors.append({"error_type": "unexpected_claim_lock_status", "actual": claim.get("status")})
    if claim.get("next_todo") != EXPECTED_CLAIM_NEXT:
        errors.append({"error_type": "unexpected_claim_lock_next_todo", "actual": claim.get("next_todo")})
    if claim.get("validation_errors") != 0:
        errors.append({"error_type": "claim_lock_validation_errors", "actual": claim.get("validation_errors")})
    if line_count(args.claim_lock_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "claim_lock_validation_errors_file_not_empty"})

    claim_decision = claim.get("decision", {})
    for key, expected in {
        "main_validation_table_locked": True,
        "main_validation_table_allowed": True,
        "official_test_benchmark_claim_allowed": False,
        "h003_embedding_extension_in_main_claim_now": False,
        "h003_embedding_extension_future_optional": True,
    }.items():
        if claim_decision.get(key) is not expected:
            errors.append({"error_type": "unexpected_claim_decision", "key": key, "actual": claim_decision.get(key), "expected": expected})

    boundary = claim.get("locked_claim_boundary", {})
    for key, expected in {
        "main_split": "official_3DSSG_validation_split",
        "primary_score": "S2_source_x_Ce",
        "baseline": "S0_source_score",
        "method_role": "factorized reliability/reranking layer",
    }.items():
        if boundary.get(key) != expected:
            errors.append({"error_type": "unexpected_locked_boundary", "key": key, "actual": boundary.get(key), "expected": expected})

    if skeleton.get("status") != EXPECTED_SKELETON_STATUS:
        errors.append({"error_type": "unexpected_skeleton_status", "actual": skeleton.get("status")})
    if skeleton.get("validation_errors") != 0:
        errors.append({"error_type": "skeleton_validation_errors", "actual": skeleton.get("validation_errors")})
    if line_count(args.skeleton_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "skeleton_validation_errors_file_not_empty"})

    if runtime.get("status") != EXPECTED_RUNTIME_STATUS:
        errors.append({"error_type": "unexpected_runtime_status", "actual": runtime.get("status")})
    if runtime.get("validation_errors") != 0:
        errors.append({"error_type": "runtime_validation_errors", "actual": runtime.get("validation_errors")})
    if line_count(args.runtime_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "runtime_validation_errors_file_not_empty"})

    runtime_boundary = runtime.get("boundary", {})
    for key, expected in {
        "official_validation_eval_only": True,
        "official_test_usage": False,
        "C_e_excludes_Z_e": True,
        "Z_e_combined_only_after_C_e": True,
        "post_hoc_lambda_tuning": False,
    }.items():
        if runtime_boundary.get(key) != expected:
            errors.append({"error_type": "unexpected_runtime_boundary", "key": key, "actual": runtime_boundary.get(key), "expected": expected})
    return errors


def main_table_rows(primary_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_k = {int(row["K"]): row for row in primary_rows if row.get("K")}
    for k in K_GRID:
        row = by_k.get(k)
        if not row:
            continue
        rows.append(
            {
                "K": k,
                "split": "official_3DSSG_validation",
                "sources": "VL-SAT + Open3DSG",
                "families": "relative_vertical + size_relative",
                "baseline": "S0_source_score",
                "h002_score": "S2_source_x_Ce",
                "S0_Recall@K": fmt(row.get("S0_Recall@K")),
                "H002_Recall@K": fmt(row.get("S2_Recall@K")),
                "Delta_Recall@K": fmt(row.get("delta_Recall@K")),
                "S0_Violation@K": fmt(row.get("S0_Violation@K")),
                "H002_Violation@K": fmt(row.get("S2_Violation@K")),
                "Delta_Violation@K": fmt(row.get("delta_Violation@K")),
                "paper_role": "main_validation_benchmark_row",
            }
        )
    return rows


def source_family_caveat_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "source_id": row.get("source_id", ""),
                "route_family": row.get("route_family", ""),
                "K": row.get("K", ""),
                "Delta_Recall@K": fmt(row.get("delta_Recall@K")),
                "Delta_Violation@K": fmt(row.get("delta_Violation@K")),
                "required_caveat": "small Recall@K regression in this source/family/K cell; do not claim uniform improvement",
            }
        )
    return out


def control_compact_rows(control_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in control_rows:
        out.append(
            {
                "K": row.get("K", ""),
                "control": row.get("control", ""),
                "control_role": row.get("control_role", ""),
                "Delta_Recall@K": fmt(row.get("delta_Recall@K")),
                "Delta_Violation@K": fmt(row.get("delta_Violation@K")),
                "paper_role": row.get("paper_role", ""),
            }
        )
    return out


def blocked_checklist_rows() -> list[dict[str, Any]]:
    return [
        {
            "claim_or_field": "official 3DSSG test result",
            "status": "blocked",
            "required_replacement": "official 3DSSG validation split result",
        },
        {
            "claim_or_field": "SOTA / leaderboard wording",
            "status": "blocked",
            "required_replacement": "main validation benchmark comparison",
        },
        {
            "claim_or_field": "unconstrained open-set GT evaluation",
            "status": "blocked",
            "required_replacement": "Open3DSG as open-vocabulary source with closed 3DSSG mapping",
        },
        {
            "claim_or_field": "uniform improvement across all source/family/K cells",
            "status": "blocked",
            "required_replacement": "weighted primary improvement with explicit 3-cell Recall@K regression caveat",
        },
        {
            "claim_or_field": "H003 embedding as main contribution",
            "status": "blocked_now",
            "required_replacement": "future/optional extension of C_e",
        },
    ]


def caption_rows() -> list[dict[str, Any]]:
    return [
        {
            "caption_id": "main_validation_table",
            "caption": (
                "Main validation benchmark on the official 3DSSG validation split. "
                "We compare source-score ranking with H002 compatibility-aware reranking on VL-SAT and Open3DSG "
                "validation predictions. Open3DSG is used as an open-vocabulary source, while quantitative "
                "Recall@K is computed after mapping to closed-vocabulary 3DSSG labels. Violation@K is our "
                "geometry-consistency metric."
            ),
        }
    ]


def markdown_table(rows: list[dict[str, Any]], fields: list[str]) -> list[str]:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")) for field in fields) + " |")
    return lines


def write_paper_table(path: Path, table_rows: list[dict[str, Any]], caveats: list[dict[str, Any]], controls: list[dict[str, Any]]) -> None:
    fields = [
        "K",
        "S0_Recall@K",
        "H002_Recall@K",
        "Delta_Recall@K",
        "S0_Violation@K",
        "H002_Violation@K",
        "Delta_Violation@K",
    ]
    caveat_fields = ["source_id", "route_family", "K", "Delta_Recall@K", "Delta_Violation@K"]
    control_fields = ["K", "control", "Delta_Recall@K", "Delta_Violation@K"]
    selected_controls = [
        row
        for row in controls
        if row.get("control") in {"source x shuffled C_e", "source x wrong-T C_e"} and str(row.get("K")) in {"5", "20", "50", "100"}
    ]
    lines = [
        "# H002 Main Validation Table",
        "",
        "Caption:",
        "",
        caption_rows()[0]["caption"],
        "",
        "## Main Table",
        "",
        *markdown_table(table_rows, fields),
        "",
        "## Required Source-Family Caveats",
        "",
        *markdown_table(caveats, caveat_fields),
        "",
        "## Compact Mechanism Controls",
        "",
        *markdown_table(selected_controls, control_fields),
        "",
        "Notes:",
        "",
        "- `S2_source_x_Ce` is computed by combining source score with `C_e` only after `C_e` is estimated from `T_e` and `G_e`.",
        "- This table uses official 3DSSG validation, not official test.",
        "- `Violation@K` is an H002 custom geometry-consistency metric.",
        "- `support_contact` remains diagnostic/failure taxonomy and is not included in the primary success aggregation.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Main Validation Table Materialization",
        "",
        "## Purpose",
        "",
        "Materialize caption-ready table rows from the locked H002 validation source-reranking artifacts.",
        "This stage does not run new metrics, tune thresholds, or touch official test data.",
        "",
        "## Result",
        "",
        "```text",
        f"artifact_root = {summary['output_artifacts']['artifact_root']}/",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"main_table_rows = {summary['decision']['main_table_rows']}",
        f"source_family_caveat_rows = {summary['decision']['source_family_caveat_rows']}",
        f"control_rows = {summary['decision']['control_rows']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Interpretation",
        "",
        "- The materialized main table compares `S0_source_score` and `S2_source_x_Ce` over K = {5, 10, 20, 50, 100}.",
        "- The table is main validation benchmark material, not an official test result.",
        "- Source-family caveats are retained because 3/20 cells show small Recall@K regressions.",
        "- H003 embedding remains outside the current main table.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    claim_summary = read_json(args.claim_lock_dir / "summary.json")
    skeleton_summary = read_json(args.skeleton_dir / "summary.json")
    runtime_manifest = read_json(args.runtime_dir / "metric_manifest.json")
    errors = validate_inputs(claim_summary, skeleton_summary, runtime_manifest, args)

    primary_rows = read_csv(args.skeleton_dir / "primary_tradeoff_table.csv")
    caveat_rows = read_csv(args.skeleton_dir / "source_family_caveat_table.csv")
    control_rows = read_csv(args.skeleton_dir / "control_table.csv")
    if len(primary_rows) != len(K_GRID):
        errors.append({"error_type": "unexpected_primary_table_row_count", "actual": len(primary_rows), "expected": len(K_GRID)})
    if len(caveat_rows) != 3:
        errors.append({"error_type": "unexpected_source_family_caveat_count", "actual": len(caveat_rows), "expected": 3})
    if len(control_rows) != 15:
        errors.append({"error_type": "unexpected_control_row_count", "actual": len(control_rows), "expected": 15})

    table_rows = main_table_rows(primary_rows)
    compact_caveats = source_family_caveat_rows(caveat_rows)
    compact_controls = control_compact_rows(control_rows)
    blocked_rows = blocked_checklist_rows()
    captions = caption_rows()

    status = STATUS_ERRORS if errors else STATUS_READY
    selected_path = "input_errors_fix_before_main_validation_table_materialization" if errors else SELECTED_PATH
    next_todo = EXPECTED_CLAIM_NEXT if errors else NEXT_TODO

    validation_errors_path = args.output_dir / "validation_errors.jsonl"
    main_table_path = args.output_dir / "main_validation_table.csv"
    paper_table_path = args.output_dir / "main_validation_table.md"
    caveats_path = args.output_dir / "source_family_caveats.csv"
    controls_path = args.output_dir / "control_table_compact.csv"
    blocked_path = args.output_dir / "blocked_wording_checklist.csv"
    captions_path = args.output_dir / "caption_ready.csv"
    next_contract_path = args.output_dir / "next_contract.json"
    report_path = args.output_dir / "report.md"
    summary_path = args.output_dir / "summary.json"

    write_jsonl(validation_errors_path, errors)
    write_csv(main_table_path, table_rows)
    write_csv(caveats_path, compact_caveats)
    write_csv(controls_path, compact_controls)
    write_csv(blocked_path, blocked_rows)
    write_csv(captions_path, captions)
    write_paper_table(paper_table_path, table_rows, compact_caveats, compact_controls)
    write_json(
        next_contract_path,
        {
            "next_todo": next_todo,
            "review_inputs": [
                rel_path(main_table_path),
                rel_path(paper_table_path),
                rel_path(caveats_path),
                rel_path(controls_path),
                rel_path(blocked_path),
            ],
            "required_review_checks": [
                "caption contains official validation and not official test",
                "table reports 3 source-family-K Recall@K caveat rows",
                "main claim does not mention SOTA or leaderboard",
                "Open3DSG wording keeps open-vocabulary source / closed-label mapping boundary",
                "H003 embedding remains future/optional",
            ],
        },
    )

    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(errors),
        "next_todo": next_todo,
        "input_artifacts": {
            "claim_lock_summary": rel_path(args.claim_lock_dir / "summary.json"),
            "validation_table_skeleton_summary": rel_path(args.skeleton_dir / "summary.json"),
            "runtime_metric_manifest": rel_path(args.runtime_dir / "metric_manifest.json"),
        },
        "decision": {
            "main_validation_table_materialized": not errors,
            "paper_table_markdown_ready": not errors,
            "main_table_rows": len(table_rows),
            "source_family_caveat_rows": len(compact_caveats),
            "control_rows": len(compact_controls),
            "primary_score": "S2_source_x_Ce",
            "baseline": "S0_source_score",
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "h003_embedding_extension_in_main_claim_now": False,
            "h003_embedding_extension_future_optional": True,
        },
        "output_artifacts": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(summary_path),
            "validation_errors": rel_path(validation_errors_path),
            "main_validation_table": rel_path(main_table_path),
            "main_validation_table_markdown": rel_path(paper_table_path),
            "source_family_caveats": rel_path(caveats_path),
            "control_table_compact": rel_path(controls_path),
            "blocked_wording_checklist": rel_path(blocked_path),
            "caption_ready": rel_path(captions_path),
            "next_contract": rel_path(next_contract_path),
            "report": rel_path(report_path),
        },
    }
    write_report(report_path, summary)
    write_json(summary_path, summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
