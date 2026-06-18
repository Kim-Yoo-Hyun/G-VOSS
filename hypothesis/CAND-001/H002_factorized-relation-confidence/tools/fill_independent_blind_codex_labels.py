#!/usr/bin/env python3
"""Create sanitized H002 blind sheets and fill them with Codex bootstrap labels."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import textwrap
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_PROTOCOL_DIR = RGA_ROOT / "independent_label_protocol"
DEFAULT_INPUT_SHEET = DEFAULT_PROTOCOL_DIR / "blind_all_sheet.tsv"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_blind_codex_labels"
DEFAULT_SANITIZED_SHEET = DEFAULT_PROTOCOL_DIR / "blind_all_sheet_sanitized.tsv"
DEFAULT_FILLED_SHEET = DEFAULT_PROTOCOL_DIR / "blind_all_sheet_codex_ver.tsv"

REVIEWER_ID = "(codex_ver_blind)"
REVIEW_ROUND = "1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-sheet", type=Path, default=DEFAULT_INPUT_SHEET)
    parser.add_argument("--sanitized-sheet", type=Path, default=DEFAULT_SANITIZED_SHEET)
    parser.add_argument("--filled-sheet", type=Path, default=DEFAULT_FILLED_SHEET)
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


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{path}: missing TSV header")
        return list(reader.fieldnames), [dict(row) for row in reader]


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path = as_abs(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path = as_abs(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path = as_abs(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def safe_int(value: str, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_name(value: str) -> str:
    allowed = []
    for char in value.lower().strip():
        if char.isalnum():
            allowed.append(char)
        elif char in {" ", "-", "_", "/"}:
            allowed.append("-")
    cleaned = "".join(allowed).strip("-")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned or "item"


def copy_sanitized_image(src: str, dst: Path) -> str:
    if not src:
        return ""
    src_path = as_abs(Path(src))
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not src_path.exists():
        return ""
    shutil.copy2(src_path, dst)
    return rel_path(dst)


def fit_image(path: Path, size: tuple[int, int]) -> Image.Image:
    if not path.exists():
        return Image.new("RGB", size, (245, 245, 245))
    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.LANCZOS)
    canvas = Image.new("RGB", size, (255, 255, 255))
    x = (size[0] - image.width) // 2
    y = (size[1] - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, font: ImageFont.ImageFont, width: int) -> int:
    x, y = xy
    for line in textwrap.wrap(text, width=width):
        draw.text((x, y), line, fill=(20, 20, 20), font=font)
        y += 22
    return y


def make_contact_sheet(row: dict[str, str], crop_paths: list[str], output_path: Path) -> str:
    output_path = as_abs(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    width, height = 1400, 900
    canvas = Image.new("RGB", (width, height), (250, 250, 246))
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    title = (
        f"{row['subject_label']}({row['subject_id']}) - {row['predicate_label']} -> "
        f"{row['object_label']}({row['object_id']})"
    )
    draw.text((28, 24), title, fill=(0, 0, 0), font=font)
    draw.text((28, 52), f"scan={row['scan_id']} | family={row['predicate_family']}", fill=(35, 35, 35), font=font)
    y = draw_wrapped(draw, (28, 82), f"Question: {row['family_question']}", font, 150)

    labels = ["subject view 1", "subject view 2", "object view 1", "object view 2"]
    positions = [(28, 170), (360, 170), (728, 170), (1060, 170)]
    box_size = (316, 238)
    for label, path, (x, y0) in zip(labels, crop_paths, positions, strict=True):
        draw.text((x, y0 - 22), label, fill=(20, 20, 20), font=font)
        image = fit_image(as_abs(Path(path)), box_size) if path else Image.new("RGB", box_size, (245, 245, 245))
        canvas.paste(image, (x, y0))
        draw.rectangle((x, y0, x + box_size[0], y0 + box_size[1]), outline=(160, 160, 160), width=1)

    checklist = [
        "Review checklist:",
        "1. Are subject/object identities visible enough?",
        "2. Is the relation supported, contradicted, trivial, or ambiguous?",
        "3. Use abstain_uncertain when crops/3D context are insufficient.",
        "4. This sanitized sheet contains only visible identity and crop evidence.",
    ]
    y = max(y + 40, 470)
    for line in checklist:
        draw.text((28, y), line, fill=(25, 25, 25), font=font)
        y += 24

    canvas.save(output_path, quality=92)
    return rel_path(output_path)


def visibility_from_count(value: str) -> str:
    count = safe_int(value)
    if count >= 2:
        return "good"
    if count == 1:
        return "partial"
    return "uncertain"


def support_label(row: dict[str, str]) -> dict[str, str]:
    sub = row["subject_label"].lower()
    obj = row["object_label"].lower()
    pred = row["predicate_label"].lower()

    if sub == "floor":
        label = "invalid_relation"
        support = "contradicts"
        informative = "not_evaluable"
        confidence = "high"
        check = "subject is floor, so floor being supported by furniture is implausible"
    elif sub == "curtain" and obj == "floor":
        label = "invalid_relation"
        support = "contradicts"
        informative = "not_evaluable"
        confidence = "medium"
        check = "curtain-floor support is likely contact/proximity, not support"
    elif sub == "monitor" and obj == "bar":
        label = "abstain_uncertain"
        support = "uncertain"
        informative = "uncertain"
        confidence = "low"
        check = "bar could mean counter/bar object; support cannot be confirmed from visible metadata"
    elif obj == "wall" and sub in {"sink", "bidet"}:
        label = "annotation_sparsity_candidate"
        support = "supports"
        informative = "informative"
        confidence = "medium"
        check = "wall-mounted or wall-supported fixture is plausible"
    elif obj in {
        "floor",
        "desk",
        "couch table",
        "nightstand",
        "kitchen cabinet",
        "table",
        "cabinet",
        "shelf",
    }:
        label = "reliable_informative"
        support = "supports"
        informative = "informative"
        confidence = "medium" if pred == "supported by" else "high"
        check = "support object is a plausible support surface"
    else:
        label = "abstain_uncertain"
        support = "uncertain"
        informative = "uncertain"
        confidence = "low"
        check = "support relation needs visual or mesh confirmation"
    return {
        "relation_validity_label": label,
        "visual_3d_support": support,
        "relation_informativeness": informative,
        "pair_context_sufficient": "yes" if label in {"reliable_informative", "annotation_sparsity_candidate", "invalid_relation"} else "uncertain",
        "family_specific_check": check,
        "confidence": confidence,
    }


def proximity_label(row: dict[str, str]) -> dict[str, str]:
    pair = (row["subject_label"].lower(), row["object_label"].lower())
    informative_pairs = {
        ("chair", "desk"),
        ("chair", "table"),
        ("table", "chair"),
        ("kitchen appliance", "kitchen cabinet"),
        ("oven", "kitchen counter"),
        ("couch table", "couch"),
        ("stand", "armchair"),
        ("stand", "desk"),
        ("toilet paper dispenser", "toilet"),
        ("toilet paper dispenser", "shower"),
    }
    trivial_object_labels = {"floor", "wall"}

    if pair in informative_pairs:
        label = "reliable_informative"
        informative = "informative"
        confidence = "medium"
        check = "proximity is functionally meaningful for this object pair"
    elif pair[0] == pair[1] or pair[0] in trivial_object_labels or pair[1] in trivial_object_labels:
        label = "valid_but_trivial_dense"
        informative = "trivial_dense"
        confidence = "medium"
        check = "close-by relation is likely dense or uninformative for this pair"
    else:
        label = "valid_but_trivial_dense"
        informative = "trivial_dense"
        confidence = "low"
        check = "visible metadata does not show why this proximity edge is informative"
    return {
        "relation_validity_label": label,
        "visual_3d_support": "supports",
        "relation_informativeness": informative,
        "pair_context_sufficient": "yes" if label == "reliable_informative" else "uncertain",
        "family_specific_check": check,
        "confidence": confidence,
    }


def vertical_label(row: dict[str, str]) -> dict[str, str]:
    sub = row["subject_label"].lower()
    obj = row["object_label"].lower()
    pred = row["predicate_label"].lower()

    informative_pairs = {
        ("window", "bench"),
        ("window", "desk"),
        ("toilet paper dispenser", "toilet"),
        ("toilet paper", "toilet brush"),
        ("shelf", "armchair"),
        ("book", "box"),
    }
    trivial_with_ceiling = sub == "ceiling" and pred == "higher than"
    trivial_with_wall_or_floor = obj in {"wall", "floor"} or sub in {"wall", "floor"}
    same_class_ambiguous = sub == obj

    if same_class_ambiguous:
        label = "abstain_uncertain"
        support = "uncertain"
        informative = "uncertain"
        confidence = "low"
        check = "same-class vertical ordering needs instance-level visual confirmation"
    elif (sub, obj) in informative_pairs:
        label = "reliable_informative"
        support = "supports"
        informative = "informative"
        confidence = "medium"
        check = "object category pair gives a meaningful vertical relation"
    elif trivial_with_ceiling or trivial_with_wall_or_floor:
        label = "valid_but_trivial_dense"
        support = "supports"
        informative = "trivial_dense"
        confidence = "medium"
        check = "relation is likely true but too generic for informative edge reliability"
    elif pred == "higher than":
        label = "annotation_sparsity_candidate"
        support = "supports"
        informative = "informative"
        confidence = "low"
        check = "higher-than relation is plausible but needs visual/3D confirmation"
    elif pred == "lower than":
        label = "valid_but_trivial_dense"
        support = "supports"
        informative = "trivial_dense"
        confidence = "low"
        check = "lower-than relation appears generic or under-specified from visible metadata"
    else:
        label = "abstain_uncertain"
        support = "uncertain"
        informative = "uncertain"
        confidence = "low"
        check = "unsupported vertical predicate"
    return {
        "relation_validity_label": label,
        "visual_3d_support": support,
        "relation_informativeness": informative,
        "pair_context_sufficient": "yes" if label in {"reliable_informative", "annotation_sparsity_candidate"} else "uncertain",
        "family_specific_check": check,
        "confidence": confidence,
    }


def assign_label(row: dict[str, str]) -> dict[str, str]:
    family = row["predicate_family"]
    if family == "support_contact":
        return support_label(row)
    if family == "proximity":
        return proximity_label(row)
    if family == "relative_vertical":
        return vertical_label(row)
    return {
        "relation_validity_label": "abstain_uncertain",
        "visual_3d_support": "not_evaluable",
        "relation_informativeness": "not_evaluable",
        "pair_context_sufficient": "uncertain",
        "family_specific_check": "family not handled by codex visible-metadata bootstrap",
        "confidence": "low",
    }


def sanitize_and_fill(
    fieldnames: list[str],
    rows: list[dict[str, str]],
    output_dir: Path,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, Any]]]:
    output_dir = as_abs(output_dir)
    sanitized_asset_dir = output_dir / "sanitized_assets"
    sanitized_contact_dir = output_dir / "sanitized_contact_sheets"
    sanitized_rows: list[dict[str, str]] = []
    filled_rows: list[dict[str, str]] = []
    label_rows: list[dict[str, Any]] = []

    for row in rows:
        blind_id = row["blind_review_id"]
        safe_id = safe_name(blind_id)
        sanitized = dict(row)
        crop_fields = ["subject_image_1", "subject_image_2", "object_image_1", "object_image_2"]
        sanitized_crop_paths: list[str] = []
        for field in crop_fields:
            suffix = field.replace("_image_", "-")
            dst = sanitized_asset_dir / f"{safe_id}_{suffix}.jpg"
            rel = copy_sanitized_image(row.get(field, ""), dst)
            sanitized[field] = rel
            sanitized_crop_paths.append(rel)

        contact_name = (
            f"{safe_id}_{safe_name(row['subject_label'])}_{safe_name(row['predicate_label'])}_"
            f"{safe_name(row['object_label'])}.jpg"
        )
        sanitized["contact_sheet"] = make_contact_sheet(
            sanitized,
            sanitized_crop_paths,
            sanitized_contact_dir / contact_name,
        )
        sanitized_rows.append(sanitized)

        spec = assign_label(sanitized)
        filled = dict(sanitized)
        filled.update(
            {
                "reviewer_id": REVIEWER_ID,
                "review_round": REVIEW_ROUND,
                "subject_visibility": visibility_from_count(sanitized.get("subject_image_count", "")),
                "object_visibility": visibility_from_count(sanitized.get("object_image_count", "")),
                "pair_covisible": "uncertain",
                "pair_context_sufficient": spec["pair_context_sufficient"],
                "visual_3d_support": spec["visual_3d_support"],
                "relation_informativeness": spec["relation_informativeness"],
                "relation_validity_label": spec["relation_validity_label"],
                "family_specific_check": spec["family_specific_check"],
                "confidence": spec["confidence"],
                "notes": (
                    "codex_ver_blind visible-metadata bootstrap label; sanitized assets used; "
                    "no internal key or hidden relation metadata was read; not human-confirmed"
                ),
            }
        )
        filled_rows.append(filled)
        label_rows.append(
            {
                "schema_version": "h002_independent_blind_codex_label_v0",
                "label_source": "codex_ver_blind_visible_metadata_bootstrap",
                "not_human_confirmed": True,
                "paper_evidence_allowed": False,
                "posterior_claim_allowed": False,
                "blind_review_id": blind_id,
                "scan_id": sanitized["scan_id"],
                "subject_id": sanitized["subject_id"],
                "subject_label": sanitized["subject_label"],
                "predicate_label": sanitized["predicate_label"],
                "predicate_family": sanitized["predicate_family"],
                "object_id": sanitized["object_id"],
                "object_label": sanitized["object_label"],
                "relation_validity_label": spec["relation_validity_label"],
                "confidence": spec["confidence"],
                "visual_3d_support": spec["visual_3d_support"],
                "relation_informativeness": spec["relation_informativeness"],
                "family_specific_check": spec["family_specific_check"],
                "contact_sheet": sanitized["contact_sheet"],
            }
        )
    return sanitized_rows, filled_rows, label_rows


def write_family_sheets(base_sheet: Path, fieldnames: list[str], rows: list[dict[str, str]], suffix: str) -> dict[str, str]:
    protocol_dir = as_abs(base_sheet).parent
    paths = {}
    for family in sorted({row["predicate_family"] for row in rows}):
        family_rows = [row for row in rows if row["predicate_family"] == family]
        path = protocol_dir / f"blind_{family}_sheet_{suffix}.tsv"
        write_tsv(path, fieldnames, family_rows)
        paths[family] = rel_path(path)
    return paths


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Blind Label Fill",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Labels are `(codex_ver_blind)` bootstrap labels.",
        "- The fill script reads the blind sheet only; it does not read `internal_key.jsonl`.",
        "- Original contact sheets leaked hidden rank/score/geometry text, so sanitized assets were generated.",
        "- Labels are train-only hypothesis-stage labels and are not paper-locked human labels.",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| rows | {summary['counts']['rows']} |",
        f"| sanitized contact sheets | {summary['counts']['sanitized_contact_sheets']} |",
        f"| binary-usable rows | {summary['counts']['binary_usable_rows']} |",
        f"| positive rows | {summary['counts']['positive_rows']} |",
        f"| negative rows | {summary['counts']['negative_rows']} |",
        f"| excluded rows | {summary['counts']['excluded_rows']} |",
        "",
        "## Label Counts",
        "",
        "| Label | Count |",
        "| --- | ---: |",
    ]
    for label, count in summary["label_counts"].items():
        lines.append(f"| `{label}` | {count} |")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
        ]
    )
    as_abs(path).write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    created_at = datetime.now(timezone.utc).isoformat()
    fieldnames, rows = read_tsv(args.input_sheet)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sanitized_rows, filled_rows, label_rows = sanitize_and_fill(fieldnames, rows, output_dir)
    write_tsv(args.sanitized_sheet, fieldnames, sanitized_rows)
    write_tsv(args.filled_sheet, fieldnames, filled_rows)
    sanitized_family_paths = write_family_sheets(args.sanitized_sheet, fieldnames, sanitized_rows, "sanitized")
    filled_family_paths = write_family_sheets(args.filled_sheet, fieldnames, filled_rows, "codex_ver")

    positive = {"reliable_informative", "annotation_sparsity_candidate"}
    negative = {
        "valid_but_trivial_dense",
        "invalid_relation",
        "invalid_pair",
        "visibility_or_geometry_artifact",
    }
    label_counts = dict(Counter(row["relation_validity_label"] for row in filled_rows))
    positive_rows = sum(label_counts.get(label, 0) for label in positive)
    negative_rows = sum(label_counts.get(label, 0) for label in negative)
    excluded_rows = len(filled_rows) - positive_rows - negative_rows

    summary = {
        "schema_version": "h002_independent_blind_codex_label_fill_summary_v0",
        "status": "independent_blind_codex_labels_filled",
        "created_at": created_at,
        "input_sheet": rel_path(args.input_sheet),
        "sanitized_sheet": rel_path(args.sanitized_sheet),
        "filled_sheet": rel_path(args.filled_sheet),
        "output_dir": rel_path(output_dir),
        "sanitized_family_sheets": sanitized_family_paths,
        "filled_family_sheets": filled_family_paths,
        "leakage_fix": {
            "original_contact_sheets_have_hidden_text": True,
            "sanitized_contact_sheets_created": True,
            "sanitized_crop_paths_created": True,
            "internal_key_read": False,
            "hidden_rank_score_pgeom_used_for_labeling": False,
        },
        "counts": {
            "rows": len(filled_rows),
            "sanitized_contact_sheets": len(filled_rows),
            "binary_usable_rows": positive_rows + negative_rows,
            "positive_rows": positive_rows,
            "negative_rows": negative_rows,
            "excluded_rows": excluded_rows,
        },
        "label_counts": label_counts,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "reviewer_id": REVIEWER_ID,
            "label_source": "codex_ver_blind_visible_metadata_bootstrap",
            "paper_evidence_allowed": False,
            "posterior_claim_allowed": False,
        },
        "decision": (
            "Rank-hidden Codex bootstrap labels are filled on sanitized blind sheets. "
            "Run independent_label_ingestion.py on the filled sheet before any "
            "residual/gated combiner diagnostic."
        ),
    }
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "labels.jsonl", label_rows)
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} rows={summary['counts']['rows']} "
        f"binary={summary['counts']['binary_usable_rows']} "
        f"positive={summary['counts']['positive_rows']} negative={summary['counts']['negative_rows']} "
        f"excluded={summary['counts']['excluded_rows']} validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
