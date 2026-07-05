#!/usr/bin/env python3
"""Plan the additional relation-family sweep after coverage review."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review"
)

EXPECTED_REVIEW_STATUS = "h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_size_relative_table_plan_ready"
EXPECTED_REVIEW_NEXT = "compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review_v1"
STATUS_READY = "h002_compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_additional_relation_family_sweep_plan_after_coverage_review_input_errors"
SELECTED_PATH = "plan_schema_first_family_sweep_with_predicate_level_fallback"
NEXT_TODO = "compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
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


def split_predicates(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def validate_inputs(
    review: dict[str, Any],
    expansion_queue: list[dict[str, str]],
    sweep_scope: list[dict[str, str]],
    review_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if review.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review.get("status")})
    if review.get("next_todo") != EXPECTED_REVIEW_NEXT:
        errors.append({"error_type": "unexpected_review_next_todo", "actual": review.get("next_todo")})
    if review.get("validation_errors") != 0:
        errors.append({"error_type": "review_validation_errors_present", "actual": review.get("validation_errors")})
    if read_jsonl(review_dir / "validation_errors.jsonl"):
        errors.append({"error_type": "review_validation_error_rows_present"})
    boundary = review.get("boundary", {})
    for key in ["h001_artifacts_modified", "paper_evidence_allowed", "test_usage", "validation_usage"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if review.get("review_verdict", {}).get("coverage_sufficient_for_promotion") is not False:
        errors.append({"error_type": "coverage_review_not_marked_insufficient"})
    if not expansion_queue:
        errors.append({"error_type": "empty_expansion_queue"})
    queue_families = {row.get("family") for row in expansion_queue}
    for family in ["relative_horizontal", "containment_in", "attachment_deferred", "part_structural", "identity_symmetry"]:
        if family not in queue_families:
            errors.append({"error_type": "missing_expansion_family", "family": family})
    scope_families = {row.get("family") for row in sweep_scope}
    for family in ["relative_vertical", "size_relative", "support_contact", "proximity"]:
        if family not in scope_families:
            errors.append({"error_type": "missing_completed_or_current_family", "family": family})
    return errors


def family_sweep_plan(expansion_queue: list[dict[str, str]]) -> list[dict[str, Any]]:
    order_overrides = {
        "relative_horizontal": {
            "execution_stage": "stage_1_reference_frame_protocol",
            "family_level_probe": "left/right/front/behind frame semantics and geometry schema",
            "success_gate": "reference frame is unambiguous and wrong-frame controls can be defined",
            "failure_action": "defer family or split into axis-specific predicate probes",
            "next_todo_if_selected": "compatibility_dataset_v3_relative_horizontal_reference_frame_protocol_plan",
        },
        "containment_in": {
            "execution_stage": "stage_2_containment_schema",
            "family_level_probe": "containment ratio, vertical enclosure, object-in-container capacity scan",
            "success_gate": "enough non-shortcut accept/reject rows after containment geometry controls",
            "failure_action": "split into standing-in, lying-in, hanging-in, inside predicate probes",
            "next_todo_if_selected": "compatibility_dataset_v3_containment_schema_capacity_plan",
        },
        "attachment_deferred": {
            "execution_stage": "stage_3_observability_heavy",
            "family_level_probe": "visual/mesh/Q_e source adapter and observability protocol",
            "success_gate": "deployable visual/mesh evidence exists without source-score or packet shortcut",
            "failure_action": "split into attached-to, hanging-on, connected-to, mounted-on predicate probes",
            "next_todo_if_selected": "compatibility_dataset_v3_attachment_visual_mesh_qe_protocol_plan",
        },
        "part_structural": {
            "execution_stage": "stage_4_structural_boundary",
            "family_level_probe": "diagnostic boundary scan for structural/part-whole predicates",
            "success_gate": "clear physical compatibility evidence exists beyond ontology/class semantics",
            "failure_action": "split into build-in, leaning-against, belonging-to, part-of, cover diagnostics",
            "next_todo_if_selected": "compatibility_dataset_v3_part_structural_boundary_scan_plan",
        },
        "identity_symmetry": {
            "execution_stage": "stage_5_out_of_scope_boundary",
            "family_level_probe": "identity/symmetry count audit and exclusion rationale",
            "success_gate": "not intended as physical compatibility route; sufficient exclusion evidence recorded",
            "failure_action": "split same-as and same-symmetry-as only for out-of-scope rationale",
            "next_todo_if_selected": "compatibility_dataset_v3_identity_symmetry_exclusion_audit_plan",
        },
    }
    rows: list[dict[str, Any]] = []
    for source in expansion_queue:
        family = source["family"]
        override = order_overrides.get(family, {})
        predicates = split_predicates(source.get("predicates", ""))
        rows.append(
            {
                "rank": source.get("rank", ""),
                "family": family,
                "predicates": "; ".join(predicates),
                "num_predicates": len(predicates),
                "execution_stage": override.get("execution_stage", ""),
                "sweep_role": source.get("sweep_role", ""),
                "family_level_probe": override.get("family_level_probe", ""),
                "success_gate": override.get("success_gate", ""),
                "failure_action": override.get("failure_action", "split into predicate-level probes"),
                "predicate_level_fallback_required": len(predicates) >= 3,
                "next_todo_if_selected": override.get("next_todo_if_selected", ""),
                "gt_total": source.get("gt_total", ""),
                "risk": source.get("risk", ""),
            }
        )
    return rows


def predicate_fallback_policy(expansion_queue: list[dict[str, str]], sweep_scope: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        {
            "policy_id": "P0",
            "family": "global",
            "predicate": "*",
            "trigger": "family-level target fails or is ambiguous",
            "action": "do not discard the whole family; run predicate-level schema/capacity/shortcut probe",
            "reason": "a family can fail because one predicate is broad/superordinate while another predicate is geometry-checkable",
            "claim_rule": "successful predicate may become predicate-level evidence; failed siblings become diagnostic/deferred",
        }
    ]
    source_rows = expansion_queue + [
        row
        for row in sweep_scope
        if row.get("family") in {"support_contact", "attachment_deferred", "containment_in", "part_structural", "relative_horizontal"}
    ]
    seen: set[tuple[str, str]] = set()
    for family_row in source_rows:
        family = family_row.get("family", "")
        predicates = split_predicates(family_row.get("predicates", ""))
        if len(predicates) < 2:
            continue
        for pred in predicates:
            key = (family, pred)
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                {
                    "policy_id": f"P_{family}_{pred}".replace(" ", "_").replace("/", "_"),
                    "family": family,
                    "predicate": pred,
                    "trigger": "family-level AUROC/control/target-identifiability fails",
                    "action": "create predicate-level probe with its own target, controls, and role decision",
                    "reason": "predicate-specific geometry semantics may differ inside the same family",
                    "claim_rule": "report predicate-level result separately; do not average into a solved-family claim",
                }
            )
    return rows


def predicate_probe_queue(expansion_queue: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family_row in expansion_queue:
        family = family_row["family"]
        for order, pred in enumerate(split_predicates(family_row.get("predicates", "")), start=1):
            priority = "primary_axis" if order <= 2 else "secondary_or_diagnostic"
            if family == "relative_horizontal" and pred in {"left", "right", "front", "behind"}:
                priority = "primary_reference_axis"
            if family == "attachment_deferred" and pred in {"attached to", "hanging on"}:
                priority = "primary_observability_axis"
            if family == "containment_in" and pred in {"standing in", "lying in"}:
                priority = "primary_containment_axis"
            rows.append(
                {
                    "family": family,
                    "predicate": pred,
                    "probe_priority": priority,
                    "probe_type": "predicate_level_fallback_or_followup",
                    "required_fields": required_fields_for_predicate(family, pred),
                    "decision_after_probe": "main_if_identifiable_else_diagnostic_or_deferred",
                }
            )
    return rows


def required_fields_for_predicate(family: str, predicate: str) -> str:
    if family == "relative_horizontal":
        return "reference frame, XY centroid/order, camera/world axes, wrong-frame control"
    if family == "containment_in":
        return "containment ratio, bbox/mesh overlap, vertical enclosure, occlusion/coverage"
    if family == "attachment_deferred":
        return "mesh contact, visual/multiview evidence, attachment point, Q_e observability"
    if family == "part_structural":
        return "part-whole ontology, structural support/contact, segmentation boundary"
    if family == "identity_symmetry":
        return "identity/symmetry evidence, duplicate instance check, out-of-scope rationale"
    return "family-specific geometry evidence"


def execution_gates() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "G1",
            "gate": "schema_first",
            "requirement": "define geometry evidence, semantic content, source confidence, Q_e fields, and blocked fields before materializing rows",
            "blocks_next_if_fail": True,
        },
        {
            "gate_id": "G2",
            "gate": "family_level_probe",
            "requirement": "try family-level route only when predicate semantics share a coherent geometry evidence axis",
            "blocks_next_if_fail": False,
        },
        {
            "gate_id": "G3",
            "gate": "predicate_level_fallback",
            "requirement": "if family-level target fails, split by predicate and inspect each relation type separately",
            "blocks_next_if_fail": True,
        },
        {
            "gate_id": "G4",
            "gate": "shortcut_audit",
            "requirement": "class-pair, predicate, source/rank, scan/endpoint, construction and geometry-rule probes must be audited",
            "blocks_next_if_fail": True,
        },
        {
            "gate_id": "G5",
            "gate": "route_decision",
            "requirement": "each family/predicate must be assigned main, diagnostic, future, deferred, or out-of-scope",
            "blocks_next_if_fail": True,
        },
    ]


def next_execution_queue(plan_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "order": row["rank"],
            "next_todo_candidate": row["next_todo_if_selected"],
            "family": row["family"],
            "start_condition": "previous family protocol/probe completed or explicitly deferred",
            "stop_condition": "family route decision plus predicate-level fallback decisions written",
        }
        for row in plan_rows
    ]


def write_report(path: Path, summary: dict[str, Any], plan_rows: list[dict[str, Any]]) -> None:
    lines = [
        "# Additional Relation-Family Sweep Plan After Coverage Review",
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
        "Proceed with a schema-first sweep over additional relation families before final H002 claim boundary.",
        "",
        "Family-level failure does not mean the whole family is discarded. If a family-level target fails,",
        "the workflow must split into predicate-level probes and inspect each relation type separately.",
        "",
        "## Sweep Order",
        "",
        "| Rank | Family | Stage | Predicate Fallback | Next TODO |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in plan_rows:
        lines.append(
            f"| {row['rank']} | `{row['family']}` | {row['execution_stage']} | "
            f"{row['predicate_level_fallback_required']} | `{row['next_todo_if_selected']}` |"
        )
    lines.extend(
        [
            "",
            "## Global Fallback Rule",
            "",
            "If a family contains multiple relation types and the family-level probe fails, run",
            "predicate-level probes before deciding the family boundary. Successful predicates may become",
            "predicate-level evidence; failed predicates remain diagnostic/deferred/out-of-scope.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    review = read_json(args.review_dir / "summary.json")
    expansion_queue = read_csv(args.review_dir / "expansion_queue.csv")
    sweep_scope = read_csv(args.review_dir / "sweep_scope.csv")
    predicate_gap = read_csv(args.review_dir / "predicate_gap_snapshot.csv")

    errors = validate_inputs(review, expansion_queue, sweep_scope, args.review_dir)
    plan_rows = family_sweep_plan(expansion_queue)
    fallback_rows = predicate_fallback_policy(expansion_queue, sweep_scope)
    predicate_rows = predicate_probe_queue(expansion_queue)
    gates = execution_gates()
    next_rows = next_execution_queue(plan_rows)

    if not any(row["family"] == "relative_horizontal" for row in plan_rows):
        errors.append({"error_type": "missing_relative_horizontal_plan"})
    if not any(row["gate"] == "predicate_level_fallback" for row in gates):
        errors.append({"error_type": "missing_predicate_fallback_gate"})
    if not any(row.get("family") == "support_contact" for row in fallback_rows):
        errors.append({"error_type": "missing_support_contact_fallback_example"})

    status = STATUS_ERRORS if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "input_paths": {
            "coverage_review": rel_path(args.review_dir),
            "expansion_queue": rel_path(args.review_dir / "expansion_queue.csv"),
            "sweep_scope": rel_path(args.review_dir / "sweep_scope.csv"),
            "predicate_gap_snapshot": rel_path(args.review_dir / "predicate_gap_snapshot.csv"),
        },
        "output_paths": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "family_sweep_plan": rel_path(args.output_dir / "family_sweep_plan.csv"),
            "predicate_fallback_policy": rel_path(args.output_dir / "predicate_fallback_policy.csv"),
            "predicate_probe_queue": rel_path(args.output_dir / "predicate_probe_queue.csv"),
            "execution_gates": rel_path(args.output_dir / "execution_gates.csv"),
            "next_execution_queue": rel_path(args.output_dir / "next_execution_queue.csv"),
            "predicate_gap_snapshot": rel_path(args.output_dir / "predicate_gap_snapshot.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "counts": {
            "family_sweep_rows": len(plan_rows),
            "predicate_fallback_policy_rows": len(fallback_rows),
            "predicate_probe_rows": len(predicate_rows),
            "execution_gate_rows": len(gates),
            "predicate_gap_rows": len(predicate_gap),
        },
        "selected_next_family": "relative_horizontal",
        "selected_next_todo": NEXT_TODO,
        "user_rule_encoded": (
            "If a multi-predicate family fails at family level, observe and decide each relation type separately."
        ),
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "split": "train_only_sweep_plan",
            "test_usage": False,
            "validation_usage": False,
            "all_family_model_training_allowed": False,
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "family_sweep_plan.csv", plan_rows)
    write_csv(args.output_dir / "predicate_fallback_policy.csv", fallback_rows)
    write_csv(args.output_dir / "predicate_probe_queue.csv", predicate_rows)
    write_csv(args.output_dir / "execution_gates.csv", gates)
    write_csv(args.output_dir / "next_execution_queue.csv", next_rows)
    write_csv(args.output_dir / "predicate_gap_snapshot.csv", predicate_gap)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", summary, plan_rows)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
