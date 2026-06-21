#!/usr/bin/env python3
"""Fill independent support/vertical label collection sheet from visible evidence only."""

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

DEFAULT_COLLECTION_DIR = RGA_ROOT / "independent_support_vertical_v2_target_path_decision_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_v2_independent_label_fill_codex_independent_ver"

REVIEWER_ID = "(codex_independent_support_vertical_visible_only)"
REVIEW_ROUND = "1"
LABEL_SOURCE = "codex_independent_support_vertical_visible_only_bootstrap"

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
WALL_ATTACHED_CANDIDATES = {
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-dir", type=Path, default=DEFAULT_COLLECTION_DIR)
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


def pair_evaluability(row: dict[str, str], endpoint_identity: str, geometry_validity: str) -> str:
    if endpoint_identity == "uncertain":
        return "uncertain"
    if geometry_validity == "not_evaluable":
        return "not_evaluable"
    if str(row.get("evidence_packet_status") or "") == "ready_with_packet_caveat":
        return "partially_evaluable"
    return "evaluable"


def endpoint_identity(row: dict[str, str]) -> str:
    subject = lower(row, "subject_label")
    obj = lower(row, "object_label")
    if is_generic(subject) or is_generic(obj):
        return "uncertain"
    return "both_valid"


def support_geometry(row: dict[str, str]) -> tuple[str, str, str]:
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
        return "not_evaluable", "endpoint_identity_issue", "generic endpoint label prevents support/contact judgment"
    if subject in {"floor", "ceiling"} and pred in {"lying on", "standing on", "supported by"}:
        return "contradicts_predicate", "geometry_contradiction", "room surface as supported subject contradicts support/contact"
    if subject == "wall" and pred in {"lying on", "standing on"}:
        return "contradicts_predicate", "geometry_contradiction", "wall cannot naturally lie or stand on another object"
    if obj == "wall" and subject in WALL_ATTACHED_CANDIDATES and norm_xy <= 0.65:
        return "supports_predicate", "better_alternative_predicate", "wall contact is plausible but attached-to may be a better predicate"
    if obj in ROOM_SURFACE_LABELS:
        if overlap >= 0.10 or norm_xy <= 0.80 or (obj == "floor" and gap <= 1.25):
            return "supports_predicate", "dense_or_trivial_relation", "room-surface support is plausible but weakly informative"
        return "ambiguous", "visibility_or_evidence_gap", "room-surface support evidence is weak or spatially unclear"
    if gap <= 0.45 and overlap >= 0.20 and obj in SUPPORT_SURFACES:
        return "supports_predicate", "physically_supported_informative", "small support gap, enough xy overlap, plausible support surface"
    if gap <= 1.00 and overlap >= 0.10 and obj in SUPPORT_SURFACES:
        return "supports_predicate", "annotation_sparsity_candidate", "support is plausible but evidence is moderate"
    if gap > 1.75 and overlap < 0.10:
        return "contradicts_predicate", "geometry_contradiction", "large support gap with little projected overlap"
    return "ambiguous", "visibility_or_evidence_gap", "support/contact evidence is not decisive"


def vertical_geometry(row: dict[str, str]) -> tuple[str, str, str]:
    subject = lower(row, "subject_label")
    obj = lower(row, "object_label")
    signed_margin = safe_float(row, "witness_relative_vertical_signed_margin")
    sign_agree = safe_float(row, "witness_relative_vertical_sign_agreement")
    abs_margin = abs(signed_margin)

    if is_generic(subject) or is_generic(obj):
        return "not_evaluable", "endpoint_identity_issue", "generic endpoint label prevents vertical-order judgment"
    if sign_agree < 0.5 and abs_margin >= 0.20:
        return "contradicts_predicate", "geometry_contradiction", "vertical witness direction contradicts predicate"
    if abs_margin < 0.15:
        return "ambiguous", "visibility_or_evidence_gap", "vertical margin is too small"
    if subject in ROOM_SURFACE_LABELS or obj in ROOM_SURFACE_LABELS:
        if sign_agree >= 0.5:
            return "supports_predicate", "dense_or_trivial_relation", "vertical relation involving room structure is weakly informative"
        return "ambiguous", "visibility_or_evidence_gap", "room-structure vertical relation is unclear"
    if (subject, obj) in INFORMATIVE_VERTICAL_PAIRS and sign_agree >= 0.5:
        return "supports_predicate", "physically_supported_informative", "category pair and vertical witness support an informative relation"
    if sign_agree >= 0.5 and abs_margin >= 0.25:
        return "supports_predicate", "annotation_sparsity_candidate", "vertical witness supports predicate but informativeness needs audit"
    return "ambiguous", "visibility_or_evidence_gap", "vertical relation remains ambiguous"


def geometry_decision(row: dict[str, str]) -> tuple[str, str, str]:
    family = lower(row, "predicate_family")
    if family == "support_contact":
        return support_geometry(row)
    if family == "relative_vertical":
        return vertical_geometry(row)
    return "not_evaluable", "other", "predicate family is outside selected support/vertical scope"


def reliability_decision(endpoint: str, geometry: str, primary_reason: str) -> tuple[str, str]:
    if endpoint != "both_valid":
        return "uncertain", "endpoint_identity"
    if geometry == "contradicts_predicate":
        return "unreliable", "none"
    if geometry in {"ambiguous", "not_evaluable"}:
        if primary_reason == "endpoint_identity_issue":
            return "uncertain", "endpoint_identity"
        return "uncertain", "weak_geometry"
    if primary_reason == "physically_supported_informative":
        return "reliable", "none"
    if primary_reason == "annotation_sparsity_candidate":
        return "reliable", "none"
    if primary_reason == "dense_or_trivial_relation":
        return "unreliable", "dense_relation"
    if primary_reason == "better_alternative_predicate":
        return "unreliable", "ontology_ambiguity"
    if primary_reason == "ontology_mismatch":
        return "unreliable", "ontology_ambiguity"
    return "uncertain", "other"


def fill_row(row: dict[str, str]) -> dict[str, str]:
    endpoint = endpoint_identity(row)
    geometry, primary_reason, reason_note = geometry_decision(row)
    reliability, uncertainty = reliability_decision(endpoint, geometry, primary_reason)
    if reliability == "unreliable" and uncertainty == "none":
        uncertainty = "none"
    evaluability = pair_evaluability(row, endpoint, geometry)
    output = dict(row)
    output.update(
        {
            "reviewer_id": REVIEWER_ID,
            "review_round": REVIEW_ROUND,
            "endpoint_identity_independent": endpoint,
            "pair_evaluability_independent": evaluability,
            "geometry_validity_independent": geometry,
            "relation_reliability_independent": reliability,
            "primary_reason_independent": primary_reason,
            "uncertainty_reason_independent": uncertainty,
            "label_notes_independent": f"codex_independent visible-only bootstrap; {reason_note}",
        }
    )
    return output


def validate_rows(rows: list[dict[str, str]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    allowed = schema["allowed_review_values"]
    for row_number, row in enumerate(rows, start=2):
        blind_id = row.get("blind_review_id", "")
        for field in schema["required_completion_fields"]:
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


def independent_records(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in rows:
        records.append(
            {
                "schema_version": "h002_support_vertical_independent_label_fill_record_v1",
                "label_source": LABEL_SOURCE,
                "reviewer_id": row["reviewer_id"],
                "review_round": row["review_round"],
                "not_human_confirmed": True,
                "paper_evidence_allowed": False,
                "posterior_claim_allowed": False,
                "hidden_manifest_read": False,
                "v2_codex_axes_read": False,
                "semantic_score_or_rank_used": False,
                "p_geom_valid_used": False,
                "geometry_status_used": False,
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
                "endpoint_identity_independent": row["endpoint_identity_independent"],
                "pair_evaluability_independent": row["pair_evaluability_independent"],
                "geometry_validity_independent": row["geometry_validity_independent"],
                "relation_reliability_independent": row["relation_reliability_independent"],
                "primary_reason_independent": row["primary_reason_independent"],
                "uncertainty_reason_independent": row["uncertainty_reason_independent"],
                "label_notes_independent": row["label_notes_independent"],
            }
        )
    return records


def nested_counts(rows: list[dict[str, str]], group_key: str, value_key: str) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[row[group_key]][row[value_key]] += 1
    return {key: dict(sorted(value.items())) for key, value in sorted(grouped.items())}


def summarize(rows: list[dict[str, str]]) -> dict[str, Any]:
    axes = [
        "endpoint_identity_independent",
        "pair_evaluability_independent",
        "geometry_validity_independent",
        "relation_reliability_independent",
        "primary_reason_independent",
        "uncertainty_reason_independent",
    ]
    return {
        "rows": len(rows),
        "family_counts": dict(sorted(Counter(row["predicate_family"] for row in rows).items())),
        "predicate_counts": dict(sorted(Counter(row["predicate_label"] for row in rows).items())),
        "packet_status_counts": dict(sorted(Counter(row["evidence_packet_status"] for row in rows).items())),
        "axis_counts": {axis: dict(sorted(Counter(row[axis] for row in rows).items())) for axis in axes},
        "geometry_by_family": nested_counts(rows, "predicate_family", "geometry_validity_independent"),
        "reliability_by_family": nested_counts(rows, "predicate_family", "relation_reliability_independent"),
        "reason_by_family": nested_counts(rows, "predicate_family", "primary_reason_independent"),
    }


def split_rows(rows: list[dict[str, str]], family: str) -> list[dict[str, str]]:
    return [row for row in rows if row["predicate_family"] == family]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Support/Vertical Independent Label Fill",
        "",
        "## Boundary",
        "",
        "- Open3DSG train-only hypothesis-stage fill.",
        "- This is Codex independent visible-only bootstrap, not human-confirmed review.",
        "- Hidden manifest, v2 Codex axes, prior labels, score/rank, p_geom_valid, and geometry_status are not read.",
        "- No posterior is trained.",
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
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    collection_dir = as_abs(args.collection_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    schema = read_json(collection_dir / "independent_collection_schema.json")
    source_sheet = collection_dir / "independent_collection_sheet.tsv"
    fieldnames, rows = read_tsv(source_sheet)
    filled_rows = [fill_row(row) for row in rows]
    errors = validate_rows(filled_rows, schema)
    records = independent_records(filled_rows)
    counts = summarize(filled_rows)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "completed_sheet": output_dir / "completed_independent_collection_sheet_codex_independent_ver.tsv",
        "completed_support_contact_sheet": output_dir / "completed_support_contact_independent_sheet_codex_independent_ver.tsv",
        "completed_relative_vertical_sheet": output_dir / "completed_relative_vertical_independent_sheet_codex_independent_ver.tsv",
        "independent_labels": output_dir / "independent_labels.jsonl",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
    }
    status = (
        "full_train_independent_support_vertical_v2_independent_labels_filled_codex_independent_ver"
        if not errors
        else "full_train_independent_support_vertical_v2_independent_label_fill_has_errors"
    )
    next_todo = (
        "full_train_independent_support_vertical_v2_independent_label_ingestion"
        if not errors
        else "fix_full_train_independent_support_vertical_v2_independent_label_fill_errors"
    )
    summary = {
        "schema_version": "h002_support_vertical_v2_independent_label_fill_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "collection_schema": rel_path(collection_dir / "independent_collection_schema.json"),
            "source_sheet": rel_path(source_sheet),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "label_source": LABEL_SOURCE,
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "hidden_manifest_read": False,
            "v2_codex_axes_read": False,
            "prior_label_or_label_use_read": False,
            "semantic_score_or_rank_used": False,
            "p_geom_valid_used": False,
            "geometry_status_used": False,
            "multi_view_as_model_input": False,
        },
        "counts": counts,
        "fill_validation_error_count": len(errors),
        "decision": (
            "Filled the independent collection sheet with a Codex independent visible-only bootstrap. "
            "This is stronger than reusing v2 Codex axes because the fill reads only the labeler-visible "
            "collection sheet, but it is still not human-confirmed paper evidence."
        ),
        "next_todo": next_todo,
    }

    write_tsv(output_paths["completed_sheet"], fieldnames, filled_rows)
    write_tsv(output_paths["completed_support_contact_sheet"], fieldnames, split_rows(filled_rows, "support_contact"))
    write_tsv(output_paths["completed_relative_vertical_sheet"], fieldnames, split_rows(filled_rows, "relative_vertical"))
    write_jsonl(output_paths["independent_labels"], records)
    write_jsonl(output_paths["fill_validation_errors"], errors)
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    counts = summary["counts"]
    reliability = counts["axis_counts"]["relation_reliability_independent"]
    geometry = counts["axis_counts"]["geometry_validity_independent"]
    print(
        f"status={summary['status']} rows={counts['rows']} "
        f"support={counts['family_counts'].get('support_contact', 0)} "
        f"vertical={counts['family_counts'].get('relative_vertical', 0)} "
        f"reliable={reliability.get('reliable', 0)} unreliable={reliability.get('unreliable', 0)} "
        f"uncertain={reliability.get('uncertain', 0)} "
        f"geom_support={geometry.get('supports_predicate', 0)} geom_contra={geometry.get('contradicts_predicate', 0)} "
        f"errors={summary['fill_validation_error_count']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"test_used={summary['boundary']['test_usage']} next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
