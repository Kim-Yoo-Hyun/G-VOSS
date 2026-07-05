#!/usr/bin/env python3
"""Write the close-by candidate materialization plan without selecting rows."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INVENTORY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_source_inventory"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan"

EXPECTED_INVENTORY_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_source_inventory_ready_for_candidate_materialization_plan"
)
EXPECTED_INVENTORY_NEXT = "compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan_input_errors"
SELECTED_PATH = "materialize_close_by_controlled_candidates_with_distance_controls"
NEXT_TODO = "compatibility_dataset_v3_proximity_close_by_candidate_materialization"

PRIMARY_ACCEPT_QUOTA = 400
PRIMARY_REJECT_QUOTA = 400
ABSTAIN_NEAR_NONGT_QUOTA = 120
ABSTAIN_AMBIGUOUS_QUOTA = 80
ABSTAIN_UNCERTAIN_QUOTA = 40
RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA = 120
RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA = 120

MAX_ROWS_PER_SCAN = 18
MAX_ROWS_PER_CLASS_PAIR = 48
MAX_ROWS_PER_CLASS_PAIR_RANK = 24
MAX_ROWS_PER_DIRECTED_PAIR = 2
MAX_ROWS_PER_RAW_DISTANCE_BIN = 80


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


def read_csv(path: Path) -> list[dict[str, str]]:
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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
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


def parse_count_string(value: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in value.split(";"):
        item = item.strip()
        if not item or ":" not in item:
            continue
        key, raw = item.rsplit(":", 1)
        counts[key.strip()] = int(raw.strip())
    return counts


def int_field(row: dict[str, Any], key: str) -> int:
    try:
        return int(row.get(key, 0))
    except (TypeError, ValueError):
        return 0


def validate_inventory(inventory: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if inventory.get("status") != EXPECTED_INVENTORY_STATUS:
        errors.append({"error_type": "unexpected_inventory_status", "actual": inventory.get("status")})
    if inventory.get("next_todo") != EXPECTED_INVENTORY_NEXT:
        errors.append({"error_type": "unexpected_inventory_next_todo", "actual": inventory.get("next_todo")})
    if inventory.get("validation_errors") != 0:
        errors.append({"error_type": "inventory_validation_errors_present", "actual": inventory.get("validation_errors")})
    boundary = inventory.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "materializes_rows",
        "fills_labels",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "inventory_boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in [
        "summary.json",
        "control_group_summary.csv",
        "class_pair_rank_mixed_capacity.csv",
        "raw_distance_mixed_capacity.csv",
        "raw_distance_rank_mixed_capacity.csv",
        "target_bucket_counts.csv",
        "feature_availability.csv",
    ]:
        path = args.inventory_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_inventory_artifact", "path": rel_path(path)})
    return errors


def group_summary_by_name(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["group_name"]: row for row in rows}


def quota_table(candidate_counts: dict[str, int]) -> list[dict[str, Any]]:
    abstain_total = ABSTAIN_NEAR_NONGT_QUOTA + ABSTAIN_AMBIGUOUS_QUOTA + ABSTAIN_UNCERTAIN_QUOTA
    return [
        {
            "split": "train_only",
            "subset": "primary_binary",
            "pool": "accept_anchor",
            "role": "accept",
            "available": candidate_counts.get("accept_anchor", 0),
            "quota": PRIMARY_ACCEPT_QUOTA,
            "label_C_e": 1,
            "label_p_rel": "accept",
            "label_p_obs": "observable",
            "selection_basis": "exact_match + satisfied + near",
        },
        {
            "split": "train_only",
            "subset": "primary_binary",
            "pool": "reject_far_geometry",
            "role": "reject",
            "available": candidate_counts.get("reject_far_geometry", 0),
            "quota": PRIMARY_REJECT_QUOTA,
            "label_C_e": 0,
            "label_p_rel": "reject",
            "label_p_obs": "observable",
            "selection_basis": "non-exact + unsatisfied + far",
        },
        {
            "split": "train_only",
            "subset": "abstain_qe",
            "pool": "near_nonexact_satisfied",
            "role": "abstain_or_audit",
            "available": candidate_counts.get("abstain_or_audit", 0),
            "quota": ABSTAIN_NEAR_NONGT_QUOTA,
            "label_C_e": "abstain",
            "label_p_rel": "abstain",
            "label_p_obs": "observable_but_unlabeled",
            "selection_basis": "non-exact + satisfied + near",
        },
        {
            "split": "train_only",
            "subset": "abstain_qe",
            "pool": "ambiguous_distance",
            "role": "abstain",
            "available": candidate_counts.get("abstain_or_audit", 0),
            "quota": ABSTAIN_AMBIGUOUS_QUOTA,
            "label_C_e": "abstain",
            "label_p_rel": "abstain",
            "label_p_obs": "ambiguous",
            "selection_basis": "ambiguous normalized distance",
        },
        {
            "split": "train_only",
            "subset": "abstain_qe",
            "pool": "geometry_uncertain",
            "role": "abstain",
            "available": candidate_counts.get("abstain_or_audit", 0),
            "quota": ABSTAIN_UNCERTAIN_QUOTA,
            "label_C_e": "abstain",
            "label_p_rel": "abstain",
            "label_p_obs": "uncertain_or_unobservable",
            "selection_basis": "geometry_status == uncertain",
        },
        {
            "split": "train_only",
            "subset": "raw_distance_diagnostic",
            "pool": "accept_anchor_raw_distance_matched",
            "role": "accept_diagnostic",
            "available": candidate_counts.get("accept_anchor", 0),
            "quota": RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA,
            "label_C_e": 1,
            "label_p_rel": "accept",
            "label_p_obs": "observable",
            "selection_basis": "accept anchor selected within mixed raw-distance bins",
        },
        {
            "split": "train_only",
            "subset": "raw_distance_diagnostic",
            "pool": "reject_far_geometry_raw_distance_matched",
            "role": "reject_diagnostic",
            "available": candidate_counts.get("reject_far_geometry", 0),
            "quota": RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA,
            "label_C_e": 0,
            "label_p_rel": "reject",
            "label_p_obs": "observable",
            "selection_basis": "reject far geometry selected within mixed raw-distance bins",
        },
        {
            "split": "train_only",
            "subset": "diagnostic_only",
            "pool": "gt_geometry_conflict",
            "role": "audit_required",
            "available": candidate_counts.get("gt_geometry_conflict", 0),
            "quota": min(4, candidate_counts.get("gt_geometry_conflict", 0)),
            "label_C_e": "audit_required",
            "label_p_rel": "audit_required",
            "label_p_obs": "observable",
            "selection_basis": "exact_match + far/unsatisfied conflict, not used for training",
        },
        {
            "split": "train_only",
            "subset": "planned_total",
            "pool": "all_materialized_rows",
            "role": "summary",
            "available": "",
            "quota": PRIMARY_ACCEPT_QUOTA
            + PRIMARY_REJECT_QUOTA
            + abstain_total
            + RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA
            + RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA
            + min(4, candidate_counts.get("gt_geometry_conflict", 0)),
            "label_C_e": "",
            "label_p_rel": "",
            "label_p_obs": "",
            "selection_basis": "primary + abstain + diagnostic subsets",
        },
    ]


def sampling_caps() -> list[dict[str, Any]]:
    return [
        {"cap_axis": "scan_id", "max_rows": MAX_ROWS_PER_SCAN, "applies_to": "all subsets", "reason": "avoid scan memorization"},
        {"cap_axis": "subject_object_class_pair", "max_rows": MAX_ROWS_PER_CLASS_PAIR, "applies_to": "primary_binary", "reason": "avoid class-pair shortcut"},
        {"cap_axis": "subject_object_class_pair + rank_band", "max_rows": MAX_ROWS_PER_CLASS_PAIR_RANK, "applies_to": "primary_binary", "reason": "preserve class-pair+rank balance"},
        {"cap_axis": "directed_pair_id", "max_rows": MAX_ROWS_PER_DIRECTED_PAIR, "applies_to": "all subsets", "reason": "avoid duplicate pair concentration"},
        {"cap_axis": "raw_distance_bin", "max_rows": MAX_ROWS_PER_RAW_DISTANCE_BIN, "applies_to": "raw_distance_diagnostic", "reason": "avoid one raw-distance bin dominating diagnostic subset"},
    ]


def model_view_contract() -> list[dict[str, Any]]:
    return [
        {"view": "T_only", "allowed_fields": "predicate text, relation family, subject/object class text", "blocked_fields": "source score/rank, geometry, labels", "purpose": "semantic-only baseline"},
        {"view": "Z_only", "allowed_fields": "source score, rank band, source id", "blocked_fields": "GT labels, geometry target, hidden construction bucket", "purpose": "source-confidence shortcut baseline"},
        {"view": "G_only", "allowed_fields": "distance, normalized distance, overlap, z geometry, raw metric geometry", "blocked_fields": "predicate label as target, source score/rank, GT status", "purpose": "geometry-only baseline"},
        {"view": "distance_only", "allowed_fields": "distance_xy, distance_3d, normalized_distance_xy, normalized_distance_3d", "blocked_fields": "overlap, class text, source score/rank", "purpose": "mandatory proximity baseline"},
        {"view": "p_geom_valid_rule", "allowed_fields": "p_geom_valid only", "blocked_fields": "semantic/source fields", "purpose": "H001-style rule baseline or teacher candidate"},
        {"view": "T_plus_G_compatibility", "allowed_fields": "T_e + G_e interaction", "blocked_fields": "Z_e, GT status, p_geom_valid target", "purpose": "main C_e view"},
        {"view": "T_plus_G_plus_Q", "allowed_fields": "T_e + G_e + Q_e safe fields", "blocked_fields": "Z_e for C_e", "purpose": "observability-aware compatibility diagnostic"},
        {"view": "Z_plus_C_plus_Q_later", "allowed_fields": "Z_e + C_e + Q_e outputs", "blocked_fields": "raw GT and hidden construction fields", "purpose": "later p_rel/p_obs decision, not this materialization plan"},
    ]


def control_plan() -> list[dict[str, Any]]:
    return [
        {"control": "class_pair_only", "required": True, "expected": "should not dominate primary target after class-pair+rank balancing"},
        {"control": "source_only_Z", "required": True, "expected": "checks rank/source leakage"},
        {"control": "distance_only", "required": True, "expected": "strong baseline; close-by claim must be interpreted against it"},
        {"control": "p_geom_valid_rule", "required": True, "expected": "H001-style geometry rule baseline"},
        {"control": "raw_distance_diagnostic_subset", "required": True, "expected": "small subset where raw-distance bins contain both accept and reject"},
        {"control": "normalized_distance_diagnostic_subset", "required": False, "expected": "not feasible now because inventory capacity is zero"},
        {"control": "shuffled_geometry", "required": True, "expected": "must degrade relative to paired geometry"},
        {"control": "wrong_pair_geometry", "required": True, "expected": "must degrade relative to paired geometry"},
        {"control": "no_gt_as_negative_ablation", "required": False, "expected": "diagnostic only; never main label policy"},
    ]


def blocked_fields() -> list[dict[str, Any]]:
    blocked = [
        ("row_key", "identity", "row identity shortcut"),
        ("prediction_id", "identity", "source row shortcut"),
        ("scan_id", "identity/control", "scan memorization"),
        ("directed_pair_id", "identity/control", "pair memorization"),
        ("label_match_status", "GT/source join", "target construction leakage"),
        ("matched_gt_ids", "GT/source join", "GT leakage"),
        ("matched_predicates", "GT/source join", "GT leakage"),
        ("geometry_status", "target construction", "target leakage unless used only for hidden audit"),
        ("distance_bucket", "target construction", "near/far construction shortcut"),
        ("candidate_bucket", "target construction", "direct label leakage"),
        ("HL_LH_bucket", "RGA", "queue membership cannot be target"),
        ("p_geom_valid", "geometry rule", "baseline-only by default, not main C_e input"),
    ]
    return [{"field": field, "source": source, "reason": reason, "model_safe": False} for field, source, reason in blocked]


def materialization_gates(
    inventory: dict[str, Any],
    control_summary: dict[str, dict[str, str]],
    quota_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidate_counts = parse_count_string(inventory["close_by_inventory"]["candidate_counts"])
    primary_total = PRIMARY_ACCEPT_QUOTA + PRIMARY_REJECT_QUOTA
    abstain_total = ABSTAIN_NEAR_NONGT_QUOTA + ABSTAIN_AMBIGUOUS_QUOTA + ABSTAIN_UNCERTAIN_QUOTA
    raw_diag_total = RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA + RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA
    gates = [
        {"gate": "accept_quota_available", "value": candidate_counts.get("accept_anchor", 0), "required": PRIMARY_ACCEPT_QUOTA, "passed": candidate_counts.get("accept_anchor", 0) >= PRIMARY_ACCEPT_QUOTA},
        {"gate": "reject_quota_available", "value": candidate_counts.get("reject_far_geometry", 0), "required": PRIMARY_REJECT_QUOTA, "passed": candidate_counts.get("reject_far_geometry", 0) >= PRIMARY_REJECT_QUOTA},
        {"gate": "abstain_quota_available", "value": candidate_counts.get("abstain_or_audit", 0), "required": abstain_total, "passed": candidate_counts.get("abstain_or_audit", 0) >= abstain_total},
        {"gate": "class_pair_rank_capacity", "value": int_field(control_summary["class_pair_rank"], "balanced_accept_reject_rows"), "required": primary_total, "passed": int_field(control_summary["class_pair_rank"], "balanced_accept_reject_rows") >= primary_total},
        {"gate": "raw_distance_diagnostic_capacity", "value": int_field(control_summary["raw_distance_bin"], "balanced_accept_reject_rows"), "required": raw_diag_total, "passed": int_field(control_summary["raw_distance_bin"], "balanced_accept_reject_rows") >= raw_diag_total},
        {"gate": "planned_rows_nonzero", "value": sum(int(row["quota"]) for row in quota_rows if row["subset"] != "planned_total"), "required": 1, "passed": True},
    ]
    warnings = []
    norm_capacity = int_field(control_summary["norm_distance_bin"], "balanced_accept_reject_rows")
    if norm_capacity == 0:
        warnings.append(
            {
                "warning_type": "normalized_distance_matched_capacity_zero",
                "meaning": "close-by target can be solved by normalized-distance separation unless distance-only controls are reported",
                "required_action": "include distance_only and p_geom_valid_rule baselines; treat raw-distance subset as diagnostic",
            }
        )
    reject_label_counts = parse_count_string(inventory["close_by_inventory"]["reject_label_status_counts"])
    if reject_label_counts.get("no_gt_for_pair", 0) > 0:
        warnings.append(
            {
                "warning_type": "reject_pool_contains_no_gt_rows",
                "meaning": "reject labels are geometry-defined but many rows still have no GT relation",
                "required_action": "keep no-GT status hidden and document that rejection is based on far unsatisfied geometry",
            }
        )
    return gates, warnings


def row_schema_contract() -> dict[str, Any]:
    return {
        "row_id": "h002_close_by_<subset>_<index>",
        "factor_blocks": {
            "T_e": ["predicate_label", "predicate_text", "predicate_family", "subject_class_text", "object_class_text"],
            "Z_e": ["semantic_score_raw", "semantic_score_norm", "rank_band", "rank_in_context", "source_id"],
            "G_e": [
                "distance_3d",
                "distance_xy",
                "normalized_distance_3d",
                "normalized_distance_xy",
                "projected_iou_xy",
                "projected_subject_overlap_ratio",
                "projected_object_overlap_ratio",
                "center_delta_z",
                "normalized_center_delta_z",
                "subject_top_z",
                "subject_bottom_z",
                "object_top_z",
                "object_bottom_z",
            ],
            "Q_e": ["geometry_available", "geometry_checkable", "feature_missing_mask", "ambiguity_bucket"],
            "hidden_control": [
                "scan_id",
                "directed_pair_id",
                "label_match_status",
                "geometry_status",
                "distance_bucket",
                "candidate_bucket",
                "raw_distance_bin",
                "class_pair_rank_key",
            ],
            "targets": ["C_e_label", "p_rel_label", "p_obs_label", "subset_role"],
        },
        "hard_rule": "C_e model view must exclude Z_e, p_geom_valid, hidden_control, and targets.",
    }


def build_report(
    summary: dict[str, Any],
    inventory: dict[str, Any],
    gates: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> str:
    control = inventory["group_capacity"]
    planned_total = PRIMARY_ACCEPT_QUOTA + PRIMARY_REJECT_QUOTA + ABSTAIN_NEAR_NONGT_QUOTA + ABSTAIN_AMBIGUOUS_QUOTA + ABSTAIN_UNCERTAIN_QUOTA + RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA + RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA + min(4, parse_count_string(inventory["close_by_inventory"]["candidate_counts"]).get("gt_geometry_conflict", 0))
    return f"""# H002 Proximity Close-By Candidate Materialization Plan

