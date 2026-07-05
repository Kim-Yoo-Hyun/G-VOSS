#!/usr/bin/env python3
"""Audit H002 reliability target v3 independence before posterior smoke."""

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

DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v3_label_ingestion_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_target_independence_audit_codex_proxy_user_requested"

RELIABILITY_TARGET = "relation_reliability_v3_binary_target"
GEOMETRY_TARGET = "geometry_support_v3_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v3_binary_target"

TARGET_INPUTS = {
    RELIABILITY_TARGET: "relation_reliability_v3_posterior_candidates.jsonl",
    GEOMETRY_TARGET: "geometry_support_v3_posterior_candidates.jsonl",
    USEFULNESS_TARGET: "relation_usefulness_v3_posterior_candidates.jsonl",
}

HIDDEN_PROVENANCE_KEYS = [
    "sampling_category_hidden",
    "expected_v3_role_hidden",
]

ENDPOINT_PATTERN_KEYS = [
    "endpoint_flag_pattern_hidden",
]

CONSTRUCTION_KEYS = [
    "queue_kind_hidden",
    "rank_band_hidden",
    "label_match_status_hidden",
]

EXPECTED_GEOMETRY_ALIGNMENT_KEYS = [
    "geometry_status_hidden",
]

VISIBLE_RELATION_KEYS = [
    "predicate_family",
    "predicate_label",
]

VISIBLE_OBJECT_KEYS = [
    "subject_label",
    "object_label",
]

VISIBLE_COVERAGE_KEYS = [
    "evidence_packet_status",
]

RISK_NMI_THRESHOLD = 0.20
RISK_MAJORITY_THRESHOLD = 0.85
RISK_POSITIVE_RATE_RANGE_THRESHOLD = 0.70
RISK_LARGE_GROUP_ROWS = 10
RISK_LARGE_GROUP_PURITY = 0.95

MIN_STRICT_ROWS = 50
MIN_STRICT_PER_CLASS = 20
MIN_DIAGNOSTIC_ROWS = 30
MIN_DIAGNOSTIC_PER_CLASS = 10

