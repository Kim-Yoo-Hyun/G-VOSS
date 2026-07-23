#!/usr/bin/env python3
"""Convert the supplied compact teaser into a hybrid raster/vector figure.

The dense gray scene projections are retained as high-resolution raster layers.
All titles, relation labels, axes, ticks, object annotations, connecting lines,
and rank outcomes are redrawn as SVG vectors.  The locked geometry-figure
manifest is checked before the paper-facing asset is emitted.
"""

from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PNG = ROOT / "paper" / "reference_AAAI" / "Figure1_exchange.png"
SOURCE_MANIFEST = ROOT / "paper" / "generated" / "figures" / "figure3_geometry_manifest.json"
OUT_DIR = ROOT / "paper" / "generated" / "figures"
OUTPUT_STEM = "teaser_exchange_hybrid"

CANVAS_W = 1076
CANVAS_H = 485
RASTER_SCALE = 4

COLORS = {
    "ink": "#171717",
    "axis": "#252525",
    "muted": "#8b8b8b",
    "divider": "#d0d0d0",
    "subject": "#e66101",
    "object": "#164dcc",
    "demote": "#e31a1c",
    "method": "#006d6f",
    "white": "#ffffff",
}

# Pixel-aligned interiors from the supplied 1,076 x 485 composition.  Axes,
# labels, and colored annotations are intentionally excluded and redrawn below.
PANEL_CROPS = {
    "left": (55, 97, 500, 373),
    "right": (594, 97, 1055, 373),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_locked_case() -> dict:
    manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
    context = manifest["teaser_context"]
    target = context["target_removed"]
    promoted = context["promoted"]
    expected = {
        "scan_id": "c2d99345-1947-2fbf-818d-90ea82acef29",
        "subgraph_id": "c2d99345-1947-2fbf-818d-90ea82acef29_2",
        "target": ("desk", "higher than", "ceiling", 6, 425, "violated"),
        "promoted": ("desk", "close by", "chair", 81, 30, "satisfied"),
    }
    actual_target = (
        target["subject_label"],
        target["predicate"],
        target["object_label"],
        target["source_rank"],
        target["routed_rank"],
        target["status"],
    )
    actual_promoted = (
        promoted["subject_label"],
        promoted["predicate"],
        promoted["object_label"],
        promoted["source_rank"],
        promoted["routed_rank"],
        promoted["status"],
    )
    checks = {
        "scan_id": context["scan_id"] == expected["scan_id"],
        "subgraph_id": context["subgraph_id"] == expected["subgraph_id"],
        "target": actual_target == expected["target"],
        "promoted": actual_promoted == expected["promoted"],
        "all_source_validations": all(context["validations"].values()),
    }
    if not all(checks.values()):
        raise ValueError(f"teaser case lock failed: {checks}")
    return {"context": context, "checks": checks}


def extract_scene_layer(image: Image.Image, name: str, crop: tuple[int, int, int, int]) -> Path:
    """Keep only the neutral gray scene marks and upscale them for print."""
    source = np.asarray(image.crop(crop).convert("RGBA"), dtype=np.uint8)
    rgb = source[..., :3].astype(np.int16)
    channel_range = rgb.max(axis=2) - rgb.min(axis=2)
    luminance = rgb.mean(axis=2)

    # The supplied point projections are neutral gray.  Colored object labels,
    # markers, and relation lines are discarded so their vector redraw does not
    # double-print.  Near-white antialiasing is retained but the white field is
    # made transparent.
    neutral_scene = (
        (channel_range <= 16)
        & (luminance >= 62)
        & (luminance <= 247)
        & (source[..., 3] > 0)
    )
    layer = np.zeros_like(source)
    gray = np.clip(np.round(luminance), 0, 255).astype(np.uint8)
    layer[..., 0] = gray
    layer[..., 1] = gray
    layer[..., 2] = gray
    layer[..., 3] = np.where(neutral_scene, source[..., 3], 0)

    raster = Image.fromarray(layer, mode="RGBA")
    raster = raster.resize(
        (raster.width * RASTER_SCALE, raster.height * RASTER_SCALE),
        Image.Resampling.LANCZOS,
    )
    path = OUT_DIR / f"{OUTPUT_STEM}_{name}_scene.png"
    raster.save(path, optimize=True)
    return path


def text(
    x: float,
    y: float,
    content: str,
    size: float = 20,
    weight: int = 400,
    fill: str = COLORS["ink"],
    anchor: str = "start",
    style: str = "normal",
    family: str = "TeX Gyre Heros, Helvetica, Arial, sans-serif",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="{family}" font-size="{size:.1f}" font-weight="{weight}" '
        f'font-style="{style}" fill="{fill}">{html.escape(content)}</text>'
    )


def relation_text(x: float, y: float, predicate: str, object_label: str) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" '
        'font-family="TeX Gyre Heros, Helvetica, Arial, sans-serif" '
        'font-size="20" font-weight="400" xml:space="preserve">'
        f'<tspan fill="{COLORS["subject"]}">desk</tspan>'
        f'<tspan fill="{COLORS["ink"]}"> → {html.escape(predicate)} → </tspan>'
        f'<tspan fill="{COLORS["object"]}">{html.escape(object_label)}</tspan>'
        '</text>'
    )


