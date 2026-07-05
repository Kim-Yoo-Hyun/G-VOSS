#!/usr/bin/env python3
"""Plan exact-stratum repaired materialization for H002 independent validity."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_CAPACITY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan"
)

EXPECTED_INPUT_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan_ready_for_materialization_plan"
)
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan_input_errors"
SELECTED_PATH = "materialize_exact_predicate_class_balanced_independent_validity_rows"
NEXT_TODO = "compatibility_dataset_v3_independent_validity_stratum_repair_candidate_materialization"

TARGET_PRIMARY_ROWS = 1600
TARGET_PAIRS = TARGET_PRIMARY_ROWS // 2
MAX_PAIRS_PER_STRATUM = 125
MIN_PRIMARY_ROWS = 800
MIN_ROWS_PER_CLASS = 400
MIN_RETAINED_EXACT_STRATA = 30
PRIMARY_PREDICATES = {"higher than", "lower than", "standing on", "lying on"}
RELATIVE_VERTICAL_PREDICATES = {"higher than", "lower than"}
SUPPORT_CONTACT_PREDICATES = {"standing on", "lying on"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def family_for_predicate(predicate: str) -> str:
    if predicate in RELATIVE_VERTICAL_PREDICATES:
        return "relative_vertical"
    if predicate in SUPPORT_CONTACT_PREDICATES:
        return "support_contact_pose_conditioned"
    return "unsupported"


def validate_capacity(capacity: dict[str, Any], capacity_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if capacity.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "actual": capacity.get("status")})
    if capacity.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_capacity_next", "actual": capacity.get("next_todo")})
    if capacity.get("validation_errors") != 0:
        errors.append({"error_type": "capacity_validation_errors", "actual": capacity.get("validation_errors")})
    if capacity.get("selected_path") != "materialize_exact_predicate_class_stratum_repaired_independent_validity_target":
        errors.append({"error_type": "unexpected_capacity_selected_path", "actual": capacity.get("selected_path")})
    gate = capacity.get("repair_gate", {})
    if gate.get("repair_ready") is not True:
        errors.append({"error_type": "repair_gate_not_ready", "actual": gate.get("repair_ready")})
    boundary = capacity.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "capacity_boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in ["top_strata.csv", "summary.json", "next_plan_contract.json"]:
        if not (capacity_dir / name).exists():
            errors.append({"error_type": "missing_capacity_artifact", "path": rel_path(capacity_dir / name)})
    return errors


def read_exact_strata(top_strata_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with top_strata_path.open("r", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("axis") != "predicate_x_class_pair":
                continue
            predicate, subject_label, object_label = json.loads(row["stratum"])
            if predicate not in PRIMARY_PREDICATES:
                continue
            positive = int(row["positive"])
            negative = int(row["negative"])
            scan_capped_capacity = int(row["scan_capped_capacity"])
            raw_pairs = min(positive, negative)
            scan_capped_pairs = min(raw_pairs, scan_capped_capacity // 2)
            rows.append(
                {
                    "axis": row["axis"],
                    "family": family_for_predicate(predicate),
                    "predicate_label": predicate,
                    "subject_class_label": subject_label,
                    "object_class_label": object_label,
                    "available_positive": positive,
                    "available_negative": negative,
                    "raw_balanced_capacity_rows": int(row["balanced_capacity"]),
                    "scan_capped_capacity_rows": scan_capped_capacity,
                    "positive_scans": int(row["positive_scans"]),
                    "negative_scans": int(row["negative_scans"]),
                    "available_balanced_pairs_after_scan_cap": scan_capped_pairs,
                    "max_pairs_per_stratum": MAX_PAIRS_PER_STRATUM,
                    "eligible_pairs_after_plan_cap": min(scan_capped_pairs, MAX_PAIRS_PER_STRATUM),
                }
            )
    return rows


def plan_quotas(exact_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Include scarce support/contact exact strata first, then fill with vertical strata."""
    rows = [dict(row) for row in exact_rows]
    for row in rows:
        row["target_positive_quota"] = 0
        row["target_negative_quota"] = 0
        row["target_total_rows"] = 0
        row["materialize"] = False
        row["selection_pass"] = "not_selected"
        row["scope_role"] = "available_exact_stratum"
        row["reason"] = ""

    remaining_pairs = TARGET_PAIRS

    support_rows = sorted(
        [row for row in rows if row["family"] == "support_contact_pose_conditioned"],
        key=lambda row: (-int(row["eligible_pairs_after_plan_cap"]), row["predicate_label"], row["subject_class_label"], row["object_class_label"]),
    )
    for row in support_rows:
        quota = min(int(row["eligible_pairs_after_plan_cap"]), remaining_pairs)
        if quota <= 0:
            continue
        row["target_positive_quota"] = quota
        row["target_negative_quota"] = quota
        row["target_total_rows"] = quota * 2
        row["materialize"] = True
        row["selection_pass"] = "include_all_support_contact_exact_capacity_first"
        row["scope_role"] = "support_contact_diagnostic_slice"
        row["reason"] = "support/contact exact mixed capacity is scarce, so retain all scan-capped exact strata before filling vertical rows"
        remaining_pairs -= quota
        if remaining_pairs == 0:
            break

    vertical_rows = sorted(
        [row for row in rows if row["family"] == "relative_vertical"],
        key=lambda row: (-int(row["eligible_pairs_after_plan_cap"]), -int(row["scan_capped_capacity_rows"]), row["predicate_label"], row["subject_class_label"], row["object_class_label"]),
    )
    for row in vertical_rows:
        if remaining_pairs == 0:
            break
        quota = min(int(row["eligible_pairs_after_plan_cap"]), remaining_pairs)
        if quota <= 0:
            continue
        row["target_positive_quota"] = quota
        row["target_negative_quota"] = quota
        row["target_total_rows"] = quota * 2
        row["materialize"] = True
        row["selection_pass"] = "fill_remaining_quota_with_relative_vertical_exact_strata"
        row["scope_role"] = "primary_exact_stratum_repair_slice"
        row["reason"] = "relative-vertical provides most exact-stratum mixed capacity after support/contact capacity is retained"
        remaining_pairs -= quota

    selected = [row for row in rows if row["materialize"] is True]
    selected.sort(
        key=lambda row: (
            0 if row["family"] == "support_contact_pose_conditioned" else 1,
            row["selection_pass"],
            -int(row["target_total_rows"]),
            row["predicate_label"],
            row["subject_class_label"],
            row["object_class_label"],
        )
    )
    for idx, row in enumerate(selected, start=1):
        row["stratum_id"] = f"exact_predicate_class_{idx:03d}"
        row["selection_order"] = idx
    return selected


