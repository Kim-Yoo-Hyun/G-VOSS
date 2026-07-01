#!/usr/bin/env python3
"""Create the H002 ablation/table plan after multi-family claim synthesis."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SYNTHESIS_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview"
)
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis"

EXPECTED_SYNTHESIS_STATUS = (
    "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview_ready"
)
EXPECTED_SYNTHESIS_NEXT = "compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis_v1"
STATUS_READY = "h002_compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis_input_errors"
SELECTED_PATH = "freeze_candidate_ablation_contract_select_relation_family_coverage_gap_audit"
NEXT_TODO = "compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthesis-dir", type=Path, default=DEFAULT_SYNTHESIS_DIR)
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
    summary: dict[str, Any],
    claim_skeleton: dict[str, Any],
    family_routes: list[dict[str, str]],
    evidence_rows: list[dict[str, str]],
    next_contract: dict[str, Any],
    synthesis_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_SYNTHESIS_STATUS:
        errors.append({"error_type": "unexpected_synthesis_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_SYNTHESIS_NEXT:
        errors.append({"error_type": "unexpected_synthesis_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "synthesis_validation_errors_present", "actual": summary.get("validation_errors")})
    validation_rows = read_jsonl(synthesis_dir / "validation_errors.jsonl")
    if validation_rows:
        errors.append({"error_type": "synthesis_validation_error_rows_present", "rows": len(validation_rows)})
    boundary = summary.get("boundary", {})
    for key in ["h001_artifacts_modified", "paper_evidence_allowed", "runs_new_learned_smoke", "test_usage", "validation_usage"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("split") != "train_only_claim_synthesis":
        errors.append({"error_type": "unexpected_split", "actual": boundary.get("split")})
    if claim_skeleton.get("short_claim") != "relation-aware predicate-geometry compatibility routing":
        errors.append({"error_type": "unexpected_short_claim", "actual": claim_skeleton.get("short_claim")})
    route_by_family = {row.get("family"): row for row in family_routes}
    for family in ["relative_vertical", "support_contact", "proximity", "attachment_like", "relative_horizontal"]:
        if family not in route_by_family:
            errors.append({"error_type": "missing_family_route", "family": family})
    evidence_by_family = {row.get("family"): row for row in evidence_rows}
    if evidence_by_family.get("relative_vertical", {}).get("paper_role") != "main mechanism evidence":
        errors.append({"error_type": "relative_vertical_role_not_main", "row": evidence_by_family.get("relative_vertical")})
    if evidence_by_family.get("support_contact", {}).get("paper_role") != "main route evidence with caveat":
        errors.append({"error_type": "support_contact_role_not_caveated_main", "row": evidence_by_family.get("support_contact")})
    required_contract_items = {
        "main mechanism table rows",
        "diagnostic route table rows",
        "semantic-only, geometry-only, concat, interaction, wrong-T, shuffled-G controls",
        "Q_e/p_obs table position",
        "paper-level held-out/Docker promotion gates",
        "forbidden wording and caveat wording",
    }
    missing_contract = required_contract_items - set(next_contract.get("must_define", []))
    if missing_contract:
        errors.append({"error_type": "next_contract_missing_items", "missing": sorted(missing_contract)})
    return errors


def main_table_plan(evidence_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    evidence_by_family = {row.get("family"): row for row in evidence_rows}
    relative = evidence_by_family.get("relative_vertical", {})
    support = evidence_by_family.get("support_contact", {})
    proximity = evidence_by_family.get("proximity", {})
    attachment = evidence_by_family.get("attachment_like", {})
    return [
        {
            "table_id": "T1",
            "table_name": "Candidate Predicate-Geometry Compatibility Mechanism",
            "paper_position": "candidate_main_after_more_family_coverage",
            "rows": "relative_vertical; support_contact",
            "required_columns": "family; predicates; route; semantic_only; geometry_only; concat; interaction_Ce; wrong_T; shuffled_G; role; caveat",
            "primary_message": "plain semantic/geometry concatenation is insufficient; predicate-geometry interaction is the key evidence.",
            "source_artifacts": "evidence_table.csv; support/contact smoke; relative_vertical v3 smoke",
            "include_now": "yes_hypothesis_contract_not_final_main_table",
            "paper_promotion_requirement": "relation-family coverage audit, then Docker reproduction, grouped held-out split, bootstrap/CI, frozen model-safe schema",
            "relative_vertical_signal": relative.get("primary_signal"),
            "support_contact_signal": support.get("primary_signal"),
        },
        {
            "table_id": "T2",
            "table_name": "Relation-Aware Evidence Routing Taxonomy",
            "paper_position": "required_before_final_main_table",
            "rows": "relative_vertical; support_contact; supported_by; proximity; attachment_like; relative_horizontal",
            "required_columns": "family; predicates; route_type; required_evidence; p_obs_role; decision; risk",
            "primary_message": "different relation families require different evidence routes rather than one fixed fusion formula.",
            "source_artifacts": "family_route_table.csv",
            "include_now": "yes_hypothesis_contract",
            "paper_promotion_requirement": "complete remaining relation-family coverage/gap audit before Docker experiment",
            "relative_vertical_signal": "clean_Ce_anchor",
            "support_contact_signal": "challenging_Ce_route_with_caveat",
        },
        {
            "table_id": "T3",
            "table_name": "Geometry-Easy and Observability-Heavy Diagnostics",
            "paper_position": "appendix_or_analysis",
            "rows": "close by; attached to; hanging on; connected to; supported by",
            "required_columns": "family; predicate; diagnostic_finding; why_not_main; future_requirement",
            "primary_message": "close by is a geometry-easy control, while attachment-like relations require visual/mesh observability before learned compatibility claims.",
            "source_artifacts": "proximity path decision; attachment diagnostic freeze; support superordinate diagnostics",
            "include_now": "yes_diagnostic_only",
            "paper_promotion_requirement": "do not use as main performance table without independent target and controls",
            "relative_vertical_signal": "",
            "support_contact_signal": "",
            "proximity_signal": proximity.get("primary_signal"),
            "attachment_signal": attachment.get("primary_signal"),
        },
        {
            "table_id": "T4",
            "table_name": "Claim Boundary and Reviewer Risk",
            "paper_position": "appendix_or_rebuttal_asset",
            "rows": "blocked claims; caveat wording; promotion gates",
            "required_columns": "risk; severity; paper_wording; required_artifact",
            "primary_message": "H002 is currently a train-only mechanism hypothesis, not a paper-level held-out reliability result.",
            "source_artifacts": "reviewer_risk_table.csv; promotion_gates.csv",
            "include_now": "yes_internal_then_appendix_if_needed",
            "paper_promotion_requirement": "convert risks into explicit limitations and controls",
            "relative_vertical_signal": "",
            "support_contact_signal": "",
        },
    ]


def ablation_matrix() -> list[dict[str, Any]]:
    return [
        {
            "ablation_id": "A0",
            "name": "constant_or_label_prior",
            "inputs": "none",
            "tests": "target class balance and grouped split sanity",
            "expected_role": "floor baseline",
            "main_or_control": "control",
            "fail_if": "near main method performance",
        },
        {
            "ablation_id": "A1",
            "name": "T_e semantic content only",
            "inputs": "predicate text/label; subject/object classes",
            "tests": "whether semantic labels alone solve compatibility",
            "expected_role": "semantic-only baseline",
            "main_or_control": "baseline",
            "fail_if": "matches interaction under controlled splits",
        },
        {
            "ablation_id": "A2",
            "name": "Z_e source confidence only",
            "inputs": "source score; rank; source id if available",
            "tests": "source-prior shortcut",
            "expected_role": "source-confidence baseline, excluded from C_e",
            "main_or_control": "baseline/control",
            "fail_if": "dominates C_e target or leaks construction policy",
        },
        {
            "ablation_id": "A3",
            "name": "G_e geometry-only",
            "inputs": "predicate-independent geometry evidence",
            "tests": "whether geometry alone decides the target",
            "expected_role": "geometry-only baseline",
            "main_or_control": "baseline",
            "fail_if": "main compatibility target is solved by distance/contact alone except geometry-easy diagnostics",
        },
        {
            "ablation_id": "A4",
            "name": "T_e + G_e plain concat",
            "inputs": "semantic content and geometry features by concatenation",
            "tests": "whether simple fusion is enough",
            "expected_role": "critical baseline",
            "main_or_control": "baseline",
            "fail_if": "same performance as interaction model",
        },
        {
            "ablation_id": "A5",
            "name": "C_e predicate-geometry interaction",
            "inputs": "T_e x G_e interaction without Z_e",
            "tests": "core compatibility mechanism",
            "expected_role": "main mechanism model",
            "main_or_control": "main",
            "fail_if": "does not beat T-only, G-only, and concat or controls do not collapse",
        },
        {
            "ablation_id": "A6",
            "name": "C_e + Q_e selective decision",
            "inputs": "compatibility plus observability/evidence-quality",
            "tests": "p_obs and abstain behavior",
            "expected_role": "selective reliability extension, not truth label",
            "main_or_control": "secondary",
            "fail_if": "Q_e acts as relation truth or shuffled-Q gives same interpretation",
        },
        {
            "ablation_id": "A7",
            "name": "C_e + Q_e + Z_e final p_rel",
            "inputs": "compatibility, observability, and source confidence",
            "tests": "final reliability head after C_e is established",
            "expected_role": "later p_rel model, not current main mechanism",
            "main_or_control": "future/promotion",
            "fail_if": "source score copies labels or hides C_e contribution",
        },
        {
            "ablation_id": "A8",
            "name": "fixed fusion without route",
            "inputs": "same factor formula for every relation family",
            "tests": "need for relation-aware routing",
            "expected_role": "method simplification ablation",
            "main_or_control": "ablation",
            "fail_if": "route-aware version does not explain close-by/support/attachment differences",
        },
    ]


def control_matrix() -> list[dict[str, Any]]:
    return [
        {
            "control_id": "C1",
            "name": "wrong predicate same geometry",
            "applies_to": "relative_vertical; support_contact",
            "question": "does the model need the correct predicate semantics?",
            "expected": "performance collapses",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C2",
            "name": "shuffled geometry global",
            "applies_to": "relative_vertical; support_contact",
            "question": "does the model rely on matched geometry?",
            "expected": "near chance or clear degradation",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C3",
            "name": "shuffled geometry within predicate/family",
            "applies_to": "relative_vertical; support_contact",
            "question": "does the model exploit generic predicate priors?",
            "expected": "clear degradation",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C4",
            "name": "class-pair only",
            "applies_to": "all learned targets",
            "question": "can object class pairs reconstruct labels?",
            "expected": "below main interaction and reported as shortcut probe",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C5",
            "name": "source/rank only",
            "applies_to": "all learned targets",
            "question": "does source confidence determine the target?",
            "expected": "weak for C_e, optionally useful only for final p_rel",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C6",
            "name": "distance or p_geom_valid only",
            "applies_to": "proximity; support_contact; relative_vertical",
            "question": "is this just a geometry rule verifier?",
            "expected": "proximity can be solved; support_contact should not; relative_vertical is a geometry-control route",
            "blocks_promotion_if_fail": False,
        },
        {
            "control_id": "C7",
            "name": "Q_e shuffled or Q_e only",
            "applies_to": "p_obs and selective decision",
            "question": "is observability being used as truth?",
            "expected": "Q_e helps abstain/coverage, not C_e truth",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C8",
            "name": "scan and endpoint leakage",
            "applies_to": "all train/held-out splits",
            "question": "does the split memorize scene or object pair identifiers?",
            "expected": "grouped split by scan/endpoint; ids excluded from model view",
            "blocks_promotion_if_fail": True,
        },
    ]


def promotion_gates() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "G1",
            "gate": "schema freeze",
            "requirement": "model-safe fields, hidden/audit fields, label fields, and construction fields are separated before any run",
            "minimum_evidence": "schema leakage audit with zero model-visible blocked fields",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G2",
            "gate": "Docker reproduction",
            "requirement": "paper-level H002 experiments run from Docker/compose with pinned dependencies and manifest",
            "minimum_evidence": "command log, output manifest, validation_errors=0",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G3",
            "gate": "grouped held-out evaluation",
            "requirement": "scan and endpoint-pair grouped split; no validation/test leakage in target construction",
            "minimum_evidence": "held-out table and split manifest",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G4",
            "gate": "core C_e ablation",
            "requirement": "interaction model beats T-only, G-only, Z-only, and plain T+G concat on main learned routes",
            "minimum_evidence": "relative_vertical and support_contact ablation table with CI/bootstrap",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G5",
            "gate": "counterfactual controls",
            "requirement": "wrong-T and shuffled-G controls degrade relative to matched T/G",
            "minimum_evidence": "control matrix with paired deltas and failure rows",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G6",
            "gate": "route taxonomy boundary",
            "requirement": "geometry-easy, compatibility-heavy, observability-heavy, and deferred families are explicitly separated",
            "minimum_evidence": "route table plus caveat wording",
            "blocks_paper_promotion": False,
        },
        {
            "gate_id": "G7",
            "gate": "Q_e/p_obs separation",
            "requirement": "Q_e is evaluated as observability/selective-decision evidence, not relation truth",
            "minimum_evidence": "Q_e-only/shuffled-Q control and abstain metric",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G8",
            "gate": "claim wording lock",
            "requirement": "do not claim paper-level reliability, all-family generality, or solved support/contact until gates pass",
            "minimum_evidence": "reviewer-risk table and paper wording checklist",
            "blocks_paper_promotion": True,
        },
    ]


def reviewer_response_plan() -> list[dict[str, Any]]:
    return [
        {
            "reviewer_question": "Is this just concatenating semantic and geometry features?",
            "answer": "No. Plain T_e+G_e concat is a critical baseline and currently fails where interaction succeeds. The claim depends on wrong-T and shuffled-G controls collapsing.",
            "required_table": "T1; ablation_matrix A4/A5; controls C1-C3",
        },
        {
            "reviewer_question": "Why not all 3DSSG relation types?",
            "answer": "The method is relation-aware: only geometry-relevant families should use geometry compatibility. Ontology-like or reference-frame-dependent relations are routed to diagnostic/deferred states.",
            "required_table": "T2 relation route taxonomy",
        },
        {
            "reviewer_question": "Support/contact AUROC is only near 0.70. Is that strong enough?",
            "answer": "Do not claim solved support/contact. Use it as challenging route evidence: interaction is the only condition that improves over semantic-only, geometry-only, and concat while controls collapse.",
            "required_table": "T1 support_contact row; failure analysis appendix",
        },
        {
            "reviewer_question": "Is close by just a distance threshold?",
            "answer": "Yes under the current target, so close by is not the main C_e proof. It is a geometry-easy control showing why route-specific factor usage is necessary.",
            "required_table": "T2/T3 proximity row",
        },
        {
            "reviewer_question": "Does Q_e leak the answer?",
            "answer": "Q_e is not a truth label. It is used for p_obs/abstain and must be validated with Q_e-only and shuffled-Q controls.",
            "required_table": "A6; controls C7; promotion gate G7",
        },
        {
            "reviewer_question": "Why is this not paper evidence yet?",
            "answer": "Current artifacts are train-only hypothesis evidence. Paper-level claims require Docker reproduction, held-out grouped evaluation, frozen schema, and CI.",
            "required_table": "promotion_gates G1-G8",
        },
    ]


def forbidden_wording() -> list[dict[str, str]]:
    return [
        {
            "forbidden": "H002 solves relation reliability for 3D scene graphs.",
            "replacement": "H002 provides a train-only mechanism and route plan for predicate-geometry compatibility learning.",
        },
        {
            "forbidden": "support/contact is solved.",
            "replacement": "support/contact provides challenging compatibility-route evidence with caveat.",
        },
        {
            "forbidden": "Q_e predicts relation truth.",
            "replacement": "Q_e estimates observability and supports abstention/selective decision.",
        },
        {
            "forbidden": "close by proves the learned compatibility model.",
            "replacement": "close by is a geometry-easy diagnostic/generalization control under the current target.",
        },
        {
            "forbidden": "all relation families are covered.",
            "replacement": "the current route taxonomy separates main, diagnostic, future, and deferred relation families.",
        },
    ]


def write_table_spec(path: Path) -> None:
    text = """# H002 Ablation And Table Plan

