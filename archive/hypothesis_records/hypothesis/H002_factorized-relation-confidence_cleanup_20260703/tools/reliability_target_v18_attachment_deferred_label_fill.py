#!/usr/bin/env python3
"""Fill H002 v18 attachment-deferred labels using visible fields only."""

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

DEFAULT_CANDIDATE_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_candidate_mining"
DEFAULT_CANDIDATE_SUMMARY = DEFAULT_CANDIDATE_DIR / "summary.json"
DEFAULT_INPUT_SHEET = DEFAULT_CANDIDATE_DIR / "label_ready_sheet_v18.tsv"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v18_attachment_deferred_label_fill"

SCHEMA_VERSION = "h002_reliability_target_v18_attachment_deferred_label_fill_v1"
EXPECTED_CANDIDATE_STATUS = "h002_reliability_target_v18_attachment_deferred_candidate_mining_ready_for_label_fill"
EXPECTED_NEXT_TODO = "reliability_target_v18_attachment_deferred_label_fill"
STATUS_READY = "h002_reliability_target_v18_attachment_deferred_label_filled_codex_proxy_visible_only"
STATUS_ERROR = "h002_reliability_target_v18_attachment_deferred_label_fill_errors"
NEXT_TODO = "reliability_target_v18_attachment_deferred_label_ingestion"

REVIEWER_ID = "codex_proxy_v18_attachment_deferred_visible_only_user_requested"
REVIEW_ROUND = "1"
LABEL_POLICY = "v18_visible_attachment_hanging_conservative_connected_diagnostic"

VISIBLE_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "scene_context_summary_v18",
    "geometry_witness_summary_v18",
    "attachment_witness_summary_v18",
    "coverage_summary_v18",
    "uncertainty_summary_v18",
    "review_question_v18",
    "relation_reliability_state_v18",
    "geometry_support_state_v18",
    "relation_usefulness_state_v18",
    "endpoint_identity_state_v18",
    "coverage_state_v18",
    "primary_reason_v18",
    "uncertainty_reason_v18",
    "review_notes_v18",
]

FILLED_FIELDS = [
    "blind_review_id",
    "review_card",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_family_visible",
    "scene_context_summary_v18",
    "geometry_witness_summary_v18",
    "attachment_witness_summary_v18",
    "coverage_summary_v18",
    "uncertainty_summary_v18",
    "review_question_v18",
    "reviewer_id_v18",
    "review_round_v18",
    "label_policy_v18",
    "relation_reliability_state_v18",
    "geometry_support_state_v18",
    "relation_usefulness_state_v18",
    "endpoint_identity_state_v18",
    "coverage_state_v18",
    "primary_reason_v18",
    "uncertainty_reason_v18",
    "review_notes_v18",
]

ALLOWED_VALUES = {
    "relation_reliability_state_v18": {
        "accept_reliable_attachment",
        "reject_unreliable_attachment",
        "diagnostic_connected_possible",
        "diagnostic_connected_ambiguous",
        "abstain_uncertain",
    },
    "geometry_support_state_v18": {"supports", "contradicts", "ambiguous", "not_evaluable"},
    "relation_usefulness_state_v18": {
        "useful_physical_relation",
        "diagnostic_only",
        "not_a_relation",
        "uncertain",
    },
    "endpoint_identity_state_v18": {
        "clear",
        "generic_or_structural_ambiguous",
        "wrong_direction_or_endpoint",
        "not_evaluable",
    },
    "coverage_state_v18": {"sufficient", "limited", "missing", "not_evaluable"},
    "primary_reason_v18": {
        "clear_attachment_layout",
        "attachment_geometry_contradiction",
        "hanging_anchor_plausible",
        "hanging_anchor_missing_or_support_confound",
        "connected_diagnostic_needs_visual_mesh",
        "endpoint_identity_ambiguous",
        "geometry_evidence_mixed",
        "broad_structural_surface_ambiguous",
        "ordinary_support_or_proximity_confound",
        "coverage_or_visual_evidence_limited",
    },
    "uncertainty_reason_v18": {
        "none",
        "large_box_overlap",
        "thin_structure_missing",
        "functional_connection_needs_visual",
        "structural_surface_ambiguous",
        "support_contact_confound",
        "mixed_3d_cues",
        "generic_endpoint_label",
    },
}

