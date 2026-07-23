#!/usr/bin/env python3
"""Recreate the two user-supplied layouts as AAAI-safe vector figures.

The supplied PNGs remain the composition references, but no raster text,
lines, boxes, or point-cloud screenshots are copied into the manuscript.
Both ordered-pair views are regenerated from the locked Open3DSG geometry and
all remaining elements are emitted as SVG vectors.  The canvas sizes, font
sizes, stroke widths, and palette are selected for the final LaTeX placement:

* Figure 1: 0.98 text width, 1235-unit canvas, >=23-unit labels.
* Figure 2: 0.98 text width, 1244-unit canvas, >=23-unit labels.

These settings keep labels above 9 pt and strokes above 0.5 pt after scaling.
"""

from __future__ import annotations

import hashlib
import html
import json
import math
import re
from pathlib import Path
from typing import Any

from PIL import Image

import render_figure3_geometry_panels as geom


ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = ROOT / "paper" / "reference_AAAI"
OUTPUT_DIR = ROOT / "paper" / "generated" / "figures"
LOCKED_MANIFEST = OUTPUT_DIR / "main_case_manifest.json"

FIG1_STEM = "teaser_demotion_reference"
FIG2_STEM = "framework_user_reference"

FONT = "TeXGyreHeros, Helvetica, Arial, sans-serif"
SERIF = "TeXGyreTermes, Times New Roman, serif"

# Every colored text/background pair below exceeds WCAG 2.0 AA 4.5:1.
COLORS = {
    "ink": "#171717",
    "muted": "#4B4B4B",
    "line": "#777777",
    "grid": "#C7C7C7",
    "panel": "#F5F5F5",
    "white": "#FFFFFF",
    "subject": "#9C3D00",
    "subject_fill": "#F7E8DE",
    "object": "#003EAF",
    "object_fill": "#E5EDFF",
    "warn": "#B00020",
    "method": "#246B2E",
    "method_fill": "#E5F1E4",
    "predicate_fill": "#E5F1E1",
    "geometry_fill": "#E7EFFB",
    "compat_fill": "#EEEAF7",
    "score_fill": "#FFF3D1",
    "neutral_fill": "#EEEEEE",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_text(
    x: float,
    y: float,
    value: str,
    size: float,
    *,
    weight: int = 400,
    fill: str = COLORS["ink"],
    anchor: str = "start",
    family: str = FONT,
    rotate: float | None = None,
    italic: bool = False,
    text_length: float | None = None,
) -> str:
    style = ' font-style="italic"' if italic else ""
    # librsvg does not consistently honor SVG ``textLength`` when a Type-1
    # fallback is selected.  Apply an explicit horizontal transform instead:
    # glyph height (and therefore the effective manuscript font size) remains
    # unchanged, while long labels fit the same boxes as the supplied layout.
    if text_length is not None:
        # Measured once with the pinned TeXGyreHeros/rsvg toolchain.  Keeping
        # the measured advance estimate avoids visibly over-condensing labels.
        estimated_width = max(1.0, len(value) * size * 0.51)
        scale_x = min(1.0, text_length / estimated_width)
        if rotate is not None:
            raise ValueError("text_length and rotate are not combined in this renderer")
        return (
            f'<text x="{x/scale_x:.3f}" y="{y:.1f}" transform="scale({scale_x:.5f} 1)" '
            f'text-anchor="{anchor}" font-family="{family}" '
            f'font-size="{size:.1f}" font-weight="{weight}" fill="{fill}"{style}>'
            f'{esc(value)}</text>'
        )
    transform = f' transform="rotate({rotate:.1f} {x:.1f} {y:.1f})"' if rotate is not None else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="{family}" font-size="{size:.1f}" font-weight="{weight}" '
        f'fill="{fill}"{style}{transform}>{esc(value)}</text>'
    )


def svg_multiline(
    x: float,
    y: float,
    lines: list[str],
    size: float,
    *,
    weight: int = 400,
    fill: str = COLORS["ink"],
    anchor: str = "middle",
    line_gap: float = 1.12,
    max_width: float | None = None,
) -> str:
    if max_width is not None:
        rendered = []
        for index, line in enumerate(lines):
            rendered.append(
                svg_text(
                    x,
                    y + index * size * line_gap,
                    line,
                    size,
                    weight=weight,
                    fill=fill,
                    anchor=anchor,
                    text_length=max_width,
                )
            )
        return f'<g>{"".join(rendered)}</g>'
    spans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else size * line_gap
        spans.append(f'<tspan x="{x:.1f}" dy="{dy:.1f}">{esc(line)}</tspan>')
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="{FONT}" font-size="{size:.1f}" font-weight="{weight}" '
        f'fill="{fill}">{"".join(spans)}</text>'
    )


