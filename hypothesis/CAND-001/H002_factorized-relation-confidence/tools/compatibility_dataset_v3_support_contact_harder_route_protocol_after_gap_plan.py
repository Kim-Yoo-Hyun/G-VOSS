#!/usr/bin/env python3
"""Freeze the H002 support/contact harder-route protocol after the gap plan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_GAP_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_principled_design_gap_plan_after_table_review"
DEFAULT_OFFICIAL_SCHEMA_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_candidate_materialization_schema_audit_after_docker_implementation"
DEFAULT_OFFICIAL_RESULT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_metric_result_review_after_runner"
DEFAULT_SUPPORT_POINT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position"
DEFAULT_SUPPORT_POSE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan"

EXPECTED_GAP_STATUS = "h002_compatibility_dataset_v3_principled_design_gap_plan_after_table_review_ready"
EXPECTED_GAP_NEXT = "compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan_input_errors"
SELECTED_PATH = "support_contact_harder_route_protocol_locked_select_source_inventory"
NEXT_TODO = "compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-dir", type=Path, default=DEFAULT_GAP_DIR)
    parser.add_argument("--official-schema-dir", type=Path, default=DEFAULT_OFFICIAL_SCHEMA_DIR)
    parser.add_argument("--official-result-dir", type=Path, default=DEFAULT_OFFICIAL_RESULT_DIR)
    parser.add_argument("--support-point-dir", type=Path, default=DEFAULT_SUPPORT_POINT_DIR)
    parser.add_argument("--support-pose-dir", type=Path, default=DEFAULT_SUPPORT_POSE_DIR)
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
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def validate_inputs(gap_summary: dict[str, Any], gap_contract: dict[str, Any], gap_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if gap_summary.get("status") != EXPECTED_GAP_STATUS:
        errors.append({"error_type": "unexpected_gap_status", "actual": gap_summary.get("status")})
    if gap_summary.get("next_todo") != EXPECTED_GAP_NEXT:
        errors.append({"error_type": "unexpected_gap_next_todo", "actual": gap_summary.get("next_todo")})
    if gap_summary.get("validation_errors") != 0:
        errors.append({"error_type": "gap_validation_errors", "actual": gap_summary.get("validation_errors")})
    if line_count(gap_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "gap_validation_errors_file_not_empty"})

    decision = gap_summary.get("decision", {})
    if decision.get("selected_gap") != "harder_support_contact_route":
        errors.append({"error_type": "unexpected_selected_gap", "actual": decision.get("selected_gap")})
    if decision.get("source_deployable_experiment") != "defer_until_harder_route_stable":
        errors.append({"error_type": "source_deployable_not_deferred", "actual": decision.get("source_deployable_experiment")})
    if decision.get("p_obs_p_rel_branch") != "defer_until_independent_observability_labels":
        errors.append({"error_type": "pobs_prel_not_deferred", "actual": decision.get("p_obs_p_rel_branch")})

    relation_types = gap_contract.get("relation_types", {})
    if relation_types.get("main") != ["standing on", "lying on"]:
        errors.append({"error_type": "unexpected_main_predicates", "actual": relation_types.get("main")})
    if relation_types.get("diagnostic") != ["supported by"]:
        errors.append({"error_type": "unexpected_diagnostic_predicates", "actual": relation_types.get("diagnostic")})
    feature_boundary = gap_contract.get("feature_boundary", {})
    if "excluded from C_e" not in feature_boundary.get("Z_e", ""):
        errors.append({"error_type": "z_e_not_excluded_from_c_e", "actual": feature_boundary.get("Z_e")})
    if "excluded from C_e" not in feature_boundary.get("Q_e", ""):
        errors.append({"error_type": "q_e_not_excluded_from_c_e", "actual": feature_boundary.get("Q_e")})
    return errors


def relation_scope_rows() -> list[dict[str, Any]]:
    return [
        {
            "predicate": "standing on",
            "route_role": "main",
            "target_role": "hard_support_contact_compatibility",
            "positive_semantics": "subject is upright or load-bearing with bottom support from object",
            "negative_semantics": "near/above/contact-like but not standing support",
            "reason": "Requires pose/contact/support-surface evidence beyond signed z-order.",
        },
        {
            "predicate": "lying on",
            "route_role": "main",
            "target_role": "hard_support_contact_compatibility",
            "positive_semantics": "subject is horizontally supported by object with broad/local contact",
            "negative_semantics": "near/above/contact-like but not lying support",
            "reason": "Requires orientation and contact-patch compatibility, not just vertical relation.",
        },
        {
            "predicate": "supported by",
            "route_role": "diagnostic",
            "target_role": "superordinate_support_decomposition",
            "positive_semantics": "broad support evidence may exist but subtype is under-specified",
            "negative_semantics": "reject or abstain depending on whether subtype evidence is missing or contradictory",
            "reason": "Too broad for the main binary C_e target; useful for relabel/abstain diagnostics.",
        },
    ]


def geometry_evidence_rows() -> list[dict[str, Any]]:
    return [
        {
            "feature_group": "vertical_gap",
            "model_safe_name": "g_vertical_gap",
            "description": "distance between subject bottom and object top/support surface",
            "predicate_independent": True,
            "why_needed": "support/contact cannot ignore whether the subject is physically above or interpenetrating the object",
        },
        {
            "feature_group": "xy_overlap",
            "model_safe_name": "g_xy_support_overlap",
            "description": "horizontal overlap between subject footprint and object support footprint",
            "predicate_independent": True,
            "why_needed": "standing/lying require plausible support area, not only small Euclidean distance",
        },
        {
            "feature_group": "contact_patch",
            "model_safe_name": "g_contact_patch_ratio",
            "description": "near-contact point or mesh patch size normalized by subject/object scale",
            "predicate_independent": True,
            "why_needed": "local contact evidence distinguishes true support from proximity",
        },
        {
            "feature_group": "support_surface_normal",
            "model_safe_name": "g_support_surface_normal_alignment",
            "description": "whether the candidate support object exposes a surface normal compatible with support",
            "predicate_independent": True,
            "why_needed": "support requires a plausible load-bearing surface, not any neighboring object",
        },
        {
            "feature_group": "subject_pose_axis",
            "model_safe_name": "g_subject_principal_axis",
            "description": "subject principal-axis orientation and height/width ratio in pair-normalized coordinates",
            "predicate_independent": True,
            "why_needed": "standing versus lying depends on pose/orientation after T_e interprets G_e",
        },
        {
            "feature_group": "bottom_surface_proximity",
            "model_safe_name": "g_bottom_surface_proximity",
            "description": "proximity between subject lower surface and candidate support surface",
            "predicate_independent": True,
            "why_needed": "filters cases where centers are close but support surfaces do not align",
        },
        {
            "feature_group": "local_point_density",
            "model_safe_name": "g_local_contact_point_density",
            "description": "density of subject/object points near the estimated contact region",
            "predicate_independent": True,
            "why_needed": "guards against OBB-only artifacts and sparse/fragmented contact evidence",
        },
        {
            "feature_group": "mesh_gap_intersection",
            "model_safe_name": "g_mesh_gap_intersection",
            "description": "mesh-derived gap or intersection around the candidate support region",
            "predicate_independent": True,
            "why_needed": "mesh evidence can expose impossible penetration or missing physical contact",
        },
        {
            "feature_group": "surface_alignment",
            "model_safe_name": "g_surface_alignment",
            "description": "alignment between subject contact surface and object support surface",
            "predicate_independent": True,
            "why_needed": "standing/lying compatibility should use local surface relation, not only global boxes",
        },
    ]


def factor_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "factor": "T_e",
            "main_c_e_input": "yes",
            "allowed_fields": "predicate text/label, predicate family embedding, optional subject/object semantic class content",
            "blocked_fields": "source score, source rank, GT match, proxy label, geometry status",
            "reason": "T_e should encode relation meaning, not upstream confidence or construction metadata.",
        },
        {
            "factor": "G_e",
            "main_c_e_input": "yes",
            "allowed_fields": "predicate-independent pose/contact/overlap/gap/point/mesh features",
            "blocked_fields": "predicate label, source score, label-derived status, p_geom_valid rule label",
            "reason": "G_e must be evidence before predicate interpretation.",
        },
        {
            "factor": "Z_e",
            "main_c_e_input": "no",
            "allowed_fields": "source confidence and rank only in diagnostic or later reliability calibration",
            "blocked_fields": "all Z_e fields inside compatibility head",
            "reason": "C_e must not copy source confidence.",
        },
        {
            "factor": "Q_e",
            "main_c_e_input": "no",
            "allowed_fields": "coverage, mesh completeness, view availability, evidence quality diagnostics",
            "blocked_fields": "Q_e inside main hard-route compatibility metric",
            "reason": "This stage tests compatibility, not p_obs/selective decision.",
        },
        {
            "factor": "C_e",
            "main_c_e_input": "output",
            "allowed_fields": "learned or scored compatibility between T_e and G_e",
            "blocked_fields": "direct target labels, hidden construction fields, source confidence shortcut",
            "reason": "C_e is the mechanism being tested.",
        },
    ]


def model_safe_schema_rows() -> list[dict[str, Any]]:
    return [
        {"field_group": "row_id", "model_safe": True, "examples": "candidate_id, scan_id_hash_or_group_id", "notes": "scan_id may be used only for split/grouping, not as C_e feature"},
        {"field_group": "T_e", "model_safe": True, "examples": "predicate_label, predicate_family, subject_class, object_class", "notes": "source score/rank excluded"},
        {"field_group": "G_e", "model_safe": True, "examples": "g_vertical_gap, g_xy_support_overlap, g_contact_patch_ratio, g_subject_principal_axis", "notes": "predicate-independent feature names only"},
        {"field_group": "feature_mask", "model_safe": True, "examples": "has_point_contact, has_mesh_gap, has_surface_normal", "notes": "mask can indicate availability but must not encode target"},
        {"field_group": "target", "model_safe": False, "examples": "accept/reject label, compatibility_label", "notes": "target is label-only, never input"},
        {"field_group": "hidden_construction", "model_safe": False, "examples": "proxy_bucket, geometry_status, p_geom_valid_bucket, label_source", "notes": "hidden manifest only"},
        {"field_group": "Z_e", "model_safe": False, "examples": "source_score, source_rank, source_id", "notes": "diagnostic or later p_rel calibration only"},
        {"field_group": "Q_e", "model_safe": False, "examples": "coverage_tier, mesh_quality, multiview_quality", "notes": "diagnostic only for this hard-route C_e protocol"},
    ]


def control_protocol_rows() -> list[dict[str, Any]]:
    return [
        {
            "control": "semantic_only",
            "required": True,
            "input": "T_e only",
            "pass_expectation": "below T_e_x_G_e",
            "failure_meaning": "predicate/class prior can solve target",
        },
        {
            "control": "geometry_only",
            "required": True,
            "input": "G_e only",
            "pass_expectation": "below T_e_x_G_e",
            "failure_meaning": "target collapsed to a fixed geometry rule",
        },
        {
            "control": "plain_concat",
            "required": True,
            "input": "T_e + G_e without explicit compatibility interaction",
            "pass_expectation": "below T_e_x_G_e or clearly weaker under controls",
            "failure_meaning": "factorized compatibility not needed over naive fusion",
        },
        {
            "control": "wrong_T_same_route",
            "required": True,
            "input": "swap standing on and lying on T_e while preserving G_e",
            "pass_expectation": "metric degrades strongly",
            "failure_meaning": "predicate semantics is not being used",
        },
        {
            "control": "shuffled_G_global",
            "required": True,
            "input": "shuffle G_e across rows",
            "pass_expectation": "near chance or clear degradation",
            "failure_meaning": "geometry evidence is not row-specific",
        },
        {
            "control": "shuffled_G_within_class_pair",
            "required": True,
            "input": "shuffle G_e within predicate/class-pair or support-surface strata when available",
            "pass_expectation": "degrade relative to real T_e_x_G_e",
            "failure_meaning": "class-pair prior rather than pair geometry drives result",
        },
        {
            "control": "subject_object_swap",
            "required": True,
            "input": "swap subject/object geometry roles",
            "pass_expectation": "degrade for directional support relations",
            "failure_meaning": "model ignores support direction",
        },
        {
            "control": "shortcut_probe_suite",
            "required": True,
            "input": "predicate-only, subject class, object class, class pair, predicate x class pair, scan id, instance id, source rank",
            "pass_expectation": "cannot explain the claimed gain alone",
            "failure_meaning": "route remains shortcut-prone",
        },
    ]


def split_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "stage": "source_inventory",
            "policy": "read-only inventory before row materialization",
            "official_validation_allowed": "inventory_only",
            "official_test_allowed": False,
            "reason": "Confirm feature availability and class-pair balance before metric generation.",
        },
        {
            "stage": "materialization",
            "policy": "Docker materialization under experiments/H002_compatibility_routing when promoted",
            "official_validation_allowed": "candidate_materialization_without_metric",
            "official_test_allowed": False,
            "reason": "Maintain paper-level reproducibility without test leakage.",
        },
        {
            "stage": "schema_shortcut_audit",
            "policy": "must pass before any learned smoke or official metric",
            "official_validation_allowed": "schema_audit_only",
            "official_test_allowed": False,
            "reason": "Previous support/contact branch had class-pair shortcut risk.",
        },
        {
            "stage": "metric_runner",
            "policy": "run only after protocol, materialization, split, and shortcut audit are locked",
            "official_validation_allowed": "eval_only_after_freeze",
            "official_test_allowed": False,
            "reason": "Avoid result-driven protocol edits.",
        },
    ]


def promotion_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "G1_feature_boundary",
            "required_condition": "C_e input includes T_e and G_e only; Z_e/Q_e/hidden construction fields absent",
            "promotion_if_passed": "protocol can proceed to source inventory/materialization",
            "blocked_if_failed": "compatibility claim invalid",
        },
        {
            "gate": "G2_shortcut_resistance",
            "required_condition": "predicate/class/class-pair/source-rank/scan/instance probes do not explain the claimed gain",
            "promotion_if_passed": "hard-route metric may be interpreted as compatibility evidence",
            "blocked_if_failed": "keep diagnostic and repair sampling",
        },
        {
            "gate": "G3_ablation_dominance",
            "required_condition": "T_e_x_G_e beats T-only, G-only, and plain concat under family-wise metrics",
            "promotion_if_passed": "support/contact can become hard-route mechanism evidence",
            "blocked_if_failed": "do not claim factorized compatibility necessity",
        },
        {
            "gate": "G4_control_collapse",
            "required_condition": "wrong-T and shuffled-G controls degrade substantially",
            "promotion_if_passed": "predicate and geometry are both used",
            "blocked_if_failed": "model may be exploiting non-causal shortcuts",
        },
        {
            "gate": "G5_predicate_slice_consistency",
            "required_condition": "standing on and lying on slices both improve or failure is explicitly explained",
            "promotion_if_passed": "support/contact route is not one-predicate-only",
            "blocked_if_failed": "narrow the claim to the successful predicate or keep diagnostic",
        },
        {
            "gate": "G6_claim_boundary",
            "required_condition": "no claim of solved support/contact, source reranking, p_rel/p_obs, official test, or all-relation generalization",
            "promotion_if_passed": "bounded hard-route evidence wording allowed",
            "blocked_if_failed": "paper-facing use blocked",
        },
    ]


def blocked_claim_rows() -> list[dict[str, Any]]:
    return [
        {"blocked_claim": "support/contact is solved", "reason": "This protocol only tests hard-route C_e evidence."},
        {"blocked_claim": "calibrated p_rel or p_obs", "reason": "Q_e and observability labels are excluded from this stage."},
        {"blocked_claim": "source reranking recall/violation improvement", "reason": "Z_e/source candidates are deferred until hard route is stable."},
        {"blocked_claim": "official test performance", "reason": "Official test remains unused."},
        {"blocked_claim": "all 3DSSG relation generalization", "reason": "The route is scoped to standing/lying support/contact with supported-by diagnostics."},
    ]


def next_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "selected_path": SELECTED_PATH,
        "route": "support_contact_harder_route",
        "purpose": "Inventory and materialize a harder support/contact C_e route before source-deployable or p_obs/p_rel experiments.",
        "main_predicates": ["standing on", "lying on"],
        "diagnostic_predicates": ["supported by"],
        "main_c_e_inputs": ["T_e", "G_e"],
        "excluded_from_main_c_e": ["Z_e", "Q_e", "target labels", "hidden construction fields", "H001 p_geom_valid/rule labels"],
        "required_geometry_evidence": [row["model_safe_name"] for row in geometry_evidence_rows()],
        "required_controls": [row["control"] for row in control_protocol_rows()],
        "promotion_gates": [row["gate"] for row in promotion_gate_rows()],
        "next_stage_should_do": [
            "inventory full-train and official-validation availability for the richer G_e fields",
            "check standing/lying class-pair balance before materialization",
            "confirm point/mesh/multiview evidence availability without adding Q_e to C_e",
            "prepare model-safe and hidden manifest schemas for Docker materialization",
        ],
        "next_stage_should_not_do": [
            "run official test",
            "promote paper metric",
            "train p_obs/p_rel",
            "use source score or source rank inside C_e",
            "rewrite the protocol after seeing metrics",
        ],
    }


def evidence_context(
    official_schema: dict[str, Any],
    official_result: dict[str, Any],
    support_point: dict[str, Any],
    support_pose: dict[str, Any],
) -> dict[str, Any]:
    official_audit = official_schema.get("audit_summary", {})
    official_decision = official_result.get("decision", {})
    support_pose_result = support_pose.get("mechanism_result", {})
    return {
        "official_schema_status": official_schema.get("status"),
        "official_support_contact_high_shortcut": official_audit.get("support_contact_high_shortcut"),
        "official_z_e_excluded_from_main_c_e": official_audit.get("z_e_excluded_from_main_c_e"),
        "official_metric_support_contact_role": "diagnostic" if "support_contact" in official_decision.get("diagnostic_families", []) else "unknown",
        "support_point_status": support_point.get("status"),
        "support_point_selected_path": support_point.get("selected_path"),
        "support_pose_status": support_pose.get("status"),
        "support_pose_selected_path": support_pose.get("selected_path"),
        "support_pose_primary_auroc": support_pose_result.get("primary_auroc"),
        "support_pose_geometry_only_auroc": support_pose_result.get("geometry_only_auroc"),
        "support_pose_plain_concat_auroc": support_pose_result.get("plain_concat_auroc"),
        "support_pose_wrong_t_auroc": support_pose_result.get("wrong_t_auroc"),
    }


def write_report(path: Path, summary: dict[str, Any], tables: dict[str, list[dict[str, Any]]], contract: dict[str, Any]) -> None:
    lines = [
        "# H002 Support/Contact Harder Route Protocol After Gap Plan",
        "",
        "## Status",
        "",
        "```text",
        f"artifact_root = {summary['output_artifacts']['artifact_root']}",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Judgment",
        "",
        "The next H002 route is not another signed-comparison family. It is a",
        "support/contact hard route where the same pair geometry must be interpreted",
        "through the predicate semantics of `standing on` or `lying on`.",
        "",
        "This stage freezes the protocol only. It does not run a new model, does not",
        "produce an official metric, and does not promote a paper result.",
        "",
        "## Relation Scope",
        "",
        "| Predicate | Role | Target Role | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for row in tables["relation_scope"]:
        lines.append(f"| `{row['predicate']}` | {row['route_role']} | {row['target_role']} | {row['reason']} |")
    lines.extend(["", "## Factor Boundary", "", "| Factor | Main C_e Input | Allowed | Blocked |", "| --- | --- | --- | --- |"])
    for row in tables["factor_boundary"]:
        lines.append(f"| `{row['factor']}` | {row['main_c_e_input']} | {row['allowed_fields']} | {row['blocked_fields']} |")
    lines.extend(["", "## Geometry Evidence", "", "| Feature | Model-Safe Name | Why Needed |", "| --- | --- | --- |"])
    for row in tables["geometry_evidence"]:
        lines.append(f"| `{row['feature_group']}` | `{row['model_safe_name']}` | {row['why_needed']} |")
    lines.extend(["", "## Required Controls", "", "| Control | Input | Pass Expectation | Failure Meaning |", "| --- | --- | --- | --- |"])
    for row in tables["control_protocol"]:
        lines.append(f"| `{row['control']}` | {row['input']} | {row['pass_expectation']} | {row['failure_meaning']} |")
    lines.extend(["", "## Promotion Gates", "", "| Gate | Required Condition | If Failed |", "| --- | --- | --- |"])
    for row in tables["promotion_gates"]:
        lines.append(f"| `{row['gate']}` | {row['required_condition']} | {row['blocked_if_failed']} |")
    lines.extend(
        [
            "",
            "## Next Contract",
            "",
            "```json",
            json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Decision",
            "",
            "- `standing on` and `lying on` are the main hard-route predicates.",
            "- `supported by` remains diagnostic for superordinate support decomposition/relabel/abstain analysis.",
            "- `G_e` is enriched but remains predicate-independent.",
            "- `Z_e` and `Q_e` stay out of the main `C_e` input.",
            "- Source reranking and `p_obs`/`p_rel` remain deferred.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir

    gap_summary = read_json(args.gap_dir / "summary.json")
    gap_contract = read_json(args.gap_dir / "selected_contract.json")
    validation_errors = validate_inputs(gap_summary, gap_contract, args.gap_dir)

    official_schema = read_json(args.official_schema_dir / "summary.json")
    official_result = read_json(args.official_result_dir / "summary.json")
    support_point = read_json(args.support_point_dir / "summary.json")
    support_pose = read_json(args.support_pose_dir / "summary.json")

    tables = {
        "relation_scope": relation_scope_rows(),
        "geometry_evidence": geometry_evidence_rows(),
        "factor_boundary": factor_boundary_rows(),
        "model_safe_schema": model_safe_schema_rows(),
        "control_protocol": control_protocol_rows(),
        "split_policy": split_policy_rows(),
        "promotion_gates": promotion_gate_rows(),
        "blocked_claims": blocked_claim_rows(),
    }
    contract = next_contract()
    context = evidence_context(official_schema, official_result, support_point, support_pose)

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "blocked_fix_gap_plan_before_protocol",
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO if not validation_errors else EXPECTED_GAP_NEXT,
        "input_artifacts": {
            "gap_plan_summary": rel_path(args.gap_dir / "summary.json"),
            "gap_plan_selected_contract": rel_path(args.gap_dir / "selected_contract.json"),
            "official_schema_audit_summary": rel_path(args.official_schema_dir / "summary.json"),
            "official_metric_result_review": rel_path(args.official_result_dir / "summary.json"),
            "support_point_multiview_review": rel_path(args.support_point_dir / "summary.json"),
            "support_pose_conditioned_review": rel_path(args.support_pose_dir / "summary.json"),
        },
        "decision": {
            "protocol_locked": not validation_errors,
            "selected_route": "support_contact_harder_route",
            "main_predicates": ["standing on", "lying on"],
            "diagnostic_predicates": ["supported by"],
            "main_c_e_inputs": ["T_e", "G_e"],
            "z_e_excluded_from_main_c_e": True,
            "q_e_excluded_from_main_c_e": True,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "source_deployable_experiment": "defer_until_harder_route_stable",
            "p_obs_p_rel_branch": "defer_until_independent_observability_labels",
        },
        "evidence_context": context,
        "output_artifacts": {
            "artifact_root": rel_path(output_dir),
            "relation_scope": rel_path(output_dir / "relation_scope.csv"),
            "geometry_evidence_protocol": rel_path(output_dir / "geometry_evidence_protocol.csv"),
            "factor_boundary": rel_path(output_dir / "factor_boundary.csv"),
            "model_safe_schema": rel_path(output_dir / "model_safe_schema.csv"),
            "control_protocol": rel_path(output_dir / "control_protocol.csv"),
            "split_policy": rel_path(output_dir / "split_policy.csv"),
            "promotion_gates": rel_path(output_dir / "promotion_gates.csv"),
            "blocked_claims": rel_path(output_dir / "blocked_claims.csv"),
            "next_contract": rel_path(output_dir / "next_contract.json"),
            "report": rel_path(output_dir / "report.md"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(output_dir / "relation_scope.csv", tables["relation_scope"])
    write_csv(output_dir / "geometry_evidence_protocol.csv", tables["geometry_evidence"])
    write_csv(output_dir / "factor_boundary.csv", tables["factor_boundary"])
    write_csv(output_dir / "model_safe_schema.csv", tables["model_safe_schema"])
    write_csv(output_dir / "control_protocol.csv", tables["control_protocol"])
    write_csv(output_dir / "split_policy.csv", tables["split_policy"])
    write_csv(output_dir / "promotion_gates.csv", tables["promotion_gates"])
    write_csv(output_dir / "blocked_claims.csv", tables["blocked_claims"])
    write_json(output_dir / "next_contract.json", contract)
    write_report(output_dir / "report.md", summary, tables, contract)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
