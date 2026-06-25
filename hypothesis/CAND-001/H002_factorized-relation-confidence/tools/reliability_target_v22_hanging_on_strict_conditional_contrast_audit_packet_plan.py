#!/usr/bin/env python3
"""Plan neutral audit packets for H002 v22 hanging-on strict candidates."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_SOURCE_INVENTORY_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory"
DEFAULT_CANDIDATE_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan"

EXPECTED_SOURCE_INVENTORY_STATUS = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_source_inventory_ready_for_audit_packet_plan"
EXPECTED_SOURCE_INVENTORY_NEXT = "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan"
EXPECTED_CANDIDATE_STATUS = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_candidate_mining_ready_for_source_inventory"

STATUS_READY = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan_ready_for_materialization"
STATUS_ERRORS = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_plan_validation_errors"
NEXT_TODO_READY = "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_materialization"

TARGET_ROWS = 240
ROLE_ACCEPT = "accept_proxy_supported_candidate"
ROLE_REJECT = "reject_proxy_contradicted_candidate"

VISIBLE_FIELDS = [
    "packet_id",
    "blind_review_id",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "packet_role",
    "evidence_tier",
    "evidence_tier_description",
    "visual_context_summary",
    "mesh_context_summary",
    "audit_question",
    "review_relation_reliability",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "review_notes",
]

FORBIDDEN_VISIBLE_FIELDS = [
    "scan_id",
    "subgraph_id",
    "source_id",
    "subject_id",
    "object_id",
    "instance_id",
    "prediction_id",
    "directed_pair_id",
    "planned_proxy_role_hidden",
    "rank_band_hidden",
    "geometry_bucket_hidden",
    "object_family_pair_hidden",
    "coverage_proxy_hidden",
    "uncertainty_bucket_hidden",
    "gt_label_match_status_hidden",
    "strict_group_value_hidden",
    "source_path",
    "subject_crop_file_examples",
    "object_crop_file_examples",
    "subject_origin_file_examples",
    "object_origin_file_examples",
]

FORBIDDEN_VISIBLE_SUBSTRINGS = [
    "_hidden",
    "proxy",
    "rank_band",
    "geometry_bucket",
    "object_family",
    "gt_label",
    "strict_group",
    "scan_id",
    "subgraph_id",
    "subject_id",
    "object_id",
    "instance_id",
    "prediction_id",
    "directed_pair_id",
    "source_path",
    "file_examples",
    "p_geom",
    "geometry_status",
    "semantic_score",
    "source_score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def bucket_count(value: int) -> str:
    if value <= 0:
        return "none"
    if value == 1:
        return "one"
    if value <= 3:
        return "two_or_three"
    return "four_or_more"


def evidence_tier(row: dict[str, Any]) -> tuple[str, str]:
    if row["audit_ready_state"] == "strong_pair_visual_audit_ready":
        return (
            "T1_strong_pair_visual",
            "same-frame subject/object visual context is available; mesh and sequence assets are reserved for packet materialization",
        )
    if row["audit_ready_state"] == "individual_visual_plus_mesh_audit_ready":
        return (
            "T2_individual_visual_plus_mesh",
            "individual subject/object visual crops and mesh/sequence assets are available; direct same-frame pair context is not available",
        )
    return (
        "T3_not_audit_ready",
        "independent visual or mesh evidence is incomplete; this row should not be materialized without repair",
    )


def visual_summary(row: dict[str, Any], tier: str) -> str:
    subject_bucket = bucket_count(int(row["subject_crop_count"]))
    object_bucket = bucket_count(int(row["object_crop_count"]))
    if tier == "T1_strong_pair_visual":
        shared_bucket = bucket_count(int(row["shared_origin_frame_count"]))
        return (
            "same-frame subject/object visual context available; "
            f"shared visual contexts {shared_bucket}; subject crops {subject_bucket}; object crops {object_bucket}"
        )
    if tier == "T2_individual_visual_plus_mesh":
        return (
            "separate subject/object visual crops available; no direct same-frame pair context; "
            f"subject crops {subject_bucket}; object crops {object_bucket}"
        )
    return f"limited visual context; subject crops {subject_bucket}; object crops {object_bucket}"


def mesh_summary(row: dict[str, Any]) -> str:
    if row["mesh_ready"] and row["sequence_ready"]:
        return "mesh, aligned instance assets, semantic segmentation, and color/depth/pose sequence assets are available"
    if row["mesh_ready"]:
        return "mesh and aligned instance assets are available; sequence evidence is limited"
    return "mesh evidence is not materialization-ready"


def audit_question(row: dict[str, Any]) -> str:
    relation = f"{row['subject_label']} {row['predicate_label']} {row['object_label']}"
    return (
        f"Using only the packet-local visual and mesh/context evidence, should `{relation}` be accepted as a reliable "
        "hanging or mounted scene-graph relation, rejected as unreliable, or marked uncertain?"
    )


def validate_inputs(
    source_inventory_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if source_inventory_summary.get("status") != EXPECTED_SOURCE_INVENTORY_STATUS:
        errors.append(
            {
                "error_type": "unexpected_source_inventory_status",
                "expected": EXPECTED_SOURCE_INVENTORY_STATUS,
                "actual": source_inventory_summary.get("status"),
            }
        )
    if source_inventory_summary.get("next_todo") != EXPECTED_SOURCE_INVENTORY_NEXT:
        errors.append(
            {
                "error_type": "unexpected_source_inventory_next",
                "expected": EXPECTED_SOURCE_INVENTORY_NEXT,
                "actual": source_inventory_summary.get("next_todo"),
            }
        )
    if candidate_summary.get("status") != EXPECTED_CANDIDATE_STATUS:
        errors.append(
            {
                "error_type": "unexpected_candidate_status",
                "expected": EXPECTED_CANDIDATE_STATUS,
                "actual": candidate_summary.get("status"),
            }
        )
    if source_inventory_summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_inventory_validation_errors_present", "actual": source_inventory_summary.get("validation_errors")})
    if candidate_summary.get("validation_errors") != 0:
        errors.append({"error_type": "candidate_validation_errors_present", "actual": candidate_summary.get("validation_errors")})
    if len(inventory_rows) != TARGET_ROWS:
        errors.append({"error_type": "unexpected_inventory_row_count", "expected": TARGET_ROWS, "actual": len(inventory_rows)})

    counts = source_inventory_summary.get("counts", {})
    if counts.get("source_inventory_gate_pass") is not True:
        errors.append({"error_type": "source_inventory_gate_not_passed"})
    if counts.get("audit_ready_rows") != TARGET_ROWS:
        errors.append({"error_type": "unexpected_audit_ready_rows", "expected": TARGET_ROWS, "actual": counts.get("audit_ready_rows")})

    for source, payload in [("source_inventory", source_inventory_summary), ("candidate_mining", candidate_summary)]:
        boundary = payload.get("boundary", {})
        for key in [
            "validation_usage",
            "test_usage",
            "fills_new_labels",
            "trains_new_posterior",
            "posterior_smoke_allowed",
            "paper_evidence_allowed",
            "h001_artifacts_modified",
            "multi_view_as_model_input",
            "mesh_as_model_input",
        ]:
            if boundary.get(key) is not False:
                errors.append(
                    {
                        "error_type": "boundary_violation",
                        "source": source,
                        "key": key,
                        "expected": False,
                        "actual": boundary.get(key),
                    }
                )

    row_roles = Counter(row.get("planned_proxy_role_hidden") for row in inventory_rows)
    if row_roles != Counter({ROLE_ACCEPT: TARGET_ROWS // 2, ROLE_REJECT: TARGET_ROWS // 2}):
        errors.append({"error_type": "unexpected_proxy_role_balance", "actual": dict(row_roles)})
    predicates = Counter(row.get("predicate_label") for row in inventory_rows)
    if predicates != Counter({"hanging on": TARGET_ROWS}):
        errors.append({"error_type": "unexpected_predicate_counts", "actual": dict(predicates)})
    return errors


def build_packet_rows(inventory_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    visible_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(inventory_rows):
        tier, tier_description = evidence_tier(row)
        packet_id = f"apv22_{idx:04d}_{row['blind_review_id']}"
        candidate_relation = f"{row['subject_label']} {row['predicate_label']} {row['object_label']}"
        visible_rows.append(
            {
                "packet_id": packet_id,
                "blind_review_id": row["blind_review_id"],
                "candidate_relation": candidate_relation,
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "object_label": row["object_label"],
                "relation_family_visible": "hanging or mounted relation",
                "packet_role": "primary_hanging_on_reliability_candidate",
                "evidence_tier": tier,
                "evidence_tier_description": tier_description,
                "visual_context_summary": visual_summary(row, tier),
                "mesh_context_summary": mesh_summary(row),
                "audit_question": audit_question(row),
                "review_relation_reliability": "",
                "review_geometry_support": "",
                "review_endpoint_identity": "",
                "review_coverage": "",
                "review_uncertainty": "",
                "review_notes": "",
            }
        )
        hidden_rows.append(
            {
                "schema_version": "h002_reliability_target_v22_hanging_on_audit_packet_hidden_plan_v1",
                "packet_id": packet_id,
                "blind_review_id": row["blind_review_id"],
                "scan_id": row["scan_id"],
                "subgraph_id": row["subgraph_id"],
                "source_id": row["source_id"],
                "subject_id": row["subject_id"],
                "object_id": row["object_id"],
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "object_label": row["object_label"],
                "packet_role": "primary_hanging_on_reliability_candidate",
                "planned_proxy_role_hidden": row["planned_proxy_role_hidden"],
                "rank_band_hidden": row["rank_band_hidden"],
                "geometry_bucket_hidden": row["geometry_bucket_hidden"],
                "object_family_pair_hidden": row["object_family_pair_hidden"],
                "coverage_proxy_hidden": row["coverage_proxy_hidden"],
                "uncertainty_bucket_hidden": row["uncertainty_bucket_hidden"],
                "gt_label_match_status_hidden": row["gt_label_match_status_hidden"],
                "strict_group_value_hidden": row["strict_group_value_hidden"],
                "audit_ready_state": row["audit_ready_state"],
                "visual_context_state": row["visual_context_state"],
                "evidence_tier": tier,
                "subject_crop_count": row["subject_crop_count"],
                "object_crop_count": row["object_crop_count"],
                "subject_origin_count": row["subject_origin_count"],
                "object_origin_count": row["object_origin_count"],
                "shared_origin_frame_count": row["shared_origin_frame_count"],
                "shared_origin_frames": row["shared_origin_frames"],
                "shared_crop_view_ranks": row["shared_crop_view_ranks"],
                "subject_crop_file_examples": row["subject_crop_file_examples"],
                "object_crop_file_examples": row["object_crop_file_examples"],
                "subject_origin_file_examples": row["subject_origin_file_examples"],
                "object_origin_file_examples": row["object_origin_file_examples"],
                "scan_exists": row["scan_exists"],
                "multi_view_exists": row["multi_view_exists"],
                "sequence_ready": row["sequence_ready"],
                "mesh_ready": row["mesh_ready"],
                "mesh_obj_exists": row["mesh_obj_exists"],
                "instance_ply_exists": row["instance_ply_exists"],
                "aligned_instance_ply_exists": row["aligned_instance_ply_exists"],
                "semseg_json_exists": row["semseg_json_exists"],
                "segment_json_exists": row["segment_json_exists"],
                "sequence_color_frames": row["sequence_color_frames"],
                "sequence_depth_frames": row["sequence_depth_frames"],
                "sequence_pose_frames": row["sequence_pose_frames"],
                "visible_packet_materialization_next": True,
                "model_input_allowed_now": False,
            }
        )
    return visible_rows, hidden_rows


def build_counts(visible_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> dict[str, Any]:
    rows_by_evidence_tier = Counter(row["evidence_tier"] for row in visible_rows)
    hidden_by_proxy_role = Counter(row["planned_proxy_role_hidden"] for row in hidden_rows)
    by_proxy_and_tier: dict[str, dict[str, int]] = {}
    for proxy_role in sorted(hidden_by_proxy_role):
        subset = [row for row in hidden_rows if row["planned_proxy_role_hidden"] == proxy_role]
        by_proxy_and_tier[proxy_role] = dict(Counter(row["evidence_tier"] for row in subset))
    gates = {
        "rows_exactly_240": len(visible_rows) == TARGET_ROWS,
        "all_rows_primary_hanging_on": Counter(row["predicate_label"] for row in visible_rows) == Counter({"hanging on": TARGET_ROWS}),
        "t1_rows_exactly_73": rows_by_evidence_tier.get("T1_strong_pair_visual", 0) == 73,
        "t2_rows_exactly_167": rows_by_evidence_tier.get("T2_individual_visual_plus_mesh", 0) == 167,
        "no_t3_rows": rows_by_evidence_tier.get("T3_not_audit_ready", 0) == 0,
        "proxy_balance_120_120": hidden_by_proxy_role == Counter({ROLE_ACCEPT: TARGET_ROWS // 2, ROLE_REJECT: TARGET_ROWS // 2}),
        "accept_and_reject_each_have_t1_rows": all(
            by_proxy_and_tier.get(role, {}).get("T1_strong_pair_visual", 0) > 0 for role in [ROLE_ACCEPT, ROLE_REJECT]
        ),
    }
    return {
        "rows": len(visible_rows),
        "rows_by_packet_role": dict(Counter(row["packet_role"] for row in visible_rows)),
        "rows_by_evidence_tier": dict(rows_by_evidence_tier),
        "rows_by_predicate": dict(Counter(row["predicate_label"] for row in visible_rows)),
        "primary_rows": sum(1 for row in visible_rows if row["packet_role"] == "primary_hanging_on_reliability_candidate"),
        "hidden_by_proxy_role": dict(hidden_by_proxy_role),
        "hidden_by_proxy_role_and_tier": by_proxy_and_tier,
        "audit_packet_plan_gate_pass": all(gates.values()),
        "audit_packet_plan_gates": gates,
    }


def validate_visible_schema(visible_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    visible_set = set(VISIBLE_FIELDS)
    forbidden_present = sorted(visible_set & set(FORBIDDEN_VISIBLE_FIELDS))
    if forbidden_present:
        errors.append({"error_type": "forbidden_visible_fields_present", "fields": forbidden_present})
    for field in VISIBLE_FIELDS:
        for forbidden in FORBIDDEN_VISIBLE_SUBSTRINGS:
            if forbidden in field:
                errors.append({"error_type": "forbidden_visible_field_substring", "field": field, "substring": forbidden})
    for row in visible_rows:
        if set(row) != visible_set:
            errors.append(
                {
                    "error_type": "visible_row_schema_mismatch",
                    "packet_id": row.get("packet_id"),
                    "missing": sorted(visible_set - set(row)),
                    "extra": sorted(set(row) - visible_set),
                }
            )
        row_text = json.dumps(row, ensure_ascii=False).lower()
        for forbidden in FORBIDDEN_VISIBLE_SUBSTRINGS:
            if forbidden in row_text:
                errors.append({"error_type": "forbidden_visible_value_substring", "packet_id": row.get("packet_id"), "substring": forbidden})
        for review_field in [
            "review_relation_reliability",
            "review_geometry_support",
            "review_endpoint_identity",
            "review_coverage",
            "review_uncertainty",
            "review_notes",
        ]:
            if row.get(review_field) != "":
                errors.append({"error_type": "review_field_not_blank", "packet_id": row.get("packet_id"), "field": review_field})
    return errors


def build_contract(counts: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v22_hanging_on_audit_packet_contract_v1",
        "purpose": "plan neutral visual/mesh audit packets for hanging-on strict conditional-contrast candidates before labels",
        "packet_roles": {
            "primary_hanging_on_reliability_candidate": {
                "predicates": ["hanging on"],
                "future_target_role": "eligible_for_relation_reliability_label_only_after_packet_materialization_leakage_review_label_ingestion_and_target_independence_audit",
            }
        },
        "evidence_tiers": {
            "T1_strong_pair_visual": "same-frame subject/object visual context plus mesh/sequence assets",
            "T2_individual_visual_plus_mesh": "individual subject/object visual crops plus mesh/sequence assets; no direct same-frame pair context",
        },
        "visible_fields": VISIBLE_FIELDS,
        "forbidden_visible_fields": FORBIDDEN_VISIBLE_FIELDS,
        "forbidden_visible_substrings": FORBIDDEN_VISIBLE_SUBSTRINGS,
        "review_value_schema": {
            "review_relation_reliability": ["accept_reliable", "reject_unreliable", "abstain_uncertain"],
            "review_geometry_support": ["supported", "unsupported", "uncertain"],
            "review_endpoint_identity": ["clear_endpoint_identity", "uncertain_endpoint_identity", "wrong_endpoint"],
            "review_coverage": ["sufficient", "limited", "insufficient"],
            "review_uncertainty": [
                "none",
                "visual_ambiguous",
                "mesh_needed",
                "ontology_ambiguous",
                "occlusion_or_viewpoint_limited",
            ],
        },
        "materialization_policy": {
            "copy_or_link_images_with_neutral_packet_local_names": True,
            "visible_packet_must_not_expose_scan_subgraph_or_instance_ids": True,
            "visible_packet_must_not_expose_proxy_role_or_selection_route": True,
            "visible_packet_must_not_expose_rank_geometry_bucket_gt_or_strict_group": True,
            "visible_packet_must_not_expose_source_path_or_original_image_filename": True,
            "mesh_paths_hidden_manifest_only": True,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
        },
        "post_materialization_gates": {
            "visible_packet_rows": TARGET_ROWS,
            "primary_rows": TARGET_ROWS,
            "review_fields_blank": True,
            "visible_leakage_hits": 0,
            "all_packet_dirs_exist": True,
            "preserve_t1_t2_tier": True,
        },
        "current_counts": counts,
    }


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    return f"""# H002 V22 Hanging-On Strict Audit Packet Plan

