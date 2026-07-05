#!/usr/bin/env python3
"""Fill support/vertical v2 factual-axis label sheet without direct targets."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_READINESS_DIR = RGA_ROOT / "independent_support_vertical_v2_label_readiness_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_label_fill_codex_ver"

REVIEWER_ID = "(codex_ver_support_vertical_v2_factual_axes)"
REVIEW_ROUND = "1"
LABEL_SOURCE = "codex_ver_support_vertical_v2_factual_axes_bootstrap"

GENERIC_LABELS = {
    "",
    "object",
    "objects",
    "item",
    "items",
    "clutter",
    "garbage",
    "unknown",
}
ROOM_SURFACE_LABELS = {"floor", "wall", "ceiling"}
SUPPORT_SURFACES = {
    "floor",
    "desk",
    "table",
    "couch table",
    "chair",
    "armchair",
    "bed",
    "shelf",
    "cabinet",
    "kitchen cabinet",
    "bath cabinet",
    "wardrobe",
    "nightstand",
    "tv stand",
    "stand",
    "bathtub",
    "commode",
    "sink",
    "toilet",
    "box",
}
WALL_MOUNTED_CANDIDATES = {
    "mirror",
    "frame",
    "picture",
    "toilet paper",
    "towel",
    "shower curtain",
    "sink",
    "bidet",
}
INFORMATIVE_VERTICAL_PAIRS = {
    ("sink", "bath cabinet"),
    ("scale", "bath cabinet"),
    ("bath cabinet", "scale"),
    ("toilet paper", "toilet brush"),
    ("toilet paper dispenser", "toilet"),
    ("mirror", "sink"),
    ("mirror", "toilet brush"),
    ("shelf", "armchair"),
    ("window", "bench"),
    ("window", "desk"),
    ("book", "box"),
}

V2_COMPLETION_FIELDS = [
    "reviewer_id",
    "review_round",
    "endpoint_validity_v2",
    "pair_visibility_v2",
    "relation_geometry_answer_v2",
    "geometry_evidence_strength_v2",
    "relation_informativeness_v2",
    "ontology_fit_v2",
    "uncertainty_reason_v2",
    "audit_notes_v2",
]

FORBIDDEN_OUTPUT_HEADER_FRAGMENTS = [
    "binary_target",
    "target_y",
    "posterior",
    "relation_reliability",
    "independent_relation_label",
    "label_use",
    "confidence",
    "geometry_status",
    "rank_band",
    "label_match",
    "proposed_audit_role",
    "prediction_id",
    "p_geom",
    "semantic_score",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-dir", type=Path, default=DEFAULT_READINESS_DIR)
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


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


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def lower(row: dict[str, str], key: str) -> str:
    return str(row.get(key) or "").strip().lower()


def safe_float(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        value = float(str(row.get(key, "")).strip())
    except (TypeError, ValueError):
        return default
    if math.isnan(value) or math.isinf(value):
        return default
    return value


def is_generic(label: str) -> bool:
    return label in GENERIC_LABELS


def packet_visibility(row: dict[str, str], endpoint_validity: str, uncertain: bool = False) -> str:
    if endpoint_validity == "uncertain":
        return "uncertain"
    if uncertain:
        return "uncertain"
    if str(row.get("evidence_packet_status") or "") == "ready_with_packet_caveat":
        return "partially_visible"
    return "visible"


def support_contact_axes(row: dict[str, str]) -> dict[str, str]:
    subject = lower(row, "subject_label")
    obj = lower(row, "object_label")
    pred = lower(row, "predicate_label")
    gap = safe_float(row, "witness_support_contact_gap_abs")
    overlap = max(
        safe_float(row, "witness_support_contact_xy_overlap"),
        safe_float(row, "witness_subject_overlap_xy"),
        safe_float(row, "witness_object_overlap_xy"),
    )
    norm_xy = safe_float(row, "witness_normalized_distance_xy")

    if is_generic(subject) or is_generic(obj):
        return {
            "endpoint_validity_v2": "uncertain",
            "relation_geometry_answer_v2": "not_evaluable",
            "geometry_evidence_strength_v2": "none",
            "relation_informativeness_v2": "uncertain",
            "ontology_fit_v2": "uncertain",
            "uncertainty_reason_v2": "endpoint_identity",
            "audit_notes_v2": "codex_ver: generic endpoint label prevents factual support/contact judgment",
        }

    if subject in {"floor", "ceiling"} and pred in {"lying on", "standing on", "supported by"}:
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "contradicts_predicate",
            "geometry_evidence_strength_v2": "strong",
            "relation_informativeness_v2": "uncertain",
            "ontology_fit_v2": "ontology_mismatch",
            "uncertainty_reason_v2": "none",
            "audit_notes_v2": "codex_ver: room surface as supported subject contradicts support/contact predicate",
        }

    if subject == "wall" and pred in {"lying on", "standing on"}:
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "contradicts_predicate",
            "geometry_evidence_strength_v2": "moderate",
            "relation_informativeness_v2": "uncertain",
            "ontology_fit_v2": "ontology_mismatch",
            "uncertainty_reason_v2": "none",
            "audit_notes_v2": "codex_ver: wall is not a natural subject for lying/standing-on support",
        }

    if obj in ROOM_SURFACE_LABELS:
        support_like = overlap >= 0.10 or norm_xy <= 0.80 or (obj == "floor" and gap <= 1.25)
        if obj == "wall" and subject in WALL_MOUNTED_CANDIDATES and norm_xy <= 0.65:
            return {
                "endpoint_validity_v2": "both_valid",
                "relation_geometry_answer_v2": "supports_predicate",
                "geometry_evidence_strength_v2": "moderate",
                "relation_informativeness_v2": "informative",
                "ontology_fit_v2": "better_alternative_predicate",
                "uncertainty_reason_v2": "ontology_ambiguity",
                "audit_notes_v2": "codex_ver: wall contact is plausible but attached-to may be the better predicate",
            }
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "supports_predicate" if support_like else "ambiguous",
            "geometry_evidence_strength_v2": "moderate" if support_like else "weak",
            "relation_informativeness_v2": "redundant_room_structure",
            "ontology_fit_v2": "fits_predicate" if support_like else "uncertain",
            "uncertainty_reason_v2": "dense_relation" if support_like else "weak_geometry",
            "audit_notes_v2": "codex_ver: support/contact with room surface is geometrically plausible but weakly informative",
        }

    if gap <= 0.40 and overlap >= 0.20 and obj in SUPPORT_SURFACES:
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "supports_predicate",
            "geometry_evidence_strength_v2": "strong",
            "relation_informativeness_v2": "informative",
            "ontology_fit_v2": "fits_predicate",
            "uncertainty_reason_v2": "none",
            "audit_notes_v2": "codex_ver: small support gap, sufficient xy overlap, and plausible support surface",
        }

    if gap <= 1.00 and overlap >= 0.10 and obj in SUPPORT_SURFACES:
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "supports_predicate",
            "geometry_evidence_strength_v2": "moderate",
            "relation_informativeness_v2": "informative",
            "ontology_fit_v2": "fits_predicate",
            "uncertainty_reason_v2": "none",
            "audit_notes_v2": "codex_ver: support/contact witness is plausible but moderate-strength",
        }

    if gap > 1.75 and overlap < 0.10:
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "contradicts_predicate",
            "geometry_evidence_strength_v2": "moderate",
            "relation_informativeness_v2": "uncertain",
            "ontology_fit_v2": "fits_predicate",
            "uncertainty_reason_v2": "weak_geometry",
            "audit_notes_v2": "codex_ver: large support/contact gap with little projected overlap",
        }

    return {
        "endpoint_validity_v2": "both_valid",
        "relation_geometry_answer_v2": "ambiguous",
        "geometry_evidence_strength_v2": "weak",
        "relation_informativeness_v2": "uncertain",
        "ontology_fit_v2": "uncertain",
        "uncertainty_reason_v2": "weak_geometry",
        "audit_notes_v2": "codex_ver: support/contact evidence is not decisive from visible witness fields",
    }


def relative_vertical_axes(row: dict[str, str]) -> dict[str, str]:
    subject = lower(row, "subject_label")
    obj = lower(row, "object_label")
    pred = lower(row, "predicate_label")
    signed_margin = safe_float(row, "witness_relative_vertical_signed_margin")
    sign_agree = safe_float(row, "witness_relative_vertical_sign_agreement")
    abs_margin = abs(signed_margin)

    if is_generic(subject) or is_generic(obj):
        return {
            "endpoint_validity_v2": "uncertain",
            "relation_geometry_answer_v2": "not_evaluable",
            "geometry_evidence_strength_v2": "none",
            "relation_informativeness_v2": "uncertain",
            "ontology_fit_v2": "uncertain",
            "uncertainty_reason_v2": "endpoint_identity",
            "audit_notes_v2": "codex_ver: generic endpoint label prevents factual vertical-order judgment",
        }

    if sign_agree < 0.5 and abs_margin >= 0.20:
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "contradicts_predicate",
            "geometry_evidence_strength_v2": "strong" if abs_margin >= 0.50 else "moderate",
            "relation_informativeness_v2": "uncertain",
            "ontology_fit_v2": "fits_predicate",
            "uncertainty_reason_v2": "none",
            "audit_notes_v2": "codex_ver: vertical witness direction contradicts predicate direction",
        }

    if abs_margin < 0.15:
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "ambiguous",
            "geometry_evidence_strength_v2": "weak",
            "relation_informativeness_v2": "uncertain",
            "ontology_fit_v2": "uncertain",
            "uncertainty_reason_v2": "weak_geometry",
            "audit_notes_v2": "codex_ver: vertical margin is too small for confident factual judgment",
        }

    if subject in ROOM_SURFACE_LABELS or obj in ROOM_SURFACE_LABELS:
        supported = sign_agree >= 0.5
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "supports_predicate" if supported else "ambiguous",
            "geometry_evidence_strength_v2": "moderate" if supported and abs_margin >= 0.25 else "weak",
            "relation_informativeness_v2": "redundant_room_structure",
            "ontology_fit_v2": "fits_predicate" if supported else "uncertain",
            "uncertainty_reason_v2": "dense_relation" if supported else "weak_geometry",
            "audit_notes_v2": "codex_ver: vertical relation involving room structure is geometrically checkable but weakly informative",
        }

    if subject == obj and sign_agree >= 0.5:
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "supports_predicate",
            "geometry_evidence_strength_v2": "moderate" if abs_margin >= 0.25 else "weak",
            "relation_informativeness_v2": "uncertain",
            "ontology_fit_v2": "uncertain",
            "uncertainty_reason_v2": "needs_multiview_or_mesh",
            "audit_notes_v2": "codex_ver: same-class vertical relation needs instance-level visual confirmation",
        }

    if (subject, obj) in INFORMATIVE_VERTICAL_PAIRS and sign_agree >= 0.5:
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "supports_predicate",
            "geometry_evidence_strength_v2": "strong" if abs_margin >= 0.50 else "moderate",
            "relation_informativeness_v2": "informative",
            "ontology_fit_v2": "fits_predicate",
            "uncertainty_reason_v2": "none",
            "audit_notes_v2": "codex_ver: category pair and vertical witness support an informative relation",
        }

    if sign_agree >= 0.5 and abs_margin >= 0.25:
        return {
            "endpoint_validity_v2": "both_valid",
            "relation_geometry_answer_v2": "supports_predicate",
            "geometry_evidence_strength_v2": "moderate",
            "relation_informativeness_v2": "informative",
            "ontology_fit_v2": "fits_predicate",
            "uncertainty_reason_v2": "none",
            "audit_notes_v2": "codex_ver: vertical witness supports predicate; informativeness remains bootstrap-level",
        }

    return {
        "endpoint_validity_v2": "both_valid",
        "relation_geometry_answer_v2": "ambiguous",
        "geometry_evidence_strength_v2": "weak",
        "relation_informativeness_v2": "uncertain",
        "ontology_fit_v2": "uncertain",
        "uncertainty_reason_v2": "weak_geometry",
        "audit_notes_v2": "codex_ver: vertical relation is ambiguous under visible witness fields",
    }


def assign_axes(row: dict[str, str]) -> dict[str, str]:
    family = lower(row, "predicate_family")
    if family == "support_contact":
        axes = support_contact_axes(row)
    elif family == "relative_vertical":
        axes = relative_vertical_axes(row)
    else:
        axes = {
            "endpoint_validity_v2": "uncertain",
            "relation_geometry_answer_v2": "not_evaluable",
            "geometry_evidence_strength_v2": "none",
            "relation_informativeness_v2": "uncertain",
            "ontology_fit_v2": "uncertain",
            "uncertainty_reason_v2": "other",
            "audit_notes_v2": "codex_ver: predicate family is outside selected support/vertical scope",
        }
    axes["pair_visibility_v2"] = packet_visibility(
        row,
        axes["endpoint_validity_v2"],
        uncertain=axes["relation_geometry_answer_v2"] == "not_evaluable",
    )
    return axes


def fill_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    filled: list[dict[str, str]] = []
    for row in rows:
        output = dict(row)
        output.update(
            {
                "reviewer_id": REVIEWER_ID,
                "review_round": REVIEW_ROUND,
                **assign_axes(row),
            }
        )
        filled.append(output)
    return filled


def validate_rows(rows: list[dict[str, str]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = schema["allowed_review_values"]
    required = schema["required_completion_fields"]
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id", "")
        for field in required:
            value = str(row.get(field, "")).strip()
            if not value:
                errors.append(
                    {
                        "error_type": "missing_required_completion_field",
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                    }
                )
                continue
            if field in allowed and value not in allowed[field]:
                errors.append(
                    {
                        "error_type": "invalid_completion_value",
                        "row_number": row_number,
                        "blind_review_id": blind_id,
                        "field": field,
                        "value": value,
                        "allowed": allowed[field],
                    }
                )
        if row.get("reviewer_id") != REVIEWER_ID:
            errors.append(
                {
                    "error_type": "unexpected_reviewer_id",
                    "row_number": row_number,
                    "blind_review_id": blind_id,
                    "value": row.get("reviewer_id"),
                }
            )
    return errors


def output_header_errors(fieldnames: list[str]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for field in fieldnames:
        lower_field = field.lower()
        hits = [fragment for fragment in FORBIDDEN_OUTPUT_HEADER_FRAGMENTS if fragment in lower_field]
        if hits:
            errors.append({"error_type": "forbidden_output_header", "field": field, "matches": hits})
    return errors


def factual_records(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in rows:
        records.append(
            {
                "schema_version": "h002_support_vertical_v2_factual_label_v1",
                "label_source": LABEL_SOURCE,
                "not_human_confirmed": True,
                "paper_evidence_allowed": False,
                "posterior_claim_allowed": False,
                "hidden_reference_used": False,
                "direct_reliability_target_filled": False,
                "validation_used": False,
                "test_used": False,
                "blind_review_id": row["blind_review_id"],
                "audit_scope": row["audit_scope"],
                "scan_id": row["scan_id"],
                "scene_context_id": row["scene_context_id"],
                "subject_id": row["subject_id"],
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "predicate_family": row["predicate_family"],
                "object_id": row["object_id"],
                "object_label": row["object_label"],
                "evidence_packet_status": row["evidence_packet_status"],
                "endpoint_validity_v2": row["endpoint_validity_v2"],
                "pair_visibility_v2": row["pair_visibility_v2"],
                "relation_geometry_answer_v2": row["relation_geometry_answer_v2"],
                "geometry_evidence_strength_v2": row["geometry_evidence_strength_v2"],
                "relation_informativeness_v2": row["relation_informativeness_v2"],
                "ontology_fit_v2": row["ontology_fit_v2"],
                "uncertainty_reason_v2": row["uncertainty_reason_v2"],
                "audit_notes_v2": row["audit_notes_v2"],
            }
        )
    return records


def nested_axis_counts(rows: list[dict[str, str]], group_key: str, axis: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[row[group_key]][row[axis]] += 1
    return {key: dict(sorted(value.items())) for key, value in sorted(grouped.items())}


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    axes = [
        "endpoint_validity_v2",
        "pair_visibility_v2",
        "relation_geometry_answer_v2",
        "geometry_evidence_strength_v2",
        "relation_informativeness_v2",
        "ontology_fit_v2",
        "uncertainty_reason_v2",
    ]
    return {
        "rows": len(rows),
        "family_counts": dict(sorted(Counter(row["predicate_family"] for row in rows).items())),
        "predicate_counts": dict(sorted(Counter(row["predicate_label"] for row in rows).items())),
        "packet_status_counts": dict(sorted(Counter(row["evidence_packet_status"] for row in rows).items())),
        "axis_counts": {axis: dict(sorted(Counter(row[axis] for row in rows).items())) for axis in axes},
        "relation_geometry_by_family": nested_axis_counts(rows, "predicate_family", "relation_geometry_answer_v2"),
        "informativeness_by_family": nested_axis_counts(rows, "predicate_family", "relation_informativeness_v2"),
        "ontology_fit_by_family": nested_axis_counts(rows, "predicate_family", "ontology_fit_v2"),
        "uncertainty_by_family": nested_axis_counts(rows, "predicate_family", "uncertainty_reason_v2"),
    }


def split_rows(rows: list[dict[str, str]], family: str) -> list[dict[str, str]]:
    return [row for row in rows if row["predicate_family"] == family]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Support/Vertical V2 Factual-Axis Label Fill",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage fill.",
        "- This is Codex-version factual-axis bootstrap, not human-confirmed paper evidence.",
        "- Direct relation reliability label and binary target are not filled in this stage.",
        "- Hidden metadata, source score/rank, p_geom_valid, geometry_status, and label-match fields are not read.",
        "- Multi-view/mesh packet paths remain audit pointers, not posterior inputs.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| rows | {counts['rows']} |",
        f"| support_contact rows | {counts['family_counts'].get('support_contact', 0)} |",
        f"| relative_vertical rows | {counts['family_counts'].get('relative_vertical', 0)} |",
        f"| fill validation errors | {summary['fill_validation_error_count']} |",
        f"| output header errors | {summary['output_header_error_count']} |",
        "",
        "## Axis Counts",
        "",
    ]
    for axis, axis_counts in counts["axis_counts"].items():
        lines.extend([f"### `{axis}`", "", "| Value | Rows |", "| --- | ---: |"])
        for value, count in axis_counts.items():
            lines.append(f"| `{value}` | {count} |")
        lines.append("")
    lines.extend(
        [
            "## Family Breakdown",
            "",
            "| Family | Geometry Answer | Informativeness | Ontology Fit |",
            "| --- | --- | --- | --- |",
        ]
    )
    families = sorted(counts["family_counts"])
    for family in families:
        geom = ", ".join(f"{k}:{v}" for k, v in counts["relation_geometry_by_family"][family].items())
        info = ", ".join(f"{k}:{v}" for k, v in counts["informativeness_by_family"][family].items())
        onto = ", ".join(f"{k}:{v}" for k, v in counts["ontology_fit_by_family"][family].items())
        lines.append(f"| `{family}` | {geom} | {info} | {onto} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Output Files",
            "",
            "```text",
            summary["output_paths"]["completed_sheet"],
            summary["output_paths"]["factual_labels"],
            summary["output_paths"]["fill_validation_errors"],
            summary["output_paths"]["header_errors"],
            "```",
            "",
            "## Next TODO",
            "",
            summary["next_todo"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    readiness_dir = as_abs(args.readiness_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    readiness = read_json(readiness_dir / "summary.json")
    if readiness.get("status") != "full_train_independent_support_vertical_v2_label_readiness_ready_for_fill":
        raise RuntimeError(f"v2 label readiness is not ready: {readiness.get('status')}")
    schema = read_json(readiness_dir / "v2_completion_schema.json")
    source_sheet = readiness_dir / "support_vertical_v2_label_fill_sheet.tsv"
    fieldnames, rows = read_tsv(source_sheet)
    filled_rows = fill_rows(rows)
    fill_errors = validate_rows(filled_rows, schema)
    header_errors = output_header_errors(fieldnames)
    records = factual_records(filled_rows)
    counts = summarize(filled_rows)

    output_paths = {
        "summary_json": output_dir / "summary.json",
        "report_md": output_dir / "report.md",
        "completed_sheet": output_dir / "completed_support_vertical_v2_label_fill_sheet_codex_ver.tsv",
        "completed_support_contact_sheet": output_dir / "completed_support_contact_v2_label_fill_sheet_codex_ver.tsv",
        "completed_relative_vertical_sheet": output_dir / "completed_relative_vertical_v2_label_fill_sheet_codex_ver.tsv",
        "factual_labels": output_dir / "factual_labels.jsonl",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
        "header_errors": output_dir / "header_errors.jsonl",
    }
    errors = fill_errors + header_errors
    status = (
        "full_train_independent_support_vertical_v2_labels_filled_codex_ver"
        if not errors
        else "full_train_independent_support_vertical_v2_label_fill_has_errors"
    )
    next_todo = (
        "full_train_independent_support_vertical_v2_label_ingestion"
        if not errors
        else "fix_full_train_independent_support_vertical_v2_label_fill_errors"
    )
    summary = {
        "schema_version": "h002_full_train_independent_support_vertical_v2_label_fill_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation_used": False,
        "test_used": False,
        "input": {
            "readiness_summary": rel_path(readiness_dir / "summary.json"),
            "completion_schema": rel_path(readiness_dir / "v2_completion_schema.json"),
            "source_sheet": rel_path(source_sheet),
            "readiness_status": readiness.get("status"),
        },
        "boundary": {
            "split": "train_only",
            "selected_scope": ["support_contact", "relative_vertical"],
            "label_source": LABEL_SOURCE,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_reference_read": False,
            "hidden_target_metadata_used": False,
            "source_score_or_rank_used": False,
            "p_geom_valid_used": False,
            "geometry_status_used": False,
            "direct_reliability_label_filled": False,
            "binary_target_filled": False,
            "multi_view_as_model_input": False,
            "trains_new_posterior": False,
        },
        "counts": counts,
        "fill_validation_error_count": len(fill_errors),
        "output_header_error_count": len(header_errors),
        "decision": (
            "Codex-version v2 factual axes are filled from visible relation fields and raw witness values only. "
            "This locks a bootstrap label surface for post-label ingestion, where geometry-validity and "
            "relation-reliability targets may be derived separately."
        ),
        "next_todo": next_todo,
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
    }

    write_tsv(output_paths["completed_sheet"], fieldnames, filled_rows)
    write_tsv(output_paths["completed_support_contact_sheet"], fieldnames, split_rows(filled_rows, "support_contact"))
    write_tsv(output_paths["completed_relative_vertical_sheet"], fieldnames, split_rows(filled_rows, "relative_vertical"))
    write_jsonl(output_paths["factual_labels"], records)
    write_jsonl(output_paths["fill_validation_errors"], fill_errors)
    write_jsonl(output_paths["header_errors"], header_errors)
    write_json(output_paths["summary_json"], summary)
    write_report(output_paths["report_md"], summary)

    print(
        "status={status} validation_used={validation_used} test_used={test_used} rows={rows} "
        "support={support} vertical={vertical} fill_errors={fill_errors} header_errors={header_errors} "
        "next={next_todo}".format(
            status=summary["status"],
            validation_used=summary["validation_used"],
            test_used=summary["test_used"],
            rows=counts["rows"],
            support=counts["family_counts"].get("support_contact", 0),
            vertical=counts["family_counts"].get("relative_vertical", 0),
            fill_errors=len(fill_errors),
            header_errors=len(header_errors),
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
