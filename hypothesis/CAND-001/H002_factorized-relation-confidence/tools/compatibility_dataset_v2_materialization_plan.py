#!/usr/bin/env python3
"""Plan how to materialize the H002 compatibility dataset v2."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
RGA_ROOT = H2_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_CONTRACT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_contract"
DEFAULT_PROTOTYPE_DIR = H2_ROOT / "artifacts/prototype_dataset_v1"
DEFAULT_INGESTION_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_ingestion_all_label_ready_user_confirmed"
DEFAULT_TARGET_AUDIT_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_target_independence_audit_all_label_ready_user_confirmed"
DEFAULT_RAW_WITNESS_DIR = RGA_ROOT / "independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_all_label_ready"
DEFAULT_V16_CAPACITY_DIR = RGA_ROOT / "reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v2_materialization_plan"

EXPECTED_CONTRACT_STATUS = "h002_compatibility_dataset_v2_contract_ready"
EXPECTED_CONTRACT_NEXT = "compatibility_dataset_v2_materialization_plan"
EXPECTED_PROTOTYPE_STATUS = "h002_prototype_dataset_v1_ready"
EXPECTED_INGESTION_STATUS = "full_train_independent_support_vertical_v2_revised_sampling_ingested_with_basic_probe_risk"
EXPECTED_TARGET_AUDIT_STATUS = (
    "full_train_independent_support_vertical_v2_revised_sampling_target_independence_audit_relation_strict_slice_ready"
)
EXPECTED_RAW_WITNESS_STATUS = "full_train_independent_support_vertical_v2_revised_sampling_raw_witness_feature_join_v2_ready"
EXPECTED_V16_CAPACITY_STATUS = "h002_reliability_target_v16_cross_stratum_support_contact_contrast_capacity_scan_blocked_capacity_or_controls"

SCHEMA_VERSION = "h002_compatibility_dataset_v2_materialization_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v2_materialization_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v2_materialization_plan_input_errors"
NEXT_TODO = "compatibility_dataset_v2_capacity_scan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract-dir", type=Path, default=DEFAULT_CONTRACT_DIR)
    parser.add_argument("--prototype-dir", type=Path, default=DEFAULT_PROTOTYPE_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
    parser.add_argument("--target-audit-dir", type=Path, default=DEFAULT_TARGET_AUDIT_DIR)
    parser.add_argument("--raw-witness-dir", type=Path, default=DEFAULT_RAW_WITNESS_DIR)
    parser.add_argument("--v16-capacity-dir", type=Path, default=DEFAULT_V16_CAPACITY_DIR)
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


def read_csv(path: Path) -> list[dict[str, str]]:
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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validation_count(value: Any) -> int:
    if value in (None, 0, [], {}):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, list):
        return len(value)
    return 1


def bool_from_csv(value: str) -> bool:
    return value.strip().lower() == "true"


def validate_inputs(
    contract_summary: dict[str, Any],
    prototype_summary: dict[str, Any],
    ingestion_summary: dict[str, Any],
    target_audit_summary: dict[str, Any],
    raw_witness_summary: dict[str, Any],
    v16_capacity_summary: dict[str, Any],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = [
        ("contract", contract_summary, EXPECTED_CONTRACT_STATUS),
        ("prototype", prototype_summary, EXPECTED_PROTOTYPE_STATUS),
        ("ingestion", ingestion_summary, EXPECTED_INGESTION_STATUS),
        ("target_audit", target_audit_summary, EXPECTED_TARGET_AUDIT_STATUS),
        ("raw_witness", raw_witness_summary, EXPECTED_RAW_WITNESS_STATUS),
        ("v16_capacity", v16_capacity_summary, EXPECTED_V16_CAPACITY_STATUS),
    ]
    for name, payload, status in expected:
        if payload.get("status") != status:
            errors.append({"error_type": "unexpected_status", "input": name, "expected": status, "actual": payload.get("status")})
        if validation_count(payload.get("validation_errors")) != 0:
            errors.append({"error_type": "input_validation_errors", "input": name, "actual": payload.get("validation_errors")})
        if validation_count(payload.get("counts", {}).get("validation_errors")) != 0:
            errors.append(
                {
                    "error_type": "input_count_validation_errors",
                    "input": name,
                    "actual": payload.get("counts", {}).get("validation_errors"),
                }
            )

    if contract_summary.get("next_todo") != EXPECTED_CONTRACT_NEXT:
        errors.append({"error_type": "unexpected_contract_next", "actual": contract_summary.get("next_todo")})
    if contract_summary.get("posterior_smoke_allowed") is not False:
        errors.append({"error_type": "contract_allows_posterior", "actual": contract_summary.get("posterior_smoke_allowed")})

    for name, payload in [
        ("raw_witness", raw_witness_summary),
        ("ingestion", ingestion_summary),
        ("target_audit", target_audit_summary),
    ]:
        boundary = payload.get("boundary", {})
        if boundary.get("validation_usage") not in (False, None):
            errors.append({"error_type": "validation_usage_not_false", "input": name, "actual": boundary.get("validation_usage")})
        if boundary.get("test_usage") not in (False, None):
            errors.append({"error_type": "test_usage_not_false", "input": name, "actual": boundary.get("test_usage")})
    return errors


def contract_quota_rows(dataset_contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in dataset_contract["family_contract"]:
        if row["scope"].startswith("primary"):
            rows.append(
                {
                    "relation_family": row["relation_family"],
                    "scope": row["scope"],
                    "requested_positive": row["requested_min_positive"],
                    "requested_negative": row["requested_min_negative"],
                    "minimum_reportable_positive": row["minimum_reportable_positive"],
                    "minimum_reportable_negative": row["minimum_reportable_negative"],
                    "materialization_policy": row["materialization_policy"],
                }
            )
    return rows


def prototype_compatibility_counts(prototype_summary: dict[str, Any]) -> dict[str, dict[str, int]]:
    counts = prototype_summary.get("counts", {})
    return {
        "support_contact": {"positive": 50, "negative": 49, "rows": int(counts.get("by_family", {}).get("support_contact", 0))},
        "relative_vertical": {"positive": 17, "negative": 18, "rows": int(counts.get("by_family", {}).get("relative_vertical", 0))},
    }


def ingestion_reliability_counts(ingestion_summary: dict[str, Any]) -> dict[str, dict[str, int]]:
    target = ingestion_summary.get("counts", {}).get("targets", {}).get("relation_reliability_revised_sampling_user_confirmed_target", {})
    family = target.get("by_family", {})
    out: dict[str, dict[str, int]] = {}
    for relation_family in ["support_contact", "relative_vertical"]:
        values = family.get(relation_family, {})
        out[relation_family] = {
            "positive": int(values.get("1", 0)),
            "negative": int(values.get("0", 0)),
            "rows": int(values.get("1", 0)) + int(values.get("0", 0)),
        }
    return out


def compare_to_contract(
    source_name: str,
    source_counts: dict[str, dict[str, int]],
    quota_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    comparisons: list[dict[str, Any]] = []
    quota_by_family = {row["relation_family"]: row for row in quota_rows}
    for family, counts in sorted(source_counts.items()):
        quota = quota_by_family[family]
        pos = int(counts["positive"])
        neg = int(counts["negative"])
        comparisons.append(
            {
                "source": source_name,
                "relation_family": family,
                "positive": pos,
                "negative": neg,
                "rows": int(counts.get("rows", pos + neg)),
                "requested_positive": quota["requested_positive"],
                "requested_negative": quota["requested_negative"],
                "minimum_reportable_positive": quota["minimum_reportable_positive"],
                "minimum_reportable_negative": quota["minimum_reportable_negative"],
                "passes_requested_positive": pos >= int(quota["requested_positive"]),
                "passes_requested_negative": neg >= int(quota["requested_negative"]),
                "passes_minimum_positive": pos >= int(quota["minimum_reportable_positive"]),
                "passes_minimum_negative": neg >= int(quota["minimum_reportable_negative"]),
            }
        )
    return comparisons


def v16_capacity_rows(v16_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in v16_rows:
        out.append(
            {
                "cell_id": row["cell_id"],
                "family": row["family"],
                "predicate_label": row["predicate_label"],
                "queue_kind": row["queue_kind"],
                "role": row["role"],
                "target_rows": int(row["target_rows"]),
                "minimum_rows_after_capacity_scan": int(row["minimum_rows_after_capacity_scan"]),
                "raw_rows": int(row["raw_rows"]),
                "hard_filtered_rows": int(row["hard_filtered_rows"]),
                "eligible_rows": int(row["eligible_rows"]),
                "distinct_scans": int(row["distinct_scans"]),
                "minimum_capacity_pass": bool_from_csv(row["minimum_capacity_pass"]),
                "target_capacity_pass": bool_from_csv(row["target_capacity_pass"]),
            }
        )
    return out


def source_inventory(
    contract_dir: Path,
    prototype_dir: Path,
    ingestion_dir: Path,
    target_audit_dir: Path,
    raw_witness_dir: Path,
    v16_capacity_dir: Path,
    prototype_summary: dict[str, Any],
    ingestion_summary: dict[str, Any],
    target_audit_summary: dict[str, Any],
    raw_witness_summary: dict[str, Any],
    v16_capacity_summary: dict[str, Any],
    v16_quota_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "source_name": "compatibility_dataset_v2_contract",
            "path": rel_path(contract_dir),
            "role": "binding v2 schema, blocked fields, family quotas, and controls",
            "reuse_policy": "must_follow",
        },
        {
            "source_name": "prototype_dataset_v1",
            "path": rel_path(prototype_dir),
            "role": "schema/example seed only",
            "reuse_policy": "do_not_directly_promote_to_v2",
            "key_counts": prototype_summary.get("counts", {}).get("by_family", {}),
            "reason": "primary families are below v2 minimum/reportable mass and attachment is diagnostic-only",
        },
        {
            "source_name": "revised_sampling_all_label_ready_user_confirmed",
            "path": rel_path(ingestion_dir),
            "role": "train-only human-confirmed support/vertical reliability labels",
            "reuse_policy": "seed_and_audit_reference_only",
            "key_counts": ingestion_summary.get("counts", {}).get("targets", {}).get(
                "relation_reliability_revised_sampling_user_confirmed_target", {}
            ),
            "reason": "support positive and relative vertical positive/negative mass are below v2 compatibility quota; labels target reliability rather than clean C_e compatibility",
        },
        {
            "source_name": "revised_sampling_target_independence_audit",
            "path": rel_path(target_audit_dir),
            "role": "evidence that a strict train-only relation-reliability slice exists",
            "reuse_policy": "control_reference_only",
            "key_decision": target_audit_summary.get("decision"),
        },
        {
            "source_name": "raw_witness_feature_join_v2",
            "path": rel_path(raw_witness_dir),
            "role": "best available train-only raw geometry feature adapter seed",
            "reuse_policy": "repackage_required_before_v2",
            "key_decision": raw_witness_summary.get("decision"),
            "reason": "rows are posterior-ready with baseline_inputs, not yet v2 T_e/Z_e/G_e/Q_e compatibility rows",
        },
        {
            "source_name": "v16_cross_stratum_capacity_scan",
            "path": rel_path(v16_capacity_dir),
            "role": "full-train capacity signal for mining support/vertical contrasts",
            "reuse_policy": "capacity_diagnostic_only",
            "key_counts": v16_capacity_summary.get("counts", {}),
            "quota_cells": v16_quota_rows,
            "reason": "capacity is high in some cells, but previous target was blocked by control/shortcut risks and is not a final v2 label sheet",
        },
    ]


def materialization_plan(capacity_rows: list[dict[str, Any]], quota_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "selected_route": "v2_capacity_scan_before_materialization",
        "direct_materialization_allowed": False,
        "why_not_direct_materialization": [
            "prototype v1 does not meet v2 primary family class-mass requirements",
            "all-label-ready support/vertical target is a relation-reliability label source, not a clean compatibility dataset v2 target",
            "raw-witness feature join v2 uses baseline_inputs/posterior-ready schema and must be repackaged into T_e/Z_e/G_e/Q_e",
            "previous v16 capacity scan shows candidate abundance but also control risks; v2-specific capacity scan is required",
        ],
        "reusable_sources": {
            "feature_adapter_seed": "raw_witness_feature_join_v2",
            "label_seed": "revised_sampling_all_label_ready_user_confirmed",
            "capacity_seed": "v16_cross_stratum_capacity_scan",
            "diagnostic_qe_seed": "attachment_independent_positive_anchor_packets_and_labels",
        },
        "capacity_scan_requirements": {
            "output_root": "artifacts/compatibility_dataset_v2_capacity_scan/",
            "required_files": [
                "summary.json",
                "quota_feasibility.csv",
                "capacity_by_family.csv",
                "candidate_pool_preview.jsonl",
                "risk_precheck.json",
                "report.md",
                "validation_errors.jsonl",
            ],
            "must_check": [
                "train_only_provenance",
                "T_e/Z_e/G_e/Q_e separability",
                "C_e excludes Z_e",
                "G_e excludes predicate/family/source/label/construction keys",
                "family positive/negative minimums",
                "predicate and endpoint-label balance",
                "rank/source-score balance",
                "hidden construction probe risk",
                "wrong-pair and shuffled-geometry availability",
                "relative_vertical predicate flip and subject/object swap availability",
            ],
        },
        "family_plan": [
            {
                "relation_family": "support_contact",
                "predicates": ["standing on", "lying on", "supported by"],
                "target_from_contract": next(row for row in quota_rows if row["relation_family"] == "support_contact"),
                "materialization_action": "mine balanced anchor/counterfactual rows from full-train raw-witness features",
                "positive_policy": "clear support/contact geometry or audited accept; no source-only positive",
                "negative_policy": "wrong-pair, shuffled geometry, contact-gap/support perturbation, and same-family/rank/coverage hard negatives",
                "avoid": "do not collapse to only lying-on HL/LH or geometry_status shortcut",
            },
            {
                "relation_family": "relative_vertical",
                "predicates": ["higher than", "lower than"],
                "target_from_contract": next(row for row in quota_rows if row["relation_family"] == "relative_vertical"),
                "materialization_action": "mine directional compatibility rows with explicit predicate flip and subject/object swap controls",
                "positive_policy": "clear vertical order agreement or audited accept",
                "negative_policy": "higher/lower flip, subject/object swap, wrong-pair, shuffled geometry, and same-rank hard negatives",
                "avoid": "do not use only lower-than LH satisfied rows as a shortcut-compatible control",
            },
            {
                "relation_family": "attachment_like",
                "predicates": ["attached to", "hanging on", "connected to"],
                "target_from_contract": "diagnostic_only",
                "materialization_action": "reuse existing packet/label artifacts only for Q_e, observability, and failure taxonomy",
                "positive_policy": "not primary C_e/p_rel unless future independent verification passes",
                "negative_policy": "not primary C_e/p_rel under current contract",
                "avoid": "do not use current positive-anchor labels as main reliability target",
            },
        ],
        "capacity_seed_evidence": capacity_rows,
    }


def build_report(summary: dict[str, Any], plan: dict[str, Any], comparisons: list[dict[str, Any]]) -> str:
    lines = [
        "# H002 Compatibility Dataset V2 Materialization Plan",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_route = {summary['selected_route']}",
        f"direct_materialization_allowed = {str(summary['direct_materialization_allowed']).lower()}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Decision",
        "",
        "Do not directly materialize `h002_compatibility_dataset_v2` from the existing v1/prototype or all-label-ready files.",
        "Use the raw-witness v2 feature join as a feature-adapter seed, then run a v2-specific full-train capacity scan.",
        "",
        "## Why",
        "",
    ]
    for reason in plan["why_not_direct_materialization"]:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## Current Class Mass Check",
            "",
            "| Source | Family | Pos | Neg | Min Pos | Min Neg | Pass Min |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in comparisons:
        pass_min = row["passes_minimum_positive"] and row["passes_minimum_negative"]
        lines.append(
            f"| `{row['source']}` | `{row['relation_family']}` | {row['positive']} | {row['negative']} | "
            f"{row['minimum_reportable_positive']} | {row['minimum_reportable_negative']} | `{pass_min}` |"
        )
    lines.extend(
        [
            "",
            "## Next Capacity Scan",
            "",
            "The next step should create `artifacts/compatibility_dataset_v2_capacity_scan/` and verify whether balanced, shortcut-controlled rows can be mined before any learned smoke.",
            "",
            "Required checks:",
            "",
        ]
    )
    for check in plan["capacity_scan_requirements"]["must_check"]:
        lines.append(f"- `{check}`")
    lines.extend(["", "## Next", "", f"`{summary['next_todo']}`"])
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    contract_summary = read_json(args.contract_dir / "summary.json")
    dataset_contract = read_json(args.contract_dir / "dataset_contract.json")
    prototype_summary = read_json(args.prototype_dir / "summary.json")
    ingestion_summary = read_json(args.ingestion_dir / "summary.json")
    target_audit_summary = read_json(args.target_audit_dir / "summary.json")
    raw_witness_summary = read_json(args.raw_witness_dir / "summary.json")
    input_contract = read_json(args.raw_witness_dir / "input_contract_v2.json")
    v16_capacity_summary = read_json(args.v16_capacity_dir / "summary.json")
    v16_quota = v16_capacity_rows(read_csv(args.v16_capacity_dir / "quota_feasibility.csv"))

    errors = validate_inputs(
        contract_summary,
        prototype_summary,
        ingestion_summary,
        target_audit_summary,
        raw_witness_summary,
        v16_capacity_summary,
    )

    quota_rows = contract_quota_rows(dataset_contract)
    prototype_compare = compare_to_contract("prototype_v1_compatibility", prototype_compatibility_counts(prototype_summary), quota_rows)
    ingestion_compare = compare_to_contract("all_label_ready_relation_reliability", ingestion_reliability_counts(ingestion_summary), quota_rows)
    comparisons = prototype_compare + ingestion_compare

    plan = materialization_plan(v16_quota, quota_rows)
    inventory = source_inventory(
        args.contract_dir,
        args.prototype_dir,
        args.ingestion_dir,
        args.target_audit_dir,
        args.raw_witness_dir,
        args.v16_capacity_dir,
        prototype_summary,
        ingestion_summary,
        target_audit_summary,
        raw_witness_summary,
        v16_capacity_summary,
        v16_quota,
    )

    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_compatibility_dataset_v2_materialization_inputs"
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "validation_errors": len(errors),
        "selected_route": plan["selected_route"],
        "direct_materialization_allowed": plan["direct_materialization_allowed"],
        "next_todo": next_todo,
        "posterior_smoke_allowed": False,
        "paper_evidence_allowed": False,
        "dataset_name": dataset_contract["dataset_name"],
        "input_roots": {
            "contract": rel_path(args.contract_dir),
            "prototype": rel_path(args.prototype_dir),
            "ingestion": rel_path(args.ingestion_dir),
            "target_audit": rel_path(args.target_audit_dir),
            "raw_witness": rel_path(args.raw_witness_dir),
            "v16_capacity": rel_path(args.v16_capacity_dir),
        },
        "current_class_mass_check": comparisons,
        "raw_witness_input_contract": {
            "allowed_model_input_root": input_contract.get("allowed_model_input_root"),
            "schema_version": input_contract.get("schema_version"),
            "requires_repackage_to_v2_factor_blocks": True,
        },
        "boundary": {
            "split": "train_only_plan",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_model": False,
            "materializes_final_dataset": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "materialization_plan": rel_path(args.output_dir / "materialization_plan.json"),
            "source_inventory": rel_path(args.output_dir / "source_inventory.json"),
            "capacity_requirements": rel_path(args.output_dir / "capacity_requirements.csv"),
            "class_mass_check": rel_path(args.output_dir / "class_mass_check.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "materialization_plan.json", plan)
    write_json(args.output_dir / "source_inventory.json", inventory)
    write_csv(args.output_dir / "capacity_requirements.csv", quota_rows)
    write_csv(args.output_dir / "class_mass_check.csv", comparisons)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    (args.output_dir / "report.md").write_text(build_report(summary, plan, comparisons), encoding="utf-8")

    print(f"status={status}")
    print(f"selected_route={plan['selected_route']}")
    print(f"direct_materialization_allowed={plan['direct_materialization_allowed']}")
    print(f"next={next_todo}")
    print(f"validation_errors={len(errors)}")


if __name__ == "__main__":
    main()
