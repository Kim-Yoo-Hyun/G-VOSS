#!/usr/bin/env python3
"""Review H002 route-coverage sufficiency after the relative-horizontal table plan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_TABLE_PLAN_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis"
)
DEFAULT_GAP_AUDIT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan"
)

EXPECTED_TABLE_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis_ready"
)
EXPECTED_TABLE_PLAN_NEXT = (
    "compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan"
)
EXPECTED_GAP_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan_ready"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan_ready"
)
STATUS_ERRORS = (
    "h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan_input_errors"
)
SELECTED_PATH = (
    "coverage_sufficient_for_hypothesis_framework_proceed_to_schema_freeze_promotion_protocol_no_new_family_now"
)
NEXT_TODO = "compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table-plan-dir", type=Path, default=DEFAULT_TABLE_PLAN_DIR)
    parser.add_argument("--gap-audit-dir", type=Path, default=DEFAULT_GAP_AUDIT_DIR)
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
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
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
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    table_summary: dict[str, Any],
    gap_summary: dict[str, Any],
    main_table_rows: list[dict[str, str]],
    route_rows: list[dict[str, str]],
    promotion_rows: list[dict[str, str]],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if table_summary.get("status") != EXPECTED_TABLE_PLAN_STATUS:
        errors.append({"input": "table_plan", "error_type": "unexpected_status", "actual": table_summary.get("status")})
    if table_summary.get("next_todo") != EXPECTED_TABLE_PLAN_NEXT:
        errors.append({"input": "table_plan", "error_type": "unexpected_next_todo", "actual": table_summary.get("next_todo")})
    if table_summary.get("validation_errors") != 0:
        errors.append(
            {"input": "table_plan", "error_type": "validation_errors_present", "actual": table_summary.get("validation_errors")}
        )
    if read_jsonl(roots["table_plan"] / "validation_errors.jsonl"):
        errors.append({"input": "table_plan", "error_type": "validation_error_rows_present"})

    if gap_summary.get("status") != EXPECTED_GAP_AUDIT_STATUS:
        errors.append({"input": "gap_audit", "error_type": "unexpected_status", "actual": gap_summary.get("status")})
    if gap_summary.get("validation_errors") != 0:
        errors.append(
            {"input": "gap_audit", "error_type": "validation_errors_present", "actual": gap_summary.get("validation_errors")}
        )
    if read_jsonl(roots["gap_audit"] / "validation_errors.jsonl"):
        errors.append({"input": "gap_audit", "error_type": "validation_error_rows_present"})

    boundary = table_summary.get("boundary", {})
    for key in [
        "h001_artifacts_modified",
        "paper_evidence_allowed",
        "runs_new_learned_smoke",
        "test_usage",
        "trains_new_model",
        "validation_usage",
    ]:
        if boundary.get(key) is not False:
            errors.append({"input": "table_plan", "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})

    main_rows = set(table_summary.get("main_mechanism_families", []))
    expected_main = {"relative_vertical", "size_relative", "relative_horizontal", "support_contact"}
    missing_main = expected_main - main_rows
    if missing_main:
        errors.append({"input": "table_plan", "error_type": "missing_main_mechanism_family", "missing": sorted(missing_main)})

    route_families = {row.get("family") for row in route_rows}
    for family in ["proximity", "support_contact_superordinate", "attachment_like"]:
        if family not in route_families:
            errors.append({"input": "route_taxonomy", "error_type": "missing_boundary_family", "family": family})

    table_ids = {row.get("table_id") for row in main_table_rows}
    if not {"T1", "T2", "T3", "T4"}.issubset(table_ids):
        errors.append({"input": "main_table_plan", "error_type": "missing_required_table", "actual": sorted(table_ids)})

    gate_ids = {row.get("gate_id") for row in promotion_rows}
    if "G2" not in gate_ids or "G9" not in gate_ids:
        errors.append({"input": "promotion_gates", "error_type": "missing_route_or_wording_gate", "actual": sorted(gate_ids)})
    return errors


def coverage_criteria() -> list[dict[str, Any]]:
    return [
        {
            "criterion_id": "C1",
            "criterion": "clean signed geometry route",
            "required_for": "mechanism identifiability",
            "families": "relative_vertical",
            "status": "pass",
            "interpretation": "higher/lower provides a clean T_e x signed-G_e anchor but is too easy alone",
        },
        {
            "criterion_id": "C2",
            "criterion": "clean non-axis physical route",
            "required_for": "avoid vertical-only claim",
            "families": "size_relative",
            "status": "pass_with_calibration_caveat",
            "interpretation": "bigger/smaller gives an independent physical comparison route; high AUROC is mechanism evidence, not calibrated reliability",
        },
        {
            "criterion_id": "C3",
            "criterion": "frame-aware directional route",
            "required_for": "avoid excluding horizontal spatial relations",
            "families": "relative_horizontal",
            "status": "pass_with_reference_frame_caveat",
            "interpretation": "left/right/front/behind adds reference-frame-sensitive compatibility with wrong-frame and endpoint-swap controls",
        },
        {
            "criterion_id": "C4",
            "criterion": "challenging contact/pose route",
            "required_for": "avoid only rule-like clean routes",
            "families": "support_contact",
            "status": "pass_with_challenging_case_caveat",
            "interpretation": "standing/lying contact route shows interaction necessity but remains near-threshold and not fully solved",
        },
        {
            "criterion_id": "C5",
            "criterion": "geometry-easy diagnostic/control",
            "required_for": "show framework does not force learned compatibility where geometry suffices",
            "families": "proximity",
            "status": "pass_as_control_not_main",
            "interpretation": "close by is retained as a geometry-only route/control, not as main C_e proof",
        },
        {
            "criterion_id": "C6",
            "criterion": "observability-heavy boundary",
            "required_for": "define Q_e/p_obs boundary",
            "families": "attachment_like",
            "status": "pass_as_deferred_boundary",
            "interpretation": "attached/hanging/connected require visual/mesh evidence and should remain future/deferred",
        },
        {
            "criterion_id": "C7",
            "criterion": "superordinate and non-physical boundary",
            "required_for": "prevent all-family overclaim",
            "families": "supported_by; containment_in; part_structural; identity_symmetry",
            "status": "pass_as_boundary",
            "interpretation": "these relations are diagnostic, future, or out-of-scope for the current physical compatibility claim",
        },
        {
            "criterion_id": "C8",
            "criterion": "all-family generality",
            "required_for": "broad 3DSSG relation reliability claim",
            "families": "all 3DSSG/Open3DSG predicates",
            "status": "blocked_not_required_for_current_claim",
            "interpretation": "not needed for the current hypothesis-stage route framework; must remain outside the claim",
        },
    ]


def updated_family_decisions(route_rows: list[dict[str, str]], gap_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    route_by_family = {row.get("family"): row for row in route_rows}
    gap_by_family = {row.get("family"): row for row in gap_rows}
    families = [
        "relative_vertical",
        "size_relative",
        "relative_horizontal",
        "support_contact",
        "proximity",
        "support_contact_superordinate",
        "attachment_like",
        "containment_in",
        "part_structural",
        "identity_symmetry",
        "background_none",
    ]
    fallback = {
        "support_contact_superordinate": {
            "predicates": "supported by",
            "route": "diagnostic taxonomy",
            "use_in_claim": "diagnostic",
            "decision": "defer primary claim",
            "risk": "superordinate support label cannot be used as clean accept/reject target",
        },
        "containment_in": {
            "predicates": "standing in; lying in; hanging in; inside",
            "route": "future containment route",
            "use_in_claim": "future_or_diagnostic",
            "decision": "defer; low GT and containment/occlusion ambiguity",
            "risk": "small count and ambiguous containment geometry",
        },
        "part_structural": {
            "predicates": "build in; leaning against; belonging to; part of; cover",
            "route": "semantic/structural boundary",
            "use_in_claim": "out_of_scope_boundary",
            "decision": "do not use as main physical compatibility target now",
            "risk": "can become ontology/part segmentation rather than predicate-geometry compatibility",
        },
        "identity_symmetry": {
            "predicates": "same as; same symmetry as",
            "route": "identity/symmetry boundary",
            "use_in_claim": "out_of_scope_boundary",
            "decision": "exclude from current physical compatibility claim",
            "risk": "identity and symmetry are separate reasoning tasks",
        },
        "background_none": {
            "predicates": "none",
            "route": "no-relation background",
            "use_in_claim": "out_of_scope",
            "decision": "ignore for H002 relation-family coverage",
            "risk": "not a relation family",
        },
    }
    role_override = {
        "relative_vertical": "main_clean_mechanism_anchor",
        "size_relative": "main_clean_mechanism_anchor_with_calibration_caveat",
        "relative_horizontal": "main_frame_aware_mechanism_anchor_with_reference_frame_caveat",
        "support_contact": "main_challenging_compatibility_route_with_caveat",
        "proximity": "geometry_easy_control_or_generality",
        "support_contact_superordinate": "diagnostic_superordinate_boundary",
        "attachment_like": "observability_heavy_future_or_diagnostic",
        "containment_in": "future_containment_boundary",
        "part_structural": "semantic_structural_boundary",
        "identity_symmetry": "identity_symmetry_boundary",
        "background_none": "ignore",
    }
    claim_use = {
        "relative_vertical": "main",
        "size_relative": "main",
        "relative_horizontal": "main_with_reference_frame_caveat",
        "support_contact": "main_with_caveat",
        "proximity": "control_or_generality",
        "support_contact_superordinate": "diagnostic",
        "attachment_like": "future_or_diagnostic",
        "containment_in": "future_or_diagnostic",
        "part_structural": "boundary_only",
        "identity_symmetry": "boundary_only",
        "background_none": "exclude",
    }
    rows: list[dict[str, Any]] = []
    for family in families:
        route = route_by_family.get(family, {})
        gap = gap_by_family.get(family, {})
        fb = fallback.get(family, {})
        rows.append(
            {
                "family": family,
                "predicates": route.get("predicates") or gap.get("predicates") or fb.get("predicates", ""),
                "coverage_status_after_review": role_override[family],
                "use_in_claim": claim_use[family],
                "route": route.get("route") or fb.get("route", ""),
                "evidence_route": route.get("evidence_route") or gap.get("evidence_need") or "",
                "decision": route.get("decision") or fb.get("decision", ""),
                "risk": route.get("risk") or gap.get("risk") or fb.get("risk", ""),
                "gt_total_if_known": gap.get("gt_total", ""),
                "queue_total_if_known": gap.get("queue_total", ""),
                "paper_action": paper_action_for_family(family),
            }
        )
    return rows


def paper_action_for_family(family: str) -> str:
    actions = {
        "relative_vertical": "keep in T1 as clean mechanism row",
        "size_relative": "keep in T1 as clean mechanism row with calibration caveat",
        "relative_horizontal": "keep in T1 as frame-aware mechanism row; do not claim complete horizontal ontology",
        "support_contact": "keep in T1 as challenging compatibility route evidence; do not call solved",
        "proximity": "keep in T2/T3 as geometry-easy route/control",
        "support_contact_superordinate": "keep in T3 as diagnostic boundary",
        "attachment_like": "keep in T2/T3 as observability-heavy future route",
        "containment_in": "list as future containment route only if all-family inventory is discussed",
        "part_structural": "list as boundary/out-of-scope if reviewer asks about missing predicates",
        "identity_symmetry": "list as boundary/out-of-scope if reviewer asks about missing predicates",
        "background_none": "omit from paper relation-family claim",
    }
    return actions[family]


def sufficiency_decision() -> list[dict[str, Any]]:
    return [
        {
            "decision_id": "D1",
            "option": "add another family before promotion planning",
            "verdict": "reject_for_now",
            "reason": "current coverage already includes clean sign, clean size, frame-aware horizontal, challenging contact, geometry-easy control, and observability-heavy boundary",
            "when_to_reopen": "only if the paper claim is widened to all-family generality or deployable visual/mesh attachment evidence",
        },
        {
            "decision_id": "D2",
            "option": "proceed to schema freeze and promotion protocol",
            "verdict": "selected",
            "reason": "the missing step is no longer family discovery; it is freezing model-safe fields, split policy, Docker reproduction, calibration boundary, and claim wording",
            "when_to_reopen": "after schema freeze, if held-out/Docker planning reveals a family-specific leakage or support/contact instability blocker",
        },
        {
            "decision_id": "D3",
            "option": "claim all relation families are covered",
            "verdict": "reject",
            "reason": "attachment, containment, part/structural, identity/symmetry, and complete horizontal ontology remain outside current evidence",
            "when_to_reopen": "requires new adapters, labels/evidence, controls, and held-out experiments",
        },
        {
            "decision_id": "D4",
            "option": "drop support/contact because it is near-threshold",
            "verdict": "reject",
            "reason": "support/contact is the only current challenging route showing that clean deterministic routes are not the whole story",
            "when_to_reopen": "if failure analysis shows controls no longer collapse or interaction no longer beats single-factor baselines",
        },
    ]


def next_gate_plan() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "N1",
            "next_gate": "schema freeze",
            "purpose": "freeze model-safe fields, hidden construction fields, and artifact provenance before any promotion run",
            "required_output": "schema-freeze manifest; blocked-field audit; input provenance table",
            "blocks": "all learned/Docker promotion",
        },
        {
            "gate_id": "N2",
            "next_gate": "promotion protocol",
            "purpose": "decide which hypothesis-stage rows can become Docker-reproducible paper-level experiments",
            "required_output": "Docker/compose plan, split manifest, metric table contract, rerun commands",
            "blocks": "paper-level performance claim",
        },
        {
            "gate_id": "N3",
            "next_gate": "held-out grouped evaluation plan",
            "purpose": "move beyond train-only mechanism evidence without scan/endpoint leakage",
            "required_output": "scan and endpoint-pair grouped split definition; no target-construction leakage statement",
            "blocks": "held-out/test reliability claim",
        },
        {
            "gate_id": "N4",
            "next_gate": "calibration protocol",
            "purpose": "separate high-AUROC compatibility scores from calibrated p_rel/p_obs probability claims",
            "required_output": "proper-scoring/ECE/Brier protocol and calibration split",
            "blocks": "calibrated p_rel/p_obs claim",
        },
        {
            "gate_id": "N5",
            "next_gate": "wording lock",
            "purpose": "prevent overclaiming complete horizontal ontology, all-family generality, and solved support/contact",
            "required_output": "claim boundary checklist and reviewer response table",
            "blocks": "paper writing",
        },
    ]


def reviewer_risks() -> list[dict[str, Any]]:
    return [
        {
            "risk": "The selected families are cherry-picked.",
            "severity": "high",
            "answer": "Report the family inventory and boundary table: main rows, diagnostic controls, future/deferred, and out-of-scope families are all explicit.",
            "needed_artifact": "family decision table and route taxonomy",
        },
        {
            "risk": "Clean families are deterministic rules.",
            "severity": "medium",
            "answer": "Use clean routes as mechanism-identifiability anchors, not as the whole method; support/contact remains the challenging route.",
            "needed_artifact": "T1 ablation plus support/contact caveat",
        },
        {
            "risk": "close by is only a distance verifier.",
            "severity": "medium",
            "answer": "Keep proximity as geometry-easy control/generality, not main compatibility evidence.",
            "needed_artifact": "T2/T3 diagnostic boundary table",
        },
        {
            "risk": "Horizontal relations are incomplete.",
            "severity": "high_if_hidden",
            "answer": "State frame convention and `in front of` exclusion. Do not claim complete horizontal ontology.",
            "needed_artifact": "relative-horizontal controls and claim boundary",
        },
        {
            "risk": "Support/contact is not fully solved.",
            "severity": "high_if_overclaimed",
            "answer": "Use it as challenging compatibility-route evidence because interaction beats single-factor baselines and controls collapse; do not call it solved.",
            "needed_artifact": "support/contact failure analysis and caveat",
        },
        {
            "risk": "H002 still lacks paper-level evidence.",
            "severity": "high",
            "answer": "Correct. Route coverage is sufficient only to start schema freeze and promotion protocol, not to claim final results.",
            "needed_artifact": "next gate plan",
        },
    ]


def write_report(
    path: Path,
    status: str,
    validation_errors: int,
    coverage_rows: list[dict[str, Any]],
    decision_rows: list[dict[str, Any]],
    next_rows: list[dict[str, Any]],
) -> None:
    main_rows = "relative_vertical, size_relative, relative_horizontal, support_contact"
    lines = [
        "# H002 Route-Coverage Sufficiency Review After Relative-Horizontal Table Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {status}",
        f"selected_path = {SELECTED_PATH}",
        f"validation_errors = {validation_errors}",
        f"next_todo = {NEXT_TODO}",
        "```",
        "",
        "## Decision",
        "",
        "The missing step is no longer family discovery. It is freezing model-safe fields,",
        "split policy, Docker reproduction, calibration boundary, and claim wording.",
        "",
        "Current coverage is sufficient for the H002 hypothesis-stage framework claim,",
        "but not sufficient for all-family generality or paper-level reliability.",
        "",
        "Main mechanism rows:",
        "",
        "```text",
        main_rows,
        "```",
        "",
        "## Coverage Criteria",
        "",
        "| Criterion | Families | Status | Interpretation |",
        "| --- | --- | --- | --- |",
    ]
    for row in coverage_rows:
        lines.append(f"| {row['criterion']} | {row['families']} | {row['status']} | {row['interpretation']} |")
    lines.extend(
        [
            "",
            "## Selected Next Gate",
            "",
            "H002 should not add another relation family before promotion planning.",
            "The next step is to freeze schema and write the promotion protocol.",
            "",
            "| Gate | Purpose | Required Output |",
            "| --- | --- | --- |",
        ]
    )
    for row in next_rows:
        lines.append(f"| {row['next_gate']} | {row['purpose']} | {row['required_output']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Allowed:",
            "",
            "- train-only relation-aware predicate-geometry compatibility routing claim",
            "- main rows for clean, frame-aware, and challenging compatibility routes",
            "- diagnostic/control rows for proximity, supported-by, and attachment-like boundaries",
            "",
            "Blocked:",
            "",
            "- all-family generality",
            "- calibrated `p_rel` / `p_obs`",
            "- held-out/test or paper-level performance",
            "- complete horizontal ontology including `in front of`",
            "- support/contact fully solved",
            "- geometry-only framework claim",
            "",
            "## Next",
            "",
            "```text",
            NEXT_TODO,
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    table_plan_dir = args.table_plan_dir.resolve()
    gap_audit_dir = args.gap_audit_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    table_summary = read_json(table_plan_dir / "summary.json")
    gap_summary = read_json(gap_audit_dir / "summary.json")
    main_table_rows = read_csv(table_plan_dir / "main_table_plan.csv")
    route_rows = read_csv(table_plan_dir / "route_taxonomy_table.csv")
    promotion_rows = read_csv(table_plan_dir / "promotion_gates.csv")
    gap_rows = read_csv(gap_audit_dir / "family_coverage_gap.csv")

    roots = {"table_plan": table_plan_dir, "gap_audit": gap_audit_dir}
    errors = validate_inputs(table_summary, gap_summary, main_table_rows, route_rows, promotion_rows, roots)
    status = STATUS_ERRORS if errors else STATUS_READY

    coverage_rows = coverage_criteria()
    family_rows = updated_family_decisions(route_rows, gap_rows)
    decision_rows = sufficiency_decision()
    next_rows = next_gate_plan()
    risk_rows = reviewer_risks()

    output_paths = {
        "artifact_root": rel_path(output_dir),
        "coverage_criteria": rel_path(output_dir / "coverage_criteria.csv"),
        "family_decisions": rel_path(output_dir / "family_decisions.csv"),
        "sufficiency_decision": rel_path(output_dir / "sufficiency_decision.csv"),
        "next_gate_plan": rel_path(output_dir / "next_gate_plan.csv"),
        "reviewer_risk_matrix": rel_path(output_dir / "reviewer_risk_matrix.csv"),
        "report": rel_path(output_dir / "report.md"),
        "summary": rel_path(output_dir / "summary.json"),
        "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "input_errors_fix_before_sufficiency_decision",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "table_plan": rel_path(table_plan_dir),
            "gap_audit": rel_path(gap_audit_dir),
        },
        "output_paths": output_paths,
        "counts": {
            "coverage_criteria_rows": len(coverage_rows),
            "family_decision_rows": len(family_rows),
            "sufficiency_decision_rows": len(decision_rows),
            "next_gate_rows": len(next_rows),
            "reviewer_risk_rows": len(risk_rows),
            "main_mechanism_families": 4,
        },
        "main_mechanism_families": [
            "relative_vertical",
            "size_relative",
            "relative_horizontal",
            "support_contact",
        ],
        "diagnostic_or_boundary_families": [
            "proximity",
            "support_contact_superordinate",
            "attachment_like",
            "containment_in",
            "part_structural",
            "identity_symmetry",
        ],
        "decision": "route_coverage_sufficient_for_hypothesis_stage_framework_claim",
        "paper_boundary": {
            "all_family_generality_allowed": False,
            "calibrated_p_rel_p_obs_allowed": False,
            "complete_horizontal_ontology_allowed": False,
            "held_out_or_test_claim_allowed": False,
            "paper_evidence_allowed_now": False,
            "support_contact_solved_claim_allowed": False,
        },
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
    }

    write_csv(output_dir / "coverage_criteria.csv", coverage_rows)
    write_csv(output_dir / "family_decisions.csv", family_rows)
    write_csv(output_dir / "sufficiency_decision.csv", decision_rows)
    write_csv(output_dir / "next_gate_plan.csv", next_rows)
    write_csv(output_dir / "reviewer_risk_matrix.csv", risk_rows)
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", status, len(errors), coverage_rows, decision_rows, next_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
