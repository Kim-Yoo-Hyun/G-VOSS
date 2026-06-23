#!/usr/bin/env python3
"""Decide the H002 path after the v18 attachment target-independence audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_target_independence_audit"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_path_decision_after_audit"

EXPECTED_AUDIT_STATUS = "h002_reliability_target_v18_attachment_deferred_target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
EXPECTED_NEXT_TODO = "reliability_target_v18_attachment_deferred_path_decision_after_audit"

STATUS = "h002_reliability_target_v18_attachment_deferred_path_decision_select_v19_independent_evidence_repair_plan"
SELECTED_PATH = "freeze_v18_attachment_diagnostic_select_v19_independent_evidence_repair_plan"
NEXT_TODO = "reliability_target_v19_attachment_deferred_independent_evidence_repair_plan"


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
    connected = audit.get("target_decisions", {}).get("connected_diagnostic", {})
    geometry = audit.get("target_decisions", {}).get("geometry_support_binary", {})

    if relation.get("posterior_allowed") is not False:
        errors.append({"error_type": "relation_posterior_unexpectedly_allowed", "actual": relation.get("posterior_allowed")})
    if relation.get("class_mass_pass") is not False:
        errors.append({"error_type": "relation_class_mass_unexpectedly_passed", "actual": relation.get("class_mass_pass")})
    if relation.get("strict_clear_slice_count") != 0:
        errors.append({"error_type": "relation_strict_clear_slice_unexpected", "actual": relation.get("strict_clear_slice_count")})
    if relation.get("diagnostic_clear_slice_count") != 0:
        errors.append({"error_type": "relation_diagnostic_clear_slice_unexpected", "actual": relation.get("diagnostic_clear_slice_count")})
    if connected.get("strict_clear_slice_count") != 0:
        errors.append({"error_type": "connected_strict_clear_slice_unexpected", "actual": connected.get("strict_clear_slice_count")})
    if geometry.get("posterior_allowed") is not False:
        errors.append({"error_type": "geometry_support_unexpectedly_posterior_allowed", "actual": geometry.get("posterior_allowed")})

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


def build_option_matrix(audit: dict[str, Any]) -> list[dict[str, str]]:
    relation = audit["target_decisions"]["relation_binary"]
    connected = audit["target_decisions"]["connected_diagnostic"]
    geometry = audit["target_decisions"]["geometry_support_binary"]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "Primary relation reliability has 33/81 class split and no strict or diagnostic clear slice.",
        },
        {
            "option": "use_geometry_support_as_primary",
            "verdict": "reject",
            "reason": f"Geometry-support has class mass ({geometry['class_counts']}) but is an auxiliary evidence target and has no strict independent slice.",
        },
        {
            "option": "treat_connected_to_as_primary_binary",
            "verdict": "reject",
            "reason": f"`connected to` remains diagnostic ({connected['class_counts']}); functional connection is not reliably decidable from OBB geometry alone.",
        },
        {
            "option": "mine_more_same_style_attachment_rows",
            "verdict": "reject",
            "reason": "More rows from the same visible-only geometry-summary label surface would likely increase the same construction and witness-text shortcuts.",
        },
        {
            "option": "loosen_label_policy_to_create_more_positives",
            "verdict": "reject",
            "reason": "This would hide positive sparsity without fixing independence. It would make relation reliability closer to geometry validity.",
        },
        {
            "option": "freeze_v18_attachment_as_diagnostic_evidence",
            "verdict": "select",
            "reason": "v18 is useful negative target-construction evidence: typed witnesses and labels are not enough unless the label source is independent from geometry summaries.",
        },
        {
            "option": "select_independent_evidence_repair_plan",
            "verdict": "select_next",
            "reason": "The next route should build an independent label/audit evidence plan before any posterior smoke, while keeping multi-view out of deployable inputs.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": "Multi-view can be audit/confirmation evidence, but using it as an input now would mask target-construction failure.",
        },
        {
            "option": "abandon_attachment_deferred",
            "verdict": "reject",
            "reason": f"The route failed as a posterior target but remains informative; relation positives {relation['class_counts']} and shortcut risks point to label-evidence repair, not abandonment.",
        },
    ]


def build_selected_plan(audit: dict[str, Any]) -> dict[str, Any]:
    relation = audit["target_decisions"]["relation_binary"]
    connected = audit["target_decisions"]["connected_diagnostic"]
    geometry = audit["target_decisions"]["geometry_support_binary"]
    counts = audit["counts"]
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "posterior_smoke_allowed": False,
        "candidate_mining_allowed": False,
        "label_fill_allowed": False,
        "v18_role": {
            "status": "diagnostic_only_negative_target_construction_evidence",
            "what_it_shows": [
                "typed 3D witness schema alone is not sufficient for a relation reliability target",
                "visible-only geometry/witness summaries can make labels too close to geometry validity",
                "attachment/hanging relations need stronger independent evidence to separate reliability from geometry support",
                "connected to should remain diagnostic until visual or mesh evidence can confirm functional connection",
            ],
            "not_allowed": [
                "do not run posterior smoke on current v18 target",
                "do not treat geometry-support as the main reliability target",
                "do not promote connected to into primary binary target",
                "do not use v18 as paper metric evidence",
            ],
        },
        "audit_snapshot": {
            "relation_binary_rows": relation["rows"],
            "relation_binary_class_counts": relation["class_counts"],
            "relation_min_class_count": relation["min_class_count"],
            "relation_class_mass_pass": relation["class_mass_pass"],
            "relation_strict_clear_slice_count": relation["strict_clear_slice_count"],
            "relation_diagnostic_clear_slice_count": relation["diagnostic_clear_slice_count"],
            "connected_diagnostic_rows": connected["rows"],
            "connected_diagnostic_class_counts": connected["class_counts"],
            "geometry_support_rows": geometry["rows"],
            "geometry_support_class_counts": geometry["class_counts"],
            "geometry_support_class_mass_pass": geometry["class_mass_pass"],
            "geometry_support_strict_clear_slice_count": geometry["strict_clear_slice_count"],
            "full_quick_probe_risk_flags": counts["full_quick_probe_risk_flags"],
            "slice_blocking_risk_flags": counts["slice_blocking_risk_flags"],
        },
        "failure_cause": [
            "primary reliable attachment positives are only 33",
            "strict and diagnostic controlled slices are both 0",
            "balanced slices remain explained by object pair, scan, cell, queue, reason, machine hint, and witness summaries",
            "geometry-support is a useful evidence axis but not independent relation reliability",
            "functional connection needs evidence beyond OBB-level geometry",
        ],
        "next_route": {
            "name": "v19_attachment_deferred_independent_evidence_repair_plan",
            "goal": "Design a target-repair route where relation reliability labels are less dependent on the same 3D geometry summaries used as evidence factors.",
            "requirements": [
                "keep all rows train-only",
                "keep posterior smoke blocked",
                "separate label/audit evidence from deployable input features",
                "use multi-view or mesh only as audit/confirmation evidence at this stage",
                "do not expose construction keys such as cell id, queue, geometry status, machine hint, or rank band as label/model inputs",
                "define positive criteria that distinguish reliable physical attachment from mere geometric support or proximity",
                "define reject criteria that include false attachment, floor/support confound, wrong endpoint, and insufficient evidence",
                "keep connected to diagnostic-only unless visual/mesh evidence supports functional connection",
                "require a future target-independence audit before any posterior smoke",
            ],
            "candidate_designs": [
                {
                    "name": "independent_visual_or_mesh_audit_packet",
                    "role": "preferred repair direction",
                    "description": "Use co-visible views, crop quality, mesh/contact boundary, or manual audit notes only to decide labels, while keeping these audit labels separate from future model inputs.",
                },
                {
                    "name": "two_stage_attachment_label",
                    "role": "label schema repair",
                    "description": "First decide geometry support/coverage, then decide relation reliability using independent evidence. This prevents geometry validity from becoming the label itself.",
                },
                {
                    "name": "attachment_hanging_primary_connected_diagnostic",
                    "role": "scope control",
                    "description": "Keep `attached to` and `hanging on` as primary candidates; keep `connected to` diagnostic-only until stronger evidence exists.",
                },
                {
                    "name": "support_contact_fallback",
                    "role": "fallback if visual/mesh evidence is unavailable",
                    "description": "If independent evidence cannot be assembled for attachment, return to support/contact with a stricter independent label source rather than reusing v18 labels.",
                },
            ],
        },
        "multi_view_policy": {
            "audit_or_confirmation_evidence_now": True,
            "deployable_model_input_now": False,
            "promotion_rule": "V_mv_e can become a deployable factor only after a target-independent label surface exists.",
        },
        "claim_boundary": {
            "rga_framework": "still bidirectional semantic-geometry mismatch",
            "attachment_branch": "diagnostic target-construction evidence until repaired",
            "no_paper_metric_evidence": True,
            "no_validation_or_test_usage": True,
            "no_h001_artifact_modification": True,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["selected_plan"]
    snap = plan["audit_snapshot"]
    lines = [
        "# H002 V18 Attachment Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Decision",
        "",
        "Freeze v18 attachment as diagnostic target-construction evidence and select an independent-evidence repair plan as the next route.",
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
        f"connected_diagnostic_rows = {snap['connected_diagnostic_rows']}",
        f"connected_diagnostic_class_counts = {snap['connected_diagnostic_class_counts']}",
        f"geometry_support_rows = {snap['geometry_support_rows']}",
        f"geometry_support_class_counts = {snap['geometry_support_class_counts']}",
        f"full_quick_probe_risk_flags = {snap['full_quick_probe_risk_flags']}",
        f"slice_blocking_risk_flags = {snap['slice_blocking_risk_flags']}",
        "```",
        "",
        "## Why This Path",
        "",
        "The current blocker is not posterior capacity. The target itself is still too close to geometry/witness summaries and construction metadata. Running a stronger combiner would only learn this artifact.",
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
            "- Multi-view or mesh evidence is allowed only as future audit/confirmation evidence, not as model input.",
            "- Hidden fields remain audit/control metadata only.",
            "- H001 and paper artifacts are not modified.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    audit = read_json(audit_dir / "summary.json")
    validation_errors = validate_audit(audit)
    options = build_option_matrix(audit)
    plan = build_selected_plan(audit)

    if validation_errors:
        status = "h002_reliability_target_v18_attachment_deferred_path_decision_after_audit_errors"
        selected_path = "blocked_by_validation_errors"
        next_todo = EXPECTED_NEXT_TODO
    else:
        status = STATUS
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
        "schema_version": "h002_reliability_target_v18_attachment_deferred_path_decision_after_audit_v1",
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
        "option_verdicts": {item["option"]: item["verdict"] for item in options},
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
            "multi_view_as_audit_or_confirmation_evidence_only": True,
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
    print(f"multi_view_as_model_input={summary['boundary']['multi_view_as_model_input']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
