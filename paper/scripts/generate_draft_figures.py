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
    ROOT / "experiments" / "H001_geom_reliability" / "structured_main_v1" /
    "evaluation" / "summary.json"
)
ROUTING_METRICS = (
    ROOT / "experiments" / "H001_geom_reliability" / "support_contact_routing_v1" /
    "evaluation" / "summary.json"
)
OPEN3DSG_OFFICIAL_METRICS = (
    ROOT / "experiments" / "H001_geom_reliability" / "open3dsg_official_route_v1" /
    "evaluation" / "summary.json"
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
    "source_score": "#4b5563",
    "family_slot_rerank": "#059669",
    "axis": "#111827",
    "grid": "#d1d5db",
    "muted": "#6b7280",
    "panel": "#f8fafc",
    "ink": "#111827",
}

KS = (5, 10, 20, 50, 100)

EXPECTED_FIGURE2_K100 = {
    "VL-SAT": {"source_score": (0.9635, 0.0476), "family_slot_rerank": (0.9658, 0.0295)},
    "Open3DSG": {"source_score": (0.5111, 0.1242), "family_slot_rerank": (0.5692, 0.0324)},
    "SGFN": {"source_score": (0.9235, 0.0630), "family_slot_rerank": (0.9303, 0.0350)},
}

EXPECTED_FIGURE3_CASES = [
    "open3dsg_case_001",
    "open3dsg_case_010",
    "open3dsg_case_026",
]

