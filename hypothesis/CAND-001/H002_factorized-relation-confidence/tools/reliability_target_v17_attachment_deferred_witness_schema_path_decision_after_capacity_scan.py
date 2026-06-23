#!/usr/bin/env python3
"""Decide the H002 path after the v17 attachment witness capacity scan."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_CAPACITY_DIR = RGA_ROOT / "reliability_target_v17_attachment_deferred_witness_schema_capacity_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v17_attachment_deferred_witness_schema_path_decision_after_capacity_scan"

EXPECTED_CAPACITY_STATUS = "h002_reliability_target_v17_attachment_deferred_witness_schema_capacity_scan_passed_ready_for_path_decision"
EXPECTED_CAPACITY_NEXT = "reliability_target_v17_attachment_deferred_witness_schema_path_decision_after_capacity_scan"

STATUS = "h002_reliability_target_v17_attachment_deferred_witness_schema_path_decision_select_attachment_candidate_mining"
SELECTED_PATH = "select_v18_attachment_deferred_candidate_mining_attached_hanging_primary_connected_diagnostic"
NEXT_TODO = "reliability_target_v18_attachment_deferred_candidate_mining"


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
        errors.append(
            {
                "error_type": "unexpected_capacity_status",
                "expected": EXPECTED_CAPACITY_STATUS,
                "actual": summary.get("status"),
            }
        )
    if summary.get("next_todo") != EXPECTED_CAPACITY_NEXT:
        errors.append(
            {
                "error_type": "unexpected_capacity_next_todo",
                "expected": EXPECTED_CAPACITY_NEXT,
                "actual": summary.get("next_todo"),
            }
        )

    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "label_sheet_created",
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
    if decision.get("capacity_pass") is not True:
        errors.append({"error_type": "capacity_expected_to_pass", "actual": decision.get("capacity_pass")})
    if decision.get("failed_checks"):
        errors.append({"error_type": "capacity_failed_checks_present", "actual": decision.get("failed_checks")})
    if decision.get("forbidden_visible_field_hits") != 0:
        errors.append({"error_type": "forbidden_visible_field_hits_present", "actual": decision.get("forbidden_visible_field_hits")})

    counts = summary.get("counts", {})
    selection = summary.get("selection_summary", {})
    if counts.get("raw_feature_join_coverage", 0.0) < 0.95:
        errors.append({"error_type": "raw_feature_join_coverage_too_low", "actual": counts.get("raw_feature_join_coverage")})
    if selection.get("selected_total") != 240:
        errors.append({"error_type": "unexpected_selected_total", "expected": 240, "actual": selection.get("selected_total")})
    if selection.get("deficits") != {}:
        errors.append({"error_type": "selection_deficits_present", "actual": selection.get("deficits")})

    required_cells = {
        "A1_attached_near_anchor_supported_candidate": 40,
        "A2_attached_far_or_floor_confound_candidate": 40,
        "H1_hanging_anchor_supported_candidate": 40,
        "H2_hanging_no_anchor_or_floor_supported_candidate": 40,
        "C1_connected_near_or_overlap_diagnostic": 30,
        "C2_connected_far_or_functional_ambiguous_diagnostic": 30,
        "U1_attachment_missing_or_uncertain_coverage_audit": 20,
    }
    selected_by_cell = selection.get("selected_by_cell", {})
    for cell_id, expected in required_cells.items():
        if selected_by_cell.get(cell_id) != expected:
            errors.append(
                {
                    "error_type": "unexpected_selected_cell_count",
                    "cell_id": cell_id,
                    "expected": expected,
                    "actual": selected_by_cell.get(cell_id),
                }
            )
    return errors


def build_option_matrix(capacity: dict[str, Any]) -> list[dict[str, Any]]:
    counts = capacity["counts"]
    selection = capacity["selection_summary"]
    return [
        {
            "option": "create_label_sheet_directly_from_capacity_preview",
            "verdict": "reject",
            "reason": "The preview is an internal capacity artifact. It still contains construction state and is not a label-ready surface.",
        },
        {
            "option": "proceed_to_candidate_mining_for_attached_and_hanging",
            "verdict": "select_as_primary_route",
            "reason": "`attached to` and `hanging on` have sufficient supported and counter/uncertain cells, and their witness schema is less reducible to the support/contact geometry-status shortcut that blocked v16.",
            "evidence": {
                "A1_attached_supported_candidates": counts["cell_counts"]["A1_attached_near_anchor_supported_candidate"],
                "A2_attached_counter_candidates": counts["cell_counts"]["A2_attached_far_or_floor_confound_candidate"],
                "H1_hanging_supported_candidates": counts["cell_counts"]["H1_hanging_anchor_supported_candidate"],
                "H2_hanging_counter_candidates": counts["cell_counts"]["H2_hanging_no_anchor_or_floor_supported_candidate"],
                "selected_primary_rows": selection["selected_by_cell"]["A1_attached_near_anchor_supported_candidate"]
                + selection["selected_by_cell"]["A2_attached_far_or_floor_confound_candidate"]
                + selection["selected_by_cell"]["H1_hanging_anchor_supported_candidate"]
                + selection["selected_by_cell"]["H2_hanging_no_anchor_or_floor_supported_candidate"],
            },
        },
        {
            "option": "include_connected_to_as_primary_binary_target",
            "verdict": "reject_for_now",
            "reason": "`connected to` can be geometrically near or overlapping, but functional connection is not identifiable from OBB geometry alone. It should remain diagnostic/audit until visual or mesh confirmation is available.",
            "evidence": {
                "C1_connected_diagnostic_candidates": counts["cell_counts"]["C1_connected_near_or_overlap_diagnostic"],
                "C2_connected_diagnostic_candidates": counts["cell_counts"]["C2_connected_far_or_functional_ambiguous_diagnostic"],
                "functional_connection_ambiguous_rows": counts["uncertainty_flag_counts"]["functional_connection_ambiguous_without_visual_or_mesh"],
            },
        },
        {
            "option": "require_multi_view_before_any_candidate_mining",
            "verdict": "reject",
            "reason": "The next test is whether factorized semantic/geometry/coverage/uncertainty evidence is useful before deployable visual evidence is added. Multi-view remains audit-only for ambiguous rows.",
        },
        {
            "option": "use_predicate_rank_cell_or_machine_hint_as_visible_label_fields",
            "verdict": "reject",
            "reason": "Those fields are construction and sampling aids. Exposing them to label or model surfaces would recreate the shortcut-risk that earlier stages were designed to avoid.",
        },
        {
            "option": "proceed_to_v18_attachment_candidate_mining",
            "verdict": "select",
            "reason": "Capacity passes with no deficits, but a separate candidate-mining step is required to create a hidden-field-safe label packet and target-independence audit surface.",
        },
    ]


def build_selected_plan(capacity: dict[str, Any]) -> dict[str, Any]:
    counts = capacity["counts"]
    selection = capacity["selection_summary"]
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "posterior_smoke_allowed": False,
        "candidate_mining_allowed": True,
        "label_sheet_allowed_now": False,
        "primary_relation_scope": ["attached to", "hanging on"],
        "diagnostic_relation_scope": ["connected to"],
        "audit_relation_scope": ["attachment_missing_or_uncertain_coverage"],
        "why_candidate_mining_is_allowed": [
            "Raw pair geometry joins to all attachment rows in train split.",
            "Supported and counter/uncertain typed witness cells have enough capacity for `attached to` and `hanging on`.",
            "The route avoids the v16 failure mode where HL/LH directly encoded satisfied/unsatisfied status.",
            "The next step can hide construction fields before any human/codex label fill.",
        ],
        "why_direct_label_sheet_is_not_allowed": [
            "The capacity preview is still an internal sampling artifact.",
            "Hidden construction fields such as cell id, provisional status, anchor bucket, and rank band must be removed or quarantined.",
            "Label instructions need to separate accept/reject/abstain from geometry witness status.",
        ],
        "connected_to_policy": {
            "role": "diagnostic_only",
            "reason": "Functional connection may require visual or mesh evidence; OBB proximity/overlap is insufficient as a primary binary target.",
            "allowed_use_next": [
                "coverage and ambiguity audit",
                "future multi-view confirmation packet",
                "qualitative evidence for why visual factors may later extend H002",
            ],
            "forbidden_use_next": [
                "primary accept/reject binary target",
                "posterior training label",
                "paper-level performance claim",
            ],
        },
        "multi_view_policy": {
            "current_role": "audit_or_confirmation_only",
            "not_model_input": True,
            "when_to_add_as_factor": "only after the S/G/C/U factorized posterior has a target-independent label surface",
        },
        "v18_candidate_mining_contract": {
            "split": "train_only",
            "target_rows": 240,
            "primary_binary_candidate_rows": 160,
            "diagnostic_rows": 60,
            "uncertainty_audit_rows": 20,
            "primary_cells": {
                "A1_attached_near_anchor_supported_candidate": 40,
                "A2_attached_far_or_floor_confound_candidate": 40,
                "H1_hanging_anchor_supported_candidate": 40,
                "H2_hanging_no_anchor_or_floor_supported_candidate": 40,
            },
            "diagnostic_cells": {
                "C1_connected_near_or_overlap_diagnostic": 30,
                "C2_connected_far_or_functional_ambiguous_diagnostic": 30,
            },
            "audit_cells": {
                "U1_attachment_missing_or_uncertain_coverage_audit": 20,
            },
            "visible_label_fields_allowed": [
                "scan_id",
                "subgraph_id",
                "subject_id",
                "object_id",
                "subject_label",
                "object_label",
                "predicate_label",
                "source_score_or_rank",
                "short geometry witness summary",
                "coverage summary",
                "uncertainty summary",
            ],
            "hidden_fields_required": [
                "cell_id",
                "provisional_status",
                "anchor_bucket",
                "rank_band",
                "machine_hint",
                "geometry_status",
                "reason_family",
                "sampling_queue",
            ],
            "post_label_minimums_before_posterior": {
                "usable_binary_rows": 120,
                "accept_rows": 50,
                "reject_rows": 50,
                "abstain_rows_allowed_but_not_binary": True,
            },
            "required_audits_after_label_ingestion": [
                "predicate shortcut audit",
                "endpoint/object shortcut audit",
                "rank/source-score band audit",
                "hidden cell/provisional-status audit",
                "geometry-only shortcut audit",
                "same-predicate supported-vs-counter contrast audit",
            ],
        },
        "capacity_snapshot": {
            "attachment_rows": counts["attachment_rows"],
            "joined_rows": counts["joined_rows"],
            "raw_feature_join_coverage": counts["raw_feature_join_coverage"],
            "cell_counts": counts["cell_counts"],
            "selected_by_cell": selection["selected_by_cell"],
            "selection_deficits": selection["deficits"],
            "selected_scan_count": selection["selected_scan_count"],
            "selected_subgraph_count": selection["selected_subgraph_count"],
            "selected_directed_pair_count": selection["selected_directed_pair_count"],
            "selected_visible_pair_count": selection["selected_visible_pair_count"],
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["selected_plan"]
    snap = plan["capacity_snapshot"]
    lines = [
        "# H002 V17 Attachment Path Decision",
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
        "Proceed to v18 candidate mining, but only with `attached to` and `hanging on` as the primary binary relation scope. Keep `connected to` diagnostic-only.",
        "",
        "## Evidence",
        "",
        "```text",
        f"attachment_rows = {snap['attachment_rows']}",
        f"joined_rows = {snap['joined_rows']}",
        f"raw_feature_join_coverage = {snap['raw_feature_join_coverage']:.6f}",
        f"selection_deficits = {snap['selection_deficits']}",
        f"selected_by_cell = {snap['selected_by_cell']}",
        f"selected_scan_count = {snap['selected_scan_count']}",
        f"selected_subgraph_count = {snap['selected_subgraph_count']}",
        f"selected_directed_pair_count = {snap['selected_directed_pair_count']}",
        "```",
        "",
        "## Rationale",
        "",
        "`attached to` and `hanging on` have enough typed witness capacity and are less likely than v16 support/contact to collapse into a single satisfied/unsatisfied construction shortcut. `connected to` is different: near/overlap evidence can suggest a possible connection, but the relation is often functional and may need visual or mesh confirmation.",
        "",
        "## Boundary",
        "",
        "This is a train-only path decision. It authorizes candidate mining only. It is not a label sheet, not posterior evidence, not validation/test evidence, and not paper-level evidence.",
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


def main() -> None:
    args = parse_args()
    capacity_dir = as_abs(args.capacity_dir)
    output_dir = as_abs(args.output_dir)
    capacity = read_json(capacity_dir / "summary.json")
    errors = validate_capacity(capacity)

    option_matrix = build_option_matrix(capacity)
    selected_plan = build_selected_plan(capacity)

    boundary = {
        "split": "train_only",
        "validation_usage": False,
        "test_usage": False,
        "fills_new_labels": False,
        "ingests_existing_labels": False,
        "label_sheet_created": False,
        "trains_new_posterior": False,
        "posterior_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "h001_artifacts_modified": False,
        "rga_redefined_as_lh_only": False,
        "multi_view_as_model_input": False,
        "hidden_fields_as_model_input": False,
    }
    summary = {
        "schema_version": "h002_reliability_target_v17_attachment_deferred_witness_schema_path_decision_after_capacity_scan_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
        "boundary": boundary,
        "input_paths": {
            "capacity_summary": rel_path(capacity_dir / "summary.json"),
            "capacity_preview": rel_path(capacity_dir / "selection_preview_internal.jsonl"),
        },
        "output_dir": rel_path(output_dir),
        "option_matrix": option_matrix,
        "selected_plan": selected_plan,
        "decision": {
            "candidate_mining_allowed": True,
            "label_sheet_now": "blocked_until_v18_hidden_field_safe_candidate_packet",
            "posterior_smoke_now": "blocked",
            "primary_scope": ["attached to", "hanging on"],
            "diagnostic_scope": ["connected to"],
            "multi_view_policy": "audit_or_confirmation_only",
        },
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "option_matrix": rel_path(output_dir / "option_matrix.json"),
            "selected_plan": rel_path(output_dir / "selected_plan.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "option_matrix.json", option_matrix)
    write_json(output_dir / "selected_plan.json", selected_plan)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", summary)

    print(f"status={STATUS}")
    print(f"selected_path={SELECTED_PATH}")
    print(f"next_todo={NEXT_TODO}")
    print(f"validation_errors={len(errors)}")
    print(f"candidate_mining_allowed={selected_plan['candidate_mining_allowed']}")
    print(f"primary_relation_scope={','.join(selected_plan['primary_relation_scope'])}")
    print(f"diagnostic_relation_scope={','.join(selected_plan['diagnostic_relation_scope'])}")
    print(f"posterior_smoke_allowed={boundary['posterior_smoke_allowed']}")
    print(f"output_dir={rel_path(output_dir)}")


if __name__ == "__main__":
    main()
