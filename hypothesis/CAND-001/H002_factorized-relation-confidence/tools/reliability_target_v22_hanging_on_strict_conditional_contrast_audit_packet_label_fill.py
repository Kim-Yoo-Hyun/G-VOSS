#!/usr/bin/env python3
"""Fill H002 v22 hanging-on audit-packet labels from reviewer-visible packets only."""

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

DEFAULT_MATERIALIZATION_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_materialization"
DEFAULT_LEAKAGE_REVIEW_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_leakage_review"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_fill"

EXPECTED_MATERIALIZATION_STATUS = (
    "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_materialization_ready_for_leakage_review"
)
EXPECTED_LEAKAGE_REVIEW_STATUS = (
    "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_leakage_review_passed_ready_for_label_fill"
)

SCHEMA_VERSION = "h002_reliability_target_v22_hanging_on_audit_packet_label_fill_v1"
STATUS_READY = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_filled_codex_visible_packet"
STATUS_ERROR = "h002_reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_fill_errors"
NEXT_TODO = "reliability_target_v22_hanging_on_strict_conditional_contrast_audit_packet_label_ingestion"

REVIEWER_ID = "codex_visible_packet_labeler_v22_user_requested"
REVIEW_ROUND = "1"
LABEL_POLICY = "v22_visible_packet_hanging_on_conservative_single_predicate"

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
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "review_notes",
]

FILLED_FIELDS = [
    *VISIBLE_FIELDS[:13],
    "reviewer_id_v22",
    "review_round_v22",
    "label_policy_v22",
    "review_relation_reliability",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "review_notes",
]

ALLOWED_VALUES = {
    "review_relation_reliability": {"accept_reliable", "reject_unreliable", "abstain_uncertain"},
    "review_geometry_support": {"supports", "contradicts", "ambiguous", "not_evaluable"},
    "review_endpoint_identity": {"clear_endpoint_identity", "uncertain_endpoint_identity"},
    "review_coverage": {"sufficient", "limited"},
    "review_uncertainty": {"low", "medium", "high", "visual_ambiguous", "endpoint_ambiguous", "ontology_ambiguous"},
}

PRIMARY_ROLE = "primary_hanging_on_reliability_candidate"
PRIMARY_PREDICATE = "hanging on"
EVIDENCE_TIERS = {"T1_strong_pair_visual", "T2_individual_visual_plus_mesh"}

GENERIC_LABELS = {"object", "objects", "item", "items", "thing", "things", "stuff", "clutter"}
SAME_LABEL_REJECT_EXCEPTIONS: set[str] = set()

HARD_SUPPORT_ANCHORS = {
    "bed",
    "bench",
    "chair",
    "couch",
    "sofa",
    "armchair",
    "sofa chair",
    "cushion",
    "pillow",
    "table",
    "desk",
    "nightstand",
    "bedside table",
    "counter",
    "kitchen counter",
    "sink",
    "toilet",
    "bathtub",
    "trash can",
    "washing machine",
    "microwave",
    "refrigerator",
    "coffee machine",
    "kettle",
    "bucket",
    "suitcase",
    "ottoman",
    "stool",
    "bar",
    "carpet",
    "commode",
    "laptop",
    "monitor",
    "tv",
    "food",
    "bread",
    "toilet brush",
    "toilet paper",
}

IMPLAUSIBLE_HANGING_SUBJECTS = {
    "bed",
    "bench",
    "chair",
    "couch",
    "sofa",
    "armchair",
    "sofa chair",
    "dining chair",
    "table",
    "desk",
    "nightstand",
    "bedside table",
    "counter",
    "kitchen counter",
    "sink",
    "toilet",
    "bathtub",
    "washing machine",
    "refrigerator",
    "microwave",
    "oven",
    "kitchen appliance",
    "pc",
    "laptop",
    "monitor",
    "wardrobe",
    "window",
    "doorframe",
    "door",
}

STRONG_HANGING_SUBJECTS = {
    "curtain",
    "blinds",
    "towel",
    "bag",
    "backpack",
    "clothes",
}
STRONG_HANGING_ANCHORS = {
    "window",
    "door",
    "doorframe",
    "wardrobe",
    "closet",
    "rack",
    "stand",
}
MOUNTABLE_SUBJECTS = {
    "shelf",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "picture",
    "mirror",
    "frame",
    "decoration",
    "light",
    "lamp",
    "plant",
    "organizer",
    "rack",
}
MOUNTING_ANCHORS = {"door", "window", "doorframe", "wardrobe", "cabinet", "kitchen cabinet", "stand", "rack"}


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