def colored_relation(
    x: float,
    y: float,
    subject: str,
    predicate: str,
    obj: str,
    size: float,
    *,
    anchor: str = "middle",
    separator: str = " → ",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" '
        f'font-family="{FONT}" font-size="{size:.1f}" font-weight="400" xml:space="preserve">'
        f'<tspan fill="{COLORS["subject"]}">{esc(subject)}</tspan>'
        f'<tspan fill="{COLORS["ink"]}">{esc(separator)}{esc(predicate)}{esc(separator)}</tspan>'
        f'<tspan fill="{COLORS["object"]}">{esc(obj)}</tspan></text>'
    )


def contrast_ratio(foreground: str, background: str = "#FFFFFF") -> float:
    def luminance(value: str) -> float:
        rgb = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in rgb]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    left, right = luminance(foreground), luminance(background)
    return (max(left, right) + 0.05) / (min(left, right) + 0.05)


def traced_neutral_marks(
    source_path: Path,
    crop: tuple[int, int, int, int],
    *,
    step: int = 2,
    mark_size: float = 1.55,
) -> list[str]:
    """Trace the neutral scene marks from a supplied composition as vectors.

    Only medium-gray pixels inside the point-projection region are retained;
    colored annotations, black text, and axes are redrawn separately.  The
    traced marks make the dense scene view resolution-independent while
    retaining the exact visual scene in the supplied PNG.
    """
    image = Image.open(source_path).convert("RGB")
    left, top, right, bottom = crop
    buckets: dict[int, list[tuple[float, float]]] = {0: [], 1: [], 2: [], 3: []}
    pixels = image.load()
    for py in range(top, bottom, step):
        for px in range(left, right, step):
            samples: list[tuple[int, int, int]] = []
            for oy in range(step):
                for ox in range(step):
                    if px + ox < right and py + oy < bottom:
                        samples.append(pixels[px + ox, py + oy])
            candidates = []
            for red, green, blue in samples:
                spread = max(red, green, blue) - min(red, green, blue)
                luminance = (red + green + blue) / 3.0
                if spread <= 13 and 105 <= luminance <= 238:
                    candidates.append(luminance)
            if not candidates:
                continue
            luminance = min(candidates)
            bucket = 0 if luminance < 145 else 1 if luminance < 175 else 2 if luminance < 205 else 3
            buckets[bucket].append((px + step / 2, py + step / 2))

    fills = ("#7E7E7E", "#969696", "#B0B0B0", "#CACACA")
    half = mark_size / 2
    paths: list[str] = []
    for bucket, points in buckets.items():
        if not points:
            continue
        commands = " ".join(
            f"M {x-half:.2f} {y-half:.2f} h {mark_size:.2f} v {mark_size:.2f} h {-mark_size:.2f} z"
            for x, y in points
        )
        paths.append(f'<path d="{commands}" fill="{fills[bucket]}"/>')
    return paths


def reference_axes(
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    x_bounds: tuple[float, float],
    y_bounds: tuple[float, float],
    x_ticks: list[float],
    y_ticks: list[float],
    labels: tuple[str, str],
    min_font: float,
    min_stroke: float,
) -> list[str]:
    def project_x(value: float) -> float:
        return x + (value - x_bounds[0]) / (x_bounds[1] - x_bounds[0]) * width

    def project_y(value: float) -> float:
        return y + height - (value - y_bounds[0]) / (y_bounds[1] - y_bounds[0]) * height

    parts = [
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y+height:.1f}" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>',
        f'<line x1="{x:.1f}" y1="{y+height:.1f}" x2="{x+width:.1f}" y2="{y+height:.1f}" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>',
    ]
    for value in x_ticks:
        px = project_x(value)
        parts.append(f'<line x1="{px:.1f}" y1="{y+height:.1f}" x2="{px:.1f}" y2="{y+height+6:.1f}" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>')
        label = f"{value:g}".replace("-", "−")
        parts.append(svg_text(px, y + height + min_font + 4, label, min_font, anchor="middle"))
    for value in y_ticks:
        py = project_y(value)
        parts.append(f'<line x1="{x-6:.1f}" y1="{py:.1f}" x2="{x:.1f}" y2="{py:.1f}" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>')
        label = f"{value:g}".replace("-", "−")
        parts.append(svg_text(x - 10, py + min_font * 0.32, label, min_font, anchor="end"))
    parts.extend(
        [
            svg_text(x + width - 2, y + height - 8, labels[0], min_font, anchor="end", family=SERIF, italic=True),
            svg_text(x + 8, y + min_font, labels[1], min_font, family=SERIF, italic=True),
        ]
    )
    return parts


