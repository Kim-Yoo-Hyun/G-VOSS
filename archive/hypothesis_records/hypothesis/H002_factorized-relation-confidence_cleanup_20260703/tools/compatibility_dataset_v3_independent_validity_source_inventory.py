#!/usr/bin/env python3
"""Inventory train-side GT/source/geometry capacity for the H002 independent validity target."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_target_plan"
DEFAULT_MATCH_ROWS = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga/match_rows.jsonl"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_source_inventory"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_independent_validity_target_plan_ready"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_independent_validity_source_inventory"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_source_inventory_v1"
STATUS_READY = "h002_compatibility_dataset_v3_independent_validity_source_inventory_ready_for_materialization_plan"
STATUS_BLOCKED = "h002_compatibility_dataset_v3_independent_validity_source_inventory_blocked"
STATUS_ERRORS = "h002_compatibility_dataset_v3_independent_validity_source_inventory_input_errors"
SELECTED_PATH_READY = "materialize_gt_anchored_independent_validity_rows"
SELECTED_PATH_BLOCKED = "freeze_independent_validity_inventory_diagnostic"
NEXT_READY = "compatibility_dataset_v3_independent_validity_materialization_plan"
NEXT_BLOCKED = "compatibility_dataset_v3_independent_validity_blocker_review"

PRIMARY_FAMILY_PREDICATES = {
    "relative_vertical": {"higher than", "lower than"},
    "support_contact_pose_conditioned": {"standing on", "lying on"},
}

RAW_MATCH_FAMILY_TO_TARGET = {
    "relative_vertical": "relative_vertical",
    "support_contact": "support_contact_pose_conditioned",
}

MIN_EXACT_SATISFIED = 100
MIN_STRONG_NEGATIVE = 100
MIN_GEOMETRY_JOIN_RATE = 0.90
MAX_NO_GT_AS_NEGATIVE_ALLOWED = 0
PREVIEW_PER_BUCKET = 8


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
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


def validate_inputs(plan: dict[str, Any], match_rows: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan.get("status")})
    if plan.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan.get("next_todo")})
    if plan.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors", "actual": plan.get("validation_errors")})
    boundary = plan.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": boundary.get(key)})
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def has_source_z(row: dict[str, Any]) -> bool:
    semantic = row.get("semantic", {})
    return (
        semantic.get("semantic_score_raw") is not None
        and semantic.get("semantic_score_norm") is not None
        and semantic.get("rank_in_context") is not None
    )


def has_geometry_g(row: dict[str, Any]) -> bool:
    geometry = row.get("geometry", {})
    return bool(geometry.get("geometry_checkable") is True and geometry.get("raw_features") is not None)


def target_family(row: dict[str, Any]) -> str | None:
    predicate = row.get("predicate", {})
    label = predicate.get("predicate_label")
    raw_family = predicate.get("predicate_family")
    family = RAW_MATCH_FAMILY_TO_TARGET.get(str(raw_family))
    if family is None:
        return None
    if str(label) not in PRIMARY_FAMILY_PREDICATES[family]:
        return None
    return family


def compact_preview(row: dict[str, Any], bucket: str) -> dict[str, Any]:
    identity = row.get("identity", {})
    edge = row.get("edge", {})
    predicate = row.get("predicate", {})
    label = row.get("label", {})
    geometry = row.get("geometry", {})
    semantic = row.get("semantic", {})
    rga = row.get("rga", {})
    return {
        "bucket": bucket,
        "prediction_id": identity.get("prediction_id"),
        "scan_id": identity.get("scan_id"),
        "subgraph_id": identity.get("subgraph_id"),
        "subject_id": identity.get("subject_id"),
        "object_id": identity.get("object_id"),
        "subject_label": edge.get("subject_label"),
        "predicate_label": predicate.get("predicate_label"),
        "object_label": edge.get("object_label"),
        "label_match_status": label.get("label_match_status"),
        "matched_predicates": label.get("matched_predicates", []),
        "geometry_status": geometry.get("geometry_status"),
        "p_geom_valid": geometry.get("p_geom_valid"),
        "semantic_rank": semantic.get("rank_in_context"),
        "semantic_score_raw": semantic.get("semantic_score_raw"),
        "rank_band": rga.get("rank_band"),
    }


def bucket_for_row(row: dict[str, Any]) -> str | None:
    label_status = row.get("label", {}).get("label_match_status")
    geometry_status = row.get("geometry", {}).get("geometry_status")
    if label_status == "exact_match" and geometry_status == "satisfied":
        return "positive_exact_gt_satisfied"
    if label_status == "exact_match" and geometry_status == "unsatisfied":
        return "gt_conflict_exact_unsatisfied"
    if label_status in {"family_match", "pair_has_other_predicate"} and geometry_status == "unsatisfied":
        return "strong_negative_gt_pair_other_predicate_unsatisfied"
    if label_status == "no_gt_for_pair" and geometry_status == "satisfied":
        return "abstain_no_gt_geometry_satisfied"
    if label_status == "no_gt_for_pair" and geometry_status == "unsatisfied":
        return "audit_no_gt_geometry_unsatisfied"
    if geometry_status == "uncertain":
        return "abstain_geometry_uncertain"
    return None


def scan_match_rows(match_rows: Path) -> dict[str, Any]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    unique_pairs: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    previews: dict[str, list[dict[str, Any]]] = defaultdict(list)
    rank_bands: dict[str, Counter[str]] = defaultdict(Counter)
    predicate_counts: dict[str, Counter[str]] = defaultdict(Counter)

    total_rows = 0
    selected_rows = 0
    with match_rows.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            total_rows += 1
            row = json.loads(line)
            family = target_family(row)
            if family is None:
                continue
            selected_rows += 1
            identity = row.get("identity", {})
            label = row.get("label", {})
            geometry = row.get("geometry", {})
            semantic = row.get("semantic", {})
            predicate = row.get("predicate", {})
            rga = row.get("rga", {})

            pair_id = str(identity.get("directed_pair_id"))
            label_status = str(label.get("label_match_status"))
            geometry_status = str(geometry.get("geometry_status"))
            predicate_label = str(predicate.get("predicate_label"))
            rank_band = str(rga.get("rank_band"))

            counters[family]["rows"] += 1
            counters[family][f"label_status::{label_status}"] += 1
            counters[family][f"geometry_status::{geometry_status}"] += 1
            counters[family]["source_z_join"] += int(has_source_z(row))
            counters[family]["geometry_g_join"] += int(has_geometry_g(row))
            counters[family]["observable"] += int(has_geometry_g(row) and geometry_status in {"satisfied", "unsatisfied", "uncertain"})
            counters[family]["positive_exact_gt_satisfied"] += int(label_status == "exact_match" and geometry_status == "satisfied")
            counters[family]["positive_exact_gt_checkable"] += int(label_status == "exact_match" and has_geometry_g(row))
            counters[family]["gt_conflict_exact_unsatisfied"] += int(label_status == "exact_match" and geometry_status == "unsatisfied")
            counters[family]["strong_negative_gt_pair_other_predicate_unsatisfied"] += int(
                label_status in {"family_match", "pair_has_other_predicate"} and geometry_status == "unsatisfied"
            )
            counters[family]["strong_negative_same_family_unsatisfied"] += int(
                label_status == "family_match" and geometry_status == "unsatisfied"
            )
            counters[family]["strong_negative_other_family_unsatisfied"] += int(
                label_status == "pair_has_other_predicate" and geometry_status == "unsatisfied"
            )
            counters[family]["abstain_no_gt_geometry_satisfied"] += int(
                label_status == "no_gt_for_pair" and geometry_status == "satisfied"
            )
            counters[family]["audit_no_gt_geometry_unsatisfied"] += int(
                label_status == "no_gt_for_pair" and geometry_status == "unsatisfied"
            )
            counters[family]["abstain_geometry_uncertain"] += int(geometry_status == "uncertain")
            counters[family]["forbidden_no_gt_negative_used"] += 0

            unique_pairs[family]["all"].add(pair_id)
            unique_pairs[family][f"label_status::{label_status}"].add(pair_id)
            unique_pairs[family][f"geometry_status::{geometry_status}"].add(pair_id)
            if label_status == "exact_match" and geometry_status == "satisfied":
                unique_pairs[family]["positive_exact_gt_satisfied"].add(pair_id)
            if label_status in {"family_match", "pair_has_other_predicate"} and geometry_status == "unsatisfied":
                unique_pairs[family]["strong_negative_gt_pair_other_predicate_unsatisfied"].add(pair_id)
            if label_status == "no_gt_for_pair" and geometry_status == "satisfied":
                unique_pairs[family]["abstain_no_gt_geometry_satisfied"].add(pair_id)

            predicate_counts[family][predicate_label] += 1
            rank_bands[family][rank_band] += 1

            bucket = bucket_for_row(row)
            if bucket and len(previews[f"{family}::{bucket}"]) < PREVIEW_PER_BUCKET:
                previews[f"{family}::{bucket}"].append(compact_preview(row, bucket))

    family_stats: dict[str, dict[str, Any]] = {}
    for family, counter in counters.items():
        rows = counter["rows"]
        geom_join = counter["geometry_g_join"]
        source_join = counter["source_z_join"]
        strong_neg = counter["strong_negative_gt_pair_other_predicate_unsatisfied"]
        exact_sat = counter["positive_exact_gt_satisfied"]
        family_stats[family] = {
            "rows": rows,
            "unique_pairs": len(unique_pairs[family]["all"]),
            "source_z_join": source_join,
            "source_z_join_rate": source_join / rows if rows else 0.0,
            "geometry_g_join": geom_join,
            "geometry_g_join_rate": geom_join / rows if rows else 0.0,
            "label_status_counts": {
                key.split("::", 1)[1]: value for key, value in counter.items() if key.startswith("label_status::")
            },
            "geometry_status_counts": {
                key.split("::", 1)[1]: value for key, value in counter.items() if key.startswith("geometry_status::")
            },
            "predicate_counts": dict(predicate_counts[family]),
            "rank_band_counts": dict(rank_bands[family]),
            "positive_exact_gt_satisfied": exact_sat,
            "positive_exact_gt_checkable": counter["positive_exact_gt_checkable"],
            "gt_conflict_exact_unsatisfied": counter["gt_conflict_exact_unsatisfied"],
            "strong_negative_gt_pair_other_predicate_unsatisfied": strong_neg,
            "strong_negative_same_family_unsatisfied": counter["strong_negative_same_family_unsatisfied"],
            "strong_negative_other_family_unsatisfied": counter["strong_negative_other_family_unsatisfied"],
            "abstain_no_gt_geometry_satisfied": counter["abstain_no_gt_geometry_satisfied"],
            "audit_no_gt_geometry_unsatisfied": counter["audit_no_gt_geometry_unsatisfied"],
            "abstain_geometry_uncertain": counter["abstain_geometry_uncertain"],
            "forbidden_no_gt_negative_used": counter["forbidden_no_gt_negative_used"],
            "unique_positive_exact_gt_satisfied_pairs": len(unique_pairs[family]["positive_exact_gt_satisfied"]),
            "unique_strong_negative_pairs": len(unique_pairs[family]["strong_negative_gt_pair_other_predicate_unsatisfied"]),
            "unique_no_gt_satisfied_pairs": len(unique_pairs[family]["abstain_no_gt_geometry_satisfied"]),
        }

    return {
        "total_match_rows_scanned": total_rows,
        "selected_primary_rows": selected_rows,
        "family_stats": family_stats,
        "candidate_preview_rows": [row for rows in previews.values() for row in rows],
    }


def family_rows(scan: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in ["relative_vertical", "support_contact_pose_conditioned"]:
        stats = scan["family_stats"].get(family, {})
        total = stats.get("rows", 0)
        rows.append(
            {
                "family": family,
                "rows": total,
                "unique_pairs": stats.get("unique_pairs", 0),
                "source_z_join": stats.get("source_z_join", 0),
                "source_z_join_rate": round(float(stats.get("source_z_join_rate", 0.0)), 6),
                "geometry_g_join": stats.get("geometry_g_join", 0),
                "geometry_g_join_rate": round(float(stats.get("geometry_g_join_rate", 0.0)), 6),
                "positive_exact_gt_satisfied": stats.get("positive_exact_gt_satisfied", 0),
                "positive_exact_gt_checkable": stats.get("positive_exact_gt_checkable", 0),
                "strong_negative_gt_pair_other_predicate_unsatisfied": stats.get(
                    "strong_negative_gt_pair_other_predicate_unsatisfied", 0
                ),
                "gt_conflict_exact_unsatisfied": stats.get("gt_conflict_exact_unsatisfied", 0),
                "abstain_no_gt_geometry_satisfied": stats.get("abstain_no_gt_geometry_satisfied", 0),
                "audit_no_gt_geometry_unsatisfied": stats.get("audit_no_gt_geometry_unsatisfied", 0),
                "abstain_geometry_uncertain": stats.get("abstain_geometry_uncertain", 0),
                "label_status_counts": json.dumps(stats.get("label_status_counts", {}), sort_keys=True),
                "geometry_status_counts": json.dumps(stats.get("geometry_status_counts", {}), sort_keys=True),
            }
        )
    return rows


def capacity_decision_rows(scan: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family in ["relative_vertical", "support_contact_pose_conditioned"]:
        stats = scan["family_stats"].get(family, {})
        positives = int(stats.get("positive_exact_gt_satisfied", 0))
        negatives = int(stats.get("strong_negative_gt_pair_other_predicate_unsatisfied", 0))
        geom_rate = float(stats.get("geometry_g_join_rate", 0.0))
        forbidden = int(stats.get("forbidden_no_gt_negative_used", 0))
        rows.append(
            {
                "family": family,
                "positive_gate": positives >= MIN_EXACT_SATISFIED,
                "positive_exact_gt_satisfied": positives,
                "negative_gate": negatives >= MIN_STRONG_NEGATIVE,
                "strong_negative_gt_pair_other_predicate_unsatisfied": negatives,
                "geometry_join_gate": geom_rate >= MIN_GEOMETRY_JOIN_RATE,
                "geometry_g_join_rate": round(geom_rate, 6),
                "no_gt_negative_policy_gate": forbidden <= MAX_NO_GT_AS_NEGATIVE_ALLOWED,
                "forbidden_no_gt_negative_used": forbidden,
                "materialization_feasible": (
                    positives >= MIN_EXACT_SATISFIED
                    and negatives >= MIN_STRONG_NEGATIVE
                    and geom_rate >= MIN_GEOMETRY_JOIN_RATE
                    and forbidden <= MAX_NO_GT_AS_NEGATIVE_ALLOWED
                ),
            }
        )
    return rows


def target_pool_rows(scan: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for family, stats in scan["family_stats"].items():
        pools = [
            (
                "positive_exact_gt_satisfied",
                "positive",
                "GT predicate matches candidate and geometry is satisfied",
                stats.get("positive_exact_gt_satisfied", 0),
                stats.get("unique_positive_exact_gt_satisfied_pairs", 0),
            ),
            (
                "strong_negative_gt_pair_other_predicate_unsatisfied",
                "negative_candidate",
                "pair has another GT predicate or same-family mismatch and candidate geometry is unsatisfied",
                stats.get("strong_negative_gt_pair_other_predicate_unsatisfied", 0),
                stats.get("unique_strong_negative_pairs", 0),
            ),
            (
                "gt_conflict_exact_unsatisfied",
                "audit_required",
                "GT predicate matches candidate but geometry is unsatisfied; possible GT/geometry conflict",
                stats.get("gt_conflict_exact_unsatisfied", 0),
                "n/a",
            ),
            (
                "abstain_no_gt_geometry_satisfied",
                "abstain_or_audit",
                "no GT for pair but geometry supports candidate; likely annotation sparsity or false positive",
                stats.get("abstain_no_gt_geometry_satisfied", 0),
                stats.get("unique_no_gt_satisfied_pairs", 0),
            ),
            (
                "audit_no_gt_geometry_unsatisfied",
                "audit_or_control",
                "no GT for pair and geometry contradicts candidate; not automatic negative",
                stats.get("audit_no_gt_geometry_unsatisfied", 0),
                "n/a",
            ),
            (
                "abstain_geometry_uncertain",
                "abstain",
                "geometry is uncertain, so p_obs should handle decision availability",
                stats.get("abstain_geometry_uncertain", 0),
                "n/a",
            ),
        ]
        for name, role, policy, count, unique_count in pools:
            rows.append(
                {
                    "family": family,
                    "pool": name,
                    "target_role": role,
                    "count": count,
                    "unique_pair_count": unique_count,
                    "policy": policy,
                }
            )
    return rows


def build_decision(scan: dict[str, Any], input_errors: list[dict[str, Any]]) -> dict[str, Any]:
    family_gate_rows = capacity_decision_rows(scan)
    families_ready = [row["family"] for row in family_gate_rows if row["materialization_feasible"]]
    if input_errors:
        status = STATUS_ERRORS
        selected_path = "fix_source_inventory_inputs"
        next_todo = "fix_independent_validity_source_inventory_inputs"
    elif families_ready:
        status = STATUS_READY
        selected_path = SELECTED_PATH_READY
        next_todo = NEXT_READY
    else:
        status = STATUS_BLOCKED
        selected_path = SELECTED_PATH_BLOCKED
        next_todo = NEXT_BLOCKED

    return {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "split": "train_only_source_inventory",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "capacity_decision_table": family_gate_rows,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "families_ready_for_materialization_plan": families_ready,
        "family_inventory_table": family_rows(scan),
        "input_match_rows": rel_path(DEFAULT_MATCH_ROWS),
        "next_todo": next_todo,
        "policy": {
            "no_gt_as_negative": "forbidden",
            "positive_source": "exact GT match with satisfied geometry",
            "negative_source": "GT-pair other-predicate or same-family mismatch with unsatisfied geometry",
            "abstain_source": "no-GT geometry-supported, geometry-uncertain, or low-coverage cases",
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "source_inventory": {
            "selected_primary_rows": scan["selected_primary_rows"],
            "total_match_rows_scanned": scan["total_match_rows_scanned"],
        },
        "status": status,
        "target_pool_table": target_pool_rows(scan),
        "validation_errors": len(input_errors),
    }


def next_plan_contract(decision: dict[str, Any]) -> dict[str, Any]:
    return {
        "next_todo": decision["next_todo"],
        "purpose": "Materialize independent train-side validity rows only for families that passed GT/source/geometry/hard-negative inventory gates.",
        "families_ready": decision["families_ready_for_materialization_plan"],
        "required_materialization_rules": [
            "use exact GT + geometry satisfied as positive candidates",
            "use same-family or GT-pair other-predicate geometry-unsatisfied rows as negative candidates",
            "keep no-GT geometry-supported rows as abstain/audit, not negative",
            "preserve grouped split by scan/pair",
            "exclude hidden label/construction fields from model views",
            "run schema/shortcut audit before learned smoke",
        ],
        "blocked_until_materialization_plan": [
            "learned smoke",
            "p_rel/p_obs promotion",
            "paper-level Docker evidence",
            "adding attachment/proximity as primary independent target",
        ],
        "success_condition": [
            "row quotas by family and target role",
            "blocked-field schema",
            "balanced or explicitly weighted class plan",
            "hard-negative matching policy",
            "abstain/no-GT handling policy",
            "next schema/shortcut audit gate",
        ],
    }


def build_report(decision: dict[str, Any]) -> str:
    lines = [
        "# H002 Independent Validity Source Inventory",
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
        "## Inventory Summary",
        "",
        "```text",
        f"total_match_rows_scanned = {decision['source_inventory']['total_match_rows_scanned']}",
        f"selected_primary_rows = {decision['source_inventory']['selected_primary_rows']}",
        f"families_ready = {decision['families_ready_for_materialization_plan']}",
        "```",
        "",
        "## Family Inventory",
        "",
        "| Family | Rows | Source Z Join | Geometry G Join | Exact GT Satisfied | Strong Negatives | No-GT Satisfied Abstain |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in decision["family_inventory_table"]:
        lines.append(
            f"| `{row['family']}` | `{row['rows']}` | `{row['source_z_join_rate']}` | "
            f"`{row['geometry_g_join_rate']}` | `{row['positive_exact_gt_satisfied']}` | "
            f"`{row['strong_negative_gt_pair_other_predicate_unsatisfied']}` | "
            f"`{row['abstain_no_gt_geometry_satisfied']}` |"
        )

    lines.extend(
        [
            "",
            "## Capacity Gates",
            "",
            "| Family | Positive Gate | Negative Gate | Geometry Join Gate | Materialization Feasible |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in decision["capacity_decision_table"]:
        lines.append(
            f"| `{row['family']}` | `{row['positive_gate']}` ({row['positive_exact_gt_satisfied']}) | "
            f"`{row['negative_gate']}` ({row['strong_negative_gt_pair_other_predicate_unsatisfied']}) | "
            f"`{row['geometry_join_gate']}` ({row['geometry_g_join_rate']}) | "
            f"`{row['materialization_feasible']}` |"
        )

    lines.extend(
        [
            "",
            "## Target Pool Policy",
            "",
            "| Family | Pool | Role | Count | Policy |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in decision["target_pool_table"]:
        lines.append(f"| `{row['family']}` | `{row['pool']}` | `{row['target_role']}` | `{row['count']}` | {row['policy']} |")

    lines.extend(
        [
            "",
            "## Decision",
            "",
            "The inventory is ready for a materialization plan if at least one primary family passes",
            "positive, strong-negative, geometry-join, and no-GT-policy gates. This stage does not",
            "materialize rows and does not train a model.",
            "",
            "No-GT rows remain abstain/audit candidates. They are not used as negative labels.",
            "",
            "## Boundary",
            "",
            "- Train-only source inventory.",
            "- No validation/test usage.",
            "- No row materialization.",
            "- No learned model trained.",
            "- No H001 artifact modification.",
            "- No paper-level evidence promotion.",
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
    plan = read_json(args.plan_dir / "summary.json")
    input_errors = validate_inputs(plan, args.match_rows)
    scan = {"total_match_rows_scanned": 0, "selected_primary_rows": 0, "family_stats": {}, "candidate_preview_rows": []}
    if not input_errors:
        scan = scan_match_rows(args.match_rows)
    decision = build_decision(scan, input_errors)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", decision)
    write_json(output_dir / "next_plan_contract.json", next_plan_contract(decision))
    write_csv(output_dir / "family_inventory_table.csv", decision["family_inventory_table"])
    write_csv(output_dir / "capacity_decision_table.csv", decision["capacity_decision_table"])
    write_csv(output_dir / "target_pool_table.csv", decision["target_pool_table"])
    write_jsonl(output_dir / "candidate_pool_preview.jsonl", scan["candidate_preview_rows"])
    write_jsonl(output_dir / "validation_errors.jsonl", input_errors)
    (output_dir / "report.md").write_text(build_report(decision), encoding="utf-8")
    return 1 if input_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
