#!/usr/bin/env python3
"""Write the support/contact pose-conditioned target design plan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_feature_probe_result_review"
DEFAULT_FEATURE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_target_plan"

EXPECTED_REVIEW_STATUS = "h002_compatibility_dataset_v3_support_contact_feature_probe_result_review_select_pose_conditioned_target_plan"
EXPECTED_REVIEW_NEXT = "compatibility_dataset_v3_support_contact_pose_conditioned_target_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_target_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_target_plan_ready_for_capacity_scan"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_target_plan_input_errors"
SELECTED_PATH = "capacity_scan_pose_conditioned_same_geometry_lying_standing_target"
NEXT_TODO = "compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--feature-dir", type=Path, default=DEFAULT_FEATURE_DIR)
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
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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


def validate_inputs(
    review_summary: dict[str, Any],
    review_validation_rows: list[dict[str, Any]],
    feature_summary: dict[str, Any],
    predicate_pair_summary: list[dict[str, str]],
    target_constraints: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if review_summary.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review_summary.get("status")})
    if review_summary.get("next_todo") != EXPECTED_REVIEW_NEXT:
        errors.append({"error_type": "unexpected_review_next", "actual": review_summary.get("next_todo")})
    if review_summary.get("validation_errors") != 0:
        errors.append({"error_type": "review_validation_errors", "actual": review_summary.get("validation_errors")})
    if review_validation_rows:
        errors.append({"error_type": "review_validation_error_rows_present", "rows": len(review_validation_rows)})
    decision = review_summary.get("path_decision", {})
    if decision.get("target_design_plan_allowed") is not True:
        errors.append({"error_type": "target_design_plan_not_allowed", "actual": decision.get("target_design_plan_allowed")})
    for key in ["candidate_materialization_allowed", "learned_smoke_allowed", "paper_evidence_allowed"]:
        if decision.get(key) is not False:
            errors.append({"error_type": "review_boundary_not_false", "key": key, "actual": decision.get(key)})

    counts = feature_summary.get("counts", {})
    if counts.get("support_rows") != 161498:
        errors.append({"error_type": "unexpected_support_rows", "actual": counts.get("support_rows")})
    if counts.get("tier_a_records") != counts.get("support_rows"):
        errors.append({"error_type": "tier_a_not_full_support_rows", "counts": counts})
    if counts.get("tier_b_records", 0) < 1000:
        errors.append({"error_type": "tier_b_probe_below_plan_minimum", "actual": counts.get("tier_b_records")})

    pairs = {row.get("predicate_pair"): row for row in predicate_pair_summary}
    if pairs.get("lying on vs standing on", {}).get("verdict") != "pose_conditioned_contrast_candidate":
        errors.append({"error_type": "primary_pair_not_candidate", "actual": pairs.get("lying on vs standing on")})
    if pairs.get("standing on vs supported by", {}).get("verdict") != "collapse_or_superordinate_overlap":
        errors.append({"error_type": "standing_supported_not_marked_superordinate", "actual": pairs.get("standing on vs supported by")})
    constraints = {row.get("constraint"): row.get("decision") for row in target_constraints}
    if constraints.get("same_geometry_rows") != "required":
        errors.append({"error_type": "same_geometry_constraint_missing", "actual": constraints.get("same_geometry_rows")})
    if constraints.get("supported_by_role") != "not_primary_negative":
        errors.append({"error_type": "supported_by_boundary_missing", "actual": constraints.get("supported_by_role")})
    return errors


def target_contract() -> dict[str, Any]:
    return {
        "dataset_name": "h002_support_contact_pose_conditioned_v3",
        "contract_role": "train-only target design plan before materialization",
        "primary_task": "predicate-geometry compatibility C_e for support/contact pose semantics",
        "core_principle": (
            "Each geometry anchor creates two rows with the same G_e and different T_e. "
            "The positive label depends on whether the object-pair pose is lying-like or upright-support-like."
        ),
        "primary_contrast": {
            "predicates": ["lying on", "standing on"],
            "rows_per_anchor": 2,
            "same_geometry_required": True,
            "anchor_states": [
                {
                    "anchor_state": "lying_like_support_contact",
                    "positive_predicate": "lying on",
                    "negative_predicate": "standing on",
                    "reason": "subject pose is low/flat/horizontal while contact/support evidence is present",
                },
                {
                    "anchor_state": "upright_support_contact",
                    "positive_predicate": "standing on",
                    "negative_predicate": "lying on",
                    "reason": "subject pose is upright/vertical while contact/support evidence is present",
                },
            ],
        },
        "diagnostic_contrast": {
            "predicates": ["lying on", "supported by"],
            "role": "diagnostic_or_superordinate_check",
            "reason": "`supported by` may be true for both lying and standing support cases, so it is not a clean negative for `standing on`.",
        },
        "excluded_primary_contrast": {
            "predicates": ["standing on", "supported by"],
            "reason": "feature-probe review found near-collapse/superordinate overlap",
        },
        "factor_boundary": {
            "T_e": "predicate text/label, relation family, subject/object class labels",
            "Z_e": "source score/rank/source id; allowed only in source baselines, not in C_e",
            "G_e": "predicate-independent mesh/pose/contact feature vector shared by the two rows in an anchor",
            "C_e": "compatibility(T_e, G_e), with Z_e excluded",
            "Q_e": "observability and evidence availability, including optional multi-view audit quality",
        },
        "label_policy": {
            "positive_source": "predeclared geometry/pose/contact anchor state, not source score/rank or HL/LH queue kind",
            "negative_source": "predicate flip on the same G_e anchor",
            "abstain_source": "ambiguous pose, weak contact, low coverage, hard-surface-dominated ambiguous cases",
            "no_gt_policy": "no-GT rows are not automatic negatives",
            "supported_by_policy": "diagnostic superordinate label, not primary binary negative",
        },
        "not_allowed": [
            "HL/LH queue kind as target label",
            "standing on vs supported by as primary binary contrast",
            "wrong-pair geometry as primary negative",
            "shuffled geometry as primary negative",
            "gap/overlap perturbation as primary negative",
            "source score/rank in compatibility head",
            "validation/test usage",
        ],
    }


def anchor_feature_policy() -> list[dict[str, Any]]:
    return [
        {
            "feature_family": "contact_support_core",
            "role": "anchor_filter",
            "features": "abs surface gap, XY overlap/support area, point contact candidate ratio",
            "capacity_scan_thresholds": {
                "abs_gap_max_m_grid": [0.05, 0.10, 0.15, 0.20],
                "xy_overlap_min_grid": [0.10, 0.25, 0.40],
                "point_contact_candidate_ratio_min_grid": [0.01, 0.03, 0.05],
            },
            "decision_rule": "anchor must pass at least one support/contact core threshold set before pose labeling",
        },
        {
            "feature_family": "lying_pose",
            "role": "positive_state_for_lying_on",
            "features": "subject vertical extent ratio, subject flatness ratio, subject major/minor axis upness",
            "capacity_scan_thresholds": {
                "subject_vertical_extent_ratio_max_grid": [0.45, 0.60, 0.80],
                "subject_flatness_ratio_max_grid": [0.20, 0.30, 0.40],
                "subject_major_axis_upness_max_grid": [0.35, 0.50],
            },
            "decision_rule": "lying_like if subject is flat/low or dominant axis is not vertical while contact is present",
        },
        {
            "feature_family": "upright_pose",
            "role": "positive_state_for_standing_on",
            "features": "subject vertical extent ratio, subject major axis upness, subject bottom-band density",
            "capacity_scan_thresholds": {
                "subject_vertical_extent_ratio_min_grid": [1.00, 1.20, 1.50],
                "subject_major_axis_upness_min_grid": [0.50, 0.65, 0.80],
                "point_subject_bottom_band_density_min_grid": [0.02, 0.05, 0.08],
            },
            "decision_rule": "upright_like if subject is vertically elongated/upright while contact is present",
        },
        {
            "feature_family": "quality_observability",
            "role": "Q_e_or_abstain",
            "features": "point counts, scan asset availability, optional multi-view/crop quality",
            "capacity_scan_thresholds": {
                "subject_point_count_min_grid": [30, 100, 300],
                "object_point_count_min_grid": [30, 100, 300],
            },
            "decision_rule": "insufficient geometry or visibility becomes abstain, not reject",
        },
    ]


def quota_plan() -> list[dict[str, Any]]:
    return [
        {
            "quota": "primary_total_rows",
            "target": 400,
            "minimum": 240,
            "unit": "rows",
            "notes": "two rows per anchor; same G_e, different T_e",
        },
        {
            "quota": "primary_anchor_groups",
            "target": 200,
            "minimum": 120,
            "unit": "anchors",
            "notes": "each anchor produces `lying on` and `standing on` rows",
        },
        {
            "quota": "lying_like_anchor_groups",
            "target": 100,
            "minimum": 60,
            "unit": "anchors",
            "notes": "`lying on` positive, `standing on` negative",
        },
        {
            "quota": "upright_anchor_groups",
            "target": 100,
            "minimum": 60,
            "unit": "anchors",
            "notes": "`standing on` positive, `lying on` negative",
        },
        {
            "quota": "non_hard_surface_anchor_share",
            "target": 0.40,
            "minimum": 0.30,
            "unit": "share",
            "notes": "avoid floor/wall/ceiling/room dominance",
        },
        {
            "quota": "max_single_visible_pair_share",
            "target": 0.08,
            "minimum": 0.12,
            "unit": "max_share",
            "notes": "avoid visible object-pair shortcut",
        },
        {
            "quota": "max_single_scan_share",
            "target": 0.05,
            "minimum": 0.10,
            "unit": "max_share",
            "notes": "avoid scan memorization",
        },
        {
            "quota": "supported_by_diagnostic_rows",
            "target": 80,
            "minimum": 0,
            "unit": "rows",
            "notes": "optional diagnostic only; not part of primary binary target",
        },
    ]


def row_schema() -> dict[str, Any]:
    return {
        "schema_name": "h002_support_contact_pose_conditioned_row_v1",
        "top_level_fields": [
            "row_id",
            "anchor_id",
            "split",
            "scan_id_audit_only",
            "subject_instance_id_audit_only",
            "object_instance_id_audit_only",
            "T_e",
            "Z_e_safe",
            "G_e_mesh_pose_contact",
            "Q_e_safe",
            "labels",
            "controls_hidden",
        ],
        "model_feature_blocks": {
            "T_e": [
                "predicate_label",
                "predicate_text",
                "relation_family",
                "subject_class_label",
                "object_class_label",
            ],
            "G_e_mesh_pose_contact": [
                "center_delta_z",
                "surface_gap_subject_bottom_to_object_top",
                "abs_surface_gap_subject_bottom_to_object_top",
                "xy_overlap_min_ratio",
                "support_area_proxy",
                "center_distance_xy",
                "normalized_center_distance_xy",
                "subject_major_axis_upness",
                "subject_vertical_extent_ratio",
                "subject_flatness_ratio",
                "object_vertical_extent_ratio",
                "object_flatness_ratio",
                "normal_alignment",
                "obb_contact_likelihood_proxy",
                "point_surface_gap_subject_bottom_to_object_top_optional",
                "point_abs_surface_gap_optional",
                "point_contact_candidate_ratio_optional",
                "point_subject_bottom_band_density_optional",
                "point_object_top_band_density_optional",
            ],
            "Q_e_safe": [
                "geometry_available",
                "semseg_obb_available",
                "aligned_ply_available",
                "point_counts_sufficient",
                "multi_view_audit_available",
            ],
            "Z_e_safe": [
                "source_score_available",
                "source_rank_available",
            ],
        },
        "labels": {
            "compatibility_y": "1 for compatible predicate on the anchor G_e, 0 for predicate flip",
            "anchor_pose_state": "audit-only lying_like_support_contact or upright_support_contact",
            "abstain_reason": "optional; ambiguous_pose, weak_contact, low_coverage, hard_surface_ambiguous",
        },
        "blocked_model_inputs": [
            "anchor_pose_state",
            "queue_kind",
            "geometry_status",
            "source_score",
            "source_rank",
            "rank_band",
            "visible_pair",
            "scan_id",
            "subject_instance_id",
            "object_instance_id",
            "p_geom_valid",
            "consistency_score",
            "disagreement_score",
            "underconfidence_score",
            "counterfactual_type",
            "row_role",
            "human_label",
        ],
    }


def model_and_control_plan() -> list[dict[str, Any]]:
    return [
        {
            "model_or_control": "M1_source_only_Z",
            "input": "Z_e_safe",
            "expected": "near chance",
            "purpose": "source score/rank must not solve the constructed compatibility target",
        },
        {
            "model_or_control": "M2_semantic_only_T",
            "input": "T_e",
            "expected": "near chance",
            "purpose": "predicate-only must be balanced across positive/negative labels",
        },
        {
            "model_or_control": "M3_geometry_only_G",
            "input": "G_e_mesh_pose_contact",
            "expected": "near chance under grouped evaluation",
            "purpose": "same G_e appears with both positive and negative predicate rows",
        },
        {
            "model_or_control": "M4_plain_concat_TG",
            "input": "T_e + G_e",
            "expected": "diagnostic baseline",
            "purpose": "test whether generic concatenation is enough",
        },
        {
            "model_or_control": "M5_compatibility_interaction",
            "input": "predicate-conditioned interaction between T_e and G_e",
            "expected": "primary success condition",
            "purpose": "test H002 C_e mechanism for support/contact pose semantics",
        },
        {
            "model_or_control": "C1_wrong_T_same_G",
            "input": "swap predicate token within anchor",
            "expected": "score inversion or strong degradation",
            "purpose": "verify the model uses predicate-geometry compatibility",
        },
        {
            "model_or_control": "C2_shuffled_G_same_predicate",
            "input": "shuffle G_e across anchors within predicate",
            "expected": "near chance",
            "purpose": "verify geometry evidence is anchored to the actual object pair",
        },
        {
            "model_or_control": "C3_hard_surface_only_probe",
            "input": "hard-surface indicator as audit-only probe",
            "expected": "below shortcut threshold",
            "purpose": "prevent floor/wall/ceiling shortcut",
        },
    ]


def capacity_scan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "input_sources": {
            "rga_queue_rows": "artifacts/train_rga_full/open3dsg_train_full/rga/train_hl_queue.jsonl and train_lh_queue.jsonl",
            "semseg_features": "derive Tier A semseg OBB/normal features for all support/contact rows",
            "aligned_ply_features": "derive Tier B point/contact features for candidate anchors after semseg prefilter",
            "feature_probe_artifacts": "use previous feature schema, diagnostics, and thresholds as planning references",
        },
        "required_outputs": [
            "capacity_summary.json",
            "threshold_grid_capacity.csv",
            "anchor_candidate_preview.jsonl",
            "shortcut_capacity_audit.csv",
            "path_decision.json",
            "summary.json",
            "report.md",
            "validation_errors.jsonl",
        ],
        "capacity_questions": [
            "How many lying-like and upright-support anchors pass contact/core filters?",
            "Can anchor groups be balanced so each predicate has equal positives and negatives?",
            "Can non-hard-surface share reach at least 0.30 and preferably 0.40?",
            "Can visible-pair and scan concentration be capped?",
            "Does adding optional PLY contact features materially improve anchor separation?",
        ],
        "promotion_gate_to_materialization": {
            "minimum_anchor_groups": 120,
            "target_anchor_groups": 200,
            "minimum_lying_like_anchors": 60,
            "minimum_upright_anchors": 60,
            "minimum_non_hard_surface_share": 0.30,
            "max_single_visible_pair_share": 0.12,
            "max_single_scan_share": 0.10,
            "predicate_positive_counts_balanced": True,
            "geometry_group_rows_per_anchor": 2,
            "validation_usage": False,
            "test_usage": False,
        },
    }


def path_decision(errors: list[dict[str, Any]]) -> dict[str, Any]:
    if errors:
        return {
            "status": STATUS_ERRORS,
            "selected_path": "fix_inputs_before_pose_conditioned_plan",
            "next_todo": EXPECTED_REVIEW_NEXT,
            "validation_errors": len(errors),
            "capacity_scan_allowed": False,
            "candidate_materialization_allowed": False,
            "learned_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "rationale": "Input validation failed; target design plan is not reliable.",
        }
    return {
        "status": STATUS_READY,
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "validation_errors": 0,
        "capacity_scan_allowed": True,
        "candidate_materialization_allowed": False,
        "learned_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "rationale": "The support/contact target should proceed through a capacity scan for pose-conditioned same-G lying/standing anchors before materialization.",
    }


def report_text(summary: dict[str, Any]) -> str:
    decision = summary["path_decision"]
    return f"""# Compatibility Dataset V3 Support/Contact Pose-Conditioned Target Plan

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
next_todo = {summary['next_todo']}
validation_errors = {summary['validation_errors']}
```

## Target Definition

Primary contrast:

```text
same G_e anchor + T_e = lying on
same G_e anchor + T_e = standing on
```

The label is determined by the anchor pose:

```text
lying-like support/contact pose:
  lying on = positive
  standing on = negative

