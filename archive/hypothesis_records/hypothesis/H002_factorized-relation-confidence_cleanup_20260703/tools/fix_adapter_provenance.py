#!/usr/bin/env python3
"""Normalize H002 Open3DSG adapter provenance after reusing the H001 adapter."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_adapter_provenance_fix_v1"
DEFAULT_TRAIN_PILOT_SUBSET = (
    "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
    "train_rga_seed/open3dsg_train_pilot/source_contract/relationships_train_pilot.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--predictions-jsonl",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "train_rga_seed/open3dsg_train_pilot/adapter/predictions.jsonl"
        ),
    )
    parser.add_argument("--subset-source", default=DEFAULT_TRAIN_PILOT_SUBSET)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H002_factorized-relation-confidence/artifacts/"
            "train_rga_seed/open3dsg_train_pilot/adapter/provenance_fix_manifest.json"
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    predictions = resolve(repo_root, args.predictions_jsonl)
    manifest_path = resolve(repo_root, args.manifest)
    tmp = predictions.with_suffix(predictions.suffix + ".tmp")

    old_sources: Counter[str] = Counter()
    rows = 0
    changed = 0
    with predictions.open("r", encoding="utf-8") as src, tmp.open("w", encoding="utf-8") as dst:
        for line_no, line in enumerate(src, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {predictions}:{line_no}") from exc
            old = str(row.get("subset_source"))
            old_sources[old] += 1
            if old != args.subset_source:
                row["subset_source"] = args.subset_source
                changed += 1
            dst.write(json.dumps(row, sort_keys=True))
            dst.write("\n")
            rows += 1

    tmp.replace(predictions)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": "ready",
        "inputs": {"predictions_jsonl": relpath(repo_root, predictions)},
        "outputs": {"predictions_jsonl": relpath(repo_root, predictions)},
        "subset_source": args.subset_source,
        "counts": {
            "rows": rows,
            "changed_rows": changed,
            "old_subset_sources": dict(sorted(old_sources.items())),
        },
        "reason": (
            "The reused H001 Open3DSG adapter hardcodes subset_source to the validation JSON. "
            "H002 train pilot predictions must instead point to the frozen train pilot subset."
        ),
    }
    write_json(manifest_path, payload)
    print(json.dumps({"status": "ready", "rows": rows, "changed_rows": changed}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
