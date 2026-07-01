#!/usr/bin/env python3
"""Select class-pair controlled repair after support/contact label ingestion."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_INGESTION_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingestion"
)
DEFAULT_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion"
)

EXPECTED_INGESTION_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_label_ingested_shortcut_risk_blocks_smoke"
)
EXPECTED_INGESTION_NEXT = (
    "compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_class_pair_repair_ready_for_packet_materialization"
)
STATUS_PARTIAL = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_class_pair_repair_partial_capacity"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_path_decision_after_label_ingestion_errors"
)
SELECTED_PATH = "class_pair_controlled_repair_first"
NEXT_TODO = (
    "compatibility_dataset_v3_support_contact_visual_mesh_audit_class_pair_repair_packet_materialization"
)

PREDICATES = ["lying on", "standing on", "supported by"]
PREDICATE_SET = set(PREDICATES)
HARD_SURFACE_LABELS = {"floor", "wall", "ceiling", "room", "window", "door"}
SOURCE_FILES = {
    "aligned_ply": "labels.instances.align.annotated.v2.ply",
    "mesh_obj": "mesh.refined.v2.obj",
    "mesh_seg": "mesh.refined.0.010000.segs.v2.json",
    "semseg": "semseg.v2.json",
    "sequence_zip": "sequence.zip",
}

TARGET_TOTAL_ROWS = 480
TARGET_PER_PREDICATE = 160
TARGET_PER_PREDICATE_KIND = 80
GROUP_KIND_CAP = 20
SCAN_CAP = 12
DIRECTED_PAIR_CAP = 1
HARD_SURFACE_CAP = 320


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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
    rows: list[dict[str, Any]] = []
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


def stable_int(value: Any) -> int:
    return int(hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:12], 16)


def stable_review_id(row: dict[str, Any], index: int) -> str:
    digest = hashlib.sha1(str(row["prediction_id"]).encode("utf-8")).hexdigest()[:10]
    return f"scvm_cpair_{index:04d}_{digest}"


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def directed_pair_key(row: dict[str, Any]) -> str:
    return f"{row.get('scan_id')}::{row.get('subgraph_id')}::{row.get('subject_id')}->{row.get('object_id')}"


def class_pair_key(row: dict[str, Any]) -> str:
    return f"{row.get('subject_label')}->{row.get('object_label')}"


def predicate_class_pair_key(row: dict[str, Any]) -> str:
    return f"{row.get('predicate_label')}::{class_pair_key(row)}"


def hard_surface_pair(row: dict[str, Any]) -> bool:
    return norm(row.get("subject_label")) in HARD_SURFACE_LABELS or norm(row.get("object_label")) in HARD_SURFACE_LABELS


def repair_proxy_kind(row: dict[str, Any]) -> str:
    """Sampling-only proxy. The repair target must come from later visible-packet labels."""
    predicate = row.get("predicate_label")
    matched = set(row.get("matched_predicates") or [])
    label_match = row.get("label_match_status")
    if predicate == "lying on" and (label_match == "exact_match" or "lying on" in matched):
        return "accept_like"
    if predicate == "standing on" and (label_match == "exact_match" or "standing on" in matched):
        return "accept_like"
    if predicate == "supported by" and (label_match == "exact_match" or "supported by" in matched):
        return "accept_like"
    if predicate == "lying on" and "standing on" in matched:
        return "reject_like"
    if predicate == "standing on" and "lying on" in matched:
        return "reject_like"
    if predicate == "supported by" and label_match == "pair_has_other_predicate" and not (matched & PREDICATE_SET):
        return "reject_like"
    return "exclude"


def load_support_rows(rga_dir: Path) -> tuple[list[dict[str, Any]], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    line_counts: dict[str, int] = {}
    for name in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = rga_dir / name
        line_count = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                line_count += 1
                row = json.loads(line)
                if row.get("predicate_family") != "support_contact":
                    continue
                if row.get("predicate_label") not in PREDICATE_SET:
                    continue
                proxy_kind = repair_proxy_kind(row)
                if proxy_kind == "exclude":
                    continue
                out = dict(row)
                out["_repair_proxy_kind"] = proxy_kind
                out["_directed_pair_key"] = directed_pair_key(out)
                out["_class_pair_key"] = class_pair_key(out)
                out["_predicate_class_pair_key"] = predicate_class_pair_key(out)
                out["_hard_surface_pair"] = hard_surface_pair(out)
                rows.append(out)
        line_counts[rel_path(path)] = line_count
    return rows, line_counts


def validate_inputs(summary: dict[str, Any], target_rows: list[dict[str, Any]], rga_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"error_type": "unexpected_ingestion_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INGESTION_NEXT:
        errors.append({"error_type": "unexpected_ingestion_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "ingestion_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    if boundary.get("split") != "train full only":
        errors.append({"error_type": "unexpected_split", "actual": boundary.get("split")})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if len(target_rows) != 480:
        errors.append({"error_type": "target_row_count_mismatch", "actual": len(target_rows), "expected": 480})
    for filename in ["train_hl_queue.jsonl", "train_lh_queue.jsonl"]:
        path = rga_dir / filename
        if not path.exists():
            errors.append({"error_type": "missing_train_queue", "path": rel_path(path)})
    return errors


def current_control_capacity(target_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = {
        "class_pair": lambda row: row["subject_object_class_pair"],
        "predicate_x_class_pair": lambda row: f"{row['predicate_label']}::{row['subject_object_class_pair']}",
        "predicate_x_class_pair_x_rank_band": lambda row: (
            f"{row['predicate_label']}::{row['subject_object_class_pair']}::{row.get('rank_band_hidden')}"
        ),
    }
    out: list[dict[str, Any]] = []
    usable = [row for row in target_rows if row.get("p_rel_target") is not None]
    for axis, key_fn in specs.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in usable:
            groups[key_fn(row)].append(row)
        mixed_groups = []
        for key, rows in groups.items():
            counts = Counter(int(row["p_rel_target"]) for row in rows)
            if counts[0] and counts[1]:
                mixed_groups.append((key, counts))
        out.append(
            {
                "axis": axis,
                "usable_rows": len(usable),
                "groups": len(groups),
                "mixed_groups": len(mixed_groups),
                "mixed_rows": sum(sum(counts.values()) for _, counts in mixed_groups),
                "balanced_rows": sum(2 * min(counts[0], counts[1]) for _, counts in mixed_groups),
            }
        )
    return out


def capacity_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axes = {
        "class_pair": "_class_pair_key",
        "predicate_x_class_pair": "_predicate_class_pair_key",
    }
    out: list[dict[str, Any]] = []
    for axis, field in axes.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[row[field]].append(row)
        mixed = []
        for key, group_rows in groups.items():
            counts = Counter(row["_repair_proxy_kind"] for row in group_rows)
            if counts["accept_like"] and counts["reject_like"]:
                mixed.append((key, counts, group_rows))
        out.append(
            {
                "axis": axis,
                "raw_groups": len(groups),
                "mixed_groups": len(mixed),
                "mixed_raw_rows": sum(len(group_rows) for _, _, group_rows in mixed),
                "balanced_raw_rows": sum(2 * min(counts["accept_like"], counts["reject_like"]) for _, counts, _ in mixed),
            }
        )
    predicate_counts = Counter(row["predicate_label"] for row in rows)
    kind_counts = Counter(row["_repair_proxy_kind"] for row in rows)
    for predicate, count in sorted(predicate_counts.items()):
        out.append({"axis": "raw_proxy_predicate", "value": predicate, "count": count})
    for kind, count in sorted(kind_counts.items()):
        out.append({"axis": "raw_proxy_kind", "value": kind, "count": count})
    return out


def select_repair_candidates(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["_predicate_class_pair_key"]].append(row)
    eligible_groups: set[str] = set()
    for key, group_rows in grouped.items():
        counts = Counter(row["_repair_proxy_kind"] for row in group_rows)
        if counts["accept_like"] and counts["reject_like"]:
            eligible_groups.add(key)

    by_pred_kind: dict[tuple[str, str], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["_predicate_class_pair_key"] not in eligible_groups:
            continue
        by_pred_kind[(row["predicate_label"], row["_repair_proxy_kind"])][row["_predicate_class_pair_key"]].append(row)

    for groups in by_pred_kind.values():
        for key in groups:
            groups[key].sort(
                key=lambda row: (
                    str(row.get("rank_band")),
                    str(row.get("queue_kind")),
                    stable_int(row.get("prediction_id")),
                )
            )

    need = {
        (predicate, proxy_kind): TARGET_PER_PREDICATE_KIND
        for predicate in PREDICATES
        for proxy_kind in ["accept_like", "reject_like"]
    }
    selected: list[dict[str, Any]] = []
    used_prediction_ids: set[str] = set()
    scan_counts: Counter[str] = Counter()
    directed_counts: Counter[str] = Counter()
    group_kind_counts: Counter[tuple[str, str]] = Counter()
    hard_count = 0

    progress = True
    while progress and any(count > 0 for count in need.values()):
        progress = False
        for pred_kind in list(need):
            if need[pred_kind] <= 0:
                continue
            groups = by_pred_kind.get(pred_kind, {})
            for group_key in sorted(groups, key=lambda key: (group_kind_counts[(key, pred_kind[1])], stable_int(key))):
                if group_kind_counts[(group_key, pred_kind[1])] >= GROUP_KIND_CAP:
                    continue
                candidate = None
                for row in groups[group_key]:
                    if row["prediction_id"] in used_prediction_ids:
                        continue
                    if scan_counts[row["scan_id"]] >= SCAN_CAP:
                        continue
                    if directed_counts[row["_directed_pair_key"]] >= DIRECTED_PAIR_CAP:
                        continue
                    if row["_hard_surface_pair"] and hard_count >= HARD_SURFACE_CAP:
                        continue
                    candidate = row
                    break
                if candidate is None:
                    continue
                selected.append(candidate)
                used_prediction_ids.add(candidate["prediction_id"])
                scan_counts[candidate["scan_id"]] += 1
                directed_counts[candidate["_directed_pair_key"]] += 1
                group_kind_counts[(group_key, pred_kind[1])] += 1
                hard_count += int(candidate["_hard_surface_pair"])
                need[pred_kind] -= 1
                progress = True
                break

    deficits = [
        {
            "predicate_label": predicate,
            "repair_proxy_kind": proxy_kind,
            "remaining_rows": remaining,
            "target_rows": TARGET_PER_PREDICATE_KIND,
        }
        for (predicate, proxy_kind), remaining in sorted(need.items())
        if remaining > 0
    ]
    return selected, deficits


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
        "repair_proxy_kind": row.get("_repair_proxy_kind"),
        "construction_bucket": "class_pair_controlled_repair_candidate",
        "hidden_stratum": f"{row.get('predicate_label')}::{row.get('_class_pair_key')}::{row.get('_repair_proxy_kind')}",
        "directed_pair_key": row.get("_directed_pair_key"),
        "subject_object_class_pair": row.get("_class_pair_key"),
        "predicate_class_pair": row.get("_predicate_class_pair_key"),
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


def count_rows(selected: list[dict[str, Any]]) -> dict[str, Any]:
    scan_counts = Counter(row["scan_id"] for row in selected)
    directed_counts = Counter(row["_directed_pair_key"] for row in selected)
    group_counts = Counter(row["_predicate_class_pair_key"] for row in selected)
    return {
        "selected_rows": len(selected),
        "predicate_counts": dict(Counter(row["predicate_label"] for row in selected)),
        "repair_proxy_kind_counts": dict(Counter(row["_repair_proxy_kind"] for row in selected)),
        "predicate_x_proxy_kind_counts": {
            f"{predicate}|{kind}": count
            for (predicate, kind), count in sorted(Counter((row["predicate_label"], row["_repair_proxy_kind"]) for row in selected).items())
        },
        "predicate_class_pair_groups": len(group_counts),
        "max_predicate_class_pair_rows": max(group_counts.values()) if group_counts else 0,
        "max_scan_rows": max(scan_counts.values()) if scan_counts else 0,
        "max_directed_pair_rows": max(directed_counts.values()) if directed_counts else 0,
        "hard_surface_rows": sum(1 for row in selected if row["_hard_surface_pair"]),
    }


def balance_rows(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    axes = {
        "predicate_label": Counter(row["predicate_label"] for row in selected),
        "repair_proxy_kind": Counter(row["_repair_proxy_kind"] for row in selected),
        "predicate_x_proxy_kind": Counter(f"{row['predicate_label']}|{row['_repair_proxy_kind']}" for row in selected),
        "predicate_class_pair": Counter(row["_predicate_class_pair_key"] for row in selected),
        "queue_kind_hidden": Counter(row.get("queue_kind") for row in selected),
        "label_match_status_hidden": Counter(row.get("label_match_status") for row in selected),
        "hard_surface_pair_hidden": Counter(str(row.get("_hard_surface_pair")) for row in selected),
        "rank_band_hidden": Counter(row.get("rank_band") for row in selected),
    }
    out: list[dict[str, Any]] = []
    for axis, counter in axes.items():
        total = sum(counter.values()) or 1
        for value, count in counter.most_common():
            out.append({"axis": axis, "value": value, "count": count, "share": count / total})
    return out


def cap_gate_rows(selected: list[dict[str, Any]], source_missing_errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = count_rows(selected)
    return [
        {"gate": "selected_rows", "value": counts["selected_rows"], "threshold": TARGET_TOTAL_ROWS, "pass": counts["selected_rows"] == TARGET_TOTAL_ROWS},
        {"gate": "per_predicate_rows", "value": counts["predicate_counts"], "threshold": TARGET_PER_PREDICATE, "pass": all(count == TARGET_PER_PREDICATE for count in counts["predicate_counts"].values())},
        {
            "gate": "per_predicate_proxy_kind_rows",
            "value": counts["predicate_x_proxy_kind_counts"],
            "threshold": TARGET_PER_PREDICATE_KIND,
            "pass": all(count == TARGET_PER_PREDICATE_KIND for count in counts["predicate_x_proxy_kind_counts"].values()),
        },
        {"gate": "predicate_class_pair_group_kind_cap", "value": counts["max_predicate_class_pair_rows"], "threshold": GROUP_KIND_CAP * 2, "pass": counts["max_predicate_class_pair_rows"] <= GROUP_KIND_CAP * 2},
        {"gate": "scan_cap", "value": counts["max_scan_rows"], "threshold": SCAN_CAP, "pass": counts["max_scan_rows"] <= SCAN_CAP},
        {"gate": "directed_pair_cap", "value": counts["max_directed_pair_rows"], "threshold": DIRECTED_PAIR_CAP, "pass": counts["max_directed_pair_rows"] <= DIRECTED_PAIR_CAP},
        {"gate": "hard_surface_cap", "value": counts["hard_surface_rows"], "threshold": HARD_SURFACE_CAP, "pass": counts["hard_surface_rows"] <= HARD_SURFACE_CAP},
        {"gate": "required_source_files", "value": len(source_missing_errors), "threshold": 0, "pass": len(source_missing_errors) == 0},
    ]


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Path Decision After Label Ingestion",
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
            "## Decision",
            "",
            "The current 480 proxy-label artifact is not smoke-ready because exact class-pair control is nearly absent. The selected path is class-pair controlled repair using train-full candidate mining.",
            "",
            "## Capacity",
            "",
            "```json",
            json.dumps(summary["capacity_summary"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Selected Repair Candidates",
            "",
            "```json",
            json.dumps(summary["selected_candidate_summary"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "Boundary: repair proxy labels are used only for sampling. They are not final targets. The next stage must materialize visible packets and fill labels again.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    ingestion_summary = read_json(args.ingestion_dir / "summary.json")
    target_rows = read_jsonl(args.ingestion_dir / "target_rows.jsonl")
    validation_errors = validate_inputs(ingestion_summary, target_rows, args.rga_dir)
    current_capacity = current_control_capacity(target_rows)

    source_rows, source_line_counts = load_support_rows(args.rga_dir)
    full_capacity = capacity_rows(source_rows)
    selected_rows, selection_deficits = select_repair_candidates(source_rows)

    visible_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    packet_sources: list[dict[str, Any]] = []
    source_missing_errors: list[dict[str, Any]] = []
    for idx, row in enumerate(selected_rows, start=1):
        review_id = stable_review_id(row, idx)
        visible_rows.append(visible_row(row, review_id))
        hidden_rows.append(hidden_row(row, review_id))
        packet_source = packet_source_row(row, review_id, args.three_rscan_root)
        packet_sources.append(packet_source)
        if not packet_source["all_required_sources_exist"]:
            source_missing_errors.append(
                {
                    "review_id": review_id,
                    "error_type": "required_source_missing",
                    "missing_sources": [
                        key for key, value in packet_source.items() if key.endswith("_exists") and not value
                    ],
                }
            )

    cap_gates = cap_gate_rows(selected_rows, source_missing_errors)
    validation_errors.extend(selection_deficits)
    validation_errors.extend(source_missing_errors)
    for gate in cap_gates:
        if gate["pass"] is not True:
            validation_errors.append({"error_type": "cap_gate_failed", **gate})

    status = STATUS_READY if not validation_errors else STATUS_PARTIAL
    next_todo = NEXT_TODO
    if any(error.get("error_type", "").startswith("unexpected") or error.get("error_type") == "missing_train_queue" for error in validation_errors):
        status = STATUS_ERROR
        next_todo = "repair_support_contact_visual_mesh_audit_path_decision_after_label_ingestion"

    output_paths = {
        "balance": output_dir / "balance.csv",
        "cap_gates": output_dir / "cap_gates.csv",
        "current_control_capacity": output_dir / "current_control_capacity.csv",
        "full_train_capacity": output_dir / "full_train_capacity.csv",
        "hidden_manifest": output_dir / "hidden_manifest.jsonl",
        "label_sheet_template": output_dir / "label_sheet_template.csv",
        "packet_source_manifest": output_dir / "packet_source_manifest.jsonl",
        "repair_candidate_manifest": output_dir / "repair_candidate_manifest.jsonl",
        "report": output_dir / "report.md",
        "summary": output_dir / "summary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    selected_summary = count_rows(selected_rows)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "current_control_capacity": current_capacity,
        "capacity_summary": {
            "source_rows_after_proxy_filter": len(source_rows),
            "source_line_counts": source_line_counts,
            "full_train_capacity_rows": full_capacity,
            "selection_policy": {
                "target_total_rows": TARGET_TOTAL_ROWS,
                "target_per_predicate": TARGET_PER_PREDICATE,
                "target_per_predicate_proxy_kind": TARGET_PER_PREDICATE_KIND,
                "control_axis": "predicate_x_subject_object_class_pair",
                "group_kind_cap": GROUP_KIND_CAP,
                "scan_cap": SCAN_CAP,
                "directed_pair_cap": DIRECTED_PAIR_CAP,
                "hard_surface_cap": HARD_SURFACE_CAP,
            },
        },
        "selected_candidate_summary": selected_summary,
        "cap_gates": cap_gates,
        "boundary": {
            "split": "train full only",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "fills_new_labels": False,
            "paper_evidence_allowed": False,
            "repair_proxy_is_sampling_only": True,
            "final_target_requires_visible_packet_label_fill": True,
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
    }

    write_csv(output_paths["current_control_capacity"], current_capacity)
    write_csv(output_paths["full_train_capacity"], full_capacity)
    write_csv(output_paths["label_sheet_template"], visible_rows)
    write_jsonl(output_paths["hidden_manifest"], hidden_rows)
    write_jsonl(output_paths["packet_source_manifest"], packet_sources)
    write_jsonl(output_paths["repair_candidate_manifest"], hidden_rows)
    write_csv(output_paths["balance"], balance_rows(selected_rows))
    write_csv(output_paths["cap_gates"], cap_gates)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == STATUS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
