#!/usr/bin/env python3
"""Render geometry-backed Figure 3 panels for the locked Open3DSG cases.

This script intentionally uses the same locked qualitative case IDs as the
row-card Figure 3 draft. It draws lightweight point-cloud geometry panels from
the Open3DSG preprocessed payload, not scene crops and not a human audit.
"""

from __future__ import annotations

import html
import importlib
import importlib.util
import json
import math
import pickle
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


# Some preprocessed pickles were written with numpy 2 module paths, while the
# reproduction Docker image currently has numpy 1.x. The alias keeps loading
# deterministic without rewriting the ignored pickle payload.
sys.modules.setdefault("numpy._core", importlib.import_module("numpy.core"))
sys.modules.setdefault("numpy._core.multiarray", importlib.import_module("numpy.core.multiarray"))
sys.modules.setdefault("numpy._core.numeric", importlib.import_module("numpy.core.numeric"))


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "paper" / "generated" / "figures"
QUEUE_JSONL = (
    ROOT
    / "experiments"
    / "H001_geom_reliability"
    / "sources"
    / "open3dsg"
    / "failure_cases"
    / "queue.jsonl"
)
PREPROCESSED_ROOT = (
    ROOT
    / "local_dataset"
    / "Open3DSG_staged"
    / "h001_full_validation_runtime"
    / "output"
    / "datasets"
    / "OpenSG_3RScan"
    / "preprocessed"
)

EXPECTED_CASES = [
    "open3dsg_case_001",
    "open3dsg_case_010",
    "open3dsg_case_026",
]

PREDICTIONS_JSONL = (
    ROOT / "experiments" / "H001_geom_reliability" / "sources" / "open3dsg" /
    "full_validation" / "recovery_relaxed_views_min2" / "adapter" / "predictions.jsonl"
)
VERIFICATION_JSONL = (
    ROOT / "experiments" / "H001_geom_reliability" / "sources" / "open3dsg" /
    "full_validation" / "recovery_relaxed_views_min2" / "geometry" / "verification.jsonl"
)
FAMILY_MODEL_JSON = (
    ROOT / "archive" / "hypothesis_records" / "hypothesis" / "CAND-001" /
    "H001_geometry-grounded-verification" / "artifacts" / "calibration" /
    "p_geom_valid_family" / "model.json"
)

PANEL_META = {
    "open3dsg_case_001": {
        "panel": "A",
        "role": "successful proximity correction",
        "view": "topdown",
        "takeaway": "Semantic close-by rank is high, but XY object geometry is far.",
    },
    "open3dsg_case_010": {
        "panel": "B",
        "role": "successful support correction",
        "view": "vertical",
        "takeaway": "Support/contact evidence exposes a positive float gap.",
    },
    "open3dsg_case_026": {
        "panel": "C",
        "role": "residual compatibility error",
        "view": "vertical",
        "takeaway": "A high compatibility score can still retain a verifier violation in the top ranks.",
    },
}

REASON_LABELS = {
    "far_in_normalized_xy": "normalized pair distance is large",
    "point_subtype_delegated_to_obb_for_family": "local contact evidence is unavailable",
    "vertical_order_contradicts_predicate": "vertical order contradicts the predicted relation",
    "positive_float_gap_large": "vertical separation is too large",
    "subtype_soft_support_contact": "support/contact evidence is weak",
}

COLORS = {
    "subject": "#dc2626",
    "subject_fill": "#fecaca",
    "object": "#2563eb",
    "object_fill": "#bfdbfe",
    "axis": "#111827",
    "grid": "#d1d5db",
    "muted": "#6b7280",
    "panel": "#f8fafc",
    "ink": "#111827",
    "warn": "#b91c1c",
}


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def svg_text(
    x: float,
    y: float,
    text: str,
    size: int = 13,
    weight: int = 400,
    fill: str = "#111827",
    anchor: str = "start",
) -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(text)}</text>'
    )


