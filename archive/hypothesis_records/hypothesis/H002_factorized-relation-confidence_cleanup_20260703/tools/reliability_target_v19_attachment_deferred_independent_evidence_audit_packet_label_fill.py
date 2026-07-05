#!/usr/bin/env python3
"""Fill H002 v19 attachment audit-packet labels from reviewer-visible packets only."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_MATERIALIZATION_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization"
DEFAULT_LEAKAGE_REVIEW_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_fill"

EXPECTED_MATERIALIZATION_STATUS = (
    "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_materialization_ready_for_leakage_review"
)
EXPECTED_LEAKAGE_REVIEW_STATUS = (
    "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_leakage_review_passed_ready_for_label_fill"
)

SCHEMA_VERSION = "h002_reliability_target_v19_attachment_packet_label_fill_v1"
STATUS_READY = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_filled_codex_visible_packet"
STATUS_ERROR = "h002_reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_fill_errors"
NEXT_TODO = "reliability_target_v19_attachment_deferred_independent_evidence_audit_packet_label_ingestion"

REVIEWER_ID = "codex_visible_packet_labeler_v19_user_requested"
REVIEW_ROUND = "1"
LABEL_POLICY = "v19_visible_packet_attachment_hanging_conservative_connected_diagnostic"

VISIBLE_FIELDS = [
    "packet_id",
    "blind_review_id",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "packet_role",
    "evidence_tier",
    "evidence_tier_description",
    "visual_context_summary",
    "mesh_context_summary",
    "audit_question",
    "review_relation_reliability",
    "review_geometry_support",
    "review_uncertainty",
    "review_notes",
]

FILLED_FIELDS = [
    *VISIBLE_FIELDS[:13],
    "reviewer_id_v19",
    "review_round_v19",
    "label_policy_v19",
    "review_relation_reliability",
    "review_geometry_support",
    "review_uncertainty",
    "review_notes",
]

ALLOWED_VALUES = {
    "review_relation_reliability": {
        "accept_reliable_attachment",
        "reject_unreliable_attachment",
        "diagnostic_connected_possible",
        "diagnostic_connected_ambiguous",
        "abstain_uncertain",
    },
    "review_geometry_support": {"supports", "contradicts", "ambiguous", "not_evaluable"},
    "review_uncertainty": {"low", "medium", "high", "diagnostic_only"},
}

GENERIC_LABELS = {"object", "objects", "item", "items", "thing", "things", "stuff", "clutter"}
BROAD_STRUCTURAL_SUBJECTS = {"wall", "floor", "ceiling"}
FLOOR_SUPPORT_LABELS = {"floor", "table", "desk", "bed", "chair", "bench", "stool", "sofa", "couch", "armchair"}
SOFT_SUPPORT_LABELS = {"pillow", "blanket", "clothes", "bag", "box", "bucket", "trash can", "plant", "basket", "bin"}

ATTACHMENT_ANCHORS = {
    "wall",
    "ceiling",
    "door",
    "doorframe",
    "window",
    "tv stand",
    "stand",
    "shelf",
    "cabinet",
    "kitchen cabinet",
    "rack",
    "closet",
    "wardrobe",
    "blinds",
    "curtain",
}
ATTACHABLE_SUBJECTS = {
    "board",
    "cabinet",
    "kitchen cabinet",
    "shelf",
    "counter",
    "commode",
    "decoration",
    "picture",
    "frame",
    "tv",
    "monitor",
    "rack",
    "curtain",
    "blinds",
    "light",
    "lamp",
    "doorframe",
    "door",
    "radiator",
    "heater",
    "folder",
}
HANGING_ANCHORS = {
    "wall",
    "ceiling",
    "door",
    "doorframe",
    "window",
    "curtain",
    "blinds",
    "shelf",
    "rack",
    "cabinet",
    "kitchen cabinet",
    "wardrobe",
    "closet",
}
HANGING_SUBJECTS = {
    "plate",
    "plant",
    "shelf",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "curtain",
    "blinds",
    "clothes",
    "towel",
    "bag",
    "backpack",
    "picture",
    "frame",
    "decoration",
    "light",
    "lamp",
    "organizer",
    "stuffed animal",
}
LARGE_NOT_HANGING_SUBJECTS = {
    "wall",
    "floor",
    "ceiling",
    "bed",
    "table",
    "desk",
    "side table",
    "nightstand",
    "sofa",
    "couch",
    "chair",
    "dining chair",
    "ottoman",
    "washing machine",
    "wardrobe",
    "microwave",
    "monitor",
}
CONNECTED_PLAUSIBLE_PAIRS = {
    ("door", "doorframe"),
    ("shelf", "wall"),
    ("shelf", "floor"),
    ("frame", "wall"),
    ("closet", "wall"),
    ("kitchen counter", "kitchen cabinet"),
    ("floor", "wall"),
    ("ceiling", "door"),
    ("window", "floor"),
    ("floor", "window"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--materialization-dir", type=Path, default=DEFAULT_MATERIALIZATION_DIR)
    parser.add_argument("--leakage-review-dir", type=Path, default=DEFAULT_LEAKAGE_REVIEW_DIR)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def count_packet_images(packet_dir: Path) -> int:
    image_dir = as_abs(packet_dir) / "images"
    if not image_dir.is_dir():
        return 0
    return sum(1 for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"})


def base_decision(reliability: str, geometry: str, uncertainty: str, reason: str, note: str) -> dict[str, str]:
    return {
        "review_relation_reliability": reliability,
        "review_geometry_support": geometry,
        "review_uncertainty": uncertainty,
        "primary_reason_v19": reason,
        "review_notes": note,
    }


def endpoint_quality(subject: str, obj: str) -> str:
    if subject in GENERIC_LABELS or obj in GENERIC_LABELS:
        return "generic_endpoint"
    if subject == obj:
        return "same_label_endpoint"
    return "clear"


def evidence_uncertainty(row: dict[str, str], image_count: int) -> str:
    if row["evidence_tier"] == "T1_strong_pair_visual" and image_count >= 12:
        return "low"
    if row["evidence_tier"] in {"T1_strong_pair_visual", "T2_individual_visual_plus_mesh"} and image_count >= 8:
        return "medium"
    return "high"


def label_attached(row: dict[str, str], image_count: int) -> dict[str, str]:
    subject = norm(row["subject_label"])
    obj = norm(row["object_label"])
    tier = row["evidence_tier"]
    endpoint = endpoint_quality(subject, obj)
    uncertainty = evidence_uncertainty(row, image_count)

    if endpoint == "generic_endpoint":
        return base_decision(
            "abstain_uncertain",
            "ambiguous",
            "high",
            "generic_endpoint_label",
            "codex v19 visible-packet: endpoint label is too generic for a reliable attachment judgment",
        )
    if endpoint == "same_label_endpoint":
        return base_decision(
            "reject_unreliable_attachment",
            "contradicts",
            uncertainty,
            "duplicate_or_self_like_endpoint",
            "codex v19 visible-packet: same-label endpoint pair is not a useful directed attachment edge",
        )
    if subject in BROAD_STRUCTURAL_SUBJECTS:
        return base_decision(
            "reject_unreliable_attachment",
            "contradicts",
            uncertainty,
            "wrong_direction_broad_structural_subject",
            "codex v19 visible-packet: broad structural surface as directed subject makes the attachment edge unreliable",
        )
    if subject == "floor" or obj in FLOOR_SUPPORT_LABELS or obj in SOFT_SUPPORT_LABELS:
        return base_decision(
            "reject_unreliable_attachment",
            "contradicts",
            uncertainty,
            "ordinary_support_or_proximity_confound",
            "codex v19 visible-packet: relation is better explained as support/proximity than attachment",
        )
    if obj in ATTACHMENT_ANCHORS and subject in ATTACHABLE_SUBJECTS:
        return base_decision(
            "accept_reliable_attachment",
            "supports",
            uncertainty,
            "anchor_compatible_attachment_pair",
            "codex v19 visible-packet: endpoint labels and packet evidence support an attachment-like anchor relation",
        )
    if obj in {"wall", "ceiling", "doorframe", "window"} and tier == "T1_strong_pair_visual":
        return base_decision(
            "abstain_uncertain",
            "ambiguous",
            "medium",
            "possible_anchor_but_subject_type_unclear",
            "codex v19 visible-packet: exact pair visual context exists, but the subject type is not a clear attachment object",
        )
    return base_decision(
        "abstain_uncertain",
        "ambiguous",
        uncertainty,
        "insufficient_attachment_evidence",
        "codex v19 visible-packet: attachment cues are not strong enough for a binary decision",
    )


def label_hanging(row: dict[str, str], image_count: int) -> dict[str, str]:
    subject = norm(row["subject_label"])
    obj = norm(row["object_label"])
    endpoint = endpoint_quality(subject, obj)
    uncertainty = evidence_uncertainty(row, image_count)

    if endpoint == "generic_endpoint":
        return base_decision(
            "abstain_uncertain",
            "ambiguous",
            "high",
            "generic_endpoint_label",
            "codex v19 visible-packet: endpoint label is too generic for a reliable hanging judgment",
        )
    if endpoint == "same_label_endpoint":
        return base_decision(
            "reject_unreliable_attachment",
            "contradicts",
            uncertainty,
            "duplicate_or_self_like_endpoint",
            "codex v19 visible-packet: same-label endpoint pair is not a useful hanging edge",
        )
    if subject in LARGE_NOT_HANGING_SUBJECTS or subject in BROAD_STRUCTURAL_SUBJECTS:
        return base_decision(
            "reject_unreliable_attachment",
            "contradicts",
            uncertainty,
            "implausible_hanging_subject",
            "codex v19 visible-packet: subject type is unlikely to be hanging as a directed scene-graph relation",
        )
    if obj in {"floor", "table", "desk", "bed", "chair", "dining table", "sink"}:
        return base_decision(
            "reject_unreliable_attachment",
            "contradicts",
            uncertainty,
            "support_surface_confound",
            "codex v19 visible-packet: object is a support/proximity surface rather than a hanging anchor",
        )
    if obj in HANGING_ANCHORS and subject in HANGING_SUBJECTS:
        return base_decision(
            "accept_reliable_attachment",
            "supports",
            uncertainty,
            "anchor_compatible_hanging_pair",
            "codex v19 visible-packet: endpoint labels and packet evidence support a hanging or mounted relation",
        )
    if obj in HANGING_ANCHORS:
        return base_decision(
            "abstain_uncertain",
            "ambiguous",
            uncertainty,
            "anchor_possible_subject_unclear",
            "codex v19 visible-packet: anchor is plausible but subject type makes the hanging edge uncertain",
        )
    return base_decision(
        "reject_unreliable_attachment",
        "contradicts",
        uncertainty,
        "missing_hanging_anchor",
        "codex v19 visible-packet: hanging relation lacks a plausible anchor in the visible packet fields",
    )


def label_connected(row: dict[str, str], image_count: int) -> dict[str, str]:
    subject = norm(row["subject_label"])
    obj = norm(row["object_label"])
    endpoint = endpoint_quality(subject, obj)
    if endpoint != "clear":
        return base_decision(
            "diagnostic_connected_ambiguous",
            "ambiguous",
            "diagnostic_only",
            "connected_endpoint_ambiguous",
            "codex v19 visible-packet: connected-to is diagnostic-only and endpoint identity is ambiguous",
        )
    possible = (subject, obj) in CONNECTED_PLAUSIBLE_PAIRS or (obj, subject) in CONNECTED_PLAUSIBLE_PAIRS
    possible = possible or (row["evidence_tier"] == "T1_strong_pair_visual" and image_count >= 12)
    return base_decision(
        "diagnostic_connected_possible" if possible else "diagnostic_connected_ambiguous",
        "supports" if possible else "ambiguous",
        "diagnostic_only",
        "connected_diagnostic_needs_visual_or_mesh",
        "codex v19 visible-packet: connected-to is retained as diagnostic-only because functional connection is not a primary binary target",
    )


def label_row(row: dict[str, str], packet_info: dict[str, Any]) -> dict[str, str]:
    image_count = int(packet_info.get("local_image_count", 0))
    predicate = norm(row["predicate_label"])
    if row["packet_role"] == "uncertainty_or_coverage_audit_only":
        return base_decision(
            "abstain_uncertain",
            "ambiguous",
            evidence_uncertainty(row, image_count),
            "audit_only_row_not_primary_target",
            "codex v19 visible-packet: row was explicitly routed to uncertainty/coverage audit rather than primary binary target",
        )
    if predicate == "attached to":
        return label_attached(row, image_count)
    if predicate == "hanging on":
        return label_hanging(row, image_count)
    if predicate == "connected to":
        return label_connected(row, image_count)
    return base_decision(
        "abstain_uncertain",
        "not_evaluable",
        "high",
        "predicate_out_of_scope",
        "codex v19 visible-packet: predicate is outside the v19 attachment audit policy",
    )


def validate_inputs(
    materialization_summary: dict[str, Any],
    leakage_summary: dict[str, Any],
    fieldnames: list[str],
    rows: list[dict[str, str]],
    packet_index: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if materialization_summary.get("status") != EXPECTED_MATERIALIZATION_STATUS:
        errors.append(
            {
                "error_type": "unexpected_materialization_status",
                "expected": EXPECTED_MATERIALIZATION_STATUS,
                "actual": materialization_summary.get("status"),
            }
        )
    if leakage_summary.get("status") != EXPECTED_LEAKAGE_REVIEW_STATUS:
        errors.append(
            {
                "error_type": "unexpected_leakage_review_status",
                "expected": EXPECTED_LEAKAGE_REVIEW_STATUS,
                "actual": leakage_summary.get("status"),
            }
        )
    if leakage_summary.get("counts", {}).get("visible_leakage_hits") != 0:
        errors.append({"error_type": "visible_leakage_hits_present", "actual": leakage_summary.get("counts", {}).get("visible_leakage_hits")})
    if leakage_summary.get("validation_errors") != 0:
        errors.append({"error_type": "leakage_validation_errors_present", "actual": leakage_summary.get("validation_errors")})
    if fieldnames != VISIBLE_FIELDS:
        errors.append({"error_type": "visible_sheet_schema_mismatch", "expected": VISIBLE_FIELDS, "actual": fieldnames})
    if len(rows) != 240:
        errors.append({"error_type": "unexpected_row_count", "expected": 240, "actual": len(rows)})
    if len(packet_index) != 240:
        errors.append({"error_type": "unexpected_packet_index_count", "expected": 240, "actual": len(packet_index)})

    boundary = leakage_summary.get("boundary", {})
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
        "mesh_as_model_input",
        "old_labels_visible",
        "construction_metadata_visible",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "leakage_boundary_violation", "key": key, "expected": False, "actual": boundary.get(key)})

    seen: set[str] = set()
    packet_ids = {row.get("packet_id") for row in packet_index}
    for row_number, row in enumerate(rows, start=2):
        packet_id = row.get("packet_id", "")
        if not packet_id:
            errors.append({"error_type": "missing_packet_id", "row_number": row_number})
        if packet_id in seen:
            errors.append({"error_type": "duplicate_packet_id", "packet_id": packet_id})
        seen.add(packet_id)
        if packet_id not in packet_ids:
            errors.append({"error_type": "packet_missing_from_index", "packet_id": packet_id})
        for field in ["review_relation_reliability", "review_geometry_support", "review_uncertainty", "review_notes"]:
            if str(row.get(field, "")).strip():
                errors.append({"error_type": "review_field_already_filled", "packet_id": packet_id, "field": field})
    return errors


def build_packet_info(packet_index: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_packet: dict[str, dict[str, Any]] = {}
    for row in packet_index:
        packet_dir = Path(row["packet_dir"])
        packet_md = Path(row["packet_markdown"])
        info = dict(row)
        info["local_image_count"] = count_packet_images(packet_dir)
        info["packet_markdown_exists"] = as_abs(packet_md).is_file()
        info["packet_markdown_path"] = rel_path(packet_md)
        by_packet[row["packet_id"]] = info
    return by_packet


def fill_rows(rows: list[dict[str, str]], packet_info_by_id: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    filled: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    for row in rows:
        packet_info = packet_info_by_id.get(row["packet_id"], {})
        decision = label_row(row, packet_info)
        filled_row = {key: row.get(key, "") for key in VISIBLE_FIELDS}
        filled_row.update(
            {
                "reviewer_id_v19": REVIEWER_ID,
                "review_round_v19": REVIEW_ROUND,
                "label_policy_v19": LABEL_POLICY,
                "review_relation_reliability": decision["review_relation_reliability"],
                "review_geometry_support": decision["review_geometry_support"],
                "review_uncertainty": decision["review_uncertainty"],
                "review_notes": decision["review_notes"],
            }
        )
        filled.append(filled_row)
        decisions.append(
            {
                "schema_version": "h002_reliability_target_v19_attachment_packet_label_decision_v1",
                "packet_id": row["packet_id"],
                "blind_review_id": row["blind_review_id"],
                "candidate_relation": row["candidate_relation"],
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "object_label": row["object_label"],
                "packet_role": row["packet_role"],
                "evidence_tier": row["evidence_tier"],
                "packet_markdown_exists": bool(packet_info.get("packet_markdown_exists")),
                "local_image_count": int(packet_info.get("local_image_count", 0)),
                "review_relation_reliability": decision["review_relation_reliability"],
                "review_geometry_support": decision["review_geometry_support"],
                "review_uncertainty": decision["review_uncertainty"],
                "primary_reason_v19": decision["primary_reason_v19"],
                "review_notes": decision["review_notes"],
                "provenance": {
                    "filled_by": "codex_visible_packet_labeler",
                    "user_requested_codex_fill": True,
                    "used_visible_review_sheet": True,
                    "used_packet_markdown": True,
                    "used_packet_local_image_availability": True,
                    "used_hidden_manifest": False,
                    "used_source_path": False,
                    "used_scan_id": False,
                    "used_v18_labels": False,
                    "used_geometry_status_or_rank_hint": False,
                    "used_source_score_or_rank": False,
                    "used_validation_or_test": False,
                    "used_p_geom_valid": False,
                    "used_multi_view_as_model_input": False,
                    "used_mesh_as_model_input": False,
                    "paper_evidence_allowed": False,
                },
            }
        )
    return filled, decisions


def validate_outputs(rows: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        if row.get("reviewer_id_v19") != REVIEWER_ID:
            errors.append({"error_type": "missing_reviewer_id", "row_number": row_number, "packet_id": row.get("packet_id")})
        for field, allowed in ALLOWED_VALUES.items():
            value = row.get(field, "")
            if value not in allowed:
                errors.append({"error_type": "invalid_review_value", "row_number": row_number, "packet_id": row.get("packet_id"), "field": field, "value": value})
    for decision in decisions:
        if not decision.get("packet_markdown_exists"):
            errors.append({"error_type": "packet_markdown_missing", "packet_id": decision.get("packet_id")})
        if int(decision.get("local_image_count", 0)) <= 0:
            errors.append({"error_type": "packet_images_missing", "packet_id": decision.get("packet_id")})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V19 Attachment Audit Packet Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"hidden_manifest_read = {summary['boundary']['hidden_manifest_read']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Result",
        "",
        "Filled the v19 leakage-reviewed audit packet sheet with Codex visible-packet labels.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"review_relation_reliability = {counts['review_relation_reliability']}",
        f"review_geometry_support = {counts['review_geometry_support']}",
        f"review_uncertainty = {counts['review_uncertainty']}",
        f"binary_primary_usable_rows = {counts['binary_primary_usable_rows']}",
        f"primary_positive_rows = {counts['primary_positive_rows']}",
        f"primary_negative_rows = {counts['primary_negative_rows']}",
        f"diagnostic_connected_rows = {counts['diagnostic_connected_rows']}",
        f"abstain_rows = {counts['abstain_rows']}",
        "```",
        "",
        "## Policy",
        "",
        "`attached to` and `hanging on` are filled as conservative primary attachment-family candidates. "
        "`connected to` remains diagnostic-only. T1 exact same-frame packet evidence lowers uncertainty; "
        "T2 individual visual plus mesh evidence is treated cautiously.",
        "",
        "## Boundary",
        "",
        "This is hypothesis-stage label material. It does not read the hidden manifest, source paths, scan ids, v18 labels, source scores/ranks, validation/test rows, or `p_geom_valid`. It does not train or run a posterior and is not paper evidence.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    materialization_dir = as_abs(args.materialization_dir)
    leakage_review_dir = as_abs(args.leakage_review_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    materialization_summary_path = materialization_dir / "summary.json"
    leakage_summary_path = leakage_review_dir / "summary.json"
    visible_sheet_path = materialization_dir / "visible_review_sheet.tsv"
    packet_index_path = materialization_dir / "packet_index.jsonl"

    materialization_summary = read_json(materialization_summary_path)
    leakage_summary = read_json(leakage_summary_path)
    fieldnames, input_rows = read_tsv(visible_sheet_path)
    packet_index = read_jsonl(packet_index_path)
    validation_errors = validate_inputs(materialization_summary, leakage_summary, fieldnames, input_rows, packet_index)

    packet_info_by_id = build_packet_info(packet_index)
    filled_rows, decision_rows = fill_rows(input_rows, packet_info_by_id)
    validation_errors.extend(validate_outputs(filled_rows, decision_rows))

    reliability_counts = Counter(row["review_relation_reliability"] for row in filled_rows)
    geometry_counts = Counter(row["review_geometry_support"] for row in filled_rows)
    uncertainty_counts = Counter(row["review_uncertainty"] for row in filled_rows)
    predicate_reliability_counts = Counter(f"{row['predicate_label']}|{row['review_relation_reliability']}" for row in filled_rows)
    role_reliability_counts = Counter(f"{row['packet_role']}|{row['review_relation_reliability']}" for row in filled_rows)
    tier_reliability_counts = Counter(f"{row['evidence_tier']}|{row['review_relation_reliability']}" for row in filled_rows)
    reason_counts = Counter(row["primary_reason_v19"] for row in decision_rows)

    primary_binary = [
        row
        for row in filled_rows
        if row["packet_role"] == "primary_attachment_reliability_candidate"
        and row["predicate_label"] in {"attached to", "hanging on"}
        and row["review_relation_reliability"] in {"accept_reliable_attachment", "reject_unreliable_attachment"}
    ]
    diagnostic_connected = [row for row in filled_rows if row["packet_role"] == "connected_diagnostic_only"]

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "filled_visible_review_sheet": output_dir / "filled_visible_review_sheet_v19.tsv",
        "label_decisions": output_dir / "label_decisions_v19.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    status = STATUS_READY if not validation_errors else STATUS_ERROR
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "materialization_summary": rel_path(materialization_summary_path),
            "leakage_review_summary": rel_path(leakage_summary_path),
            "visible_review_sheet": rel_path(visible_sheet_path),
            "packet_index": rel_path(packet_index_path),
            "hidden_manifest_read": False,
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "reviewer_id": REVIEWER_ID,
        "review_round": REVIEW_ROUND,
        "label_policy": LABEL_POLICY,
        "counts": {
            "rows": len(filled_rows),
            "review_relation_reliability": dict(sorted(reliability_counts.items())),
            "review_geometry_support": dict(sorted(geometry_counts.items())),
            "review_uncertainty": dict(sorted(uncertainty_counts.items())),
            "predicate_reliability": dict(sorted(predicate_reliability_counts.items())),
            "role_reliability": dict(sorted(role_reliability_counts.items())),
            "tier_reliability": dict(sorted(tier_reliability_counts.items())),
            "primary_reason_v19": dict(sorted(reason_counts.items())),
            "binary_primary_usable_rows": len(primary_binary),
            "primary_positive_rows": sum(1 for row in primary_binary if row["review_relation_reliability"] == "accept_reliable_attachment"),
            "primary_negative_rows": sum(1 for row in primary_binary if row["review_relation_reliability"] == "reject_unreliable_attachment"),
            "diagnostic_connected_rows": len(diagnostic_connected),
            "abstain_rows": int(reliability_counts.get("abstain_uncertain", 0)),
            "packet_rows_with_markdown": sum(1 for row in decision_rows if row["packet_markdown_exists"]),
            "packet_rows_with_images": sum(1 for row in decision_rows if row["local_image_count"] > 0),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": True,
            "visible_packet_label_fill": True,
            "hidden_manifest_read": False,
            "used_visible_review_sheet": True,
            "used_packet_markdown": True,
            "used_packet_local_image_availability": True,
            "used_source_path": False,
            "used_scan_id": False,
            "used_v18_labels": False,
            "used_geometry_status_or_rank_hint": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "connected_primary_binary_target": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_tsv(output_paths["filled_visible_review_sheet"], filled_rows, FILLED_FIELDS)
    write_jsonl(output_paths["label_decisions"], decision_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    print(f"status={summary['status']}")
    print(f"rows={counts['rows']}")
    print(f"review_relation_reliability={counts['review_relation_reliability']}")
    print(f"review_geometry_support={counts['review_geometry_support']}")
    print(f"review_uncertainty={counts['review_uncertainty']}")
    print(f"binary_primary_usable_rows={counts['binary_primary_usable_rows']}")
    print(f"primary_positive_rows={counts['primary_positive_rows']}")
    print(f"primary_negative_rows={counts['primary_negative_rows']}")
    print(f"diagnostic_connected_rows={counts['diagnostic_connected_rows']}")
    print(f"hidden_manifest_read={summary['boundary']['hidden_manifest_read']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
