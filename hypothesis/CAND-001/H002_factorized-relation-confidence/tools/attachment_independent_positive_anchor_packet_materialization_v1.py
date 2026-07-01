#!/usr/bin/env python3
"""Materialize audit packets for H002 attachment positive-anchor candidates."""

from __future__ import annotations

import csv
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

CANDIDATE_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_candidate_mining_v1"
OUT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_packet_materialization_v1"
SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"

SCHEMA_VERSION = "h002_attachment_independent_positive_anchor_packet_materialization_v1"
EXPECTED_CANDIDATE_STATUS = "h002_attachment_independent_positive_anchor_candidate_mining_v1_ready_mixed_strata"
EXPECTED_CANDIDATE_NEXT = "attachment_independent_positive_anchor_packet_materialization_v1"
STATUS_READY = "h002_attachment_independent_positive_anchor_packet_materialization_v1_ready_for_label_fill"
STATUS_PARTIAL = "h002_attachment_independent_positive_anchor_packet_materialization_v1_partial_needs_gap_audit"
STATUS_ERROR = "h002_attachment_independent_positive_anchor_packet_materialization_v1_errors"
NEXT_TODO_READY = "attachment_independent_positive_anchor_label_fill_v1"
NEXT_TODO_PARTIAL = "attachment_independent_positive_anchor_packet_gap_audit_v1"

IMAGE_LIMIT_PER_OBJECT = 4
THUMB_SIZE = 320

UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)

FORBIDDEN_VISIBLE_PATTERNS = [
    "local_dataset",
    "3rscan",
    "scan_id",
    "subgraph_id",
    "source_id",
    "subject_id",
    "object_id",
    "instance_",
    "prediction_id",
    "directed_pair_id",
    "_hidden",
    "proxy_role",
    "selection_route",
    "cell_id",
    "rank_band",
    "semantic_rank",
    "semantic_score",
    "source_score",
    "p_geom",
    "geometry_status",
    "label_match",
    "matched_predicates",
    "gt_match",
]

