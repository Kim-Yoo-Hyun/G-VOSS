#!/usr/bin/env python3
"""Decide the H002 path after the v19 attachment audit-packet target audit."""

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
    "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_"
    "target_independence_audit"
)
DEFAULT_OUTPUT_DIR = RGA_ROOT / (
    "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_"
    "path_decision_after_audit"
)

EXPECTED_AUDIT_STATUS = (
    "h002_reliability_target_v19_attachment_deferred_audit_packet_"
    "target_independence_audit_blocked_positive_sparse_and_shortcut_risk"
)
EXPECTED_NEXT_TODO = (
    "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_"
    "path_decision_after_audit"
)

STATUS = (
    "h002_reliability_target_v19_attachment_deferred_audit_packet_path_decision_"
    "select_v20_endpoint_balanced_counterfactual_repair_plan"
)
SELECTED_PATH = (
    "freeze_v19_audit_packet_diagnostic_select_v20_endpoint_balanced_"
    "counterfactual_repair_plan"
)
NEXT_TODO = "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan"


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
    connected = decisions.get("connected_diagnostic", {})
    geometry = decisions.get("geometry_support_binary", {})

    expected_relation_counts = {"0": 99, "1": 26}
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
        errors.append(
            {
                "error_type": "geometry_support_unexpectedly_posterior_allowed",
                "actual": geometry.get("posterior_allowed"),
            }
        )
    if connected.get("posterior_allowed") is not False:
        errors.append(
            {
                "error_type": "connected_diagnostic_unexpectedly_posterior_allowed",
                "actual": connected.get("posterior_allowed"),
            }
        )

    counts = audit.get("counts", {})
    if counts.get("full_quick_probe_risk_flags", 0) <= 0:
        errors.append(
            {
                "error_type": "expected_full_probe_risk_not_found",
                "actual": counts.get("full_quick_probe_risk_flags"),
            }
        )
    if counts.get("slice_blocking_risk_flags", 0) <= 0:
        errors.append(
            {
                "error_type": "expected_slice_risk_not_found",
                "actual": counts.get("slice_blocking_risk_flags"),
            }
        )

    boundary = audit.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
        "uses_p_geom_valid",
        "uses_source_score_or_rank",
        "uses_geometry_status_or_rank_hint",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "audit_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def load_top_risks(audit_dir: Path) -> list[dict[str, Any]]:
    risk_path = audit_dir / "full_shortcut_risks.json"
    if not risk_path.exists():
        return []
    rows = json.loads(risk_path.read_text(encoding="utf-8"))
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
            "option": "try_stronger_posterior_combiner_now",
            "verdict": "reject",
            "reason": "A stronger combiner would mostly learn endpoint, scan, predicate, and construction artifacts.",
        },
        {
            "option": "use_geometry_support_as_primary",
            "verdict": "reject",
            "reason": (
                f"Geometry support is also class-sparse ({geometry['class_counts']}) and remains an "
                "auxiliary evidence target, not relation reliability."
            ),
        },
        {
            "option": "promote_connected_to_primary",
            "verdict": "reject",
            "reason": (
                f"`connected to` remains diagnostic ({connected['class_counts']}); functional connection is "
                "not decidable from the current label surface."
            ),
        },
        {
            "option": "mine_more_rows_with_same_packet_recipe",
            "verdict": "reject",
            "reason": "More same-style rows would likely preserve endpoint and scan shortcuts instead of fixing target independence.",
        },
        {
            "option": "loosen_label_policy_to_raise_positive_count",
            "verdict": "reject",
            "reason": "This would solve class mass cosmetically while making reliability closer to geometry support.",
        },
        {
            "option": "add_multi_view_or_mesh_as_model_input_now",
            "verdict": "reject_for_now",
            "reason": "Visual/mesh evidence can help audit labels, but using it as input before target repair would mask target-construction failure.",
        },
        {
            "option": "freeze_v19_audit_packet_as_diagnostic",
            "verdict": "select",
            "reason": "v19 is valuable negative evidence showing that independent packet provenance alone does not guarantee a target-independent reliability label.",
        },
        {
            "option": "select_v20_endpoint_balanced_counterfactual_repair_plan",
            "verdict": "select_next",
            "reason": "The next target must directly force class mass and endpoint/object/predicate/scan controls before posterior smoke.",
        },
    ]


