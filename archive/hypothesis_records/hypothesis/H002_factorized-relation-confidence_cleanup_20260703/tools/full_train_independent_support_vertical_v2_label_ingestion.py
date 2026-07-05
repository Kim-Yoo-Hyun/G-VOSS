#!/usr/bin/env python3
"""Ingest support/vertical v2 factual-axis labels after label lock."""

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

DEFAULT_FILL_DIR = RGA_ROOT / "independent_support_vertical_v2_label_fill_codex_ver"
DEFAULT_READINESS_DIR = RGA_ROOT / "independent_support_vertical_v2_label_readiness_codex_ver"
DEFAULT_PACKET_DIR = RGA_ROOT / "independent_support_vertical_audit_packet_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_label_ingestion_codex_ver"

DEFAULT_COMPLETED_SHEET = DEFAULT_FILL_DIR / "completed_support_vertical_v2_label_fill_sheet_codex_ver.tsv"
DEFAULT_FILL_SUMMARY = DEFAULT_FILL_DIR / "summary.json"
DEFAULT_SCHEMA = DEFAULT_READINESS_DIR / "v2_completion_schema.json"
DEFAULT_INTERNAL_REFERENCE = DEFAULT_PACKET_DIR / "internal_reference_post_label_only.jsonl"
DEFAULT_PROXIMITY_RISK_SLICE = DEFAULT_PACKET_DIR / "proximity_risk_slice_post_label_only.jsonl"

LABEL_SOURCE = "codex_ver_support_vertical_v2_factual_axes_bootstrap"
SELECTED_FAMILIES = {"support_contact", "relative_vertical"}
EXCLUDED_RISK_FAMILY = "proximity"

VISIBLE_WITNESS_KEYS = [
    "witness_distance_xy_m",
    "witness_distance_3d_m",
    "witness_center_delta_z_m",
    "witness_vertical_gap_subject_on_object_m",
    "witness_projected_iou_xy",
    "witness_subject_overlap_xy",
    "witness_object_overlap_xy",
    "witness_normalized_distance_xy",
    "witness_support_contact_gap_abs",
    "witness_support_contact_xy_overlap",
    "witness_relative_vertical_signed_margin",
    "witness_relative_vertical_sign_agreement",
]

V2_TARGET_AXIS_KEYS = [
    "endpoint_validity_v2",
    "pair_visibility_v2",
    "relation_geometry_answer_v2",
    "geometry_evidence_strength_v2",
    "relation_informativeness_v2",
    "ontology_fit_v2",
    "uncertainty_reason_v2",
]

DEPLOYABLE_INTERNAL_EVIDENCE_KEYS = [
    "semantic_rank_hidden",
    "semantic_score_raw_hidden",
    "semantic_score_norm_hidden",
    "p_geom_valid_hidden",
    "absolute_disagreement_hidden",
]

HIDDEN_AUDIT_KEYS = [
    "prediction_id_hidden",
    "queue_kind_hidden",
    "proposed_audit_role_hidden",
    "label_match_status_hidden",
    "geometry_status_hidden",
    "rank_band_hidden",
    "relation_validity_label_hidden",
    "label_use_hidden",
    "posterior_target_y_hidden",
    "label_source_hidden",
    "reviewer_id_hidden",
    "human_confirmed_hidden",
]

HIDDEN_GROUP_KEYS = [
    "queue_kind_hidden",
    "proposed_audit_role_hidden",
    "label_match_status_hidden",
    "geometry_status_hidden",
    "rank_band_hidden",
    "relation_validity_label_hidden",
    "label_use_hidden",
    "posterior_target_y_hidden",
]

VISIBLE_NON_TARGET_GROUP_KEYS = [
    "predicate_family",
    "predicate_label",
    "evidence_packet_status",
]

