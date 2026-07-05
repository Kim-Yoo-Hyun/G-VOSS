#!/usr/bin/env python3
"""Decide the H002 path after v6 uncertainty-aware seed audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_DESIGN_DIR = RGA_ROOT / "reliability_target_v6_uncertainty_aware_target_design_codex_proxy_user_requested"
DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v6_uncertainty_aware_seed_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v6_uncertainty_aware_path_decision_codex_proxy_user_requested"

NEXT_TODO = "reliability_target_v6_shortcut_controlled_sampling_plan"
SELECTED_PATH = "v6_shortcut_controlled_sampling_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, default=DEFAULT_DESIGN_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
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


def validate_upstream(design: dict[str, Any], audit: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_design_status = "h002_reliability_target_v6_uncertainty_aware_target_design_ready_for_seed_audit"
    expected_audit_status = "h002_reliability_target_v6_uncertainty_aware_seed_audit_blocked_shortcut_risk"
    if design.get("status") != expected_design_status:
        errors.append({"error_type": "unexpected_design_status", "expected": expected_design_status, "actual": design.get("status")})
    if audit.get("status") != expected_audit_status:
        errors.append({"error_type": "unexpected_audit_status", "expected": expected_audit_status, "actual": audit.get("status")})
    if audit.get("next_todo") != "reliability_target_v6_uncertainty_aware_path_decision":
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit.get("next_todo")})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "fills_new_labels", "multi_view_as_model_input", "paper_evidence_allowed", "h001_artifacts_modified"]:
        if audit.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "audit_boundary_violation", "key": key, "actual": audit.get("boundary", {}).get(key)})
    class_mass = audit.get("class_mass", {})
    if class_mass.get("diagnostic_class_mass_pass") is not True:
        errors.append({"error_type": "diagnostic_class_mass_not_passed", "actual": class_mass.get("diagnostic_class_mass_pass")})
    if class_mass.get("posterior_class_mass_pass") is not False:
        errors.append({"error_type": "unexpected_posterior_class_mass_state", "actual": class_mass.get("posterior_class_mass_pass")})
    if audit.get("risk_summary", {}).get("blocking_risk_count", 0) <= 0:
        errors.append({"error_type": "missing_expected_blocking_risk", "actual": audit.get("risk_summary", {}).get("blocking_risk_count")})
    if audit.get("posterior_smoke_allowed") is not False:
        errors.append({"error_type": "posterior_already_allowed", "actual": audit.get("posterior_smoke_allowed")})
    return errors


def option_matrix(audit: dict[str, Any]) -> list[dict[str, str]]:
    class_mass = audit["class_mass"]
    risks = audit["risk_summary"]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": (
                "Posterior class mass fails and 11 blocking shortcut-risk groups remain; a positive smoke result "
                "would not separate factorized evidence learning from construction shortcuts."
            ),
        },
        {
            "option": "use_current_v6_seed_with_class_weighting",
            "verdict": "reject",
            "reason": (
                "Class weighting can address imbalance, but cannot remove cell/pair/object-family leakage. "
                f"Current state counts are {class_mass['state_counts']}."
            ),
        },
        {
            "option": "expand_same_v5_cell_contrast_source",
            "verdict": "reject_as_primary",
            "reason": (
                "The current 72 seeds already show that v5 cell/pair construction is highly predictive of the "
                "target; adding more of the same source is likely to amplify the same shortcut."
            ),
        },
        {
            "option": "collapse_to_binary_accept_reject",
            "verdict": "reject",
            "reason": (
                "This returns to the v5 failure mode by discarding the dominant abstain_uncertain state "
                f"({class_mass['state_counts']['abstain_uncertain']} rows)."
            ),
        },
        {
            "option": "use_geometry_support_or_usefulness_as_main_target",
            "verdict": "reject",
            "reason": (
                "Those axes are useful diagnostics, but replacing reliability with them collapses H002 back into "
                "geometry validity or relation utility rather than relation reliability."
            ),
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": (
                "Multi-view may help audit ambiguous labels, but adding it before the base target is independent "
                "would mix target-construction shortcut risk with a stronger evidence source."
            ),
        },
        {
            "option": "freeze_h002_as_rga_diagnostic_only",
            "verdict": "fallback",
            "reason": (
                "If a shortcut-controlled sampling plan cannot produce independent labels, H002 should stop as "
                "an RGA diagnostic/benchmark framework rather than force posterior learning."
            ),
        },
        {
            "option": "v6_shortcut_controlled_sampling_plan",
            "verdict": "select",
            "reason": (
                "Keep the v6 reliability target schema, but build a new candidate sampling plan that controls "
                "cell/pair/object-family and visible object-label shortcuts before any new label fill."
            ),
        },
    ]


def risk_to_action_matrix(audit: dict[str, Any]) -> list[dict[str, Any]]:
    risks = audit["risk_summary"]["top_blocking_risks"]
    by_key = {row["group_key"]: row for row in risks}
    return [
        {
            "risk": "cell_or_pair_identity_predicts_state",
            "evidence": [by_key.get("cell_contrast_pair_id_hidden"), by_key.get("cell_contrast_key_hidden")],
            "action": "Do not reuse v5 cell id/key as a sampling backbone; build candidate cells whose target labels are not predetermined by pair construction.",
            "gate": "post-label audit must show no blocking risk for cell/pair keys before posterior smoke.",
        },
        {
            "risk": "endpoint_object_family_predicts_state",
            "evidence": [by_key.get("subject_object_family_cell_hidden"), by_key.get("object_family_cell_hidden")],
            "action": "Cap and balance object-family cells across relation families, semantic rank bands, and geometry residual bands.",
            "gate": "subject-object-family and object-family grouping must not exceed shortcut thresholds.",
        },
        {
            "risk": "visible_object_label_predicts_state",
            "evidence": [by_key.get("subject_label"), by_key.get("object_label")],
            "action": "Do not use subject/object labels as main posterior factors; sample for label diversity and evaluate with object-label grouped controls.",
            "gate": "visible object labels cannot explain the target above shortcut thresholds.",
        },
        {
            "risk": "posterior_class_mass_is_too_small",
            "evidence": audit["class_mass"],
            "action": "Target a larger balanced label batch before posterior smoke instead of merely adding the minimum one or eight rows needed for class count.",
            "gate": "minimum 20 per state for smoke; preferred diagnostic target is at least 40 per state after label audit.",
        },
        {
            "risk": "multi_view_could_mask_target_shortcut",
            "evidence": "multi_view_as_model_input=false in current boundary",
            "action": "Use multi-view only to resolve label ambiguity in the next annotation protocol; do not feed it as a model factor yet.",
            "gate": "base S/G/C/U reliability target must pass target-independence audit first.",
        },
    ]


def sampling_requirements(audit: dict[str, Any]) -> dict[str, Any]:
    current_counts = audit["class_mass"]["state_counts"]
    posterior_min = audit["class_mass"]["posterior_smoke_min_per_state"]
    minimum_additions_to_mass_floor = {
        state: max(0, posterior_min - count)
        for state, count in current_counts.items()
    }
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "target_schema_to_keep": "relation_reliability_state_v6 = accept_reliable / reject_unreliable / abstain_uncertain",
        "minimum_additions_to_existing_seed_mass_floor": minimum_additions_to_mass_floor,
        "preferred_post_label_mass": {
            "accept_reliable": ">=40",
            "reject_unreliable": ">=40",
            "abstain_uncertain": ">=40",
        },
        "sampling_principles": [
            "sample candidates before seeing labels; do not select rows by expected target state alone",
            "stratify by deployable semantic score/rank bands and continuous geometry evidence bands",
            "cap repeated subject/object labels and object-family cells",
            "include both high-semantic/low-geometry and low-semantic/high-geometry mismatch candidates",
            "include same-family and same-rank-band controls",
            "keep hidden cell/pair/object-family fields audit-only",
            "use multi-view only to clarify labels, not as posterior input",
        ],
        "must_report_after_label_fill": [
            "state counts",
            "risk summary by cell/pair/object-family/object-label groups",
            "controlled slice availability",
            "posterior smoke allowed flag",
            "validation/test usage false",
        ],
        "posterior_reopen_conditions": [
            "all primary states meet at least the posterior smoke mass floor",
            "no blocking shortcut-risk group remains above the predeclared thresholds",
            "a nontrivial controlled slice remains after grouping",
            "semantic, geometry, coverage, and uncertainty features are deployable and not review labels",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    class_mass = summary["audit_snapshot"]["class_mass"]
    risk = summary["audit_snapshot"]["risk_summary"]
    lines = [
        "# H002 Reliability Target V6 Uncertainty-Aware Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Split: Open3DSG train-only.",
        "- Validation/test rows: not used.",
        "- Posterior model: not trained.",
        "- New labels: not filled.",
        "- H001 artifacts: not modified.",
        "- Multi-view remains audit/label evidence only.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Selected path:",
        "",
        f"`{summary['selected_path']}`",
        "",
        "## Audit Snapshot",
        "",
        f"- State counts: `{class_mass['state_counts']}`",
        f"- Diagnostic class mass pass: `{class_mass['diagnostic_class_mass_pass']}`",
        f"- Posterior class mass pass: `{class_mass['posterior_class_mass_pass']}`",
        f"- Blocking shortcut-risk groups: `{risk['blocking_risk_count']}`",
        "",
        "## Option Matrix",
        "",
        "| Option | Verdict | Reason |",
        "| --- | --- | --- |",
    ]
    for row in summary["option_matrix"]:
        lines.append(f"| `{row['option']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    design_dir = as_abs(args.design_dir)
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    design = read_json(design_dir / "summary.json")
    audit = read_json(audit_dir / "summary.json")
    errors = validate_upstream(design, audit)
    options = option_matrix(audit)
    risk_actions = risk_to_action_matrix(audit)
    requirements = sampling_requirements(audit)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "risk_to_action_matrix": output_dir / "risk_to_action_matrix.json",
        "sampling_requirements": output_dir / "sampling_requirements.json",
        "validation_errors": output_dir / "validation_errors.json",
    }

    status = "h002_reliability_target_v6_uncertainty_aware_path_decision_select_shortcut_controlled_sampling_plan"
    if errors:
        status = "h002_reliability_target_v6_uncertainty_aware_path_decision_validation_failed"

    decision = (
        "Do not run posterior smoke, do not class-weight the current seed, and do not expand the same v5 "
        "cell-contrast source as the primary route. Keep the v6 reliability target schema, but move next to "
        "a shortcut-controlled sampling plan that creates a new label queue with object/cell/pair controls "
        "before any further label fill or posterior attempt."
    )

    summary = {
        "schema_version": "h002_reliability_target_v6_uncertainty_aware_path_decision_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selected_path": SELECTED_PATH if not errors else "blocked_by_validation_errors",
        "decision": decision,
        "next_todo": NEXT_TODO if not errors else "fix_path_decision_validation_errors",
        "input_paths": {
            "design_summary": rel_path(design_dir / "summary.json"),
            "audit_summary": rel_path(audit_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "fills_new_labels": False,
            "posterior_smoke_allowed": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "audit_snapshot": {
            "class_mass": audit["class_mass"],
            "risk_summary": {
                "risk_count": audit["risk_summary"]["risk_count"],
                "blocking_risk_count": audit["risk_summary"]["blocking_risk_count"],
                "blocking_risk_counts_by_mode": audit["risk_summary"]["blocking_risk_counts_by_mode"],
                "top_blocking_risks": audit["risk_summary"]["top_blocking_risks"][:8],
            },
            "blocked_reasons": audit["blocked_reasons"],
        },
        "option_matrix": options,
        "risk_to_action_matrix": risk_actions,
        "sampling_requirements": requirements,
        "posterior_smoke_allowed": False,
        "validation_error_count": len(errors),
    }

    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    write_json(output_paths["option_matrix"], options)
    write_json(output_paths["risk_to_action_matrix"], risk_actions)
    write_json(output_paths["sampling_requirements"], requirements)
    write_json(output_paths["validation_errors"], errors)

    return summary


def main() -> None:
    summary = run(parse_args())
    class_mass = summary["audit_snapshot"]["class_mass"]
    risk = summary["audit_snapshot"]["risk_summary"]
    print(f"status={summary['status']}")
    print(f"selected={summary['selected_path']}")
    print(f"state_counts={class_mass['state_counts']}")
    print(f"posterior_class_mass_pass={class_mass['posterior_class_mass_pass']}")
    print(f"blocking_risk_count={risk['blocking_risk_count']}")
    print(f"posterior_allowed={summary['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_error_count']}")
    print(f"next={summary['next_todo']}")


if __name__ == "__main__":
    main()
