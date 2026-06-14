#!/usr/bin/env python3
"""Patch Open3DSG view generation thresholds for isolated recovery runs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


FILTER_ORIGINAL = """            if pixels > 12 and ((ratio > 0.3 or pixels > 80) or (instance_names[inst] in ['wall', 'floor'] and pixels > 80)):
"""

FILTER_PATCHED = """            min_pixels = int(os.environ.get("OPEN3DSG_VIEW_MIN_PIXELS", "12"))
            ratio_crit = float(os.environ.get("OPEN3DSG_VIEW_RATIO_CRIT", "0.3"))
            pixel_crit = int(os.environ.get("OPEN3DSG_VIEW_PIXEL_CRIT", "80"))
            surface_pixel_crit = int(os.environ.get("OPEN3DSG_VIEW_SURFACE_PIXEL_CRIT", str(pixel_crit)))
            if pixels > min_pixels and ((ratio > ratio_crit or pixels > pixel_crit) or (instance_names[inst] in ['wall', 'floor'] and pixels > surface_pixel_crit)):
"""

VIS_ORIGINAL = """                                    intrinsic_info['m_intrinsic'], instance_names, intrinsic_info['m_Width'], intrinsic_info['m_Height'], 0, 0.20, scene_data)
"""

VIS_PATCHED = """                                    intrinsic_info['m_intrinsic'], instance_names, intrinsic_info['m_Width'], intrinsic_info['m_Height'], 0, float(os.environ.get("OPEN3DSG_VIEW_VIS_THRESH", "0.20")), scene_data)
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


def replace_once(text: str, original: str, patched: str, label: str) -> tuple[str, bool]:
    if patched in text:
        return text, False
    if original not in text:
        raise RuntimeError(f"could not find Open3DSG view threshold block: {label}")
    return text.replace(original, patched), True


def main() -> int:
    args = parse_args()
    target = args.source_root / "open3dsg/data/get_object_frame.py"
    text = target.read_text(encoding="utf-8")
    changed = False
    text, did_change = replace_once(text, FILTER_ORIGINAL, FILTER_PATCHED, "object frame filter")
    changed = changed or did_change
    text, did_change = replace_once(text, VIS_ORIGINAL, VIS_PATCHED, "projection visibility threshold")
    changed = changed or did_change
    if changed:
        target.write_text(text, encoding="utf-8")
    print(
        json.dumps(
            {
                "schema_version": "h001_open3dsg_view_threshold_patch_v1",
                "date_checked": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "status": "patched" if changed else "already_patched",
                "changed": changed,
                "target": relpath(args.repo_root, target),
                "default_behavior": "unset env keeps Open3DSG defaults: min_pixels=12, ratio=0.3, pixels=80, vis_thresh=0.20",
                "recovery_env": [
                    "OPEN3DSG_VIEW_MIN_PIXELS",
                    "OPEN3DSG_VIEW_RATIO_CRIT",
                    "OPEN3DSG_VIEW_PIXEL_CRIT",
                    "OPEN3DSG_VIEW_SURFACE_PIXEL_CRIT",
                    "OPEN3DSG_VIEW_VIS_THRESH",
                ],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
