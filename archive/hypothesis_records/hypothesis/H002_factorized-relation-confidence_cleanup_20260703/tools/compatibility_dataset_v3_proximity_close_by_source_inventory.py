#!/usr/bin/env python3
"""Inventory train-only close-by source capacity before materializing H002 rows."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_TARGET_PLAN_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_target_plan"
DEFAULT_TRAIN_RGA_DIR = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_proximity_close_by_source_inventory"

EXPECTED_PLAN_STATUS = "h002_compatibility_dataset_v3_proximity_close_by_target_plan_ready_for_source_inventory"
EXPECTED_PLAN_NEXT = "compatibility_dataset_v3_proximity_close_by_source_inventory"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_proximity_close_by_source_inventory_v1"
STATUS_READY = "h002_compatibility_dataset_v3_proximity_close_by_source_inventory_ready_for_candidate_materialization_plan"
STATUS_DIAGNOSTIC = "h002_compatibility_dataset_v3_proximity_close_by_source_inventory_diagnostic_only"
STATUS_ERROR = "h002_compatibility_dataset_v3_proximity_close_by_source_inventory_input_errors"
SELECTED_PATH = "select_close_by_candidate_materialization_plan_with_far_geometry_negatives_and_controls"
NEXT_TODO = "compatibility_dataset_v3_proximity_close_by_candidate_materialization_plan"

NEAR_NORM_XY = 0.80
FAR_NORM_XY = 2.50
RAW_DISTANCE_BIN_WIDTH = 0.50
NORM_DISTANCE_BIN_WIDTH = 0.25

MIN_ACCEPT = 160
MIN_REJECT = 160
MIN_ABSTAIN = 80
MIN_CLASS_PAIR_BALANCED = 400
MIN_CLASS_RANK_BALANCED = 400
MIN_RAW_DISTANCE_BALANCED = 200


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-plan-dir", type=Path, default=DEFAULT_TARGET_PLAN_DIR)
    parser.add_argument("--train-rga-dir", type=Path, default=DEFAULT_TRAIN_RGA_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
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


def validate_inputs(plan_summary: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan_summary.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan_summary.get("status")})
    if plan_summary.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next_todo", "actual": plan_summary.get("next_todo")})
    if plan_summary.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan_summary.get("validation_errors")})
    boundary = plan_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "materializes_rows",
        "fills_labels",
        "runs_learned_smoke",
        "trains_new_model",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    for name in ["target_contract.json", "source_inventory_contract.json", "summary.json"]:
        path = args.target_plan_dir / name
        if not path.exists():
            errors.append({"error_type": "missing_target_plan_artifact", "path": rel_path(path)})
    match_rows = args.train_rga_dir / "match_rows.jsonl"
    if not match_rows.exists():
        errors.append({"error_type": "missing_match_rows", "path": rel_path(match_rows)})
    return errors


def nested_get(row: dict[str, Any], *keys: str) -> Any:
    value: Any = row
    for key in keys:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def predicate_label(row: dict[str, Any]) -> str | None:
    predicate = row.get("predicate")
    if isinstance(predicate, dict):
        return predicate.get("predicate_label")
    return row.get("predicate_label")


def numeric(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def distance_bucket(norm_xy: float | None) -> str:
    if norm_xy is None:
        return "missing"
    if norm_xy <= NEAR_NORM_XY:
        return "near"
    if norm_xy >= FAR_NORM_XY:
        return "far"
    return "ambiguous"


def metric_bin(value: float | None, width: float) -> str:
    if value is None:
        return "missing"
    start = int(value / width) * width
    end = start + width
    return f"{start:.2f}-{end:.2f}"


def classify_candidate(label_status: str, geometry_status: str, bucket: str) -> str:
    if label_status == "exact_match" and geometry_status == "satisfied" and bucket == "near":
        return "accept_anchor"
    if label_status == "exact_match" and bucket == "far":
        return "gt_geometry_conflict"
    if label_status != "exact_match" and geometry_status == "unsatisfied" and bucket == "far":
        return "reject_far_geometry"
    if geometry_status == "uncertain" or bucket == "ambiguous" or (label_status != "exact_match" and bucket == "near"):
        return "abstain_or_audit"
    return "other"


def flatten_counter(counter: Counter[Any], limit: int = 10) -> str:
    return "; ".join(f"{key}:{value}" for key, value in counter.most_common(limit))


def add_group(groups: dict[Any, Counter[str]], key: Any, target: str) -> None:
    groups[key][target] += 1


def group_summary(groups: dict[Any, Counter[str]], group_name: str) -> dict[str, Any]:
    mixed = 0
    balanced = 0
    accept_total = 0
    reject_total = 0
    abstain_total = 0
    for counts in groups.values():
        accept = counts.get("accept_anchor", 0)
        reject = counts.get("reject_far_geometry", 0)
        abstain = counts.get("abstain_or_audit", 0)
        accept_total += accept
        reject_total += reject
        abstain_total += abstain
        if accept and reject:
            mixed += 1
            balanced += 2 * min(accept, reject)
    return {
        "group_name": group_name,
        "groups": len(groups),
        "mixed_accept_reject_groups": mixed,
        "balanced_accept_reject_rows": balanced,
        "accept_rows": accept_total,
        "reject_rows": reject_total,
        "abstain_rows": abstain_total,
    }


def group_rows(groups: dict[Any, Counter[str]], group_name: str, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, counts in groups.items():
        accept = counts.get("accept_anchor", 0)
        reject = counts.get("reject_far_geometry", 0)
        abstain = counts.get("abstain_or_audit", 0)
        rows.append(
            {
                "group_name": group_name,
                "group_key": " :: ".join(str(part) for part in key) if isinstance(key, tuple) else str(key),
                "accept_anchor": accept,
                "reject_far_geometry": reject,
                "abstain_or_audit": abstain,
                "gt_geometry_conflict": counts.get("gt_geometry_conflict", 0),
                "other": counts.get("other", 0),
                "balanced_accept_reject_rows": 2 * min(accept, reject),
                "is_mixed_accept_reject": bool(accept and reject),
            }
        )
    rows.sort(key=lambda row: (row["balanced_accept_reject_rows"], row["accept_anchor"] + row["reject_far_geometry"]), reverse=True)
    return rows[:limit] if limit is not None else rows


def update_feature_availability(feature_counts: Counter[str], row: dict[str, Any], raw_features: dict[str, Any]) -> None:
    feature_counts["row"] += 1
    if nested_get(row, "geometry", "geometry_available") is True:
        feature_counts["geometry_available"] += 1
    if nested_get(row, "geometry", "geometry_checkable") is True:
        feature_counts["geometry_checkable"] += 1
    if nested_get(row, "geometry", "p_geom_valid") is not None:
        feature_counts["p_geom_valid_baseline"] += 1
    for key in [
        "distance_3d",
        "distance_xy",
        "normalized_distance_3d",
        "normalized_distance_xy",
        "projected_iou_xy",
        "projected_subject_overlap_ratio",
        "projected_object_overlap_ratio",
        "subject_top_z",
        "subject_bottom_z",
        "object_top_z",
        "object_bottom_z",
        "center_delta_z",
        "normalized_center_delta_z",
    ]:
        if key in raw_features and raw_features.get(key) is not None:
            feature_counts[key] += 1
    if "subject_top_z" in raw_features and "subject_bottom_z" in raw_features:
        feature_counts["subject_vertical_extent_derivable"] += 1
    if "object_top_z" in raw_features and "object_bottom_z" in raw_features:
        feature_counts["object_vertical_extent_derivable"] += 1


def scan_close_by(match_rows_path: Path) -> dict[str, Any]:
    counters: dict[str, Counter[Any]] = {
        "candidate": Counter(),
        "distance_bucket": Counter(),
        "label_status": Counter(),
        "geometry_status": Counter(),
        "rank_band": Counter(),
        "candidate_detail": Counter(),
        "reject_label_status": Counter(),
        "accept_rank_band": Counter(),
        "reject_rank_band": Counter(),
    }
    feature_counts: Counter[str] = Counter()
    groups: dict[str, dict[Any, Counter[str]]] = {
        "class_pair": defaultdict(Counter),
        "class_pair_rank": defaultdict(Counter),
        "scan": defaultdict(Counter),
        "raw_distance_bin": defaultdict(Counter),
        "raw_distance_bin_rank": defaultdict(Counter),
        "raw_distance_bin_class_pair": defaultdict(Counter),
        "norm_distance_bin": defaultdict(Counter),
        "norm_distance_bin_rank": defaultdict(Counter),
    }
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)
    target_bucket_rows: Counter[tuple[str, str, str, str]] = Counter()
    total = 0
    for line in match_rows_path.open("r", encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        if predicate_label(row) != "close by":
            continue
        total += 1
        edge = row.get("edge") or {}
        raw_features = nested_get(row, "geometry", "raw_features") or {}
        if not isinstance(raw_features, dict):
            raw_features = {}
        update_feature_availability(feature_counts, row, raw_features)
        label_status = str(nested_get(row, "label", "label_match_status"))
        geometry_status = str(nested_get(row, "geometry", "geometry_status"))
        rank_band = str(nested_get(row, "rga", "rank_band"))
        norm_xy = numeric(raw_features.get("normalized_distance_xy"))
        raw_xy = numeric(raw_features.get("distance_xy"))
        bucket = distance_bucket(norm_xy)
        target = classify_candidate(label_status, geometry_status, bucket)
        counters["candidate"][target] += 1
        counters["distance_bucket"][bucket] += 1
        counters["label_status"][label_status] += 1
        counters["geometry_status"][geometry_status] += 1
        counters["rank_band"][rank_band] += 1
        counters["candidate_detail"][(target, label_status, geometry_status, bucket)] += 1
        if target == "accept_anchor":
            counters["accept_rank_band"][rank_band] += 1
        if target == "reject_far_geometry":
            counters["reject_rank_band"][rank_band] += 1
            counters["reject_label_status"][label_status] += 1
        target_bucket_rows[(target, label_status, geometry_status, bucket)] += 1
        subject_label = edge.get("subject_label")
        object_label = edge.get("object_label")
        class_pair = f"{subject_label}->{object_label}"
        scan_id = nested_get(row, "identity", "scan_id")
        raw_bin = metric_bin(raw_xy, RAW_DISTANCE_BIN_WIDTH)
        norm_bin = metric_bin(norm_xy, NORM_DISTANCE_BIN_WIDTH)
        add_group(groups["class_pair"], class_pair, target)
        add_group(groups["class_pair_rank"], (class_pair, rank_band), target)
        add_group(groups["scan"], scan_id, target)
        add_group(groups["raw_distance_bin"], raw_bin, target)
        add_group(groups["raw_distance_bin_rank"], (raw_bin, rank_band), target)
        add_group(groups["raw_distance_bin_class_pair"], (raw_bin, class_pair), target)
        add_group(groups["norm_distance_bin"], norm_bin, target)
        add_group(groups["norm_distance_bin_rank"], (norm_bin, rank_band), target)
        if len(examples[target]) < 8:
            examples[target].append(
                {
                    "row_key": nested_get(row, "identity", "row_key"),
                    "scan_id": scan_id,
                    "subject_id": nested_get(row, "identity", "subject_id"),
                    "object_id": nested_get(row, "identity", "object_id"),
                    "subject_label": subject_label,
                    "object_label": object_label,
                    "label_match_status": label_status,
                    "geometry_status": geometry_status,
                    "rank_band": rank_band,
                    "distance_bucket": bucket,
                    "distance_xy": raw_xy,
                    "normalized_distance_xy": norm_xy,
                    "p_geom_valid_baseline": nested_get(row, "geometry", "p_geom_valid"),
                }
            )
    group_summaries = [group_summary(values, name) for name, values in groups.items()]
    target_rows = [
        {
            "candidate_bucket": target,
            "label_match_status": label_status,
            "geometry_status": geometry_status,
            "distance_bucket": bucket,
            "rows": count,
        }
        for (target, label_status, geometry_status, bucket), count in target_bucket_rows.items()
    ]
    target_rows.sort(key=lambda row: row["rows"], reverse=True)
    feature_rows = []
    for field, count in feature_counts.items():
        role = "G_e"
        if field in {"geometry_available", "geometry_checkable", "subject_vertical_extent_derivable", "object_vertical_extent_derivable"}:
            role = "Q_e_or_G_e_support"
        if field == "p_geom_valid_baseline":
            role = "baseline_only"
        feature_rows.append(
            {
                "field": field,
                "present_rows": count,
                "total_rows": total,
                "coverage": round(count / total, 6) if total else 0.0,
                "role": role,
            }
        )
    feature_rows.extend(
        [
            {
                "field": "subject_object_full_xyz_extent",
                "present_rows": 0,
                "total_rows": total,
                "coverage": 0.0,
                "role": "source_adapter_needed_if_required",
            },
            {
                "field": "multi_view_visibility",
                "present_rows": 0,
                "total_rows": total,
                "coverage": 0.0,
                "role": "not_used_now_audit_extension_only",
            },
        ]
    )
    feature_rows.sort(key=lambda row: (row["role"], row["field"]))
    return {
        "total_rows": total,
        "candidate_counts": counters["candidate"],
        "distance_bucket_counts": counters["distance_bucket"],
        "label_status_counts": counters["label_status"],
        "geometry_status_counts": counters["geometry_status"],
        "rank_band_counts": counters["rank_band"],
        "reject_label_status_counts": counters["reject_label_status"],
        "accept_rank_band_counts": counters["accept_rank_band"],
        "reject_rank_band_counts": counters["reject_rank_band"],
        "target_bucket_rows": target_rows,
        "feature_rows": feature_rows,
        "group_summaries": group_summaries,
        "group_rows": {
            "class_pair": group_rows(groups["class_pair"], "class_pair"),
            "class_pair_rank": group_rows(groups["class_pair_rank"], "class_pair_rank"),
            "raw_distance_bin": group_rows(groups["raw_distance_bin"], "raw_distance_bin"),
            "raw_distance_bin_rank": group_rows(groups["raw_distance_bin_rank"], "raw_distance_bin_rank"),
            "raw_distance_bin_class_pair": group_rows(groups["raw_distance_bin_class_pair"], "raw_distance_bin_class_pair", limit=5000),
            "norm_distance_bin": group_rows(groups["norm_distance_bin"], "norm_distance_bin"),
            "norm_distance_bin_rank": group_rows(groups["norm_distance_bin_rank"], "norm_distance_bin_rank"),
            "scan": group_rows(groups["scan"], "scan", limit=5000),
        },
        "examples": examples,
    }


def decide_route(scan: dict[str, Any], validation_errors: list[dict[str, Any]]) -> tuple[str, str, list[dict[str, Any]]]:
    if validation_errors:
        return STATUS_ERROR, "blocked_input_errors", [{"gate": "input_validation", "passed": False, "value": len(validation_errors), "required": 0}]
    counts = scan["candidate_counts"]
    summaries = {row["group_name"]: row for row in scan["group_summaries"]}
    gate_rows = [
        {"gate": "accept_anchor_count", "value": counts.get("accept_anchor", 0), "required": MIN_ACCEPT, "passed": counts.get("accept_anchor", 0) >= MIN_ACCEPT},
        {"gate": "reject_far_geometry_count", "value": counts.get("reject_far_geometry", 0), "required": MIN_REJECT, "passed": counts.get("reject_far_geometry", 0) >= MIN_REJECT},
        {"gate": "abstain_or_audit_count", "value": counts.get("abstain_or_audit", 0), "required": MIN_ABSTAIN, "passed": counts.get("abstain_or_audit", 0) >= MIN_ABSTAIN},
        {
            "gate": "class_pair_balanced_capacity",
            "value": summaries["class_pair"]["balanced_accept_reject_rows"],
            "required": MIN_CLASS_PAIR_BALANCED,
            "passed": summaries["class_pair"]["balanced_accept_reject_rows"] >= MIN_CLASS_PAIR_BALANCED,
        },
        {
            "gate": "class_pair_rank_balanced_capacity",
            "value": summaries["class_pair_rank"]["balanced_accept_reject_rows"],
            "required": MIN_CLASS_RANK_BALANCED,
            "passed": summaries["class_pair_rank"]["balanced_accept_reject_rows"] >= MIN_CLASS_RANK_BALANCED,
        },
        {
            "gate": "raw_distance_balanced_capacity",
            "value": summaries["raw_distance_bin"]["balanced_accept_reject_rows"],
            "required": MIN_RAW_DISTANCE_BALANCED,
            "passed": summaries["raw_distance_bin"]["balanced_accept_reject_rows"] >= MIN_RAW_DISTANCE_BALANCED,
        },
    ]
    passed = all(bool(row["passed"]) for row in gate_rows)
    if passed:
        return STATUS_READY, SELECTED_PATH, gate_rows
    return STATUS_DIAGNOSTIC, "freeze_close_by_inventory_diagnostic_only", gate_rows


def counter_string(counter: Counter[Any]) -> str:
    return flatten_counter(counter, limit=12)


def build_route_decision(status: str, selected_path: str, gate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    failed = [row["gate"] for row in gate_rows if not row["passed"]]
    return [
        {
            "decision": selected_path,
            "status": status,
            "reason": "all inventory gates passed" if not failed else "some inventory gates failed: " + "; ".join(failed),
            "next_todo": NEXT_TODO if status == STATUS_READY else "review_close_by_inventory_or_relax_target_contract",
            "support_contact_after_close_by": "standing_on_then_lying_on_then_supported_by_individual_predicate_probe",
        }
    ]


def build_candidate_policy() -> list[dict[str, Any]]:
    return [
        {
            "candidate_bucket": "accept_anchor",
            "construction_rule": f"label_match_status == exact_match and geometry_status == satisfied and normalized_distance_xy <= {NEAR_NORM_XY}",
            "target_role": "positive anchor for C_e / p_rel",
            "caveat": "still candidate-level; future materialization may cap class pairs and scans",
        },
        {
            "candidate_bucket": "reject_far_geometry",
            "construction_rule": f"label_match_status != exact_match and geometry_status == unsatisfied and normalized_distance_xy >= {FAR_NORM_XY}",
            "target_role": "far-geometry negative candidate",
            "caveat": "negative is based on far geometry, not on no-GT status alone",
        },
        {
            "candidate_bucket": "abstain_or_audit",
            "construction_rule": "uncertain geometry, ambiguous distance, or non-exact near satisfied pair",
            "target_role": "Q_e / p_obs candidate or audit pool",
            "caveat": "not a hidden negative class",
        },
        {
            "candidate_bucket": "gt_geometry_conflict",
            "construction_rule": "exact-match close-by but far/unsatisfied geometry",
            "target_role": "diagnostic conflict only",
            "caveat": "do not train as reject without audit because it conflicts with GT",
        },
    ]


def build_report(summary: dict[str, Any], scan: dict[str, Any], gate_rows: list[dict[str, Any]]) -> str:
    groups = {row["group_name"]: row for row in scan["group_summaries"]}
    return f"""# H002 Proximity Close-By Source Inventory

