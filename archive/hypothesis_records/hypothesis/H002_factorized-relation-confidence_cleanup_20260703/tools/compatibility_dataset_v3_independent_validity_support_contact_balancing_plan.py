#!/usr/bin/env python3
"""Plan a support/contact-primary independent-validity target for H002."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_CALIBRATION_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_calibration_scope_plan"
)
DEFAULT_SOURCE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_source_inventory"
DEFAULT_STRATUM_PLAN_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan"
)
DEFAULT_SUPPORT_POSE_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_support_contact_balancing_plan"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_calibration_scope_plan_select_support_contact_balancing"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_independent_validity_support_contact_balancing_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_plan_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_plan_ready_for_materialization"
)
STATUS_ERRORS = "h002_compatibility_dataset_v3_independent_validity_support_contact_balancing_plan_input_errors"
SELECTED_PATH = "materialize_support_contact_primary_independent_validity_with_shortcut_audit"
NEXT_TODO = "compatibility_dataset_v3_independent_validity_support_contact_balancing_candidate_materialization"

TARGET_PRIMARY_ROWS = 1200
MIN_PRIMARY_ROWS = 800
MIN_PRIMARY_ROWS_FROM_PREVIOUS = 400
TARGET_PREDICATE_ROWS = {
    "lying on": 600,
    "standing on": 600,
}
TARGET_LABEL_PER_PREDICATE = {
    "lying on": {1: 300, 0: 300},
    "standing on": {1: 300, 0: 300},
}
SUPPORT_FAMILY = "support_contact_pose_conditioned"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibration-dir", type=Path, default=DEFAULT_CALIBRATION_DIR)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--stratum-plan-dir", type=Path, default=DEFAULT_STRATUM_PLAN_DIR)
    parser.add_argument("--support-pose-dir", type=Path, default=DEFAULT_SUPPORT_POSE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
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
                fields.append(key)
                seen.add(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def int_field(row: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(row.get(key, default))
    except (TypeError, ValueError):
        return default


def parse_json_field(row: dict[str, str], key: str) -> Any:
    value = row.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def validate_inputs(
    calibration: dict[str, Any],
    source_summary: dict[str, Any],
    stratum_summary: dict[str, Any],
    support_pose_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if calibration.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_calibration_status", "actual": calibration.get("status")})
    if calibration.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_calibration_next", "actual": calibration.get("next_todo")})
    if calibration.get("validation_errors") != 0:
        errors.append({"error_type": "calibration_validation_errors", "actual": calibration.get("validation_errors")})
    if source_summary.get("status") != "h002_compatibility_dataset_v3_independent_validity_source_inventory_ready_for_materialization_plan":
        errors.append({"error_type": "unexpected_source_inventory_status", "actual": source_summary.get("status")})
    if stratum_summary.get("status") != "h002_compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan_ready":
        errors.append({"error_type": "unexpected_stratum_plan_status", "actual": stratum_summary.get("status")})
    if (
        support_pose_summary.get("status")
        != "h002_compatibility_dataset_v3_support_contact_pose_conditioned_result_review_accept_scoped_Ce_select_multi_family_synthesis"
    ):
        errors.append({"error_type": "unexpected_support_pose_review_status", "actual": support_pose_summary.get("status")})
    for name, summary in [
        ("calibration", calibration),
        ("source_inventory", source_summary),
        ("stratum_plan", stratum_summary),
        ("support_pose_review", support_pose_summary),
    ]:
        boundary = summary.get("boundary", {})
        for key in ["h001_artifacts_modified", "paper_evidence_allowed", "test_usage", "validation_usage"]:
            actual = boundary.get(key)
            if actual is None and key == "paper_evidence_allowed":
                actual = summary.get("paper_evidence_allowed")
            if actual is not False:
                errors.append({"error_type": "boundary_not_false", "summary": name, "key": key, "actual": actual})
    return errors


def support_source_capacity(source_rows: list[dict[str, str]]) -> dict[str, Any]:
    for row in source_rows:
        if row.get("family") == SUPPORT_FAMILY:
            return {
                "family": SUPPORT_FAMILY,
                "rows": int_field(row, "rows"),
                "unique_pairs": int_field(row, "unique_pairs"),
                "source_z_join_rate": float(row.get("source_z_join_rate", 0.0)),
                "geometry_g_join_rate": float(row.get("geometry_g_join_rate", 0.0)),
                "positive_exact_gt_satisfied": int_field(row, "positive_exact_gt_satisfied"),
                "strong_negative_gt_pair_other_predicate_unsatisfied": int_field(
                    row, "strong_negative_gt_pair_other_predicate_unsatisfied"
                ),
                "gt_conflict_exact_unsatisfied": int_field(row, "gt_conflict_exact_unsatisfied"),
                "abstain_no_gt_geometry_satisfied": int_field(row, "abstain_no_gt_geometry_satisfied"),
                "abstain_geometry_uncertain": int_field(row, "abstain_geometry_uncertain"),
                "label_status_counts": parse_json_field(row, "label_status_counts"),
                "geometry_status_counts": parse_json_field(row, "geometry_status_counts"),
            }
    return {}


def support_stratum_counts(quota_rows: list[dict[str, str]]) -> dict[str, Any]:
    support_rows = [row for row in quota_rows if row.get("family") == SUPPORT_FAMILY]
    by_predicate: dict[str, int] = {}
    exact_strata = len(support_rows)
    for row in support_rows:
        predicate = row.get("predicate_label", "unknown")
        by_predicate[predicate] = by_predicate.get(predicate, 0) + int_field(row, "target_total_rows")
    return {
        "exact_predicate_class_rows": sum(by_predicate.values()),
        "exact_predicate_class_strata": exact_strata,
        "by_predicate": dict(sorted(by_predicate.items())),
    }


def predicate_capacity(top_strata_rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for row in top_strata_rows:
        if row.get("axis") != "predicate_label":
            continue
        stratum = parse_json_field(row, "stratum")
        if not isinstance(stratum, list) or len(stratum) != 2:
            continue
        family, predicate = stratum
        if family != SUPPORT_FAMILY:
            continue
        result[str(predicate)] = {
            "positive": int_field(row, "positive"),
            "negative": int_field(row, "negative"),
            "balanced_capacity": int_field(row, "balanced_capacity"),
            "scan_capped_capacity": int_field(row, "scan_capped_capacity"),
            "positive_scans": int_field(row, "positive_scans"),
            "negative_scans": int_field(row, "negative_scans"),
        }
    return result


def support_family_capacity(top_strata_rows: list[dict[str, str]]) -> dict[str, int]:
    for row in top_strata_rows:
        if row.get("axis") != "family":
            continue
        stratum = parse_json_field(row, "stratum")
        if stratum == [SUPPORT_FAMILY]:
            return {
                "positive": int_field(row, "positive"),
                "negative": int_field(row, "negative"),
                "balanced_capacity": int_field(row, "balanced_capacity"),
                "scan_capped_capacity": int_field(row, "scan_capped_capacity"),
                "positive_scans": int_field(row, "positive_scans"),
                "negative_scans": int_field(row, "negative_scans"),
            }
    return {}


def build_capacity_table(
    source_capacity: dict[str, Any],
    family_capacity: dict[str, int],
    pred_capacity: dict[str, dict[str, int]],
    exact_counts: dict[str, Any],
    support_pose_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.append(
        {
            "level": "source_inventory_family",
            "target_source": "GT_anchored_independent_validity",
            "positive": source_capacity.get("positive_exact_gt_satisfied"),
            "negative": source_capacity.get("strong_negative_gt_pair_other_predicate_unsatisfied"),
            "balanced_or_available_rows": 2
            * min(
                int(source_capacity.get("positive_exact_gt_satisfied", 0)),
                int(source_capacity.get("strong_negative_gt_pair_other_predicate_unsatisfied", 0)),
            ),
            "scan_capped_rows": family_capacity.get("scan_capped_capacity"),
            "target_rows": TARGET_PRIMARY_ROWS,
            "meets_min_400": family_capacity.get("scan_capped_capacity", 0) >= MIN_PRIMARY_ROWS_FROM_PREVIOUS,
            "meets_min_800": family_capacity.get("scan_capped_capacity", 0) >= MIN_PRIMARY_ROWS,
            "meets_target_1200": family_capacity.get("scan_capped_capacity", 0) >= TARGET_PRIMARY_ROWS,
            "verdict": "capacity_pass_but_needs_shortcut_controls",
        }
    )
    for predicate, cap in sorted(pred_capacity.items()):
        target = TARGET_PREDICATE_ROWS.get(predicate, 0)
        rows.append(
            {
                "level": f"predicate::{predicate}",
                "target_source": "GT_anchored_independent_validity",
                "positive": cap.get("positive"),
                "negative": cap.get("negative"),
                "balanced_or_available_rows": cap.get("balanced_capacity"),
                "scan_capped_rows": cap.get("scan_capped_capacity"),
                "target_rows": target,
                "meets_min_400": cap.get("scan_capped_capacity", 0) >= MIN_PRIMARY_ROWS_FROM_PREVIOUS,
                "meets_min_800": cap.get("scan_capped_capacity", 0) >= MIN_PRIMARY_ROWS,
                "meets_target_1200": cap.get("scan_capped_capacity", 0) >= target,
                "verdict": "predicate_quota_pass" if cap.get("scan_capped_capacity", 0) >= target else "predicate_quota_deficit",
            }
        )
    rows.append(
        {
            "level": "exact_predicate_x_class_current",
            "target_source": "GT_anchored_independent_validity",
            "positive": int(exact_counts.get("exact_predicate_class_rows", 0)) // 2,
            "negative": int(exact_counts.get("exact_predicate_class_rows", 0)) // 2,
            "balanced_or_available_rows": exact_counts.get("exact_predicate_class_rows"),
            "scan_capped_rows": exact_counts.get("exact_predicate_class_rows"),
            "target_rows": MIN_PRIMARY_ROWS_FROM_PREVIOUS,
            "meets_min_400": int(exact_counts.get("exact_predicate_class_rows", 0)) >= MIN_PRIMARY_ROWS_FROM_PREVIOUS,
            "meets_min_800": int(exact_counts.get("exact_predicate_class_rows", 0)) >= MIN_PRIMARY_ROWS,
            "meets_target_1200": int(exact_counts.get("exact_predicate_class_rows", 0)) >= TARGET_PRIMARY_ROWS,
            "verdict": "reject_as_primary_balance_unit_capacity_88",
        }
    )
    support_pose_counts = support_pose_summary.get("mechanism_result", {}).get("counts", {})
    rows.append(
        {
            "level": "pose_conditioned_constructed_target",
            "target_source": "constructed_Ce_mechanism_auxiliary",
            "positive": support_pose_counts.get("positive"),
            "negative": support_pose_counts.get("negative"),
            "balanced_or_available_rows": support_pose_counts.get("rows"),
            "scan_capped_rows": support_pose_counts.get("rows"),
            "target_rows": MIN_PRIMARY_ROWS_FROM_PREVIOUS,
            "meets_min_400": support_pose_counts.get("rows", 0) >= MIN_PRIMARY_ROWS_FROM_PREVIOUS,
            "meets_min_800": support_pose_counts.get("rows", 0) >= MIN_PRIMARY_ROWS,
            "meets_target_1200": support_pose_counts.get("rows", 0) >= TARGET_PRIMARY_ROWS,
            "verdict": "auxiliary_only_not_independent_validity_gt",
        }
    )
    return rows


def build_route_table(capacity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "route": "continue_exact_predicate_class_balance",
            "verdict": "rejected",
            "evidence": "support/contact exact predicate-class rows remain 88, below the 400-row minimum.",
            "reason": "This preserves the strongest shortcut control but cannot support a primary family claim.",
            "next_action": "do_not_use_as_support_contact_primary_target",
        },
        {
            "route": "reuse_pose_conditioned_constructed_target",
            "verdict": "rejected_as_main",
            "evidence": "400 rows and clean controls exist, but labels are constructed C_e compatibility labels.",
            "reason": "This is useful as an auxiliary mechanism proof, not independent-validity evidence.",
            "next_action": "keep_as_auxiliary_Ce_mechanism_evidence",
        },
        {
            "route": "predicate_balanced_support_contact_independent_validity",
            "verdict": "selected",
            "evidence": "family scan-capped capacity is 2134 rows; lying-on 1370 and standing-on 764 scan-capped rows can support a 1200-row predicate-balanced target.",
            "reason": "This is the strongest feasible path to make support/contact primary while keeping GT-anchored independent validity.",
            "next_action": NEXT_TODO,
        },
        {
            "route": "learned_smoke_or_larger_architecture_now",
            "verdict": "blocked",
            "evidence": "No support/contact-primary model-safe dataset exists yet.",
            "reason": "Architecture changes would only mask target/sampling uncertainty.",
            "next_action": "materialize_and_audit_schema_first",
        },
        {
            "route": "calibrated_p_rel_claim_now",
            "verdict": "blocked",
            "evidence": "The target is still train-only C_e/independent-validity preparation, not held-out p_rel/p_obs evidence.",
            "reason": "Reliability posterior requires held-out/Docker and selective-decision target gates.",
            "next_action": "keep_p_rel_p_obs_claim_blocked",
        },
    ]


def materialization_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "dataset_name": "h002_support_contact_primary_independent_validity_candidates_v1",
        "split": "train_only",
        "target_rows": TARGET_PRIMARY_ROWS,
        "minimum_rows": MIN_PRIMARY_ROWS,
        "family": SUPPORT_FAMILY,
        "predicate_quota": TARGET_PREDICATE_ROWS,
        "label_quota_per_predicate": {
            predicate: {str(label): count for label, count in quota.items()}
            for predicate, quota in TARGET_LABEL_PER_PREDICATE.items()
        },
        "positive_policy": "label_match_status=exact_match and geometry_status=satisfied",
        "negative_policy": "label_match_status in {family_match, pair_has_other_predicate} and geometry_status=unsatisfied",
        "excluded_from_primary": [
            "no_gt_for_pair",
            "gt_conflict_exact_unsatisfied",
            "geometry_uncertain",
            "geometry_unsupported",
        ],
        "balance_unit": "predicate_label first, then class-pair/scan/rank capped sampling",
        "why_not_exact_predicate_class_balance": "Exact predicate-class support/contact capacity is only 88 rows under current independent-validity target.",
        "caps_and_controls": {
            "max_single_scan_share": 0.05,
            "max_single_directed_pair_share": 0.01,
            "max_single_subject_object_class_pair_share": 0.10,
            "max_single_rank_band_share": 0.55,
            "predicate_internal_label_balance_required": True,
            "class_pair_distribution_report_required": True,
            "rank_band_distribution_report_required": True,
            "scan_distribution_report_required": True,
        },
        "feature_boundary": {
            "T_e_allowed": [
                "predicate_label",
                "predicate_text",
                "relation_family",
                "subject_class_label",
                "object_class_label",
            ],
            "Z_e_allowed_but_not_in_Ce": [
                "source_id",
                "semantic_score_raw",
                "semantic_score_norm",
                "semantic_rank",
                "rank_band",
            ],
            "G_e_allowed": [
                "raw_distance_features",
                "raw_height_features",
                "raw_overlap_features",
                "raw_contact_or_gap_features",
                "raw_object_size_features",
                "raw_pair_pose_features",
                "raw_geometry_feature_available_mask",
            ],
            "Q_e_allowed": [
                "raw_geometry_available",
                "raw_geometry_feature_count",
                "object_pair_feature_coverage",
                "mesh_or_point_availability",
            ],
            "blocked_model_inputs": [
                "geometry_status",
                "p_geom_valid",
                "consistency_score",
                "geometry_residual_proxy",
                "label_match_status",
                "matched_gt_ids",
                "matched_predicates",
                "target_pool",
                "selection_pass",
                "hidden provenance",
            ],
        },
        "required_outputs": [
            "candidate_rows.jsonl",
            "model_safe_view.jsonl",
            "hidden_manifest.jsonl",
            "quota_audit.csv",
            "class_pair_balance_audit.csv",
            "schema_precheck.json",
            "validation_errors.jsonl",
        ],
        "required_next_gates": [
            "materialized rows >= 800 and target 1200 if capacity after caps permits",
            "positive/negative balanced within each predicate",
            "model_safe_view has zero blocked construction fields",
            "single-feature shortcut probes below risk threshold before learned smoke",
            "geometry-only and semantic/source-only baselines reported separately",
        ],
    }


def scope_decisions(capacity_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "scope_item": "support_contact_primary_target",
            "decision": "selected_next",
            "reason": "Predicate-level support/contact independent-validity capacity is sufficient for a primary target.",
        },
        {
            "scope_item": "exact_predicate_class_balance",
            "decision": "relax_for_support_contact_only",
            "reason": "It leaves only 88 support/contact rows; use as audit/cap signal, not as the balancing unit.",
        },
        {
            "scope_item": "constructed_pose_conditioned_rows",
            "decision": "auxiliary_only",
            "reason": "They test C_e mechanics but are not independent GT-anchored validity labels.",
        },
        {
            "scope_item": "calibrated_p_rel",
            "decision": "blocked",
            "reason": "No held-out reliability target or selective-decision protocol yet.",
        },
        {
            "scope_item": "paper_promotion",
            "decision": "blocked",
            "reason": "This remains train-only hypothesis planning and has not entered Docker experiment protocol.",
        },
    ]


def write_report(
    path: Path,
    summary: dict[str, Any],
    capacity_rows: list[dict[str, Any]],
    routes: list[dict[str, Any]],
) -> None:
    selected = next(row for row in routes if row["verdict"] == "selected")
    cap_lines = []
    for row in capacity_rows:
        cap_lines.append(
            "- `{level}`: rows `{rows}`, target `{target}`, verdict `{verdict}`".format(
                level=row["level"],
                rows=row["scan_capped_rows"],
                target=row["target_rows"],
                verdict=row["verdict"],
            )
        )
    text = f"""# Compatibility Dataset V3 Independent Validity Support Contact Balancing Plan