## Purpose

This artifact converts the frozen multi-family claim skeleton into a candidate paper-table
and ablation contract. It does not define the final main table, does not run a new learned
model, and does not promote H002 to paper-level evidence.

## Important Boundary

This is not the final main table. H002 still needs a relation-family coverage/gap audit
before Docker promotion, because many Open3DSG/3DSSG relation types are not yet covered by
the current geometry-checkable queue or require new evidence schemas/source adapters.

## Candidate Tables

1. `T1 Predicate-Geometry Compatibility Mechanism`
   - Candidate rows: `relative_vertical`, `support_contact`
   - Required comparisons: semantic-only, source-only, geometry-only, plain concat,
     interaction `C_e`, wrong-T, shuffled-G
   - Claim: interaction is necessary; fixed concatenation is not enough.

2. `T2 Relation-Aware Evidence Routing Taxonomy`
   - Main/diagnostic/future/deferred route table.
   - Claim: relation reliability needs route-specific evidence use.

3. `T3 Geometry-Easy and Observability-Heavy Diagnostics`
   - `close by` as geometry-easy control.
   - `attached to`, `hanging on`, `connected to` as observability-heavy future/diagnostic.

4. `T4 Claim Boundary and Reviewer Risk`
   - Blocked claims, caveat wording, and promotion requirements.