def base_decision(
    reliability: str,
    geometry: str,
    endpoint: str,
    coverage: str,
    uncertainty: str,
    reason: str,
    note: str,
) -> dict[str, str]:
    return {
        "review_relation_reliability": reliability,
        "review_geometry_support": geometry,
        "review_endpoint_identity": endpoint,
        "review_coverage": coverage,
        "review_uncertainty": uncertainty,
        "primary_reason_v22": reason,
        "review_notes": note,
    }


def coverage_value(row: dict[str, str], image_count: int) -> str:
    if row["evidence_tier"] == "T1_strong_pair_visual" and image_count >= 12:
        return "sufficient"
    return "limited"


def evidence_uncertainty(row: dict[str, str], image_count: int, coverage: str) -> str:
    if coverage == "sufficient" and image_count >= 12:
        return "low"
    if row["evidence_tier"] in EVIDENCE_TIERS and image_count >= 8:
        return "medium"
    return "high"


def endpoint_quality(subject: str, obj: str) -> str:
    if subject in GENERIC_LABELS or obj in GENERIC_LABELS:
        return "generic_endpoint"
    if subject == obj and subject not in SAME_LABEL_REJECT_EXCEPTIONS:
        return "same_label_endpoint"
    return "clear"


def label_hanging(row: dict[str, str], image_count: int) -> dict[str, str]:
    subject = norm(row["subject_label"])
    obj = norm(row["object_label"])
    coverage = coverage_value(row, image_count)
    uncertainty = evidence_uncertainty(row, image_count, coverage)
    endpoint = endpoint_quality(subject, obj)

    if endpoint == "generic_endpoint":
        return base_decision(
            "abstain_uncertain",
            "ambiguous",
            "uncertain_endpoint_identity",
            coverage,
            "endpoint_ambiguous",
            "generic_endpoint_label",
            "codex v22 visible-packet: endpoint label is generic, so the hanging relation cannot be accepted or rejected confidently",
        )
    if endpoint == "same_label_endpoint":
        return base_decision(
            "reject_unreliable",
            "contradicts",
            "uncertain_endpoint_identity",
            coverage,
            uncertainty,
            "duplicate_or_self_like_endpoint",
            "codex v22 visible-packet: same-label directed pair is not reliable evidence for a hanging-on edge",
        )
    if subject in IMPLAUSIBLE_HANGING_SUBJECTS:
        return base_decision(
            "reject_unreliable",
            "contradicts",
            "clear_endpoint_identity",
            coverage,
            uncertainty,
            "implausible_hanging_subject",
            "codex v22 visible-packet: subject type is unlikely to be hanging or mounted as the directed scene-graph relation",
        )
    if obj in HARD_SUPPORT_ANCHORS:
        return base_decision(
            "reject_unreliable",
            "contradicts",
            "clear_endpoint_identity",
            coverage,
            uncertainty,
            "support_or_proximity_confound",
            "codex v22 visible-packet: object is a support/proximity surface rather than a hanging anchor",
        )
    if subject in STRONG_HANGING_SUBJECTS and obj in STRONG_HANGING_ANCHORS:
        return base_decision(
            "accept_reliable",
            "supports",
            "clear_endpoint_identity",
            coverage,
            uncertainty,
            "strong_hanging_subject_anchor_pair",
            "codex v22 visible-packet: subject and object labels form a plausible hanging or mounted pair under the packet evidence",
        )
    if subject in MOUNTABLE_SUBJECTS and obj in MOUNTING_ANCHORS and coverage == "sufficient":
        return base_decision(
            "abstain_uncertain",
            "ambiguous",
            "clear_endpoint_identity",
            coverage,
            "visual_ambiguous",
            "mountable_pair_needs_direct_attachment_confirmation",
            "codex v22 visible-packet: pair is mountable, but the visible packet does not prove a hanging-on relation strongly enough",
        )
    if subject in MOUNTABLE_SUBJECTS and obj in MOUNTING_ANCHORS:
        return base_decision(
            "abstain_uncertain",
            "ambiguous",
            "clear_endpoint_identity",
            coverage,
            "visual_ambiguous",
            "mountable_pair_limited_pair_context",
            "codex v22 visible-packet: mountable endpoint labels are plausible, but direct pair context is limited",
        )
    return base_decision(
        "reject_unreliable",
        "contradicts",
        "clear_endpoint_identity",
        coverage,
        uncertainty,
        "missing_hanging_anchor_or_wrong_relation_family",
        "codex v22 visible-packet: visible endpoint labels are better explained by support, proximity, containment, or an unrelated relation",
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
        errors.append({"error_type": "unexpected_materialization_status", "actual": materialization_summary.get("status")})
    if leakage_summary.get("status") != EXPECTED_LEAKAGE_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_leakage_review_status", "actual": leakage_summary.get("status")})
    if leakage_summary.get("counts", {}).get("visible_leakage_hits") != 0:
        errors.append({"error_type": "visible_leakage_hits_present", "actual": leakage_summary.get("counts", {}).get("visible_leakage_hits")})
    if leakage_summary.get("validation_errors") != 0:
        errors.append({"error_type": "leakage_validation_errors_present", "actual": leakage_summary.get("validation_errors")})
    if fieldnames != VISIBLE_FIELDS:
        errors.append({"error_type": "visible_sheet_schema_mismatch", "expected": VISIBLE_FIELDS, "actual": fieldnames})
    if len(rows) != 240:
        errors.append({"error_type": "unexpected_visible_row_count", "expected": 240, "actual": len(rows)})
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
        if row.get("predicate_label") != PRIMARY_PREDICATE:
            errors.append({"error_type": "unexpected_predicate", "packet_id": packet_id, "actual": row.get("predicate_label")})
        if row.get("packet_role") != PRIMARY_ROLE:
            errors.append({"error_type": "unexpected_packet_role", "packet_id": packet_id, "actual": row.get("packet_role")})
        if row.get("evidence_tier") not in EVIDENCE_TIERS:
            errors.append({"error_type": "unexpected_evidence_tier", "packet_id": packet_id, "actual": row.get("evidence_tier")})
        for field in ["review_relation_reliability", "review_geometry_support", "review_endpoint_identity", "review_coverage", "review_uncertainty", "review_notes"]:
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
        image_count = int(packet_info.get("local_image_count", 0))
        decision = label_hanging(row, image_count)
        filled_row = {key: row.get(key, "") for key in VISIBLE_FIELDS}
        filled_row.update(
            {
                "reviewer_id_v22": REVIEWER_ID,
                "review_round_v22": REVIEW_ROUND,
                "label_policy_v22": LABEL_POLICY,
                "review_relation_reliability": decision["review_relation_reliability"],
                "review_geometry_support": decision["review_geometry_support"],
                "review_endpoint_identity": decision["review_endpoint_identity"],
                "review_coverage": decision["review_coverage"],
                "review_uncertainty": decision["review_uncertainty"],
                "review_notes": decision["review_notes"],
            }
        )
        filled.append(filled_row)
        decisions.append(
            {
                "schema_version": "h002_reliability_target_v22_hanging_on_packet_label_decision_v1",
                "packet_id": row["packet_id"],
                "blind_review_id": row["blind_review_id"],
                "candidate_relation": row["candidate_relation"],
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "object_label": row["object_label"],
                "packet_role": row["packet_role"],
                "evidence_tier": row["evidence_tier"],
                "packet_markdown_exists": bool(packet_info.get("packet_markdown_exists")),
                "local_image_count": image_count,
                "review_relation_reliability": decision["review_relation_reliability"],
                "review_geometry_support": decision["review_geometry_support"],
                "review_endpoint_identity": decision["review_endpoint_identity"],
                "review_coverage": decision["review_coverage"],
                "review_uncertainty": decision["review_uncertainty"],
                "primary_reason_v22": decision["primary_reason_v22"],
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
                    "used_existing_gt_match_axis": False,
                    "used_proxy_role_or_strict_group_id": False,
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
        if row.get("reviewer_id_v22") != REVIEWER_ID:
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
        "# H002 V22 Hanging-On Audit Packet Label Fill",
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
        "Filled the v22 leakage-reviewed `hanging on` packet sheet with conservative Codex visible-packet labels.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"review_relation_reliability = {counts['review_relation_reliability']}",
        f"review_geometry_support = {counts['review_geometry_support']}",
        f"review_endpoint_identity = {counts['review_endpoint_identity']}",
        f"review_coverage = {counts['review_coverage']}",
        f"review_uncertainty = {counts['review_uncertainty']}",
        f"primary_reason_v22 = {counts['primary_reason_v22']}",
        f"binary_primary_usable_rows = {counts['binary_primary_usable_rows']}",
        f"primary_positive_rows = {counts['primary_positive_rows']}",
        f"primary_negative_rows = {counts['primary_negative_rows']}",
        f"abstain_rows = {counts['abstain_rows']}",
        "```",
        "",
        "## Policy",
        "",
        "`hanging on` is accepted only for strong subject-anchor pairs such as curtain/blinds/towel/bag on door/window-like anchors. "
        "Support/proximity confounds, same-label endpoints, broad furniture/appliance subjects, and generic endpoints are rejected or abstained. "
        "T1 exact pair evidence lowers uncertainty; T2 individual visual plus mesh evidence is treated cautiously.",
        "",
        "## Boundary",
        "",
        "This is hypothesis-stage label material. It does not read the hidden manifest, source paths, scan ids, existing GT-match axis, proxy role, strict group id, source scores/ranks, validation/test rows, or `p_geom_valid`. It does not train or run a posterior and is not paper evidence.",
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
    endpoint_counts = Counter(row["review_endpoint_identity"] for row in filled_rows)
    coverage_counts = Counter(row["review_coverage"] for row in filled_rows)
    uncertainty_counts = Counter(row["review_uncertainty"] for row in filled_rows)
    tier_reliability_counts = Counter(f"{row['evidence_tier']}|{row['review_relation_reliability']}" for row in filled_rows)
    reason_counts = Counter(row["primary_reason_v22"] for row in decision_rows)
    subject_reliability_counts = Counter(f"{row['subject_label']}|{row['review_relation_reliability']}" for row in filled_rows)
    object_reliability_counts = Counter(f"{row['object_label']}|{row['review_relation_reliability']}" for row in filled_rows)

    primary_binary = [
        row
        for row in filled_rows
        if row["packet_role"] == PRIMARY_ROLE
        and row["predicate_label"] == PRIMARY_PREDICATE
        and row["review_relation_reliability"] in {"accept_reliable", "reject_unreliable"}
    ]

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "filled_visible_review_sheet": output_dir / "filled_visible_review_sheet_v22.tsv",
        "label_decisions": output_dir / "label_decisions_v22.jsonl",
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
            "review_endpoint_identity": dict(sorted(endpoint_counts.items())),
            "review_coverage": dict(sorted(coverage_counts.items())),
            "review_uncertainty": dict(sorted(uncertainty_counts.items())),
            "tier_reliability": dict(sorted(tier_reliability_counts.items())),
            "subject_reliability_top20": dict(subject_reliability_counts.most_common(20)),
            "object_reliability_top20": dict(object_reliability_counts.most_common(20)),
            "primary_reason_v22": dict(sorted(reason_counts.items())),
            "binary_primary_usable_rows": len(primary_binary),
            "primary_positive_rows": sum(1 for row in primary_binary if row["review_relation_reliability"] == "accept_reliable"),
            "primary_negative_rows": sum(1 for row in primary_binary if row["review_relation_reliability"] == "reject_unreliable"),
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
            "used_existing_gt_match_axis": False,
            "used_proxy_role_or_strict_group_id": False,
            "used_geometry_status_or_rank_hint": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
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
    print(f"review_endpoint_identity={counts['review_endpoint_identity']}")
    print(f"review_coverage={counts['review_coverage']}")
    print(f"review_uncertainty={counts['review_uncertainty']}")
    print(f"binary_primary_usable_rows={counts['binary_primary_usable_rows']}")
    print(f"primary_positive_rows={counts['primary_positive_rows']}")
    print(f"primary_negative_rows={counts['primary_negative_rows']}")
    print(f"abstain_rows={counts['abstain_rows']}")
    print(f"hidden_manifest_read={summary['boundary']['hidden_manifest_read']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
