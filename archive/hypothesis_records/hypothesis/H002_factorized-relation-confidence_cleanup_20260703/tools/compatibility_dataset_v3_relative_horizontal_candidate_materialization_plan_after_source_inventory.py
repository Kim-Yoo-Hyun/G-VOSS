#!/usr/bin/env python3
"""Write the H002 relative-horizontal candidate materialization plan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INVENTORY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory"
)

EXPECTED_INVENTORY_STATUS = "h002_compatibility_dataset_v3_relative_horizontal_source_inventory_after_reference_frame_protocol_plan_ready"
EXPECTED_INVENTORY_NEXT = "compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory_v1"
STATUS_READY = "h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_relative_horizontal_candidate_materialization_plan_after_source_inventory_input_errors"
SELECTED_PATH = "materialize_relative_horizontal_same_g_predicate_flip_rows_with_frame_qe_controls"
NEXT_TODO = "compatibility_dataset_v3_relative_horizontal_candidate_materialization_after_plan"

AXIS_PAIRS = ("left_right", "front_behind")
PRIMARY_GROUPS_PER_AXIS_PAIR = 600
PRIMARY_ROWS_PER_AXIS_PAIR = PRIMARY_GROUPS_PER_AXIS_PAIR * 2
PRIMARY_GROUPS_TOTAL = PRIMARY_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS)
PRIMARY_ROWS_TOTAL = PRIMARY_GROUPS_TOTAL * 2
POSITIVE_ROWS_TOTAL = PRIMARY_GROUPS_TOTAL
NEGATIVE_ROWS_TOTAL = PRIMARY_GROUPS_TOTAL
PREDICATE_ROWS_PER_MAIN_PREDICATE = PRIMARY_GROUPS_PER_AXIS_PAIR

BOUNDARY_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR = 80
OPPOSING_FRAME_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR = 80
MAX_GROUPS_PER_SCAN = 24
MAX_GROUPS_PER_CLASS_PAIR = 160
MAX_GROUPS_PER_CLASS_PAIR_AXIS_PAIR = 80
MIN_ALIGNMENT_RATE = 0.70
MIN_COMPATIBLE_UNIQUE_PER_AXIS_PAIR = 1000


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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def to_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def validate_inputs(
    inventory_summary: dict[str, Any],
    inventory_errors: list[dict[str, Any]],
    predicate_rows: list[dict[str, str]],
    selected_axis_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if inventory_summary.get("status") != EXPECTED_INVENTORY_STATUS:
        errors.append({"error_type": "unexpected_inventory_status", "actual": inventory_summary.get("status")})
    if inventory_summary.get("next_todo") != EXPECTED_INVENTORY_NEXT:
        errors.append({"error_type": "unexpected_inventory_next", "actual": inventory_summary.get("next_todo")})
    if inventory_summary.get("validation_errors") != 0:
        errors.append(
            {"error_type": "inventory_validation_errors_present", "actual": inventory_summary.get("validation_errors")}
        )
    if inventory_errors:
        errors.append({"error_type": "inventory_validation_error_rows_present", "rows": len(inventory_errors)})
    boundary = inventory_summary.get("boundary", {})
    for key in [
        "h001_artifacts_modified",
        "materializes_rows",
        "paper_evidence_allowed",
        "runs_new_learned_smoke",
        "trains_new_model",
        "validation_usage",
        "test_usage",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "inventory_boundary_not_false", "key": key, "actual": boundary.get(key)})
    capacity = inventory_summary.get("capacity_summary", {})
    if capacity.get("ready_for_materialization_plan") is not True:
        errors.append({"error_type": "inventory_not_ready_for_materialization_plan"})
    if not predicate_rows:
        errors.append({"error_type": "missing_predicate_inventory"})
    if not selected_axis_rows:
        errors.append({"error_type": "missing_selected_axis_candidates"})

    predicate_map = {row.get("predicate_label"): row for row in predicate_rows}
    for predicate in ["left", "right", "front", "behind"]:
        row = predicate_map.get(predicate)
        if not row or row.get("status") != "observed":
            errors.append({"error_type": "missing_observed_main_predicate", "predicate": predicate})
    in_front = predicate_map.get("in front of")
    if not in_front or to_int(in_front.get("train_anchor_rows")) != 0:
        errors.append({"error_type": "in_front_of_should_be_zero_or_diagnostic", "actual": in_front})

    axis_map = {row.get("axis_pair"): row for row in selected_axis_rows}
    for axis_pair in AXIS_PAIRS:
        row = axis_map.get(axis_pair)
        if not row:
            errors.append({"error_type": "missing_axis_pair", "axis_pair": axis_pair})
            continue
        if to_float(row.get("alignment_rate")) < MIN_ALIGNMENT_RATE:
            errors.append(
                {
                    "error_type": "axis_alignment_too_low",
                    "axis_pair": axis_pair,
                    "actual": row.get("alignment_rate"),
                    "required": MIN_ALIGNMENT_RATE,
                }
            )
        if to_int(row.get("compatible_unique_directed_pair_predicate")) < MIN_COMPATIBLE_UNIQUE_PER_AXIS_PAIR:
            errors.append(
                {
                    "error_type": "axis_capacity_too_low",
                    "axis_pair": axis_pair,
                    "actual": row.get("compatible_unique_directed_pair_predicate"),
                    "required": MIN_COMPATIBLE_UNIQUE_PER_AXIS_PAIR,
                }
            )
    return errors


def row_quota_plan() -> list[dict[str, Any]]:
    return [
        {
            "component": "primary_left_right_same_g",
            "axis_pair": "left_right",
            "groups": PRIMARY_GROUPS_PER_AXIS_PAIR,
            "rows": PRIMARY_ROWS_PER_AXIS_PAIR,
            "positive_rows": PRIMARY_GROUPS_PER_AXIS_PAIR,
            "negative_rows": PRIMARY_GROUPS_PER_AXIS_PAIR,
            "predicate_rows": "left 600; right 600",
            "selection_rule": "compatible nonboundary scene_world_x anchors with left=negative/right=positive, expanded to same-G predicate flips",
            "model_use": "main C_e compatibility smoke after schema audit",
        },
        {
            "component": "primary_front_behind_same_g",
            "axis_pair": "front_behind",
            "groups": PRIMARY_GROUPS_PER_AXIS_PAIR,
            "rows": PRIMARY_ROWS_PER_AXIS_PAIR,
            "positive_rows": PRIMARY_GROUPS_PER_AXIS_PAIR,
            "negative_rows": PRIMARY_GROUPS_PER_AXIS_PAIR,
            "predicate_rows": "front 600; behind 600",
            "selection_rule": "compatible nonboundary scene_world_y anchors with front=negative/behind=positive, expanded to same-G predicate flips",
            "model_use": "main C_e compatibility smoke after schema audit",
        },
        {
            "component": "axis_boundary_qe_diagnostic",
            "axis_pair": "left_right; front_behind",
            "groups": BOUNDARY_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS),
            "rows": BOUNDARY_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS) * 2,
            "positive_rows": 0,
            "negative_rows": 0,
            "predicate_rows": "balanced within available boundary rows",
            "selection_rule": "abs signed offset below frozen boundary margin",
            "model_use": "Q_e/p_obs diagnostic only; excluded from binary C_e target",
        },
        {
            "component": "opposing_frame_diagnostic",
            "axis_pair": "left_right; front_behind",
            "groups": OPPOSING_FRAME_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS),
            "rows": OPPOSING_FRAME_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS) * 2,
            "positive_rows": 0,
            "negative_rows": 0,
            "predicate_rows": "balanced if available",
            "selection_rule": "GT predicate opposes selected world-axis sign",
            "model_use": "frame-disagreement/Q_e audit only; excluded from primary C_e binary target",
        },
        {
            "component": "in_front_of_alias_diagnostic",
            "axis_pair": "front_behind",
            "groups": 0,
            "rows": 0,
            "positive_rows": 0,
            "negative_rows": 0,
            "predicate_rows": "in front of 0",
            "selection_rule": "`in front of` not observed in current train/full sources",
            "model_use": "document exclusion; do not merge with `front`",
        },
    ]


def frame_selection_plan(selected_axis_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in selected_axis_rows:
        axis_pair = row["axis_pair"]
        if axis_pair == "left_right":
            predicate_sign_rule = "left=negative, right=positive"
            predicate_pair = "left/right"
        else:
            predicate_sign_rule = "front=negative, behind=positive"
            predicate_pair = "front/behind"
        rows.append(
            {
                "axis_pair": axis_pair,
                "predicate_pair": predicate_pair,
                "selected_frame": row["axis_candidate"],
                "predicate_sign_rule": predicate_sign_rule,
                "alignment_rate": row["alignment_rate"],
                "nonboundary_rows": row["nonboundary_rows"],
                "boundary_rows": row["boundary_rows"],
                "compatible_unique": row["compatible_unique_directed_pair_predicate"],
                "same_g_predicate_flip_rows_available": row["same_g_predicate_flip_rows"],
                "claim_boundary": "source-inventory candidate only; not paper evidence",
                "qe_requirement": row["required_qe_filter"],
            }
        )
    return rows


def target_construction_plan() -> list[dict[str, Any]]:
    return [
        {
            "target_component": "same_g_predicate_flip_primary",
            "definition": "for each selected anchor, create two rows with identical G_e_horizontal and opposite predicates",
            "allowed_for_main": True,
            "positive_rule": "predicate agrees with selected frame sign rule",
            "negative_rule": "opposite predicate on identical directed pair geometry",
            "grouping": "paired rows share one CV/group id",
        },
        {
            "target_component": "axis_boundary_qe",
            "definition": "rows with abs signed offset below boundary margin",
            "allowed_for_main": False,
            "positive_rule": "none",
            "negative_rule": "none",
            "grouping": "Q_e/p_obs diagnostic; do not force binary compatibility",
        },
        {
            "target_component": "opposing_frame_audit",
            "definition": "rows where GT predicate opposes selected world-frame sign",
            "allowed_for_main": False,
            "positive_rule": "none",
            "negative_rule": "none",
            "grouping": "frame-disagreement audit; inspect before any use",
        },
        {
            "target_component": "in_front_of_alias",
            "definition": "`in front of` alias route",
            "allowed_for_main": False,
            "positive_rule": "none",
            "negative_rule": "none",
            "grouping": "no observed source rows; keep diagnostic-only",
        },
    ]


def qe_policy() -> list[dict[str, Any]]:
    return [
        {
            "q_e_field": "axis_boundary_flag",
            "source": "abs selected signed offset < 0.10m",
            "decision_role": "p_obs / abstain",
            "not_relation_truth": True,
        },
        {
            "q_e_field": "frame_disagreement_flag",
            "source": "GT predicate opposes selected world-axis sign",
            "decision_role": "diagnostic or abstain until audited",
            "not_relation_truth": True,
        },
        {
            "q_e_field": "view_frame_available",
            "source": "sequence color/pose and multi_view assets",
            "decision_role": "future view-frame audit, not first C_e input",
            "not_relation_truth": True,
        },
        {
            "q_e_field": "in_front_of_unobserved",
            "source": "train/full source count is zero",
            "decision_role": "exclude from main materialization",
            "not_relation_truth": True,
        },
    ]


def feature_schema() -> list[dict[str, Any]]:
    return [
        {
            "block": "T_e",
            "field": "predicate_text",
            "allowed_main": True,
            "definition": "left/right/front/behind predicate text or one-hot",
            "notes": "The semantic query for compatibility with G_e_horizontal.",
        },
        {
            "block": "G_e_horizontal",
            "field": "delta_x_subject_minus_object",
            "allowed_main": True,
            "definition": "continuous x displacement in scene-aligned frame",
            "notes": "Predicate-independent; used for left/right route.",
        },
        {
            "block": "G_e_horizontal",
            "field": "delta_y_subject_minus_object",
            "allowed_main": True,
            "definition": "continuous y displacement in scene-aligned frame",
            "notes": "Predicate-independent; used for front/behind route.",
        },
        {
            "block": "G_e_horizontal",
            "field": "horizontal_distance",
            "allowed_main": True,
            "definition": "distance in xy plane",
            "notes": "Can expose proximity shortcut; report ablation.",
        },
        {
            "block": "Q_e_frame",
            "field": "abs_selected_axis_offset",
            "allowed_main": False,
            "definition": "signless selected-axis margin",
            "notes": "Q_e/p_obs diagnostic only, not relation truth.",
        },
        {
            "block": "Q_e_frame",
            "field": "frame_disagreement_flag",
            "allowed_main": False,
            "definition": "GT predicate opposes selected frame sign",
            "notes": "Hidden/audit or Q_e diagnostic only.",
        },
        {
            "block": "Z_e",
            "field": "source_score_or_rank",
            "allowed_main": False,
            "definition": "relation source confidence",
            "notes": "Not available/allowed in first C_e target construction.",
        },
    ]


def blocked_fields() -> list[dict[str, Any]]:
    fields = [
        ("gt_predicate_label", "target/source provenance"),
        ("source_predicate_label", "source provenance"),
        ("anchor_predicate_label", "construction provenance"),
        ("compatibility_label", "label field"),
        ("p_rel_label", "label field"),
        ("p_obs_label", "label field"),
        ("selected_frame_compatible", "label proxy"),
        ("axis_pair_label", "construction routing field; use only for stratification"),
        ("axis_bucket_x", "discretized signed rule proxy"),
        ("axis_bucket_y", "discretized signed rule proxy"),
        ("candidate_component", "construction provenance"),
        ("is_original_gt_anchor", "construction/source provenance"),
        ("same_g_group_id", "group identity leakage"),
        ("subgraph_anchor_key", "row identity leakage"),
        ("directed_pair_predicate_key", "row identity leakage"),
        ("scan_id", "scan leakage; CV grouping only"),
        ("subject_id", "instance leakage"),
        ("object_id", "instance leakage"),
        ("subject_class_label", "blocked from first main view; class ablation only"),
        ("object_class_label", "blocked from first main view; class ablation only"),
        ("class_pair", "hidden shortcut audit only"),
        ("in_front_of_alias_flag", "source/ontology diagnostic"),
    ]
    return [{"field": field, "blocked_from": "model_safe_main_view", "reason": reason} for field, reason in fields]


def control_plan() -> list[dict[str, Any]]:
    return [
        {
            "control_id": "H0_schema_leakage",
            "purpose": "ensure target/source/construction fields are absent from model-safe rows",
            "pass_condition": "0 blocked-field hits",
        },
        {
            "control_id": "H1_geometry_only",
            "purpose": "G_e_horizontal alone should not solve same-G predicate-flip labels",
            "pass_condition": "AUROC <= 0.60 overall and per axis-pair",
        },
        {
            "control_id": "H2_semantic_only",
            "purpose": "predicate text alone should not solve labels",
            "pass_condition": "AUROC <= 0.60",
        },
        {
            "control_id": "H3_TG_interaction",
            "purpose": "main C_e compatibility route",
            "pass_condition": "AUROC >= 0.85 and improves over T-only/G-only",
        },
        {
            "control_id": "H4_wrong_T",
            "purpose": "swap predicate query while keeping G_e_horizontal fixed",
            "pass_condition": "score collapses or inverts relative to H3",
        },
        {
            "control_id": "H5_axis_sign_flip",
            "purpose": "flip selected signed axis while keeping T_e fixed",
            "pass_condition": "score collapses or inverts",
        },
        {
            "control_id": "H6_wrong_frame_rotation",
            "purpose": "swap x/y or reverse selected frame axis",
            "pass_condition": "performance degrades, showing frame-specific evidence is used",
        },
        {
            "control_id": "H7_subject_object_swap",
            "purpose": "swap endpoints and verify directional relation consistency",
            "pass_condition": "score changes consistently or degrades",
        },
        {
            "control_id": "H8_class_pair_hidden_probe",
            "purpose": "audit class-pair shortcut outside model-safe view",
            "pass_condition": "AUROC/majority <= 0.60",
        },
        {
            "control_id": "H9_qe_exclusion",
            "purpose": "axis-boundary and frame-disagreement rows are excluded from primary binary C_e",
            "pass_condition": "0 diagnostic rows in primary binary target",
        },
    ]


def output_manifest_plan() -> list[dict[str, Any]]:
    return [
        {"file": "candidate_rows.jsonl", "role": "all train-only materialized rows with labels/provenance", "model_safe": False},
        {"file": "model_safe_main_view.jsonl", "role": "T_e + continuous G_e_horizontal primary rows", "model_safe": True},
        {"file": "model_safe_qe_view.jsonl", "role": "Q_e frame/axis-boundary diagnostic view", "model_safe": True},
        {"file": "hidden_manifest.jsonl", "role": "source/construction/frame/class-pair provenance for audit", "model_safe": False},
        {"file": "group_manifest.jsonl", "role": "same-G predicate flip group integrity", "model_safe": False},
        {"file": "schema_precheck.json", "role": "counts, caps, blocked-field audit, and row-balance precheck", "model_safe": False},
    ]


def materialization_contract(selected_axis_rows: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "dataset_id": "h002_relative_horizontal_same_g_predicate_flip_v1",
        "source_artifact": rel_path(DEFAULT_INVENTORY_DIR),
        "next_runner": NEXT_TODO,
        "primary_design": {
            "groups": PRIMARY_GROUPS_TOTAL,
            "rows": PRIMARY_ROWS_TOTAL,
            "group_definition": "same scan, subject, object, directed pair, and identical G_e_horizontal; two rows differ only by predicate T_e",
            "axis_pairs": {
                "left_right": {
                    "predicates": ["left", "right"],
                    "selected_frame": "scene_world_x",
                    "sign_rule": "left=negative, right=positive",
                    "groups": PRIMARY_GROUPS_PER_AXIS_PAIR,
                    "rows": PRIMARY_ROWS_PER_AXIS_PAIR,
                },
                "front_behind": {
                    "predicates": ["front", "behind"],
                    "selected_frame": "scene_world_y",
                    "sign_rule": "front=negative, behind=positive",
                    "groups": PRIMARY_GROUPS_PER_AXIS_PAIR,
                    "rows": PRIMARY_ROWS_PER_AXIS_PAIR,
                },
            },
            "positive_rule": "predicate agrees with selected frame sign rule",
            "negative_rule": "opposite predicate on identical directed pair geometry",
        },
        "quota": {
            "primary_groups": PRIMARY_GROUPS_TOTAL,
            "primary_rows": PRIMARY_ROWS_TOTAL,
            "positive_rows": POSITIVE_ROWS_TOTAL,
            "negative_rows": NEGATIVE_ROWS_TOTAL,
            "left_rows": PREDICATE_ROWS_PER_MAIN_PREDICATE,
            "right_rows": PREDICATE_ROWS_PER_MAIN_PREDICATE,
            "front_rows": PREDICATE_ROWS_PER_MAIN_PREDICATE,
            "behind_rows": PREDICATE_ROWS_PER_MAIN_PREDICATE,
            "in_front_of_rows": 0,
        },
        "caps": {
            "max_groups_per_scan": MAX_GROUPS_PER_SCAN,
            "max_groups_per_class_pair": MAX_GROUPS_PER_CLASS_PAIR,
            "max_groups_per_class_pair_axis_pair": MAX_GROUPS_PER_CLASS_PAIR_AXIS_PAIR,
        },
        "diagnostics": {
            "axis_boundary_groups": BOUNDARY_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS),
            "axis_boundary_rows": BOUNDARY_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS) * 2,
            "opposing_frame_groups": OPPOSING_FRAME_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS),
            "opposing_frame_rows": OPPOSING_FRAME_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS) * 2,
            "in_front_of_policy": "diagnostic_only_zero_source_rows",
        },
        "source_inventory_selected_axes": selected_axis_rows,
        "model_safe_view": {
            "main_allowed_blocks": ["T_e.predicate_text", "G_e_horizontal.continuous_signed_offsets"],
            "blocked_blocks": ["Z_e", "source/GT provenance", "construction fields", "discretized direction labels"],
            "qe_blocks": ["Q_e_frame.axis_boundary", "Q_e_frame.frame_disagreement"],
        },
    }


def next_runner_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Materialize train-only relative-horizontal same-G predicate-flip rows under the frozen frame/Q_e contract.",
        "must_create": [
            "2400 primary rows from 1200 same-G groups",
            "600 left/right groups and 600 front/behind groups",
            "balanced positive/negative compatibility labels",
            "diagnostic axis-boundary and opposing-frame rows outside the primary binary target",
            "hidden manifest with source/frame/class-pair provenance",
            "model-safe main view with no blocked fields",
        ],
        "must_not_do": [
            "do not include `in front of` in primary binary rows",
            "do not use validation/test",
            "do not train a learned model",
            "do not expose selected_frame_compatible, axis buckets, construction flags, scan id, or endpoint ids in model-safe rows",
            "do not force frame-disagreement/opposing rows into primary accept/reject labels",
        ],
    }


def build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# Relative-Horizontal Candidate Materialization Plan After Source Inventory",
        "",
        "## Result",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Frozen Plan",
        "",
        "```text",
        f"primary_groups = {PRIMARY_GROUPS_TOTAL}",
        f"primary_rows = {PRIMARY_ROWS_TOTAL}",
        f"positive_rows = {POSITIVE_ROWS_TOTAL}",
        f"negative_rows = {NEGATIVE_ROWS_TOTAL}",
        "left/right groups = 600",
        "front/behind groups = 600",
        "in front of rows = 0",
        "```",
        "",
        "## Interpretation",
        "",
        "`relative_horizontal` has enough source capacity, but frame alignment is not clean enough",
        "to treat world-frame labels as unquestioned ground truth. The materialization must keep",
        "axis-boundary and frame-disagreement rows outside the primary binary target and route them",
        "through `Q_e` or diagnostics.",
        "",
        "## Boundary",
        "",
        "- No rows were materialized in this stage.",
        "- No learned smoke or training was run.",
        "- No validation/test source was used.",
        "- H001 artifacts were not modified.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    inventory_summary_path = args.inventory_dir / "summary.json"
    inventory_summary = read_json(inventory_summary_path) if inventory_summary_path.exists() else {}
    inventory_errors = read_jsonl(args.inventory_dir / "validation_errors.jsonl")
    predicate_rows = read_csv(args.inventory_dir / "predicate_inventory.csv")
    selected_axis_rows = read_csv(args.inventory_dir / "selected_axis_candidates.csv")
    validation_errors = validate_inputs(inventory_summary, inventory_errors, predicate_rows, selected_axis_rows)

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    selected_path = None if validation_errors else SELECTED_PATH
    next_todo = None if validation_errors else NEXT_TODO

    output_paths = {
        "summary": args.output_dir / "summary.json",
        "materialization_contract": args.output_dir / "materialization_contract.json",
        "row_quota_plan": args.output_dir / "row_quota_plan.csv",
        "frame_selection_plan": args.output_dir / "frame_selection_plan.csv",
        "target_construction_plan": args.output_dir / "target_construction_plan.csv",
        "qe_policy": args.output_dir / "qe_policy.csv",
        "feature_schema": args.output_dir / "feature_schema.csv",
        "blocked_fields": args.output_dir / "blocked_fields.csv",
        "control_plan": args.output_dir / "control_plan.csv",
        "output_manifest_plan": args.output_dir / "output_manifest_plan.csv",
        "next_runner_contract": args.output_dir / "next_runner_contract.json",
        "report": args.output_dir / "report.md",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }

    quota_rows = row_quota_plan()
    frame_rows = frame_selection_plan(selected_axis_rows)
    target_rows = target_construction_plan()
    qe_rows = qe_policy()
    feature_rows = feature_schema()
    blocked_rows = blocked_fields()
    control_rows = control_plan()
    manifest_rows = output_manifest_plan()
    contract = materialization_contract(selected_axis_rows)
    next_contract = next_runner_contract()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "inventory_dir": rel_path(args.inventory_dir),
            "inventory_summary": rel_path(inventory_summary_path),
            "selected_axis_candidates": rel_path(args.inventory_dir / "selected_axis_candidates.csv"),
            "predicate_inventory": rel_path(args.inventory_dir / "predicate_inventory.csv"),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "plan_counts": {
            "primary_groups": PRIMARY_GROUPS_TOTAL,
            "primary_rows": PRIMARY_ROWS_TOTAL,
            "primary_positive_rows": POSITIVE_ROWS_TOTAL,
            "primary_negative_rows": NEGATIVE_ROWS_TOTAL,
            "left_right_groups": PRIMARY_GROUPS_PER_AXIS_PAIR,
            "front_behind_groups": PRIMARY_GROUPS_PER_AXIS_PAIR,
            "predicate_rows_each": PREDICATE_ROWS_PER_MAIN_PREDICATE,
            "axis_boundary_diagnostic_groups": BOUNDARY_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS),
            "axis_boundary_diagnostic_rows": BOUNDARY_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS) * 2,
            "opposing_frame_diagnostic_groups": OPPOSING_FRAME_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS),
            "opposing_frame_diagnostic_rows": OPPOSING_FRAME_DIAGNOSTIC_GROUPS_PER_AXIS_PAIR * len(AXIS_PAIRS) * 2,
            "in_front_of_rows": 0,
        },
        "caps": {
            "max_groups_per_scan": MAX_GROUPS_PER_SCAN,
            "max_groups_per_class_pair": MAX_GROUPS_PER_CLASS_PAIR,
            "max_groups_per_class_pair_axis_pair": MAX_GROUPS_PER_CLASS_PAIR_AXIS_PAIR,
        },
        "selected_axes": frame_rows,
        "input_capacity_summary": inventory_summary.get("capacity_summary", {}),
        "boundary": {
            "split": "train_only_materialization_plan",
            "materializes_rows": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "claim_boundary": {
            "rows_materialized_now": False,
            "learned_smoke_allowed_now": False,
            "paper_evidence_allowed_now": False,
            "relative_horizontal_solved": False,
            "frame_alignment_claim_allowed": False,
        },
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["materialization_contract"], contract)
    write_csv(output_paths["row_quota_plan"], quota_rows)
    write_csv(output_paths["frame_selection_plan"], frame_rows)
    write_csv(output_paths["target_construction_plan"], target_rows)
    write_csv(output_paths["qe_policy"], qe_rows)
    write_csv(output_paths["feature_schema"], feature_rows)
    write_csv(output_paths["blocked_fields"], blocked_rows)
    write_csv(output_paths["control_plan"], control_rows)
    write_csv(output_paths["output_manifest_plan"], manifest_rows)
    write_json(output_paths["next_runner_contract"], next_contract)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
