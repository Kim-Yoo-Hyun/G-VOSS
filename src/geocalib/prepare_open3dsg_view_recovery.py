#!/usr/bin/env python3
"""Back up and optionally remove Open3DSG view pickles before recovery."""

from __future__ import annotations

import argparse
import json
import shutil
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
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--scan-id", action="append", required=True)
    parser.add_argument("--remove-original", action="store_true")
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


def file_record(repo_root: Path, path: Path) -> dict[str, Any]:
    return {
        "path": relpath(repo_root, path),
        "exists": path.exists(),
        "size_bytes": path.stat().st_size if path.exists() else 0,
    }


def main() -> int:
    args = parse_args()
    views_root = args.runtime_root / "output/datasets/OpenSG_3RScan/views"
    backup_root = args.output_dir / "original_views"
    records: list[dict[str, Any]] = []
    for scan_id in args.scan_id:
        src = views_root / f"{scan_id}_object2image.pkl"
        backup = backup_root / f"{scan_id}_object2image.pkl"
        before = file_record(args.repo_root, src)
        backup.parent.mkdir(parents=True, exist_ok=True)
        action = "missing_original"
        if src.exists():
            if not backup.exists():
                shutil.copy2(src, backup)
                action = "backed_up"
            else:
                action = "backup_already_exists"
            if args.remove_original:
                src.unlink()
                action += "_removed_original"
        records.append(
            {
                "scan_id": scan_id,
                "action": action,
                "before": before,
                "backup": file_record(args.repo_root, backup),
                "after": file_record(args.repo_root, src),
            }
        )
    manifest = {
        "schema_version": "h001_open3dsg_view_recovery_prepare_v1",
        "date_checked": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "prepared",
        "runtime_root": relpath(args.repo_root, args.runtime_root),
        "output_dir": relpath(args.repo_root, args.output_dir),
        "remove_original": args.remove_original,
        "scan_count": len(args.scan_id),
        "records": relpath(args.repo_root, args.output_dir / "records.jsonl"),
    }
    write_jsonl(args.output_dir / "records.jsonl", records)
    write_json(args.output_dir / "manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
