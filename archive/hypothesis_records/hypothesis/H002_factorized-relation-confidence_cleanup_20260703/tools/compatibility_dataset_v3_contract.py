#!/usr/bin/env python3
"""Write the H002 v3 predicate-conditioned compatibility dataset contract."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_target_redesign_plan"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_contract"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v2_target_redesign_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_contract"
EXPECTED_PLAN_DATASET = "h002_compatibility_dataset_v3_predicate_conditioned"
EXPECTED_PLAN_ROUTE = "same_geometry_multi_predicate"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_contract_v1"
STATUS_READY = "h002_compatibility_dataset_v3_contract_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_contract_input_errors"
NEXT_TODO = "compatibility_dataset_v3_capacity_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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
    if not fields:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(plan_summary: dict[str, Any], target_plan: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan_summary.get("validation_errors")})
    if target_plan.get("dataset_name") != EXPECTED_PLAN_DATASET:
        errors.append({"error_type": "unexpected_dataset_name", "actual": target_plan.get("dataset_name")})
    if target_plan.get("selected_route") != EXPECTED_PLAN_ROUTE:
        errors.append({"error_type": "unexpected_selected_route", "actual": target_plan.get("selected_route")})
    if "relative_vertical" != plan_summary.get("primary_v3_family"):
        errors.append({"error_type": "unexpected_primary_v3_family", "actual": plan_summary.get("primary_v3_family")})
    return errors


def dataset_contract() -> dict[str, Any]:
    return {
        "dataset_name": "h002_compatibility_dataset_v3_predicate_conditioned",
        "contract_role": "train-only hypothesis dataset contract",
        "primary_task": "Task A: predicate-geometry compatibility C_e",
        "not_a_target_for": [
            "p_rel final human reliability",
            "validation/test evaluation",
            "paper-level result promotion",
        ],
        "core_principle": (
            "For primary rows, the same directed object-pair geometry G_e is paired with multiple "
            "predicate semantics T_e. Exactly one predicate should be compatible under a predeclared "
            "rule, so G_e alone cannot solve the label."
        ),
        "factor_boundary": {
            "T_e": "predicate text/label, relation family, subject/object class labels, and text-only semantic content",
            "Z_e": "source id, source score, rank, and rank band; allowed only for source baselines or full reliability models, not for C_e",
            "G_e": "predicate-independent numeric/object-pair geometry evidence shared inside a primary geometry group",
            "C_e": "compatibility(T_e, G_e), computed without Z_e",
            "Q_e": "evidence availability and observability quality; not a direct truth label",
        },
        "primary_family": {
            "family": "relative_vertical",
            "predicates": ["higher than", "lower than"],
            "row_group": "same directed subject/object pair and same numeric G_e",
            "rows_per_geometry_group": 2,
            "positive_rule": "predicate agrees with signed vertical ordering when vertical margin is clear",
            "negative_rule": "opposite predicate on the same directed-pair geometry",
            "ambiguous_rule": "exclude from primary if absolute vertical margin is below the frozen threshold",
            "initial_margin_contract": {
                "absolute_center_delta_z_m_min": 0.10,
                "normalized_center_delta_z_min": 0.20,
                "margin_tuning_policy": (
                    "Capacity scan may report sensitivity over a small predeclared grid, but the "
                    "materialization threshold must be frozen before learned smoke."
                ),
            },
            "allowed_primary_negative": "predicate-negative same-G row",
            "blocked_primary_negatives": [
                "wrong_pair_geometry",
                "shuffled_geometry",
                "generic_geometry_perturbation",
                "subject_object_swap unless declared as a separate control",
            ],
        },
        "secondary_family": {
            "family": "support_contact",
            "status": "secondary_until_evidence_probe_passes",
            "predicates": ["standing on", "lying on", "supported by"],
            "required_before_primary": [
                "object role evidence",
                "pose/orientation evidence",
                "contact direction or support normal evidence",
                "mesh or multi-view evidence availability",
            ],
            "reason": (
                "Current support/contact v2 rows are dominated by distance and overlap shifts; using "
                "them as first primary v3 rows would likely repeat geometry-only dominance."
            ),
        },
        "deferred_families": [
            {
                "family": "proximity",
                "predicates": ["close by"],
                "reason": "single-predicate distance compatibility is likely geometry-only and not a clean C_e identifiability target",
            },
            {
                "family": "attachment_like",
                "predicates": ["attached to", "hanging on", "connected to"],
                "reason": "requires stronger visual/mesh or role evidence before primary C_e use",
            },
        ],
        "split_policy": {
            "hypothesis_stage": "train_only",
            "grouping_for_smoke": "grouped by geometry_group_id",
            "validation_usage": False,
            "test_usage": False,
        },
    }


def row_schema() -> dict[str, Any]:
    return {
        "required_top_level_fields": [
            "row_id",
            "geometry_group_id",
            "split",
            "source_dataset",
            "scan_id",
            "subject_instance_id",
            "object_instance_id",
            "directed_pair_id",
            "T_e",
            "Z_e_safe",
            "G_e_numeric",
            "Q_e_safe",
            "labels",
            "controls_hidden",
        ],
        "T_e": [
            "predicate_label",
            "predicate_text",
            "relation_family",
            "subject_class_label",
            "object_class_label",
            "subject_object_text",
        ],
        "Z_e_safe": [
            "source_id",
            "source_score_available",
            "source_score_raw",
            "source_score_normalized",
            "source_rank",
            "source_rank_band",
        ],
        "G_e_numeric": [
            "center_delta_z_m",
            "abs_center_delta_z_m",
            "normalized_center_delta_z",
            "subject_center_z",
            "object_center_z",
            "subject_top_z",
            "subject_bottom_z",
            "object_top_z",
            "object_bottom_z",
            "distance_xy_m",
            "bbox_iou_xy",
            "projected_overlap_max",
            "vertical_gap_subject_on_object",
            "geometry_feature_hash",
        ],
        "Q_e_safe": [
            "geometry_available",
            "obb_available",
            "mesh_available",
            "view_packet_available",
            "evidence_availability_count",
            "missing_evidence_types",
        ],
        "labels": [
            "compatibility_label",
            "compatibility_label_name",
            "label_rule_id",
            "label_margin_id",
            "is_primary_same_geometry_predicate_contrast",
        ],
        "controls_hidden": [
            "raw_source_predicate",
            "construction_route",
            "counterfactual_type",
            "anchor_row_id",
            "materialization_policy_id",
            "audit_only_geometry_status",
        ],
        "primary_group_integrity": [
            "same geometry_group_id",
            "same directed_pair_id",
            "same geometry_feature_hash",
            "different predicate_label",
            "one compatibility_label = 1",
            "one compatibility_label = 0",
        ],
    }


def family_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "family": "relative_vertical",
            "role": "primary_v3_identifiability_target",
            "predicates": "higher than; lower than",
            "minimum_reportable_groups": 100,
            "requested_groups": 200,
            "requested_rows": 400,
            "positive_negative_policy": "one positive and one opposite-predicate negative per same-G geometry group",
            "required_evidence": "signed vertical order with frozen margin",
            "promotion_condition": "geometry-only near chance and T_e+G_e beats T_e-only/G_e-only/source-only",
            "status": "selected_for_capacity_scan",
        },
        {
            "family": "support_contact",
            "role": "secondary_evidence_probe",
            "predicates": "standing on; lying on; supported by",
            "minimum_reportable_groups": 0,
            "requested_groups": 0,
            "requested_rows": 0,
            "positive_negative_policy": "not primary until role/orientation or visual/mesh evidence exists",
            "required_evidence": "pose/orientation, contact direction, surface normal, or visual/mesh evidence",
            "promotion_condition": "evidence probe shows same/near-G support rows can be predicate-distinguished",
            "status": "diagnostic_only_for_now",
        },
        {
            "family": "proximity",
            "role": "future_generality",
            "predicates": "close by",
            "minimum_reportable_groups": 0,
            "requested_groups": 0,
            "requested_rows": 0,
            "positive_negative_policy": "deferred",
            "required_evidence": "future multi-predicate or cross-family contrast",
            "promotion_condition": "must avoid collapse into distance-only verifier",
            "status": "deferred",
        },
        {
            "family": "attachment_like",
            "role": "future_hard_family",
            "predicates": "attached to; hanging on; connected to",
            "minimum_reportable_groups": 0,
            "requested_groups": 0,
            "requested_rows": 0,
            "positive_negative_policy": "deferred after visual/mesh evidence",
            "required_evidence": "visual/mesh contact or attachment cue",
            "promotion_condition": "independent target slices clear shortcut audit",
            "status": "deferred",
        },
    ]


def gate_contract_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "input_plan_validation",
            "stage": "contract",
            "criterion": "v2 target-redesign plan status ready and validation_errors == 0",
            "blocks_if_fail": True,
        },
        {
            "gate": "same_geometry_group_integrity",
            "stage": "materialization",
            "criterion": "each primary geometry group has identical geometry_feature_hash across predicate alternatives",
            "blocks_if_fail": True,
        },
        {
            "gate": "balanced_same_group_labels",
            "stage": "materialization",
            "criterion": "each primary group has exactly one accept-compatible and one reject-compatible predicate row",
            "blocks_if_fail": True,
        },
        {
            "gate": "blocked_field_absence",
            "stage": "model_view",
            "criterion": "model views exclude construction, label-rule, row-role, raw-source, and hidden audit fields",
            "blocks_if_fail": True,
        },
        {
            "gate": "geometry_only_near_chance",
            "stage": "learned_smoke",
            "criterion": "G_e-only AUROC should be near 0.50 on same-G primary rows",
            "blocks_if_fail": True,
        },
        {
            "gate": "predicate_conditioning_gain",
            "stage": "learned_smoke",
            "criterion": "T_e + G_e beats G_e-only, T_e-only, and Z_e-only by a frozen margin",
            "blocks_if_fail": True,
        },
        {
            "gate": "wrong_predicate_degradation",
            "stage": "learned_smoke",
            "criterion": "wrong-T same-G control degrades relative to correct T_e + G_e",
            "blocks_if_fail": True,
        },
        {
            "gate": "shuffled_geometry_degradation",
            "stage": "learned_smoke",
            "criterion": "shuffled-G control degrades relative to correct T_e + G_e",
            "blocks_if_fail": True,
        },
        {
            "gate": "source_shortcut_control",
            "stage": "learned_smoke",
            "criterion": "source-only, rank-only, predicate-only, and object-pair probes remain near chance",
            "blocks_if_fail": True,
        },
        {
            "gate": "support_contact_evidence_probe",
            "stage": "capacity_scan",
            "criterion": "support/contact rows are primary only if extra role/orientation/visual/mesh evidence exists",
            "blocks_if_fail": False,
        },
    ]


def blocked_field_rows() -> list[dict[str, Any]]:
    blocked = [
        ("compatibility_label", "label", "target leakage"),
        ("compatibility_label_name", "label", "target leakage"),
        ("label_rule_id", "label", "rule shortcut"),
        ("label_margin_id", "label", "rule shortcut"),
        ("is_primary_same_geometry_predicate_contrast", "label", "construction shortcut"),
        ("row_role", "construction", "positive/negative construction shortcut"),
        ("counterfactual_type", "construction", "v2 failure shortcut"),
        ("construction_route", "construction", "materialization shortcut"),
        ("materialization_policy_id", "construction", "materialization shortcut"),
        ("anchor_row_id", "construction", "paired-row shortcut"),
        ("geometry_group_id", "identifier", "allowed only for grouping, never as model feature"),
        ("row_id", "identifier", "identifier shortcut"),
        ("raw_source_predicate", "source", "source/label provenance shortcut"),
        ("source_score_inherited_for_counterfactual", "source", "v2 inherited-score shortcut"),
        ("geometry_source", "construction", "raw geometry provenance shortcut"),
        ("geometry_status_baseline", "audit", "audit-only status leakage"),
        ("audit_only_geometry_status", "audit", "audit-only status leakage"),
        ("p_geom_valid", "baseline", "allowed only as named baseline/teacher, not inside G_e primary view unless declared"),
    ]
    return [{"field": name, "category": category, "reason": reason} for name, category, reason in blocked]


def model_view_rows() -> list[dict[str, Any]]:
    return [
        {
            "view": "semantic_only_T",
            "allowed_factors": "T_e",
            "purpose": "semantic shortcut baseline",
            "expected_gate": "near chance on same-G vertical groups",
        },
        {
            "view": "source_only_Z_safe",
            "allowed_factors": "Z_e_safe",
            "purpose": "source confidence shortcut baseline",
            "expected_gate": "near chance on same-G vertical groups",
        },
        {
            "view": "geometry_only_G",
            "allowed_factors": "G_e_numeric",
            "purpose": "main geometry-only baseline",
            "expected_gate": "near chance because positive/negative rows share G_e",
        },
        {
            "view": "compatibility_TG",
            "allowed_factors": "T_e + G_e_numeric",
            "purpose": "primary C_e compatibility view",
            "expected_gate": "beats T-only/G-only/Z-only and degrades under wrong-T or shuffled-G",
        },
        {
            "view": "factorized_sanitized_TZGQ",
            "allowed_factors": "T_e + Z_e_safe + G_e_numeric + Q_e_safe",
            "purpose": "later full factorized reliability model view",
            "expected_gate": "not primary until C_e view passes",
        },
    ]


def smoke_protocol() -> dict[str, Any]:
    return {
        "stage": "future_after_capacity_scan_and_materialization",
        "task": "Task A predicate-geometry compatibility C_e",
        "split": "train-only grouped cross validation",
        "group_key": "geometry_group_id",
        "primary_metric": "AUROC",
        "secondary_metrics": ["AUPRC", "balanced_accuracy", "Brier", "ECE"],
        "minimum_smoke_conditions": {
            "geometry_only_near_chance": True,
            "compatibility_beats_geometry_only": True,
            "compatibility_beats_semantic_only": True,
            "wrong_T_same_G_degrades": True,
            "shuffled_G_degrades": True,
            "source_shortcuts_near_chance": True,
        },
        "diagnostic_if_fail": [
            "If G_e-only wins, v3 still contains geometry distribution leakage.",
            "If T_e-only wins, the target is predicate-label shortcuted.",
            "If wrong-T same-G does not degrade, the model is not using predicate-conditioned geometry.",
            "If shuffled-G does not degrade, the model is not using the paired geometry evidence.",
        ],
        "paper_boundary": "hypothesis-stage only until Docker reproduction and independent evaluation are added",
    }


def write_report(path: Path, summary: dict[str, Any], contract: dict[str, Any]) -> None:
    lines = [
        "# Compatibility Dataset V3 Contract",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v3_contract/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Purpose",
        "",
        "This contract fixes the next H002 target as predicate-conditioned compatibility rather than",
        "generic geometry perturbation detection. The primary row design is:",
        "",
        "```text",
        "same G_e + higher than = one label",
        "same G_e + lower than = opposite label",
        "```",
        "",
        "Therefore `G_e` alone should be insufficient, and the smoke must test whether `T_e` changes",
        "how the model interprets the same geometry evidence.",
        "",
        "## Primary Family",
        "",
        f"- family: `{contract['primary_family']['family']}`",
        f"- predicates: `{'; '.join(contract['primary_family']['predicates'])}`",
        "- group: same directed pair, same numeric `G_e`, different predicate text",
        "- label: signed vertical order under a frozen margin",
        "",
        "## Secondary / Deferred",
        "",
        "Support/contact remains secondary because the previous v2 target was dominated by",
        "distance/overlap shifts. It can be promoted only after role/orientation or visual/mesh",
        "evidence exists. Proximity and attachment-like relations remain future/deferred routes.",
        "",
        "## Required Gates",
        "",
    ]
    for row in gate_contract_rows():
        lines.append(f"- `{row['gate']}`: {row['criterion']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- train-only hypothesis-stage contract",
            "- no validation/test usage",
            "- no dataset materialization in this step",
            "- no learned smoke in this step",
            "- no paper evidence promotion",
            "- no H001 artifact modification",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    target_plan = read_json(args.plan_dir / "target_redesign_plan.json")
    errors = validate_inputs(plan_summary, target_plan)
    status = STATUS_READY if not errors else STATUS_ERRORS

    contract = dataset_contract()
    schema = row_schema()
    protocol = smoke_protocol()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO,
        "input_plan_root": rel_path(args.plan_dir),
        "output_root": rel_path(args.output_dir),
        "dataset_name": contract["dataset_name"],
        "selected_route": "same_geometry_multi_predicate",
        "primary_family": "relative_vertical",
        "secondary_family": "support_contact",
        "requested_primary_geometry_groups": 200,
        "minimum_reportable_primary_geometry_groups": 100,
        "requested_primary_rows": 400,
        "materializes_dataset": False,
        "runs_learned_smoke": False,
        "paper_evidence_allowed": False,
        "validation_errors": len(errors),
        "boundary": {
            "contract_only": True,
            "train_only": True,
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
        },
        "key_decisions": {
            "v2_remains_diagnostic_only": True,
            "primary_v3_requires_same_geometry_multi_predicate_groups": True,
            "C_e_excludes_Z_e": True,
            "geometry_only_is_main_baseline": True,
            "support_contact_not_primary_until_evidence_probe": True,
            "capacity_scan_before_materialization": True,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "dataset_contract": rel_path(args.output_dir / "dataset_contract.json"),
            "row_schema": rel_path(args.output_dir / "row_schema.json"),
            "family_contract": rel_path(args.output_dir / "family_contract.csv"),
            "gate_contract": rel_path(args.output_dir / "gate_contract.csv"),
            "blocked_fields": rel_path(args.output_dir / "blocked_fields.csv"),
            "model_views": rel_path(args.output_dir / "model_views.csv"),
            "smoke_protocol": rel_path(args.output_dir / "smoke_protocol.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "dataset_contract.json", contract)
    write_json(args.output_dir / "row_schema.json", schema)
    write_csv(args.output_dir / "family_contract.csv", family_contract_rows())
    write_csv(args.output_dir / "gate_contract.csv", gate_contract_rows())
    write_csv(args.output_dir / "blocked_fields.csv", blocked_field_rows())
    write_csv(args.output_dir / "model_views.csv", model_view_rows())
    write_json(args.output_dir / "smoke_protocol.json", protocol)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, contract)


if __name__ == "__main__":
    main()
