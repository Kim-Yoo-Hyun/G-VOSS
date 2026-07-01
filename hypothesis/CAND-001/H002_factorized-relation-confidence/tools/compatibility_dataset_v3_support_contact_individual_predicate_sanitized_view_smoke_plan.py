#!/usr/bin/env python3
"""Write the support/contact individual-predicate sanitized-view smoke plan."""

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
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan"
)

EXPECTED_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan"
)
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan"
EXPECTED_INPUT_SCHEMA = "h002_support_contact_individual_predicate_sanitized_view_v1"
SMOKE_READY_SCHEMA = "h002_support_contact_individual_predicate_smoke_ready_view_v1"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan_ready"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_plan_input_errors"
)
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner"

EXPECTED_ROWS = 640
EXPECTED_POSITIVE = 320
EXPECTED_NEGATIVE = 320
EXPECTED_PREDICATES = {"lying on": 320, "standing on": 320}
EXPECTED_FEATURE_BLOCKS = {"T_e", "G_e_mesh_pose_contact", "Q_e"}

SEMANTIC_SHORTCUT_AUROC_MAX = 0.60
GEOMETRY_ONLY_MAIN_CLAIM_MARGIN = 0.02
PRIMARY_AUROC_MIN = 0.70
PRIMARY_GAIN_OVER_T_OR_G_MIN = 0.05
SHUFFLED_G_DEGRADATION_MARGIN = 0.05

