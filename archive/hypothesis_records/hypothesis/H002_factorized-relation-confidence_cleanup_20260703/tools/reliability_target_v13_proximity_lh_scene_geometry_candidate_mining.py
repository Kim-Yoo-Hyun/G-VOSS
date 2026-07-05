#!/usr/bin/env python3
"""Mine scene/geometry-aware proximity LH candidates for H002 v13."""

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

DEFAULT_PLAN_DIR = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_repair_plan"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v13_proximity_lh_scene_geometry_candidate_mining"

EXPECTED_PLAN_STATUS = "h002_reliability_target_v13_proximity_lh_scene_geometry_repair_plan_ready"
EXPECTED_PLAN_NEXT = "reliability_target_v13_proximity_lh_scene_geometry_candidate_mining"

NEXT_TODO = "reliability_target_v13_proximity_lh_scene_geometry_label_fill"

ROWS_PER_BLOCK = 8
TARGET_BLOCKS = 30
TARGET_ROWS = ROWS_PER_BLOCK * TARGET_BLOCKS

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
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "scene_context_summary_v13",
    "geometry_witness_summary_v13",
    "nearest_neighbor_context_v13",
    "local_density_context_v13",
    "duplicate_or_many_alternatives_context_v13",
    "crop_or_layout_evidence_v13",
    "review_question_v13",
    "relation_reliability_state_v13",
    "scene_usefulness_state_v13",
    "primary_reason_v13",
    "uncertainty_reason_v13",
    "review_notes_v13",
]

FORBIDDEN_VISIBLE_PATTERNS = [
    "semantic_rank",
    "semantic score",
    "semantic_score",
    "machine_hint",
    "label_match",
    "rank_band",
    "rank_",
    "p_geom",
    "posterior",
    "rga-",
    "exact_match",
    "pair_has_other_predicate",
    "no_gt_for_pair",
    "semantic_underconfidence",
    "geometry_supported_alternative",
    "dense_proximity_or_annotation",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
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
                yield line_no, json.loads(line)
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


def write_tsv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def stable_int(value: str) -> int:
    return int(stable_hash(value)[:12], 16)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any, default: int = 999999) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def endpoint_type(label: str) -> str:
    if label in HARD_ROOM_SURFACES:
        return f"hard_room_surface:{label}"
    if label in STRUCTURAL_CONTEXT:
        return f"structural_context:{label}"
    return "object"


def p_geom_bin(value: Any) -> str:
    score = as_float(value)
    if score is None:
        return "missing"
    if score >= 0.95:
        return "very_high"
    if score >= 0.85:
        return "high"
    if score >= 0.70:
        return "medium"
    return "low"


def density_bin(value: int) -> str:
    if value <= 2:
        return "sparse"
    if value <= 5:
        return "moderate"
    if value <= 12:
        return "dense"
    return "very_dense"


def tier_from_rank(rank_index: int, total: int) -> str:
    if total <= 1:
        return "single_candidate"
    frac = rank_index / max(total - 1, 1)
    if frac <= 0.25:
        return "front_tier"
    if frac <= 0.75:
        return "middle_tier"
    return "tail_tier"


def distance_bin(raw_features: dict[str, Any] | None) -> str:
    if not raw_features:
        return "unknown_distance"
    norm_xy = as_float(raw_features.get("normalized_distance_xy"))
    xy = as_float(raw_features.get("distance_xy"))
    value = norm_xy if norm_xy is not None else xy
    if value is None:
        return "unknown_distance"
    if value <= 0.25:
        return "tight_xy"
    if value <= 0.50:
        return "near_xy"
    if value <= 0.75:
        return "moderate_xy"
    return "broad_xy"


def overlap_bin(raw_features: dict[str, Any] | None) -> str:
    if not raw_features:
        return "unknown_overlap"
    values = [
        as_float(raw_features.get("projected_iou_xy")),
        as_float(raw_features.get("projected_subject_overlap_ratio")),
        as_float(raw_features.get("projected_object_overlap_ratio")),
    ]
    values = [value for value in values if value is not None]
    if not values:
        return "unknown_overlap"
    value = max(values)
    if value >= 0.50:
        return "high_footprint_overlap"
    if value >= 0.20:
        return "medium_footprint_overlap"
    if value >= 0.05:
        return "low_footprint_overlap"
    return "little_or_no_footprint_overlap"


