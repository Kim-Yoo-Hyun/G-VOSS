#!/usr/bin/env python3
"""Audit H002 v8 endpoint-pair counterfactual target independence."""

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

DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_label_ingestion_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit_codex_proxy_user_requested"

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
    RELIABILITY_MULTICLASS: "h002_reliability_target_v8_endpoint_pair_counterfactual_multiclass_row_v1",
    RELIABILITY_BINARY: "h002_reliability_target_v8_endpoint_pair_counterfactual_binary_row_v1",
    GEOMETRY_TARGET: "h002_geometry_support_v6_endpoint_pair_counterfactual_binary_row_v1",
    USEFULNESS_TARGET: "h002_relation_usefulness_v6_endpoint_pair_counterfactual_binary_row_v1",
}

EXPECTED_CLASSES = {
    RELIABILITY_MULTICLASS: {"accept_reliable", "reject_unreliable", "abstain_uncertain"},
    RELIABILITY_BINARY: {0, 1},
    GEOMETRY_TARGET: {0, 1},
    USEFULNESS_TARGET: {0, 1},
}

VISIBLE_RELATION_KEYS = ["predicate_family", "predicate_label"]
VISIBLE_OBJECT_KEYS = ["subject_label", "object_label"]
HIDDEN_SAMPLING_KEYS = ["semantic_geometry_bucket_hidden", "source_queue_hidden", "rank_band_hidden"]
ENDPOINT_PAIR_KEYS = [
    "exact_endpoint_pair_key_hidden",
    "undirected_endpoint_pair_key_hidden",
    "scene_label_pair_key_hidden",
    "v8_group_key_hidden",
    "endpoint_pattern_hidden",
    "subject_object_label_pair_hidden",
    "subject_object_family_cell_hidden",
    "object_family_cell_hidden",
    "structural_pair_hidden",
    "hard_room_surface_pair_hidden",
]
GEOMETRY_ALIGNMENT_KEYS = [
    "geometry_status_hidden",
    "h001_verification_status_hidden",
    "label_match_status_hidden",
    "label_geometry_bucket_hidden",
]
CONSTRUCTION_COVERAGE_KEYS = [
    "evidence_packet_status",
    "packet_gap_decision",
    "row_gap_decision_hidden",
    "normalized_evidence_status_hidden",
    "packet_status_hidden",
    "asset_packet_source_hidden",
    "packet_source_hidden",
    "replacement_source_hidden",
    "replacement_for_family_bucket_hidden",
]
HIDDEN_MACHINE_HINT_KEYS = ["machine_hint_hidden"]

GROUP_KEY_CATEGORIES = {
    "visible_relation": VISIBLE_RELATION_KEYS,
    "visible_object_identity": VISIBLE_OBJECT_KEYS,
    "hidden_sampling_axis": HIDDEN_SAMPLING_KEYS,
    "endpoint_pair_control": ENDPOINT_PAIR_KEYS,
    "geometry_alignment": GEOMETRY_ALIGNMENT_KEYS,
    "construction_coverage": CONSTRUCTION_COVERAGE_KEYS,
    "hidden_machine_hint": HIDDEN_MACHINE_HINT_KEYS,
}

BLOCKING_RISK_CATEGORIES = {
    "visible_relation",
    "visible_object_identity",
    "hidden_sampling_axis",
    "endpoint_pair_control",
    "construction_coverage",
    "hidden_machine_hint",
}

CONTROL_REQUIRED_CATEGORIES = {"geometry_alignment"}

