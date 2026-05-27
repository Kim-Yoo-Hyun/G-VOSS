#!/usr/bin/env python3
"""Render or preflight Qwen-VL full-source pair crops without model inference."""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


SCHEMA_VERSION = "h001_qwen_vl_full_source_crops_v1"


@dataclass(frozen=True)
class ViewCandidate:
    frame_id: str
    visible_pixels: int
    visibility_ratio: float
    bbox_xyxy: tuple[int, int, int, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/input.jsonl"),
    )
    parser.add_argument(
        "--shards-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/shards.jsonl"),
    )
    parser.add_argument(
        "--views-dir",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime/output/datasets/OpenSG_3RScan/views"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/full_source_crops"),
    )
    parser.add_argument("--mode", choices=["render", "preflight"], default="render")
    parser.add_argument("--shard-id", default="all")
    parser.add_argument("--padding-ratio", type=float, default=0.18)
    parser.add_argument("--min-padding-px", type=int, default=12)
    parser.add_argument("--line-width", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def resolve(repo_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def install_numpy_pickle_compat() -> None:
    try:
        import numpy.core as np_core  # type: ignore
        import numpy.core.multiarray as np_multiarray  # type: ignore
        import numpy.core.numeric as np_numeric  # type: ignore
    except Exception:
        return
    sys.modules.setdefault("numpy._core", np_core)
    sys.modules.setdefault("numpy._core.multiarray", np_multiarray)
    sys.modules.setdefault("numpy._core.numeric", np_numeric)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_line(row: dict[str, Any]) -> str:
    return json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            line = canonical_line(row)
            digest.update(line.encode("utf-8"))
            digest.update(b"\n")
            handle.write(line)
            handle.write("\n")
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_bbox(raw_bbox: Any) -> tuple[int, int, int, int] | None:
    if raw_bbox is None or len(raw_bbox) != 4:
        return None
    x1, y1, x2, y2 = [int(round(float(value))) for value in raw_bbox]
    if x2 < x1:
        x1, x2 = x2, x1
    if y2 < y1:
        y1, y2 = y2, y1
    if x2 == x1:
        x2 += 1
    if y2 == y1:
        y2 += 1
    return (x1, y1, x2, y2)


def load_object_views(path: Path, object_id: int | str) -> list[ViewCandidate]:
    install_numpy_pickle_compat()
    with path.open("rb") as handle:
        payload = pickle.load(handle)
    entries = payload.get(str(object_id), [])
    views: list[ViewCandidate] = []
    for entry in entries:
        if len(entry) < 4:
            continue
        bbox = normalize_bbox(entry[3])
        if bbox is None:
            continue
        views.append(
            ViewCandidate(
                frame_id=str(entry[0]),
                visible_pixels=int(entry[1]),
                visibility_ratio=float(entry[2]),
                bbox_xyxy=bbox,
            )
        )
    return views


def clamp_bbox(bbox: tuple[int, int, int, int], width: int, height: int) -> tuple[int, int, int, int]:
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(width - 1, x1))
    y1 = max(0, min(height - 1, y1))
    x2 = max(x1 + 1, min(width, x2))
    y2 = max(y1 + 1, min(height, y2))
    return (x1, y1, x2, y2)


def union_crop_box(
    subject_bbox: tuple[int, int, int, int],
    object_bbox: tuple[int, int, int, int],
    width: int,
    height: int,
    padding_ratio: float,
    min_padding_px: int,
) -> tuple[int, int, int, int]:
    x1 = min(subject_bbox[0], object_bbox[0])
    y1 = min(subject_bbox[1], object_bbox[1])
    x2 = max(subject_bbox[2], object_bbox[2])
    y2 = max(subject_bbox[3], object_bbox[3])
    span = max(x2 - x1, y2 - y1)
    padding = max(min_padding_px, int(round(span * padding_ratio)))
    return clamp_bbox((x1 - padding, y1 - padding, x2 + padding, y2 + padding), width, height)


def shift_bbox(bbox: tuple[int, int, int, int], crop_box: tuple[int, int, int, int]) -> list[int]:
    return [bbox[0] - crop_box[0], bbox[1] - crop_box[1], bbox[2] - crop_box[0], bbox[3] - crop_box[1]]


def pair_crop(row: dict[str, Any]) -> dict[str, Any]:
    for item in row.get("crop_paths", []):
        if item.get("role") == "pair":
            return item
    raise ValueError(f"missing_pair_crop:{row.get('record_id')}")


def context_crop(row: dict[str, Any]) -> dict[str, Any]:
    for item in row.get("crop_paths", []):
        if item.get("role") == "context":
            return item
    raise ValueError(f"missing_context_crop:{row.get('record_id')}")


def select_rows(input_rows: list[dict[str, Any]], shards: list[dict[str, Any]], shard_id: str) -> list[dict[str, Any]]:
    if shard_id == "all":
        return input_rows
    for shard in shards:
        if shard.get("shard_id") == shard_id:
            return input_rows[int(shard["row_start"]) : int(shard["row_end_exclusive"])]
    raise ValueError(f"unknown_shard_id:{shard_id}")


def representative_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for row in rows:
        path = str(pair_crop(row).get("path"))
        selected.setdefault(path, row)
    return [selected[key] for key in sorted(selected)]


def find_frame_view(views: list[ViewCandidate], frame_id: str) -> ViewCandidate | None:
    candidates = [item for item in views if item.frame_id == frame_id]
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item.visibility_ratio, item.visible_pixels))


