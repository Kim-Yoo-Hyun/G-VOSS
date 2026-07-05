#!/usr/bin/env python3
"""Write the H002 size-relative candidate materialization plan."""

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
    H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory"
)

EXPECTED_INVENTORY_STATUS = "h002_compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan_ready"
EXPECTED_INVENTORY_NEXT = "compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory_v1"
STATUS_READY = "h002_compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory_ready"
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_size_relative_candidate_materialization_plan_after_source_inventory_input_errors"
)
SELECTED_PATH = "materialize_size_relative_same_g_predicate_flip_rows"
NEXT_TODO = "compatibility_dataset_v3_size_relative_candidate_materialization_after_plan"

PRIMARY_GROUPS_TOTAL = 1200
PRIMARY_GROUPS_PER_DIRECTION = 600
PRIMARY_ROWS_TOTAL = PRIMARY_GROUPS_TOTAL * 2
AMBIGUOUS_GROUPS_AVAILABLE = 50
OPPOSING_GROUPS_AVAILABLE = 36
CLASS_PAIR_GROUP_CAP = 240
CLASS_PAIR_DIRECTION_CAP = 120
SCAN_GROUP_CAP = 24
MIN_STRICT_GROUPS_REQUIRED = 1200
MIN_STRICT_PER_DIRECTION_REQUIRED = 600


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


