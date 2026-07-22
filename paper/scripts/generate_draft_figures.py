#!/usr/bin/env python3
"""Generate draft H001 paper figures from locked source artifacts.

The figures are draft SVGs for manuscript planning. They are intentionally
simple, traceable, and source-backed rather than camera-ready artwork.
"""

from __future__ import annotations

import html
import json
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "paper" / "generated" / "figures"

STRUCTURED_MAIN_METRICS = (
    ROOT / "experiments" / "H001_geom_reliability" / "no_family_indicator_v1" /
    "evaluation" / "structured_main" / "summary.json"
)
ROUTING_METRICS = (
    ROOT / "experiments" / "H001_geom_reliability" / "no_family_indicator_v1" /
    "evaluation" / "support_routing" / "summary.json"
)
ROUTED_COMPARATOR_METRICS = (
    ROOT / "experiments" / "H001_geom_reliability" / "no_family_indicator_v1" /
    "evaluation" / "routed_comparators" / "summary.json"
)
OPEN3DSG_OFFICIAL_METRICS = (
    ROOT / "experiments" / "H001_geom_reliability" / "no_family_indicator_v1" /
    "evaluation" / "open3dsg_route" / "summary.json"
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
COLORS = {
    "source_score": "#4b5563",
    "routed_product": "#007c76",
    "routed_matched_mlp": "#7b3fa1",
    "axis": "#111827",
    "grid": "#d1d5db",
    "muted": "#6b7280",
    "panel": "#f8fafc",
    "ink": "#111827",
}

FIGURE_FONT = "TeX Gyre Heros, Helvetica, sans-serif"

KS = (5, 10, 20, 50, 100)

EXPECTED_FIGURE2_REFERENCES = {
    "50": {
        "VL-SAT": {"source_score": (0.9272, 0.0268), "routed_product": (0.9277, 0.0197), "routed_matched_mlp": (0.9272, 0.0189)},
        "Open3DSG": {"source_score": (0.4043, 0.1387), "routed_product": (0.4418, 0.0342), "routed_matched_mlp": (0.4670, 0.0413)},
        "SGFN": {"source_score": (0.7402, 0.0385), "routed_product": (0.7450, 0.0263), "routed_matched_mlp": (0.7457, 0.0258)},
    },
    "100": {
        "VL-SAT": {"source_score": (0.9635, 0.0476), "routed_product": (0.9658, 0.0295), "routed_matched_mlp": (0.9650, 0.0296)},
        "Open3DSG": {"source_score": (0.5111, 0.1242), "routed_product": (0.5685, 0.0324), "routed_matched_mlp": (0.5989, 0.0371)},
        "SGFN": {"source_score": (0.9235, 0.0630), "routed_product": (0.9303, 0.0350), "routed_matched_mlp": (0.9288, 0.0350)},
    },
}

EXPECTED_FIGURE3_CASES = [
    "open3dsg_case_001",
    "open3dsg_case_019",
    "open3dsg_case_026",
]

LABELS = {
    "source_score": "Source",
    "routed_product": "RelCompat3D-Linear",
    "routed_matched_mlp": "RelCompat3D-MLP",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_text(x: float, y: float, text: str, size: int = 14, weight: int = 400, fill: str = "#111827",
             anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FIGURE_FONT}" '
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


def box(
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    body: str,
    fill: str = "#ffffff",
    wrap_width: int = 24,
) -> str:
    text = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{fill}" stroke="#94a3b8" stroke-width="1.4"/>',
        svg_text(x + 16, y + 26, title, size=15, weight=700),
        svg_wrapped_text(x + 16, y + 52, body, width=wrap_width, size=12, fill="#374151"),
    ]
    return "\n".join(text)


def generate_figure1() -> str:
    width, height = 1600, 610
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="610" viewBox="0 0 1600 610">',
        '<rect width="1600" height="610" fill="#ffffff"/>',
        arrow_marker(),
        svg_text(800, 34, "RelCompat3D: Relation-Consistent Geometric Re-ranking", 24, 700, anchor="middle"),
        svg_text(800, 59, "A high predictor score need not imply geometric support; compatibility uses predicate and ordered-pair measurements.", 13, 400, "#475569", "middle"),
    ]

    columns = [
        (20, 82, 360, 495, "1. High-confidence failure", "#eef4ff", "#4f78b8"),
        (405, 82, 355, 495, "2. Preserve identity & isolate factors", "#f4f7ff", "#688fc8"),
        (785, 82, 375, 495, "3. Learn & project compatibility", "#eef8eb", "#6a9d56"),
        (1185, 82, 395, 495, "4. Re-rank & evaluate jointly", "#f8f2fb", "#8d68b8"),
    ]
    for x, y, w, h, title, fill, stroke in columns:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="38" rx="10" fill="{stroke}" fill-opacity="0.13"/>')
        parts.append(svg_text(x + w / 2, y + 25, title, 15, 700, "#172554", "middle"))

    # Column 1: readable object-pair geometry rather than a nested screenshot.
    parts.extend([
        '<rect x="40" y="140" width="320" height="245" rx="8" fill="#ffffff" stroke="#94a3b8"/>',
        '<line x1="62" y1="342" x2="338" y2="342" stroke="#94a3b8" stroke-width="2"/>',
        '<rect x="78" y="218" width="62" height="124" rx="7" fill="#fca5a5" stroke="#b91c1c" stroke-width="2"/>',
        '<circle cx="294" cy="307" r="35" fill="#93c5fd" stroke="#1d4ed8" stroke-width="2"/>',
        '<line x1="145" y1="276" x2="252" y2="303" stroke="#d97706" stroke-width="2" stroke-dasharray="7 5" marker-end="url(#arrow)"/>',
        svg_text(109, 205, "subject", 12, 700, "#991b1b", "middle"),
        svg_text(294, 257, "object", 12, 700, "#1e3a8a", "middle"),
        svg_text(200, 258, "large pair distance", 12, 700, "#9a3412", "middle"),
        svg_text(200, 372, "geometry of reconstructed ordered pair", 11, 400, "#475569", "middle"),
    ])
    parts.extend([
        svg_text(45, 414, "Open3DSG: heater —close by→ trash can", 13, 700),
        svg_text(45, 440, "source rank 19   •   Z = 0.853", 12, 700, "#1d4ed8"),
        svg_text(45, 466, "measured geometry of ordered pair: far apart", 12, 400, "#9a3412"),
        svg_text(45, 500, "High predictor score ≠ geometric support", 14, 700, "#9a3412"),
    ])

    # Column 2: identity-preserving row plus T, G, Z factor separation.
    parts.extend([
        box(430, 137, 305, 85, "Ordered-pair identity", "scan • context • subject/object IDs", "#ffffff", 38),
        box(430, 241, 305, 72, "Predicate semantics  T", "predicate label and relation family", "#ffffff", 36),
        box(430, 331, 305, 102, "Ordered-pair measurements  G", "distance, overlap, extents, and vertical displacement", "#fffaf0", 38),
        box(430, 451, 305, 72, "Predictor score  Z", "used only during re-ranking", "#ffffff", 36),
        svg_text(582, 551, "Associate geometry by object identity", 12, 700, "#1e3a8a", "middle"),
    ])

    # Column 3: learned compatibility, leakage boundary, and falsification.
    parts.extend([
        f'<rect x="820" y="137" width="305" height="127" rx="9" fill="#ffffff" stroke="#86a978"/>',
        svg_text(972, 168, "Compatibility fitted on training data", 15, 700, "#315b27", "middle"),
        svg_text(972, 204, "C_tr(T,G)", 23, 700, "#315b27", "middle"),
        svg_text(972, 231, "linked margin + transformation averaging", 11, 400, "#475569", "middle"),
        svg_text(972, 251, "exact transformation consistency", 11, 700, "#315b27", "middle"),
        f'<rect x="835" y="286" width="275" height="43" rx="21" fill="#fee2e2" stroke="#ef4444"/>',
        svg_text(972, 313, "C_tr excludes the predictor score", 14, 700, "#991b1b", "middle"),
        box(815, 353, 315, 87, "Linked counterfactual objective", "positive above its wrong-T / wrong-pair negative", "#ffffff", 39),
        box(815, 461, 315, 92, "Valid transformations", "close-by: endpoint swap • vertical: swap + inverse predicate • support/contact: identity only", "#ffffff", 40),
    ])

    # Column 4: scoring, observable rank change, and joint evaluation.
    parts.extend([
        box(1215, 132, 335, 63, "Within-family product", "S = Z × C_tr(T,G)", "#ffffff", 39),
        box(1215, 207, 335, 63, "Fusion comparators", "rank-average • RRF", "#ffffff", 39),
        box(1215, 282, 335, 58, "Pooled compatibility ablation", "pooled product", "#ffffff", 39),
        f'<rect x="1215" y="352" width="335" height="66" rx="9" fill="#fff7ed" stroke="#d97706"/>',
        svg_text(1382, 377, "Observed re-ranking", 14, 700, "#9a3412", "middle"),
        svg_text(1382, 404, "rank 19  →  178", 19, 700, "#9a3412", "middle"),
        f'<rect x="1215" y="433" width="335" height="120" rx="9" fill="#ffffff" stroke="#a78bca"/>',
        svg_text(1382, 462, "Joint evaluation contract", 15, 700, "#5b3b82", "middle"),
        svg_text(1242, 494, "Exact-match Recall@K  ↑", 13, 700, "#166534"),
        svg_text(1242, 522, "Rule-based Violation@K  ↓", 13, 700, "#991b1b"),
        svg_text(1242, 546, "uncertainty • coverage • paired CI", 11, 400, "#475569"),
    ])

    for x1, x2 in [(380, 405), (760, 785), (1160, 1185)]:
        parts.append(f'<line x1="{x1}" y1="305" x2="{x2}" y2="305" stroke="#374151" stroke-width="2.2" marker-end="url(#arrow)"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def load_figure2_data() -> dict[str, dict[str, dict[str, dict[str, float]]]]:
    payload = json.loads(ROUTED_COMPARATOR_METRICS.read_text())
    result: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
    for source, label in (
        ("vlsat", "VL-SAT"),
        ("open3dsg", "Open3DSG"),
        ("sgfn", "SGFN"),
    ):
        overall = payload["sources"][source]["results"]
        result[label] = {
            condition: {
                str(k): {
                    "recall": float(overall[condition][str(k)]["recall"]["point"]),
                    "violation": float(overall[condition][str(k)]["violation_all"]["point"]),
                }
                for k in KS
            }
            for condition in ("source_score", "routed_product", "routed_matched_mlp")
        }
    return result


def generate_camera_ready_figure2(
    data: dict[str, dict[str, dict[str, dict[str, float]]]],
) -> str:
    """Render the locked trajectories with 9-pt-safe labels and line widths."""
    width, height = 1500, 520
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1500" height="520" fill="#ffffff"/>',
        f'<line x1="500" y1="28" x2="550" y2="28" stroke="{COLORS["source_score"]}" stroke-width="3.2" stroke-dasharray="9,7"/>',
        f'<circle cx="525" cy="28" r="7" fill="#ffffff" stroke="{COLORS["source_score"]}" stroke-width="2.2"/>',
        svg_text(562, 37, "Source", 28, 400),
        f'<line x1="700" y1="28" x2="750" y2="28" stroke="{COLORS["routed_product"]}" stroke-width="3.4"/>',
        f'<rect x="718" y="21" width="14" height="14" fill="{COLORS["routed_product"]}" stroke="#ffffff" stroke-width="1.8"/>',
        svg_text(762, 37, "RelCompat3D-Linear", 28, 400),
        f'<line x1="1085" y1="28" x2="1135" y2="28" stroke="{COLORS["routed_matched_mlp"]}" stroke-width="3.4"/>',
        f'<path d="M 1110 20 L 1118 35 L 1102 35 Z" fill="{COLORS["routed_matched_mlp"]}" stroke="#ffffff" stroke-width="1.8"/>',
        svg_text(1147, 37, "RelCompat3D-MLP", 28, 400),
    ]
    panels = [
        ("(a) VL-SAT", "VL-SAT", 78, (0.36, 1.0), (0.0, 0.06)),
        ("(b) Open3DSG", "Open3DSG", 568, (0.0, 0.70), (0.0, 0.70)),
        ("(c) SGFN", "SGFN", 1058, (0.20, 1.0), (0.0, 0.10)),
    ]
    plot_y, plot_w, plot_h = 92, 360, 300

    def map_point(
        recall: float,
        violation: float,
        plot_x: float,
        x_range: tuple[float, float],
        y_range: tuple[float, float],
    ) -> tuple[float, float]:
        x = plot_x + (recall - x_range[0]) / (x_range[1] - x_range[0]) * plot_w
        y = plot_y + plot_h - (violation - y_range[0]) / (y_range[1] - y_range[0]) * plot_h
        return x, y

    for title, source, plot_x, x_range, y_range in panels:
        parts.append(svg_text(plot_x + plot_w / 2, 72, title, 32, 700, anchor="middle"))
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            gx = plot_x + frac * plot_w
            gy = plot_y + frac * plot_h
            parts.extend(
                [
                    f'<line x1="{gx:.1f}" y1="{plot_y}" x2="{gx:.1f}" y2="{plot_y+plot_h}" stroke="#d9dde1" stroke-width="1.6"/>',
                    f'<line x1="{plot_x}" y1="{gy:.1f}" x2="{plot_x+plot_w}" y2="{gy:.1f}" stroke="#d9dde1" stroke-width="1.6"/>',
                ]
            )
            x_tick = 100 * (x_range[0] + frac * (x_range[1] - x_range[0]))
            y_tick = 100 * (y_range[0] + (1 - frac) * (y_range[1] - y_range[0]))
            parts.append(svg_text(gx, plot_y + plot_h + 64, f"{x_tick:.0f}", 28, 400, COLORS["muted"], "middle"))
            parts.append(svg_text(plot_x - 14, gy + 9, f"{y_tick:.0f}", 28, 400, COLORS["muted"], "end"))
        parts.extend(
            [
                f'<line x1="{plot_x}" y1="{plot_y+plot_h}" x2="{plot_x+plot_w}" y2="{plot_y+plot_h}" stroke="{COLORS["axis"]}" stroke-width="2.2"/>',
                f'<line x1="{plot_x}" y1="{plot_y}" x2="{plot_x}" y2="{plot_y+plot_h}" stroke="{COLORS["axis"]}" stroke-width="2.2"/>',
                svg_text(plot_x + plot_w / 2, 510, "Recall@K (%)", 30, 700, anchor="middle"),
            ]
        )

        mapped: dict[str, list[tuple[float, float]]] = {}
        for condition in ("source_score", "routed_product", "routed_matched_mlp"):
            points = [
                map_point(
                    data[source][condition][str(k)]["recall"],
                    data[source][condition][str(k)]["violation"],
                    plot_x,
                    x_range,
                    y_range,
                )
                for k in KS
            ]
            mapped[condition] = points
            path = " ".join(
                ("M" if index == 0 else "L") + f" {x:.1f} {y:.1f}"
                for index, (x, y) in enumerate(points)
            )
            dash = ' stroke-dasharray="9,7"' if condition == "source_score" else ""
            parts.append(
                f'<path d="{path}" fill="none" stroke="{COLORS[condition]}" stroke-width="3.4"{dash}/>'
            )
            for x, y in points:
                if condition == "source_score":
                    parts.append(
                        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#ffffff" stroke="{COLORS[condition]}" stroke-width="2.2"/>'
                    )
                elif condition == "routed_product":
                    parts.append(
                        f'<rect x="{x-7:.1f}" y="{y-7:.1f}" width="14" height="14" fill="{COLORS[condition]}" stroke="#ffffff" stroke-width="1.8"/>'
                    )
                else:
                    parts.append(
                        f'<path d="M {x:.1f} {y-8:.1f} L {x+8:.1f} {y+7:.1f} L {x-8:.1f} {y+7:.1f} Z" fill="{COLORS[condition]}" stroke="#ffffff" stroke-width="1.8"/>'
                    )
        label_offsets = {
            ("VL-SAT", "source_score", 50): (-18, -16),
            ("VL-SAT", "source_score", 100): (16, -16),
            ("SGFN", "source_score", 10): (-13, -16),
            ("SGFN", "source_score", 20): (14, -16),
        }
        for k, (x, y) in zip(KS, mapped["source_score"]):
            dx, dy = label_offsets.get((source, "source_score", k), (0, -16))
            if y + dy < plot_y + 25:
                dy = 31
            if y + dy > plot_y + plot_h - 5:
                dy = -16
            parts.append(
                svg_text(
                    x + dx,
                    y + dy,
                    str(k),
                    28,
                    700,
                    COLORS["source_score"],
                    "middle",
                )
            )
    parts.append(
        f'<text x="30" y="245" transform="rotate(-90 30 245)" font-family="{FIGURE_FONT}" font-size="30" font-weight="700" fill="{COLORS["axis"]}" text-anchor="middle">Violation@K (%) ↓</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def convert_svg(stem: str) -> None:
    if shutil.which("rsvg-convert") is None:
        return
    subprocess.run(
        [
            "rsvg-convert",
            "--width",
            "2400",
            "--keep-aspect-ratio",
            "--output",
            str(OUT_DIR / f"{stem}.png"),
            str(OUT_DIR / f"{stem}.svg"),
        ],
        check=True,
    )
    subprocess.run(
        ["rsvg-convert", "-f", "pdf", "-o", str(OUT_DIR / f"{stem}.pdf"), str(OUT_DIR / f"{stem}.svg")],
        check=True,
    )


def load_figure3_cases() -> list[dict[str, object]]:
    inspection = json.loads(INSPECTION_JSON.read_text())
    family_cases = {case["case_id"]: case for case in inspection["representative_cases"]["family_mechanism_examples"]}
    residual_cases = {case["case_id"]: case for case in inspection["representative_cases"]["residual_calibration_risk"]}
    cases = []
    for case_id in EXPECTED_FIGURE3_CASES:
        cases.append(family_cases.get(case_id) or residual_cases[case_id])
    return cases


def validate_outputs(figure2_data: dict[str, dict[str, dict[str, dict[str, float]]]], figure3_cases: list[dict[str, object]]) -> dict[str, object]:
    errors: list[str] = []
    tolerance = 5e-4

    for k, source_rows in EXPECTED_FIGURE2_REFERENCES.items():
        for source, expected_rows in source_rows.items():
            for condition, expected in expected_rows.items():
                actual = figure2_data.get(source, {}).get(condition, {}).get(k)
                if actual is None:
                    errors.append(f"missing Figure 2 row: {source} {condition} K={k}")
                    continue
                for metric, expected_value in zip(("recall", "violation"), expected):
                    diff = abs(float(actual[metric]) - expected_value)
                    if diff > tolerance:
                        errors.append(
                            f"Figure 2 mismatch: {source} {condition} K={k} {metric} "
                            f"actual={float(actual[metric]):.6f} expected={expected_value:.6f}"
                        )

    actual_cases = [str(case["case_id"]) for case in figure3_cases]
    if actual_cases != EXPECTED_FIGURE3_CASES:
        errors.append(f"Figure 3 case order mismatch: actual={actual_cases} expected={EXPECTED_FIGURE3_CASES}")

    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "checks": {
            "figure2_locked_values": "passed" if not [e for e in errors if e.startswith("Figure 2")] else "failed",
            "main_figure_case_locks": "passed" if actual_cases == EXPECTED_FIGURE3_CASES else "failed",
            "svg_xml_parse": "checked_by_external_command",
        },
        "tolerance": tolerance,
    }


