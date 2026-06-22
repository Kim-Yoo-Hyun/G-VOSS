#!/usr/bin/env python3
"""Decide the H002 path after v6 shortcut-controlled target independence audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v6_shortcut_controlled_label_ingestion_codex_proxy_user_requested"
DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v6_shortcut_controlled_target_independence_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v6_shortcut_controlled_path_decision_codex_proxy_user_requested"

RELIABILITY_MULTICLASS = "relation_reliability_state_v6_multiclass_target"
RELIABILITY_BINARY = "relation_reliability_v6_binary_target"
GEOMETRY_TARGET = "geometry_support_v6_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v6_binary_target"

SELECTED_PATH = "v7_object_cell_evidence_contrast_feasibility_scan"
NEXT_TODO = "reliability_target_v7_object_cell_evidence_contrast_feasibility_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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


def target_snapshot(audit: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for target_name in [RELIABILITY_MULTICLASS, RELIABILITY_BINARY, GEOMETRY_TARGET, USEFULNESS_TARGET]:
        decision = audit["target_decisions"][target_name]
        original = decision["original"]
        strict = decision.get("recommended_strict_slice")
        diagnostic = decision.get("recommended_diagnostic_slice")
        output[target_name] = {
            "status": decision["status"],
            "rows": original["rows"],
            "min_class": original["min_class"],
            "class_counts": original["class_counts"],
            "strict_slice": strict["slice_name"] if strict else "none",
            "diagnostic_slice": diagnostic["slice_name"] if diagnostic else "none",
            "risk_counts": {
                "hidden_sampling_axis": original.get("hidden_sampling_axis_risk_count", 0),
                "endpoint_object_structure": original.get("endpoint_object_structure_risk_count", 0),
                "geometry_alignment": original.get("geometry_alignment_risk_count", 0),
                "construction_coverage": original.get("construction_coverage_risk_count", 0),
                "hidden_machine_hint": original.get("hidden_machine_hint_risk_count", 0),
                "visible_object_identity": original.get("visible_object_identity_risk_count", 0),
                "visible_relation_surface": original.get("visible_relation_surface_risk_count", 0),
            },
            "top_risks": {
                "hidden_sampling_axis": original.get("top_hidden_sampling_axis_risks", [])[:4],
                "endpoint_object_structure": original.get("top_endpoint_object_structure_risks", [])[:4],
                "geometry_alignment": original.get("top_geometry_alignment_risks", [])[:4],
                "construction_coverage": original.get("top_construction_coverage_risks", [])[:4],
                "hidden_machine_hint": original.get("top_hidden_machine_hint_risks", [])[:2],
                "visible_object_identity": original.get("top_visible_object_identity_risks", [])[:3],
            },
        }
    return output


def slice_snapshot(audit: dict[str, Any]) -> dict[str, Any]:
    selected = [
        "original_v6",
        "candidate_bucket_balanced_v6",
        "rank_band_balanced_v6",
        "geometry_status_balanced_v6",
        "source_geometry_balanced_v6",
        "family_bucket_balanced_v6",
        "object_family_cell_balanced_v6",
        "subject_object_family_cell_balanced_v6",
        "subject_object_label_pair_balanced_v6",
        "machine_hint_balanced_v6",
    ]
    output: dict[str, Any] = {}
    for target_name in [RELIABILITY_MULTICLASS, RELIABILITY_BINARY, GEOMETRY_TARGET, USEFULNESS_TARGET]:
        target_rows = {row["slice_name"]: row for row in audit["slice_summaries"] if row["target_name"] == target_name}
        output[target_name] = {
            name: {
                "rows": target_rows[name]["rows"],
                "min_class": target_rows[name]["min_class"],
                "blocking_risk": target_rows[name]["blocking_risk"],
                "hidden_sampling_axis_risk_count": target_rows[name]["hidden_sampling_axis_risk_count"],
                "endpoint_object_structure_risk_count": target_rows[name]["endpoint_object_structure_risk_count"],
                "geometry_alignment_risk_count": target_rows[name]["geometry_alignment_risk_count"],
                "construction_coverage_risk_count": target_rows[name]["construction_coverage_risk_count"],
                "visible_object_identity_risk_count": target_rows[name]["visible_object_identity_risk_count"],
                "strict_candidate": target_rows[name]["strict_candidate"],
                "diagnostic_candidate": target_rows[name]["diagnostic_candidate"],
            }
            for name in selected
            if name in target_rows
        }
    return output


def validate_upstream(ingestion: dict[str, Any], audit: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_ingestion_status = "h002_reliability_target_v6_shortcut_controlled_label_ingested_with_probe_risk"
    expected_audit_status = "h002_reliability_target_v6_shortcut_controlled_target_independence_audit_blocked_shortcut_risk"
    if ingestion.get("status") != expected_ingestion_status:
        errors.append({"error_type": "unexpected_ingestion_status", "expected": expected_ingestion_status, "actual": ingestion.get("status")})
    if audit.get("status") != expected_audit_status:
        errors.append({"error_type": "unexpected_audit_status", "expected": expected_audit_status, "actual": audit.get("status")})
    if audit.get("next_todo") != "reliability_target_v6_shortcut_controlled_path_decision":
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit.get("next_todo")})
    if audit.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit.get("validation_errors")})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_smoke_allowed", "paper_evidence_allowed"]:
        if audit.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "audit_boundary_violation", "key": key, "actual": audit.get("boundary", {}).get(key)})
    if audit["target_decisions"][RELIABILITY_MULTICLASS]["original"]["min_class"] < 40:
        errors.append({"error_type": "unexpected_primary_mass_too_small_for_v6_path_decision"})
    return errors


def option_matrix(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    primary = snapshot[RELIABILITY_MULTICLASS]
    binary = snapshot[RELIABILITY_BINARY]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "The primary target has usable mass, but no strict or diagnostic controlled slice; a posterior result would be dominated by object/category shortcuts.",
        },
        {
            "option": "swap_in_sota_combiner_now",
            "verdict": "reject_for_now",
            "reason": "The bottleneck is not the posterior combiner; it is target independence. A stronger combiner would likely learn object-pair/category shortcuts faster.",
        },
        {
            "option": "class_weight_or_rebalance_existing_v6_labels",
            "verdict": "reject",
            "reason": f"Class mass is not the blocker: primary min class is {primary['min_class']}. Reweighting does not remove shortcut correlation.",
        },
        {
            "option": "use_binary_reliability_target",
            "verdict": "reject_as_primary",
            "reason": f"Binary target has {binary['rows']} rows with balanced classes, but it also has no strict/diagnostic slice and loses the abstain/uncertainty axis.",
        },
        {
            "option": "use_geometry_support_or_usefulness_as_main_target",
            "verdict": "reject",
            "reason": "These are auxiliary evidence axes. Promoting them would change H002 from relation reliability to geometry support or utility prediction.",
        },
        {
            "option": "expand_same_v6_family_bucket_sampling",
            "verdict": "reject_as_primary",
            "reason": "Family/bucket balancing already failed. More rows from the same construction can increase mass while preserving the same object/category shortcut.",
        },
        {
            "option": "narrow_to_single_relation_or_common_object_labels",
            "verdict": "reject_as_immediate_solution",
            "reason": "Narrowing can hide the shortcut instead of solving it unless it is preceded by a feasibility scan that proves within-cell evidence contrast remains.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": "Multi-view may help label ambiguity, but adding it now would confound target-construction shortcut risk with a stronger evidence source.",
        },
        {
            "option": SELECTED_PATH,
            "verdict": "select",
            "reason": "Keep the v6 reliability state schema, but change sampling from family/bucket-balanced rows to object/category-controlled evidence contrasts before any new label fill.",
        },
        {
            "option": "freeze_h002_as_rga_diagnostic_framework",
            "verdict": "fallback",
            "reason": "If the next feasibility scan finds no object/category-controlled contrast capacity, stop forcing posterior learning and frame H002 as an RGA diagnostic/benchmark contribution.",
        },
    ]


def risk_to_action_matrix(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    primary = snapshot[RELIABILITY_MULTICLASS]
    binary = snapshot[RELIABILITY_BINARY]
    return [
        {
            "risk": "subject_object_category_determines_primary_target",
            "evidence": primary["top_risks"]["endpoint_object_structure"][:3],
            "action": "Next sampling must search for candidate groups where object/category is held fixed but semantic rank and continuous geometry evidence vary.",
            "gate": "subject_object_family_cell and subject_object_label_pair cannot remain blocking risks after label fill.",
        },
        {
            "risk": "binary_target_repeats_same_shortcut",
            "evidence": binary["top_risks"]["endpoint_object_structure"][:3],
            "action": "Do not collapse v6 to binary as the main target; keep abstain/uncertainty as a first-class state.",
            "gate": "binary diagnostic can be reported only after the multiclass target passes independence gates.",
        },
        {
            "risk": "visible_object_labels_explain_target",
            "evidence": primary["top_risks"]["visible_object_identity"],
            "action": "Visible subject/object labels should be used for grouping/control and audit, not as direct posterior features in the first proof.",
            "gate": "same-object-label or object-family grouped controls must remain nontrivial.",
        },
        {
            "risk": "geometry_status_balancing_is_insufficient",
            "evidence": "geometry_status_balanced_v6 and source_geometry_balanced_v6 still have endpoint/object and visible-object risks",
            "action": "Use continuous geometry evidence/residual bands inside object-category cells rather than frozen geometry_status alone.",
            "gate": "feasibility scan must show mixed geometry residual bands within object/category-controlled cells.",
        },
        {
            "risk": "same_construction_expansion_would_not_fix_independence",
            "evidence": "family/bucket/candidate/rank balanced slices remain blocked",
            "action": "Run feasibility before candidate mining or new label fill.",
            "gate": "selection should be based on pre-label capacity, not post-hoc label outcomes.",
        },
    ]


def next_plan(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "kept_target_schema": "relation_reliability_state_v6 = accept_reliable / reject_unreliable / abstain_uncertain",
        "objective": (
            "Check whether the full train pool contains object/category-controlled evidence-contrast cells that can support "
            "a relation reliability target without leaking target labels through object identity."
        ),
        "feasibility_scan_unit": [
            "predicate_family",
            "predicate_label or typed predicate group",
            "subject_object_family_cell or relaxed object_family_cell",
            "endpoint_flag_pattern",
        ],
        "contrast_axes_to_require": [
            "semantic rank/score band variation",
            "continuous geometry residual or p_geom_valid band variation",
            "high-semantic/low-geometry and low-semantic/high-geometry mismatch coverage",
            "coverage/evaluability variation recorded separately",
        ],
        "candidate_mining_not_allowed_yet": True,
        "new_label_fill_not_allowed_yet": True,
        "posterior_smoke_not_allowed_yet": True,
        "minimum_feasibility_gates": {
            "primary_groups_with_mixed_semantic_geometry_evidence": ">= 20",
            "expected_rows_after_caps": ">= 160",
            "max_single_object_label_pair_share": "<= 0.10",
            "max_single_subject_object_family_cell_share": "<= 0.10",
            "support_contact_and_relative_vertical_both_present": True,
            "no_validation_or_test_usage": True,
        },
        "fallback_if_feasibility_fails": "freeze_h002_as_rga_diagnostic_framework_or_restrict_to_new_relation_family_after_user_confirmation",
        "posterior_reopen_conditions": [
            "the new label batch keeps multiclass mass for accept/reject/abstain",
            "target-independence audit finds a strict or at least predeclared diagnostic controlled slice",
            "object/category grouping no longer predicts target above risk thresholds",
            "semantic/geometry/coverage/uncertainty features are deployable and not review labels",
        ],
        "why_this_is_principled": (
            "The observed failure mechanism is object/category leakage. The selected path changes the sampling unit so the "
            "hypothesis is tested inside object/category-controlled evidence contrasts, rather than adding model capacity."
        ),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    snapshot = summary["target_snapshot"]
    primary = snapshot[RELIABILITY_MULTICLASS]
    binary = snapshot[RELIABILITY_BINARY]
    lines = [
        "# H002 Reliability Target V6 Shortcut-Controlled Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage decision.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- No new labels are filled.",
        "- H001 artifacts are not modified.",
        "- Multi-view remains audit/label evidence only, not model input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Selected path:",
        "",
        f"`{summary['selected_path']}`",
        "",
        "Next TODO:",
        "",
        f"`{summary['next_todo']}`",
        "",
        "## Reason",
        "",
        summary["decision"],
        "",
        "## Audit Snapshot",
        "",
        "| Target | Status | Rows | Min Class | Class Counts | Strict Slice | Diagnostic Slice |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for target_name, target in snapshot.items():
        lines.append(
            f"| `{target_name}` | `{target['status']}` | {target['rows']} | {target['min_class']} | "
            f"`{target['class_counts']}` | `{target['strict_slice']}` | `{target['diagnostic_slice']}` |"
        )

    lines.extend(
        [
            "",
            "## Main Blocker",
            "",
            "The current v6 target is not blocked by label mass. It is blocked because object/category structure predicts the target.",
            "",
            "Primary multiclass top risks:",
            "",
        ]
    )
    for item in primary["top_risks"]["endpoint_object_structure"][:4]:
        lines.append(
            f"- `{item['group_key']}`: NMI `{item['normalized_mutual_information']:.4f}`, "
            f"majority acc `{item['majority_rule_accuracy']:.4f}`, class-rate range `{item['class_rate_range']:.4f}`"
        )
    lines.extend(["", "Binary reliability top risks:", ""])
    for item in binary["top_risks"]["endpoint_object_structure"][:4]:
        lines.append(
            f"- `{item['group_key']}`: NMI `{item['normalized_mutual_information']:.4f}`, "
            f"majority acc `{item['majority_rule_accuracy']:.4f}`, class-rate range `{item['class_rate_range']:.4f}`"
        )

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
            "## Selected Next Plan",
            "",
            f"- selected path: `{summary['next_plan']['selected_path']}`",
            f"- target schema kept: `{summary['next_plan']['kept_target_schema']}`",
            f"- objective: {summary['next_plan']['objective']}",
            "",
            "Feasibility gates:",
            "",
        ]
    )
    for key, value in summary["next_plan"]["minimum_feasibility_gates"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(
        [
            "",
            "Posterior reopen conditions:",
            "",
        ]
    )
    for item in summary["next_plan"]["posterior_reopen_conditions"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    ingestion_dir = as_abs(args.ingestion_dir)
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    ingestion = read_json(ingestion_dir / "summary.json")
    audit = read_json(audit_dir / "summary.json")
    errors = validate_upstream(ingestion, audit)
    snapshot = target_snapshot(audit)
    slices = slice_snapshot(audit)
    options = option_matrix(snapshot)
    risk_actions = risk_to_action_matrix(snapshot)
    plan = next_plan(snapshot)

    status = "h002_reliability_target_v6_shortcut_controlled_path_decision_select_v7_object_cell_evidence_contrast_feasibility"
    decision = (
        "Do not run posterior smoke or change the combiner yet. Keep the v6 multiclass reliability schema, "
        "but change the next work unit to an object/category-controlled evidence-contrast feasibility scan. "
        "This directly targets the observed failure mechanism: target labels are predictable from object/category structure."
    )
    if errors:
        status = "h002_reliability_target_v6_shortcut_controlled_path_decision_errors"
        decision = "Fix upstream audit or ingestion errors before selecting the next H002 path."
        plan["selected_path"] = "fix_upstream_errors"
        plan["next_todo"] = "fix_reliability_target_v6_shortcut_controlled_path_decision_errors"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "risk_to_action_matrix": output_dir / "risk_to_action_matrix.json",
        "next_plan": output_dir / "next_plan.json",
        "validation_errors": output_dir / "validation_errors.json",
    }

    summary = {
        "schema_version": "h002_reliability_target_v6_shortcut_controlled_path_decision_summary_v1",
        "status": status,
        "created_at": created_at,
        "selected_path": plan["selected_path"],
        "decision": decision,
        "next_todo": plan["next_todo"],
        "input_paths": {
            "ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "target_independence_audit_summary": rel_path(audit_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "fills_new_labels": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
            "posterior_smoke_allowed": False,
        },
        "validation_errors": errors,
        "audit_status": audit.get("status"),
        "ingestion_status": ingestion.get("status"),
        "target_snapshot": snapshot,
        "slice_snapshot": slices,
        "option_matrix": options,
        "risk_to_action_matrix": risk_actions,
        "next_plan": plan,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["option_matrix"], options)
    write_json(output_paths["risk_to_action_matrix"], risk_actions)
    write_json(output_paths["next_plan"], plan)
    write_json(output_paths["validation_errors"], errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    primary = summary["target_snapshot"][RELIABILITY_MULTICLASS]
    binary = summary["target_snapshot"][RELIABILITY_BINARY]
    print(
        "status={status} selected={selected} primary_rows={primary_rows} "
        "primary_min={primary_min} primary_status={primary_status} binary_rows={binary_rows} "
        "binary_min={binary_min} errors={errors} posterior_allowed={posterior_allowed} "
        "validation_used={validation_used} test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            selected=summary["selected_path"],
            primary_rows=primary["rows"],
            primary_min=primary["min_class"],
            primary_status=primary["status"],
            binary_rows=binary["rows"],
            binary_min=binary["min_class"],
            errors=len(summary["validation_errors"]),
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
