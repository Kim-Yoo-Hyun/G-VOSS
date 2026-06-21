#!/usr/bin/env python3
"""Mine endpoint-controlled H002 candidates for label expansion."""

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

DEFAULT_PLAN_DIR = RGA_ROOT / "endpoint_controlled_resampling_plan_all_label_ready"
DEFAULT_PLAN_SUMMARY = DEFAULT_PLAN_DIR / "summary.json"
DEFAULT_DEFICITS = DEFAULT_PLAN_DIR / "endpoint_label_deficits.csv"
DEFAULT_LABELLED_ROWS = (
    RGA_ROOT
    / "independent_support_vertical_v2_revised_sampling_raw_witness_v2_combiner_error_analysis_all_label_ready/row_diagnostics.jsonl"
)
DEFAULT_CANDIDATE_POOL = RGA_ROOT / "controlled_label_mining/candidate_pool.jsonl"
DEFAULT_PACKET_MANIFEST = RGA_ROOT / "independent_asset_packets/packet_manifest.jsonl"
DEFAULT_HL_QUEUE = RGA_ROOT / "train_hl_queue.jsonl"
DEFAULT_LH_QUEUE = RGA_ROOT / "train_lh_queue.jsonl"
DEFAULT_SCHEMA = RGA_ROOT / "independent_support_vertical_v2_sampling_protocol_decision/revised_sampling_review_schema.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "endpoint_controlled_candidate_mining"