## Required Ablations

- `T_e` only
- `Z_e` only
- `G_e` only
- `T_e + G_e` plain concat
- `C_e = interaction(T_e, G_e)` without `Z_e`
- `C_e + Q_e` selective decision
- `C_e + Q_e + Z_e` final `p_rel` only after mechanism is established
- fixed-fusion without relation-aware route

## Required Controls

- wrong-predicate same geometry
- shuffled geometry global
- shuffled geometry within predicate/family
- class-pair only
- source/rank only
- distance or `p_geom_valid` only
- `Q_e` shuffled or `Q_e` only
- scan/endpoint leakage control

## Promotion Boundary

H002 remains hypothesis-stage until relation-family coverage/gap audit, Docker reproduction,
frozen schema, grouped held-out evaluation, and control/CI artifacts are complete.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# H002 Ablation And Table Plan After Multi-Family Synthesis

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Decision

The current H002 claim has been converted into candidate table and ablation requirements.
This is not the final main table. Before Docker promotion, H002 must audit remaining
relation families and decide which are main, diagnostic, future, or out-of-scope.

Current short claim:

```text
relation-aware predicate-geometry compatibility routing
```

## Candidate Table Plan

- `T1`: predicate-geometry compatibility mechanism candidate table for `relative_vertical` and
  `support_contact`.
