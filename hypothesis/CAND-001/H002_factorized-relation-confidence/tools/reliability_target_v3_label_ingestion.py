#!/usr/bin/env python3
"""Ingest H002 reliability target v3 labels after proxy fill."""

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
PLAN_DIR = RGA_ROOT / "reliability_target_v3_positive_anchor_plan"
FILL_DIR = RGA_ROOT / "reliability_target_v3_label_fill_codex_proxy_user_requested"

DEFAULT_COMPLETED_SHEET = FILL_DIR / "completed_v3_positive_anchor_label_sheet_codex_proxy_user_requested.tsv"
DEFAULT_FILL_SUMMARY = FILL_DIR / "summary.json"
DEFAULT_SCHEMA = PLAN_DIR / "v3_label_schema.json"
DEFAULT_MANIFEST = PLAN_DIR / "v3_positive_anchor_manifest_post_label_only.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_label_ingestion_codex_proxy_user_requested"

LABEL_SOURCE = "codex_proxy_reliability_target_v3_user_requested"
RELIABILITY_TARGET = "relation_reliability_v3_binary_target"
GEOMETRY_TARGET = "geometry_support_v3_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v3_binary_target"
RELIABILITY_MULTICLASS = "relation_reliability_v3_multiclass_target"

COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_identity_v3",
    "pair_evaluability_v3",
    "geometry_support_v3",
    "relation_usefulness_v3",
    "relation_reliability_v3",
    "primary_reason_v3",
    "uncertainty_reason_v3",
]

VISIBLE_GROUP_KEYS = [
    "predicate_family",
    "predicate_label",
    "subject_label",
    "object_label",
    "evidence_packet_status",
]

