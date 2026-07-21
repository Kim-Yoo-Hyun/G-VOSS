#!/usr/bin/env python3
"""Render source-backed framework and pair--evidence--outcome figures.

The qualitative grid uses ordered-pair point clouds from the Open3DSG
preprocessed payload and links each view to its evidence and ranking outcome.
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
    "full_validation" / "adapter" / "predictions.jsonl"
)
VERIFICATION_JSONL = (
    ROOT / "experiments" / "H001_geom_reliability" / "sources" / "open3dsg" /
    "full_validation" / "geometry" / "verification.jsonl"
)
GROUND_TRUTH_JSONL = (
    ROOT / "experiments" / "H001_geom_reliability" / "sources" / "vlsat" /
    "full_validation" / "adapter" / "ground_truth.jsonl"
)
STRUCTURED_MODEL_JSON = (
    ROOT / "experiments" / "H001_geom_reliability" / "no_family_indicator_v1" /
    "fit" / "structured_models.json"
)
PRIMARY_SCAN_CI_JSON = (
    ROOT / "experiments" / "H001_geom_reliability" /
    "no_family_indicator_v1" / "evaluation" / "scan_cluster" / "summary.json"
)
SURFACE_AUDIT_JSON = (
    ROOT / "experiments" / "H001_geom_reliability" /
    "no_family_indicator_v1" / "evaluation" / "surface_audit" / "summary.json"
)

TEASER_SCAN_ID = "c2d99345-1947-2fbf-818d-90ea82acef29"
TEASER_SUBGRAPH_ID = f"{TEASER_SCAN_ID}_2"
TEASER_REMOVED_KEY = (TEASER_SUBGRAPH_ID, 16, 6, "higher than")
TEASER_PROMOTED_KEY = (TEASER_SUBGRAPH_ID, 16, 23, "close by")
TEASER_EXPECTED_RANKS = {
    "removed": (6, 425),
    "promoted": (81, 30),
}

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
    # Color-blind-safe accents are restricted to data identity and method state.
    # Large backgrounds and decorative color fields are intentionally avoided.
    "subject": "#d55e00",
    "subject_fill": "#f2c6ad",
    "object": "#0072b2",
    "object_fill": "#b9d9ea",
    "method": "#007c76",
    "method_dark": "#005c57",
    "residual": "#9a6700",
    "axis": "#262626",
    "grid": "#d4d4d4",
    "line": "#b8bdc3",
    "muted": "#5f6368",
    "panel": "#ffffff",
    "ink": "#202124",
    "warn": "#9a3412",
}

FIGURE_FONT = "TeX Gyre Heros, Helvetica, sans-serif"


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
    # At the manuscript's full-width placement, 27 SVG units render at just
    # over 9 pt; the one-column teaser uses the same lower bound.
    size = max(size, 27)
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FIGURE_FONT}" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(text)}</text>'
    )


def svg_ctr_text(
    x: float,
    y: float,
    prefix: str,
    suffix: str,
    size: int,
    weight: int = 400,
    fill: str = "#111827",
    anchor: str = "start",
) -> str:
    """Render C^{tr} with same-size Unicode modifier glyphs."""
    size = max(size, 27)
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FIGURE_FONT}" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
        f'{esc(prefix)}Cᵗʳ{esc(suffix)}</text>'
    )


def svg_outlined_text(
    x: float,
    y: float,
    text: str,
    size: int,
    weight: int,
    fill: str,
    anchor: str = "start",
) -> str:
    """Render a compact direct label over a point-cloud view."""
    size = max(size, 27)
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FIGURE_FONT}" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" '
        f'stroke="#ffffff" stroke-width="3" stroke-linejoin="round" paint-order="stroke">'
        f'{esc(text)}</text>'
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


def attach_structured_product_ranks(cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Attach ranks and return the fixed, source-backed teaser context."""
    evalmod = load_eval_module()
    sys.path.insert(0, str(ROOT / "src" / "geocalib"))
    import run_structured_main_evaluation as main_eval

    model = json.loads(STRUCTURED_MODEL_JSON.read_text(encoding="utf-8"))
    scorer = main_eval.make_structured_scorer(model)
    target_subgraphs = {
        row["source_prediction"]["subgraph_id"] for row in cases.values()
    } | {TEASER_SUBGRAPH_ID}
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
                "key": key,
                "family": family,
                "semantic": float(semantic),
                "compatibility": float(compatibility),
                "product": float(semantic) * float(compatibility),
                "status": verification.get("verification_status")
                or (verification.get("verification") or {}).get("verification_status"),
                "subject_id": int(prediction["edge"]["subject_id"]),
                "subject_label": prediction["edge"]["subject_label"],
                "object_id": int(prediction["edge"]["object_id"]),
                "object_label": prediction["edge"]["object_label"],
                "predicate": prediction["predicate"]["predicate_label"],
                "distance_xy": raw.get("distance_xy"),
                "center_delta_z": raw.get("center_delta_z"),
            })
    exact_gt_keys: set[tuple[str, int, int, str]] = set()
    with GROUND_TRUTH_JSONL.open(encoding="utf-8") as gt_handle:
        for line in gt_handle:
            gt = json.loads(line)
            if gt.get("subgraph_id") != TEASER_SUBGRAPH_ID:
                continue
            exact_gt_keys.add(
                (
                    gt["subgraph_id"],
                    int(gt["subject_id"]),
                    int(gt["object_id"]),
                    gt["predicate_label"],
                )
            )

    teaser_context: dict[str, Any] | None = None
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
        if subgraph == TEASER_SUBGRAPH_ID:
            source_top = source_order[:50]
            method_top = routed_order[:50]
            source_ids = {id(row) for row in source_top}
            method_ids = {id(row) for row in method_top}

            def compact(row: dict[str, Any]) -> dict[str, Any]:
                return {
                    "subject_id": row["subject_id"],
                    "subject_label": row["subject_label"],
                    "object_id": row["object_id"],
                    "object_label": row["object_label"],
                    "predicate": row["predicate"],
                    "family": row["family"],
                    "status": row["status"],
                    "source_score": row["semantic"],
                    "compatibility": row["compatibility"],
                    "source_rank": source_rank[row["key"]],
                    "routed_rank": routed_rank[row["key"]],
                    "distance_xy": row["distance_xy"],
                    "center_delta_z": row["center_delta_z"],
                }

            if TEASER_REMOVED_KEY not in by_key or TEASER_PROMOTED_KEY not in by_key:
                raise ValueError("missing_fixed_teaser_relation")
            target_row = by_key[TEASER_REMOVED_KEY]
            promoted_row = by_key[TEASER_PROMOTED_KEY]
            target_ranks = (
                source_rank[TEASER_REMOVED_KEY], routed_rank[TEASER_REMOVED_KEY]
            )
            promoted_ranks = (
                source_rank[TEASER_PROMOTED_KEY], routed_rank[TEASER_PROMOTED_KEY]
            )
            teaser_context = {
                "scan_id": TEASER_SCAN_ID,
                "subgraph_id": subgraph,
                "k": 50,
                "source_top": [compact(row) for row in source_top],
                "method_top": [compact(row) for row in method_top],
                "target_removed": compact(target_row),
                "promoted": compact(promoted_row),
                "validations": {
                    "source_count": len(source_top),
                    "method_count": len(method_top),
                    "target_in_source_top50": id(target_row) in source_ids,
                    "target_not_in_method_top50": id(target_row) not in method_ids,
                    "promoted_not_in_source_top50": id(promoted_row) not in source_ids,
                    "promoted_in_method_top50": id(promoted_row) in method_ids,
                    "promoted_status_satisfied": promoted_row["status"] == "satisfied",
                    "promoted_exact_label_gt": TEASER_PROMOTED_KEY in exact_gt_keys,
                    "removed_not_exact_label_gt": TEASER_REMOVED_KEY not in exact_gt_keys,
                    "removed_status_violated": target_row["status"] == "violated",
                    "removed_rank_lock": target_ranks == TEASER_EXPECTED_RANKS["removed"],
                    "promoted_rank_lock": promoted_ranks == TEASER_EXPECTED_RANKS["promoted"],
                },
            }
    missing = [case_id for case_id, row in cases.items() if "structured_product" not in row]
    if missing:
        raise ValueError(f"missing_structured_product_rows:{missing}")
    if teaser_context is None or not all(teaser_context["validations"].values()):
        raise ValueError(f"invalid_teaser_context:{teaser_context}")
    return teaser_context


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