FORBIDDEN_INPUT_FIELDS = {
    "cell_id",
    "provisional",
    "anchor_bucket",
    "rank_band",
    "machine_hint",
    "geometry_status",
    "reason_family",
    "sampling_queue",
    "bucket_top100",
    "label_match",
    "semantic_rank",
    "semantic_score",
    "prediction_id",
    "hidden",
}

GENERIC_LABELS = {"object", "objects", "item", "items", "stuff", "thing", "things"}
STRUCTURAL_LABELS = {"wall", "floor", "ceiling", "door", "doorframe", "window", "room"}
HANGING_ANCHORS = {
    "wall",
    "ceiling",
    "door",
    "doorframe",
    "window",
    "curtain",
    "blinds",
    "rack",
    "shelf",
    "cabinet",
    "kitchen cabinet",
}
ATTACHMENT_ANCHORS = {
    "wall",
    "ceiling",
    "door",
    "doorframe",
    "window",
    "shelf",
    "cabinet",
    "kitchen cabinet",
    "table",
    "desk",
    "bed",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-summary", type=Path, default=DEFAULT_CANDIDATE_SUMMARY)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
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


def parse_choice(text: str, mapping: dict[str, str], default: str) -> str:
    text = norm(text)
    for marker, value in mapping.items():
        if marker in text:
            return value
    return default


def parse_visible_cues(row: dict[str, str]) -> dict[str, Any]:
    geom = norm(row.get("geometry_witness_summary_v18", ""))
    uncertainty = norm(row.get("uncertainty_summary_v18", ""))
    subject = norm(row.get("subject_label"))
    obj = norm(row.get("object_label"))
    return {
        "predicate": norm(row.get("predicate_label")),
        "subject": subject,
        "object": obj,
        "distance_3d": parse_choice(
            geom,
            {
                "very near 3d separation": "very_near",
                "moderate 3d separation": "moderate",
                "wide 3d separation": "wide",
            },
            "unknown",
        ),
        "distance_xy": parse_choice(
            geom,
            {
                "very near horizontal separation": "very_near",
                "moderate horizontal separation": "moderate",
                "wide horizontal separation": "wide",
            },
            "unknown",
        ),
        "overlap": parse_choice(
            geom,
            {
                "large footprint overlap": "large",
                "partial footprint overlap": "partial",
                "little footprint overlap": "little",
            },
            "unknown",
        ),
        "vertical": parse_choice(
            geom,
            {
                "subject center appears above object center": "above",
                "subject center appears below object center": "below",
                "subject and object appear in a similar height band": "similar",
            },
            "unknown",
        ),
        "generic_endpoint": subject in GENERIC_LABELS or obj in GENERIC_LABELS,
        "subject_structural": subject in STRUCTURAL_LABELS,
        "object_structural": obj in STRUCTURAL_LABELS,
        "floor_involved": subject == "floor" or obj == "floor",
        "large_box_overlap": "large boxes can overstate" in uncertainty,
        "thin_structure_missing": "thin contact regions" in uncertainty,
        "functional_connection_needs_visual": "functional connection may need" in uncertainty,
        "structural_surface_ambiguous": "broad structural surfaces" in uncertainty,
        "support_contact_confound": "ordinary support contact may explain" in uncertainty,
        "mixed_3d_cues": "3d cues are mixed" in uncertainty,
    }


def uncertainty_reason(cues: dict[str, Any]) -> str:
    if cues["generic_endpoint"]:
        return "generic_endpoint_label"
    if cues["functional_connection_needs_visual"]:
        return "functional_connection_needs_visual"
    if cues["support_contact_confound"]:
        return "support_contact_confound"
    if cues["structural_surface_ambiguous"]:
        return "structural_surface_ambiguous"
    if cues["thin_structure_missing"]:
        return "thin_structure_missing"
    if cues["large_box_overlap"]:
        return "large_box_overlap"
    if cues["mixed_3d_cues"]:
        return "mixed_3d_cues"
    return "none"


def base_result(
    relation: str,
    geometry: str,
    usefulness: str,
    endpoint: str,
    coverage: str,
    reason: str,
    uncertainty: str,
    note: str,
) -> dict[str, str]:
    return {
        "relation_reliability_state_v18": relation,
        "geometry_support_state_v18": geometry,
        "relation_usefulness_state_v18": usefulness,
        "endpoint_identity_state_v18": endpoint,
        "coverage_state_v18": coverage,
        "primary_reason_v18": reason,
        "uncertainty_reason_v18": uncertainty,
        "review_notes_v18": note,
    }


def endpoint_problem(cues: dict[str, Any]) -> dict[str, str] | None:
    if cues["generic_endpoint"]:
        return base_result(
            "abstain_uncertain",
            "ambiguous",
            "uncertain",
            "generic_or_structural_ambiguous",
            "sufficient",
            "endpoint_identity_ambiguous",
            "generic_endpoint_label",
            "codex v18 visible-only: endpoint label is too generic for a reliable attachment-family decision",
        )
    if cues["subject"] in {"wall", "ceiling", "floor"} and cues["object"] not in STRUCTURAL_LABELS:
        return base_result(
            "reject_unreliable_attachment",
            "contradicts",
            "not_a_relation",
            "wrong_direction_or_endpoint",
            "sufficient",
            "broad_structural_surface_ambiguous",
            uncertainty_reason(cues),
            "codex v18 visible-only: broad structural surface as directed subject makes the attachment edge direction unreliable",
        )
    return None


def label_attached(row: dict[str, str], cues: dict[str, Any]) -> dict[str, str]:
    endpoint = endpoint_problem(cues)
    if endpoint is not None:
        return endpoint

    near = cues["distance_3d"] in {"very_near", "moderate"} and cues["distance_xy"] in {"very_near", "moderate"}
    overlap = cues["overlap"] in {"large", "partial"}
    object_anchor = cues["object"] in ATTACHMENT_ANCHORS or cues["object_structural"]
    support_confound = cues["floor_involved"] or cues["support_contact_confound"]

    if support_confound:
        return base_result(
            "reject_unreliable_attachment",
            "contradicts",
            "not_a_relation",
            "clear",
            "limited" if cues["support_contact_confound"] else "sufficient",
            "ordinary_support_or_proximity_confound",
            uncertainty_reason(cues),
            "codex v18 visible-only: visible evidence is better explained as support/proximity than physical attachment",
        )

    if near and overlap and object_anchor and not cues["large_box_overlap"]:
        return base_result(
            "accept_reliable_attachment",
            "supports",
            "useful_physical_relation",
            "clear",
            "sufficient",
            "clear_attachment_layout",
            uncertainty_reason(cues),
            "codex v18 visible-only: endpoint labels and near/overlap geometry support an attachment-like relation",
        )

    if cues["distance_3d"] == "wide" and cues["overlap"] == "little":
        return base_result(
            "reject_unreliable_attachment",
            "contradicts",
            "not_a_relation",
            "clear",
            "sufficient",
            "attachment_geometry_contradiction",
            uncertainty_reason(cues),
            "codex v18 visible-only: wide separation and little overlap contradict an attachment relation",
        )

    if near and overlap and object_anchor:
        return base_result(
            "abstain_uncertain",
            "ambiguous",
            "uncertain",
            "clear",
            "limited",
            "coverage_or_visual_evidence_limited",
            uncertainty_reason(cues),
            "codex v18 visible-only: geometry is plausible but ambiguity flags make the attachment boundary uncertain",
        )

    return base_result(
        "abstain_uncertain",
        "ambiguous",
        "uncertain",
        "clear",
        "sufficient",
        "geometry_evidence_mixed",
        uncertainty_reason(cues),
        "codex v18 visible-only: attachment cues are mixed or insufficient for a binary decision",
    )


def label_hanging(row: dict[str, str], cues: dict[str, Any]) -> dict[str, str]:
    endpoint = endpoint_problem(cues)
    if endpoint is not None:
        return endpoint

    near = cues["distance_3d"] in {"very_near", "moderate"} and cues["distance_xy"] in {"very_near", "moderate"}
    overlap = cues["overlap"] in {"large", "partial"}
    plausible_anchor = cues["object"] in HANGING_ANCHORS or cues["object_structural"]
    not_floor_support = not cues["floor_involved"] and not cues["support_contact_confound"]

    if cues["floor_involved"] or cues["support_contact_confound"]:
        return base_result(
            "reject_unreliable_attachment",
            "contradicts",
            "not_a_relation",
            "clear",
            "limited" if cues["support_contact_confound"] else "sufficient",
            "hanging_anchor_missing_or_support_confound",
            uncertainty_reason(cues),
            "codex v18 visible-only: visible evidence suggests floor/support confound rather than hanging",
        )

    if near and overlap and plausible_anchor and not_floor_support:
        return base_result(
            "accept_reliable_attachment",
            "supports",
            "useful_physical_relation",
            "clear",
            "sufficient",
            "hanging_anchor_plausible",
            uncertainty_reason(cues),
            "codex v18 visible-only: near/overlap geometry and anchor-like object support a hanging or mounted relation",
        )

    if cues["distance_3d"] == "wide" or (cues["overlap"] == "little" and not plausible_anchor):
        return base_result(
            "reject_unreliable_attachment",
            "contradicts",
            "not_a_relation",
            "clear",
            "sufficient",
            "hanging_anchor_missing_or_support_confound",
            uncertainty_reason(cues),
            "codex v18 visible-only: hanging relation lacks a nearby plausible anchor in the visible 3D evidence",
        )

    return base_result(
        "abstain_uncertain",
        "ambiguous",
        "uncertain",
        "clear",
        "limited" if cues["thin_structure_missing"] else "sufficient",
        "coverage_or_visual_evidence_limited" if cues["thin_structure_missing"] else "geometry_evidence_mixed",
        uncertainty_reason(cues),
        "codex v18 visible-only: hanging cues are mixed or need finer contact evidence",
    )


def label_connected(row: dict[str, str], cues: dict[str, Any]) -> dict[str, str]:
    near_or_overlap = cues["distance_3d"] in {"very_near", "moderate"} or cues["overlap"] in {"large", "partial"}
    state = "diagnostic_connected_possible" if near_or_overlap and not cues["generic_endpoint"] else "diagnostic_connected_ambiguous"
    geometry = "supports" if near_or_overlap else "ambiguous"
    return base_result(
        state,
        geometry,
        "diagnostic_only",
        "generic_or_structural_ambiguous" if cues["generic_endpoint"] else "clear",
        "limited",
        "connected_diagnostic_needs_visual_mesh",
        "functional_connection_needs_visual" if cues["functional_connection_needs_visual"] else uncertainty_reason(cues),
        "codex v18 visible-only: connected-to is diagnostic only because functional connection can require visual or mesh evidence",
    )


def label_row(row: dict[str, str]) -> dict[str, str]:
    cues = parse_visible_cues(row)
    if cues["predicate"] == "attached to":
        return label_attached(row, cues)
    if cues["predicate"] == "hanging on":
        return label_hanging(row, cues)
    if cues["predicate"] == "connected to":
        return label_connected(row, cues)
    return base_result(
        "abstain_uncertain",
        "not_evaluable",
        "uncertain",
        "not_evaluable",
        "not_evaluable",
        "coverage_or_visual_evidence_limited",
        "mixed_3d_cues",
        "codex v18 visible-only: predicate is outside the v18 attachment label policy",
    )


def validate_inputs(candidate_summary: dict[str, Any], fieldnames: list[str], rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if candidate_summary.get("status") != EXPECTED_CANDIDATE_STATUS:
        errors.append({"error_type": "unexpected_candidate_status", "expected": EXPECTED_CANDIDATE_STATUS, "actual": candidate_summary.get("status")})
    if candidate_summary.get("next_todo") != EXPECTED_NEXT_TODO:
        errors.append({"error_type": "unexpected_candidate_next_todo", "expected": EXPECTED_NEXT_TODO, "actual": candidate_summary.get("next_todo")})
    if candidate_summary.get("validation_errors") != 0:
        errors.append({"error_type": "candidate_validation_errors_present", "actual": candidate_summary.get("validation_errors")})

    boundary = candidate_summary.get("boundary", {})
    expected_false = [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]
    for key in expected_false:
        if boundary.get(key) is not False:
            errors.append({"error_type": "candidate_boundary_violation", "key": key, "actual": boundary.get(key)})
    if boundary.get("label_sheet_created") is not True:
        errors.append({"error_type": "candidate_boundary_violation", "key": "label_sheet_created", "actual": boundary.get("label_sheet_created")})

    expected_rows = candidate_summary.get("counts", {}).get("selected_rows")
    if expected_rows != len(rows):
        errors.append({"error_type": "row_count_mismatch", "expected": expected_rows, "actual": len(rows)})
    if fieldnames != VISIBLE_FIELDS:
        errors.append({"error_type": "visible_columns_mismatch", "expected": VISIBLE_FIELDS, "actual": fieldnames})

    for field in fieldnames:
        lower = field.lower()
        for token in FORBIDDEN_INPUT_FIELDS:
            if token in lower:
                errors.append({"error_type": "forbidden_visible_input_field", "field": field, "token": token})

    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id", "")
        if not blind_id:
            errors.append({"error_type": "missing_blind_review_id", "row_number": row_number})
        if blind_id in seen_ids:
            errors.append({"error_type": "duplicate_blind_review_id", "blind_review_id": blind_id})
        seen_ids.add(blind_id)
        for field in [
            "relation_reliability_state_v18",
            "geometry_support_state_v18",
            "relation_usefulness_state_v18",
            "endpoint_identity_state_v18",
            "coverage_state_v18",
            "primary_reason_v18",
            "uncertainty_reason_v18",
            "review_notes_v18",
        ]:
            if str(row.get(field, "")).strip():
                errors.append({"error_type": "review_field_already_filled", "row_number": row_number, "blind_review_id": blind_id, "field": field})
        if row.get("predicate_label") not in {"attached to", "hanging on", "connected to"}:
            errors.append({"error_type": "unexpected_predicate", "row_number": row_number, "blind_review_id": blind_id, "predicate": row.get("predicate_label")})
    return errors


def fill_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    filled: list[dict[str, str]] = []
    decisions: list[dict[str, Any]] = []
    for row in rows:
        cues = parse_visible_cues(row)
        decision = label_row(row)
        filled_row = {key: row.get(key, "") for key in VISIBLE_FIELDS}
        filled_row.update(
            {
                "reviewer_id_v18": REVIEWER_ID,
                "review_round_v18": REVIEW_ROUND,
                "label_policy_v18": LABEL_POLICY,
                **decision,
            }
        )
        filled.append(filled_row)
        decisions.append(
            {
                "blind_review_id": row.get("blind_review_id"),
                "candidate_relation": row.get("candidate_relation"),
                "subject_label": row.get("subject_label"),
                "predicate_label": row.get("predicate_label"),
                "object_label": row.get("object_label"),
                "relation_family_visible": row.get("relation_family_visible"),
                **cues,
                **decision,
                "reviewer_id_v18": REVIEWER_ID,
                "label_policy_v18": LABEL_POLICY,
            }
        )
    return filled, decisions


def validate_outputs(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row_number, row in enumerate(rows, start=2):
        for field, allowed in ALLOWED_VALUES.items():
            value = row.get(field, "")
            if value not in allowed:
                errors.append({"error_type": "invalid_review_value", "row_number": row_number, "blind_review_id": row.get("blind_review_id"), "field": field, "value": value})
        if row.get("reviewer_id_v18") != REVIEWER_ID:
            errors.append({"error_type": "missing_reviewer_id", "row_number": row_number, "blind_review_id": row.get("blind_review_id")})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 V18 Attachment Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"hidden_manifest_read = {summary['boundary']['hidden_audit_manifest_read']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        "```",
        "",
        "## Result",
        "",
        "Filled the v18 attachment-deferred label sheet with Codex proxy labels using only reviewer-visible fields.",
        "",
        "```text",
        f"rows = {counts['rows']}",
        f"relation_reliability_state_v18 = {counts['relation_reliability_state_v18']}",
        f"geometry_support_state_v18 = {counts['geometry_support_state_v18']}",
        f"binary_primary_usable_rows = {counts['binary_primary_usable_rows']}",
        f"primary_positive_rows = {counts['primary_positive_rows']}",
        f"primary_negative_rows = {counts['primary_negative_rows']}",
        f"diagnostic_rows = {counts['diagnostic_rows']}",
        f"abstain_rows = {counts['abstain_rows']}",
        "```",
        "",
        "## Label Policy",
        "",
        "`attached to` and `hanging on` are filled as conservative primary candidates. `connected to` is filled as diagnostic-only because functional connection can require visual or mesh evidence. Hidden audit metadata was not read or used during fill.",
        "",
        "## Boundary",
        "",
        "This is a hypothesis-stage proxy label fill. It is not target-independence evidence, posterior evidence, validation/test evidence, or paper evidence.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    candidate_summary_path = as_abs(args.candidate_summary)
    input_sheet = as_abs(args.input_sheet)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    candidate_summary = read_json(candidate_summary_path)
    fieldnames, input_rows = read_tsv(input_sheet)
    validation_errors = validate_inputs(candidate_summary, fieldnames, input_rows)
    filled_rows, decision_rows = fill_rows(input_rows)
    validation_errors.extend(validate_outputs(filled_rows))

    reliability_counts = Counter(row["relation_reliability_state_v18"] for row in filled_rows)
    geometry_counts = Counter(row["geometry_support_state_v18"] for row in filled_rows)
    usefulness_counts = Counter(row["relation_usefulness_state_v18"] for row in filled_rows)
    endpoint_counts = Counter(row["endpoint_identity_state_v18"] for row in filled_rows)
    coverage_counts = Counter(row["coverage_state_v18"] for row in filled_rows)
    reason_counts = Counter(row["primary_reason_v18"] for row in filled_rows)
    uncertainty_counts = Counter(row["uncertainty_reason_v18"] for row in filled_rows)
    predicate_reliability_counts = Counter(f"{row['predicate_label']}|{row['relation_reliability_state_v18']}" for row in filled_rows)
    family_reliability_counts = Counter(f"{row['relation_family_visible']}|{row['relation_reliability_state_v18']}" for row in filled_rows)

    primary_binary = [
        row
        for row in filled_rows
        if row["predicate_label"] in {"attached to", "hanging on"}
        and row["relation_reliability_state_v18"] in {"accept_reliable_attachment", "reject_unreliable_attachment"}
    ]
    diagnostic_rows = [row for row in filled_rows if row["predicate_label"] == "connected to"]
    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "filled_label_sheet": output_dir / "filled_label_sheet_v18.tsv",
        "label_decisions": output_dir / "label_decisions_v18.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
    }
    status = STATUS_READY if not validation_errors else STATUS_ERROR
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "candidate_summary": rel_path(candidate_summary_path),
            "input_sheet": rel_path(input_sheet),
            "hidden_manifest_read": False,
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "reviewer_id": REVIEWER_ID,
        "review_round": REVIEW_ROUND,
        "label_policy": LABEL_POLICY,
        "counts": {
            "rows": len(filled_rows),
            "relation_reliability_state_v18": dict(reliability_counts),
            "geometry_support_state_v18": dict(geometry_counts),
            "relation_usefulness_state_v18": dict(usefulness_counts),
            "endpoint_identity_state_v18": dict(endpoint_counts),
            "coverage_state_v18": dict(coverage_counts),
            "primary_reason_v18": dict(reason_counts),
            "uncertainty_reason_v18": dict(uncertainty_counts),
            "predicate_reliability_state_v18": dict(predicate_reliability_counts),
            "family_reliability_state_v18": dict(family_reliability_counts),
            "binary_primary_usable_rows": len(primary_binary),
            "primary_positive_rows": sum(1 for row in primary_binary if row["relation_reliability_state_v18"] == "accept_reliable_attachment"),
            "primary_negative_rows": sum(1 for row in primary_binary if row["relation_reliability_state_v18"] == "reject_unreliable_attachment"),
            "diagnostic_rows": len(diagnostic_rows),
            "abstain_rows": int(reliability_counts.get("abstain_uncertain", 0)),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": True,
            "visible_only_label_fill": True,
            "hidden_audit_manifest_read": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
        },
        "validation_errors": len(validation_errors),
        "next_todo": NEXT_TODO,
    }

    write_tsv(output_paths["filled_label_sheet"], filled_rows, FILLED_FIELDS)
    write_jsonl(output_paths["label_decisions"], decision_rows)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    print(f"status={summary['status']}")
    print(f"rows={summary['counts']['rows']}")
    print(f"labels={summary['counts']['relation_reliability_state_v18']}")
    print(f"geometry_support={summary['counts']['geometry_support_state_v18']}")
    print(f"binary_primary_usable_rows={summary['counts']['binary_primary_usable_rows']}")
    print(f"primary_positive_rows={summary['counts']['primary_positive_rows']}")
    print(f"primary_negative_rows={summary['counts']['primary_negative_rows']}")
    print(f"diagnostic_rows={summary['counts']['diagnostic_rows']}")
    print(f"hidden_manifest_read={summary['boundary']['hidden_audit_manifest_read']}")
    print(f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"next={summary['next_todo']}")
    return 0 if summary["validation_errors"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
