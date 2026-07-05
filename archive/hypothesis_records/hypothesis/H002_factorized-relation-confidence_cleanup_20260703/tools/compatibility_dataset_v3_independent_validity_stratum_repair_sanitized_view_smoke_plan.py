#!/usr/bin/env python3
"""Write the learned-smoke plan for exact-stratum repaired independent-validity rows."""

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
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan"
)

EXPECTED_AUDIT_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan"
)
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan"
EXPECTED_VIEW_SCHEMA = "h002_exact_stratum_repaired_independent_validity_sanitized_primary_view_v1"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan_ready"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_plan_input_errors"
)
NEXT_TODO = "compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner"

EXPECTED_ROWS = 1600
EXPECTED_POSITIVE = 800
EXPECTED_NEGATIVE = 800
EXPECTED_FEATURE_BLOCKS = {"T_e", "Z_e_safe", "G_e_raw", "Q_e_safe"}
SEMANTIC_SOURCE_SHORTCUT_AUROC_MAX = 0.60
RAW_GEOMETRY_DOMINANCE_MARGIN = 0.02
SHUFFLED_G_AUROC_MARGIN = 0.05
PRIMARY_AUROC_MIN = 0.65
PRIMARY_GAIN_OVER_SEMANTIC_SOURCE_MIN = 0.05
PRIMARY_GAIN_OVER_GEOMETRY_MIN = 0.00

