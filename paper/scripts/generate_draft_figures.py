#!/usr/bin/env python3
"""Generate draft H001 paper figures from locked source artifacts.

The figures are draft SVGs for manuscript planning. They are intentionally
simple, traceable, and source-backed rather than camera-ready artwork.
"""

from __future__ import annotations

import base64
import html
import io
import json
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "paper" / "generated" / "figures"

VLSAT_FULL_METRICS = (
    ROOT / "experiments" / "H001_geom_reliability" / "sources" / "vlsat" / "full_validation" / "metrics_k_sweep" / "metrics.json"
)
OPEN3DSG_METRICS = (
    ROOT
    / "experiments"
    / "H001_geom_reliability"
    / "sources"
    / "open3dsg"
    / "full_validation"
    / "recovery_relaxed_views_min2"
    / "metrics_k_sweep"
    / "metrics.json"
)
SGFN_METRICS = (
    ROOT / "experiments" / "H001_geom_reliability" / "sources" / "sgfn" /
    "confirmatory_metrics" / "summary.json"
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
    "family_conditional_risk": "#059669",
    "axis": "#111827",
    "grid": "#d1d5db",
    "muted": "#6b7280",
    "panel": "#f8fafc",
    "ink": "#111827",
}

KS = (5, 10, 20, 50, 100)

EXPECTED_FIGURE2_K100 = {
    "VL-SAT": {"semantic_only": (0.9635, 0.0476), "family_conditional_risk": (0.9683, 0.0333)},
    "Open3DSG": {"semantic_only": (0.5161, 0.1242), "family_conditional_risk": (0.6047, 0.0341)},
    "SGFN": {"semantic_only": (0.9235, 0.0630), "family_conditional_risk": (0.9416, 0.0381)},
}

EXPECTED_FIGURE3_CASES = [
    "open3dsg_case_001",
    "open3dsg_case_010",
    "open3dsg_case_026",
]