def wrapped_text(x: float, y: float, text: str, width: int, size: int = 12, fill: str = "#111827") -> str:
    parts = []
    for idx, line in enumerate(textwrap.wrap(text, width=width, break_long_words=False, break_on_hyphens=False)):
        parts.append(svg_text(x, y + idx * (size + 4), line, size=size, fill=fill))
    return "\n".join(parts)


def load_queue_cases() -> dict[str, dict[str, Any]]:
    cases: dict[str, dict[str, Any]] = {}
    with QUEUE_JSONL.open() as handle:
        for line in handle:
            row = json.loads(line)
            case_id = row.get("case_id")
            if case_id in EXPECTED_CASES:
                cases[case_id] = row
    return cases


def load_eval_module() -> Any:
    path = ROOT / "src" / "geocalib" / "evaluate_predictions.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("h001_figure3_eval", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_import:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def attach_current_family_product_ranks(cases: dict[str, dict[str, Any]]) -> None:
    """Attach ranks from the same family-product score reported in the main table."""
    evalmod = load_eval_module()
    model = json.loads(FAMILY_MODEL_JSON.read_text(encoding="utf-8"))
    target_subgraphs = {row["source_prediction"]["subgraph_id"] for row in cases.values()}
    target_keys = {
        (
            row["source_prediction"]["subgraph_id"],
            int(row["source_prediction"]["subject_id"]),
            int(row["source_prediction"]["object_id"]),
            row["source_prediction"]["predicate_label"],
        ): case_id
        for case_id, row in cases.items()
    }
    grouped: dict[str, list[dict[str, Any]]] = {subgraph: [] for subgraph in target_subgraphs}
    with PREDICTIONS_JSONL.open(encoding="utf-8") as pred_handle, VERIFICATION_JSONL.open(encoding="utf-8") as ver_handle:
        for pred_line, ver_line in zip(pred_handle, ver_handle):
            prediction = json.loads(pred_line)
            if prediction["subgraph_id"] not in target_subgraphs:
                continue
            family = prediction["predicate"]["predicate_family"]
            if family not in {"support_contact", "proximity", "relative_vertical"}:
                continue
            verification = json.loads(ver_line)
            if prediction["prediction_id"] != verification["prediction_id"]:
                raise ValueError("prediction_verification_identity_mismatch")
            semantic = evalmod.semantic_score(prediction)
            compact = evalmod.compact_verification(verification)
            compatibility = evalmod.family_specific_p_geom_valid(prediction, compact, model)
            if semantic is None or compatibility is None:
                continue
            key = (
                prediction["subgraph_id"], int(prediction["edge"]["subject_id"]),
                int(prediction["edge"]["object_id"]), prediction["predicate"]["predicate_label"],
            )
            grouped[prediction["subgraph_id"]].append({
                "key": key, "semantic": float(semantic), "compatibility": float(compatibility),
                "product": float(semantic) * float(compatibility),
            })
    for subgraph, rows in grouped.items():
        source_order = sorted(rows, key=lambda item: (-item["semantic"], item["key"]))
        product_order = sorted(rows, key=lambda item: (-item["product"], item["key"]))
        source_rank = {row["key"]: rank for rank, row in enumerate(source_order, 1)}
        product_rank = {row["key"]: rank for rank, row in enumerate(product_order, 1)}
        by_key = {row["key"]: row for row in rows}
        for key, case_id in target_keys.items():
            if key[0] != subgraph or key not in by_key:
                continue
            item = by_key[key]
            cases[case_id]["current_family_product"] = {
                "source_score": item["semantic"],
                "compatibility": item["compatibility"],
                "source_rank": source_rank[key],
                "product_rank": product_rank[key],
            }
    missing = [case_id for case_id, row in cases.items() if "current_family_product" not in row]
    if missing:
        raise ValueError(f"missing_current_family_product_rows:{missing}")


def subgraph_number(subgraph_id: str) -> str:
    return subgraph_id.rsplit("_", 1)[-1]


def load_preprocessed(scan_id: str, subgraph_id: str) -> tuple[dict[str, Any], Path]:
    path = PREPROCESSED_ROOT / scan_id / f"data_dict_{subgraph_number(subgraph_id)}.pkl"
    with path.open("rb") as handle:
        return pickle.load(handle), path


