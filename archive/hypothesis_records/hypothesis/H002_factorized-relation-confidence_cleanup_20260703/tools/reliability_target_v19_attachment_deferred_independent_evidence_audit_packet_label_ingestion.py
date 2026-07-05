#!/usr/bin/env python3
"""Ingest H002 v19 attachment audit-packet labels after visible-packet label fill."""

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

DEFAULT_FILL_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_fill"
DEFAULT_MATERIALIZATION_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion"

DEFAULT_FILL_SUMMARY = DEFAULT_FILL_DIR / "summary.json"
DEFAULT_FILLED_SHEET = DEFAULT_FILL_DIR / "filled_visible_review_sheet_v19.tsv"
DEFAULT_LABEL_DECISIONS = DEFAULT_FILL_DIR / "label_decisions_v19.jsonl"
DEFAULT_HIDDEN_MANIFEST = DEFAULT_MATERIALIZATION_DIR / "materialized_hidden_manifest.jsonl"

SCHEMA_VERSION = "h002_reliability_target_v19_attachment_packet_label_ingestion_v1"
EXPECTED_FILL_STATUS = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_filled_codex_visible_packet"
EXPECTED_FILL_NEXT = "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion"
STATUS_READY_FOR_AUDIT = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingested_ready_for_target_independence_audit"
STATUS_POSITIVE_SPARSE_WITH_RISK = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingested_positive_sparse_with_probe_risk"
STATUS_POSITIVE_SPARSE = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingested_positive_sparse"
STATUS_WITH_RISK = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingested_with_probe_risk"
STATUS_ERROR = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion_errors"
NEXT_TODO = "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_target_independence_audit"

LABEL_SOURCE = "codex_visible_packet_labeler_v19_user_requested"
MIN_CLASS_MASS_FOR_POSTERIOR = 50

MULTICLASS_TARGET = "attachment_deferred_reliability_v19_multiclass"
BINARY_TARGET = "attachment_deferred_primary_reliability_v19_binary"
CONNECTED_TARGET = "attachment_deferred_connected_diagnostic_v19_multiclass"
GEOMETRY_SUPPORT_TARGET = "attachment_deferred_geometry_support_v19_binary"
UNCERTAINTY_TARGET = "attachment_deferred_uncertainty_v19_multiclass"
EVIDENCE_TIER_TARGET = "attachment_deferred_evidence_tier_v19_multiclass"

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
    "reviewer_id_v19",
    "review_round_v19",
    "label_policy_v19",
    "review_relation_reliability",
    "review_geometry_support",
    "review_uncertainty",
    "review_notes",
]

ALLOWED_RELIABILITY = {
    "accept_reliable_attachment",
    "reject_unreliable_attachment",
    "diagnostic_connected_possible",
    "diagnostic_connected_ambiguous",
    "abstain_uncertain",
}
ALLOWED_GEOMETRY_SUPPORT = {"supports", "contradicts", "ambiguous", "not_evaluable"}
ALLOWED_UNCERTAINTY = {"low", "medium", "high", "diagnostic_only"}
ALLOWED_PREDICATES = {"attached to", "hanging on", "connected to"}
ALLOWED_PACKET_ROLES = {
    "primary_attachment_reliability_candidate",
    "connected_diagnostic_only",
    "uncertainty_or_coverage_audit_only",
}
ALLOWED_EVIDENCE_TIERS = {"T1_strong_pair_visual", "T2_individual_visual_plus_mesh"}

PRIMARY_BINARY_MAP = {
    "accept_reliable_attachment": 1,
    "reject_unreliable_attachment": 0,
}
GEOMETRY_SUPPORT_BINARY_MAP = {
    "supports": 1,
    "contradicts": 0,
}

