#!/usr/bin/env python3
"""Decide the H002 path after the v21 attachment conditional contrast scan."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_CAPACITY_DIR = RGA_ROOT / "reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_after_capacity_scan"

EXPECTED_CAPACITY_STATUS = (
    "h002_reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan_"
    "blocked_predicate_imbalanced_strict_capacity"
)
EXPECTED_CAPACITY_NEXT = "reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_after_capacity_scan"

STATUS = (
    "h002_reliability_target_v21_attachment_deferred_conditional_contrast_path_decision_"
    "select_v22_hanging_on_strict_packet_plan"
)
SELECTED_PATH = "freeze_v21_capacity_diagnostic_select_hanging_on_strict_primary_attached_to_diagnostic_relaxed_probe"
NEXT_TODO = "reliability_target_v22_hanging_on_strict_conditional_contrast_packet_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
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


def validate_capacity(capacity: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if capacity.get("status") != EXPECTED_CAPACITY_STATUS:
        errors.append(
            {
                "error_type": "unexpected_capacity_status",
                "expected": EXPECTED_CAPACITY_STATUS,
                "actual": capacity.get("status"),
            }
        )
    if capacity.get("next_todo") != EXPECTED_CAPACITY_NEXT:
        errors.append(
            {
                "error_type": "unexpected_capacity_next_todo",
                "expected": EXPECTED_CAPACITY_NEXT,
                "actual": capacity.get("next_todo"),
            }
        )
    if capacity.get("validation_errors") != 0:
        errors.append({"error_type": "capacity_validation_errors_present", "actual": capacity.get("validation_errors")})

    boundary = capacity.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "human_label_claim",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "capacity_boundary_violation", "key": key, "actual": boundary.get(key)})

    decision = capacity.get("capacity_decision", {})
    if decision.get("capacity_pass") is not False:
        errors.append({"error_type": "capacity_expected_blocked_for_path_decision", "actual": decision.get("capacity_pass")})
    if decision.get("failed_checks") != ["strict_spec_each_primary_predicate_mixed_min_10"]:
        errors.append(
            {
                "error_type": "unexpected_failed_checks",
                "expected": ["strict_spec_each_primary_predicate_mixed_min_10"],
                "actual": decision.get("failed_checks"),
            }
        )

    strict = capacity.get("spec_summary_by_name", {}).get("same_predicate_rank_geometry_family", {})
    diagnostic = capacity.get("spec_summary_by_name", {}).get("same_predicate_rank_family", {})
    if strict.get("mixed_accept_reject_groups", 0) < 40:
        errors.append({"error_type": "strict_mixed_groups_too_low", "actual": strict.get("mixed_accept_reject_groups")})
    if strict.get("balanced_pair_capacity", 0) < 1000:
        errors.append({"error_type": "strict_balanced_capacity_too_low", "actual": strict.get("balanced_pair_capacity")})
    if set(strict.get("by_predicate", {}).keys()) != {"hanging on"}:
        errors.append({"error_type": "unexpected_strict_predicate_set", "actual": sorted(strict.get("by_predicate", {}).keys())})
    if set(diagnostic.get("by_predicate", {}).keys()) != {"attached to", "hanging on"}:
        errors.append(
            {"error_type": "unexpected_diagnostic_predicate_set", "actual": sorted(diagnostic.get("by_predicate", {}).keys())}
        )
    return errors


def strict_condition_rationale() -> dict[str, Any]:
    return {
        "is_dataset_ground_truth_rule": False,
        "is_h002_control_rule": True,
        "fields": ["predicate_label", "rank_band", "geometry_bucket", "object_family_pair"],
        "purpose": [
            "Prevent the target from being solved by predicate identity alone.",
            "Prevent the target from being solved by source rank or semantic-score band alone.",
            "Prevent the target from being solved by coarse geometry validity bucket alone.",
            "Prevent the target from being solved by subject/object category or object-family prior alone.",
            "Force any later posterior to explain residual reliability using factorized evidence rather than one shortcut axis.",
        ],
        "basis": [
            "Earlier H002 audits repeatedly failed because predicate, rank, endpoint, object label, or geometry-status shortcuts predicted labels.",
            "The H002 claim is not that geometry bucket alone is enough; the claim requires semantic score, geometry validity, coverage, uncertainty, and reliability to stay separable.",
            "A controlled slice is a standard experimental design principle: compare examples under matched confounders before claiming a factor contributes independent signal.",
        ],
        "not_a_final_model_input_rule": (
            "The strict fields are control/audit strata. They are not all intended as deployable model inputs, "
            "and they do not define the final relation ontology."
        ),
    }


def build_option_matrix(capacity: dict[str, Any]) -> list[dict[str, Any]]:
    strict = capacity["spec_summary_by_name"]["same_predicate_rank_geometry_family"]
    diagnostic = capacity["spec_summary_by_name"]["same_predicate_rank_family"]
    return [
        {
            "option": "two_predicate_strict_primary_attached_and_hanging",
            "verdict": "reject",
            "reason": (
                "The strict selected spec has mixed strata only for `hanging on`; `attached to` does not pass the "
                "per-primary-predicate mixed-stratum gate."
            ),
            "evidence": strict["by_predicate"],
        },
        {
            "option": "relax_geometry_bucket_and_use_both_predicates_as_primary",
            "verdict": "reject_for_primary_defer_as_diagnostic",
            "reason": (
                "The relaxed same-predicate/rank/object-family spec has much larger capacity, but removing geometry "
                "bucket control reopens the risk that the target is explained by coarse geometry bucket rather than "
                "factorized reliability."
            ),
            "evidence": diagnostic["by_predicate"],
        },
        {
            "option": "hanging_on_strict_primary_attached_to_diagnostic",
            "verdict": "select",
            "reason": (
                "`hanging on` is the only primary predicate that retains mixed proxy strata under predicate, rank, "
                "geometry bucket, and object-family controls. This is the strongest next target-construction route."
            ),
            "evidence": strict["by_predicate"].get("hanging on", {}),
        },
        {
            "option": "freeze_attachment_branch_as_diagnostic_only",
            "verdict": "reject_for_now",
            "reason": "Full-train strict capacity exists for `hanging on`, so stopping the branch now would discard a viable controlled target.",
        },
        {
            "option": "promote_connected_to_primary",
            "verdict": "reject",
            "reason": "`connected to` remains functional-connection ambiguous without stronger visual/mesh evidence.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": "Multi-view/mesh should remain audit evidence until a target-independent reliability target exists.",
        },
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "v21 is proxy capacity only. No human-confirmed target or target-independence audit exists for the selected strict route.",
        },
    ]


def build_next_contract(capacity: dict[str, Any]) -> dict[str, Any]:
    strict = capacity["spec_summary_by_name"]["same_predicate_rank_geometry_family"]
    return {
        "name": NEXT_TODO,
        "selected_primary_relation_scope": ["hanging on"],
        "diagnostic_relation_scope": ["attached to", "connected to"],
        "split": "train_only",
        "posterior_smoke_allowed": False,
        "validation_or_test_allowed": False,
        "packet_plan_allowed": True,
        "label_fill_allowed_in_next_step": False,
        "required_controls": {
            "predicate_label": "fixed_to_hanging_on",
            "rank_band": "balanced_or_capped",
            "geometry_bucket": "controlled_within_packet",
            "object_family_pair": "controlled_or_capped",
            "scan_id": "capped",
            "visible_endpoint_pair": "capped",
            "coverage_proxy": "reported_and_capped",
            "uncertainty_bucket": "reported_and_separated",
        },
        "pre_label_packet_gates": {
            "strict_mixed_groups_min": 80,
            "strict_balanced_capacity_min": 1000,
            "packet_rows_target": 240,
            "proxy_accept_reject_min_each": 80,
            "max_single_scan_share": 0.05,
            "max_visible_endpoint_pair_share": 0.04,
            "visible_leakage_hits": 0,
        },
        "hanging_on_capacity_snapshot": strict["by_predicate"].get("hanging on", {}),
        "blocked_until_after_packet_plan": [
            "candidate_materialization",
            "label_fill",
            "label_ingestion",
            "target_independence_audit",
            "posterior_smoke",
            "multi_view_as_model_input",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    strict = summary["capacity_snapshot"]["strict_spec"]
    diagnostic = summary["capacity_snapshot"]["diagnostic_spec"]
    lines = [
        "# H002 V21 Conditional Contrast Path Decision",
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
        "## Strict Condition",
        "",
        "strict condition은 데이터셋이 제공한 GT rule이 아니다. H002가 만든 hypothesis-stage control rule이다.",
        "",
        "```text",
        "strict_spec = same_predicate_rank_geometry_family",
        "fields = predicate_label + rank_band + geometry_bucket + object_family_pair",
        "```",
        "",
        "필요한 이유는 posterior target이 predicate, rank, coarse geometry bucket, object-family prior 중 하나만으로 "
        "풀리는 것을 막기 위해서다. 이전 H002 stage들이 반복적으로 shortcut 문제에 막혔기 때문에, v21에서는 "
        "label packet을 만들기 전에 full-train에서 이런 control이 가능한지를 먼저 확인했다.",
        "",
        "## Capacity Snapshot",
        "",
        "```text",
        f"strict_mixed_groups = {strict['mixed_accept_reject_groups']}",
        f"strict_balanced_capacity = {strict['balanced_pair_capacity']}",
        f"strict_by_predicate = {strict['by_predicate']}",
        f"diagnostic_mixed_groups = {diagnostic['mixed_accept_reject_groups']}",
        f"diagnostic_balanced_capacity = {diagnostic['balanced_pair_capacity']}",
        f"diagnostic_by_predicate = {diagnostic['by_predicate']}",
        "```",
        "",
        "## Decision",
        "",
        "`hanging on`을 strict primary 후보로 남기고, `attached to`는 diagnostic/relaxed probe로 낮춘다. "
        "`connected to`는 계속 diagnostic-only로 둔다.",
        "",
        "이 선택이 가장 보수적인 이유는 `hanging on`만 strict condition 안에서 mixed proxy strata를 유지하기 때문이다. "
        "`attached to`를 primary로 유지하려면 geometry bucket control을 풀어야 하는데, 그러면 이후 성능이 좋아져도 "
        "factorized reliability가 아니라 coarse geometry bucket shortcut 효과로 보일 위험이 크다.",
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
            f"selected_primary_relation_scope = {summary['next_contract']['selected_primary_relation_scope']}",
            f"diagnostic_relation_scope = {summary['next_contract']['diagnostic_relation_scope']}",
            "packet_plan_allowed = true",
            "label_fill_allowed_in_next_step = false",
            "posterior_smoke_allowed = false",
            "```",
            "",
            "## Boundary",
            "",
            "- Train-only H002 hypothesis artifact.",
            "- No validation/test rows were used.",
            "- No labels were filled or ingested.",
            "- No posterior was trained or evaluated.",
            "- Multi-view and mesh remain audit/confirmation evidence only.",
            "- H001 and paper artifacts were not modified.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    capacity_dir = as_abs(args.capacity_dir)
    output_dir = as_abs(args.output_dir)
    capacity = read_json(capacity_dir / "summary.json")
    validation_errors = validate_capacity(capacity)

    output_paths = {
        "summary": output_dir / "summary.json",
        "path_decision": output_dir / "path_decision.json",
        "report": output_dir / "report.md",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    option_matrix = build_option_matrix(capacity)
    next_contract = build_next_contract(capacity)
    path_decision = {
        "selected_path": SELECTED_PATH,
        "selected_next_todo": NEXT_TODO,
        "decision": "narrow_strict_primary_to_hanging_on_keep_attached_to_diagnostic",
        "strict_condition_rationale": strict_condition_rationale(),
        "option_matrix": option_matrix,
        "next_contract": next_contract,
    }

    summary = {
        "status": STATUS if not validation_errors else "validation_failed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "input_artifacts": {
            "capacity_summary": rel_path(capacity_dir / "summary.json"),
            "capacity_report": rel_path(capacity_dir / "report.md"),
            "relation_scope_status": rel_path(capacity_dir / "relation_scope_full_train_status.json"),
        },
        "output_artifacts": {key: rel_path(path) for key, path in output_paths.items()},
        "capacity_snapshot": {
            "counts": capacity["counts"],
            "capacity_decision": capacity["capacity_decision"],
            "strict_spec": capacity["spec_summary_by_name"]["same_predicate_rank_geometry_family"],
            "diagnostic_spec": capacity["spec_summary_by_name"]["same_predicate_rank_family"],
            "relation_scope_status": capacity["relation_scope_status"],
        },
        "strict_condition_rationale": strict_condition_rationale(),
        "option_matrix": option_matrix,
        "next_contract": next_contract,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["path_decision"], path_decision)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    strict = summary["capacity_snapshot"]["strict_spec"]
    diagnostic = summary["capacity_snapshot"]["diagnostic_spec"]
    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next={summary['next_todo']}")
    print(f"strict_mixed_groups={strict['mixed_accept_reject_groups']}")
    print(f"strict_by_predicate={strict['by_predicate']}")
    print(f"diagnostic_by_predicate={diagnostic['by_predicate']}")
    print(f"posterior_smoke_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