SLICE_SPECS = {
    "original_v3": {
        "balanced_keys": [],
        "reason": "full v3 binary target",
        "priority": 99,
    },
    "sampling_category_balanced_v3": {
        "balanced_keys": ["sampling_category_hidden"],
        "reason": "matched positives/negatives within hidden sampling category",
        "priority": 1,
    },
    "expected_role_balanced_v3": {
        "balanced_keys": ["expected_v3_role_hidden"],
        "reason": "matched positives/negatives within hidden expected role",
        "priority": 2,
    },
    "endpoint_pattern_balanced_v3": {
        "balanced_keys": ["endpoint_flag_pattern_hidden"],
        "reason": "matched positives/negatives within hidden endpoint flag pattern",
        "priority": 3,
    },
    "queue_balanced_v3": {
        "balanced_keys": ["queue_kind_hidden"],
        "reason": "matched positives/negatives within hidden HL/LH queue",
        "priority": 4,
    },
    "rank_band_balanced_v3": {
        "balanced_keys": ["rank_band_hidden"],
        "reason": "matched positives/negatives within hidden semantic rank band",
        "priority": 5,
    },
    "label_match_balanced_v3": {
        "balanced_keys": ["label_match_status_hidden"],
        "reason": "matched positives/negatives within hidden label-match state",
        "priority": 6,
    },
    "geometry_status_balanced_v3": {
        "balanced_keys": ["geometry_status_hidden"],
        "reason": "matched positives/negatives within hidden geometry status",
        "priority": 7,
    },
    "family_balanced_v3": {
        "balanced_keys": ["predicate_family"],
        "reason": "matched positives/negatives within visible predicate family",
        "priority": 8,
    },
    "predicate_balanced_v3": {
        "balanced_keys": ["predicate_label"],
        "reason": "matched positives/negatives within visible predicate label",
        "priority": 9,
    },
    "subject_label_balanced_v3": {
        "balanced_keys": ["subject_label"],
        "reason": "matched positives/negatives within visible subject label",
        "priority": 10,
    },
    "object_label_balanced_v3": {
        "balanced_keys": ["object_label"],
        "reason": "matched positives/negatives within visible object label",
        "priority": 11,
    },
    "endpoint_family_balanced_v3": {
        "balanced_keys": ["endpoint_flag_pattern_hidden", "predicate_family"],
        "reason": "matched positives/negatives within endpoint pattern and family",
        "priority": 12,
    },
    "endpoint_object_balanced_v3": {
        "balanced_keys": ["endpoint_flag_pattern_hidden", "object_label"],
        "reason": "matched positives/negatives within endpoint pattern and object label",
        "priority": 13,
    },
    "sampling_object_balanced_v3": {
        "balanced_keys": ["sampling_category_hidden", "object_label"],
        "reason": "matched positives/negatives within hidden sampling category and object label",
        "priority": 14,
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


def target_y(row: dict[str, Any]) -> int:
    return int(row["target_y"])


def nested_get(mapping: dict[str, Any], keys: list[str]) -> Any:
    value: Any = mapping
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def group_value(row: dict[str, Any], key: str) -> str:
    if key in row:
        return str(row.get(key))
    hidden = row.get("hidden_audit_metadata_post_label_only", {})
    if key in hidden:
        return str(hidden.get(key))
    deployable = row.get("deployable_evidence_after_label_lock", {})
    coverage = deployable.get("coverage_evidence", {})
    if key in coverage:
        return str(coverage.get(key))
    semantic = deployable.get("semantic_evidence", {})
    if key in semantic:
        return str(semantic.get(key))
    geometry = deployable.get("geometry_scalar_evidence", {})
    if key in geometry:
        return str(geometry.get(key))
    return "missing"


def semantic_rank(row: dict[str, Any]) -> float:
    value = nested_get(row, ["deployable_evidence_after_label_lock", "semantic_evidence", "semantic_rank"])
    if value is None:
        value = nested_get(row, ["hidden_audit_metadata_post_label_only", "semantic_rank_hidden"])
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
        prob = count / total
        entropy -= prob * math.log2(prob)
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
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    positive_rates: list[float] = []
    large_group_high_purity = False
    table: list[dict[str, Any]] = []

    for value, group_rows in sorted(grouped.items()):
        counts = Counter(target_y(row) for row in group_rows)
        pos = counts[1]
        neg = counts[0]
        total = pos + neg
        majority = max(pos, neg)
        majority_acc = majority / total if total else 0.0
        positive_rate = pos / total if total else 0.0
        group_entropy = entropy_from_counts(counts)
        if rows:
            weighted_conditional_entropy += total / len(rows) * group_entropy
        majority_correct += majority
        positive_rates.append(positive_rate)
        if total >= RISK_LARGE_GROUP_ROWS and majority_acc >= RISK_LARGE_GROUP_PURITY:
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
                "positive": pos,
                "negative": neg,
                "positive_rate": positive_rate,
                "majority_label": 1 if pos >= neg else 0,
                "majority_accuracy": majority_acc,
                "entropy_bits": group_entropy,
            }
        )

    mutual_information = max(0.0, overall_entropy - weighted_conditional_entropy)
    nmi = mutual_information / overall_entropy if overall_entropy > 0 else 0.0
    positive_rate_range = (max(positive_rates) - min(positive_rates)) if positive_rates else 0.0
    majority_rule_accuracy = majority_correct / len(rows) if rows else 0.0
    risk_flag = (
        nmi >= RISK_NMI_THRESHOLD
        or majority_rule_accuracy >= RISK_MAJORITY_THRESHOLD
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
        "majority_rule_accuracy": majority_rule_accuracy,
        "positive_rate_range": positive_rate_range,
        "large_group_high_purity": large_group_high_purity,
        "single_class_groups": sum(1 for item in table if item["positive"] == 0 or item["negative"] == 0),
        "risk_flag": risk_flag,
    }
    return table, summary


