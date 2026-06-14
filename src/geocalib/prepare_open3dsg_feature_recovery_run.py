#!/usr/bin/env python3
"""Prepare a hardlinked Open3DSG feature run dir for recovery regeneration."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--source-run-dir", type=Path, required=True)
    parser.add_argument("--dest-run-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--purge-feature-id", action="append", default=[])
    return parser.parse_args()


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def hardlink_tree(src: Path, dst: Path) -> dict[str, int]:
    linked = 0
    existing = 0
    dirs = 0
    for root, dirnames, filenames in os.walk(src):
        root_path = Path(root)
        rel = root_path.relative_to(src)
        dst_root = dst / rel
        dst_root.mkdir(parents=True, exist_ok=True)
        dirs += len(dirnames)
        for filename in filenames:
            src_file = root_path / filename
            dst_file = dst_root / filename
            if dst_file.exists():
                existing += 1
                continue
            os.link(src_file, dst_file)
            linked += 1
    return {"linked_files": linked, "existing_files": existing, "visited_dirs": dirs}


def count_pt_files(path: Path) -> int:
    return sum(1 for item in path.rglob("*.pt") if item.is_file()) if path.is_dir() else 0


def main() -> int:
    args = parse_args()
    if not args.source_run_dir.is_dir():
        raise FileNotFoundError(f"missing source run dir: {args.source_run_dir}")
    before_dest_pt = count_pt_files(args.dest_run_dir)
    copy_stats = hardlink_tree(args.source_run_dir, args.dest_run_dir)
    purge_records: list[dict[str, Any]] = []
    for feature_id in sorted(set(args.purge_feature_id)):
        removed = []
        missing = []
        for subdir in sorted(child for child in args.dest_run_dir.iterdir() if child.is_dir()):
            target = subdir / f"{feature_id}.pt"
            if target.exists():
                target.unlink()
                removed.append(relpath(args.repo_root, target))
            else:
                missing.append(relpath(args.repo_root, target))
        purge_records.append(
            {
                "feature_id": feature_id,
                "removed_count": len(removed),
                "missing_count": len(missing),
                "removed": removed,
                "missing": missing,
            }
        )
    manifest = {
        "schema_version": "h001_open3dsg_feature_recovery_prepare_v1",
        "date_checked": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "prepared",
        "source_run_dir": relpath(args.repo_root, args.source_run_dir),
        "dest_run_dir": relpath(args.repo_root, args.dest_run_dir),
        "before_dest_pt_files": before_dest_pt,
        "after_dest_pt_files": count_pt_files(args.dest_run_dir),
        "copy_stats": copy_stats,
        "purged_feature_ids": len(purge_records),
        "records": relpath(args.repo_root, args.output_dir / "records.jsonl"),
    }
    write_jsonl(args.output_dir / "records.jsonl", purge_records)
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
