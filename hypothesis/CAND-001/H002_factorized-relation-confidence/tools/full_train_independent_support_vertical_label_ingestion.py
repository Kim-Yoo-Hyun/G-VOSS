#!/usr/bin/env python3
"""Ingest selected support/vertical labels after label lock."""

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

DEFAULT_FILL_DIR = RGA_ROOT / "independent_support_vertical_label_fill_codex_ver"
DEFAULT_READINESS_DIR = RGA_ROOT / "independent_support_vertical_label_readiness_codex_ver"
DEFAULT_PACKET_DIR = RGA_ROOT / "independent_support_vertical_audit_packet_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_label_ingestion_codex_ver"

DEFAULT_COMPLETED_SHEET = DEFAULT_FILL_DIR / "completed_support_vertical_label_fill_sheet_codex_ver.tsv"
DEFAULT_FILL_SUMMARY = DEFAULT_FILL_DIR / "summary.json"
DEFAULT_SCHEMA = DEFAULT_READINESS_DIR / "completion_schema.json"
DEFAULT_INTERNAL_REFERENCE = DEFAULT_PACKET_DIR / "internal_reference_post_label_only.jsonl"
DEFAULT_PROXIMITY_RISK_SLICE = DEFAULT_PACKET_DIR / "proximity_risk_slice_post_label_only.jsonl"

LABEL_SOURCE = "codex_ver_support_vertical_visible_witness_bootstrap"
SELECTED_FAMILIES = {"support_contact", "relative_vertical"}
EXCLUDED_RISK_FAMILY = "proximity"

FORBIDDEN_COMPLETED_HEADER_FRAGMENTS = [
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "label_match",
    "proposed",
    "queue",
    "target",
    "posterior",
    "hidden",
    "relation_validity_label",
]

DEPLOYABLE_INTERNAL_EVIDENCE_KEYS = [
    "semantic_rank_hidden",
    "semantic_score_raw_hidden",
    "semantic_score_norm_hidden",
    "p_geom_valid_hidden",
    "absolute_disagreement_hidden",
]

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
]

