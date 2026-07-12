#!/usr/bin/env python3
"""Build claim-safe H002 paper figures and supplementary tables."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


BLUE = "#2C6EBA"
GREEN = "#2E8B57"
ORANGE = "#D97706"
RED = "#B33A3A"
PURPLE = "#6F4BA8"
GRAY = "#5B6573"
LIGHT = "#E7EBF0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--paper-root", type=Path, required=True)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ci_pair(text: str) -> tuple[float, float]:
    cleaned = text.strip().strip("[]")
    low, high = cleaned.split(",")
    return float(low), float(high)


def fmt_ci(point: float, low: float, high: float) -> str:
    return f"{point:+.3f} [{low:+.3f}, {high:+.3f}]"


def tex_escape(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(char, char) for char in text)


def source_name(source_id: str) -> str:
    return "Open3DSG" if source_id.startswith("open3dsg") else "VL-SAT"


def configure_plotting() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.titlesize": 8.5,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def build_method_overview(out: Path) -> None:
    """Build the claim-safe, paper-width H002 overview diagram."""

    fig, ax = plt.subplots(figsize=(7.15, 3.25))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")

    stages = [
        {
            "x": 0.015,
            "title": "1  Source",
            "edge": BLUE,
            "fill": "#EEF5FC",
            "lines": [
                "VL-SAT / Open3DSG",
                r"edge $e=(s,p,o)$",
                r"$Z_e$: score + rank",
            ],
        },
        {
            "x": 0.210,
            "title": "2  Evidence",
            "edge": ORANGE,
            "fill": "#FFF7E8",
            "lines": [
                r"$T_e$: predicate, classes",
                r"$G_e$: pair geometry",
                r"$\Delta z$, size, offset, gap",
                r"$Z_e \notin C_e$",
            ],
        },
        {
            "x": 0.405,
            "title": "3  Compatibility",
            "edge": GREEN,
            "fill": "#EEF8F2",
            "lines": [
                r"$C_e^{raw}=f_\theta(T_e,G_e)$",
                r"explicit $T_e\!\times\!G_e$ terms",
                "train-only logistic model",
                "counterfactual controls",
            ],
        },
        {
            "x": 0.600,
            "title": "4  Reranking",
            "edge": PURPLE,
            "fill": "#F5F0FA",
            "lines": [
                r"$\widetilde Z_e$: per source",
                r"$\widetilde C_e$: per source-family",
                r"$S_{comp}=\widetilde Z_e\widetilde C_e$",
                r"baseline: $S_{src}=Z_e$",
            ],
        },
        {
            "x": 0.795,
            "title": "5  Evaluation",
            "edge": RED,
            "fill": "#FCF0F0",
            "lines": [
                "3DSSG validation",
                r"Recall@$K$ $\uparrow$",
                r"Violation@$K$ $\downarrow$",
                "grouped bootstrap CI",
            ],
        },
    ]

    width = 0.175
    y = 0.33
    height = 0.51
    for index, stage in enumerate(stages):
        box = FancyBboxPatch(
            (stage["x"], y),
            width,
            height,
            boxstyle="round,pad=0.006,rounding_size=0.012",
            linewidth=1.1,
            edgecolor=stage["edge"],
            facecolor=stage["fill"],
        )
        ax.add_patch(box)
        ax.add_patch(
            Rectangle(
                (stage["x"], y + height - 0.105),
                width,
                0.105,
                linewidth=0,
                facecolor=stage["edge"],
                alpha=0.13,
            )
        )
        ax.text(
            stage["x"] + width / 2,
            y + height - 0.052,
            stage["title"],
            ha="center",
            va="center",
            fontsize=9.0,
            weight="bold",
            color="#17212B",
        )
        ax.text(
            stage["x"] + width / 2,
            y + height - 0.155,
            "\n".join(stage["lines"]),
            ha="center",
            va="top",
            fontsize=7.7,
            linespacing=1.43,
            color="#24313D",
        )
        if index < len(stages) - 1:
            x0 = stage["x"] + width + 0.004
            x1 = stages[index + 1]["x"] - 0.004
            ax.add_patch(
                FancyArrowPatch(
                    (x0, y + height / 2),
                    (x1, y + height / 2),
                    arrowstyle="-|>",
                    mutation_scale=9,
                    linewidth=1.0,
                    color="#53606C",
                )
            )

    ax.add_patch(
        FancyArrowPatch(
            (0.100, 0.895),
            (0.685, 0.895),
            connectionstyle="arc3,rad=0.0",
            arrowstyle="-|>",
            mutation_scale=9,
            linewidth=1.0,
            linestyle="--",
            color=GRAY,
        )
    )
    ax.text(
        0.39,
        0.950,
        r"$Z_e$ bypasses compatibility and enters only at reranking",
        ha="center",
        va="center",
        fontsize=8.4,
        color="#36424D",
    )

    route_y = 0.035
    route_h = 0.205
    route_specs = [
        (0.015, 0.230, GREEN, "Validated", "higher/lower\nbigger/smaller"),
        (0.250, 0.210, ORANGE, "Qualified", "left/right\nsource-dependent"),
        (0.465, 0.260, BLUE, "Control + failure", "close by; front/behind\nsupport/contact"),
        (0.730, 0.255, GRAY, "Not claimed", "hidden test; all-family\ncalibrated abstention"),
    ]
    for x, w, edge, title, body in route_specs:
        box = FancyBboxPatch(
            (x, route_y),
            w,
            route_h,
            boxstyle="round,pad=0.006,rounding_size=0.01",
            linewidth=0.9,
            edgecolor=edge,
            facecolor="white",
        )
        ax.add_patch(box)
        ax.text(x + 0.012, route_y + route_h - 0.048, title, fontsize=8.3, weight="bold", color=edge, va="top")
        ax.text(x + 0.012, route_y + route_h - 0.105, body, fontsize=7.2, color="#303A44", va="top", linespacing=1.2)

    ax.text(0.015, 0.276, "Route-specific evidence status", fontsize=9.0, weight="bold", color="#17212B")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.985, bottom=0.01)
    fig.savefig(out, bbox_inches="tight", pad_inches=0.02, facecolor="white")
    plt.close(fig)


def build_tradeoff_figure(main_rows: list[dict[str, str]], out: Path) -> None:
    rows = [row for row in main_rows if row["table_section"] == "main_core"]
    rows.sort(key=lambda row: int(row["K"]))
    ks = [int(row["K"]) for row in rows]
    recall = [float(row["Delta_Recall@K"]) for row in rows]
    violation = [float(row["Delta_Violation@K"]) for row in rows]
    recall_ci = [ci_pair(row["Delta_Recall_CI95"]) for row in rows]
    violation_ci = [ci_pair(row["Delta_Violation_CI95"]) for row in rows]

    fig, axes = plt.subplots(2, 1, figsize=(3.28, 3.15), sharex=True)
    for ax, values, cis, color, ylabel in [
        (axes[0], recall, recall_ci, BLUE, r"$\Delta$ Recall@K"),
        (axes[1], violation, violation_ci, GREEN, r"$\Delta$ Violation@K"),
    ]:
        lower = [value - low for value, (low, _) in zip(values, cis)]
        upper = [high - value for value, (_, high) in zip(values, cis)]
        ax.errorbar(
            ks,
            values,
            yerr=[lower, upper],
            color=color,
            marker="o",
            markersize=4,
            linewidth=1.4,
            capsize=2.5,
            label=r"$S_{comp}-S_{src}$",
        )
        ax.axhline(0.0, color=GRAY, linewidth=0.7, linestyle="--")
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", color=LIGHT, linewidth=0.7)
        ax.legend(loc="best", frameon=False)
    axes[0].set_title("Comparison route: bootstrap 95% CI")
    axes[1].set_xlabel("K")
    axes[1].set_xticks(ks)
    axes[0].text(0.98, 0.06, "higher is better", transform=axes[0].transAxes, ha="right", color=GRAY, fontsize=6.5)
    axes[1].text(0.98, 0.06, "lower is better", transform=axes[1].transAxes, ha="right", color=GRAY, fontsize=6.5)
    fig.tight_layout(pad=0.55, h_pad=0.35)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def add_case_panel(ax, x: float, y: float, width: float, height: float, title: str, lines: list[str], color: str) -> None:
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.012",
        linewidth=1.0,
        edgecolor=color,
        facecolor="white",
    )
    ax.add_patch(box)
    ax.text(x + 0.02, y + height - 0.055, title, color=color, weight="bold", fontsize=8, va="top")
    ax.text(x + 0.02, y + height - 0.115, "\n".join(lines), color="#1F2933", fontsize=7, va="top", linespacing=1.35)


def build_qualitative_figure(cases: list[dict[str, str]], out: Path) -> None:
    by_id = {row["case_id"]: row for row in cases}
    selected = [
        (
            "Source violation filtered",
            by_id["comparison_source_violation_filtered_by_scomp"],
            RED,
            "Filtered from $S_{comp}$ top-20",
        ),
        (
            "GT relation promoted",
            by_id["comparison_gt_match_promoted_by_scomp"],
            GREEN,
            "Promoted into $S_{comp}$ top-20",
        ),
        (
            "Lateral violation filtered",
            by_id["left_right_source_violation_filtered_by_frame_route"],
            ORANGE,
            "Filtered by frame-aware route",
        ),
    ]

    fig, ax = plt.subplots(figsize=(7.0, 2.55))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.01, 0.97, "Actual validation rows used in the qualitative audit", fontsize=9, weight="bold", va="top")
    for index, (title, row, color, outcome) in enumerate(selected):
        x = 0.01 + index * 0.33
        score = float(row["score"])
        candidate_suffix = row["candidate_id"].split(":")[-3:]
        candidate_short = ":".join(candidate_suffix)
        lines = [
            f"Source: {source_name(row['source_id'])}",
            f"Predicate: {row['predicate_label']}",
            f"Observed score/rank: {score:.3f} / {row['rank']}",
            f"GT match: {row['gt_exact_match']}",
            f"Geometry: {row['violation_status']}",
            f"Row: {candidate_short}",
            "",
            outcome,
        ]
        add_case_panel(ax, x, 0.08, 0.31, 0.78, title, lines, color)
    fig.tight_layout(pad=0.4)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def build_failure_figure(
    appendix_rows: list[dict[str, str]],
    support_summary: dict,
    support_probes: list[dict[str, str]],
    out: Path,
) -> None:
    front_rows = [row for row in appendix_rows if row["route"] == "frame_depth_ambiguity" and int(row["K"]) in {20, 50}]
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.75), gridspec_kw={"width_ratios": [1.35, 0.8, 0.82]})

    ax = axes[0]
    markers = {20: "o", 50: "s"}
    colors = {"Open3DSG": BLUE, "VL-SAT": ORANGE}
    for row in front_rows:
        source = source_name(row["source_scope"])
        k = int(row["K"])
        ax.scatter(
            float(row["Delta_Recall@K"]),
            float(row["Delta_Violation@K"]),
            s=48,
            marker=markers[k],
            color=colors[source],
            edgecolor="white",
            linewidth=0.7,
        )
        ax.annotate(f"{source}, K={k}", (float(row["Delta_Recall@K"]), float(row["Delta_Violation@K"])), xytext=(4, 3), textcoords="offset points", fontsize=6.5)
    ax.axvline(0.0, color=GRAY, linestyle="--", linewidth=0.7)
    ax.axhline(0.0, color=GRAY, linestyle="--", linewidth=0.7)
    ax.set_xlabel(r"$\Delta$ Recall@K")
    ax.set_ylabel(r"$\Delta$ Violation@K")
    ax.set_title("(a) front/behind: lower violation, lost recall")
    ax.grid(color=LIGHT, linewidth=0.7)

    counts = support_summary["row_counts"]["binary_counts"]
    positives = int(counts["1"])
    negatives = int(counts["0"])
    ax = axes[1]
    bars = ax.bar(["accept", "reject"], [positives, negatives], color=[GREEN, RED], width=0.6)
    for bar, value in zip(bars, [positives, negatives]):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 7, str(value), ha="center", fontsize=8, weight="bold")
    ax.set_ylim(0, max(negatives * 1.23, 380))
    ax.set_ylabel("Binary target rows")
    ax.set_title("(b) target imbalance")
    ax.grid(axis="y", color=LIGHT, linewidth=0.7)
    geometry_rule = next(row for row in support_probes if row["target"] == "binary" and row["probe"] == "geometry_rule_state")
    majority = negatives / (positives + negatives)

    ax = axes[2]
    ax.axis("off")
    ax.set_title("(c) independence gate")
    ax.text(0.02, 0.80, "Majority baseline", fontsize=7, color=GRAY)
    ax.text(0.02, 0.69, f"{majority:.3f}", fontsize=15, weight="bold", color=RED)
    ax.text(0.02, 0.50, "geometry_rule_state", fontsize=7, color=GRAY)
    ax.text(0.02, 0.39, f"{float(geometry_rule['leave_one_out_accuracy']):.3f} acc. / {float(geometry_rule['leave_one_out_macro_recall']):.3f} macro", fontsize=9, weight="bold", color=PURPLE)
    ax.text(0.02, 0.19, "Circular proxy target", fontsize=8, weight="bold", color=RED)
    ax.text(0.02, 0.09, "Metric rerun blocked", fontsize=7.5, color="#1F2933")
    fig.tight_layout(pad=0.7, w_pad=1.1)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def build_counterfactual_table(ci_rows: list[dict[str, str]]) -> str:
    wanted = {
        "S2_source_x_Ce_minus_S0_source_score": "Source score",
        "S2_source_x_Ce_minus_A1_source_x_G_only": "Geometry-only",
        "S2_source_x_Ce_minus_A2_source_x_TG_concat": "Plain concat.",
        "S2_source_x_Ce_minus_C1_source_x_shuffled_Ce": "Shuffled $C_e$",
        "S2_source_x_Ce_minus_C2_source_x_wrong_T_Ce": "Wrong-$T_e$",
    }
    indexed: dict[tuple[str, str], dict[str, str]] = {}
    for row in ci_rows:
        if int(row["K"]) == 20 and row["comparison"] in wanted:
            indexed[(row["comparison"], row["metric"])] = row
    lines = []
    for comparison, label in wanted.items():
        recall = indexed[(comparison, "Recall@K")]
        violation = indexed[(comparison, "Violation@K")]
        lines.append(
            f"{label} & {fmt_ci(float(recall['point_delta']), float(recall['ci_low_95']), float(recall['ci_high_95']))} & "
            f"{fmt_ci(float(violation['point_delta']), float(violation['ci_low_95']), float(violation['ci_high_95']))} \\\\"
        )
    return "\n".join(lines)


def build_main_grid_table(main_rows: list[dict[str, str]]) -> str:
    rows = [row for row in main_rows if row["table_section"] == "main_core"]
    rows.sort(key=lambda row: int(row["K"]))
    lines = []
    for row in rows:
        recall_low, recall_high = ci_pair(row["Delta_Recall_CI95"])
        violation_low, violation_high = ci_pair(row["Delta_Violation_CI95"])
        lines.append(
            f"{row['K']} & {fmt_ci(float(row['Delta_Recall@K']), recall_low, recall_high)} & "
            f"{fmt_ci(float(row['Delta_Violation@K']), violation_low, violation_high)} \\\\"
        )
    return "\n".join(lines)


def build_family_table(family_rows: list[dict[str, str]]) -> str:
    rows = [
        row
        for row in family_rows
        if row["comparison"] == "S2_source_x_Ce_minus_S0_source_score" and int(row["K"]) in {20, 50}
    ]
    indexed = {(row["source_id"], row["route_family"], int(row["K"]), row["metric"]): row for row in rows}
    lines = []
    sources = ["open3dsg_recovery_relaxed_views_min2", "vlsat_full_validation"]
    families = ["relative_vertical", "size_relative"]
    for source in sources:
        for family in families:
            for k in [20, 50]:
                recall = indexed[(source, family, k, "Recall@K")]
                violation = indexed[(source, family, k, "Violation@K")]
                lines.append(
                    f"{source_name(source)} & {tex_escape(family.replace('_', ' '))} & {k} & "
                    f"{fmt_ci(float(recall['point_delta']), float(recall['ci_low_95']), float(recall['ci_high_95']))} & "
                    f"{fmt_ci(float(violation['point_delta']), float(violation['ci_low_95']), float(violation['ci_high_95']))} \\\\"
                )
    return "\n".join(lines)


def build_normalization_table(rows: list[dict[str, str]]) -> str:
    labels = {
        "normalization_sensitivity_raw_product": "Raw product",
        "normalization_sensitivity_rank_percentile": "Rank percentile",
    }
    selected = [row for row in rows if int(row["K"]) in {10, 20, 50} and row["baseline_role"] in labels]
    selected.sort(key=lambda row: (labels[row["baseline_role"]], int(row["K"])))
    lines = []
    for row in selected:
        lines.append(
            f"{labels[row['baseline_role']]} & {row['K']} & {float(row['delta_Recall@K']):+.3f} & {float(row['delta_Violation@K']):+.3f} \\\\"
        )
    return "\n".join(lines)


def build_support_table(summary: dict, probes: list[dict[str, str]]) -> str:
    counts = summary["row_counts"]["binary_counts"]
    positives = int(counts["1"])
    negatives = int(counts["0"])
    majority = negatives / (positives + negatives)
    probe_labels = {
        "predicate_x_class_pair": r"predicate $\times$ class pair",
        "geometry_rule_state": "geometry rule state",
        "geometry_core_signature": "geometry core signature",
    }
    selected = [row for row in probes if row["target"] == "binary" and row["probe"] in probe_labels]
    lines = [
        f"Target composition & {positives} accept / {negatives} reject & {majority:.3f} majority & -- \\\\"
    ]
    for row in selected:
        lines.append(
            f"{probe_labels[row['probe']]} & {row['rows']} rows & {float(row['leave_one_out_accuracy']):.3f} LOO acc. & {float(row['leave_one_out_macro_recall']):.3f} macro recall \\\\"
        )
    return "\n".join(lines)


def write_appendix_tables(
    path: Path,
    main_rows: list[dict[str, str]],
    ci_rows: list[dict[str, str]],
    family_rows: list[dict[str, str]],
    sensitivity_rows: list[dict[str, str]],
    support_summary: dict,
    support_probes: list[dict[str, str]],
) -> None:
    content = rf"""
