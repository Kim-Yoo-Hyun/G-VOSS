#!/usr/bin/env python3
"""Write the H002 compatibility dataset v2 contract."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SCOPE_DIR = H2_ROOT / "artifacts/compatibility_learning_scope_plan_v1"
DEFAULT_PROTOTYPE_DIR = H2_ROOT / "artifacts/prototype_dataset_v1"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_contract"

EXPECTED_SCOPE_STATUS = "h002_compatibility_learning_scope_plan_ready"
EXPECTED_SCOPE_NEXT = "compatibility_dataset_v2_contract"

SCHEMA_VERSION = "h002_compatibility_dataset_v2_contract"
STATUS_READY = "h002_compatibility_dataset_v2_contract_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v2_contract_input_errors"
NEXT_TODO = "compatibility_dataset_v2_materialization_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-dir", type=Path, default=DEFAULT_SCOPE_DIR)
    parser.add_argument("--prototype-dir", type=Path, default=DEFAULT_PROTOTYPE_DIR)
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
                seen.add(key)
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(scope: dict[str, Any], prototype: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if scope.get("status") != EXPECTED_SCOPE_STATUS:
        errors.append({"error_type": "unexpected_scope_status", "actual": scope.get("status")})
    if scope.get("next_todo") != EXPECTED_SCOPE_NEXT:
        errors.append({"error_type": "unexpected_scope_next", "actual": scope.get("next_todo")})
    if scope.get("validation_errors") != 0:
        errors.append({"error_type": "scope_validation_errors", "actual": scope.get("validation_errors")})
    if scope.get("posterior_smoke_allowed") is not False:
        errors.append({"error_type": "scope_allows_posterior", "actual": scope.get("posterior_smoke_allowed")})
    if prototype.get("status") != "h002_prototype_dataset_v1_ready":
        errors.append({"error_type": "unexpected_prototype_status", "actual": prototype.get("status")})
    if prototype.get("counts", {}).get("validation_errors") != 0:
        errors.append({"error_type": "prototype_validation_errors", "actual": prototype.get("counts", {}).get("validation_errors")})
    required_primary = ["support_contact", "relative_vertical"]
    primary = scope.get("key_decisions", {}).get("primary_families_v1", [])
    if primary != required_primary:
        errors.append({"error_type": "unexpected_primary_families", "expected": required_primary, "actual": primary})
    diagnostic = scope.get("key_decisions", {}).get("diagnostic_hard_families", [])
    if diagnostic != ["attachment_like"]:
        errors.append({"error_type": "unexpected_diagnostic_families", "actual": diagnostic})
    return errors


def row_schema_contract() -> dict[str, Any]:
    return {
        "identity_fields": [
            "row_id",
            "group_id",
            "row_role",
            "split",
            "source_dataset",
            "relation_source",
            "scan_id",
            "scene_id",
            "subject_instance_id",
            "object_instance_id",
            "directed_pair_id",
            "candidate_relation_text",
        ],
        "factor_blocks": {
            "T_e": {
                "required": [
                    "predicate_label",
                    "predicate_text",
                    "relation_family",
                    "subject_label",
                    "object_label",
                    "subject_object_text",
                ],
                "blocked": [
                    "source score",
                    "source rank",
                    "source id",
                    "official GT match",
                    "audit label",
                    "target construction key",
                ],
            },
            "Z_e": {
                "required": [
                    "source_id",
                    "source_score_available",
                    "source_score_raw",
                    "source_score_normalized",
                    "source_rank",
                    "source_rank_band",
                ],
                "blocked_from": ["C_e"],
            },
            "G_e": {
                "required": [
                    "geometry_features",
                    "geometry_feature_mask",
                    "geometry_feature_units",
                    "geometry_normalization",
                    "geometry_source",
                ],
                "blocked": [
                    "predicate label/text",
                    "relation family",
                    "source score/rank/id",
                    "GT/audit label",
                    "counterfactual construction key",
                    "hidden proxy/cell/machine hint",
                ],
            },
            "Q_e": {
                "required": [
                    "asset_tier",
                    "coverage_features",
                    "missing_geometry_flag",
                    "low_coverage_flag",
                    "unsupported_family_flag",
                    "evidence_conflict_flag",
                ],
                "blocked": ["source score/rank as uncertainty proxy", "accept/reject target", "construction key"],
            },
        },
        "label_axes": {
            "compatibility_axis": [
                "compatibility_label",
                "positive_tier",
                "negative_tier",
                "counterfactual_type",
                "anchor_row_id",
                "matching_fields",
            ],
            "observability_axis": ["observability_label", "observability_reason", "p_obs_target_usable"],
            "reliability_eval_axis": ["reliability_label", "binary_usable", "multiclass_usable", "label_source"],
            "official_gt_axis": ["gt_match_status", "gt_predicates_for_pair", "gt_family_for_pair", "gt_used_as_model_input"],
            "audit_axis": ["audit_label", "audit_provenance", "audit_hidden_fields_exposed", "geometry_support_label"],
        },
        "model_views": {
            "source_only": ["Z_e"],
            "semantic_source": ["T_e", "Z_e"],
            "geometry_only": ["G_e"],
            "compatibility_main": ["T_e", "G_e"],
            "obs_head": ["Q_e"],
            "full_factorized": ["T_e", "Z_e", "G_e", "Q_e"],
            "geometry_rule_baseline": ["p_geom_valid_baseline", "geometry_status_baseline"],
        },
    }


def family_contract_rows(scope: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "relation_family": "support_contact",
            "scope": "primary",
            "predicates": "standing on; lying on; supported by",
            "requested_min_positive": 120,
            "requested_min_negative": 120,
            "minimum_reportable_positive": 60,
            "minimum_reportable_negative": 60,
            "positive_tiers": "P1 audit/user-confirmed; P2 high-precision support geometry; optional P0 GT+geometry-usable",
            "negative_tiers": "N1 wrong-pair; N2 shuffled geometry; N5 support/contact perturbation; N6 same-family/rank/coverage",
            "required_counterfactuals": "wrong_pair_geometry; shuffled_geometry; contact_gap_or_overlap_perturbation",
            "required_controls": "predicate/family; source-rank; endpoint-label; hidden construction; scan/instance",
            "g_e_requirements": "support gap; projected XY overlap; contact/support overlap; vertical gap; raw witness v2 numeric geometry",
            "q_e_requirements": "raw witness availability; geometry coverage; missing/artifact flags",
            "materialization_policy": "capacity_scan_then_materialize",
            "paper_status": "hypothesis_only_until_docker_promotion",
        },
        {
            "relation_family": "relative_vertical",
            "scope": "primary_needs_expansion",
            "predicates": "higher than; lower than",
            "requested_min_positive": 80,
            "requested_min_negative": 80,
            "minimum_reportable_positive": 60,
            "minimum_reportable_negative": 60,
            "positive_tiers": "P1 audit/user-confirmed; P2 high-precision vertical-order verified; optional P0 GT+geometry-usable",
            "negative_tiers": "N3 predicate flip; N4 subject/object swap; N1 wrong-pair; N2 shuffled geometry; N6 same-rank/coverage",
            "required_counterfactuals": "higher_lower_flip; subject_object_swap; wrong_pair_geometry; shuffled_geometry",
            "required_controls": "predicate direction; source-rank; endpoint-label; hidden construction; scan/instance",
            "g_e_requirements": "delta_z; top/bottom margin; vertical ordering; XY context; object height normalization",
            "q_e_requirements": "geometry availability; vertical margin confidence; missing geometry",
            "materialization_policy": "capacity_scan_required_before_materialization",
            "paper_status": "hypothesis_only_until_expanded_and_controlled",
        },
        {
            "relation_family": "attachment_like",
            "scope": "diagnostic_only",
            "predicates": "attached to; hanging on; connected to",
            "requested_min_positive": 0,
            "requested_min_negative": 0,
            "minimum_reportable_positive": 0,
            "minimum_reportable_negative": 0,
            "positive_tiers": "P1 only if future independent verification passes",
            "negative_tiers": "diagnostic hard cases only under current contract",
            "required_counterfactuals": "none for current primary C_e target",
            "required_controls": "packet provenance; visible endpoint; rank; hidden construction; observability reason",
            "g_e_requirements": "do not use as v2 primary p_rel/C_e target; numeric G_e only for diagnostic/pretraining if separately named",
            "q_e_requirements": "packet readiness; mesh/contact-sheet availability; subject/object image counts; uncertainty/abstain reason",
            "materialization_policy": "reuse_existing_packets_as_diagnostic_qe_view",
            "paper_status": "diagnostic_only",
        },
        {
            "relation_family": "proximity",
            "scope": "future_generality",
            "predicates": "close by",
            "requested_min_positive": 0,
            "requested_min_negative": 0,
            "minimum_reportable_positive": 0,
            "minimum_reportable_negative": 0,
            "positive_tiers": "future P2 high-precision distance-verified or P1 audit",
            "negative_tiers": "future distance perturbation and wrong-pair geometry",
            "required_counterfactuals": "not in v2 primary",
            "required_controls": "dense relation noise and no-GT incompleteness controls",
            "g_e_requirements": "boundary distance; XY distance; normalized distance; footprint gap",
            "q_e_requirements": "scene scale and coverage quality",
            "materialization_policy": "future_branch_after_primary_scope",
            "paper_status": "future",
        },
    ]


def dataset_contract(scope: dict[str, Any], prototype: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset_name": "h002_compatibility_dataset_v2",
        "purpose": "train-only method dataset for predicate-geometry compatibility learning",
        "selected_scope": scope.get("selected_scope"),
        "source_summary": {
            "prototype_v1_counts": prototype.get("counts", {}),
            "scope_key_decisions": scope.get("key_decisions", {}),
        },
        "output_root": "artifacts/compatibility_dataset_v2/",
        "required_files": {
            "source_candidates.jsonl": "train-side candidates before counterfactual expansion",
            "compatibility_rows.jsonl": "primary C_e rows for support_contact and relative_vertical",
            "diagnostic_rows.jsonl": "attachment_like Q_e/failure-taxonomy rows, not p_rel/C_e target",
            "counterfactual_groups.jsonl": "anchor/counterfactual grouping with matching fields",
            "baseline_view.jsonl": "flattened baseline and shortcut-probe view",
            "audit_view.jsonl": "label/control/provenance-only view",
            "schema.json": "field/blocking contract",
            "split_manifest.json": "train-only provenance",
            "summary.json": "counts/gates",
            "validation_errors.jsonl": "must be empty before smoke",
            "report.md": "human-readable materialization summary",
        },
        "target_policy": {
            "task_a_compatibility": "primary",
            "task_b_observability": "secondary_selective_decision",
            "task_c_reliability": "diagnostic_until_independent_reliability_target_clears",
            "attachment_like": "diagnostic_only",
            "no_gt_policy": "no_gt_is_unknown_not_negative",
            "source_candidate_policy": "source_candidate_is_not_positive_without_tier_evidence",
        },
        "family_contract": family_contract_rows(scope),
        "row_schema": row_schema_contract(),
    }


def control_contract() -> dict[str, Any]:
    return {
        "must_run_before_any_smoke_claim": [
            "schema_leakage_check",
            "train_only_split_check",
            "class_mass_check",
            "family_balance_check",
            "group_integrity_check",
            "source_only_baseline",
            "semantic_source_baseline",
            "geometry_only_baseline",
            "compatibility_main",
            "predicate_family_shortcut",
            "source_rank_shortcut",
            "endpoint_label_pair_shortcut",
            "scan_instance_hidden_probe",
            "hidden_construction_probe",
            "wrong_pair_geometry_control",
            "shuffled_geometry_control",
            "directional_flip_swap_control_for_relative_vertical",
        ],
        "blocking_conditions": [
            "validation_errors_nonzero",
            "any_validation_or_test_usage",
            "G_e_contains_predicate_or_source_fields",
            "C_e_uses_Z_e",
            "hidden_construction_fields_in_model_input",
            "no_gt_used_as_negative",
            "attachment_like_used_as_primary_p_rel_target",
            "relative_vertical_lacks_directional_flip_or_swap_control",
        ],
        "minimum_reportable_class_mass": {
            "overall_primary_task_a": {"positive": 120, "negative": 120},
            "support_contact": {"positive": 60, "negative": 60},
            "relative_vertical": {"positive": 60, "negative": 60},
        },
        "promotion_boundary": {
            "hypothesis_smoke": "allowed after v2 materialization validation passes",
            "paper_experiment": "requires Docker promotion and separate experiment root",
            "posterior_reliability_claim": "blocked until independent p_rel target clears shortcut audit",
        },
    }


def build_report(summary: dict[str, Any], contract: dict[str, Any]) -> str:
    lines = [
        "# H002 Compatibility Dataset V2 Contract",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"dataset_name = {contract['dataset_name']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Scope",
        "",
        "```text",
        "primary = support_contact, relative_vertical",
        "diagnostic = attachment_like",
        "future = proximity",
        "deferred = relative_horizontal, containment",
        "```",
        "",
        "## Family Contract",
        "",
        "| Family | Scope | Requested Min | Required Counterfactuals |",
        "| --- | --- | ---: | --- |",
    ]
    for row in contract["family_contract"]:
        requested = f"{row['requested_min_positive']}/{row['requested_min_negative']}"
        lines.append(
            f"| `{row['relation_family']}` | `{row['scope']}` | `{requested}` | {row['required_counterfactuals']} |"
        )
    lines.extend(
        [
            "",
            "## Critical Rules",
            "",
            "- `C_e` uses `T_e + G_e` only; `Z_e` is forbidden in compatibility input.",
            "- `G_e` cannot contain predicate, source score/rank, GT/audit labels, or construction keys.",
            "- H001 `p_geom_valid` is baseline/teacher/ablation only.",
            "- `no_gt_for_pair` is unknown, not negative.",
            "- `attachment_like` remains diagnostic-only under this contract.",
            "- `relative_vertical` must include predicate flip or subject/object swap controls.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    scope_summary = read_json(args.scope_dir / "summary.json")
    prototype_summary = read_json(args.prototype_dir / "summary.json")
    errors = validate_inputs(scope_summary, prototype_summary)

    contract = dataset_contract(scope_summary, prototype_summary)
    controls = control_contract()
    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_compatibility_dataset_v2_contract_inputs"
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_roots": {
            "scope": rel_path(args.scope_dir),
            "prototype": rel_path(args.prototype_dir),
        },
        "validation_errors": len(errors),
        "dataset_name": contract["dataset_name"],
        "next_todo": next_todo,
        "posterior_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "selected_scope": contract["selected_scope"],
        "family_contract": contract["family_contract"],
        "minimum_reportable_class_mass": controls["minimum_reportable_class_mass"],
        "blocking_conditions": controls["blocking_conditions"],
        "boundary": {
            "split": "train_only_contract",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "dataset_contract": rel_path(args.output_dir / "dataset_contract.json"),
            "row_schema": rel_path(args.output_dir / "row_schema.json"),
            "family_contract": rel_path(args.output_dir / "family_contract.csv"),
            "control_contract": rel_path(args.output_dir / "control_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "dataset_contract.json", contract)
    write_json(args.output_dir / "row_schema.json", contract["row_schema"])
    write_csv(args.output_dir / "family_contract.csv", contract["family_contract"])
    write_json(args.output_dir / "control_contract.json", controls)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    (args.output_dir / "report.md").write_text(build_report(summary, contract), encoding="utf-8")

    print(f"status={status}")
    print(f"dataset={contract['dataset_name']}")
    print(f"next={next_todo}")
    print("primary=support_contact,relative_vertical")
    print("diagnostic=attachment_like")
    print(f"validation_errors={len(errors)}")


if __name__ == "__main__":
    main()