def planned_counts(quota_rows: list[dict[str, Any]]) -> dict[str, Any]:
    family_rows: Counter[str] = Counter()
    predicate_rows: Counter[str] = Counter()
    for row in quota_rows:
        family_rows[row["family"]] += int(row["target_total_rows"])
        predicate_rows[row["predicate_label"]] += int(row["target_total_rows"])
    positive = sum(int(row["target_positive_quota"]) for row in quota_rows)
    negative = sum(int(row["target_negative_quota"]) for row in quota_rows)
    support_rows = family_rows.get("support_contact_pose_conditioned", 0)
    return {
        "planned_primary_rows": positive + negative,
        "planned_positive_rows": positive,
        "planned_negative_rows": negative,
        "retained_exact_strata": len(quota_rows),
        "max_pairs_per_stratum": MAX_PAIRS_PER_STRATUM,
        "target_primary_rows": TARGET_PRIMARY_ROWS,
        "by_family": dict(sorted(family_rows.items())),
        "by_predicate": dict(sorted(predicate_rows.items())),
        "support_contact_rows": support_rows,
        "support_contact_scope": "diagnostic_slice" if support_rows < 400 else "primary_family_slice",
    }


def validate_plan(quota_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    counts = planned_counts(quota_rows)
    if counts["planned_primary_rows"] != TARGET_PRIMARY_ROWS:
        errors.append(
            {
                "error_type": "target_primary_rows_not_filled",
                "actual": counts["planned_primary_rows"],
                "expected": TARGET_PRIMARY_ROWS,
            }
        )
    if counts["planned_positive_rows"] != counts["planned_negative_rows"]:
        errors.append(
            {
                "error_type": "primary_label_imbalance",
                "positive": counts["planned_positive_rows"],
                "negative": counts["planned_negative_rows"],
            }
        )
    if counts["planned_positive_rows"] < MIN_ROWS_PER_CLASS or counts["planned_negative_rows"] < MIN_ROWS_PER_CLASS:
        errors.append(
            {
                "error_type": "primary_class_count_below_minimum",
                "positive": counts["planned_positive_rows"],
                "negative": counts["planned_negative_rows"],
                "minimum": MIN_ROWS_PER_CLASS,
            }
        )
    if counts["planned_primary_rows"] < MIN_PRIMARY_ROWS:
        errors.append({"error_type": "primary_rows_below_minimum", "actual": counts["planned_primary_rows"]})
    if counts["retained_exact_strata"] < MIN_RETAINED_EXACT_STRATA:
        errors.append(
            {
                "error_type": "retained_exact_strata_below_minimum",
                "actual": counts["retained_exact_strata"],
                "minimum": MIN_RETAINED_EXACT_STRATA,
            }
        )
    for row in quota_rows:
        if int(row["target_positive_quota"]) != int(row["target_negative_quota"]):
            errors.append({"error_type": "stratum_not_balanced", "stratum_id": row.get("stratum_id")})
        if int(row["target_positive_quota"]) > int(row["eligible_pairs_after_plan_cap"]):
            errors.append(
                {
                    "error_type": "quota_exceeds_plan_cap",
                    "stratum_id": row.get("stratum_id"),
                    "quota": row["target_positive_quota"],
                    "available": row["eligible_pairs_after_plan_cap"],
                }
            )
    return errors


def warning_rows(quota_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = planned_counts(quota_rows)
    warnings: list[dict[str, Any]] = []
    support_rows = counts["by_family"].get("support_contact_pose_conditioned", 0)
    vertical_rows = counts["by_family"].get("relative_vertical", 0)
    if support_rows < 400:
        warnings.append(
            {
                "warning_type": "support_contact_exact_stratum_capacity_small",
                "support_contact_rows": support_rows,
                "interpretation": "support/contact remains diagnostic in this repaired independent-validity target",
            }
        )
    if vertical_rows > support_rows * 4:
        warnings.append(
            {
                "warning_type": "family_distribution_imbalanced_after_exact_stratum_repair",
                "relative_vertical_rows": vertical_rows,
                "support_contact_rows": support_rows,
                "interpretation": "do not claim this target proves family-balanced generality",
            }
        )
    return warnings


def row_schema_contract() -> dict[str, Any]:
    return {
        "schema_name": "h002_exact_stratum_repaired_independent_validity_row_v1",
        "split": "train_only",
        "target_scope": {
            "primary_binary": "exact predicate x subject/object class balanced independent validity",
            "nonbinary_abstain": "deferred until primary repaired target passes schema audit",
            "support_contact_slice": "diagnostic due exact-stratum capacity limit",
        },
        "required_outputs_for_next_materializer": [
            "candidate_rows.jsonl",
            "model_safe_view.jsonl",
            "hidden_manifest.jsonl",
            "quota_audit.csv",
            "schema_precheck.json",
            "validation_errors.jsonl",
        ],
        "required_top_level_fields": [
            "row_id",
            "split",
            "family",
            "predicate_label",
            "subject_class_label",
            "object_class_label",
            "feature_blocks",
            "labels",
            "controls_hidden",
        ],
        "feature_blocks_allowed": {
            "T_e": [
                "predicate_label",
                "predicate_text",
                "relation_family",
                "subject_class_label",
                "object_class_label",
            ],
            "Z_e_safe": [
                "source_id",
                "semantic_score_raw",
                "semantic_score_norm",
                "semantic_rank",
                "rank_band",
            ],
            "G_e_raw": [
                "raw_distance_features",
                "raw_height_features",
                "raw_overlap_features",
                "raw_contact_or_gap_features",
                "raw_object_size_features",
                "raw_pair_pose_features",
                "raw_geometry_feature_available_mask",
            ],
            "Q_e_safe": [
                "raw_geometry_available",
                "raw_geometry_feature_count",
                "object_pair_feature_coverage",
                "mesh_or_point_availability",
            ],
        },
        "labels": {
            "C_e_validity": "1 for exact GT+satisfied geometry, 0 for GT-pair other predicate/family mismatch+unsatisfied geometry",
            "p_rel": "accept / reject for primary binary rows",
            "p_obs": "observable for primary binary rows",
        },
        "primary_binary_filter": {
            "include_only": ["positive", "negative"],
            "exclude": ["no_gt", "uncertain", "gt_conflict", "abstain"],
        },
        "grouped_evaluation_key": "scan_id + directed_pair_id",
    }


def blocked_field_rows() -> list[dict[str, Any]]:
    blocked = [
        ("identity.scan_id", "split/group/provenance leakage; keep only as hidden group key"),
        ("identity.subgraph_id", "split/group/provenance leakage"),
        ("identity.directed_pair_id", "endpoint identity leakage; keep only as hidden group key"),
        ("identity.prediction_id", "source row identity leakage"),
        ("label.label_match_status", "target construction label"),
        ("label.matched_gt_ids", "target construction label"),
        ("label.matched_predicates", "target construction label"),
        ("geometry.geometry_status", "construction summary that directly defines this target"),
        ("geometry.p_geom_valid", "rule-based construction/calibration summary; baseline or teacher only"),
        ("geometry.consistency_score", "construction summary derived from rule status"),
        ("geometry.geometry_residual_proxy", "construction residual summary; hidden audit only"),
        ("geometry.geometry_axis", "construction shortcut for relation family/status"),
        ("target_pool", "sampling provenance"),
        ("selection_pass", "sampling provenance"),
        ("scope_role", "sampling provenance"),
        ("labels.*", "target label"),
        ("controls_hidden.*", "audit-only controls"),
        ("provenance.*", "artifact provenance"),
    ]
    return [{"field": field, "reason": reason, "model_input_allowed": False} for field, reason in blocked]


def matching_policy() -> dict[str, Any]:
    return {
        "eligible_stratum": "predicate_label + subject_class_label + object_class_label with both positive and negative rows",
        "label_policy": {
            "positive": "label_match_status=exact_match and geometry_status=satisfied",
            "negative": "label_match_status in {family_match, pair_has_other_predicate} and geometry_status=unsatisfied",
            "no_gt": "deferred; not negative",
            "gt_conflict": "deferred/audit; not primary",
        },
        "quota_policy": {
            "target_primary_rows": TARGET_PRIMARY_ROWS,
            "target_positive_rows": TARGET_PAIRS,
            "target_negative_rows": TARGET_PAIRS,
            "balance_unit": "exact predicate x subject/object class stratum",
            "max_pairs_per_stratum": MAX_PAIRS_PER_STRATUM,
            "support_contact_policy": "include all scan-capped exact mixed support/contact capacity first",
            "vertical_policy": "fill remaining rows with relative-vertical exact mixed strata",
        },
        "within_stratum_selection": [
            "select equal positive and negative rows per retained exact stratum",
            "round-robin scans to respect scan cap",
            "round-robin rank bands after exact stratum balancing when rows exist",
            "prefer raw G_e feature availability but do not use construction summaries as model input",
        ],
        "blocked_for_model_input": [
            "geometry_status",
            "p_geom_valid",
            "consistency_score",
            "geometry_residual_proxy",
            "label_match_status",
            "target_pool",
            "selection_pass",
            "hidden GT provenance",
        ],
    }


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Materialize train-only rows following exact predicate-class quota plan, then audit schema shortcuts before any learned smoke.",
        "required_inputs": [
            "train match_rows.jsonl",
            "stratum_quota_plan.csv",
            "row_schema_contract.json",
            "matching_policy.json",
        ],
        "required_outputs": [
            "candidate_rows.jsonl",
            "model_safe_view.jsonl",
            "hidden_manifest.jsonl",
            "quota_audit.csv",
            "schema_precheck.json",
            "validation_errors.jsonl",
        ],
        "success_gates": [
            "primary rows exactly 1600",
            "positive/negative exactly 800/800",
            "each retained exact predicate-class stratum is internally balanced",
            "retained exact strata >= 30",
            "blocked construction summaries absent from model_safe_view",
            "support/contact slice reported as diagnostic if below 400 rows",
        ],
        "blocked_actions": [
            "do not run learned smoke in the materializer",
            "do not use validation/test rows",
            "do not modify H001 artifacts",
            "do not use geometry_status or p_geom_valid as model input",
            "do not claim family-balanced generality from this target",
        ],
    }


def build_decision(capacity: dict[str, Any], quota_rows: list[dict[str, Any]], errors: list[dict[str, Any]]) -> dict[str, Any]:
    counts = planned_counts(quota_rows) if quota_rows else {}
    warnings = warning_rows(quota_rows) if quota_rows else []
    status = STATUS_READY if not errors else STATUS_ERRORS
    return {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_materialization_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "blocked_field_table": blocked_field_rows(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_capacity_status": capacity.get("status"),
        "matching_policy": matching_policy(),
        "next_plan_contract": next_plan_contract(),
        "next_todo": NEXT_TODO if not errors else "fix_stratum_repair_materialization_plan_inputs",
        "planned_counts": counts,
        "quota_summary": {
            "target_primary_rows": TARGET_PRIMARY_ROWS,
            "target_positive_rows": TARGET_PAIRS,
            "target_negative_rows": TARGET_PAIRS,
            "max_pairs_per_stratum": MAX_PAIRS_PER_STRATUM,
            "min_retained_exact_strata": MIN_RETAINED_EXACT_STRATA,
        },
        "row_schema_contract": row_schema_contract(),
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH if not errors else "fix_inputs_before_materialization",
        "status": status,
        "validation_errors": len(errors),
        "warnings": warnings,
    }


def build_report(decision: dict[str, Any], quota_rows: list[dict[str, Any]]) -> str:
    counts = decision.get("planned_counts", {})
    lines = [
        "# H002 Independent Validity Stratum Repair Materialization Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {decision['status']}",
        f"selected_path = {decision['selected_path']}",
        f"validation_errors = {decision['validation_errors']}",
        f"next_todo = {decision['next_todo']}",
        "```",
        "",
        "## Purpose",
        "",
        "The previous independent-validity rows were balanced overall but shortcut-prone because",
        "`predicate_x_class_pair` almost recovered the label. This plan freezes the next",
        "materialization as an exact-stratum repair: every retained",
        "`predicate_label + subject_class_label + object_class_label` stratum must contain equal",
        "positive and negative rows.",
        "",
        "## Planned Counts",
        "",
        "```text",
        f"target_primary_rows = {decision['quota_summary']['target_primary_rows']}",
        f"planned_primary_rows = {counts.get('planned_primary_rows')}",
        f"planned_positive_rows = {counts.get('planned_positive_rows')}",
        f"planned_negative_rows = {counts.get('planned_negative_rows')}",
        f"retained_exact_strata = {counts.get('retained_exact_strata')}",
        f"max_pairs_per_stratum = {decision['quota_summary']['max_pairs_per_stratum']}",
        "```",
        "",
        "Family distribution:",
        "",
        "| Family | Planned Rows | Interpretation |",
        "| --- | ---: | --- |",
    ]
    by_family = counts.get("by_family", {})
    for family, value in by_family.items():
        interpretation = "primary exact-stratum repair slice"
        if family == "support_contact_pose_conditioned" and value < 400:
            interpretation = "diagnostic slice due limited exact-stratum capacity"
        lines.append(f"| `{family}` | `{value}` | {interpretation} |")
    lines.extend(
        [
            "",
            "Predicate distribution:",
            "",
            "| Predicate | Planned Rows |",
            "| --- | ---: |",
        ]
    )
    for predicate, value in counts.get("by_predicate", {}).items():
        lines.append(f"| `{predicate}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Quota Policy",
            "",
            "- Select only exact predicate-class strata with both labels.",
            "- Balance positive and negative rows inside every retained stratum.",
            "- Cap each stratum at `125` positive/negative pairs.",
            "- Include all scan-capped support/contact exact mixed capacity first, because it is scarce.",
            "- Fill the remaining quota with relative-vertical exact mixed strata.",
            "- Keep nonbinary/no-GT/uncertain rows deferred until this primary repaired target passes schema audit.",
            "",
            "## Caveat",
            "",
            "This is not a family-balanced generality target. Full train has enough exact-stratum capacity",
            "for shortcut repair, but support/contact contributes only a small diagnostic slice under exact",
            "predicate-class balancing. If the next materialization passes shortcut audit, it supports the",
            "independent-validity mechanism most strongly for `relative_vertical`, with support/contact used",
            "as a capacity-limited stress slice.",
            "",
            "## Blocked Model Inputs",
            "",
            "`geometry_status`, `p_geom_valid`, `consistency_score`, residual summaries, target pools,",
            "`label_match_status`, hidden GT provenance, scan ids, and selection metadata must remain hidden.",
            "Raw metric geometry features can be used as `G_e_raw`.",
            "",
            "## Selected Strata Preview",
            "",
            "| Stratum | Family | Pos Quota | Neg Quota | Rows | Role |",
            "| --- | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for row in quota_rows[:20]:
        stratum = f"{row['predicate_label']} / {row['subject_class_label']} -> {row['object_class_label']}"
        lines.append(
            f"| `{stratum}` | `{row['family']}` | {row['target_positive_quota']} | "
            f"{row['target_negative_quota']} | {row['target_total_rows']} | `{row['scope_role']}` |"
        )
    if len(quota_rows) > 20:
        lines.append(f"| ... | ... | ... | ... | ... | `{len(quota_rows) - 20} more strata` |")
    if decision.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        for warning in decision["warnings"]:
            lines.append(f"- `{warning['warning_type']}`: {warning['interpretation']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only materialization plan.",
            "- No row materialization in this stage.",
            "- No learned model or learned smoke.",
            "- No validation/test usage.",
            "- No H001 artifact modification.",
            "- Not paper evidence.",
            "",
            "## Next",
            "",
            "```text",
            decision["next_todo"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    capacity = read_json(args.capacity_dir / "summary.json")
    input_errors = validate_capacity(capacity, args.capacity_dir)

    exact_rows: list[dict[str, Any]] = []
    quota_rows: list[dict[str, Any]] = []
    plan_errors: list[dict[str, Any]] = []
    if not input_errors:
        exact_rows = read_exact_strata(args.capacity_dir / "top_strata.csv")
        quota_rows = plan_quotas(exact_rows)
        plan_errors = validate_plan(quota_rows)

    errors = input_errors + plan_errors
    decision = build_decision(capacity, quota_rows, errors)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", decision)
    write_json(output_dir / "row_schema_contract.json", decision["row_schema_contract"])
    write_json(output_dir / "matching_policy.json", decision["matching_policy"])
    write_json(output_dir / "next_plan_contract.json", decision["next_plan_contract"])
    write_csv(output_dir / "stratum_quota_plan.csv", quota_rows)
    write_csv(output_dir / "blocked_field_table.csv", decision["blocked_field_table"])
    write_jsonl(output_dir / "warnings.jsonl", decision["warnings"])
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(build_report(decision, quota_rows), encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