\noindent
\begin{{minipage}}[t]{{0.48\textwidth}}
\centering
\small
\setlength{{\tabcolsep}}{{4pt}}
\begin{{tabular}}{{rcc}}
\toprule
K & $\Delta$Recall@K (95\% CI) & $\Delta$Violation@K (95\% CI) \\
\midrule
{build_main_grid_table(main_rows)}
\bottomrule
\end{{tabular}}
\captionof{{table}}{{Full validation comparison-route grid for $S_{{\mathrm{{comp}}}}-S_{{\mathrm{{src}}}}$. The route contains higher/lower and bigger/smaller only; Violation@K is custom and this is not a hidden-test benchmark.}}
\label{{tab:supp-main-grid}}
\end{{minipage}}
\hfill
\begin{{minipage}}[t]{{0.48\textwidth}}
\centering
\small
\setlength{{\tabcolsep}}{{5pt}}
\begin{{tabular}}{{lrrr}}
\toprule
Variant & K & Main $-$ variant $\Delta$R & $\Delta$V \\
\midrule
{build_normalization_table(sensitivity_rows)}
\bottomrule
\end{{tabular}}
\captionof{{table}}{{Normalization sensitivity. Positive $\Delta$R means the frozen min--max score has higher recall; positive $\Delta$V means it has higher violation and is worse on that axis. We do not claim normalization invariance.}}
\label{{tab:supp-normalization}}
\end{{minipage}}

