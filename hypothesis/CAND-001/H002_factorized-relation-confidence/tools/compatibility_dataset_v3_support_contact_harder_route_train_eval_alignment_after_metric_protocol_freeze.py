#!/usr/bin/env python3
"""Align train-side support/contact features to the official 43-feature schema."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PROTOCOL_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit"
)
DEFAULT_TRAIN_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization"
)
DEFAULT_TRAIN_SCHEMA_AUDIT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit"
)
DEFAULT_OFFICIAL_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/support_contact_harder_materialization/latest"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze"
)

EXPECTED_PROTOCOL_STATUS = "h002_support_contact_harder_route_metric_protocol_freeze_after_schema_shortcut_audit_ready"
EXPECTED_PROTOCOL_NEXT = "compatibility_dataset_v3_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze"
EXPECTED_TRAIN_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_TRAIN_SCHEMA_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit_ready_for_smoke_plan"
)

SCHEMA_VERSION = "h002_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze_v1"
STATUS_READY = "h002_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze_ready"
STATUS_ERRORS = "h002_support_contact_harder_route_train_eval_alignment_after_metric_protocol_freeze_errors"
SELECTED_PATH = "support_contact_train_eval_aligned_select_metric_runner_protocol"
NEXT_TODO = "compatibility_dataset_v3_support_contact_harder_route_metric_runner_after_train_eval_alignment"

OFFICIAL_FEATURES = [
    "aabb_intersection_volume_proxy",
    "abs_surface_gap_subject_bottom_to_object_top",
    "center_delta_z",
    "contact_band_width",
    "contact_patch_ratio_proxy",
    "local_contact_point_count",
    "local_contact_point_density",
    "normal_alignment_abs",
    "object_flatness_ratio",
    "object_footprint_area",
    "object_height",
    "object_horizontal_extent_ratio",
    "object_minor_axis_upness",
    "object_near_subject_bottom_point_count",
    "object_near_subject_bottom_point_ratio",
    "object_normal_upness",
    "object_principal_axis_upness",
    "object_vertical_extent_ratio",
    "point_object_count",
    "point_pair_min_count",
    "point_pair_total_count",
    "point_subject_count",
    "subject_flatness_ratio",
    "subject_footprint_area",
    "subject_height",
    "subject_horizontal_extent_ratio",
    "subject_minor_axis_upness",
    "subject_near_object_top_point_count",
    "subject_near_object_top_point_ratio",
    "subject_normal_upness",
    "subject_principal_axis_upness",
    "subject_vertical_extent_ratio",
    "support_contact_likelihood_proxy",
    "support_surface_normal_upness",
    "surface_alignment_abs",
    "surface_gap_subject_bottom_to_object_top",
    "vertical_overlap_ratio",
    "xy_center_distance",
    "xy_overlap_area",
    "xy_overlap_max_ratio",
    "xy_overlap_min_ratio",
    "xy_overlap_object_ratio",
    "xy_overlap_subject_ratio",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol-dir", type=Path, default=DEFAULT_PROTOCOL_DIR)
    parser.add_argument("--train-dir", type=Path, default=DEFAULT_TRAIN_DIR)
    parser.add_argument("--train-schema-audit-dir", type=Path, default=DEFAULT_TRAIN_SCHEMA_AUDIT_DIR)
    parser.add_argument("--official-dir", type=Path, default=DEFAULT_OFFICIAL_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return list(iter_jsonl(path))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def line_count(path: Path) -> int:
    if not path.exists():
        return -1
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def val(row: dict[str, Any], block: str, key: str) -> float:
    value = row.get("feature_blocks", {}).get(block, {}).get(key)
    if not is_finite_number(value):
        raise KeyError(f"{block}.{key}")
    return float(value)


def safe_div(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return float(num) / float(den)


def vertical_overlap_depth(row: dict[str, Any]) -> float:
    subject_bottom = val(row, "G_e_point_pose", "subject_bottom_z")
    subject_top = val(row, "G_e_point_pose", "subject_top_z")
    object_bottom = val(row, "G_e_point_pose", "object_bottom_z")
    object_top = val(row, "G_e_point_pose", "object_top_z")
    return max(0.0, min(subject_top, object_top) - max(subject_bottom, object_bottom))


def canonical_feature_map() -> dict[str, tuple[str, str, Callable[[dict[str, Any]], float]]]:
    return {
        "aabb_intersection_volume_proxy": (
            "derived",
            "G_e_contact_patch.point_xy_overlap_area * vertical_overlap_depth_from_G_e_point_pose",
            lambda r: val(r, "G_e_contact_patch", "point_xy_overlap_area") * vertical_overlap_depth(r),
        ),
        "abs_surface_gap_subject_bottom_to_object_top": (
            "direct",
            "G_e_contact_patch.point_abs_surface_gap_subject_bottom_to_object_top",
            lambda r: val(r, "G_e_contact_patch", "point_abs_surface_gap_subject_bottom_to_object_top"),
        ),
        "center_delta_z": (
            "direct",
            "G_e_contact_patch.point_center_delta_z",
            lambda r: val(r, "G_e_contact_patch", "point_center_delta_z"),
        ),
        "contact_band_width": ("constant", "0.03", lambda r: 0.03),
        "contact_patch_ratio_proxy": (
            "direct_proxy",
            "G_e_contact_patch.point_object_top_near_subject_bottom",
            lambda r: val(r, "G_e_contact_patch", "point_object_top_near_subject_bottom"),
        ),
        "local_contact_point_count": (
            "derived_proxy",
            "G_e_contact_patch.point_object_top_near_subject_bottom * G_e_point_pose.pair_min_point_count",
            lambda r: val(r, "G_e_contact_patch", "point_object_top_near_subject_bottom")
            * val(r, "G_e_point_pose", "pair_min_point_count"),
        ),
        "local_contact_point_density": (
            "derived_proxy",
            "local_contact_point_count / G_e_point_pose.pair_min_point_count",
            lambda r: val(r, "G_e_contact_patch", "point_object_top_near_subject_bottom"),
        ),
        "normal_alignment_abs": (
            "direct_transform",
            "abs(G_e_obb_baseline.normal_alignment)",
            lambda r: abs(val(r, "G_e_obb_baseline", "normal_alignment")),
        ),
        "object_flatness_ratio": (
            "direct",
            "G_e_point_pose.object_flatness_proxy",
            lambda r: val(r, "G_e_point_pose", "object_flatness_proxy"),
        ),
        "object_footprint_area": (
            "direct",
            "G_e_point_pose.object_xy_area",
            lambda r: val(r, "G_e_point_pose", "object_xy_area"),
        ),
        "object_height": ("direct", "G_e_point_pose.object_extent_z", lambda r: val(r, "G_e_point_pose", "object_extent_z")),
        "object_horizontal_extent_ratio": (
            "direct",
            "G_e_point_pose.object_horizontal_extent_ratio",
            lambda r: val(r, "G_e_point_pose", "object_horizontal_extent_ratio"),
        ),
        "object_minor_axis_upness": (
            "direct",
            "G_e_obb_baseline.object_minor_axis_upness",
            lambda r: val(r, "G_e_obb_baseline", "object_minor_axis_upness"),
        ),
        "object_near_subject_bottom_point_count": (
            "derived_proxy",
            "G_e_contact_patch.point_object_top_near_subject_bottom * G_e_point_pose.object_point_count",
            lambda r: val(r, "G_e_contact_patch", "point_object_top_near_subject_bottom")
            * val(r, "G_e_point_pose", "object_point_count"),
        ),
        "object_near_subject_bottom_point_ratio": (
            "direct_proxy",
            "G_e_contact_patch.point_object_top_near_subject_bottom",
            lambda r: val(r, "G_e_contact_patch", "point_object_top_near_subject_bottom"),
        ),
        "object_normal_upness": (
            "direct",
            "G_e_obb_baseline.object_normal_upness",
            lambda r: val(r, "G_e_obb_baseline", "object_normal_upness"),
        ),
        "object_principal_axis_upness": (
            "direct",
            "G_e_obb_baseline.object_major_axis_upness",
            lambda r: val(r, "G_e_obb_baseline", "object_major_axis_upness"),
        ),
        "object_vertical_extent_ratio": (
            "direct",
            "G_e_point_pose.object_vertical_extent_ratio",
            lambda r: val(r, "G_e_point_pose", "object_vertical_extent_ratio"),
        ),
        "point_object_count": ("direct", "G_e_point_pose.object_point_count", lambda r: val(r, "G_e_point_pose", "object_point_count")),
        "point_pair_min_count": (
            "direct",
            "G_e_point_pose.pair_min_point_count",
            lambda r: val(r, "G_e_point_pose", "pair_min_point_count"),
        ),
        "point_pair_total_count": (
            "direct",
            "G_e_point_pose.pair_total_point_count",
            lambda r: val(r, "G_e_point_pose", "pair_total_point_count"),
        ),
        "point_subject_count": ("direct", "G_e_point_pose.subject_point_count", lambda r: val(r, "G_e_point_pose", "subject_point_count")),
        "subject_flatness_ratio": (
            "direct",
            "G_e_point_pose.subject_flatness_proxy",
            lambda r: val(r, "G_e_point_pose", "subject_flatness_proxy"),
        ),
        "subject_footprint_area": (
            "direct",
            "G_e_point_pose.subject_xy_area",
            lambda r: val(r, "G_e_point_pose", "subject_xy_area"),
        ),
        "subject_height": ("direct", "G_e_point_pose.subject_extent_z", lambda r: val(r, "G_e_point_pose", "subject_extent_z")),
        "subject_horizontal_extent_ratio": (
            "direct",
            "G_e_point_pose.subject_horizontal_extent_ratio",
            lambda r: val(r, "G_e_point_pose", "subject_horizontal_extent_ratio"),
        ),
        "subject_minor_axis_upness": (
            "direct",
            "G_e_obb_baseline.subject_minor_axis_upness",
            lambda r: val(r, "G_e_obb_baseline", "subject_minor_axis_upness"),
        ),
        "subject_near_object_top_point_count": (
            "derived_proxy",
            "G_e_contact_patch.point_object_top_near_subject_bottom * G_e_point_pose.subject_point_count",
            lambda r: val(r, "G_e_contact_patch", "point_object_top_near_subject_bottom")
            * val(r, "G_e_point_pose", "subject_point_count"),
        ),
        "subject_near_object_top_point_ratio": (
            "proxy_symmetric_contact_band",
            "G_e_contact_patch.point_object_top_near_subject_bottom",
            lambda r: val(r, "G_e_contact_patch", "point_object_top_near_subject_bottom"),
        ),
        "subject_normal_upness": (
            "direct",
            "G_e_obb_baseline.subject_normal_upness",
            lambda r: val(r, "G_e_obb_baseline", "subject_normal_upness"),
        ),
        "subject_principal_axis_upness": (
            "direct",
            "G_e_obb_baseline.subject_major_axis_upness",
            lambda r: val(r, "G_e_obb_baseline", "subject_major_axis_upness"),
        ),
        "subject_vertical_extent_ratio": (
            "direct",
            "G_e_point_pose.subject_vertical_extent_ratio",
            lambda r: val(r, "G_e_point_pose", "subject_vertical_extent_ratio"),
        ),
        "support_contact_likelihood_proxy": (
            "direct_proxy",
            "G_e_contact_patch.point_support_contact_likelihood_proxy",
            lambda r: val(r, "G_e_contact_patch", "point_support_contact_likelihood_proxy"),
        ),
        "support_surface_normal_upness": (
            "direct",
            "G_e_obb_baseline.support_normal_verticality",
            lambda r: val(r, "G_e_obb_baseline", "support_normal_verticality"),
        ),
        "surface_alignment_abs": (
            "direct_transform",
            "abs(G_e_obb_baseline.normal_alignment)",
            lambda r: abs(val(r, "G_e_obb_baseline", "normal_alignment")),
        ),
        "surface_gap_subject_bottom_to_object_top": (
            "direct",
            "G_e_contact_patch.point_surface_gap_subject_bottom_to_object_top",
            lambda r: val(r, "G_e_contact_patch", "point_surface_gap_subject_bottom_to_object_top"),
        ),
        "vertical_overlap_ratio": (
            "derived",
            "vertical_overlap_depth / min(subject_height, object_height)",
            lambda r: safe_div(
                vertical_overlap_depth(r),
                min(val(r, "G_e_point_pose", "subject_extent_z"), val(r, "G_e_point_pose", "object_extent_z")),
            ),
        ),
        "xy_center_distance": (
            "direct",
            "G_e_contact_patch.point_center_distance_xy",
            lambda r: val(r, "G_e_contact_patch", "point_center_distance_xy"),
        ),
        "xy_overlap_area": (
            "direct",
            "G_e_contact_patch.point_xy_overlap_area",
            lambda r: val(r, "G_e_contact_patch", "point_xy_overlap_area"),
        ),
        "xy_overlap_max_ratio": (
            "derived",
            "G_e_contact_patch.point_xy_overlap_area / max(subject_xy_area, object_xy_area)",
            lambda r: safe_div(
                val(r, "G_e_contact_patch", "point_xy_overlap_area"),
                max(val(r, "G_e_point_pose", "subject_xy_area"), val(r, "G_e_point_pose", "object_xy_area")),
            ),
        ),
        "xy_overlap_min_ratio": (
            "direct",
            "G_e_contact_patch.point_xy_overlap_min_ratio",
            lambda r: val(r, "G_e_contact_patch", "point_xy_overlap_min_ratio"),
        ),
        "xy_overlap_object_ratio": (
            "direct",
            "G_e_contact_patch.point_xy_overlap_object_ratio",
            lambda r: val(r, "G_e_contact_patch", "point_xy_overlap_object_ratio"),
        ),
        "xy_overlap_subject_ratio": (
            "direct",
            "G_e_contact_patch.point_xy_overlap_subject_ratio",
            lambda r: val(r, "G_e_contact_patch", "point_xy_overlap_subject_ratio"),
        ),
    }


def stable_split(scan_id: str) -> str:
    digest = hashlib.sha1(scan_id.encode("utf-8")).hexdigest()
    return "internal_dev" if int(digest[:8], 16) % 5 == 0 else "internal_train"


def canonicalize_row(row: dict[str, Any], source: dict[str, Any], feature_map: dict[str, tuple[str, str, Callable]]) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    vector: dict[str, float] = {}
    mask: dict[str, bool] = {}
    for feature in OFFICIAL_FEATURES:
        try:
            value = feature_map[feature][2](row)
            if not is_finite_number(value):
                raise ValueError(f"nonfinite {feature}")
            vector[feature] = float(value)
            mask[feature] = True
        except Exception as exc:  # noqa: BLE001 - validation artifact should preserve reason
            vector[feature] = 0.0
            mask[feature] = False
            errors.append({"row_id": row.get("row_id"), "feature": feature, "reason": str(exc)})

    predicate = row.get("feature_blocks", {}).get("T_e", {}).get("predicate_label")
    split = stable_split(str(source.get("scan_id_hidden", "")))
    aligned = {
        "candidate_id": f"train_aligned::{row.get('row_id')}",
        "schema_version": f"{SCHEMA_VERSION}_model_safe_no_class",
        "dataset_name": "h002_support_contact_harder_route_train_aligned_v1",
        "split": split,
        "source_split": "train",
        "subset": "main_compatibility",
        "route_family": "support_contact",
        "predicate_label": predicate,
        "feature_blocks": {
            "T_e": {
                "predicate_text": predicate,
                "predicate_label": predicate,
                "route_family": "support_contact",
                "predicate_family_embedding_key": "support_contact",
            },
            "G_e": {
                "g_e_available": all(mask.values()),
                "g_e_feature_names": OFFICIAL_FEATURES,
                "g_e_feature_vector": vector,
                "g_e_feature_mask": mask,
                "geometry_reference_policy": "canonicalized_train_point_obb_contact_features_aligned_to_official_43_feature_schema",
            },
        },
        "feature_use_policy": {
            "main_C_e_allowed_blocks": ["T_e", "G_e"],
            "excluded_from_primary_C_e": ["Z_e", "Q_e", "class labels", "H001 p_geom_valid", "source score/rank"],
            "label_not_features": ["labels.C_e"],
            "row_identity_not_features": ["candidate_id", "source_row_id", "scan_id_hidden", "subject_id_hidden", "object_id_hidden"],
        },
        "labels": {"C_e": int(row.get("labels", {}).get("C_e"))},
        "official_validation_eval_only": False,
        "official_test_used": False,
        "paper_metric_ready": False,
        "source_row_id": row.get("row_id"),
    }
    class_ablation = {
        **aligned,
        "schema_version": f"{SCHEMA_VERSION}_class_ablation",
        "feature_blocks": {
            **aligned["feature_blocks"],
            "T_e": {
                **aligned["feature_blocks"]["T_e"],
                "subject_class_text": row.get("feature_blocks", {}).get("T_e", {}).get("subject_class_text"),
                "object_class_text": row.get("feature_blocks", {}).get("T_e", {}).get("object_class_text"),
            },
        },
        "feature_use_policy": {
            **aligned["feature_use_policy"],
            "class_labels_policy": "diagnostic_ablation_only_not_primary_C_e",
        },
    }
    hidden = {
        "candidate_id": aligned["candidate_id"],
        "source_row_id": row.get("row_id"),
        "scan_id": source.get("scan_id_hidden"),
        "subject_id": source.get("subject_id_hidden"),
        "object_id": source.get("object_id_hidden"),
        "class_pair": source.get("class_pair_hidden"),
        "predicate_label": predicate,
        "label": int(row.get("labels", {}).get("C_e")),
        "split": split,
        "source_id": source.get("source_id_hidden"),
        "source_score_policy": "Z_e_hidden_excluded_from_primary_C_e",
        "p_geom_valid_policy": "hidden_diagnostic_only_not_primary_G_e",
    }
    return aligned, class_ablation, hidden, errors


def validate_protocol(protocol_summary: dict[str, Any], train_summary: dict[str, Any], train_audit: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if protocol_summary.get("status") != EXPECTED_PROTOCOL_STATUS:
        errors.append({"error_type": "unexpected_protocol_status", "actual": protocol_summary.get("status")})
    if protocol_summary.get("next_todo") != EXPECTED_PROTOCOL_NEXT:
        errors.append({"error_type": "unexpected_protocol_next_todo", "actual": protocol_summary.get("next_todo")})
    if protocol_summary.get("validation_errors") != 0:
        errors.append({"error_type": "protocol_validation_errors", "actual": protocol_summary.get("validation_errors")})
    if train_summary.get("status") != EXPECTED_TRAIN_STATUS:
        errors.append({"error_type": "unexpected_train_materialization_status", "actual": train_summary.get("status")})
    if train_summary.get("validation_errors") != 0:
        errors.append({"error_type": "train_materialization_validation_errors", "actual": train_summary.get("validation_errors")})
    if train_audit.get("status") != EXPECTED_TRAIN_SCHEMA_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_train_schema_audit_status", "actual": train_audit.get("status")})
    if train_audit.get("validation_errors") != 0:
        errors.append({"error_type": "train_schema_audit_validation_errors", "actual": train_audit.get("validation_errors")})
    return errors


def build_report(summary: dict[str, Any]) -> str:
    return f"""# Support/Contact Hard Route Train/Eval Alignment

