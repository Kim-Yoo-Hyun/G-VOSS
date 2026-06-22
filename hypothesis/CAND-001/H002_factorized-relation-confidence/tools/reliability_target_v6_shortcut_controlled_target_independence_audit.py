#!/usr/bin/env python3
"""Audit H002 v6 shortcut-controlled target independence."""

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

DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v6_shortcut_controlled_label_ingestion_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v6_shortcut_controlled_target_independence_audit_codex_proxy_user_requested"

RELIABILITY_MULTICLASS = "relation_reliability_state_v6_multiclass_target"
RELIABILITY_BINARY = "relation_reliability_v6_binary_target"
GEOMETRY_TARGET = "geometry_support_v6_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v6_binary_target"

TARGET_INPUTS = {
    RELIABILITY_MULTICLASS: "relation_reliability_v6_multiclass_targets.jsonl",
    RELIABILITY_BINARY: "relation_reliability_v6_binary_targets.jsonl",
    GEOMETRY_TARGET: "geometry_support_v6_binary_targets.jsonl",
    USEFULNESS_TARGET: "relation_usefulness_v6_binary_targets.jsonl",
}

TARGET_SCHEMA_VERSIONS = {
    RELIABILITY_MULTICLASS: "h002_reliability_target_v6_shortcut_controlled_multiclass_row_v1",
    RELIABILITY_BINARY: "h002_reliability_target_v6_shortcut_controlled_binary_row_v1",
    GEOMETRY_TARGET: "h002_geometry_support_v6_shortcut_controlled_binary_row_v1",
    USEFULNESS_TARGET: "h002_relation_usefulness_v6_shortcut_controlled_binary_row_v1",
}

TARGET_CLASSES = {
    RELIABILITY_MULTICLASS: ["accept_reliable", "reject_unreliable", "abstain_uncertain"],
    RELIABILITY_BINARY: [0, 1],
    GEOMETRY_TARGET: [0, 1],
    USEFULNESS_TARGET: [0, 1],
}

HIDDEN_SAMPLING_KEYS = [
    "candidate_bucket_hidden",
    "semantic_band_hidden",
    "geometry_band_hidden",
    "coverage_bucket_hidden",
    "source_queue_hidden",
    "queue_kind_hidden",
    "rank_band_hidden",
]

ENDPOINT_OBJECT_KEYS = [
    "endpoint_flag_pattern_hidden",
    "object_family_cell_hidden",
    "subject_object_family_cell_hidden",
    "subject_object_label_pair_hidden",
]

GEOMETRY_ALIGNMENT_KEYS = [
    "geometry_status_hidden",
    "h001_verification_status_hidden",
    "label_match_status_hidden",
    "label_match_family_hidden",
    "label_geometry_bucket_hidden",
]

CONSTRUCTION_COVERAGE_KEYS = [
    "asset_packet_source_hidden",
    "row_gap_decision_hidden",
    "normalized_evidence_status_hidden",
    "evidence_packet_status",
    "packet_gap_decision",
]

HIDDEN_HINT_KEYS = ["machine_hint_hidden"]
VISIBLE_RELATION_KEYS = ["predicate_family", "predicate_label"]
VISIBLE_OBJECT_KEYS = ["subject_label", "object_label"]

RISK_NMI_THRESHOLD = 0.20
RISK_MAJORITY_EXCESS_THRESHOLD = 0.10
RISK_CLASS_RATE_RANGE_THRESHOLD = 0.70
RISK_LARGE_GROUP_ROWS = 10
RISK_LARGE_GROUP_PURITY = 0.95

MIN_STRICT_ROWS_BINARY = 50
MIN_STRICT_PER_CLASS_BINARY = 20
MIN_DIAGNOSTIC_ROWS_BINARY = 30
MIN_DIAGNOSTIC_PER_CLASS_BINARY = 10
MIN_STRICT_ROWS_MULTICLASS = 90
MIN_STRICT_PER_CLASS_MULTICLASS = 20
MIN_DIAGNOSTIC_ROWS_MULTICLASS = 45
MIN_DIAGNOSTIC_PER_CLASS_MULTICLASS = 10