Created at: `{summary['created_at']}`

## Status

```text
status = {summary['status']}
next_todo = {summary['next_todo']}
validation_errors = {summary['validation_errors']}
audit_packet_plan_gate_pass = {counts['audit_packet_plan_gate_pass']}
posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}
multi_view_as_model_input = {summary['boundary']['multi_view_as_model_input']}
```

## Packet Roles

```text
rows = {counts['rows']}
rows_by_packet_role = {counts['rows_by_packet_role']}
rows_by_predicate = {counts['rows_by_predicate']}
primary_rows = {counts['primary_rows']}
hidden_by_proxy_role = {counts['hidden_by_proxy_role']}
```

## Evidence Tiers

```text
rows_by_evidence_tier = {counts['rows_by_evidence_tier']}
hidden_by_proxy_role_and_tier = {counts['hidden_by_proxy_role_and_tier']}
```

## Decision

The packet plan preserves the v69 source-inventory tier distinction:

- `T1_strong_pair_visual`: same-frame subject/object visual context.
- `T2_individual_visual_plus_mesh`: separate object views plus mesh/sequence context.

The next step may materialize audit packets, but reviewer-visible files must not expose scan ids,
subgraph ids, instance ids, proxy roles, rank bands, geometry buckets, object-family pairs,
GT-match status, strict-group ids, source paths, original image filenames, or other hidden
candidate-construction metadata.

