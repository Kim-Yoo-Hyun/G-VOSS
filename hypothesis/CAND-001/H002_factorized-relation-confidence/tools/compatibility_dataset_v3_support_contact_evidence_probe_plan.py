#!/usr/bin/env python3
"""Write the support/contact evidence probe plan after the v3 result review."""

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

DEFAULT_DECISION_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_result_review_and_family_extension_decision"
DEFAULT_V2_CAPACITY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_capacity_scan"
DEFAULT_V2_CANDIDATE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_candidate_materialization"
DEFAULT_V2_FAILURE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_failure_analysis"
DEFAULT_V2_SCHEMA_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_schema_shortcut_audit"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_evidence_probe_plan"

EXPECTED_DECISION_STATUS = "h002_compatibility_dataset_v3_result_review_accept_mechanism_select_support_contact_probe"
EXPECTED_DECISION_NEXT = "compatibility_dataset_v3_support_contact_evidence_probe_plan"
EXPECTED_SELECTED_FAMILY = "support_contact"

EXPECTED_V2_CAPACITY_STATUS = "h002_compatibility_dataset_v2_capacity_scan_passed_with_controls_ready_for_candidate_materialization"
EXPECTED_V2_CANDIDATE_STATUS = "h002_compatibility_dataset_v2_candidate_materialization_ready_for_schema_shortcut_audit"
EXPECTED_V2_FAILURE_STATUS = "h002_compatibility_dataset_v2_failure_analysis_ready"
EXPECTED_V2_SCHEMA_STATUS = "h002_compatibility_dataset_v2_schema_shortcut_audit_requires_sanitized_view"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_evidence_probe_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_evidence_probe_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_evidence_probe_plan_input_errors"
SELECTED_ROUTE = "support_contact_evidence_inventory_before_materialization_or_smoke"
NEXT_TODO = "compatibility_dataset_v3_support_contact_evidence_probe_runner"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--decision-dir", type=Path, default=DEFAULT_DECISION_DIR)
    parser.add_argument("--v2-capacity-dir", type=Path, default=DEFAULT_V2_CAPACITY_DIR)
    parser.add_argument("--v2-candidate-dir", type=Path, default=DEFAULT_V2_CANDIDATE_DIR)
    parser.add_argument("--v2-failure-dir", type=Path, default=DEFAULT_V2_FAILURE_DIR)
    parser.add_argument("--v2-schema-dir", type=Path, default=DEFAULT_V2_SCHEMA_DIR)
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
    decision: dict[str, Any],
    capacity: dict[str, Any],
    candidate: dict[str, Any],
    failure: dict[str, Any],
    schema: dict[str, Any],
    v2_validation_rows: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if decision.get("status") != EXPECTED_DECISION_STATUS:
        errors.append({"error_type": "unexpected_decision_status", "actual": decision.get("status")})
    if decision.get("next_todo") != EXPECTED_DECISION_NEXT:
        errors.append({"error_type": "unexpected_decision_next", "actual": decision.get("next_todo")})
    if decision.get("selected_next_family") != EXPECTED_SELECTED_FAMILY:
        errors.append({"error_type": "unexpected_selected_family", "actual": decision.get("selected_next_family")})
    if decision.get("validation_errors") != 0:
        errors.append({"error_type": "decision_validation_errors", "actual": decision.get("validation_errors")})

    expected_statuses = [
        ("v2_capacity", capacity, EXPECTED_V2_CAPACITY_STATUS),
        ("v2_candidate", candidate, EXPECTED_V2_CANDIDATE_STATUS),
        ("v2_failure", failure, EXPECTED_V2_FAILURE_STATUS),
        ("v2_schema", schema, EXPECTED_V2_SCHEMA_STATUS),
    ]
    for name, summary, expected in expected_statuses:
        if summary.get("status") != expected:
            errors.append({"error_type": "unexpected_input_status", "input": name, "actual": summary.get("status"), "expected": expected})
        if summary.get("validation_errors") not in (0, None):
            errors.append({"error_type": "input_validation_errors", "input": name, "actual": summary.get("validation_errors")})
    for name, rows in v2_validation_rows.items():
        if rows:
            errors.append({"error_type": "input_validation_error_rows_present", "input": name, "rows": len(rows)})

    if failure.get("primary_cause") != "target_is_geometry_perturbation_detection_not_predicate_conditioned_compatibility":
        errors.append({"error_type": "unexpected_v2_failure_cause", "actual": failure.get("primary_cause")})
    return errors