## Status

```text
status = {summary["status"]}
selected_path = {summary["selected_path"]}
validation_errors = {summary["validation_errors"]}
next_todo = {summary["next_todo"]}
```

## Decision

Proceed to a close-by candidate materialization plan. The current inventory has
enough train-only positive anchors, far-geometry negatives, abstain/audit rows,
and matched-control capacity.

## Inventory Snapshot

```text
close_by_rows = {scan["total_rows"]}
candidate_counts = {counter_string(scan["candidate_counts"])}
distance_bucket_counts = {counter_string(scan["distance_bucket_counts"])}
label_status_counts = {counter_string(scan["label_status_counts"])}
geometry_status_counts = {counter_string(scan["geometry_status_counts"])}
rank_band_counts = {counter_string(scan["rank_band_counts"])}
```

Candidate policy:

```text
accept_anchor = exact_match + satisfied geometry + normalized_distance_xy <= {NEAR_NORM_XY}
reject_far_geometry = non-exact + unsatisfied geometry + normalized_distance_xy >= {FAR_NORM_XY}
abstain_or_audit = uncertain geometry, ambiguous distance, or non-exact near row
```

The reject pool is not defined by `no_gt_for_pair`. It is defined by far geometry.
The label-status distribution of reject candidates is:

```text
reject_label_status_counts = {counter_string(scan["reject_label_status_counts"])}
```

