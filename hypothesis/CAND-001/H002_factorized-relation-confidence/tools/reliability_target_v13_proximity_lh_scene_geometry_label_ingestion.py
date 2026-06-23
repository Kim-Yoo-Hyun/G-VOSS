#!/usr/bin/env python3
"""Ingest H002 v13 proximity scene/geometry labels and run quick target probes."""

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

FILL_DIR = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_label_fill"
CANDIDATE_DIR = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_candidate_mining"

DEFAULT_FILL_SUMMARY = FILL_DIR / "summary.json"
DEFAULT_FILLED_SHEET = FILL_DIR / "filled_label_sheet_v13.tsv"
DEFAULT_HIDDEN_MANIFEST = CANDIDATE_DIR / "hidden_audit_manifest_v13.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_label_ingestion"

SCHEMA_VERSION = "h002_reliability_target_v13_proximity_lh_scene_geometry_label_ingestion_v1"
EXPECTED_FILL_STATUS = "h002_reliability_target_v13_proximity_lh_scene_geometry_label_filled_codex_proxy_visible_only"
EXPECTED_FILL_NEXT_TODO = "reliability_target_v13_proximity_lh_scene_geometry_label_ingestion"
NEXT_TODO = "reliability_target_v13_proximity_lh_scene_geometry_target_independence_audit"

LABEL_SOURCE = "codex_proxy_v13_scene_geometry_visible_only_user_requested"
MIN_CLASS_MASS_FOR_POSTERIOR = 50

MULTICLASS_TARGET = "proximity_lh_scene_geometry_reliability_v13_multiclass"
BINARY_TARGET = "proximity_lh_scene_geometry_reliability_v13_binary"
GEOMETRY_SUPPORT_TARGET = "proximity_lh_scene_geometry_support_v13_binary"
USEFULNESS_TARGET = "proximity_lh_scene_usefulness_v13_binary"

COMPLETION_FIELDS = [
    "reviewer_id_v13",
    "review_round_v13",
    "label_policy_v13",
    "relation_reliability_state_v13",
    "scene_usefulness_state_v13",
    "primary_reason_v13",
    "uncertainty_reason_v13",
    "review_notes_v13",
]

VISIBLE_IDENTITY_FIELDS = [
    "blind_review_id",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
]

VISIBLE_CONTEXT_FIELDS = [
    "scene_context_summary_v13",
    "geometry_witness_summary_v13",
    "nearest_neighbor_context_v13",
    "local_density_context_v13",
    "duplicate_or_many_alternatives_context_v13",
    "crop_or_layout_evidence_v13",
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
    "source_queue_hidden",
    "semantic_rank_hidden",
    "semantic_score_norm_hidden",
    "p_geom_valid_hidden",
    "p_geom_bin_hidden",
    "geometry_status_hidden",
    "label_match_status_hidden",
    "label_geometry_bucket_hidden",
    "machine_hint_hidden",
    "rank_band_hidden",
    "subject_object_label_pair_hidden",
    "endpoint_cell_hidden",
    "target_construction_block_hidden",
    "raw_features_hidden",
]

RISK_PREDICTORS = [
    "label_match_status_hidden",
    "machine_hint_hidden",
    "rank_band_hidden",
    "p_geom_bin_hidden",
    "target_construction_block_hidden",
    "subject_object_label_pair_hidden",
    "endpoint_cell_hidden",
    "scan_id",
    "subject_label",
    "object_label",
    "subject_object_visible_pair",
    "scene_context_summary_v13",
    "geometry_witness_summary_v13",
    "nearest_neighbor_context_v13",
    "local_density_context_v13",
    "duplicate_or_many_alternatives_context_v13",
]

RISK_THRESHOLDS = {
    "majority_rule_accuracy": 0.85,
    "majority_excess_over_baseline": 0.10,
    "normalized_mutual_information": 0.20,
    "large_group_rows": 10,
    "large_group_purity": 0.90,
}