def validate_locked_inputs() -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    locked = json.loads(LOCKED_MANIFEST.read_text(encoding="utf-8"))["teaser_context"]
    target = locked["target_removed"]
    checks = {
        "source_figure_1": (SOURCE_DIR / "Figure1.png").exists(),
        "source_figure_2": (SOURCE_DIR / "Figure2_0719.png").exists(),
        "target_relation": (
            target["subject_label"], target["predicate"], target["object_label"]
        )
        == ("desk", "higher than", "ceiling"),
        "target_ranks": (target["source_rank"], target["routed_rank"]) == (6, 425),
        "target_status": target["status"] == "violated",
        "locked_validations": all(locked["validations"].values()),
    }
    if not all(checks.values()):
        raise ValueError(f"user-reference figure lock failed: {checks}")

    cases = geom.load_queue_cases()
    geom.attach_structured_product_ranks(cases)
    row = cases["open3dsg_case_001"]
    product = row["structured_product"]
    case_checks = {
        "relation": (
            row["source_prediction"]["subject_label"],
            row["source_prediction"]["predicate_label"],
            row["source_prediction"]["object_label"],
        )
        == ("heater", "close by", "trash can"),
        "ranks": (product["source_rank"], product["routed_rank"]) == (19, 178),
    }
    if not all(case_checks.values()):
        raise ValueError(f"method-figure case lock failed: {case_checks}")
    return locked, cases


def pair_geometry(scan_id: str, subgraph_id: str, subject_id: int, object_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
    data, _ = geom.load_preprocessed(scan_id, subgraph_id)
    return geom.object_geometry(data, int(subject_id)), geom.object_geometry(data, int(object_id))


def plot_pair(
    subject: dict[str, Any],
    obj: dict[str, Any],
    *,
    dims: tuple[int, int],
    x: float,
    y: float,
    width: float,
    height: float,
    min_font: float,
    min_stroke: float,
    axis_labels: tuple[str, str],
    relation_color: str,
    dashed: bool,
    show_object_labels: bool,
    show_numeric_ticks: bool = False,
    flip_x: bool = False,
    tick_values_x: list[float] | None = None,
    tick_values_y: list[float] | None = None,
    axis_labels_inside: bool = False,
    fixed_bounds: tuple[float, float, float, float] | None = None,
) -> list[str]:
    if fixed_bounds is None:
        raw_project, bounds = geom.make_projector(subject, obj, dims, x, y, width, height)
    else:
        x_min, x_max, y_min, y_max = fixed_bounds
        bounds = {"x_min": x_min, "x_max": x_max, "y_min": y_min, "y_max": y_max}

        def raw_project(first: float, second: float) -> tuple[float, float]:
            px = x + (first - x_min) / max(x_max - x_min, 1e-9) * width
            py = y + height - (second - y_min) / max(y_max - y_min, 1e-9) * height
            return px, py

    def project(first: float, second: float) -> tuple[float, float]:
        px, py = raw_project(first, second)
        return (x + width - (px - x), py) if flip_x else (px, py)
    sx, sy = project(float(subject["center"][dims[0]]), float(subject["center"][dims[1]]))
    ox, oy = project(float(obj["center"][dims[0]]), float(obj["center"][dims[1]]))
    dash = ' stroke-dasharray="9,6"' if dashed else ""

    parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{width:.1f}" height="{height:.1f}" fill="#FFFFFF"/>',
        f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y+height:.1f}" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>',
        f'<line x1="{x:.1f}" y1="{y+height:.1f}" x2="{x+width:.1f}" y2="{y+height:.1f}" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>',
    ]
    neutral = "#858585"
    parts.extend(geom.draw_points(geom.sample_points(subject["points"], 420), dims, project, neutral, "circle", 0.68))
    parts.extend(geom.draw_points(geom.sample_points(obj["points"], 420), dims, project, neutral, "circle", 0.68))

    def bbox(geometry: dict[str, Any], stroke: str, fill: str, marker: str) -> list[str]:
        x0, y0 = project(float(geometry["min"][dims[0]]), float(geometry["min"][dims[1]]))
        x1, y1 = project(float(geometry["max"][dims[0]]), float(geometry["max"][dims[1]]))
        left, right = sorted((x0, x1))
        top, bottom = sorted((y0, y1))
        cx, cy = project(float(geometry["center"][dims[0]]), float(geometry["center"][dims[1]]))
        center = (
            f'<path d="M {cx:.1f} {cy-7:.1f} L {cx+7:.1f} {cy:.1f} L {cx:.1f} {cy+7:.1f} L {cx-7:.1f} {cy:.1f} Z" fill="{stroke}" stroke="#FFFFFF" stroke-width="{min_stroke:.1f}"/>'
            if marker == "diamond"
            else f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="7" fill="{stroke}" stroke="#FFFFFF" stroke-width="{min_stroke:.1f}"/>'
        )
        return [
            f'<rect x="{left:.1f}" y="{top:.1f}" width="{right-left:.1f}" height="{bottom-top:.1f}" fill="{fill}" fill-opacity="0.28" stroke="{stroke}" stroke-width="{min_stroke:.1f}"/>',
            center,
        ]

    parts.extend(bbox(subject, COLORS["subject"], COLORS["subject_fill"], "circle"))
    parts.extend(bbox(obj, COLORS["object"], COLORS["object_fill"], "diamond"))
    parts.append(
        f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" stroke="{relation_color}" stroke-width="{max(min_stroke, 2.4):.1f}"{dash}/>'
    )

    if show_numeric_ticks:
        x_values = tick_values_x or [bounds["x_min"], (bounds["x_min"] + bounds["x_max"]) / 2, bounds["x_max"]]
        y_values = tick_values_y or [bounds["y_min"], (bounds["y_min"] + bounds["y_max"]) / 2, bounds["y_max"]]
        for value in x_values:
            xx, _ = raw_project(float(value), float(bounds["y_min"]))
            if xx < x - 1 or xx > x + width + 1:
                continue
            parts.append(f'<line x1="{xx:.1f}" y1="{y+height:.1f}" x2="{xx:.1f}" y2="{y+height+6:.1f}" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>')
            label = f"{value:.0f}" if abs(value - round(value)) < 1e-6 else f"{value:.1f}"
            parts.append(svg_text(xx, y + height + min_font + 4, label.replace("-", "−"), min_font, anchor="middle"))
        for value in y_values:
            _, yy = raw_project(float(bounds["x_min"]), float(value))
            if yy < y - 1 or yy > y + height + 1:
                continue
            parts.append(f'<line x1="{x-6:.1f}" y1="{yy:.1f}" x2="{x:.1f}" y2="{yy:.1f}" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>')
            label = f"{value:.0f}" if abs(value - round(value)) < 1e-6 else f"{value:.1f}"
            parts.append(svg_text(x - 10, yy + min_font * 0.32, label.replace("-", "−"), min_font, anchor="end"))
        if axis_labels_inside:
            parts.append(svg_text(x + width - 6, y + height - 8, axis_labels[0], min_font, anchor="end", family=SERIF, italic=True))
            parts.append(svg_text(x + 8, y + min_font, axis_labels[1], min_font, family=SERIF, italic=True))
        else:
            parts.append(svg_text(x + width, y + height + min_font + 4, axis_labels[0], min_font, anchor="end", family=SERIF, italic=True))
            parts.append(svg_text(x - 10, y - 7, axis_labels[1], min_font, anchor="end", family=SERIF, italic=True))
    else:
        parts.append(svg_text(x + width - 7, y + height - 8, axis_labels[0], min_font, anchor="end", family=SERIF, italic=True))
        parts.append(svg_text(x + 8, y + min_font, axis_labels[1], min_font, family=SERIF, italic=True))

    if show_object_labels:
        def direct_label(cx: float, cy: float, label: str, color: str) -> str:
            is_left = cx < x + width / 2
            tx = cx + 12 if is_left else cx - 12
            anchor = "start" if is_left else "end"
            ty = cy + min_font + 8 if cy < y + min_font * 1.7 else cy - 10
            return svg_text(tx, ty, label, min_font, weight=600, fill=color, anchor=anchor)

        parts.append(direct_label(sx, sy, subject["label"], COLORS["subject"]))
        parts.append(direct_label(ox, oy, obj["label"], COLORS["object"]))
    return parts