def make_scene_projector(
    geometries: list[dict[str, Any]],
    dims: tuple[int, int],
    plot_x: float,
    plot_y: float,
    plot_w: float,
    plot_h: float,
) -> tuple[Any, dict[str, Any]]:
    xs: list[float] = []
    ys: list[float] = []
    for geom in geometries:
        xs.extend([float(geom["min"][dims[0]]), float(geom["max"][dims[0]])])
        ys.extend([float(geom["min"][dims[1]]), float(geom["max"][dims[1]])])
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
        f'<rect x="{plot_x:.1f}" y="{plot_y:.1f}" width="{plot_w:.1f}" height="{plot_h:.1f}" fill="#ffffff" stroke="{COLORS["line"]}" stroke-width="1"/>'
    ]
    parts.append(svg_text(plot_x + plot_w - 4, plot_y + plot_h + 18, x_label, 19, fill=COLORS["muted"], anchor="end"))
    parts.append(svg_text(plot_x + 5, plot_y + 20, y_label, 19, fill=COLORS["muted"]))
    return parts


def draw_points(
    points: np.ndarray,
    dims: tuple[int, int],
    project: Any,
    color: str,
    marker: str = "circle",
    opacity: float = 0.5,
) -> list[str]:
    parts = []
    for point in points:
        x, y = project(float(point[dims[0]]), float(point[dims[1]]))
        if marker == "square":
            parts.append(
                f'<rect x="{x-1.35:.1f}" y="{y-1.35:.1f}" width="2.7" height="2.7" '
                f'fill="{color}" opacity="{opacity:.2f}"/>'
            )
        else:
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="1.35" '
                f'fill="{color}" opacity="{opacity:.2f}"/>'
            )
    return parts