SELECTED_FAMILIES = {"support_contact", "relative_vertical"}
SURFACE_LIKE_LABELS = {
    "floor",
    "table",
    "desk",
    "chair",
    "armchair",
    "sofa",
    "bed",
    "shelf",
    "counter",
    "countertop",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "wardrobe",
    "commode",
    "nightstand",
    "stool",
    "bench",
}
ROOM_SURFACE_LABELS = {"floor", "wall", "ceiling"}
WALL_LIKE_LABELS = {"wall", "ceiling"}

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
    "evidence_packet_status",
    "multiview_packet",
    "pointcloud_or_mesh_packet",
    "contact_or_context_sheet",
    "external_reviewer_id",
    "external_review_round",
    "endpoint_identity_external",
    "visual_pair_evaluability_external",
    "mesh_pair_evaluability_external",
    "visual_geometry_answer_external",
    "mesh_geometry_answer_external",
    "relation_informativeness_external",
    "final_relation_reliability_external",
    "uncertainty_reason_external",
    "external_label_notes",
]
FAMILY_QUESTIONS = {
    "support_contact": "Does the subject physically contact or support/attach to the object in the packet evidence?",
    "relative_vertical": "Is the subject clearly higher/lower than the object in the packet evidence?",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-summary", type=Path, default=DEFAULT_PLAN_SUMMARY)
    parser.add_argument("--deficits", type=Path, default=DEFAULT_DEFICITS)
    parser.add_argument("--labelled-rows", type=Path, default=DEFAULT_LABELLED_ROWS)
    parser.add_argument("--candidate-pool", type=Path, default=DEFAULT_CANDIDATE_POOL)
    parser.add_argument("--packet-manifest", type=Path, default=DEFAULT_PACKET_MANIFEST)
    parser.add_argument("--hl-queue", type=Path, default=DEFAULT_HL_QUEUE)
    parser.add_argument("--lh-queue", type=Path, default=DEFAULT_LH_QUEUE)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_json(path: Path, payload: dict[str, Any]) -> None:
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
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
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


def blind_review_id(row: dict[str, Any]) -> str:
    return "ftep_" + stable_hash("h002_endpoint_controlled_label_v1:" + str(row["prediction_id"]))[:12]


def asset_request_id(row: dict[str, Any]) -> str:
    key = ":".join(str(row.get(name)) for name in ["scan_id", "subgraph_id", "subject_id", "predicate_label", "object_id"])
    return "asset_" + stable_hash("h002_full_train_asset_request_v0:" + key)[:12]


def norm_label(value: Any) -> str:
    return str(value or "").strip().lower()


def is_floor_like(label: Any) -> bool:
    return norm_label(label) == "floor"


def is_wall_like(label: Any) -> bool:
    return norm_label(label) in WALL_LIKE_LABELS


def is_support_surface_like(label: Any) -> bool:
    return norm_label(label) in SURFACE_LIKE_LABELS


def is_room_surface(label: Any) -> bool:
    return norm_label(label) in ROOM_SURFACE_LABELS


def endpoint_flag_pattern(row: dict[str, Any]) -> str:
    family = str(row.get("predicate_family"))
    object_label = row.get("object_label")
    subject_label = row.get("subject_label")
    parts = [
        f"endpoint_object_floor_like_flag={int(is_floor_like(object_label))}",
        f"endpoint_object_support_surface_like_flag={int(is_support_surface_like(object_label))}",
        f"endpoint_object_wall_like_flag={int(is_wall_like(object_label))}",
        f"endpoint_subject_room_surface_flag={int(is_room_surface(subject_label))}",
        f"relative_vertical_gate={int(family == 'relative_vertical')}",
        f"support_contact_gate={int(family == 'support_contact')}",
    ]
    return "|".join(parts)


def expected_label_proxy(row: dict[str, Any]) -> str:
    queue = str(row.get("queue_kind") or row.get("queue_kind_hidden") or "")
    axis = str(row.get("candidate_axis") or row.get("candidate_axis_hidden") or "")
    geometry = str(row.get("geometry_status") or row.get("geometry_status_hidden") or "")
    verification = str(row.get("h001_verification_status") or row.get("h001_verification_status_hidden") or "")
    if queue == "LH" or axis == "semantic_underconfidence_or_missing_relation" or geometry == "satisfied" or verification == "satisfied":
        return "positive"
    if queue == "HL" or axis == "semantic_overconfidence" or geometry in {"unsatisfied", "violated"} or verification == "violated":
        return "negative"
    return "unknown"


def rank_value(row: dict[str, Any]) -> float:
    try:
        return float(row.get("semantic_rank") or row.get("semantic_rank_hidden") or 999999)
    except (TypeError, ValueError):
        return 999999.0


def score_value(row: dict[str, Any], key: str, default: float) -> float:
    try:
        value = row.get(key)
        if value is None:
            value = row.get(f"{key}_hidden")
        return float(value)
    except (TypeError, ValueError):
        return default


def sort_key(row: dict[str, Any], needed_label: str) -> tuple[Any, ...]:
    proxy = expected_label_proxy(row)
    proxy_mismatch = 0 if proxy == needed_label else 1
    rank = rank_value(row)
    p_geom = score_value(row, "p_geom_valid", 0.5)
    semantic = score_value(row, "semantic_score_norm", 0.0)
    if needed_label == "positive":
        quality = -p_geom
    else:
        quality = (p_geom, -semantic)
    return (
        proxy_mismatch,
        quality,
        rank,
        str(row.get("scan_id")),
        str(row.get("subgraph_id")),
        str(row.get("prediction_id")),
    )


def load_deficits(path: Path) -> list[dict[str, Any]]:
    rows = []
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                {
                    "endpoint_flag_pattern": row["endpoint_flag_pattern"],
                    "current_rows": int(row["rows"]),
                    "current_positive": int(row["positive"]),
                    "current_negative": int(row["negative"]),
                    "need_positive": int(row["need_positive_labels"]),
                    "need_negative": int(row["need_negative_labels"]),
                    "priority": row["priority"],
                }
            )
    return rows


def packet_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("scan_id")),
        str(row.get("subject_id")),
        str(row.get("object_id")),
        str(row.get("predicate_label")),
    )


def prediction_id(row: dict[str, Any]) -> str:
    if row.get("prediction_id"):
        return str(row["prediction_id"])
    return "open3dsg_ov:h002_train_open3dsg_full:{subgraph}:{subject}:{object}:{predicate}".format(
        subgraph=row.get("subgraph_id"),
        subject=row.get("subject_id"),
        object=row.get("object_id"),
        predicate=row.get("predicate_label"),
    )