def to_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def validate_inputs(
    inventory_summary: dict[str, Any],
    inventory_errors: list[dict[str, Any]],
    predicate_rows: list[dict[str, str]],
    class_pair_rows: list[dict[str, str]],
    margin_rows: list[dict[str, str]],
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
    capacity = inventory_summary.get("capacity", {})
    if capacity.get("ready_for_materialization_plan") is not True:
        errors.append({"error_type": "inventory_not_ready_for_materialization_plan"})
    if to_int(capacity.get("strict_compatible_unique_flip_groups")) < MIN_STRICT_GROUPS_REQUIRED:
        errors.append(
            {
                "error_type": "strict_group_capacity_too_small",
                "actual": capacity.get("strict_compatible_unique_flip_groups"),
                "required": MIN_STRICT_GROUPS_REQUIRED,
            }
        )
    by_predicate = capacity.get("strict_compatible_unique_by_predicate", {})
    for predicate in ["bigger than", "smaller than"]:
        if to_int(by_predicate.get(predicate)) < MIN_STRICT_PER_DIRECTION_REQUIRED:
            errors.append(
                {
                    "error_type": "strict_direction_capacity_too_small",
                    "predicate": predicate,
                    "actual": by_predicate.get(predicate),
                    "required": MIN_STRICT_PER_DIRECTION_REQUIRED,
                }
            )
    if not predicate_rows:
        errors.append({"error_type": "missing_predicate_anchor_inventory"})
    if not class_pair_rows:
        errors.append({"error_type": "missing_class_pair_inventory"})
    if not margin_rows:
        errors.append({"error_type": "missing_size_margin_inventory"})
    return errors


def row_quota_plan() -> list[dict[str, Any]]:
    return [
        {
            "component": "primary_same_g_compatibility",
            "split_role": "train_only_primary",
            "groups": PRIMARY_GROUPS_TOTAL,
            "rows": PRIMARY_ROWS_TOTAL,
            "positive_rows": PRIMARY_GROUPS_TOTAL,
            "negative_rows": PRIMARY_GROUPS_TOTAL,
            "subject_bigger_groups": PRIMARY_GROUPS_PER_DIRECTION,
            "subject_smaller_groups": PRIMARY_GROUPS_PER_DIRECTION,
            "predicate_rows": "bigger than 1200; smaller than 1200",
            "label_axis": "C_e binary compatibility",
            "selection_rule": "strict compatible source anchors with abs volume ratio >= 1.25, expanded to both predicates on same G_e",
            "model_use": "main compatibility smoke after schema audit",
        },
        {
            "component": "ambiguous_size_qe_diagnostic",
            "split_role": "train_only_diagnostic",
            "groups": AMBIGUOUS_GROUPS_AVAILABLE,
            "rows": AMBIGUOUS_GROUPS_AVAILABLE * 2,
            "positive_rows": 0,
            "negative_rows": 0,
            "subject_bigger_groups": 0,
            "subject_smaller_groups": 0,
            "predicate_rows": "bigger than 50; smaller than 50",
            "label_axis": "Q_e / p_obs ambiguous-size diagnostic",
            "selection_rule": "abs volume ratio < 1.15",
            "model_use": "excluded from C_e binary; used to test abstain/uncertain design",
        },
        {
            "component": "gt_geometry_conflict_audit",
            "split_role": "train_only_audit",
            "groups": OPPOSING_GROUPS_AVAILABLE,
            "rows": OPPOSING_GROUPS_AVAILABLE * 2,
            "positive_rows": 0,
            "negative_rows": 0,
            "subject_bigger_groups": 0,
            "subject_smaller_groups": 0,
            "predicate_rows": "bigger than 36; smaller than 36",
            "label_axis": "hidden audit only",
            "selection_rule": "GT predicate opposes volume direction",
            "model_use": "excluded from primary smoke until inspected; candidate annotation/noise analysis",
        },
    ]


def feature_schema() -> list[dict[str, Any]]:
    return [
        {
            "block": "T_e",
            "field": "predicate_text",
            "model_view": "compatibility_main",
            "allowed": True,
            "definition": "`bigger than` or `smaller than` text/one-hot embedding",
            "notes": "This is the semantic query whose compatibility with G_e_size is tested.",
        },
        {
            "block": "T_e",
            "field": "relation_family",
            "model_view": "compatibility_main",
            "allowed": True,
            "definition": "constant `size_relative`",
            "notes": "Allowed but uninformative inside this single-family smoke.",
        },
        {
            "block": "T_e_optional",
            "field": "subject_class_label/object_class_label",
            "model_view": "class_ablation_only",
            "allowed": False,
            "definition": "3DSSG object class labels",
            "notes": "Blocked from first main view because class-pair mass is concentrated in same-class pairs.",
        },
        {
            "block": "G_e_size",
            "field": "log_volume_ratio_s_over_o",
            "model_view": "compatibility_main",
            "allowed": True,
            "definition": "continuous log subject volume over object volume",
            "notes": "Predicate-independent; identical for both rows inside a same-G flip group.",
        },
        {
            "block": "G_e_size",
            "field": "log_max_extent_ratio_s_over_o",
            "model_view": "compatibility_main",
            "allowed": True,
            "definition": "continuous log max OBB extent ratio",
            "notes": "Robust scale cue for elongated objects.",
        },
        {
            "block": "G_e_size",
            "field": "log_footprint_area_ratio_s_over_o",
            "model_view": "compatibility_main",
            "allowed": True,
            "definition": "continuous log horizontal footprint area ratio",
            "notes": "Predicate-independent geometric evidence.",
        },
        {
            "block": "G_e_size",
            "field": "log_vertical_extent_ratio_s_over_o",
            "model_view": "compatibility_main",
            "allowed": True,
            "definition": "continuous log vertical extent ratio",
            "notes": "Ablates size as height-like evidence.",
        },
        {
            "block": "Q_e_size",
            "field": "abs_log_volume_ratio",
            "model_view": "observability_or_qe",
            "allowed": True,
            "definition": "signless size margin",
            "notes": "Can support ambiguity/abstain, but not the signed compatibility label alone.",
        },
        {
            "block": "Q_e_size",
            "field": "pair_obb_available",
            "model_view": "observability_or_qe",
            "allowed": True,
            "definition": "whether both object OBBs are available",
            "notes": "Expected true for primary rows; still kept for schema consistency.",
        },
        {
            "block": "Z_e",
            "field": "source_score/rank",
            "model_view": "not_available_first_probe",
            "allowed": False,
            "definition": "source confidence from relation predictor",
            "notes": "Current source is GT anchor inventory, not a relation predictor output.",
        },
    ]


def blocked_fields() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for field, reason in [
        ("gt_predicate_label", "target/source provenance"),
        ("source_predicate_label", "source provenance"),
        ("anchor_predicate_label", "construction provenance"),
        ("compatibility_label", "label field"),
        ("p_rel_label", "label field"),
        ("p_obs_label", "label field"),
        ("gt_compatible_by_volume", "label proxy"),
        ("gt_compatible_by_vote", "label proxy"),
        ("direction_by_volume", "discretized signed rule proxy"),
        ("direction_by_vote", "discretized signed rule proxy"),
        ("volume_ratio_band", "discretized construction/margin field; use signless Q_e only in main view"),
        ("candidate_component", "construction provenance"),
        ("is_original_gt_anchor", "construction/source provenance"),
        ("subgraph_anchor_key", "row identity leakage"),
        ("directed_pair_predicate_key", "row identity leakage"),
        ("scan_id", "scan leakage; CV grouping only"),
        ("subject_id", "instance leakage"),
        ("object_id", "instance leakage"),
        ("subject_class_label", "blocked from first main view; class ablation only"),
        ("object_class_label", "blocked from first main view; class ablation only"),
        ("class_pair", "blocked from first main view; hidden shortcut audit only"),
    ]:
        rows.append({"field": field, "blocked_from": "model_safe_main_view", "reason": reason})
    return rows


def control_plan() -> list[dict[str, Any]]:
    return [
        {
            "control_id": "C0_schema_leakage",
            "purpose": "ensure blocked target/source/construction fields are absent from model-safe rows",
            "pass_condition": "0 blocked-field hits",
        },
        {
            "control_id": "C1_geometry_only",
            "purpose": "test whether G_e_size alone can solve same-G predicate-flip labels",
            "pass_condition": "AUROC <= 0.60 or near-chance accuracy",
        },
        {
            "control_id": "C2_semantic_only",
            "purpose": "test whether predicate text alone can solve labels",
            "pass_condition": "AUROC <= 0.60",
        },
        {
            "control_id": "C3_TG_interaction",
            "purpose": "main compatibility route",
            "pass_condition": "AUROC >= 0.85 and improves over T-only/G-only",
        },
        {
            "control_id": "C4_wrong_T",
            "purpose": "swap predicate query while keeping G_e_size fixed",
            "pass_condition": "score collapses or inverts relative to C3",
        },
        {
            "control_id": "C5_shuffled_G_within_class_pair",
            "purpose": "verify geometry is pair-specific and not class-only",
            "pass_condition": "AUROC <= 0.60",
        },
        {
            "control_id": "C6_shuffled_G_global",
            "purpose": "verify global geometry shuffling destroys compatibility signal",
            "pass_condition": "AUROC <= 0.60",
        },
        {
            "control_id": "C7_class_pair_hidden_probe",
            "purpose": "detect residual class-pair shortcut outside model-safe view",
            "pass_condition": "majority/AUROC <= 0.60",
        },
        {
            "control_id": "C8_ambiguous_Qe_holdout",
            "purpose": "ensure ambiguous size rows are not treated as binary C_e labels",
            "pass_condition": "ambiguous rows excluded from primary binary target",
        },
    ]


def materialization_contract() -> dict[str, Any]:
    return {
        "dataset_id": "h002_size_relative_same_g_predicate_flip_v1",
        "source_artifact": rel_path(DEFAULT_INVENTORY_DIR),
        "next_runner": NEXT_TODO,
        "primary_design": {
            "groups": PRIMARY_GROUPS_TOTAL,
            "rows": PRIMARY_ROWS_TOTAL,
            "group_definition": "same scan, subject, object, and identical G_e_size; two candidate rows differ only by predicate T_e",
            "row_pair": ["predicate=bigger than", "predicate=smaller than"],
            "positive_rule": "predicate agrees with continuous size direction from source anchor",
            "negative_rule": "predicate is the flipped incompatible size predicate on the same G_e_size",
        },
        "quota": {
            "subject_bigger_groups": PRIMARY_GROUPS_PER_DIRECTION,
            "subject_smaller_groups": PRIMARY_GROUPS_PER_DIRECTION,
            "positive_rows": PRIMARY_GROUPS_TOTAL,
            "negative_rows": PRIMARY_GROUPS_TOTAL,
            "bigger_than_rows": PRIMARY_GROUPS_TOTAL,
            "smaller_than_rows": PRIMARY_GROUPS_TOTAL,
        },
        "caps": {
            "max_groups_per_class_pair": CLASS_PAIR_GROUP_CAP,
            "max_groups_per_class_pair_direction": CLASS_PAIR_DIRECTION_CAP,
            "max_groups_per_scan": SCAN_GROUP_CAP,
        },
        "diagnostics": {
            "ambiguous_size_groups": AMBIGUOUS_GROUPS_AVAILABLE,
            "ambiguous_size_rows": AMBIGUOUS_GROUPS_AVAILABLE * 2,
            "gt_geometry_conflict_groups": OPPOSING_GROUPS_AVAILABLE,
            "gt_geometry_conflict_rows": OPPOSING_GROUPS_AVAILABLE * 2,
        },
        "model_safe_view": {
            "main_allowed_blocks": ["T_e.predicate_text", "G_e_size.continuous_log_ratios"],
            "qe_allowed_blocks": ["Q_e_size.signless_margin", "Q_e_size.pair_obb_available"],
            "blocked_blocks": ["Z_e", "GT/source provenance", "construction fields", "class labels in first main view"],
        },
    }


def output_manifest_plan() -> list[dict[str, Any]]:
    return [
        {
            "file": "candidate_rows.jsonl",
            "role": "full train-only materialized rows with labels and provenance",
            "model_safe": False,
        },
        {
            "file": "model_safe_main_view.jsonl",
            "role": "primary T_e + continuous G_e_size rows for schema audit and smoke plan",
            "model_safe": True,
        },
        {
            "file": "model_safe_qe_view.jsonl",
            "role": "signless Q_e_size / observability diagnostic view",
            "model_safe": True,
        },
        {
            "file": "hidden_manifest.jsonl",
            "role": "GT/source/construction/class-pair provenance for audit only",
            "model_safe": False,
        },
        {
            "file": "group_manifest.jsonl",
            "role": "same-G group membership and paired-row integrity checks",
            "model_safe": False,
        },
        {
            "file": "schema_precheck.json",
            "role": "row counts, blocked-field hits, label balance, and cap audit",
            "model_safe": False,
        },
    ]


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# H002 Size-Relative Candidate Materialization Plan After Source Inventory",
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
            f"subject_bigger_groups = {PRIMARY_GROUPS_PER_DIRECTION}",
            f"subject_smaller_groups = {PRIMARY_GROUPS_PER_DIRECTION}",
            f"ambiguous_diagnostic_rows = {AMBIGUOUS_GROUPS_AVAILABLE * 2}",
            f"gt_geometry_conflict_audit_rows = {OPPOSING_GROUPS_AVAILABLE * 2}",
            "```",
            "",
            "## Main Design",
            "",
            "The materialization runner must create paired rows with identical `G_e_size` and flipped `T_e`:",
            "",
            "```text",
            "row A: same subject/object geometry, predicate = bigger than",
            "row B: same subject/object geometry, predicate = smaller than",
            "```",
            "",
            "This makes geometry-only insufficient for the binary compatibility target. The expected signal is the",
            "`T_e x G_e_size` interaction.",
            "",
            "## Boundary",
            "",
            "- No rows were materialized in this stage.",
            "- No learned smoke or training was run.",
            "- No validation/test source was used.",
            "- H001 artifacts were not modified.",
        ]
    ) + "\n"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    inventory_summary_path = args.inventory_dir / "summary.json"
    inventory_errors_path = args.inventory_dir / "validation_errors.jsonl"
    inventory_summary = read_json(inventory_summary_path) if inventory_summary_path.exists() else {}
    inventory_errors = read_jsonl(inventory_errors_path)
    predicate_rows = read_csv(args.inventory_dir / "predicate_anchor_inventory.csv")
    class_pair_rows = read_csv(args.inventory_dir / "class_pair_inventory.csv")
    margin_rows = read_csv(args.inventory_dir / "size_margin_inventory.csv")
    validation_errors = validate_inputs(inventory_summary, inventory_errors, predicate_rows, class_pair_rows, margin_rows)

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_by_input_validation_errors"
        next_todo = EXPECTED_INVENTORY_NEXT
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO

    output_paths = {
        "materialization_contract": args.output_dir / "materialization_contract.json",
        "row_quota_plan": args.output_dir / "row_quota_plan.csv",
        "feature_schema": args.output_dir / "feature_schema.csv",
        "blocked_fields": args.output_dir / "blocked_fields.csv",
        "control_plan": args.output_dir / "control_plan.csv",
        "output_manifest_plan": args.output_dir / "output_manifest_plan.csv",
        "report": args.output_dir / "report.md",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }

    contract = materialization_contract()
    quota_rows = row_quota_plan()
    feature_rows = feature_schema()
    blocked_rows = blocked_fields()
    control_rows = control_plan()
    manifest_rows = output_manifest_plan()

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
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
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
        "plan_counts": {
            "primary_groups": PRIMARY_GROUPS_TOTAL,
            "primary_rows": PRIMARY_ROWS_TOTAL,
            "primary_positive_rows": PRIMARY_GROUPS_TOTAL,
            "primary_negative_rows": PRIMARY_GROUPS_TOTAL,
            "subject_bigger_groups": PRIMARY_GROUPS_PER_DIRECTION,
            "subject_smaller_groups": PRIMARY_GROUPS_PER_DIRECTION,
            "ambiguous_diagnostic_groups": AMBIGUOUS_GROUPS_AVAILABLE,
            "ambiguous_diagnostic_rows": AMBIGUOUS_GROUPS_AVAILABLE * 2,
            "gt_geometry_conflict_audit_groups": OPPOSING_GROUPS_AVAILABLE,
            "gt_geometry_conflict_audit_rows": OPPOSING_GROUPS_AVAILABLE * 2,
        },
        "caps": {
            "max_groups_per_class_pair": CLASS_PAIR_GROUP_CAP,
            "max_groups_per_class_pair_direction": CLASS_PAIR_DIRECTION_CAP,
            "max_groups_per_scan": SCAN_GROUP_CAP,
        },
        "input_capacity": inventory_summary.get("capacity", {}),
        "claim_boundary": {
            "rows_materialized_now": False,
            "learned_smoke_allowed_now": False,
            "paper_evidence_allowed_now": False,
            "size_relative_solved": False,
            "geometry_only_success_counts_as_main_claim": False,
        },
    }

    write_json(output_paths["materialization_contract"], contract)
    write_csv(output_paths["row_quota_plan"], quota_rows)
    write_csv(output_paths["feature_schema"], feature_rows)
    write_csv(output_paths["blocked_fields"], blocked_rows)
    write_csv(output_paths["control_plan"], control_rows)
    write_csv(output_paths["output_manifest_plan"], manifest_rows)
    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
