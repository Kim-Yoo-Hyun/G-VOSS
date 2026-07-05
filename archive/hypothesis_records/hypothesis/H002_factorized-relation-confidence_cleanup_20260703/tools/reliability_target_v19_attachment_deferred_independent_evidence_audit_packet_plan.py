#!/usr/bin/env python3
"""Plan tiered audit packets for H002 v19 attachment independent evidence."""

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

DEFAULT_INVENTORY_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_source_inventory"
DEFAULT_PLAN_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_repair_plan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan"

EXPECTED_INVENTORY_STATUS = "h002_reliability_target_v19_attachment_deferred_independent_evidence_source_inventory_ready"
EXPECTED_INVENTORY_NEXT = "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan"
EXPECTED_REPAIR_PLAN_STATUS = "h002_reliability_target_v19_attachment_deferred_independent_evidence_repair_plan_ready_for_source_inventory"

STATUS = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_plan_ready_for_materialization"
NEXT_TODO = "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization"

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
    "review_uncertainty",
    "review_notes",
]

FORBIDDEN_VISIBLE_FIELDS = [
    "scan_id",
    "subgraph_id",
    "source_id",
    "subject_id",
    "object_id",
    "candidate_role_hidden",
    "cell_id_hidden",
    "sampling_queue_hidden",
    "geometry_status_hidden",
    "rank_band_hidden",
    "semantic_rank_hidden",
    "semantic_score_norm_hidden",
    "machine_hint_hidden",
    "label_match_status_hidden",
    "matched_predicates_hidden",
    "raw_features_hidden",
    "relation_reliability_state_v18",
    "relation_reliability_binary_target",
    "geometry_support_state_v18",
    "geometry_support_binary_target",
    "relation_usefulness_state_v18",
    "relation_usefulness_binary_target",
    "primary_reason_v18",
    "review_notes_v18",
    "reviewer_id_v18",
    "label_source",
]