def support_capacity_snapshot(capacity: dict[str, Any]) -> dict[str, Any]:
    family_rows = {
        row.get("relation_family"): row
        for row in capacity.get("family_capacity", [])
    }
    quota_rows = {
        row.get("relation_family"): row
        for row in capacity.get("quota_feasibility", [])
    }
    support = family_rows.get("support_contact", {})
    quota = quota_rows.get("support_contact", {})
    return {
        "eligible_positive": support.get("eligible_positive"),
        "eligible_negative": support.get("eligible_negative"),
        "positive_distinct_directed_pairs": support.get("positive_distinct_directed_pairs"),
        "negative_distinct_directed_pairs": support.get("negative_distinct_directed_pairs"),
        "positive_distinct_visible_pairs": support.get("positive_distinct_visible_pairs"),
        "negative_distinct_visible_pairs": support.get("negative_distinct_visible_pairs"),
        "predicate_positive_counts": quota.get("predicate_positive_counts"),
        "predicate_negative_counts": quota.get("predicate_negative_counts"),
        "direct_hl_lh_predicate_balance_pass": quota.get("direct_hl_lh_predicate_balance_pass"),
        "generated_counterfactual_policy": quota.get("generated_counterfactual_policy"),
    }


def support_candidate_snapshot(candidate: dict[str, Any]) -> dict[str, Any]:
    counts = candidate.get("counts", {})
    raw = candidate.get("raw_witness_join", {})
    return {
        "support_rows": counts.get("by_family_label", {}).get("support_contact|positive", 0)
        + counts.get("by_family_label", {}).get("support_contact|counterfactual_negative", 0),
        "support_positive": counts.get("by_family_label", {}).get("support_contact|positive"),
        "support_negative": counts.get("by_family_label", {}).get("support_contact|counterfactual_negative"),
        "support_predicate_counts": {
            key: value
            for key, value in counts.get("by_predicate_label", {}).items()
            if str(key).startswith("support_contact|")
        },
        "support_counterfactual_counts": {
            key: value
            for key, value in counts.get("by_counterfactual_type", {}).items()
            if str(key).startswith("support_contact|")
        },
        "raw_fields": raw.get("raw_fields", []),
        "raw_witness_matched_support_rows": raw.get("matched_by_family", {}).get("support_contact"),
    }


def support_row_feature_snapshot(sanitized_rows: list[dict[str, Any]]) -> dict[str, Any]:
    support_rows = [
        row
        for row in sanitized_rows
        if row.get("T_e", {}).get("relation_family") == "support_contact"
    ]
    g_counts: Counter[str] = Counter()
    q_counts: Counter[str] = Counter()
    predicate_label_counts: Counter[str] = Counter()
    for row in support_rows:
        label = row.get("y_compatibility")
        pred = row.get("T_e", {}).get("predicate_label")
        predicate_label_counts[f"{pred}|{label}"] += 1
        g_features = row.get("G_e_numeric", {}).get("geometry_features", {})
        for key in g_features:
            g_counts[key] += 1
        for key in row.get("Q_e_sanitized", {}):
            q_counts[key] += 1
    return {
        "support_rows": len(support_rows),
        "predicate_label_counts": dict(sorted(predicate_label_counts.items())),
        "available_g_numeric_fields": dict(sorted(g_counts.items())),
        "available_q_fields": dict(sorted(q_counts.items())),
        "has_role_or_orientation_field": any("orientation" in key or "role" in key or "pose" in key for key in g_counts),
        "has_contact_direction_field": any("contact_direction" in key for key in g_counts),
        "has_surface_normal_field": any(key in {"normal", "surface_normal", "subject_normal", "object_normal"} or key.endswith("_normal") for key in g_counts),
        "has_mesh_or_visual_q_field": any("mesh" in key or "view" in key or "visual" in key for key in q_counts),
    }


