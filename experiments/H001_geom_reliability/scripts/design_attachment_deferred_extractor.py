#!/usr/bin/env python3
"""Freeze the attachment-deferred evidence extractor contract.

This is a design/contract step only. It does not read point clouds, does not
assign verification status, and does not run metrics. The goal is to make the
future attachment evidence extractor auditable before verifier/calibration work
starts.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_attachment_deferred_extractor_contract_v1"
STATUS = "attachment_deferred_extractor_contract_ready_no_extraction"
TARGET_FAMILY = "attachment_deferred"
PREDICATE_LABELS = ["attached to", "hanging on", "connected to"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def output_schema() -> dict[str, Any]:
    surface_type = ["wall", "ceiling", "floor", "furniture", "fixture", "object_part", "unknown"]
    normal_class = ["horizontal_up", "horizontal_down", "vertical", "slanted", "unknown"]
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "H001 attachment-deferred evidence row",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "extractor_version",
            "row_id",
            "source_name",
            "scan_id",
            "subgraph_id",
            "subject_id",
            "object_id",
            "subject_label",
            "object_label",
            "predicate_label",
            "predicate_family",
            "extractor_status",
            "subtype_hint",
            "geometry_available",
            "obb_evidence",
            "point_contact_evidence",
            "surface_evidence",
            "gravity_evidence",
            "contradictory_support_evidence",
            "affordance_context",
            "quality_flags",
            "missing_fields",
            "notes",
        ],
        "properties": {
            "schema_version": {"const": "h001_attachment_deferred_evidence_row_v1"},
            "extractor_version": {"type": "string"},
            "row_id": {"type": "string"},
            "source_name": {"enum": ["vlsat_closed_set", "open3dsg_ov", "gt_positive", "counterfactual"]},
            "scan_id": {"type": "string"},
            "subgraph_id": {"type": "string"},
            "subject_id": {"type": ["integer", "string"]},
            "object_id": {"type": ["integer", "string"]},
            "subject_label": {"type": ["string", "null"]},
            "object_label": {"type": ["string", "null"]},
            "predicate_label": {"enum": PREDICATE_LABELS},
            "predicate_family": {"const": TARGET_FAMILY},
            "extractor_status": {
                "enum": [
                    "ready",
                    "partial",
                    "missing_geometry",
                    "missing_points",
                    "unsupported_label",
                    "invalid_object_pair",
                ]
            },
            "subtype_hint": {
                "enum": [
                    "attached_to_vertical_or_overhead_surface",
                    "attached_to_furniture_or_fixture",
                    "ambiguous_functional_attachment",
                    "hanging_from_vertical_surface",
                    "hanging_from_overhead_or_fixture",
                    "ambiguous_draped_or_occluded_hanging",
                    "connected_adjacent_or_contiguous",
                    "connected_by_fixture_or_part",
                    "ambiguous_functional_connection",
                    "unknown",
                ]
            },
            "geometry_available": {
                "type": "object",
                "additionalProperties": False,
                "required": ["obb", "points", "surface_candidates", "normals"],
                "properties": {
                    "obb": {"type": "boolean"},
                    "points": {"type": "boolean"},
                    "surface_candidates": {"type": "boolean"},
                    "normals": {"type": "boolean"},
                },
            },
            "obb_evidence": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "distance_3d_m",
                    "distance_xy_m",
                    "normalized_distance_3d",
                    "normalized_distance_xy",
                    "projected_xy_overlap",
                    "vertical_gap_m",
                    "center_delta_z_m",
                ],
                "properties": {
                    key: {"type": ["number", "null"]}
                    for key in [
                        "distance_3d_m",
                        "distance_xy_m",
                        "normalized_distance_3d",
                        "normalized_distance_xy",
                        "projected_xy_overlap",
                        "vertical_gap_m",
                        "center_delta_z_m",
                    ]
                },
            },
            "point_contact_evidence": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "subject_point_count",
                    "object_point_count",
                    "min_point_distance_m",
                    "near_contact_point_count",
                    "near_contact_threshold_m",
                    "contact_patch_extent_m2",
                    "contact_patch_score",
                ],
                "properties": {
                    "subject_point_count": {"type": ["integer", "null"]},
                    "object_point_count": {"type": ["integer", "null"]},
                    "min_point_distance_m": {"type": ["number", "null"]},
                    "near_contact_point_count": {"type": ["integer", "null"]},
                    "near_contact_threshold_m": {"type": ["number", "null"]},
                    "contact_patch_extent_m2": {"type": ["number", "null"]},
                    "contact_patch_score": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                },
            },
            "surface_evidence": {
                "type": "object",
                "additionalProperties": False,
                "required": ["selected_surface_type", "selected_surface_normal_class", "candidate_count", "candidates"],
                "properties": {
                    "selected_surface_type": {"enum": surface_type},
                    "selected_surface_normal_class": {"enum": normal_class},
                    "candidate_count": {"type": "integer", "minimum": 0},
                    "candidates": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "surface_id",
                                "surface_type",
                                "normal_class",
                                "normal_xyz",
                                "distance_m",
                                "projected_overlap_ratio",
                                "point_contact_count",
                                "evidence_source",
                            ],
                            "properties": {
                                "surface_id": {"type": ["string", "null"]},
                                "surface_type": {"enum": surface_type},
                                "normal_class": {"enum": normal_class},
                                "normal_xyz": {
                                    "type": ["array", "null"],
                                    "items": {"type": "number"},
                                    "minItems": 3,
                                    "maxItems": 3,
                                },
                                "distance_m": {"type": ["number", "null"]},
                                "projected_overlap_ratio": {
                                    "type": ["number", "null"],
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "point_contact_count": {"type": ["integer", "null"]},
                                "evidence_source": {
                                    "enum": [
                                        "segmented_points",
                                        "obb_plane_proxy",
                                        "object_label_prior",
                                        "missing",
                                    ]
                                },
                            },
                        },
                    },
                },
            },
            "gravity_evidence": {
                "type": "object",
                "additionalProperties": False,
                "required": ["floor_clearance_m", "near_vertical_or_overhead_surface", "hanging_geometry_score"],
                "properties": {
                    "floor_clearance_m": {"type": ["number", "null"]},
                    "near_vertical_or_overhead_surface": {"type": ["boolean", "null"]},
                    "hanging_geometry_score": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                },
            },
            "contradictory_support_evidence": {
                "type": "object",
                "additionalProperties": False,
                "required": ["floor_or_table_supported", "support_explanation_score", "reason_codes"],
                "properties": {
                    "floor_or_table_supported": {"type": ["boolean", "null"]},
                    "support_explanation_score": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                    "reason_codes": {"type": "array", "items": {"type": "string"}},
                },
            },
            "affordance_context": {
                "type": "object",
                "additionalProperties": False,
                "required": ["class_pair_prior", "class_pair_prior_source", "allowed_as_proof"],
                "properties": {
                    "class_pair_prior": {"enum": ["plausible", "implausible", "unknown"]},
                    "class_pair_prior_source": {"enum": ["fixed_list", "none"]},
                    "allowed_as_proof": {"const": False},
                },
            },
            "quality_flags": {"type": "array", "items": {"type": "string"}},
            "missing_fields": {"type": "array", "items": {"type": "string"}},
            "notes": {"type": "array", "items": {"type": "string"}},
        },
    }


def field_catalog() -> dict[str, Any]:
    return {
        "schema_version": "h001_attachment_deferred_field_catalog_v1",
        "status": STATUS,
        "principles": [
            "Extractor emits evidence only; verifier emits satisfied/violated/uncertain later.",
            "Object class affordance is optional context and must never be the sole proof.",
            "Missing or ambiguous surface evidence should become partial/missing flags, not a hidden violation.",
            "Exact predicate labels remain separate for recall; family grouping is only for evidence extraction.",
        ],
        "field_groups": [
            {
                "name": "identity",
                "purpose": "Preserve row/source/object identity across VL-SAT, Open3DSG, GT positives, and counterfactuals.",
                "required_fields": [
                    "row_id",
                    "source_name",
                    "scan_id",
                    "subgraph_id",
                    "subject_id",
                    "object_id",
                    "predicate_label",
                    "predicate_family",
                ],
            },
            {
                "name": "obb_evidence",
                "purpose": "Reuse existing semseg OBB geometry for distance, overlap, and vertical context.",
                "required_fields": [
                    "distance_3d_m",
                    "distance_xy_m",
                    "normalized_distance_3d",
                    "normalized_distance_xy",
                    "projected_xy_overlap",
                    "vertical_gap_m",
                    "center_delta_z_m",
                ],
            },
            {
                "name": "point_contact_evidence",
                "purpose": "Estimate local near-contact and contact patch evidence from segmented points when available.",
                "required_fields": [
                    "subject_point_count",
                    "object_point_count",
                    "min_point_distance_m",
                    "near_contact_point_count",
                    "near_contact_threshold_m",
                    "contact_patch_extent_m2",
                    "contact_patch_score",
                ],
            },
            {
                "name": "surface_evidence",
                "purpose": "Identify plausible wall, ceiling, furniture, fixture, or object-part attachment surfaces.",
                "required_fields": [
                    "selected_surface_type",
                    "selected_surface_normal_class",
                    "candidate_count",
                    "candidates",
                ],
            },
            {
                "name": "gravity_and_contradiction",
                "purpose": "Represent hanging plausibility and alternative floor/table support explanations.",
                "required_fields": [
                    "floor_clearance_m",
                    "near_vertical_or_overhead_surface",
                    "hanging_geometry_score",
                    "floor_or_table_supported",
                    "support_explanation_score",
                ],
            },
            {
                "name": "affordance_context",
                "purpose": "Record class-pair plausibility only as context for later audit/ablation.",
                "required_fields": [
                    "class_pair_prior",
                    "class_pair_prior_source",
                    "allowed_as_proof",
                ],
            },
        ],
        "forbidden_extractor_outputs": [
            "verification_status",
            "p_geom_valid",
            "satisfied",
            "violated",
            "uncertain_as_decision",
            "recall_credit",
            "reranked_score",
        ],
    }


def subtype_policy() -> dict[str, Any]:
    return {
        "schema_version": "h001_attachment_deferred_subtype_policy_v1",
        "status": STATUS,
        "predicate_to_subtype_hints": {
            "attached to": [
                {
                    "subtype_hint": "attached_to_vertical_or_overhead_surface",
                    "required_evidence": [
                        "near vertical/overhead candidate surface",
                        "small object-to-surface distance",
                        "local near-contact or contact patch",
                    ],
                    "uncertain_cases": [
                        "hidden fastener or occluded contact",
                        "surface normal unavailable",
                        "object class suggests attachment but geometry is weak",
                    ],
                },
                {
                    "subtype_hint": "attached_to_furniture_or_fixture",
                    "required_evidence": [
                        "near furniture/fixture/object-part surface",
                        "small object-to-surface distance",
                        "local contact or projected overlap",
                    ],
                    "uncertain_cases": ["functional attachment without visible contact"],
                },
                {
                    "subtype_hint": "ambiguous_functional_attachment",
                    "required_evidence": ["class/context suggests attachment but geometry is not decisive"],
                    "uncertain_cases": ["always uncertain until visual or stronger geometry evidence exists"],
                },
            ],
            "hanging on": [
                {
                    "subtype_hint": "hanging_from_vertical_surface",
                    "required_evidence": [
                        "subject near vertical surface",
                        "subject not primarily floor/table supported",
                        "gravity cue consistent with hanging",
                    ],
                    "uncertain_cases": ["draped object", "occluded contact point", "normal unavailable"],
                },
                {
                    "subtype_hint": "hanging_from_overhead_or_fixture",
                    "required_evidence": [
                        "subject near overhead/fixture candidate",
                        "positive floor clearance or suspended geometry",
                        "no stronger floor/table support explanation",
                    ],
                    "uncertain_cases": ["thin wires or small hooks not visible in point cloud"],
                },
                {
                    "subtype_hint": "ambiguous_draped_or_occluded_hanging",
                    "required_evidence": ["partial geometry only"],
                    "uncertain_cases": ["always uncertain until visual or stronger geometry evidence exists"],
                },
            ],
            "connected to": [
                {
                    "subtype_hint": "connected_adjacent_or_contiguous",
                    "required_evidence": [
                        "very small object-object distance",
                        "local contact or near-contact",
                        "spatial continuity along boundary",
                    ],
                    "uncertain_cases": ["connection hidden by occlusion"],
                },
                {
                    "subtype_hint": "connected_by_fixture_or_part",
                    "required_evidence": [
                        "fixture/object-part candidate nearby",
                        "small distance to intermediate support/part",
                    ],
                    "uncertain_cases": ["intermediate part not segmented as a separate object"],
                },
                {
                    "subtype_hint": "ambiguous_functional_connection",
                    "required_evidence": ["class/context suggests connection but physical contact is not visible"],
                    "uncertain_cases": ["always uncertain until visual or stronger geometry evidence exists"],
                },
            ],
        },
    }


def extraction_plan() -> dict[str, Any]:
    return {
        "schema_version": "h001_attachment_deferred_extraction_plan_v1",
        "status": STATUS,
        "inputs": {
            "prediction_jsonl": "VL-SAT/Open3DSG/GT/counterfactual rows with scan_id, subgraph_id, subject_id, object_id, predicate_label",
            "obb_geometry": "existing semseg_obb_v0 features from the row-preserving geometry join",
            "segmented_points": "labels.instances.annotated.v2.ply or staged point evidence when available",
            "object_metadata": "object labels and object ids from 3DSSG/3RScan context",
            "optional_visual_context": "not used by extractor contract; reserved for later audit only",
        },
        "phases": [
            {
                "id": "E1",
                "name": "identity_and_obb_pass_through",
                "description": "Preserve source row identity and copy OBB distance/overlap/vertical features.",
                "output_groups": ["identity", "obb_evidence", "geometry_available"],
            },
            {
                "id": "E2",
                "name": "local_point_contact_estimation",
                "description": "Estimate min point distance, near-contact counts, and contact patch proxy for the subject-object pair.",
                "output_groups": ["point_contact_evidence", "quality_flags"],
            },
            {
                "id": "E3",
                "name": "surface_candidate_estimation",
                "description": "Collect wall/ceiling/furniture/fixture/object-part surface candidates and classify normals.",
                "output_groups": ["surface_evidence", "quality_flags"],
            },
            {
                "id": "E4",
                "name": "gravity_and_contradictory_support_cues",
                "description": "Compute hanging plausibility and competing floor/table support explanation fields.",
                "output_groups": ["gravity_evidence", "contradictory_support_evidence"],
            },
            {
                "id": "E5",
                "name": "subtype_hint_and_context",
                "description": "Assign a conservative subtype hint and class-pair affordance context without making a validity decision.",
                "output_groups": ["subtype_hint", "affordance_context", "missing_fields", "notes"],
            },
        ],
        "next_implementation_gate": "G1b_attachment_evidence_extractor_dry_run",
        "metric_block": "Do not run source metrics from this contract. Metrics require verifier/calibration gates after extractor implementation.",
    }


def validation_plan() -> dict[str, Any]:
    return {
        "schema_version": "h001_attachment_deferred_validation_plan_v1",
        "status": STATUS,
        "contract_checks": [
            "Every output row validates against output_schema.json.",
            "Row count is preserved from the selected attachment input rows.",
            "No forbidden verifier/metric fields appear in extractor output.",
            "Every row has source identity and exact predicate label.",
            "Rows without points or surface candidates use partial/missing statuses and missing_fields.",
        ],
        "sanity_checks_before_verifier": [
            "Per-label extractor_status counts for attached/hanging/connected are reported.",
            "Surface type distribution is reported by predicate label.",
            "Near-contact availability is reported by source and label.",
            "Affordance-only rows are counted separately and cannot be treated as valid.",
            "A small visual sanity queue is created before any hard violation policy is frozen.",
        ],
        "required_reports": [
            "manifest.json",
            "schema_validation_summary.json",
            "field_coverage.json",
            "report.md",
        ],
    }


def example_row() -> dict[str, Any]:
    return {
        "schema_version": "h001_attachment_deferred_evidence_row_v1",
        "extractor_version": "h001_attachment_deferred_extractor_v1",
        "row_id": "example_scan::example_subgraph::12::34::attached to",
        "source_name": "gt_positive",
        "scan_id": "example_scan",
        "subgraph_id": "example_subgraph",
        "subject_id": 12,
        "object_id": 34,
        "subject_label": "picture",
        "object_label": "wall",
        "predicate_label": "attached to",
        "predicate_family": TARGET_FAMILY,
        "extractor_status": "ready",
        "subtype_hint": "attached_to_vertical_or_overhead_surface",
        "geometry_available": {
            "obb": True,
            "points": True,
            "surface_candidates": True,
            "normals": True,
        },
        "obb_evidence": {
            "distance_3d_m": 0.05,
            "distance_xy_m": 0.03,
            "normalized_distance_3d": 0.08,
            "normalized_distance_xy": 0.05,
            "projected_xy_overlap": 0.31,
            "vertical_gap_m": 0.0,
            "center_delta_z_m": 0.15,
        },
        "point_contact_evidence": {
            "subject_point_count": 420,
            "object_point_count": 1500,
            "min_point_distance_m": 0.018,
            "near_contact_point_count": 36,
            "near_contact_threshold_m": 0.05,
            "contact_patch_extent_m2": 0.012,
            "contact_patch_score": 0.72,
        },
        "surface_evidence": {
            "selected_surface_type": "wall",
            "selected_surface_normal_class": "vertical",
            "candidate_count": 1,
            "candidates": [
                {
                    "surface_id": "object:34",
                    "surface_type": "wall",
                    "normal_class": "vertical",
                    "normal_xyz": [1.0, 0.0, 0.0],
                    "distance_m": 0.018,
                    "projected_overlap_ratio": 0.31,
                    "point_contact_count": 36,
                    "evidence_source": "segmented_points",
                }
            ],
        },
        "gravity_evidence": {
            "floor_clearance_m": 1.2,
            "near_vertical_or_overhead_surface": True,
            "hanging_geometry_score": 0.0,
        },
        "contradictory_support_evidence": {
            "floor_or_table_supported": False,
            "support_explanation_score": 0.0,
            "reason_codes": [],
        },
        "affordance_context": {
            "class_pair_prior": "plausible",
            "class_pair_prior_source": "fixed_list",
            "allowed_as_proof": False,
        },
        "quality_flags": [],
        "missing_fields": [],
        "notes": ["Example row only; not extracted from data."],
    }


def commands_md() -> str:
    return """# Attachment Deferred Evidence Extractor Contract Commands

