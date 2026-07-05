#!/usr/bin/env python3
"""Write the H002 v3 sanitized-view learned-smoke plan."""

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

DEFAULT_AUDIT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_schema_shortcut_audit"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan"

EXPECTED_AUDIT_STATUS = "h002_compatibility_dataset_v3_schema_shortcut_audit_ready_for_sanitized_view_smoke_plan"
EXPECTED_AUDIT_NEXT = "compatibility_dataset_v3_sanitized_view_smoke_plan"
EXPECTED_SMOKE_READY_SCHEMA = "h002_compatibility_dataset_v3_smoke_ready_view_v1"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_sanitized_view_smoke_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_sanitized_view_smoke_plan_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_sanitized_view_smoke_plan_input_errors"
NEXT_TODO = "compatibility_dataset_v3_sanitized_view_smoke_runner"

PASS_AUROC_NEAR_CHANCE_MAX = 0.60
PRIMARY_AUROC_MIN = 0.90
PRIMARY_GAIN_MIN = 0.30


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
    rows = []
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
        fields = ["empty"]
        rows = [{"empty": ""}]
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


def safe_label(row: dict[str, Any]) -> int:
    return int(row["target_y"])


def nested_get(row: dict[str, Any], dotted: str, default: Any = None) -> Any:
    cur: Any = row
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def count_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = Counter(safe_label(row) for row in rows)
    by_group: dict[str, list[int]] = defaultdict(list)
    schema_versions = Counter(str(row.get("schema_version")) for row in rows)
    predicates = Counter(str(nested_get(row, "feature_blocks.T_e.predicate_label")) for row in rows)
    for row in rows:
        by_group[str(row.get("cv_group_id"))].append(safe_label(row))
    complete_groups = sum(1 for values in by_group.values() if sorted(values) == [0, 1])
    return {
        "rows": len(rows),
        "positive": labels[1],
        "negative": labels[0],
        "groups": len(by_group),
        "paired_groups_with_one_positive_one_negative": complete_groups,
        "schema_versions": dict(sorted(schema_versions.items())),
        "predicate_counts": dict(sorted(predicates.items())),
    }


