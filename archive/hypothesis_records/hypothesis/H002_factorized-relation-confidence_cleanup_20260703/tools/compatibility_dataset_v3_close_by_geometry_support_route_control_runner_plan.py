#!/usr/bin/env python3
"""Plan the deterministic R1 close-by geometry-support route controls."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_ROUTE_ROOT = H2_ROOT / "artifacts/route_specific_targets/r1_proximity"
DEFAULT_SCHEMA_AUDIT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan"
)

EXPECTED_ROUTE_STATUS = "h002_compatibility_dataset_v3_close_by_geometry_support_route_materialization_after_plan_ready"
EXPECTED_SCHEMA_AUDIT_STATUS = "h002_compatibility_dataset_v3_close_by_geometry_support_schema_audit_after_materialization_ready"
EXPECTED_SCHEMA_AUDIT_NEXT = "compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_close_by_geometry_support_route_control_runner_plan_input_errors"
SELECTED_PATH = "plan_r1_close_by_geometry_only_route_controls_no_interaction_runner"
NEXT_TODO = "compatibility_dataset_v3_close_by_geometry_support_route_control_runner"

EXPECTED_TOTAL_ROWS = 1284
EXPECTED_PRIMARY_ROWS = 800
EXPECTED_PRIMARY_LABELS = {"geometry_supported": 400, "geometry_unsupported": 400}
EXPECTED_ALL_LABELS = {
    "abstain": 240,
    "audit_required": 4,
    "geometry_supported": 520,
    "geometry_unsupported": 520,
}

REQUIRED_CONTROLS = {
    "distance_geometry_baseline",
    "scale_control",
    "coverage_control",
    "source_score_rank_control",
    "class_pair_control",
    "shuffled_g_wrong_pair_geometry",
    "wording_guard",
}

REQUIRED_G_FEATURES = [
    "distance_xy",
    "distance_3d",
    "normalized_distance_xy",
    "normalized_distance_3d",
    "projected_iou_xy",
    "projected_subject_overlap_ratio",
    "projected_object_overlap_ratio",
    "subject_top_z",
    "subject_bottom_z",
    "object_top_z",
    "object_bottom_z",
]

REQUIRED_Q_FEATURES = [
    "geometry_available",
    "geometry_checkable",
    "feature_complete",
    "feature_missing_count",
]

REQUIRED_Z_FEATURES = [
    "semantic_score_norm",
    "semantic_score_raw",
    "rank_in_context",
    "predicate_rank_for_pair",
    "rank_band",
]

REQUIRED_HIDDEN_AUDIT_FIELDS = [
    "candidate_bucket",
    "distance_bucket",
    "geometry_status",
    "label_match_status",
    "norm_distance_bin",
    "p_geom_valid",
    "raw_distance_bin",
    "subject_object_class_pair",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-root", type=Path, default=DEFAULT_ROUTE_ROOT)
    parser.add_argument("--schema-audit-dir", type=Path, default=DEFAULT_SCHEMA_AUDIT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
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


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    value: Any = row
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def finite(value: Any) -> bool:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(parsed)


def validate_inputs(
    route_summary: dict[str, Any],
    schema_audit_summary: dict[str, Any],
    route_errors: list[dict[str, Any]],
    schema_audit_errors: list[dict[str, Any]],
    model_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    control_manifest: dict[str, Any],
    route_gate_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if route_summary.get("status") != EXPECTED_ROUTE_STATUS:
        errors.append({"error_type": "unexpected_route_status", "actual": route_summary.get("status")})
    if route_summary.get("validation_errors") != 0 or route_errors:
        errors.append(
            {
                "error_type": "route_validation_errors_present",
                "summary_count": route_summary.get("validation_errors"),
                "rows": len(route_errors),
            }
        )
    if schema_audit_summary.get("status") != EXPECTED_SCHEMA_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_schema_audit_status", "actual": schema_audit_summary.get("status")})
    if schema_audit_summary.get("next_todo") != EXPECTED_SCHEMA_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_schema_audit_next", "actual": schema_audit_summary.get("next_todo")})
    if schema_audit_summary.get("validation_errors") != 0 or schema_audit_errors:
        errors.append(
            {
                "error_type": "schema_audit_validation_errors_present",
                "summary_count": schema_audit_summary.get("validation_errors"),
                "rows": len(schema_audit_errors),
            }
        )
    if schema_audit_summary.get("passed_checks") != schema_audit_summary.get("total_checks"):
        errors.append(
            {
                "error_type": "schema_audit_not_all_passed",
                "passed": schema_audit_summary.get("passed_checks"),
                "total": schema_audit_summary.get("total_checks"),
            }
        )
    if len(model_rows) != EXPECTED_TOTAL_ROWS or len(hidden_rows) != EXPECTED_TOTAL_ROWS:
        errors.append({"error_type": "unexpected_row_count", "model": len(model_rows), "hidden": len(hidden_rows)})

    primary_rows = [row for row in model_rows if row.get("route_targets", {}).get("is_primary_binary")]
    primary_counts = Counter(row.get("route_targets", {}).get("geometry_support_label") for row in primary_rows)
    if len(primary_rows) != EXPECTED_PRIMARY_ROWS:
        errors.append({"error_type": "unexpected_primary_rows", "actual": len(primary_rows)})
    if dict(primary_counts) != EXPECTED_PRIMARY_LABELS:
        errors.append({"error_type": "unexpected_primary_label_counts", "actual": dict(primary_counts)})
    all_counts = Counter(row.get("route_targets", {}).get("geometry_support_label") for row in model_rows)
    if dict(all_counts) != EXPECTED_ALL_LABELS:
        errors.append({"error_type": "unexpected_all_label_counts", "actual": dict(all_counts)})

    controls = set(control_manifest.get("required_controls", []))
    missing_controls = sorted(REQUIRED_CONTROLS - controls)
    if missing_controls:
        errors.append({"error_type": "missing_required_controls", "missing": missing_controls})

    gate_by_name = {row.get("gate"): row for row in route_gate_rows}
    runner_gate = gate_by_name.get("route_control_runner_plan", {})
    interaction_gate = gate_by_name.get("learned_interaction_smoke", {})
    paper_gate = gate_by_name.get("paper_result_claim", {})
    if str(runner_gate.get("allowed")).lower() != "true":
        errors.append({"error_type": "runner_gate_not_allowed", "gate": runner_gate})
    if str(interaction_gate.get("allowed")).lower() != "false":
        errors.append({"error_type": "interaction_gate_not_blocked", "gate": interaction_gate})
    if str(paper_gate.get("allowed")).lower() != "false":
        errors.append({"error_type": "paper_gate_not_blocked", "gate": paper_gate})

    for name, summary in [("route", route_summary), ("schema_audit", schema_audit_summary)]:
        boundary = summary.get("boundary", {})
        for key in ["h001_artifacts_modified", "validation_usage", "test_usage", "runs_model"]:
            if boundary.get(key) is not False:
                errors.append(
                    {
                        "error_type": "boundary_not_false",
                        "summary": name,
                        "key": key,
                        "actual": boundary.get(key),
                    }
                )
    return errors


def feature_availability_rows(model_rows: list[dict[str, Any]], hidden_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for block, features, prefix in [
        ("G_e_route", REQUIRED_G_FEATURES, "feature_blocks.G_e_route"),
        ("Q_e_observability", REQUIRED_Q_FEATURES, "feature_blocks.Q_e_observability"),
        ("Z_e_source_baseline", REQUIRED_Z_FEATURES, "feature_blocks.Z_e_source_baseline"),
    ]:
        for feature in features:
            path = f"{prefix}.{feature}"
            present = sum(nested_get(row, path) is not None for row in model_rows)
            finite_count = sum(finite(nested_get(row, path)) for row in model_rows)
            rows.append(
                {
                    "view": "model_safe_rows",
                    "block": block,
                    "feature": feature,
                    "path": path,
                    "present_rows": present,
                    "finite_rows": finite_count,
                    "total_rows": len(model_rows),
                    "runner_use": runner_use_for_feature(block, feature),
                }
            )
    for feature in REQUIRED_HIDDEN_AUDIT_FIELDS:
        path = f"hidden_controls.{feature}"
        present = sum(nested_get(row, path) is not None for row in hidden_rows)
        finite_count = sum(finite(nested_get(row, path)) for row in hidden_rows)
        rows.append(
            {
                "view": "hidden_manifest",
                "block": "hidden_controls",
                "feature": feature,
                "path": path,
                "present_rows": present,
                "finite_rows": finite_count,
                "total_rows": len(hidden_rows),
                "runner_use": "audit/control only, never route score input",
            }
        )
    return rows


def runner_use_for_feature(block: str, feature: str) -> str:
    if block == "G_e_route":
        if feature.startswith("normalized_distance") or feature.startswith("distance"):
            return "primary deterministic geometry route baseline"
        if feature in {"subject_top_z", "subject_bottom_z", "object_top_z", "object_bottom_z"}:
            return "scale/extent diagnostic"
        return "secondary geometry diagnostic"
    if block == "Q_e_observability":
        return "coverage/abstain diagnostic only"
    if block == "Z_e_source_baseline":
        return "source/rank baseline only"
    return "diagnostic"


def runner_input_contract(route_root: Path) -> list[dict[str, Any]]:
    return [
        {
            "input_name": "model_safe_rows",
            "path": rel_path(route_root / "model_safe_rows.jsonl"),
            "required": True,
            "runner_use": "primary input for deterministic controls",
            "forbidden_use": "do not train T_e x G_e interaction model from R1",
        },
        {
            "input_name": "hidden_manifest",
            "path": rel_path(route_root / "hidden_manifest.jsonl"),
            "required": True,
            "runner_use": "class-pair, p_geom_valid, distance-bin, shuffled/wrong-pair audit controls only",
            "forbidden_use": "do not expose identity/construction fields as model-safe route features",
        },
        {
            "input_name": "control_manifest",
            "path": rel_path(route_root / "control_manifest.json"),
            "required": True,
            "runner_use": "control and claim-boundary contract",
            "forbidden_use": "do not reinterpret distance dominance as interaction success",
        },
        {
            "input_name": "split_or_group_manifest",
            "path": rel_path(route_root / "split_or_group_manifest.json"),
            "required": True,
            "runner_use": "train-only grouping/leakage guard",
            "forbidden_use": "no validation/test split construction",
        },
    ]


def metric_plan() -> list[dict[str, Any]]:
    return [
        {
            "metric": "AUROC",
            "target": "geometry_support_binary over primary_binary rows",
            "required_for": "all numeric score controls",
            "interpretation": "geometry-only route separability, not relation interaction",
        },
        {
            "metric": "best_threshold_accuracy",
            "target": "geometry_support_binary over primary_binary rows",
            "required_for": "distance, normalized-distance, p_geom_valid hidden baseline",
            "interpretation": "deterministic threshold behavior",
        },
        {
            "metric": "F1_at_best_threshold",
            "target": "geometry_support_binary over primary_binary rows",
            "required_for": "route score reporting",
            "interpretation": "binary geometry-support quality",
        },
        {
            "metric": "coverage_counts",
            "target": "all rows by subset and Q_e state",
            "required_for": "coverage_control",
            "interpretation": "what is decidable vs abstain/audit",
        },
        {
            "metric": "control_drop",
            "target": "true-G score minus shuffled/wrong-pair score",
            "required_for": "shuffled-G and wrong-pair geometry controls",
            "interpretation": "pair-specific geometry use",
        },
        {
            "metric": "wording_gate",
            "target": "report metadata",
            "required_for": "all outputs",
            "interpretation": "must say geometry-only route; must not say T_e x G_e evidence",
        },
    ]


def control_runner_plan() -> list[dict[str, Any]]:
    return [
        {
            "control_id": "C1",
            "control_name": "distance_xy",
            "score_source": "G_e_route.distance_xy",
            "rows": "primary_binary",
            "expected_behavior": "high separability; lower distance should imply geometry_supported",
            "allowed_claim": "distance-based geometry-support route baseline",
            "blocked_claim": "predicate-geometry interaction",
        },
        {
            "control_id": "C2",
            "control_name": "distance_3d",
            "score_source": "G_e_route.distance_3d",
            "rows": "primary_binary",
            "expected_behavior": "high separability, possibly slightly weaker than normalized distance",
            "allowed_claim": "raw 3D geometry diagnostic",
            "blocked_claim": "semantic compatibility",
        },
        {
            "control_id": "C3",
            "control_name": "normalized_distance_xy",
            "score_source": "G_e_route.normalized_distance_xy",
            "rows": "primary_binary",
            "expected_behavior": "strongest or near-strongest geometry-support signal",
            "allowed_claim": "scale-normalized proximity route evidence",
            "blocked_claim": "new relation predictor",
        },
        {
            "control_id": "C4",
            "control_name": "normalized_distance_3d",
            "score_source": "G_e_route.normalized_distance_3d",
            "rows": "primary_binary",
            "expected_behavior": "strong geometry-support signal",
            "allowed_claim": "scale-normalized 3D proximity diagnostic",
            "blocked_claim": "T_e x G_e interaction",
        },
        {
            "control_id": "C5",
            "control_name": "overlap_geometry",
            "score_source": "G_e_route.projected_iou_xy and overlap ratios",
            "rows": "primary_binary",
            "expected_behavior": "secondary, weaker than distance",
            "allowed_claim": "overlap is not the main proximity signal",
            "blocked_claim": "complete geometry evidence",
        },
        {
            "control_id": "C6",
            "control_name": "scale_control",
            "score_source": "raw distance vs normalized distance; vertical extent proxies",
            "rows": "primary_binary + raw_distance_diagnostic",
            "expected_behavior": "normalized distance should explain close-by better than raw distance in scale-varied rows",
            "allowed_claim": "route separates metric distance from object-scale effects",
            "blocked_claim": "scale alone defines close by",
        },
        {
            "control_id": "C7",
            "control_name": "coverage_control",
            "score_source": "Q_e_observability + subset labels",
            "rows": "all rows",
            "expected_behavior": "abstain/audit rows stay out of binary route metric",
            "allowed_claim": "Q_e gates decidability",
            "blocked_claim": "Q_e is relation truth",
        },
        {
            "control_id": "C8",
            "control_name": "source_score_rank",
            "score_source": "Z_e_source_baseline",
            "rows": "primary_binary",
            "expected_behavior": "source/rank should not replace geometry route score",
            "allowed_claim": "source baseline comparison",
            "blocked_claim": "source confidence defines geometry support",
        },
        {
            "control_id": "C9",
            "control_name": "class_pair_only",
            "score_source": "hidden_controls.subject_object_class_pair",
            "rows": "primary_binary",
            "expected_behavior": "audit-only leakage/memorization probe",
            "allowed_claim": "category shortcut risk report",
            "blocked_claim": "model-safe route feature",
        },
        {
            "control_id": "C10",
            "control_name": "p_geom_valid_hidden_baseline",
            "score_source": "hidden_controls.p_geom_valid",
            "rows": "primary_binary + diagnostic rows",
            "expected_behavior": "strong hidden geometry-rule reference",
            "allowed_claim": "reference diagnostic only",
            "blocked_claim": "deployable route input unless separately exposed/calibrated",
        },
        {
            "control_id": "C11",
            "control_name": "shuffled_G",
            "score_source": "G_e_route permuted across rows with labels fixed",
            "rows": "primary_binary",
            "expected_behavior": "degrade relative to true G_e",
            "allowed_claim": "pair-specific geometry control",
            "blocked_claim": "new learned model robustness",
        },
        {
            "control_id": "C12",
            "control_name": "wrong_pair_geometry",
            "score_source": "G_e_route from a different directed pair, preferably same subset/rank band when possible",
            "rows": "primary_binary",
            "expected_behavior": "degrade relative to true pair geometry",
            "allowed_claim": "object-pair alignment matters",
            "blocked_claim": "semantic relation grounding solved",
        },
    ]


def output_contract() -> list[dict[str, Any]]:
    return [
        {
            "file": "summary.json",
            "required": True,
            "content": "status, row counts, route, boundary, selected path, next todo",
        },
        {
            "file": "route_control_metrics.csv",
            "required": True,
            "content": "one row per control with AUROC/accuracy/F1/counts/control_drop where applicable",
        },
        {
            "file": "route_control_scores.jsonl",
            "required": True,
            "content": "optional row-level deterministic scores for audit only",
        },
        {
            "file": "control_failure_flags.csv",
            "required": True,
            "content": "flags for missing controls, leakage, or wording drift",
        },
        {
            "file": "report.md",
            "required": True,
            "content": "geometry-only route result narrative and blocked claims",
        },
        {
            "file": "validation_errors.jsonl",
            "required": True,
            "content": "empty when runner passes",
        },
    ]


def row_profile(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    subset_counts = Counter(row.get("subset") for row in model_rows)
    role_counts = Counter(row.get("role") for row in model_rows)
    label_counts = Counter(row.get("route_targets", {}).get("geometry_support_label") for row in model_rows)
    rows: list[dict[str, Any]] = []
    for name, counts in [("subset", subset_counts), ("role", role_counts), ("geometry_support_label", label_counts)]:
        for value, count in sorted(counts.items(), key=lambda kv: str(kv[0])):
            rows.append({"profile_type": name, "value": value, "rows": count})
    return rows


def collect_plan_errors(
    feature_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    route_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for row in feature_rows:
        if row["view"] == "model_safe_rows" and row["block"] in {"G_e_route", "Q_e_observability"}:
            if int(row["present_rows"]) != EXPECTED_TOTAL_ROWS:
                errors.append({"error_type": "required_feature_missing", **row})
    control_names = {row["control_name"] for row in control_rows}
    for required in [
        "distance_xy",
        "normalized_distance_xy",
        "scale_control",
        "coverage_control",
        "source_score_rank",
        "class_pair_only",
        "shuffled_G",
        "wrong_pair_geometry",
    ]:
        if required not in control_names:
            errors.append({"error_type": "missing_control_runner_plan", "control_name": required})
    boundary = route_summary.get("boundary", {})
    if boundary.get("validation_usage") is not False or boundary.get("test_usage") is not False:
        errors.append({"error_type": "route_boundary_uses_validation_or_test", "boundary": boundary})
    return errors


def render_report(summary: dict[str, Any]) -> str:
    return f"""# H002 R1 Close-By Geometry-Support Route Control Runner Plan

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Purpose