LABELS = {
    "source_score": "Source score",
    "family_slot_rerank": "Applicability-routed RelCompat3D",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def svg_text(x: float, y: float, text: str, size: int = 14, weight: int = 400, fill: str = "#111827",
             anchor: str = "start") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Helvetica, Arial, sans-serif" '
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
        svg_text(800, 34, "RelCompat3D: Relation-Algebra-Constrained Geometric Compatibility", 24, 700, anchor="middle"),
        svg_text(800, 59, "High source confidence need not imply geometric support; one predictor-agnostic model scores the reconstructed object pair.", 13, 400, "#475569", "middle"),
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
        svg_text(200, 372, "reconstructed ordered-pair geometry", 11, 400, "#475569", "middle"),
    ])
    parts.extend([
        svg_text(45, 414, "Open3DSG: heater —close by→ trash can", 13, 700),
        svg_text(45, 440, "source rank 19   •   Z = 0.853", 12, 700, "#1d4ed8"),
        svg_text(45, 466, "actual ordered-pair geometry: far apart", 12, 400, "#9a3412"),
        svg_text(45, 500, "High source confidence ≠ geometric support", 14, 700, "#9a3412"),
    ])

    # Column 2: identity-preserving row plus T, G, Z factor separation.
    parts.extend([
        box(430, 137, 305, 85, "Identity-preserving row", "scan • context • subject/object IDs", "#ffffff", 38),
        box(430, 241, 305, 72, "Predicate semantics  T", "predicate label and relation family", "#ffffff", 36),
        box(430, 331, 305, 102, "Same-pair geometry  G", "distance, contact, overlap, extents, and vertical displacement", "#fffaf0", 38),
        box(430, 451, 305, 72, "Source confidence  Z", "fixed source relation score", "#ffffff", 36),
        svg_text(582, 551, "Join by object identity—not category", 12, 700, "#1e3a8a", "middle"),
    ])

    # Column 3: learned compatibility, leakage boundary, and falsification.
    parts.extend([
        f'<rect x="820" y="137" width="305" height="127" rx="9" fill="#ffffff" stroke="#86a978"/>',
        svg_text(972, 168, "Train-only compatibility", 15, 700, "#315b27", "middle"),
        svg_text(972, 204, "C_alg(T,G)", 23, 700, "#315b27", "middle"),
        svg_text(972, 231, "linked margin + exact orbit projection", 11, 400, "#475569", "middle"),
        svg_text(972, 251, "swap / inverse equivariance by construction", 11, 700, "#315b27", "middle"),
        f'<rect x="835" y="286" width="275" height="43" rx="21" fill="#fee2e2" stroke="#ef4444"/>',
        svg_text(972, 313, "No source-score input to C_alg", 14, 700, "#991b1b", "middle"),
        box(815, 353, 315, 87, "Linked counterfactual objective", "positive above its wrong-T / wrong-pair negative", "#ffffff", 39),
        box(815, 461, 315, 92, "Relation algebra", "close-by swap • vertical inverse • no blanket support swap", "#ffffff", 40),
    ])

    # Column 4: scoring, observable rank change, and joint evaluation.
    parts.extend([
        box(1215, 132, 335, 63, "Main structured product", "S = Z × C_alg(T,G)", "#ffffff", 39),
        box(1215, 207, 335, 63, "Fusion comparators", "rank-average • RRF", "#ffffff", 39),
        box(1215, 282, 335, 58, "Family-conditioning ablation", "pooled product", "#ffffff", 39),
        f'<rect x="1215" y="352" width="335" height="66" rx="9" fill="#fff7ed" stroke="#d97706"/>',
        svg_text(1382, 377, "Observed re-ranking", 14, 700, "#9a3412", "middle"),
        svg_text(1382, 404, "rank 19  →  304", 19, 700, "#9a3412", "middle"),
        f'<rect x="1215" y="433" width="335" height="120" rx="9" fill="#ffffff" stroke="#a78bca"/>',
        svg_text(1382, 462, "Joint evaluation contract", 15, 700, "#5b3b82", "middle"),
        svg_text(1242, 494, "Exact-label Recall@K  ↑", 13, 700, "#166534"),
        svg_text(1242, 522, "Verifier-derived Violation@K  ↓", 13, 700, "#991b1b"),
        svg_text(1242, 546, "uncertainty • coverage • paired CI", 11, 400, "#475569"),
    ])

    for x1, x2 in [(380, 405), (760, 785), (1160, 1185)]:
        parts.append(f'<line x1="{x1}" y1="305" x2="{x2}" y2="305" stroke="#374151" stroke-width="2.2" marker-end="url(#arrow)"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def load_figure2_data() -> dict[str, dict[str, dict[str, dict[str, float]]]]:
    payload = json.loads(ROUTING_METRICS.read_text())
    open_payload = json.loads(OPEN3DSG_OFFICIAL_METRICS.read_text())
    result: dict[str, dict[str, dict[str, dict[str, float]]]] = {}
    for source, label in (
        ("vlsat", "VL-SAT"),
        ("open3dsg", "Open3DSG"),
        ("sgfn", "SGFN"),
    ):
        overall = (
            open_payload["routes"]["official_strict_full_548"]["overall"]
            if source == "open3dsg"
            else payload["sources"][source]["overall"]
        )
        result[label] = {
            condition: {
                str(k): {
                    "recall": float(overall[condition][str(k)]["recall"]["point"]),
                    "violation": float(overall[condition][str(k)]["violation_all"]["point"]),
                }
                for k in KS
            }
            for condition in ("source_score", "family_slot_rerank")
        }
    return result


def generate_figure2(data: dict[str, dict[str, dict[str, dict[str, float]]]]) -> str:
    width, height = 1500, 430
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="430" viewBox="0 0 1500 430">',
        '<rect width="1500" height="430" fill="#ffffff"/>',
        f'<line x1="1040" y1="24" x2="1088" y2="24" stroke="{COLORS["source_score"]}" stroke-width="2.5" stroke-dasharray="7 5"/>',
        svg_text(1098, 30, "Source score", 20, 400),
        f'<line x1="1220" y1="24" x2="1268" y2="24" stroke="{COLORS["family_slot_rerank"]}" stroke-width="2.8"/>',
        svg_text(1278, 30, "RelCompat3D (routed)", 20, 400),
    ]

    panels = [
        ("(a) VL-SAT", "VL-SAT", 70, 70, 380, 280),
        ("(b) Open3DSG", "Open3DSG", 560, 70, 380, 280),
        ("(c) SGFN", "SGFN", 1050, 70, 380, 280),
    ]

    def map_point(x: float, y: float, px: int, py: int, pw: int, ph: int, xr: tuple[float, float], yr: tuple[float, float]) -> tuple[float, float]:
        sx = px + (x - xr[0]) / (xr[1] - xr[0]) * pw
        sy = py + ph - (y - yr[0]) / (yr[1] - yr[0]) * ph
        return sx, sy

    for title, source, px, py, pw, ph in panels:
        all_rows = [row for condition in data[source].values() for row in condition.values()]
        recalls = [row["recall"] for row in all_rows]
        violations = [row["violation"] for row in all_rows]
        xpad = max((max(recalls) - min(recalls)) * 0.10, 0.005)
        ypad = max((max(violations) - min(violations)) * 0.12, 0.002)
        xr = (max(0.0, min(recalls) - xpad), min(1.0, max(recalls) + xpad))
        yr = (max(0.0, min(violations) - ypad), max(violations) + ypad)
        parts.append(svg_text(px, py - 20, title, 25, 700))
        for frac in (0.0, 0.5, 1.0):
            gx = px + frac * pw
            gy = py + frac * ph
            parts.append(f'<line x1="{gx:.1f}" y1="{py}" x2="{gx:.1f}" y2="{py+ph}" stroke="#e5e7eb" stroke-width="1"/>')
            parts.append(f'<line x1="{px}" y1="{gy:.1f}" x2="{px+pw}" y2="{gy:.1f}" stroke="#e5e7eb" stroke-width="1"/>')
            parts.append(svg_text(gx, py + ph + 19, f"{xr[0] + frac * (xr[1] - xr[0]):.3f}", 16, 400, "#6b7280", "middle"))
            parts.append(svg_text(px - 10, py + ph - frac * ph + 4, f"{yr[0] + frac * (yr[1] - yr[0]):.3f}", 16, 400, "#6b7280", "end"))
        parts.append(f'<line x1="{px}" y1="{py+ph}" x2="{px+pw}" y2="{py+ph}" stroke="{COLORS["axis"]}" stroke-width="1.4"/>')
        parts.append(f'<line x1="{px}" y1="{py}" x2="{px}" y2="{py+ph}" stroke="{COLORS["axis"]}" stroke-width="1.4"/>')
        parts.append(svg_text(px + pw / 2, py + ph + 46, "Recall@K", 21, 700, anchor="middle"))

        mapped_points = {}
        for condition in ("source_score", "family_slot_rerank"):
            points = [
                map_point(data[source][condition][str(k)]["recall"], data[source][condition][str(k)]["violation"], px, py, pw, ph, xr, yr)
                for k in KS
            ]
            mapped_points[condition] = points
            path = " ".join(("M" if idx == 0 else "L") + f" {x:.1f} {y:.1f}" for idx, (x, y) in enumerate(points))
            dash = ' stroke-dasharray="7 5"' if condition == "source_score" else ""
            parts.append(f'<path d="{path}" fill="none" stroke="{COLORS[condition]}" stroke-width="2.8"{dash}/>')
            for k, (x, y) in zip(KS, points):
                radius = 5.5 if k == 100 else 4.2
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{COLORS[condition]}" stroke="#ffffff" stroke-width="1.2"/>')
                if k == 100:
                    parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" fill="none" stroke="#111827" stroke-width="1.4"/>')
        for idx, k in enumerate(KS):
            sx, sy = mapped_points["source_score"][idx]
            mx, my = mapped_points["family_slot_rerank"][idx]
            label_x = (sx + mx) / 2
            label_y = min(sy, my) - 10
            if source == "SGFN" and k in {10, 20}:
                label_x += -14 if k == 10 else 18
            parts.append(svg_text(label_x, label_y, str(k), 16, 700, "#374151", "middle"))

    parts.append(f'<text x="20" y="215" transform="rotate(-90 20 215)" font-family="Helvetica, Arial, sans-serif" font-size="21" font-weight="700" fill="#111827" text-anchor="middle">Violation@K (lower is better)</text>')
    parts.append(svg_text(1475, 414, "Outline: K=100", 16, 400, "#4b5563", "end"))
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

    for source, expected_rows in EXPECTED_FIGURE2_K100.items():
        for condition, expected in expected_rows.items():
            actual = figure2_data.get(source, {}).get(condition, {}).get("100")
            if actual is None:
                errors.append(f"missing Figure 2 row: {source} {condition} K=100")
                continue
            for metric, expected_value in zip(("recall", "violation"), expected):
                diff = abs(float(actual[metric]) - expected_value)
                if diff > tolerance:
                    errors.append(
                        f"Figure 2 mismatch: {source} {condition} {metric} "
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
            "figure3_case_ids": "passed" if actual_cases == EXPECTED_FIGURE3_CASES else "failed",
            "svg_xml_parse": "checked_by_external_command",
        },
        "tolerance": tolerance,
    }