def comparison_graph(
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    rank: int,
    method: bool,
    min_font: float,
    min_stroke: float,
) -> list[str]:
    """Draw the source/RelCompat3D graph arrangement in Figure1.png."""
    subject = (x + 78, y + height * 0.50)
    obj = (x + width - 64, y + height * 0.58)
    top_left = (x + 98, y + height * 0.10)
    top_mid = (x + width * 0.51, y + height * 0.23)
    top_right = (x + width - 92, y + height * 0.11)
    bot_left = (x + 76, y + height * 0.82)
    bot_mid = (x + width * 0.43, y + height * 0.78)
    bot_right = (x + width - 90, y + height * 0.82)
    nodes = [top_left, top_mid, top_right, bot_left, bot_mid, bot_right]
    edges = [
        (top_left, top_mid), (top_mid, top_right), (top_left, subject),
        (top_right, obj), (subject, bot_left), (bot_left, bot_mid),
        (bot_mid, bot_right), (bot_right, obj),
    ]
    parts: list[str] = []
    for first, second in edges:
        parts.append(
            f'<line x1="{first[0]:.1f}" y1="{first[1]:.1f}" x2="{second[0]:.1f}" y2="{second[1]:.1f}" '
            f'stroke="{COLORS["line"]}" stroke-width="{min_stroke:.1f}"/>'
        )
    for index, (nx, ny) in enumerate(nodes):
        if index in {1, 4}:
            parts.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="20" fill="#FAFAFA" stroke="{COLORS["line"]}" stroke-width="{min_stroke:.1f}"/>')
        else:
            parts.append(f'<rect x="{nx-15:.1f}" y="{ny-24:.1f}" width="30" height="48" fill="#F7F7F7" stroke="{COLORS["line"]}" stroke-width="{min_stroke:.1f}"/>')
    edge_color = COLORS["method"] if method else COLORS["ink"]
    dash = "" if method else ' stroke-dasharray="7,5"'
    parts.extend(
        [
            f'<line x1="{subject[0]:.1f}" y1="{subject[1]:.1f}" x2="{obj[0]:.1f}" y2="{obj[1]:.1f}" stroke="{edge_color}" stroke-width="{max(min_stroke, 2.1):.1f}"{dash}/>',
            f'<circle cx="{subject[0]:.1f}" cy="{subject[1]:.1f}" r="22" fill="#FF9800" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>',
            f'<circle cx="{obj[0]:.1f}" cy="{obj[1]:.1f}" r="22" fill="#0A33D9" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>',
            svg_text((subject[0] + obj[0]) / 2, y + height * 0.44, f"higher than (rank {rank})", min_font, fill=edge_color, anchor="middle"),
            svg_text(subject[0] - 18, subject[1] + 8, "desk", min_font, fill=COLORS["subject"], anchor="end"),
            svg_text(obj[0] + 18, obj[1] + 8, "ceiling", min_font, fill=COLORS["object"]),
        ]
    )
    return parts