def failure_snapshot(failure: dict[str, Any]) -> dict[str, Any]:
    support_fp = None
    feature_shifts = None
    for finding in failure.get("key_findings", []):
        if finding.get("claim") == "Support/contact drives most geometry signal.":
            support_fp = finding.get("value")
        if finding.get("claim") == "Top numeric feature shifts are geometry distribution shifts, not predicate-conditioned evidence.":
            feature_shifts = finding.get("value")
    return {
        "primary_cause": failure.get("primary_cause"),
        "support_contact_failure": support_fp,
        "top_feature_shifts": feature_shifts[:8] if isinstance(feature_shifts, list) else feature_shifts,
        "target_redesign_requirements": failure.get("target_redesign_requirements", []),
    }


def evidence_axis_rows(feature_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    g_fields = set(feature_snapshot["available_g_numeric_fields"])
    q_fields = set(feature_snapshot["available_q_fields"])
    return [
        {
            "axis": "distance_and_overlap",
            "status": "available_but_insufficient_as_primary",
            "observed_fields": sorted(field for field in g_fields if "distance" in field or "overlap" in field or "iou" in field),
            "role_in_next_probe": "baseline and shortcut-risk signal",
            "reason": "v2 showed this can solve generated negatives as generic geometry perturbation.",
        },
        {
            "axis": "vertical_gap_and_support_order",
            "status": "available_partial",
            "observed_fields": sorted(field for field in g_fields if "vertical" in field or "bottom" in field or "top" in field or "center_delta_z" in field),
            "role_in_next_probe": "candidate support-direction proxy",
            "reason": "May help support/contact, but still not enough to distinguish standing/lying/support role by itself.",
        },
        {
            "axis": "role_orientation_pose",
            "status": "missing_in_current_numeric_view",
            "observed_fields": sorted(field for field in g_fields if "role" in field or "orientation" in field or "pose" in field),
            "role_in_next_probe": "required for standing vs lying feasibility",
            "reason": "Predicate semantics for standing/lying likely need object orientation or pose beyond OBB gap/overlap.",
        },
        {
            "axis": "contact_direction_surface_normal",
            "status": "missing_or_not_explicit",
            "observed_fields": sorted(
                field
                for field in g_fields
                if field in {"normal", "surface_normal", "subject_normal", "object_normal"}
                or field.endswith("_normal")
                or "contact_direction" in field
            ),
            "role_in_next_probe": "required for support direction and surface support",
            "reason": "Without surface normals/contact direction, support/contact may remain generic contact detection.",
        },
        {
            "axis": "mesh_visual_multiview",
            "status": "missing_in_v2_sanitized_view",
            "observed_fields": sorted(field for field in q_fields if "mesh" in field or "view" in field or "visual" in field),
            "role_in_next_probe": "decide whether new evidence axis is required",
            "reason": "Attachment/contact semantics may need visual/mesh evidence; current Q_e only reports raw witness coverage.",
        },
        {
            "axis": "source_object_structural_shortcuts",
            "status": "must_control",
            "observed_fields": ["subject/object labels", "source rank", "hard room surface filter counts"],
            "role_in_next_probe": "shortcut audit",
            "reason": "Support/contact can be dominated by object categories and structural objects such as floor/wall/ceiling.",
        },
    ]


def probe_task_rows() -> list[dict[str, Any]]:
    return [
        {
            "task": "source_inventory",
            "input": "v2 capacity scan + match_rows path",
            "question": "How many support/contact rows exist for standing on, lying on, supported by under full train-side artifacts?",
            "output": "counts by predicate, queue type, scan, directed pair, visible pair, hard room-surface filter",
            "pass_condition": "sufficient rows exist for at least one non-generated controlled candidate route",
        },
        {
            "task": "field_availability_audit",
            "input": "v2 sanitized_model_view + raw witness fields",
            "question": "Which evidence axes are actually present beyond distance/overlap/gap?",
            "output": "availability table for role/orientation/contact direction/surface normal/mesh/visual",
            "pass_condition": "at least one evidence axis beyond generic distance/overlap is present, or probe explicitly routes to visual/mesh materialization",
        },
        {
            "task": "same_or_near_geometry_group_probe",
            "input": "full train match_rows / candidate pools",
            "question": "Can same-G or near-G groups be formed where predicate changes validity without distribution shift?",
            "output": "candidate group counts for same directed pair, same visible pair, and near-G bins",
            "pass_condition": "target design predicts G_e-only near chance before learned smoke",
        },
        {
            "task": "negative_policy_audit",
            "input": "v2 counterfactual groups and failure analysis",
            "question": "Which negative policies are allowed as primary versus controls?",
            "output": "primary-negative allowed list and control-only list",
            "pass_condition": "gap/overlap perturbation, wrong-pair, and shuffled-geometry are control-only, not primary target negatives",
        },
        {
            "task": "shortcut_precheck",
            "input": "candidate group metadata after probe",
            "question": "Can object class, structural objects, predicate, source rank, or visible pair predict the target?",
            "output": "majority-rule and threshold shortcut probes",
            "pass_condition": "high/medium shortcut axes are either balanced or route is diagnostic-only",
        },
    ]


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "direct_support_contact_smoke_from_v2_rows",
            "verdict": "reject",
            "reason": "v2 failure showed support/contact generated negatives are geometry-perturbation dominated.",
            "next_action": "do_not_train",
        },
        {
            "route": "same_geometry_support_contact_multi_predicate",
            "verdict": "probe",
            "reason": "Best analogue to v3 relative-vertical, but likely needs role/orientation evidence.",
            "next_action": "scan_same_or_near_G_candidate_capacity",
        },
        {
            "route": "near_geometry_matched_support_contact",
            "verdict": "probe",
            "reason": "May be feasible if exact same-G is too sparse; must prove G_e-only remains near chance.",
            "next_action": "define_near_G_bins_and_shortcut_controls",
        },
        {
            "route": "visual_mesh_evidence_axis_before_support_smoke",
            "verdict": "conditional_select",
            "reason": "If role/orientation/contact direction is absent in current numeric fields, new evidence is required before fair support/contact C_e.",
            "next_action": "route_to_visual_mesh_materialization_plan_if_probe_fails",
        },
        {
            "route": "keep_support_contact_secondary",
            "verdict": "fallback",
            "reason": "If probe cannot find non-shortcut evidence axes, support/contact should not be used as primary H002 evidence.",
            "next_action": "retain_relative_vertical_as_mechanism_proof_and_defer_family_extension",
        },
    ]