def build_selected_plan(audit: dict[str, Any], top_risks: list[dict[str, Any]]) -> dict[str, Any]:
    relation = audit["target_decisions"]["relation_binary"]
    connected = audit["target_decisions"]["connected_diagnostic"]
    geometry = audit["target_decisions"]["geometry_support_binary"]
    counts = audit["counts"]
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "posterior_smoke_allowed": False,
        "candidate_mining_allowed_in_this_stage": False,
        "label_fill_allowed_in_this_stage": False,
        "v19_role": {
            "status": "diagnostic_only_negative_target_construction_evidence",
            "what_it_shows": [
                "reviewer-visible audit packets can remove leakage yet still produce shortcut-heavy targets",
                "independent provenance is not the same as target independence",
                "attachment reliability positives are sparse under the current packet and label criteria",
                "endpoint/object/predicate/scan distributions must be controlled by construction, not only audited after labeling",
            ],
            "not_allowed": [
                "do not run posterior smoke on the v19 target",
                "do not replace relation reliability with geometry-support labels",
                "do not promote connected to into a primary target",
                "do not use v19 as paper metric evidence",
            ],
        },
        "audit_snapshot": {
            "relation_binary_rows": relation["rows"],
            "relation_binary_class_counts": relation["class_counts"],
            "relation_min_class_count": relation["min_class_count"],
            "relation_class_mass_pass": relation["class_mass_pass"],
            "relation_strict_clear_slice_count": relation["strict_clear_slice_count"],
            "relation_diagnostic_clear_slice_count": relation["diagnostic_clear_slice_count"],
            "geometry_support_rows": geometry["rows"],
            "geometry_support_class_counts": geometry["class_counts"],
            "geometry_support_min_class_count": geometry["min_class_count"],
            "connected_diagnostic_rows": connected["rows"],
            "connected_diagnostic_class_counts": connected["class_counts"],
            "full_quick_probe_risk_flags": counts["full_quick_probe_risk_flags"],
            "slice_blocking_risk_flags": counts["slice_blocking_risk_flags"],
            "slice_audit_rows": counts["slice_audit_rows"],
            "slice_risk_rows": counts["slice_risk_rows"],
        },
        "top_shortcut_risks": top_risks,
        "failure_cause": [
            "class-mass gate fails because reliable attachment positives are only 26",
            "strict and diagnostic controlled slice counts are both 0",
            "balanced slices are still explainable by predicate, subject/object labels, endpoint pair, scan, and subgraph metadata",
            "geometry-support labels do not solve the problem because they are evidence-axis labels, not reliability labels",
            "current packet sampling did not force accept/reject contrast within comparable endpoint/object/predicate strata",
        ],
        "next_route": {
            "name": "v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan",
            "goal": (
                "Build a target-repair plan that creates enough positive and negative attachment-reliability "
                "examples while preventing endpoint/object/predicate/scan shortcuts from explaining labels."
            ),
            "requirements": [
                "use train-only rows only",
                "keep posterior smoke blocked until a new target-independence audit passes",
                "mine from the full train attachment candidate pool, not only the current 240-row packet",
                "require post-label class mass of at least 60 accept and 60 reject rows before posterior smoke",
                "prefer exact endpoint-pair mixed accept/reject contrast where feasible",
                "if exact endpoint-pair contrast is infeasible, use subject/object-family, predicate, evidence-tier, and scan-balanced counterfactual strata",
                "cap repeated scans, subgraphs, subject/object labels, and visible endpoint pairs",
                "force `attached to` and `hanging on` to each contain both accept and reject cases after label fill",
                "keep `connected to` diagnostic-only unless a separate visual/mesh-functional criterion is defined",
                "use multi-view or mesh only for label/audit confirmation, not as deployable model input",
                "do not expose geometry status, rank band, machine hint, source score, p_geom_valid, cell id, or queue id as model inputs",
                "write the label protocol before label fill so positive count is not raised by loosening criteria after seeing labels",
            ],
            "repair_designs": [
                {
                    "name": "endpoint_pair_mixed_contrast",
                    "priority": 1,
                    "description": "Search for visible endpoint pairs or near-identical endpoint families that contain both plausible and implausible attachment edges.",
                },
                {
                    "name": "counterfactual_endpoint_controls",
                    "priority": 2,
                    "description": "For each positive anchor, add wrong-endpoint or confound negatives matched by predicate, scan family, object family, and evidence tier.",
                },
                {
                    "name": "scan_and_object_family_caps",
                    "priority": 3,
                    "description": "Prevent wall/floor/ceiling/object-frequency shortcuts by balancing object families and limiting repeated scans/subgraphs.",
                },
                {
                    "name": "visual_mesh_audit_confirmation_only",
                    "priority": 4,
                    "description": "Use packet-local visual/mesh evidence to decide labels, but keep those fields out of deployable factorized-posterior inputs.",
                },
            ],
        },
        "multi_view_policy": {
            "audit_or_confirmation_evidence_now": True,
            "deployable_model_input_now": False,
            "promotion_rule": "V_mv_e can be promoted only after a target-independent reliability label surface exists.",
        },
        "claim_boundary": {
            "h002_core_claim": "semantic score != geometry validity != relation reliability",
            "rga_framework": "still bidirectional semantic-geometry mismatch",
            "attachment_branch": "diagnostic target-construction evidence until v20 repair succeeds",
            "no_paper_metric_evidence": True,
            "no_validation_or_test_usage": True,
            "no_h001_artifact_modification": True,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["selected_plan"]
    snap = plan["audit_snapshot"]
    lines = [
        "# H002 V19 Attachment Audit-Packet Path Decision",
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
        "v19 audit packet target은 diagnostic-only negative target-construction evidence로 고정한다.",
        "",
        "다음 route는 `v20_attachment_deferred_endpoint_balanced_counterfactual_repair_plan`이다.",
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
        f"geometry_support_rows = {snap['geometry_support_rows']}",
        f"geometry_support_class_counts = {snap['geometry_support_class_counts']}",
        f"connected_diagnostic_rows = {snap['connected_diagnostic_rows']}",
        f"connected_diagnostic_class_counts = {snap['connected_diagnostic_class_counts']}",
        f"full_quick_probe_risk_flags = {snap['full_quick_probe_risk_flags']}",
        f"slice_blocking_risk_flags = {snap['slice_blocking_risk_flags']}",
        "```",
        "",
        "## Why",
        "",
        "현재 blocker는 posterior 결합 방식이 약하다는 문제가 아니다. Label target이 아직",
        "positive-sparse이고, endpoint/object/predicate/scan 같은 쉬운 shortcut으로 설명된다.",
        "따라서 더 강한 posterior combiner를 넣으면 factorized reliability를 검증하는 것이 아니라",
        "target construction artifact를 학습할 위험이 크다.",
        "",
        "## Rejected Options",
        "",
    ]
    for option in summary["option_matrix"]:
        if option["verdict"].startswith("reject"):
            lines.append(f"- `{option['option']}`: {option['verdict']} - {option['reason']}")
    lines.extend(
        [
            "",
            "## Selected Next Route Requirements",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in plan["next_route"]["requirements"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only decision.",
            "- No validation/test rows.",
            "- No posterior trained.",
            "- Multi-view and mesh remain audit/confirmation evidence only.",
            "- Hidden fields and construction keys remain audit/control metadata only.",
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
    top_risks = load_top_risks(audit_dir)
    options = build_option_matrix(audit)
    plan = build_selected_plan(audit, top_risks)

    if validation_errors:
        status = "h002_reliability_target_v19_attachment_deferred_audit_packet_path_decision_after_audit_errors"
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
        "schema_version": (
            "h002_reliability_target_v19_attachment_deferred_independent_evidence_"
            "audit_packet_path_decision_after_audit_v1"
        ),
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "audit_summary": rel_path(audit_dir / "summary.json"),
            "audit_report": rel_path(audit_dir / "report.md"),
            "full_shortcut_risks": rel_path(audit_dir / "full_shortcut_risks.json"),
            "slice_risks": rel_path(audit_dir / "slice_risks.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "selected_path": selected_path,
        "selected_plan": plan,
        "option_matrix": options,
        "option_verdicts": {item["option"]: item["verdict"] for item in options},
        "audit_snapshot": plan["audit_snapshot"],
        "top_shortcut_risks": top_risks,
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
            "mesh_as_model_input": False,
            "multi_view_or_mesh_as_audit_or_confirmation_evidence_only": True,
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
