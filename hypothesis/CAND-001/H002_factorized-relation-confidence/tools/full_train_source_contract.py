#!/usr/bin/env python3
"""Freeze an H002 Open3DSG full-train source contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_full_train_source_contract_v1"
SCOPE_ID = "open3dsg_train_full"
SOURCE_ID = "open3dsg_train_full"
SELECTION_MODE = "all_ready_train_contexts"
PRIMARY_FAMILIES = {"support_contact", "proximity", "relative_vertical"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--train-subset-json",
        type=Path,
        default=Path("local_dataset/3DSSG_subset/relationships_train.json"),
    )
    parser.add_argument(
        "--train-preprocess-records",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/sources/open3dsg/train_preprocess/records.jsonl"
        ),
    )
    parser.add_argument(
        "--train-view-records",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/train_views/records.jsonl"),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "train_rga_full/open3dsg_train_full/source_contract"
        ),
    )
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_no}") from exc
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            handle.write("\n")


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def predicate_family(label: str) -> str:
    if label in {"standing on", "lying on", "supported by"}:
        return "support_contact"
    if label == "close by":
        return "proximity"
    if label in {"higher than", "lower than"}:
        return "relative_vertical"
    if label in {"left", "right", "front", "behind", "in front of"}:
        return "relative_horizontal"
    if label in {"attached to", "hanging on", "mounted on", "connected to"}:
        return "attachment_deferred"
    return "unsupported_first_pass"


def subgraph_id(scan_id: str, split_id: int) -> str:
    return f"{scan_id}_{split_id}"


def valid_after(row: dict[str, Any]) -> bool:
    return bool(row.get("after", {}).get("exists")) and bool(row.get("after", {}).get("valid_pickle"))


def build_subset_index(subset: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for entry in subset.get("scans", []):
        scan_id = str(entry.get("scan"))
        split_id = int(entry.get("split"))
        index[subgraph_id(scan_id, split_id)] = entry
    return index


def family_counts(entry: dict[str, Any]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for rel in entry.get("relationships", []):
        if len(rel) < 4:
            counts["malformed"] += 1
            continue
        counts[predicate_family(str(rel[3]))] += 1
    return counts


def build_ready_contexts(
    subset_index: dict[str, dict[str, Any]],
    preprocess_rows: list[dict[str, Any]],
    view_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    view_ready = {
        str(row.get("scan_id"))
        for row in view_rows
        if row.get("scan_id") is not None and valid_after(row)
    }

    contexts: list[dict[str, Any]] = []
    dropped: Counter[str] = Counter()
    preprocess_seen = 0
    for row in preprocess_rows:
        preprocess_seen += 1
        scan_id = str(row.get("scan_id"))
        split_id = int(row.get("split"))
        sid = subgraph_id(scan_id, split_id)
        if scan_id not in view_ready:
            dropped["view_not_ready"] += 1
            continue
        if not valid_after(row):
            dropped["preprocess_not_ready"] += 1
            continue
        relationship_count = int(row.get("relationship_count") or 0)
        if relationship_count <= 0:
            dropped["no_relationship"] += 1
            continue
        subset_entry = subset_index.get(sid)
        if subset_entry is None:
            dropped["missing_subset_entry"] += 1
            continue
        counts = family_counts(subset_entry)
        contexts.append(
            {
                "scan_id": scan_id,
                "split": split_id,
                "subgraph_id": sid,
                "relationship_count": relationship_count,
                "object_count": len(subset_entry.get("objects", {})),
                "family_counts": dict(sorted(counts.items())),
                "primary_family_count": sum(counts.get(family, 0) for family in PRIMARY_FAMILIES),
                "preprocess_path": row.get("path"),
                "selection_mode": SELECTION_MODE,
            }
        )

    contexts.sort(key=lambda item: (str(item["scan_id"]), int(item["split"]), str(item["subgraph_id"])))
    stats = {
        "view_ready_scans": len(view_ready),
        "preprocess_records": preprocess_seen,
        "ready_candidate_contexts": len(contexts),
        "dropped": dict(sorted(dropped.items())),
    }
    return contexts, stats


def make_report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    family_counts_payload = manifest["selection"]["family_counts"]
    lines = [
        "# H002 Open3DSG Full Train Source Contract",
        "",
        f"Status: `{manifest['status']}`",
        f"Scope: `{manifest['scope_id']}`",
        f"Selection mode: `{manifest['selection_mode']}`",
        "",
        "## Counts",
        "",
        f"- official train subset contexts: `{counts['official_train_subset_contexts']}`",
        f"- ready candidate contexts: `{counts['ready_candidate_contexts']}`",
        f"- selected contexts: `{counts['selected_contexts']}`",
        f"- selected scans: `{counts['selected_scans']}`",
        f"- selected relationships: `{counts['selected_relationships']}`",
        "",
        "## Family Counts",
        "",
    ]
    for family, count in sorted(family_counts_payload.items()):
        lines.append(f"- `{family}`: `{count}`")
    lines.extend(
        [
            "",
            "## Outputs",
            "",
        ]
    )
    for key, path in sorted(manifest["outputs"].items()):
        lines.append(f"- {key}: `{path}`")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This artifact freezes a train-only full scope for H002. It reads train-side "
            "Open3DSG readiness records as provenance and does not modify H001 artifacts.",
            "",
        ]
    )
    if manifest["blockers"]:
        lines.extend(["## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    train_subset_path = resolve(repo_root, args.train_subset_json)
    preprocess_path = resolve(repo_root, args.train_preprocess_records)
    views_path = resolve(repo_root, args.train_view_records)

    blockers: list[str] = []
    for label, path in {
        "train_subset_json": train_subset_path,
        "train_preprocess_records": preprocess_path,
        "train_view_records": views_path,
    }.items():
        if not path.is_file():
            blockers.append(f"missing_{label}:{relpath(repo_root, path)}")

    subset: dict[str, Any] = {"scans": []}
    subset_index: dict[str, dict[str, Any]] = {}
    contexts: list[dict[str, Any]] = []
    candidate_stats: dict[str, Any] = {}
    if not blockers:
        subset = load_json(train_subset_path)
        subset_index = build_subset_index(subset)
        contexts, candidate_stats = build_ready_contexts(
            subset_index=subset_index,
            preprocess_rows=load_jsonl(preprocess_path),
            view_rows=load_jsonl(views_path),
        )

    selected_ids = [str(row["subgraph_id"]) for row in contexts]
    selected_scans = sorted({str(row["scan_id"]) for row in contexts})
    selected_id_set = set(selected_ids)
    entries_by_id = {
        subgraph_id(str(entry["scan"]), int(entry["split"])): entry
        for entry in subset.get("scans", [])
        if subgraph_id(str(entry["scan"]), int(entry["split"])) in selected_id_set
    }
    selected_entries = [entries_by_id[sid] for sid in selected_ids if sid in entries_by_id]

    if len(selected_entries) != len(contexts):
        blockers.append(f"selected_entries:{len(selected_entries)}/{len(contexts)}")
    if len(contexts) != int(candidate_stats.get("ready_candidate_contexts", 0)):
        blockers.append(
            f"selected_contexts_not_all_ready:{len(contexts)}/{candidate_stats.get('ready_candidate_contexts', 0)}"
        )

    selected_family_counts: Counter[str] = Counter()
    selected_relationships = 0
    for entry in selected_entries:
        counts = family_counts(entry)
        selected_family_counts.update(counts)
        selected_relationships += sum(counts.values())
    primary_coverage = {
        family: int(selected_family_counts.get(family, 0)) for family in sorted(PRIMARY_FAMILIES)
    }
    missing_primary = [family for family, count in primary_coverage.items() if count <= 0]
    if missing_primary:
        blockers.append(f"missing_primary_family_coverage:{','.join(missing_primary)}")

    paths = {
        "source_contract": out_dir / "source_contract.json",
        "selected_scans": out_dir / "selected_scans.txt",
        "selected_subgraphs": out_dir / "selected_subgraphs.txt",
        "train_contexts": out_dir / "train_contexts.jsonl",
        "train_subset_json": out_dir / "relationships_train_full.json",
        "report": out_dir / "report.md",
    }

    write_lines(paths["selected_scans"], selected_scans)
    write_lines(paths["selected_subgraphs"], selected_ids)
    write_jsonl(paths["train_contexts"], contexts)
    write_json(paths["train_subset_json"], {"scans": selected_entries})

    dropped = candidate_stats.get("dropped", {})
    counts_payload = {
        "official_train_subset_contexts": len(subset.get("scans", [])),
        "preprocess_records": int(candidate_stats.get("preprocess_records", 0)),
        "ready_candidate_contexts": int(candidate_stats.get("ready_candidate_contexts", 0)),
        "selected_contexts": len(contexts),
        "selected_subgraphs": len(contexts),
        "selected_scans": len(selected_scans),
        "selected_relationships": selected_relationships,
        "dropped_preprocess_not_ready": int(dropped.get("preprocess_not_ready", 0)),
        "dropped_view_not_ready": int(dropped.get("view_not_ready", 0)),
        "dropped_no_relationship": int(dropped.get("no_relationship", 0)),
        "dropped_missing_subset_entry": int(dropped.get("missing_subset_entry", 0)),
    }

    status = "ready" if not blockers else "blocked"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": status,
        "scope_id": SCOPE_ID,
        "source_id": SOURCE_ID,
        "selection_mode": SELECTION_MODE,
        "inputs": {
            "train_subset_json": {
                "path": relpath(repo_root, train_subset_path),
                "sha256": sha256_file(train_subset_path),
            },
            "train_preprocess_records": {
                "path": relpath(repo_root, preprocess_path),
                "sha256": sha256_file(preprocess_path),
            },
            "train_view_records": {
                "path": relpath(repo_root, views_path),
                "sha256": sha256_file(views_path),
            },
        },
        "outputs": {key: relpath(repo_root, path) for key, path in paths.items()},
        "selection": {
            "rule": (
                "Select every train-origin context with a ready Open3DSG preprocess pickle, "
                "ready train view pickle, at least one GT relationship, and a matching "
                "relationships_train.json entry."
            ),
            "primary_families": sorted(PRIMARY_FAMILIES),
            "primary_family_coverage": primary_coverage,
            "family_counts": dict(sorted(selected_family_counts.items())),
        },
        "counts": counts_payload,
        "candidate_stats": candidate_stats,
        "blockers": blockers,
        "claim_boundary": (
            "Train full source selection only. This artifact is not semantic-geometric "
            "diagnostic evidence until Open3DSG raw dump, adapter prediction export, geometry "
            "join, and RGA match-status rows are produced for this exact scope."
        ),
        "forbidden_split_boundary": {
            "validation_or_test_rows_used": False,
            "h001_heldout_artifacts_used": False,
            "runtime_validation_filename_allowed_only_inside_h002_train_full_runtime": True,
        },
    }
    write_json(paths["source_contract"], manifest)
    paths["report"].write_text(make_report(manifest), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": status,
                "selected_contexts": len(contexts),
                "selected_scans": len(selected_scans),
                "out": relpath(repo_root, out_dir),
            },
            sort_keys=True,
        )
    )
    return 0 if status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
