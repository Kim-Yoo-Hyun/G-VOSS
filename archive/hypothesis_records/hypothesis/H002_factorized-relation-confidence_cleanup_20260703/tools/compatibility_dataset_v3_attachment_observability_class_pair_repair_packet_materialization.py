#!/usr/bin/env python3
"""Materialize R7 attachment-observability packets for class-pair repair rows."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
ARTIFACT_ROOT = H2_ROOT / "artifacts"

DEFAULT_PLAN_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan"
)
DEFAULT_OUTPUT_DIR = (
    ARTIFACT_ROOT
    / "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization"
)

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_plan_ready"
)
EXPECTED_PLAN_NEXT = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_ready_for_label_fill"
)
STATUS_PARTIAL = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_partial_needs_gap_audit"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_materialization_errors"
)
NEXT_READY = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_label_fill"
)
NEXT_PARTIAL = (
    "compatibility_dataset_v3_attachment_observability_class_pair_repair_packet_gap_audit"
)

TARGET_ROWS = 480
IMAGE_LIMIT_PER_OBJECT = 6
THUMB_SIZE = 280
CARD_WIDTH = 980
CARD_HEIGHT = 620

VISIBLE_REVIEW_FIELDS = [
    "review_row_id",
    "candidate_relation",
    "subject_label",
    "predicate_label",
    "object_label",
    "relation_route",
    "review_order",
    "packet_scope",
    "packet_status",
    "evidence_tier",
    "subject_image_count",
    "object_image_count",
    "pair_shared_view_count",
    "pair_shared_frame_count",
    "mesh_ready",
    "sequence_ready",
    "review_observability_label",
    "review_relation_label",
    "review_evidence_quality",
    "review_endpoint_identity",
    "review_notes",
]

FORBIDDEN_VISIBLE_TOKENS = [
    "local_dataset",
    "scan_id",
    "subgraph_id",
    "subject_id",
    "object_id",
    "candidate_id",
    "prediction_id",
    "directed_pair_id",
    "packet_request_id",
    "source_score",
    "source_rank",
    "source_id",
    "rank_band",
    "semantic_score",
    "semantic_rank",
    "proxy",
    "gt_",
    "geometry_bucket",
    "coverage_proxy",
    "uncertainty_bucket",
    "p_geom_valid",
    "label_match_status",
    "construction_bucket",
    "hidden",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def validate_inputs(
    plan_summary: dict[str, Any],
    visible_plan_rows: list[dict[str, Any]],
    hidden_plan_rows: list[dict[str, Any]],
    evidence_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})
    for name, rows in [
        ("packet_plan_rows", visible_plan_rows),
        ("hidden_asset_manifest_plan", hidden_plan_rows),
        ("evidence_inventory_by_candidate", evidence_rows),
    ]:
        if len(rows) != TARGET_ROWS:
            errors.append({"error_type": f"{name}_count_mismatch", "actual": len(rows), "expected": TARGET_ROWS})
    visible_ids = {row.get("review_row_id") for row in visible_plan_rows}
    hidden_ids = {row.get("review_row_id") for row in hidden_plan_rows}
    if visible_ids != hidden_ids:
        errors.append({"error_type": "visible_hidden_review_id_mismatch"})
    candidate_ids = {row.get("candidate_id") for row in hidden_plan_rows}
    evidence_ids = {row.get("candidate_id") for row in evidence_rows}
    if candidate_ids != evidence_ids:
        errors.append({"error_type": "hidden_evidence_candidate_id_mismatch"})
    boundary = plan_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "fills_labels",
        "materializes_packet_assets",
        "materializes_model_rows",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
        "multi_view_or_mesh_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "plan_boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("multi_view_or_mesh_as_audit_evidence_only") is not True:
        errors.append(
            {
                "error_type": "plan_audit_evidence_boundary_not_true",
                "actual": boundary.get("multi_view_or_mesh_as_audit_evidence_only"),
            }
        )
    return errors


def font() -> ImageFont.ImageFont:
    return ImageFont.load_default()


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    lines: list[str],
    fill: tuple[int, int, int] = (20, 20, 20),
    spacing: int = 20,
) -> None:
    x, y = xy
    fnt = font()
    for line in lines:
        draw.text((x, y), line, fill=fill, font=fnt)
        y += spacing


def load_thumbnail(source: Path, size: int = THUMB_SIZE) -> Image.Image | None:
    try:
        with Image.open(source) as image:
            rgb = image.convert("RGB")
            rgb.thumbnail((size, size))
            return rgb.copy()
    except Exception:
        return None


def save_thumbnail(source: Path, target: Path) -> bool:
    image = load_thumbnail(source)
    if image is None:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="JPEG", quality=88)
    return True


def materialize_image_group(source_paths: list[str], packet_dir: Path, prefix: str) -> tuple[list[Path], list[dict[str, Any]]]:
    copied: list[Path] = []
    hidden_sources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, raw_source in enumerate(source_paths[:IMAGE_LIMIT_PER_OBJECT], start=1):
        if raw_source in seen:
            continue
        seen.add(raw_source)
        source = REPO_ROOT / raw_source if not Path(raw_source).is_absolute() else Path(raw_source)
        target = packet_dir / "images" / f"{prefix}_{idx:02d}.jpg"
        if save_thumbnail(source, target):
            copied.append(target)
            hidden_sources.append(
                {
                    "visible_name": target.name,
                    "source_path_hidden": raw_source,
                    "materialized_path_hidden": rel_path(target),
                    "bytes": target.stat().st_size,
                }
            )
    return copied, hidden_sources


def make_pair_crop(
    subject_images: list[Path],
    object_images: list[Path],
    target: Path,
    subject_label: str,
    predicate_label: str,
    object_label: str,
) -> bool:
    subject = load_thumbnail(subject_images[0], 360) if subject_images else None
    obj = load_thumbnail(object_images[0], 360) if object_images else None
    if subject is None and obj is None:
        return False
    canvas = Image.new("RGB", (980, 560), "white")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 979, 559), outline=(30, 30, 30), width=2)
    draw_text_block(
        draw,
        (24, 18),
        [
            "Pair Evidence",
            f"Subject: {subject_label}",
            f"Predicate: {predicate_label}",
            f"Object: {object_label}",
        ],
        spacing=22,
    )
    if subject is not None:
        canvas.paste(subject, (72, 154))
        draw.rectangle((66, 148, 426, 508), outline=(185, 28, 28), width=4)
        draw.text((74, 126), "subject", fill=(185, 28, 28), font=font())
    else:
        draw.rectangle((66, 148, 426, 508), outline=(185, 28, 28), width=4)
        draw.text((118, 322), "subject view missing", fill=(185, 28, 28), font=font())
    if obj is not None:
        canvas.paste(obj, (554, 154))
        draw.rectangle((548, 148, 908, 508), outline=(30, 80, 190), width=4)
        draw.text((556, 126), "object", fill=(30, 80, 190), font=font())
    else:
        draw.rectangle((548, 148, 908, 508), outline=(30, 80, 190), width=4)
        draw.text((600, 322), "object view missing", fill=(30, 80, 190), font=font())
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG")
    return True


def make_multiview_sheet(subject_images: list[Path], object_images: list[Path], target: Path, subject_label: str, object_label: str) -> bool:
    cells: list[tuple[str, str, Image.Image]] = []
    for role, label, paths in [
        ("subject", subject_label, subject_images),
        ("object", object_label, object_images),
    ]:
        for idx, path in enumerate(paths, start=1):
            image = load_thumbnail(path)
            if image is not None:
                cells.append((role, f"{label} view {idx}", image))
    if not cells:
        return False
    cols = 4
    label_h = 34
    cell_w = THUMB_SIZE
    cell_h = THUMB_SIZE + label_h
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (role, label, image) in enumerate(cells):
        col = idx % cols
        row = idx // cols
        x = col * cell_w
        y = row * cell_h
        color = (185, 28, 28) if role == "subject" else (30, 80, 190)
        draw.rectangle((x + 1, y + 1, x + cell_w - 2, y + cell_h - 2), outline=color, width=3)
        draw.text((x + 8, y + 8), f"{role}: {label}"[:44], fill=color, font=font())
        sheet.paste(image, (x + max((cell_w - image.width) // 2, 0), y + label_h))
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, format="JPEG", quality=90)
    return True


def make_evidence_card(
    target: Path,
    visible: dict[str, Any],
    hidden: dict[str, Any],
    subject_count: int,
    object_count: int,
) -> bool:
    canvas = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, CARD_WIDTH - 1, CARD_HEIGHT - 1), outline=(30, 30, 30), width=2)
    draw.rectangle((0, 0, CARD_WIDTH - 1, 84), fill=(245, 245, 245), outline=(30, 30, 30), width=2)
    draw_text_block(
        draw,
        (24, 18),
        [
            "Attachment Observability Evidence",
            f"{visible['subject_label']} -- {visible['predicate_label']} -- {visible['object_label']}",
        ],
        spacing=25,
    )
    lines = [
        "Reviewer-visible evidence summary:",
        "",
        f"- packet status: {visible['packet_status']}",
        f"- evidence tier: {visible['evidence_tier']}",
        f"- subject views copied: {subject_count}",
        f"- object views copied: {object_count}",
        f"- pair shared view count: {visible['pair_shared_view_count']}",
        f"- pair shared frame count: {visible['pair_shared_frame_count']}",
        f"- mesh/semseg ready: {visible['mesh_ready']}",
        f"- sequence ready: {visible['sequence_ready']}",
        "",
        "Review order:",
        "1. Decide whether evidence is observable enough.",
        "2. If observable, accept or reject the relation.",
        "3. If not observable or endpoint identity is ambiguous, abstain.",
        "",
        "Hidden provenance and source-confidence fields are not shown in this packet.",
    ]
    draw_text_block(draw, (44, 118), lines, spacing=24)
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG")
    return True


def packet_status(subject_count: int, object_count: int, pair_ready: bool, card_ready: bool, multiview_ready: bool) -> str:
    if subject_count > 0 and object_count > 0 and pair_ready and card_ready and multiview_ready:
        return "ready"
    if subject_count > 0 or object_count > 0 or pair_ready or card_ready or multiview_ready:
        return "partial"
    return "missing"


def write_packet_md(path: Path, visible: dict[str, Any]) -> None:
    lines = [
        "# Attachment Observability Relation Evidence Packet",
        "",
        f"Review row id: `{visible['review_row_id']}`",
        "",
        "Relation:",
        "",
        f"- Subject: `{visible['subject_label']}`",
        f"- Predicate: `{visible['predicate_label']}`",
        f"- Object: `{visible['object_label']}`",
        "",
        "Boundary:",
        "",
        "This packet contains reviewer-facing multi-view and mesh/observability evidence only. Audit metadata and labels are stored separately.",
        "",
        "## Pair Crop",
        "",
        "![pair crop](pair_crop.png)",
        "",
        "## Evidence Card",
        "",
        "![evidence card](observability_card.png)",
        "",
        "## Multi-View Sheet",
        "",
        "![multi-view sheet](multiview_sheet.jpg)",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def materialize_packet(
    visible_plan: dict[str, Any],
    hidden_plan: dict[str, Any],
    packet_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if packet_dir.exists():
        shutil.rmtree(packet_dir)
    packet_dir.mkdir(parents=True, exist_ok=True)
    (packet_dir / "images").mkdir(exist_ok=True)

    subject_images, subject_hidden = materialize_image_group(
        list(hidden_plan.get("subject_asset_samples", [])),
        packet_dir,
        "subject",
    )
    object_images, object_hidden = materialize_image_group(
        list(hidden_plan.get("object_asset_samples", [])),
        packet_dir,
        "object",
    )

    pair_crop = packet_dir / "pair_crop.png"
    observability_card = packet_dir / "observability_card.png"
    multiview_sheet = packet_dir / "multiview_sheet.jpg"

    pair_ready = make_pair_crop(
        subject_images,
        object_images,
        pair_crop,
        str(visible_plan["subject_label"]),
        str(visible_plan["predicate_label"]),
        str(visible_plan["object_label"]),
    )
    visible = dict(visible_plan)
    status = packet_status(len(subject_images), len(object_images), pair_ready, True, bool(subject_images or object_images))
    visible["packet_status"] = status
    card_ready = make_evidence_card(observability_card, visible, hidden_plan, len(subject_images), len(object_images))
    multiview_ready = make_multiview_sheet(
        subject_images,
        object_images,
        multiview_sheet,
        str(visible_plan["subject_label"]),
        str(visible_plan["object_label"]),
    )
    status = packet_status(len(subject_images), len(object_images), pair_ready, card_ready, multiview_ready)
    visible["packet_status"] = status

    packet_md = packet_dir / "packet.md"
    write_packet_md(packet_md, visible)

    hidden_out = {
        **hidden_plan,
        "subject_label": visible_plan["subject_label"],
        "predicate_label": visible_plan["predicate_label"],
        "object_label": visible_plan["object_label"],
        "packet_status_hidden": status,
        "packet_dir_hidden": rel_path(packet_dir),
        "packet_md_hidden": rel_path(packet_md),
        "pair_crop_path_hidden": rel_path(pair_crop if pair_ready else None),
        "observability_card_path_hidden": rel_path(observability_card if card_ready else None),
        "multiview_sheet_path_hidden": rel_path(multiview_sheet if multiview_ready else None),
        "subject_image_count_hidden": len(subject_images),
        "object_image_count_hidden": len(object_images),
        "pair_crop_ready_hidden": pair_ready,
        "observability_card_ready_hidden": card_ready,
        "multiview_sheet_ready_hidden": multiview_ready,
        "subject_image_sources_hidden": subject_hidden,
        "object_image_sources_hidden": object_hidden,
        "boundary_hidden": "packet evidence only; not model input, not label target construction, and not paper evidence",
    }
    return visible, hidden_out


def leakage_scan_visible_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        for field, value in row.items():
            lower_field = field.lower()
            lower_value = str(value).lower()
            for token in FORBIDDEN_VISIBLE_TOKENS:
                token_lower = token.lower()
                if token_lower in lower_field or token_lower in lower_value:
                    hits.append({"row": idx, "field": field, "hit_type": "forbidden_visible_token", "token": token})
    return hits


def leakage_scan_packet_text(packet_root: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for packet_md in packet_root.glob("*/packet.md"):
        text = packet_md.read_text(encoding="utf-8", errors="ignore").lower()
        for token in FORBIDDEN_VISIBLE_TOKENS:
            token_lower = token.lower()
            if token_lower in text:
                hits.append({"surface": rel_path(packet_md), "hit_type": "forbidden_visible_token", "token": token})
    return hits


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# R7 Attachment Observability Class-Pair Repair Packet Materialization",
            "",
            "## Result",
            "",
            "```text",
            f"status = {summary['status']}",
            f"selected_path = {summary['selected_path']}",
            f"validation_errors = {summary['validation_errors']}",
            f"next_todo = {summary['next_todo']}",
            "```",
            "",
            "## Counts",
            "",
            "```json",
            json.dumps(summary["counts"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Boundary",
            "",
            "This step materializes packet assets and a label-ready visible sheet. It does not fill labels, ingest targets, create model-safe rows, run learned smoke, use validation/test data, or modify H001 artifacts.",
            "",
            "The visible sheet intentionally excludes scan ids, instance ids, source/rank fields, proxy roles, GT status, construction buckets, and filesystem paths. Packet paths are kept in the hidden manifest and can be resolved by `review_row_id`.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary = read_json(args.plan_dir / "summary.json")
    visible_plan_rows = read_jsonl(args.plan_dir / "packet_plan_rows.jsonl")
    hidden_plan_rows = read_jsonl(args.plan_dir / "hidden_asset_manifest_plan.jsonl")
    evidence_rows = read_jsonl(args.plan_dir / "evidence_inventory_by_candidate.jsonl")
    validation_errors = validate_inputs(plan_summary, visible_plan_rows, hidden_plan_rows, evidence_rows)

    hidden_by_id = {row["review_row_id"]: row for row in hidden_plan_rows}
    visible_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    for visible_plan in visible_plan_rows:
        review_id = str(visible_plan["review_row_id"])
        packet_dir = output_dir / "packets" / review_id
        visible, hidden = materialize_packet(visible_plan, hidden_by_id[review_id], packet_dir)
        visible_rows.append(visible)
        hidden_rows.append(hidden)

    visible_leakage_hits = leakage_scan_visible_rows(visible_rows)
    visible_leakage_hits.extend(leakage_scan_packet_text(output_dir / "packets"))
    if visible_leakage_hits:
        validation_errors.append({"error_type": "visible_leakage_hits_present", "count": len(visible_leakage_hits)})

    status_counts = Counter(row["packet_status_hidden"] for row in hidden_rows)
    predicate_status_counts = Counter(
        f"{row['predicate_label']}|{row['packet_status_hidden']}" for row in hidden_rows
    )
    proxy_status_counts = Counter(
        f"{row['hidden_proxy_role']}|{row['packet_status_hidden']}" for row in hidden_rows
    )
    tier_status_counts = Counter(f"{row['evidence_tier']}|{row['packet_status_hidden']}" for row in hidden_rows)
    label_ready = [row for row in hidden_rows if row["packet_status_hidden"] == "ready"]
    non_ready = [row for row in hidden_rows if row["packet_status_hidden"] != "ready"]

    if len(visible_rows) != TARGET_ROWS:
        validation_errors.append({"error_type": "materialized_visible_count_mismatch", "actual": len(visible_rows)})
    if len(hidden_rows) != TARGET_ROWS:
        validation_errors.append({"error_type": "materialized_hidden_count_mismatch", "actual": len(hidden_rows)})

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "attachment_observability_packet_materialization_errors"
        next_todo = "repair_attachment_observability_class_pair_repair_packet_materialization"
    elif non_ready:
        status = STATUS_PARTIAL
        selected_path = "attachment_observability_packets_partial_gap_audit_required"
        next_todo = NEXT_PARTIAL
    else:
        status = STATUS_READY
        selected_path = "attachment_observability_packets_ready_for_label_fill"
        next_todo = NEXT_READY

    output_paths = {
        "visible_review_sheet": output_dir / "visible_review_sheet.csv",
        "packet_manifest": output_dir / "packet_manifest.jsonl",
        "materialized_hidden_manifest": output_dir / "materialized_hidden_manifest.jsonl",
        "label_ready_manifest": output_dir / "label_ready_manifest.jsonl",
        "non_ready_packet_rows": output_dir / "non_ready_packet_rows.jsonl",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
    }
    counts = {
        "packet_rows": len(hidden_rows),
        "packet_status_counts": dict(status_counts),
        "predicate_status_counts": dict(sorted(predicate_status_counts.items())),
        "proxy_status_counts": dict(sorted(proxy_status_counts.items())),
        "tier_status_counts": dict(sorted(tier_status_counts.items())),
        "label_ready_rows": len(label_ready),
        "non_ready_rows": len(non_ready),
        "visible_leakage_hits": len(visible_leakage_hits),
        "subject_image_rows": sum(1 for row in hidden_rows if row["subject_image_count_hidden"] > 0),
        "object_image_rows": sum(1 for row in hidden_rows if row["object_image_count_hidden"] > 0),
        "pair_crop_rows": sum(1 for row in hidden_rows if row["pair_crop_ready_hidden"]),
        "observability_card_rows": sum(1 for row in hidden_rows if row["observability_card_ready_hidden"]),
        "multiview_sheet_rows": sum(1 for row in hidden_rows if row["multiview_sheet_ready_hidden"]),
        "total_subject_images": sum(row["subject_image_count_hidden"] for row in hidden_rows),
        "total_object_images": sum(row["object_image_count_hidden"] for row in hidden_rows),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
        "plan_status": plan_summary.get("status"),
        "counts": counts,
        "boundary": {
            "split": "train_only_packet_materialization",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_packet_assets": True,
            "fills_labels": False,
            "ingests_labels": False,
            "materializes_model_rows": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "multi_view_or_mesh_as_audit_evidence": True,
            "multi_view_or_mesh_as_model_input": False,
            "proxy_roles_hidden_sampling_only": True,
            "final_target_requires_visible_packet_label_fill": True,
        },
        "input_paths": {
            "plan_summary": rel_path(args.plan_dir / "summary.json"),
            "packet_plan_rows": rel_path(args.plan_dir / "packet_plan_rows.jsonl"),
            "hidden_asset_manifest_plan": rel_path(args.plan_dir / "hidden_asset_manifest_plan.jsonl"),
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
    }

    write_csv(output_paths["visible_review_sheet"], visible_rows, VISIBLE_REVIEW_FIELDS)
    write_jsonl(output_paths["packet_manifest"], visible_rows)
    write_jsonl(output_paths["materialized_hidden_manifest"], hidden_rows)
    write_jsonl(output_paths["label_ready_manifest"], label_ready)
    write_jsonl(output_paths["non_ready_packet_rows"], non_ready)
    write_jsonl(output_paths["visible_leakage_hits"], visible_leakage_hits)
    write_jsonl(output_paths["validation_errors"], validation_errors)
    write_json(output_paths["summary"], summary)
    output_paths["report"].write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status != STATUS_ERROR else 1


if __name__ == "__main__":
    raise SystemExit(main())
