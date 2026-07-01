#!/usr/bin/env python3
"""Freeze H002 route-specific target definitions and promotion protocol."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review"
)

EXPECTED_REVIEW_STATUS = (
    "h002_compatibility_dataset_v3_route_coverage_sufficiency_review_after_relative_horizontal_table_plan_ready"
)
EXPECTED_REVIEW_NEXT = "compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_v1"
STATUS_READY = "h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_input_errors"
SELECTED_PATH = "freeze_route_specific_target_definitions_and_promotion_protocol"
NEXT_TODO = "compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
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


def validate_inputs(review: dict[str, Any], review_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if review.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review.get("status")})
    if review.get("next_todo") != EXPECTED_REVIEW_NEXT:
        errors.append({"error_type": "unexpected_review_next_todo", "actual": review.get("next_todo")})
    if review.get("validation_errors") != 0:
        errors.append({"error_type": "review_validation_errors_present", "actual": review.get("validation_errors")})
    validation_rows = read_jsonl(review_dir / "validation_errors.jsonl")
    if validation_rows:
        errors.append({"error_type": "review_validation_error_rows_present", "rows": len(validation_rows)})
    boundary = review.get("paper_boundary", {})
    for key in [
        "all_family_generality_allowed",
        "calibrated_p_rel_p_obs_allowed",
        "complete_horizontal_ontology_allowed",
        "held_out_or_test_claim_allowed",
        "paper_evidence_allowed_now",
        "support_contact_solved_claim_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    required_main = {"relative_vertical", "size_relative", "relative_horizontal", "support_contact"}
    missing_main = required_main - set(review.get("main_mechanism_families", []))
    if missing_main:
        errors.append({"error_type": "missing_main_family", "missing": sorted(missing_main)})
    return errors


def route_taxonomy_freeze() -> list[dict[str, Any]]:
    return [
        {
            "route_id": "R1",
            "route_type": "geometry_only_learned_evaluated_route",
            "family": "proximity",
            "relations": "close by",
            "paper_role": "claim_control_evidence",
            "core_question": "Can geometry evidence alone explain the relation?",
            "target_semantics": "learn/evaluate G_e sufficiency; do not require T_e x G_e interaction",
            "primary_factors": "G_e; optional Q_e for coverage",
            "blocked_interpretation": "close by requires predicate-geometry interaction",
            "status_after_freeze": "included_as_geometry_only_route",
        },
        {
            "route_id": "R2",
            "route_type": "predicate_geometry_interaction_route",
            "family": "relative_vertical",
            "relations": "higher than; lower than",
            "paper_role": "main_mechanism_evidence",
            "core_question": "Does T_e x signed vertical G_e identify compatibility better than T-only, G-only, or concat?",
            "target_semantics": "same geometry can be compatible or incompatible depending on predicate direction",
            "primary_factors": "T_e; G_e; C_e",
            "blocked_interpretation": "geometry-only universal reliability",
            "status_after_freeze": "included_as_clean_interaction_route",
        },
        {
            "route_id": "R3",
            "route_type": "predicate_geometry_interaction_route",
            "family": "size_relative",
            "relations": "bigger than; smaller than",
            "paper_role": "main_mechanism_evidence_with_calibration_caveat",
            "core_question": "Does T_e x size-ratio G_e identify compatibility beyond T-only, G-only, or concat?",
            "target_semantics": "same size relation flips when predicate flips",
            "primary_factors": "T_e; G_e; C_e",
            "blocked_interpretation": "calibrated p_rel/p_obs or all-family result",
            "status_after_freeze": "included_as_clean_interaction_route",
        },
        {
            "route_id": "R4",
            "route_type": "predicate_geometry_interaction_route",
            "family": "relative_horizontal",
            "relations": "left; right; front; behind",
            "paper_role": "main_mechanism_evidence_with_reference_frame_caveat",
            "core_question": "Does T_e x frame-aware horizontal G_e identify directional compatibility?",
            "target_semantics": "compatibility depends on signed horizontal axis under a frozen reference-frame convention",
            "primary_factors": "T_e; G_e; C_e; Q_e for frame/axis boundary",
            "blocked_interpretation": "complete horizontal ontology including in front of",
            "status_after_freeze": "included_as_frame_aware_interaction_route",
        },
        {
            "route_id": "R5",
            "route_type": "predicate_geometry_interaction_route",
            "family": "support_contact",
            "relations": "standing on; lying on",
            "paper_role": "main_challenging_evidence_with_caveat",
            "core_question": "Does contact/pose geometry become reliable only when interpreted with the predicate?",
            "target_semantics": "standing and lying support require different pose/contact compatibility",
            "primary_factors": "T_e; G_e; C_e; Q_e",
            "blocked_interpretation": "support/contact fully solved",
            "status_after_freeze": "included_as_challenging_interaction_route",
        },
        {
            "route_id": "R6",
            "route_type": "superordinate_support_decomposition_route",
            "family": "superordinate_support",
            "relations": "supported by",
            "paper_role": "claim_control_or_next_probe",
            "core_question": "Should broad support be accepted, relabeled into subtype, or abstained?",
            "target_semantics": "decompose broad support into subtype/relabel/abstain rather than clean binary truth",
            "primary_factors": "T_e; G_e; Q_e; p_obs; relabel target",
            "blocked_interpretation": "supported by is a clean negative for standing/lying on",
            "status_after_freeze": "included_as_decomposition_route_candidate",
        },
        {
            "route_id": "R7",
            "route_type": "observability_aware_route",
            "family": "attachment_observability",
            "relations": "attached to; hanging on; connected to",
            "paper_role": "next_probe_or_future_evidence",
            "core_question": "Is the evidence observable enough to decide attachment/connection reliability?",
            "target_semantics": "accept/reject/abstain with visual, mesh, contact, and topology evidence; connected to remains diagnostic until functional/physical schema exists",
            "primary_factors": "G_e; Q_e; p_obs; C_e when observable",
            "blocked_interpretation": "OBB distance alone decides attachment reliability",
            "status_after_freeze": "included_as_observability_route",
        },
        {
            "route_id": "R8",
            "route_type": "contact_orientation_feasibility_route",
            "family": "contact_orientation",
            "relations": "leaning against",
            "paper_role": "next_feasibility_route",
            "core_question": "Can contact, normal alignment, tilt, and support explain leaning?",
            "target_semantics": "contact-orientation compatibility with normals/pose and coverage-aware abstain",
            "primary_factors": "G_e normals/pose/contact; Q_e",
            "blocked_interpretation": "generic support/contact is enough",
            "status_after_freeze": "included_as_next_feasibility_candidate",
        },
        {
            "route_id": "R9",
            "route_type": "occlusion_coverage_feasibility_route",
            "family": "occlusion_coverage",
            "relations": "cover",
            "paper_role": "next_feasibility_route",
            "core_question": "Can projected overlap, occlusion, and visibility reduction explain cover?",
            "target_semantics": "coverage/occlusion compatibility plus Q_e for visible evidence",
            "primary_factors": "G_e overlap/occlusion; Q_e visibility",
            "blocked_interpretation": "cover is purely semantic ontology",
            "status_after_freeze": "included_as_next_feasibility_candidate",
        },
        {
            "route_id": "R10",
            "route_type": "containment_feasibility_route",
            "family": "containment",
            "relations": "standing in; lying in; hanging in; inside",
            "paper_role": "next_feasibility_route",
            "core_question": "Can containment be decided with containment ratio plus occlusion/completeness evidence?",
            "target_semantics": "containment compatibility with point-in-container, OBB/mesh containment, and abstain for incomplete evidence",
            "primary_factors": "G_e containment; Q_e completeness/visibility; p_obs",
            "blocked_interpretation": "OBB overlap alone is reliable containment",
            "status_after_freeze": "included_as_next_feasibility_candidate",
        },
        {
            "route_id": "R11",
            "route_type": "identity_symmetry_route",
            "family": "identity_symmetry",
            "relations": "same as; same symmetry as",
            "paper_role": "separate_task_candidate",
            "core_question": "Can geometry/shape identity or symmetry evidence verify duplicate/symmetry relations?",
            "target_semantics": "identity, duplicate, or symmetry compatibility; not the same as physical relation reliability",
            "primary_factors": "G_e shape/size/pose/symmetry; T_e identity semantics; Q_e",
            "blocked_interpretation": "no geometry issue exists",
            "status_after_freeze": "included_as_separate_route_candidate",
        },
        {
            "route_id": "R12",
            "route_type": "semantic_structural_route",
            "family": "semantic_structural",
            "relations": "part of; belonging to",
            "paper_role": "semantic_structural_boundary_or_future",
            "core_question": "Is the relation semantic/structural rather than directly physical?",
            "target_semantics": "part-whole or association compatibility; likely requires ontology/structure evidence beyond metric geometry",
            "primary_factors": "T_e; structural evidence; optional G_e; Q_e",
            "blocked_interpretation": "metric geometry alone is sufficient",
            "status_after_freeze": "included_as_semantic_structural_boundary",
        },
        {
            "route_id": "R13",
            "route_type": "embedded_structure_feasibility_route",
            "family": "embedded_structure",
            "relations": "build in",
            "paper_role": "future_feasibility_route",
            "core_question": "Can cavity, wall, and embedded geometry verify built-in structure?",
            "target_semantics": "embedded structural compatibility requiring mesh/scene context",
            "primary_factors": "G_e mesh/cavity/context; Q_e completeness",
            "blocked_interpretation": "build in is covered by generic containment",
            "status_after_freeze": "included_as_future_feasibility_candidate",
        },
    ]


def target_definition_freeze(route_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    definitions = {
        "geometry_only_learned_evaluated_route": {
            "positive_definition": "relation is supported by route-specific geometry threshold or audited geometry evidence",
            "negative_definition": "matched object pair is outside the geometry support condition; not merely no-GT",
            "abstain_definition": "low coverage, missing geometry, or boundary distance ambiguity",
            "required_controls": "distance-bin control; scale control; shuffled-G; wrong-pair geometry",
            "metric_contract": "AUROC/F1 for route decision plus violation/coverage tradeoff; do not use as T_e x G_e proof",
        },
        "predicate_geometry_interaction_route": {
            "positive_definition": "T_e is compatible with the predicate-independent G_e under route-specific semantics",
            "negative_definition": "predicate flip, sign flip, endpoint swap, wrong-frame, or hard negative makes the same/similar G_e incompatible",
            "abstain_definition": "route-specific evidence missing or near boundary",
            "required_controls": "T-only; G-only; Z-only if available; concat; T_e x G_e; wrong-T; shuffled-G; sign/endpoint/frame controls",
            "metric_contract": "interaction must beat single-factor/concat baselines and collapse under counterfactual controls",
        },
        "superordinate_support_decomposition_route": {
            "positive_definition": "broad support is visually/geometrically plausible",
            "negative_definition": "no support evidence under matched surface/contact conditions",
            "abstain_definition": "support exists but subtype is ambiguous or evidence insufficient",
            "required_controls": "standing/lying subtype confusion; support-surface control; relabel-vs-delete audit",
            "metric_contract": "report accept/relabel/abstain accuracy and subtype confusion, not only binary AUROC",
        },
        "observability_aware_route": {
            "positive_definition": "attachment/connection is supported by observable contact, mesh, topology, or multi-view evidence",
            "negative_definition": "matched row with no physical/functional evidence after visibility is sufficient",
            "abstain_definition": "evidence needed for the relation is missing, occluded, or not resolvable",
            "required_controls": "no-view; low-visibility; shuffled-view; wrong-pair view; mesh/contact ablation",
            "metric_contract": "evaluate p_obs/selective decision separately from p_rel accept/reject",
        },
        "contact_orientation_feasibility_route": {
            "positive_definition": "leaning relation has contact plus orientation/normal evidence",
            "negative_definition": "near/contact without leaning orientation or support plausibility",
            "abstain_definition": "normal/pose/contact evidence missing",
            "required_controls": "normal shuffle; tilt ablation; contact-only baseline",
            "metric_contract": "feasibility audit before paper claim",
        },
        "occlusion_coverage_feasibility_route": {
            "positive_definition": "subject covers object under projected overlap/visibility reduction",
            "negative_definition": "overlap absent or object remains visible under matched view/scale",
            "abstain_definition": "no view or occlusion evidence",
            "required_controls": "view shuffle; overlap-only baseline; visibility coverage bins",
            "metric_contract": "feasibility audit before paper claim",
        },
        "containment_feasibility_route": {
            "positive_definition": "object is contained under 3D containment/point-in-container evidence",
            "negative_definition": "matched pair lacks containment while class/source confounds are controlled",
            "abstain_definition": "container geometry incomplete or object is occluded/partially scanned",
            "required_controls": "class-pair control; containment-ratio bins; completeness ablation",
            "metric_contract": "feasibility audit before paper claim",
        },
        "identity_symmetry_route": {
            "positive_definition": "identity/symmetry relation is supported by shape, size, pose, or symmetry evidence",
            "negative_definition": "same class but nonmatching shape/symmetry under controlled pair",
            "abstain_definition": "insufficient instance segmentation or shape evidence",
            "required_controls": "class-only baseline; shape shuffle; duplicate-pair leakage check",
            "metric_contract": "separate task candidate; do not mix with physical relation reliability table unless scoped",
        },
        "semantic_structural_route": {
            "positive_definition": "semantic/structural relation is supported by ontology or part-whole evidence",
            "negative_definition": "matched semantic pair lacks structural/ontology support",
            "abstain_definition": "metric geometry cannot resolve semantic association",
            "required_controls": "class-pair/ontology baseline; structural evidence ablation",
            "metric_contract": "boundary/future route unless structural evidence is formalized",
        },
        "embedded_structure_feasibility_route": {
            "positive_definition": "object is built into scene structure with cavity/wall/mesh evidence",
            "negative_definition": "near wall or container without embedded structure",
            "abstain_definition": "mesh/cavity evidence incomplete",
            "required_controls": "wall-near baseline; mesh-completeness control",
            "metric_contract": "future feasibility route",
        },
    }
    rows: list[dict[str, Any]] = []
    for row in route_rows:
        route_type = row["route_type"]
        contract = definitions[route_type]
        rows.append(
            {
                "route_id": row["route_id"],
                "route_type": route_type,
                "family": row["family"],
                "relations": row["relations"],
                **contract,
            }
        )
    return rows


def schema_freeze_manifest() -> list[dict[str, Any]]:
    return [
        {
            "block": "row_identity",
            "model_safe": False,
            "allowed_view": "audit/control/provenance",
            "fields": "row_id; group_id; scan_id; scene_id; subject_instance_id; object_instance_id; directed_pair_id",
            "rule": "never use identity fields as model input except named leakage probes",
        },
        {
            "block": "T_e",
            "model_safe": True,
            "allowed_view": "model",
            "fields": "predicate label/text; relation family; subject/object class; optional text embeddings",
            "rule": "semantic content only; no source score, label, target bucket, or construction key",
        },
        {
            "block": "Z_e",
            "model_safe": True,
            "allowed_view": "final p_rel/source baseline only",
            "fields": "source id; source score; normalized score; rank; rank band",
            "rule": "excluded from C_e; must have shuffle/rank controls",
        },
        {
            "block": "G_e",
            "model_safe": True,
            "allowed_view": "model",
            "fields": "predicate-independent object/pair geometry; point/mesh/contact/containment/shape features",
            "rule": "no predicate, relation family, source score, GT/audit label, or route construction bucket",
        },
        {
            "block": "Q_e",
            "model_safe": True,
            "allowed_view": "p_obs/selective decision",
            "fields": "point/mesh/view availability; coverage; completeness; conflict; unsupported evidence flags",
            "rule": "does not directly decide relation truth; controls abstain/selective decision",
        },
        {
            "block": "C_e",
            "model_safe": "derived",
            "allowed_view": "model output/head",
            "fields": "compatibility(T_e, G_e)",
            "rule": "must not use Z_e; route-specific meaning must be declared",
        },
        {
            "block": "labels",
            "model_safe": False,
            "allowed_view": "target/evaluation only",
            "fields": "route target; accept/reject/abstain; p_obs target; relabel/subtype target",
            "rule": "not input; no-GT is not automatic negative",
        },
        {
            "block": "hidden_construction",
            "model_safe": False,
            "allowed_view": "audit/control only",
            "fields": "geometry status bucket; construction stratum; candidate bucket; hidden machine hints; label source",
            "rule": "must be absent from model-safe view and reported only in shortcut audits",
        },
        {
            "block": "route_metadata",
            "model_safe": "limited",
            "allowed_view": "router or stratified reporting",
            "fields": "route_type; paper_role; target_semantics",
            "rule": "allowed for route selection/reporting; not allowed to encode target labels or hidden construction buckets",
        },
    ]


def promotion_protocol() -> list[dict[str, Any]]:
    return [
        {
            "stage": "P0",
            "name": "hypothesis-stage route taxonomy freeze",
            "status": "complete_in_this_artifact",
            "required_before_next": "route taxonomy, target definition, schema freeze manifest",
            "paper_claim_allowed": False,
        },
        {
            "stage": "P1",
            "name": "route-specific target manifest plan",
            "status": "next",
            "required_before_next": "per-route dataset roots, model-safe/hidden views, positive/negative/abstain definitions, controls",
            "paper_claim_allowed": False,
        },
        {
            "stage": "P2",
            "name": "schema and shortcut audit",
            "status": "pending",
            "required_before_next": "blocked field hits = 0; identity/source/class shortcut probes reported",
            "paper_claim_allowed": False,
        },
        {
            "stage": "P3",
            "name": "hypothesis smoke runner",
            "status": "pending",
            "required_before_next": "single-factor, concat, route model, and counterfactual controls per route",
            "paper_claim_allowed": False,
        },
        {
            "stage": "P4",
            "name": "Docker reproduction protocol",
            "status": "pending",
            "required_before_next": "Dockerfile/compose, pinned deps, mounted dataset paths, command manifest",
            "paper_claim_allowed": False,
        },
        {
            "stage": "P5",
            "name": "held-out grouped evaluation",
            "status": "pending",
            "required_before_next": "scan and endpoint-pair grouped split; no target construction leakage",
            "paper_claim_allowed": "only scoped mechanism/performance claim after pass",
        },
        {
            "stage": "P6",
            "name": "calibration and selective decision",
            "status": "pending",
            "required_before_next": "ECE/Brier/NLL/selective-risk protocol for p_obs and p_rel",
            "paper_claim_allowed": "only calibrated p_obs/p_rel claim after pass",
        },
        {
            "stage": "P7",
            "name": "paper wording lock",
            "status": "pending",
            "required_before_next": "allowed/blocked claim checklist and reviewer-response table",
            "paper_claim_allowed": "only after P4-P6 relevant gates pass",
        },
    ]


def paper_claim_boundary() -> list[dict[str, Any]]:
    return [
        {
            "claim": "relation-aware evidence routing",
            "status": "allowed_hypothesis_stage",
            "wording": "Different relation families require different target definitions and evidence routes.",
            "required_artifact": "route_taxonomy_freeze.csv",
        },
        {
            "claim": "fixed semantic-geometry fusion is insufficient",
            "status": "allowed_as_framework_claim",
            "wording": "Do not use one universal fusion target; compare routes by their route-specific targets.",
            "required_artifact": "target_definition_freeze.csv",
        },
        {
            "claim": "geometry-only route exists",
            "status": "allowed_scoped",
            "wording": "`close by` is a geometry-only learned/evaluated route, not a predicate-geometry interaction proof.",
            "required_artifact": "proximity route target and controls",
        },
        {
            "claim": "predicate-geometry interaction route exists",
            "status": "allowed_scoped",
            "wording": "Use relative vertical, size, horizontal, and support/contact as scoped mechanism rows.",
            "required_artifact": "T_e/G_e/concat/interaction/control tables",
        },
        {
            "claim": "observability-aware route exists",
            "status": "allowed_as_protocol_or_future_until_materialized",
            "wording": "Attachment/containment/cover require Q_e and p_obs; do not force binary accept/reject when evidence is missing.",
            "required_artifact": "observability route manifest and audit",
        },
        {
            "claim": "paper-level reliability improvement",
            "status": "blocked",
            "wording": "Not allowed until Docker and held-out grouped evaluation pass.",
            "required_artifact": "Docker protocol and held-out metrics",
        },
        {
            "claim": "calibrated p_rel/p_obs",
            "status": "blocked",
            "wording": "Not allowed until calibration protocol passes.",
            "required_artifact": "ECE/Brier/NLL/selective-risk report",
        },
        {
            "claim": "all-family generality",
            "status": "blocked",
            "wording": "Do not claim every 3DSSG relation is solved; taxonomy includes future/boundary routes.",
            "required_artifact": "family inventory and boundary table",
        },
    ]


def next_probe_queue() -> list[dict[str, Any]]:
    return [
        {
            "rank": 1,
            "next_candidate": "route_specific_target_manifest_plan",
            "relations": "all frozen routes",
            "reason": "before new mining, every route needs model-safe fields, hidden fields, target axes, and controls",
            "next_action": NEXT_TODO,
        },
        {
            "rank": 2,
            "next_candidate": "close by geometry-only route manifest",
            "relations": "close by",
            "reason": "convert proximity from diagnostic-only wording to geometry-only learned/evaluated route",
            "next_action": "define distance/scale/coverage controls and model-safe G_e route target",
        },
        {
            "rank": 3,
            "next_candidate": "supported by decomposition manifest",
            "relations": "supported by",
            "reason": "broad support is useful as relabel/abstain/decomposition route, not clean binary negative",
            "next_action": "define accept/relabel/abstain and standing/lying subtype controls",
        },
        {
            "rank": 4,
            "next_candidate": "attachment observability manifest",
            "relations": "attached to; hanging on; connected to",
            "reason": "promising but needs Q_e/p_obs and visual/mesh/topology evidence separation",
            "next_action": "define observable/unobservable and physical/functional evidence schema",
        },
        {
            "rank": 5,
            "next_candidate": "cover/leaning/containment feasibility manifests",
            "relations": "cover; leaning against; standing in; lying in; hanging in; inside",
            "reason": "high-value feasibility routes but need route-specific evidence schema before materialization",
            "next_action": "capacity/schema audit only",
        },
        {
            "rank": 6,
            "next_candidate": "identity/symmetry and semantic/structural boundary manifests",
            "relations": "same as; same symmetry as; part of; belonging to; build in",
            "reason": "possible extensions but should be scoped as separate route/task candidates",
            "next_action": "boundary and feasibility audit, not main paper route",
        },
    ]


def write_report(
    path: Path,
    status: str,
    validation_errors: int,
    routes: list[dict[str, Any]],
    promotion: list[dict[str, Any]],
) -> None:
    main_routes = [row for row in routes if "main" in row["paper_role"]]
    lines = [
        "# H002 Schema Freeze And Promotion Protocol After Route-Coverage Review",
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
        "## Core Decision",
        "",
        "H002 now freezes relation-specific target definitions. The question is not whether a",
        "relation is a learned compatibility target or not. The question is which evidence route",
        "and target semantics that relation requires.",
        "",
        "Frozen route types:",
        "",
        "- geometry-only learned/evaluated route",
        "- predicate-geometry interaction route",
        "- superordinate support decomposition / relabel / abstain route",
        "- observability-aware route",
        "- contact-orientation, occlusion/coverage, and containment feasibility routes",
        "- identity/symmetry route",
        "- semantic/structural route",
        "",
        "## Route Mapping",
        "",
        "| Route | Relations | Paper Role | Target Semantics |",
        "| --- | --- | --- | --- |",
    ]
    for row in routes:
        lines.append(
            f"| {row['route_type']} | {row['relations']} | {row['paper_role']} | {row['target_semantics']} |"
        )
    lines.extend(
        [
            "",
            "## Main Mechanism Rows",
            "",
            "| Family | Relations | Role |",
            "| --- | --- | --- |",
        ]
    )
    for row in main_routes:
        lines.append(f"| {row['family']} | {row['relations']} | {row['paper_role']} |")
    lines.extend(
        [
            "",
            "## Promotion Protocol",
            "",
            "| Stage | Name | Status | Required Before Next |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in promotion:
        lines.append(f"| {row['stage']} | {row['name']} | {row['status']} | {row['required_before_next']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Allowed now:",
            "",
            "- route-specific target definition",
            "- train-only hypothesis-stage framework claim",
            "- geometry-only route for `close by`",
            "- predicate-geometry route for current main mechanism rows",
            "- observability/decomposition/semantic-structural routes as protocol or future/boundary routes",
            "",
            "Blocked now:",
            "",
            "- paper-level reliability improvement",
            "- calibrated `p_rel` / `p_obs`",
            "- all-family solved/general relation reliability",
            "- forcing all relation types into one binary target or one fixed fusion head",
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
    review_dir = args.review_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    review = read_json(review_dir / "summary.json")
    family_decisions = read_csv(review_dir / "family_decisions.csv")
    errors = validate_inputs(review, review_dir)
    status = STATUS_ERRORS if errors else STATUS_READY

    routes = route_taxonomy_freeze()
    targets = target_definition_freeze(routes)
    schema_rows = schema_freeze_manifest()
    promotion_rows = promotion_protocol()
    claim_rows = paper_claim_boundary()
    next_rows = next_probe_queue()

    output_paths = {
        "artifact_root": rel_path(output_dir),
        "route_taxonomy_freeze": rel_path(output_dir / "route_taxonomy_freeze.csv"),
        "target_definition_freeze": rel_path(output_dir / "target_definition_freeze.csv"),
        "schema_freeze_manifest": rel_path(output_dir / "schema_freeze_manifest.csv"),
        "promotion_protocol": rel_path(output_dir / "promotion_protocol.csv"),
        "paper_claim_boundary": rel_path(output_dir / "paper_claim_boundary.csv"),
        "next_probe_queue": rel_path(output_dir / "next_probe_queue.csv"),
        "report": rel_path(output_dir / "report.md"),
        "summary": rel_path(output_dir / "summary.json"),
        "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "input_errors_fix_before_schema_freeze",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "route_coverage_review": rel_path(review_dir),
        },
        "output_paths": output_paths,
        "counts": {
            "route_taxonomy_rows": len(routes),
            "target_definition_rows": len(targets),
            "schema_freeze_rows": len(schema_rows),
            "promotion_protocol_rows": len(promotion_rows),
            "paper_claim_boundary_rows": len(claim_rows),
            "next_probe_rows": len(next_rows),
            "previous_family_decision_rows": len(family_decisions),
        },
        "frozen_claim": (
            "H002 asks which evidence route and target definition each relation family requires: "
            "geometry-only, predicate-geometry interaction, observability-aware, superordinate "
            "decomposition, identity/symmetry, or semantic/structural."
        ),
        "main_mechanism_relations": [
            "higher than",
            "lower than",
            "bigger than",
            "smaller than",
            "left",
            "right",
            "front",
            "behind",
            "standing on",
            "lying on",
        ],
        "route_redefinition": {
            "close by": "geometry-only learned/evaluated route",
            "supported by": "superordinate support decomposition / relabel / abstain route",
            "attached to; hanging on; connected to": "observability-aware route",
            "cover; leaning against; standing in; lying in; hanging in; inside": "next feasibility routes",
            "same as; same symmetry as": "identity/symmetry route",
            "part of; belonging to": "semantic/structural route",
        },
        "paper_boundary": {
            "paper_level_reliability_allowed_now": False,
            "calibrated_p_rel_p_obs_allowed_now": False,
            "all_relation_types_same_target_allowed": False,
            "route_specific_target_definitions_allowed": True,
            "geometry_only_close_by_route_allowed": True,
            "supported_by_decomposition_route_allowed": True,
        },
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
    }

    write_csv(output_dir / "route_taxonomy_freeze.csv", routes)
    write_csv(output_dir / "target_definition_freeze.csv", targets)
    write_csv(output_dir / "schema_freeze_manifest.csv", schema_rows)
    write_csv(output_dir / "promotion_protocol.csv", promotion_rows)
    write_csv(output_dir / "paper_claim_boundary.csv", claim_rows)
    write_csv(output_dir / "next_probe_queue.csv", next_rows)
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", status, len(errors), routes, promotion_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
