#!/usr/bin/env python3
"""Synthesize H002 scope after freezing support/contact independent validity."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_IV_REVIEW_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review"
)
DEFAULT_POSE_REVIEW_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review"
)
DEFAULT_CALIBRATION_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_calibration_scope_plan"
)
DEFAULT_SUPPORT_FREEZE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_after_capacity_scan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze"
)

EXPECTED_IV_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review_accept_Ce_select_calibration_scope_plan"
)
EXPECTED_POSE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_result_review_accept_scoped_Ce_select_multi_family_synthesis"
)
EXPECTED_CALIBRATION_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_calibration_scope_plan_select_support_contact_balancing"
)
EXPECTED_FREEZE_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_class_pair_repair_path_decision_freeze_independent_validity_diagnostic"
)
EXPECTED_FREEZE_NEXT = "compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_independent_validity_freeze_v1"
STATUS_READY = "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_freeze_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_freeze_input_errors"
SELECTED_PATH = "freeze_current_scope_select_independent_target_source_decision"
NEXT_TODO = "compatibility_dataset_v3_independent_target_source_decision_after_scope_synthesis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iv-review-dir", type=Path, default=DEFAULT_IV_REVIEW_DIR)
    parser.add_argument("--pose-review-dir", type=Path, default=DEFAULT_POSE_REVIEW_DIR)
    parser.add_argument("--calibration-dir", type=Path, default=DEFAULT_CALIBRATION_DIR)
    parser.add_argument("--support-freeze-dir", type=Path, default=DEFAULT_SUPPORT_FREEZE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_required(path: Path, errors: list[dict[str, Any]], label: str) -> dict[str, Any]:
    if not path.exists():
        errors.append({"input": label, "error_type": "missing_summary", "path": rel_path(path)})
        return {}
    return read_json(path)


def validate_inputs(
    iv_review: dict[str, Any],
    pose_review: dict[str, Any],
    calibration: dict[str, Any],
    freeze: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    checks = [
        ("iv_review", iv_review, EXPECTED_IV_STATUS),
        ("pose_review", pose_review, EXPECTED_POSE_STATUS),
        ("calibration", calibration, EXPECTED_CALIBRATION_STATUS),
        ("support_freeze", freeze, EXPECTED_FREEZE_STATUS),
    ]
    for label, payload, expected_status in checks:
        if payload.get("status") != expected_status:
            errors.append({"input": label, "error_type": "unexpected_status", "actual": payload.get("status")})
        if payload.get("validation_errors") != 0:
            errors.append({"input": label, "error_type": "validation_errors_present", "actual": payload.get("validation_errors")})
        boundary = payload.get("boundary", {})
        for key in ["validation_usage", "test_usage", "h001_artifacts_modified"]:
            if boundary.get(key) is not False:
                errors.append(
                    {"input": label, "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)}
                )
    if freeze.get("next_todo") != EXPECTED_FREEZE_NEXT:
        errors.append({"input": "support_freeze", "error_type": "unexpected_next", "actual": freeze.get("next_todo")})

    iv_claim = iv_review.get("claim_boundary", {})
    if iv_claim.get("allowed_scope", {}).get("primary_family") != "relative_vertical":
        errors.append(
            {
                "input": "iv_review",
                "error_type": "unexpected_primary_family",
                "actual": iv_claim.get("allowed_scope", {}).get("primary_family"),
            }
        )
    if freeze.get("selected_path") != "freeze_support_contact_independent_validity_as_diagnostic_select_scope_synthesis":
        errors.append({"input": "support_freeze", "error_type": "unexpected_selected_path", "actual": freeze.get("selected_path")})
    return errors


def family_scope_rows(iv_review: dict[str, Any], pose_review: dict[str, Any], freeze: dict[str, Any]) -> list[dict[str, Any]]:
    iv_mech = iv_review.get("mechanism_result", {})
    family_slice = iv_mech.get("family_slice", {})
    pose_mech = pose_review.get("mechanism_result", {})
    cap = freeze.get("capacity_snapshot", {})
    return [
        {
            "family": "relative_vertical",
            "predicates": "higher than; lower than",
            "current_role": "main_train_only_Ce_evidence",
            "target_type": "GT-anchored exact-stratum repaired independent-validity target",
            "rows": family_slice.get("relative_vertical", {}).get("rows"),
            "primary_auroc": family_slice.get("relative_vertical", {}).get("primary_auroc"),
            "geometry_only_auroc": family_slice.get("relative_vertical", {}).get("geometry_only_auroc"),
            "claim_allowed": "C_e discrimination/ranking mechanism on train-only target",
            "claim_blocked": "paper-level held-out reliability or p_rel/p_obs posterior",
            "next_requirement": "external/held-out or independent target-source decision before promotion",
        },
        {
            "family": "support_contact_pose_conditioned",
            "predicates": "lying on; standing on",
            "current_role": "scoped_constructed_Ce_mechanism_evidence",
            "target_type": "controlled pose-conditioned same-G_e predicate contrast",
            "rows": pose_mech.get("counts", {}).get("rows"),
            "primary_auroc": pose_mech.get("primary_auroc"),
            "geometry_only_auroc": pose_mech.get("geometry_only_auroc"),
            "claim_allowed": "support/contact-specific C_e mechanism proof",
            "claim_blocked": "independent relation-validity reliability",
            "next_requirement": "human/visual/mesh or alternative GT source if support/contact must be main",
        },
        {
            "family": "support_contact_independent_validity",
            "predicates": "lying on; standing on",
            "current_role": "diagnostic_only_frozen",
            "target_type": "Open3DSG train-side GT/source independent-validity construction",
            "rows": cap.get("primary_candidate_rows"),
            "primary_auroc": "",
            "geometry_only_auroc": "",
            "claim_allowed": "negative target-construction evidence",
            "claim_blocked": "main support/contact learned smoke",
            "next_requirement": (
                f"strict predicate-class capacity is {cap.get('predicate_x_class_pair_scan_capped_capacity')} "
                f"rows; need new target source for main support/contact reliability"
            ),
        },
        {
            "family": "attachment_like",
            "predicates": "attached to; hanging on; connected to",
            "current_role": "deferred",
            "target_type": "requires visual/mesh evidence and stronger observability labels",
            "rows": "",
            "primary_auroc": "",
            "geometry_only_auroc": "",
            "claim_allowed": "none in current main H002 scope",
            "claim_blocked": "target independence and observability unresolved",
            "next_requirement": "audit-first visual/mesh target if reactivated",
        },
        {
            "family": "proximity",
            "predicates": "close by",
            "current_role": "deferred",
            "target_type": "distance-dominant relation family",
            "rows": "",
            "primary_auroc": "",
            "geometry_only_auroc": "",
            "claim_allowed": "none in current main H002 scope",
            "claim_blocked": "risks collapsing to distance verifier",
            "next_requirement": "only revisit after independent reliability target is stable",
        },
    ]


def claim_boundary(iv_review: dict[str, Any], calibration: dict[str, Any], freeze: dict[str, Any]) -> dict[str, Any]:
    iv_mech = iv_review.get("mechanism_result", {})
    calibration_audit = calibration.get("calibration_metric_audit", {})
    primary_cal = calibration_audit.get("primary_model", {})
    cap = freeze.get("capacity_snapshot", {})
    return {
        "allowed_now": (
            "H002 currently supports a train-only predicate-conditioned compatibility mechanism: "
            "semantic/source evidence and predicate-independent geometry are insufficient by themselves, "
            "while C_e = compatibility(T_e, G_e) separates valid and invalid relation candidates on the "
            "exact-stratum repaired target."
        ),
        "primary_evidence": {
            "family_scope": "relative_vertical_dominant",
            "model": iv_mech.get("primary_model"),
            "primary_auroc": iv_mech.get("primary_auroc"),
            "geometry_only_auroc": iv_mech.get("geometry_only_auroc"),
            "source_only_auroc": iv_mech.get("source_only_auroc"),
            "wrong_predicate_auroc": iv_mech.get("wrong_predicate_auroc"),
        },
        "support_contact_boundary": {
            "independent_validity_status": "diagnostic_only_frozen",
            "strict_predicate_class_capacity": cap.get("predicate_x_class_pair_scan_capped_capacity"),
            "lying_on_capacity": cap.get("lying_on_strict_scan_capped_capacity"),
            "standing_on_capacity": cap.get("standing_on_strict_scan_capped_capacity"),
            "pose_conditioned_status": "scoped_Ce_mechanism_evidence_only",
        },
        "calibration_boundary": {
            "proper_probability_ece": primary_cal.get("probability_ece_10"),
            "brier": primary_cal.get("brier"),
            "legacy_ece_downgraded": True,
            "calibrated_p_rel_p_obs_claim_allowed": False,
            "reason": "probability quality is train-only C_e score calibration, not held-out relation reliability posterior",
        },
        "blocked_claims": [
            "paper-level result",
            "held-out validation/test performance",
            "all-family 3DSSG reliability",
            "support/contact independent-validity main result",
            "calibrated p_rel / p_obs reliability posterior",
            "attachment/proximity/horizontal generality",
        ],
    }


def route_rows() -> list[dict[str, Any]]:
    return [
        {
            "route": "promote_current_H002_to_paper_evidence",
            "verdict": "reject_now",
            "reason": "All evidence is train-only hypothesis-stage; support/contact independent-validity is diagnostic-only.",
            "next_action": "do not create Docker paper experiment root yet",
        },
        {
            "route": "run_more_support_contact_repair_on_same_source",
            "verdict": "reject",
            "reason": "Full-train strict predicate-class capacity is only 88 rows; more sampling cannot fix this source construction.",
            "next_action": "require a different target source if support/contact must be main",
        },
        {
            "route": "use_relative_vertical_Ce_as_current_main_H002_evidence",
            "verdict": "selected",
            "reason": "It is the cleanest train-only independent-validity C_e evidence after shortcut repair.",
            "next_action": "keep claim scoped to C_e discrimination/ranking",
        },
        {
            "route": "retain_support_contact_pose_conditioned_mechanism",
            "verdict": "selected_diagnostic_mechanism",
            "reason": "It supports predicate-conditioned geometry interpretation, but not independent relation reliability.",
            "next_action": "use only as mechanism evidence",
        },
        {
            "route": "decide_next_independent_target_source",
            "verdict": "selected_next",
            "reason": "The next bottleneck is not architecture; it is target source and external validity.",
            "next_action": NEXT_TODO,
        },
    ]


def reviewer_risk_rows() -> list[dict[str, Any]]:
    return [
        {
            "risk": "single_main_family",
            "severity": "high",
            "current_answer": "Main independent-validity evidence is relative-vertical dominant.",
            "required_next": "Decide whether to seek a new target source or keep H002 as scoped mechanism evidence.",
        },
        {
            "risk": "support_contact_target_shortcut",
            "severity": "high",
            "current_answer": "Support/contact independent-validity is frozen diagnostic-only due predicate-class capacity 88.",
            "required_next": "Use human/visual/mesh audit or another source if support/contact must be main.",
        },
        {
            "risk": "not_final_reliability",
            "severity": "high",
            "current_answer": "Current evidence validates C_e, not deployable p_rel/p_obs.",
            "required_next": "Define independent reliability labels and selective decision protocol.",
        },
        {
            "risk": "calibration_scope",
            "severity": "medium",
            "current_answer": "Corrected train-only probability ECE is low, but posterior reliability is not established.",
            "required_next": "Use held-out/Docker calibration only after target source is frozen.",
        },
        {
            "risk": "architecture_overfitting",
            "severity": "medium",
            "current_answer": "Current bottleneck is not combiner capacity.",
            "required_next": "Avoid bigger architecture until target-source bottleneck is resolved.",
        },
    ]


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Choose the next independent target source after H002 scope is frozen.",
        "candidate_routes": [
            "relative_vertical held-out/Docker promotion as a scoped C_e method",
            "human/visual/mesh audited support/contact reliability labels",
            "cross-source agreement target using another relation source",
            "stop H002 as mechanism evidence and return to H001/GeoCalib paper path",
        ],
        "do_not_do_next": [
            "Do not run support/contact learned smoke from the frozen independent-validity target.",
            "Do not treat relaxed class-pair diagnostic as main evidence.",
            "Do not add a larger neural combiner before target-source decision.",
            "Do not use validation/test rows for new hypothesis target construction.",
        ],
        "success_condition": [
            "one selected target-source route",
            "explicit claim boundary",
            "required labels/features",
            "minimum class-mass and shortcut gates",
            "Docker promotion decision if paper-level evidence is pursued",
        ],
    }


def write_report(path: Path, summary: dict[str, Any], families: list[dict[str, Any]], risks: list[dict[str, Any]], routes: list[dict[str, Any]]) -> None:
    claim = summary["claim_boundary"]
    lines = [
        "# H002 Scope Synthesis After Support/Contact Freeze",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Claim Boundary",
        "",
        claim["allowed_now"],
        "",
        "Blocked claims:",
        "",
        *[f"- {item}" for item in claim["blocked_claims"]],
        "",
        "## Family Scope",
        "",
    ]
    for row in families:
        lines.extend(
            [
                f"- `{row['family']}`: {row['current_role']}",
                f"  Predicates: {row['predicates']}",
                f"  Allowed: {row['claim_allowed']}",
                f"  Blocked: {row['claim_blocked']}",
                f"  Next: {row['next_requirement']}",
            ]
        )
    lines.extend(["", "## Reviewer Risks", ""])
    for row in risks:
        lines.append(f"- `{row['risk']}` ({row['severity']}): {row['current_answer']} Next: {row['required_next']}")
    lines.extend(["", "## Routes", ""])
    for row in routes:
        lines.append(f"- `{row['route']}`: {row['verdict']}. {row['reason']} Next: {row['next_action']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only synthesis.",
            "- No validation/test usage.",
            "- No row materialization.",
            "- No learned smoke or model training.",
            "- No calibrated `p_rel` / `p_obs` claim.",
            "- No paper-level evidence.",
            "- No H001 artifact modification.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    load_errors: list[dict[str, Any]] = []
    iv_review = load_required(args.iv_review_dir / "summary.json", load_errors, "iv_review")
    pose_review = load_required(args.pose_review_dir / "summary.json", load_errors, "pose_review")
    calibration = load_required(args.calibration_dir / "summary.json", load_errors, "calibration")
    freeze = load_required(args.support_freeze_dir / "summary.json", load_errors, "support_freeze")
    validation_errors = load_errors + validate_inputs(iv_review, pose_review, calibration, freeze)

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_errors"
        next_todo = EXPECTED_FREEZE_NEXT
        families: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []
        routes: list[dict[str, Any]] = []
        claim = {}
        next_contract = {}
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO
        families = family_scope_rows(iv_review, pose_review, freeze)
        risks = reviewer_risk_rows()
        routes = route_rows()
        claim = claim_boundary(iv_review, calibration, freeze)
        next_contract = next_plan_contract()

    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_scope_synthesis",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "claim_boundary": claim,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_artifacts": {
            "iv_review": rel_path(args.iv_review_dir),
            "pose_review": rel_path(args.pose_review_dir),
            "calibration": rel_path(args.calibration_dir),
            "support_freeze": rel_path(args.support_freeze_dir),
        },
        "next_plan_contract": next_contract,
        "next_todo": next_todo,
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
        "validation_error_path": rel_path(args.output_dir / "validation_errors.jsonl"),
    }
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "claim_boundary.json", claim)
    write_json(args.output_dir / "next_plan_contract.json", next_contract)
    write_csv(args.output_dir / "family_scope.csv", families)
    write_csv(args.output_dir / "reviewer_risks.csv", risks)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_report(args.output_dir / "report.md", summary, families, risks, routes)
    print(
        json.dumps(
            {
                "status": status,
                "selected_path": selected_path,
                "next_todo": next_todo,
                "validation_errors": len(validation_errors),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 1 if status == STATUS_ERROR else 0


if __name__ == "__main__":
    raise SystemExit(main())