VISIBLE_GROUP_KEYS = [
    "predicate_family",
    "predicate_label",
    "confidence",
    "visual_3d_support",
    "relation_informativeness",
    "object_pair_visible",
    "evidence_packet_status",
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


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
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


def label_to_binary_policy(schema: dict[str, Any]) -> dict[str, str]:
    policy: dict[str, str] = {}
    for use, labels in schema["label_to_binary_policy"].items():
        for label in labels:
            policy[label] = use
    return policy


def label_use(label: str, policy: dict[str, str]) -> str:
    return policy[label]


def binary_y(use: str) -> int | None:
    if use == "positive":
        return 1
    if use == "negative":
        return 0
    return None


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
            errors.append(
                {
                    "error_type": "forbidden_completed_header",
                    "field": field,
                    "matches": matches,
                }
            )
    return errors


def validate_completed_row(
    row: dict[str, str],
    row_number: int,
    schema: dict[str, Any],
    policy: dict[str, str],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = schema["allowed_review_values"]
    for field in schema["required_completion_fields"]:
        value = row.get(field)
        if not nonempty(value):
            errors.append(
                {
                    "error_type": "missing_required_completion_field",
                    "row_number": row_number,
                    "blind_review_id": row.get("blind_review_id"),
                    "field": field,
                }
            )
            continue
        if field in allowed and str(value).strip() not in set(allowed[field]):
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
    label = str(row.get("independent_relation_label") or "").strip()
    if label and label not in policy:
        errors.append(
            {
                "error_type": "label_missing_from_binary_policy",
                "row_number": row_number,
                "blind_review_id": row.get("blind_review_id"),
                "label": label,
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
            "object_pair_visible": row.get("object_pair_visible"),
            "relation_visible_or_inferable": row.get("relation_visible_or_inferable"),
            "confidence": row.get("confidence"),
        },
        "forbidden_as_posterior_input": {
            "geometry_status_hidden": False,
            "label_match_status_hidden": False,
            "proposed_audit_role_hidden": False,
            "queue_kind_hidden": False,
            "relation_validity_label_hidden": False,
            "posterior_target_y_hidden": False,
        },
    }


def hidden_audit_metadata(internal: dict[str, Any]) -> dict[str, Any]:
    metadata = {key: internal.get(key) for key in HIDDEN_AUDIT_KEYS}
    for key in DEPLOYABLE_INTERNAL_EVIDENCE_KEYS:
        metadata[key] = internal.get(key)
    return metadata


def make_validated_label(
    row: dict[str, str],
    internal: dict[str, Any],
    policy: dict[str, str],
) -> dict[str, Any]:
    label = str(row["independent_relation_label"]).strip()
    use = label_use(label, policy)
    y = binary_y(use)
    return {
        "schema_version": "h002_support_vertical_ingested_label_v1",
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
        "independent_relation_label": label,
        "label_use": use,
        "posterior_target": y,
        "binary_usable": y is not None,
        "reviewer_id": row.get("reviewer_id"),
        "review_round": row.get("review_round"),
        "subject_identity_valid": row.get("subject_identity_valid"),
        "object_identity_valid": row.get("object_identity_valid"),
        "object_pair_visible": row.get("object_pair_visible"),
        "relation_visible_or_inferable": row.get("relation_visible_or_inferable"),
        "visual_3d_support": row.get("visual_3d_support"),
        "relation_informativeness": row.get("relation_informativeness"),
        "confidence": row.get("confidence"),
        "evidence_packet_status": row.get("evidence_packet_status"),
        "evidence_notes": row.get("evidence_notes"),
        "deployable_evidence_after_label_lock": deployable_evidence(row, internal),
        "hidden_audit_metadata_post_label_only": hidden_audit_metadata(internal),
        "boundary": {
            "split": "train_only",
            "label_source": LABEL_SOURCE,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_internal_reference_joined_after_label_lock": True,
            "hidden_target_metadata_as_model_input": False,
            "multi_view_as_model_input": False,
            "proximity_excluded_from_main_path": True,
        },
    }


def build_targets(labels: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    multiclass: list[dict[str, Any]] = []
    binary: list[dict[str, Any]] = []
    posterior_rows: list[dict[str, Any]] = []
    for label in labels:
        base = {
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
            "independent_relation_label": label["independent_relation_label"],
            "label_use": label["label_use"],
            "reviewer_id": label["reviewer_id"],
            "confidence": label["confidence"],
        }
        multiclass.append(
            {
                "schema_version": "h002_support_vertical_multiclass_target_v1",
                **base,
                "allowed_use": "train-only support/vertical reliability taxonomy and diagnostics",
                "paper_locked": False,
                "human_confirmed": False,
            }
        )
        if not label["binary_usable"]:
            continue
        binary_row = {
            "schema_version": "h002_support_vertical_binary_target_v1",
            **base,
            "posterior_target": label["posterior_target"],
            "allowed_use": "train-only support/vertical posterior diagnostic",
            "paper_locked": False,
            "human_confirmed": False,
        }
        binary.append(binary_row)
        posterior_rows.append(
            {
                **binary_row,
                "schema_version": "h002_support_vertical_posterior_row_v1",
                "deployable_evidence_after_label_lock": label["deployable_evidence_after_label_lock"],
                "hidden_audit_metadata_post_label_only": label["hidden_audit_metadata_post_label_only"],
                "audit_note": (
                    "Use deployable evidence for train-only posterior diagnostics. "
                    "Use hidden metadata only for post-label target-independence audits."
                ),
            }
        )
    return multiclass, binary, posterior_rows


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


def group_probe(rows: list[dict[str, Any]], key: str, source: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[group_value(row, key)].append(row)

    overall_counts = Counter(int(row["posterior_target"]) for row in rows)
    overall_entropy = entropy_from_counts(overall_counts)
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    positive_rates: list[float] = []
    large_group_high_purity = False
    table: list[dict[str, Any]] = []
    for value, group_rows in sorted(groups.items()):
        counts = Counter(int(row["posterior_target"]) for row in group_rows)
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


def target_independence_probe(posterior_rows: list[dict[str, Any]]) -> dict[str, Any]:
    group_table: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for key in VISIBLE_GROUP_KEYS:
        table, summary = group_probe(posterior_rows, key, "visible_label_surface")
        group_table.extend(table)
        summaries.append(summary)
    for key in HIDDEN_GROUP_KEYS:
        table, summary = group_probe(posterior_rows, key, "hidden_post_label_audit")
        group_table.extend(table)
        summaries.append(summary)

    hidden_risks = [
        item
        for item in summaries
        if item["source"] == "hidden_post_label_audit" and item["risk_flag"]
    ]
    visible_shortcuts = [
        item
        for item in summaries
        if item["source"] == "visible_label_surface" and item["risk_flag"]
    ]
    if hidden_risks:
        status = "target_independence_risk_hidden_metadata_correlated"
    elif visible_shortcuts:
        status = "target_independence_risk_visible_policy_shortcut"
    else:
        status = "target_independence_probe_pass"

    return {
        "schema_version": "h002_support_vertical_target_independence_probe_v1",
        "status": status,
        "risk_thresholds": RISK_THRESHOLDS,
        "summaries": summaries,
        "group_table": group_table,
        "hidden_risks": sorted(
            hidden_risks,
            key=lambda row: (-row["normalized_mutual_information"], -row["majority_rule_accuracy"]),
        ),
        "visible_shortcuts": sorted(
            visible_shortcuts,
            key=lambda row: (-row["normalized_mutual_information"], -row["majority_rule_accuracy"]),
        ),
    }


def ingest(
    completed_rows: list[dict[str, str]],
    internal_rows: list[dict[str, Any]],
    schema: dict[str, Any],
    policy: dict[str, str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    internal_by_id = {str(row["blind_review_id"]): row for row in internal_rows}
    labels: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(completed_rows, start=2):
        row_errors = validate_completed_row(row, row_number, schema, policy)
        blind_id = str(row.get("blind_review_id") or "")
        if not blind_id:
            row_errors.append({"error_type": "missing_blind_review_id", "row_number": row_number})
        internal = internal_by_id.get(blind_id)
        if internal is None:
            row_errors.append(
                {
                    "error_type": "missing_internal_reference_for_completed_row",
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                }
            )
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
        labels.append(make_validated_label(row, internal_by_id[blind_id], policy))
    return labels, errors


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key)) for row in rows).items()))


def nested_label_counts(rows: list[dict[str, Any]], group_key: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[str(row.get(group_key))][str(row.get("independent_relation_label"))] += 1
    return {key: dict(sorted(counter.items())) for key, counter in sorted(grouped.items())}


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    probe = summary["target_independence_probe"]
    lines = [
        "# H002 Full-Train Independent Support/Vertical Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage ingestion.",
        "- No validation/test rows are used.",
        "- No posterior is trained in this step.",
        "- Completed labels are joined to hidden provenance only after label lock.",
        "- Hidden target-construction metadata is audit-only and not posterior input.",
        "- Multi-view evidence remains audit evidence only.",
        "- Labels are Codex bootstrap labels, not human-confirmed paper evidence.",
        "- `proximity` remains excluded from the main support/vertical path.",
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
        f"| validated label rows | {counts['validated_label_rows']} |",
        f"| binary target rows | {counts['binary_target_rows']} |",
        f"| positive rows | {counts['positive_rows']} |",
        f"| negative rows | {counts['negative_rows']} |",
        f"| excluded rows | {counts['excluded_rows']} |",
        f"| ingestion errors | {counts['errors']} |",
        "",
        "## Label Counts",
        "",
        "| Label | Rows |",
        "| --- | ---: |",
    ]
    for label, count in summary["label_counts"].items():
        lines.append(f"| `{label}` | {count} |")
    lines.extend(
        [
            "",
            "## Family Counts",
            "",
            "| Family | Labels |",
            "| --- | --- |",
        ]
    )
    for family, labels in summary["labels_by_family"].items():
        joined = ", ".join(f"`{label}:{count}`" for label, count in labels.items())
        lines.append(f"| `{family}` | {joined} |")
    lines.extend(
        [
            "",
            "## Target Independence Probe",
            "",
            f"Probe status: `{probe['status']}`",
            "",
            "| Source | Group Key | Majority Acc | NMI | Pos Rate Range | Risk |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for item in sorted(
        probe["summaries"],
        key=lambda row: (
            0 if row["source"] == "hidden_post_label_audit" else 1,
            -row["risk_flag"],
            -row["normalized_mutual_information"],
            -row["majority_rule_accuracy"],
        ),
    ):
        lines.append(
            "| `{source}` | `{group_key}` | {majority_rule_accuracy:.4f} | "
            "{normalized_mutual_information:.4f} | {positive_rate_range:.4f} | `{risk_flag}` |".format(
                **item
            )
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
    policy = label_to_binary_policy(schema)
    internal_rows = read_jsonl(internal_reference_path)
    proximity_rows = read_jsonl(proximity_risk_slice_path)

    errors: list[dict[str, Any]] = []
    errors.extend(validate_completed_headers(fieldnames, schema))
    errors.extend(validate_id_sets(completed_rows, internal_rows, proximity_rows))
    errors.extend(validate_internal_rows(internal_rows, proximity_rows))
    if fill_summary.get("boundary", {}).get("hidden_internal_reference_read") is not False:
        errors.append({"error_type": "fill_summary_does_not_confirm_hidden_reference_was_unread"})
    if fill_summary.get("boundary", {}).get("source_score_or_rank_used") is not False:
        errors.append({"error_type": "fill_summary_does_not_confirm_source_score_rank_was_unread"})

    validated_labels, row_errors = ingest(completed_rows, internal_rows, schema, policy)
    errors.extend(row_errors)
    multiclass_targets, binary_targets, posterior_rows = build_targets(validated_labels)
    probe = target_independence_probe(posterior_rows) if posterior_rows else {
        "schema_version": "h002_support_vertical_target_independence_probe_v1",
        "status": "target_independence_probe_no_binary_rows",
        "risk_thresholds": RISK_THRESHOLDS,
        "summaries": [],
        "group_table": [],
        "hidden_risks": [],
        "visible_shortcuts": [],
    }

    target_counts = Counter(row["posterior_target"] for row in binary_targets)
    label_counts = dict(sorted(Counter(row["independent_relation_label"] for row in validated_labels).items()))
    binary_rows = len(binary_targets)
    positive_rate = target_counts[1] / binary_rows if binary_rows else 0.0

    if errors:
        status = "full_train_independent_support_vertical_label_ingestion_errors"
        decision = "Fix support/vertical ingestion errors before target audit or posterior smoke."
        next_todo = "fix_full_train_independent_support_vertical_label_ingestion_errors"
    elif not binary_targets:
        status = "full_train_independent_support_vertical_label_ingestion_no_binary_targets"
        decision = "Labels were ingested, but no binary target rows were materialized."
        next_todo = "revise_full_train_independent_support_vertical_label_policy"
    elif probe["status"] != "target_independence_probe_pass":
        status = "full_train_independent_support_vertical_label_ingested_with_target_risk"
        decision = (
            "Support/vertical labels and targets are materialized, but the post-label "
            "target probe shows shortcut risk. Run a dedicated target-independence audit "
            "before posterior smoke."
        )
        next_todo = "full_train_independent_support_vertical_target_independence_audit"
    else:
        status = "full_train_independent_support_vertical_label_ingested_ready_for_target_audit"
        decision = (
            "Support/vertical labels and targets are materialized with no basic group-level "
            "shortcut risk. Run the dedicated target audit before any posterior smoke."
        )
        next_todo = "full_train_independent_support_vertical_target_independence_audit"

    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"
    validated_path = output_dir / "validated_labels.jsonl"
    binary_path = output_dir / "binary_targets.jsonl"
    multiclass_path = output_dir / "multiclass_targets.jsonl"
    posterior_path = output_dir / "posterior_rows.jsonl"
    errors_path = output_dir / "ingestion_errors.jsonl"
    probe_path = output_dir / "target_independence_probe.json"
    group_table_path = output_dir / "target_group_table.csv"
    shortcut_audit_path = output_dir / "shortcut_audit.csv"

    summary = {
        "schema_version": "h002_support_vertical_label_ingestion_summary_v1",
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
        "output_paths": {
            "summary": rel_path(summary_path),
            "report": rel_path(report_path),
            "validated_labels": rel_path(validated_path),
            "binary_targets": rel_path(binary_path),
            "multiclass_targets": rel_path(multiclass_path),
            "posterior_rows": rel_path(posterior_path),
            "ingestion_errors": rel_path(errors_path),
            "target_independence_probe": rel_path(probe_path),
            "target_group_table": rel_path(group_table_path),
            "shortcut_audit": rel_path(shortcut_audit_path),
        },
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
            "deployable_source_scores_hidden_from_labeler_until_lock": True,
            "multi_view_as_model_input": False,
        },
        "counts": {
            "completed_sheet_rows": len(completed_rows),
            "internal_reference_rows": len(internal_rows),
            "proximity_risk_slice_rows": len(proximity_rows),
            "validated_label_rows": len(validated_labels),
            "binary_target_rows": len(binary_targets),
            "positive_rows": target_counts[1],
            "negative_rows": target_counts[0],
            "excluded_rows": len(validated_labels) - len(binary_targets),
            "positive_rate_binary": positive_rate,
            "multiclass_target_rows": len(multiclass_targets),
            "errors": len(errors),
        },
        "label_counts": label_counts,
        "labels_by_family": nested_label_counts(validated_labels, "predicate_family"),
        "labels_by_predicate": nested_label_counts(validated_labels, "predicate_label"),
        "binary_by_family": nested_label_counts(binary_targets, "predicate_family"),
        "visible_group_counts": {
            "predicate_family": count_by(validated_labels, "predicate_family"),
            "predicate_label": count_by(validated_labels, "predicate_label"),
            "confidence": count_by(validated_labels, "confidence"),
            "visual_3d_support": count_by(validated_labels, "visual_3d_support"),
            "relation_informativeness": count_by(validated_labels, "relation_informativeness"),
        },
        "target_independence_probe": {
            key: value for key, value in probe.items() if key != "group_table"
        },
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(summary_path, summary)
    write_json(probe_path, probe)
    write_jsonl(validated_path, validated_labels)
    write_jsonl(binary_path, binary_targets)
    write_jsonl(multiclass_path, multiclass_targets)
    write_jsonl(posterior_path, posterior_rows)
    write_jsonl(errors_path, errors)
    write_csv(group_table_path, probe["group_table"])
    write_csv(shortcut_audit_path, probe["summaries"])
    write_report(report_path, summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    probe = summary["target_independence_probe"]
    print(
        f"status={summary['status']} labels={counts['validated_label_rows']} "
        f"binary={counts['binary_target_rows']} positive={counts['positive_rows']} "
        f"negative={counts['negative_rows']} excluded={counts['excluded_rows']} "
        f"errors={counts['errors']} probe={probe['status']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