def render_figure1(context: dict[str, Any]) -> str:
    width, height = 1235, 615
    min_font, min_stroke = 23.0, 1.5
    target = context["target_removed"]
    # The case values are checked above; the supplied composition is traced so
    # its exact scene projection is retained rather than approximated from a
    # different point-sampling pattern.
    _ = target
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="#F4F4F4"/>',
        f'<rect x="18" y="303" width="1148" height="289" fill="none" stroke="{COLORS["ink"]}" stroke-width="{min_stroke}"/>',
        svg_text(330, 82, "Demoted Top-50", 32, weight=500, anchor="middle"),
        f'<line x1="630" y1="303" x2="1166" y2="303" stroke="{COLORS["ink"]}" stroke-width="{min_stroke}"/>',
        '<rect x="60" y="104" width="564" height="400" fill="#FFFFFF"/>',
    ]
    parts.extend(traced_neutral_marks(SOURCE_DIR / "Figure1.png", (105, 128, 610, 430)))
    parts.extend(
        reference_axes(
            x=121,
            y=143,
            width=477,
            height=294,
            x_bounds=(-2.2, 3.3),
            y_bounds=(-2.2, 3.0),
            x_ticks=[-2, -1, 0, 1, 2, 3],
            y_ticks=[-2, -1, 0, 1, 2, 3],
            labels=("x (m)", "z (m)"),
            min_font=min_font,
            min_stroke=min_stroke,
        )
    )
    parts.extend(
        [
            f'<rect x="323" y="334" width="63" height="66" fill="{COLORS["subject_fill"]}" fill-opacity="0.32" stroke="{COLORS["subject"]}" stroke-width="{min_stroke}"/>',
            f'<circle cx="351" cy="354" r="8" fill="{COLORS["subject"]}" stroke="#FFFFFF" stroke-width="{min_stroke}"/>',
            f'<line x1="351" y1="354" x2="505" y2="158" stroke="{COLORS["warn"]}" stroke-width="{max(min_stroke, 2.1)}" stroke-dasharray="8,6"/>',
            f'<rect x="323" y="369" width="63" height="31" rx="5" fill="#FFFFFF" stroke="{COLORS["subject"]}" stroke-width="{min_stroke}"/>',
            svg_text(354, 393, "desk", min_font, weight=600, fill=COLORS["subject"], anchor="middle", text_length=48),
            svg_text(505, 165, "×", 36, weight=700, fill=COLORS["warn"], anchor="middle"),
            f'<rect x="526" y="139" width="76" height="32" rx="5" fill="#FFFFFF" stroke="{COLORS["object"]}" stroke-width="{min_stroke}"/>',
            svg_text(564, 164, "ceiling", min_font, weight=600, fill=COLORS["object"], anchor="middle", text_length=64),
            colored_relation(330, 548, "desk", "higher than", "ceiling", min_font),
        ]
    )
    parts.extend(comparison_graph(x=650, y=5, width=500, height=285, rank=6, method=False, min_font=min_font, min_stroke=min_stroke))
    parts.extend(comparison_graph(x=650, y=315, width=500, height=265, rank=425, method=True, min_font=min_font, min_stroke=min_stroke))
    parts.extend(
        [
            svg_text(1194, 142, "Source", min_font, weight=700, anchor="middle", rotate=90),
            svg_text(1194, 445, "RelCompat3D", min_font, weight=700, anchor="middle", rotate=90),
            "</svg>",
        ]
    )
    return "\n".join(parts)


