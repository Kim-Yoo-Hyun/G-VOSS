#!/usr/bin/env python3
"""Generate draft GeoCalib paper figures from locked source artifacts.

The figures are draft SVGs for manuscript planning. They are intentionally
simple, traceable, and source-backed rather than camera-ready artwork.
"""

from __future__ import annotations

import html
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "paper" / "generated" / "figures"

VLSAT_FULL_METRICS = (
    ROOT / "experiments" / "H001_geom_reliability" / "sources" / "vlsat" / "full_validation" / "metrics" / "metrics.json"
)
OPEN3DSG_METRICS = (
    ROOT
    / "experiments"
    / "H001_geom_reliability"
    / "sources"
    / "open3dsg"
    / "full_validation"
    / "recovery_relaxed_views_min2"
    / "metrics"
    / "metrics.json"
)
INSPECTION_JSON = (
    ROOT
    / "experiments"
    / "H001_geom_reliability"
    / "sources"
    / "open3dsg"
    / "failure_cases"
    / "inspection.json"
)
LAYOUT_REVIEW = OUT_DIR / "layout_review.md"


COLORS = {
    "semantic_only": "#4b5563",
    "probabilistic_recalibrated": "#2563eb",
    "family_specific_p_geom_valid": "#059669",
    "rule_verified_point_subtype": "#dc2626",
    "axis": "#111827",
    "grid": "#d1d5db",
    "muted": "#6b7280",
    "panel": "#f8fafc",
    "ink": "#111827",
}

EXPECTED_FIGURE2 = {
    "VL-SAT": {
        "semantic_only": {"r100": 0.9635, "violation100": 0.0476},
        "probabilistic_recalibrated": {"r100": 0.9688, "violation100": 0.0404},
        "family_specific_p_geom_valid": {"r100": 0.9683, "violation100": 0.0333},
        "rule_verified_point_subtype": {"r100": 0.9627, "violation100": 0.0},
    },
    "Open3DSG": {
        "semantic_only": {"r100": 0.5161, "violation100": 0.1242},
        "probabilistic_recalibrated": {"r100": 0.5723, "violation100": 0.0811},
        "family_specific_p_geom_valid": {"r100": 0.6047, "violation100": 0.0341},
        "rule_verified_point_subtype": {"r100": 0.5368, "violation100": 0.0},
    },
}

EXPECTED_FIGURE3_CASES = [
    "open3dsg_case_001",
    "open3dsg_case_005",
    "open3dsg_case_010",
    "open3dsg_case_007",
]

LABELS = {
    "semantic_only": "semantic",
    "probabilistic_recalibrated": "prob.",
    "family_specific_p_geom_valid": "family",
    "rule_verified_point_subtype": "rule",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_text(x: float, y: float, text: str, size: int = 14, weight: int = 400, fill: str = "#111827",
             anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(text)}</text>'
    )


def wrapped_lines(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)


def svg_wrapped_text(x: float, y: float, text: str, width: int, line_height: int = 17,
                     size: int = 13, fill: str = "#111827", weight: int = 400) -> str:
    lines = wrapped_lines(text, width)
    parts = []
    for idx, line in enumerate(lines):
        parts.append(svg_text(x, y + idx * line_height, line, size=size, weight=weight, fill=fill))
    return "\n".join(parts)


def arrow_marker() -> str:
    return (
        '<defs>'
        '<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#374151"/></marker>'
        '</defs>'
    )


def box(x: int, y: int, w: int, h: int, title: str, body: str, fill: str = "#ffffff") -> str:
    text = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="#94a3b8" stroke-width="1.4"/>',
        svg_text(x + 16, y + 26, title, size=15, weight=700),
        svg_wrapped_text(x + 16, y + 52, body, width=24, size=12, fill="#374151"),
    ]
    return "\n".join(text)


