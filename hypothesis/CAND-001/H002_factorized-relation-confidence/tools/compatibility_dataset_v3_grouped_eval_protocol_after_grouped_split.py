#!/usr/bin/env python3
"""Write and validate the H002 grouped evaluation protocol after grouped split."""

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

DEFAULT_GROUPED_SPLIT_STAGE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit"
)
DEFAULT_SPLIT_DIR = REPO_ROOT / "experiments/H002_compatibility_routing/splits/latest"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split"
)

EXPECTED_PREV_STATUS = (
    "h002_compatibility_dataset_v3_grouped_split_protocol_after_materialization_schema_audit_ready"
)
EXPECTED_PREV_NEXT = "compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split"
EXPECTED_ROW_COUNT = 6952
EXPECTED_GROUP_COUNT = 3684
EXPECTED_ROUTE_FAMILIES = {
    "relative_vertical",
    "size_relative",
    "relative_horizontal",
    "support_contact",
}
EXPECTED_ALLOWED_C_E_BLOCKS = ("T_e", "G_e")
EXPECTED_BLOCKED_C_E_BLOCKS = ("Z_e", "Q_e", "extra_safe_blocks")

SCHEMA_VERSION = "h002_compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split_v1"
STATUS_READY = "h002_compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split_ready"
STATUS_ERROR = "h002_compatibility_dataset_v3_grouped_eval_protocol_after_grouped_split_input_errors"
SELECTED_PATH = "grouped_eval_protocol_ready_select_grouped_eval_runner"
NEXT_TODO = "compatibility_dataset_v3_grouped_eval_runner_after_protocol"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grouped-split-stage-dir", type=Path, default=DEFAULT_GROUPED_SPLIT_STAGE_DIR)
    parser.add_argument("--split-dir", type=Path, default=DEFAULT_SPLIT_DIR)
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
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def model_view_contract() -> list[dict[str, Any]]:
    return [
        {
            "view_id": "M0_constant",
            "role": "sanity_baseline",
            "allowed_blocks": [],
            "feature_policy": "majority_prior_only",
            "claim_use": "sanity_only",
        },
        {
            "view_id": "M1_T_semantic_only",
            "role": "semantic_content_baseline",
            "allowed_blocks": ["T_e"],
            "feature_policy": "predicate_text_label_relation_family_subject_object_class_only",
            "claim_use": "baseline",
        },
        {
            "view_id": "M2_G_geometry_only",
            "role": "predicate_independent_geometry_baseline",
            "allowed_blocks": ["G_e"],
            "feature_policy": "numeric_geometry_vector_and_availability_mask_only",
            "claim_use": "baseline",
        },
        {
            "view_id": "M3_T_plus_G_concat",
            "role": "naive_fusion_baseline",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "plain_concatenation_without_explicit_TxG_cross_terms",
            "claim_use": "baseline",
        },
        {
            "view_id": "M4_TxG_compatibility",
            "role": "primary_compatibility_model",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "predicate_or_relation_family_conditioned_geometry_interaction_terms_allowed",
            "claim_use": "primary_C_e_evidence",
        },
        {
            "view_id": "C1_wrong_T_control",
            "role": "counterfactual_control",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "reuse_M4_with_wrong_predicate_or_wrong_semantic_T_e_within_family_when_possible",
            "claim_use": "control_must_degrade_or_invert",
        },
        {
            "view_id": "C2_shuffled_G_control",
            "role": "counterfactual_control",
            "allowed_blocks": ["T_e", "G_e"],
            "feature_policy": "reuse_M4_with_G_e_shuffled_within_route_family_and_split",
            "claim_use": "control_must_degrade_toward_chance",
        },
        {
            "view_id": "D1_Z_source_confidence_diagnostic",
            "role": "diagnostic_only_not_C_e",
            "allowed_blocks": ["Z_e"],
            "feature_policy": "source_score_rank_band_source_id_only",
            "claim_use": "diagnostic_source_shortcut_check_only",
        },
        {
            "view_id": "D2_Q_observability_diagnostic",
            "role": "diagnostic_only_not_C_e",
            "allowed_blocks": ["Q_e"],
            "feature_policy": "observability_quality_and_availability_only",
            "claim_use": "diagnostic_Q_e_for_future_p_obs_only",
        },
    ]


