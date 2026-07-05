#!/usr/bin/env python3
"""Write the H002 support/contact harder-route materialization plan."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SOURCE_INVENTORY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol"
)
DEFAULT_OFFICIAL_MATERIALIZATION_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/official_materialization/latest"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory"
)

EXPECTED_SOURCE_STATUS = "h002_compatibility_dataset_v3_support_contact_harder_route_source_inventory_after_protocol_ready"
EXPECTED_SOURCE_NEXT = "compatibility_dataset_v3_support_contact_harder_route_materialization_plan_after_source_inventory"

SCHEMA_VERSION = "h002_support_contact_harder_route_materialization_plan_after_source_inventory_v1"
STATUS_READY = "h002_support_contact_harder_route_materialization_plan_after_source_inventory_ready"
STATUS_ERRORS = "h002_support_contact_harder_route_materialization_plan_after_source_inventory_input_errors"
SELECTED_PATH = "support_contact_harder_route_materialization_plan_ready_select_docker_materializer_implementation"
NEXT_TODO = "compatibility_dataset_v3_support_contact_harder_route_docker_materialization_after_plan"

MAIN_PREDICATES = ["standing on", "lying on"]
DIAGNOSTIC_PREDICATES = ["supported by"]
FAMILY = "support_contact"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--official-materialization-dir", type=Path, default=DEFAULT_OFFICIAL_MATERIALIZATION_DIR)
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


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


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


def official_support_rows(model_safe_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in iter_jsonl(model_safe_path):
        if row.get("route_family") == FAMILY and row.get("predicate_label") in MAIN_PREDICATES:
            rows.append(row)
    return rows


def class_pair(row: dict[str, Any]) -> str:
    t_e = row.get("feature_blocks", {}).get("T_e", {})
    return f"{t_e.get('subject_class_label')}->{t_e.get('object_class_label')}"


def validate_inputs(
    source_summary: dict[str, Any],
    source_errors: list[dict[str, Any]],
    feature_rows: list[dict[str, str]],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_inventory_status", "actual": source_summary.get("status")})
    if source_summary.get("next_todo") != EXPECTED_SOURCE_NEXT:
        errors.append({"error_type": "unexpected_source_inventory_next_todo", "actual": source_summary.get("next_todo")})
    if source_summary.get("validation_errors") != 0:
        errors.append(
            {
                "error_type": "source_inventory_validation_errors_present",
                "actual": source_summary.get("validation_errors"),
            }
        )
    if source_errors:
        errors.append({"error_type": "source_inventory_validation_error_rows_present", "rows": len(source_errors)})

    decision = source_summary.get("decision", {})
    expected_booleans = {
        "source_inventory_ready": True,
        "materialization_plan_allowed": True,
        "current_official_g_e_is_hard_route_complete": False,
        "z_e_excluded_from_main_c_e": True,
        "q_e_excluded_from_main_c_e": True,
        "official_test_usage": False,
        "paper_metric_promoted": False,
    }
    for key, expected in expected_booleans.items():
        if decision.get(key) is not expected:
            errors.append({"error_type": "unexpected_source_inventory_decision", "key": key, "actual": decision.get(key)})

    required_paths = [
        args.source_inventory_dir / "geometry_evidence_availability.csv",
        args.source_inventory_dir / "shortcut_caveat.csv",
        args.source_inventory_dir / "source_split_inventory.csv",
        args.official_materialization_dir / "model_safe_view.jsonl",
        args.official_materialization_dir / "hidden_manifest.jsonl",
    ]
    for path in required_paths:
        if not path.exists():
            errors.append({"error_type": "missing_required_input", "path": rel_path(path)})

    if not feature_rows:
        errors.append({"error_type": "missing_geometry_evidence_availability_rows"})
    return errors


def support_row_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    predicates = Counter(row.get("predicate_label") for row in rows)
    labels = Counter(str(row.get("target_y")) for row in rows)
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get("cv_or_group_key"))].append(row)

    paired_ok = 0
    paired_bad = 0
    for group_rows in groups.values():
        preds = {row.get("predicate_label") for row in group_rows}
        ys = {row.get("target_y") for row in group_rows}
        if len(group_rows) == 2 and preds == set(MAIN_PREDICATES) and ys == {0, 1}:
            paired_ok += 1
        else:
            paired_bad += 1

    by_predicate_class: dict[tuple[str, str], Counter[int]] = defaultdict(Counter)
    by_class: dict[str, Counter[int]] = defaultdict(Counter)
    for row in rows:
        cp = class_pair(row)
        y = int(row.get("target_y"))
        by_predicate_class[(cp, str(row.get("predicate_label")))][y] += 1
        by_class[cp][y] += 1

    mixed_predicate_class_cells = [
        {"class_pair": cp, "predicate": pred, "label_0": counts.get(0, 0), "label_1": counts.get(1, 0)}
        for (cp, pred), counts in by_predicate_class.items()
        if counts.get(0, 0) > 0 and counts.get(1, 0) > 0
    ]
    mixed_balanced_rows = sum(2 * min(row["label_0"], row["label_1"]) for row in mixed_predicate_class_cells)
    mixed_rows = sum(row["label_0"] + row["label_1"] for row in mixed_predicate_class_cells)

    return {
        "rows": len(rows),
        "predicate_counts": dict(sorted(predicates.items())),
        "label_counts": dict(sorted(labels.items())),
        "same_pair_groups": len(groups),
        "paired_predicate_flip_groups_ok": paired_ok,
        "paired_predicate_flip_groups_bad": paired_bad,
        "class_pair_count": len(by_class),
        "predicate_class_cell_count": len(by_predicate_class),
        "mixed_predicate_class_cell_count": len(mixed_predicate_class_cells),
        "mixed_predicate_class_rows": mixed_rows,
        "mixed_predicate_class_balanced_rows": mixed_balanced_rows,
        "top_mixed_predicate_class_cells": sorted(
            mixed_predicate_class_cells,
            key=lambda row: (-(row["label_0"] + row["label_1"]), row["class_pair"], row["predicate"]),
        )[:20],
    }


def geometry_feature_contract(feature_availability: list[dict[str, str]]) -> list[dict[str, Any]]:
    availability_by_name = {row.get("required_feature"): row for row in feature_availability}
    feature_defs = [
        (
            "g_vertical_gap",
            "G_e_contact_gap",
            "surface_gap_subject_bottom_to_object_top; abs_surface_gap_subject_bottom_to_object_top; center_delta_z",
            "direct_current",
            "required_main",
            "vertical support/contact gap and order evidence",
        ),
        (
            "g_xy_support_overlap",
            "G_e_support_overlap",
            "xy_overlap_min_ratio; xy_overlap_max_ratio; optional xy_overlap_area",
            "direct_current",
            "required_main",
            "horizontal overlap needed for physical support",
        ),
        (
            "g_bottom_surface_proximity",
            "G_e_contact_gap",
            "subject_bottom_to_object_top proximity and signed/absolute gap",
            "direct_current",
            "required_main",
            "whether subject bottom is near object support surface",
        ),
        (
            "g_subject_principal_axis",
            "G_e_pose",
            "subject vertical extent ratio; OBB axes upness; flatness proxy",
            "partial_current_plus_obb_axes",
            "required_main",
            "standing vs lying needs subject pose/orientation, not only contact",
        ),
        (
            "g_support_surface_normal_alignment",
            "G_e_surface",
            "object dominant normal upness; support surface normal verticality",
            "semseg_normal_derived",
            "required_main_if_derivable",
            "whether object offers an upward support surface",
        ),
        (
            "g_surface_alignment",
            "G_e_surface",
            "subject/object normal alignment; OBB-axis alignment",
            "semseg_normal_or_obb_axis_derived",
            "required_main_if_derivable",
            "standing/lying compatibility depends on surface and pose alignment",
        ),
        (
            "g_contact_patch_ratio",
            "G_e_contact_patch",
            "support contact likelihood proxy; point xy overlap; near-surface contact patch",
            "proxy_current_true_patch_requires_extractor_update",
            "required_main_after_extractor_update",
            "distinguishes broad lying contact from point/small-area contact",
        ),
        (
            "g_local_contact_point_density",
            "G_e_contact_patch",
            "point counts near contact band using aligned PLY and segment membership",
            "requires_point_extraction",
            "required_main_after_extractor_update",
            "local evidence around the potential contact region",
        ),
        (
            "g_mesh_gap_intersection",
            "G_e_mesh_optional",
            "mesh gap, penetration, intersection, or explicit missing mask",
            "optional_mesh_extractor_or_missing_mask",
            "optional_or_qe_masked",
            "useful but not required for the first hard-route materializer",
        ),
    ]

    rows: list[dict[str, Any]] = []
    for feature, block, planned_fields, implementation, role, rationale in feature_defs:
        avail = availability_by_name.get(feature, {})
        rows.append(
            {
                "feature": feature,
                "block": block,
                "planned_fields": planned_fields,
                "implementation_status": implementation,
                "main_role": role,
                "official_available_or_derivable_rate": avail.get("official_available_or_derivable_rate", ""),
                "source_inventory_status": avail.get("official_source_status", ""),
                "train_reference_status": avail.get("train_status", ""),
                "rationale": rationale,
            }
        )
    return rows


def model_view_plan() -> list[dict[str, Any]]:
    return [
        {
            "view": "model_safe_main_no_class",
            "allowed_blocks": "T_e.predicate_text + T_e.route_family + G_e_hard_route_numeric",
            "blocked_blocks": "Z_e; Q_e; class labels; ids; GT/source/construction fields; H001 p_geom_valid",
            "purpose": "primary hard-route C_e view isolating predicate-geometry compatibility",
        },
        {
            "view": "model_safe_main_with_class_ablation",
            "allowed_blocks": "T_e.predicate_text + optional subject/object class embeddings + G_e_hard_route_numeric",
            "blocked_blocks": "Z_e; Q_e; ids; GT/source/construction fields; H001 p_geom_valid",
            "purpose": "ablation only, because predicate x class-pair shortcut is high",
        },
        {
            "view": "model_safe_geometry_only",
            "allowed_blocks": "G_e_hard_route_numeric",
            "blocked_blocks": "T_e; Z_e; Q_e; class labels; ids; provenance",
            "purpose": "geometry-only baseline and sanity check",
        },
        {
            "view": "model_safe_qe_diagnostic",
            "allowed_blocks": "Q_e extraction/missingness/observability flags only",
            "blocked_blocks": "target_y; GT/source/construction fields; Z_e",
            "purpose": "future p_obs/abstain analysis, not main C_e",
        },
        {
            "view": "hidden_manifest",
            "allowed_blocks": "GT/source provenance, scan/object ids, class pair, target generation, H001 bridge policy",
            "blocked_blocks": "not a model input",
            "purpose": "shortcut audit, pairing audit, and provenance only",
        },
    ]


def target_construction_plan(row_summary: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "target_component": "official_validation_same_pair_predicate_flip",
            "rows": row_summary["rows"],
            "groups": row_summary["same_pair_groups"],
            "paired_groups_ok": row_summary["paired_predicate_flip_groups_ok"],
            "allowed_for_main_after_schema_audit": True,
            "positive_rule": "predicate matches the official GT predicate for the directed pair",
            "negative_rule": "opposite support/contact predicate on the same directed pair geometry",
            "notes": "This is eval-only official validation materialization, not official test.",
        },
        {
            "target_component": "predicate_class_mixed_control_slice",
            "rows": row_summary["mixed_predicate_class_rows"],
            "balanced_rows": row_summary["mixed_predicate_class_balanced_rows"],
            "mixed_cells": row_summary["mixed_predicate_class_cell_count"],
            "allowed_for_main_after_schema_audit": False,
            "positive_rule": "accept/reject both exist inside the same predicate x class-pair cell",
            "negative_rule": "same cell opposite label",
            "notes": "Capacity is expected to be small; use as shortcut diagnostic, not the primary target.",
        },
        {
            "target_component": "supported_by_diagnostic",
            "rows": 0,
            "groups": 0,
            "allowed_for_main_after_schema_audit": False,
            "positive_rule": "none",
            "negative_rule": "none",
            "notes": "`supported by` remains superordinate relabel/abstain diagnostic and is excluded from main binary C_e.",
        },
    ]


def blocked_fields() -> list[dict[str, Any]]:
    fields = [
        ("target_y", "label field"),
        ("compatibility_label", "label field"),
        ("gt_predicate_label", "GT/source provenance"),
        ("gt_exact_match_flag", "GT/source provenance"),
        ("true_predicates_for_directed_pair_family", "target/source provenance"),
        ("candidate_predicate_label", "construction provenance unless duplicated as T_e.predicate_text"),
        ("counterfactual_type", "construction provenance"),
        ("target_generation_rule", "construction provenance"),
        ("source_score", "Z_e; not allowed in main C_e"),
        ("rank", "Z_e; not allowed in main C_e"),
        ("source_id", "Z_e/provenance"),
        ("h001_p_geom_valid", "H001 geometry score; hidden/diagnostic only"),
        ("h001_verification_status", "H001 hidden/diagnostic only"),
        ("Q_e", "observability/quality; excluded from main C_e"),
        ("geometry_quality_flag", "Q_e diagnostic; not main C_e"),
        ("g_e_feature_available_mask", "missingness can become Q_e shortcut; keep in hidden/Q_e diagnostic for first hard-route metric"),
        ("scan_id", "scan leakage; grouping/audit only"),
        ("subject_id", "instance leakage"),
        ("object_id", "instance leakage"),
        ("cv_or_group_key", "pair identity leakage"),
        ("class_pair", "hidden shortcut audit only"),
        ("subject_class_label", "blocked from primary no-class view; ablation only"),
        ("object_class_label", "blocked from primary no-class view; ablation only"),
    ]
    return [{"field": field, "blocked_from": "model_safe_main_no_class", "reason": reason} for field, reason in fields]


def control_plan() -> list[dict[str, Any]]:
    return [
        {
            "control_id": "S0_schema_leakage",
            "purpose": "ensure target/source/construction/id/H001/Q_e fields are absent from model_safe_main_no_class",
            "pass_condition": "0 blocked-field hits",
        },
        {
            "control_id": "S1_predicate_only",
            "purpose": "measure predicate prior without geometry",
            "pass_condition": "reported, not used as success alone; high value weakens claim",
        },
        {
            "control_id": "S2_geometry_only",
            "purpose": "test whether richer G_e alone explains standing/lying compatibility",
            "pass_condition": "must be below T_e x G_e or claim becomes geometry-only route",
        },
        {
            "control_id": "S3_plain_concat",
            "purpose": "compare against unstructured T_e + G_e feature concatenation",
            "pass_condition": "T_e x G_e interaction should improve or be more robust under controls",
        },
        {
            "control_id": "S4_TG_interaction",
            "purpose": "main predicate-geometry compatibility model",
            "pass_condition": "improves over predicate-only, geometry-only, and concat on family-wise metrics",
        },
        {
            "control_id": "S5_wrong_T_same_route",
            "purpose": "swap standing/lying predicate while keeping G_e fixed",
            "pass_condition": "score collapses or inverts relative to S4",
        },
        {
            "control_id": "S6_shuffled_G_global",
            "purpose": "verify geometry is pair-specific",
            "pass_condition": "performance degrades toward chance or below S4",
        },
        {
            "control_id": "S7_shuffled_G_within_class_pair",
            "purpose": "verify signal is not only predicate x class-pair prior",
            "pass_condition": "performance degrades materially; failure keeps support_contact diagnostic",
        },
        {
            "control_id": "S8_predicate_x_class_pair_probe",
            "purpose": "quantify the known shortcut risk",
            "pass_condition": "must be reported; if it explains the gain, no solved support/contact claim",
        },
        {
            "control_id": "S9_pose_contact_ablation",
            "purpose": "measure whether pose/contact-density features add value beyond OBB gap/overlap",
            "pass_condition": "richer G_e should outperform OBB-only on support/contact hard route",
        },
    ]


def docker_implementation_plan() -> list[dict[str, Any]]:
    return [
        {
            "item": "script",
            "planned_path": "experiments/H002_compatibility_routing/scripts/materialize_support_contact_harder_route.py",
            "requirement": "read official validation materialization, hidden manifest, 3RScan semseg/PLY/mesh assets, and write richer support/contact rows",
        },
        {
            "item": "docker_service",
            "planned_name": "h002-support-contact-hard-materialize",
            "requirement": "mount local_dataset read-only, repo writable only for experiment outputs, H001 artifacts read-only if referenced",
        },
        {
            "item": "output_root",
            "planned_path": "experiments/H002_compatibility_routing/support_contact_harder_materialization/latest/",
            "requirement": "row-level runtime output; do not copy to results/ before schema/metric review",
        },
        {
            "item": "next_audit",
            "planned_stage": "support_contact_harder_materialization_schema_audit_after_docker_materialization",
            "requirement": "blocked-field, model-safe/hidden alignment, pair integrity, feature availability, shortcut risk, and control readiness",
        },
    ]


def output_manifest_plan() -> list[dict[str, Any]]:
    return [
        {"file": "candidate_rows.jsonl", "role": "full richer support/contact rows with labels/provenance", "model_safe": False},
        {"file": "model_safe_main_no_class.jsonl", "role": "T_e predicate + richer predicate-independent G_e only", "model_safe": True},
        {"file": "model_safe_main_with_class_ablation.jsonl", "role": "optional class-semantic ablation view", "model_safe": True},
        {"file": "model_safe_geometry_only.jsonl", "role": "G_e-only baseline view", "model_safe": True},
        {"file": "model_safe_qe_diagnostic.jsonl", "role": "Q_e/missingness/observability diagnostic view, not main C_e", "model_safe": True},
        {"file": "hidden_manifest.jsonl", "role": "GT/source/construction/class-pair/provenance audit fields", "model_safe": False},
        {"file": "group_manifest.jsonl", "role": "same-pair predicate-flip integrity and cv/group keys", "model_safe": False},
        {"file": "feature_availability.csv", "role": "per-feature coverage and missingness summary", "model_safe": False},
        {"file": "schema_precheck.json", "role": "row counts, blocked-field hits, class-pair shortcut precheck", "model_safe": False},
        {"file": "validation_errors.jsonl", "role": "runtime validation errors", "model_safe": False},
    ]


def promotion_gate() -> list[dict[str, Any]]:
    return [
        {
            "gate": "G0_materialization_integrity",
            "required": "3178 official validation support/contact rows, 1589 paired groups, 0 validation errors",
            "failure_action": "do not run metrics",
        },
        {
            "gate": "G1_richer_Ge_availability",
            "required": "direct OBB features complete; normal/pose/contact-density features materialized or explicitly masked",
            "failure_action": "keep OBB-only diagnostic status",
        },
        {
            "gate": "G2_schema_separation",
            "required": "0 blocked-field hits in model_safe_main_no_class",
            "failure_action": "repair schema before metrics",
        },
        {
            "gate": "G3_shortcut_control",
            "required": "predicate x class-pair probe reported; within-class-pair shuffled-G control included",
            "failure_action": "support_contact remains diagnostic/failure-taxonomy",
        },
        {
            "gate": "G4_interaction_evidence",
            "required": "T_e x G_e improves over predicate-only, geometry-only, and plain concat; wrong-T and shuffled-G controls degrade",
            "failure_action": "do not promote support_contact as main compatibility-route evidence",
        },
        {
            "gate": "G5_claim_boundary",
            "required": "no official test use; no source reranking or p_obs/p_rel claim from this materializer",
            "failure_action": "block paper-result promotion",
        },
    ]


def materialization_contract(row_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset_id": "h002_support_contact_harder_route_official_validation_v1",
        "source_artifact": rel_path(DEFAULT_SOURCE_INVENTORY_DIR),
        "next_runner": NEXT_TODO,
        "split_policy": {
            "official_validation": "eval_only",
            "official_test": "unused",
            "train_point_multiview": "reference_template_only",
        },
        "main_predicates": MAIN_PREDICATES,
        "diagnostic_predicates": DIAGNOSTIC_PREDICATES,
        "primary_design": {
            "rows": row_summary["rows"],
            "groups": row_summary["same_pair_groups"],
            "group_definition": "same scan, directed subject/object pair, support_contact route; two rows differ by standing/lying predicate",
            "positive_rule": "candidate predicate matches official GT support/contact predicate",
            "negative_rule": "opposite standing/lying predicate on the same G_e",
            "main_view": "model_safe_main_no_class",
        },
        "controlled_capacity": {
            "predicate_class_cell_count": row_summary["predicate_class_cell_count"],
            "mixed_predicate_class_cell_count": row_summary["mixed_predicate_class_cell_count"],
            "mixed_predicate_class_rows": row_summary["mixed_predicate_class_rows"],
            "mixed_predicate_class_balanced_rows": row_summary["mixed_predicate_class_balanced_rows"],
            "interpretation": "within predicate x class-pair mixed capacity is small; use as diagnostic, not primary target",
        },
        "model_safe_policy": {
            "main_c_e_inputs": ["T_e.predicate_text", "G_e_hard_route_numeric"],
            "z_e_policy": "excluded from main C_e",
            "q_e_policy": "excluded from main C_e; separate diagnostic view only",
            "class_policy": "blocked from primary no-class view; optional ablation only",
            "h001_policy": "p_geom_valid hidden/diagnostic only, never main G_e",
        },
    }


def next_runner_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "selected_path": SELECTED_PATH,
        "purpose": "Implement Docker materialization for richer official-validation support/contact hard-route G_e.",
        "must_create": [
            "candidate_rows.jsonl",
            "model_safe_main_no_class.jsonl",
            "model_safe_main_with_class_ablation.jsonl",
            "model_safe_geometry_only.jsonl",
            "model_safe_qe_diagnostic.jsonl",
            "hidden_manifest.jsonl",
            "group_manifest.jsonl",
            "feature_availability.csv",
            "schema_precheck.json",
            "validation_errors.jsonl",
        ],
        "must_preserve": [
            "official validation is eval-only",
            "official test unused",
            "T_e + G_e only for primary C_e",
            "Z_e and Q_e excluded from primary C_e",
            "class labels excluded from primary no-class view",
            "hidden construction/provenance fields excluded from model-safe views",
        ],
        "must_not_do": [
            "do not run metrics in the materializer",
            "do not promote support_contact as solved",
            "do not use H001 p_geom_valid as main G_e",
            "do not use source score/rank in C_e",
        ],
    }


def build_report(summary: dict[str, Any]) -> str:
    rows = summary["plan_counts"]
    caps = summary["controlled_capacity"]
    return "\n".join(
        [
            "# H002 Support/Contact Harder Route Materialization Plan After Source Inventory",
            "",
            "## Status",
            "",
            "```text",
            f"artifact_root = {summary['output_paths']['artifact_root']}",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"validation_errors = {summary['validation_errors']}",
            f"next_todo = {summary['next_todo']}",
            "```",
            "",
            "## Frozen Materialization Scope",
            "",
            "```text",
            f"official_validation_rows = {rows['official_validation_rows']}",
            f"same_pair_predicate_flip_groups = {rows['same_pair_predicate_flip_groups']}",
            f"paired_groups_ok = {rows['paired_groups_ok']}",
            f"mixed_predicate_class_cells = {caps['mixed_predicate_class_cell_count']}",
            f"mixed_predicate_class_balanced_rows = {caps['mixed_predicate_class_balanced_rows']}",
            "official_test_used = false",
            "paper_metric_promoted = false",
            "```",
            "",
            "## Judgment",
            "",
            "Proceed to Docker materializer implementation, but do not run a metric yet. The next materializer",
            "should replace the current OBB-proxy-only support/contact `G_e` with richer predicate-independent",
            "pose/contact/surface evidence. The primary model-safe view must isolate `T_e + G_e`; `Z_e`,",
            "`Q_e`, class labels, H001 `p_geom_valid`, GT/source fields, and construction fields remain out.",
            "",
            "The known weakness is not fixed by this plan: `predicate x class-pair` is a high-risk shortcut.",
            "Therefore support/contact remains diagnostic until the richer materialization passes schema,",
            "shortcut, wrong-T, shuffled-G, and class-pair-aware controls.",
            "",
            "## Next",
            "",
            "```text",
            NEXT_TODO,
            "```",
        ]
    ) + "\n"


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source_summary_path = args.source_inventory_dir / "summary.json"
    source_summary = read_json(source_summary_path) if source_summary_path.exists() else {}
    source_errors = read_jsonl(args.source_inventory_dir / "validation_errors.jsonl")
    feature_availability = read_csv(args.source_inventory_dir / "geometry_evidence_availability.csv")
    validation_errors = validate_inputs(source_summary, source_errors, feature_availability, args)

    official_rows: list[dict[str, Any]] = []
    model_safe_path = args.official_materialization_dir / "model_safe_view.jsonl"
    if model_safe_path.exists():
        official_rows = official_support_rows(model_safe_path)
    row_summary = support_row_summary(official_rows) if official_rows else {
        "rows": 0,
        "predicate_counts": {},
        "label_counts": {},
        "same_pair_groups": 0,
        "paired_predicate_flip_groups_ok": 0,
        "paired_predicate_flip_groups_bad": 0,
        "class_pair_count": 0,
        "predicate_class_cell_count": 0,
        "mixed_predicate_class_cell_count": 0,
        "mixed_predicate_class_rows": 0,
        "mixed_predicate_class_balanced_rows": 0,
        "top_mixed_predicate_class_cells": [],
    }

    if row_summary["rows"] != source_summary.get("decision", {}).get("official_validation_rows"):
        validation_errors.append(
            {
                "error_type": "official_support_row_count_mismatch",
                "actual": row_summary["rows"],
                "expected": source_summary.get("decision", {}).get("official_validation_rows"),
            }
        )
    if row_summary["paired_predicate_flip_groups_bad"] != 0:
        validation_errors.append(
            {
                "error_type": "paired_predicate_flip_group_integrity_failed",
                "bad_groups": row_summary["paired_predicate_flip_groups_bad"],
            }
        )

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    selected_path = "blocked_by_input_validation_errors" if validation_errors else SELECTED_PATH
    next_todo = EXPECTED_SOURCE_NEXT if validation_errors else NEXT_TODO

    output_paths = {
        "artifact_root": args.output_dir,
        "summary": args.output_dir / "summary.json",
        "materialization_contract": args.output_dir / "materialization_contract.json",
        "geometry_feature_contract": args.output_dir / "geometry_feature_contract.csv",
        "model_view_plan": args.output_dir / "model_view_plan.csv",
        "target_construction_plan": args.output_dir / "target_construction_plan.csv",
        "blocked_fields": args.output_dir / "blocked_fields.csv",
        "control_plan": args.output_dir / "control_plan.csv",
        "docker_implementation_plan": args.output_dir / "docker_implementation_plan.csv",
        "output_manifest_plan": args.output_dir / "output_manifest_plan.csv",
        "promotion_gate": args.output_dir / "promotion_gate.csv",
        "mixed_predicate_class_cells": args.output_dir / "mixed_predicate_class_cells.csv",
        "next_runner_contract": args.output_dir / "next_runner_contract.json",
        "report": args.output_dir / "report.md",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }

    geometry_rows = geometry_feature_contract(feature_availability)
    model_rows = model_view_plan()
    target_rows = target_construction_plan(row_summary)
    blocked_rows = blocked_fields()
    control_rows = control_plan()
    docker_rows = docker_implementation_plan()
    manifest_rows = output_manifest_plan()
    gate_rows = promotion_gate()
    contract = materialization_contract(row_summary)
    next_contract = next_runner_contract()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "input_paths": {
            "source_inventory_dir": rel_path(args.source_inventory_dir),
            "source_inventory_summary": rel_path(source_summary_path),
            "official_materialization_dir": rel_path(args.official_materialization_dir),
            "official_model_safe_view": rel_path(model_safe_path),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "plan_counts": {
            "official_validation_rows": row_summary["rows"],
            "same_pair_predicate_flip_groups": row_summary["same_pair_groups"],
            "paired_groups_ok": row_summary["paired_predicate_flip_groups_ok"],
            "paired_groups_bad": row_summary["paired_predicate_flip_groups_bad"],
            "predicate_counts": row_summary["predicate_counts"],
            "label_counts": row_summary["label_counts"],
            "class_pair_count": row_summary["class_pair_count"],
        },
        "controlled_capacity": {
            "predicate_class_cell_count": row_summary["predicate_class_cell_count"],
            "mixed_predicate_class_cell_count": row_summary["mixed_predicate_class_cell_count"],
            "mixed_predicate_class_rows": row_summary["mixed_predicate_class_rows"],
            "mixed_predicate_class_balanced_rows": row_summary["mixed_predicate_class_balanced_rows"],
            "interpretation": "too small for primary metric; use as shortcut diagnostic/control slice",
        },
        "decision": {
            "materialization_plan_ready": not bool(validation_errors),
            "docker_materializer_next": not bool(validation_errors),
            "current_official_g_e_is_hard_route_complete": False,
            "paper_metric_promoted": False,
            "official_test_usage": False,
            "support_contact_solved_claim_allowed": False,
            "z_e_excluded_from_main_c_e": True,
            "q_e_excluded_from_main_c_e": True,
            "class_labels_excluded_from_primary_view": True,
        },
        "boundary": {
            "materializes_rows": False,
            "runs_new_metric": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["materialization_contract"], contract)
    write_csv(output_paths["geometry_feature_contract"], geometry_rows)
    write_csv(output_paths["model_view_plan"], model_rows)
    write_csv(output_paths["target_construction_plan"], target_rows)
    write_csv(output_paths["blocked_fields"], blocked_rows)
    write_csv(output_paths["control_plan"], control_rows)
    write_csv(output_paths["docker_implementation_plan"], docker_rows)
    write_csv(output_paths["output_manifest_plan"], manifest_rows)
    write_csv(output_paths["promotion_gate"], gate_rows)
    write_csv(output_paths["mixed_predicate_class_cells"], row_summary["top_mixed_predicate_class_cells"])
    write_json(output_paths["next_runner_contract"], next_contract)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")
    write_jsonl(output_paths["validation_errors"], validation_errors)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