\vspace{{8pt}}
\begin{{center}}
\centering
\small
\setlength{{\tabcolsep}}{{5pt}}
\begin{{tabular}}{{lcc}}
\toprule
Reference/control at $K=20$ & $\Delta$Recall@20 (95\% CI) & $\Delta$Violation@20 (95\% CI) \\
\midrule
{build_counterfactual_table(ci_rows)}
\bottomrule
\end{{tabular}}
\captionof{{table}}{{Counterfactual and mechanism controls on the validation comparison route. Deltas are $S_{{\mathrm{{comp}}}}$ minus the named row. Matched compatibility outperforms source, geometry-only, plain concatenation, shuffled-$C_e$, and wrong-predicate controls.}}
\label{{tab:supp-controls}}
\end{{center}}

\vspace{{5pt}}
\begin{{center}}
\centering
\scriptsize
\setlength{{\tabcolsep}}{{3.5pt}}
\begin{{tabular}}{{llrcc}}
\toprule
Source & Family & K & $\Delta$Recall@K (95\% CI) & $\Delta$Violation@K (95\% CI) \\
\midrule
{build_family_table(family_rows)}
\bottomrule
\end{{tabular}}
\captionof{{table}}{{Source/family-wise bootstrap intervals for $S_{{\mathrm{{comp}}}}-S_{{\mathrm{{src}}}}$. The table exposes heterogeneous cells rather than treating the aggregate as uniform improvement.}}
\label{{tab:supp-family-ci}}
\end{{center}}

