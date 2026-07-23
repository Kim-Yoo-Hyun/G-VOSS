#!/usr/bin/env python3
"""Build isolated candidate paper artifacts for the no-family-indicator refit.

The script never writes under ``paper/``.  It consumes only completed branch
outputs, emits candidate TeX/figures under the experiment branch, and stages a
compact non-submission release with checksums.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BRANCH_REL = Path("experiments/RelCompat3D_geom_reliability/no_family_indicator_v1")
SOURCES = ("open3dsg", "vlsat", "sgfn")
SOURCE_LABELS = {"open3dsg": "Open3DSG", "vlsat": "VL-SAT", "sgfn": "SGFN"}
KS = (5, 10, 20, 50, 100)
ROUTED_METHODS = (
    "source_score",
    "routed_product",
    "routed_matched_mlp",
    "routed_rank_average",
    "routed_rrf",
)
METHOD_LABELS = {
    "source_score": "Source",
    "routed_product": "RelCompat3D",
    "routed_matched_mlp": "Matched MLP",
    "routed_rank_average": "RankAvg",
    "routed_rrf": "RRF",
    "all_family_product": "Product (all families)",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--release-out", type=Path, required=True)
    return parser.parse_args()


def resolve(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else root / value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write(path, json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def require_completed(evaluation: Path, names: tuple[str, ...]) -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for name in names:
        path = evaluation / name / "manifest.json"
        payload = load(path)
        if payload.get("status") != "completed":
            raise ValueError(f"evaluation_not_completed:{name}:{payload.get('status')}")
        manifests[name] = payload
    return manifests


def routed_cell(summary: dict[str, Any], source: str, method: str, k: int) -> dict[str, float]:
    cell = summary["sources"][source]["results"][method][str(k)]
    return {
        "recall": float(cell["recall"]["point"]),
        "violation": float(cell["violation_all"]["point"]),
    }


def all_family_cell(
    structured: dict[str, Any], open_route: dict[str, Any], source: str, k: int
) -> dict[str, float]:
    overall = (
        open_route["routes"]["official_strict_full_548"]["overall"]
        if source == "open3dsg"
        else structured["sources"][source]["overall"]
    )
    cell = overall["structured_product"][str(k)]
    return {
        "recall": float(cell["recall"]["point"]),
        "violation": float(cell["violation_all"]["point"]),
    }


def collect_main(
    routed: dict[str, Any], structured: dict[str, Any], open_route: dict[str, Any]
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for source in SOURCES:
        result[source] = {}
        for method in ROUTED_METHODS:
            result[source][method] = {
                str(k): routed_cell(routed, source, method, k) for k in KS
            }
        result[source]["all_family_product"] = {
            str(k): all_family_cell(structured, open_route, source, k) for k in KS
        }
    return result


def main_results_tex(data: dict[str, Any]) -> str:
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"{\small",
        r"\setlength{\tabcolsep}{2.0pt}",
        r"\begin{tabular}{@{}llrrrrrrrrrr@{}}",
        r"\toprule",
        r"& & \multicolumn{2}{c}{$K=5$} & \multicolumn{2}{c}{$K=10$} & \multicolumn{2}{c}{$K=20$} & \multicolumn{2}{c}{$K=50$} & \multicolumn{2}{c}{$K=100$} \\",
        r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}\cmidrule(lr){9-10}\cmidrule(lr){11-12}",
        r"Predictor & Ranking rule & R & V & R & V & R & V & R & V & R & V \\",
        r"\midrule",
    ]
    order = (*ROUTED_METHODS, "all_family_product")
    for source_index, source in enumerate(SOURCES):
        lines.append(rf"\multirow{{6}}{{*}}{{{SOURCE_LABELS[source]}}}")
        for method in order:
            label = METHOD_LABELS[method]
            if method == "routed_product":
                label = rf"\textbf{{{label}}}"
            values: list[str] = []
            for k in KS:
                cell = data[source][method][str(k)]
                values.extend((f"{100*cell['recall']:.2f}", f"{100*cell['violation']:.2f}"))
            prefix = "& " if method != order[0] else "& "
            lines.append(prefix + label + " & " + " & ".join(values) + r" \\")
        if source_index != len(SOURCES) - 1:
            lines.append(r"\midrule")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"}",
            r"\caption{Candidate no-family-indicator results. Exact-label Recall (R$\uparrow$) and verifier-derived Violation (V$\downarrow$) are percentages. All matched methods use the unchanged family-aware ranking procedure.}",
            r"\label{tab:no-family-main}",
            r"\end{table*}",
            "",
        ]
    )
    return "\n".join(lines)


def ablation_tex(summary: dict[str, Any]) -> str:
    labels = {
        "structured_product": "RelCompat3D",
        "wrong_predicate_product": "Wrong predicate",
        "wrong_pair_product": "Wrong pair",
        "shuffled_geometry_product": "Shuffled geometry",
        "endpoint_swap_fixed_label_product": "Fixed-predicate swap",
        "distance_only": "Distance only",
        "compatibility_only": "Compatibility only",
    }
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\setlength{\tabcolsep}{1.5pt}",
        r"\begin{tabular}{@{}llrrrr@{}}",
        r"\toprule",
        r"Predictor & Condition & R@50 & V@50 & R@100 & V@100 \\",
        r"\midrule",
    ]
    for source_index, source in enumerate(SOURCES):
        lines.append(rf"\multirow{{7}}{{*}}{{{SOURCE_LABELS[source]}}}")
        metrics = summary["sources"][source]["metrics"]
        for key, label in labels.items():
            values = []
            for k in (50, 100):
                cell = metrics[key][str(k)]
                values.extend(
                    (f"{100*cell['recall']['point']:.2f}", f"{100*cell['violation']['point']:.2f}")
                )
            shown = rf"\textbf{{{label}}}" if key == "structured_product" else label
            lines.append("& " + shown + " & " + " & ".join(values) + r" \\")
        if source_index != len(SOURCES) - 1:
            lines.append(r"\midrule")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{Candidate ablations under the same candidates and ranking procedure. All entries are percentages.}",
            r"\label{tab:no-family-ablation}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def surface_tex(summary: dict[str, Any]) -> str:
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"Predictor & Source & Ours & Change (95\% CI) & Coverage \\",
        r"\midrule",
    ]
    for source in ("vlsat", "open3dsg", "sgfn"):
        consensus = summary["results"][source]["audits"]["consensus"]
        source_cell = consensus["source"]["50"]
        method_cell = consensus["relcompat3d"]["50"]
        delta = consensus["relcompat3d_minus_source"]["50"]["violation"]
        ci = delta["paired_scan_cluster_ci95"]
        lines.append(
            f"{SOURCE_LABELS[source]} & {100*source_cell['violation']['point']:.2f} & "
            f"{100*method_cell['violation']['point']:.2f} & "
            f"${100*delta['point']:+.2f}$ [${100*ci[0]:+.2f},{100*ci[1]:+.2f}$] & "
            f"{100*method_cell['coverage']['point']:.1f}/{100*method_cell['decidable_coverage']['point']:.1f} " + r"\\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{Candidate surface-based Violation at $K=50$ using point--mesh consensus. Coverage is measured/decidable.}",
            r"\label{tab:no-family-surface}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def scan_ci_tex(summary: dict[str, Any]) -> str:
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\begin{tabular}{@{}lrrrrr@{}}",
        r"\toprule",
        r"Predictor & $K$ & $\Delta$Recall & 95\% CI & $\Delta$Violation & 95\% CI \\",
        r"\midrule",
    ]
    for source_index, source in enumerate(("vlsat", "open3dsg", "sgfn")):
        for k_index, k in enumerate(KS):
            delta = summary["sources"][source]["results"]["deltas_vs_source_score"]["routed_product"][str(k)]
            r_cell = delta["recall"]
            v_cell = delta["violation_all"]
            r_ci = r_cell["paired_scan_cluster_ci95"]
            v_ci = v_cell["paired_scan_cluster_ci95"]
            predictor = rf"\multirow{{5}}{{*}}{{{SOURCE_LABELS[source]}}}" if k_index == 0 else ""
            lines.append(
                f"{predictor} & {k} & {100*r_cell['point']:+.2f} & [{100*r_ci[0]:+.2f},{100*r_ci[1]:+.2f}] & "
                f"{100*v_cell['point']:+.2f} & [{100*v_ci[0]:+.2f},{100*v_ci[1]:+.2f}] " + r"\\"
            )
        if source_index != 2:
            lines.append(r"\midrule")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{Paired scan-cluster intervals for RelCompat3D minus Source at every reported budget. Entries are percentage points.}",
            r"\label{tab:no-family-ci}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def pooled_hard_tex(structured: dict[str, Any]) -> str:
    labels = {
        "structured_product": "Family product",
        "pooled_product": "Pooled product",
        "hard_rule_filter": "Hard-rule filter",
    }
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\begin{tabular}{@{}llrrrr@{}}",
        r"\toprule",
        r"Predictor & Condition & R@50 & V@50 & R@100 & V@100 \\",
        r"\midrule",
    ]
    for source_index, source in enumerate(SOURCES):
        overall = structured["sources"][source]["overall"]
        for method_index, (method, label) in enumerate(labels.items()):
            values = []
            for k in (50, 100):
                cell = overall[method][str(k)]
                values.extend((100*cell["recall"]["point"], 100*cell["violation_all"]["point"]))
            predictor = SOURCE_LABELS[source] if method_index == 0 else ""
            lines.append(
                f"{predictor} & {label} & " + " & ".join(f"{value:.2f}" for value in values) + r" \\"
            )
        if source_index != len(SOURCES) - 1:
            lines.append(r"\midrule")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{Unrestricted family-conditioning and hard-filter comparisons. Values are percentages; the hard filter may select fewer than $K$ candidates.}",
            r"\label{tab:no-family-pooled-hard}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def uncertainty_tex(support: dict[str, Any], open_route: dict[str, Any]) -> str:
    lines = [
        r"\begin{table}[t]",
        r"\centering\small",
        r"\begin{tabular}{@{}llrrrr@{}}",
        r"\toprule",
        r"Predictor & Ranking & $V_{all}$ & $V_{dec}$ & $U$ & $V_{pess}$ \\",
        r"\midrule",
    ]
    for source_index, source in enumerate(("vlsat", "open3dsg", "sgfn")):
        overall = (
            open_route["routes"]["official_strict_full_548"]["overall"]
            if source == "open3dsg"
            else support["sources"][source]["overall"]
        )
        for method_index, (method, label) in enumerate(
            (("source_score", "Source"), ("family_slot_rerank", "RelCompat3D"))
        ):
            cell = overall[method]["100"]
            values = (
                cell["violation_all"]["point"],
                cell["violation_decidable"]["point"],
                cell["uncertainty_rate"]["point"],
                cell["pessimistic_violation"]["point"],
            )
            predictor = SOURCE_LABELS[source] if method_index == 0 else ""
            lines.append(
                f"{predictor} & {label} & " + " & ".join(f"{value:.4f}" for value in values) + r" \\"
            )
        if source_index != 2:
            lines.append(r"\midrule")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{Verifier-uncertainty sensitivity at $K=100$.}",
            r"\label{tab:no-family-uncertainty}",
            r"\end{table}",
            "",
        ]
    )
    return "\n".join(lines)


def heldout_tex(summary: dict[str, Any]) -> str:
    labels = {
        "main_route": "Main",
        "exact_scalar_held_out": "Remove exact scalar",
        "primitive_family_held_out": "Remove measurement family",
        "alternative_evidence_only": "Alternative evidence only",
    }
    lines = [
        r"\begin{table*}[t]",
        r"\centering\small",
        r"\begin{tabular}{@{}llrrrrrr@{}}",
        r"\toprule",
        r"Predictor & Condition & \multicolumn{2}{c}{K=50} & \multicolumn{2}{c}{K=100} & $\Delta$R@50 & $\Delta$V@50 \\",
        r"& & R & V & R & V & & \\",
        r"\midrule",
    ]
    for si, source in enumerate(("vlsat", "open3dsg", "sgfn")):
        block = summary["sources"][source]["scan_cluster"]
        for key, label in labels.items():
            cells = []
            for k in (50, 100):
                item = block[key][str(k)]
                cells.extend((100*item["recall"]["point"], 100*item["violation_all"]["point"]))
            delta = block["deltas_vs_main_route"][key]["50"] if key != "main_route" else None
            dr = 0.0 if delta is None else 100*delta["recall"]["point"]
            dv = 0.0 if delta is None else 100*delta["violation_all"]["point"]
            lines.append(
                f"{SOURCE_LABELS[source] if key == 'main_route' else ''} & {label} & "
                + " & ".join(f"{value:.2f}" for value in cells)
                + f" & {dr:+.2f} & {dv:+.2f} " + r"\\"
            )
        if si != 2:
            lines.append(r"\midrule")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{Candidate feature-removal analysis. Deltas compare each condition with the no-family-indicator main route.}",
            r"\label{tab:no-family-heldout}",
            r"\end{table*}",
            "",
        ]
    )
    return "\n".join(lines)


def counterfactual_tex(summary: dict[str, Any]) -> str:
    lines = [
        r"\begin{table*}[t]",
        r"\centering\scriptsize",
        r"\begin{tabular}{@{}lrrrrrrr@{}}",
        r"\toprule",
        r"Condition & Dev order & \multicolumn{2}{c}{VL-SAT K=50} & \multicolumn{2}{c}{Open3DSG K=50} & \multicolumn{2}{c}{SGFN K=50} \\",
        r"& & R & V & R & V & R & V \\",
        r"\midrule",
    ]
    for condition in summary["condition_order"]:
        order = summary["conditions"][condition]["ordering"]["overall"]["positive_win_rate"]
        values = []
        for source in ("vlsat", "open3dsg", "sgfn"):
            cell = summary["sources"][source]["scan_cluster"][condition]["50"]
            values.extend((100*cell["recall"]["point"], 100*cell["violation_all"]["point"]))
        lines.append(
            condition.replace("_", r"\_") + f" & {100*order:.2f} & "
            + " & ".join(f"{value:.2f}" for value in values)
            + r" \\"
        )
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular}",
            r"\caption{One-factor counterfactual-policy sensitivity after removing the constant family indicator. No condition is selected on validation.}",
            r"\label{tab:no-family-counterfactual}",
            r"\end{table*}",
            "",
        ]
    )
    return "\n".join(lines)


def comparison_payload(new: dict[str, Any], old: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {"sources": {}, "max_abs_change": {"recall": 0.0, "violation": 0.0}}
    for source in SOURCES:
        result["sources"][source] = {}
        for k in KS:
            new_cell = routed_cell(new, source, "routed_product", k)
            old_cell = routed_cell(old, source, "routed_product", k)
            delta = {
                "recall": new_cell["recall"] - old_cell["recall"],
                "violation": new_cell["violation"] - old_cell["violation"],
            }
            result["sources"][source][str(k)] = {
                "old": old_cell,
                "new": new_cell,
                "delta": delta,
            }
            for metric in ("recall", "violation"):
                result["max_abs_change"][metric] = max(
                    result["max_abs_change"][metric], abs(delta[metric])
                )
    return result


def comparison_markdown(comparison: dict[str, Any], lock: dict[str, Any]) -> str:
    lines = [
        "# No-Family-Indicator Candidate Comparison",
        "",
        "The active manuscript is unchanged. Values below compare the candidate family-aware product with the currently active model.",
        "",
        "| Predictor | K | Old R/V | New R/V | Change R/V (percentage points) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for source in SOURCES:
        for k in KS:
            row = comparison["sources"][source][str(k)]
            lines.append(
                f"| {SOURCE_LABELS[source]} | {k} | "
                f"{100*row['old']['recall']:.2f}/{100*row['old']['violation']:.2f} | "
                f"{100*row['new']['recall']:.2f}/{100*row['new']['violation']:.2f} | "
                f"{100*row['delta']['recall']:+.2f}/{100*row['delta']['violation']:+.2f} |"
            )
    lines.extend(
        [
            "",
            f"- Maximum absolute Recall change: `{100*comparison['max_abs_change']['recall']:.3f}` percentage points.",
            f"- Maximum absolute Violation change: `{100*comparison['max_abs_change']['violation']:.3f}` percentage points.",
            f"- Candidate structured model SHA256: `{lock['structured_model_sha256']}`.",
            f"- Candidate strict model SHA256: `{lock['strict_model_sha256']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def render_figure2(data: dict[str, Any]) -> str:
    width, height = 1500, 520
    colors = {"source_score": "#4b5563", "routed_product": "#007c76"}
    ranges = {
        "vlsat": ((0.36, 1.0), (0.0, 0.06)),
        "open3dsg": ((0.0, 0.70), (0.0, 0.70)),
        "sgfn": ((0.20, 1.0), (0.0, 0.10)),
    }
    positions = {"vlsat": 78, "open3dsg": 568, "sgfn": 1058}

    def text(x: float, y: float, value: str, size: int, weight: int = 400, anchor: str = "start") -> str:
        return (
            f'<text x="{x:.1f}" y="{y:.1f}" font-family="TeX Gyre Heros, Helvetica, sans-serif" '
            f'font-size="{size}" font-weight="{weight}" fill="#111827" text-anchor="{anchor}">'
            f"{html.escape(value)}</text>"
        )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1500" height="520" fill="#ffffff"/>',
        '<line x1="980" y1="28" x2="1038" y2="28" stroke="#4b5563" stroke-width="3.2" stroke-dasharray="9,7"/>',
        '<circle cx="1009" cy="28" r="7" fill="#ffffff" stroke="#4b5563" stroke-width="2.2"/>',
        text(1052, 37, "Source", 29),
        '<line x1="1158" y1="28" x2="1216" y2="28" stroke="#007c76" stroke-width="3.4"/>',
        '<rect x="1180" y="21" width="14" height="14" fill="#007c76"/>',
        text(1230, 37, "RelCompat3D", 29),
    ]
    plot_y, plot_w, plot_h = 92, 360, 300
    for panel_index, source in enumerate(("vlsat", "open3dsg", "sgfn")):
        plot_x = positions[source]
        x_range, y_range = ranges[source]
        parts.append(text(plot_x + plot_w / 2, 72, f"({chr(97+panel_index)}) {SOURCE_LABELS[source]}", 32, 700, "middle"))
        for frac in (0.0, 0.25, 0.5, 0.75, 1.0):
            gx = plot_x + frac * plot_w
            gy = plot_y + frac * plot_h
            parts.append(f'<line x1="{gx:.1f}" y1="{plot_y}" x2="{gx:.1f}" y2="{plot_y+plot_h}" stroke="#d9dde1" stroke-width="1.6"/>')
            parts.append(f'<line x1="{plot_x}" y1="{gy:.1f}" x2="{plot_x+plot_w}" y2="{gy:.1f}" stroke="#d9dde1" stroke-width="1.6"/>')
            xt = 100 * (x_range[0] + frac * (x_range[1] - x_range[0]))
            yt = 100 * (y_range[0] + (1-frac) * (y_range[1] - y_range[0]))
            parts.append(text(gx, plot_y + plot_h + 40, f"{xt:.0f}", 27, 400, "middle"))
            parts.append(text(plot_x - 14, gy + 9, f"{yt:.0f}", 27, 400, "end"))
        parts.append(f'<line x1="{plot_x}" y1="{plot_y+plot_h}" x2="{plot_x+plot_w}" y2="{plot_y+plot_h}" stroke="#111827" stroke-width="2.2"/>')
        parts.append(f'<line x1="{plot_x}" y1="{plot_y}" x2="{plot_x}" y2="{plot_y+plot_h}" stroke="#111827" stroke-width="2.2"/>')
        parts.append(text(plot_x + plot_w/2, 510, "Recall@K (%)", 30, 700, "middle"))
        mapped: dict[str, list[tuple[float, float]]] = {}
        for method in ("source_score", "routed_product"):
            points = []
            for k in KS:
                cell = data[source][method][str(k)]
                x = plot_x + (cell["recall"] - x_range[0]) / (x_range[1]-x_range[0]) * plot_w
                y = plot_y + plot_h - (cell["violation"] - y_range[0]) / (y_range[1]-y_range[0]) * plot_h
                points.append((x, y))
            mapped[method] = points
            path = " ".join(("M" if i == 0 else "L") + f" {x:.1f} {y:.1f}" for i, (x, y) in enumerate(points))
            dash = ' stroke-dasharray="9,7"' if method == "source_score" else ""
            parts.append(f'<path d="{path}" fill="none" stroke="{colors[method]}" stroke-width="3.2"{dash}/>')
            for x, y in points:
                if method == "source_score":
                    parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#ffffff" stroke="{colors[method]}" stroke-width="2.2"/>')
                else:
                    parts.append(f'<rect x="{x-7:.1f}" y="{y-7:.1f}" width="14" height="14" fill="{colors[method]}"/>')
        for k, (x, y) in zip(KS, mapped["routed_product"]):
            parts.append(text(x, y - 14, str(k), 27, 700, "middle"))
    parts.append('<text x="24" y="255" transform="rotate(-90 24 255)" font-family="TeX Gyre Heros, Helvetica, sans-serif" font-size="30" font-weight="700" fill="#111827" text-anchor="middle">Violation@K (%) ↓</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def supplement_tex() -> str:
    return r"""\documentclass[10pt]{article}