def all_group_summaries(
    rows: list[dict[str, Any]],
    target_name: str,
    slice_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    key_groups = [
        ("hidden_provenance", "hidden_post_label_audit", HIDDEN_PROVENANCE_KEYS),
        ("endpoint_pattern", "hidden_post_label_audit", ENDPOINT_PATTERN_KEYS),
        ("construction", "hidden_post_label_audit", CONSTRUCTION_KEYS),
        ("expected_geometry_alignment", "hidden_post_label_audit", EXPECTED_GEOMETRY_ALIGNMENT_KEYS),
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
    output = [summary for summary in summaries if summary["risk_mode"] == risk_mode and summary["risk_flag"]]
    return sorted(
        output,
        key=lambda item: (
            -float(item["normalized_mutual_information"]),
            -float(item["majority_rule_accuracy"]),
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
        "by_family": dict(sorted(Counter(group_value(row, "predicate_family") for row in rows).items())),
        "by_predicate": dict(sorted(Counter(group_value(row, "predicate_label") for row in rows).items())),
        "by_subject_label": dict(sorted(Counter(group_value(row, "subject_label") for row in rows).items())),
        "by_object_label": dict(sorted(Counter(group_value(row, "object_label") for row in rows).items())),
        "by_sampling_category": dict(sorted(Counter(group_value(row, "sampling_category_hidden") for row in rows).items())),
        "by_endpoint_pattern": dict(sorted(Counter(group_value(row, "endpoint_flag_pattern_hidden") for row in rows).items())),
        "by_geometry_status": dict(sorted(Counter(group_value(row, "geometry_status_hidden") for row in rows).items())),
        "by_label_match": dict(sorted(Counter(group_value(row, "label_match_status_hidden") for row in rows).items())),
    }


def top_risks(risks: list[dict[str, Any]], limit: int = 8) -> list[dict[str, Any]]:
    return [
        {
            "group_key": item["group_key"],
            "majority_rule_accuracy": item["majority_rule_accuracy"],
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
    hidden_provenance = risk_summaries(summaries, "hidden_provenance")
    endpoint_pattern = risk_summaries(summaries, "endpoint_pattern")
    construction = risk_summaries(summaries, "construction")
    geometry_alignment = risk_summaries(summaries, "expected_geometry_alignment")
    visible_relation = risk_summaries(summaries, "visible_relation_surface")
    visible_object = risk_summaries(summaries, "visible_object_identity")
    visible_coverage = risk_summaries(summaries, "visible_coverage")

    strict_size_ready = counts["rows"] >= MIN_STRICT_ROWS and counts["min_class"] >= MIN_STRICT_PER_CLASS
    diagnostic_size_ready = counts["rows"] >= MIN_DIAGNOSTIC_ROWS and counts["min_class"] >= MIN_DIAGNOSTIC_PER_CLASS

    strict_candidate = (
        strict_size_ready
        and not hidden_provenance
        and not endpoint_pattern
        and not construction
        and not visible_object
    )
    diagnostic_candidate = (
        diagnostic_size_ready
        and not hidden_provenance
        and not endpoint_pattern
        and not construction
    )
    geometry_only_candidate = (
        diagnostic_size_ready
        and not hidden_provenance
        and not endpoint_pattern
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
        "strict_size_ready": strict_size_ready,
        "diagnostic_size_ready": diagnostic_size_ready,
        "hidden_provenance_risk_count": len(hidden_provenance),
        "endpoint_pattern_risk_count": len(endpoint_pattern),
        "construction_risk_count": len(construction),
        "expected_geometry_alignment_risk_count": len(geometry_alignment),
        "visible_relation_surface_risk_count": len(visible_relation),
        "visible_object_identity_risk_count": len(visible_object),
        "visible_coverage_risk_count": len(visible_coverage),
        "strict_candidate": strict_candidate,
        "diagnostic_candidate": diagnostic_candidate,
        "geometry_only_candidate": geometry_only_candidate,
        "top_hidden_provenance_risks": top_risks(hidden_provenance),
        "top_endpoint_pattern_risks": top_risks(endpoint_pattern),
        "top_construction_risks": top_risks(construction),
        "top_expected_geometry_alignment_risks": top_risks(geometry_alignment),
        "top_visible_relation_surface_risks": top_risks(visible_relation),
        "top_visible_object_identity_risks": top_risks(visible_object),
        "top_visible_coverage_risks": top_risks(visible_coverage),
        "counts": counts,
    }


def build_slices(target_name: str, rows: list[dict[str, Any]], output_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
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
        if row.get("predicate_family") not in {"support_contact", "relative_vertical"}:
            errors.append({"target_name": target_name, "error_type": "row_outside_support_vertical_scope", "row_number": index, "blind_review_id": blind_id, "predicate_family": row.get("predicate_family")})
        if row.get("actual_user_reviewer") is not False:
            errors.append({"target_name": target_name, "error_type": "unexpected_actual_user_reviewer", "row_number": index, "blind_review_id": blind_id, "value": row.get("actual_user_reviewer")})
        if row.get("filled_by") != "codex_proxy":
            errors.append({"target_name": target_name, "error_type": "unexpected_filled_by", "row_number": index, "blind_review_id": blind_id, "value": row.get("filled_by")})
        forbidden = row.get("deployable_evidence_after_label_lock", {}).get("forbidden_as_posterior_input", {})
        for key in [
            "v3_review_fields",
            "sampling_category_hidden",
            "expected_v3_role_hidden",
            "queue_kind_hidden",
            "geometry_status_hidden",
            "label_match_status_hidden",
            "rank_band_hidden",
            "endpoint_flag_pattern_hidden",
            "audit_packet_paths",
            "multi_view_as_model_input",
        ]:
            if forbidden.get(key) is not True:
                errors.append({"target_name": target_name, "error_type": "missing_forbidden_flag", "field": key, "row_number": index, "blind_review_id": blind_id})
        if row.get("audit_only_v3_review_fields", {}).get("not_model_input") is not True:
            errors.append({"target_name": target_name, "error_type": "v3_review_fields_not_audit_only", "row_number": index, "blind_review_id": blind_id})
    return errors


def per_target_decision(target_name: str, summaries: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    original = next(item for item in summaries if item["slice_name"] == "original_v3")
    strict = choose_candidate(summaries, "strict_candidate")
    diagnostic = choose_candidate(summaries, "diagnostic_candidate")
    geometry_only = choose_candidate(summaries, "geometry_only_candidate")
    if errors:
        status = "target_independence_audit_errors"
        decision = "Fix row validation errors before using v3 target slices."
        next_step = "fix_reliability_target_v3_target_independence_errors"
    elif strict:
        status = "strict_controlled_slice_ready"
        decision = "A strict v3 controlled slice clears hidden provenance, endpoint pattern, construction, and object-label shortcut checks."
        next_step = "reliability_target_v3_source_feature_join_then_posterior_smoke"
    elif diagnostic:
        status = "diagnostic_slice_only"
        decision = "A diagnostic v3 slice clears hidden provenance, endpoint, and construction checks but still has object-label risk or insufficient strict mass."
        next_step = "reliability_target_v3_path_decision"
    elif geometry_only:
        status = "geometry_only_slice_only"
        decision = "The only usable signal is geometry-aligned; this is not enough for a factorized reliability posterior claim."
        next_step = "reliability_target_v3_path_decision"
    else:
        status = "blocked_no_controlled_slice"
        decision = "No strict or diagnostic controlled slice exists."
        next_step = "reliability_target_v3_path_decision"
    return {
        "target_name": target_name,
        "status": status,
        "decision": decision,
        "next_step": next_step,
        "original": original,
        "recommended_strict_slice": strict,
        "recommended_diagnostic_slice": diagnostic,
        "recommended_geometry_only_slice": geometry_only,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Reliability Target V3 Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage target audit.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- V3 labels are user-requested Codex proxy labels, not independent human annotation.",
        "- Hidden provenance/sampling metadata is used only after label lock for audit and slice construction.",
        "- V3 review fields, hidden buckets, audit packet paths, and multi-view evidence are not posterior inputs.",
        "- Geometry alignment risk is reported separately from hidden provenance and object-label shortcut risk.",
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
        "| Target | Status | Rows | Pos | Neg | Strict Slice | Diagnostic Slice | Geometry-Only Slice |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        strict = decision.get("recommended_strict_slice")
        diagnostic = decision.get("recommended_diagnostic_slice")
        geometry_only = decision.get("recommended_geometry_only_slice")
        lines.append(
            f"| `{target_name}` | `{decision['status']}` | {original['rows']} | {original['positive']} | {original['negative']} | "
            f"`{strict['slice_name'] if strict else 'none'}` | "
            f"`{diagnostic['slice_name'] if diagnostic else 'none'}` | "
            f"`{geometry_only['slice_name'] if geometry_only else 'none'}` |"
        )
    lines.extend(
        [
            "",
            "## Original Target Risks",
            "",
            "| Target | Risk Mode | Key | Majority Acc | NMI | Pos Rate Range |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    risk_fields = [
        ("hidden_provenance", "top_hidden_provenance_risks"),
        ("endpoint_pattern", "top_endpoint_pattern_risks"),
        ("construction", "top_construction_risks"),
        ("expected_geometry_alignment", "top_expected_geometry_alignment_risks"),
        ("visible_relation_surface", "top_visible_relation_surface_risks"),
        ("visible_object_identity", "top_visible_object_identity_risks"),
    ]
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        for risk_mode, field in risk_fields:
            risks = original[field]
            if not risks:
                lines.append(f"| `{target_name}` | `{risk_mode}` | none | 0.0000 | 0.0000 | 0.0000 |")
            for item in risks:
                lines.append(
                    f"| `{target_name}` | `{risk_mode}` | `{item['group_key']}` | "
                    f"{item['majority_rule_accuracy']:.4f} | "
                    f"{item['normalized_mutual_information']:.4f} | "
                    f"{item['positive_rate_range']:.4f} |"
                )
    lines.extend(
        [
            "",
            "## Controlled Slices",
            "",
            "| Target | Slice | Rows | Pos | Neg | Hidden | Endpoint | Construction | Geometry Align | Object Risk | Strict | Diagnostic |",
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
            f"{item['hidden_provenance_risk_count']} | {item['endpoint_pattern_risk_count']} | "
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

    all_slice_summaries: list[dict[str, Any]] = []
    all_group_rows: list[dict[str, Any]] = []
    all_group_summaries: list[dict[str, Any]] = []
    all_validation_errors: list[dict[str, Any]] = []
    input_counts: dict[str, Any] = {}
    input_paths: dict[str, str] = {"ingestion_summary": rel_path(ingestion_dir / "summary.json")}
    target_decisions: dict[str, Any] = {}

    for target_name, filename in TARGET_INPUTS.items():
        input_path = ingestion_dir / filename
        input_paths[target_name] = rel_path(input_path)
        rows = read_jsonl(input_path)
        validation_errors = validate_rows(target_name, rows)
        all_validation_errors.extend(validation_errors)
        slice_summaries, group_rows, group_summaries = build_slices(target_name, rows, output_dir)
        all_slice_summaries.extend(slice_summaries)
        all_group_rows.extend(group_rows)
        all_group_summaries.extend(group_summaries)
        target_decisions[target_name] = per_target_decision(target_name, slice_summaries, validation_errors)
        input_counts[target_name] = counts_for(rows) | {"validation_errors": len(validation_errors)}

    relation_decision = target_decisions[RELIABILITY_TARGET]
    relation_strict = relation_decision["recommended_strict_slice"]
    relation_diagnostic = relation_decision["recommended_diagnostic_slice"]
    relation_geometry_only = relation_decision["recommended_geometry_only_slice"]

    if all_validation_errors:
        status = "h002_reliability_target_v3_target_independence_audit_errors"
        decision = "Fix target-independence audit validation errors before any path decision."
        next_todo = "fix_reliability_target_v3_target_independence_audit_errors"
    elif relation_strict:
        status = "h002_reliability_target_v3_target_independence_audit_strict_slice_ready"
        decision = "A strict relation reliability slice exists. Posterior smoke may proceed only on that train-only slice."
        next_todo = "reliability_target_v3_source_feature_join_then_posterior_smoke"
    elif relation_diagnostic:
        status = "h002_reliability_target_v3_target_independence_audit_diagnostic_slice_only"
        decision = "A diagnostic relation reliability slice exists, but strict posterior method validation remains blocked."
        next_todo = "reliability_target_v3_path_decision"
    elif relation_geometry_only:
        status = "h002_reliability_target_v3_target_independence_audit_geometry_only_slice_only"
        decision = "Only geometry-aligned slices are usable; factorized reliability posterior remains blocked."
        next_todo = "reliability_target_v3_path_decision"
    else:
        status = "h002_reliability_target_v3_target_independence_audit_blocked_no_controlled_slice"
        decision = "No controlled relation reliability slice clears hidden, endpoint, construction, and object-label shortcut checks."
        next_todo = "reliability_target_v3_path_decision"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "slice_summaries": output_dir / "slice_summaries.csv",
        "group_summaries": output_dir / "group_summaries.csv",
        "group_table": output_dir / "group_table.csv",
        "target_slices": output_dir / "target_slices",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": "h002_reliability_target_v3_target_independence_audit_summary_v1",
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
            "label_source": "codex_proxy_reliability_target_v3_user_requested",
            "actual_user_reviewer": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_metadata_used_for_audit_only": True,
            "review_fields_used_for_audit_only": True,
            "multi_view_as_model_input": False,
            "geometry_alignment_separated_from_shortcut_risks": True,
        },
        "risk_thresholds": {
            "normalized_mutual_information": RISK_NMI_THRESHOLD,
            "majority_rule_accuracy": RISK_MAJORITY_THRESHOLD,
            "positive_rate_range": RISK_POSITIVE_RATE_RANGE_THRESHOLD,
            "large_group_rows": RISK_LARGE_GROUP_ROWS,
            "large_group_purity": RISK_LARGE_GROUP_PURITY,
            "min_strict_rows": MIN_STRICT_ROWS,
            "min_strict_per_class": MIN_STRICT_PER_CLASS,
            "min_diagnostic_rows": MIN_DIAGNOSTIC_ROWS,
            "min_diagnostic_per_class": MIN_DIAGNOSTIC_PER_CLASS,
        },
        "ingestion_status": ingestion_summary.get("status"),
        "input_counts": input_counts,
        "validation_errors": len(all_validation_errors),
        "hidden_provenance_keys": HIDDEN_PROVENANCE_KEYS,
        "endpoint_pattern_keys": ENDPOINT_PATTERN_KEYS,
        "construction_keys": CONSTRUCTION_KEYS,
        "expected_geometry_alignment_keys": EXPECTED_GEOMETRY_ALIGNMENT_KEYS,
        "visible_relation_keys": VISIBLE_RELATION_KEYS,
        "visible_object_keys": VISIBLE_OBJECT_KEYS,
        "target_decisions": target_decisions,
        "strict_ready_targets": [target for target, decision_item in target_decisions.items() if decision_item["recommended_strict_slice"]],
        "diagnostic_only_targets": [
            target
            for target, decision_item in target_decisions.items()
            if not decision_item["recommended_strict_slice"] and decision_item["recommended_diagnostic_slice"]
        ],
        "blocked_targets": [
            target
            for target, decision_item in target_decisions.items()
            if not decision_item["recommended_strict_slice"] and not decision_item["recommended_diagnostic_slice"]
        ],
        "slice_summaries": all_slice_summaries,
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_csv(
        output_paths["slice_summaries"],
        [
            {
                "target_name": item["target_name"],
                "slice_name": item["slice_name"],
                "rows": item["rows"],
                "positive": item["positive"],
                "negative": item["negative"],
                "min_class": item["min_class"],
                "hidden_provenance_risk_count": item["hidden_provenance_risk_count"],
                "endpoint_pattern_risk_count": item["endpoint_pattern_risk_count"],
                "construction_risk_count": item["construction_risk_count"],
                "expected_geometry_alignment_risk_count": item["expected_geometry_alignment_risk_count"],
                "visible_relation_surface_risk_count": item["visible_relation_surface_risk_count"],
                "visible_object_identity_risk_count": item["visible_object_identity_risk_count"],
                "strict_size_ready": item["strict_size_ready"],
                "diagnostic_size_ready": item["diagnostic_size_ready"],
                "strict_candidate": item["strict_candidate"],
                "diagnostic_candidate": item["diagnostic_candidate"],
                "geometry_only_candidate": item["geometry_only_candidate"],
                "balanced_keys": "|".join(item["balanced_keys"]),
                "path": item["path"],
            }
            for item in all_slice_summaries
        ],
    )
    write_csv(output_paths["group_summaries"], all_group_summaries)
    write_csv(output_paths["group_table"], all_group_rows)
    write_jsonl(output_paths["validation_errors"], all_validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    relation = summary["target_decisions"][RELIABILITY_TARGET]
    original = relation["original"]
    strict = relation.get("recommended_strict_slice")
    diagnostic = relation.get("recommended_diagnostic_slice")
    print(
        f"status={summary['status']} relation_rows={original['rows']} "
        f"relation_pos={original['positive']} relation_neg={original['negative']} "
        f"errors={summary['validation_errors']} "
        f"relation_strict={strict['slice_name'] if strict else 'none'} "
        f"relation_diagnostic={diagnostic['slice_name'] if diagnostic else 'none'} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
