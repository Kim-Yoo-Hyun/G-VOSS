#!/usr/bin/env python3
"""Plan the H002 v16 controlled cross-stratum support/contact contrast route."""

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

DEFAULT_DECISION_DIR = RGA_ROOT / "reliability_target_v15_physical_relation_family_path_decision_after_capacity_scan"
DEFAULT_CAPACITY_DIR = RGA_ROOT / "reliability_target_v15_physical_relation_family_capacity_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v16_cross_stratum_support_contact_contrast_plan"

EXPECTED_DECISION_STATUS = "h002_reliability_target_v15_physical_relation_family_path_decision_select_cross_stratum_support_contact_contrast"
EXPECTED_DECISION_NEXT = "reliability_target_v16_cross_stratum_support_contact_contrast_plan"
EXPECTED_SELECTED_PATH = "reject_same_witness_select_v16_cross_stratum_support_contact_contrast"
EXPECTED_CAPACITY_STATUS = "h002_reliability_target_v15_physical_relation_family_capacity_scan_blocked_capacity_or_mixed_strata"

STATUS = "h002_reliability_target_v16_cross_stratum_support_contact_contrast_plan_ready_for_capacity_scan"
NEXT_TODO = "reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-dir", type=Path, default=DEFAULT_DECISION_DIR)
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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(decision: dict[str, Any], capacity: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if decision.get("status") != EXPECTED_DECISION_STATUS:
        errors.append({"error_type": "unexpected_decision_status", "expected": EXPECTED_DECISION_STATUS, "actual": decision.get("status")})
    if decision.get("next_todo") != EXPECTED_DECISION_NEXT:
        errors.append({"error_type": "unexpected_decision_next_todo", "expected": EXPECTED_DECISION_NEXT, "actual": decision.get("next_todo")})
    if decision.get("selected_path") != EXPECTED_SELECTED_PATH:
        errors.append({"error_type": "unexpected_selected_path", "expected": EXPECTED_SELECTED_PATH, "actual": decision.get("selected_path")})
    if decision.get("validation_errors") != 0:
        errors.append({"error_type": "decision_validation_errors_present", "actual": decision.get("validation_errors")})
    if capacity.get("status") != EXPECTED_CAPACITY_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "expected": EXPECTED_CAPACITY_STATUS, "actual": capacity.get("status")})
    if capacity.get("validation_errors") != 0:
        errors.append({"error_type": "capacity_validation_errors_present", "actual": capacity.get("validation_errors")})

    for source, payload in [("decision", decision), ("capacity", capacity)]:
        boundary = payload.get("boundary", {})
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
                errors.append({"error_type": "boundary_violation", "source": source, "key": key, "actual": boundary.get(key)})

    cap = capacity.get("capacity_decision", {})
    if cap.get("support_contact_rows_available", 0) < 200:
        errors.append({"error_type": "insufficient_support_contact_rows", "expected_at_least": 200, "actual": cap.get("support_contact_rows_available")})
    if cap.get("support_contact_mixed_witness_strata") != 0:
        errors.append({"error_type": "mixed_witness_expected_zero_from_v32", "expected": 0, "actual": cap.get("support_contact_mixed_witness_strata")})

    by_pred = {row["predicate_key"]: row for row in capacity.get("quota_feasibility", [])}
    lie = by_pred.get("support_contact|lying on", {})
    stand = by_pred.get("support_contact|standing on", {})
    if int(lie.get("eligible_hl", 0)) <= 0 or int(lie.get("eligible_lh", 0)) <= 0:
        errors.append({"error_type": "lying_on_not_bidirectional", "actual": lie})
    if int(stand.get("eligible_hl", 0)) != 0:
        errors.append({"error_type": "standing_on_expected_no_hl_under_current_filter", "actual": stand})
    return errors


