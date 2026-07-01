#!/usr/bin/env python3
"""Generate draft H001 paper figures from locked source artifacts.

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
    "family_conditional_risk": "#059669",
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
        "family_conditional_risk": {"r100": 0.9683, "violation100": 0.0333},
        "rule_verified_point_subtype": {"r100": 0.9627, "violation100": 0.0},
    },
    "Open3DSG": {
        "semantic_only": {"r100": 0.5161, "violation100": 0.1242},
        "probabilistic_recalibrated": {"r100": 0.5723, "violation100": 0.0811},
        "family_conditional_risk": {"r100": 0.6047, "violation100": 0.0341},
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
    "probabilistic_recalibrated": "pooled",
    "family_conditional_risk": "GeoCalib",
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
    boxes = [
        (50, 220, 160, 115, "Relation source", "VL-SAT / Open3DSG scored predicate rows"),
        (250, 220, 170, 115, "Row contract", "scan, subgraph, subject, object, predicate, score"),
        (460, 220, 170, 115, "Geometry join", "identity-preserving object-pair evidence"),
        (670, 220, 170, 115, "Verifier", "family-specific satisfied / uncertain / violated"),
        (880, 220, 170, 115, "Calibration", "estimate p_geom_valid from frozen geometry features"),
        (1090, 220, 150, 115, "Evaluation", "R@K and Violation@K reported together"),
    ]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="650" viewBox="0 0 1280 650">',
        '<rect width="1280" height="650" fill="#ffffff"/>',
        arrow_marker(),
        svg_text(50, 50, "Figure 1. Calibrated geometry-consistency evaluation and re-ranking framework", 22, 700),
        svg_text(50, 78, "Top-tier claim: a concrete failure mechanism motivates the framework form.", 14, 400, "#4b5563"),
    ]
    parts.extend(
        [
            f'<rect x="50" y="105" width="360" height="80" rx="8" fill="#fff7ed" stroke="#fb923c" stroke-width="1.4"/>',
            svg_text(70, 132, "Failure mechanism", 16, 700, "#9a3412"),
            svg_wrapped_text(70, 158, "Semantic scores can rank plausible relations that conflict with object-pair geometry.", 48, 16, 12, "#7c2d12"),
            f'<rect x="470" y="105" width="330" height="80" rx="8" fill="#fef2f2" stroke="#f87171" stroke-width="1.4"/>',
            svg_text(490, 132, "Cause", 16, 700, "#991b1b"),
            svg_wrapped_text(490, 158, "Semantic confidence is not calibrated to relation-level physical consistency.", 44, 16, 12, "#7f1d1d"),
            f'<rect x="860" y="105" width="360" height="80" rx="8" fill="#eff6ff" stroke="#60a5fa" stroke-width="1.4"/>',
            svg_text(880, 132, "Design necessity", 16, 700, "#1d4ed8"),
            svg_wrapped_text(880, 158, "Preserve identity, join geometry, calibrate validity, then report recall and violations together.", 48, 16, 12, "#1e3a8a"),
            '<line x1="410" y1="145" x2="470" y2="145" stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>',
            '<line x1="800" y1="145" x2="860" y2="145" stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>',
            svg_text(50, 207, "Framework instantiated by this failure-to-design link", 14, 700, "#374151"),
        ]
    )
    for item in boxes:
        parts.append(box(*item))
    for idx in range(len(boxes) - 1):
        x1 = boxes[idx][0] + boxes[idx][2] + 8
        y1 = boxes[idx][1] + boxes[idx][3] / 2
        x2 = boxes[idx + 1][0] - 8
        y2 = boxes[idx + 1][1] + boxes[idx + 1][3] / 2
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            'stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>'
        )

    y = 405
    parts.extend(
        [
            svg_text(55, y, "Operating points", 17, 700),
            box(55, y + 22, 245, 90, "Pooled risk", "score_sem * pooled p_geom_valid; ablation", "#eff6ff"),
            box(330, y + 22, 245, 90, "Rule-verified", "remove hard violations; zero-violation diagnostic", "#fff1f2"),
            box(605, y + 22, 245, 90, "GeoCalib", "score_sem * family-conditioned p_geom_valid", "#ecfdf5"),
            box(880, y + 22, 310, 90, "Controls", "geometry-only, distance-only, shuffled geometry, wrong-pair geometry", "#f8fafc"),
            svg_text(
                55,
                588,
                "Caption guard: describe this as a framework, not a verifier script or broad open-vocabulary generation method.",
                13,
                400,
                "#6b7280",
            ),
        ]
    )
    parts.append("</svg>")
    return "\n".join(parts)


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
        ("family_conditional_risk", "control_family_specific_p_geom_valid"),
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
        for condition in ["probabilistic_recalibrated", "family_conditional_risk", "rule_verified_point_subtype"]:
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
    for idx, condition in enumerate(["semantic_only", "probabilistic_recalibrated", "family_conditional_risk", "rule_verified_point_subtype"]):
        x = legend_x + 132 + idx * 190
        parts.append(f'<circle cx="{x}" cy="{legend_y-4}" r="6" fill="{COLORS[condition]}"/>')
        parts.append(svg_text(x + 12, legend_y, LABELS[condition], 12, 400))
    parts.append(svg_text(70, 585, "Open3DSG panel uses the full-validation 548/548 recovery branch; 533/548 covered branch is sensitivity evidence.", 12, 400, "#6b7280"))
    parts.append("</svg>")
    return "\n".join(parts)


def write_figure1_png() -> None:
    width, height = 1280, 650
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype("DejaVuSans-Bold.ttf", 25)
    head = ImageFont.truetype("DejaVuSans-Bold.ttf", 17)
    body = ImageFont.truetype("DejaVuSans.ttf", 14)
    body_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
    small = ImageFont.truetype("DejaVuSans.ttf", 12)
    small_bold = ImageFont.truetype("DejaVuSans-Bold.ttf", 12)

    def text(x: int, y: int, value: str, fill: str = "#111827", font: ImageFont.FreeTypeFont = body) -> None:
        draw.text((x, y), value, fill=fill, font=font)

    def wrap_text(
        x: int,
        y: int,
        value: str,
        width_chars: int,
        fill: str = "#374151",
        font: ImageFont.FreeTypeFont = body,
        line_h: int = 18,
    ) -> None:
        for idx, line in enumerate(wrapped_lines(value, width_chars)):
            draw.text((x, y + idx * line_h), line, fill=fill, font=font)

    def panel(x: int, y: int, w: int, h: int, label: str, fill: str, stroke: str = "#94a3b8") -> None:
        draw.rounded_rectangle((x, y, x + w, y + h), radius=10, fill=fill, outline=stroke, width=2)
        text(x + 16, y + 13, label, font=head)

    def arrow(x1: int, y1: int, x2: int, y2: int, color: str = "#374151") -> None:
        draw.line((x1, y1, x2, y2), fill=color, width=3)
        draw.polygon([(x2, y2), (x2 - 12, y2 - 7), (x2 - 12, y2 + 7)], fill=color)

    text(50, 30, "GeoCalib: calibrating geometric consistency for relation rows", font=title)
    text(
        50,
        64,
        "A semantically plausible edge is not necessarily reliable for the same 3D object pair.",
        "#4b5563",
        body,
    )

    panel(50, 105, 330, 168, "1. Failure example", "#fff7ed", "#fb923c")
    draw.ellipse((82, 176, 162, 236), fill="#fef3c7", outline="#d97706", width=2)
    draw.ellipse((246, 176, 326, 236), fill="#fee2e2", outline="#dc2626", width=2)
    text(105, 198, "chair", "#92400e", small_bold)
    text(270, 198, "wall", "#991b1b", small_bold)
    arrow(164, 206, 244, 206, "#b45309")
    text(178, 181, "standing on", "#92400e", small_bold)
    text(72, 238, "semantic score: high", "#7c2d12", small)
    text(72, 256, "geometry: violated", "#991b1b", small_bold)
    text(205, 238, "plausible label", "#7c2d12", small)
    text(205, 256, "wrong physical state", "#991b1b", small_bold)

    panel(430, 105, 360, 168, "2. Same-pair geometry", "#eff6ff", "#60a5fa")
    wrap_text(
        452,
        154,
        "Join evidence by scan, subgraph, subject id, and object id rather than by category names.",
        43,
        "#1e3a8a",
    )
    text(452, 226, "Evidence: distance, contact, overlap, vertical order", "#1e3a8a", body)

    panel(850, 105, 380, 168, "3. Calibrated re-ranking", "#ecfdf5", "#34d399")
    text(872, 153, "GeoCalib score", "#065f46", body_bold)
    text(872, 179, "semantic_score x p_geom_valid_family", "#065f46", body)
    wrap_text(872, 213, "Family-conditioned risk keeps top-K utility while penalizing inconsistency.", 43, "#065f46")

    arrow(390, 190, 420, 190)
    arrow(800, 190, 840, 190)

    text(50, 318, "What changes in the top-K list?", font=head)
    panel(50, 348, 360, 135, "Semantic-only", "#f8fafc")
    text(76, 394, "rank 1  chair -- standing on -- wall", font=small_bold)
    text(76, 418, "high semantic confidence, violated geometry", "#991b1b", small)
    text(76, 446, "failure: symbolic edge contradicts 3D evidence", "#6b7280", small)

    panel(460, 348, 360, 135, "GeoCalib", "#f0fdf4", "#22c55e")
    text(486, 394, "same semantic score + same-pair geometry", "#065f46", small_bold)
    text(486, 418, "invalid edges are softly demoted", "#065f46", small)
    text(486, 446, "evaluate recall and violation together", "#6b7280", small)

    panel(870, 348, 360, 135, "Controls", "#f8fafc")
    text(896, 394, "geometry-only / distance-only", font=small_bold)
    text(896, 418, "shuffled geometry / wrong-pair geometry", font=small_bold)
    text(896, 446, "test whether same-pair calibration matters", "#6b7280", small)

    text(50, 545, "Paper-facing names:", font=body_bold)
    text(
        228,
        545,
        "GeoCalib = main score; pooled risk = ablation; strict rule = diagnostic; controls = simpler explanations.",
        "#374151",
        body,
    )
    text(
        50,
        585,
        "Caption guard: scoped relation-reliability framework, not a broad open-vocabulary generation method.",
        "#6b7280",
        small,
    )
    image.save(OUT_DIR / "figure1_framework.png")


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
        for condition in ["probabilistic_recalibrated", "family_conditional_risk", "rule_verified_point_subtype"]:
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
    for idx, condition in enumerate(["semantic_only", "probabilistic_recalibrated", "family_conditional_risk", "rule_verified_point_subtype"]):
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
        "claim_boundary": "draft figures only; scoped H001 relation-reliability claim",
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
