#!/usr/bin/env python3
"""Audit endpoint-controlled target independence for H002."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import full_train_independent_support_vertical_v2_target_independence_audit as base


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_INGESTION_DIR = RGA_ROOT / "endpoint_controlled_label_ingestion_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "endpoint_controlled_target_independence_audit_codex_proxy_user_requested"

GEOMETRY_TARGET = "geometry_validity_endpoint_controlled_target"
RELIABILITY_TARGET = "relation_reliability_endpoint_controlled_target"

TARGET_INPUTS = {
    GEOMETRY_TARGET: "geometry_validity_endpoint_controlled_posterior_rows.jsonl",
    RELIABILITY_TARGET: "relation_reliability_endpoint_controlled_posterior_rows.jsonl",
}

PRIOR_CARRYOVER_KEYS = [
    "relation_validity_label_hidden",
    "label_use_hidden",
    "posterior_target_y_hidden",
]

CONSTRUCTION_KEYS = [
    "queue_kind_hidden",
    "proposed_audit_role_hidden",
    "label_match_status_hidden",
    "rank_band_hidden",
]

EXPECTED_GEOMETRY_ALIGNMENT_KEYS = [
    "geometry_status_hidden",
]

ENDPOINT_CONTROL_KEYS = [
    "endpoint_flag_pattern_hidden",
    "expected_label_proxy_hidden",
    "needed_label_proxy_hidden",
    "selected_source_hidden",
]

VISIBLE_NON_TARGET_KEYS = [
    "predicate_family",
    "predicate_label",
    "evidence_packet_status",
]

MIN_POSTERIOR_ROWS = 50
MIN_POSTERIOR_PER_CLASS = 20
MIN_POSITIVES_FOR_SMOKE = 10

SLICE_SPECS = {
    "original_endpoint_controlled": {
        "balanced_keys": [],
        "reason": "full endpoint-controlled binary target",
        "priority": 99,
    },
    "queue_balanced_endpoint_controlled": {
        "balanced_keys": ["queue_kind_hidden"],
        "reason": "matched positives/negatives within hidden HL/LH queue",
        "priority": 1,
    },
    "role_balanced_endpoint_controlled": {
        "balanced_keys": ["proposed_audit_role_hidden"],
        "reason": "matched positives/negatives within hidden proposed audit role",
        "priority": 2,
    },
    "rank_balanced_endpoint_controlled": {
        "balanced_keys": ["rank_band_hidden"],
        "reason": "matched positives/negatives within hidden rank band",
        "priority": 3,
    },
    "label_match_balanced_endpoint_controlled": {
        "balanced_keys": ["label_match_status_hidden"],
        "reason": "matched positives/negatives within hidden label-match status",
        "priority": 4,
    },
    "geometry_status_balanced_endpoint_controlled": {
        "balanced_keys": ["geometry_status_hidden"],
        "reason": "matched positives/negatives within hidden geometry status",
        "priority": 5,
    },
    "endpoint_pattern_balanced_endpoint_controlled": {
        "balanced_keys": ["endpoint_flag_pattern_hidden"],
        "reason": "matched positives/negatives within hidden endpoint flag pattern",
        "priority": 6,
    },
    "expected_label_balanced_endpoint_controlled": {
        "balanced_keys": ["expected_label_proxy_hidden"],
        "reason": "matched positives/negatives within hidden expected label proxy",
        "priority": 7,
    },
    "selected_source_balanced_endpoint_controlled": {
        "balanced_keys": ["selected_source_hidden"],
        "reason": "matched positives/negatives within packet-ready vs generated-asset source",
        "priority": 8,
    },
    "family_balanced_endpoint_controlled": {
        "balanced_keys": ["predicate_family"],
        "reason": "matched positives/negatives within visible predicate family",
        "priority": 9,
    },
    "predicate_balanced_endpoint_controlled": {
        "balanced_keys": ["predicate_label"],
        "reason": "matched positives/negatives within visible predicate label",
        "priority": 10,
    },
    "endpoint_family_balanced_endpoint_controlled": {
        "balanced_keys": ["endpoint_flag_pattern_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden endpoint pattern and visible family",
        "priority": 11,
    },
    "queue_family_balanced_endpoint_controlled": {
        "balanced_keys": ["queue_kind_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden queue and visible family",
        "priority": 12,
    },
    "rank_family_balanced_endpoint_controlled": {
        "balanced_keys": ["rank_band_hidden", "predicate_family"],
        "reason": "matched positives/negatives within hidden rank band and visible family",
        "priority": 13,
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
        if row.get("user_requested_proxy_review") is not True:
            errors.append({"target_name": target_name, "error_type": "missing_user_requested_proxy_review", "row_number": index, "blind_review_id": blind_id})
        if row.get("paper_locked") is not False:
            errors.append({"target_name": target_name, "error_type": "unexpected_paper_locked", "row_number": index, "blind_review_id": blind_id, "value": row.get("paper_locked")})
        review_fields = row.get("audit_only_endpoint_controlled_review_fields", {})
        if review_fields.get("not_model_input") is not True:
            errors.append({"target_name": target_name, "error_type": "review_fields_not_marked_audit_only", "row_number": index, "blind_review_id": blind_id})
        forbidden = row.get("deployable_evidence_after_label_lock", {}).get("forbidden_as_posterior_input", {})
        for key in ["endpoint_controlled_review_fields", "hidden_strata", "audit_packet_paths", "multi_view_as_model_input"]:
            if forbidden.get(key) is not True:
                errors.append({"target_name": target_name, "error_type": "missing_forbidden_flag", "field": key, "row_number": index, "blind_review_id": blind_id})
        source_scores = row.get("deployable_evidence_after_label_lock", {}).get(
            "source_semantic_and_geometry_scores_hidden_from_labeler_until_lock", {}
        )
        if source_scores.get("available_in_this_ingestion") is not False:
            errors.append({"target_name": target_name, "error_type": "source_scores_unexpectedly_available", "row_number": index, "blind_review_id": blind_id})
        if "hidden_audit_metadata_post_label_only" not in row:
            errors.append({"target_name": target_name, "error_type": "missing_hidden_audit_metadata", "row_number": index, "blind_review_id": blind_id})
    return errors


def group_value(row: dict[str, Any], key: str) -> str:
    return base.group_value(row, key)


def annotate_group_summary(summary: dict[str, Any]) -> dict[str, Any]:
    rows = int(summary.get("rows", 0))
    pos = int(summary.get("overall_positive", 0))
    neg = int(summary.get("overall_negative", 0))
    min_class = min(pos, neg)
    majority_baseline = max(pos, neg) / rows if rows else 0.0
    summary["target_majority_baseline"] = majority_baseline
    summary["majority_excess_over_baseline"] = float(summary.get("majority_rule_accuracy", 0.0)) - majority_baseline
    summary["positive_sparse_dominated"] = min_class < MIN_POSITIVES_FOR_SMOKE
    summary["shortcut_flag_debiased"] = (
        float(summary.get("normalized_mutual_information", 0.0)) >= base.RISK_NMI_THRESHOLD
        or float(summary.get("positive_rate_range", 0.0)) >= base.RISK_POSITIVE_RATE_RANGE_THRESHOLD
        or bool(summary.get("large_group_high_purity"))
        or float(summary.get("majority_excess_over_baseline", 0.0)) >= 0.10
    )
    return summary


def all_group_summaries(
    rows: list[dict[str, Any]],
    target_name: str,
    slice_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    group_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    key_groups = [
        ("prior_carryover", "hidden_post_label_audit", PRIOR_CARRYOVER_KEYS),
        ("construction", "hidden_post_label_audit", CONSTRUCTION_KEYS),
        ("expected_geometry_alignment", "hidden_post_label_audit", EXPECTED_GEOMETRY_ALIGNMENT_KEYS),
        ("endpoint_control", "hidden_post_label_audit", ENDPOINT_CONTROL_KEYS),
        ("visible_non_target", "visible_non_target_surface", VISIBLE_NON_TARGET_KEYS),
    ]
    for risk_mode, source, keys in key_groups:
        for key in keys:
            table, summary = base.group_summary(rows, key, source, risk_mode, target_name, slice_name)
            group_rows.extend(table)
            summaries.append(annotate_group_summary(summary))
    return group_rows, summaries


def risk_summaries(summaries: list[dict[str, Any]], risk_mode: str) -> list[dict[str, Any]]:
    output = [summary for summary in summaries if summary["risk_mode"] == risk_mode and summary["shortcut_flag_debiased"]]
    return sorted(
        output,
        key=lambda item: (
            -float(item["normalized_mutual_information"]),
            -float(item["majority_excess_over_baseline"]),
            -float(item["positive_rate_range"]),
        ),
    )


def clone_for_slice(row: dict[str, Any], target_name: str, slice_name: str, spec: dict[str, Any]) -> dict[str, Any]:
    copied = dict(row)
    copied["target_name_for_audit"] = target_name
    copied["target_slice_name"] = slice_name
    copied["target_slice_reason"] = spec["reason"]
    copied["balanced_keys"] = spec["balanced_keys"]
    copied["audit_selection_only"] = True
    copied["paper_evidence_allowed"] = False
    return copied


def stable_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("scan_id", "")), str(row.get("prediction_id", row.get("blind_review_id", "")))


def balanced_slice(rows: list[dict[str, Any]], target_name: str, slice_name: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    keys = list(spec["balanced_keys"])
    if not keys:
        return [clone_for_slice(row, target_name, slice_name, spec) for row in sorted(rows, key=stable_key)]

    groups: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(tuple(group_value(row, key) for key in keys), []).append(row)

    selected: list[dict[str, Any]] = []
    for _, group_rows in sorted(groups.items()):
        positives = sorted([row for row in group_rows if base.target_y(row) == 1], key=stable_key)
        negatives = sorted([row for row in group_rows if base.target_y(row) == 0], key=stable_key)
        count = min(len(positives), len(negatives))
        selected.extend(clone_for_slice(row, target_name, slice_name, spec) for row in positives[:count])
        selected.extend(clone_for_slice(row, target_name, slice_name, spec) for row in negatives[:count])
    return sorted(selected, key=stable_key)


def counts_for(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(base.target_y(row) for row in rows)
    return {
        "rows": len(rows),
        "positive": counts[1],
        "negative": counts[0],
        "min_class": min(counts[1], counts[0]) if rows else 0,
        "positive_rate": counts[1] / len(rows) if rows else 0.0,
        "majority_baseline": max(counts[1], counts[0]) / len(rows) if rows else 0.0,
        "by_family": dict(sorted(Counter(group_value(row, "predicate_family") for row in rows).items())),
        "by_predicate": dict(sorted(Counter(group_value(row, "predicate_label") for row in rows).items())),
        "by_queue": dict(sorted(Counter(group_value(row, "queue_kind_hidden") for row in rows).items())),
        "by_role": dict(sorted(Counter(group_value(row, "proposed_audit_role_hidden") for row in rows).items())),
        "by_rank_band": dict(sorted(Counter(group_value(row, "rank_band_hidden") for row in rows).items())),
        "by_geometry_status": dict(sorted(Counter(group_value(row, "geometry_status_hidden") for row in rows).items())),
        "by_endpoint_pattern": dict(sorted(Counter(group_value(row, "endpoint_flag_pattern_hidden") for row in rows).items())),
        "by_selected_source": dict(sorted(Counter(group_value(row, "selected_source_hidden") for row in rows).items())),
    }


def top_risk_rows(risks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "group_key": item["group_key"],
            "majority_rule_accuracy": item["majority_rule_accuracy"],
            "target_majority_baseline": item["target_majority_baseline"],
            "majority_excess_over_baseline": item["majority_excess_over_baseline"],
            "normalized_mutual_information": item["normalized_mutual_information"],
            "positive_rate_range": item["positive_rate_range"],
            "positive_sparse_dominated": item["positive_sparse_dominated"],
        }
        for item in risks[:8]
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
    prior_risks = risk_summaries(summaries, "prior_carryover")
    construction_risks = risk_summaries(summaries, "construction")
    geometry_risks = risk_summaries(summaries, "expected_geometry_alignment")
    endpoint_risks = risk_summaries(summaries, "endpoint_control")
    visible_risks = risk_summaries(summaries, "visible_non_target")
    size_ready = counts["rows"] >= MIN_POSTERIOR_ROWS and counts["min_class"] >= MIN_POSTERIOR_PER_CLASS
    smoke_min_ready = counts["positive"] >= MIN_POSITIVES_FOR_SMOKE and counts["negative"] >= MIN_POSITIVES_FOR_SMOKE
    strict_candidate = size_ready and smoke_min_ready and not prior_risks and not construction_risks and not endpoint_risks
    diagnostic_candidate = smoke_min_ready and not construction_risks and not endpoint_risks
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
        "size_ready": size_ready,
        "smoke_min_ready": smoke_min_ready,
        "positive_sparse": counts["positive"] < MIN_POSITIVES_FOR_SMOKE or counts["negative"] < MIN_POSITIVES_FOR_SMOKE,
        "prior_carryover_risk_count": len(prior_risks),
        "construction_risk_count": len(construction_risks),
        "expected_geometry_alignment_risk_count": len(geometry_risks),
        "endpoint_control_risk_count": len(endpoint_risks),
        "visible_non_target_risk_count": len(visible_risks),
        "strict_candidate": strict_candidate,
        "diagnostic_candidate": diagnostic_candidate,
        "top_prior_carryover_risks": top_risk_rows(prior_risks),
        "top_construction_risks": top_risk_rows(construction_risks),
        "top_expected_geometry_alignment": top_risk_rows(geometry_risks),
        "top_endpoint_control_risks": top_risk_rows(endpoint_risks),
        "top_visible_non_target_risks": top_risk_rows(visible_risks),
        "counts": counts,
    }


def build_slices_for_target(target_name: str, rows: list[dict[str, Any]], output_dir: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    slice_dir = output_dir / "target_slices" / target_name
    slice_summaries: list[dict[str, Any]] = []
    group_rows: list[dict[str, Any]] = []
    group_summary_rows: list[dict[str, Any]] = []
    for slice_name, spec in SLICE_SPECS.items():
        slice_rows = balanced_slice(rows, target_name, slice_name, spec)
        path = slice_dir / f"{slice_name}.jsonl"
        base.write_jsonl(path, slice_rows)
        groups, summaries = all_group_summaries(slice_rows, target_name, slice_name)
        group_rows.extend(groups)
        group_summary_rows.extend(summaries)
        slice_summaries.append(slice_summary(target_name, slice_name, spec, slice_rows, summaries, path))
    return slice_summaries, group_rows, group_summary_rows


def choose_candidate(slice_summaries: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    candidates = [item for item in slice_summaries if item[key]]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item["priority"], -item["rows"], -item["min_class"]))[0]


def per_target_decision(target_name: str, summaries: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    original = next(item for item in summaries if item["slice_name"] == "original_endpoint_controlled")
    strict = choose_candidate(summaries, "strict_candidate")
    diagnostic = choose_candidate(summaries, "diagnostic_candidate")
    if errors:
        status = "target_independence_audit_errors"
        decision = "Fix row validation errors before using endpoint-controlled target slices."
        next_step = "fix_endpoint_controlled_target_independence_audit_errors"
    elif original["positive_sparse"]:
        status = "blocked_positive_sparse"
        decision = "The target is too positive-sparse for posterior smoke or controlled-slice claims."
        next_step = "endpoint_controlled_target_path_decision"
    elif strict:
        status = "strict_controlled_slice_ready"
        decision = "A strict endpoint-controlled slice clears construction and endpoint-control shortcut checks."
        next_step = "endpoint_controlled_source_feature_join_then_posterior_smoke"
    elif diagnostic:
        status = "diagnostic_slice_only"
        decision = "A diagnostic slice exists, but strict endpoint-controlled target independence is not cleared."
        next_step = "endpoint_controlled_target_path_decision"
    else:
        status = "blocked_no_controlled_slice"
        decision = "No size-ready strict or diagnostic controlled slice exists."
        next_step = "endpoint_controlled_target_path_decision"
    return {
        "target_name": target_name,
        "status": status,
        "decision": decision,
        "next_step": next_step,
        "original": original,
        "recommended_strict_slice": strict,
        "recommended_diagnostic_slice": diagnostic,
    }


def positive_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keep_keys = [
        "blind_review_id",
        "scan_id",
        "subgraph_id",
        "subject_id",
        "subject_label",
        "predicate_label",
        "object_id",
        "object_label",
        "predicate_family",
        "target_y",
        "queue_kind_hidden",
        "rank_band_hidden",
        "geometry_status_hidden",
        "label_match_status_hidden",
        "endpoint_flag_pattern_hidden",
        "selected_source_hidden",
    ]
    return [{key: row.get(key) for key in keep_keys} for row in rows if base.target_y(row) == 1]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Endpoint-Controlled Target Independence Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage target audit.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- Codex-proxy endpoint-controlled labels are not paper-level human annotations.",
        "- Hidden endpoint/sampling metadata is used only after label lock for audit.",
        "- Review fields, hidden endpoint metadata, packet paths, and multi-view evidence are not posterior inputs.",
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
        "| Target | Status | Rows | Pos | Neg | Positive Sparse | Strict Slice | Diagnostic Slice |",
        "| --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        strict = decision.get("recommended_strict_slice")
        diagnostic = decision.get("recommended_diagnostic_slice")
        lines.append(
            f"| `{target_name}` | `{decision['status']}` | {original['rows']} | {original['positive']} | {original['negative']} | "
            f"`{original['positive_sparse']}` | `{strict['slice_name'] if strict else 'none'}` | "
            f"`{diagnostic['slice_name'] if diagnostic else 'none'}` |"
        )
    lines.extend(
        [
            "",
            "## Original Target Risks",
            "",
            "| Target | Risk Mode | Key | Majority Acc | Baseline | NMI | Pos Rate Range | Sparse-Dominated |",
            "| --- | --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for target_name, decision in summary["target_decisions"].items():
        original = decision["original"]
        risk_fields = [
            ("prior_carryover", "top_prior_carryover_risks"),
            ("construction", "top_construction_risks"),
            ("expected_geometry_alignment", "top_expected_geometry_alignment"),
            ("endpoint_control", "top_endpoint_control_risks"),
            ("visible_non_target", "top_visible_non_target_risks"),
        ]
        for risk_mode, field in risk_fields:
            risks = original[field]
            if not risks:
                lines.append(f"| `{target_name}` | `{risk_mode}` | none | 0.0000 | 0.0000 | 0.0000 | 0.0000 | `{original['positive_sparse']}` |")
            for item in risks:
                lines.append(
                    f"| `{target_name}` | `{risk_mode}` | `{item['group_key']}` | "
                    f"{item['majority_rule_accuracy']:.4f} | {item['target_majority_baseline']:.4f} | "
                    f"{item['normalized_mutual_information']:.4f} | {item['positive_rate_range']:.4f} | "
                    f"`{item['positive_sparse_dominated']}` |"
                )
    lines.extend(
        [
            "",
            "## Positive-Sparsity Diagnosis",
            "",
            f"- Minimum positives for a smoke target: `{summary['risk_thresholds']['min_positives_for_smoke']}`.",
            f"- Relation reliability positives: `{summary['input_counts'][RELIABILITY_TARGET]['positive']}`.",
            f"- Relation reliability majority baseline: `{summary['input_counts'][RELIABILITY_TARGET]['majority_baseline']:.4f}`.",
            "- Therefore the endpoint-controlled reliability target is not posterior-ready.",
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

    all_slice_summaries: list[dict[str, Any]] = []
    all_group_rows: list[dict[str, Any]] = []
    all_group_summaries: list[dict[str, Any]] = []
    all_validation_errors: list[dict[str, Any]] = []
    target_decisions: dict[str, Any] = {}
    input_counts: dict[str, Any] = {}
    input_paths: dict[str, str] = {"ingestion_summary": rel_path(ingestion_dir / "summary.json")}
    positive_row_outputs: dict[str, str] = {}

    for target_name, filename in TARGET_INPUTS.items():
        input_path = ingestion_dir / filename
        input_paths[target_name] = rel_path(input_path)
        rows = base.read_jsonl(input_path)
        validation_errors = validate_rows(target_name, rows)
        all_validation_errors.extend(validation_errors)
        slice_summaries, group_rows, group_summaries = build_slices_for_target(target_name, rows, output_dir)
        all_slice_summaries.extend(slice_summaries)
        all_group_rows.extend(group_rows)
        all_group_summaries.extend(group_summaries)
        target_decisions[target_name] = per_target_decision(target_name, slice_summaries, validation_errors)
        counts = counts_for(rows)
        counts["validation_errors"] = len(validation_errors)
        input_counts[target_name] = counts
        positive_path = output_dir / f"{target_name}_positive_rows.jsonl"
        base.write_jsonl(positive_path, positive_rows(rows))
        positive_row_outputs[target_name] = rel_path(positive_path)

    relation_decision = target_decisions[RELIABILITY_TARGET]
    relation_counts = input_counts[RELIABILITY_TARGET]
    if all_validation_errors:
        status = "h002_endpoint_controlled_target_independence_audit_errors"
        decision = "Fix endpoint-controlled audit validation errors before any target path decision."
        next_todo = "fix_endpoint_controlled_target_independence_audit_errors"
    elif relation_counts["positive"] < MIN_POSITIVES_FOR_SMOKE:
        status = "h002_endpoint_controlled_target_independence_audit_blocked_positive_sparse"
        decision = (
            "Endpoint-controlled target audit confirms posterior smoke remains blocked: relation reliability "
            "has too few positives and no strict controlled slice."
        )
        next_todo = "endpoint_controlled_target_path_decision"
    elif relation_decision["recommended_strict_slice"]:
        status = "h002_endpoint_controlled_target_independence_audit_strict_slice_ready"
        decision = "A strict endpoint-controlled relation reliability slice exists."
        next_todo = "endpoint_controlled_source_feature_join_then_posterior_smoke"
    else:
        status = "h002_endpoint_controlled_target_independence_audit_blocked_no_strict_slice"
        decision = "Relation reliability target is not strict-slice ready after endpoint-controlled audit."
        next_todo = "endpoint_controlled_target_path_decision"

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "slice_summaries": output_dir / "slice_summaries.csv",
        "group_summaries": output_dir / "group_summaries.csv",
        "group_table": output_dir / "group_table.csv",
        "target_slices": output_dir / "target_slices",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    output_paths.update({f"{target}_positive_rows": Path(path) for target, path in positive_row_outputs.items()})

    summary = {
        "schema_version": "h002_endpoint_controlled_target_independence_audit_summary_v1",
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
            "label_source": "codex_proxy_endpoint_controlled_user_requested",
            "actual_user_reviewer": False,
            "posterior_claim_allowed": False,
            "hidden_metadata_used_for_audit_only": True,
            "review_fields_used_for_target_or_audit_only": True,
            "endpoint_controlled_review_fields_as_model_input": False,
            "hidden_endpoint_metadata_as_model_input": False,
            "multi_view_as_model_input": False,
        },
        "risk_thresholds": {
            "normalized_mutual_information": base.RISK_NMI_THRESHOLD,
            "majority_rule_accuracy": base.RISK_MAJORITY_THRESHOLD,
            "positive_rate_range": base.RISK_POSITIVE_RATE_RANGE_THRESHOLD,
            "large_group_rows": base.RISK_LARGE_GROUP_ROWS,
            "large_group_purity": base.RISK_LARGE_GROUP_PURITY,
            "min_posterior_rows": MIN_POSTERIOR_ROWS,
            "min_posterior_per_class": MIN_POSTERIOR_PER_CLASS,
            "min_positives_for_smoke": MIN_POSITIVES_FOR_SMOKE,
        },
        "ingestion_status": ingestion_summary.get("status"),
        "input_counts": input_counts,
        "validation_errors": len(all_validation_errors),
        "target_decisions": target_decisions,
        "strict_ready_targets": [
            target for target, item in target_decisions.items() if item["recommended_strict_slice"] is not None
        ],
        "diagnostic_only_targets": [
            target
            for target, item in target_decisions.items()
            if item["recommended_strict_slice"] is None and item["recommended_diagnostic_slice"] is not None
        ],
        "blocked_targets": [
            target
            for target, item in target_decisions.items()
            if item["recommended_strict_slice"] is None and item["recommended_diagnostic_slice"] is None
        ],
        "slice_summaries": all_slice_summaries,
        "decision": decision,
        "next_todo": next_todo,
    }

    base.write_json(output_paths["summary"], summary)
    base.write_csv(output_paths["slice_summaries"], all_slice_summaries)
    base.write_csv(output_paths["group_summaries"], all_group_summaries)
    base.write_csv(output_paths["group_table"], all_group_rows)
    base.write_jsonl(output_paths["validation_errors"], all_validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["input_counts"][RELIABILITY_TARGET]
    decision = summary["target_decisions"][RELIABILITY_TARGET]
    strict = decision.get("recommended_strict_slice")
    diagnostic = decision.get("recommended_diagnostic_slice")
    print(
        f"status={summary['status']} relation_rows={counts['rows']} "
        f"relation_pos={counts['positive']} relation_neg={counts['negative']} "
        f"majority_baseline={counts['majority_baseline']:.4f} "
        f"errors={summary['validation_errors']} "
        f"relation_strict={strict['slice_name'] if strict else 'none'} "
        f"relation_diagnostic={diagnostic['slice_name'] if diagnostic else 'none'} "
        f"validation_used={summary['boundary']['validation_usage']} test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
