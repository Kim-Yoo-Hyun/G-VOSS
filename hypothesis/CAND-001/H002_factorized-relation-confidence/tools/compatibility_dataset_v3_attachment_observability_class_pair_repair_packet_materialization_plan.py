#!/usr/bin/env python3
"""Plan R7 attachment-observability packet materialization for class-pair repair rows."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
ARTIFACT_ROOT = H2_ROOT / "artifacts"

DEFAULT_CANDIDATE_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining"
)
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan"
)

EXPECTED_CANDIDATE_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_candidate_mining_ready_for_packet_materialization_plan"
)
EXPECTED_CANDIDATE_NEXT = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan_ready"
)
STATUS_PARTIAL = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan_partial_needs_gap_audit"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan_input_or_output_errors"
)
NEXT_TODO_READY = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization"
)
NEXT_TODO_PARTIAL = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_gap_audit"
)

PRIMARY_PREDICATES = ("attached to", "hanging on")
DIAGNOSTIC_PREDICATES = ("connected to",)
REQUIRED_ROWS = 480
REQUIRED_PER_PREDICATE = {"attached to": 240, "hanging on": 240}
REQUIRED_PER_ROLE_PER_PREDICATE = {
    "accept_proxy_supported_candidate": 80,
    "reject_proxy_contradicted_candidate": 120,
    "uncertain_proxy": 40,
}

INSTANCE_RE = re.compile(
    r"^instance_(?P<instance_id>\d+)_class_(?P<label>.+?)_"
    r"(?P<kind>croped_view|view)(?P<view_rank>\d+)"
    r"(?:_score_(?P<score>[-+0-9.eE]+)_ratio_(?P<ratio>[-+0-9.eE]+))?"
    r"(?:_(?P<frame_id>\d+))?_(?P<side>[AB])\.jpg$"
)

VISIBLE_REVIEW_FIELDS = [
    "review_observability_label",
    "review_relation_label",
    "review_evidence_quality",
    "review_endpoint_identity",
    "review_notes",
]

FORBIDDEN_VISIBLE_SUBSTRINGS = (
    "scan_id",
    "subgraph_id",
    "subject_id",
    "object_id",
    "candidate_id",
    "prediction_id",
    "directed_pair_id",
    "packet_request_id",
    "path",
    "rank",
    "source",
    "proxy",
    "gt_",
    "geometry_bucket",
    "coverage_proxy",
    "uncertainty_bucket",
    "hidden",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
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
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_candidate_inputs(
    summary: dict[str, Any],
    candidates: list[dict[str, Any]],
    packet_requests: list[dict[str, Any]],
    candidate_errors: list[dict[str, Any]],
    scan_root: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_CANDIDATE_STATUS:
        errors.append({"error_type": "unexpected_candidate_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_CANDIDATE_NEXT:
        errors.append({"error_type": "unexpected_candidate_next", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "candidate_validation_errors_present", "actual": summary.get("validation_errors")})
    if candidate_errors:
        errors.append({"error_type": "candidate_validation_error_rows_present", "rows": len(candidate_errors)})
    if not scan_root.exists():
        errors.append({"error_type": "missing_scan_root", "path": rel_path(scan_root)})

    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "fills_labels",
        "materializes_model_rows",
        "packet_materialization_started",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "candidate_boundary_not_false", "key": key, "actual": boundary.get(key)})

    if len(candidates) != REQUIRED_ROWS:
        errors.append({"error_type": "unexpected_candidate_row_count", "actual": len(candidates), "expected": REQUIRED_ROWS})
    if len(packet_requests) != REQUIRED_ROWS:
        errors.append({"error_type": "unexpected_packet_request_count", "actual": len(packet_requests), "expected": REQUIRED_ROWS})

    candidate_ids = [row.get("candidate_id") for row in candidates]
    request_ids = [row.get("candidate_id") for row in packet_requests]
    if len(candidate_ids) != len(set(candidate_ids)):
        errors.append({"error_type": "duplicate_candidate_ids", "actual_unique": len(set(candidate_ids))})
    if set(candidate_ids) != set(request_ids):
        errors.append({"error_type": "candidate_packet_request_id_mismatch"})

    pred_counts = Counter(str(row.get("predicate_label")) for row in candidates)
    for predicate, expected in REQUIRED_PER_PREDICATE.items():
        if pred_counts.get(predicate, 0) != expected:
            errors.append(
                {
                    "error_type": "unexpected_predicate_count",
                    "predicate": predicate,
                    "actual": pred_counts.get(predicate, 0),
                    "expected": expected,
                }
            )
    for predicate in DIAGNOSTIC_PREDICATES:
        if pred_counts.get(predicate, 0) != 0:
            errors.append({"error_type": "diagnostic_predicate_in_primary_candidate_rows", "predicate": predicate})

    for predicate in PRIMARY_PREDICATES:
        for role, expected in REQUIRED_PER_ROLE_PER_PREDICATE.items():
            actual = sum(
                1
                for row in candidates
                if row.get("predicate_label") == predicate and row.get("reliability_proxy_role") == role
            )
            if actual != expected:
                errors.append(
                    {
                        "error_type": "unexpected_predicate_role_count",
                        "predicate": predicate,
                        "role": role,
                        "actual": actual,
                        "expected": expected,
                    }
                )
    return errors


def empty_instance_record() -> dict[str, Any]:
    return {
        "crop_count": 0,
        "origin_count": 0,
        "crop_view_ranks": set(),
        "origin_view_ranks": set(),
        "origin_frame_ids": set(),
        "crop_scores": [],
        "crop_ratios": [],
        "sample_paths": [],
    }


def scan_inventory(scan_id: str, scan_root: Path, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    if scan_id in cache:
        return cache[scan_id]
    scan_dir = scan_root / scan_id
    multiview_dir = scan_dir / "multi_view"
    by_instance: dict[int, dict[str, Any]] = defaultdict(empty_instance_record)
    if multiview_dir.exists():
        for image_path in sorted(multiview_dir.glob("*.jpg")):
            match = INSTANCE_RE.match(image_path.name)
            if not match:
                continue
            instance_id = int(match.group("instance_id"))
            record = by_instance[instance_id]
            kind = match.group("kind")
            view_rank = match.group("view_rank")
            frame_id = match.group("frame_id")
            if kind == "croped_view":
                record["crop_count"] += 1
                if view_rank:
                    record["crop_view_ranks"].add(view_rank)
                if match.group("score"):
                    record["crop_scores"].append(float(match.group("score")))
                if match.group("ratio"):
                    record["crop_ratios"].append(float(match.group("ratio")))
            else:
                record["origin_count"] += 1
                if view_rank:
                    record["origin_view_ranks"].add(view_rank)
                if frame_id:
                    record["origin_frame_ids"].add(frame_id)
            if len(record["sample_paths"]) < 12:
                record["sample_paths"].append(rel_path(image_path))
    inventory = {
        "scan_exists": scan_dir.exists(),
        "multiview_dir_exists": multiview_dir.exists(),
        "semseg_exists": (scan_dir / "semseg.v2.json").exists(),
        "instance_mesh_exists": (scan_dir / "labels.instances.annotated.v2.ply").exists(),
        "sequence_zip_exists": (scan_dir / "sequence.zip").exists(),
        "sequence_dir_exists": (scan_dir / "sequence").exists(),
        "scan_dir": rel_path(scan_dir),
        "multiview_dir": rel_path(multiview_dir),
        "semseg_path": rel_path(scan_dir / "semseg.v2.json"),
        "instance_mesh_path": rel_path(scan_dir / "labels.instances.annotated.v2.ply"),
        "sequence_zip_path": rel_path(scan_dir / "sequence.zip"),
        "by_instance": by_instance,
    }
    cache[scan_id] = inventory
    return inventory


def serialize_instance_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "crop_count": int(record.get("crop_count", 0)),
        "origin_count": int(record.get("origin_count", 0)),
        "total_image_count": int(record.get("crop_count", 0)) + int(record.get("origin_count", 0)),
        "crop_view_rank_count": len(record.get("crop_view_ranks", set())),
        "origin_view_rank_count": len(record.get("origin_view_ranks", set())),
        "origin_frame_count": len(record.get("origin_frame_ids", set())),
        "sample_paths": list(record.get("sample_paths", [])),
    }


def evidence_for_row(row: dict[str, Any], scan_root: Path, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
    scan_id = str(row["scan_id"])
    subject_id = int(row["subject_id"])
    object_id = int(row["object_id"])
    scan = scan_inventory(scan_id, scan_root, cache)
    subject = scan["by_instance"].get(subject_id, empty_instance_record())
    obj = scan["by_instance"].get(object_id, empty_instance_record())

    subject_crop_ranks = subject.get("crop_view_ranks", set())
    object_crop_ranks = obj.get("crop_view_ranks", set())
    subject_origin_ranks = subject.get("origin_view_ranks", set())
    object_origin_ranks = obj.get("origin_view_ranks", set())
    subject_frames = subject.get("origin_frame_ids", set())
    object_frames = obj.get("origin_frame_ids", set())
    shared_crop_view_ranks = subject_crop_ranks & object_crop_ranks
    shared_origin_view_ranks = subject_origin_ranks & object_origin_ranks
    shared_origin_frames = subject_frames & object_frames
    subject_total = int(subject.get("crop_count", 0)) + int(subject.get("origin_count", 0))
    object_total = int(obj.get("crop_count", 0)) + int(obj.get("origin_count", 0))
    both_multiview = subject_total > 0 and object_total > 0
    shared_view_ready = bool(shared_crop_view_ranks or shared_origin_view_ranks)
    shared_frame_ready = bool(shared_origin_frames)
    mesh_ready = bool(scan["instance_mesh_exists"] and scan["semseg_exists"])
    sequence_ready = bool(scan["sequence_zip_exists"] or scan["sequence_dir_exists"])

    if not scan["scan_exists"] or not mesh_ready:
        tier = "T4_not_ready_gap_audit"
    elif both_multiview and shared_view_ready:
        tier = "T1_pair_multiview_ready"
    elif both_multiview:
        tier = "T2_object_multiview_mesh_ready"
    elif mesh_ready:
        tier = "T3_mesh_only_or_limited_view"
    else:
        tier = "T4_not_ready_gap_audit"

    return {
        "candidate_id": row["candidate_id"],
        "predicate_label": row["predicate_label"],
        "reliability_proxy_role": row["reliability_proxy_role"],
        "exact_class_pair_id": row["exact_class_pair_id"],
        "scan_id": scan_id,
        "subject_id": subject_id,
        "object_id": object_id,
        "scan_exists": bool(scan["scan_exists"]),
        "mesh_ready": mesh_ready,
        "semseg_exists": bool(scan["semseg_exists"]),
        "instance_mesh_exists": bool(scan["instance_mesh_exists"]),
        "sequence_ready": sequence_ready,
        "multiview_dir_exists": bool(scan["multiview_dir_exists"]),
        "subject_image_count": subject_total,
        "object_image_count": object_total,
        "subject_crop_count": int(subject.get("crop_count", 0)),
        "object_crop_count": int(obj.get("crop_count", 0)),
        "subject_origin_count": int(subject.get("origin_count", 0)),
        "object_origin_count": int(obj.get("origin_count", 0)),
        "both_multiview_ready": both_multiview,
        "shared_crop_view_rank_count": len(shared_crop_view_ranks),
        "shared_origin_view_rank_count": len(shared_origin_view_ranks),
        "shared_origin_frame_count": len(shared_origin_frames),
        "shared_view_ready": shared_view_ready,
        "shared_frame_ready": shared_frame_ready,
        "evidence_tier": tier,
        "subject_assets": serialize_instance_record(subject),
        "object_assets": serialize_instance_record(obj),
        "scan_paths": {
            "scan_dir": scan["scan_dir"],
            "multiview_dir": scan["multiview_dir"],
            "semseg_path": scan["semseg_path"],
            "instance_mesh_path": scan["instance_mesh_path"],
            "sequence_zip_path": scan["sequence_zip_path"],
        },
    }


def visible_plan_row(index: int, row: dict[str, Any], packet_request: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    plan_id = f"r7attach_review_{index:04d}"
    payload = {
        "review_row_id": plan_id,
        "candidate_relation": packet_request.get("labeler_visible_relation"),
        "subject_label": row.get("subject_label"),
        "predicate_label": row.get("predicate_label"),
        "object_label": row.get("object_label"),
        "relation_route": "attachment_observability",
        "review_order": index,
        "packet_scope": "pair_multiview_mesh_contact_if_available",
        "evidence_tier": evidence["evidence_tier"],
        "subject_image_count": evidence["subject_image_count"],
        "object_image_count": evidence["object_image_count"],
        "pair_shared_view_count": evidence["shared_crop_view_rank_count"]
        + evidence["shared_origin_view_rank_count"],
        "pair_shared_frame_count": evidence["shared_origin_frame_count"],
        "mesh_ready": evidence["mesh_ready"],
        "sequence_ready": evidence["sequence_ready"],
        "review_task": (
            "First judge whether visual/mesh evidence is sufficient. "
            "If observable, judge whether the relation is reliable; otherwise abstain."
        ),
        "review_observability_label": "",
        "review_relation_label": "",
        "review_evidence_quality": "",
        "review_endpoint_identity": "",
        "review_notes": "",
    }
    return payload


def hidden_manifest_row(
    visible: dict[str, Any],
    row: dict[str, Any],
    packet_request: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    hidden_keys = [
        "candidate_id",
        "prediction_id",
        "scan_id",
        "subgraph_id",
        "directed_pair_id",
        "subject_id",
        "object_id",
        "exact_class_pair_id",
        "reliability_proxy_role",
        "rank_band",
        "geometry_bucket",
        "coverage_proxy",
        "uncertainty_bucket",
        "gt_label_match_status",
        "raw_feature_join_state",
        "provisional_status_hidden",
        "cell_id_hidden",
        "anchor_bucket_hidden",
        "capacity_evidence_tier",
    ]
    payload = {
        "review_row_id": visible["review_row_id"],
        "packet_request_id": packet_request.get("packet_request_id"),
        "packet_scope": packet_request.get("packet_scope"),
        "hidden_exact_class_pair_id": packet_request.get("hidden_exact_class_pair_id"),
        "hidden_proxy_role": packet_request.get("hidden_proxy_role"),
        "evidence_tier": evidence["evidence_tier"],
        "evidence_counts": {
            "subject_image_count": evidence["subject_image_count"],
            "object_image_count": evidence["object_image_count"],
            "shared_view_rank_count": evidence["shared_crop_view_rank_count"]
            + evidence["shared_origin_view_rank_count"],
            "shared_frame_count": evidence["shared_origin_frame_count"],
            "mesh_ready": evidence["mesh_ready"],
            "sequence_ready": evidence["sequence_ready"],
        },
        "asset_paths": evidence["scan_paths"],
        "subject_asset_samples": evidence["subject_assets"].get("sample_paths", []),
        "object_asset_samples": evidence["object_assets"].get("sample_paths", []),
    }
    for key in hidden_keys:
        if key in row:
            payload[key] = row[key]
    return payload


def visible_schema() -> dict[str, Any]:
    return {
        "schema_version": "r7_attachment_observability_visible_label_surface_v1",
        "visible_fields": [
            "review_row_id",
            "candidate_relation",
            "subject_label",
            "predicate_label",
            "object_label",
            "relation_route",
            "review_order",
            "packet_scope",
            "evidence_tier",
            "subject_image_count",
            "object_image_count",
            "pair_shared_view_count",
            "pair_shared_frame_count",
            "mesh_ready",
            "sequence_ready",
            *VISIBLE_REVIEW_FIELDS,
        ],
        "review_label_options": {
            "review_observability_label": ["observable", "not_observable", "uncertain"],
            "review_relation_label": ["accept", "reject", "abstain"],
            "review_evidence_quality": ["sufficient", "partial", "poor"],
            "review_endpoint_identity": ["clear", "ambiguous", "wrong_endpoint"],
        },
        "forbidden_visible_fields": list(FORBIDDEN_VISIBLE_SUBSTRINGS),
        "principle": (
            "Visible rows are for human packet review only. Source rank/score, proxy role, GT status, "
            "construction buckets, scan ids, instance ids, and filesystem paths stay in hidden manifests."
        ),
    }


def packet_contract() -> dict[str, Any]:
    return {
        "contract_version": "r7_attachment_observability_packet_contract_v1",
        "route": "R7_attachment_observability",
        "primary_predicates": list(PRIMARY_PREDICATES),
        "diagnostic_predicates": list(DIAGNOSTIC_PREDICATES),
        "packet_units": [
            {
                "name": "pair_multiview_contact_sheet",
                "required": True,
                "source": "local_dataset/3RScan/scans/<scan>/multi_view/",
                "purpose": "visual endpoint identity, co-visibility, and attachment/hanging plausibility audit",
            },
            {
                "name": "mesh_semseg_context",
                "required": True,
                "source": "labels.instances.annotated.v2.ply + semseg.v2.json",
                "purpose": "geometry/mesh availability for contact and local-anchor evidence extraction",
            },
            {
                "name": "sequence_or_frame_reference",
                "required": "preferred",
                "source": "sequence.zip or sequence/",
                "purpose": "optional frame provenance for shared-view or co-visible crops",
            },
            {
                "name": "hidden_provenance_manifest",
                "required": True,
                "source": "candidate row and packet request manifest",
                "purpose": "audit-only mapping from visible review id to scan/instance/source/proxy fields",
            },
        ],
        "factor_boundary": {
            "T_e_visible_semantic_content": "subject/object labels and predicate text are visible",
            "G_e_future_geometry_evidence": "derived from mesh/point/contact evidence after packet materialization",
            "Q_e_observability": "derived from evidence availability and reviewer-visible packet quality",
            "Z_e_source_confidence": "hidden; not used for C_e or p_obs",
            "targets": "not filled in this step",
        },
        "blocked_from_model_input": [
            "source score/rank",
            "candidate id",
            "packet request id",
            "scan id",
            "instance ids",
            "proxy role",
            "GT match status",
            "geometry/coverage construction buckets",
            "review labels",
        ],
        "next_step_outputs": [
            "packet directories/contact sheets",
            "label-ready visible sheet",
            "hidden manifest with asset paths",
            "gap audit rows if any T3/T4 evidence remains",
        ],
    }


def counter_rows(prefix: str, counter: Counter[Any]) -> list[dict[str, Any]]:
    return [{"group": prefix, "key": str(key), "count": value} for key, value in counter.most_common()]


def quota_audit_rows(candidates: list[dict[str, Any]], evidence_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_candidate = {row["candidate_id"]: row for row in evidence_rows}
    counters: dict[str, Counter[Any]] = defaultdict(Counter)
    for row in candidates:
        evidence = by_candidate[row["candidate_id"]]
        predicate = row["predicate_label"]
        role = row["reliability_proxy_role"]
        counters["predicate"][predicate] += 1
        counters["proxy_role"][role] += 1
        counters["predicate_role"][f"{predicate}|{role}"] += 1
        counters["predicate_evidence_tier"][f"{predicate}|{evidence['evidence_tier']}"] += 1
        counters["role_evidence_tier"][f"{role}|{evidence['evidence_tier']}"] += 1
        counters["geometry_bucket_hidden"][row.get("geometry_bucket", "")] += 1
        counters["coverage_proxy_hidden"][row.get("coverage_proxy", "")] += 1
        counters["gt_label_match_status_hidden"][row.get("gt_label_match_status", "")] += 1
    rows: list[dict[str, Any]] = []
    for name in [
        "predicate",
        "proxy_role",
        "predicate_role",
        "predicate_evidence_tier",
        "role_evidence_tier",
        "geometry_bucket_hidden",
        "coverage_proxy_hidden",
        "gt_label_match_status_hidden",
    ]:
        rows.extend(counter_rows(name, counters[name]))
    return rows


def materialization_steps() -> list[dict[str, Any]]:
    return [
        {
            "step": "M1_build_visible_label_surface",
            "description": "Create reviewer-facing rows without source/rank/proxy/GT/scan/id/path fields.",
            "writes_assets": False,
        },
        {
            "step": "M2_write_hidden_asset_manifest",
            "description": "Map review_row_id to scan, instance ids, packet request id, proxy construction fields, and asset paths.",
            "writes_assets": False,
        },
        {
            "step": "M3_materialize_packets_next",
            "description": "Use the hidden manifest to generate pair multiview contact sheets and mesh/semseg evidence summaries.",
            "writes_assets": True,
        },
        {
            "step": "M4_gap_audit_if_needed",
            "description": "If T3/T4 rows appear after actual asset creation, decide limited-view inclusion or replacement.",
            "writes_assets": False,
        },
        {
            "step": "M5_stop_before_labels",
            "description": "Do not fill human labels or run learned smoke until packet readiness and label surface pass.",
            "writes_assets": False,
        },
    ]


def check_visible_leakage(visible_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_index, row in enumerate(visible_rows, start=1):
        for key in row:
            lowered = key.lower()
            if any(token in lowered for token in FORBIDDEN_VISIBLE_SUBSTRINGS):
                errors.append({"row_index": row_index, "error_type": "forbidden_visible_field", "field": key})
    return errors


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["evidence_summary"]
    selection = summary["candidate_selection_snapshot"]
    lines = [
        "# R7 Attachment Observability Class-Pair Repair Packet Materialization Plan",
        "",
        f"Created: `{summary['created_at_utc']}`",
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
        "## Candidate Scope",
        "",
        f"- total candidates: `{selection['selected_rows']}`",
        f"- predicates: `{selection['predicate_counts']}`",
        f"- proxy roles: `{selection['role_counts']}`",
        f"- unique scans: `{selection['unique_scans']}`",
        f"- exact predicate/class-pair groups: `{selection['unique_exact_class_pairs']}`",
        "",
        "## Evidence Readiness",
        "",
        f"- scan/mesh/semseg/sequence availability: `{counts['scan_mesh_sequence_ready']}`",
        f"- subject/object multiview available: `{counts['both_multiview_ready']}/{counts['rows']}`",
        f"- shared view-rank ready: `{counts['shared_view_ready']}/{counts['rows']}`",
        f"- shared frame ready: `{counts['shared_frame_ready']}/{counts['rows']}`",
        f"- evidence tiers: `{counts['evidence_tier_counts']}`",
        "",
        "## Decision",
        "",
        "이 단계는 실제 packet 이미지를 만들지 않고, packet 생성 계약과 visible/hidden manifest를 고정했다. "
        "480개 모두 `T1_pair_multiview_ready`이므로 바로 packet materialization으로 넘어갈 수 있다.",
        "",
        "중요한 경계는 다음과 같다.",
        "",
        "- reviewer-visible plan에는 scan id, instance id, source/rank, proxy role, GT status, geometry bucket, file path를 넣지 않았다.",
        "- hidden manifest에는 packet 생성을 위한 provenance와 asset path를 보존했다.",
        "- multi-view/mesh는 아직 model input이 아니라 audit/evidence packet 생성을 위한 source다.",
        "- label fill, target ingestion, schema audit, learned smoke는 아직 실행하지 않았다.",
        "",
        "Next:",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_summary_path = args.candidate_dir / "summary.json"
    candidate_rows_path = args.candidate_dir / "candidate_rows_internal.jsonl"
    packet_requests_path = args.candidate_dir / "packet_request_manifest.jsonl"
    candidate_errors_path = args.candidate_dir / "validation_errors.jsonl"

    candidate_summary = read_json(candidate_summary_path)
    candidates = read_jsonl(candidate_rows_path)
    packet_requests = read_jsonl(packet_requests_path)
    candidate_errors = read_jsonl(candidate_errors_path)
    validation_errors = validate_candidate_inputs(
        candidate_summary,
        candidates,
        packet_requests,
        candidate_errors,
        args.scan_root,
    )

    packet_by_candidate = {row["candidate_id"]: row for row in packet_requests}
    scan_cache: dict[str, dict[str, Any]] = {}
    evidence_rows: list[dict[str, Any]] = []
    visible_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []

    for index, row in enumerate(candidates, start=1):
        evidence = evidence_for_row(row, args.scan_root, scan_cache)
        packet_request = packet_by_candidate.get(row["candidate_id"], {})
        visible = visible_plan_row(index, row, packet_request, evidence)
        hidden = hidden_manifest_row(visible, row, packet_request, evidence)
        evidence_rows.append(evidence)
        visible_rows.append(visible)
        hidden_rows.append(hidden)

    validation_errors.extend(check_visible_leakage(visible_rows))

    evidence_tiers = Counter(row["evidence_tier"] for row in evidence_rows)
    not_ready_rows = sum(count for tier, count in evidence_tiers.items() if tier.startswith("T4"))
    limited_rows = sum(count for tier, count in evidence_tiers.items() if tier.startswith("T3"))
    if validation_errors:
        status = STATUS_ERROR
        selected_path = "input_or_leakage_errors_block_packet_plan"
        next_todo = "fix_attachment_observability_class_pair_repair_packet_plan_inputs"
    elif not_ready_rows or limited_rows:
        status = STATUS_PARTIAL
        selected_path = "packet_plan_partial_gap_audit_required"
        next_todo = NEXT_TODO_PARTIAL
    else:
        status = STATUS_READY
        selected_path = "class_pair_repair_packet_materialization_plan_ready"
        next_todo = NEXT_TODO_READY

    evidence_summary = {
        "rows": len(evidence_rows),
        "evidence_tier_counts": dict(evidence_tiers),
        "scan_mesh_sequence_ready": sum(
            1 for row in evidence_rows if row["scan_exists"] and row["mesh_ready"] and row["sequence_ready"]
        ),
        "both_multiview_ready": sum(1 for row in evidence_rows if row["both_multiview_ready"]),
        "shared_view_ready": sum(1 for row in evidence_rows if row["shared_view_ready"]),
        "shared_frame_ready": sum(1 for row in evidence_rows if row["shared_frame_ready"]),
        "mesh_ready": sum(1 for row in evidence_rows if row["mesh_ready"]),
        "sequence_ready": sum(1 for row in evidence_rows if row["sequence_ready"]),
        "not_ready_rows": not_ready_rows,
        "limited_rows": limited_rows,
    }

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "packet_materialization_contract": output_dir / "packet_materialization_contract.json",
        "visible_label_schema": output_dir / "visible_label_schema.json",
        "packet_plan_rows": output_dir / "packet_plan_rows.jsonl",
        "hidden_asset_manifest_plan": output_dir / "hidden_asset_manifest_plan.jsonl",
        "evidence_inventory_by_candidate": output_dir / "evidence_inventory_by_candidate.jsonl",
        "evidence_tier_audit": output_dir / "evidence_tier_audit.csv",
        "quota_audit": output_dir / "quota_audit.csv",
        "materialization_steps": output_dir / "materialization_steps.csv",
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
        "input_paths": {
            "candidate_summary": rel_path(candidate_summary_path),
            "candidate_rows_internal": rel_path(candidate_rows_path),
            "packet_request_manifest": rel_path(packet_requests_path),
            "scan_root": rel_path(args.scan_root),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "candidate_selection_snapshot": {
            "selected_rows": len(candidates),
            "predicate_counts": candidate_summary.get("selection_summary", {}).get("predicate_counts"),
            "role_counts": candidate_summary.get("selection_summary", {}).get("role_counts"),
            "unique_scans": candidate_summary.get("selection_summary", {}).get("unique_scans"),
            "unique_exact_class_pairs": candidate_summary.get("selection_summary", {}).get("unique_exact_class_pairs"),
            "predicate_role_counts": candidate_summary.get("selection_summary", {}).get("predicate_role_counts"),
        },
        "evidence_summary": evidence_summary,
        "route": {
            "route_id": "R7",
            "family": "attachment_observability",
            "primary_predicates": list(PRIMARY_PREDICATES),
            "diagnostic_predicates": list(DIAGNOSTIC_PREDICATES),
            "connected_to_rows": 0,
        },
        "packet_plan": {
            "visible_plan_rows": len(visible_rows),
            "hidden_manifest_rows": len(hidden_rows),
            "evidence_inventory_rows": len(evidence_rows),
            "actual_packet_assets_materialized": 0,
            "ready_for_packet_materialization": status == STATUS_READY,
        },
        "boundary": {
            "split": "train_only_packet_materialization_plan",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "fills_labels": False,
            "materializes_packet_assets": False,
            "materializes_model_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "multi_view_or_mesh_as_audit_evidence_only": True,
            "multi_view_or_mesh_as_model_input": False,
            "writes_plan_only": True,
        },
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["packet_materialization_contract"], packet_contract())
    write_json(output_paths["visible_label_schema"], visible_schema())
    write_jsonl(output_paths["packet_plan_rows"], visible_rows)
    write_jsonl(output_paths["hidden_asset_manifest_plan"], hidden_rows)
    write_jsonl(output_paths["evidence_inventory_by_candidate"], evidence_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_csv(output_paths["evidence_tier_audit"], counter_rows("evidence_tier", evidence_tiers))
    write_csv(output_paths["quota_audit"], quota_audit_rows(candidates, evidence_rows))
    write_csv(output_paths["materialization_steps"], materialization_steps())
    output_paths["report"].write_text(report_text(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
