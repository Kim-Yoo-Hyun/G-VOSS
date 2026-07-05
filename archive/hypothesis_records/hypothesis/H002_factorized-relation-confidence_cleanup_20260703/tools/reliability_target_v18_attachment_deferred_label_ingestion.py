#!/usr/bin/env python3
"""Ingest H002 v18 attachment-deferred labels and run quick target probes."""

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

FILL_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_label_fill"
CANDIDATE_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_candidate_mining"

DEFAULT_FILL_SUMMARY = FILL_DIR / "summary.json"
DEFAULT_FILLED_SHEET = FILL_DIR / "filled_label_sheet_v18.tsv"
DEFAULT_HIDDEN_MANIFEST = CANDIDATE_DIR / "hidden_audit_manifest_v18.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_label_ingestion"

SCHEMA_VERSION = "h002_reliability_target_v18_attachment_deferred_label_ingestion_v1"
EXPECTED_FILL_STATUS = "h002_reliability_target_v18_attachment_deferred_label_filled_codex_proxy_visible_only"
EXPECTED_FILL_NEXT_TODO = "reliability_target_v18_attachment_deferred_label_ingestion"
NEXT_TODO = "reliability_target_v18_attachment_deferred_target_independence_audit"

LABEL_SOURCE = "codex_proxy_v18_attachment_deferred_visible_only_user_requested"
MIN_CLASS_MASS_FOR_POSTERIOR = 50

MULTICLASS_TARGET = "attachment_deferred_reliability_v18_multiclass"
BINARY_TARGET = "attachment_deferred_primary_reliability_v18_binary"
GEOMETRY_SUPPORT_TARGET = "attachment_deferred_geometry_support_v18_binary"
USEFULNESS_TARGET = "attachment_deferred_usefulness_v18_binary"
ENDPOINT_TARGET = "attachment_deferred_endpoint_identity_v18_multiclass"
COVERAGE_TARGET = "attachment_deferred_coverage_v18_multiclass"
DIAGNOSTIC_TARGET = "attachment_deferred_connected_diagnostic_v18_multiclass"

VISIBLE_IDENTITY_FIELDS = [
    "blind_review_id",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
]

VISIBLE_CONTEXT_FIELDS = [
    "scene_context_summary_v18",
    "geometry_witness_summary_v18",
    "attachment_witness_summary_v18",
    "coverage_summary_v18",
    "uncertainty_summary_v18",
]

COMPLETION_FIELDS = [
    "reviewer_id_v18",
    "review_round_v18",
    "label_policy_v18",
    "relation_reliability_state_v18",
    "geometry_support_state_v18",
    "relation_usefulness_state_v18",
    "endpoint_identity_state_v18",
    "coverage_state_v18",
    "primary_reason_v18",
    "uncertainty_reason_v18",
    "review_notes_v18",
]

HIDDEN_AUDIT_FIELDS = [
    "prediction_id",
    "split",
    "source_id",
    "scan_id",
    "subgraph_id",
    "subject_id",
    "object_id",
    "predicate_family",
    "candidate_role_hidden",
    "cell_id_hidden",
    "provisional_status_hidden",
    "anchor_bucket_hidden",
    "rank_band_hidden",
    "semantic_rank_hidden",
    "semantic_score_norm_hidden",
    "bucket_top100_hidden",
    "sampling_queue_hidden",
    "geometry_status_hidden",
    "reason_family_hidden",
    "machine_hint_hidden",
    "label_match_status_hidden",
    "matched_predicates_hidden",
    "directed_pair_id_hidden",
    "source_geometry_family_hidden",
    "source_geometry_predicate_hidden",
    "raw_feature_join_state_hidden",
    "attachment_witness_support_score_hidden",
    "attachment_witness_contradiction_score_hidden",
    "uncertainty_flags_hidden",
    "raw_features_hidden",
]

RISK_PREDICTORS = [
    "candidate_role_hidden",
    "cell_id_hidden",
    "provisional_status_hidden",
    "anchor_bucket_hidden",
    "rank_band_hidden",
    "bucket_top100_hidden",
    "sampling_queue_hidden",
    "geometry_status_hidden",
    "reason_family_hidden",
    "machine_hint_hidden",
    "label_match_status_hidden",
    "predicate_label",
    "relation_family_visible",
    "subject_object_visible_pair",
    "scan_id",
    "subject_label",
    "object_label",
    "geometry_witness_summary_v18",
    "attachment_witness_summary_v18",
    "uncertainty_summary_v18",
]

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 10,
    "large_group_purity": 0.90,
}