RISK_NMI_THRESHOLD = 0.20
RISK_MAJORITY_EXCESS_THRESHOLD = 0.10
RISK_MAJORITY_ACC_THRESHOLD = 0.85
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
    "original_v8": {
        "balanced_keys": [],
        "reason": "full v8 endpoint-pair counterfactual target",
        "priority": 99,
    },
    "family_balanced_v8": {
        "balanced_keys": ["predicate_family"],
        "reason": "balanced within predicate family",
        "priority": 1,
    },
    "predicate_balanced_v8": {
        "balanced_keys": ["predicate_label"],
        "reason": "balanced within predicate label",
        "priority": 2,
    },
    "semantic_geometry_bucket_balanced_v8": {
        "balanced_keys": ["semantic_geometry_bucket_hidden"],
        "reason": "balanced within semantic/geometry bucket",
        "priority": 3,
    },
    "source_queue_balanced_v8": {
        "balanced_keys": ["source_queue_hidden"],
        "reason": "balanced within HL/LH source queue",
        "priority": 4,
    },
    "rank_band_balanced_v8": {
        "balanced_keys": ["rank_band_hidden"],
        "reason": "balanced within semantic rank band",
        "priority": 5,
    },
    "geometry_status_balanced_v8": {
        "balanced_keys": ["geometry_status_hidden"],
        "reason": "balanced within frozen geometry status",
        "priority": 6,
    },
    "packet_gap_balanced_v8": {
        "balanced_keys": ["packet_gap_decision"],
        "reason": "balanced within packet gap decision",
        "priority": 7,
    },
    "subject_label_balanced_v8": {
        "balanced_keys": ["subject_label"],
        "reason": "balanced within visible subject label",
        "priority": 8,
    },
    "object_label_balanced_v8": {
        "balanced_keys": ["object_label"],
        "reason": "balanced within visible object label",
        "priority": 9,
    },
    "endpoint_pattern_balanced_v8": {
        "balanced_keys": ["endpoint_pattern_hidden"],
        "reason": "balanced within endpoint pattern",
        "priority": 10,
    },
    "exact_endpoint_pair_balanced_v8": {
        "balanced_keys": ["exact_endpoint_pair_key_hidden"],
        "reason": "balanced within exact endpoint pair",
        "priority": 11,
    },
    "subject_object_label_pair_balanced_v8": {
        "balanced_keys": ["subject_object_label_pair_hidden"],
        "reason": "balanced within subject/object label pair",
        "priority": 12,
    },
    "v8_group_balanced_v8": {
        "balanced_keys": ["v8_group_key_hidden"],
        "reason": "balanced within v8 endpoint-pair group",
        "priority": 13,
    },
    "family_bucket_balanced_v8": {
        "balanced_keys": ["predicate_family", "semantic_geometry_bucket_hidden"],
        "reason": "balanced within predicate family and candidate bucket",
        "priority": 14,
    },
    "family_geometry_status_balanced_v8": {
        "balanced_keys": ["predicate_family", "geometry_status_hidden"],
        "reason": "balanced within predicate family and frozen geometry status",
        "priority": 15,
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
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_target_value(value: Any) -> Any:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, str):
        if value in {"0", "1"}:
            return int(value)
        return value
    return value


def target_value(row: dict[str, Any]) -> Any:
    return normalize_target_value(row.get("target_y"))


def group_value(row: dict[str, Any], key: str) -> str:
    if key in row:
        return str(row.get(key))
    hidden = row.get("hidden_audit_metadata_post_label_only", {})
    if key in hidden:
        return str(hidden.get(key))
    deployable = row.get("deployable_evidence_after_label_lock", {})
    if key in deployable:
        return str(deployable.get(key))
    for nested_key in [
        "coverage_evidence",
        "source_semantic_and_geometry_scores_hidden_from_labeler_until_lock",
        "semantic_evidence",
        "geometry_evidence",
        "uncertainty_evidence",
    ]:
        nested = deployable.get(nested_key, {})
        if isinstance(nested, dict) and key in nested:
            return str(nested.get(key))
    return "missing"


def group_tuple(row: dict[str, Any], keys: list[str]) -> str:
    if not keys:
        return "__all__"
    return "||".join(f"{key}={group_value(row, key)}" for key in keys)


def semantic_rank(row: dict[str, Any]) -> float:
    for key in ["semantic_rank_hidden", "semantic_rank", "source_rank"]:
        value = row.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    deployable = row.get("deployable_evidence_after_label_lock", {})
    source = deployable.get("source_semantic_and_geometry_scores_hidden_from_labeler_until_lock", {})
    for key in ["semantic_rank", "rank", "source_rank"]:
        value = source.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                pass
    return 1e12