def vertical_bin(raw_features: dict[str, Any] | None) -> str:
    if not raw_features:
        return "unknown_vertical_offset"
    value = as_float(raw_features.get("normalized_center_delta_z"))
    if value is None:
        value = as_float(raw_features.get("center_delta_z"))
    if value is None:
        return "unknown_vertical_offset"
    abs_value = abs(value)
    if abs_value <= 0.15:
        return "similar_height_band"
    if abs_value <= 0.45:
        return "moderate_height_offset"
    return "large_height_offset"


def validate_plan(plan_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "expected": EXPECTED_PLAN_STATUS, "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "expected": EXPECTED_PLAN_NEXT, "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})
    boundary = plan_summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "posterior_smoke_allowed", "paper_evidence_allowed", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_violation", "key": key, "actual": boundary.get(key)})
    readiness = plan_summary.get("readiness", {})
    if readiness.get("candidate_group_goal_pass") is not True:
        errors.append({"error_type": "candidate_group_goal_not_passed", "actual": readiness.get("candidate_group_goal_pass")})
    if readiness.get("candidate_capacity_goal_pass") is not True:
        errors.append({"error_type": "candidate_capacity_goal_not_passed", "actual": readiness.get("candidate_capacity_goal_pass")})
    return errors


def enrich(row: dict[str, Any]) -> dict[str, Any]:
    subject_label = norm(row.get("subject_label"))
    object_label = norm(row.get("object_label"))
    p_geom = as_float(row.get("p_geom_valid"))
    return {
        **row,
        "subject_label_norm": subject_label,
        "object_label_norm": object_label,
        "subject_object_label_pair": f"{subject_label}|{object_label}",
        "endpoint_cell": f"{endpoint_type(subject_label)}|{endpoint_type(object_label)}",
        "structural_pair": subject_label in STRUCTURAL_CONTEXT or object_label in STRUCTURAL_CONTEXT,
        "hard_room_surface_pair": subject_label in HARD_ROOM_SURFACES or object_label in HARD_ROOM_SURFACES,
        "generic_endpoint_pair": subject_label in GENERIC_LABELS or object_label in GENERIC_LABELS,
        "semantic_rank_int": as_int(row.get("semantic_rank")),
        "p_geom_valid_float": p_geom,
        "p_geom_bin": p_geom_bin(p_geom),
        "subgraph_key": f"{row.get('scan_id')}|{row.get('subgraph_id')}",
        "subject_context_key": f"{row.get('scan_id')}|{row.get('subgraph_id')}|{row.get('subject_id')}",
        "object_context_key": f"{row.get('scan_id')}|{row.get('subgraph_id')}|{row.get('object_id')}",
    }


