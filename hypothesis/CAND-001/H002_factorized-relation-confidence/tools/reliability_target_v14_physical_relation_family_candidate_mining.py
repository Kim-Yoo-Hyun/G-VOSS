#!/usr/bin/env python3
"""Mine H002 v14 physical relation-family candidates from train-only queues."""

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

DEFAULT_PLAN_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_sampling_plan"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v14_physical_relation_family_candidate_mining"

EXPECTED_PLAN_STATUS = "h002_reliability_target_v14_physical_relation_family_sampling_plan_ready_for_candidate_mining"
EXPECTED_PLAN_NEXT = "reliability_target_v14_physical_relation_family_candidate_mining"
STATUS_READY = "h002_reliability_target_v14_physical_relation_family_candidate_mining_ready_for_label_fill"
STATUS_ERRORS = "h002_reliability_target_v14_physical_relation_family_candidate_mining_errors"
NEXT_TODO = "reliability_target_v14_physical_relation_family_label_fill"

TARGET_ROWS = 240
HARD_ROOM_SURFACES = {"floor", "wall", "ceiling"}
STRUCTURAL_CONTEXT = {"floor", "wall", "ceiling", "room", "door", "doorframe", "window"}

VISIBLE_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "scene_context_summary_v14",
    "geometry_witness_summary_v14",
    "support_or_vertical_witness_summary_v14",
    "coverage_summary_v14",
    "endpoint_identity_summary_v14",
    "review_question_v14",
    "relation_reliability_state_v14",
    "geometry_support_state_v14",
    "relation_usefulness_state_v14",
    "endpoint_identity_state_v14",
    "coverage_state_v14",
    "primary_reason_v14",
    "uncertainty_reason_v14",
    "review_notes_v14",
]

FORBIDDEN_VISIBLE_PATTERNS = [
    "semantic",
    "rank",
    "machine_hint",
    "label_match",
    "p_geom",
    "posterior",
    "rga-",
    "semantic_geometry_bucket",
    "queue bucket",
    "queue",
    "exact_match",
    "pair_has_other_predicate",
    "no_gt_for_pair",
    "satisfied",
    "unsatisfied",
    "source score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
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


def read_csv(path: Path) -> list[dict[str, str]]:
    with as_abs(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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


def as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
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


def validate_plan(plan: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "expected": EXPECTED_PLAN_STATUS, "actual": plan.get("status")})
    if plan.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "expected": EXPECTED_PLAN_NEXT, "actual": plan.get("next_todo")})
    if plan.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan.get("validation_errors")})
    boundary = plan.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def load_plan_cells(plan_dir: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in read_csv(plan_dir / "cell_quotas.csv"):
        rows.append(
            {
                **row,
                "target_rows": int(row["target_rows"]),
                "available_queue_rows": int(row["available_queue_rows"]),
            }
        )
    return rows


def quota_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row["predicate_family"]), str(row["predicate_label"]), str(row["queue_kind"]))


def row_cell_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (str(row.get("predicate_family")), str(row.get("predicate_label")), str(row.get("queue_kind")))


def hard_filter_reason(row: dict[str, Any]) -> str | None:
    family = str(row.get("predicate_family"))
    subject = norm(row.get("subject_label"))
    obj = norm(row.get("object_label"))
    if family == "support_contact":
        if subject in HARD_ROOM_SURFACES:
            return "support_subject_hard_room_surface"
        if obj in {"wall", "ceiling"}:
            return "support_object_wall_or_ceiling"
    if family == "relative_vertical" and subject in HARD_ROOM_SURFACES and obj in HARD_ROOM_SURFACES:
        return "vertical_both_endpoints_hard_room_surface"
    if not row.get("prediction_id"):
        return "missing_prediction_id"
    return None


def directed_pair_key(row: dict[str, Any]) -> str:
    return "|".join([str(row.get("scan_id")), str(row.get("subgraph_id")), str(row.get("subject_id")), str(row.get("object_id"))])


