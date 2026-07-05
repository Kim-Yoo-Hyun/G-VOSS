#!/usr/bin/env python3
"""Review the repaired independent-validity smoke result and lock claim scope."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review"
)

EXPECTED_RUNNER_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner_passed_controls"
)
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review_accept_Ce_select_calibration_scope_plan"
)
STATUS_ERRORS = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review_input_errors"
SELECTED_PATH = "accept_independent_validity_Ce_smoke_select_calibration_and_scope_plan"
NEXT_TODO = "compatibility_dataset_v3_independent_validity_calibration_scope_plan"

PRIMARY_MODEL = "M6_TG_compatibility_interaction"
FULL_MODEL = "M7_factorized_TZGQ"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-dir", type=Path, default=DEFAULT_RUNNER_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


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
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def metric(summary: dict[str, Any], model: str, key: str = "auroc") -> float | None:
    value = summary.get("key_metrics", {}).get(model, {}).get(key)
    return None if value is None else float(value)


def gate(summary: dict[str, Any], name: str) -> bool:
    return summary.get("gates", {}).get(name, {}).get("pass") is True


def family_metric(metrics_by_family: dict[str, Any], family: str, model: str, key: str = "auroc") -> float | None:
    value = metrics_by_family.get("family", {}).get(family, {}).get(model, {}).get(key)
    return None if value is None else float(value)


def validate_runner(summary: dict[str, Any], validation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_next", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "runner_validation_errors", "actual": summary.get("validation_errors")})
    if validation_rows:
        errors.append({"error_type": "runner_validation_error_rows_present", "rows": len(validation_rows)})

    counts = summary.get("counts", {})
    if counts.get("rows") != 1600 or counts.get("positive") != 800 or counts.get("negative") != 800:
        errors.append({"error_type": "unexpected_counts", "counts": counts})
    if counts.get("mixed_label_groups") != 491:
        errors.append({"error_type": "unexpected_mixed_label_groups", "counts": counts})
    if counts.get("family_counts", {}).get("relative_vertical") != 1512:
        errors.append({"error_type": "unexpected_relative_vertical_count", "counts": counts})
    if counts.get("family_counts", {}).get("support_contact_pose_conditioned") != 88:
        errors.append({"error_type": "unexpected_support_contact_count", "counts": counts})

    for key in [
        "gate_data_integrity",
        "gate_semantic_source_shortcuts",
        "gate_primary_predictive_signal",
        "gate_gain_over_semantic_source",
        "gate_geometry_dominance_check",
        "gate_shuffle_controls",
        "gate_wrong_predicate_control",
        "gate_group_contrast_score_direction",
    ]:
        if not gate(summary, key):
            errors.append({"error_type": "required_gate_failed", "gate": key, "actual": summary.get("gates", {}).get(key)})

    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "raw_candidate_rows_used_as_model_input"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if summary.get("paper_evidence_allowed") is not False:
        errors.append({"error_type": "paper_evidence_unexpectedly_allowed"})

    primary_auc = metric(summary, PRIMARY_MODEL)
    geom_auc = metric(summary, "M4_geometry_only_G")
    best_semantic = summary.get("gates", {}).get("gate_semantic_source_shortcuts", {}).get("best_semantic_source")
    primary_ece = metric(summary, PRIMARY_MODEL, "ece_10")
    if primary_auc is None or primary_auc < 0.90:
        errors.append({"error_type": "primary_auc_below_review_gate", "actual": primary_auc})
    if geom_auc is None or geom_auc > 0.60:
        errors.append({"error_type": "geometry_only_above_review_gate", "actual": geom_auc})
    if best_semantic is None or float(best_semantic) > 0.60:
        errors.append({"error_type": "semantic_source_above_review_gate", "actual": best_semantic})
    if primary_ece is None:
        errors.append({"error_type": "missing_primary_ece"})
    return errors


def mechanism_result(summary: dict[str, Any], metrics_by_family: dict[str, Any]) -> dict[str, Any]:
    gates = summary.get("gates", {})
    primary_auc = metric(summary, PRIMARY_MODEL)
    full_auc = metric(summary, FULL_MODEL)
    geometry_auc = metric(summary, "M4_geometry_only_G")
    best_semantic = gates.get("gate_semantic_source_shortcuts", {}).get("best_semantic_source")
    return {
        "accepted": True,
        "level": "train_only_hypothesis_smoke",
        "primary_family_scope": "relative_vertical_dominant",
        "primary_model": PRIMARY_MODEL,
        "primary_auroc": primary_auc,
        "full_factorized_model": FULL_MODEL,
        "full_factorized_auroc": full_auc,
        "best_semantic_source_auroc": best_semantic,
        "geometry_only_auroc": geometry_auc,
        "plain_concat_auroc": metric(summary, "M5_TG_concat"),
        "source_only_auroc": metric(summary, "M2_source_only_Z"),
        "wrong_predicate_auroc": metric(summary, "C3_wrong_predicate_family_control"),
        "shuffled_g_global_auroc": metric(summary, "C1_shuffled_G_global"),
        "shuffled_g_within_predicate_auroc": metric(summary, "C2_shuffled_G_within_predicate"),
        "primary_gain_over_semantic_source": gates.get("gate_gain_over_semantic_source", {}).get("actual_gain"),
        "primary_gain_over_geometry_only": None if primary_auc is None or geometry_auc is None else primary_auc - geometry_auc,
        "primary_ece_10": metric(summary, PRIMARY_MODEL, "ece_10"),
        "calibrated_probability_claim_allowed": False,
        "family_slice": {
            "relative_vertical": {
                "rows": summary.get("counts", {}).get("family_counts", {}).get("relative_vertical"),
                "primary_auroc": family_metric(metrics_by_family, "relative_vertical", PRIMARY_MODEL),
                "geometry_only_auroc": family_metric(metrics_by_family, "relative_vertical", "M4_geometry_only_G"),
                "wrong_predicate_auroc": family_metric(metrics_by_family, "relative_vertical", "C3_wrong_predicate_family_control"),
                "verdict": "primary_supported",
            },
            "support_contact_pose_conditioned": {
                "rows": summary.get("counts", {}).get("family_counts", {}).get("support_contact_pose_conditioned"),
                "primary_auroc": family_metric(metrics_by_family, "support_contact_pose_conditioned", PRIMARY_MODEL),
                "full_factorized_auroc": family_metric(metrics_by_family, "support_contact_pose_conditioned", FULL_MODEL),
                "geometry_only_auroc": family_metric(metrics_by_family, "support_contact_pose_conditioned", "M4_geometry_only_G"),
                "wrong_predicate_auroc": family_metric(
                    metrics_by_family,
                    "support_contact_pose_conditioned",
                    "C3_wrong_predicate_family_control",
                ),
                "verdict": "diagnostic_only_small_slice",
            },
        },
    }


def route_rows(mech: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "route": "accept_repaired_independent_validity_Ce_smoke",
            "verdict": "selected",
            "evidence": (
                f"{PRIMARY_MODEL} AUROC {mech['primary_auroc']}; geometry-only {mech['geometry_only_auroc']}; "
                f"semantic/source max {mech['best_semantic_source_auroc']}."
            ),
            "reason": "The repaired target no longer collapses to semantic/source shortcuts or geometry-only evidence.",
            "next_action": "retain_as_current_strongest_H002_Ce_mechanism_evidence",
        },
        {
            "route": "claim_calibrated_relation_reliability_probability",
            "verdict": "reject",
            "evidence": f"Primary ECE-10 is {mech['primary_ece_10']}.",
            "reason": "The model discriminates compatibility well, but score calibration is poor.",
            "next_action": "run_calibration_scope_plan_before_any_p_rel_claim",
        },
        {
            "route": "promote_support_contact_from_this_artifact",
            "verdict": "reject_as_primary",
            "evidence": "support_contact_pose_conditioned contributes only 88 rows; slice wrong-predicate AUROC is marginal.",
            "reason": "The global result is relative-vertical dominant.",
            "next_action": "treat_support_contact_slice_as_diagnostic_and_design_family-specific follow-up if needed",
        },
        {
            "route": "promote_to_paper_level_experiment_now",
            "verdict": "defer",
            "evidence": "Runner is host-side train-only hypothesis smoke with no validation/test use.",
            "reason": "Paper promotion requires Docker reproduction, held-out protocol, calibration policy, and family scope freeze.",
            "next_action": "do_not_create_paper_experiment_root_yet",
        },
        {
            "route": "run_more_complex_combiner_now",
            "verdict": "reject",
            "evidence": "M6 and M7 are already near-perfect on this target.",
            "reason": "The next bottleneck is not architecture capacity; it is calibration, scope, and external validity.",
            "next_action": "avoid adding transformer/MoE before target and calibration risks are closed",
        },
        {
            "route": "calibration_and_scope_plan",
            "verdict": "selected_next",
            "evidence": "The result is strong but uncalibrated and relative-vertical dominant.",
            "reason": "This is the smallest next step that decides whether H002 can move from C_e discrimination to reliability scoring.",
            "next_action": NEXT_TODO,
        },
    ]


def family_rows(mech: dict[str, Any]) -> list[dict[str, Any]]:
    rel = mech["family_slice"]["relative_vertical"]
    support = mech["family_slice"]["support_contact_pose_conditioned"]
    return [
        {
            "family": "relative_vertical",
            "rows": rel["rows"],
            "predicates": "higher than; lower than",
            "primary_auroc": rel["primary_auroc"],
            "geometry_only_auroc": rel["geometry_only_auroc"],
            "wrong_predicate_auroc": rel["wrong_predicate_auroc"],
            "verdict": "primary_supported",
            "allowed_claim": "C_e strongly captures predicate-conditioned vertical compatibility.",
            "blocked_claim": "All-relation reliability or calibrated posterior.",
        },
        {
            "family": "support_contact_pose_conditioned",
            "rows": support["rows"],
            "predicates": "lying on; standing on",
            "primary_auroc": support["primary_auroc"],
            "geometry_only_auroc": support["geometry_only_auroc"],
            "wrong_predicate_auroc": support["wrong_predicate_auroc"],
            "verdict": "diagnostic_only",
            "allowed_claim": "There is a weak positive signal, but it is not a primary conclusion from this artifact.",
            "blocked_claim": "Support/contact independent-validity generality.",
        },
        {
            "family": "attachment_like",
            "rows": 0,
            "predicates": "attached to; hanging on; connected to",
            "primary_auroc": None,
            "geometry_only_auroc": None,
            "wrong_predicate_auroc": None,
            "verdict": "not_tested_here",
            "allowed_claim": "None from this artifact.",
            "blocked_claim": "Attachment generality.",
        },
        {
            "family": "proximity",
            "rows": 0,
            "predicates": "close by",
            "primary_auroc": None,
            "geometry_only_auroc": None,
            "wrong_predicate_auroc": None,
            "verdict": "not_tested_here",
            "allowed_claim": "None from this artifact.",
            "blocked_claim": "Proximity generality.",
        },
    ]


def reviewer_risk_rows(mech: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "risk": "calibration_gap",
            "severity": "high",
            "evidence": f"Primary ECE-10 is {mech['primary_ece_10']}.",
            "interpretation": "Current output is a strong ranker/discriminator, not a calibrated reliability posterior.",
            "required_next": "Define calibration objective and train-internal calibration diagnostic before p_rel/p_obs claims.",
        },
        {
            "risk": "relative_vertical_dominance",
            "severity": "high",
            "evidence": "1512/1600 rows are relative_vertical; support/contact contributes 88 rows.",
            "interpretation": "Current result mainly proves vertical compatibility.",
            "required_next": "Either freeze claim as relative-vertical primary or create a separate balanced support/contact target.",
        },
        {
            "risk": "too_clean_target",
            "severity": "medium",
            "evidence": f"{PRIMARY_MODEL} AUROC is {mech['primary_auroc']}.",
            "interpretation": "Near-perfect performance may reflect a clean mechanism target, not final open-world difficulty.",
            "required_next": "Use this as mechanism proof and evaluate harder/human/GT reliability later.",
        },
        {
            "risk": "train_only_evidence",
            "severity": "high",
            "evidence": "No validation/test usage; runner is hypothesis-stage host script.",
            "interpretation": "Not paper-level evidence.",
            "required_next": "Docker and held-out protocol only after calibration/scope decision.",
        },
        {
            "risk": "architecture_overfitting",
            "severity": "medium",
            "evidence": "M6 and M7 are already near-perfect; more complex models are unnecessary now.",
            "interpretation": "A transformer/MoE could mask target issues rather than solve them.",
            "required_next": "Do not add architecture complexity before calibration and scope blockers are resolved.",
        },
    ]


def claim_boundary(mech: dict[str, Any]) -> dict[str, Any]:
    return {
        "allowed_claim": (
            "On a train-only exact-stratum repaired independent-validity target, semantic/source "
            "features and predicate-independent geometry alone are insufficient, while an explicit "
            "predicate-conditioned compatibility factor C_e = compatibility(T_e, G_e) separates "
            "valid and invalid relation candidates."
        ),
        "allowed_scope": {
            "split": "train_internal_grouped_cv",
            "primary_family": "relative_vertical",
            "secondary_family": "support_contact_pose_conditioned_diagnostic_only",
            "task": "compatibility discrimination/ranking",
            "not_probability_calibration": True,
        },
        "blocked_claims": [
            "calibrated relation reliability posterior",
            "paper-level result",
            "held-out validation/test performance",
            "broad all-relation 3DSSG reliability",
            "support/contact independent-validity generality from this artifact",
            "attachment/proximity/horizontal relation generality",
        ],
        "why_not_h001_or_simple_geometry": (
            "The geometry-only baseline is near chance, and the signal appears only when T_e conditions "
            "the interpretation of G_e. Therefore this artifact supports compatibility learning rather "
            "than a standalone geometry verifier."
        ),
        "calibration_boundary": {
            "primary_ece_10": mech["primary_ece_10"],
            "calibrated_probability_claim_allowed": False,
            "next_requirement": NEXT_TODO,
        },
    }


def write_report(path: Path, summary: dict[str, Any], mech: dict[str, Any], risks: list[dict[str, Any]]) -> None:
    support = mech["family_slice"]["support_contact_pose_conditioned"]
    lines = [
        "# Compatibility Dataset V3 Independent Validity Stratum Repair Smoke Result Review",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review/",
        "```",
        "",
        "Status:",
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
        "The repaired independent-validity smoke is accepted as the current strongest H002",
        "`C_e` mechanism evidence. It fixed the earlier shortcut and geometry-dominance blockers:",
        "",
        f"- semantic/source max AUROC: `{mech['best_semantic_source_auroc']}`",
        f"- geometry-only AUROC: `{mech['geometry_only_auroc']}`",
        f"- `M6_TG_compatibility_interaction` AUROC: `{mech['primary_auroc']}`",
        f"- `M7_factorized_TZGQ` AUROC: `{mech['full_factorized_auroc']}`",
        f"- wrong-predicate control AUROC: `{mech['wrong_predicate_auroc']}`",
        "",
        "## Claim Boundary",
        "",
        "Allowed claim:",
        "",
        "> Train-internal repaired independent-validity evidence supports explicit",
        "> predicate-conditioned semantic-geometry compatibility `C_e` as a necessary factor for",
        "> relation reliability representation.",
        "",
        "Blocked claims:",
        "",
        "- calibrated posterior reliability;",
        "- paper-level or held-out result;",
        "- broad all-relation 3DSSG generality;",
        "- support/contact generality from this artifact alone.",
        "",
        "## Family Scope",
        "",
        f"- `relative_vertical`: primary supported, rows `{mech['family_slice']['relative_vertical']['rows']}`, AUROC `{mech['family_slice']['relative_vertical']['primary_auroc']}`.",
        f"- `support_contact_pose_conditioned`: diagnostic only, rows `{support['rows']}`, AUROC `{support['primary_auroc']}`, wrong-predicate AUROC `{support['wrong_predicate_auroc']}`.",
        "",
        "## Main Risks",
        "",
    ]
    for risk in risks:
        lines.append(f"- `{risk['risk']}` ({risk['severity']}): {risk['interpretation']}")
    lines.extend(
        [
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    runner_summary = read_json(args.runner_dir / "summary.json")
    metrics_by_family = read_json(args.runner_dir / "metrics_by_family.json")
    validation_rows = read_jsonl(args.runner_dir / "validation_errors.jsonl")
    errors = validate_runner(runner_summary, validation_rows)
    mech = mechanism_result(runner_summary, metrics_by_family)
    routes = route_rows(mech)
    families = family_rows(mech)
    risks = reviewer_risk_rows(mech)
    boundary = claim_boundary(mech)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_ERRORS if errors else STATUS_READY,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "runner_root": rel_path(args.runner_dir),
        "output_root": rel_path(args.output_dir),
        "validation_errors": len(errors),
        "mechanism_result": mech,
        "claim_boundary": boundary,
        "paper_evidence_allowed": False,
        "boundary": {
            "split": "train_internal_grouped_cv",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "calibrated_probability_claim_allowed": False,
            "support_contact_primary_claim_allowed": False,
            "paper_promotion_allowed": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "claim_boundary": rel_path(args.output_dir / "claim_boundary.json"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "family_scope": rel_path(args.output_dir / "family_scope.csv"),
            "reviewer_risks": rel_path(args.output_dir / "reviewer_risks.csv"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
            "report": rel_path(args.output_dir / "report.md"),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "claim_boundary.json", boundary)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_jsonl(args.output_dir / "route_decision.jsonl", routes)
    write_csv(args.output_dir / "family_scope.csv", families)
    write_jsonl(args.output_dir / "family_scope.jsonl", families)
    write_csv(args.output_dir / "reviewer_risks.csv", risks)
    write_jsonl(args.output_dir / "reviewer_risks.jsonl", risks)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", summary, mech, risks)

    print(
        "status={status} selected={selected} M6={m6} M4={m4} ECE={ece} next={next_todo}".format(
            status=summary["status"],
            selected=summary["selected_path"],
            m6=mech["primary_auroc"],
            m4=mech["geometry_only_auroc"],
            ece=mech["primary_ece_10"],
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
