#!/usr/bin/env python3
"""Audit H002 v5 cell-contrast target independence."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_label_ingestion_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_target_independence_audit_codex_proxy_user_requested"

RELIABILITY_TARGET = "relation_reliability_v5_binary_target"
GEOMETRY_TARGET = "geometry_support_v5_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v5_binary_target"

TARGET_INPUTS = {
    RELIABILITY_TARGET: "relation_reliability_v5_posterior_candidates.jsonl",
    GEOMETRY_TARGET: "geometry_support_v5_posterior_candidates.jsonl",
    USEFULNESS_TARGET: "relation_usefulness_v5_posterior_candidates.jsonl",
}

TARGET_SCHEMA_VERSIONS = {
    RELIABILITY_TARGET: "h002_reliability_target_v5_cell_contrast_posterior_candidate_row_v1",
    GEOMETRY_TARGET: "h002_geometry_support_v5_cell_contrast_posterior_candidate_row_v1",
    USEFULNESS_TARGET: "h002_relation_usefulness_v5_cell_contrast_posterior_candidate_row_v1",
}

CELL_CONTRAST_KEYS = [
    "cell_contrast_role_hidden",
    "contrast_role_hidden",
    "cell_contrast_pair_id_hidden",
    "cell_contrast_level_hidden",
    "cell_contrast_key_hidden",
]

ENDPOINT_OBJECT_KEYS = [
    "endpoint_flag_pattern_hidden",
    "endpoint_family_cell_hidden",
    "subject_object_family_cell_hidden",
    "object_family_cell_hidden",
]

CONSTRUCTION_KEYS = [
    "source_queue_hidden",
    "queue_kind_hidden",
    "rank_band_hidden",
    "asset_packet_source_hidden",
    "row_gap_decision_hidden",
    "pair_gap_decision_hidden",
]

GEOMETRY_ALIGNMENT_KEYS = [
    "geometry_status_hidden",
    "h001_verification_status_hidden",
    "label_match_status_hidden",
    "label_match_family_hidden",
    "label_geometry_bucket_hidden",
]

VISIBLE_RELATION_KEYS = ["predicate_family", "predicate_label"]
VISIBLE_OBJECT_KEYS = ["subject_label", "object_label"]
VISIBLE_COVERAGE_KEYS = ["evidence_packet_status", "packet_gap_decision"]

RISK_NMI_THRESHOLD = 0.20
RISK_MAJORITY_EXCESS_THRESHOLD = 0.10
RISK_POSITIVE_RATE_RANGE_THRESHOLD = 0.70
RISK_LARGE_GROUP_ROWS = 10
RISK_LARGE_GROUP_PURITY = 0.95

MIN_STRICT_ROWS = 50
MIN_STRICT_PER_CLASS = 20
MIN_DIAGNOSTIC_ROWS = 30
MIN_DIAGNOSTIC_PER_CLASS = 10
MIN_CLASS_FOR_POSTERIOR = 20

SLICE_SPECS = {
    "original_cell_contrast_v5": {
        "balanced_keys": [],
        "reason": "full v5 cell-contrast target",
        "priority": 99,
    },
    "cell_role_balanced_v5": {
        "balanced_keys": ["cell_contrast_role_hidden"],
        "reason": "matched positives/negatives within hidden positive/negative proxy role",
        "priority": 1,
    },
    "source_queue_balanced_v5": {
        "balanced_keys": ["source_queue_hidden"],
        "reason": "matched positives/negatives within hidden HL/LH source queue",
        "priority": 2,
    },
    "geometry_status_balanced_v5": {
        "balanced_keys": ["geometry_status_hidden"],
        "reason": "matched positives/negatives within hidden geometry status",
        "priority": 3,
    },
    "rank_band_balanced_v5": {
        "balanced_keys": ["rank_band_hidden"],
        "reason": "matched positives/negatives within semantic rank band",
        "priority": 4,
    },
    "packet_source_balanced_v5": {
        "balanced_keys": ["asset_packet_source_hidden"],
        "reason": "matched positives/negatives within packet-source provenance",
        "priority": 5,
    },
    "family_balanced_v5": {
        "balanced_keys": ["predicate_family"],
        "reason": "matched positives/negatives within visible predicate family",
        "priority": 6,
    },
    "predicate_balanced_v5": {
        "balanced_keys": ["predicate_label"],
        "reason": "matched positives/negatives within visible predicate label",
        "priority": 7,
    },
    "subject_label_balanced_v5": {
        "balanced_keys": ["subject_label"],
        "reason": "matched positives/negatives within visible subject label",
        "priority": 8,
    },
    "object_label_balanced_v5": {
        "balanced_keys": ["object_label"],
        "reason": "matched positives/negatives within visible object label",
        "priority": 9,
    },
    "object_family_cell_balanced_v5": {
        "balanced_keys": ["object_family_cell_hidden"],
        "reason": "matched positives/negatives within hidden object-family cell",
        "priority": 10,
    },
    "endpoint_flag_pattern_balanced_v5": {
        "balanced_keys": ["endpoint_flag_pattern_hidden"],
        "reason": "matched positives/negatives within endpoint flag pattern",
        "priority": 11,
    },
    "subject_object_family_cell_balanced_v5": {
        "balanced_keys": ["subject_object_family_cell_hidden"],
        "reason": "matched positives/negatives within subject-object-family cell",
        "priority": 12,
    },
    "cell_key_balanced_v5": {
        "balanced_keys": ["cell_contrast_key_hidden"],
        "reason": "matched positives/negatives within strict cell-contrast key",
        "priority": 13,
    },
    "cell_pair_balanced_v5": {
        "balanced_keys": ["cell_contrast_pair_id_hidden"],
        "reason": "matched positives/negatives within exact pair id",
        "priority": 14,
    },
    "object_label_family_balanced_v5": {
        "balanced_keys": ["object_label", "predicate_family"],
        "reason": "matched positives/negatives within object label and predicate family",
        "priority": 15,
    },
    "endpoint_object_balanced_v5": {
        "balanced_keys": ["endpoint_flag_pattern_hidden", "object_label"],
        "reason": "matched positives/negatives within endpoint pattern and object label",
        "priority": 16,
    },
    "object_family_rank_balanced_v5": {
        "balanced_keys": ["object_family_cell_hidden", "rank_band_hidden"],
        "reason": "matched positives/negatives within object-family cell and rank band",
        "priority": 17,
    },
    "source_geometry_balanced_v5": {
        "balanced_keys": ["source_queue_hidden", "geometry_status_hidden"],
        "reason": "matched positives/negatives within source queue and geometry status",
        "priority": 18,
    },
    "role_object_family_balanced_v5": {
        "balanced_keys": ["cell_contrast_role_hidden", "object_family_cell_hidden"],
        "reason": "matched positives/negatives within cell role and object-family cell",
        "priority": 19,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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


def target_y(row: dict[str, Any]) -> int:
    return int(row["target_y"])


def group_value(row: dict[str, Any], key: str) -> str:
    if key in row:
        return str(row.get(key))
    hidden = row.get("hidden_audit_metadata_post_label_only", {})
    if key in hidden:
        return str(hidden.get(key))
    deployable = row.get("deployable_evidence_after_label_lock", {})
    for section in ["coverage_evidence", "semantic_evidence", "geometry_scalar_evidence"]:
        values = deployable.get(section, {})
        if key in values:
            return str(values.get(key))
    return "missing"


def semantic_rank(row: dict[str, Any]) -> float:
    value = row.get("hidden_audit_metadata_post_label_only", {}).get("semantic_rank_hidden")
    if value is None:
        value = row.get("deployable_evidence_after_label_lock", {}).get("semantic_evidence", {}).get("semantic_rank")
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1e12


def stable_key(row: dict[str, Any]) -> tuple[float, str]:
    return semantic_rank(row), str(row.get("prediction_id", row.get("blind_review_id", "")))


def entropy_from_counts(counts: Counter[Any]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        probability = count / total
        entropy -= probability * math.log2(probability)
    return entropy


def group_summary(
    rows: list[dict[str, Any]],
    group_key: str,
    source: str,
    risk_mode: str,
    target_name: str,
    slice_name: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[group_value(row, group_key)].append(row)

    total_counts = Counter(target_y(row) for row in rows)
    overall_entropy = entropy_from_counts(total_counts)
    majority_baseline = max(total_counts[0], total_counts[1]) / len(rows) if rows else 0.0
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    positive_rates: list[float] = []
    large_group_high_purity = False
    table: list[dict[str, Any]] = []

    for value, group_rows in sorted(grouped.items()):
        counts = Counter(target_y(row) for row in group_rows)
        positive = counts[1]
        negative = counts[0]
        total = positive + negative
        majority = max(positive, negative)
        majority_accuracy = majority / total if total else 0.0
        positive_rate = positive / total if total else 0.0
        group_entropy = entropy_from_counts(counts)
        if rows:
            weighted_conditional_entropy += total / len(rows) * group_entropy
        majority_correct += majority
        positive_rates.append(positive_rate)
        if total >= RISK_LARGE_GROUP_ROWS and majority_accuracy >= RISK_LARGE_GROUP_PURITY:
            large_group_high_purity = True
        table.append(
            {
                "target_name": target_name,
                "slice_name": slice_name,
                "risk_mode": risk_mode,
                "source": source,
                "group_key": group_key,
                "group_value": value,
                "rows": total,
                "positive": positive,
                "negative": negative,
                "positive_rate": positive_rate,
                "majority_label": 1 if positive >= negative else 0,
                "majority_accuracy": majority_accuracy,
                "entropy_bits": group_entropy,
            }
        )

    mutual_information = max(0.0, overall_entropy - weighted_conditional_entropy)
    nmi = mutual_information / overall_entropy if overall_entropy > 0 else 0.0
    positive_rate_range = max(positive_rates) - min(positive_rates) if positive_rates else 0.0
    majority_rule_accuracy = majority_correct / len(rows) if rows else 0.0
    majority_excess_over_baseline = majority_rule_accuracy - majority_baseline
    risk_flag = (
        nmi >= RISK_NMI_THRESHOLD
        or majority_excess_over_baseline >= RISK_MAJORITY_EXCESS_THRESHOLD
        or positive_rate_range >= RISK_POSITIVE_RATE_RANGE_THRESHOLD
        or large_group_high_purity
    )
    summary = {
        "target_name": target_name,
        "slice_name": slice_name,
        "risk_mode": risk_mode,
        "source": source,
        "group_key": group_key,
        "groups": len(grouped),
        "rows": len(rows),
        "overall_positive": total_counts[1],
        "overall_negative": total_counts[0],
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": weighted_conditional_entropy,
        "mutual_information_bits": mutual_information,
        "normalized_mutual_information": nmi,
        "majority_baseline": majority_baseline,
        "majority_rule_accuracy": majority_rule_accuracy,
        "majority_excess_over_baseline": majority_excess_over_baseline,
        "positive_rate_range": positive_rate_range,
        "large_group_high_purity": large_group_high_purity,
        "single_class_groups": sum(1 for item in table if item["positive"] == 0 or item["negative"] == 0),
        "minority_class_sparse": min(total_counts[1], total_counts[0]) < MIN_CLASS_FOR_POSTERIOR,
        "risk_flag": risk_flag,
    }
    return table, summary


def all_group_summaries(
    rows: list[dict[str, Any]],
    target_name: str,
    slice_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    key_groups = [
        ("cell_contrast_design", "hidden_post_label_audit", CELL_CONTRAST_KEYS),
        ("endpoint_object_structure", "hidden_post_label_audit", ENDPOINT_OBJECT_KEYS),
        ("construction", "hidden_post_label_audit", CONSTRUCTION_KEYS),
        ("expected_geometry_alignment", "hidden_post_label_audit", GEOMETRY_ALIGNMENT_KEYS),
        ("visible_relation_surface", "visible_non_target_surface", VISIBLE_RELATION_KEYS),
        ("visible_object_identity", "visible_non_target_surface", VISIBLE_OBJECT_KEYS),
        ("visible_coverage", "visible_non_target_surface", VISIBLE_COVERAGE_KEYS),
    ]
    group_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for risk_mode, source, keys in key_groups:
        for key in keys:
            table, summary = group_summary(rows, key, source, risk_mode, target_name, slice_name)
            group_rows.extend(table)
            summaries.append(summary)
    return group_rows, summaries


def risk_summaries(summaries: list[dict[str, Any]], risk_mode: str) -> list[dict[str, Any]]:
    risks = [summary for summary in summaries if summary["risk_mode"] == risk_mode and summary["risk_flag"]]
    return sorted(
        risks,
        key=lambda item: (
            -float(item["normalized_mutual_information"]),
            -float(item["majority_excess_over_baseline"]),
            -float(item["positive_rate_range"]),
        ),
    )


def clone_for_slice(row: dict[str, Any], target_name: str, slice_name: str, spec: dict[str, Any]) -> dict[str, Any]:
    copied = deepcopy(row)
    copied["target_name_for_audit"] = target_name
    copied["target_slice_name"] = slice_name
    copied["target_slice_reason"] = spec["reason"]
    copied["balanced_keys"] = spec["balanced_keys"]
    copied["audit_selection_only"] = True
    copied["paper_evidence_allowed"] = False
    return copied


def balanced_slice(rows: list[dict[str, Any]], target_name: str, slice_name: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    keys = list(spec["balanced_keys"])
    if not keys:
        return [clone_for_slice(row, target_name, slice_name, spec) for row in sorted(rows, key=stable_key)]

    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[tuple(group_value(row, key) for key in keys)].append(row)

    selected: list[dict[str, Any]] = []
    for _, group_rows in sorted(grouped.items()):
        positives = sorted([row for row in group_rows if target_y(row) == 1], key=stable_key)
        negatives = sorted([row for row in group_rows if target_y(row) == 0], key=stable_key)
        count = min(len(positives), len(negatives))
        selected.extend(clone_for_slice(row, target_name, slice_name, spec) for row in positives[:count])
        selected.extend(clone_for_slice(row, target_name, slice_name, spec) for row in negatives[:count])
    return sorted(selected, key=stable_key)


def counts_for(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(target_y(row) for row in rows)
    rows_count = len(rows)
    return {
        "rows": rows_count,
        "positive": counts[1],
        "negative": counts[0],
        "min_class": min(counts[1], counts[0]) if rows_count else 0,
        "positive_rate": counts[1] / rows_count if rows_count else 0.0,
        "majority_baseline": max(counts[1], counts[0]) / rows_count if rows_count else 0.0,
        "by_cell_role": dict(sorted(Counter(group_value(row, "cell_contrast_role_hidden") for row in rows).items())),
        "by_family": dict(sorted(Counter(group_value(row, "predicate_family") for row in rows).items())),
        "by_predicate": dict(sorted(Counter(group_value(row, "predicate_label") for row in rows).items())),
        "by_subject_label": dict(sorted(Counter(group_value(row, "subject_label") for row in rows).items())),
        "by_object_label": dict(sorted(Counter(group_value(row, "object_label") for row in rows).items())),
        "by_endpoint_pattern": dict(sorted(Counter(group_value(row, "endpoint_flag_pattern_hidden") for row in rows).items())),
        "by_rank_band": dict(sorted(Counter(group_value(row, "rank_band_hidden") for row in rows).items())),
        "by_geometry_status": dict(sorted(Counter(group_value(row, "geometry_status_hidden") for row in rows).items())),
        "by_label_geometry_bucket": dict(sorted(Counter(group_value(row, "label_geometry_bucket_hidden") for row in rows).items())),
        "by_object_family_cell": dict(sorted(Counter(group_value(row, "object_family_cell_hidden") for row in rows).items())),
        "by_subject_object_family_cell": dict(sorted(Counter(group_value(row, "subject_object_family_cell_hidden") for row in rows).items())),
    }


def top_risks(risks: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return [
        {
            "group_key": item["group_key"],
            "majority_baseline": item["majority_baseline"],
            "majority_rule_accuracy": item["majority_rule_accuracy"],
            "majority_excess_over_baseline": item["majority_excess_over_baseline"],
            "normalized_mutual_information": item["normalized_mutual_information"],
            "positive_rate_range": item["positive_rate_range"],
            "large_group_high_purity": item["large_group_high_purity"],
        }
        for item in risks[:limit]
    ]


def slice_summary(
    target_name: str,
    slice_name: str,
    spec: dict[str, Any],
    rows: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    path: Path,
) -> dict[str, Any]:
    counts = counts_for(rows)
    cell = risk_summaries(summaries, "cell_contrast_design")
    endpoint_object = risk_summaries(summaries, "endpoint_object_structure")
    construction = risk_summaries(summaries, "construction")
    geometry_alignment = risk_summaries(summaries, "expected_geometry_alignment")
    visible_relation = risk_summaries(summaries, "visible_relation_surface")
    visible_object = risk_summaries(summaries, "visible_object_identity")
    visible_coverage = risk_summaries(summaries, "visible_coverage")

    strict_size_ready = counts["rows"] >= MIN_STRICT_ROWS and counts["min_class"] >= MIN_STRICT_PER_CLASS
    diagnostic_size_ready = counts["rows"] >= MIN_DIAGNOSTIC_ROWS and counts["min_class"] >= MIN_DIAGNOSTIC_PER_CLASS
    minority_class_sparse = counts["min_class"] < MIN_CLASS_FOR_POSTERIOR

    strict_candidate = (
        strict_size_ready
        and not minority_class_sparse
        and not cell
        and not endpoint_object
        and not construction
        and not visible_object
    )
    diagnostic_candidate = (
        diagnostic_size_ready
        and not cell
        and not endpoint_object
        and not construction
        and not visible_object
    )
    geometry_axis_candidate = (
        diagnostic_size_ready
        and not cell
        and not endpoint_object
        and not construction
        and not visible_object
        and bool(geometry_alignment)
    )

    return {
        "target_name": target_name,
        "slice_name": slice_name,
        "path": rel_path(path),
        "balanced_keys": spec["balanced_keys"],
        "reason": spec["reason"],
        "priority": spec["priority"],
        "rows": counts["rows"],
        "positive": counts["positive"],
        "negative": counts["negative"],
        "min_class": counts["min_class"],
        "positive_rate": counts["positive_rate"],
        "majority_baseline": counts["majority_baseline"],
        "minority_class_sparse": minority_class_sparse,
        "strict_size_ready": strict_size_ready,
        "diagnostic_size_ready": diagnostic_size_ready,
        "cell_contrast_design_risk_count": len(cell),
        "endpoint_object_structure_risk_count": len(endpoint_object),
        "construction_risk_count": len(construction),
        "expected_geometry_alignment_risk_count": len(geometry_alignment),
        "visible_relation_surface_risk_count": len(visible_relation),
        "visible_object_identity_risk_count": len(visible_object),
        "visible_coverage_risk_count": len(visible_coverage),
        "strict_candidate": strict_candidate,
        "diagnostic_candidate": diagnostic_candidate,
        "geometry_axis_candidate": geometry_axis_candidate,
        "top_cell_contrast_design_risks": top_risks(cell),
        "top_endpoint_object_structure_risks": top_risks(endpoint_object),
        "top_construction_risks": top_risks(construction),
        "top_expected_geometry_alignment_risks": top_risks(geometry_alignment),
        "top_visible_relation_surface_risks": top_risks(visible_relation),
        "top_visible_object_identity_risks": top_risks(visible_object),
        "top_visible_coverage_risks": top_risks(visible_coverage),
        "counts": counts,
    }


def build_slices(
    target_name: str,
    rows: list[dict[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    slice_dir = output_dir / "target_slices" / target_name
    slice_summaries: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    group_summary_rows: list[dict[str, Any]] = []
    for slice_name, spec in SLICE_SPECS.items():
        slice_rows = balanced_slice(rows, target_name, slice_name, spec)
        path = slice_dir / f"{slice_name}.jsonl"
        write_jsonl(path, slice_rows)
        groups, summaries = all_group_summaries(slice_rows, target_name, slice_name)
        group_rows.extend(groups)
        group_summary_rows.extend(summaries)
        slice_summaries.append(slice_summary(target_name, slice_name, spec, slice_rows, summaries, path))
    return slice_summaries, group_rows, group_summary_rows


def choose_candidate(slice_summaries: list[dict[str, Any]], field: str) -> dict[str, Any] | None:
    candidates = [item for item in slice_summaries if item[field]]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item["priority"], -item["rows"], -item["min_class"]))[0]


def validate_ingestion_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_status = "h002_reliability_target_v5_cell_contrast_label_ingested_sparse_no_direct_pair_contrast_with_probe_risk"
    expected_next = "reliability_target_v5_cell_contrast_target_independence_audit"
    if summary.get("status") != expected_status:
        errors.append({"error_type": "unexpected_ingestion_status", "expected": expected_status, "actual": summary.get("status")})
    if summary.get("next_todo") != expected_next:
        errors.append({"error_type": "unexpected_ingestion_next_todo", "expected": expected_next, "actual": summary.get("next_todo")})
    boundary = summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "review_fields_as_model_input",
        "hidden_sampling_axes_as_model_input",
        "multi_view_as_model_input",
        "paper_evidence_allowed",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "unexpected_boundary_flag", "field": key, "expected": False, "actual": boundary.get(key)})
    if boundary.get("split") != "train_only":
        errors.append({"error_type": "unexpected_boundary_split", "expected": "train_only", "actual": boundary.get("split")})
    return errors


def validate_rows(target_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    seen = set()
    for index, row in enumerate(rows, start=1):
        blind_id = row.get("blind_review_id")
        if blind_id in seen:
            errors.append({"target_name": target_name, "error_type": "duplicate_blind_review_id", "row_number": index, "blind_review_id": blind_id})
        seen.add(blind_id)
        if row.get("target_name") != target_name:
            errors.append({"target_name": target_name, "error_type": "unexpected_target_name", "row_number": index, "blind_review_id": blind_id, "value": row.get("target_name")})
        expected_schema = TARGET_SCHEMA_VERSIONS[target_name]
        if row.get("schema_version") != expected_schema:
            errors.append({"target_name": target_name, "error_type": "unexpected_schema_version", "row_number": index, "blind_review_id": blind_id, "expected": expected_schema, "value": row.get("schema_version")})
        if row.get("predicate_family") not in {"support_contact", "relative_vertical"}:
            errors.append({"target_name": target_name, "error_type": "row_outside_support_vertical_scope", "row_number": index, "blind_review_id": blind_id, "predicate_family": row.get("predicate_family")})
        if row.get("actual_user_reviewer") is not False:
            errors.append({"target_name": target_name, "error_type": "unexpected_actual_user_reviewer", "row_number": index, "blind_review_id": blind_id, "value": row.get("actual_user_reviewer")})
        if row.get("filled_by") != "codex_proxy":
            errors.append({"target_name": target_name, "error_type": "unexpected_filled_by", "row_number": index, "blind_review_id": blind_id, "value": row.get("filled_by")})
        if row.get("audit_only_v5_review_fields", {}).get("not_model_input") is not True:
            errors.append({"target_name": target_name, "error_type": "v5_review_fields_not_audit_only", "row_number": index, "blind_review_id": blind_id})
        forbidden = row.get("deployable_evidence_after_label_lock", {}).get("forbidden_as_posterior_input", {})
        for key in [
            "v5_review_fields",
            "cell_contrast_role_hidden",
            "cell_contrast_pair_id_hidden",
            "cell_contrast_key_hidden",
            "source_queue_hidden",
            "geometry_status_hidden",
            "label_match_status_hidden",
            "rank_band_hidden",
            "endpoint_flag_pattern_hidden",
            "asset_packet_source_hidden",
            "audit_packet_paths",
            "multi_view_content",
        ]:
            if forbidden.get(key) is not True:
                errors.append({"target_name": target_name, "error_type": "missing_forbidden_flag", "field": key, "row_number": index, "blind_review_id": blind_id})
    return errors


def pair_diagnostic_from_ingestion(summary: dict[str, Any]) -> dict[str, Any]:
    pair = summary.get("pair_diagnostics", {})
    return {
        "pair_count": int(pair.get("pair_count", 0)),
        "direct_reliable_unreliable_contrast_pairs": int(pair.get("direct_reliable_unreliable_contrast_pairs", 0)),
        "pair_label_pattern_counts": pair.get("pair_label_pattern_counts", {}),
    }


def per_target_decision(
    target_name: str,
    summaries: list[dict[str, Any]],
    errors: list[dict[str, Any]],
    pair_diagnostic: dict[str, Any],
) -> dict[str, Any]:
    original = next(item for item in summaries if item["slice_name"] == "original_cell_contrast_v5")
    strict = choose_candidate(summaries, "strict_candidate")
    diagnostic = choose_candidate(summaries, "diagnostic_candidate")
    geometry_axis = choose_candidate(summaries, "geometry_axis_candidate")
    no_direct_pair_contrast = pair_diagnostic["direct_reliable_unreliable_contrast_pairs"] == 0
    if errors:
        status = "target_independence_audit_errors"
        decision = "Fix row validation errors before using v5 cell-contrast target slices."
        next_step = "fix_reliability_target_v5_cell_contrast_target_independence_errors"
    elif target_name == RELIABILITY_TARGET and original["minority_class_sparse"] and no_direct_pair_contrast:
        status = "blocked_sparse_no_direct_pair_contrast"
        decision = "The relation reliability target is minority-class sparse and has no direct reliable/unreliable pair contrast."
        next_step = "reliability_target_v5_cell_contrast_path_decision"
    elif original["minority_class_sparse"]:
        status = "blocked_minority_class_sparse"
        decision = "The target has too few minority-class rows for posterior use."
        next_step = "reliability_target_v5_cell_contrast_path_decision"
    elif strict:
        status = "strict_controlled_slice_ready"
        decision = "A strict controlled slice clears cell, endpoint/object, construction, and object-label shortcut checks."
        next_step = "reliability_target_v5_cell_contrast_source_feature_join"
    elif diagnostic:
        status = "diagnostic_slice_only"
        decision = "A diagnostic controlled slice remains, but it is not large enough for strict posterior smoke."
        next_step = "reliability_target_v5_cell_contrast_path_decision"
    elif geometry_axis:
        status = "geometry_axis_slice_only"
        decision = "Only a geometry-aligned diagnostic slice remains; this is not enough for a factorized reliability posterior claim."
        next_step = "reliability_target_v5_cell_contrast_path_decision"
    else:
        status = "blocked_no_controlled_slice"
        decision = "No strict or diagnostic controlled slice clears cell, endpoint/object, construction, and visible object shortcut risks."
        next_step = "reliability_target_v5_cell_contrast_path_decision"
    return {
        "target_name": target_name,
        "status": status,
        "decision": decision,
        "next_step": next_step,
        "original": original,
        "recommended_strict_slice": strict,
        "recommended_diagnostic_slice": diagnostic,
        "recommended_geometry_axis_slice": geometry_axis,
    }


def global_decision(target_decisions: dict[str, Any], errors: list[dict[str, Any]]) -> tuple[str, str, str]:
    if errors:
        return (
            "h002_reliability_target_v5_cell_contrast_target_independence_audit_errors",
            "Fix v5 target audit validation errors before any target decision.",
            "fix_reliability_target_v5_cell_contrast_target_independence_errors",
        )
    reliability = target_decisions[RELIABILITY_TARGET]
    if reliability["status"] == "strict_controlled_slice_ready":
        return (
            "h002_reliability_target_v5_cell_contrast_target_independence_audit_reliability_ready",
            "The main relation reliability target has a strict controlled slice; source feature join may be planned next.",
            "reliability_target_v5_cell_contrast_source_feature_join",
        )
    if reliability["status"] == "diagnostic_slice_only":
        return (
            "h002_reliability_target_v5_cell_contrast_target_independence_audit_diagnostic_only",
            "The main relation reliability target has only a diagnostic slice; posterior smoke remains blocked.",
            "reliability_target_v5_cell_contrast_path_decision",
        )
    return (
        "h002_reliability_target_v5_cell_contrast_target_independence_audit_blocked",
        (
            "The main relation reliability target is sparse, has no direct reliable/unreliable pair contrast, "
            "and no controlled slice clears cell, endpoint/object, construction, and visible object shortcut risks. "
            "Posterior smoke remains blocked."
        ),
        "reliability_target_v5_cell_contrast_path_decision",
    )


def risk_line(target_name: str, risk_mode: str, field: str, original: dict[str, Any]) -> list[str]:
    risks = original[field]
    if not risks:
        return [f"| `{target_name}` | `{risk_mode}` | none | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |"]
    lines = []
    for item in risks:
        lines.append(
            f"| `{target_name}` | `{risk_mode}` | `{item['group_key']}` | "
            f"{item['majority_baseline']:.4f} | "
            f"{item['majority_rule_accuracy']:.4f} | "
            f"{item['majority_excess_over_baseline']:.4f} | "
            f"{item['normalized_mutual_information']:.4f} | "
            f"{item['positive_rate_range']:.4f} |"
        )
    return lines


def write_report(path: Path, summary: dict[str, Any]) -> None:
    pair = summary["pair_diagnostics"]
    lines = [
        "# H002 Reliability Target V5 Cell Contrast Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage target audit.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- V5 labels are user-requested Codex proxy labels, not independent human annotation.",
        "- Hidden cell-contrast, construction, geometry-status, and packet metadata is used only after label lock for audit and slice construction.",
        "- V5 review fields, hidden sampling axes, audit packet paths, and multi-view evidence are not posterior inputs.",
        "- Posterior smoke is blocked unless the main relation reliability target has a strict controlled slice.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Pair Contrast",
        "",
        f"- pairs: `{pair['pair_count']}`",
        f"- direct reliable/unreliable pair contrast pairs: `{pair['direct_reliable_unreliable_contrast_pairs']}`",
        f"- pair label patterns: `{pair['pair_label_pattern_counts']}`",
        "",
        "## Per-Target Decisions",
        "",
        "| Target | Status | Rows | Pos | Neg | Strict Slice | Diagnostic Slice | Geometry-Axis Slice |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        strict = decision.get("recommended_strict_slice")
        diagnostic = decision.get("recommended_diagnostic_slice")
        geometry_axis = decision.get("recommended_geometry_axis_slice")
        lines.append(
            f"| `{target_name}` | `{decision['status']}` | {original['rows']} | {original['positive']} | {original['negative']} | "
            f"`{strict['slice_name'] if strict else 'none'}` | "
            f"`{diagnostic['slice_name'] if diagnostic else 'none'}` | "
            f"`{geometry_axis['slice_name'] if geometry_axis else 'none'}` |"
        )

    lines.extend(
        [
            "",
            "## Original Target Risks",
            "",
            "| Target | Risk Mode | Key | Majority Baseline | Majority Acc | Excess | NMI | Pos Rate Range |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    risk_fields = [
        ("cell_contrast_design", "top_cell_contrast_design_risks"),
        ("endpoint_object_structure", "top_endpoint_object_structure_risks"),
        ("construction", "top_construction_risks"),
        ("expected_geometry_alignment", "top_expected_geometry_alignment_risks"),
        ("visible_relation_surface", "top_visible_relation_surface_risks"),
        ("visible_object_identity", "top_visible_object_identity_risks"),
    ]
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        for risk_mode, field in risk_fields:
            lines.extend(risk_line(target_name, risk_mode, field, original))

    lines.extend(
        [
            "",
            "## Controlled Slices",
            "",
            "| Target | Slice | Rows | Pos | Neg | Cell | Endpoint/Object | Construction | Geometry Align | Object Risk | Strict | Diagnostic |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for item in sorted(
        summary["slice_summaries"],
        key=lambda row: (
            row["target_name"],
            not row["strict_candidate"],
            not row["diagnostic_candidate"],
            row["priority"],
            -row["rows"],
        ),
    ):
        lines.append(
            f"| `{item['target_name']}` | `{item['slice_name']}` | {item['rows']} | {item['positive']} | {item['negative']} | "
            f"{item['cell_contrast_design_risk_count']} | {item['endpoint_object_structure_risk_count']} | "
            f"{item['construction_risk_count']} | {item['expected_geometry_alignment_risk_count']} | "
            f"{item['visible_object_identity_risk_count']} | `{item['strict_candidate']}` | `{item['diagnostic_candidate']}` |"
        )
    lines.extend(["", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    ingestion_dir = as_abs(args.ingestion_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    ingestion_summary = read_json(ingestion_dir / "summary.json")
    pair_diagnostic = pair_diagnostic_from_ingestion(ingestion_summary)

    all_slice_summaries: list[dict[str, Any]] = []
    all_group_rows: list[dict[str, Any]] = []
    all_group_summaries: list[dict[str, Any]] = []
    all_validation_errors: list[dict[str, Any]] = validate_ingestion_summary(ingestion_summary)
    input_counts: dict[str, Any] = {}
    input_paths: dict[str, str] = {"ingestion_summary": rel_path(ingestion_dir / "summary.json")}
    target_decisions: dict[str, Any] = {}

    for target_name, filename in TARGET_INPUTS.items():
        path = ingestion_dir / filename
        rows = read_jsonl(path)
        input_paths[target_name] = rel_path(path)
        input_counts[target_name] = counts_for(rows)
        errors = validate_rows(target_name, rows)
        all_validation_errors.extend(errors)
        slice_summaries, group_rows, group_summary_rows = build_slices(target_name, rows, output_dir)
        all_slice_summaries.extend(slice_summaries)
        all_group_rows.extend(group_rows)
        all_group_summaries.extend(group_summary_rows)
        target_decisions[target_name] = per_target_decision(target_name, slice_summaries, errors, pair_diagnostic)

    status, decision, next_todo = global_decision(target_decisions, all_validation_errors)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "slice_summaries": output_dir / "slice_summaries.csv",
        "group_summaries": output_dir / "group_summaries.csv",
        "group_table": output_dir / "group_table.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    summary = {
        "schema_version": "h002_reliability_target_v5_cell_contrast_target_independence_audit_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "next_todo": next_todo,
        "input_paths": input_paths,
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": status.endswith("_reliability_ready"),
            "hidden_manifest_joined_after_label_lock": True,
            "review_fields_as_model_input": False,
            "hidden_sampling_axes_as_model_input": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
        },
        "risk_thresholds": {
            "risk_nmi_threshold": RISK_NMI_THRESHOLD,
            "risk_majority_excess_threshold": RISK_MAJORITY_EXCESS_THRESHOLD,
            "risk_positive_rate_range_threshold": RISK_POSITIVE_RATE_RANGE_THRESHOLD,
            "risk_large_group_rows": RISK_LARGE_GROUP_ROWS,
            "risk_large_group_purity": RISK_LARGE_GROUP_PURITY,
            "min_strict_rows": MIN_STRICT_ROWS,
            "min_strict_per_class": MIN_STRICT_PER_CLASS,
            "min_diagnostic_rows": MIN_DIAGNOSTIC_ROWS,
            "min_diagnostic_per_class": MIN_DIAGNOSTIC_PER_CLASS,
            "min_class_for_posterior": MIN_CLASS_FOR_POSTERIOR,
        },
        "input_counts": input_counts,
        "pair_diagnostics": pair_diagnostic,
        "ingestion_status": ingestion_summary.get("status"),
        "validation_errors": len(all_validation_errors),
        "target_decisions": target_decisions,
        "slice_summaries": all_slice_summaries,
    }

    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    write_csv(output_paths["slice_summaries"], all_slice_summaries)
    write_csv(output_paths["group_summaries"], all_group_summaries)
    write_csv(output_paths["group_table"], all_group_rows)
    write_jsonl(output_paths["validation_errors"], all_validation_errors)
    return summary


def main() -> int:
    summary = run(parse_args())
    reliability = summary["target_decisions"][RELIABILITY_TARGET]["original"]
    geometry = summary["target_decisions"][GEOMETRY_TARGET]["original"]
    usefulness = summary["target_decisions"][USEFULNESS_TARGET]["original"]
    print(
        "status={status} rel={rel_rows}/{rel_pos}/{rel_neg} rel_status={rel_status} "
        "geom={geom_rows}/{geom_pos}/{geom_neg} geom_status={geom_status} "
        "use={use_rows}/{use_pos}/{use_neg} use_status={use_status} "
        "direct_pair_contrast={direct_pair_contrast} errors={errors} "
        "posterior_allowed={posterior_allowed} validation_used={validation_used} "
        "test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            rel_rows=reliability["rows"],
            rel_pos=reliability["positive"],
            rel_neg=reliability["negative"],
            rel_status=summary["target_decisions"][RELIABILITY_TARGET]["status"],
            geom_rows=geometry["rows"],
            geom_pos=geometry["positive"],
            geom_neg=geometry["negative"],
            geom_status=summary["target_decisions"][GEOMETRY_TARGET]["status"],
            use_rows=usefulness["rows"],
            use_pos=usefulness["positive"],
            use_neg=usefulness["negative"],
            use_status=summary["target_decisions"][USEFULNESS_TARGET]["status"],
            direct_pair_contrast=summary["pair_diagnostics"]["direct_reliable_unreliable_contrast_pairs"],
            errors=summary["validation_errors"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
