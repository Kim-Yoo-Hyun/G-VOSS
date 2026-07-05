#!/usr/bin/env python3
"""Plan support/contact individual predicate probes after close-by freeze."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_CLOSE_BY_DECISION_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_proximity_close_by_path_decision_after_schema_shortcut_audit"
)
DEFAULT_CAPACITY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relation_family_generalization_capacity_scan"
DEFAULT_FEATURE_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_feature_probe_result_review"
DEFAULT_POSE_RESULT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review"
DEFAULT_VISUAL_REPAIR_DECISION_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_after_label_ingestion"
)
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_probe_plan"

EXPECTED_CLOSE_BY_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_path_decision_freeze_close_by_select_support_contact_individual_probe"
)
EXPECTED_CLOSE_BY_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_probe_plan"
EXPECTED_FEATURE_REVIEW_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_feature_probe_result_review_select_pose_conditioned_target_plan"
)
EXPECTED_POSE_RESULT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_result_review_accept_scoped_Ce_select_multi_family_synthesis"
)
EXPECTED_VISUAL_REPAIR_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_path_decision_freeze_diagnostic"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_individual_predicate_probe_plan_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_probe_plan_ready_for_source_inventory"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_individual_predicate_probe_plan_input_errors"
SELECTED_PATH = "plan_individual_support_contact_source_inventory_standing_primary_lying_secondary_supported_diagnostic"
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_source_inventory"

PREDICATES = ["standing on", "lying on", "supported by"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--close-by-decision-dir", type=Path, default=DEFAULT_CLOSE_BY_DECISION_DIR)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--feature-review-dir", type=Path, default=DEFAULT_FEATURE_REVIEW_DIR)
    parser.add_argument("--pose-result-dir", type=Path, default=DEFAULT_POSE_RESULT_DIR)
    parser.add_argument("--visual-repair-decision-dir", type=Path, default=DEFAULT_VISUAL_REPAIR_DECISION_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def parse_int(value: str | None) -> int:
    if value is None or value == "":
        return 0
    return int(value)


def parse_label_count(counts: str, key: str) -> int:
    if not counts:
        return 0
    for part in counts.split(";"):
        part = part.strip()
        if part.startswith(f"{key}:"):
            return parse_int(part.split(":", 1)[1])
    return 0


def load_inputs(args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, str]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    required_json = {
        "close_by_decision": args.close_by_decision_dir / "summary.json",
        "feature_review": args.feature_review_dir / "summary.json",
        "pose_result": args.pose_result_dir / "summary.json",
        "visual_repair_decision": args.visual_repair_decision_dir / "summary.json",
    }
    loaded: dict[str, dict[str, Any]] = {}
    for label, path in required_json.items():
        if not path.exists():
            errors.append({"error_type": "missing_input_json", "input": label, "path": rel_path(path)})
            loaded[label] = {}
        else:
            loaded[label] = read_json(path)

    capacity_path = args.capacity_dir / "predicate_capacity.csv"
    if not capacity_path.exists():
        errors.append({"error_type": "missing_capacity_csv", "path": rel_path(capacity_path)})
        capacity_rows: list[dict[str, str]] = []
    else:
        capacity_rows = read_csv(capacity_path)
    return (
        loaded["close_by_decision"],
        loaded["feature_review"],
        loaded["pose_result"],
        loaded["visual_repair_decision"],
        capacity_rows,
        errors,
    )


def validate_boundary(summary: dict[str, Any], label: str, errors: list[dict[str, Any]]) -> None:
    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "paper_evidence_allowed",
        "runs_learned_smoke",
        "trains_new_model",
    ]:
        if key in boundary and boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "input": label, "key": key, "actual": boundary.get(key)})


def validate_inputs(
    close_by: dict[str, Any],
    feature_review: dict[str, Any],
    pose_result: dict[str, Any],
    visual_repair: dict[str, Any],
    capacity_rows: list[dict[str, str]],
    load_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors = list(load_errors)
    if errors:
        return errors

    if close_by.get("status") != EXPECTED_CLOSE_BY_STATUS:
        errors.append({"error_type": "unexpected_close_by_status", "actual": close_by.get("status")})
    if close_by.get("next_todo") != EXPECTED_CLOSE_BY_NEXT:
        errors.append({"error_type": "unexpected_close_by_next", "actual": close_by.get("next_todo")})
    if close_by.get("validation_errors") != 0:
        errors.append({"error_type": "close_by_validation_errors", "actual": close_by.get("validation_errors")})
    if close_by.get("selected_path") != "freeze_close_by_diagnostic_select_support_contact_individual_predicate_probe":
        errors.append({"error_type": "unexpected_close_by_selected_path", "actual": close_by.get("selected_path")})

    if feature_review.get("status") != EXPECTED_FEATURE_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_feature_review_status", "actual": feature_review.get("status")})
    if feature_review.get("validation_errors") != 0:
        errors.append({"error_type": "feature_review_validation_errors", "actual": feature_review.get("validation_errors")})
    if feature_review.get("path_decision", {}).get("target_design_plan_allowed") is not True:
        errors.append(
            {
                "error_type": "feature_review_target_design_not_allowed",
                "actual": feature_review.get("path_decision", {}).get("target_design_plan_allowed"),
            }
        )

    if pose_result.get("status") != EXPECTED_POSE_RESULT_STATUS:
        errors.append({"error_type": "unexpected_pose_result_status", "actual": pose_result.get("status")})
    if pose_result.get("validation_errors") != 0:
        errors.append({"error_type": "pose_result_validation_errors", "actual": pose_result.get("validation_errors")})
    mechanism = pose_result.get("mechanism_result", {})
    if mechanism.get("primary_model") != "M5b_compatibility_TG_pose_interaction":
        errors.append({"error_type": "unexpected_pose_primary_model", "actual": mechanism.get("primary_model")})
    if mechanism.get("primary_auroc") != 1.0 or mechanism.get("geometry_only_auroc") != 0.5:
        errors.append(
            {
                "error_type": "pose_mechanism_metrics_unexpected",
                "primary_auroc": mechanism.get("primary_auroc"),
                "geometry_only_auroc": mechanism.get("geometry_only_auroc"),
            }
        )

    if visual_repair.get("status") != EXPECTED_VISUAL_REPAIR_STATUS:
        errors.append({"error_type": "unexpected_visual_repair_status", "actual": visual_repair.get("status")})
    if visual_repair.get("validation_errors") != 0:
        errors.append({"error_type": "visual_repair_validation_errors", "actual": visual_repair.get("validation_errors")})
    if "shortcut_risk_blocks_smoke" not in visual_repair.get("input_snapshot", {}).get("status", ""):
        errors.append(
            {
                "error_type": "visual_repair_input_not_shortcut_blocked",
                "actual": visual_repair.get("input_snapshot", {}).get("status"),
            }
        )

    for label, summary in [
        ("close_by", close_by),
        ("feature_review", feature_review),
        ("pose_result", pose_result),
        ("visual_repair", visual_repair),
    ]:
        validate_boundary(summary, label, errors)

    by_predicate = {row.get("predicate_label"): row for row in capacity_rows}
    for predicate in PREDICATES:
        row = by_predicate.get(predicate)
        if not row:
            errors.append({"error_type": "missing_predicate_capacity", "predicate": predicate})
            continue
        if row.get("family") != "support_contact":
            errors.append({"error_type": "unexpected_predicate_family", "predicate": predicate, "actual": row.get("family")})
        if row.get("verdict") != "capacity_ready_needs_target_plan":
            errors.append({"error_type": "predicate_capacity_not_ready", "predicate": predicate, "actual": row.get("verdict")})
        if parse_int(row.get("queue_rows")) < 50000:
            errors.append({"error_type": "predicate_queue_too_small", "predicate": predicate, "actual": row.get("queue_rows")})
        if parse_int(row.get("mixed_class_pair_groups_exact_vs_other")) < 50:
            errors.append(
                {
                    "error_type": "predicate_mixed_class_pair_groups_too_small",
                    "predicate": predicate,
                    "actual": row.get("mixed_class_pair_groups_exact_vs_other"),
                }
            )
    return errors


def predicate_capacity_table(capacity_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    by_predicate = {row["predicate_label"]: row for row in capacity_rows}
    roles = {
        "standing on": {
            "priority": 1,
            "plan_role": "primary_individual_probe",
            "target_role": "primary C_e / p_rel candidate if source inventory passes",
            "why": "largest exact-match count and sufficient mixed class-pair capacity; tests upright support-contact geometry evidence",
        },
        "lying on": {
            "priority": 2,
            "plan_role": "secondary_pose_conditioned_probe",
            "target_role": "secondary C_e candidate and paired contrast with standing on",
            "why": "pose-conditioned mechanism already passed; lower exact count than standing on but still materializable",
        },
        "supported by": {
            "priority": 3,
            "plan_role": "diagnostic_superordinate_probe",
            "target_role": "Q_e / taxonomy / superordinate-support diagnostic, not clean binary negative",
            "why": "superordinate relation overlaps standing/lying support states; useful for claim boundary and failure taxonomy",
        },
    }
    out: list[dict[str, Any]] = []
    for predicate in PREDICATES:
        row = by_predicate[predicate]
        role = roles[predicate]
        out.append(
            {
                "predicate_label": predicate,
                "family": row.get("family", ""),
                "priority": role["priority"],
                "plan_role": role["plan_role"],
                "target_role": role["target_role"],
                "open3dsg_train_full_gt_count": parse_int(row.get("open3dsg_train_full_gt_count")),
                "queue_rows": parse_int(row.get("queue_rows")),
                "hl_rows": parse_int(row.get("hl_rows")),
                "lh_rows": parse_int(row.get("lh_rows")),
                "exact_matches": parse_label_count(row.get("label_match_status_counts", ""), "exact_match"),
                "family_matches": parse_label_count(row.get("label_match_status_counts", ""), "family_match"),
                "no_gt_for_pair": parse_label_count(row.get("label_match_status_counts", ""), "no_gt_for_pair"),
                "pair_has_other_predicate": parse_label_count(row.get("label_match_status_counts", ""), "pair_has_other_predicate"),
                "mixed_class_pair_groups_exact_vs_other": parse_int(row.get("mixed_class_pair_groups_exact_vs_other")),
                "balanced_rows_exact_vs_other": parse_int(row.get("balanced_rows_exact_vs_other")),
                "reason": role["why"],
            }
        )
    return out


def evidence_policy() -> list[dict[str, Any]]:
    return [
        {
            "predicate_label": "standing on",
            "primary_positive_evidence": "upright subject pose + bottom-to-top support gap/contact + XY support overlap",
            "candidate_positive_sources": "exact_match rows plus visually/mesh-confirmed upright support rows",
            "candidate_reject_sources": "same predicate/class-pair/rank candidates with absent contact, lying-like pose, or visual/mesh reject",
            "abstain_policy": "weak mesh/point coverage, ambiguous orientation, or partial occlusion",
            "blocked_shortcuts": "hard_surface_pair, subject/object class pair, source rank band, queue kind, raw geometry status",
            "model_input_allowed": "T_e without Z_e for C_e, G_e contact/pose tokens, Q_e evidence availability",
        },
        {
            "predicate_label": "lying on",
            "primary_positive_evidence": "lying-like low/flat subject pose + support/contact evidence",
            "candidate_positive_sources": "exact_match rows plus pose-conditioned lying-like anchors",
            "candidate_reject_sources": "same class/rank/contact candidates with upright pose or no lying evidence",
            "abstain_policy": "flatness/pose ambiguous, low point count, or contact evidence missing",
            "blocked_shortcuts": "hard_surface_pair, queue kind, source rank band, endpoint pair, object class only",
            "model_input_allowed": "same G_e anchor may pair with lying/standing T_e for controlled C_e",
        },
        {
            "predicate_label": "supported by",
            "primary_positive_evidence": "generic support/contact relation evidence independent of standing/lying pose",
            "candidate_positive_sources": "exact_match/family_match rows plus support-confirmed audit rows",
            "candidate_reject_sources": "no support/contact evidence, not merely standing/lying alternative labels",
            "abstain_policy": "support plausible but relation specificity unclear",
            "blocked_shortcuts": "do not use as negative for standing on; do not collapse into hard_surface shortcut",
            "model_input_allowed": "diagnostic Q_e/C_e only unless source inventory finds clean positive/reject cells",
        },
    ]


def route_decision() -> list[dict[str, Any]]:
    return [
        {
            "route": "reuse_grouped_support_contact_visual_mesh_target",
            "verdict": "reject",
            "reason": "grouped class-pair repair remained shortcut-prone and p_rel was solved by predicate/class-pair/source strata",
            "next_condition": "none for current artifact; keep as diagnostic negative evidence",
        },
        {
            "route": "reuse_pose_conditioned_lying_standing_as_main_result",
            "verdict": "defer_as_scoped_mechanism",
            "reason": "pose-conditioned C_e passed controls but uses constructed labels, so it is not independent p_rel/p_obs reliability",
            "next_condition": "use as mechanism prior while building individual predicate source inventory",
        },
        {
            "route": "standing_on_individual_probe",
            "verdict": "select_primary",
            "reason": "largest exact-match pool and sufficient class-pair mixing; tests contact/support evidence beyond pure distance",
            "next_condition": "source inventory must find accept/reject or auditable cells after class-pair/rank/hard-surface controls",
        },
        {
            "route": "lying_on_individual_probe",
            "verdict": "select_secondary",
            "reason": "paired pose-conditioned mechanism is strong and can test same-G predicate compatibility against standing on",
            "next_condition": "source inventory must preserve pose-conditioned controls and avoid construction-label leakage",
        },
        {
            "route": "supported_by_individual_probe",
            "verdict": "select_diagnostic",
            "reason": "superordinate overlap makes it valuable for taxonomy and Q_e but risky as a clean binary target",
            "next_condition": "source inventory must treat it as diagnostic unless clean support/non-support cells appear",
        },
    ]


def shortcut_gates() -> list[dict[str, Any]]:
    return [
        {
            "gate": "predicate_specific_balance",
            "applies_to": "standing on; lying on",
            "required_before_materialization": "each selected primary predicate must have positive/reject or auditable candidate cells",
            "fail_action": "keep predicate diagnostic only",
        },
        {
            "gate": "class_pair_control",
            "applies_to": "all",
            "required_before_materialization": "subject/object class pair cannot be pure accept or pure reject in the selected target cells",
            "fail_action": "repair mining or diagnostic freeze",
        },
        {
            "gate": "rank_source_control",
            "applies_to": "all",
            "required_before_materialization": "source rank/source score bands must be balanced or hidden and audited",
            "fail_action": "block learned smoke",
        },
        {
            "gate": "hard_surface_control",
            "applies_to": "standing on; supported by",
            "required_before_materialization": "floor/table/wall-like endpoint strata must be capped and reported",
            "fail_action": "block learned smoke or use masked diagnostic",
        },
        {
            "gate": "same_geometry_anchor_control",
            "applies_to": "lying on; standing on",
            "required_before_materialization": "paired rows should share G_e where possible so C_e depends on T_e-G_e compatibility",
            "fail_action": "do not claim compatibility mechanism",
        },
        {
            "gate": "supported_by_superordinate_boundary",
            "applies_to": "supported by",
            "required_before_materialization": "supported by cannot be used as a negative for standing on without visual/mesh reject evidence",
            "fail_action": "diagnostic-only supported by",
        },
        {
            "gate": "no_gt_policy",
            "applies_to": "all",
            "required_before_materialization": "no-GT rows are candidates for audit, not automatic reject labels",
            "fail_action": "block target",
        },
    ]


def rejected_reuse_table() -> list[dict[str, Any]]:
    return [
        {
            "artifact_or_route": "support_contact_visual_mesh_audit_class_pair_repair",
            "reuse_decision": "diagnostic_only",
            "reason": "target had enough rows but shortcut risk remained high through predicate/class-pair and generic endpoint fields",
        },
        {
            "artifact_or_route": "support_contact_pose_conditioned_same_G",
            "reuse_decision": "mechanism_prior_only",
            "reason": "excellent C_e control result but constructed target, not independent relation reliability",
        },
        {
            "artifact_or_route": "grouped_support_contact_label",
            "reuse_decision": "do_not_reuse_as_main",
            "reason": "grouping standing/lying/supported by hides predicate-specific geometry semantics",
        },
        {
            "artifact_or_route": "supported_by_as_standing_negative",
            "reuse_decision": "reject",
            "reason": "supported by is superordinate and can be true together with standing on",
        },
    ]


def reviewer_risk_table() -> list[dict[str, Any]]:
    return [
        {
            "risk": "support_contact_already_failed",
            "severity": "medium",
            "response": "The grouped target failed; this plan deliberately moves to predicate-specific probes and keeps grouped artifacts diagnostic.",
        },
        {
            "risk": "standing_on_class_pair_shortcut",
            "severity": "high",
            "response": "Require class-pair, hard-surface, rank, and source controls before materialization.",
        },
        {
            "risk": "lying_standing_constructed_label",
            "severity": "medium",
            "response": "Use previous pose-conditioned result as C_e mechanism evidence only, then source inventory must seek harder audit/GT cells.",
        },
        {
            "risk": "supported_by_overlap",
            "severity": "high",
            "response": "Treat supported by as diagnostic/superordinate unless clean support vs non-support cells exist.",
        },
        {
            "risk": "model_architecture_before_target",
            "severity": "high",
            "response": "No learned smoke until source inventory and shortcut gates pass.",
        },
    ]


def target_contrast_contract() -> dict[str, Any]:
    return {
        "contract_name": "h002_support_contact_individual_predicate_probe_contract_v1",
        "purpose": "Test whether support/contact geometry evidence can support predicate-specific C_e and eventual p_rel without grouped-target shortcut.",
        "selected_primary": "standing on",
        "selected_secondary": "lying on",
        "selected_diagnostic": "supported by",
        "factor_boundary": {
            "T_e": "predicate text/label, relation family, subject/object class content; no source score/rank",
            "Z_e": "source confidence/rank/source id; baseline and final reliability only, excluded from C_e",
            "G_e": "predicate-independent contact/support/pose/mesh geometry evidence",
            "C_e": "compatibility between T_e and G_e",
            "Q_e": "observability/evidence quality and abstain gate",
            "p_obs": "judgment possibility, not relation truth",
            "p_rel": "relation reliability when p_obs is high",
        },
        "primary_success_condition_for_next_inventory": [
            "candidate cells exist for standing on and lying on after class-pair/rank/hard-surface controls",
            "supported by can be separated into support-confirmed / no-support / ambiguous diagnostic cells",
            "no-GT rows are not used as automatic negatives",
            "source score/rank and predicate/class-pair cannot solve the target alone",
        ],
        "learning_blocked_until": [
            "source inventory validates row capacity",
            "candidate materialization writes model-safe and hidden views",
            "schema/shortcut audit passes",
        ],
    }


def write_report(
    path: Path,
    summary: dict[str, Any],
    predicate_plan: list[dict[str, Any]],
    routes: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 Support/Contact Individual Predicate Probe Plan",
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
        "## Decision",
        "",
        "Proceed to a source inventory for individual support/contact predicates.",
        "",
        "Do not reuse the grouped support/contact target as a main learned target. `standing on` is the primary probe, `lying on` is the secondary pose-conditioned probe, and `supported by` is diagnostic/superordinate.",
        "",
        "## Predicate Plan",
        "",
        "| Priority | Predicate | Role | Queue Rows | Exact Matches | Mixed Class-Pair Groups | Boundary |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in predicate_plan:
        lines.append(
            "| "
            f"{row['priority']} | `{row['predicate_label']}` | {row['plan_role']} | {row['queue_rows']} | "
            f"{row['exact_matches']} | {row['mixed_class_pair_groups_exact_vs_other']} | {row['target_role']} |"
        )
    lines.extend(
        [
            "",
            "## Route Decisions",
            "",
            "| Route | Verdict | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for row in routes:
        lines.append(f"| `{row['route']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Required Before Learned Smoke",
            "",
            "- Source inventory must confirm controlled candidate cells.",
            "- Candidate materialization must keep construction fields hidden.",
            "- Schema and shortcut audit must pass before any learned smoke.",
            "- `supported by` must not be used as a negative for `standing on` without explicit reject evidence.",
            "- No validation/test rows are used in this hypothesis-stage plan.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    close_by, feature_review, pose_result, visual_repair, capacity_rows, load_errors = load_inputs(args)
    validation_errors = validate_inputs(
        close_by,
        feature_review,
        pose_result,
        visual_repair,
        capacity_rows,
        load_errors,
    )

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_errors"
        next_todo = EXPECTED_CLOSE_BY_NEXT
        predicate_plan: list[dict[str, Any]] = []
        policies: list[dict[str, Any]] = []
        routes: list[dict[str, Any]] = []
        gates: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        risks: list[dict[str, Any]] = []
        contract: dict[str, Any] = {}
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO
        predicate_plan = predicate_capacity_table(capacity_rows)
        policies = evidence_policy()
        routes = route_decision()
        gates = shortcut_gates()
        rejected = rejected_reuse_table()
        risks = reviewer_risk_table()
        contract = target_contrast_contract()

    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_probe_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "close_by_path_decision": rel_path(args.close_by_decision_dir / "summary.json"),
            "capacity_scan_predicate_capacity": rel_path(args.capacity_dir / "predicate_capacity.csv"),
            "feature_review": rel_path(args.feature_review_dir / "summary.json"),
            "pose_conditioned_result_review": rel_path(args.pose_result_dir / "summary.json"),
            "visual_repair_path_decision": rel_path(args.visual_repair_decision_dir / "summary.json"),
        },
        "next_todo": next_todo,
        "output_paths": {
            "evidence_policy": rel_path(args.output_dir / "evidence_policy.csv"),
            "predicate_probe_plan": rel_path(args.output_dir / "predicate_probe_plan.csv"),
            "rejected_reuse_table": rel_path(args.output_dir / "rejected_reuse_table.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "reviewer_risk_table": rel_path(args.output_dir / "reviewer_risk_table.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "shortcut_gates": rel_path(args.output_dir / "shortcut_gates.csv"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "target_contrast_contract": rel_path(args.output_dir / "target_contrast_contract.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "selected_predicates": {
            "primary": "standing on",
            "secondary": "lying on",
            "diagnostic": "supported by",
        },
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "target_contrast_contract.json", contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "predicate_probe_plan.csv", predicate_plan)
    write_csv(args.output_dir / "evidence_policy.csv", policies)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_csv(args.output_dir / "shortcut_gates.csv", gates)
    write_csv(args.output_dir / "rejected_reuse_table.csv", rejected)
    write_csv(args.output_dir / "reviewer_risk_table.csv", risks)
    write_report(args.output_dir / "report.md", summary, predicate_plan, routes)

    print(
        json.dumps(
            {
                "status": status,
                "selected_path": selected_path,
                "validation_errors": len(validation_errors),
                "next_todo": next_todo,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