def blocked_actions() -> list[dict[str, Any]]:
    return [
        {
            "action": "run_support_contact_learned_smoke_now",
            "blocked": True,
            "reason": "Would likely repeat v2 geometry perturbation detection.",
        },
        {
            "action": "use_contact_gap_or_overlap_perturbation_as_primary_negative",
            "blocked": True,
            "reason": "This is too easy and should be a sanity control only.",
        },
        {
            "action": "claim_support_contact_generality_from_v2_smoke",
            "blocked": True,
            "reason": "v2 failed predicate-conditioning controls.",
        },
        {
            "action": "promote_relative_vertical_result_to_broad_reliability",
            "blocked": True,
            "reason": "v3 is a scoped C_e mechanism proof, not p_rel/p_obs evidence.",
        },
    ]


def probe_contract() -> dict[str, Any]:
    return {
        "selected_route": SELECTED_ROUTE,
        "next_todo": NEXT_TODO,
        "family": "support_contact",
        "candidate_predicates": ["standing on", "lying on", "supported by"],
        "objective": "Determine whether support/contact has enough non-shortcut evidence to support a clean predicate-conditioned C_e target.",
        "minimum_probe_outputs": [
            "source_inventory.json",
            "evidence_axis_inventory.csv",
            "same_or_near_geometry_capacity.csv",
            "negative_policy_audit.csv",
            "shortcut_precheck.csv",
            "path_decision.json",
        ],
        "primary_questions": [
            "Do current artifacts expose role/orientation/contact-direction evidence beyond generic gap/overlap?",
            "Can same-G or near-G predicate alternatives be formed without changing generic G_e distribution?",
            "Can G_e-only be expected near chance before learned smoke?",
            "Are object class, structural object, predicate, source rank, and visible-pair shortcuts controllable?",
            "Is visual/mesh evidence required before support/contact can become a primary C_e target?",
        ],
        "success_gate": {
            "support_contact_materialization_allowed": [
                "non-generated candidate route found",
                "role/orientation/contact-direction or equivalent evidence axis present",
                "same-G or near-G groups available at reportable scale",
                "geometry-only precheck expected near chance",
                "shortcut precheck controllable",
            ],
            "route_to_visual_mesh_required": [
                "no role/orientation/contact-direction fields present",
                "only distance/overlap/gap fields available",
                "same-G/near-G support predicate alternatives not found",
            ],
            "diagnostic_only": [
                "shortcuts cannot be balanced",
                "support/contact label remains generic geometry perturbation",
            ],
        },
        "split": "train_only_probe",
        "runs_learned_smoke": False,
        "paper_evidence_allowed": False,
    }


