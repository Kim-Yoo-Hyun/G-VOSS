#!/usr/bin/env python3
"""Decide the H002 path after v13 proximity scene/geometry target audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_target_independence_audit"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_path_decision_after_audit"

EXPECTED_AUDIT_STATUS = "h002_reliability_target_v13_proximity_lh_scene_geometry_target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
EXPECTED_NEXT_TODO = "reliability_target_v13_proximity_lh_scene_geometry_path_decision_after_audit"

SELECTED_PATH = "freeze_v13_proximity_diagnostic_select_v14_physical_relation_family_feasibility"
NEXT_TODO = "reliability_target_v14_physical_relation_family_feasibility_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def validate_audit(audit: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "expected": EXPECTED_AUDIT_STATUS, "actual": audit.get("status")})
    if audit.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_audit_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": audit.get("next_todo")})
    if audit.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit.get("validation_errors")})

    relation = audit.get("target_decisions", {}).get("relation_binary", {})
    if relation.get("posterior_allowed") is not False:
        errors.append({"error_type": "relation_posterior_unexpectedly_allowed", "actual": relation.get("posterior_allowed")})
    if relation.get("class_mass_pass") is not False:
        errors.append({"error_type": "relation_class_mass_unexpectedly_passed", "actual": relation.get("class_mass_pass")})
    if relation.get("strict_clear_slice_count") != 0:
        errors.append({"error_type": "relation_strict_clear_slice_unexpected", "actual": relation.get("strict_clear_slice_count")})
    if relation.get("diagnostic_clear_slice_count") != 0:
        errors.append({"error_type": "relation_diagnostic_clear_slice_unexpected", "actual": relation.get("diagnostic_clear_slice_count")})

    boundary = audit.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "audit_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def option_matrix(audit: dict[str, Any]) -> list[dict[str, str]]:
    relation = audit["target_decisions"]["relation_binary"]
    geometry = audit["target_decisions"]["geometry_support_binary"]
    counts = audit["counts"]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "Primary relation reliability has no strict or diagnostic clear slice and positive mass is below the predeclared gate.",
        },
        {
            "option": "use_geometry_support_as_primary_target",
            "verdict": "reject",
            "reason": f"Geometry-support has class mass ({geometry['class_counts']}) but no strict independent slice, and it is an auxiliary evidence-axis target rather than relation reliability.",
        },
        {
            "option": "mine_more_close_by_positives_immediately",
            "verdict": "reject_for_primary_path",
            "reason": "More positive mining would likely relax the conservative label policy or overfit to geometry-witness text; it should not be the next primary posterior path.",
        },
        {
            "option": "freeze_v13_proximity_as_diagnostic_only",
            "verdict": "select",
            "reason": "v13 shows that scene/geometry-aware proximity improves same-pair contrast over v12, but remains positive-sparse and shortcut-entangled. Keep it as generality/limitation evidence.",
        },
        {
            "option": "keep_close_by_as_generality_evidence",
            "verdict": "select",
            "reason": "Close-by remains useful for showing that dense proximity is hard for relation reliability, but not as the primary posterior target under the current labels.",
        },
        {
            "option": "return_to_support_vertical_exact_pair",
            "verdict": "reject_as_repeat",
            "reason": "Earlier v8/v9 showed exact-pair support/vertical is rank/predicate entangled. Repeating the same target construction would not address the failure cause.",
        },
        {
            "option": "select_physical_relation_family_feasibility",
            "verdict": "select_next",
            "reason": "The next target should test families with stronger physical witnesses and less dense-neighborhood noise: support_contact with repaired sampling and attachment_deferred feasibility.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": "Multi-view remains audit evidence only until a clean S/G/C/U target exists. Adding it now would mix target repair with a new deployable evidence axis.",
        },
        {
            "option": "relative_horizontal_now",
            "verdict": "reject_for_now",
            "reason": "left/right/front/behind introduces coordinate-frame ambiguity, which is a different blocker from relation reliability target independence.",
        },
        {
            "option": "stop_h002",
            "verdict": "reject",
            "reason": f"The audit is informative: v12 object-pair shortcut was reduced, but relation target remains blocked ({relation['class_counts']}, risk flags {counts['full_quick_probe_risk_flags']}). A better family route is justified.",
        },
    ]


def selected_plan(audit: dict[str, Any]) -> dict[str, Any]:
    relation = audit["target_decisions"]["relation_binary"]
    geometry = audit["target_decisions"]["geometry_support_binary"]
    counts = audit["counts"]
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "posterior_smoke_allowed": False,
        "v13_proximity_role": {
            "status": "diagnostic_only_generality_and_limitation_evidence",
            "what_it_shows": [
                "close by / proximity has enough LH train rows but no current HL counterpart",
                "scene/geometry-aware labels improve same-pair mixed contrast over visible-only labels",
                "dense proximity still produces positive sparsity and geometry/scene shortcut entanglement",
            ],
            "not_allowed": [
                "do not use v13 proximity as primary posterior target",
                "do not report factorized posterior improvement from v13 proximity",
                "do not claim bidirectional close-by reliability is solved",
            ],
        },
        "audit_snapshot": {
            "relation_binary_rows": relation["rows"],
            "relation_binary_class_counts": relation["class_counts"],
            "relation_min_class_count": relation["min_class_count"],
            "relation_class_mass_pass": relation["class_mass_pass"],
            "relation_strict_clear_slice_count": relation["strict_clear_slice_count"],
            "relation_diagnostic_clear_slice_count": relation["diagnostic_clear_slice_count"],
            "geometry_support_class_counts": geometry["class_counts"],
            "geometry_support_class_mass_pass": geometry["class_mass_pass"],
            "geometry_support_strict_clear_slice_count": geometry["strict_clear_slice_count"],
            "full_quick_probe_risk_flags": counts["full_quick_probe_risk_flags"],
            "slice_blocking_risk_flags": counts["slice_blocking_risk_flags"],
        },
        "why_not_more_close_by_now": [
            "reliable close-by positives are sparse under the conservative visible scene/geometry policy",
            "positive mining would likely favor rows with easy geometry-witness text and reinforce p_geom/geometry-summary shortcuts",
            "close by is intrinsically dense and often redundant, so relation usefulness is harder to separate from local density",
            "current proximity branch is LH-only, so it cannot carry the bidirectional RGA claim by itself",
        ],
        "next_route": {
            "name": "v14_physical_relation_family_feasibility_scan",
            "goal": "Find a primary H002 target route where relation reliability is not dominated by dense proximity or exact-pair predicate/rank shortcuts.",
            "candidate_families": [
                {
                    "family": "support_contact",
                    "predicates": ["standing on", "lying on"],
                    "role": "first feasibility anchor",
                    "reason": "contact/support has concrete geometric witnesses and is closer to current raw witness machinery, but must avoid the old exact-pair rank/predicate construction.",
                },
                {
                    "family": "attachment_deferred",
                    "predicates": ["attached to", "hanging on", "connected to"],
                    "role": "novelty-oriented feasibility candidate",
                    "reason": "attachment-style relations are less likely than close by to collapse into dense proximity noise, but may need stricter witness schema and audit evidence.",
                },
                {
                    "family": "relative_vertical",
                    "predicates": ["higher than", "lower than"],
                    "role": "control family only",
                    "reason": "vertical order is geometry-easy and useful as a control, but less central for proving relation reliability beyond geometry validity.",
                },
            ],
            "feasibility_questions": [
                "Is there enough train-only row mass per family and predicate?",
                "Can positive/reject/abstain reliability labels be formed without exact-pair predicate/rank shortcut?",
                "Can same-family or same-witness controlled slices survive shortcut audit?",
                "Can continuous geometry evidence be separated from frozen geometry-status labels?",
                "Can multi-view remain audit-only rather than deployable input at this stage?",
            ],
        },
        "claim_boundary": {
            "rga_framework": "still bidirectional semantic-geometry mismatch",
            "proximity_branch": "diagnostic/generality evidence only",
            "no_paper_metric_evidence": True,
            "no_validation_or_test_usage": True,
            "no_h001_artifact_modification": True,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["selected_plan"]
    snap = plan["audit_snapshot"]
    lines = [
        "# H002 V13 Proximity Scene/Geometry Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        "Freeze v13 proximity as diagnostic/generality evidence and select a physical relation-family feasibility scan as the next primary target-repair route.",
        "",
        "```text",
        f"selected_path = {summary['selected_path']}",
        f"next_todo = {summary['next_todo']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Audit Snapshot",
        "",
        "```text",
        f"relation_binary_rows = {snap['relation_binary_rows']}",
        f"relation_binary_class_counts = {snap['relation_binary_class_counts']}",
        f"relation_min_class_count = {snap['relation_min_class_count']}",
        f"relation_class_mass_pass = {snap['relation_class_mass_pass']}",
        f"relation_strict_clear_slice_count = {snap['relation_strict_clear_slice_count']}",
        f"relation_diagnostic_clear_slice_count = {snap['relation_diagnostic_clear_slice_count']}",
        f"geometry_support_class_counts = {snap['geometry_support_class_counts']}",
        f"geometry_support_strict_clear_slice_count = {snap['geometry_support_strict_clear_slice_count']}",
        f"full_quick_probe_risk_flags = {snap['full_quick_probe_risk_flags']}",
        f"slice_blocking_risk_flags = {snap['slice_blocking_risk_flags']}",
        "```",
        "",
        "## Why Not More Close By Now",
        "",
    ]
    lines.extend(f"- {item}" for item in plan["why_not_more_close_by_now"])
    lines.extend(
        [
            "",
            "## Next Route",
            "",
            f"`{plan['next_route']['name']}`",
            "",
            plan["next_route"]["goal"],
            "",
            "| Family | Role | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for family in plan["next_route"]["candidate_families"]:
        predicates = ", ".join(f"`{pred}`" for pred in family["predicates"])
        lines.append(f"| `{family['family']}` ({predicates}) | {family['role']} | {family['reason']} |")
    lines.extend(
        [
            "",
            "## Option Matrix",
            "",
            "| Option | Verdict | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for option in summary["option_matrix"]:
        lines.append(f"| `{option['option']}` | `{option['verdict']}` | {option['reason']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only evidence only.",
            "- No posterior is trained.",
            "- No validation/test rows are used.",
            "- Multi-view remains audit evidence only.",
            "- H001 artifacts and paper outputs are not modified.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audit = read_json(audit_dir / "summary.json")
    validation_errors = validate_audit(audit)
    matrix = option_matrix(audit)
    plan = selected_plan(audit)

    status = (
        "h002_reliability_target_v13_proximity_lh_scene_geometry_path_decision_select_physical_relation_feasibility"
        if not validation_errors
        else "h002_reliability_target_v13_proximity_lh_scene_geometry_path_decision_errors"
    )
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": "h002_reliability_target_v13_proximity_lh_scene_geometry_path_decision_after_audit_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selected_path": SELECTED_PATH,
        "decision": "Freeze v13 proximity as diagnostic/generality evidence; move primary target repair to physical relation-family feasibility.",
        "input_paths": {
            "audit_summary": rel_path(audit_dir / "summary.json"),
            "audit_report": rel_path(audit_dir / "report.md"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "selected_plan": plan,
        "option_matrix": matrix,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "reads_hidden_audit_manifest_after_label_lock": True,
            "hidden_fields_as_model_input": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }
    write_jsonl(output_paths["option_matrix"], matrix)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    snap = summary["selected_plan"]["audit_snapshot"]
    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"relation_binary_class_counts={snap['relation_binary_class_counts']}")
    print(f"relation_strict_clear_slices={snap['relation_strict_clear_slice_count']}")
    print(f"geometry_support_strict_clear_slices={snap['geometry_support_strict_clear_slice_count']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