ALLOWED_PREDICATES = {"attached to", "hanging on", "connected to"}
ALLOWED_RELIABILITY_STATES = {
    "accept_reliable_attachment",
    "reject_unreliable_attachment",
    "diagnostic_connected_possible",
    "diagnostic_connected_ambiguous",
    "abstain_uncertain",
}
ALLOWED_GEOMETRY_SUPPORT_STATES = {"supports", "contradicts", "ambiguous", "not_evaluable"}
ALLOWED_USEFULNESS_STATES = {"useful_physical_relation", "diagnostic_only", "not_a_relation", "uncertain"}
ALLOWED_ENDPOINT_STATES = {"clear", "generic_or_structural_ambiguous", "wrong_direction_or_endpoint", "not_evaluable"}
ALLOWED_COVERAGE_STATES = {"sufficient", "limited", "missing", "not_evaluable"}

PRIMARY_BINARY_MAP = {
    "accept_reliable_attachment": 1,
    "reject_unreliable_attachment": 0,
}

GEOMETRY_SUPPORT_BINARY_MAP = {
    "supports": 1,
    "contradicts": 0,
}

USEFULNESS_BINARY_MAP = {
    "useful_physical_relation": 1,
    "not_a_relation": 0,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fill-summary", type=Path, default=DEFAULT_FILL_SUMMARY)
    parser.add_argument("--filled-sheet", type=Path, default=DEFAULT_FILLED_SHEET)
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


def semantic_rank_band(value: Any) -> str:
    try:
        rank = int(float(value))
    except (TypeError, ValueError):
        return "missing"
    if rank <= 50:
        return "top50"
    if rank <= 100:
        return "top100_only"
    if rank <= 200:
        return "rank_101_200"
    if rank <= 500:
        return "rank_201_500"
    if rank <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def validate_fill_summary(fill_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if fill_summary.get("status") != EXPECTED_FILL_STATUS:
        errors.append({"error_type": "unexpected_fill_status", "expected": EXPECTED_FILL_STATUS, "actual": fill_summary.get("status")})
    if fill_summary.get("next_todo") != EXPECTED_FILL_NEXT_TODO:
        errors.append({"error_type": "unexpected_fill_next_todo", "expected": EXPECTED_FILL_NEXT_TODO, "actual": fill_summary.get("next_todo")})
    if fill_summary.get("validation_errors") != 0:
        errors.append({"error_type": "fill_validation_errors_present", "actual": fill_summary.get("validation_errors")})
    boundary = fill_summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "hidden_audit_manifest_read",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "fill_boundary_violation", "key": key, "actual": boundary.get(key)})
    if boundary.get("visible_only_label_fill") is not True:
        errors.append({"error_type": "fill_boundary_violation", "key": "visible_only_label_fill", "actual": boundary.get("visible_only_label_fill")})
    if boundary.get("fills_new_labels") is not True:
        errors.append({"error_type": "fill_boundary_violation", "key": "fills_new_labels", "actual": boundary.get("fills_new_labels")})
    return errors