## Status

```text
artifact_root = {summary['output_artifacts']['artifact_root']}/
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Result

- canonical official features: `{summary['feature_alignment']['official_feature_count']}`
- mapped features: `{summary['feature_alignment']['mapped_feature_count']}`
- aligned rows: `{summary['row_counts']['aligned_rows']}`
- internal train/dev rows: `{summary['row_counts']['internal_train_rows']}` / `{summary['row_counts']['internal_dev_rows']}`
- scan overlap with official validation: `{summary['leakage_audit']['scan_overlap']}`
- endpoint overlap with official validation: `{summary['leakage_audit']['endpoint_overlap']}`

## Interpretation

Train-side support/contact rows were canonicalized to the official 43-feature
hard-route `G_e` schema. Some fields are direct mappings, while contact-band and
intersection fields are derived proxies. This is acceptable for the next metric
runner, but the runner must report the feature-map provenance.

Official validation remains eval-only. The aligned train/dev rows are the only
allowed fitting and model-selection rows for the next support/contact hard-route
metric runner.

## Boundary

- no metric was run
- official test was not used
- no paper result was promoted
- class labels remain ablation-only
- `Q_e` remains diagnostic-only
- no `support_contact solved` claim
"""


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    protocol_summary = read_json(args.protocol_dir / "summary.json")
    train_summary = read_json(args.train_dir / "summary.json")
    train_audit_summary = read_json(args.train_schema_audit_dir / "summary.json")
    validation_errors = validate_protocol(protocol_summary, train_summary, train_audit_summary)

    if line_count(args.protocol_dir / "validation_errors.jsonl") != 0:
        validation_errors.append({"error_type": "non_empty_protocol_validation_errors"})
    if line_count(args.train_dir / "validation_errors.jsonl") != 0:
        validation_errors.append({"error_type": "non_empty_train_validation_errors"})
    if line_count(args.train_schema_audit_dir / "validation_errors.jsonl") != 0:
        validation_errors.append({"error_type": "non_empty_train_schema_validation_errors"})

    official_rows = read_jsonl(args.official_dir / "model_safe_main_no_class.jsonl")
    official_hidden = read_jsonl(args.official_dir / "hidden_manifest.jsonl")
    official_features = official_rows[0]["feature_blocks"]["G_e"]["g_e_feature_names"] if official_rows else []
    if official_features != OFFICIAL_FEATURES:
        validation_errors.append({"error_type": "official_feature_list_mismatch"})

    train_rows_all = read_jsonl(args.train_dir / "model_safe_view.jsonl")
    train_sources = {row["row_id"]: row for row in read_jsonl(args.train_dir / "source_manifest.jsonl")}
    train_rows = [
        row
        for row in train_rows_all
        if row.get("model_use") == "main_train_candidate_if_schema_audit_passes"
        and row.get("feature_blocks", {}).get("T_e", {}).get("predicate_label") in {"standing on", "lying on"}
    ]

    feature_map = canonical_feature_map()
    map_rows = [
        {
            "official_feature": feature,
            "map_type": feature_map[feature][0],
            "train_source_or_formula": feature_map[feature][1],
            "status": "mapped",
        }
        for feature in OFFICIAL_FEATURES
    ]

    aligned_rows: list[dict[str, Any]] = []
    class_rows: list[dict[str, Any]] = []
    hidden_rows: list[dict[str, Any]] = []
    feature_errors: list[dict[str, Any]] = []
    for row in train_rows:
        source = train_sources.get(row.get("row_id"))
        if not source:
            feature_errors.append({"row_id": row.get("row_id"), "error_type": "missing_source_manifest"})
            continue
        aligned, class_ablation, hidden, errors = canonicalize_row(row, source, feature_map)
        aligned_rows.append(aligned)
        class_rows.append(class_ablation)
        hidden_rows.append(hidden)
        feature_errors.extend({"error_type": "feature_mapping_error", **err} for err in errors)

    official_scans = {row.get("scan_id") for row in official_hidden}
    official_endpoints = {(row.get("scan_id"), row.get("subject_id"), row.get("object_id")) for row in official_hidden}
    train_scans = {row.get("scan_id") for row in hidden_rows}
    train_endpoints = {(row.get("scan_id"), row.get("subject_id"), row.get("object_id")) for row in hidden_rows}
    scan_overlap = official_scans & train_scans
    endpoint_overlap = official_endpoints & train_endpoints
    if scan_overlap:
        validation_errors.append({"error_type": "official_train_scan_overlap", "count": len(scan_overlap)})
    if endpoint_overlap:
        validation_errors.append({"error_type": "official_train_endpoint_overlap", "count": len(endpoint_overlap)})
    if feature_errors:
        validation_errors.extend(feature_errors[:20])

    feature_presence: dict[str, int] = Counter()
    feature_nonfinite: dict[str, int] = Counter()
    for row in aligned_rows:
        vector = row["feature_blocks"]["G_e"]["g_e_feature_vector"]
        for feature in OFFICIAL_FEATURES:
            if feature in vector:
                feature_presence[feature] += 1
            if not is_finite_number(vector.get(feature)):
                feature_nonfinite[feature] += 1

    feature_alignment_rows = [
        {
            "feature": feature,
            "present_rows": feature_presence.get(feature, 0),
            "nonfinite_rows": feature_nonfinite.get(feature, 0),
            "total_rows": len(aligned_rows),
            "present_rate": round(safe_div(feature_presence.get(feature, 0), len(aligned_rows)), 6),
            "map_type": feature_map[feature][0],
        }
        for feature in OFFICIAL_FEATURES
    ]

    split_counts = Counter(row["split"] for row in aligned_rows)
    split_label_counts: dict[tuple[str, int], int] = Counter((row["split"], row["labels"]["C_e"]) for row in aligned_rows)
    split_pred_counts: dict[tuple[str, str], int] = Counter((row["split"], row["predicate_label"]) for row in aligned_rows)
    split_rows = []
    for split in ["internal_train", "internal_dev"]:
        split_rows.append(
            {
                "split": split,
                "rows": split_counts.get(split, 0),
                "label_0": split_label_counts.get((split, 0), 0),
                "label_1": split_label_counts.get((split, 1), 0),
                "standing_on": split_pred_counts.get((split, "standing on"), 0),
                "lying_on": split_pred_counts.get((split, "lying on"), 0),
            }
        )

    status = STATUS_READY if not validation_errors else STATUS_ERRORS
    selected_path = SELECTED_PATH if not validation_errors else "blocked_fix_train_eval_alignment"
    next_todo = NEXT_TODO if not validation_errors else "fix_support_contact_train_eval_alignment"

    output_artifacts = {
        "artifact_root": rel_path(args.output_dir),
        "summary": rel_path(args.output_dir / "summary.json"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        "feature_map": rel_path(args.output_dir / "feature_map.csv"),
        "feature_alignment_audit": rel_path(args.output_dir / "feature_alignment_audit.csv"),
        "leakage_audit": rel_path(args.output_dir / "leakage_audit.csv"),
        "split_manifest": rel_path(args.output_dir / "split_manifest.csv"),
        "model_safe_no_class_train_dev": rel_path(args.output_dir / "model_safe_no_class_train_dev.jsonl"),
        "class_ablation_train_dev": rel_path(args.output_dir / "class_ablation_train_dev.jsonl"),
        "hidden_train_dev_manifest": rel_path(args.output_dir / "hidden_train_dev_manifest.jsonl"),
        "runner_input_contract": rel_path(args.output_dir / "runner_input_contract.json"),
        "next_contract": rel_path(args.output_dir / "next_contract.json"),
        "report": rel_path(args.output_dir / "report.md"),
    }

    leakage_rows = [
        {
            "check": "scan_overlap_with_official_validation",
            "count": len(scan_overlap),
            "pass": len(scan_overlap) == 0,
        },
        {
            "check": "endpoint_overlap_with_official_validation",
            "count": len(endpoint_overlap),
            "pass": len(endpoint_overlap) == 0,
        },
        {
            "check": "official_test_usage",
            "count": 0,
            "pass": True,
        },
    ]

    runner_contract = {
        "schema_version": f"{SCHEMA_VERSION}_runner_input_contract",
        "status": "runner_input_ready" if not validation_errors else "blocked",
        "train_dev_inputs": {
            "model_safe_no_class_train_dev": output_artifacts["model_safe_no_class_train_dev"],
            "class_ablation_train_dev": output_artifacts["class_ablation_train_dev"],
            "hidden_train_dev_manifest": output_artifacts["hidden_train_dev_manifest"],
        },
        "official_validation_inputs": {
            "model_safe_main_no_class": rel_path(args.official_dir / "model_safe_main_no_class.jsonl"),
            "model_safe_main_with_class_ablation": rel_path(args.official_dir / "model_safe_main_with_class_ablation.jsonl"),
            "hidden_manifest": rel_path(args.official_dir / "hidden_manifest.jsonl"),
        },
        "protocol_inputs": {
            "metric_contract": rel_path(args.protocol_dir / "support_contact_metric_contract.json"),
            "model_view_contract": rel_path(args.protocol_dir / "model_view_contract.csv"),
            "control_contract": rel_path(args.protocol_dir / "control_contract.csv"),
        },
        "fit_policy": [
            "fit only on rows where split == internal_train",
            "select hyperparameters only on rows where split == internal_dev",
            "evaluate official validation once after training/dev selection",
            "do not use class_ablation_train_dev for primary M1-M4",
            "do not use Q_e in primary M1-M4",
        ],
        "blocked": [
            "official_test",
            "source_reranking",
            "p_obs_p_rel_claim",
            "support_contact_solved_claim",
        ],
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "validation_errors": len(validation_errors),
        "next_todo": next_todo,
        "row_counts": {
            "train_source_rows": len(train_rows_all),
            "main_candidate_rows": len(train_rows),
            "aligned_rows": len(aligned_rows),
            "internal_train_rows": split_counts.get("internal_train", 0),
            "internal_dev_rows": split_counts.get("internal_dev", 0),
            "official_validation_rows": len(official_rows),
        },
        "feature_alignment": {
            "official_feature_count": len(OFFICIAL_FEATURES),
            "mapped_feature_count": len(map_rows),
            "direct_or_transform_count": sum(1 for row in map_rows if row["map_type"] in {"direct", "direct_transform"}),
            "derived_or_proxy_count": sum(1 for row in map_rows if row["map_type"] not in {"direct", "direct_transform"}),
            "feature_errors": len(feature_errors),
        },
        "leakage_audit": {
            "train_scan_count": len(train_scans),
            "official_scan_count": len(official_scans),
            "scan_overlap": len(scan_overlap),
            "train_endpoint_count": len(train_endpoints),
            "official_endpoint_count": len(official_endpoints),
            "endpoint_overlap": len(endpoint_overlap),
        },
        "decision": {
            "train_eval_alignment_ready": not bool(validation_errors),
            "metric_runner_next": not bool(validation_errors),
            "official_validation_eval_only": True,
            "official_test_usage": False,
            "paper_metric_promoted": False,
            "support_contact_solved_claim_allowed": False,
            "class_ablation_diagnostic_only": True,
            "q_e_diagnostic_only": True,
        },
        "input_artifacts": {
            "protocol_summary": rel_path(args.protocol_dir / "summary.json"),
            "train_materialization_summary": rel_path(args.train_dir / "summary.json"),
            "train_schema_audit_summary": rel_path(args.train_schema_audit_dir / "summary.json"),
            "official_materialization_manifest": rel_path(args.official_dir / "row_manifest.json"),
        },
        "output_artifacts": output_artifacts,
    }

    next_contract = {
        "next_todo": next_todo,
        "selected_path": selected_path,
        "purpose": "Implement and run support/contact hard-route metric runner using aligned train/dev and official eval-only inputs.",
        "must_use": [
            output_artifacts["model_safe_no_class_train_dev"],
            output_artifacts["hidden_train_dev_manifest"],
            rel_path(args.official_dir / "model_safe_main_no_class.jsonl"),
            rel_path(args.official_dir / "hidden_manifest.jsonl"),
            rel_path(args.protocol_dir / "support_contact_metric_contract.json"),
        ],
        "must_not_do": [
            "do not fit on official validation",
            "do not use official test",
            "do not use class labels in primary M1-M4",
            "do not use Q_e in primary M1-M4",
            "do not claim support_contact solved",
        ],
    }

    write_json(args.output_dir / "summary.json", summary)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "feature_map.csv", map_rows)
    write_csv(args.output_dir / "feature_alignment_audit.csv", feature_alignment_rows)
    write_csv(args.output_dir / "leakage_audit.csv", leakage_rows)
    write_csv(args.output_dir / "split_manifest.csv", split_rows)
    write_jsonl(args.output_dir / "model_safe_no_class_train_dev.jsonl", aligned_rows)
    write_jsonl(args.output_dir / "class_ablation_train_dev.jsonl", class_rows)
    write_jsonl(args.output_dir / "hidden_train_dev_manifest.jsonl", hidden_rows)
    write_json(args.output_dir / "runner_input_contract.json", runner_contract)
    write_json(args.output_dir / "next_contract.json", next_contract)
    (args.output_dir / "report.md").write_text(build_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
