#!/usr/bin/env python3
"""Scan full train capacity for exact-stratum repair of independent validity."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
RGA_ROOT = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_path_decision_after_schema_shortcut_audit"
)
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan"

EXPECTED_INPUT_STATUS = "h002_compatibility_dataset_v3_independent_validity_path_decision_select_stratum_repair_capacity_scan"
EXPECTED_INPUT_NEXT = "compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan_ready_for_materialization_plan"
STATUS_BLOCKED = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan_blocked_insufficient_capacity"
STATUS_ERRORS = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_capacity_scan_input_errors"
SELECTED_PATH_READY = "materialize_exact_predicate_class_stratum_repaired_independent_validity_target"
SELECTED_PATH_BLOCKED = "freeze_independent_validity_target_as_diagnostic"
NEXT_READY = "compatibility_dataset_v3_independent_validity_stratum_repair_materialization_plan"
NEXT_BLOCKED = "compatibility_dataset_v3_independent_validity_diagnostic_freeze_synthesis"

PRIMARY_FAMILY_PREDICATES = {
    "relative_vertical": {"higher than", "lower than"},
    "support_contact_pose_conditioned": {"standing on", "lying on"},
}
RAW_MATCH_FAMILY_TO_TARGET = {
    "relative_vertical": "relative_vertical",
    "support_contact": "support_contact_pose_conditioned",
}

MIN_REPAIRED_PRIMARY_ROWS = 800
MIN_REPAIRED_PER_CLASS = 400
MIN_MIXED_EXACT_STRATA = 30
MIN_SCAN_CAPPED_ROWS = 600
SCAN_SHARE_CAP = 0.08
PREVIEW_PER_LABEL = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION_DIR)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def safe_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def target_family(row: dict[str, Any]) -> str | None:
    predicate = row.get("predicate", {})
    family = RAW_MATCH_FAMILY_TO_TARGET.get(str(predicate.get("predicate_family")))
    if family is None:
        return None
    if str(predicate.get("predicate_label")) not in PRIMARY_FAMILY_PREDICATES[family]:
        return None
    return family


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


def primary_label(row: dict[str, Any]) -> int | None:
    label_status = row.get("label", {}).get("label_match_status")
    geometry_status = row.get("geometry", {}).get("geometry_status")
    if label_status == "exact_match" and geometry_status == "satisfied":
        return 1
    if label_status in {"family_match", "pair_has_other_predicate"} and geometry_status == "unsatisfied":
        return 0
    return None


def rank_band(row: dict[str, Any]) -> str:
    rga = row.get("rga", {})
    if rga.get("rank_band"):
        return str(rga["rank_band"])
    rank = safe_int(row.get("semantic", {}).get("rank_in_context"))
    if rank is None:
        return "rank_unknown"
    if rank <= 50:
        return "top50"
    if rank <= 100:
        return "top100_only"
    if rank <= 200:
        return "rank_101_200"
    if rank <= 500:
        return "rank_201_500"
    if rank <= 1000:
        return "rank_501_1000"
    return "rank_gt1000"


def axis_key(row: dict[str, Any], axis: str, family: str) -> tuple[Any, ...]:
    edge = row.get("edge", {})
    predicate = row.get("predicate", {})
    subject = str(edge.get("subject_label"))
    obj = str(edge.get("object_label"))
    pred = str(predicate.get("predicate_label"))
    if axis == "family":
        return (family,)
    if axis == "predicate_label":
        return (family, pred)
    if axis == "subject_object_class_pair":
        return (subject, obj)
    if axis == "predicate_x_class_pair":
        return (pred, subject, obj)
    if axis == "predicate_x_class_pair_x_rank_band":
        return (pred, subject, obj, rank_band(row))
    raise ValueError(axis)


def visible_row(row: dict[str, Any], label_y: int, family: str) -> dict[str, Any]:
    identity = row.get("identity", {})
    edge = row.get("edge", {})
    predicate = row.get("predicate", {})
    semantic = row.get("semantic", {})
    geometry = row.get("geometry", {})
    label = row.get("label", {})
    return {
        "family": family,
        "label_y": label_y,
        "label_match_status": label.get("label_match_status"),
        "object_label": edge.get("object_label"),
        "p_geom_valid": geometry.get("p_geom_valid"),
        "predicate_label": predicate.get("predicate_label"),
        "rank_band": rank_band(row),
        "scan_id": identity.get("scan_id"),
        "semantic_rank": semantic.get("rank_in_context"),
        "semantic_score_norm": semantic.get("semantic_score_norm"),
        "subject_label": edge.get("subject_label"),
    }


def validate_inputs(path_decision: dict[str, Any], match_rows: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if path_decision.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_path_decision_status", "actual": path_decision.get("status")})
    if path_decision.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_path_decision_next", "actual": path_decision.get("next_todo")})
    if path_decision.get("validation_errors") != 0:
        errors.append({"error_type": "path_decision_validation_errors", "actual": path_decision.get("validation_errors")})
    boundary = path_decision.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed", "runs_learned_smoke"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def scan_capped_min_class(scan_counter: Counter[str], target_m: int) -> int:
    cap = max(1, int(target_m * SCAN_SHARE_CAP))
    return sum(min(count, cap) for count in scan_counter.values())


def scan_capped_pair_capacity(pos_scans: Counter[str], neg_scans: Counter[str], raw_m: int) -> int:
    if raw_m <= 0:
        return 0
    for m in range(raw_m, 0, -1):
        if scan_capped_min_class(pos_scans, m) >= m and scan_capped_min_class(neg_scans, m) >= m:
            return 2 * m
    return 0


def compute_axis_summary(
    axis: str,
    counts: dict[tuple[Any, ...], Counter[int]],
    scan_counts: dict[tuple[Any, ...], dict[int, Counter[str]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_capacity = 0
    scan_capped_capacity = 0
    mixed_groups = 0
    top: list[dict[str, Any]] = []
    for key, counter in counts.items():
        pos = counter[1]
        neg = counter[0]
        balanced = 2 * min(pos, neg)
        if balanced > 0:
            mixed_groups += 1
            capped = scan_capped_pair_capacity(scan_counts[key][1], scan_counts[key][0], min(pos, neg))
            raw_capacity += balanced
            scan_capped_capacity += capped
            top.append(
                {
                    "axis": axis,
                    "stratum": json.dumps(key, ensure_ascii=False),
                    "positive": pos,
                    "negative": neg,
                    "balanced_capacity": balanced,
                    "scan_capped_capacity": capped,
                    "positive_scans": len(scan_counts[key][1]),
                    "negative_scans": len(scan_counts[key][0]),
                    "rows": pos + neg,
                }
            )
    top.sort(key=lambda row: (row["scan_capped_capacity"], row["balanced_capacity"], row["rows"]), reverse=True)
    summary = {
        "axis": axis,
        "groups": len(counts),
        "mixed_groups": mixed_groups,
        "balanced_capacity": raw_capacity,
        "balanced_positive_capacity": raw_capacity // 2,
        "balanced_negative_capacity": raw_capacity // 2,
        "scan_capped_capacity": scan_capped_capacity,
        "scan_capped_positive_capacity": scan_capped_capacity // 2,
        "scan_capped_negative_capacity": scan_capped_capacity // 2,
        "meets_raw_repair_gate": raw_capacity >= MIN_REPAIRED_PRIMARY_ROWS,
        "meets_scan_capped_gate": scan_capped_capacity >= MIN_SCAN_CAPPED_ROWS,
    }
    return summary, top[:40]


def scan_match_rows(match_rows: Path) -> dict[str, Any]:
    axes = [
        "family",
        "predicate_label",
        "subject_object_class_pair",
        "predicate_x_class_pair",
        "predicate_x_class_pair_x_rank_band",
    ]
    axis_counts: dict[str, dict[tuple[Any, ...], Counter[int]]] = {
        axis: defaultdict(Counter) for axis in axes
    }
    axis_scan_counts: dict[str, dict[tuple[Any, ...], dict[int, Counter[str]]]] = {
        axis: defaultdict(lambda: {0: Counter(), 1: Counter()}) for axis in axes
    }
    preview_by_exact: dict[tuple[Any, ...], dict[int, list[dict[str, Any]]]] = defaultdict(lambda: {0: [], 1: []})
    primary_counts: Counter[str] = Counter()
    family_label_counts: dict[str, Counter[int]] = defaultdict(Counter)
    predicate_label_counts: dict[str, Counter[int]] = defaultdict(Counter)

    total_rows = 0
    selected_family_rows = 0
    primary_rows = 0
    source_z_join = 0
    geometry_g_join = 0

    with match_rows.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            total_rows += 1
            row = json.loads(line)
            family = target_family(row)
            if family is None:
                continue
            selected_family_rows += 1
            label_y = primary_label(row)
            if label_y is None:
                continue
            primary_rows += 1
            source_z_join += int(has_source_z(row))
            geometry_g_join += int(has_geometry_g(row))
            identity = row.get("identity", {})
            scan_id = str(identity.get("scan_id"))
            predicate = str(row.get("predicate", {}).get("predicate_label"))
            primary_counts["positive" if label_y == 1 else "negative"] += 1
            family_label_counts[family][label_y] += 1
            predicate_label_counts[predicate][label_y] += 1

            for axis in axes:
                key = axis_key(row, axis, family)
                axis_counts[axis][key][label_y] += 1
                axis_scan_counts[axis][key][label_y][scan_id] += 1

            exact_key = axis_key(row, "predicate_x_class_pair", family)
            if len(preview_by_exact[exact_key][label_y]) < PREVIEW_PER_LABEL:
                preview_by_exact[exact_key][label_y].append(visible_row(row, label_y, family))

    axis_summary_rows: list[dict[str, Any]] = []
    top_strata_rows: list[dict[str, Any]] = []
    for axis in axes:
        summary, top = compute_axis_summary(axis, axis_counts[axis], axis_scan_counts[axis])
        axis_summary_rows.append(summary)
        top_strata_rows.extend(top)

    exact_counts = axis_counts["predicate_x_class_pair"]
    exact_top = sorted(
        [
            {
                "stratum": json.dumps(key, ensure_ascii=False),
                "positive": counter[1],
                "negative": counter[0],
                "balanced_capacity": 2 * min(counter[1], counter[0]),
                "positive_preview": preview_by_exact[key][1],
                "negative_preview": preview_by_exact[key][0],
            }
            for key, counter in exact_counts.items()
            if counter[0] > 0 and counter[1] > 0
        ],
        key=lambda row: (row["balanced_capacity"], row["positive"] + row["negative"]),
        reverse=True,
    )[:80]

    return {
        "axis_summary_rows": axis_summary_rows,
        "exact_mixed_strata_preview": exact_top,
        "family_label_counts": {
            family: {"positive": counter[1], "negative": counter[0]} for family, counter in sorted(family_label_counts.items())
        },
        "geometry_g_join_rate_primary": geometry_g_join / primary_rows if primary_rows else 0.0,
        "predicate_label_counts": {
            predicate: {"positive": counter[1], "negative": counter[0]}
            for predicate, counter in sorted(predicate_label_counts.items())
        },
        "primary_counts": dict(primary_counts),
        "primary_rows": primary_rows,
        "selected_family_rows": selected_family_rows,
        "source_z_join_rate_primary": source_z_join / primary_rows if primary_rows else 0.0,
        "top_strata_rows": top_strata_rows,
        "total_match_rows": total_rows,
    }


def build_route_table(exact_summary: dict[str, Any]) -> list[dict[str, Any]]:
    ready = (
        exact_summary["balanced_capacity"] >= MIN_REPAIRED_PRIMARY_ROWS
        and exact_summary["balanced_positive_capacity"] >= MIN_REPAIRED_PER_CLASS
        and exact_summary["mixed_groups"] >= MIN_MIXED_EXACT_STRATA
        and exact_summary["scan_capped_capacity"] >= MIN_SCAN_CAPPED_ROWS
    )
    return [
        {
            "route": "materialize_exact_predicate_class_repair_target",
            "verdict": "selected" if ready else "reject",
            "evidence": (
                f"exact mixed strata {exact_summary['mixed_groups']}, raw capacity {exact_summary['balanced_capacity']}, "
                f"scan-capped capacity {exact_summary['scan_capped_capacity']}."
            ),
            "reason": "This controls the strongest semantic shortcut observed in the previous audit.",
            "next_action": NEXT_READY if ready else "insufficient_exact_stratum_capacity",
        },
        {
            "route": "materialize_class_pair_only_repair_target",
            "verdict": "reject",
            "evidence": "Previous audit showed predicate_x_class_pair is stronger than class-pair alone.",
            "reason": "Class-pair-only control would leave predicate-conditioned shortcut unresolved.",
            "next_action": "do_not_use",
        },
        {
            "route": "use_geometry_status_or_p_geom_valid_as_model_input",
            "verdict": "reject",
            "evidence": "Those fields are construction summaries from the target rule.",
            "reason": "They would collapse the task into reproducing the label construction.",
            "next_action": "keep_blocked",
        },
        {
            "route": "freeze_independent_validity_target",
            "verdict": "fallback" if ready else "selected",
            "evidence": "If exact stratum repair lacks capacity, independent validity remains diagnostic only.",
            "reason": "H002 should not train on a shortcut-prone target.",
            "next_action": NEXT_BLOCKED if not ready else "not_needed_now",
        },
    ]


def build_next_contract(ready: bool) -> dict[str, Any]:
    if ready:
        return {
            "next_todo": NEXT_READY,
            "purpose": "Materialize a train-only independent-validity target balanced within exact predicate x subject/object class strata.",
            "required_controls": [
                "select only exact predicate x subject/object class strata with both labels",
                "balance positive and negative rows within each retained stratum",
                "apply scan caps and rank-band diversity after exact semantic-stratum balance",
                "exclude geometry_status, p_geom_valid, consistency_score, residual, target_pool, label_match_status, and hidden provenance from model input",
                "write hidden manifest and sanitized primary view separately",
            ],
            "success_gates": [
                "primary rows >= 800",
                "positive/negative >= 400/400",
                "predicate_x_class_pair shortcut <= low risk in schema audit",
                "raw G_e features remain available",
            ],
        }
    return {
        "next_todo": NEXT_BLOCKED,
        "purpose": "Freeze independent validity as diagnostic and synthesize why a deployable p_rel target needs a different source of independent labels.",
        "required_controls": [
            "do not run learned smoke on current independent validity rows",
            "preserve current artifacts as diagnostic evidence",
            "return to external/human/multiview reliability target design if p_rel remains a goal",
        ],
    }


def build_summary(path_decision: dict[str, Any], scan: dict[str, Any], input_errors: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    exact = next(row for row in scan["axis_summary_rows"] if row["axis"] == "predicate_x_class_pair")
    ready = (
        exact["balanced_capacity"] >= MIN_REPAIRED_PRIMARY_ROWS
        and exact["balanced_positive_capacity"] >= MIN_REPAIRED_PER_CLASS
        and exact["mixed_groups"] >= MIN_MIXED_EXACT_STRATA
        and exact["scan_capped_capacity"] >= MIN_SCAN_CAPPED_ROWS
    )
    if input_errors:
        status = STATUS_ERRORS
        selected_path = "fix_stratum_repair_capacity_scan_inputs"
        next_todo = "fix_independent_validity_stratum_repair_capacity_scan_inputs"
    elif ready:
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
            "runs_learned_smoke": False,
            "split": "train_only_full_train_capacity_scan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "full_train_scan": {
            "geometry_g_join_rate_primary": scan["geometry_g_join_rate_primary"],
            "primary_counts": scan["primary_counts"],
            "primary_rows": scan["primary_rows"],
            "selected_family_rows": scan["selected_family_rows"],
            "source_z_join_rate_primary": scan["source_z_join_rate_primary"],
            "total_match_rows": scan["total_match_rows"],
        },
        "input_path_decision_status": path_decision.get("status"),
        "next_todo": next_todo,
        "output_paths": {
            "axis_capacity": rel_path(output_dir / "axis_capacity.csv"),
            "exact_mixed_strata_preview": rel_path(output_dir / "exact_mixed_strata_preview.jsonl"),
            "family_label_counts": rel_path(output_dir / "family_label_counts.csv"),
            "next_plan_contract": rel_path(output_dir / "next_plan_contract.json"),
            "predicate_label_counts": rel_path(output_dir / "predicate_label_counts.csv"),
            "report": rel_path(output_dir / "report.md"),
            "route_table": rel_path(output_dir / "route_table.csv"),
            "summary": rel_path(output_dir / "summary.json"),
            "top_strata": rel_path(output_dir / "top_strata.csv"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "repair_gate": {
            "exact_predicate_class_balanced_capacity": exact["balanced_capacity"],
            "exact_predicate_class_mixed_groups": exact["mixed_groups"],
            "exact_predicate_class_scan_capped_capacity": exact["scan_capped_capacity"],
            "min_mixed_exact_strata": MIN_MIXED_EXACT_STRATA,
            "min_repaired_primary_rows": MIN_REPAIRED_PRIMARY_ROWS,
            "min_repaired_per_class": MIN_REPAIRED_PER_CLASS,
            "min_scan_capped_rows": MIN_SCAN_CAPPED_ROWS,
            "repair_ready": ready,
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(input_errors),
    }


def rows_from_counts(table: dict[str, dict[str, int]]) -> list[dict[str, Any]]:
    return [
        {"key": key, "positive": counts["positive"], "negative": counts["negative"], "rows": counts["positive"] + counts["negative"]}
        for key, counts in sorted(table.items())
    ]


def build_report(summary: dict[str, Any], axis_rows: list[dict[str, Any]], route_rows: list[dict[str, Any]]) -> str:
    gate = summary["repair_gate"]
    scan = summary["full_train_scan"]
    lines = [
        "# H002 Independent Validity Stratum Repair Capacity Scan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Full Train Scan",
        "",
        "```text",
        f"total_match_rows = {scan['total_match_rows']}",
        f"selected_family_rows = {scan['selected_family_rows']}",
        f"primary_rows = {scan['primary_rows']}",
        f"primary_positive = {scan['primary_counts'].get('positive', 0)}",
        f"primary_negative = {scan['primary_counts'].get('negative', 0)}",
        "```",
        "",
        "## Axis Capacity",
        "",
        "| Axis | Groups | Mixed Groups | Raw Balanced Capacity | Scan-Capped Capacity |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in axis_rows:
        lines.append(
            f"| `{row['axis']}` | {row['groups']} | {row['mixed_groups']} | {row['balanced_capacity']} | {row['scan_capped_capacity']} |"
        )
    lines.extend(
        [
            "",
            "## Repair Gate",
            "",
            "```text",
            f"exact_predicate_class_mixed_groups = {gate['exact_predicate_class_mixed_groups']}",
            f"exact_predicate_class_balanced_capacity = {gate['exact_predicate_class_balanced_capacity']}",
            f"exact_predicate_class_scan_capped_capacity = {gate['exact_predicate_class_scan_capped_capacity']}",
            f"repair_ready = {gate['repair_ready']}",
            "```",
            "",
            "## Route Table",
            "",
            "| Route | Verdict | Next Action |",
            "| --- | --- | --- |",
        ]
    )
    for row in route_rows:
        lines.append(f"| `{row['route']}` | `{row['verdict']}` | `{row['next_action']}` |")
    lines.extend(["", "## Next", "", "```text", summary["next_todo"], "```", ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    path_decision = read_json(args.path_decision_dir / "summary.json")
    input_errors = validate_inputs(path_decision, args.match_rows)
    scan = {
        "axis_summary_rows": [],
        "exact_mixed_strata_preview": [],
        "family_label_counts": {},
        "geometry_g_join_rate_primary": 0.0,
        "predicate_label_counts": {},
        "primary_counts": {},
        "primary_rows": 0,
        "selected_family_rows": 0,
        "source_z_join_rate_primary": 0.0,
        "top_strata_rows": [],
        "total_match_rows": 0,
    }
    if not input_errors:
        scan = scan_match_rows(args.match_rows)
    summary = build_summary(path_decision, scan, input_errors, args.output_dir)
    exact = next((row for row in scan["axis_summary_rows"] if row["axis"] == "predicate_x_class_pair"), {"balanced_capacity": 0})
    ready = bool(summary["repair_gate"]["repair_ready"])
    routes = build_route_table(exact)

    write_csv(args.output_dir / "axis_capacity.csv", scan["axis_summary_rows"])
    write_csv(args.output_dir / "top_strata.csv", scan["top_strata_rows"])
    write_jsonl(args.output_dir / "exact_mixed_strata_preview.jsonl", scan["exact_mixed_strata_preview"])
    write_csv(args.output_dir / "family_label_counts.csv", rows_from_counts(scan["family_label_counts"]))
    write_csv(args.output_dir / "predicate_label_counts.csv", rows_from_counts(scan["predicate_label_counts"]))
    write_csv(args.output_dir / "route_table.csv", routes)
    write_json(args.output_dir / "next_plan_contract.json", build_next_contract(ready))
    write_jsonl(args.output_dir / "validation_errors.jsonl", input_errors)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(build_report(summary, scan["axis_summary_rows"], routes), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": summary["status"],
                "selected_path": summary["selected_path"],
                "next_todo": summary["next_todo"],
                "validation_errors": len(input_errors),
                "repair_gate": summary["repair_gate"],
            },
            sort_keys=True,
        )
    )
    return 1 if input_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