upright support/contact pose:
  standing on = positive
  lying on = negative
```

`supported by` is diagnostic/superordinate and is not used as the clean primary negative for
`standing on`.

## Why This Plan

The previous feature review found that support/contact features are derivable, but direct
materialization remains blocked. The correct next target must force compatibility to depend on
the interaction between `T_e` and `G_e`, not on geometry alone, predicate alone, source score, or
queue construction.

## Capacity Scan Gate

```text
capacity_scan_allowed = {decision['capacity_scan_allowed']}
candidate_materialization_allowed = {decision['candidate_materialization_allowed']}
learned_smoke_allowed = {decision['learned_smoke_allowed']}
paper_evidence_allowed = {decision['paper_evidence_allowed']}
```

The next runner should only scan capacity. It should not materialize final rows or train a model.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()
    review_dir = args.review_dir
    feature_dir = args.feature_dir
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    review_summary = read_json(review_dir / "summary.json")
    feature_summary = read_json(feature_dir / "summary.json")
    review_validation_rows = read_jsonl(review_dir / "validation_errors.jsonl")
    predicate_pair_summary = read_csv(review_dir / "predicate_pair_summary.csv")
    target_constraints = read_csv(review_dir / "target_design_constraints.csv")
    errors = validate_inputs(
        review_summary=review_summary,
        review_validation_rows=review_validation_rows,
        feature_summary=feature_summary,
        predicate_pair_summary=predicate_pair_summary,
        target_constraints=target_constraints,
    )
    decision = path_decision(errors)

    contract = target_contract()
    anchor_policy = anchor_feature_policy()
    quotas = quota_plan()
    schema = row_schema()
    model_plan = model_and_control_plan()
    scan_contract = capacity_scan_contract()
    counts = feature_summary.get("counts", {})
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": decision["status"],
        "selected_path": decision["selected_path"],
        "next_todo": decision["next_todo"],
        "validation_errors": len(errors),
        "review_status": review_summary.get("status"),
        "feature_probe_status": feature_summary.get("status"),
        "counts": {
            "support_rows": counts.get("support_rows"),
            "tier_a_records": counts.get("tier_a_records"),
            "tier_b_records": counts.get("tier_b_records"),
            "tier_b_distinct_scans": counts.get("tier_b_distinct_scans"),
        },
        "primary_contrast": "lying on vs standing on",
        "diagnostic_contrast": "lying on vs supported by",
        "excluded_primary_contrast": "standing on vs supported by",
        "target_contract": contract,
        "quota_plan": quotas,
        "capacity_scan_contract": scan_contract,
        "path_decision": decision,
        "output_paths": {
            "target_contract": rel_path(output_dir / "target_contract.json"),
            "row_schema": rel_path(output_dir / "row_schema.json"),
            "anchor_feature_policy": rel_path(output_dir / "anchor_feature_policy.csv"),
            "quota_plan": rel_path(output_dir / "quota_plan.csv"),
            "model_and_control_plan": rel_path(output_dir / "model_and_control_plan.csv"),
            "capacity_scan_contract": rel_path(output_dir / "capacity_scan_contract.json"),
            "path_decision": rel_path(output_dir / "path_decision.json"),
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "boundary": {
            "split": "train_only_target_design_plan",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_candidate_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
    }

    write_json(output_dir / "target_contract.json", contract)
    write_json(output_dir / "row_schema.json", schema)
    write_csv(output_dir / "anchor_feature_policy.csv", anchor_policy)
    write_csv(output_dir / "quota_plan.csv", quotas)
    write_csv(output_dir / "model_and_control_plan.csv", model_plan)
    write_json(output_dir / "capacity_scan_contract.json", scan_contract)
    write_json(output_dir / "path_decision.json", decision)
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(report_text(summary), encoding="utf-8")

    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