## Status

```text
status = {summary["status"]}
selected_path = {summary["selected_path"]}
validation_errors = {summary["validation_errors"]}
warnings = {summary["warnings"]}
next_todo = {summary["next_todo"]}
```

## Decision

Proceed to train-only close-by candidate materialization. This stage only writes
the materialization contract; it does not select rows, fill labels, run smoke, or
train a model.

## Planned Quotas

```text
primary_binary = {PRIMARY_ACCEPT_QUOTA + PRIMARY_REJECT_QUOTA}
  accept_anchor = {PRIMARY_ACCEPT_QUOTA}
  reject_far_geometry = {PRIMARY_REJECT_QUOTA}
abstain_qe = {ABSTAIN_NEAR_NONGT_QUOTA + ABSTAIN_AMBIGUOUS_QUOTA + ABSTAIN_UNCERTAIN_QUOTA}
  near_nonexact_satisfied = {ABSTAIN_NEAR_NONGT_QUOTA}
  ambiguous_distance = {ABSTAIN_AMBIGUOUS_QUOTA}
  geometry_uncertain = {ABSTAIN_UNCERTAIN_QUOTA}
raw_distance_diagnostic = {RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA + RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA}
  accept = {RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA}
  reject = {RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA}
gt_geometry_conflict_audit = up to 4
planned_total_rows = {planned_total}
```