def stable_key(row: dict[str, Any]) -> tuple[float, str]:
    return semantic_rank(row), str(row.get("blind_review_id") or row.get("prediction_id") or "")


def entropy(counts: Counter[Any]) -> float:
    total = sum(counts.values())
    if total <= 0:
        return 0.0
    value = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        prob = count / total
        value -= prob * math.log2(prob)
    return value


def group_risk_summary(target_name: str, rows: list[dict[str, Any]], category: str, key: str) -> dict[str, Any]:
    class_counts = Counter(target_value(row) for row in rows)
    total = len(rows)
    baseline_acc = max(class_counts.values()) / total if total else 0.0
    groups: dict[str, Counter[Any]] = defaultdict(Counter)
    for row in rows:
        groups[group_value(row, key)][target_value(row)] += 1

    majority_correct = sum(max(counts.values()) for counts in groups.values()) if total else 0
    majority_acc = majority_correct / total if total else 0.0
    hy = entropy(class_counts)
    h_y_given_g = 0.0
    for counts in groups.values():
        group_total = sum(counts.values())
        if group_total:
            h_y_given_g += (group_total / total) * entropy(counts)
    mutual_info = max(0.0, hy - h_y_given_g)
    nmi = mutual_info / hy if hy > 0 else 0.0

    class_rate_range = 0.0
    for cls in class_counts:
        rates = []
        for counts in groups.values():
            group_total = sum(counts.values())
            if group_total > 0:
                rates.append(counts[cls] / group_total)
        if rates:
            class_rate_range = max(class_rate_range, max(rates) - min(rates))

    large_group_max_purity = 0.0
    large_group_key = "none"
    large_group_rows = 0
    pure_group_count = 0
    single_class_group_count = 0
    for group_key, counts in groups.items():
        group_total = sum(counts.values())
        purity = max(counts.values()) / group_total if group_total else 0.0
        if purity >= 0.999:
            single_class_group_count += 1
        if group_total >= RISK_LARGE_GROUP_ROWS and purity >= RISK_LARGE_GROUP_PURITY:
            pure_group_count += 1
            if purity > large_group_max_purity or (purity == large_group_max_purity and group_total > large_group_rows):
                large_group_max_purity = purity
                large_group_key = group_key
                large_group_rows = group_total

    reasons: list[str] = []
    if nmi >= RISK_NMI_THRESHOLD:
        reasons.append("high_nmi")
    if majority_acc >= RISK_MAJORITY_ACC_THRESHOLD:
        reasons.append("high_majority_accuracy")
    if majority_acc - baseline_acc >= RISK_MAJORITY_EXCESS_THRESHOLD:
        reasons.append("majority_excess_over_baseline")
    if class_rate_range >= RISK_CLASS_RATE_RANGE_THRESHOLD:
        reasons.append("high_class_rate_range")
    if large_group_max_purity >= RISK_LARGE_GROUP_PURITY:
        reasons.append("large_pure_group")

    risk_level = "none"
    if reasons:
        risk_level = "control_required" if category in CONTROL_REQUIRED_CATEGORIES else "blocking"

    top_groups = []
    for group_key, counts in sorted(
        groups.items(),
        key=lambda item: (-sum(item[1].values()), -max(item[1].values()), str(item[0])),
    )[:8]:
        group_total = sum(counts.values())
        top_groups.append(
            {
                "group_value": group_key,
                "rows": group_total,
                "majority_label": str(counts.most_common(1)[0][0]) if counts else "",
                "majority_rate": max(counts.values()) / group_total if group_total else 0.0,
                "class_counts": {str(cls): count for cls, count in sorted(counts.items(), key=lambda x: str(x[0]))},
            }
        )

    return {
        "target_name": target_name,
        "category": category,
        "group_key": key,
        "rows": total,
        "classes": {str(cls): count for cls, count in sorted(class_counts.items(), key=lambda x: str(x[0]))},
        "groups": len(groups),
        "majority_baseline_accuracy": baseline_acc,
        "majority_rule_accuracy": majority_acc,
        "majority_excess_over_baseline": majority_acc - baseline_acc,
        "normalized_mutual_information": nmi,
        "class_rate_range": class_rate_range,
        "large_group_max_purity": large_group_max_purity,
        "large_group_key": large_group_key,
        "large_group_rows": large_group_rows,
        "single_class_group_count": single_class_group_count,
        "large_pure_group_count": pure_group_count,
        "risk_level": risk_level,
        "risk_reasons": reasons,
        "top_groups": top_groups,
    }


