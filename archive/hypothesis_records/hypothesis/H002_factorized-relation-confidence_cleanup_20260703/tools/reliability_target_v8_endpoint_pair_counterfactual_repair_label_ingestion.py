#!/usr/bin/env python3
"""Ingest v8 repair endpoint-pair counterfactual labels after proxy fill."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

import reliability_target_v8_endpoint_pair_counterfactual_label_ingestion as base


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

FILL_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_label_fill_codex_proxy_user_requested"
READINESS_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_label_readiness_codex_proxy_user_requested"

DEFAULT_COMPLETED_SHEET = FILL_DIR / "completed_v8_repair_label_sheet_codex_proxy_user_requested.tsv"
DEFAULT_FILL_SUMMARY = FILL_DIR / "summary.json"
DEFAULT_SCHEMA = READINESS_DIR / "label_schema.json"
DEFAULT_MANIFEST = READINESS_DIR / "ready_manifest_post_label_only.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_repair_label_ingestion_codex_proxy_user_requested"

LABEL_SOURCE = "codex_proxy_reliability_target_v8_endpoint_pair_counterfactual_repair_user_requested"

VISIBLE_GROUP_KEYS = [
    "predicate_family",
    "predicate_label",
    "subject_label",
    "object_label",
    "subject_object_label_pair_visible",
    "evidence_packet_status",
    "review_scope",
]

HIDDEN_GROUP_KEYS = [
    "label_geometry_bucket_hidden",
    "semantic_geometry_bucket_hidden",
    "rank_band_hidden",
    "source_queue_hidden",
    "geometry_status_hidden",
    "h001_verification_status_hidden",
    "label_match_status_hidden",
    "machine_hint_hidden",
    "subject_object_family_cell_hidden",
    "subject_object_label_pair_hidden",
    "endpoint_pattern_hidden",
    "exact_endpoint_pair_key_hidden",
    "undirected_endpoint_pair_key_hidden",
    "counterfactual_pair_id_hidden",
    "counterfactual_pair_type_hidden",
    "additional_batch_role_hidden",
    "primary_gap_decision_hidden",
    "row_gap_decision_hidden",
    "normalized_evidence_status_hidden",
    "packet_status_hidden",
    "asset_packet_source_hidden",
    "packet_source_hidden",
    "replacement_source_hidden",
    "diagnostic_status_hidden",
    "label_readiness_status_hidden",
    "structural_pair_hidden",
    "hard_room_surface_pair_hidden",
    "generic_endpoint_pair_hidden",
    "batch_name_hidden",
    "source_id_hidden",
]

ALLOWED_REVIEW_VALUES = {
    "endpoint_identity_v6": {"clear", "uncertain", "wrong_endpoint", "not_evaluable"},
    "pair_evaluability_v6": {
        "evaluable",
        "evidence_limited",
        "predicate_ambiguous",
        "segmentation_limited",
        "not_evaluable",
    },
    "geometry_support_v6": {"supports", "contradicts", "ambiguous", "not_evaluable"},
    "relation_usefulness_v6": {"useful_nontrivial", "trivial_or_redundant", "not_a_relation", "uncertain"},
    "relation_reliability_state_v6": {"accept_reliable", "reject_unreliable", "abstain_uncertain"},
    "primary_reason_v6": {
        "geometric_support",
        "geometric_contradiction",
        "semantic_ontology_mismatch",
        "insufficient_evidence",
        "endpoint_identity_issue",
        "object_segmentation_issue",
        "predicate_definition_ambiguous",
        "trivial_room_surface_or_structure",
        "coverage_limited",
        "not_evaluable",
    },
    "uncertainty_reason_v6": {
        "",
        "ambiguous_contact",
        "ambiguous_vertical_order",
        "coverage_limited",
        "object_segmentation_issue",
        "occlusion_or_view_limit",
        "predicate_definition_ambiguous",
        "endpoint_identity_issue",
        "not_evaluable",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-sheet", type=Path, default=DEFAULT_COMPLETED_SHEET)
    parser.add_argument("--fill-summary", type=Path, default=DEFAULT_FILL_SUMMARY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def validate_fill_summary(fill_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_status = "h002_reliability_target_v8_repair_label_filled_codex_proxy_user_requested"
    if fill_summary.get("status") != expected_status:
        errors.append({"error_type": "fill_summary_status_unexpected", "expected": expected_status, "value": fill_summary.get("status")})
    expected_next = "reliability_target_v8_endpoint_pair_counterfactual_repair_label_ingestion"
    if fill_summary.get("next_todo") != expected_next:
        errors.append({"error_type": "fill_summary_next_todo_unexpected", "expected": expected_next, "value": fill_summary.get("next_todo")})

    boundary = fill_summary.get("boundary", {})
    expected_false = [
        "actual_user_reviewer",
        "paper_evidence_allowed",
        "paper_metric_evidence",
        "h001_artifacts_modified",
        "used_hidden_manifest_for_label_decision",
        "used_semantic_geometry_bucket_for_label_decision",
        "used_endpoint_pair_metadata_for_label_decision",
        "used_source_score_or_rank",
        "used_p_geom_valid",
        "used_geometry_status",
        "used_source_queue",
        "used_label_match_status",
        "used_target_construction_metadata",
        "validation_usage",
        "test_usage",
        "multi_view_as_model_input",
        "posterior_smoke_allowed",
        "trains_new_posterior",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_summary_boundary_mismatch", "field": key, "expected": False, "value": boundary.get(key)})
    expected_true = ["user_requested_proxy_fill", "post_label_hidden_manifest_diagnostic_join"]
    for key in expected_true:
        if boundary.get(key) is not True:
            errors.append({"error_type": "fill_summary_boundary_mismatch", "field": key, "expected": True, "value": boundary.get(key)})
    if boundary.get("filled_by") != "codex_proxy":
        errors.append({"error_type": "fill_summary_boundary_mismatch", "field": "filled_by", "expected": "codex_proxy", "value": boundary.get("filled_by")})
    if boundary.get("split") != "train_only":
        errors.append({"error_type": "fill_summary_boundary_mismatch", "field": "split", "expected": "train_only", "value": boundary.get("split")})
    return errors


def validate_row(row: dict[str, str], row_number: int, schema: dict[str, Any], manifest: dict[str, Any] | None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    blind_id = str(row.get("blind_review_id") or "")
    for field in base.COMPLETION_FIELDS:
        value = str(row.get(field) or "")
        if not value and field != "uncertainty_reason_v6":
            errors.append({"error_type": "missing_completion_field", "row_number": row_number, "blind_review_id": blind_id, "field": field})
            continue
        if field in ALLOWED_REVIEW_VALUES and value not in ALLOWED_REVIEW_VALUES[field]:
            errors.append({"error_type": "invalid_completion_value", "row_number": row_number, "blind_review_id": blind_id, "field": field, "value": value})

    reliability = row.get("relation_reliability_state_v6")
    geometry = row.get("geometry_support_v6")
    usefulness = row.get("relation_usefulness_v6")
    uncertainty = row.get("uncertainty_reason_v6")
    if reliability == "accept_reliable" and geometry != "supports":
        errors.append({"error_type": "accept_without_geometry_support", "row_number": row_number, "blind_review_id": blind_id, "geometry_support_v6": geometry})
    if reliability == "accept_reliable" and usefulness != "useful_nontrivial":
        errors.append({"error_type": "accept_without_useful_nontrivial", "row_number": row_number, "blind_review_id": blind_id, "relation_usefulness_v6": usefulness})
    if reliability == "abstain_uncertain" and not uncertainty:
        errors.append({"error_type": "abstain_without_uncertainty_reason", "row_number": row_number, "blind_review_id": blind_id})
    if reliability in {"accept_reliable", "reject_unreliable"} and uncertainty:
        errors.append({"error_type": "binary_label_with_uncertainty_reason", "row_number": row_number, "blind_review_id": blind_id, "uncertainty_reason_v6": uncertainty})

    if manifest is None:
        return errors

    identity_pairs = {
        "scan_id": "scan_id",
        "scene_context_id": "scene_context_id",
        "predicate_family": "predicate_family",
        "predicate_label": "predicate_label",
        "subject_id": "subject_id",
        "subject_label": "subject_label",
        "object_id": "object_id",
        "object_label": "object_label",
        "review_scope": "review_scope",
    }
    for completed_key, manifest_key in identity_pairs.items():
        if str(row.get(completed_key) or "") != str(manifest.get(manifest_key) or ""):
            errors.append(
                {
                    "error_type": "completed_manifest_identity_mismatch",
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "field": completed_key,
                    "completed_value": row.get(completed_key),
                    "manifest_value": manifest.get(manifest_key),
                }
            )

    if str(row.get("evidence_packet_status") or "") != str(manifest.get("packet_status_hidden") or ""):
        errors.append(
            {
                "error_type": "completed_manifest_packet_status_mismatch",
                "row_number": row_number,
                "blind_review_id": blind_id,
                "completed_value": row.get("evidence_packet_status"),
                "manifest_value": manifest.get("packet_status_hidden"),
            }
        )

    for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
        if str(row.get(field) or "") != str(manifest.get(field) or ""):
            errors.append(
                {
                    "error_type": "completed_manifest_packet_path_mismatch",
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "field": field,
                    "completed_value": row.get(field),
                    "manifest_value": manifest.get(field),
                }
            )
    return errors


def hidden_metadata(manifest: dict[str, Any]) -> dict[str, Any]:
    semantic_geometry_bucket = manifest.get("semantic_geometry_bucket_hidden") or manifest.get("label_geometry_bucket_hidden")
    row_gap_decision = manifest.get("row_gap_decision_hidden") or manifest.get("primary_gap_decision_hidden")
    normalized_status = manifest.get("normalized_evidence_status_hidden") or manifest.get("packet_status_hidden")
    output = {
        "additional_batch_role_hidden": manifest.get("additional_batch_role_hidden"),
        "asset_packet_source_hidden": manifest.get("asset_packet_source_hidden"),
        "batch_name_hidden": manifest.get("batch_name"),
        "counterfactual_pair_id_hidden": manifest.get("counterfactual_pair_id_hidden"),
        "counterfactual_pair_type_hidden": manifest.get("counterfactual_pair_type_hidden"),
        "diagnostic_reason_hidden": manifest.get("diagnostic_reason_hidden"),
        "diagnostic_status_hidden": manifest.get("diagnostic_status_hidden"),
        "endpoint_pattern_hidden": manifest.get("endpoint_pattern_hidden"),
        "exact_endpoint_pair_key_hidden": manifest.get("exact_endpoint_pair_key_hidden"),
        "generic_endpoint_pair_hidden": manifest.get("generic_endpoint_pair_hidden"),
        "geometry_status_hidden": manifest.get("geometry_status_hidden"),
        "h001_verification_status_hidden": manifest.get("h001_verification_status_hidden"),
        "hard_room_surface_pair_hidden": manifest.get("hard_room_surface_pair_hidden"),
        "label_geometry_bucket_hidden": manifest.get("label_geometry_bucket_hidden"),
        "semantic_geometry_bucket_hidden": semantic_geometry_bucket,
        "label_match_status_hidden": manifest.get("label_match_status_hidden"),
        "label_readiness_status_hidden": manifest.get("label_readiness_status_hidden"),
        "machine_hint_hidden": manifest.get("machine_hint_hidden"),
        "normalized_evidence_status_hidden": normalized_status,
        "object_family_cell_hidden": manifest.get("object_family_cell_hidden") or manifest.get("subject_object_family_cell_hidden"),
        "p_geom_valid_hidden": manifest.get("p_geom_valid_hidden"),
        "packet_source_hidden": manifest.get("packet_source_hidden"),
        "packet_status_hidden": manifest.get("packet_status_hidden"),
        "primary_gap_decision_hidden": manifest.get("primary_gap_decision_hidden"),
        "rank_band_hidden": manifest.get("rank_band_hidden"),
        "replacement_source_hidden": manifest.get("replacement_source_hidden"),
        "row_gap_decision_hidden": row_gap_decision,
        "scene_label_pair_key_hidden": manifest.get("scene_label_pair_key_hidden"),
        "semantic_rank_hidden": manifest.get("semantic_rank_hidden"),
        "semantic_score_norm_hidden": manifest.get("semantic_score_norm_hidden"),
        "semantic_score_raw_hidden": manifest.get("semantic_score_raw_hidden"),
        "source_id_hidden": manifest.get("source_id"),
        "source_queue_hidden": manifest.get("source_queue_hidden"),
        "structural_pair_hidden": manifest.get("structural_pair_hidden"),
        "subject_object_family_cell_hidden": manifest.get("subject_object_family_cell_hidden"),
        "subject_object_label_pair_hidden": manifest.get("subject_object_label_pair_hidden"),
        "undirected_endpoint_pair_key_hidden": manifest.get("undirected_endpoint_pair_key_hidden"),
        "v8_group_key_hidden": manifest.get("counterfactual_pair_id_hidden"),
    }
    output["prediction_id"] = manifest.get("prediction_id")
    output["forbidden_as_labeler_visible"] = manifest.get("forbidden_as_labeler_visible", [])
    output["packet_paths"] = {
        "multiview_packet": manifest.get("multiview_packet"),
        "pointcloud_or_mesh_packet": manifest.get("pointcloud_or_mesh_packet"),
        "contact_or_context_sheet": manifest.get("contact_or_context_sheet"),
    }
    return output


def deployable_evidence_after_label_lock(row: dict[str, str], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "semantic_evidence": {
            "semantic_rank": manifest.get("semantic_rank_hidden"),
            "semantic_score_raw": manifest.get("semantic_score_raw_hidden"),
            "semantic_score_norm": manifest.get("semantic_score_norm_hidden"),
            "available_after_label_lock": True,
        },
        "geometry_scalar_evidence": {
            "p_geom_valid": manifest.get("p_geom_valid_hidden"),
            "role": "geometry_only_baseline_scalar",
            "available_after_label_lock": True,
        },
        "coverage_evidence": {
            "evidence_packet_status": row.get("evidence_packet_status"),
            "packet_status": manifest.get("packet_status_hidden"),
            "primary_gap_decision": manifest.get("primary_gap_decision_hidden"),
            "diagnostic_status": manifest.get("diagnostic_status_hidden"),
        },
        "audit_packet_evidence": {
            "packet_paths": {
                "multiview_packet": manifest.get("multiview_packet"),
                "pointcloud_or_mesh_packet": manifest.get("pointcloud_or_mesh_packet"),
                "contact_or_context_sheet": manifest.get("contact_or_context_sheet"),
            },
            "multi_view_as_model_input": False,
            "used_for_label_audit_only": True,
        },
        "forbidden_as_posterior_input": {
            "v6_review_fields": True,
            "label_geometry_bucket_hidden": True,
            "source_queue_hidden": True,
            "geometry_status_hidden": True,
            "label_match_status_hidden": True,
            "counterfactual_pair_id_hidden": True,
            "exact_endpoint_pair_key_hidden": True,
            "subject_object_label_pair_hidden": True,
            "machine_hint_hidden": True,
            "asset_packet_source_hidden": True,
            "audit_packet_paths": True,
            "multi_view_content": True,
        },
    }


def base_identity(row: dict[str, str], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": row["blind_review_id"],
        "prediction_id": manifest.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("scene_context_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "review_scope": row.get("review_scope"),
        "evidence_packet_status": row.get("evidence_packet_status"),
        "packet_gap_decision": manifest.get("primary_gap_decision_hidden") or manifest.get("row_gap_decision_hidden") or "primary_label_ready",
    }


def target_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is None:
        return None
    hidden = label["hidden_audit_metadata_post_label_only"]
    row = {
        "schema_version": schema_version.replace("endpoint_pair_counterfactual", "endpoint_pair_counterfactual_repair"),
        "target_name": target["target_name"],
        "target_y": target["target_y"],
        "target_use": target["target_use"],
        "target_reason": target["reason"],
        "blind_review_id": label["blind_review_id"],
        "prediction_id": label["prediction_id"],
        "scan_id": label["scan_id"],
        "subgraph_id": label["subgraph_id"],
        "subject_id": label["subject_id"],
        "subject_label": label["subject_label"],
        "predicate_label": label["predicate_label"],
        "predicate_family": label["predicate_family"],
        "object_id": label["object_id"],
        "object_label": label["object_label"],
        "subject_object_label_pair_visible": f"{label['subject_label']}|{label['object_label']}",
        "review_scope": label.get("review_scope"),
        "evidence_packet_status": label["evidence_packet_status"],
        "packet_gap_decision": label["packet_gap_decision"],
        "filled_by": "codex_proxy",
        "actual_user_reviewer": False,
        "paper_locked": False,
    }
    if "target_class_id" in target:
        row["target_class_id"] = target["target_class_id"]
    for key in HIDDEN_GROUP_KEYS:
        row[key] = hidden.get(key)
    return row


def build_summary_status(
    errors: list[dict[str, Any]],
    probes: dict[str, dict[str, Any]],
    reliability_binary_count: dict[str, Any],
    multiclass_count: dict[str, Any],
) -> tuple[str, str, str]:
    any_probe_risk = any(probe["status"] != "target_independence_probe_pass" for probe in probes.values())
    enough_binary_mass = reliability_binary_count.get("positive", 0) >= 20 and reliability_binary_count.get("negative", 0) >= 20
    enough_multiclass_mass = all(
        multiclass_count.get("classes", {}).get(label, 0) >= 20
        for label in ["accept_reliable", "reject_unreliable", "abstain_uncertain"]
    )
    if errors:
        return (
            "h002_reliability_target_v8_repair_label_ingestion_errors",
            "Fix v8 repair endpoint-pair counterfactual label ingestion errors before target audit.",
            "fix_reliability_target_v8_endpoint_pair_counterfactual_repair_label_ingestion_errors",
        )
    if not enough_multiclass_mass:
        return (
            "h002_reliability_target_v8_repair_label_ingested_multiclass_sparse",
            "V8 repair labels are ingested, but at least one multiclass reliability state is sparse.",
            "reliability_target_v8_endpoint_pair_counterfactual_repair_target_independence_audit",
        )
    if not enough_binary_mass:
        return (
            "h002_reliability_target_v8_repair_label_ingested_binary_sparse",
            "V8 repair labels are ingested, but binary reliable/unreliable diagnostic mass is sparse.",
            "reliability_target_v8_endpoint_pair_counterfactual_repair_target_independence_audit",
        )
    if any_probe_risk:
        return (
            "h002_reliability_target_v8_repair_label_ingested_with_probe_risk",
            "V8 repair labels are ingested, but hidden/visible shortcut probes flag target-construction risk. Run repair target-independence audit before any posterior smoke.",
            "reliability_target_v8_endpoint_pair_counterfactual_repair_target_independence_audit",
        )
    return (
        "h002_reliability_target_v8_repair_label_ingested_ready_for_target_independence_audit",
        "V8 repair labels are ingested. Run dedicated target-independence audit before posterior smoke.",
        "reliability_target_v8_endpoint_pair_counterfactual_repair_target_independence_audit",
    )


def write_report(path: Path, summary: dict[str, Any]) -> None:
    targets = summary["counts"]["targets"]
    probes = summary["target_independence_probes"]
    multiclass = targets[base.RELIABILITY_MULTICLASS]
    binary = targets[base.RELIABILITY_BINARY]
    geometry = targets[base.GEOMETRY_TARGET]
    usefulness = targets[base.USEFULNESS_TARGET]
    lines = [
        "# H002 Reliability Target V8 Repair Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage ingestion.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Labels are user-requested Codex proxy labels, not independent human annotation.",
        "- V6 review fields are target/audit fields and must not be posterior input.",
        "- Hidden manifest is joined only after label lock.",
        "- Multi-view/mesh packet evidence remains audit evidence only, not model input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Target Counts",
        "",
        "| Target | Rows | Classes / Pos-Neg | Excluded |",
        "| --- | ---: | --- | ---: |",
        f"| `{base.RELIABILITY_MULTICLASS}` | {multiclass['rows']} | `{multiclass['classes']}` | 0 |",
        f"| `{base.RELIABILITY_BINARY}` | {binary['rows']} | `pos={binary.get('positive', 0)}, neg={binary.get('negative', 0)}` | {summary['counts']['excluded_targets'][base.RELIABILITY_BINARY]} |",
        f"| `{base.GEOMETRY_TARGET}` | {geometry['rows']} | `pos={geometry.get('positive', 0)}, neg={geometry.get('negative', 0)}` | {summary['counts']['excluded_targets'][base.GEOMETRY_TARGET]} |",
        f"| `{base.USEFULNESS_TARGET}` | {usefulness['rows']} | `pos={usefulness.get('positive', 0)}, neg={usefulness.get('negative', 0)}` | {summary['counts']['excluded_targets'][base.USEFULNESS_TARGET]} |",
        "",
        "## Probe",
        "",
        "| Target | Probe Status | Hidden Risks | Visible Risks |",
        "| --- | --- | ---: | ---: |",
    ]
    for target_name in [base.RELIABILITY_MULTICLASS, base.RELIABILITY_BINARY, base.GEOMETRY_TARGET, base.USEFULNESS_TARGET]:
        probe = probes[target_name]
        lines.append(f"| `{target_name}` | `{probe['status']}` | {len(probe['hidden_risks'])} | {len(probe['visible_non_target_shortcuts'])} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def patch_base() -> None:
    base.LABEL_SOURCE = LABEL_SOURCE
    base.VISIBLE_GROUP_KEYS = VISIBLE_GROUP_KEYS
    base.HIDDEN_GROUP_KEYS = HIDDEN_GROUP_KEYS
    base.validate_fill_summary = validate_fill_summary
    base.validate_row = validate_row
    base.hidden_metadata = hidden_metadata
    base.deployable_evidence_after_label_lock = deployable_evidence_after_label_lock
    base.base_identity = base_identity
    base.target_row = target_row
    base.build_summary_status = build_summary_status
    base.write_report = write_report


def summarize_probe_counts(summary: dict[str, Any]) -> dict[str, int]:
    probes = summary["target_independence_probes"]
    return {
        "hidden_risks": sum(len(probe["hidden_risks"]) for probe in probes.values()),
        "visible_risks": sum(len(probe["visible_non_target_shortcuts"]) for probe in probes.values()),
    }


def main() -> int:
    patch_base()
    summary = base.run(parse_args())
    targets = summary["counts"]["targets"]
    multiclass = targets[base.RELIABILITY_MULTICLASS]
    reliability = targets[base.RELIABILITY_BINARY]
    geometry = targets[base.GEOMETRY_TARGET]
    usefulness = targets[base.USEFULNESS_TARGET]
    probe_counts = summarize_probe_counts(summary)
    print(
        "status={status} rows={rows} multiclass={multiclass} rel_binary={rel_rows} rel_pos={rel_pos} "
        "rel_neg={rel_neg} geom_binary={geom_rows} geom_pos={geom_pos} geom_neg={geom_neg} "
        "use_binary={use_rows} use_pos={use_pos} use_neg={use_neg} errors={errors} "
        "hidden_probe_risks={hidden_risks} visible_probe_risks={visible_risks} "
        "validation_used={validation_used} test_used={test_used} posterior_allowed={posterior_allowed} "
        "next={next_todo}".format(
            status=summary["status"],
            rows=summary["counts"]["rows"],
            multiclass=multiclass["classes"],
            rel_rows=reliability["rows"],
            rel_pos=reliability.get("positive", 0),
            rel_neg=reliability.get("negative", 0),
            geom_rows=geometry["rows"],
            geom_pos=geometry.get("positive", 0),
            geom_neg=geometry.get("negative", 0),
            use_rows=usefulness["rows"],
            use_pos=usefulness.get("positive", 0),
            use_neg=usefulness.get("negative", 0),
            errors=summary["counts"]["ingestion_errors"],
            hidden_risks=probe_counts["hidden_risks"],
            visible_risks=probe_counts["visible_risks"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
