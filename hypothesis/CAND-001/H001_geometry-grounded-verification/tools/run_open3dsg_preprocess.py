#!/usr/bin/env python3
"""Run/audit Open3DSG preprocessing for selected H001 subgraphs."""

from __future__ import annotations

import argparse
import concurrent.futures
import importlib
import json
import os
import pickle
import sys
import traceback
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from run_open3dsg_views import (
    copy_open3dsg_source,
    install_numpy_pickle_compat,
    patch_config,
    relpath,
    write_json,
    write_jsonl,
)


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]

DEFAULT_LOCAL_DATASET = REPO_ROOT / "local_dataset"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "open3dsg_ov" / "preprocess"
DEFAULT_SOURCE = Path("/tmp/open3dsg_source")
DEFAULT_STAGED_ROOT = DEFAULT_LOCAL_DATASET / "Open3DSG_staged" / "h001_runtime"
DEFAULT_WORK_SOURCE = DEFAULT_STAGED_ROOT / "source" / "open3dsg_source"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--open3dsg-source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--work-source", type=Path, default=DEFAULT_WORK_SOURCE)
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--split", default="validation", choices=("train", "validation", "test"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--scan-id", action="append", default=None)
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--refresh-source", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--deep-inspect", action="store_true")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def configure_import(staged_root: str, work_source: str) -> None:
    os.environ["OPEN3DSG_HOME"] = str(Path.home())
    os.environ["OPEN3DSG_BASE"] = staged_root
    os.environ["OPEN3DSG_DATA"] = str(Path(staged_root) / "data")
    os.environ["OPEN3DSG_DATA_OUT"] = str(Path(staged_root) / "output")
    if work_source not in sys.path:
        sys.path.insert(0, work_source)


def relationship_id(relationship: dict[str, Any]) -> str:
    return f"{relationship['scan']}-{str(hex(relationship['split']))[-1]}"


def preprocessed_path(staged_root: Path, relationship: dict[str, Any]) -> Path:
    split = str(hex(relationship["split"]))[-1]
    return (
        staged_root
        / "output"
        / "datasets"
        / "OpenSG_3RScan"
        / "preprocessed"
        / relationship["scan"]
        / f"data_dict_{split}.pkl"
    )


def read_relationships(staged_root: Path, split: str) -> list[dict[str, Any]]:
    path = staged_root / "data" / "3RScan" / "3DSSG_subset" / f"relationships_{split}.json"
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("scans", [])


def select_relationships(args: argparse.Namespace) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    relationships = read_relationships(args.staged_root, args.split)
    if args.scan_id:
        wanted = set(args.scan_id)
        selected = [relationship for relationship in relationships if relationship.get("scan") in wanted]
        return relationships, selected
    start = max(args.offset, 0)
    end = None if args.limit is None else start + max(args.limit, 0)
    return relationships, relationships[start:end]


def inspect_pickle(path: Path, deep: bool = False) -> dict[str, Any]:
    if not path.exists():
        return {
            "exists": False,
            "valid_pickle": False,
            "size_bytes": 0,
            "objects_count": None,
            "predicate_count": None,
        }
    size = path.stat().st_size
    out: dict[str, Any] = {
        "exists": True,
        "valid_pickle": size > 0,
        "size_bytes": size,
        "objects_count": None,
        "predicate_count": None,
    }
    if not deep:
        return out
    try:
        install_numpy_pickle_compat()
        with path.open("rb") as handle:
            payload = pickle.load(handle)
        out.update(
            {
                "valid_pickle": isinstance(payload, dict),
                "scan_id": payload.get("scan_id") if isinstance(payload, dict) else None,
                "objects_count": payload.get("objects_count") if isinstance(payload, dict) else None,
                "predicate_count": payload.get("predicate_count") if isinstance(payload, dict) else None,
                "keys": sorted(payload.keys()) if isinstance(payload, dict) else [],
            }
        )
    except Exception as exc:  # noqa: BLE001
        out.update({"valid_pickle": False, "error": f"{type(exc).__name__}:{exc}"})
    return out