FORBIDDEN_COMPLETED_HEADER_FRAGMENTS = [
    "independent_relation_label",
    "binary_target",
    "posterior_target",
    "target_y",
    "label_use",
    "confidence",
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "label_match",
    "proposed_audit_role",
    "prediction_id",
    "relation_validity_label",
]

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "normalized_mutual_information": 0.20,
    "positive_rate_range": 0.70,
    "large_group_rows": 10,
    "large_group_purity": 0.95,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--completed-sheet", type=Path, default=DEFAULT_COMPLETED_SHEET)
    parser.add_argument("--fill-summary", type=Path, default=DEFAULT_FILL_SUMMARY)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--internal-reference", type=Path, default=DEFAULT_INTERNAL_REFERENCE)
    parser.add_argument("--proximity-risk-slice", type=Path, default=DEFAULT_PROXIMITY_RISK_SLICE)
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
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        output = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(output) or math.isinf(output):
        return None
    return output


def nonempty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def validate_completed_headers(fieldnames: list[str], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = ["blind_review_id", *schema["required_completion_fields"]]
    for field in required:
        if field not in fieldnames:
            errors.append({"error_type": "missing_required_header", "field": field})
    for field in fieldnames:
        lower = field.lower()
        matches = [token for token in FORBIDDEN_COMPLETED_HEADER_FRAGMENTS if token in lower]
        if matches:
            errors.append({"error_type": "forbidden_completed_header", "field": field, "matches": matches})
    return errors


def validate_completed_row(
    row: dict[str, str],
    row_number: int,
    schema: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = schema["allowed_review_values"]
    for field in schema["required_completion_fields"]:
        value = str(row.get(field, "")).strip()
        if not value:
            errors.append(
                {
                    "error_type": "missing_required_completion_field",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id"),
                    "field": field,
                }
            )
            continue
        if field in allowed and value not in set(allowed[field]):
            errors.append(
                {
                    "error_type": "invalid_review_value",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id"),
                    "field": field,
                    "value": value,
                    "allowed": allowed[field],
                }
            )
    return errors


def validate_id_sets(
    completed_rows: list[dict[str, str]],
    internal_rows: list[dict[str, Any]],
    proximity_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    completed_ids = [str(row.get("blind_review_id") or "") for row in completed_rows]
    internal_ids = [str(row.get("blind_review_id") or "") for row in internal_rows]
    proximity_ids = [str(row.get("blind_review_id") or "") for row in proximity_rows]
    for blind_id, count in Counter(completed_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_completed_blind_review_id", "blind_review_id": blind_id, "count": count})
    for blind_id, count in Counter(internal_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_internal_blind_review_id", "blind_review_id": blind_id, "count": count})
    completed_set = {blind_id for blind_id in completed_ids if blind_id}
    internal_set = {blind_id for blind_id in internal_ids if blind_id}
    proximity_set = {blind_id for blind_id in proximity_ids if blind_id}
    for blind_id in sorted(completed_set - internal_set):
        errors.append({"error_type": "completed_id_missing_from_internal_reference", "blind_review_id": blind_id})
    for blind_id in sorted(internal_set - completed_set):
        errors.append({"error_type": "internal_reference_id_missing_from_completed_sheet", "blind_review_id": blind_id})
    for blind_id in sorted(completed_set & proximity_set):
        errors.append({"error_type": "proximity_risk_id_overlaps_selected_sheet", "blind_review_id": blind_id})
    return errors


def validate_internal_rows(internal_rows: list[dict[str, Any]], proximity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for idx, row in enumerate(internal_rows, start=1):
        blind_id = row.get("blind_review_id")
        if row.get("post_label_join_only") is not True:
            errors.append({"error_type": "internal_reference_not_post_label_only", "row_number": idx, "blind_review_id": blind_id})
        family = row.get("predicate_family")
        if family not in SELECTED_FAMILIES:
            errors.append(
                {
                    "error_type": "internal_reference_family_outside_selected_scope",
                    "row_number": idx,
                    "blind_review_id": blind_id,
                    "predicate_family": family,
                }
            )
    for idx, row in enumerate(proximity_rows, start=1):
        family = row.get("predicate_family")
        if family != EXCLUDED_RISK_FAMILY:
            errors.append(
                {
                    "error_type": "proximity_risk_slice_unexpected_family",
                    "row_number": idx,
                    "blind_review_id": row.get("blind_review_id"),
                    "predicate_family": family,
                }
            )
    return errors


def derive_geometry_validity(row: dict[str, str]) -> dict[str, Any]:
    answer = row["relation_geometry_answer_v2"]
    strength = row["geometry_evidence_strength_v2"]
    if answer == "contradicts_predicate":
        return {"target_name": "geometry_validity_target_v2", "target_use": "negative", "target_y": 0, "reason": "geometry_answer_contradicts"}
    if answer == "supports_predicate" and strength in {"strong", "moderate"}:
        return {"target_name": "geometry_validity_target_v2", "target_use": "positive", "target_y": 1, "reason": f"supports_with_{strength}_evidence"}
    return {"target_name": "geometry_validity_target_v2", "target_use": "exclude", "target_y": None, "reason": f"exclude_answer={answer}_strength={strength}"}


def derive_relation_reliability(row: dict[str, str]) -> dict[str, Any]:
    endpoint = row["endpoint_validity_v2"]
    visibility = row["pair_visibility_v2"]
    answer = row["relation_geometry_answer_v2"]
    strength = row["geometry_evidence_strength_v2"]
    informative = row["relation_informativeness_v2"]
    ontology = row["ontology_fit_v2"]

    negative_reasons: list[str] = []
    if endpoint in {"subject_invalid", "object_invalid", "pair_invalid"}:
        negative_reasons.append(f"endpoint={endpoint}")
    if answer == "contradicts_predicate":
        negative_reasons.append("geometry_contradicts")
    if informative in {"dense_trivial", "redundant_room_structure"}:
        negative_reasons.append(f"informativeness={informative}")
    if ontology in {"better_alternative_predicate", "ontology_mismatch"}:
        negative_reasons.append(f"ontology={ontology}")
    if negative_reasons:
        return {
            "target_name": "relation_reliability_target_v2",
            "target_use": "negative",
            "target_y": 0,
            "reason": ";".join(negative_reasons),
        }

    if (
        endpoint == "both_valid"
        and visibility in {"visible", "partially_visible"}
        and answer == "supports_predicate"
        and strength in {"strong", "moderate"}
        and informative == "informative"
        and ontology == "fits_predicate"
    ):
        return {
            "target_name": "relation_reliability_target_v2",
            "target_use": "positive",
            "target_y": 1,
            "reason": "all_reliability_positive_conditions_met",
        }

    return {
        "target_name": "relation_reliability_target_v2",
        "target_use": "exclude",
        "target_y": None,
        "reason": (
            f"exclude_endpoint={endpoint}_visibility={visibility}_answer={answer}_"
            f"strength={strength}_informativeness={informative}_ontology={ontology}"
        ),
    }


def target_derivation_fields(row: dict[str, str]) -> dict[str, Any]:
    return {
        "reviewer_id": row.get("reviewer_id"),
        "review_round": row.get("review_round"),
        "endpoint_validity_v2": row.get("endpoint_validity_v2"),
        "pair_visibility_v2": row.get("pair_visibility_v2"),
        "relation_geometry_answer_v2": row.get("relation_geometry_answer_v2"),
        "geometry_evidence_strength_v2": row.get("geometry_evidence_strength_v2"),
        "relation_informativeness_v2": row.get("relation_informativeness_v2"),
        "ontology_fit_v2": row.get("ontology_fit_v2"),
        "uncertainty_reason_v2": row.get("uncertainty_reason_v2"),
        "audit_notes_v2": row.get("audit_notes_v2"),
        "not_model_input": True,
    }


def deployable_evidence(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    visible_witness = {key: safe_float(row.get(key)) for key in VISIBLE_WITNESS_KEYS if key in row}
    source_geometry = {
        "semantic_rank": safe_float(internal.get("semantic_rank_hidden")),
        "semantic_score_raw": safe_float(internal.get("semantic_score_raw_hidden")),
        "semantic_score_norm": safe_float(internal.get("semantic_score_norm_hidden")),
        "p_geom_valid": safe_float(internal.get("p_geom_valid_hidden")),
        "absolute_disagreement": safe_float(internal.get("absolute_disagreement_hidden")),
    }
    return {
        "source_semantic_and_geometry_scores_hidden_from_labeler_until_lock": source_geometry,
        "raw_visible_witness_values": visible_witness,
        "coverage_evidence": {
            "evidence_packet_status": row.get("evidence_packet_status"),
        },
        "forbidden_as_posterior_input": {
            "target_derivation_audit_only_v2_fields": True,
            "geometry_status_hidden": True,
            "label_match_status_hidden": True,
            "proposed_audit_role_hidden": True,
            "queue_kind_hidden": True,
            "relation_validity_label_hidden": True,
            "posterior_target_y_hidden": True,
        },
    }


def hidden_audit_metadata(internal: dict[str, Any]) -> dict[str, Any]:
    metadata = {key: internal.get(key) for key in HIDDEN_AUDIT_KEYS}
    for key in DEPLOYABLE_INTERNAL_EVIDENCE_KEYS:
        metadata[key] = internal.get(key)
    return metadata


def base_identity(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": row["blind_review_id"],
        "prediction_id": internal.get("prediction_id_hidden"),
        "scan_id": internal.get("scan_id"),
        "subgraph_id": internal.get("subgraph_id"),
        "subject_id": internal.get("subject_id"),
        "subject_label": internal.get("subject_label"),
        "predicate_label": internal.get("predicate_label"),
        "predicate_family": internal.get("predicate_family"),
        "object_id": internal.get("object_id"),
        "object_label": internal.get("object_label"),
        "evidence_packet_status": row.get("evidence_packet_status"),
    }


def make_validated_label(row: dict[str, str], internal: dict[str, Any]) -> dict[str, Any]:
    geometry_target = derive_geometry_validity(row)
    reliability_target = derive_relation_reliability(row)
    return {
        "schema_version": "h002_support_vertical_v2_ingested_label_v1",
        **base_identity(row, internal),
        "label_source": LABEL_SOURCE,
        "not_human_confirmed": True,
        "paper_evidence_allowed": False,
        "posterior_claim_allowed": False,
        "hidden_reference_joined_after_label_lock": True,
        "direct_reliability_label_present": False,
        "target_derivation_audit_only": target_derivation_fields(row),
        "geometry_validity_target_v2": geometry_target,
        "relation_reliability_target_v2": reliability_target,
        "deployable_evidence_after_label_lock": deployable_evidence(row, internal),
        "hidden_audit_metadata_post_label_only": hidden_audit_metadata(internal),
        "boundary": {
            "split": "train_only",
            "label_source": LABEL_SOURCE,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_target_metadata_as_model_input": False,
            "target_derivation_fields_as_model_input": False,
            "multi_view_as_model_input": False,
            "proximity_excluded_from_main_path": True,
        },
    }


def target_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is None:
        return None
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
        "human_confirmed": False,
        "paper_locked": False,
    }


def posterior_row(label: dict[str, Any], target_key: str, schema_version: str) -> dict[str, Any] | None:
    row = target_row(label, target_key, schema_version)
    if row is None:
        return None
    return {
        **row,
        "deployable_evidence_after_label_lock": label["deployable_evidence_after_label_lock"],
        "audit_only_target_derivation_fields": label["target_derivation_audit_only"],
        "hidden_audit_metadata_post_label_only": label["hidden_audit_metadata_post_label_only"],
        "audit_note": (
            "Use deployable evidence for train-only posterior diagnostics. "
            "Do not use audit-only target-derivation fields or hidden metadata as model input."
        ),
    }


def excluded_target_row(label: dict[str, Any], target_key: str) -> dict[str, Any] | None:
    target = label[target_key]
    if target["target_y"] is not None:
        return None
    return {
        "schema_version": "h002_support_vertical_v2_excluded_target_v1",
        "target_name": target["target_name"],
        "target_use": target["target_use"],
        "target_y": None,
        "target_reason": target["reason"],
        "blind_review_id": label["blind_review_id"],
        "prediction_id": label["prediction_id"],
        "scan_id": label["scan_id"],
        "predicate_label": label["predicate_label"],
        "predicate_family": label["predicate_family"],
        "subject_label": label["subject_label"],
        "object_label": label["object_label"],
        "target_derivation_audit_only": label["target_derivation_audit_only"],
    }


def ingest(
    completed_rows: list[dict[str, str]],
    internal_rows: list[dict[str, Any]],
    schema: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    internal_by_id = {str(row["blind_review_id"]): row for row in internal_rows}
    labels: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(completed_rows, start=2):
        row_errors = validate_completed_row(row, row_number, schema)
        blind_id = str(row.get("blind_review_id") or "")
        if not blind_id:
            row_errors.append({"error_type": "missing_blind_review_id", "row_number": row_number})
        internal = internal_by_id.get(blind_id)
        if internal is None:
            row_errors.append({"error_type": "missing_internal_reference_for_completed_row", "row_number": row_number, "blind_review_id": blind_id})
        completed_family = row.get("predicate_family")
        if completed_family not in SELECTED_FAMILIES:
            row_errors.append(
                {
                    "error_type": "completed_row_family_outside_selected_scope",
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "predicate_family": completed_family,
                }
            )
        if row_errors:
            errors.extend(row_errors)
            continue
        labels.append(make_validated_label(row, internal_by_id[blind_id]))
    return labels, errors


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
    evidence = row.get("deployable_evidence_after_label_lock", {})
    coverage = evidence.get("coverage_evidence", {})
    if key in coverage:
        return str(coverage.get(key))
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
    pos_rate_min = min(positive_rates) if positive_rates else 0.0
    pos_rate_max = max(positive_rates) if positive_rates else 0.0
    pos_rate_range = pos_rate_max - pos_rate_min
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
        "positive_rate_min": pos_rate_min,
        "positive_rate_max": pos_rate_max,
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
            "schema_version": "h002_support_vertical_v2_target_independence_probe_v1",
            "target_name": target_name,
            "status": "target_independence_probe_no_binary_rows",
            "risk_thresholds": RISK_THRESHOLDS,
            "summaries": [],
            "group_table": [],
            "hidden_risks": [],
            "visible_non_target_shortcuts": [],
        }
    for key in VISIBLE_NON_TARGET_GROUP_KEYS:
        table, summary = group_probe(target_rows, key, "visible_non_target_surface", target_name)
        group_table.extend(table)
        summaries.append(summary)
    for key in HIDDEN_GROUP_KEYS:
        table, summary = group_probe(target_rows, key, "hidden_post_label_audit", target_name)
        group_table.extend(table)
        summaries.append(summary)

    hidden_risks = [item for item in summaries if item["source"] == "hidden_post_label_audit" and item["risk_flag"]]
    visible_shortcuts = [item for item in summaries if item["source"] == "visible_non_target_surface" and item["risk_flag"]]
    if hidden_risks:
        status = "target_independence_risk_hidden_metadata_correlated"
    elif visible_shortcuts:
        status = "target_independence_risk_visible_non_target_shortcut"
    else:
        status = "target_independence_probe_pass"
    return {
        "schema_version": "h002_support_vertical_v2_target_independence_probe_v1",
        "target_name": target_name,
        "status": status,
        "risk_thresholds": RISK_THRESHOLDS,
        "summaries": summaries,
        "group_table": group_table,
        "hidden_risks": sorted(
            hidden_risks,
            key=lambda row: (-row["normalized_mutual_information"], -row["majority_rule_accuracy"]),
        ),
        "visible_non_target_shortcuts": sorted(
            visible_shortcuts,
            key=lambda row: (-row["normalized_mutual_information"], -row["majority_rule_accuracy"]),
        ),
    }


def count_target(rows: list[dict[str, Any]]) -> dict[str, Any]:
    target_counts = Counter(row["target_y"] for row in rows)
    total = len(rows)
    return {
        "rows": total,
        "positive": target_counts[1],
        "negative": target_counts[0],
        "positive_rate": (target_counts[1] / total) if total else 0.0,
        "by_family": nested_target_counts(rows, "predicate_family"),
        "by_predicate": nested_target_counts(rows, "predicate_label"),
    }


def nested_target_counts(rows: list[dict[str, Any]], group_key: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[str(row.get(group_key))][str(row.get("target_y"))] += 1
    return {key: dict(sorted(counter.items())) for key, counter in sorted(grouped.items())}


def axis_counts(labels: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    output: dict[str, dict[str, int]] = {}
    for axis in V2_TARGET_AXIS_KEYS:
        output[axis] = dict(sorted(Counter(row["target_derivation_audit_only"].get(axis) for row in labels).items()))
    return output


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Full-Train Independent Support/Vertical V2 Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage ingestion.",
        "- No validation/test rows are used.",
        "- No posterior is trained in this step.",
        "- V2 factual axes are joined to hidden provenance only after label lock.",
        "- Hidden metadata and v2 target-derivation fields are audit-only, not posterior input.",
        "- Geometry validity and relation reliability targets are derived separately.",
        "- Multi-view evidence remains audit evidence only.",
        "- Labels are Codex bootstrap labels, not human-confirmed paper evidence.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| completed sheet rows | {counts['completed_sheet_rows']} |",
        f"| internal reference rows | {counts['internal_reference_rows']} |",
        f"| proximity risk slice rows | {counts['proximity_risk_slice_rows']} |",
        f"| validated v2 labels | {counts['validated_label_rows']} |",
        f"| ingestion errors | {counts['errors']} |",
        "",
        "## Target Counts",
        "",
        "| Target | Rows | Positive | Negative | Positive Rate | Excluded |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for target_name in ["geometry_validity_target_v2", "relation_reliability_target_v2"]:
        item = counts["targets"][target_name]
        lines.append(
            f"| `{target_name}` | {item['rows']} | {item['positive']} | {item['negative']} | "
            f"{item['positive_rate']:.4f} | {counts['excluded_targets'][target_name]} |"
        )
    lines.extend(
        [
            "",
            "## Axis Counts",
            "",
        ]
    )
    for axis, values in summary["axis_counts"].items():
        joined = ", ".join(f"`{key}:{value}`" for key, value in values.items())
        lines.append(f"- `{axis}`: {joined}")
    lines.extend(
        [
            "",
            "## Target Independence Probe",
            "",
            "| Target | Probe Status | Hidden Risks | Visible Non-Target Shortcuts |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for target_name, probe in summary["target_independence_probes"].items():
        lines.append(
            f"| `{target_name}` | `{probe['status']}` | {len(probe['hidden_risks'])} | "
            f"{len(probe['visible_non_target_shortcuts'])} |"
        )
    lines.extend(
        [
            "",
            "## Top Hidden Risks",
            "",
            "| Target | Hidden Key | Majority Acc | NMI | Pos Rate Range |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for target_name, probe in summary["target_independence_probes"].items():
        for item in probe["hidden_risks"][:6]:
            lines.append(
                f"| `{target_name}` | `{item['group_key']}` | {item['majority_rule_accuracy']:.4f} | "
                f"{item['normalized_mutual_information']:.4f} | {item['positive_rate_range']:.4f} |"
            )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    completed_sheet = as_abs(args.completed_sheet)
    fill_summary_path = as_abs(args.fill_summary)
    schema_path = as_abs(args.schema)
    internal_reference_path = as_abs(args.internal_reference)
    proximity_risk_slice_path = as_abs(args.proximity_risk_slice)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).isoformat()
    fieldnames, completed_rows = read_tsv(completed_sheet)
    fill_summary = read_json(fill_summary_path)
    schema = read_json(schema_path)
    internal_rows = read_jsonl(internal_reference_path)
    proximity_rows = read_jsonl(proximity_risk_slice_path)

    errors: list[dict[str, Any]] = []
    errors.extend(validate_completed_headers(fieldnames, schema))
    errors.extend(validate_id_sets(completed_rows, internal_rows, proximity_rows))
    errors.extend(validate_internal_rows(internal_rows, proximity_rows))
    boundary = fill_summary.get("boundary", {})
    if boundary.get("hidden_reference_read") is not False:
        errors.append({"error_type": "fill_summary_does_not_confirm_hidden_reference_was_unread"})
    if boundary.get("source_score_or_rank_used") is not False:
        errors.append({"error_type": "fill_summary_does_not_confirm_source_score_rank_was_unread"})
    if boundary.get("p_geom_valid_used") is not False:
        errors.append({"error_type": "fill_summary_does_not_confirm_p_geom_valid_was_unread"})
    if boundary.get("direct_reliability_label_filled") is not False:
        errors.append({"error_type": "fill_summary_does_not_confirm_direct_reliability_label_absent"})
    if boundary.get("binary_target_filled") is not False:
        errors.append({"error_type": "fill_summary_does_not_confirm_binary_target_absent"})

    validated_labels, row_errors = ingest(completed_rows, internal_rows, schema)
    errors.extend(row_errors)

    geometry_targets = [
        row
        for row in (target_row(label, "geometry_validity_target_v2", "h002_support_vertical_v2_geometry_validity_target_v1") for label in validated_labels)
        if row is not None
    ]
    reliability_targets = [
        row
        for row in (target_row(label, "relation_reliability_target_v2", "h002_support_vertical_v2_relation_reliability_target_v1") for label in validated_labels)
        if row is not None
    ]
    geometry_posterior_rows = [
        row
        for row in (
            posterior_row(label, "geometry_validity_target_v2", "h002_support_vertical_v2_geometry_validity_posterior_row_v1")
            for label in validated_labels
        )
        if row is not None
    ]
    reliability_posterior_rows = [
        row
        for row in (
            posterior_row(label, "relation_reliability_target_v2", "h002_support_vertical_v2_relation_reliability_posterior_row_v1")
            for label in validated_labels
        )
        if row is not None
    ]
    excluded_targets = [
        row
        for label in validated_labels
        for row in (
            excluded_target_row(label, "geometry_validity_target_v2"),
            excluded_target_row(label, "relation_reliability_target_v2"),
        )
        if row is not None
    ]

    probes = {
        "geometry_validity_target_v2": target_independence_probe(geometry_posterior_rows, "geometry_validity_target_v2"),
        "relation_reliability_target_v2": target_independence_probe(reliability_posterior_rows, "relation_reliability_target_v2"),
    }
    all_group_rows = [row for probe in probes.values() for row in probe["group_table"]]
    all_probe_summaries = [row for probe in probes.values() for row in probe["summaries"]]

    target_counts = {
        "geometry_validity_target_v2": count_target(geometry_targets),
        "relation_reliability_target_v2": count_target(reliability_targets),
    }
    excluded_counts = Counter(row["target_name"] for row in excluded_targets)

    if errors:
        status = "full_train_independent_support_vertical_v2_label_ingestion_errors"
        decision = "Fix v2 support/vertical ingestion errors before target audit or posterior smoke."
        next_todo = "fix_full_train_independent_support_vertical_v2_label_ingestion_errors"
    elif not reliability_targets:
        status = "full_train_independent_support_vertical_v2_label_ingestion_no_reliability_targets"
        decision = "V2 labels were ingested, but no relation reliability target rows were materialized."
        next_todo = "revise_full_train_independent_support_vertical_v2_label_policy"
    elif any(probe["status"] != "target_independence_probe_pass" for probe in probes.values()):
        status = "full_train_independent_support_vertical_v2_label_ingested_with_target_risk"
        decision = (
            "V2 factual axes and derived targets are materialized, but the basic post-label "
            "probe still finds group-level target risk. Run a dedicated v2 target-independence "
            "audit before any posterior smoke."
        )
        next_todo = "full_train_independent_support_vertical_v2_target_independence_audit"
    else:
        status = "full_train_independent_support_vertical_v2_label_ingested_ready_for_target_audit"
        decision = (
            "V2 factual axes and derived targets are materialized with no basic group-level "
            "shortcut risk. Run the dedicated target audit before any posterior smoke."
        )
        next_todo = "full_train_independent_support_vertical_v2_target_independence_audit"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validated_labels": output_dir / "validated_v2_labels.jsonl",
        "geometry_validity_targets": output_dir / "geometry_validity_targets_v2.jsonl",
        "relation_reliability_targets": output_dir / "relation_reliability_targets_v2.jsonl",
        "geometry_validity_posterior_rows": output_dir / "geometry_validity_posterior_rows_v2.jsonl",
        "relation_reliability_posterior_rows": output_dir / "relation_reliability_posterior_rows_v2.jsonl",
        "excluded_targets": output_dir / "excluded_targets_v2.jsonl",
        "target_independence_probe": output_dir / "target_independence_probe.json",
        "target_group_table": output_dir / "target_group_table.csv",
        "shortcut_audit": output_dir / "shortcut_audit.csv",
        "ingestion_errors": output_dir / "ingestion_errors.jsonl",
    }

    summary = {
        "schema_version": "h002_support_vertical_v2_label_ingestion_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "completed_sheet": rel_path(completed_sheet),
            "fill_summary": rel_path(fill_summary_path),
            "completion_schema": rel_path(schema_path),
            "internal_reference_post_label_only": rel_path(internal_reference_path),
            "proximity_risk_slice_post_label_only": rel_path(proximity_risk_slice_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "selected_scope": sorted(SELECTED_FAMILIES),
            "excluded_risk_scope": EXCLUDED_RISK_FAMILY,
            "label_source": LABEL_SOURCE,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_reference_joined_after_label_lock": True,
            "hidden_target_metadata_as_model_input": False,
            "target_derivation_fields_as_model_input": False,
            "deployable_source_scores_hidden_from_labeler_until_lock": True,
            "multi_view_as_model_input": False,
            "geometry_validity_and_relation_reliability_separated": True,
        },
        "counts": {
            "completed_sheet_rows": len(completed_rows),
            "internal_reference_rows": len(internal_rows),
            "proximity_risk_slice_rows": len(proximity_rows),
            "validated_label_rows": len(validated_labels),
            "errors": len(errors),
            "targets": target_counts,
            "excluded_targets": {
                "geometry_validity_target_v2": excluded_counts["geometry_validity_target_v2"],
                "relation_reliability_target_v2": excluded_counts["relation_reliability_target_v2"],
            },
        },
        "axis_counts": axis_counts(validated_labels),
        "target_independence_probes": {
            target_name: {key: value for key, value in probe.items() if key != "group_table"}
            for target_name, probe in probes.items()
        },
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["target_independence_probe"], probes)
    write_jsonl(output_paths["validated_labels"], validated_labels)
    write_jsonl(output_paths["geometry_validity_targets"], geometry_targets)
    write_jsonl(output_paths["relation_reliability_targets"], reliability_targets)
    write_jsonl(output_paths["geometry_validity_posterior_rows"], geometry_posterior_rows)
    write_jsonl(output_paths["relation_reliability_posterior_rows"], reliability_posterior_rows)
    write_jsonl(output_paths["excluded_targets"], excluded_targets)
    write_jsonl(output_paths["ingestion_errors"], errors)
    write_csv(output_paths["target_group_table"], all_group_rows)
    write_csv(output_paths["shortcut_audit"], all_probe_summaries)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    geom = counts["targets"]["geometry_validity_target_v2"]
    rel = counts["targets"]["relation_reliability_target_v2"]
    print(
        f"status={summary['status']} labels={counts['validated_label_rows']} "
        f"geom_binary={geom['rows']} geom_pos={geom['positive']} geom_neg={geom['negative']} "
        f"rel_binary={rel['rows']} rel_pos={rel['positive']} rel_neg={rel['negative']} "
        f"errors={counts['errors']} validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
