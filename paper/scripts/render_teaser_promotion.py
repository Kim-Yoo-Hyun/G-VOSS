#!/usr/bin/env python3
"""Prepare the supplied promotion-only teaser for a one-column layout trial."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "paper" / "reference_AAAI" / "Figure1.png"
CASE_MANIFEST = ROOT / "paper" / "generated" / "figures" / "figure3_geometry_manifest.json"
OUT_DIR = ROOT / "paper" / "generated" / "figures"
STEM = "teaser_promotion_trial"
EXPECTED_SIZE = (647, 327)
SCALE = 4


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_case() -> dict[str, bool]:
    context = json.loads(CASE_MANIFEST.read_text(encoding="utf-8"))["teaser_context"]
    promoted = context["promoted"]
    checks = {
        "same_context": context["subgraph_id"] == "c2d99345-1947-2fbf-818d-90ea82acef29_2",
        "relation": (
            promoted["subject_label"],
            promoted["predicate"],
            promoted["object_label"],
        ) == ("desk", "close by", "chair"),
        "rank_change": (promoted["source_rank"], promoted["routed_rank"]) == (81, 30),
        "satisfied": promoted["status"] == "satisfied",
        "exact_label": bool(context["validations"]["promoted_exact_label_gt"]),
    }
    if not all(checks.values()):
        raise ValueError(f"promotion teaser case lock failed: {checks}")
    return checks


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    checks = validate_case()
    source = Image.open(SOURCE).convert("RGBA")
    if source.size != EXPECTED_SIZE:
        raise ValueError(f"unexpected promotion teaser size: {source.size}")

    raster = source.resize(
        (source.width * SCALE, source.height * SCALE),
        Image.Resampling.LANCZOS,
    )
    raster_path = OUT_DIR / f"{STEM}.png"
    raster.save(raster_path, optimize=True)

    width, height = raster.size
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg"
     xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="{width}" height="{height}" fill="#ffffff"/>
  <image x="0" y="0" width="{width}" height="{height}"
         preserveAspectRatio="xMidYMid meet"
         xlink:href="{raster_path.name}"/>
</svg>
'''
    svg_path = OUT_DIR / f"{STEM}.svg"
    svg_path.write_text(svg, encoding="utf-8")

    manifest = {
        "schema_version": "h001_teaser_promotion_trial_v1",
        "status": "one_column_trial_asset_generated_case_lock_verified",
        "source": str(SOURCE.relative_to(ROOT)),
        "source_sha256": sha256(SOURCE),
        "source_size": list(source.size),
        "scale": SCALE,
        "raster": str(raster_path.relative_to(ROOT)),
        "raster_size": list(raster.size),
        "raster_sha256": sha256(raster_path),
        "svg": str(svg_path.relative_to(ROOT)),
        "svg_sha256": sha256(svg_path),
        "case_checks": checks,
    }
    manifest_path = OUT_DIR / f"{STEM}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(svg_path)
    print(manifest_path)


if __name__ == "__main__":
    main()
