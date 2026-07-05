#!/usr/bin/env python3
"""Audit the H002 v6 uncertainty-aware reliability design seeds."""

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

DEFAULT_DESIGN_DIR = RGA_ROOT / "reliability_target_v6_uncertainty_aware_target_design_codex_proxy_user_requested"
DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_label_ingestion_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v6_uncertainty_aware_seed_audit_codex_proxy_user_requested"

STATE_ORDER = ["accept_reliable", "reject_unreliable", "abstain_uncertain"]

NEXT_TODO = "reliability_target_v6_uncertainty_aware_path_decision"

RISK_NMI_THRESHOLD = 0.20
RISK_MAJORITY_EXCESS_THRESHOLD = 0.10
RISK_MAX_STATE_RATE_RANGE_THRESHOLD = 0.70
RISK_LARGE_GROUP_ROWS = 10
RISK_LARGE_GROUP_PURITY = 0.95

KEY_GROUPS = [
    {
        "risk_mode": "cell_contrast_design",
        "source": "hidden_post_label_audit",
        "blocking_for_posterior": True,
        "keys": [
            "cell_contrast_pair_id_hidden",
            "cell_contrast_key_hidden",
            "cell_contrast_role_hidden",
            "contrast_role_hidden",
            "cell_contrast_level_hidden",
        ],
    },
    {
        "risk_mode": "endpoint_object_structure",
        "source": "hidden_post_label_audit",
        "blocking_for_posterior": True,
        "keys": [
            "subject_object_family_cell_hidden",
            "object_family_cell_hidden",
            "endpoint_family_cell_hidden",
            "endpoint_flag_pattern_hidden",
        ],
    },
    {
        "risk_mode": "construction",
        "source": "hidden_post_label_audit",
        "blocking_for_posterior": True,
        "keys": [
            "source_queue_hidden",
            "queue_kind_hidden",
            "rank_band_hidden",
            "asset_packet_source_hidden",
            "row_gap_decision_hidden",
            "pair_gap_decision_hidden",
        ],
    },
    {
        "risk_mode": "geometry_alignment",
        "source": "hidden_post_label_audit",
        "blocking_for_posterior": True,
        "keys": [
            "geometry_status_hidden",
            "h001_verification_status_hidden",
            "label_match_status_hidden",
            "label_match_family_hidden",
            "label_geometry_bucket_hidden",
        ],
    },
    {
        "risk_mode": "visible_relation_surface",
        "source": "visible_conditioning_surface",
        "blocking_for_posterior": False,
        "keys": ["predicate_family", "predicate_label"],
    },
    {
        "risk_mode": "visible_object_identity",
        "source": "visible_non_target_surface",
        "blocking_for_posterior": True,
        "keys": ["subject_label", "object_label"],
    },
    {
        "risk_mode": "visible_coverage",
        "source": "visible_non_target_surface",
        "blocking_for_posterior": True,
        "keys": ["evidence_packet_status", "packet_gap_decision"],
    },
    {
        "risk_mode": "auxiliary_label_axes",
        "source": "target_auxiliary_label_axis_not_model_input",
        "blocking_for_posterior": False,
        "keys": ["v6_geometry_state_aux", "v6_usefulness_state_aux", "v6_reliability_subtype"],
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design-dir", type=Path, default=DEFAULT_DESIGN_DIR)
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
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def entropy_from_counts(counts: Counter[str]) -> float:
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


def safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def flatten_audit_row(seed: dict[str, Any], validated: dict[str, Any]) -> dict[str, Any]:
    hidden = validated.get("hidden_audit_metadata_post_label_only", {})
    deployable = validated.get("deployable_evidence_after_label_lock", {})
    semantic = deployable.get("semantic_evidence", {})
    geometry = deployable.get("geometry_scalar_evidence", {})
    coverage = deployable.get("coverage_evidence", {})

    row = {
        "schema_version": "h002_reliability_target_v6_uncertainty_aware_seed_audit_row_v1",
        "blind_review_id": seed["blind_review_id"],
        "scan_id": seed["scan_id"],
        "scene_context_id": seed.get("scene_context_id"),
        "subgraph_id": validated.get("subgraph_id"),
        "prediction_id": validated.get("prediction_id"),
        "subject_id": seed["subject_id"],
        "object_id": seed["object_id"],
        "subject_label": seed["subject_label"],
        "object_label": seed["object_label"],
        "predicate_label": seed["predicate_label"],
        "predicate_family": seed["predicate_family"],
        "v6_reliability_state": seed["v6_reliability_state"],
        "v6_reliability_subtype": seed["v6_reliability_subtype"],
        "v6_geometry_state_aux": seed["v6_geometry_state_aux"],
        "v6_usefulness_state_aux": seed["v6_usefulness_state_aux"],
        "v5_relation_reliability": seed["v5_relation_reliability"],
        "v5_geometry_support": seed["v5_geometry_support"],
        "v5_relation_usefulness": seed["v5_relation_usefulness"],
        "v5_primary_reason": seed["v5_primary_reason"],
        "v5_uncertainty_reason": seed["v5_uncertainty_reason"],
        "evidence_packet_status": seed["evidence_packet_status"],
        "packet_gap_decision": seed["packet_gap_decision"],
        "semantic_score_raw": semantic.get("semantic_score_raw"),
        "semantic_score_norm": semantic.get("semantic_score_norm"),
        "semantic_rank": semantic.get("semantic_rank"),
        "p_geom_valid": geometry.get("p_geom_valid"),
        "geometry_scalar_role": geometry.get("role"),
        "coverage_packet_gap_reason": coverage.get("packet_gap_reason"),
        "target_use": "seed_audit_only",
        "posterior_training_allowed": False,
        "paper_evidence_allowed": False,
        "validation_usage": False,
        "test_usage": False,
        "h001_artifacts_modified": False,
    }

    for key in [
        "cell_contrast_pair_id_hidden",
        "cell_contrast_key_hidden",
        "cell_contrast_role_hidden",
        "contrast_role_hidden",
        "cell_contrast_level_hidden",
        "subject_object_family_cell_hidden",
        "object_family_cell_hidden",
        "endpoint_family_cell_hidden",
        "endpoint_flag_pattern_hidden",
        "source_queue_hidden",
        "queue_kind_hidden",
        "rank_band_hidden",
        "asset_packet_source_hidden",
        "row_gap_decision_hidden",
        "pair_gap_decision_hidden",
        "geometry_status_hidden",
        "h001_verification_status_hidden",
        "label_match_status_hidden",
        "label_match_family_hidden",
        "label_geometry_bucket_hidden",
        "semantic_rank_hidden",
        "semantic_score_norm_hidden",
        "semantic_score_raw_hidden",
        "p_geom_valid_hidden",
        "machine_hint_hidden",
        "reason_codes_hidden",
        "packet_status_hidden",
    ]:
        row[key] = hidden.get(key)

    return row


def validate_inputs(
    design_summary: dict[str, Any],
    target_schema: dict[str, Any],
    input_contract: dict[str, Any],
    gate_plan: dict[str, Any],
    seeds: list[dict[str, Any]],
    validated_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_status = "h002_reliability_target_v6_uncertainty_aware_target_design_ready_for_seed_audit"
    if design_summary.get("status") != expected_status:
        errors.append({"error_type": "unexpected_design_status", "expected": expected_status, "actual": design_summary.get("status")})
    if design_summary.get("next_todo") != "reliability_target_v6_uncertainty_aware_seed_audit":
        errors.append({"error_type": "unexpected_design_next_todo", "actual": design_summary.get("next_todo")})
    if target_schema.get("selected_primary_target") != "nominal_multiclass_reliability_with_abstention":
        errors.append({"error_type": "unexpected_target_form", "actual": target_schema.get("selected_primary_target")})
    for key in ["validation_usage", "test_usage", "multi_view_as_model_input"]:
        if input_contract.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "input_contract_boundary_violation", "key": key, "actual": input_contract.get("boundary", {}).get(key)})
    if gate_plan.get("class_mass_gates", {}).get("diagnostic_seed_min_per_state") != 10:
        errors.append({"error_type": "unexpected_diagnostic_mass_gate", "actual": gate_plan.get("class_mass_gates", {}).get("diagnostic_seed_min_per_state")})

    seed_ids = [row.get("blind_review_id") for row in seeds]
    valid_ids = [row.get("blind_review_id") for row in validated_rows]
    if len(seeds) != 72:
        errors.append({"error_type": "unexpected_seed_count", "expected": 72, "actual": len(seeds)})
    if len(validated_rows) != 72:
        errors.append({"error_type": "unexpected_validated_count", "expected": 72, "actual": len(validated_rows)})
    if len(seed_ids) != len(set(seed_ids)):
        errors.append({"error_type": "duplicate_seed_ids", "duplicates": sorted([item for item, count in Counter(seed_ids).items() if count > 1])})
    if set(seed_ids) != set(valid_ids):
        errors.append(
            {
                "error_type": "seed_validated_id_mismatch",
                "missing_in_validated": sorted(set(seed_ids) - set(valid_ids)),
                "missing_in_seed": sorted(set(valid_ids) - set(seed_ids)),
            }
        )
    for row in seeds:
        if row.get("target_use") != "design_seed_only":
            errors.append({"error_type": "seed_target_use_not_design_only", "blind_review_id": row.get("blind_review_id"), "actual": row.get("target_use")})
        if row.get("posterior_training_allowed") is not False:
            errors.append({"error_type": "seed_posterior_training_allowed", "blind_review_id": row.get("blind_review_id")})
        if row.get("paper_evidence_allowed") is not False:
            errors.append({"error_type": "seed_paper_evidence_allowed", "blind_review_id": row.get("blind_review_id")})
    for row in validated_rows:
        boundary = row.get("boundary", {})
        if boundary.get("split") != "train_only":
            errors.append({"error_type": "validated_row_not_train_only", "blind_review_id": row.get("blind_review_id"), "actual": boundary.get("split")})
        for key in ["validation_usage", "test_usage", "multi_view_as_model_input", "paper_evidence_allowed", "posterior_claim_allowed"]:
            if boundary.get(key) is not False:
                errors.append({"error_type": "validated_boundary_violation", "blind_review_id": row.get("blind_review_id"), "key": key, "actual": boundary.get(key)})
    return errors


def class_mass_summary(rows: list[dict[str, Any]], gate_plan: dict[str, Any]) -> dict[str, Any]:
    counts = Counter(row["v6_reliability_state"] for row in rows)
    diagnostic_min = int(gate_plan["class_mass_gates"]["diagnostic_seed_min_per_state"])
    posterior_min = int(gate_plan["class_mass_gates"]["posterior_smoke_min_per_state"])
    ordered_counts = {state: counts[state] for state in STATE_ORDER}
    return {
        "rows": len(rows),
        "state_counts": ordered_counts,
        "min_state_count": min(ordered_counts.values()) if ordered_counts else 0,
        "diagnostic_seed_min_per_state": diagnostic_min,
        "posterior_smoke_min_per_state": posterior_min,
        "diagnostic_class_mass_pass": all(count >= diagnostic_min for count in ordered_counts.values()),
        "posterior_class_mass_pass": all(count >= posterior_min for count in ordered_counts.values()),
        "posterior_sparse_states": [state for state, count in ordered_counts.items() if count < posterior_min],
        "majority_state": counts.most_common(1)[0][0] if counts else "",
        "majority_baseline": counts.most_common(1)[0][1] / len(rows) if rows else 0.0,
        "entropy_bits": entropy_from_counts(counts),
    }


def group_summary(
    rows: list[dict[str, Any]],
    group_key: str,
    risk_mode: str,
    source: str,
    blocking_for_posterior: bool,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(group_key, "missing"))].append(row)

    total_counts = Counter(row["v6_reliability_state"] for row in rows)
    overall_entropy = entropy_from_counts(total_counts)
    majority_baseline = max(total_counts.values()) / len(rows) if rows else 0.0
    conditional_entropy = 0.0
    majority_correct = 0
    state_rates: dict[str, list[float]] = {state: [] for state in STATE_ORDER}
    large_group_high_purity = False
    table_rows: list[dict[str, Any]] = []

    for value, group_rows in sorted(grouped.items()):
        counts = Counter(row["v6_reliability_state"] for row in group_rows)
        total = len(group_rows)
        majority_state, majority_count = counts.most_common(1)[0]
        majority_accuracy = majority_count / total if total else 0.0
        group_entropy = entropy_from_counts(counts)
        conditional_entropy += total / len(rows) * group_entropy if rows else 0.0
        majority_correct += majority_count
        if total >= RISK_LARGE_GROUP_ROWS and majority_accuracy >= RISK_LARGE_GROUP_PURITY:
            large_group_high_purity = True
        for state in STATE_ORDER:
            state_rates[state].append(counts[state] / total if total else 0.0)
        table_rows.append(
            {
                "risk_mode": risk_mode,
                "source": source,
                "group_key": group_key,
                "group_value": value,
                "blocking_for_posterior": blocking_for_posterior,
                "rows": total,
                "accept_reliable": counts["accept_reliable"],
                "reject_unreliable": counts["reject_unreliable"],
                "abstain_uncertain": counts["abstain_uncertain"],
                "majority_state": majority_state,
                "majority_accuracy": majority_accuracy,
                "entropy_bits": group_entropy,
            }
        )

    mutual_information = max(0.0, overall_entropy - conditional_entropy)
    nmi = mutual_information / overall_entropy if overall_entropy > 0 else 0.0
    majority_rule_accuracy = majority_correct / len(rows) if rows else 0.0
    majority_excess = majority_rule_accuracy - majority_baseline
    state_rate_ranges = {
        state: (max(values) - min(values)) if values else 0.0
        for state, values in state_rates.items()
    }
    max_state_rate_range = max(state_rate_ranges.values()) if state_rate_ranges else 0.0
    single_state_groups = sum(
        1 for item in table_rows if sum(1 for state in STATE_ORDER if item[state] > 0) == 1
    )
    risk_flag = (
        nmi >= RISK_NMI_THRESHOLD
        or majority_excess >= RISK_MAJORITY_EXCESS_THRESHOLD
        or max_state_rate_range >= RISK_MAX_STATE_RATE_RANGE_THRESHOLD
        or large_group_high_purity
    )
    summary = {
        "risk_mode": risk_mode,
        "source": source,
        "group_key": group_key,
        "blocking_for_posterior": blocking_for_posterior,
        "groups": len(grouped),
        "rows": len(rows),
        "accept_reliable": total_counts["accept_reliable"],
        "reject_unreliable": total_counts["reject_unreliable"],
        "abstain_uncertain": total_counts["abstain_uncertain"],
        "overall_entropy_bits": overall_entropy,
        "conditional_entropy_bits": conditional_entropy,
        "mutual_information_bits": mutual_information,
        "normalized_mutual_information": nmi,
        "majority_baseline": majority_baseline,
        "majority_rule_accuracy": majority_rule_accuracy,
        "majority_excess_over_baseline": majority_excess,
        "state_rate_ranges": state_rate_ranges,
        "max_state_rate_range": max_state_rate_range,
        "large_group_high_purity": large_group_high_purity,
        "single_state_groups": single_state_groups,
        "risk_flag": risk_flag,
        "blocking_risk_flag": bool(blocking_for_posterior and risk_flag),
    }
    return table_rows, summary