## Required Caps

```text
max_rows_per_scan = {MAX_ROWS_PER_SCAN}
max_rows_per_class_pair = {MAX_ROWS_PER_CLASS_PAIR}
max_rows_per_class_pair_rank = {MAX_ROWS_PER_CLASS_PAIR_RANK}
max_rows_per_directed_pair = {MAX_ROWS_PER_DIRECTED_PAIR}
max_rows_per_raw_distance_bin = {MAX_ROWS_PER_RAW_DISTANCE_BIN}
```

## Capacity Basis

```text
candidate_counts = {inventory["close_by_inventory"]["candidate_counts"]}
class_pair_rank balanced rows = {control["class_pair_rank"]["balanced_accept_reject_rows"]}
raw_distance_bin balanced rows = {control["raw_distance_bin"]["balanced_accept_reject_rows"]}
norm_distance_bin balanced rows = {control["norm_distance_bin"]["balanced_accept_reject_rows"]}
```

`norm_distance_bin` capacity is zero. This is a warning, not an input error:
the plan can proceed, but close-by evaluation must report distance-only and
`p_geom_valid_rule` baselines and keep a raw-distance diagnostic subset.

## Gates

{chr(10).join(f"- {row['gate']}: value {row['value']} / required {row['required']} / passed {row['passed']}" for row in gates)}