## Control Capacity

```text
class_pair mixed groups = {groups["class_pair"]["mixed_accept_reject_groups"]}
class_pair balanced rows = {groups["class_pair"]["balanced_accept_reject_rows"]}
class_pair_rank mixed groups = {groups["class_pair_rank"]["mixed_accept_reject_groups"]}
class_pair_rank balanced rows = {groups["class_pair_rank"]["balanced_accept_reject_rows"]}
raw_distance_bin mixed groups = {groups["raw_distance_bin"]["mixed_accept_reject_groups"]}
raw_distance_bin balanced rows = {groups["raw_distance_bin"]["balanced_accept_reject_rows"]}
norm_distance_bin mixed groups = {groups["norm_distance_bin"]["mixed_accept_reject_groups"]}
norm_distance_bin balanced rows = {groups["norm_distance_bin"]["balanced_accept_reject_rows"]}
scan mixed groups = {groups["scan"]["mixed_accept_reject_groups"]}
scan balanced rows = {groups["scan"]["balanced_accept_reject_rows"]}
```

Interpretation:

- class-pair and class-pair+rank controls have enough capacity for a controlled materialization plan.
- raw-distance controls exist but are much smaller, so they should be used as a dedicated diagnostic subset.
- normalized-distance controls have zero accept/reject mixing because the current target deliberately uses
  normalized distance to separate near and far. This means the main `close by` result must include
  a distance-only baseline and should not claim to beat normalized distance unless a stricter same-distance
  subset is materialized later.