def draw_bbox(
    geom: dict[str, Any],
    dims: tuple[int, int],
    project: Any,
    stroke: str,
    fill: str,
    dashed: bool = False,
    center_marker: str = "circle",
) -> list[str]:
    x0, y0 = project(float(geom["min"][dims[0]]), float(geom["min"][dims[1]]))
    x1, y1 = project(float(geom["max"][dims[0]]), float(geom["max"][dims[1]]))
    left, right = sorted([x0, x1])
    top, bottom = sorted([y0, y1])
    cx, cy = project(float(geom["center"][dims[0]]), float(geom["center"][dims[1]]))
    dash = ' stroke-dasharray="6,4"' if dashed else ""
    center = (
        f'<rect x="{cx-4.0:.1f}" y="{cy-4.0:.1f}" width="8" height="8" '
        f'fill="{stroke}" stroke="#ffffff" stroke-width="1"/>'
        if center_marker == "square"
        else f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.2" fill="{stroke}" stroke="#ffffff" stroke-width="1"/>'
    )
    return [
        f'<rect x="{left:.1f}" y="{top:.1f}" width="{right-left:.1f}" height="{bottom-top:.1f}" fill="{fill}" opacity="0.08" stroke="{stroke}" stroke-width="1.6"{dash}/>',
        center,
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
    return (horizontal_dim, 2), horizontal_label, "z", f"elevation {horizontal_label}–z"


def draw_case_panel(case_id: str, row: dict[str, Any], x: float, y: float, w: float, h: float) -> tuple[str, dict[str, Any]]:
    pred = row["source_prediction"]
    data, preprocess_path = load_preprocessed(pred["scan_id"], pred["subgraph_id"])
    subject = object_geometry(data, int(pred["subject_id"]))
    obj = object_geometry(data, int(pred["object_id"]))
    dims, x_label, y_label, view_label = panel_dims(case_id, subject, obj)
    measure = measurements(subject, obj)

    # The qualitative view is deliberately a plain evidence grid rather than a
    # stack of interface-like cards.  Core labels remain readable at the final
    # two-column manuscript width.
    plot_x, plot_y, plot_w, plot_h = x + 8, y + 90, w - 16, 218
    project, bounds = make_projector(subject, obj, dims, plot_x, plot_y, plot_w, plot_h)
    s_c = project(float(subject["center"][dims[0]]), float(subject["center"][dims[1]]))
    o_c = project(float(obj["center"][dims[0]]), float(obj["center"][dims[1]]))

    panel_title = {
        "open3dsg_case_001": "(a) Proximity correction",
        "open3dsg_case_019": "(b) Vertical-order correction",
        "open3dsg_case_026": "(c) Support/contact residual",
    }[case_id]
    parts = [
        svg_text(x + 4, y + 25, panel_title, 26, 700),
        svg_text(
            x + 4,
            y + 55,
            f'{pred["subject_label"]}  →  {pred["predicate_label"]}  →  {pred["object_label"]}',
            22,
            400,
            COLORS["ink"],
        ),
        svg_text(x + 8, y + 81, view_label, 20, 400, COLORS["muted"]),
    ]
    parts.extend(draw_axes(plot_x, plot_y, plot_w, plot_h, x_label, y_label))
    parts.extend(draw_points(subject["sample"], dims, project, COLORS["subject"], "circle", 0.62))
    parts.extend(draw_points(obj["sample"], dims, project, COLORS["object"], "square", 0.28))
    parts.extend(draw_bbox(subject, dims, project, COLORS["subject"], COLORS["subject_fill"]))
    parts.extend(draw_bbox(obj, dims, project, COLORS["object"], COLORS["object_fill"], True, "square"))
    parts.append(
        f'<line x1="{s_c[0]:.1f}" y1="{s_c[1]:.1f}" x2="{o_c[0]:.1f}" y2="{o_c[1]:.1f}" '
        f'stroke="{COLORS["axis"]}" stroke-width="1.5" stroke-dasharray="5,4"/>'
    )

    if PANEL_META[case_id]["view"] == "topdown":
        metric_line = f'XY center distance = {measure["xy_center_distance"]:.2f} m'
        evidence_line = "large separation for close by"
    elif row["source_prediction"]["predicate_family"] == "support_contact":
        gap = f'{measure["subject_bottom_minus_object_top"]:.2f}'.replace("-", "−")
        metric_line = f'vertical bottom–top gap = {gap} m'
        evidence_line = "contact evidence remains unresolved"
    else:
        delta_z = f'{measure["z_center_delta_subject_minus_object"]:.2f}'.replace("-", "−")
        metric_line = f'subject–object center Δz = {delta_z} m'
        evidence_line = "subject lies below the object"

    if case_id == "open3dsg_case_001":
        outcome = "Demoted: inconsistent proximity"
    elif case_id == "open3dsg_case_019":
        outcome = "Demoted: inverted vertical order"
    else:
        outcome = "Unchanged: kept in source order"
    compatibility = float(row["structured_product"]["compatibility"])
    if case_id == "open3dsg_case_026":
        score_line = f'Source order  ·  Z={row["structured_product"]["source_score"]:.3f}; C not applied'
        score_svg = svg_text(x + 8, y + 491, score_line, 20, 400, COLORS["muted"])
    else:
        compatibility_suffix = (
            f"={compatibility:.3f}" if compatibility >= 0.001 else "<.001"
        )
        score_svg = svg_ctr_text(
            x + 8,
            y + 491,
            f'Source → RelCompat3D  ·  Z={row["structured_product"]["source_score"]:.3f}; ',
            compatibility_suffix,
            20,
            400,
            COLORS["muted"],
        )
    outcome_color = COLORS["method"] if case_id != "open3dsg_case_026" else COLORS["residual"]
    parts.extend(
        [
            f'<line x1="{x+8:.1f}" y1="{y+342:.1f}" x2="{x+w-8:.1f}" y2="{y+342:.1f}" stroke="{COLORS["line"]}" stroke-width="1"/>',
            svg_text(x + 8, y + 367, "Measured evidence", 21, 700, COLORS["muted"]),
            svg_text(x + 8, y + 394, metric_line, 22, 700, COLORS["ink"]),
            svg_text(x + 8, y + 419, evidence_line, 20, 400, COLORS["muted"]),
            f'<line x1="{x+8:.1f}" y1="{y+436:.1f}" x2="{x+w-8:.1f}" y2="{y+436:.1f}" stroke="{COLORS["line"]}" stroke-width="1"/>',
            svg_text(
                x + 8,
                y + 465,
                f'Rank {row["structured_product"]["source_rank"]} → {row["structured_product"]["routed_rank"]}',
                23,
                700,
                COLORS["ink"],
            ),
            score_svg,
            f'<line x1="{x+8:.1f}" y1="{y+502:.1f}" x2="{x+8:.1f}" y2="{y+527:.1f}" stroke="{outcome_color}" stroke-width="4"/>',
            svg_text(x + 20, y + 523, outcome, 21, 700, COLORS["ink"]),
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
    plot_x, plot_y, plot_w, plot_h = 20, 62, 390, 228
    project, _ = make_projector(subject, obj, dims, plot_x, plot_y, plot_w, plot_h)
    s_c = project(float(subject["center"][0]), float(subject["center"][1]))
    o_c = project(float(obj["center"][0]), float(obj["center"][1]))

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="410" viewBox="0 0 1440 410">',
        '<rect width="1440" height="410" fill="#ffffff"/>',
        f'<defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{COLORS["axis"]}"/></marker></defs>',
        f'<line x1="435" y1="18" x2="435" y2="394" stroke="{COLORS["grid"]}" stroke-width="1"/>',
        f'<line x1="1035" y1="18" x2="1035" y2="394" stroke="{COLORS["grid"]}" stroke-width="1"/>',
        svg_text(20, 31, "(a) Failure example", 27, 700),
        svg_text(460, 31, "(b) Compatibility and score", 27, 700),
        svg_text(1060, 31, "(c) Re-ranking", 27, 700),
    ]
    parts.extend(draw_axes(plot_x, plot_y, plot_w, plot_h, "x", "y"))
    parts.extend(draw_points(subject["sample"], dims, project, COLORS["subject"], "circle", 0.62))
    parts.extend(draw_points(obj["sample"], dims, project, COLORS["object"], "square", 0.28))
    parts.extend(draw_bbox(subject, dims, project, COLORS["subject"], COLORS["subject_fill"]))
    parts.extend(draw_bbox(obj, dims, project, COLORS["object"], COLORS["object_fill"], True, "square"))
    parts.append(
        f'<line x1="{s_c[0]:.1f}" y1="{s_c[1]:.1f}" x2="{o_c[0]:.1f}" y2="{o_c[1]:.1f}" '
        f'stroke="{COLORS["axis"]}" stroke-width="1.5" stroke-dasharray="6 4"/>'
    )
    parts.extend([
        f'<circle cx="285" cy="78" r="5" fill="{COLORS["subject"]}"/>',
        svg_text(296, 84, "subject", 19, 400, COLORS["muted"]),
        f'<rect x="365" y="73" width="10" height="10" fill="{COLORS["object"]}"/>',
        svg_text(381, 84, "object", 19, 400, COLORS["muted"]),
        svg_text(20, 326, "heater  →  close by  →  trash can", 22, 700),
        svg_text(20, 355, "Open3DSG: Z = 0.853; source rank 19", 21, 400, COLORS["muted"]),
        f'<line x1="20" y1="368" x2="20" y2="393" stroke="{COLORS["warn"]}" stroke-width="4"/>',
        svg_text(32, 389, "measured XY distance = 4.33 m", 22, 700, COLORS["ink"]),
    ])

    def simple_box(
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        detail: str,
        stroke: str = "#9aa0a6",
        title_size: int = 21,
    ) -> list[str]:
        return [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="#ffffff" stroke="{stroke}" stroke-width="1.25"/>',
            svg_text(x + 14, y + 27, title, title_size, 700),
            svg_text(x + 14, y + 53, detail, 19, 400, COLORS["muted"]),
        ]

    parts.extend(simple_box(465, 66, 230, 66, "Predicate semantics", "T: close by / proximity", COLORS["object"], 20))
    parts.extend(simple_box(465, 158, 230, 70, "Pair measurements", "G: distance, Δz, overlap", COLORS["object"], 20))
    parts.extend(simple_box(465, 300, 250, 66, "Predictor score", "Z: used only for re-ranking", title_size=20))
    parts.extend([
        f'<line x1="695" y1="99" x2="748" y2="121" stroke="{COLORS["axis"]}" stroke-width="1.7" marker-end="url(#arrow)"/>',
        f'<line x1="695" y1="193" x2="748" y2="177" stroke="{COLORS["axis"]}" stroke-width="1.7" marker-end="url(#arrow)"/>',
        f'<rect x="735" y="78" width="280" height="148" rx="4" fill="#ffffff" stroke="{COLORS["method"]}" stroke-width="1.6"/>',
        f'<line x1="735" y1="78" x2="1015" y2="78" stroke="{COLORS["method"]}" stroke-width="4"/>',
        svg_ctr_text(875, 113, "Compatibility ", "(T,G)", 22, 700, COLORS["method_dark"], "middle"),
        svg_text(875, 148, "linked pairwise ordering", 20, 400, COLORS["muted"], "middle"),
        svg_text(875, 178, "transformation averaging", 20, 400, COLORS["muted"], "middle"),
        svg_ctr_text(875, 211, "", "(T,G) = 0.003", 24, 700, COLORS["method_dark"], "middle"),
        f'<line x1="876" y1="226" x2="876" y2="282" stroke="{COLORS["axis"]}" stroke-width="1.7" marker-end="url(#arrow)"/>',
        f'<line x1="715" y1="333" x2="748" y2="333" stroke="{COLORS["axis"]}" stroke-width="1.7" marker-end="url(#arrow)"/>',
        f'<rect x="752" y="286" width="248" height="80" rx="4" fill="#ffffff" stroke="{COLORS["axis"]}" stroke-width="1.4"/>',
        svg_text(876, 317, "Within-family score", 20, 700, COLORS["muted"], "middle"),
        svg_ctr_text(876, 350, "u = Z × ", "(T,G)", 25, 700, COLORS["ink"], "middle"),
        f'<line x1="1000" y1="326" x2="1062" y2="225" stroke="{COLORS["axis"]}" stroke-width="1.7" marker-end="url(#arrow)"/>',
    ])

    parts.extend([
        svg_text(1120, 98, "19", 44, 700, COLORS["muted"], "middle"),
        svg_text(1120, 128, "source rank", 20, 400, COLORS["muted"], "middle"),
        f'<line x1="1175" y1="97" x2="1260" y2="97" stroke="{COLORS["axis"]}" stroke-width="2" marker-end="url(#arrow)"/>',
        svg_text(1330, 98, str(row["structured_product"]["routed_rank"]), 44, 700, COLORS["method"], "middle"),
        svg_text(1330, 128, "RelCompat3D rank", 20, 400, COLORS["muted"], "middle"),
        f'<rect x="1062" y="151" width="355" height="116" rx="4" fill="#ffffff" stroke="{COLORS["method"]}" stroke-width="1.5"/>',
        svg_text(1239, 181, "Family-aware re-ranking", 22, 700, COLORS["method_dark"], "middle"),
        f'<line x1="1080" y1="193" x2="1399" y2="193" stroke="{COLORS["grid"]}" stroke-width="1"/>',
        svg_ctr_text(1239, 220, "proximity, vertical  →  rank by Z × ", "", 19, 400, COLORS["ink"], "middle"),
        svg_text(1239, 250, "support/contact  →  rank by Z", 19, 400, COLORS["ink"], "middle"),
        f'<line x1="1062" y1="303" x2="1417" y2="303" stroke="{COLORS["line"]}" stroke-width="1.2"/>',
        svg_text(1239, 330, "Joint evaluation", 22, 700, COLORS["ink"], "middle"),
        svg_text(1147, 360, "Recall@K  ↑", 21, 400, COLORS["ink"], "middle"),
        f'<line x1="1239" y1="340" x2="1239" y2="371" stroke="{COLORS["grid"]}" stroke-width="1"/>',
        svg_text(1332, 360, "Violation@K  ↓", 21, 400, COLORS["ink"], "middle"),
        svg_text(1147, 386, "exact predicate match", 18, 400, COLORS["muted"], "middle"),
        svg_text(1332, 386, "rule-based verifier", 18, 400, COLORS["muted"], "middle"),
    ])
    parts.append("</svg>")
    return "\n".join(parts)


def load_teaser_metrics() -> dict[str, float]:
    primary = json.loads(PRIMARY_SCAN_CI_JSON.read_text(encoding="utf-8"))
    surface = json.loads(SURFACE_AUDIT_JSON.read_text(encoding="utf-8"))
    source = primary["sources"]["open3dsg"]["results"]["source_score"]["50"]
    method = primary["sources"]["open3dsg"]["results"]["family_slot_rerank"]["50"]
    surface_rows = surface["results"]["open3dsg"]["audits"]["consensus"]
    return {
        "source_recall": float(source["recall"]["point"]),
        "method_recall": float(method["recall"]["point"]),
        "source_violation": float(source["violation_all"]["point"]),
        "method_violation": float(method["violation_all"]["point"]),
        "surface_source_violation": float(surface_rows["source"]["50"]["violation"]["point"]),
        "surface_method_violation": float(surface_rows["relcompat3d"]["50"]["violation"]["point"]),
    }


def render_teaser(
    cases: dict[str, dict[str, Any]],
    metrics: dict[str, float],
    context: dict[str, Any],
) -> str:
    """Render the same reconstructed scene before and after Top-50 re-ranking."""
    data, _ = load_preprocessed(context["scan_id"], context["subgraph_id"])
    geometries = [object_geometry(data, int(object_id)) for object_id in data["objects_id"]]
    by_id = {int(geom["object_id"]): geom for geom in geometries}
    target = context["target_removed"]
    promoted = context["promoted"]

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="315" viewBox="0 0 720 315">',
        '<rect width="720" height="315" fill="#ffffff"/>',
        f'<defs><marker id="teaser-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{COLORS["axis"]}"/></marker></defs>',
        svg_text(18, 27, "Source Top-50 graph", 22, 700),
        svg_text(394, 27, "RelCompat3D Top-50 graph", 22, 700, COLORS["method_dark"]),
        f'<line x1="348" y1="132" x2="372" y2="132" stroke="{COLORS["axis"]}" stroke-width="1.8" marker-end="url(#teaser-arrow)"/>',
    ]

    def draw_graph(
        selection: list[dict[str, Any]],
        x: float,
        removed_ghost: bool,
    ) -> list[str]:
        plot_x, plot_y, plot_w, plot_h = x, 43, 326, 170
        project, _ = make_scene_projector(geometries, (0, 1), plot_x, plot_y, plot_w, plot_h)
        graph_parts = [
            f'<rect x="{plot_x:.1f}" y="{plot_y:.1f}" width="{plot_w:.1f}" height="{plot_h:.1f}" fill="#ffffff" stroke="{COLORS["line"]}" stroke-width="1"/>',
            svg_text(plot_x + 7, plot_y + 18, "top-down reconstructed scene", 16, 400, COLORS["muted"]),
        ]
        for geom in geometries:
            graph_parts.extend(
                draw_points(sample_points(geom["points"], 55), (0, 1), project, "#7f8a93", "circle", 0.22)
            )

        seen_pairs: set[tuple[int, int]] = set()
        for candidate in selection:
            pair = (int(candidate["subject_id"]), int(candidate["object_id"]))
            if pair in seen_pairs or pair[0] not in by_id or pair[1] not in by_id:
                continue
            seen_pairs.add(pair)
            subject = by_id[pair[0]]
            obj = by_id[pair[1]]
            sx, sy = project(float(subject["center"][0]), float(subject["center"][1]))
            ox, oy = project(float(obj["center"][0]), float(obj["center"][1]))
            graph_parts.append(
                f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" '
                f'stroke="#7f8a93" stroke-width="0.9" opacity="0.22"/>'
            )
        for geom in geometries:
            cx, cy = project(float(geom["center"][0]), float(geom["center"][1]))
            graph_parts.append(
                f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2.7" fill="#ffffff" stroke="{COLORS["axis"]}" stroke-width="0.9"/>'
            )

        emphasis = target if not removed_ghost else promoted
        s_geom = by_id[int(emphasis["subject_id"])]
        o_geom = by_id[int(emphasis["object_id"])]
        sx, sy = project(float(s_geom["center"][0]), float(s_geom["center"][1]))
        ox, oy = project(float(o_geom["center"][0]), float(o_geom["center"][1]))
        accent = COLORS["warn"] if not removed_ghost else COLORS["method"]
        graph_parts.append(
            f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" '
            f'stroke="{accent}" stroke-width="3.2"/>'
        )
        for px, py in ((sx, sy), (ox, oy)):
            graph_parts.append(
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="#ffffff" stroke="{accent}" stroke-width="2"/>'
            )
        for index, (px, py, label) in enumerate(
            (
                (sx, sy, s_geom["label"]),
                (ox, oy, o_geom["label"]),
            )
        ):
            anchor = "start" if px < plot_x + plot_w / 2 else "end"
            label_x = px + 7 if anchor == "start" else px - 7
            if py < plot_y + 38:
                label_y = py + 18
            else:
                label_y = py - 8 if index == 0 else py + 18
            graph_parts.append(
                svg_outlined_text(
                    label_x,
                    label_y,
                    str(label).replace("_", " "),
                    19,
                    700,
                    accent,
                    anchor,
                )
            )
        if removed_ghost:
            ts = by_id[int(target["subject_id"])]
            to = by_id[int(target["object_id"])]
            tx1, ty1 = project(float(ts["center"][0]), float(ts["center"][1]))
            tx2, ty2 = project(float(to["center"][0]), float(to["center"][1]))
            graph_parts.append(
                f'<line x1="{tx1:.1f}" y1="{ty1:.1f}" x2="{tx2:.1f}" y2="{ty2:.1f}" '
                f'stroke="{COLORS["warn"]}" stroke-width="1.5" stroke-dasharray="5,4" opacity="0.55"/>'
            )
            mx, my = (tx1 + tx2) / 2, (ty1 + ty2) / 2
            graph_parts.extend([
                f'<line x1="{mx-5:.1f}" y1="{my-5:.1f}" x2="{mx+5:.1f}" y2="{my+5:.1f}" stroke="{COLORS["warn"]}" stroke-width="1.8"/>',
                f'<line x1="{mx-5:.1f}" y1="{my+5:.1f}" x2="{mx+5:.1f}" y2="{my-5:.1f}" stroke="{COLORS["warn"]}" stroke-width="1.8"/>',
            ])
        return graph_parts

    parts.extend(draw_graph(context["source_top"], 10, False))
    parts.extend(draw_graph(context["method_top"], 384, True))
    parts.extend([
        f'<line x1="12" y1="220" x2="708" y2="220" stroke="{COLORS["line"]}" stroke-width="1"/>',
        f'<line x1="18" y1="227" x2="18" y2="244" stroke="{COLORS["warn"]}" stroke-width="4"/>',
        svg_text(
            29,
            241,
            f'{target["subject_label"]}–{target["object_label"]}: {target["predicate"]}  '
            f'#{target["source_rank"]} → #{target["routed_rank"]}',
            17,
            700,
        ),
        f'<line x1="18" y1="250" x2="18" y2="267" stroke="{COLORS["method"]}" stroke-width="4"/>',
        svg_text(
            29,
            264,
            f'{promoted["subject_label"]}–{promoted["object_label"]}: {promoted["predicate"]}  '
            f'#{promoted["source_rank"]} → #{promoted["routed_rank"]}',
            17,
            700,
        ),
        f'<line x1="12" y1="275" x2="708" y2="275" stroke="{COLORS["grid"]}" stroke-width="1"/>',
        svg_text(20, 303, "Open3DSG, K=50", 15, 700, COLORS["muted"]),
        svg_text(
            355,
            303,
            f'Recall {100*metrics["source_recall"]:.1f} → {100*metrics["method_recall"]:.1f}%',
            17,
            700,
            COLORS["method_dark"],
            "middle",
        ),
        svg_text(
            595,
            303,
            f'Violation {100*metrics["source_violation"]:.1f} → {100*metrics["method_violation"]:.1f}%',
            17,
            700,
            COLORS["method_dark"],
            "middle",
        ),
        '</svg>',
    ])
    return "\n".join(parts)


def render_exchange_teaser(
    metrics: dict[str, float],
    context: dict[str, Any],
) -> str:
    """Render one fixed Top-50 exchange and a separate aggregate summary."""
    # The teaser is placed at 0.97 column width.  A 29-unit SVG font renders
    # slightly above the AAAI 9-pt minimum at that final placement.
    teaser_min_font = 29
    data, _ = load_preprocessed(context["scan_id"], context["subgraph_id"])
    target = context["target_removed"]
    promoted = context["promoted"]
    by_id = {
        object_id: object_geometry(data, object_id)
        for object_id in {
            int(target["subject_id"]),
            int(target["object_id"]),
            int(promoted["subject_id"]),
            int(promoted["object_id"]),
        }
    }

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="462" viewBox="0 0 720 462">',
        '<rect width="720" height="462" fill="#ffffff"/>',
    ]

    def draw_pair_panel(
        candidate: dict[str, Any],
        x: float,
        dims: tuple[int, int],
        panel_title: str,
        axis_labels: tuple[str, str],
        accent: str,
        dashed: bool,
        evidence_label: str,
        status_label: str,
    ) -> list[str]:
        subject = by_id[int(candidate["subject_id"])]
        obj = by_id[int(candidate["object_id"])]
        plot_x, plot_y, plot_w, plot_h = x, 70, 336, 182
        project, _ = make_projector(subject, obj, dims, plot_x, plot_y, plot_w, plot_h)
        sx, sy = project(
            float(subject["center"][dims[0]]), float(subject["center"][dims[1]])
        )
        ox, oy = project(
            float(obj["center"][dims[0]]), float(obj["center"][dims[1]])
        )
        dash = ' stroke-dasharray="8,6"' if dashed else ""
        panel = [
            svg_text(x, 28, panel_title, 29, 700, COLORS["ink"]),
            svg_text(
                x,
                59,
                f'{candidate["subject_label"]} {candidate["predicate"]} {candidate["object_label"]}',
                teaser_min_font,
                400,
                COLORS["ink"],
            ),
            f'<rect x="{plot_x:.1f}" y="{plot_y:.1f}" width="{plot_w:.1f}" height="{plot_h:.1f}" fill="#ffffff" stroke="{COLORS["line"]}" stroke-width="1.8"/>',
            svg_text(plot_x + 8, plot_y + 28, axis_labels[1], teaser_min_font, 400, COLORS["muted"]),
            svg_text(plot_x + plot_w - 8, plot_y + plot_h - 8, axis_labels[0], teaser_min_font, 400, COLORS["muted"], "end"),
        ]
        panel.extend(
            draw_points(
                sample_points(subject["points"], 220),
                dims,
                project,
                COLORS["subject"],
                "circle",
                0.58,
            )
        )
        panel.extend(
            draw_points(
                sample_points(obj["points"], 220),
                dims,
                project,
                COLORS["object"],
                "square",
                0.38,
            )
        )
        panel.extend(
            draw_bbox(
                subject, dims, project, COLORS["subject"], COLORS["subject_fill"]
            )
        )
        panel.extend(
            draw_bbox(
                obj,
                dims,
                project,
                COLORS["object"],
                COLORS["object_fill"],
                True,
                "square",
            )
        )
        panel.append(
            f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" '
            f'stroke="{accent}" stroke-width="3.2"{dash}/>'
        )
        mx, my = (sx + ox) / 2, (sy + oy) / 2
        if dashed:
            panel.extend(
                [
                    f'<line x1="{mx-7:.1f}" y1="{my-7:.1f}" x2="{mx+7:.1f}" y2="{my+7:.1f}" stroke="{accent}" stroke-width="2.4"/>',
                    f'<line x1="{mx-7:.1f}" y1="{my+7:.1f}" x2="{mx+7:.1f}" y2="{my-7:.1f}" stroke="{accent}" stroke-width="2.4"/>',
                ]
            )
        else:
            panel.append(
                f'<path d="M {mx:.1f} {my-7:.1f} L {mx+7:.1f} {my:.1f} L {mx:.1f} {my+7:.1f} L {mx-7:.1f} {my:.1f} Z" fill="#ffffff" stroke="{accent}" stroke-width="2.4"/>'
            )
        panel.extend(
            [
                svg_text(
                    x,
                    284,
                    f'Rank {candidate["source_rank"]}  →  {candidate["routed_rank"]}',
                    30,
                    700,
                    COLORS["ink"],
                ),
                svg_text(x, 316, evidence_label, teaser_min_font, 700, accent),
                svg_text(x, 344, status_label, teaser_min_font, 700, accent),
            ]
        )
        return panel

    target_delta = f'{float(target["center_delta_z"]):.2f}'.replace("-", "−")

    parts.extend(
        draw_pair_panel(
            target,
            12,
            (0, 2),
            "(a) Leaves Top-50",
            ("x", "z"),
            COLORS["warn"],
            True,
            f'Δz = {target_delta} m',
            "verifier-violated",
        )
    )
    parts.extend(
        draw_pair_panel(
            promoted,
            372,
            (0, 1),
            "(b) Enters Top-50",
            ("x", "y"),
            COLORS["method_dark"],
            False,
            f'XY distance = {float(promoted["distance_xy"]):.2f} m',
            "exact-label GT",
        )
    )
    parts.extend(
        [
            f'<line x1="12" y1="360" x2="708" y2="360" stroke="{COLORS["line"]}" stroke-width="1.8"/>',
            svg_text(
                360,
                390,
                "Open3DSG aggregate (548 contexts), K=50",
                teaser_min_font,
                700,
                COLORS["muted"],
                "middle",
            ),
            svg_text(
                360,
                421,
                f'Recall: {100*metrics["source_recall"]:.1f} → {100*metrics["method_recall"]:.1f}%',
                teaser_min_font,
                700,
                COLORS["method_dark"],
                "middle",
            ),
            svg_text(
                360,
                452,
                f'Violation: {100*metrics["source_violation"]:.1f} → {100*metrics["method_violation"]:.1f}%',
                teaser_min_font,
                700,
                COLORS["method_dark"],
                "middle",
            ),
            "</svg>",
        ]
    )
    return "\n".join(parts)


