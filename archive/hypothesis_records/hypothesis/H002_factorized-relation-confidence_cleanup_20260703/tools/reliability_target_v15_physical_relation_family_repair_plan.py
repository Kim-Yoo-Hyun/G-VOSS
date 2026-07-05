#!/usr/bin/env python3
"""Freeze the v15 physical relation-family repair contract for H002."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_path_decision_after_audit"
DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_target_independence_audit"
DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_label_ingestion"
DEFAULT_CANDIDATE_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_candidate_mining"
DEFAULT_SAMPLING_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_sampling_plan"
DEFAULT_FEASIBILITY_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_feasibility_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v15_physical_relation_family_repair_plan"

EXPECTED_PATH_STATUS = "h002_reliability_target_v14_physical_relation_family_path_decision_select_v15_repair_plan"
EXPECTED_PATH_NEXT = "reliability_target_v15_physical_relation_family_repair_plan"
EXPECTED_SELECTED_PATH = "freeze_v14_diagnostic_select_v15_witness_matched_physical_relation_repair_plan"
EXPECTED_AUDIT_STATUS = "h002_reliability_target_v14_physical_relation_family_target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
EXPECTED_INGESTION_STATUS = "h002_reliability_target_v14_physical_relation_family_label_ingested_positive_sparse_with_probe_risk"
EXPECTED_CANDIDATE_STATUS = "h002_reliability_target_v14_physical_relation_family_candidate_mining_ready_for_label_fill"
EXPECTED_SAMPLING_STATUS = "h002_reliability_target_v14_physical_relation_family_sampling_plan_ready_for_candidate_mining"
EXPECTED_FEASIBILITY_STATUS = "h002_reliability_target_v14_physical_relation_family_feasibility_scan_ready_support_primary_attachment_schema_deferred"

STATUS = "h002_reliability_target_v15_physical_relation_family_repair_plan_ready_for_capacity_scan"
NEXT_TODO = "reliability_target_v15_physical_relation_family_capacity_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-dir", type=Path, default=DEFAULT_PATH_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--sampling-dir", type=Path, default=DEFAULT_SAMPLING_DIR)
    parser.add_argument("--feasibility-dir", type=Path, default=DEFAULT_FEASIBILITY_DIR)
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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def boundary_errors(source: str, boundary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    false_keys = [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]
    for key in false_keys:
        if boundary.get(key) is not False:
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
    ingestion_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    sampling_summary: dict[str, Any],
    feasibility_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []

    expected = [
        ("path_decision", path_summary, EXPECTED_PATH_STATUS),
        ("target_audit", audit_summary, EXPECTED_AUDIT_STATUS),
        ("label_ingestion", ingestion_summary, EXPECTED_INGESTION_STATUS),
        ("candidate_mining", candidate_summary, EXPECTED_CANDIDATE_STATUS),
        ("sampling_plan", sampling_summary, EXPECTED_SAMPLING_STATUS),
        ("feasibility_scan", feasibility_summary, EXPECTED_FEASIBILITY_STATUS),
    ]
    for source, payload, expected_status in expected:
        if payload.get("status") != expected_status:
            errors.append(
                {
                    "error_type": "unexpected_status",
                    "source": source,
                    "expected": expected_status,
                    "actual": payload.get("status"),
                }
            )
        if payload.get("validation_errors") not in (None, 0):
            errors.append(
                {
                    "error_type": "upstream_validation_errors_present",
                    "source": source,
                    "actual": payload.get("validation_errors"),
                }
            )
        errors.extend(boundary_errors(source, payload.get("boundary", {})))

    if path_summary.get("next_todo") != EXPECTED_PATH_NEXT:
        errors.append(
            {
                "error_type": "unexpected_path_next_todo",
                "expected": EXPECTED_PATH_NEXT,
                "actual": path_summary.get("next_todo"),
            }
        )
    if path_summary.get("selected_path") != EXPECTED_SELECTED_PATH:
        errors.append(
            {
                "error_type": "unexpected_selected_path",
                "expected": EXPECTED_SELECTED_PATH,
                "actual": path_summary.get("selected_path"),
            }
        )

    relation = audit_summary.get("target_decisions", {}).get("relation_binary", {})
    if relation.get("posterior_allowed") is not False:
        errors.append({"error_type": "posterior_unexpectedly_allowed", "actual": relation.get("posterior_allowed")})
    if relation.get("class_counts") != {"0": 152, "1": 48}:
        errors.append({"error_type": "unexpected_v14_class_counts", "expected": {"0": 152, "1": 48}, "actual": relation.get("class_counts")})
    if relation.get("strict_clear_slice_count") != 0:
        errors.append({"error_type": "strict_slice_unexpectedly_available", "actual": relation.get("strict_clear_slice_count")})
    if relation.get("diagnostic_clear_slice_count") != 0:
        errors.append({"error_type": "diagnostic_slice_unexpectedly_available", "actual": relation.get("diagnostic_clear_slice_count")})

    selected_rows = candidate_summary.get("counts", {}).get("selected_rows")
    if selected_rows != 240:
        errors.append({"error_type": "unexpected_v14_candidate_rows", "expected": 240, "actual": selected_rows})

    return errors


def build_failure_snapshot(
    audit_summary: dict[str, Any],
    ingestion_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    sampling_summary: dict[str, Any],
    feasibility_summary: dict[str, Any],
) -> dict[str, Any]:
    relation = audit_summary["target_decisions"]["relation_binary"]
    target_viability = ingestion_summary.get("target_viability", {})
    counts = ingestion_summary.get("counts", {})
    candidate_counts = candidate_summary.get("counts", {})
    route_by_family = {row["family"]: row for row in feasibility_summary.get("route_matrix", [])}

    return {
        "v14_role": "diagnostic_target_construction_failure_evidence",
        "relation_binary": {
            "rows": relation.get("rows"),
            "class_counts": relation.get("class_counts"),
            "min_class_count": relation.get("min_class_count"),
            "class_mass_pass": relation.get("class_mass_pass"),
            "strict_clear_slice_count": relation.get("strict_clear_slice_count"),
            "diagnostic_clear_slice_count": relation.get("diagnostic_clear_slice_count"),
            "posterior_allowed": relation.get("posterior_allowed"),
        },
        "ingestion_viability": {
            "reliability_positive_rows": target_viability.get("reliability_positive_rows"),
            "reliability_negative_rows": target_viability.get("reliability_negative_rows"),
            "minimum_per_class_for_posterior": target_viability.get("minimum_per_class_for_posterior"),
            "class_mass_pass": target_viability.get("class_mass_pass"),
            "same_predicate_mixed_reliability_binary_groups": target_viability.get("same_predicate_mixed_reliability_binary_groups"),
            "same_quota_cell_mixed_reliability_binary_groups": target_viability.get("same_quota_cell_mixed_reliability_binary_groups"),
            "same_visible_pair_mixed_reliability_binary_groups": target_viability.get("same_visible_pair_mixed_reliability_binary_groups"),
        },
        "label_counts": {
            "binary_rows": counts.get("binary_rows"),
            "abstain_rows": counts.get("abstain_rows"),
            "family_groups": counts.get("family_groups"),
            "binary_target": counts.get("binary_target"),
            "geometry_support_target": counts.get("geometry_support_target"),
            "geometry_support_state_v14": counts.get("geometry_support_state_v14"),
        },
        "candidate_construction": {
            "selected_rows": candidate_counts.get("selected_rows"),
            "support_contact_rows": candidate_counts.get("support_contact_rows"),
            "relative_vertical_rows": candidate_counts.get("relative_vertical_rows"),
            "unique_scans": candidate_counts.get("unique_scans"),
            "unique_subgraphs": candidate_counts.get("unique_subgraphs"),
            "unique_directed_pairs": candidate_counts.get("unique_directed_pairs"),
            "unique_label_pairs": candidate_counts.get("unique_label_pairs"),
            "visible_leakage_hits": candidate_counts.get("visible_leakage_hits"),
            "any_hard_endpoint_rows": candidate_counts.get("any_hard_endpoint_rows"),
        },
        "v14_sampling_problem": [
            "support_contact candidate capacity exists, but v14 label surface made geometry witness evidence too directly predictive of labels",
            "relative_vertical control rows contributed easy geometry labels and should not be used to inflate primary reliability positives",
            "standing-on HL rows were practically unavailable after hard endpoint filtering, so v15 must check capacity before quota lock",
            "balanced 48/48 subsampling would not remove scan/object/pair/quota/witness shortcuts",
        ],
        "family_capacity_prior": {
            "support_contact": {
                "verdict": route_by_family.get("support_contact", {}).get("verdict"),
                "hl_rows": route_by_family.get("support_contact", {}).get("hl_rows"),
                "lh_rows": route_by_family.get("support_contact", {}).get("lh_rows"),
                "same_predicate_hl_lh_balanced_capacity": route_by_family.get("support_contact", {}).get("same_predicate_hl_lh_balanced_capacity"),
                "visible_label_pair_mixed_hl_lh_groups": route_by_family.get("support_contact", {}).get("visible_label_pair_mixed_hl_lh_groups"),
                "risk_flags": route_by_family.get("support_contact", {}).get("risk_flags"),
            },
            "relative_vertical": {
                "verdict": route_by_family.get("relative_vertical", {}).get("verdict"),
                "hl_rows": route_by_family.get("relative_vertical", {}).get("hl_rows"),
                "lh_rows": route_by_family.get("relative_vertical", {}).get("lh_rows"),
                "risk_flags": route_by_family.get("relative_vertical", {}).get("risk_flags"),
            },
            "attachment_deferred": {
                "verdict": route_by_family.get("attachment_deferred", {}).get("verdict"),
                "unsupported_share": route_by_family.get("attachment_deferred", {}).get("unsupported_share"),
                "next_action": route_by_family.get("attachment_deferred", {}).get("next_action"),
            },
        },
    }


def build_requirements() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v15_physical_relation_family_repair_requirements_v1",
        "selected_route": "support_contact_witness_matched_repair_with_relative_vertical_control",
        "primary_target": {
            "family": "support_contact",
            "allowed_predicates": ["lying on", "standing on"],
            "goal": "make relation reliability labels depend on evidence agreement, not on direct endpoint/predicate/quota shortcuts",
            "must_increase_positive_mass_without_label_relaxation": True,
            "minimum_binary_positive_after_label_fill": 60,
            "minimum_binary_negative_after_label_fill": 60,
            "preferred_binary_positive_after_label_fill": 80,
            "posterior_smoke_allowed_before_target_independence_audit": False,
        },
        "control_target": {
            "family": "relative_vertical",
            "allowed_predicates": ["lower than"],
            "role": "geometry-easy control only",
            "max_share_of_candidate_sheet": 0.20,
            "cannot_supply_primary_positive_mass": True,
        },
        "deferred_target": {
            "family": "attachment_deferred",
            "predicates": ["attached to", "connected to", "hanging on"],
            "status": "defer_until_witness_schema_exists",
            "multi_view_policy": "audit_confirmation_only_not_model_input",
        },
        "candidate_matching_axes": [
            "predicate_label",
            "source_queue_kind",
            "rank_band",
            "geometry_status",
            "p_geom_bin",
            "coarse_witness_bin",
            "reason_signature",
            "endpoint_generic_state",
            "source_semantic_score_band",
        ],
        "pre_label_group_requirements": {
            "same_matched_witness_stratum_min_candidate_rows": 6,
            "same_matched_witness_stratum_min_expected_sides": 2,
            "minimum_mixed_witness_strata_before_label_fill": 8,
            "minimum_distinct_scans": 80,
            "minimum_distinct_visible_pairs": 120,
            "max_rows_per_scan": 4,
            "max_rows_per_visible_pair": 3,
            "max_single_predicate_share": 0.80,
            "max_single_rank_band_share": 0.45,
        },
        "post_label_independence_gates": {
            "strict_slice_min_rows": 80,
            "strict_slice_min_per_class": 40,
            "diagnostic_slice_min_rows": 40,
            "diagnostic_slice_min_per_class": 15,
            "shortcut_probe_must_not_clear_using_only": [
                "scan_id",
                "subject_object_label_pair",
                "endpoint_pair_id",
                "predicate_label",
                "quota_cell",
                "rank_band",
                "machine_hint",
                "geometry_status",
                "coarse_witness_text",
            ],
        },
        "label_surface_contract": {
            "visible_fields_allowed": [
                "review_id",
                "predicate_label",
                "subject_label",
                "object_label",
                "plain_language_relation_prompt",
                "factor_separated_numeric_bins",
                "coverage_note",
                "uncertainty_note",
            ],
            "visible_fields_forbidden": [
                "label_match_status",
                "machine_hint",
                "queue_kind",
                "semantic_geometry_bucket",
                "quota_cell_id",
                "geometry_status",
                "p_geom_valid",
                "direct_accept_reject_hint",
                "support_or_vertical_witness_summary_v14",
                "phrases that directly say near contact, large vertical gap, vertical order matches, or vertical order contradicts",
            ],
            "hidden_audit_fields_only": [
                "label_match_status_hidden",
                "machine_hint_hidden",
                "rank_band_hidden",
                "queue_kind_hidden",
                "geometry_status_hidden",
                "p_geom_valid_hidden",
                "reason_codes_hidden",
            ],
        },
        "model_input_boundary": {
            "semantic_score_allowed": True,
            "object_confidence_allowed_if_available": True,
            "continuous_geometry_evidence_allowed_after_target_lock": True,
            "coverage_uncertainty_allowed_after_target_lock": True,
            "hidden_target_construction_keys_allowed": False,
            "multi_view_as_model_input_allowed_now": False,
            "posterior_training_allowed_now": False,
        },
    }


def build_quota_plan() -> list[dict[str, Any]]:
    return [
        {
            "cell_id": "P1_support_lie_witness_matched",
            "family": "support_contact",
            "predicate_label": "lying on",
            "role": "primary_repair_anchor",
            "target_rows": 160,
            "min_rows_after_capacity_scan": 120,
            "purpose": "repair support-contact positive sparsity using witness-matched candidates",
            "notes": "Must include both semantic-high/geometry-low and semantic-low/geometry-high buckets where possible; final labels cannot be inferred from queue kind.",
        },
        {
            "cell_id": "P2_support_stand_diversity_probe",
            "family": "support_contact",
            "predicate_label": "standing on",
            "role": "primary_diversity_probe",
            "target_rows": 32,
            "min_rows_after_capacity_scan": 16,
            "purpose": "check whether support-contact claim survives beyond lying-on rows",
            "notes": "Only keep if hard endpoint and room-surface shortcuts can be controlled; otherwise reallocate to P1 with explicit report.",
        },
        {
            "cell_id": "P3_support_hard_negative_or_ambiguous_match",
            "family": "support_contact",
            "predicate_label": "lying on",
            "role": "primary_hard_contrast",
            "target_rows": 32,
            "min_rows_after_capacity_scan": 24,
            "purpose": "find rows within the same support/contact witness stratum where reliability is not trivially determined by visible geometry text",
            "notes": "This cell is allowed only if capacity scan finds matched strata with mixed expected sides.",
        },
        {
            "cell_id": "C1_vertical_lower_control",
            "family": "relative_vertical",
            "predicate_label": "lower than",
            "role": "control_not_primary",
            "target_rows": 16,
            "min_rows_after_capacity_scan": 0,
            "purpose": "retain a small geometry-easy control for sanity checks",
            "notes": "Do not use this cell to satisfy the primary support-contact positive-mass gate.",
        },
    ]


def build_capacity_scan_contract(requirements: dict[str, Any], quota_plan: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v15_capacity_scan_contract_v1",
        "next_todo": NEXT_TODO,
        "inputs": {
            "hl_queue": rel_path(RGA_ROOT / "train_hl_queue.jsonl"),
            "lh_queue": rel_path(RGA_ROOT / "train_lh_queue.jsonl"),
            "v15_requirements": "requirements.json",
            "quota_plan": "quota_plan.csv",
        },
        "must_measure": [
            "eligible rows by quota cell after hard endpoint filtering",
            "capacity by candidate_matching_axes",
            "mixed expected-side strata before label fill",
            "distinct scan/subgraph/visible-pair coverage",
            "share of rows that would expose forbidden visible fields",
            "standing-on capacity after room-surface shortcut filters",
        ],
        "pass_criteria": {
            "support_contact_primary_rows_available": 224,
            "support_contact_primary_candidate_rows_after_caps": 200,
            "minimum_mixed_witness_strata_before_label_fill": requirements["pre_label_group_requirements"]["minimum_mixed_witness_strata_before_label_fill"],
            "relative_vertical_max_rows": sum(row["target_rows"] for row in quota_plan if row["family"] == "relative_vertical"),
            "forbidden_visible_field_hits": 0,
        },
        "fail_actions": [
            "if support_contact capacity fails, keep v14 diagnostic and run attachment witness schema probe instead of posterior smoke",
            "if standing-on capacity fails, reallocate to lying-on only with explicit diversity caveat",
            "if witness strata are not mixed, do not produce a label sheet",
            "if forbidden visible fields are required for label fill, redesign review packet before mining",
        ],
    }


def write_label_surface_contract(path: Path, requirements: dict[str, Any]) -> None:
    surface = requirements["label_surface_contract"]
    lines = [
        "# V15 Label Surface Contract",
        "",
        "이 문서는 v15 label sheet가 reviewer-visible field로 무엇을 보여줄 수 있는지와",
        "무엇을 숨겨야 하는지를 고정한다.",
        "",
        "## Allowed Visible Fields",
        "",
    ]
    lines.extend(f"- `{field}`" for field in surface["visible_fields_allowed"])
    lines.extend(
        [
            "",
            "## Forbidden Visible Fields",
            "",
        ]
    )
    lines.extend(f"- `{field}`" for field in surface["visible_fields_forbidden"])
    lines.extend(
        [
            "",
            "## Hidden Audit Only",
            "",
        ]
    )
    lines.extend(f"- `{field}`" for field in surface["hidden_audit_fields_only"])
    lines.extend(
        [
            "",
            "## Rationale",
            "",
            "v14의 실패 원인은 relation family 자체가 아니라, visible witness summary가 label policy를",
            "너무 직접적으로 노출한 데 있다. v15는 continuous geometry evidence를 posterior input으로",
            "사용할 가능성을 남기되, label sheet 단계에서는 direct label template를 제거한다.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    failure = summary["v14_failure_snapshot"]
    req = summary["requirements"]
    lines = [
        "# H002 V15 Physical Relation-Family Repair Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_route = {summary['selected_route']}",
        f"next_todo = {summary['next_todo']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Why V15 Exists",
        "",
        "v14는 physical relation family로 이동했지만 posterior target으로는 아직 사용할 수 없다.",
        f"Relation binary count는 `{failure['relation_binary']['class_counts']}`이고, strict/diagnostic clear slice는 각각 "
        f"`{failure['relation_binary']['strict_clear_slice_count']}` / `{failure['relation_binary']['diagnostic_clear_slice_count']}`이다.",
        "",
        "문제는 단순히 positive가 48개라서 threshold보다 2개 부족한 것이 아니다. v14는 balanced 48/48로 잘라도",
        "scan/object/pair/quota/rank/witness text가 label을 쉽게 설명할 수 있다. 따라서 다음 단계는 posterior 결합 방식이 아니라",
        "target construction repair다.",
        "",
        "## Selected Repair",
        "",
        f"- Primary: `{req['primary_target']['family']}` with `{', '.join(req['primary_target']['allowed_predicates'])}`",
        f"- Control: `{req['control_target']['family']}` with `{', '.join(req['control_target']['allowed_predicates'])}`",
        f"- Deferred: `{req['deferred_target']['family']}` until witness schema exists",
        "",
        "v15는 support/contact relation을 primary로 두고, relative vertical은 sanity/control로만 유지한다.",
        "attachment/hanging/connection 계열은 multi-view audit 후보로는 유망하지만, 현재 geometry witness가 정의되지 않았기 때문에",
        "posterior target으로 바로 쓰지 않는다.",
        "",
        "## Required Matching Axes",
        "",
    ]
    lines.extend(f"- `{axis}`" for axis in req["candidate_matching_axes"])
    lines.extend(
        [
            "",
            "## Gates",
            "",
            f"- Binary positive after label fill: at least `{req['primary_target']['minimum_binary_positive_after_label_fill']}`",
            f"- Binary negative after label fill: at least `{req['primary_target']['minimum_binary_negative_after_label_fill']}`",
            f"- Mixed witness strata before label fill: at least `{req['pre_label_group_requirements']['minimum_mixed_witness_strata_before_label_fill']}`",
            f"- Strict slice: `{req['post_label_independence_gates']['strict_slice_min_rows']}` rows with `{req['post_label_independence_gates']['strict_slice_min_per_class']}` per class",
            f"- Diagnostic slice: `{req['post_label_independence_gates']['diagnostic_slice_min_rows']}` rows with `{req['post_label_independence_gates']['diagnostic_slice_min_per_class']}` per class",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
            "The next step must run a capacity scan. If it cannot find matched support-contact strata with enough candidate mass,",
            "the branch should stop at diagnostic evidence or move to an attachment witness-schema probe instead of forcing posterior smoke.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    path_dir = as_abs(args.path_dir)
    audit_dir = as_abs(args.audit_dir)
    ingestion_dir = as_abs(args.ingestion_dir)
    candidate_dir = as_abs(args.candidate_dir)
    sampling_dir = as_abs(args.sampling_dir)
    feasibility_dir = as_abs(args.feasibility_dir)
    output_dir = as_abs(args.output_dir)

    path_summary = read_json(path_dir / "summary.json")
    audit_summary = read_json(audit_dir / "summary.json")
    ingestion_summary = read_json(ingestion_dir / "summary.json")
    candidate_summary = read_json(candidate_dir / "summary.json")
    sampling_summary = read_json(sampling_dir / "summary.json")
    feasibility_summary = read_json(feasibility_dir / "summary.json")

    errors = validate_inputs(
        path_summary=path_summary,
        audit_summary=audit_summary,
        ingestion_summary=ingestion_summary,
        candidate_summary=candidate_summary,
        sampling_summary=sampling_summary,
        feasibility_summary=feasibility_summary,
    )

    failure_snapshot = build_failure_snapshot(
        audit_summary=audit_summary,
        ingestion_summary=ingestion_summary,
        candidate_summary=candidate_summary,
        sampling_summary=sampling_summary,
        feasibility_summary=feasibility_summary,
    )
    requirements = build_requirements()
    quota_plan = build_quota_plan()
    capacity_scan_contract = build_capacity_scan_contract(requirements, quota_plan)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "v14_failure_snapshot.json", failure_snapshot)
    write_json(output_dir / "requirements.json", requirements)
    write_json(output_dir / "capacity_scan_contract.json", capacity_scan_contract)
    write_csv(
        output_dir / "quota_plan.csv",
        quota_plan,
        [
            "cell_id",
            "family",
            "predicate_label",
            "role",
            "target_rows",
            "min_rows_after_capacity_scan",
            "purpose",
            "notes",
        ],
    )
    write_label_surface_contract(output_dir / "label_surface_contract.md", requirements)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)

    summary = {
        "schema_version": "h002_reliability_target_v15_physical_relation_family_repair_plan_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS if not errors else "blocked_validation_errors",
        "selected_route": requirements["selected_route"],
        "next_todo": NEXT_TODO,
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
            "v14_path_decision_summary": rel_path(path_dir / "summary.json"),
            "v14_target_audit_summary": rel_path(audit_dir / "summary.json"),
            "v14_label_ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "v14_candidate_mining_summary": rel_path(candidate_dir / "summary.json"),
            "v14_sampling_plan_summary": rel_path(sampling_dir / "summary.json"),
            "v14_feasibility_summary": rel_path(feasibility_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "v14_failure_snapshot": rel_path(output_dir / "v14_failure_snapshot.json"),
            "requirements": rel_path(output_dir / "requirements.json"),
            "quota_plan": rel_path(output_dir / "quota_plan.csv"),
            "label_surface_contract": rel_path(output_dir / "label_surface_contract.md"),
            "capacity_scan_contract": rel_path(output_dir / "capacity_scan_contract.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "v14_failure_snapshot": failure_snapshot,
        "requirements": requirements,
        "quota_plan_total_rows": sum(row["target_rows"] for row in quota_plan),
        "quota_plan": quota_plan,
        "capacity_scan_contract": capacity_scan_contract,
        "decision": {
            "posterior_smoke_now": "blocked",
            "reason": "v14 target is positive-sparse and shortcut-entangled; v15 must repair candidate matching and label surface first",
            "if_capacity_scan_passes": "produce v15 label-ready sheet",
            "if_capacity_scan_fails": "freeze as diagnostic or move to attachment witness schema probe",
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"selected_route={summary['selected_route']}")
    print(f"next_todo={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"output_dir={summary['output_dir']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