def metric_contract() -> dict[str, Any]:
    return {
        "target": "C_e",
        "target_field": "target_y",
        "train_split": "internal_train",
        "dev_split": "internal_dev",
        "heldout_split": "internal_heldout",
        "selection_policy": [
            "fit model or rule on internal_train only",
            "use internal_dev only for model-view selection or threshold/calibration diagnostics",
            "report internal_heldout only after the protocol and runner are fixed",
        ],
        "required_metrics": [
            "AUROC",
            "AUPRC",
            "balanced_accuracy",
            "macro_F1",
            "Brier",
            "NLL_if_probabilistic",
        ],
        "required_report_breakdowns": [
            "overall_macro_over_route_families",
            "per_route_family",
            "per_predicate",
            "internal_dev",
            "internal_heldout",
        ],
        "primary_comparison": "M4_TxG_compatibility_vs_M1_T_semantic_only_M2_G_geometry_only_M3_T_plus_G_concat",
        "control_comparisons": [
            "M4_TxG_compatibility_vs_C1_wrong_T_control",
            "M4_TxG_compatibility_vs_C2_shuffled_G_control",
        ],
        "minimum_reporting_rule": "do not average away a failed route family; report family rows before macro summary",
    }


def blocked_feature_contract() -> dict[str, Any]:
    return {
        "blocked_for_all_models": [
            "cv_group_id",
            "unified_row_id",
            "source_row_id",
            "source_artifact",
            "model_safe_source",
            "protocol_split",
            "split_policy",
            "feature_use_policy",
            "paper_metric_ready",
            "route_role",
            "hidden_manifest_fields",
            "construction_bucket",
            "label_match_status",
            "geometry_status",
            "candidate_bucket",
            "distance_bucket",
        ],
        "blocked_for_C_e_main": [
            "feature_blocks.Z_e",
            "feature_blocks.Q_e",
            "feature_blocks.extra_safe_blocks",
        ],
        "allowed_for_C_e_main": [
            "feature_blocks.T_e",
            "feature_blocks.G_e",
        ],
        "diagnostic_only_not_main_C_e": [
            "D1_Z_source_confidence_diagnostic",
            "D2_Q_observability_diagnostic",
        ],
    }


def output_contract() -> dict[str, Any]:
    return {
        "next_runtime_output_root": "experiments/H002_compatibility_routing/evaluation/latest",
        "expected_files": [
            "eval_manifest.json",
            "model_view_manifest.json",
            "route_metrics.csv",
            "predicate_metrics.csv",
            "control_metrics.csv",
            "prediction_scores.jsonl",
            "leakage_audit.csv",
            "validation_errors.jsonl",
        ],
        "compact_results_policy": (
            "do not copy metrics to results/h002_compatibility_routing until the grouped "
            "evaluation runner validates controls and a result-review stage exists"
        ),
    }


def next_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "must_do": [
            "implement grouped evaluation runner or Docker service following this protocol",
            "fit only on internal_train and evaluate on internal_dev/internal_heldout",
            "emit per-family and per-predicate metrics for all required model views",
            "emit wrong-T and shuffled-G controls for the primary compatibility model",
            "keep Q_e and Z_e out of main C_e unless a later protocol explicitly changes the claim",
        ],
        "must_not_do": [
            "call internal_heldout official validation or official test",
            "use cv_group_id, source ids, protocol_split, or hidden construction fields as features",
            "promote metrics to paper results without a grouped result-review and claim-lock stage",
            "claim p_obs or p_rel calibration from this C_e-only protocol",
        ],
    }


