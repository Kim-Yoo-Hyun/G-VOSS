#!/usr/bin/env python3
"""Summarize H001 low-K top-rank reliability diagnostics."""

from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_low_k_sweep_summary_v1"
KS = (5, 10, 20, 50, 100)
LOCKED_KS = (50, 100)
CONDITIONS = (
    "semantic_only",
    "probabilistic_recalibrated",
    "rule_verified_point_subtype",
    "control_family_specific_p_geom_valid",
)
CONDITION_LABELS = {
    "semantic_only": "semantic",
    "probabilistic_recalibrated": "probabilistic",
    "rule_verified_point_subtype": "rule",
    "control_family_specific_p_geom_valid": "family_specific",
}
SOURCE_SPECS = (
    {
        "key": "vlsat",
        "name": "VL-SAT full-validation",
        "bootstrap_name": "vlsat_closed_set_full_validation",
        "root": Path("experiments/H001_geom_reliability/sources/vlsat/full_validation"),
    },
    {
        "key": "open3dsg_recovery",
        "name": "Open3DSG recovery full-validation",
        "bootstrap_name": "open3dsg_ov_full_validation_recovery_relaxed_views_min2",
        "root": Path(
            "experiments/H001_geom_reliability/sources/open3dsg/full_validation/"
            "recovery_relaxed_views_min2"
        ),
    },
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/k_sweep"),
    )
    parser.add_argument(
        "--combined-bootstrap-json",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/sources/open3dsg/full_validation/"
            "recovery_relaxed_views_min2/bootstrap_ci_k_sweep/summary.json"
        ),
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finite(value: Any) -> float | None:
    if value is None:
        return None
    try:
        output = float(value)
    except (TypeError, ValueError):
        return None
    return output if math.isfinite(output) else None


def close(a: Any, b: Any, tol: float = 1e-12) -> bool:
    if a is None or b is None:
        return a is None and b is None
    fa = finite(a)
    fb = finite(b)
    if fa is None or fb is None:
        return a == b
    return abs(fa - fb) <= tol


def metric_block(metrics: dict[str, Any], condition: str, block: str, k: int) -> dict[str, Any]:
    return metrics["conditions"][condition][block]["by_k"][str(k)]


def recall_value(metrics: dict[str, Any], condition: str, k: int) -> float | None:
    return finite(metric_block(metrics, condition, "recall", k).get("recall"))


def violation_value(metrics: dict[str, Any], condition: str, k: int) -> float | None:
    return finite(metric_block(metrics, condition, "violation_rate", k).get("violation_rate"))


def bootstrap_source(bootstrap: dict[str, Any], source_name: str) -> dict[str, Any]:
    source = bootstrap.get("sources", {}).get(source_name)
    if not isinstance(source, dict):
        raise KeyError(f"missing bootstrap source: {source_name}")
    return source