FORBIDDEN_FEATURE_TOKENS = [
    "controls_hidden",
    "geometry_axis",
    "geometry_residual_proxy",
    "geometry_status",
    "label_match",
    "matched_gt",
    "p_geom_valid",
    "prediction_id",
    "scan_id",
    "selection_pass",
    "source_line_no",
    "stratum_id",
    "target_pool",
    "target_role",
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
                seen.add(key)
                fields.append(key)
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


def label_y(row: dict[str, Any]) -> int:
    return int(row["target_y"])


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


def count_summary(rows: list[dict[str, Any]], audit_summary: dict[str, Any]) -> dict[str, Any]:
    labels = Counter(label_y(row) for row in rows)
    groups: dict[str, list[int]] = defaultdict(list)
    predicates = Counter(str(nested_get(row, "feature_blocks.T_e.predicate_label")) for row in rows)
    families = Counter(str(row.get("family")) for row in rows)
    schemas = Counter(str(row.get("schema_version")) for row in rows)
    for row in rows:
        groups[str(row.get("cv_group_id"))].append(label_y(row))
    mixed_groups = sum(1 for values in groups.values() if 0 in values and 1 in values)
    return {
        "family_counts": dict(sorted(families.items())),
        "groups": len(groups),
        "mixed_label_groups": mixed_groups,
        "negative": labels[0],
        "positive": labels[1],
        "predicate_counts": dict(sorted(predicates.items())),
        "retained_exact_strata": audit_summary.get("counts", {}).get("retained_exact_strata"),
        "rows": len(rows),
        "schema_versions": dict(sorted(schemas.items())),
    }


def validate_inputs(audit_summary: dict[str, Any], contract: dict[str, Any], rows: list[dict[str, Any]], audit_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit_summary.get("next_todo")})
    if audit_summary.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors", "actual": audit_summary.get("validation_errors")})
    path_decision = audit_summary.get("path_decision", {})
    if path_decision.get("sanitized_view_smoke_plan_allowed") is not True:
        errors.append({"error_type": "smoke_plan_not_allowed", "actual": path_decision})
    risk = audit_summary.get("risk_summary", {})
    for key in [
        "critical_high_or_medium_risk",
        "source_confidence_high_or_medium_risk",
        "raw_geometry_high_or_medium_risk",
        "sanitized_blocked_feature_path_hits",
        "model_feature_blocked_key_hits",
    ]:
        if int(risk.get(key, -1)) != 0:
            errors.append({"error_type": "audit_risk_not_clear", "field": key, "actual": risk.get(key)})
    if contract.get("schema_version") != EXPECTED_VIEW_SCHEMA:
        errors.append({"error_type": "unexpected_contract_schema", "actual": contract.get("schema_version")})
    validation_path = audit_dir / "validation_errors.jsonl"
    if validation_path.exists() and validation_path.read_text(encoding="utf-8").strip():
        errors.append({"error_type": "nonempty_audit_validation_errors"})

    counts = count_summary(rows, audit_summary)
    if counts["rows"] != EXPECTED_ROWS or counts["positive"] != EXPECTED_POSITIVE or counts["negative"] != EXPECTED_NEGATIVE:
        errors.append({"error_type": "unexpected_row_or_label_counts", **counts})
    if counts["retained_exact_strata"] != 35:
        errors.append({"error_type": "unexpected_retained_exact_strata", "actual": counts["retained_exact_strata"]})
    if counts["family_counts"].get("support_contact_pose_conditioned", 0) != 88:
        errors.append({"error_type": "unexpected_support_contact_diagnostic_count", **counts})
    for row in rows:
        example_id = row.get("example_id")
        if row.get("schema_version") != EXPECTED_VIEW_SCHEMA:
            errors.append({"error_type": "unexpected_row_schema", "example_id": example_id, "actual": row.get("schema_version")})
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
        "feature_blocks.T_e.relation_family",
        "feature_blocks.T_e.subject_class_label",
        "feature_blocks.T_e.object_class_label",
        "feature_blocks.Z_e_safe.source_id",
        "feature_blocks.Z_e_safe.semantic_score_norm",
        "feature_blocks.Z_e_safe.semantic_score_raw",
        "feature_blocks.Z_e_safe.semantic_rank",
        "feature_blocks.Z_e_safe.rank_band",
        "feature_blocks.G_e_raw.raw_geometry_feature_vector.center_delta_z",
        "feature_blocks.G_e_raw.raw_geometry_feature_vector.distance_3d",
        "feature_blocks.G_e_raw.raw_geometry_feature_vector.distance_xy",
        "feature_blocks.G_e_raw.raw_geometry_feature_vector.normalized_center_delta_z",
        "feature_blocks.G_e_raw.raw_geometry_feature_vector.normalized_distance_3d",
        "feature_blocks.G_e_raw.raw_geometry_feature_vector.normalized_distance_xy",
        "feature_blocks.G_e_raw.raw_geometry_feature_vector.projected_iou_xy",
        "feature_blocks.G_e_raw.raw_geometry_feature_vector.projected_object_overlap_ratio",
        "feature_blocks.G_e_raw.raw_geometry_feature_vector.projected_subject_overlap_ratio",
        "feature_blocks.G_e_raw.raw_geometry_feature_vector.vertical_gap_subject_on_object",
        "feature_blocks.Q_e_safe.mesh_or_point_availability",
        "feature_blocks.Q_e_safe.object_pair_feature_coverage",
        "feature_blocks.Q_e_safe.raw_geometry_available",
        "feature_blocks.Q_e_safe.raw_geometry_feature_count",
    ]
    out: list[dict[str, Any]] = []
    for path in paths:
        values = [nested_get(row, path) for row in rows]
        missing = sum(1 for value in values if value is None or value == "")
        distinct = len({json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values})
        out.append(
            {
                "distinct_values": distinct,
                "feature_path": path,
                "missing": missing,
                "rows": len(rows),
                "usable_as_feature": True,
            }
        )
    return out


def feature_path_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = sorted({path for row in rows for path in feature_paths(row.get("feature_blocks", {}), "feature_blocks")})
    return [{"feature_path": path, "model_input_allowed": True} for path in paths]


