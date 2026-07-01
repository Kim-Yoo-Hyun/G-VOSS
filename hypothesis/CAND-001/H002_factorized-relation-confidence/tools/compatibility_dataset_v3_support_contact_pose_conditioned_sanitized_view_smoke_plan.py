#!/usr/bin/env python3
"""Write the support/contact pose-conditioned sanitized-view learned-smoke plan."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_AUDIT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan"
)

EXPECTED_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan"
)
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan"
EXPECTED_SMOKE_READY_SCHEMA = "h002_support_contact_pose_conditioned_smoke_ready_view_v1"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan_input_errors"
NEXT_TODO = "compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner"

PASS_AUROC_NEAR_CHANCE_MAX = 0.60
PRIMARY_AUROC_MIN = 0.90
PRIMARY_GAIN_MIN = 0.30
CONCAT_GAIN_MIN = 0.10

EXPECTED_FEATURE_BLOCKS = {"T_e", "Z_e_safe", "G_e_mesh_pose_contact", "Q_e_safe"}
FORBIDDEN_FEATURE_TOKENS = [
    "labels",
    "controls_hidden",
    "row_id",
    "anchor_id",
    "scan_id",
    "subject_id",
    "object_id",
    "visible_pair",
    "queue",
    "source_predicates",
    "pose_state",
    "G_e_hash",
    "geometry_feature_hash",
    "p_geom_valid",
    "label_source",
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
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


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
                fields.append(key)
                seen.add(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = row
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def safe_label(row: dict[str, Any]) -> int:
    return int(row["target_y"])


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(safe_label(row) for row in rows)
    groups: dict[str, list[int]] = defaultdict(list)
    predicates = Counter(str(nested_get(row, "feature_blocks.T_e.predicate_label")) for row in rows)
    schema_versions = Counter(str(row.get("schema_version")) for row in rows)
    point_complete = sum(1 for row in rows if nested_get(row, "feature_blocks.Q_e_safe.point_feature_complete"))
    semseg_complete = sum(1 for row in rows if nested_get(row, "feature_blocks.Q_e_safe.semseg_obb_available"))
    for row in rows:
        groups[str(row.get("cv_group_id"))].append(safe_label(row))
    paired = sum(1 for values in groups.values() if sorted(values) == [0, 1])
    return {
        "groups": len(groups),
        "negative": labels[0],
        "paired_groups_with_one_positive_one_negative": paired,
        "point_complete_rows": point_complete,
        "positive": labels[1],
        "predicate_counts": dict(sorted(predicates.items())),
        "rows": len(rows),
        "schema_versions": dict(sorted(schema_versions.items())),
        "semseg_complete_rows": semseg_complete,
    }


def validate_inputs(
    audit_summary: dict[str, Any],
    contract: dict[str, Any],
    rows: list[dict[str, Any]],
    audit_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit_summary.get("next_todo")})
    if audit_summary.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors", "actual": audit_summary.get("validation_errors")})
    risk = audit_summary.get("risk_summary", {})
    if risk.get("allowed_feature_high_or_medium_risk") != 0:
        errors.append({"error_type": "allowed_feature_shortcut_risk", "actual": risk})
    if risk.get("blocked_feature_path_hits") != 0 or risk.get("blocked_field_leakage_hits") != 0:
        errors.append({"error_type": "blocked_field_leakage", "actual": risk})
    if audit_summary.get("path_decision", {}).get("sanitized_view_smoke_plan_allowed") is not True:
        errors.append({"error_type": "smoke_plan_not_allowed", "actual": audit_summary.get("path_decision")})
    if contract.get("schema_version") != EXPECTED_SMOKE_READY_SCHEMA:
        errors.append({"error_type": "unexpected_contract_schema", "actual": contract.get("schema_version")})

    validation_path = audit_dir / "validation_errors.jsonl"
    if validation_path.exists() and validation_path.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_audit_validation_errors_file"})

    counts = count_summary(rows)
    if counts["rows"] != 400 or counts["positive"] != 200 or counts["negative"] != 200:
        errors.append({"error_type": "unexpected_row_or_label_counts", **counts})
    if counts["groups"] != 200 or counts["paired_groups_with_one_positive_one_negative"] != 200:
        errors.append({"error_type": "unexpected_group_counts", **counts})
    if counts["predicate_counts"] != {"lying on": 200, "standing on": 200}:
        errors.append({"error_type": "unexpected_predicate_counts", **counts})
    if counts["semseg_complete_rows"] != 400:
        errors.append({"error_type": "semseg_features_incomplete", **counts})

    for row in rows:
        example_id = row.get("example_id")
        if row.get("schema_version") != EXPECTED_SMOKE_READY_SCHEMA:
            errors.append({"error_type": "unexpected_row_schema", "example_id": example_id, "actual": row.get("schema_version")})
        feature_blocks = row.get("feature_blocks", {})
        if set(feature_blocks) != EXPECTED_FEATURE_BLOCKS:
            errors.append({"error_type": "unexpected_feature_blocks", "example_id": example_id, "blocks": sorted(feature_blocks)})
        feature_text = json.dumps(feature_blocks, ensure_ascii=False)
        for token in FORBIDDEN_FEATURE_TOKENS:
            if token in feature_text:
                errors.append({"error_type": "forbidden_token_in_features", "example_id": example_id, "token": token})
    return errors


def input_profile_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = [
        "feature_blocks.T_e.predicate_label",
        "feature_blocks.T_e.subject_class_label",
        "feature_blocks.T_e.object_class_label",
        "feature_blocks.Z_e_safe.source_score_available",
        "feature_blocks.Z_e_safe.source_rank_available",
        "feature_blocks.G_e_mesh_pose_contact.abs_surface_gap_subject_bottom_to_object_top",
        "feature_blocks.G_e_mesh_pose_contact.xy_overlap_min_ratio",
        "feature_blocks.G_e_mesh_pose_contact.subject_vertical_extent_ratio",
        "feature_blocks.G_e_mesh_pose_contact.subject_flatness_ratio",
        "feature_blocks.G_e_mesh_pose_contact.subject_major_axis_upness",
        "feature_blocks.G_e_mesh_pose_contact.obb_contact_likelihood_proxy",
        "feature_blocks.G_e_mesh_pose_contact.point_abs_surface_gap_optional",
        "feature_blocks.G_e_mesh_pose_contact.point_contact_candidate_ratio_optional",
        "feature_blocks.G_e_mesh_pose_contact.point_subject_bottom_band_density_optional",
        "feature_blocks.G_e_mesh_pose_contact.point_object_top_band_density_optional",
        "feature_blocks.Q_e_safe.semseg_obb_available",
        "feature_blocks.Q_e_safe.aligned_ply_point_features_available",
        "feature_blocks.Q_e_safe.point_feature_complete",
        "feature_blocks.Q_e_safe.hard_surface_pair_allowed",
    ]
    output: list[dict[str, Any]] = []
    for path in paths:
        values = [nested_get(row, path) for row in rows]
        missing = sum(1 for value in values if value is None or value == "")
        distinct = len({json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values})
        output.append(
            {
                "distinct_values": distinct,
                "feature_path": path,
                "missing": missing,
                "rows": len(rows),
                "usable_as_feature": True,
            }
        )
    return output


def model_view_rows() -> list[dict[str, Any]]:
    return [
        {
            "model": "M0_intercept",
            "input_blocks": "none",
            "feature_engineering": "constant",
            "primary": False,
            "role": "class-balance sanity baseline",
        },
        {
            "model": "M1_source_only_Z_safe",
            "input_blocks": "Z_e_safe",
            "feature_engineering": "source score/rank availability flags only",
            "primary": False,
            "role": "source-confidence availability shortcut baseline",
        },
        {
            "model": "M2_semantic_only_T",
            "input_blocks": "T_e",
            "feature_engineering": "predicate/object categorical features",
            "primary": False,
            "role": "semantic prior shortcut baseline",
        },
        {
            "model": "M3_semantic_source_TZ_safe",
            "input_blocks": "T_e + Z_e_safe",
            "feature_engineering": "semantic categorical plus source availability flags",
            "primary": False,
            "role": "semantic/source shortcut baseline without geometry",
        },
        {
            "model": "M4_geometry_only_G",
            "input_blocks": "G_e_mesh_pose_contact",
            "feature_engineering": "predicate-independent support/contact pose and contact geometry only",
            "primary": False,
            "role": "geometry-only control; should be near chance because both rows in a pair share the same G_e",
        },
        {
            "model": "M5a_compatibility_TG_concat",
            "input_blocks": "T_e + G_e_mesh_pose_contact",
            "feature_engineering": "plain concatenation without predicate-conditioned pose interaction",
            "primary": False,
            "role": "tests whether generic feature aggregation is enough",
        },
        {
            "model": "M5b_compatibility_TG_pose_interaction",
            "input_blocks": "T_e + G_e_mesh_pose_contact",
            "feature_engineering": "predicate-conditioned lying/upright pose interactions over support/contact geometry",
            "primary": True,
            "role": "primary C_e smoke for support/contact predicate-geometry compatibility",
        },
        {
            "model": "M6_factorized_sanitized_TZGQ_pose_interaction",
            "input_blocks": "T_e + Z_e_safe + G_e_mesh_pose_contact + Q_e_safe",
            "feature_engineering": "M5b interaction plus source and evidence-quality factors",
            "primary": False,
            "role": "full factorized representation smoke; not the main C_e proof",
        },
        {
            "model": "S1_predicate_label_shortcut",
            "input_blocks": "T_e.predicate_label",
            "feature_engineering": "predicate label only",
            "primary": False,
            "role": "shortcut probe",
        },
        {
            "model": "S2_object_pair_shortcut",
            "input_blocks": "T_e.subject_class_label + T_e.object_class_label",
            "feature_engineering": "object class pair only",
            "primary": False,
            "role": "object-pair semantic shortcut probe",
        },
        {
            "model": "S3_quality_shortcut",
            "input_blocks": "Q_e_safe",
            "feature_engineering": "evidence quality flags only",
            "primary": False,
            "role": "observability shortcut probe",
        },
        {
            "model": "C1_wrong_T_same_G_control",
            "input_blocks": "wrong T_e + same G_e_mesh_pose_contact",
            "feature_engineering": "swap lying on <-> standing on while preserving G_e",
            "primary": False,
            "role": "negative control for predicate conditioning",
        },
        {
            "model": "C2_shuffled_G_global_control",
            "input_blocks": "T_e + globally shuffled G_e_mesh_pose_contact",
            "feature_engineering": "deterministic geometry shuffle preserving label distribution",
            "primary": False,
            "role": "negative control for aligned geometry use",
        },
        {
            "model": "C3_shuffled_G_within_predicate_control",
            "input_blocks": "T_e + G_e_mesh_pose_contact shuffled within predicate label",
            "feature_engineering": "harder shuffle preserving predicate distribution",
            "primary": False,
            "role": "negative control for pair-specific geometry alignment",
        },
    ]


def gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "blocks_runner_if_fail": True,
            "criterion": "rows=400, labels=200/200, groups=200, each cv_group_id has one positive and one negative",
            "gate": "data_integrity",
        },
        {
            "blocks_runner_if_fail": True,
            "criterion": "runner reads only audited smoke_ready_view.jsonl feature_blocks; example_id/cv_group_id/target_y are metadata only",
            "gate": "input_safety",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": f"M1/M2/M3/M4/S1/S2/S3 AUROC <= {PASS_AUROC_NEAR_CHANCE_MAX:.2f}",
            "gate": "shortcut_baselines_near_chance",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": f"M5b AUROC >= {PRIMARY_AUROC_MIN:.2f} and at least +{PRIMARY_GAIN_MIN:.2f} over max(M1,M2,M3,M4)",
            "gate": "primary_compatibility_success",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": f"M5b should beat no-interaction M5a by at least {CONCAT_GAIN_MIN:.2f} AUROC or show stronger paired margin/control behavior",
            "gate": "interaction_over_concat",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": "C1 wrong-T same-G must strongly degrade or invert paired scores relative to M5b",
            "gate": "wrong_T_same_G_degradation",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": f"C2/C3 shuffled-G controls should fall near chance, preferably AUROC <= {PASS_AUROC_NEAR_CHANCE_MAX:.2f}",
            "gate": "shuffled_G_degradation",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": "within each cv_group_id, score(compatible row) - score(incompatible row) should be positive for M5b",
            "gate": "paired_score_margin",
        },
        {
            "blocks_promotion_if_fail": True,
            "criterion": "hypothesis-stage train-only smoke; Docker reproduction required before paper-level evidence",
            "gate": "paper_boundary",
        },
    ]


def control_rows() -> list[dict[str, Any]]:
    return [
        {
            "construction": "swap lying on <-> standing on in T_e while keeping G_e and original target",
            "control": "wrong_T_same_G",
            "expected_result": "primary compatibility score should degrade or invert",
        },
        {
            "construction": "permute G_e blocks across all rows with a deterministic seed",
            "control": "shuffled_G_global",
            "expected_result": "T_e + shuffled G_e should approach shortcut baseline",
        },
        {
            "construction": "permute G_e blocks within each predicate label",
            "control": "shuffled_G_within_predicate",
            "expected_result": "preserves predicate distribution but breaks object-pair pose/contact alignment",
        },
        {
            "construction": "use T_e + G_e without predicate-conditioned lying/upright pose interaction features",
            "control": "no_interaction_concat",
            "expected_result": "if this fails but M5b passes, the target specifically requires predicate-geometry interaction",
        },
    ]


def smoke_plan(input_path: Path, contract_path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = count_summary(rows)
    return {
        "controls": control_rows(),
        "feature_engineering": {
            "G_e_mesh_pose_contact": "predicate-independent support/contact pose, contact, overlap, gap, and optional point-contact features",
            "Q_e_policy": "observability/coverage covariate only; not a truth label",
            "T_e": "predicate/object categorical fields; predicate selects lying-like or upright geometry interpretation only inside interaction views",
            "Z_e_policy": "excluded from C_e primary view; included only in source and full factorized baselines",
            "predicate_conditioned_interactions": [
                "is_lying(predicate) * lying_pose_features",
                "is_standing(predicate) * upright_pose_features",
                "is_lying(predicate) * low_major_axis_upness_or_flatness_features",
                "is_standing(predicate) * high_major_axis_upness_and_vertical_extent_features",
                "predicate-conditioned contact/overlap/gap features shared across both predicates",
            ],
        },
        "gates": gate_rows(),
        "input_contract": {
            "allowed_blocks": ["T_e", "Z_e_safe", "G_e_mesh_pose_contact", "Q_e_safe"],
            "feature_root": "feature_blocks",
            "forbidden_as_features": FORBIDDEN_FEATURE_TOKENS,
            "group_key": "cv_group_id",
            "input_file": rel_path(input_path),
            "input_sha256": sha256_file(input_path),
            "metadata_only": ["example_id", "cv_group_id", "target_y", "schema_version"],
            "model_view_contract": rel_path(contract_path),
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
            "paired compatible-minus-incompatible score margin",
            "fold-level mean/std",
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
            "group_rule": "both rows from the same geometry anchor must stay in the same fold",
            "split": "train_internal_grouped_cv",
            "test_usage": False,
            "validation_usage": False,
        },
        "task": {
            "name": "Task A support/contact predicate-geometry compatibility C_e",
            "not_in_scope": [
                "p_rel final human reliability",
                "p_obs abstention",
                "validation/test performance",
                "paper-level result claim",
            ],
            "target": "target_y in smoke_ready_view.jsonl",
            "target_semantics": "1 if lying/standing predicate is compatible with the same support/contact pose geometry, otherwise 0",
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Support/Contact Pose-Conditioned Sanitized View Smoke Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"compatibility positive / negative = {summary['counts']['positive']} / {summary['counts']['negative']}",
        f"paired groups = {summary['counts']['paired_groups_with_one_positive_one_negative']}",
        f"validation_errors = {summary['validation_errors']}",
        f"learned_smoke_executed = {str(summary['learned_smoke_executed']).lower()}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Main Decision",
        "",
        "The next learned smoke must use only the audited support/contact `smoke_ready_view.jsonl`.",
        "Raw candidate rows, hidden manifests, row ids, anchor ids, scan ids, visible pairs, queue",
        "kinds, source predicates, hidden pose state, and geometry hashes are not model features.",
        "",
        "The primary smoke is `M5b_compatibility_TG_pose_interaction`, which tests whether the",
        "predicate changes the interpretation of the same support/contact geometry evidence.",
        "",
        "## Planned Baselines",
        "",
        "- `M1_source_only_Z_safe`",
        "- `M2_semantic_only_T`",
        "- `M3_semantic_source_TZ_safe`",
        "- `M4_geometry_only_G`",
        "- `M5a_compatibility_TG_concat`",
        "- `M5b_compatibility_TG_pose_interaction` as the primary `C_e` smoke",
        "- `M6_factorized_sanitized_TZGQ_pose_interaction`",
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
        f"- shortcut/source/semantic/geometry-only baselines should remain <= {PASS_AUROC_NEAR_CHANCE_MAX:.2f} AUROC",
        f"- primary `M5b` should reach >= {PRIMARY_AUROC_MIN:.2f} AUROC",
        f"- primary `M5b` should beat the best non-compatibility baseline by >= {PRIMARY_GAIN_MIN:.2f} AUROC",
        f"- primary `M5b` should beat no-interaction concat by >= {CONCAT_GAIN_MIN:.2f} AUROC or show stronger paired/control behavior",
        "- wrong-T and shuffled-G controls must degrade",
        "- paired compatible-minus-incompatible score margin should be positive",
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
    input_path = args.audit_dir / "smoke_ready_view.jsonl"
    contract_path = args.audit_dir / "smoke_ready_model_view_contract.json"
    rows = read_jsonl(input_path)
    contract = read_json(contract_path)
    errors = validate_inputs(audit_summary, contract, rows, args.audit_dir)
    status = STATUS_READY if not errors else STATUS_ERROR
    counts = count_summary(rows)
    plan = smoke_plan(input_path, contract_path, rows)

    output_paths = {
        "controls": args.output_dir / "controls.csv",
        "gates": args.output_dir / "gates.csv",
        "input_manifest": args.output_dir / "input_manifest.json",
        "input_profile": args.output_dir / "input_profile.csv",
        "model_views": args.output_dir / "model_views.csv",
        "report": args.output_dir / "report.md",
        "smoke_plan": args.output_dir / "smoke_plan.json",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }

    write_json(output_paths["smoke_plan"], plan)
    write_csv(output_paths["model_views"], model_view_rows())
    write_csv(output_paths["gates"], gate_rows())
    write_csv(output_paths["controls"], control_rows())
    write_csv(output_paths["input_profile"], input_profile_rows(rows))
    write_jsonl(output_paths["validation_errors"], errors)

    input_manifest = {
        "allowed_input_source": not errors,
        "counts": counts,
        "schema_version": "h002_support_contact_pose_conditioned_sanitized_view_smoke_input_manifest_v1",
        "smoke_ready_model_view_contract": rel_path(contract_path),
        "smoke_ready_model_view_contract_sha256": sha256_file(contract_path),
        "smoke_ready_view": rel_path(input_path),
        "smoke_ready_view_sha256": sha256_file(input_path),
        "source_audit_summary": rel_path(args.audit_dir / "summary.json"),
    }
    write_json(output_paths["input_manifest"], input_manifest)

    summary = {
        "audit_root": rel_path(args.audit_dir),
        "boundary": {
            "h001_artifacts_modified": False,
            "raw_candidate_rows_promoted_as_model_input": False,
            "runs_learned_smoke": False,
            "split": "train_only_smoke_plan",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "counts": counts,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "learned_smoke_executed": False,
        "near_chance_baseline_auroc_max": PASS_AUROC_NEAR_CHANCE_MAX,
        "next_todo": NEXT_TODO if not errors else "compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_plan_repair",
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "output_root": rel_path(args.output_dir),
        "paper_evidence_allowed": False,
        "primary_gain_min": PRIMARY_GAIN_MIN,
        "primary_gate_auroc_min": PRIMARY_AUROC_MIN,
        "primary_model": "M5b_compatibility_TG_pose_interaction",
        "schema_version": SCHEMA_VERSION,
        "smoke_runner_implementation_allowed": not errors,
        "status": status,
        "validation_errors": len(errors),
    }
    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
