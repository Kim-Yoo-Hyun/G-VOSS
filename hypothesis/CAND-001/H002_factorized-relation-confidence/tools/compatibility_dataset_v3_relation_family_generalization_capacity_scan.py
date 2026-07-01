#!/usr/bin/env python3
"""Scan relation-family capacity after H002 all-family scope synthesis."""

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

DEFAULT_SCOPE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze"
)
DEFAULT_TRAIN_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relation_family_generalization_capacity_scan"

EXPECTED_SCOPE_STATUS = (
    "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_ready"
)
EXPECTED_SCOPE_NEXT = "compatibility_dataset_v3_relation_family_generalization_capacity_scan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_relation_family_generalization_capacity_scan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_relation_family_generalization_capacity_scan_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_relation_family_generalization_capacity_scan_input_errors"
SELECTED_PATH = "select_proximity_close_by_target_plan_with_all_family_eligibility_table"
NEXT_TODO = "compatibility_dataset_v3_proximity_close_by_target_plan"

MIN_QUEUE_ROWS = 1000
MIN_EXACT_MATCH_ROWS = 200
MIN_MIXED_CLASS_GROUPS = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope-dir", type=Path, default=DEFAULT_SCOPE_DIR)
    parser.add_argument("--train-rga-dir", type=Path, default=DEFAULT_TRAIN_RGA_DIR)
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


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_inputs(scope: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if scope.get("status") != EXPECTED_SCOPE_STATUS:
        errors.append({"error_type": "unexpected_scope_status", "actual": scope.get("status")})
    if scope.get("next_todo") != EXPECTED_SCOPE_NEXT:
        errors.append({"error_type": "unexpected_scope_next_todo", "actual": scope.get("next_todo")})
    if scope.get("validation_errors") != 0:
        errors.append({"error_type": "scope_validation_errors_present", "actual": scope.get("validation_errors")})
    boundary = scope.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = args.train_rga_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_queue", "path": rel_path(path)})
    for name in ["all_relation_types.csv", "family_priority_table.csv"]:
        path = args.scope_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_scope_artifact", "path": rel_path(path)})
    return errors


def class_pair_key(row: dict[str, Any]) -> str:
    return f"{row.get('subject_label')}->{row.get('object_label')}"


def scan_queues(queue_dir: Path) -> tuple[dict[str, dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    stats: dict[str, dict[str, Any]] = {}
    groups: dict[str, dict[str, Counter[str]]] = defaultdict(lambda: defaultdict(Counter))
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for queue_name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = queue_dir / queue_name
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                row = json.loads(line)
                predicate = str(row.get("predicate_label"))
                stat = stats.setdefault(
                    predicate,
                    {
                        "predicate_label": predicate,
                        "family": row.get("predicate_family"),
                        "queue_rows": 0,
                        "hl_rows": 0,
                        "lh_rows": 0,
                        "label_match_status_counts": Counter(),
                        "geometry_status_counts": Counter(),
                        "rank_band_counts": Counter(),
                        "class_pair_counts": Counter(),
                        "scan_counts": Counter(),
                        "directed_pair_count": 0,
                        "_directed_pairs": set(),
                    },
                )
                stat["queue_rows"] += 1
                if queue_name == "train_hl_queue.jsonl":
                    stat["hl_rows"] += 1
                else:
                    stat["lh_rows"] += 1
                stat["label_match_status_counts"][row.get("label_match_status")] += 1
                stat["geometry_status_counts"][row.get("geometry_status")] += 1
                stat["rank_band_counts"][row.get("rank_band")] += 1
                stat["class_pair_counts"][class_pair_key(row)] += 1
                stat["scan_counts"][row.get("scan_id")] += 1
                directed_key = f"{row.get('scan_id')}::{row.get('subgraph_id')}::{row.get('subject_id')}->{row.get('object_id')}"
                stat["_directed_pairs"].add(directed_key)
                groups[predicate][class_pair_key(row)][str(row.get("label_match_status"))] += 1
                if len(examples[predicate]) < 5:
                    examples[predicate].append(
                        {
                            "predicate_label": predicate,
                            "queue": queue_name,
                            "label_match_status": row.get("label_match_status"),
                            "geometry_status": row.get("geometry_status"),
                            "rank_band": row.get("rank_band"),
                            "subject_label": row.get("subject_label"),
                            "object_label": row.get("object_label"),
                            "p_geom_valid": row.get("p_geom_valid"),
                        }
                    )
    for stat in stats.values():
        stat["directed_pair_count"] = len(stat.pop("_directed_pairs"))
    mixed_group_rows: dict[str, dict[str, int]] = {}
    for predicate, class_groups in groups.items():
        mixed = 0
        exact_vs_other = 0
        exact_rows_in_mixed = 0
        other_rows_in_mixed = 0
        for counts in class_groups.values():
            exact = counts.get("exact_match", 0)
            other = sum(count for key, count in counts.items() if key != "exact_match")
            if exact and other:
                mixed += 1
                exact_vs_other += 2 * min(exact, other)
                exact_rows_in_mixed += exact
                other_rows_in_mixed += other
        mixed_group_rows[predicate] = {
            "mixed_class_pair_groups_exact_vs_other": mixed,
            "balanced_rows_exact_vs_other": exact_vs_other,
            "exact_rows_in_mixed_groups": exact_rows_in_mixed,
            "other_rows_in_mixed_groups": other_rows_in_mixed,
        }
    for predicate, values in mixed_group_rows.items():
        stats[predicate].update(values)
    return stats, examples


def flatten_counter(counter: Counter[Any], limit: int = 8) -> str:
    return "; ".join(f"{key}:{value}" for key, value in counter.most_common(limit))


def predicate_capacity_rows(all_relation_types: list[dict[str, str]], queue_stats: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in all_relation_types:
        predicate = row["predicate_label"]
        stat = queue_stats.get(predicate, {})
        queue_rows = int(stat.get("queue_rows", 0))
        exact = int(stat.get("label_match_status_counts", Counter()).get("exact_match", 0))
        mixed_groups = int(stat.get("mixed_class_pair_groups_exact_vs_other", 0))
        if queue_rows == 0:
            verdict = "source_adapter_needed"
            reason = "not present in current H002 geometry-checkable queue"
        elif queue_rows < MIN_QUEUE_ROWS:
            verdict = "too_sparse_current_queue"
            reason = "queue rows below scan threshold"
        elif exact < MIN_EXACT_MATCH_ROWS:
            verdict = "exact_match_sparse_audit_only"
            reason = "few exact GT anchors under current queue"
        elif mixed_groups < MIN_MIXED_CLASS_GROUPS:
            verdict = "shortcut_risk_needs_target_plan"
            reason = "not enough exact-vs-other mixing inside class-pair groups"
        else:
            verdict = "capacity_ready_needs_target_plan"
            reason = "queue mass and class-pair mixing are sufficient for a target plan"
        if predicate == "close by":
            verdict = "selected_target_plan_lh_only"
            reason = "large queue and GT mass, but current queue is LH-only so target plan must avoid no-GT-as-negative"
        rows.append(
            {
                "predicate_label": predicate,
                "family": row["family"],
                "open3dsg_train_full_gt_count": row["open3dsg_train_full_gt_count"],
                "queue_rows": queue_rows,
                "hl_rows": int(stat.get("hl_rows", 0)),
                "lh_rows": int(stat.get("lh_rows", 0)),
                "label_match_status_counts": flatten_counter(stat.get("label_match_status_counts", Counter())),
                "geometry_status_counts": flatten_counter(stat.get("geometry_status_counts", Counter())),
                "rank_band_counts": flatten_counter(stat.get("rank_band_counts", Counter())),
                "unique_class_pairs": len(stat.get("class_pair_counts", Counter())),
                "mixed_class_pair_groups_exact_vs_other": mixed_groups,
                "balanced_rows_exact_vs_other": int(stat.get("balanced_rows_exact_vs_other", 0)),
                "directed_pair_count": int(stat.get("directed_pair_count", 0)),
                "verdict": verdict,
                "reason": reason,
            }
        )
    rows.sort(key=lambda item: (0 if item["predicate_label"] == "close by" else 1, -int(item["queue_rows"]), item["predicate_label"]))
    return rows


def family_capacity_rows(family_priority: list[dict[str, str]], predicate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in predicate_rows:
        by_family[row["family"]].append(row)
    rows: list[dict[str, Any]] = []
    for row in family_priority:
        family = row["family"]
        preds = by_family.get(family, [])
        queue_total = sum(int(pred["queue_rows"]) for pred in preds)
        exact_total = 0
        mixed_total = sum(int(pred["mixed_class_pair_groups_exact_vs_other"]) for pred in preds)
        for pred in preds:
            counts = {}
            for item in str(pred["label_match_status_counts"]).split("; "):
                if ":" in item:
                    key, value = item.rsplit(":", 1)
                    try:
                        counts[key] = int(value)
                    except ValueError:
                        pass
            exact_total += counts.get("exact_match", 0)
        if family == "proximity":
            verdict = "selected_first_active_family"
        elif family == "support_contact":
            verdict = "per_predicate_probe_after_proximity"
        elif queue_total > 0:
            verdict = "covered_by_current_queue"
        else:
            verdict = "requires_new_source_adapter_or_schema"
        rows.append(
            {
                "family": family,
                "predicates": row["predicates"],
                "gt_total": row["open3dsg_train_full_gt_total"],
                "queue_total": queue_total,
                "exact_match_total": exact_total,
                "mixed_class_pair_groups_exact_vs_other": mixed_total,
                "verdict": verdict,
                "next_action": row["next_action"],
            }
        )
    rows.sort(key=lambda item: (0 if item["family"] == "proximity" else 1, -int(item["queue_total"]), item["family"]))
    return rows


def route_rows(close_by: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "route": "proximity_close_by_target_plan",
            "verdict": "selected",
            "evidence": (
                f"queue_rows={close_by.get('queue_rows')}, exact_match={close_by.get('label_match_status_counts')}, "
                f"mixed_class_pair_groups={close_by.get('mixed_class_pair_groups_exact_vs_other')}"
            ),
            "requirement": "construct hard negatives without treating all no-GT close-by pairs as false",
        },
        {
            "route": "support_contact_individual_predicate_probe",
            "verdict": "defer_after_close_by_plan",
            "evidence": "standing on, lying on, supported by have different exact/family/no-GT patterns",
            "requirement": "per-predicate target plan, not grouped support/contact target reuse",
        },
        {
            "route": "all_relation_types_model_training",
            "verdict": "reject",
            "evidence": "many predicates are absent from current H002 queue and need new geometry schema/source adapters",
            "requirement": "capacity/shortcut scan first",
        },
    ]


def write_report(path: Path, summary: dict[str, Any], family_rows: list[dict[str, Any]], predicate_rows: list[dict[str, Any]]) -> None:
    close_by = next(row for row in predicate_rows if row["predicate_label"] == "close by")
    lines = [
        "# H002 Relation-Family Generalization Capacity Scan",
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
        "## Decision",
        "",
        "Proceed to a proximity / `close by` target plan first, while preserving the all-family eligibility table.",
        "",
        "`close by` is not automatically paper-ready. The scan shows that it is large but LH-only in the current H002 queue, so the next target plan must control dense-relation noise and must not treat every no-GT pair as a negative.",
        "",
        "## Close By Snapshot",
        "",
        "```text",
        f"queue_rows = {close_by['queue_rows']}",
        f"HL rows = {close_by['hl_rows']}",
        f"LH rows = {close_by['lh_rows']}",
        f"label_match_status = {close_by['label_match_status_counts']}",
        f"geometry_status = {close_by['geometry_status_counts']}",
        f"mixed class-pair groups exact-vs-other = {close_by['mixed_class_pair_groups_exact_vs_other']}",
        f"balanced rows exact-vs-other = {close_by['balanced_rows_exact_vs_other']}",
        "```",
        "",
        "## Family Table",
        "",
    ]
    for row in family_rows:
        lines.extend(
            [
                f"- `{row['family']}`: {row['verdict']}",
                f"  GT total: {row['gt_total']}; queue total: {row['queue_total']}; exact matches: {row['exact_match_total']}",
                f"  Mixed class-pair groups: {row['mixed_class_pair_groups_exact_vs_other']}",
                f"  Next: {row['next_action']}",
            ]
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only capacity scan.",
            "- No validation/test usage.",
            "- No row materialization.",
            "- No learned smoke or model training.",
            "- No paper evidence.",
            "- No H001 artifact modification.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    scope_path = args.scope_dir / "summary.json"
    if scope_path.exists():
        scope = read_json(scope_path)
    else:
        scope = {}
    validation_errors = validate_inputs(scope, args)
    all_relation_types = read_csv(args.scope_dir / "all_relation_types.csv") if (args.scope_dir / "all_relation_types.csv").exists() else []
    family_priority = read_csv(args.scope_dir / "family_priority_table.csv") if (args.scope_dir / "family_priority_table.csv").exists() else []
    queue_stats, examples = scan_queues(args.train_rga_dir) if args.train_rga_dir.exists() else ({}, {})
    predicate_rows = predicate_capacity_rows(all_relation_types, queue_stats)
    family_rows = family_capacity_rows(family_priority, predicate_rows)
    close_by = next((row for row in predicate_rows if row["predicate_label"] == "close by"), {})
    routes = route_rows(close_by) if close_by else []

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_errors"
        next_todo = EXPECTED_SCOPE_NEXT
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH
        next_todo = NEXT_TODO

    output_paths = {
        "example_rows": args.output_dir / "example_rows.json",
        "family_capacity": args.output_dir / "family_capacity.csv",
        "predicate_capacity": args.output_dir / "predicate_capacity.csv",
        "report": args.output_dir / "report.md",
        "route_decision": args.output_dir / "route_decision.csv",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_capacity_scan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "close_by_snapshot": close_by,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_scope_summary": rel_path(scope_path),
        "next_todo": next_todo,
        "output_paths": {name: rel_path(path) for name, path in output_paths.items()},
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(validation_errors),
    }
    write_json(output_paths["summary"], summary)
    write_json(output_paths["example_rows"], examples)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_csv(output_paths["predicate_capacity"], predicate_rows)
    write_csv(output_paths["family_capacity"], family_rows)
    write_csv(output_paths["route_decision"], routes)
    write_report(output_paths["report"], summary, family_rows, predicate_rows)
    print(
        json.dumps(
            {
                "status": status,
                "selected_path": selected_path,
                "validation_errors": len(validation_errors),
                "next_todo": next_todo,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 1 if status == STATUS_ERROR else 0


if __name__ == "__main__":
    raise SystemExit(main())
