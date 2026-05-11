#!/usr/bin/env python3
"""Render Qwen-VL tiny-pilot object-pair crops from 3RScan frames."""

from __future__ import annotations

import argparse
import hashlib
import json
import pickle
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw


MANIFEST_SCHEMA_VERSION = "h001_qwen_vl_pair_crops_v1"


@dataclass(frozen=True)
class ViewCandidate:
    frame_id: str
    visible_pixels: int
    visibility_ratio: float
    bbox_xyxy: tuple[int, int, int, int]


@dataclass(frozen=True)
class PairView:
    subject: ViewCandidate
    object: ViewCandidate
    score: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--tiny-pilot-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/tiny_pilot"),
    )
    parser.add_argument(
        "--views-dir",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/training_repro/output/datasets/OpenSG_3RScan/views"
        ),
    )
    parser.add_argument("--rscan-root", type=Path, default=Path("local_dataset/3RScan/scans"))
    parser.add_argument("--crop-root", type=Path, default=Path("local_dataset/qwen_vl_crops/tiny_pilot"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/crops"),
    )
    parser.add_argument("--padding-ratio", type=float, default=0.18)
    parser.add_argument("--min-padding-px", type=int, default=12)
    parser.add_argument("--line-width", type=int, default=4)
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            handle.write("\n")


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


def best_by_frame(views: list[ViewCandidate]) -> dict[str, ViewCandidate]:
    selected: dict[str, ViewCandidate] = {}
    for view in views:
        current = selected.get(view.frame_id)
        if current is None:
            selected[view.frame_id] = view
            continue
        if (view.visibility_ratio, view.visible_pixels) > (current.visibility_ratio, current.visible_pixels):
            selected[view.frame_id] = view
    return selected


def select_pair_view(subject_views: list[ViewCandidate], object_views: list[ViewCandidate]) -> PairView | None:
    subject_by_frame = best_by_frame(subject_views)
    object_by_frame = best_by_frame(object_views)
    shared_frames = sorted(set(subject_by_frame).intersection(object_by_frame))
    if not shared_frames:
        return None
    pairs: list[PairView] = []
    for frame_id in shared_frames:
        subject = subject_by_frame[frame_id]
        obj = object_by_frame[frame_id]
        score = (
            subject.visibility_ratio
            + obj.visibility_ratio
            + 0.000001 * (subject.visible_pixels + obj.visible_pixels)
        )
        pairs.append(PairView(subject=subject, object=obj, score=score))
    return max(pairs, key=lambda item: (item.score, item.subject.visible_pixels + item.object.visible_pixels))


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


def replace_crop_paths(row: dict[str, Any], pair_path: str, frame_path: str, frame_id: str, subject_box: list[int], object_box: list[int]) -> dict[str, Any]:
    updated = dict(row)
    crop_paths: list[dict[str, Any]] = []
    for crop in row["crop_paths"]:
        item = dict(crop)
        if item["role"] == "pair":
            item["path"] = pair_path
            item["view_id"] = "pair_view_000"
            item["frame_id"] = frame_id
            item["subject_bbox_xyxy"] = subject_box
            item["object_bbox_xyxy"] = object_box
        elif item["role"] == "context":
            item["path"] = frame_path
            item["view_id"] = "context_frame_000"
            item["frame_id"] = frame_id
            item["subject_bbox_xyxy"] = None
            item["object_bbox_xyxy"] = None
        crop_paths.append(item)
    updated["crop_paths"] = crop_paths
    return updated


def render_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Qwen-VL Pair Crop Rendering",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Scope",
        "",
        "This renders tiny-pilot object-pair crops only. It does not download a model or run Qwen-VL inference.",
        "",
        "## Counts",
        "",
        f"- input rows: `{manifest['counts']['input_rows']}`",
        f"- rendered crops: `{manifest['counts']['rendered_crops']}`",
        f"- updated input rows: `{manifest['counts']['updated_input_rows']}`",
        f"- rows without shared view: `{manifest['counts']['no_shared_view']}`",
        f"- missing image rows: `{manifest['counts']['missing_image']}`",
        "",
        "## Outputs",
        "",
    ]
    for name, path in manifest["outputs"].items():
        lines.append(f"- `{name}`: `{path}`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "These crops are runtime input artifacts only. They are not Qwen-VL prediction or metric evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    tiny_pilot_dir = resolve(repo_root, args.tiny_pilot_dir)
    views_dir = resolve(repo_root, args.views_dir)
    rscan_root = resolve(repo_root, args.rscan_root)
    crop_root = resolve(repo_root, args.crop_root)
    out_dir = resolve(repo_root, args.out)
    assert tiny_pilot_dir is not None
    assert views_dir is not None
    assert rscan_root is not None
    assert crop_root is not None
    assert out_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True)
    crop_root.mkdir(parents=True, exist_ok=True)

    input_path = tiny_pilot_dir / "input.jsonl"
    tiny_manifest = load_json(tiny_pilot_dir / "manifest.json")
    input_sha_before = sha256_file(input_path)
    rows = load_jsonl(input_path)
    updated_rows: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    warnings: list[str] = []
    counters: Counter[str] = Counter()

    if tiny_manifest.get("status") != "tiny_pilot_scope_ready_no_model_runtime":
        errors.append(f"tiny_pilot_not_ready:{tiny_manifest.get('status')}")

    for row in rows:
        counters["input_rows"] += 1
        scan_id = str(row["scan_id"])
        subject_id = row["subject_id"]
        object_id = row["object_id"]
        pair_entries = [item for item in row["crop_paths"] if item["role"] == "pair"]
        if not pair_entries:
            errors.append(f"missing_pair_entry:{row['record_id']}")
            updated_rows.append(row)
            continue

        object2image_path = views_dir / f"{scan_id}_object2image.pkl"
        if not object2image_path.exists():
            errors.append(f"missing_object2image:{scan_id}")
            updated_rows.append(row)
            continue

        subject_views = load_object_views(object2image_path, subject_id)
        object_views = load_object_views(object2image_path, object_id)
        if not subject_views:
            errors.append(f"missing_subject_views:{row['record_id']}")
            updated_rows.append(row)
            continue
        if not object_views:
            errors.append(f"missing_object_views:{row['record_id']}")
            updated_rows.append(row)
            continue

        selected = select_pair_view(subject_views, object_views)
        if selected is None:
            counters["no_shared_view"] += 1
            errors.append(f"no_shared_view:{row['record_id']}")
            updated_rows.append(row)
            continue

        source_image = rscan_root / scan_id / "sequence" / selected.subject.frame_id
        if not source_image.exists():
            counters["missing_image"] += 1
            errors.append(f"missing_image:{row['record_id']}:{relpath(repo_root, source_image)}")
            updated_rows.append(row)
            continue

        with Image.open(source_image) as image:
            rgb = image.convert("RGB")
            width, height = rgb.size
            subject_bbox = clamp_bbox(selected.subject.bbox_xyxy, width, height)
            object_bbox = clamp_bbox(selected.object.bbox_xyxy, width, height)
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

        pair_rel_path = Path(pair_entries[0]["path"])
        pair_output = resolve(repo_root, pair_rel_path)
        if pair_output is None:
            errors.append(f"invalid_pair_output:{row['record_id']}")
            updated_rows.append(row)
            continue
        pair_output.parent.mkdir(parents=True, exist_ok=True)
        crop.save(pair_output, format="PNG")

        updated = replace_crop_paths(
            row=row,
            pair_path=relpath(repo_root, pair_output) or str(pair_output),
            frame_path=relpath(repo_root, source_image) or str(source_image),
            frame_id=selected.subject.frame_id,
            subject_box=subject_crop_box,
            object_box=object_crop_box,
        )
        updated_rows.append(updated)
        counters["rendered_crops"] += 1
        records.append(
            {
                "record_id": row["record_id"],
                "scan_id": scan_id,
                "subgraph_id": row["subgraph_id"],
                "subject_id": subject_id,
                "object_id": object_id,
                "predicate_family": row["predicate_family"],
                "source_frame": relpath(repo_root, source_image),
                "pair_crop_path": relpath(repo_root, pair_output),
                "pair_crop_sha256": sha256_file(pair_output),
                "source_bbox_xyxy": {
                    "subject": list(subject_bbox),
                    "object": list(object_bbox),
                    "crop": list(crop_box),
                },
                "crop_bbox_xyxy": {
                    "subject": subject_crop_box,
                    "object": object_crop_box,
                },
                "visibility": {
                    "subject_pixels": selected.subject.visible_pixels,
                    "object_pixels": selected.object.visible_pixels,
                    "subject_ratio": selected.subject.visibility_ratio,
                    "object_ratio": selected.object.visibility_ratio,
                    "shared_frame_score": selected.score,
                },
                "render_status": "rendered",
            }
        )

    if len(updated_rows) != len(rows):
        errors.append(f"updated_rows:{len(updated_rows)} expected:{len(rows)}")

    write_jsonl(input_path, updated_rows)
    input_sha_after = sha256_file(input_path)
    write_jsonl(out_dir / "records.jsonl", records)
    status = "pair_crops_rendered_no_model_download_no_inference" if not errors else "blocked_pair_crop_render_errors"
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "runtime_policy": "no_model_download_no_inference",
        "inputs": {
            "tiny_pilot_dir": relpath(repo_root, tiny_pilot_dir),
            "input_jsonl": relpath(repo_root, input_path),
            "views_dir": relpath(repo_root, views_dir),
            "rscan_root": relpath(repo_root, rscan_root),
        },
        "outputs": {
            "crop_root": relpath(repo_root, crop_root),
            "records_jsonl": relpath(repo_root, out_dir / "records.jsonl"),
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "report": relpath(repo_root, out_dir / "report.md"),
            "updated_input_jsonl": relpath(repo_root, input_path),
        },
        "counts": {
            "input_rows": len(rows),
            "updated_input_rows": len(updated_rows),
            "rendered_crops": counters["rendered_crops"],
            "no_shared_view": counters["no_shared_view"],
            "missing_image": counters["missing_image"],
            "family_counts": dict(sorted(Counter(row["predicate_family"] for row in rows).items())),
        },
        "input_sha256": {
            "before": input_sha_before,
            "after": input_sha_after,
            "changed": input_sha_before != input_sha_after,
        },
        "rendering_policy": {
            "view_selection": "choose shared frame maximizing subject/object visibility ratio and visible pixels",
            "pair_crop": "union of subject/object 2D boxes with fixed padding",
            "annotation": "subject red box, object blue box; no text labels added to image",
        },
        "validation": {"errors": errors, "warnings": warnings},
        "next_action": "Run qwen_vl_tiny_pilot_validator and qwen_vl_runtime_plan after rendering.",
    }
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(render_report(manifest), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