def enrich(row: dict[str, Any], cell: dict[str, Any], source_queue_path: Path) -> dict[str, Any]:
    subject = norm(row.get("subject_label"))
    obj = norm(row.get("object_label"))
    consistency = as_float(row.get("consistency_score"))
    p_geom = as_float(row.get("p_geom_valid"))
    rank = as_int(row.get("semantic_rank"))
    return {
        **row,
        "quota_cell_id": cell["cell_id"],
        "quota_cell_role": cell["row_role"],
        "source_queue_path": rel_path(source_queue_path),
        "subject_label_norm": subject,
        "object_label_norm": obj,
        "subject_object_label_pair": f"{subject}|{obj}",
        "directed_pair_key": directed_pair_key(row),
        "subgraph_key": f"{row.get('scan_id')}|{row.get('subgraph_id')}",
        "any_hard_endpoint": subject in HARD_ROOM_SURFACES or obj in HARD_ROOM_SURFACES,
        "floor_as_object": obj == "floor",
        "structural_endpoint": subject in STRUCTURAL_CONTEXT or obj in STRUCTURAL_CONTEXT,
        "consistency_float": consistency,
        "p_geom_valid_float": p_geom,
        "semantic_rank_int": rank,
        "hash_key": stable_int(str(row.get("prediction_id"))),
    }


