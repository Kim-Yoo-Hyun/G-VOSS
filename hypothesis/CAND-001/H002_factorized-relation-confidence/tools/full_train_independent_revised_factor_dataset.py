#!/usr/bin/env python3
"""Materialize H002 revised factor inputs for the train-only controlled slice."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import factor_smoke as smoke


H002_ROOT = Path(__file__).resolve().parents[1]
FULL_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full"
RGA_ROOT = FULL_ROOT / "rga"
DEFAULT_ROWS = RGA_ROOT / "independent_controlled_posterior_smoke_codex_ver/controlled_posterior_rows.jsonl"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_DESIGN = RGA_ROOT / "independent_factor_revision_design_codex_ver/summary.json"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "independent_revised_factor_dataset_codex_ver"

REVISED_VIEWS = [
    "D1_revised_residual_base",
    "D2_support_contact_split_residual",
    "D3_relative_vertical_order_residual",
    "D4_coverage_uncertainty_shrinkage",
]

RAW_FIELDS = [
    "center_delta_z",
    "distance_3d",
    "distance_xy",
    "normalized_center_delta_z",
    "normalized_distance_3d",
    "normalized_distance_xy",
    "object_bottom_z",
    "object_top_z",
    "projected_iou_xy",
    "projected_object_overlap_ratio",
    "projected_subject_overlap_ratio",
    "subject_bottom_z",
    "subject_top_z",
    "vertical_gap_subject_on_object",
]

FORBIDDEN_FEATURE_KEY_FRAGMENTS = [
    "label_match",
    "proposed_audit_role",
    "queue_kind",
    "rank_band",
    "geometry_status",
    "reviewer",
    "labeler_confidence",
    "label_confidence",
    "human_confirmed",
    "paper_locked",
    "target_slice",
]

FLOOR_LIKE_TERMS = ("floor", "ground", "stair", "step", "platform", "base")
SUPPORT_SURFACE_TERMS = (
    "table",
    "desk",
    "shelf",
    "counter",
    "cabinet",
    "chair",
    "bed",
    "sofa",
    "bench",
    "stand",
    "rack",
    "sink",
    "toilet",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, default=DEFAULT_ROWS)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--design", type=Path, default=DEFAULT_DESIGN)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def read_json(path: Path) -> dict[str, Any]:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def clip(value: float, left: float = 0.0, right: float = 1.0) -> float:
    return min(max(value, left), right)


def safe_float(value: Any, default: float = 0.0) -> float:
    return smoke.safe_float(value, default)


def read_rows(path: Path) -> list[dict[str, Any]]:
    return smoke.read_jsonl(path)


def prediction_id(row: dict[str, Any]) -> str:
    return str(row["identity"]["prediction_id"])


def iter_jsonl(path: Path) -> Any:
    with smoke.as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


def collect_match_rows(path: Path, wanted_ids: set[str]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    matched: dict[str, dict[str, Any]] = {}
    scanned = 0
    for scanned, row in enumerate(iter_jsonl(path), start=1):
        row_id = str(row.get("identity", {}).get("prediction_id", ""))
        if row_id in wanted_ids:
            matched[row_id] = row
            if len(matched) == len(wanted_ids):
                break
    return matched, {
        "match_rows_path": smoke.rel_path(path),
        "wanted_ids": len(wanted_ids),
        "matched_ids": len(matched),
        "missing_ids": len(wanted_ids) - len(matched),
        "rows_scanned_until_complete": scanned,
    }


def has_term(label: str, terms: tuple[str, ...]) -> bool:
    lowered = label.lower()
    return any(term in lowered for term in terms)


def expected_vertical_sign(predicate_label: str) -> float:
    label = predicate_label.lower()
    if "higher" in label or "above" in label:
        return 1.0
    if "lower" in label or "below" in label or "under" in label:
        return -1.0
    return 0.0


def base_features(row: dict[str, Any], match_row: dict[str, Any] | None) -> dict[str, float]:
    base = row["baseline_inputs"]["factorized_reliability_posterior"]
    geom = (match_row or {}).get("geometry") or {}
    raw = geom.get("raw_features") or {}
    semantic = safe_float(base.get("semantic_score_norm"))
    p_geom = safe_float(base.get("p_geom_valid"), 0.5)
    consistency = safe_float(base.get("consistency_score"), 0.0)
    disagreement = abs(semantic - p_geom)
    rank = max(safe_float(base.get("semantic_rank"), 1.0), 1.0)
    out = {
        "semantic_score_norm": semantic,
        "semantic_score_raw": safe_float(base.get("semantic_score_raw")),
        "negative_semantic_score_norm": 1.0 - semantic,
        "semantic_rank": rank,
        "semantic_rank_log": math.log1p(rank),
        "semantic_rank_inverse": 1.0 / rank,
        "p_geom_valid": p_geom,
        "p_geom_invalid": 1.0 - p_geom,
        "consistency_score": consistency,
        "absolute_disagreement": disagreement,
        "semantic_minus_geometry": semantic - p_geom,
        "geometry_minus_semantic": p_geom - semantic,
        "underconfidence_score": max(0.0, p_geom - semantic),
        "overconfidence_score": max(0.0, semantic - p_geom),
        "semantic_x_geometry": semantic * p_geom,
        "semantic_x_consistency": semantic * consistency,
        "geometry_x_consistency": p_geom * consistency,
        "geometry_available_flag": 1.0 if geom.get("geometry_available") else 0.0,
        "geometry_checkable_flag": 1.0 if geom.get("geometry_checkable") else 0.0,
        "raw_feature_present": 1.0 if raw else 0.0,
        "unsupported_family_flag": 1.0 if not raw else 0.0,
        "near_boundary_uncertainty": 1.0 - 2.0 * abs(p_geom - 0.5),
        "disagreement_uncertainty": disagreement,
    }
    for field in RAW_FIELDS:
        out[f"raw_{field}"] = safe_float(raw.get(field), 0.0)
    return out


def support_contact_features(row: dict[str, Any], base: dict[str, float]) -> dict[str, float]:
    identity = row["identity"]
    family = str(identity["predicate_family"])
    gate = 1.0 if family == "support_contact" else 0.0
    object_label = str(identity.get("object_label", ""))
    subject_label = str(identity.get("subject_label", ""))
    vertical_gap = base["raw_vertical_gap_subject_on_object"]
    subj_overlap = base["raw_projected_subject_overlap_ratio"]
    obj_overlap = base["raw_projected_object_overlap_ratio"]
    iou = base["raw_projected_iou_xy"]
    xy_overlap = max(subj_overlap, obj_overlap, iou)
    floor_like_object = 1.0 if has_term(object_label, FLOOR_LIKE_TERMS) else 0.0
    surface_like_object = 1.0 if has_term(object_label, SUPPORT_SURFACE_TERMS) else 0.0
    floor_like_subject = 1.0 if has_term(subject_label, FLOOR_LIKE_TERMS) else 0.0
    weak_contact = 1.0 if abs(vertical_gap) <= 0.10 and xy_overlap >= 0.05 else 0.0
    return {
        "support_contact_gate": gate,
        "support_contact_x_contact_gap_abs": gate * abs(vertical_gap),
        "support_contact_x_penetration_proxy": gate * max(0.0, -vertical_gap),
        "support_contact_x_above_support_gap": gate * max(0.0, vertical_gap),
        "support_contact_x_xy_support_overlap": gate * xy_overlap,
        "support_contact_x_projected_subject_overlap_ratio": gate * subj_overlap,
        "support_contact_x_projected_object_overlap_ratio": gate * obj_overlap,
        "support_contact_x_normalized_distance_xy": gate * base["raw_normalized_distance_xy"],
        "support_contact_x_floor_like_support_flag": gate * floor_like_object,
        "support_contact_x_surface_like_support_flag": gate * surface_like_object,
        "support_contact_x_subject_floor_like_flag": gate * floor_like_subject,
        "support_contact_x_weak_contact_flag": gate * weak_contact,
        "support_contact_x_far_xy_risk": gate * clip(base["raw_normalized_distance_xy"]),
    }


def relative_vertical_features(row: dict[str, Any], base: dict[str, float]) -> dict[str, float]:
    identity = row["identity"]
    family = str(identity["predicate_family"])
    gate = 1.0 if family == "relative_vertical" else 0.0
    expected_sign = expected_vertical_sign(str(identity["predicate_label"]))
    norm_delta = base["raw_normalized_center_delta_z"]
    center_delta = base["raw_center_delta_z"]
    signed_margin = expected_sign * norm_delta
    signed_clearance = expected_sign * center_delta
    sign_agreement = 1.0 if expected_sign != 0.0 and signed_margin > 0.0 else 0.0
    conflict = 1.0 if expected_sign != 0.0 and signed_margin <= 0.0 else 0.0
    return {
        "relative_vertical_gate": gate,
        "relative_vertical_x_expected_z_sign": gate * expected_sign,
        "relative_vertical_x_signed_margin": gate * signed_margin,
        "relative_vertical_x_sign_agreement": gate * sign_agreement,
        "relative_vertical_x_sign_conflict": gate * conflict,
        "relative_vertical_x_vertical_margin_abs": gate * abs(norm_delta),
        "relative_vertical_x_vertical_clearance": gate * signed_clearance,
        "relative_vertical_x_projected_iou_xy": gate * base["raw_projected_iou_xy"],
        "relative_vertical_x_center_delta_z": gate * center_delta,
        "relative_vertical_x_normalized_center_delta_z": gate * norm_delta,
    }


def coverage_features(row: dict[str, Any], base: dict[str, float]) -> dict[str, float | str]:
    identity = row["identity"]
    family = str(identity["predicate_family"])
    coverage = base["geometry_available_flag"] * base["geometry_checkable_flag"] * base["raw_feature_present"]
    unsupported = 1.0 - coverage
    uncertainty = clip((base["near_boundary_uncertainty"] + base["absolute_disagreement"] + unsupported) / 3.0)
    return {
        "predicate_family": family,
        "family_support_contact": 1.0 if family == "support_contact" else 0.0,
        "family_relative_vertical": 1.0 if family == "relative_vertical" else 0.0,
        "family_proximity": 1.0 if family == "proximity" else 0.0,
        "coverage_flag": coverage,
        "raw_geometry_missing_flag": 1.0 - base["raw_feature_present"],
        "unsupported_family_flag": unsupported,
        "near_boundary_uncertainty": base["near_boundary_uncertainty"],
        "disagreement_uncertainty": base["absolute_disagreement"],
        "coverage_x_abs_disagreement": coverage * base["absolute_disagreement"],
        "coverage_x_p_geom_valid": coverage * base["p_geom_valid"],
        "uncertainty_x_geometry_minus_semantic": uncertainty * base["geometry_minus_semantic"],
        "uncertainty_x_semantic_minus_geometry": uncertainty * base["semantic_minus_geometry"],
        "family_shrinkage_gate": coverage,
    }


def materialize_row(row: dict[str, Any], match_row: dict[str, Any] | None) -> dict[str, Any]:
    row = json.loads(json.dumps(row))
    base = base_features(row, match_row)
    support = support_contact_features(row, base)
    vertical = relative_vertical_features(row, base)
    coverage = coverage_features(row, base)
    baseline_inputs = dict(row["baseline_inputs"])
    baseline_inputs["D1_revised_residual_base"] = dict(base)
    baseline_inputs["D2_support_contact_split_residual"] = {**base, **support}
    baseline_inputs["D3_relative_vertical_order_residual"] = {**base, **vertical}
    baseline_inputs["D4_coverage_uncertainty_shrinkage"] = {**base, **support, **vertical, **coverage}
    row["baseline_inputs"] = baseline_inputs
    row["record_type"] = "h002_full_train_independent_revised_factor_row"
    row["schema_version"] = "h002_full_train_independent_revised_factor_row_v0"
    row["provenance"] = {
        **row.get("provenance", {}),
        "revised_factor_dataset": "independent_revised_factor_dataset_codex_ver",
        "raw_geometry_joined": match_row is not None,
        "hidden_metadata_as_model_input": False,
        "geometry_status_as_model_input": False,
        "multi_view_as_model_input": False,
    }
    return row


def feature_schema(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for view in REVISED_VIEWS:
        numeric_keys: set[str] = set()
        categorical_keys: dict[str, set[str]] = {}
        for row in rows:
            for key, value in row["baseline_inputs"][view].items():
                if isinstance(value, (int, float, bool)) or value is None:
                    numeric_keys.add(key)
                else:
                    categorical_keys.setdefault(key, set()).add(str(value))
        out.append(
            {
                "view": view,
                "numeric_feature_count": len(numeric_keys),
                "categorical_feature_count": sum(len(values) for values in categorical_keys.values()),
                "numeric_features": ",".join(sorted(numeric_keys)),
                "categorical_features": ",".join(
                    f"{key}={ '|'.join(sorted(values)) }" for key, values in sorted(categorical_keys.items())
                ),
            }
        )
    return out


def leakage_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    hits = []
    for row in rows:
        row_id = prediction_id(row)
        for view in REVISED_VIEWS:
            for key in row["baseline_inputs"][view]:
                for fragment in FORBIDDEN_FEATURE_KEY_FRAGMENTS:
                    if fragment in key:
                        hits.append({"prediction_id": row_id, "view": view, "feature_key": key, "fragment": fragment})
    return {
        "schema_version": "h002_revised_factor_leakage_report_v0",
        "checked_views": REVISED_VIEWS,
        "forbidden_fragments": FORBIDDEN_FEATURE_KEY_FRAGMENTS,
        "forbidden_feature_key_hits": hits,
        "forbidden_hit_count": len(hits),
        "target_hidden_fields_present_but_not_model_input": [
            "geometry_status_hidden",
            "label_match_status_hidden",
            "proposed_audit_role_hidden",
            "queue_kind_hidden",
            "rank_band_hidden",
        ],
    }


def summarize(rows: list[dict[str, Any]], matched: dict[str, dict[str, Any]], join_manifest: dict[str, Any]) -> dict[str, Any]:
    family_counts = Counter(str(row["identity"]["predicate_family"]) for row in rows)
    target_counts = Counter(str(row["target"]["y"]) for row in rows)
    raw_counts = Counter()
    for row in rows:
        view = row["baseline_inputs"]["D1_revised_residual_base"]
        family = str(row["identity"]["predicate_family"])
        if view["raw_feature_present"] == 1.0:
            raw_counts[family] += 1
    return {
        "row_count": len(rows),
        "unique_prediction_ids": len({prediction_id(row) for row in rows}),
        "family_counts": dict(sorted(family_counts.items())),
        "target_counts": dict(sorted(target_counts.items())),
        "raw_feature_rows_by_family": dict(sorted(raw_counts.items())),
        "join_manifest": join_manifest,
        "matched_ids": len(matched),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    ds = summary["dataset_summary"]
    leak = summary["leakage_report"]
    lines = [
        "# H002 Full Train Independent Revised Factor Dataset",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Boundary",
        "",
        "- Train-only dataset materialization.",
        "- No model is trained here.",
        "- No validation/test rows are used.",
        "- Hidden audit metadata is not materialized inside revised factor views.",
        "- Multi-view remains audit evidence only.",
        "- `geometry_status` is not used as a model feature.",
        "",
        "## Dataset",
        "",
        f"- Rows: `{ds['row_count']}`",
        f"- Unique prediction ids: `{ds['unique_prediction_ids']}`",
        f"- Matched raw geometry ids: `{ds['matched_ids']}`",
        f"- Match rows scanned: `{ds['join_manifest']['rows_scanned_until_complete']}`",
        "",
        "## Family Counts",
        "",
        "| Family | Rows | Raw Feature Rows |",
        "| --- | ---: | ---: |",
    ]
    for family, count in ds["family_counts"].items():
        lines.append(f"| `{family}` | {count} | {ds['raw_feature_rows_by_family'].get(family, 0)} |")
    lines.extend(
        [
            "",
            "## Revised Views",
            "",
        ]
    )
    for view in REVISED_VIEWS:
        lines.append(f"- `{view}`")
    lines.extend(
        [
            "",
            "## Leakage Check",
            "",
            f"Forbidden feature key hits: `{leak['forbidden_hit_count']}`",
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def write_outputs(output_dir: Path, summary: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    smoke.write_json(output_dir / "summary.json", summary)
    smoke.write_jsonl(output_dir / "revised_factor_rows.jsonl", rows)
    smoke.write_jsonl(output_dir / "feature_audit_sample.jsonl", rows[:10])
    smoke.write_json(output_dir / "join_manifest.json", summary["dataset_summary"]["join_manifest"])
    smoke.write_json(output_dir / "leakage_report.json", summary["leakage_report"])
    smoke.write_json(output_dir / "smoke_plan.json", summary["smoke_plan"])
    write_csv(
        output_dir / "feature_schema.csv",
        summary["feature_schema"],
        ["view", "numeric_feature_count", "categorical_feature_count", "numeric_features", "categorical_features"],
    )
    write_report(output_dir / "report.md", summary)


def run(args: argparse.Namespace) -> dict[str, Any]:
    design = read_json(args.design)
    input_rows = read_rows(args.rows)
    wanted_ids = {prediction_id(row) for row in input_rows}
    matched, join_manifest = collect_match_rows(args.match_rows, wanted_ids)
    materialized_rows = [materialize_row(row, matched.get(prediction_id(row))) for row in input_rows]
    leak = leakage_report(materialized_rows)
    schema = feature_schema(materialized_rows)
    output_dir = smoke.as_abs(args.output_dir)
    summary = {
        "schema_version": "h002_full_train_independent_revised_factor_dataset_summary_v0",
        "status": "full_train_independent_revised_factor_dataset_ready",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": {
            "rows": smoke.rel_path(args.rows),
            "match_rows": smoke.rel_path(args.match_rows),
            "design": smoke.rel_path(args.design),
            "design_status": design.get("status"),
        },
        "output_dir": smoke.rel_path(output_dir),
        "boundary": {
            "split": "train_only",
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "hidden_metadata_as_model_input": False,
            "geometry_status_as_model_input": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
            "posterior_performance_claim_allowed": False,
        },
        "revised_views": REVISED_VIEWS,
        "dataset_summary": summarize(materialized_rows, matched, join_manifest),
        "feature_schema": schema,
        "leakage_report": leak,
        "smoke_plan": {
            "next_todo": "full_train_independent_revised_factor_smoke",
            "row_artifact": smoke.rel_path(output_dir / "revised_factor_rows.jsonl"),
            "baseline_views": [
                "semantic_only",
                "geometry_only",
                "semantic_plus_geometry",
                "current_factorized_reliability_posterior",
            ],
            "revised_views": REVISED_VIEWS,
            "controls": design.get("next_smoke_plan", {}).get("controls", []),
        },
        "claim_boundary": {
            "allowed": "Revised deployable factor dataset is ready for train-only smoke.",
            "blocked": "No posterior performance claim is allowed before revised factor smoke.",
        },
        "next_todo": "full_train_independent_revised_factor_smoke",
    }
    write_outputs(output_dir, summary, materialized_rows)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    ds = summary["dataset_summary"]
    print(
        "status={status} rows={rows} matched={matched} forbidden_hits={hits} "
        "validation_used={validation_used} next={next_todo}".format(
            status=summary["status"],
            rows=ds["row_count"],
            matched=ds["matched_ids"],
            hits=summary["leakage_report"]["forbidden_hit_count"],
            validation_used=summary["boundary"]["validation_usage"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