def generate_figure1() -> str:
    width, height = 1280, 650
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="650" viewBox="0 0 1280 650">',
        '<rect width="1280" height="650" fill="#ffffff"/>',
        arrow_marker(),
        svg_text(50, 46, "Figure 1. GeoCalib: calibrated geometry-consistency re-ranking", 22, 700),
        svg_text(50, 74, "Relation-source graph edges become identity-preserved evidence records before recall-violation evaluation.", 14, 400, "#4b5563"),
    ]

    panels = [
        (50, 110, 340, 345, "A. Relation-source graph", "High semantic scores can rank plausible but physically inconsistent edges."),
        (470, 110, 340, 345, "B. Evidence-rich edge record", "The same subject-object edge is joined to explicit 3D evidence and calibrated validity."),
        (890, 110, 340, 345, "C. Reliable relation graph", "Re-ranking demotes violated edges and reports recall with geometric violation."),
    ]
    for x, y, w, h, title, subtitle in panels:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.4"/>')
        parts.append(svg_text(x + 20, y + 30, title, 16, 700))
        parts.append(svg_wrapped_text(x + 20, y + 55, subtitle, 42, 16, 12, "#475569"))

    parts.extend(
        [
            '<polygon points="90,375 350,375 325,245 115,245" fill="#eef2ff" stroke="#c7d2fe"/>',
            '<line x1="115" y1="245" x2="90" y2="375" stroke="#d1d5db" stroke-width="1"/>',
            '<line x1="185" y1="245" x2="175" y2="375" stroke="#d1d5db" stroke-width="1"/>',
            '<line x1="255" y1="245" x2="260" y2="375" stroke="#d1d5db" stroke-width="1"/>',
            '<line x1="325" y1="245" x2="350" y2="375" stroke="#d1d5db" stroke-width="1"/>',
            '<rect x="150" y="270" width="86" height="48" rx="5" fill="#bfdbfe" stroke="#2563eb" stroke-width="1.5"/>',
            '<rect x="170" y="237" width="42" height="34" rx="4" fill="#fde68a" stroke="#b45309" stroke-width="1.5"/>',
            '<rect x="275" y="310" width="40" height="50" rx="4" fill="#fecaca" stroke="#dc2626" stroke-width="1.5"/>',
            '<rect x="95" y="325" width="45" height="35" rx="4" fill="#bbf7d0" stroke="#059669" stroke-width="1.5"/>',
            svg_text(193, 333, "desk", 11, 700, "#1d4ed8", "middle"),
            svg_text(191, 230, "lamp", 11, 700, "#92400e", "middle"),
            svg_text(296, 303, "bin", 11, 700, "#991b1b", "middle"),
            svg_text(118, 318, "heater", 11, 700, "#047857", "middle"),
            '<path d="M190 237 C190 212 193 205 195 196" stroke="#059669" stroke-width="2.5" fill="none" marker-end="url(#arrow)"/>',
            svg_text(225, 214, "on 0.94", 12, 700, "#047857"),
            '<path d="M138 335 C190 302 245 296 275 324" stroke="#dc2626" stroke-width="2.5" fill="none" stroke-dasharray="5 3" marker-end="url(#arrow)"/>',
            svg_text(178, 292, "close by 0.88", 12, 700, "#b91c1c"),
            '<rect x="68" y="392" width="306" height="40" rx="6" fill="#fff7ed" stroke="#fb923c"/>',
            svg_text(86, 416, "Failure: plausible edge violates geometry", 12, 700, "#9a3412"),
            '<line x1="395" y1="282" x2="465" y2="282" stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>',
            '<rect x="505" y="205" width="270" height="220" rx="8" fill="#ffffff" stroke="#94a3b8" stroke-width="1.4"/>',
            svg_text(525, 232, "identity key", 13, 700, "#334155"),
            svg_text(525, 258, "scan, subgraph, subject, object", 12, 400, "#475569"),
            svg_text(525, 284, "predicate: close by     sem=.88", 12, 400, "#475569"),
            '<line x1="525" y1="302" x2="755" y2="302" stroke="#cbd5e1" stroke-width="1"/>',
            svg_text(525, 330, "joined 3D evidence", 13, 700, "#334155"),
            svg_text(525, 356, "xy distance: far", 12, 400, "#b91c1c"),
            svg_text(525, 380, "vertical/order: unrelated", 12, 400, "#475569"),
            svg_text(525, 404, "verifier: violated  ->  p_geom=.06", 12, 700, "#b91c1c"),
            '<line x1="815" y1="282" x2="885" y2="282" stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>',
            '<rect x="990" y="255" width="86" height="48" rx="5" fill="#bfdbfe" stroke="#2563eb" stroke-width="1.5"/>',
            '<rect x="1012" y="220" width="42" height="34" rx="4" fill="#fde68a" stroke="#b45309" stroke-width="1.5"/>',
            '<rect x="1118" y="315" width="40" height="50" rx="4" fill="#fecaca" stroke="#dc2626" stroke-width="1.5"/>',
            '<rect x="932" y="315" width="45" height="35" rx="4" fill="#bbf7d0" stroke="#059669" stroke-width="1.5"/>',
            '<path d="M1033 220 C1033 207 1033 200 1033 191" stroke="#059669" stroke-width="3" fill="none" marker-end="url(#arrow)"/>',
            svg_text(1068, 207, "kept", 12, 700, "#047857"),
            '<path d="M978 330 C1034 300 1090 302 1118 330" stroke="#dc2626" stroke-width="2" fill="none" stroke-dasharray="5 4" marker-end="url(#arrow)"/>',
            svg_text(1036, 307, "demoted", 12, 700, "#b91c1c"),
            '<rect x="925" y="382" width="270" height="44" rx="6" fill="#ecfdf5" stroke="#34d399"/>',
            svg_text(950, 409, "report R@K with Violation@K", 13, 700, "#047857"),
        ]
    )

    y = 500
    parts.extend(
        [
            '<rect x="50" y="492" width="1180" height="128" rx="8" fill="#ffffff" stroke="#cbd5e1" stroke-width="1.3"/>',
            svg_text(70, y + 26, "Operating points and controls", 16, 700),
            svg_text(70, y + 57, "probabilistic: score_sem x p_geom_valid", 12, 700, "#1d4ed8"),
            svg_text(350, y + 57, "rule-verified: remove hard violations", 12, 700, "#b91c1c"),
            svg_text(640, y + 57, "family-specific: stricter calibrated validity", 12, 700, "#047857"),
            svg_text(70, y + 84, "controls: geometry-only, distance-only, shuffled, wrong-pair", 12, 700, "#334155"),
            svg_text(70, y + 112, "Claim boundary: a relation-reliability layer for geometry-checkable families, not a new open-vocabulary generator.", 12, 400, "#64748b"),
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


def write_figure1_png() -> None:
    width, height = 1280, 650
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    subtitle_font = ImageFont.truetype("DejaVuSans.ttf", 14)
    font = ImageFont.truetype("DejaVuSans.ttf", 12)
    font_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)
    panel_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 16)
    small_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 11)

    def text(x: int, y: int, value: str, fill: str = "#111827", bold: bool = False) -> None:
        draw.text((x, y), value, fill=fill, font=font_bold if bold else font)

    def wrapped(x: int, y: int, value: str, width_chars: int, fill: str = "#475569") -> None:
        for idx, line in enumerate(wrapped_lines(value, width_chars)):
            draw.text((x, y + idx * 16), line, fill=fill, font=font)

    def arrow(x1: int, y1: int, x2: int, y2: int, fill: str = "#374151", width_px: int = 2) -> None:
        draw.line((x1, y1, x2, y2), fill=fill, width=width_px)
        if x2 >= x1:
            head = [(x2, y2), (x2 - 12, y2 - 6), (x2 - 12, y2 + 6)]
        else:
            head = [(x2, y2), (x2 + 12, y2 - 6), (x2 + 12, y2 + 6)]
        draw.polygon(head, fill=fill)

    def curve(points: list[tuple[int, int]], fill: str, width_px: int = 2, dash: bool = False) -> None:
        if dash:
            for idx in range(len(points) - 1):
                if idx % 2 == 0:
                    draw.line((points[idx], points[idx + 1]), fill=fill, width=width_px)
        else:
            draw.line(points, fill=fill, width=width_px, joint="curve")
        x2, y2 = points[-1]
        draw.polygon([(x2, y2), (x2 - 10, y2 - 6), (x2 - 5, y2 + 8)], fill=fill)

    draw.text((50, 30), "Figure 1. GeoCalib: calibrated geometry-consistency re-ranking", fill="#111827", font=title_font)
    draw.text((50, 63), "Relation-source graph edges become identity-preserved evidence records before recall-violation evaluation.", fill="#4b5563", font=subtitle_font)

    panels = [
        (50, 110, 340, 345, "A. Relation-source graph", "High semantic scores can rank plausible but physically inconsistent edges."),
        (470, 110, 340, 345, "B. Evidence-rich edge record", "The same subject-object edge is joined to explicit 3D evidence and calibrated validity."),
        (890, 110, 340, 345, "C. Reliable relation graph", "Re-ranking demotes violated edges and reports recall with geometric violation."),
    ]
    for x, y, w, h, title, subtitle in panels:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=8, fill="#f8fafc", outline="#cbd5e1", width=2)
        draw.text((x + 20, y + 18), title, fill="#111827", font=panel_font)
        wrapped(x + 20, y + 46, subtitle, 42)

    draw.polygon([(90, 375), (350, 375), (325, 245), (115, 245)], fill="#eef2ff", outline="#c7d2fe")
    for line in [((115, 245), (90, 375)), ((185, 245), (175, 375)), ((255, 245), (260, 375)), ((325, 245), (350, 375))]:
        draw.line(line, fill="#d1d5db", width=1)
    draw.rounded_rectangle((150, 270, 236, 318), radius=5, fill="#bfdbfe", outline="#2563eb", width=2)
    draw.rounded_rectangle((170, 237, 212, 271), radius=4, fill="#fde68a", outline="#b45309", width=2)
    draw.rounded_rectangle((275, 310, 315, 360), radius=4, fill="#fecaca", outline="#dc2626", width=2)
    draw.rounded_rectangle((95, 325, 140, 360), radius=4, fill="#bbf7d0", outline="#059669", width=2)
    draw.text((181, 321), "desk", fill="#1d4ed8", font=small_bold)
    draw.text((179, 218), "lamp", fill="#92400e", font=small_bold)
    draw.text((287, 292), "bin", fill="#991b1b", font=small_bold)
    draw.text((100, 306), "heater", fill="#047857", font=small_bold)
    curve([(190, 237), (190, 212), (195, 196)], "#059669", 3)
    text(225, 202, "on 0.94", "#047857", True)
    curve([(138, 335), (190, 302), (245, 296), (275, 324)], "#dc2626", 3, dash=True)
    text(178, 278, "close by 0.88", "#b91c1c", True)
    draw.rounded_rectangle((68, 392, 374, 432), radius=6, fill="#fff7ed", outline="#fb923c", width=1)
    text(86, 405, "Failure: plausible edge violates geometry", "#9a3412", True)

    arrow(395, 282, 465, 282)

    draw.rounded_rectangle((505, 205, 775, 425), radius=8, fill="white", outline="#94a3b8", width=2)
    text(525, 221, "identity key", "#334155", True)
    text(525, 247, "scan, subgraph, subject, object", "#475569")
    text(525, 273, "predicate: close by     sem=.88", "#475569")
    draw.line((525, 302, 755, 302), fill="#cbd5e1", width=1)
    text(525, 316, "joined 3D evidence", "#334155", True)
    text(525, 342, "xy distance: far", "#b91c1c")
    text(525, 366, "vertical/order: unrelated", "#475569")
    text(525, 390, "verifier: violated  ->  p_geom=.06", "#b91c1c", True)

    arrow(815, 282, 885, 282)

    draw.rounded_rectangle((990, 255, 1076, 303), radius=5, fill="#bfdbfe", outline="#2563eb", width=2)
    draw.rounded_rectangle((1012, 220, 1054, 254), radius=4, fill="#fde68a", outline="#b45309", width=2)
    draw.rounded_rectangle((1118, 315, 1158, 365), radius=4, fill="#fecaca", outline="#dc2626", width=2)
    draw.rounded_rectangle((932, 315, 977, 350), radius=4, fill="#bbf7d0", outline="#059669", width=2)
    curve([(1033, 220), (1033, 207), (1033, 191)], "#059669", 3)
    text(1068, 193, "kept", "#047857", True)
    curve([(978, 330), (1034, 300), (1090, 302), (1118, 330)], "#dc2626", 2, dash=True)
    text(1036, 293, "demoted", "#b91c1c", True)
    draw.rounded_rectangle((925, 382, 1195, 426), radius=6, fill="#ecfdf5", outline="#34d399", width=1)
    draw.text((950, 396), "report R@K with Violation@K", fill="#047857", font=font_bold)

    draw.rounded_rectangle((50, 492, 1230, 620), radius=8, fill="white", outline="#cbd5e1", width=1)
    draw.text((70, 514), "Operating points and controls", fill="#111827", font=panel_font)
    text(70, 545, "probabilistic: score_sem x p_geom_valid", "#1d4ed8", True)
    text(350, 545, "rule-verified: remove hard violations", "#b91c1c", True)
    text(640, 545, "family-specific: stricter calibrated validity", "#047857", True)
    text(70, 572, "controls: geometry-only, distance-only, shuffled, wrong-pair", "#334155", True)
    text(70, 599, "Claim boundary: a relation-reliability layer for geometry-checkable families, not a new open-vocabulary generator.", "#64748b")
    image.save(OUT_DIR / "figure1_framework.png")


