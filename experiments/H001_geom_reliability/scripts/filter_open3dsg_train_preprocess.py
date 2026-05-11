#!/usr/bin/env python3
"""Filter Open3DSG split relationships whose preprocessed pickle is unavailable."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_preprocess_filter_v2"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--split", choices=("train", "validation"), default="train")
    parser.add_argument(
        "--staged-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/training_repro"),
    )
    parser.add_argument("--preprocess-manifest", type=Path, default=None)
    parser.add_argument("--retry-manifest", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.preprocess_manifest is None:
        args.preprocess_manifest = Path(
            f"experiments/H001_geom_reliability/sources/open3dsg/{args.split}_preprocess/manifest.json"
        )
    if args.retry_manifest is None:
        args.retry_manifest = Path(
            f"experiments/H001_geom_reliability/sources/open3dsg/{args.split}_preprocess_retry/manifest.json"
        )
    if args.out is None:
        args.out = Path(
            f"experiments/H001_geom_reliability/sources/open3dsg/{args.split}_preprocess_filter"
        )
    return args


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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def relationship_id(row: dict[str, Any]) -> str:
    return f"{row['scan']}-{str(hex(int(row['split'])))[-1]}"


def read_missing(preprocess_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    summary = preprocess_manifest.get("summary", {})
    rows = summary.get("failed_records", [])
    return [row for row in rows if row.get("action") == "missing_output"]


def count_relations(rows: list[dict[str, Any]]) -> int:
    return sum(len(row.get("relationships", [])) for row in rows)


def build_report(manifest: dict[str, Any]) -> str:
    split = manifest["split"]
    lines = [
        f"# Open3DSG {split.title()} Preprocess Filter",
        "",
        f"Created at: `{manifest['created_at']}`",
        f"Status: `{manifest['status']}`",
        f"Applied: `{manifest['applied']}`",
        "",
        "## Counts",
        "",
        f"- original {split} subgraphs: `{manifest['original']['subgraphs']}`",
        f"- kept {split} subgraphs: `{manifest['filtered']['subgraphs']}`",
        f"- removed {split} subgraphs: `{manifest['removed']['subgraphs']}`",
        f"- original {split} scans: `{manifest['original']['unique_scans']}`",
        f"- kept {split} scans: `{manifest['filtered']['unique_scans']}`",
        f"- removed-only scans: `{manifest['removed']['removed_only_scans']}`",
        f"- original relation annotations: `{manifest['original']['relations']}`",
        f"- kept relation annotations: `{manifest['filtered']['relations']}`",
        f"- removed relation annotations: `{manifest['removed']['relations']}`",
        "",
        "## Recoverability Check",
        "",
        f"- full preprocess missing rows: `{manifest['recoverability']['full_missing_count']}`",
        f"- `too few visible objects` log count: `{manifest['recoverability']['too_few_visible_log_count']}`",
        f"- retry manifest: `{manifest['recoverability']['retry_manifest']}`",
        f"- retry missing rows: `{manifest['recoverability']['retry_missing_count']}`",
        f"- decision: `{manifest['recoverability']['decision']}`",
        "",
        "## Runtime Files",
        "",
        f"- filtered relationships: `{manifest['outputs']['filtered_relationships']}`",
        f"- filtered scan list: `{manifest['outputs']['filtered_scans']}`",
        f"- missing rows: `{manifest['outputs']['missing_rows']}`",
        f"- removed rows: `{manifest['outputs']['removed_rows']}`",
    ]
    if manifest.get("applied"):
        lines.extend(
            [
                "",
                "## Applied Runtime Mutation",
                "",
                f"- runtime relationships file: `{manifest['applied_files']['relationships']}`",
                f"- runtime scans file: `{manifest['applied_files']['scans']}`",
                f"- backup relationships: `{manifest['applied_files']['relationships_backup']}`",
                f"- backup scans: `{manifest['applied_files']['scans_backup']}`",
            ]
        )
    lines.extend(["", "## Claim Limit", "", manifest["claim_limit"], ""])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    staged_root = resolve(repo_root, args.staged_root).resolve()
    out_dir = resolve(repo_root, args.out)
    preprocess_manifest_path = resolve(repo_root, args.preprocess_manifest)
    retry_manifest_path = resolve(repo_root, args.retry_manifest)

    subset_root = staged_root / "data/3RScan/3DSSG_subset"
    split = args.split
    relationships_path = subset_root / f"relationships_{split}.json"
    scans_path = subset_root / f"{split}_scans.txt"
    relationships_backup = subset_root / f"relationships_{split}.unfiltered.json"
    scans_backup = subset_root / f"{split}_scans.unfiltered.txt"
    source_relationships_path = relationships_backup if relationships_backup.exists() else relationships_path
    source_scans_path = scans_backup if scans_backup.exists() else scans_path
    relationships_payload = load_json(source_relationships_path)
    split_rows = relationships_payload.get("scans", [])
    preprocess_manifest = load_json(preprocess_manifest_path)
    missing_rows = read_missing(preprocess_manifest)
    missing_ids = {row["relationship_id"] for row in missing_rows}

    kept_rows = [row for row in split_rows if relationship_id(row) not in missing_ids]
    removed_rows = [row for row in split_rows if relationship_id(row) in missing_ids]
    kept_scans = sorted({row["scan"] for row in kept_rows})
    original_scans = sorted({row["scan"] for row in split_rows})
    removed_scans = sorted({row["scan"] for row in removed_rows})
    removed_only_scans = sorted(set(removed_scans) - set(kept_scans))

    filtered_relationships = dict(relationships_payload)
    filtered_relationships["scans"] = kept_rows

    out_dir.mkdir(parents=True, exist_ok=True)
    filtered_relationships_path = out_dir / f"relationships_{split}.filtered.json"
    filtered_scans_path = out_dir / f"{split}_scans.filtered.txt"
    missing_rows_path = out_dir / "missing.jsonl"
    removed_rows_path = out_dir / "removed.jsonl"
    write_json(filtered_relationships_path, filtered_relationships)
    filtered_scans_path.write_text("\n".join(kept_scans) + "\n", encoding="utf-8")
    write_jsonl(missing_rows_path, missing_rows)
    write_jsonl(
        removed_rows_path,
        [
            {
                "relationship_id": relationship_id(row),
                "scan_id": row["scan"],
                "split": row["split"],
                "object_count_annotation": len(row.get("objects", {})),
                "relationship_count": len(row.get("relationships", [])),
            }
            for row in removed_rows
        ],
    )

    retry_manifest = load_json(retry_manifest_path) if retry_manifest_path.exists() else None
    retry_missing_count = None
    if retry_manifest is not None:
        retry_missing_count = retry_manifest.get("summary", {}).get("missing_subgraph_count")
    full_log = out_dir.parent / f"{split}_preprocess/full.log"
    too_few_count = (
        full_log.read_text(encoding="utf-8", errors="ignore").count("too few visible objects, scene missalignment possible")
        if full_log.exists()
        else None
    )

    applied_files: dict[str, str] = {}
    if args.apply:
        if not relationships_backup.exists():
            shutil.copy2(relationships_path, relationships_backup)
        if not scans_backup.exists():
            shutil.copy2(scans_path, scans_backup)
        write_json(relationships_path, filtered_relationships)
        scans_path.write_text("\n".join(kept_scans) + "\n", encoding="utf-8")
        applied_files = {
            "relationships": relpath(repo_root, relationships_path),
            "scans": relpath(repo_root, scans_path),
            "relationships_backup": relpath(repo_root, relationships_backup),
            "scans_backup": relpath(repo_root, scans_backup),
        }

    removed_object_counts = Counter(len(row.get("objects", {})) for row in removed_rows)
    claim_limit = (
        "Open3DSG training will use an explicit preprocessed-ready train split. "
        "Report train coverage as 3744/3852 subgraphs and do not claim full official-train preprocessing."
        if split == "train"
        else (
            "Open3DSG training will use an explicit preprocessed-ready validation split. "
            f"Report validation coverage as {len(kept_rows)}/{len(split_rows)} subgraphs and do not claim full validation preprocessing."
        )
    )
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "filter_applied" if args.apply else "filter_ready",
        "applied": bool(args.apply),
        "split": split,
        "repo_root": str(repo_root),
        "staged_root": relpath(repo_root, staged_root),
        "source_relationships": relpath(repo_root, source_relationships_path),
        "source_scans": relpath(repo_root, source_scans_path),
        "runtime_relationships": relpath(repo_root, relationships_path),
        "runtime_scans": relpath(repo_root, scans_path),
        "preprocess_manifest": relpath(repo_root, preprocess_manifest_path),
        "original": {
            "subgraphs": len(split_rows),
            "unique_scans": len(original_scans),
            "relations": count_relations(split_rows),
        },
        "filtered": {
            "subgraphs": len(kept_rows),
            "unique_scans": len(kept_scans),
            "relations": count_relations(kept_rows),
        },
        "removed": {
            "subgraphs": len(removed_rows),
            "unique_scans": len(set(removed_scans)),
            "removed_only_scans": len(removed_only_scans),
            "relations": count_relations(removed_rows),
            "object_count_histogram": dict(sorted(removed_object_counts.items())),
        },
        "recoverability": {
            "full_missing_count": len(missing_rows),
            "too_few_visible_log_count": too_few_count,
            "retry_manifest": relpath(repo_root, retry_manifest_path) if retry_manifest_path.exists() else None,
            "retry_missing_count": retry_missing_count,
            "decision": "not_recoverable_by_simple_retry_filter_missing_subgraphs",
        },
        "outputs": {
            "filtered_relationships": relpath(repo_root, filtered_relationships_path),
            "filtered_scans": relpath(repo_root, filtered_scans_path),
            "missing_rows": relpath(repo_root, missing_rows_path),
            "removed_rows": relpath(repo_root, removed_rows_path),
        },
        "applied_files": applied_files,
        "claim_limit": claim_limit,
        "next_action": "Rerun training preflight before feature dump or training.",
    }
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(build_report(manifest), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "kept": len(kept_rows), "removed": len(removed_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
