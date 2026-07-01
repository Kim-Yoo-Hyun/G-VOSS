#!/usr/bin/env python3
"""Plan R1 close-by geometry-support route materialization."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_ROUTE_PLAN_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit"
)
DEFAULT_MANIFEST_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze"
)
DEFAULT_CLOSE_BY_MATERIALIZATION_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization"
)
DEFAULT_CLOSE_BY_AUDIT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit"
)
DEFAULT_CLOSE_BY_DECISION_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan"
)

EXPECTED_ROUTE_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_route_specific_target_materialization_plan_after_manifest_audit_ready"
)
EXPECTED_ROUTE_PLAN_NEXT = "compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan"
EXPECTED_MANIFEST_STATUS = "h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_ready"
EXPECTED_CLOSE_BY_MATERIALIZATION_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_CLOSE_BY_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_blocked_distance_rule_shortcut"
)
EXPECTED_CLOSE_BY_DECISION_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_path_decision_freeze_close_by_select_support_contact_individual_probe"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan_input_errors"
SELECTED_PATH = "materialize_r1_close_by_as_geometry_support_route_root_not_interaction_claim"
NEXT_TODO = "compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-plan-dir", type=Path, default=DEFAULT_ROUTE_PLAN_DIR)
    parser.add_argument("--manifest-dir", type=Path, default=DEFAULT_MANIFEST_DIR)
    parser.add_argument("--close-by-materialization-dir", type=Path, default=DEFAULT_CLOSE_BY_MATERIALIZATION_DIR)
    parser.add_argument("--close-by-audit-dir", type=Path, default=DEFAULT_CLOSE_BY_AUDIT_DIR)
    parser.add_argument("--close-by-decision-dir", type=Path, default=DEFAULT_CLOSE_BY_DECISION_DIR)
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
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def r1_row(rows: list[dict[str, str]]) -> dict[str, str]:
    for row in rows:
        if row.get("route_id") == "R1":
            return row
    return {}


def boundary_false_errors(summary: dict[str, Any], keys: list[str], prefix: str) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    boundary = summary.get("boundary", {})
    for key in keys:
        if key in {"validation_usage", "test_usage"} and "validation_or_test_used" in boundary:
            if boundary.get("validation_or_test_used") is not False:
                errors.append(
                    {
                        "error_type": f"{prefix}_boundary_not_false",
                        "key": "validation_or_test_used",
                        "actual": boundary.get("validation_or_test_used"),
                    }
                )
            continue
        if boundary.get(key) is not False:
            errors.append({"error_type": f"{prefix}_boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def validate_inputs(
    route_summary: dict[str, Any],
    manifest_summary: dict[str, Any],
    close_summary: dict[str, Any],
    audit_summary: dict[str, Any],
    decision_summary: dict[str, Any],
    route_materialization_rows: list[dict[str, str]],
    route_output_rows: list[dict[str, str]],
    first_followup_rows: list[dict[str, str]],
    target_manifest_rows: list[dict[str, str]],
    field_manifest_rows: list[dict[str, str]],
    control_manifest_rows: list[dict[str, str]],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if route_summary.get("status") != EXPECTED_ROUTE_PLAN_STATUS:
        errors.append({"error_type": "unexpected_route_plan_status", "actual": route_summary.get("status")})
    if route_summary.get("next_todo") != EXPECTED_ROUTE_PLAN_NEXT:
        errors.append({"error_type": "unexpected_route_plan_next_todo", "actual": route_summary.get("next_todo")})
    if route_summary.get("validation_errors") != 0:
        errors.append({"error_type": "route_plan_validation_errors_present", "actual": route_summary.get("validation_errors")})
    if read_jsonl(args.route_plan_dir / "validation_errors.jsonl"):
        errors.append({"error_type": "route_plan_validation_error_rows_present"})

    if manifest_summary.get("status") != EXPECTED_MANIFEST_STATUS:
        errors.append({"error_type": "unexpected_manifest_status", "actual": manifest_summary.get("status")})
    if manifest_summary.get("validation_errors") != 0:
        errors.append({"error_type": "manifest_validation_errors_present", "actual": manifest_summary.get("validation_errors")})

    if close_summary.get("status") != EXPECTED_CLOSE_BY_MATERIALIZATION_STATUS:
        errors.append({"error_type": "unexpected_close_by_materialization_status", "actual": close_summary.get("status")})
    if close_summary.get("validation_errors") != 0:
        errors.append({"error_type": "close_by_materialization_validation_errors_present", "actual": close_summary.get("validation_errors")})
    if read_jsonl(args.close_by_materialization_dir / "validation_errors.jsonl"):
        errors.append({"error_type": "close_by_materialization_validation_error_rows_present"})

    if audit_summary.get("status") != EXPECTED_CLOSE_BY_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_close_by_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("validation_errors") != 0:
        errors.append({"error_type": "close_by_audit_validation_errors_present", "actual": audit_summary.get("validation_errors")})
    if audit_summary.get("critical_blockers", 0) < 5:
        errors.append({"error_type": "distance_rule_dominance_not_confirmed", "actual": audit_summary.get("critical_blockers")})

    if decision_summary.get("status") != EXPECTED_CLOSE_BY_DECISION_STATUS:
        errors.append({"error_type": "unexpected_close_by_decision_status", "actual": decision_summary.get("status")})
    if decision_summary.get("validation_errors") != 0:
        errors.append({"error_type": "close_by_decision_validation_errors_present", "actual": decision_summary.get("validation_errors")})

    for label, summary in [
        ("route_plan", route_summary),
        ("close_by_materialization", close_summary),
        ("close_by_audit", audit_summary),
        ("close_by_decision", decision_summary),
    ]:
        errors.extend(
            boundary_false_errors(
                summary,
                ["h001_artifacts_modified", "validation_usage", "test_usage"],
                label,
            )
        )

    r1_materialization = r1_row(route_materialization_rows)
    r1_output = r1_row(route_output_rows)
    r1_target = r1_row(target_manifest_rows)
    r1_field = r1_row(field_manifest_rows)
    r1_control = r1_row(control_manifest_rows)
    r1_followups = [row for row in first_followup_rows if row.get("route_id") == "R1"]

    if not r1_materialization:
        errors.append({"error_type": "missing_r1_materialization_plan_row"})
    elif r1_materialization.get("target_axis") != "geometry_support":
        errors.append({"error_type": "r1_target_axis_not_geometry_support", "actual": r1_materialization.get("target_axis")})
    if not r1_output:
        errors.append({"error_type": "missing_r1_output_contract_row"})
    if not r1_target:
        errors.append({"error_type": "missing_r1_target_manifest_row"})
    elif r1_target.get("route_type") != "geometry_only_learned_evaluated_route":
        errors.append({"error_type": "r1_route_type_not_geometry_only", "actual": r1_target.get("route_type")})
    if not r1_field:
        errors.append({"error_type": "missing_r1_field_manifest_row"})
    if not r1_control:
        errors.append({"error_type": "missing_r1_control_manifest_row"})
    if not r1_followups:
        errors.append({"error_type": "missing_r1_first_followup_row"})

    counts = close_summary.get("row_counts", {})
    expected_counts = {
        "primary_binary_rows": 800,
        "abstain_qe_rows": 240,
        "raw_distance_diagnostic_rows": 240,
        "gt_geometry_conflict_audit_rows": 4,
        "total_rows": 1284,
    }
    for key, expected in expected_counts.items():
        if counts.get(key) != expected:
            errors.append({"error_type": "unexpected_close_by_row_count", "key": key, "actual": counts.get(key), "expected": expected})
    return errors


def route_input_reuse_plan(args: argparse.Namespace) -> list[dict[str, Any]]:
    return [
        {
            "source_artifact": "compatibility_dataset_v3_proximity_close_by_candidate_materialization",
            "path": rel_path(args.close_by_materialization_dir),
            "reuse_role": "normalize_existing_rows_into_r1_route_root",
            "reuse_policy": "reuse rows, but rename C_e_label to geometry_support_label and mark C_e interaction as not_applicable",
            "allowed_now": True,
        },
        {
            "source_artifact": "compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit",
            "path": rel_path(args.close_by_audit_dir),
            "reuse_role": "convert distance-rule blocker into expected geometry-only route diagnostic",
            "reuse_policy": "distance-only dominance is expected for R1, not a compatibility success",
            "allowed_now": True,
        },
        {
            "source_artifact": "compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit",
            "path": rel_path(args.close_by_decision_dir),
            "reuse_role": "preserve old claim boundary",
            "reuse_policy": "old decision still blocks T_e x G_e claim and learned interaction smoke",
            "allowed_now": True,
        },
        {
            "source_artifact": "route_specific_target_manifest_plan_after_schema_freeze",
            "path": rel_path(args.manifest_dir),
            "reuse_role": "R1 schema and target contract",
            "reuse_policy": "enforce target_axis=geometry_support and route_type=geometry_only",
            "allowed_now": True,
        },
    ]


def row_component_plan(close_counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "component": "primary_geometry_support_binary",
            "source_subset": "primary_binary",
            "planned_rows": close_counts.get("primary_binary_rows", 800),
            "positive_rows": 400,
            "negative_rows": 400,
            "target_field": "geometry_support_label",
            "label_space": "geometry_supported; geometry_unsupported",
            "model_use": "geometry-only route evaluation",
            "must_not_claim": "predicate_geometry_interaction",
        },
        {
            "component": "observability_abstain_qe",
            "source_subset": "abstain_qe",
            "planned_rows": close_counts.get("abstain_qe_rows", 240),
            "positive_rows": 0,
            "negative_rows": 0,
            "target_field": "p_obs_label",
            "label_space": "observable_but_unlabeled; ambiguous; uncertain_or_unobservable",
            "model_use": "Q_e / abstain diagnostics only",
            "must_not_claim": "relation_truth_from_Q_e",
        },
        {
            "component": "raw_distance_diagnostic",
            "source_subset": "raw_distance_diagnostic",
            "planned_rows": close_counts.get("raw_distance_diagnostic_rows", 240),
            "positive_rows": 120,
            "negative_rows": 120,
            "target_field": "geometry_support_label",
            "label_space": "geometry_supported; geometry_unsupported",
            "model_use": "raw-vs-normalized distance and scale diagnostics",
            "must_not_claim": "main_interaction_target",
        },
        {
            "component": "gt_geometry_conflict_audit",
            "source_subset": "gt_geometry_conflict_audit",
            "planned_rows": close_counts.get("gt_geometry_conflict_audit_rows", 4),
            "positive_rows": 0,
            "negative_rows": 0,
            "target_field": "audit_required",
            "label_space": "audit_required",
            "model_use": "manual audit / no training",
            "must_not_claim": "negative_training_rows",
        },
    ]


def model_safe_schema_plan() -> list[dict[str, Any]]:
    return [
        {
            "block": "T_e",
            "route_policy": "annotation_only",
            "fields": "predicate_text; predicate_label; predicate_family; subject_class_text; object_class_text",
            "allowed_in_route_score": False,
            "allowed_in_baseline": True,
            "reason": "R1 tests geometry-support route, not predicate-geometry interaction",
        },
        {
            "block": "Z_e",
            "route_policy": "source_baseline_only",
            "fields": "source_id; semantic_score_raw; semantic_score_norm; rank_in_context; predicate_rank_for_pair; rank_band",
            "allowed_in_route_score": False,
            "allowed_in_baseline": True,
            "reason": "source confidence can be compared, but cannot define geometry support",
        },
        {
            "block": "G_e",
            "route_policy": "primary_route_input",
            "fields": "distance_xy; distance_3d; normalized_distance_xy; normalized_distance_3d; center_delta_z; projected_iou_xy; overlap ratios; scale_proxy fields if available",
            "allowed_in_route_score": True,
            "allowed_in_baseline": True,
            "reason": "R1 route is geometry-decidable by design",
        },
        {
            "block": "Q_e",
            "route_policy": "abstain_and_coverage",
            "fields": "geometry_available; geometry_checkable; feature_complete; feature_missing_count; boundary_ambiguity; coverage_state if available",
            "allowed_in_route_score": "for abstain only",
            "allowed_in_baseline": True,
            "reason": "Q_e decides whether geometry evidence is usable, not whether relation is true",
        },
        {
            "block": "C_e",
            "route_policy": "not_applicable_for_interaction",
            "fields": "geometry_support_label can be stored separately; C_e_interaction_label must be absent or not_applicable",
            "allowed_in_route_score": False,
            "allowed_in_baseline": False,
            "reason": "avoid misrepresenting close by as T_e x G_e evidence",
        },
    ]


def hidden_and_blocked_field_plan() -> list[dict[str, Any]]:
    return [
        {
            "field_group": "identity",
            "fields": "row_id; scan_id; subgraph_id; subject_id; object_id; directed_pair_id; prediction_id; row_key",
            "allowed_model_input": False,
            "audit_use": "leakage and grouping only",
        },
        {
            "field_group": "construction",
            "fields": "candidate_bucket; geometry_status; distance_bucket; label_match_status; raw_distance_bin; norm_distance_bin",
            "allowed_model_input": False,
            "audit_use": "quota and shortcut audit only",
        },
        {
            "field_group": "thresholds",
            "fields": "near_threshold_normalized_distance_xy; far_threshold_normalized_distance_xy; bin widths; p_geom_valid rule bucket",
            "allowed_model_input": False,
            "audit_use": "route construction reproducibility and baseline diagnostics",
        },
        {
            "field_group": "target_labels",
            "fields": "geometry_support_label; p_obs_label; p_rel_label; audit_required",
            "allowed_model_input": False,
            "audit_use": "supervision and evaluation only",
        },
    ]


def distance_scale_coverage_control_plan() -> list[dict[str, Any]]:
    return [
        {
            "control": "distance_geometry_baseline",
            "purpose": "confirm G_e distance solves or nearly solves the geometry_support target",
            "pass_condition": "distance/normalized-distance AUROC remains high and is reported as geometry-only route evidence",
            "failure_meaning": "target no longer measures close-by geometry support",
        },
        {
            "control": "scale_control",
            "purpose": "separate raw distance from object-scale-normalized distance",
            "pass_condition": "report raw vs normalized distance, scale-bin counts, and scale-only probe",
            "failure_meaning": "route may be object-size or class-size shortcut instead of proximity geometry",
        },
        {
            "control": "coverage_control",
            "purpose": "separate G_e from Q_e",
            "pass_condition": "missing/ambiguous geometry rows go to abstain or diagnostic, not binary accept/reject",
            "failure_meaning": "Q_e is being used as truth instead of observability",
        },
        {
            "control": "source_score_rank_control",
            "purpose": "ensure source confidence is not defining geometry_support",
            "pass_condition": "Z_e-only remains diagnostic/baseline and cannot replace G_e route score",
            "failure_meaning": "target is contaminated by source confidence",
        },
        {
            "control": "class_pair_control",
            "purpose": "ensure object category pairs do not explain the route without geometry",
            "pass_condition": "class-pair-only stays secondary and is reported as leakage risk if high",
            "failure_meaning": "route target may be category co-occurrence rather than geometry support",
        },
        {
            "control": "shuffled_g_wrong_pair_geometry",
            "purpose": "confirm route uses the correct object-pair geometry",
            "pass_condition": "shuffled-G and wrong-pair geometry degrade relative to true G_e",
            "failure_meaning": "route score may not be pair-specific geometry",
        },
        {
            "control": "wording_guard",
            "purpose": "prevent overclaiming close by as interaction evidence",
            "pass_condition": "all reports call R1 geometry-only learned/evaluated route or claim-control evidence",
            "failure_meaning": "paper claim drifts back to fixed universal fusion or T_e x G_e interaction",
        },
    ]


def output_contract() -> list[dict[str, Any]]:
    route_root = "artifacts/route_specific_targets/r1_proximity/"
    return [
        {
            "file": "summary.json",
            "path": route_root + "summary.json",
            "required": True,
            "content": "status, selected_path, row counts, source artifacts, boundary, validation_errors",
        },
        {
            "file": "schema.json",
            "path": route_root + "schema.json",
            "required": True,
            "content": "T_e/Z_e/G_e/Q_e/C_e route policy and blocked fields",
        },
        {
            "file": "model_safe_rows.jsonl",
            "path": route_root + "model_safe_rows.jsonl",
            "required": True,
            "content": "rows with geometry_support_label target, no identity/construction leaks",
        },
        {
            "file": "hidden_manifest.jsonl",
            "path": route_root + "hidden_manifest.jsonl",
            "required": True,
            "content": "identity, construction buckets, threshold bins, source snapshots",
        },
        {
            "file": "audit_view.jsonl",
            "path": route_root + "audit_view.jsonl",
            "required": True,
            "content": "human-readable audit rows with hidden controls, not model input",
        },
        {
            "file": "control_manifest.json",
            "path": route_root + "control_manifest.json",
            "required": True,
            "content": "distance, scale, coverage, source, class-pair, shuffled-G, wrong-pair controls",
        },
        {
            "file": "split_or_group_manifest.json",
            "path": route_root + "split_or_group_manifest.json",
            "required": True,
            "content": "train-only grouping keys and leakage guard metadata",
        },
        {
            "file": "report.md",
            "path": route_root + "report.md",
            "required": True,
            "content": "route interpretation, counts, controls, and claim boundary",
        },
        {
            "file": "validation_errors.jsonl",
            "path": route_root + "validation_errors.jsonl",
            "required": True,
            "content": "empty when route materialization passes",
        },
    ]


def next_gate_plan() -> list[dict[str, Any]]:
    return [
        {
            "gate": "materialize_route_root",
            "next_todo": NEXT_TODO,
            "allowed": True,
            "condition": "this plan passes with validation_errors=0",
        },
        {
            "gate": "schema_shortcut_audit",
            "next_todo": "compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization",
            "allowed": "after route materialization",
            "condition": "route root exists and blocked model input fields are absent",
        },
        {
            "gate": "learned_smoke",
            "next_todo": "not_immediate",
            "allowed": False,
            "condition": "not needed to prove R1 interaction; only geometry route baseline/control may be run later",
        },
        {
            "gate": "paper_claim",
            "next_todo": "not_immediate",
            "allowed": False,
            "condition": "R1 alone is claim-control/general route evidence, not H002 main mechanism",
        },
    ]


def render_report(summary: dict[str, Any]) -> str:
    return f"""# H002 R1 Close-By Geometry-Support Materialization Plan

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Purpose