def validate_id_sets(label_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    label_ids = [str(row.get("blind_review_id") or "") for row in label_rows]
    manifest_ids = [str(row.get("blind_review_id") or "") for row in manifest_rows]
    for blind_id, count in Counter(label_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_filled_blind_review_id", "blind_review_id": blind_id, "count": count})
    for blind_id, count in Counter(manifest_ids).items():
        if blind_id and count > 1:
            errors.append({"error_type": "duplicate_manifest_blind_review_id", "blind_review_id": blind_id, "count": count})
    label_set = {blind_id for blind_id in label_ids if blind_id}
    manifest_set = {blind_id for blind_id in manifest_ids if blind_id}
    for blind_id in sorted(label_set - manifest_set):
        errors.append({"error_type": "filled_id_missing_from_manifest", "blind_review_id": blind_id})
    for blind_id in sorted(manifest_set - label_set):
        errors.append({"error_type": "manifest_id_missing_from_filled_sheet", "blind_review_id": blind_id})
    return errors


def validate_label_rows(fieldnames: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    required = [*VISIBLE_IDENTITY_FIELDS, *VISIBLE_CONTEXT_FIELDS, *COMPLETION_FIELDS]
    for field in required:
        if field not in fieldnames:
            errors.append({"error_type": "missing_filled_sheet_field", "field": field})
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id", "")
        reliability_state = row.get("relation_reliability_state_v18", "")
        geometry_state = row.get("geometry_support_state_v18", "")
        usefulness_state = row.get("relation_usefulness_state_v18", "")
        endpoint_state = row.get("endpoint_identity_state_v18", "")
        coverage_state = row.get("coverage_state_v18", "")
        if reliability_state not in ALLOWED_RELIABILITY_STATES:
            errors.append({"error_type": "invalid_reliability_state", "row_number": row_number, "blind_review_id": blind_id, "state": reliability_state})
        if geometry_state not in ALLOWED_GEOMETRY_SUPPORT_STATES:
            errors.append({"error_type": "invalid_geometry_support_state", "row_number": row_number, "blind_review_id": blind_id, "state": geometry_state})
        if usefulness_state not in ALLOWED_USEFULNESS_STATES:
            errors.append({"error_type": "invalid_usefulness_state", "row_number": row_number, "blind_review_id": blind_id, "state": usefulness_state})
        if endpoint_state not in ALLOWED_ENDPOINT_STATES:
            errors.append({"error_type": "invalid_endpoint_identity_state", "row_number": row_number, "blind_review_id": blind_id, "state": endpoint_state})
        if coverage_state not in ALLOWED_COVERAGE_STATES:
            errors.append({"error_type": "invalid_coverage_state", "row_number": row_number, "blind_review_id": blind_id, "state": coverage_state})
        if row.get("predicate_label") not in ALLOWED_PREDICATES:
            errors.append({"error_type": "unexpected_predicate", "row_number": row_number, "blind_review_id": blind_id, "predicate": row.get("predicate_label")})
        for field in COMPLETION_FIELDS:
            if not str(row.get(field, "")).strip() and field != "uncertainty_reason_v18":
                errors.append({"error_type": "missing_completion_field", "row_number": row_number, "blind_review_id": blind_id, "field": field})
    return errors


def validate_manifest_rows(manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(manifest_rows, start=1):
        blind_id = str(row.get("blind_review_id", ""))
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_manifest_row", "row_number": row_number, "blind_review_id": blind_id, "split": row.get("split")})
        if row.get("predicate_label") not in ALLOWED_PREDICATES:
            errors.append({"error_type": "unexpected_manifest_predicate", "row_number": row_number, "blind_review_id": blind_id, "predicate": row.get("predicate_label")})
        if row.get("predicate_family") != "attachment_deferred":
            errors.append({"error_type": "unexpected_manifest_family", "row_number": row_number, "blind_review_id": blind_id, "family": row.get("predicate_family")})
        if row.get("posterior_input_allowed") is not False:
            errors.append({"error_type": "posterior_input_allowed_not_false", "row_number": row_number, "blind_review_id": blind_id, "actual": row.get("posterior_input_allowed")})
        if row.get("model_input_allowed") is not False:
            errors.append({"error_type": "model_input_allowed_not_false", "row_number": row_number, "blind_review_id": blind_id, "actual": row.get("model_input_allowed")})
    return errors


def joined_rows(label_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest_by_id = {str(row["blind_review_id"]): dict(row) for row in manifest_rows}
    rows: list[dict[str, Any]] = []
    for label_row in label_rows:
        blind_id = str(label_row["blind_review_id"])
        manifest = manifest_by_id[blind_id]
        manifest.setdefault("rank_band_hidden", semantic_rank_band(manifest.get("semantic_rank_hidden")))
        subject_label = label_row.get("subject_label", "")
        object_label = label_row.get("object_label", "")
        reliability_state = label_row["relation_reliability_state_v18"]
        geometry_support_state = label_row["geometry_support_state_v18"]
        usefulness_state = label_row["relation_usefulness_state_v18"]
        primary_binary = PRIMARY_BINARY_MAP.get(reliability_state)
        geometry_support_binary = GEOMETRY_SUPPORT_BINARY_MAP.get(geometry_support_state)
        usefulness_binary = USEFULNESS_BINARY_MAP.get(usefulness_state)
        is_primary_scope = label_row.get("predicate_label") in {"attached to", "hanging on"}
        is_connected_diagnostic = label_row.get("predicate_label") == "connected to"
        row = {
            "schema_version": SCHEMA_VERSION,
            "label_source": LABEL_SOURCE,
            "blind_review_id": blind_id,
            "prediction_id": manifest.get("prediction_id"),
            "split": "train",
            "source_id": manifest.get("source_id"),
            "scan_id": manifest.get("scan_id"),
            "subgraph_id": manifest.get("subgraph_id"),
            "subject_id": manifest.get("subject_id"),
            "subject_label": subject_label,
            "predicate_label": label_row.get("predicate_label"),
            "predicate_family": manifest.get("predicate_family"),
            "object_id": manifest.get("object_id"),
            "object_label": object_label,
            "relation_family_visible": label_row.get("relation_family_visible"),
            "subject_object_visible_pair": f"{subject_label.strip().lower()}|{object_label.strip().lower()}",
            **{field: label_row.get(field) for field in VISIBLE_CONTEXT_FIELDS},
            "reviewer_id_v18": label_row.get("reviewer_id_v18"),
            "review_round_v18": label_row.get("review_round_v18"),
            "label_policy_v18": label_row.get("label_policy_v18"),
            "relation_reliability_state_v18": reliability_state,
            "relation_reliability_multiclass_target": reliability_state,
            "relation_reliability_binary_target": primary_binary,
            "relation_reliability_binary_usable": primary_binary is not None and is_primary_scope,
            "connected_diagnostic_target": reliability_state if is_connected_diagnostic else None,
            "connected_diagnostic_usable": is_connected_diagnostic,
            "geometry_support_state_v18": geometry_support_state,
            "geometry_support_binary_target": geometry_support_binary,
            "geometry_support_binary_usable": geometry_support_binary is not None,
            "relation_usefulness_state_v18": usefulness_state,
            "relation_usefulness_binary_target": usefulness_binary,
            "relation_usefulness_binary_usable": usefulness_binary is not None,
            "endpoint_identity_state_v18": label_row.get("endpoint_identity_state_v18"),
            "coverage_state_v18": label_row.get("coverage_state_v18"),
            "primary_reason_v18": label_row.get("primary_reason_v18"),
            "uncertainty_reason_v18": label_row.get("uncertainty_reason_v18"),
            "review_notes_v18": label_row.get("review_notes_v18"),
            **{field: manifest.get(field) for field in HIDDEN_AUDIT_FIELDS},
        }
        rows.append(row)
    return rows


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
    acc = correct / len(rows)
    nmi = normalized_mutual_information(rows, predictor, label)
    top_groups = []
    large_pure_group = False
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
        acc >= RISK_THRESHOLDS["majority_rule_accuracy"]
        and acc - baseline >= RISK_THRESHOLDS["majority_excess_over_baseline"]
    ) or nmi >= RISK_THRESHOLDS["normalized_mutual_information"] or large_pure_group
    return {
        "predictor": predictor,
        "label": label,
        "rows": len(rows),
        "groups": len(groups),
        "label_counts": dict(label_counts),
        "majority_rule_accuracy": acc,
        "majority_baseline_accuracy": baseline,
        "majority_excess_over_baseline": acc - baseline,
        "normalized_mutual_information": nmi,
        "risk_flag": risk_flag,
        "top_groups": top_groups[:12],
    }


def target_record(row: dict[str, Any], target_name: str, target_value: Any) -> dict[str, Any]:
    return {
        "blind_review_id": row["blind_review_id"],
        "prediction_id": row["prediction_id"],
        "split": row["split"],
        "target_name": target_name,
        "target_value": target_value,
        "label_source": LABEL_SOURCE,
        "predicate_family": row["predicate_family"],
        "predicate_label": row["predicate_label"],
        "candidate_role_hidden": row.get("candidate_role_hidden"),
        "cell_id_hidden": row.get("cell_id_hidden"),
    }


def target_rows(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    multiclass_rows = [
        target_record(row, MULTICLASS_TARGET, row["relation_reliability_multiclass_target"])
        for row in rows
    ]
    binary_rows = [
        target_record(row, BINARY_TARGET, row["relation_reliability_binary_target"])
        for row in rows
        if row["relation_reliability_binary_usable"]
    ]
    diagnostic_rows = [
        target_record(row, DIAGNOSTIC_TARGET, row["connected_diagnostic_target"])
        for row in rows
        if row["connected_diagnostic_usable"]
    ]
    geometry_support_rows = [
        target_record(row, GEOMETRY_SUPPORT_TARGET, row["geometry_support_binary_target"])
        for row in rows
        if row["geometry_support_binary_usable"]
    ]
    usefulness_rows = [
        target_record(row, USEFULNESS_TARGET, row["relation_usefulness_binary_target"])
        for row in rows
        if row["relation_usefulness_binary_usable"]
    ]
    endpoint_rows = [
        target_record(row, ENDPOINT_TARGET, row["endpoint_identity_state_v18"])
        for row in rows
    ]
    coverage_rows = [
        target_record(row, COVERAGE_TARGET, row["coverage_state_v18"])
        for row in rows
    ]
    abstain_rows = [
        {
            **target_record(row, BINARY_TARGET, None),
            "abstain_reason": row["uncertainty_reason_v18"] or row["primary_reason_v18"],
            "relation_reliability_state_v18": row["relation_reliability_state_v18"],
            "geometry_support_state_v18": row["geometry_support_state_v18"],
            "relation_usefulness_state_v18": row["relation_usefulness_state_v18"],
            "endpoint_identity_state_v18": row["endpoint_identity_state_v18"],
            "coverage_state_v18": row["coverage_state_v18"],
        }
        for row in rows
        if not row["relation_reliability_binary_usable"]
    ]
    return {
        "multiclass": multiclass_rows,
        "binary": binary_rows,
        "diagnostic_connected": diagnostic_rows,
        "geometry_support": geometry_support_rows,
        "usefulness": usefulness_rows,
        "endpoint": endpoint_rows,
        "coverage": coverage_rows,
        "abstain": abstain_rows,
    }


def probe_risks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    label_specs = [
        (rows, "relation_reliability_multiclass_target"),
        ([row for row in rows if row["relation_reliability_binary_usable"]], "relation_reliability_binary_target"),
        ([row for row in rows if row["geometry_support_binary_usable"]], "geometry_support_binary_target"),
        ([row for row in rows if row["relation_usefulness_binary_usable"]], "relation_usefulness_binary_target"),
        ([row for row in rows if row["connected_diagnostic_usable"]], "connected_diagnostic_target"),
        (rows, "endpoint_identity_state_v18"),
        (rows, "coverage_state_v18"),
    ]
    risks: list[dict[str, Any]] = []
    for label_rows, label in label_specs:
        for predictor in RISK_PREDICTORS:
            risks.append(majority_risk(label_rows, predictor, label))
    return risks


def group_contrast(rows: list[dict[str, Any]], group_field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(group_field, "missing"))].append(row)
    out: list[dict[str, Any]] = []
    for group_value, group_rows in grouped.items():
        relation_counts = Counter(row["relation_reliability_state_v18"] for row in group_rows)
        binary_values = {row["relation_reliability_binary_target"] for row in group_rows if row["relation_reliability_binary_usable"]}
        geometry_values = {row["geometry_support_binary_target"] for row in group_rows if row["geometry_support_binary_usable"]}
        usefulness_values = {row["relation_usefulness_binary_target"] for row in group_rows if row["relation_usefulness_binary_usable"]}
        endpoint_values = {row["endpoint_identity_state_v18"] for row in group_rows}
        out.append(
            {
                "group_field": group_field,
                "group_value": group_value,
                "rows": len(group_rows),
                "accept": relation_counts.get("accept_reliable_attachment", 0),
                "reject": relation_counts.get("reject_unreliable_attachment", 0),
                "abstain": relation_counts.get("abstain_uncertain", 0),
                "diagnostic_possible": relation_counts.get("diagnostic_connected_possible", 0),
                "diagnostic_ambiguous": relation_counts.get("diagnostic_connected_ambiguous", 0),
                "mixed_reliability_binary": len(binary_values) > 1,
                "mixed_geometry_support_binary": len(geometry_values) > 1,
                "mixed_usefulness_binary": len(usefulness_values) > 1,
                "mixed_endpoint_state": len(endpoint_values) > 1,
            }
        )
    out.sort(key=lambda item: (-item["rows"], str(item["group_value"])))
    return out


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    viability = summary["target_viability"]
    lines = [
        "# H002 V18 Attachment Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Result",
        "",
        "Ingested the locked v18 filled labels and joined hidden audit metadata by `blind_review_id`.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"multiclass_rows = {counts['multiclass_rows']}",
        f"binary_rows = {counts['binary_rows']}",
        f"diagnostic_connected_rows = {counts['diagnostic_connected_rows']}",
        f"abstain_rows = {counts['abstain_rows']}",
        f"geometry_support_rows = {counts['geometry_support_rows']}",
        f"usefulness_rows = {counts['usefulness_rows']}",
        f"endpoint_rows = {counts['endpoint_rows']}",
        f"coverage_rows = {counts['coverage_rows']}",
        f"relation_reliability_state_v18 = {counts['relation_reliability_state_v18']}",
        f"binary_target = {counts['binary_target']}",
        f"geometry_support_target = {counts['geometry_support_target']}",
        f"usefulness_target = {counts['usefulness_target']}",
        f"quick_probe_risk_flags = {counts['quick_probe_risk_flags']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Target Viability",
        "",
        "```text",
        f"minimum_per_class_for_posterior = {viability['minimum_per_class_for_posterior']}",
        f"reliability_positive_rows = {viability['reliability_positive_rows']}",
        f"reliability_negative_rows = {viability['reliability_negative_rows']}",
        f"class_mass_pass = {viability['class_mass_pass']}",
        f"same_cell_mixed_reliability_binary_groups = {viability['same_cell_mixed_reliability_binary_groups']}",
        f"same_visible_pair_mixed_reliability_binary_groups = {viability['same_visible_pair_mixed_reliability_binary_groups']}",
        f"same_predicate_mixed_reliability_binary_groups = {viability['same_predicate_mixed_reliability_binary_groups']}",
        "```",
        "",
        "The positive class is below the predeclared minimum class mass, so posterior smoke remains blocked even before the full target-independence audit.",
        "",
        "## Boundary",
        "",
        "Hidden audit metadata is read only after label lock for ingestion and shortcut audit. It is not a deployable model input.",
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
    hidden_manifest_path = as_abs(args.hidden_manifest)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fill_summary = read_json(fill_summary_path)
    fieldnames, label_rows = read_tsv(filled_sheet_path)
    manifest_rows = read_jsonl(hidden_manifest_path)

    validation_errors = validate_fill_summary(fill_summary)
    validation_errors.extend(validate_label_rows(fieldnames, label_rows))
    validation_errors.extend(validate_id_sets(label_rows, manifest_rows))
    validation_errors.extend(validate_manifest_rows(manifest_rows))

    rows = joined_rows(label_rows, manifest_rows) if not validation_errors else []
    targets = target_rows(rows)
    risks = probe_risks(rows)
    risk_flags = [risk for risk in risks if risk.get("risk_flag")]
    cell_contrast = group_contrast(rows, "cell_id_hidden")
    visible_pair_contrast = group_contrast(rows, "subject_object_visible_pair")
    predicate_contrast = group_contrast(rows, "predicate_label")
    family_contrast = group_contrast(rows, "predicate_family")
    role_contrast = group_contrast(rows, "candidate_role_hidden")

    state_counts = Counter(row["relation_reliability_state_v18"] for row in rows)
    geometry_support_counts = Counter(row["geometry_support_state_v18"] for row in rows)
    usefulness_counts = Counter(row["relation_usefulness_state_v18"] for row in rows)
    endpoint_counts = Counter(row["endpoint_identity_state_v18"] for row in rows)
    coverage_counts = Counter(row["coverage_state_v18"] for row in rows)
    binary_counts = Counter(str(row["relation_reliability_binary_target"]) for row in rows if row["relation_reliability_binary_usable"])
    geometry_binary_counts = Counter(str(row["geometry_support_binary_target"]) for row in rows if row["geometry_support_binary_usable"])
    usefulness_binary_counts = Counter(str(row["relation_usefulness_binary_target"]) for row in rows if row["relation_usefulness_binary_usable"])
    diagnostic_counts = Counter(str(row["connected_diagnostic_target"]) for row in rows if row["connected_diagnostic_usable"])
    reason_counts = Counter(row["primary_reason_v18"] for row in rows)
    uncertainty_counts = Counter(row["uncertainty_reason_v18"] for row in rows)
    label_match_counts = Counter(str(row.get("label_match_status_hidden")) for row in rows)
    machine_hint_counts = Counter(str(row.get("machine_hint_hidden")) for row in rows)
    rank_band_counts = Counter(str(row.get("rank_band_hidden")) for row in rows)
    bucket_counts = Counter(str(row.get("bucket_top100_hidden")) for row in rows)
    candidate_role_counts = Counter(str(row.get("candidate_role_hidden")) for row in rows)
    cell_counts = Counter(str(row.get("cell_id_hidden")) for row in rows)
    provisional_counts = Counter(str(row.get("provisional_status_hidden")) for row in rows)
    anchor_counts = Counter(str(row.get("anchor_bucket_hidden")) for row in rows)
    geometry_status_counts = Counter(str(row.get("geometry_status_hidden")) for row in rows)
    predicate_family_counts = Counter(str(row.get("predicate_family")) for row in rows)
    predicate_counts = Counter(str(row.get("predicate_label")) for row in rows)

    positive_rows = sum(1 for row in rows if row.get("relation_reliability_binary_target") == 1)
    negative_rows = sum(1 for row in rows if row.get("relation_reliability_binary_target") == 0)
    class_mass_pass = positive_rows >= MIN_CLASS_MASS_FOR_POSTERIOR and negative_rows >= MIN_CLASS_MASS_FOR_POSTERIOR
    same_cell_mixed = sum(1 for row in cell_contrast if row["mixed_reliability_binary"])
    same_pair_mixed = sum(1 for row in visible_pair_contrast if row["mixed_reliability_binary"])
    same_predicate_mixed = sum(1 for row in predicate_contrast if row["mixed_reliability_binary"])

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "ingested_rows": output_dir / "ingested_rows.jsonl",
        "multiclass_target": output_dir / "multiclass_target.jsonl",
        "binary_target": output_dir / "binary_target.jsonl",
        "diagnostic_connected_target": output_dir / "diagnostic_connected_target.jsonl",
        "geometry_support_target": output_dir / "geometry_support_target.jsonl",
        "usefulness_target": output_dir / "usefulness_target.jsonl",
        "endpoint_identity_target": output_dir / "endpoint_identity_target.jsonl",
        "coverage_target": output_dir / "coverage_target.jsonl",
        "abstain_rows": output_dir / "abstain_rows.jsonl",
        "quick_probe_risks": output_dir / "quick_probe_risks.json",
        "cell_contrast_summary": output_dir / "cell_contrast_summary.csv",
        "visible_pair_contrast_summary": output_dir / "visible_pair_contrast_summary.csv",
        "predicate_contrast_summary": output_dir / "predicate_contrast_summary.csv",
        "family_contrast_summary": output_dir / "family_contrast_summary.csv",
        "role_contrast_summary": output_dir / "role_contrast_summary.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    if validation_errors:
        status = "h002_reliability_target_v18_attachment_deferred_label_ingestion_errors"
    elif not class_mass_pass and risk_flags:
        status = "h002_reliability_target_v18_attachment_deferred_label_ingested_positive_sparse_with_probe_risk"
    elif not class_mass_pass:
        status = "h002_reliability_target_v18_attachment_deferred_label_ingested_positive_sparse"
    elif risk_flags:
        status = "h002_reliability_target_v18_attachment_deferred_label_ingested_with_probe_risk"
    else:
        status = "h002_reliability_target_v18_attachment_deferred_label_ingested_ready_for_independence_audit"

    posterior_allowed = False
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "fill_summary": rel_path(fill_summary_path),
            "filled_sheet": rel_path(filled_sheet_path),
            "hidden_manifest": rel_path(hidden_manifest_path),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": {
            "rows": len(rows),
            "multiclass_rows": len(targets["multiclass"]),
            "binary_rows": len(targets["binary"]),
            "diagnostic_connected_rows": len(targets["diagnostic_connected"]),
            "abstain_rows": len(targets["abstain"]),
            "geometry_support_rows": len(targets["geometry_support"]),
            "usefulness_rows": len(targets["usefulness"]),
            "endpoint_rows": len(targets["endpoint"]),
            "coverage_rows": len(targets["coverage"]),
            "relation_reliability_state_v18": dict(state_counts),
            "geometry_support_state_v18": dict(geometry_support_counts),
            "relation_usefulness_state_v18": dict(usefulness_counts),
            "endpoint_identity_state_v18": dict(endpoint_counts),
            "coverage_state_v18": dict(coverage_counts),
            "binary_target": dict(binary_counts),
            "geometry_support_target": dict(geometry_binary_counts),
            "usefulness_target": dict(usefulness_binary_counts),
            "diagnostic_connected_target": dict(diagnostic_counts),
            "primary_reason_v18": dict(reason_counts),
            "uncertainty_reason_v18": dict(uncertainty_counts),
            "label_match_status_hidden": dict(label_match_counts),
            "machine_hint_hidden": dict(machine_hint_counts),
            "rank_band_hidden": dict(rank_band_counts),
            "bucket_top100_hidden": dict(bucket_counts),
            "candidate_role_hidden": dict(candidate_role_counts),
            "cell_id_hidden": dict(cell_counts),
            "provisional_status_hidden": dict(provisional_counts),
            "anchor_bucket_hidden": dict(anchor_counts),
            "geometry_status_hidden": dict(geometry_status_counts),
            "predicate_family": dict(predicate_family_counts),
            "predicate_label": dict(predicate_counts),
            "cell_groups": len(cell_contrast),
            "visible_pair_groups": len(visible_pair_contrast),
            "predicate_groups": len(predicate_contrast),
            "family_groups": len(family_contrast),
            "role_groups": len(role_contrast),
            "quick_probe_risk_flags": len(risk_flags),
        },
        "target_viability": {
            "minimum_per_class_for_posterior": MIN_CLASS_MASS_FOR_POSTERIOR,
            "reliability_positive_rows": positive_rows,
            "reliability_negative_rows": negative_rows,
            "class_mass_pass": class_mass_pass,
            "same_cell_mixed_reliability_binary_groups": same_cell_mixed,
            "same_visible_pair_mixed_reliability_binary_groups": same_pair_mixed,
            "same_predicate_mixed_reliability_binary_groups": same_predicate_mixed,
            "posterior_smoke_allowed_after_ingestion": posterior_allowed,
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
            "reads_hidden_audit_manifest_after_label_lock": True,
            "hidden_fields_as_model_input": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": posterior_allowed,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_jsonl(output_paths["ingested_rows"], rows)
    write_jsonl(output_paths["multiclass_target"], targets["multiclass"])
    write_jsonl(output_paths["binary_target"], targets["binary"])
    write_jsonl(output_paths["diagnostic_connected_target"], targets["diagnostic_connected"])
    write_jsonl(output_paths["geometry_support_target"], targets["geometry_support"])
    write_jsonl(output_paths["usefulness_target"], targets["usefulness"])
    write_jsonl(output_paths["endpoint_identity_target"], targets["endpoint"])
    write_jsonl(output_paths["coverage_target"], targets["coverage"])
    write_jsonl(output_paths["abstain_rows"], targets["abstain"])
    write_json(output_paths["quick_probe_risks"], risks)
    write_csv(output_paths["cell_contrast_summary"], cell_contrast)
    write_csv(output_paths["visible_pair_contrast_summary"], visible_pair_contrast)
    write_csv(output_paths["predicate_contrast_summary"], predicate_contrast)
    write_csv(output_paths["family_contrast_summary"], family_contrast)
    write_csv(output_paths["role_contrast_summary"], role_contrast)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"multiclass_rows={summary['counts']['multiclass_rows']}")
    print(f"binary_rows={summary['counts']['binary_rows']}")
    print(f"diagnostic_connected_rows={summary['counts']['diagnostic_connected_rows']}")
    print(f"geometry_support_rows={summary['counts']['geometry_support_rows']}")
    print(f"usefulness_rows={summary['counts']['usefulness_rows']}")
    print(f"endpoint_rows={summary['counts']['endpoint_rows']}")
    print(f"coverage_rows={summary['counts']['coverage_rows']}")
    print(f"abstain_rows={summary['counts']['abstain_rows']}")
    print(f"positive_rows={summary['target_viability']['reliability_positive_rows']}")
    print(f"negative_rows={summary['target_viability']['reliability_negative_rows']}")
    print(f"class_mass_pass={summary['target_viability']['class_mass_pass']}")
    print(f"quick_probe_risk_flags={summary['counts']['quick_probe_risk_flags']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