LABELS = {
    "semantic_only": "Source score",
    "family_conditional_risk": "Family-calibrated product",
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
    width, height = 1600, 590
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="590" viewBox="0 0 1600 590">',
        '<rect width="1600" height="590" fill="#ffffff"/>',
        arrow_marker(),
        svg_text(800, 34, "GeoCalib: Factor-Isolated Reliability for 3D Scene Graph Relations", 24, 700, anchor="middle"),
        svg_text(800, 58, "The source proposes a plausible relation; same-pair geometry independently tests whether the predicate is supported.", 13, 400, "#475569", "middle"),
    ]

    columns = [
        (20, 82, 360, 475, "1. Observed failure", "#eef4ff", "#4f78b8"),
        (405, 82, 355, 475, "2. Isolate evidence factors", "#f4f7ff", "#688fc8"),
        (785, 82, 375, 475, "3. Calibrate compatibility", "#eef8eb", "#6a9d56"),
        (1185, 82, 395, 475, "4. Re-rank and evaluate", "#f8f2fb", "#8d68b8"),
    ]
    for x, y, w, h, title, fill, stroke in columns:
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')
        parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="38" rx="10" fill="{stroke}" fill-opacity="0.13"/>')
        parts.append(svg_text(x + w / 2, y + 25, title, 15, 700, "#172554", "middle"))

    # Column 1: an actual ordered object-pair example from Figure 3.
    geometry_png = OUT_DIR / "figure3_geometry_panels.png"
    if geometry_png.exists():
        image = Image.open(geometry_png).convert("RGB")
        crop = image.crop((0, 0, image.width // 3, image.height))
        buffer = io.BytesIO()
        crop.save(buffer, format="PNG")
        payload = base64.b64encode(buffer.getvalue()).decode("ascii")
        parts.append(f'<image x="40" y="140" width="320" height="255" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{payload}"/>')
    else:
        parts.append(f'<rect x="40" y="140" width="320" height="255" rx="8" fill="#ffffff" stroke="#94a3b8"/>')
        parts.append(svg_text(200, 270, "ordered-pair geometry", 14, 700, "#475569", "middle"))
    parts.extend([
        svg_text(45, 425, "Open3DSG: heater —close by→ trash can", 13, 700),
        svg_text(45, 451, "source confidence 0.853, but pair geometry is far", 12, 400, "#9a3412"),
        svg_text(45, 478, "Semantic plausibility ≠ physical support", 14, 700, "#9a3412"),
    ])

    # Column 2: T, G, Z separation and the leakage boundary.
    parts.extend([
        box(430, 145, 305, 82, "Predicate semantics  T", "predicate label and family", "#ffffff", 34),
        box(430, 248, 305, 105, "Same-pair geometry  G", "distance, contact, overlap, support, and vertical order", "#fffaf0", 38),
        box(430, 374, 305, 82, "Source confidence  Z", "the fixed source relation score", "#ffffff", 34),
        f'<rect x="455" y="482" width="255" height="42" rx="21" fill="#fee2e2" stroke="#ef4444"/>',
        svg_text(582, 508, "Z never enters C(T,G)", 14, 700, "#991b1b", "middle"),
    ])

    # Column 3: compatibility and falsifiable evidence contract.
    parts.extend([
        f'<rect x="830" y="145" width="285" height="112" rx="9" fill="#ffffff" stroke="#86a978"/>',
        svg_text(972, 176, "Compatibility", 15, 700, "#315b27", "middle"),
        svg_text(972, 210, "C(T,G)", 22, 700, "#315b27", "middle"),
        svg_text(972, 236, "predicate-conditioned geometry", 11, 400, "#475569", "middle"),
        box(815, 284, 315, 100, "Identity-preserving join", "scan, context, subject ID, object ID", "#ffffff", 39),
        box(815, 408, 315, 110, "Falsification tests", "wrong predicate, mismatched pair, shuffled geometry, inverse relation", "#ffffff", 38),
    ])

    # Column 4: soft scoring and joint evaluation.
    parts.extend([
        box(1215, 145, 335, 82, "Calibrated product", "S = Z × C(T,G)", "#ffffff", 39),
        box(1215, 248, 335, 82, "Scale-robust rank fusion", "average within-context ranks", "#ffffff", 39),
        f'<rect x="1215" y="360" width="335" height="156" rx="9" fill="#ffffff" stroke="#a78bca"/>',
        svg_text(1382, 391, "Joint reliability evaluation", 15, 700, "#5b3b82", "middle"),
        svg_text(1245, 428, "Exact-label Recall@K", 14, 700, "#166534"),
        svg_text(1245, 460, "Verifier Violation@K", 14, 700, "#991b1b"),
        svg_text(1245, 490, "uncertainty, coverage, paired CI", 12, 400, "#475569"),
    ])

    for x1, x2 in [(380, 405), (760, 785), (1160, 1185)]:
        parts.append(f'<line x1="{x1}" y1="305" x2="{x2}" y2="305" stroke="#374151" stroke-width="2.2" marker-end="url(#arrow)"/>')
    parts.append("</svg>")
    return "\n".join(parts)


def metric_sweep(metrics: dict[str, Any], key: str) -> dict[str, dict[str, float]]:
    row = metrics["conditions"][key]
    return {
        str(k): {
            "recall": float(row["recall"]["by_k"][str(k)]["recall"]),
            "violation": float(row["violation_rate"]["by_k"][str(k)]["violation_rate"]),
        }
        for k in KS
    }


def load_figure2_data() -> dict[str, dict[str, dict[str, dict[str, float]]]]:
    vlsat_metrics = json.loads(VLSAT_FULL_METRICS.read_text())
    open3dsg_metrics = json.loads(OPEN3DSG_METRICS.read_text())
    sgfn_payload = json.loads(SGFN_METRICS.read_text())
    sgfn = sgfn_payload["sources"]["sgfn_official_full_l160_confirmatory"]["overall_global"]
    sgfn_sweep = {
        label: {
            str(k): {
                "recall": float(sgfn[key][str(k)]["recall"]["point"]),
                "violation": float(sgfn[key][str(k)]["violation_rate"]["point"]),
            }
            for k in KS
        }
        for label, key in (
            ("semantic_only", "semantic_only"),
            ("family_conditional_risk", "family_conditional_risk"),
        )
    }
    return {
        "VL-SAT": {
            "semantic_only": metric_sweep(vlsat_metrics, "semantic_only"),
            "family_conditional_risk": metric_sweep(vlsat_metrics, "control_family_specific_p_geom_valid"),
        },
        "Open3DSG": {
            "semantic_only": metric_sweep(open3dsg_metrics, "semantic_only"),
            "family_conditional_risk": metric_sweep(open3dsg_metrics, "control_family_specific_p_geom_valid"),
        },
        "SGFN": sgfn_sweep,
    }


def generate_figure2(data: dict[str, dict[str, dict[str, dict[str, float]]]]) -> str:
    width, height = 1500, 520
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="520" viewBox="0 0 1500 520">',
        '<rect width="1500" height="520" fill="#ffffff"/>',
        svg_text(20, 35, "Recall–violation trajectories across ranking budgets", 22, 700),
        svg_text(1480, 35, "lower Violation  ↓    higher Recall  →", 12, 700, "#475569", "end"),
    ]

    panels = [
        ("A. VL-SAT", "VL-SAT", 45, 100, 420, 330),
        ("B. Open3DSG", "Open3DSG", 540, 100, 420, 330),
        ("C. SGFN", "SGFN", 1035, 100, 420, 330),
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
        parts.append(f'<rect x="{px-20}" y="{py-43}" width="{pw+40}" height="{ph+83}" rx="8" fill="#f8fafc" stroke="#e5e7eb"/>')
        parts.append(svg_text(px, py - 20, title, 17, 700))
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            gx = px + frac * pw
            gy = py + frac * ph
            parts.append(f'<line x1="{gx:.1f}" y1="{py}" x2="{gx:.1f}" y2="{py+ph}" stroke="{COLORS["grid"]}" stroke-width="0.8"/>')
            parts.append(f'<line x1="{px}" y1="{gy:.1f}" x2="{px+pw}" y2="{gy:.1f}" stroke="{COLORS["grid"]}" stroke-width="0.8"/>')
        parts.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="none" stroke="{COLORS["axis"]}" stroke-width="1.2"/>')
        parts.append(svg_text(px + pw / 2, py + ph + 36, "Exact-label Recall@K", 13, 700, anchor="middle"))
        parts.append(svg_text(px + 8, py + 18, "V@K", 11, 700, "#475569"))
        parts.append(svg_text(px, py + ph + 18, f"{xr[0]:.3f}", 10, 400, "#6b7280", "middle"))
        parts.append(svg_text(px + pw, py + ph + 18, f"{xr[1]:.3f}", 10, 400, "#6b7280", "middle"))
        parts.append(svg_text(px - 8, py + ph, f"{yr[0]:.3f}", 10, 400, "#6b7280", "end"))
        parts.append(svg_text(px - 8, py, f"{yr[1]:.3f}", 10, 400, "#6b7280", "end"))

        for condition in ("semantic_only", "family_conditional_risk"):
            points = [
                map_point(data[source][condition][str(k)]["recall"], data[source][condition][str(k)]["violation"], px, py, pw, ph, xr, yr)
                for k in KS
            ]
            path = " ".join(("M" if idx == 0 else "L") + f" {x:.1f} {y:.1f}" for idx, (x, y) in enumerate(points))
            dash = ' stroke-dasharray="5 4"' if condition == "semantic_only" else ""
            parts.append(f'<path d="{path}" fill="none" stroke="{COLORS[condition]}" stroke-width="2.2"{dash}/>')
            for k, (x, y) in zip(KS, points):
                radius = 6 if k == 100 else 4.5
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{COLORS[condition]}" stroke="#ffffff" stroke-width="1.5"/>')
                if k == 100:
                    parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="10" fill="none" stroke="#d97706" stroke-width="2"/>')
                dx = 7 if condition == "family_conditional_risk" else -7
                anchor = "start" if dx > 0 else "end"
                dy = -5 if k in {5, 20, 100} else 12
                parts.append(svg_text(x + dx, y + dy, str(k), 9, 700, COLORS[condition], anchor))

    parts.append(f'<line x1="30" y1="485" x2="75" y2="485" stroke="{COLORS["semantic_only"]}" stroke-width="2.2" stroke-dasharray="5 4"/>')
    parts.append(svg_text(84, 490, "Source score", 12, 400))
    parts.append(f'<line x1="205" y1="485" x2="250" y2="485" stroke="{COLORS["family_conditional_risk"]}" stroke-width="2.2"/>')
    parts.append(svg_text(259, 490, "Family-calibrated product", 12, 400))
    parts.append(svg_text(555, 490, "K=10 operational", 11, 700, "#475569"))
    parts.append(svg_text(720, 490, "K=50 canonical secondary", 11, 700, "#475569"))
    parts.append(svg_text(955, 490, "K=100 primary (orange ring)", 11, 700, "#d97706"))
    parts.append("</svg>")
    return "\n".join(parts)


def write_figure1_png() -> None:
    if shutil.which("rsvg-convert") is None:
        return
    subprocess.run(
        [
            "rsvg-convert",
            "--width",
            "2400",
            "--keep-aspect-ratio",
            "--output",
            str(OUT_DIR / "figure1_framework.png"),
            str(OUT_DIR / "figure1_framework.svg"),
        ],
        check=True,
    )


def write_figure2_png(data: dict[str, dict[str, dict[str, dict[str, float]]]]) -> None:
    if shutil.which("rsvg-convert") is None:
        return
    subprocess.run(
        ["rsvg-convert", "--width", "2400", "--keep-aspect-ratio", "--output", str(OUT_DIR / "figure2_tradeoff.png"), str(OUT_DIR / "figure2_tradeoff.svg")],
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
            str(SGFN_METRICS.relative_to(ROOT)),
            str(INSPECTION_JSON.relative_to(ROOT)),
        ],
        "validation": str((OUT_DIR / "validation.json").relative_to(ROOT)),
        "layout_review": str(LAYOUT_REVIEW.relative_to(ROOT)),
        "claim_boundary": "source-level evidence on a fixed geometry-identifiable 3DSSG target; K=100 is primary and smaller K are secondary diagnostics",
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
- `figure2_tradeoff.svg`: three-source Recall--Violation trajectories over K=5/10/20/50/100.
- `figure2_tradeoff.png`: LaTeX-facing PNG conversion of the K-sweep tradeoff.
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
