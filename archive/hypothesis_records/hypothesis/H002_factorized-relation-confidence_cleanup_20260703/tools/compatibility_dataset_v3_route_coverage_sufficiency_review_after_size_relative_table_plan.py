#!/usr/bin/env python3
"""Review route coverage after the size-relative-aware table plan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_TABLE_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis"
)
DEFAULT_COVERAGE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan"
DEFAULT_CAPACITY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relation_family_generalization_capacity_scan"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan"
)

EXPECTED_TABLE_STATUS = "h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_size_relative_synthesis_ready"
EXPECTED_TABLE_NEXT = "compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan"
EXPECTED_COVERAGE_STATUS = "h002_compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan_ready"
EXPECTED_CAPACITY_STATUS = "h002_compatibility_dataset_v3_relation_family_generalization_capacity_scan_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan_input_errors"
SELECTED_PATH = "coverage_not_sufficient_add_relation_family_sweep_before_promotion"
NEXT_TODO = "compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table-dir", type=Path, default=DEFAULT_TABLE_DIR)
    parser.add_argument("--coverage-dir", type=Path, default=DEFAULT_COVERAGE_DIR)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
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
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    table_summary: dict[str, Any],
    coverage_summary: dict[str, Any],
    capacity_summary: dict[str, Any],
    main_tables: list[dict[str, str]],
    route_taxonomy: list[dict[str, str]],
    coverage_rows: list[dict[str, str]],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = {
        "table": (table_summary, EXPECTED_TABLE_STATUS),
        "coverage": (coverage_summary, EXPECTED_COVERAGE_STATUS),
        "capacity": (capacity_summary, EXPECTED_CAPACITY_STATUS),
    }
    for name, (summary, expected_status) in expected.items():
        if summary.get("status") != expected_status:
            errors.append({"input": name, "error_type": "unexpected_status", "actual": summary.get("status")})
        if summary.get("validation_errors") != 0:
            errors.append({"input": name, "error_type": "validation_errors_present", "actual": summary.get("validation_errors")})
        rows = read_jsonl(roots[name] / "validation_errors.jsonl")
        if rows:
            errors.append({"input": name, "error_type": "validation_error_rows_present", "rows": len(rows)})
        boundary = summary.get("boundary", {})
        for key in ["h001_artifacts_modified", "paper_evidence_allowed", "test_usage", "validation_usage"]:
            if key in boundary and boundary.get(key) is not False:
                errors.append({"input": name, "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})

    if table_summary.get("next_todo") != EXPECTED_TABLE_NEXT:
        errors.append({"input": "table", "error_type": "unexpected_next_todo", "actual": table_summary.get("next_todo")})

    main_t1 = next((row for row in main_tables if row.get("table_id") == "T1"), {})
    for family in ["relative_vertical", "size_relative", "support_contact"]:
        if family not in main_t1.get("rows", ""):
            errors.append({"input": "main_table", "error_type": "missing_t1_family", "family": family})
    route_families = {row.get("family") for row in route_taxonomy}
    for family in ["proximity", "support_contact_superordinate", "attachment_like", "relative_horizontal"]:
        if family not in route_families:
            errors.append({"input": "route_taxonomy", "error_type": "missing_route_family", "family": family})

    coverage_by_family = {row.get("family"): row for row in coverage_rows}
    for family in ["relative_horizontal", "attachment_deferred", "containment_in", "part_structural", "identity_symmetry"]:
        if family not in coverage_by_family:
            errors.append({"input": "coverage", "error_type": "missing_gap_family", "family": family})
    return errors


def coverage_decision() -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "D1",
            "decision": "coverage_not_sufficient_for_promotion",
            "verdict": "selected",
            "reason": "Current main rows cover clean vertical, clean size, and challenging support/contact, but several high-mass or semantically distinct families remain untested.",
            "next_action": "run additional relation-family sweep before promotion planning",
        },
        {
            "decision_id": "D2",
            "decision": "promote_current_three_family_table_now",
            "verdict": "reject",
            "reason": "Reviewer can still ask whether the method only works on vertical/size/support families.",
            "next_action": "defer paper-promotion planning",
        },
        {
            "decision_id": "D3",
            "decision": "train_all_relation_families_in_one_model_now",
            "verdict": "reject",
            "reason": "Many families need new evidence schema/source adapters; direct all-family training would mix incompatible targets and shortcuts.",
            "next_action": "sweep families with schema-first probes",
        },
        {
            "decision_id": "D4",
            "decision": "perform_broad_family_sweep_then_judge",
            "verdict": "selected",
            "reason": "Matches the current research strategy: test remaining relation families first, then decide final claim boundary.",
            "next_action": NEXT_TODO,
        },
    ]


def expansion_queue(coverage_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows_by_family = {row["family"]: row for row in coverage_rows}
    order = [
        {
            "rank": 1,
            "family": "relative_horizontal",
            "predicates": "left; right; front; behind; in front of",
            "sweep_role": "high_value_reference_frame_probe",
            "why_next": "largest missing GT mass and common reviewer question, but needs reference-frame protocol before rows",
            "required_first_step": "reference_frame_protocol_and_schema_probe_plan",
            "expected_outcome": "likely deferred or controlled if world/camera/viewer-frame ambiguity cannot be fixed",
        },
        {
            "rank": 2,
            "family": "containment_in",
            "predicates": "standing in; lying in; hanging in; inside",
            "sweep_role": "containment_schema_probe",
            "why_next": "semantically distinct from vertical/size/support and directly geometry-checkable via containment ratio, despite low GT count",
            "required_first_step": "containment_geometry_schema_and_capacity_scan",
            "expected_outcome": "main if target is identifiable; otherwise diagnostic low-count family",
        },
        {
            "rank": 3,
            "family": "attachment_deferred",
            "predicates": "attached to; hanging on; connected to; mounted on",
            "sweep_role": "observability_heavy_visual_mesh_probe",
            "why_next": "important hard family that tests Q_e and visual/mesh observability, but not suitable for immediate scalar geometry-only target",
            "required_first_step": "visual_mesh_source_adapter_and_Qe_protocol",
            "expected_outcome": "future/diagnostic unless deployable visual/mesh evidence passes shortcut controls",
        },
        {
            "rank": 4,
            "family": "part_structural",
            "predicates": "build in; leaning against; belonging to; part of; cover",
            "sweep_role": "structural_semantic_boundary_probe",
            "why_next": "tests whether H002 should exclude ontology/part-whole-like relations from geometry compatibility claims",
            "required_first_step": "diagnostic_schema_boundary_scan",
            "expected_outcome": "likely diagnostic/out-of-scope rather than main C_e route",
        },
        {
            "rank": 5,
            "family": "identity_symmetry",
            "predicates": "same as; same symmetry as",
            "sweep_role": "out_of_scope_boundary_probe",
            "why_next": "not a physical predicate-geometry compatibility relation, but documenting exclusion improves reviewer defense",
            "required_first_step": "out_of_scope_rationale_and_count_audit",
            "expected_outcome": "exclude from current physical compatibility claim",
        },
    ]
    out: list[dict[str, Any]] = []
    for row in order:
        cov = rows_by_family.get(row["family"], {})
        merged = dict(row)
        merged.update(
            {
                "gt_total": cov.get("gt_total", ""),
                "queue_total": cov.get("queue_total", ""),
                "current_coverage_class": cov.get("coverage_class", ""),
                "previous_decision": cov.get("decision", ""),
                "risk": cov.get("risk", ""),
            }
        )
        out.append(merged)
    return out


def sweep_scope(coverage_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    covered_or_completed = {
        "relative_vertical": "main_clean_completed",
        "size_relative": "main_clean_completed",
        "support_contact": "main_challenging_caveated_completed",
        "proximity": "diagnostic_geometry_easy_completed",
    }
    out: list[dict[str, Any]] = []
    for row in coverage_rows:
        family = row["family"]
        status = covered_or_completed.get(family, "remaining_or_deferred")
        if family == "background_none":
            status = "exclude_not_relation"
        out.append(
            {
                "family": family,
                "predicates": row.get("predicates", ""),
                "gt_total": row.get("gt_total", ""),
                "queue_total": row.get("queue_total", ""),
                "status_after_review": status,
                "paper_role_after_review": row.get("paper_role", ""),
                "coverage_decision": row.get("decision", ""),
                "next_action_after_review": (
                    "already_in_current_table_or_diagnostic"
                    if family in covered_or_completed
                    else "covered_by_additional_sweep_or_exclusion_rationale"
                ),
            }
        )
    return out


def reviewer_risks() -> list[dict[str, Any]]:
    return [
        {
            "risk": "current table may look cherry-picked",
            "severity": "high",
            "response": "Run a family sweep over remaining missing/deferred relation families before final claim boundary.",
            "artifact_needed": "additional relation-family sweep plan and per-family protocol notes",
        },
        {
            "risk": "horizontal relations have high GT mass but no result",
            "severity": "high",
            "response": "Do not ignore them; first define reference-frame semantics and then decide if materialization is valid.",
            "artifact_needed": "relative-horizontal reference-frame protocol",
        },
        {
            "risk": "attachment relations are important but deferred",
            "severity": "medium",
            "response": "Treat them as observability-heavy; require visual/mesh/Q_e adapter before learned input.",
            "artifact_needed": "attachment visual/mesh source adapter protocol",
        },
        {
            "risk": "containment low count may be dismissed",
            "severity": "medium",
            "response": "Run schema/capacity probe; if sparse, keep as diagnostic but document why.",
            "artifact_needed": "containment geometry schema scan",
        },
        {
            "risk": "part/identity families are not geometry-compatibility",
            "severity": "medium",
            "response": "Document exclusion as a principled boundary, not a missing experiment.",
            "artifact_needed": "out-of-scope boundary table",
        },
    ]


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Plan an additional relation-family sweep before H002 promotion planning.",
        "user_direction": "add more relation families and judge after checking them broadly",
        "must_include": [
            "relative_horizontal reference-frame protocol",
            "containment_in schema/capacity probe",
            "attachment_deferred visual/mesh/Q_e protocol",
            "part_structural diagnostic boundary",
            "identity_symmetry out-of-scope rationale",
        ],
        "must_not_do": [
            "do not train one all-family model before schemas are defined",
            "do not promote current three-family table as final paper result",
            "do not use validation/test for target construction",
            "do not modify H001 artifacts",
        ],
        "recommended_execution_style": "schema-first sweep, then per-family promote/diagnostic/defer decision",
    }


def write_report(
    path: Path,
    summary: dict[str, Any],
    queue: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
) -> None:
    lines = [
        "# Route Coverage Sufficiency Review After Size-Relative Table Plan",
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
        "## Decision",
        "",
        "Current route coverage is not sufficient for promotion planning. The next step should add",
        "more relation families through schema-first probes, then decide the final claim boundary.",
        "",
        "This follows the current user direction: check more relation families first, then judge.",
        "",
        "## Expansion Queue",
        "",
        "| Rank | Family | Role | Required First Step | Expected Outcome |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in queue:
        lines.append(
            f"| {row['rank']} | `{row['family']}` | {row['sweep_role']} | "
            f"{row['required_first_step']} | {row['expected_outcome']} |"
        )
    lines.extend(["", "## Route Decisions", "", "| Decision | Verdict | Reason |", "| --- | --- | --- |"])
    for row in decisions:
        lines.append(f"| `{row['decision']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- No paper-level H002 claim yet.",
            "- No all-family model training before per-family schemas are defined.",
            "- Current three main rows are useful but not enough to stop exploration.",
            "- H001 artifacts remain untouched.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    table_summary = read_json(args.table_dir / "summary.json")
    coverage_summary = read_json(args.coverage_dir / "summary.json")
    capacity_summary = read_json(args.capacity_dir / "summary.json")
    main_tables = read_csv(args.table_dir / "main_table_plan.csv")
    route_taxonomy = read_csv(args.table_dir / "route_taxonomy_table.csv")
    coverage_rows = read_csv(args.coverage_dir / "family_coverage_gap.csv")
    predicate_gap = read_csv(args.coverage_dir / "predicate_coverage_gap.csv")

    roots = {"table": args.table_dir, "coverage": args.coverage_dir, "capacity": args.capacity_dir}
    errors = validate_inputs(
        table_summary,
        coverage_summary,
        capacity_summary,
        main_tables,
        route_taxonomy,
        coverage_rows,
        roots,
    )
    decisions = coverage_decision()
    queue = expansion_queue(coverage_rows)
    scope = sweep_scope(coverage_rows)
    risks = reviewer_risks()
    contract = next_plan_contract()

    if not queue:
        errors.append({"error_type": "empty_expansion_queue"})
    if queue and queue[0]["family"] != "relative_horizontal":
        errors.append({"error_type": "unexpected_first_expansion_family", "actual": queue[0]["family"]})

    status = STATUS_ERRORS if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "input_paths": {
            "table_plan": rel_path(args.table_dir),
            "coverage_gap": rel_path(args.coverage_dir),
            "capacity_scan": rel_path(args.capacity_dir),
        },
        "output_paths": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "coverage_decision": rel_path(args.output_dir / "coverage_decision.csv"),
            "expansion_queue": rel_path(args.output_dir / "expansion_queue.csv"),
            "sweep_scope": rel_path(args.output_dir / "sweep_scope.csv"),
            "predicate_gap_snapshot": rel_path(args.output_dir / "predicate_gap_snapshot.csv"),
            "reviewer_risks": rel_path(args.output_dir / "reviewer_risks.csv"),
            "next_plan_contract": rel_path(args.output_dir / "next_plan_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "counts": {
            "current_main_mechanism_families": 3,
            "coverage_gap_families": len(coverage_rows),
            "predicate_gap_rows": len(predicate_gap),
            "expansion_queue_rows": len(queue),
            "sweep_scope_rows": len(scope),
        },
        "review_verdict": {
            "coverage_sufficient_for_promotion": False,
            "reason": "Additional relation families should be checked before final H002 claim boundary.",
            "selected_next_family": queue[0]["family"] if queue else None,
            "selected_next_mode": "broad_schema_first_family_sweep",
        },
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "split": "train_only_coverage_review",
            "test_usage": False,
            "validation_usage": False,
            "all_family_model_training_allowed": False,
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "coverage_decision.csv", decisions)
    write_csv(args.output_dir / "expansion_queue.csv", queue)
    write_csv(args.output_dir / "sweep_scope.csv", scope)
    write_csv(args.output_dir / "predicate_gap_snapshot.csv", predicate_gap)
    write_csv(args.output_dir / "reviewer_risks.csv", risks)
    write_json(args.output_dir / "next_plan_contract.json", contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", summary, queue, decisions)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
