#!/usr/bin/env python3
"""Materialize visual/mesh audit packets for H002 support/contact candidates."""

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

DEFAULT_SOURCE_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory"
)
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization"
)

EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_source_inventory_ready_for_packet_materialization"
)
EXPECTED_SOURCE_NEXT = "compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization_ready_for_label_fill"
)
STATUS_PARTIAL = (
    "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization_partial_needs_gap_audit"
)
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_materialization_errors"
SELECTED_PATH_READY = "packet_assets_materialized_visible_sheet_ready_for_label_fill"
SELECTED_PATH_PARTIAL = "packet_assets_materialized_partial_gap_audit_required"
NEXT_READY = "compatibility_dataset_v3_support_contact_visual_mesh_audit_label_fill"
NEXT_PARTIAL = "compatibility_dataset_v3_support_contact_visual_mesh_audit_packet_gap_audit"

TARGET_ROWS = 480
IMAGE_LIMIT_PER_OBJECT = 4
THUMB_SIZE = 300
CARD_WIDTH = 900
CARD_HEIGHT = 560

VISIBLE_FIELDS = [
    "review_id",
    "scan_id_visible",
    "subject_label",
    "predicate_label",
    "object_label",
    "point_crop_path",
    "mesh_render_path",
    "multiview_contact_sheet_path",
    "mesh_contact_summary_visible",
    "pose_summary_visible",
    "coverage_summary_visible",
    "review_relation_reliability",
    "review_geometry_support",
    "review_observability",
    "review_counter_relation",
    "review_uncertainty_reason",
    "review_notes",
]

FORBIDDEN_VISIBLE_TOKENS = [
    "local_dataset",
    "source_score",
    "source_rank",
    "source_id",
    "queue_kind",
    "geometry_status",
    "p_geom_valid",
    "label_match_status",
    "construction_bucket",
    "hidden_stratum",
    "prediction_id",
    "semantic_score",
    "semantic_rank",
    "rank_band",
    "machine_hint",
    "matched_predicates",
    "subject_id",
    "object_id",
    "PACKET_PENDING",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
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
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def validate_inputs(summary: dict[str, Any], visible_rows: list[dict[str, str]], hidden_rows: list[dict[str, Any]], packet_sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_status", "actual": summary.get("status"), "expected": EXPECTED_SOURCE_STATUS})
    if summary.get("next_todo") != EXPECTED_SOURCE_NEXT:
        errors.append({"error_type": "unexpected_source_next_todo", "actual": summary.get("next_todo"), "expected": EXPECTED_SOURCE_NEXT})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_validation_errors_present", "actual": summary.get("validation_errors")})
    if len(visible_rows) != TARGET_ROWS:
        errors.append({"error_type": "visible_row_count_mismatch", "actual": len(visible_rows), "expected": TARGET_ROWS})
    if len(hidden_rows) != TARGET_ROWS:
        errors.append({"error_type": "hidden_row_count_mismatch", "actual": len(hidden_rows), "expected": TARGET_ROWS})
    if len(packet_sources) != TARGET_ROWS:
        errors.append({"error_type": "packet_source_count_mismatch", "actual": len(packet_sources), "expected": TARGET_ROWS})
    visible_ids = {row["review_id"] for row in visible_rows}
    hidden_ids = {row["review_id"] for row in hidden_rows}
    packet_ids = {row["review_id"] for row in packet_sources}
    if visible_ids != hidden_ids or visible_ids != packet_ids:
        errors.append({"error_type": "review_id_set_mismatch"})
    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "source_boundary_not_false", "key": key, "actual": boundary.get(key)})
    return errors


def unique_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        out.append(path)
    return out


def scan_dir(scan_root: Path, scan_id: str) -> Path:
    return scan_root / scan_id


