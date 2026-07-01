#!/usr/bin/env python3
"""Materialize the R1 close-by geometry-support route root."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_PLAN_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan"
)
DEFAULT_SOURCE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_candidate_materialization"
DEFAULT_SCHEMA_AUDIT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit"
DEFAULT_ROUTE_ROOT = H2_ROOT / "artifacts/route_specific_targets/r1_proximity"

EXPECTED_PLAN_STATUS = (
    "h002_compatibility_dataset_v3_close_by_geometry_support_materialization_plan_after_route_plan_ready"
)
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan"
EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_candidate_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_SCHEMA_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_proximity_close_by_schema_shortcut_audit_blocked_distance_rule_shortcut"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan_v1"
MODEL_SAFE_SCHEMA = "h002_r1_close_by_geometry_support_model_safe_rows_v1"
HIDDEN_SCHEMA = "h002_r1_close_by_geometry_support_hidden_manifest_v1"
AUDIT_SCHEMA = "h002_r1_close_by_geometry_support_audit_view_v1"

STATUS_READY = "h002_compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan_input_errors"
SELECTED_PATH = "materialized_r1_close_by_geometry_support_route_root"
NEXT_TODO = "compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization"

ROUTE_ID = "R1"
ROUTE_FAMILY = "proximity"
ROUTE_RELATION = "close by"
ROUTE_TYPE = "geometry_only_learned_evaluated_route"
TARGET_AXIS = "geometry_support"

BLOCKED_FEATURE_KEYS = {
    "audit_label",
    "candidate_bucket",
    "class_pair_rank_key",
    "directed_pair_id",
    "distance_bucket",
    "geometry_status",
    "gt_match",
    "label_match_status",
    "norm_distance_bin",
    "object_id",
    "p_geom_invalid",
    "p_geom_valid",
    "prediction_id",
    "raw_distance_bin",
    "row_id",
    "row_key",
    "scan_id",
    "source_feature_snapshot",
    "subject_id",
    "subject_object_class_pair",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan-dir", type=Path, default=DEFAULT_PLAN_DIR)
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--schema-audit-dir", type=Path, default=DEFAULT_SCHEMA_AUDIT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_ROUTE_ROOT)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate_inputs(
    plan_summary: dict[str, Any],
    source_summary: dict[str, Any],
    schema_audit_summary: dict[str, Any],
    model_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    plan_errors: list[dict[str, Any]],
    source_errors: list[dict[str, Any]],
    schema_audit_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0 or plan_errors:
        errors.append(
            {
                "error_type": "plan_validation_errors_present",
                "summary_count": plan_summary.get("validation_errors"),
                "rows": len(plan_errors),
            }
        )
    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append({"error_type": "unexpected_source_status", "actual": source_summary.get("status")})
    if source_summary.get("validation_errors") != 0 or source_errors:
        errors.append(
            {
                "error_type": "source_validation_errors_present",
                "summary_count": source_summary.get("validation_errors"),
                "rows": len(source_errors),
            }
        )
    if schema_audit_summary.get("status") != EXPECTED_SCHEMA_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_schema_audit_status", "actual": schema_audit_summary.get("status")})
    if schema_audit_summary.get("validation_errors") != 0 or schema_audit_errors:
        errors.append(
            {
                "error_type": "schema_audit_validation_errors_present",
                "summary_count": schema_audit_summary.get("validation_errors"),
                "rows": len(schema_audit_errors),
            }
        )

    for name, summary in [
        ("plan", plan_summary),
        ("source", source_summary),
        ("schema_audit", schema_audit_summary),
    ]:
        boundary = summary.get("boundary", {})
        for key in ["h001_artifacts_modified", "validation_usage", "test_usage"]:
            if key in boundary and boundary.get(key) is not False:
                errors.append(
                    {
                        "error_type": "upstream_boundary_not_false",
                        "summary": name,
                        "key": key,
                        "actual": boundary.get(key),
                    }
                )
        if boundary.get("validation_or_test_used") is not None and boundary.get("validation_or_test_used") is not False:
            errors.append(
                {
                    "error_type": "upstream_boundary_not_false",
                    "summary": name,
                    "key": "validation_or_test_used",
                    "actual": boundary.get("validation_or_test_used"),
                }
            )

    expected_total = source_summary.get("row_counts", {}).get("total_rows")
    if len(model_rows) != expected_total:
        errors.append({"error_type": "model_row_count_mismatch", "actual": len(model_rows), "expected": expected_total})
    if len(hidden_rows) != expected_total:
        errors.append({"error_type": "hidden_row_count_mismatch", "actual": len(hidden_rows), "expected": expected_total})
    model_ids = [row.get("row_id") for row in model_rows]
    hidden_ids = [row.get("row_id") for row in hidden_rows]
    if len(model_ids) != len(set(model_ids)):
        errors.append({"error_type": "duplicate_model_row_id", "duplicates": len(model_ids) - len(set(model_ids))})
    if sorted(model_ids) != sorted(hidden_ids):
        errors.append({"error_type": "model_hidden_row_id_set_mismatch"})
    return errors


def geometry_support_label(old_targets: dict[str, Any]) -> tuple[str, int | None]:
    value = old_targets.get("C_e_label")
    if value == 1:
        return "geometry_supported", 1
    if value == 0:
        return "geometry_unsupported", 0
    if value == "abstain":
        return "abstain", None
    if value == "audit_required":
        return "audit_required", None
    return str(value), None


def route_row_id(old_row_id: str) -> str:
    return old_row_id.replace("h002_close_by_", "h002_r1_close_by_", 1)


def transform_model_row(row: dict[str, Any]) -> dict[str, Any]:
    old_targets = row.get("targets", {})
    label, binary = geometry_support_label(old_targets)
    features = row.get("feature_blocks", {})
    return {
        "schema_version": MODEL_SAFE_SCHEMA,
        "route_id": ROUTE_ID,
        "route_family": ROUTE_FAMILY,
        "route_relation": ROUTE_RELATION,
        "route_type": ROUTE_TYPE,
        "target_axis": TARGET_AXIS,
        "route_row_id": route_row_id(row["row_id"]),
        "source_row_id_ref": row["row_id"],
        "split": row.get("split"),
        "subset": row.get("subset"),
        "role": row.get("role"),
        "feature_blocks": {
            "T_e_annotation": features.get("T_e", {}),
            "Z_e_source_baseline": features.get("Z_e_safe", {}),
            "G_e_route": features.get("G_e", {}),
            "Q_e_observability": features.get("Q_e_safe", {}),
        },
        "route_targets": {
            "geometry_support_label": label,
            "geometry_support_binary": binary,
            "p_obs_label": old_targets.get("p_obs_label"),
            "p_rel_label": old_targets.get("p_rel_label"),
            "c_e_interaction_label": "not_applicable",
            "target_axis": TARGET_AXIS,
            "is_primary_binary": old_targets.get("is_primary_binary", False),
            "is_abstain_or_audit": old_targets.get("is_abstain_or_audit", False),
            "is_raw_distance_diagnostic": old_targets.get("is_raw_distance_diagnostic", False),
        },
        "model_input_policy": {
            "primary_route_input": "G_e_route",
            "T_e_annotation_allowed_as_route_score": False,
            "Z_e_source_allowed_as_route_score": False,
            "Q_e_allowed_for_abstain_only": True,
            "C_e_interaction_applicable": False,
        },
    }


def transform_hidden_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": HIDDEN_SCHEMA,
        "route_id": ROUTE_ID,
        "route_family": ROUTE_FAMILY,
        "route_relation": ROUTE_RELATION,
        "route_type": ROUTE_TYPE,
        "target_axis": TARGET_AXIS,
        "route_row_id": route_row_id(row["row_id"]),
        "source_row_id_ref": row["row_id"],
        "identity": row.get("identity", {}),
        "hidden_controls": row.get("hidden_controls", {}),
        "control_tags": row.get("control_tags", {}),
        "source_feature_snapshot": row.get("source_feature_snapshot", {}),
        "target_construction": row.get("target_construction", {}),
        "blocked_model_input_groups": {
            "identity": "row/scan/endpoint identifiers",
            "construction": "candidate, status, label-match, and bin fields",
            "thresholds": "route construction thresholds and p_geom_valid rule buckets",
        },
    }


def build_audit_row(model_row: dict[str, Any], hidden_row: dict[str, Any]) -> dict[str, Any]:
    features = model_row.get("feature_blocks", {})
    hidden_controls = hidden_row.get("hidden_controls", {})
    return {
        "schema_version": AUDIT_SCHEMA,
        "route_row_id": model_row["route_row_id"],
        "source_row_id_ref": model_row["source_row_id_ref"],
        "split": model_row.get("split"),
        "subset": model_row.get("subset"),
        "role": model_row.get("role"),
        "route_targets": model_row.get("route_targets", {}),
        "semantic_context": features.get("T_e_annotation", {}),
        "source_baseline": features.get("Z_e_source_baseline", {}),
        "geometry_evidence_summary": {
            key: features.get("G_e_route", {}).get(key)
            for key in [
                "distance_xy",
                "distance_3d",
                "normalized_distance_xy",
                "normalized_distance_3d",
                "projected_iou_xy",
                "projected_subject_overlap_ratio",
                "projected_object_overlap_ratio",
            ]
        },
        "observability": features.get("Q_e_observability", {}),
        "hidden_distance_controls": {
            key: hidden_controls.get(key)
            for key in [
                "candidate_bucket",
                "geometry_status",
                "label_match_status",
                "distance_bucket",
                "raw_distance_bin",
                "norm_distance_bin",
                "p_geom_valid",
                "p_geom_invalid",
                "subject_object_class_pair",
            ]
        },
        "identity_for_audit_only": hidden_row.get("identity", {}),
    }


def flatten_keys(payload: Any, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(payload, dict):
        for key, value in payload.items():
            key_str = str(key)
            keys.add(key_str)
            keys.update(flatten_keys(value, f"{prefix}.{key_str}" if prefix else key_str))
    elif isinstance(payload, list):
        for item in payload:
            keys.update(flatten_keys(item, prefix))
    return keys


def output_validation(
    model_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    audit_rows: list[dict[str, Any]],
    source_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if not (len(model_rows) == len(hidden_rows) == len(audit_rows) == source_counts.get("total_rows")):
        errors.append(
            {
                "error_type": "output_row_count_mismatch",
                "model": len(model_rows),
                "hidden": len(hidden_rows),
                "audit": len(audit_rows),
                "expected": source_counts.get("total_rows"),
            }
        )
    route_ids = {row.get("route_id") for row in model_rows}
    if route_ids != {ROUTE_ID}:
        errors.append({"error_type": "unexpected_route_ids", "actual": sorted(route_ids)})
    target_axes = {row.get("target_axis") for row in model_rows}
    if target_axes != {TARGET_AXIS}:
        errors.append({"error_type": "unexpected_target_axes", "actual": sorted(target_axes)})
    old_target_hits = [row["route_row_id"] for row in model_rows if "C_e_label" in json.dumps(row, sort_keys=True)]
    if old_target_hits:
        errors.append({"error_type": "legacy_c_e_label_present", "rows": old_target_hits[:5], "count": len(old_target_hits)})
    interaction_values = {row.get("route_targets", {}).get("c_e_interaction_label") for row in model_rows}
    if interaction_values != {"not_applicable"}:
        errors.append({"error_type": "c_e_interaction_not_uniformly_not_applicable", "actual": sorted(map(str, interaction_values))})

    primary_rows = [row for row in model_rows if row.get("route_targets", {}).get("is_primary_binary")]
    primary_counts = Counter(row.get("route_targets", {}).get("geometry_support_label") for row in primary_rows)
    if len(primary_rows) != source_counts.get("primary_binary_rows"):
        errors.append({"error_type": "primary_row_count_mismatch", "actual": len(primary_rows)})
    if primary_counts.get("geometry_supported") != 400 or primary_counts.get("geometry_unsupported") != 400:
        errors.append({"error_type": "primary_label_balance_mismatch", "actual": dict(primary_counts)})

    for row in model_rows:
        feature_keys = flatten_keys(row.get("feature_blocks", {}))
        hits = sorted(feature_keys & BLOCKED_FEATURE_KEYS)
        if hits:
            errors.append({"error_type": "blocked_feature_key_present", "route_row_id": row["route_row_id"], "hits": hits})
            if len(errors) > 20:
                break
    return errors


def schema_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "route": {
            "route_id": ROUTE_ID,
            "family": ROUTE_FAMILY,
            "relation": ROUTE_RELATION,
            "route_type": ROUTE_TYPE,
            "target_axis": TARGET_AXIS,
        },
        "model_safe_rows": {
            "schema_version": MODEL_SAFE_SCHEMA,
            "metadata_fields": ["route_row_id", "source_row_id_ref", "split", "subset", "role", "route_id"],
            "feature_blocks": {
                "T_e_annotation": "annotation/baseline only, not route score",
                "Z_e_source_baseline": "source baseline only, not route score",
                "G_e_route": "primary geometry-support route evidence",
                "Q_e_observability": "abstain/coverage only",
            },
            "targets": {
                "geometry_support_label": "geometry_supported | geometry_unsupported | abstain | audit_required",
                "geometry_support_binary": "1 | 0 | null",
                "c_e_interaction_label": "always not_applicable for R1",
            },
        },
        "blocked_feature_keys": sorted(BLOCKED_FEATURE_KEYS),
        "claim_boundary": {
            "distance_dominance": "expected_route_property",
            "predicate_geometry_interaction_claim": "blocked",
            "paper_evidence_from_this_root_alone": "blocked",
        },
    }


def control_manifest_payload(schema_audit_summary: dict[str, Any], shortcut_rows: list[dict[str, str]]) -> dict[str, Any]:
    high_risk = [
        row
        for row in shortcut_rows
        if row.get("risk_level") == "high"
        and row.get("probe_name", "").startswith(("primary_binary:", "combined_binary:"))
    ][:12]
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "target_axis": TARGET_AXIS,
        "interpretation": {
            "distance_rule_dominance": "expected for geometry-only route",
            "not_interaction_evidence": True,
            "must_report_as": "geometry-only learned/evaluated route or claim-control evidence",
        },
        "required_controls": [
            "distance_geometry_baseline",
            "scale_control",
            "coverage_control",
            "source_score_rank_control",
            "class_pair_control",
            "shuffled_g_wrong_pair_geometry",
            "wording_guard",
        ],
        "legacy_shortcut_audit": {
            "status": schema_audit_summary.get("status"),
            "critical_blockers_reinterpreted_as_route_property": schema_audit_summary.get("critical_blockers"),
            "main_claim_verdict_old": schema_audit_summary.get("main_claim_verdict"),
            "learned_smoke_allowed_old": schema_audit_summary.get("learned_smoke_allowed"),
            "selected_high_risk_probes": high_risk,
        },
    }


def split_or_group_manifest(model_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> dict[str, Any]:
    hidden_by_route = {row["route_row_id"]: row for row in hidden_rows}
    subset_counts = Counter(row.get("subset") for row in model_rows)
    role_counts = Counter(row.get("role") for row in model_rows)
    label_counts = Counter(row.get("route_targets", {}).get("geometry_support_label") for row in model_rows)
    scans = {
        hidden_by_route[row["route_row_id"]].get("identity", {}).get("scan_id")
        for row in model_rows
        if row["route_row_id"] in hidden_by_route
    }
    class_pairs = {
        hidden_by_route[row["route_row_id"]].get("hidden_controls", {}).get("subject_object_class_pair")
        for row in model_rows
        if row["route_row_id"] in hidden_by_route
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "route_id": ROUTE_ID,
        "split_policy": "train_only",
        "grouping_policy": {
            "model_training_now": False,
            "recommended_group_keys_if_later_used": ["scan_id", "directed_pair_id"],
            "group_keys_location": "hidden_manifest.jsonl only",
        },
        "counts": {
            "rows": len(model_rows),
            "subset_counts": dict(sorted(subset_counts.items())),
            "role_counts": dict(sorted(role_counts.items())),
            "geometry_support_label_counts": dict(sorted(label_counts.items())),
            "unique_scans_hidden": len({scan for scan in scans if scan}),
            "unique_class_pairs_hidden": len({pair for pair in class_pairs if pair}),
        },
        "leakage_guard": {
            "scan_id_in_model_features": False,
            "directed_pair_id_in_model_features": False,
            "construction_bucket_in_model_features": False,
            "distance_bins_in_model_features": False,
            "row_id_is_metadata_not_feature": True,
        },
    }


def count_rows(model_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    subset_counts = Counter(row.get("subset") for row in model_rows)
    role_counts = Counter(row.get("role") for row in model_rows)
    label_counts = Counter(row.get("route_targets", {}).get("geometry_support_label") for row in model_rows)
    binary_counts = Counter(row.get("route_targets", {}).get("geometry_support_binary") for row in model_rows)
    row_counts = []
    for key, value in sorted(subset_counts.items()):
        row_counts.append({"count_type": "subset", "name": key, "rows": value})
    for key, value in sorted(role_counts.items()):
        row_counts.append({"count_type": "role", "name": key, "rows": value})
    label_rows = []
    for key, value in sorted(label_counts.items()):
        label_rows.append({"label_field": "geometry_support_label", "label": key, "rows": value})
    for key, value in sorted(binary_counts.items(), key=lambda kv: str(kv[0])):
        label_rows.append({"label_field": "geometry_support_binary", "label": key, "rows": value})
    return row_counts, label_rows


def render_report(summary: dict[str, Any]) -> str:
    counts = summary["row_counts"]
    return f"""# H002 R1 Close-By Geometry-Support Route Materialization

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Route