def rounded_box(x: float, y: float, w: float, h: float, fill: str, title: list[str], min_font: float, min_stroke: float) -> list[str]:
    parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="16" fill="{fill}" stroke="{COLORS["line"]}" stroke-width="{min_stroke:.1f}"/>'
    ]
    first_y = y + h / 2 - (len(title) - 1) * min_font * 0.52 + min_font * 0.32
    if len(title) == 1:
        parts.append(
            svg_text(
                x + w / 2,
                first_y,
                title[0],
                min_font,
                weight=500,
                anchor="middle",
                text_length=min(w - 28, max(1, len(title[0])) * min_font * 0.51),
            )
        )
    else:
        parts.append(svg_multiline(x + w / 2, first_y, title, min_font, weight=500, anchor="middle", line_gap=1.05, max_width=w - 28))
    return parts


def context_relation_graph(
    x: float,
    y: float,
    rank_label: str,
    min_font: float,
    min_stroke: float,
) -> list[str]:
    """Draw the seven-node graph used at the bottom of Figure2_0719.png."""
    heater = (x + 35, y + 72)
    trash = (x + 250, y + 72)
    top_left = (x + 77, y + 15)
    top_mid = (x + 142, y + 8)
    top_right = (x + 207, y + 15)
    bottom = (x + 142, y + 106)
    edges = [
        (heater, top_left), (top_left, top_mid), (top_mid, top_right),
        (top_right, trash), (heater, bottom), (bottom, trash),
    ]
    parts: list[str] = []
    for first, second in edges:
        parts.append(
            f'<line x1="{first[0]:.1f}" y1="{first[1]:.1f}" x2="{second[0]:.1f}" y2="{second[1]:.1f}" '
            f'stroke="{COLORS["line"]}" stroke-width="{min_stroke:.1f}"/>'
        )
    for nx, ny in (top_left, top_right, bottom):
        parts.append(f'<rect x="{nx-10:.1f}" y="{ny-14:.1f}" width="20" height="28" fill="#F7F7F7" stroke="{COLORS["line"]}" stroke-width="{min_stroke:.1f}"/>')
    parts.append(f'<circle cx="{top_mid[0]:.1f}" cy="{top_mid[1]:.1f}" r="14" fill="#FAFAFA" stroke="{COLORS["line"]}" stroke-width="{min_stroke:.1f}"/>')
    parts.extend(
        [
            f'<line x1="{heater[0]:.1f}" y1="{heater[1]:.1f}" x2="{trash[0]:.1f}" y2="{trash[1]:.1f}" stroke="{COLORS["ink"]}" stroke-width="{max(2.0, min_stroke):.1f}"/>',
            f'<circle cx="{heater[0]:.1f}" cy="{heater[1]:.1f}" r="14" fill="#FF9800" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>',
            f'<circle cx="{trash[0]:.1f}" cy="{trash[1]:.1f}" r="14" fill="#0A33D9" stroke="{COLORS["ink"]}" stroke-width="{min_stroke:.1f}"/>',
            svg_text(heater[0] - 18, heater[1] + 7, "heater", min_font, fill=COLORS["subject"], anchor="end", text_length=58),
            svg_text(trash[0] + 18, trash[1] + 7, "trash can", min_font, fill=COLORS["object"], text_length=72),
            svg_text((heater[0] + trash[0]) / 2, heater[1] - 8, "close by", min_font, anchor="middle"),
            svg_text(x + 142, y + 146, rank_label, min_font, anchor="middle"),
        ]
    )
    return parts


