#!/usr/bin/env python3
"""Plan H002 reliability target v4 matched-contrast sampling."""

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

DEFAULT_PATH_DECISION = RGA_ROOT / "reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested/summary.json"
DEFAULT_PACKET_MANIFEST = RGA_ROOT / "independent_asset_packets/packet_manifest.jsonl"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v4_matched_contrast_plan"

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

RECOMMENDED_PAIR_COUNT = 80
MINIMUM_PAIR_COUNT = 40
PER_STRATUM_PAIR_CAP = 4
PER_SCAN_ROW_CAP = 6
PER_OBJECT_LABEL_ROW_CAP = 24
PER_FAMILY_ROW_CAP = 90

MATCHING_LEVELS = [
    {
        "name": "strict_predicate_object_rank",
        "keys": ["predicate_label", "endpoint_flag_pattern_hidden", "object_family_cell_hidden", "rank_band_hidden"],
        "rank_exact": True,
    },
    {
        "name": "family_object_rank",
        "keys": ["predicate_family", "endpoint_flag_pattern_hidden", "object_family_cell_hidden", "rank_band_hidden"],
        "rank_exact": True,
    },
    {
        "name": "family_endpoint_rank",
        "keys": ["predicate_family", "endpoint_flag_pattern_hidden", "rank_band_hidden"],
        "rank_exact": True,
    },
    {
        "name": "predicate_object_rank_controlled",
        "keys": ["predicate_label", "endpoint_flag_pattern_hidden", "object_family_cell_hidden"],
        "rank_exact": False,
    },
    {
        "name": "family_object_rank_controlled",
        "keys": ["predicate_family", "endpoint_flag_pattern_hidden", "object_family_cell_hidden"],
        "rank_exact": False,
    },
    {
        "name": "family_endpoint_rank_controlled",
        "keys": ["predicate_family", "endpoint_flag_pattern_hidden"],
        "rank_exact": False,
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
    endpoint = endpoint_pattern(row)
    normalized = {
        "prediction_id": row.get("prediction_id"),
        "source_id": row.get("source_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "scene_context_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
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
        "subject_object_family_cell_hidden": "|".join(
            [str(row.get("subject_label")), str(row.get("object_label")), str(row.get("predicate_family"))]
        ),
        "object_family_cell_hidden": "|".join([norm_label(row.get("object_label")), str(row.get("predicate_family"))]),
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
        balanced_pair_capacity = 0
        packet_ready_rows = 0
        for group_rows in grouped.values():
            pos = positive_rows(group_rows)
            neg = negative_rows(group_rows)
            if not pos or not neg:
                continue
            eligible_groups += 1
            eligible_rows += len(group_rows)
            positive_capacity += len(pos)
            negative_capacity += len(neg)
            balanced_pair_capacity += min(len(pos), len(neg))
            packet_ready_rows += sum(1 for row in group_rows if row["packet_ready"])
        row = {
            "matching_level": level["name"],
            "priority": priority,
            "keys": "|".join(level["keys"]),
            "rank_exact": bool(level["rank_exact"]),
            "total_groups": len(grouped),
            "eligible_groups": eligible_groups,
            "eligible_rows": eligible_rows,
            "positive_capacity": positive_capacity,
            "negative_capacity": negative_capacity,
            "balanced_pair_capacity": balanced_pair_capacity,
            "packet_ready_rows_in_eligible_groups": packet_ready_rows,
            "meets_minimum_pair_count": balanced_pair_capacity >= MINIMUM_PAIR_COUNT,
            "meets_recommended_pair_count": balanced_pair_capacity >= RECOMMENDED_PAIR_COUNT,
        }
        inventory.append(row)
        if selected is None and row["meets_recommended_pair_count"]:
            selected = {"level": level, "inventory": row}
    if selected is None:
        for row, level in zip(inventory, MATCHING_LEVELS):
            if row["meets_minimum_pair_count"]:
                selected = {"level": level, "inventory": row}
                break
    if selected is None:
        selected = {"level": MATCHING_LEVELS[-1], "inventory": inventory[-1]}
    return inventory, selected


def stratum_inventory(rows: list[dict[str, Any]], level: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[stratum_key(row, level["keys"])].append(row)
    output: list[dict[str, Any]] = []
    for key, group_rows in grouped.items():
        roles = Counter(row["contrast_role_hidden"] for row in group_rows)
        pos = roles["likely_reliable_positive_proxy"]
        neg = roles["geometry_contradiction_negative_proxy"] + roles["trivial_satisfied_negative_proxy"]
        if not pos or not neg:
            continue
        families = Counter(str(row["predicate_family"]) for row in group_rows)
        rank_bands = Counter(str(row["rank_band_hidden"]) for row in group_rows)
        output.append(
            {
                "matching_level": level["name"],
                "stratum_key": " || ".join(key),
                "rows": len(group_rows),
                "positive_proxy": pos,
                "geometry_negative_proxy": roles["geometry_contradiction_negative_proxy"],
                "trivial_negative_proxy": roles["trivial_satisfied_negative_proxy"],
                "negative_proxy_total": neg,
                "balanced_pair_capacity": min(pos, neg),
                "packet_ready": sum(1 for row in group_rows if row["packet_ready"]),
                "asset_needed": sum(1 for row in group_rows if not row["packet_ready"]),
                "support_contact": families["support_contact"],
                "relative_vertical": families["relative_vertical"],
                "rank_bands": json.dumps(dict(sorted(rank_bands.items())), sort_keys=True),
                "top_object_labels": json.dumps(
                    dict(Counter(norm_label(row["object_label"]) for row in group_rows).most_common(8)),
                    sort_keys=True,
                ),
            }
        )
    output.sort(key=lambda item: (-item["balanced_pair_capacity"], -item["negative_proxy_total"], -item["positive_proxy"], item["stratum_key"]))
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
        group_records.append((min(len(pos), len(neg)), len(neg), len(pos), key, pos, neg))
    group_records.sort(key=lambda item: (-item[0], -item[1], -item[2], item[3]))

    selected: list[dict[str, Any]] = []
    stratum_preview: list[dict[str, Any]] = []
    scan_counts: Counter[str] = Counter()
    object_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    used_predictions: set[str] = set()
    target_rows = RECOMMENDED_PAIR_COUNT * 2

    for capacity, _, _, key, pos_rows, neg_rows in group_records:
        pairs_for_stratum = 0
        for pos, neg in zip(pos_rows, neg_rows):
            if len(selected) >= target_rows:
                break
            pair = [pos, neg]
            if any(str(row["prediction_id"]) in used_predictions for row in pair):
                continue
            if any(scan_counts[str(row["scan_id"])] >= PER_SCAN_ROW_CAP for row in pair):
                continue
            if any(object_counts[norm_label(row["object_label"])] >= PER_OBJECT_LABEL_ROW_CAP for row in pair):
                continue
            if any(family_counts[str(row["predicate_family"])] >= PER_FAMILY_ROW_CAP for row in pair):
                continue
            if pairs_for_stratum >= PER_STRATUM_PAIR_CAP:
                break
            pair_id = f"v4pair_{len(selected)//2 + 1:04d}"
            for row, role in [(pos, "positive_proxy"), (neg, "negative_proxy")]:
                copied = dict(row)
                copied["matched_contrast_pair_id"] = pair_id
                copied["matched_contrast_role_hidden"] = role
                copied["matched_contrast_level_hidden"] = level["name"]
                copied["matched_contrast_stratum_hidden"] = " || ".join(key)
                copied["audit_selection_only"] = True
                copied["paper_evidence_allowed"] = False
                selected.append(copied)
                used_predictions.add(str(row["prediction_id"]))
                scan_counts[str(row["scan_id"])] += 1
                object_counts[norm_label(row["object_label"])] += 1
                family_counts[str(row["predicate_family"])] += 1
            pairs_for_stratum += 1
        if pairs_for_stratum:
            stratum_preview.append(
                {
                    "matching_level": level["name"],
                    "stratum_key": " || ".join(key),
                    "selected_pairs": pairs_for_stratum,
                    "available_pair_capacity": capacity,
                    "selected_rows": pairs_for_stratum * 2,
                }
            )
        if len(selected) >= target_rows:
            break
    return selected, stratum_preview


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
                "matched_contrast_pair_id": row["matched_contrast_pair_id"],
                "matched_contrast_role_hidden": row["matched_contrast_role_hidden"],
                "matched_contrast_level_hidden": row["matched_contrast_level_hidden"],
                "matched_contrast_stratum_hidden": row["matched_contrast_stratum_hidden"],
                "asset_request_reason": "matched_contrast_v4_seed_needs_multiview_pointcloud_context_packet",
            }
        )
    return rows


def build_sampling_contract(selected_level: dict[str, Any], selected_inventory: dict[str, Any]) -> dict[str, Any]:
    rank_policy = "exact_match" if selected_level["rank_exact"] else "post_selection_quota_and_audit_control"
    return {
        "schema_version": "h002_reliability_target_v4_matched_contrast_sampling_contract_v1",
        "selected_matching_level": selected_level["name"],
        "selected_matching_keys": selected_level["keys"],
        "rank_control_policy": rank_policy,
        "rank_exact_matching_feasible": bool(selected_level["rank_exact"]),
        "selected_level_inventory": selected_inventory,
        "target_pairs": RECOMMENDED_PAIR_COUNT,
        "minimum_pairs": MINIMUM_PAIR_COUNT,
        "target_rows": RECOMMENDED_PAIR_COUNT * 2,
        "label_target_after_review": "relation_reliability_v4_binary_target",
        "positive_negative_source": (
            "contrast roles are sampling proxies only; final reliability labels must come from visible packet review"
        ),
        "forbidden_as_model_input": [
            "contrast_role_hidden",
            "matched_contrast_pair_id",
            "matched_contrast_level_hidden",
            "matched_contrast_stratum_hidden",
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
        "posterior_reopen_gate": [
            "relation reliability binary target has at least 20 positives and 20 negatives",
            "strict or explicitly defensible diagnostic controlled slice exists",
            "anchor/category shortcut risk is zero on selected slice",
            "endpoint/object and visible object-label shortcuts are not sufficient to explain target",
            "rank-band and geometry-status controls do not dominate selected slice",
            "validation/test usage remains false",
        ],
        "fallback_stop_rule": (
            "If v4 matched contrast cannot create an independent target, freeze H002 as RGA diagnostic/decomposition "
            "instead of forcing posterior smoke."
        ),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Reliability Target V4 Matched Contrast Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only planning artifact.",
        "- No validation/test rows are used.",
        "- No labels are filled.",
        "- No posterior is trained.",
        "- H001 artifacts are not modified.",
        "- Multi-view remains audit/label evidence, not model input.",
        "- Contrast roles are sampling proxies only, not target labels.",
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
        "| Level | Rank Exact | Eligible Groups | Pair Capacity | Meets Recommended |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in summary["matching_level_inventory"]:
        lines.append(
            f"| `{row['matching_level']}` | `{row['rank_exact']}` | {row['eligible_groups']} | "
            f"{row['balanced_pair_capacity']} | `{row['meets_recommended_pair_count']}` |"
        )
    lines.extend(
        [
            "",
            "## Selected Contract",
            "",
            f"- selected matching level: `{summary['selected_matching_level']}`",
            f"- selected matching keys: `{', '.join(summary['selected_matching_keys'])}`",
            f"- rank policy: `{summary['rank_control_policy']}`",
            f"- preview rows: `{summary['preview_selection']['selected_rows']}`",
            f"- preview pairs: `{summary['preview_selection']['selected_pairs']}`",
            f"- preview packet-ready rows: `{summary['preview_selection']['packet_ready_rows']}`",
            f"- preview asset-needed rows: `{summary['preview_selection']['asset_needed_rows']}`",
            "",
            "## Interpretation",
            "",
            "- Exact rank-band matching is too strict for the current source: strict rank-matched levels have no usable contrast capacity.",
            "- The feasible path is object/endpoint-family matching with rank handled by quota and post-label audit controls.",
            "- This is still a stricter construction than v3 because positives and negatives are drawn from the same endpoint/object stratum rather than from separate anchor buckets.",
            "- Posterior remains blocked until v4 labels are filled, ingested, and target-independence audit passes.",
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
    level_inventory, selected_level_bundle = build_level_inventory(rows)
    selected_level = selected_level_bundle["level"]
    selected_level_inventory = selected_level_bundle["inventory"]
    strata = stratum_inventory(rows, selected_level)
    selected_preview, selected_strata_preview = select_preview_rows(rows, selected_level)
    asset_requests = asset_request_rows(selected_preview)
    contract = build_sampling_contract(selected_level, selected_level_inventory)

    role_counts = Counter(row["contrast_role_hidden"] for row in rows)
    family_counts = Counter(str(row["predicate_family"]) for row in selected_preview)
    rank_counts = Counter(str(row["rank_band_hidden"]) for row in selected_preview)
    preview_role_counts = Counter(row["matched_contrast_role_hidden"] for row in selected_preview)
    packet_ready_count = sum(1 for row in selected_preview if row["packet_ready"])

    status = (
        "h002_reliability_target_v4_matched_contrast_plan_ready_with_asset_requests"
        if asset_requests
        else "h002_reliability_target_v4_matched_contrast_plan_ready_packet_complete"
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "matching_level_inventory": output_dir / "matching_level_inventory.csv",
        "selected_strata_inventory": output_dir / "selected_strata_inventory.csv",
        "selected_strata_preview": output_dir / "selected_strata_preview.csv",
        "seed_preview_internal": output_dir / "seed_preview_internal.jsonl",
        "asset_request_preview": output_dir / "asset_request_preview.jsonl",
        "sampling_contract": output_dir / "sampling_contract.json",
    }

    summary = {
        "schema_version": "h002_reliability_target_v4_matched_contrast_plan_summary_v1",
        "status": status,
        "created_at": created_at,
        "decision": (
            "Plan v4 matched-contrast sampling. Exact rank-band matching is infeasible in the current train queue, "
            "so use family/object/endpoint matching with rank-band quota and post-label shortcut audit controls."
        ),
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
            "ready_packet_keys": len(packets),
        },
        "matching_level_inventory": level_inventory,
        "selected_matching_level": selected_level["name"],
        "selected_matching_keys": selected_level["keys"],
        "rank_control_policy": contract["rank_control_policy"],
        "selected_level_inventory": selected_level_inventory,
        "selected_strata_count": len(strata),
        "preview_selection": {
            "selected_rows": len(selected_preview),
            "selected_pairs": len(selected_preview) // 2,
            "packet_ready_rows": packet_ready_count,
            "asset_needed_rows": len(selected_preview) - packet_ready_count,
            "role_counts": dict(sorted(preview_role_counts.items())),
            "family_counts": dict(sorted(family_counts.items())),
            "rank_band_counts": dict(sorted(rank_counts.items())),
            "unique_scans": len({str(row["scan_id"]) for row in selected_preview}),
            "unique_physical_pairs": len({physical_pair_key(row) for row in selected_preview}),
        },
        "sampling_contract": contract,
        "next_todo": "reliability_target_v4_matched_contrast_candidate_mining",
    }

    write_json(output_paths["summary"], summary)
    write_csv(output_paths["matching_level_inventory"], level_inventory)
    write_csv(output_paths["selected_strata_inventory"], strata)
    write_csv(output_paths["selected_strata_preview"], selected_strata_preview)
    write_jsonl(output_paths["seed_preview_internal"], selected_preview)
    write_jsonl(output_paths["asset_request_preview"], asset_requests)
    write_json(output_paths["sampling_contract"], contract)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    preview = summary["preview_selection"]
    print(
        "status={status} selected_level={level} rows={rows} pairs={pairs} "
        "packet_ready={packet_ready} asset_needed={asset_needed} posterior_allowed={posterior_allowed} "
        "validation_used={validation_used} test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            level=summary["selected_matching_level"],
            rows=preview["selected_rows"],
            pairs=preview["selected_pairs"],
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
