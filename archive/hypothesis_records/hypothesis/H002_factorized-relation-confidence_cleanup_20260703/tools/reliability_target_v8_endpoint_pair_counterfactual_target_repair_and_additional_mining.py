#!/usr/bin/env python3
"""Repair-audit v8 labels and mine additional exact endpoint-pair contrasts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_LABEL_INGESTION_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_label_ingestion_codex_proxy_user_requested"
DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit_codex_proxy_user_requested"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_PACKET_MANIFESTS = [
    RGA_ROOT / "independent_asset_packets/packet_manifest.jsonl",
    RGA_ROOT / "reliability_target_v5_cell_contrast_asset_packets/generated_packet_manifest.jsonl",
    RGA_ROOT / "reliability_target_v6_shortcut_controlled_asset_packets_codex_proxy_user_requested/generated_packet_manifest.jsonl",
    RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_asset_packets_codex_proxy_user_requested/generated_packet_manifest.jsonl",
    RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets_codex_proxy_user_requested/generated_replacement_packet_manifest.jsonl",
    RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_asset_packets_codex_proxy_user_requested/generated_packet_manifest.jsonl",
]
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_target_repair_and_additional_mining_codex_proxy_user_requested"

EXPECTED_INGESTION_STATUS = "h002_reliability_target_v8_endpoint_pair_counterfactual_label_ingested_with_probe_risk"
EXPECTED_AUDIT_STATUS = "h002_reliability_target_v8_endpoint_pair_counterfactual_target_independence_audit_blocked_shortcut_risk"

PRIMARY_FAMILIES = {"support_contact", "relative_vertical"}
SCAN_PAIR_CAP_PRIMARY = 4
LABEL_PAIR_CAP_PRIMARY = 6
FAMILY_CELL_CAP_PRIMARY = 6
VERTICAL_PAIR_TARGET = 60
SUPPORT_PAIR_TARGET = 40
PROXIMITY_PAIR_TARGET = 20

HARD_ROOM_SURFACES = {"floor", "wall", "ceiling"}
STRUCTURAL_CONTEXT = {
    "floor",
    "wall",
    "ceiling",
    "room",
    "door",
    "doorframe",
    "window",
    "blinds",
    "curtain",
}
GENERIC_LABELS = {"object", "item", "stuff", "thing"}

VISIBLE_FIELDS = [
    "blind_review_id",
    "review_scope",
    "scan_id",
    "scene_context_id",
    "subject_id",
    "subject_label",
    "predicate_label",
    "predicate_family",
    "object_id",
    "object_label",
    "family_question",
    "endpoint_pair_note",
    "counterfactual_prompt",
    "supporting_cues",
    "contradicting_cues",
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "reviewer_id",
    "review_round",
    "endpoint_identity_v6",
    "pair_evaluability_v6",
    "geometry_support_v6",
    "relation_usefulness_v6",
    "relation_reliability_state_v6",
    "primary_reason_v6",
    "uncertainty_reason_v6",
    "label_notes_v6",
]

REVIEW_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_identity_v6",
    "pair_evaluability_v6",
    "geometry_support_v6",
    "relation_usefulness_v6",
    "relation_reliability_state_v6",
    "primary_reason_v6",
    "uncertainty_reason_v6",
    "label_notes_v6",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label-ingestion-dir", type=Path, default=DEFAULT_LABEL_INGESTION_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--packet-manifest", type=Path, action="append", default=list(DEFAULT_PACKET_MANIFESTS))
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


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


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
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def stable_int(value: str) -> int:
    return int(stable_hash(value)[:12], 16)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 999999) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def exact_key(row: dict[str, Any]) -> str:
    return f"{row['scan_id']}|{row['subgraph_id']}|{row['subject_id']}|{row['object_id']}"


def endpoint_type(label: str) -> str:
    if label in HARD_ROOM_SURFACES:
        return f"hard_room_surface:{label}"
    if label in STRUCTURAL_CONTEXT:
        return f"structural_context:{label}"
    return "object"


def endpoint_pattern(subject_label: str, object_label: str) -> str:
    same = "same_label" if subject_label == object_label else "different_label"
    return f"sub={endpoint_type(subject_label)}|obj={endpoint_type(object_label)}|{same}"


def is_packet_ready(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    status = row.get("packet_status") or row.get("evidence_packet_status")
    return (
        status == "ready"
        and bool(row.get("multiview_packet"))
        and bool(row.get("pointcloud_or_mesh_packet"))
        and bool(row.get("contact_or_context_sheet"))
    )


def packet_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (str(row.get("scan_id")), str(row.get("subject_id")), str(row.get("object_id")), str(row.get("predicate_label")))


def load_ready_packets(paths: list[Path]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    packets: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for path in paths:
        abs_path = as_abs(path)
        if not abs_path.exists():
            continue
        for row in iter_jsonl(abs_path):
            if is_packet_ready(row):
                packets[packet_key(row)] = row
    return packets


def validate_inputs(ingestion_summary: dict[str, Any], audit_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if ingestion_summary.get("status") != EXPECTED_INGESTION_STATUS:
        errors.append({"error_type": "unexpected_ingestion_status", "value": ingestion_summary.get("status")})
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "value": audit_summary.get("status")})
    for source_name, summary in [("ingestion", ingestion_summary), ("audit", audit_summary)]:
        boundary = summary.get("boundary", {})
        if boundary.get("validation_usage") is not False or boundary.get("test_usage") is not False:
            errors.append({"error_type": "unexpected_validation_test_usage", "source": source_name, "boundary": boundary})
    return errors


def group_value(row: dict[str, Any], key: str) -> str:
    return str(row.get(key, "missing"))


def current_repair_audit(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    specs = {
        "exact_endpoint": ["exact_endpoint_pair_key_hidden"],
        "exact_endpoint_family": ["exact_endpoint_pair_key_hidden", "predicate_family"],
        "exact_endpoint_predicate": ["exact_endpoint_pair_key_hidden", "predicate_label"],
        "exact_endpoint_bucket": ["exact_endpoint_pair_key_hidden", "semantic_geometry_bucket_hidden"],
        "exact_endpoint_geometry_status": ["exact_endpoint_pair_key_hidden", "geometry_status_hidden"],
        "label_pair_family": ["subject_object_label_pair_hidden", "predicate_family"],
        "label_pair_predicate": ["subject_object_label_pair_hidden", "predicate_label"],
        "family_bucket": ["predicate_family", "semantic_geometry_bucket_hidden"],
        "predicate_bucket": ["predicate_label", "semantic_geometry_bucket_hidden"],
    }
    summaries: list[dict[str, Any]] = []
    slice_rows: list[dict[str, Any]] = []
    best_balanced_rows = 0
    best_spec = "none"
    for spec_name, keys in specs.items():
        groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            group_key = "||".join(f"{key}={group_value(row, key)}" for key in keys)
            groups[group_key].append(row)
        mixed_groups = []
        balanced_rows = []
        for group_key, group_rows in groups.items():
            counts = Counter(int(row["target_y"]) for row in group_rows)
            if counts[0] > 0 and counts[1] > 0:
                mixed_groups.append((group_key, counts))
                per_class = min(counts[0], counts[1])
                for cls in [0, 1]:
                    cls_rows = sorted([row for row in group_rows if int(row["target_y"]) == cls], key=lambda item: str(item.get("prediction_id")))
                    balanced_rows.extend(cls_rows[:per_class])
        if len(balanced_rows) > best_balanced_rows:
            best_balanced_rows = len(balanced_rows)
            best_spec = spec_name
        counts = Counter(int(row["target_y"]) for row in balanced_rows)
        summaries.append(
            {
                "spec_name": spec_name,
                "group_keys": "|".join(keys),
                "groups": len(groups),
                "mixed_groups": len(mixed_groups),
                "mixed_rows": sum(sum(counts.values()) for _, counts in mixed_groups),
                "balanced_rows": len(balanced_rows),
                "balanced_positive": counts[1],
                "balanced_negative": counts[0],
                "strict_size_ready": len(balanced_rows) >= 50 and min(counts.values() or [0]) >= 20,
                "posterior_repair_candidate": False,
            }
        )
        for row in balanced_rows:
            slice_rows.append(
                {
                    "repair_spec": spec_name,
                    "blind_review_id": row.get("blind_review_id"),
                    "prediction_id": row.get("prediction_id"),
                    "target_y": row.get("target_y"),
                    "scan_id": row.get("scan_id"),
                    "subgraph_id": row.get("subgraph_id"),
                    "subject_label": row.get("subject_label"),
                    "predicate_label": row.get("predicate_label"),
                    "predicate_family": row.get("predicate_family"),
                    "object_label": row.get("object_label"),
                    "exact_endpoint_pair_key_hidden": row.get("exact_endpoint_pair_key_hidden"),
                    "semantic_geometry_bucket_hidden": row.get("semantic_geometry_bucket_hidden"),
                    "geometry_status_hidden": row.get("geometry_status_hidden"),
                }
            )
    summary = {
        "current_binary_rows": len(rows),
        "current_positive": sum(1 for row in rows if int(row["target_y"]) == 1),
        "current_negative": sum(1 for row in rows if int(row["target_y"]) == 0),
        "best_repair_spec": best_spec,
        "best_repair_balanced_rows": best_balanced_rows,
        "repair_sufficient_for_posterior": best_balanced_rows >= 50,
    }
    return summaries, slice_rows, summary


def enrich_queue_row(row: dict[str, Any], queue_path: Path) -> dict[str, Any]:
    subject_label = norm(row.get("subject_label"))
    object_label = norm(row.get("object_label"))
    predicate_label = norm(row.get("predicate_label"))
    ids = sorted([str(row.get("subject_id")), str(row.get("object_id"))])
    return {
        **row,
        "source_queue_path": rel_path(queue_path),
        "scene_context_id": str(row.get("subgraph_id")),
        "subject_label_norm": subject_label,
        "object_label_norm": object_label,
        "predicate_label_norm": predicate_label,
        "exact_endpoint_pair_key": exact_key(row),
        "undirected_endpoint_pair_key": f"{row['scan_id']}|{row['subgraph_id']}|{ids[0]}|{ids[1]}",
        "subject_object_label_pair": f"{subject_label}|{object_label}",
        "subject_object_family_cell": f"{subject_label}|{object_label}|{row.get('predicate_family')}",
        "endpoint_pattern": endpoint_pattern(subject_label, object_label),
        "structural_pair": subject_label in STRUCTURAL_CONTEXT or object_label in STRUCTURAL_CONTEXT,
        "hard_room_surface_pair": subject_label in HARD_ROOM_SURFACES or object_label in HARD_ROOM_SURFACES,
        "generic_endpoint_pair": subject_label in GENERIC_LABELS or object_label in GENERIC_LABELS,
        "semantic_rank_int": as_int(row.get("semantic_rank")),
        "semantic_score_norm_float": as_float(row.get("semantic_score_norm")),
        "p_geom_valid_float": as_float(row.get("p_geom_valid")),
    }


def read_train_rows(hl_queue: Path, lh_queue: Path) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    counts = {
        "read_rows_by_queue": Counter(),
        "kept_rows_by_family": Counter(),
        "kept_rows_by_queue": Counter(),
    }
    required = ["prediction_id", "scan_id", "subgraph_id", "subject_id", "subject_label", "predicate_label", "predicate_family", "object_id", "object_label", "queue_kind"]
    for path, queue_name in [(hl_queue, "HL"), (lh_queue, "LH")]:
        for row in iter_jsonl(path):
            counts["read_rows_by_queue"][queue_name] += 1
            missing = [field for field in required if field not in row]
            if missing:
                errors.append({"error_type": "missing_train_queue_fields", "missing": missing, "prediction_id": row.get("prediction_id"), "queue": queue_name})
                continue
            if row.get("predicate_family") not in {"support_contact", "relative_vertical", "proximity"}:
                continue
            enriched = enrich_queue_row(row, path)
            rows.append(enriched)
            counts["kept_rows_by_family"][str(row.get("predicate_family"))] += 1
            counts["kept_rows_by_queue"][queue_name] += 1
    return rows, {key: dict(value) for key, value in counts.items()}, errors


def group_inventory(rows: list[dict[str, Any]], current_exact_keys: set[str]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    by_exact: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_exact[row["exact_endpoint_pair_key"]].append(row)
    inventory: list[dict[str, Any]] = []
    for group_key, group_rows in by_exact.items():
        predicate_counts = Counter(row["predicate_label_norm"] for row in group_rows)
        family_counts = Counter(row["predicate_family"] for row in group_rows)
        queue_counts = Counter(row["queue_kind"] for row in group_rows)
        structural = any(row["structural_pair"] for row in group_rows)
        hard = any(row["hard_room_surface_pair"] for row in group_rows)
        generic = any(row["generic_endpoint_pair"] for row in group_rows)
        predicate_set = set(predicate_counts)
        support_predicates = predicate_set & {"standing on", "lying on", "supported by"}
        row = group_rows[0]
        group_type_flags = {
            "vertical_direction_counterfactual": {"higher than", "lower than"} <= predicate_set,
            "support_pose_counterfactual": {"standing on", "lying on"} <= predicate_set,
            "support_any_alternative": len(support_predicates) >= 2,
            "proximity_context_candidate": "close by" in predicate_set and len(predicate_set) >= 2,
        }
        inventory.append(
            {
                "group_key": group_key,
                "scan_id": row.get("scan_id"),
                "subgraph_id": row.get("subgraph_id"),
                "subject_id": row.get("subject_id"),
                "object_id": row.get("object_id"),
                "subject_label": row.get("subject_label"),
                "object_label": row.get("object_label"),
                "subject_object_label_pair": row.get("subject_object_label_pair"),
                "row_count": len(group_rows),
                "predicate_count": len(predicate_counts),
                "predicate_counts": dict(sorted(predicate_counts.items())),
                "family_counts": dict(sorted(family_counts.items())),
                "queue_counts": dict(sorted(queue_counts.items())),
                "has_current_v8_label": group_key in current_exact_keys,
                "structural_pair": structural,
                "hard_room_surface_pair": hard,
                "generic_endpoint_pair": generic,
                **group_type_flags,
            }
        )
    counts = {
        "exact_endpoint_groups": len(inventory),
        "vertical_direction_counterfactual_groups": sum(1 for item in inventory if item["vertical_direction_counterfactual"]),
        "support_pose_counterfactual_groups": sum(1 for item in inventory if item["support_pose_counterfactual"]),
        "support_any_alternative_groups": sum(1 for item in inventory if item["support_any_alternative"]),
        "proximity_context_candidate_groups": sum(1 for item in inventory if item["proximity_context_candidate"]),
        "strict_nonstruct_not_current_vertical_groups": sum(
            1
            for item in inventory
            if item["vertical_direction_counterfactual"] and not item["structural_pair"] and not item["generic_endpoint_pair"] and not item["has_current_v8_label"]
        ),
        "strict_nonstruct_not_current_support_pose_groups": sum(
            1
            for item in inventory
            if item["support_pose_counterfactual"] and not item["structural_pair"] and not item["generic_endpoint_pair"] and not item["has_current_v8_label"]
        ),
        "strict_nonstruct_not_current_proximity_groups": sum(
            1
            for item in inventory
            if item["proximity_context_candidate"] and not item["structural_pair"] and not item["generic_endpoint_pair"] and not item["has_current_v8_label"]
        ),
    }
    return inventory, by_exact, counts


def row_priority(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["structural_pair"],
        row["hard_room_surface_pair"],
        row["generic_endpoint_pair"],
        row["semantic_rank_int"],
        -row["semantic_score_norm_float"],
        stable_int(str(row.get("prediction_id"))),
    )


def group_priority(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        item["structural_pair"],
        item["hard_room_surface_pair"],
        item["generic_endpoint_pair"],
        item["has_current_v8_label"],
        -item["predicate_count"],
        stable_int(item["group_key"]),
    )


def choose_predicate_row(group_rows: list[dict[str, Any]], predicate: str) -> dict[str, Any] | None:
    candidates = [row for row in group_rows if row["predicate_label_norm"] == predicate]
    if not candidates:
        return None
    return sorted(candidates, key=row_priority)[0]


def can_select_pair(rows: list[dict[str, Any]], counters: dict[str, Counter], used_prediction_ids: set[str]) -> bool:
    if any(str(row.get("prediction_id")) in used_prediction_ids for row in rows):
        return False
    scan = str(rows[0]["scan_id"])
    label_pair = str(rows[0]["subject_object_label_pair"])
    if counters["scan_pair"][scan] + 1 > SCAN_PAIR_CAP_PRIMARY:
        return False
    if counters["label_pair"][label_pair] + 1 > LABEL_PAIR_CAP_PRIMARY:
        return False
    for row in rows:
        family_cell = str(row["subject_object_family_cell"])
        if counters["family_cell"][family_cell] + 1 > FAMILY_CELL_CAP_PRIMARY:
            return False
    return True


def selected_candidate_row(row: dict[str, Any], batch_role: str, pair_id: str, packet: dict[str, Any] | None, hidden_pair_type: str) -> dict[str, Any]:
    ready = is_packet_ready(packet)
    return {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_additional_candidate_v1",
        "batch_name": "v8_target_repair_additional_mining",
        "blind_review_id": "ftv8r_" + stable_hash("v8_repair:" + str(row["prediction_id"]))[:12],
        "review_scope": "h002_reliability_v8_endpoint_pair_counterfactual_repair_review",
        "additional_batch_role_hidden": batch_role,
        "counterfactual_pair_id_hidden": pair_id,
        "counterfactual_pair_type_hidden": hidden_pair_type,
        "prediction_id": row.get("prediction_id"),
        "split": "train",
        "source_id": row.get("source_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "scene_context_id": row.get("scene_context_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "source_queue_hidden": row.get("queue_kind"),
        "semantic_rank_hidden": row.get("semantic_rank"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm"),
        "semantic_score_raw_hidden": row.get("semantic_score_raw"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "geometry_status_hidden": row.get("geometry_status"),
        "h001_verification_status_hidden": row.get("h001_verification_status"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket"),
        "label_match_status_hidden": row.get("label_match_status"),
        "machine_hint_hidden": row.get("machine_hint"),
        "rank_band_hidden": row.get("rank_band"),
        "exact_endpoint_pair_key_hidden": row.get("exact_endpoint_pair_key"),
        "undirected_endpoint_pair_key_hidden": row.get("undirected_endpoint_pair_key"),
        "subject_object_label_pair_hidden": row.get("subject_object_label_pair"),
        "subject_object_family_cell_hidden": row.get("subject_object_family_cell"),
        "endpoint_pattern_hidden": row.get("endpoint_pattern"),
        "structural_pair_hidden": row.get("structural_pair"),
        "hard_room_surface_pair_hidden": row.get("hard_room_surface_pair"),
        "generic_endpoint_pair_hidden": row.get("generic_endpoint_pair"),
        "packet_status_hidden": "ready" if ready else "asset_needed",
        "packet_source_hidden": "existing_packet_manifest" if ready else "asset_needed",
        "multiview_packet": (packet or {}).get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": (packet or {}).get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": (packet or {}).get("contact_or_context_sheet", ""),
        "label_sheet_allowed": True,
        "label_fill_allowed": False,
        "posterior_input_allowed": False,
    }


def visible_prompt(row: dict[str, Any]) -> dict[str, str]:
    family = str(row.get("predicate_family"))
    label = norm(row.get("predicate_label"))
    if family == "relative_vertical":
        return {
            "question": "Is the subject clearly higher or lower than the object as stated by the predicate?",
            "supporting": "clear vertical ordering, predicate direction matches evidence, comparable object-level endpoints",
            "contradicting": "opposite vertical direction, ambiguous height, non-comparable endpoint, endpoint identity issue",
        }
    if family == "support_contact":
        pose = "standing/lying pose" if label in {"standing on", "lying on"} else "support/contact direction"
        return {
            "question": "Does the subject physically contact, rest on, or receive support from the object as stated?",
            "supporting": f"visible contact or plausible support, correct {pose}, non-trivial object pair",
            "contradicting": "nearby without contact/support, clear gap, wrong pose predicate, endpoint identity issue, trivial structure",
        }
    if family == "proximity":
        return {
            "question": "Is the subject meaningfully close to the object, beyond a dense/trivial scene relation?",
            "supporting": "clear proximity with useful scene-graph meaning, non-trivial object pair",
            "contradicting": "dense relation noise, trivial room context, weak visual evidence, endpoint identity issue",
        }
    return {
        "question": "Does the relation hold according to the evidence?",
        "supporting": "relation is supported by visual and geometric evidence",
        "contradicting": "relation is contradicted, trivial, or not evaluable from the evidence",
    }


def visible_row(row: dict[str, Any]) -> dict[str, Any]:
    prompt = visible_prompt(row)
    ready = row.get("packet_status_hidden") == "ready"
    output = {
        "blind_review_id": row["blind_review_id"],
        "review_scope": row["review_scope"],
        "scan_id": row.get("scan_id", ""),
        "scene_context_id": row.get("scene_context_id", ""),
        "subject_id": row.get("subject_id", ""),
        "subject_label": row.get("subject_label", ""),
        "predicate_label": row.get("predicate_label", ""),
        "predicate_family": row.get("predicate_family", ""),
        "object_id": row.get("object_id", ""),
        "object_label": row.get("object_label", ""),
        "family_question": prompt["question"],
        "endpoint_pair_note": "Evaluate this predicate for the shown subject-object pair; paired counterfactual predicates are not shown as labels.",
        "counterfactual_prompt": "Judge only whether this relation is reliable for this endpoint pair, not whether another relation could also be true.",
        "supporting_cues": prompt["supporting"],
        "contradicting_cues": prompt["contradicting"],
        "evidence_packet_status": "ready" if ready else "asset_needed",
        "multiview_packet": row.get("multiview_packet", "") if ready else "",
        "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", "") if ready else "",
        "contact_or_context_sheet": row.get("contact_or_context_sheet", "") if ready else "",
    }
    for field in REVIEW_FIELDS:
        output[field] = ""
    return output


def asset_request_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_repair_asset_request_v1",
        "blind_review_id": row["blind_review_id"],
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "scene_context_id": row["scene_context_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "target_packet_stem": row["blind_review_id"],
        "requested_artifacts": ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"],
        "asset_request_reason": "v8_repair_additional_exact_endpoint_pair_counterfactual_candidate_needs_packet",
        "hidden_pair_type": row["counterfactual_pair_type_hidden"],
    }


def select_pairs(
    inventory: list[dict[str, Any]],
    by_exact: dict[str, list[dict[str, Any]]],
    packets: dict[tuple[str, str, str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    proximity_preview: list[dict[str, Any]] = []
    counters = {"scan_pair": Counter(), "label_pair": Counter(), "family_cell": Counter()}
    used_prediction_ids: set[str] = set()
    used_group_keys: set[str] = set()

    def add_pair(rows: list[dict[str, Any]], batch_role: str, pair_type: str) -> bool:
        if len(rows) != 2:
            return False
        if not can_select_pair(rows, counters, used_prediction_ids):
            return False
        pair_id = "ftv8r_pair_" + stable_hash("|".join(str(row.get("prediction_id")) for row in rows))[:12]
        for row in rows:
            packet = packets.get(packet_key(row))
            selected_row = selected_candidate_row(row, batch_role, pair_id, packet, pair_type)
            selected.append(selected_row)
            used_prediction_ids.add(str(row.get("prediction_id")))
            counters["family_cell"][str(row["subject_object_family_cell"])] += 1
        counters["scan_pair"][str(rows[0]["scan_id"])] += 1
        counters["label_pair"][str(rows[0]["subject_object_label_pair"])] += 1
        used_group_keys.add(str(rows[0]["exact_endpoint_pair_key"]))
        return True

    vertical_groups = [
        item
        for item in inventory
        if item["vertical_direction_counterfactual"]
        and not item["structural_pair"]
        and not item["generic_endpoint_pair"]
        and not item["has_current_v8_label"]
    ]
    for item in sorted(vertical_groups, key=group_priority):
        if sum(1 for row in selected if row["additional_batch_role_hidden"] == "vertical_direction_counterfactual") >= VERTICAL_PAIR_TARGET * 2:
            break
        group_rows = by_exact[item["group_key"]]
        lower = choose_predicate_row(group_rows, "lower than")
        higher = choose_predicate_row(group_rows, "higher than")
        if lower and higher:
            add_pair([lower, higher], "vertical_direction_counterfactual", "same_endpoint_higher_lower")

    support_groups = [
        item
        for item in inventory
        if item["support_pose_counterfactual"]
        and not item["structural_pair"]
        and not item["generic_endpoint_pair"]
        and not item["has_current_v8_label"]
        and item["group_key"] not in used_group_keys
    ]
    for item in sorted(support_groups, key=group_priority):
        if sum(1 for row in selected if row["additional_batch_role_hidden"] == "support_pose_counterfactual") >= SUPPORT_PAIR_TARGET * 2:
            break
        group_rows = by_exact[item["group_key"]]
        standing = choose_predicate_row(group_rows, "standing on")
        lying = choose_predicate_row(group_rows, "lying on")
        if standing and lying:
            add_pair([standing, lying], "support_pose_counterfactual", "same_endpoint_standing_lying")

    proximity_groups = [
        item
        for item in inventory
        if item["proximity_context_candidate"]
        and not item["structural_pair"]
        and not item["generic_endpoint_pair"]
        and not item["has_current_v8_label"]
        and item["group_key"] not in used_group_keys
    ]
    prox_pairs = 0
    for item in sorted(proximity_groups, key=group_priority):
        if prox_pairs >= PROXIMITY_PAIR_TARGET:
            break
        group_rows = by_exact[item["group_key"]]
        close = choose_predicate_row(group_rows, "close by")
        other_candidates = [row for row in group_rows if row["predicate_label_norm"] != "close by"]
        if not close or not other_candidates:
            continue
        other = sorted(other_candidates, key=row_priority)[0]
        pair_id = "ftv8r_future_pair_" + stable_hash(str(close.get("prediction_id")) + "|" + str(other.get("prediction_id")))[:12]
        for row in [close, other]:
            packet = packets.get(packet_key(row))
            proximity_preview.append(selected_candidate_row(row, "future_proximity_context_preview", pair_id, packet, "same_endpoint_close_by_context"))
        prox_pairs += 1

    summary = {
        "selected_primary_rows": len(selected),
        "selected_primary_pairs": len({row["counterfactual_pair_id_hidden"] for row in selected}),
        "vertical_direction_rows": sum(1 for row in selected if row["additional_batch_role_hidden"] == "vertical_direction_counterfactual"),
        "support_pose_rows": sum(1 for row in selected if row["additional_batch_role_hidden"] == "support_pose_counterfactual"),
        "packet_ready_primary_rows": sum(1 for row in selected if row["packet_status_hidden"] == "ready"),
        "asset_needed_primary_rows": sum(1 for row in selected if row["packet_status_hidden"] != "ready"),
        "selected_scans": len({row["scan_id"] for row in selected}),
        "selected_label_pairs": len({row["subject_object_label_pair_hidden"] for row in selected}),
        "max_rows_per_scan": max(Counter(row["scan_id"] for row in selected).values()) if selected else 0,
        "max_rows_per_label_pair": max(Counter(row["subject_object_label_pair_hidden"] for row in selected).values()) if selected else 0,
        "future_proximity_preview_rows": len(proximity_preview),
        "future_proximity_preview_pairs": len({row["counterfactual_pair_id_hidden"] for row in proximity_preview}),
        "packet_ready_proximity_preview_rows": sum(1 for row in proximity_preview if row["packet_status_hidden"] == "ready"),
        "asset_needed_proximity_preview_rows": sum(1 for row in proximity_preview if row["packet_status_hidden"] != "ready"),
    }
    return selected, proximity_preview, summary


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 V8 Target Repair And Additional Mining",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        summary["decision"],
        "",
        "## Current V8 Repair Audit",
        "",
        "Existing labels are not enough for a strict repaired posterior target.",
        "",
        "```text",
        f"current_binary_rows = {summary['current_repair_summary']['current_binary_rows']}",
        f"positive/negative = {summary['current_repair_summary']['current_positive']} / {summary['current_repair_summary']['current_negative']}",
        f"best_repair_spec = {summary['current_repair_summary']['best_repair_spec']}",
        f"best_repair_balanced_rows = {summary['current_repair_summary']['best_repair_balanced_rows']}",
        f"repair_sufficient_for_posterior = {summary['current_repair_summary']['repair_sufficient_for_posterior']}",
        "```",
        "",
        "## Additional Mining",
        "",
        "Full-train exact endpoint-pair inventory:",
        "",
        "```text",
    ]
    for key, value in summary["inventory_counts"].items():
        lines.append(f"{key} = {value}")
    lines.extend(
        [
            "```",
            "",
            "Selected primary additional candidates:",
            "",
            "```text",
        ]
    )
    for key, value in summary["selection_summary"].items():
        lines.append(f"{key} = {value}")
    lines.extend(
        [
            "```",
            "",
            "## Interpretation",
            "",
            "- Current v8 labels cannot be repaired into a shortcut-controlled posterior target.",
            "- Full-train mining has enough exact endpoint-pair counterfactual candidates for a new stricter label batch.",
            "- The strongest next batch is `higher than`/`lower than` direction contrast plus `standing on`/`lying on` pose contrast.",
            "- `close by` has abundant exact-pair context candidates, but it should remain a future/diagnostic extension because dense proximity noise can make labels ambiguous.",
            "- Most newly selected rows still need evidence packets before label readiness/fill.",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    ingestion_dir = as_abs(args.label_ingestion_dir)
    audit_dir = as_abs(args.audit_dir)
    ingestion_summary = read_json(ingestion_dir / "summary.json")
    audit_summary = read_json(audit_dir / "summary.json")
    validation_errors = validate_inputs(ingestion_summary, audit_summary)

    current_rows = list(iter_jsonl(ingestion_dir / "relation_reliability_v6_binary_targets.jsonl"))
    current_exact_keys = {str(row.get("exact_endpoint_pair_key_hidden")) for row in current_rows}
    current_repair_summaries, current_slice_rows, current_repair_summary = current_repair_audit(current_rows)

    train_rows, train_counts, train_errors = read_train_rows(as_abs(args.hl_queue), as_abs(args.lh_queue))
    validation_errors.extend(train_errors)
    inventory, by_exact, inventory_counts = group_inventory(train_rows, current_exact_keys)
    packets = load_ready_packets(args.packet_manifest)
    selected, proximity_preview, selection_summary = select_pairs(inventory, by_exact, packets)

    asset_requests = [asset_request_row(row) for row in selected if row["packet_status_hidden"] != "ready"]
    visible_rows = [visible_row(row) for row in selected]
    proximity_visible_rows = [visible_row(row) for row in proximity_preview]

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "current_repair_audit": output_dir / "current_repair_audit.csv",
        "current_repair_candidate_rows": output_dir / "current_repair_candidate_rows.jsonl",
        "full_train_contrast_inventory": output_dir / "full_train_contrast_inventory.csv",
        "selected_primary_candidates": output_dir / "selected_primary_candidates.jsonl",
        "selected_primary_label_sheet": output_dir / "selected_primary_label_sheet.tsv",
        "asset_request_manifest": output_dir / "asset_request_manifest.jsonl",
        "future_proximity_preview_candidates": output_dir / "future_proximity_preview_candidates.jsonl",
        "future_proximity_preview_label_sheet": output_dir / "future_proximity_preview_label_sheet.tsv",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    if validation_errors:
        status = "h002_reliability_target_v8_repair_and_additional_mining_errors"
        decision = "Input validation errors remain; fix them before using any repair/mining output."
        next_todo = "fix_reliability_target_v8_repair_and_additional_mining_errors"
    elif current_repair_summary["repair_sufficient_for_posterior"]:
        status = "h002_reliability_target_v8_current_repair_possible_unexpected"
        decision = "A current-label repair slice appears large enough; run target-independence audit on that slice before posterior smoke."
        next_todo = "reliability_target_v8_repaired_slice_target_independence_audit"
    elif selection_summary["selected_primary_rows"] >= 160:
        status = "h002_reliability_target_v8_current_repair_insufficient_additional_mining_ready"
        decision = (
            "Current v8 labels cannot form a strict repaired target, but full-train exact endpoint-pair "
            "mining produced a sizeable additional label batch. Proceed to asset packet generation/readiness, "
            "not posterior smoke."
        )
        next_todo = "reliability_target_v8_endpoint_pair_counterfactual_repair_asset_packets"
    else:
        status = "h002_reliability_target_v8_current_repair_and_additional_mining_insufficient"
        decision = "Current labels are insufficient and additional exact endpoint-pair mining did not produce enough primary rows."
        next_todo = "revise_v8_target_scope_or_add_new_relation_families"

    summary = {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_target_repair_and_additional_mining_summary_v1",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "label_ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "target_independence_audit_summary": rel_path(audit_dir / "summary.json"),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "fills_new_labels": False,
            "posterior_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "hidden_metadata_used_for_mining_only": True,
        },
        "current_repair_summary": current_repair_summary,
        "train_counts": train_counts,
        "inventory_counts": inventory_counts,
        "selection_summary": selection_summary,
        "validation_errors": len(validation_errors),
        "decision": decision,
        "next_todo": next_todo,
    }

    inventory_csv = []
    for item in sorted(inventory, key=group_priority):
        inventory_csv.append(
            {
                **{key: value for key, value in item.items() if key not in {"predicate_counts", "family_counts", "queue_counts"}},
                "predicate_counts": json.dumps(item["predicate_counts"], sort_keys=True, ensure_ascii=False),
                "family_counts": json.dumps(item["family_counts"], sort_keys=True, ensure_ascii=False),
                "queue_counts": json.dumps(item["queue_counts"], sort_keys=True, ensure_ascii=False),
            }
        )

    write_json(output_paths["summary"], summary)
    write_csv(output_paths["current_repair_audit"], current_repair_summaries)
    write_jsonl(output_paths["current_repair_candidate_rows"], current_slice_rows)
    write_csv(output_paths["full_train_contrast_inventory"], inventory_csv)
    write_jsonl(output_paths["selected_primary_candidates"], selected)
    write_tsv(output_paths["selected_primary_label_sheet"], visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["asset_request_manifest"], asset_requests)
    write_jsonl(output_paths["future_proximity_preview_candidates"], proximity_preview)
    write_tsv(output_paths["future_proximity_preview_label_sheet"], proximity_visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"current_best_repair={summary['current_repair_summary']['best_repair_spec']}:{summary['current_repair_summary']['best_repair_balanced_rows']}")
    print(f"selected_primary_rows={summary['selection_summary']['selected_primary_rows']}")
    print(f"vertical_rows={summary['selection_summary']['vertical_direction_rows']} support_rows={summary['selection_summary']['support_pose_rows']}")
    print(f"asset_needed_primary_rows={summary['selection_summary']['asset_needed_primary_rows']}")
    print(f"future_proximity_preview_rows={summary['selection_summary']['future_proximity_preview_rows']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