\vspace{{5pt}}
\begin{{center}}
\centering
\small
\setlength{{\tabcolsep}}{{5pt}}
\begin{{tabular}}{{llll}}
\toprule
Audit item & Data & Accuracy/statistic & Balanced statistic \\
\midrule
{build_support_table(support_summary, support_probes)}
\bottomrule
\end{{tabular}}
\captionof{{table}}{{Support/contact target-independence audit. Only 35 binary positives remain, the majority baseline is 0.908, and the geometry-rule construction field reconstructs the target with 1.0 leave-one-out accuracy and macro recall. This circularity blocks training, metric reruns, and solved-route wording.}}
\label{{tab:supp-support-audit}}
\end{{center}}
""".strip() + "\n"
    path.write_text(content, encoding="utf-8")


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out = args.out.resolve()
    paper_root = args.paper_root.resolve()
    out.mkdir(parents=True, exist_ok=True)
    figure_out = out / "figures"
    table_out = out / "tables"
    figure_out.mkdir(exist_ok=True)
    table_out.mkdir(exist_ok=True)
    (paper_root / "figures").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)

    input_paths = {
        "main_table": repo_root / "experiments/H002_compatibility_routing/main_validation_table_refresh/latest/main_table.csv",
        "appendix_table": repo_root / "experiments/H002_compatibility_routing/main_validation_table_refresh/latest/appendix_table.csv",
        "qualitative_cases": repo_root / "experiments/H002_compatibility_routing/qualitative_evidence_package/latest/qualitative_cases.csv",
        "main_ci": repo_root / "experiments/H002_compatibility_routing/source_reranking_ci/latest/main_reranking_delta_ci.csv",
        "family_ci": repo_root / "experiments/H002_compatibility_routing/source_reranking_ci/latest/familywise_reranking_delta_ci.csv",
        "sensitivity": repo_root / "experiments/H002_compatibility_routing/source_reranking_sensitivity/latest/comparison_metrics.csv",
        "support_summary": repo_root / "experiments/H002_compatibility_routing/support_contact_independent_target_repair_shortcut_audit/latest/summary.json",
        "support_probes": repo_root / "experiments/H002_compatibility_routing/support_contact_independent_target_repair_shortcut_audit/latest/shortcut_probe_table.csv",
    }
    missing = [str(path) for path in input_paths.values() if not path.is_file()]
    validation_errors: list[dict[str, str]] = []
    if missing:
        validation_errors.append({"error": "missing_input", "paths": ";".join(missing)})
        (out / "validation_errors.jsonl").write_text("\n".join(json.dumps(row) for row in validation_errors) + "\n", encoding="utf-8")
        raise SystemExit(f"Missing inputs: {missing}")

    configure_plotting()
    main_rows = read_csv(input_paths["main_table"])
    appendix_rows = read_csv(input_paths["appendix_table"])
    qualitative_cases = read_csv(input_paths["qualitative_cases"])
    ci_rows = read_csv(input_paths["main_ci"])
    family_rows = read_csv(input_paths["family_ci"])
    sensitivity_rows = read_csv(input_paths["sensitivity"])
    support_summary = read_json(input_paths["support_summary"])
    support_probes = read_csv(input_paths["support_probes"])

    binary_counts = support_summary["row_counts"]["binary_counts"]
    if int(binary_counts["1"]) != 35 or int(binary_counts["0"]) != 347:
        validation_errors.append({"error": "support_count_drift", "counts": json.dumps(binary_counts, sort_keys=True)})
    geometry_rule = next((row for row in support_probes if row["target"] == "binary" and row["probe"] == "geometry_rule_state"), None)
    if geometry_rule is None:
        validation_errors.append({"error": "missing_geometry_rule_probe"})
    elif not (
        math.isclose(float(geometry_rule["leave_one_out_accuracy"]), 1.0)
        and math.isclose(float(geometry_rule["leave_one_out_macro_recall"]), 1.0)
    ):
        validation_errors.append({"error": "geometry_rule_probe_drift"})

    overview_path = figure_out / "method_overview.pdf"
    tradeoff_path = figure_out / "comparison_tradeoff_ci.pdf"
    qualitative_path = figure_out / "qualitative_reranking_rows.pdf"
    failure_path = figure_out / "failure_routes.pdf"
    table_path = table_out / "appendix_tables.tex"
    build_method_overview(overview_path)
    build_tradeoff_figure(main_rows, tradeoff_path)
    build_qualitative_figure(qualitative_cases, qualitative_path)
    build_failure_figure(appendix_rows, support_summary, support_probes, failure_path)
    write_appendix_tables(table_path, main_rows, ci_rows, family_rows, sensitivity_rows, support_summary, support_probes)

    generated = [overview_path, tradeoff_path, qualitative_path, failure_path, table_path]
    for path in [overview_path, tradeoff_path, qualitative_path, failure_path]:
        shutil.copy2(path, paper_root / "figures" / path.name)
    shutil.copy2(table_path, paper_root / "tables" / table_path.name)

    paper_files = [paper_root / "main.tex", paper_root / "supplement.tex"]
    normalized_paper = " ".join("\n".join(path.read_text(encoding="utf-8") for path in paper_files).split())
    required_claim_boundaries = [
        "We do not solve reliable 3D relation estimation across all relation families",
        "calibrated selective reliability is left for future validation.",
        "learned geometry variant is not part of the primary score",
        "Target circularity prevents an independent support/contact evaluation.",
        "The experiment is a validation-split study",
    ]
    forbidden_positive_claims = [
        "We solve reliable 3D relation estimation across all relation families.",
        "Support/contact is a validated route.",
        "Support/contact is solved.",
        "calibrated selective reliability is solved.",
        "learned $\\Ge$ is the primary score.",
        "This is an official hidden-test result.",
    ]
    missing_boundaries = [text for text in required_claim_boundaries if text not in normalized_paper]
    forbidden_hits = [text for text in forbidden_positive_claims if text in normalized_paper]
    if missing_boundaries:
        validation_errors.append({"error": "missing_claim_boundary", "values": " || ".join(missing_boundaries)})
    if forbidden_hits:
        validation_errors.append({"error": "forbidden_positive_claim", "values": " || ".join(forbidden_hits)})
    claim_audit_path = out / "claim_audit.json"
    claim_audit_path.write_text(
        json.dumps(
            {
                "status": "pass" if not missing_boundaries and not forbidden_hits else "fail",
                "paper_files": [str(path.relative_to(repo_root)) for path in paper_files],
                "required_boundaries": {text: text in normalized_paper for text in required_claim_boundaries},
                "forbidden_positive_claims": {text: text in normalized_paper for text in forbidden_positive_claims},
                "missing_boundaries": missing_boundaries,
                "forbidden_hits": forbidden_hits,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    generated.append(claim_audit_path)
    for path in generated:
        if not path.is_file() or path.stat().st_size == 0:
            validation_errors.append({"error": "empty_output", "path": str(path)})

    manifest = {
        "schema_version": "h002_paper_strengthening_assets_v1",
        "status": "ready" if not validation_errors else "failed_validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "split": "official_3DSSG_validation",
            "hidden_test_claim": False,
            "support_contact_solved": False,
            "pobs_prel_solved": False,
            "learned_Ge_promoted": False,
        },
        "support_contact": {
            "binary_accept": int(binary_counts["1"]),
            "binary_reject": int(binary_counts["0"]),
            "majority_baseline": int(binary_counts["0"]) / (int(binary_counts["0"]) + int(binary_counts["1"])),
            "geometry_rule_state_loo_accuracy": float(geometry_rule["leave_one_out_accuracy"]),
            "geometry_rule_state_loo_macro_recall": float(geometry_rule["leave_one_out_macro_recall"]),
        },
        "inputs": {name: {"path": str(path.relative_to(repo_root)), "sha256": sha256(path)} for name, path in input_paths.items()},
        "outputs": {path.name: {"path": str(path.relative_to(repo_root)), "sha256": sha256(path), "bytes": path.stat().st_size} for path in generated},
        "validation_errors": len(validation_errors),
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "validation_errors.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in validation_errors), encoding="utf-8")
    report = f"""# H002 Paper Strengthening Assets

## Status

```text
status = {manifest['status']}
validation_errors = {len(validation_errors)}
figures = 4
appendix_table_source = tables/appendix_tables.tex
```

## Scope

- Method overview exposes the factor separation, leakage boundary, score path, and route status.
- Comparison-route Recall/Violation plot uses frozen bootstrap confidence intervals.
- Qualitative figure uses seven-row package entries and displays three actual validation rows.
- Failure figure reports front/behind tradeoffs and the latest support/contact target audit.
- Support/contact remains diagnostic: 35 accept, 347 reject, majority baseline 0.908, and geometry-rule LOO accuracy/macro recall 1.0/1.0.
- No hidden-test, support/contact-solved, calibrated p_obs/p_rel, or learned-G_e promotion claim is opened.
"""
    (out / "report.md").write_text(report, encoding="utf-8")
    if validation_errors:
        raise SystemExit(f"Asset validation failed with {len(validation_errors)} errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
