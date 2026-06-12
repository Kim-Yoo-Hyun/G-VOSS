#!/usr/bin/env python3
"""Build the Qwen-VL full-source input universe without running inference."""

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

from PIL import Image


SCHEMA_VERSION = "h001_qwen_vl_full_source_input_v1"
INPUT_SCHEMA_VERSION = "h001_qwen_vl_input_v2"
SPLIT_NAME = "h001_validation_hardened"
TARGET_FAMILIES = ["support_contact", "proximity", "relative_vertical"]
EXPECTED_SCANS = 127
EXPECTED_CONTEXTS = 388
EXPECTED_DIRECTED_PAIRS = 25916
EXPECTED_ALL_PAIR_FAMILY_ROWS = 77748
EXPECTED_IN_SCOPE_GT = 2545


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
        "--contract-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl"),
    )
    parser.add_argument(
        "--subset-json",
        type=Path,
        default=Path("local_dataset/3DSSG_subset/relationships_validation.json"),
    )
    parser.add_argument(
        "--selected-scans",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/subset/"
            "h001_validation_hardened/scans.txt"
        ),
    )
    parser.add_argument(
        "--views-dir",
        type=Path,
        default=Path(
            "local_dataset/Open3DSG_staged/h001_runtime/output/datasets/OpenSG_3RScan/views"
        ),
    )
    parser.add_argument("--rscan-root", type=Path, default=Path("local_dataset/3RScan/scans"))
    parser.add_argument("--crop-root", type=Path, default=Path("local_dataset/qwen_vl_crops/full_source"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/full_source_input"),
    )
    parser.add_argument(
        "--runtime-output-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime"),
    )
    parser.add_argument("--split-name", default=SPLIT_NAME)
    parser.add_argument("--expected-scans", type=int, default=EXPECTED_SCANS)
    parser.add_argument("--expected-contexts", type=int, default=EXPECTED_CONTEXTS)
    parser.add_argument("--expected-directed-pairs", type=int, default=EXPECTED_DIRECTED_PAIRS)
    parser.add_argument("--expected-universe-rows", type=int, default=EXPECTED_ALL_PAIR_FAMILY_ROWS)
    parser.add_argument("--expected-in-scope-gt", type=int, default=EXPECTED_IN_SCOPE_GT)
    parser.add_argument("--shard-id-prefix", default="qwen_full_source_shard")
    parser.add_argument("--shard-size", type=int, default=250)
    parser.add_argument("--padding-ratio", type=float, default=0.18)
    parser.add_argument("--min-padding-px", type=int, default=12)
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


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


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


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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


def install_numpy_pickle_compat() -> None:
    try:
        import numpy as _np  # type: ignore
        import numpy.core as _np_core  # type: ignore
        import numpy.core.multiarray as _np_multiarray  # type: ignore
        import numpy.core.numeric as _np_numeric  # type: ignore
    except Exception:
        return
    sys.modules.setdefault("numpy._core", _np_core)
    sys.modules.setdefault("numpy._core.multiarray", _np_multiarray)
    sys.modules.setdefault("numpy._core.numeric", _np_numeric)