def build_report(summary: dict[str, Any]) -> str:
    cap = summary["support_capacity_snapshot"]
    cand = summary["support_candidate_snapshot"]
    failure = summary["failure_snapshot"]
    lines = [
        "# Compatibility Dataset V3 Support/Contact Evidence Probe Plan",
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
        "## Why This Plan Exists",
        "",
        "The v3 `relative_vertical` smoke passed, but support/contact cannot be tested by reusing v2",
        "generated counterfactuals. v2 showed that support/contact was dominated by generic",
        "distance/overlap/gap shifts rather than predicate-conditioned compatibility.",
        "",
        "## Prior Evidence",
        "",
        "```text",
        f"support eligible positive / negative = {cap['eligible_positive']} / {cap['eligible_negative']}",
        f"support v2 materialized positive / negative = {cand['support_positive']} / {cand['support_negative']}",
        f"direct HL/LH predicate balance pass = {cap['direct_hl_lh_predicate_balance_pass']}",
        f"generated counterfactual policy = {cap['generated_counterfactual_policy']}",
        f"v2 primary cause = {failure['primary_cause']}",
        "```",
        "",
        "Available raw numeric fields are OBB/distance/overlap/gap fields. The next probe must",
        "check whether role, orientation, contact direction, surface normal, mesh, or visual evidence",
        "exists before any learned support/contact smoke.",
        "",
        "## Probe Tasks",
        "",
        "| Task | Question | Pass Condition |",
        "| --- | --- | --- |",
    ]
    for row in summary["probe_tasks"]:
        lines.append(f"| `{row['task']}` | {row['question']} | {row['pass_condition']} |")
    lines.extend(
        [
            "",
            "## Route Table",
            "",
            "| Route | Verdict | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for row in summary["route_table"]:
        lines.append(f"| `{row['route']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Blocked Actions",
            "",
        ]
    )
    for row in summary["blocked_actions"]:
        lines.append(f"- `{row['action']}`: {row['reason']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only planning artifact.",
            "- No learned smoke is run in this step.",
            "- No validation/test usage.",
            "- No paper-level evidence promotion.",
            "- No H001 artifact modification.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    decision = read_json(args.decision_dir / "summary.json")
    capacity = read_json(args.v2_capacity_dir / "summary.json")
    candidate = read_json(args.v2_candidate_dir / "summary.json")
    failure = read_json(args.v2_failure_dir / "summary.json")
    schema = read_json(args.v2_schema_dir / "summary.json")
    validation_rows = {
        "decision": read_jsonl(args.decision_dir / "validation_errors.jsonl"),
        "v2_capacity": read_jsonl(args.v2_capacity_dir / "validation_errors.jsonl"),
        "v2_candidate": read_jsonl(args.v2_candidate_dir / "validation_errors.jsonl"),
        "v2_failure": read_jsonl(args.v2_failure_dir / "validation_errors.jsonl"),
        "v2_schema": read_jsonl(args.v2_schema_dir / "validation_errors.jsonl"),
    }
    sanitized_rows = read_jsonl(args.v2_schema_dir / "sanitized_model_view.jsonl")

    errors = validate_inputs(decision, capacity, candidate, failure, schema, validation_rows)
    feature_snapshot = support_row_feature_snapshot(sanitized_rows)
    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_support_contact_evidence_probe_plan_inputs"

    summary: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_route": SELECTED_ROUTE if not errors else "fix_inputs_before_probe_plan",
        "next_todo": next_todo,
        "validation_errors": len(errors),
        "input_roots": {
            "decision": rel_path(args.decision_dir),
            "v2_capacity": rel_path(args.v2_capacity_dir),
            "v2_candidate": rel_path(args.v2_candidate_dir),
            "v2_failure": rel_path(args.v2_failure_dir),
            "v2_schema": rel_path(args.v2_schema_dir),
        },
        "support_capacity_snapshot": support_capacity_snapshot(capacity),
        "support_candidate_snapshot": support_candidate_snapshot(candidate),
        "support_feature_snapshot": feature_snapshot,
        "failure_snapshot": failure_snapshot(failure),
        "evidence_axes": evidence_axis_rows(feature_snapshot),
        "probe_tasks": probe_task_rows(),
        "route_table": route_rows(),
        "blocked_actions": blocked_actions(),
        "probe_contract": probe_contract(),
        "boundary": {
            "split": "train_only_probe_plan",
            "validation_usage": False,
            "test_usage": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "probe_plan": rel_path(args.output_dir / "probe_plan.json"),
            "evidence_axes": rel_path(args.output_dir / "evidence_axes.csv"),
            "probe_tasks": rel_path(args.output_dir / "probe_tasks.csv"),
            "route_table": rel_path(args.output_dir / "route_table.csv"),
            "blocked_actions": rel_path(args.output_dir / "blocked_actions.csv"),
            "source_inventory": rel_path(args.output_dir / "source_inventory.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    source_inventory = {
        "support_capacity_snapshot": summary["support_capacity_snapshot"],
        "support_candidate_snapshot": summary["support_candidate_snapshot"],
        "support_feature_snapshot": summary["support_feature_snapshot"],
        "input_roots": summary["input_roots"],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "probe_plan.json", summary["probe_contract"])
    write_csv(args.output_dir / "evidence_axes.csv", summary["evidence_axes"])
    write_csv(args.output_dir / "probe_tasks.csv", summary["probe_tasks"])
    write_csv(args.output_dir / "route_table.csv", summary["route_table"])
    write_csv(args.output_dir / "blocked_actions.csv", summary["blocked_actions"])
    write_json(args.output_dir / "source_inventory.json", source_inventory)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    (args.output_dir / "report.md").write_text(build_report(summary), encoding="utf-8")

    print(f"status={summary['status']}")
    print(f"selected_route={summary['selected_route']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