def metric_row(metrics: dict[str, Any], key: str, label: str, source: str) -> dict[str, float | str]:
    row = metrics["conditions"][key]
    return {
        "source": source,
        "condition": label,
        "r100": row["recall"]["by_k"]["100"]["recall"],
        "violation100": row["violation_rate"]["by_k"]["100"]["violation_rate"],
    }


def load_figure2_data() -> dict[str, list[dict[str, float | str]]]:
    keep = [
        ("semantic_only", "semantic_only"),
        ("probabilistic_recalibrated", "probabilistic_recalibrated"),
        ("family_specific_p_geom_valid", "control_family_specific_p_geom_valid"),
        ("rule_verified_point_subtype", "rule_verified_point_subtype"),
    ]
    vlsat_metrics = json.loads(VLSAT_FULL_METRICS.read_text())
    open3dsg_metrics = json.loads(OPEN3DSG_METRICS.read_text())
    vlsat = [metric_row(vlsat_metrics, key, label, "VL-SAT") for label, key in keep]
    open3dsg = [metric_row(open3dsg_metrics, key, label, "Open3DSG") for label, key in keep]
    return {"VL-SAT": vlsat, "Open3DSG": open3dsg}


def generate_figure2(data: dict[str, list[dict[str, float | str]]]) -> str:
    width, height = 1280, 620
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="620" viewBox="0 0 1280 620">',
        '<rect width="1280" height="620" fill="#ffffff"/>',
        arrow_marker(),
        svg_text(55, 45, "Figure 2. Recall-violation tradeoff", 22, 700),
        svg_text(55, 72, "Draft plot from locked R@100 and Violation@100 values. Lower violation and higher recall are better.", 14, 400, "#4b5563"),
    ]

    panels = [
        ("A. VL-SAT primary source", "VL-SAT", 70, 115, 520, 360, (0.0, 0.05), (0.960, 0.971)),
        ("B. Open3DSG open-vocabulary source", "Open3DSG", 690, 115, 520, 360, (0.0, 0.13), (0.50, 0.62)),
    ]

    def map_point(x: float, y: float, px: int, py: int, pw: int, ph: int, xr: tuple[float, float], yr: tuple[float, float]) -> tuple[float, float]:
        sx = px + (x - xr[0]) / (xr[1] - xr[0]) * pw
        sy = py + ph - (y - yr[0]) / (yr[1] - yr[0]) * ph
        return sx, sy

    for title, source, px, py, pw, ph, xr, yr in panels:
        parts.append(f'<rect x="{px-15}" y="{py-45}" width="{pw+40}" height="{ph+105}" rx="8" fill="#f8fafc" stroke="#e5e7eb"/>')
        parts.append(svg_text(px, py - 20, title, 17, 700))
        for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
            gx = px + frac * pw
            gy = py + frac * ph
            parts.append(f'<line x1="{gx:.1f}" y1="{py}" x2="{gx:.1f}" y2="{py+ph}" stroke="{COLORS["grid"]}" stroke-width="0.8"/>')
            parts.append(f'<line x1="{px}" y1="{gy:.1f}" x2="{px+pw}" y2="{gy:.1f}" stroke="{COLORS["grid"]}" stroke-width="0.8"/>')
        parts.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="none" stroke="{COLORS["axis"]}" stroke-width="1.2"/>')
        parts.append(svg_text(px + pw / 2, py + ph + 44, "Violation@100", 14, 700, anchor="middle"))
        parts.append(svg_text(px - 45, py + ph / 2, "R@100", 14, 700, anchor="middle"))
        parts.append(svg_text(px, py + ph + 20, f"{xr[0]:.2f}", 11, 400, "#6b7280", "middle"))
        parts.append(svg_text(px + pw, py + ph + 20, f"{xr[1]:.2f}", 11, 400, "#6b7280", "middle"))
        parts.append(svg_text(px - 12, py + ph, f"{yr[0]:.3f}", 11, 400, "#6b7280", "end"))
        parts.append(svg_text(px - 12, py, f"{yr[1]:.3f}", 11, 400, "#6b7280", "end"))

        points: dict[str, tuple[float, float]] = {}
        for row in data[source]:
            points[row["condition"]] = map_point(
                float(row["violation100"]), float(row["r100"]), px, py, pw, ph, xr, yr
            )
        semantic = points["semantic_only"]
        for condition in ["probabilistic_recalibrated", "family_specific_p_geom_valid", "rule_verified_point_subtype"]:
            x2, y2 = points[condition]
            parts.append(
                f'<line x1="{semantic[0]:.1f}" y1="{semantic[1]:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                'stroke="#64748b" stroke-width="1.6" stroke-dasharray="4 3" marker-end="url(#arrow)"/>'
            )
        for row in data[source]:
            condition = str(row["condition"])
            x, y = points[condition]
            color = COLORS[condition]
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{color}" stroke="#ffffff" stroke-width="2"/>')
            label = LABELS[condition]
            dx = 10 if condition != "rule_verified_point_subtype" else -8
            anchor = "start" if dx > 0 else "end"
            parts.append(svg_text(x + dx, y - 8, label, 12, 700, color, anchor))

    legend_x, legend_y = 70, 540
    parts.append(svg_text(legend_x, legend_y, "Operating points:", 13, 700))
    for idx, condition in enumerate(["semantic_only", "probabilistic_recalibrated", "family_specific_p_geom_valid", "rule_verified_point_subtype"]):
        x = legend_x + 132 + idx * 190
        parts.append(f'<circle cx="{x}" cy="{legend_y-4}" r="6" fill="{COLORS[condition]}"/>')
        parts.append(svg_text(x + 12, legend_y, LABELS[condition], 12, 400))
    parts.append(svg_text(70, 585, "Open3DSG panel uses the full-validation 548/548 recovery branch; 533/548 covered branch is sensitivity evidence.", 12, 400, "#6b7280"))
    parts.append("</svg>")
    return "\n".join(parts)


