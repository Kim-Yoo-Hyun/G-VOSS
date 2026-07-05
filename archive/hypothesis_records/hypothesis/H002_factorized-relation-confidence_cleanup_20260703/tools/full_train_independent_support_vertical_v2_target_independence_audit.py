#!/usr/bin/env python3
"""Audit v2 support/vertical target independence and controlled slices."""

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

DEFAULT_INGESTION_DIR = RGA_ROOT / "independent_support_vertical_v2_label_ingestion_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_target_independence_audit_codex_ver"

TARGET_INPUTS = {
    "geometry_validity_target_v2": "geometry_validity_posterior_rows_v2.jsonl",
    "relation_reliability_target_v2": "relation_reliability_posterior_rows_v2.jsonl",
}

HARMFUL_PRIOR_CARRYOVER_KEYS = [
    "relation_validity_label_hidden",
    "label_use_hidden",
    "posterior_target_y_hidden",
]

CONSTRUCTION_KEYS = [
    "rank_band_hidden",
    "proposed_audit_role_hidden",
    "queue_kind_hidden",
    "label_match_status_hidden",
]

EXPECTED_GEOMETRY_ALIGNMENT_KEYS = [
    "geometry_status_hidden",
]

VISIBLE_NON_TARGET_KEYS = [
    "predicate_family",
    "predicate_label",
    "evidence_packet_status",
]

RISK_NMI_THRESHOLD = 0.20
RISK_MAJORITY_THRESHOLD = 0.85
RISK_POSITIVE_RATE_RANGE_THRESHOLD = 0.70
RISK_LARGE_GROUP_ROWS = 10
RISK_LARGE_GROUP_PURITY = 0.95

MIN_CANDIDATE_ROWS = 50
MIN_CANDIDATE_PER_CLASS = 20

