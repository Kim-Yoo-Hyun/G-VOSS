#!/usr/bin/env python3
"""Decide the H002 path after the v16 cross-stratum capacity scan."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_CAPACITY_DIR = RGA_ROOT / "reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v16_cross_stratum_support_contact_contrast_path_decision_after_capacity_scan"

EXPECTED_CAPACITY_STATUS = "h002_reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan_blocked_capacity_or_controls"
EXPECTED_CAPACITY_NEXT = "reliability_target_v16_cross_stratum_support_contact_contrast_path_decision_after_capacity_scan"

STATUS = "h002_reliability_target_v16_cross_stratum_path_decision_select_attachment_deferred_witness_schema_probe"
SELECTED_PATH = "freeze_v16_diagnostic_select_v17_attachment_deferred_witness_schema_probe"
NEXT_TODO = "reliability_target_v17_attachment_deferred_witness_schema_probe_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def validate_capacity(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_CAPACITY_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "expected": EXPECTED_CAPACITY_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_CAPACITY_NEXT:
        errors.append({"error_type": "unexpected_capacity_next_todo", "expected": EXPECTED_CAPACITY_NEXT, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "capacity_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "capacity_boundary_violation", "key": key, "actual": boundary.get(key)})

    decision = summary.get("capacity_decision", {})
    checks = decision.get("checks", {})
    if decision.get("capacity_pass") is not False:
        errors.append({"error_type": "capacity_should_be_blocked_for_this_decision", "actual": decision.get("capacity_pass")})
    expected_failed = {
        "selected_targets_after_caps_pass",
        "primary_hl_selected_100",
        "primary_lh_selected_100",
        "mixed_primary_blocks_available",
        "selected_primary_blocks_with_both_sides",
        "side_axis_concentration_precheck_pass",
    }
    actual_failed = set(decision.get("failed_checks", []))
    missing = sorted(expected_failed - actual_failed)
    if missing:
        errors.append({"error_type": "expected_failed_checks_missing", "missing": missing, "actual_failed_checks": sorted(actual_failed)})
    if checks.get("quota_target_capacity_pass") is not True:
        errors.append({"error_type": "raw_quota_capacity_expected_to_pass", "actual": checks.get("quota_target_capacity_pass")})
    if checks.get("quota_minimum_capacity_pass") is not True:
        errors.append({"error_type": "minimum_quota_capacity_expected_to_pass", "actual": checks.get("quota_minimum_capacity_pass")})
    return errors


def build_option_matrix(capacity: dict[str, Any]) -> list[dict[str, Any]]:
    selection = capacity["selection_summary"]
    blocks = capacity["block_summary"]
    return [
        {
            "option": "create_v16_label_sheet_now",
            "verdict": "reject",
            "reason": "Capacity scan failed the control gate; forcing a sheet would convert a diagnostic artifact into a shortcut-prone target.",
        },
        {
            "option": "relax_geometry_status_and_reason_caps",
            "verdict": "reject",
            "reason": "The failed caps are not incidental. HL is all unsatisfied and LH is all satisfied, so relaxing the caps would allow the target to collapse to geometry-status/reason-family shortcuts.",
        },
        {
            "option": "mine_more_lying_on_rows",
            "verdict": "reject",
            "reason": "Raw row count already passes. The blocker is independent contrast capacity, not additional rows.",
            "evidence": {
                "P1_selected": selection["selected_by_cell"].get("P1_lie_hl_primary_overconfidence", 0),
                "P2_selected": selection["selected_by_cell"].get("P2_lie_lh_primary_underconfidence", 0),
                "primary_mixed_blocks_available": blocks["primary_mixed_blocks_available"],
            },
        },
        {
            "option": "keep_v16_as_diagnostic_only",
            "verdict": "select_as_freeze",
            "reason": "v16 is useful negative evidence: it shows why raw HL/LH capacity is not enough for a posterior target.",
        },
        {
            "option": "try_more_support_contact_predicates_immediately",
            "verdict": "reject_for_now",
            "reason": "standing-on has no eligible HL after hard filtering, and support/contact is currently dominated by lying-on plus deterministic geometry-status coupling.",
        },
        {
            "option": "move_to_attachment_deferred_witness_schema_probe",
            "verdict": "select_as_next_route",
            "reason": "Attachment relations need a richer typed witness schema before target construction. This directly addresses the current failure: a binary satisfied/unsatisfied support rule is too easy to shortcut.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "defer",
            "reason": "Multi-view should remain audit/confirmation evidence until a geometry/label target independent of construction shortcuts exists.",
        },
    ]


def selected_plan(capacity: dict[str, Any]) -> dict[str, Any]:
    cell_capacity = {row["cell_id"]: row for row in capacity["capacity_by_cell"]}
    return {
        "selected_path": SELECTED_PATH,
        "current_route_disposition": "v16_cross_stratum_support_contact_contrast_frozen_as_diagnostic_only",
        "next_todo": NEXT_TODO,
        "posterior_smoke_allowed": False,
        "why_v16_is_frozen": [
            "The target candidate rows exist, but the contrast is not independently usable.",
            "The primary sides encode geometry-status almost deterministically: HL means unsatisfied, LH means satisfied in the selected family.",
            "A posterior trained after simply relaxing caps would be rewarded for reading the construction artifact, not relation reliability.",
        ],
        "capacity_snapshot": {
            "eligible_target_rows": capacity["counts"]["eligible_target_rows"],
            "lying_on_hl_eligible": cell_capacity["P1_lie_hl_primary_overconfidence"]["eligible_rows"],
            "lying_on_lh_eligible": cell_capacity["P2_lie_lh_primary_underconfidence"]["eligible_rows"],
            "standing_on_lh_eligible": cell_capacity["D1_stand_lh_diversity_diagnostic"]["eligible_rows"],
            "lower_than_lh_eligible": cell_capacity["C1_vertical_lower_control"]["eligible_rows"],
            "selected_by_cell": capacity["selection_summary"]["selected_by_cell"],
            "selection_deficits": capacity["selection_summary"]["deficits"],
            "primary_mixed_blocks_available": capacity["block_summary"]["primary_mixed_blocks_available"],
            "selected_primary_blocks_with_both_sides": capacity["selection_summary"]["selected_primary_blocks_with_both_sides"],
            "risk_flags": capacity["shortcut_risk_precheck"]["risk_flags"],
        },
        "next_route": {
            "name": "attachment_deferred_witness_schema_probe",
            "relation_scope": ["attached to", "hanging on", "connected to"],
            "purpose": "Define and capacity-check typed geometric/coverage witnesses for attachment-like relations before any target mining.",
            "reason_for_attachment": [
                "Attachment is less reducible to a single support gap than lying-on support/contact.",
                "It can expose cases where geometry evidence, visual context, and relation reliability disagree.",
                "The current RGA policy marks this family as unsupported/deferred, so the correct next step is schema design, not label mining.",
            ],
            "initial_witness_axes": [
                "contact_or_near_contact_distance",
                "relative_pose_and_vertical_anchor_plausibility",
                "surface_or_support_normal_alignment_if_available",
                "containment_or_overlap_proxy_when_relevant",
                "object_affordance_or_attachment_context_bucket",
                "coverage_state",
                "uncertainty_state",
            ],
            "multi_view_policy": "audit_or_confirmation_evidence_only_at_first; not deployable model input",
            "train_only": True,
        },
        "gates_before_posterior": [
            "witness schema probe must not use validation/test",
            "capacity scan must report candidate counts and unsupported/missing coverage separately",
            "candidate mining must hide queue/rank/geometry-status construction fields",
            "label fill and ingestion must happen before any model smoke",
            "target-independence audit must pass before semantic_only/geometry_only/factorized comparison",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["selected_plan"]
    snap = plan["capacity_snapshot"]
    lines = [
        "# H002 V16 Cross-Stratum Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Decision",
        "",
        "Freeze v16 as diagnostic-only and move to an `attachment_deferred` witness schema probe.",
        "",
        "## Evidence",
        "",
        "```text",
        f"lying_on_hl_eligible = {snap['lying_on_hl_eligible']}",
        f"lying_on_lh_eligible = {snap['lying_on_lh_eligible']}",
        f"selected_by_cell = {snap['selected_by_cell']}",
        f"selection_deficits = {snap['selection_deficits']}",
        f"primary_mixed_blocks_available = {snap['primary_mixed_blocks_available']}",
        f"selected_primary_blocks_with_both_sides = {snap['selected_primary_blocks_with_both_sides']}",
        f"risk_flags = {snap['risk_flags']}",
        "```",
        "",
        "## Rationale",
        "",
        "The failure is not a lack of rows. It is that the current support/contact HL and LH sides are too tightly coupled to geometry status and reason family. Relaxing the failed caps would make the target easier, but it would also make the target less independent.",
        "",
        "## Boundary",
        "",
        "This is a train-only hypothesis path decision. It is not a label sheet, not posterior evidence, not validation/test evidence, and not paper-level evidence.",
        "",
        "## Next",
        "",
        "```text",
        summary["next_todo"],
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    capacity_dir = as_abs(args.capacity_dir)
    output_dir = as_abs(args.output_dir)
    capacity = read_json(capacity_dir / "summary.json")
    errors = validate_capacity(capacity)
    option_matrix = build_option_matrix(capacity)
    plan = selected_plan(capacity)
    output_dir.mkdir(parents=True, exist_ok=True)

    status = STATUS if not errors else "h002_reliability_target_v16_cross_stratum_path_decision_validation_errors"
    next_todo = NEXT_TODO if not errors else EXPECTED_CAPACITY_NEXT
    summary = {
        "schema_version": "h002_reliability_target_v16_cross_stratum_path_decision_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not errors else None,
        "next_todo": next_todo,
        "validation_errors": len(errors),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "hidden_fields_as_model_input": False,
        },
        "input_paths": {
            "capacity_summary": rel_path(capacity_dir / "summary.json"),
            "capacity_report": rel_path(capacity_dir / "report.md"),
            "capacity_by_cell": rel_path(capacity_dir / "capacity_by_cell.csv"),
            "block_capacity": rel_path(capacity_dir / "block_capacity.csv"),
            "shortcut_risk_precheck": rel_path(capacity_dir / "shortcut_risk_precheck.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "option_matrix": rel_path(output_dir / "option_matrix.json"),
            "selected_plan": rel_path(output_dir / "selected_plan.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "option_matrix": option_matrix,
        "selected_plan": plan,
        "decision": {
            "posterior_smoke_now": "blocked",
            "label_sheet_now": "blocked",
            "v16_disposition": plan["current_route_disposition"],
            "next_route": plan["next_route"]["name"],
        },
    }
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "option_matrix.json", option_matrix)
    write_json(output_dir / "selected_plan.json", plan)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next_todo={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"v16_disposition={summary['decision']['v16_disposition']}")
    print(f"next_route={summary['decision']['next_route']}")
    print(f"output_dir={summary['output_dir']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