## Warnings

{chr(10).join(f"- {row['warning_type']}: {row['required_action']}" for row in warnings) if warnings else "- none"}

## Next

```text
{summary["next_todo"]}
```
"""


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    inventory_summary_path = args.inventory_dir / "summary.json"
    inventory = read_json(inventory_summary_path) if inventory_summary_path.exists() else {}
    validation_errors = validate_inventory(inventory, args)

    if validation_errors:
        candidate_counts: dict[str, int] = {}
        control_summary: dict[str, dict[str, str]] = {}
    else:
        candidate_counts = parse_count_string(inventory["close_by_inventory"]["candidate_counts"])
        control_summary = group_summary_by_name(read_csv(args.inventory_dir / "control_group_summary.csv"))

    quotas = quota_table(candidate_counts)
    if validation_errors:
        gates: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        status = STATUS_ERROR
        selected_path = "blocked_input_errors"
        next_todo = "fix_input_errors"
    else:
        gates, warnings = materialization_gates(inventory, control_summary, quotas)
        status = STATUS_READY if all(bool(row["passed"]) for row in gates) else STATUS_ERROR
        selected_path = SELECTED_PATH if status == STATUS_READY else "blocked_capacity_gates"
        next_todo = NEXT_TODO if status == STATUS_READY else "review_close_by_materialization_plan"
        if status != STATUS_READY:
            validation_errors.extend({"error_type": "gate_failed", "gate": row["gate"], "value": row["value"], "required": row["required"]} for row in gates if not row["passed"])

    planned_primary_binary = PRIMARY_ACCEPT_QUOTA + PRIMARY_REJECT_QUOTA
    planned_abstain = ABSTAIN_NEAR_NONGT_QUOTA + ABSTAIN_AMBIGUOUS_QUOTA + ABSTAIN_UNCERTAIN_QUOTA
    planned_raw_diagnostic = RAW_DISTANCE_DIAGNOSTIC_ACCEPT_QUOTA + RAW_DISTANCE_DIAGNOSTIC_REJECT_QUOTA
    planned_gt_conflict = min(4, candidate_counts.get("gt_geometry_conflict", 0))
    planned_total = planned_primary_binary + planned_abstain + planned_raw_diagnostic + planned_gt_conflict

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "warnings": len(warnings),
        "input_inventory_summary": rel_path(inventory_summary_path),
        "planned_counts": {
            "planned_total_rows": planned_total,
            "primary_binary_rows": planned_primary_binary,
            "primary_accept": PRIMARY_ACCEPT_QUOTA,
            "primary_reject": PRIMARY_REJECT_QUOTA,
            "abstain_qe_rows": planned_abstain,
            "raw_distance_diagnostic_rows": planned_raw_diagnostic,
            "gt_geometry_conflict_audit_rows": planned_gt_conflict,
        },
        "boundary": {
            "split": "train_only_materialization_plan",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "fills_labels": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "quota_table": rel_path(args.output_dir / "quota_table.csv"),
            "sampling_caps": rel_path(args.output_dir / "sampling_caps.csv"),
            "model_view_contract": rel_path(args.output_dir / "model_view_contract.csv"),
            "control_plan": rel_path(args.output_dir / "control_plan.csv"),
            "blocked_fields": rel_path(args.output_dir / "blocked_fields.csv"),
            "row_schema_contract": rel_path(args.output_dir / "row_schema_contract.json"),
            "materialization_gates": rel_path(args.output_dir / "materialization_gates.csv"),
            "warnings": rel_path(args.output_dir / "warnings.jsonl"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    route_decision = [
        {
            "decision": selected_path,
            "status": status,
            "next_todo": next_todo,
            "planned_total_rows": planned_total,
            "primary_binary_rows": planned_primary_binary,
            "warning_summary": "; ".join(row["warning_type"] for row in warnings) if warnings else "none",
            "support_contact_after_close_by": "standing_on_then_lying_on_then_supported_by_individual_predicate_probe",
        }
    ]

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "quota_table.csv", quotas)
    write_csv(args.output_dir / "sampling_caps.csv", sampling_caps())
    write_csv(args.output_dir / "model_view_contract.csv", model_view_contract())
    write_csv(args.output_dir / "control_plan.csv", control_plan())
    write_csv(args.output_dir / "blocked_fields.csv", blocked_fields())
    write_json(args.output_dir / "row_schema_contract.json", row_schema_contract())
    write_csv(args.output_dir / "materialization_gates.csv", gates)
    write_jsonl(args.output_dir / "warnings.jsonl", warnings)
    write_csv(args.output_dir / "route_decision.csv", route_decision)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    (args.output_dir / "report.md").write_text(build_report(summary, inventory, gates, warnings), encoding="utf-8")


if __name__ == "__main__":
    main()