SLICE_SPECS = {
    "original_v2": {
        "balanced_keys": [],
        "reason": "full v2 binary target",
        "priority": 99,
    },
    "prior_relation_validity_balanced_v2": {
        "balanced_keys": ["relation_validity_label_hidden"],
        "reason": "matched positives/negatives within prior hidden relation-validity label",
        "priority": 10,
    },
    "prior_label_use_balanced_v2": {
        "balanced_keys": ["label_use_hidden"],
        "reason": "matched positives/negatives within prior hidden label-use bucket",
        "priority": 10,
    },
    "prior_target_y_balanced_v2": {
        "balanced_keys": ["posterior_target_y_hidden"],
        "reason": "matched positives/negatives within prior hidden target-y bucket",
        "priority": 10,
    },
    "rank_band_balanced_v2": {
        "balanced_keys": ["rank_band_hidden"],
        "reason": "matched positives/negatives within hidden semantic rank band",
        "priority": 1,
    },
    "queue_balanced_v2": {
        "balanced_keys": ["queue_kind_hidden"],
        "reason": "matched positives/negatives within hidden HL/LH queue",
        "priority": 2,
    },
    "role_balanced_v2": {
        "balanced_keys": ["proposed_audit_role_hidden"],
        "reason": "matched positives/negatives within hidden proposed audit role",
        "priority": 3,
    },
    "label_match_balanced_v2": {
        "balanced_keys": ["label_match_status_hidden"],
        "reason": "matched positives/negatives within hidden label-match status",
        "priority": 4,
    },
    "geometry_status_balanced_v2": {
        "balanced_keys": ["geometry_status_hidden"],
        "reason": "matched positives/negatives within expected hidden geometry status",
        "priority": 5,
    },
    "family_balanced_v2": {
        "balanced_keys": ["predicate_family"],
        "reason": "matched positives/negatives within visible predicate family",
        "priority": 6,
    },
    "predicate_balanced_v2": {
        "balanced_keys": ["predicate_label"],
        "reason": "matched positives/negatives within visible predicate label",
        "priority": 7,
    },
    "rank_family_balanced_v2": {
        "balanced_keys": ["rank_band_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden rank band and visible family",
        "priority": 8,
    },
    "queue_family_balanced_v2": {
        "balanced_keys": ["queue_kind_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden queue and visible family",
        "priority": 9,
    },
    "role_family_balanced_v2": {
        "balanced_keys": ["proposed_audit_role_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden role and visible family",
        "priority": 9,
    },
    "prior_label_rank_balanced_v2": {
        "balanced_keys": ["relation_validity_label_hidden", "rank_band_hidden"],
        "reason": "matched positives/negatives within prior label and rank band",
        "priority": 11,
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
    source_scores = deployable.get("source_semantic_and_geometry_scores_hidden_from_labeler_until_lock", {})
    if key in source_scores:
        return str(source_scores.get(key))
    return "missing"


def semantic_rank(row: dict[str, Any]) -> float:
    hidden = row.get("hidden_audit_metadata_post_label_only", {})
    value = hidden.get("semantic_rank_hidden")
    if value is None:
        value = (
            row.get("deployable_evidence_after_label_lock", {})
            .get("source_semantic_and_geometry_scores_hidden_from_labeler_until_lock", {})
            .get("semantic_rank")
        )
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1e12


def stable_key(row: dict[str, Any]) -> tuple[float, str]:
    return semantic_rank(row), str(row.get("prediction_id", row.get("blind_review_id")))


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
    by_group: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_group[group_value(row, group_key)].append(row)

    total_counts = Counter(target_y(row) for row in rows)
    overall_entropy = entropy_from_counts(total_counts)
    weighted_conditional_entropy = 0.0
    majority_correct = 0
    positive_rates: list[float] = []
    large_group_high_purity = False
    table: list[dict[str, Any]] = []

    for value, group_rows in sorted(by_group.items()):
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
    positive_rate_min = min(positive_rates) if positive_rates else 0.0
    positive_rate_max = max(positive_rates) if positive_rates else 0.0
    positive_rate_range = positive_rate_max - positive_rate_min
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
        "groups": len(by_group),
        "rows": len(rows),
        "overall_positive": total_counts[1],
        "overall_negative": total_counts[0],
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": weighted_conditional_entropy,
        "mutual_information_bits": mutual_information,
        "normalized_mutual_information": nmi,
        "majority_rule_accuracy": majority_rule_accuracy,
        "positive_rate_min": positive_rate_min,
        "positive_rate_max": positive_rate_max,
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
    group_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    key_groups = [
        ("harmful_prior_carryover", "hidden_post_label_audit", HARMFUL_PRIOR_CARRYOVER_KEYS),
        ("construction", "hidden_post_label_audit", CONSTRUCTION_KEYS),
        ("expected_geometry_alignment", "hidden_post_label_audit", EXPECTED_GEOMETRY_ALIGNMENT_KEYS),
        ("visible_non_target", "visible_non_target_surface", VISIBLE_NON_TARGET_KEYS),
    ]
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

    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[tuple(group_value(row, key) for key in keys)].append(row)

    selected: list[dict[str, Any]] = []
    for _, group_rows in sorted(groups.items()):
        positives = sorted([row for row in group_rows if target_y(row) == 1], key=stable_key)
        negatives = sorted([row for row in group_rows if target_y(row) == 0], key=stable_key)
        count = min(len(positives), len(negatives))
        selected.extend(clone_for_slice(row, target_name, slice_name, spec) for row in positives[:count])
        selected.extend(clone_for_slice(row, target_name, slice_name, spec) for row in negatives[:count])
    return sorted(selected, key=stable_key)


def counts_for(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(target_y(row) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "by_family": dict(sorted(Counter(group_value(row, "predicate_family") for row in rows).items())),
        "by_predicate": dict(sorted(Counter(group_value(row, "predicate_label") for row in rows).items())),
        "by_rank_band": dict(sorted(Counter(group_value(row, "rank_band_hidden") for row in rows).items())),
        "by_role": dict(sorted(Counter(group_value(row, "proposed_audit_role_hidden") for row in rows).items())),
        "by_geometry_status": dict(sorted(Counter(group_value(row, "geometry_status_hidden") for row in rows).items())),
        "by_prior_relation_validity": dict(sorted(Counter(group_value(row, "relation_validity_label_hidden") for row in rows).items())),
    }


def top_risk_rows(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "group_key": item["group_key"],
            "majority_rule_accuracy": item["majority_rule_accuracy"],
            "normalized_mutual_information": item["normalized_mutual_information"],
            "positive_rate_range": item["positive_rate_range"],
        }
        for item in risks[:6]
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
    harmful_risks = risk_summaries(summaries, "harmful_prior_carryover")
    construction_risks = risk_summaries(summaries, "construction")
    geometry_alignment_risks = risk_summaries(summaries, "expected_geometry_alignment")
    visible_risks = risk_summaries(summaries, "visible_non_target")
    min_class = min(counts["positive"], counts["negative"]) if rows else 0
    size_ready = counts["rows"] >= MIN_CANDIDATE_ROWS and min_class >= MIN_CANDIDATE_PER_CLASS
    strict_candidate = size_ready and len(harmful_risks) == 0 and len(construction_risks) == 0
    clean_plus_visible_candidate = strict_candidate and len(visible_risks) == 0
    construction_candidate = size_ready and len(construction_risks) == 0 and len(harmful_risks) > 0
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
        "min_class": min_class,
        "size_ready": size_ready,
        "harmful_prior_risk_count": len(harmful_risks),
        "construction_risk_count": len(construction_risks),
        "expected_geometry_alignment_risk_count": len(geometry_alignment_risks),
        "visible_non_target_risk_count": len(visible_risks),
        "strict_candidate": strict_candidate,
        "clean_plus_visible_candidate": clean_plus_visible_candidate,
        "construction_only_candidate": construction_candidate,
        "top_harmful_prior_risks": top_risk_rows(harmful_risks),
        "top_construction_risks": top_risk_rows(construction_risks),
        "top_expected_geometry_alignment": top_risk_rows(geometry_alignment_risks),
        "top_visible_non_target_risks": top_risk_rows(visible_risks),
        "counts": counts,
    }


def build_slices_for_target(
    target_name: str,
    rows: list[dict[str, Any]],
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    slice_dir = output_dir / "target_slices" / target_name
    slice_summaries: list[dict[str, Any]] = []
    group_table: list[dict[str, Any]] = []
    group_summary_rows: list[dict[str, Any]] = []
    for slice_name, spec in SLICE_SPECS.items():
        slice_rows = balanced_slice(rows, target_name, slice_name, spec)
        path = slice_dir / f"{slice_name}.jsonl"
        write_jsonl(path, slice_rows)
        groups, summaries = all_group_summaries(slice_rows, target_name, slice_name)
        group_table.extend(groups)
        group_summary_rows.extend(summaries)
        slice_summaries.append(slice_summary(target_name, slice_name, spec, slice_rows, summaries, path))
    return slice_summaries, group_table, group_summary_rows


def choose_candidate(slice_summaries: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    candidates = [item for item in slice_summaries if item[key]]
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
            errors.append(
                {
                    "target_name": target_name,
                    "error_type": "unexpected_target_name",
                    "row_number": index,
                    "blind_review_id": blind_id,
                    "value": row.get("target_name"),
                }
            )
        if row.get("predicate_family") not in {"support_contact", "relative_vertical"}:
            errors.append(
                {
                    "target_name": target_name,
                    "error_type": "row_outside_support_vertical_scope",
                    "row_number": index,
                    "blind_review_id": blind_id,
                    "predicate_family": row.get("predicate_family"),
                }
            )
        if row.get("human_confirmed") is not False:
            errors.append(
                {
                    "target_name": target_name,
                    "error_type": "unexpected_human_confirmed_flag",
                    "row_number": index,
                    "blind_review_id": blind_id,
                    "human_confirmed": row.get("human_confirmed"),
                }
            )
        if "audit_only_target_derivation_fields" not in row:
            errors.append({"target_name": target_name, "error_type": "missing_audit_only_target_derivation_fields", "row_number": index, "blind_review_id": blind_id})
    return errors


def per_target_decision(target_name: str, summaries: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    original = next(item for item in summaries if item["slice_name"] == "original_v2")
    strict = choose_candidate(summaries, "strict_candidate")
    clean = choose_candidate(summaries, "clean_plus_visible_candidate")
    construction = choose_candidate(summaries, "construction_only_candidate")
    if errors:
        status = "target_independence_audit_errors"
        decision = "Fix row validation errors before using any v2 target slice."
        next_step = "fix_v2_target_independence_audit_errors"
    elif strict:
        status = "strict_controlled_slice_ready"
        decision = (
            "A strict controlled slice clears harmful prior-label carryover and construction-risk checks. "
            "Posterior smoke may proceed only on this train-only slice."
        )
        next_step = "v2_controlled_posterior_smoke"
    elif construction:
        status = "strict_blocked_construction_slice_available"
        decision = (
            "No strict slice clears harmful prior-label carryover. A construction-only slice exists for "
            "plumbing/error diagnostics, but not method validation."
        )
        next_step = "revise_v2_target_or_collect_independent_labels"
    else:
        status = "blocked_no_controlled_slice"
        decision = "No size-ready strict or construction-only controlled slice exists."
        next_step = "revise_v2_target_or_collect_independent_labels"
    return {
        "target_name": target_name,
        "status": status,
        "decision": decision,
        "next_step": next_step,
        "original": original,
        "recommended_strict_slice": strict,
        "recommended_clean_plus_visible_slice": clean,
        "recommended_construction_slice": construction,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Support/Vertical V2 Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage target audit.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Hidden metadata is used only after label lock for audit and controlled-slice construction.",
        "- Harmful prior carryover is separated from expected geometry alignment.",
        "- Geometry-status alignment is reported but not used as the main harmful-carryover blocker.",
        "- Codex labels are not human-confirmed paper evidence.",
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
        "| Target | Status | Rows | Pos | Neg | Strict Slice | Construction Slice |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        strict = decision.get("recommended_strict_slice")
        construction = decision.get("recommended_construction_slice")
        lines.append(
            f"| `{target_name}` | `{decision['status']}` | {original['rows']} | {original['positive']} | {original['negative']} | "
            f"`{strict['slice_name'] if strict else 'none'}` | `{construction['slice_name'] if construction else 'none'}` |"
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
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        for risk_mode, key in [
            ("harmful_prior_carryover", "top_harmful_prior_risks"),
            ("construction", "top_construction_risks"),
            ("expected_geometry_alignment", "top_expected_geometry_alignment"),
            ("visible_non_target", "top_visible_non_target_risks"),
        ]:
            risks = original[key]
            if not risks:
                lines.append(f"| `{target_name}` | `{risk_mode}` | none | 0.0000 | 0.0000 | 0.0000 |")
            for item in risks:
                lines.append(
                    f"| `{target_name}` | `{risk_mode}` | `{item['group_key']}` | "
                    f"{item['majority_rule_accuracy']:.4f} | {item['normalized_mutual_information']:.4f} | "
                    f"{item['positive_rate_range']:.4f} |"
                )
    lines.extend(
        [
            "",
            "## Controlled Slices",
            "",
            "| Target | Slice | Rows | Pos | Neg | Harmful Risks | Construction Risks | Geometry Align | Visible Risks | Strict | Construction Only |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for item in sorted(
        summary["slice_summaries"],
        key=lambda row: (
            row["target_name"],
            not row["strict_candidate"],
            not row["construction_only_candidate"],
            row["priority"],
            -row["rows"],
        ),
    ):
        lines.append(
            f"| `{item['target_name']}` | `{item['slice_name']}` | {item['rows']} | {item['positive']} | {item['negative']} | "
            f"{item['harmful_prior_risk_count']} | {item['construction_risk_count']} | "
            f"{item['expected_geometry_alignment_risk_count']} | {item['visible_non_target_risk_count']} | "
            f"`{item['strict_candidate']}` | `{item['construction_only_candidate']}` |"
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
    target_decisions: dict[str, Any] = {}
    input_counts: dict[str, Any] = {}
    input_paths: dict[str, str] = {"ingestion_summary": rel_path(ingestion_dir / "summary.json")}

    for target_name, filename in TARGET_INPUTS.items():
        input_path = ingestion_dir / filename
        input_paths[target_name] = rel_path(input_path)
        rows = read_jsonl(input_path)
        validation_errors = validate_rows(target_name, rows)
        all_validation_errors.extend(validation_errors)
        slice_summaries, group_rows, group_summaries = build_slices_for_target(target_name, rows, output_dir)
        all_slice_summaries.extend(slice_summaries)
        all_group_rows.extend(group_rows)
        all_group_summaries.extend(group_summaries)
        target_decisions[target_name] = per_target_decision(target_name, slice_summaries, validation_errors)
        counts = Counter(target_y(row) for row in rows)
        input_counts[target_name] = {
            "rows": len(rows),
            "positive": counts[1],
            "negative": counts[0],
            "validation_errors": len(validation_errors),
        }

    strict_ready_targets = [
        target for target, decision in target_decisions.items() if decision["recommended_strict_slice"] is not None
    ]
    construction_only_targets = [
        target
        for target, decision in target_decisions.items()
        if decision["recommended_strict_slice"] is None and decision["recommended_construction_slice"] is not None
    ]
    blocked_targets = [
        target
        for target, decision in target_decisions.items()
        if decision["recommended_strict_slice"] is None and decision["recommended_construction_slice"] is None
    ]

    if all_validation_errors:
        status = "full_train_independent_support_vertical_v2_target_independence_audit_errors"
        decision = "Fix validation errors before any v2 target slice can be used."
        next_todo = "fix_full_train_independent_support_vertical_v2_target_independence_audit_errors"
    elif "relation_reliability_target_v2" in strict_ready_targets:
        status = "full_train_independent_support_vertical_v2_target_independence_audit_relation_strict_slice_ready"
        decision = (
            "A strict relation-reliability slice exists. Posterior smoke may proceed only on that "
            "train-only slice; geometry-validity target remains diagnostic unless separately selected."
        )
        next_todo = "full_train_independent_support_vertical_v2_controlled_posterior_smoke"
    elif construction_only_targets:
        status = "full_train_independent_support_vertical_v2_target_independence_audit_strict_blocked_construction_slice_available"
        decision = (
            "No strict relation-reliability slice clears harmful prior-label carryover. Construction-only "
            "diagnostic slices may be used for plumbing/error analysis, but posterior method validation "
            "remains blocked."
        )
        next_todo = "revise_full_train_independent_support_vertical_v2_target_or_collect_independent_labels"
    else:
        status = "full_train_independent_support_vertical_v2_target_independence_audit_blocked"
        decision = (
            "No size-ready strict or construction-only controlled slice exists for v2 relation reliability."
        )
        next_todo = "revise_full_train_independent_support_vertical_v2_target_or_collect_independent_labels"

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
        "schema_version": "h002_support_vertical_v2_target_independence_audit_summary_v1",
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
            "selected_scope": ["relative_vertical", "support_contact"],
            "label_source": "codex_ver_support_vertical_v2_factual_axes_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_metadata_used_for_audit_only": True,
            "target_derivation_fields_used_for_audit_only": True,
            "multi_view_as_model_input": False,
            "expected_geometry_alignment_separated_from_harmful_carryover": True,
        },
        "risk_thresholds": {
            "normalized_mutual_information": RISK_NMI_THRESHOLD,
            "majority_rule_accuracy": RISK_MAJORITY_THRESHOLD,
            "positive_rate_range": RISK_POSITIVE_RATE_RANGE_THRESHOLD,
            "large_group_rows": RISK_LARGE_GROUP_ROWS,
            "large_group_purity": RISK_LARGE_GROUP_PURITY,
            "min_candidate_rows": MIN_CANDIDATE_ROWS,
            "min_candidate_per_class": MIN_CANDIDATE_PER_CLASS,
        },
        "ingestion_status": ingestion_summary.get("status"),
        "input_counts": input_counts,
        "validation_errors": len(all_validation_errors),
        "harmful_prior_carryover_keys": HARMFUL_PRIOR_CARRYOVER_KEYS,
        "construction_keys": CONSTRUCTION_KEYS,
        "expected_geometry_alignment_keys": EXPECTED_GEOMETRY_ALIGNMENT_KEYS,
        "visible_non_target_keys": VISIBLE_NON_TARGET_KEYS,
        "target_decisions": target_decisions,
        "strict_ready_targets": strict_ready_targets,
        "construction_only_targets": construction_only_targets,
        "blocked_targets": blocked_targets,
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
                "harmful_prior_risk_count": item["harmful_prior_risk_count"],
                "construction_risk_count": item["construction_risk_count"],
                "expected_geometry_alignment_risk_count": item["expected_geometry_alignment_risk_count"],
                "visible_non_target_risk_count": item["visible_non_target_risk_count"],
                "size_ready": item["size_ready"],
                "strict_candidate": item["strict_candidate"],
                "clean_plus_visible_candidate": item["clean_plus_visible_candidate"],
                "construction_only_candidate": item["construction_only_candidate"],
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
    rel_decision = summary["target_decisions"]["relation_reliability_target_v2"]
    strict = rel_decision.get("recommended_strict_slice")
    construction = rel_decision.get("recommended_construction_slice")
    counts = summary["input_counts"]["relation_reliability_target_v2"]
    print(
        f"status={summary['status']} relation_rows={counts['rows']} "
        f"relation_pos={counts['positive']} relation_neg={counts['negative']} "
        f"errors={summary['validation_errors']} "
        f"relation_strict={strict['slice_name'] if strict else 'none'} "
        f"relation_construction={construction['slice_name'] if construction else 'none'} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