RISK_PREDICTORS = [
    "predicate_label",
    "packet_role",
    "evidence_tier",
    "audit_ready_state_hidden",
    "visual_context_state_hidden",
    "subject_label",
    "object_label",
    "subject_object_visible_pair",
    "scan_id_hidden",
    "subgraph_id_hidden",
    "subject_id_hidden",
    "object_id_hidden",
    "shared_origin_frame_bucket",
    "shared_crop_rank_bucket",
    "materialized_image_bucket",
    "primary_reason_v19",
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
        "used_v18_labels",
        "used_geometry_status_or_rank_hint",
        "used_source_score_or_rank",
        "used_p_geom_valid",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "connected_primary_binary_target",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_boundary_violation", "key": key, "expected": False, "actual": boundary.get(key)})
    for key in ["fills_new_labels", "visible_packet_label_fill", "used_visible_review_sheet", "used_packet_markdown", "used_packet_local_image_availability"]:
        if boundary.get(key) is not True:
            errors.append({"error_type": "fill_boundary_violation", "key": key, "expected": True, "actual": boundary.get(key)})
    return errors


def validate_id_sets(
    label_rows: list[dict[str, str]],
    decision_rows: list[dict[str, Any]],
    manifest_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    label_ids = [row.get("packet_id", "") for row in label_rows]
    decision_ids = [row.get("packet_id", "") for row in decision_rows]
    manifest_ids = [row.get("packet_id", "") for row in manifest_rows]
    for name, ids in [("filled_sheet", label_ids), ("label_decisions", decision_ids), ("hidden_manifest", manifest_ids)]:
        for packet_id, count in Counter(ids).items():
            if packet_id and count > 1:
                errors.append({"error_type": f"duplicate_{name}_packet_id", "packet_id": packet_id, "count": count})
    label_set = {packet_id for packet_id in label_ids if packet_id}
    decision_set = {packet_id for packet_id in decision_ids if packet_id}
    manifest_set = {packet_id for packet_id in manifest_ids if packet_id}
    for packet_id in sorted(label_set - decision_set):
        errors.append({"error_type": "filled_packet_missing_from_decisions", "packet_id": packet_id})
    for packet_id in sorted(label_set - manifest_set):
        errors.append({"error_type": "filled_packet_missing_from_manifest", "packet_id": packet_id})
    for packet_id in sorted(decision_set - label_set):
        errors.append({"error_type": "decision_packet_missing_from_filled_sheet", "packet_id": packet_id})
    for packet_id in sorted(manifest_set - label_set):
        errors.append({"error_type": "manifest_packet_missing_from_filled_sheet", "packet_id": packet_id})
    return errors


def validate_label_rows(fieldnames: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if fieldnames != FILLED_FIELDS:
        errors.append({"error_type": "filled_sheet_schema_mismatch", "expected": FILLED_FIELDS, "actual": fieldnames})
    if len(rows) != 240:
        errors.append({"error_type": "unexpected_filled_row_count", "expected": 240, "actual": len(rows)})
    for row_number, row in enumerate(rows, start=2):
        packet_id = row.get("packet_id", "")
        if row.get("review_relation_reliability") not in ALLOWED_RELIABILITY:
            errors.append({"error_type": "invalid_reliability", "row_number": row_number, "packet_id": packet_id, "value": row.get("review_relation_reliability")})
        if row.get("review_geometry_support") not in ALLOWED_GEOMETRY_SUPPORT:
            errors.append({"error_type": "invalid_geometry_support", "row_number": row_number, "packet_id": packet_id, "value": row.get("review_geometry_support")})
        if row.get("review_uncertainty") not in ALLOWED_UNCERTAINTY:
            errors.append({"error_type": "invalid_uncertainty", "row_number": row_number, "packet_id": packet_id, "value": row.get("review_uncertainty")})
        if row.get("predicate_label") not in ALLOWED_PREDICATES:
            errors.append({"error_type": "unexpected_predicate", "row_number": row_number, "packet_id": packet_id, "value": row.get("predicate_label")})
        if row.get("packet_role") not in ALLOWED_PACKET_ROLES:
            errors.append({"error_type": "unexpected_packet_role", "row_number": row_number, "packet_id": packet_id, "value": row.get("packet_role")})
        if row.get("evidence_tier") not in ALLOWED_EVIDENCE_TIERS:
            errors.append({"error_type": "unexpected_evidence_tier", "row_number": row_number, "packet_id": packet_id, "value": row.get("evidence_tier")})
        for field in FILLED_FIELDS:
            if field not in {"review_notes"} and not str(row.get(field, "")).strip():
                errors.append({"error_type": "missing_filled_field", "row_number": row_number, "packet_id": packet_id, "field": field})
    return errors


def validate_manifest_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(rows) != 240:
        errors.append({"error_type": "unexpected_manifest_row_count", "expected": 240, "actual": len(rows)})
    for row_number, row in enumerate(rows, start=1):
        packet_id = row.get("packet_id", "")
        if row.get("schema_version") != "h002_reliability_target_v19_attachment_audit_packet_materialized_hidden_manifest_v1":
            errors.append({"error_type": "unexpected_manifest_schema", "row_number": row_number, "packet_id": packet_id, "actual": row.get("schema_version")})
        if row.get("predicate_label") not in ALLOWED_PREDICATES:
            errors.append({"error_type": "unexpected_manifest_predicate", "row_number": row_number, "packet_id": packet_id, "actual": row.get("predicate_label")})
        if row.get("packet_role") not in ALLOWED_PACKET_ROLES:
            errors.append({"error_type": "unexpected_manifest_packet_role", "row_number": row_number, "packet_id": packet_id, "actual": row.get("packet_role")})
        if row.get("evidence_tier") not in ALLOWED_EVIDENCE_TIERS:
            errors.append({"error_type": "unexpected_manifest_evidence_tier", "row_number": row_number, "packet_id": packet_id, "actual": row.get("evidence_tier")})
        if row.get("model_input_allowed_now") is not False:
            errors.append({"error_type": "model_input_allowed_now_not_false", "row_number": row_number, "packet_id": packet_id, "actual": row.get("model_input_allowed_now")})
        for field in ["scan_id_hidden", "subgraph_id_hidden", "subject_id_hidden", "object_id_hidden", "packet_dir_hidden", "packet_markdown_hidden"]:
            if field not in row:
                errors.append({"error_type": "missing_hidden_manifest_field", "row_number": row_number, "packet_id": packet_id, "field": field})
    return errors


def validate_decision_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(rows) != 240:
        errors.append({"error_type": "unexpected_decision_row_count", "expected": 240, "actual": len(rows)})
    for row_number, row in enumerate(rows, start=1):
        provenance = row.get("provenance", {})
        packet_id = row.get("packet_id", "")
        for key in [
            "used_hidden_manifest",
            "used_source_path",
            "used_scan_id",
            "used_v18_labels",
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
        if "primary_reason_v19" not in row:
            errors.append({"error_type": "missing_primary_reason", "row_number": row_number, "packet_id": packet_id})
    return errors


def asset_group_counts(assets: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(str(asset.get("group", "")) for asset in assets)
    return dict(counts)


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
        reliability = label["review_relation_reliability"]
        geometry_support = label["review_geometry_support"]
        primary_binary = PRIMARY_BINARY_MAP.get(reliability)
        geometry_binary = GEOMETRY_SUPPORT_BINARY_MAP.get(geometry_support)
        is_primary = (
            label["packet_role"] == "primary_attachment_reliability_candidate"
            and label["predicate_label"] in {"attached to", "hanging on"}
        )
        is_connected = label["packet_role"] == "connected_diagnostic_only" and label["predicate_label"] == "connected to"
        copied_assets = manifest.get("copied_assets_hidden", [])
        group_counts = asset_group_counts(copied_assets)
        shared_origin_count = len(manifest.get("shared_origin_frames_hidden", []) or [])
        shared_rank_count = len(manifest.get("shared_crop_view_ranks_hidden", []) or [])
        image_count = len(copied_assets)
        row = {
            "schema_version": SCHEMA_VERSION,
            "label_source": LABEL_SOURCE,
            "packet_id": packet_id,
            "blind_review_id": label["blind_review_id"],
            "candidate_relation": label["candidate_relation"],
            "split": "train",
            "scan_id_hidden": manifest.get("scan_id_hidden"),
            "subgraph_id_hidden": manifest.get("subgraph_id_hidden"),
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
            "mesh_ready_hidden": bool(manifest.get("mesh_ready_hidden")),
            "sequence_ready_hidden": bool(manifest.get("sequence_ready_hidden")),
            "shared_origin_frame_count": shared_origin_count,
            "shared_origin_frame_bucket": bucket_count(shared_origin_count),
            "shared_crop_rank_count": shared_rank_count,
            "shared_crop_rank_bucket": bucket_count(shared_rank_count),
            "materialized_image_count": image_count,
            "materialized_image_bucket": bucket_count(image_count),
            "asset_group_counts": group_counts,
            "visual_context_summary": label["visual_context_summary"],
            "mesh_context_summary": label["mesh_context_summary"],
            "reviewer_id_v19": label["reviewer_id_v19"],
            "review_round_v19": label["review_round_v19"],
            "label_policy_v19": label["label_policy_v19"],
            "review_relation_reliability": reliability,
            "relation_reliability_multiclass_target": reliability,
            "relation_reliability_binary_target": primary_binary,
            "relation_reliability_binary_usable": is_primary and primary_binary is not None,
            "connected_diagnostic_target": reliability if is_connected else None,
            "connected_diagnostic_usable": is_connected,
            "review_geometry_support": geometry_support,
            "geometry_support_binary_target": geometry_binary,
            "geometry_support_binary_usable": geometry_binary is not None,
            "review_uncertainty": label["review_uncertainty"],
            "review_notes": label["review_notes"],
            "primary_reason_v19": decision.get("primary_reason_v19"),
            "packet_markdown_exists": bool(decision.get("packet_markdown_exists")),
            "local_image_count": int(decision.get("local_image_count", 0)),
            "packet_dir_hidden": manifest.get("packet_dir_hidden"),
            "packet_markdown_hidden": manifest.get("packet_markdown_hidden"),
        }
        joined.append(row)
    return joined


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
    h_label = entropy(label_counts)
    h_group = entropy(group_counts)
    denom = math.sqrt(h_label * h_group)
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


def target_record(row: dict[str, Any], target_name: str, target_value: Any) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v19_attachment_target_record_v1",
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
        "audit_ready_state_hidden": row["audit_ready_state_hidden"],
        "primary_reason_v19": row["primary_reason_v19"],
    }


def build_targets(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "multiclass": [target_record(row, MULTICLASS_TARGET, row["relation_reliability_multiclass_target"]) for row in rows],
        "primary_binary": [
            target_record(row, BINARY_TARGET, row["relation_reliability_binary_target"])
            for row in rows
            if row["relation_reliability_binary_usable"]
        ],
        "connected_diagnostic": [
            target_record(row, CONNECTED_TARGET, row["connected_diagnostic_target"])
            for row in rows
            if row["connected_diagnostic_usable"]
        ],
        "geometry_support": [
            target_record(row, GEOMETRY_SUPPORT_TARGET, row["geometry_support_binary_target"])
            for row in rows
            if row["geometry_support_binary_usable"]
        ],
        "uncertainty": [target_record(row, UNCERTAINTY_TARGET, row["review_uncertainty"]) for row in rows],
        "evidence_tier": [target_record(row, EVIDENCE_TIER_TARGET, row["evidence_tier"]) for row in rows],
        "abstain": [
            {
                **target_record(row, BINARY_TARGET, None),
                "review_relation_reliability": row["review_relation_reliability"],
                "review_geometry_support": row["review_geometry_support"],
                "review_uncertainty": row["review_uncertainty"],
                "primary_reason_v19": row["primary_reason_v19"],
            }
            for row in rows
            if not row["relation_reliability_binary_usable"]
        ],
    }


def probe_risks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        (rows, "relation_reliability_multiclass_target"),
        ([row for row in rows if row["relation_reliability_binary_usable"]], "relation_reliability_binary_target"),
        ([row for row in rows if row["geometry_support_binary_usable"]], "geometry_support_binary_target"),
        ([row for row in rows if row["connected_diagnostic_usable"]], "connected_diagnostic_target"),
        (rows, "review_uncertainty"),
    ]
    out: list[dict[str, Any]] = []
    for label_rows, label in specs:
        for predictor in RISK_PREDICTORS:
            out.append(majority_risk(label_rows, predictor, label))
    return out


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
                "accept": rel_counts.get("accept_reliable_attachment", 0),
                "reject": rel_counts.get("reject_unreliable_attachment", 0),
                "abstain": rel_counts.get("abstain_uncertain", 0),
                "diagnostic_possible": rel_counts.get("diagnostic_connected_possible", 0),
                "diagnostic_ambiguous": rel_counts.get("diagnostic_connected_ambiguous", 0),
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
        "# H002 V19 Attachment Audit Packet Label Ingestion",
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
        "Joined the locked visible-packet labels with the hidden packet manifest after label fill.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"multiclass_rows = {counts['multiclass_rows']}",
        f"primary_binary_rows = {counts['primary_binary_rows']}",
        f"connected_diagnostic_rows = {counts['connected_diagnostic_rows']}",
        f"geometry_support_rows = {counts['geometry_support_rows']}",
        f"uncertainty_rows = {counts['uncertainty_rows']}",
        f"abstain_rows = {counts['abstain_rows']}",
        f"review_relation_reliability = {counts['review_relation_reliability']}",
        f"primary_binary_target = {counts['primary_binary_target']}",
        f"geometry_support_target = {counts['geometry_support_target']}",
        f"connected_diagnostic_target = {counts['connected_diagnostic_target']}",
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
        f"same_predicate_mixed_primary_binary_groups = {viability['same_predicate_mixed_primary_binary_groups']}",
        f"same_evidence_tier_mixed_primary_binary_groups = {viability['same_evidence_tier_mixed_primary_binary_groups']}",
        "```",
        "",
        "The primary binary target is still positive-sparse, so posterior smoke remains blocked even before the full target-independence audit.",
        "",
        "## Boundary",
        "",
        "The hidden manifest is read only after label lock for target construction and shortcut audit. Hidden scan/source fields, packet paths, and image source paths are not model inputs. Multi-view and mesh remain audit/confirmation evidence only.",
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
    predicate_contrast = group_contrast(rows, "predicate_label")
    role_contrast = group_contrast(rows, "packet_role")
    tier_contrast = group_contrast(rows, "evidence_tier")
    reason_contrast = group_contrast(rows, "primary_reason_v19")

    rel_counts = Counter(row["review_relation_reliability"] for row in rows)
    geom_counts = Counter(row["review_geometry_support"] for row in rows)
    uncertainty_counts = Counter(row["review_uncertainty"] for row in rows)
    primary_binary_counts = Counter(str(row["relation_reliability_binary_target"]) for row in rows if row["relation_reliability_binary_usable"])
    geom_binary_counts = Counter(str(row["geometry_support_binary_target"]) for row in rows if row["geometry_support_binary_usable"])
    connected_counts = Counter(str(row["connected_diagnostic_target"]) for row in rows if row["connected_diagnostic_usable"])
    predicate_counts = Counter(row["predicate_label"] for row in rows)
    role_counts = Counter(row["packet_role"] for row in rows)
    tier_counts = Counter(row["evidence_tier"] for row in rows)
    audit_state_counts = Counter(str(row["audit_ready_state_hidden"]) for row in rows)
    visual_state_counts = Counter(str(row["visual_context_state_hidden"]) for row in rows)
    reason_counts = Counter(str(row["primary_reason_v19"]) for row in rows)
    image_bucket_counts = Counter(str(row["materialized_image_bucket"]) for row in rows)
    shared_origin_bucket_counts = Counter(str(row["shared_origin_frame_bucket"]) for row in rows)

    positive_rows = sum(1 for row in rows if row.get("relation_reliability_binary_target") == 1 and row["relation_reliability_binary_usable"])
    negative_rows = sum(1 for row in rows if row.get("relation_reliability_binary_target") == 0 and row["relation_reliability_binary_usable"])
    class_mass_pass = positive_rows >= MIN_CLASS_MASS_FOR_POSTERIOR and negative_rows >= MIN_CLASS_MASS_FOR_POSTERIOR

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "ingested_rows": output_dir / "ingested_rows.jsonl",
        "multiclass_target": output_dir / "multiclass_target.jsonl",
        "primary_binary_target": output_dir / "primary_binary_target.jsonl",
        "connected_diagnostic_target": output_dir / "connected_diagnostic_target.jsonl",
        "geometry_support_target": output_dir / "geometry_support_target.jsonl",
        "uncertainty_target": output_dir / "uncertainty_target.jsonl",
        "evidence_tier_target": output_dir / "evidence_tier_target.jsonl",
        "abstain_rows": output_dir / "abstain_rows.jsonl",
        "quick_probe_risks": output_dir / "quick_probe_risks.json",
        "scan_contrast_summary": output_dir / "scan_contrast_summary.csv",
        "visible_pair_contrast_summary": output_dir / "visible_pair_contrast_summary.csv",
        "predicate_contrast_summary": output_dir / "predicate_contrast_summary.csv",
        "role_contrast_summary": output_dir / "role_contrast_summary.csv",
        "tier_contrast_summary": output_dir / "tier_contrast_summary.csv",
        "reason_contrast_summary": output_dir / "reason_contrast_summary.csv",
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

    same_scan_mixed = sum(1 for row in scan_contrast if row["mixed_primary_binary"])
    same_pair_mixed = sum(1 for row in visible_pair_contrast if row["mixed_primary_binary"])
    same_predicate_mixed = sum(1 for row in predicate_contrast if row["mixed_primary_binary"])
    same_role_mixed = sum(1 for row in role_contrast if row["mixed_primary_binary"])
    same_tier_mixed = sum(1 for row in tier_contrast if row["mixed_primary_binary"])

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
            "connected_diagnostic_rows": len(targets["connected_diagnostic"]),
            "geometry_support_rows": len(targets["geometry_support"]),
            "uncertainty_rows": len(targets["uncertainty"]),
            "evidence_tier_rows": len(targets["evidence_tier"]),
            "abstain_rows": len(targets["abstain"]),
            "review_relation_reliability": dict(sorted(rel_counts.items())),
            "review_geometry_support": dict(sorted(geom_counts.items())),
            "review_uncertainty": dict(sorted(uncertainty_counts.items())),
            "primary_binary_target": dict(sorted(primary_binary_counts.items())),
            "geometry_support_target": dict(sorted(geom_binary_counts.items())),
            "connected_diagnostic_target": dict(sorted(connected_counts.items())),
            "predicate_label": dict(sorted(predicate_counts.items())),
            "packet_role": dict(sorted(role_counts.items())),
            "evidence_tier": dict(sorted(tier_counts.items())),
            "audit_ready_state_hidden": dict(sorted(audit_state_counts.items())),
            "visual_context_state_hidden": dict(sorted(visual_state_counts.items())),
            "primary_reason_v19": dict(sorted(reason_counts.items())),
            "materialized_image_bucket": dict(sorted(image_bucket_counts.items())),
            "shared_origin_frame_bucket": dict(sorted(shared_origin_bucket_counts.items())),
            "scan_groups": len(scan_contrast),
            "visible_pair_groups": len(visible_pair_contrast),
            "predicate_groups": len(predicate_contrast),
            "role_groups": len(role_contrast),
            "tier_groups": len(tier_contrast),
            "reason_groups": len(reason_contrast),
            "quick_probe_risk_flags": len(risk_flags),
        },
        "target_viability": {
            "minimum_per_class_for_posterior": MIN_CLASS_MASS_FOR_POSTERIOR,
            "reliability_positive_rows": positive_rows,
            "reliability_negative_rows": negative_rows,
            "class_mass_pass": class_mass_pass,
            "same_scan_mixed_primary_binary_groups": same_scan_mixed,
            "same_visible_pair_mixed_primary_binary_groups": same_pair_mixed,
            "same_predicate_mixed_primary_binary_groups": same_predicate_mixed,
            "same_role_mixed_primary_binary_groups": same_role_mixed,
            "same_evidence_tier_mixed_primary_binary_groups": same_tier_mixed,
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
            "connected_primary_binary_target": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_jsonl(output_paths["ingested_rows"], rows)
    write_jsonl(output_paths["multiclass_target"], targets["multiclass"])
    write_jsonl(output_paths["primary_binary_target"], targets["primary_binary"])
    write_jsonl(output_paths["connected_diagnostic_target"], targets["connected_diagnostic"])
    write_jsonl(output_paths["geometry_support_target"], targets["geometry_support"])
    write_jsonl(output_paths["uncertainty_target"], targets["uncertainty"])
    write_jsonl(output_paths["evidence_tier_target"], targets["evidence_tier"])
    write_jsonl(output_paths["abstain_rows"], targets["abstain"])
    write_json(output_paths["quick_probe_risks"], risks)
    write_csv(output_paths["scan_contrast_summary"], scan_contrast)
    write_csv(output_paths["visible_pair_contrast_summary"], visible_pair_contrast)
    write_csv(output_paths["predicate_contrast_summary"], predicate_contrast)
    write_csv(output_paths["role_contrast_summary"], role_contrast)
    write_csv(output_paths["tier_contrast_summary"], tier_contrast)
    write_csv(output_paths["reason_contrast_summary"], reason_contrast)
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
    print(f"connected_diagnostic_rows={counts['connected_diagnostic_rows']}")
    print(f"geometry_support_rows={counts['geometry_support_rows']}")
    print(f"uncertainty_rows={counts['uncertainty_rows']}")
    print(f"abstain_rows={counts['abstain_rows']}")
    print(f"positive_rows={viability['reliability_positive_rows']}")
    print(f"negative_rows={viability['reliability_negative_rows']}")
    print(f"class_mass_pass={viability['class_mass_pass']}")
    print(f"quick_probe_risk_flags={counts['quick_probe_risk_flags']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
