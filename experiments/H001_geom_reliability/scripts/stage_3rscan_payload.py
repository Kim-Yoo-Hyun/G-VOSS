#!/usr/bin/env python3
"""Download/audit the 3RScan payload needed by Open3DSG training_repro."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import shutil
import tempfile
import time
import urllib.error
import urllib.request
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_URL = "http://campar.in.tum.de/public_datasets/3RScan/Dataset"
TOU_URL = "http://campar.in.tum.de/public_datasets/3RScan/3RScanTOU.pdf"

RAW_FILES = (
    "labels.instances.annotated.v2.ply",
    "mesh.refined.0.010000.segs.v2.json",
    "semseg.v2.json",
)

OPEN3DSG_FILES = (
    "mesh.refined.v2.obj",
    "mesh.refined.mtl",
    "mesh.refined_0.png",
)

SEQUENCE_ZIP = "sequence.zip"

SEQUENCE_SENTINELS = (
    "sequence/_info.txt",
    "sequence/frame-000000.color.jpg",
    "sequence/frame-000000.depth.pgm",
    "sequence/frame-000000.pose.txt",
)

FILE_SETS = {
    "all": RAW_FILES + OPEN3DSG_FILES + (SEQUENCE_ZIP,),
    "raw": RAW_FILES,
    "mesh_texture": OPEN3DSG_FILES,
    "sequence": (SEQUENCE_ZIP,),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--training-repro-artifact",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/training_repro/records.jsonl"),
    )
    parser.add_argument("--scan-id", action="append", default=None)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--missing-only", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--file-set", choices=sorted(FILE_SETS), default="all")
    parser.add_argument("--download-missing", action="store_true")
    parser.add_argument("--extract-sequence", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/payload"),
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_under_repo(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    abs_path = path if path.is_absolute() else Path.cwd() / path
    try:
        return str(abs_path.resolve().relative_to(repo_root.resolve()))
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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def file_ready(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def sequence_ready(scan_dir: Path) -> bool:
    return all((scan_dir / sentinel).is_file() and (scan_dir / sentinel).stat().st_size > 0 for sentinel in SEQUENCE_SENTINELS)


def scan_needs(scan_dir: Path, file_set: str) -> bool:
    files = FILE_SETS[file_set]
    file_missing = any(not file_ready(scan_dir / filename) for filename in files if filename != SEQUENCE_ZIP)
    sequence_missing = SEQUENCE_ZIP in files and not sequence_ready(scan_dir)
    zip_missing = SEQUENCE_ZIP in files and not file_ready(scan_dir / SEQUENCE_ZIP)
    return file_missing or sequence_missing or zip_missing


def target_scans(args: argparse.Namespace, repo_root: Path) -> list[str]:
    if args.scan_id:
        return unique_preserve_order(args.scan_id)

    artifact = resolve_under_repo(repo_root, args.training_repro_artifact)
    rows = load_jsonl(artifact)
    scans = unique_preserve_order([str(row["scan"]) for row in rows if row.get("scan")])
    if args.missing_only:
        scans_root = repo_root / "local_dataset/3RScan/scans"
        scans = [scan_id for scan_id in scans if scan_needs(scans_root / scan_id, args.file_set)]
    start = max(args.offset, 0)
    end = None if args.limit is None else start + max(args.limit, 0)
    return scans[start:end]


def download_file(url: str, target: Path, timeout: int, retries: int) -> tuple[str, str | None]:
    target.parent.mkdir(parents=True, exist_ok=True)
    last_error = None
    for attempt in range(retries + 1):
        fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
        os.close(fd)
        tmp_path = Path(tmp_name)
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response, tmp_path.open("wb") as out:
                shutil.copyfileobj(response, out, length=1024 * 1024)
            if tmp_path.stat().st_size == 0:
                raise OSError("downloaded empty file")
            os.replace(tmp_path, target)
            return "downloaded", None
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            last_error = f"{type(exc).__name__}:{exc}"
            if tmp_path.exists():
                tmp_path.unlink()
            if attempt < retries:
                time.sleep(min(2**attempt, 8))
    return "failed", last_error


def handle_file(
    *,
    repo_root: Path,
    scan_id: str,
    filename: str,
    scans_root: Path,
    base_url: str,
    download_missing: bool,
    timeout: int,
    retries: int,
) -> dict[str, Any]:
    target = scans_root / scan_id / filename
    before_ready = file_ready(target)
    before_size = target.stat().st_size if target.exists() and target.is_file() else 0
    action = "already_ready" if before_ready else "audit_missing"
    error = None
    url = f"{base_url.rstrip('/')}/{scan_id}/{filename}"
    if not before_ready and download_missing:
        action, error = download_file(url, target, timeout=timeout, retries=retries)
    after_ready = file_ready(target)
    after_size = target.stat().st_size if target.exists() and target.is_file() else 0
    return {
        "kind": "file",
        "scan": scan_id,
        "file": filename,
        "url": url,
        "path": relpath(repo_root, target),
        "before_ready": before_ready,
        "before_size": before_size,
        "after_ready": after_ready,
        "after_size": after_size,
        "action": action,
        "error": error,
    }


def safe_zip_members(zip_file: zipfile.ZipFile) -> list[zipfile.ZipInfo]:
    members = []
    for info in zip_file.infolist():
        parts = Path(info.filename).parts
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise RuntimeError(f"unsafe zip member: {info.filename}")
        if Path(info.filename).is_absolute():
            raise RuntimeError(f"absolute zip member: {info.filename}")
        members.append(info)
    return members


def extract_sequence(repo_root: Path, scan_id: str, scan_dir: Path) -> dict[str, Any]:
    zip_path = scan_dir / SEQUENCE_ZIP
    sequence_dir = scan_dir / "sequence"
    before_ready = sequence_ready(scan_dir)
    if before_ready:
        return {
            "kind": "sequence",
            "scan": scan_id,
            "path": relpath(repo_root, sequence_dir),
            "before_ready": True,
            "after_ready": True,
            "action": "already_ready",
            "error": None,
        }
    if not file_ready(zip_path):
        return {
            "kind": "sequence",
            "scan": scan_id,
            "path": relpath(repo_root, sequence_dir),
            "before_ready": False,
            "after_ready": False,
            "action": "missing_sequence_zip",
            "error": None,
        }
    try:
        sequence_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as archive:
            members = safe_zip_members(archive)
            for info in members:
                parts = Path(info.filename).parts
                rel_parts = parts[1:] if parts and parts[0] == "sequence" else parts
                if not rel_parts:
                    continue
                target = sequence_dir.joinpath(*rel_parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info) as src, target.open("wb") as dst:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)
        after_ready = sequence_ready(scan_dir)
        return {
            "kind": "sequence",
            "scan": scan_id,
            "path": relpath(repo_root, sequence_dir),
            "before_ready": False,
            "after_ready": after_ready,
            "action": "extracted" if after_ready else "extracted_incomplete",
            "error": None if after_ready else "sentinel_files_missing_after_extract",
        }
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        return {
            "kind": "sequence",
            "scan": scan_id,
            "path": relpath(repo_root, sequence_dir),
            "before_ready": False,
            "after_ready": sequence_ready(scan_dir),
            "action": "extract_failed",
            "error": f"{type(exc).__name__}:{exc}",
        }


def scan_summary(scans_root: Path, scans: list[str]) -> dict[str, Any]:
    return {
        "scans": len(scans),
        "scan_dirs_ready": sum(1 for scan_id in scans if (scans_root / scan_id).is_dir()),
        "raw_files": {name: sum(1 for scan_id in scans if file_ready(scans_root / scan_id / name)) for name in RAW_FILES},
        "mesh_texture_files": {
            name: sum(1 for scan_id in scans if file_ready(scans_root / scan_id / name)) for name in OPEN3DSG_FILES
        },
        "sequence_zip_ready": sum(1 for scan_id in scans if file_ready(scans_root / scan_id / SEQUENCE_ZIP)),
        "sequence_ready": sum(1 for scan_id in scans if sequence_ready(scans_root / scan_id)),
    }


def build_manifest(
    *,
    args: argparse.Namespace,
    repo_root: Path,
    scans: list[str],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    scans_root = repo_root / "local_dataset/3RScan/scans"
    actions = Counter(record["action"] for record in records)
    file_failures = [record for record in records if record["kind"] == "file" and not record["after_ready"]]
    sequence_failures = [record for record in records if record["kind"] == "sequence" and not record["after_ready"]]
    status = "payload_audit_ready"
    if args.download_missing:
        status = "payload_download_batch_complete" if not file_failures and not sequence_failures else "payload_download_batch_incomplete"
    if not scans:
        status = "payload_no_target_scans"
    return {
        "schema_version": "h001_open3dsg_3rscan_payload_v1",
        "date_checked": now_iso(),
        "status": status,
        "tou_url": TOU_URL,
        "download_missing": args.download_missing,
        "extract_sequence": args.extract_sequence,
        "file_set": args.file_set,
        "base_url": args.base_url,
        "processed_scan_count": len(scans),
        "processed_scans": scans,
        "actions": dict(sorted(actions.items())),
        "file_failures": file_failures[:100],
        "sequence_failures": sequence_failures[:100],
        "processed_summary": scan_summary(scans_root, scans),
        "global_training_repro_summary": global_training_summary(repo_root),
        "next_action": "Re-run open3dsg_train_root, then continue payload batches until train scan dirs, mesh/texture, and sequence readiness reach 1178/1178.",
    }


def global_training_summary(repo_root: Path) -> dict[str, Any]:
    train_manifest = repo_root / "experiments/H001_geom_reliability/sources/open3dsg/training_repro/manifest.json"
    if not train_manifest.exists():
        return {"status": "missing_training_repro_manifest"}
    payload = json.loads(train_manifest.read_text(encoding="utf-8"))
    return {
        "status": payload.get("status"),
        "official_train": payload.get("official_train"),
        "train_dev_without_h001": payload.get("train_dev_without_h001"),
        "train_payload": payload.get("train_payload"),
        "train_dev_payload": payload.get("train_dev_payload"),
    }


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    summary = manifest["processed_summary"]
    lines = [
        "# 3RScan Payload Batch",
        "",
        f"Date: `{manifest['date_checked']}`",
        f"Status: `{manifest['status']}`",
        f"Download missing: `{manifest['download_missing']}`",
        f"Extract sequence: `{manifest['extract_sequence']}`",
        f"File set: `{manifest['file_set']}`",
        f"Processed scans: `{manifest['processed_scan_count']}`",
        "",
        "## Processed Readiness",
        "",
        f"- scan dirs: `{summary['scan_dirs_ready']}/{summary['scans']}`",
        f"- sequence zip: `{summary['sequence_zip_ready']}/{summary['scans']}`",
        f"- sequence extracted: `{summary['sequence_ready']}/{summary['scans']}`",
        "",
        "## Raw Files",
        "",
        "| File | Ready |",
        "| --- | ---: |",
    ]
    for name, count in summary["raw_files"].items():
        lines.append(f"| `{name}` | {count}/{summary['scans']} |")
    lines.extend(["", "## Mesh/Texture Files", "", "| File | Ready |", "| --- | ---: |"])
    for name, count in summary["mesh_texture_files"].items():
        lines.append(f"| `{name}` | {count}/{summary['scans']} |")
    lines.extend(["", "## Actions", ""])
    if manifest["actions"]:
        lines.extend(f"- `{action}`: `{count}`" for action, count in manifest["actions"].items())
    else:
        lines.append("- none")
    lines.extend(["", "## Failures", ""])
    failures = manifest["file_failures"] + manifest["sequence_failures"]
    if failures:
        lines.extend(f"- `{item.get('scan')}:{item.get('file', 'sequence')}:{item.get('action')}`" for item in failures[:40])
    else:
        lines.append("- none")
    lines.extend(["", "## Next Action", "", manifest["next_action"], ""])
    write_text(path, "\n".join(lines))


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve_under_repo(repo_root, args.out)
    scans_root = repo_root / "local_dataset/3RScan/scans"
    scans = target_scans(args, repo_root)
    files = FILE_SETS[args.file_set]

    tasks = []
    for scan_id in scans:
        for filename in files:
            tasks.append((scan_id, filename))

    records: list[dict[str, Any]] = []
    if tasks:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(args.workers, 1)) as executor:
            future_to_task = {
                executor.submit(
                    handle_file,
                    repo_root=repo_root,
                    scan_id=scan_id,
                    filename=filename,
                    scans_root=scans_root,
                    base_url=args.base_url,
                    download_missing=args.download_missing,
                    timeout=args.timeout,
                    retries=args.retries,
                ): (scan_id, filename)
                for scan_id, filename in tasks
            }
            for future in concurrent.futures.as_completed(future_to_task):
                records.append(future.result())

    if args.extract_sequence:
        for scan_id in scans:
            records.append(extract_sequence(repo_root, scan_id, scans_root / scan_id))

    records.sort(key=lambda row: (row.get("scan", ""), row.get("kind", ""), row.get("file", "")))
    manifest = build_manifest(args=args, repo_root=repo_root, scans=scans, records=records)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "manifest.json", manifest)
    write_jsonl(out_dir / "records.jsonl", records)
    write_report(out_dir / "report.md", manifest)

    status_path = repo_root / "experiments/H001_geom_reliability/sources/open3dsg/status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    status.update(
        {
            "schema_version": "h001_open3dsg_source_status_v4",
            "payload": "payload/manifest.json",
            "payload_status": manifest["status"],
            "next_gate": manifest["next_action"],
        }
    )
    write_json(status_path, status)

    print(json.dumps({"status": manifest["status"], "out": str(out_dir)}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