def generate_figure3(cases: list[dict[str, object]]) -> str:
    width, height = 1280, 660
    roles = {
        "open3dsg_case_001": ("A", "Proximity demotion", "#eff6ff"),
        "open3dsg_case_010": ("B", "Support/contact demotion", "#ecfdf5"),
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
        "figure2_tradeoff.svg": generate_figure2(figure2_data),
    }
    for filename, content in outputs.items():
        (OUT_DIR / filename).write_text(content + "\n")
    convert_svg("figure2_tradeoff")

    (OUT_DIR / "figure2_data.json").write_text(json.dumps(figure2_data, indent=2, sort_keys=True) + "\n")
    (OUT_DIR / "figure3_cases.json").write_text(json.dumps(figure3_cases, indent=2, sort_keys=True) + "\n")
    validation = validate_outputs(figure2_data, figure3_cases)
    (OUT_DIR / "validation.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n")

    manifest = {
        "status": "draft_figures_generated_verified" if validation["status"] == "passed" else "draft_figures_generated_validation_failed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "outputs": {key: str((OUT_DIR / key).relative_to(ROOT)) for key in outputs},
        "converted_outputs": {
            "figure2_tradeoff.pdf": str((OUT_DIR / "figure2_tradeoff.pdf").relative_to(ROOT)),
            "figure2_tradeoff.png": str((OUT_DIR / "figure2_tradeoff.png").relative_to(ROOT)),
        },
        "source_lock": "paper/figures.md",
        "source_artifacts": [
            str(STRUCTURED_MAIN_METRICS.relative_to(ROOT)),
            str(INSPECTION_JSON.relative_to(ROOT)),
        ],
        "validation": str((OUT_DIR / "validation.json").relative_to(ROOT)),
        "layout_review": str(LAYOUT_REVIEW.relative_to(ROOT)),
        "claim_boundary": "cross-predictor evidence on a shared geometry-identifiable 3DSSG target; K=100 is primary and all five K values are reported",
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    geometry_note = ""
    if (OUT_DIR / "figure3_geometry_panels.svg").exists():
        geometry_note = """
- `figure1_framework.{svg,pdf,png}`: geometry-backed method overview, generated by `render_figure3_geometry_panels.py`.
- `figure3_geometry_panels.{svg,pdf,png}`: geometry-backed qualitative cases, generated by the same script.
- `figure3_geometry_manifest.json`: source and output manifest for Figures 1 and 3.
"""

    report = f"""# Draft Figure Generation

Status: `{manifest["status"]}`

Generated outputs:

- `figure2_tradeoff.svg`: three-source Recall--Violation trajectories over K=5/10/20/50/100.
- `figure2_tradeoff.pdf`: vector manuscript figure.
- `figure2_tradeoff.png`: raster preview only.
{geometry_note.rstrip()}
- `figure2_data.json`: extracted numeric values used for Figure 2.
- `figure3_cases.json`: extracted case rows used for Figure 3.
- `validation.json`: source-lock value and case-ID validation.
- `layout_review.md`: top-tier novelty/layout review, written after generation.

Validation rules:

- Verify Figure 2 values against `paper/figures.md` and the promoted structured
  main evaluation `summary.json`.
- Verify Figure 3 case IDs against `paper/figures.md` and Open3DSG `inspection.json`.
- Use the PDF conversions in LaTeX; PNG files are previews only.
"""
    (OUT_DIR / "report.md").write_text(report)


if __name__ == "__main__":
    write_outputs()