def build_contrast_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v16_cross_stratum_contrast_schema_v1",
        "route_name": "controlled_cross_stratum_support_contact_contrast",
        "target_question": "Does factorized evidence explain relation reliability across semantic-geometry disagreement states without collapsing to a single shortcut axis?",
        "primary_family": "support_contact",
        "primary_predicate": "lying on",
        "secondary_predicate_policy": {
            "standing on": "diversity_or_diagnostic_only_until_balanced_hl_capacity_exists",
            "supported by": "excluded_from_current_primary_target",
        },
        "contrast_sides": [
            {
                "side_id": "HL",
                "meaning": "semantic-high geometry-low or geometry-contradicted support/contact candidate",
                "queue_kind": "HL",
                "role": "semantic_overconfidence_side",
                "not_a_label": True,
            },
            {
                "side_id": "LH",
                "meaning": "semantic-low geometry-high or geometry-supported support/contact candidate",
                "queue_kind": "LH",
                "role": "semantic_underconfidence_side",
                "not_a_label": True,
            },
        ],
        "contrast_unit": {
            "type": "paired_or_blocked_cross_stratum_contrast",
            "block_key_match_axes": [
                "predicate_label",
                "endpoint_generic_state",
                "coarse_subject_object_category",
                "coverage_state",
            ],
            "block_distribution_control_axes": [
                "scan_id",
                "subgraph_id",
                "subject_object_label_pair",
                "semantic_rank_band",
                "source_queue_kind",
                "reason_family",
                "p_geom_bin",
                "geometry_status",
            ],
            "explicitly_not_matched_axes": [
                "geometry_status",
                "p_geom_bin",
                "reason_signature",
                "coarse_witness_bin",
            ],
            "reason": "Those axes define the semantic-geometry mismatch itself; forcing equality reproduces the v15 failure.",
        },
        "label_target_policy": {
            "relation_reliability_label": "human_or_proxy_review_after_visible evidence fill; not queue-derived",
            "queue_kind_is_label": False,
            "geometry_status_is_label": False,
            "geometry_support_is_auxiliary_only": True,
            "abstain_allowed": True,
        },
    }


def build_quota_plan() -> list[dict[str, Any]]:
    return [
        {
            "cell_id": "P1_lie_hl_primary_overconfidence",
            "family": "support_contact",
            "predicate_label": "lying on",
            "queue_kind": "HL",
            "role": "primary_cross_stratum_side",
            "target_rows": 100,
            "minimum_rows_after_capacity_scan": 80,
            "binary_target_role": "eligible_after_label_fill_if_not_abstain",
            "notes": "Do not label as reject by construction; label must come from visible evidence review.",
        },
        {
            "cell_id": "P2_lie_lh_primary_underconfidence",
            "family": "support_contact",
            "predicate_label": "lying on",
            "queue_kind": "LH",
            "role": "primary_cross_stratum_side",
            "target_rows": 100,
            "minimum_rows_after_capacity_scan": 80,
            "binary_target_role": "eligible_after_label_fill_if_not_abstain",
            "notes": "Do not label as accept by construction; label must come from visible evidence review.",
        },
        {
            "cell_id": "D1_stand_lh_diversity_diagnostic",
            "family": "support_contact",
            "predicate_label": "standing on",
            "queue_kind": "LH",
            "role": "diversity_diagnostic_not_primary_balance",
            "target_rows": 24,
            "minimum_rows_after_capacity_scan": 0,
            "binary_target_role": "diagnostic_or_auxiliary_only_by_default",
            "notes": "standing-on has no eligible HL after hard filtering; keep out of the primary balanced target unless a later route proves otherwise.",
        },
        {
            "cell_id": "C1_vertical_lower_control",
            "family": "relative_vertical",
            "predicate_label": "lower than",
            "queue_kind": "LH",
            "role": "small_geometry_easy_control",
            "target_rows": 16,
            "minimum_rows_after_capacity_scan": 0,
            "binary_target_role": "control_only",
            "notes": "Do not use vertical rows to satisfy support/contact target mass.",
        },
    ]


def build_sampling_policy() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v16_sampling_policy_v1",
        "candidate_inputs": {
            "hl_queue": rel_path(RGA_ROOT / "train_hl_queue.jsonl"),
            "lh_queue": rel_path(RGA_ROOT / "train_lh_queue.jsonl"),
            "match_rows_required_for_plan": False,
            "raw_feature_join_required_for_candidate_mining": True,
        },
        "hard_filters": [
            "missing_prediction_id",
            "support_contact subject in {floor, wall, ceiling}",
            "support_contact object in {wall, ceiling}",
            "relative_vertical both endpoints in {floor, wall, ceiling}",
        ],
        "primary_balance": {
            "primary_target_rows": 200,
            "primary_queue_balance": {"HL": 100, "LH": 100},
            "primary_predicate": "lying on",
            "standing_on_primary_allowed": False,
            "reason": "standing-on has no eligible HL after hard endpoint filtering in v32.",
        },
        "caps": {
            "max_rows_per_scan": 4,
            "max_rows_per_subgraph": 2,
            "max_rows_per_directed_pair": 1,
            "max_rows_per_visible_pair": 3,
            "max_rows_per_endpoint_generic_state_share": 0.55,
            "max_single_subject_label_share": 0.25,
            "max_single_object_label_share": 0.25,
            "max_single_rank_band_share": 0.45,
            "max_single_reason_family_share_per_side": 0.45,
            "max_single_p_geom_bin_share_per_side": 0.55,
            "max_single_geometry_status_share_per_side": 0.70,
        },
        "block_construction": {
            "minimum_blocks": 40,
            "preferred_rows_per_block": 4,
            "minimum_sides_per_primary_block": 2,
            "block_match_axes": [
                "predicate_label",
                "endpoint_generic_state",
                "coarse_subject_object_category",
                "coverage_state",
            ],
            "block_balance_axes": [
                "queue_kind",
                "semantic_rank_band",
                "scan_id",
                "subject_object_label_pair",
                "reason_family",
                "p_geom_bin",
                "geometry_status",
            ],
        },
        "fallback_order": [
            "relax block-level same endpoint category but keep global endpoint distribution caps",
            "reduce standing-on diagnostic rows before reducing primary lying-on balance",
            "reduce vertical control rows before reducing primary lying-on balance",
            "if primary HL/LH lying-on balance cannot reach 80/80 after caps, stop and run path decision",
        ],
    }