Run from the repository root.

```bash
docker build -t h001-geom-reliability:latest -f experiments/H001_geom_reliability/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm attachment_deferred_extractor_contract
```

This command creates a design/contract artifact only. It does not read point
clouds, assign verification status, fit calibration, or run source metrics.

Next implementation gate:

```text
G1b_attachment_evidence_extractor_dry_run
```
"""


def report_md(manifest: dict[str, Any]) -> str:
    return f"""# Attachment Deferred Evidence Extractor Contract

Status: `{manifest['status']}`
Created at: `{manifest['created_at']}`

## Claim Boundary

This is a G1 design artifact, not a verifier and not metric evidence. It keeps
`attachment_deferred` outside the current AAAI main claim.

## Contract Files

- `extractor_contract.json`
- `output_schema.json`
- `field_catalog.json`
- `subtype_policy.json`
- `extraction_plan.json`
- `validation_plan.json`
- `example_row.json`
- `commands.md`

## Required Evidence Groups

- identity-preserving source row fields
- reusable OBB distance/overlap/vertical evidence
- local point contact and contact patch proxies
- surface candidate type and surface normal class
- gravity/hanging cues
- contradictory floor/table support cues
- object-class affordance as context only, never as proof

## Explicit Non-Outputs

The extractor must not emit `verification_status`, `p_geom_valid`, recall
credit, or reranking scores. Those belong to later verifier, calibration, and
metric gates.