- `T2`: relation-aware evidence routing taxonomy.
- `T3`: geometry-easy and observability-heavy diagnostics.
- `T4`: claim boundary and reviewer-risk table.

## Required Ablations

The core comparison is:

```text
T_e only
Z_e only
G_e only
T_e + G_e concat
C_e interaction(T_e, G_e)
C_e + Q_e selective decision
C_e + Q_e + Z_e final p_rel
fixed fusion without route
```

`C_e` must exclude `Z_e`; otherwise the compatibility head can copy source confidence.

## Required Controls

Wrong-T, shuffled-G, class-pair-only, source/rank-only, distance/`p_geom_valid`-only,
Q-shuffle, and scan/endpoint leakage controls are mandatory before paper promotion.

## Claim Boundary

Still blocked:

- paper-level performance
- held-out/test relation reliability
- all relation-family generality
- support/contact fully solved
- `Q_e` as relation truth
- final calibrated `p_rel`/`p_obs` result

## Next

```text
{summary['next_todo']}
```
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    summary_in = read_json(args.synthesis_dir / "summary.json")
    claim = read_json(args.synthesis_dir / "claim_skeleton.json")
    family_routes = read_csv(args.synthesis_dir / "family_route_table.csv")
    evidence_rows = read_csv(args.synthesis_dir / "evidence_table.csv")
    reviewer_risks = read_csv(args.synthesis_dir / "reviewer_risk_table.csv")
    next_contract = read_json(args.synthesis_dir / "next_plan_contract.json")

    validation_errors = validate_inputs(
        summary_in,
        claim,
        family_routes,
        evidence_rows,
        next_contract,
        args.synthesis_dir,
    )
    status = STATUS_READY if not validation_errors else STATUS_ERRORS

    outputs = {
        "main_table_plan": args.output_dir / "main_table_plan.csv",
        "ablation_matrix": args.output_dir / "ablation_matrix.csv",
        "control_matrix": args.output_dir / "control_matrix.csv",
        "promotion_gates": args.output_dir / "promotion_gates.csv",
        "reviewer_response_plan": args.output_dir / "reviewer_response_plan.csv",
        "forbidden_wording": args.output_dir / "forbidden_wording.csv",
        "table_spec": args.output_dir / "table_spec.md",
        "report": args.output_dir / "report.md",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }

    main_tables = main_table_plan(evidence_rows)
    ablations = ablation_matrix()
    controls = control_matrix()
    gates = promotion_gates()
    reviewer_plan = reviewer_response_plan()
    wording = forbidden_wording()

    if len(main_tables) < 4:
        validation_errors.append({"error_type": "main_table_plan_too_short", "rows": len(main_tables)})
    if not any(row.get("name") == "T_e + G_e plain concat" for row in ablations):
        validation_errors.append({"error_type": "missing_plain_concat_ablation"})
    if not any(row.get("name") == "C_e predicate-geometry interaction" for row in ablations):
        validation_errors.append({"error_type": "missing_interaction_ablation"})
    if not any(row.get("name") == "wrong predicate same geometry" for row in controls):
        validation_errors.append({"error_type": "missing_wrong_t_control"})
    if not any(row.get("gate") == "Docker reproduction" for row in gates):
        validation_errors.append({"error_type": "missing_docker_gate"})
    if validation_errors:
        status = STATUS_ERRORS

    summary_out = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "synthesis": rel_path(args.synthesis_dir),
        },
        "output_paths": {key: rel_path(value) for key, value in outputs.items()},
        "boundary": {
            "split": "train_only_plan_artifact",
            "h001_artifacts_modified": False,
            "trains_new_model": False,
            "runs_new_learned_smoke": False,
            "paper_evidence_allowed": False,
            "validation_usage": False,
            "test_usage": False,
        },
        "claim": {
            "short_claim": "relation-aware predicate-geometry compatibility routing",
            "working_title": claim.get("working_title"),
            "allowed_now": "hypothesis-stage table and ablation contract",
            "blocked": claim.get("blocked_claims", []),
        },
        "counts": {
            "main_table_rows": len(main_tables),
            "ablation_rows": len(ablations),
            "control_rows": len(controls),
            "promotion_gate_rows": len(gates),
            "reviewer_response_rows": len(reviewer_plan),
            "forbidden_wording_rows": len(wording),
            "input_reviewer_risk_rows": len(reviewer_risks),
        },
    }

    write_csv(outputs["main_table_plan"], main_tables)
    write_csv(outputs["ablation_matrix"], ablations)
    write_csv(outputs["control_matrix"], controls)
    write_csv(outputs["promotion_gates"], gates)
    write_csv(outputs["reviewer_response_plan"], reviewer_plan)
    write_csv(outputs["forbidden_wording"], wording)
    write_table_spec(outputs["table_spec"])
    write_report(outputs["report"], summary_out)
    write_json(outputs["summary"], summary_out)
    write_jsonl(outputs["validation_errors"], validation_errors)

    print(json.dumps(summary_out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
