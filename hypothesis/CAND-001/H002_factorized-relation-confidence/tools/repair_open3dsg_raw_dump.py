#!/usr/bin/env python3
"""Repair H002 Open3DSG raw dump identity issues before adapter export."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_open3dsg_raw_dump_repair_v1"
SCORE_CONFLICT_TOLERANCE = 1e-6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--raw-dump-jsonl",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "train_rga_seed/open3dsg_train_pilot/raw_dump/raw.jsonl"
        ),
    )
    parser.add_argument(
        "--out-jsonl",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "train_rga_seed/open3dsg_train_pilot/raw_dump/raw.dedup.jsonl"
        ),
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "train_rga_seed/open3dsg_train_pilot/raw_dump/repair_manifest.json"
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_no}") from exc
            row["_h002_raw_line_no"] = line_no
            rows.append(row)
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            row = dict(row)
            row.pop("_h002_raw_line_no", None)
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def edge_key(row: dict[str, Any]) -> tuple[str | None, Any, Any]:
    edge = row.get("edge", {})
    return row.get("subgraph_id"), edge.get("subject_id"), edge.get("object_id")


def predicate_signature(row: dict[str, Any]) -> tuple[tuple[str, float | None], ...]:
    signature: list[tuple[str, float | None]] = []
    for item in row.get("predicate_scores", []):
        label = str(item.get("predicate_label"))
        score = item.get("score")
        try:
            score_value = round(float(score), 8)
        except (TypeError, ValueError):
            score_value = None
        signature.append((label, score_value))
    return tuple(signature)


def score_drift(group: list[dict[str, Any]]) -> dict[str, Any]:
    if len(group) <= 1:
        return {"label_conflict": False, "max_abs_score_diff": 0.0}
    base = group[0].get("predicate_scores", [])
    label_conflict = False
    max_abs = 0.0
    for row in group[1:]:
        current = row.get("predicate_scores", [])
        if len(base) != len(current):
            label_conflict = True
        for first, second in zip(base, current):
            if first.get("predicate_label") != second.get("predicate_label"):
                label_conflict = True
            try:
                diff = abs(float(first.get("score")) - float(second.get("score")))
            except (TypeError, ValueError):
                label_conflict = True
                continue
            max_abs = max(max_abs, diff)
    return {"label_conflict": label_conflict, "max_abs_score_diff": max_abs}


def repair(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    grouped: dict[tuple[str | None, Any, Any], list[dict[str, Any]]] = defaultdict(list)
    malformed = 0
    for row in rows:
        key = edge_key(row)
        if key[0] is None or key[1] is None or key[2] is None:
            malformed += 1
        grouped[key].append(row)

    output: list[dict[str, Any]] = []
    duplicate_groups: list[dict[str, Any]] = []
    conflict_groups = 0
    label_conflict_groups = 0
    max_abs_score_diff = 0.0
    for key in sorted(grouped, key=lambda item: (str(item[0]), str(item[1]), str(item[2]))):
        group = sorted(grouped[key], key=lambda row: int(row["_h002_raw_line_no"]))
        output.append(group[0])
        if len(group) <= 1:
            continue
        signatures = {predicate_signature(row) for row in group}
        drift = score_drift(group)
        max_abs_score_diff = max(max_abs_score_diff, float(drift["max_abs_score_diff"]))
        if drift["label_conflict"]:
            label_conflict_groups += 1
        if len(signatures) > 1:
            conflict_groups += 1
        duplicate_groups.append(
            {
                "key": {"subgraph_id": key[0], "subject_id": key[1], "object_id": key[2]},
                "count": len(group),
                "kept_line": int(group[0]["_h002_raw_line_no"]),
                "dropped_lines": [int(row["_h002_raw_line_no"]) for row in group[1:]],
                "predicate_scores_identical": len(signatures) == 1,
                "label_conflict": bool(drift["label_conflict"]),
                "max_abs_score_diff": float(drift["max_abs_score_diff"]),
                "node_index_pairs": [
                    {
                        "subject_node_index": row.get("edge", {}).get("subject_node_index"),
                        "object_node_index": row.get("edge", {}).get("object_node_index"),
                    }
                    for row in group
                ],
            }
        )

    by_subgraph = Counter(item["key"]["subgraph_id"] for item in duplicate_groups)
    severe_conflicts = label_conflict_groups > 0 or max_abs_score_diff > SCORE_CONFLICT_TOLERANCE
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": "ready" if not severe_conflicts else "ready_with_conflicting_duplicates",
        "policy": (
            "Deduplicate raw rows by (subgraph_id, subject_id, object_id). Keep the earliest "
            "raw line and drop later duplicates only before adapter export. Predicate score "
            "drift is reported but not averaged."
        ),
        "score_conflict_tolerance": SCORE_CONFLICT_TOLERANCE,
        "counts": {
            "input_rows": len(rows),
            "output_rows": len(output),
            "duplicate_groups": len(duplicate_groups),
            "duplicate_extra_rows": sum(item["count"] - 1 for item in duplicate_groups),
            "conflict_groups": conflict_groups,
            "label_conflict_groups": label_conflict_groups,
            "max_abs_score_diff": max_abs_score_diff,
            "malformed_identity_rows": malformed,
        },
        "duplicate_subgraphs": dict(sorted(by_subgraph.items())),
        "duplicate_groups_sample": duplicate_groups[:20],
    }
    return output, manifest


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    raw_path = resolve(repo_root, args.raw_dump_jsonl)
    out_path = resolve(repo_root, args.out_jsonl)
    manifest_path = resolve(repo_root, args.manifest)
    rows = read_jsonl(raw_path)
    repaired_rows, manifest = repair(rows)
    manifest["inputs"] = {"raw_dump_jsonl": relpath(repo_root, raw_path)}
    manifest["outputs"] = {
        "repaired_raw_dump_jsonl": relpath(repo_root, out_path),
        "manifest": relpath(repo_root, manifest_path),
    }
    write_jsonl(out_path, repaired_rows)
    write_json(manifest_path, manifest)
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "input_rows": manifest["counts"]["input_rows"],
                "output_rows": manifest["counts"]["output_rows"],
                "duplicate_groups": manifest["counts"]["duplicate_groups"],
                "out": relpath(repo_root, out_path),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