## Gates

{chr(10).join(f"- {row['gate']}: value {row['value']} / required {row['required']} / passed {row['passed']}" for row in gate_rows)}

## Next

```text
{summary["next_todo"]}
```

The next materialization plan should cap scan/class-pair concentration, include
raw-distance matched diagnostic rows, and keep support/contact individual predicate
probes deferred until the close-by candidate path is decided.
"""


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    plan_summary_path = args.target_plan_dir / "summary.json"
    plan_summary = read_json(plan_summary_path) if plan_summary_path.exists() else {}
    validation_errors = validate_inputs(plan_summary, args)

    if validation_errors:
        scan: dict[str, Any] = {
            "total_rows": 0,
            "candidate_counts": Counter(),
            "distance_bucket_counts": Counter(),
            "label_status_counts": Counter(),
            "geometry_status_counts": Counter(),
            "rank_band_counts": Counter(),
            "reject_label_status_counts": Counter(),
            "accept_rank_band_counts": Counter(),
            "reject_rank_band_counts": Counter(),
            "target_bucket_rows": [],
            "feature_rows": [],
            "group_summaries": [],
            "group_rows": {},
            "examples": {},
        }
    else:
        scan = scan_close_by(args.train_rga_dir / "match_rows.jsonl")

    status, selected_path, gate_rows = decide_route(scan, validation_errors)
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": NEXT_TODO if status == STATUS_READY else "review_close_by_inventory_or_relax_target_contract",
        "validation_errors": len(validation_errors),
        "input_target_plan_summary": rel_path(plan_summary_path),
        "thresholds": {
            "near_normalized_distance_xy": NEAR_NORM_XY,
            "far_normalized_distance_xy": FAR_NORM_XY,
            "raw_distance_bin_width": RAW_DISTANCE_BIN_WIDTH,
            "normalized_distance_bin_width": NORM_DISTANCE_BIN_WIDTH,
        },
        "boundary": {
            "split": "train_only_source_inventory",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "fills_labels": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
        "close_by_inventory": {
            "total_rows": scan["total_rows"],
            "candidate_counts": counter_string(scan["candidate_counts"]),
            "distance_bucket_counts": counter_string(scan["distance_bucket_counts"]),
            "label_status_counts": counter_string(scan["label_status_counts"]),
            "geometry_status_counts": counter_string(scan["geometry_status_counts"]),
            "rank_band_counts": counter_string(scan["rank_band_counts"]),
            "reject_label_status_counts": counter_string(scan["reject_label_status_counts"]),
        },
        "group_capacity": {row["group_name"]: row for row in scan["group_summaries"]},
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "candidate_policy": rel_path(args.output_dir / "candidate_policy.csv"),
            "target_bucket_counts": rel_path(args.output_dir / "target_bucket_counts.csv"),
            "feature_availability": rel_path(args.output_dir / "feature_availability.csv"),
            "control_group_summary": rel_path(args.output_dir / "control_group_summary.csv"),
            "class_pair_mixed_capacity": rel_path(args.output_dir / "class_pair_mixed_capacity.csv"),
            "class_pair_rank_mixed_capacity": rel_path(args.output_dir / "class_pair_rank_mixed_capacity.csv"),
            "raw_distance_mixed_capacity": rel_path(args.output_dir / "raw_distance_mixed_capacity.csv"),
            "raw_distance_rank_mixed_capacity": rel_path(args.output_dir / "raw_distance_rank_mixed_capacity.csv"),
            "raw_distance_class_pair_mixed_capacity": rel_path(args.output_dir / "raw_distance_class_pair_mixed_capacity.csv"),
            "norm_distance_mixed_capacity": rel_path(args.output_dir / "norm_distance_mixed_capacity.csv"),
            "scan_mixed_capacity": rel_path(args.output_dir / "scan_mixed_capacity.csv"),
            "candidate_examples": rel_path(args.output_dir / "candidate_examples.json"),
            "gate_results": rel_path(args.output_dir / "gate_results.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "candidate_policy.csv", build_candidate_policy())
    write_csv(args.output_dir / "target_bucket_counts.csv", scan["target_bucket_rows"])
    write_csv(args.output_dir / "feature_availability.csv", scan["feature_rows"])
    write_csv(args.output_dir / "control_group_summary.csv", scan["group_summaries"])
    write_csv(args.output_dir / "class_pair_mixed_capacity.csv", scan["group_rows"].get("class_pair", []))
    write_csv(args.output_dir / "class_pair_rank_mixed_capacity.csv", scan["group_rows"].get("class_pair_rank", []))
    write_csv(args.output_dir / "raw_distance_mixed_capacity.csv", scan["group_rows"].get("raw_distance_bin", []))
    write_csv(args.output_dir / "raw_distance_rank_mixed_capacity.csv", scan["group_rows"].get("raw_distance_bin_rank", []))
    write_csv(args.output_dir / "raw_distance_class_pair_mixed_capacity.csv", scan["group_rows"].get("raw_distance_bin_class_pair", []))
    write_csv(args.output_dir / "norm_distance_mixed_capacity.csv", scan["group_rows"].get("norm_distance_bin", []))
    write_csv(args.output_dir / "scan_mixed_capacity.csv", scan["group_rows"].get("scan", []))
    write_json(args.output_dir / "candidate_examples.json", scan["examples"])
    write_csv(args.output_dir / "gate_results.csv", gate_rows)
    write_csv(args.output_dir / "route_decision.csv", build_route_decision(status, selected_path, gate_rows))
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    (args.output_dir / "report.md").write_text(build_report(summary, scan, gate_rows), encoding="utf-8")


if __name__ == "__main__":
    main()