This artifact converts the old `close by` diagnostic branch into the R1
route-specific materialization plan. It does not materialize rows and does not
run a model. The key correction is that `close by` is now a geometry-only
learned/evaluated route, not `T_e x G_e` interaction evidence.

## Planned Route

```text
route_id = R1
family = proximity
relation = close by
target_axis = geometry_support
planned_route_root = artifacts/route_specific_targets/r1_proximity/
```

## Existing Row Material To Reuse

| Component | Rows | Role |
| --- | ---: | --- |
| primary geometry-support binary | {summary['row_counts']['primary_binary_rows']} | geometry_supported vs geometry_unsupported |
| Q_e / abstain diagnostics | {summary['row_counts']['abstain_qe_rows']} | coverage, ambiguity, or unobservable cases |
| raw-distance diagnostic | {summary['row_counts']['raw_distance_diagnostic_rows']} | raw-vs-normalized distance and scale control |
| GT/geometry conflict audit | {summary['row_counts']['gt_geometry_conflict_audit_rows']} | audit only, not training |

## Critical Boundary

- Distance dominance is expected for this route.
- Distance dominance must not be reported as predicate-geometry interaction.
- `T_e` is annotation/baseline only for R1.
- `Z_e` is source-baseline only for R1.
- `G_e` is the primary route evidence.
- `Q_e` controls abstain/coverage, not relation truth.

