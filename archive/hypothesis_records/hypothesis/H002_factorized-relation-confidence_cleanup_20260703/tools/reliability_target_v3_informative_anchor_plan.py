#!/usr/bin/env python3
"""Plan informative-anchor sampling for H002 reliability target v3."""

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

DEFAULT_PATH_DECISION = RGA_ROOT / "reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested/summary.json"
DEFAULT_PACKET_MANIFEST = RGA_ROOT / "independent_asset_packets/packet_manifest.jsonl"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_informative_anchor_plan"

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

TARGET_ROWS_BY_CATEGORY = {
    "informative_reliable_positive_proxy": 40,
    "geometry_contradiction_negative_proxy": 40,
    "trivial_room_surface_negative_proxy": 40,
    "uncertain_or_ontology_negative_proxy": 40,
}

PER_CATEGORY_FAMILY_CAP = 24
PER_SCAN_CAP = 4
PER_PHYSICAL_PAIR_CAP = 1


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


def packet_ready(row: dict[str, Any]) -> bool:
    return (
        row.get("packet_status") == "ready"
        and bool(row.get("multiview_packet"))
        and bool(row.get("pointcloud_or_mesh_packet"))
        and bool(row.get("contact_or_context_sheet"))
    )


def load_ready_packets(path: Path) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    packets = {}
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


def anchor_category(row: dict[str, Any]) -> str:
    queue = str(row.get("queue_kind"))
    geometry = str(row.get("geometry_status"))
    info = informative_score(row)
    room = room_surface_score(row)
    if queue == "LH" and geometry == "satisfied" and info >= 5 and room <= 1:
        return "informative_reliable_positive_proxy"
    if queue == "HL" and geometry in {"unsatisfied", "violated"}:
        return "geometry_contradiction_negative_proxy"
    if queue == "LH" and geometry == "satisfied" and room >= 3:
        return "trivial_room_surface_negative_proxy"
    return "uncertain_or_ontology_negative_proxy"


def normalize_row(row: dict[str, Any], source_queue: str, packet: dict[str, Any] | None) -> dict[str, Any]:
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
        "queue_kind_hidden": source_queue,
        "source_queue_hidden": source_queue,
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
        "endpoint_flag_pattern_hidden": endpoint_pattern(row),
        "informative_anchor_score_hidden": informative_score(row),
        "room_surface_score_hidden": room_surface_score(row),
        "label_match_family_hidden": label_match_family(row),
        "subject_object_family_cell_hidden": "|".join(
            [str(row.get("subject_label")), str(row.get("object_label")), str(row.get("predicate_family"))]
        ),
        "object_family_cell_hidden": "|".join([str(row.get("object_label")), str(row.get("predicate_family"))]),
        "endpoint_family_cell_hidden": "|".join([endpoint_pattern(row), str(row.get("predicate_family"))]),
    }
    normalized["anchor_category_hidden"] = anchor_category({**row, "queue_kind": source_queue})
    normalized["packet_ready"] = packet_ready(packet or {})
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


def inventory_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(str(row["anchor_category_hidden"]), str(row["predicate_family"]))].append(row)
    output = []
    for (category, family), group_rows in sorted(grouped.items()):
        output.append(
            {
                "anchor_category": category,
                "predicate_family": family,
                "rows": len(group_rows),
                "packet_ready": sum(1 for row in group_rows if row["packet_ready"]),
                "asset_needed": sum(1 for row in group_rows if not row["packet_ready"]),
                "unique_scans": len({str(row["scan_id"]) for row in group_rows}),
                "unique_physical_pairs": len({physical_pair_key(row) for row in group_rows}),
                "top_object_labels": json.dumps(
                    dict(Counter(norm_label(row["object_label"]) for row in group_rows).most_common(8)),
                    sort_keys=True,
                ),
                "top_subject_labels": json.dumps(
                    dict(Counter(norm_label(row["subject_label"]) for row in group_rows).most_common(8)),
                    sort_keys=True,
                ),
            }
        )
    return output


