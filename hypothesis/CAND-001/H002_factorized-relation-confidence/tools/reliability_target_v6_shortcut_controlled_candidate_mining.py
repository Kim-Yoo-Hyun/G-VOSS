#!/usr/bin/env python3
"""Mine H002 v6 shortcut-controlled candidate rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PLAN_DIR = RGA_ROOT / "reliability_target_v6_shortcut_controlled_sampling_plan_codex_proxy_user_requested"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_PACKET_MANIFESTS = [
    RGA_ROOT / "independent_asset_packets/packet_manifest.jsonl",
    RGA_ROOT / "reliability_target_v5_cell_contrast_asset_packets/generated_packet_manifest.jsonl",
]
DEFAULT_PREVIOUS_SEED_AUDIT = (
    RGA_ROOT
    / "reliability_target_v6_uncertainty_aware_seed_audit_codex_proxy_user_requested"
    / "seed_audit_rows.jsonl"
)
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v6_shortcut_controlled_candidate_mining_codex_proxy_user_requested"

PRIMARY_FAMILIES = ["support_contact", "relative_vertical"]
BUCKET_ORDER = [
    "B1_semantic_high_geometry_high",
    "B2_semantic_high_geometry_low",
    "B3_semantic_low_geometry_high",
    "B4_ambiguous_or_coverage_limited",
]
REVIEW_SCOPE = "h002_reliability_v6_shortcut_controlled_review"
SCHEMA_VERSION = "h002_reliability_target_v6_shortcut_controlled_candidate_mining_v1"
CANDIDATE_KEEP_PER_CELL = 5000

HARD_ROOM_SURFACES = {"floor", "wall", "ceiling"}
STRUCTURAL_CONTEXT = {"floor", "wall", "ceiling", "room", "door", "doorframe", "window", "blinds", "curtain"}
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

COMPLETION_FIELDS = [
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

FORBIDDEN_VISIBLE_FIELD_TOKENS = [
    "candidate_bucket",
    "expected_target",
    "semantic_score",
    "semantic_rank",
    "p_geom",
    "geometry_status",
    "rank_band",
    "source_queue",
    "cell_contrast",
    "object_family_cell",
    "label_match",
    "h001_verification",
    "gt_label",
]

FORBIDDEN_VISIBLE_VALUE_TOKENS = [
    "candidate_bucket",
    "semantic_score",
    "semantic_rank",
    "p_geom",
    "geometry_status",
    "rank_band",
    "source_queue",
    "cell_contrast",
    "object_family_cell",
    "label_match",
    "h001_verification",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--packet-manifest", type=Path, action="append", default=list(DEFAULT_PACKET_MANIFESTS))
    parser.add_argument("--previous-seed-audit", type=Path, default=DEFAULT_PREVIOUS_SEED_AUDIT)
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


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
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


def blind_review_id(row: dict[str, Any]) -> str:
    return "ftv6sc_" + stable_hash("h002_v6_shortcut_controlled:" + str(row["prediction_id"]))[:12]


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


def packet_key_from_values(scan_id: Any, subject_id: Any, object_id: Any, predicate_label: Any) -> tuple[str, str, str, str]:
    return (str(scan_id), str(subject_id), str(object_id), str(predicate_label))


def packet_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return packet_key_from_values(row.get("scan_id"), row.get("subject_id"), row.get("object_id"), row.get("predicate_label"))


def packet_ready(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    return (
        row.get("packet_status") == "ready"
        and bool(row.get("multiview_packet"))
        and bool(row.get("pointcloud_or_mesh_packet"))
        and bool(row.get("contact_or_context_sheet"))
    )


def load_ready_packets(paths: list[Path]) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    packets: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for path in paths:
        abs_path = as_abs(path)
        if not abs_path.exists():
            continue
        for row in iter_jsonl(abs_path):
            if packet_ready(row):
                packets[packet_key(row)] = row
    return packets


def load_previous_prediction_ids(path: Path) -> set[str]:
    abs_path = as_abs(path)
    if not abs_path.exists():
        return set()
    output: set[str] = set()
    for row in iter_jsonl(abs_path):
        prediction_id = row.get("prediction_id") or row.get("prediction_id_hidden")
        if prediction_id:
            output.add(str(prediction_id))
    return output


def semantic_band(row: dict[str, Any]) -> str:
    rank = as_int(row.get("semantic_rank"))
    score = as_float(row.get("semantic_score_norm"))
    if rank <= 100 or score >= 0.70:
        return "semantic_high"
    if rank > 500 or score < 0.35:
        return "semantic_low"
    return "semantic_mid"


def geometry_band(row: dict[str, Any]) -> str:
    status = str(row.get("geometry_status") or "")
    p_geom = as_float(row.get("p_geom_valid"))
    if status == "satisfied":
        return "geometry_high"
    if status in {"unsatisfied", "violated"}:
        return "geometry_low"
    if p_geom >= 0.85:
        return "geometry_high"
    if p_geom <= 0.35:
        return "geometry_low"
    return "geometry_mid_or_ambiguous"


def candidate_bucket(row: dict[str, Any]) -> str:
    sem = semantic_band(row)
    geom = geometry_band(row)
    if sem == "semantic_high" and geom == "geometry_high":
        return "B1_semantic_high_geometry_high"
    if sem == "semantic_high" and geom == "geometry_low":
        return "B2_semantic_high_geometry_low"
    if sem == "semantic_low" and geom == "geometry_high":
        return "B3_semantic_low_geometry_high"
    return "B4_ambiguous_or_coverage_limited"


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


def semantic_margin(row: dict[str, Any], band: str) -> float:
    rank = as_int(row.get("semantic_rank"))
    score = as_float(row.get("semantic_score_norm"))
    if band == "semantic_high":
        return max(max(0, 100 - rank) / 100.0, max(0.0, score - 0.70))
    if band == "semantic_low":
        return max(max(0, rank - 500) / 1000.0, max(0.0, 0.35 - score))
    return max(0.0, 0.35 - abs(score - 0.525))


def geometry_margin(row: dict[str, Any], band: str) -> float:
    status = str(row.get("geometry_status") or "")
    p_geom = as_float(row.get("p_geom_valid"))
    if band == "geometry_high":
        return 1.0 if status == "satisfied" else max(0.0, p_geom - 0.85)
    if band == "geometry_low":
        return 1.0 if status in {"unsatisfied", "violated"} else max(0.0, 0.35 - p_geom)
    return 0.2


def score_tuple(row: dict[str, Any], ready: bool) -> tuple[int, float, int, int, int]:
    sem = semantic_band(row)
    geom = geometry_band(row)
    band_margin = semantic_margin(row, sem) + geometry_margin(row, geom)
    return (
        1 if ready else 0,
        band_margin,
        informative_score(row),
        -room_surface_score(row),
        -stable_int(str(row.get("prediction_id"))),
    )


def physical_pair_key(row: dict[str, Any]) -> str:
    return "|".join([str(row.get("scan_id")), str(row.get("subgraph_id")), str(row.get("subject_id")), str(row.get("object_id"))])


def subject_object_label_pair(row: dict[str, Any]) -> str:
    return "|".join([norm_label(row.get("subject_label")), norm_label(row.get("object_label"))])


def object_family_cell(row: dict[str, Any]) -> str:
    return "|".join([norm_label(row.get("object_label")), str(row.get("predicate_family"))])


def subject_object_family_cell(row: dict[str, Any]) -> str:
    return "|".join([norm_label(row.get("subject_label")), norm_label(row.get("object_label")), str(row.get("predicate_family"))])


def predicate_label_bucket(row: dict[str, Any]) -> str:
    return "|".join([str(row.get("predicate_label")), str(row.get("candidate_bucket"))])


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


def family_prompt(row: dict[str, Any]) -> dict[str, str]:
    family = str(row.get("predicate_family"))
    if family == "support_contact":
        return {
            "question": "Does the subject physically contact, rest on, support, or attach to the object in the evidence?",
            "supporting_cues": "visible contact or support, plausible load/contact direction, consistent object identity, non-trivial object pair",
            "contradicting_cues": "nearby without contact/support, clear gap or wrong support direction, endpoint identity issue, room-surface triviality",
        }
    if family == "relative_vertical":
        return {
            "question": "Is the subject clearly higher or lower than the object as stated by the predicate?",
            "supporting_cues": "clear vertical ordering, predicate direction matches the evidence, comparable object-level endpoints",
            "contradicting_cues": "wrong vertical direction, ambiguous height, non-comparable room surface, endpoint identity issue",
        }
    return {
        "question": "Does the relation hold according to the evidence?",
        "supporting_cues": "relation is supported by visual and geometric evidence",
        "contradicting_cues": "relation is contradicted, trivial, or not evaluable from the evidence",
    }


def normalize_row(row: dict[str, Any], source_queue: str, packet: dict[str, Any] | None) -> dict[str, Any]:
    bucket = candidate_bucket(row)
    sem = semantic_band(row)
    geom = geometry_band(row)
    ready = packet_ready(packet)
    normalized = {
        "schema_version": "h002_reliability_target_v6_shortcut_controlled_candidate_internal_v1",
        "prediction_id": row.get("prediction_id"),
        "source_id": row.get("source_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "scene_context_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "subject_label_norm_hidden": norm_label(row.get("subject_label")),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "object_label_norm_hidden": norm_label(row.get("object_label")),
        "source_queue_hidden": source_queue,
        "queue_kind_hidden": row.get("queue_kind") or source_queue,
        "candidate_bucket_hidden": bucket,
        "semantic_band_hidden": sem,
        "geometry_band_hidden": geom,
        "coverage_bucket_hidden": "packet_ready" if ready else "asset_needed",
        "rank_band_hidden": row.get("rank_band"),
        "semantic_rank_hidden": row.get("semantic_rank"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm"),
        "semantic_score_raw_hidden": row.get("semantic_score_raw"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "geometry_status_hidden": row.get("geometry_status"),
        "h001_verification_status_hidden": row.get("h001_verification_status"),
        "label_match_status_hidden": row.get("label_match_status"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket"),
        "label_match_family_hidden": label_match_family(row),
        "machine_hint_hidden": row.get("machine_hint"),
        "matched_predicates_hidden": row.get("matched_predicates", []),
        "reason_codes_hidden": row.get("reason_codes", []),
        "endpoint_flag_pattern_hidden": endpoint_pattern(row),
        "informative_score_hidden": informative_score(row),
        "room_surface_score_hidden": room_surface_score(row),
        "subject_object_id_pair_hidden": physical_pair_key(row),
        "subject_object_label_pair_hidden": subject_object_label_pair(row),
        "object_family_cell_hidden": object_family_cell(row),
        "subject_object_family_cell_hidden": subject_object_family_cell(row),
        "predicate_label_bucket_hidden": predicate_label_bucket({"predicate_label": row.get("predicate_label"), "candidate_bucket": bucket}),
        "packet_ready": ready,
        "packet_status": "ready" if ready else "asset_needed",
        "packet_source_hidden": "existing_packet_manifest" if ready else "asset_needed",
        "multiview_packet": (packet or {}).get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": (packet or {}).get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": (packet or {}).get("contact_or_context_sheet", ""),
        "selection_score_tuple_hidden": score_tuple(row, ready),
    }
    normalized["blind_review_id"] = blind_review_id(normalized)
    return normalized


def passes_basic_filter(row: dict[str, Any]) -> bool:
    if row.get("predicate_family") not in set(PRIMARY_FAMILIES):
        return False
    if not row.get("prediction_id"):
        return False
    if not row.get("scan_id") or not row.get("subject_id") or not row.get("object_id") or not row.get("predicate_label"):
        return False
    return True


def push_candidate(
    heaps: dict[tuple[str, str], list[tuple[tuple[int, float, int, int, int], str, dict[str, Any]]]],
    row: dict[str, Any],
) -> None:
    cell = (str(row["predicate_family"]), str(row["candidate_bucket_hidden"]))
    key = tuple(row["selection_score_tuple_hidden"])
    item = (key, str(row["prediction_id"]), row)
    heap = heaps[cell]
    if len(heap) < CANDIDATE_KEEP_PER_CELL:
        heapq.heappush(heap, item)
    elif item[0] > heap[0][0]:
        heapq.heapreplace(heap, item)


def scan_candidates(
    hl_queue: Path,
    lh_queue: Path,
    packets: dict[tuple[str, str, str, str], dict[str, Any]],
    previous_prediction_ids: set[str],
) -> tuple[
    dict[tuple[str, str], list[dict[str, Any]]],
    dict[tuple[str, str], Counter[str]],
    Counter[str],
]:
    heaps: dict[tuple[str, str], list[tuple[tuple[int, float, int, int, int], str, dict[str, Any]]]] = defaultdict(list)
    inventory: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    global_counts: Counter[str] = Counter()
    for source_queue, path in [("HL", hl_queue), ("LH", lh_queue)]:
        for raw in iter_jsonl(path):
            global_counts[f"{source_queue}_rows_read"] += 1
            if not passes_basic_filter(raw):
                continue
            prediction_id = str(raw.get("prediction_id"))
            if prediction_id in previous_prediction_ids:
                global_counts["excluded_previous_seed_prediction_id"] += 1
                continue
            packet = packets.get(packet_key(raw))
            row = normalize_row(raw, source_queue, packet)
            cell = (str(row["predicate_family"]), str(row["candidate_bucket_hidden"]))
            inventory[cell]["eligible_rows"] += 1
            inventory[cell][f"{source_queue}_rows"] += 1
            inventory[cell][row["coverage_bucket_hidden"]] += 1
            inventory[cell][str(row["rank_band_hidden"])] += 1
            push_candidate(heaps, row)
    candidates: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for cell, heap in heaps.items():
        candidates[cell] = [item[2] for item in sorted(heap, key=lambda item: item[0], reverse=True)]
    return candidates, inventory, global_counts


def cap_keys(row: dict[str, Any]) -> dict[str, str]:
    return {
        "max_rows_per_scan": str(row["scan_id"]),
        "max_rows_per_scene_context": str(row["scene_context_id"]),
        "max_rows_per_subject_object_id_pair": str(row["subject_object_id_pair_hidden"]),
        "max_rows_per_subject_object_label_pair": str(row["subject_object_label_pair_hidden"]),
        "max_rows_per_subject_label": norm_label(row["subject_label"]),
        "max_rows_per_object_label": norm_label(row["object_label"]),
        "max_rows_per_object_family_cell": str(row["object_family_cell_hidden"]),
        "max_rows_per_subject_object_family_cell": str(row["subject_object_family_cell_hidden"]),
        "max_rows_per_predicate_label_bucket": str(row["predicate_label_bucket_hidden"]),
    }


def select_candidates(
    candidates: dict[tuple[str, str], list[dict[str, Any]]],
    bucket_specs: list[dict[str, Any]],
    caps: dict[str, int],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, int]], list[dict[str, Any]]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    cap_counts: dict[str, Counter[str]] = defaultdict(Counter)
    cell_counts: dict[tuple[str, str], dict[str, int]] = {}
    rejection_rows: list[dict[str, Any]] = []
    cells = [(row["predicate_family"], row["bucket"]) for row in bucket_specs]
    target_by_cell = {(row["predicate_family"], row["bucket"]): int(row["target_candidate_rows"]) for row in bucket_specs}
    indexes = {cell: 0 for cell in cells}
    selected_by_cell = Counter()

    def allowed(row: dict[str, Any]) -> tuple[bool, str]:
        prediction_id = str(row["prediction_id"])
        if prediction_id in selected_ids:
            return False, "duplicate_prediction_id"
        for cap_name, key in cap_keys(row).items():
            limit = int(caps[cap_name])
            if cap_counts[cap_name][key] >= limit:
                return False, cap_name
        return True, ""

    progress = True
    while progress:
        progress = False
        for cell in cells:
            if selected_by_cell[cell] >= target_by_cell[cell]:
                continue
            rows = candidates.get(cell, [])
            while indexes[cell] < len(rows):
                row = rows[indexes[cell]]
                indexes[cell] += 1
                ok, reason = allowed(row)
                if not ok:
                    if len(rejection_rows) < 2000:
                        rejection_rows.append(
                            {
                                "prediction_id": row.get("prediction_id"),
                                "predicate_family": row.get("predicate_family"),
                                "candidate_bucket_hidden": row.get("candidate_bucket_hidden"),
                                "reject_reason": reason,
                            }
                        )
                    continue
                selected.append(row)
                selected_ids.add(str(row["prediction_id"]))
                for cap_name, key in cap_keys(row).items():
                    cap_counts[cap_name][key] += 1
                selected_by_cell[cell] += 1
                progress = True
                break

    for cell in cells:
        cell_counts[cell] = {
            "target_rows": target_by_cell[cell],
            "selected_rows": selected_by_cell[cell],
            "candidate_rows_retained": len(candidates.get(cell, [])),
            "deficit": max(0, target_by_cell[cell] - selected_by_cell[cell]),
        }
    return selected, cell_counts, rejection_rows


def evidence_status(row: dict[str, Any]) -> str:
    return "ready" if row.get("packet_ready") is True and row.get("packet_status") == "ready" else "asset_needed"


def visible_row(row: dict[str, Any]) -> dict[str, Any]:
    prompt = family_prompt(row)
    ready = evidence_status(row) == "ready"
    output = {
        "blind_review_id": row["blind_review_id"],
        "review_scope": REVIEW_SCOPE,
        "scan_id": row.get("scan_id", ""),
        "scene_context_id": row.get("scene_context_id", ""),
        "subject_id": row.get("subject_id", ""),
        "subject_label": row.get("subject_label", ""),
        "predicate_label": row.get("predicate_label", ""),
        "predicate_family": row.get("predicate_family", ""),
        "object_id": row.get("object_id", ""),
        "object_label": row.get("object_label", ""),
        "family_question": prompt["question"],
        "supporting_cues": prompt["supporting_cues"],
        "contradicting_cues": prompt["contradicting_cues"],
        "evidence_packet_status": evidence_status(row),
        "multiview_packet": row.get("multiview_packet", "") if ready else "",
        "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", "") if ready else "",
        "contact_or_context_sheet": row.get("contact_or_context_sheet", "") if ready else "",
    }
    for field in COMPLETION_FIELDS:
        output[field] = ""
    return output


def manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_shortcut_controlled_manifest_v1",
        "batch_name": "reliability_target_v6_shortcut_controlled_candidate_mining",
        "blind_review_id": row["blind_review_id"],
        "prediction_id_hidden": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "scene_context_id": row.get("scene_context_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "subject_label_norm_hidden": row.get("subject_label_norm_hidden"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "object_label_norm_hidden": row.get("object_label_norm_hidden"),
        "source_id_hidden": row.get("source_id"),
        "source_queue_hidden": row.get("source_queue_hidden"),
        "queue_kind_hidden": row.get("queue_kind_hidden"),
        "candidate_bucket_hidden": row.get("candidate_bucket_hidden"),
        "semantic_band_hidden": row.get("semantic_band_hidden"),
        "geometry_band_hidden": row.get("geometry_band_hidden"),
        "coverage_bucket_hidden": row.get("coverage_bucket_hidden"),
        "rank_band_hidden": row.get("rank_band_hidden"),
        "semantic_rank_hidden": row.get("semantic_rank_hidden"),
        "semantic_score_raw_hidden": row.get("semantic_score_raw_hidden"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm_hidden"),
        "p_geom_valid_hidden": row.get("p_geom_valid_hidden"),
        "geometry_status_hidden": row.get("geometry_status_hidden"),
        "h001_verification_status_hidden": row.get("h001_verification_status_hidden"),
        "label_match_status_hidden": row.get("label_match_status_hidden"),
        "label_match_family_hidden": row.get("label_match_family_hidden"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket_hidden"),
        "matched_predicates_hidden": row.get("matched_predicates_hidden"),
        "reason_codes_hidden": row.get("reason_codes_hidden"),
        "machine_hint_hidden": row.get("machine_hint_hidden"),
        "endpoint_flag_pattern_hidden": row.get("endpoint_flag_pattern_hidden"),
        "informative_score_hidden": row.get("informative_score_hidden"),
        "room_surface_score_hidden": row.get("room_surface_score_hidden"),
        "subject_object_id_pair_hidden": row.get("subject_object_id_pair_hidden"),
        "subject_object_label_pair_hidden": row.get("subject_object_label_pair_hidden"),
        "object_family_cell_hidden": row.get("object_family_cell_hidden"),
        "subject_object_family_cell_hidden": row.get("subject_object_family_cell_hidden"),
        "predicate_label_bucket_hidden": row.get("predicate_label_bucket_hidden"),
        "packet_status_hidden": evidence_status(row),
        "packet_source_hidden": row.get("packet_source_hidden"),
        "packet_paths": {
            "multiview_packet": row.get("multiview_packet", ""),
            "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", ""),
            "contact_or_context_sheet": row.get("contact_or_context_sheet", ""),
        },
        "selection_score_tuple_hidden": row.get("selection_score_tuple_hidden"),
        "forbidden_as_labeler_visible": [
            "prediction_id_hidden",
            "candidate_bucket_hidden",
            "semantic_band_hidden",
            "geometry_band_hidden",
            "coverage_bucket_hidden",
            "rank_band_hidden",
            "semantic_rank_hidden",
            "semantic_score_raw_hidden",
            "semantic_score_norm_hidden",
            "p_geom_valid_hidden",
            "geometry_status_hidden",
            "h001_verification_status_hidden",
            "label_match_status_hidden",
            "object_family_cell_hidden",
            "subject_object_family_cell_hidden",
            "source_queue_hidden",
            "queue_kind_hidden",
            "machine_hint_hidden",
        ],
    }


def asset_request_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_request_reason": "v6_shortcut_controlled_candidate_needs_multiview_pointcloud_context_packet",
        "blind_review_id": row["blind_review_id"],
        "prediction_id": row.get("prediction_id"),
        "scan_id": row.get("scan_id"),
        "scene_context_id": row.get("scene_context_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "candidate_bucket_hidden": row.get("candidate_bucket_hidden"),
        "semantic_band_hidden": row.get("semantic_band_hidden"),
        "geometry_band_hidden": row.get("geometry_band_hidden"),
        "requested_artifacts": ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"],
        "target_packet_stem": row["blind_review_id"],
    }


def leakage_hits(fieldnames: list[str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for field in fieldnames:
        lower = field.lower()
        for token in FORBIDDEN_VISIBLE_FIELD_TOKENS:
            if token in lower:
                hits.append({"field": field, "forbidden_token": token})
    return hits


def visible_value_leakage_hits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in rows:
        blind_id = row.get("blind_review_id")
        for field, value in row.items():
            if field in {"multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"}:
                continue
            lower = str(value).lower()
            for token in FORBIDDEN_VISIBLE_VALUE_TOKENS:
                if token in lower:
                    hits.append({"blind_review_id": blind_id, "field": field, "forbidden_token": token})
                    break
    return hits


def packet_path_errors(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row in rows:
        if evidence_status(row) != "ready":
            continue
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = row.get(field)
            if not value:
                errors.append({"blind_review_id": row["blind_review_id"], "field": field, "error": "missing_ready_packet_path"})
                continue
            if not as_abs(Path(str(value))).exists():
                errors.append(
                    {
                        "blind_review_id": row["blind_review_id"],
                        "field": field,
                        "path": value,
                        "error": "ready_packet_path_not_found",
                    }
                )
    return errors


def bucket_summary_rows(
    bucket_specs: list[dict[str, Any]],
    inventory: dict[tuple[str, str], Counter[str]],
    selected: list[dict[str, Any]],
    cell_counts: dict[tuple[str, str], dict[str, int]],
) -> list[dict[str, Any]]:
    selected_counter = Counter((row["predicate_family"], row["candidate_bucket_hidden"]) for row in selected)
    output: list[dict[str, Any]] = []
    for spec in bucket_specs:
        cell = (spec["predicate_family"], spec["bucket"])
        inv = inventory.get(cell, Counter())
        output.append(
            {
                "predicate_family": cell[0],
                "candidate_bucket": cell[1],
                "target_rows": spec["target_candidate_rows"],
                "minimum_rows": spec["minimum_candidate_rows"],
                "eligible_rows": inv.get("eligible_rows", 0),
                "retained_candidate_rows": cell_counts.get(cell, {}).get("candidate_rows_retained", 0),
                "selected_rows": selected_counter[cell],
                "deficit": max(0, int(spec["target_candidate_rows"]) - selected_counter[cell]),
                "packet_ready_eligible_rows": inv.get("packet_ready", 0),
                "asset_needed_eligible_rows": inv.get("asset_needed", 0),
                "hl_rows": inv.get("HL_rows", 0),
                "lh_rows": inv.get("LH_rows", 0),
            }
        )
    return output


def cap_audit_rows(selected: list[dict[str, Any]], caps: dict[str, int]) -> list[dict[str, Any]]:
    counters: dict[str, Counter[str]] = defaultdict(Counter)
    for row in selected:
        for cap_name, key in cap_keys(row).items():
            counters[cap_name][key] += 1
    output: list[dict[str, Any]] = []
    for cap_name, counter in sorted(counters.items()):
        limit = int(caps[cap_name])
        max_key, max_count = counter.most_common(1)[0]
        output.append(
            {
                "cap_name": cap_name,
                "limit": limit,
                "max_observed": max_count,
                "max_key": max_key,
                "unique_values": len(counter),
                "violates_cap": max_count > limit,
            }
        )
    return output


def label_schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "visible_fields": VISIBLE_FIELDS,
        "completion_fields": {
            "endpoint_identity_v6": ["clear", "uncertain", "wrong_endpoint", "not_evaluable"],
            "pair_evaluability_v6": ["evaluable", "evidence_limited", "predicate_ambiguous", "segmentation_limited", "not_evaluable"],
            "geometry_support_v6": ["supports", "contradicts", "ambiguous", "not_evaluable"],
            "relation_usefulness_v6": ["useful_nontrivial", "trivial_or_redundant", "not_a_relation", "uncertain"],
            "relation_reliability_state_v6": ["accept_reliable", "reject_unreliable", "abstain_uncertain"],
            "primary_reason_v6": [
                "geometric_support",
                "geometric_contradiction",
                "semantic_ontology_mismatch",
                "annotation_sparsity_candidate",
                "dense_relation_noise",
                "endpoint_identity_issue",
                "predicate_definition_ambiguous",
                "insufficient_evidence",
                "trivial_room_surface_or_structure",
                "other",
            ],
            "uncertainty_reason_v6": [
                "",
                "occlusion_or_view_limit",
                "mesh_or_pointcloud_limit",
                "ambiguous_contact",
                "ambiguous_vertical_order",
                "object_segmentation_issue",
                "predicate_definition_ambiguous",
                "coverage_limited",
                "other",
            ],
        },
        "primary_target": "relation_reliability_state_v6",
        "hidden_sampling_fields_are_not_label_targets": True,
        "candidate_bucket_is_not_target": True,
    }


def validate_upstream(plan_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_status = "h002_reliability_target_v6_shortcut_controlled_sampling_plan_ready_for_candidate_mining"
    if plan_summary.get("status") != expected_status:
        errors.append({"error_type": "unexpected_plan_status", "expected": expected_status, "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != "reliability_target_v6_shortcut_controlled_candidate_mining":
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "fills_new_labels", "multi_view_as_model_input", "paper_evidence_allowed", "h001_artifacts_modified"]:
        if plan_summary.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "plan_boundary_violation", "key": key, "actual": plan_summary.get("boundary", {}).get(key)})
    return errors


def report_text(summary: dict[str, Any]) -> str:
    return f"""# H002 Reliability Target V6 Shortcut-Controlled Candidate Mining

