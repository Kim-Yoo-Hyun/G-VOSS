#!/usr/bin/env python3
"""Mine H002 v8 endpoint-pair counterfactual candidate rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_FEASIBILITY_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_feasibility_scan_codex_proxy_user_requested"
DEFAULT_PACKET_MANIFESTS = [
    RGA_ROOT / "independent_asset_packets/packet_manifest.jsonl",
    RGA_ROOT / "reliability_target_v5_cell_contrast_asset_packets/generated_packet_manifest.jsonl",
    RGA_ROOT / "reliability_target_v6_shortcut_controlled_asset_packets_codex_proxy_user_requested/generated_packet_manifest.jsonl",
    RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_asset_packets_codex_proxy_user_requested/generated_packet_manifest.jsonl",
    RGA_ROOT / "reliability_target_v7_object_cell_evidence_contrast_replacement_asset_packets_codex_proxy_user_requested/generated_replacement_packet_manifest.jsonl",
]
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v8_endpoint_pair_counterfactual_candidate_mining_codex_proxy_user_requested"

READY_STATUS = "h002_reliability_target_v8_endpoint_pair_counterfactual_feasibility_ready"
EXPECTED_NEXT_TODO = "reliability_target_v8_endpoint_pair_counterfactual_candidate_mining"
NEXT_TODO_ASSETS = "reliability_target_v8_endpoint_pair_counterfactual_asset_packets"
NEXT_TODO_READINESS = "reliability_target_v8_endpoint_pair_counterfactual_label_readiness"

PRIMARY_FAMILIES = ("support_contact", "relative_vertical")
BUCKETS = ("B2_semantic_high_geometry_low", "B3_semantic_low_geometry_high")
TARGET_ROWS = 240
TARGET_PER_FAMILY = 120
TARGET_PER_BUCKET = 120
TARGET_PER_FAMILY_BUCKET = 60
MAX_ROWS_PER_ENDPOINT_GROUP = 4
MAX_ROWS_PER_SCAN = 16
MAX_LABEL_PAIR_SHARE = 0.08
MAX_FAMILY_CELL_SHARE = 0.08
MAX_STRUCTURAL_SHARE = 0.15
MAX_HARD_ROOM_SURFACE_SHARE = 0.10

REVIEW_SCOPE = "h002_reliability_v8_endpoint_pair_counterfactual_review"
SCHEMA_VERSION = "h002_reliability_target_v8_endpoint_pair_counterfactual_candidate_mining_v1"

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
    "bucket",
    "expected_target",
    "semantic_score",
    "semantic_rank",
    "p_geom",
    "geometry_status",
    "rank_band",
    "source_queue",
    "strict_group",
    "endpoint_pair_key",
    "v8_group",
    "object_family_cell",
    "subject_object_family_cell",
    "label_match",
    "h001_verification",
    "gt_label",
]

FORBIDDEN_VISIBLE_VALUE_TOKENS = [
    "semantic_score",
    "semantic_rank",
    "p_geom",
    "geometry_status",
    "rank_band",
    "source_queue",
    "strict_group",
    "exact_endpoint_pair",
    "v8_group",
    "object_family_cell",
    "subject_object_family_cell",
    "label_match",
    "h001_verification",
    "b2_semantic",
    "b3_semantic",
    "rga-fp",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feasibility-dir", type=Path, default=DEFAULT_FEASIBILITY_DIR)
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


def blind_review_id(row: dict[str, Any]) -> str:
    return "ftv8ep_" + stable_hash("h002_v8_endpoint_pair:" + str(row["prediction_id"]))[:12]


def packet_key_from_values(scan_id: Any, subject_id: Any, object_id: Any, predicate_label: Any) -> tuple[str, str, str, str]:
    return (str(scan_id), str(subject_id), str(object_id), str(predicate_label))


def packet_key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return packet_key_from_values(row.get("scan_id"), row.get("subject_id"), row.get("object_id"), row.get("predicate_label"))


def packet_ready(row: dict[str, Any] | None) -> bool:
    if not row:
        return False
    status = row.get("packet_status") or row.get("evidence_packet_status")
    return (
        status == "ready"
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


def family_prompt(row: dict[str, Any]) -> dict[str, str]:
    family = str(row.get("predicate_family"))
    if family == "support_contact":
        return {
            "question": "Does the subject physically contact, rest on, support, or attach to the object in the evidence?",
            "supporting_cues": "visible contact or support, plausible load direction, consistent object identity, non-trivial object pair",
            "contradicting_cues": "nearby without contact/support, clear gap, wrong support direction, endpoint identity issue, trivial structure",
        }
    if family == "relative_vertical":
        return {
            "question": "Is the subject clearly higher or lower than the object as stated by the predicate?",
            "supporting_cues": "clear vertical ordering, predicate direction matches evidence, comparable object-level endpoints",
            "contradicting_cues": "wrong vertical direction, ambiguous height, non-comparable endpoint, endpoint identity issue",
        }
    return {
        "question": "Does the relation hold according to the evidence?",
        "supporting_cues": "relation is supported by visual and geometric evidence",
        "contradicting_cues": "relation is contradicted, trivial, or not evaluable from the evidence",
    }


def validate_upstream(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != READY_STATUS:
        errors.append({"error_type": "unexpected_feasibility_status", "expected": READY_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_feasibility_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": summary.get("next_todo")})
    if summary.get("candidate_mining_allowed") is not True:
        errors.append({"error_type": "candidate_mining_not_allowed_by_feasibility"})
    for field in ["posterior_allowed", "label_fill_allowed", "validation_used", "test_used", "h001_artifacts_modified", "multi_view_as_model_input", "paper_metric_evidence"]:
        if summary.get(field) is not False:
            errors.append({"error_type": "unexpected_feasibility_boundary", "field": field, "expected": False, "actual": summary.get(field)})
    gates = summary.get("feasibility_gates") or {}
    if gates.get("strict_feasibility_pass") is not True:
        errors.append({"error_type": "strict_feasibility_gate_not_passed"})
    if gates.get("no_validation_or_test_usage") is not True or gates.get("train_only") is not True:
        errors.append({"error_type": "split_boundary_not_train_only"})
    if gates.get("no_new_label_fill") is not True or gates.get("no_posterior_smoke") is not True:
        errors.append({"error_type": "forbidden_stage_boundary_not_preserved"})
    selection = summary.get("selection_preview_summary") or {}
    if selection.get("all_rows_exact_endpoint_pair") is not True:
        errors.append({"error_type": "preview_not_exact_endpoint_pair_only"})
    if selection.get("all_rows_queue_mixed_group") is not True:
        errors.append({"error_type": "preview_not_queue_mixed_only"})
    return errors


def internal_row(row: dict[str, Any], packet: dict[str, Any] | None) -> dict[str, Any]:
    ready = packet_ready(packet)
    return {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_internal_candidate_v1",
        "batch_name": "reliability_target_v8_endpoint_pair_counterfactual_candidate_mining",
        "blind_review_id": blind_review_id(row),
        "prediction_id": row.get("prediction_id"),
        "split": "train",
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
        "source_queue_hidden": row.get("queue_kind"),
        "semantic_geometry_bucket_hidden": row.get("semantic_geometry_bucket"),
        "semantic_rank_hidden": row.get("semantic_rank"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm"),
        "semantic_score_raw_hidden": row.get("semantic_score_raw"),
        "p_geom_valid_hidden": row.get("p_geom_valid"),
        "geometry_status_hidden": row.get("geometry_status"),
        "h001_verification_status_hidden": row.get("h001_verification_status"),
        "label_geometry_bucket_hidden": row.get("label_geometry_bucket"),
        "label_match_status_hidden": row.get("label_match_status"),
        "matched_predicates_hidden": row.get("matched_predicates", []),
        "machine_hint_hidden": row.get("machine_hint"),
        "rank_band_hidden": row.get("rank_band"),
        "subject_object_label_pair_hidden": row.get("subject_object_label_pair"),
        "object_family_cell_hidden": row.get("object_family_cell"),
        "subject_object_family_cell_hidden": row.get("subject_object_family_cell"),
        "endpoint_pattern_hidden": row.get("endpoint_pattern"),
        "exact_endpoint_pair_key_hidden": row.get("exact_endpoint_pair_key"),
        "undirected_endpoint_pair_key_hidden": row.get("undirected_endpoint_pair_key"),
        "scene_label_pair_key_hidden": row.get("scene_label_pair_key"),
        "v8_group_level_hidden": row.get("v8_group_level"),
        "v8_group_key_hidden": row.get("v8_group_key"),
        "v8_group_row_count_hidden": row.get("v8_group_row_count"),
        "v8_group_predicate_count_hidden": row.get("v8_group_predicate_count"),
        "v8_group_has_queue_mix_hidden": row.get("v8_group_has_queue_mix"),
        "v8_group_has_family_mix_hidden": row.get("v8_group_has_family_mix"),
        "v8_group_has_vertical_contradiction_hidden": row.get("v8_group_has_vertical_contradiction"),
        "v8_group_has_support_alternative_hidden": row.get("v8_group_has_support_alternative"),
        "v8_group_geometry_range_hidden": row.get("v8_group_geometry_range"),
        "v8_group_rank_range_hidden": row.get("v8_group_rank_range"),
        "structural_pair_hidden": bool(row.get("structural_pair")),
        "hard_room_surface_pair_hidden": bool(row.get("hard_room_surface_pair")),
        "packet_status_hidden": "ready" if ready else "asset_needed",
        "packet_source_hidden": "existing_packet_manifest" if ready else "asset_needed",
        "multiview_packet": (packet or {}).get("multiview_packet", ""),
        "pointcloud_or_mesh_packet": (packet or {}).get("pointcloud_or_mesh_packet", ""),
        "contact_or_context_sheet": (packet or {}).get("contact_or_context_sheet", ""),
        "label_sheet_allowed": True,
        "label_fill_allowed": False,
        "posterior_input_allowed": False,
        "forbidden_as_labeler_visible": [
            "prediction_id",
            "source_queue_hidden",
            "semantic_geometry_bucket_hidden",
            "semantic_rank_hidden",
            "semantic_score_norm_hidden",
            "semantic_score_raw_hidden",
            "p_geom_valid_hidden",
            "geometry_status_hidden",
            "h001_verification_status_hidden",
            "label_geometry_bucket_hidden",
            "label_match_status_hidden",
            "matched_predicates_hidden",
            "machine_hint_hidden",
            "rank_band_hidden",
            "subject_object_label_pair_hidden",
            "object_family_cell_hidden",
            "subject_object_family_cell_hidden",
            "exact_endpoint_pair_key_hidden",
            "v8_group_key_hidden",
            "v8_group_geometry_range_hidden",
            "v8_group_rank_range_hidden",
        ],
    }


def visible_row(row: dict[str, Any]) -> dict[str, Any]:
    prompt = family_prompt(row)
    ready = row.get("packet_status_hidden") == "ready"
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
        "endpoint_pair_note": "Evaluate this predicate for the shown subject-object pair; other predicates may exist for the same pair but are not shown as labels.",
        "counterfactual_prompt": "Judge only whether this relation is reliable for this endpoint pair, not whether another relation could also be true.",
        "supporting_cues": prompt["supporting_cues"],
        "contradicting_cues": prompt["contradicting_cues"],
        "evidence_packet_status": "ready" if ready else "asset_needed",
        "multiview_packet": row.get("multiview_packet", "") if ready else "",
        "pointcloud_or_mesh_packet": row.get("pointcloud_or_mesh_packet", "") if ready else "",
        "contact_or_context_sheet": row.get("contact_or_context_sheet", "") if ready else "",
    }
    for field in COMPLETION_FIELDS:
        output[field] = ""
    return output


def asset_request_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_asset_request_v1",
        "asset_request_reason": "v8_endpoint_pair_counterfactual_candidate_needs_multiview_pointcloud_context_packet",
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
        "target_packet_stem": row["blind_review_id"],
        "requested_artifacts": ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"],
        "hidden_strata": {
            "semantic_geometry_bucket": row.get("semantic_geometry_bucket_hidden"),
            "exact_endpoint_pair_key": row.get("exact_endpoint_pair_key_hidden"),
            "v8_group_key": row.get("v8_group_key_hidden"),
            "structural_pair": row.get("structural_pair_hidden"),
            "hard_room_surface_pair": row.get("hard_room_surface_pair_hidden"),
        },
    }


def label_schema() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "review_scope": REVIEW_SCOPE,
        "visible_fields": VISIBLE_FIELDS,
        "primary_target": "relation_reliability_state_v6",
        "kept_target_schema_from_v6": True,
        "construction": "v8_endpoint_pair_counterfactual",
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
        "hidden_sampling_fields_are_not_label_targets": True,
        "semantic_geometry_bucket_is_not_target": True,
        "endpoint_pair_group_is_not_labeler_visible": True,
        "label_fill_allowed_by_candidate_mining": False,
    }


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    family_counts = Counter(row["predicate_family"] for row in rows)
    bucket_counts = Counter(row["semantic_geometry_bucket_hidden"] for row in rows)
    family_bucket_counts = Counter(f"{row['predicate_family']}|{row['semantic_geometry_bucket_hidden']}" for row in rows)
    group_counts = Counter(row["v8_group_key_hidden"] for row in rows)
    exact_counts = Counter(row["exact_endpoint_pair_key_hidden"] for row in rows)
    scan_counts = Counter(str(row["scan_id"]) for row in rows)
    pair_counts = Counter(row["subject_object_label_pair_hidden"] for row in rows)
    cell_counts = Counter(row["subject_object_family_cell_hidden"] for row in rows)
    structural_count = sum(1 for row in rows if row["structural_pair_hidden"])
    hard_surface_count = sum(1 for row in rows if row["hard_room_surface_pair_hidden"])
    ready_count = sum(1 for row in rows if row["packet_status_hidden"] == "ready")
    queue_mixed_rows = sum(1 for row in rows if row["v8_group_has_queue_mix_hidden"] is True)
    exact_level_rows = sum(1 for row in rows if row["v8_group_level_hidden"] == "exact_endpoint_pair")
    return {
        "selected_rows": len(rows),
        "family_counts": dict(sorted(family_counts.items())),
        "bucket_counts": dict(sorted(bucket_counts.items())),
        "family_bucket_counts": dict(sorted(family_bucket_counts.items())),
        "v8_groups_used": len(group_counts),
        "exact_endpoint_pairs_used": len(exact_counts),
        "max_rows_per_v8_group": max(group_counts.values()) if group_counts else 0,
        "scans_used": len(scan_counts),
        "max_rows_per_scan": max(scan_counts.values()) if scan_counts else 0,
        "subject_object_label_pair_unique": len(pair_counts),
        "max_single_subject_object_label_pair_count": max(pair_counts.values()) if pair_counts else 0,
        "max_single_subject_object_label_pair_share": max(pair_counts.values()) / len(rows) if rows else 0.0,
        "subject_object_family_cell_unique": len(cell_counts),
        "max_single_subject_object_family_cell_count": max(cell_counts.values()) if cell_counts else 0,
        "max_single_subject_object_family_cell_share": max(cell_counts.values()) / len(rows) if rows else 0.0,
        "structural_pair_count": structural_count,
        "structural_pair_share": structural_count / len(rows) if rows else 0.0,
        "hard_room_surface_pair_count": hard_surface_count,
        "hard_room_surface_pair_share": hard_surface_count / len(rows) if rows else 0.0,
        "packet_ready_rows": ready_count,
        "asset_needed_rows": len(rows) - ready_count,
        "queue_mixed_rows": queue_mixed_rows,
        "exact_endpoint_pair_level_rows": exact_level_rows,
    }


def bucket_summary_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for family in PRIMARY_FAMILIES:
        for bucket in BUCKETS:
            subset = [row for row in rows if row["predicate_family"] == family and row["semantic_geometry_bucket_hidden"] == bucket]
            output.append(
                {
                    "predicate_family": family,
                    "semantic_geometry_bucket": bucket,
                    "target_rows": TARGET_PER_FAMILY_BUCKET,
                    "selected_rows": len(subset),
                    "asset_needed_rows": sum(1 for row in subset if row["packet_status_hidden"] != "ready"),
                    "packet_ready_rows": sum(1 for row in subset if row["packet_status_hidden"] == "ready"),
                    "v8_groups": len({row["v8_group_key_hidden"] for row in subset}),
                    "exact_endpoint_pairs": len({row["exact_endpoint_pair_key_hidden"] for row in subset}),
                    "structural_rows": sum(1 for row in subset if row["structural_pair_hidden"]),
                    "hard_room_surface_rows": sum(1 for row in subset if row["hard_room_surface_pair_hidden"]),
                    "deficit": max(0, TARGET_PER_FAMILY_BUCKET - len(subset)),
                }
            )
    return output


def cap_audit_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counters = {
        "v8_group": Counter(row["v8_group_key_hidden"] for row in rows),
        "exact_endpoint_pair": Counter(row["exact_endpoint_pair_key_hidden"] for row in rows),
        "scan_id": Counter(str(row["scan_id"]) for row in rows),
        "subject_object_label_pair": Counter(row["subject_object_label_pair_hidden"] for row in rows),
        "subject_object_family_cell": Counter(row["subject_object_family_cell_hidden"] for row in rows),
    }
    limits = {
        "v8_group": MAX_ROWS_PER_ENDPOINT_GROUP,
        "exact_endpoint_pair": MAX_ROWS_PER_ENDPOINT_GROUP,
        "scan_id": MAX_ROWS_PER_SCAN,
        "subject_object_label_pair": int(TARGET_ROWS * MAX_LABEL_PAIR_SHARE),
        "subject_object_family_cell": int(TARGET_ROWS * MAX_FAMILY_CELL_SHARE),
    }
    output: list[dict[str, Any]] = []
    for cap_name, counter in counters.items():
        max_key, max_count = counter.most_common(1)[0] if counter else ("", 0)
        output.append(
            {
                "cap_name": cap_name,
                "limit": limits[cap_name],
                "max_observed": max_count,
                "max_key": max_key,
                "unique_values": len(counter),
                "violates_cap": max_count > limits[cap_name],
            }
        )
    structural_count = sum(1 for row in rows if row["structural_pair_hidden"])
    hard_surface_count = sum(1 for row in rows if row["hard_room_surface_pair_hidden"])
    structural_limit = int(TARGET_ROWS * MAX_STRUCTURAL_SHARE)
    hard_limit = int(TARGET_ROWS * MAX_HARD_ROOM_SURFACE_SHARE)
    output.extend(
        [
            {
                "cap_name": "structural_pair_rows",
                "limit": structural_limit,
                "max_observed": structural_count,
                "max_key": "structural_pair",
                "unique_values": 1,
                "violates_cap": structural_count > structural_limit,
            },
            {
                "cap_name": "hard_room_surface_pair_rows",
                "limit": hard_limit,
                "max_observed": hard_surface_count,
                "max_key": "hard_room_surface_pair",
                "unique_values": 1,
                "violates_cap": hard_surface_count > hard_limit,
            },
        ]
    )
    return output


def field_leakage_hits(fieldnames: list[str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for field in fieldnames:
        lower = field.lower()
        for token in FORBIDDEN_VISIBLE_FIELD_TOKENS:
            if token in lower:
                hits.append({"field": field, "forbidden_token": token})
    return hits


def value_leakage_hits(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
        if row.get("packet_status_hidden") != "ready":
            continue
        for field in ["multiview_packet", "pointcloud_or_mesh_packet", "contact_or_context_sheet"]:
            value = row.get(field)
            if not value:
                errors.append({"blind_review_id": row["blind_review_id"], "field": field, "error": "missing_ready_packet_path"})
                continue
            if not as_abs(Path(str(value))).exists():
                errors.append({"blind_review_id": row["blind_review_id"], "field": field, "path": value, "error": "ready_packet_path_not_found"})
    return errors


def validate_candidate_counts(counts: dict[str, Any], bucket_rows: list[dict[str, Any]], cap_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if counts["selected_rows"] != TARGET_ROWS:
        errors.append({"error_type": "unexpected_selected_row_count", "expected": TARGET_ROWS, "actual": counts["selected_rows"]})
    if counts["queue_mixed_rows"] != counts["selected_rows"]:
        errors.append({"error_type": "non_queue_mixed_rows_selected", "actual": counts["selected_rows"] - counts["queue_mixed_rows"]})
    if counts["exact_endpoint_pair_level_rows"] != counts["selected_rows"]:
        errors.append({"error_type": "non_exact_endpoint_pair_rows_selected", "actual": counts["selected_rows"] - counts["exact_endpoint_pair_level_rows"]})
    for family in PRIMARY_FAMILIES:
        if counts["family_counts"].get(family, 0) != TARGET_PER_FAMILY:
            errors.append({"error_type": "family_count_mismatch", "family": family, "expected": TARGET_PER_FAMILY, "actual": counts["family_counts"].get(family, 0)})
    for bucket in BUCKETS:
        if counts["bucket_counts"].get(bucket, 0) != TARGET_PER_BUCKET:
            errors.append({"error_type": "bucket_count_mismatch", "bucket": bucket, "expected": TARGET_PER_BUCKET, "actual": counts["bucket_counts"].get(bucket, 0)})
    for row in bucket_rows:
        if row["selected_rows"] != TARGET_PER_FAMILY_BUCKET:
            errors.append({"error_type": "family_bucket_count_mismatch", "row": row})
    if counts["max_single_subject_object_label_pair_share"] > MAX_LABEL_PAIR_SHARE:
        errors.append({"error_type": "subject_object_label_pair_share_cap_violation", "value": counts["max_single_subject_object_label_pair_share"]})
    if counts["max_single_subject_object_family_cell_share"] > MAX_FAMILY_CELL_SHARE:
        errors.append({"error_type": "subject_object_family_cell_share_cap_violation", "value": counts["max_single_subject_object_family_cell_share"]})
    for row in cap_rows:
        if row["violates_cap"]:
            errors.append({"error_type": "cap_violation", "cap": row})
    return errors


def report_text(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    return f"""# H002 V8 Endpoint-Pair Counterfactual Candidate Mining

