#!/usr/bin/env python3
"""Plan an independent visual/mesh audit target for support/contact relations."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_DECISION_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis"
)
DEFAULT_SOURCE_INVENTORY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory"
)
DEFAULT_FEATURE_RUNNER_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner"
)
DEFAULT_FEATURE_REVIEW_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_feature_probe_result_review"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan"
)

EXPECTED_DECISION_STATUS = "h002_compatibility_dataset_v3_independent_target_source_decision_selected"
EXPECTED_DECISION_NEXT = "compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan"
EXPECTED_ROUTE = "support_contact_human_visual_mesh_audit_target"
EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_ready_for_mesh_pose_contact_probe"
)
EXPECTED_FEATURE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner_ready_for_result_review"
)
EXPECTED_REVIEW_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_feature_probe_result_review_select_pose_conditioned_target_plan"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan_ready_for_source_inventory"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan_input_errors"
SELECTED_PATH = "plan_visual_mesh_audit_target_source_before_materialization"
NEXT_TODO = "compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory"

SELECTED_PREDICATES = ["lying on", "standing on", "supported by"]
TARGET_TOTAL_ROWS = 480
MIN_TOTAL_ROWS = 360
MIN_PER_PREDICATE = 80
MIN_BINARY_ACCEPT = 80
MIN_BINARY_REJECT = 80
MIN_ABSTAIN = 60


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-dir", type=Path, default=DEFAULT_DECISION_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--feature-runner-dir", type=Path, default=DEFAULT_FEATURE_RUNNER_DIR)
    parser.add_argument("--feature-review-dir", type=Path, default=DEFAULT_FEATURE_REVIEW_DIR)
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
                fields.append(key)
                seen.add(key)
    if not fields:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_required(path: Path, errors: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if not path.exists():
        errors.append({"input": label, "error_type": "missing_file", "path": rel_path(path)})
        return {}
    return read_json(path)


def validate_boundary(summary: dict[str, Any], label: str, errors: list[dict[str, Any]]) -> None:
    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if key in boundary and boundary.get(key) is not False:
            errors.append(
                {
                    "input": label,
                    "error_type": "boundary_not_false",
                    "key": key,
                    "actual": boundary.get(key),
                }
            )


def validate_inputs(
    decision_summary: dict[str, Any],
    target_contract: dict[str, Any],
    source_summary: dict[str, Any],
    feature_summary: dict[str, Any],
    review_summary: dict[str, Any],
    existing_error_rows: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if decision_summary.get("status") != EXPECTED_DECISION_STATUS:
        errors.append(
            {
                "input": "decision_summary",
                "error_type": "unexpected_status",
                "actual": decision_summary.get("status"),
                "expected": EXPECTED_DECISION_STATUS,
            }
        )
    if decision_summary.get("next_todo") != EXPECTED_DECISION_NEXT:
        errors.append(
            {
                "input": "decision_summary",
                "error_type": "unexpected_next_todo",
                "actual": decision_summary.get("next_todo"),
                "expected": EXPECTED_DECISION_NEXT,
            }
        )
    if decision_summary.get("validation_errors") != 0:
        errors.append(
            {
                "input": "decision_summary",
                "error_type": "validation_errors_present",
                "actual": decision_summary.get("validation_errors"),
            }
        )
    if target_contract.get("selected_main_route") != EXPECTED_ROUTE:
        errors.append(
            {
                "input": "target_source_contract",
                "error_type": "unexpected_route",
                "actual": target_contract.get("selected_main_route"),
                "expected": EXPECTED_ROUTE,
            }
        )
    if list(target_contract.get("selected_predicates", [])) != SELECTED_PREDICATES:
        errors.append(
            {
                "input": "target_source_contract",
                "error_type": "unexpected_predicates",
                "actual": target_contract.get("selected_predicates"),
                "expected": SELECTED_PREDICATES,
            }
        )
    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append(
            {
                "input": "source_inventory_summary",
                "error_type": "unexpected_status",
                "actual": source_summary.get("status"),
                "expected": EXPECTED_SOURCE_STATUS,
            }
        )
    if feature_summary.get("status") != EXPECTED_FEATURE_STATUS:
        errors.append(
            {
                "input": "feature_probe_summary",
                "error_type": "unexpected_status",
                "actual": feature_summary.get("status"),
                "expected": EXPECTED_FEATURE_STATUS,
            }
        )
    if review_summary.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append(
            {
                "input": "feature_review_summary",
                "error_type": "unexpected_status",
                "actual": review_summary.get("status"),
                "expected": EXPECTED_REVIEW_STATUS,
            }
        )
    for label, summary in [
        ("decision_summary", decision_summary),
        ("source_inventory_summary", source_summary),
        ("feature_probe_summary", feature_summary),
        ("feature_review_summary", review_summary),
    ]:
        if summary.get("validation_errors") != 0:
            errors.append(
                {
                    "input": label,
                    "error_type": "validation_errors_present",
                    "actual": summary.get("validation_errors"),
                }
            )
        validate_boundary(summary, label, errors)
    for label, rows in existing_error_rows.items():
        if rows:
            errors.append({"input": label, "error_type": "existing_validation_error_rows_present", "rows": len(rows)})
    join_summary = source_summary.get("join_summary", {})
    predicate_counts = join_summary.get("predicate_counts", {})
    for predicate in SELECTED_PREDICATES:
        if int(predicate_counts.get(predicate, 0)) < MIN_PER_PREDICATE:
            errors.append(
                {
                    "input": "source_inventory_summary",
                    "error_type": "predicate_source_capacity_too_small",
                    "predicate": predicate,
                    "actual": predicate_counts.get(predicate, 0),
                    "minimum": MIN_PER_PREDICATE,
                }
            )
    for axis in ["scan_asset_complete_rate", "mesh_contact_surface_possible_rate", "sequence_multiview_possible_rate"]:
        if float(join_summary.get(axis, 0.0)) < 0.95:
            errors.append(
                {
                    "input": "source_inventory_summary",
                    "error_type": "source_coverage_too_low",
                    "axis": axis,
                    "actual": join_summary.get(axis),
                    "minimum": 0.95,
                }
            )
    return errors


def visible_packet_schema_rows() -> list[dict[str, Any]]:
    rows = [
        ("review_id", "visible_identifier", "stable anonymous row id shown to reviewers", "required", "none"),
        ("scan_id_visible", "visible_context", "scan id or hashed scan id for packet lookup", "required", "not a label"),
        ("subject_label", "visible_relation_text", "subject object class label", "required", "audit only; later shortcut probe"),
        ("predicate_label", "visible_relation_text", "candidate predicate text", "required", "part of T_e, not source score"),
        ("object_label", "visible_relation_text", "object class label", "required", "audit only; later shortcut probe"),
        ("point_crop_path", "visual_mesh_evidence", "subject/object/pair point or mesh crop", "required", "review evidence"),
        ("mesh_render_path", "visual_mesh_evidence", "pair-level mesh rendering or contact render", "required", "review evidence"),
        ("multiview_contact_sheet_path", "visual_mesh_evidence", "co-visible RGB-D or rendered view sheet when available", "required", "audit evidence only at this stage"),
        ("mesh_contact_summary_visible", "numeric_evidence_summary", "human-readable contact/gap/overlap summary without hidden target fields", "required", "review aid"),
        ("pose_summary_visible", "numeric_evidence_summary", "human-readable upright/lying/relative pose summary", "required", "review aid"),
        ("coverage_summary_visible", "observability_summary", "view/mesh/point completeness summary", "required", "Q_e audit"),
        ("review_relation_reliability", "review_field", "accept / reject / abstain", "blank_before_review", "primary human-audit label"),
        ("review_geometry_support", "review_field", "supports / contradicts / insufficient / ambiguous", "blank_before_review", "C_e/Q_e diagnostic"),
        ("review_observability", "review_field", "sufficient / limited / not_evaluable", "blank_before_review", "p_obs target source"),
        ("review_counter_relation", "review_field", "lying on / standing on / supported by / other / none / unknown", "blank_before_review", "prevents false binary negatives"),
        ("review_uncertainty_reason", "review_field", "occlusion / missing_mesh / ambiguous_pose / ontology_overlap / other", "blank_before_review", "Q_e/abstain reason"),
        ("review_notes", "review_field", "short free-text note", "blank_before_review", "audit trace"),
    ]
    return [
        {
            "field": field,
            "group": group,
            "description": description,
            "visibility": visibility,
            "use_policy": use_policy,
        }
        for field, group, description, visibility, use_policy in rows
    ]


def hidden_field_rows() -> list[dict[str, Any]]:
    rows = [
        ("source_score", "Z_e", "hidden during label fill; allowed only after labels are locked"),
        ("source_rank", "Z_e", "hidden during label fill; allowed only after labels are locked"),
        ("rank_band", "Z_e/control", "hidden construction/control field"),
        ("source_id", "Z_e/control", "hidden source provenance field"),
        ("queue_kind", "construction_proxy", "hidden because HL/LH imbalance can proxy target construction"),
        ("geometry_status", "construction_proxy", "hidden frozen RGA/helper status, not an audit label"),
        ("p_geom_valid", "construction_proxy", "hidden old geometry score, not the target"),
        ("label_match_status", "construction_proxy", "hidden GT/source match status"),
        ("construction_bucket", "construction_proxy", "hidden sampling stratum"),
        ("hidden_stratum", "construction_proxy", "hidden shortcut-control stratum"),
    ]
    return [{"field": field, "factor_group": group, "policy": policy} for field, group, policy in rows]


def label_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "review_label": "accept",
            "definition": "Visible mesh/point/multiview evidence supports the candidate predicate for the shown subject-object pair.",
            "allowed_basis": "contact/support surface, pose compatibility, relative placement, visible attachment/support context",
            "forbidden_basis": "high source score, high rank, no-GT absence, queue kind, old geometry_status",
            "maps_to": "p_obs=1, p_rel=1",
        },
        {
            "review_label": "reject",
            "definition": "Visible evidence contradicts the candidate predicate or clearly supports a different relation.",
            "allowed_basis": "no contact where contact is required, wrong pose for lying/standing, unsupported object, better counter relation",
            "forbidden_basis": "predicate is uncommon, source score is low, GT is missing",
            "maps_to": "p_obs=1, p_rel=0",
        },
        {
            "review_label": "abstain",
            "definition": "Evidence is insufficient or ontology is ambiguous enough that accept/reject would be speculative.",
            "allowed_basis": "missing/low-quality mesh, occlusion, incomplete point evidence, ambiguous broad supported-by overlap",
            "forbidden_basis": "using abstain to avoid hard negatives after looking at source score",
            "maps_to": "p_obs=0; excluded from p_rel binary but retained for Q_e",
        },
        {
            "review_label": "counter_relation",
            "definition": "If the candidate predicate is wrong but another support/contact predicate is visually better, record it.",
            "allowed_basis": "standing-like pose, lying-like pose, generic support without specific pose",
            "forbidden_basis": "turning supported by into a universal negative against standing on",
            "maps_to": "diagnostic C_e alternative-label target",
        },
    ]


def target_axis_rows() -> list[dict[str, Any]]:
    return [
        {
            "axis": "C_e_compatibility_binary",
            "positive": "accept with p_obs=1",
            "negative": "reject with p_obs=1",
            "excluded": "abstain; unsupported no-GT rows without visual/mesh contradiction",
            "claim_role": "tests predicate-geometry compatibility independent of source score",
        },
        {
            "axis": "Q_e_evidence_quality",
            "positive": "sufficient observability and coherent evidence",
            "negative": "limited or not evaluable evidence",
            "excluded": "none; this is an evidence-quality target, not relation truth",
            "claim_role": "separates observability from relation reliability",
        },
        {
            "axis": "p_obs_selective_decision",
            "positive": "sufficient evidence to judge accept/reject",
            "negative": "abstain/not evaluable",
            "excluded": "none after label lock",
            "claim_role": "decides when the system should abstain",
        },
        {
            "axis": "p_rel_given_observed",
            "positive": "accept among p_obs=1 rows",
            "negative": "reject among p_obs=1 rows",
            "excluded": "abstain rows",
            "claim_role": "relation reliability conditional on enough evidence",
        },
        {
            "axis": "counter_relation_diagnostic",
            "positive": "reviewer supplies a better support/contact relation",
            "negative": "none/unknown",
            "excluded": "not used as primary binary target",
            "claim_role": "prevents ontology-overlap errors, especially for supported by",
        },
    ]


def sampling_plan_rows() -> list[dict[str, Any]]:
    rows = [
        ("lying_on_clear_accept", "lying on", 60, "visible lying/resting pose with support evidence", "positive anchor"),
        ("lying_on_hard_reject_standing_like", "lying on", 40, "same family/class-like rows where upright/standing relation is better", "hard negative"),
        ("lying_on_abstain_or_ambiguous", "lying on", 20, "low coverage or ambiguous pose", "Q_e/abstain"),
        ("standing_on_clear_accept", "standing on", 60, "upright object supported by another object/surface", "positive anchor"),
        ("standing_on_hard_reject_lying_like", "standing on", 40, "lying/resting pose or unsupported contact", "hard negative"),
        ("standing_on_abstain_or_ambiguous", "standing on", 20, "low coverage or ambiguous support", "Q_e/abstain"),
        ("supported_by_clear_accept", "supported by", 60, "generic support visible but not necessarily pose-specific", "positive anchor"),
        ("supported_by_hard_reject_no_support", "supported by", 40, "near or co-visible pair without support/contact evidence", "hard negative"),
        ("supported_by_abstain_or_ontology_overlap", "supported by", 20, "specific predicate may be better or evidence insufficient", "Q_e/abstain"),
        ("cross_predicate_control", "mixed", 50, "same-scene/class/rank/coverage matched counter examples", "shortcut control"),
        ("coverage_stress_control", "mixed", 35, "limited mesh/multiview/point visibility rows", "p_obs/Q_e control"),
        ("hard_surface_cap_control", "mixed", 35, "floor/wall/ceiling capped and paired with non-hard-surface examples", "class shortcut control"),
    ]
    return [
        {
            "stratum": stratum,
            "predicate": predicate,
            "target_rows": target_rows,
            "selection_intent": intent,
            "target_role": role,
        }
        for stratum, predicate, target_rows, intent, role in rows
    ]


def shortcut_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "phase": "pre_materialization",
            "gate": "train_only_source",
            "threshold": "validation_usage=false and test_usage=false",
            "reason": "hypothesis target construction must not inspect held-out rows",
        },
        {
            "phase": "pre_materialization",
            "gate": "predicate_min_rows",
            "threshold": f">= {MIN_PER_PREDICATE} planned candidates per predicate",
            "reason": "avoid one-predicate-only target",
        },
        {
            "phase": "pre_materialization",
            "gate": "scan_cap",
            "threshold": "max scan share <= 0.05 preferred",
            "reason": "avoid scene identity shortcut",
        },
        {
            "phase": "pre_materialization",
            "gate": "subject_object_class_pair_cap",
            "threshold": "max class-pair share <= 0.10 preferred",
            "reason": "avoid class-pair shortcut",
        },
        {
            "phase": "pre_materialization",
            "gate": "hard_surface_cap",
            "threshold": "floor/wall/ceiling/room rows <= 0.60 preferred",
            "reason": "support/contact has strong hard-surface priors",
        },
        {
            "phase": "label_lock",
            "gate": "source_hidden",
            "threshold": "source_score/rank/queue_kind/p_geom_valid absent from visible packets",
            "reason": "labels must be independent from source confidence and old construction proxy",
        },
        {
            "phase": "post_label",
            "gate": "binary_class_mass",
            "threshold": f"accept >= {MIN_BINARY_ACCEPT}, reject >= {MIN_BINARY_REJECT}, abstain >= {MIN_ABSTAIN}",
            "reason": "p_rel and p_obs targets need usable class mass",
        },
        {
            "phase": "post_label",
            "gate": "shortcut_probe",
            "threshold": "predicate/class/source-only probes below predeclared threshold before learned smoke",
            "reason": "otherwise C_e/Q_e gains can be shortcut artifacts",
        },
        {
            "phase": "post_label",
            "gate": "same_family_hard_contrast",
            "threshold": "positive and negative rows exist within predicate or class-pair controlled slices",
            "reason": "tests compatibility rather than merely predicate identity",
        },
    ]


def feature_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "factor": "T_e",
            "allowed_inputs": "predicate text/label, subject/object class text, relation family",
            "excluded_inputs": "source score, source rank, old p_geom_valid",
            "role": "semantic query for compatibility",
        },
        {
            "factor": "Z_e",
            "allowed_inputs": "source score, rank, source id after labels are locked",
            "excluded_inputs": "review labels, hidden construction label fields",
            "role": "source confidence baseline and ablation, not C_e input",
        },
        {
            "factor": "G_e",
            "allowed_inputs": "predicate-independent mesh/point/contact/pose features",
            "excluded_inputs": "predicate-conditioned frozen labels, source score/rank",
            "role": "geometry evidence representation",
        },
        {
            "factor": "C_e",
            "allowed_inputs": "compatibility(T_e, G_e)",
            "excluded_inputs": "Z_e during contrastive compatibility learning",
            "role": "semantic-geometry compatibility",
        },
        {
            "factor": "Q_e",
            "allowed_inputs": "mesh availability, point coverage, multiview visibility, evidence agreement, missing tokens",
            "excluded_inputs": "relation accept/reject truth as a direct input",
            "role": "observability/evidence-quality factor",
        },
        {
            "factor": "p_obs",
            "allowed_inputs": "Q_e plus safe evidence availability features",
            "excluded_inputs": "source score shortcut as a decision proxy",
            "role": "decide whether to abstain",
        },
        {
            "factor": "p_rel",
            "allowed_inputs": "T_e, G_e, C_e, optional Z_e in posterior after C_e is learned independently",
            "excluded_inputs": "abstain rows as false negatives",
            "role": "reliability conditional on enough evidence",
        },
    ]


def reviewer_risk_rows() -> list[dict[str, Any]]:
    return [
        {
            "risk": "audit_labels_copy_visible_text",
            "severity": "high",
            "mitigation": "post-label predicate/class-only shortcut probes and class-pair controlled slices",
        },
        {
            "risk": "supported_by_superordinate_overlap",
            "severity": "high",
            "mitigation": "record counter_relation and do not use supported by as clean binary negative against standing on",
        },
        {
            "risk": "visual_mesh_packet_leaks_source_score",
            "severity": "critical",
            "mitigation": "visible schema explicitly excludes source_score, rank, queue_kind, geometry_status, p_geom_valid",
        },
        {
            "risk": "hard_surface_shortcut",
            "severity": "high",
            "mitigation": "cap floor/wall/ceiling/room pairs and require non-hard-surface contrasts",
        },
        {
            "risk": "positive_anchor_only_bias",
            "severity": "high",
            "mitigation": "mine positive anchors with matched hard rejects and abstain/coverage controls",
        },
        {
            "risk": "multiview_becomes_deployable_input_too_early",
            "severity": "medium",
            "mitigation": "use multiview as audit/confirmation evidence first; model input promotion requires separate gate",
        },
    ]


def build_contract(
    decision_summary: dict[str, Any],
    source_summary: dict[str, Any],
    feature_summary: dict[str, Any],
    review_summary: dict[str, Any],
) -> dict[str, Any]:
    join_summary = source_summary.get("join_summary", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "selected_route": EXPECTED_ROUTE,
        "selected_path": SELECTED_PATH,
        "selected_predicates": SELECTED_PREDICATES,
        "target_total_rows": TARGET_TOTAL_ROWS,
        "minimum_total_rows": MIN_TOTAL_ROWS,
        "minimum_per_predicate": MIN_PER_PREDICATE,
        "label_source": "visible visual/mesh/human audit evidence, not source score or old construction proxy",
        "primary_target": "p_rel given p_obs=1 over accept/reject labels",
        "observability_target": "p_obs and Q_e from sufficient/limited/not_evaluable evidence",
        "compatibility_target": "C_e from predicate semantics T_e and predicate-independent geometry G_e",
        "no_gt_policy": "No-GT is never a negative label by itself.",
        "supported_by_policy": (
            "supported by is treated as a broad/superordinate support predicate; it can be accept, reject, "
            "or counter_relation, but it is not automatically a clean negative for standing on."
        ),
        "source_capacity": {
            "support_rows": join_summary.get("rows"),
            "predicate_counts": join_summary.get("predicate_counts"),
            "distinct_scans": join_summary.get("distinct_scans"),
            "distinct_directed_pairs": join_summary.get("distinct_directed_pairs"),
            "scan_asset_complete_rate": join_summary.get("scan_asset_complete_rate"),
            "mesh_contact_surface_possible_rate": join_summary.get("mesh_contact_surface_possible_rate"),
            "sequence_multiview_possible_rate": join_summary.get("sequence_multiview_possible_rate"),
        },
        "prior_artifact_status": {
            "decision_status": decision_summary.get("status"),
            "source_inventory_status": source_summary.get("status"),
            "feature_probe_status": feature_summary.get("status"),
            "feature_review_status": review_summary.get("status"),
            "feature_review_selected_path": review_summary.get("selected_path"),
        },
        "next_todo": NEXT_TODO,
    }


def build_runner_contract(output_dir: Path) -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "next_script_expected": "tools/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory.py",
        "input_contract": {
            "source_rows": "train-only support/contact candidate rows from Open3DSG train-side artifacts",
            "assets": "3RScan mesh, semseg, aligned point/mesh crops, sequence/multiview evidence where available",
            "hidden_fields": [row["field"] for row in hidden_field_rows()],
            "visible_fields": [row["field"] for row in visible_packet_schema_rows()],
        },
        "expected_outputs": {
            "candidate_inventory": "pre-label candidate source inventory with class/scan/predicate caps",
            "packet_manifest": "packet manifest with visible paths and hidden metadata split",
            "label_sheet_template": "blank visible-only audit sheet",
            "source_balance_report": "pre-materialization shortcut and coverage diagnostics",
        },
        "stop_conditions": [
            "visible packet requires any hidden field",
            "target cannot reach minimum predicate capacity",
            "class-pair or hard-surface dominance cannot be controlled",
            "validation/test rows are needed to satisfy count",
        ],
        "plan_artifact_root": rel_path(output_dir),
    }


def build_report(summary: dict[str, Any], contract: dict[str, Any]) -> str:
    lines = [
        "# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Target Plan",
        "",
        "## Result",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Scope",
        "",
        "This step plans an independent support/contact audit target. It does not materialize rows, fill labels, run a learned smoke, or use validation/test rows.",
        "",
        "Selected predicates:",
        "",
        "```text",
        "\n".join(contract["selected_predicates"]),
        "```",
        "",
        "The target source is visual/mesh audit evidence. `source_score`, `rank`, `queue_kind`, old `geometry_status`, and old `p_geom_valid` are hidden during label creation.",
        "",
        "## Target Contract",
        "",
        "- `C_e`: predicate-geometry compatibility from `T_e` and predicate-independent `G_e`.",
        "- `Q_e`: evidence quality / observability from mesh, point, and multiview availability.",
        "- `p_obs`: whether accept/reject can be judged from current evidence.",
        "- `p_rel`: accept vs reject only after `p_obs = 1`.",
        "",
        "`No-GT` is not a negative label. `supported by` is treated as a broad support predicate, so it is not a clean negative for `standing on` unless visual/mesh evidence contradicts support.",
        "",
        "## Planned Size",
        "",
        "```text",
        f"target_total_rows = {TARGET_TOTAL_ROWS}",
        f"minimum_total_rows = {MIN_TOTAL_ROWS}",
        f"minimum_per_predicate = {MIN_PER_PREDICATE}",
        f"minimum_accept = {MIN_BINARY_ACCEPT}",
        f"minimum_reject = {MIN_BINARY_REJECT}",
        f"minimum_abstain = {MIN_ABSTAIN}",
        "```",
        "",
        "## Source Capacity",
        "",
        "```json",
        json.dumps(contract["source_capacity"], ensure_ascii=False, indent=2, sort_keys=True),
        "```",
        "",
        "## Next Step",
        "",
        f"Run `{NEXT_TODO}` to inventory candidate rows and build the packet/label-sheet contract under this schema.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    input_errors: list[dict[str, Any]] = []
    decision_summary = load_required(args.decision_dir / "summary.json", input_errors, "decision_summary")
    target_contract = load_required(args.decision_dir / "target_source_contract.json", input_errors, "target_source_contract")
    source_summary = load_required(args.source_inventory_dir / "summary.json", input_errors, "source_inventory_summary")
    feature_summary = load_required(args.feature_runner_dir / "summary.json", input_errors, "feature_probe_summary")
    review_summary = load_required(args.feature_review_dir / "summary.json", input_errors, "feature_review_summary")

    existing_error_rows = {
        "decision_validation_errors": read_jsonl(args.decision_dir / "validation_errors.jsonl"),
        "source_inventory_validation_errors": read_jsonl(args.source_inventory_dir / "validation_errors.jsonl"),
        "feature_probe_validation_errors": read_jsonl(args.feature_runner_dir / "validation_errors.jsonl"),
        "feature_review_validation_errors": read_jsonl(args.feature_review_dir / "validation_errors.jsonl"),
    }

    validation_errors = input_errors + validate_inputs(
        decision_summary,
        target_contract,
        source_summary,
        feature_summary,
        review_summary,
        existing_error_rows,
    )

    status = STATUS_READY if not validation_errors else STATUS_ERROR
    contract = build_contract(decision_summary, source_summary, feature_summary, review_summary)
    runner_contract = build_runner_contract(output_dir)

    output_paths = {
        "audit_target_contract": output_dir / "audit_target_contract.json",
        "feature_boundary": output_dir / "feature_boundary.csv",
        "hidden_field_policy": output_dir / "hidden_field_policy.csv",
        "label_policy": output_dir / "label_policy.csv",
        "report": output_dir / "report.md",
        "reviewer_risks": output_dir / "reviewer_risks.csv",
        "runner_contract": output_dir / "runner_contract.json",
        "sampling_plan": output_dir / "sampling_plan.csv",
        "shortcut_gate_plan": output_dir / "shortcut_gate_plan.csv",
        "summary": output_dir / "summary.json",
        "target_axes": output_dir / "target_axes.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "visible_packet_schema": output_dir / "visible_packet_schema.csv",
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO if not validation_errors else "repair_support_contact_visual_mesh_audit_plan_inputs",
        "validation_errors": len(validation_errors),
        "selected_predicates": SELECTED_PREDICATES,
        "target_total_rows": TARGET_TOTAL_ROWS,
        "minimum_total_rows": MIN_TOTAL_ROWS,
        "minimum_per_predicate": MIN_PER_PREDICATE,
        "minimum_binary_accept": MIN_BINARY_ACCEPT,
        "minimum_binary_reject": MIN_BINARY_REJECT,
        "minimum_abstain": MIN_ABSTAIN,
        "contract_summary": {
            "label_source": contract["label_source"],
            "primary_target": contract["primary_target"],
            "observability_target": contract["observability_target"],
            "compatibility_target": contract["compatibility_target"],
            "no_gt_policy": contract["no_gt_policy"],
            "supported_by_policy": contract["supported_by_policy"],
        },
        "source_capacity": contract["source_capacity"],
        "boundary": {
            "split": "train full only",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_candidate_rows": False,
            "fills_labels": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
    }

    write_json(output_paths["audit_target_contract"], contract)
    write_json(output_paths["runner_contract"], runner_contract)
    write_csv(output_paths["visible_packet_schema"], visible_packet_schema_rows())
    write_csv(output_paths["hidden_field_policy"], hidden_field_rows())
    write_csv(output_paths["label_policy"], label_policy_rows())
    write_csv(output_paths["target_axes"], target_axis_rows())
    write_csv(output_paths["sampling_plan"], sampling_plan_rows())
    write_csv(output_paths["shortcut_gate_plan"], shortcut_gate_rows())
    write_csv(output_paths["feature_boundary"], feature_boundary_rows())
    write_csv(output_paths["reviewer_risks"], reviewer_risk_rows())
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary, contract), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
