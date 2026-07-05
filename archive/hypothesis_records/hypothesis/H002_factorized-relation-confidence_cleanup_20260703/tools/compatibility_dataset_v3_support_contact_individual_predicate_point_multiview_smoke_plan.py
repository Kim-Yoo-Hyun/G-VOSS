#!/usr/bin/env python3
"""Write the point/multiview support/contact compatibility smoke plan."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan"
)

EXPECTED_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_schema_shortcut_audit_ready_for_smoke_plan"
)
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan"
EXPECTED_INPUT_SCHEMA = (
    "h002_support_contact_individual_predicate_point_multiview_smoke_ready_view_v1"
)
SMOKE_READY_SCHEMA = (
    "h002_support_contact_individual_predicate_point_multiview_runner_ready_view_v1"
)
SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan_ready"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_plan_input_errors"
)
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_smoke_runner"

EXPECTED_ROWS = 640
EXPECTED_POSITIVE = 320
EXPECTED_NEGATIVE = 320
EXPECTED_PREDICATES = {"lying on": 320, "standing on": 320}
EXPECTED_FEATURE_BLOCKS = {
    "G_e_contact_patch",
    "G_e_obb_baseline",
    "G_e_point_pose",
    "Q_e_observability",
    "T_e",
}

SEMANTIC_SHORTCUT_AUROC_MAX = 0.70
PRIMARY_AUROC_MIN = 0.70
PRIMARY_GAIN_OVER_SINGLE_FACTOR_MIN = 0.05
POINT_CONTACT_GAIN_OVER_OBB_MIN = 0.03
GEOMETRY_DOMINANCE_MARGIN = 0.02
SHUFFLED_CONTROL_MARGIN = 0.05

FORBIDDEN_FEATURE_TOKENS = [
    "candidate_role",
    "construction",
    "geometry_status",
    "h001",
    "hidden",
    "label_match",
    "machine_hint",
    "matched",
    "p_geom",
    "prediction_id",
    "queue",
    "rank",
    "route_name",
    "scan_id",
    "semantic_score",
    "source_score",
    "source",
    "subgraph_id",
    "subject_id",
    "object_id",
    "target_source",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
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
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(value: str, prefix: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]}"


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    value: Any = row
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def feature_paths(value: Any, prefix: str = "") -> list[str]:
    if isinstance(value, dict):
        paths: list[str] = []
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            paths.extend(feature_paths(child, child_prefix))
        return paths
    if isinstance(value, list):
        return [prefix]
    return [prefix]


def numeric_value_count(rows: list[dict[str, Any]], path: str) -> tuple[int, int]:
    present = 0
    finite = 0
    for row in rows:
        value = nested_get(row, path)
        if value is None or value == "":
            continue
        present += 1
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(parsed):
            finite += 1
    return present, finite


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(int(row["target_y"]) for row in rows)
    predicates = Counter(str(nested_get(row, "feature_blocks.T_e.predicate_label")) for row in rows)
    schemas = Counter(str(row.get("schema_version")) for row in rows)
    blocks = Counter(tuple(sorted(row.get("feature_blocks", {}).keys())) for row in rows)
    cv_groups: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        cv_group = row.get("cv_group_id") or nested_get(row, "split_metadata.cv_group_id")
        cv_groups[str(cv_group)].append(int(row["target_y"]))
    mixed_cv_groups = sum(1 for values in cv_groups.values() if 0 in values and 1 in values)
    return {
        "cv_groups": len(cv_groups),
        "feature_block_sets": {",".join(key): count for key, count in sorted(blocks.items())},
        "mixed_label_cv_groups": mixed_cv_groups,
        "negative": labels[0],
        "positive": labels[1],
        "predicate_counts": dict(sorted(predicates.items())),
        "rows": len(rows),
        "schema_versions": dict(sorted(schemas.items())),
    }


def normalize_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        cv_group = nested_get(row, "split_metadata.cv_group_id") or row.get("cv_group_id")
        row_id = str(row.get("row_id"))
        normalized.append(
            {
                "cv_group_id": str(cv_group),
                "example_id": stable_hash(row_id, "ex"),
                "feature_blocks": row["feature_blocks"],
                "row_id": row_id,
                "schema_version": SMOKE_READY_SCHEMA,
                "split": "train",
                "target_y": int(row["target_y"]),
            }
        )
    return normalized


def validate_inputs(audit_summary: dict[str, Any], raw_rows: list[dict[str, Any]], smoke_rows: list[dict[str, Any]], audit_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit_summary.get("next_todo")})
    if int(audit_summary.get("validation_errors", -1)) != 0:
        errors.append({"error_type": "audit_validation_errors", "actual": audit_summary.get("validation_errors")})
    counts = audit_summary.get("counts", {})
    if counts.get("smoke_ready_rows") != EXPECTED_ROWS:
        errors.append({"error_type": "unexpected_audit_smoke_rows", "actual": counts.get("smoke_ready_rows")})
    if counts.get("target_counts") != {"0": EXPECTED_NEGATIVE, "1": EXPECTED_POSITIVE}:
        errors.append({"error_type": "unexpected_audit_target_counts", "actual": counts.get("target_counts")})
    if counts.get("allowed_high_risk_probes") != 0 or counts.get("schema_leakage_hits") != 0:
        errors.append({"error_type": "audit_shortcut_or_schema_leakage", "actual": counts})
    validation_path = audit_dir / "validation_errors.jsonl"
    if validation_path.exists() and validation_path.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_audit_validation_errors_file"})

    for name, rows in [("raw", raw_rows), ("smoke", smoke_rows)]:
        row_counts = count_summary(rows)
        if row_counts["rows"] != EXPECTED_ROWS:
            errors.append({"error_type": f"unexpected_{name}_row_count", **row_counts})
        if row_counts["positive"] != EXPECTED_POSITIVE or row_counts["negative"] != EXPECTED_NEGATIVE:
            errors.append({"error_type": f"unexpected_{name}_label_counts", **row_counts})
        if row_counts["predicate_counts"] != EXPECTED_PREDICATES:
            errors.append({"error_type": f"unexpected_{name}_predicate_counts", **row_counts})

    raw_counts = count_summary(raw_rows)
    if raw_counts["schema_versions"] != {EXPECTED_INPUT_SCHEMA: EXPECTED_ROWS}:
        errors.append({"error_type": "unexpected_raw_schema_versions", **raw_counts})
    smoke_counts = count_summary(smoke_rows)
    if smoke_counts["schema_versions"] != {SMOKE_READY_SCHEMA: EXPECTED_ROWS}:
        errors.append({"error_type": "unexpected_smoke_schema_versions", **smoke_counts})

    for row in smoke_rows:
        feature_blocks = row.get("feature_blocks", {})
        if set(feature_blocks) != EXPECTED_FEATURE_BLOCKS:
            errors.append({"error_type": "unexpected_feature_blocks", "row_id": row.get("row_id"), "blocks": sorted(feature_blocks)})
        feature_text = json.dumps(feature_blocks, ensure_ascii=False)
        for token in FORBIDDEN_FEATURE_TOKENS:
            if token in feature_text:
                errors.append({"error_type": "forbidden_token_in_feature_blocks", "row_id": row.get("row_id"), "token": token})
    return errors


def input_profile_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = [
        "feature_blocks.T_e.predicate_label",
        "feature_blocks.T_e.predicate_family",
        "feature_blocks.T_e.subject_class_text",
        "feature_blocks.T_e.object_class_text",
        "feature_blocks.G_e_obb_baseline.abs_surface_gap_subject_bottom_to_object_top",
        "feature_blocks.G_e_obb_baseline.xy_overlap_min_ratio",
        "feature_blocks.G_e_obb_baseline.obb_contact_likelihood_proxy",
        "feature_blocks.G_e_point_pose.subject_vertical_extent_ratio",
        "feature_blocks.G_e_point_pose.subject_horizontal_extent_ratio",
        "feature_blocks.G_e_point_pose.subject_flatness_proxy",
        "feature_blocks.G_e_point_pose.object_vertical_extent_ratio",
        "feature_blocks.G_e_contact_patch.point_abs_surface_gap_subject_bottom_to_object_top",
        "feature_blocks.G_e_contact_patch.point_xy_overlap_min_ratio",
        "feature_blocks.G_e_contact_patch.point_support_contact_likelihood_proxy",
        "feature_blocks.Q_e_observability.q_e_state_code",
        "feature_blocks.Q_e_observability.co_visible_view_count_proxy",
        "feature_blocks.Q_e_observability.min_subject_object_crop_count",
    ]
    output: list[dict[str, Any]] = []
    for path in paths:
        values = [nested_get(row, path) for row in rows]
        missing = sum(1 for value in values if value is None or value == "")
        distinct = len({json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values})
        present, finite = numeric_value_count(rows, path)
        output.append(
            {
                "distinct_values": distinct,
                "feature_path": path,
                "finite_numeric": finite,
                "missing": missing,
                "present": present,
                "rows": len(rows),
                "usable_as_feature": True,
            }
        )
    return output


def feature_path_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = sorted({path for row in rows for path in feature_paths(row.get("feature_blocks", {}), "feature_blocks")})
    return [{"feature_path": path, "model_input_allowed": True} for path in paths]


def model_view_rows() -> list[dict[str, Any]]:
    return [
        {"model": "M0_intercept", "input_blocks": "none", "primary": False, "role": "class-balance sanity baseline"},
        {"model": "M1_semantic_only_T", "input_blocks": "T_e", "primary": False, "role": "semantic/content shortcut baseline"},
        {"model": "M2_obb_geometry_only", "input_blocks": "G_e_obb_baseline", "primary": False, "role": "old OBB-only geometry baseline"},
        {"model": "M3_point_pose_only", "input_blocks": "G_e_point_pose", "primary": False, "role": "point extent/pose geometry ablation"},
        {"model": "M4_contact_patch_only", "input_blocks": "G_e_contact_patch", "primary": False, "role": "point contact/support ablation"},
        {"model": "M5_point_contact_geometry", "input_blocks": "G_e_point_pose + G_e_contact_patch", "primary": False, "role": "new geometry-only evidence baseline"},
        {"model": "M6_TG_obb_concat", "input_blocks": "T_e + G_e_obb_baseline", "primary": False, "role": "old OBB T+G baseline"},
        {"model": "M7_TG_point_contact_concat", "input_blocks": "T_e + G_e_point_pose + G_e_contact_patch", "primary": False, "role": "plain point/contact fusion"},
        {"model": "M8_TG_point_contact_interaction", "input_blocks": "T_e + G_e_point_pose + G_e_contact_patch", "primary": True, "role": "primary predicate-geometry compatibility smoke"},
        {"model": "M9_TGQ_factorized_observability", "input_blocks": "T_e + G_e_point_pose + G_e_contact_patch + Q_e_observability", "primary": False, "role": "observability-aware diagnostic; Q_e should not define truth"},
        {"model": "S1_predicate_label_shortcut", "input_blocks": "T_e.predicate_label", "primary": False, "role": "shortcut probe"},
        {"model": "S2_class_pair_shortcut", "input_blocks": "T_e.subject_class_text + T_e.object_class_text", "primary": False, "role": "shortcut probe"},
        {"model": "S3_quality_only_shortcut", "input_blocks": "Q_e_observability", "primary": False, "role": "Q_e shortcut probe"},
        {"model": "C1_wrong_T_same_G", "input_blocks": "wrong T_e + same G_e_point/contact", "primary": False, "role": "predicate-conditioning negative control"},
        {"model": "C2_shuffled_G_global", "input_blocks": "T_e + globally shuffled G_e_point/contact", "primary": False, "role": "geometry-alignment negative control"},
        {"model": "C3_shuffled_G_within_predicate", "input_blocks": "T_e + within-predicate shuffled G_e_point/contact", "primary": False, "role": "harder geometry-alignment control"},
        {"model": "C4_shuffled_Q", "input_blocks": "T_e + G_e_point/contact + shuffled Q_e", "primary": False, "role": "observability alignment control"},
    ]


def gate_rows() -> list[dict[str, Any]]:
    return [
        {"gate": "data_integrity", "criterion": "rows=640, labels=320/320, predicates standing on=320 and lying on=320", "blocks_runner_if_fail": True},
        {"gate": "schema_safety", "criterion": "runner reads only smoke_ready_view.jsonl feature_blocks; row_id/example_id/cv_group_id/target_y are metadata only", "blocks_runner_if_fail": True},
        {"gate": "semantic_shortcut_control", "criterion": f"M1/S1/S2 AUROC <= {SEMANTIC_SHORTCUT_AUROC_MAX:.2f}", "blocks_promotion_if_fail": True},
        {"gate": "quality_shortcut_control", "criterion": f"S3 AUROC <= {SEMANTIC_SHORTCUT_AUROC_MAX:.2f}", "blocks_promotion_if_fail": True},
        {"gate": "primary_signal", "criterion": f"primary M8 AUROC >= {PRIMARY_AUROC_MIN:.2f}", "blocks_promotion_if_fail": True},
        {"gate": "compatibility_gain", "criterion": f"M8 beats max(M1, M2, M3, M4, M5) by >= {PRIMARY_GAIN_OVER_SINGLE_FACTOR_MIN:.2f} AUROC", "blocks_promotion_if_fail": True},
        {"gate": "point_contact_expansion_gain", "criterion": f"M8 beats M6 old OBB T+G by >= {POINT_CONTACT_GAIN_OVER_OBB_MIN:.2f} AUROC", "blocks_promotion_if_fail": True},
        {"gate": "geometry_dominance_check", "criterion": f"if M5 is within {GEOMETRY_DOMINANCE_MARGIN:.2f} AUROC of M8, interpret as geometry-dominance diagnostic", "blocks_paper_claim_if_fail": True},
        {"gate": "shuffled_geometry_degradation", "criterion": f"C2/C3 should not exceed max(M1, M5)+{SHUFFLED_CONTROL_MARGIN:.2f}", "blocks_promotion_if_fail": True},
        {"gate": "wrong_T_degradation", "criterion": "C1 wrong-T same-G should degrade or invert relative to M8", "blocks_promotion_if_fail": True},
        {"gate": "Q_e_boundary", "criterion": "M9 gain over M8 is diagnostic; Q_e must not rescue a weak C_e target by itself", "blocks_paper_claim_if_fail": True},
        {"gate": "paper_boundary", "criterion": "train-only hypothesis smoke; Docker reproduction and held-out design required before paper evidence", "blocks_paper_evidence": True},
    ]


def control_rows() -> list[dict[str, Any]]:
    return [
        {"control": "wrong_T_same_G", "construction": "swap lying on <-> standing on in T_e while keeping G_e/Q_e and target", "expected_result": "predicate-conditioned compatibility should degrade"},
        {"control": "shuffled_G_global", "construction": "permute G_e_point_pose and G_e_contact_patch across all rows", "expected_result": "breaks aligned object-pair geometry"},
        {"control": "shuffled_G_within_predicate", "construction": "permute G_e_point/contact within each predicate label", "expected_result": "preserves predicate distribution while breaking paired geometry"},
        {"control": "shuffled_Q", "construction": "permute Q_e_observability across rows", "expected_result": "tests whether Q_e alignment contributes beyond coverage prior"},
        {"control": "no_interaction_concat", "construction": "compare M7 plain concat with M8 predicate-conditioned interaction", "expected_result": "if M8 does not improve, explicit compatibility interaction is not supported"},
        {"control": "old_OBB_vs_point_contact", "construction": "compare M6 OBB T+G with M8 point/contact T+G", "expected_result": "tests whether new G_e expansion actually helps"},
    ]


def smoke_plan(input_path: Path) -> dict[str, Any]:
    return {
        "controls": control_rows(),
        "feature_engineering": {
            "G_e_contact_patch": "point-derived support/contact proxies: surface gap, XY overlap, near-contact/support likelihood",
            "G_e_obb_baseline": "previous semseg OBB geometry baseline retained for ablation",
            "G_e_point_pose": "point-derived object extent, centroid, flatness, vertical/horizontal pose proxies",
            "Q_e_observability": "evidence availability and quality only, never a truth label",
            "T_e": "predicate and object class semantic content only",
            "Z_e_policy": "source confidence/rank stays hidden and excluded from this smoke",
            "primary_interaction": "predicate indicators modulate point/contact geometry features",
        },
        "gates": gate_rows(),
        "input_contract": {
            "allowed_blocks": sorted(EXPECTED_FEATURE_BLOCKS),
            "feature_root": "feature_blocks",
            "forbidden_as_features": FORBIDDEN_FEATURE_TOKENS,
            "group_key": "cv_group_id",
            "input_file": rel_path(input_path),
            "input_sha256": sha256_file(input_path),
            "metadata_only": ["row_id", "example_id", "cv_group_id", "schema_version", "split", "target_y"],
            "negative": EXPECTED_NEGATIVE,
            "positive": EXPECTED_POSITIVE,
            "row_count": EXPECTED_ROWS,
            "target": "target_y",
        },
        "metrics": ["AUROC", "AUPRC", "accuracy", "balanced_accuracy", "Brier", "ECE", "fold mean/std", "predicate-slice AUROC"],
        "models": model_view_rows(),
        "paper_boundary": {
            "docker_required_before_paper_promotion": True,
            "hypothesis_stage_only": True,
            "paper_evidence_allowed": False,
        },
        "schema_version": SCHEMA_VERSION,
        "split_policy": {
            "folds": 5,
            "group_key": "cv_group_id",
            "group_rule": "same scan hash stays in the same fold",
            "split": "train_internal_grouped_cv",
            "test_usage": False,
            "validation_usage": False,
        },
        "task": {
            "name": "support/contact individual predicate point-multiview C_e smoke",
            "not_in_scope": ["Z_e posterior", "p_rel final reliability", "p_obs abstention", "validation/test performance", "paper-level claim"],
            "target": "target_y",
            "target_semantics": "1 if predicate is compatible with route-aware support/contact geometry/evidence, otherwise 0",
        },
    }


def render_report(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    return f"""# H002 Support/Contact Individual Predicate Point/Multiview Smoke Plan