## Next Gate

`{manifest['next_gate']}`

## Blockers Before Source Metrics

""" + "\n".join(f"- `{item}`" for item in manifest["blockers"]) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--scope-audit-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/attachment_deferred/scope_audit"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/attachment_deferred/evidence_extractor"),
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    scope_dir = args.scope_audit_dir if args.scope_audit_dir.is_absolute() else repo_root / args.scope_audit_dir
    out = args.out if args.out.is_absolute() else repo_root / args.out

    scope_manifest_path = scope_dir / "manifest.json"
    scope_schema_path = scope_dir / "evidence_schema.json"
    if not scope_manifest_path.exists() or not scope_schema_path.exists():
        raise FileNotFoundError(f"missing scope audit inputs under {scope_dir}")

    scope_manifest = read_json(scope_manifest_path)
    scope_schema = read_json(scope_schema_path)
    if scope_manifest.get("status") != "attachment_deferred_scope_schema_ready_no_metric_execution":
        raise ValueError(f"unexpected scope audit status: {scope_manifest.get('status')}")

    schema = output_schema()
    catalog = field_catalog()
    subtype = subtype_policy()
    plan = extraction_plan()
    validation = validation_plan()
    example = example_row()

    contract = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "target_family": TARGET_FAMILY,
        "predicate_labels": PREDICATE_LABELS,
        "scope_audit": {
            "path": relpath(repo_root, scope_manifest_path),
            "status": scope_manifest["status"],
            "attachment_deferred_gt_rows": scope_manifest["denominator"]["attachment_deferred_gt_rows"],
            "expanded_candidate_denominator": scope_manifest["denominator"]["expanded_candidate_denominator"],
            "vlsat_candidate_rows": scope_manifest["source_prediction_rows"]["vlsat"]["attachment_deferred_rows"],
            "open3dsg_candidate_rows": scope_manifest["source_prediction_rows"]["open3dsg"]["attachment_deferred_rows"],
        },
        "scope_schema_source": {
            "path": relpath(repo_root, scope_schema_path),
            "status": scope_schema["status"],
        },
        "output_artifacts": {
            "output_schema": "output_schema.json",
            "field_catalog": "field_catalog.json",
            "subtype_policy": "subtype_policy.json",
            "extraction_plan": "extraction_plan.json",
            "validation_plan": "validation_plan.json",
            "example_row": "example_row.json",
        },
        "forbidden_extractor_outputs": catalog["forbidden_extractor_outputs"],
        "next_gate": "G1b_attachment_evidence_extractor_dry_run",
        "blockers": [
            "extractor_implementation_not_written",
            "point_contact_estimator_not_validated",
            "surface_candidate_estimator_not_validated",
            "normal_classification_not_validated",
            "gravity_and_contradictory_support_cues_not_validated",
            "schema_validation_dry_run_not_executed",
            "attachment_verifier_policy_not_frozen",
            "train_dev_calibration_not_built",
            "source_metrics_not_run",
        ],
    }

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "created_at": utc_now(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "artifact_type": "design_contract_only",
            "metric_evidence": False,
            "verifier_evidence": False,
        },
        "inputs": {
            "scope_manifest": relpath(repo_root, scope_manifest_path),
            "scope_evidence_schema": relpath(repo_root, scope_schema_path),
        },
        "outputs": contract["output_artifacts"],
        "next_gate": contract["next_gate"],
        "blockers": contract["blockers"],
    }

    ensure_dir(out)
    write_json(out / "manifest.json", manifest)
    write_json(out / "extractor_contract.json", contract)
    write_json(out / "output_schema.json", schema)
    write_json(out / "field_catalog.json", catalog)
    write_json(out / "subtype_policy.json", subtype)
    write_json(out / "extraction_plan.json", plan)
    write_json(out / "validation_plan.json", validation)
    write_json(out / "example_row.json", example)
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest))

    print(json.dumps({"status": STATUS, "out": str(out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