def as_xyz(points: Any) -> np.ndarray:
    xyz = np.asarray(points, dtype=float)[:, :3]
    xyz = xyz[np.isfinite(xyz).all(axis=1)]
    return xyz


def sample_points(xyz: np.ndarray, limit: int = 260) -> np.ndarray:
    if len(xyz) <= limit:
        return xyz
    step = max(1, len(xyz) // limit)
    return xyz[::step][:limit]


def object_geometry(data: dict[str, Any], object_id: int) -> dict[str, Any]:
    idx = data["objects_id"].index(object_id)
    xyz = as_xyz(data["objects_pcl_glob"][idx])
    center = np.asarray(data["objects_center"][idx], dtype=float)
    return {
        "object_id": object_id,
        "label": data["id2name"].get(str(object_id), "unknown"),
        "index": idx,
        "center": center,
        "points": xyz,
        "sample": sample_points(xyz),
        "min": xyz.min(axis=0),
        "max": xyz.max(axis=0),
    }


def finite_bounds(values: list[float]) -> tuple[float, float]:
    lo = min(values)
    hi = max(values)
    if math.isclose(lo, hi):
        lo -= 0.5
        hi += 0.5
    pad = (hi - lo) * 0.10
    return lo - pad, hi + pad


def normalize(value: float, lo: float, hi: float, out_lo: float, out_hi: float) -> float:
    return out_lo + (value - lo) / (hi - lo) * (out_hi - out_lo)


def make_projector(
    subject: dict[str, Any],
    obj: dict[str, Any],
    dims: tuple[int, int],
    plot_x: float,
    plot_y: float,
    plot_w: float,
    plot_h: float,
) -> tuple[Any, dict[str, Any]]:
    xs = []
    ys = []
    for geom in (subject, obj):
        xs.extend([float(geom["min"][dims[0]]), float(geom["max"][dims[0]]), float(geom["center"][dims[0]])])
        ys.extend([float(geom["min"][dims[1]]), float(geom["max"][dims[1]]), float(geom["center"][dims[1]])])
    x_lo, x_hi = finite_bounds(xs)
    y_lo, y_hi = finite_bounds(ys)

    def project(a: float, b: float) -> tuple[float, float]:
        return (
            normalize(a, x_lo, x_hi, plot_x, plot_x + plot_w),
            normalize(b, y_lo, y_hi, plot_y + plot_h, plot_y),
        )

    return project, {"x_min": x_lo, "x_max": x_hi, "y_min": y_lo, "y_max": y_hi}


def draw_axes(plot_x: float, plot_y: float, plot_w: float, plot_h: float, x_label: str, y_label: str) -> list[str]:
    parts = [
        f'<rect x="{plot_x:.1f}" y="{plot_y:.1f}" width="{plot_w:.1f}" height="{plot_h:.1f}" fill="#ffffff" stroke="#9ca3af" stroke-width="1"/>'
    ]
    for frac in (0.25, 0.5, 0.75):
        x = plot_x + plot_w * frac
        y = plot_y + plot_h * frac
        parts.append(f'<line x1="{x:.1f}" y1="{plot_y:.1f}" x2="{x:.1f}" y2="{plot_y + plot_h:.1f}" stroke="{COLORS["grid"]}" stroke-width="0.7"/>')
        parts.append(f'<line x1="{plot_x:.1f}" y1="{y:.1f}" x2="{plot_x + plot_w:.1f}" y2="{y:.1f}" stroke="{COLORS["grid"]}" stroke-width="0.7"/>')
    parts.append(svg_text(plot_x + plot_w - 4, plot_y + plot_h + 19, x_label, 11, fill=COLORS["muted"], anchor="end"))
    parts.append(svg_text(plot_x + 4, plot_y + 14, y_label, 11, fill=COLORS["muted"]))
    return parts


def draw_points(points: np.ndarray, dims: tuple[int, int], project: Any, color: str) -> list[str]:
    parts = []
    for point in points:
        x, y = project(float(point[dims[0]]), float(point[dims[1]]))
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.35" fill="{color}" opacity="0.38"/>')
    return parts


def draw_bbox(geom: dict[str, Any], dims: tuple[int, int], project: Any, stroke: str, fill: str) -> list[str]:
    x0, y0 = project(float(geom["min"][dims[0]]), float(geom["min"][dims[1]]))
    x1, y1 = project(float(geom["max"][dims[0]]), float(geom["max"][dims[1]]))
    left, right = sorted([x0, x1])
    top, bottom = sorted([y0, y1])
    cx, cy = project(float(geom["center"][dims[0]]), float(geom["center"][dims[1]]))
    return [
        f'<rect x="{left:.1f}" y="{top:.1f}" width="{right-left:.1f}" height="{bottom-top:.1f}" fill="{fill}" opacity="0.25" stroke="{stroke}" stroke-width="1.7"/>',
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.2" fill="{stroke}" stroke="#ffffff" stroke-width="1"/>',
        svg_text(cx + 6, cy - 6, f'{geom["object_id"]}:{geom["label"]}', 11, 700, stroke),
    ]


def measurements(subject: dict[str, Any], obj: dict[str, Any]) -> dict[str, float]:
    s_center = subject["center"]
    o_center = obj["center"]
    return {
        "xy_center_distance": float(np.linalg.norm(s_center[:2] - o_center[:2])),
        "z_center_delta_subject_minus_object": float(s_center[2] - o_center[2]),
        "subject_bottom_minus_object_top": float(subject["min"][2] - obj["max"][2]),
        "subject_top_minus_object_top": float(subject["max"][2] - obj["max"][2]),
        "object_top_minus_subject_bottom": float(obj["max"][2] - subject["min"][2]),
    }


def panel_dims(case_id: str, subject: dict[str, Any], obj: dict[str, Any]) -> tuple[tuple[int, int], str, str, str]:
    view = PANEL_META[case_id]["view"]
    if view == "topdown":
        return (0, 1), "x", "y", "top-down XY"
    x_gap = abs(float(subject["center"][0] - obj["center"][0]))
    y_gap = abs(float(subject["center"][1] - obj["center"][1]))
    horizontal_dim = 0 if x_gap >= y_gap else 1
    horizontal_label = "x" if horizontal_dim == 0 else "y"
    return (horizontal_dim, 2), horizontal_label, "z", f"elevation {horizontal_label}-Z"


def draw_case_panel(case_id: str, row: dict[str, Any], x: float, y: float, w: float, h: float) -> tuple[str, dict[str, Any]]:
    pred = row["source_prediction"]
    data, preprocess_path = load_preprocessed(pred["scan_id"], pred["subgraph_id"])
    subject = object_geometry(data, int(pred["subject_id"]))
    obj = object_geometry(data, int(pred["object_id"]))
    dims, x_label, y_label, view_label = panel_dims(case_id, subject, obj)
    measure = measurements(subject, obj)

    plot_x, plot_y, plot_w, plot_h = x + 24, y + 92, w - 48, 205
    project, bounds = make_projector(subject, obj, dims, plot_x, plot_y, plot_w, plot_h)
    s_c = project(float(subject["center"][dims[0]]), float(subject["center"][dims[1]]))
    o_c = project(float(obj["center"][dims[0]]), float(obj["center"][dims[1]]))

    parts = [
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="8" fill="{COLORS["panel"]}" stroke="#cbd5e1" stroke-width="1.2"/>',
        svg_text(x + 18, y + 28, f'{PANEL_META[case_id]["panel"]}. {PANEL_META[case_id]["role"]}', 15, 700),
        svg_text(
            x + 18,
            y + 51,
            f'{pred["subject_label"]} -> {pred["object_label"]}: {pred["predicate_label"]}',
            13,
            700,
            "#374151",
        ),
        svg_text(
            x + 18,
            y + 72,
            f'source rank {row["current_family_product"]["source_rank"]} -> product rank {row["current_family_product"]["product_rank"]}; '
            f'Z={row["current_family_product"]["source_score"]:.3f}, C={row["current_family_product"]["compatibility"]:.3f}',
            12,
            400,
            "#4b5563",
        ),
    ]
    parts.extend(draw_axes(plot_x, plot_y, plot_w, plot_h, x_label, y_label))
    parts.extend(draw_points(subject["sample"], dims, project, COLORS["subject"]))
    parts.extend(draw_points(obj["sample"], dims, project, COLORS["object"]))
    parts.extend(draw_bbox(subject, dims, project, COLORS["subject"], COLORS["subject_fill"]))
    parts.extend(draw_bbox(obj, dims, project, COLORS["object"], COLORS["object_fill"]))
    parts.append(
        f'<line x1="{s_c[0]:.1f}" y1="{s_c[1]:.1f}" x2="{o_c[0]:.1f}" y2="{o_c[1]:.1f}" '
        'stroke="#111827" stroke-width="1.5" stroke-dasharray="5,4"/>'
    )

    if PANEL_META[case_id]["view"] == "topdown":
        metric_line = f'XY center distance = {measure["xy_center_distance"]:.2f}'
    elif row["source_prediction"]["predicate_family"] == "support_contact":
        metric_line = f'subject bottom - object top = {measure["subject_bottom_minus_object_top"]:.2f}'
    else:
        metric_line = f'subject center z - object center z = {measure["z_center_delta_subject_minus_object"]:.2f}'

    reason = "; ".join(REASON_LABELS.get(code, code.replace("_", " ")) for code in row["geometry"]["reason_codes"])
    parts.extend(
        [
            svg_text(x + 24, y + 324, view_label, 12, 700, "#374151"),
            svg_text(x + 24, y + 345, metric_line, 12, 400, "#374151"),
            wrapped_text(x + 24, y + 367, f'Evidence: {reason}', 48, 11, COLORS["warn"]),
        ]
    )

    case_record = {
        "case_id": case_id,
        "panel": PANEL_META[case_id]["panel"],
        "role": PANEL_META[case_id]["role"],
        "view": view_label,
        "preprocessed_path": str(preprocess_path.relative_to(ROOT)),
        "scan_id": pred["scan_id"],
        "subgraph_id": pred["subgraph_id"],
        "subject_id": pred["subject_id"],
        "subject_label": pred["subject_label"],
        "object_id": pred["object_id"],
        "object_label": pred["object_label"],
        "predicate_family": pred["predicate_family"],
        "predicate_label": pred["predicate_label"],
        "semantic_rank": row["current_family_product"]["source_rank"],
        "geometry_rank": row["current_family_product"]["product_rank"],
        "source_score": row["current_family_product"]["source_score"],
        "p_geom_valid": row["current_family_product"]["compatibility"],
        "verification_status": row["geometry"]["verification_status"],
        "reason_codes": row["geometry"]["reason_codes"],
        "ground_truth_match_status": row["ground_truth"]["match_status"],
        "matched_gt_predicates": row["ground_truth"].get("matched_predicates", []),
        "measurements": {key: round(value, 6) for key, value in measure.items()},
        "plot_bounds": {key: round(float(value), 6) for key, value in bounds.items()},
        "subject_geometry": {
            "center": [round(float(v), 6) for v in subject["center"]],
            "min": [round(float(v), 6) for v in subject["min"]],
            "max": [round(float(v), 6) for v in subject["max"]],
        },
        "object_geometry": {
            "center": [round(float(v), 6) for v in obj["center"]],
            "min": [round(float(v), 6) for v in obj["min"]],
            "max": [round(float(v), 6) for v in obj["max"]],
        },
    }
    return "\n".join(parts), case_record


def render_figure(cases: dict[str, dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    width, height = 1500, 560
    panel_w, panel_h = 460, 430
    positions = [(20, 92), (520, 92), (1020, 92)]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="560" viewBox="0 0 1500 560">',
        '<rect width="1500" height="560" fill="#ffffff"/>',
        svg_text(20, 43, "Geometry-backed re-ranking cases", 22, 700),
        svg_text(
            20,
            70,
            "Two successful corrections and one residual error, rendered from the actual ordered object-pair point clouds.",
            14,
            400,
            "#4b5563",
        ),
    ]
    records = []
    for case_id, pos in zip(EXPECTED_CASES, positions):
        panel_svg, record = draw_case_panel(case_id, cases[case_id], pos[0], pos[1], panel_w, panel_h)
        parts.append(panel_svg)
        records.append(record)
    parts.append("</svg>")
    return "\n".join(parts), records


def write_report(manifest: dict[str, Any]) -> None:
    report = OUT_DIR / "figure3_geometry_report.md"
    command = (
        'docker run --rm --user "$(id -u):$(id -g)" '
        "-v /home/yoohyun/research:/workspace -w /workspace "
        "h001-open3dsg-repro:cu128 bash -lc 'python paper/scripts/render_figure3_geometry_panels.py'"
    )
    lines = [
        "# Figure 3 Geometry Panel Generation",
        "",
        f"Status: `{manifest['status']}`",
        "",
        "Generated outputs:",
        "",
        "- `figure3_geometry_panels.svg`: point-cloud geometry panels for the locked Figure 3 cases.",
        "- `figure3_geometry_cases.json`: case-level source rows, measurements, and object geometry stats.",
        "- `figure3_geometry_manifest.json`: generation and validation manifest.",
        "",
        "Claim boundary:",
        "",
        "- These panels are qualitative reviewer-defense / failure-mechanism examples.",
        "- They are not a representative human visual audit, not a new metric, and not broad open-vocabulary evidence.",
        "- They preserve the same locked Open3DSG case IDs used by `figure3_failure_cases.svg`.",
        "",
        "Reproduction command:",
        "",
        "```bash",
        command,
        "```",
        "",
        "Validation:",
        "",
        f"- Expected locked cases: `{', '.join(EXPECTED_CASES)}`",
        f"- Rendered cases: `{', '.join(manifest['rendered_case_ids'])}`",
        f"- Missing cases: `{', '.join(manifest['missing_case_ids']) or 'none'}`",
        f"- Output SVG exists: `{manifest['outputs']['svg_exists']}`",
        f"- Output case JSON exists: `{manifest['outputs']['cases_json_exists']}`",
    ]
    report.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = load_queue_cases()
    missing = [case_id for case_id in EXPECTED_CASES if case_id not in cases]
    if missing:
        raise SystemExit(f"Missing locked cases in {QUEUE_JSONL}: {missing}")
    attach_current_family_product_ranks(cases)

    svg, records = render_figure(cases)
    svg_path = OUT_DIR / "figure3_geometry_panels.svg"
    cases_path = OUT_DIR / "figure3_geometry_cases.json"
    manifest_path = OUT_DIR / "figure3_geometry_manifest.json"

    svg_path.write_text(svg)
    cases_path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")

    rendered_case_ids = [record["case_id"] for record in records]
    manifest = {
        "schema_version": "h001_figure3_geometry_panels_v1",
        "created_at": now_iso(),
        "status": "figure3_geometry_panels_generated_verified",
        "source_queue_jsonl": str(QUEUE_JSONL.relative_to(ROOT)),
        "preprocessed_root": str(PREPROCESSED_ROOT.relative_to(ROOT)),
        "expected_case_ids": EXPECTED_CASES,
        "rendered_case_ids": rendered_case_ids,
        "missing_case_ids": [case_id for case_id in EXPECTED_CASES if case_id not in rendered_case_ids],
        "outputs": {
            "svg": str(svg_path.relative_to(ROOT)),
            "cases_json": str(cases_path.relative_to(ROOT)),
            "manifest_json": str(manifest_path.relative_to(ROOT)),
            "svg_exists": svg_path.exists(),
            "cases_json_exists": cases_path.exists(),
        },
        "claim_boundary": (
            "qualitative geometry-backed failure-mechanism evidence only; "
            "not a representative human audit and not a new metric"
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_report(manifest)
    print(json.dumps({"status": manifest["status"], "rendered_case_ids": rendered_case_ids}, indent=2))


if __name__ == "__main__":
    main()
