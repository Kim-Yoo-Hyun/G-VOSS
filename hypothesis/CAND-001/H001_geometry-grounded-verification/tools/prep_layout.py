#!/usr/bin/env python3
"""Stage generated VL-SAT annotation layout files.

This script does not mutate local_dataset. It writes generated files under the
H001 layout artifact folder so the baseline prep step is reproducible.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "layout" / "vlsat"
DEFAULT_GENERATED_SUBSET_ROOT = DEFAULT_OUTPUT_DIR / "generated" / "3DSSG_subset"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Stage generated 3DSSG_subset files needed by VL-SAT."
    )
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--generated-subset-root", type=Path, default=DEFAULT_GENERATED_SUBSET_ROOT)
    return parser.parse_args()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def scan_ids(path: Path) -> list[str]:
    data = load_json(path)
    return sorted(
        {
            str(entry.get("scan"))
            for entry in data.get("scans", [])
            if entry.get("scan") is not None
        }
    )


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    dataset_root = args.dataset_root.resolve()
    output_dir = args.output_dir.resolve()
    generated_subset_root = args.generated_subset_root.resolve()
    subset_root = dataset_root / "3DSSG_subset"

    relationships_txt = subset_root / "relationships.txt"
    train_json = subset_root / "relationships_train.json"
    validation_json = subset_root / "relationships_validation.json"

    for path in (relationships_txt, train_json, validation_json):
        if not path.exists():
            raise FileNotFoundError(path)

    generated_subset_root.mkdir(parents=True, exist_ok=True)

    relations_txt = generated_subset_root / "relations.txt"
    train_scans_txt = generated_subset_root / "train_scans.txt"
    validation_scans_txt = generated_subset_root / "validation_scans.txt"

    shutil.copyfile(relationships_txt, relations_txt)
    train_ids = scan_ids(train_json)
    validation_ids = scan_ids(validation_json)
    write_lines(train_scans_txt, train_ids)
    write_lines(validation_scans_txt, validation_ids)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prep_version": "vlsat-layout-prep-v1",
        "source_dataset_root": str(dataset_root),
        "generated_subset_root": str(generated_subset_root),
        "source_files": {
            "relationships.txt": rel(relationships_txt),
            "relationships_train.json": rel(train_json),
            "relationships_validation.json": rel(validation_json),
        },
        "generated_files": {
            "relations.txt": rel(relations_txt),
            "train_scans.txt": rel(train_scans_txt),
            "validation_scans.txt": rel(validation_scans_txt),
        },
        "counts": {
            "train_scans": len(train_ids),
            "validation_scans": len(validation_ids),
            "train_validation_overlap": len(set(train_ids) & set(validation_ids)),
        },
        "source_dataset_mutated": False,
    }
    write_json(output_dir / "generated_manifest.json", manifest)

    print(f"generated_subset_root={rel(generated_subset_root)}")
    print(f"relations={rel(relations_txt)}")
    print(f"train_scans={len(train_ids)}")
    print(f"validation_scans={len(validation_ids)}")
    print(f"manifest={rel(output_dir / 'generated_manifest.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