def render_camera_ready_framework(cases: dict[str, dict[str, Any]]) -> str:
    """Render the established framework content with 9-pt-safe callouts."""
    row = cases["open3dsg_case_001"]
    pred = row["source_prediction"]
    data, _ = load_preprocessed(pred["scan_id"], pred["subgraph_id"])
    subject = object_geometry(data, int(pred["subject_id"]))
    obj = object_geometry(data, int(pred["object_id"]))
    project, _ = make_projector(subject, obj, (0, 1), 20, 62, 380, 270)
    sx, sy = project(float(subject["center"][0]), float(subject["center"][1]))
    ox, oy = project(float(obj["center"][0]), float(obj["center"][1]))

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="520" viewBox="0 0 1440 520">',
        '<rect width="1440" height="520" fill="#ffffff"/>',
        f'<defs><marker id="framework-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{COLORS["axis"]}"/></marker></defs>',
        f'<line x1="420" y1="12" x2="420" y2="508" stroke="{COLORS["grid"]}" stroke-width="1.6"/>',
        f'<line x1="1040" y1="12" x2="1040" y2="508" stroke="{COLORS["grid"]}" stroke-width="1.6"/>',
        svg_text(20, 38, "(a) Failure example", 31, 700),
        svg_text(450, 38, "(b) Compatibility and score", 31, 700),
        svg_text(1065, 38, "(c) Re-ranking", 31, 700),
        f'<rect x="20" y="62" width="380" height="270" fill="#ffffff" stroke="{COLORS["line"]}" stroke-width="1.8"/>',
        svg_text(28, 94, "y", 27, 400, COLORS["muted"]),
        svg_text(392, 322, "x", 27, 400, COLORS["muted"], "end"),
    ]
    parts.extend(draw_points(subject["sample"], (0, 1), project, COLORS["subject"], "circle", 0.62))
    parts.extend(draw_points(obj["sample"], (0, 1), project, COLORS["object"], "square", 0.32))
    parts.extend(draw_bbox(subject, (0, 1), project, COLORS["subject"], COLORS["subject_fill"]))
    parts.extend(draw_bbox(obj, (0, 1), project, COLORS["object"], COLORS["object_fill"], True, "square"))
    parts.extend(
        [
            f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" stroke="{COLORS["axis"]}" stroke-width="2" stroke-dasharray="8,6"/>',
            svg_text(20, 374, "heater  close by  trash can", 28, 700),
            svg_text(20, 412, "Open3DSG: Z=.853; rank 19", 27, 400, COLORS["muted"]),
            f'<line x1="20" y1="436" x2="20" y2="478" stroke="{COLORS["warn"]}" stroke-width="4"/>',
            svg_text(35, 468, "XY distance: 4.33 m", 29, 700),
        ]
    )

    def input_box(x: int, y: int, w: int, h: int, title: str, details: list[str]) -> list[str]:
        box_parts = [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#ffffff" stroke="{COLORS["object"]}" stroke-width="1.8"/>',
            svg_text(x + 14, y + 34, title, 28, 700),
        ]
        for index, detail in enumerate(details):
            box_parts.append(svg_text(x + 14, y + 68 + 31 * index, detail, 27, 400, COLORS["muted"]))
        return box_parts

    parts.extend(input_box(450, 70, 225, 92, "Predicate T", ["close by"]))
    parts.extend(input_box(450, 188, 225, 124, "Geometry G", ["distance / dz", "overlap"]))
    parts.extend(input_box(450, 370, 225, 100, "Score Z", ["ranking only"]))
    parts.extend(
        [
            f'<line x1="675" y1="116" x2="685" y2="145" stroke="{COLORS["axis"]}" stroke-width="2" marker-end="url(#framework-arrow)"/>',
            f'<line x1="675" y1="250" x2="685" y2="220" stroke="{COLORS["axis"]}" stroke-width="2" marker-end="url(#framework-arrow)"/>',
            f'<rect x="685" y="88" width="330" height="230" rx="4" fill="#ffffff" stroke="{COLORS["method"]}" stroke-width="2"/>',
            f'<line x1="685" y1="88" x2="1015" y2="88" stroke="{COLORS["method"]}" stroke-width="4"/>',
            svg_text(860, 128, "Compatibility", 30, 700, COLORS["method_dark"], "middle"),
            svg_ctr_text(860, 168, "", "(T,G)", 30, 700, COLORS["method_dark"], "middle"),
            svg_text(860, 215, "linked-pair ordering", 27, 400, COLORS["muted"], "middle"),
            svg_text(860, 250, "transformation averaging", 27, 400, COLORS["muted"], "middle"),
            svg_ctr_text(860, 295, "", "(T,G)=0.003", 29, 700, COLORS["method_dark"], "middle"),
            f'<line x1="860" y1="318" x2="860" y2="365" stroke="{COLORS["axis"]}" stroke-width="2" marker-end="url(#framework-arrow)"/>',
            f'<line x1="675" y1="420" x2="685" y2="420" stroke="{COLORS["axis"]}" stroke-width="2" marker-end="url(#framework-arrow)"/>',
            f'<rect x="685" y="370" width="330" height="100" rx="4" fill="#ffffff" stroke="{COLORS["axis"]}" stroke-width="1.8"/>',
            svg_text(860, 407, "Within-family score", 28, 700, COLORS["muted"], "middle"),
            svg_ctr_text(860, 451, "u = Z × ", "(T,G)", 30, 700, COLORS["ink"], "middle"),
            f'<line x1="1015" y1="420" x2="1060" y2="260" stroke="{COLORS["axis"]}" stroke-width="2" marker-end="url(#framework-arrow)"/>',
        ]
    )

    parts.extend(
        [
            svg_text(1100, 112, "19", 48, 700, COLORS["muted"], "middle"),
            svg_text(1100, 145, "source rank", 27, 400, COLORS["muted"], "middle"),
            f'<line x1="1160" y1="105" x2="1260" y2="105" stroke="{COLORS["axis"]}" stroke-width="2.4" marker-end="url(#framework-arrow)"/>',
            svg_text(1340, 112, "178", 48, 700, COLORS["method"], "middle"),
            svg_text(1340, 145, "RelCompat3D", 27, 400, COLORS["muted"], "middle"),
            f'<rect x="1065" y="175" width="350" height="214" rx="4" fill="#ffffff" stroke="{COLORS["method"]}" stroke-width="2"/>',
            svg_text(1240, 211, "Family-aware", 28, 700, COLORS["method_dark"], "middle"),
            svg_text(1240, 242, "re-ranking", 28, 700, COLORS["method_dark"], "middle"),
            f'<line x1="1082" y1="254" x2="1398" y2="254" stroke="{COLORS["grid"]}" stroke-width="1.6"/>',
            svg_text(1240, 286, "proximity / vertical", 27, 400, COLORS["ink"], "middle"),
            svg_ctr_text(1240, 317, "Z × ", "", 28, 700, COLORS["ink"], "middle"),
            svg_text(1240, 349, "support/contact", 27, 400, COLORS["ink"], "middle"),
            svg_text(1240, 379, "keep source order", 27, 400, COLORS["ink"], "middle"),
            f'<line x1="1065" y1="410" x2="1415" y2="410" stroke="{COLORS["line"]}" stroke-width="1.8"/>',
            svg_text(1240, 446, "Joint evaluation", 29, 700, COLORS["ink"], "middle"),
            svg_text(1125, 488, "Recall@K ↑", 28, 700, COLORS["ink"], "middle"),
            svg_text(1340, 488, "Violation@K ↓", 28, 700, COLORS["ink"], "middle"),
            "</svg>",
        ]
    )
    return "\n".join(parts)