FORBIDDEN_VISIBLE_SUBSTRINGS = [
    "_hidden",
    "target",
    "state_v18",
    "reason_v18",
    "review_notes_v18",
    "reviewer_id_v18",
    "label_source",
    "scan_id",
    "subgraph_id",
    "raw_feature",
    "machine_hint",
    "rank_band",
    "geometry_status",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory-dir", type=Path, default=DEFAULT_INVENTORY_DIR)
    parser.add_argument("--repair-plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
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
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
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
            "subject and object have exact same-frame visual context plus mesh/sequence assets",
        )
    if row["audit_ready_state"] == "individual_visual_plus_mesh_audit_ready":
        return (
            "T2_individual_visual_plus_mesh",
            "subject and object have individual visual crops plus mesh/sequence assets, but no exact same-frame overlap",
        )
    if row["audit_ready_state"] == "mesh_plus_individual_crop_limited_ready":
        return (
            "T3_mesh_plus_limited_visual",
            "mesh assets exist but visual evidence is limited",
        )
    return ("T4_not_ready", "insufficient independent visual or mesh evidence")


def packet_role(row: dict[str, Any]) -> str:
    if row["candidate_role_hidden"] == "primary_binary_candidate" and row["predicate_label"] in {"attached to", "hanging on"}:
        return "primary_attachment_reliability_candidate"
    if row["predicate_label"] == "connected to":
        return "connected_diagnostic_only"
    return "uncertainty_or_coverage_audit_only"


def audit_question(row: dict[str, Any], role: str) -> str:
    relation = f"{row['subject_label']} {row['predicate_label']} {row['object_label']}"
    if role == "primary_attachment_reliability_candidate":
        return f"Using only the packet images and mesh/context evidence, should `{relation}` be treated as a reliable attachment-like scene-graph edge?"
    if role == "connected_diagnostic_only":
        return f"Using only the packet images and mesh/context evidence, is `{relation}` visually/physically plausible, or is functional connection still ambiguous?"
    return f"Using only the packet images and mesh/context evidence, is `{relation}` evaluable or should it remain uncertain?"


def visual_summary(row: dict[str, Any], tier: str) -> str:
    subject_bucket = bucket_count(int(row["subject_crop_count"]))
    object_bucket = bucket_count(int(row["object_crop_count"]))
    if tier == "T1_strong_pair_visual":
        return (
            f"strong pair visual context; same-frame overlap count {row['shared_origin_frame_count']}; "
            f"subject crops {subject_bucket}; object crops {object_bucket}"
        )
    if tier == "T2_individual_visual_plus_mesh":
        return (
            "individual subject/object visual crops with weak same-view-rank proxy; "
            f"subject crops {subject_bucket}; object crops {object_bucket}"
        )
    return f"limited visual context; subject crops {subject_bucket}; object crops {object_bucket}"


def mesh_summary(row: dict[str, Any]) -> str:
    if row["mesh_ready"] and row["sequence_ready"]:
        return "mesh, aligned instance labels, semantic segmentation, sequence color/depth/pose are available for audit materialization"
    if row["mesh_ready"]:
        return "mesh and aligned instance labels are available; sequence context is limited"
    return "mesh context is not ready"


def build_packet_rows(inventory_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    visible_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(inventory_rows):
        tier, tier_description = evidence_tier(row)
        role = packet_role(row)
        packet_id = f"apv19_{idx:04d}_{row['blind_review_id']}"
        candidate_relation = f"{row['subject_label']} {row['predicate_label']} {row['object_label']}"
        visible_rows.append(
            {
                "packet_id": packet_id,
                "blind_review_id": row["blind_review_id"],
                "candidate_relation": candidate_relation,
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "object_label": row["object_label"],
                "relation_family_visible": "attachment-like relation",
                "packet_role": role,
                "evidence_tier": tier,
                "evidence_tier_description": tier_description,
                "visual_context_summary": visual_summary(row, tier),
                "mesh_context_summary": mesh_summary(row),
                "audit_question": audit_question(row, role),
                "review_relation_reliability": "",
                "review_geometry_support": "",
                "review_uncertainty": "",
                "review_notes": "",
            }
        )
        hidden_rows.append(
            {
                "schema_version": "h002_reliability_target_v19_attachment_audit_packet_hidden_plan_v1",
                "packet_id": packet_id,
                "blind_review_id": row["blind_review_id"],
                "scan_id": row["scan_id"],
                "subgraph_id": row["subgraph_id"],
                "predicate_label": row["predicate_label"],
                "packet_role": role,
                "evidence_tier": tier,
                "audit_ready_state": row["audit_ready_state"],
                "visual_context_state": row["visual_context_state"],
                "subject_id": row["subject_id"],
                "object_id": row["object_id"],
                "subject_label": row["subject_label"],
                "object_label": row["object_label"],
                "subject_crop_file_examples": row["subject_crop_file_examples"],
                "object_crop_file_examples": row["object_crop_file_examples"],
                "subject_origin_file_examples": row["subject_origin_file_examples"],
                "object_origin_file_examples": row["object_origin_file_examples"],
                "shared_origin_frames": row["shared_origin_frames"],
                "shared_crop_view_ranks": row["shared_crop_view_ranks"],
                "mesh_ready": row["mesh_ready"],
                "sequence_ready": row["sequence_ready"],
                "model_input_allowed_now": False,
                "visible_packet_materialization_next": True,
            }
        )
    return visible_rows, hidden_rows


def build_counts(visible_rows: list[dict[str, Any]]) -> dict[str, Any]:
    primary = [row for row in visible_rows if row["packet_role"] == "primary_attachment_reliability_candidate"]
    counts = {
        "rows": len(visible_rows),
        "rows_by_packet_role": dict(Counter(row["packet_role"] for row in visible_rows)),
        "rows_by_evidence_tier": dict(Counter(row["evidence_tier"] for row in visible_rows)),
        "rows_by_predicate": dict(Counter(row["predicate_label"] for row in visible_rows)),
        "primary_rows": len(primary),
        "primary_by_evidence_tier": dict(Counter(row["evidence_tier"] for row in primary)),
        "primary_by_predicate_and_tier": {},
    }
    by_predicate_and_tier: dict[str, dict[str, int]] = {}
    for row in primary:
        by_predicate_and_tier.setdefault(row["predicate_label"], Counter())
        by_predicate_and_tier[row["predicate_label"]][row["evidence_tier"]] += 1
    counts["primary_by_predicate_and_tier"] = {key: dict(value) for key, value in by_predicate_and_tier.items()}
    counts["audit_packet_plan_gate_pass"] = (
        counts["rows"] == 240
        and counts["primary_rows"] == 160
        and counts["primary_by_evidence_tier"].get("T1_strong_pair_visual", 0) >= 20
        and counts["primary_by_evidence_tier"].get("T2_individual_visual_plus_mesh", 0) >= 100
    )
    return counts


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
        for review_field in ["review_relation_reliability", "review_geometry_support", "review_uncertainty", "review_notes"]:
            if row.get(review_field) != "":
                errors.append({"error_type": "review_field_not_blank", "packet_id": row.get("packet_id"), "field": review_field})
    return errors


def validate_inputs(
    inventory_summary: dict[str, Any],
    repair_plan_summary: dict[str, Any],
    inventory_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if inventory_summary.get("status") != EXPECTED_INVENTORY_STATUS:
        errors.append({"error_type": "unexpected_inventory_status", "expected": EXPECTED_INVENTORY_STATUS, "actual": inventory_summary.get("status")})
    if inventory_summary.get("next_todo") != EXPECTED_INVENTORY_NEXT:
        errors.append({"error_type": "unexpected_inventory_next", "expected": EXPECTED_INVENTORY_NEXT, "actual": inventory_summary.get("next_todo")})
    if repair_plan_summary.get("status") != EXPECTED_REPAIR_PLAN_STATUS:
        errors.append({"error_type": "unexpected_repair_plan_status", "expected": EXPECTED_REPAIR_PLAN_STATUS, "actual": repair_plan_summary.get("status")})
    if inventory_summary.get("validation_errors") != 0:
        errors.append({"error_type": "inventory_validation_errors_present", "actual": inventory_summary.get("validation_errors")})
    if len(inventory_rows) != 240:
        errors.append({"error_type": "unexpected_inventory_row_count", "expected": 240, "actual": len(inventory_rows)})
    if inventory_summary.get("counts", {}).get("source_inventory_gate_pass") is not True:
        errors.append({"error_type": "source_inventory_gate_not_passed"})

    for source, payload in [("inventory", inventory_summary), ("repair_plan", repair_plan_summary)]:
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
        ]:
            if boundary.get(key) is not False:
                errors.append({"error_type": "boundary_violation", "source": source, "key": key, "expected": False, "actual": boundary.get(key)})
    return errors


def build_contract(counts: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v19_attachment_audit_packet_contract_v1",
        "purpose": "materialize independent visual/mesh audit packets before any repaired labels",
        "packet_roles": {
            "primary_attachment_reliability_candidate": {
                "predicates": ["attached to", "hanging on"],
                "future_target_role": "eligible_for_repaired_relation_reliability_label_after_packet_materialization_and_leakage_check",
            },
            "connected_diagnostic_only": {
                "predicates": ["connected to"],
                "future_target_role": "diagnostic_only_until_functional_connection_evidence_is_independently_confirmed",
            },
            "uncertainty_or_coverage_audit_only": {
                "future_target_role": "audit_uncertainty_and_coverage_only",
            },
        },
        "evidence_tiers": {
            "T1_strong_pair_visual": "exact same-frame subject/object visual context plus mesh/sequence assets",
            "T2_individual_visual_plus_mesh": "separate subject/object crops plus mesh/sequence assets; no exact same-frame overlap",
            "T3_mesh_plus_limited_visual": "mesh assets with limited crop coverage",
            "T4_not_ready": "not materialization-ready",
        },
        "visible_fields": VISIBLE_FIELDS,
        "forbidden_visible_fields": FORBIDDEN_VISIBLE_FIELDS,
        "materialization_policy": {
            "copy_or_link_images_with_neutral_packet_local_names": True,
            "visible_packet_must_not_expose_scan_id_or_instance_ids": True,
            "old_review_cards_must_not_be_reused_as_visible_evidence": True,
            "geometry_summary_text_from_v18_must_not_be_reused": True,
            "mesh_paths_hidden_manifest_only": True,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
        },
        "post_materialization_gates": {
            "visible_packet_rows": 240,
            "primary_rows": 160,
            "review_fields_blank": True,
            "visible_leakage_hits": 0,
            "all_packet_dirs_exist": True,
            "primary_t1_min": 20,
            "primary_t2_min": 100,
        },
        "current_counts": counts,
    }


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    return f"""# H002 V19 Attachment Audit Packet Plan

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
rows_by_evidence_tier = {counts['rows_by_evidence_tier']}
primary_by_evidence_tier = {counts['primary_by_evidence_tier']}
primary_by_predicate_and_tier = {counts['primary_by_predicate_and_tier']}
```

## Decision

The packet plan is tiered:

- `T1_strong_pair_visual`: exact same-frame subject/object visual context.
- `T2_individual_visual_plus_mesh`: individual subject/object crops plus mesh/sequence context.

The next step may materialize audit packets, but must keep old v18 labels, geometry status,
rank, machine hints, cell ids, raw geometry features, and construction metadata out of the
reviewer-visible sheet.

## Boundary

This stage does not fill labels, mine new candidates, train posterior, use validation/test data,
or promote multi-view as a deployable model input.
"""


def main() -> int:
    args = parse_args()
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    inventory_summary = read_json(args.inventory_dir / "summary.json")
    repair_plan_summary = read_json(args.repair_plan_dir / "summary.json")
    inventory_rows = read_jsonl(args.inventory_dir / "inventory_rows.jsonl")

    validation_errors = validate_inputs(inventory_summary, repair_plan_summary, inventory_rows)
    visible_rows, hidden_rows = build_packet_rows(inventory_rows)
    counts = build_counts(visible_rows)
    validation_errors.extend(validate_visible_schema(visible_rows))
    if not counts["audit_packet_plan_gate_pass"]:
        validation_errors.append({"error_type": "audit_packet_plan_gate_failed", "counts": counts})

    contract = build_contract(counts)
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
    summary = {
        "schema_version": "h002_reliability_target_v19_attachment_audit_packet_plan_summary_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS,
        "next_todo": NEXT_TODO,
        "input_paths": {
            "inventory_summary": rel_path(args.inventory_dir / "summary.json"),
            "inventory_rows": rel_path(args.inventory_dir / "inventory_rows.jsonl"),
            "repair_plan_summary": rel_path(args.repair_plan_dir / "summary.json"),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "candidate_mining_allowed": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_as_audit_or_confirmation_evidence_only": True,
            "mesh_as_audit_or_confirmation_evidence_only": True,
            "old_labels_visible": False,
            "construction_metadata_visible": False,
        },
        "counts": counts,
        "visible_fields": VISIBLE_FIELDS,
        "forbidden_visible_fields": FORBIDDEN_VISIBLE_FIELDS,
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["audit_packet_contract"], contract)
    write_json(output_paths["visible_schema"], {"visible_fields": VISIBLE_FIELDS, "forbidden_visible_fields": FORBIDDEN_VISIBLE_FIELDS})
    write_tsv(output_paths["visible_packet_template"], visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["packet_plan_rows"], visible_rows)
    write_jsonl(output_paths["hidden_asset_manifest_plan"], hidden_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    output_paths["report"].write_text(report_text(summary), encoding="utf-8")

    print(f"status={STATUS}")
    print(f"next={NEXT_TODO}")
    print(f"rows={counts['rows']}")
    print(f"primary_rows={counts['primary_rows']}")
    print(f"primary_by_evidence_tier={counts['primary_by_evidence_tier']}")
    print(f"audit_packet_plan_gate_pass={counts['audit_packet_plan_gate_pass']}")
    print(f"validation_errors={len(validation_errors)}")
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