FORBIDDEN_FEATURE_TOKENS = [
    "candidate_role",
    "controls_hidden",
    "construction",
    "directed_pair",
    "geometry_status",
    "h001",
    "hidden",
    "label_match",
    "machine_hint",
    "matched",
    "p_geom_valid",
    "prediction_id",
    "queue",
    "rank",
    "route_name",
    "scan_id",
    "score",
    "source",
    "subgraph_id",
    "subject_id",
    "object_id",
    "target",
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
        cv_groups[str(row.get("cv_group_id"))].append(int(row["target_y"]))
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


def build_smoke_ready_rows(
    sanitized_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    hidden_by_row_id = {row.get("row_id"): row for row in hidden_rows}
    if len(hidden_by_row_id) != len(hidden_rows):
        errors.append({"error_type": "duplicate_hidden_row_id", "rows": len(hidden_rows), "unique": len(hidden_by_row_id)})

    smoke_rows: list[dict[str, Any]] = []
    for row in sanitized_rows:
        row_id = row.get("row_id")
        hidden = hidden_by_row_id.get(row_id)
        if hidden is None:
            errors.append({"error_type": "missing_hidden_for_sanitized_row", "row_id": row_id})
            continue
        scan_id = str(hidden.get("scan_id", "missing_scan"))
        smoke_rows.append(
            {
                "cv_group_id": stable_hash(scan_id, "scan"),
                "example_id": stable_hash(str(row_id), "ex"),
                "feature_blocks": row["feature_blocks"],
                "schema_version": SMOKE_READY_SCHEMA,
                "split": "train",
                "target_y": int(row["target_y"]),
            }
        )
    return smoke_rows, errors


def validate_inputs(
    audit_summary: dict[str, Any],
    sanitized_rows: list[dict[str, Any]],
    hidden_rows: list[dict[str, Any]],
    smoke_rows: list[dict[str, Any]],
    join_errors: list[dict[str, Any]],
    audit_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = list(join_errors)
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit_summary.get("next_todo")})
    if int(audit_summary.get("validation_errors", -1)) != 0:
        errors.append({"error_type": "audit_validation_errors", "actual": audit_summary.get("validation_errors")})
    counts = audit_summary.get("counts", {})
    if counts.get("sanitized_rows") != EXPECTED_ROWS:
        errors.append({"error_type": "unexpected_audit_sanitized_rows", "actual": counts.get("sanitized_rows")})
    if counts.get("target_counts") != {"0": EXPECTED_NEGATIVE, "1": EXPECTED_POSITIVE}:
        errors.append({"error_type": "unexpected_audit_target_counts", "actual": counts.get("target_counts")})
    if counts.get("allowed_high_risk_probes") != 0 or counts.get("schema_leakage_hits") != 0:
        errors.append({"error_type": "audit_shortcut_or_schema_leakage", "actual": counts})
    validation_path = audit_dir / "validation_errors.jsonl"
    if validation_path.exists() and validation_path.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_audit_validation_errors_file"})

    if len(hidden_rows) != 800:
        errors.append({"error_type": "unexpected_hidden_manifest_rows", "actual": len(hidden_rows)})

    input_counts = count_summary(sanitized_rows)
    if input_counts["rows"] != EXPECTED_ROWS:
        errors.append({"error_type": "unexpected_sanitized_row_count", **input_counts})
    if input_counts["positive"] != EXPECTED_POSITIVE or input_counts["negative"] != EXPECTED_NEGATIVE:
        errors.append({"error_type": "unexpected_sanitized_label_counts", **input_counts})
    if input_counts["predicate_counts"] != EXPECTED_PREDICATES:
        errors.append({"error_type": "unexpected_sanitized_predicate_counts", **input_counts})
    if input_counts["schema_versions"] != {EXPECTED_INPUT_SCHEMA: EXPECTED_ROWS}:
        errors.append({"error_type": "unexpected_sanitized_schema_versions", **input_counts})

    smoke_counts = count_summary(smoke_rows)
    if smoke_counts["rows"] != EXPECTED_ROWS:
        errors.append({"error_type": "unexpected_smoke_row_count", **smoke_counts})
    if smoke_counts["schema_versions"] != {SMOKE_READY_SCHEMA: EXPECTED_ROWS}:
        errors.append({"error_type": "unexpected_smoke_schema_versions", **smoke_counts})

    for row in smoke_rows:
        example_id = row.get("example_id")
        feature_blocks = row.get("feature_blocks", {})
        if set(feature_blocks) != EXPECTED_FEATURE_BLOCKS:
            errors.append({"error_type": "unexpected_feature_blocks", "example_id": example_id, "blocks": sorted(feature_blocks)})
        feature_text = json.dumps(feature_blocks, ensure_ascii=False)
        for token in FORBIDDEN_FEATURE_TOKENS:
            if token in feature_text:
                errors.append({"error_type": "forbidden_token_in_feature_blocks", "example_id": example_id, "token": token})
    return errors


def input_profile_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = [
        "feature_blocks.T_e.predicate_label",
        "feature_blocks.T_e.predicate_family",
        "feature_blocks.T_e.subject_class_text",
        "feature_blocks.T_e.object_class_text",
        "feature_blocks.G_e_mesh_pose_contact.surface_gap_subject_bottom_to_object_top",
        "feature_blocks.G_e_mesh_pose_contact.abs_surface_gap_subject_bottom_to_object_top",
        "feature_blocks.G_e_mesh_pose_contact.xy_overlap_min_ratio",
        "feature_blocks.G_e_mesh_pose_contact.support_area_proxy",
        "feature_blocks.G_e_mesh_pose_contact.normal_alignment",
        "feature_blocks.G_e_mesh_pose_contact.subject_flatness_ratio",
        "feature_blocks.G_e_mesh_pose_contact.subject_major_axis_upness",
        "feature_blocks.G_e_mesh_pose_contact.subject_vertical_extent_ratio",
        "feature_blocks.G_e_mesh_pose_contact.object_normal_upness",
        "feature_blocks.G_e_mesh_pose_contact.obb_contact_likelihood_proxy",
        "feature_blocks.Q_e.mesh_semseg_obb_available",
        "feature_blocks.Q_e.point_feature_available",
        "feature_blocks.Q_e.multi_view_feature_available",
        "feature_blocks.Q_e.missing_g_e_count",
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
        {
            "feature_engineering": "constant class-balance baseline",
            "input_blocks": "none",
            "model": "M0_intercept",
            "primary": False,
            "role": "sanity baseline",
        },
        {
            "feature_engineering": "predicate/object categorical features only",
            "input_blocks": "T_e",
            "model": "M1_semantic_only_T",
            "primary": False,
            "role": "semantic shortcut baseline; should remain near chance after schema audit",
        },
        {
            "feature_engineering": "predicate-independent support/contact pose, overlap, gap, normal, and flatness features",
            "input_blocks": "G_e_mesh_pose_contact",
            "model": "M2_geometry_only_G",
            "primary": False,
            "role": "geometry-only baseline; if it matches primary, this is geometry-dominance not compatibility evidence",
        },
        {
            "feature_engineering": "plain T_e + G_e concatenation without explicit predicate-conditioned interaction",
            "input_blocks": "T_e + G_e_mesh_pose_contact",
            "model": "M3_TG_concat",
            "primary": False,
            "role": "tests whether simple fusion is enough",
        },
        {
            "feature_engineering": "standing/lying predicate indicators multiplied by pose/contact features",
            "input_blocks": "T_e + G_e_mesh_pose_contact",
            "model": "M4_TG_predicate_geometry_interaction",
            "primary": True,
            "role": "primary C_e smoke for predicate-geometry compatibility",
        },
        {
            "feature_engineering": "M4 interaction plus evidence availability/quality covariates",
            "input_blocks": "T_e + G_e_mesh_pose_contact + Q_e",
            "model": "M5_TGQ_factorized_observability",
            "primary": False,
            "role": "checks whether Q_e changes the C_e route; Q_e is expected to be mostly constant here",
        },
        {
            "feature_engineering": "predicate label only",
            "input_blocks": "T_e.predicate_label",
            "model": "S1_predicate_label_shortcut",
            "primary": False,
            "role": "shortcut probe",
        },
        {
            "feature_engineering": "subject/object class pair only",
            "input_blocks": "T_e.subject_class_text + T_e.object_class_text",
            "model": "S2_class_pair_shortcut",
            "primary": False,
            "role": "class-pair shortcut probe",
        },
        {
            "feature_engineering": "Q_e only",
            "input_blocks": "Q_e",
            "model": "S3_quality_shortcut",
            "primary": False,
            "role": "observability shortcut probe",
        },
        {
            "feature_engineering": "swap lying on <-> standing on in T_e while preserving the same G_e",
            "input_blocks": "wrong T_e + same G_e_mesh_pose_contact",
            "model": "C1_wrong_T_same_G",
            "primary": False,
            "role": "negative control for predicate conditioning",
        },
        {
            "feature_engineering": "deterministically shuffle G_e across all rows",
            "input_blocks": "T_e + globally shuffled G_e_mesh_pose_contact",
            "model": "C2_shuffled_G_global",
            "primary": False,
            "role": "negative control for aligned geometry",
        },
        {
            "feature_engineering": "deterministically shuffle G_e within each predicate label",
            "input_blocks": "T_e + G_e_mesh_pose_contact shuffled within predicate",
            "model": "C3_shuffled_G_within_predicate",
            "primary": False,
            "role": "harder geometry alignment control",
        },
    ]


def gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocks_runner_if_fail": True,
            "criterion": "rows=640, labels=320/320, predicates standing on=320 and lying on=320",
            "gate": "data_integrity",
        },
        {
            "blocks_runner_if_fail": True,
            "criterion": "runner reads only smoke_ready_view.jsonl feature_blocks; example_id/cv_group_id/target_y are metadata only",
            "gate": "input_safety",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": f"M1/S1/S2/S3 AUROC <= {SEMANTIC_SHORTCUT_AUROC_MAX:.2f}",
            "gate": "semantic_and_quality_shortcuts_near_chance",
        },
        {
            "blocks_paper_claim_if_fail": True,
            "criterion": f"if M2 geometry-only is within {GEOMETRY_ONLY_MAIN_CLAIM_MARGIN:.2f} AUROC of M4/M5, result is geometry-dominance diagnostic",
            "gate": "geometry_dominance_check",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": f"primary M4 or M5 AUROC >= {PRIMARY_AUROC_MIN:.2f}",
            "gate": "primary_predictive_signal",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": f"primary M4/M5 beats max(M1,M2) by >= {PRIMARY_GAIN_OVER_T_OR_G_MIN:.2f} AUROC",
            "gate": "compatibility_gain_over_single_factor",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": "M4 should beat M3 concat, or runner must report that explicit interaction adds little beyond simple fusion",
            "gate": "interaction_over_concat",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": f"C2/C3 shuffled-G controls should not exceed max(M1,M2)+{SHUFFLED_G_DEGRADATION_MARGIN:.2f}",
            "gate": "shuffled_G_degradation",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": "C1 wrong-T same-G should degrade or invert relative to primary M4/M5",
            "gate": "wrong_T_same_G_degradation",
        },
        {
            "blocks_paper_evidence": True,
            "criterion": "hypothesis-stage train-only smoke; Docker reproduction and held-out design required before paper-level evidence",
            "gate": "paper_boundary",
        },
    ]