def render_camera_ready_qualitative(
    cases: dict[str, dict[str, Any]],
) -> tuple[str, list[dict[str, Any]]]:
    """Render the established three qualitative cases with readable labels."""
    width, height = 1440, 660
    positions = (10, 490, 970)
    titles = {
        "open3dsg_case_001": "(a) Proximity correction",
        "open3dsg_case_019": "(b) Vertical correction",
        "open3dsg_case_026": "(c) Contact residual",
    }
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="1440" height="660" fill="#ffffff"/>',
        f'<line x1="480" y1="8" x2="480" y2="652" stroke="{COLORS["grid"]}" stroke-width="1.6"/>',
        f'<line x1="960" y1="8" x2="960" y2="652" stroke="{COLORS["grid"]}" stroke-width="1.6"/>',
    ]
    records: list[dict[str, Any]] = []
    for case_id, x in zip(EXPECTED_CASES, positions):
        row = cases[case_id]
        pred = row["source_prediction"]
        data, _ = load_preprocessed(pred["scan_id"], pred["subgraph_id"])
        subject = object_geometry(data, int(pred["subject_id"]))
        obj = object_geometry(data, int(pred["object_id"]))
        dims, x_label, y_label, _ = panel_dims(case_id, subject, obj)
        measure = measurements(subject, obj)
        project, _ = make_projector(subject, obj, dims, x + 8, 112, 444, 250)
        sx, sy = project(float(subject["center"][dims[0]]), float(subject["center"][dims[1]]))
        ox, oy = project(float(obj["center"][dims[0]]), float(obj["center"][dims[1]]))
        relation = f'{pred["subject_label"]} / {pred["predicate_label"]} / {pred["object_label"]}'
        parts.extend(
            [
                svg_text(x + 4, 38, titles[case_id], 31, 700),
                svg_text(x + 4, 78, relation, 28, 400, COLORS["ink"]),
                f'<rect x="{x+8}" y="112" width="444" height="250" fill="#ffffff" stroke="{COLORS["line"]}" stroke-width="1.8"/>',
                svg_text(x + 18, 143, y_label, 27, 400, COLORS["muted"]),
                svg_text(x + 442, 352, x_label, 27, 400, COLORS["muted"], "end"),
            ]
        )
        parts.extend(draw_points(subject["sample"], dims, project, COLORS["subject"], "circle", 0.62))
        parts.extend(draw_points(obj["sample"], dims, project, COLORS["object"], "square", 0.32))
        parts.extend(draw_bbox(subject, dims, project, COLORS["subject"], COLORS["subject_fill"]))
        parts.extend(draw_bbox(obj, dims, project, COLORS["object"], COLORS["object_fill"], True, "square"))
        parts.append(
            f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ox:.1f}" y2="{oy:.1f}" stroke="{COLORS["axis"]}" stroke-width="2" stroke-dasharray="8,6"/>'
        )
        if case_id == "open3dsg_case_001":
            measure_title, measure_value = "XY center distance", f'{measure["xy_center_distance"]:.2f} m'
            evidence = "large separation for close by"
            outcome = "Demoted: proximity"
        elif case_id == "open3dsg_case_019":
            measure_title, measure_value = "subject−object center Δz", f'{measure["z_center_delta_subject_minus_object"]:.2f} m'.replace("-", "−")
            evidence = "subject lies below the object"
            outcome = "Demoted: vertical order"
        else:
            measure_title, measure_value = "vertical bottom−top gap", f'{measure["subject_bottom_minus_object_top"]:.2f} m'.replace("-", "−")
            evidence = "contact remains unresolved"
            outcome = "Kept in source order"
        score = row["structured_product"]
        accent = COLORS["method"] if case_id != "open3dsg_case_026" else COLORS["residual"]
        score_label = (
            f'Z={score["source_score"]:.3f}; Ctr={score["compatibility"]:.3f}'
            if case_id != "open3dsg_case_026"
            else f'Z={score["source_score"]:.3f}; source order'
        )
        parts.extend(
            [
                f'<line x1="{x+8}" y1="390" x2="{x+452}" y2="390" stroke="{COLORS["line"]}" stroke-width="1.8"/>',
                svg_text(x + 8, 427, "Measured evidence", 28, 700, COLORS["muted"]),
                svg_text(x + 8, 466, measure_title, 28, 700, COLORS["ink"]),
                svg_text(x + 8, 501, measure_value, 29, 700, COLORS["ink"]),
                svg_text(x + 8, 535, evidence, 27, 400, COLORS["muted"]),
                f'<line x1="{x+8}" y1="554" x2="{x+452}" y2="554" stroke="{COLORS["line"]}" stroke-width="1.8"/>',
                svg_text(x + 8, 590, f'Rank {score["source_rank"]} → {score["routed_rank"]}', 30, 700, COLORS["ink"]),
                svg_text(x + 8, 621, score_label, 27, 400, COLORS["muted"]),
                f'<line x1="{x+8}" y1="630" x2="{x+8}" y2="657" stroke="{accent}" stroke-width="4"/>',
                svg_text(x + 22, 654, outcome, 27, 700, COLORS["ink"]),
            ]
        )
        _, record = draw_case_panel(case_id, row, x, 0, 460, 528)
        records.append(record)
    parts.append("</svg>")
    return "\n".join(parts), records


