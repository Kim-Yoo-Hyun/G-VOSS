#!/usr/bin/env python3
"""Audit or download selected 3RScan payload files for H001."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_SCOPE_ROOT = H001_ROOT / "artifacts" / "subset" / "h001_validation_hardened"
DEFAULT_SELECTED_SCANS = DEFAULT_SCOPE_ROOT / "scans.txt"
DEFAULT_OUTPUT_DIR = DEFAULT_SCOPE_ROOT

BASE_URL = "http://campar.in.tum.de/public_datasets/3RScan/Dataset"
GEOMETRY_FILES = (
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
)
SEQUENCE_FILES = ("sequence.zip",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit/download selected 3RScan geometry and sequence payloads."
    )
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--download-base-url", default=BASE_URL)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--overwrite-empty", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--include-sequence", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--scan-id", action="append", default=None)
    parser.add_argument("--stop-on-error", action="store_true")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_scan_list(path: Path) -> list[str]:
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


def selected_scan_ids(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    all_ids = unique_preserve_order(args.scan_id or read_scan_list(args.selected_scans))
    if args.scan_id:
        return all_ids, all_ids
    start = max(args.offset, 0)
    end = None if args.limit is None else start + max(args.limit, 0)
    return all_ids, all_ids[start:end]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def file_status(path: Path) -> dict[str, Any]:
    exists = path.exists()
    size = path.stat().st_size if exists and path.is_file() else 0
    return {
        "exists": exists,
        "size_bytes": size,
        "ready": exists and path.is_file() and size > 0,
    }


def download_file(url: str, target: Path, timeout: int) -> tuple[str, str | None]:
    target.parent.mkdir(parents=True, exist_ok=True)
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
        os.replace(tmp_path, target)
        return "downloaded", None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        if tmp_path.exists():
            tmp_path.unlink()
        return "failed", f"{type(exc).__name__}:{exc}"


def handle_file(
    *,
    scan_id: str,
    group: str,
    filename: str,
    scan_dir: Path,
    download_missing: bool,
    overwrite_empty: bool,
    base_url: str,
    timeout: int,
) -> dict[str, Any]:
    path = scan_dir / filename
    before = file_status(path)
    action = "audit"
    error = None

    if before["ready"]:
        action = "already_ready"
    elif before["exists"] and before["size_bytes"] == 0 and download_missing and overwrite_empty:
        path.unlink()
        before = file_status(path)
        action = "removed_empty"

    if not before["ready"] and download_missing:
        url = f"{base_url.rstrip('/')}/{scan_id}/{filename}"
        action, error = download_file(url, path, timeout)

    after = file_status(path)
    return {
        "scan_id": scan_id,
        "group": group,
        "file": filename,
        "path": relpath(path),
        "before": before,
        "after": after,
        "action": action,
        "error": error,
    }


def required_file_specs(include_sequence: bool) -> list[tuple[str, str]]:
    specs = [("geometry", filename) for filename in GEOMETRY_FILES]
    if include_sequence:
        specs.extend(("sequence", filename) for filename in SEQUENCE_FILES)
    return specs


def scan_record(
    *,
    scan_id: str,
    dataset_root: Path,
    include_sequence: bool,
    download_missing: bool,
    overwrite_empty: bool,
    base_url: str,
    timeout: int,
) -> dict[str, Any]:
    scan_dir = dataset_root / "3RScan" / "scans" / scan_id
    file_records = [
        handle_file(
            scan_id=scan_id,
            group=group,
            filename=filename,
            scan_dir=scan_dir,
            download_missing=download_missing,
            overwrite_empty=overwrite_empty,
            base_url=base_url,
            timeout=timeout,
        )
        for group, filename in required_file_specs(include_sequence)
    ]
    geometry_ready = all(
        record["after"]["ready"] for record in file_records if record["group"] == "geometry"
    )
    sequence_ready: bool | None = all(
        record["after"]["ready"] for record in file_records if record["group"] == "sequence"
    )
    if not include_sequence:
        sequence_ready = None
    payload_ready = geometry_ready and (sequence_ready if include_sequence else True)
    return {
        "scan_id": scan_id,
        "scan_dir": relpath(scan_dir),
        "scan_dir_exists": scan_dir.is_dir(),
        "files": file_records,
        "geometry_ready": geometry_ready,
        "sequence_zip_ready": sequence_ready,
        "payload_ready": payload_ready,
        "download_failed": any(record["action"] == "failed" for record in file_records),
    }


def count_records(records: list[dict[str, Any]], include_sequence: bool) -> dict[str, Any]:
    by_action: Counter[str] = Counter()
    by_group: Counter[str] = Counter()
    for scan in records:
        by_action.update(record["action"] for record in scan["files"])
        by_group.update(
            f"{record['group']}:{'ready' if record['after']['ready'] else 'missing'}"
            for record in scan["files"]
        )
    return {
        "scans": len(records),
        "geometry_ready_scans": sum(1 for scan in records if scan["geometry_ready"]),
        "sequence_zip_ready_scans": (
            sum(1 for scan in records if scan["sequence_zip_ready"]) if include_sequence else None
        ),
        "payload_ready_scans": sum(1 for scan in records if scan["payload_ready"]),
        "download_failed_scans": sum(1 for scan in records if scan["download_failed"]),
        "files": sum(len(scan["files"]) for scan in records),
        "ready_files": sum(
            1 for scan in records for record in scan["files"] if record["after"]["ready"]
        ),
        "missing_files": sum(
            1 for scan in records for record in scan["files"] if not record["after"]["ready"]
        ),
        "actions": dict(sorted(by_action.items())),
        "file_groups": dict(sorted(by_group.items())),
    }


def blocker_records(records: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for scan in records:
        missing = [
            f"{record['group']}:{record['file']}"
            for record in scan["files"]
            if not record["after"]["ready"]
        ]
        if missing:
            blockers.append(f"{scan['scan_id']}:missing:{','.join(missing)}")
    return blockers


def make_report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    blockers = manifest["blockers"]
    lines = [
        "# Payload Readiness",
        "",
        f"Generated: {manifest['generated_at']}",
        f"Status: `{manifest['status']}`",
        f"Download missing: `{manifest['download_missing']}`",
        "",
        "## Scope",
        "",
        f"- selected scans file: `{manifest['selected_scans_file']}`",
        f"- total selected scans: `{manifest['total_selected_scans']}`",
        f"- audited scans: `{counts['scans']}`",
        f"- offset: `{manifest['batch']['offset']}`",
        f"- limit: `{manifest['batch']['limit']}`",
        "",
        "## Counts",
        "",
        f"- geometry ready scans: `{counts['geometry_ready_scans']} / {counts['scans']}`",
        f"- sequence.zip ready scans: `{counts['sequence_zip_ready_scans']} / {counts['scans']}`",
        f"- payload ready scans: `{counts['payload_ready_scans']} / {counts['scans']}`",
        f"- ready files: `{counts['ready_files']}`",
        f"- missing files: `{counts['missing_files']}`",
        f"- download failed scans: `{counts['download_failed_scans']}`",
        f"- actions: `{counts['actions']}`",
        "",
        "## Blockers",
        "",
    ]
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers[:40])
        if len(blockers) > 40:
            lines.append(f"- ... {len(blockers) - 40} more")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Next",
            "",
            "1. For an actual payload batch, run this script with `--download-missing --limit N --offset M`.",
            "2. Re-run `tools/stage_vlsat.py` with the same selected scan list and hardened staged root.",
            "3. Run `tools/prep_multiview.py --extract`, then generate `multi_view` and re-run the staged layout checker.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    all_scan_ids, active_scan_ids = selected_scan_ids(args)
    records: list[dict[str, Any]] = []
    for scan_id in active_scan_ids:
        record = scan_record(
            scan_id=scan_id,
            dataset_root=args.dataset_root.resolve(),
            include_sequence=args.include_sequence,
            download_missing=args.download_missing,
            overwrite_empty=args.overwrite_empty,
            base_url=args.download_base_url,
            timeout=args.timeout,
        )
        records.append(record)
        if args.stop_on_error and record["download_failed"]:
            break

    blockers = blocker_records(records)
    status = "ready" if records and not blockers else "blocked"
    manifest = {
        "generated_at": now_iso(),
        "schema_version": "h001_payload_readiness_v1",
        "status": status,
        "scope_name": "h001_validation_hardened",
        "dataset_root": relpath(args.dataset_root),
        "selected_scans_file": relpath(args.selected_scans.resolve()),
        "output_dir": relpath(args.output_dir.resolve()),
        "total_selected_scans": len(all_scan_ids),
        "audited_scan_ids": active_scan_ids,
        "download_missing": args.download_missing,
        "download_base_url": args.download_base_url,
        "include_sequence": args.include_sequence,
        "required_files": {
            "geometry": list(GEOMETRY_FILES),
            "sequence": list(SEQUENCE_FILES) if args.include_sequence else [],
        },
        "batch": {
            "offset": args.offset,
            "limit": args.limit,
            "explicit_scan_ids": args.scan_id or [],
        },
        "counts": count_records(records, args.include_sequence),
        "records": records,
        "blockers": blockers,
        "notes": [
            "Large payload files are stored under local_dataset/3RScan/scans/.",
            "This script does not extract sequence.zip, create aligned PLY, generate multi_view, or run VL-SAT.",
        ],
    }

    output_dir = args.output_dir.resolve()
    write_json(output_dir / "payload_manifest.json", manifest)
    (output_dir / "payload_report.md").write_text(make_report(manifest), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "audited_scans": manifest["counts"]["scans"],
                "geometry_ready": manifest["counts"]["geometry_ready_scans"],
                "sequence_zip_ready": manifest["counts"]["sequence_zip_ready_scans"],
                "payload_ready": manifest["counts"]["payload_ready_scans"],
                "missing_files": manifest["counts"]["missing_files"],
                "blockers": len(blockers),
                "output_dir": relpath(output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
