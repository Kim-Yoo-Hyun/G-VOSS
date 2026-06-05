#!/usr/bin/env python3
"""Diagnose Open3DSG full-validation contexts dropped by preprocessing."""

from __future__ import annotations

import argparse
import json
import pickle
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=Path("/workspace/local_dataset/Open3DSG_staged/h001_full_validation_runtime"),
    )
    parser.add_argument(
        "--missing-records",
        type=Path,
        default=Path(
            "/workspace/experiments/H001_geom_reliability/sources/open3dsg/"
            "full_validation/preprocess_retry2/records.jsonl"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "/workspace/experiments/H001_geom_reliability/sources/open3dsg/"
            "full_validation/preprocess_missing15_diagnosis"
        ),
    )
    parser.add_argument(
        "--missing-action",
        action="append",
        default=["missing_output"],
        help="Record action(s) to diagnose as missing. Repeatable.",
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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


def load_pickle(path: Path) -> tuple[bool, Any, str | None]:
    if not path.is_file():
        return False, None, "missing_file"
    try:
        install_numpy_pickle_compat()
        with path.open("rb") as handle:
            return True, pickle.load(handle), None
    except Exception as exc:  # noqa: BLE001
        return False, None, f"{type(exc).__name__}:{exc}"


def relationship_id(row: dict[str, Any]) -> str:
    return f"{row['scan']}-{str(hex(int(row['split'])))[-1]}"


def load_relationships(runtime_root: Path) -> dict[str, dict[str, Any]]:
    path = runtime_root / "data/3RScan/3DSSG_subset/relationships_validation.json"
    payload = read_json(path)
    return {relationship_id(row): row for row in payload.get("scans", [])}


def frame_summary(frame_rows: list[Any]) -> dict[str, Any]:
    if not frame_rows:
        return {
            "frame_count": 0,
            "best_frame": None,
            "max_pixels": 0,
            "max_visibility_ratio": 0.0,
            "max_bbox_area": 0,
        }
    best: dict[str, Any] | None = None
    max_area = 0
    for frame in frame_rows:
        name = frame[0] if len(frame) > 0 else None
        pixels = int(frame[1]) if len(frame) > 1 else 0
        ratio = float(frame[2]) if len(frame) > 2 else 0.0
        bbox = frame[3] if len(frame) > 3 else None
        area = 0
        if bbox is not None and len(bbox) >= 4:
            area = max(0, int(bbox[2]) - int(bbox[0])) * max(0, int(bbox[3]) - int(bbox[1]))
        item = {
            "frame": str(name),
            "pixels": pixels,
            "visibility_ratio": ratio,
            "bbox_area": area,
        }
        if best is None or (item["pixels"], item["visibility_ratio"], item["bbox_area"]) > (
            best["pixels"],
            best["visibility_ratio"],
            best["bbox_area"],
        ):
            best = item
        max_area = max(max_area, area)
    return {
        "frame_count": len(frame_rows),
        "best_frame": best["frame"] if best else None,
        "max_pixels": best["pixels"] if best else 0,
        "max_visibility_ratio": best["visibility_ratio"] if best else 0.0,
        "max_bbox_area": max_area,
    }


def label_for(objects: dict[str, Any], object_id: str) -> Any:
    if object_id in objects:
        return objects[object_id]
    try:
        return objects[int(object_id)]  # type: ignore[index]
    except Exception:  # noqa: BLE001
        return None


def relation_endpoint_counts(relationships: list[list[Any]], visible_ids: set[str]) -> dict[str, int]:
    total = 0
    both_visible = 0
    one_visible = 0
    none_visible = 0
    self_edges = 0
    for triple in relationships:
        if len(triple) < 2:
            continue
        total += 1
        subject = str(triple[0])
        obj = str(triple[1])
        if subject == obj:
            self_edges += 1
        visible_count = int(subject in visible_ids) + int(obj in visible_ids)
        if visible_count == 2:
            both_visible += 1
        elif visible_count == 1:
            one_visible += 1
        else:
            none_visible += 1
    return {
        "annotation_relation_count": total,
        "relations_both_endpoints_visible": both_visible,
        "relations_one_endpoint_visible": one_visible,
        "relations_no_endpoint_visible": none_visible,
        "self_edges": self_edges,
    }


def classify_record(
    view_pickle_exists: bool,
    view_pickle_error: str | None,
    annotation_object_count: int,
    visible_annotation_count: int,
    relations_both_visible: int,
) -> tuple[str, str, str]:
    if not view_pickle_exists:
        return ("file_path_cache", "unavailable", view_pickle_error or "object2image pickle is missing/unreadable")
    if visible_annotation_count < 2:
        return (
            "source_preprocess_policy_visible_object_gate",
            "not_recoverable_by_min2",
            "fewer than two annotation objects have generated object2image views",
        )
    if visible_annotation_count < 4:
        if relations_both_visible <= 0:
            return (
                "source_preprocess_policy_visible_object_gate",
                "candidate_relax_min_visible_to_2_low_metric_value",
                "relaxing the min-visible-object gate can likely write a pickle, but no GT relation has both endpoints visible",
            )
        return (
            "source_preprocess_policy_visible_object_gate",
            "candidate_relax_min_visible_to_2",
            "Open3DSG drops the context only because visible annotation objects are below the hard-coded 4-object gate",
        )
    if annotation_object_count > 0 and visible_annotation_count == 0:
        return ("view_generation_failure", "needs_view_regeneration", "annotation objects exist, but none received object2image views")
    return ("unknown_post_gate_failure", "inspect_exception", "the visible-object gate should pass; inspect stack/logs")


def diagnose(args: argparse.Namespace) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    relationships = load_relationships(args.runtime_root)
    retry_rows = read_jsonl(args.missing_records)
    missing_actions = set(args.missing_action)
    missing_rows = [row for row in retry_rows if row.get("action") in missing_actions]
    views_root = args.runtime_root / "output/datasets/OpenSG_3RScan/views"
    preprocessed_root = args.runtime_root / "output/datasets/OpenSG_3RScan/preprocessed"

    records: list[dict[str, Any]] = []
    for retry_row in missing_rows:
        rel_id = retry_row["relationship_id"]
        relationship = relationships.get(rel_id)
        if relationship is None:
            records.append({"relationship_id": rel_id, "diagnosis": "missing_relationship_annotation"})
            continue

        scan_id = relationship["scan"]
        split = int(relationship["split"])
        objects = {str(key): value for key, value in relationship.get("objects", {}).items()}
        annotation_ids = sorted(objects.keys(), key=lambda item: int(item) if item.isdigit() else item)

        view_path = views_root / f"{scan_id}_object2image.pkl"
        view_ok, object2image, view_error = load_pickle(view_path)
        if not isinstance(object2image, dict):
            object2image = {}
        view_keys = {str(key) for key in object2image.keys()}

        visible_ids: set[str] = set()
        object_rows: list[dict[str, Any]] = []
        for object_id in annotation_ids:
            frames = object2image.get(object_id, [])
            if frames:
                visible_ids.add(object_id)
            summary = frame_summary(frames)
            object_rows.append(
                {
                    "object_id": object_id,
                    "label": label_for(objects, object_id),
                    "in_object2image_pickle": object_id in view_keys,
                    "has_object2image_frames": bool(frames),
                    **summary,
                }
            )

        endpoint_counts = relation_endpoint_counts(relationship.get("relationships", []), visible_ids)
        missing_from_scan = [object_id for object_id in annotation_ids if object_id not in view_keys]
        visible_annotation_count = len(visible_ids)
        category, recoverability, reason = classify_record(
            view_pickle_exists=view_ok,
            view_pickle_error=view_error,
            annotation_object_count=len(annotation_ids),
            visible_annotation_count=visible_annotation_count,
            relations_both_visible=endpoint_counts["relations_both_endpoints_visible"],
        )

        preprocessed_path = preprocessed_root / scan_id / f"data_dict_{str(hex(split))[-1]}.pkl"
        records.append(
            {
                "relationship_id": rel_id,
                "scan_id": scan_id,
                "split": split,
                "annotation_object_count": len(annotation_ids),
                "annotation_relationship_count": len(relationship.get("relationships", [])),
                "preprocessed_path": relpath(args.repo_root, preprocessed_path),
                "preprocessed_exists": preprocessed_path.exists(),
                "view_path": relpath(args.repo_root, view_path),
                "view_pickle_exists": view_ok,
                "view_pickle_error": view_error,
                "scan_level_object_count_in_object2image": len(view_keys),
                "visible_annotation_object_count": visible_annotation_count,
                "missing_annotation_object_count": len(annotation_ids) - visible_annotation_count,
                "official_min_visible_object_gate": 4,
                "official_gate_pass": visible_annotation_count >= 4,
                "relaxed_min2_gate_pass": visible_annotation_count >= 2,
                "missing_annotation_ids_from_object2image": missing_from_scan,
                "visible_annotation_ids": sorted(visible_ids, key=lambda item: int(item) if item.isdigit() else item),
                **endpoint_counts,
                "diagnosis_category": category,
                "recoverability": recoverability,
                "diagnosis_reason": reason,
                "object_diagnostics": object_rows,
            }
        )
    return records, summarize(records, args)


def summarize(records: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    categories = Counter(row.get("diagnosis_category", "unknown") for row in records)
    recoverability = Counter(row.get("recoverability", "unknown") for row in records)
    visible_counts = Counter(str(row.get("visible_annotation_object_count", "unknown")) for row in records)
    relaxed_min2_candidates = [
        row["relationship_id"]
        for row in records
        if row.get("relaxed_min2_gate_pass") and row.get("relations_both_endpoints_visible", 0) > 0
    ]
    unrecoverable_without_view_regen = [
        row["relationship_id"] for row in records if not row.get("relaxed_min2_gate_pass")
    ]
    return {
        "schema_version": "h001_open3dsg_missing15_diagnosis_v1",
        "date_checked": now_iso(),
        "runtime_root": relpath(args.repo_root, args.runtime_root),
        "missing_records": relpath(args.repo_root, args.missing_records),
        "missing_actions": sorted(args.missing_action),
        "diagnosed_contexts": len(records),
        "official_drop_condition": {
            "file": "open3dsg/data/preprocess_3rscan.py",
            "condition": "if len(objects_id) - len(drop) < 4: print('too few visible objects, scene missalignment possible'); return",
            "meaning": "the source drops a subgraph when fewer than four annotation objects have object2image view metadata",
        },
        "view_generation_condition": {
            "file": "open3dsg/data/get_object_frame.py",
            "condition": "pixels > 12 and ((ratio > 0.3 or pixels > 80) or wall/floor pixels > 80), with R3Scan projection visibility threshold 0.20",
        },
        "categories": dict(sorted(categories.items())),
        "recoverability": dict(sorted(recoverability.items())),
        "visible_annotation_object_count_histogram": dict(sorted(visible_counts.items())),
        "relaxed_min2_candidate_count": len(relaxed_min2_candidates),
        "relaxed_min2_candidate_ids": relaxed_min2_candidates,
        "unrecoverable_without_view_regeneration_count": len(unrecoverable_without_view_regen),
        "unrecoverable_without_view_regeneration_ids": unrecoverable_without_view_regen,
    }


def write_report(path: Path, summary: dict[str, Any], records: list[dict[str, Any]]) -> None:
    lines = [
        "# Open3DSG Missing-15 Preprocess Diagnosis",
        "",
        f"Date: `{summary['date_checked']}`",
        f"Status: `diagnosis_ready`",
        f"Diagnosed contexts: `{summary['diagnosed_contexts']}`",
        "",
        "## Source Condition",
        "",
        f"- drop condition: `{summary['official_drop_condition']['condition']}`",
        f"- meaning: {summary['official_drop_condition']['meaning']}",
        f"- view generation: `{summary['view_generation_condition']['condition']}`",
        "",
        "## Summary",
        "",
        f"- categories: `{summary['categories']}`",
        f"- recoverability: `{summary['recoverability']}`",
        f"- visible annotation object counts: `{summary['visible_annotation_object_count_histogram']}`",
        f"- relaxed min-2 candidates: `{summary['relaxed_min2_candidate_count']}`",
        f"- unrecoverable without view regeneration: `{summary['unrecoverable_without_view_regeneration_count']}`",
        "",
        "## Diagnosis Table",
        "",
        "| relationship_id | ann obj | visible obj | both-visible GT rel | category | recoverability |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for row in records:
        lines.append(
            "| {relationship_id} | {annotation_object_count} | {visible_annotation_object_count} | "
            "{relations_both_endpoints_visible} | {diagnosis_category} | {recoverability} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "This artifact diagnoses the source preprocessing drop. It is not a promoted paper metric. "
            "Any relaxed recovery branch must keep canonical full-validation artifacts separate and rerun "
            "feature audit, raw dump, adapter export, geometry join, metrics, bootstrap, and table generation "
            "before it can replace the current Open3DSG full-validation bundle.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records, summary = diagnose(args)
    manifest = {
        **summary,
        "status": "diagnosis_ready",
        "outputs": {
            "records": relpath(args.repo_root, args.output_dir / "records.jsonl"),
            "summary": relpath(args.repo_root, args.output_dir / "summary.json"),
            "report": relpath(args.repo_root, args.output_dir / "report.md"),
        },
    }
    write_jsonl(args.output_dir / "records.jsonl", records)
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "manifest.json", manifest)
    write_report(args.output_dir / "report.md", summary, records)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
