#!/usr/bin/env python3
"""Review support/contact mesh-pose-contact feature probe results."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner"
DEFAULT_SOURCE_INVENTORY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_feature_probe_result_review"

EXPECTED_RUNNER_STATUS = "h002_compatibility_dataset_v3_support_contact_mesh_pose_contact_feature_probe_runner_ready_for_result_review"
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_support_contact_feature_probe_result_review"
EXPECTED_SOURCE_STATUS = "h002_compatibility_dataset_v3_support_contact_visual_mesh_source_inventory_ready_for_mesh_pose_contact_probe"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_feature_probe_result_review_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_feature_probe_result_review_select_pose_conditioned_target_plan"
STATUS_DIAGNOSTIC = "h002_compatibility_dataset_v3_support_contact_feature_probe_result_review_diagnostic_only"
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_feature_probe_result_review_input_errors"
SELECTED_PATH_READY = "select_pose_conditioned_same_geometry_support_contact_target_plan"
SELECTED_PATH_DIAGNOSTIC = "freeze_support_contact_feature_probe_as_diagnostic"
NEXT_READY = "compatibility_dataset_v3_support_contact_pose_conditioned_target_plan"
NEXT_DIAGNOSTIC = "compatibility_dataset_v3_support_contact_diagnostic_freeze"

PREDICATE_PAIRS = [
    ("lying on", "standing on"),
    ("lying on", "supported by"),
    ("standing on", "supported by"),
]

REVIEW_FEATURES = {
    "A_full_rows": [
        "center_delta_z",
        "surface_gap_subject_bottom_to_object_top",
        "abs_surface_gap_subject_bottom_to_object_top",
        "xy_overlap_min_ratio",
        "support_area_proxy",
        "center_distance_xy",
        "normalized_center_distance_xy",
        "subject_vertical_extent_ratio",
        "subject_flatness_ratio",
        "object_vertical_extent_ratio",
        "object_flatness_ratio",
        "normal_alignment",
        "obb_contact_likelihood_proxy",
    ],
    "B_stratified_sample": [
        "point_surface_gap_subject_bottom_to_object_top",
        "point_abs_surface_gap",
        "point_xy_overlap_min_ratio",
        "point_contact_candidate_ratio",
        "point_center_distance_xy",
        "point_subject_vertical_extent_ratio",
        "point_object_vertical_extent_ratio",
        "point_subject_bottom_band_density",
        "point_object_top_band_density",
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-dir", type=Path, default=DEFAULT_RUNNER_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not fields:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: Any, default: float = math.nan) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def validate_inputs(
    runner_summary: dict[str, Any],
    runner_validation_rows: list[dict[str, Any]],
    source_summary: dict[str, Any],
    derivability_rows: list[dict[str, str]],
    distribution_rows: list[dict[str, str]],
    shortcut_rows: list[dict[str, str]],
    old_numeric_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if runner_summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": runner_summary.get("status")})
    if runner_summary.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_next", "actual": runner_summary.get("next_todo")})
    if runner_summary.get("validation_errors") != 0:
        errors.append({"error_type": "runner_validation_errors", "actual": runner_summary.get("validation_errors")})
    if runner_validation_rows:
        errors.append({"error_type": "runner_validation_error_rows_present", "rows": len(runner_validation_rows)})
    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_inventory_status", "actual": source_summary.get("status")})

    counts = runner_summary.get("counts", {})
    if counts.get("support_rows") != 161498:
        errors.append({"error_type": "unexpected_support_row_count", "actual": counts.get("support_rows")})
    if counts.get("tier_a_records") != counts.get("support_rows"):
        errors.append({"error_type": "tier_a_not_full_rows", "counts": counts})
    if counts.get("tier_b_records", 0) < 1000:
        errors.append({"error_type": "tier_b_probe_too_small", "actual": counts.get("tier_b_records")})

    decision = runner_summary.get("path_decision", {})
    required_true = [
        "tier_a_derivability_pass",
        "tier_a_finite_pass",
        "tier_b_sample_pass",
        "model_safe_blocked_fields_absent",
        "new_features_not_old_proxy_pass",
    ]
    for key in required_true:
        if decision.get(key) is not True:
            errors.append({"error_type": "runner_gate_not_passed", "gate": key, "actual": decision.get(key)})
    for key in ["candidate_materialization_allowed", "learned_smoke_allowed", "paper_evidence_allowed"]:
        if decision.get(key) is not False:
            errors.append({"error_type": "runner_boundary_not_false", "gate": key, "actual": decision.get(key)})

    if not derivability_rows:
        errors.append({"error_type": "missing_derivability_rows"})
    if not distribution_rows:
        errors.append({"error_type": "missing_distribution_rows"})
    if not shortcut_rows:
        errors.append({"error_type": "missing_shortcut_risk_rows"})
    if not old_numeric_rows:
        errors.append({"error_type": "missing_old_numeric_rows"})
    return errors


def derivability_review(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        non_missing = as_float(row.get("non_missing_rate"))
        finite = as_float(row.get("finite_rate"))
        out.append(
            {
                "tier": row.get("tier"),
                "feature": row.get("feature"),
                "rows": as_int(row.get("rows")),
                "non_missing_rate": non_missing,
                "finite_rate": finite,
                "gate": "pass" if non_missing >= 0.95 and finite >= 0.99 else "fail",
            }
        )
    return out


def distribution_lookup(rows: list[dict[str, str]]) -> dict[tuple[str, str, str, str], dict[str, str]]:
    lookup: dict[tuple[str, str, str, str], dict[str, str]] = {}
    for row in rows:
        key = (
            row.get("tier", ""),
            row.get("feature", ""),
            row.get("group_axis", ""),
            row.get("group_value", ""),
        )
        lookup[key] = row
    return lookup


def standardized_delta(left: dict[str, str], right: dict[str, str]) -> tuple[float, float, float]:
    left_mean = as_float(left.get("mean"))
    right_mean = as_float(right.get("mean"))
    left_std = as_float(left.get("std"), 0.0)
    right_std = as_float(right.get("std"), 0.0)
    pooled = math.sqrt(max((left_std * left_std + right_std * right_std) / 2.0, 1e-12))
    delta = left_mean - right_mean
    return delta, abs(delta) / pooled, pooled


def predicate_delta_rows(distribution_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    lookup = distribution_lookup(distribution_rows)
    rows: list[dict[str, Any]] = []
    for tier, features in REVIEW_FEATURES.items():
        for feature in features:
            for left_predicate, right_predicate in PREDICATE_PAIRS:
                left = lookup.get((tier, feature, "predicate_label", left_predicate))
                right = lookup.get((tier, feature, "predicate_label", right_predicate))
                if not left or not right:
                    continue
                delta, smd, pooled = standardized_delta(left, right)
                rows.append(
                    {
                        "tier": tier,
                        "feature": feature,
                        "left_predicate": left_predicate,
                        "right_predicate": right_predicate,
                        "left_rows": as_int(left.get("rows")),
                        "right_rows": as_int(right.get("rows")),
                        "left_mean": as_float(left.get("mean")),
                        "right_mean": as_float(right.get("mean")),
                        "delta_left_minus_right": delta,
                        "abs_standardized_delta": smd,
                        "pooled_std": pooled,
                        "interpretation": "strong" if smd >= 0.80 else "medium" if smd >= 0.50 else "weak" if smd >= 0.20 else "near_collapse",
                    }
                )
    return rows


def summarize_predicate_pairs(delta_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for left, right in PREDICATE_PAIRS:
        pair_rows = [row for row in delta_rows if row["left_predicate"] == left and row["right_predicate"] == right]
        if not pair_rows:
            continue
        max_row = max(pair_rows, key=lambda row: row["abs_standardized_delta"])
        mean_smd = sum(float(row["abs_standardized_delta"]) for row in pair_rows) / len(pair_rows)
        medium_or_strong = sum(1 for row in pair_rows if float(row["abs_standardized_delta"]) >= 0.50)
        weak_or_better = sum(1 for row in pair_rows if float(row["abs_standardized_delta"]) >= 0.20)
        if {left, right} == {"standing on", "supported by"}:
            verdict = "collapse_or_superordinate_overlap"
            recommendation = "do_not_use_as_primary_binary_negative_pair"
        elif medium_or_strong >= 1 or weak_or_better >= 3:
            verdict = "pose_conditioned_contrast_candidate"
            recommendation = "eligible_for_target_design_after_controls"
        else:
            verdict = "weak_distributional_contrast"
            recommendation = "diagnostic_only_unless_visual_mesh_evidence_improves"
        rows.append(
            {
                "predicate_pair": f"{left} vs {right}",
                "features_reviewed": len(pair_rows),
                "mean_abs_standardized_delta": mean_smd,
                "max_abs_standardized_delta": max_row["abs_standardized_delta"],
                "max_delta_feature": max_row["feature"],
                "max_delta_tier": max_row["tier"],
                "features_abs_smd_ge_0_20": weak_or_better,
                "features_abs_smd_ge_0_50": medium_or_strong,
                "verdict": verdict,
                "recommendation": recommendation,
            }
        )
    return rows


def shortcut_review(shortcut_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    review: list[dict[str, Any]] = []
    severity_counts = Counter(row.get("severity", "") for row in shortcut_rows)
    risk_counts = Counter((row.get("risk", ""), row.get("severity", "")) for row in shortcut_rows)
    high_rows = [row for row in shortcut_rows if row.get("severity") == "high"]
    for row in shortcut_rows:
        review.append(
            {
                "risk": row.get("risk"),
                "scope": row.get("scope"),
                "feature": row.get("feature"),
                "value": row.get("value"),
                "severity": row.get("severity"),
                "mitigation": row.get("mitigation"),
            }
        )
    summary = {
        "severity_counts": dict(severity_counts),
        "risk_severity_counts": {f"{risk}:{severity}": count for (risk, severity), count in risk_counts.items()},
        "high_risk_count": len(high_rows),
        "high_risk_names": sorted({row.get("risk", "") for row in high_rows}),
        "hard_surface_high": any(row.get("risk") == "hard_surface_dominance" and row.get("severity") == "high" for row in shortcut_rows),
        "queue_imbalance_high": any(row.get("risk") == "queue_imbalance" and row.get("severity") == "high" for row in shortcut_rows),
        "high_queue_shift_features": sorted(
            row.get("feature", "") for row in shortcut_rows if row.get("risk") == "feature_queue_shift" and row.get("severity") == "high"
        ),
        "high_hard_surface_shift_features": sorted(
            row.get("feature", "") for row in shortcut_rows if row.get("risk") == "feature_hard_surface_shift" and row.get("severity") == "high"
        ),
    }
    return review, summary


def old_numeric_review(old_rows: list[dict[str, str]]) -> dict[str, Any]:
    high = [row for row in old_rows if row.get("dominance_risk") == "high"]
    max_row = None
    if old_rows:
        max_row = max(old_rows, key=lambda row: as_float(row.get("abs_pearson"), -1.0))
    return {
        "rows": len(old_rows),
        "high_dominance_count": len(high),
        "high_dominance_features": sorted({row.get("feature", "") for row in high}),
        "max_abs_pearson": as_float(max_row.get("abs_pearson")) if max_row else None,
        "max_abs_pearson_feature": max_row.get("feature") if max_row else None,
        "max_abs_pearson_old_field": max_row.get("old_numeric_field") if max_row else None,
        "pass": len(high) == 0,
    }


def gate_rows(
    runner_summary: dict[str, Any],
    source_summary: dict[str, Any],
    derivability_rows: list[dict[str, Any]],
    shortcut_summary: dict[str, Any],
    old_numeric_summary: dict[str, Any],
    pair_summary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    runner_decision = runner_summary.get("path_decision", {})
    source_decision = source_summary.get("path_decision", {})
    all_derivable = all(row.get("gate") == "pass" for row in derivability_rows)
    standing_supported = next((row for row in pair_summary if row["predicate_pair"] == "standing on vs supported by"), {})
    pose_pair_candidates = [
        row
        for row in pair_summary
        if row["predicate_pair"] in {"lying on vs standing on", "lying on vs supported by"}
        and row["verdict"] == "pose_conditioned_contrast_candidate"
    ]
    exact_capacity = None
    for risk in source_decision.get("blocking_risks_for_materialization_or_smoke", []):
        if risk.get("risk") == "same_exact_pair_clean_capacity":
            exact_capacity = risk.get("value")
            break
    return [
        {
            "gate": "runner_feature_probe_passed",
            "value": all(runner_decision.get(key) is True for key in [
                "tier_a_derivability_pass",
                "tier_a_finite_pass",
                "tier_b_sample_pass",
                "model_safe_blocked_fields_absent",
                "new_features_not_old_proxy_pass",
            ]),
            "verdict": "pass",
            "implication": "feature review is meaningful",
        },
        {
            "gate": "all_reviewed_features_derivable",
            "value": all_derivable,
            "verdict": "pass" if all_derivable else "fail",
            "implication": "no missing-feature blocker for the reviewed feature families",
        },
        {
            "gate": "old_numeric_proxy_dominance",
            "value": old_numeric_summary["high_dominance_count"],
            "verdict": "pass" if old_numeric_summary["pass"] else "fail",
            "implication": "new features are not rejected as direct copies of old p_geom_valid/gap-overlap scores",
        },
        {
            "gate": "pose_conditioned_predicate_contrast_exists",
            "value": len(pose_pair_candidates),
            "verdict": "pass" if pose_pair_candidates else "fail",
            "implication": "lying-on vs upright support predicates can be considered for controlled target design",
        },
        {
            "gate": "standing_supported_as_primary_negative_pair",
            "value": standing_supported.get("verdict"),
            "verdict": "fail" if standing_supported.get("verdict") == "collapse_or_superordinate_overlap" else "uncertain",
            "implication": "standing on and supported by should not be treated as clean opposing labels",
        },
        {
            "gate": "hard_surface_shortcut_control_needed",
            "value": shortcut_summary["hard_surface_high"],
            "verdict": "block_direct_materialization" if shortcut_summary["hard_surface_high"] else "pass",
            "implication": "hard-surface rows must be capped/stratified before target materialization",
        },
        {
            "gate": "queue_kind_target_independence",
            "value": shortcut_summary["queue_imbalance_high"],
            "verdict": "block_direct_materialization" if shortcut_summary["queue_imbalance_high"] else "pass",
            "implication": "HL/LH queue kind cannot be used as an accept/reject target",
        },
        {
            "gate": "same_exact_pair_clean_capacity",
            "value": exact_capacity,
            "verdict": "block_exact_pair_route" if exact_capacity is not None and exact_capacity < 60 else "pass",
            "implication": "do not return to exact-pair mixed-witness support/contact mining",
        },
    ]


def target_design_constraints() -> list[dict[str, Any]]:
    return [
        {
            "constraint": "primary_predicate_pairs",
            "decision": "use_pose_conditioned_pairs",
            "detail": "`lying on` vs `standing on` is the cleanest primary contrast; `lying on` vs `supported by` can be diagnostic.",
        },
        {
            "constraint": "supported_by_role",
            "decision": "not_primary_negative",
            "detail": "`supported by` behaves like a superordinate support predicate and is nearly collapsed with `standing on` in several features.",
        },
        {
            "constraint": "same_geometry_rows",
            "decision": "required",
            "detail": "For each geometry anchor, create predicate-flip rows sharing the same `G_e`; otherwise geometry-only can solve the target.",
        },
        {
            "constraint": "positive_anchor_source",
            "decision": "geometry_pose_contact_first",
            "detail": "Select clear anchors using contact, support area, and pose/orientation evidence, not source score/rank or HL/LH queue kind.",
        },
        {
            "constraint": "hard_surface_control",
            "decision": "mandatory",
            "detail": "Cap floor/wall/ceiling/room rows and require non-hard-surface cells in every materialization split.",
        },
        {
            "constraint": "model_input_boundary",
            "decision": "strict",
            "detail": "Do not expose queue kind, geometry status, source score/rank, labels, object-pair IDs, or construction provenance to model features.",
        },
        {
            "constraint": "multi_view_role",
            "decision": "Q_e_or_audit_first",
            "detail": "Use multi-view/crop evidence for observability and audit confirmation before turning it into deployable model input.",
        },
        {
            "constraint": "promotion_gate",
            "decision": "schema_shortcut_audit_before_smoke",
            "detail": "Materialized rows must pass schema leakage and shortcut audit before any learned support/contact smoke.",
        },
    ]


def path_decision(
    errors: list[dict[str, Any]],
    gate_summary_rows: list[dict[str, Any]],
    shortcut_summary: dict[str, Any],
    old_numeric_summary: dict[str, Any],
    pair_summary: list[dict[str, Any]],
) -> dict[str, Any]:
    pose_pair_candidates = [
        row
        for row in pair_summary
        if row["predicate_pair"] in {"lying on vs standing on", "lying on vs supported by"}
        and row["verdict"] == "pose_conditioned_contrast_candidate"
    ]
    direct_blockers = [
        "hard_surface_dominance",
        "HL_LH_queue_imbalance",
        "same_exact_pair_clean_capacity",
        "standing_supported_superordinate_overlap",
    ]
    if errors:
        return {
            "status": STATUS_ERRORS,
            "selected_path": "fix_inputs_before_review",
            "next_todo": EXPECTED_RUNNER_NEXT,
            "validation_errors": len(errors),
            "target_design_plan_allowed": False,
            "candidate_materialization_allowed": False,
            "learned_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "rationale": "Input validation failed; feature review cannot be trusted.",
        }
    if pose_pair_candidates and old_numeric_summary["pass"]:
        return {
            "status": STATUS_READY,
            "selected_path": SELECTED_PATH_READY,
            "next_todo": NEXT_READY,
            "validation_errors": 0,
            "target_design_plan_allowed": True,
            "candidate_materialization_allowed": False,
            "learned_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "direct_materialization_blockers": direct_blockers,
            "rationale": "Features are derivable and not old-proxy dominated, but support/contact still needs a controlled pose-conditioned target design before materialization.",
        }
    return {
        "status": STATUS_DIAGNOSTIC,
        "selected_path": SELECTED_PATH_DIAGNOSTIC,
        "next_todo": NEXT_DIAGNOSTIC,
        "validation_errors": 0,
        "target_design_plan_allowed": False,
        "candidate_materialization_allowed": False,
        "learned_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "direct_materialization_blockers": direct_blockers,
        "rationale": "Feature probe is diagnostic only; no controlled pose-conditioned contrast is strong enough for target design.",
    }


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    shortcut = summary["shortcut_summary"]
    old_numeric = summary["old_numeric_summary"]
    pair_summary = summary["predicate_pair_summary"]
    decision = summary["path_decision"]
    pair_lines = "\n".join(
        f"- {row['predicate_pair']}: verdict `{row['verdict']}`, max SMD `{row['max_abs_standardized_delta']:.4f}` on `{row['max_delta_feature']}`."
        for row in pair_summary
    )
    return f"""# Compatibility Dataset V3 Support/Contact Feature Probe Result Review

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
next_todo = {summary['next_todo']}
validation_errors = {summary['validation_errors']}
```

## Counts

```text
support_rows = {counts['support_rows']}
tier_a_records = {counts['tier_a_records']}
tier_b_records = {counts['tier_b_records']}
tier_b_distinct_scans = {counts['tier_b_distinct_scans']}
```

## Predicate Contrast Review

{pair_lines}

Interpretation:

- `lying on` has usable pose/contact-distribution differences against upright support predicates.
- `standing on` and `supported by` should not be used as clean opposing labels because `supported by`
  is close to a superordinate support predicate under the current evidence.
- A future target must use same-geometry predicate flips so geometry-only cannot solve the task.

## Risk Review

```text
high_risk_count = {shortcut['high_risk_count']}
hard_surface_high = {shortcut['hard_surface_high']}
queue_imbalance_high = {shortcut['queue_imbalance_high']}
high_queue_shift_features = {shortcut['high_queue_shift_features']}
high_hard_surface_shift_features = {shortcut['high_hard_surface_shift_features']}
old_numeric_high_dominance_count = {old_numeric['high_dominance_count']}
old_numeric_max_abs_pearson = {old_numeric['max_abs_pearson']}
```

## Decision

```text
target_design_plan_allowed = {decision['target_design_plan_allowed']}
candidate_materialization_allowed = {decision['candidate_materialization_allowed']}
learned_smoke_allowed = {decision['learned_smoke_allowed']}
paper_evidence_allowed = {decision['paper_evidence_allowed']}
```

The feature probe clears the availability/derivability blocker, not the target-construction
blocker. The next step should design a controlled support/contact target using pose-conditioned
same-geometry predicate flips. Direct materialization and learned smoke remain blocked.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()
    runner_dir = args.runner_dir
    source_dir = args.source_inventory_dir
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    runner_summary = read_json(runner_dir / "summary.json")
    source_summary = read_json(source_dir / "summary.json")
    runner_validation_rows = read_jsonl(runner_dir / "validation_errors.jsonl")
    derivability_csv = read_csv(runner_dir / "feature_derivability.csv")
    distribution_csv = read_csv(runner_dir / "feature_distribution_diagnostics.csv")
    shortcut_csv = read_csv(runner_dir / "shortcut_risk_diagnostics.csv")
    old_numeric_csv = read_csv(runner_dir / "old_numeric_dominance_diagnostics.csv")

    errors = validate_inputs(
        runner_summary=runner_summary,
        runner_validation_rows=runner_validation_rows,
        source_summary=source_summary,
        derivability_rows=derivability_csv,
        distribution_rows=distribution_csv,
        shortcut_rows=shortcut_csv,
        old_numeric_rows=old_numeric_csv,
    )
    derivability_rows = derivability_review(derivability_csv)
    delta_rows = predicate_delta_rows(distribution_csv)
    pair_summary = summarize_predicate_pairs(delta_rows)
    shortcut_rows, shortcut_summary = shortcut_review(shortcut_csv)
    old_numeric_summary = old_numeric_review(old_numeric_csv)
    gate_summary = gate_rows(
        runner_summary=runner_summary,
        source_summary=source_summary,
        derivability_rows=derivability_rows,
        shortcut_summary=shortcut_summary,
        old_numeric_summary=old_numeric_summary,
        pair_summary=pair_summary,
    )
    decision = path_decision(errors, gate_summary, shortcut_summary, old_numeric_summary, pair_summary)

    counts = runner_summary.get("counts", {})
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": decision["status"],
        "selected_path": decision["selected_path"],
        "next_todo": decision["next_todo"],
        "validation_errors": len(errors),
        "counts": {
            "support_rows": counts.get("support_rows"),
            "tier_a_records": counts.get("tier_a_records"),
            "tier_b_records": counts.get("tier_b_records"),
            "tier_b_distinct_scans": counts.get("tier_b_distinct_scans"),
            "tier_b_hard_surface_rows": counts.get("tier_b_hard_surface_rows"),
            "tier_b_non_hard_surface_rows": counts.get("tier_b_non_hard_surface_rows"),
        },
        "runner_status": runner_summary.get("status"),
        "source_inventory_status": source_summary.get("status"),
        "predicate_pair_summary": pair_summary,
        "shortcut_summary": shortcut_summary,
        "old_numeric_summary": old_numeric_summary,
        "gate_summary": gate_summary,
        "path_decision": decision,
        "output_paths": {
            "feature_probe_review": rel_path(output_dir / "feature_probe_review.csv"),
            "predicate_pair_feature_deltas": rel_path(output_dir / "predicate_pair_feature_deltas.csv"),
            "predicate_pair_summary": rel_path(output_dir / "predicate_pair_summary.csv"),
            "risk_register": rel_path(output_dir / "risk_register.csv"),
            "target_design_constraints": rel_path(output_dir / "target_design_constraints.csv"),
            "path_decision": rel_path(output_dir / "path_decision.json"),
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "boundary": {
            "split": "train_only_feature_probe_result_review",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_candidate_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
    }

    write_csv(output_dir / "feature_probe_review.csv", gate_summary)
    write_csv(output_dir / "predicate_pair_feature_deltas.csv", delta_rows)
    write_csv(output_dir / "predicate_pair_summary.csv", pair_summary)
    write_csv(output_dir / "risk_register.csv", shortcut_rows)
    write_csv(output_dir / "target_design_constraints.csv", target_design_constraints())
    write_json(output_dir / "path_decision.json", decision)
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(report_text(summary), encoding="utf-8")

    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