def validate_inputs(prev: dict[str, Any], split_manifest: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if prev.get("status") != EXPECTED_PREV_STATUS:
        errors.append({"error_type": "unexpected_previous_status", "actual": prev.get("status")})
    if prev.get("next_todo") != EXPECTED_PREV_NEXT:
        errors.append({"error_type": "unexpected_previous_next_todo", "actual": prev.get("next_todo")})
    if int(prev.get("validation_errors", 0) or 0) != 0:
        errors.append({"error_type": "previous_stage_validation_errors", "actual": prev.get("validation_errors")})
    if split_manifest.get("official_validation_or_test") is not False:
        errors.append({"error_type": "split_manifest_official_flag_not_false"})
    boundary = split_manifest.get("boundary", {})
    for key in ["paper_metric_produced", "grouped_holdout_metric_run", "official_validation_usage", "official_test_usage", "h001_artifacts_modified"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "split_boundary_not_false", "key": key, "actual": boundary.get(key)})
    row_counts = split_manifest.get("row_counts", {})
    if row_counts.get("model_safe_split_view") != EXPECTED_ROW_COUNT or len(rows) != EXPECTED_ROW_COUNT:
        errors.append({"error_type": "unexpected_row_count", "manifest": row_counts, "actual": len(rows)})
    if row_counts.get("split_assignments") != EXPECTED_GROUP_COUNT:
        errors.append({"error_type": "unexpected_group_count", "manifest": row_counts})

    families = {row.get("route_family") for row in rows}
    if families != EXPECTED_ROUTE_FAMILIES:
        errors.append({"error_type": "unexpected_route_families", "actual": sorted(families)})

    split_counts: Counter[str] = Counter()
    label_by_family_split: dict[tuple[str, str], Counter[int]] = defaultdict(Counter)
    group_to_split: dict[str, set[str]] = defaultdict(set)
    policy_counts: Counter[tuple[tuple[str, ...], tuple[str, ...]]] = Counter()
    bad_policy_examples: list[str] = []
    for row in rows:
        split_counts[row["protocol_split"]] += 1
        label_by_family_split[(row["route_family"], row["protocol_split"])][int(row["target_y"])] += 1
        group_to_split[row["cv_group_id"]].add(row["protocol_split"])
        if row.get("target_name") != "C_e":
            errors.append({"error_type": "non_C_e_target_present", "unified_row_id": row.get("unified_row_id"), "target_name": row.get("target_name")})
            break
        policy = row.get("feature_use_policy", {})
        allowed = tuple(policy.get("C_e_allowed_blocks", []))
        blocked = tuple(policy.get("C_e_blocked_blocks", []))
        policy_counts[(allowed, blocked)] += 1
        if allowed != EXPECTED_ALLOWED_C_E_BLOCKS or blocked != EXPECTED_BLOCKED_C_E_BLOCKS:
            bad_policy_examples.append(row.get("unified_row_id", "unknown"))
        if row.get("source_split") != "train":
            errors.append({"error_type": "non_train_source_split_present", "unified_row_id": row.get("unified_row_id"), "source_split": row.get("source_split")})
            break
        if row.get("paper_metric_ready") is not False:
            errors.append({"error_type": "row_paper_metric_ready_not_false", "unified_row_id": row.get("unified_row_id")})
            break
    leaked_groups = [group for group, splits in group_to_split.items() if len(splits) > 1]
    if leaked_groups:
        errors.append({"error_type": "cv_group_split_leakage", "count": len(leaked_groups), "examples": leaked_groups[:5]})
    if bad_policy_examples:
        errors.append({"error_type": "unexpected_feature_use_policy", "examples": bad_policy_examples[:5], "policy_counts": {str(k): v for k, v in policy_counts.items()}})
    for family in EXPECTED_ROUTE_FAMILIES:
        for split in ["internal_train", "internal_dev", "internal_heldout"]:
            labels = label_by_family_split[(family, split)]
            if labels[0] == 0 or labels[1] == 0:
                errors.append({"error_type": "missing_label_in_family_split", "family": family, "split": split, "labels": dict(labels)})
    return errors


