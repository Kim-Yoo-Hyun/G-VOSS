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


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "paper" / "generated" / "figures"

TABLE1_JSON = ROOT / "experiments" / "H001_geom_reliability" / "tables" / "table1_main_prediction.json"
OPEN3DSG_METRICS = (
    ROOT / "experiments" / "H001_geom_reliability" / "sources" / "open3dsg" / "metrics" / "metrics.json"
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
        "semantic_only": {"r100": 0.9894, "violation100": 0.0469},
        "probabilistic_recalibrated": {"r100": 0.9921, "violation100": 0.0391},
        "family_specific_p_geom_valid": {"r100": 0.9914, "violation100": 0.0310},
        "rule_verified_point_subtype": {"r100": 0.9890, "violation100": 0.0},
    },
    "Open3DSG": {
        "semantic_only": {"r100": 0.4963, "violation100": 0.1195},
        "probabilistic_recalibrated": {"r100": 0.5580, "violation100": 0.0803},
        "family_specific_p_geom_valid": {"r100": 0.5984, "violation100": 0.0311},
        "rule_verified_point_subtype": {"r100": 0.5238, "violation100": 0.0},
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
            box(55, y + 22, 245, 90, "Probabilistic", "score_sem * p_geom_valid; recall-first re-ranking", "#eff6ff"),
            box(330, y + 22, 245, 90, "Rule-verified", "remove hard violations; zero-violation diagnostic", "#fff1f2"),
            box(605, y + 22, 245, 90, "Family-specific", "stricter calibration for violation-first operation", "#ecfdf5"),
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


def load_figure2_data() -> dict[str, list[dict[str, float | str]]]:
    table1 = json.loads(TABLE1_JSON.read_text())
    vlsat = []
    keep = [
        "semantic_only",
        "probabilistic_recalibrated",
        "family_specific_p_geom_valid",
        "rule_verified_point_subtype",
    ]
    rows_by_condition = {row["condition"]: row for row in table1}
    for condition in keep:
        row = rows_by_condition[condition]
        vlsat.append(
            {
                "source": "VL-SAT",
                "condition": condition,
                "r100": row["r100"],
                "violation100": row["violation100"],
            }
        )

    metrics = json.loads(OPEN3DSG_METRICS.read_text())["conditions"]
    open3dsg_map = {
        "semantic_only": "semantic_only",
        "probabilistic_recalibrated": "probabilistic_recalibrated",
        "family_specific_p_geom_valid": "control_family_specific_p_geom_valid",
        "rule_verified_point_subtype": "rule_verified_point_subtype",
    }
    open3dsg = []
    for label, key in open3dsg_map.items():
        row = metrics[key]
        open3dsg.append(
            {
                "source": "Open3DSG",
                "condition": label,
                "r100": row["recall"]["by_k"]["100"]["recall"],
                "violation100": row["violation_rate"]["by_k"]["100"]["violation_rate"],
            }
        )
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
        ("A. VL-SAT primary source", "VL-SAT", 70, 115, 520, 360, (0.0, 0.05), (0.985, 0.994)),
        ("B. Open3DSG second source", "Open3DSG", 690, 115, 520, 360, (0.0, 0.13), (0.45, 0.62)),
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
    parts.append(svg_text(70, 585, "Open3DSG panel is a Docker-reproduced averaged-BLIP second-source variant under covered H001 scope.", 12, 400, "#6b7280"))
    parts.append("</svg>")
    return "\n".join(parts)


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

    (OUT_DIR / "figure2_data.json").write_text(json.dumps(figure2_data, indent=2, sort_keys=True) + "\n")
    (OUT_DIR / "figure3_cases.json").write_text(json.dumps(figure3_cases, indent=2, sort_keys=True) + "\n")
    validation = validate_outputs(figure2_data, figure3_cases)
    (OUT_DIR / "validation.json").write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n")

    manifest = {
        "status": "draft_figures_generated_verified" if validation["status"] == "passed" else "draft_figures_generated_validation_failed",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "outputs": {key: str((OUT_DIR / key).relative_to(ROOT)) for key in outputs},
        "source_lock": "paper/figures.md",
        "source_artifacts": [
            str(TABLE1_JSON.relative_to(ROOT)),
            str(OPEN3DSG_METRICS.relative_to(ROOT)),
            str(INSPECTION_JSON.relative_to(ROOT)),
        ],
        "validation": str((OUT_DIR / "validation.json").relative_to(ROOT)),
        "layout_review": str(LAYOUT_REVIEW.relative_to(ROOT)),
        "claim_boundary": "draft figures only; scoped H001 relation-reliability claim",
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    report = f"""# Draft Figure Generation

Status: `{manifest["status"]}`

Generated outputs:

- `figure1_framework.svg`: method/framework schematic.
- `figure2_tradeoff.svg`: two-panel R@100 / Violation@100 tradeoff.
- `figure3_failure_cases.svg`: Open3DSG qualitative row-card panels.
- `figure2_data.json`: extracted numeric values used for Figure 2.
- `figure3_cases.json`: extracted case rows used for Figure 3.
- `validation.json`: source-lock value and case-ID validation.
- `layout_review.md`: top-tier novelty/layout review, written after generation.

Validation rules:

- Verify Figure 2 values against `paper/figures.md`, Table 1, and Open3DSG `metrics.json`.
- Verify Figure 3 case IDs against `paper/figures.md` and Open3DSG `inspection.json`.
- Treat all SVGs as draft manuscript figures, not camera-ready final artwork.
"""
    (OUT_DIR / "report.md").write_text(report)


if __name__ == "__main__":
    write_outputs()
