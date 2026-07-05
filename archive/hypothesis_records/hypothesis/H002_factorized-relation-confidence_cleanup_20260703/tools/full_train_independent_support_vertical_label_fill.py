#!/usr/bin/env python3
"""Fill selected support/vertical audit sheet with visible-surface Codex labels."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_READINESS_DIR = RGA_ROOT / "independent_support_vertical_label_readiness_codex_ver"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_support_vertical_label_fill_codex_ver"

REVIEWER_ID = "(codex_ver_support_vertical_visible_witness)"
REVIEW_ROUND = "1"
LABEL_SOURCE = "codex_ver_support_vertical_visible_witness_bootstrap"

GENERIC_LABELS = {
    "object",
    "objects",
    "item",
    "items",
    "clutter",
    "garbage",
    "unknown",
}
STRUCTURAL_LABELS = {
    "floor",
    "wall",
    "ceiling",
    "doorframe",
}
ROOM_SURFACE_LABELS = {
    "floor",
    "wall",
    "ceiling",
}
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-dir", type=Path, default=DEFAULT_READINESS_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = smoke.as_abs(path)
    try:
        return str(path.relative_to(smoke.REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with smoke.as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), [dict(row) for row in reader]


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


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
    return label in GENERIC_LABELS or not label


def is_caveat(row: dict[str, str]) -> bool:
    return str(row.get("evidence_packet_status") or "") == "ready_with_packet_caveat"


def degrade_confidence(confidence: str, row: dict[str, str]) -> str:
    if not is_caveat(row):
        return confidence
    if confidence == "high":
        return "medium"
    return "low"


def visibility_defaults(row: dict[str, str], label: str) -> dict[str, str]:
    subject = lower(row, "subject_label")
    obj = lower(row, "object_label")
    if label == "invalid_pair":
        return {
            "subject_identity_valid": "uncertain" if is_generic(subject) else "yes",
            "object_identity_valid": "uncertain" if is_generic(obj) else "yes",
            "object_pair_visible": "uncertain",
        }
    if is_caveat(row):
        return {
            "subject_identity_valid": "uncertain",
            "object_identity_valid": "uncertain",
            "object_pair_visible": "partial",
        }
    return {
        "subject_identity_valid": "yes",
        "object_identity_valid": "yes",
        "object_pair_visible": "yes",
    }


def relation_visible_for_label(label: str) -> str:
    if label in {"reliable_informative", "annotation_sparsity_candidate", "valid_but_trivial_dense"}:
        return "yes"
    if label in {"invalid_relation", "invalid_pair", "visibility_or_geometry_artifact"}:
        return "no"
    return "uncertain"


def finalize(row: dict[str, str], spec: dict[str, str]) -> dict[str, str]:
    label = spec["independent_relation_label"]
    visibility = visibility_defaults(row, label)
    confidence = degrade_confidence(spec["confidence"], row)
    note = (
        "codex_ver support/vertical visible-witness bootstrap; no post-lock reference "
        f"or construction metadata used; reason={spec['reason']}"
    )
    if is_caveat(row):
        note += "; packet_caveat=ready_with_packet_caveat"
    return {
        **visibility,
        "relation_visible_or_inferable": spec.get("relation_visible_or_inferable", relation_visible_for_label(label)),
        "visual_3d_support": spec["visual_3d_support"],
        "relation_informativeness": spec["relation_informativeness"],
        "independent_relation_label": label,
        "confidence": confidence,
        "evidence_notes": note,
    }


def support_contact_label(row: dict[str, str]) -> dict[str, str]:
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
            "independent_relation_label": "invalid_pair",
            "visual_3d_support": "not_evaluable",
            "relation_informativeness": "not_evaluable",
            "confidence": "medium",
            "reason": "generic endpoint label prevents reliable support/contact judgment",
        }

    if subject == obj:
        return {
            "independent_relation_label": "ontology_mismatch",
            "visual_3d_support": "uncertain",
            "relation_informativeness": "uncertain",
            "confidence": "low",
            "reason": "same-class support/contact requires instance-level visual confirmation",
        }

    if subject in {"floor", "ceiling"} and pred in {"lying on", "standing on", "supported by"}:
        return {
            "independent_relation_label": "invalid_relation",
            "visual_3d_support": "contradicts",
            "relation_informativeness": "not_evaluable",
            "confidence": "high",
            "reason": "room surface as supported subject is physically implausible for this predicate",
        }

    if subject == "wall" and pred in {"lying on", "standing on"}:
        return {
            "independent_relation_label": "invalid_relation",
            "visual_3d_support": "contradicts",
            "relation_informativeness": "not_evaluable",
            "confidence": "medium",
            "reason": "wall cannot naturally lie or stand on another object",
        }

    if obj in ROOM_SURFACE_LABELS:
        if subject in WALL_MOUNTED_CANDIDATES and obj == "wall" and norm_xy <= 0.65:
            return {
                "independent_relation_label": "annotation_sparsity_candidate",
                "visual_3d_support": "supports",
                "relation_informativeness": "informative",
                "confidence": "medium",
                "reason": "wall-mounted/contact relation is plausible and often sparsely annotated",
            }
        if obj == "floor" and pred in {"standing on", "lying on"} and overlap >= 0.20 and gap <= 1.25:
            return {
                "independent_relation_label": "valid_but_trivial_dense",
                "visual_3d_support": "supports",
                "relation_informativeness": "trivial_dense",
                "confidence": "medium",
                "reason": "floor support is geometrically plausible but dense/trivial",
            }
        return {
            "independent_relation_label": "valid_but_trivial_dense",
            "visual_3d_support": "supports" if overlap >= 0.10 or norm_xy <= 0.80 else "uncertain",
            "relation_informativeness": "trivial_dense",
            "confidence": "medium" if overlap >= 0.10 or norm_xy <= 0.80 else "low",
            "reason": "support/contact with room surface is not an informative relation edge",
        }

    if gap <= 0.40 and overlap >= 0.20 and obj in SUPPORT_SURFACES:
        return {
            "independent_relation_label": "reliable_informative",
            "visual_3d_support": "supports",
            "relation_informativeness": "informative",
            "confidence": "high",
            "reason": "small support gap, sufficient XY overlap, and plausible support surface",
        }

    if gap <= 1.00 and overlap >= 0.10 and obj in SUPPORT_SURFACES:
        return {
            "independent_relation_label": "annotation_sparsity_candidate",
            "visual_3d_support": "supports",
            "relation_informativeness": "informative",
            "confidence": "medium",
            "reason": "support relation is plausible but witness is weaker or sparsely annotated",
        }

    if gap > 1.75 and overlap < 0.10:
        return {
            "independent_relation_label": "invalid_relation",
            "visual_3d_support": "contradicts",
            "relation_informativeness": "not_evaluable",
            "confidence": "medium",
            "reason": "large support/contact gap with little projected overlap",
        }

    return {
        "independent_relation_label": "abstain_uncertain",
        "visual_3d_support": "uncertain",
        "relation_informativeness": "uncertain",
        "confidence": "low",
        "reason": "support/contact evidence is not decisive from visible witness fields",
    }


def relative_vertical_label(row: dict[str, str]) -> dict[str, str]:
    subject = lower(row, "subject_label")
    obj = lower(row, "object_label")
    pred = lower(row, "predicate_label")
    signed_margin = safe_float(row, "witness_relative_vertical_signed_margin")
    sign_agree = safe_float(row, "witness_relative_vertical_sign_agreement")
    abs_margin = abs(signed_margin)

    if is_generic(subject) or is_generic(obj):
        return {
            "independent_relation_label": "invalid_pair",
            "visual_3d_support": "not_evaluable",
            "relation_informativeness": "not_evaluable",
            "confidence": "medium",
            "reason": "generic endpoint label prevents reliable vertical-order judgment",
        }

    if subject == obj:
        return {
            "independent_relation_label": "ontology_mismatch",
            "visual_3d_support": "uncertain",
            "relation_informativeness": "uncertain",
            "confidence": "low",
            "reason": "same-class vertical relation requires instance-level visual confirmation",
        }

    if sign_agree < 0.5 and abs_margin >= 0.20:
        return {
            "independent_relation_label": "invalid_relation",
            "visual_3d_support": "contradicts",
            "relation_informativeness": "not_evaluable",
            "confidence": "high" if abs_margin >= 0.50 else "medium",
            "reason": "visible vertical witness direction contradicts predicate direction",
        }

    if abs_margin < 0.15:
        return {
            "independent_relation_label": "abstain_uncertain",
            "visual_3d_support": "uncertain",
            "relation_informativeness": "uncertain",
            "confidence": "low",
            "reason": "vertical margin is too small for a confident independent label",
        }

    if subject in ROOM_SURFACE_LABELS or obj in ROOM_SURFACE_LABELS:
        if pred == "higher than" and obj == "floor" and sign_agree >= 0.5:
            return {
                "independent_relation_label": "valid_but_trivial_dense",
                "visual_3d_support": "supports",
                "relation_informativeness": "trivial_dense",
                "confidence": "medium",
                "reason": "higher-than-floor relation is geometrically true but dense/trivial",
            }
        if pred == "lower than" and subject == "floor" and sign_agree >= 0.5:
            return {
                "independent_relation_label": "valid_but_trivial_dense",
                "visual_3d_support": "supports",
                "relation_informativeness": "trivial_dense",
                "confidence": "medium",
                "reason": "floor lower-than relation is geometrically true but dense/trivial",
            }
        return {
            "independent_relation_label": "valid_but_trivial_dense",
            "visual_3d_support": "supports" if sign_agree >= 0.5 else "uncertain",
            "relation_informativeness": "trivial_dense",
            "confidence": "medium" if sign_agree >= 0.5 else "low",
            "reason": "vertical relation involving room structure is usually not informative",
        }

    if (subject, obj) in INFORMATIVE_VERTICAL_PAIRS and sign_agree >= 0.5:
        return {
            "independent_relation_label": "reliable_informative",
            "visual_3d_support": "supports",
            "relation_informativeness": "informative",
            "confidence": "high" if abs_margin >= 0.50 else "medium",
            "reason": "category pair and vertical witness support an informative relation",
        }

    if sign_agree >= 0.5 and abs_margin >= 0.25:
        return {
            "independent_relation_label": "annotation_sparsity_candidate",
            "visual_3d_support": "supports",
            "relation_informativeness": "informative",
            "confidence": "medium",
            "reason": "vertical witness supports predicate but informativeness needs audit confirmation",
        }

    return {
        "independent_relation_label": "abstain_uncertain",
        "visual_3d_support": "uncertain",
        "relation_informativeness": "uncertain",
        "confidence": "low",
        "reason": "vertical relation is ambiguous under visible witness fields",
    }


def assign_label(row: dict[str, str]) -> dict[str, str]:
    family = lower(row, "predicate_family")
    if family == "support_contact":
        return finalize(row, support_contact_label(row))
    if family == "relative_vertical":
        return finalize(row, relative_vertical_label(row))
    return finalize(
        row,
        {
            "independent_relation_label": "abstain_uncertain",
            "visual_3d_support": "not_evaluable",
            "relation_informativeness": "not_evaluable",
            "confidence": "low",
            "reason": "predicate family is outside selected support/vertical scope",
        },
    )


def binary_value(label: str, policy: dict[str, list[str]]) -> int | None:
    if label in policy["positive"]:
        return 1
    if label in policy["negative"]:
        return 0
    return None


def fill_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    filled = []
    for row in rows:
        output = dict(row)
        output.update(
            {
                "reviewer_id": REVIEWER_ID,
                "review_round": REVIEW_ROUND,
                **assign_label(row),
            }
        )
        filled.append(output)
    return filled


def validate_filled_rows(rows: list[dict[str, str]], schema: dict[str, Any]) -> list[dict[str, Any]]:
    errors = []
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


def label_records(rows: list[dict[str, str]], binary_policy: dict[str, list[str]]) -> list[dict[str, Any]]:
    records = []
    for row in rows:
        y = binary_value(row["independent_relation_label"], binary_policy)
        records.append(
            {
                "schema_version": "h002_support_vertical_codex_label_v1",
                "label_source": LABEL_SOURCE,
                "not_human_confirmed": True,
                "paper_evidence_allowed": False,
                "posterior_claim_allowed": False,
                "hidden_reference_used": False,
                "validation_used": False,
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
                "subject_identity_valid": row["subject_identity_valid"],
                "object_identity_valid": row["object_identity_valid"],
                "object_pair_visible": row["object_pair_visible"],
                "relation_visible_or_inferable": row["relation_visible_or_inferable"],
                "visual_3d_support": row["visual_3d_support"],
                "relation_informativeness": row["relation_informativeness"],
                "independent_relation_label": row["independent_relation_label"],
                "binary_target": y,
                "binary_usable": y is not None,
                "confidence": row["confidence"],
                "evidence_packet_status": row["evidence_packet_status"],
                "evidence_notes": row["evidence_notes"],
            }
        )
    return records


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(row["independent_relation_label"] for row in records)
    binary_counts = Counter(str(row["binary_target"]) for row in records if row["binary_usable"])
    confidence_counts = Counter(row["confidence"] for row in records)
    family_counts: dict[str, Counter[str]] = defaultdict(Counter)
    predicate_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in records:
        family_counts[row["predicate_family"]][row["independent_relation_label"]] += 1
        predicate_counts[row["predicate_label"]][row["independent_relation_label"]] += 1
    return {
        "rows": len(records),
        "label_counts": dict(sorted(label_counts.items())),
        "binary_usable_rows": sum(1 for row in records if row["binary_usable"]),
        "positive_rows": binary_counts.get("1", 0),
        "negative_rows": binary_counts.get("0", 0),
        "excluded_rows": len(records) - sum(1 for row in records if row["binary_usable"]),
        "binary_counts": dict(sorted(binary_counts.items())),
        "confidence_counts": dict(sorted(confidence_counts.items())),
        "labels_by_family": {key: dict(sorted(value.items())) for key, value in sorted(family_counts.items())},
        "labels_by_predicate": {key: dict(sorted(value.items())) for key, value in sorted(predicate_counts.items())},
    }


def split_rows(rows: list[dict[str, str]], family: str) -> list[dict[str, str]]:
    return [row for row in rows if row["predicate_family"] == family]


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Full-Train Support/Vertical Label Fill",
        "",
        "## Boundary",
        "",
        "- Split: Open3DSG train-only.",
        "- Labels are Codex visible-witness bootstrap labels, not human-confirmed labels.",
        "- The fill script reads the readiness-passed support_vertical sheet and completion schema only.",
        "- Hidden internal reference, source score/rank, p_geom_valid, geometry_status, and target labels are not read.",
        "- Multi-view/mesh packet paths remain audit evidence only, not posterior input.",
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
        f"| binary usable rows | {counts['binary_usable_rows']} |",
        f"| positive rows | {counts['positive_rows']} |",
        f"| negative rows | {counts['negative_rows']} |",
        f"| excluded rows | {counts['excluded_rows']} |",
        f"| fill validation errors | {summary['fill_validation_error_count']} |",
        "",
        "## Label Counts",
        "",
        "| Label | Rows |",
        "| --- | ---: |",
    ]
    for label, count in counts["label_counts"].items():
        lines.append(f"| `{label}` | {count} |")
    lines.extend(
        [
            "",
            "## Family Breakdown",
            "",
            "| Family | Labels |",
            "| --- | --- |",
        ]
    )
    for family, label_counts in counts["labels_by_family"].items():
        text = ", ".join(f"{label}:{count}" for label, count in label_counts.items())
        lines.append(f"| `{family}` | {text} |")
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
            summary["output_paths"]["labels"],
            summary["output_paths"]["binary_targets_preview"],
            summary["output_paths"]["fill_validation_errors"],
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
    readiness_dir = smoke.as_abs(args.readiness_dir)
    output_dir = smoke.as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    readiness = read_json(readiness_dir / "summary.json")
    if readiness.get("status") != "full_train_independent_support_vertical_label_readiness_ready_for_label_fill":
        raise RuntimeError(f"support/vertical label readiness is not ready: {readiness.get('status')}")
    schema = read_json(readiness_dir / "completion_schema.json")
    source_sheet = readiness_dir / "support_vertical_label_fill_sheet.tsv"
    fieldnames, rows = read_tsv(source_sheet)
    filled_rows = fill_rows(rows)
    errors = validate_filled_rows(filled_rows, schema)
    binary_policy = schema["label_to_binary_policy"]
    records = label_records(filled_rows, binary_policy)
    counts = summarize(records)

    output_paths = {
        "summary_json": output_dir / "summary.json",
        "report_md": output_dir / "report.md",
        "completed_sheet": output_dir / "completed_support_vertical_label_fill_sheet_codex_ver.tsv",
        "completed_support_contact_sheet": output_dir / "completed_support_contact_label_fill_sheet_codex_ver.tsv",
        "completed_relative_vertical_sheet": output_dir / "completed_relative_vertical_label_fill_sheet_codex_ver.tsv",
        "labels": output_dir / "labels.jsonl",
        "binary_targets_preview": output_dir / "binary_targets_preview.jsonl",
        "fill_validation_errors": output_dir / "fill_validation_errors.jsonl",
    }
    status = (
        "full_train_independent_support_vertical_labels_filled_codex_ver"
        if not errors
        else "full_train_independent_support_vertical_label_fill_has_errors"
    )
    next_todo = (
        "full_train_independent_support_vertical_label_ingestion"
        if not errors
        else "fix_full_train_independent_support_vertical_label_fill_errors"
    )
    summary = {
        "schema_version": "h002_full_train_independent_support_vertical_label_fill_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation_used": False,
        "input": {
            "readiness_summary": rel_path(readiness_dir / "summary.json"),
            "completion_schema": rel_path(readiness_dir / "completion_schema.json"),
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
            "hidden_internal_reference_read": False,
            "hidden_target_metadata_used": False,
            "source_score_or_rank_used": False,
            "p_geom_valid_used": False,
            "geometry_status_used": False,
            "multi_view_as_model_input": False,
            "trains_new_posterior": False,
        },
        "counts": counts,
        "fill_validation_error_count": len(errors),
        "decision": (
            "Codex-version support/vertical labels are filled from visible relation fields and raw witness values only. "
            "Treat them as bootstrap labels until independent/human confirmation and post-label ingestion."
        ),
        "next_todo": next_todo,
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
    }

    write_tsv(output_paths["completed_sheet"], fieldnames, filled_rows)
    write_tsv(output_paths["completed_support_contact_sheet"], fieldnames, split_rows(filled_rows, "support_contact"))
    write_tsv(output_paths["completed_relative_vertical_sheet"], fieldnames, split_rows(filled_rows, "relative_vertical"))
    write_jsonl(output_paths["labels"], records)
    write_jsonl(output_paths["binary_targets_preview"], [row for row in records if row["binary_usable"]])
    write_jsonl(output_paths["fill_validation_errors"], errors)
    write_json(output_paths["summary_json"], summary)
    write_report(output_paths["report_md"], summary)

    print(
        "status={status} validation_used={validation_used} rows={rows} binary={binary} "
        "positive={positive} negative={negative} excluded={excluded} errors={errors} next={next_todo}".format(
            status=summary["status"],
            validation_used=summary["validation_used"],
            rows=counts["rows"],
            binary=counts["binary_usable_rows"],
            positive=counts["positive_rows"],
            negative=counts["negative_rows"],
            excluded=counts["excluded_rows"],
            errors=len(errors),
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
