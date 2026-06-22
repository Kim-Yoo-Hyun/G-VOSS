#!/usr/bin/env python3
"""Decide the H002 path after the blocked proximity LH-only target audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_target_independence_audit"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v12_proximity_lh_only_path_decision_after_audit"

EXPECTED_AUDIT_STATUS = "h002_reliability_target_v12_proximity_lh_only_independence_blocked_object_pair_shortcut"
EXPECTED_NEXT_TODO = "reliability_target_v12_proximity_lh_only_path_decision_after_audit"

SELECTED_PATH = "v13_proximity_lh_scene_geometry_repair_plan"
NEXT_TODO = "reliability_target_v13_proximity_lh_scene_geometry_repair_plan"


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

    counts = audit.get("counts", {})
    if counts.get("strict_slices") != 0:
        errors.append({"error_type": "unexpected_strict_slice", "actual": counts.get("strict_slices")})
    if counts.get("diagnostic_slices") != 0:
        errors.append({"error_type": "unexpected_diagnostic_slice", "actual": counts.get("diagnostic_slices")})

    object_stats = audit.get("object_pair_mixed_stats", {})
    for key in ["subject_object_visible_pair_binary", "subject_object_label_pair_hidden_binary"]:
        if object_stats.get(key, {}).get("mixed_groups") != 0:
            errors.append({"error_type": "unexpected_object_pair_mixed_group", "key": key, "actual": object_stats.get(key, {}).get("mixed_groups")})

    decision = audit.get("decision", {})
    if decision.get("posterior_smoke_allowed") is not False:
        errors.append({"error_type": "unexpected_posterior_allowed", "actual": decision.get("posterior_smoke_allowed")})

    boundary = audit.get("boundary", {})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_smoke_allowed", "paper_evidence_allowed", "h001_artifacts_modified", "rga_redefined_as_lh_only", "multi_view_as_model_input"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "audit_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def option_matrix(audit: dict[str, Any]) -> list[dict[str, Any]]:
    counts = audit["counts"]
    object_stats = audit["object_pair_mixed_stats"]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "No strict or diagnostic controlled slice passed. Posterior performance would measure object-pair shortcut exploitation.",
        },
        {
            "option": "keep_visible_only_proxy_as_primary_target",
            "verdict": "reject",
            "reason": f"Object-pair mixed binary groups are {object_stats['subject_object_visible_pair_binary']['mixed_groups']}; object-pair identity predicts the binary target perfectly.",
        },
        {
            "option": "freeze_visible_only_proxy_branch",
            "verdict": "select_as_diagnostic_evidence",
            "reason": "The visible-only proxy branch is useful negative evidence showing that object-pair text labels cannot validate factorized relation reliability.",
        },
        {
            "option": "repair_with_scene_geometry_aware_labels",
            "verdict": "select_next",
            "reason": "The failure cause is lack of within-object-pair reliability variation. Scene/geometry-aware evidence can create labels based on actual relation usefulness rather than object-pair identity alone.",
        },
        {
            "option": "mine_same_object_pair_mixed_contrasts_only",
            "verdict": "defer_into_repair_plan",
            "reason": "Additional mining is necessary, but if labels remain visible-text-only the same shortcut will recur. Mining must be paired with scene/geometry-aware review evidence.",
        },
        {
            "option": "construct_synthetic_proximity_hl",
            "verdict": "reject_for_now",
            "reason": "This would change the empirical branch and risks constructing artificial high-semantic/low-geometry proximity rows.",
        },
        {
            "option": "add_multiview_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": "Multi-view can be audit evidence for label repair, but should not become a deployable posterior input until the base S/G/C/U target is clean.",
        },
        {
            "option": "route_to_attachment_or_other_family",
            "verdict": "defer_as_fallback",
            "reason": "Another family may be better later, but proximity has already exposed a concrete target-construction issue that can be repaired with a clearer label protocol.",
        },
    ]


def selected_plan(audit: dict[str, Any]) -> dict[str, Any]:
    counts = audit["counts"]
    object_stats = audit["object_pair_mixed_stats"]
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "current_visible_only_branch_role": "diagnostic_only_negative_evidence",
        "posterior_smoke_allowed": False,
        "why_not_posterior": [
            "strict_slices = 0 and diagnostic_slices = 0",
            "subject/object pair identity predicts the proxy target",
            "same object-pair mixed binary contrast is absent",
        ],
        "audit_snapshot": {
            "binary_rows": counts.get("binary_rows"),
            "binary_target": counts.get("binary_target"),
            "strict_slices": counts.get("strict_slices"),
            "diagnostic_slices": counts.get("diagnostic_slices"),
            "risk_flags_full": counts.get("risk_flags_full"),
            "subject_object_visible_pair_binary_mixed_groups": object_stats["subject_object_visible_pair_binary"]["mixed_groups"],
            "subject_object_label_pair_hidden_binary_mixed_groups": object_stats["subject_object_label_pair_hidden_binary"]["mixed_groups"],
        },
        "repair_principle": {
            "problem": "visible object-pair text determines the proxy label",
            "needed_target_property": "same object-pair should contain both reliable and unreliable close-by examples based on scene/geometry context",
            "label_evidence_allowed": [
                "local object layout card",
                "distance/nearest-neighbor context",
                "local density or duplicate-object context",
                "scene crop or review card if available",
                "geometry witness explanation as audit evidence",
            ],
            "label_evidence_forbidden_as_shortcut": [
                "source semantic rank",
                "machine_hint",
                "label_match_status",
                "target construction bucket",
                "posterior score",
            ],
        },
        "v13_repair_plan_requirements": {
            "candidate_source": "train-only proximity LH pool",
            "minimum_same_pair_mixed_groups_goal": 20,
            "minimum_binary_rows_goal": 120,
            "minimum_per_class_goal": 50,
            "primary_sampling_unit": "subject_object_visible_pair",
            "must_include_controls": [
                "same object-pair mixed contrast",
                "scan cap",
                "rank-band audit",
                "label-match/machine-hint audit after label lock",
                "do not mix with v8/v9 support/vertical targets",
            ],
            "posterior_gate": "blocked until repaired target passes independence audit",
        },
        "claim_boundary": {
            "rga_framework": "bidirectional HL/LH mismatch remains unchanged",
            "proximity_lh_visible_only_result": "diagnostic target-construction failure",
            "not_a_factorized_posterior_result": True,
            "not_paper_evidence": True,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["selected_plan"]
    lines = [
        "# H002 V12 Proximity LH Path Decision After Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        "Freeze the visible-only proximity LH branch as diagnostic-only negative evidence, and select a scene/geometry-aware target repair plan as the next step.",
        "",
        "## Why",
        "",
        "```text",
        f"strict_slices = {plan['audit_snapshot']['strict_slices']}",
        f"diagnostic_slices = {plan['audit_snapshot']['diagnostic_slices']}",
        f"subject_object_visible_pair_binary_mixed_groups = {plan['audit_snapshot']['subject_object_visible_pair_binary_mixed_groups']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "The failed path is not H002 itself. The failed path is visible object-pair text -> proxy label -> posterior target.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
        "The repair plan must create scene/geometry-aware labels with same object-pair mixed contrast before any posterior smoke.",
        "",
    ]
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
        "h002_reliability_target_v12_proximity_lh_path_decision_select_scene_geometry_repair"
        if not validation_errors
        else "h002_reliability_target_v12_proximity_lh_path_decision_after_audit_errors"
    )
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "selected_plan": output_dir / "selected_plan.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": "h002_reliability_target_v12_proximity_lh_path_decision_after_audit_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "audit_summary": rel_path(audit_dir / "summary.json"),
            "audit_report": rel_path(audit_dir / "report.md"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "option_matrix": matrix,
        "selected_plan": plan,
        "selected_path": plan["selected_path"],
        "next_todo": plan["next_todo"],
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "visible_only_branch_frozen_as_diagnostic": True,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["option_matrix"], matrix)
    write_json(output_paths["selected_plan"], plan)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"visible_only_branch_frozen={summary['boundary']['visible_only_branch_frozen_as_diagnostic']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