def generate_figure3(cases: list[dict[str, object]]) -> str:
    width, height = 1280, 660
    roles = {
        "open3dsg_case_001": ("A", "Proximity demotion", "#eff6ff"),
        "open3dsg_case_019": ("B", "Relative-vertical demotion", "#ecfdf5"),
        "open3dsg_case_026": ("C", "Residual calibration risk", "#fff1f2"),
    }
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="660" viewBox="0 0 1280 660">',
        '<rect width="1280" height="660" fill="#ffffff"/>',
        svg_text(55, 45, "Family-structured failures and residual calibration risk", 22, 700),
        svg_text(55, 72, "Traceable Open3DSG inspection rows; this is not a representative human audit.", 14, 400, "#4b5563"),
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
        parts.append(svg_text(x + 310, y + 153, f"Compatibility: {float(case['p_geom_valid']):.4f}", 13, 400))
        reason = ", ".join(case["reason_codes"])
        parts.append(svg_wrapped_text(x + 20, y + 178, f"Reason: {reason}", 64, size=12, fill="#374151"))
    parts.append(svg_text(60, 620, "Qualitative evidence only: 10/36 sampled rule-violated cases retain compatibility above 0.9.", 12, 400, "#6b7280"))
    parts.append("</svg>")
    return "\n".join(parts)