def build_label_surface_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v16_label_surface_contract_v1",
        "visible_fields_allowed": [
            "blind_review_id",
            "candidate_relation",
            "subject_label",
            "predicate_label",
            "object_label",
            "relation_family_visible",
            "non_template_geometry_factor_summary",
            "coverage_note",
            "endpoint_meaning_note",
            "uncertainty_note",
            "review_question",
            "relation_reliability_state",
            "geometry_support_state",
            "relation_usefulness_state",
            "primary_reason",
            "uncertainty_reason",
            "review_notes",
        ],
        "visible_fields_forbidden": [
            "queue_kind",
            "rank_band",
            "semantic_geometry_bucket",
            "geometry_status",
            "p_geom_valid",
            "machine_hint",
            "label_match_status",
            "quota_cell_id",
            "direct_accept_reject_hint",
            "HL",
            "LH",
            "RGA-HL",
            "RGA-LH",
            "phrases that directly say semantic overconfidence, semantic underconfidence, geometry satisfied, or geometry unsatisfied",
        ],
        "hidden_audit_only_fields": [
            "queue_kind_hidden",
            "rank_band_hidden",
            "geometry_status_hidden",
            "p_geom_valid_hidden",
            "reason_family_hidden",
            "reason_codes_hidden",
            "label_match_status_hidden",
            "machine_hint_hidden",
            "block_id_hidden",
            "quota_cell_id_hidden",
        ],
        "review_instruction": "Judge whether the directed relation should be trusted from visible 3D layout evidence, without using source rank, queue bucket, hidden geometry status, or target construction metadata.",
    }


def build_independence_plan() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v16_independence_plan_v1",
        "posterior_smoke_allowed_before_audit": False,
        "minimum_post_label_binary_rows": 120,
        "minimum_post_label_positive_rows": 50,
        "minimum_post_label_negative_rows": 50,
        "strict_slice": {
            "min_rows": 80,
            "min_per_class": 35,
            "must_control": [
                "predicate_label",
                "queue_kind_hidden",
                "rank_band_hidden",
                "endpoint_generic_state_hidden",
                "reason_family_hidden",
            ],
        },
        "diagnostic_slice": {
            "min_rows": 40,
            "min_per_class": 15,
        },
        "shortcut_probes": [
            "queue_kind_only",
            "geometry_status_only",
            "p_geom_bin_only",
            "predicate_label_only",
            "rank_band_only",
            "reason_family_only",
            "scan_id_only",
            "subject_object_label_pair_only",
            "endpoint_generic_state_only",
            "quota_cell_only",
            "block_id_only",
        ],
        "blocked_if": [
            "relation label can be predicted by queue kind alone",
            "relation label can be predicted by geometry status or p_geom bin alone",
            "no strict or diagnostic controlled slice exists",
            "positive or negative label mass is below the minimum gate",
            "visible label surface exposes target construction metadata",
        ],
    }