Created at: `{summary["created_at"]}`

## Boundary

- Train-only artifact.
- Labels are not filled.
- Posterior is not trained.
- Validation/test rows are not used.
- H001 artifacts are not modified.
- The v6 reliability label schema is kept, but the sampling unit is v8 endpoint-pair counterfactual contrast.
- Semantic score, rank, geometry status, `p_geom_valid`, queue kind, endpoint-pair key, and v8 group metadata are hidden from the visible label surface.

## Status

```text
status = {summary["status"]}
posterior_allowed = {summary["posterior_allowed"]}
label_fill_allowed = {summary["label_fill_allowed"]}
next = {summary["next_todo"]}
validation_errors = {summary["validation_error_count"]}
```

## Candidate Counts

```text
selected_rows = {counts["selected_rows"]}
family_counts = {counts["family_counts"]}
bucket_counts = {counts["bucket_counts"]}
family_bucket_counts = {counts["family_bucket_counts"]}
v8_groups_used = {counts["v8_groups_used"]}
exact_endpoint_pairs_used = {counts["exact_endpoint_pairs_used"]}
max_rows_per_v8_group = {counts["max_rows_per_v8_group"]}
max_single_subject_object_label_pair_share = {counts["max_single_subject_object_label_pair_share"]:.4f}
max_single_subject_object_family_cell_share = {counts["max_single_subject_object_family_cell_share"]:.4f}
structural_pair_count = {counts["structural_pair_count"]}
hard_room_surface_pair_count = {counts["hard_room_surface_pair_count"]}
packet_ready_rows = {counts["packet_ready_rows"]}
asset_needed_rows = {counts["asset_needed_rows"]}
```

