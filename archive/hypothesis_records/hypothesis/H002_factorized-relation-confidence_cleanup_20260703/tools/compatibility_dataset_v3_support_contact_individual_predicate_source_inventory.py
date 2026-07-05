#!/usr/bin/env python3
"""Inventory individual support/contact predicate source capacity."""

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

DEFAULT_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_probe_plan"
DEFAULT_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_POSE_CAPACITY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_capacity_scan"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_source_inventory"

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_probe_plan_ready_for_source_inventory"
)
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_source_inventory"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_ready_for_candidate_materialization_plan"
)
STATUS_DIAGNOSTIC = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_diagnostic_only"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_individual_predicate_source_inventory_input_errors"
SELECTED_PATH_READY = "plan_candidate_materialization_for_standing_lying_individual_predicate_cells_supported_by_diagnostic"
SELECTED_PATH_DIAGNOSTIC = "freeze_individual_support_contact_source_inventory_as_diagnostic"
NEXT_READY = "compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_plan"
NEXT_DIAGNOSTIC = "compatibility_dataset_v3_support_contact_individual_predicate_diagnostic_freeze"

PREDICATES = ["standing on", "lying on", "supported by"]
PRIMARY_PREDICATES = ["standing on", "lying on"]
HARD_SURFACE_LABELS = {"floor", "wall", "ceiling", "room", "window", "door"}
SOURCE_FILES = {
    "aligned_ply": "labels.instances.align.annotated.v2.ply",
    "mesh_obj": "mesh.refined.v2.obj",
    "mesh_seg": "mesh.refined.0.010000.segs.v2.json",
    "semseg": "semseg.v2.json",
    "sequence_zip": "sequence.zip",
}

MIN_PRIMARY_BALANCED_CLASS_PAIR_ROWS = 300
MIN_PRIMARY_MIXED_CLASS_PAIR_GROUPS = 10
MIN_DIAGNOSTIC_BALANCED_ROWS = 100


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--rga-dir", type=Path, default=DEFAULT_RGA_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--pose-capacity-dir", type=Path, default=DEFAULT_POSE_CAPACITY_DIR)
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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def class_pair(row: dict[str, Any]) -> str:
    return f"{row.get('subject_label')}->{row.get('object_label')}"


def directed_pair(row: dict[str, Any]) -> str:
    return f"{row.get('scan_id')}::{row.get('subgraph_id')}::{row.get('subject_id')}->{row.get('object_id')}"


def hard_surface_pair(row: dict[str, Any]) -> bool:
    return norm(row.get("subject_label")) in HARD_SURFACE_LABELS or norm(row.get("object_label")) in HARD_SURFACE_LABELS


def matched_set(row: dict[str, Any]) -> set[str]:
    return {str(value) for value in row.get("matched_predicates") or []}


def support_role(row: dict[str, Any]) -> str:
    predicate = row["predicate_label"]
    matched = matched_set(row)
    status = row.get("label_match_status")
    if predicate == "standing on":
        if status == "exact_match" or "standing on" in matched:
            return "clear_accept"
        if "lying on" in matched:
            return "hard_reject_lying_like"
        if status == "no_gt_for_pair":
            return "audit_no_gt"
        return "other_overlap"
    if predicate == "lying on":
        if status == "exact_match" or "lying on" in matched:
            return "clear_accept"
        if "standing on" in matched:
            return "hard_reject_standing_like"
        if status == "no_gt_for_pair":
            return "audit_no_gt"
        return "other_overlap"
    if predicate == "supported by":
        if status == "exact_match" or "supported by" in matched:
            return "clear_accept"
        if status == "pair_has_other_predicate" and not (matched & set(PREDICATES)):
            return "hard_reject_no_support"
        if status == "no_gt_for_pair" or bool(matched & {"standing on", "lying on"}):
            return "overlap_or_abstain"
        return "other_overlap"
    return "unsupported"


