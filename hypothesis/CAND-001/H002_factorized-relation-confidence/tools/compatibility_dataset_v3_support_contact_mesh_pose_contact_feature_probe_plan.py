#!/usr/bin/env python3
"""Write the support/contact mesh-pose-contact feature probe plan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SOURCE_INVENTORY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan"

EXPECTED_SOURCE_STATUS = "h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_ready_for_mesh_pose_contact_probe"
EXPECTED_SOURCE_NEXT = "compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_plan_input_errors"
SELECTED_ROUTE = "semseg_obb_normal_full_probe_ply_contact_sample_probe"
NEXT_TODO = "compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
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
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_source(summary: dict[str, Any], validation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_SOURCE_NEXT:
        errors.append({"error_type": "unexpected_source_next", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_validation_errors", "actual": summary.get("validation_errors")})
    if validation_rows:
        errors.append({"error_type": "source_validation_error_rows_present", "rows": len(validation_rows)})
    decision = summary.get("path_decision", {})
    if decision.get("mesh_pose_contact_feature_probe_allowed") is not True:
        errors.append({"error_type": "feature_probe_not_allowed", "actual": decision.get("mesh_pose_contact_feature_probe_allowed")})
    for key in ["candidate_materialization_allowed", "learned_smoke_allowed", "multiview_model_input_allowed_now"]:
        if decision.get(key) is not False:
            errors.append({"error_type": "unsafe_decision_flag", "key": key, "actual": decision.get(key)})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified"]:
        if summary.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": summary.get("boundary", {}).get(key)})
    return errors


def feature_family_rows() -> list[dict[str, Any]]:
    return [
        {
            "feature_family": "semseg_obb_pose",
            "tier": "A_full_rows",
            "factor": "G_e",
            "source": "semseg.v2.json",
            "candidate_features": "center_delta_z, bottom_top_gap, axis_length_ratios, subject_uprightness, subject_horizontalness, object_support_flatness",
            "predicate_relevance": "standing on vs lying on depends on subject pose; supported by depends on support surface geometry",
            "runner_scope": "all_support_contact_rows",
            "expected_cost": "low",
            "allowed_model_input_after_audit": True,
        },
        {
            "feature_family": "dominant_normal_alignment",
            "tier": "A_full_rows",
            "factor": "G_e",
            "source": "semseg.v2.json dominantNormal",
            "candidate_features": "subject_normal_upness, object_normal_upness, normal_alignment, support_normal_verticality",
            "predicate_relevance": "surface orientation and contact direction should affect supported-by and standing/lying distinctions",
            "runner_scope": "all_support_contact_rows",
            "expected_cost": "low",
            "allowed_model_input_after_audit": True,
        },
        {
            "feature_family": "obb_contact_proxy",
            "tier": "A_full_rows",
            "factor": "G_e_control_plus_candidate",
            "source": "semseg OBB",
            "candidate_features": "xy_overlap_ratio, support_area_proxy, signed_surface_gap, center_distance_xy, normalized_gap",
            "predicate_relevance": "kept as bridge from old numeric evidence, but must not dominate alone",
            "runner_scope": "all_support_contact_rows",
            "expected_cost": "low",
            "allowed_model_input_after_audit": True,
        },
        {
            "feature_family": "aligned_ply_object_points",
            "tier": "B_stratified_sample",
            "factor": "G_e",
            "source": "labels.instances.align.annotated.v2.ply",
            "candidate_features": "point_count, bbox_percentile_extents, PCA_axes, bottom_contact_band_density, near_surface_point_ratio",
            "predicate_relevance": "point geometry can validate pose and contact bands beyond OBB proxies",
            "runner_scope": "stratified_probe_sample",
            "expected_cost": "medium",
            "allowed_model_input_after_audit": True,
        },
        {
            "feature_family": "mesh_contact_surface",
            "tier": "B_stratified_sample",
            "factor": "G_e",
            "source": "mesh.refined.v2.obj plus mesh segment json",
            "candidate_features": "contact_patch_area_proxy, point_to_surface_gap_histogram, local_support_surface_normal",
            "predicate_relevance": "support/contact should be about surface relation, not just center distance",
            "runner_scope": "stratified_probe_sample",
            "expected_cost": "medium_to_high",
            "allowed_model_input_after_audit": True,
        },
        {
            "feature_family": "sequence_visibility_quality",
            "tier": "C_optional_inventory_only",
            "factor": "Q_e",
            "source": "sequence.zip",
            "candidate_features": "co_visible_frame_count, color_depth_pose_availability, crop_quality_proxy, occlusion_flag_placeholder",
            "predicate_relevance": "helps abstain/observability; not a primary C_e feature yet",
            "runner_scope": "asset_inventory_or_small_sample_only",
            "expected_cost": "medium",
            "allowed_model_input_after_audit": False,
        },
    ]


def probe_metric_rows() -> list[dict[str, Any]]:
    return [
        {
            "probe": "derivability",
            "metric": "feature_non_missing_rate",
            "required": ">=0.95 for Tier A; report for Tier B",
            "purpose": "confirm source join becomes numeric feature rows",
        },
        {
            "probe": "finite_value_sanity",
            "metric": "finite_numeric_rate",
            "required": ">=0.99 for retained features",
            "purpose": "drop unstable divisions, invalid normals, and degenerate OBB features",
        },
        {
            "probe": "predicate_variation",
            "metric": "effect_size_by_predicate",
            "required": "diagnostic only",
            "purpose": "check whether standing/lying/supported-by differ in pose/contact features",
        },
        {
            "probe": "hard_surface_sensitivity",
            "metric": "feature_shift_hard_vs_non_hard_surface",
            "required": "must report before any materialization",
            "purpose": "detect floor/wall/ceiling shortcut dependence",
        },
        {
            "probe": "queue_sensitivity",
            "metric": "feature_shift_HL_vs_LH",
            "required": "diagnostic only; not a target",
            "purpose": "avoid turning queue construction into feature-label shortcut",
        },
        {
            "probe": "source_leakage_absence",
            "metric": "blocked_fields_absent",
            "required": "must pass",
            "purpose": "ensure source score, rank, queue kind, construction proxy, and human labels are absent from feature output",
        },
        {
            "probe": "old_numeric_dominance_check",
            "metric": "incremental_feature_correlation_vs_old_obb_proxy",
            "required": "must report before materialization",
            "purpose": "check whether new features add evidence beyond old distance/overlap/gap proxies",
        },
    ]


def sampling_policy_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    join = summary.get("join_summary", {})
    predicate_counts = join.get("predicate_counts", {})
    queue_counts = join.get("queue_counts", {})
    return [
        {
            "scope": "Tier_A_full_semseg_features",
            "rows": join.get("rows"),
            "sampling": "all support/contact queue rows",
            "reason": "semseg OBB and dominant normal features are cheap and available at full coverage",
        },
        {
            "scope": "Tier_B_ply_mesh_probe_sample",
            "rows": 1200,
            "sampling": "balanced by predicate x hard_surface x geometry_status where possible; cap scan and visible-pair share",
            "reason": "aligned PLY and mesh contact features may be more expensive; first check feasibility and distributions",
        },
        {
            "scope": "Tier_B_non_hard_surface_priority",
            "rows": "at least 360 if available",
            "sampling": "oversample non-hard-surface support/contact pairs",
            "reason": "hard-surface dominance is a known shortcut risk",
        },
        {
            "scope": "Tier_C_multiview_sample",
            "rows": 120,
            "sampling": "small source/visibility audit sample only",
            "reason": "multi-view remains Q_e/audit-first and should not become immediate model input",
        },
        {
            "scope": "observed_predicate_counts",
            "rows": json.dumps(predicate_counts, sort_keys=True),
            "sampling": "source inventory observation",
            "reason": "predicate distribution is balanced enough for probe stratification",
        },
        {
            "scope": "observed_queue_counts",
            "rows": json.dumps(queue_counts, sort_keys=True),
            "sampling": "source inventory observation",
            "reason": "HL/LH is too imbalanced for reliability smoke; queue kind remains audit-only",
        },
    ]


def leakage_control_rows() -> list[dict[str, Any]]:
    return [
        {
            "field_group": "blocked_model_inputs",
            "fields": "source_score, semantic_rank, rank_band, queue_kind, geometry_status, h001_verification_status, label_match_status, machine_hint, counterfactual_type, row_role, human_label",
            "reason": "These encode source confidence, construction route, or labels rather than deployable geometry evidence.",
            "allowed_use": "audit/control/report only",
        },
        {
            "field_group": "allowed_feature_inputs",
            "fields": "scan_id for asset join, subject_id, object_id, semseg OBB, dominantNormal, aligned PLY objectId vertices, mesh segment files",
            "reason": "These are predicate-independent geometry sources.",
            "allowed_use": "feature derivation",
        },
        {
            "field_group": "allowed_audit_strata",
            "fields": "predicate_label, hard_surface_pair, queue_kind, geometry_status, visible_pair, scan_id",
            "reason": "Needed for stratified diagnostics and shortcut controls.",
            "allowed_use": "stratification and reporting, not feature columns for C_e",
        },
        {
            "field_group": "multi_view",
            "fields": "sequence existence, co-visible frame count, crop quality",
            "reason": "Visual evidence can help observability but can hide target shortcuts if promoted too early.",
            "allowed_use": "Q_e/audit-first only in the next runner",
        },
    ]


def runner_contract(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Derive and audit support/contact mesh/pose/contact geometry evidence candidates before materialization or learned smoke.",
        "input_roots": {
            "source_inventory": rel_path(DEFAULT_SOURCE_INVENTORY_DIR),
            "rga_queue": "artifacts/train_rga_full/open3dsg_train_full/rga/",
            "three_rscan": "local_dataset/3RScan/scans/",
        },
        "runner_requirements": [
            "derive Tier A semseg OBB/normal features for all support/contact rows",
            "derive Tier B aligned PLY/mesh contact features on a stratified sample",
            "write model-safe feature tables without source score/rank/queue/label fields",
            "write separate audit table with predicate, queue, hard-surface, geometry-status strata",
            "report derivability, finite-value, hard-surface sensitivity, queue sensitivity, and old-numeric dominance",
            "do not train a learned model",
            "do not materialize a compatibility target",
            "do not use validation/test split",
        ],
        "required_outputs": [
            "feature_schema.json",
            "tier_a_semseg_feature_summary.csv",
            "tier_b_ply_mesh_probe_summary.csv",
            "feature_derivability.csv",
            "feature_distribution_diagnostics.csv",
            "old_numeric_dominance_diagnostics.csv",
            "shortcut_risk_diagnostics.csv",
            "model_safe_feature_preview.jsonl",
            "audit_feature_preview.jsonl",
            "path_decision.json",
            "summary.json",
            "report.md",
            "validation_errors.jsonl",
        ],
        "promotion_gate": {
            "feature_probe_to_materialization_plan": [
                "Tier A feature derivability >=0.95",
                "retained features finite numeric rate >=0.99",
                "new mesh/pose/contact features are not identical to old numeric gap/overlap proxies",
                "hard-surface and queue risks are explicitly quantified",
                "model-safe feature table contains no source/label/construction fields",
            ],
            "materialization_to_learned_smoke": [
                "not authorized by this runner",
                "requires later shortcut-controlled target materialization",
            ],
        },
        "source_inventory_counts": {
            "support_rows": summary.get("join_summary", {}).get("rows"),
            "distinct_scans": summary.get("join_summary", {}).get("distinct_scans"),
            "mesh_contact_surface_possible_rate": summary.get("join_summary", {}).get("mesh_contact_surface_possible_rate"),
            "sequence_multiview_possible_rate": summary.get("join_summary", {}).get("sequence_multiview_possible_rate"),
        },
    }


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "run_learned_smoke_now",
            "verdict": "reject",
            "reason": "Source inventory only proves join coverage, not target identifiability or class balance.",
            "next_action": "feature_probe_first",
        },
        {
            "route": "materialize_support_contact_target_now",
            "verdict": "reject",
            "reason": "hard-surface dominance, HL/LH imbalance, and exact-pair capacity risks remain high.",
            "next_action": "derive_and_audit_Ge_features",
        },
        {
            "route": "promote_multiview_to_model_input_now",
            "verdict": "defer",
            "reason": "multi-view may help Q_e and audit labels, but deployable visual features need separate controls.",
            "next_action": "keep_multiview_Qe_audit_first",
        },
        {
            "route": "semseg_obb_normal_full_probe",
            "verdict": "selected_tier_A",
            "reason": "full coverage and low extraction cost make this the first geometry evidence probe.",
            "next_action": NEXT_TODO,
        },
        {
            "route": "aligned_ply_mesh_contact_sample_probe",
            "verdict": "selected_tier_B",
            "reason": "object point and mesh contact features are more informative but costlier, so start with a stratified sample.",
            "next_action": NEXT_TODO,
        },
    ]


def build_summary(source_summary: dict[str, Any], errors: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    status = STATUS_READY if not errors else STATUS_ERRORS
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_route": SELECTED_ROUTE if not errors else "fix_inputs_before_feature_probe_plan",
        "next_todo": NEXT_TODO if not errors else "fix_mesh_pose_contact_feature_probe_plan_inputs",
        "validation_errors": len(errors),
        "source_inventory_status": source_summary.get("status"),
        "source_inventory_counts": {
            "support_rows": source_summary.get("join_summary", {}).get("rows"),
            "distinct_scans": source_summary.get("join_summary", {}).get("distinct_scans"),
            "distinct_directed_pairs": source_summary.get("join_summary", {}).get("distinct_directed_pairs"),
            "scan_asset_complete_rate": source_summary.get("join_summary", {}).get("scan_asset_complete_rate"),
            "semseg_both_objects_present_rate": source_summary.get("join_summary", {}).get("semseg_both_objects_present_rate"),
            "mesh_contact_surface_possible_rate": source_summary.get("join_summary", {}).get("mesh_contact_surface_possible_rate"),
            "sequence_multiview_possible_rate": source_summary.get("join_summary", {}).get("sequence_multiview_possible_rate"),
        },
        "plan_decision": {
            "feature_probe_allowed": not errors,
            "tier_a_full_semseg_probe": True,
            "tier_b_ply_mesh_sample_probe": True,
            "multiview_qe_audit_first": True,
            "candidate_materialization_allowed": False,
            "learned_smoke_allowed": False,
            "paper_evidence_allowed": False,
        },
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "feature_family_plan": rel_path(output_dir / "feature_family_plan.csv"),
            "probe_metric_plan": rel_path(output_dir / "probe_metric_plan.csv"),
            "sampling_policy": rel_path(output_dir / "sampling_policy.csv"),
            "leakage_controls": rel_path(output_dir / "leakage_controls.csv"),
            "route_decision": rel_path(output_dir / "route_decision.csv"),
            "runner_contract": rel_path(output_dir / "runner_contract.json"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "boundary": {
            "split": "train_only_feature_probe_plan",
            "validation_usage": False,
            "test_usage": False,
            "materializes_candidate_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
    }


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["source_inventory_counts"]
    decision = summary["plan_decision"]
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Mesh-Pose-Contact Feature Probe Plan",
            "",
            "## Status",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_route = {summary['selected_route']}",
            f"next_todo = {summary['next_todo']}",
            f"validation_errors = {summary['validation_errors']}",
            "```",
            "",
            "## Source Basis",
            "",
            "```text",
            f"support_rows = {counts['support_rows']}",
            f"distinct_scans = {counts['distinct_scans']}",
            f"scan_asset_complete_rate = {counts['scan_asset_complete_rate']}",
            f"semseg_both_objects_present_rate = {counts['semseg_both_objects_present_rate']}",
            f"mesh_contact_surface_possible_rate = {counts['mesh_contact_surface_possible_rate']}",
            f"sequence_multiview_possible_rate = {counts['sequence_multiview_possible_rate']}",
            "```",
            "",
            "## Decision",
            "",
            "```text",
            f"feature_probe_allowed = {decision['feature_probe_allowed']}",
            f"tier_a_full_semseg_probe = {decision['tier_a_full_semseg_probe']}",
            f"tier_b_ply_mesh_sample_probe = {decision['tier_b_ply_mesh_sample_probe']}",
            f"multiview_qe_audit_first = {decision['multiview_qe_audit_first']}",
            f"candidate_materialization_allowed = {decision['candidate_materialization_allowed']}",
            f"learned_smoke_allowed = {decision['learned_smoke_allowed']}",
            "```",
            "",
            "## Probe Design",
            "",
            "Tier A derives semseg OBB and dominant-normal features for all support/contact rows.",
            "Tier B derives aligned PLY and mesh-contact features only on a stratified probe sample.",
            "The runner must report feature derivability, finite-value sanity, hard-surface sensitivity,",
            "queue sensitivity, and whether new mesh/pose/contact features add signal beyond old numeric",
            "gap/overlap proxies.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(args.source_inventory_dir / "summary.json")
    source_errors = read_jsonl(args.source_inventory_dir / "validation_errors.jsonl")
    errors = validate_source(source_summary, source_errors)

    summary = build_summary(source_summary, errors, output_dir)
    feature_rows = feature_family_rows()
    metric_rows = probe_metric_rows()
    sample_rows = sampling_policy_rows(source_summary)
    leakage_rows = leakage_control_rows()
    routes = route_rows()
    contract = runner_contract(source_summary)

    write_json(output_dir / "summary.json", summary)
    write_csv(output_dir / "feature_family_plan.csv", feature_rows)
    write_csv(output_dir / "probe_metric_plan.csv", metric_rows)
    write_csv(output_dir / "sampling_policy.csv", sample_rows)
    write_csv(output_dir / "leakage_controls.csv", leakage_rows)
    write_csv(output_dir / "route_decision.csv", routes)
    write_json(output_dir / "runner_contract.json", contract)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(report_text(summary), encoding="utf-8")

    print(f"status={summary['status']}")
    print(f"selected_route={summary['selected_route']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