def control_rows() -> list[dict[str, Any]]:
    return [
        {
            "construction": "swap lying on <-> standing on in T_e while keeping G_e and original target",
            "control": "wrong_T_same_G",
            "expected_result": "predicate-conditioned compatibility should degrade or invert",
        },
        {
            "construction": "permute G_e blocks across all rows with a deterministic seed",
            "control": "shuffled_G_global",
            "expected_result": "breaks aligned geometry and should approach shortcut baselines",
        },
        {
            "construction": "permute G_e blocks within each predicate label",
            "control": "shuffled_G_within_predicate",
            "expected_result": "preserves predicate distribution while breaking object-pair geometry alignment",
        },
        {
            "construction": "compare M3 plain concatenation against M4 predicate-conditioned interaction",
            "control": "no_interaction_concat",
            "expected_result": "if M4 does not improve, explicit compatibility interaction is not supported on this target",
        },
    ]


def smoke_plan(input_path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = count_summary(rows)
    return {
        "controls": control_rows(),
        "feature_engineering": {
            "G_e_mesh_pose_contact": "predicate-independent semseg OBB support/contact geometry; no source score or p_geom_valid",
            "Q_e_policy": "observability/availability covariates only; not used as a truth label",
            "T_e": "predicate and object class semantic content; no source score/rank",
            "Z_e_policy": "no Z_e in this support/contact individual-predicate smoke; source confidence remains hidden audit-only",
            "predicate_conditioned_interactions": [
                "is_standing(predicate) * upright/vertical/support geometry features",
                "is_lying(predicate) * flatness/major-axis/support geometry features",
                "predicate-conditioned contact, gap, overlap, and normal-alignment features",
            ],
        },
        "gates": gate_rows(),
        "input_contract": {
            "allowed_blocks": ["T_e", "G_e_mesh_pose_contact", "Q_e"],
            "feature_root": "feature_blocks",
            "forbidden_as_features": FORBIDDEN_FEATURE_TOKENS,
            "group_key": "cv_group_id",
            "input_file": rel_path(input_path),
            "input_sha256": sha256_file(input_path),
            "metadata_only": ["example_id", "cv_group_id", "schema_version", "split", "target_y"],
            "negative": counts["negative"],
            "positive": counts["positive"],
            "row_count": counts["rows"],
            "target": "target_y",
        },
        "metrics": [
            "AUROC",
            "AUPRC",
            "accuracy",
            "balanced_accuracy",
            "Brier",
            "ECE",
            "fold-level mean/std",
            "predicate-slice AUROC for standing on and lying on",
        ],
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
            "group_rule": "all rows from the same scan hash stay in the same fold",
            "split": "train_internal_grouped_cv",
            "test_usage": False,
            "validation_usage": False,
        },
        "task": {
            "name": "Task A support/contact individual-predicate C_e smoke",
            "not_in_scope": [
                "source-confidence posterior Z_e",
                "p_rel final human reliability",
                "p_obs abstention target",
                "validation/test performance",
                "paper-level result claim",
            ],
            "target": "target_y in smoke_ready_view.jsonl",
            "target_semantics": "1 if the support/contact predicate is compatible with route-aware geometry/evidence, otherwise 0",
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Support/Contact Individual Predicate Sanitized View Smoke Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"positive / negative = {summary['counts']['positive']} / {summary['counts']['negative']}",
        f"predicate_counts = {summary['counts']['predicate_counts']}",
        f"cv_groups = {summary['counts']['cv_groups']}",
        f"validation_errors = {summary['validation_errors']}",
        f"learned_smoke_executed = {str(summary['learned_smoke_executed']).lower()}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Main Decision",
        "",
        "The learned smoke must read only the generated `smoke_ready_view.jsonl`.",
        "`example_id`, `cv_group_id`, `schema_version`, `split`, and `target_y` are metadata only.",
        "The raw materialized rows, hidden manifest, scan ids, source score/rank, H001",
        "`p_geom_valid`, label-match status, candidate role, route name, and construction fields",
        "must not be model features.",
        "",
        "The primary smoke is `M4_TG_predicate_geometry_interaction`. It tests whether",
        "`standing on` and `lying on` require different interpretations of the same",
        "predicate-independent support/contact geometry evidence.",
        "",
        "## Planned Baselines",
        "",
        "- `M1_semantic_only_T`",
        "- `M2_geometry_only_G`",
        "- `M3_TG_concat`",
        "- `M4_TG_predicate_geometry_interaction` as the primary `C_e` smoke",
        "- `M5_TGQ_factorized_observability`",
        "- `S1/S2/S3` shortcut probes",
        "",
        "## Planned Controls",
        "",
        "- wrong-T same-G",
        "- shuffled-G global",
        "- shuffled-G within predicate",
        "- no-interaction concat",
        "",
        "## Promotion Gates",
        "",
        f"- semantic/quality shortcuts should remain <= {SEMANTIC_SHORTCUT_AUROC_MAX:.2f} AUROC",
        f"- primary M4/M5 should reach >= {PRIMARY_AUROC_MIN:.2f} AUROC",
        f"- primary M4/M5 should beat max(M1,M2) by >= {PRIMARY_GAIN_OVER_T_OR_G_MIN:.2f} AUROC",
        f"- if geometry-only M2 is within {GEOMETRY_ONLY_MAIN_CLAIM_MARGIN:.2f} AUROC of M4/M5, the result is geometry-dominance diagnostic",
        "- wrong-T and shuffled-G controls must degrade",
        "",
        "## Boundary",
        "",
        "- train-only smoke plan",
        "- no learned smoke executed",
        "- no validation/test usage",
        "- no paper evidence promotion",
        "- no H001 artifact modification",
        "",
        "## Next",
        "",
        "```text",
        summary["next_todo"],
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    audit_summary = read_json(args.audit_dir / "summary.json")
    sanitized_path = args.audit_dir / "sanitized_view.jsonl"
    sanitized_rows = read_jsonl(sanitized_path)

    hidden_path = REPO_ROOT / audit_summary["input_paths"]["hidden_manifest"]
    hidden_rows = read_jsonl(hidden_path)
    smoke_rows, join_errors = build_smoke_ready_rows(sanitized_rows, hidden_rows)
    errors = validate_inputs(audit_summary, sanitized_rows, hidden_rows, smoke_rows, join_errors, args.audit_dir)
    status = STATUS_READY if not errors else STATUS_ERROR

    smoke_ready_path = args.output_dir / "smoke_ready_view.jsonl"
    write_jsonl(smoke_ready_path, smoke_rows)

    counts = count_summary(smoke_rows)
    write_json(args.output_dir / "smoke_plan.json", smoke_plan(smoke_ready_path, smoke_rows))
    write_csv(args.output_dir / "model_views.csv", model_view_rows())
    write_csv(args.output_dir / "gates.csv", gate_rows())
    write_csv(args.output_dir / "controls.csv", control_rows())
    write_csv(args.output_dir / "input_profile.csv", input_profile_rows(smoke_rows))
    write_csv(args.output_dir / "feature_paths.csv", feature_path_rows(smoke_rows))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)

    input_manifest = {
        "allowed_input_source": not errors,
        "counts": counts,
        "hidden_manifest_for_group_metadata": rel_path(hidden_path),
        "hidden_manifest_for_group_metadata_sha256": sha256_file(hidden_path),
        "schema_version": "h002_support_contact_individual_predicate_smoke_input_manifest_v1",
        "smoke_ready_view": rel_path(smoke_ready_path),
        "smoke_ready_view_sha256": sha256_file(smoke_ready_path),
        "source_audit_summary": rel_path(args.audit_dir / "summary.json"),
        "source_audit_summary_sha256": sha256_file(args.audit_dir / "summary.json"),
        "source_sanitized_view": rel_path(sanitized_path),
        "source_sanitized_view_sha256": sha256_file(sanitized_path),
    }
    write_json(args.output_dir / "input_manifest.json", input_manifest)

    summary = {
        "boundary": {
            "fills_labels": False,
            "h001_artifacts_modified": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "runs_learned_smoke": False,
            "split": "train_only_smoke_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "counts": counts,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "hidden_manifest_for_group_metadata": rel_path(hidden_path),
            "schema_audit_summary": rel_path(args.audit_dir / "summary.json"),
            "schema_audit_sanitized_view": rel_path(sanitized_path),
        },
        "learned_smoke_executed": False,
        "next_todo": NEXT_TODO,
        "output_paths": {
            "controls": rel_path(args.output_dir / "controls.csv"),
            "feature_paths": rel_path(args.output_dir / "feature_paths.csv"),
            "gates": rel_path(args.output_dir / "gates.csv"),
            "input_manifest": rel_path(args.output_dir / "input_manifest.json"),
            "input_profile": rel_path(args.output_dir / "input_profile.csv"),
            "model_views": rel_path(args.output_dir / "model_views.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "smoke_plan": rel_path(args.output_dir / "smoke_plan.json"),
            "smoke_ready_view": rel_path(smoke_ready_path),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": "plan_sanitized_support_contact_individual_predicate_ce_smoke",
        "status": status,
        "validation_errors": len(errors),
    }
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