def row_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_family = Counter(row["route_family"] for row in rows)
    by_split = Counter(row["protocol_split"] for row in rows)
    by_family_split: dict[str, dict[str, int]] = defaultdict(dict)
    by_family_label: dict[str, dict[str, int]] = defaultdict(dict)
    for row in rows:
        by_family_split[row["route_family"]][row["protocol_split"]] = (
            by_family_split[row["route_family"]].get(row["protocol_split"], 0) + 1
        )
        key = str(row["target_y"])
        by_family_label[row["route_family"]][key] = by_family_label[row["route_family"]].get(key, 0) + 1
    return {
        "rows": len(rows),
        "route_families": dict(sorted(by_family.items())),
        "splits": dict(sorted(by_split.items())),
        "route_family_by_split": {k: dict(sorted(v.items())) for k, v in sorted(by_family_split.items())},
        "route_family_by_label": {k: dict(sorted(v.items())) for k, v in sorted(by_family_label.items())},
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    model_views = payload["model_views"]
    lines = [
        "# H002 Grouped Evaluation Protocol",
        "",
        "## Verdict",
        "",
        "Grouped evaluation protocol is ready. This stage defines the internal train/dev/heldout evaluation contract but does not run metrics.",
        "",
        "## Scope",
        "",
        f"- target: `{payload['metric_contract']['target']}`",
        f"- train split: `{payload['metric_contract']['train_split']}`",
        f"- dev split: `{payload['metric_contract']['dev_split']}`",
        f"- heldout split: `{payload['metric_contract']['heldout_split']}`",
        f"- rows: `{payload['row_summary']['rows']}`",
        "- official validation/test: `False`",
        "- paper metric produced: `False`",
        "",
        "## Model Views",
        "",
        "| View | Role | Allowed blocks | Claim use |",
        "| --- | --- | --- | --- |",
    ]
    for view in model_views:
        blocks = ", ".join(f"`{block}`" for block in view["allowed_blocks"]) or "`none`"
        lines.append(f"| `{view['view_id']}` | {view['role']} | {blocks} | {view['claim_use']} |")
    lines.extend(
        [
            "",
            "## Required Metrics",
            "",
        ]
    )
    for metric in payload["metric_contract"]["required_metrics"]:
        lines.append(f"- `{metric}`")
    lines.extend(
        [
            "",
            "## Blocked Fields",
            "",
            "The grouped evaluation runner must not use top-level ids, split metadata, hidden construction fields, `Z_e`, or `Q_e` in the main `C_e` model.",
            "",
            "## Next",
            "",
            f"`{payload['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    prev_summary = read_json(args.grouped_split_stage_dir / "summary.json")
    split_manifest = read_json(args.split_dir / "split_manifest.json")
    rows = read_jsonl(args.split_dir / "model_safe_split_view.jsonl")
    errors = validate_inputs(prev_summary, split_manifest, rows)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    status = STATUS_READY if not errors else STATUS_ERROR
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "fix_grouped_eval_protocol_inputs",
        "next_todo": NEXT_TODO if not errors else EXPECTED_PREV_NEXT,
        "created_at_utc": now,
        "validation_errors": len(errors),
        "input_artifacts": {
            "grouped_split_stage": rel_path(args.grouped_split_stage_dir),
            "split_runtime": rel_path(args.split_dir),
            "model_safe_split_view": rel_path(args.split_dir / "model_safe_split_view.jsonl"),
        },
        "row_summary": row_summary(rows),
        "model_views": model_view_contract(),
        "metric_contract": metric_contract(),
        "blocked_feature_contract": blocked_feature_contract(),
        "output_contract": output_contract(),
        "boundary": {
            "protocol_only": True,
            "grouped_metric_run": False,
            "paper_metric_produced": False,
            "official_validation_usage": False,
            "official_test_usage": False,
            "p_obs_claim_enabled": False,
            "p_rel_claim_enabled": False,
            "h001_artifacts_modified": False,
        },
        "next_step_contract": next_contract(),
    }

    write_json(args.output_dir / "summary.json", payload)
    write_json(args.output_dir / "model_view_contract.json", model_view_contract())
    write_json(args.output_dir / "metric_contract.json", metric_contract())
    write_json(args.output_dir / "blocked_feature_contract.json", blocked_feature_contract())
    write_json(args.output_dir / "output_contract.json", output_contract())
    write_json(args.output_dir / "next_contract.json", next_contract())
    write_csv(args.output_dir / "model_view_contract.csv", model_view_contract())
    write_csv(args.output_dir / "route_split_counts.csv", read_csv(args.split_dir / "route_split_counts.csv"))
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