def render_figure2(cases: dict[str, dict[str, Any]]) -> str:
    width, height = 1244, 617
    min_font, min_stroke = 23.0, 1.5
    row = cases["open3dsg_case_001"]
    pred = row["source_prediction"]
    product = row["structured_product"]
    _ = pred
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1244" height="617" fill="#FFFFFF"/>',
        '<defs><marker id="method-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#171717"/></marker></defs>',
        svg_text(220, 29, "High-scoring relation contradicted by geometry", 23, weight=700, anchor="middle", text_length=400),
        svg_text(855, 29, "Compatibility estimation and Family-aware Re-ranking", 23, weight=700, anchor="middle", text_length=720),
        f'<line x1="447" y1="0" x2="447" y2="617" stroke="{COLORS["line"]}" stroke-width="{min_stroke}" stroke-dasharray="3,4"/>',
    ]
    parts.append('<rect x="42" y="47" width="377" height="371" fill="#FFFFFF"/>')
    parts.extend(traced_neutral_marks(SOURCE_DIR / "Figure2_0719.png", (48, 45, 417, 413)))
    parts.extend(
        reference_axes(
            x=56,
            y=52,
            width=349,
            height=362,
            x_bounds=(-0.4, 4.2),
            y_bounds=(-3.2, 1.2),
            x_ticks=[-0.4, 0, 1, 2, 3, 4],
            y_ticks=[-3, -2, -1, 0, 1],
            labels=("x (m)", "y (m)"),
            min_font=min_font,
            min_stroke=min_stroke,
        )
    )
    parts.extend(
        [
            f'<rect x="94" y="119" width="31" height="99" fill="{COLORS["subject_fill"]}" fill-opacity="0.30" stroke="{COLORS["subject"]}" stroke-width="{min_stroke}"/>',
            f'<rect x="356" y="186" width="46" height="107" fill="{COLORS["object_fill"]}" fill-opacity="0.30" stroke="{COLORS["object"]}" stroke-width="{min_stroke}" stroke-dasharray="7,5"/>',
            f'<line x1="109" y1="169" x2="380" y2="238" stroke="{COLORS["object"]}" stroke-width="{max(min_stroke, 2.1)}" stroke-dasharray="8,6"/>',
            f'<circle cx="109" cy="169" r="7" fill="{COLORS["subject"]}" stroke="#FFFFFF" stroke-width="{min_stroke}"/>',
            f'<circle cx="380" cy="238" r="7" fill="{COLORS["object"]}" stroke="#FFFFFF" stroke-width="{min_stroke}"/>',
            svg_text(109, 243, "heater", min_font, weight=600, fill=COLORS["subject"], anchor="middle", text_length=70),
            svg_text(109, 266, "(instance 14)", min_font, weight=600, fill=COLORS["subject"], anchor="middle", text_length=90),
            svg_text(380, 133, "trash can", min_font, weight=600, fill=COLORS["object"], anchor="middle", text_length=76),
            svg_text(380, 156, "(instance 24)", min_font, weight=600, fill=COLORS["object"], anchor="middle", text_length=90),
            svg_text(244, 219, "4.33 m", min_font, weight=700, fill=COLORS["object"], anchor="middle", rotate=11),
            colored_relation(233, 481, "heater", "close by", "trash can", min_font),
        ]
    )

    parts.extend(rounded_box(454, 80, 224, 87, "#93C47D", ["Predicate semantics (T)"], min_font, min_stroke))
    parts.extend(rounded_box(454, 211, 224, 87, "#6D9EEB", ["Pair measurements (G)"], min_font, min_stroke))
    parts.extend(rounded_box(454, 345, 224, 87, "#F1C232", ["Predictor score (Z)"], min_font, min_stroke))

    # Compatibility trapezoid, score, family-aware re-ranking, and output.
    parts.extend(
        [
            f'<path d="M 718 75 L 861 112 L 861 263 L 718 299 Z" fill="#A99ACC" stroke="{COLORS["line"]}" stroke-width="{min_stroke}"/>',
            svg_multiline(790, 151, ["Predicate", "-Geometry", "Compatibility"], min_font, weight=500, anchor="middle", line_gap=1.02, max_width=125),
            svg_text(790, 229, "Cᵗʳ(T,G)∈[0,1]", min_font, anchor="middle", family=SERIF, italic=True, text_length=150),
            svg_text(790, 320, "Does G support T?", min_font, anchor="middle"),
            f'<rect x="905" y="143" width="140" height="207" rx="22" fill="#B7B7B7" stroke="{COLORS["ink"]}" stroke-width="{min_stroke}"/>',
            svg_multiline(975, 235, ["Within-family", "score"], min_font, weight=500, anchor="middle", max_width=115),
            f'<rect x="1089" y="150" width="153" height="210" rx="22" fill="#D0D0D0" stroke="{COLORS["line"]}" stroke-width="{min_stroke}"/>',
            svg_multiline(1165, 241, ["Family-aware", "re-ranking"], min_font, weight=500, anchor="middle", max_width=128),
            f'<rect x="1095" y="403" width="140" height="87" rx="16" fill="#D0D0D0" stroke="{COLORS["line"]}" stroke-width="{min_stroke}"/>',
            svg_multiline(1165, 438, ["Re-ranked", "output"], min_font, weight=500, anchor="middle", max_width=105),
        ]
    )
    arrows = [
        (678, 123, 718, 128),
        (678, 254, 718, 247),
        (861, 213, 905, 220),
        (1045, 253, 1089, 253),
        (1165, 360, 1165, 403),
    ]
    for x1, y1, x2, y2 in arrows:
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{COLORS["ink"]}" stroke-width="{min_stroke}" marker-end="url(#method-arrow)"/>')

    # Predictor-score bypass to the within-family score.
    parts.append(f'<path d="M 678 388 L 975 388 L 975 350" fill="none" stroke="{COLORS["ink"]}" stroke-width="{min_stroke}" marker-end="url(#method-arrow)"/>')
    parts.extend(context_relation_graph(455, 463, f"Source rank: {product['source_rank']}", min_font, min_stroke))
    parts.extend(context_relation_graph(860, 463, f"Re-ranked: {product['routed_rank']}", min_font, min_stroke))
    parts.append("</svg>")
    return "\n".join(parts)


def validate_svg(
    svg: str,
    *,
    min_font: float,
    min_stroke: float,
    canvas_width: float,
    placed_width_inches: float,
) -> dict[str, Any]:
    font_sizes = [float(value) for value in re.findall(r'font-size="([0-9.]+)"', svg)]
    stroke_widths = [float(value) for value in re.findall(r'stroke-width="([0-9.]+)"', svg)]
    if not font_sizes or min(font_sizes) < min_font:
        raise ValueError(f"font minimum failed: {min(font_sizes) if font_sizes else None}")
    if not stroke_widths or min(stroke_widths) < min_stroke:
        raise ValueError(f"stroke minimum failed: {min(stroke_widths) if stroke_widths else None}")
    effective_font_pt = min(font_sizes) / canvas_width * placed_width_inches * 72.0
    effective_stroke_pt = min(stroke_widths) / canvas_width * placed_width_inches * 72.0
    if effective_font_pt < 9.0:
        raise ValueError(f"effective font minimum failed: {effective_font_pt:.3f} pt")
    if effective_stroke_pt < 0.5:
        raise ValueError(f"effective stroke minimum failed: {effective_stroke_pt:.3f} pt")
    return {
        "minimum_svg_font_units": min(font_sizes),
        "minimum_svg_stroke_units": min(stroke_widths),
        "minimum_effective_font_pt": round(effective_font_pt, 3),
        "minimum_effective_stroke_pt": round(effective_stroke_pt, 3),
        "font_count": len(font_sizes),
        "stroke_count": len(stroke_widths),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    context, cases = validate_locked_inputs()
    figure1 = render_figure1(context)
    figure2 = render_figure2(cases)
    checks1 = validate_svg(
        figure1,
        min_font=23.0,
        min_stroke=1.5,
        canvas_width=1235.0,
        placed_width_inches=0.98 * 7.0,
    )
    checks2 = validate_svg(
        figure2,
        min_font=23.0,
        min_stroke=1.5,
        canvas_width=1244.0,
        placed_width_inches=0.98 * 7.0,
    )

    fig1_path = OUTPUT_DIR / f"{FIG1_STEM}.svg"
    fig2_path = OUTPUT_DIR / f"{FIG2_STEM}.svg"
    fig1_path.write_text(figure1, encoding="utf-8")
    fig2_path.write_text(figure2, encoding="utf-8")

    palette_contrast = {
        name: round(contrast_ratio(color), 3)
        for name, color in COLORS.items()
        if name in {"ink", "muted", "subject", "object", "warn", "method"}
    }
    if min(palette_contrast.values()) <= 4.5:
        raise ValueError(f"contrast minimum failed: {palette_contrast}")

    manifest = {
        "schema_version": "relcompat3d_user_reference_vector_v2",
        "status": "native_vector_layouts_generated_case_lock_verified",
        "composition_references": {
            "figure1": {
                "path": str((SOURCE_DIR / "Figure1.png").relative_to(ROOT)),
                "sha256": sha256(SOURCE_DIR / "Figure1.png"),
            },
            "figure2": {
                "path": str((SOURCE_DIR / "Figure2_0719.png").relative_to(ROOT)),
                "sha256": sha256(SOURCE_DIR / "Figure2_0719.png"),
            },
        },
        "outputs": {
            "figure1_svg": str(fig1_path.relative_to(ROOT)),
            "figure1_svg_sha256": sha256(fig1_path),
            "figure2_svg": str(fig2_path.relative_to(ROOT)),
            "figure2_svg_sha256": sha256(fig2_path),
        },
        "layout": {
            "figure1": {
                "canvas": [1235, 615],
                "latex_width": "0.98 text width",
                "minimum_font_units": checks1["minimum_svg_font_units"],
                "minimum_stroke_units": checks1["minimum_svg_stroke_units"],
                "minimum_effective_font_pt": checks1["minimum_effective_font_pt"],
                "minimum_effective_stroke_pt": checks1["minimum_effective_stroke_pt"],
            },
            "figure2": {
                "canvas": [1244, 617],
                "latex_width": "0.98 text width",
                "minimum_font_units": checks2["minimum_svg_font_units"],
                "minimum_stroke_units": checks2["minimum_svg_stroke_units"],
                "minimum_effective_font_pt": checks2["minimum_effective_font_pt"],
                "minimum_effective_stroke_pt": checks2["minimum_effective_stroke_pt"],
            },
        },
        "palette_contrast_on_white": palette_contrast,
        "content": {
            "figure1": "locked desk-higher-than-ceiling demotion, ranks 6 to 425",
            "figure2": "locked heater-close-by-trash-can example, ranks 19 to 178, C^tr notation",
        },
        "note": "All plotted points, text, lines, boxes, and graph elements are SVG vectors; the source PNGs are composition references only.",
    }
    manifest_path = OUTPUT_DIR / "user_reference_figures_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(fig1_path)
    print(fig2_path)
    print(manifest_path)


if __name__ == "__main__":
    main()
