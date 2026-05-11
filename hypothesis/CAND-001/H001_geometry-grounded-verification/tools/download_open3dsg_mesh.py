#!/usr/bin/env python3
"""Download/audit Open3DSG mesh and texture files for selected H001 scans."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import tempfile
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]

DEFAULT_LOCAL_DATASET = REPO_ROOT / "local_dataset"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_validation_hardened" / "scans.txt"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "open3dsg_ov" / "mesh_texture"

BASE_URL = "http://campar.in.tum.de/public_datasets/3RScan/Dataset"
OPEN3DSG_FILES = (
    "mesh.refined.v2.obj",
    "mesh.refined.mtl",
    "mesh.refined_0.png",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dataset", type=Path, default=DEFAULT_LOCAL_DATASET)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--scan-id", action="append", default=None)
    parser.add_argument("--overwrite-empty", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_scans(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def selected_scans(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    all_scans = unique_preserve_order(args.scan_id or read_scans(args.selected_scans))
    if args.scan_id:
        return all_scans, all_scans
    start = max(args.offset, 0)
    end = None if args.limit is None else start + max(args.limit, 0)
    return all_scans, all_scans[start:end]


def file_status(path: Path) -> dict[str, Any]:
    exists = path.exists()
    size = path.stat().st_size if exists and path.is_file() else 0
    return {
        "exists": exists,
        "size_bytes": size,
        "ready": exists and path.is_file() and size > 0,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def download_one(url: str, target: Path, timeout: int, retries: int) -> tuple[str, str | None]:
    target.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(retries + 1):
        fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                with tmp_path.open("wb") as out:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        out.write(chunk)
            if tmp_path.stat().st_size == 0:
                raise OSError("downloaded empty file")
            os.replace(tmp_path, target)
            return "downloaded", None
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            last_error = f"{type(exc).__name__}:{exc}"
            if tmp_path.exists():
                tmp_path.unlink()
            if attempt < retries:
                time.sleep(min(2 ** attempt, 8))
    return "failed", last_error


def handle_file(
    *,
    scan_id: str,
    filename: str,
    scan_root: Path,
    base_url: str,
    download_missing: bool,
    timeout: int,
    retries: int,
    overwrite_empty: bool,
) -> dict[str, Any]:
    target = scan_root / scan_id / filename
    before = file_status(target)
    action = "already_ready" if before["ready"] else "audit_missing"
    error = None
    url = f"{base_url.rstrip('/')}/{scan_id}/{filename}"

    if before["exists"] and before["size_bytes"] == 0 and not before["ready"] and overwrite_empty:
        target.unlink()
        before = file_status(target)
        action = "removed_empty"

    if not before["ready"] and download_missing:
        action, error = download_one(url, target, timeout=timeout, retries=retries)

    after = file_status(target)
    return {
        "scan_id": scan_id,
        "file": filename,
        "url": url,
        "path": relpath(target),
        "before": before,
        "after": after,
        "action": action,
        "error": error,
    }


def summarize(records: list[dict[str, Any]], scans: list[str]) -> dict[str, Any]:
    by_action = Counter(record["action"] for record in records)
    by_file = {
        filename: sum(1 for record in records if record["file"] == filename and record["after"]["ready"])
        for filename in OPEN3DSG_FILES
    }
    scan_ready = {
        scan_id: all(
            record["after"]["ready"]
            for record in records
            if record["scan_id"] == scan_id
        )
        for scan_id in scans
    }
    failures = [record for record in records if not record["after"]["ready"]]
    return {
        "selected_scan_count": len(scans),
        "ready_scan_count": sum(scan_ready.values()),
        "ready_file_counts": by_file,
        "ready_files": sum(1 for record in records if record["after"]["ready"]),
        "missing_files": len(failures),
        "total_files": len(records),
        "actions": dict(sorted(by_action.items())),
        "failed_records": failures,
        "total_size_bytes": sum(record["after"]["size_bytes"] for record in records if record["after"]["ready"]),
    }


def build_manifest(args: argparse.Namespace, records: list[dict[str, Any]], all_scans: list[str], scans: list[str]) -> dict[str, Any]:
    summary = summarize(records, scans)
    status = "mesh_texture_ready" if summary["missing_files"] == 0 and scans else "mesh_texture_blocked"
    if not args.download_missing and summary["missing_files"] > 0:
        status = "mesh_texture_audit_missing"
    blockers = []
    for filename, count in summary["ready_file_counts"].items():
        if count < len(scans):
            blockers.append(f"missing_scan_file:{filename}:{count}/{len(scans)}")
    return {
        "schema_version": "h001_open3dsg_mesh_texture_v1",
        "date_checked": now_iso(),
        "status": status,
        "download_missing": args.download_missing,
        "local_dataset": relpath(args.local_dataset),
        "selected_scans_file": relpath(args.selected_scans),
        "all_selected_scan_count": len(all_scans),
        "processed_scan_count": len(scans),
        "offset": args.offset,
        "limit": args.limit,
        "base_url": args.base_url,
        "files": list(OPEN3DSG_FILES),
        "summary": summary,
        "blockers": blockers,
        "claim_limit": "No Open3DSG raw dump, JSONL export, geometry join, metric, or improvement claim exists after mesh/texture acquisition.",
        "next_action": "Run Open3DSG view/preprocessed pickle generation after mesh/texture files are ready.",
    }


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    summary = manifest["summary"]
    lines = [
        "# Open3DSG Mesh/Texture Acquisition",
        "",
        f"Date: `{manifest['date_checked']}`",
        f"Status: `{manifest['status']}`",
        f"Download missing: `{manifest['download_missing']}`",
        f"Processed scans: `{manifest['processed_scan_count']}`",
        "",
        "## Readiness",
        "",
        f"- ready scans: `{summary['ready_scan_count']}/{manifest['processed_scan_count']}`",
        f"- ready files: `{summary['ready_files']}/{summary['total_files']}`",
        f"- missing files: `{summary['missing_files']}`",
        "",
        "| File | Ready scans |",
        "| --- | --- |",
    ]
    for filename, count in summary["ready_file_counts"].items():
        lines.append(f"| `{filename}` | `{count}/{manifest['processed_scan_count']}` |")
    lines.extend(["", "## Actions", ""])
    for action, count in summary["actions"].items():
        lines.append(f"- `{action}`: `{count}`")
    lines.extend(["", "## Blockers", ""])
    if manifest["blockers"]:
        lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    else:
        lines.append("- none")
    lines.extend(["", "## Claim Limit", "", manifest["claim_limit"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    all_scans, scans = selected_scans(args)
    scan_root = args.local_dataset / "3RScan" / "scans"
    tasks = [
        {
            "scan_id": scan_id,
            "filename": filename,
            "scan_root": scan_root,
            "base_url": args.base_url,
            "download_missing": args.download_missing,
            "timeout": args.timeout,
            "retries": args.retries,
            "overwrite_empty": args.overwrite_empty,
        }
        for scan_id in scans
        for filename in OPEN3DSG_FILES
    ]

    records: list[dict[str, Any]] = []
    workers = max(1, args.workers)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(handle_file, **task) for task in tasks]
        for index, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            record = future.result()
            records.append(record)
            print(
                f"[{index}/{len(futures)}] {record['scan_id']} {record['file']} "
                f"{record['action']} ready={record['after']['ready']} size={record['after']['size_bytes']}"
            )

    records.sort(key=lambda item: (item["scan_id"], item["file"]))
    manifest = build_manifest(args, records, all_scans, scans)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "manifest.json", manifest)
    write_jsonl(args.output_dir / "records.jsonl", records)
    write_report(args.output_dir / "report.md", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if manifest["status"] == "mesh_texture_ready" or not args.download_missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