```text
route_id = R1
family = proximity
relation = close by
target_axis = geometry_support
route_type = geometry_only_learned_evaluated_route
```

## What Was Materialized

The existing close-by train-only rows were normalized into the route-specific
root:

```text
artifacts/route_specific_targets/r1_proximity/
```

The old `C_e_label` is no longer exposed. It is converted to
`geometry_support_label`, while `c_e_interaction_label` is fixed to
`not_applicable`.

| Component | Rows |
| --- | ---: |
| total | {counts['total_rows']} |
| primary geometry-support binary | {counts['primary_binary_rows']} |
| Q_e / abstain diagnostics | {counts['abstain_qe_rows']} |
| raw-distance diagnostic | {counts['raw_distance_diagnostic_rows']} |
| GT/geometry conflict audit | {counts['gt_geometry_conflict_audit_rows']} |

## Interpretation

- `close by` is geometry-only route evidence.
- Distance dominance is expected and should be reported as a route property.
- This route is not evidence that `T_e x G_e` interaction is needed.
- `T_e` and `Z_e` are retained only for annotation/source baselines.
- `Q_e` is retained for coverage and abstain diagnostics.

## Boundary

- Train-only route materialization.
- No validation/test used.
- No learned smoke or model training.
- No paper-level result claim.
- No H001 artifact modified.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()

    plan_summary = read_json(args.plan_dir / "summary.json")
    source_summary = read_json(args.source_dir / "summary.json")
    schema_audit_summary = read_json(args.schema_audit_dir / "summary.json")
    plan_errors = read_jsonl(args.plan_dir / "validation_errors.jsonl")
    source_errors = read_jsonl(args.source_dir / "validation_errors.jsonl")
    schema_audit_errors = read_jsonl(args.schema_audit_dir / "validation_errors.jsonl")
    source_model_rows = read_jsonl(args.source_dir / "model_safe_view.jsonl")
    source_hidden_rows = read_jsonl(args.source_dir / "hidden_manifest.jsonl")
    shortcut_rows = read_csv(args.schema_audit_dir / "shortcut_probes.csv")

    errors = validate_inputs(
        plan_summary,
        source_summary,
        schema_audit_summary,
        source_model_rows,
        source_hidden_rows,
        plan_errors,
        source_errors,
        schema_audit_errors,
    )

    hidden_by_source_id = {row["row_id"]: transform_hidden_row(row) for row in source_hidden_rows}
    model_rows = [transform_model_row(row) for row in source_model_rows]
    hidden_rows = [hidden_by_source_id[row["source_row_id_ref"]] for row in model_rows if row["source_row_id_ref"] in hidden_by_source_id]
    hidden_by_route_id = {row["route_row_id"]: row for row in hidden_rows}
    audit_rows = [build_audit_row(row, hidden_by_route_id[row["route_row_id"]]) for row in model_rows]

    errors.extend(output_validation(model_rows, hidden_rows, audit_rows, source_summary.get("row_counts", {})))

    status = STATUS_READY if not errors else STATUS_ERRORS
    output_paths = {
        "summary": args.output_dir / "summary.json",
        "schema": args.output_dir / "schema.json",
        "model_safe_rows": args.output_dir / "model_safe_rows.jsonl",
        "hidden_manifest": args.output_dir / "hidden_manifest.jsonl",
        "audit_view": args.output_dir / "audit_view.jsonl",
        "control_manifest": args.output_dir / "control_manifest.json",
        "split_or_group_manifest": args.output_dir / "split_or_group_manifest.json",
        "report": args.output_dir / "report.md",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
        "row_counts": args.output_dir / "row_counts.csv",
        "label_counts": args.output_dir / "label_counts.csv",
    }
    row_count_rows, label_count_rows = count_rows(model_rows, hidden_rows)
    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": True,
            "paper_evidence_allowed_now": False,
            "runs_model": False,
            "test_usage": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_artifacts": {
            "plan": rel_path(args.plan_dir),
            "source_materialization": rel_path(args.source_dir),
            "legacy_schema_audit": rel_path(args.schema_audit_dir),
        },
        "next_todo": NEXT_TODO,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "row_counts": source_summary.get("row_counts", {}),
        "route": {
            "route_id": ROUTE_ID,
            "family": ROUTE_FAMILY,
            "relation": ROUTE_RELATION,
            "route_type": ROUTE_TYPE,
            "target_axis": TARGET_AXIS,
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH,
        "status": status,
        "validation_errors": len(errors),
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["schema"], schema_payload())
    write_jsonl(output_paths["model_safe_rows"], model_rows)
    write_jsonl(output_paths["hidden_manifest"], hidden_rows)
    write_jsonl(output_paths["audit_view"], audit_rows)
    write_json(output_paths["control_manifest"], control_manifest_payload(schema_audit_summary, shortcut_rows))
    write_json(output_paths["split_or_group_manifest"], split_or_group_manifest(model_rows, hidden_rows))
    write_jsonl(output_paths["validation_errors"], errors)
    write_csv(output_paths["row_counts"], row_count_rows)
    write_csv(output_paths["label_counts"], label_count_rows)
    output_paths["report"].write_text(render_report(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
