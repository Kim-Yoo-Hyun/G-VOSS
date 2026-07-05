#!/usr/bin/env python3
"""Decide the H002 path after the v22 hanging-on target-independence audit."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_path_decision_after_audit"

EXPECTED_AUDIT_STATUS = (
    "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_"
    "target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
)
EXPECTED_AUDIT_NEXT = "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_path_decision_after_audit"

STATUS = (
    "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_"
    "path_decision_select_v23_positive_anchor_repair_plan"
)
SELECTED_PATH = "freeze_v22_hanging_on_strict_diagnostic_select_v23_positive_anchor_repair_plan"
NEXT_TODO = "reliability_target_v23_hanging_on_positive_anchor_repair_plan"


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


def read_slice_rows(path: Path) -> list[dict[str, Any]]:
    path = as_abs(path)
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def validate_audit(audit: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "expected": EXPECTED_AUDIT_STATUS, "actual": audit.get("status")})
    if audit.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "expected": EXPECTED_AUDIT_NEXT, "actual": audit.get("next_todo")})
    if audit.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit.get("validation_errors")})

    relation = audit.get("target_decisions", {}).get("relation_binary", {})
    if relation.get("class_counts") != {"0": 193, "1": 9}:
        errors.append({"error_type": "unexpected_relation_class_counts", "expected": {"0": 193, "1": 9}, "actual": relation.get("class_counts")})
    if relation.get("class_mass_pass") is not False:
        errors.append({"error_type": "relation_class_mass_unexpectedly_passed", "actual": relation.get("class_mass_pass")})
    if relation.get("posterior_allowed") is not False:
        errors.append({"error_type": "relation_posterior_unexpectedly_allowed", "actual": relation.get("posterior_allowed")})
    if relation.get("strict_clear_slice_count") != 0:
        errors.append({"error_type": "relation_strict_clear_slice_unexpected", "actual": relation.get("strict_clear_slice_count")})
    if relation.get("diagnostic_clear_slice_count") != 0:
        errors.append({"error_type": "relation_diagnostic_clear_slice_unexpected", "actual": relation.get("diagnostic_clear_slice_count")})

    counts = audit.get("counts", {})
    if counts.get("full_quick_probe_risk_flags") != 107:
        errors.append({"error_type": "unexpected_full_quick_probe_risk_flags", "expected": 107, "actual": counts.get("full_quick_probe_risk_flags")})
    if counts.get("slice_blocking_risk_flags") != 1666:
        errors.append({"error_type": "unexpected_slice_blocking_risk_flags", "expected": 1666, "actual": counts.get("slice_blocking_risk_flags")})

    boundary = audit.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "hidden_fields_as_model_input",
        "existing_gt_match_axis_as_model_input",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "h001_artifacts_modified",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "audit_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def critical_slice_snapshot(audit_dir: Path) -> dict[str, Any]:
    rows = read_slice_rows(audit_dir / "controlled_slice_audit.csv")
    wanted = {
        "full",
        "same_visible_pair",
        "same_strict_group",
        "same_scan",
        "same_subject_label",
        "same_object_label",
        "same_geometry_bucket",
        "same_rank_band",
        "same_gt_status",
    }
    out: dict[str, Any] = {}
    for row in rows:
        if row.get("target") != "relation_binary" or row.get("slice_name") not in wanted:
            continue
        out[row["slice_name"]] = {
            "rows": int(row["rows"]),
            "class_counts": row["class_counts"],
            "min_class_count": int(row["min_class_count"]),
            "mixed_groups": int(row["mixed_groups"]),
            "blocking_risk_flags": int(row["blocking_risk_flags"]),
            "strict_clear": row["strict_clear"] == "True",
            "diagnostic_clear": row["diagnostic_clear"] == "True",
            "top_blocking_predictors": row["top_blocking_predictors"],
        }
    return out


def build_option_matrix(audit: dict[str, Any]) -> list[dict[str, Any]]:
    relation = audit["target_decisions"]["relation_binary"]
    geometry = audit["target_decisions"]["geometry_support_binary"]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": (
                f"Primary binary target is {relation['class_counts']} with min class {relation['min_class_count']}; "
                "strict/diagnostic clear slices are 0/0."
            ),
        },
        {
            "option": "train_on_balanced_9_9_slice",
            "verdict": "reject",
            "reason": "The largest balanced full slice has only 18 rows and still carries object, endpoint, geometry-support, and scan shortcuts.",
        },
        {
            "option": "try_stronger_posterior_combiner_now",
            "verdict": "reject",
            "reason": "The bottleneck is target construction. A stronger combiner would fit reject-heavy construction artifacts, not factorized reliability.",
        },
        {
            "option": "use_geometry_support_as_primary_target",
            "verdict": "reject",
            "reason": (
                f"Geometry support mirrors the relation target in v22 ({geometry['class_counts']}) and is an evidence axis, "
                "not the relation-level reliability label."
            ),
        },
        {
            "option": "label_more_rows_with_same_v22_recipe",
            "verdict": "reject_for_now",
            "reason": "The strict packet already sampled 240 rows from the strongest controlled route and produced only 9 accepts; repeating it is likely to repeat positive sparsity.",
        },
        {
            "option": "freeze_v22_as_diagnostic_only",
            "verdict": "select",
            "reason": "v22 is useful negative target-construction evidence but is not a posterior-ready target.",
        },
        {
            "option": "positive_anchor_repair_plan",
            "verdict": "select_next",
            "reason": (
                "The observed accepts are concentrated in real hanging-anchor cases. The next route should test whether "
                "enough accept/reject contrasts exist inside matched subject-anchor affordance cells, rather than sampling "
                "generic hanging-on candidates."
            ),
        },
        {
            "option": "promote_attached_to_or_connected_to_primary_now",
            "verdict": "reject",
            "reason": "`attached to` lost strict capacity in v21 and `connected to` remains functional-connection ambiguous without a stronger criterion.",
        },
        {
            "option": "multi_view_or_mesh_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": "Multi-view/mesh remains audit and label-confirmation evidence until an independent reliability target exists.",
        },
        {
            "option": "conclude_h002_is_invalid",
            "verdict": "reject",
            "reason": "The result shows the current target is invalid for posterior testing; it does not falsify the semantic/geometry/reliability factorization hypothesis.",
        },
    ]


def build_next_contract(audit: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": NEXT_TODO,
        "purpose": (
            "Repair the positive-sparse `hanging on` target by first testing whether accept-rich but "
            "shortcut-controlled positive-anchor strata exist in the full train pool."
        ),
        "split": "train_only",
        "posterior_smoke_allowed": False,
        "validation_or_test_allowed": False,
        "fills_new_labels_in_next_step": False,
        "primary_relation_scope": ["hanging on"],
        "diagnostic_relation_scope": ["attached to", "connected to"],
        "repair_principle": (
            "Do not simply add easy positives. Mine positive-anchor cells only if each positive cell can be "
            "paired with hard negatives under matched subject/anchor family, rank band, geometry bucket, and coverage."
        ),
        "candidate_positive_anchor_examples": [
            "curtain hanging on window/door/blinds-like anchor",
            "towel hanging on rack/door/handle-like anchor",
            "bag hanging on door/hook/chair-like anchor",
            "clothes/cloth hanging on rail/stand-like anchor",
        ],
        "required_controls": {
            "predicate_label": "fixed_to_hanging_on",
            "subject_affordance_family": "matched_or_capped",
            "anchor_affordance_family": "matched_or_capped",
            "subject_label": "capped_and_reported",
            "object_label": "capped_and_reported",
            "rank_band": "matched_or_balanced",
            "geometry_bucket": "matched_or_balanced",
            "coverage_tier": "matched_or_balanced",
            "scan_id": "capped",
            "visible_endpoint_pair": "capped",
        },
        "pre_label_capacity_gates": {
            "positive_anchor_candidate_rows_min": 300,
            "matched_positive_negative_cells_min": 30,
            "balanced_proxy_capacity_min": 160,
            "max_single_subject_label_share": 0.20,
            "max_single_object_label_share": 0.20,
            "max_single_scan_share": 0.05,
            "max_visible_endpoint_pair_share": 0.04,
        },
        "post_label_gates_if_later_materialized": {
            "accept_reject_minimum": "60/60",
            "strict_clear_slice_required": True,
            "same_visible_pair_or_affordance_cell_mixed_required": True,
            "visible_leakage_hits": 0,
        },
        "blocked_until_after_repair_plan": [
            "candidate_mining",
            "audit_packet_materialization",
            "label_fill",
            "label_ingestion",
            "target_independence_audit",
            "posterior_smoke",
            "multi_view_as_model_input",
        ],
        "fallback_if_capacity_fails": (
            "Stop attachment-deferred target construction as a posterior route and write a blocker synthesis "
            "rather than weakening controls."
        ),
        "input_evidence": {
            "v22_relation_binary": audit["target_decisions"]["relation_binary"]["class_counts"],
            "v22_risk_flags": audit["counts"]["full_quick_probe_risk_flags"],
            "v22_slice_blocking_flags": audit["counts"]["slice_blocking_risk_flags"],
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    relation = summary["audit_snapshot"]["relation_binary"]
    lines = [
        "# H002 V22 Hanging-On Path Decision",
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
        "## Input Audit",
        "",
        "```text",
        f"relation_binary_rows = {relation['rows']}",
        f"relation_binary_counts = {relation['class_counts']}",
        f"min_class_count = {relation['min_class_count']}",
        f"strict_clear_slices = {relation['strict_clear_slice_count']}",
        f"diagnostic_clear_slices = {relation['diagnostic_clear_slice_count']}",
        f"quick_probe_risk_flags = {summary['audit_snapshot']['counts']['full_quick_probe_risk_flags']}",
        f"slice_blocking_risk_flags = {summary['audit_snapshot']['counts']['slice_blocking_risk_flags']}",
        "```",
        "",
        "## Decision",
        "",
        "v22 `hanging on` strict target은 posterior target으로 승격하지 않는다. Diagnostic-only negative "
        "target-construction evidence로 고정한다.",
        "",
        "다음 route는 `v23_hanging_on_positive_anchor_repair_plan`으로 선택한다. 목적은 generic "
        "`hanging on` 후보를 더 많이 뽑는 것이 아니라, 실제 accept가 발생하는 hanging-anchor cell 안에서 "
        "accept/reject contrast가 충분히 존재하는지 먼저 검증하는 것이다.",
        "",
        "## Why",
        "",
        "- 현재 target은 `9/193`으로 severe positive-sparse다.",
        "- balanced full slice도 `9/9`에 불과하고 같은 visible endpoint pair slice는 0 rows다.",
        "- 같은 recipe로 더 라벨링하면 reject-heavy target을 반복할 가능성이 크다.",
        "- 하지만 9개 accept는 실제 hanging-anchor 사례가 존재함을 보여주므로, positive-anchor cell을 "
        "통제된 방식으로 따로 검사할 가치는 남아 있다.",
        "",
        "## Option Matrix",
        "",
    ]
    for option in summary["option_matrix"]:
        lines.append(f"- `{option['option']}`: {option['verdict']} - {option['reason']}")
    lines.extend(
        [
            "",
            "## Next Contract",
            "",
            "```text",
            f"name = {summary['next_contract']['name']}",
            f"primary_relation_scope = {summary['next_contract']['primary_relation_scope']}",
            f"diagnostic_relation_scope = {summary['next_contract']['diagnostic_relation_scope']}",
            f"posterior_smoke_allowed = {summary['next_contract']['posterior_smoke_allowed']}",
            "```",
            "",
            "The repair plan must not add easy positives unless matched hard negatives exist under subject-anchor "
            "affordance, rank, geometry, coverage, scan, and endpoint controls.",
            "",
            "## Boundary",
            "",
            "- Train-only H002 hypothesis artifact.",
            "- No validation/test rows used.",
            "- No labels filled.",
            "- No posterior trained or evaluated.",
            "- Multi-view/mesh remain audit/confirmation evidence only.",
            "- H001 and paper artifacts were not modified.",
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
    slices = critical_slice_snapshot(audit_dir)
    option_matrix = build_option_matrix(audit)
    next_contract = build_next_contract(audit)

    output_paths = {
        "summary": output_dir / "summary.json",
        "path_decision": output_dir / "path_decision.json",
        "report": output_dir / "report.md",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    path_decision = {
        "selected_path": SELECTED_PATH,
        "decision": "freeze_v22_as_diagnostic_only_and_plan_positive_anchor_repair",
        "rationale": [
            "v22 primary binary target is too positive-sparse for posterior testing.",
            "No strict or diagnostic clear controlled slice exists.",
            "The repeated bottleneck is target construction, not posterior combiner strength.",
            "Positive-anchor repair is the only remaining local route that directly addresses the positive-sparse cause without weakening shortcut controls.",
        ],
        "rejected_shortcuts": [
            "balanced_9_9_training",
            "same_recipe_more_labels",
            "geometry_support_as_primary",
            "stronger_combiner_before_target_repair",
            "multi_view_as_model_input_before_target_independence",
        ],
        "next_contract": next_contract,
    }

    summary = {
        "schema_version": "h002_reliability_target_v22_hanging_on_path_decision_v1",
        "status": STATUS if not validation_errors else STATUS + "_errors",
        "selected_path": SELECTED_PATH,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_artifacts": {
            "audit_summary": rel_path(audit_dir / "summary.json"),
            "audit_report": rel_path(audit_dir / "report.md"),
            "controlled_slice_audit": rel_path(audit_dir / "controlled_slice_audit.csv"),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "audit_snapshot": {
            "counts": audit.get("counts", {}),
            "relation_binary": audit.get("target_decisions", {}).get("relation_binary", {}),
            "geometry_support_binary": audit.get("target_decisions", {}).get("geometry_support_binary", {}),
            "critical_relation_slices": slices,
        },
        "option_matrix": option_matrix,
        "path_decision": path_decision,
        "next_contract": next_contract,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "hidden_fields_as_model_input": False,
            "existing_gt_match_axis_as_model_input": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "h001_artifacts_modified": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["path_decision"], path_decision)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    relation = summary["audit_snapshot"]["relation_binary"]
    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next={summary['next_todo']}")
    print(f"relation_counts={relation['class_counts']}")
    print(f"strict_clear={relation['strict_clear_slice_count']}")
    print(f"diagnostic_clear={relation['diagnostic_clear_slice_count']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