Artifact root:

```text
{summary["output_root"]}
```

Status:

```text
status = {summary["status"]}
selected_path = {summary["selected_path"]}
validation_errors = {summary["validation_errors"]}
next_todo = {summary["next_todo"]}
```

## Decision

Selected route:

```text
{selected["route"]}
```

Reason:

{selected["reason"]}

## Capacity

{chr(10).join(cap_lines)}

The earlier exact predicate-class balancing is too strict for support/contact. It keeps strong
shortcut control but leaves only `88` support/contact rows. Predicate-level support/contact
capacity is sufficient: lying-on and standing-on can support a `1200`-row target under the current
scan-capped inventory.

## Contract

The next materializer should build a train-only support/contact-primary independent-validity
candidate set with:

- `1200` target rows, minimum `800`;
- `600` rows for `lying on` and `600` rows for `standing on`;
- `300/300` positive/negative balance within each predicate;
- no `no_gt_for_pair` rows as negatives;
- no `p_geom_valid`, `geometry_status`, label provenance, or construction summaries in model input;
- class-pair, scan, directed-pair, and rank-band caps before learned smoke.

## Blocked

- calibrated `p_rel` / `p_obs`;
- paper-level H002 result;
- all-family relation reliability;
- architecture escalation before candidate materialization and schema shortcut audit.

