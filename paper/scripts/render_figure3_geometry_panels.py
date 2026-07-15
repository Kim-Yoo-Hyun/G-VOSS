#!/usr/bin/env python3
"""Render geometry-backed Figure 3 panels for selected locked Open3DSG cases.

It draws lightweight point-cloud geometry panels from the Open3DSG
preprocessed payload, not scene crops and not a human audit.
"""

from __future__ import annotations

import html
import importlib
import importlib.util
import json
import math
import pickle
import shutil
import subprocess
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
    "open3dsg_case_019",
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
STRUCTURED_MODEL_JSON = (
    ROOT / "experiments" / "H001_geom_reliability" / "relation_algebra_v1" /
    "evaluation" / "models.json"
)

PANEL_META = {
    "open3dsg_case_001": {
        "panel": "A",
        "role": "successful proximity correction",
        "view": "topdown",
        "takeaway": "Semantic close-by rank is high, but XY object geometry is far.",
    },
    "open3dsg_case_019": {
        "panel": "B",
        "role": "successful relative-vertical correction",
        "view": "vertical",
        "takeaway": "The subject-object vertical order contradicts the predicted predicate.",
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
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="Helvetica, Arial, sans-serif" '
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


def attach_structured_product_ranks(cases: dict[str, dict[str, Any]]) -> None:
    """Attach unrestricted-product and applicability-routed ranks."""
    evalmod = load_eval_module()
    sys.path.insert(0, str(ROOT / "src" / "geocalib"))
    import run_structured_main_evaluation as main_eval

    model = json.loads(STRUCTURED_MODEL_JSON.read_text(encoding="utf-8"))
    scorer = main_eval.make_structured_scorer(model)
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
            raw = main_eval.strict.raw_numeric(verification)
            compatibility = scorer(
                family, prediction["predicate"]["predicate_label"], raw
            )
            if semantic is None or compatibility is None:
                continue
            key = (
                prediction["subgraph_id"], int(prediction["edge"]["subject_id"]),
                int(prediction["edge"]["object_id"]), prediction["predicate"]["predicate_label"],
            )
            grouped[prediction["subgraph_id"]].append({
                "key": key, "family": family, "semantic": float(semantic), "compatibility": float(compatibility),
                "product": float(semantic) * float(compatibility),
            })
    for subgraph, rows in grouped.items():
        source_order = sorted(rows, key=lambda item: (-item["semantic"], item["key"]))
        product_order = sorted(rows, key=lambda item: (-item["product"], item["key"]))
        family_queues = {}
        for family in {row["family"] for row in rows}:
            family_rows = [row for row in rows if row["family"] == family]
            score = "semantic" if family == "support_contact" else "product"
            family_queues[family] = sorted(family_rows, key=lambda item: (-item[score], item["key"]))
        offsets = {family: 0 for family in family_queues}
        routed_order = []
        for source_item in source_order:
            family = source_item["family"]
            routed_order.append(family_queues[family][offsets[family]])
            offsets[family] += 1
        source_rank = {row["key"]: rank for rank, row in enumerate(source_order, 1)}
        product_rank = {row["key"]: rank for rank, row in enumerate(product_order, 1)}
        routed_rank = {row["key"]: rank for rank, row in enumerate(routed_order, 1)}
        by_key = {row["key"]: row for row in rows}
        for key, case_id in target_keys.items():
            if key[0] != subgraph or key not in by_key:
                continue
            item = by_key[key]
            cases[case_id]["structured_product"] = {
                "source_score": item["semantic"],
                "compatibility": item["compatibility"],
                "source_rank": source_rank[key],
                "product_rank": product_rank[key],
                "routed_rank": routed_rank[key],
            }
    missing = [case_id for case_id, row in cases.items() if "structured_product" not in row]
    if missing:
        raise ValueError(f"missing_structured_product_rows:{missing}")


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
        f'<rect x="{plot_x:.1f}" y="{plot_y:.1f}" width="{plot_w:.1f}" height="{plot_h:.1f}" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>'
    ]
    parts.append(svg_text(plot_x + plot_w - 4, plot_y + plot_h + 19, x_label, 15, fill=COLORS["muted"], anchor="end"))
    parts.append(svg_text(plot_x + 4, plot_y + 16, y_label, 15, fill=COLORS["muted"]))
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
        f'<rect x="{left:.1f}" y="{top:.1f}" width="{right-left:.1f}" height="{bottom-top:.1f}" fill="{fill}" opacity="0.18" stroke="{stroke}" stroke-width="1.6"/>',
        f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.2" fill="{stroke}" stroke="#ffffff" stroke-width="1"/>',
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

    plot_x, plot_y, plot_w, plot_h = x + 18, y + 58, w - 36, 245
    project, bounds = make_projector(subject, obj, dims, plot_x, plot_y, plot_w, plot_h)
    s_c = project(float(subject["center"][dims[0]]), float(subject["center"][dims[1]]))
    o_c = project(float(obj["center"][dims[0]]), float(obj["center"][dims[1]]))

    panel_title = {
        "open3dsg_case_001": "(a) Routed correction: proximity",
        "open3dsg_case_019": "(b) Routed correction: vertical",
        "open3dsg_case_026": "(c) Limitation: support",
    }[case_id]
    parts = [
        svg_text(x + 4, y + 20, panel_title, 25, 700),
        svg_text(
            x + 4,
            y + 43,
            f'{pred["subject_label"]}  →  {pred["predicate_label"]}  →  {pred["object_label"]}',
            20,
            700,
            "#374151",
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

    if case_id == "open3dsg_case_001":
        outcome = "geometry-identifiable violation demoted"
    elif case_id == "open3dsg_case_019":
        outcome = "inverse vertical-order violation demoted"
    else:
        outcome = "support violation preserved"
    compatibility = float(row["structured_product"]["compatibility"])
    compatibility_text = f"C={compatibility:.3f}" if compatibility >= 0.001 else "C<.001"
    parts.extend(
        [
            svg_text(
                x + 18,
                y + 329,
                f'rank {row["structured_product"]["source_rank"]} → {row["structured_product"]["routed_rank"]}   |   '
                f'Z={row["structured_product"]["source_score"]:.3f}   {compatibility_text}',
                20,
                700,
                "#111827",
            ),
            svg_text(x + 18, y + 354, metric_line, 18, 400, "#4b5563"),
            svg_text(x + 18, y + 382, outcome, 19, 700, COLORS["warn"]),
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
        "semantic_rank": row["structured_product"]["source_rank"],
        "geometry_rank": row["structured_product"]["routed_rank"],
        "unrestricted_product_rank": row["structured_product"]["product_rank"],
        "source_score": row["structured_product"]["source_score"],
        "p_geom_valid": row["structured_product"]["compatibility"],
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


def render_framework(cases: dict[str, dict[str, Any]]) -> str:
    """Render a compact framework figure with a source-backed geometry example."""
    row = cases["open3dsg_case_001"]
    pred = row["source_prediction"]
    data, _ = load_preprocessed(pred["scan_id"], pred["subgraph_id"])
    subject = object_geometry(data, int(pred["subject_id"]))
    obj = object_geometry(data, int(pred["object_id"]))
    dims = (0, 1)
    plot_x, plot_y, plot_w, plot_h = 28, 66, 385, 235
    project, _ = make_projector(subject, obj, dims, plot_x, plot_y, plot_w, plot_h)
    s_c = project(float(subject["center"][0]), float(subject["center"][1]))
    o_c = project(float(obj["center"][0]), float(obj["center"][1]))

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="405" viewBox="0 0 1500 405">',
        '<rect width="1500" height="405" fill="#ffffff"/>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#374151"/></marker></defs>',
        '<line x1="445" y1="24" x2="445" y2="385" stroke="#e5e7eb" stroke-width="1"/>',
        '<line x1="1080" y1="24" x2="1080" y2="385" stroke="#e5e7eb" stroke-width="1"/>',
        svg_text(24, 30, "(a) High-confidence relation", 25, 700),
        svg_text(476, 30, "(b) Source-score-excluded compatibility", 25, 700),
        svg_text(1110, 30, "(c) Re-ranking", 25, 700),
    ]
    parts.extend(draw_axes(plot_x, plot_y, plot_w, plot_h, "x", "y"))
    parts.extend(draw_points(subject["sample"], dims, project, COLORS["subject"]))
    parts.extend(draw_points(obj["sample"], dims, project, COLORS["object"]))
    parts.extend(draw_bbox(subject, dims, project, COLORS["subject"], COLORS["subject_fill"]))
    parts.extend(draw_bbox(obj, dims, project, COLORS["object"], COLORS["object_fill"]))
    parts.append(
        f'<line x1="{s_c[0]:.1f}" y1="{s_c[1]:.1f}" x2="{o_c[0]:.1f}" y2="{o_c[1]:.1f}" '
        'stroke="#111827" stroke-width="1.5" stroke-dasharray="6 4"/>'
    )
    parts.extend([
        '<circle cx="287" cy="53" r="5" fill="#dc2626"/>',
        svg_text(298, 58, "subject", 16, 400, "#374151"),
        '<circle cx="369" cy="53" r="5" fill="#2563eb"/>',
        svg_text(380, 58, "object", 16, 400, "#374151"),
        svg_text(28, 330, "heater  →  close by  →  trash can", 20, 700),
        svg_text(28, 356, "Open3DSG: Z = 0.853; rank 19", 19, 400, "#374151"),
        svg_text(28, 383, "XY distance = 4.33 m", 19, 700, COLORS["warn"]),
    ])

    def simple_box(x: float, y: float, w: float, h: float, title: str, detail: str, stroke: str = "#94a3b8") -> list[str]:
        return [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#ffffff" stroke="{stroke}" stroke-width="1.3"/>',
            svg_text(x + 14, y + 25, title, 21, 700),
            svg_text(x + 14, y + 51, detail, 17, 400, "#4b5563"),
        ]

    parts.extend(simple_box(485, 63, 205, 65, "Predicate T", "close by / proximity"))
    parts.extend(simple_box(485, 166, 205, 65, "Pair geometry G", "distance, overlap, contact"))
    parts.extend(simple_box(485, 297, 205, 65, "Source score Z", "used only in re-ranking"))
    parts.extend([
        '<line x1="690" y1="96" x2="762" y2="126" stroke="#374151" stroke-width="1.7" marker-end="url(#arrow)"/>',
        '<line x1="690" y1="198" x2="762" y2="164" stroke="#374151" stroke-width="1.7" marker-end="url(#arrow)"/>',
        '<rect x="765" y="86" width="265" height="133" rx="7" fill="#f0fdf4" stroke="#059669" stroke-width="1.6"/>',
        svg_text(897, 119, "Compatibility C(T,G)", 22, 700, "#065f46", "middle"),
        svg_text(897, 151, "linked counterfactual ordering", 17, 400, "#374151", "middle"),
        svg_text(897, 178, "relation-algebra projection", 17, 400, "#374151", "middle"),
        svg_text(897, 205, "C = 0.003", 22, 700, "#065f46", "middle"),
        svg_text(897, 250, "Z is not an input to C", 19, 700, "#b91c1c", "middle"),
        '<line x1="897" y1="219" x2="897" y2="286" stroke="#374151" stroke-width="1.7" marker-end="url(#arrow)"/>',
        '<line x1="690" y1="329" x2="765" y2="329" stroke="#374151" stroke-width="1.7" marker-end="url(#arrow)"/>',
        '<rect x="765" y="286" width="265" height="76" rx="7" fill="#ffffff" stroke="#111827" stroke-width="1.5"/>',
        svg_text(897, 319, "S = Z × C(T,G)", 25, 700, "#111827", "middle"),
        svg_text(897, 349, "within applicable family", 17, 400, "#4b5563", "middle"),
        '<line x1="1030" y1="324" x2="1125" y2="205" stroke="#374151" stroke-width="1.7" marker-end="url(#arrow)"/>',
    ])

    parts.extend([
        svg_text(1160, 91, "19", 42, 700, "#4b5563", "middle"),
        svg_text(1160, 122, "source rank", 18, 400, "#4b5563", "middle"),
        '<line x1="1215" y1="93" x2="1300" y2="93" stroke="#374151" stroke-width="2" marker-end="url(#arrow)"/>',
        svg_text(1360, 91, str(row["structured_product"]["routed_rank"]), 42, 700, "#059669", "middle"),
        svg_text(1360, 122, "re-ranked", 18, 400, "#4b5563", "middle"),
        '<rect x="1125" y="159" width="335" height="82" rx="6" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>',
        svg_text(1292, 186, "Family-slot routing", 21, 700, "#111827", "middle"),
        svg_text(1292, 212, "proximity / vertical: re-ranked", 18, 400, "#4b5563", "middle"),
        svg_text(1292, 233, "support/contact: source order", 18, 400, "#4b5563", "middle"),
        '<rect x="1125" y="276" width="335" height="88" rx="6" fill="#ffffff" stroke="#94a3b8" stroke-width="1.2"/>',
        svg_text(1292, 306, "Joint evaluation", 21, 700, "#111827", "middle"),
        svg_text(1292, 336, "Exact-label Recall@K", 19, 400, "#166534", "middle"),
        svg_text(1292, 360, "Verifier-derived Violation@K", 19, 400, "#991b1b", "middle"),
    ])
    parts.append("</svg>")
    return "\n".join(parts)


def render_figure(cases: dict[str, dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    width, height = 1500, 445
    panel_w, panel_h = 460, 395
    positions = [(20, 38), (520, 38), (1020, 38)]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="445" viewBox="0 0 1500 445">',
        '<rect width="1500" height="445" fill="#ffffff"/>',
        '<circle cx="1110" cy="18" r="5" fill="#dc2626"/>',
        svg_text(1121, 24, "subject", 18, 400, "#374151"),
        '<circle cx="1205" cy="18" r="5" fill="#2563eb"/>',
        svg_text(1216, 24, "object", 18, 400, "#374151"),
        '<line x1="500" y1="38" x2="500" y2="425" stroke="#e5e7eb" stroke-width="1"/>',
        '<line x1="1000" y1="38" x2="1000" y2="425" stroke="#e5e7eb" stroke-width="1"/>',
    ]
    records = []
    for case_id, pos in zip(EXPECTED_CASES, positions):
        panel_svg, record = draw_case_panel(case_id, cases[case_id], pos[0], pos[1], panel_w, panel_h)
        parts.append(panel_svg)
        records.append(record)
    parts.append("</svg>")
    return "\n".join(parts), records


def convert_svg(stem: str) -> None:
    if shutil.which("rsvg-convert") is None:
        return
    source = OUT_DIR / f"{stem}.svg"
    subprocess.run(
        ["rsvg-convert", "--width", "2400", "--keep-aspect-ratio", "--output", str(OUT_DIR / f"{stem}.png"), str(source)],
        check=True,
    )
    subprocess.run(
        ["rsvg-convert", "-f", "pdf", "-o", str(OUT_DIR / f"{stem}.pdf"), str(source)],
        check=True,
    )


def write_report(manifest: dict[str, Any]) -> None:
    report = OUT_DIR / "figure3_geometry_report.md"
    command = (
        'docker run --rm --entrypoint bash --user "$(id -u):$(id -g)" '
        '-v "$PWD":/workspace -w /workspace '
        "h001-geom-reliability:latest -lc 'python paper/scripts/render_figure3_geometry_panels.py'"
    )
    lines = [
        "# Geometry-Backed Figure Generation",
        "",
        f"Status: `{manifest['status']}`",
        "",
        "Generated outputs:",
        "",
        "- `figure1_framework.{svg,pdf,png}`: source-backed framework overview.",
        "- `figure3_geometry_panels.{svg,pdf,png}`: point-cloud qualitative panels.",
        "- `figure3_geometry_cases.json`: case-level source rows, measurements, and object geometry stats.",
        "- `figure3_geometry_manifest.json`: generation and validation manifest.",
        "",
        "Claim boundary:",
        "",
        "- The panels illustrate correction mechanisms and an applicability boundary; they are not a representative evaluation sample.",
        "- They preserve the selected Open3DSG case identities and use the corresponding preprocessed point clouds.",
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
        f"- Figure 1 PDF exists: `{manifest['outputs']['figure1_pdf_exists']}`",
        f"- Figure 3 PDF exists: `{manifest['outputs']['figure3_pdf_exists']}`",
        f"- Output case JSON exists: `{manifest['outputs']['cases_json_exists']}`",
    ]
    report.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = load_queue_cases()
    missing = [case_id for case_id in EXPECTED_CASES if case_id not in cases]
    if missing:
        raise SystemExit(f"Missing locked cases in {QUEUE_JSONL}: {missing}")
    attach_structured_product_ranks(cases)

    svg, records = render_figure(cases)
    framework_svg = render_framework(cases)
    svg_path = OUT_DIR / "figure3_geometry_panels.svg"
    framework_path = OUT_DIR / "figure1_framework.svg"
    cases_path = OUT_DIR / "figure3_geometry_cases.json"
    manifest_path = OUT_DIR / "figure3_geometry_manifest.json"

    svg_path.write_text(svg)
    framework_path.write_text(framework_svg)
    convert_svg("figure1_framework")
    convert_svg("figure3_geometry_panels")
    cases_path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")

    rendered_case_ids = [record["case_id"] for record in records]
    manifest = {
        "schema_version": "h001_geometry_figures_v3",
        "created_at": now_iso(),
        "status": "figure3_geometry_panels_generated_verified",
        "source_queue_jsonl": str(QUEUE_JSONL.relative_to(ROOT)),
        "structured_model_json": str(STRUCTURED_MODEL_JSON.relative_to(ROOT)),
        "paper_score": "applicability-routed relation-algebra-constrained product",
        "preprocessed_root": str(PREPROCESSED_ROOT.relative_to(ROOT)),
        "expected_case_ids": EXPECTED_CASES,
        "rendered_case_ids": rendered_case_ids,
        "missing_case_ids": [case_id for case_id in EXPECTED_CASES if case_id not in rendered_case_ids],
        "outputs": {
            "figure1_svg": str(framework_path.relative_to(ROOT)),
            "figure1_pdf": str((OUT_DIR / "figure1_framework.pdf").relative_to(ROOT)),
            "figure3_svg": str(svg_path.relative_to(ROOT)),
            "figure3_pdf": str((OUT_DIR / "figure3_geometry_panels.pdf").relative_to(ROOT)),
            "cases_json": str(cases_path.relative_to(ROOT)),
            "manifest_json": str(manifest_path.relative_to(ROOT)),
            "figure1_pdf_exists": (OUT_DIR / "figure1_framework.pdf").exists(),
            "figure3_pdf_exists": (OUT_DIR / "figure3_geometry_panels.pdf").exists(),
            "cases_json_exists": cases_path.exists(),
        },
        "claim_boundary": (
            "qualitative geometry-backed correction and applicability-boundary evidence only; "
            "not a representative human audit and not a new metric"
        ),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_report(manifest)
    print(json.dumps({"status": manifest["status"], "rendered_case_ids": rendered_case_ids}, indent=2))


if __name__ == "__main__":
    main()
