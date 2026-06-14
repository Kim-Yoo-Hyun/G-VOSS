#!/usr/bin/env python3
"""Create VL-SAT aligned PLY files for selected H001 scans."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_validation_hardened" / "scans.txt"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "layout" / "vlsat" / "hardened"

RAW_PLY = "labels.instances.annotated.v2.ply"
ALIGNED_PLY = "labels.instances.align.annotated.v2.ply"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create aligned PLY files for selected reference/rescan 3RScan payloads."
    )
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--scan-id", action="append", default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def selected_scan_ids(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    all_ids = unique_preserve_order(args.scan_id or read_lines(args.selected_scans))
    if args.scan_id:
        return all_ids, all_ids
    start = max(args.offset, 0)
    end = None if args.limit is None else start + max(args.limit, 0)
    return all_ids, all_ids[start:end]


def load_metadata(dataset_root: Path) -> dict[str, dict[str, Any]]:
    metadata_path = dataset_root / "3RScan" / "files" / "3RScan.json"
    with metadata_path.open("r", encoding="utf-8") as handle:
        scenes = json.load(handle)

    records: dict[str, dict[str, Any]] = {}
    for scene in scenes:
        reference = str(scene.get("reference", "")).strip()
        if reference:
            records[reference] = {
                "scan_id": reference,
                "group_reference": reference,
                "is_reference": True,
                "transform": None,
            }
        for scan in scene.get("scans", []):
            scan_id = str(scan.get("reference", "")).strip()
            if not scan_id:
                continue
            records[scan_id] = {
                "scan_id": scan_id,
                "group_reference": reference,
                "is_reference": scan_id == reference,
                "transform": scan.get("transform"),
            }
    return records


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def transform_point(parts: list[str], matrix: list[float]) -> list[str]:
    x, y, z = (float(parts[0]), float(parts[1]), float(parts[2]))
    vec = (x, y, z, 1.0)
    out = [sum(vec[row] * matrix[row * 4 + col] for row in range(4)) for col in range(3)]
    return [f"{value:.9g}" for value in out] + parts[3:]


def transform_ascii_ply(source: Path, target: Path, matrix: list[float]) -> None:
    fd, tmp_name = tempfile.mkstemp(dir=str(target.parent), prefix=f".{target.name}.", suffix=".tmp")
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        with source.open("r", encoding="ascii", errors="strict") as src, tmp_path.open(
            "w", encoding="ascii", newline="\n"
        ) as dst:
            vertex_count: int | None = None
            header_lines: list[str] = []
            for line in src:
                header_lines.append(line)
                stripped = line.strip()
                if stripped.startswith("element vertex "):
                    vertex_count = int(stripped.split()[-1])
                if stripped == "end_header":
                    break

            if vertex_count is None:
                raise RuntimeError(f"{source}: missing vertex count in PLY header")
            if not any(line.strip() == "format ascii 1.0" for line in header_lines):
                raise RuntimeError(f"{source}: only ASCII PLY is supported")

            dst.writelines(header_lines)
            for _ in range(vertex_count):
                line = src.readline()
                if not line:
                    raise RuntimeError(f"{source}: unexpected EOF in vertex block")
                parts = line.strip().split()
                if len(parts) < 3:
                    raise RuntimeError(f"{source}: malformed vertex row")
                dst.write(" ".join(transform_point(parts, matrix)) + "\n")

            shutil.copyfileobj(src, dst)
        os.replace(tmp_path, target)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def align_scan(scan_id: str, *, dataset_root: Path, metadata: dict[str, dict[str, Any]], overwrite: bool) -> dict[str, Any]:
    scan_dir = dataset_root / "3RScan" / "scans" / scan_id
    raw = scan_dir / RAW_PLY
    aligned = scan_dir / ALIGNED_PLY
    record = metadata.get(scan_id, {})
    is_reference = bool(record.get("is_reference"))
    transform = record.get("transform")

    if aligned.exists() and not overwrite:
        status = "already_present"
    elif not raw.exists():
        status = "missing_raw_ply"
    elif is_reference:
        aligned.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(raw, aligned)
        status = "reference_copied"
    elif isinstance(transform, list) and len(transform) == 16:
        aligned.parent.mkdir(parents=True, exist_ok=True)
        transform_ascii_ply(raw, aligned, [float(value) for value in transform])
        status = "rescan_transformed"
    elif scan_id not in metadata:
        status = "missing_metadata"
    else:
        status = "missing_transform"

    return {
        "scan_id": scan_id,
        "scan_dir": rel(scan_dir),
        "raw_ply": rel(raw),
        "aligned_ply": rel(aligned),
        "group_reference": record.get("group_reference"),
        "is_reference": is_reference,
        "has_transform": isinstance(transform, list) and len(transform) == 16,
        "status": status,
        "raw_exists": raw.exists(),
        "aligned_exists": aligned.exists(),
        "aligned_ready": aligned.exists() and aligned.is_file() and aligned.stat().st_size > 0,
    }


def make_report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    lines = [
        "# Aligned PLY",
        "",
        f"Generated: {manifest['generated_at']}",
        f"Status: `{manifest['status']}`",
        "",
        "## Counts",
        "",
        f"- total selected scans: `{manifest['total_selected_scans']}`",
        f"- processed scans: `{counts['processed_scans']}`",
        f"- aligned ready scans: `{counts['aligned_ready_scans']}`",
        f"- reference copied: `{counts['reference_copied']}`",
        f"- rescan transformed: `{counts['rescan_transformed']}`",
        f"- already present: `{counts['already_present']}`",
        f"- blocked scans: `{counts['blocked_scans']}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = manifest["blockers"]
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers[:40])
    else:
        lines.append("- none")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    dataset_root = args.dataset_root.resolve()
    all_scan_ids, active_scan_ids = selected_scan_ids(args)
    metadata = load_metadata(dataset_root)
    records = [
        align_scan(scan_id, dataset_root=dataset_root, metadata=metadata, overwrite=args.overwrite)
        for scan_id in active_scan_ids
    ]
    blockers = [
        f"{record['scan_id']}:{record['status']}"
        for record in records
        if not record["aligned_ready"]
    ]
    counts = {
        "processed_scans": len(records),
        "aligned_ready_scans": sum(1 for record in records if record["aligned_ready"]),
        "reference_copied": sum(1 for record in records if record["status"] == "reference_copied"),
        "rescan_transformed": sum(1 for record in records if record["status"] == "rescan_transformed"),
        "already_present": sum(1 for record in records if record["status"] == "already_present"),
        "blocked_scans": len(blockers),
    }
    status = "ready" if records and not blockers else "blocked"
    manifest = {
        "generated_at": now_iso(),
        "schema_version": "h001_aligned_ply_v1",
        "status": status,
        "dataset_root": rel(dataset_root),
        "selected_scans_file": rel(args.selected_scans.resolve()),
        "total_selected_scans": len(all_scan_ids),
        "batch": {
            "offset": args.offset,
            "limit": args.limit,
            "explicit_scan_ids": args.scan_id or [],
        },
        "counts": counts,
        "records": records,
        "blockers": blockers,
        "notes": [
            "Transform semantics match VL-SAT data_processing/transform_ply.py: row-vector [x y z 1] multiplied by the 3RScan transform matrix.",
            "Only ASCII PLY input is supported by this lightweight H001 helper.",
        ],
    }
    output_dir = args.output_dir.resolve()
    write_json(output_dir / "aligned_manifest.json", manifest)
    (output_dir / "aligned_report.md").write_text(make_report(manifest), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "processed_scans": counts["processed_scans"],
                "aligned_ready": counts["aligned_ready_scans"],
                "reference_copied": counts["reference_copied"],
                "rescan_transformed": counts["rescan_transformed"],
                "blockers": counts["blocked_scans"],
                "output_dir": rel(output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