## Interpretation

The v8 candidate queue is fixed from exact endpoint-pair queue-mixed contrast groups. This is not posterior evidence.
Because asset-needed rows remain, the next step is asset packet generation/readiness before any label fill.

## Next TODO

`{summary["next_todo"]}`
"""


def run(args: argparse.Namespace) -> dict[str, Any]:
    feasibility_dir = as_abs(args.feasibility_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    feasibility_summary = read_json(feasibility_dir / "summary.json")
    validation_errors = validate_upstream(feasibility_summary)
    packets = load_ready_packets([as_abs(path) for path in args.packet_manifest])
    preview_rows = list(iter_jsonl(feasibility_dir / "feasibility_preview_rows.jsonl"))

    duplicate_ids = [pid for pid, count in Counter(str(row.get("prediction_id")) for row in preview_rows).items() if count > 1]
    if duplicate_ids:
        validation_errors.append({"error_type": "duplicate_prediction_ids_in_preview", "count": len(duplicate_ids), "examples": duplicate_ids[:10]})

    selected = [internal_row(row, packets.get(packet_key(row))) for row in preview_rows]
    selected = sorted(selected, key=lambda row: (row["predicate_family"], row["semantic_geometry_bucket_hidden"], row["blind_review_id"]))

    visible_rows = [visible_row(row) for row in selected]
    packet_ready_rows = [row for row in selected if row["packet_status_hidden"] == "ready"]
    asset_needed_rows = [row for row in selected if row["packet_status_hidden"] != "ready"]
    packet_ready_visible_rows = [visible_row(row) for row in packet_ready_rows]
    asset_requests = [asset_request_row(row) for row in asset_needed_rows]

    counts = count_summary(selected)
    bucket_rows = bucket_summary_rows(selected)
    cap_rows = cap_audit_rows(selected)
    validation_errors.extend(validate_candidate_counts(counts, bucket_rows, cap_rows))
    field_hits = field_leakage_hits(VISIBLE_FIELDS)
    value_hits = value_leakage_hits(visible_rows)
    packet_errors = packet_path_errors(selected)
    if field_hits or value_hits:
        validation_errors.append({"error_type": "visible_label_surface_leakage", "field_hits": len(field_hits), "value_hits": len(value_hits)})
    if packet_errors:
        validation_errors.append({"error_type": "ready_packet_path_errors", "count": len(packet_errors)})

    if validation_errors:
        status = "h002_reliability_target_v8_endpoint_pair_counterfactual_candidate_mining_errors"
        next_todo = "fix_reliability_target_v8_endpoint_pair_counterfactual_candidate_mining_errors"
    elif counts["asset_needed_rows"] > 0:
        status = "h002_reliability_target_v8_endpoint_pair_counterfactual_candidate_mining_ready_needs_asset_packets"
        next_todo = NEXT_TODO_ASSETS
    else:
        status = "h002_reliability_target_v8_endpoint_pair_counterfactual_candidate_mining_ready_for_label_readiness"
        next_todo = NEXT_TODO_READINESS

    output_paths = {
        "summary": rel_path(output_dir / "summary.json"),
        "report": rel_path(output_dir / "report.md"),
        "label_schema": rel_path(output_dir / "label_schema.json"),
        "label_sheet": rel_path(output_dir / "v8_endpoint_pair_counterfactual_label_sheet.tsv"),
        "packet_ready_label_sheet": rel_path(output_dir / "v8_endpoint_pair_counterfactual_packet_ready_label_sheet.tsv"),
        "selected_candidates_internal": rel_path(output_dir / "selected_candidates_internal.jsonl"),
        "selected_packet_ready_candidates": rel_path(output_dir / "selected_packet_ready_candidates.jsonl"),
        "selected_asset_needed_candidates": rel_path(output_dir / "selected_asset_needed_candidates.jsonl"),
        "asset_request_manifest": rel_path(output_dir / "asset_request_manifest.jsonl"),
        "bucket_summary": rel_path(output_dir / "bucket_summary.csv"),
        "cap_audit": rel_path(output_dir / "cap_audit.csv"),
        "leakage_audit": rel_path(output_dir / "leakage_audit.json"),
        "packet_path_errors": rel_path(output_dir / "packet_path_errors.json"),
        "validation_errors": rel_path(output_dir / "validation_errors.json"),
    }
    summary = {
        "schema_version": "h002_reliability_target_v8_endpoint_pair_counterfactual_candidate_mining_summary_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "posterior_allowed": False,
        "label_fill_allowed": False,
        "label_sheet_created": True,
        "candidate_mining_allowed_by_upstream": feasibility_summary.get("candidate_mining_allowed"),
        "validation_used": False,
        "test_used": False,
        "train_only": True,
        "h001_artifacts_modified": False,
        "multi_view_as_model_input": False,
        "paper_metric_evidence": False,
        "counts": counts,
        "validation_error_count": len(validation_errors),
        "validation": {
            "field_leakage_hits": len(field_hits),
            "value_leakage_hits": len(value_hits),
            "packet_path_errors": len(packet_errors),
            "cap_violations": sum(1 for row in cap_rows if row["violates_cap"]),
            "bucket_deficit_total": sum(row["deficit"] for row in bucket_rows),
        },
        "feasibility_status": feasibility_summary.get("status"),
        "feasibility_output_dir": rel_path(feasibility_dir),
        "kept_target_schema": "relation_reliability_state_v6 = accept_reliable / reject_unreliable / abstain_uncertain",
        "construction": "v8_endpoint_pair_counterfactual",
        "input_paths": {
            "feasibility_summary": rel_path(feasibility_dir / "summary.json"),
            "feasibility_preview_rows": rel_path(feasibility_dir / "feasibility_preview_rows.jsonl"),
            "packet_manifests": [rel_path(path) for path in args.packet_manifest],
        },
        "output_dir": rel_path(output_dir),
        "output_paths": output_paths,
    }

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "label_schema.json", label_schema())
    write_tsv(output_dir / "v8_endpoint_pair_counterfactual_label_sheet.tsv", visible_rows, VISIBLE_FIELDS)
    write_tsv(output_dir / "v8_endpoint_pair_counterfactual_packet_ready_label_sheet.tsv", packet_ready_visible_rows, VISIBLE_FIELDS)
    write_jsonl(output_dir / "selected_candidates_internal.jsonl", selected)
    write_jsonl(output_dir / "selected_packet_ready_candidates.jsonl", packet_ready_rows)
    write_jsonl(output_dir / "selected_asset_needed_candidates.jsonl", asset_needed_rows)
    write_jsonl(output_dir / "asset_request_manifest.jsonl", asset_requests)
    write_csv(output_dir / "bucket_summary.csv", bucket_rows)
    write_csv(output_dir / "cap_audit.csv", cap_rows)
    write_json(
        output_dir / "leakage_audit.json",
        {
            "field_hits": field_hits,
            "value_hits": value_hits,
            "forbidden_visible_field_tokens": FORBIDDEN_VISIBLE_FIELD_TOKENS,
            "forbidden_visible_value_tokens": FORBIDDEN_VISIBLE_VALUE_TOKENS,
        },
    )
    write_json(output_dir / "packet_path_errors.json", packet_errors)
    write_json(output_dir / "validation_errors.json", validation_errors)
    (output_dir / "report.md").write_text(report_text(summary), encoding="utf-8")
    return summary


def main() -> int:
    summary = run(parse_args())
    print(
        "status={status} rows={rows} ready={ready} asset_needed={asset_needed} "
        "groups={groups} max_pair_share={pair_share:.4f} errors={errors} next={next_todo}".format(
            status=summary["status"],
            rows=summary["counts"]["selected_rows"],
            ready=summary["counts"]["packet_ready_rows"],
            asset_needed=summary["counts"]["asset_needed_rows"],
            groups=summary["counts"]["v8_groups_used"],
            pair_share=summary["counts"]["max_single_subject_object_label_pair_share"],
            errors=summary["validation_error_count"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
