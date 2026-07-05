#!/usr/bin/env python3
"""Fill H002 positive-anchor packet labels from reviewer-visible packet fields only."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

INPUT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_packet_materialization_v1"
OUT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_label_fill_v1"

SCHEMA_VERSION = "h002_attachment_independent_positive_anchor_label_fill_v1"
EXPECTED_INPUT_STATUS = "h002_attachment_independent_positive_anchor_packet_materialization_v1_ready_for_label_fill"
EXPECTED_INPUT_NEXT = "attachment_independent_positive_anchor_label_fill_v1"
STATUS_READY = "h002_attachment_independent_positive_anchor_label_fill_v1_completed"
STATUS_ERROR = "h002_attachment_independent_positive_anchor_label_fill_v1_errors"
NEXT_TODO = "attachment_independent_positive_anchor_label_ingestion_v1"

REVIEWER_ID = "codex_visible_packet_proxy_labeler_v1_user_requested"
REVIEW_ROUND = "1"
LABEL_POLICY = "visible_endpoint_packet_conservative_attachment_v1"

VISIBLE_FIELDS = [
    "candidate_id",
    "packet_request_id",
    "subject_label",
    "predicate_label",
    "object_label",
    "reviewer_visible_relation_text",
    "packet_status",
    "multiview_packet",
    "contact_or_context_sheet",
    "mesh_packet",
    "review_relation_reliability",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "review_notes",
]

FILLED_FIELDS = [
    "candidate_id",
    "packet_request_id",
    "subject_label",
    "predicate_label",
    "object_label",
    "reviewer_visible_relation_text",
    "packet_status",
    "multiview_packet",
    "contact_or_context_sheet",
    "mesh_packet",
    "reviewer_id",
    "review_round",
    "label_policy",
    "decision_reason",
    "packet_image_count",
    "review_relation_reliability",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "review_notes",
]

ALLOWED = {
    "review_relation_reliability": {"accept_reliable", "reject_unreliable", "abstain_uncertain"},
    "review_geometry_support": {"supported", "unsupported", "uncertain"},
    "review_endpoint_identity": {"clear_endpoint_identity", "uncertain_endpoint_identity"},
    "review_coverage": {"sufficient", "limited", "insufficient"},
    "review_uncertainty": {
        "none",
        "visual_ambiguous",
        "mesh_needed",
        "ontology_ambiguous",
        "functional_connection_ambiguous",
        "occlusion_or_viewpoint_limited",
    },
}

FORBIDDEN_NOTE_TOKENS = {
    "_hidden",
    "proxy_role",
    "cell_id",
    "rank_band",
    "source_score",
    "semantic_score",
    "p_geom",
    "scan_id",
    "subject_id",
    "object_id",
    "gt_match",
    "label_match",
}

GENERIC_LABELS = {"object", "objects", "item", "items", "thing", "things", "stuff", "clutter"}

IMPLAUSIBLE_HANGING_SUBJECTS = {
    "bed",
    "bench",
    "chair",
    "dining chair",
    "armchair",
    "sofa",
    "couch",
    "table",
    "desk",
    "side table",
    "nightstand",
    "stool",
    "window",
    "doorframe",
    "door",
    "floor",
    "heater",
    "radiator",
    "bucket",
    "box",
    "pillow",
}

HANGING_SUBJECTS = {
    "curtain",
    "blinds",
    "towel",
    "bag",
    "backpack",
    "clothes",
    "picture",
    "mirror",
    "decoration",
    "light",
    "lamp",
    "stuffed animal",
    "plate",
}

HANGING_ANCHORS = {
    "wall",
    "ceiling",
    "window",
    "doorframe",
    "door",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "curtain",
    "blinds",
}

HANGING_MOUNTABLE_SUBJECTS = {"shelf", "cabinet", "kitchen cabinet", "bath cabinet"}
HANGING_MOUNTING_ANCHORS = {"wall", "ceiling", "doorframe", "door"}
PLANT_HANGING_ANCHORS = {"wall", "ceiling"}
SUPPORT_OR_PROXIMITY_ANCHORS = {
    "bed",
    "bench",
    "chair",
    "dining chair",
    "armchair",
    "sofa",
    "couch",
    "table",
    "desk",
    "side table",
    "nightstand",
    "stool",
    "floor",
    "pillow",
    "box",
    "bucket",
    "object",
    "item",
}

FIXTURE_OR_MOUNTED_OBJECTS = {
    "window",
    "doorframe",
    "door",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "shelf",
    "picture",
    "mirror",
    "decoration",
    "lamp",
    "light",
    "radiator",
    "heater",
    "curtain",
    "blinds",
    "monitor",
    "tv",
    "plant",
}

ATTACHMENT_STRUCTURES = {
    "wall",
    "ceiling",
    "floor",
    "doorframe",
    "window",
    "door",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "shelf",
    "wardrobe",
    "curtain",
    "blinds",
}

MOVABLE_OR_SUPPORT_OBJECTS = {
    "chair",
    "dining chair",
    "armchair",
    "bench",
    "bed",
    "box",
    "bucket",
    "bag",
    "pillow",
    "towel",
    "blanket",
    "clothes",
    "stool",
    "object",
    "item",
    "stuffed animal",
    "plate",
    "side table",
    "table",
    "desk",
    "nightstand",
}

STRUCTURAL_ATTACHMENT_PAIRS = [
    {"wall", "doorframe"},
    {"wall", "window"},
    {"wall", "ceiling"},
    {"wall", "floor"},
    {"door", "doorframe"},
]


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def as_abs(path_text: str) -> Path:
    path = Path(path_text)
    return path if path.is_absolute() else REPO_ROOT / path


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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


def norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def packet_image_count(row: dict[str, str]) -> int:
    packet_path = as_abs(row["multiview_packet"])
    image_dir = packet_path.parent / "images"
    if not image_dir.is_dir():
        return 0
    return sum(1 for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"})


def endpoint_identity(subject: str, obj: str) -> str:
    if subject == obj or subject in GENERIC_LABELS or obj in GENERIC_LABELS:
        return "uncertain_endpoint_identity"
    return "clear_endpoint_identity"


def coverage(row: dict[str, str], image_count: int) -> str:
    if row.get("packet_status") != "ready":
        return "insufficient"
    if image_count >= 6 and row.get("contact_or_context_sheet") and row.get("mesh_packet"):
        return "sufficient"
    return "limited"


def decision(
    reliability: str,
    geometry: str,
    endpoint: str,
    coverage_value: str,
    uncertainty: str,
    reason: str,
    note: str,
) -> dict[str, str]:
    return {
        "review_relation_reliability": reliability,
        "review_geometry_support": geometry,
        "review_endpoint_identity": endpoint,
        "review_coverage": coverage_value,
        "review_uncertainty": uncertainty,
        "decision_reason": reason,
        "review_notes": note,
    }


def label_connected(row: dict[str, str], image_count: int) -> dict[str, str]:
    endpoint = endpoint_identity(norm(row["subject_label"]), norm(row["object_label"]))
    cov = coverage(row, image_count)
    return decision(
        "abstain_uncertain",
        "uncertain",
        endpoint,
        cov,
        "functional_connection_ambiguous",
        "connected_diagnostic_requires_functional_evidence",
        "codex visible packet: connected-to is kept diagnostic because functional connection evidence is not established by the packet alone",
    )


def label_hanging(row: dict[str, str], image_count: int) -> dict[str, str]:
    subject = norm(row["subject_label"])
    obj = norm(row["object_label"])
    endpoint = endpoint_identity(subject, obj)
    cov = coverage(row, image_count)
    low_uncertainty = "none" if cov == "sufficient" else "occlusion_or_viewpoint_limited"

    if endpoint == "uncertain_endpoint_identity":
        if subject in GENERIC_LABELS or obj in GENERIC_LABELS:
            return decision(
                "abstain_uncertain",
                "uncertain",
                endpoint,
                cov,
                "visual_ambiguous",
                "generic_endpoint_label",
                "codex visible packet: generic endpoint label prevents a confident hanging relation judgment",
            )
        return decision(
            "reject_unreliable",
            "unsupported",
            endpoint,
            cov,
            "visual_ambiguous",
            "same_label_endpoint",
            "codex visible packet: same-label endpoints do not provide reliable directed hanging evidence",
        )

    if subject in IMPLAUSIBLE_HANGING_SUBJECTS:
        return decision(
            "reject_unreliable",
            "unsupported",
            endpoint,
            cov,
            low_uncertainty,
            "implausible_hanging_subject",
            "codex visible packet: subject category is better explained by support, contact, or proximity than hanging",
        )

    if obj in SUPPORT_OR_PROXIMITY_ANCHORS:
        return decision(
            "reject_unreliable",
            "unsupported",
            endpoint,
            cov,
            low_uncertainty,
            "support_or_proximity_confound",
            "codex visible packet: object category is a support or proximity surface rather than a hanging anchor",
        )

    if subject in HANGING_SUBJECTS and obj in HANGING_ANCHORS:
        return decision(
            "accept_reliable",
            "supported",
            endpoint,
            cov,
            low_uncertainty,
            "plausible_hanging_subject_anchor_pair",
            "codex visible packet: endpoint categories form a plausible hanging or mounted relation",
        )

    if subject == "plant" and obj in PLANT_HANGING_ANCHORS:
        return decision(
            "accept_reliable",
            "supported",
            endpoint,
            cov,
            low_uncertainty,
            "plausible_hanging_plant_anchor_pair",
            "codex visible packet: plant with wall or ceiling anchor is treated as a plausible hanging relation",
        )

    if subject in HANGING_MOUNTABLE_SUBJECTS and obj in HANGING_MOUNTING_ANCHORS:
        return decision(
            "accept_reliable",
            "supported",
            endpoint,
            cov,
            low_uncertainty,
            "plausible_mounted_object_anchor_pair",
            "codex visible packet: mountable subject with wall or ceiling-like anchor is reliable enough for audit accept",
        )

    if obj in HANGING_ANCHORS:
        return decision(
            "abstain_uncertain",
            "uncertain",
            endpoint,
            cov,
            "ontology_ambiguous",
            "anchor_present_but_relation_family_ambiguous",
            "codex visible packet: an anchor exists, but relation could be support, attachment, or proximity rather than hanging",
        )

    return decision(
        "reject_unreliable",
        "unsupported",
        endpoint,
        cov,
        low_uncertainty,
        "missing_hanging_anchor",
        "codex visible packet: endpoint categories do not support a hanging relation",
    )


def label_attached(row: dict[str, str], image_count: int) -> dict[str, str]:
    subject = norm(row["subject_label"])
    obj = norm(row["object_label"])
    endpoint = endpoint_identity(subject, obj)
    cov = coverage(row, image_count)
    low_uncertainty = "none" if cov == "sufficient" else "occlusion_or_viewpoint_limited"

    if endpoint == "uncertain_endpoint_identity":
        if subject in GENERIC_LABELS or obj in GENERIC_LABELS:
            return decision(
                "abstain_uncertain",
                "uncertain",
                endpoint,
                cov,
                "visual_ambiguous",
                "generic_endpoint_label",
                "codex visible packet: generic endpoint label prevents a confident attachment judgment",
            )
        return decision(
            "reject_unreliable",
            "unsupported",
            endpoint,
            cov,
            "visual_ambiguous",
            "same_label_endpoint",
            "codex visible packet: same-label endpoints do not provide reliable directed attachment evidence",
        )

    pair = {subject, obj}
    if any(pair == accepted_pair for accepted_pair in STRUCTURAL_ATTACHMENT_PAIRS):
        return decision(
            "accept_reliable",
            "supported",
            endpoint,
            cov,
            low_uncertainty,
            "canonical_structural_attachment_pair",
            "codex visible packet: structural endpoint pair is a canonical attachment relation",
        )

    fixture_to_structure = (
        subject in FIXTURE_OR_MOUNTED_OBJECTS and obj in ATTACHMENT_STRUCTURES
    ) or (
        obj in FIXTURE_OR_MOUNTED_OBJECTS and subject in ATTACHMENT_STRUCTURES
    )
    subject_is_movable_confounded = subject in MOVABLE_OR_SUPPORT_OBJECTS and obj in ATTACHMENT_STRUCTURES and subject not in FIXTURE_OR_MOUNTED_OBJECTS
    object_is_movable_confounded = obj in MOVABLE_OR_SUPPORT_OBJECTS and subject in ATTACHMENT_STRUCTURES and obj not in FIXTURE_OR_MOUNTED_OBJECTS
    if fixture_to_structure and not subject_is_movable_confounded and not object_is_movable_confounded:
        return decision(
            "accept_reliable",
            "supported",
            endpoint,
            cov,
            low_uncertainty,
            "fixture_or_mounted_object_attachment_pair",
            "codex visible packet: fixture or mounted endpoint with structural anchor supports attachment",
        )

    if subject in MOVABLE_OR_SUPPORT_OBJECTS and obj in MOVABLE_OR_SUPPORT_OBJECTS:
        return decision(
            "reject_unreliable",
            "unsupported",
            endpoint,
            cov,
            low_uncertainty,
            "movable_pair_contact_or_proximity_confound",
            "codex visible packet: movable-object pair is better explained by contact or proximity than attachment",
        )

    if subject in ATTACHMENT_STRUCTURES or obj in ATTACHMENT_STRUCTURES:
        return decision(
            "abstain_uncertain",
            "uncertain",
            endpoint,
            cov,
            "ontology_ambiguous",
            "structural_anchor_without_clear_attachment",
            "codex visible packet: structural anchor exists, but direct attachment evidence is ambiguous",
        )

    return decision(
        "reject_unreliable",
        "unsupported",
        endpoint,
        cov,
        low_uncertainty,
        "missing_attachment_anchor",
        "codex visible packet: endpoint categories do not support an attachment relation",
    )


def label_row(row: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    image_count = packet_image_count(row)
    predicate = row["predicate_label"]
    if predicate == "connected to":
        label = label_connected(row, image_count)
    elif predicate == "hanging on":
        label = label_hanging(row, image_count)
    elif predicate == "attached to":
        label = label_attached(row, image_count)
    else:
        label = decision(
            "abstain_uncertain",
            "uncertain",
            "uncertain_endpoint_identity",
            coverage(row, image_count),
            "ontology_ambiguous",
            "unsupported_predicate_in_this_packet",
            "codex visible packet: predicate is outside the current attachment audit scope",
        )

    filled = {
        **row,
        "reviewer_id": REVIEWER_ID,
        "review_round": REVIEW_ROUND,
        "label_policy": LABEL_POLICY,
        "decision_reason": label["decision_reason"],
        "packet_image_count": image_count,
        "review_relation_reliability": label["review_relation_reliability"],
        "review_geometry_support": label["review_geometry_support"],
        "review_endpoint_identity": label["review_endpoint_identity"],
        "review_coverage": label["review_coverage"],
        "review_uncertainty": label["review_uncertainty"],
        "review_notes": label["review_notes"],
    }
    decision_row = {
        "schema_version": "h002_attachment_positive_anchor_label_decision_v1",
        "candidate_id": row["candidate_id"],
        "packet_request_id": row["packet_request_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "object_label": row["object_label"],
        "reviewer_visible_relation_text": row["reviewer_visible_relation_text"],
        "packet_status": row["packet_status"],
        "packet_image_count": image_count,
        "review_relation_reliability": label["review_relation_reliability"],
        "review_geometry_support": label["review_geometry_support"],
        "review_endpoint_identity": label["review_endpoint_identity"],
        "review_coverage": label["review_coverage"],
        "review_uncertainty": label["review_uncertainty"],
        "decision_reason": label["decision_reason"],
        "review_notes": label["review_notes"],
        "provenance": {
            "filled_by": "codex_visible_packet_proxy_labeler",
            "user_requested_codex_fill": True,
            "used_visible_review_sheet": True,
            "used_packet_paths": True,
            "used_packet_local_image_availability": True,
            "used_hidden_manifest": False,
            "used_source_path": False,
            "used_scan_id": False,
            "used_existing_gt_match_axis": False,
            "used_proxy_role_or_cell_id": False,
            "used_source_score_or_rank": False,
            "used_p_geom_valid": False,
            "used_validation_or_test": False,
            "used_multi_view_as_model_input": False,
            "used_mesh_as_model_input": False,
            "paper_evidence_allowed": False,
        },
    }
    return filled, decision_row


def validate_inputs(summary: dict[str, Any], fields: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_INPUT_STATUS:
        errors.append({"error_type": "unexpected_input_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_INPUT_NEXT:
        errors.append({"error_type": "unexpected_input_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "input_validation_errors_present", "actual": summary.get("validation_errors")})
    if summary.get("counts", {}).get("visible_leakage_hits") != 0:
        errors.append({"error_type": "input_visible_leakage_hits_present", "actual": summary.get("counts", {}).get("visible_leakage_hits")})
    if fields != VISIBLE_FIELDS:
        errors.append({"error_type": "visible_sheet_schema_mismatch", "expected": VISIBLE_FIELDS, "actual": fields})
    if len(rows) != 560:
        errors.append({"error_type": "unexpected_visible_row_count", "expected": 560, "actual": len(rows)})
    seen: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        candidate_id = row.get("candidate_id", "")
        if not candidate_id:
            errors.append({"error_type": "missing_candidate_id", "row_number": row_number})
        elif candidate_id in seen:
            errors.append({"error_type": "duplicate_candidate_id", "candidate_id": candidate_id, "row_number": row_number})
        seen.add(candidate_id)
        if row.get("packet_status") != "ready":
            errors.append({"error_type": "packet_not_ready", "candidate_id": candidate_id, "actual": row.get("packet_status")})
        if row.get("predicate_label") not in {"attached to", "hanging on", "connected to"}:
            errors.append({"error_type": "unexpected_predicate", "candidate_id": candidate_id, "actual": row.get("predicate_label")})
        for field in [
            "review_relation_reliability",
            "review_geometry_support",
            "review_endpoint_identity",
            "review_coverage",
            "review_uncertainty",
            "review_notes",
        ]:
            if str(row.get(field, "")).strip():
                errors.append({"error_type": "review_field_already_filled", "candidate_id": candidate_id, "field": field})
    return errors


def validate_outputs(rows: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        if row.get("reviewer_id") != REVIEWER_ID:
            errors.append({"error_type": "missing_reviewer_id", "row_number": row_number, "candidate_id": row.get("candidate_id")})
        if int(row.get("packet_image_count", 0)) <= 0:
            errors.append({"error_type": "packet_images_missing", "row_number": row_number, "candidate_id": row.get("candidate_id")})
        for field, allowed in ALLOWED.items():
            value = row.get(field, "")
            if value not in allowed:
                errors.append({"error_type": "invalid_review_value", "row_number": row_number, "candidate_id": row.get("candidate_id"), "field": field, "value": value})
        note = str(row.get("review_notes", "")).lower()
        for token in FORBIDDEN_NOTE_TOKENS:
            if token in note:
                errors.append({"error_type": "forbidden_token_in_review_notes", "row_number": row_number, "candidate_id": row.get("candidate_id"), "token": token})
    if len(rows) != len(decisions):
        errors.append({"error_type": "filled_decision_count_mismatch", "filled": len(rows), "decisions": len(decisions)})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Attachment Independent Positive Anchor Label Fill V1",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Label Source",
        "",
        "```text",
        f"reviewer_id = {REVIEWER_ID}",
        f"label_policy = {LABEL_POLICY}",
        "used_hidden_manifest = False",
        "used_source_score_or_rank = False",
        "used_proxy_role_or_cell_id = False",
        "used_p_geom_valid = False",
        "used_validation_or_test = False",
        "```",
        "",
        "The fill uses only reviewer-visible relation fields and packet availability from the packet sheet. "
        "It does not read the materialized hidden manifest.",
        "",
        "## Counts",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"review_relation_reliability = {counts['review_relation_reliability']}",
        f"review_geometry_support = {counts['review_geometry_support']}",
        f"review_endpoint_identity = {counts['review_endpoint_identity']}",
        f"review_coverage = {counts['review_coverage']}",
        f"review_uncertainty = {counts['review_uncertainty']}",
        f"predicate_label = {counts['predicate_label']}",
        f"by_predicate_and_reliability = {counts['by_predicate_and_reliability']}",
        f"primary_binary_preview = {counts['primary_binary_preview']}",
        f"primary_binary_preview_rows = {counts['primary_binary_preview_rows']}",
        f"connected_diagnostic_rows = {counts['connected_diagnostic_rows']}",
        "```",
        "",
        "## Interpretation",
        "",
        "This stage produces independent audit labels for the positive-anchor packet batch. "
        "It intentionally does not balance labels after the fact. The useful question is whether the "
        "post-ingestion target remains identifiable after shortcut controls.",
        "",
        "## Boundary",
        "",
        "- train-only H002 artifact;",
        "- no validation/test data;",
        "- no posterior training;",
        "- no paper evidence promotion;",
        "- no H001 artifact modification;",
        "- `connected to` remains diagnostic and is not part of the primary binary target.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    input_summary = read_json(INPUT_DIR / "summary.json")
    fields, input_rows = read_csv(INPUT_DIR / "visible_review_sheet_with_packets.csv")
    errors = validate_inputs(input_summary, fields, input_rows)

    filled: list[dict[str, Any]] = []
    decisions: list[dict[str, Any]] = []
    if not errors:
        for row in input_rows:
            filled_row, decision_row = label_row(row)
            filled.append(filled_row)
            decisions.append(decision_row)
        errors.extend(validate_outputs(filled, decisions))

    rel_counts = Counter(row.get("review_relation_reliability", "") for row in filled)
    geom_counts = Counter(row.get("review_geometry_support", "") for row in filled)
    endpoint_counts = Counter(row.get("review_endpoint_identity", "") for row in filled)
    coverage_counts = Counter(row.get("review_coverage", "") for row in filled)
    uncertainty_counts = Counter(row.get("review_uncertainty", "") for row in filled)
    predicate_counts = Counter(row.get("predicate_label", "") for row in filled)
    predicate_reliability_counts = Counter(
        (row.get("predicate_label", ""), row.get("review_relation_reliability", "")) for row in filled
    )
    reason_counts = Counter(row.get("decision_reason", "") for row in filled)
    primary_binary = [
        row for row in filled
        if row.get("predicate_label") in {"attached to", "hanging on"}
        and row.get("review_relation_reliability") in {"accept_reliable", "reject_unreliable"}
    ]
    primary_binary_counts = Counter(row["review_relation_reliability"] for row in primary_binary)
    connected_rows = [row for row in filled if row.get("predicate_label") == "connected to"]

    output_paths = {
        "summary": OUT_DIR / "summary.json",
        "report": OUT_DIR / "report.md",
        "filled_visible_review_sheet": OUT_DIR / "filled_visible_review_sheet.csv",
        "label_decisions": OUT_DIR / "label_decisions.jsonl",
        "validation_errors": OUT_DIR / "validation_errors.jsonl",
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "next_todo": NEXT_TODO,
        "input_paths": {
            "materialization_summary": rel_path(INPUT_DIR / "summary.json"),
            "visible_review_sheet_with_packets": rel_path(INPUT_DIR / "visible_review_sheet_with_packets.csv"),
        },
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "counts": {
            "rows": len(filled),
            "review_relation_reliability": dict(sorted(rel_counts.items())),
            "review_geometry_support": dict(sorted(geom_counts.items())),
            "review_endpoint_identity": dict(sorted(endpoint_counts.items())),
            "review_coverage": dict(sorted(coverage_counts.items())),
            "review_uncertainty": dict(sorted(uncertainty_counts.items())),
            "predicate_label": dict(sorted(predicate_counts.items())),
            "by_predicate_and_reliability": {
                f"{predicate}|{label}": count
                for (predicate, label), count in sorted(predicate_reliability_counts.items())
            },
            "decision_reason": dict(sorted(reason_counts.items())),
            "primary_binary_preview": dict(sorted(primary_binary_counts.items())),
            "primary_binary_preview_rows": len(primary_binary),
            "primary_positive_rows": primary_binary_counts.get("accept_reliable", 0),
            "primary_negative_rows": primary_binary_counts.get("reject_unreliable", 0),
            "abstain_rows": rel_counts.get("abstain_uncertain", 0),
            "connected_diagnostic_rows": len(connected_rows),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": True,
            "hidden_manifest_read": False,
            "used_source_path": False,
            "used_scan_id": False,
            "used_existing_gt_match_axis": False,
            "used_proxy_role_or_cell_id": False,
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
        "validation_errors": len(errors),
    }

    write_csv(output_paths["filled_visible_review_sheet"], filled, FILLED_FIELDS)
    write_jsonl(output_paths["label_decisions"], decisions)
    write_jsonl(output_paths["validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)

    print(f"status={summary['status']}")
    print(f"next={summary['next_todo']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"review_relation_reliability={summary['counts']['review_relation_reliability']}")
    print(f"primary_binary_preview={summary['counts']['primary_binary_preview']}")
    print(f"connected_diagnostic_rows={summary['counts']['connected_diagnostic_rows']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
