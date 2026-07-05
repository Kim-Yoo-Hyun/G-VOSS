#!/usr/bin/env python3
"""Decide the H002 path after the v20 attachment audit-packet target audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / (
    "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_"
    "audit_packet_target_independence_audit"
)
DEFAULT_OUTPUT_DIR = RGA_ROOT / (
    "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_"
    "audit_packet_path_decision_after_audit"
)

EXPECTED_AUDIT_STATUS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_"
    "audit_packet_target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
)
EXPECTED_NEXT_TODO = (
    "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_"
    "audit_packet_path_decision_after_audit"
)

STATUS = (
    "h002_reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_"
    "audit_packet_path_decision_select_v21_conditional_contrast_capacity_scan"
)
SELECTED_PATH = (
    "freeze_v20_audit_packet_diagnostic_select_v21_conditional_contrast_capacity_scan"
)
NEXT_TODO = "reliability_target_v21_attachment_deferred_conditional_contrast_capacity_scan"


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
        errors.append(
            {
                "error_type": "unexpected_audit_status",
                "expected": EXPECTED_AUDIT_STATUS,
                "actual": audit.get("status"),
            }
        )
    if audit.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append(
            {
                "error_type": "unexpected_audit_next_todo",
                "expected": EXPECTED_NEXT_TODO,
                "actual": audit.get("next_todo"),
            }
        )
    if audit.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors_present", "actual": audit.get("validation_errors")})

    decisions = audit.get("target_decisions", {})
    relation = decisions.get("relation_binary", {})
    geometry = decisions.get("geometry_support_binary", {})
    connected = decisions.get("connected_diagnostic", {})

    expected_relation_counts = {"0": 182, "1": 25}
    if relation.get("class_counts") != expected_relation_counts:
        errors.append(
            {
                "error_type": "unexpected_relation_class_counts",
                "expected": expected_relation_counts,
                "actual": relation.get("class_counts"),
            }
        )
    if relation.get("posterior_allowed") is not False:
        errors.append({"error_type": "relation_posterior_unexpectedly_allowed", "actual": relation.get("posterior_allowed")})
    if relation.get("class_mass_pass") is not False:
        errors.append({"error_type": "relation_class_mass_unexpectedly_passed", "actual": relation.get("class_mass_pass")})
    if relation.get("strict_clear_slice_count") != 0:
        errors.append({"error_type": "relation_strict_clear_slice_unexpected", "actual": relation.get("strict_clear_slice_count")})
    if relation.get("diagnostic_clear_slice_count") != 0:
        errors.append(
            {
                "error_type": "relation_diagnostic_clear_slice_unexpected",
                "actual": relation.get("diagnostic_clear_slice_count"),
            }
        )
    if geometry.get("posterior_allowed") is not False:
        errors.append({"error_type": "geometry_support_unexpectedly_posterior_allowed", "actual": geometry.get("posterior_allowed")})
    if connected.get("posterior_allowed") is not False:
        errors.append({"error_type": "connected_diagnostic_unexpectedly_posterior_allowed", "actual": connected.get("posterior_allowed")})

    counts = audit.get("counts", {})
    if counts.get("full_quick_probe_risk_flags", 0) <= 0:
        errors.append({"error_type": "expected_full_probe_risk_not_found", "actual": counts.get("full_quick_probe_risk_flags")})
    if counts.get("slice_blocking_risk_flags", 0) <= 0:
        errors.append({"error_type": "expected_slice_risk_not_found", "actual": counts.get("slice_blocking_risk_flags")})

    boundary = audit.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "audit_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def load_top_risks(audit_dir: Path) -> list[dict[str, Any]]:
    risk_path = as_abs(audit_dir / "full_shortcut_risks.json")
    if not risk_path.exists():
        return []
    payload = json.loads(risk_path.read_text(encoding="utf-8"))
    rows = payload.get("risks", payload if isinstance(payload, list) else [])
    flagged = [row for row in rows if row.get("risk_flag")]
    flagged.sort(
        key=lambda row: (
            row.get("target") != "relation_binary",
            -float(row.get("majority_excess_over_baseline", 0.0)),
            -float(row.get("normalized_mutual_information", 0.0)),
        )
    )
    keep_fields = [
        "target",
        "predictor",
        "rows",
        "label_counts",
        "majority_baseline_accuracy",
        "majority_rule_accuracy",
        "majority_excess_over_baseline",
        "normalized_mutual_information",
    ]
    return [{key: row.get(key) for key in keep_fields} for row in flagged[:12]]


def build_option_matrix(audit: dict[str, Any]) -> list[dict[str, str]]:
    relation = audit["target_decisions"]["relation_binary"]
    connected = audit["target_decisions"]["connected_diagnostic"]
    geometry = audit["target_decisions"]["geometry_support_binary"]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": (
                f"Primary target is positive-sparse ({relation['class_counts']}) and has no strict or "
                "diagnostic clear slice."
            ),
        },
        {
            "option": "use_balanced_25_25_slice_as_posterior_target",
            "verdict": "reject",
            "reason": "A 25/25 slice is too small and still blocked by predicate/object/endpoint/geometry-support shortcuts.",
        },
        {
            "option": "try_stronger_posterior_combiner_now",
            "verdict": "reject",
            "reason": "The limiting factor is target construction; a stronger combiner would learn construction artifacts.",
        },
        {
            "option": "use_geometry_support_as_primary",
            "verdict": "reject",
            "reason": (
                f"Geometry support has class mass ({geometry['class_counts']}) but no strict independent slice and "
                "is an evidence axis, not the relation reliability target."
            ),
        },
        {
            "option": "promote_connected_to_primary",
            "verdict": "reject",
            "reason": (
                f"`connected to` remains diagnostic-only ({connected['class_counts']}); functional connection is "
                "not decidable from the current packet."
            ),
        },
        {
            "option": "label_more_rows_with_same_v20_recipe",
            "verdict": "defer",
            "reason": "More random packet rows may repeat the reject-heavy pattern; scan conditional contrast capacity first.",
        },
        {
            "option": "conclude_h002_factorization_is_unnecessary",
            "verdict": "reject",
            "reason": "The audit only shows the current 320-row target is not adequate; it does not test full-train capacity.",
        },
        {
            "option": "multi_view_or_mesh_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": "Multi-view/mesh remains audit evidence until a target-independent reliability target exists.",
        },
        {
            "option": "full_train_conditional_contrast_capacity_scan",
            "verdict": "select",
            "reason": "This directly tests whether the 320-row failure is a sampling artifact and whether factorized targets exist.",
        },
    ]


def build_next_contract() -> dict[str, Any]:
    return {
        "name": NEXT_TODO,
        "purpose": (
            "Scan the full train attachment pool for conditional strata where reliability cannot be "
            "explained by one easy axis alone."
        ),
        "split": "train_only",
        "posterior_smoke_allowed": False,
        "validation_or_test_allowed": False,
        "primary_relation_scope": ["attached to", "hanging on"],
        "diagnostic_relation_scope": ["connected to"],
        "contrast_questions": [
            "same predicate + same/near geometry-support proxy can still yield accept/reject candidates",
            "same predicate + same rank band can still yield accept/reject candidates",
            "same evidence tier + same coverage state can still contain mixed reliability candidates",
            "same object-pair family can still contain mixed reliability candidates",
            "uncertainty/coverage can explain abstain separately from reject",
        ],
        "strata_keys_to_scan": [
            "predicate_label",
            "rank_band_hidden_or_source_rank_bin",
            "geometry_support_proxy",
            "evidence_tier",
            "review_coverage_or_source_coverage_proxy",
            "uncertainty_proxy",
            "subject_object_visible_pair_or_family",
            "endpoint_identity_proxy",
            "gt_label_match_status_hidden",
            "scan_id_hidden",
        ],
        "minimum_capacity_targets": {
            "candidate_rows": 1000,
            "candidate_strata_with_mixed_proxy": 40,
            "post_label_accept_reject_minimum": "60/60",
            "post_label_strict_clear_slice_required": True,
        },
        "blocked_until_after_capacity_scan": [
            "label_fill",
            "label_ingestion",
            "target_independence_audit",
            "posterior_smoke",
            "multi_view_as_model_input",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    relation = summary["audit_snapshot"]["relation_binary"]
    geometry = summary["audit_snapshot"]["geometry_support_binary"]
    lines = [
        "# H002 V20 Attachment Audit Packet Path Decision",
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
        "## Audit Snapshot",
        "",
        "```text",
        f"relation_binary_rows = {relation['rows']}",
        f"relation_binary_counts = {relation['class_counts']}",
        f"relation_class_mass_pass = {relation['class_mass_pass']}",
        f"relation_strict_clear_slices = {relation['strict_clear_slice_count']}",
        f"relation_diagnostic_clear_slices = {relation['diagnostic_clear_slice_count']}",
        f"geometry_support_rows = {geometry['rows']}",
        f"geometry_support_counts = {geometry['class_counts']}",
        f"full_quick_probe_risk_flags = {summary['audit_snapshot']['counts']['full_quick_probe_risk_flags']}",
        f"slice_blocking_risk_flags = {summary['audit_snapshot']['counts']['slice_blocking_risk_flags']}",
        "```",
        "",
        "## Decision",
        "",
        "v20 endpoint-balanced audit packet은 posterior target으로 승격하지 않는다.",
        "",
        "대신 v20은 diagnostic negative target-construction evidence로 고정하고, 다음 route는 "
        "`v21_attachment_deferred_conditional_contrast_capacity_scan`으로 선택한다.",
        "",
        "## Why",
        "",
        "v20의 320-row packet이 우연히 reject-heavy였을 가능성은 남아 있다. 따라서 현재 결과로 "
        "`attachment_deferred` 전체나 H002 factorization을 기각하지 않는다. 다만 현재 target은 "
        "positive `25`개, strict/diagnostic clear slice `0/0`이라 posterior smoke로 넘길 수 없다.",
        "",
        "다음 단계는 더 많은 label을 바로 채우는 것이 아니라 full train pool에서 조건부 contrast "
        "capacity를 먼저 확인하는 것이다. 목표는 같은 predicate, 비슷한 geometry/rank/evidence "
        "조건 안에서도 accept/reject 또는 abstain 후보가 실제로 충분히 존재하는지 보는 것이다.",
        "",
        "## Rejected Options",
        "",
    ]
    for option in summary["option_matrix"]:
        if option["verdict"] != "select":
            lines.append(f"- `{option['option']}`: {option['verdict']} - {option['reason']}")
    lines.extend(
        [
            "",
            "## Selected Next Contract",
            "",
            "```text",
            f"name = {summary['next_contract']['name']}",
            f"split = {summary['next_contract']['split']}",
            f"primary_relation_scope = {summary['next_contract']['primary_relation_scope']}",
            f"diagnostic_relation_scope = {summary['next_contract']['diagnostic_relation_scope']}",
            "posterior_smoke_allowed = false",
            "validation_or_test_allowed = false",
            "```",
            "",
            "Required contrast questions:",
            "",
        ]
    )
    for question in summary["next_contract"]["contrast_questions"]:
        lines.append(f"- {question}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only H002 hypothesis artifact.",
            "- No validation/test rows were used.",
            "- No posterior was trained or evaluated.",
            "- Multi-view and mesh remain audit/confirmation evidence only.",
            "- H001 and paper artifacts were not modified.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    audit = read_json(audit_dir / "summary.json")
    validation_errors = validate_audit(audit)

    output_paths = {
        "summary": output_dir / "summary.json",
        "path_decision": output_dir / "path_decision.json",
        "report": output_dir / "report.md",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    path_decision = {
        "selected_path": SELECTED_PATH,
        "selected_next_todo": NEXT_TODO,
        "freeze_current_target_as": "diagnostic_negative_target_construction_evidence",
        "reason": (
            "The current 320-row v20 target is positive-sparse and shortcut-risky, but this may be "
            "a sampling/target-construction artifact. Scan full-train conditional contrast capacity next."
        ),
        "option_matrix": build_option_matrix(audit),
        "next_contract": build_next_contract(),
    }

    summary = {
        "status": STATUS if not validation_errors else "validation_failed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "input_artifacts": {
            "audit_summary": rel_path(audit_dir / "summary.json"),
            "audit_report": rel_path(audit_dir / "report.md"),
        },
        "output_artifacts": {key: rel_path(path) for key, path in output_paths.items()},
        "audit_snapshot": {
            "relation_binary": audit["target_decisions"]["relation_binary"],
            "relation_multiclass": audit["target_decisions"]["relation_multiclass"],
            "geometry_support_binary": audit["target_decisions"]["geometry_support_binary"],
            "coverage_binary": audit["target_decisions"]["coverage_binary"],
            "endpoint_identity_binary": audit["target_decisions"]["endpoint_identity_binary"],
            "uncertainty_multiclass": audit["target_decisions"]["uncertainty_multiclass"],
            "connected_diagnostic": audit["target_decisions"]["connected_diagnostic"],
            "counts": audit["counts"],
        },
        "top_shortcut_risks": load_top_risks(audit_dir),
        "option_matrix": path_decision["option_matrix"],
        "next_contract": path_decision["next_contract"],
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "fills_new_labels": False,
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
    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next={summary['next_todo']}")
    relation = summary["audit_snapshot"]["relation_binary"]
    print(f"relation_binary_rows={relation['rows']}")
    print(f"relation_binary_counts={relation['class_counts']}")
    print(f"posterior_smoke_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
