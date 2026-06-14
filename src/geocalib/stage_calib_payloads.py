#!/usr/bin/env python3
"""Audit or download H001-Calib-Pilot geometry payloads."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import urllib.error
import urllib.request
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_PILOT_ROOT = H001_ROOT / "artifacts" / "subset" / "h001_calib_pilot"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "calibration" / "train_dev_payload"

BASE_URL = "http://campar.in.tum.de/public_datasets/3RScan/Dataset"
GEOMETRY_FILES = (
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit/download H001-Calib-Pilot train/dev geometry payloads."
    )
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--pilot-root", type=Path, default=DEFAULT_PILOT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--overwrite-empty", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--stop-on-error", action="store_true")
    parser.add_argument("--download-base-url", default=BASE_URL)
    parser.add_argument("--timeout", type=int, default=120)
    return parser.parse_args()


def read_scan_list(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


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
    role: str,
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
    elif before["exists"] and before["size_bytes"] == 0 and overwrite_empty:
        path.unlink()
        before = file_status(path)
        action = "removed_empty"

    if not before["ready"] and download_missing:
        url = f"{base_url.rstrip('/')}/{scan_id}/{filename}"
        action, error = download_file(url, path, timeout)

    after = file_status(path)
    return {
        "scan_id": scan_id,
        "role": role,
        "file": filename,
        "path": relpath(path),
        "before": before,
        "after": after,
        "action": action,
        "error": error,
    }


def scan_record(
    *,
    scan_id: str,
    role: str,
    dataset_root: Path,
    download_missing: bool,
    overwrite_empty: bool,
    base_url: str,
    timeout: int,
) -> dict[str, Any]:
    scan_dir = dataset_root / "3RScan" / "scans" / scan_id
    file_records = [
        handle_file(
            scan_id=scan_id,
            role=role,
            filename=filename,
            scan_dir=scan_dir,
            download_missing=download_missing,
            overwrite_empty=overwrite_empty,
            base_url=base_url,
            timeout=timeout,
        )
        for filename in GEOMETRY_FILES
    ]
    return {
        "scan_id": scan_id,
        "role": role,
        "scan_dir": relpath(scan_dir),
        "files": file_records,
        "geometry_ready": all(record["after"]["ready"] for record in file_records),
        "download_failed": any(record["action"] == "failed" for record in file_records),
    }


def role_counts(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_action: Counter[str] = Counter()
    for scan in records:
        by_action.update(record["action"] for record in scan["files"])
    return {
        "scans": len(records),
        "geometry_ready_scans": sum(1 for scan in records if scan["geometry_ready"]),
        "download_failed_scans": sum(1 for scan in records if scan["download_failed"]),
        "files": sum(len(scan["files"]) for scan in records),
        "ready_files": sum(
            1 for scan in records for record in scan["files"] if record["after"]["ready"]
        ),
        "missing_files": sum(
            1 for scan in records for record in scan["files"] if not record["after"]["ready"]
        ),
        "actions": dict(sorted(by_action.items())),
    }


def make_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Train/Dev Payload",
        "",
        f"Last updated: {manifest['created_at']}",
        f"Status: `{manifest['status']}`",
        f"Download missing: `{manifest['download_missing']}`",
        "",
        "## Counts",
        "",
        "| Role | Scans | Geometry ready | Failed scans | Ready files | Missing files |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for role in ("train", "dev"):
        counts = manifest["counts"][role]
        lines.append(
            "| {role} | {scans} | {ready} | {failed} | {ready_files} | {missing_files} |".format(
                role=role,
                scans=counts["scans"],
                ready=counts["geometry_ready_scans"],
                failed=counts["download_failed_scans"],
                ready_files=counts["ready_files"],
                missing_files=counts["missing_files"],
            )
        )

    lines.extend(["", "## Actions", ""])
    for role in ("train", "dev"):
        actions = manifest["counts"][role]["actions"]
        lines.append(f"- `{role}`: `{actions}`")

    blockers = manifest["blockers"]
    lines.extend(["", "## Blockers", ""])
    if blockers:
        for blocker in blockers[:30]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Next",
            "",
            "1. If status is `ready`, run `tools/export_calibration.py` for `train_dev_calib`.",
            "2. If blocked, retry failed downloads or choose a smaller fallback split.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    train_scans_path = args.pilot_root / "train_scans.txt"
    dev_scans_path = args.pilot_root / "dev_scans.txt"
    missing_inputs = [path for path in (train_scans_path, dev_scans_path) if not path.exists()]
    if missing_inputs:
        print(json.dumps({"status": "blocked", "missing_inputs": [relpath(p) for p in missing_inputs]}))
        return 2

    train_ids = read_scan_list(train_scans_path)
    dev_ids = read_scan_list(dev_scans_path)
    train_records = [
        scan_record(
            scan_id=scan_id,
            role="train",
            dataset_root=args.dataset_root,
            download_missing=args.download_missing,
            overwrite_empty=args.overwrite_empty,
            base_url=args.download_base_url,
            timeout=args.timeout,
        )
        for scan_id in train_ids
    ]
    dev_records = [
        scan_record(
            scan_id=scan_id,
            role="dev",
            dataset_root=args.dataset_root,
            download_missing=args.download_missing,
            overwrite_empty=args.overwrite_empty,
            base_url=args.download_base_url,
            timeout=args.timeout,
        )
        for scan_id in dev_ids
    ]

    blockers = []
    for scan in [*train_records, *dev_records]:
        if not scan["geometry_ready"]:
            missing = [
                record["file"]
                for record in scan["files"]
                if not record["after"]["ready"]
            ]
            blockers.append(f"{scan['role']}:{scan['scan_id']}:missing:{','.join(missing)}")

    status = "ready" if not blockers else "blocked"
    manifest = {
        "schema_version": "h001_calib_payload_manifest_v1",
        "created_at": date.today().isoformat(),
        "status": status,
        "split_name": "train_dev_calib",
        "dataset_root": relpath(args.dataset_root),
        "pilot_root": relpath(args.pilot_root),
        "output_dir": relpath(args.output_dir),
        "download_missing": args.download_missing,
        "required_files": list(GEOMETRY_FILES),
        "counts": {
            "train": role_counts(train_records),
            "dev": role_counts(dev_records),
            "all": role_counts([*train_records, *dev_records]),
        },
        "records": {
            "train": train_records,
            "dev": dev_records,
        },
        "blockers": blockers,
        "notes": [
            "Large geometry payload files are stored under local_dataset/3RScan/scans/.",
            "This artifact only records audit/download status for the H001-Calib-Pilot train/dev split.",
        ],
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "manifest.json", manifest)
    (args.output_dir / "report.md").write_text(make_report(manifest), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "train_ready": manifest["counts"]["train"]["geometry_ready_scans"],
                "dev_ready": manifest["counts"]["dev"]["geometry_ready_scans"],
                "missing_files": manifest["counts"]["all"]["missing_files"],
                "blockers": len(blockers),
                "output_dir": relpath(args.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
