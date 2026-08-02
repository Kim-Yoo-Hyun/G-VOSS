#!/usr/bin/env python3
"""Regenerate the record-backed supplementary qualitative figure."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[2]
SOURCE_SVG = Path(__file__).with_name("qualitative_geometry_source.svg")
OUT = ROOT / "paper" / "aaai" / "supplement_figures"

ORANGE = "#D55E00"
BLUE = "#0072B2"
DARK = "#202124"
MUTED = "#5F6368"
RULE = "#B8BDC3"
TEAL = "#007C76"
OCHRE = "#9A6700"


CASES = [
    {
        "panel": "(a)",
        "slug": "proximity_xy",
        "title": "Proximity promotion",
        "relation": "desk / close by / chair",
        "projection": "xy",
        "sample_source": "centers_only",
        "bounds": (-0.34, 0.34, -0.24, 0.24),
        "subject_center": (-0.21778589894179382, 0.0),
        "object_center": (0.21778589894179382, 0.0),
        "ticks_x": (-0.2, 0.0, 0.2),
        "ticks_y": (-0.2, 0.0, 0.2),
        "axis_y": "y",
        "evidence": "XY center distance",
        "value": "0.436 m",
        "interpretation": "nearby centers support close by",
        "rank": "Rank 81 → 30",
        "outcome": "Promoted: proximity",
        "outcome_color": TEAL,
    },
    {
        "panel": "(b)",
        "slug": "vertical_order_xz",
        "title": "Vertical-order demotion",
        "relation": "floor / higher than / curtain",
        "projection": "xz",
        "frame": (498.0, 112.0, 444.0, 250.0),
        "bounds": (-0.793435, 3.087785, -1.992, 0.912),
        "subject_center": (0.939121, -1.505710),
        "object_center": (2.456483, -0.488452),
        "ticks_x": (-0.5, 0, 1, 2, 3),
        "ticks_y": (-1.5, -1.0, -0.5, 0, 0.5),
        "axis_y": "z",
        "evidence": "subject−object center Δz",
        "value": "−1.02 m",
        "interpretation": "subject lies below the object",
        "rank": "Rank 1 → 430",
        "outcome": "Demoted: vertical order",
        "outcome_color": TEAL,
    },
    {
        "panel": "(c)",
        "slug": "support_contact_xz",
        "title": "Support/contact unchanged",
        "relation": "door / lying on / floor",
        "projection": "xz",
        "frame": (978.0, 112.0, 444.0, 250.0),
        "bounds": (-5.441762, 4.539382, -2.036, 0.676),
        "subject_center": (2.458429, -0.452578),
        "object_center": (-1.028215, -1.547378),
        "ticks_x": (-4, -2, 0, 2, 4),
        "ticks_y": (-2, -1, 0),
        "axis_y": "z",
        "evidence": "vertical bottom−top gap",
        "value": "−0.06 m",
        "interpretation": "contact remains unresolved",
        "rank": "Rank 21 → 21",
        "outcome": "Kept in source order",
        "outcome_color": OCHRE,
    },
]


def configure_fonts() -> None:
    preferred = "Times New Roman"
    font_manager.findfont(preferred, fallback_to_default=False)
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": [preferred],
            "mathtext.fontset": "stix",
            "axes.unicode_minus": False,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "svg.hashsalt": "relcompat3d-supplement-qualitative",
        }
    )


def extract_screen_points() -> list[tuple[np.ndarray, np.ndarray]]:
    """Read the 260 endpoint samples per instance from the preserved SVG."""
    root = ET.parse(SOURCE_SVG).getroot()
    extracted: list[tuple[np.ndarray, np.ndarray]] = []

    for case in CASES:
        if case.get("sample_source") == "centers_only":
            empty = np.empty((0, 2), dtype=float)
            extracted.append((empty, empty))
            continue

        frame_x, _, frame_w, _ = case["frame"]
        lo = frame_x
        hi = frame_x + frame_w
        subject: list[tuple[float, float]] = []
        object_: list[tuple[float, float]] = []

        for element in root.iter():
            tag = element.tag.rsplit("}", 1)[-1]
            fill = element.attrib.get("fill", "").lower()
            if tag == "circle" and "cx" in element.attrib:
                x = float(element.attrib["cx"])
                radius = float(element.attrib["r"])
                if lo <= x <= hi and np.isclose(radius, 1.35) and fill == ORANGE.lower():
                    subject.append((x, float(element.attrib["cy"])))
            elif tag == "rect" and "x" in element.attrib:
                x = float(element.attrib["x"])
                width = float(element.attrib["width"])
                if lo <= x <= hi and np.isclose(width, 2.7) and fill == BLUE.lower():
                    object_.append((x + width / 2, float(element.attrib["y"]) + width / 2))

        if len(subject) != 260 or len(object_) != 260:
            raise RuntimeError(
                f"{case['panel']}: expected 260/260 samples, got "
                f"{len(subject)}/{len(object_)}"
            )
        extracted.append((np.asarray(subject), np.asarray(object_)))

    return extracted


def screen_to_data(points: np.ndarray, case: dict) -> np.ndarray:
    frame_x, frame_y, frame_w, frame_h = case["frame"]
    x_min, x_max, y_min, y_max = case["bounds"]
    x = x_min + (points[:, 0] - frame_x) * (x_max - x_min) / frame_w
    y = y_max - (points[:, 1] - frame_y) * (y_max - y_min) / frame_h
    return np.column_stack((x, y))


def style_projection(ax: plt.Axes, case: dict, subject: np.ndarray, object_: np.ndarray) -> None:
    subject_center = np.asarray(case["subject_center"], dtype=float)
    object_center = np.asarray(case["object_center"], dtype=float)

    if subject.size:
        ax.scatter(subject[:, 0], subject[:, 1], s=11, c=ORANGE, alpha=0.45, linewidths=0, zorder=1)
    if object_.size:
        ax.scatter(object_[:, 0], object_[:, 1], s=11, c=BLUE, alpha=0.40, linewidths=0, zorder=1)
    ax.plot(
        [subject_center[0], object_center[0]],
        [subject_center[1], object_center[1]],
        color=BLUE,
        linewidth=3.0,
        linestyle=(0, (6, 4)),
        zorder=3,
    )
    ax.scatter(*subject_center, s=180, c=ORANGE, edgecolors="white", linewidths=2.0, zorder=5)
    ax.scatter(*object_center, s=180, c=BLUE, edgecolors="white", linewidths=2.0, zorder=5)

    x_min, x_max, y_min, y_max = case["bounds"]
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_xticks(case["ticks_x"])
    ax.set_yticks(case["ticks_y"])
    ax.tick_params(axis="both", labelsize=20, width=1.3, length=5.5, pad=5)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("black")
        ax.spines[spine].set_linewidth(1.5)
    ax.plot(1, 0, marker=">", markersize=10, color="black", transform=ax.transAxes, clip_on=False)
    ax.plot(0, 1, marker="^", markersize=10, color="black", transform=ax.transAxes, clip_on=False)
    ax.text(0.98, 0.025, "x", transform=ax.transAxes, ha="right", va="bottom", fontsize=24, fontstyle="italic")
    ax.text(
        0.025,
        0.98,
        case["axis_y"],
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=24,
        fontstyle="italic",
    )
    ax.set_box_aspect(0.70)
    ax.set_xlabel("")
    ax.set_ylabel("")


def add_header(ax: plt.Axes, case: dict) -> None:
    ax.axis("off")
    ax.text(0, 0.96, f"{case['panel']} {case['title']}", ha="left", va="top", fontsize=21, fontweight="bold", color=DARK)
    ax.text(0, 0.05, case["relation"], ha="left", va="bottom", fontsize=19.5, color=DARK)


def add_evidence(ax: plt.Axes, case: dict) -> None:
    ax.axis("off")
    ax.plot([0, 1], [0.98, 0.98], color=RULE, linewidth=1.5, transform=ax.transAxes, clip_on=False)
    ax.text(0, 0.86, "Measured evidence", transform=ax.transAxes, fontsize=20, fontweight="bold", color=MUTED, va="top")
    ax.text(0, 0.64, case["evidence"], transform=ax.transAxes, fontsize=19.5, fontweight="bold", color=DARK, va="top")
    ax.text(0, 0.46, case["value"], transform=ax.transAxes, fontsize=21, fontweight="bold", color=DARK, va="top")
    ax.text(0, 0.28, case["interpretation"], transform=ax.transAxes, fontsize=19.5, color=MUTED, va="top")
    ax.plot([0, 1], [0.19, 0.19], color=RULE, linewidth=1.5, transform=ax.transAxes, clip_on=False)
    ax.text(0, 0.09, case["rank"], transform=ax.transAxes, fontsize=21.5, fontweight="bold", color=DARK, va="top")
    ax.plot([0, 0], [-0.14, 0.01], color=case["outcome_color"], linewidth=4, transform=ax.transAxes, clip_on=False)
    ax.text(0.03, -0.06, case["outcome"], transform=ax.transAxes, fontsize=20, fontweight="bold", color=DARK, va="top")


def validate_case(case: dict, subject: np.ndarray, object_: np.ndarray) -> None:
    if not (np.isfinite(subject).all() and np.isfinite(object_).all()):
        raise ValueError(f"{case['panel']}: non-finite projected point")
    if case["projection"] == "xy":
        distance = np.linalg.norm(np.asarray(case["subject_center"]) - np.asarray(case["object_center"]))
        if not np.isclose(distance, 0.43557179788358763, atol=1e-6):
            raise ValueError(f"proximity distance mismatch: {distance}")
    elif case["panel"] == "(b)":
        delta_z = case["subject_center"][1] - case["object_center"][1]
        if not np.isclose(delta_z, -1.017258, atol=1e-6):
            raise ValueError(f"vertical delta mismatch: {delta_z}")


def save_svg(fig: plt.Figure, path: Path) -> None:
    fig.savefig(
        path,
        facecolor="white",
        metadata={
            "Creator": "RelCompat3D supplementary qualitative renderer",
            "Date": None,
        },
    )
    svg_text = path.read_text(encoding="utf-8")
    path.write_text(
        "\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n",
        encoding="utf-8",
    )


def write_graph_only_panels(
    projected: list[tuple[np.ndarray, np.ndarray]],
) -> list[str]:
    outputs: list[str] = []
    for case, (subject, object_) in zip(CASES, projected, strict=True):
        fig, ax = plt.subplots(figsize=(4.6, 3.8), facecolor="white")
        fig.subplots_adjust(left=0.17, right=0.94, bottom=0.17, top=0.95)
        style_projection(ax, case, subject, object_)

        svg_path = OUT / f"{case['slug']}.svg"
        png_path = OUT / f"{case['slug']}.png"
        save_svg(fig, svg_path)
        fig.savefig(png_path, dpi=300, facecolor="white")
        plt.close(fig)
        outputs.extend((str(svg_path), str(png_path)))
    return outputs


def main() -> None:
    configure_fonts()
    screen_points = extract_screen_points()
    projected = [
        (subject, object_)
        if case.get("sample_source") == "centers_only"
        else (screen_to_data(subject, case), screen_to_data(object_, case))
        for case, (subject, object_) in zip(CASES, screen_points, strict=True)
    ]

    fig = plt.figure(figsize=(14.4, 6.6), facecolor="white")
    grid = fig.add_gridspec(
        3,
        3,
        height_ratios=(0.90, 3.00, 2.10),
        left=0.045,
        right=0.985,
        bottom=0.075,
        top=0.975,
        wspace=0.22,
        hspace=0.17,
    )

    for column, (case, (subject, object_)) in enumerate(zip(CASES, projected, strict=True)):
        validate_case(case, subject, object_)
        add_header(fig.add_subplot(grid[0, column]), case)
        style_projection(fig.add_subplot(grid[1, column]), case, subject, object_)
        add_evidence(fig.add_subplot(grid[2, column]), case)

    for x in (0.347, 0.674):
        fig.add_artist(
            mpl.lines.Line2D([x, x], [0.035, 0.975], transform=fig.transFigure, color="#D4D4D4", linewidth=1.3)
        )

    OUT.mkdir(parents=True, exist_ok=True)
    svg_path = OUT / "qualitative_geometry_panels.svg"
    png_path = OUT / "qualitative_geometry_panels.png"
    save_svg(fig, svg_path)
    fig.savefig(png_path, dpi=200, facecolor="white")
    plt.close(fig)
    graph_only_outputs = write_graph_only_panels(projected)

    print(
        json.dumps(
            {
                "status": "completed",
                "source": str(SOURCE_SVG),
                "source_samples_per_endpoint": 260,
                "outputs": [str(svg_path), str(png_path), *graph_only_outputs],
                "projections": [case["projection"] for case in CASES],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