Created at: `{summary["created_at"]}`

## Boundary

- Train-only artifact.
- Labels are not filled.
- Posterior is not trained.
- Validation/test rows are not used.
- H001 artifacts are not modified.
- Multi-view remains label-audit evidence only, not posterior input.
- Candidate bucket, score fields, geometry status, and object-family cells are hidden from the label surface.

## Status

`{summary["status"]}`

## Outputs

| Item | Count |
| --- | ---: |
| selected rows | {summary["counts"]["selected_rows"]} |
| target rows | {summary["counts"]["target_rows"]} |
| bucket deficits | {summary["counts"]["bucket_deficit_total"]} |
| packet-ready rows | {summary["counts"]["packet_ready_rows"]} |
| asset-needed rows | {summary["counts"]["asset_needed_rows"]} |
| asset request rows | {summary["counts"]["asset_request_rows"]} |
| cap violations | {summary["validation"]["cap_violations"]} |
| label surface leakage hits | {summary["validation"]["label_surface_leakage_hits"]} |
| packet path errors | {summary["validation"]["packet_path_errors"]} |
| validation errors | {summary["validation"]["validation_errors"]} |

## Interpretation

The v6 shortcut-controlled candidate queue is mined under the fixed 240-row plan.
Because `{summary["counts"]["asset_needed_rows"]}` rows still need packets, the next step is asset packet generation/readiness, not label fill or posterior smoke.