def all_group_risks(target_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for category, keys in GROUP_KEY_CATEGORIES.items():
        for key in keys:
            risks.append(group_risk_summary(target_name, rows, category, key))
    return risks


def balanced_slice(rows: list[dict[str, Any]], keys: list[str]) -> list[dict[str, Any]]:
    if not keys:
        return sorted(rows, key=stable_key)
    buckets: dict[str, dict[Any, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        buckets[group_tuple(row, keys)][target_value(row)].append(row)
    selected: list[dict[str, Any]] = []
    for class_buckets in buckets.values():
        if len(class_buckets) < 2:
            continue
        min_count = min(len(items) for items in class_buckets.values())
        if min_count <= 0:
            continue
        for items in class_buckets.values():
            selected.extend(sorted(items, key=stable_key)[:min_count])
    return sorted(selected, key=stable_key)


def size_thresholds(target_name: str) -> dict[str, int]:
    if target_name == RELIABILITY_MULTICLASS:
        return {
            "strict_rows": MIN_STRICT_ROWS_MULTICLASS,
            "strict_per_class": MIN_STRICT_PER_CLASS_MULTICLASS,
            "diagnostic_rows": MIN_DIAGNOSTIC_ROWS_MULTICLASS,
            "diagnostic_per_class": MIN_DIAGNOSTIC_PER_CLASS_MULTICLASS,
        }
    return {
        "strict_rows": MIN_STRICT_ROWS_BINARY,
        "strict_per_class": MIN_STRICT_PER_CLASS_BINARY,
        "diagnostic_rows": MIN_DIAGNOSTIC_ROWS_BINARY,
        "diagnostic_per_class": MIN_DIAGNOSTIC_PER_CLASS_BINARY,
    }


def class_count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(target_value(row) for row in rows)
    return {
        "rows": len(rows),
        "classes": {str(cls): count for cls, count in sorted(counts.items(), key=lambda x: str(x[0]))},
        "min_class": min(counts.values()) if counts else 0,
        "majority_baseline_accuracy": max(counts.values()) / len(rows) if rows else 0.0,
    }


def validate_target_rows(target_name: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_classes = EXPECTED_CLASSES[target_name]
    seen = set()
    for index, row in enumerate(rows, start=1):
        blind_id = str(row.get("blind_review_id") or "")
        if blind_id in seen:
            errors.append({"target_name": target_name, "error_type": "duplicate_blind_review_id", "row_number": index, "blind_review_id": blind_id})
        seen.add(blind_id)
        if row.get("target_name") != target_name:
            errors.append({"target_name": target_name, "error_type": "unexpected_target_name", "row_number": index, "value": row.get("target_name")})
        if row.get("schema_version") != TARGET_SCHEMA_VERSIONS[target_name]:
            errors.append({"target_name": target_name, "error_type": "unexpected_schema_version", "row_number": index, "value": row.get("schema_version")})
        if target_value(row) not in expected_classes:
            errors.append({"target_name": target_name, "error_type": "unexpected_target_value", "row_number": index, "value": row.get("target_y")})
        # Split and validation/test provenance are recorded at the ingestion
        # summary boundary, not repeated on every target row.
        if row.get("predicate_family") not in {"relative_vertical", "support_contact"}:
            errors.append({"target_name": target_name, "error_type": "unexpected_predicate_family", "row_number": index, "value": row.get("predicate_family")})
    return errors


def slice_summary(target_name: str, slice_name: str, spec: dict[str, Any], rows: list[dict[str, Any]], path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    group_risks = all_group_risks(target_name, rows)
    count_summary = class_count_summary(rows)
    thresholds = size_thresholds(target_name)
    blocking_risks = [risk for risk in group_risks if risk["risk_level"] == "blocking"]
    control_risks = [risk for risk in group_risks if risk["risk_level"] == "control_required"]
    blocking_by_category = Counter(risk["category"] for risk in blocking_risks)
    control_by_category = Counter(risk["category"] for risk in control_risks)
    strict_size_ready = (
        count_summary["rows"] >= thresholds["strict_rows"]
        and len(count_summary["classes"]) >= 2
        and count_summary["min_class"] >= thresholds["strict_per_class"]
    )
    diagnostic_size_ready = (
        count_summary["rows"] >= thresholds["diagnostic_rows"]
        and len(count_summary["classes"]) >= 2
        and count_summary["min_class"] >= thresholds["diagnostic_per_class"]
    )
    strict_candidate = strict_size_ready and not blocking_risks and not control_risks
    diagnostic_candidate = diagnostic_size_ready and not blocking_risks
    construction_only_candidate = diagnostic_size_ready and not [
        risk for risk in blocking_risks if risk["category"] not in {"construction_coverage"}
    ]
    top_blocking = sorted(
        blocking_risks,
        key=lambda risk: (
            -risk["normalized_mutual_information"],
            -risk["majority_rule_accuracy"],
            -risk["class_rate_range"],
            risk["group_key"],
        ),
    )[:8]
    top_control = sorted(
        control_risks,
        key=lambda risk: (
            -risk["normalized_mutual_information"],
            -risk["majority_rule_accuracy"],
            -risk["class_rate_range"],
            risk["group_key"],
        ),
    )[:6]
    summary = {
        "target_name": target_name,
        "slice_name": slice_name,
        "reason": spec["reason"],
        "balanced_keys": spec["balanced_keys"],
        "priority": spec["priority"],
        "path": rel_path(path),
        **count_summary,
        "strict_size_ready": strict_size_ready,
        "diagnostic_size_ready": diagnostic_size_ready,
        "strict_candidate": strict_candidate,
        "diagnostic_candidate": diagnostic_candidate,
        "construction_only_candidate": construction_only_candidate,
        "blocking_risk_count": len(blocking_risks),
        "control_required_risk_count": len(control_risks),
        "blocking_by_category": dict(blocking_by_category),
        "control_required_by_category": dict(control_by_category),
        "top_blocking_risks": top_blocking,
        "top_control_required_risks": top_control,
    }
    return summary, group_risks


def choose_slice(summaries: list[dict[str, Any]], field: str) -> dict[str, Any] | None:
    candidates = [summary for summary in summaries if summary.get(field)]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item["priority"], -item["rows"], item["slice_name"]))[0]


def per_target_decision(target_name: str, summaries: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    original = next(summary for summary in summaries if summary["slice_name"] == "original_v8")
    strict = choose_slice(summaries, "strict_candidate")
    diagnostic = choose_slice(summaries, "diagnostic_candidate")
    construction = choose_slice(summaries, "construction_only_candidate")
    thresholds = size_thresholds(target_name)
    if errors:
        status = "target_independence_audit_errors"
        posterior_allowed = False
        decision = "Fix target row validation errors before using this target."
        next_step = "fix_v8_target_independence_audit_errors"
    elif not original["strict_size_ready"]:
        status = "blocked_insufficient_binary_or_multiclass_mass"
        posterior_allowed = False
        decision = "The target does not meet the minimum row/per-class count for a strict posterior smoke."
        next_step = "revise_v8_sampling_or_label_more_rows"
    elif strict:
        status = "strict_controlled_slice_ready"
        posterior_allowed = target_name == RELIABILITY_BINARY
        decision = "A strict slice clears blocking and geometry-control risks."
        next_step = "v8_source_feature_join_then_controlled_posterior_smoke"
    elif diagnostic:
        status = "blocked_geometry_control_required"
        posterior_allowed = False
        decision = "No strict slice clears geometry-control risks, but a diagnostic slice clears blocking shortcut risks."
        next_step = "build_same_geometry_status_control_or_revise_v8_labels"
    elif construction:
        status = "blocked_construction_shortcut_only_diagnostic_slice"
        posterior_allowed = False
        decision = "Only construction-only diagnostic slices are available; method validation remains blocked."
        next_step = "revise_v8_target_or_collect_more_independent_labels"
    else:
        status = "blocked_shortcut_risk"
        posterior_allowed = False
        decision = "Object, endpoint, packet, family, bucket, or hidden metadata shortcuts remain too predictive."
        next_step = "revise_v8_target_or_collect_more_independent_labels"
    return {
        "target_name": target_name,
        "status": status,
        "posterior_allowed": posterior_allowed,
        "decision": decision,
        "next_step": next_step,
        "minimums": thresholds,
        "original": original,
        "recommended_strict_slice": strict,
        "recommended_diagnostic_slice": diagnostic,
        "recommended_construction_slice": construction,
        "validation_errors": len(errors),
    }


def validate_ingestion_summary(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_next = "reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit"
    if summary.get("next_todo") != expected_next:
        errors.append({"error_type": "unexpected_ingestion_next_todo", "expected": expected_next, "value": summary.get("next_todo")})
    boundary = summary.get("boundary", {})
    if boundary.get("validation_usage") is not False or boundary.get("test_usage") is not False:
        errors.append(
            {
                "error_type": "ingestion_boundary_uses_validation_or_test",
                "validation_usage": boundary.get("validation_usage"),
                "test_usage": boundary.get("test_usage"),
            }
        )
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    relation_types = summary["relation_types"]
    lines = [
        "# H002 V8 Endpoint-Pair Counterfactual Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Split: Open3DSG train-only.",
        "- No validation/test rows are used.",
        "- No posterior is trained in this step.",
        "- Hidden metadata is used only after label lock for target-independence auditing.",
        "- Geometry-status alignment is treated as control-required, not as deployable posterior input.",
        "- Multi-view remains audit evidence only.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        summary["decision"],
        "",
        "## Relation Types",
        "",
        "| Family | Rows | Predicate Counts |",
        "| --- | ---: | --- |",
    ]
    for family, item in sorted(relation_types["family_counts"].items()):
        pred_counts = relation_types["predicates_by_family"].get(family, {})
        pred_text = ", ".join(f"`{pred}`={count}" for pred, count in sorted(pred_counts.items()))
        lines.append(f"| `{family}` | {item} | {pred_text} |")
    lines.extend(
        [
            "",
            "## Target Artifacts",
            "",
            "| Target | Rows | Classes | Posterior Allowed | Status |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        classes = ", ".join(f"`{label}`={count}" for label, count in original["classes"].items())
        lines.append(
            f"| `{target_name}` | {original['rows']} | {classes} | "
            f"`{decision['posterior_allowed']}` | `{decision['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Original Shortcut Risks",
            "",
            "| Target | Category | Key | Majority Acc | Baseline | NMI | Class Range | Reasons |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        risks = original["top_blocking_risks"] + original["top_control_required_risks"]
        if not risks:
            lines.append(f"| `{target_name}` | none | none | 0.0000 | 0.0000 | 0.0000 | 0.0000 | none |")
        for risk in risks:
            lines.append(
                f"| `{target_name}` | `{risk['category']}` | `{risk['group_key']}` | "
                f"{risk['majority_rule_accuracy']:.4f} | {risk['majority_baseline_accuracy']:.4f} | "
                f"{risk['normalized_mutual_information']:.4f} | {risk['class_rate_range']:.4f} | "
                f"`{','.join(risk['risk_reasons'])}` |"
            )
    lines.extend(
        [
            "",
            "## Controlled Slice Summary",
            "",
            "| Target | Slice | Rows | Min Class | Blocking Risks | Control Risks | Strict | Diagnostic |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
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
            f"{item['blocking_risk_count']} | {item['control_required_risk_count']} | "
            f"`{item['strict_candidate']}` | `{item['diagnostic_candidate']}` |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The 240-row multiclass artifact is useful for coverage/error taxonomy, but abstain rows dominate.",
            "- The 69-row relation-reliability binary target has enough positive/negative mass for a smoke candidate.",
            "- However, endpoint/object/predicate metadata shortcuts are too predictive, so posterior smoke is blocked.",
            "- Geometry-support and usefulness targets are exported as auxiliary targets, not as proof of factorized posterior quality.",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    ingestion_dir = as_abs(args.ingestion_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    ingestion_summary = read_json(ingestion_dir / "summary.json")
    validation_errors = validate_ingestion_summary(ingestion_summary)
    input_paths: dict[str, str] = {"ingestion_summary": rel_path(ingestion_dir / "summary.json")}
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "target_risk_summary": output_dir / "target_risk_summary.csv",
        "group_risk_table": output_dir / "group_risk_table.csv",
        "slice_summaries": output_dir / "slice_summaries.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "target_slices": output_dir / "target_slices",
    }

    all_slice_summaries: list[dict[str, Any]] = []
    all_group_risks: list[dict[str, Any]] = []
    target_decisions: dict[str, Any] = {}
    target_counts: dict[str, Any] = {}
    target_validation_errors: dict[str, list[dict[str, Any]]] = {}
    relation_type_source_rows: list[dict[str, Any]] = []

    for target_name, filename in TARGET_INPUTS.items():
        input_path = ingestion_dir / filename
        input_paths[target_name] = rel_path(input_path)
        rows = read_jsonl(input_path)
        if target_name == RELIABILITY_MULTICLASS:
            relation_type_source_rows = rows
        errors = validate_target_rows(target_name, rows)
        target_validation_errors[target_name] = errors
        validation_errors.extend(errors)
        target_counts[target_name] = class_count_summary(rows)
        slice_summaries: list[dict[str, Any]] = []
        for slice_name, spec in SLICE_SPECS.items():
            slice_rows = balanced_slice(rows, spec["balanced_keys"])
            slice_path = output_paths["target_slices"] / target_name / f"{slice_name}.jsonl"
            write_jsonl(slice_path, slice_rows)
            summary, group_risks = slice_summary(target_name, slice_name, spec, slice_rows, slice_path)
            slice_summaries.append(summary)
            all_slice_summaries.append(summary)
            for risk in group_risks:
                row = {
                    "target_name": risk["target_name"],
                    "slice_name": slice_name,
                    "category": risk["category"],
                    "group_key": risk["group_key"],
                    "rows": risk["rows"],
                    "groups": risk["groups"],
                    "majority_baseline_accuracy": risk["majority_baseline_accuracy"],
                    "majority_rule_accuracy": risk["majority_rule_accuracy"],
                    "majority_excess_over_baseline": risk["majority_excess_over_baseline"],
                    "normalized_mutual_information": risk["normalized_mutual_information"],
                    "class_rate_range": risk["class_rate_range"],
                    "large_group_max_purity": risk["large_group_max_purity"],
                    "large_group_key": risk["large_group_key"],
                    "large_group_rows": risk["large_group_rows"],
                    "risk_level": risk["risk_level"],
                    "risk_reasons": "|".join(risk["risk_reasons"]),
                }
                all_group_risks.append(row)
        target_decisions[target_name] = per_target_decision(target_name, slice_summaries, errors)

    family_counts = Counter(row.get("predicate_family") for row in relation_type_source_rows)
    predicate_counts = Counter(row.get("predicate_label") for row in relation_type_source_rows)
    predicates_by_family: dict[str, Counter[str]] = defaultdict(Counter)
    for row in relation_type_source_rows:
        predicates_by_family[str(row.get("predicate_family"))][str(row.get("predicate_label"))] += 1

    relation_decision = target_decisions[RELIABILITY_BINARY]
    if validation_errors:
        status = "h002_reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit_errors"
        decision = "Validation errors remain; do not run posterior smoke."
        next_todo = "fix_reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit_errors"
        posterior_allowed = False
    elif relation_decision["posterior_allowed"]:
        status = "h002_reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit_relation_binary_ready"
        decision = "The relation-reliability binary target has a strict controlled slice and may proceed to feature join."
        next_todo = "reliability_target_v8_endpoint_pair_counterfactual_source_feature_join"
        posterior_allowed = True
    else:
        status = "h002_reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit_blocked_shortcut_risk"
        decision = (
            "The 69-row binary target is class-usable, but object/endpoint/predicate/metadata shortcuts remain "
            "too predictive. Posterior smoke should stay blocked until a stricter target or controlled slice exists."
        )
        next_todo = "reliability_target_v8_endpoint_pair_counterfactual_target_path_decision"
        posterior_allowed = False

    summary = {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": input_paths,
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_claim_allowed": posterior_allowed,
            "multi_view_as_model_input": False,
            "hidden_metadata_used_for_audit_only": True,
            "geometry_status_is_control_axis_not_main_score": True,
            "target_labels_source": "codex_proxy_user_requested_treat_as_human_confirmed_for_hypothesis_stage",
        },
        "risk_thresholds": {
            "normalized_mutual_information": RISK_NMI_THRESHOLD,
            "majority_excess_over_baseline": RISK_MAJORITY_EXCESS_THRESHOLD,
            "majority_rule_accuracy": RISK_MAJORITY_ACC_THRESHOLD,
            "class_rate_range": RISK_CLASS_RATE_RANGE_THRESHOLD,
            "large_group_rows": RISK_LARGE_GROUP_ROWS,
            "large_group_purity": RISK_LARGE_GROUP_PURITY,
        },
        "relation_types": {
            "family_counts": dict(sorted(family_counts.items())),
            "predicate_counts": dict(sorted(predicate_counts.items())),
            "predicates_by_family": {family: dict(sorted(counts.items())) for family, counts in sorted(predicates_by_family.items())},
        },
        "ingestion_status": ingestion_summary.get("status"),
        "target_counts": target_counts,
        "target_decisions": target_decisions,
        "slice_summaries": all_slice_summaries,
        "validation_errors": len(validation_errors),
        "decision": decision,
        "next_todo": next_todo,
    }

    target_risk_rows: list[dict[str, Any]] = []
    for target_name, target_decision in target_decisions.items():
        original = target_decision["original"]
        for risk in original["top_blocking_risks"] + original["top_control_required_risks"]:
            target_risk_rows.append(
                {
                    "target_name": target_name,
                    "category": risk["category"],
                    "group_key": risk["group_key"],
                    "risk_level": risk["risk_level"],
                    "risk_reasons": "|".join(risk["risk_reasons"]),
                    "majority_rule_accuracy": risk["majority_rule_accuracy"],
                    "majority_baseline_accuracy": risk["majority_baseline_accuracy"],
                    "normalized_mutual_information": risk["normalized_mutual_information"],
                    "class_rate_range": risk["class_rate_range"],
                }
            )

    slice_csv_rows = [
        {
            "target_name": item["target_name"],
            "slice_name": item["slice_name"],
            "rows": item["rows"],
            "min_class": item["min_class"],
            "classes": json.dumps(item["classes"], sort_keys=True),
            "blocking_risk_count": item["blocking_risk_count"],
            "control_required_risk_count": item["control_required_risk_count"],
            "strict_size_ready": item["strict_size_ready"],
            "diagnostic_size_ready": item["diagnostic_size_ready"],
            "strict_candidate": item["strict_candidate"],
            "diagnostic_candidate": item["diagnostic_candidate"],
            "construction_only_candidate": item["construction_only_candidate"],
            "balanced_keys": "|".join(item["balanced_keys"]),
            "path": item["path"],
        }
        for item in all_slice_summaries
    ]

    write_json(output_paths["summary"], summary)
    write_csv(output_paths["target_risk_summary"], target_risk_rows)
    write_csv(output_paths["group_risk_table"], all_group_risks)
    write_csv(output_paths["slice_summaries"], slice_csv_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    rel = summary["target_decisions"][RELIABILITY_BINARY]
    original = rel["original"]
    print(f"status={summary['status']}")
    print(f"relation_binary_rows={original['rows']} classes={original['classes']}")
    print(f"relation_binary_status={rel['status']} posterior_allowed={rel['posterior_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"relation_types={summary['relation_types']['family_counts']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