def load_processor(staged_root: str, work_source: str, skip_existing: bool) -> Any:
    configure_import(staged_root, work_source)
    module = importlib.import_module("open3dsg.data.preprocess_3rscan")
    return module.Preprocessor(skip_existing=skip_existing, distance="min")


def run_with_processor(
    relationship: dict[str, Any],
    staged_root: Path,
    processor: Any,
    audit_only: bool,
    force: bool,
    deep_inspect: bool,
) -> dict[str, Any]:
    out_path = preprocessed_path(staged_root, relationship)
    before = inspect_pickle(out_path, deep=False)
    action = "already_ready" if before["valid_pickle"] and not force else "audit_missing"
    error = None
    traceback_text = None
    after = before

    if not audit_only and action != "already_ready":
        try:
            install_numpy_pickle_compat()
            processor.write_pickle(relationship)
            action = "regenerated" if before["valid_pickle"] and force else "generated"
        except Exception as exc:  # noqa: BLE001
            action = "failed"
            error = f"{type(exc).__name__}:{exc}"
            traceback_text = traceback.format_exc(limit=20)
        after = inspect_pickle(out_path, deep=deep_inspect)

    if action in {"generated", "regenerated", "already_ready"} and not after["valid_pickle"]:
        action = "missing_output"

    return {
        "relationship_id": relationship_id(relationship),
        "scan_id": relationship["scan"],
        "split": relationship["split"],
        "path": relpath(out_path),
        "relationship_count": len(relationship.get("relationships", [])),
        "object_count_annotation": len(relationship.get("objects", {})),
        "before": before,
        "after": after,
        "action": action,
        "error": error,
        "traceback": traceback_text,
    }


def run_one_process(
    relationship: dict[str, Any],
    staged_root: str,
    work_source: str,
    audit_only: bool,
    force: bool,
    deep_inspect: bool,
) -> dict[str, Any]:
    processor = load_processor(staged_root, work_source, skip_existing=not force)
    return run_with_processor(relationship, Path(staged_root), processor, audit_only, force, deep_inspect)


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    actions = Counter(record["action"] for record in records)
    ready = [record for record in records if record["after"]["valid_pickle"]]
    failed = [record for record in records if record["action"] in {"failed", "missing_output"}]
    missing = [record for record in records if not record["after"]["valid_pickle"]]
    return {
        "processed_subgraph_count": len(records),
        "ready_subgraph_count": len(ready),
        "missing_subgraph_count": len(records) - len(ready),
        "unique_ready_scans": len({record["scan_id"] for record in ready}),
        "actions": dict(sorted(actions.items())),
        "failed_records": failed,
        "missing_records": missing,
        "total_size_bytes": sum(record["after"]["size_bytes"] for record in ready),
        "total_annotation_relations": sum(record["relationship_count"] for record in records),
    }