HIDDEN_GROUP_KEYS = [
    "sampling_category_hidden",
    "expected_v3_role_hidden",
    "queue_kind_hidden",
    "geometry_status_hidden",
    "label_match_status_hidden",
    "rank_band_hidden",
    "endpoint_flag_pattern_hidden",
]

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "normalized_mutual_information": 0.20,
    "positive_rate_range": 0.70,
    "large_group_rows": 20,
    "large_group_purity": 0.90,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-sheet", type=Path, default=DEFAULT_COMPLETED_SHEET)
    parser.add_argument("--fill-summary", type=Path, default=DEFAULT_FILL_SUMMARY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
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
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_headers(fieldnames: list[str], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = [
        "blind_review_id",
        "scan_id",
        "scene_context_id",
        "subject_id",
        "subject_label",
        "predicate_label",
        "predicate_family",
        "object_id",
        "object_label",
        *schema["required_completion_fields"],
    ]
    for field in required:
        if field not in fieldnames:
            errors.append({"error_type": "missing_required_header", "field": field})
    return errors


def validate_id_sets(completed_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    completed_ids = [str(row.get("blind_review_id") or "") for row in completed_rows]
    manifest_ids = [str(row.get("blind_review_id") or "") for row in manifest_rows]
    for blind_id, count in Counter(completed_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_completed_blind_review_id", "blind_review_id": blind_id, "count": count})
    for blind_id, count in Counter(manifest_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_manifest_blind_review_id", "blind_review_id": blind_id, "count": count})
    completed_set = {blind_id for blind_id in completed_ids if blind_id}
    manifest_set = {blind_id for blind_id in manifest_ids if blind_id}
    for blind_id in sorted(completed_set - manifest_set):
        errors.append({"error_type": "completed_id_missing_from_manifest", "blind_review_id": blind_id})
    for blind_id in sorted(manifest_set - completed_set):
        errors.append({"error_type": "manifest_id_missing_from_completed_sheet", "blind_review_id": blind_id})
    return errors


def validate_fill_summary(fill_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    boundary = fill_summary.get("boundary", {})
    expected_false = [
        "actual_user_reviewer",
        "paper_evidence_allowed",
        "used_hidden_manifest_for_label_decision",
        "used_sampling_category_for_label_decision",
        "used_expected_role_for_label_decision",
        "used_source_score_or_rank",
        "used_p_geom_valid",
        "used_geometry_status",
        "used_label_match_status",
        "used_numeric_witness_values",
        "validation_usage",
        "test_usage",
        "multi_view_as_model_input",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_summary_boundary_mismatch", "field": key, "expected": False, "value": boundary.get(key)})
    if boundary.get("filled_by") != "codex_proxy":
        errors.append({"error_type": "fill_summary_boundary_mismatch", "field": "filled_by", "expected": "codex_proxy", "value": boundary.get("filled_by")})
    if boundary.get("split") != "train_only":
        errors.append({"error_type": "fill_summary_boundary_mismatch", "field": "split", "expected": "train_only", "value": boundary.get("split")})
    if fill_summary.get("status") != "h002_reliability_target_v3_label_filled_codex_proxy_user_requested":
        errors.append({"error_type": "fill_summary_status_unexpected", "value": fill_summary.get("status")})
    return errors


def validate_row(row: dict[str, str], row_number: int, schema: dict[str, Any], manifest: dict[str, Any] | None) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = {key: set(value) for key, value in schema["allowed_values"].items()}
    blind_id = str(row.get("blind_review_id") or "")
    for field in COMPLETION_FIELDS:
        value = str(row.get(field) or "")
        if not value:
            errors.append({"error_type": "missing_completion_field", "row_number": row_number, "blind_review_id": blind_id, "field": field})
        elif field in allowed and value not in allowed[field]:
            errors.append({"error_type": "invalid_completion_value", "row_number": row_number, "blind_review_id": blind_id, "field": field, "value": value})
    if manifest is not None:
        identity_pairs = {
            "scan_id": "scan_id",
            "scene_context_id": "subgraph_id",
            "predicate_family": "predicate_family",
            "predicate_label": "predicate_label",
            "subject_id": "subject_id",
            "subject_label": "subject_label",
            "object_id": "object_id",
            "object_label": "object_label",
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
    return errors


def hidden_metadata(manifest: dict[str, Any]) -> dict[str, Any]:
    hidden = dict(manifest.get("hidden_sampling_axes_post_label_only", {}))
    return {
        "sampling_category_hidden": manifest.get("sampling_category_hidden"),
        "expected_v3_role_hidden": manifest.get("expected_v3_role_hidden"),
        "prediction_id_hidden": manifest.get("prediction_id_hidden"),
        "queue_kind_hidden": hidden.get("queue_kind_hidden"),
        "geometry_status_hidden": hidden.get("geometry_status_hidden"),
        "label_match_status_hidden": hidden.get("label_match_status_hidden"),
        "rank_band_hidden": hidden.get("rank_band_hidden"),
        "endpoint_flag_pattern_hidden": hidden.get("endpoint_flag_pattern_hidden"),
        "endpoint_pair_note_hidden": hidden.get("endpoint_pair_note_hidden"),
        "semantic_rank_hidden": hidden.get("semantic_rank_hidden"),
        "semantic_score_raw_hidden": hidden.get("semantic_score_raw_hidden"),
        "semantic_score_norm_hidden": hidden.get("semantic_score_norm_hidden"),
        "p_geom_valid_hidden": hidden.get("p_geom_valid_hidden"),
        "reason_codes_hidden": hidden.get("reason_codes_hidden"),
        "matched_predicates_hidden": hidden.get("matched_predicates_hidden"),
        "forbidden_as_labeler_visible": manifest.get("forbidden_as_labeler_visible", []),
    }


def deployable_evidence_after_label_lock(row: dict[str, str], manifest: dict[str, Any]) -> dict[str, Any]:
    hidden = manifest.get("hidden_sampling_axes_post_label_only", {})
    return {
        "semantic_evidence": {
            "semantic_rank": hidden.get("semantic_rank_hidden"),
            "semantic_score_raw": hidden.get("semantic_score_raw_hidden"),
            "semantic_score_norm": hidden.get("semantic_score_norm_hidden"),
            "available_after_label_lock": True,
        },
        "geometry_scalar_evidence": {
            "p_geom_valid": hidden.get("p_geom_valid_hidden"),
            "role": "legacy_geometry_only_baseline_scalar",
            "available_after_label_lock": True,
        },
        "coverage_evidence": {
            "evidence_packet_status": row.get("evidence_packet_status"),
        },
        "forbidden_as_posterior_input": {
            "v3_review_fields": True,
            "sampling_category_hidden": True,
            "expected_v3_role_hidden": True,
            "queue_kind_hidden": True,
            "geometry_status_hidden": True,
            "label_match_status_hidden": True,
            "rank_band_hidden": True,
            "endpoint_flag_pattern_hidden": True,
            "audit_packet_paths": True,
            "multi_view_as_model_input": True,
        },
    }


def review_fields(row: dict[str, str]) -> dict[str, Any]:
    return {
        "reviewer_id": row.get("reviewer_id"),
        "review_round": row.get("review_round"),
        "endpoint_identity_v3": row.get("endpoint_identity_v3"),
        "pair_evaluability_v3": row.get("pair_evaluability_v3"),
        "geometry_support_v3": row.get("geometry_support_v3"),
        "relation_usefulness_v3": row.get("relation_usefulness_v3"),
        "relation_reliability_v3": row.get("relation_reliability_v3"),
        "primary_reason_v3": row.get("primary_reason_v3"),
        "uncertainty_reason_v3": row.get("uncertainty_reason_v3"),
        "label_notes_v3": row.get("label_notes_v3"),
        "not_model_input": True,
    }


def base_identity(row: dict[str, str], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": row["blind_review_id"],
        "prediction_id": manifest.get("prediction_id_hidden"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("scene_context_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "evidence_packet_status": row.get("evidence_packet_status"),
    }


def derive_reliability_binary(row: dict[str, str]) -> dict[str, Any]:
    value = row["relation_reliability_v3"]
    if value == "reliable":
        return {"target_name": RELIABILITY_TARGET, "target_y": 1, "target_use": "positive", "reason": "v3_relation_reliability_reliable"}
    if value.startswith("unreliable_"):
        return {"target_name": RELIABILITY_TARGET, "target_y": 0, "target_use": "negative", "reason": f"v3_relation_reliability={value}"}
    return {"target_name": RELIABILITY_TARGET, "target_y": None, "target_use": "exclude", "reason": f"exclude_relation_reliability={value}"}


def derive_geometry_binary(row: dict[str, str]) -> dict[str, Any]:
    value = row["geometry_support_v3"]
    if value == "supports_predicate":
        return {"target_name": GEOMETRY_TARGET, "target_y": 1, "target_use": "positive", "reason": "v3_geometry_supports_predicate"}
    if value == "contradicts_predicate":
        return {"target_name": GEOMETRY_TARGET, "target_y": 0, "target_use": "negative", "reason": "v3_geometry_contradicts_predicate"}
    return {"target_name": GEOMETRY_TARGET, "target_y": None, "target_use": "exclude", "reason": f"exclude_geometry_support={value}"}


def derive_usefulness_binary(row: dict[str, str]) -> dict[str, Any]:
    value = row["relation_usefulness_v3"]
    if value == "informative":
        return {"target_name": USEFULNESS_TARGET, "target_y": 1, "target_use": "positive", "reason": "v3_relation_usefulness_informative"}
    if value in {"trivial_dense_or_room_structure", "ontology_mismatch"}:
        return {"target_name": USEFULNESS_TARGET, "target_y": 0, "target_use": "negative", "reason": f"v3_relation_usefulness={value}"}
    return {"target_name": USEFULNESS_TARGET, "target_y": None, "target_use": "exclude", "reason": f"exclude_relation_usefulness={value}"}


def relation_multiclass(row: dict[str, str]) -> dict[str, Any]:
    return {
        "target_name": RELIABILITY_MULTICLASS,
        "target_y": row["relation_reliability_v3"],
        "target_use": "multiclass",
        "reason": f"v3_relation_reliability={row['relation_reliability_v3']}",
    }


def make_label(row: dict[str, str], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v3_ingested_label_v1",
        **base_identity(row, manifest),
        "label_source": LABEL_SOURCE,
        "filled_by": "codex_proxy",
        "actual_user_reviewer": False,
        "user_requested_proxy_fill": True,
        "paper_evidence_allowed": False,
        "posterior_claim_allowed": False,
        "hidden_manifest_joined_after_label_lock": True,
        "review_fields_are_target_only": True,
        "v3_review_fields": review_fields(row),
        "relation_reliability_v3_binary_target": derive_reliability_binary(row),
        "geometry_support_v3_binary_target": derive_geometry_binary(row),
        "relation_usefulness_v3_binary_target": derive_usefulness_binary(row),
        "relation_reliability_v3_multiclass_target": relation_multiclass(row),
        "deployable_evidence_after_label_lock": deployable_evidence_after_label_lock(row, manifest),
        "hidden_audit_metadata_post_label_only": hidden_metadata(manifest),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "actual_user_reviewer": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "review_fields_as_model_input": False,
            "hidden_sampling_axes_as_model_input": False,
            "multi_view_as_model_input": False,
        },
    }


def ingest(completed_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]], schema: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifest_by_id = {str(row["blind_review_id"]): row for row in manifest_rows}
    labels: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(completed_rows, start=2):
        blind_id = str(row.get("blind_review_id") or "")
        manifest = manifest_by_id.get(blind_id)
        row_errors = validate_row(row, row_number, schema, manifest)
        if manifest is None:
            row_errors.append({"error_type": "missing_manifest_for_completed_row", "row_number": row_number, "blind_review_id": blind_id})
        if row_errors:
            errors.extend(row_errors)
            continue
        labels.append(make_label(row, manifest_by_id[blind_id]))
    return labels, errors


def target_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is None:
        return None
    hidden = label["hidden_audit_metadata_post_label_only"]
    return {
        "schema_version": schema_version,
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
        "evidence_packet_status": label["evidence_packet_status"],
        "filled_by": "codex_proxy",
        "actual_user_reviewer": False,
        "paper_locked": False,
        "sampling_category_hidden": hidden.get("sampling_category_hidden"),
        "expected_v3_role_hidden": hidden.get("expected_v3_role_hidden"),
        "queue_kind_hidden": hidden.get("queue_kind_hidden"),
        "geometry_status_hidden": hidden.get("geometry_status_hidden"),
        "label_match_status_hidden": hidden.get("label_match_status_hidden"),
        "rank_band_hidden": hidden.get("rank_band_hidden"),
        "endpoint_flag_pattern_hidden": hidden.get("endpoint_flag_pattern_hidden"),
    }


def multiclass_target_row(label: dict[str, Any]) -> dict[str, Any]:
    row = target_row(label, "relation_reliability_v3_multiclass_target", "h002_reliability_target_v3_multiclass_row_v1")
    assert row is not None
    return row


def posterior_candidate_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    row = target_row(label, target_key, schema_version)
    if row is None:
        return None
    return {
        **row,
        "deployable_evidence_after_label_lock": label["deployable_evidence_after_label_lock"],
        "audit_only_v3_review_fields": label["v3_review_fields"],
        "hidden_audit_metadata_post_label_only": label["hidden_audit_metadata_post_label_only"],
        "audit_note": (
            "Posterior smoke remains blocked until target-independence audit. "
            "Do not use v3 review fields, hidden bucket fields, geometry_status, "
            "label_match_status, or audit packet paths as model input."
        ),
    }


def excluded_target_row(label: dict[str, Any], target_key: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is not None:
        return None
    return {
        "schema_version": "h002_reliability_target_v3_excluded_target_v1",
        "target_name": target["target_name"],
        "target_y": None,
        "target_use": target["target_use"],
        "target_reason": target["reason"],
        "blind_review_id": label["blind_review_id"],
        "scan_id": label["scan_id"],
        "predicate_label": label["predicate_label"],
        "predicate_family": label["predicate_family"],
        "subject_label": label["subject_label"],
        "object_label": label["object_label"],
        "v3_review_fields": label["v3_review_fields"],
    }


def entropy_from_counts(counts: Counter[Any]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    value = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        p = count / total
        value -= p * math.log2(p)
    return value


def group_value(row: dict[str, Any], key: str) -> str:
    if key in row:
        return str(row.get(key))
    hidden = row.get("hidden_audit_metadata_post_label_only", {})
    if key in hidden:
        return str(hidden.get(key))
    return "missing"


def group_probe(rows: list[dict[str, Any]], key: str, source: str, target_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[group_value(row, key)].append(row)

    overall_counts = Counter(int(row["target_y"]) for row in rows)
    overall_entropy = entropy_from_counts(overall_counts)
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    positive_rates: list[float] = []
    large_group_high_purity = False
    table: list[dict[str, Any]] = []
    for value, group_rows in sorted(groups.items()):
        counts = Counter(int(row["target_y"]) for row in group_rows)
        pos = counts[1]
        neg = counts[0]
        total = pos + neg
        majority = max(pos, neg)
        purity = majority / total if total else 0.0
        pos_rate = pos / total if total else 0.0
        group_entropy = entropy_from_counts(counts)
        weighted_conditional_entropy += (total / len(rows) * group_entropy) if rows else 0.0
        majority_correct += majority
        positive_rates.append(pos_rate)
        if total >= RISK_THRESHOLDS["large_group_rows"] and purity >= RISK_THRESHOLDS["large_group_purity"]:
            large_group_high_purity = True
        table.append(
            {
                "target_name": target_name,
                "source": source,
                "group_key": key,
                "group_value": value,
                "rows": total,
                "positive": pos,
                "negative": neg,
                "positive_rate": pos_rate,
                "majority_label": 1 if pos >= neg else 0,
                "majority_accuracy": purity,
                "entropy_bits": group_entropy,
            }
        )
    mutual_info = max(0.0, overall_entropy - weighted_conditional_entropy)
    nmi = mutual_info / overall_entropy if overall_entropy > 0 else 0.0
    pos_rate_range = (max(positive_rates) - min(positive_rates)) if positive_rates else 0.0
    majority_rule_accuracy = majority_correct / len(rows) if rows else 0.0
    risk_flag = (
        majority_rule_accuracy >= RISK_THRESHOLDS["majority_rule_accuracy"]
        or nmi >= RISK_THRESHOLDS["normalized_mutual_information"]
        or pos_rate_range >= RISK_THRESHOLDS["positive_rate_range"]
        or large_group_high_purity
    )
    summary = {
        "target_name": target_name,
        "source": source,
        "group_key": key,
        "groups": len(groups),
        "rows": len(rows),
        "overall_positive": overall_counts[1],
        "overall_negative": overall_counts[0],
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": weighted_conditional_entropy,
        "mutual_information_bits": mutual_info,
        "normalized_mutual_information": nmi,
        "majority_rule_accuracy": majority_rule_accuracy,
        "positive_rate_range": pos_rate_range,
        "large_group_high_purity": large_group_high_purity,
        "risk_flag": risk_flag,
    }
    return table, summary


def target_independence_probe(target_rows: list[dict[str, Any]], target_name: str) -> dict[str, Any]:
    group_table: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    if not target_rows:
        return {
            "schema_version": "h002_reliability_target_v3_independence_probe_v1",
            "target_name": target_name,
            "status": "target_independence_probe_no_binary_rows",
            "summaries": [],
            "group_table": [],
            "hidden_risks": [],
            "visible_non_target_shortcuts": [],
        }
    for key in VISIBLE_GROUP_KEYS:
        table, summary = group_probe(target_rows, key, "visible_non_target_surface", target_name)
        group_table.extend(table)
        summaries.append(summary)
    for key in HIDDEN_GROUP_KEYS:
        table, summary = group_probe(target_rows, key, "hidden_post_label_audit", target_name)
        group_table.extend(table)
        summaries.append(summary)

    hidden_risks = [item for item in summaries if item["source"] == "hidden_post_label_audit" and item["risk_flag"]]
    visible_risks = [item for item in summaries if item["source"] == "visible_non_target_surface" and item["risk_flag"]]
    if hidden_risks:
        status = "target_independence_risk_hidden_metadata_correlated"
    elif visible_risks:
        status = "target_independence_risk_visible_non_target_shortcut"
    else:
        status = "target_independence_probe_pass"
    return {
        "schema_version": "h002_reliability_target_v3_independence_probe_v1",
        "target_name": target_name,
        "status": status,
        "risk_thresholds": RISK_THRESHOLDS,
        "summaries": summaries,
        "group_table": group_table,
        "hidden_risks": sorted(hidden_risks, key=lambda row: (-row["normalized_mutual_information"], -row["majority_rule_accuracy"])),
        "visible_non_target_shortcuts": sorted(visible_risks, key=lambda row: (-row["normalized_mutual_information"], -row["majority_rule_accuracy"])),
    }


def count_binary_target(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["target_y"] for row in rows)
    total = len(rows)
    return {
        "rows": total,
        "positive": counts[1],
        "negative": counts[0],
        "positive_rate": counts[1] / total if total else 0.0,
        "by_family": nested_counts(rows, "predicate_family"),
        "by_predicate": nested_counts(rows, "predicate_label"),
    }


def count_multiclass(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["target_y"] for row in rows)
    return {"rows": len(rows), "classes": dict(sorted(counts.items()))}


def nested_counts(rows: list[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[str(row.get(key))][str(row.get("target_y"))] += 1
    return {group: dict(sorted(counter.items())) for group, counter in sorted(grouped.items())}


def axis_counts(labels: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for axis in [
        "endpoint_identity_v3",
        "pair_evaluability_v3",
        "geometry_support_v3",
        "relation_usefulness_v3",
        "relation_reliability_v3",
        "primary_reason_v3",
        "uncertainty_reason_v3",
    ]:
        output[axis] = dict(sorted(Counter(label["v3_review_fields"].get(axis) for label in labels).items()))
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    targets = summary["counts"]["binary_targets"]
    probes = summary["target_independence_probes"]
    lines = [
        "# H002 Reliability Target V3 Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage ingestion.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Labels are user-requested Codex proxy labels, not independent human annotation.",
        "- V3 review fields are target/audit fields and must not be posterior input.",
        "- Hidden manifest is joined only after label lock.",
        "- Multi-view/mesh packet evidence remains audit evidence only, not model input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Binary Target Counts",
        "",
        "| Target | Rows | Positive | Negative | Positive Rate | Excluded |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for target_name in [RELIABILITY_TARGET, GEOMETRY_TARGET, USEFULNESS_TARGET]:
        item = targets[target_name]
        excluded = summary["counts"]["excluded_targets"][target_name]
        lines.append(
            f"| `{target_name}` | {item['rows']} | {item['positive']} | {item['negative']} | "
            f"{item['positive_rate']:.4f} | {excluded} |"
        )
    lines.extend(["", "## Probe", "", "| Target | Probe Status | Hidden Risks | Visible Risks |", "| --- | --- | ---: | ---: |"])
    for target_name in [RELIABILITY_TARGET, GEOMETRY_TARGET, USEFULNESS_TARGET]:
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


def run(args: argparse.Namespace) -> dict[str, Any]:
    completed_sheet = as_abs(args.completed_sheet)
    fill_summary_path = as_abs(args.fill_summary)
    schema_path = as_abs(args.schema)
    manifest_path = as_abs(args.manifest)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    fieldnames, completed_rows = read_tsv(completed_sheet)
    fill_summary = read_json(fill_summary_path)
    schema = read_json(schema_path)
    manifest_rows = read_jsonl(manifest_path)

    errors: list[dict[str, Any]] = []
    errors.extend(validate_headers(fieldnames, schema))
    errors.extend(validate_id_sets(completed_rows, manifest_rows))
    errors.extend(validate_fill_summary(fill_summary))
    labels, label_errors = ingest(completed_rows, manifest_rows, schema)
    errors.extend(label_errors)

    reliability_targets = [row for row in (target_row(label, "relation_reliability_v3_binary_target", "h002_reliability_target_v3_binary_row_v1") for label in labels) if row is not None]
    geometry_targets = [row for row in (target_row(label, "geometry_support_v3_binary_target", "h002_geometry_support_v3_binary_row_v1") for label in labels) if row is not None]
    usefulness_targets = [row for row in (target_row(label, "relation_usefulness_v3_binary_target", "h002_relation_usefulness_v3_binary_row_v1") for label in labels) if row is not None]
    multiclass_targets = [multiclass_target_row(label) for label in labels]

    reliability_posterior = [row for row in (posterior_candidate_row(label, "relation_reliability_v3_binary_target", "h002_reliability_target_v3_posterior_candidate_row_v1") for label in labels) if row is not None]
    geometry_posterior = [row for row in (posterior_candidate_row(label, "geometry_support_v3_binary_target", "h002_geometry_support_v3_posterior_candidate_row_v1") for label in labels) if row is not None]
    usefulness_posterior = [row for row in (posterior_candidate_row(label, "relation_usefulness_v3_binary_target", "h002_relation_usefulness_v3_posterior_candidate_row_v1") for label in labels) if row is not None]

    excluded_targets = [
        row
        for label in labels
        for row in (
            excluded_target_row(label, "relation_reliability_v3_binary_target"),
            excluded_target_row(label, "geometry_support_v3_binary_target"),
            excluded_target_row(label, "relation_usefulness_v3_binary_target"),
        )
        if row is not None
    ]
    excluded_counts = Counter(row["target_name"] for row in excluded_targets)
    probes = {
        RELIABILITY_TARGET: target_independence_probe(reliability_posterior, RELIABILITY_TARGET),
        GEOMETRY_TARGET: target_independence_probe(geometry_posterior, GEOMETRY_TARGET),
        USEFULNESS_TARGET: target_independence_probe(usefulness_posterior, USEFULNESS_TARGET),
    }
    probe_summaries = [row for probe in probes.values() for row in probe["summaries"]]
    probe_group_rows = [row for probe in probes.values() for row in probe["group_table"]]

    any_probe_risk = any(probe["status"] != "target_independence_probe_pass" for probe in probes.values())
    reliability_count = count_binary_target(reliability_targets)
    enough_reliability_mass = reliability_count["positive"] >= 20 and reliability_count["negative"] >= 20

    if errors:
        status = "h002_reliability_target_v3_label_ingestion_errors"
        decision = "Fix v3 label ingestion errors before target audit."
        next_todo = "fix_reliability_target_v3_label_ingestion_errors"
    elif any_probe_risk:
        status = "h002_reliability_target_v3_label_ingested_with_probe_risk"
        decision = (
            "V3 labels are ingested and reliability binary mass is usable, but hidden/visible "
            "shortcut probes still flag target-construction risk. Run a dedicated target-independence "
            "audit before any posterior smoke."
        )
        next_todo = "reliability_target_v3_target_independence_audit"
    elif not enough_reliability_mass:
        status = "h002_reliability_target_v3_label_ingested_positive_sparse"
        decision = "V3 labels are ingested, but reliability binary mass is still too sparse for posterior smoke."
        next_todo = "reliability_target_v3_target_independence_audit"
    else:
        status = "h002_reliability_target_v3_label_ingested_ready_for_target_independence_audit"
        decision = "V3 labels are ingested. Run dedicated target-independence audit before posterior smoke."
        next_todo = "reliability_target_v3_target_independence_audit"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validated_v3_labels": output_dir / "validated_v3_labels.jsonl",
        "relation_reliability_binary_targets": output_dir / "relation_reliability_v3_binary_targets.jsonl",
        "geometry_support_binary_targets": output_dir / "geometry_support_v3_binary_targets.jsonl",
        "relation_usefulness_binary_targets": output_dir / "relation_usefulness_v3_binary_targets.jsonl",
        "relation_reliability_multiclass_targets": output_dir / "relation_reliability_v3_multiclass_targets.jsonl",
        "relation_reliability_posterior_candidates": output_dir / "relation_reliability_v3_posterior_candidates.jsonl",
        "geometry_support_posterior_candidates": output_dir / "geometry_support_v3_posterior_candidates.jsonl",
        "relation_usefulness_posterior_candidates": output_dir / "relation_usefulness_v3_posterior_candidates.jsonl",
        "excluded_targets": output_dir / "excluded_v3_targets.jsonl",
        "target_independence_probe": output_dir / "target_independence_probe.json",
        "target_independence_probe_summaries": output_dir / "target_independence_probe_summaries.csv",
        "target_independence_group_table": output_dir / "target_independence_group_table.csv",
        "ingestion_errors": output_dir / "ingestion_errors.jsonl",
    }

    summary = {
        "schema_version": "h002_reliability_target_v3_label_ingestion_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "input_paths": {
            "completed_sheet": rel_path(completed_sheet),
            "fill_summary": rel_path(fill_summary_path),
            "v3_label_schema": rel_path(schema_path),
            "post_label_manifest": rel_path(manifest_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "filled_by": "codex_proxy",
            "actual_user_reviewer": False,
            "paper_evidence_allowed": False,
            "hidden_manifest_joined_after_label_lock": True,
            "review_fields_as_model_input": False,
            "hidden_sampling_axes_as_model_input": False,
            "multi_view_as_model_input": False,
            "posterior_smoke_allowed": False,
        },
        "counts": {
            "rows": len(labels),
            "ingestion_errors": len(errors),
            "axis_counts": axis_counts(labels),
            "binary_targets": {
                RELIABILITY_TARGET: count_binary_target(reliability_targets),
                GEOMETRY_TARGET: count_binary_target(geometry_targets),
                USEFULNESS_TARGET: count_binary_target(usefulness_targets),
            },
            "multiclass_targets": {
                RELIABILITY_MULTICLASS: count_multiclass(multiclass_targets),
            },
            "excluded_targets": {
                RELIABILITY_TARGET: excluded_counts[RELIABILITY_TARGET],
                GEOMETRY_TARGET: excluded_counts[GEOMETRY_TARGET],
                USEFULNESS_TARGET: excluded_counts[USEFULNESS_TARGET],
            },
        },
        "target_independence_probes": {
            key: {
                "status": value["status"],
                "hidden_risks": value["hidden_risks"],
                "visible_non_target_shortcuts": value["visible_non_target_shortcuts"],
            }
            for key, value in probes.items()
        },
        "next_todo": next_todo,
    }

    write_jsonl(output_paths["validated_v3_labels"], labels)
    write_jsonl(output_paths["relation_reliability_binary_targets"], reliability_targets)
    write_jsonl(output_paths["geometry_support_binary_targets"], geometry_targets)
    write_jsonl(output_paths["relation_usefulness_binary_targets"], usefulness_targets)
    write_jsonl(output_paths["relation_reliability_multiclass_targets"], multiclass_targets)
    write_jsonl(output_paths["relation_reliability_posterior_candidates"], reliability_posterior)
    write_jsonl(output_paths["geometry_support_posterior_candidates"], geometry_posterior)
    write_jsonl(output_paths["relation_usefulness_posterior_candidates"], usefulness_posterior)
    write_jsonl(output_paths["excluded_targets"], excluded_targets)
    write_jsonl(output_paths["ingestion_errors"], errors)
    write_json(
        output_paths["target_independence_probe"],
        {
            "schema_version": "h002_reliability_target_v3_target_independence_probe_bundle_v1",
            "probes": probes,
        },
    )
    write_csv(output_paths["target_independence_probe_summaries"], probe_summaries)
    write_csv(output_paths["target_independence_group_table"], probe_group_rows)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    targets = summary["counts"]["binary_targets"]
    reliability = targets[RELIABILITY_TARGET]
    print(
        f"status={summary['status']} rows={summary['counts']['rows']} "
        f"rel_binary={reliability['rows']} rel_pos={reliability['positive']} rel_neg={reliability['negative']} "
        f"errors={summary['counts']['ingestion_errors']} "
        f"probe={summary['target_independence_probes'][RELIABILITY_TARGET]['status']} "
        f"validation_used={summary['boundary']['validation_usage']} test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
