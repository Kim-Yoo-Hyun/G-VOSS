#!/usr/bin/env python3
"""Prepare sequence directories and generate VL-SAT multi_view features."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT

DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_mini" / "scans.txt"
DEFAULT_ARTIFACT_DIR = H001_ROOT / "artifacts" / "layout" / "vlsat"
DEFAULT_STAGED_ROOT = DEFAULT_DATASET_ROOT / "VLSAT_staged" / "CVPR2023-VLSAT"
DEFAULT_SOURCE_SCAN_ROOT = DEFAULT_DATASET_ROOT / "3RScan" / "scans"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract selected 3RScan sequence.zip files for VL-SAT multi_view generation."
    )
    parser.add_argument("--source-scan-root", type=Path, default=DEFAULT_SOURCE_SCAN_ROOT)
    parser.add_argument("--staged-root", type=Path, default=DEFAULT_STAGED_ROOT)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Extract sequence.zip into source scan sequence/ directories.",
    )
    parser.add_argument(
        "--overwrite-sequence",
        action="store_true",
        help="Replace existing source sequence/ directories before extraction.",
    )
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def count_files(path: Path, pattern: str) -> int:
    if not path.is_dir():
        return 0
    return sum(1 for _ in path.glob(pattern))


def read_frame_count(info_path: Path) -> int | None:
    if not info_path.exists():
        return None
    for line in info_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip().startswith("m_frames.size"):
            try:
                return int(line.strip().split()[-1])
            except ValueError:
                return None
    return None


def safe_extract_sequence(zip_path: Path, sequence_dir: Path, overwrite: bool) -> dict[str, Any]:
    if not zip_path.exists():
        return {"status": "missing_zip", "zip_path": rel(zip_path), "sequence_dir": rel(sequence_dir)}
    if sequence_dir.exists():
        if not overwrite:
            return {"status": "already_present", "zip_path": rel(zip_path), "sequence_dir": rel(sequence_dir)}
        shutil.rmtree(sequence_dir)

    sequence_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        bad = zf.testzip()
        if bad is not None:
            return {
                "status": "bad_zip_member",
                "zip_path": rel(zip_path),
                "sequence_dir": rel(sequence_dir),
                "bad_member": bad,
            }
        for member in zf.infolist():
            target = sequence_dir / member.filename
            resolved = target.resolve()
            if sequence_dir.resolve() not in resolved.parents and resolved != sequence_dir.resolve():
                raise RuntimeError(f"unsafe zip member path: {member.filename}")
        zf.extractall(sequence_dir)
    return {"status": "extracted", "zip_path": rel(zip_path), "sequence_dir": rel(sequence_dir)}


def link_or_copy_sequence(source_sequence: Path, staged_sequence: Path) -> dict[str, Any]:
    if not source_sequence.exists():
        return {
            "status": "missing_source",
            "source": rel(source_sequence),
            "target": rel(staged_sequence),
            "target_exists": staged_sequence.exists(),
        }
    if staged_sequence.exists() or staged_sequence.is_symlink():
        return {
            "status": "already_present",
            "source": rel(source_sequence),
            "target": rel(staged_sequence),
            "target_exists": True,
        }
    staged_sequence.parent.mkdir(parents=True, exist_ok=True)
    staged_sequence.symlink_to(source_sequence.resolve(), target_is_directory=True)
    return {
        "status": "staged",
        "source": rel(source_sequence),
        "target": rel(staged_sequence),
        "target_exists": staged_sequence.exists(),
    }


def inspect_sequence(sequence_dir: Path) -> dict[str, Any]:
    info_path = sequence_dir / "_info.txt"
    frame_count = read_frame_count(info_path)
    color_count = count_files(sequence_dir, "frame-*.color.jpg")
    pose_count = count_files(sequence_dir, "frame-*.pose.txt")
    depth_count = count_files(sequence_dir, "frame-*.depth.pgm")
    ready = bool(frame_count) and color_count > 0 and pose_count > 0 and color_count == pose_count
    if frame_count is not None:
        ready = ready and color_count <= frame_count and pose_count <= frame_count
    return {
        "sequence_dir": rel(sequence_dir),
        "exists": sequence_dir.is_dir(),
        "info_exists": info_path.exists(),
        "frame_count_declared": frame_count,
        "color_frame_count": color_count,
        "pose_frame_count": pose_count,
        "depth_frame_count": depth_count,
        "ready_for_pointcloud2image": ready,
    }


def dependency_status() -> dict[str, Any]:
    code = (
        "import importlib.util, json;"
        "mods=['torch','clip','trimesh','numpy','PIL','matplotlib'];"
        "print(json.dumps({m: importlib.util.find_spec(m) is not None for m in mods}, sort_keys=True))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        return {"check_status": "failed", "stderr": result.stderr.strip()}
    data = json.loads(result.stdout)
    return {"check_status": "ok", "modules": data, "missing": sorted(k for k, v in data.items() if not v)}


def build_report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    blockers = manifest["blockers"]
    lines = [
        "# Multi-View Prep",
        "",
        f"Generated: {manifest['generated_at']}",
        "",
        "## Verdict",
        "",
        f"- status: `{manifest['status']}`",
        f"- selected scans: `{counts['selected_scans']}`",
        f"- source sequence ready scans: `{counts['source_sequence_ready_scans']}`",
        f"- staged sequence ready scans: `{counts['staged_sequence_ready_scans']}`",
        f"- multi_view ready scans: `{counts['multi_view_ready_scans']}`",
        "",
        "## Blockers",
        "",
    ]
    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- none")
    lines.extend(["", "## Dependency Check", ""])
    deps = manifest["dependency_status"]
    if deps.get("check_status") == "ok":
        missing = deps.get("missing", [])
        lines.append(f"- missing modules: `{', '.join(missing) if missing else 'none'}`")
    else:
        lines.append(f"- dependency check failed: `{deps.get('stderr', '')}`")
    lines.extend(["", "## Per-Scan Status", ""])
    for scan in manifest["scan_records"]:
        source = scan["source_sequence"]
        staged = scan["staged_sequence"]
        lines.append(
            "- `{scan_id}`: source_sequence=`{source_ready}`, staged_sequence=`{staged_ready}`, multi_view_files=`{multi_view_files}`".format(
                scan_id=scan["scan_id"],
                source_ready=str(source["ready_for_pointcloud2image"]).lower(),
                staged_ready=str(staged["ready_for_pointcloud2image"]).lower(),
                multi_view_files=scan["multi_view_file_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Next",
            "",
            "1. Resolve any blockers listed above.",
            "2. If status is `ready`, re-run `tools/stage_vlsat.py` and staged `tools/check_layout.py`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    source_scan_root = args.source_scan_root.resolve()
    staged_scan_root = args.staged_root.resolve() / "data" / "3RScan"
    selected_scans = read_lines(args.selected_scans.resolve())

    scan_records: list[dict[str, Any]] = []
    extraction_counter: Counter[str] = Counter()
    for scan_id in selected_scans:
        source_scan_dir = source_scan_root / scan_id
        staged_scan_dir = staged_scan_root / scan_id
        source_sequence = source_scan_dir / "sequence"
        staged_sequence = staged_scan_dir / "sequence"
        extraction = {"status": "not_requested"}
        if args.extract:
            extraction = safe_extract_sequence(
                source_scan_dir / "sequence.zip",
                source_sequence,
                overwrite=args.overwrite_sequence,
            )
        extraction_counter[extraction["status"]] += 1
        sequence_stage = link_or_copy_sequence(source_sequence, staged_sequence)
        source_sequence_status = inspect_sequence(source_sequence)
        staged_sequence_status = inspect_sequence(staged_sequence)
        multi_view_dir = staged_scan_dir / "multi_view"
        scan_records.append(
            {
                "scan_id": scan_id,
                "source_scan_dir": rel(source_scan_dir),
                "staged_scan_dir": rel(staged_scan_dir),
                "extraction": extraction,
                "sequence_stage": sequence_stage,
                "source_sequence": source_sequence_status,
                "staged_sequence": staged_sequence_status,
                "multi_view_dir": rel(multi_view_dir),
                "multi_view_file_count": count_files(multi_view_dir, "*.npy"),
            }
        )

    deps = dependency_status()
    counts = {
        "selected_scans": len(selected_scans),
        "source_sequence_ready_scans": sum(
            1 for record in scan_records if record["source_sequence"]["ready_for_pointcloud2image"]
        ),
        "staged_sequence_ready_scans": sum(
            1 for record in scan_records if record["staged_sequence"]["ready_for_pointcloud2image"]
        ),
        "multi_view_ready_scans": sum(1 for record in scan_records if record["multi_view_file_count"] > 0),
        "extraction_status": dict(sorted(extraction_counter.items())),
    }
    blockers: list[str] = []
    if counts["staged_sequence_ready_scans"] < counts["selected_scans"]:
        blockers.append("staged sequence directories are not ready for every selected scan")
    if deps.get("missing"):
        blockers.append("Python environment is missing required multi_view generation dependencies")
    if counts["multi_view_ready_scans"] < counts["selected_scans"]:
        blockers.append("multi_view features are not generated for every selected scan")

    if blockers:
        status = "ready_for_generation" if len(blockers) == 1 and "multi_view" in blockers[0] else "blocked"
    else:
        status = "ready"

    manifest = {
        "generated_at": now_iso(),
        "prep_version": "vlsat-multiview-prep-v1",
        "status": status,
        "source_scan_root": str(source_scan_root),
        "staged_scan_root": str(staged_scan_root),
        "selected_scans_file": rel(args.selected_scans.resolve()),
        "selected_scans": selected_scans,
        "dependency_status": deps,
        "counts": counts,
        "blockers": blockers,
        "scan_records": scan_records,
    }
    output_dir = args.artifact_dir.resolve()
    write_json(output_dir / "multiview_manifest.json", manifest)
    write_text(output_dir / "multiview_report.md", build_report(manifest))

    print(f"status={manifest['status']}")
    print(f"source_sequence_ready_scans={counts['source_sequence_ready_scans']}")
    print(f"staged_sequence_ready_scans={counts['staged_sequence_ready_scans']}")
    print(f"multi_view_ready_scans={counts['multi_view_ready_scans']}")
    print(f"report={rel(output_dir / 'multiview_report.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
