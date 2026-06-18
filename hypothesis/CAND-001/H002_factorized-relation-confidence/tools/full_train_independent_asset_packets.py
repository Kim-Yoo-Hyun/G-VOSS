#!/usr/bin/env python3
"""Generate blind evidence packets for H002 full-train independent labels."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
PROTOCOL_ROOT = RGA_ROOT / "independent_label_protocol"
DEFAULT_ASSET_REQUESTS = PROTOCOL_ROOT / "asset_request_manifest.jsonl"
DEFAULT_PROTOCOL_SUMMARY = PROTOCOL_ROOT / "summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_asset_packets"
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"

BLIND_SHEETS = [
    "blind_all_sheet.tsv",
    "blind_priority_sheet.tsv",
    "blind_support_contact_sheet.tsv",
    "blind_relative_vertical_sheet.tsv",
    "blind_proximity_sheet.tsv",
]

FORBIDDEN_LABEL_SURFACE_SUBSTRINGS = [
    "score",
    "rank",
    "p_geom",
    "geometry_status",
    "h001_verification",
    "queue",
    "label_match",
    "proposed",
    "role",
    "candidate_axis",
    "prediction_id",
    "final_controlled",
    "failure_taxonomy",
    "matched_gt",
    "matched_predicate",
    "bucket",
    "machine_hint",
    "reason_code",
    "semantic",
    "consistency",
    "disagreement",
    "underconfidence",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--asset-requests", type=Path, default=DEFAULT_ASSET_REQUESTS)
    parser.add_argument("--protocol-summary", type=Path, default=DEFAULT_PROTOCOL_SUMMARY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
    parser.add_argument("--images-per-object", type=int, default=4)
    parser.add_argument("--thumb-size", type=int, default=320)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


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


def read_tsv(path: Path) -> list[dict[str, Any]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def scan_dir(scan_root: Path, scan_id: str) -> Path:
    return as_abs(scan_root) / scan_id


def unique_paths(paths: list[Path]) -> list[Path]:
    seen = set()
    output = []
    for path in paths:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        output.append(path)
    return output


def find_object_images(scan_root: Path, scan_id: str, object_id: Any, limit: int) -> list[Path]:
    multi_view = scan_dir(scan_root, scan_id) / "multi_view"
    if not multi_view.exists():
        return []
    object_id_text = str(object_id)
    cropped = sorted(multi_view.glob(f"instance_{object_id_text}_class_*_croped_view*_A.jpg"))
    direct = [
        path
        for path in sorted(multi_view.glob(f"instance_{object_id_text}_class_*_view*_A.jpg"))
        if "_croped_" not in path.name
    ]
    return unique_paths(cropped + direct)[:limit]


def save_thumbnail(src: Path, dest: Path, thumb_size: int) -> bool:
    try:
        with Image.open(src) as image:
            rgb = image.convert("RGB")
            rgb.thumbnail((thumb_size, thumb_size))
            dest.parent.mkdir(parents=True, exist_ok=True)
            rgb.save(dest, format="JPEG", quality=88)
        return True
    except Exception:
        return False


def materialize_images(
    src_paths: list[Path],
    packet_dir: Path,
    prefix: str,
    thumb_size: int,
) -> list[Path]:
    outputs = []
    for index, src in enumerate(src_paths, start=1):
        dest = packet_dir / f"{prefix}_{index:02d}.jpg"
        if save_thumbnail(src, dest, thumb_size):
            outputs.append(dest)
    return outputs


def make_contact_sheet(
    subject_images: list[Path],
    object_images: list[Path],
    dest: Path,
    *,
    subject_label: str,
    object_label: str,
    thumb_size: int,
) -> bool:
    image_paths = [("subject", path) for path in subject_images] + [("object", path) for path in object_images]
    if not image_paths:
        return False
    cells = []
    for role, path in image_paths:
        try:
            with Image.open(path) as image:
                rgb = image.convert("RGB")
                rgb.thumbnail((thumb_size, thumb_size))
                cells.append((role, path.name, rgb.copy()))
        except Exception:
            continue
    if not cells:
        return False
    cols = 4
    label_height = 34
    cell_w = thumb_size
    cell_h = thumb_size + label_height
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (role, filename, image) in enumerate(cells):
        col = idx % cols
        row = idx // cols
        x = col * cell_w
        y = row * cell_h
        label = f"{role}: {subject_label if role == 'subject' else object_label}"
        draw.text((x + 6, y + 4), label[:42], fill=(0, 0, 0))
        draw.text((x + 6, y + 18), filename[:42], fill=(80, 80, 80))
        img_x = x + max((cell_w - image.width) // 2, 0)
        sheet.paste(image, (img_x, y + label_height))
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(dest, format="JPEG", quality=90)
    return True


def mesh_sources(scan_root: Path, scan_id: str) -> dict[str, Path | None]:
    root = scan_dir(scan_root, scan_id)
    candidates = {
        "scene_mesh_obj": root / "mesh.refined.v2.obj",
        "scene_mesh_mtl": root / "mesh.refined.mtl",
        "instance_labels_ply": root / "labels.instances.annotated.v2.ply",
        "aligned_instance_labels_ply": root / "labels.instances.align.annotated.v2.ply",
        "segments_json": root / "semseg.v2.json",
    }
    return {key: path if path.exists() else None for key, path in candidates.items()}


def write_mesh_packet(path: Path, row: dict[str, Any], sources: dict[str, Path | None]) -> bool:
    available = {key: value for key, value in sources.items() if value is not None}
    if not available:
        return False
    lines = [
        "# Mesh Evidence Packet",
        "",
        f"Blind review id: `{row['blind_review_id']}`",
        f"Scan: `{row['scan_id']}`",
        "",
        "Relation:",
        "",
        f"- Subject: `{row['subject_label']}` (`{row['subject_id']}`)",
        f"- Predicate: `{row['predicate_label']}`",
        f"- Object: `{row['object_label']}` (`{row['object_id']}`)",
        "",
        "Files:",
        "",
    ]
    for key, value in sorted(available.items()):
        lines.append(f"- `{key}`: `{rel_path(value)}`")
    lines.extend(
        [
            "",
            "Boundary:",
            "",
            "These files are audit support only. They are not model input in this stage.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return True


def write_packet_md(
    path: Path,
    row: dict[str, Any],
    subject_images: list[Path],
    object_images: list[Path],
    contact_sheet: Path | None,
    mesh_packet: Path | None,
) -> None:
    lines = [
        "# Independent Evidence Packet",
        "",
        f"Blind review id: `{row['blind_review_id']}`",
        f"Scan: `{row['scan_id']}`",
        f"Scene context: `{row['subgraph_id']}`",
        "",
        "Relation:",
        "",
        f"- Subject: `{row['subject_label']}` (`{row['subject_id']}`)",
        f"- Predicate: `{row['predicate_label']}`",
        f"- Object: `{row['object_label']}` (`{row['object_id']}`)",
        "",
        "Boundary:",
        "",
        "This packet contains audit evidence only. It does not expose source ordering, target-construction metadata, or model confidence fields.",
        "",
    ]
    if contact_sheet is not None:
        lines.extend(["Contact/context sheet:", "", f"![contact/context]({contact_sheet.name})", ""])
    if subject_images:
        lines.extend(["Subject views:", ""])
        for image in subject_images:
            lines.append(f"![subject]({image.name})")
        lines.append("")
    if object_images:
        lines.extend(["Object views:", ""])
        for image in object_images:
            lines.append(f"![object]({image.name})")
        lines.append("")
    if mesh_packet is not None:
        lines.extend(["Geometry files:", "", f"[mesh packet]({mesh_packet.name})", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def packet_status(subject_count: int, object_count: int, contact_ready: bool, mesh_ready: bool) -> str:
    if subject_count > 0 and object_count > 0 and contact_ready and mesh_ready:
        return "ready"
    if subject_count > 0 or object_count > 0 or mesh_ready:
        return "partial"
    return "missing"


def generate_packet(row: dict[str, Any], args: argparse.Namespace, output_dir: Path) -> dict[str, Any]:
    packet_dir = output_dir / "packets" / str(row["blind_review_id"])
    if packet_dir.exists():
        shutil.rmtree(packet_dir)
    packet_dir.mkdir(parents=True, exist_ok=True)

    subject_src = find_object_images(args.scan_root, str(row["scan_id"]), row["subject_id"], args.images_per_object)
    object_src = find_object_images(args.scan_root, str(row["scan_id"]), row["object_id"], args.images_per_object)
    subject_images = materialize_images(subject_src, packet_dir, "subject", args.thumb_size)
    object_images = materialize_images(object_src, packet_dir, "object", args.thumb_size)

    contact_sheet = packet_dir / "contact_context_sheet.jpg"
    contact_ready = make_contact_sheet(
        subject_images,
        object_images,
        contact_sheet,
        subject_label=str(row["subject_label"]),
        object_label=str(row["object_label"]),
        thumb_size=args.thumb_size,
    )
    contact_path = contact_sheet if contact_ready else None

    mesh_packet = packet_dir / "mesh_packet.md"
    mesh_ready = write_mesh_packet(mesh_packet, row, mesh_sources(args.scan_root, str(row["scan_id"])))
    mesh_path = mesh_packet if mesh_ready else None

    packet_md = packet_dir / "packet.md"
    write_packet_md(packet_md, row, subject_images, object_images, contact_path, mesh_path)
    status = packet_status(len(subject_images), len(object_images), contact_ready, mesh_ready)

    return {
        "schema_version": "h002_full_train_independent_asset_packet_v0",
        "blind_review_id": row["blind_review_id"],
        "asset_request_id": row["asset_request_id"],
        "scan_id": row["scan_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "packet_status": status,
        "subject_image_count": len(subject_images),
        "object_image_count": len(object_images),
        "contact_sheet_ready": contact_ready,
        "mesh_packet_ready": mesh_ready,
        "multiview_packet": rel_path(packet_md),
        "pointcloud_or_mesh_packet": rel_path(mesh_path),
        "contact_or_context_sheet": rel_path(contact_path),
        "label_surface_safe": True,
        "boundary": "Audit evidence only. Multi-view is not model input.",
    }


def update_blind_sheets(protocol_dir: Path, output_dir: Path, packet_by_id: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    sheet_outputs = []
    for sheet_name in BLIND_SHEETS:
        input_path = protocol_dir / sheet_name
        if not input_path.exists():
            continue
        rows = read_tsv(input_path)
        for row in rows:
            packet = packet_by_id.get(str(row.get("blind_review_id")))
            if not packet:
                continue
            row["evidence_packet_status"] = packet["packet_status"]
            row["multiview_packet"] = packet["multiview_packet"]
            row["pointcloud_or_mesh_packet"] = packet["pointcloud_or_mesh_packet"]
            row["contact_or_context_sheet"] = packet["contact_or_context_sheet"]
        output_path = output_dir / sheet_name.replace(".tsv", "_with_packets.tsv")
        write_tsv(output_path, rows)
        counts = Counter(row.get("evidence_packet_status") for row in rows)
        sheet_outputs.append(
            {
                "source_sheet": rel_path(input_path),
                "output_sheet": rel_path(output_path),
                "rows": len(rows),
                "status_counts": dict(sorted(counts.items())),
            }
        )
    return sheet_outputs


def label_surface_leakage_audit(packet_rows: list[dict[str, Any]], sheet_outputs: list[dict[str, Any]], output_dir: Path) -> dict[str, Any]:
    hits = []
    for packet in packet_rows[: min(len(packet_rows), 30)]:
        packet_path = as_abs(Path(packet["multiview_packet"]))
        packet_paths = [packet_path]
        mesh_path = as_abs(Path(packet["pointcloud_or_mesh_packet"])) if packet["pointcloud_or_mesh_packet"] else None
        if mesh_path is not None:
            packet_paths.append(mesh_path)
        for current_path in packet_paths:
            text = current_path.read_text(encoding="utf-8") if current_path.exists() else ""
            lower = text.lower()
            for token in FORBIDDEN_LABEL_SURFACE_SUBSTRINGS:
                if token in lower:
                    hits.append({"surface": rel_path(current_path), "forbidden_substring": token})
    for sheet in sheet_outputs:
        rows = read_tsv(Path(sheet["output_sheet"]))
        if not rows:
            continue
        for field in rows[0]:
            lower = field.lower()
            for token in FORBIDDEN_LABEL_SURFACE_SUBSTRINGS:
                if token in lower:
                    hits.append({"surface": sheet["output_sheet"], "field": field, "forbidden_substring": token})
    return {
        "status": "pass" if not hits else "fail",
        "sampled_packet_text_count": min(len(packet_rows), 30),
        "forbidden_substrings": FORBIDDEN_LABEL_SURFACE_SUBSTRINGS,
        "hits": hits,
        "output_dir": rel_path(output_dir),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Full Train Independent Asset Packets",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage artifact.",
        "- No validation/test rows are used.",
        "- Multi-view/mesh/point-cloud evidence is audit support only.",
        "- No posterior is trained in this stage.",
        "- Original image filenames are not exposed in label-facing packets.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Packet Counts",
        "",
        "| Status | Rows |",
        "| --- | ---: |",
    ]
    for key, value in summary["packet_status_counts"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Coverage",
            "",
            f"- subject images linked: {summary['coverage']['subject_image_rows']} / {summary['coverage']['rows']}",
            f"- object images linked: {summary['coverage']['object_image_rows']} / {summary['coverage']['rows']}",
            f"- contact/context sheets ready: {summary['coverage']['contact_sheet_rows']} / {summary['coverage']['rows']}",
            f"- mesh packets ready: {summary['coverage']['mesh_packet_rows']} / {summary['coverage']['rows']}",
            "",
            "## Label Surface",
            "",
            f"Leakage audit: `{summary['label_surface_leakage_audit']['status']}`",
            "",
            "## Updated Sheets",
            "",
            "| Sheet | Rows | Status Counts |",
            "| --- | ---: | --- |",
        ]
    )
    for sheet in summary["updated_sheets"]:
        lines.append(f"| `{sheet['output_sheet']}` | {sheet['rows']} | `{sheet['status_counts']}` |")
    lines.extend(
        [
            "",
            "## Non-Ready Rows",
            "",
            f"`{summary['non_ready_packet_rows']}`",
            "",
        ]
    )
    lines.extend(
        [
            "",
            "## Next TODO",
            "",
            summary["next_todo"],
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    asset_requests = read_jsonl(args.asset_requests)
    protocol_summary = read_json(args.protocol_summary) if as_abs(args.protocol_summary).exists() else {}
    output_dir = as_abs(args.output_dir)
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    packet_rows = [generate_packet(row, args, output_dir) for row in asset_requests]
    packet_by_id = {str(row["blind_review_id"]): row for row in packet_rows}
    write_jsonl(output_dir / "packet_manifest.jsonl", packet_rows)
    non_ready_rows = [row for row in packet_rows if row["packet_status"] != "ready"]
    write_jsonl(output_dir / "non_ready_packet_rows.jsonl", non_ready_rows)
    updated_sheets = update_blind_sheets(PROTOCOL_ROOT, output_dir, packet_by_id)
    leakage = label_surface_leakage_audit(packet_rows, updated_sheets, output_dir)

    status_counts = Counter(row["packet_status"] for row in packet_rows)
    family_status_counts = Counter((row["predicate_family"], row["packet_status"]) for row in packet_rows)
    ready_rows = status_counts.get("ready", 0)
    partial_rows = status_counts.get("partial", 0)
    missing_rows = status_counts.get("missing", 0)
    leakage_pass = leakage["status"] == "pass"
    status = (
        "full_train_independent_asset_packets_ready"
        if ready_rows == len(packet_rows) and leakage_pass
        else "full_train_independent_asset_packets_partial"
        if ready_rows + partial_rows > 0 and leakage_pass
        else "full_train_independent_asset_packets_blocked"
    )
    next_todo = (
        "full_train_independent_label_readiness: verify packet-filled blind sheets and prepare label ingestion."
        if status == "full_train_independent_asset_packets_ready"
        else "full_train_asset_packet_gap_audit: inspect missing/partial packet rows before label fill."
    )
    coverage = {
        "rows": len(packet_rows),
        "subject_image_rows": sum(1 for row in packet_rows if row["subject_image_count"] > 0),
        "object_image_rows": sum(1 for row in packet_rows if row["object_image_count"] > 0),
        "contact_sheet_rows": sum(1 for row in packet_rows if row["contact_sheet_ready"]),
        "mesh_packet_rows": sum(1 for row in packet_rows if row["mesh_packet_ready"]),
    }
    summary = {
        "schema_version": "h002_full_train_independent_asset_packets_summary_v0",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "asset_requests": rel_path(args.asset_requests),
            "protocol_summary": rel_path(args.protocol_summary),
            "scan_root": rel_path(args.scan_root),
        },
        "output_dir": rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "vmv_model_input_allowed": False,
            "asset_role": "audit_evidence_only",
            "source_protocol_status": protocol_summary.get("status"),
        },
        "packet_rows": len(packet_rows),
        "packet_status_counts": dict(sorted(status_counts.items())),
        "missing_rows": missing_rows,
        "coverage": coverage,
        "family_status_counts": {
            f"{family}:{status_key}": value
            for (family, status_key), value in sorted(family_status_counts.items())
        },
        "updated_sheets": updated_sheets,
        "packet_manifest": rel_path(output_dir / "packet_manifest.jsonl"),
        "non_ready_packet_rows": rel_path(output_dir / "non_ready_packet_rows.jsonl"),
        "label_surface_leakage_audit": leakage,
        "next_todo": next_todo,
    }
    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    print(
        f"status={summary['status']} rows={summary['packet_rows']} "
        f"status_counts={summary['packet_status_counts']} "
        f"leakage={summary['label_surface_leakage_audit']['status']} "
        f"validation_used={summary['boundary']['validation_usage']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