## Status

```text
artifact_root = {summary["output_paths"]["artifact_root"]}
status = {summary["status"]}
rows = {counts["rows"]}
positive / negative = {counts["positive"]} / {counts["negative"]}
predicate_counts = {json.dumps(counts["predicate_counts"], ensure_ascii=False, sort_keys=True)}
cv_groups = {counts["cv_groups"]}
mixed_label_cv_groups = {counts["mixed_label_cv_groups"]}
validation_errors = {summary["validation_errors"]}
learned_smoke_executed = false
next_todo = {summary["next_todo"]}
```

## Planned Main Comparison

- `M1_semantic_only_T`
- `M2_obb_geometry_only`
- `M3_point_pose_only`
- `M4_contact_patch_only`
- `M5_point_contact_geometry`
- `M6_TG_obb_concat`
- `M7_TG_point_contact_concat`
- `M8_TG_point_contact_interaction` as the primary compatibility smoke
- `M9_TGQ_factorized_observability`

## Required Controls

- wrong-T same-G
- shuffled-G global
- shuffled-G within predicate
- shuffled-Q
- no-interaction concat
- old OBB versus point/contact expansion

## Interpretation

This step does not train a model. It freezes the train-only grouped-CV smoke input
and the comparison contract. The runner must use only `smoke_ready_view.jsonl`;
hidden construction fields, source score/rank, H001 `p_geom_valid`, scan/object ids,
and visual paths remain outside model input.
"""


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    audit_summary = read_json(args.audit_dir / "summary.json")
    raw_rows = read_jsonl(args.audit_dir / "smoke_ready_view.jsonl")
    smoke_rows = normalize_rows(raw_rows)
    validation_errors = validate_inputs(audit_summary, raw_rows, smoke_rows, args.audit_dir)

    input_path = args.output_dir / "smoke_ready_view.jsonl"
    write_jsonl(input_path, smoke_rows)

    counts = count_summary(smoke_rows)
    plan = smoke_plan(input_path)
    status = STATUS_READY if not validation_errors else STATUS_ERROR
    output_paths = {
        "artifact_root": rel_path(args.output_dir),
        "control_plan": rel_path(args.output_dir / "control_plan.csv"),
        "feature_paths": rel_path(args.output_dir / "feature_paths.csv"),
        "gate_plan": rel_path(args.output_dir / "gate_plan.csv"),
        "input_manifest": rel_path(args.output_dir / "input_manifest.json"),
        "input_profile": rel_path(args.output_dir / "input_profile.csv"),
        "model_views": rel_path(args.output_dir / "model_views.csv"),
        "report": rel_path(args.output_dir / "report.md"),
        "smoke_plan": rel_path(args.output_dir / "smoke_plan.json"),
        "smoke_ready_view": rel_path(input_path),
        "summary": rel_path(args.output_dir / "summary.json"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
    }
    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_new_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_smoke_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
            "visual_model_input_allowed": False,
        },
        "counts": counts,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "audit_summary": rel_path(args.audit_dir / "summary.json"),
            "audit_smoke_ready_view": rel_path(args.audit_dir / "smoke_ready_view.jsonl"),
        },
        "learned_smoke_executed": False,
        "next_todo": NEXT_TODO,
        "output_paths": output_paths,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "validation_errors": len(validation_errors),
    }
    input_manifest = {
        "input_sha256": sha256_file(input_path),
        "input_rows": counts["rows"],
        "schema_version": SMOKE_READY_SCHEMA,
        "source_audit_summary": rel_path(args.audit_dir / "summary.json"),
        "source_audit_smoke_ready_view": rel_path(args.audit_dir / "smoke_ready_view.jsonl"),
    }

    write_csv(args.output_dir / "control_plan.csv", control_rows())
    write_csv(args.output_dir / "feature_paths.csv", feature_path_rows(smoke_rows))
    write_csv(args.output_dir / "gate_plan.csv", gate_rows())
    write_json(args.output_dir / "input_manifest.json", input_manifest)
    write_csv(args.output_dir / "input_profile.csv", input_profile_rows(smoke_rows))
    write_csv(args.output_dir / "model_views.csv", model_view_rows())
    write_json(args.output_dir / "smoke_plan.json", plan)
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_json(args.output_dir / "summary.json", summary)
    (args.output_dir / "report.md").write_text(render_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