def render_figure(cases: dict[str, dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    width, height = 1440, 540
    panel_w, panel_h = 460, 528
    positions = [(10, 6), (490, 6), (970, 6)]
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="540" viewBox="0 0 1440 540">',
        '<rect width="1440" height="540" fill="#ffffff"/>',
        f'<line x1="480" y1="8" x2="480" y2="532" stroke="{COLORS["grid"]}" stroke-width="1"/>',
        f'<line x1="960" y1="8" x2="960" y2="532" stroke="{COLORS["grid"]}" stroke-width="1"/>',
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


def enforce_minimum_stroke(svg: str) -> str:
    """Enforce the 0.5-pt print minimum at the locked manuscript widths."""
    for width in ("0.9", "1", "1.2", "1.25", "1.4", "1.5"):
        svg = svg.replace(f'stroke-width="{width}"', 'stroke-width="1.6"')
    return svg


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
        "- `teaser_overview.{svg,pdf,png}`: fixed pair-level Top-50 exchange and separately labeled aggregate result for the optional first-page teaser.",
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
        f"- Teaser PDF exists: `{manifest['outputs']['teaser_pdf_exists']}`",
        f"- Teaser exchange checks: `{manifest['teaser_context']['validations']}`",
        f"- Output case JSON exists: `{manifest['outputs']['cases_json_exists']}`",
    ]
    report.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cases = load_queue_cases()
    missing = [case_id for case_id in EXPECTED_CASES if case_id not in cases]
    if missing:
        raise SystemExit(f"Missing locked cases in {QUEUE_JSONL}: {missing}")
    teaser_context = attach_structured_product_ranks(cases)

    svg, records = render_camera_ready_qualitative(cases)
    framework_svg = render_camera_ready_framework(cases)
    teaser_metrics = load_teaser_metrics()
    teaser_svg = render_exchange_teaser(teaser_metrics, teaser_context)
    svg_path = OUT_DIR / "figure3_geometry_panels.svg"
    framework_path = OUT_DIR / "figure1_framework.svg"
    teaser_path = OUT_DIR / "teaser_overview.svg"
    cases_path = OUT_DIR / "figure3_geometry_cases.json"
    manifest_path = OUT_DIR / "figure3_geometry_manifest.json"

    svg_path.write_text(enforce_minimum_stroke(svg))
    framework_path.write_text(enforce_minimum_stroke(framework_svg))
    teaser_path.write_text(enforce_minimum_stroke(teaser_svg))
    convert_svg("figure1_framework")
    convert_svg("figure3_geometry_panels")
    convert_svg("teaser_overview")
    cases_path.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")

    rendered_case_ids = [record["case_id"] for record in records]
    manifest = {
        "schema_version": "h001_geometry_figures_v6",
        "created_at": now_iso(),
        "status": "figure3_geometry_panels_generated_verified",
        "source_queue_jsonl": str(QUEUE_JSONL.relative_to(ROOT)),
        "structured_model_json": str(STRUCTURED_MODEL_JSON.relative_to(ROOT)),
        "paper_score": "family-aware relation-consistent product",
        "preprocessed_root": str(PREPROCESSED_ROOT.relative_to(ROOT)),
        "expected_case_ids": EXPECTED_CASES,
        "rendered_case_ids": rendered_case_ids,
        "missing_case_ids": [case_id for case_id in EXPECTED_CASES if case_id not in rendered_case_ids],
        "outputs": {
            "figure1_svg": str(framework_path.relative_to(ROOT)),
            "figure1_pdf": str((OUT_DIR / "figure1_framework.pdf").relative_to(ROOT)),
            "figure3_svg": str(svg_path.relative_to(ROOT)),
            "figure3_pdf": str((OUT_DIR / "figure3_geometry_panels.pdf").relative_to(ROOT)),
            "teaser_svg": str(teaser_path.relative_to(ROOT)),
            "teaser_pdf": str((OUT_DIR / "teaser_overview.pdf").relative_to(ROOT)),
            "cases_json": str(cases_path.relative_to(ROOT)),
            "manifest_json": str(manifest_path.relative_to(ROOT)),
            "figure1_pdf_exists": (OUT_DIR / "figure1_framework.pdf").exists(),
            "figure3_pdf_exists": (OUT_DIR / "figure3_geometry_panels.pdf").exists(),
            "teaser_pdf_exists": (OUT_DIR / "teaser_overview.pdf").exists(),
            "cases_json_exists": cases_path.exists(),
        },
        "teaser_metrics": teaser_metrics,
        "teaser_context": {
            "scan_id": teaser_context["scan_id"],
            "subgraph_id": teaser_context["subgraph_id"],
            "k": teaser_context["k"],
            "target_removed": teaser_context["target_removed"],
            "promoted": teaser_context["promoted"],
            "validations": teaser_context["validations"],
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