def write_outputs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    figure2_data = load_figure2_data()
    figure3_cases = load_figure3_cases()

    outputs = {
        "figure2_tradeoff.svg": generate_camera_ready_figure2(figure2_data),
    }
    for filename, content in outputs.items():
        (OUT_DIR / filename).write_text(content + "\n")
    convert_svg("figure2_tradeoff")

    (OUT_DIR / "figure2_data.json").write_text(json.dumps(figure2_data, indent=2, sort_keys=True) + "\n")
    validation = validate_outputs(figure2_data, figure3_cases)
    (OUT_DIR / "validation.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n")

    manifest = {
        "status": "current_main_figures_generated_verified" if validation["status"] == "passed" else "current_main_figures_validation_failed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "outputs": {key: str((OUT_DIR / key).relative_to(ROOT)) for key in outputs},
        "converted_outputs": {
            "figure2_tradeoff.pdf": str((OUT_DIR / "figure2_tradeoff.pdf").relative_to(ROOT)),
            "figure2_tradeoff.png": str((OUT_DIR / "figure2_tradeoff.png").relative_to(ROOT)),
        },
        "source_lock": "paper/figures.md",
        "source_artifacts": [
            str(ROUTED_COMPARATOR_METRICS.relative_to(ROOT)),
            str(INSPECTION_JSON.relative_to(ROOT)),
        ],
        "validation": str((OUT_DIR / "validation.json").relative_to(ROOT)),
        "claim_boundary": "evidence across predictors on a shared geometry-identifiable 3DSSG target; all five K values are labeled without a selected-point marker",
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    write_outputs()