def read_repair_pool(lh_queue_path: Path) -> tuple[list[dict[str, Any]], dict[str, int], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    counts = Counter()
    errors: list[dict[str, Any]] = []
    for line_no, row in iter_jsonl(lh_queue_path):
        counts["lh_queue_rows_read"] += 1
        if row.get("predicate_family") != "proximity" or norm(row.get("predicate_label")) != "close by":
            continue
        counts["proximity_rows"] += 1
        enriched = enrich(row)
        if row.get("bucket_top100") != "RGA-LH":
            counts["not_rga_lh"] += 1
            continue
        if row.get("geometry_status") != "satisfied":
            counts["not_geometry_satisfied"] += 1
            continue
        if enriched["structural_pair"]:
            counts["structural_pair_excluded"] += 1
            continue
        if enriched["generic_endpoint_pair"]:
            counts["generic_endpoint_pair_excluded"] += 1
            continue
        if not row.get("prediction_id"):
            errors.append({"error_type": "missing_prediction_id", "line_no": line_no})
            continue
        rows.append(enriched)
        counts["repair_pool_rows"] += 1
    return rows, dict(counts), errors


def read_group_inventory(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row["rows"] = int(row["rows"])
            row["unique_scans"] = int(row["unique_scans"])
            row["unique_subgraphs"] = int(row["unique_subgraphs"])
            row["v13_block_candidate"] = row["v13_block_candidate"] == "True"
            row["strong_v13_block_candidate"] = row["strong_v13_block_candidate"] == "True"
            rows.append(row)
    return rows


def select_blocks(inventory: list[dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    selected: list[str] = []
    subject_counts = Counter()
    object_counts = Counter()
    self_pair_count = 0
    skipped = Counter()

    candidates = [row for row in inventory if row.get("strong_v13_block_candidate")]
    for row in candidates:
        pair = row["subject_object_label_pair"]
        subject, obj = pair.split("|", 1)
        is_self_pair = subject == obj
        if subject_counts[subject] >= 4:
            skipped["subject_cap"] += 1
            continue
        if object_counts[obj] >= 4:
            skipped["object_cap"] += 1
            continue
        if is_self_pair and self_pair_count >= 6:
            skipped["self_pair_cap"] += 1
            continue
        selected.append(pair)
        subject_counts[subject] += 1
        object_counts[obj] += 1
        if is_self_pair:
            self_pair_count += 1
        if len(selected) >= TARGET_BLOCKS:
            break

    if len(selected) < TARGET_BLOCKS:
        used = set(selected)
        for row in candidates:
            pair = row["subject_object_label_pair"]
            if pair in used:
                continue
            selected.append(pair)
            used.add(pair)
            if len(selected) >= TARGET_BLOCKS:
                break

    return selected, {
        "target_blocks": TARGET_BLOCKS,
        "selected_blocks": len(selected),
        "subject_cap": 4,
        "object_cap": 4,
        "self_pair_cap": 6,
        "self_pair_count": self_pair_count,
        "skipped": dict(skipped),
        "selected_subject_counts": dict(subject_counts),
        "selected_object_counts": dict(object_counts),
    }


def build_context(rows: list[dict[str, Any]]) -> dict[str, Any]:
    subgraph_counts = Counter(row["subgraph_key"] for row in rows)
    subject_counts = Counter(row["subject_context_key"] for row in rows)
    object_counts = Counter(row["object_context_key"] for row in rows)
    subgraph_label_pair_counts = Counter(f"{row['subgraph_key']}|{row['subject_object_label_pair']}" for row in rows)
    subject_object_label_counts = Counter(f"{row['subject_context_key']}|{row['object_label_norm']}" for row in rows)
    object_subject_label_counts = Counter(f"{row['object_context_key']}|{row['subject_label_norm']}" for row in rows)
    subject_sorted: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        subject_sorted[row["subject_context_key"]].append(row)
    for candidates in subject_sorted.values():
        candidates.sort(key=lambda item: (-(item["p_geom_valid_float"] or -1), str(item.get("prediction_id"))))
    subject_position: dict[str, tuple[int, int]] = {}
    for candidates in subject_sorted.values():
        total = len(candidates)
        for index, row in enumerate(candidates):
            subject_position[str(row.get("prediction_id"))] = (index, total)
    return {
        "subgraph_counts": subgraph_counts,
        "subject_counts": subject_counts,
        "object_counts": object_counts,
        "subgraph_label_pair_counts": subgraph_label_pair_counts,
        "subject_object_label_counts": subject_object_label_counts,
        "object_subject_label_counts": object_subject_label_counts,
        "subject_position": subject_position,
    }


def row_priority(row: dict[str, Any]) -> tuple[Any, ...]:
    p_order = {"very_high": 0, "high": 1, "medium": 2, "low": 3, "missing": 4}
    return (
        p_order.get(str(row.get("p_geom_bin")), 5),
        str(row.get("label_match_status")),
        str(row.get("rank_band")),
        str(row.get("scan_id")),
        stable_int(str(row.get("prediction_id"))),
    )


def select_rows_for_block(group_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = sorted(group_rows, key=row_priority)
    selected: list[dict[str, Any]] = []
    seen_scans: set[str] = set()
    seen_subgraphs: set[str] = set()
    seen_label_match: set[str] = set()
    seen_rank_band: set[str] = set()
    seen_p_bin: set[str] = set()

    while candidates and len(selected) < ROWS_PER_BLOCK:
        best_index = 0
        best_score: tuple[Any, ...] | None = None
        for index, row in enumerate(candidates):
            score = (
                str(row.get("scan_id")) not in seen_scans,
                str(row.get("subgraph_id")) not in seen_subgraphs,
                str(row.get("label_match_status")) not in seen_label_match,
                str(row.get("p_geom_bin")) not in seen_p_bin,
                str(row.get("rank_band")) not in seen_rank_band,
                -(row.get("p_geom_valid_float") or 0.0),
                -stable_int(str(row.get("prediction_id"))),
            )
            if best_score is None or score > best_score:
                best_score = score
                best_index = index
        row = candidates.pop(best_index)
        selected.append(row)
        seen_scans.add(str(row.get("scan_id")))
        seen_subgraphs.add(str(row.get("subgraph_id")))
        seen_label_match.add(str(row.get("label_match_status")))
        seen_rank_band.add(str(row.get("rank_band")))
        seen_p_bin.add(str(row.get("p_geom_bin")))
    return selected


def select_candidates(rows: list[dict[str, Any]], block_pairs: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_pair: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_pair[row["subject_object_label_pair"]].append(row)

    selected: list[dict[str, Any]] = []
    block_summaries: list[dict[str, Any]] = []
    for block_index, pair in enumerate(block_pairs, start=1):
        block_rows = select_rows_for_block(by_pair[pair])
        selected.extend(block_rows)
        block_summaries.append(
            {
                "target_construction_block": f"v13_block_{block_index:02d}",
                "subject_object_label_pair": pair,
                "selected_rows": len(block_rows),
                "unique_scans": len({str(row.get("scan_id")) for row in block_rows}),
                "unique_subgraphs": len({str(row.get("subgraph_id")) for row in block_rows}),
                "label_match_status_values_hidden": len({str(row.get("label_match_status")) for row in block_rows}),
                "rank_band_values_hidden": len({str(row.get("rank_band")) for row in block_rows}),
                "p_geom_bin_values_hidden": len({str(row.get("p_geom_bin")) for row in block_rows}),
            }
        )
        for row in block_rows:
            row["target_construction_block"] = f"v13_block_{block_index:02d}"
    return selected, block_summaries


def read_raw_features(match_rows_path: Path, prediction_ids: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    counts = {"requested": len(prediction_ids), "found": 0, "match_rows_scanned": 0}
    for _, row in iter_jsonl(match_rows_path):
        counts["match_rows_scanned"] += 1
        identity = row.get("identity", {})
        prediction_id = identity.get("prediction_id") or row.get("prediction_id")
        if prediction_id not in prediction_ids:
            continue
        geometry = row.get("geometry", {})
        found[str(prediction_id)] = geometry.get("raw_features") or {}
        counts["found"] = len(found)
        if len(found) >= len(prediction_ids):
            break
    return found, counts


def visible_relation(row: dict[str, Any]) -> str:
    return f"{row.get('subject_label')} close by {row.get('object_label')}"


def visible_row(row: dict[str, Any], context: dict[str, Any], raw_features: dict[str, Any], review_card: str) -> dict[str, str]:
    prediction_id = str(row.get("prediction_id"))
    subject_index, subject_total = context["subject_position"].get(prediction_id, (0, 1))
    subgraph_count = context["subgraph_counts"][row["subgraph_key"]]
    subject_count = context["subject_counts"][row["subject_context_key"]]
    object_count = context["object_counts"][row["object_context_key"]]
    label_pair_count = context["subgraph_label_pair_counts"][f"{row['subgraph_key']}|{row['subject_object_label_pair']}"]
    same_obj_label_count = context["subject_object_label_counts"][f"{row['subject_context_key']}|{row['object_label_norm']}"]
    same_subj_label_count = context["object_subject_label_counts"][f"{row['object_context_key']}|{row['subject_label_norm']}"]

    dist = distance_bin(raw_features)
    overlap = overlap_bin(raw_features)
    vertical = vertical_bin(raw_features)
    local_tier = tier_from_rank(subject_index, subject_total)

    return {
        "blind_review_id": "ftv13p_" + stable_hash(prediction_id)[:12],
        "review_card": review_card,
        "candidate_relation": visible_relation(row),
        "subject_label": str(row.get("subject_label")),
        "predicate_label": "close by",
        "object_label": str(row.get("object_label")),
        "scene_context_summary_v13": f"local relation in a {density_bin(subgraph_count)} proximity context; subject alternatives {density_bin(subject_count)}; object alternatives {density_bin(object_count)}",
        "geometry_witness_summary_v13": f"distance={dist}; footprint_overlap={overlap}; vertical_offset={vertical}; witness is binned from 3D layout",
        "nearest_neighbor_context_v13": f"subject-side geometry-neighbor tier: {local_tier}; evaluated among local candidates for this subject",
        "local_density_context_v13": f"subgraph proximity density={density_bin(subgraph_count)}; subject candidate density={density_bin(subject_count)}; object candidate density={density_bin(object_count)}",
        "duplicate_or_many_alternatives_context_v13": f"same visible pair in local subgraph={density_bin(label_pair_count)}; same object-label alternatives for subject={density_bin(same_obj_label_count)}; same subject-label alternatives for object={density_bin(same_subj_label_count)}",
        "crop_or_layout_evidence_v13": "3D layout witness available as binned text; image or crop evidence is not used as model input in this stage",
        "review_question_v13": "Is this close-by relation a useful local relation for this scene context, rather than dense neighborhood noise or a trivial context relation?",
        "relation_reliability_state_v13": "",
        "scene_usefulness_state_v13": "",
        "primary_reason_v13": "",
        "uncertainty_reason_v13": "",
        "review_notes_v13": "",
    }


def hidden_row(row: dict[str, Any], raw_features: dict[str, Any], visible: dict[str, str]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v13_proximity_scene_geometry_candidate_mining_hidden_v1",
        "blind_review_id": visible["blind_review_id"],
        "prediction_id": row.get("prediction_id"),
        "split": "train",
        "source_id": row.get("source_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "source_queue_hidden": row.get("bucket_top100"),
        "semantic_rank_hidden": row.get("semantic_rank"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "p_geom_bin_hidden": row.get("p_geom_bin"),
        "geometry_status_hidden": row.get("geometry_status"),
        "label_match_status_hidden": row.get("label_match_status"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket"),
        "machine_hint_hidden": row.get("machine_hint"),
        "rank_band_hidden": row.get("rank_band"),
        "subject_object_label_pair_hidden": row.get("subject_object_label_pair"),
        "endpoint_cell_hidden": row.get("endpoint_cell"),
        "target_construction_block_hidden": row.get("target_construction_block"),
        "raw_features_hidden": raw_features,
        "reviewer_visible": False,
        "posterior_input_allowed": False,
        "model_input_allowed": False,
    }


def write_review_card(path: Path, row: dict[str, str]) -> None:
    lines = [
        f"# {row['candidate_relation']}",
        "",
        "## Scene Evidence",
        "",
        f"- {row['scene_context_summary_v13']}",
        f"- {row['geometry_witness_summary_v13']}",
        f"- {row['nearest_neighbor_context_v13']}",
        f"- {row['local_density_context_v13']}",
        f"- {row['duplicate_or_many_alternatives_context_v13']}",
        f"- {row['crop_or_layout_evidence_v13']}",
        "",
        "## Question",
        "",
        row["review_question_v13"],
        "",
        "## Fill Fields",
        "",
        "- relation_reliability_state_v13:",
        "- scene_usefulness_state_v13:",
        "- primary_reason_v13:",
        "- uncertainty_reason_v13:",
        "- review_notes_v13:",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def leakage_hits(rows: list[dict[str, str]], review_card_dir: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in rows:
        for field, value in row.items():
            lower = str(value).lower()
            for pattern in FORBIDDEN_VISIBLE_PATTERNS:
                if pattern in lower:
                    hits.append({"surface": "label_sheet", "blind_review_id": row["blind_review_id"], "field": field, "pattern": pattern})
        card_path = review_card_dir / f"{row['blind_review_id']}.md"
        text = card_path.read_text(encoding="utf-8").lower()
        for pattern in FORBIDDEN_VISIBLE_PATTERNS:
            if pattern in text:
                hits.append({"surface": "review_card", "blind_review_id": row["blind_review_id"], "field": str(card_path), "pattern": pattern})
    return hits


def validate_outputs(visible_rows: list[dict[str, str]], hidden_rows: list[dict[str, Any]], block_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(visible_rows) != TARGET_ROWS:
        errors.append({"error_type": "unexpected_visible_row_count", "expected": TARGET_ROWS, "actual": len(visible_rows)})
    if len(hidden_rows) != TARGET_ROWS:
        errors.append({"error_type": "unexpected_hidden_row_count", "expected": TARGET_ROWS, "actual": len(hidden_rows)})
    if len(block_summaries) != TARGET_BLOCKS:
        errors.append({"error_type": "unexpected_block_count", "expected": TARGET_BLOCKS, "actual": len(block_summaries)})
    blind_ids = [row["blind_review_id"] for row in visible_rows]
    if len(set(blind_ids)) != len(blind_ids):
        errors.append({"error_type": "duplicate_blind_review_id"})
    predictions = [row["prediction_id"] for row in hidden_rows]
    if len(set(predictions)) != len(predictions):
        errors.append({"error_type": "duplicate_prediction_id"})
    for summary in block_summaries:
        if summary["selected_rows"] != ROWS_PER_BLOCK:
            errors.append({"error_type": "block_row_count_mismatch", "block": summary["target_construction_block"], "actual": summary["selected_rows"]})
        if summary["unique_scans"] < 3:
            errors.append({"error_type": "block_scan_diversity_low", "block": summary["target_construction_block"], "actual": summary["unique_scans"]})
        if summary["label_match_status_values_hidden"] < 2:
            errors.append({"error_type": "block_label_match_hidden_diversity_low", "block": summary["target_construction_block"], "actual": summary["label_match_status_values_hidden"]})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V13 Proximity Scene/Geometry Candidate Mining",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Result",
        "",
        "```text",
        f"selected_rows = {counts['selected_rows']}",
        f"selected_blocks = {counts['selected_blocks']}",
        f"rows_per_block = {counts['rows_per_block']}",
        f"unique_scans = {counts['unique_scans']}",
        f"unique_subgraphs = {counts['unique_subgraphs']}",
        f"visible_leakage_hits = {counts['visible_leakage_hits']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## What Changed From V12",
        "",
        "v12 exposed only object-pair text and produced an object-pair shortcut. v13 candidate mining keeps the same proximity LH branch but changes the visible evidence surface to local scene/geometry context.",
        "",
        "## Visible Evidence",
        "",
        "- binned 3D geometry witness",
        "- subject/object local candidate density",
        "- local same-pair and duplicate-label alternatives",
        "- scene layout review card",
        "",
        "Hidden fields such as source rank, machine hint, label-match status, target construction block, and raw geometry scores are retained only in `hidden_audit_manifest.jsonl`.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
        "Posterior smoke remains blocked until labels are filled, ingested, and pass target-independence audit.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    plan_dir = as_abs(args.plan_dir)
    output_dir = as_abs(args.output_dir)
    review_card_dir = output_dir / "review_cards_v13"
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(plan_dir / "summary.json")
    validation_errors = validate_plan(plan_summary)
    group_inventory = read_group_inventory(plan_dir / "repair_group_inventory.csv")
    block_pairs, block_selection = select_blocks(group_inventory)
    repair_pool, input_counts, read_errors = read_repair_pool(args.lh_queue)
    validation_errors.extend(read_errors[:100])

    context = build_context(repair_pool)
    selected, block_summaries = select_candidates(repair_pool, block_pairs)
    selected_ids = {str(row.get("prediction_id")) for row in selected}
    raw_feature_map, raw_feature_counts = read_raw_features(args.match_rows, selected_ids)

    visible_rows: list[dict[str, str]] = []
    hidden_rows: list[dict[str, Any]] = []
    internal_rows: list[dict[str, Any]] = []
    for row in selected:
        prediction_id = str(row.get("prediction_id"))
        blind_id = "ftv13p_" + stable_hash(prediction_id)[:12]
        review_card = f"review_cards_v13/{blind_id}.md"
        raw_features = raw_feature_map.get(prediction_id, {})
        visible = visible_row(row, context, raw_features, review_card)
        hidden = hidden_row(row, raw_features, visible)
        visible_rows.append(visible)
        hidden_rows.append(hidden)
        internal_rows.append({**row, "blind_review_id": visible["blind_review_id"], "raw_features_joined": bool(raw_features)})
        write_review_card(review_card_dir / f"{visible['blind_review_id']}.md", visible)

    validation_errors.extend(validate_outputs(visible_rows, hidden_rows, block_summaries))
    leakage = leakage_hits(visible_rows, review_card_dir)
    if leakage:
        validation_errors.append({"error_type": "visible_leakage_hits_present", "count": len(leakage)})

    selected_scans = {str(row.get("scan_id")) for row in selected}
    selected_subgraphs = {str(row.get("subgraph_id")) for row in selected}
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "label_ready_sheet": output_dir / "label_ready_sheet_v13.tsv",
        "hidden_audit_manifest": output_dir / "hidden_audit_manifest_v13.jsonl",
        "selected_candidates_internal": output_dir / "selected_candidates_internal.jsonl",
        "selected_block_summary": output_dir / "selected_block_summary.csv",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    status = (
        "h002_reliability_target_v13_proximity_lh_scene_geometry_candidate_mining_ready_for_label_fill"
        if not validation_errors
        else "h002_reliability_target_v13_proximity_lh_scene_geometry_candidate_mining_errors"
    )
    summary = {
        "schema_version": "h002_reliability_target_v13_proximity_lh_scene_geometry_candidate_mining_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "plan_summary": rel_path(plan_dir / "summary.json"),
            "repair_group_inventory": rel_path(plan_dir / "repair_group_inventory.csv"),
            "lh_queue": rel_path(args.lh_queue),
            "match_rows": rel_path(args.match_rows),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "input_counts": input_counts,
        "raw_feature_join": raw_feature_counts,
        "block_selection": block_selection,
        "counts": {
            "selected_rows": len(visible_rows),
            "selected_blocks": len(block_summaries),
            "rows_per_block": ROWS_PER_BLOCK,
            "unique_scans": len(selected_scans),
            "unique_subgraphs": len(selected_subgraphs),
            "visible_pair_blocks": len({row["subject_object_label_pair_hidden"] for row in hidden_rows}),
            "raw_feature_joined_rows": sum(1 for row in internal_rows if row["raw_features_joined"]),
            "visible_leakage_hits": len(leakage),
            "block_label_match_hidden_min_values": min((row["label_match_status_values_hidden"] for row in block_summaries), default=0),
            "block_rank_band_hidden_min_values": min((row["rank_band_values_hidden"] for row in block_summaries), default=0),
            "block_p_geom_bin_hidden_min_values": min((row["p_geom_bin_values_hidden"] for row in block_summaries), default=0),
        },
        "next_todo": NEXT_TODO,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "rga_redefined_as_lh_only": False,
        },
        "validation_errors": len(validation_errors),
    }

    write_json(output_paths["summary"], summary)
    write_tsv(output_paths["label_ready_sheet"], visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["hidden_audit_manifest"], hidden_rows)
    write_jsonl(output_paths["selected_candidates_internal"], internal_rows)
    write_csv(output_paths["selected_block_summary"], block_summaries)
    write_jsonl(output_paths["visible_leakage_hits"], leakage)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(f"status={summary['status']}")
    print(f"selected_rows={counts['selected_rows']}")
    print(f"selected_blocks={counts['selected_blocks']}")
    print(f"unique_scans={counts['unique_scans']}")
    print(f"raw_feature_joined_rows={counts['raw_feature_joined_rows']}")
    print(f"visible_leakage_hits={counts['visible_leakage_hits']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