def model_view_rows() -> list[dict[str, Any]]:
    return [
        {
            "model": "M0_intercept",
            "input_blocks": "none",
            "feature_engineering": "constant class-balance baseline",
            "primary": False,
            "role": "sanity baseline",
        },
        {
            "model": "M1_semantic_only_T",
            "input_blocks": "T_e",
            "feature_engineering": "predicate/class categorical features only",
            "primary": False,
            "role": "semantic shortcut baseline; should remain near chance after exact-stratum repair",
        },
        {
            "model": "M2_source_only_Z",
            "input_blocks": "Z_e_safe",
            "feature_engineering": "source score/rank/rank-band features only",
            "primary": False,
            "role": "source confidence shortcut baseline; should remain near chance",
        },
        {
            "model": "M3_semantic_source_TZ",
            "input_blocks": "T_e + Z_e_safe",
            "feature_engineering": "semantic categorical plus source confidence features",
            "primary": False,
            "role": "non-geometry shortcut baseline",
        },
        {
            "model": "M4_geometry_only_G",
            "input_blocks": "G_e_raw",
            "feature_engineering": "raw predicate-independent geometry vector only",
            "primary": False,
            "role": "geometry-only baseline; may be predictive and must be reported, not suppressed",
        },
        {
            "model": "M5_TG_concat",
            "input_blocks": "T_e + G_e_raw",
            "feature_engineering": "plain semantic plus raw geometry concatenation",
            "primary": False,
            "role": "tests whether simple fusion is enough",
        },
        {
            "model": "M6_TG_compatibility_interaction",
            "input_blocks": "T_e + G_e_raw",
            "feature_engineering": "predicate/family-conditioned geometry interactions over raw features",
            "primary": True,
            "role": "primary C_e smoke for predicate-geometry compatibility",
        },
        {
            "model": "M7_factorized_TZGQ",
            "input_blocks": "T_e + Z_e_safe + G_e_raw + Q_e_safe",
            "feature_engineering": "M6 interactions plus source confidence and evidence quality factors",
            "primary": False,
            "role": "full factorized relation reliability representation smoke",
        },
        {
            "model": "S1_predicate_x_class_pair_shortcut",
            "input_blocks": "T_e only",
            "feature_engineering": "predicate + subject/object class pair majority or one-hot model",
            "primary": False,
            "role": "must remain near chance; this was the previous blocker",
        },
        {
            "model": "S2_source_rank_score_shortcut",
            "input_blocks": "Z_e_safe only",
            "feature_engineering": "source score and rank only",
            "primary": False,
            "role": "source-confidence shortcut probe",
        },
        {
            "model": "C1_shuffled_G_global",
            "input_blocks": "T_e + globally shuffled G_e_raw",
            "feature_engineering": "deterministic row-level geometry permutation",
            "primary": False,
            "role": "negative control for aligned geometry use",
        },
        {
            "model": "C2_shuffled_G_within_predicate",
            "input_blocks": "T_e + G_e_raw shuffled within predicate_label",
            "feature_engineering": "preserve predicate distribution while breaking pair-specific geometry",
            "primary": False,
            "role": "harder geometry-alignment control",
        },
        {
            "model": "C3_wrong_predicate_family_control",
            "input_blocks": "wrong T_e + same G_e_raw",
            "feature_engineering": "swap higher/lower when possible and perturb support/contact predicate text for diagnostic rows",
            "primary": False,
            "role": "negative control for predicate conditioning",
        },
    ]


def gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "data_integrity",
            "criterion": "rows=1600, labels=800/800, exact strata=35, train-only",
            "blocks_runner_if_fail": True,
        },
        {
            "gate": "schema_safety",
            "criterion": "runner reads only smoke_ready_view.jsonl feature_blocks; no geometry_status/p_geom_valid/label_match/target_pool",
            "blocks_runner_if_fail": True,
        },
        {
            "gate": "semantic_source_shortcuts",
            "criterion": f"M1/M2/M3/S1/S2 AUROC <= {SEMANTIC_SOURCE_SHORTCUT_AUROC_MAX:.2f}",
            "blocks_promotion_if_fail": True,
        },
        {
            "gate": "primary_predictive_signal",
            "criterion": f"primary M6 or full M7 AUROC >= {PRIMARY_AUROC_MIN:.2f}",
            "blocks_promotion_if_fail": True,
        },
        {
            "gate": "gain_over_semantic_source",
            "criterion": f"primary M6/M7 beats max(M1,M2,M3) by >= {PRIMARY_GAIN_OVER_SEMANTIC_SOURCE_MIN:.2f} AUROC",
            "blocks_promotion_if_fail": True,
        },
        {
            "gate": "geometry_dominance_check",
            "criterion": f"if M4 geometry-only is within {RAW_GEOMETRY_DOMINANCE_MARGIN:.2f} AUROC of best factorized view, claim is geometry-evidence baseline not factorized compatibility",
            "blocks_paper_claim_if_fail": True,
        },
        {
            "gate": "shuffle_controls",
            "criterion": f"C1/C2 shuffled-G controls should not exceed max(M1,M2,M3)+{SHUFFLED_G_AUROC_MARGIN:.2f}",
            "blocks_promotion_if_fail": True,
        },
        {
            "gate": "family_scope",
            "criterion": "support/contact rows=88 remain diagnostic; primary learned conclusion is relative_vertical-dominant",
            "blocks_overgeneralization_if_fail": True,
        },
        {
            "gate": "paper_boundary",
            "criterion": "hypothesis-stage train-only smoke; Docker reproduction and held-out design required before paper-level evidence",
            "blocks_paper_evidence": True,
        },
    ]


