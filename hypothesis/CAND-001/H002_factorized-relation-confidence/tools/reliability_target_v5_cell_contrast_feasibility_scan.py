#!/usr/bin/env python3
"""Scan H002 v5 within-cell contrast feasibility."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION = RGA_ROOT / "reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested/summary.json"
DEFAULT_PACKET_MANIFEST = RGA_ROOT / "independent_asset_packets/packet_manifest.jsonl"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_feasibility_scan"

SELECTED_FAMILIES = {"support_contact", "relative_vertical"}
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
SUPPORT_SURFACES = {
    "armchair",
    "bed",
    "bench",
    "cabinet",
    "chair",
    "counter",
    "countertop",
    "desk",
    "kitchen cabinet",
    "shelf",
    "sofa",
    "stand",
    "stool",
    "table",
}

TARGET_PAIRS = 40
TARGET_ROWS = TARGET_PAIRS * 2
RECOMMENDED_PAIRS = 80
MIN_MIXED_CELLS = 10
MAX_SINGLE_CELL_SHARE = 0.20
PER_CELL_PAIR_CAP = 2
PER_SCAN_ROW_CAP = 6
PER_OBJECT_LABEL_ROW_CAP = 24
PER_FAMILY_ROW_CAP = 48

MATCHING_LEVELS = [
    {
        "name": "strict_predicate_subject_object_endpoint",
        "keys": ["predicate_label", "subject_label_norm", "object_label_norm", "endpoint_flag_pattern_hidden"],
        "description": "same predicate, visible subject/object labels, and endpoint pattern",
    },
    {
        "name": "family_subject_object_endpoint",
        "keys": ["predicate_family", "subject_label_norm", "object_label_norm", "endpoint_flag_pattern_hidden"],
        "description": "same family, visible subject/object labels, and endpoint pattern",
    },
    {
        "name": "subject_object_family_cell",
        "keys": ["subject_object_family_cell_hidden"],
        "description": "same subject/object/family cell",
    },
    {
        "name": "object_family_with_endpoint",
        "keys": ["predicate_family", "object_label_norm", "endpoint_flag_pattern_hidden"],
        "description": "object-family fallback with endpoint pattern",
    },
    {
        "name": "object_family_cell",
        "keys": ["predicate_family", "object_label_norm"],
        "description": "object-family fallback",
    },
    {
        "name": "endpoint_family_cell",
        "keys": ["predicate_family", "endpoint_flag_pattern_hidden"],
        "description": "endpoint/family fallback",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision", type=Path, default=DEFAULT_PATH_DECISION)
    parser.add_argument("--packet-manifest", type=Path, default=DEFAULT_PACKET_MANIFEST)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
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


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm_label(value: Any) -> str:
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


def packet_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("scan_id")),
        str(row.get("subject_id")),
        str(row.get("object_id")),
        str(row.get("predicate_label")),
    )


def physical_pair_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("scan_id")),
        str(row.get("subgraph_id") or row.get("scene_context_id")),
        str(row.get("subject_id")),
        str(row.get("object_id")),
    )


def packet_ready(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    return (
        row.get("packet_status") == "ready"
        and bool(row.get("multiview_packet"))
        and bool(row.get("pointcloud_or_mesh_packet"))
        and bool(row.get("contact_or_context_sheet"))
    )


def load_ready_packets(path: Path) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    packets: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in iter_jsonl(path):
        if packet_ready(row):
            packets[packet_key(row)] = row
    return packets


def endpoint_pattern(row: dict[str, Any]) -> str:
    subject = norm_label(row.get("subject_label"))
    obj = norm_label(row.get("object_label"))
    family = str(row.get("predicate_family"))
    return "|".join(
        [
            f"subject_room_surface={int(subject in HARD_ROOM_SURFACES)}",
            f"object_room_surface={int(obj in HARD_ROOM_SURFACES)}",
            f"subject_structural={int(subject in STRUCTURAL_CONTEXT)}",
            f"object_structural={int(obj in STRUCTURAL_CONTEXT)}",
            f"same_label={int(subject == obj)}",
            f"support_contact={int(family == 'support_contact')}",
            f"relative_vertical={int(family == 'relative_vertical')}",
        ]
    )


def informative_score(row: dict[str, Any]) -> int:
    subject = norm_label(row.get("subject_label"))
    obj = norm_label(row.get("object_label"))
    family = str(row.get("predicate_family"))
    predicate = str(row.get("predicate_label"))
    score = 0
    if subject not in HARD_ROOM_SURFACES:
        score += 1
    if obj not in HARD_ROOM_SURFACES:
        score += 1
    if subject not in STRUCTURAL_CONTEXT:
        score += 1
    if obj not in STRUCTURAL_CONTEXT:
        score += 1
    if subject != obj:
        score += 1
    if family == "support_contact":
        if obj in SUPPORT_SURFACES:
            score += 2
        if predicate in {"supported by", "standing on"}:
            score += 1
        if predicate == "lying on" and obj in HARD_ROOM_SURFACES:
            score -= 2
    if family == "relative_vertical":
        if subject not in STRUCTURAL_CONTEXT and obj not in STRUCTURAL_CONTEXT:
            score += 2
        if predicate in {"higher than", "lower than"}:
            score += 1
    return score


def room_surface_score(row: dict[str, Any]) -> int:
    subject = norm_label(row.get("subject_label"))
    obj = norm_label(row.get("object_label"))
    score = 0
    if subject in HARD_ROOM_SURFACES:
        score += 2
    if obj in HARD_ROOM_SURFACES:
        score += 2
    if subject in STRUCTURAL_CONTEXT:
        score += 1
    if obj in STRUCTURAL_CONTEXT:
        score += 1
    if subject == obj:
        score += 2
    return score


def label_match_family(row: dict[str, Any]) -> str:
    matched = [str(item).lower() for item in row.get("matched_predicates") or []]
    family = str(row.get("predicate_family"))
    if not matched:
        return "no_matched_predicate"
    if family == "support_contact" and any(item in {"standing on", "lying on", "supported by"} for item in matched):
        return "same_family_match"
    if family == "relative_vertical" and any(item in {"higher than", "lower than"} for item in matched):
        return "same_family_match"
    return "other_family_or_ontology_match"


def contrast_role(row: dict[str, Any], source_queue: str) -> str:
    geometry = str(row.get("geometry_status"))
    info = informative_score(row)
    room = room_surface_score(row)
    if source_queue == "LH" and geometry == "satisfied" and info >= 5 and room <= 1:
        return "likely_reliable_positive_proxy"
    if source_queue == "HL" and geometry in {"unsatisfied", "violated"}:
        return "geometry_contradiction_negative_proxy"
    if source_queue == "LH" and geometry == "satisfied" and room >= 3:
        return "trivial_satisfied_negative_proxy"
    return "uncertain_or_unmatched_proxy"


def normalize_row(row: dict[str, Any], source_queue: str, packet: dict[str, Any] | None) -> dict[str, Any]:
    subject_label_norm = norm_label(row.get("subject_label"))
    object_label_norm = norm_label(row.get("object_label"))
    endpoint = endpoint_pattern(row)
    normalized = {
        "prediction_id": row.get("prediction_id"),
        "source_id": row.get("source_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "scene_context_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "subject_label_norm": subject_label_norm,
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "object_label_norm": object_label_norm,
        "source_queue_hidden": source_queue,
        "queue_kind_hidden": source_queue,
        "rank_band_hidden": row.get("rank_band"),
        "semantic_rank_hidden": row.get("semantic_rank"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm"),
        "semantic_score_raw_hidden": row.get("semantic_score_raw"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "geometry_status_hidden": row.get("geometry_status"),
        "h001_verification_status_hidden": row.get("h001_verification_status"),
        "label_match_status_hidden": row.get("label_match_status"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket"),
        "machine_hint_hidden": row.get("machine_hint"),
        "matched_predicates_hidden": row.get("matched_predicates", []),
        "reason_codes_hidden": row.get("reason_codes", []),
        "endpoint_flag_pattern_hidden": endpoint,
        "informative_score_hidden": informative_score(row),
        "room_surface_score_hidden": room_surface_score(row),
        "label_match_family_hidden": label_match_family(row),
        "subject_object_family_cell_hidden": "|".join([subject_label_norm, object_label_norm, str(row.get("predicate_family"))]),
        "object_family_cell_hidden": "|".join([object_label_norm, str(row.get("predicate_family"))]),
        "endpoint_family_cell_hidden": "|".join([endpoint, str(row.get("predicate_family"))]),
    }
    normalized["contrast_role_hidden"] = contrast_role(row, source_queue)
    normalized["packet_ready"] = packet_ready(packet)
    normalized["packet_status"] = (packet or {}).get("packet_status", "asset_needed")
    normalized["multiview_packet"] = (packet or {}).get("multiview_packet", "")
    normalized["pointcloud_or_mesh_packet"] = (packet or {}).get("pointcloud_or_mesh_packet", "")
    normalized["contact_or_context_sheet"] = (packet or {}).get("contact_or_context_sheet", "")
    normalized["original_blind_review_id"] = (packet or {}).get("blind_review_id", "")
    return normalized


def load_rows(hl_queue: Path, lh_queue: Path, packets: dict[tuple[str, str, str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source_queue, path in [("HL", hl_queue), ("LH", lh_queue)]:
        for row in iter_jsonl(path):
            if row.get("predicate_family") not in SELECTED_FAMILIES:
                continue
            packet = packets.get(packet_key(row))
            rows.append(normalize_row(row, source_queue, packet))
    return rows


def stratum_key(row: dict[str, Any], keys: list[str]) -> tuple[str, ...]:
    return tuple(str(row.get(key, "")) for key in keys)


def positive_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row["contrast_role_hidden"] == "likely_reliable_positive_proxy"]


def negative_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row["contrast_role_hidden"] in {"geometry_contradiction_negative_proxy", "trivial_satisfied_negative_proxy"}
    ]


def negative_type_counts(rows: list[dict[str, Any]]) -> Counter[str]:
    return Counter(row["contrast_role_hidden"] for row in negative_rows(rows))


def build_level_inventory(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    inventory: list[dict[str, Any]] = []
    selected: dict[str, Any] | None = None
    for priority, level in enumerate(MATCHING_LEVELS, start=1):
        grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[stratum_key(row, level["keys"])].append(row)
        eligible_groups = 0
        eligible_rows = 0
        positive_capacity = 0
        negative_capacity = 0
        geometry_negative_capacity = 0
        trivial_negative_capacity = 0
        balanced_pair_capacity = 0
        packet_ready_rows = 0
        subject_object_cells = set()
        families = Counter()
        for group_rows in grouped.values():
            pos = positive_rows(group_rows)
            neg = negative_rows(group_rows)
            if not pos or not neg:
                continue
            neg_counts = negative_type_counts(group_rows)
            eligible_groups += 1
            eligible_rows += len(group_rows)
            positive_capacity += len(pos)
            negative_capacity += len(neg)
            geometry_negative_capacity += neg_counts["geometry_contradiction_negative_proxy"]
            trivial_negative_capacity += neg_counts["trivial_satisfied_negative_proxy"]
            balanced_pair_capacity += min(len(pos), len(neg))
            packet_ready_rows += sum(1 for row in group_rows if row["packet_ready"])
            subject_object_cells.update(str(row["subject_object_family_cell_hidden"]) for row in group_rows)
            families.update(str(row["predicate_family"]) for row in group_rows)
        row = {
            "matching_level": level["name"],
            "priority": priority,
            "keys": "|".join(level["keys"]),
            "description": level["description"],
            "total_groups": len(grouped),
            "eligible_groups": eligible_groups,
            "eligible_rows": eligible_rows,
            "positive_capacity": positive_capacity,
            "negative_capacity": negative_capacity,
            "geometry_negative_capacity": geometry_negative_capacity,
            "trivial_negative_capacity": trivial_negative_capacity,
            "balanced_pair_capacity": balanced_pair_capacity,
            "packet_ready_rows_in_eligible_groups": packet_ready_rows,
            "distinct_subject_object_family_cells": len(subject_object_cells),
            "support_contact_rows_in_eligible_groups": families["support_contact"],
            "relative_vertical_rows_in_eligible_groups": families["relative_vertical"],
            "meets_minimum_pair_count": balanced_pair_capacity >= TARGET_PAIRS,
            "meets_recommended_pair_count": balanced_pair_capacity >= RECOMMENDED_PAIRS,
            "meets_minimum_cell_count": eligible_groups >= MIN_MIXED_CELLS,
        }
        inventory.append(row)
        if (
            selected is None
            and row["meets_minimum_pair_count"]
            and row["meets_minimum_cell_count"]
            and row["support_contact_rows_in_eligible_groups"] > 0
            and row["relative_vertical_rows_in_eligible_groups"] > 0
        ):
            selected = {"level": level, "inventory": row}
    if selected is None:
        selected = {"level": MATCHING_LEVELS[-1], "inventory": inventory[-1]}
    return inventory, selected


def cell_inventory(rows: list[dict[str, Any]], level: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[stratum_key(row, level["keys"])].append(row)
    output: list[dict[str, Any]] = []
    for key, group_rows in grouped.items():
        roles = Counter(row["contrast_role_hidden"] for row in group_rows)
        pos = roles["likely_reliable_positive_proxy"]
        geometry_neg = roles["geometry_contradiction_negative_proxy"]
        trivial_neg = roles["trivial_satisfied_negative_proxy"]
        neg = geometry_neg + trivial_neg
        if not pos or not neg:
            continue
        families = Counter(str(row["predicate_family"]) for row in group_rows)
        rank_bands = Counter(str(row["rank_band_hidden"]) for row in group_rows)
        source_queues = Counter(str(row["source_queue_hidden"]) for row in group_rows)
        output.append(
            {
                "matching_level": level["name"],
                "cell_key": " || ".join(key),
                "rows": len(group_rows),
                "positive_proxy": pos,
                "negative_proxy_total": neg,
                "geometry_negative_proxy": geometry_neg,
                "trivial_negative_proxy": trivial_neg,
                "balanced_pair_capacity": min(pos, neg),
                "packet_ready": sum(1 for row in group_rows if row["packet_ready"]),
                "asset_needed": sum(1 for row in group_rows if not row["packet_ready"]),
                "support_contact": families["support_contact"],
                "relative_vertical": families["relative_vertical"],
                "rank_bands": json.dumps(dict(sorted(rank_bands.items())), sort_keys=True),
                "source_queues": json.dumps(dict(sorted(source_queues.items())), sort_keys=True),
                "top_scan_ids": json.dumps(dict(Counter(str(row["scan_id"]) for row in group_rows).most_common(5)), sort_keys=True),
            }
        )
    output.sort(
        key=lambda item: (
            -item["balanced_pair_capacity"],
            -item["negative_proxy_total"],
            -item["positive_proxy"],
            item["cell_key"],
        )
    )
    return output


def selection_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    role = row["contrast_role_hidden"]
    packet_penalty = 0 if row["packet_ready"] else 1
    semantic_rank = as_int(row.get("semantic_rank_hidden"))
    p_geom = as_float(row.get("p_geom_valid_hidden"), 0.5)
    info = int(row["informative_score_hidden"])
    room = int(row["room_surface_score_hidden"])
    if role == "likely_reliable_positive_proxy":
        quality = (-info, -p_geom, semantic_rank)
    elif role == "geometry_contradiction_negative_proxy":
        quality = (p_geom, -info, semantic_rank)
    else:
        quality = (-room, -p_geom, semantic_rank)
    return (packet_penalty, *quality, str(row["scan_id"]), str(row["prediction_id"]))


def select_preview_rows(rows: list[dict[str, Any]], level: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[stratum_key(row, level["keys"])].append(row)

    group_records = []
    for key, group_rows in grouped.items():
        pos = sorted(positive_rows(group_rows), key=selection_sort_key)
        neg = sorted(negative_rows(group_rows), key=selection_sort_key)
        if not pos or not neg:
            continue
        family = Counter(str(row["predicate_family"]) for row in group_rows).most_common(1)[0][0]
        group_records.append((min(len(pos), len(neg)), len(neg), len(pos), family, key, pos, neg))
    group_records.sort(key=lambda item: (-item[0], item[3], item[4]))

    selected: list[dict[str, Any]] = []
    cell_preview: list[dict[str, Any]] = []
    scan_counts: Counter[str] = Counter()
    object_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    cell_counts: Counter[str] = Counter()
    used_predictions: set[str] = set()
    used_physical_pairs: set[tuple[str, str, str, str]] = set()

    for capacity, _, _, _, key, pos_rows, neg_rows in group_records:
        pairs_for_cell = 0
        cell_key = " || ".join(key)
        for pos, neg in zip(pos_rows, neg_rows):
            if len(selected) >= TARGET_ROWS:
                break
            pair = [pos, neg]
            if any(str(row["prediction_id"]) in used_predictions for row in pair):
                continue
            if any(physical_pair_key(row) in used_physical_pairs for row in pair):
                continue
            if any(scan_counts[str(row["scan_id"])] >= PER_SCAN_ROW_CAP for row in pair):
                continue
            if any(object_counts[norm_label(row["object_label"])] >= PER_OBJECT_LABEL_ROW_CAP for row in pair):
                continue
            if any(family_counts[str(row["predicate_family"])] >= PER_FAMILY_ROW_CAP for row in pair):
                continue
            if pairs_for_cell >= PER_CELL_PAIR_CAP:
                break
            pair_id = f"v5cell_{len(selected)//2 + 1:04d}"
            for row, role in [(pos, "positive_proxy"), (neg, "negative_proxy")]:
                copied = dict(row)
                copied["cell_contrast_pair_id"] = pair_id
                copied["cell_contrast_role_hidden"] = role
                copied["cell_contrast_level_hidden"] = level["name"]
                copied["cell_contrast_key_hidden"] = cell_key
                copied["audit_selection_only"] = True
                copied["paper_evidence_allowed"] = False
                selected.append(copied)
                used_predictions.add(str(row["prediction_id"]))
                used_physical_pairs.add(physical_pair_key(row))
                scan_counts[str(row["scan_id"])] += 1
                object_counts[norm_label(row["object_label"])] += 1
                family_counts[str(row["predicate_family"])] += 1
                cell_counts[cell_key] += 1
            pairs_for_cell += 1
        if pairs_for_cell:
            cell_preview.append(
                {
                    "matching_level": level["name"],
                    "cell_key": cell_key,
                    "selected_pairs": pairs_for_cell,
                    "selected_rows": pairs_for_cell * 2,
                    "available_pair_capacity": capacity,
                }
            )
        if len(selected) >= TARGET_ROWS:
            break
    return selected, cell_preview


def asset_request_rows(selected: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for row in selected:
        if row["packet_ready"]:
            continue
        rows.append(
            {
                "prediction_id": row["prediction_id"],
                "scan_id": row["scan_id"],
                "scene_context_id": row["scene_context_id"],
                "subject_id": row["subject_id"],
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "predicate_family": row["predicate_family"],
                "object_id": row["object_id"],
                "object_label": row["object_label"],
                "cell_contrast_pair_id": row["cell_contrast_pair_id"],
                "cell_contrast_role_hidden": row["cell_contrast_role_hidden"],
                "cell_contrast_level_hidden": row["cell_contrast_level_hidden"],
                "cell_contrast_key_hidden": row["cell_contrast_key_hidden"],
                "asset_request_reason": "v5_cell_contrast_feasibility_selected_row_needs_multiview_pointcloud_context_packet",
            }
        )
    return rows


def selection_summary(selected: list[dict[str, Any]], selected_cells: list[dict[str, Any]]) -> dict[str, Any]:
    cell_counts = Counter(str(row["cell_contrast_key_hidden"]) for row in selected)
    family_counts = Counter(str(row["predicate_family"]) for row in selected)
    role_counts = Counter(str(row["cell_contrast_role_hidden"]) for row in selected)
    source_counts = Counter(str(row["source_queue_hidden"]) for row in selected)
    rank_counts = Counter(str(row["rank_band_hidden"]) for row in selected)
    max_cell_rows = max(cell_counts.values()) if cell_counts else 0
    rows = len(selected)
    return {
        "selected_rows": rows,
        "selected_pairs": rows // 2,
        "selected_cells": len(cell_counts),
        "selected_cell_preview_rows": len(selected_cells),
        "max_cell_rows": max_cell_rows,
        "max_cell_share": max_cell_rows / rows if rows else 0.0,
        "packet_ready_rows": sum(1 for row in selected if row["packet_ready"]),
        "asset_needed_rows": sum(1 for row in selected if not row["packet_ready"]),
        "family_counts": dict(sorted(family_counts.items())),
        "role_counts": dict(sorted(role_counts.items())),
        "source_queue_counts": dict(sorted(source_counts.items())),
        "rank_band_counts": dict(sorted(rank_counts.items())),
        "unique_scans": len({str(row["scan_id"]) for row in selected}),
        "unique_physical_pairs": len({physical_pair_key(row) for row in selected}),
    }


def feasibility_flags(level_inventory: dict[str, Any], selected_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "has_minimum_capacity": level_inventory["balanced_pair_capacity"] >= TARGET_PAIRS,
        "has_recommended_capacity": level_inventory["balanced_pair_capacity"] >= RECOMMENDED_PAIRS,
        "has_minimum_mixed_cells": level_inventory["eligible_groups"] >= MIN_MIXED_CELLS,
        "selected_preview_has_target_rows": selected_summary["selected_rows"] >= TARGET_ROWS,
        "selected_preview_has_target_pairs": selected_summary["selected_pairs"] >= TARGET_PAIRS,
        "selected_preview_has_minimum_cells": selected_summary["selected_cells"] >= MIN_MIXED_CELLS,
        "single_cell_share_ok": selected_summary["max_cell_share"] <= MAX_SINGLE_CELL_SHARE,
        "both_families_represented": all(
            selected_summary["family_counts"].get(family, 0) > 0 for family in sorted(SELECTED_FAMILIES)
        ),
        "asset_path_explicit": True,
    }


def build_contract(selected_level: dict[str, Any], selected_inventory: dict[str, Any], flags: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v5_cell_contrast_feasibility_contract_v1",
        "selected_matching_level": selected_level["name"],
        "selected_matching_keys": selected_level["keys"],
        "target_pairs_for_next_label_round": TARGET_PAIRS,
        "target_rows_for_next_label_round": TARGET_ROWS,
        "selected_level_inventory": selected_inventory,
        "feasibility_flags": flags,
        "next_label_round_allowed": all(flags.values()),
        "label_target_after_review": "relation_reliability_v5_binary_target",
        "positive_negative_source": (
            "cell contrast roles are sampling proxies only; final reliability labels must come from visible packet review"
        ),
        "forbidden_as_model_input": [
            "cell_contrast_role_hidden",
            "cell_contrast_pair_id",
            "cell_contrast_level_hidden",
            "cell_contrast_key_hidden",
            "queue_kind_hidden",
            "source_queue_hidden",
            "rank_band_hidden",
            "geometry_status_hidden",
            "label_match_status_hidden",
            "label_geometry_bucket_hidden",
            "p_geom_valid_hidden",
            "semantic_rank_hidden",
            "semantic_score_norm_hidden",
            "asset_packet_paths",
            "multi_view_as_model_input",
        ],
        "posterior_reopen_gate_after_labels": [
            "relation reliability binary target has at least 20 positives and 20 negatives",
            "subject_object_family_cell balanced slice is nonempty and diagnostic-ready",
            "endpoint/object and visible object-label risk are not sufficient to predict the target",
            "rank band, source queue, geometry status, and packet source are controlled or audited",
            "validation/test usage remains false",
        ],
        "stop_rule": (
            "If selected feasibility flags fail or v5 labels still fail target independence, freeze H002 as RGA "
            "diagnostic/decomposition rather than forcing posterior smoke."
        ),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Reliability Target V5 Cell Contrast Feasibility Scan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only feasibility scan.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- H001 artifacts are not modified.",
        "- Multi-view remains audit/label evidence, not model input.",
        "- Cell contrast roles are sampling proxies only, not target labels.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Matching Level Inventory",
        "",
        "| Level | Eligible Groups | Pair Capacity | Pos | Neg | Geometry Neg | Trivial Neg | Meets Minimum |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in summary["matching_level_inventory"]:
        lines.append(
            f"| `{row['matching_level']}` | {row['eligible_groups']} | {row['balanced_pair_capacity']} | "
            f"{row['positive_capacity']} | {row['negative_capacity']} | {row['geometry_negative_capacity']} | "
            f"{row['trivial_negative_capacity']} | `{row['meets_minimum_pair_count']}` |"
        )
    preview = summary["preview_selection"]
    flags = summary["feasibility_flags"]
    lines.extend(
        [
            "",
            "## Selected Feasibility Preview",
            "",
            f"- selected level: `{summary['selected_matching_level']}`",
            f"- selected keys: `{', '.join(summary['selected_matching_keys'])}`",
            f"- selected rows: `{preview['selected_rows']}`",
            f"- selected pairs: `{preview['selected_pairs']}`",
            f"- selected mixed cells: `{preview['selected_cells']}`",
            f"- max single-cell share: `{preview['max_cell_share']:.4f}`",
            f"- packet-ready rows: `{preview['packet_ready_rows']}`",
            f"- asset-needed rows: `{preview['asset_needed_rows']}`",
            f"- family counts: `{json.dumps(preview['family_counts'], sort_keys=True)}`",
            "",
            "## Feasibility Flags",
            "",
            "| Flag | Value |",
            "| --- | --- |",
        ]
    )
    for key, value in flags.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- V4 failed because exact subject/object/family target control was empty after labeling.",
            "- Full train-only pool still has enough within-cell proxy capacity for a stricter v5 label round.",
            "- This does not open posterior smoke. It only justifies a v5 candidate/asset/label-readiness path.",
            "- Hidden cell contrast roles and construction metadata remain audit-only and forbidden as posterior inputs.",
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

    path_decision = read_json(args.path_decision)
    packets = load_ready_packets(args.packet_manifest)
    rows = load_rows(args.hl_queue, args.lh_queue, packets)
    level_inventory, selected_bundle = build_level_inventory(rows)
    selected_level = selected_bundle["level"]
    selected_level_inventory = selected_bundle["inventory"]
    cells = cell_inventory(rows, selected_level)
    selected_preview, selected_cell_preview = select_preview_rows(rows, selected_level)
    asset_requests = asset_request_rows(selected_preview)
    preview_summary = selection_summary(selected_preview, selected_cell_preview)
    flags = feasibility_flags(selected_level_inventory, preview_summary)
    contract = build_contract(selected_level, selected_level_inventory, flags)

    status = (
        "h002_reliability_target_v5_cell_contrast_feasibility_ready_for_candidate_mining"
        if contract["next_label_round_allowed"]
        else "h002_reliability_target_v5_cell_contrast_feasibility_blocked"
    )
    next_todo = (
        "reliability_target_v5_cell_contrast_candidate_mining"
        if contract["next_label_round_allowed"]
        else "h002_rga_diagnostic_framework_freeze"
    )
    decision = (
        "Full train-only support/vertical pool has enough within-cell proxy capacity for a stricter v5 label round. "
        "Proceed to v5 candidate mining and asset planning, but keep posterior smoke blocked until labels are filled, "
        "ingested, and target-independence audit passes."
        if contract["next_label_round_allowed"]
        else (
            "Full train-only support/vertical pool does not provide enough within-cell proxy capacity. Freeze H002 as "
            "an RGA diagnostic/decomposition framework rather than forcing posterior smoke."
        )
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "matching_level_inventory": output_dir / "matching_level_inventory.csv",
        "cell_inventory": output_dir / "cell_inventory.csv",
        "selected_cell_preview": output_dir / "selected_cell_preview.csv",
        "seed_preview_internal": output_dir / "seed_preview_internal.jsonl",
        "asset_request_preview": output_dir / "asset_request_preview.jsonl",
        "feasibility_contract": output_dir / "feasibility_contract.json",
    }

    role_counts = Counter(row["contrast_role_hidden"] for row in rows)
    family_counts = Counter(str(row["predicate_family"]) for row in rows)
    summary = {
        "schema_version": "h002_reliability_target_v5_cell_contrast_feasibility_scan_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": decision,
        "path_decision_status": path_decision.get("status"),
        "path_decision_selected": path_decision.get("selected_path"),
        "input_paths": {
            "path_decision": rel_path(args.path_decision),
            "packet_manifest": rel_path(args.packet_manifest),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "labels_filled": False,
            "posterior_trained": False,
            "posterior_smoke_allowed": False,
            "multi_view_as_model_input": False,
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
        },
        "inventory": {
            "total_support_vertical_rows": len(rows),
            "role_counts": dict(sorted(role_counts.items())),
            "family_counts": dict(sorted(family_counts.items())),
            "ready_packet_keys": len(packets),
        },
        "matching_level_inventory": level_inventory,
        "selected_matching_level": selected_level["name"],
        "selected_matching_keys": selected_level["keys"],
        "selected_level_inventory": selected_level_inventory,
        "selected_cell_count": len(cells),
        "preview_selection": preview_summary,
        "feasibility_flags": flags,
        "feasibility_contract": contract,
        "next_todo": next_todo,
    }

    write_json(output_paths["summary"], summary)
    write_csv(output_paths["matching_level_inventory"], level_inventory)
    write_csv(output_paths["cell_inventory"], cells)
    write_csv(output_paths["selected_cell_preview"], selected_cell_preview)
    write_jsonl(output_paths["seed_preview_internal"], selected_preview)
    write_jsonl(output_paths["asset_request_preview"], asset_requests)
    write_json(output_paths["feasibility_contract"], contract)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    preview = summary["preview_selection"]
    print(
        "status={status} selected_level={level} rows={rows} pairs={pairs} cells={cells} "
        "max_cell_share={max_share:.4f} packet_ready={packet_ready} asset_needed={asset_needed} "
        "posterior_allowed={posterior_allowed} validation_used={validation_used} test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            level=summary["selected_matching_level"],
            rows=preview["selected_rows"],
            pairs=preview["selected_pairs"],
            cells=preview["selected_cells"],
            max_share=preview["max_cell_share"],
            packet_ready=preview["packet_ready_rows"],
            asset_needed=preview["asset_needed_rows"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
