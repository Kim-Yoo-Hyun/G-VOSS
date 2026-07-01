#!/usr/bin/env python3
"""Write the target redesign plan after H002 compatibility dataset v2 failure analysis."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_FAILURE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_failure_analysis"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_target_redesign_plan"

EXPECTED_FAILURE_STATUS = "h002_compatibility_dataset_v2_failure_analysis_ready"
EXPECTED_FAILURE_NEXT = "compatibility_dataset_v2_target_redesign_plan"
EXPECTED_PRIMARY_CAUSE = "target_is_geometry_perturbation_detection_not_predicate_conditioned_compatibility"

SCHEMA_VERSION = "h002_compatibility_dataset_v2_target_redesign_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v2_target_redesign_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v2_target_redesign_plan_input_errors"
NEXT_TODO = "compatibility_dataset_v3_contract"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--failure-dir", type=Path, default=DEFAULT_FAILURE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def validate_failure(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_FAILURE_STATUS:
        errors.append({"error_type": "unexpected_failure_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_FAILURE_NEXT:
        errors.append({"error_type": "unexpected_failure_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "failure_analysis_validation_errors", "actual": summary.get("validation_errors")})
    if summary.get("primary_cause") != EXPECTED_PRIMARY_CAUSE:
        errors.append({"error_type": "unexpected_primary_cause", "actual": summary.get("primary_cause")})
    return errors


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "v3_same_geometry_multi_predicate",
            "decision": "selected",
            "role": "primary_next_contract",
            "why": "Directly fixes v2: geometry-only cannot assign two labels to the same geometry, so predicate conditioning becomes necessary.",
            "next_artifact": "compatibility_dataset_v3_contract",
        },
        {
            "route": "v2_more_rows_same_construction",
            "decision": "rejected",
            "role": "would_repeat_failure",
            "why": "More wrong-pair/shuffled/perturbation negatives would strengthen generic geometry detection rather than predicate-conditioned compatibility.",
            "next_artifact": "none",
        },
        {
            "route": "stronger_combiner_or_transformer_now",
            "decision": "rejected",
            "role": "method_before_target",
            "why": "The failure is target identifiability, not insufficient model capacity.",
            "next_artifact": "none",
        },
        {
            "route": "human_reliability_label_now",
            "decision": "deferred",
            "role": "p_rel_after_Ce_target",
            "why": "Human reliability is still useful later, but the immediate blocker is C_e compatibility target construction.",
            "next_artifact": "future_audit_protocol",
        },
    ]


def family_route_rows() -> list[dict[str, Any]]:
    return [
        {
            "family": "relative_vertical",
            "v3_role": "primary_clean_identifiability",
            "predicates": "higher than; lower than",
            "target_design": "same directed pair geometry is paired with both predicates; exactly one label is positive when vertical margin is clear",
            "why_predicate_conditioning_required": "The same G_e appears in both positive and negative rows, so G_e alone cannot solve the label.",
            "initial_quota": "200 geometry groups / 400 rows if capacity allows",
            "required_geometry_margin": "abs(center_delta_z) and normalized_center_delta_z must exceed a contract threshold fixed before materialization",
            "risks": "Can become a rule-learning sanity task if used alone; must be reported as identifiability proof, not broad relation reliability.",
            "next_action": "capacity scan for clear vertical same-geometry predicate pairs",
        },
        {
            "family": "support_contact",
            "v3_role": "secondary_hard_compatibility",
            "predicates": "standing on; lying on; supported by",
            "target_design": "same or near-identical support-like geometry is evaluated under role-specific predicates; generic supported-by must be separated from standing/lying if orientation/pose evidence exists",
            "why_predicate_conditioning_required": "Support-like G_e can be shared while predicate validity depends on object role, contact direction, orientation, and possibly visual/mesh evidence.",
            "initial_quota": "diagnostic contract first; primary only after evidence fields can distinguish role/orientation",
            "required_geometry_margin": "contact/overlap/gap alone is insufficient; requires role/orientation or visual/mesh evidence availability",
            "risks": "Current numeric G_e makes support/contact geometry-only dominant; standing vs lying may not be labelable from OBB geometry.",
            "next_action": "write diagnostic support route in v3 contract but do not use as first primary smoke unless evidence probe passes",
        },
        {
            "family": "proximity",
            "v3_role": "future_generality_not_Ce_primary",
            "predicates": "close by",
            "target_design": "distance-threshold compatibility is mostly geometry-only, so it should not be the first predicate-conditioning target",
            "why_predicate_conditioning_required": "Not applicable with a single predicate unless paired with semantic relation alternatives.",
            "initial_quota": "none",
            "required_geometry_margin": "future relation-family generality only",
            "risks": "Would collapse H002 back to geometry verifier.",
            "next_action": "defer",
        },
        {
            "family": "attachment_like",
            "v3_role": "future_hard_family_with_visual_mesh",
            "predicates": "attached to; hanging on; connected to",
            "target_design": "requires multi-view/mesh/functional evidence; current numeric geometry is insufficient",
            "why_predicate_conditioning_required": "Predicate semantics are meaningful but evidence quality dominates.",
            "initial_quota": "none",
            "required_geometry_margin": "visual/mesh evidence first",
            "risks": "Premature use repeats prior target-independence failures.",
            "next_action": "keep diagnostic",
        },
    ]


def target_contract() -> dict[str, Any]:
    return {
        "dataset_name": "h002_compatibility_dataset_v3_predicate_conditioned",
        "selected_route": "same_geometry_multi_predicate",
        "primary_task": "Task A predicate-geometry compatibility",
        "core_principle": (
            "The same or near-identical G_e must appear with multiple T_e alternatives so that "
            "geometry-only cannot solve the label and predicate conditioning is necessary."
        ),
        "row_group_contract": {
            "group_unit": "geometry_group",
            "required_rows_per_group_minimum": 2,
            "required_labels_per_group": ["one positive", "one or more predicate-negative rows"],
            "same_G_e_requirement": "primary rows in a group must share identical or audited near-identical numeric G_e",
            "allowed_T_e_change": "predicate_label and predicate_text only unless a declared subject-object swap control is being evaluated",
            "source_score_policy": "Z_e excluded from C_e; inherited/source metadata flags blocked; source-only reported as a baseline only",
        },
        "primary_vertical_contract": {
            "predicates": ["higher than", "lower than"],
            "positive_rule": "predicate agrees with signed vertical ordering under a predeclared margin",
            "negative_rule": "opposite predicate on the same directed pair geometry",
            "blocked_negative_types_as_primary": ["wrong_pair_geometry", "shuffled_geometry", "generic_geometry_perturbation"],
            "sanity_controls_only": ["wrong_pair_geometry", "shuffled_geometry"],
        },
        "support_contact_contract": {
            "status": "secondary_until_evidence_probe_passes",
            "reason": "Current support/contact target is dominated by distance/overlap geometry shifts.",
            "required_extra_evidence_candidates": ["object role", "pose/orientation", "contact direction", "surface normal", "multi-view/mesh evidence"],
            "blocked_primary_negatives": ["contact_gap_or_overlap_perturbation as primary", "shuffled support-like geometry as primary"],
        },
        "model_gates": {
            "required_pass": [
                "T_e + G_e beats G_e-only by a predeclared margin",
                "wrong-T same-G control degrades from T_e + G_e",
                "same-G group geometry-only is near chance",
                "source-only, predicate-only, object-pair-only shortcuts remain near chance",
                "family-specific metrics reported separately",
            ],
            "diagnostic_if_fail": [
                "G_e-only >= T_e + G_e",
                "wrong-T same-G equals T_e + G_e",
                "shuffled-G does not degrade",
            ],
        },
        "boundary": {
            "train_only": True,
            "paper_evidence_allowed": False,
            "docker_required_before_paper_promotion": True,
            "h001_artifacts_modified": False,
        },
    }


def gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "same_geometry_group_integrity",
            "criterion": "positive and predicate-negative rows share identical or audited near-identical G_e",
            "blocks_if_fail": True,
        },
        {
            "gate": "geometry_only_near_chance",
            "criterion": "G_e-only AUROC should be near chance on same-G predicate pairs",
            "blocks_if_fail": True,
        },
        {
            "gate": "predicate_conditioning_gain",
            "criterion": "T_e + G_e must beat G_e-only and semantic-only/source-only baselines",
            "blocks_if_fail": True,
        },
        {
            "gate": "wrong_predicate_degradation",
            "criterion": "wrong-T same-G must degrade compared with T_e + G_e",
            "blocks_if_fail": True,
        },
        {
            "gate": "source_semantic_shortcut_control",
            "criterion": "source-only, predicate-only, object-pair-only probes remain near chance",
            "blocks_if_fail": True,
        },
        {
            "gate": "support_contact_evidence_probe",
            "criterion": "support/contact can be promoted only if role/orientation/visual/mesh evidence exists",
            "blocks_if_fail": False,
        },
    ]


def validation_errors(failure_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return validate_failure(failure_summary)


def write_report(path: Path, summary: dict[str, Any], contract: dict[str, Any]) -> None:
    lines = [
        "# Compatibility Dataset V2 Target Redesign Plan",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v2_target_redesign_plan/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_route = {summary['selected_route']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Decision",
        "",
        "Do not repair v2 by adding more generated negatives or by using a stronger combiner. The",
        "failure analysis showed a target-identifiability problem: v2 is solved as generic geometry",
        "perturbation detection, not as predicate-conditioned compatibility.",
        "",
        "Selected next route:",
        "",
        "```text",
        "h002_compatibility_dataset_v3_predicate_conditioned",
        "same_geometry_multi_predicate contrast",
        "```",
        "",
        "## Core Contract",
        "",
        contract["core_principle"],
        "",
        "Primary initial family:",
        "",
        "```text",
        "relative_vertical: higher than / lower than same-geometry predicate contrast",
        "```",
        "",
        "Support/contact is kept as secondary until additional role/orientation or visual/mesh evidence",
        "can make `standing on`, `lying on`, and `supported by` distinguishable beyond generic",
        "distance/overlap geometry.",
        "",
        "## Required Gates",
        "",
    ]
    for row in gate_rows():
        lines.append(f"- `{row['gate']}`: {row['criterion']}")
    lines.extend(
        [
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    failure_summary = read_json(args.failure_dir / "summary.json")
    errors = validation_errors(failure_summary)
    contract = target_contract()
    status = STATUS_READY if not errors else STATUS_ERRORS
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO,
        "failure_root": rel_path(args.failure_dir),
        "output_root": rel_path(args.output_dir),
        "selected_route": "v3_same_geometry_multi_predicate_contract",
        "v2_status": "diagnostic_only_negative_evidence",
        "primary_v3_family": "relative_vertical",
        "secondary_v3_family": "support_contact",
        "validation_errors": len(errors),
        "paper_evidence_allowed": False,
        "boundary": {
            "analysis_only_plan": True,
            "materializes_dataset": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
        },
        "key_decisions": {
            "do_not_repair_v2_with_more_rows": True,
            "do_not_try_stronger_combiner_before_target_fix": True,
            "v3_must_make_predicate_conditioning_necessary": True,
            "same_geometry_multi_predicate_required": True,
            "geometry_only_is_main_baseline": True,
            "support_contact_requires_evidence_probe_before_primary": True,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "target_redesign_plan": rel_path(args.output_dir / "target_redesign_plan.json"),
            "route_decisions": rel_path(args.output_dir / "route_decisions.csv"),
            "family_routes": rel_path(args.output_dir / "family_routes.csv"),
            "gate_contract": rel_path(args.output_dir / "gate_contract.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "target_redesign_plan.json", contract)
    write_csv(args.output_dir / "route_decisions.csv", route_rows())
    write_csv(args.output_dir / "family_routes.csv", family_route_rows())
    write_csv(args.output_dir / "gate_contract.csv", gate_rows())
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, contract)


if __name__ == "__main__":
    main()
