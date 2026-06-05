#!/usr/bin/env python3
"""Freeze paper-facing Open3DSG caveat wording."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_paper_caveats_v2"
STATUS_READY = "open3dsg_paper_caveats_ready"
STATUS_BLOCKED = "blocked_missing_required_inputs"
STATUS_CHECKPOINT_AVG = "checkpoint_selection_ready_labeled_avg_blip_variant"
STATUS_CHECKPOINT_NON_AVG = "checkpoint_selection_ready_official_non_avg_blip"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/paper_caveats"),
    )
    parser.add_argument(
        "--train-filter",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/train_preprocess_filter/manifest.json"),
    )
    parser.add_argument(
        "--validation-filter",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/validation_preprocess_filter/manifest.json"),
    )
    parser.add_argument(
        "--h001-feature-audit",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/dump_features_h001_eval/manifest.json"),
    )
    parser.add_argument(
        "--metric-scope",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/metric_scope/manifest.json"),
    )
    parser.add_argument(
        "--checkpoint-selection",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/manifest.json"),
    )
    parser.add_argument(
        "--raw-identity",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/raw_dump_identity/manifest.json"),
    )
    parser.add_argument(
        "--adapter",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/adapter/manifest.json"),
    )
    parser.add_argument(
        "--case-inspection",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/failure_cases/inspection.json"),
    )
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def get(payload: dict[str, Any], path: list[str], default: Any = None) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def ratio_text(kept: Any, total: Any, noun: str) -> str:
    return f"{kept}/{total} {noun}"


def build_payload(repo_root: Path, paths: dict[str, Path], inputs: dict[str, dict[str, Any]], out_dir: Path) -> dict[str, Any]:
    train = inputs["train_filter"]
    validation = inputs["validation_filter"]
    feature = inputs["h001_feature_audit"]
    scope = inputs["metric_scope"]
    checkpoint = inputs["checkpoint_selection"]
    raw_identity = inputs["raw_identity"]
    adapter = inputs["adapter"]
    inspection = inputs["case_inspection"]

    selected_run = feature.get("selected_run_audit", {})
    feature_validation = get(selected_run, ["split_coverage", "validation"], {})
    ground_truth = scope.get("ground_truth_denominator", {})
    checkpoint_payload = checkpoint.get("selected_checkpoint", {})
    checkpoint_status = checkpoint.get("status")
    route_comparison = checkpoint.get("route_comparison", {})
    raw_scope = raw_identity.get("scope", {})
    raw_dump = raw_identity.get("raw_dump", {})

    facts = {
        "train_filter": {
            "original_scans": get(train, ["original", "unique_scans"]),
            "filtered_scans": get(train, ["filtered", "unique_scans"]),
            "original_subgraphs": get(train, ["original", "subgraphs"]),
            "filtered_subgraphs": get(train, ["filtered", "subgraphs"]),
            "original_relations": get(train, ["original", "relations"]),
            "filtered_relations": get(train, ["filtered", "relations"]),
            "removed_subgraphs": get(train, ["removed", "subgraphs"]),
            "removed_relations": get(train, ["removed", "relations"]),
            "removed_only_scans": get(train, ["removed", "removed_only_scans"]),
            "recoverability_decision": get(train, ["recoverability", "decision"]),
        },
        "train_dev_filter": {
            "original_scans": get(validation, ["original", "unique_scans"]),
            "filtered_scans": get(validation, ["filtered", "unique_scans"]),
            "original_subgraphs": get(validation, ["original", "subgraphs"]),
            "filtered_subgraphs": get(validation, ["filtered", "subgraphs"]),
            "original_relations": get(validation, ["original", "relations"]),
            "filtered_relations": get(validation, ["filtered", "relations"]),
            "removed_subgraphs": get(validation, ["removed", "subgraphs"]),
            "removed_relations": get(validation, ["removed", "relations"]),
            "recoverability_decision": get(validation, ["recoverability", "decision"]),
        },
        "h001_eval_coverage": {
            "selected_scans": raw_scope.get("selected_scans"),
            "identity_contexts": raw_scope.get("contexts"),
            "identity_directed_pairs": raw_scope.get("directed_pairs"),
            "loadable_feature_ids": feature_validation.get("expected_unique"),
            "complete_feature_ids": feature_validation.get("complete_all_roles"),
            "missing_preprocessed": feature_validation.get("missing_preprocessed"),
            "raw_dump_rows": raw_dump.get("row_count"),
            "adapter_prediction_rows": get(adapter, ["counts", "prediction_rows"]),
            "adapter_filtered_raw_rows": get(adapter, ["counts", "raw_rows_filtered_outside_h001_context"]),
        },
        "metric_denominator": {
            "gt_rows": ground_truth.get("rows"),
            "in_scope_gt_denominator": ground_truth.get("in_scope_gt_denominator"),
            "target_family_counts": ground_truth.get("target_family_counts"),
            "excluded_gt_rows": ground_truth.get("excluded_gt_rows"),
            "recall_matching": "exact predicate-label matching",
        },
        "variant": {
            "selected_checkpoint": checkpoint_payload.get("checkpoint_path"),
            "source_stage": checkpoint_payload.get("source_stage"),
            "selection_signal": checkpoint_payload.get("selection_metric_source"),
            "train_dev_val_loss": get(checkpoint_payload, ["training_internal_val_loss", "value"]),
            "train_dev_val_loss_step": get(checkpoint_payload, ["training_internal_val_loss", "step"]),
            "claim_limitations": checkpoint.get("claim_limitations", []),
        },
        "residual_calibration": {
            "inspection_status": inspection.get("status"),
            "selected_cases": get(inspection, ["counts", "selected_cases"]),
            "demoted_by_geometry": get(inspection, ["counts", "demoted_by_geometry"]),
            "promoted_or_retained_by_geometry": get(inspection, ["counts", "promoted_or_retained_by_geometry"]),
            "violated_with_p_geom_valid_gt_0_9": get(inspection, ["counts", "violated_with_p_geom_valid_gt_0_9"]),
            "claim_boundary": inspection.get("claim_boundary"),
        },
    }

    non_avg_selected_note = ""
    if checkpoint_status == STATUS_CHECKPOINT_NON_AVG:
        non_avg_selected_note = (
            " A separate official non-averaged BLIP checkpoint selection now exists, "
            "but the downstream H001 Open3DSG raw dump, adapter, geometry, metrics, "
            "bootstrap CI, Table 6, and caveat wording have not been regenerated for "
            "that route; current paper-facing metrics remain the averaged-BLIP result."
        )

    fixed_wording = {
        "table_note_short": (
            "Open3DSG results use a Docker-reproduced averaged-BLIP variant selected by train-dev val/loss before H001 held-out inspection. "
            "They are reported on the Open3DSG-covered H001 eval scope after preprocessed-ready filtering, with exact-label recall over 2,545 in-scope GT relations."
        ),
        "scope_caveat": (
            "Open3DSG training uses an explicit preprocessed-ready split: "
            f"{ratio_text(facts['train_filter']['filtered_scans'], facts['train_filter']['original_scans'], 'train scans')}, "
            f"{ratio_text(facts['train_filter']['filtered_subgraphs'], facts['train_filter']['original_subgraphs'], 'train subgraphs')}, and "
            f"{ratio_text(facts['train_filter']['filtered_relations'], facts['train_filter']['original_relations'], 'train relations')}. "
            "The train-dev validation split is also filtered to "
            f"{ratio_text(facts['train_dev_filter']['filtered_subgraphs'], facts['train_dev_filter']['original_subgraphs'], 'subgraphs')}. "
            "H001 evaluation uses the covered loadable Open3DSG scope with "
            f"{ratio_text(facts['h001_eval_coverage']['complete_feature_ids'], facts['h001_eval_coverage']['identity_contexts'], 'contexts/features')} "
            "and reports `validation_missing_preprocessed:11` as an explicit caveat."
        ),
        "variant_caveat": (
            "The Open3DSG checkpoint is an explicitly labeled averaged-BLIP variant, not the exact non-averaged BLIP projector route. "
            "The selected checkpoint is `epoch=13-step=13104.ckpt`, chosen by train-dev `val/loss` 0.3288108110 at step 13103 before H001 held-out metric, failure, or visual inspection."
            + non_avg_selected_note
        ),
        "denominator_caveat": (
            "Open3DSG recall is exact predicate-label matched. Family grouping is used for reliability/violation reporting only. "
            "The reported H001-family denominator is 2,545 GT rows: support_contact 1,199, proximity 1,128, and relative_vertical 218; 4,960 other-family GT rows are outside the H001 metric claim."
        ),
        "residual_calibration_caveat": (
            "The calibrated `p_geom_valid` score is not a hard validity label. Qualitative inspection found 10/36 sampled rule-violated cases with `p_geom_valid > 0.9`, so probabilistic, rule-verified, and family-specific variants must be reported separately."
        ),
        "non_claim": (
            "These Open3DSG results support measured H001-family relation-reliability evidence, not broad open-vocabulary 3DSSG generation improvement and not arbitrary-baseline generality."
        ),
    }

    validation_errors: list[str] = []
    validation_warnings: list[str] = []
    expected_statuses = {
        "train_filter": "filter_applied",
        "validation_filter": "filter_applied",
        "metric_scope": "metric_scope_policy_ready_no_metric_execution",
        "raw_identity": "raw_dump_identity_audit_ready",
        "adapter": "ready",
        "case_inspection": "qualitative_case_inspection_ready",
    }
    for name, status in expected_statuses.items():
        if inputs[name].get("status") != status:
            validation_errors.append(f"{name}_status:{inputs[name].get('status')}!= {status}")
    if checkpoint_status not in {STATUS_CHECKPOINT_AVG, STATUS_CHECKPOINT_NON_AVG}:
        validation_errors.append(f"checkpoint_selection_status:{checkpoint_status} not in accepted paper-caveat statuses")
    if checkpoint_status == STATUS_CHECKPOINT_NON_AVG:
        validation_warnings.append("checkpoint_selection_is_official_non_avg_but_active_downstream_result_remains_avg_blip")
        delta = route_comparison.get("train_dev_val_loss_delta_non_avg_minus_avg")
        if delta is not None and delta > 0:
            validation_warnings.append(f"non_avg_train_dev_val_loss_worse_than_avg_blip_by:{delta}")
    if feature_validation.get("missing_preprocessed") != 11:
        validation_errors.append(f"unexpected_validation_missing_preprocessed:{feature_validation.get('missing_preprocessed')}")
    if feature_validation.get("complete_all_roles") != 377:
        validation_errors.append(f"unexpected_complete_feature_ids:{feature_validation.get('complete_all_roles')}")
    if ground_truth.get("in_scope_gt_denominator") != 2545:
        validation_errors.append(f"unexpected_in_scope_gt_denominator:{ground_truth.get('in_scope_gt_denominator')}")

    outputs = {
        "manifest_json": relpath(repo_root, out_dir / "manifest.json"),
        "report_md": relpath(repo_root, out_dir / "report.md"),
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY if not validation_errors else STATUS_BLOCKED,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {name: relpath(repo_root, path) for name, path in paths.items()},
        "facts": facts,
        "fixed_wording": fixed_wording,
        "validation": {"errors": validation_errors, "warnings": validation_warnings},
        "outputs": outputs,
        "claim_boundary": (
            "Paper-facing wording artifact only. It fixes how to report Open3DSG scope/variant/calibration caveats; "
            "it does not change metrics, taxonomy, checkpoint selection, or denominator policy."
        ),
    }


def build_report(payload: dict[str, Any]) -> str:
    facts = payload["facts"]
    wording = payload["fixed_wording"]
    lines = [
        "# Open3DSG Paper Caveats",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "## Purpose",
        "",
        "This artifact freezes the paper-facing caveat wording for Open3DSG Table 6 and failure-analysis discussion.",
        "It does not change metrics, taxonomy, checkpoint selection, or denominator policy.",
        "",
        "## Fixed Wording",
        "",
    ]
    for key, text in wording.items():
        lines.append(f"### `{key}`")
        lines.append("")
        lines.append(text)
        lines.append("")

    lines.extend(
        [
            "## Coverage Facts",
            "",
            "### Train Filter",
            "",
            f"- train scans: `{facts['train_filter']['filtered_scans']}/{facts['train_filter']['original_scans']}`",
            f"- train subgraphs: `{facts['train_filter']['filtered_subgraphs']}/{facts['train_filter']['original_subgraphs']}`",
            f"- train relations: `{facts['train_filter']['filtered_relations']}/{facts['train_filter']['original_relations']}`",
            f"- removed subgraphs/relations: `{facts['train_filter']['removed_subgraphs']}/{facts['train_filter']['removed_relations']}`",
            f"- recoverability: `{facts['train_filter']['recoverability_decision']}`",
            "",
            "### Train-Dev Validation Filter",
            "",
            f"- validation scans: `{facts['train_dev_filter']['filtered_scans']}/{facts['train_dev_filter']['original_scans']}`",
            f"- validation subgraphs: `{facts['train_dev_filter']['filtered_subgraphs']}/{facts['train_dev_filter']['original_subgraphs']}`",
            f"- validation relations: `{facts['train_dev_filter']['filtered_relations']}/{facts['train_dev_filter']['original_relations']}`",
            f"- recoverability: `{facts['train_dev_filter']['recoverability_decision']}`",
            "",
            "### H001 Eval Coverage",
            "",
            f"- selected scans / identity contexts / directed pairs: `{facts['h001_eval_coverage']['selected_scans']}` / `{facts['h001_eval_coverage']['identity_contexts']}` / `{facts['h001_eval_coverage']['identity_directed_pairs']}`",
            f"- complete feature ids: `{facts['h001_eval_coverage']['complete_feature_ids']}`",
            f"- missing preprocessed contexts: `{facts['h001_eval_coverage']['missing_preprocessed']}`",
            f"- raw dump rows: `{facts['h001_eval_coverage']['raw_dump_rows']}`",
            f"- adapter prediction rows: `{facts['h001_eval_coverage']['adapter_prediction_rows']}`",
            f"- adapter filtered raw rows outside H001 object context: `{facts['h001_eval_coverage']['adapter_filtered_raw_rows']}`",
            "",
            "### Metric Denominator",
            "",
            f"- GT rows: `{facts['metric_denominator']['gt_rows']}`",
            f"- in-scope GT denominator: `{facts['metric_denominator']['in_scope_gt_denominator']}`",
            f"- target family counts: `{facts['metric_denominator']['target_family_counts']}`",
            f"- excluded GT rows: `{facts['metric_denominator']['excluded_gt_rows']}`",
            "",
            "### Residual Calibration Risk",
            "",
            f"- inspected cases: `{facts['residual_calibration']['selected_cases']}`",
            f"- demoted by geometry-aware reranking: `{facts['residual_calibration']['demoted_by_geometry']}`",
            f"- promoted or retained: `{facts['residual_calibration']['promoted_or_retained_by_geometry']}`",
            f"- rule-violated with p_geom_valid > 0.9: `{facts['residual_calibration']['violated_with_p_geom_valid_gt_0_9']}`",
            "",
            "## Validation",
            "",
        ]
    )
    errors = payload["validation"]["errors"]
    if errors:
        for error in errors:
            lines.append(f"- `{error}`")
    else:
        lines.append("- no validation errors")
    warnings = payload["validation"].get("warnings", [])
    if warnings:
        lines.append("")
        lines.append("Warnings:")
        lines.append("")
        for warning in warnings:
            lines.append(f"- `{warning}`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            payload["claim_boundary"],
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root
    out_dir = resolve(repo_root, args.out)
    paths = {
        "train_filter": resolve(repo_root, args.train_filter),
        "validation_filter": resolve(repo_root, args.validation_filter),
        "h001_feature_audit": resolve(repo_root, args.h001_feature_audit),
        "metric_scope": resolve(repo_root, args.metric_scope),
        "checkpoint_selection": resolve(repo_root, args.checkpoint_selection),
        "raw_identity": resolve(repo_root, args.raw_identity),
        "adapter": resolve(repo_root, args.adapter),
        "case_inspection": resolve(repo_root, args.case_inspection),
    }

    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_BLOCKED,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "missing_inputs": {name: relpath(repo_root, paths[name]) for name in missing},
        }
        write_json(out_dir / "manifest.json", payload)
        (out_dir / "report.md").write_text("# Open3DSG Paper Caveats\n\nStatus: `blocked_missing_required_inputs`\n", encoding="utf-8")
        print(json.dumps({"status": STATUS_BLOCKED, "missing": missing}, sort_keys=True))
        return

    inputs = {name: load_json(path) for name, path in paths.items()}
    payload = build_payload(repo_root, paths, inputs, out_dir)
    write_json(out_dir / "manifest.json", payload)
    (out_dir / "report.md").write_text(build_report(payload), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "manifest": relpath(repo_root, out_dir / "manifest.json")}, sort_keys=True))


if __name__ == "__main__":
    main()
