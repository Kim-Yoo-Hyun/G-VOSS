#!/usr/bin/env python3
"""Decide the H002 path after v7 object-cell target independence audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_target_independence_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v7_path_decision_codex_proxy_user_requested"

RELIABILITY_MULTICLASS = "relation_reliability_state_v6_multiclass_target"
RELIABILITY_BINARY = "relation_reliability_v6_binary_target"
GEOMETRY_TARGET = "geometry_support_v6_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v6_binary_target"

SELECTED_PATH = "v8_endpoint_pair_counterfactual_feasibility_scan"
NEXT_TODO = "reliability_target_v8_endpoint_pair_counterfactual_feasibility_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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
            "top_risks": {
                "hidden_sampling_axis": original.get("top_hidden_sampling_axis_risks", [])[:4],
                "endpoint_object_structure": original.get("top_endpoint_object_structure_risks", [])[:5],
                "geometry_alignment": original.get("top_geometry_alignment_risks", [])[:4],
                "construction_coverage": original.get("top_construction_coverage_risks", [])[:4],
                "hidden_machine_hint": original.get("top_hidden_machine_hint_risks", [])[:3],
                "visible_relation_surface": original.get("top_visible_relation_surface_risks", [])[:3],
                "visible_object_identity": original.get("top_visible_object_identity_risks", [])[:3],
            },
        }
    return output


def validate_audit(audit: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_status = "h002_reliability_target_v7_object_cell_evidence_contrast_target_independence_audit_blocked_shortcut_risk"
    expected_next = "reliability_target_v7_object_cell_evidence_contrast_path_decision"
    if audit.get("status") != expected_status:
        errors.append({"error_type": "unexpected_audit_status", "expected": expected_status, "actual": audit.get("status")})
    if audit.get("next_todo") != expected_next:
        errors.append({"error_type": "unexpected_audit_next_todo", "expected": expected_next, "actual": audit.get("next_todo")})
    if audit.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit.get("validation_errors")})

    boundary = audit.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "review_fields_as_model_input",
        "hidden_sampling_axes_as_model_input",
        "multi_view_as_model_input",
        "paper_evidence_allowed",
        "paper_metric_evidence",
        "h001_artifacts_modified",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "audit_boundary_violation", "key": key, "expected": False, "actual": boundary.get(key)})
    if boundary.get("split") != "train_only":
        errors.append({"error_type": "unexpected_boundary_split", "expected": "train_only", "actual": boundary.get("split")})

    for target_name in [RELIABILITY_MULTICLASS, RELIABILITY_BINARY, GEOMETRY_TARGET, USEFULNESS_TARGET]:
        decision = audit["target_decisions"].get(target_name, {})
        if decision.get("status") != "blocked_shortcut_risk":
            errors.append({"error_type": "unexpected_target_status", "target_name": target_name, "actual": decision.get("status")})
        if decision.get("recommended_strict_slice") is not None:
            errors.append({"error_type": "unexpected_strict_slice", "target_name": target_name})
        if decision.get("recommended_diagnostic_slice") is not None:
            errors.append({"error_type": "unexpected_diagnostic_slice", "target_name": target_name})
    return errors


def option_matrix(snapshot: dict[str, Any]) -> list[dict[str, str]]:
    primary = snapshot[RELIABILITY_MULTICLASS]
    binary = snapshot[RELIABILITY_BINARY]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "No strict or diagnostic controlled slice clears object/category shortcut risk, so posterior performance would not test factorized reliability.",
        },
        {
            "option": "swap_in_sota_combiner_now",
            "verdict": "reject_for_now",
            "reason": "The observed failure is target construction, not combiner capacity. A stronger combiner can exploit object/category lookup more efficiently.",
        },
        {
            "option": "class_weight_or_threshold_tuning",
            "verdict": "reject",
            "reason": f"The primary target has usable mass with min class {primary['min_class']}; reweighting cannot remove endpoint/object leakage.",
        },
        {
            "option": "use_binary_reliability_as_primary",
            "verdict": "reject",
            "reason": f"The binary target has {binary['rows']} rows but repeats the same shortcut risk and discards the abstain/uncertainty state.",
        },
        {
            "option": "use_geometry_support_or_usefulness_as_primary",
            "verdict": "reject",
            "reason": "Those targets are auxiliary evidence axes. Promoting them would change H002 from relation reliability to geometry-support or utility prediction.",
        },
        {
            "option": "expand_v7_object_cell_sampling",
            "verdict": "reject_as_primary",
            "reason": "v7 already controls object-cell distribution, yet subject/object family and strict-group keys still nearly determine the target.",
        },
        {
            "option": "collect_more_labels_on_current_v7_sheet",
            "verdict": "reject_as_primary",
            "reason": "More labels on the same construction improve label provenance but do not address the sampling shortcut that the audit exposed.",
        },
        {
            "option": "add_object_labels_as_posterior_factors",
            "verdict": "reject_for_first_proof",
            "reason": "Object labels may be legitimate context later, but they are currently the dominant shortcut; first proof should avoid relying on them.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": "Multi-view is useful as audit evidence, but adding it before a clean target would confound feature gain with target shortcut.",
        },
        {
            "option": SELECTED_PATH,
            "verdict": "select",
            "reason": "Hold endpoint/object context fixed and ask whether predicate/evidence counterfactual contrasts remain; this directly attacks the shortcut mechanism.",
        },
        {
            "option": "freeze_h002_as_rga_diagnostic_benchmark",
            "verdict": "fallback",
            "reason": "If endpoint-pair counterfactual feasibility fails, stop forcing posterior learning and frame the contribution around RGA audit/benchmark evidence.",
        },
    ]


def risk_to_action_matrix(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    primary = snapshot[RELIABILITY_MULTICLASS]
    binary = snapshot[RELIABILITY_BINARY]
    geometry = snapshot[GEOMETRY_TARGET]
    return [
        {
            "risk": "object_category_lookup",
            "evidence": primary["top_risks"]["endpoint_object_structure"][:4],
            "action": "Use endpoint-pair or near-endpoint counterfactual groups so object identity is held fixed before label generation.",
            "success_gate": "subject_object_family_cell_hidden, strict_group_key_hidden, and subject_object_label_pair_hidden cannot remain blocking risks.",
        },
        {
            "risk": "binary_target_repeats_primary_shortcut",
            "evidence": binary["top_risks"]["endpoint_object_structure"][:4],
            "action": "Keep multiclass accept/reject/abstain as the main target; use binary only as diagnostic after a clean multiclass slice exists.",
            "success_gate": "binary target is not promoted unless multiclass target passes independence audit.",
        },
        {
            "risk": "geometry_support_is_not_reliability",
            "evidence": geometry["top_risks"]["endpoint_object_structure"][:4],
            "action": "Keep geometry support as an evidence axis, not as the target; target should ask relation reliability conditioned on endpoint and predicate.",
            "success_gate": "geometry target may support analysis but cannot replace relation reliability.",
        },
        {
            "risk": "frozen_status_shortcut",
            "evidence": "v7 can balance high-level buckets but still fails object/category control",
            "action": "Use continuous evidence contrast inside controlled endpoint/object cells instead of frozen satisfied/unsatisfied states as the main selector.",
            "success_gate": "selected cells contain variation in semantic rank/score and continuous geometry evidence before labels are filled.",
        },
        {
            "risk": "multi_view_confounds_target_construction",
            "evidence": "target has not passed independence audit without multi-view features",
            "action": "Continue using multi-view only for audit/confirmation until the core S/G/C/U factor target passes.",
            "success_gate": "multi-view can become V_mv_e only after a clean S_e/G_e/C_e/U_e target exists.",
        },
    ]


def next_plan() -> dict[str, Any]:
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "kept_target_schema": "relation_reliability_state_v6 = accept_reliable / reject_unreliable / abstain_uncertain",
        "new_sampling_principle": "endpoint/object context first, evidence contrast second",
        "objective": (
            "Scan the full train pool for endpoint-pair or near-endpoint counterfactual groups where object identity is fixed "
            "but predicate, semantic evidence, and geometry evidence vary enough to define relation reliability."
        ),
        "candidate_group_units": [
            "exact endpoint pair: scan_id + subgraph_id + subject_id + object_id",
            "directional endpoint pair with subject/object swap for asymmetric predicates",
            "same subject/object label pair inside the same scene only as a relaxed fallback",
            "same predicate family and endpoint pattern as a diagnostic control, not the primary unit",
        ],
        "contrast_types_to_search": [
            "same endpoint pair with multiple candidate predicates",
            "same endpoint pair with contradictory vertical direction candidates",
            "same endpoint pair with support/contact versus non-support alternatives",
            "subject/object swap counterfactual for asymmetric relations",
            "wrong-pair geometry control only after endpoint-pair groups are exhausted",
        ],
        "evidence_axes_to_require_before_labeling": [
            "semantic score or rank variation within controlled group",
            "continuous geometry evidence or p_geom_valid variation within controlled group",
            "coverage/evaluability recorded but not used as target",
            "both high-semantic/low-geometry and low-semantic/high-geometry cases when available",
        ],
        "minimum_feasibility_gates": {
            "exact_endpoint_pair_contrast_groups": ">= 20 preferred, else report relaxed fallback",
            "expected_rows_after_caps": ">= 120 for diagnostic, >= 200 for strict label batch",
            "min_predicate_family_count": "support_contact >= 40 and relative_vertical >= 40 if both remain in scope",
            "max_single_subject_object_label_pair_share": "<= 0.08",
            "max_single_subject_object_family_cell_share": "<= 0.08",
            "prelabel_hidden_target_use": False,
            "validation_or_test_usage": False,
        },
        "posterior_reopen_conditions": [
            "v8 label batch preserves accept/reject/abstain mass",
            "target-independence audit finds a strict or predeclared diagnostic controlled slice",
            "object/category grouping no longer predicts target above risk thresholds",
            "model inputs remain deployable evidence factors S_e/G_e/C_e/U_e, not review labels or hidden construction labels",
        ],
        "fallback_if_v8_fails": "freeze v7 as negative target-construction evidence and reframe H002 around RGA diagnostic/benchmark, or select a new relation family only after user confirmation",
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Reliability Target V7 Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage decision.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- No new labels are filled.",
        "- Multi-view remains audit evidence only.",
        "- H001 artifacts are not modified.",
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
        "## Decision",
        "",
        summary["decision"],
        "",
        "## Target Snapshot",
        "",
        "| Target | Status | Rows | Min Class | Class Counts | Strict Slice | Diagnostic Slice |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for target_name, target in summary["target_snapshot"].items():
        lines.append(
            f"| `{target_name}` | `{target['status']}` | {target['rows']} | {target['min_class']} | "
            f"`{target['class_counts']}` | `{target['strict_slice']}` | `{target['diagnostic_slice']}` |"
        )

    primary = summary["target_snapshot"][RELIABILITY_MULTICLASS]
    lines.extend(["", "## Main Blocker", ""])
    lines.append(
        "The blocker is not label mass. The blocker is that object/category structure predicts the target after v7 object-cell balancing."
    )
    lines.extend(["", "Primary reliability endpoint/object risks:", ""])
    for item in primary["top_risks"]["endpoint_object_structure"][:5]:
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
            "## Next Plan",
            "",
            f"- selected path: `{summary['next_plan']['selected_path']}`",
            f"- target schema kept: `{summary['next_plan']['kept_target_schema']}`",
            f"- sampling principle: `{summary['next_plan']['new_sampling_principle']}`",
            f"- objective: {summary['next_plan']['objective']}",
            "",
            "Candidate group units:",
            "",
        ]
    )
    for item in summary["next_plan"]["candidate_group_units"]:
        lines.append(f"- {item}")

    lines.extend(["", "Contrast types:", ""])
    for item in summary["next_plan"]["contrast_types_to_search"]:
        lines.append(f"- {item}")

    lines.extend(["", "Minimum feasibility gates:", ""])
    for key, value in summary["next_plan"]["minimum_feasibility_gates"].items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "Posterior reopen conditions:", ""])
    for item in summary["next_plan"]["posterior_reopen_conditions"]:
        lines.append(f"- {item}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).isoformat()
    audit = read_json(audit_dir / "summary.json")
    errors = validate_audit(audit)
    snapshot = target_snapshot(audit)
    options = option_matrix(snapshot)
    risk_actions = risk_to_action_matrix(snapshot)
    plan = next_plan()

    if errors:
        status = "h002_reliability_target_v7_path_decision_errors"
        decision = "Fix v7 target-independence audit errors before selecting a new path."
        selected_path = "fix_v7_path_decision_errors"
        next_todo = "fix_reliability_target_v7_path_decision_errors"
    else:
        status = "h002_reliability_target_v7_path_decision_select_v8_endpoint_pair_counterfactual_feasibility"
        decision = (
            "Do not run posterior smoke, do not replace the combiner, and do not expand the same v7 object-cell sampling. "
            "The next principled step is an endpoint-pair counterfactual feasibility scan that holds object identity fixed "
            "and tests whether relation-level semantic/geometry evidence contrast still exists."
        )
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "risk_to_action_matrix": output_dir / "risk_to_action_matrix.json",
        "next_plan": output_dir / "next_plan.json",
        "validation_errors": output_dir / "validation_errors.json",
    }

    summary = {
        "schema_version": "h002_reliability_target_v7_path_decision_summary_v1",
        "status": status,
        "created_at": created_at,
        "selected_path": selected_path,
        "decision": decision,
        "next_todo": next_todo,
        "input_paths": {
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
            "paper_metric_evidence": False,
            "posterior_smoke_allowed": False,
        },
        "validation_errors": errors,
        "audit_status": audit.get("status"),
        "target_snapshot": snapshot,
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
