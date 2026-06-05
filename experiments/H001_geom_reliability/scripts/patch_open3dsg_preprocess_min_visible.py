#!/usr/bin/env python3
"""Patch Open3DSG R3Scan preprocessing to expose the min-visible-object gate."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ORIGINAL = """        if len(objects_id)-len(drop) < 4:
            print('too few visible objects, scene missalignment possible')
            return
            # raise Exception('too few visible objects, scene missalignment possible')
"""

PATCHED = """        min_visible_objects = int(os.environ.get("OPEN3DSG_MIN_VISIBLE_OBJECTS", "4"))
        if len(objects_id)-len(drop) < min_visible_objects:
            print('too few visible objects, scene missalignment possible')
            return
            # raise Exception('too few visible objects, scene missalignment possible')
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    return parser.parse_args()


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def main() -> int:
    args = parse_args()
    target = args.source_root / "open3dsg/data/preprocess_3rscan.py"
    text = target.read_text(encoding="utf-8")
    changed = False
    if PATCHED in text:
        status = "already_patched"
    elif ORIGINAL in text:
        text = text.replace(ORIGINAL, PATCHED)
        target.write_text(text, encoding="utf-8")
        status = "patched"
        changed = True
    else:
        raise RuntimeError(f"could not find min-visible-object gate in {target}")
    print(
        json.dumps(
            {
                "schema_version": "h001_open3dsg_preprocess_min_visible_patch_v1",
                "date_checked": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "status": status,
                "changed": changed,
                "target": relpath(args.repo_root, target),
                "default_behavior": "OPEN3DSG_MIN_VISIBLE_OBJECTS unset keeps the official gate at 4",
                "recovery_override": "set OPEN3DSG_MIN_VISIBLE_OBJECTS=2 for isolated recovery only",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