def find_object_images(scan_root: Path, scan_id: str, object_id: Any, limit: int) -> list[Path]:
    multi_view = scan_dir(scan_root, str(scan_id)) / "multi_view"
    if not multi_view.exists():
        return []
    object_text = str(object_id)
    cropped = sorted(multi_view.glob(f"instance_{object_text}_class_*_croped_view*_*.jpg"))
    direct = [
        path
        for path in sorted(multi_view.glob(f"instance_{object_text}_class_*_view*_*.jpg"))
        if "_croped_" not in path.name
    ]
    return unique_paths(cropped + direct)[:limit]


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


def materialize_image_group(source_paths: list[Path], packet_dir: Path, prefix: str) -> tuple[list[Path], list[dict[str, Any]]]:
    copied: list[Path] = []
    hidden_sources: list[dict[str, Any]] = []
    for idx, source in enumerate(source_paths, start=1):
        target = packet_dir / "images" / f"{prefix}_{idx:02d}.jpg"
        if save_thumbnail(source, target):
            copied.append(target)
            hidden_sources.append(
                {
                    "visible_name": target.name,
                    "source_path_hidden": rel_path(source),
                    "materialized_path_hidden": rel_path(target),
                    "bytes": target.stat().st_size,
                }
            )
    return copied, hidden_sources


def font() -> ImageFont.ImageFont:
    return ImageFont.load_default()


def draw_text_block(draw: ImageDraw.ImageDraw, xy: tuple[int, int], lines: list[str], fill: tuple[int, int, int] = (20, 20, 20), spacing: int = 18) -> None:
    x, y = xy
    fnt = font()
    for line in lines:
        draw.text((x, y), line, fill=fill, font=fnt)
        y += spacing


def make_pair_crop(subject_images: list[Path], object_images: list[Path], target: Path, subject_label: str, predicate_label: str, object_label: str) -> bool:
    subject = load_thumbnail(subject_images[0], 360) if subject_images else None
    obj = load_thumbnail(object_images[0], 360) if object_images else None
    if subject is None and obj is None:
        return False
    canvas = Image.new("RGB", (900, 520), "white")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 899, 519), outline=(30, 30, 30), width=2)
    draw_text_block(
        draw,
        (24, 20),
        [
            "Pair Evidence",
            f"Subject: {subject_label}",
            f"Predicate: {predicate_label}",
            f"Object: {object_label}",
        ],
        spacing=20,
    )
    if subject is not None:
        canvas.paste(subject, (60, 145))
        draw.rectangle((55, 140, 415, 500), outline=(185, 28, 28), width=4)
        draw.text((62, 118), "subject", fill=(185, 28, 28), font=font())
    else:
        draw.rectangle((55, 140, 415, 500), outline=(185, 28, 28), width=4)
        draw.text((95, 310), "subject view missing", fill=(185, 28, 28), font=font())
    if obj is not None:
        canvas.paste(obj, (485, 145))
        draw.rectangle((480, 140, 840, 500), outline=(30, 80, 190), width=4)
        draw.text((487, 118), "object", fill=(30, 80, 190), font=font())
    else:
        draw.rectangle((480, 140, 840, 500), outline=(30, 80, 190), width=4)
        draw.text((520, 310), "object view missing", fill=(30, 80, 190), font=font())
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
        draw.text((x + 8, y + 8), f"{role}: {label}"[:42], fill=color, font=font())
        sheet.paste(image, (x + max((cell_w - image.width) // 2, 0), y + label_h))
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, format="JPEG", quality=90)
    return True


def make_mesh_card(target: Path, subject_label: str, predicate_label: str, object_label: str, source_row: dict[str, Any]) -> bool:
    exists_keys = [
        "aligned_ply_exists",
        "mesh_obj_exists",
        "mesh_seg_exists",
        "semseg_exists",
        "sequence_zip_exists",
    ]
    if not all(source_row.get(key) is True for key in exists_keys):
        return False
    canvas = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), "white")
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, CARD_WIDTH - 1, CARD_HEIGHT - 1), outline=(30, 30, 30), width=2)
    draw.rectangle((0, 0, CARD_WIDTH - 1, 76), fill=(245, 245, 245), outline=(30, 30, 30), width=2)
    draw_text_block(
        draw,
        (24, 18),
        [
            "Mesh / Geometry Evidence",
            f"{subject_label}  -- {predicate_label} --  {object_label}",
        ],
        spacing=24,
    )
    lines = [
        "Reviewer-visible evidence availability:",
        "",
        "- aligned object point labels: available",
        "- scene mesh geometry: available",
        "- mesh segmentation metadata: available",
        "- object semantic segmentation: available",
        "- RGB-D sequence / multi-view source: available",
        "",
        "Use this together with the pair crop and multi-view sheet.",
        "Internal file paths and source-confidence fields are hidden from this packet.",
    ]
    draw_text_block(draw, (44, 115), lines, spacing=24)
    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(target, format="PNG")
    return True