\usepackage[letterpaper,margin=0.65in]{geometry}
\usepackage{booktabs,multirow,graphicx}
\usepackage[T1]{fontenc}
\title{No-Family-Indicator v1: Candidate Supplement (Non-Submission)}
\author{Isolated RelCompat3D evaluation artifact}
\date{}
\begin{document}
\maketitle
\section{Scope}
This candidate removes only the constant family indicator from each family-specific compatibility head. All splits, targets, normalization, optimization, ranking, metrics, and uncertainty procedures are unchanged. Internal development is used only as a sanity check. The active manuscript is not modified by this artifact.
\section{Official-validation results}
\input{main_results_table}
\input{scan_cluster_ci_table}
\section{Controls and construct checks}
\input{ablation_table}
\input{pooled_hard_table}
\input{uncertainty_table}
\input{surface_audit_table}
\input{held_out_primitive_table}
\input{counterfactual_sensitivity_table}
\section{Artifact lock}
The candidate model, score contract, protocol files, compact evaluation summaries, and SHA256 manifest are included in the accompanying release candidate.
\end{document}
"""


def copy_release_files(root: Path, branch: Path, candidate: Path, release: Path) -> None:
    if release.exists() and any(release.iterdir()):
        raise FileExistsError(f"nonempty_release_output:{release}")
    release.mkdir(parents=True, exist_ok=True)
    for src, dst in (
        (branch / "protocol.json", release / "protocol.json"),
        (branch / "active_paper_lock.json", release / "active_paper_lock.json"),
        (branch / "fit", release / "fit"),
        (branch / "protocols", release / "protocols"),
        (candidate, release / "candidate_paper"),
    ):
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    evaluation_release = release / "evaluation"
    evaluation_release.mkdir()
    for evaluation_dir in sorted((branch / "evaluation").iterdir()):
        if not evaluation_dir.is_dir():
            continue
        target = evaluation_release / evaluation_dir.name
        target.mkdir()
        for name in ("manifest.json", "summary.json", "summary.md", "metrics.csv", "models.json", "uncertainty.csv", "mechanism.json", "thresholds.json"):
            source = evaluation_dir / name
            if source.exists():
                shutil.copy2(source, target / name)
    source_dir = release / "source"
    source_dir.mkdir()
    for rel in (
        Path("src/relcompat3d/fit_linear.py"),
        Path("src/relcompat3d/freeze_protocols.py"),
        Path("src/relcompat3d/build_paper_artifacts.py"),
        Path("src/relcompat3d/render_paper_figures.py"),
        Path("scripts/run_no_family_indicator_v1.sh"),
        Path("configs/relcompat3d/compose.structured.yaml"),
    ):
        target = source_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, target)


def release_manifest(release: Path) -> dict[str, Any]:
    files = sorted(path for path in release.rglob("*") if path.is_file())
    entries = [
        {
            "path": str(path.relative_to(release)),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in files
    ]
    return {
        "schema_version": "relcompat3d_no_family_indicator_release_candidate_v1",
        "status": "verified_non_submission_candidate",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "file_count_before_manifest": len(entries),
        "files": entries,
    }


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    branch = root / BRANCH_REL
    evaluation = branch / "evaluation"
    out = resolve(root, args.out)
    release = resolve(root, args.release_out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_candidate_output:{out}")
    expected = (
        "structured_main",
        "support_routing",
        "open3dsg_route",
        "nonlinear",
        "routed_comparators",
        "routed_ablation",
        "scan_cluster",
        "structured_scan_cluster",
        "surface_audit",
        "held_out_primitive",
        "counterfactual_sensitivity",
    )
    manifests = require_completed(evaluation, expected)
    lock = load(branch / "fit/final_lock.json")
    paper_lock = load(branch / "active_paper_lock.json")
    active_unchanged = {
        rel: (root / rel).exists() and sha256(root / rel) == expected_hash
        for rel, expected_hash in paper_lock["artifacts"].items()
    }
    if not all(active_unchanged.values()):
        raise ValueError(f"active_paper_changed:{active_unchanged}")

    routed = load(evaluation / "routed_comparators/summary.json")
    structured = load(evaluation / "structured_main/summary.json")
    support = load(evaluation / "support_routing/summary.json")
    open_route = load(evaluation / "open3dsg_route/summary.json")
    ablation = load(evaluation / "routed_ablation/summary.json")
    surface = load(evaluation / "surface_audit/summary.json")
    heldout = load(evaluation / "held_out_primitive/summary.json")
    counterfactual = load(evaluation / "counterfactual_sensitivity/summary.json")
    counterfactual_models = load(evaluation / "counterfactual_sensitivity/models.json")
    heldout_models = load(evaluation / "held_out_primitive/models.json")
    old_routed = load(
        root / "experiments/RelCompat3D_geom_reliability/routed_comparators_v1/evaluation/summary.json"
    )
    main_data = collect_main(routed, structured, open_route)
    comparison = comparison_payload(routed, old_routed)

    out.mkdir(parents=True, exist_ok=True)
    candidate_figures = branch / "candidate_figures"
    figure_manifest = load(candidate_figures / "manifest.json")
    if figure_manifest.get("status") != "completed_svg_candidates":
        raise ValueError("candidate_qualitative_figures_not_completed")
    for source in sorted(candidate_figures.iterdir()):
        if source.is_file():
            shutil.copy2(source, out / source.name)
    for stem in ("figure3_qualitative", "teaser_exchange"):
        subprocess.run(
            ["rsvg-convert", "-f", "pdf", "-o", str(out / f"{stem}.pdf"), str(out / f"{stem}.svg")],
            check=True,
        )
        subprocess.run(
            ["rsvg-convert", "--width", "2400", "--output", str(out / f"{stem}.png"), str(out / f"{stem}.svg")],
            check=True,
        )
    write_json(out / "main_results.json", main_data)
    write_json(out / "comparison.json", comparison)
    write(out / "comparison.md", comparison_markdown(comparison, lock))
    write(out / "main_results_table.tex", main_results_tex(main_data))
    write(out / "ablation_table.tex", ablation_tex(ablation))
    write(out / "surface_audit_table.tex", surface_tex(surface))
    write(out / "scan_cluster_ci_table.tex", scan_ci_tex(routed))
    write(out / "pooled_hard_table.tex", pooled_hard_tex(structured))
    write(out / "uncertainty_table.tex", uncertainty_tex(support, open_route))
    write(out / "held_out_primitive_table.tex", heldout_tex(heldout))
    write(out / "counterfactual_sensitivity_table.tex", counterfactual_tex(counterfactual))
    figure_svg = render_figure2(main_data)
    write(out / "figure2_tradeoff.svg", figure_svg)
    if shutil.which("rsvg-convert"):
        subprocess.run(
            ["rsvg-convert", "-f", "pdf", "-o", str(out / "figure2_tradeoff.pdf"), str(out / "figure2_tradeoff.svg")],
            check=True,
        )
        subprocess.run(
            ["rsvg-convert", "--width", "2400", "--output", str(out / "figure2_tradeoff.png"), str(out / "figure2_tradeoff.svg")],
            check=True,
        )
    write(out / "candidate_supplement.tex", supplement_tex())
    write(
        out / "method_figure_note.md",
        "# Method Figure Impact\n\n"
        "The active method diagram does not depict the removed constant family one-hot. "
        "Its predicate, pair-measurement, predictor-score, compatibility, and family-aware "
        "ranking flow is therefore unchanged. The result-dependent trajectory, teaser, and "
        "qualitative ranks are regenerated in this candidate directory.\n",
    )
    if not shutil.which("latexmk"):
        raise FileNotFoundError("latexmk_not_available_for_candidate_supplement")
    subprocess.run(
        [
            "latexmk",
            "-pdf",
            "-interaction=nonstopmode",
            "-halt-on-error",
            "candidate_supplement.tex",
        ],
        cwd=out,
        check=True,
    )
    for suffix in ("aux", "fdb_latexmk", "fls", "log"):
        auxiliary = out / f"candidate_supplement.{suffix}"
        if auxiliary.exists():
            auxiliary.unlink()

    validations = {
        "all_expected_evaluations_completed": len(manifests) == len(expected),
        "active_paper_artifacts_unchanged": all(active_unchanged.values()),
        "all_predictors_and_k_present": all(
            all(str(k) in main_data[source][method] for k in KS)
            for source in SOURCES
            for method in (*ROUTED_METHODS, "all_family_product")
        ),
        "family_indicator_absent_in_locked_model": not any(
            name.startswith("family:")
            for attempt in load(branch / "fit/structured_models.json")["attempts"].values()
            for model in attempt.values()
            for name in model["feature_names"]
        ),
        "family_indicator_absent_in_counterfactual_refits": not any(
            name.startswith("family:")
            for condition in counterfactual_models["conditions"].values()
            for model in condition.values()
            for name in model["feature_names"]
        ),
        "family_indicator_absent_in_feature_removal_refits": not any(
            name.startswith("family:")
            for condition in heldout_models["models"].values()
            for model in condition.values()
            for name in model["feature_names"]
        ),
        "route_checks_pass": all(
            all(source_checks.values()) for source_checks in routed["route_checks"].values()
        ),
        "candidate_figure_pdf_created": (out / "figure2_tradeoff.pdf").exists(),
        "candidate_supplement_pdf_created": (out / "candidate_supplement.pdf").exists(),
        "candidate_qualitative_pdf_created": (out / "figure3_qualitative.pdf").exists(),
        "candidate_teaser_pdf_created": (out / "teaser_exchange.pdf").exists(),
    }
    if not all(validations.values()):
        raise ValueError(f"candidate_validation_failed:{validations}")
    manifest = {
        "schema_version": "relcompat3d_no_family_indicator_candidate_paper_v1",
        "status": "completed_non_submission_candidate",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_lock": lock,
        "active_paper_checks": active_unchanged,
        "evaluation_manifests": {
            name: sha256(evaluation / name / "manifest.json") for name in expected
        },
        "validations": validations,
        "comparison": comparison["max_abs_change"],
        "outputs": sorted(path.name for path in out.iterdir()),
    }
    write_json(out / "manifest.json", manifest)

    copy_release_files(root, branch, out, release)
    readme = (
        "# RelCompat3D No-Family-Indicator v1 Release Candidate\n\n"
        "Status: non-submission candidate for user review. The active paper is unchanged.\n\n"
        "The bundle contains the model/score lock, frozen protocols, compact official-validation outputs, candidate tables/figure/supplement source, and source entry points.\n"
    )
    write(release / "README.md", readme)
    release_data = release_manifest(release)
    write_json(release / "manifest.json", release_data)
    checksum_lines = [
        f"{entry['sha256']}  {entry['path']}" for entry in release_data["files"]
    ] + [f"{sha256(release / 'manifest.json')}  manifest.json"]
    write(release / "SHA256SUMS", "\n".join(checksum_lines) + "\n")
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "candidate_out": str(out.relative_to(root)),
                "release_out": str(release.relative_to(root)),
                "validations": validations,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