def validate_inputs(audit_summary: dict[str, Any], contract: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if audit_summary.get("status") != EXPECTED_AUDIT_STATUS:
        errors.append({"error_type": "unexpected_audit_status", "actual": audit_summary.get("status")})
    if audit_summary.get("next_todo") != EXPECTED_AUDIT_NEXT:
        errors.append({"error_type": "unexpected_audit_next_todo", "actual": audit_summary.get("next_todo")})
    if audit_summary.get("validation_errors") != 0:
        errors.append({"error_type": "audit_validation_errors", "actual": audit_summary.get("validation_errors")})
    if audit_summary.get("smoke_ready_view_allowed_as_model_input_source") is not True:
        errors.append({"error_type": "smoke_ready_view_not_allowed", "actual": audit_summary.get("smoke_ready_view_allowed_as_model_input_source")})
    if contract.get("schema_version") != "h002_v3_smoke_ready_model_view_contract_v1":
        errors.append({"error_type": "unexpected_smoke_contract_schema", "actual": contract.get("schema_version")})
    counts = count_summary(rows)
    if counts["rows"] != 400 or counts["positive"] != 200 or counts["negative"] != 200:
        errors.append({"error_type": "unexpected_row_or_label_counts", **counts})
    if counts["groups"] != 200 or counts["paired_groups_with_one_positive_one_negative"] != 200:
        errors.append({"error_type": "unexpected_group_counts", **counts})
    for row in rows:
        row_id = row.get("example_id")
        if row.get("schema_version") != EXPECTED_SMOKE_READY_SCHEMA:
            errors.append({"error_type": "unexpected_row_schema", "example_id": row_id, "actual": row.get("schema_version")})
        feature_blocks = row.get("feature_blocks", {})
        if set(feature_blocks) != {"T_e", "Z_e_safe", "G_e_numeric", "Q_e_safe"}:
            errors.append({"error_type": "unexpected_feature_blocks", "example_id": row_id, "blocks": sorted(feature_blocks)})
        if "geometry_feature_hash" in feature_blocks.get("G_e_numeric", {}):
            errors.append({"error_type": "geometry_feature_hash_in_model_features", "example_id": row_id})
        for blocked in ["labels", "controls_hidden", "raw_source_predicate", "positive_predicate", "direction_bucket", "visible_pair", "endpoint_state"]:
            if blocked in json.dumps(feature_blocks, ensure_ascii=False):
                errors.append({"error_type": "blocked_token_in_feature_blocks", "example_id": row_id, "token": blocked})
    return errors


def input_profile_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = [
        "feature_blocks.T_e.predicate_label",
        "feature_blocks.T_e.subject_class_label",
        "feature_blocks.T_e.object_class_label",
        "feature_blocks.T_e.subject_object_text",
        "feature_blocks.Z_e_safe.source_score_normalized",
        "feature_blocks.Z_e_safe.source_rank",
        "feature_blocks.Z_e_safe.source_rank_band",
        "feature_blocks.G_e_numeric.center_delta_z_m",
        "feature_blocks.G_e_numeric.normalized_center_delta_z",
        "feature_blocks.G_e_numeric.distance_xy_m",
        "feature_blocks.G_e_numeric.vertical_gap_subject_on_object",
        "feature_blocks.Q_e_safe.geometry_available",
        "feature_blocks.Q_e_safe.obb_available",
        "feature_blocks.Q_e_safe.mesh_available",
        "feature_blocks.Q_e_safe.view_packet_available",
    ]
    out = []
    for path in paths:
        values = [nested_get(row, path) for row in rows]
        missing = sum(1 for value in values if value is None or value == "")
        distinct = len({json.dumps(value, ensure_ascii=False, sort_keys=True) for value in values})
        out.append(
            {
                "feature_path": path,
                "rows": len(rows),
                "missing": missing,
                "distinct_values": distinct,
                "usable_as_feature": True,
            }
        )
    return out


def model_view_rows() -> list[dict[str, Any]]:
    return [
        {
            "model": "M0_intercept",
            "input_blocks": "none",
            "feature_engineering": "constant",
            "role": "class-balance sanity baseline",
            "primary": False,
        },
        {
            "model": "M1_source_only_Z_safe",
            "input_blocks": "Z_e_safe",
            "feature_engineering": "numeric source score/rank + rank band one-hot",
            "role": "source confidence shortcut baseline",
            "primary": False,
        },
        {
            "model": "M2_semantic_only_T",
            "input_blocks": "T_e",
            "feature_engineering": "predicate/object text categorical features",
            "role": "semantic prior shortcut baseline",
            "primary": False,
        },
        {
            "model": "M3_semantic_source_TZ_safe",
            "input_blocks": "T_e + Z_e_safe",
            "feature_engineering": "semantic categorical + source confidence",
            "role": "semantic/source shortcut baseline without geometry",
            "primary": False,
        },
        {
            "model": "M4_geometry_only_G",
            "input_blocks": "G_e_numeric",
            "feature_engineering": "predicate-independent numeric geometry only",
            "role": "geometry-only control; should be near chance in same-G rows",
            "primary": False,
        },
        {
            "model": "M5a_compatibility_TG_concat",
            "input_blocks": "T_e + G_e_numeric",
            "feature_engineering": "plain concatenation without predicate-conditioned interaction",
            "role": "tests whether concat alone is enough",
            "primary": False,
        },
        {
            "model": "M5b_compatibility_TG_interaction",
            "input_blocks": "T_e + G_e_numeric",
            "feature_engineering": "predicate expected-z-sign times vertical geometry features",
            "role": "primary C_e smoke for predicate-conditioned geometry compatibility",
            "primary": True,
        },
        {
            "model": "M6_factorized_sanitized_TZGQ_interaction",
            "input_blocks": "T_e + Z_e_safe + G_e_numeric + Q_e_safe",
            "feature_engineering": "M5b interaction plus source and evidence-quality factors",
            "role": "full factorized representation smoke; not the main C_e proof",
            "primary": False,
        },
        {
            "model": "S1_predicate_label_shortcut",
            "input_blocks": "T_e.predicate_label",
            "feature_engineering": "predicate label only",
            "role": "shortcut probe",
            "primary": False,
        },
        {
            "model": "S2_object_pair_shortcut",
            "input_blocks": "T_e.subject_object_text",
            "feature_engineering": "subject/object text only",
            "role": "visible-pair semantic shortcut probe",
            "primary": False,
        },
        {
            "model": "S3_source_score_rank_shortcut",
            "input_blocks": "Z_e_safe.source_score_normalized + source_rank + source_rank_band",
            "feature_engineering": "source confidence only",
            "role": "source shortcut probe",
            "primary": False,
        },
        {
            "model": "C1_wrong_T_same_G_control",
            "input_blocks": "wrong T_e + same G_e_numeric",
            "feature_engineering": "swap higher/lower predicate while preserving G_e",
            "role": "negative control for predicate conditioning",
            "primary": False,
        },
        {
            "model": "C2_shuffled_G_global_control",
            "input_blocks": "T_e + globally shuffled G_e_numeric",
            "feature_engineering": "deterministic row-level geometry shuffle preserving label distribution",
            "role": "negative control for aligned geometry use",
            "primary": False,
        },
        {
            "model": "C3_shuffled_G_within_predicate_control",
            "input_blocks": "T_e + G_e_numeric shuffled within predicate label",
            "feature_engineering": "harder shuffle preserving predicate distribution",
            "role": "negative control for pair-specific geometry alignment",
            "primary": False,
        },
    ]


def gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "data_integrity",
            "criterion": "rows=400, labels=200/200, groups=200, each cv_group_id has one positive and one negative",
            "blocks_runner_if_fail": True,
        },
        {
            "gate": "input_safety",
            "criterion": "runner reads only smoke_ready_view.jsonl feature_blocks; example_id/cv_group_id/target_y are metadata only",
            "blocks_runner_if_fail": True,
        },
        {
            "gate": "shortcut_baselines_near_chance",
            "criterion": f"M1/M2/M3/M4/S1/S2/S3 AUROC <= {PASS_AUROC_NEAR_CHANCE_MAX:.2f}",
            "blocks_promotion_if_fail": True,
        },
        {
            "gate": "primary_compatibility_success",
            "criterion": f"M5b AUROC >= {PRIMARY_AUROC_MIN:.2f} and at least +{PRIMARY_GAIN_MIN:.2f} over max(M1,M2,M3,M4)",
            "blocks_promotion_if_fail": True,
        },
        {
            "gate": "wrong_T_same_G_degradation",
            "criterion": "C1 wrong-T same-G must strongly degrade or invert paired scores relative to M5b",
            "blocks_promotion_if_fail": True,
        },
        {
            "gate": "shuffled_G_degradation",
            "criterion": f"C2/C3 shuffled-G controls should fall near chance, preferably AUROC <= {PASS_AUROC_NEAR_CHANCE_MAX:.2f}",
            "blocks_promotion_if_fail": True,
        },
        {
            "gate": "paired_score_drop",
            "criterion": "within each cv_group_id, score(compatible row) - score(incompatible row) should be positive for M5b",
            "blocks_promotion_if_fail": True,
        },
        {
            "gate": "paper_boundary",
            "criterion": "hypothesis-stage train-only smoke; Docker reproduction required before paper-level evidence",
            "blocks_promotion_if_fail": True,
        },
    ]


