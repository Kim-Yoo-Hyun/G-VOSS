#!/usr/bin/env python3
"""Update H002 ablation/table plan after adding relative-horizontal synthesis."""

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
    H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis"
)

EXPECTED_SYNTHESIS_STATUS = "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_relative_horizontal_ready"
EXPECTED_SYNTHESIS_NEXT = "compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis_v1"
STATUS_READY = "h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_ablation_and_table_plan_update_after_relative_horizontal_synthesis_input_errors"
SELECTED_PATH = "freeze_relative_horizontal_aware_table_contract_select_route_coverage_sufficiency_review"
NEXT_TODO = "compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan"


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
    claim: dict[str, Any],
    evidence: list[dict[str, str]],
    family_routes: list[dict[str, str]],
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
    for key in [
        "h001_artifacts_modified",
        "paper_evidence_allowed",
        "runs_new_learned_smoke",
        "test_usage",
        "trains_new_model",
        "validation_usage",
        "complete_horizontal_ontology_claim_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("split") != "train_only_claim_synthesis":
        errors.append({"error_type": "unexpected_split", "actual": boundary.get("split")})
    if claim.get("short_claim") != "relation-aware predicate-geometry compatibility routing":
        errors.append({"error_type": "unexpected_short_claim", "actual": claim.get("short_claim")})

    evidence_by_family = {row.get("family"): row for row in evidence}
    for family in ["relative_vertical", "size_relative", "relative_horizontal", "support_contact", "proximity", "attachment_like"]:
        if family not in evidence_by_family:
            errors.append({"error_type": "missing_evidence_family", "family": family})
    if evidence_by_family.get("relative_horizontal", {}).get("paper_role") != "main mechanism evidence with reference-frame caveat":
        errors.append({"error_type": "relative_horizontal_role_not_updated", "row": evidence_by_family.get("relative_horizontal")})
    if "frame-aware" not in evidence_by_family.get("relative_horizontal", {}).get("route_type", ""):
        errors.append({"error_type": "relative_horizontal_not_frame_aware", "row": evidence_by_family.get("relative_horizontal")})

    route_by_family = {row.get("family"): row for row in family_routes}
    for family in [
        "relative_vertical",
        "size_relative",
        "relative_horizontal",
        "support_contact",
        "support_contact_superordinate",
        "proximity",
        "attachment_like",
    ]:
        if family not in route_by_family:
            errors.append({"error_type": "missing_family_route", "family": family})
    if route_by_family.get("relative_horizontal", {}).get("use_in_claim") != "main_with_reference_frame_caveat":
        errors.append({"error_type": "relative_horizontal_route_not_main_with_caveat", "row": route_by_family.get("relative_horizontal")})

    required_items = {
        "relative_vertical clean compatibility row",
        "size_relative clean compatibility row",
        "relative_horizontal frame-aware compatibility row",
        "support_contact challenging compatibility row with caveat",
        "proximity geometry-easy diagnostic/control row",
        "attachment_like observability-heavy deferred row",
        "wrong-frame and endpoint-swap controls for relative_horizontal",
        "calibration caveat for high-AUROC but high-ECE smoke results",
    }
    missing = required_items - set(next_contract.get("must_include", []))
    if missing:
        errors.append({"error_type": "next_contract_missing_required_items", "missing": sorted(missing)})
    return errors


def family_metric(evidence: dict[str, dict[str, str]], family: str, key: str) -> str:
    return evidence.get(family, {}).get(key, "")


def main_table_plan(evidence_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    evidence = {row["family"]: row for row in evidence_rows}
    return [
        {
            "table_id": "T1",
            "table_name": "Predicate-Geometry Compatibility Mechanism",
            "table_status": "candidate_main_mechanism_table",
            "rows": "relative_vertical; size_relative; relative_horizontal; support_contact",
            "required_columns": (
                "family; predicates; semantic_only; geometry_only; concat; interaction_Ce; wrong_T; "
                "shuffled_G; sign_flip_if_available; wrong_frame_if_applicable; endpoint_swap_if_applicable; caveat"
            ),
            "primary_message": "explicit T_e x G_e compatibility is needed; T-only, G-only, and plain concat are insufficient on main mechanism routes",
            "relative_vertical_signal": family_metric(evidence, "relative_vertical", "primary_signal"),
            "size_relative_signal": family_metric(evidence, "size_relative", "primary_signal"),
            "relative_horizontal_signal": family_metric(evidence, "relative_horizontal", "primary_signal"),
            "support_contact_signal": family_metric(evidence, "support_contact", "primary_signal"),
            "paper_promotion_requirement": "Docker reproduction, held-out grouped split, CI/bootstrap, and frozen schema",
        },
        {
            "table_id": "T2",
            "table_name": "Relation-Aware Evidence Routing Taxonomy",
            "table_status": "required_framework_table",
            "rows": "relative_vertical; size_relative; relative_horizontal; support_contact; supported_by; close_by; attachment_like",
            "required_columns": "family; predicates; route; evidence_route; p_obs_role; use_in_claim; decision; risk",
            "primary_message": "relation families require different evidence routes rather than a universal fixed fusion formula",
            "relative_vertical_signal": "clean_sign_Ce_route",
            "size_relative_signal": "clean_size_Ce_route_with_calibration_caveat",
            "relative_horizontal_signal": "frame_aware_directional_Ce_route",
            "support_contact_signal": "challenging_Ce_route_with_caveat",
            "paper_promotion_requirement": "coverage sufficiency review before final main-table lock",
        },
        {
            "table_id": "T3",
            "table_name": "Diagnostic Boundary Cases",
            "table_status": "analysis_or_appendix",
            "rows": "close by; supported by; attached to; hanging on; connected to; in front of",
            "required_columns": "family; predicate; diagnostic_finding; why_not_main; future_requirement",
            "primary_message": "some relations are geometry-easy, superordinate, observability-heavy, absent, or reference-frame dependent",
            "relative_vertical_signal": "",
            "size_relative_signal": "",
            "relative_horizontal_signal": "in_front_of_absent; frame controls required",
            "support_contact_signal": "supported_by_superordinate_deferred",
            "paper_promotion_requirement": "do not count as main learned compatibility result unless target/evidence gates pass",
        },
        {
            "table_id": "T4",
            "table_name": "Calibration and Claim Boundary",
            "table_status": "reviewer_defense_table",
            "rows": "blocked claims; calibration caveat; horizontal ontology caveat; promotion gates; forbidden wording",
            "required_columns": "claim_or_risk; allowed; caveat; required_artifact",
            "primary_message": "high AUROC mechanism results are not calibrated p_rel/p_obs or paper-level reliability claims",
            "relative_vertical_signal": "not_final_reliability",
            "size_relative_signal": "ECE_caveat",
            "relative_horizontal_signal": "ECE_and_frame_caveat",
            "support_contact_signal": "near_threshold_caveat",
            "paper_promotion_requirement": "explicit wording lock, calibration protocol, and horizontal coverage boundary",
        },
    ]


def route_taxonomy_table(family_routes: list[dict[str, str]]) -> list[dict[str, Any]]:
    role_order = {
        "relative_vertical": 1,
        "size_relative": 2,
        "relative_horizontal": 3,
        "support_contact": 4,
        "proximity": 5,
        "support_contact_superordinate": 6,
        "attachment_like": 7,
    }
    rows = [dict(row) for row in family_routes]
    rows.sort(key=lambda row: role_order.get(row.get("family", ""), 99))
    return rows


def ablation_matrix() -> list[dict[str, Any]]:
    return [
        {
            "ablation_id": "A0",
            "name": "constant_or_label_prior",
            "inputs": "none",
            "applies_to": "all targets",
            "tests": "class balance and grouped split sanity",
            "expected": "floor baseline",
            "promotion_gate": "must stay near chance",
        },
        {
            "ablation_id": "A1",
            "name": "T_e semantic content only",
            "inputs": "predicate and object semantic content",
            "applies_to": "relative_vertical; size_relative; relative_horizontal; support_contact",
            "tests": "semantic shortcut",
            "expected": "below C_e interaction",
            "promotion_gate": "blocks if it matches C_e",
        },
        {
            "ablation_id": "A2",
            "name": "Z_e source confidence only",
            "inputs": "source score/rank/source id where available",
            "applies_to": "C_e target audit and later p_rel",
            "tests": "source-confidence shortcut",
            "expected": "excluded from C_e, optional for later p_rel",
            "promotion_gate": "blocks C_e if it predicts compatibility",
        },
        {
            "ablation_id": "A3",
            "name": "G_e geometry-only",
            "inputs": "predicate-independent geometry evidence",
            "applies_to": "relative_vertical; size_relative; relative_horizontal; support_contact; proximity diagnostic",
            "tests": "geometry-only verifier risk",
            "expected": "main C_e routes should not be solved by G_e alone; proximity may be geometry-easy",
            "promotion_gate": "blocks if main C_e route is merely a geometry rule",
        },
        {
            "ablation_id": "A4",
            "name": "T_e + G_e plain concat",
            "inputs": "semantic content and geometry by no-interaction concatenation",
            "applies_to": "relative_vertical; size_relative; relative_horizontal; support_contact",
            "tests": "fixed fusion baseline",
            "expected": "below interaction C_e",
            "promotion_gate": "blocks if plain concat matches interaction",
        },
        {
            "ablation_id": "A5",
            "name": "C_e predicate-geometry interaction",
            "inputs": "interaction(T_e, G_e), excluding Z_e",
            "applies_to": "relative_vertical; size_relative; relative_horizontal; support_contact",
            "tests": "main compatibility mechanism",
            "expected": "best main mechanism model with controls passing",
            "promotion_gate": "must beat A1/A3/A4 and degrade under controls",
        },
        {
            "ablation_id": "A6",
            "name": "C_e + Q_e selective decision",
            "inputs": "compatibility plus observability/evidence quality",
            "applies_to": "support_contact; attachment_like future; relative_horizontal axis-boundary diagnostics; p_obs",
            "tests": "observability and abstain behavior",
            "expected": "helps decide when to abstain, not relation truth",
            "promotion_gate": "blocks if Q_e becomes truth leakage",
        },
        {
            "ablation_id": "A7",
            "name": "C_e + Q_e + Z_e final p_rel",
            "inputs": "compatibility, observability, and source confidence",
            "applies_to": "future reliability posterior",
            "tests": "final reliability head after C_e is established",
            "expected": "future/promotion stage only",
            "promotion_gate": "not current main result",
        },
        {
            "ablation_id": "A8",
            "name": "fixed fusion without relation route",
            "inputs": "same factor formula for every relation family",
            "applies_to": "all family routes",
            "tests": "need for relation-aware routing",
            "expected": "should fail to explain close-by/support/attachment/horizontal differences",
            "promotion_gate": "must be weaker or less explanatory than route-aware design",
        },
        {
            "ablation_id": "A9",
            "name": "calibrated probability head",
            "inputs": "C_e and optional Q_e/Z_e with calibration objective",
            "applies_to": "future p_rel/p_obs",
            "tests": "whether high AUROC becomes calibrated probability",
            "expected": "future only; current clean-route ECE blocks calibration claim",
            "promotion_gate": "requires separate calibration protocol",
        },
    ]


def control_matrix() -> list[dict[str, Any]]:
    return [
        {
            "control_id": "C1",
            "name": "wrong predicate same geometry",
            "applies_to": "relative_vertical; size_relative; relative_horizontal; support_contact",
            "question": "does C_e require correct predicate semantics?",
            "expected": "collapse or inversion",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C2",
            "name": "shuffled geometry global",
            "applies_to": "relative_vertical; size_relative; relative_horizontal; support_contact",
            "question": "does C_e rely on matched object-pair geometry?",
            "expected": "near chance or clear degradation",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C3",
            "name": "shuffled geometry within predicate/family",
            "applies_to": "relative_vertical; size_relative; relative_horizontal; support_contact",
            "question": "does C_e exploit generic predicate priors?",
            "expected": "clear degradation",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C4",
            "name": "sign-flipped geometry",
            "applies_to": "relative_vertical; size_relative; relative_horizontal",
            "question": "does C_e use the direction/sign of geometry evidence?",
            "expected": "collapse or inversion",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C5",
            "name": "wrong-frame xy swap",
            "applies_to": "relative_horizontal",
            "question": "does horizontal C_e depend on the frozen reference-frame route?",
            "expected": "clear degradation",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C6",
            "name": "subject/object endpoint swap",
            "applies_to": "relative_horizontal; directional relations where endpoint order matters",
            "question": "does C_e respect directed relation endpoints?",
            "expected": "collapse or inversion",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C7",
            "name": "class-pair only",
            "applies_to": "all learned targets",
            "question": "can object class pairs reconstruct labels?",
            "expected": "below C_e interaction and reported as shortcut probe",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C8",
            "name": "source/rank only",
            "applies_to": "all learned targets",
            "question": "does source confidence determine the target?",
            "expected": "weak for C_e; allowed only as separate Z_e in later p_rel",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C9",
            "name": "distance or p_geom_valid only",
            "applies_to": "proximity; support_contact; size_relative; relative_vertical; relative_horizontal",
            "question": "is this just a geometry rule verifier?",
            "expected": "proximity may pass; clean C_e routes require T_e x G_e; support_contact should not be solved by raw G_e",
            "blocks_promotion_if_fail": False,
        },
        {
            "control_id": "C10",
            "name": "Q_e shuffled or Q_e only",
            "applies_to": "p_obs and selective decision",
            "question": "is observability being used as truth?",
            "expected": "Q_e supports abstain/coverage, not C_e truth",
            "blocks_promotion_if_fail": True,
        },
        {
            "control_id": "C11",
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
            "requirement": "model-safe, hidden/audit, label, and construction fields are separated before any run",
            "minimum_evidence": "schema leakage audit with zero model-visible blocked fields",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G2",
            "gate": "route coverage sufficiency review",
            "requirement": "decide whether current main/diagnostic/deferred family coverage is enough or another family is required",
            "minimum_evidence": "coverage sufficiency artifact after this table update",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G3",
            "gate": "Docker reproduction",
            "requirement": "paper-level H002 experiments run from Docker/compose with pinned dependencies and manifest",
            "minimum_evidence": "command log, output manifest, validation_errors=0",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G4",
            "gate": "grouped held-out evaluation",
            "requirement": "scan and endpoint-pair grouped split; no validation/test leakage in target construction",
            "minimum_evidence": "held-out table and split manifest",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G5",
            "gate": "core C_e ablation",
            "requirement": "interaction model beats T-only, G-only, Z-only, and plain T+G concat on main learned routes",
            "minimum_evidence": "relative_vertical, size_relative, relative_horizontal, and support_contact ablation table with CI/bootstrap",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G6",
            "gate": "counterfactual controls",
            "requirement": "wrong-T, shuffled-G, sign-flip, wrong-frame, and endpoint-swap where applicable degrade relative to matched T/G",
            "minimum_evidence": "control matrix with paired deltas and failure rows",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G7",
            "gate": "calibration boundary",
            "requirement": "high-AUROC mechanism results are separated from calibrated p_rel/p_obs claims",
            "minimum_evidence": "ECE/proper scoring report and calibration protocol if probability is claimed",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G8",
            "gate": "Q_e/p_obs separation",
            "requirement": "Q_e is evaluated as observability/selective-decision evidence, not relation truth",
            "minimum_evidence": "Q_e-only/shuffled-Q control and abstain metric",
            "blocks_paper_promotion": True,
        },
        {
            "gate_id": "G9",
            "gate": "claim wording lock",
            "requirement": "do not claim paper-level reliability, complete horizontal coverage, all-family generality, geometry-only method, or solved support/contact until gates pass",
            "minimum_evidence": "reviewer-risk table and paper wording checklist",
            "blocks_paper_promotion": True,
        },
    ]


def forbidden_wording() -> list[dict[str, str]]:
    return [
        {
            "forbidden": "H002 solves relation reliability for 3D scene graphs.",
            "replacement": "H002 provides train-only mechanism evidence for relation-aware predicate-geometry compatibility routing.",
        },
        {
            "forbidden": "relative_horizontal covers all horizontal spatial relations.",
            "replacement": "relative_horizontal is a frame-aware route over left/right/front/behind; in front of is absent/excluded.",
        },
        {
            "forbidden": "relative_horizontal is a geometry-only method.",
            "replacement": "relative_horizontal requires predicate-conditioned frame-aware T_e x G_e compatibility.",
        },
        {
            "forbidden": "size_relative proves calibrated relation reliability.",
            "replacement": "size_relative is a clean C_e mechanism route with a calibration caveat.",
        },
        {
            "forbidden": "support/contact is solved.",
            "replacement": "support/contact provides challenging compatibility-route evidence with caveat.",
        },
        {
            "forbidden": "H002 is a geometry-only framework.",
            "replacement": "H002 requires T_e x G_e compatibility; geometry-only is a baseline/control and may only solve geometry-easy diagnostics.",
        },
        {
            "forbidden": "Q_e predicts relation truth.",
            "replacement": "Q_e estimates observability and supports abstention/selective decision.",
        },
        {
            "forbidden": "close by proves the learned compatibility model.",
            "replacement": "close by is a geometry-easy diagnostic/control under the current target.",
        },
        {
            "forbidden": "all relation families are covered.",
            "replacement": "the current route taxonomy separates main, diagnostic, future, and deferred families.",
        },
    ]


def reviewer_response_plan() -> list[dict[str, Any]]:
    return [
        {
            "reviewer_question": "Is this just concatenating semantic and geometry features?",
            "answer": "No. Plain T_e+G_e concat is an explicit baseline and fails on clean vertical, size, and horizontal routes where T_e x G_e succeeds.",
            "required_artifact": "T1; A4/A5; C1-C6 controls",
        },
        {
            "reviewer_question": "Are the clean routes too easy?",
            "answer": "They are mechanism anchors, not the entire claim. support/contact remains the challenging route and diagnostics define the route boundary.",
            "required_artifact": "T1/T2; reviewer risks; support/contact caveat",
        },
        {
            "reviewer_question": "Why not all 3DSSG relation types?",
            "answer": "H002 is relation-aware: geometry compatibility is meaningful only for geometry-relevant families; ontology/reference-frame/observability-heavy families are routed differently.",
            "required_artifact": "T2 route taxonomy; coverage sufficiency review next",
        },
        {
            "reviewer_question": "Does relative_horizontal depend on an arbitrary frame?",
            "answer": "Yes, horizontal predicates require a frame convention. That is why the route is explicitly frame-aware and includes wrong-frame, sign-flip, and endpoint-swap controls.",
            "required_artifact": "T1/T2 horizontal row; C5/C6 controls",
        },
        {
            "reviewer_question": "Where is in front of?",
            "answer": "`in front of` is not observed in the current train-side source and is excluded. H002 does not claim complete horizontal ontology coverage.",
            "required_artifact": "T3 diagnostic boundary; forbidden wording",
        },
        {
            "reviewer_question": "Support/contact AUROC is only near 0.70. Is that strong enough?",
            "answer": "Do not claim solved support/contact. Use it as challenging route evidence because interaction beats single-factor baselines and controls degrade.",
            "required_artifact": "T1 support/contact row; failure analysis",
        },
        {
            "reviewer_question": "Is close by just a distance threshold?",
            "answer": "Yes under the current target; this is why it is diagnostic/control rather than main learned C_e proof.",
            "required_artifact": "T2/T3 proximity row",
        },
        {
            "reviewer_question": "Does high AUROC imply calibrated reliability?",
            "answer": "No. clean route smokes have high AUROC but high ECE; p_rel/p_obs calibration remains blocked.",
            "required_artifact": "T4; G7; calibration caveat",
        },
        {
            "reviewer_question": "Why is this not paper evidence yet?",
            "answer": "Current artifacts are train-only hypothesis evidence. Paper-level claims require coverage review, Docker, grouped held-out evaluation, and CI.",
            "required_artifact": "promotion gates G1-G9",
        },
    ]


def write_table_spec(path: Path) -> None:
    text = """# H002 Ablation And Table Plan Update After Relative-Horizontal

## Purpose

This artifact refreshes the H002 table and ablation contract after adding
`relative_horizontal` to the multi-family synthesis. It does not run a model and
does not promote H002 to paper-level evidence.

## Candidate Tables

1. `T1 Predicate-Geometry Compatibility Mechanism`
   - Rows: `relative_vertical`, `size_relative`, `relative_horizontal`,
     `support_contact`.
   - Required comparisons: `T_e` only, `Z_e` only if available, `G_e` only,
     `T_e + G_e` concat, `C_e = interaction(T_e, G_e)`, wrong-T, shuffled-G,
     sign-flip, and horizontal-specific wrong-frame / endpoint-swap controls.

2. `T2 Relation-Aware Evidence Routing Taxonomy`
   - Rows: clean routes, challenging routes, geometry-easy controls,
     observability-heavy future routes, superordinate diagnostics, and
     frame-aware horizontal route.

3. `T3 Diagnostic Boundary Cases`
   - `close by`, `supported by`, `attached to`, `hanging on`, `connected to`,
     and absent/deferred `in front of`.

4. `T4 Calibration and Claim Boundary`
   - Blocks calibrated `p_rel`/`p_obs`, paper-level performance, all-family
     generality, complete horizontal ontology, geometry-only claims, and solved
     support/contact wording.

## Current Mechanism Rows

- `relative_vertical`: clean `T_e x G_e` mechanism anchor.
- `size_relative`: clean `T_e x G_e` mechanism anchor with calibration caveat.
- `relative_horizontal`: frame-aware `T_e x G_e` mechanism anchor with horizontal controls.
- `support_contact`: challenging `T_e x G_e` route evidence with caveat.

## Promotion Boundary

The next step is a route-coverage sufficiency review. H002 should not move to
Docker or paper-level result promotion until that review decides whether the
current family coverage is enough or whether another relation family must be
added.
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# H002 Ablation And Table Plan Update After Relative-Horizontal

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Decision

The H002 candidate table contract now includes `relative_horizontal`.

Main mechanism rows:

```text
relative_vertical
size_relative
relative_horizontal
support_contact
```

Key update:

- `relative_horizontal` adds frame-aware controls:
  - wrong-frame x/y swap
  - selected-axis sign flip
  - subject/object endpoint swap
- `in front of` remains excluded/deferred.
- The claim remains train-only mechanism evidence, not paper-level reliability.

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

    synthesis_summary = read_json(args.synthesis_dir / "summary.json")
    claim = read_json(args.synthesis_dir / "claim_skeleton.json")
    evidence = read_csv(args.synthesis_dir / "evidence_table.csv")
    routes = read_csv(args.synthesis_dir / "family_route_table.csv")
    next_contract = read_json(args.synthesis_dir / "next_plan_contract.json")

    errors = validate_inputs(synthesis_summary, claim, evidence, routes, next_contract, args.synthesis_dir)
    main_tables = main_table_plan(evidence)
    route_taxonomy = route_taxonomy_table(routes)
    ablations = ablation_matrix()
    controls = control_matrix()
    gates = promotion_gates()
    wording = forbidden_wording()
    reviewer_plan = reviewer_response_plan()

    status = STATUS_ERRORS if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "input_paths": {
            "synthesis": rel_path(args.synthesis_dir),
            "synthesis_summary": rel_path(args.synthesis_dir / "summary.json"),
            "evidence_table": rel_path(args.synthesis_dir / "evidence_table.csv"),
            "family_route_table": rel_path(args.synthesis_dir / "family_route_table.csv"),
            "next_plan_contract": rel_path(args.synthesis_dir / "next_plan_contract.json"),
        },
        "output_paths": {
            "artifact_root": rel_path(args.output_dir),
            "summary": rel_path(args.output_dir / "summary.json"),
            "main_table_plan": rel_path(args.output_dir / "main_table_plan.csv"),
            "route_taxonomy_table": rel_path(args.output_dir / "route_taxonomy_table.csv"),
            "ablation_matrix": rel_path(args.output_dir / "ablation_matrix.csv"),
            "control_matrix": rel_path(args.output_dir / "control_matrix.csv"),
            "promotion_gates": rel_path(args.output_dir / "promotion_gates.csv"),
            "forbidden_wording": rel_path(args.output_dir / "forbidden_wording.csv"),
            "reviewer_response_plan": rel_path(args.output_dir / "reviewer_response_plan.csv"),
            "table_spec": rel_path(args.output_dir / "table_spec.md"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "counts": {
            "main_table_rows": len(main_tables),
            "route_taxonomy_rows": len(route_taxonomy),
            "ablation_rows": len(ablations),
            "control_rows": len(controls),
            "promotion_gate_rows": len(gates),
            "forbidden_wording_rows": len(wording),
            "reviewer_response_rows": len(reviewer_plan),
        },
        "main_mechanism_families": [
            "relative_vertical",
            "size_relative",
            "relative_horizontal",
            "support_contact",
        ],
        "claim_boundary": {
            "allowed": "train-only relation-aware predicate-geometry compatibility routing mechanism evidence",
            "blocked": [
                "paper-level performance",
                "held-out/test reliability",
                "calibrated p_rel/p_obs",
                "complete horizontal ontology",
                "geometry-only framework",
                "support/contact fully solved",
                "all-family generality",
            ],
        },
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "split": "train_only_table_plan",
            "test_usage": False,
            "validation_usage": False,
            "calibrated_probability_claim_allowed": False,
            "complete_horizontal_ontology_claim_allowed": False,
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "main_table_plan.csv", main_tables)
    write_csv(args.output_dir / "route_taxonomy_table.csv", route_taxonomy)
    write_csv(args.output_dir / "ablation_matrix.csv", ablations)
    write_csv(args.output_dir / "control_matrix.csv", controls)
    write_csv(args.output_dir / "promotion_gates.csv", gates)
    write_csv(args.output_dir / "forbidden_wording.csv", wording)
    write_csv(args.output_dir / "reviewer_response_plan.csv", reviewer_plan)
    write_table_spec(args.output_dir / "table_spec.md")
    write_report(args.output_dir / "report.md", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