def validate_locked_match(source_name: str, locked: dict[str, Any], sweep: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for condition in CONDITIONS:
        for k in LOCKED_KS:
            for field in ("denominator", "correct", "recall", "selected_predictions"):
                old = metric_block(locked, condition, "recall", k).get(field)
                new = metric_block(sweep, condition, "recall", k).get(field)
                if not close(old, new):
                    errors.append(
                        f"{source_name}:{condition}:R@{k}:{field}:locked={old}:sweep={new}"
                    )
            for field in ("denominator", "violated", "violation_rate", "geometry_coverage"):
                old = metric_block(locked, condition, "violation_rate", k).get(field)
                new = metric_block(sweep, condition, "violation_rate", k).get(field)
                if not close(old, new):
                    errors.append(
                        f"{source_name}:{condition}:V@{k}:{field}:locked={old}:sweep={new}"
                    )
    return errors


def validate_bootstrap_points(
    source_name: str,
    metrics: dict[str, Any],
    bootstrap: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    source = bootstrap_source(bootstrap, source_name)
    for condition in CONDITIONS:
        for k in KS:
            k_key = str(k)
            observed_r = (
                source.get("conditions", {})
                .get(condition, {})
                .get(k_key, {})
                .get("recall", {})
                .get("point")
            )
            observed_v = (
                source.get("conditions", {})
                .get(condition, {})
                .get(k_key, {})
                .get("violation_rate", {})
                .get("point")
            )
            expected_r = recall_value(metrics, condition, k)
            expected_v = violation_value(metrics, condition, k)
            if not close(observed_r, expected_r):
                errors.append(
                    f"{source_name}:{condition}:R@{k}:bootstrap_point={observed_r}:metrics={expected_r}"
                )
            if not close(observed_v, expected_v):
                errors.append(
                    f"{source_name}:{condition}:V@{k}:bootstrap_point={observed_v}:metrics={expected_v}"
                )
    return errors


def source_rows(source_key: str, source_name: str, metrics: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        for k in KS:
            semantic_r = recall_value(metrics, "semantic_only", k)
            semantic_v = violation_value(metrics, "semantic_only", k)
            r_value = recall_value(metrics, condition, k)
            v_value = violation_value(metrics, condition, k)
            rows.append(
                {
                    "source_key": source_key,
                    "source": source_name,
                    "condition": condition,
                    "condition_label": CONDITION_LABELS[condition],
                    "k": k,
                    "recall": r_value,
                    "violation": v_value,
                    "delta_recall_vs_semantic": (
                        r_value - semantic_r
                        if r_value is not None and semantic_r is not None
                        else None
                    ),
                    "delta_violation_vs_semantic": (
                        v_value - semantic_v
                        if v_value is not None and semantic_v is not None
                        else None
                    ),
                    "recall_correct": metric_block(metrics, condition, "recall", k).get("correct"),
                    "recall_denominator": metric_block(metrics, condition, "recall", k).get(
                        "denominator"
                    ),
                    "selected_predictions": metric_block(metrics, condition, "recall", k).get(
                        "selected_predictions"
                    ),
                    "violation_denominator": metric_block(
                        metrics, condition, "violation_rate", k
                    ).get("denominator"),
                    "violated": metric_block(metrics, condition, "violation_rate", k).get(
                        "violated"
                    ),
                    "geometry_coverage": metric_block(
                        metrics, condition, "violation_rate", k
                    ).get("geometry_coverage"),
                }
            )
    return rows


def attach_bootstrap_deltas(
    rows: list[dict[str, Any]],
    bootstrap: dict[str, Any],
    source_name_by_key: dict[str, str],
) -> None:
    bootstrap_name_by_key = {
        spec["key"]: spec["bootstrap_name"]
        for spec in SOURCE_SPECS
    }
    for row in rows:
        source = bootstrap_source(bootstrap, bootstrap_name_by_key[row["source_key"]])
        k_key = str(row["k"])
        condition = row["condition"]
        deltas = source.get("deltas_vs_semantic_only", {}).get(condition, {}).get(k_key, {})
        row["bootstrap_delta_recall_ci95"] = deltas.get("recall", {}).get("ci95")
        row["bootstrap_delta_violation_ci95"] = deltas.get("violation_rate", {}).get("ci95")
        row["bootstrap_source"] = source_name_by_key[row["source_key"]]


def gate_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for condition in (
        "probabilistic_recalibrated",
        "control_family_specific_p_geom_valid",
        "rule_verified_point_subtype",
    ):
        for k in (10, 20):
            subset = [row for row in rows if row["condition"] == condition and row["k"] == k]
            violation_consistent = all(
                row["delta_violation_vs_semantic"] is not None
                and row["delta_violation_vs_semantic"] < 0.0
                for row in subset
            )
            recall_not_collapsed = all(
                row["delta_recall_vs_semantic"] is not None
                and row["delta_recall_vs_semantic"] >= -0.05
                for row in subset
            )
            output.append(
                {
                    "condition": condition,
                    "condition_label": CONDITION_LABELS[condition],
                    "k": k,
                    "violation_reduction_both_sources": violation_consistent,
                    "recall_delta_ge_minus_5pp_both_sources": recall_not_collapsed,
                    "main_reflection_candidate": violation_consistent and recall_not_collapsed,
                }
            )
    return output


def pct(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{100.0 * value:.2f}"


def pp(value: float | None) -> str:
    if value is None:
        return "NA"
    return f"{100.0 * value:+.2f}"


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# H001 Low-K Top-Rank Diagnostic",
        "",
        f"Created at UTC: `{payload['created_at_utc']}`",
        f"Status: `{payload['status']}`",
        "",
        "## Protocol",
        "",
        "- Fixed K grid: `5, 10, 20, 50, 100`.",
        "- `K=1` is excluded from paper-metric consideration because it is too noisy.",
        "- Low-K metrics are diagnostic until explicitly promoted after result review.",
        "- Existing `metrics/` outputs are not overwritten; this report reads `metrics_k_sweep/`.",
        "",
        "## Validation",
        "",
    ]
    if payload["validation_errors"]:
        lines.extend(f"- `{item}`" for item in payload["validation_errors"])
    else:
        lines.append("- `K=50/100` point estimates, denominators, selected counts, and geometry coverage match the locked `metrics/` outputs.")
        lines.append("- Bootstrap point estimates match `metrics_k_sweep/metrics.json` for all reported K values.")
    lines.extend(
        [
            "",
            "## Main-Candidate Gate",
            "",
            "| condition | K | violation reduction both sources | recall delta >= -5 pp both sources | candidate |",
            "| --- | ---: | --- | --- | --- |",
        ]
    )
    for gate in payload["gate_summary"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    gate["condition_label"],
                    str(gate["k"]),
                    str(gate["violation_reduction_both_sources"]).lower(),
                    str(gate["recall_delta_ge_minus_5pp_both_sources"]).lower(),
                    str(gate["main_reflection_candidate"]).lower(),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## K-Sweep Metrics",
            "",
            "| source | condition | K | R@K | V@K | dR vs semantic | dV vs semantic |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in payload["rows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    row["source"],
                    row["condition_label"],
                    str(row["k"]),
                    pct(row["recall"]),
                    pct(row["violation"]),
                    pp(row["delta_recall_vs_semantic"]),
                    pp(row["delta_violation_vs_semantic"]),
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- CSV: `{payload['artifacts']['csv']}`",
            f"- SVG: `{payload['artifacts']['svg']}`",
            "",
        ]
    )
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "source_key",
        "source",
        "condition",
        "condition_label",
        "k",
        "recall",
        "violation",
        "delta_recall_vs_semantic",
        "delta_violation_vs_semantic",
        "recall_correct",
        "recall_denominator",
        "selected_predictions",
        "violation_denominator",
        "violated",
        "geometry_coverage",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in fieldnames})


