#!/usr/bin/env python3
"""Freeze the H002 v20 attachment endpoint-balanced counterfactual repair plan."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DIR = RGA_ROOT / (
    "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_"
    "path_decision_after_audit"
)
DEFAULT_AUDIT_DIR = RGA_ROOT / (
    "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_"
    "target_independence_audit"
)
DEFAULT_SOURCE_INVENTORY_DIR = RGA_ROOT / (
    "reliability_target_v19_attachment_deferred_independent_evidence_source_inventory"
)
DEFAULT_CAPACITY_DIR = RGA_ROOT / "reliability_target_v17_attachment_deferred_witness_schema_capacity_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / (
    "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan"
)

EXPECTED_PATH_STATUS = (
    "h002_reliability_target_v19_attachment_deferred_audit_packet_path_decision_"
    "select_v20_endpoint_balanced_counterfactual_repair_plan"
)
EXPECTED_PATH_NEXT = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan"
EXPECTED_SELECTED_PATH = (
    "freeze_v19_audit_packet_diagnostic_select_v20_endpoint_balanced_"
    "counterfactual_repair_plan"
)
EXPECTED_AUDIT_STATUS = (
    "h002_reliability_target_v19_attachment_deferred_audit_packet_"
    "target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
)
EXPECTED_SOURCE_STATUS = "h002_reliability_target_v19_attachment_deferred_independent_evidence_source_inventory_ready"
EXPECTED_CAPACITY_STATUS = (
    "h002_reliability_target_v17_attachment_deferred_witness_schema_capacity_scan_"
    "passed_ready_for_path_decision"
)

STATUS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_"
    "counterfactual_repair_plan_ready_for_capacity_scan"
)
NEXT_TODO = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-dir", type=Path, default=DEFAULT_PATH_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
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


def validate_boundary(source: str, boundary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    false_keys = [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]
    for key in false_keys:
        if key in boundary and boundary.get(key) is not False:
            errors.append(
                {
                    "error_type": "boundary_violation",
                    "source": source,
                    "key": key,
                    "expected": False,
                    "actual": boundary.get(key),
                }
            )
    return errors


def validate_inputs(
    path_summary: dict[str, Any],
    audit_summary: dict[str, Any],
    source_summary: dict[str, Any],
    capacity_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = [
        ("path_decision", path_summary, EXPECTED_PATH_STATUS),
        ("target_audit", audit_summary, EXPECTED_AUDIT_STATUS),
        ("source_inventory", source_summary, EXPECTED_SOURCE_STATUS),
        ("capacity_scan", capacity_summary, EXPECTED_CAPACITY_STATUS),
    ]
    for source, payload, status in expected:
        if payload.get("status") != status:
            errors.append({"error_type": "unexpected_status", "source": source, "expected": status, "actual": payload.get("status")})
        if payload.get("validation_errors") not in (None, 0):
            errors.append({"error_type": "upstream_validation_errors_present", "source": source, "actual": payload.get("validation_errors")})
        errors.extend(validate_boundary(source, payload.get("boundary", {})))

    if path_summary.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append({"error_type": "unexpected_path_next", "expected": EXPECTED_PATH_NEXT, "actual": path_summary.get("next_todo")})
    if path_summary.get("selected_path") != EXPECTED_SELECTED_PATH:
        errors.append({"error_type": "unexpected_selected_path", "expected": EXPECTED_SELECTED_PATH, "actual": path_summary.get("selected_path")})

    selected_plan = path_summary.get("selected_plan", {})
    if selected_plan.get("posterior_smoke_allowed") is not False:
        errors.append(
            {
                "error_type": "path_plan_unexpectedly_allows_posterior",
                "actual": selected_plan.get("posterior_smoke_allowed"),
            }
        )
    if selected_plan.get("multi_view_policy", {}).get("deployable_model_input_now") is not False:
        errors.append(
            {
                "error_type": "path_plan_unexpectedly_promotes_multiview",
                "actual": selected_plan.get("multi_view_policy", {}).get("deployable_model_input_now"),
            }
        )

    relation = audit_summary.get("target_decisions", {}).get("relation_binary", {})
    if relation.get("class_counts") != {"0": 99, "1": 26}:
        errors.append({"error_type": "unexpected_relation_counts", "expected": {"0": 99, "1": 26}, "actual": relation.get("class_counts")})
    if relation.get("class_mass_pass") is not False:
        errors.append({"error_type": "relation_class_mass_unexpectedly_passed", "actual": relation.get("class_mass_pass")})
    if relation.get("strict_clear_slice_count") != 0:
        errors.append({"error_type": "relation_strict_slice_unexpected", "actual": relation.get("strict_clear_slice_count")})
    if relation.get("diagnostic_clear_slice_count") != 0:
        errors.append({"error_type": "relation_diagnostic_slice_unexpected", "actual": relation.get("diagnostic_clear_slice_count")})

    source_counts = source_summary.get("counts", {})
    if source_counts.get("source_inventory_gate_pass") is not True:
        errors.append({"error_type": "source_inventory_gate_expected_pass", "actual": source_counts.get("source_inventory_gate_pass")})
    if source_counts.get("primary_audit_ready_rows", 0) < 160:
        errors.append({"error_type": "primary_audit_ready_too_low", "expected_min": 160, "actual": source_counts.get("primary_audit_ready_rows")})

    cap_counts = capacity_summary.get("counts", {})
    if cap_counts.get("attachment_rows", 0) <= 0:
        errors.append({"error_type": "missing_attachment_capacity", "actual": cap_counts.get("attachment_rows")})
    if cap_counts.get("raw_feature_join_coverage") != 1.0:
        errors.append({"error_type": "unexpected_raw_feature_join_coverage", "expected": 1.0, "actual": cap_counts.get("raw_feature_join_coverage")})
    return errors


def build_upstream_snapshot(
    path_summary: dict[str, Any],
    audit_summary: dict[str, Any],
    source_summary: dict[str, Any],
    capacity_summary: dict[str, Any],
) -> dict[str, Any]:
    relation = audit_summary["target_decisions"]["relation_binary"]
    geometry = audit_summary["target_decisions"]["geometry_support_binary"]
    connected = audit_summary["target_decisions"]["connected_diagnostic"]
    return {
        "v19_role": "diagnostic_only_negative_target_construction_evidence",
        "path_decision": {
            "selected_path": path_summary.get("selected_path"),
            "next_todo": path_summary.get("next_todo"),
            "option_verdicts": path_summary.get("option_verdicts"),
        },
        "relation_binary": {
            "rows": relation.get("rows"),
            "class_counts": relation.get("class_counts"),
            "min_class_count": relation.get("min_class_count"),
            "class_mass_pass": relation.get("class_mass_pass"),
            "strict_clear_slice_count": relation.get("strict_clear_slice_count"),
            "diagnostic_clear_slice_count": relation.get("diagnostic_clear_slice_count"),
        },
        "geometry_support_auxiliary": {
            "rows": geometry.get("rows"),
            "class_counts": geometry.get("class_counts"),
            "why_not_primary": "geometry_support is an evidence-axis target, not relation reliability",
        },
        "connected_diagnostic": {
            "rows": connected.get("rows"),
            "class_counts": connected.get("class_counts"),
            "why_not_primary": "functional connection needs a separate visual/mesh-functional criterion",
        },
        "shortcut_risks": {
            "full_quick_probe_risk_flags": audit_summary.get("counts", {}).get("full_quick_probe_risk_flags"),
            "slice_blocking_risk_flags": audit_summary.get("counts", {}).get("slice_blocking_risk_flags"),
            "top_shortcut_risks": path_summary.get("top_shortcut_risks", [])[:8],
        },
        "source_inventory": {
            "primary_rows": source_summary.get("counts", {}).get("primary_rows"),
            "primary_audit_ready_rows": source_summary.get("counts", {}).get("primary_audit_ready_rows"),
            "primary_by_predicate": source_summary.get("counts", {}).get("primary_by_predicate"),
            "rows_by_audit_ready_state": source_summary.get("counts", {}).get("rows_by_audit_ready_state"),
            "source_inventory_gate_pass": source_summary.get("counts", {}).get("source_inventory_gate_pass"),
        },
        "capacity_prior": {
            "attachment_rows": capacity_summary.get("counts", {}).get("attachment_rows"),
            "predicate_counts": capacity_summary.get("counts", {}).get("predicate_counts"),
            "cell_counts": capacity_summary.get("counts", {}).get("cell_counts"),
            "rank_band_counts": capacity_summary.get("counts", {}).get("rank_band_counts"),
            "distinct": capacity_summary.get("counts", {}).get("distinct"),
            "raw_feature_join_coverage": capacity_summary.get("counts", {}).get("raw_feature_join_coverage"),
        },
    }


def repair_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v20_attachment_endpoint_balanced_counterfactual_repair_contract_v1",
        "selected_route": "endpoint_balanced_counterfactual_repair",
        "purpose": "Repair the attachment reliability target so it cannot be solved by endpoint/object/predicate/scan shortcuts.",
        "primary_predicates": ["attached to", "hanging on"],
        "diagnostic_predicates": ["connected to"],
        "not_a_posterior_stage": True,
        "target_semantics": {
            "relation_reliability": "whether the relation edge should be trusted after semantic, geometry, coverage, and uncertainty evidence are considered",
            "geometry_support": "auxiliary evidence axis only; not the main target",
            "semantic_score": "source evidence axis only; not the label",
        },
        "core_requirements": [
            "use train-only candidates only",
            "mine from the full train attachment candidate pool",
            "do not reuse v19 labels as posterior labels",
            "do not loosen labels just to create positives",
            "do not promote multi-view or mesh into deployable model input",
            "write and freeze label criteria before label fill",
            "connected to remains diagnostic-only unless a separate functional criterion is defined",
        ],
    }


def sampling_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v20_attachment_sampling_contract_v1",
        "capacity_scan_required_next": True,
        "candidate_pool": {
            "source": "full train attachment_deferred candidate pool from v17 typed witness capacity scan",
            "predicates": ["attached to", "hanging on", "connected to diagnostic only"],
            "allowed_sampling_axes": [
                "predicate_label",
                "visible_subject_label",
                "visible_object_label",
                "visible_endpoint_pair",
                "scan_id",
                "subgraph_id",
                "evidence_tier",
                "typed_witness_cell",
                "anchor_affordance_bucket",
                "floor_support_confound",
                "coverage_state",
                "provisional_supported_or_contradicted_candidate",
            ],
            "sampling_axes_are_hidden_after_sampling": True,
        },
        "candidate_sample_size_options_for_capacity_scan": [240, 320, 400],
        "default_candidate_sheet_if_capacity_allows": 320,
        "minimum_post_label_binary_gate": {
            "accept_reliable_attachment_min": 60,
            "reject_unreliable_attachment_min": 60,
            "usable_binary_rows_min": 160,
            "attached_to_accept_min": 25,
            "attached_to_reject_min": 25,
            "hanging_on_accept_min": 25,
            "hanging_on_reject_min": 25,
        },
        "contrast_priority": [
            {
                "level": "E1_exact_visible_endpoint_pair_predicate_mixed",
                "goal": "same visible subject/object label pair and same predicate should contain both positive-anchor and hard-negative candidates",
                "preferred_min_mixed_groups_before_label": 30,
            },
            {
                "level": "E2_same_object_family_predicate_evidence_tier",
                "goal": "fallback when exact visible-pair contrast is too sparse",
                "preferred_min_mixed_groups_before_label": 40,
            },
            {
                "level": "E3_scan_balanced_positive_anchor_wrong_endpoint",
                "goal": "within or near a scan, pair plausible anchors with wrong-endpoint or confound negatives",
                "preferred_min_blocks_before_label": 40,
            },
            {
                "level": "E4_global_counterfactual_hard_negative",
                "goal": "add hard negatives matched by predicate/object family/evidence tier when local contrast is unavailable",
                "role": "fallback_only",
            },
        ],
        "caps": {
            "max_rows_per_scan": 4,
            "max_rows_per_subgraph": 2,
            "max_rows_per_visible_endpoint_pair": 6,
            "max_rows_per_subject_label": 32,
            "max_rows_per_object_label": 40,
            "max_rows_per_predicate_evidence_tier_cell": 80,
            "max_wall_or_floor_or_ceiling_subject_share": 0.20,
            "max_wall_or_floor_or_ceiling_object_share": 0.35,
        },
        "forbidden_shortcuts_on_visible_label_surface": [
            "scan_id",
            "subgraph_id",
            "object instance id",
            "rank band",
            "source score",
            "p_geom_valid",
            "geometry status",
            "machine hint",
            "typed witness cell id",
            "quota cell",
            "sampling role",
            "old v18 or v19 label",
            "old v18 or v19 review note",
        ],
    }


def label_protocol_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v20_attachment_label_protocol_contract_v1",
        "principle": "semantic plausibility, geometry support, and relation reliability must remain separate labels or evidence axes",
        "primary_labels": ["accept_reliable_attachment", "reject_unreliable_attachment", "abstain_uncertain"],
        "auxiliary_labels": ["geometry_supports", "geometry_contradicts", "geometry_ambiguous", "coverage_low", "coverage_sufficient"],
        "accept_criteria": [
            "subject and object identities are clear enough for the predicate",
            "visible or mesh evidence supports a physical attachment or hanging relation",
            "the relation is not better explained by ordinary support/contact/proximity alone",
            "direction is plausible for the predicate",
            "coverage is sufficient or uncertainty is low",
        ],
        "reject_criteria": [
            "wrong endpoint or wrong direction",
            "ordinary floor/table support explains the configuration better than attachment or hanging",
            "far distance, no plausible anchor, or geometry contradicts the predicate",
            "object pair is semantically plausible but no physical attachment/hanging evidence is visible",
            "relation is a dataset-frequency or object-prior artifact",
        ],
        "abstain_criteria": [
            "subject/object not visible enough",
            "connection boundary is occluded or not represented in available views/mesh",
            "thin structure or connector is missing",
            "functional connection would be required but not observable",
            "evidence conflicts and cannot be resolved without new data",
        ],
        "connected_to_policy": {
            "status": "diagnostic_only",
            "reason": "connected to can mean functional, physical, cable-like, or structural connection; current H002 does not yet have a separate functional criterion",
            "allowed_labels": ["diagnostic_connected_possible", "diagnostic_connected_ambiguous", "diagnostic_connected_reject"],
            "not_used_to_satisfy_primary_class_mass": True,
        },
        "audit_evidence_policy": {
            "multi_view_or_mesh_can_decide_labels": True,
            "multi_view_or_mesh_as_deployable_input": False,
            "label_audit_evidence_and_model_input_must_remain_separate": True,
        },
    }


def independence_gate_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v20_attachment_independence_gate_contract_v1",
        "pre_label_capacity_gates": {
            "candidate_sample_size_options_must_be_evaluated": [240, 320, 400],
            "exact_visible_pair_mixed_capacity_report_required": True,
            "object_family_mixed_capacity_report_required": True,
            "scan_balanced_counterfactual_capacity_report_required": True,
            "quota_deficit_report_required": True,
            "visible_leakage_required": 0,
            "validation_errors_required": 0,
        },
        "post_label_gates_before_target_audit": {
            "usable_binary_rows_min": 160,
            "accept_reliable_attachment_min": 60,
            "reject_unreliable_attachment_min": 60,
            "per_primary_predicate_accept_reject_min": 25,
            "abstain_allowed": True,
            "connected_rows_excluded_from_primary_binary": True,
        },
        "target_independence_gates_before_posterior": {
            "strict_clear_slice_count_min": 1,
            "diagnostic_clear_slice_count_min": 1,
            "majority_rule_excess_max_for_single_predictor": 0.10,
            "single_predictor_risk_fields": [
                "predicate_label",
                "subject_label",
                "object_label",
                "subject_object_visible_pair",
                "scan_id_hidden",
                "subgraph_id_hidden",
                "evidence_tier",
                "coverage_state",
                "rank_band_hidden",
                "geometry_status_hidden",
                "machine_hint_hidden",
                "typed_witness_cell_hidden",
                "sampling_role_hidden",
            ],
            "posterior_smoke_allowed_if_any_gate_fails": False,
        },
    }


def capacity_scan_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v20_attachment_capacity_scan_contract_v1",
        "next_todo": NEXT_TODO,
        "must_report": [
            "candidate rows by predicate and evidence tier",
            "exact visible endpoint-pair mixed capacity",
            "object-family mixed capacity",
            "positive-anchor to wrong-endpoint counterfactual blocks",
            "scan/subgraph/object-label cap deficits",
            "quota feasibility for sample sizes 240, 320, and 400",
            "expected post-label class-mass risk",
            "whether `attached to` and `hanging on` can each support accept/reject contrast",
            "whether `connected to` remains diagnostic-only",
        ],
        "do_not_do": [
            "do not fill labels",
            "do not train posterior",
            "do not use validation/test",
            "do not expose hidden sampling keys on the visible review surface",
            "do not use source score, p_geom_valid, rank band, or geometry status as target labels",
        ],
        "decision_after_capacity_scan": [
            "if capacity passes, proceed to candidate mining",
            "if exact endpoint-pair contrast fails but family/counterfactual contrast passes, use fallback with explicit caveat",
            "if all contrast routes fail, freeze attachment branch as diagnostic and reconsider relation-family scope",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    snap = summary["upstream_snapshot"]
    lines = [
        "# H002 V20 Attachment Endpoint-Balanced Counterfactual Repair Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Decision",
        "",
        "v19 audit packet target은 diagnostic-only negative target-construction evidence로 유지한다.",
        "v20은 full train attachment pool에서 endpoint/object/predicate/scan shortcut을 직접 통제하는",
        "counterfactual target repair plan으로 진행한다.",
        "",
        "## Why",
        "",
        "현재 blocker는 결합 방식이 아니라 target construction이다.",
        "",
        "```text",
        f"relation_binary = {snap['relation_binary']['class_counts']}",
        f"relation_class_mass_pass = {snap['relation_binary']['class_mass_pass']}",
        f"strict_clear_slice_count = {snap['relation_binary']['strict_clear_slice_count']}",
        f"diagnostic_clear_slice_count = {snap['relation_binary']['diagnostic_clear_slice_count']}",
        f"full_quick_probe_risk_flags = {snap['shortcut_risks']['full_quick_probe_risk_flags']}",
        f"slice_blocking_risk_flags = {snap['shortcut_risks']['slice_blocking_risk_flags']}",
        "```",
        "",
        "## Repair Contract",
        "",
        "- Primary predicates: `attached to`, `hanging on`.",
        "- `connected to` remains diagnostic-only.",
        "- Capacity scan must evaluate sample sizes `240`, `320`, and `400`.",
        "- Default candidate sheet is `320` only if caps and contrast capacity pass.",
        "- Post-label gate requires at least `60/60` accept/reject and `160` usable binary rows.",
        "- Multi-view/mesh remains label/audit confirmation evidence only.",
        "- Posterior smoke remains blocked until a repaired target passes target-independence audit.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    path_dir = as_abs(args.path_dir)
    audit_dir = as_abs(args.audit_dir)
    source_dir = as_abs(args.source_inventory_dir)
    capacity_dir = as_abs(args.capacity_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path_summary = read_json(path_dir / "summary.json")
    audit_summary = read_json(audit_dir / "summary.json")
    source_summary = read_json(source_dir / "summary.json")
    capacity_summary = read_json(capacity_dir / "summary.json")

    validation_errors = validate_inputs(path_summary, audit_summary, source_summary, capacity_summary)
    upstream = build_upstream_snapshot(path_summary, audit_summary, source_summary, capacity_summary)
    repair = repair_contract()
    sampling = sampling_contract()
    labels = label_protocol_contract()
    independence = independence_gate_contract()
    capacity = capacity_scan_contract()

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "upstream_snapshot": output_dir / "upstream_snapshot.json",
        "repair_contract": output_dir / "repair_contract.json",
        "sampling_contract": output_dir / "sampling_contract.json",
        "label_protocol_contract": output_dir / "label_protocol_contract.json",
        "independence_gate_contract": output_dir / "independence_gate_contract.json",
        "capacity_scan_contract": output_dir / "capacity_scan_contract.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan_v1",
        "status": STATUS if not validation_errors else "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "path_decision_summary": rel_path(path_dir / "summary.json"),
            "target_audit_summary": rel_path(audit_dir / "summary.json"),
            "source_inventory_summary": rel_path(source_dir / "summary.json"),
            "capacity_scan_summary": rel_path(capacity_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "upstream_snapshot": upstream,
        "selected_repair_route": {
            "name": "endpoint_balanced_counterfactual_repair",
            "primary_predicates": ["attached to", "hanging on"],
            "diagnostic_predicates": ["connected to"],
            "next_gate": NEXT_TODO,
            "posterior_smoke_allowed": False,
        },
        "post_label_minimums": sampling["minimum_post_label_binary_gate"],
        "capacity_scan_required": True,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "candidate_mining_allowed": False,
            "capacity_scan_allowed_next": True,
            "hidden_fields_as_model_input": False,
            "uses_source_score_or_rank": False,
            "uses_p_geom_valid": False,
            "uses_geometry_status_or_rank_hint": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_or_mesh_as_audit_or_confirmation_evidence_only": True,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["upstream_snapshot"], upstream)
    write_json(output_paths["repair_contract"], repair)
    write_json(output_paths["sampling_contract"], sampling)
    write_json(output_paths["label_protocol_contract"], labels)
    write_json(output_paths["independence_gate_contract"], independence)
    write_json(output_paths["capacity_scan_contract"], capacity)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"selected_route={summary['selected_repair_route']['name']}")
    print(f"primary_predicates={','.join(summary['selected_repair_route']['primary_predicates'])}")
    print(f"diagnostic_predicates={','.join(summary['selected_repair_route']['diagnostic_predicates'])}")
    print(f"post_label_accept_min={summary['post_label_minimums']['accept_reliable_attachment_min']}")
    print(f"post_label_reject_min={summary['post_label_minimums']['reject_unreliable_attachment_min']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