def write_figure2_png(data: dict[str, list[dict[str, float | str]]]) -> None:
    width, height = 1280, 620
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("DejaVuSans.ttf", 22)
    font_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 22)
    small = ImageFont.truetype("DejaVuSans.ttf", 14)
    small_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    tiny = ImageFont.truetype("DejaVuSans.ttf", 11)

    def text(x: int, y: int, value: str, fill: str = "#111827", bold: bool = False) -> None:
        draw.text((x, y), value, fill=fill, font=font_bold if bold else small)

    def map_point(x: float, y: float, px: int, py: int, pw: int, ph: int, xr: tuple[float, float], yr: tuple[float, float]) -> tuple[float, float]:
        sx = px + (x - xr[0]) / (xr[1] - xr[0]) * pw
        sy = py + ph - (y - yr[0]) / (yr[1] - yr[0]) * ph
        return sx, sy

    draw.text((55, 35), "Figure 2. Recall-violation tradeoff", fill="#111827", font=font_bold)
    draw.text((55, 67), "Draft plot from full-validation R@100 and Violation@100 values. Lower violation and higher recall are better.", fill="#4b5563", font=small)
    panels = [
        ("A. VL-SAT primary source", "VL-SAT", 70, 115, 520, 360, (0.0, 0.05), (0.960, 0.971)),
        ("B. Open3DSG open-vocabulary source", "Open3DSG", 690, 115, 520, 360, (0.0, 0.13), (0.50, 0.62)),
    ]
    for title, source, px, py, pw, ph, xr, yr in panels:
        draw.rounded_rectangle((px - 15, py - 45, px + pw + 25, py + ph + 60), radius=8, fill="#f8fafc", outline="#e5e7eb")
        text(px, py - 32, title, bold=True)
        for frac in [0.0, 0.25, 0.5, 0.75, 1.0]:
            gx = px + frac * pw
            gy = py + frac * ph
            draw.line((gx, py, gx, py + ph), fill="#d1d5db", width=1)
            draw.line((px, gy, px + pw, gy), fill="#d1d5db", width=1)
        draw.rectangle((px, py, px + pw, py + ph), outline="#111827", width=2)
        draw.text((px + pw // 2 - 45, py + ph + 34), "Violation@100", fill="#111827", font=small_bold)
        draw.text((px - 52, py + ph // 2), "R@100", fill="#111827", font=small_bold)
        draw.text((px - 5, py + ph + 8), f"{xr[0]:.2f}", fill="#6b7280", font=tiny)
        draw.text((px + pw - 18, py + ph + 8), f"{xr[1]:.2f}", fill="#6b7280", font=tiny)
        draw.text((px - 46, py + ph - 8), f"{yr[0]:.3f}", fill="#6b7280", font=tiny)
        draw.text((px - 46, py - 8), f"{yr[1]:.3f}", fill="#6b7280", font=tiny)

        points = {
            str(row["condition"]): map_point(float(row["violation100"]), float(row["r100"]), px, py, pw, ph, xr, yr)
            for row in data[source]
        }
        semantic = points["semantic_only"]
        for condition in ["probabilistic_recalibrated", "family_specific_p_geom_valid", "rule_verified_point_subtype"]:
            x2, y2 = points[condition]
            draw.line((semantic[0], semantic[1], x2, y2), fill="#64748b", width=2)
        for row in data[source]:
            condition = str(row["condition"])
            x, y = points[condition]
            color = COLORS[condition]
            draw.ellipse((x - 8, y - 8, x + 8, y + 8), fill=color, outline="white", width=2)
            dx = 11 if condition != "rule_verified_point_subtype" else -42
            draw.text((x + dx, y - 18), LABELS[condition], fill=color, font=small_bold)

    text(70, 530, "Operating points:", bold=True)
    for idx, condition in enumerate(["semantic_only", "probabilistic_recalibrated", "family_specific_p_geom_valid", "rule_verified_point_subtype"]):
        x = 205 + idx * 190
        y = 532
        draw.ellipse((x - 6, y - 6, x + 6, y + 6), fill=COLORS[condition])
        draw.text((x + 12, y - 9), LABELS[condition], fill="#111827", font=small)
    draw.text((70, 575), "Open3DSG panel uses the full-validation 548/548 recovery branch; 533/548 covered branch is sensitivity evidence.", fill="#6b7280", font=small)
    image.save(OUT_DIR / "figure2_tradeoff.png")


def load_figure3_cases() -> list[dict[str, object]]:
    inspection = json.loads(INSPECTION_JSON.read_text())
    family_cases = {case["case_id"]: case for case in inspection["representative_cases"]["family_mechanism_examples"]}
    residual_cases = {case["case_id"]: case for case in inspection["representative_cases"]["residual_calibration_risk"]}
    cases = []
    for case_id in EXPECTED_FIGURE3_CASES:
        cases.append(family_cases.get(case_id) or residual_cases[case_id])
    return cases


def validate_outputs(figure2_data: dict[str, list[dict[str, float | str]]], figure3_cases: list[dict[str, object]]) -> dict[str, object]:
    errors: list[str] = []
    tolerance = 5e-4

    for source, expected_rows in EXPECTED_FIGURE2.items():
        actual_by_condition = {str(row["condition"]): row for row in figure2_data[source]}
        for condition, expected in expected_rows.items():
            actual = actual_by_condition.get(condition)
            if actual is None:
                errors.append(f"missing Figure 2 row: {source} {condition}")
                continue
            for metric in ("r100", "violation100"):
                diff = abs(float(actual[metric]) - expected[metric])
                if diff > tolerance:
                    errors.append(
                        f"Figure 2 mismatch: {source} {condition} {metric} "
                        f"actual={float(actual[metric]):.6f} expected={expected[metric]:.6f}"
                    )

    actual_cases = [str(case["case_id"]) for case in figure3_cases]
    if actual_cases != EXPECTED_FIGURE3_CASES:
        errors.append(f"Figure 3 case order mismatch: actual={actual_cases} expected={EXPECTED_FIGURE3_CASES}")

    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "checks": {
            "figure2_locked_values": "passed" if not [e for e in errors if e.startswith("Figure 2")] else "failed",
            "figure3_case_ids": "passed" if actual_cases == EXPECTED_FIGURE3_CASES else "failed",
            "svg_xml_parse": "checked_by_external_command",
        },
        "tolerance": tolerance,
    }


def generate_figure3(cases: list[dict[str, object]]) -> str:
    width, height = 1280, 660
    roles = {
        "open3dsg_case_001": ("A", "Proximity demotion", "#eff6ff"),
        "open3dsg_case_005": ("B", "Vertical demotion", "#fef3c7"),
        "open3dsg_case_010": ("C", "Support/contact demotion", "#ecfdf5"),
        "open3dsg_case_007": ("D", "Residual calibration risk", "#fff1f2"),
    }
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="660" viewBox="0 0 1280 660">',
        '<rect width="1280" height="660" fill="#ffffff"/>',
        svg_text(55, 45, "Figure 3. Family-structured failure cases and residual calibration risk", 22, 700),
        svg_text(55, 72, "Draft row-card panels from traceable Open3DSG qualitative inspection rows; not a representative human audit.", 14, 400, "#4b5563"),
    ]
    positions = [(60, 120), (660, 120), (60, 365), (660, 365)]
    for case, (x, y) in zip(cases, positions):
        panel, role, fill = roles[str(case["case_id"])]
        parts.append(f'<rect x="{x}" y="{y}" width="540" height="205" rx="8" fill="{fill}" stroke="#94a3b8" stroke-width="1.2"/>')
        parts.append(svg_text(x + 20, y + 30, f"{panel}. {role}", 17, 700))
        parts.append(svg_text(x + 20, y + 58, str(case["case_id"]), 12, 700, "#4b5563"))
        parts.append(svg_text(x + 20, y + 86, f"Family: {case['family']}    Predicate: {case['predicate']}", 13, 700))
        parts.append(svg_wrapped_text(x + 20, y + 113, f"Pair: {case['pair']}", 50, size=13))
        parts.append(svg_text(x + 20, y + 153, f"Semantic -> geometry rank: {case['semantic_rank']} -> {case['geometry_rank']}", 13, 400))
        parts.append(svg_text(x + 310, y + 153, f"p_geom_valid: {float(case['p_geom_valid']):.4f}", 13, 400))
        reason = ", ".join(case["reason_codes"])
        parts.append(svg_wrapped_text(x + 20, y + 178, f"Reason: {reason}", 64, size=12, fill="#374151"))
    parts.append(svg_text(60, 620, "Caption guard: qualitative reviewer-defense evidence only; 10/36 sampled rule-violated cases have p_geom_valid > 0.9.", 12, 400, "#6b7280"))
    parts.append("</svg>")
    return "\n".join(parts)


def write_outputs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    figure2_data = load_figure2_data()
    figure3_cases = load_figure3_cases()

    outputs = {
        "figure1_framework.svg": generate_figure1(),
        "figure2_tradeoff.svg": generate_figure2(figure2_data),
        "figure3_failure_cases.svg": generate_figure3(figure3_cases),
    }
    for filename, content in outputs.items():
        (OUT_DIR / filename).write_text(content + "\n")
    write_figure1_png()
    write_figure2_png(figure2_data)

    (OUT_DIR / "figure2_data.json").write_text(json.dumps(figure2_data, indent=2, sort_keys=True) + "\n")
    (OUT_DIR / "figure3_cases.json").write_text(json.dumps(figure3_cases, indent=2, sort_keys=True) + "\n")
    validation = validate_outputs(figure2_data, figure3_cases)
    (OUT_DIR / "validation.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n")

    manifest = {
        "status": "draft_figures_generated_verified" if validation["status"] == "passed" else "draft_figures_generated_validation_failed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "outputs": {key: str((OUT_DIR / key).relative_to(ROOT)) for key in outputs},
        "png_outputs": {
            "figure1_framework.png": str((OUT_DIR / "figure1_framework.png").relative_to(ROOT)),
            "figure2_tradeoff.png": str((OUT_DIR / "figure2_tradeoff.png").relative_to(ROOT)),
        },
        "source_lock": "paper/figures.md",
        "source_artifacts": [
            str(VLSAT_FULL_METRICS.relative_to(ROOT)),
            str(OPEN3DSG_METRICS.relative_to(ROOT)),
            str(INSPECTION_JSON.relative_to(ROOT)),
        ],
        "validation": str((OUT_DIR / "validation.json").relative_to(ROOT)),
        "layout_review": str(LAYOUT_REVIEW.relative_to(ROOT)),
        "claim_boundary": "draft figures only; scoped GeoCalib relation-reliability claim",
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    geometry_note = ""
    if (OUT_DIR / "figure3_geometry_panels.svg").exists():
        geometry_note = """
- `figure3_geometry_panels.svg`: preferred geometry-backed Open3DSG failure panels, generated by `render_figure3_geometry_panels.py`.
- `figure3_geometry_panels.png`: LaTeX-facing conversion for the preferred Figure 3, if present.
- `figure3_geometry_manifest.json`: generation manifest for geometry-backed Figure 3, if present.
"""

    report = f"""# Draft Figure Generation

Status: `{manifest["status"]}`

Generated outputs:

- `figure1_framework.svg`: method/framework schematic.
- `figure1_framework.png`: LaTeX-facing PNG conversion of the Figure 1 framework.
- `figure2_tradeoff.svg`: two-panel R@100 / Violation@100 tradeoff.
- `figure2_tradeoff.png`: LaTeX-facing PNG conversion of the Figure 2 tradeoff.
- `figure3_failure_cases.svg`: Open3DSG qualitative row-card panels.
{geometry_note.rstrip()}
- `figure2_data.json`: extracted numeric values used for Figure 2.
- `figure3_cases.json`: extracted case rows used for Figure 3.
- `validation.json`: source-lock value and case-ID validation.
- `layout_review.md`: top-tier novelty/layout review, written after generation.

Validation rules:

- Verify Figure 2 values against `paper/figures.md`, VL-SAT full-validation
  `metrics.json`, and Open3DSG full-validation recovery `metrics.json`.
- Verify Figure 3 case IDs against `paper/figures.md` and Open3DSG `inspection.json`.
- Treat all SVGs as draft manuscript figures, not camera-ready final artwork.
"""
    (OUT_DIR / "report.md").write_text(report)


if __name__ == "__main__":
    write_outputs()