def svg_polyline(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def render_svg(rows: list[dict[str, Any]]) -> str:
    width = 900
    height = 360
    panel_w = 410
    panel_h = 260
    margin_x = 60
    margin_y = 55
    gap = 30
    colors = {
        "semantic_only": "#555555",
        "probabilistic_recalibrated": "#0072B2",
        "rule_verified_point_subtype": "#009E73",
        "control_family_specific_p_geom_valid": "#D55E00",
    }
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,sans-serif;font-size:12px}.title{font-size:15px;font-weight:bold}.axis{stroke:#333;stroke-width:1}.grid{stroke:#ddd;stroke-width:1}.line{fill:none;stroke-width:2.4}.pt{stroke:white;stroke-width:1}</style>',
    ]
    for panel_index, spec in enumerate(SOURCE_SPECS):
        source_rows = [row for row in rows if row["source_key"] == spec["key"]]
        x0 = margin_x + panel_index * (panel_w + gap)
        y0 = margin_y
        recalls = [row["recall"] for row in source_rows if row["recall"] is not None]
        violations = [row["violation"] for row in source_rows if row["violation"] is not None]
        min_r = max(0.0, min(recalls) - 0.02)
        max_r = min(1.0, max(recalls) + 0.02)
        min_v = 0.0
        max_v = min(1.0, max(violations) + 0.02)
        if max_r <= min_r:
            max_r = min_r + 0.01
        if max_v <= min_v:
            max_v = min_v + 0.01

        def sx(value: float) -> float:
            return x0 + (value - min_r) / (max_r - min_r) * panel_w

        def sy(value: float) -> float:
            return y0 + panel_h - (value - min_v) / (max_v - min_v) * panel_h

        parts.append(f'<text class="title" x="{x0}" y="{y0 - 22}">{spec["name"]}</text>')
        parts.append(f'<line class="axis" x1="{x0}" y1="{y0 + panel_h}" x2="{x0 + panel_w}" y2="{y0 + panel_h}"/>')
        parts.append(f'<line class="axis" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0 + panel_h}"/>')
        parts.append(f'<text x="{x0 + panel_w - 80}" y="{y0 + panel_h + 34}">Recall</text>')
        parts.append(f'<text x="{x0 - 42}" y="{y0 + 12}">Violation</text>')
        parts.append(f'<text x="{x0}" y="{y0 + panel_h + 17}">{min_r:.2f}</text>')
        parts.append(f'<text x="{x0 + panel_w - 32}" y="{y0 + panel_h + 17}">{max_r:.2f}</text>')
        parts.append(f'<text x="{x0 - 38}" y="{y0 + panel_h}">{min_v:.2f}</text>')
        parts.append(f'<text x="{x0 - 38}" y="{y0 + 5}">{max_v:.2f}</text>')
        for condition in CONDITIONS:
            condition_rows = [
                row for row in source_rows if row["condition"] == condition
            ]
            condition_rows.sort(key=lambda row: row["k"])
            points = [
                (sx(row["recall"]), sy(row["violation"]))
                for row in condition_rows
                if row["recall"] is not None and row["violation"] is not None
            ]
            color = colors[condition]
            if points:
                parts.append(
                    f'<polyline class="line" stroke="{color}" points="{svg_polyline(points)}"/>'
                )
                for point, row in zip(points, condition_rows):
                    parts.append(
                        f'<circle class="pt" cx="{point[0]:.1f}" cy="{point[1]:.1f}" r="3.5" fill="{color}"/>'
                    )
                    if row["k"] in (5, 100):
                        parts.append(
                            f'<text x="{point[0] + 5:.1f}" y="{point[1] - 5:.1f}" fill="{color}">K={row["k"]}</text>'
                        )
    legend_x = 60
    legend_y = 335
    for idx, condition in enumerate(CONDITIONS):
        x = legend_x + idx * 205
        color = colors[condition]
        parts.append(f'<line x1="{x}" y1="{legend_y}" x2="{x + 22}" y2="{legend_y}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{x + 28}" y="{legend_y + 4}">{CONDITION_LABELS[condition]}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    combined_bootstrap = load_json(resolve(repo_root, args.combined_bootstrap_json))

    validation_errors: list[str] = []
    rows: list[dict[str, Any]] = []
    source_inputs: dict[str, Any] = {}
    source_name_by_key = {spec["key"]: spec["bootstrap_name"] for spec in SOURCE_SPECS}
    for spec in SOURCE_SPECS:
        root = resolve(repo_root, spec["root"])
        locked_metrics = load_json(root / "metrics/metrics.json")
        sweep_metrics = load_json(root / "metrics_k_sweep/metrics.json")
        if tuple(sweep_metrics.get("ks", [])) != KS:
            validation_errors.append(
                f"{spec['name']}:unexpected_ks:{sweep_metrics.get('ks')}"
            )
        validation_errors.extend(validate_locked_match(spec["name"], locked_metrics, sweep_metrics))
        validation_errors.extend(
            validate_bootstrap_points(
                spec["bootstrap_name"],
                sweep_metrics,
                combined_bootstrap,
            )
        )
        rows.extend(source_rows(spec["key"], spec["name"], sweep_metrics))
        source_inputs[spec["key"]] = {
            "root": relpath(repo_root, root),
            "locked_metrics": relpath(repo_root, root / "metrics/metrics.json"),
            "sweep_metrics": relpath(repo_root, root / "metrics_k_sweep/metrics.json"),
            "bootstrap": relpath(repo_root, resolve(repo_root, args.combined_bootstrap_json)),
        }

    attach_bootstrap_deltas(rows, combined_bootstrap, source_name_by_key)
    csv_path = out_dir / "recall_violation_curve.csv"
    svg_path = out_dir / "recall_violation_curve.svg"
    write_csv(csv_path, rows)
    svg_path.write_text(render_svg(rows), encoding="utf-8")

    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now(),
        "status": "ready" if not validation_errors else "ready_with_validation_errors",
        "protocol": {
            "ks": list(KS),
            "excluded_from_paper_metric": [1],
            "metric_role": "top-rank reliability diagnostic",
            "main_reflection_requires_review": True,
        },
        "source_inputs": source_inputs,
        "combined_bootstrap": relpath(repo_root, resolve(repo_root, args.combined_bootstrap_json)),
        "validation_errors": validation_errors,
        "gate_summary": gate_summary(rows),
        "rows": rows,
        "artifacts": {
            "csv": relpath(repo_root, csv_path),
            "svg": relpath(repo_root, svg_path),
        },
    }
    write_json(out_dir / "summary.json", payload)
    (out_dir / "summary.md").write_text(render_markdown(payload), encoding="utf-8")
    write_json(
        out_dir / "manifest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "created_at_utc": payload["created_at_utc"],
            "status": payload["status"],
            "output_files": [
                relpath(repo_root, out_dir / "summary.json"),
                relpath(repo_root, out_dir / "summary.md"),
                relpath(repo_root, csv_path),
                relpath(repo_root, svg_path),
            ],
        },
    )
    print(json.dumps({"status": payload["status"], "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