SLICE_SPECS = {
    "original_v6": {
        "balanced_keys": [],
        "reason": "full v6 shortcut-controlled target",
        "priority": 99,
    },
    "family_balanced_v6": {
        "balanced_keys": ["predicate_family"],
        "reason": "balanced within predicate family",
        "priority": 1,
    },
    "candidate_bucket_balanced_v6": {
        "balanced_keys": ["candidate_bucket_hidden"],
        "reason": "balanced within semantic/geometry candidate bucket",
        "priority": 2,
    },
    "source_queue_balanced_v6": {
        "balanced_keys": ["source_queue_hidden"],
        "reason": "balanced within source queue",
        "priority": 3,
    },
    "rank_band_balanced_v6": {
        "balanced_keys": ["rank_band_hidden"],
        "reason": "balanced within semantic rank band",
        "priority": 4,
    },
    "geometry_status_balanced_v6": {
        "balanced_keys": ["geometry_status_hidden"],
        "reason": "balanced within geometry status",
        "priority": 5,
    },
    "semantic_geometry_band_balanced_v6": {
        "balanced_keys": ["semantic_band_hidden", "geometry_band_hidden"],
        "reason": "balanced within semantic/geometry evidence bands",
        "priority": 6,
    },
    "coverage_balanced_v6": {
        "balanced_keys": ["coverage_bucket_hidden"],
        "reason": "balanced within coverage bucket",
        "priority": 7,
    },
    "packet_status_balanced_v6": {
        "balanced_keys": ["evidence_packet_status"],
        "reason": "balanced within evidence packet status",
        "priority": 8,
    },
    "predicate_balanced_v6": {
        "balanced_keys": ["predicate_label"],
        "reason": "balanced within predicate label",
        "priority": 9,
    },
    "subject_label_balanced_v6": {
        "balanced_keys": ["subject_label"],
        "reason": "balanced within visible subject label",
        "priority": 10,
    },
    "object_label_balanced_v6": {
        "balanced_keys": ["object_label"],
        "reason": "balanced within visible object label",
        "priority": 11,
    },
    "object_family_cell_balanced_v6": {
        "balanced_keys": ["object_family_cell_hidden"],
        "reason": "balanced within object-family cell",
        "priority": 12,
    },
    "endpoint_flag_pattern_balanced_v6": {
        "balanced_keys": ["endpoint_flag_pattern_hidden"],
        "reason": "balanced within endpoint flag pattern",
        "priority": 13,
    },
    "subject_object_family_cell_balanced_v6": {
        "balanced_keys": ["subject_object_family_cell_hidden"],
        "reason": "balanced within subject-object-family cell",
        "priority": 14,
    },
    "subject_object_label_pair_balanced_v6": {
        "balanced_keys": ["subject_object_label_pair_hidden"],
        "reason": "balanced within subject/object label pair",
        "priority": 15,
    },
    "family_bucket_balanced_v6": {
        "balanced_keys": ["predicate_family", "candidate_bucket_hidden"],
        "reason": "balanced within family and candidate bucket",
        "priority": 16,
    },
    "family_geometry_status_balanced_v6": {
        "balanced_keys": ["predicate_family", "geometry_status_hidden"],
        "reason": "balanced within family and geometry status",
        "priority": 17,
    },
    "source_geometry_balanced_v6": {
        "balanced_keys": ["source_queue_hidden", "geometry_status_hidden"],
        "reason": "balanced within source queue and geometry status",
        "priority": 18,
    },
    "object_family_rank_balanced_v6": {
        "balanced_keys": ["object_family_cell_hidden", "rank_band_hidden"],
        "reason": "balanced within object-family cell and rank band",
        "priority": 19,
    },
    "endpoint_object_balanced_v6": {
        "balanced_keys": ["endpoint_flag_pattern_hidden", "object_label"],
        "reason": "balanced within endpoint pattern and visible object label",
        "priority": 20,
    },
    "machine_hint_balanced_v6": {
        "balanced_keys": ["machine_hint_hidden"],
        "reason": "diagnostic balance within hidden machine hint",
        "priority": 21,
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


def target_label(row: dict[str, Any]) -> Any:
    return row["target_y"]


def target_classes(target_name: str) -> list[Any]:
    return TARGET_CLASSES[target_name]


def group_value(row: dict[str, Any], key: str) -> str:
    return str(row.get(key, "missing"))


def semantic_rank(row: dict[str, Any]) -> float:
    value = row.get("semantic_rank_hidden")
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


def class_rate_range(group_counts: list[Counter[Any]], classes: list[Any]) -> float:
    if not group_counts:
        return 0.0
    max_range = 0.0
    for label in classes:
        rates: list[float] = []
        for counts in group_counts:
            total = sum(counts.values())
            rates.append((counts[label] / total) if total else 0.0)
        max_range = max(max_range, max(rates) - min(rates))
    return max_range


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

    classes = target_classes(target_name)
    total_counts = Counter(target_label(row) for row in rows)
    overall_entropy = entropy_from_counts(total_counts)
    majority_baseline = max(total_counts.values()) / len(rows) if rows else 0.0
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    large_group_high_purity = False
    per_group_counts: list[Counter[Any]] = []
    table: list[dict[str, Any]] = []

    for value, group_rows in sorted(grouped.items()):
        counts = Counter(target_label(row) for row in group_rows)
        total = sum(counts.values())
        majority_label, majority = max(counts.items(), key=lambda item: (item[1], str(item[0]))) if counts else ("", 0)
        majority_accuracy = majority / total if total else 0.0
        group_entropy = entropy_from_counts(counts)
        if rows:
            weighted_conditional_entropy += total / len(rows) * group_entropy
        majority_correct += majority
        per_group_counts.append(counts)
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
                "class_counts": json.dumps({str(label): counts[label] for label in classes}, sort_keys=True, ensure_ascii=False),
                "majority_label": majority_label,
                "majority_accuracy": majority_accuracy,
                "entropy_bits": group_entropy,
            }
        )

    mutual_information = max(0.0, overall_entropy - weighted_conditional_entropy)
    nmi = mutual_information / overall_entropy if overall_entropy > 0 else 0.0
    rate_range = class_rate_range(per_group_counts, classes)
    majority_rule_accuracy = majority_correct / len(rows) if rows else 0.0
    majority_excess_over_baseline = majority_rule_accuracy - majority_baseline
    risk_flag = (
        nmi >= RISK_NMI_THRESHOLD
        or majority_excess_over_baseline >= RISK_MAJORITY_EXCESS_THRESHOLD
        or rate_range >= RISK_CLASS_RATE_RANGE_THRESHOLD
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
        "class_counts": {str(label): total_counts[label] for label in classes},
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": weighted_conditional_entropy,
        "mutual_information_bits": mutual_information,
        "normalized_mutual_information": nmi,
        "majority_baseline": majority_baseline,
        "majority_rule_accuracy": majority_rule_accuracy,
        "majority_excess_over_baseline": majority_excess_over_baseline,
        "class_rate_range": rate_range,
        "large_group_high_purity": large_group_high_purity,
        "single_class_groups": sum(1 for item in table if sum(1 for v in json.loads(item["class_counts"]).values() if v > 0) <= 1),
        "risk_flag": risk_flag,
    }
    return table, summary