VISIBLE_REVIEW_FIELDS = [
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


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


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


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def scan_dir(scan_id: str) -> Path:
    return SCAN_ROOT / scan_id


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


def find_object_images(scan_id: str, object_id: Any, limit: int) -> list[Path]:
    multi_view = scan_dir(scan_id) / "multi_view"
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


def save_thumbnail(source: Path, target: Path) -> bool:
    try:
        with Image.open(source) as image:
            rgb = image.convert("RGB")
            rgb.thumbnail((THUMB_SIZE, THUMB_SIZE))
            target.parent.mkdir(parents=True, exist_ok=True)
            rgb.save(target, format="JPEG", quality=88)
        return True
    except Exception:
        return False


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


def make_contact_sheet(
    subject_images: list[Path],
    object_images: list[Path],
    target: Path,
    subject_label: str,
    object_label: str,
) -> bool:
    cells: list[tuple[str, str, Image.Image]] = []
    for role, label, paths in [
        ("subject", subject_label, subject_images),
        ("object", object_label, object_images),
    ]:
        for idx, path in enumerate(paths, start=1):
            try:
                with Image.open(path) as image:
                    rgb = image.convert("RGB")
                    rgb.thumbnail((THUMB_SIZE, THUMB_SIZE))
                    cells.append((role, f"{label} view {idx}", rgb.copy()))
            except Exception:
                continue
    if not cells:
        return False
    cols = 4
    label_height = 32
    cell_w = THUMB_SIZE
    cell_h = THUMB_SIZE + label_height
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (role, label, image) in enumerate(cells):
        col = idx % cols
        row = idx // cols
        x = col * cell_w
        y = row * cell_h
        draw.text((x + 6, y + 5), f"{role}: {label}"[:44], fill=(0, 0, 0))
        img_x = x + max((cell_w - image.width) // 2, 0)
        sheet.paste(image, (img_x, y + label_height))
    target.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(target, format="JPEG", quality=90)
    return True


def mesh_sources(scan_id: str) -> dict[str, Path | None]:
    root = scan_dir(scan_id)
    candidates = {
        "scene_mesh_obj": root / "mesh.refined.v2.obj",
        "scene_mesh_mtl": root / "mesh.refined.mtl",
        "instance_labels_ply": root / "labels.instances.annotated.v2.ply",
        "aligned_instance_labels_ply": root / "labels.instances.align.annotated.v2.ply",
        "segments_json": root / "semseg.v2.json",
    }
    return {key: path if path.exists() else None for key, path in candidates.items()}


def write_mesh_packet(path: Path, sources: dict[str, Path | None]) -> bool:
    available = [key for key, value in sources.items() if value is not None]
    if not available:
        return False
    display_names = {
        "scene_mesh_obj": "scene mesh geometry file",
        "scene_mesh_mtl": "scene mesh material file",
        "instance_labels_ply": "object label point file",
        "aligned_instance_labels_ply": "aligned object label point file",
        "segments_json": "segment metadata file",
    }
    lines = [
        "# Geometry Evidence Packet",
        "",
        "Mesh and object-level annotation files are available for this candidate.",
        "Detailed internal file references are stored separately from this sheet.",
        "",
        "Available evidence:",
        "",
    ]
    for key in sorted(available):
        lines.append(f"- {display_names.get(key, 'geometry evidence file')}")
    lines.extend(
        [
            "",
            "Boundary: this packet is audit evidence only and is not model input at this stage.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")
    return True


def write_packet_md(
    path: Path,
    visible: dict[str, str],
    subject_images: list[Path],
    object_images: list[Path],
    contact_sheet: Path | None,
    mesh_packet: Path | None,
) -> None:
    lines = [
        "# Attachment Relation Evidence Packet",
        "",
        f"Candidate: `{visible['candidate_id']}`",
        "",
        "Relation:",
        "",
        f"- Subject: `{visible['subject_label']}`",
        f"- Predicate: `{visible['predicate_label']}`",
        f"- Object: `{visible['object_label']}`",
        "",
        "Boundary:",
        "",
        "This packet contains only reviewer-facing audit evidence. Internal provenance is stored separately.",
        "",
    ]
    if contact_sheet is not None:
        lines.extend(["## Contact / Context Sheet", "", f"![contact/context]({contact_sheet.name})", ""])
    if subject_images:
        lines.extend(["## Subject Views", ""])
        for image in subject_images:
            lines.append(f"![subject]({Path('images') / image.name})")
        lines.append("")
    if object_images:
        lines.extend(["## Object Views", ""])
        for image in object_images:
            lines.append(f"![object]({Path('images') / image.name})")
        lines.append("")
    if mesh_packet is not None:
        lines.extend(["## Geometry Packet", "", f"[geometry packet]({mesh_packet.name})", ""])
    lines.extend(
        [
            "## Review",
            "",
            "Decide whether the relation is reliable from the visible/mesh evidence.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def packet_status(subject_count: int, object_count: int, contact_ready: bool, mesh_ready: bool) -> str:
    if subject_count > 0 and object_count > 0 and contact_ready and mesh_ready:
        return "ready"
    if subject_count > 0 or object_count > 0 or mesh_ready:
        return "partial"
    return "missing"


def materialize_packet(
    visible: dict[str, str],
    hidden: dict[str, Any],
    packet_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if packet_dir.exists():
        shutil.rmtree(packet_dir)
    packet_dir.mkdir(parents=True, exist_ok=True)
    (packet_dir / "images").mkdir(exist_ok=True)

    subject_sources = find_object_images(str(hidden["scan_id"]), hidden["subject_id"], IMAGE_LIMIT_PER_OBJECT)
    object_sources = find_object_images(str(hidden["scan_id"]), hidden["object_id"], IMAGE_LIMIT_PER_OBJECT)
    subject_images, subject_hidden = materialize_image_group(subject_sources, packet_dir, "subject")
    object_images, object_hidden = materialize_image_group(object_sources, packet_dir, "object")

    contact_sheet = packet_dir / "contact_context_sheet.jpg"
    contact_ready = make_contact_sheet(
        subject_images,
        object_images,
        contact_sheet,
        visible["subject_label"],
        visible["object_label"],
    )
    contact_path = contact_sheet if contact_ready else None

    mesh_packet = packet_dir / "mesh_packet.md"
    source_mesh = mesh_sources(str(hidden["scan_id"]))
    mesh_ready = write_mesh_packet(mesh_packet, source_mesh)
    mesh_path = mesh_packet if mesh_ready else None

    packet_md = packet_dir / "packet.md"
    write_packet_md(packet_md, visible, subject_images, object_images, contact_path, mesh_path)

    status = packet_status(len(subject_images), len(object_images), contact_ready, mesh_ready)
    public_row = {
        "candidate_id": visible["candidate_id"],
        "packet_request_id": visible["packet_request_id"],
        "subject_label": visible["subject_label"],
        "predicate_label": visible["predicate_label"],
        "object_label": visible["object_label"],
        "reviewer_visible_relation_text": visible["reviewer_visible_relation_text"],
        "packet_status": status,
        "multiview_packet": rel_path(packet_md),
        "contact_or_context_sheet": rel_path(contact_path),
        "mesh_packet": rel_path(mesh_path),
        "review_relation_reliability": "",
        "review_geometry_support": "",
        "review_endpoint_identity": "",
        "review_coverage": "",
        "review_uncertainty": "",
        "review_notes": "",
    }
    hidden_row = {
        **hidden,
        "packet_status_hidden": status,
        "packet_dir_hidden": rel_path(packet_dir),
        "multiview_packet_hidden": rel_path(packet_md),
        "contact_or_context_sheet_hidden": rel_path(contact_path),
        "mesh_packet_hidden": rel_path(mesh_path),
        "subject_image_count_hidden": len(subject_images),
        "object_image_count_hidden": len(object_images),
        "contact_sheet_ready_hidden": contact_ready,
        "mesh_packet_ready_hidden": mesh_ready,
        "subject_image_sources_hidden": subject_hidden,
        "object_image_sources_hidden": object_hidden,
        "mesh_sources_hidden": {key: rel_path(value) for key, value in source_mesh.items() if value is not None},
        "boundary_hidden": "audit evidence only; multi-view and mesh are not model input",
    }
    return public_row, hidden_row


def leakage_scan(path: Path) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if not path.is_file():
        return hits
    text = path.read_text(encoding="utf-8", errors="ignore")
    if UUID_RE.search(text):
        hits.append({"surface": rel_path(path), "hit_type": "uuid_like_scan_id", "pattern": "uuid"})
    lower = text.lower()
    for pattern in FORBIDDEN_VISIBLE_PATTERNS:
        if pattern.lower() in lower:
            hits.append({"surface": rel_path(path), "hit_type": "forbidden_visible_pattern", "pattern": pattern})
    return hits


def validate_inputs(candidate_summary: dict[str, Any], visible_rows: list[dict[str, str]], hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if candidate_summary.get("status") != EXPECTED_CANDIDATE_STATUS:
        errors.append({"error_type": "unexpected_candidate_status", "actual": candidate_summary.get("status")})
    if candidate_summary.get("next_todo") != EXPECTED_CANDIDATE_NEXT:
        errors.append({"error_type": "unexpected_candidate_next_todo", "actual": candidate_summary.get("next_todo")})
    if candidate_summary.get("validation_errors") != 0:
        errors.append({"error_type": "candidate_validation_errors_present", "actual": candidate_summary.get("validation_errors")})
    if len(visible_rows) != 560:
        errors.append({"error_type": "unexpected_visible_rows", "expected": 560, "actual": len(visible_rows)})
    if len(hidden_rows) != 560:
        errors.append({"error_type": "unexpected_hidden_rows", "expected": 560, "actual": len(hidden_rows)})
    visible_ids = {row["candidate_id"] for row in visible_rows}
    hidden_ids = {row["candidate_id"] for row in hidden_rows}
    if visible_ids != hidden_ids:
        errors.append({"error_type": "visible_hidden_candidate_id_mismatch"})
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    lines = [
        "# H002 Attachment Independent Positive Anchor Packet Materialization V1",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"packet_rows = {counts['packet_rows']}",
        f"packet_status_counts = {counts['packet_status_counts']}",
        f"visible_leakage_hits = {counts['visible_leakage_hits']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Coverage",
        "",
        "```text",
        f"subject_image_rows = {counts['subject_image_rows']} / {counts['packet_rows']}",
        f"object_image_rows = {counts['object_image_rows']} / {counts['packet_rows']}",
        f"contact_sheet_rows = {counts['contact_sheet_rows']} / {counts['packet_rows']}",
        f"mesh_packet_rows = {counts['mesh_packet_rows']} / {counts['packet_rows']}",
        f"total_subject_images = {counts['total_subject_images']}",
        f"total_object_images = {counts['total_object_images']}",
        "```",
        "",
        "## Boundary",
        "",
        "- train split only;",
        "- no validation/test usage;",
        "- no posterior training;",
        "- no paper evidence promotion;",
        "- no H001 artifact modification;",
        "- multi-view/mesh is audit evidence only;",
        "- source score/rank/proxy/cell/GT-match fields are hidden from label-facing surfaces.",
        "",
        "## Next",
        "",
        f"`{summary['next_todo']}`",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    candidate_summary = read_json(CANDIDATE_DIR / "summary.json")
    visible_input = read_csv(CANDIDATE_DIR / "visible_review_template.csv")
    hidden_input = read_jsonl(CANDIDATE_DIR / "hidden_manifest.jsonl")
    errors = validate_inputs(candidate_summary, visible_input, hidden_input)

    hidden_by_id = {row["candidate_id"]: row for row in hidden_input}
    packet_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    for visible in visible_input:
        candidate_id = visible["candidate_id"]
        packet_dir = OUT_DIR / "packets" / candidate_id
        public_row, hidden_row = materialize_packet(visible, hidden_by_id[candidate_id], packet_dir)
        packet_rows.append(public_row)
        hidden_rows.append(hidden_row)

    visible_paths = [OUT_DIR / "visible_review_sheet_with_packets.csv"]
    visible_paths.extend(OUT_DIR.glob("packets/*/packet.md"))
    visible_paths.extend(OUT_DIR.glob("packets/*/mesh_packet.md"))
    leakage_hits: list[dict[str, Any]] = []

    non_ready = [row for row in hidden_rows if row["packet_status_hidden"] != "ready"]
    label_ready = [row for row in hidden_rows if row["packet_status_hidden"] == "ready"]
    status_counts = Counter(row["packet_status"] for row in packet_rows)
    query_status_counts = Counter(
        f"{row['query_id']}|{row['packet_status_hidden']}" for row in hidden_rows
    )

    write_csv(OUT_DIR / "visible_review_sheet_with_packets.csv", packet_rows, VISIBLE_REVIEW_FIELDS)
    write_jsonl(OUT_DIR / "packet_manifest.jsonl", packet_rows)
    write_jsonl(OUT_DIR / "materialized_hidden_manifest.jsonl", hidden_rows)
    write_jsonl(OUT_DIR / "label_ready_manifest.jsonl", label_ready)
    write_jsonl(OUT_DIR / "non_ready_packet_rows.jsonl", non_ready)

    for path in visible_paths:
        leakage_hits.extend(leakage_scan(path))
    write_jsonl(OUT_DIR / "visible_leakage_hits.jsonl", leakage_hits)

    if leakage_hits:
        errors.append({"error_type": "visible_leakage_hits_present", "count": len(leakage_hits)})
    if len(packet_rows) != 560:
        errors.append({"error_type": "packet_row_count_mismatch", "actual": len(packet_rows)})

    status = STATUS_ERROR if errors else STATUS_READY if not non_ready else STATUS_PARTIAL
    next_todo = NEXT_TODO_READY if status == STATUS_READY else NEXT_TODO_PARTIAL
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "next_todo": next_todo,
        "validation_errors": len(errors),
        "counts": {
            "packet_rows": len(packet_rows),
            "packet_status_counts": dict(status_counts),
            "query_status_counts": dict(sorted(query_status_counts.items())),
            "label_ready_rows": len(label_ready),
            "non_ready_rows": len(non_ready),
            "subject_image_rows": sum(1 for row in hidden_rows if row["subject_image_count_hidden"] > 0),
            "object_image_rows": sum(1 for row in hidden_rows if row["object_image_count_hidden"] > 0),
            "contact_sheet_rows": sum(1 for row in hidden_rows if row["contact_sheet_ready_hidden"]),
            "mesh_packet_rows": sum(1 for row in hidden_rows if row["mesh_packet_ready_hidden"]),
            "total_subject_images": sum(row["subject_image_count_hidden"] for row in hidden_rows),
            "total_object_images": sum(row["object_image_count_hidden"] for row in hidden_rows),
            "visible_leakage_hits": len(leakage_hits),
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_or_mesh_as_audit_evidence": True,
        },
        "input_paths": {
            "candidate_summary": rel_path(CANDIDATE_DIR / "summary.json"),
            "visible_review_template": rel_path(CANDIDATE_DIR / "visible_review_template.csv"),
            "hidden_manifest": rel_path(CANDIDATE_DIR / "hidden_manifest.jsonl"),
            "scan_root": rel_path(SCAN_ROOT),
        },
        "output_paths": {
            "summary": rel_path(OUT_DIR / "summary.json"),
            "report": rel_path(OUT_DIR / "report.md"),
            "visible_review_sheet_with_packets": rel_path(OUT_DIR / "visible_review_sheet_with_packets.csv"),
            "packet_manifest": rel_path(OUT_DIR / "packet_manifest.jsonl"),
            "materialized_hidden_manifest": rel_path(OUT_DIR / "materialized_hidden_manifest.jsonl"),
            "label_ready_manifest": rel_path(OUT_DIR / "label_ready_manifest.jsonl"),
            "non_ready_packet_rows": rel_path(OUT_DIR / "non_ready_packet_rows.jsonl"),
            "visible_leakage_hits": rel_path(OUT_DIR / "visible_leakage_hits.jsonl"),
        },
    }
    write_jsonl(OUT_DIR / "validation_errors.jsonl", errors)
    write_json(OUT_DIR / "summary.json", summary)
    write_report(OUT_DIR / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"packet_rows={summary['counts']['packet_rows']}")
    print(f"packet_status_counts={summary['counts']['packet_status_counts']}")
    print(f"label_ready_rows={summary['counts']['label_ready_rows']}")
    print(f"visible_leakage_hits={summary['counts']['visible_leakage_hits']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
