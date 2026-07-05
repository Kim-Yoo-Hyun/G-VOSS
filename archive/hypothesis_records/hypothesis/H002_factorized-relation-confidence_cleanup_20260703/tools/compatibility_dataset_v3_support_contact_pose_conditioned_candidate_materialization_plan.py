#!/usr/bin/env python3
"""Write the materialization plan for support/contact pose-conditioned candidates."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_CAPACITY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan"
DEFAULT_TARGET_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_target_plan"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan"

EXPECTED_CAPACITY_STATUS = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan_ready_for_candidate_materialization_plan"
EXPECTED_CAPACITY_NEXT = "compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan"
EXPECTED_TARGET_PLAN_STATUS = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_target_plan_ready_for_capacity_scan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization_plan_input_errors"
SELECTED_PATH = "materialize_pose_conditioned_support_contact_candidates_from_frozen_anchor_preview"
NEXT_TODO = "compatibility_dataset_v3_support_contact_pose_conditioned_candidate_materialization"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--target-plan-dir", type=Path, default=DEFAULT_TARGET_PLAN_DIR)
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
    capacity_summary: dict[str, Any],
    capacity_errors: list[dict[str, Any]],
    target_plan_summary: dict[str, Any],
    anchor_preview_rows: list[dict[str, Any]],
    shortcut_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if capacity_summary.get("status") != EXPECTED_CAPACITY_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "actual": capacity_summary.get("status")})
    if capacity_summary.get("next_todo") != EXPECTED_CAPACITY_NEXT:
        errors.append({"error_type": "unexpected_capacity_next", "actual": capacity_summary.get("next_todo")})
    if capacity_summary.get("validation_errors") != 0:
        errors.append({"error_type": "capacity_validation_errors", "actual": capacity_summary.get("validation_errors")})
    if capacity_errors:
        errors.append({"error_type": "capacity_validation_error_rows_present", "rows": len(capacity_errors)})
    if target_plan_summary.get("status") != EXPECTED_TARGET_PLAN_STATUS:
        errors.append({"error_type": "unexpected_target_plan_status", "actual": target_plan_summary.get("status")})
    decision = capacity_summary.get("path_decision", {})
    if decision.get("candidate_materialization_plan_allowed") is not True:
        errors.append({"error_type": "materialization_plan_not_allowed", "actual": decision.get("candidate_materialization_plan_allowed")})
    for key in ["candidate_materialization_allowed", "learned_smoke_allowed", "paper_evidence_allowed"]:
        if decision.get(key) is not False:
            errors.append({"error_type": "capacity_boundary_not_false", "key": key, "actual": decision.get(key)})

    cap = capacity_summary.get("capacity_summary", {})
    if cap.get("selected_anchor_groups") != 200:
        errors.append({"error_type": "unexpected_selected_anchor_groups", "actual": cap.get("selected_anchor_groups")})
    if cap.get("selected_total_rows_if_materialized") != 400:
        errors.append({"error_type": "unexpected_materialized_row_count", "actual": cap.get("selected_total_rows_if_materialized")})
    if cap.get("passes_materialization_capacity_gate") is not True:
        errors.append({"error_type": "capacity_gate_not_passed", "actual": cap.get("passes_materialization_capacity_gate")})

    if len(anchor_preview_rows) != 200:
        errors.append({"error_type": "unexpected_anchor_preview_rows", "actual": len(anchor_preview_rows)})
    anchor_ids = [row.get("anchor_id") for row in anchor_preview_rows]
    if len(set(anchor_ids)) != len(anchor_ids):
        errors.append({"error_type": "duplicate_anchor_ids", "unique": len(set(anchor_ids)), "rows": len(anchor_ids)})
    state_counts = Counter(str(row.get("anchor_pose_state")) for row in anchor_preview_rows)
    if state_counts.get("lying_like_support_contact", 0) != 100 or state_counts.get("upright_support_contact", 0) != 100:
        errors.append({"error_type": "unexpected_anchor_state_counts", "actual": dict(state_counts)})
    hard_rows = sum(1 for row in anchor_preview_rows if row.get("hard_surface_pair") is True)
    if hard_rows != 0:
        errors.append({"error_type": "hard_surface_rows_in_frozen_anchor_preview", "actual": hard_rows})
    for row in anchor_preview_rows:
        target_rows = row.get("target_rows_preview")
        if not isinstance(target_rows, list) or len(target_rows) != 2:
            errors.append({"error_type": "bad_target_rows_preview", "anchor_id": row.get("anchor_id"), "actual": target_rows})
            continue
        labels = {item.get("predicate_label"): item.get("compatibility_y") for item in target_rows}
        if set(labels) != {"lying on", "standing on"}:
            errors.append({"error_type": "missing_predicate_flip_rows", "anchor_id": row.get("anchor_id"), "labels": labels})
        if sorted(labels.values()) != [0, 1]:
            errors.append({"error_type": "target_pair_not_one_positive_one_negative", "anchor_id": row.get("anchor_id"), "labels": labels})
    if not shortcut_rows:
        errors.append({"error_type": "missing_shortcut_capacity_audit"})
    return errors


def materialization_contract(capacity_dir: Path) -> dict[str, Any]:
    return {
        "dataset_name": "h002_support_contact_pose_conditioned_candidates_v1",
        "contract_role": "train-only candidate materialization contract",
        "frozen_anchor_source": rel_path(capacity_dir / "anchor_candidate_preview.jsonl"),
        "selection_policy": "reuse frozen 200-anchor capacity preview exactly; do not re-rank, expand, or refill anchors in materializer",
        "rows_per_anchor": 2,
        "expected_rows": 400,
        "primary_predicates": ["lying on", "standing on"],
        "diagnostic_predicates": ["supported by"],
        "label_rule": {
            "lying_like_support_contact": {"lying on": 1, "standing on": 0},
            "upright_support_contact": {"lying on": 0, "standing on": 1},
        },
        "same_geometry_requirement": "both predicate rows from an anchor must share identical G_e fields and anchor_id",
        "split_policy": {
            "split": "train",
            "cv_group_id": "anchor_id",
            "grouped_cv_required": True,
            "validation_usage": False,
            "test_usage": False,
        },
        "materializer_allowed_actions": [
            "read frozen anchor preview",
            "expand each anchor into lying-on and standing-on rows",
            "copy model-safe G_e and Q_e fields",
            "create audit-only hidden controls",
            "write candidate_rows, smoke_ready_candidate_view, hidden_manifest, and manifest",
        ],
        "materializer_forbidden_actions": [
            "select additional anchors",
            "change thresholds",
            "use queue kind as label",
            "use source score or rank in compatibility label",
            "materialize validation/test rows",
            "run learned smoke",
        ],
    }


def row_schema() -> dict[str, Any]:
    return {
        "schema_name": "h002_support_contact_pose_conditioned_candidate_row_v1",
        "required_top_level_fields": [
            "row_id",
            "anchor_id",
            "cv_group_id",
            "split",
            "source_dataset",
            "T_e",
            "Z_e_safe",
            "G_e_mesh_pose_contact",
            "Q_e_safe",
            "labels",
            "controls_hidden",
        ],
        "model_safe_blocks": {
            "T_e": [
                "predicate_label",
                "predicate_text",
                "relation_family",
                "subject_class_label",
                "object_class_label",
            ],
            "Z_e_safe": [
                "source_score_available",
                "source_rank_available",
            ],
            "G_e_mesh_pose_contact": [
                "abs_surface_gap_subject_bottom_to_object_top",
                "xy_overlap_min_ratio",
                "subject_vertical_extent_ratio",
                "subject_flatness_ratio",
                "subject_major_axis_upness",
                "obb_contact_likelihood_proxy",
                "point_abs_surface_gap_optional",
                "point_contact_candidate_ratio_optional",
                "point_subject_bottom_band_density_optional",
                "point_object_top_band_density_optional",
            ],
            "Q_e_safe": [
                "semseg_obb_available",
                "aligned_ply_point_features_available",
                "point_feature_complete",
                "hard_surface_pair_allowed",
            ],
        },
        "labels": {
            "compatibility_y": "binary target for predicate-geometry compatibility",
            "target_family": "support_contact_pose_conditioned",
            "label_source": "pose_conditioned_same_G_predicate_flip",
        },
        "controls_hidden": [
            "anchor_pose_state",
            "scan_id",
            "subject_id",
            "object_id",
            "visible_pair",
            "hard_surface_pair",
            "source_predicates",
            "queue_kinds",
            "G_e_hash",
        ],
    }


def blocked_fields() -> list[dict[str, Any]]:
    fields = [
        ("anchor_pose_state", "label construction state; audit-only"),
        ("queue_kind", "HL/LH construction queue; audit-only"),
        ("geometry_status", "legacy RGA status; audit-only"),
        ("source_score", "source confidence must not enter C_e"),
        ("semantic_rank", "source rank shortcut"),
        ("rank_band", "source rank shortcut"),
        ("visible_pair", "object-pair shortcut"),
        ("scan_id", "scan memorization"),
        ("subject_id", "instance shortcut"),
        ("object_id", "instance shortcut"),
        ("p_geom_valid", "old H001 geometry proxy baseline, not main G_e"),
        ("consistency_score", "old proxy score"),
        ("disagreement_score", "old proxy score"),
        ("underconfidence_score", "old proxy score"),
        ("target_rows_preview", "label preview source, not feature"),
        ("compatibility_y", "target label"),
    ]
    return [{"field": field, "status": "blocked_from_model_input", "reason": reason} for field, reason in fields]


def output_manifest_contract() -> dict[str, Any]:
    return {
        "expected_outputs": {
            "candidate_rows": "candidate_rows.jsonl",
            "smoke_ready_candidate_view": "smoke_ready_candidate_view.jsonl",
            "hidden_manifest": "hidden_manifest.jsonl",
            "schema_shortcut_precheck": "schema_shortcut_precheck.csv",
            "materialization_manifest": "manifest.json",
            "summary": "summary.json",
            "report": "report.md",
            "validation_errors": "validation_errors.jsonl",
        },
        "expected_counts": {
            "anchor_groups": 200,
            "rows": 400,
            "positive_rows": 200,
            "negative_rows": 200,
            "lying_on_rows": 200,
            "standing_on_rows": 200,
            "lying_like_anchor_groups": 100,
            "upright_anchor_groups": 100,
        },
        "post_materialization_required_next": "compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit",
        "learned_smoke_after_materialization": "blocked_until_schema_shortcut_audit_passes",
    }


def downstream_gates() -> list[dict[str, Any]]:
    return [
        {
            "gate": "row_count_integrity",
            "required": "400 rows from 200 anchors, exactly 2 rows per anchor",
            "failure_action": "stop_before_schema_audit",
        },
        {
            "gate": "label_balance",
            "required": "200 positive / 200 negative; 200 lying on / 200 standing on",
            "failure_action": "stop_before_schema_audit",
        },
        {
            "gate": "same_G_e_pair_integrity",
            "required": "paired rows within an anchor share identical G_e hash",
            "failure_action": "stop_before_schema_audit",
        },
        {
            "gate": "blocked_field_absence",
            "required": "model-safe view excludes all blocked fields",
            "failure_action": "stop_before_learned_smoke",
        },
        {
            "gate": "shortcut_precheck",
            "required": "predicate-only, geometry-only, visible-pair, scan, and queue probes reported before smoke",
            "failure_action": "route_to_schema_shortcut_repair",
        },
        {
            "gate": "grouped_cv_contract",
            "required": "anchor_id is the CV group; paired rows never split across folds",
            "failure_action": "stop_before_learned_smoke",
        },
    ]


def plan_summary_rows(capacity_summary: dict[str, Any], anchor_preview_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    state_counts = Counter(row.get("anchor_pose_state") for row in anchor_preview_rows)
    predicate_counts = Counter(item.get("predicate_label") for row in anchor_preview_rows for item in row.get("target_rows_preview", []))
    label_counts = Counter(item.get("compatibility_y") for row in anchor_preview_rows for item in row.get("target_rows_preview", []))
    cap = capacity_summary.get("capacity_summary", {})
    return [
        {"item": "frozen_anchor_rows", "value": len(anchor_preview_rows), "required": 200, "pass": len(anchor_preview_rows) == 200},
        {"item": "materialized_rows_planned", "value": len(anchor_preview_rows) * 2, "required": 400, "pass": len(anchor_preview_rows) * 2 == 400},
        {"item": "lying_like_anchors", "value": state_counts.get("lying_like_support_contact", 0), "required": 100, "pass": state_counts.get("lying_like_support_contact", 0) == 100},
        {"item": "upright_anchors", "value": state_counts.get("upright_support_contact", 0), "required": 100, "pass": state_counts.get("upright_support_contact", 0) == 100},
        {"item": "lying_on_rows_planned", "value": predicate_counts.get("lying on", 0), "required": 200, "pass": predicate_counts.get("lying on", 0) == 200},
        {"item": "standing_on_rows_planned", "value": predicate_counts.get("standing on", 0), "required": 200, "pass": predicate_counts.get("standing on", 0) == 200},
        {"item": "positive_rows_planned", "value": label_counts.get(1, 0), "required": 200, "pass": label_counts.get(1, 0) == 200},
        {"item": "negative_rows_planned", "value": label_counts.get(0, 0), "required": 200, "pass": label_counts.get(0, 0) == 200},
        {"item": "capacity_gate", "value": cap.get("passes_materialization_capacity_gate"), "required": True, "pass": cap.get("passes_materialization_capacity_gate") is True},
    ]


def path_decision(errors: list[dict[str, Any]]) -> dict[str, Any]:
    if errors:
        return {
            "status": STATUS_ERRORS,
            "selected_path": "fix_inputs_before_materialization_plan",
            "next_todo": EXPECTED_CAPACITY_NEXT,
            "validation_errors": len(errors),
            "candidate_materialization_allowed": False,
            "learned_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "rationale": "Input validation failed; materialization plan cannot be trusted.",
        }
    return {
        "status": STATUS_READY,
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "validation_errors": 0,
        "candidate_materialization_allowed": True,
        "learned_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "rationale": "Frozen 200-anchor preview and row schema are ready for candidate materialization; learned smoke remains blocked until schema shortcut audit.",
    }


def report_text(summary: dict[str, Any]) -> str:
    decision = summary["path_decision"]
    return f"""# Compatibility Dataset V3 Support/Contact Pose-Conditioned Candidate Materialization Plan

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
next_todo = {summary['next_todo']}
validation_errors = {summary['validation_errors']}
```

## Plan

The materializer must reuse the frozen `200`-anchor capacity preview exactly and expand each
anchor into two rows:

```text
same G_e + predicate = lying on
same G_e + predicate = standing on
```

Expected materialized rows:

```text
anchors = 200
rows = 400
positive = 200
negative = 200
lying on rows = 200
standing on rows = 200
```

## Decision

```text
candidate_materialization_allowed = {decision['candidate_materialization_allowed']}
learned_smoke_allowed = {decision['learned_smoke_allowed']}
paper_evidence_allowed = {decision['paper_evidence_allowed']}
```

Learned smoke is still blocked until materialized rows pass a schema and shortcut audit.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    capacity_summary = read_json(args.capacity_dir / "summary.json")
    capacity_errors = read_jsonl(args.capacity_dir / "validation_errors.jsonl")
    target_plan_summary = read_json(args.target_plan_dir / "summary.json")
    anchor_preview_rows = read_jsonl(args.capacity_dir / "anchor_candidate_preview.jsonl")
    shortcut_rows = read_csv(args.capacity_dir / "shortcut_capacity_audit.csv")
    errors = validate_inputs(capacity_summary, capacity_errors, target_plan_summary, anchor_preview_rows, shortcut_rows)

    contract = materialization_contract(args.capacity_dir)
    schema = row_schema()
    manifest_contract = output_manifest_contract()
    gates = downstream_gates()
    plan_rows = plan_summary_rows(capacity_summary, anchor_preview_rows)
    decision = path_decision(errors)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": decision["status"],
        "selected_path": decision["selected_path"],
        "next_todo": decision["next_todo"],
        "validation_errors": len(errors),
        "capacity_status": capacity_summary.get("status"),
        "target_plan_status": target_plan_summary.get("status"),
        "plan_counts": {
            "frozen_anchor_groups": len(anchor_preview_rows),
            "planned_rows": len(anchor_preview_rows) * 2,
            "state_counts": dict(sorted(Counter(row.get("anchor_pose_state") for row in anchor_preview_rows).items())),
            "predicate_counts_if_materialized": dict(
                sorted(Counter(item.get("predicate_label") for row in anchor_preview_rows for item in row.get("target_rows_preview", [])).items())
            ),
            "label_counts_if_materialized": dict(
                sorted((str(key), value) for key, value in Counter(item.get("compatibility_y") for row in anchor_preview_rows for item in row.get("target_rows_preview", [])).items())
            ),
        },
        "materialization_contract": contract,
        "path_decision": decision,
        "output_paths": {
            "materialization_contract": rel_path(output_dir / "materialization_contract.json"),
            "row_schema": rel_path(output_dir / "row_schema.json"),
            "blocked_fields": rel_path(output_dir / "blocked_fields.csv"),
            "output_manifest_contract": rel_path(output_dir / "output_manifest_contract.json"),
            "downstream_gates": rel_path(output_dir / "downstream_gates.csv"),
            "plan_summary": rel_path(output_dir / "plan_summary.csv"),
            "path_decision": rel_path(output_dir / "path_decision.json"),
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "boundary": {
            "split": "train_only_candidate_materialization_plan",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_candidate_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
    }

    write_json(output_dir / "materialization_contract.json", contract)
    write_json(output_dir / "row_schema.json", schema)
    write_csv(output_dir / "blocked_fields.csv", blocked_fields())
    write_json(output_dir / "output_manifest_contract.json", manifest_contract)
    write_csv(output_dir / "downstream_gates.csv", gates)
    write_csv(output_dir / "plan_summary.csv", plan_rows)
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