def best_by_frame(views: list[ViewCandidate]) -> dict[str, ViewCandidate]:
    selected: dict[str, ViewCandidate] = {}
    for view in views:
        current = selected.get(view.frame_id)
        if current is None or (view.visibility_ratio, view.visible_pixels) > (
            current.visibility_ratio,
            current.visible_pixels,
        ):
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
        score = subject.visibility_ratio + obj.visibility_ratio + 0.000001 * (
            subject.visible_pixels + obj.visible_pixels
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


def sanitize(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def image_size(path: Path, cache: dict[Path, tuple[int, int]]) -> tuple[int, int] | None:
    if path in cache:
        return cache[path]
    try:
        with Image.open(path) as image:
            size = image.size
    except Exception:
        return None
    cache[path] = size
    return size


def build_record_id(split_name: str, subgraph_id: str, subject_id: int, object_id: int, family: str) -> str:
    return f"qwen_vl:{split_name}:{subgraph_id}:{subject_id}:{object_id}:{family}"


def build_pair_crop_path(crop_root: Path, subgraph_id: str, subject_id: int, object_id: int) -> Path:
    return crop_root / sanitize(subgraph_id) / f"{subject_id}_{object_id}" / "pair_view_000.png"


def load_contexts(subset_json: Path, selected_scans: Path) -> list[dict[str, Any]]:
    selected = set(read_lines(selected_scans))
    subset = load_json(subset_json)
    contexts: list[dict[str, Any]] = []
    for entry in subset.get("scans", []):
        scan_id = str(entry.get("scan"))
        if scan_id not in selected:
            continue
        split_id = int(entry.get("split"))
        objects = {int(key): str(value) for key, value in entry.get("objects", {}).items()}
        contexts.append(
            {
                "scan_id": scan_id,
                "subset_split_id": split_id,
                "subgraph_id": f"{scan_id}_{split_id}",
                "objects": objects,
            }
        )
    contexts.sort(key=lambda item: item["subgraph_id"])
    return contexts


def family_map(contract_dir: Path) -> dict[str, list[str]]:
    contract = load_json(contract_dir / "adapter_contract.json")
    mapping = contract["input_schema"]["predicate_family_map"]
    return {family: list(mapping[family]) for family in TARGET_FAMILIES}


def build_input_row(
    repo_root: Path,
    crop_root: Path,
    context: dict[str, Any],
    subject_id: int,
    object_id: int,
    family: str,
    candidate_predicates: list[str],
    selected: PairView,
    source_image: Path,
    subject_crop_box: list[int],
    object_crop_box: list[int],
    split_name: str,
) -> dict[str, Any]:
    subgraph_id = str(context["subgraph_id"])
    pair_path = build_pair_crop_path(crop_root, subgraph_id, subject_id, object_id)
    return {
        "schema_version": INPUT_SCHEMA_VERSION,
        "record_id": build_record_id(split_name, subgraph_id, subject_id, object_id, family),
        "scan_id": context["scan_id"],
        "subgraph_id": subgraph_id,
        "split": "held_out",
        "subject_id": subject_id,
        "object_id": object_id,
        "subject_label": context["objects"][subject_id],
        "object_label": context["objects"][object_id],
        "predicate_family": family,
        "candidate_predicates": candidate_predicates,
        "view_set_id": f"qwen_full:{subgraph_id}:{subject_id}:{object_id}:pair_view_000",
        "crop_paths": [
            {
                "path": relpath(repo_root, pair_path),
                "role": "pair",
                "view_id": "pair_view_000",
                "frame_id": selected.subject.frame_id,
                "subject_bbox_xyxy": subject_crop_box,
                "object_bbox_xyxy": object_crop_box,
            },
            {
                "path": relpath(repo_root, source_image),
                "role": "context",
                "view_id": "context_frame_000",
                "frame_id": selected.subject.frame_id,
                "subject_bbox_xyxy": None,
                "object_bbox_xyxy": None,
            },
        ],
        "geometry_summary": None,
    }


def build_shards(
    repo_root: Path,
    input_path: Path,
    output_root: Path,
    row_count: int,
    shard_size: int,
    shard_id_prefix: str,
) -> list[dict[str, Any]]:
    shards: list[dict[str, Any]] = []
    for shard_index, start in enumerate(range(0, row_count, shard_size)):
        end = min(start + shard_size, row_count)
        shard_id = f"{shard_id_prefix}_{shard_index:04d}"
        shards.append(
            {
                "shard_id": shard_id,
                "row_start": start,
                "row_end_exclusive": end,
                "row_count": end - start,
                "input_jsonl": relpath(repo_root, input_path),
                "raw_response_jsonl": relpath(repo_root, output_root / "raw_response" / f"{shard_id}.jsonl"),
                "predictions_jsonl": relpath(repo_root, output_root / "predictions" / f"{shard_id}.jsonl"),
                "log_template": f"logs/qwen_vl_infer_{shard_id}_${{ts}}.log",
                "exit_template": f"logs/qwen_vl_infer_{shard_id}_${{ts}}.exit",
            }
        )
    return shards


def report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    lines = [
        "# Qwen-VL Full-Source Input Audit",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Scope",
        "",
        "- Role: third semantic source / modern VLM extension.",
        "- No model download, model load, or Qwen inference is run by this artifact.",
        "- Qwen remains non-metric until sharded inference, parser validation, adapter export, geometry join, metrics, bootstrap, and audit complete.",
        "",
        "## Counts",
        "",
        f"- selected scans: `{counts['selected_scans']}`",
        f"- contexts: `{counts['contexts']}`",
        f"- directed pairs: `{counts['directed_pairs']}`",
        f"- universe query rows: `{counts['universe_rows']}`",
        f"- inferable input rows: `{counts['input_rows']}`",
        f"- missing query rows: `{counts['missing_rows']}`",
        f"- shards: `{counts['shards']}`",
        f"- shard size: `{manifest['sharding']['shard_size']}`",
        "",
        "## Missing-Row Policy",
        "",
        manifest["missing_row_policy"],
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
    contract_dir = resolve(repo_root, args.contract_dir)
    subset_json = resolve(repo_root, args.subset_json)
    selected_scans = resolve(repo_root, args.selected_scans)
    views_dir = resolve(repo_root, args.views_dir)
    rscan_root = resolve(repo_root, args.rscan_root)
    crop_root = resolve(repo_root, args.crop_root)
    out_dir = resolve(repo_root, args.out)
    runtime_output_root = resolve(repo_root, args.runtime_output_root)
    assert contract_dir is not None
    assert subset_json is not None
    assert selected_scans is not None
    assert views_dir is not None
    assert rscan_root is not None
    assert crop_root is not None
    assert out_dir is not None
    assert runtime_output_root is not None
    out_dir.mkdir(parents=True, exist_ok=True)

    family_to_predicates = family_map(contract_dir)
    contexts = load_contexts(subset_json, selected_scans)
    selected_scan_count = len(set(read_lines(selected_scans)))
    image_size_cache: dict[Path, tuple[int, int]] = {}
    view_cache: dict[tuple[str, int], list[ViewCandidate] | None] = {}
    pair_cache: dict[tuple[str, int, int], tuple[str, PairView | None, Path | None, list[int] | None, list[int] | None]] = {}
    universe_rows: list[dict[str, Any]] = []
    input_rows: list[dict[str, Any]] = []
    missing_rows: list[dict[str, Any]] = []
    counters: Counter[str] = Counter()
    missing_reason_counts: Counter[str] = Counter()
    warnings: list[str] = []
    errors: list[str] = []

    def object_views(scan_id: str, object_id: int) -> list[ViewCandidate] | None:
        key = (scan_id, object_id)
        if key in view_cache:
            return view_cache[key]
        path = views_dir / f"{scan_id}_object2image.pkl"
        if not path.exists():
            view_cache[key] = None
            return None
        try:
            views = load_object_views(path, object_id)
        except Exception:
            view_cache[key] = None
            return None
        view_cache[key] = views
        return views

    def pair_audit(
        context: dict[str, Any], subject_id: int, object_id: int
    ) -> tuple[str, PairView | None, Path | None, list[int] | None, list[int] | None]:
        key = (str(context["subgraph_id"]), subject_id, object_id)
        if key in pair_cache:
            return pair_cache[key]
        scan_id = str(context["scan_id"])
        subject_views = object_views(scan_id, subject_id)
        object_views_ = object_views(scan_id, object_id)
        if subject_views is None or object_views_ is None:
            result = ("missing_object2image_metadata", None, None, None, None)
            pair_cache[key] = result
            return result
        if not subject_views:
            result = ("missing_subject_views", None, None, None, None)
            pair_cache[key] = result
            return result
        if not object_views_:
            result = ("missing_object_views", None, None, None, None)
            pair_cache[key] = result
            return result
        selected = select_pair_view(subject_views, object_views_)
        if selected is None:
            result = ("missing_shared_pair_view", None, None, None, None)
            pair_cache[key] = result
            return result
        source_image = rscan_root / scan_id / "sequence" / selected.subject.frame_id
        if not source_image.exists():
            result = ("missing_source_image", selected, source_image, None, None)
            pair_cache[key] = result
            return result
        size = image_size(source_image, image_size_cache)
        if size is None:
            result = ("unreadable_source_image", selected, source_image, None, None)
            pair_cache[key] = result
            return result
        width, height = size
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
        result = (
            "ready_for_crop_render",
            selected,
            source_image,
            shift_bbox(subject_bbox, crop_box),
            shift_bbox(object_bbox, crop_box),
        )
        pair_cache[key] = result
        return result

    for context in contexts:
        objects = context["objects"]
        object_ids = sorted(objects)
        for subject_id in object_ids:
            for object_id in object_ids:
                if subject_id == object_id:
                    continue
                counters["directed_pairs"] += 1
                pair_status, selected, source_image, subject_box, object_box = pair_audit(
                    context, subject_id, object_id
                )
                for family in TARGET_FAMILIES:
                    record_id = build_record_id(args.split_name, str(context["subgraph_id"]), subject_id, object_id, family)
                    universe = {
                        "schema_version": "h001_qwen_vl_full_source_universe_v1",
                        "record_id": record_id,
                        "scan_id": context["scan_id"],
                        "subgraph_id": context["subgraph_id"],
                        "split": "held_out",
                        "subject_id": subject_id,
                        "object_id": object_id,
                        "subject_label": objects[subject_id],
                        "object_label": objects[object_id],
                        "predicate_family": family,
                        "candidate_predicates": family_to_predicates[family],
                        "pair_status": pair_status,
                        "eligible_for_inference": pair_status == "ready_for_crop_render",
                    }
                    universe_rows.append(universe)
                    if pair_status == "ready_for_crop_render":
                        assert selected is not None
                        assert source_image is not None
                        assert subject_box is not None
                        assert object_box is not None
                        input_rows.append(
                            build_input_row(
                                repo_root=repo_root,
                                crop_root=crop_root,
                                context=context,
                                subject_id=subject_id,
                                object_id=object_id,
                                family=family,
                                candidate_predicates=family_to_predicates[family],
                                selected=selected,
                                source_image=source_image,
                                subject_crop_box=subject_box,
                                object_crop_box=object_box,
                                split_name=args.split_name,
                            )
                        )
                    else:
                        missing_rows.append({**universe, "missing_reason": pair_status})
                        missing_reason_counts[pair_status] += 1

    if selected_scan_count != args.expected_scans:
        errors.append(f"selected_scans:{selected_scan_count}/{args.expected_scans}")
    if len(contexts) != args.expected_contexts:
        errors.append(f"contexts:{len(contexts)}/{args.expected_contexts}")
    if counters["directed_pairs"] != args.expected_directed_pairs:
        errors.append(f"directed_pairs:{counters['directed_pairs']}/{args.expected_directed_pairs}")
    if len(universe_rows) != args.expected_universe_rows:
        errors.append(f"universe_rows:{len(universe_rows)}/{args.expected_universe_rows}")
    if not input_rows:
        errors.append("input_rows:0")

    family_counts = Counter(row["predicate_family"] for row in universe_rows)
    input_family_counts = Counter(row["predicate_family"] for row in input_rows)
    missing_family_counts = Counter(row["predicate_family"] for row in missing_rows)
    if missing_rows:
        warnings.append(f"missing_rows_present:{len(missing_rows)}")

    universe_path = out_dir / "universe.jsonl"
    input_path = out_dir / "input.jsonl"
    missing_path = out_dir / "missing.jsonl"
    shards_path = out_dir / "shards.jsonl"
    shards = build_shards(
        repo_root,
        input_path,
        runtime_output_root,
        len(input_rows),
        args.shard_size,
        args.shard_id_prefix,
    )

    universe_sha = write_jsonl(universe_path, universe_rows)
    input_sha = write_jsonl(input_path, input_rows)
    missing_sha = write_jsonl(missing_path, missing_rows)
    shards_sha = write_jsonl(shards_path, shards)

    status = "full_source_input_ready_with_missing_rows_no_inference" if not errors else "blocked_full_source_input_audit"
    if not missing_rows and not errors:
        status = "full_source_input_ready_no_inference"

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "role": "third_semantic_source_modern_vlm_extension",
        "runtime_policy": "no_model_download_no_model_load_no_inference",
        "inputs": {
            "contract_dir": relpath(repo_root, contract_dir),
            "subset_json": relpath(repo_root, subset_json),
            "selected_scans": relpath(repo_root, selected_scans),
            "views_dir": relpath(repo_root, views_dir),
            "rscan_root": relpath(repo_root, rscan_root),
            "crop_root": relpath(repo_root, crop_root),
            "runtime_output_root": relpath(repo_root, runtime_output_root),
            "split_name": args.split_name,
        },
        "outputs": {
            "universe_jsonl": relpath(repo_root, universe_path),
            "input_jsonl": relpath(repo_root, input_path),
            "missing_jsonl": relpath(repo_root, missing_path),
            "shards_jsonl": relpath(repo_root, shards_path),
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "coverage": relpath(repo_root, out_dir / "coverage.json"),
            "report": relpath(repo_root, out_dir / "report.md"),
        },
        "counts": {
            "selected_scans": selected_scan_count,
            "contexts": len(contexts),
            "directed_pairs": counters["directed_pairs"],
            "universe_rows": len(universe_rows),
            "input_rows": len(input_rows),
            "missing_rows": len(missing_rows),
            "shards": len(shards),
            "expected_in_scope_gt_rows": args.expected_in_scope_gt,
            "family_counts": dict(sorted(family_counts.items())),
            "input_family_counts": dict(sorted(input_family_counts.items())),
            "missing_family_counts": dict(sorted(missing_family_counts.items())),
            "missing_reason_counts": dict(sorted(missing_reason_counts.items())),
            "unique_pair_view_audits": len(pair_cache),
            "unique_source_images_checked": len(image_size_cache),
        },
        "sharding": {
            "shard_size": args.shard_size,
            "resume_key": "record_id",
            "input_order": "subgraph_id, subject_id, object_id, predicate_family",
            "full_inference_must_use_background_job": True,
        },
        "missing_row_policy": (
            "Rows without shared object-pair view metadata or source images are retained in missing.jsonl "
            "and excluded from Qwen inference input.jsonl. Qwen metrics must report this denominator "
            "separately and must not silently inherit Open3DSG denominators after row drops."
        ),
        "hashes": {
            "universe_jsonl_sha256": universe_sha,
            "input_jsonl_sha256": input_sha,
            "missing_jsonl_sha256": missing_sha,
            "shards_jsonl_sha256": shards_sha,
        },
        "validation": {
            "errors": errors,
            "warnings": warnings,
        },
        "next_action": (
            "Validate input.jsonl with qwen_vl_contract_validator, then implement full-source crop rendering "
            "or render-on-demand inference shards before any Qwen paper metric run."
        ),
    }
    coverage = {
        "schema_version": "h001_qwen_vl_full_source_coverage_v1",
        "created_at": manifest["created_at"],
        "status": status,
        "counts": manifest["counts"],
        "missing_row_policy": manifest["missing_row_policy"],
        "coverage_rates": {
            "input_rows_over_universe_rows": len(input_rows) / len(universe_rows) if universe_rows else 0.0,
            "missing_rows_over_universe_rows": len(missing_rows) / len(universe_rows) if universe_rows else 0.0,
        },
    }
    write_json(out_dir / "coverage.json", coverage)
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(report(manifest), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
