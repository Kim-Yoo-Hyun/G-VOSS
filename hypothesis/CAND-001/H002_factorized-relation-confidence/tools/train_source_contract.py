#!/usr/bin/env python3
"""Freeze an H002 Open3DSG train pilot source contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_train_source_contract_v1"
PILOT_NAME = "open3dsg_train_pilot"
PRIMARY_FAMILIES = {"support_contact", "proximity", "relative_vertical"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--limit", type=int, default=100)
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
            "train_rga_seed/open3dsg_train_pilot/source_contract"
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
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
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


def build_candidates(
    subset_index: dict[str, dict[str, Any]],
    preprocess_rows: list[dict[str, Any]],
    view_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    view_ready = {
        str(row.get("scan_id"))
        for row in view_rows
        if row.get("scan_id") is not None and valid_after(row)
    }

    candidates: list[dict[str, Any]] = []
    dropped: Counter[str] = Counter()
    for row in preprocess_rows:
        scan_id = str(row.get("scan_id"))
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
        split_id = int(row.get("split"))
        sid = subgraph_id(scan_id, split_id)
        subset_entry = subset_index.get(sid)
        if subset_entry is None:
            dropped["missing_subset_entry"] += 1
            continue
        counts = family_counts(subset_entry)
        object_count = len(subset_entry.get("objects", {}))
        candidates.append(
            {
                "scan_id": scan_id,
                "split": split_id,
                "subgraph_id": sid,
                "relationship_count": relationship_count,
                "object_count": object_count,
                "family_counts": dict(sorted(counts.items())),
                "primary_family_count": sum(counts.get(family, 0) for family in PRIMARY_FAMILIES),
                "preprocess_path": row.get("path"),
            }
        )

    stats = {
        "view_ready_scans": len(view_ready),
        "candidate_subgraphs": len(candidates),
        "dropped": dict(sorted(dropped.items())),
    }
    return candidates, stats


def select_pilot(candidates: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_scan[candidate["scan_id"]].append(candidate)

    scan_representatives: list[dict[str, Any]] = []
    for scan_id in sorted(by_scan):
        choices = sorted(
            by_scan[scan_id],
            key=lambda row: (
                -int(row["primary_family_count"]),
                -int(row["relationship_count"]),
                int(row["split"]),
                row["subgraph_id"],
            ),
        )
        scan_representatives.append(choices[0])

    selected: list[dict[str, Any]] = []
    used_scans: set[str] = set()

    missing = set(PRIMARY_FAMILIES)
    while missing and len(selected) < limit:
        ranked = sorted(
            (
                row
                for row in scan_representatives
                if row["scan_id"] not in used_scans
                and any(row["family_counts"].get(family, 0) for family in missing)
            ),
            key=lambda row: (
                -sum(row["family_counts"].get(family, 0) for family in missing),
                row["scan_id"],
                int(row["split"]),
            ),
        )
        if not ranked:
            break
        choice = ranked[0]
        selected.append(choice)
        used_scans.add(choice["scan_id"])
        missing -= {family for family in missing if choice["family_counts"].get(family, 0)}

    for row in sorted(scan_representatives, key=lambda item: (item["scan_id"], int(item["split"]))):
        if len(selected) >= limit:
            break
        if row["scan_id"] in used_scans:
            continue
        selected.append(row)
        used_scans.add(row["scan_id"])

    return selected


def make_report(manifest: dict[str, Any]) -> str:
    selected = manifest["counts"]["selected_subgraphs"]
    scans = manifest["counts"]["selected_scans"]
    coverage = manifest["selection"]["primary_family_coverage"]
    status = manifest["status"]
    outputs = manifest["outputs"]
    return "\n".join(
        [
            "# H002 Open3DSG Train Pilot Source Contract",
            "",
            f"Status: `{status}`",
            f"Selected subgraphs: `{selected}`",
            f"Selected scans: `{scans}`",
            f"Primary family coverage: `{coverage}`",
            "",
            "## Outputs",
            "",
            f"- source contract: `{outputs['source_contract']}`",
            f"- selected scans: `{outputs['selected_scans']}`",
            f"- selected subgraphs: `{outputs['selected_subgraphs']}`",
            f"- pilot contexts: `{outputs['pilot_contexts']}`",
            f"- pilot subset JSON: `{outputs['pilot_subset_json']}`",
            "",
            "## Boundary",
            "",
            "This artifact freezes a train-only pilot scope for H002. It reads H001 train-side "
            "preprocess/view records but does not modify H001 artifacts.",
            "",
        ]
    )


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
    candidates: list[dict[str, Any]] = []
    candidate_stats: dict[str, Any] = {}
    if not blockers:
        subset = load_json(train_subset_path)
        subset_index = build_subset_index(subset)
        candidates, candidate_stats = build_candidates(
            subset_index=subset_index,
            preprocess_rows=load_jsonl(preprocess_path),
            view_rows=load_jsonl(views_path),
        )
    else:
        subset_index = {}

    selected = select_pilot(candidates, args.limit) if candidates else []
    selected_ids = [row["subgraph_id"] for row in selected]
    selected_scans = [row["scan_id"] for row in selected]
    selected_id_set = set(selected_ids)
    pilot_entries = [entry for sid, entry in subset_index.items() if sid in selected_id_set]
    pilot_entries.sort(key=lambda entry: selected_ids.index(subgraph_id(str(entry["scan"]), int(entry["split"]))))

    selected_family_counts: Counter[str] = Counter()
    for row in selected:
        selected_family_counts.update(row["family_counts"])
    primary_coverage = {
        family: int(selected_family_counts.get(family, 0)) for family in sorted(PRIMARY_FAMILIES)
    }

    if len(selected) < args.limit:
        blockers.append(f"selected_subgraphs:{len(selected)}/{args.limit}")
    missing_primary = [family for family, count in primary_coverage.items() if count <= 0]
    if missing_primary:
        blockers.append(f"missing_primary_family_coverage:{','.join(missing_primary)}")

    paths = {
        "source_contract": out_dir / "source_contract.json",
        "selected_scans": out_dir / "selected_scans.txt",
        "selected_subgraphs": out_dir / "selected_subgraphs.txt",
        "pilot_contexts": out_dir / "pilot_contexts.jsonl",
        "pilot_subset_json": out_dir / "relationships_train_pilot.json",
        "report": out_dir / "report.md",
    }

    write_lines(paths["selected_scans"], selected_scans)
    write_lines(paths["selected_subgraphs"], selected_ids)
    write_jsonl(paths["pilot_contexts"], selected)
    write_json(paths["pilot_subset_json"], {"scans": pilot_entries})

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": "ready" if not blockers else "blocked",
        "pilot_name": PILOT_NAME,
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
            "limit": args.limit,
            "rule": (
                "train-only subgraphs with ready Open3DSG preprocess pickle, ready train view "
                "pickle, at least one GT relationship, one subgraph per scan, greedy coverage "
                "of support_contact/proximity/relative_vertical, then deterministic scan order"
            ),
            "primary_families": sorted(PRIMARY_FAMILIES),
            "primary_family_coverage": primary_coverage,
            "family_counts": dict(sorted(selected_family_counts.items())),
        },
        "counts": {
            "train_subset_contexts": len(subset.get("scans", [])),
            "candidate_subgraphs": candidate_stats.get("candidate_subgraphs", 0),
            "selected_subgraphs": len(selected),
            "selected_scans": len(set(selected_scans)),
            "pilot_subset_contexts": len(pilot_entries),
        },
        "candidate_stats": candidate_stats,
        "blockers": blockers,
        "claim_boundary": (
            "Train scope selection only. This artifact is not semantic-geometric diagnostic "
            "evidence until Open3DSG raw dump, adapter prediction export, geometry join, and "
            "RGA match-status rows are produced for this exact scope."
        ),
    }
    write_json(paths["source_contract"], manifest)
    paths["report"].write_text(make_report(manifest), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "selected_subgraphs": len(selected),
                "selected_scans": len(set(selected_scans)),
                "out": relpath(repo_root, out_dir),
            },
            sort_keys=True,
        )
    )
    return 0 if manifest["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
