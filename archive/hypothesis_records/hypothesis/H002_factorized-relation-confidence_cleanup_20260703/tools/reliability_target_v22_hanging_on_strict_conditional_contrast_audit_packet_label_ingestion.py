#!/usr/bin/env python3
"""Ingest H002 v22 hanging-on audit-packet labels after visible label lock."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_FILL_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_fill"
DEFAULT_MATERIALIZATION_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_materialization"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion"

DEFAULT_FILL_SUMMARY = DEFAULT_FILL_DIR / "summary.json"
DEFAULT_FILLED_SHEET = DEFAULT_FILL_DIR / "filled_visible_review_sheet_v22.tsv"
DEFAULT_LABEL_DECISIONS = DEFAULT_FILL_DIR / "label_decisions_v22.jsonl"
DEFAULT_HIDDEN_MANIFEST = DEFAULT_MATERIALIZATION_DIR / "materialized_hidden_manifest.jsonl"

SCHEMA_VERSION = "h002_reliability_target_v22_hanging_on_label_ingestion_v1"
TARGET_SCHEMA = "h002_reliability_target_v22_hanging_on_target_record_v1"
EXPECTED_FILL_STATUS = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_filled_codex_visible_packet"
EXPECTED_FILL_NEXT = "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion"
EXPECTED_MANIFEST_SCHEMA = "h002_reliability_target_v22_hanging_on_audit_packet_materialized_hidden_manifest_v1"

STATUS_READY_FOR_AUDIT = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingested_ready_for_target_independence_audit"
STATUS_POSITIVE_SPARSE_WITH_RISK = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingested_positive_sparse_with_probe_risk"
STATUS_POSITIVE_SPARSE = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingested_positive_sparse"
STATUS_WITH_RISK = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingested_with_probe_risk"
STATUS_ERROR = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion_errors"
NEXT_TODO = "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_target_independence_audit"

LABEL_SOURCE = "codex_visible_packet_labeler_v22_user_requested"
MIN_CLASS_MASS_FOR_POSTERIOR = 60

MULTICLASS_TARGET = "hanging_on_reliability_v22_multiclass"
PRIMARY_BINARY_TARGET = "hanging_on_reliability_v22_binary"
GEOMETRY_SUPPORT_TARGET = "hanging_on_geometry_support_v22_binary"
ENDPOINT_TARGET = "hanging_on_endpoint_identity_v22_binary"
COVERAGE_TARGET = "hanging_on_coverage_v22_binary"
UNCERTAINTY_TARGET = "hanging_on_uncertainty_v22_multiclass"
EVIDENCE_TIER_TARGET = "hanging_on_evidence_tier_v22_multiclass"

FILLED_FIELDS = [
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
    "reviewer_id_v22",
    "review_round_v22",
    "label_policy_v22",
    "review_relation_reliability",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "review_notes",
]

PRIMARY_ROLE = "primary_hanging_on_reliability_candidate"
PRIMARY_PREDICATE = "hanging on"
ALLOWED_RELIABILITY = {"accept_reliable", "reject_unreliable", "abstain_uncertain"}
ALLOWED_GEOMETRY_SUPPORT = {"supports", "contradicts", "ambiguous", "not_evaluable"}
ALLOWED_ENDPOINT = {"clear_endpoint_identity", "uncertain_endpoint_identity"}
ALLOWED_COVERAGE = {"sufficient", "limited"}
ALLOWED_UNCERTAINTY = {"low", "medium", "high", "visual_ambiguous", "endpoint_ambiguous", "ontology_ambiguous"}
ALLOWED_EVIDENCE_TIERS = {"T1_strong_pair_visual", "T2_individual_visual_plus_mesh"}

RELIABILITY_BINARY = {"accept_reliable": 1, "reject_unreliable": 0}
GEOMETRY_BINARY = {"supports": 1, "contradicts": 0}
ENDPOINT_BINARY = {"clear_endpoint_identity": 1, "uncertain_endpoint_identity": 0}
COVERAGE_BINARY = {"sufficient": 1, "limited": 0}

RISK_PREDICTORS = [
    "evidence_tier",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "primary_reason_v22",
    "subject_label",
    "object_label",
    "subject_object_visible_pair",
    "scan_id_hidden",
    "subgraph_id_hidden",
    "subject_id_hidden",
    "object_id_hidden",
    "audit_ready_state_hidden",
    "visual_context_state_hidden",
    "coverage_proxy_hidden",
    "rank_band_hidden",
    "geometry_bucket_hidden",
    "object_family_pair_hidden",
    "planned_proxy_role_hidden",
    "strict_group_value_hidden",
    "candidate_gt_label_match_status_hidden",
    "gt_label_match_status_hidden",
    "shared_origin_frame_bucket",
    "shared_crop_rank_bucket",
    "materialized_image_bucket",
]

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 10,
    "large_group_purity": 0.90,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fill-summary", type=Path, default=DEFAULT_FILL_SUMMARY)
    parser.add_argument("--filled-sheet", type=Path, default=DEFAULT_FILLED_SHEET)
    parser.add_argument("--label-decisions", type=Path, default=DEFAULT_LABEL_DECISIONS)
    parser.add_argument("--hidden-manifest", type=Path, default=DEFAULT_HIDDEN_MANIFEST)
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def bucket_count(value: int) -> str:
    if value <= 0:
        return "none"
    if value == 1:
        return "one"
    if value <= 3:
        return "two_or_three"
    return "four_or_more"


def visible_pair(subject: Any, obj: Any) -> str:
    return f"{norm(subject)}|{norm(obj)}"


def asset_group_counts(assets: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(str(asset.get("group", "")) for asset in assets))


def validate_fill_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_FILL_STATUS:
        errors.append({"error_type": "unexpected_fill_status", "expected": EXPECTED_FILL_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_FILL_NEXT:
        errors.append({"error_type": "unexpected_fill_next_todo", "expected": EXPECTED_FILL_NEXT, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "fill_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "hidden_manifest_read",
        "used_source_path",
        "used_scan_id",
        "used_existing_gt_match_axis",
        "used_proxy_role_or_strict_group_id",
        "used_geometry_status_or_rank_hint",
        "used_source_score_or_rank",
        "used_p_geom_valid",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_boundary_violation", "key": key, "expected": False, "actual": boundary.get(key)})
    expected_true = ["fills_new_labels", "visible_packet_label_fill", "used_visible_review_sheet", "used_packet_markdown", "used_packet_local_image_availability"]
    for key in expected_true:
        if boundary.get(key) is not True:
            errors.append({"error_type": "fill_boundary_violation", "key": key, "expected": True, "actual": boundary.get(key)})
    return errors


def validate_label_rows(fieldnames: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if fieldnames != FILLED_FIELDS:
        errors.append({"error_type": "filled_sheet_schema_mismatch", "expected": FILLED_FIELDS, "actual": fieldnames})
    if len(rows) != 240:
        errors.append({"error_type": "unexpected_filled_row_count", "expected": 240, "actual": len(rows)})
    for row_number, row in enumerate(rows, start=2):
        packet_id = row.get("packet_id", "")
        checks = [
            ("review_relation_reliability", ALLOWED_RELIABILITY),
            ("review_geometry_support", ALLOWED_GEOMETRY_SUPPORT),
            ("review_endpoint_identity", ALLOWED_ENDPOINT),
            ("review_coverage", ALLOWED_COVERAGE),
            ("review_uncertainty", ALLOWED_UNCERTAINTY),
        ]
        for field, allowed in checks:
            if row.get(field) not in allowed:
                errors.append({"error_type": f"invalid_{field}", "row_number": row_number, "packet_id": packet_id, "value": row.get(field)})
        if row.get("predicate_label") != PRIMARY_PREDICATE:
            errors.append({"error_type": "unexpected_predicate", "row_number": row_number, "packet_id": packet_id, "value": row.get("predicate_label")})
        if row.get("packet_role") != PRIMARY_ROLE:
            errors.append({"error_type": "unexpected_packet_role", "row_number": row_number, "packet_id": packet_id, "value": row.get("packet_role")})
        if row.get("evidence_tier") not in ALLOWED_EVIDENCE_TIERS:
            errors.append({"error_type": "unexpected_evidence_tier", "row_number": row_number, "packet_id": packet_id, "value": row.get("evidence_tier")})
        for field in FILLED_FIELDS:
            if field != "review_notes" and not str(row.get(field, "")).strip():
                errors.append({"error_type": "missing_filled_field", "row_number": row_number, "packet_id": packet_id, "field": field})
    return errors


def validate_decision_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(rows) != 240:
        errors.append({"error_type": "unexpected_decision_row_count", "expected": 240, "actual": len(rows)})
    for row_number, row in enumerate(rows, start=1):
        packet_id = row.get("packet_id", "")
        provenance = row.get("provenance", {})
        for key in [
            "used_hidden_manifest",
            "used_source_path",
            "used_scan_id",
            "used_existing_gt_match_axis",
            "used_proxy_role_or_strict_group_id",
            "used_geometry_status_or_rank_hint",
            "used_source_score_or_rank",
            "used_validation_or_test",
            "used_p_geom_valid",
            "used_multi_view_as_model_input",
            "used_mesh_as_model_input",
            "paper_evidence_allowed",
        ]:
            if provenance.get(key) is not False:
                errors.append({"error_type": "decision_provenance_violation", "row_number": row_number, "packet_id": packet_id, "key": key, "actual": provenance.get(key)})
        if "primary_reason_v22" not in row:
            errors.append({"error_type": "missing_primary_reason_v22", "row_number": row_number, "packet_id": packet_id})
    return errors


def validate_manifest_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(rows) != 240:
        errors.append({"error_type": "unexpected_manifest_row_count", "expected": 240, "actual": len(rows)})
    for row_number, row in enumerate(rows, start=1):
        packet_id = row.get("packet_id", "")
        if row.get("schema_version") != EXPECTED_MANIFEST_SCHEMA:
            errors.append({"error_type": "unexpected_manifest_schema", "row_number": row_number, "packet_id": packet_id, "actual": row.get("schema_version")})
        if row.get("predicate_label") != PRIMARY_PREDICATE:
            errors.append({"error_type": "unexpected_manifest_predicate", "row_number": row_number, "packet_id": packet_id, "actual": row.get("predicate_label")})
        if row.get("packet_role") != PRIMARY_ROLE:
            errors.append({"error_type": "unexpected_manifest_packet_role", "row_number": row_number, "packet_id": packet_id, "actual": row.get("packet_role")})
        if row.get("evidence_tier") not in ALLOWED_EVIDENCE_TIERS:
            errors.append({"error_type": "unexpected_manifest_evidence_tier", "row_number": row_number, "packet_id": packet_id, "actual": row.get("evidence_tier")})
        if row.get("model_input_allowed_now") is not False:
            errors.append({"error_type": "model_input_allowed_now_not_false", "row_number": row_number, "packet_id": packet_id, "actual": row.get("model_input_allowed_now")})
        for field in [
            "scan_id_hidden",
            "subgraph_id_hidden",
            "subject_id_hidden",
            "object_id_hidden",
            "packet_dir_hidden",
            "packet_markdown_hidden",
            "existing_gt_match_axis_hidden",
            "planned_proxy_role_hidden",
            "strict_group_value_hidden",
            "rank_band_hidden",
            "geometry_bucket_hidden",
        ]:
            if field not in row:
                errors.append({"error_type": "missing_hidden_manifest_field", "row_number": row_number, "packet_id": packet_id, "field": field})
    return errors


def validate_id_sets(
    label_rows: list[dict[str, str]],
    decision_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    groups = {
        "filled_sheet": [row.get("packet_id", "") for row in label_rows],
        "label_decisions": [row.get("packet_id", "") for row in decision_rows],
        "hidden_manifest": [row.get("packet_id", "") for row in manifest_rows],
    }
    sets = {name: {packet_id for packet_id in ids if packet_id} for name, ids in groups.items()}
    for name, ids in groups.items():
        for packet_id, count in Counter(ids).items():
            if packet_id and count > 1:
                errors.append({"error_type": f"duplicate_{name}_packet_id", "packet_id": packet_id, "count": count})
    for source, target in [
        ("filled_sheet", "label_decisions"),
        ("filled_sheet", "hidden_manifest"),
        ("label_decisions", "filled_sheet"),
        ("hidden_manifest", "filled_sheet"),
    ]:
        for packet_id in sorted(sets[source] - sets[target]):
            errors.append({"error_type": f"{source}_packet_missing_from_{target}", "packet_id": packet_id})
    return errors


def join_rows(
    label_rows: list[dict[str, str]],
    decision_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decision_by_packet = {row["packet_id"]: row for row in decision_rows}
    manifest_by_packet = {row["packet_id"]: row for row in manifest_rows}
    joined: list[dict[str, Any]] = []
    for label in label_rows:
        packet_id = label["packet_id"]
        decision = decision_by_packet[packet_id]
        manifest = manifest_by_packet[packet_id]
        gt_axis = manifest.get("existing_gt_match_axis_hidden") or {}
        copied_assets = manifest.get("copied_assets_hidden", []) or []
        shared_origin_count = len(manifest.get("shared_origin_frames_hidden", []) or [])
        shared_rank_count = len(manifest.get("shared_crop_view_ranks_hidden", []) or [])
        image_count = len(copied_assets)
        reliability = label["review_relation_reliability"]
        geometry_support = label["review_geometry_support"]
        row = {
            "schema_version": SCHEMA_VERSION,
            "label_source": LABEL_SOURCE,
            "split": "train",
            "packet_id": packet_id,
            "blind_review_id": label["blind_review_id"],
            "candidate_relation": label["candidate_relation"],
            "scan_id_hidden": manifest.get("scan_id_hidden"),
            "subgraph_id_hidden": manifest.get("subgraph_id_hidden"),
            "source_id_hidden": manifest.get("source_id_hidden"),
            "prediction_id_hidden": manifest.get("prediction_id_hidden"),
            "subject_id_hidden": manifest.get("subject_id_hidden"),
            "subject_label": label["subject_label"],
            "predicate_label": label["predicate_label"],
            "predicate_family": "attachment_deferred",
            "object_id_hidden": manifest.get("object_id_hidden"),
            "object_label": label["object_label"],
            "subject_object_visible_pair": visible_pair(label["subject_label"], label["object_label"]),
            "relation_family_visible": label["relation_family_visible"],
            "packet_role": label["packet_role"],
            "evidence_tier": label["evidence_tier"],
            "audit_ready_state_hidden": manifest.get("audit_ready_state_hidden"),
            "visual_context_state_hidden": manifest.get("visual_context_state_hidden"),
            "coverage_proxy_hidden": manifest.get("coverage_proxy_hidden"),
            "rank_band_hidden": manifest.get("rank_band_hidden"),
            "geometry_bucket_hidden": manifest.get("geometry_bucket_hidden"),
            "object_family_pair_hidden": manifest.get("object_family_pair_hidden"),
            "uncertainty_bucket_hidden": manifest.get("uncertainty_bucket_hidden"),
            "planned_proxy_role_hidden": manifest.get("planned_proxy_role_hidden"),
            "strict_group_value_hidden": manifest.get("strict_group_value_hidden"),
            "candidate_gt_label_match_status_hidden": manifest.get("candidate_gt_label_match_status_hidden"),
            "mesh_ready_hidden": bool(manifest.get("mesh_ready_hidden")),
            "sequence_ready_hidden": bool(manifest.get("sequence_ready_hidden")),
            "shared_origin_frame_count": shared_origin_count,
            "shared_origin_frame_bucket": bucket_count(shared_origin_count),
            "shared_crop_rank_count": shared_rank_count,
            "shared_crop_rank_bucket": bucket_count(shared_rank_count),
            "materialized_image_count": image_count,
            "materialized_image_bucket": bucket_count(image_count),
            "asset_group_counts": asset_group_counts(copied_assets),
            "visual_context_summary": label["visual_context_summary"],
            "mesh_context_summary": label["mesh_context_summary"],
            "reviewer_id_v22": label["reviewer_id_v22"],
            "review_round_v22": label["review_round_v22"],
            "label_policy_v22": label["label_policy_v22"],
            "review_relation_reliability": reliability,
            "relation_reliability_multiclass_target": reliability,
            "relation_reliability_binary_target": RELIABILITY_BINARY.get(reliability),
            "relation_reliability_binary_usable": reliability in RELIABILITY_BINARY,
            "review_geometry_support": geometry_support,
            "geometry_support_binary_target": GEOMETRY_BINARY.get(geometry_support),
            "geometry_support_binary_usable": geometry_support in GEOMETRY_BINARY,
            "review_endpoint_identity": label["review_endpoint_identity"],
            "endpoint_identity_binary_target": ENDPOINT_BINARY.get(label["review_endpoint_identity"]),
            "review_coverage": label["review_coverage"],
            "coverage_binary_target": COVERAGE_BINARY.get(label["review_coverage"]),
            "review_uncertainty": label["review_uncertainty"],
            "review_notes": label["review_notes"],
            "primary_reason_v22": decision.get("primary_reason_v22"),
            "packet_markdown_exists": bool(decision.get("packet_markdown_exists")),
            "local_image_count": int(decision.get("local_image_count", 0)),
            "gt_label_match_status_hidden": gt_axis.get("label_match_status_hidden"),
            "gt_label_match_hidden": gt_axis.get("label_match_hidden"),
            "gt_family_match_hidden": gt_axis.get("family_match_hidden"),
            "gt_matched_predicates_hidden": gt_axis.get("matched_predicates_hidden"),
            "gt_matched_families_hidden": gt_axis.get("matched_families_hidden"),
            "gt_label_source_hidden": gt_axis.get("label_source_hidden"),
            "gt_semantic_score_norm_hidden": gt_axis.get("semantic_score_norm_hidden"),
            "gt_rank_in_context_hidden": gt_axis.get("rank_in_context_hidden"),
            "gt_geometry_status_hidden": gt_axis.get("geometry_status_hidden"),
            "gt_label_geometry_bucket_hidden": gt_axis.get("label_geometry_bucket_hidden"),
            "gt_p_geom_valid_hidden": gt_axis.get("p_geom_valid_hidden"),
            "packet_dir_hidden": manifest.get("packet_dir_hidden"),
            "packet_markdown_hidden": manifest.get("packet_markdown_hidden"),
        }
        joined.append(row)
    return joined


def target_record(row: dict[str, Any], target_name: str, target_value: Any) -> dict[str, Any]:
    return {
        "schema_version": TARGET_SCHEMA,
        "target_name": target_name,
        "target_value": target_value,
        "label_source": LABEL_SOURCE,
        "split": "train",
        "packet_id": row["packet_id"],
        "blind_review_id": row["blind_review_id"],
        "scan_id_hidden": row["scan_id_hidden"],
        "subgraph_id_hidden": row["subgraph_id_hidden"],
        "subject_id_hidden": row["subject_id_hidden"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id_hidden": row["object_id_hidden"],
        "object_label": row["object_label"],
        "packet_role": row["packet_role"],
        "evidence_tier": row["evidence_tier"],
        "primary_reason_v22": row["primary_reason_v22"],
        "gt_label_match_status_hidden": row["gt_label_match_status_hidden"],
    }


def build_targets(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "multiclass": [target_record(row, MULTICLASS_TARGET, row["relation_reliability_multiclass_target"]) for row in rows],
        "primary_binary": [
            target_record(row, PRIMARY_BINARY_TARGET, row["relation_reliability_binary_target"])
            for row in rows
            if row["relation_reliability_binary_usable"]
        ],
        "geometry_support": [
            target_record(row, GEOMETRY_SUPPORT_TARGET, row["geometry_support_binary_target"])
            for row in rows
            if row["geometry_support_binary_usable"]
        ],
        "endpoint_identity": [target_record(row, ENDPOINT_TARGET, row["endpoint_identity_binary_target"]) for row in rows],
        "coverage": [target_record(row, COVERAGE_TARGET, row["coverage_binary_target"]) for row in rows],
        "uncertainty": [target_record(row, UNCERTAINTY_TARGET, row["review_uncertainty"]) for row in rows],
        "evidence_tier": [target_record(row, EVIDENCE_TIER_TARGET, row["evidence_tier"]) for row in rows],
        "abstain": [
            {
                **target_record(row, PRIMARY_BINARY_TARGET, None),
                "review_relation_reliability": row["review_relation_reliability"],
                "review_geometry_support": row["review_geometry_support"],
                "review_endpoint_identity": row["review_endpoint_identity"],
                "review_coverage": row["review_coverage"],
                "review_uncertainty": row["review_uncertainty"],
                "primary_reason_v22": row["primary_reason_v22"],
            }
            for row in rows
            if not row["relation_reliability_binary_usable"]
        ],
    }


def entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    value = 0.0
    for count in counter.values():
        if count:
            p = count / total
            value -= p * math.log(p, 2)
    return value


def normalized_mutual_information(rows: list[dict[str, Any]], predictor: str, label: str) -> float:
    if not rows:
        return 0.0
    label_counts = Counter(str(row.get(label, "missing")) for row in rows)
    group_counts = Counter(str(row.get(predictor, "missing")) for row in rows)
    joint = Counter((str(row.get(predictor, "missing")), str(row.get(label, "missing"))) for row in rows)
    total = len(rows)
    mi = 0.0
    for (group, target), count in joint.items():
        pxy = count / total
        px = group_counts[group] / total
        py = label_counts[target] / total
        if pxy and px and py:
            mi += pxy * math.log(pxy / (px * py), 2)
    denom = math.sqrt(entropy(label_counts) * entropy(group_counts))
    return mi / denom if denom else 0.0


def majority_risk(rows: list[dict[str, Any]], predictor: str, label: str) -> dict[str, Any]:
    if not rows:
        return {
            "predictor": predictor,
            "label": label,
            "rows": 0,
            "majority_rule_accuracy": None,
            "majority_baseline_accuracy": None,
            "majority_excess_over_baseline": None,
            "normalized_mutual_information": None,
            "risk_flag": False,
            "label_counts": {},
            "groups": 0,
            "top_groups": [],
        }
    label_counts = Counter(str(row.get(label, "missing")) for row in rows)
    baseline = max(label_counts.values()) / len(rows)
    groups: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        groups[str(row.get(predictor, "missing"))][str(row.get(label, "missing"))] += 1
    correct = sum(max(counter.values()) for counter in groups.values())
    accuracy = correct / len(rows)
    nmi = normalized_mutual_information(rows, predictor, label)
    large_pure_group = False
    top_groups: list[dict[str, Any]] = []
    for group_value, counter in groups.items():
        total = sum(counter.values())
        majority_label, majority_count = counter.most_common(1)[0]
        majority_rate = majority_count / total
        if total >= RISK_THRESHOLDS["large_group_rows"] and majority_rate >= RISK_THRESHOLDS["large_group_purity"]:
            large_pure_group = True
        top_groups.append(
            {
                "group_value": group_value,
                "rows": total,
                "majority_label": majority_label,
                "majority_rate": majority_rate,
                "label_counts": dict(counter),
            }
        )
    top_groups.sort(key=lambda item: (-item["rows"], str(item["group_value"])))
    risk_flag = (
        accuracy >= RISK_THRESHOLDS["majority_rule_accuracy"]
        and accuracy - baseline >= RISK_THRESHOLDS["majority_excess_over_baseline"]
    ) or nmi >= RISK_THRESHOLDS["normalized_mutual_information"] or large_pure_group
    return {
        "predictor": predictor,
        "label": label,
        "rows": len(rows),
        "groups": len(groups),
        "label_counts": dict(label_counts),
        "majority_rule_accuracy": accuracy,
        "majority_baseline_accuracy": baseline,
        "majority_excess_over_baseline": accuracy - baseline,
        "normalized_mutual_information": nmi,
        "risk_flag": risk_flag,
        "top_groups": top_groups[:12],
    }


def probe_risks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        (rows, "relation_reliability_multiclass_target"),
        ([row for row in rows if row["relation_reliability_binary_usable"]], "relation_reliability_binary_target"),
        ([row for row in rows if row["geometry_support_binary_usable"]], "geometry_support_binary_target"),
        (rows, "endpoint_identity_binary_target"),
        (rows, "coverage_binary_target"),
        (rows, "review_uncertainty"),
    ]
    out: list[dict[str, Any]] = []
    for label_rows, label in specs:
        for predictor in RISK_PREDICTORS:
            out.append(majority_risk(label_rows, predictor, label))
    return out


def gt_group(row: dict[str, Any]) -> str:
    status = row.get("gt_label_match_status_hidden")
    if status in {"exact_match", "family_match"}:
        return "GT_match"
    if status in {"pair_has_other_predicate", "no_gt_for_pair"}:
        return "No_GT_current_relation"
    return "GT_unknown"


def mismatch_table(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter((gt_group(row), row["review_relation_reliability"]) for row in rows)
    output: list[dict[str, Any]] = []
    for gt_state in ["GT_match", "No_GT_current_relation", "GT_unknown"]:
        for reliability in ["accept_reliable", "reject_unreliable", "abstain_uncertain"]:
            output.append({"gt_group": gt_state, "review_relation_reliability": reliability, "rows": counts.get((gt_state, reliability), 0)})
    return output


def group_contrast(rows: list[dict[str, Any]], group_field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(group_field, "missing"))].append(row)
    out: list[dict[str, Any]] = []
    for group_value, group_rows in grouped.items():
        rel_counts = Counter(row["review_relation_reliability"] for row in group_rows)
        binary_values = {row["relation_reliability_binary_target"] for row in group_rows if row["relation_reliability_binary_usable"]}
        geom_values = {row["geometry_support_binary_target"] for row in group_rows if row["geometry_support_binary_usable"]}
        uncertainty_values = {row["review_uncertainty"] for row in group_rows}
        out.append(
            {
                "group_field": group_field,
                "group_value": group_value,
                "rows": len(group_rows),
                "accept": rel_counts.get("accept_reliable", 0),
                "reject": rel_counts.get("reject_unreliable", 0),
                "abstain": rel_counts.get("abstain_uncertain", 0),
                "mixed_primary_binary": len(binary_values) > 1,
                "mixed_geometry_support_binary": len(geom_values) > 1,
                "mixed_uncertainty": len(uncertainty_values) > 1,
            }
        )
    out.sort(key=lambda item: (-item["rows"], str(item["group_value"])))
    return out


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    viability = summary["target_viability"]
    lines = [
        "# H002 V22 Hanging-On Audit Packet Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Result",
        "",
        "Joined the locked v22 visible-packet labels with the hidden packet manifest after label fill.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"multiclass_rows = {counts['multiclass_rows']}",
        f"primary_binary_rows = {counts['primary_binary_rows']}",
        f"geometry_support_rows = {counts['geometry_support_rows']}",
        f"endpoint_identity_rows = {counts['endpoint_identity_rows']}",
        f"coverage_rows = {counts['coverage_rows']}",
        f"uncertainty_rows = {counts['uncertainty_rows']}",
        f"abstain_rows = {counts['abstain_rows']}",
        f"review_relation_reliability = {counts['review_relation_reliability']}",
        f"primary_binary_target = {counts['primary_binary_target']}",
        f"geometry_support_target = {counts['geometry_support_target']}",
        f"gt_label_match_status = {counts['gt_label_match_status']}",
        f"quick_probe_risk_flags = {counts['quick_probe_risk_flags']}",
        "```",
        "",
        "## Target Viability",
        "",
        "```text",
        f"minimum_per_class_for_posterior = {viability['minimum_per_class_for_posterior']}",
        f"reliability_positive_rows = {viability['reliability_positive_rows']}",
        f"reliability_negative_rows = {viability['reliability_negative_rows']}",
        f"class_mass_pass = {viability['class_mass_pass']}",
        f"same_scan_mixed_primary_binary_groups = {viability['same_scan_mixed_primary_binary_groups']}",
        f"same_visible_pair_mixed_primary_binary_groups = {viability['same_visible_pair_mixed_primary_binary_groups']}",
        f"same_strict_group_mixed_primary_binary_groups = {viability['same_strict_group_mixed_primary_binary_groups']}",
        f"same_proxy_role_mixed_primary_binary_groups = {viability['same_proxy_role_mixed_primary_binary_groups']}",
        "```",
        "",
        "The primary binary target is severe positive-sparse, so posterior smoke remains blocked even before the full target-independence audit.",
        "",
        "## Boundary",
        "",
        "The hidden manifest and existing GT-match axis are read only after label lock for target construction, mismatch analysis, and shortcut audit. Hidden fields are not model inputs. Multi-view and mesh remain audit/confirmation evidence only.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    fill_summary_path = as_abs(args.fill_summary)
    filled_sheet_path = as_abs(args.filled_sheet)
    label_decisions_path = as_abs(args.label_decisions)
    hidden_manifest_path = as_abs(args.hidden_manifest)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fill_summary = read_json(fill_summary_path)
    fieldnames, label_rows = read_tsv(filled_sheet_path)
    decision_rows = read_jsonl(label_decisions_path)
    manifest_rows = read_jsonl(hidden_manifest_path)

    validation_errors = validate_fill_summary(fill_summary)
    validation_errors.extend(validate_label_rows(fieldnames, label_rows))
    validation_errors.extend(validate_decision_rows(decision_rows))
    validation_errors.extend(validate_manifest_rows(manifest_rows))
    validation_errors.extend(validate_id_sets(label_rows, decision_rows, manifest_rows))

    rows = join_rows(label_rows, decision_rows, manifest_rows) if not validation_errors else []
    targets = build_targets(rows)
    risks = probe_risks(rows)
    risk_flags = [risk for risk in risks if risk.get("risk_flag")]

    scan_contrast = group_contrast(rows, "scan_id_hidden")
    visible_pair_contrast = group_contrast(rows, "subject_object_visible_pair")
    tier_contrast = group_contrast(rows, "evidence_tier")
    reason_contrast = group_contrast(rows, "primary_reason_v22")
    proxy_role_contrast = group_contrast(rows, "planned_proxy_role_hidden")
    strict_group_contrast = group_contrast(rows, "strict_group_value_hidden")
    geometry_bucket_contrast = group_contrast(rows, "geometry_bucket_hidden")
    rank_band_contrast = group_contrast(rows, "rank_band_hidden")
    gt_status_contrast = group_contrast(rows, "gt_label_match_status_hidden")
    gt_mismatch = mismatch_table(rows)

    rel_counts = Counter(row["review_relation_reliability"] for row in rows)
    geom_counts = Counter(row["review_geometry_support"] for row in rows)
    endpoint_counts = Counter(row["review_endpoint_identity"] for row in rows)
    coverage_counts = Counter(row["review_coverage"] for row in rows)
    uncertainty_counts = Counter(row["review_uncertainty"] for row in rows)
    primary_binary_counts = Counter(str(row["relation_reliability_binary_target"]) for row in rows if row["relation_reliability_binary_usable"])
    geom_binary_counts = Counter(str(row["geometry_support_binary_target"]) for row in rows if row["geometry_support_binary_usable"])
    endpoint_binary_counts = Counter(str(row["endpoint_identity_binary_target"]) for row in rows)
    coverage_binary_counts = Counter(str(row["coverage_binary_target"]) for row in rows)
    gt_status_counts = Counter(str(row["gt_label_match_status_hidden"]) for row in rows)
    tier_counts = Counter(row["evidence_tier"] for row in rows)
    audit_state_counts = Counter(str(row["audit_ready_state_hidden"]) for row in rows)
    visual_state_counts = Counter(str(row["visual_context_state_hidden"]) for row in rows)
    reason_counts = Counter(str(row["primary_reason_v22"]) for row in rows)
    proxy_counts = Counter(str(row["planned_proxy_role_hidden"]) for row in rows)
    rank_counts = Counter(str(row["rank_band_hidden"]) for row in rows)
    geom_bucket_counts = Counter(str(row["geometry_bucket_hidden"]) for row in rows)
    strict_group_counts = Counter(str(row["strict_group_value_hidden"]) for row in rows)

    positive_rows = sum(1 for row in rows if row["relation_reliability_binary_usable"] and row["relation_reliability_binary_target"] == 1)
    negative_rows = sum(1 for row in rows if row["relation_reliability_binary_usable"] and row["relation_reliability_binary_target"] == 0)
    class_mass_pass = positive_rows >= MIN_CLASS_MASS_FOR_POSTERIOR and negative_rows >= MIN_CLASS_MASS_FOR_POSTERIOR

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "ingested_rows": output_dir / "ingested_rows.jsonl",
        "multiclass_target": output_dir / "multiclass_target.jsonl",
        "primary_binary_target": output_dir / "primary_binary_target.jsonl",
        "geometry_support_target": output_dir / "geometry_support_target.jsonl",
        "endpoint_identity_target": output_dir / "endpoint_identity_target.jsonl",
        "coverage_target": output_dir / "coverage_target.jsonl",
        "uncertainty_target": output_dir / "uncertainty_target.jsonl",
        "evidence_tier_target": output_dir / "evidence_tier_target.jsonl",
        "abstain_rows": output_dir / "abstain_rows.jsonl",
        "quick_probe_risks": output_dir / "quick_probe_risks.json",
        "gt_reliability_mismatch_table": output_dir / "gt_reliability_mismatch_table.csv",
        "scan_contrast_summary": output_dir / "scan_contrast_summary.csv",
        "visible_pair_contrast_summary": output_dir / "visible_pair_contrast_summary.csv",
        "tier_contrast_summary": output_dir / "tier_contrast_summary.csv",
        "reason_contrast_summary": output_dir / "reason_contrast_summary.csv",
        "proxy_role_contrast_summary": output_dir / "proxy_role_contrast_summary.csv",
        "strict_group_contrast_summary": output_dir / "strict_group_contrast_summary.csv",
        "geometry_bucket_contrast_summary": output_dir / "geometry_bucket_contrast_summary.csv",
        "rank_band_contrast_summary": output_dir / "rank_band_contrast_summary.csv",
        "gt_status_contrast_summary": output_dir / "gt_status_contrast_summary.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    if validation_errors:
        status = STATUS_ERROR
    elif not class_mass_pass and risk_flags:
        status = STATUS_POSITIVE_SPARSE_WITH_RISK
    elif not class_mass_pass:
        status = STATUS_POSITIVE_SPARSE
    elif risk_flags:
        status = STATUS_WITH_RISK
    else:
        status = STATUS_READY_FOR_AUDIT

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "fill_summary": rel_path(fill_summary_path),
            "filled_sheet": rel_path(filled_sheet_path),
            "label_decisions": rel_path(label_decisions_path),
            "hidden_manifest": rel_path(hidden_manifest_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": {
            "rows": len(rows),
            "multiclass_rows": len(targets["multiclass"]),
            "primary_binary_rows": len(targets["primary_binary"]),
            "geometry_support_rows": len(targets["geometry_support"]),
            "endpoint_identity_rows": len(targets["endpoint_identity"]),
            "coverage_rows": len(targets["coverage"]),
            "uncertainty_rows": len(targets["uncertainty"]),
            "evidence_tier_rows": len(targets["evidence_tier"]),
            "abstain_rows": len(targets["abstain"]),
            "review_relation_reliability": dict(sorted(rel_counts.items())),
            "review_geometry_support": dict(sorted(geom_counts.items())),
            "review_endpoint_identity": dict(sorted(endpoint_counts.items())),
            "review_coverage": dict(sorted(coverage_counts.items())),
            "review_uncertainty": dict(sorted(uncertainty_counts.items())),
            "primary_binary_target": dict(sorted(primary_binary_counts.items())),
            "geometry_support_target": dict(sorted(geom_binary_counts.items())),
            "endpoint_identity_target": dict(sorted(endpoint_binary_counts.items())),
            "coverage_target": dict(sorted(coverage_binary_counts.items())),
            "gt_label_match_status": dict(sorted(gt_status_counts.items())),
            "evidence_tier": dict(sorted(tier_counts.items())),
            "audit_ready_state_hidden": dict(sorted(audit_state_counts.items())),
            "visual_context_state_hidden": dict(sorted(visual_state_counts.items())),
            "primary_reason_v22": dict(sorted(reason_counts.items())),
            "planned_proxy_role_hidden": dict(sorted(proxy_counts.items())),
            "rank_band_hidden": dict(sorted(rank_counts.items())),
            "geometry_bucket_hidden": dict(sorted(geom_bucket_counts.items())),
            "strict_group_count": len(strict_group_counts),
            "scan_groups": len(scan_contrast),
            "visible_pair_groups": len(visible_pair_contrast),
            "tier_groups": len(tier_contrast),
            "reason_groups": len(reason_contrast),
            "proxy_role_groups": len(proxy_role_contrast),
            "strict_group_contrast_groups": len(strict_group_contrast),
            "geometry_bucket_groups": len(geometry_bucket_contrast),
            "rank_band_groups": len(rank_band_contrast),
            "gt_status_groups": len(gt_status_contrast),
            "quick_probe_risk_flags": len(risk_flags),
        },
        "target_viability": {
            "minimum_per_class_for_posterior": MIN_CLASS_MASS_FOR_POSTERIOR,
            "reliability_positive_rows": positive_rows,
            "reliability_negative_rows": negative_rows,
            "class_mass_pass": class_mass_pass,
            "same_scan_mixed_primary_binary_groups": sum(1 for row in scan_contrast if row["mixed_primary_binary"]),
            "same_visible_pair_mixed_primary_binary_groups": sum(1 for row in visible_pair_contrast if row["mixed_primary_binary"]),
            "same_evidence_tier_mixed_primary_binary_groups": sum(1 for row in tier_contrast if row["mixed_primary_binary"]),
            "same_reason_mixed_primary_binary_groups": sum(1 for row in reason_contrast if row["mixed_primary_binary"]),
            "same_proxy_role_mixed_primary_binary_groups": sum(1 for row in proxy_role_contrast if row["mixed_primary_binary"]),
            "same_strict_group_mixed_primary_binary_groups": sum(1 for row in strict_group_contrast if row["mixed_primary_binary"]),
            "same_geometry_bucket_mixed_primary_binary_groups": sum(1 for row in geometry_bucket_contrast if row["mixed_primary_binary"]),
            "same_rank_band_mixed_primary_binary_groups": sum(1 for row in rank_band_contrast if row["mixed_primary_binary"]),
            "same_gt_status_mixed_primary_binary_groups": sum(1 for row in gt_status_contrast if row["mixed_primary_binary"]),
            "posterior_smoke_allowed_after_ingestion": False,
        },
        "quick_probe": {
            "risk_thresholds": RISK_THRESHOLDS,
            "risk_flags": [
                {
                    "predictor": risk["predictor"],
                    "label": risk["label"],
                    "rows": risk["rows"],
                    "majority_rule_accuracy": risk["majority_rule_accuracy"],
                    "majority_baseline_accuracy": risk["majority_baseline_accuracy"],
                    "majority_excess_over_baseline": risk["majority_excess_over_baseline"],
                    "normalized_mutual_information": risk["normalized_mutual_information"],
                }
                for risk in risk_flags
            ],
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": True,
            "reads_hidden_manifest_after_label_lock": True,
            "hidden_manifest_used_for_label_fill": False,
            "existing_gt_match_axis_used_for_label_fill": False,
            "existing_gt_match_axis_joined_after_label_lock": True,
            "hidden_fields_as_model_input": False,
            "uses_source_score_or_rank": False,
            "uses_geometry_status_or_rank_hint": False,
            "uses_p_geom_valid": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_jsonl(output_paths["ingested_rows"], rows)
    write_jsonl(output_paths["multiclass_target"], targets["multiclass"])
    write_jsonl(output_paths["primary_binary_target"], targets["primary_binary"])
    write_jsonl(output_paths["geometry_support_target"], targets["geometry_support"])
    write_jsonl(output_paths["endpoint_identity_target"], targets["endpoint_identity"])
    write_jsonl(output_paths["coverage_target"], targets["coverage"])
    write_jsonl(output_paths["uncertainty_target"], targets["uncertainty"])
    write_jsonl(output_paths["evidence_tier_target"], targets["evidence_tier"])
    write_jsonl(output_paths["abstain_rows"], targets["abstain"])
    write_json(output_paths["quick_probe_risks"], {"risk_thresholds": RISK_THRESHOLDS, "risks": risks})
    write_csv(output_paths["gt_reliability_mismatch_table"], gt_mismatch)
    write_csv(output_paths["scan_contrast_summary"], scan_contrast)
    write_csv(output_paths["visible_pair_contrast_summary"], visible_pair_contrast)
    write_csv(output_paths["tier_contrast_summary"], tier_contrast)
    write_csv(output_paths["reason_contrast_summary"], reason_contrast)
    write_csv(output_paths["proxy_role_contrast_summary"], proxy_role_contrast)
    write_csv(output_paths["strict_group_contrast_summary"], strict_group_contrast)
    write_csv(output_paths["geometry_bucket_contrast_summary"], geometry_bucket_contrast)
    write_csv(output_paths["rank_band_contrast_summary"], rank_band_contrast)
    write_csv(output_paths["gt_status_contrast_summary"], gt_status_contrast)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    viability = summary["target_viability"]
    print(f"status={summary['status']}")
    print(f"rows={counts['rows']}")
    print(f"multiclass_rows={counts['multiclass_rows']}")
    print(f"primary_binary_rows={counts['primary_binary_rows']}")
    print(f"geometry_support_rows={counts['geometry_support_rows']}")
    print(f"endpoint_identity_rows={counts['endpoint_identity_rows']}")
    print(f"coverage_rows={counts['coverage_rows']}")
    print(f"uncertainty_rows={counts['uncertainty_rows']}")
    print(f"abstain_rows={counts['abstain_rows']}")
    print(f"positive_rows={viability['reliability_positive_rows']}")
    print(f"negative_rows={viability['reliability_negative_rows']}")
    print(f"class_mass_pass={viability['class_mass_pass']}")
    print(f"gt_label_match_status={counts['gt_label_match_status']}")
    print(f"quick_probe_risk_flags={counts['quick_probe_risk_flags']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
