#!/usr/bin/env python3
"""Stage H001 held-out 3RScan scan symlinks for Open3DSG eval feature dumping."""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_eval_payload_stage_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime"),
    )
    parser.add_argument("--raw-scans-root", type=Path, default=Path("local_dataset/3RScan/scans"))
    parser.add_argument(
        "--selected-scans",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/subset/"
            "h001_validation_hardened/scans.txt"
        ),
    )
    parser.add_argument(
        "--relationships-validation",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime/data/3RScan/3DSSG_subset/relationships_validation.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/h001_eval_payload"),
    )
    parser.add_argument("--write", action="store_true")
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_scan_ids(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True))
            handle.write("\n")


def symlink_record(repo_root: Path, src: Path, dst: Path) -> dict[str, Any]:
    record: dict[str, Any] = {
        "src": relpath(repo_root, src),
        "dst": relpath(repo_root, dst),
        "src_exists": src.is_dir(),
    }
    if not src.is_dir():
        record["status"] = "missing_source"
        return record
    dst.parent.mkdir(parents=True, exist_ok=True)
    relative_target = os.path.relpath(src.resolve(), dst.parent.resolve())
    if dst.is_symlink():
        current = os.readlink(dst)
        if current == relative_target:
            record["status"] = "ready_symlink"
        else:
            dst.unlink()
            dst.symlink_to(relative_target, target_is_directory=True)
            record["status"] = "normalized_symlink"
        return record
    if dst.exists():
        record["status"] = "ready_existing_path" if dst.is_dir() else "blocked_existing_non_dir"
        return record
    dst.symlink_to(relative_target, target_is_directory=True)
    record["status"] = "created_symlink"
    return record


def sequence_summary(scan_dir: Path) -> dict[str, Any]:
    sequence_dir = scan_dir / "sequence"
    color_count = len(list(sequence_dir.glob("*.color.jpg"))) if sequence_dir.is_dir() else 0
    return {
        "sequence_dir_exists": sequence_dir.is_dir(),
        "color_frames": color_count,
        "info_exists": (sequence_dir / "_info.txt").is_file(),
        "frame_000000_color": (sequence_dir / "frame-000000.color.jpg").is_file(),
    }


def make_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG H001 Eval Payload",
        "",
        f"Created at: `{payload['created_at']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Counts",
        "",
        f"- selected scans: `{payload['counts']['selected_scans']}`",
        f"- validation contexts: `{payload['counts']['validation_contexts']}`",
        f"- linked scans: `{payload['counts']['linked_scans']}`",
        f"- sequence-ready scans: `{payload['counts']['sequence_ready_scans']}`",
        "",
        "## Paths",
        "",
        f"- runtime 3RScan root: `{payload['paths']['runtime_r3scan_root']}`",
        f"- raw scans root: `{payload['paths']['raw_scans_root']}`",
        f"- records: `{payload['paths']['records']}`",
    ]
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in payload["blockers"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    runtime_root = resolve(repo_root, args.runtime_root).resolve()
    raw_scans_root = resolve(repo_root, args.raw_scans_root).resolve()
    selected_scans_path = resolve(repo_root, args.selected_scans)
    relationships_path = resolve(repo_root, args.relationships_validation)
    out_dir = resolve(repo_root, args.out)

    selected_scans = read_scan_ids(selected_scans_path)
    validation_rows = load_json(relationships_path).get("scans", [])
    validation_scans = {str(row.get("scan")) for row in validation_rows if row.get("scan")}
    target_scans = sorted(selected_scans & validation_scans)
    runtime_r3scan_root = runtime_root / "data/3RScan"

    records: list[dict[str, Any]] = []
    for scan_id in target_scans:
        src = raw_scans_root / scan_id
        dst = runtime_r3scan_root / scan_id
        record = {"scan_id": scan_id, **symlink_record(repo_root, src, dst)}
        record.update(sequence_summary(dst))
        records.append(record)

    status_counts = Counter(record["status"] for record in records)
    linked = sum(1 for record in records if record["status"] in {"created_symlink", "ready_symlink", "normalized_symlink", "ready_existing_path"})
    sequence_ready = sum(1 for record in records if record["sequence_dir_exists"] and record["color_frames"] > 0)

    blockers: list[str] = []
    if len(target_scans) != len(selected_scans):
        blockers.append(f"selected_validation_scan_mismatch:{len(target_scans)}/{len(selected_scans)}")
    if linked != len(target_scans):
        blockers.append(f"linked_scans:{linked}/{len(target_scans)}")
    if sequence_ready != len(target_scans):
        blockers.append(f"sequence_ready_scans:{sequence_ready}/{len(target_scans)}")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": "ready" if not blockers else "blocked",
        "paths": {
            "runtime_r3scan_root": relpath(repo_root, runtime_r3scan_root),
            "raw_scans_root": relpath(repo_root, raw_scans_root),
            "selected_scans": relpath(repo_root, selected_scans_path),
            "relationships_validation": relpath(repo_root, relationships_path),
            "records": relpath(repo_root, out_dir / "records.jsonl"),
        },
        "counts": {
            "selected_scans": len(selected_scans),
            "validation_scan_ids": len(validation_scans),
            "validation_contexts": len(validation_rows),
            "target_scans": len(target_scans),
            "linked_scans": linked,
            "sequence_ready_scans": sequence_ready,
        },
        "link_status_counts": dict(status_counts),
        "blockers": blockers,
        "next_action": "Run dump_features_h001_eval after status is ready.",
    }

    if args.write:
        write_json(out_dir / "manifest.json", payload)
        write_jsonl(out_dir / "records.jsonl", records)
        (out_dir / "report.md").write_text(make_report(payload), encoding="utf-8")

    print(json.dumps({"status": payload["status"], "blockers": blockers}, sort_keys=True))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