def build_manifest(
    args: argparse.Namespace,
    all_relationships: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    records: list[dict[str, Any]],
    config_patch: str,
) -> dict[str, Any]:
    summary = summarize(records)
    full_ready = bool(relationships) and summary["missing_subgraph_count"] == 0
    partial_ready = bool(relationships) and summary["ready_subgraph_count"] > 0
    status = "preprocess_ready" if full_ready else "preprocess_blocked"
    if partial_ready and not full_ready:
        status = "preprocess_partial_ready"
    if args.audit_only and not partial_ready:
        status = "preprocess_audit_missing"
    blockers = []
    warnings = []
    if summary["missing_subgraph_count"]:
        key = (
            f"open3dsg_preprocessed_pickles:"
            f"{summary['ready_subgraph_count']}/{len(relationships)}"
        )
        if partial_ready:
            warnings.append(f"partial_runtime:{key}")
        else:
            blockers.append(f"missing_runtime:{key}")
    return {
        "schema_version": "h001_open3dsg_preprocess_v1",
        "date_checked": now_iso(),
        "status": status,
        "split": args.split,
        "audit_only": args.audit_only,
        "force": args.force,
        "workers": max(1, args.workers),
        "open3dsg_min_visible_objects": os.environ.get("OPEN3DSG_MIN_VISIBLE_OBJECTS", "4"),
        "open3dsg_source": relpath(args.open3dsg_source),
        "work_source": relpath(args.work_source),
        "staged_root": relpath(args.staged_root),
        "preprocessed_root": relpath(
            args.staged_root / "output" / "datasets" / "OpenSG_3RScan" / "preprocessed"
        ),
        "config_patch": config_patch,
        "all_split_subgraph_count": len(all_relationships),
        "processed_subgraph_count": len(relationships),
        "offset": args.offset,
        "limit": args.limit,
        "summary": summary,
        "blockers": blockers,
        "warnings": warnings,
        "claim_limit": "No Open3DSG raw dump, prediction JSONL, geometry join, metric, or improvement claim exists after preprocessing.",
        "next_action": "Acquire Open3DSG checkpoint/model artifacts, then run raw dump smoke.",
    }


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    summary = manifest["summary"]
    lines = [
        "# Open3DSG Preprocess Generation",
        "",
        f"Date: `{manifest['date_checked']}`",
        f"Status: `{manifest['status']}`",
        f"Split: `{manifest['split']}`",
        f"Processed subgraphs: `{manifest['processed_subgraph_count']}`",
        f"Workers: `{manifest['workers']}`",
        f"Preprocessed root: `{manifest['preprocessed_root']}`",
        "",
        "## Readiness",
        "",
        f"- ready subgraphs: `{summary['ready_subgraph_count']}/{manifest['processed_subgraph_count']}`",
        f"- missing subgraphs: `{summary['missing_subgraph_count']}`",
        f"- unique ready scans: `{summary['unique_ready_scans']}`",
        f"- total annotation relations: `{summary['total_annotation_relations']}`",
        f"- total pickle bytes: `{summary['total_size_bytes']}`",
        "",
        "## Actions",
        "",
    ]
    for action, count in summary["actions"].items():
        lines.append(f"- `{action}`: `{count}`")
    lines.extend(["", "## Blockers", ""])
    if manifest["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    if manifest.get("warnings"):
        lines.extend(f"- `{warning}`" for warning in manifest["warnings"])
    else:
        lines.append("- none")
    lines.extend(["", "## Claim Limit", "", manifest["claim_limit"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    all_relationships, relationships = select_relationships(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    copy_open3dsg_source(args.open3dsg_source, args.work_source, args.refresh_source)
    config_patch = patch_config(args.open3dsg_source, args.work_source, args.output_dir)
    configure_import(str(args.staged_root.resolve()), str(args.work_source.resolve()))

    records: list[dict[str, Any]] = []
    workers = max(1, args.workers)
    if workers == 1:
        processor = load_processor(str(args.staged_root.resolve()), str(args.work_source.resolve()), skip_existing=not args.force)
        for idx, relationship in enumerate(relationships, start=1):
            record = run_with_processor(relationship, args.staged_root, processor, args.audit_only, args.force, args.deep_inspect)
            records.append(record)
            print(
                f"[{idx}/{len(relationships)}] {record['relationship_id']} {record['action']} "
                f"ready={record['after']['valid_pickle']} bytes={record['after']['size_bytes']}"
            )
    else:
        with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as executor:
            futures = [
                executor.submit(
                    run_one_process,
                    relationship,
                    str(args.staged_root.resolve()),
                    str(args.work_source.resolve()),
                    args.audit_only,
                    args.force,
                    args.deep_inspect,
                )
                for relationship in relationships
            ]
            for idx, future in enumerate(concurrent.futures.as_completed(futures), start=1):
                record = future.result()
                records.append(record)
                print(
                    f"[{idx}/{len(relationships)}] {record['relationship_id']} {record['action']} "
                    f"ready={record['after']['valid_pickle']} bytes={record['after']['size_bytes']}"
                )

    records.sort(key=lambda item: (item["scan_id"], item["split"]))
    manifest = build_manifest(args, all_relationships, relationships, records, config_patch)
    write_json(args.output_dir / "manifest.json", manifest)
    write_jsonl(args.output_dir / "records.jsonl", records)
    write_report(args.output_dir / "report.md", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if manifest["status"] in {"preprocess_ready", "preprocess_partial_ready"} or args.audit_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