def control_rows() -> list[dict[str, Any]]:
    return [
        {
            "control": "shuffled_G_global",
            "construction": "permute the entire G_e_raw block across all rows with a deterministic seed",
            "expected_result": "performance should drop toward non-geometry shortcut baselines",
        },
        {
            "control": "shuffled_G_within_predicate",
            "construction": "permute G_e_raw within predicate_label strata",
            "expected_result": "preserves predicate distribution but breaks pair-specific geometry",
        },
        {
            "control": "wrong_predicate_family",
            "construction": "swap higher/lower for relative_vertical rows when possible; perturb support/contact predicate text only as diagnostic",
            "expected_result": "predicate-conditioned compatibility score should degrade",
        },
        {
            "control": "no_interaction_concat",
            "construction": "compare M5 plain concatenation against M6 predicate-conditioned interactions",
            "expected_result": "if M6 does not beat M5, compatibility architecture adds little beyond concatenation",
        },
    ]


def smoke_plan(input_path: Path, contract_path: Path, rows: list[dict[str, Any]], audit_summary: dict[str, Any]) -> dict[str, Any]:
    counts = count_summary(rows, audit_summary)
    return {
        "schema_version": SCHEMA_VERSION,
        "task": {
            "name": "Task A repaired independent-validity C_e smoke",
            "target": "target_y in smoke_ready_view.jsonl",
            "target_semantics": "1 for exact GT+satisfied geometry, 0 for GT-pair other predicate/family mismatch+unsatisfied geometry",
            "not_in_scope": [
                "held-out validation/test performance",
                "paper-level result claim",
                "family-balanced support/contact conclusion",
                "p_obs abstention target",
            ],
        },
        "input_contract": {
            "allowed_blocks": ["T_e", "Z_e_safe", "G_e_raw", "Q_e_safe"],
            "feature_root": "feature_blocks",
            "group_key": "cv_group_id",
            "input_file": rel_path(input_path),
            "input_sha256": sha256_file(input_path),
            "metadata_only": ["example_id", "cv_group_id", "target_y", "target_name", "schema_version", "split", "text"],
            "model_view_contract": rel_path(contract_path),
            "negative": counts["negative"],
            "positive": counts["positive"],
            "row_count": counts["rows"],
            "target": "target_y",
        },
        "split_policy": {
            "folds": 5,
            "group_key": "cv_group_id",
            "group_rule": "all rows with the same cv_group_id stay in the same fold",
            "split": "train_internal_grouped_cv",
            "test_usage": False,
            "validation_usage": False,
        },
        "feature_engineering": {
            "G_e_raw": "raw metric geometry vector; no p_geom_valid or geometry_status",
            "Q_e_safe": "evidence quality/availability covariates only",
            "T_e": "predicate/class semantic content; exact-stratum shortcut already audited",
            "Z_e_policy": "source confidence baseline and final factor only; not part of C_e compatibility head",
            "predicate_conditioned_interactions": [
                "relative_vertical: expected vertical direction times center_delta_z / normalized_center_delta_z",
                "support/contact diagnostic: predicate-family-conditioned contact/gap/overlap interactions",
                "generic: relation family one-hot times raw geometry vector",
            ],
        },
        "metrics": [
            "AUROC",
            "AUPRC",
            "accuracy",
            "balanced_accuracy",
            "Brier",
            "ECE",
            "fold-level mean/std",
            "family-slice AUROC for relative_vertical and support_contact diagnostic slice",
        ],
        "models": model_view_rows(),
        "gates": gate_rows(),
        "controls": control_rows(),
        "paper_boundary": {
            "docker_required_before_paper_promotion": True,
            "hypothesis_stage_only": True,
            "paper_evidence_allowed": False,
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Independent Validity Stratum Repair Sanitized View Smoke Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"rows = {summary['counts']['rows']}",
        f"positive / negative = {summary['counts']['positive']} / {summary['counts']['negative']}",
        f"validation_errors = {summary['validation_errors']}",
        f"learned_smoke_executed = {str(summary['learned_smoke_executed']).lower()}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Main Decision",
        "",
        "Use the audited `sanitized_primary_view.jsonl` from the exact-stratum repair schema audit as",
        "the only model input source. Raw candidate rows and hidden manifests are audit-only.",
        "",
        "This smoke is not a paired same-G compatibility test. It is a repaired independent-validity",
        "target, so geometry-only may be predictive. The runner must report geometry-only as a serious",
        "baseline and check whether factorized compatibility adds anything beyond it.",
        "",
        "## Planned Baselines",
        "",
        "- `M1_semantic_only_T`",
        "- `M2_source_only_Z`",
        "- `M3_semantic_source_TZ`",
        "- `M4_geometry_only_G`",
        "- `M5_TG_concat`",
        "- `M6_TG_compatibility_interaction` as primary `C_e` smoke",
        "- `M7_factorized_TZGQ` as full factorized smoke",
        "",
        "## Planned Controls",
        "",
        "- shuffled-G global",
        "- shuffled-G within predicate",
        "- wrong-predicate-family control",
        "- no-interaction concat",
        "",
        "## Promotion Gates",
        "",
        f"- semantic/source shortcut baselines should remain <= {SEMANTIC_SOURCE_SHORTCUT_AUROC_MAX:.2f} AUROC",
        f"- primary M6 or M7 should reach >= {PRIMARY_AUROC_MIN:.2f} AUROC",
        f"- primary view should beat max semantic/source baseline by >= {PRIMARY_GAIN_OVER_SEMANTIC_SOURCE_MIN:.2f} AUROC",
        f"- if geometry-only M4 is within {RAW_GEOMETRY_DOMINANCE_MARGIN:.2f} AUROC of factorized view, claim becomes geometry-dominance diagnostic",
        "- support/contact remains diagnostic because only 88 rows are present",
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
    input_path = args.audit_dir / "sanitized_primary_view.jsonl"
    contract_path = args.audit_dir / "smoke_ready_model_view_contract.json"
    rows = read_jsonl(input_path)
    contract = read_json(contract_path)
    errors = validate_inputs(audit_summary, contract, rows, args.audit_dir)
    status = STATUS_READY if not errors else STATUS_ERROR
    counts = count_summary(rows, audit_summary)

    smoke_ready_path = args.output_dir / "smoke_ready_view.jsonl"
    write_jsonl(smoke_ready_path, rows)
    write_json(args.output_dir / "smoke_plan.json", smoke_plan(smoke_ready_path, contract_path, rows, audit_summary))
    write_csv(args.output_dir / "model_views.csv", model_view_rows())
    write_csv(args.output_dir / "gates.csv", gate_rows())
    write_csv(args.output_dir / "controls.csv", control_rows())
    write_csv(args.output_dir / "input_profile.csv", input_profile_rows(rows))
    write_csv(args.output_dir / "feature_paths.csv", feature_path_rows(rows))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)

    input_manifest = {
        "allowed_input_source": True,
        "counts": counts,
        "schema_version": "h002_exact_stratum_repaired_smoke_input_manifest_v1",
        "smoke_ready_model_view_contract": rel_path(contract_path),
        "smoke_ready_model_view_contract_sha256": sha256_file(contract_path),
        "smoke_ready_view": rel_path(smoke_ready_path),
        "smoke_ready_view_sha256": sha256_file(smoke_ready_path),
        "source_audit_summary": rel_path(args.audit_dir / "summary.json"),
        "source_sanitized_primary_view": rel_path(input_path),
        "source_sanitized_primary_view_sha256": sha256_file(input_path),
    }
    write_json(args.output_dir / "input_manifest.json", input_manifest)

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
        "near_chance_semantic_source_auroc_max": SEMANTIC_SOURCE_SHORTCUT_AUROC_MAX,
        "next_todo": NEXT_TODO if not errors else "fix_stratum_repair_sanitized_view_smoke_plan_inputs",
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
        "paper_evidence_allowed": False,
        "primary_gain_over_geometry_min": PRIMARY_GAIN_OVER_GEOMETRY_MIN,
        "primary_gain_over_semantic_source_min": PRIMARY_GAIN_OVER_SEMANTIC_SOURCE_MIN,
        "primary_model": "M6_TG_compatibility_interaction",
        "raw_geometry_dominance_margin": RAW_GEOMETRY_DOMINANCE_MARGIN,
        "schema_version": SCHEMA_VERSION,
        "smoke_runner_implementation_allowed": not errors,
        "status": status,
        "validation_errors": len(errors),
    }
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary)
    print(json.dumps({"status": status, "validation_errors": len(errors), "counts": counts}, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
