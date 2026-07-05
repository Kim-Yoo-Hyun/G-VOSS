#!/usr/bin/env python3
"""Decide the H002 path after v14 physical relation-family target audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_target_independence_audit"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_path_decision_after_audit"

EXPECTED_AUDIT_STATUS = "h002_reliability_target_v14_physical_relation_family_target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
EXPECTED_NEXT_TODO = "reliability_target_v14_physical_relation_family_path_decision_after_audit"

SELECTED_PATH = "freeze_v14_diagnostic_select_v15_witness_matched_physical_relation_repair_plan"
NEXT_TODO = "reliability_target_v15_physical_relation_family_repair_plan"


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
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "Primary reliability target has 48/152 class split, no strict clear slice, and no diagnostic clear slice.",
        },
        {
            "option": "use_balanced_full_slice_48_48",
            "verdict": "reject",
            "reason": "Balanced full slice exists, but shortcut risks from scan/object identity, pair identity, quota cell, rank band, machine hint, and witness text remain.",
        },
        {
            "option": "add_two_positive_rows_only",
            "verdict": "reject",
            "reason": "This would pass the numeric class-mass threshold but not address the 0 clear slices or witness-text shortcut.",
        },
        {
            "option": "use_geometry_support_or_usefulness_as_primary",
            "verdict": "reject",
            "reason": "These targets have the same 48/152 split as relation reliability and are auxiliary evidence-axis targets, not relation reliability itself.",
        },
        {
            "option": "keep_v14_as_primary_with_caveat",
            "verdict": "reject",
            "reason": "A caveat cannot replace target independence for a posterior method claim.",
        },
        {
            "option": "freeze_v14_as_diagnostic_evidence",
            "verdict": "select",
            "reason": "v14 usefully shows that physical-family labels still fail if the visible label surface exposes geometry-witness summaries too directly.",
        },
        {
            "option": "repair_v14_sampling_and_label_surface",
            "verdict": "select_next",
            "reason": "The next target should match within witness/predicate/queue strata, increase positive support-contact mass, and reduce direct witness-text shortcut.",
        },
        {
            "option": "switch_to_attachment_deferred_immediately",
            "verdict": "defer",
            "reason": "Attachment remains promising, but current geometry policy marks it unsupported; a witness schema probe should follow only after the v15 repair plan states the schema requirements.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": "Multi-view should remain audit/confirmation evidence until a clean S/G/C/U target exists. Adding it now would mask target-construction failure.",
        },
        {
            "option": "stop_h002",
            "verdict": "reject",
            "reason": f"The failure is informative and localized: class mass {relation['class_counts']} plus shortcut risk. It points to target repair, not abandoning the hypothesis.",
        },
    ]


def selected_plan(audit: dict[str, Any]) -> dict[str, Any]:
    relation = audit["target_decisions"]["relation_binary"]
    counts = audit["counts"]
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "posterior_smoke_allowed": False,
        "v14_role": {
            "status": "diagnostic_only_negative_evidence",
            "what_it_shows": [
                "physical relation families are not sufficient by themselves if labels are derived from direct witness summaries",
                "support_contact plus relative_vertical gives more structured row mass than proximity, but relation reliability target still fails independence",
                "adding two positives would not solve the shortcut problem",
            ],
            "not_allowed": [
                "do not run posterior smoke on current v14 target",
                "do not claim factorized posterior improves relation reliability from v14",
                "do not use geometry_support or usefulness as a replacement primary target",
            ],
        },
        "audit_snapshot": {
            "relation_binary_rows": relation["rows"],
            "relation_binary_class_counts": relation["class_counts"],
            "relation_min_class_count": relation["min_class_count"],
            "relation_class_mass_pass": relation["class_mass_pass"],
            "relation_strict_clear_slice_count": relation["strict_clear_slice_count"],
            "relation_diagnostic_clear_slice_count": relation["diagnostic_clear_slice_count"],
            "full_quick_probe_risk_flags": counts["full_quick_probe_risk_flags"],
            "slice_blocking_risk_flags": counts["slice_blocking_risk_flags"],
        },
        "failure_cause": [
            "positive class mass is 48, below the predeclared posterior gate of 50",
            "balanced 48/48 full slice remains shortcut-entangled",
            "visible witness summaries are too close to the proxy label policy",
            "quota and geometry status still predict labels too strongly",
            "scan/object/pair identity risks remain after balancing",
        ],
        "next_route": {
            "name": "v15_physical_relation_family_repair_plan",
            "goal": "Repair target construction before any posterior method claim.",
            "requirements": [
                "increase primary relation positive mass without simply relaxing labels",
                "sample within matched predicate, source queue, rank band, geometry status, and witness buckets",
                "reduce or redesign visible witness text so it is not a direct label template",
                "separate support_contact primary target from relative_vertical control target",
                "require mixed accept/reject groups within matched witness strata before label fill",
                "keep hidden audit fields and target construction keys out of model inputs",
                "keep multi-view as audit evidence only",
            ],
            "candidate_designs": [
                {
                    "name": "support_contact_witness_matched_repair",
                    "role": "preferred next repair route",
                    "description": "Mine additional support/contact rows and balance accept/reject candidates within same predicate, queue, rank band, p_geom bin, geometry status, and coarse witness strata.",
                },
                {
                    "name": "label_surface_redesign",
                    "role": "required guardrail",
                    "description": "Replace direct support_or_vertical witness summaries with less templated review packets or audit-only evidence so string fields do not trivially encode labels.",
                },
                {
                    "name": "relative_vertical_control_only",
                    "role": "control",
                    "description": "Keep lower-than/vertical rows for diagnostic control, not as the source of primary positive mass.",
                },
                {
                    "name": "attachment_deferred_schema_probe",
                    "role": "deferred extension",
                    "description": "Define witness schema for attached to, hanging on, connected to after v15 repair plan; do not use unsupported-family rows as target yet.",
                },
            ],
        },
        "claim_boundary": {
            "rga_framework": "still bidirectional semantic-geometry mismatch",
            "v14_branch": "diagnostic target-construction failure evidence",
            "no_paper_metric_evidence": True,
            "no_validation_or_test_usage": True,
            "no_h001_artifact_modification": True,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["selected_plan"]
    snap = plan["audit_snapshot"]
    lines = [
        "# H002 V14 Physical Relation-Family Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Decision",
        "",
        "Freeze current v14 as diagnostic target-construction evidence and select a v15 witness-matched physical relation-family repair plan.",
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
        f"full_quick_probe_risk_flags = {snap['full_quick_probe_risk_flags']}",
        f"slice_blocking_risk_flags = {snap['slice_blocking_risk_flags']}",
        "```",
        "",
        "## Why Not Just Add Two Positives",
        "",
        "The target is not blocked only by the numeric `48 < 50` class-mass gap. The balanced `48/48` full slice still has shortcut risk from scan/object identity, pair identity, quota cell, rank band, machine hint, and direct witness summaries.",
        "",
        "## Selected Repair Requirements",
        "",
    ]
    lines.extend(f"- {item}" for item in plan["next_route"]["requirements"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only decision.",
            "- No validation/test rows.",
            "- No posterior trained.",
            "- Hidden fields remain audit/control metadata only.",
            "- H001 and paper artifacts are not modified.",
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
    options = option_matrix(audit)
    plan = selected_plan(audit)

    if validation_errors:
        status = "h002_reliability_target_v14_physical_relation_family_path_decision_after_audit_errors"
        selected_path = "blocked_by_validation_errors"
        next_todo = EXPECTED_NEXT_TODO
    else:
        status = "h002_reliability_target_v14_physical_relation_family_path_decision_select_v15_repair_plan"
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.jsonl",
        "selected_plan": output_dir / "selected_plan.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    summary = {
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "audit_summary": rel_path(audit_dir / "summary.json"),
            "audit_report": rel_path(audit_dir / "report.md"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "selected_path": selected_path,
        "selected_plan": plan,
        "option_verdicts": {
            item["option"]: item["verdict"]
            for item in options
        },
        "audit_snapshot": plan["audit_snapshot"],
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
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["selected_plan"], plan)
    write_jsonl(output_paths["option_matrix"], options)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    snap = summary["audit_snapshot"]
    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"relation_binary_counts={snap['relation_binary_class_counts']}")
    print(f"relation_class_mass_pass={snap['relation_class_mass_pass']}")
    print(f"relation_strict_clear_slice_count={snap['relation_strict_clear_slice_count']}")
    print(f"relation_diagnostic_clear_slice_count={snap['relation_diagnostic_clear_slice_count']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