def cell_inventory(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for cell_type, key in [
            ("subject_object_family", row["subject_object_family_cell_hidden"]),
            ("object_family", row["object_family_cell_hidden"]),
            ("endpoint_family", row["endpoint_family_cell_hidden"]),
        ]:
            grouped[(str(row["anchor_category_hidden"]), cell_type, str(key))].append(row)
    output = []
    for (category, cell_type, key), group_rows in grouped.items():
        families = Counter(str(row["predicate_family"]) for row in group_rows)
        output.append(
            {
                "anchor_category": category,
                "cell_type": cell_type,
                "cell_key": key,
                "rows": len(group_rows),
                "packet_ready": sum(1 for row in group_rows if row["packet_ready"]),
                "asset_needed": sum(1 for row in group_rows if not row["packet_ready"]),
                "unique_scans": len({str(row["scan_id"]) for row in group_rows}),
                "unique_physical_pairs": len({physical_pair_key(row) for row in group_rows}),
                "support_contact": families.get("support_contact", 0),
                "relative_vertical": families.get("relative_vertical", 0),
            }
        )
    output.sort(key=lambda item: (-item["packet_ready"], -item["rows"], item["anchor_category"], item["cell_type"], item["cell_key"]))
    return output


def selection_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    category = str(row["anchor_category_hidden"])
    packet_penalty = 0 if row["packet_ready"] else 1
    semantic_rank = as_int(row.get("semantic_rank_hidden"))
    p_geom = as_float(row.get("p_geom_valid_hidden"), 0.5)
    info = int(row["informative_anchor_score_hidden"])
    room = int(row["room_surface_score_hidden"])
    if category == "informative_reliable_positive_proxy":
        quality = (-info, -p_geom, semantic_rank)
    elif category == "geometry_contradiction_negative_proxy":
        quality = (p_geom, -info, semantic_rank)
    elif category == "trivial_room_surface_negative_proxy":
        quality = (-room, -p_geom, semantic_rank)
    else:
        quality = (-info, semantic_rank)
    return (packet_penalty, *quality, str(row["scan_id"]), str(row["prediction_id"]))


def select_seed_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    status_rows: list[dict[str, Any]] = []
    used_predictions: set[str] = set()
    scan_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str, str, str]] = Counter()
    category_family_counts: Counter[tuple[str, str]] = Counter()

    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_category[str(row["anchor_category_hidden"])].append(row)

    for category, target_rows in TARGET_ROWS_BY_CATEGORY.items():
        candidates = sorted(by_category.get(category, []), key=selection_sort_key)
        selected_for_category = 0
        passes = [
            {"scan_cap": PER_SCAN_CAP, "pair_cap": PER_PHYSICAL_PAIR_CAP, "family_cap": PER_CATEGORY_FAMILY_CAP, "name": "strict_diverse"},
            {"scan_cap": PER_SCAN_CAP * 2, "pair_cap": PER_PHYSICAL_PAIR_CAP, "family_cap": target_rows, "name": "relaxed_family"},
            {"scan_cap": 999999, "pair_cap": 2, "family_cap": target_rows, "name": "relaxed_diversity"},
        ]
        for selection_pass in passes:
            if selected_for_category >= target_rows:
                break
            for row in candidates:
                if selected_for_category >= target_rows:
                    break
                prediction_id = str(row["prediction_id"])
                scan_id = str(row["scan_id"])
                pair_key = physical_pair_key(row)
                family = str(row["predicate_family"])
                fam_key = (category, family)
                if prediction_id in used_predictions:
                    continue
                if scan_counts[scan_id] >= selection_pass["scan_cap"]:
                    continue
                if pair_counts[pair_key] >= selection_pass["pair_cap"]:
                    continue
                if category_family_counts[fam_key] >= selection_pass["family_cap"]:
                    continue
                copied = dict(row)
                copied["sampling_category_hidden"] = category
                copied["sampling_selection_pass_hidden"] = selection_pass["name"]
                copied["recommended_label_role_hidden"] = category
                selected.append(copied)
                used_predictions.add(prediction_id)
                scan_counts[scan_id] += 1
                pair_counts[pair_key] += 1
                category_family_counts[fam_key] += 1
                selected_for_category += 1
        status_rows.append(
            {
                "anchor_category": category,
                "requested_rows": target_rows,
                "selected_rows": selected_for_category,
                "available_rows": len(candidates),
                "available_packet_ready": sum(1 for row in candidates if row["packet_ready"]),
                "selected_packet_ready": sum(
                    1 for row in selected if row["anchor_category_hidden"] == category and row["packet_ready"]
                ),
                "selected_asset_needed": sum(
                    1 for row in selected if row["anchor_category_hidden"] == category and not row["packet_ready"]
                ),
            }
        )
    return selected, status_rows


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
                "anchor_category_hidden": row["anchor_category_hidden"],
                "asset_request_reason": "informative_anchor_seed_needs_multiview_pointcloud_context_packet",
            }
        )
    return rows


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Reliability Target V3 Informative Anchor Plan",
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
        "- Candidate proxy categories are sampling strata only, not target labels.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Inventory",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| total support/vertical rows | {summary['inventory']['total_support_vertical_rows']} |",
        f"| informative positive proxy rows | {summary['inventory']['informative_reliable_positive_proxy']} |",
        f"| geometry contradiction negative proxy rows | {summary['inventory']['geometry_contradiction_negative_proxy']} |",
        f"| trivial room/surface negative proxy rows | {summary['inventory']['trivial_room_surface_negative_proxy']} |",
        f"| uncertain/ontology proxy rows | {summary['inventory']['uncertain_or_ontology_negative_proxy']} |",
        f"| selected seed rows | {summary['seed_selection']['selected_rows']} |",
        f"| selected packet-ready rows | {summary['seed_selection']['selected_packet_ready']} |",
        f"| selected asset-needed rows | {summary['seed_selection']['selected_asset_needed']} |",
        "",
        "## Seed Selection",
        "",
        "| Anchor Category | Requested | Selected | Available | Packet Ready Selected | Asset Needed Selected |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in summary["selection_status"]:
        lines.append(
            f"| `{row['anchor_category']}` | {row['requested_rows']} | {row['selected_rows']} | "
            f"{row['available_rows']} | {row['selected_packet_ready']} | {row['selected_asset_needed']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The full train queue contains enough non-trivial informative-positive proxy candidates to plan a new label pool.",
            "- Some selected rows still need asset packets, so the next mining step must either request packets or restrict to packet-ready seeds with an explicit coverage caveat.",
            "- `floor`, `wall`, and `ceiling` are not removed; they are capped and kept mainly as explicit trivial negatives.",
            "- Posterior remains blocked until labels are filled, ingested, and a target-independence audit finds a controlled reliability target.",
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
    selected, selection_status = select_seed_rows(rows)
    inventory = Counter(str(row["anchor_category_hidden"]) for row in rows)
    selected_counts = Counter(str(row["anchor_category_hidden"]) for row in selected)
    family_counts = Counter(str(row["predicate_family"]) for row in selected)
    packet_ready_selected = sum(1 for row in selected if row["packet_ready"])
    asset_needed_selected = len(selected) - packet_ready_selected
    status = (
        "h002_reliability_target_v3_informative_anchor_plan_ready_with_asset_requests"
        if asset_needed_selected
        else "h002_reliability_target_v3_informative_anchor_plan_ready_packet_complete"
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "category_inventory": output_dir / "category_inventory.csv",
        "cell_inventory": output_dir / "cell_inventory.csv",
        "seed_candidates_internal": output_dir / "seed_candidates_internal.jsonl",
        "asset_request_plan": output_dir / "asset_request_plan.jsonl",
        "selection_status": output_dir / "selection_status.csv",
        "sampling_contract": output_dir / "sampling_contract.json",
    }

    summary = {
        "schema_version": "h002_reliability_target_v3_informative_anchor_plan_summary_v1",
        "created_at": created_at,
        "status": status,
        "decision": (
            "Plan a new train-only informative-anchor label pool. Retain object/endpoint controls, cap "
            "floor/wall/ceiling trivial relations, and explicitly separate informative positives, geometry "
            "contradiction negatives, trivial room/surface negatives, and uncertain/ontology negatives."
        ),
        "path_decision_status": path_decision.get("status"),
        "path_decision_selected": path_decision.get("selected_path"),
        "posterior_allowed": False,
        "validation_used": False,
        "test_used": False,
        "multi_view_as_model_input": False,
        "next_todo": "reliability_target_v3_informative_anchor_candidate_mining",
        "input_paths": {
            "path_decision": rel_path(args.path_decision),
            "packet_manifest": rel_path(args.packet_manifest),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
        },
        "inventory": {
            "ready_packets": len(packets),
            "total_support_vertical_rows": len(rows),
            "informative_reliable_positive_proxy": inventory["informative_reliable_positive_proxy"],
            "geometry_contradiction_negative_proxy": inventory["geometry_contradiction_negative_proxy"],
            "trivial_room_surface_negative_proxy": inventory["trivial_room_surface_negative_proxy"],
            "uncertain_or_ontology_negative_proxy": inventory["uncertain_or_ontology_negative_proxy"],
        },
        "seed_selection": {
            "target_rows": sum(TARGET_ROWS_BY_CATEGORY.values()),
            "selected_rows": len(selected),
            "selected_packet_ready": packet_ready_selected,
            "selected_asset_needed": asset_needed_selected,
            "selected_by_category": dict(sorted(selected_counts.items())),
            "selected_by_family": dict(sorted(family_counts.items())),
            "unique_scans": len({str(row["scan_id"]) for row in selected}),
            "unique_physical_pairs": len({physical_pair_key(row) for row in selected}),
        },
        "selection_status": selection_status,
        "sampling_contract": {
            "target_rows_by_category": TARGET_ROWS_BY_CATEGORY,
            "per_category_family_cap": PER_CATEGORY_FAMILY_CAP,
            "per_scan_cap": PER_SCAN_CAP,
            "per_physical_pair_cap": PER_PHYSICAL_PAIR_CAP,
            "room_surface_labels_capped": sorted(HARD_ROOM_SURFACES),
            "support_surface_positive_bias": sorted(SUPPORT_SURFACES),
            "candidate_proxy_categories_are_sampling_strata_only": True,
            "labeler_visible_forbidden_fields": [
                "anchor_category",
                "informative_anchor_score",
                "room_surface_score",
                "candidate_proxy",
                "queue_kind",
                "rank_band",
                "geometry_status",
                "p_geom_valid",
                "semantic_score",
                "semantic_rank",
                "label_match_status",
                "endpoint_flag_pattern",
            ],
            "posterior_reopen_gate": [
                "relation reliability binary target has at least 20 positives and 20 negatives",
                "strict or defensible diagnostic controlled slice exists",
                "trivial_dense_or_room_structure does not dominate the target",
                "object-label-only and endpoint-only probes do not explain the target",
                "validation/test usage remains false",
            ],
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
    }

    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    write_csv(output_paths["category_inventory"], inventory_rows(rows))
    write_csv(output_paths["cell_inventory"], cell_inventory(rows))
    write_jsonl(output_paths["seed_candidates_internal"], selected)
    write_jsonl(output_paths["asset_request_plan"], asset_request_rows(selected))
    write_csv(output_paths["selection_status"], selection_status)
    write_json(output_paths["sampling_contract"], summary["sampling_contract"])
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        "status={status} total={total} selected={selected} packet_ready={packet_ready} asset_needed={asset_needed} "
        "posterior_allowed={posterior_allowed} validation_used={validation_used} test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            total=summary["inventory"]["total_support_vertical_rows"],
            selected=summary["seed_selection"]["selected_rows"],
            packet_ready=summary["seed_selection"]["selected_packet_ready"],
            asset_needed=summary["seed_selection"]["selected_asset_needed"],
            posterior_allowed=summary["posterior_allowed"],
            validation_used=summary["validation_used"],
            test_used=summary["test_used"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