ALLOWED_RELIABILITY_STATES = {
    "accept_reliable_close_by",
    "reject_dense_relation_noise",
    "reject_trivial_or_context_only",
    "abstain_uncertain",
}

ALLOWED_USEFULNESS_STATES = {
    "useful_local_relation",
    "redundant_dense_neighborhood",
    "trivial_global_context",
    "not_evaluable",
}

RELIABILITY_BINARY_MAP = {
    "accept_reliable_close_by": 1,
    "reject_dense_relation_noise": 0,
    "reject_trivial_or_context_only": 0,
}

GEOMETRY_SUPPORT_STATE_MAP = {
    "accept_reliable_close_by": "geometry_supported_close_by",
    "reject_dense_relation_noise": "geometry_supported_but_dense",
    "reject_trivial_or_context_only": "geometry_weak_or_insufficient",
    "abstain_uncertain": "geometry_uncertain_or_not_evaluable",
}

GEOMETRY_SUPPORT_BINARY_MAP = {
    "accept_reliable_close_by": 1,
    "reject_dense_relation_noise": 1,
    "reject_trivial_or_context_only": 0,
}

USEFULNESS_BINARY_MAP = {
    "useful_local_relation": 1,
    "redundant_dense_neighborhood": 0,
    "trivial_global_context": 0,
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
        relation_state = row.get("relation_reliability_state_v13", "")
        usefulness_state = row.get("scene_usefulness_state_v13", "")
        if relation_state not in ALLOWED_RELIABILITY_STATES:
            errors.append({"error_type": "invalid_reliability_state", "row_number": row_number, "blind_review_id": blind_id, "state": relation_state})
        if usefulness_state not in ALLOWED_USEFULNESS_STATES:
            errors.append({"error_type": "invalid_usefulness_state", "row_number": row_number, "blind_review_id": blind_id, "state": usefulness_state})
        for field in COMPLETION_FIELDS:
            if not str(row.get(field, "")).strip() and field != "uncertainty_reason_v13":
                errors.append({"error_type": "missing_completion_field", "row_number": row_number, "blind_review_id": blind_id, "field": field})
        if row.get("predicate_label") != "close by":
            errors.append({"error_type": "unexpected_predicate", "row_number": row_number, "blind_review_id": blind_id, "predicate": row.get("predicate_label")})
    return errors


def validate_manifest_rows(manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(manifest_rows, start=1):
        blind_id = str(row.get("blind_review_id", ""))
        if row.get("split") != "train":
            errors.append({"error_type": "non_train_manifest_row", "row_number": row_number, "blind_review_id": blind_id, "split": row.get("split")})
        if row.get("predicate_label") != "close by":
            errors.append({"error_type": "non_close_by_manifest_row", "row_number": row_number, "blind_review_id": blind_id, "predicate": row.get("predicate_label")})
        if row.get("source_queue_hidden") != "RGA-LH":
            errors.append({"error_type": "unexpected_source_queue", "row_number": row_number, "blind_review_id": blind_id, "queue": row.get("source_queue_hidden")})
        if row.get("posterior_input_allowed") is not False:
            errors.append({"error_type": "posterior_input_allowed_not_false", "row_number": row_number, "blind_review_id": blind_id, "actual": row.get("posterior_input_allowed")})
        if row.get("model_input_allowed") is not False:
            errors.append({"error_type": "model_input_allowed_not_false", "row_number": row_number, "blind_review_id": blind_id, "actual": row.get("model_input_allowed")})
    return errors


def derive_geometry_support_state(reliability_state: str) -> str:
    return GEOMETRY_SUPPORT_STATE_MAP.get(reliability_state, "geometry_uncertain_or_not_evaluable")


def joined_rows(label_rows: list[dict[str, str]], manifest_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    manifest_by_id = {str(row["blind_review_id"]): row for row in manifest_rows}
    rows: list[dict[str, Any]] = []
    for label_row in label_rows:
        blind_id = str(label_row["blind_review_id"])
        manifest = manifest_by_id[blind_id]
        subject_label = label_row.get("subject_label", "")
        object_label = label_row.get("object_label", "")
        reliability_state = label_row["relation_reliability_state_v13"]
        usefulness_state = label_row["scene_usefulness_state_v13"]
        reliability_binary = RELIABILITY_BINARY_MAP.get(reliability_state)
        geometry_support_state = derive_geometry_support_state(reliability_state)
        geometry_support_binary = GEOMETRY_SUPPORT_BINARY_MAP.get(reliability_state)
        usefulness_binary = USEFULNESS_BINARY_MAP.get(usefulness_state)
        rows.append(
            {
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
                "subject_object_visible_pair": f"{subject_label.strip().lower()}|{object_label.strip().lower()}",
                **{field: label_row.get(field) for field in VISIBLE_CONTEXT_FIELDS},
                "reviewer_id_v13": label_row.get("reviewer_id_v13"),
                "review_round_v13": label_row.get("review_round_v13"),
                "label_policy_v13": label_row.get("label_policy_v13"),
                "relation_reliability_state_v13": reliability_state,
                "relation_reliability_multiclass_target": reliability_state,
                "relation_reliability_binary_target": reliability_binary,
                "relation_reliability_binary_usable": reliability_binary is not None,
                "scene_usefulness_state_v13": usefulness_state,
                "scene_usefulness_binary_target": usefulness_binary,
                "scene_usefulness_binary_usable": usefulness_binary is not None,
                "geometry_support_state_v13": geometry_support_state,
                "geometry_support_binary_target": geometry_support_binary,
                "geometry_support_binary_usable": geometry_support_binary is not None,
                "primary_reason_v13": label_row.get("primary_reason_v13"),
                "uncertainty_reason_v13": label_row.get("uncertainty_reason_v13"),
                "review_notes_v13": label_row.get("review_notes_v13"),
                **{field: manifest.get(field) for field in HIDDEN_AUDIT_FIELDS},
            }
        )
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
        "source_queue_hidden": row.get("source_queue_hidden"),
        "target_construction_block_hidden": row.get("target_construction_block_hidden"),
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
    geometry_support_rows = [
        target_record(row, GEOMETRY_SUPPORT_TARGET, row["geometry_support_binary_target"])
        for row in rows
        if row["geometry_support_binary_usable"]
    ]
    usefulness_rows = [
        target_record(row, USEFULNESS_TARGET, row["scene_usefulness_binary_target"])
        for row in rows
        if row["scene_usefulness_binary_usable"]
    ]
    abstain_rows = [
        {
            **target_record(row, BINARY_TARGET, None),
            "abstain_reason": row["uncertainty_reason_v13"] or row["primary_reason_v13"],
            "relation_reliability_state_v13": row["relation_reliability_state_v13"],
            "scene_usefulness_state_v13": row["scene_usefulness_state_v13"],
            "geometry_support_state_v13": row["geometry_support_state_v13"],
        }
        for row in rows
        if not row["relation_reliability_binary_usable"]
    ]
    return {
        "multiclass": multiclass_rows,
        "binary": binary_rows,
        "geometry_support": geometry_support_rows,
        "usefulness": usefulness_rows,
        "abstain": abstain_rows,
    }


def probe_risks(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    label_specs = [
        (rows, "relation_reliability_multiclass_target"),
        ([row for row in rows if row["relation_reliability_binary_usable"]], "relation_reliability_binary_target"),
        ([row for row in rows if row["geometry_support_binary_usable"]], "geometry_support_binary_target"),
        ([row for row in rows if row["scene_usefulness_binary_usable"]], "scene_usefulness_binary_target"),
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
        relation_counts = Counter(row["relation_reliability_state_v13"] for row in group_rows)
        binary_values = {row["relation_reliability_binary_target"] for row in group_rows if row["relation_reliability_binary_usable"]}
        geometry_values = {row["geometry_support_binary_target"] for row in group_rows if row["geometry_support_binary_usable"]}
        usefulness_values = {row["scene_usefulness_binary_target"] for row in group_rows if row["scene_usefulness_binary_usable"]}
        out.append(
            {
                "group_field": group_field,
                "group_value": group_value,
                "rows": len(group_rows),
                "accept": relation_counts.get("accept_reliable_close_by", 0),
                "reject_dense": relation_counts.get("reject_dense_relation_noise", 0),
                "reject_trivial": relation_counts.get("reject_trivial_or_context_only", 0),
                "abstain": relation_counts.get("abstain_uncertain", 0),
                "mixed_reliability_binary": len(binary_values) > 1,
                "mixed_geometry_support_binary": len(geometry_values) > 1,
                "mixed_usefulness_binary": len(usefulness_values) > 1,
            }
        )
    out.sort(key=lambda item: (-item["rows"], str(item["group_value"])))
    return out


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    viability = summary["target_viability"]
    lines = [
        "# H002 V13 Proximity Scene/Geometry Label Ingestion",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Result",
        "",
        "Ingested the locked v13 filled labels and joined hidden audit metadata by `blind_review_id`.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"multiclass_rows = {counts['multiclass_rows']}",
        f"binary_rows = {counts['binary_rows']}",
        f"abstain_rows = {counts['abstain_rows']}",
        f"geometry_support_rows = {counts['geometry_support_rows']}",
        f"usefulness_rows = {counts['usefulness_rows']}",
        f"relation_reliability_state_v13 = {counts['relation_reliability_state_v13']}",
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
        f"same_block_mixed_reliability_binary_groups = {viability['same_block_mixed_reliability_binary_groups']}",
        f"same_visible_pair_mixed_reliability_binary_groups = {viability['same_visible_pair_mixed_reliability_binary_groups']}",
        "```",
        "",
        "Positive mass is below the predeclared minimum class mass, so posterior smoke remains blocked even before the full target-independence audit.",
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
    block_contrast = group_contrast(rows, "target_construction_block_hidden")
    visible_pair_contrast = group_contrast(rows, "subject_object_visible_pair")

    state_counts = Counter(row["relation_reliability_state_v13"] for row in rows)
    usefulness_counts = Counter(row["scene_usefulness_state_v13"] for row in rows)
    geometry_support_counts = Counter(row["geometry_support_state_v13"] for row in rows)
    binary_counts = Counter(str(row["relation_reliability_binary_target"]) for row in rows if row["relation_reliability_binary_usable"])
    geometry_binary_counts = Counter(str(row["geometry_support_binary_target"]) for row in rows if row["geometry_support_binary_usable"])
    usefulness_binary_counts = Counter(str(row["scene_usefulness_binary_target"]) for row in rows if row["scene_usefulness_binary_usable"])
    reason_counts = Counter(row["primary_reason_v13"] for row in rows)
    uncertainty_counts = Counter(row["uncertainty_reason_v13"] for row in rows)
    label_match_counts = Counter(str(row.get("label_match_status_hidden")) for row in rows)
    machine_hint_counts = Counter(str(row.get("machine_hint_hidden")) for row in rows)
    rank_band_counts = Counter(str(row.get("rank_band_hidden")) for row in rows)
    p_geom_bin_counts = Counter(str(row.get("p_geom_bin_hidden")) for row in rows)

    positive_rows = sum(1 for row in rows if row.get("relation_reliability_binary_target") == 1)
    negative_rows = sum(1 for row in rows if row.get("relation_reliability_binary_target") == 0)
    class_mass_pass = positive_rows >= MIN_CLASS_MASS_FOR_POSTERIOR and negative_rows >= MIN_CLASS_MASS_FOR_POSTERIOR
    same_block_mixed = sum(1 for row in block_contrast if row["mixed_reliability_binary"])
    same_pair_mixed = sum(1 for row in visible_pair_contrast if row["mixed_reliability_binary"])

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "ingested_rows": output_dir / "ingested_rows.jsonl",
        "multiclass_target": output_dir / "multiclass_target.jsonl",
        "binary_target": output_dir / "binary_target.jsonl",
        "geometry_support_target": output_dir / "geometry_support_target.jsonl",
        "usefulness_target": output_dir / "usefulness_target.jsonl",
        "abstain_rows": output_dir / "abstain_rows.jsonl",
        "quick_probe_risks": output_dir / "quick_probe_risks.json",
        "block_contrast_summary": output_dir / "block_contrast_summary.csv",
        "visible_pair_contrast_summary": output_dir / "visible_pair_contrast_summary.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    if validation_errors:
        status = "h002_reliability_target_v13_proximity_lh_scene_geometry_label_ingestion_errors"
    elif not class_mass_pass and risk_flags:
        status = "h002_reliability_target_v13_proximity_lh_scene_geometry_label_ingested_positive_sparse_with_probe_risk"
    elif not class_mass_pass:
        status = "h002_reliability_target_v13_proximity_lh_scene_geometry_label_ingested_positive_sparse"
    elif risk_flags:
        status = "h002_reliability_target_v13_proximity_lh_scene_geometry_label_ingested_with_probe_risk"
    else:
        status = "h002_reliability_target_v13_proximity_lh_scene_geometry_label_ingested_ready_for_independence_audit"

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
            "abstain_rows": len(targets["abstain"]),
            "geometry_support_rows": len(targets["geometry_support"]),
            "usefulness_rows": len(targets["usefulness"]),
            "relation_reliability_state_v13": dict(state_counts),
            "scene_usefulness_state_v13": dict(usefulness_counts),
            "geometry_support_state_v13": dict(geometry_support_counts),
            "binary_target": dict(binary_counts),
            "geometry_support_target": dict(geometry_binary_counts),
            "usefulness_target": dict(usefulness_binary_counts),
            "primary_reason_v13": dict(reason_counts),
            "uncertainty_reason_v13": dict(uncertainty_counts),
            "label_match_status_hidden": dict(label_match_counts),
            "machine_hint_hidden": dict(machine_hint_counts),
            "rank_band_hidden": dict(rank_band_counts),
            "p_geom_bin_hidden": dict(p_geom_bin_counts),
            "target_construction_blocks": len(block_contrast),
            "visible_pair_groups": len(visible_pair_contrast),
            "quick_probe_risk_flags": len(risk_flags),
        },
        "target_viability": {
            "minimum_per_class_for_posterior": MIN_CLASS_MASS_FOR_POSTERIOR,
            "reliability_positive_rows": positive_rows,
            "reliability_negative_rows": negative_rows,
            "class_mass_pass": class_mass_pass,
            "same_block_mixed_reliability_binary_groups": same_block_mixed,
            "same_visible_pair_mixed_reliability_binary_groups": same_pair_mixed,
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
    write_jsonl(output_paths["geometry_support_target"], targets["geometry_support"])
    write_jsonl(output_paths["usefulness_target"], targets["usefulness"])
    write_jsonl(output_paths["abstain_rows"], targets["abstain"])
    write_json(output_paths["quick_probe_risks"], risks)
    write_csv(output_paths["block_contrast_summary"], block_contrast)
    write_csv(output_paths["visible_pair_contrast_summary"], visible_pair_contrast)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"binary_rows={summary['counts']['binary_rows']}")
    print(f"geometry_support_rows={summary['counts']['geometry_support_rows']}")
    print(f"usefulness_rows={summary['counts']['usefulness_rows']}")
    print(f"abstain_rows={summary['counts']['abstain_rows']}")
    print(f"positive_rows={summary['target_viability']['reliability_positive_rows']}")
    print(f"class_mass_pass={summary['target_viability']['class_mass_pass']}")
    print(f"quick_probe_risk_flags={summary['counts']['quick_probe_risk_flags']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