def write_label_surface_markdown(path: Path, contract: dict[str, Any]) -> None:
    lines = [
        "# V16 Label Surface Contract",
        "",
        "v16은 cross-stratum contrast를 사용하지만, label reviewer에게 queue side나 hidden geometry status를 노출하지 않는다.",
        "",
        "## Allowed Visible Fields",
        "",
    ]
    lines.extend(f"- `{field}`" for field in contract["visible_fields_allowed"])
    lines.extend(["", "## Forbidden Visible Fields", ""])
    lines.extend(f"- `{field}`" for field in contract["visible_fields_forbidden"])
    lines.extend(["", "## Hidden Audit Only Fields", ""])
    lines.extend(f"- `{field}`" for field in contract["hidden_audit_only_fields"])
    lines.extend(["", "## Review Instruction", "", contract["review_instruction"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["contrast_schema"]
    quotas = summary["quota_plan"]
    lines = [
        "# H002 V16 Cross-Stratum Support/Contact Contrast Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Core Decision",
        "",
        f"Route: `{plan['route_name']}`",
        "",
        "v16 keeps `support_contact` but changes the matching unit. HL and LH are no longer forced into the same witness bucket.",
        "They are different semantic-geometry disagreement states and will be compared through controlled cross-stratum blocks.",
        "",
        "## Quota",
        "",
        "| Cell | Predicate | Queue | Role | Rows |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in quotas:
        lines.append(f"| `{row['cell_id']}` | `{row['predicate_label']}` | `{row['queue_kind']}` | `{row['role']}` | `{row['target_rows']}` |")
    lines.extend(
        [
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
            "The next stage must scan whether these cross-stratum block and cap requirements are feasible before any label sheet is generated.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    decision_dir = as_abs(args.decision_dir)
    capacity_dir = as_abs(args.capacity_dir)
    output_dir = as_abs(args.output_dir)

    decision = read_json(decision_dir / "summary.json")
    capacity = read_json(capacity_dir / "summary.json")
    errors = validate_inputs(decision, capacity)

    contrast_schema = build_contrast_schema()
    quota_plan = build_quota_plan()
    sampling_policy = build_sampling_policy()
    label_surface = build_label_surface_contract()
    independence_plan = build_independence_plan()

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "contrast_schema.json", contrast_schema)
    write_json(output_dir / "sampling_policy.json", sampling_policy)
    write_json(output_dir / "label_surface_contract.json", label_surface)
    write_label_surface_markdown(output_dir / "label_surface_contract.md", label_surface)
    write_json(output_dir / "target_independence_plan.json", independence_plan)
    write_csv(
        output_dir / "quota_plan.csv",
        quota_plan,
        [
            "cell_id",
            "family",
            "predicate_label",
            "queue_kind",
            "role",
            "target_rows",
            "minimum_rows_after_capacity_scan",
            "binary_target_role",
            "notes",
        ],
    )
    write_jsonl(output_dir / "validation_errors.jsonl", errors)

    summary = {
        "schema_version": "h002_reliability_target_v16_cross_stratum_support_contact_contrast_plan_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS if not errors else "blocked_validation_errors",
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
            "path_decision_summary": rel_path(decision_dir / "summary.json"),
            "capacity_summary": rel_path(capacity_dir / "summary.json"),
            "quota_feasibility": rel_path(capacity_dir / "quota_feasibility.csv"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "contrast_schema": rel_path(output_dir / "contrast_schema.json"),
            "sampling_policy": rel_path(output_dir / "sampling_policy.json"),
            "quota_plan": rel_path(output_dir / "quota_plan.csv"),
            "label_surface_contract_json": rel_path(output_dir / "label_surface_contract.json"),
            "label_surface_contract_md": rel_path(output_dir / "label_surface_contract.md"),
            "target_independence_plan": rel_path(output_dir / "target_independence_plan.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "capacity_basis": {
            "support_contact_rows_available": capacity["capacity_decision"]["support_contact_rows_available"],
            "support_contact_rows_after_caps": capacity["capacity_decision"]["support_contact_rows_after_caps"],
            "support_contact_mixed_witness_strata": capacity["capacity_decision"]["support_contact_mixed_witness_strata"],
            "lying_on_eligible_hl": next(row["eligible_hl"] for row in capacity["quota_feasibility"] if row["predicate_key"] == "support_contact|lying on"),
            "lying_on_eligible_lh": next(row["eligible_lh"] for row in capacity["quota_feasibility"] if row["predicate_key"] == "support_contact|lying on"),
            "standing_on_eligible_hl": next(row["eligible_hl"] for row in capacity["quota_feasibility"] if row["predicate_key"] == "support_contact|standing on"),
            "standing_on_eligible_lh": next(row["eligible_lh"] for row in capacity["quota_feasibility"] if row["predicate_key"] == "support_contact|standing on"),
        },
        "contrast_schema": contrast_schema,
        "quota_plan_total_rows": sum(row["target_rows"] for row in quota_plan),
        "quota_plan": quota_plan,
        "sampling_policy": sampling_policy,
        "label_surface_contract": label_surface,
        "target_independence_plan": independence_plan,
        "decision": {
            "posterior_smoke_now": "blocked",
            "candidate_mining_now": "blocked_until_capacity_scan",
            "if_capacity_scan_passes": "produce v16 cross-stratum label-ready sheet",
            "if_capacity_scan_fails": "run path decision; likely move to attachment schema probe or revise controls",
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"next_todo={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"quota_plan_total_rows={summary['quota_plan_total_rows']}")
    print(f"output_dir={summary['output_dir']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