def normalize_candidate(row: dict[str, Any], *, source_pool: str, packet: dict[str, Any] | None = None) -> dict[str, Any]:
    output = {
        "prediction_id": prediction_id(row),
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "subject_id": row.get("subject_id"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "predicate_family": row.get("predicate_family"),
        "object_id": row.get("object_id"),
        "object_label": row.get("object_label"),
        "queue_kind": row.get("queue_kind"),
        "candidate_axis": row.get("candidate_axis"),
        "proposed_audit_role": row.get("proposed_audit_role"),
        "label_match_status": row.get("label_match_status"),
        "geometry_status": row.get("geometry_status"),
        "h001_verification_status": row.get("h001_verification_status"),
        "semantic_rank": row.get("semantic_rank"),
        "rank_band": row.get("rank_band"),
        "semantic_score_norm": row.get("semantic_score_norm"),
        "semantic_score_raw": row.get("semantic_score_raw"),
        "p_geom_valid": row.get("p_geom_valid"),
        "consistency_score": row.get("consistency_score"),
        "underconfidence_score": row.get("underconfidence_score"),
        "reason_codes": row.get("reason_codes") or [],
        "matched_predicates": row.get("matched_predicates") or [],
        "matched_gt_ids": row.get("matched_gt_ids") or [],
        "source_pool": source_pool,
        "endpoint_flag_pattern": endpoint_flag_pattern(row),
    }
    output["expected_label_proxy"] = expected_label_proxy(output)
    output["blind_review_id"] = packet.get("blind_review_id") if packet else blind_review_id(output)
    output["asset_request_id"] = packet.get("asset_request_id") if packet else asset_request_id(output)
    output["packet_status"] = packet.get("packet_status") if packet else "needs_asset_generation"
    output["multiview_packet"] = packet.get("multiview_packet", "") if packet else ""
    output["pointcloud_or_mesh_packet"] = packet.get("pointcloud_or_mesh_packet", "") if packet else ""
    output["contact_or_context_sheet"] = packet.get("contact_or_context_sheet", "") if packet else ""
    return output


def visible_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "blind_review_id": row["blind_review_id"],
        "review_scope": "endpoint_controlled_support_vertical_v1",
        "scan_id": row["scan_id"],
        "scene_context_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "family_question": FAMILY_QUESTIONS.get(str(row["predicate_family"]), ""),
        "evidence_packet_status": row["packet_status"],
        "multiview_packet": row.get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": row.get("contact_or_context_sheet", ""),
        "external_reviewer_id": "",
        "external_review_round": "",
        "endpoint_identity_external": "",
        "visual_pair_evaluability_external": "",
        "mesh_pair_evaluability_external": "",
        "visual_geometry_answer_external": "",
        "mesh_geometry_answer_external": "",
        "relation_informativeness_external": "",
        "final_relation_reliability_external": "",
        "uncertainty_reason_external": "",
        "external_label_notes": "",
    }


def manifest_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_endpoint_controlled_candidate_manifest_v1",
        "batch_name": "endpoint_controlled_candidate_mining",
        "blind_review_id": row["blind_review_id"],
        "asset_request_id": row["asset_request_id"],
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "packet_paths": {
            "multiview_packet": row.get("multiview_packet", ""),
            "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", ""),
            "contact_or_context_sheet": row.get("contact_or_context_sheet", ""),
        },
        "hidden_sampling_axes_post_label_only": {
            "endpoint_flag_pattern_hidden": row["endpoint_flag_pattern"],
            "needed_label_proxy_hidden": row["needed_label"],
            "selected_source_hidden": row["selected_source"],
            "expected_label_proxy_hidden": row["expected_label_proxy"],
            "queue_kind_hidden": row.get("queue_kind"),
            "candidate_axis_hidden": row.get("candidate_axis"),
            "geometry_status_hidden": row.get("geometry_status"),
            "proposed_audit_role_hidden": row.get("proposed_audit_role"),
            "label_match_status_hidden": row.get("label_match_status"),
            "rank_band_hidden": row.get("rank_band"),
            "semantic_rank_hidden": row.get("semantic_rank"),
            "semantic_score_norm_hidden": row.get("semantic_score_norm"),
            "p_geom_valid_hidden": row.get("p_geom_valid"),
        },
        "forbidden_as_labeler_visible": [
            "endpoint_flag_pattern",
            "needed_label_proxy",
            "expected_label_proxy",
            "source score/rank",
            "p_geom_valid",
            "geometry_status",
            "queue kind",
            "proposed audit role",
            "label match status",
            "numeric witness values",
            "previous proxy labels",
            "posterior target fields",
        ],
    }