def validate_inputs(plan_summary: dict[str, Any], plan_errors: list[dict[str, Any]], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})
    if plan_errors:
        errors.append({"error_type": "plan_validation_error_rows_present", "rows": len(plan_errors)})
    selected = plan_summary.get("selected_predicates", {})
    if selected.get("primary") != "standing on" or selected.get("secondary") != "lying on" or selected.get("diagnostic") != "supported by":
        errors.append({"error_type": "unexpected_selected_predicates", "actual": selected})
    boundary = plan_summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "paper_evidence_allowed", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = args.rga_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_rga_queue", "path": rel_path(path)})
    if not args.scan_root.exists():
        errors.append({"error_type": "missing_scan_root", "path": rel_path(args.scan_root)})
    pose_summary = args.pose_capacity_dir / "summary.json"
    if not pose_summary.exists():
        errors.append({"error_type": "missing_pose_capacity_summary", "path": rel_path(pose_summary)})
    return errors


def load_rows(rga_dir: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    line_counts: dict[str, int] = {}
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = rga_dir / name
        count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                count += 1
                row = json.loads(line)
                if row.get("predicate_label") in PREDICATES and row.get("predicate_family") == "support_contact":
                    row = dict(row)
                    row["_role"] = support_role(row)
                    row["_class_pair"] = class_pair(row)
                    row["_directed_pair"] = directed_pair(row)
                    row["_hard_surface_pair"] = hard_surface_pair(row)
                    rows.append(row)
        line_counts[rel_path(path)] = count
    return rows, line_counts


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def mixed_capacity(rows: list[dict[str, Any]], pos_role: str, neg_role: str, group_fields: list[str]) -> dict[str, Any]:
    groups: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
    for row in rows:
        key = tuple(row[field] if field.startswith("_") else row.get(field) for field in group_fields)
        groups[key][row["_role"]] += 1
    mixed = {key: counts for key, counts in groups.items() if counts[pos_role] and counts[neg_role]}
    balanced_rows = sum(min(counts[pos_role], counts[neg_role]) * 2 for counts in mixed.values())
    return {
        "mixed_groups": len(mixed),
        "balanced_rows": balanced_rows,
        "largest_group_rows": max((sum(counts.values()) for counts in mixed.values()), default=0),
    }


def predicate_inventory(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    role_pairs = {
        "standing on": ("clear_accept", "hard_reject_lying_like"),
        "lying on": ("clear_accept", "hard_reject_standing_like"),
        "supported by": ("clear_accept", "hard_reject_no_support"),
    }
    for predicate in PREDICATES:
        pred_rows = [row for row in rows if row["predicate_label"] == predicate]
        roles = Counter(row["_role"] for row in pred_rows)
        pos_role, neg_role = role_pairs[predicate]
        class_pair = mixed_capacity(pred_rows, pos_role, neg_role, ["_class_pair"])
        class_pair_rank = mixed_capacity(pred_rows, pos_role, neg_role, ["_class_pair", "rank_band"])
        role = "primary" if predicate == "standing on" else ("secondary" if predicate == "lying on" else "diagnostic")
        if predicate in PRIMARY_PREDICATES:
            ready = (
                class_pair["balanced_rows"] >= MIN_PRIMARY_BALANCED_CLASS_PAIR_ROWS
                and class_pair["mixed_groups"] >= MIN_PRIMARY_MIXED_CLASS_PAIR_GROUPS
            )
        else:
            ready = class_pair["balanced_rows"] >= MIN_DIAGNOSTIC_BALANCED_ROWS
        output.append(
            {
                "predicate_label": predicate,
                "plan_role": role,
                "rows": len(pred_rows),
                "queue_kind_counts": json.dumps(counter_dict(Counter(row.get("queue_kind") for row in pred_rows)), sort_keys=True),
                "label_match_status_counts": json.dumps(counter_dict(Counter(row.get("label_match_status") for row in pred_rows)), sort_keys=True),
                "geometry_status_counts": json.dumps(counter_dict(Counter(row.get("geometry_status") for row in pred_rows)), sort_keys=True),
                "rank_band_counts": json.dumps(counter_dict(Counter(row.get("rank_band") for row in pred_rows)), sort_keys=True),
                "role_counts": json.dumps(counter_dict(roles), sort_keys=True),
                "unique_scans": len({row.get("scan_id") for row in pred_rows}),
                "unique_class_pairs": len({row["_class_pair"] for row in pred_rows}),
                "hard_surface_rows": sum(1 for row in pred_rows if row["_hard_surface_pair"]),
                "hard_surface_share": round(sum(1 for row in pred_rows if row["_hard_surface_pair"]) / len(pred_rows), 6) if pred_rows else 0.0,
                "primary_pos_role": pos_role,
                "primary_neg_role": neg_role,
                "class_pair_mixed_groups": class_pair["mixed_groups"],
                "class_pair_balanced_rows": class_pair["balanced_rows"],
                "class_pair_rank_mixed_groups": class_pair_rank["mixed_groups"],
                "class_pair_rank_balanced_rows": class_pair_rank["balanced_rows"],
                "source_inventory_ready": ready,
                "source_inventory_verdict": "ready_for_candidate_plan" if ready and predicate != "supported by" else ("diagnostic_ready" if ready else "diagnostic_or_repair_needed"),
            }
        )
    return output


def role_capacity(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for predicate in PREDICATES:
        pred_rows = [row for row in rows if row["predicate_label"] == predicate]
        role_counts = Counter(row["_role"] for row in pred_rows)
        for role_name, count in role_counts.most_common():
            role_rows = [row for row in pred_rows if row["_role"] == role_name]
            output.append(
                {
                    "predicate_label": predicate,
                    "candidate_role": role_name,
                    "rows": count,
                    "unique_class_pairs": len({row["_class_pair"] for row in role_rows}),
                    "unique_scans": len({row.get("scan_id") for row in role_rows}),
                    "hard_surface_rows": sum(1 for row in role_rows if row["_hard_surface_pair"]),
                    "top_rank_band": Counter(row.get("rank_band") for row in role_rows).most_common(1)[0][0] if role_rows else "",
                    "top_label_match_status": Counter(row.get("label_match_status") for row in role_rows).most_common(1)[0][0] if role_rows else "",
                }
            )
    return output


def controlled_cell_capacity(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("standing on", "clear_accept", "hard_reject_lying_like"),
        ("lying on", "clear_accept", "hard_reject_standing_like"),
        ("supported by", "clear_accept", "hard_reject_no_support"),
    ]
    group_axes = {
        "class_pair": ["_class_pair"],
        "class_pair_x_rank_band": ["_class_pair", "rank_band"],
        "scan": ["scan_id"],
        "scan_x_class_pair": ["scan_id", "_class_pair"],
    }
    out: list[dict[str, Any]] = []
    for predicate, pos_role, neg_role in specs:
        pred_rows = [row for row in rows if row["predicate_label"] == predicate]
        for axis, fields in group_axes.items():
            cap = mixed_capacity(pred_rows, pos_role, neg_role, fields)
            out.append(
                {
                    "predicate_label": predicate,
                    "axis": axis,
                    "positive_role": pos_role,
                    "negative_role": neg_role,
                    **cap,
                }
            )
    return out


def same_geometry_anchor_capacity(rows: list[dict[str, Any]], pose_summary: dict[str, Any]) -> list[dict[str, Any]]:
    pair_predicates: dict[str, set[str]] = defaultdict(set)
    pair_rows: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        pair_predicates[row["_directed_pair"]].add(row["predicate_label"])
        pair_rows[row["_directed_pair"]].append(row)
    standing_lying_pairs = [key for key, predicates in pair_predicates.items() if {"standing on", "lying on"} <= predicates]
    all_three_pairs = [key for key, predicates in pair_predicates.items() if set(PREDICATES) <= predicates]
    pose_capacity = pose_summary.get("capacity_summary", {})
    return [
        {
            "anchor_type": "predicted_same_pair_standing_and_lying",
            "pairs": len(standing_lying_pairs),
            "rows": sum(len(pair_rows[key]) for key in standing_lying_pairs),
            "role": "raw same-G candidate capacity from Open3DSG queue",
        },
        {
            "anchor_type": "predicted_same_pair_all_three_support_contact",
            "pairs": len(all_three_pairs),
            "rows": sum(len(pair_rows[key]) for key in all_three_pairs),
            "role": "diagnostic overlap capacity including supported by",
        },
        {
            "anchor_type": "pose_conditioned_classified_anchors_previous_artifact",
            "pairs": pose_capacity.get("classified_anchors_for_selected_threshold", 0),
            "rows": pose_capacity.get("selected_total_rows_if_materialized", 0),
            "role": "previous verified same-G pose-conditioned C_e mechanism capacity",
        },
        {
            "anchor_type": "pose_conditioned_selected_anchor_groups_previous_artifact",
            "pairs": pose_capacity.get("selected_anchor_groups", 0),
            "rows": pose_capacity.get("selected_total_rows_if_materialized", 0),
            "role": "previous selected balanced lying/upright anchors",
        },
    ]


def source_availability(rows: list[dict[str, Any]], scan_root: Path) -> list[dict[str, Any]]:
    scans = sorted({str(row.get("scan_id")) for row in rows})
    output: list[dict[str, Any]] = []
    for scan_id in scans:
        root = scan_root / scan_id
        exists = {f"{key}_exists": (root / filename).exists() for key, filename in SOURCE_FILES.items()}
        output.append(
            {
                "scan_id": scan_id,
                "all_required_sources_exist": all(exists.values()),
                **exists,
            }
        )
    return output


def route_decision(predicate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_predicate = {row["predicate_label"]: row for row in predicate_rows}
    standing_ready = bool(by_predicate["standing on"]["source_inventory_ready"])
    lying_ready = bool(by_predicate["lying on"]["source_inventory_ready"])
    supported_ready = bool(by_predicate["supported by"]["source_inventory_ready"])
    return [
        {
            "route": "standing_on_individual_candidate_plan",
            "verdict": "select_primary" if standing_ready else "diagnostic_or_repair_needed",
            "evidence": f"class-pair balanced rows = {by_predicate['standing on']['class_pair_balanced_rows']}, mixed groups = {by_predicate['standing on']['class_pair_mixed_groups']}",
            "reason": "standing on has enough exact accept and lying-like hard reject capacity for a materialization plan" if standing_ready else "standing on lacks controlled role capacity",
        },
        {
            "route": "lying_on_individual_candidate_plan",
            "verdict": "select_secondary" if lying_ready else "diagnostic_or_repair_needed",
            "evidence": f"class-pair balanced rows = {by_predicate['lying on']['class_pair_balanced_rows']}, mixed groups = {by_predicate['lying on']['class_pair_mixed_groups']}",
            "reason": "lying on has enough exact accept and standing-like hard reject capacity for paired C_e probes" if lying_ready else "lying on lacks controlled role capacity",
        },
        {
            "route": "supported_by_as_primary_binary_target",
            "verdict": "reject_main_even_if_capacity_exists",
            "evidence": f"class-pair balanced rows = {by_predicate['supported by']['class_pair_balanced_rows']}, mixed groups = {by_predicate['supported by']['class_pair_mixed_groups']}",
            "reason": "supported by is superordinate and remains diagnostic unless visual/mesh source inventory later proves clean support/non-support labels",
        },
        {
            "route": "candidate_materialization_plan",
            "verdict": "selected_next" if standing_ready and lying_ready else "blocked",
            "evidence": f"standing_ready = {standing_ready}; lying_ready = {lying_ready}; supported_diagnostic_ready = {supported_ready}",
            "reason": "write a plan before materializing rows; no learned smoke is allowed yet",
        },
    ]


def shortcut_capacity_audit(predicate_rows: list[dict[str, Any]], source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_predicate = {row["predicate_label"]: row for row in predicate_rows}
    return [
        {
            "risk": "class_pair_shortcut",
            "severity": "medium",
            "value": {
                predicate: by_predicate[predicate]["class_pair_mixed_groups"] for predicate in PREDICATES
            },
            "mitigation": "candidate plan must cap class-pair and preserve mixed accept/reject groups",
        },
        {
            "risk": "rank_source_shortcut",
            "severity": "medium",
            "value": counter_dict(Counter(row.get("rank_band") for row in source_rows)),
            "mitigation": "rank/source fields stay hidden and rank bands must be audited after materialization",
        },
        {
            "risk": "hard_surface_shortcut",
            "severity": "high",
            "value": {
                predicate: by_predicate[predicate]["hard_surface_share"] for predicate in PREDICATES
            },
            "mitigation": "standing on and supported by require hard-surface caps or stratified diagnostic tables",
        },
        {
            "risk": "no_gt_as_negative",
            "severity": "high",
            "value": {
                predicate: json.loads(by_predicate[predicate]["role_counts"]).get("audit_no_gt", 0)
                for predicate in PREDICATES
            },
            "mitigation": "no-GT rows remain audit/abstain candidates, never automatic reject",
        },
        {
            "risk": "supported_by_superordinate_overlap",
            "severity": "high",
            "value": by_predicate["supported by"]["role_counts"],
            "mitigation": "supported by remains diagnostic and cannot be used as standing-on negative",
        },
    ]


def preview_examples(rows: list[dict[str, Any]], limit_per_predicate_role: int = 2) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: Counter[tuple[str, str]] = Counter()
    for row in sorted(rows, key=lambda item: str(item.get("prediction_id"))):
        key = (row["predicate_label"], row["_role"])
        if seen[key] >= limit_per_predicate_role:
            continue
        seen[key] += 1
        output.append(
            {
                "predicate_label": row["predicate_label"],
                "candidate_role": row["_role"],
                "scan_id": row.get("scan_id"),
                "subject_label": row.get("subject_label"),
                "object_label": row.get("object_label"),
                "label_match_status": row.get("label_match_status"),
                "matched_predicates": row.get("matched_predicates"),
                "rank_band": row.get("rank_band"),
                "queue_kind": row.get("queue_kind"),
                "hard_surface_pair": row.get("_hard_surface_pair"),
            }
        )
    return output


def write_report(path: Path, summary: dict[str, Any], predicate_rows: list[dict[str, Any]], routes: list[dict[str, Any]]) -> None:
    lines = [
        "# H002 Support/Contact Individual Predicate Source Inventory",
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
        "## Answer To Current Scope",
        "",
        "Yes. This stage treats support/contact relation types separately: `standing on`, `lying on`, and `supported by` are inventoried with different roles.",
        "",
        "## Predicate Inventory",
        "",
        "| Predicate | Role | Rows | Class-Pair Balanced Rows | Mixed Groups | Verdict |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in predicate_rows:
        lines.append(
            "| "
            f"`{row['predicate_label']}` | {row['plan_role']} | {row['rows']} | "
            f"{row['class_pair_balanced_rows']} | {row['class_pair_mixed_groups']} | "
            f"{row['source_inventory_verdict']} |"
        )
    lines.extend(
        [
            "",
            "## Route Decision",
            "",
            "| Route | Verdict | Evidence |",
            "| --- | --- | --- |",
        ]
    )
    for row in routes:
        lines.append(f"| `{row['route']}` | `{row['verdict']}` | {row['evidence']} |")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only source inventory.",
            "- No validation/test usage.",
            "- No row materialization or label fill.",
            "- No learned smoke or model training.",
            "- `supported by` remains diagnostic/superordinate.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary_path = args.plan_dir / "summary.json"
    plan_summary = read_json(plan_summary_path) if plan_summary_path.exists() else {}
    plan_errors = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    validation_errors = validate_inputs(plan_summary, plan_errors, args)

    pose_summary = read_json(args.pose_capacity_dir / "summary.json") if (args.pose_capacity_dir / "summary.json").exists() else {}
    source_rows, line_counts = load_rows(args.rga_dir) if not validation_errors else ([], {})
    predicate_rows = predicate_inventory(source_rows) if source_rows else []
    role_rows = role_capacity(source_rows) if source_rows else []
    cell_rows = controlled_cell_capacity(source_rows) if source_rows else []
    anchor_rows = same_geometry_anchor_capacity(source_rows, pose_summary) if source_rows else []
    availability_rows = source_availability(source_rows, args.scan_root) if source_rows else []
    routes = route_decision(predicate_rows) if predicate_rows else []
    shortcut_rows = shortcut_capacity_audit(predicate_rows, source_rows) if predicate_rows else []
    examples = preview_examples(source_rows)

    ready = bool(predicate_rows) and all(
        row["source_inventory_ready"] for row in predicate_rows if row["predicate_label"] in PRIMARY_PREDICATES
    )
    if validation_errors:
        status = STATUS_ERROR
        selected_path = "blocked_input_errors"
        next_todo = EXPECTED_PLAN_NEXT
    elif ready:
        status = STATUS_READY
        selected_path = SELECTED_PATH_READY
        next_todo = NEXT_READY
    else:
        status = STATUS_DIAGNOSTIC
        selected_path = SELECTED_PATH_DIAGNOSTIC
        next_todo = NEXT_DIAGNOSTIC

    all_sources_ready = all(row["all_required_sources_exist"] for row in availability_rows) if availability_rows else False
    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_source_inventory",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "plan_summary": rel_path(plan_summary_path),
            "pose_capacity_summary": rel_path(args.pose_capacity_dir / "summary.json"),
            "train_hl_queue": rel_path(args.rga_dir / "train_hl_queue.jsonl"),
            "train_lh_queue": rel_path(args.rga_dir / "train_lh_queue.jsonl"),
        },
        "line_counts": line_counts,
        "next_todo": next_todo,
        "output_paths": {
            "controlled_cell_capacity": rel_path(args.output_dir / "controlled_cell_capacity.csv"),
            "predicate_source_inventory": rel_path(args.output_dir / "predicate_source_inventory.csv"),
            "preview_examples": rel_path(args.output_dir / "preview_examples.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "role_capacity": rel_path(args.output_dir / "role_capacity.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "same_geometry_anchor_capacity": rel_path(args.output_dir / "same_geometry_anchor_capacity.csv"),
            "shortcut_capacity_audit": rel_path(args.output_dir / "shortcut_capacity_audit.csv"),
            "source_availability": rel_path(args.output_dir / "source_availability.csv"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "source_summary": {
            "all_required_sources_exist": all_sources_ready,
            "predicate_rows": {row["predicate_label"]: row["rows"] for row in predicate_rows},
            "primary_ready": ready,
            "supported_by_role": "diagnostic_superordinate",
            "unique_scans": len(availability_rows),
            "total_support_contact_rows": len(source_rows),
        },
        "status": status,
        "validation_errors": len(validation_errors),
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "preview_examples.json", examples)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "predicate_source_inventory.csv", predicate_rows)
    write_csv(args.output_dir / "role_capacity.csv", role_rows)
    write_csv(args.output_dir / "controlled_cell_capacity.csv", cell_rows)
    write_csv(args.output_dir / "same_geometry_anchor_capacity.csv", anchor_rows)
    write_csv(args.output_dir / "source_availability.csv", availability_rows)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_csv(args.output_dir / "shortcut_capacity_audit.csv", shortcut_rows)
    write_report(args.output_dir / "report.md", summary, predicate_rows, routes)

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
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