## Boundary

This stage does not fill labels, ingest labels, copy packet assets, train posterior, use
validation/test data, or promote multi-view/mesh as deployable model input.
"""


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_inventory_summary = read_json(args.source_inventory_dir / "summary.json")
    candidate_summary = read_json(args.candidate_dir / "summary.json")
    inventory_rows = read_jsonl(args.source_inventory_dir / "inventory_rows.jsonl")

    validation_errors = validate_inputs(source_inventory_summary, candidate_summary, inventory_rows)
    visible_rows, hidden_rows = build_packet_rows(inventory_rows)
    counts = build_counts(visible_rows, hidden_rows)
    validation_errors.extend(validate_visible_schema(visible_rows))
    if not counts["audit_packet_plan_gate_pass"]:
        validation_errors.append({"error_type": "audit_packet_plan_gate_failed", "counts": counts})

    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    next_todo = NEXT_TODO_READY if not validation_errors else EXPECTED_SOURCE_INVENTORY_NEXT

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "audit_packet_contract": output_dir / "audit_packet_contract.json",
        "visible_schema": output_dir / "visible_schema.json",
        "visible_packet_template": output_dir / "visible_packet_template.tsv",
        "packet_plan_rows": output_dir / "packet_plan_rows.jsonl",
        "hidden_asset_manifest_plan": output_dir / "hidden_asset_manifest_plan.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    contract = build_contract(counts)
    summary = {
        "schema_version": "h002_reliability_target_v22_hanging_on_audit_packet_plan_summary_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "input_paths": {
            "source_inventory_summary": rel_path(args.source_inventory_dir / "summary.json"),
            "source_inventory_rows": rel_path(args.source_inventory_dir / "inventory_rows.jsonl"),
            "candidate_summary": rel_path(args.candidate_dir / "summary.json"),
            "visible_candidate_sheet": rel_path(args.candidate_dir / "visible_candidate_sheet.tsv"),
            "hidden_candidate_manifest": rel_path(args.candidate_dir / "hidden_candidate_manifest.jsonl"),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "candidate_mining_allowed": False,
            "copies_or_materializes_packet_assets": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_as_audit_or_confirmation_evidence_only": True,
            "mesh_as_audit_or_confirmation_evidence_only": True,
            "construction_metadata_visible": False,
        },
        "counts": counts,
        "visible_fields": VISIBLE_FIELDS,
        "forbidden_visible_fields": FORBIDDEN_VISIBLE_FIELDS,
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["audit_packet_contract"], contract)
    write_json(
        output_paths["visible_schema"],
        {
            "schema_version": "h002_reliability_target_v22_hanging_on_visible_schema_v1",
            "visible_fields": VISIBLE_FIELDS,
            "forbidden_visible_fields": FORBIDDEN_VISIBLE_FIELDS,
            "forbidden_visible_substrings": FORBIDDEN_VISIBLE_SUBSTRINGS,
            "review_value_schema": contract["review_value_schema"],
        },
    )
    write_tsv(output_paths["visible_packet_template"], visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["packet_plan_rows"], visible_rows)
    write_jsonl(output_paths["hidden_asset_manifest_plan"], hidden_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    output_paths["report"].write_text(report_text(summary), encoding="utf-8")
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"rows={counts['rows']}")
    print(f"primary_rows={counts['primary_rows']}")
    print(f"rows_by_evidence_tier={counts['rows_by_evidence_tier']}")
    print(f"hidden_by_proxy_role={counts['hidden_by_proxy_role']}")
    print(f"audit_packet_plan_gate_pass={counts['audit_packet_plan_gate_pass']}")
    print(f"validation_errors={summary['validation_errors']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