def render_one(repo_root: Path, views_dir: Path, row: dict[str, Any], args: argparse.Namespace) -> tuple[dict[str, Any], str | None]:
    pair = pair_crop(row)
    context = context_crop(row)
    pair_path = resolve(repo_root, Path(str(pair["path"])))
    source_image = resolve(repo_root, Path(str(context["path"])))
    if pair_path is None or source_image is None:
        return {}, f"bad_path:{row.get('record_id')}"
    if args.mode == "preflight":
        if not pair_path.exists():
            return {}, f"missing_pair_crop:{relpath(repo_root, pair_path)}"
        return {
            "record_id": row["record_id"],
            "scan_id": row["scan_id"],
            "subgraph_id": row["subgraph_id"],
            "subject_id": row["subject_id"],
            "object_id": row["object_id"],
            "pair_crop_path": relpath(repo_root, pair_path),
            "pair_crop_sha256": sha256_file(pair_path),
            "status": "verified_existing",
        }, None
    if pair_path.exists() and not args.overwrite:
        return {
            "record_id": row["record_id"],
            "scan_id": row["scan_id"],
            "subgraph_id": row["subgraph_id"],
            "subject_id": row["subject_id"],
            "object_id": row["object_id"],
            "pair_crop_path": relpath(repo_root, pair_path),
            "pair_crop_sha256": sha256_file(pair_path),
            "status": "already_existing",
        }, None
    if not source_image.exists():
        return {}, f"missing_source_image:{row.get('record_id')}:{relpath(repo_root, source_image)}"
    frame_id = str(pair.get("frame_id") or context.get("frame_id"))
    object2image_path = views_dir / f"{row['scan_id']}_object2image.pkl"
    if not object2image_path.exists():
        return {}, f"missing_object2image:{row.get('record_id')}:{relpath(repo_root, object2image_path)}"
    subject_views = load_object_views(object2image_path, row["subject_id"])
    object_views = load_object_views(object2image_path, row["object_id"])
    subject_view = find_frame_view(subject_views, frame_id)
    object_view = find_frame_view(object_views, frame_id)
    if subject_view is None:
        return {}, f"missing_subject_frame_view:{row.get('record_id')}:{frame_id}"
    if object_view is None:
        return {}, f"missing_object_frame_view:{row.get('record_id')}:{frame_id}"

    with Image.open(source_image) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        subject_bbox = clamp_bbox(subject_view.bbox_xyxy, width, height)
        object_bbox = clamp_bbox(object_view.bbox_xyxy, width, height)
        crop_box = union_crop_box(
            subject_bbox,
            object_bbox,
            width,
            height,
            padding_ratio=args.padding_ratio,
            min_padding_px=args.min_padding_px,
        )
        crop = rgb.crop(crop_box)
    subject_crop_box = shift_bbox(subject_bbox, crop_box)
    object_crop_box = shift_bbox(object_bbox, crop_box)
    draw = ImageDraw.Draw(crop)
    draw.rectangle(subject_crop_box, outline=(255, 64, 64), width=args.line_width)
    draw.rectangle(object_crop_box, outline=(64, 180, 255), width=args.line_width)
    pair_path.parent.mkdir(parents=True, exist_ok=True)
    crop.save(pair_path, format="PNG")

    warnings: list[str] = []
    if pair.get("subject_bbox_xyxy") != subject_crop_box:
        warnings.append("subject_bbox_differs_from_input")
    if pair.get("object_bbox_xyxy") != object_crop_box:
        warnings.append("object_bbox_differs_from_input")
    return {
        "record_id": row["record_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "object_id": row["object_id"],
        "source_frame": relpath(repo_root, source_image),
        "frame_id": frame_id,
        "pair_crop_path": relpath(repo_root, pair_path),
        "pair_crop_sha256": sha256_file(pair_path),
        "source_bbox_xyxy": {
            "subject": list(subject_bbox),
            "object": list(object_bbox),
            "crop": list(crop_box),
        },
        "crop_bbox_xyxy": {
            "subject": subject_crop_box,
            "object": object_crop_box,
        },
        "status": "rendered",
        "warnings": warnings,
    }, None


def render_report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    lines = [
        "# Qwen-VL Full-Source Crop Rendering",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Scope",
        "",
        f"- mode: `{manifest['mode']}`",
        f"- shard id: `{manifest['shard_id']}`",
        "- No Qwen model load or inference is run.",
        "",
        "## Counts",
        "",
        f"- selected input rows: `{counts['selected_input_rows']}`",
        f"- unique pair crops: `{counts['unique_pair_crops']}`",
        f"- rendered: `{counts['rendered']}`",
        f"- already existing: `{counts['already_existing']}`",
        f"- verified existing: `{counts['verified_existing']}`",
        f"- errors: `{counts['errors']}`",
        "",
        "## Outputs",
        "",
    ]
    for key, value in manifest["outputs"].items():
        lines.append(f"- `{key}`: `{value}`")
    if manifest["validation"]["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- `{item}`" for item in manifest["validation"]["errors"][:80])
    if manifest["validation"]["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- `{item}`" for item in manifest["validation"]["warnings"][:80])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    input_path = resolve(repo_root, args.input_jsonl)
    shards_path = resolve(repo_root, args.shards_jsonl)
    views_dir = resolve(repo_root, args.views_dir)
    out_base = resolve(repo_root, args.out)
    assert input_path is not None
    assert shards_path is not None
    assert views_dir is not None
    assert out_base is not None
    out_dir = out_base / ("all" if args.shard_id == "all" else f"shards/{args.shard_id}")
    out_dir.mkdir(parents=True, exist_ok=True)

    input_rows = load_jsonl(input_path)
    shards = load_jsonl(shards_path)
    selected_rows = select_rows(input_rows, shards, args.shard_id)
    reps = representative_rows(selected_rows)
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    status_counts: Counter[str] = Counter()
    for row in reps:
        try:
            record, error = render_one(repo_root, views_dir, row, args)
        except Exception as exc:  # keep batch audit robust and explicit
            record, error = {}, f"exception:{row.get('record_id')}:{type(exc).__name__}:{exc}"
        if error:
            errors.append(error)
            continue
        records.append(record)
        status_counts[str(record.get("status"))] += 1
        warnings.extend(str(item) for item in record.get("warnings", []))

    records_path = out_dir / "records.jsonl"
    records_sha = write_jsonl(records_path, records)
    status = "full_source_crops_ready_no_inference" if not errors else "blocked_full_source_crop_errors"
    if args.mode == "preflight" and not errors:
        status = "full_source_crop_preflight_ready_no_inference"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "mode": args.mode,
        "shard_id": args.shard_id,
        "runtime_policy": "no_model_download_no_model_load_no_inference",
        "inputs": {
            "input_jsonl": relpath(repo_root, input_path),
            "shards_jsonl": relpath(repo_root, shards_path),
            "views_dir": relpath(repo_root, views_dir),
        },
        "outputs": {
            "records_jsonl": relpath(repo_root, records_path),
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "report": relpath(repo_root, out_dir / "report.md"),
        },
        "counts": {
            "selected_input_rows": len(selected_rows),
            "unique_pair_crops": len(reps),
            "records": len(records),
            "rendered": status_counts["rendered"],
            "already_existing": status_counts["already_existing"],
            "verified_existing": status_counts["verified_existing"],
            "errors": len(errors),
        },
        "hashes": {
            "records_jsonl_sha256": records_sha,
        },
        "rendering_policy": {
            "view_selection": "use the frame_id frozen in full_source_input/input.jsonl",
            "pair_crop": "union of subject/object 2D boxes with fixed padding",
            "annotation": "subject red box, object blue box; no text labels added to image",
            "overwrite": bool(args.overwrite),
        },
        "validation": {
            "errors": errors,
            "warnings": warnings[:200],
            "warnings_truncated": len(warnings) > 200,
        },
        "next_action": (
            "Run preflight after render. Qwen inference remains blocked until crop preflight is ready."
        ),
    }
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(render_report(manifest), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
