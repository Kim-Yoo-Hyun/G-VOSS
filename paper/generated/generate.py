from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D


# ============================================================
# 1. Font and PDF settings
# ============================================================

FONT_NAME = "Times New Roman"

try:
    font_manager.findfont(FONT_NAME, fallback_to_default=False)
except ValueError as exc:
    raise RuntimeError(
        "Times New Roman이 설치되어 있지 않습니다. "
        "해당 폰트가 설치된 환경에서 실행하세요."
    ) from exc

mpl.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": [FONT_NAME],

        # PDF에서 TrueType font로 embed
        "pdf.fonttype": 42,
        "ps.fonttype": 42,

        # SVG에서 text를 path로 변환하지 않음
        "svg.fonttype": "none",

        "axes.unicode_minus": False,
    }
)


# ============================================================
# 2. Data
# ============================================================

K_VALUES = [5, 10, 20, 50, 100]

data = {
    "VL-SAT": {
        "Source": [
            (41.94, 0.29),
            (63.22, 0.82),
            (80.74, 1.42),
            (92.72, 2.68),
            (96.35, 4.76),
        ],
        "RelCompat3D-Linear": [
            (42.07, 0.15),
            (63.39, 0.57),
            (80.82, 1.14),
            (92.77, 1.97),
            (96.58, 2.95),
        ],
        "RelCompat3D-MLP": [
            (42.09, 0.15),
            (63.47, 0.51),
            (80.92, 1.09),
            (92.72, 1.89),
            (96.50, 2.96),
        ],
        "xlim": (36, 100),
        "ylim": (0, 6),
        "xticks": [40, 60, 80, 100],
        "yticks": [0, 1, 2, 3, 4, 5, 6],
    },

    "Open3DSG": {
        "Source": [
            (3.42, 52.05),
            (9.87, 32.89),
            (19.89, 20.99),
            (40.43, 13.87),
            (51.11, 12.42),
        ],
        "RelCompat3D-Linear": [
            (3.73, 0.94),
            (11.38, 2.33),
            (23.62, 3.13),
            (44.18, 3.42),
            (56.85, 3.24),
        ],
        "RelCompat3D-MLP": [
            (3.70, 4.95),
            (11.78, 4.97),
            (24.67, 4.56),
            (46.70, 4.13),
            (59.89, 3.71),
        ],
        "xlim": (0, 70),
        "ylim": (0, 70),
        "xticks": [0, 20, 40, 60],
        "yticks": [0, 20, 40, 60],
    },

    "SGFN": {
        "Source": [
            (31.17, 2.37),
            (39.75, 3.49),
            (49.12, 3.22),
            (74.02, 3.85),
            (92.35, 6.30),
        ],
        "RelCompat3D-Linear": [
            (31.17, 2.37),
            (39.75, 3.47),
            (49.14, 2.97),
            (74.50, 2.63),
            (93.03, 3.50),
        ],
        "RelCompat3D-MLP": [
            (31.17, 2.37),
            (39.75, 3.47),
            (49.19, 2.96),
            (74.57, 2.58),
            (92.88, 3.50),
        ],
        "xlim": (20, 100),
        "ylim": (0, 10),
        "xticks": [20, 40, 60, 80, 100],
        "yticks": [0, 2, 4, 6, 8, 10],
    },
}


# ============================================================
# 3. Style
# ============================================================

SOURCE_COLOR = "#808080"
LINEAR_COLOR = "#119C99"
MLP_COLOR = "#7647D8"

styles = {
    "Source": {
        "color": SOURCE_COLOR,
        "linestyle": (0, (4, 3)),
        "marker": "o",
    },
    "RelCompat3D-Linear": {
        "color": LINEAR_COLOR,
        "linestyle": "-",
        "marker": "s",
    },
    "RelCompat3D-MLP": {
        "color": MLP_COLOR,
        "linestyle": "-",
        "marker": "^",
    },
}


# K-label 위치: 단위는 화면상의 point offset
label_offsets = {
    "VL-SAT": {
        5: (2, 5),
        10: (2, 5),
        20: (2, 5),
        50: (-9, 5),
        100: (-18, 5),
    },
    "Open3DSG": {
        5: (2, 5),
        10: (2, 5),
        20: (2, 5),
        50: (2, 5),
        100: (2, 5),
    },
    "SGFN": {
        5: (-9, 5),
        10: (-8, 5),
        20: (4, 5),
        50: (-8, 5),
        100: (-18, 5),
    },
}