def read_candidate_pools(
    cell_rows: list[dict[str, Any]],
    hl_queue: Path,
    lh_queue: Path,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    cells_by_key = {quota_key(row): row for row in cell_rows}
    pools: dict[str, list[dict[str, Any]]] = {row["cell_id"]: [] for row in cell_rows}
    counts: Counter[str] = Counter()
    raw_by_cell: Counter[str] = Counter()
    hard_filtered_by_cell: Counter[str] = Counter()
    filter_reasons: Counter[str] = Counter()
    seen_predictions: set[str] = set()

    for queue_path in [hl_queue, lh_queue]:
        for _, row in iter_jsonl(queue_path):
            key = row_cell_key(row)
            if key not in cells_by_key:
                continue
            cell = cells_by_key[key]
            cell_id = cell["cell_id"]
            counts["candidate_cell_rows_seen"] += 1
            raw_by_cell[cell_id] += 1
            prediction_id = str(row.get("prediction_id"))
            if prediction_id in seen_predictions:
                filter_reasons["duplicate_prediction_id_in_input"] += 1
                continue
            reason = hard_filter_reason(row)
            if reason:
                filter_reasons[reason] += 1
                hard_filtered_by_cell[cell_id] += 1
                continue
            seen_predictions.add(prediction_id)
            pools[cell_id].append(enrich(row, cell, queue_path))
            counts["candidate_cell_rows_after_hard_filter"] += 1

    return pools, {
        "input_counts": dict(counts),
        "raw_by_cell": dict(raw_by_cell),
        "hard_filtered_by_cell": dict(hard_filtered_by_cell),
        "filter_reasons": dict(filter_reasons),
        "after_hard_filter_by_cell": {cell: len(rows) for cell, rows in pools.items()},
    }


def effective_quotas(cell_rows: list[dict[str, Any]], pools: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    quotas = {row["cell_id"]: int(row["target_rows"]) for row in cell_rows}
    adjustments: list[dict[str, Any]] = []
    for row in cell_rows:
        cell_id = row["cell_id"]
        available = len(pools[cell_id])
        target = quotas[cell_id]
        if available >= target:
            continue
        deficit = target - available
        if cell_id == "S3_support_stand_hl":
            quotas[cell_id] = available
            quotas["S1_support_lie_hl"] += deficit
            adjustments.append(
                {
                    "from_cell": cell_id,
                    "to_cell": "S1_support_lie_hl",
                    "rows_moved": deficit,
                    "reason": "standing-on HL rows all violate hard endpoint filter; move quota to lying-on HL to preserve support-contact HL mass without hard-room-surface shortcut",
                }
            )
        else:
            adjustments.append(
                {
                    "from_cell": cell_id,
                    "to_cell": "",
                    "rows_moved": deficit,
                    "reason": "quota deficit remains unresolved",
                }
            )
    return quotas, adjustments


def caps() -> dict[str, int]:
    return {
        "max_rows_per_scan": 6,
        "max_rows_per_subgraph": 3,
        "max_rows_per_directed_endpoint_pair": 1,
        "max_rows_per_subject_object_label_pair": 8,
        "max_rows_per_subject_label": 24,
        "max_rows_per_object_label": 30,
        "max_rows_with_any_hard_room_surface_endpoint": 48,
        "max_rows_with_floor_as_object": 32,
        "max_rows_per_quota_cell_from_one_scan": 2,
    }


def sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    queue_kind = str(row.get("queue_kind"))
    rank = int(row["semantic_rank_int"])
    consistency = row.get("consistency_float")
    consistency_distance = abs((consistency if consistency is not None else 0.5) - 0.5)
    rank_score = rank if queue_kind == "HL" else -rank
    return (
        row["any_hard_endpoint"],
        row["floor_as_object"],
        row["structural_endpoint"],
        -consistency_distance,
        rank_score,
        row["hash_key"],
    )


def would_exceed_caps(row: dict[str, Any], counts: dict[str, Counter], cap: dict[str, int]) -> str | None:
    if counts["scan"][str(row.get("scan_id"))] >= cap["max_rows_per_scan"]:
        return "max_rows_per_scan"
    if counts["subgraph"][str(row.get("subgraph_id"))] >= cap["max_rows_per_subgraph"]:
        return "max_rows_per_subgraph"
    if counts["directed_pair"][row["directed_pair_key"]] >= cap["max_rows_per_directed_endpoint_pair"]:
        return "max_rows_per_directed_endpoint_pair"
    if counts["label_pair"][row["subject_object_label_pair"]] >= cap["max_rows_per_subject_object_label_pair"]:
        return "max_rows_per_subject_object_label_pair"
    if counts["subject_label"][row["subject_label_norm"]] >= cap["max_rows_per_subject_label"]:
        return "max_rows_per_subject_label"
    if counts["object_label"][row["object_label_norm"]] >= cap["max_rows_per_object_label"]:
        return "max_rows_per_object_label"
    if row["any_hard_endpoint"] and counts["global"]["any_hard_endpoint"] >= cap["max_rows_with_any_hard_room_surface_endpoint"]:
        return "max_rows_with_any_hard_room_surface_endpoint"
    if row["floor_as_object"] and counts["global"]["floor_as_object"] >= cap["max_rows_with_floor_as_object"]:
        return "max_rows_with_floor_as_object"
    cell_scan = f"{row['quota_cell_id']}|{row.get('scan_id')}"
    if counts["cell_scan"][cell_scan] >= cap["max_rows_per_quota_cell_from_one_scan"]:
        return "max_rows_per_quota_cell_from_one_scan"
    return None


def update_counts(row: dict[str, Any], counts: dict[str, Counter]) -> None:
    counts["scan"][str(row.get("scan_id"))] += 1
    counts["subgraph"][str(row.get("subgraph_id"))] += 1
    counts["directed_pair"][row["directed_pair_key"]] += 1
    counts["label_pair"][row["subject_object_label_pair"]] += 1
    counts["subject_label"][row["subject_label_norm"]] += 1
    counts["object_label"][row["object_label_norm"]] += 1
    counts["cell_scan"][f"{row['quota_cell_id']}|{row.get('scan_id')}"] += 1
    counts["cell"][row["quota_cell_id"]] += 1
    if row["any_hard_endpoint"]:
        counts["global"]["any_hard_endpoint"] += 1
    if row["floor_as_object"]:
        counts["global"]["floor_as_object"] += 1


def select_candidates(pools: dict[str, list[dict[str, Any]]], quotas: dict[str, int]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    cap = caps()
    counts: dict[str, Counter] = defaultdict(Counter)
    skip_reasons: Counter[str] = Counter()
    cell_order = sorted([cell for cell, target in quotas.items() if target > 0], key=lambda cell: (len(pools[cell]) / max(quotas[cell], 1), cell))

    for cell_id in cell_order:
        target = quotas[cell_id]
        chosen = 0
        for row in sorted(pools[cell_id], key=sort_key):
            if chosen >= target:
                break
            reason = would_exceed_caps(row, counts, cap)
            if reason:
                skip_reasons[f"{cell_id}:{reason}"] += 1
                continue
            selected.append(row)
            update_counts(row, counts)
            chosen += 1

    deficits = {cell: quotas[cell] - counts["cell"][cell] for cell in quotas if quotas[cell] - counts["cell"][cell] > 0}
    return selected, {
        "caps": cap,
        "cell_order": cell_order,
        "skip_reasons": dict(skip_reasons),
        "cell_selected": dict(counts["cell"]),
        "deficits": deficits,
        "scan_counts_top": dict(counts["scan"].most_common(10)),
        "subgraph_counts_top": dict(counts["subgraph"].most_common(10)),
        "label_pair_counts_top": dict(counts["label_pair"].most_common(10)),
        "subject_label_counts_top": dict(counts["subject_label"].most_common(10)),
        "object_label_counts_top": dict(counts["object_label"].most_common(10)),
        "global_counts": dict(counts["global"]),
    }


def read_raw_features(match_rows: Path, prediction_ids: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    counts = {"requested": len(prediction_ids), "found": 0, "match_rows_scanned": 0}
    for _, row in iter_jsonl(match_rows):
        counts["match_rows_scanned"] += 1
        prediction_id = str((row.get("identity") or {}).get("prediction_id") or row.get("prediction_id"))
        if prediction_id not in prediction_ids:
            continue
        found[prediction_id] = (row.get("geometry") or {}).get("raw_features") or {}
        counts["found"] = len(found)
        if len(found) >= len(prediction_ids):
            break
    return found, counts


def bin_value(value: float | None, cuts: tuple[float, float], labels: tuple[str, str, str]) -> str:
    if value is None:
        return "unknown"
    if value <= cuts[0]:
        return labels[0]
    if value <= cuts[1]:
        return labels[1]
    return labels[2]


def distance_bin(raw: dict[str, Any]) -> str:
    value = as_float(raw.get("normalized_distance_xy"))
    if value is None:
        value = as_float(raw.get("distance_xy"))
    return bin_value(value, (0.30, 0.70), ("tight horizontal separation", "moderate horizontal separation", "wide horizontal separation"))


def overlap_bin(raw: dict[str, Any]) -> str:
    values = [
        as_float(raw.get("projected_iou_xy")),
        as_float(raw.get("projected_subject_overlap_ratio")),
        as_float(raw.get("projected_object_overlap_ratio")),
    ]
    values = [value for value in values if value is not None]
    if not values:
        return "unknown footprint overlap"
    value = max(values)
    if value >= 0.35:
        return "large footprint overlap"
    if value >= 0.10:
        return "partial footprint overlap"
    return "little footprint overlap"


def vertical_relation_bin(raw: dict[str, Any]) -> str:
    value = as_float(raw.get("normalized_center_delta_z"))
    if value is None:
        value = as_float(raw.get("center_delta_z"))
    if value is None:
        return "unknown vertical ordering"
    if value > 0.20:
        return "subject center appears above object center"
    if value < -0.20:
        return "subject center appears below object center"
    return "subject and object appear in a similar height band"


def support_gap_bin(raw: dict[str, Any]) -> str:
    value = as_float(raw.get("vertical_gap_subject_on_object"))
    if value is None:
        return "unknown support gap"
    abs_value = abs(value)
    if abs_value <= 0.05:
        return "near-contact vertical gap"
    if abs_value <= 0.25:
        return "small vertical gap"
    return "large vertical gap"


def relation_family_visible(row: dict[str, Any]) -> str:
    if row.get("predicate_family") == "support_contact":
        return "support/contact relation"
    if row.get("predicate_family") == "relative_vertical":
        return "relative vertical relation"
    return "physical relation"


def visible_row(row: dict[str, Any], raw: dict[str, Any], review_card: str) -> dict[str, str]:
    family = str(row.get("predicate_family"))
    relation = f"{row.get('subject_label')} {row.get('predicate_label')} {row.get('object_label')}"
    shared_geometry = f"{distance_bin(raw)}; {overlap_bin(raw)}; {vertical_relation_bin(raw)}"
    if family == "support_contact":
        witness = f"support/contact cue uses footprint overlap and vertical gap bins: {overlap_bin(raw)}; {support_gap_bin(raw)}"
        question = "Should this support/contact relation be trusted as a scene-graph edge under the visible 3D layout evidence?"
    else:
        witness = f"vertical relation cue uses object-center ordering and height-band separation: {vertical_relation_bin(raw)}"
        question = "Should this vertical relation be trusted as a scene-graph edge under the visible 3D layout evidence?"
    return {
        "blind_review_id": "ftv14p_" + stable_hash(str(row.get("prediction_id")))[:12],
        "review_card": review_card,
        "candidate_relation": relation,
        "subject_label": str(row.get("subject_label")),
        "predicate_label": str(row.get("predicate_label")),
        "object_label": str(row.get("object_label")),
        "relation_family_visible": relation_family_visible(row),
        "scene_context_summary_v14": "candidate relation from a physical-relation audit sheet; review only the relation and visible 3D layout evidence",
        "geometry_witness_summary_v14": shared_geometry,
        "support_or_vertical_witness_summary_v14": witness,
        "coverage_summary_v14": "3D layout witness is available; image or multi-view evidence is not used as model input in this stage",
        "endpoint_identity_summary_v14": "verify whether the visible subject and object labels make the directed relation meaningful",
        "review_question_v14": question,
        "relation_reliability_state_v14": "",
        "geometry_support_state_v14": "",
        "relation_usefulness_state_v14": "",
        "endpoint_identity_state_v14": "",
        "coverage_state_v14": "",
        "primary_reason_v14": "",
        "uncertainty_reason_v14": "",
        "review_notes_v14": "",
    }


def hidden_row(row: dict[str, Any], raw: dict[str, Any], visible: dict[str, str], fallback_applied: bool) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v14_physical_relation_family_candidate_hidden_v1",
        "blind_review_id": visible["blind_review_id"],
        "prediction_id": row.get("prediction_id"),
        "split": "train",
        "source_id": row.get("source_id"),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_family": row.get("predicate_family"),
        "predicate_label": row.get("predicate_label"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "quota_cell_id_hidden": row.get("quota_cell_id"),
        "quota_cell_role_hidden": row.get("quota_cell_role"),
        "fallback_applied_hidden": fallback_applied,
        "source_queue_hidden": row.get("bucket_top100"),
        "queue_kind_hidden": row.get("queue_kind"),
        "semantic_geometry_bucket_hidden": row.get("semantic_geometry_bucket"),
        "semantic_rank_hidden": row.get("semantic_rank"),
        "rank_band_hidden": row.get("rank_band"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm"),
        "semantic_score_raw_hidden": row.get("semantic_score_raw"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "consistency_score_hidden": row.get("consistency_score"),
        "geometry_status_hidden": row.get("geometry_status"),
        "h001_verification_status_hidden": row.get("h001_verification_status"),
        "label_match_status_hidden": row.get("label_match_status"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket"),
        "machine_hint_hidden": row.get("machine_hint"),
        "matched_gt_ids_hidden": row.get("matched_gt_ids"),
        "matched_predicates_hidden": row.get("matched_predicates"),
        "reason_codes_hidden": row.get("reason_codes"),
        "subject_object_label_pair_hidden": row.get("subject_object_label_pair"),
        "directed_pair_key_hidden": row.get("directed_pair_key"),
        "any_hard_endpoint_hidden": row.get("any_hard_endpoint"),
        "floor_as_object_hidden": row.get("floor_as_object"),
        "raw_features_hidden": raw,
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
        f"- Relation family: {row['relation_family_visible']}",
        f"- {row['geometry_witness_summary_v14']}",
        f"- {row['support_or_vertical_witness_summary_v14']}",
        f"- {row['coverage_summary_v14']}",
        f"- {row['endpoint_identity_summary_v14']}",
        "",
        "## Question",
        "",
        row["review_question_v14"],
        "",
        "## Fill Fields",
        "",
        "- relation_reliability_state_v14:",
        "- geometry_support_state_v14:",
        "- relation_usefulness_state_v14:",
        "- endpoint_identity_state_v14:",
        "- coverage_state_v14:",
        "- primary_reason_v14:",
        "- uncertainty_reason_v14:",
        "- review_notes_v14:",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def leakage_hits(visible_rows: list[dict[str, str]], review_card_dir: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for row in visible_rows:
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


def cell_summary_rows(selected: list[dict[str, Any]], quotas: dict[str, int], pools: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    by_cell: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in selected:
        by_cell[row["quota_cell_id"]].append(row)
    rows: list[dict[str, Any]] = []
    for cell_id in sorted(quotas):
        cell_rows = by_cell[cell_id]
        rows.append(
            {
                "cell_id": cell_id,
                "effective_target_rows": quotas[cell_id],
                "selected_rows": len(cell_rows),
                "pool_rows_after_hard_filter": len(pools[cell_id]),
                "unique_scans": len({str(row.get("scan_id")) for row in cell_rows}),
                "unique_subgraphs": len({str(row.get("subgraph_id")) for row in cell_rows}),
                "unique_label_pairs": len({row["subject_object_label_pair"] for row in cell_rows}),
                "any_hard_endpoint_rows": sum(1 for row in cell_rows if row["any_hard_endpoint"]),
                "floor_as_object_rows": sum(1 for row in cell_rows if row["floor_as_object"]),
                "top_label_pairs_hidden": json.dumps(dict(Counter(row["subject_object_label_pair"] for row in cell_rows).most_common(8)), sort_keys=True),
            }
        )
    return rows


def validate_outputs(
    visible_rows: list[dict[str, str]],
    hidden_rows: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    cell_rows: list[dict[str, Any]],
    effective: dict[str, int],
    selection: dict[str, Any],
    raw_feature_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if len(visible_rows) != TARGET_ROWS:
        errors.append({"error_type": "unexpected_visible_row_count", "expected": TARGET_ROWS, "actual": len(visible_rows)})
    if len(hidden_rows) != TARGET_ROWS:
        errors.append({"error_type": "unexpected_hidden_row_count", "expected": TARGET_ROWS, "actual": len(hidden_rows)})
    if len(selected) != TARGET_ROWS:
        errors.append({"error_type": "unexpected_selected_row_count", "expected": TARGET_ROWS, "actual": len(selected)})
    if selection["deficits"]:
        errors.append({"error_type": "quota_deficits_after_selection", "deficits": selection["deficits"]})
    if raw_feature_counts.get("found") != raw_feature_counts.get("requested"):
        errors.append({"error_type": "raw_feature_join_incomplete", **raw_feature_counts})
    blind_ids = [row["blind_review_id"] for row in visible_rows]
    if len(set(blind_ids)) != len(blind_ids):
        errors.append({"error_type": "duplicate_blind_review_id"})
    prediction_ids = [str(row["prediction_id"]) for row in hidden_rows]
    if len(set(prediction_ids)) != len(prediction_ids):
        errors.append({"error_type": "duplicate_prediction_id"})
    directed_pairs = [str(row["directed_pair_key_hidden"]) for row in hidden_rows]
    if len(set(directed_pairs)) != len(directed_pairs):
        errors.append({"error_type": "duplicate_directed_pair"})
    expected_cells = {row["cell_id"] for row in cell_rows}
    selected_cells = {str(row["quota_cell_id_hidden"]) for row in hidden_rows}
    if selected_cells - expected_cells:
        errors.append({"error_type": "unexpected_selected_cells", "cells": sorted(selected_cells - expected_cells)})
    for cell_id, expected in effective.items():
        actual = sum(1 for row in hidden_rows if row["quota_cell_id_hidden"] == cell_id)
        if actual != expected:
            errors.append({"error_type": "cell_count_mismatch", "cell_id": cell_id, "expected": expected, "actual": actual})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V14 Physical Relation-Family Candidate Mining",
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
        f"support_contact_rows = {counts['support_contact_rows']}",
        f"relative_vertical_rows = {counts['relative_vertical_rows']}",
        f"unique_scans = {counts['unique_scans']}",
        f"unique_subgraphs = {counts['unique_subgraphs']}",
        f"visible_leakage_hits = {counts['visible_leakage_hits']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Quota Adjustment",
        "",
    ]
    if summary["quota_adjustments"]:
        for item in summary["quota_adjustments"]:
            lines.append(f"- `{item['from_cell']}` -> `{item['to_cell']}`: {item['rows_moved']} rows. {item['reason']}")
    else:
        lines.append("- No quota adjustment was needed.")
    lines.extend(
        [
            "",
            "## Guardrail",
            "",
            "Queue kind, source rank, machine hint, label-match status, and raw scores are hidden audit fields only. They are not exposed in the label sheet or review cards.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
            "Posterior smoke remains blocked until labels are filled, ingested, and pass target-independence audit.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    plan_dir = as_abs(args.plan_dir)
    output_dir = as_abs(args.output_dir)
    review_card_dir = output_dir / "review_cards_v14"
    output_dir.mkdir(parents=True, exist_ok=True)

    plan = read_json(plan_dir / "summary.json")
    validation_errors = validate_plan(plan)
    cell_rows = load_plan_cells(plan_dir)
    pools, pool_counts = read_candidate_pools(cell_rows, args.hl_queue, args.lh_queue)
    effective, quota_adjustments = effective_quotas(cell_rows, pools)
    selected, selection = select_candidates(pools, effective)
    selected_ids = {str(row.get("prediction_id")) for row in selected}
    raw_feature_map, raw_feature_counts = read_raw_features(args.match_rows, selected_ids)

    fallback_cells = {item["to_cell"] for item in quota_adjustments if item.get("to_cell")}
    visible_rows: list[dict[str, str]] = []
    hidden_rows: list[dict[str, Any]] = []
    internal_rows: list[dict[str, Any]] = []
    for row in selected:
        prediction_id = str(row.get("prediction_id"))
        blind_id = "ftv14p_" + stable_hash(prediction_id)[:12]
        review_card = f"review_cards_v14/{blind_id}.md"
        raw = raw_feature_map.get(prediction_id, {})
        visible = visible_row(row, raw, review_card)
        hidden = hidden_row(row, raw, visible, fallback_applied=row["quota_cell_id"] in fallback_cells)
        visible_rows.append(visible)
        hidden_rows.append(hidden)
        internal_rows.append({**row, "blind_review_id": visible["blind_review_id"], "raw_features_joined": bool(raw)})
        write_review_card(review_card_dir / f"{visible['blind_review_id']}.md", visible)

    leakage = leakage_hits(visible_rows, review_card_dir)
    validation_errors.extend(validate_outputs(visible_rows, hidden_rows, selected, cell_rows, effective, selection, raw_feature_counts))
    if leakage:
        validation_errors.append({"error_type": "visible_leakage_hits_present", "count": len(leakage)})

    cell_summaries = cell_summary_rows(selected, effective, pools)
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "label_ready_sheet": output_dir / "label_ready_sheet_v14.tsv",
        "hidden_audit_manifest": output_dir / "hidden_audit_manifest_v14.jsonl",
        "selected_candidates_internal": output_dir / "selected_candidates_internal.jsonl",
        "cell_summary": output_dir / "cell_summary.csv",
        "quota_adjustments": output_dir / "quota_adjustments.jsonl",
        "cap_summary": output_dir / "cap_summary.json",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    counts = {
        "selected_rows": len(selected),
        "support_contact_rows": sum(1 for row in selected if row.get("predicate_family") == "support_contact"),
        "relative_vertical_rows": sum(1 for row in selected if row.get("predicate_family") == "relative_vertical"),
        "unique_scans": len({str(row.get("scan_id")) for row in selected}),
        "unique_subgraphs": len({str(row.get("subgraph_id")) for row in selected}),
        "unique_directed_pairs": len({row["directed_pair_key"] for row in selected}),
        "unique_label_pairs": len({row["subject_object_label_pair"] for row in selected}),
        "raw_feature_joined_rows": sum(1 for row in internal_rows if row["raw_features_joined"]),
        "visible_leakage_hits": len(leakage),
        "any_hard_endpoint_rows": sum(1 for row in selected if row["any_hard_endpoint"]),
        "floor_as_object_rows": sum(1 for row in selected if row["floor_as_object"]),
    }
    summary = {
        "schema_version": "h002_reliability_target_v14_physical_relation_family_candidate_mining_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "plan_summary": rel_path(plan_dir / "summary.json"),
            "cell_quotas": rel_path(plan_dir / "cell_quotas.csv"),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
            "match_rows": rel_path(args.match_rows),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "effective_quotas": effective,
        "quota_adjustments": quota_adjustments,
        "pool_counts": pool_counts,
        "raw_feature_join": raw_feature_counts,
        "selection": selection,
        "counts": counts,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "hidden_fields_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_json(output_paths["summary"], summary)
    write_tsv(output_paths["label_ready_sheet"], visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_paths["hidden_audit_manifest"], hidden_rows)
    write_jsonl(output_paths["selected_candidates_internal"], internal_rows)
    write_csv(output_paths["cell_summary"], cell_summaries)
    write_jsonl(output_paths["quota_adjustments"], quota_adjustments)
    write_json(output_paths["cap_summary"], selection)
    write_jsonl(output_paths["visible_leakage_hits"], leakage)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(f"status={summary['status']}")
    print(f"selected_rows={counts['selected_rows']}")
    print(f"support_contact_rows={counts['support_contact_rows']}")
    print(f"relative_vertical_rows={counts['relative_vertical_rows']}")
    print(f"unique_scans={counts['unique_scans']}")
    print(f"raw_feature_joined_rows={counts['raw_feature_joined_rows']}")
    print(f"visible_leakage_hits={counts['visible_leakage_hits']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