## Next TODO

`{summary["next_todo"]}`
"""


def run(args: argparse.Namespace) -> dict[str, Any]:
    plan_dir = as_abs(args.plan_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(plan_dir / "summary.json")
    bucket_specs = read_json(plan_dir / "bucket_specs.json")
    cap_policy = read_json(plan_dir / "cap_policy.json")
    caps = {key: int(value) for key, value in cap_policy["caps"].items()}
    validation_errors = validate_upstream(plan_summary)
    packets = load_ready_packets([as_abs(path) for path in args.packet_manifest])
    previous_ids = load_previous_prediction_ids(args.previous_seed_audit)
    candidates, inventory, global_counts = scan_candidates(as_abs(args.hl_queue), as_abs(args.lh_queue), packets, previous_ids)
    selected, cell_counts, rejection_rows = select_candidates(candidates, bucket_specs, caps)
    selected = sorted(selected, key=lambda row: (row["predicate_family"], row["candidate_bucket_hidden"], row["blind_review_id"]))
    visible_rows = [visible_row(row) for row in selected]
    packet_ready_visible_rows = [visible_row(row) for row in selected if evidence_status(row) == "ready"]
    manifests = [manifest_row(row) for row in selected]
    asset_requests = [asset_request_row(row) for row in selected if evidence_status(row) != "ready"]
    bucket_summary = bucket_summary_rows(bucket_specs, inventory, selected, cell_counts)
    cap_summary = cap_audit_rows(selected, caps)
    field_leaks = leakage_hits(VISIBLE_FIELDS)
    value_leaks = visible_value_leakage_hits(visible_rows)
    packet_errors = packet_path_errors(selected)
    cap_violations = [row for row in cap_summary if row["violates_cap"]]
    bucket_deficit_total = sum(row["deficit"] for row in bucket_summary)
    if bucket_deficit_total:
        validation_errors.append({"error_type": "bucket_selection_deficit", "deficit": bucket_deficit_total})
    if cap_violations:
        validation_errors.append({"error_type": "cap_violation", "violations": cap_violations})
    if field_leaks or value_leaks:
        validation_errors.append({"error_type": "label_surface_leakage", "field_hits": len(field_leaks), "value_hits": len(value_leaks)})
    if packet_errors:
        validation_errors.append({"error_type": "ready_packet_path_errors", "count": len(packet_errors)})

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "label_sheet": output_dir / "v6_shortcut_controlled_label_sheet.tsv",
        "packet_ready_label_sheet": output_dir / "v6_shortcut_controlled_packet_ready_label_sheet.tsv",
        "manifest_post_label_only": output_dir / "v6_shortcut_controlled_manifest_post_label_only.jsonl",
        "selected_candidates_internal": output_dir / "selected_candidates_internal.jsonl",
        "candidate_bucket_summary": output_dir / "candidate_bucket_summary.csv",
        "cap_audit_summary": output_dir / "cap_audit_summary.csv",
        "asset_request_plan": output_dir / "asset_request_plan.jsonl",
        "label_schema": output_dir / "label_schema.json",
        "label_surface_field_leakage_hits": output_dir / "label_surface_field_leakage_hits.jsonl",
        "label_surface_value_leakage_hits": output_dir / "label_surface_value_leakage_hits.jsonl",
        "packet_path_errors": output_dir / "packet_path_errors.jsonl",
        "selection_rejections_sample": output_dir / "selection_rejections_sample.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }

    next_todo = "reliability_target_v6_shortcut_controlled_asset_packets" if asset_requests else "reliability_target_v6_shortcut_controlled_label_readiness"
    status = "h002_reliability_target_v6_shortcut_controlled_candidate_mining_ready_needs_asset_packets"
    if validation_errors:
        status = "h002_reliability_target_v6_shortcut_controlled_candidate_mining_ready_with_validation_warnings"
    elif not asset_requests:
        status = "h002_reliability_target_v6_shortcut_controlled_candidate_mining_ready_for_label_readiness"

    counts = {
        "target_rows": int(cap_policy["target_queue_rows"]),
        "selected_rows": len(selected),
        "bucket_deficit_total": bucket_deficit_total,
        "packet_ready_rows": len(packet_ready_visible_rows),
        "asset_needed_rows": len(asset_requests),
        "asset_request_rows": len(asset_requests),
        "unique_scans": len({row["scan_id"] for row in selected}),
        "unique_scene_contexts": len({row["scene_context_id"] for row in selected}),
        "unique_subject_labels": len({norm_label(row["subject_label"]) for row in selected}),
        "unique_object_labels": len({norm_label(row["object_label"]) for row in selected}),
        "family_counts": dict(sorted(Counter(str(row["predicate_family"]) for row in selected).items())),
        "bucket_counts": dict(sorted(Counter(str(row["candidate_bucket_hidden"]) for row in selected).items())),
        "family_bucket_counts": {
            f"{family}|{bucket}": count
            for (family, bucket), count in sorted(Counter((row["predicate_family"], row["candidate_bucket_hidden"]) for row in selected).items())
        },
        "coverage_counts_hidden": dict(sorted(Counter(str(row["coverage_bucket_hidden"]) for row in selected).items())),
        "source_queue_counts_hidden": dict(sorted(Counter(str(row["source_queue_hidden"]) for row in selected).items())),
        "geometry_status_counts_hidden": dict(sorted(Counter(str(row["geometry_status_hidden"]) for row in selected).items())),
        "semantic_band_counts_hidden": dict(sorted(Counter(str(row["semantic_band_hidden"]) for row in selected).items())),
        "geometry_band_counts_hidden": dict(sorted(Counter(str(row["geometry_band_hidden"]) for row in selected).items())),
        "previous_seed_prediction_ids_excluded": global_counts.get("excluded_previous_seed_prediction_id", 0),
        "source_rows_read": {
            "HL": global_counts.get("HL_rows_read", 0),
            "LH": global_counts.get("LH_rows_read", 0),
        },
        "ready_packet_manifest_entries": len(packets),
    }

    validation = {
        "validation_errors": len(validation_errors),
        "cap_violations": len(cap_violations),
        "label_surface_leakage_hits": len(field_leaks) + len(value_leaks),
        "label_surface_field_leakage_hits": len(field_leaks),
        "label_surface_value_leakage_hits": len(value_leaks),
        "packet_path_errors": len(packet_errors),
        "duplicate_prediction_ids": len(selected) - len({row["prediction_id"] for row in selected}),
        "duplicate_blind_review_ids": len(selected) - len({row["blind_review_id"] for row in selected}),
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": (
            "Mined the fixed train-only v6 shortcut-controlled candidate queue. The selected rows satisfy "
            "the 240-row bucket plan and concentration caps, but rows without packets require an asset "
            "packet/readiness step before label fill."
        ),
        "next_todo": next_todo,
        "input_paths": {
            "sampling_plan_summary": rel_path(plan_dir / "summary.json"),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
            "packet_manifests": [rel_path(path) for path in args.packet_manifest],
            "previous_seed_audit": rel_path(args.previous_seed_audit),
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
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "candidate_bucket_visible_to_labeler": False,
            "candidate_bucket_posterior_input_allowed": False,
        },
        "counts": counts,
        "validation": validation,
        "bucket_summary": bucket_summary,
        "cap_summary": cap_summary,
        "posterior_smoke_allowed": False,
    }

    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(report_text(summary), encoding="utf-8")
    write_tsv(output_paths["label_sheet"], visible_rows, VISIBLE_FIELDS)
    write_tsv(output_paths["packet_ready_label_sheet"], packet_ready_visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["manifest_post_label_only"], manifests)
    write_jsonl(output_paths["selected_candidates_internal"], selected)
    write_csv(output_paths["candidate_bucket_summary"], bucket_summary)
    write_csv(output_paths["cap_audit_summary"], cap_summary)
    write_jsonl(output_paths["asset_request_plan"], asset_requests)
    write_json(output_paths["label_schema"], label_schema())
    write_jsonl(output_paths["label_surface_field_leakage_hits"], field_leaks)
    write_jsonl(output_paths["label_surface_value_leakage_hits"], value_leaks)
    write_jsonl(output_paths["packet_path_errors"], packet_errors)
    write_jsonl(output_paths["selection_rejections_sample"], rejection_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    return summary


def main() -> None:
    summary = run(parse_args())
    counts = summary["counts"]
    validation = summary["validation"]
    print(f"status={summary['status']}")
    print(f"selected_rows={counts['selected_rows']}")
    print(f"target_rows={counts['target_rows']}")
    print(f"bucket_deficit_total={counts['bucket_deficit_total']}")
    print(f"packet_ready_rows={counts['packet_ready_rows']}")
    print(f"asset_needed_rows={counts['asset_needed_rows']}")
    print(f"cap_violations={validation['cap_violations']}")
    print(f"validation_errors={validation['validation_errors']}")
    print(f"posterior_allowed={summary['posterior_smoke_allowed']}")
    print(f"next={summary['next_todo']}")


if __name__ == "__main__":
    main()