# ============================================================
# 4. Draw figure
# ============================================================

fig, axes = plt.subplots(
    nrows=1,
    ncols=3,
    figsize=(6.9, 2.4),
)

# 직접 여백 설정: bbox_inches="tight"에 의존하지 않음
fig.subplots_adjust(
    left=0.075,
    right=0.985,
    bottom=0.235,
    top=0.745,
    wspace=0.31,
)

panel_letters = ["(a)", "(b)", "(c)"]

for panel_index, (ax, panel_name) in enumerate(zip(axes, data.keys())):
    panel = data[panel_name]

    ax.set_xlim(*panel["xlim"])
    ax.set_ylim(*panel["ylim"])
    ax.set_xticks(panel["xticks"])
    ax.set_yticks(panel["yticks"])

    ax.set_title(
        f"{panel_letters[panel_index]} {panel_name}",
        loc="left",
        fontsize=11.5,
        fontweight="bold",
        pad=9,
    )

    ax.set_xlabel(
        "Recall@K (%)",
        fontsize=10,
        labelpad=5,
    )

    if panel_index == 0:
        ax.set_ylabel(
            "Violation@K (%) ↓",
            fontsize=10,
            labelpad=5,
        )

    ax.tick_params(
        axis="both",
        which="major",
        labelsize=9,
        width=0.7,
        length=3,
        pad=2,
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(0.7)
    ax.spines["bottom"].set_linewidth(0.7)

    # Curve 순서: Source → Linear → MLP
    for method_name in [
        "Source",
        "RelCompat3D-Linear",
        "RelCompat3D-MLP",
    ]:
        points = panel[method_name]
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]

        style = styles[method_name]

        ax.plot(
            xs,
            ys,
            color=style["color"],
            linestyle=style["linestyle"],
            marker=style["marker"],
            linewidth=1.0,
            markersize=5.0,
            markerfacecolor=style["color"],
            markeredgecolor=style["color"],
            markeredgewidth=0.7,
            zorder=2 if method_name == "Source" else 3,
        )

    # Source marker에만 K label 표시
    for k_value, point in zip(K_VALUES, panel["Source"]):
        x_value, y_value = point
        offset_x, offset_y = label_offsets[panel_name][k_value]

        ax.annotate(
            str(k_value),
            xy=(x_value, y_value),
            xytext=(offset_x, offset_y),
            textcoords="offset points",
            fontsize=9,
            color="black",
            ha="left",
            va="bottom",
        )


# ============================================================
# 5. Figure-level legend
# ============================================================

legend_handles = [
    Line2D(
        [0],
        [0],
        color=SOURCE_COLOR,
        linestyle=(0, (4, 3)),
        marker="o",
        linewidth=1,
        markersize=5,
        label="Source",
    ),
    Line2D(
        [0],
        [0],
        color=LINEAR_COLOR,
        linestyle="-",
        marker="s",
        linewidth=1,
        markersize=5,
        label="RelCompat3D-Linear",
    ),
    Line2D(
        [0],
        [0],
        color=MLP_COLOR,
        linestyle="-",
        marker="^",
        linewidth=1,
        markersize=5,
        label="RelCompat3D-MLP",
    ),
]

fig.legend(
    handles=legend_handles,

    # Figure 상단에 가로 한 줄로 배치
    loc="upper center",
    # bbox_to_anchor=(0.68, 0.995),
    bbox_to_anchor=(0.74, 0.955),

    ncol=3,
    frameon=False,
    fontsize=9.5,

    # legend를 조밀하게 구성
    handlelength=1.45,
    handletextpad=0.35,
    columnspacing=0.75,
    labelspacing=0.0,
    borderaxespad=0.0,
    borderpad=0.0,

    markerscale=1.0,
)


# ============================================================
# 6. Save
# ============================================================

output_dir = Path("/home/yoohyun/research/paper/generated")
output_dir.mkdir(parents=True, exist_ok=True)

pdf_path = output_dir / "Figure3.pdf"
svg_path = output_dir / "Figure3.svg"

fig.savefig(
    pdf_path,
    format="pdf",
    facecolor="white",
)

fig.savefig(
    svg_path,
    format="svg",
    facecolor="white",
)

plt.close(fig)

print(f"Saved: {pdf_path}")
print(f"Saved: {svg_path}")