def asset_request_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_request_id": row["asset_request_id"],
        "blind_review_id": row["blind_review_id"],
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "requested_assets": [
            "subject_object_multiview_crops",
            "co_visible_view_contact_or_context_sheet",
            "object_pair_pointcloud_or_mesh_crop",
            "optional_instance_segmentation_overlay",
        ],
        "asset_policy": "Audit evidence only. Do not use as V_mv_e model input at this stage.",
        "endpoint_controlled_candidate": True,
    }


def select_from_pool(pool: list[dict[str, Any]], pattern: str, needed_label: str, limit: int, used_ids: set[str]) -> list[dict[str, Any]]:
    candidates = [
        row
        for row in pool
        if row["endpoint_flag_pattern"] == pattern
        and row["prediction_id"] not in used_ids
        and row.get("predicate_family") in SELECTED_FAMILIES
    ]
    candidates = sorted(candidates, key=lambda row: sort_key(row, needed_label))
    selected = candidates[:limit]
    used_ids.update(row["prediction_id"] for row in selected)
    return selected


def load_packet_ready_pool(candidate_pool: Path, packet_manifest: Path, labelled_ids: set[str]) -> list[dict[str, Any]]:
    packets = {packet_key(row): row for row in read_jsonl(packet_manifest)}
    rows = []
    for row in read_jsonl(candidate_pool):
        if row.get("predicate_family") not in SELECTED_FAMILIES:
            continue
        if prediction_id(row) in labelled_ids:
            continue
        packet = packets.get(packet_key(row))
        if not packet or packet.get("packet_status") not in {"ready", "ready_with_packet_caveat"}:
            continue
        rows.append(normalize_candidate(row, source_pool="candidate_pool_packet_ready", packet=packet))
    return rows


def load_asset_needed_pool(queue_paths: list[Path], labelled_ids: set[str], excluded_ids: set[str]) -> list[dict[str, Any]]:
    rows = []
    for path in queue_paths:
        for row in iter_jsonl(path):
            if row.get("predicate_family") not in SELECTED_FAMILIES:
                continue
            row_id = prediction_id(row)
            if row_id in labelled_ids or row_id in excluded_ids:
                continue
            rows.append(normalize_candidate(row, source_pool=Path(path).name, packet=None))
    return rows


def read_labelled_ids(path: Path) -> set[str]:
    return {str(row["prediction_id"]) for row in read_jsonl(path)}