def write_packet_md(path: Path, visible: dict[str, Any]) -> None:
    lines = [
        "# Support/Contact Relation Evidence Packet",
        "",
        f"Review id: `{visible['review_id']}`",
        "",
        "Relation:",
        "",
        f"- Subject: `{visible['subject_label']}`",
        f"- Predicate: `{visible['predicate_label']}`",
        f"- Object: `{visible['object_label']}`",
        "",
        "Boundary:",
        "",
        "This packet contains reviewer-facing visual and mesh evidence only. Source confidence, rank, old geometry status, old geometry score, and target-construction fields are stored separately.",
        "",
        "## Pair Crop",
        "",
        f"![pair crop]({Path(visible['point_crop_path']).name})",
        "",
        "## Mesh / Geometry Card",
        "",
        f"![mesh card]({Path(visible['mesh_render_path']).name})",
        "",
        "## Multi-View Sheet",
        "",
        f"![multi-view sheet]({Path(visible['multiview_contact_sheet_path']).name})",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def packet_status(subject_count: int, object_count: int, pair_ready: bool, mesh_ready: bool, multiview_ready: bool) -> str:
    if subject_count > 0 and object_count > 0 and pair_ready and mesh_ready and multiview_ready:
        return "ready"
    if subject_count > 0 or object_count > 0 or pair_ready or mesh_ready or multiview_ready:
        return "partial"
    return "missing"


def materialize_packet(
    visible_template: dict[str, str],
    hidden: dict[str, Any],
    source: dict[str, Any],
    packet_dir: Path,
    scan_root: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if packet_dir.exists():
        shutil.rmtree(packet_dir)
    packet_dir.mkdir(parents=True, exist_ok=True)
    (packet_dir / "images").mkdir(exist_ok=True)

    subject_sources = find_object_images(scan_root, hidden["scan_id"], hidden["subject_id"], IMAGE_LIMIT_PER_OBJECT)
    object_sources = find_object_images(scan_root, hidden["scan_id"], hidden["object_id"], IMAGE_LIMIT_PER_OBJECT)
    subject_images, subject_hidden = materialize_image_group(subject_sources, packet_dir, "subject")
    object_images, object_hidden = materialize_image_group(object_sources, packet_dir, "object")

    point_crop = packet_dir / "point_pair_crop.png"
    mesh_render = packet_dir / "mesh_contact_render.png"
    multiview_sheet = packet_dir / "multiview_contact_sheet.jpg"

    pair_ready = make_pair_crop(
        subject_images,
        object_images,
        point_crop,
        visible_template["subject_label"],
        visible_template["predicate_label"],
        visible_template["object_label"],
    )
    mesh_ready = make_mesh_card(
        mesh_render,
        visible_template["subject_label"],
        visible_template["predicate_label"],
        visible_template["object_label"],
        source,
    )
    multiview_ready = make_multiview_sheet(
        subject_images,
        object_images,
        multiview_sheet,
        visible_template["subject_label"],
        visible_template["object_label"],
    )

    status = packet_status(len(subject_images), len(object_images), pair_ready, mesh_ready, multiview_ready)
    visible = dict(visible_template)
    visible.update(
        {
            "point_crop_path": rel_path(point_crop if pair_ready else None),
            "mesh_render_path": rel_path(mesh_render if mesh_ready else None),
            "multiview_contact_sheet_path": rel_path(multiview_sheet if multiview_ready else None),
            "mesh_contact_summary_visible": (
                "mesh/point sources available; inspect mesh card and pair crop"
                if mesh_ready
                else "mesh/point evidence incomplete"
            ),
            "pose_summary_visible": (
                f"subject views={len(subject_images)}; object views={len(object_images)}; relation={visible_template['predicate_label']}"
            ),
            "coverage_summary_visible": (
                f"packet_status={status}; subject_views={len(subject_images)}; object_views={len(object_images)}"
            ),
        }
    )
    packet_md = packet_dir / "packet.md"
    write_packet_md(packet_md, visible)

    hidden_out = {
        **hidden,
        "packet_status_hidden": status,
        "packet_dir_hidden": rel_path(packet_dir),
        "packet_md_hidden": rel_path(packet_md),
        "point_crop_path_hidden": rel_path(point_crop if pair_ready else None),
        "mesh_render_path_hidden": rel_path(mesh_render if mesh_ready else None),
        "multiview_contact_sheet_path_hidden": rel_path(multiview_sheet if multiview_ready else None),
        "subject_image_count_hidden": len(subject_images),
        "object_image_count_hidden": len(object_images),
        "pair_crop_ready_hidden": pair_ready,
        "mesh_render_ready_hidden": mesh_ready,
        "multiview_sheet_ready_hidden": multiview_ready,
        "subject_image_sources_hidden": subject_hidden,
        "object_image_sources_hidden": object_hidden,
        "raw_packet_sources_hidden": {
            key: value for key, value in source.items() if key.endswith("_source_hidden")
        },
        "boundary_hidden": "visual/mesh audit evidence only; not model input and not label target construction",
    }
    return visible, hidden_out


def leakage_scan_text(path: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if not path.exists() or not path.is_file():
        return hits
    text = path.read_text(encoding="utf-8", errors="ignore")
    lower = text.lower()
    for token in FORBIDDEN_VISIBLE_TOKENS:
        if token.lower() in lower:
            hits.append({"surface": rel_path(path), "hit_type": "forbidden_visible_token", "token": token})
    return hits


def leakage_scan_visible_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        for field, value in row.items():
            lower = str(value).lower()
            for token in FORBIDDEN_VISIBLE_TOKENS:
                if token.lower() in lower:
                    hits.append({"row": idx, "field": field, "hit_type": "forbidden_visible_token", "token": token})
    return hits


def build_report(summary: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Compatibility Dataset V3 Support/Contact Visual/Mesh Audit Packet Materialization",
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
            "## Packet Counts",
            "",
            "```json",
            json.dumps(summary["counts"], ensure_ascii=False, indent=2, sort_keys=True),
            "```",
            "",
            "## Boundary",
            "",
            "This step materializes reviewer-facing packet assets only. It does not fill labels, train a model, run learned smoke, use validation/test rows, or modify H001 artifacts.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(args.source_dir / "summary.json")
    visible_input = read_csv(args.source_dir / "label_sheet_template.csv")
    hidden_input = read_jsonl(args.source_dir / "hidden_manifest.jsonl")
    packet_sources = read_jsonl(args.source_dir / "packet_source_manifest.jsonl")
    validation_errors = validate_inputs(source_summary, visible_input, hidden_input, packet_sources)

    hidden_by_id = {row["review_id"]: row for row in hidden_input}
    source_by_id = {row["review_id"]: row for row in packet_sources}

    visible_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    for visible_template in visible_input:
        review_id = visible_template["review_id"]
        packet_dir = output_dir / "packets" / review_id
        visible, hidden = materialize_packet(
            visible_template,
            hidden_by_id[review_id],
            source_by_id[review_id],
            packet_dir,
            args.scan_root,
        )
        visible_rows.append(visible)
        hidden_rows.append(hidden)

    visible_leakage_hits = leakage_scan_visible_rows(visible_rows)
    for packet_md in output_dir.glob("packets/*/packet.md"):
        visible_leakage_hits.extend(leakage_scan_text(packet_md))

    status_counts = Counter(row["packet_status_hidden"] for row in hidden_rows)
    predicate_status_counts = Counter(
        f"{row['predicate_label']}|{row['packet_status_hidden']}" for row in hidden_rows
    )
    non_ready = [row for row in hidden_rows if row["packet_status_hidden"] != "ready"]
    label_ready = [row for row in hidden_rows if row["packet_status_hidden"] == "ready"]

    if visible_leakage_hits:
        validation_errors.append({"error_type": "visible_leakage_hits_present", "count": len(visible_leakage_hits)})
    if len(visible_rows) != TARGET_ROWS:
        validation_errors.append({"error_type": "materialized_visible_count_mismatch", "actual": len(visible_rows)})
    if len(hidden_rows) != TARGET_ROWS:
        validation_errors.append({"error_type": "materialized_hidden_count_mismatch", "actual": len(hidden_rows)})

    if validation_errors:
        status = STATUS_ERROR
        selected_path = "packet_materialization_errors"
        next_todo = "repair_support_contact_visual_mesh_audit_packet_materialization"
    elif non_ready:
        status = STATUS_PARTIAL
        selected_path = SELECTED_PATH_PARTIAL
        next_todo = NEXT_PARTIAL
    else:
        status = STATUS_READY
        selected_path = SELECTED_PATH_READY
        next_todo = NEXT_READY

    output_paths = {
        "label_ready_manifest": output_dir / "label_ready_manifest.jsonl",
        "materialized_hidden_manifest": output_dir / "materialized_hidden_manifest.jsonl",
        "non_ready_packet_rows": output_dir / "non_ready_packet_rows.jsonl",
        "packet_manifest": output_dir / "packet_manifest.jsonl",
        "report": output_dir / "report.md",
        "summary": output_dir / "summary.json",
        "validation_errors": output_dir / "validation_errors.jsonl",
        "visible_leakage_hits": output_dir / "visible_leakage_hits.jsonl",
        "visible_review_sheet_with_packets": output_dir / "visible_review_sheet_with_packets.csv",
    }

    counts = {
        "packet_rows": len(hidden_rows),
        "packet_status_counts": dict(status_counts),
        "predicate_status_counts": dict(sorted(predicate_status_counts.items())),
        "label_ready_rows": len(label_ready),
        "non_ready_rows": len(non_ready),
        "subject_image_rows": sum(1 for row in hidden_rows if row["subject_image_count_hidden"] > 0),
        "object_image_rows": sum(1 for row in hidden_rows if row["object_image_count_hidden"] > 0),
        "pair_crop_rows": sum(1 for row in hidden_rows if row["pair_crop_ready_hidden"]),
        "mesh_render_rows": sum(1 for row in hidden_rows if row["mesh_render_ready_hidden"]),
        "multiview_sheet_rows": sum(1 for row in hidden_rows if row["multiview_sheet_ready_hidden"]),
        "total_subject_images": sum(row["subject_image_count_hidden"] for row in hidden_rows),
        "total_object_images": sum(row["object_image_count_hidden"] for row in hidden_rows),
        "visible_leakage_hits": len(visible_leakage_hits),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "source_inventory_status": source_summary.get("status"),
        "counts": counts,
        "boundary": {
            "split": "train full only",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_packet_assets": True,
            "fills_labels": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "multi_view_or_mesh_as_audit_evidence": True,
            "multi_view_or_mesh_as_model_input": False,
        },
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
    }

    write_csv(output_paths["visible_review_sheet_with_packets"], visible_rows, VISIBLE_FIELDS)
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