This artifact plans the deterministic control runner for the R1 `close by`
geometry-support route. It does not run metrics or train a model.

The runner must report `close by` as a geometry-only learned/evaluated route.
Distance dominance is expected and must not be promoted to `T_e x G_e`
interaction evidence.

## Planned Controls

- raw and normalized distance geometry baselines
- overlap geometry diagnostic
- raw-vs-normalized scale control
- coverage / abstain control
- source score and rank-only baseline
- class-pair hidden audit
- hidden `p_geom_valid` reference diagnostic
- shuffled-G and wrong-pair geometry controls

## Boundary

- Train-only plan.
- No validation/test used.
- No model run.
- No paper-level claim.
- H001 artifacts are not modified.
- Learned interaction smoke is blocked for R1.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()

    route_summary = read_json(args.route_root / "summary.json")
    schema_audit_summary = read_json(args.schema_audit_dir / "summary.json")
    control_manifest = read_json(args.route_root / "control_manifest.json")
    model_rows = read_jsonl(args.route_root / "model_safe_rows.jsonl")
    hidden_rows = read_jsonl(args.route_root / "hidden_manifest.jsonl")
    route_errors = read_jsonl(args.route_root / "validation_errors.jsonl")
    schema_audit_errors = read_jsonl(args.schema_audit_dir / "validation_errors.jsonl")
    route_gate_rows = read_csv(args.schema_audit_dir / "route_runner_gate.csv")

    errors = validate_inputs(
        route_summary,
        schema_audit_summary,
        route_errors,
        schema_audit_errors,
        model_rows,
        hidden_rows,
        control_manifest,
        route_gate_rows,
    )

    feature_rows = feature_availability_rows(model_rows, hidden_rows)
    control_rows = control_runner_plan()
    errors.extend(collect_plan_errors(feature_rows, control_rows, route_summary))

    status = STATUS_READY if not errors else STATUS_ERRORS
    output_paths = {
        "summary": args.output_dir / "summary.json",
        "report": args.output_dir / "report.md",
        "runner_input_contract": args.output_dir / "runner_input_contract.csv",
        "feature_availability": args.output_dir / "feature_availability.csv",
        "metric_plan": args.output_dir / "metric_plan.csv",
        "control_runner_plan": args.output_dir / "control_runner_plan.csv",
        "row_profile": args.output_dir / "row_profile.csv",
        "output_contract": args.output_dir / "output_contract.csv",
        "route_runner_gate": args.output_dir / "route_runner_gate.csv",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    route_runner_gate = [
        {
            "gate": "route_control_runner",
            "allowed": status == STATUS_READY,
            "next_todo": NEXT_TODO,
            "reason": "plan passed; run deterministic geometry-only controls",
        },
        {
            "gate": "learned_interaction_smoke",
            "allowed": False,
            "next_todo": "not_allowed_for_r1",
            "reason": "R1 is geometry-only route evidence",
        },
        {
            "gate": "paper_result_claim",
            "allowed": False,
            "next_todo": "not_allowed_from_plan",
            "reason": "plan contains no executed metrics",
        },
    ]
    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed_now": False,
            "runs_model": False,
            "runs_metrics": False,
            "test_usage": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_artifacts": {
            "route_root": rel_path(args.route_root),
            "schema_audit": rel_path(args.schema_audit_dir),
        },
        "next_todo": NEXT_TODO,
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "planned_controls": len(control_rows),
        "route": route_summary.get("route", {}),
        "row_counts": route_summary.get("row_counts", {}),
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH,
        "status": status,
        "validation_errors": len(errors),
    }

    write_json(output_paths["summary"], summary)
    write_jsonl(output_paths["validation_errors"], errors)
    write_csv(output_paths["runner_input_contract"], runner_input_contract(args.route_root))
    write_csv(output_paths["feature_availability"], feature_rows)
    write_csv(output_paths["metric_plan"], metric_plan())
    write_csv(output_paths["control_runner_plan"], control_rows)
    write_csv(output_paths["row_profile"], row_profile(model_rows))
    write_csv(output_paths["output_contract"], output_contract())
    write_csv(output_paths["route_runner_gate"], route_runner_gate)
    output_paths["report"].write_text(render_report(summary), encoding="utf-8")


if __name__ == "__main__":
    main()
