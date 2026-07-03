#!/usr/bin/env python3
"""Plan the next H002 evidence gap after the paper-table skeleton review."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock"
DEFAULT_OFFICIAL_SOURCE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_source_inventory_after_protocol_plan"
DEFAULT_SUPPORT_POINT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position"
DEFAULT_SUPPORT_POSE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review"
DEFAULT_ATTACHMENT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_attachment_observability_class_pair_repair_path_decision_after_schema_shortcut_audit"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_principled_design_gap_plan_after_table_review"

EXPECTED_REVIEW_STATUS = "h002_compatibility_dataset_v3_paper_table_skeleton_review_after_claim_boundary_lock_reviewed"
EXPECTED_REVIEW_NEXT = "compatibility_dataset_v3_principled_design_gap_plan_after_table_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_principled_design_gap_plan_after_table_review_v1"
STATUS_READY = "h002_compatibility_dataset_v3_principled_design_gap_plan_after_table_review_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_principled_design_gap_plan_after_table_review_input_errors"
SELECTED_PATH = "select_harder_support_contact_route_protocol_before_source_deployable_promotion"
NEXT_TODO = "compatibility_dataset_v3_support_contact_harder_route_protocol_after_gap_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
    parser.add_argument("--official-source-dir", type=Path, default=DEFAULT_OFFICIAL_SOURCE_DIR)
    parser.add_argument("--support-point-dir", type=Path, default=DEFAULT_SUPPORT_POINT_DIR)
    parser.add_argument("--support-pose-dir", type=Path, default=DEFAULT_SUPPORT_POSE_DIR)
    parser.add_argument("--attachment-dir", type=Path, default=DEFAULT_ATTACHMENT_DIR)
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
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def validate_inputs(review_summary: dict[str, Any], review_dir: Path, recommendation: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if review_summary.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review_summary.get("status")})
    if review_summary.get("next_todo") != EXPECTED_REVIEW_NEXT:
        errors.append({"error_type": "unexpected_review_next_todo", "actual": review_summary.get("next_todo")})
    if review_summary.get("validation_errors") != 0:
        errors.append({"error_type": "review_validation_errors", "actual": review_summary.get("validation_errors")})
    if line_count(review_dir / "validation_errors.jsonl") != 0:
        errors.append({"error_type": "review_validation_errors_file_not_empty"})

    decision = review_summary.get("decision", {})
    required = {
        "principled_structure": True,
        "natural_design_flow": True,
        "table_is_standalone_paper_result": False,
        "keep_as_bounded_mechanism_evidence": True,
        "final_paper_result_promotion": "not_yet",
    }
    for key, expected in required.items():
        if decision.get(key) != expected:
            errors.append({"error_type": "unexpected_review_decision", "key": key, "actual": decision.get(key), "expected": expected})

    rec_lookup = {row.get("option"): row.get("recommendation") for row in recommendation}
    if rec_lookup.get("C_add_harder_route_before_promotion") != "strong_accept":
        errors.append({"error_type": "harder_route_not_recommended", "actual": rec_lookup.get("C_add_harder_route_before_promotion")})
    if rec_lookup.get("D_shift_to_source_reranking_immediately") != "defer":
        errors.append({"error_type": "source_reranking_not_deferred", "actual": rec_lookup.get("D_shift_to_source_reranking_immediately")})
    return errors


def evidence_context(
    official_source: dict[str, Any],
    support_point: dict[str, Any],
    support_pose: dict[str, Any],
    attachment: dict[str, Any],
) -> dict[str, Any]:
    return {
        "official_source_status": official_source.get("status"),
        "official_source_next": official_source.get("next_todo"),
        "official_source_selected_policy": official_source.get("selected_policy", {}),
        "support_point_status": support_point.get("status"),
        "support_point_selected_path": support_point.get("selected_path"),
        "support_pose_status": support_pose.get("status"),
        "support_pose_selected_path": support_pose.get("selected_path"),
        "attachment_status": attachment.get("status"),
        "attachment_selected_path": attachment.get("selected_path"),
    }


def gap_inventory_rows() -> list[dict[str, Any]]:
    return [
        {
            "gap": "G1_obvious_signed_comparison",
            "severity": "high",
            "current_evidence": "Primary table uses relative_vertical + size_relative; M4 AUROC 0.995453.",
            "why_it_matters": "Reviewer can reduce the result to direct signed geometry checks.",
            "repair_direction": "Add a harder non-sign route where relation semantics changes how geometry is interpreted.",
            "selected_for_next": "yes",
        },
        {
            "gap": "G2_not_source_deployable",
            "severity": "high",
            "current_evidence": "Current official table is GT/counterfactual mechanism evaluation, not VL-SAT/Open3DSG source reranking.",
            "why_it_matters": "A reliability method eventually needs to work on source candidate outputs.",
            "repair_direction": "Run source-candidate experiment only after harder C_e route is stable.",
            "selected_for_next": "defer_after_harder_route",
        },
        {
            "gap": "G3_p_obs_p_rel_not_evaluated",
            "severity": "medium",
            "current_evidence": "Q_e/p_obs/p_rel are principled but disabled in official table.",
            "why_it_matters": "The full framework includes selective decision and abstention.",
            "repair_direction": "Keep as design/future until independent observability labels are stable.",
            "selected_for_next": "defer",
        },
        {
            "gap": "G4_support_contact_evidence_weakness",
            "severity": "medium_high",
            "current_evidence": "Official support_contact M4 AUROC 0.631712; wrong-T across-route control can be stronger.",
            "why_it_matters": "support/contact is the natural hard route that would reduce the signed-comparison critique.",
            "repair_direction": "Create a support_contact harder-route protocol with richer pose/contact/mesh/point evidence and stricter controls.",
            "selected_for_next": "yes",
        },
        {
            "gap": "G5_attachment_observability_shortcut",
            "severity": "medium",
            "current_evidence": "Attachment class-pair repair remains shortcut-blocked and p_obs negative-sparse.",
            "why_it_matters": "Attachment would test observability, but current labels collapse to class priors.",
            "repair_direction": "Keep attachment as diagnostic until visual/mesh evidence labels are redesigned.",
            "selected_for_next": "defer",
        },
    ]


def option_decision_rows() -> list[dict[str, Any]]:
    return [
        {
            "option": "A_promote_current_table",
            "decision": "reject",
            "reason": "Current table is strong mechanism evidence but too clean/signed-comparison-heavy.",
            "next_action": "none",
        },
        {
            "option": "B_harder_support_contact_route",
            "decision": "selected",
            "reason": "Directly addresses the signed-comparison critique using a nontrivial contact/pose relation family already present in official validation.",
            "next_action": NEXT_TODO,
        },
        {
            "option": "C_source_deployable_experiment",
            "decision": "defer",
            "reason": "Source reranking is important, but premature before a harder C_e route is stable.",
            "next_action": "run_after_harder_route_protocol_and_smoke",
        },
        {
            "option": "D_observability_pobs_branch",
            "decision": "defer",
            "reason": "Q_e/p_obs is principled, but existing observability labels are shortcut-prone or negative-sparse.",
            "next_action": "run_after_label_redesign_or_visual_mesh_target_repair",
        },
        {
            "option": "E_attachment_observability_route",
            "decision": "defer",
            "reason": "Current attached/hanging labels collapse to class-pair shortcuts after visual label fill.",
            "next_action": "keep_as_diagnostic_until_label_redesign",
        },
    ]


def protocol_requirements_rows() -> list[dict[str, Any]]:
    return [
        {
            "requirement": "target_scope",
            "locked_value": "support_contact harder route: standing on, lying on; supported by diagnostic only",
            "reason": "Avoid broad superordinate support ambiguity while testing nontrivial predicate-geometry compatibility.",
        },
        {
            "requirement": "evidence_scope",
            "locked_value": "G_e enriched with pose/contact/overlap/gap/point or mesh evidence; T_e kept separate; Z_e/Q_e excluded from C_e",
            "reason": "The next route should test C_e, not source confidence or observability truth.",
        },
        {
            "requirement": "controls",
            "locked_value": "semantic-only, geometry-only, concat, wrong-T same-route, shuffled-G global/within-family, subject-object swap, class-pair shortcut audit",
            "reason": "The prior failure modes were shortcut leakage and weak control collapse.",
        },
        {
            "requirement": "split_policy",
            "locked_value": "protocol first; then Docker official-validation or grouped heldout; no official test",
            "reason": "Preserve paper-level discipline and avoid test leakage.",
        },
        {
            "requirement": "promotion_gate",
            "locked_value": "M4 must beat T-only/G-only/concat and degrade under wrong-T/shuffled-G; support_contact cannot be called solved unless controls pass",
            "reason": "The goal is interaction necessity, not inflated absolute AUROC.",
        },
        {
            "requirement": "paper_boundary",
            "locked_value": "hard-route evidence only; no p_rel/p_obs, source reranking, SOTA, or all-relation claim",
            "reason": "Keep the next stage aligned with the current H002 mechanism claim.",
        },
    ]


def selected_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "selected_path": SELECTED_PATH,
        "purpose": "Design a harder support/contact compatibility route before any paper-result promotion.",
        "why_this_next": [
            "It directly targets the current table's strongest critique: signed-comparison tasks are too clean.",
            "support/contact requires pose/contact evidence and cannot be reduced to a simple vertical or size sign.",
            "Prior support/contact probes show interaction evidence, but official validation remains diagnostic, so protocol repair is justified.",
            "Source reranking and p_obs/p_rel are important but should follow a stable hard-route C_e protocol."
        ],
        "selected_family": "support_contact_harder_route",
        "relation_types": {
            "main": ["standing on", "lying on"],
            "diagnostic": ["supported by"],
            "deferred": ["attached to", "hanging on", "connected to"],
        },
        "feature_boundary": {
            "T_e": "predicate text/label and semantic content only",
            "G_e": "predicate-independent pose/contact/overlap/gap/point/mesh evidence",
            "Z_e": "excluded from C_e; can only be diagnostic",
            "Q_e": "excluded from C_e; can only be diagnostic until p_obs labels are stable",
        },
        "blocked_claims": [
            "support_contact solved",
            "calibrated p_rel/p_obs",
            "source reranking recall/violation improvement",
            "official test result",
            "all 3DSSG relation generalization",
        ],
        "success_conditions": [
            "protocol defines model-safe/hidden fields and C_e input boundaries",
            "row materialization can support class-pair and predicate-class-pair shortcut audits",
            "M4-style compatibility beats T-only, G-only, and concat",
            "wrong-T and shuffled-G controls degrade",
            "support_contact remains framed as hard-route evidence unless controls and external validation pass",
        ],
    }


def write_report(
    path: Path,
    summary: dict[str, Any],
    gaps: list[dict[str, Any]],
    options: list[dict[str, Any]],
    requirements: list[dict[str, Any]],
    contract: dict[str, Any],
) -> None:
    lines = [
        "# H002 Principled Design Gap Plan After Table Review",
        "",
        "## Status",
        "",
        "```text",
        f"artifact_root = {summary['output_artifacts']['artifact_root']}",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Judgment",
        "",
        "The H002 design remains principled. The current weakness is not the factorization",
        "itself, but the evidence mix: the strongest table rows are signed-comparison",
        "relations that can look too close to direct geometry rules.",
        "",
        "Therefore the next step should not be stronger model tuning or immediate source",
        "reranking. The next step should design a harder support/contact compatibility",
        "route with richer geometry evidence and the same strict C_e feature boundary.",
        "",
        "## Gap Inventory",
        "",
        "| Gap | Severity | Selected | Repair Direction |",
        "| --- | --- | --- | --- |",
    ]
    for row in gaps:
        lines.append(f"| `{row['gap']}` | {row['severity']} | {row['selected_for_next']} | {row['repair_direction']} |")
    lines.extend(["", "## Option Decision", "", "| Option | Decision | Reason |", "| --- | --- | --- |"])
    for row in options:
        lines.append(f"| `{row['option']}` | {row['decision']} | {row['reason']} |")
    lines.extend(["", "## Selected Protocol Requirements", "", "| Requirement | Locked Value | Reason |", "| --- | --- | --- |"])
    for row in requirements:
        lines.append(f"| `{row['requirement']}` | {row['locked_value']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Selected Contract",
            "",
            "```json",
            json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Decision",
            "",
            "- Keep the existing table as bounded mechanism evidence.",
            "- Do not promote H002 to final paper result yet.",
            "- Select the support/contact harder-route protocol as the next step.",
            "- Defer source-deployable reranking and p_obs/p_rel until after the hard-route protocol is stable.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir

    review_summary = read_json(args.review_dir / "summary.json")
    recommendation = read_csv(args.review_dir / "recommendation.csv")
    validation_errors = validate_inputs(review_summary, args.review_dir, recommendation)

    official_source = read_json(args.official_source_dir / "summary.json")
    support_point = read_json(args.support_point_dir / "summary.json")
    support_pose = read_json(args.support_pose_dir / "summary.json")
    attachment = read_json(args.attachment_dir / "summary.json")

    gaps = gap_inventory_rows()
    options = option_decision_rows()
    requirements = protocol_requirements_rows()
    contract = selected_contract()
    context = evidence_context(official_source, support_point, support_pose, attachment)

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "blocked_fix_review_inputs_before_gap_plan",
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO if not validation_errors else EXPECTED_REVIEW_NEXT,
        "input_artifacts": {
            "table_review_summary": rel_path(args.review_dir / "summary.json"),
            "table_review_recommendation": rel_path(args.review_dir / "recommendation.csv"),
            "official_source_inventory": rel_path(args.official_source_dir / "summary.json"),
            "support_point_multiview_review": rel_path(args.support_point_dir / "summary.json"),
            "support_pose_conditioned_review": rel_path(args.support_pose_dir / "summary.json"),
            "attachment_observability_decision": rel_path(args.attachment_dir / "summary.json"),
        },
        "decision": {
            "principled_structure_kept": True,
            "current_table_role": "bounded_mechanism_evidence",
            "final_paper_result_promotion": "not_yet",
            "selected_gap": "harder_support_contact_route",
            "selected_next_action": NEXT_TODO,
            "source_deployable_experiment": "defer_until_harder_route_stable",
            "p_obs_p_rel_branch": "defer_until_independent_observability_labels",
        },
        "evidence_context": context,
        "output_artifacts": {
            "artifact_root": rel_path(output_dir),
            "gap_inventory": rel_path(output_dir / "gap_inventory.csv"),
            "option_decision": rel_path(output_dir / "option_decision.csv"),
            "protocol_requirements": rel_path(output_dir / "protocol_requirements.csv"),
            "selected_contract": rel_path(output_dir / "selected_contract.json"),
            "report": rel_path(output_dir / "report.md"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(output_dir / "gap_inventory.csv", gaps)
    write_csv(output_dir / "option_decision.csv", options)
    write_csv(output_dir / "protocol_requirements.csv", requirements)
    write_json(output_dir / "selected_contract.json", contract)
    write_report(output_dir / "report.md", summary, gaps, options, requirements, contract)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
