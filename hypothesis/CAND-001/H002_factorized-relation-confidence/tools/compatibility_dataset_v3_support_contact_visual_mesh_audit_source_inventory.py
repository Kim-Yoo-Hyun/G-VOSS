#!/usr/bin/env python3
"""Inventory train-only source rows for the support/contact visual/mesh audit target."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan"
)
DEFAULT_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_target_plan_ready_for_source_inventory"
)
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory_ready_for_packet_materialization"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory_errors"
SELECTED_PATH = "source_inventory_ready_packet_materialization_required"
NEXT_TODO = "compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization"

SELECTED_PREDICATES = {"lying on", "standing on", "supported by"}
HARD_SURFACE_LABELS = {"floor", "wall", "ceiling", "room", "window", "door"}

SCAN_CAP = 24
CLASS_PAIR_CAP = 48
DIRECTED_PAIR_CAP = 2
HARD_SURFACE_CAP = 288
MIN_HL_ROWS = 60
TARGET_ROWS = 480

SOURCE_FILES = {
    "aligned_ply": "labels.instances.align.annotated.v2.ply",
    "mesh_obj": "mesh.refined.v2.obj",
    "mesh_seg": "mesh.refined.0.010000.segs.v2.json",
    "semseg": "semseg.v2.json",
    "sequence_zip": "sequence.zip",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--rga-dir", type=Path, default=DEFAULT_RGA_DIR)
    parser.add_argument("--three-rscan-root", type=Path, default=DEFAULT_3RSCAN_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def stable_int(value: str) -> int:
    return int(hashlib.sha1(value.encode("utf-8")).hexdigest()[:12], 16)


def stable_review_id(row: dict[str, Any], index: int) -> str:
    digest = hashlib.sha1(str(row["prediction_id"]).encode("utf-8")).hexdigest()[:10]
    return f"scvm_audit_{index:04d}_{digest}"


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def matched_predicates(row: dict[str, Any]) -> set[str]:
    return {str(value) for value in row.get("matched_predicates") or []}


def directed_pair_key(row: dict[str, Any]) -> str:
    return f"{row.get('scan_id')}::{row.get('subgraph_id')}::{row.get('subject_id')}->{row.get('object_id')}"


def class_pair_key(row: dict[str, Any]) -> str:
    return f"{row.get('subject_label')}->{row.get('object_label')}"


def hard_surface_pair(row: dict[str, Any]) -> bool:
    return norm(row.get("subject_label")) in HARD_SURFACE_LABELS or norm(row.get("object_label")) in HARD_SURFACE_LABELS


def support_contact_row(row: dict[str, Any]) -> bool:
    return row.get("predicate_family") == "support_contact" and row.get("predicate_label") in SELECTED_PREDICATES


def enrich_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out["_directed_pair_key"] = directed_pair_key(row)
    out["_class_pair_key"] = class_pair_key(row)
    out["_hard_surface_pair"] = hard_surface_pair(row)
    out["_matched_predicates_set"] = matched_predicates(row)
    return out


def load_support_rows(rga_dir: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    line_counts: dict[str, int] = {}
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = rga_dir / name
        line_count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line_count += 1
                row = json.loads(line)
                if support_contact_row(row):
                    rows.append(enrich_row(row))
        line_counts[rel_path(path)] = line_count
    return rows, line_counts


def validate_inputs(plan_summary: dict[str, Any], plan_errors: list[dict[str, Any]], sampling_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append(
            {
                "input": "plan_summary",
                "error_type": "unexpected_status",
                "actual": plan_summary.get("status"),
                "expected": EXPECTED_PLAN_STATUS,
            }
        )
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append(
            {
                "input": "plan_summary",
                "error_type": "unexpected_next_todo",
                "actual": plan_summary.get("next_todo"),
                "expected": EXPECTED_PLAN_NEXT,
            }
        )
    if plan_summary.get("validation_errors") != 0:
        errors.append(
            {
                "input": "plan_summary",
                "error_type": "validation_errors_present",
                "actual": plan_summary.get("validation_errors"),
            }
        )
    if plan_errors:
        errors.append({"input": "plan_validation_errors", "error_type": "rows_present", "rows": len(plan_errors)})
    boundary = plan_summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"input": "plan_summary", "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    quota_sum = sum(int(row["target_rows"]) for row in sampling_rows)
    if quota_sum != int(plan_summary.get("target_total_rows", TARGET_ROWS)):
        errors.append(
            {
                "input": "sampling_plan",
                "error_type": "quota_sum_mismatch",
                "quota_sum": quota_sum,
                "target_total_rows": plan_summary.get("target_total_rows"),
            }
        )
    return errors


def build_pair_predicates(rows: list[dict[str, Any]]) -> dict[str, set[str]]:
    pair_predicates: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        pair_predicates[row["_directed_pair_key"]].add(row["predicate_label"])
    return pair_predicates


def stratum_specs(pair_predicates: dict[str, set[str]]) -> dict[str, tuple[Callable[[dict[str, Any]], bool], str]]:
    return {
        "lying_on_clear_accept": (
            lambda r: r["predicate_label"] == "lying on"
            and ("lying on" in r["_matched_predicates_set"] or r.get("label_match_status") == "exact_match"),
            "normal",
        ),
        "lying_on_hard_reject_standing_like": (
            lambda r: r["predicate_label"] == "lying on" and "standing on" in r["_matched_predicates_set"],
            "prefer_hl",
        ),
        "lying_on_abstain_or_ambiguous": (
            lambda r: r["predicate_label"] == "lying on" and r.get("label_match_status") == "no_gt_for_pair",
            "prefer_hl",
        ),
        "standing_on_clear_accept": (
            lambda r: r["predicate_label"] == "standing on"
            and ("standing on" in r["_matched_predicates_set"] or r.get("label_match_status") == "exact_match"),
            "normal",
        ),
        "standing_on_hard_reject_lying_like": (
            lambda r: r["predicate_label"] == "standing on" and "lying on" in r["_matched_predicates_set"],
            "normal",
        ),
        "standing_on_abstain_or_ambiguous": (
            lambda r: r["predicate_label"] == "standing on" and r.get("label_match_status") == "no_gt_for_pair",
            "prefer_hl",
        ),
        "supported_by_clear_accept": (
            lambda r: r["predicate_label"] == "supported by"
            and ("supported by" in r["_matched_predicates_set"] or r.get("label_match_status") == "exact_match"),
            "normal",
        ),
        "supported_by_hard_reject_no_support": (
            lambda r: r["predicate_label"] == "supported by"
            and r.get("label_match_status") == "pair_has_other_predicate"
            and not (r["_matched_predicates_set"] & SELECTED_PREDICATES),
            "normal",
        ),
        "supported_by_abstain_or_ontology_overlap": (
            lambda r: r["predicate_label"] == "supported by"
            and (
                r.get("label_match_status") == "no_gt_for_pair"
                or bool(r["_matched_predicates_set"] & {"standing on", "lying on"})
            ),
            "normal",
        ),
        "cross_predicate_control": (
            lambda r: len(pair_predicates[r["_directed_pair_key"]] & SELECTED_PREDICATES) >= 2,
            "normal",
        ),
        "coverage_stress_control": (
            lambda r: r.get("label_match_status") == "no_gt_for_pair",
            "prefer_hl",
        ),
        "hard_surface_cap_control": (
            lambda r: bool(r["_hard_surface_pair"]),
            "prefer_hard",
        ),
    }


def sort_key(row: dict[str, Any], mode: str, scan_counts: Counter[str], class_counts: Counter[str]) -> tuple[Any, ...]:
    queue_priority = 0 if mode == "prefer_hl" and row.get("queue_kind") == "HL" else 1
    if mode == "prefer_hard":
        hard_priority = 0 if row["_hard_surface_pair"] else 1
    else:
        hard_priority = 0 if not row["_hard_surface_pair"] else 1
    return (
        queue_priority,
        hard_priority,
        class_counts[row["_class_pair_key"]],
        scan_counts[row.get("scan_id")],
        stable_int(str(row.get("prediction_id"))),
    )


def select_candidates(rows: list[dict[str, Any]], sampling_rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    pair_predicates = build_pair_predicates(rows)
    specs = stratum_specs(pair_predicates)
    selected: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    used_prediction_ids: set[str] = set()
    scan_counts: Counter[str] = Counter()
    class_counts: Counter[str] = Counter()
    directed_pair_counts: Counter[str] = Counter()
    hard_count = 0

    for quota in sampling_rows:
        stratum = quota["stratum"]
        target_rows = int(quota["target_rows"])
        predicate = quota["predicate"]
        if stratum not in specs:
            errors.append({"error_type": "unknown_sampling_stratum", "stratum": stratum})
            continue
        predicate_filter, mode = specs[stratum]
        candidates = [row for row in rows if row["prediction_id"] not in used_prediction_ids and predicate_filter(row)]
        candidates.sort(key=lambda row: sort_key(row, mode, scan_counts, class_counts))
        added = 0
        for row in candidates:
            if added >= target_rows:
                break
            if scan_counts[row["scan_id"]] >= SCAN_CAP:
                continue
            if class_counts[row["_class_pair_key"]] >= CLASS_PAIR_CAP:
                continue
            if directed_pair_counts[row["_directed_pair_key"]] >= DIRECTED_PAIR_CAP:
                continue
            if row["_hard_surface_pair"] and hard_count >= HARD_SURFACE_CAP:
                continue
            selected_row = dict(row)
            selected_row["sampling_stratum"] = stratum
            selected_row["sampling_target_role"] = quota.get("target_role")
            selected_row["sampling_predicate_group"] = predicate
            selected.append(selected_row)
            used_prediction_ids.add(row["prediction_id"])
            scan_counts[row["scan_id"]] += 1
            class_counts[row["_class_pair_key"]] += 1
            directed_pair_counts[row["_directed_pair_key"]] += 1
            hard_count += int(row["_hard_surface_pair"])
            added += 1
        if added != target_rows:
            errors.append(
                {
                    "error_type": "sampling_quota_deficit",
                    "stratum": stratum,
                    "target_rows": target_rows,
                    "selected_rows": added,
                    "candidate_pool": len(candidates),
                }
            )
    return selected, errors


def scan_source_paths(scan_root: Path, scan_id: str) -> dict[str, Path]:
    root = scan_root / scan_id
    return {key: root / filename for key, filename in SOURCE_FILES.items()}


def visible_row(row: dict[str, Any], review_id: str) -> dict[str, Any]:
    packet_root = f"PACKET_PENDING/{review_id}"
    return {
        "review_id": review_id,
        "scan_id_visible": row["scan_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "object_label": row["object_label"],
        "point_crop_path": f"{packet_root}/point_pair_crop.png",
        "mesh_render_path": f"{packet_root}/mesh_contact_render.png",
        "multiview_contact_sheet_path": f"{packet_root}/multiview_contact_sheet.jpg",
        "mesh_contact_summary_visible": "pending_packet_materialization_from_mesh_and_point_sources",
        "pose_summary_visible": "pending_packet_materialization_from_instance_pose_sources",
        "coverage_summary_visible": "raw_sources_ready_packet_not_rendered",
        "review_relation_reliability": "",
        "review_geometry_support": "",
        "review_observability": "",
        "review_counter_relation": "",
        "review_uncertainty_reason": "",
        "review_notes": "",
    }


def hidden_row(row: dict[str, Any], review_id: str) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "object_label": row.get("object_label"),
        "source_id": row.get("source_id"),
        "source_score": row.get("semantic_score_norm"),
        "source_score_raw": row.get("semantic_score_raw"),
        "source_rank": row.get("semantic_rank"),
        "rank_band": row.get("rank_band"),
        "queue_kind": row.get("queue_kind"),
        "geometry_status": row.get("geometry_status"),
        "p_geom_valid": row.get("p_geom_valid"),
        "label_match_status": row.get("label_match_status"),
        "matched_predicates": row.get("matched_predicates"),
        "reason_codes": row.get("reason_codes"),
        "machine_hint": row.get("machine_hint"),
        "h001_verification_status": row.get("h001_verification_status"),
        "construction_bucket": row.get("sampling_stratum"),
        "hidden_stratum": f"{row.get('sampling_stratum')}::{row.get('predicate_label')}::{row.get('_class_pair_key')}",
        "directed_pair_key": row.get("_directed_pair_key"),
        "subject_object_class_pair": row.get("_class_pair_key"),
        "hard_surface_pair": row.get("_hard_surface_pair"),
    }


def packet_source_row(row: dict[str, Any], review_id: str, scan_root: Path) -> dict[str, Any]:
    paths = scan_source_paths(scan_root, str(row["scan_id"]))
    source_exists = {f"{key}_exists": path.exists() for key, path in paths.items()}
    return {
        "review_id": review_id,
        "packet_status": "source_ready_packet_not_rendered",
        "scan_id_hidden": row.get("scan_id"),
        "subject_id_hidden": row.get("subject_id"),
        "object_id_hidden": row.get("object_id"),
        **{f"{key}_source_hidden": rel_path(path) for key, path in paths.items()},
        **source_exists,
        "all_required_sources_exist": all(source_exists.values()),
    }


def selected_inventory_row(row: dict[str, Any], review_id: str, packet_source: dict[str, Any]) -> dict[str, Any]:
    return {
        "review_id": review_id,
        "predicate_label": row.get("predicate_label"),
        "subject_label": row.get("subject_label"),
        "object_label": row.get("object_label"),
        "sampling_stratum": row.get("sampling_stratum"),
        "sampling_target_role": row.get("sampling_target_role"),
        "sampling_predicate_group": row.get("sampling_predicate_group"),
        "source_ready": packet_source["all_required_sources_exist"],
        "packet_status": packet_source["packet_status"],
        "hidden_queue_kind": row.get("queue_kind"),
        "hidden_label_match_status": row.get("label_match_status"),
        "hidden_hard_surface_pair": row.get("_hard_surface_pair"),
        "hidden_rank_band": row.get("rank_band"),
    }


def counter_dict(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))}


def build_balance_rows(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters = {
        "predicate_label": Counter(row["predicate_label"] for row in selected),
        "sampling_stratum": Counter(row["sampling_stratum"] for row in selected),
        "queue_kind_hidden": Counter(row.get("queue_kind") for row in selected),
        "label_match_status_hidden": Counter(row.get("label_match_status") for row in selected),
        "hard_surface_pair_hidden": Counter(str(row.get("_hard_surface_pair")) for row in selected),
        "rank_band_hidden": Counter(row.get("rank_band") for row in selected),
    }
    rows: list[dict[str, Any]] = []
    for axis, counter in counters.items():
        total = sum(counter.values()) or 1
        for value, count in counter.most_common():
            rows.append({"axis": axis, "value": value, "count": count, "share": count / total})
    return rows


def build_cap_rows(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scan_counts = Counter(row["scan_id"] for row in selected)
    class_counts = Counter(row["_class_pair_key"] for row in selected)
    directed_counts = Counter(row["_directed_pair_key"] for row in selected)
    hard_count = sum(1 for row in selected if row["_hard_surface_pair"])
    total = len(selected) or 1
    return [
        {
            "gate": "selected_rows",
            "value": len(selected),
            "threshold": TARGET_ROWS,
            "pass": len(selected) == TARGET_ROWS,
            "detail": "exact selected candidate count",
        },
        {
            "gate": "scan_cap",
            "value": max(scan_counts.values()) if scan_counts else 0,
            "threshold": SCAN_CAP,
            "pass": (max(scan_counts.values()) if scan_counts else 0) <= SCAN_CAP,
            "detail": scan_counts.most_common(5),
        },
        {
            "gate": "subject_object_class_pair_cap",
            "value": max(class_counts.values()) if class_counts else 0,
            "threshold": CLASS_PAIR_CAP,
            "pass": (max(class_counts.values()) if class_counts else 0) <= CLASS_PAIR_CAP,
            "detail": class_counts.most_common(5),
        },
        {
            "gate": "directed_pair_cap",
            "value": max(directed_counts.values()) if directed_counts else 0,
            "threshold": DIRECTED_PAIR_CAP,
            "pass": (max(directed_counts.values()) if directed_counts else 0) <= DIRECTED_PAIR_CAP,
            "detail": directed_counts.most_common(5),
        },
        {
            "gate": "hard_surface_cap",
            "value": hard_count,
            "threshold": HARD_SURFACE_CAP,
            "pass": hard_count <= HARD_SURFACE_CAP,
            "detail": {"count": hard_count, "share": hard_count / total},
        },
        {
            "gate": "hidden_HL_minimum",
            "value": sum(1 for row in selected if row.get("queue_kind") == "HL"),
            "threshold": MIN_HL_ROWS,
            "pass": sum(1 for row in selected if row.get("queue_kind") == "HL") >= MIN_HL_ROWS,
            "detail": "hidden mismatch-direction coverage, not visible to reviewers",
        },
    ]


def visible_leakage_errors(visible_rows: list[dict[str, Any]], hidden_fields: list[str]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    hidden_tokens = {"source_score", "source_rank", "rank_band", "source_id", "queue_kind", "geometry_status", "p_geom_valid", "label_match_status", "construction_bucket", "hidden_stratum"}
    hidden_tokens.update(hidden_fields)
    for idx, row in enumerate(visible_rows, start=1):
        for field, value in row.items():
            if field in hidden_tokens:
                errors.append({"row": idx, "field": field, "error_type": "hidden_field_visible"})
            text = str(value)
            for token in hidden_tokens:
                if token and token in text:
                    errors.append({"row": idx, "field": field, "error_type": "hidden_token_in_visible_value", "token": token})
    return errors


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Source Inventory",
            "",
            "## Result",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"validation_errors = {summary['validation_errors']}",
            f"next_todo = {summary['next_todo']}",
            "```",
            "",
            "## Selected Candidate Source",
            "",
            "```json",
            json.dumps(summary["selected_source_summary"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Boundary",
            "",
            "This step inventories train-only source rows and writes visible/hidden manifests. It does not render packets, fill labels, train a model, run a learned smoke, or use validation/test rows.",
            "",
            "The next step must materialize packet images/sheets before any label fill. The current visible sheet uses `PACKET_PENDING/...` paths by design.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    plan_errors = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    sampling_rows = read_csv(args.plan_dir / "sampling_plan.csv")
    visible_schema = read_csv(args.plan_dir / "visible_packet_schema.csv")
    hidden_policy = read_csv(args.plan_dir / "hidden_field_policy.csv")
    visible_fields = [row["field"] for row in visible_schema]
    hidden_fields = [row["field"] for row in hidden_policy]

    validation_errors = validate_inputs(plan_summary, plan_errors, sampling_rows)
    source_rows, line_counts = load_support_rows(args.rga_dir)
    selected_rows, selection_errors = select_candidates(source_rows, sampling_rows)
    validation_errors.extend(selection_errors)

    visible_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    packet_sources: list[dict[str, Any]] = []
    selected_inventory: list[dict[str, Any]] = []
    source_missing_errors: list[dict[str, Any]] = []

    for idx, row in enumerate(selected_rows, start=1):
        review_id = stable_review_id(row, idx)
        packet_source = packet_source_row(row, review_id, args.three_rscan_root)
        if not packet_source["all_required_sources_exist"]:
            source_missing_errors.append(
                {
                    "review_id": review_id,
                    "error_type": "required_source_missing",
                    "missing_sources": [key for key, value in packet_source.items() if key.endswith("_exists") and not value],
                }
            )
        visible_rows.append(visible_row(row, review_id))
        hidden_rows.append(hidden_row(row, review_id))
        packet_sources.append(packet_source)
        selected_inventory.append(selected_inventory_row(row, review_id, packet_source))

    validation_errors.extend(source_missing_errors)
    validation_errors.extend(visible_leakage_errors(visible_rows, hidden_fields))

    cap_rows = build_cap_rows(selected_rows)
    for cap_row in cap_rows:
        if not cap_row["pass"]:
            validation_errors.append(
                {
                    "error_type": "cap_gate_failed",
                    "gate": cap_row["gate"],
                    "value": cap_row["value"],
                    "threshold": cap_row["threshold"],
                }
            )

    predicate_counts = Counter(row["predicate_label"] for row in selected_rows)
    stratum_counts = Counter(row["sampling_stratum"] for row in selected_rows)
    queue_counts = Counter(row.get("queue_kind") for row in selected_rows)
    label_counts = Counter(row.get("label_match_status") for row in selected_rows)
    hard_count = sum(1 for row in selected_rows if row["_hard_surface_pair"])
    status = STATUS_READY if not validation_errors else STATUS_ERROR

    output_paths = {
        "balance_report": output_dir / "source_balance_report.csv",
        "cap_diagnostics": output_dir / "cap_diagnostics.csv",
        "hidden_manifest": output_dir / "hidden_manifest.jsonl",
        "label_sheet_template": output_dir / "label_sheet_template.csv",
        "packet_source_manifest": output_dir / "packet_source_manifest.jsonl",
        "report": output_dir / "report.md",
        "selected_candidate_inventory": output_dir / "selected_candidate_inventory.jsonl",
        "source_pool_summary": output_dir / "source_pool_summary.json",
        "summary": output_dir / "summary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    selected_source_summary = {
        "selected_rows": len(selected_rows),
        "target_rows": TARGET_ROWS,
        "predicate_counts": counter_dict(predicate_counts),
        "stratum_counts": counter_dict(stratum_counts),
        "queue_kind_counts_hidden": counter_dict(queue_counts),
        "label_match_status_counts_hidden": counter_dict(label_counts),
        "hard_surface_rows": hard_count,
        "hard_surface_share": hard_count / (len(selected_rows) or 1),
        "all_required_sources_exist": all(row["all_required_sources_exist"] for row in packet_sources),
        "visible_sheet_rows": len(visible_rows),
        "hidden_manifest_rows": len(hidden_rows),
    }

    source_pool_summary = {
        "support_rows_scanned": len(source_rows),
        "rga_line_counts": line_counts,
        "predicate_counts": counter_dict(Counter(row["predicate_label"] for row in source_rows)),
        "queue_kind_counts_hidden": counter_dict(Counter(row.get("queue_kind") for row in source_rows)),
        "label_match_status_counts_hidden": counter_dict(Counter(row.get("label_match_status") for row in source_rows)),
        "distinct_scans": len({row["scan_id"] for row in source_rows}),
        "distinct_directed_pairs": len({row["_directed_pair_key"] for row in source_rows}),
        "distinct_class_pairs": len({row["_class_pair_key"] for row in source_rows}),
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO if not validation_errors else "repair_support_contact_visual_mesh_audit_source_inventory",
        "validation_errors": len(validation_errors),
        "plan_status": plan_summary.get("status"),
        "selected_source_summary": selected_source_summary,
        "cap_summary": {row["gate"]: {"value": row["value"], "threshold": row["threshold"], "pass": row["pass"]} for row in cap_rows},
        "boundary": {
            "split": "train full only",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_candidate_rows": True,
            "materializes_packet_assets": False,
            "fills_labels": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
    }

    write_csv(output_paths["label_sheet_template"], visible_rows, visible_fields)
    write_jsonl(output_paths["hidden_manifest"], hidden_rows)
    write_jsonl(output_paths["packet_source_manifest"], packet_sources)
    write_jsonl(output_paths["selected_candidate_inventory"], selected_inventory)
    write_csv(output_paths["balance_report"], build_balance_rows(selected_rows))
    write_csv(output_paths["cap_diagnostics"], cap_rows)
    write_json(output_paths["source_pool_summary"], source_pool_summary)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