def build_group_audit(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    group_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    for group in KEY_GROUPS:
        for key in group["keys"]:
            table, summary = group_summary(
                rows,
                key,
                group["risk_mode"],
                group["source"],
                bool(group["blocking_for_posterior"]),
            )
            group_rows.extend(table)
            summaries.append(summary)
    return group_rows, summaries


def sorted_risks(summaries: list[dict[str, Any]], blocking_only: bool) -> list[dict[str, Any]]:
    risks = [
        item for item in summaries
        if item["risk_flag"] and (item["blocking_risk_flag"] if blocking_only else True)
    ]
    return sorted(
        risks,
        key=lambda item: (
            -float(item["normalized_mutual_information"]),
            -float(item["majority_excess_over_baseline"]),
            -float(item["max_state_rate_range"]),
            item["group_key"],
        ),
    )


def compact_risk(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "risk_mode": item["risk_mode"],
        "group_key": item["group_key"],
        "blocking_for_posterior": item["blocking_for_posterior"],
        "normalized_mutual_information": item["normalized_mutual_information"],
        "majority_baseline": item["majority_baseline"],
        "majority_rule_accuracy": item["majority_rule_accuracy"],
        "majority_excess_over_baseline": item["majority_excess_over_baseline"],
        "max_state_rate_range": item["max_state_rate_range"],
        "large_group_high_purity": item["large_group_high_purity"],
        "single_state_groups": item["single_state_groups"],
    }


def seed_inventory(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    views = {
        "state": ["v6_reliability_state"],
        "state_x_subtype": ["v6_reliability_state", "v6_reliability_subtype"],
        "state_x_geometry_aux": ["v6_reliability_state", "v6_geometry_state_aux"],
        "state_x_usefulness_aux": ["v6_reliability_state", "v6_usefulness_state_aux"],
        "state_x_family": ["v6_reliability_state", "predicate_family"],
        "state_x_predicate": ["v6_reliability_state", "predicate_label"],
        "state_x_geometry_status_hidden": ["v6_reliability_state", "geometry_status_hidden"],
        "state_x_cell_role_hidden": ["v6_reliability_state", "cell_contrast_role_hidden"],
        "state_x_rank_band_hidden": ["v6_reliability_state", "rank_band_hidden"],
    }
    output: list[dict[str, Any]] = []
    for view, keys in views.items():
        counts = Counter(tuple(str(row.get(key, "")) for key in keys) for row in rows)
        for key, count in sorted(counts.items()):
            output.append(
                {
                    "inventory_view": view,
                    "key_1": key[0] if len(key) > 0 else "",
                    "key_2": key[1] if len(key) > 1 else "",
                    "count": count,
                }
            )
    return output


def risk_summary(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    risks = sorted_risks(summaries, blocking_only=False)
    blocking = sorted_risks(summaries, blocking_only=True)
    return {
        "risk_thresholds": {
            "normalized_mutual_information": RISK_NMI_THRESHOLD,
            "majority_excess_over_baseline": RISK_MAJORITY_EXCESS_THRESHOLD,
            "max_state_rate_range": RISK_MAX_STATE_RATE_RANGE_THRESHOLD,
            "large_group_rows": RISK_LARGE_GROUP_ROWS,
            "large_group_purity": RISK_LARGE_GROUP_PURITY,
        },
        "risk_count": len(risks),
        "blocking_risk_count": len(blocking),
        "risk_counts_by_mode": dict(sorted(Counter(item["risk_mode"] for item in risks).items())),
        "blocking_risk_counts_by_mode": dict(sorted(Counter(item["risk_mode"] for item in blocking).items())),
        "top_risks": [compact_risk(item) for item in risks[:12]],
        "top_blocking_risks": [compact_risk(item) for item in blocking[:12]],
        "auxiliary_label_axis_note": (
            "Auxiliary label axes are audited to expose target coupling, but they are not "
            "posterior inputs and do not by themselves block posterior reopening."
        ),
    }


def choose_status(validation_errors: list[dict[str, Any]], class_mass: dict[str, Any], risks: dict[str, Any]) -> tuple[str, list[str], bool]:
    blocked_reasons: list[str] = []
    if validation_errors:
        blocked_reasons.append("input_validation_errors")
    if not class_mass["diagnostic_class_mass_pass"]:
        blocked_reasons.append("diagnostic_class_mass_failed")
    if not class_mass["posterior_class_mass_pass"]:
        blocked_reasons.append("posterior_class_mass_failed")
    if risks["blocking_risk_count"] > 0:
        blocked_reasons.append("shortcut_risk_in_blocking_group")

    posterior_allowed = not validation_errors and class_mass["posterior_class_mass_pass"] and risks["blocking_risk_count"] == 0
    if validation_errors:
        status = "h002_reliability_target_v6_uncertainty_aware_seed_audit_validation_failed"
    elif risks["blocking_risk_count"] > 0:
        status = "h002_reliability_target_v6_uncertainty_aware_seed_audit_blocked_shortcut_risk"
    elif not class_mass["posterior_class_mass_pass"]:
        status = "h002_reliability_target_v6_uncertainty_aware_seed_audit_blocked_class_mass"
    else:
        status = "h002_reliability_target_v6_uncertainty_aware_seed_audit_ready_for_posterior_smoke"
    return status, blocked_reasons, posterior_allowed


def write_report(path: Path, summary: dict[str, Any]) -> None:
    class_mass = summary["class_mass"]
    risks = summary["risk_summary"]
    lines = [
        "# H002 Reliability Target V6 Uncertainty-Aware Seed Audit",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Split: Open3DSG train-only.",
        "- Validation/test rows: not used.",
        "- Posterior model: not trained.",
        "- H001 artifacts: not modified.",
        "- V5 labels remain design-seed/audit-only, not paper evidence.",
        "- Multi-view remains audit evidence only.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Class Mass",
        "",
        "| State | Rows |",
        "| --- | ---: |",
    ]
    for state in STATE_ORDER:
        lines.append(f"| `{state}` | {class_mass['state_counts'][state]} |")
    lines.extend(
        [
            "",
            f"- Diagnostic seed gate pass: `{class_mass['diagnostic_class_mass_pass']}`",
            f"- Posterior class-mass gate pass: `{class_mass['posterior_class_mass_pass']}`",
            f"- Sparse states for posterior: `{', '.join(class_mass['posterior_sparse_states'])}`",
            f"- Majority baseline: `{class_mass['majority_baseline']:.4f}`",
            "",
            "## Shortcut Audit",
            "",
            f"- Total risk groups: `{risks['risk_count']}`",
            f"- Blocking risk groups: `{risks['blocking_risk_count']}`",
            "",
            "Top blocking risks:",
            "",
            "| Risk Mode | Group Key | NMI | Majority Acc. | Max State-Rate Range |",
            "| --- | --- | ---: | ---: | ---: |",
        ]
    )
    for item in risks["top_blocking_risks"][:8]:
        lines.append(
            "| `{risk_mode}` | `{group_key}` | {nmi:.4f} | {maj:.4f} | {rng:.4f} |".format(
                risk_mode=item["risk_mode"],
                group_key=item["group_key"],
                nmi=item["normalized_mutual_information"],
                maj=item["majority_rule_accuracy"],
                rng=item["max_state_rate_range"],
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
    design_dir = as_abs(args.design_dir)
    ingestion_dir = as_abs(args.ingestion_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    design_summary = read_json(design_dir / "summary.json")
    target_schema = read_json(design_dir / "target_schema.json")
    input_contract = read_json(design_dir / "input_contract.json")
    gate_plan = read_json(design_dir / "independence_gate_plan.json")
    seeds = read_jsonl(design_dir / "seed_labels_v6_design_only.jsonl")
    validated_rows = read_jsonl(ingestion_dir / "validated_v5_labels.jsonl")

    errors = validate_inputs(design_summary, target_schema, input_contract, gate_plan, seeds, validated_rows)
    validated_by_id = {row["blind_review_id"]: row for row in validated_rows}
    audit_rows = [
        flatten_audit_row(seed, validated_by_id[seed["blind_review_id"]])
        for seed in seeds
        if seed["blind_review_id"] in validated_by_id
    ]
    class_mass = class_mass_summary(audit_rows, gate_plan)
    group_rows, group_summaries = build_group_audit(audit_rows)
    risks = risk_summary(group_summaries)
    status, blocked_reasons, posterior_allowed = choose_status(errors, class_mass, risks)
    decision = (
        "V6 preserves the uncertainty state and passes the diagnostic seed class-mass gate, "
        "but the current 72 v5-derived seed rows are still strongly tied to cell/pair/object/geometry "
        "construction variables and do not meet posterior class mass. Keep v6 as a target-design "
        "direction, keep these rows audit-only, and run a path decision before any posterior smoke."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "seed_audit_rows": output_dir / "seed_audit_rows.jsonl",
        "group_summaries": output_dir / "group_summaries.csv",
        "group_table": output_dir / "group_table.csv",
        "class_mass": output_dir / "class_mass.json",
        "risk_summary": output_dir / "risk_summary.json",
        "seed_inventory": output_dir / "seed_state_inventory.csv",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    summary = {
        "schema_version": "h002_reliability_target_v6_uncertainty_aware_seed_audit_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "blocked_reasons": blocked_reasons,
        "next_todo": NEXT_TODO,
        "input_paths": {
            "design_summary": rel_path(design_dir / "summary.json"),
            "target_schema": rel_path(design_dir / "target_schema.json"),
            "input_contract": rel_path(design_dir / "input_contract.json"),
            "independence_gate_plan": rel_path(design_dir / "independence_gate_plan.json"),
            "seed_labels": rel_path(design_dir / "seed_labels_v6_design_only.jsonl"),
            "validated_v5_labels": rel_path(ingestion_dir / "validated_v5_labels.jsonl"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "fills_new_labels": False,
            "posterior_smoke_allowed": posterior_allowed,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "v5_labels_are_design_seed_only": True,
        },
        "class_mass": class_mass,
        "risk_summary": risks,
        "validation_error_count": len(errors),
        "posterior_smoke_allowed": posterior_allowed,
        "target_use": "seed_audit_only",
        "upstream_status": {
            "design": design_summary.get("status"),
            "design_next_todo": design_summary.get("next_todo"),
        },
    }

    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    write_jsonl(output_paths["seed_audit_rows"], audit_rows)
    write_csv(output_paths["group_summaries"], group_summaries)
    write_csv(output_paths["group_table"], group_rows)
    write_json(output_paths["class_mass"], class_mass)
    write_json(output_paths["risk_summary"], risks)
    write_csv(output_paths["seed_inventory"], seed_inventory(audit_rows))
    write_jsonl(output_paths["validation_errors"], errors)

    return summary


def main() -> None:
    summary = run(parse_args())
    class_mass = summary["class_mass"]
    print(f"status={summary['status']}")
    print(f"rows={class_mass['rows']}")
    print(f"state_counts={class_mass['state_counts']}")
    print(f"diagnostic_pass={class_mass['diagnostic_class_mass_pass']}")
    print(f"posterior_class_mass_pass={class_mass['posterior_class_mass_pass']}")
    print(f"blocking_risk_count={summary['risk_summary']['blocking_risk_count']}")
    print(f"posterior_allowed={summary['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_error_count']}")
    print(f"next={summary['next_todo']}")


if __name__ == "__main__":
    main()