## Controls Required Before Any Result Wording

1. distance and normalized-distance route baseline
2. raw-distance vs object-scale-normalized distance comparison
3. coverage / ambiguity / missing-geometry abstain split
4. source score and rank-only baseline
5. class-pair and endpoint leakage audit
6. shuffled-G and wrong-pair geometry controls
7. wording guard: R1 is geometry-only route evidence

## Boundary

Allowed now:

- route materialization plan
- route root output contract
- control/schema planning

Blocked now:

- row materialization
- learned smoke runner
- calibrated `p_rel` / `p_obs`
- paper-level result claim
- `T_e x G_e` interaction claim for `close by`

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()

    route_summary = read_json(args.route_plan_dir / "summary.json")
    manifest_summary = read_json(args.manifest_dir / "summary.json")
    close_summary = read_json(args.close_by_materialization_dir / "summary.json")
    audit_summary = read_json(args.close_by_audit_dir / "summary.json")
    decision_summary = read_json(args.close_by_decision_dir / "summary.json")

    route_materialization_rows = read_csv(args.route_plan_dir / "route_materialization_plan.csv")
    route_output_rows = read_csv(args.route_plan_dir / "route_output_contract.csv")
    first_followup_rows = read_csv(args.route_plan_dir / "first_route_followup_plan.csv")
    target_manifest_rows = read_csv(args.manifest_dir / "route_target_manifest.csv")
    field_manifest_rows = read_csv(args.manifest_dir / "route_field_manifest.csv")
    control_manifest_rows = read_csv(args.manifest_dir / "route_control_manifest.csv")

    errors = validate_inputs(
        route_summary,
        manifest_summary,
        close_summary,
        audit_summary,
        decision_summary,
        route_materialization_rows,
        route_output_rows,
        first_followup_rows,
        target_manifest_rows,
        field_manifest_rows,
        control_manifest_rows,
        args,
    )

    row_counts = close_summary.get("row_counts", {})
    status = STATUS_READY if not errors else STATUS_ERRORS
    output_paths = {
        "summary": args.output_dir / "summary.json",
        "report": args.output_dir / "report.md",
        "route_input_reuse_plan": args.output_dir / "route_input_reuse_plan.csv",
        "row_component_plan": args.output_dir / "row_component_plan.csv",
        "model_safe_schema_plan": args.output_dir / "model_safe_schema_plan.csv",
        "hidden_and_blocked_field_plan": args.output_dir / "hidden_and_blocked_field_plan.csv",
        "distance_scale_coverage_control_plan": args.output_dir / "distance_scale_coverage_control_plan.csv",
        "route_output_contract": args.output_dir / "route_output_contract.csv",
        "next_gate_plan": args.output_dir / "next_gate_plan.csv",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed_now": False,
            "runs_model": False,
            "test_usage": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_artifacts": {
            "route_plan": rel_path(args.route_plan_dir),
            "manifest": rel_path(args.manifest_dir),
            "close_by_materialization": rel_path(args.close_by_materialization_dir),
            "close_by_schema_audit": rel_path(args.close_by_audit_dir),
            "close_by_path_decision": rel_path(args.close_by_decision_dir),
        },
        "next_todo": NEXT_TODO,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "planned_route": {
            "route_id": "R1",
            "family": "proximity",
            "relations": "close by",
            "target_axis": "geometry_support",
            "route_type": "geometry_only_learned_evaluated_route",
            "planned_route_root": "artifacts/route_specific_targets/r1_proximity/",
        },
        "row_counts": row_counts,
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH,
        "status": status,
        "validation_errors": len(errors),
    }

    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], errors)
    write_csv(output_paths["route_input_reuse_plan"], route_input_reuse_plan(args))
    write_csv(output_paths["row_component_plan"], row_component_plan(row_counts))
    write_csv(output_paths["model_safe_schema_plan"], model_safe_schema_plan())
    write_csv(output_paths["hidden_and_blocked_field_plan"], hidden_and_blocked_field_plan())
    write_csv(output_paths["distance_scale_coverage_control_plan"], distance_scale_coverage_control_plan())
    write_csv(output_paths["route_output_contract"], output_contract())
    write_csv(output_paths["next_gate_plan"], next_gate_plan())
    output_paths["report"].write_text(render_report(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