def all_group_summaries(
    rows: list[dict[str, Any]],
    target_name: str,
    slice_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    key_groups = [
        ("hidden_sampling_axis", "hidden_post_label_audit", HIDDEN_SAMPLING_KEYS),
        ("endpoint_object_structure", "hidden_post_label_audit", ENDPOINT_OBJECT_KEYS),
        ("geometry_alignment", "hidden_post_label_audit", GEOMETRY_ALIGNMENT_KEYS),
        ("construction_coverage", "hidden_post_label_audit", CONSTRUCTION_COVERAGE_KEYS),
        ("hidden_machine_hint", "hidden_post_label_audit", HIDDEN_HINT_KEYS),
        ("visible_relation_surface", "visible_non_target_surface", VISIBLE_RELATION_KEYS),
        ("visible_object_identity", "visible_non_target_surface", VISIBLE_OBJECT_KEYS),
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
            -float(item["class_rate_range"]),
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

    classes = target_classes(target_name)
    selected: list[dict[str, Any]] = []
    for _, group_rows in sorted(grouped.items()):
        by_class: dict[Any, list[dict[str, Any]]] = {
            label: sorted([row for row in group_rows if target_label(row) == label], key=stable_key)
            for label in classes
        }
        count = min(len(by_class[label]) for label in classes)
        if count <= 0:
            continue
        for label in classes:
            selected.extend(clone_for_slice(row, target_name, slice_name, spec) for row in by_class[label][:count])
    return sorted(selected, key=stable_key)


def counts_for(rows: list[dict[str, Any]], target_name: str) -> dict[str, Any]:
    classes = target_classes(target_name)
    counts = Counter(target_label(row) for row in rows)
    rows_count = len(rows)
    min_class = min((counts[label] for label in classes), default=0) if rows_count else 0
    return {
        "rows": rows_count,
        "class_counts": {str(label): counts[label] for label in classes},
        "min_class": min_class,
        "majority_baseline": (max(counts[label] for label in classes) / rows_count) if rows_count else 0.0,
        "by_family": dict(sorted(Counter(group_value(row, "predicate_family") for row in rows).items())),
        "by_predicate": dict(sorted(Counter(group_value(row, "predicate_label") for row in rows).items())),
        "by_subject_label": dict(sorted(Counter(group_value(row, "subject_label") for row in rows).items())),
        "by_object_label": dict(sorted(Counter(group_value(row, "object_label") for row in rows).items())),
        "by_candidate_bucket": dict(sorted(Counter(group_value(row, "candidate_bucket_hidden") for row in rows).items())),
        "by_source_queue": dict(sorted(Counter(group_value(row, "source_queue_hidden") for row in rows).items())),
        "by_geometry_status": dict(sorted(Counter(group_value(row, "geometry_status_hidden") for row in rows).items())),
        "by_object_family_cell": dict(sorted(Counter(group_value(row, "object_family_cell_hidden") for row in rows).items())),
        "by_subject_object_family_cell": dict(sorted(Counter(group_value(row, "subject_object_family_cell_hidden") for row in rows).items())),
    }


def binary_counts_for_report(counts: dict[str, Any]) -> tuple[int, int]:
    class_counts = counts["class_counts"]
    return int(class_counts.get("1", 0)), int(class_counts.get("0", 0))


def top_risks(risks: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return [
        {
            "group_key": item["group_key"],
            "majority_baseline": item["majority_baseline"],
            "majority_rule_accuracy": item["majority_rule_accuracy"],
            "majority_excess_over_baseline": item["majority_excess_over_baseline"],
            "normalized_mutual_information": item["normalized_mutual_information"],
            "class_rate_range": item["class_rate_range"],
            "large_group_high_purity": item["large_group_high_purity"],
        }
        for item in risks[:limit]
    ]


def min_sizes(target_name: str) -> tuple[int, int, int, int]:
    if target_name == RELIABILITY_MULTICLASS:
        return (
            MIN_STRICT_ROWS_MULTICLASS,
            MIN_STRICT_PER_CLASS_MULTICLASS,
            MIN_DIAGNOSTIC_ROWS_MULTICLASS,
            MIN_DIAGNOSTIC_PER_CLASS_MULTICLASS,
        )
    return (
        MIN_STRICT_ROWS_BINARY,
        MIN_STRICT_PER_CLASS_BINARY,
        MIN_DIAGNOSTIC_ROWS_BINARY,
        MIN_DIAGNOSTIC_PER_CLASS_BINARY,
    )


def slice_summary(
    target_name: str,
    slice_name: str,
    spec: dict[str, Any],
    rows: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    path: Path,
) -> dict[str, Any]:
    counts = counts_for(rows, target_name)
    hidden_sampling = risk_summaries(summaries, "hidden_sampling_axis")
    endpoint_object = risk_summaries(summaries, "endpoint_object_structure")
    geometry_alignment = risk_summaries(summaries, "geometry_alignment")
    construction_coverage = risk_summaries(summaries, "construction_coverage")
    hidden_hint = risk_summaries(summaries, "hidden_machine_hint")
    visible_relation = risk_summaries(summaries, "visible_relation_surface")
    visible_object = risk_summaries(summaries, "visible_object_identity")

    min_strict_rows, min_strict_class, min_diag_rows, min_diag_class = min_sizes(target_name)
    strict_size_ready = counts["rows"] >= min_strict_rows and counts["min_class"] >= min_strict_class
    diagnostic_size_ready = counts["rows"] >= min_diag_rows and counts["min_class"] >= min_diag_class
    blocking_risk = bool(hidden_sampling or endpoint_object or geometry_alignment or construction_coverage or hidden_hint or visible_object)
    label_surface_only_risk = bool(visible_relation) and not blocking_risk

    strict_candidate = strict_size_ready and not blocking_risk
    diagnostic_candidate = diagnostic_size_ready and not blocking_risk
    label_surface_only_candidate = diagnostic_size_ready and label_surface_only_risk

    return {
        "target_name": target_name,
        "slice_name": slice_name,
        "path": rel_path(path),
        "balanced_keys": spec["balanced_keys"],
        "reason": spec["reason"],
        "priority": spec["priority"],
        "rows": counts["rows"],
        "class_counts": counts["class_counts"],
        "min_class": counts["min_class"],
        "majority_baseline": counts["majority_baseline"],
        "strict_size_ready": strict_size_ready,
        "diagnostic_size_ready": diagnostic_size_ready,
        "hidden_sampling_axis_risk_count": len(hidden_sampling),
        "endpoint_object_structure_risk_count": len(endpoint_object),
        "geometry_alignment_risk_count": len(geometry_alignment),
        "construction_coverage_risk_count": len(construction_coverage),
        "hidden_machine_hint_risk_count": len(hidden_hint),
        "visible_relation_surface_risk_count": len(visible_relation),
        "visible_object_identity_risk_count": len(visible_object),
        "blocking_risk": blocking_risk,
        "strict_candidate": strict_candidate,
        "diagnostic_candidate": diagnostic_candidate,
        "label_surface_only_candidate": label_surface_only_candidate,
        "top_hidden_sampling_axis_risks": top_risks(hidden_sampling),
        "top_endpoint_object_structure_risks": top_risks(endpoint_object),
        "top_geometry_alignment_risks": top_risks(geometry_alignment),
        "top_construction_coverage_risks": top_risks(construction_coverage),
        "top_hidden_machine_hint_risks": top_risks(hidden_hint),
        "top_visible_relation_surface_risks": top_risks(visible_relation),
        "top_visible_object_identity_risks": top_risks(visible_object),
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
    expected_status = "h002_reliability_target_v6_shortcut_controlled_label_ingested_with_probe_risk"
    expected_next = "reliability_target_v6_shortcut_controlled_target_independence_audit"
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
    expected_schema = TARGET_SCHEMA_VERSIONS[target_name]
    expected_classes = set(target_classes(target_name))
    for index, row in enumerate(rows, start=1):
        blind_id = row.get("blind_review_id")
        if blind_id in seen:
            errors.append({"target_name": target_name, "error_type": "duplicate_blind_review_id", "row_number": index, "blind_review_id": blind_id})
        seen.add(blind_id)
        if row.get("target_name") != target_name:
            errors.append({"target_name": target_name, "error_type": "unexpected_target_name", "row_number": index, "blind_review_id": blind_id, "value": row.get("target_name")})
        if row.get("schema_version") != expected_schema:
            errors.append({"target_name": target_name, "error_type": "unexpected_schema_version", "row_number": index, "blind_review_id": blind_id, "expected": expected_schema, "value": row.get("schema_version")})
        if row.get("target_y") not in expected_classes:
            errors.append({"target_name": target_name, "error_type": "unexpected_target_y", "row_number": index, "blind_review_id": blind_id, "value": row.get("target_y")})
        if row.get("predicate_family") not in {"support_contact", "relative_vertical"}:
            errors.append({"target_name": target_name, "error_type": "row_outside_support_vertical_scope", "row_number": index, "blind_review_id": blind_id, "predicate_family": row.get("predicate_family")})
        if row.get("actual_user_reviewer") is not False:
            errors.append({"target_name": target_name, "error_type": "unexpected_actual_user_reviewer", "row_number": index, "blind_review_id": blind_id, "value": row.get("actual_user_reviewer")})
        if row.get("filled_by") != "codex_proxy":
            errors.append({"target_name": target_name, "error_type": "unexpected_filled_by", "row_number": index, "blind_review_id": blind_id, "value": row.get("filled_by")})
        if row.get("paper_locked") is not False:
            errors.append({"target_name": target_name, "error_type": "unexpected_paper_locked", "row_number": index, "blind_review_id": blind_id, "value": row.get("paper_locked")})
    return errors


def per_target_decision(target_name: str, summaries: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    original = next(item for item in summaries if item["slice_name"] == "original_v6")
    strict = choose_candidate(summaries, "strict_candidate")
    diagnostic = choose_candidate(summaries, "diagnostic_candidate")
    label_surface_only = choose_candidate(summaries, "label_surface_only_candidate")
    if errors:
        status = "target_independence_audit_errors"
        decision = "Fix row validation errors before using v6 shortcut-controlled target slices."
        next_step = "fix_reliability_target_v6_shortcut_controlled_target_independence_errors"
    elif strict:
        status = "strict_controlled_slice_ready"
        decision = "A strict controlled slice clears sampling, object/category, geometry-status, construction, and visible-object shortcut checks."
        next_step = "reliability_target_v6_shortcut_controlled_source_feature_join"
    elif diagnostic:
        status = "diagnostic_slice_only"
        decision = "A diagnostic controlled slice remains, but it is not large enough for strict posterior smoke."
        next_step = "reliability_target_v6_shortcut_controlled_path_decision"
    elif label_surface_only:
        status = "label_surface_only_slice"
        decision = "Only label-surface dependency remains in a diagnostic slice; this is not enough for main posterior evidence."
        next_step = "reliability_target_v6_shortcut_controlled_path_decision"
    elif original["min_class"] < min_sizes(target_name)[1]:
        status = "blocked_minority_class_sparse"
        decision = "The target has too few rows in at least one class for strict posterior use."
        next_step = "reliability_target_v6_shortcut_controlled_path_decision"
    else:
        status = "blocked_shortcut_risk"
        decision = "No strict or diagnostic controlled slice clears object/category, sampling, geometry-status, construction, and visible-object shortcut risks."
        next_step = "reliability_target_v6_shortcut_controlled_path_decision"
    return {
        "target_name": target_name,
        "status": status,
        "decision": decision,
        "next_step": next_step,
        "original": original,
        "recommended_strict_slice": strict,
        "recommended_diagnostic_slice": diagnostic,
        "recommended_label_surface_only_slice": label_surface_only,
    }


def global_decision(target_decisions: dict[str, Any], errors: list[dict[str, Any]]) -> tuple[str, str, str]:
    if errors:
        return (
            "h002_reliability_target_v6_shortcut_controlled_target_independence_audit_errors",
            "Fix v6 target audit validation errors before any target decision.",
            "fix_reliability_target_v6_shortcut_controlled_target_independence_errors",
        )
    multiclass = target_decisions[RELIABILITY_MULTICLASS]
    binary = target_decisions[RELIABILITY_BINARY]
    if multiclass["status"] == "strict_controlled_slice_ready":
        return (
            "h002_reliability_target_v6_shortcut_controlled_target_independence_audit_multiclass_reliability_ready",
            "The primary multiclass relation reliability target has a strict controlled slice; source feature join may be planned next.",
            "reliability_target_v6_shortcut_controlled_source_feature_join",
        )
    if binary["status"] == "strict_controlled_slice_ready":
        return (
            "h002_reliability_target_v6_shortcut_controlled_target_independence_audit_binary_only",
            "Only the binary diagnostic relation reliability target has a strict slice; primary multiclass evidence remains blocked.",
            "reliability_target_v6_shortcut_controlled_path_decision",
        )
    return (
        "h002_reliability_target_v6_shortcut_controlled_target_independence_audit_blocked_shortcut_risk",
        (
            "The v6 targets have usable class mass, but no controlled slice clears the main shortcut risks. "
            "Posterior smoke remains blocked; decide whether to resample, relabel, or change target construction."
        ),
        "reliability_target_v6_shortcut_controlled_path_decision",
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
            f"{item['class_rate_range']:.4f} |"
        )
    return lines


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Reliability Target V6 Shortcut-Controlled Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage target audit.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- V6 labels are user-requested Codex proxy labels, not independent human annotation.",
        "- Hidden sampling/object/geometry/coverage metadata is used only after label lock for audit and slice construction.",
        "- Review labels, hidden sampling axes, audit packet paths, and multi-view evidence are not posterior inputs.",
        "- Posterior smoke is blocked unless the primary relation reliability target has a strict controlled slice.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Per-Target Decisions",
        "",
        "| Target | Status | Rows | Min Class | Class Counts | Strict Slice | Diagnostic Slice | Label-Surface Slice |",
        "| --- | --- | ---: | ---: | --- | --- | --- | --- |",
    ]
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        strict = decision.get("recommended_strict_slice")
        diagnostic = decision.get("recommended_diagnostic_slice")
        label_surface = decision.get("recommended_label_surface_only_slice")
        lines.append(
            f"| `{target_name}` | `{decision['status']}` | {original['rows']} | {original['min_class']} | "
            f"`{original['class_counts']}` | "
            f"`{strict['slice_name'] if strict else 'none'}` | "
            f"`{diagnostic['slice_name'] if diagnostic else 'none'}` | "
            f"`{label_surface['slice_name'] if label_surface else 'none'}` |"
        )

    lines.extend(
        [
            "",
            "## Original Target Risks",
            "",
            "| Target | Risk Mode | Key | Majority Baseline | Majority Acc | Excess | NMI | Class Rate Range |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    risk_fields = [
        ("hidden_sampling_axis", "top_hidden_sampling_axis_risks"),
        ("endpoint_object_structure", "top_endpoint_object_structure_risks"),
        ("geometry_alignment", "top_geometry_alignment_risks"),
        ("construction_coverage", "top_construction_coverage_risks"),
        ("hidden_machine_hint", "top_hidden_machine_hint_risks"),
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
            "| Target | Slice | Rows | Min Class | Hidden Sampling | Endpoint/Object | Geometry | Construction | Machine Hint | Object Risk | Strict | Diagnostic |",
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
            f"| `{item['target_name']}` | `{item['slice_name']}` | {item['rows']} | {item['min_class']} | "
            f"{item['hidden_sampling_axis_risk_count']} | {item['endpoint_object_structure_risk_count']} | "
            f"{item['geometry_alignment_risk_count']} | {item['construction_coverage_risk_count']} | "
            f"{item['hidden_machine_hint_risk_count']} | {item['visible_object_identity_risk_count']} | "
            f"`{item['strict_candidate']}` | `{item['diagnostic_candidate']}` |"
        )
    lines.extend(["", "## Next TODO", "", f"`{summary['next_todo']}`", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    ingestion_dir = as_abs(args.ingestion_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()
    ingestion_summary = read_json(ingestion_dir / "summary.json")

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
        input_counts[target_name] = counts_for(rows, target_name)
        errors = validate_rows(target_name, rows)
        all_validation_errors.extend(errors)
        slice_summaries, group_rows, group_summary_rows = build_slices(target_name, rows, output_dir)
        all_slice_summaries.extend(slice_summaries)
        all_group_rows.extend(group_rows)
        all_group_summaries.extend(group_summary_rows)
        target_decisions[target_name] = per_target_decision(target_name, slice_summaries, errors)

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
        "schema_version": "h002_reliability_target_v6_shortcut_controlled_target_independence_audit_summary_v1",
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
            "posterior_smoke_allowed": status.endswith("_multiclass_reliability_ready"),
            "hidden_manifest_joined_after_label_lock": True,
            "review_fields_as_model_input": False,
            "hidden_sampling_axes_as_model_input": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
        },
        "risk_thresholds": {
            "risk_nmi_threshold": RISK_NMI_THRESHOLD,
            "risk_majority_excess_threshold": RISK_MAJORITY_EXCESS_THRESHOLD,
            "risk_class_rate_range_threshold": RISK_CLASS_RATE_RANGE_THRESHOLD,
            "risk_large_group_rows": RISK_LARGE_GROUP_ROWS,
            "risk_large_group_purity": RISK_LARGE_GROUP_PURITY,
            "min_strict_rows_binary": MIN_STRICT_ROWS_BINARY,
            "min_strict_per_class_binary": MIN_STRICT_PER_CLASS_BINARY,
            "min_strict_rows_multiclass": MIN_STRICT_ROWS_MULTICLASS,
            "min_strict_per_class_multiclass": MIN_STRICT_PER_CLASS_MULTICLASS,
            "min_diagnostic_rows_binary": MIN_DIAGNOSTIC_ROWS_BINARY,
            "min_diagnostic_per_class_binary": MIN_DIAGNOSTIC_PER_CLASS_BINARY,
            "min_diagnostic_rows_multiclass": MIN_DIAGNOSTIC_ROWS_MULTICLASS,
            "min_diagnostic_per_class_multiclass": MIN_DIAGNOSTIC_PER_CLASS_MULTICLASS,
        },
        "input_counts": input_counts,
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
    multiclass = summary["target_decisions"][RELIABILITY_MULTICLASS]["original"]
    rel_bin = summary["target_decisions"][RELIABILITY_BINARY]["original"]
    geom = summary["target_decisions"][GEOMETRY_TARGET]["original"]
    use = summary["target_decisions"][USEFULNESS_TARGET]["original"]
    rel_pos, rel_neg = binary_counts_for_report(rel_bin)
    geom_pos, geom_neg = binary_counts_for_report(geom)
    use_pos, use_neg = binary_counts_for_report(use)
    print(
        "status={status} multiclass_rows={mc_rows} multiclass_min={mc_min} "
        "multiclass_status={mc_status} rel_binary={rel_rows}/{rel_pos}/{rel_neg} "
        "rel_binary_status={rel_status} geom={geom_rows}/{geom_pos}/{geom_neg} "
        "geom_status={geom_status} use={use_rows}/{use_pos}/{use_neg} "
        "use_status={use_status} errors={errors} posterior_allowed={posterior_allowed} "
        "validation_used={validation_used} test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            mc_rows=multiclass["rows"],
            mc_min=multiclass["min_class"],
            mc_status=summary["target_decisions"][RELIABILITY_MULTICLASS]["status"],
            rel_rows=rel_bin["rows"],
            rel_pos=rel_pos,
            rel_neg=rel_neg,
            rel_status=summary["target_decisions"][RELIABILITY_BINARY]["status"],
            geom_rows=geom["rows"],
            geom_pos=geom_pos,
            geom_neg=geom_neg,
            geom_status=summary["target_decisions"][GEOMETRY_TARGET]["status"],
            use_rows=use["rows"],
            use_pos=use_pos,
            use_neg=use_neg,
            use_status=summary["target_decisions"][USEFULNESS_TARGET]["status"],
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