## Next

```text
{summary["next_todo"]}
```
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    calibration = read_json(args.calibration_dir / "summary.json")
    source_summary = read_json(args.source_dir / "summary.json")
    stratum_summary = read_json(args.stratum_plan_dir / "summary.json")
    support_pose_summary = read_json(args.support_pose_dir / "summary.json")
    source_rows = read_csv(args.source_dir / "family_inventory_table.csv")
    top_strata_rows = read_csv(
        H2_ROOT
        / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan/top_strata.csv"
    )
    quota_rows = read_csv(args.stratum_plan_dir / "stratum_quota_plan.csv")

    errors = validate_inputs(calibration, source_summary, stratum_summary, support_pose_summary)
    for required_path in [
        args.source_dir / "family_inventory_table.csv",
        args.stratum_plan_dir / "stratum_quota_plan.csv",
        H2_ROOT
        / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan/top_strata.csv",
    ]:
        if not required_path.exists():
            errors.append({"error_type": "missing_required_artifact", "path": rel_path(required_path)})

    source_capacity = support_source_capacity(source_rows)
    family_capacity = support_family_capacity(top_strata_rows)
    pred_capacity = predicate_capacity(top_strata_rows)
    exact_counts = support_stratum_counts(quota_rows)
    capacity_rows = build_capacity_table(
        source_capacity,
        family_capacity,
        pred_capacity,
        exact_counts,
        support_pose_summary,
    )
    routes = build_route_table(capacity_rows)
    contract = materialization_contract()
    scope = scope_decisions(capacity_rows)

    status = STATUS_READY if not errors else STATUS_ERRORS
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_support_contact_balancing_inputs",
        "next_todo": NEXT_TODO if not errors else "fix_support_contact_balancing_plan_inputs",
        "validation_errors": len(errors),
        "output_root": rel_path(args.output_dir),
        "inputs": {
            "calibration_scope": rel_path(args.calibration_dir),
            "source_inventory": rel_path(args.source_dir),
            "stratum_materialization_plan": rel_path(args.stratum_plan_dir),
            "support_pose_review": rel_path(args.support_pose_dir),
        },
        "capacity_summary": {
            "source_family_capacity": source_capacity,
            "family_scan_capped_capacity": family_capacity,
            "predicate_scan_capped_capacity": pred_capacity,
            "current_exact_predicate_class_support_rows": exact_counts,
            "target_primary_rows": TARGET_PRIMARY_ROWS,
            "minimum_primary_rows": MIN_PRIMARY_ROWS,
        },
        "selected_route": next(row for row in routes if row["verdict"] == "selected"),
        "materialization_contract": contract,
        "claim_boundary": {
            "allowed_now": "train-only support/contact balancing plan for independent-validity candidate materialization",
            "blocked": [
                "calibrated p_rel/p_obs",
                "paper-level result",
                "held-out performance",
                "all-family 3DSSG relation reliability",
                "learned smoke before schema shortcut audit",
            ],
        },
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_candidate_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_planning",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "capacity_table": rel_path(args.output_dir / "capacity_table.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "scope_decision": rel_path(args.output_dir / "scope_decision.csv"),
            "materialization_contract": rel_path(args.output_dir / "materialization_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "capacity_table.csv", capacity_rows)
    write_jsonl(args.output_dir / "capacity_table.jsonl", capacity_rows)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_jsonl(args.output_dir / "route_decision.jsonl", routes)
    write_csv(args.output_dir / "scope_decision.csv", scope)
    write_jsonl(args.output_dir / "scope_decision.jsonl", scope)
    write_json(args.output_dir / "materialization_contract.json", contract)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", summary, capacity_rows, routes)

    print(
        "status={status} selected={selected} target_rows={target} exact_rows={exact} next={next_todo}".format(
            status=summary["status"],
            selected=summary["selected_path"],
            target=TARGET_PRIMARY_ROWS,
            exact=exact_counts.get("exact_predicate_class_rows"),
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