def validate_boundary(plan_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors = []
    if plan_summary.get("next_todo") != "revised_sampling_endpoint_controlled_candidate_mining":
        errors.append({"error_type": "unexpected_plan_next_todo", "value": plan_summary.get("next_todo")})
    boundary = plan_summary.get("boundary", {})
    if boundary.get("validation_usage") is not False:
        errors.append({"error_type": "plan_validation_usage_not_false"})
    if boundary.get("test_usage") is not False:
        errors.append({"error_type": "plan_test_usage_not_false"})
    return errors


def mining_rows(
    deficits: list[dict[str, Any]],
    packet_ready_pool: list[dict[str, Any]],
    asset_needed_pool: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    used_ids: set[str] = set()
    selected_packet: list[dict[str, Any]] = []
    selected_asset: list[dict[str, Any]] = []
    status_rows: list[dict[str, Any]] = []
    for deficit in deficits:
        pattern = deficit["endpoint_flag_pattern"]
        for needed_label, need_key in [("positive", "need_positive"), ("negative", "need_negative")]:
            needed = int(deficit[need_key])
            if needed <= 0:
                continue
            packet_rows = select_from_pool(packet_ready_pool, pattern, needed_label, needed, used_ids)
            remaining = needed - len(packet_rows)
            asset_rows = select_from_pool(asset_needed_pool, pattern, needed_label, remaining, used_ids) if remaining > 0 else []
            for row in packet_rows:
                row["needed_label"] = needed_label
                row["selected_source"] = "packet_ready"
            for row in asset_rows:
                row["needed_label"] = needed_label
                row["selected_source"] = "asset_needed"
            selected_packet.extend(packet_rows)
            selected_asset.extend(asset_rows)
            status_rows.append(
                {
                    "endpoint_flag_pattern": pattern,
                    "needed_label": needed_label,
                    "requested": needed,
                    "selected_packet_ready": len(packet_rows),
                    "selected_asset_needed": len(asset_rows),
                    "selected_total": len(packet_rows) + len(asset_rows),
                    "residual_unfilled": needed - len(packet_rows) - len(asset_rows),
                    "current_rows": deficit["current_rows"],
                    "current_positive": deficit["current_positive"],
                    "current_negative": deficit["current_negative"],
                    "priority": deficit["priority"],
                }
            )
    return selected_packet, selected_asset, status_rows


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Endpoint-Controlled Candidate Mining",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only candidate mining.",
        "- No validation/test rows are used.",
        "- No posterior model is trained.",
        "- Endpoint fields are sampling/audit fields only, not deployable posterior inputs.",
        "- Mined labels are not target labels until the review sheet is filled and ingested.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| requested deficit labels | {summary['counts']['requested_deficit_labels']} |",
        f"| selected packet-ready candidates | {summary['counts']['selected_packet_ready']} |",
        f"| selected asset-needed candidates | {summary['counts']['selected_asset_needed']} |",
        f"| residual unfilled | {summary['counts']['residual_unfilled']} |",
        f"| packet-ready positive proxy | {summary['counts']['selected_packet_ready_by_needed_label'].get('positive', 0)} |",
        f"| packet-ready negative proxy | {summary['counts']['selected_packet_ready_by_needed_label'].get('negative', 0)} |",
        f"| asset-needed positive proxy | {summary['counts']['selected_asset_needed_by_needed_label'].get('positive', 0)} |",
        f"| asset-needed negative proxy | {summary['counts']['selected_asset_needed_by_needed_label'].get('negative', 0)} |",
        "",
        "## Decision",
        "",
        summary["decision"],
        "",
        "## Next TODO",
        "",
        "```text",
        summary["next_todo"],
        "```",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_summary)
    deficits = load_deficits(args.deficits)
    labelled_ids = read_labelled_ids(args.labelled_rows)
    validation_errors = validate_boundary(plan_summary)
    schema = read_json(args.schema)
    if list(schema.get("visible_fields", [])) != VISIBLE_FIELDS:
        validation_errors.append({"error_type": "visible_schema_mismatch"})

    packet_ready_pool = load_packet_ready_pool(args.candidate_pool, args.packet_manifest, labelled_ids)
    excluded_ids = set(labelled_ids) | {row["prediction_id"] for row in packet_ready_pool}
    asset_needed_pool = load_asset_needed_pool([args.hl_queue, args.lh_queue], labelled_ids, excluded_ids)

    selected_packet, selected_asset, deficit_status = mining_rows(deficits, packet_ready_pool, asset_needed_pool)
    requested = sum(row["requested"] for row in deficit_status)
    residual = sum(row["residual_unfilled"] for row in deficit_status)
    selected_all = selected_packet + selected_asset

    packet_sheet_rows = [visible_row(row) for row in selected_packet]
    packet_manifest_rows = [manifest_row(row) for row in selected_packet]
    asset_request_rows = [asset_request_row(row) for row in selected_asset]
    asset_needed_manifest_rows = [manifest_row(row) for row in selected_asset]
    selected_all_manifest = [manifest_row(row) for row in selected_all]

    status = (
        "h002_endpoint_controlled_candidate_mining_input_errors"
        if validation_errors
        else "h002_endpoint_controlled_candidate_mining_ready_needs_asset_packets"
        if selected_asset
        else "h002_endpoint_controlled_candidate_mining_ready_for_label_fill"
    )
    next_todo = (
        "fix_endpoint_controlled_candidate_mining_inputs"
        if validation_errors
        else "endpoint_controlled_asset_packet_generation"
        if selected_asset
        else "endpoint_controlled_label_fill"
    )
    decision = (
        "Input errors block candidate mining."
        if validation_errors
        else (
            "Endpoint-controlled candidate mining can cover the capped deficit, but the selected set "
            f"requires {len(selected_asset)} additional asset packets before label fill. Use the "
            "packet-ready sheet only as a partial batch; do not rerun posterior smoke until the "
            "asset-needed candidates are packetized, filled, and ingested."
        )
        if selected_asset
        else "All endpoint-controlled deficit candidates are packet-ready; proceed to label fill."
    )

    counts = {
        "requested_deficit_labels": requested,
        "selected_packet_ready": len(selected_packet),
        "selected_asset_needed": len(selected_asset),
        "selected_total": len(selected_all),
        "residual_unfilled": residual,
        "selected_packet_ready_by_needed_label": dict(Counter(row["needed_label"] for row in selected_packet)),
        "selected_asset_needed_by_needed_label": dict(Counter(row["needed_label"] for row in selected_asset)),
        "selected_by_endpoint_pattern": dict(Counter(row["endpoint_flag_pattern"] for row in selected_all)),
        "packet_ready_pool_rows": len(packet_ready_pool),
        "asset_needed_pool_rows": len(asset_needed_pool),
        "labelled_excluded_rows": len(labelled_ids),
    }
    summary = {
        "schema_version": "h002_endpoint_controlled_candidate_mining_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "input_paths": {
            "plan_summary": rel_path(args.plan_summary),
            "deficits": rel_path(args.deficits),
            "labelled_rows": rel_path(args.labelled_rows),
            "candidate_pool": rel_path(args.candidate_pool),
            "packet_manifest": rel_path(args.packet_manifest),
            "hl_queue": rel_path(args.hl_queue),
            "lh_queue": rel_path(args.lh_queue),
            "schema": rel_path(args.schema),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split_policy": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "posterior_trained": False,
            "endpoint_as_model_input": False,
            "paper_metric_evidence": False,
        },
        "validation_errors": validation_errors,
        "counts": counts,
        "deficit_status": deficit_status,
        "decision": decision,
        "next_todo": next_todo,
    }

    write_json(output_dir / "summary.json", summary)
    write_csv(output_dir / "deficit_status.csv", deficit_status)
    write_jsonl(output_dir / "selected_packet_ready_candidates.jsonl", selected_packet)
    write_jsonl(output_dir / "selected_asset_needed_candidates.jsonl", selected_asset)
    write_jsonl(output_dir / "selected_all_candidates_manifest_post_label_only.jsonl", selected_all_manifest)
    write_tsv(output_dir / "endpoint_controlled_packet_ready_label_sheet.tsv", packet_sheet_rows, VISIBLE_FIELDS)
    write_jsonl(output_dir / "endpoint_controlled_packet_ready_manifest_post_label_only.jsonl", packet_manifest_rows)
    write_jsonl(output_dir / "asset_request_manifest.jsonl", asset_request_rows)
    write_jsonl(output_dir / "asset_needed_manifest_post_label_only.jsonl", asset_needed_manifest_rows)
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"requested_deficit_labels={requested}")
    print(f"selected_packet_ready={len(selected_packet)}")
    print(f"selected_asset_needed={len(selected_asset)}")
    print(f"residual_unfilled={residual}")
    print(f"next={summary['next_todo']}")


if __name__ == "__main__":
    main()
