#!/usr/bin/env python3
"""Fill H002 full-train independent sheets with Codex bootstrap labels."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_READINESS_DIR = RGA_ROOT / "independent_label_readiness"
DEFAULT_GAP_DIR = RGA_ROOT / "asset_packet_gap_audit"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_label_fill_codex_ver"

REVIEWER_ID = "(codex_ver_full_train_independent)"
REVIEW_ROUND = "1"

SHEET_FILES = {
    "all": "label_ready_all_sheet_with_packets.tsv",
    "priority": "label_ready_priority_sheet_with_packets.tsv",
    "support_contact": "label_ready_support_contact_sheet_with_packets.tsv",
    "relative_vertical": "label_ready_relative_vertical_sheet_with_packets.tsv",
    "proximity": "label_ready_proximity_sheet_with_packets.tsv",
}

LABEL_TO_BINARY = {
    "reliable_informative": 1,
    "annotation_sparsity_candidate": 1,
    "valid_but_trivial_dense": 0,
    "invalid_relation": 0,
    "invalid_pair": 0,
    "visibility_or_geometry_artifact": 0,
    "ontology_mismatch": None,
    "abstain_uncertain": None,
}

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

FUNCTIONAL_PROXIMITY_PAIRS = {
    ("chair", "desk"),
    ("chair", "table"),
    ("table", "chair"),
    ("cushion", "armchair"),
    ("clothes", "armchair"),
    ("pillow", "bed"),
    ("blanket", "bed"),
    ("bath cabinet", "wall"),
    ("sink", "bath cabinet"),
    ("scale", "bath cabinet"),
    ("towel", "door"),
    ("towel", "wall"),
    ("toilet paper", "toilet brush"),
    ("toilet paper dispenser", "toilet"),
    ("toilet brush", "toilet"),
    ("trash can", "commode"),
    ("shower curtain", "bathtub"),
    ("plant", "window"),
}

INFORMATIVE_VERTICAL_PAIRS = {
    ("sink", "bath cabinet"),
    ("scale", "bath cabinet"),
    ("cushion", "armchair"),
    ("pillow", "bed"),
    ("blanket", "bed"),
    ("toilet paper", "toilet brush"),
    ("suitcase", "wardrobe"),
    ("window", "bench"),
    ("window", "desk"),
    ("shelf", "armchair"),
    ("book", "box"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-dir", type=Path, default=DEFAULT_READINESS_DIR)
    parser.add_argument("--gap-dir", type=Path, default=DEFAULT_GAP_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = list(reader.fieldnames or [])
        return fieldnames, [dict(row) for row in reader]


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def lower(row: dict[str, str], key: str) -> str:
    return str(row.get(key) or "").strip().lower()


def is_generic(label: str) -> bool:
    return label in GENERIC_LABELS


def is_caveat(row: dict[str, str]) -> bool:
    return str(row.get("packet_gap_decision") or "") == "label_ready_with_packet_caveat"


def degrade_confidence(confidence: str, row: dict[str, str]) -> str:
    if not is_caveat(row):
        return confidence
    if confidence == "high":
        return "medium"
    return "low"


def base_visibility(row: dict[str, str]) -> dict[str, str]:
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


def finalize(row: dict[str, str], spec: dict[str, str]) -> dict[str, str]:
    visibility = base_visibility(row)
    label = spec["independent_relation_label"]
    if label == "invalid_pair":
        visibility["subject_identity_valid"] = "uncertain" if is_generic(lower(row, "subject_label")) else "yes"
        visibility["object_identity_valid"] = "uncertain" if is_generic(lower(row, "object_label")) else "yes"
        visibility["object_pair_visible"] = "uncertain"
    if label in {"abstain_uncertain", "ontology_mismatch"} and is_caveat(row):
        visibility["object_pair_visible"] = "partial"

    relation_visible = spec.get("relation_visible_or_inferable")
    if relation_visible is None:
        if label in {"reliable_informative", "annotation_sparsity_candidate", "valid_but_trivial_dense"}:
            relation_visible = "yes"
        elif label in {"invalid_relation", "invalid_pair", "visibility_or_geometry_artifact"}:
            relation_visible = "no"
        else:
            relation_visible = "uncertain"

    confidence = degrade_confidence(spec["confidence"], row)
    caveat_note = ""
    if is_caveat(row):
        caveat_note = " packet_gap_caveat=yes; identity must be rechecked from available packet evidence."

    return {
        **visibility,
        "relation_visible_or_inferable": relation_visible,
        "visual_3d_support": spec["visual_3d_support"],
        "relation_informativeness": spec["relation_informativeness"],
        "independent_relation_label": label,
        "confidence": confidence,
        "evidence_notes": (
            "codex_ver_full_train_independent bootstrap label; visible sheet fields "
            "and packet availability only; no internal_key or hidden target metadata "
            f"used; reason={spec['reason']}.{caveat_note}"
        ),
    }


def support_contact_label(row: dict[str, str]) -> dict[str, str]:
    subject = lower(row, "subject_label")
    obj = lower(row, "object_label")
    pred = lower(row, "predicate_label")

    if is_generic(subject) or is_generic(obj):
        return {
            "independent_relation_label": "invalid_pair",
            "visual_3d_support": "not_evaluable",
            "relation_informativeness": "not_evaluable",
            "confidence": "medium",
            "reason": "generic endpoint label makes relation identity unreliable",
        }

    if subject == "floor":
        return {
            "independent_relation_label": "invalid_relation",
            "visual_3d_support": "contradicts",
            "relation_informativeness": "not_evaluable",
            "confidence": "high",
            "reason": "floor as supported/standing/lying subject is physically implausible",
        }

    if subject == "ceiling" and pred in {"lying on", "standing on"}:
        return {
            "independent_relation_label": "invalid_relation",
            "visual_3d_support": "contradicts",
            "relation_informativeness": "not_evaluable",
            "confidence": "medium",
            "reason": "ceiling cannot plausibly lie or stand on another object",
        }

    if subject == obj:
        return {
            "independent_relation_label": "ontology_mismatch",
            "visual_3d_support": "uncertain",
            "relation_informativeness": "uncertain",
            "confidence": "low",
            "reason": "same-class support relation needs instance-level confirmation",
        }

    if subject in STRUCTURAL_LABELS and obj in STRUCTURAL_LABELS:
        return {
            "independent_relation_label": "valid_but_trivial_dense",
            "visual_3d_support": "supports",
            "relation_informativeness": "trivial_dense",
            "confidence": "medium",
            "reason": "structural support/contact is plausible but not informative",
        }

    if obj in SUPPORT_SURFACES:
        return {
            "independent_relation_label": "reliable_informative",
            "visual_3d_support": "supports",
            "relation_informativeness": "informative",
            "confidence": "high" if obj not in {"floor", "wall"} else "medium",
            "reason": "object category is a plausible support/contact surface",
        }

    if obj == "wall" and subject in {"mirror", "frame", "toilet paper", "towel", "shower curtain"}:
        return {
            "independent_relation_label": "annotation_sparsity_candidate",
            "visual_3d_support": "supports",
            "relation_informativeness": "informative",
            "confidence": "medium",
            "reason": "wall-mounted/contact relation is plausible but may be sparse in labels",
        }

    return {
        "independent_relation_label": "abstain_uncertain",
        "visual_3d_support": "uncertain",
        "relation_informativeness": "uncertain",
        "confidence": "low",
        "reason": "support/contact relation requires visual or mesh confirmation",
    }


def relative_vertical_label(row: dict[str, str]) -> dict[str, str]:
    subject = lower(row, "subject_label")
    obj = lower(row, "object_label")
    pred = lower(row, "predicate_label")

    if is_generic(subject) or is_generic(obj):
        return {
            "independent_relation_label": "invalid_pair",
            "visual_3d_support": "not_evaluable",
            "relation_informativeness": "not_evaluable",
            "confidence": "medium",
            "reason": "generic endpoint label makes vertical relation identity unreliable",
        }

    if subject == obj:
        return {
            "independent_relation_label": "abstain_uncertain",
            "visual_3d_support": "uncertain",
            "relation_informativeness": "uncertain",
            "confidence": "low",
            "reason": "same-class vertical order needs instance-level visual confirmation",
        }

    if pred == "higher than" and subject == "floor":
        return {
            "independent_relation_label": "invalid_relation",
            "visual_3d_support": "contradicts",
            "relation_informativeness": "not_evaluable",
            "confidence": "high",
            "reason": "floor is not expected to be higher than another object",
        }

    if pred == "lower than" and obj == "floor":
        return {
            "independent_relation_label": "invalid_relation",
            "visual_3d_support": "contradicts",
            "relation_informativeness": "not_evaluable",
            "confidence": "high",
            "reason": "object below floor is physically implausible in this relation family",
        }

    if (pred == "higher than" and obj == "floor") or (pred == "lower than" and obj == "ceiling"):
        return {
            "independent_relation_label": "valid_but_trivial_dense",
            "visual_3d_support": "supports",
            "relation_informativeness": "trivial_dense",
            "confidence": "medium",
            "reason": "relation is usually true but dominated by room-surface triviality",
        }

    if subject in STRUCTURAL_LABELS or obj in STRUCTURAL_LABELS:
        return {
            "independent_relation_label": "valid_but_trivial_dense",
            "visual_3d_support": "supports",
            "relation_informativeness": "trivial_dense",
            "confidence": "medium",
            "reason": "vertical relation involving room structure is likely generic",
        }

    if (subject, obj) in INFORMATIVE_VERTICAL_PAIRS:
        return {
            "independent_relation_label": "reliable_informative",
            "visual_3d_support": "supports",
            "relation_informativeness": "informative",
            "confidence": "medium",
            "reason": "category pair makes the vertical relation informative",
        }

    return {
        "independent_relation_label": "annotation_sparsity_candidate",
        "visual_3d_support": "supports",
        "relation_informativeness": "informative",
        "confidence": "low",
        "reason": "vertical relation is plausible but needs visual or mesh confirmation",
    }


def proximity_label(row: dict[str, str]) -> dict[str, str]:
    subject = lower(row, "subject_label")
    obj = lower(row, "object_label")

    if is_generic(subject) or is_generic(obj):
        return {
            "independent_relation_label": "invalid_pair",
            "visual_3d_support": "not_evaluable",
            "relation_informativeness": "not_evaluable",
            "confidence": "medium",
            "reason": "generic endpoint label makes proximity edge identity unreliable",
        }

    if subject == obj or subject in STRUCTURAL_LABELS or obj in STRUCTURAL_LABELS:
        return {
            "independent_relation_label": "valid_but_trivial_dense",
            "visual_3d_support": "supports",
            "relation_informativeness": "trivial_dense",
            "confidence": "medium",
            "reason": "proximity edge is likely dense or structurally trivial",
        }

    if (subject, obj) in FUNCTIONAL_PROXIMITY_PAIRS or (obj, subject) in FUNCTIONAL_PROXIMITY_PAIRS:
        return {
            "independent_relation_label": "reliable_informative",
            "visual_3d_support": "supports",
            "relation_informativeness": "informative",
            "confidence": "medium",
            "reason": "category pair makes proximity relation functionally meaningful",
        }

    return {
        "independent_relation_label": "valid_but_trivial_dense",
        "visual_3d_support": "supports",
        "relation_informativeness": "trivial_dense",
        "confidence": "low",
        "reason": "visible metadata does not show why this proximity edge is informative",
    }


def assign_label(row: dict[str, str]) -> dict[str, str]:
    family = lower(row, "predicate_family")
    if family == "support_contact":
        return finalize(row, support_contact_label(row))
    if family == "relative_vertical":
        return finalize(row, relative_vertical_label(row))
    if family == "proximity":
        return finalize(row, proximity_label(row))
    return finalize(
        row,
        {
            "independent_relation_label": "abstain_uncertain",
            "visual_3d_support": "not_evaluable",
            "relation_informativeness": "not_evaluable",
            "confidence": "low",
            "reason": "predicate family is not handled by full-train Codex bootstrap fill",
        },
    )


def binary_target(label: str) -> int | None:
    return LABEL_TO_BINARY[label]


def fill_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    filled = []
    for row in rows:
        updates = assign_label(row)
        out = dict(row)
        out.update(
            {
                "reviewer_id": REVIEWER_ID,
                "review_round": REVIEW_ROUND,
                **updates,
            }
        )
        filled.append(out)
    return filled


def label_records(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    records = []
    for row in rows:
        y = binary_target(row["independent_relation_label"])
        records.append(
            {
                "schema_version": "h002_full_train_independent_codex_label_v0",
                "label_source": "codex_ver_full_train_independent_visible_surface_bootstrap",
                "not_human_confirmed": True,
                "paper_evidence_allowed": False,
                "posterior_claim_allowed": False,
                "blind_review_id": row["blind_review_id"],
                "asset_request_id": row["asset_request_id"],
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
                "packet_gap_decision": row["packet_gap_decision"],
                "evidence_notes": row["evidence_notes"],
            }
        )
    return records


def summarize(rows: list[dict[str, str]], records: list[dict[str, Any]]) -> dict[str, Any]:
    label_counts = Counter(row["independent_relation_label"] for row in rows)
    target_counts = Counter(str(row["binary_target"]) for row in records if row["binary_usable"])
    by_family = defaultdict(Counter)
    by_predicate = defaultdict(Counter)
    confidence = Counter(row["confidence"] for row in rows)
    for record in records:
        label = record["independent_relation_label"]
        by_family[record["predicate_family"]][label] += 1
        by_predicate[record["predicate_label"]][label] += 1
    return {
        "rows": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "binary_usable_rows": sum(1 for row in records if row["binary_usable"]),
        "positive_rows": target_counts.get("1", 0),
        "negative_rows": target_counts.get("0", 0),
        "excluded_rows": label_counts.get("ontology_mismatch", 0) + label_counts.get("abstain_uncertain", 0),
        "target_counts": dict(sorted(target_counts.items())),
        "confidence_counts": dict(sorted(confidence.items())),
        "labels_by_family": {key: dict(sorted(value.items())) for key, value in sorted(by_family.items())},
        "labels_by_predicate": {key: dict(sorted(value.items())) for key, value in sorted(by_predicate.items())},
    }


def output_name(sheet_name: str) -> str:
    return sheet_name.replace("label_ready_", "completed_").replace("_with_packets.tsv", "_codex_ver.tsv")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Full Train Independent Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Labels are `(codex_ver_full_train_independent)` bootstrap labels.",
        "- The fill script reads label-ready sheets only.",
        "- `internal_key.jsonl` and hidden target-construction metadata are not read.",
        "- Validation/test rows are not used.",
        "- These labels are not human-confirmed and are not paper evidence.",
        "- Posterior claims remain blocked until post-label ingestion and controls.",
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
        label_text = ", ".join(f"{label}:{count}" for label, count in label_counts.items())
        lines.append(f"| `{family}` | {label_text} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            summary["next_todo"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    readiness_dir = as_abs(args.readiness_dir)
    gap_dir = as_abs(args.gap_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    readiness = read_json(readiness_dir / "summary.json")
    if readiness.get("status") != "full_train_independent_label_readiness_ready_for_label_fill":
        raise RuntimeError(f"label readiness is not ready: {readiness.get('status')}")

    completed_sheets = {}
    sheet_summaries = {}
    all_filled_rows: list[dict[str, str]] = []
    all_records: list[dict[str, Any]] = []
    fieldnames_by_sheet: dict[str, list[str]] = {}

    for name, filename in SHEET_FILES.items():
        fieldnames, rows = read_tsv(gap_dir / filename)
        filled_rows = fill_rows(rows)
        records = label_records(filled_rows)
        out_path = output_dir / output_name(filename)
        write_tsv(out_path, fieldnames, filled_rows)
        completed_sheets[name] = rel_path(out_path)
        sheet_summaries[name] = summarize(filled_rows, records)
        fieldnames_by_sheet[name] = fieldnames
        if name == "all":
            all_filled_rows = filled_rows
            all_records = records

    labels_path = output_dir / "labels.jsonl"
    binary_targets_path = output_dir / "binary_targets_preview.jsonl"
    summary_path = output_dir / "summary.json"
    report_path = output_dir / "report.md"
    write_jsonl(labels_path, all_records)
    write_jsonl(binary_targets_path, [row for row in all_records if row["binary_usable"]])

    counts = summarize(all_filled_rows, all_records)
    status = "full_train_independent_codex_labels_filled_not_human_confirmed"
    summary = {
        "schema_version": "h002_full_train_independent_label_fill_summary_v0",
        "status": status,
        "created_at": created_at,
        "input_paths": {
            "readiness_summary": rel_path(readiness_dir / "summary.json"),
            "gap_dir": rel_path(gap_dir),
        },
        "output_dir": rel_path(output_dir),
        "completed_sheets": completed_sheets,
        "output_paths": {
            "labels": rel_path(labels_path),
            "binary_targets_preview": rel_path(binary_targets_path),
            "summary": rel_path(summary_path),
            "report": rel_path(report_path),
        },
        "counts": counts,
        "sheet_summaries": sheet_summaries,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "label_source": "codex_ver_full_train_independent_visible_surface_bootstrap",
            "human_confirmed": False,
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
            "internal_key_read": False,
            "hidden_target_metadata_used": False,
            "vmv_model_input_allowed": False,
            "trains_new_posterior": False,
        },
        "binary_policy": LABEL_TO_BINARY,
        "decision": (
            "Codex-version independent labels are filled on the rank/role-hidden "
            "label-ready sheets. Treat them as bootstrap labels only; run full-train "
            "independent label ingestion before any posterior smoke."
        ),
        "next_todo": "full_train_independent_label_ingestion",
    }
    write_json(summary_path, summary)
    write_report(report_path, summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    counts = summary["counts"]
    print(
        f"status={summary['status']} rows={counts['rows']} binary={counts['binary_usable_rows']} "
        f"positive={counts['positive_rows']} negative={counts['negative_rows']} "
        f"excluded={counts['excluded_rows']} validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
