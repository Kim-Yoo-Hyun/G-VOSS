#!/usr/bin/env python3
"""Render the label-free XY geometry panel used by the Figure 2 example."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CASE_ROOT = (
    ROOT
    / "archive/local/pre_submission_20260722/previous_archive/experiments"
    / "H001_geom_reliability/pre_submission_20260722/no_family_indicator_v1"
)
CASE_JSON = CASE_ROOT / "candidate_figures/qualitative_cases.json"
SOURCE_SVG = CASE_ROOT / "candidate_figures/figure3_qualitative.svg"

ORANGE = "#D55E00"
BLUE = "#0057B8"
DARK = "#202124"


def configure_fonts() -> None:
    preferred = "Times New Roman"
    try:
        font_manager.findfont(preferred, fallback_to_default=False)
        serif = [preferred]
    except ValueError:
        serif = ["TeX Gyre Termes", "Nimbus Roman", "DejaVu Serif"]
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": serif,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.unicode_minus": False,
        }
    )


def load_case() -> dict:
    cases = json.loads(CASE_JSON.read_text(encoding="utf-8"))
    return next(case for case in cases if case["case_id"] == "open3dsg_case_001")


def source_points(case: dict) -> tuple[np.ndarray, np.ndarray]:
    """Recover source-backed object XY samples from the preserved SVG panel."""
    root = ET.parse(SOURCE_SVG).getroot()
    namespace = {"svg": "http://www.w3.org/2000/svg"}

    subject_screen: list[tuple[float, float]] = []
    object_screen: list[tuple[float, float]] = []
    subject_marker: tuple[float, float] | None = None
    object_marker: tuple[float, float] | None = None

    for circle in root.findall("svg:circle", namespace):
        fill = circle.attrib.get("fill", "").lower()
        opacity = circle.attrib.get("opacity")
        if (
            fill == "#d55e00"
            and opacity == "0.62"
            and float(circle.attrib["cx"]) < 480
        ):
            subject_screen.append(
                (float(circle.attrib["cx"]), float(circle.attrib["cy"]))
            )
        if (
            fill == "#d55e00"
            and circle.attrib.get("stroke", "").lower() == "#ffffff"
            and circle.attrib.get("r") == "4.2"
            and float(circle.attrib["cx"]) < 480
        ):
            subject_marker = (
                float(circle.attrib["cx"]),
                float(circle.attrib["cy"]),
            )

    for rect in root.findall("svg:rect", namespace):
        fill = rect.attrib.get("fill", "").lower()
        opacity = rect.attrib.get("opacity")
        if fill == "#0072b2" and opacity == "0.32" and float(rect.attrib["x"]) < 480:
            object_screen.append(
                (
                    float(rect.attrib["x"]) + float(rect.attrib["width"]) / 2,
                    float(rect.attrib["y"]) + float(rect.attrib["height"]) / 2,
                )
            )
        if (
            fill == "#0072b2"
            and rect.attrib.get("stroke", "").lower() == "#ffffff"
            and rect.attrib.get("width") == "8"
            and float(rect.attrib["x"]) < 480
        ):
            object_marker = (
                float(rect.attrib["x"]) + 4,
                float(rect.attrib["y"]) + 4,
            )

    if subject_marker is None or object_marker is None:
        raise RuntimeError("Could not recover the center markers from the source SVG.")

    subject_xy = np.asarray(case["subject_geometry"]["center"][:2], dtype=float)
    object_xy = np.asarray(case["object_geometry"]["center"][:2], dtype=float)
    subject_marker = np.asarray(subject_marker, dtype=float)
    object_marker = np.asarray(object_marker, dtype=float)

    # The preserved SVG uses an affine screen mapping with an inverted y axis.
    scale_x = (subject_marker[0] - object_marker[0]) / (
        subject_xy[0] - object_xy[0]
    )
    offset_x = subject_marker[0] - scale_x * subject_xy[0]
    scale_y = (subject_marker[1] - object_marker[1]) / (
        object_xy[1] - subject_xy[1]
    )
    offset_y = subject_marker[1] + scale_y * subject_xy[1]

    def invert(points: list[tuple[float, float]]) -> np.ndarray:
        array = np.asarray(points, dtype=float)
        return np.column_stack(
            (
                (array[:, 0] - offset_x) / scale_x,
                (offset_y - array[:, 1]) / scale_y,
            )
        )

    return invert(subject_screen), invert(object_screen)


def main() -> None:
    configure_fonts()
    case = load_case()
    subject_points, object_points = source_points(case)
    subject_xy = np.asarray(case["subject_geometry"]["center"][:2], dtype=float)
    object_xy = np.asarray(case["object_geometry"]["center"][:2], dtype=float)
    distance = float(np.linalg.norm(subject_xy - object_xy))
    expected = float(case["measurements"]["xy_center_distance"])
    if not np.isclose(distance, expected, atol=1e-6):
        raise ValueError(f"distance_mismatch:{distance}:{expected}")

    fig, ax = plt.subplots(figsize=(4.15, 4.5))
    fig.subplots_adjust(left=0.14, right=0.97, bottom=0.12, top=0.97)

    # The compact snapshot preserves pair points but not the full scan points.
    ax.scatter(
        subject_points[:, 0],
        subject_points[:, 1],
        s=2.8,
        c=ORANGE,
        alpha=0.42,
        linewidths=0,
        rasterized=False,
        zorder=1,
    )
    ax.scatter(
        object_points[:, 0],
        object_points[:, 1],
        s=2.8,
        c=BLUE,
        alpha=0.42,
        linewidths=0,
        rasterized=False,
        zorder=1,
    )

    ax.scatter(
        *subject_xy,
        s=55,
        c=ORANGE,
        edgecolors="white",
        linewidths=0.8,
        zorder=5,
    )
    ax.scatter(
        *object_xy,
        s=55,
        c=BLUE,
        marker="o",
        edgecolors="white",
        linewidths=0.8,
        zorder=5,
    )
    ax.plot(
        [subject_xy[0], object_xy[0]],
        [subject_xy[1], object_xy[1]],
        color=BLUE,
        linewidth=1.25,
        linestyle=(0, (5, 3)),
        zorder=4,
    )

    bounds = case["plot_bounds"]
    ax.set_xlim(bounds["x_min"], bounds["x_max"])
    ax.set_ylim(bounds["y_min"], bounds["y_max"])
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([-0.4, 0, 1, 2, 3, 4])
    ax.set_yticks([-3, -2, -1, 0, 1])
    ax.tick_params(axis="both", labelsize=10, width=0.8, length=3)
    for label in (*ax.get_xticklabels(), *ax.get_yticklabels()):
        label.set_fontname("Times New Roman")
        label.set_fontsize(10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.9)
    ax.spines["bottom"].set_linewidth(0.9)
    ax.plot(
        1,
        0,
        marker=">",
        markersize=5,
        color="black",
        transform=ax.transAxes,
        clip_on=False,
    )
    ax.plot(
        0,
        1,
        marker="^",
        markersize=5,
        color="black",
        transform=ax.transAxes,
        clip_on=False,
    )
    ax.text(
        0.985,
        0.02,
        "x",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=12,
        fontname="Times New Roman",
        fontstyle="italic",
        color=DARK,
    )
    ax.text(
        0.02,
        0.985,
        "y",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=12,
        fontname="Times New Roman",
        fontstyle="italic",
        color=DARK,
    )
    ax.set_xlabel("")
    ax.set_ylabel("")

    for suffix in ("svg", "pdf"):
        fig.savefig(
            OUT / f"Figure2_xy.{suffix}",
            facecolor="white",
            metadata={"Creator": "RelCompat3D label-free XY renderer"},
        )
    fig.savefig(
        OUT / "Figure2_xy.png",
        dpi=300,
        facecolor="white",
    )
    plt.close(fig)

    print(
        json.dumps(
            {
                "status": "completed",
                "distance_m": distance,
                "subject_points": int(len(subject_points)),
                "object_points": int(len(object_points)),
                "outputs": [
                    str(OUT / "Figure2_xy.svg"),
                    str(OUT / "Figure2_xy.pdf"),
                    str(OUT / "Figure2_xy.png"),
                ],
                "scope": "pair-point reconstruction; full scan points unavailable",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