def control_rows() -> list[dict[str, Any]]:
    return [
        {
            "control": "wrong_T_same_G",
            "construction": "swap higher than <-> lower than in T_e while keeping G_e and original target",
            "expected_result": "primary compatibility score should degrade or invert",
        },
        {
            "control": "shuffled_G_global",
            "construction": "permute G_e blocks across all rows with a deterministic seed",
            "expected_result": "T_e + shuffled G_e should approach shortcut baseline",
        },
        {
            "control": "shuffled_G_within_predicate",
            "construction": "permute G_e blocks within each predicate label",
            "expected_result": "preserves predicate distribution but breaks object-pair geometry alignment",
        },
        {
            "control": "no_interaction_concat",
            "construction": "use T_e + G_e without predicate-conditioned interaction features",
            "expected_result": "if this fails but M5b passes, the target specifically requires semantic-geometry interaction",
        },
    ]


def smoke_plan(input_path: Path, contract_path: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = count_summary(rows)
    return {
        "schema_version": SCHEMA_VERSION,
        "task": {
            "name": "Task A predicate-geometry compatibility C_e",
            "target": "target_y in smoke_ready_view.jsonl",
            "target_semantics": "1 if predicate is compatible with signed vertical geometry, otherwise 0",
            "not_in_scope": [
                "p_rel final human reliability",
                "p_obs abstention",
                "validation/test performance",
                "paper-level result claim",
            ],
        },
        "input_contract": {
            "input_file": rel_path(input_path),
            "input_sha256": sha256_file(input_path),
            "model_view_contract": rel_path(contract_path),
            "row_count": counts["rows"],
            "positive": counts["positive"],
            "negative": counts["negative"],
            "group_key": "cv_group_id",
            "target": "target_y",
            "feature_root": "feature_blocks",
            "allowed_blocks": ["T_e", "Z_e_safe", "G_e_numeric", "Q_e_safe"],
            "metadata_only": ["example_id", "cv_group_id", "target_y", "target_name", "schema_version"],
            "forbidden_as_features": [
                "geometry_feature_hash",
                "labels",
                "controls_hidden",
                "row_id",
                "geometry_group_id",
                "raw_source_predicate",
                "source_prediction_id",
                "positive_predicate",
                "direction_bucket",
                "visible_pair",
                "endpoint_state",
            ],
        },
        "split_policy": {
            "split": "train_internal_grouped_cv",
            "folds": 5,
            "group_key": "cv_group_id",
            "group_rule": "both rows from the same geometry group must stay in the same fold",
            "validation_usage": False,
            "test_usage": False,
        },
        "feature_engineering": {
            "T_e": "categorical/text fields; predicate label can be mapped to expected_z_sign only inside interaction views",
            "G_e_numeric": "numeric geometry fields only, no geometry_feature_hash",
            "predicate_conditioned_interactions": [
                "expected_z_sign(predicate) * center_delta_z_m",
                "expected_z_sign(predicate) * normalized_center_delta_z",
                "expected_z_sign(predicate) * subject_center_z - object_center_z equivalent features if used",
            ],
            "Z_e_policy": "excluded from C_e primary view; included only in source and full factorized baselines",
            "Q_e_policy": "coverage/availability covariate only; not a truth label",
        },
        "metrics": [
            "AUROC",
            "AUPRC",
            "accuracy",
            "balanced_accuracy",
            "Brier",
            "ECE",
            "paired compatible-minus-incompatible score drop",
            "fold-level mean/std",
        ],
        "models": model_view_rows(),
        "gates": gate_rows(),
        "controls": control_rows(),
        "paper_boundary": {
            "paper_evidence_allowed": False,
            "hypothesis_stage_only": True,
            "docker_required_before_paper_promotion": True,
        },
    }


def validation_errors(audit_summary: dict[str, Any], rows: list[dict[str, Any]], contract: dict[str, Any]) -> list[dict[str, Any]]:
    return validate_inputs(audit_summary, contract, rows)


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Compatibility Dataset V3 Sanitized View Smoke Plan",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v3_sanitized_view_smoke_plan/",
        "```",
        "",
        "Status:",
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
        "The next learned smoke must use the audited `smoke_ready_view.jsonl` from the v3 schema",
        "shortcut audit. Raw `candidate_rows.jsonl` and the intermediate materialization",
        "`sanitized_model_view.jsonl` are not model-input sources.",
        "",
        "The primary smoke is not plain score concatenation. It must include a predicate-conditioned",
        "interaction view:",
        "",
        "```text",
        "expected_z_sign(predicate) * vertical geometry",
        "```",
        "",
        "This directly tests whether `T_e` changes the interpretation of the same `G_e`.",
        "",
        "## Planned Baselines",
        "",
        "- `M1_source_only_Z_safe`",
        "- `M2_semantic_only_T`",
        "- `M3_semantic_source_TZ_safe`",
        "- `M4_geometry_only_G`",
        "- `M5a_compatibility_TG_concat`",
        "- `M5b_compatibility_TG_interaction` as the primary `C_e` smoke",
        "- `M6_factorized_sanitized_TZGQ_interaction`",
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
        "- wrong-T and shuffled-G controls must degrade",
        "- paired compatible-minus-incompatible score difference should be positive",
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


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    audit_summary = read_json(args.audit_dir / "summary.json")
    input_path = args.audit_dir / "smoke_ready_view.jsonl"
    contract_path = args.audit_dir / "smoke_ready_model_view_contract.json"
    rows = read_jsonl(input_path)
    contract = read_json(contract_path)
    errors = validation_errors(audit_summary, rows, contract)
    status = STATUS_READY if not errors else STATUS_ERROR
    plan = smoke_plan(input_path, contract_path, rows)
    counts = count_summary(rows)

    write_json(args.output_dir / "smoke_plan.json", plan)
    write_csv(args.output_dir / "model_views.csv", model_view_rows())
    write_csv(args.output_dir / "gates.csv", gate_rows())
    write_csv(args.output_dir / "controls.csv", control_rows())
    write_csv(args.output_dir / "input_profile.csv", input_profile_rows(rows))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)

    input_manifest = {
        "schema_version": "h002_v3_sanitized_view_smoke_input_manifest_v1",
        "smoke_ready_view": rel_path(input_path),
        "smoke_ready_view_sha256": sha256_file(input_path),
        "smoke_ready_model_view_contract": rel_path(contract_path),
        "smoke_ready_model_view_contract_sha256": sha256_file(contract_path),
        "source_audit_summary": rel_path(args.audit_dir / "summary.json"),
        "counts": counts,
        "allowed_input_source": True,
    }
    write_json(args.output_dir / "input_manifest.json", input_manifest)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": NEXT_TODO if not errors else "compatibility_dataset_v3_sanitized_view_smoke_plan_repair",
        "audit_root": rel_path(args.audit_dir),
        "output_root": rel_path(args.output_dir),
        "counts": counts,
        "validation_errors": len(errors),
        "learned_smoke_executed": False,
        "smoke_runner_implementation_allowed": not errors,
        "paper_evidence_allowed": False,
        "primary_model": "M5b_compatibility_TG_interaction",
        "primary_gate_auroc_min": PRIMARY_AUROC_MIN,
        "near_chance_baseline_auroc_max": PASS_AUROC_NEAR_CHANCE_MAX,
        "primary_gain_min": PRIMARY_GAIN_MIN,
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "input_manifest": rel_path(args.output_dir / "input_manifest.json"),
            "smoke_plan": rel_path(args.output_dir / "smoke_plan.json"),
            "model_views": rel_path(args.output_dir / "model_views.csv"),
            "gates": rel_path(args.output_dir / "gates.csv"),
            "controls": rel_path(args.output_dir / "controls.csv"),
            "input_profile": rel_path(args.output_dir / "input_profile.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "boundary": {
            "split": "train_only_smoke_plan",
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "raw_candidate_rows_promoted_as_model_input": False,
        },
    }
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary)


if __name__ == "__main__":
    main()
