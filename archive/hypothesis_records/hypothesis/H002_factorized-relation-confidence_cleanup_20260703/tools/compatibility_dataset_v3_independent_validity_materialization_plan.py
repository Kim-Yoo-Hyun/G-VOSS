#!/usr/bin/env python3
"""Write the materialization plan for GT-anchored independent validity rows."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INVENTORY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_source_inventory"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_materialization_plan"

EXPECTED_INVENTORY_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_source_inventory_ready_for_materialization_plan"
)
EXPECTED_INVENTORY_NEXT = "compatibility_dataset_v3_independent_validity_materialization_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_materialization_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_independent_validity_materialization_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_independent_validity_materialization_plan_input_errors"
SELECTED_PATH = "materialize_balanced_gt_anchored_independent_validity_candidates"
NEXT_TODO = "compatibility_dataset_v3_independent_validity_candidate_materialization"

PRIMARY_QUOTA_PER_CLASS = 800
ABSTAIN_NO_GT_SATISFIED_QUOTA = 200
ABSTAIN_GEOMETRY_UNCERTAIN_QUOTA = 200
AUDIT_GT_CONFLICT_CAP = 50


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", type=Path, default=DEFAULT_INVENTORY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def validate_inventory(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if inventory.get("status") != EXPECTED_INVENTORY_STATUS:
        errors.append({"error_type": "unexpected_inventory_status", "actual": inventory.get("status")})
    if inventory.get("next_todo") != EXPECTED_INVENTORY_NEXT:
        errors.append({"error_type": "unexpected_inventory_next", "actual": inventory.get("next_todo")})
    if inventory.get("validation_errors") != 0:
        errors.append({"error_type": "inventory_validation_errors", "actual": inventory.get("validation_errors")})
    boundary = inventory.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "inventory_boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("materializes_rows") is not False:
        errors.append({"error_type": "inventory_materialized_rows", "actual": boundary.get("materializes_rows")})
    ready = set(inventory.get("families_ready_for_materialization_plan", []))
    for family in ["relative_vertical", "support_contact_pose_conditioned"]:
        if family not in ready:
            errors.append({"error_type": "family_not_ready", "family": family})
    for row in inventory.get("capacity_decision_table", []):
        if row.get("materialization_feasible") is not True:
            errors.append({"error_type": "family_materialization_not_feasible", "family": row.get("family")})
    return errors


def inventory_by_family(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(row["family"]): row for row in inventory.get("family_inventory_table", [])}


def quota_rows(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    by_family = inventory_by_family(inventory)
    rows: list[dict[str, Any]] = []
    for family in ["relative_vertical", "support_contact_pose_conditioned"]:
        info = by_family[family]
        positive_available = int(info.get("positive_exact_gt_satisfied", 0))
        negative_available = int(info.get("strong_negative_gt_pair_other_predicate_unsatisfied", 0))
        no_gt_satisfied_available = int(info.get("abstain_no_gt_geometry_satisfied", 0))
        uncertain_available = int(info.get("abstain_geometry_uncertain", 0))
        gt_conflict_available = int(info.get("gt_conflict_exact_unsatisfied", 0))
        positive_quota = min(PRIMARY_QUOTA_PER_CLASS, positive_available)
        negative_quota = min(PRIMARY_QUOTA_PER_CLASS, negative_available)
        no_gt_quota = min(ABSTAIN_NO_GT_SATISFIED_QUOTA, no_gt_satisfied_available)
        uncertain_quota = min(ABSTAIN_GEOMETRY_UNCERTAIN_QUOTA, uncertain_available)
        audit_quota = min(AUDIT_GT_CONFLICT_CAP, gt_conflict_available)
        rows.extend(
            [
                {
                    "family": family,
                    "pool": "positive_exact_gt_satisfied",
                    "target_role": "positive",
                    "available": positive_available,
                    "quota": positive_quota,
                    "label_C_e_validity": 1,
                    "label_p_rel": "accept",
                    "label_p_obs": "observable",
                    "materialize_for_primary_binary": True,
                },
                {
                    "family": family,
                    "pool": "strong_negative_gt_pair_other_predicate_unsatisfied",
                    "target_role": "negative",
                    "available": negative_available,
                    "quota": negative_quota,
                    "label_C_e_validity": 0,
                    "label_p_rel": "reject",
                    "label_p_obs": "observable",
                    "materialize_for_primary_binary": True,
                },
                {
                    "family": family,
                    "pool": "abstain_no_gt_geometry_satisfied",
                    "target_role": "abstain_or_audit",
                    "available": no_gt_satisfied_available,
                    "quota": no_gt_quota,
                    "label_C_e_validity": "abstain",
                    "label_p_rel": "abstain",
                    "label_p_obs": "observable",
                    "materialize_for_primary_binary": False,
                },
                {
                    "family": family,
                    "pool": "abstain_geometry_uncertain",
                    "target_role": "abstain",
                    "available": uncertain_available,
                    "quota": uncertain_quota,
                    "label_C_e_validity": "abstain",
                    "label_p_rel": "abstain",
                    "label_p_obs": "abstain_or_unobservable",
                    "materialize_for_primary_binary": False,
                },
                {
                    "family": family,
                    "pool": "gt_conflict_exact_unsatisfied",
                    "target_role": "audit_required",
                    "available": gt_conflict_available,
                    "quota": audit_quota,
                    "label_C_e_validity": "audit_required",
                    "label_p_rel": "audit_required",
                    "label_p_obs": "observable",
                    "materialize_for_primary_binary": False,
                },
            ]
        )
    return rows


def validate_quota_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row in rows:
        if int(row["quota"]) > int(row["available"]):
            errors.append(
                {
                    "error_type": "quota_exceeds_available",
                    "family": row["family"],
                    "pool": row["pool"],
                    "quota": row["quota"],
                    "available": row["available"],
                }
            )
    for family in ["relative_vertical", "support_contact_pose_conditioned"]:
        pos = [row for row in rows if row["family"] == family and row["pool"] == "positive_exact_gt_satisfied"][0]
        neg = [
            row
            for row in rows
            if row["family"] == family and row["pool"] == "strong_negative_gt_pair_other_predicate_unsatisfied"
        ][0]
        if int(pos["quota"]) < PRIMARY_QUOTA_PER_CLASS:
            errors.append({"error_type": "positive_quota_below_primary", "family": family, "quota": pos["quota"]})
        if int(neg["quota"]) < PRIMARY_QUOTA_PER_CLASS:
            errors.append({"error_type": "negative_quota_below_primary", "family": family, "quota": neg["quota"]})
        if int(pos["quota"]) != int(neg["quota"]):
            errors.append({"error_type": "primary_binary_unbalanced", "family": family, "pos": pos["quota"], "neg": neg["quota"]})
    return errors


def planned_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(int(row["quota"]) for row in rows)
    primary = sum(int(row["quota"]) for row in rows if row["materialize_for_primary_binary"] is True)
    by_family: dict[str, int] = {}
    by_role: dict[str, int] = {}
    for row in rows:
        by_family[row["family"]] = by_family.get(row["family"], 0) + int(row["quota"])
        by_role[row["target_role"]] = by_role.get(row["target_role"], 0) + int(row["quota"])
    return {
        "planned_total_rows": total,
        "planned_primary_binary_rows": primary,
        "planned_nonbinary_audit_or_abstain_rows": total - primary,
        "by_family": by_family,
        "by_role": by_role,
    }


def row_schema_contract() -> dict[str, Any]:
    return {
        "schema_name": "h002_independent_validity_candidate_row_v1",
        "required_top_level_fields": [
            "row_id",
            "cv_group_id",
            "split",
            "family",
            "target_role",
            "feature_blocks",
            "labels",
            "provenance_safe",
            "controls_hidden",
        ],
        "feature_blocks": {
            "T_e": [
                "predicate_label",
                "predicate_text",
                "relation_family",
                "subject_class_label",
                "object_class_label",
            ],
            "Z_e_safe": [
                "semantic_score_raw",
                "semantic_score_norm",
                "semantic_rank",
                "rank_band",
            ],
            "G_e": [
                "geometry_status",
                "p_geom_valid",
                "consistency_score",
                "geometry_residual_proxy",
                "raw_geometry_feature_vector",
            ],
            "Q_e_safe": [
                "geometry_available",
                "geometry_checkable",
                "coverage_state",
                "reason_code_count",
                "has_uncertain_geometry",
            ],
        },
        "labels": {
            "C_e_validity": "1 / 0 / abstain / audit_required",
            "p_obs": "observable / abstain_or_unobservable",
            "p_rel": "accept / reject / abstain / audit_required",
        },
        "primary_binary_filter": {
            "include_roles": ["positive", "negative"],
            "exclude_labels": ["abstain", "audit_required"],
        },
        "cv_group_id": "scan_id + directed_pair_id",
        "grouped_split_required": True,
    }


def blocked_field_rows() -> list[dict[str, Any]]:
    blocked = [
        ("identity.prediction_id", "row identity and source metadata"),
        ("identity.row_key", "row identity and source metadata"),
        ("identity.scan_id", "split/group leakage"),
        ("identity.subgraph_id", "split/group leakage"),
        ("identity.directed_pair_id", "object-pair identity leakage"),
        ("label.label_match_status", "target construction label"),
        ("label.label_match", "target construction label"),
        ("label.family_match", "target construction label"),
        ("label.matched_gt_ids", "target construction label"),
        ("label.matched_predicates", "target construction label"),
        ("target_role", "target construction label"),
        ("labels.C_e_validity", "target label"),
        ("labels.p_obs", "target label"),
        ("labels.p_rel", "target label"),
        ("controls_hidden.*", "audit-only controls"),
        ("provenance.*", "artifact provenance"),
    ]
    return [{"field": field, "reason": reason, "model_input_allowed": False} for field, reason in blocked]


def matching_policy() -> dict[str, Any]:
    return {
        "positive_pool": {
            "source": "exact_match + geometry_status=satisfied",
            "role": "accept",
            "quota_per_family": PRIMARY_QUOTA_PER_CLASS,
        },
        "negative_pool": {
            "source": "family_match or pair_has_other_predicate + geometry_status=unsatisfied",
            "role": "reject",
            "quota_per_family": PRIMARY_QUOTA_PER_CLASS,
            "hard_negative_priority": [
                "same predicate family when available",
                "same rank band",
                "same object-class pair if possible",
                "same scan cap",
            ],
        },
        "abstain_pools": {
            "no_gt_geometry_satisfied": {
                "quota_per_family": ABSTAIN_NO_GT_SATISFIED_QUOTA,
                "role": "abstain_or_audit",
                "negative_allowed": False,
            },
            "geometry_uncertain": {
                "quota_per_family": ABSTAIN_GEOMETRY_UNCERTAIN_QUOTA,
                "role": "abstain",
                "negative_allowed": False,
            },
            "gt_conflict_exact_unsatisfied": {
                "quota_cap_per_family": AUDIT_GT_CONFLICT_CAP,
                "role": "audit_required",
                "negative_allowed": False,
            },
        },
        "caps": {
            "max_single_scan_share": 0.08,
            "max_single_visible_pair_share": 0.05,
            "group_by": "scan_id + directed_pair_id",
        },
        "forbidden_negative_policy": "no-GT rows are never negative labels",
    }


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Materialize GT-anchored independent validity candidate rows following the frozen quotas and schema.",
        "required_outputs": [
            "candidate_rows.jsonl",
            "smoke_ready_view.jsonl",
            "hidden_manifest.jsonl",
            "materialization_manifest.json",
            "quota_audit.csv",
            "validation_errors.jsonl",
        ],
        "required_gates_after_materialization": [
            "row-count and quota audit",
            "no-GT negative policy audit",
            "blocked-field absence audit",
            "group integrity audit",
            "single-feature shortcut audit",
            "schema/shortcut audit before learned smoke",
        ],
        "do_not_do_next": [
            "do not run learned smoke in the materializer",
            "do not use validation/test rows",
            "do not modify H001 artifacts",
            "do not include hidden GT labels in model input",
            "do not treat no-GT as negative",
        ],
    }


def build_decision(inventory: dict[str, Any], quota_errors: list[dict[str, Any]], input_errors: list[dict[str, Any]]) -> dict[str, Any]:
    quotas = quota_rows(inventory) if not input_errors else []
    counts = planned_counts(quotas) if quotas else {}
    errors = input_errors + quota_errors
    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_independent_validity_materialization_plan_inputs"
    selected_path = SELECTED_PATH if not errors else "fix_inputs_before_materialization_plan"
    return {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "split": "train_only_materialization_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "blocked_field_table": blocked_field_rows(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_inventory_status": inventory.get("status"),
        "matching_policy": matching_policy(),
        "next_plan_contract": next_plan_contract(),
        "next_todo": next_todo,
        "planned_counts": counts,
        "quota_table": quotas,
        "row_schema_contract": row_schema_contract(),
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(errors),
    }


def build_report(decision: dict[str, Any]) -> str:
    lines = [
        "# H002 Independent Validity Materialization Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {decision['status']}",
        f"selected_path = {decision['selected_path']}",
        f"validation_errors = {decision['validation_errors']}",
        f"next_todo = {decision['next_todo']}",
        "```",
        "",
        "## Planned Counts",
        "",
        "```text",
        f"planned_total_rows = {decision.get('planned_counts', {}).get('planned_total_rows')}",
        f"planned_primary_binary_rows = {decision.get('planned_counts', {}).get('planned_primary_binary_rows')}",
        f"planned_nonbinary_audit_or_abstain_rows = {decision.get('planned_counts', {}).get('planned_nonbinary_audit_or_abstain_rows')}",
        "```",
        "",
        "## Quota Table",
        "",
        "| Family | Pool | Role | Available | Quota | C_e | p_rel | p_obs |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in decision["quota_table"]:
        lines.append(
            f"| `{row['family']}` | `{row['pool']}` | `{row['target_role']}` | `{row['available']}` | "
            f"`{row['quota']}` | `{row['label_C_e_validity']}` | `{row['label_p_rel']}` | `{row['label_p_obs']}` |"
        )
    lines.extend(
        [
            "",
            "## Materialization Policy",
            "",
            "- Positives are exact GT matches with satisfied geometry.",
            "- Negatives are GT-pair other-predicate or same-family mismatches with unsatisfied geometry.",
            "- No-GT rows are abstain/audit only, never negative.",
            "- Geometry-uncertain rows are abstain and should primarily test `p_obs`.",
            "- GT exact match plus unsatisfied geometry is audit-required, not a negative.",
            "",
            "## Schema Boundary",
            "",
            "Model-safe blocks are `T_e`, `Z_e_safe`, `G_e`, and `Q_e_safe`. Hidden GT join labels,",
            "matched predicates, scan ids, directed-pair ids, target labels, and provenance fields are",
            "not model inputs.",
            "",
            "## Next Gates",
            "",
        ]
    )
    for gate in decision["next_plan_contract"]["required_gates_after_materialization"]:
        lines.append(f"- {gate}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only materialization plan.",
            "- No validation/test usage.",
            "- No row materialization in this stage.",
            "- No learned model trained.",
            "- No H001 artifact modification.",
            "- No paper-level evidence promotion.",
            "",
            "## Next",
            "",
            "```text",
            decision["next_todo"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    inventory = read_json(args.inventory_dir / "summary.json")
    input_errors = validate_inventory(inventory)
    quotas = quota_rows(inventory) if not input_errors else []
    quota_errors = validate_quota_rows(quotas) if quotas else []
    decision = build_decision(inventory, quota_errors, input_errors)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", decision)
    write_json(output_dir / "row_schema_contract.json", decision["row_schema_contract"])
    write_json(output_dir / "matching_policy.json", decision["matching_policy"])
    write_json(output_dir / "next_plan_contract.json", decision["next_plan_contract"])
    write_csv(output_dir / "quota_table.csv", decision["quota_table"])
    write_csv(output_dir / "blocked_field_table.csv", decision["blocked_field_table"])
    write_jsonl(output_dir / "validation_errors.jsonl", input_errors + quota_errors)
    (output_dir / "report.md").write_text(build_report(decision), encoding="utf-8")
    return 1 if input_errors or quota_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