def rank_text(x: float, left_rank: int, right_rank: int) -> str:
    return (
        f'<text x="{x:.1f}" y="469" text-anchor="middle" '
        'font-family="TeX Gyre Heros, Helvetica, Arial, sans-serif" '
        'font-size="20" font-weight="400" fill="#171717" xml:space="preserve">'
        '<tspan>Source rank </tspan>'
        f'<tspan font-weight="700">{left_rank}</tspan>'
        '<tspan> → RelCompat3D rank </tspan>'
        f'<tspan font-weight="700">{right_rank}</tspan>'
        '</text>'
    )


def axes(
    x: float,
    y: float,
    width: float,
    height: float,
    x_bounds: tuple[float, float],
    y_bounds: tuple[float, float],
    x_ticks: Iterable[int],
    y_ticks: Iterable[int],
    x_label: str,
    y_label: str,
) -> list[str]:
    x0, x1 = x_bounds
    y0, y1 = y_bounds

    def px(value: float) -> float:
        return x + (value - x0) / (x1 - x0) * width

    def py(value: float) -> float:
        return y + height - (value - y0) / (y1 - y0) * height

    parts = [
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y+height:.1f}" stroke="{COLORS["axis"]}" stroke-width="1.2"/>',
        f'<line x1="{x:.1f}" y1="{y+height:.1f}" x2="{x+width:.1f}" y2="{y+height:.1f}" stroke="{COLORS["axis"]}" stroke-width="1.2"/>',
    ]
    for value in x_ticks:
        xx = px(value)
        parts.append(
            f'<line x1="{xx:.1f}" y1="{y+height:.1f}" x2="{xx:.1f}" y2="{y+height+7:.1f}" stroke="{COLORS["axis"]}" stroke-width="1.1"/>'
        )
        parts.append(text(xx, y + height + 29, str(value).replace("-", "−"), 19.5, anchor="middle"))
    for value in y_ticks:
        yy = py(value)
        parts.append(
            f'<line x1="{x-7:.1f}" y1="{yy:.1f}" x2="{x:.1f}" y2="{yy:.1f}" stroke="{COLORS["axis"]}" stroke-width="1.1"/>'
        )
        parts.append(text(x - 14, yy + 6, str(value).replace("-", "−"), 19.5, anchor="end"))
    parts.append(
        text(
            x + width - 2,
            y + height + 53,
            x_label,
            21,
            fill=COLORS["axis"],
            anchor="end",
            style="italic",
            family="TeX Gyre Termes, Times New Roman, serif",
        )
    )
    parts.append(
        text(
            x - 49,
            y - 17,
            y_label,
            21,
            fill=COLORS["axis"],
            style="italic",
            family="TeX Gyre Termes, Times New Roman, serif",
        )
    )
    return parts


def label_box(x: float, y: float, width: float, label: str, color: str) -> list[str]:
    return [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="28" rx="5" fill="#ffffff" fill-opacity="0.90" stroke="{color}" stroke-width="1.2"/>',
        text(x + width / 2, y + 21, label, 20, 600, color, "middle"),
    ]


def render_svg(left_scene: Path, right_scene: Path) -> str:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{CANVAS_W}" height="{CANVAS_H}" viewBox="0 0 {CANVAS_W} {CANVAS_H}">',
        '<rect width="1076" height="485" fill="#ffffff"/>',
        '<g shape-rendering="geometricPrecision" text-rendering="geometricPrecision">',
        text(268, 27, "Leaves Top-50 (demoted)", 22, 500, anchor="middle"),
        text(808, 27, "Enters Top-50 (promoted)", 22, 500, anchor="middle"),
        relation_text(268, 59, "higher than", "ceiling"),
        relation_text(808, 59, "close by", "chair"),
        f'<line x1="528" y1="64" x2="528" y2="438" stroke="{COLORS["divider"]}" stroke-width="1.2"/>',
        f'<image x="55" y="97" width="445" height="276" xlink:href="{left_scene.name}" preserveAspectRatio="none"/>',
        f'<image x="594" y="97" width="461" height="276" xlink:href="{right_scene.name}" preserveAspectRatio="none"/>',
    ]
    parts.extend(axes(55, 97, 445, 276, (-2.2, 3.5), (-2.6, 3.0), range(-2, 4), range(-2, 4), "x (m)", "z (m)"))
    parts.extend(axes(594, 97, 461, 276, (-3.2, 3.6), (-2.0, 3.0), range(-3, 4), range(-2, 4), "x (m)", "y (m)"))

    # Left: violated vertical prediction leaving Top-50.
    parts.extend(
        [
            '<rect x="241" y="266" width="51" height="70" fill="#e66101" fill-opacity="0.06" stroke="#e66101" stroke-width="1.4"/>',
            '<line x1="265" y1="295" x2="405" y2="113" stroke="#e31a1c" stroke-width="2.2" stroke-dasharray="10,7"/>',
            '<circle cx="265" cy="295" r="8.5" fill="#e66101" stroke="#ffffff" stroke-width="1.4"/>',
            text(406, 119, "×", 36, 700, COLORS["demote"], "middle"),
        ]
    )
    parts.extend(label_box(241, 307, 54, "desk", COLORS["subject"]))
    parts.extend(label_box(431, 96, 61, "ceiling", COLORS["object"]))

    # Right: exact-label proximity prediction entering Top-50.
    parts.extend(
        [
            '<rect x="748" y="219" width="62" height="70" fill="#e66101" fill-opacity="0.06" stroke="#e66101" stroke-width="1.4"/>',
            '<rect x="922" y="231" width="61" height="64" fill="#164dcc" fill-opacity="0.05" stroke="#164dcc" stroke-width="1.4"/>',
            '<line x1="779" y1="250" x2="952" y2="269" stroke="#006d6f" stroke-width="3.0"/>',
            '<circle cx="779" cy="250" r="8.5" fill="#e66101" stroke="#ffffff" stroke-width="1.4"/>',
            '<path d="M952 257 L964 269 L952 281 L940 269 Z" fill="#164dcc" stroke="#ffffff" stroke-width="1.4"/>',
        ]
    )
    parts.extend(label_box(750, 200, 58, "desk", COLORS["subject"]))
    parts.extend(label_box(921, 202, 63, "chair", COLORS["object"]))

    parts.extend(
        [
            rank_text(270, 6, 425),
            rank_text(810, 81, 30),
            '</g>',
            '</svg>',
        ]
    )
    return "\n".join(parts)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    validation = validate_locked_case()
    source = Image.open(SOURCE_PNG).convert("RGBA")
    if source.size != (CANVAS_W, CANVAS_H):
        raise ValueError(f"unexpected supplied teaser size: {source.size}")

    left_scene = extract_scene_layer(source, "left", PANEL_CROPS["left"])
    right_scene = extract_scene_layer(source, "right", PANEL_CROPS["right"])
    svg_path = OUT_DIR / f"{OUTPUT_STEM}.svg"
    svg_path.write_text(render_svg(left_scene, right_scene), encoding="utf-8")

    manifest = {
        "schema_version": "relcompat3d_teaser_hybrid_v1",
        "status": "hybrid_svg_generated_case_lock_verified",
        "source_png": str(SOURCE_PNG.relative_to(ROOT)),
        "source_png_sha256": sha256(SOURCE_PNG),
        "source_geometry_manifest": str(SOURCE_MANIFEST.relative_to(ROOT)),
        "case_checks": validation["checks"],
        "canvas": {"width": CANVAS_W, "height": CANVAS_H},
        "raster_scale": RASTER_SCALE,
        "raster_layers": {
            "left": {
                "path": str(left_scene.relative_to(ROOT)),
                "sha256": sha256(left_scene),
                "pixel_size": list(Image.open(left_scene).size),
            },
            "right": {
                "path": str(right_scene.relative_to(ROOT)),
                "sha256": sha256(right_scene),
                "pixel_size": list(Image.open(right_scene).size),
            },
        },
        "vector_content": [
            "titles",
            "relation labels",
            "axes and ticks",
            "object labels and markers",
            "relation lines",
            "rank outcomes",
        ],
        "svg": str(svg_path.relative_to(ROOT)),
        "svg_sha256": sha256(svg_path),
    }
    manifest_path = OUT_DIR / f"{OUTPUT_STEM}_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(svg_path)
    print(manifest_path)


if __name__ == "__main__":
    main()
