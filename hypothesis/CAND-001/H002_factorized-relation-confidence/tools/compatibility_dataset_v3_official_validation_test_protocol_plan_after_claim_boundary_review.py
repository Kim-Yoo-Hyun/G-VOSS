#!/usr/bin/env python3
"""Plan official validation/test protocol after H002 claim-boundary review."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_CLAIM_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review"
DEFAULT_3DSSG_SUBSET_DIR = REPO_ROOT / "local_dataset/3DSSG_subset"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review"

EXPECTED_CLAIM_STATUS = "h002_compatibility_dataset_v3_repaired_grouped_eval_claim_boundary_review_ready"
EXPECTED_CLAIM_NEXT = "compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review_v1"
STATUS_READY = "h002_compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_official_validation_test_protocol_plan_after_claim_boundary_review_input_errors"
SELECTED_PATH = "official_protocol_ready_select_source_inventory"
NEXT_TODO = "compatibility_dataset_v3_official_source_inventory_after_protocol_plan"

PROMOTED_PREDICATES = {
    "relative_horizontal": ["left", "right", "front", "behind"],
    "relative_vertical": ["higher than", "lower than"],
    "size_relative": ["bigger than", "smaller than"],
    "support_contact": ["standing on", "lying on"],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-dir", type=Path, default=DEFAULT_CLAIM_DIR)
    parser.add_argument("--subset-dir", type=Path, default=DEFAULT_3DSSG_SUBSET_DIR)
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
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
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
                fields.append(key)
                seen.add(key)
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def relationship_predicate(rel: Any) -> str:
    if isinstance(rel, list) and len(rel) >= 4:
        return str(rel[3])
    if isinstance(rel, dict):
        return str(rel.get("predicate") or rel.get("relationship") or rel.get("relation") or "unknown")
    return "unknown"


def scan_relationships(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, dict):
        scans = data.get("scans", [])
    elif isinstance(data, list):
        scans = data
    else:
        scans = []
    return scans if isinstance(scans, list) else []


def split_inventory(subset_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}
    for split in ["train", "validation", "test"]:
        path = subset_dir / f"relationships_{split}.json"
        exists = path.exists()
        rel_counter: Counter[str] = Counter()
        scan_count = 0
        relation_count = 0
        if exists:
            data = read_json(path)
            scans = scan_relationships(data)
            scan_count = len(scans)
            for scan in scans:
                rels = scan.get("relationships", []) if isinstance(scan, dict) else []
                relation_count += len(rels)
                for rel in rels:
                    rel_counter[relationship_predicate(rel)] += 1
        summary[split] = {
            "path": rel_path(path),
            "exists": exists,
            "scan_count": scan_count,
            "relation_count": relation_count,
        }
        for family, predicates in PROMOTED_PREDICATES.items():
            family_total = sum(rel_counter[predicate] for predicate in predicates)
            rows.append(
                {
                    "split": split,
                    "split_file_exists": exists,
                    "route_family": family,
                    "predicates": "; ".join(predicates),
                    "predicate_counts": "; ".join(f"{predicate}={rel_counter[predicate]}" for predicate in predicates),
                    "family_relation_count": family_total,
                    "scan_count": scan_count,
                    "total_relation_count": relation_count,
                    "protocol_use": "primary_inventory_and_future_metric" if split == "validation" else ("train_reference_only" if split == "train" else "deferred_unavailable_or_final_only"),
                }
            )
    return rows, summary


def validate_inputs(
    *,
    claim_summary: dict[str, Any],
    claim_errors: list[dict[str, Any]],
    claim_rows: list[dict[str, str]],
    family_rows: list[dict[str, str]],
    blocked_rows: list[dict[str, str]],
    gap_rows: list[dict[str, str]],
    split_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if claim_summary.get("status") != EXPECTED_CLAIM_STATUS:
        errors.append({"error_type": "unexpected_claim_status", "actual": claim_summary.get("status")})
    if claim_summary.get("next_todo") != EXPECTED_CLAIM_NEXT:
        errors.append({"error_type": "unexpected_claim_next_todo", "actual": claim_summary.get("next_todo")})
    if claim_summary.get("validation_errors") != 0:
        errors.append({"error_type": "claim_summary_validation_errors", "actual": claim_summary.get("validation_errors")})
    if claim_errors:
        errors.append({"error_type": "claim_validation_error_rows_present", "rows": len(claim_errors)})

    boundary = claim_summary.get("boundary", {})
    if boundary.get("c_e_claim_enabled") is not True:
        errors.append({"error_type": "c_e_claim_not_enabled", "actual": boundary.get("c_e_claim_enabled")})
    for key in ["official_validation_usage", "official_test_usage", "paper_metric_produced", "p_rel_claim_enabled", "p_obs_claim_enabled"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "claim_boundary_not_false", "key": key, "actual": boundary.get(key)})

    if len(claim_rows) < 3:
        errors.append({"error_type": "claim_boundary_rows_missing", "rows": len(claim_rows)})
    family_status = {row.get("route_family"): row.get("status") for row in family_rows}
    expected = {
        "relative_horizontal": "claim_supporting",
        "relative_vertical": "claim_supporting",
        "size_relative": "claim_supporting",
        "support_contact": "partial",
    }
    for family, status in expected.items():
        if family_status.get(family) != status:
            errors.append({"error_type": "unexpected_family_claim_status", "family": family, "actual": family_status.get(family)})
    if not any("official" in row.get("blocked_claim", "").lower() for row in blocked_rows):
        errors.append({"error_type": "official_metric_block_not_recorded"})
    if not any(row.get("next_need") == "official_validation_test_protocol" for row in gap_rows):
        errors.append({"error_type": "official_protocol_gap_not_recorded"})

    validation_rows = [row for row in split_rows if row["split"] == "validation"]
    if not validation_rows or not all(row["split_file_exists"] for row in validation_rows):
        errors.append({"error_type": "validation_split_file_missing"})
    if not any(row["split"] == "test" and not row["split_file_exists"] for row in split_rows):
        errors.append({"error_type": "expected_local_test_absence_not_recorded"})
    return errors


def official_protocol_steps() -> list[dict[str, Any]]:
    return [
        {
            "step": "O1",
            "status": "completed_by_this_stage",
            "name": "claim_boundary_lock",
            "purpose": "Prevent internal grouped metrics from being promoted as paper metrics.",
            "output": "allowed/blocked claim boundary and promotion gaps.",
        },
        {
            "step": "O2",
            "status": "next",
            "name": "official_source_inventory",
            "purpose": "Count official validation availability for GT relations, object geometry, and optional VL-SAT/Open3DSG source candidates.",
            "output": "official source inventory with family/predicate capacity and missing-source caveats.",
        },
        {
            "step": "O3",
            "status": "pending",
            "name": "official_candidate_materialization_protocol",
            "purpose": "Freeze GT/counterfactual candidate construction and source-prediction candidate construction before metrics.",
            "output": "model-safe view, hidden manifest, and blocked-field contract.",
        },
        {
            "step": "O4",
            "status": "pending",
            "name": "official_metric_freeze",
            "purpose": "Freeze metrics, baselines, controls, family scope, and paper wording before running evaluation.",
            "output": "metric-freeze artifact; no tuning from validation after this point.",
        },
        {
            "step": "O5",
            "status": "pending",
            "name": "official_validation_eval",
            "purpose": "Run Docker evaluation on official validation candidate rows.",
            "output": "family/predicate metrics, controls, leakage audit, and caveats.",
        },
        {
            "step": "O6",
            "status": "conditional",
            "name": "official_test_eval",
            "purpose": "Use only if a public/accessible official test split with labels or an accepted evaluation server exists.",
            "output": "single frozen final test report; no method change after test.",
        },
        {
            "step": "O7",
            "status": "pending",
            "name": "paper_promotion_review",
            "purpose": "Decide whether H002 remains hypothesis evidence, appendix evidence, or becomes a paper claim.",
            "output": "paper-promotion decision and table wording.",
        },
    ]


def source_candidate_contract() -> list[dict[str, Any]]:
    return [
        {
            "source_route": "GT_counterfactual_mechanism",
            "priority": "primary",
            "split_policy": "official_validation_first",
            "candidate_definition": "Use official GT positive relations and predeclared predicate/object-pair counterfactuals for the same promoted families.",
            "target": "C_e compatibility discrimination",
            "uses_Z_e": "false",
            "paper_role_if_pass": "mechanism evidence for predicate-geometry compatibility on official validation.",
        },
        {
            "source_route": "VL-SAT_source_candidates",
            "priority": "secondary_bridge",
            "split_policy": "official_validation_after_inventory",
            "candidate_definition": "Use source prediction rows keyed by scan/object/predicate if reusable validation outputs exist.",
            "target": "source-candidate reliability/reranking bridge",
            "uses_Z_e": "diagnostic_only_unless_p_rel_protocol",
            "paper_role_if_pass": "bridge from compatibility mechanism to source relation output reliability.",
        },
        {
            "source_route": "Open3DSG_source_candidates",
            "priority": "secondary_bridge",
            "split_policy": "official_validation_after_inventory",
            "candidate_definition": "Use source prediction rows keyed by scan/object/predicate if reusable validation outputs exist.",
            "target": "open-vocabulary source-candidate reliability/reranking bridge",
            "uses_Z_e": "diagnostic_only_unless_p_rel_protocol",
            "paper_role_if_pass": "second-source bridge; must disclose recovery/filtering provenance if reused.",
        },
        {
            "source_route": "official_test",
            "priority": "deferred",
            "split_policy": "test_only_after_full_freeze_if_available",
            "candidate_definition": "No local test relation label file is assumed by this plan.",
            "target": "final frozen evaluation only",
            "uses_Z_e": "same_as_frozen_validation_protocol",
            "paper_role_if_pass": "final held-out confirmation only if accessible.",
        },
    ]


def metric_contract() -> list[dict[str, Any]]:
    return [
        {
            "metric_group": "C_e_mechanism",
            "primary_metrics": "AUROC; AUPRC; balanced_accuracy; macro_F1",
            "unit": "family and predicate",
            "required_baselines": "T_e_only; G_e_only; T_plus_G_concat",
            "required_controls": "wrong_T; shuffled_G; split_leakage_audit",
            "promotion_rule": "Claim-supporting only if family-level M4 beats all baselines and controls collapse.",
        },
        {
            "metric_group": "source_bridge_optional",
            "primary_metrics": "Recall@K or relation retrieval metric; invalid/violation rate; compatibility-risk tradeoff",
            "unit": "source, family, K",
            "required_baselines": "source_score; geometry_only; source_plus_geometry_concat_or_product_if_defined",
            "required_controls": "wrong_pair_geometry; shuffled_geometry; family-stratified reporting",
            "promotion_rule": "Only after source inventory and metric-freeze; not required for current C_e mechanism claim.",
        },
        {
            "metric_group": "calibration_selective_optional",
            "primary_metrics": "ECE; Brier; NLL; coverage-risk curve; abstain accuracy",
            "unit": "family and source",
            "required_baselines": "uncalibrated; semantic_only; geometry_only",
            "required_controls": "OOD or low-coverage rows if available",
            "promotion_rule": "Only if p_rel/p_obs claims are re-enabled by a separate protocol.",
        },
    ]


def baseline_control_contract() -> list[dict[str, Any]]:
    return [
        {
            "view_id": "M1_T_semantic_only",
            "role": "baseline",
            "allowed_inputs": "T_e only",
            "blocked_inputs": "G_e; Z_e; Q_e; construction labels",
        },
        {
            "view_id": "M2_G_geometry_only",
            "role": "baseline",
            "allowed_inputs": "G_e only",
            "blocked_inputs": "predicate text except route-independent feature selection; source score; construction labels",
        },
        {
            "view_id": "M3_T_plus_G_concat",
            "role": "baseline",
            "allowed_inputs": "T_e and G_e concatenation without interaction terms",
            "blocked_inputs": "Z_e; Q_e; construction labels",
        },
        {
            "view_id": "M4_TxG_compatibility",
            "role": "primary_C_e",
            "allowed_inputs": "T_e and G_e with predicate-geometry compatibility features",
            "blocked_inputs": "Z_e; Q_e; source rank/score; target construction labels",
        },
        {
            "view_id": "C1_wrong_T_control",
            "role": "control",
            "allowed_inputs": "M4 with wrong predicate/text control",
            "blocked_inputs": "real target labels or source confidence",
        },
        {
            "view_id": "C2_shuffled_G_control",
            "role": "control",
            "allowed_inputs": "M4 with shuffled geometry control",
            "blocked_inputs": "matched true geometry",
        },
    ]


def family_eval_scope(family_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in family_rows:
        family = row.get("route_family", "")
        status = row.get("status", "")
        rows.append(
            {
                "route_family": family,
                "predicates": row.get("predicates", ""),
                "current_internal_status": status,
                "official_validation_role": "primary_C_e_mechanism" if status == "claim_supporting" else "partial_challenging_diagnostic",
                "include_in_primary_table_if_pass": str(status == "claim_supporting"),
                "include_in_failure_taxonomy": str(status != "claim_supporting"),
                "current_heldout_M4_auroc": row.get("heldout_M4_auroc", ""),
                "claim_boundary": row.get("paper_wording", ""),
            }
        )
    return rows


def promotion_gates() -> list[dict[str, Any]]:
    return [
        {
            "gate": "validation_inventory_pass",
            "required": "official validation relation/object/geometry capacity counted for each promoted family",
            "blocks_if_fail": "do not run official metrics",
        },
        {
            "gate": "candidate_protocol_freeze",
            "required": "positive/counterfactual/source-candidate construction is frozen before metric computation",
            "blocks_if_fail": "metric-dependent target redesign",
        },
        {
            "gate": "schema_leakage_zero",
            "required": "model-safe view has zero construction/proxy/label leakage",
            "blocks_if_fail": "learned metric invalid",
        },
        {
            "gate": "control_collapse",
            "required": "wrong-T and shuffled-G controls are reported and weaker than M4",
            "blocks_if_fail": "compatibility claim invalid",
        },
        {
            "gate": "family_boundary_reporting",
            "required": "family and predicate metrics reported; aggregate-only reporting forbidden",
            "blocks_if_fail": "overbroad claim risk",
        },
        {
            "gate": "test_freeze_policy",
            "required": "test split is not touched unless validation protocol, code, metrics, and wording are frozen",
            "blocks_if_fail": "test contamination risk",
        },
    ]


def write_report(
    path: Path,
    *,
    summary: dict[str, Any],
    split_rows: list[dict[str, Any]],
    steps: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    metric_rows: list[dict[str, Any]],
    gate_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 Official Validation/Test Protocol Plan",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Decision",
        "",
        "The next H002 stage should not run a new model immediately. It should first inventory official validation sources and freeze the official candidate/metric protocol.",
        "",
        "Policy:",
        "",
        "- Use official validation first.",
        "- Do not use test unless a public/accessible official test target exists and every protocol decision is frozen.",
        "- Current internal grouped metrics remain hypothesis-stage evidence only.",
        "",
        "## Local Split Inventory",
        "",
        "| Split | Family | Count | Predicate counts | Protocol use |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for row in split_rows:
        lines.append(
            f"| {row['split']} | `{row['route_family']}` | {row['family_relation_count']} | {row['predicate_counts']} | {row['protocol_use']} |"
        )
    lines.extend(
        [
            "",
            "## Protocol Steps",
            "",
            "| Step | Status | Name | Purpose |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in steps:
        lines.append(f"| `{row['step']}` | {row['status']} | {row['name']} | {row['purpose']} |")
    lines.extend(
        [
            "",
            "## Source Candidate Routes",
            "",
            "| Route | Priority | Split policy | Target |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in source_rows:
        lines.append(f"| `{row['source_route']}` | {row['priority']} | {row['split_policy']} | {row['target']} |")
    lines.extend(
        [
            "",
            "## Metric Contract",
            "",
            "| Metric group | Primary metrics | Unit | Required controls |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in metric_rows:
        lines.append(f"| `{row['metric_group']}` | {row['primary_metrics']} | {row['unit']} | {row['required_controls']} |")
    lines.extend(
        [
            "",
            "## Promotion Gates",
            "",
        ]
    )
    for row in gate_rows:
        lines.append(f"- `{row['gate']}`: {row['required']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- official validation metric 생성 없음; split inventory만 수행.",
            "- official test 사용 없음.",
            "- paper-level result 생성 없음.",
            "- `C_e` official protocol만 planning; `p_rel` / `p_obs`는 optional future protocol.",
            "- H001 artifact 수정 없음.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    claim_summary = read_json(args.claim_dir / "summary.json")
    claim_errors = read_jsonl(args.claim_dir / "validation_errors.jsonl")
    claim_rows = read_csv(args.claim_dir / "claim_boundary.csv")
    family_rows = read_csv(args.claim_dir / "family_claim_roles.csv")
    blocked_rows = read_csv(args.claim_dir / "blocked_claims.csv")
    gap_rows = read_csv(args.claim_dir / "promotion_gaps.csv")
    split_rows, split_summary = split_inventory(args.subset_dir)

    validation_errors = validate_inputs(
        claim_summary=claim_summary,
        claim_errors=claim_errors,
        claim_rows=claim_rows,
        family_rows=family_rows,
        blocked_rows=blocked_rows,
        gap_rows=gap_rows,
        split_rows=split_rows,
    )

    steps = official_protocol_steps()
    source_rows = source_candidate_contract()
    metric_rows = metric_contract()
    baseline_rows = baseline_control_contract()
    family_scope_rows = family_eval_scope(family_rows)
    gate_rows = promotion_gates()

    status = STATUS_ERRORS if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": status,
        "selected_path": SELECTED_PATH if not validation_errors else "fix_official_protocol_plan_inputs",
        "next_todo": NEXT_TODO if not validation_errors else "fix_official_validation_test_protocol_plan_inputs",
        "validation_errors": len(validation_errors),
        "input_artifacts": {
            "claim_summary": rel_path(args.claim_dir / "summary.json"),
            "claim_boundary": rel_path(args.claim_dir / "claim_boundary.csv"),
            "family_claim_roles": rel_path(args.claim_dir / "family_claim_roles.csv"),
            "blocked_claims": rel_path(args.claim_dir / "blocked_claims.csv"),
            "promotion_gaps": rel_path(args.claim_dir / "promotion_gaps.csv"),
            "3dssg_subset_dir": rel_path(args.subset_dir),
        },
        "split_summary": split_summary,
        "boundary": {
            "official_validation_inventory_counted": True,
            "official_validation_metric_produced": False,
            "official_test_usage": False,
            "paper_metric_produced": False,
            "test_split_file_observed": bool(split_summary.get("test", {}).get("exists")),
            "validation_tuning_allowed": False,
            "p_rel_claim_enabled": False,
            "p_obs_claim_enabled": False,
            "h001_artifacts_modified": False,
        },
        "selected_policy": {
            "primary_next_step": "official_source_inventory",
            "primary_split": "3DSSG_subset official validation",
            "test_policy": "defer unless official test labels/eval server are available after freeze",
            "primary_candidate_route": "GT_counterfactual_mechanism",
            "secondary_candidate_routes": ["VL-SAT_source_candidates", "Open3DSG_source_candidates"],
        },
        "output_artifacts": {
            "official_protocol_steps": rel_path(args.output_dir / "official_protocol_steps.csv"),
            "official_split_inventory": rel_path(args.output_dir / "official_split_inventory.csv"),
            "source_candidate_contract": rel_path(args.output_dir / "source_candidate_contract.csv"),
            "family_eval_scope": rel_path(args.output_dir / "family_eval_scope.csv"),
            "metric_contract": rel_path(args.output_dir / "metric_contract.csv"),
            "baseline_control_contract": rel_path(args.output_dir / "baseline_control_contract.csv"),
            "promotion_gates": rel_path(args.output_dir / "promotion_gates.csv"),
            "next_runner_contract": rel_path(args.output_dir / "next_runner_contract.json"),
            "report": rel_path(args.output_dir / "report.md"),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "next_contract.json", {"next_todo": summary["next_todo"], "selected_path": summary["selected_path"]})
    write_json(args.output_dir / "next_runner_contract.json", {
        "next_todo": summary["next_todo"],
        "runner_purpose": "Inventory official validation/test source availability before materializing any official metric rows.",
        "must_check": [
            "3DSSG_subset validation relation capacity for promoted predicates",
            "object/geometry join availability for validation scans",
            "VL-SAT validation source candidate availability",
            "Open3DSG validation source candidate availability",
            "absence or availability of official test labels/evaluation server",
        ],
        "must_not_do": [
            "train or tune on validation metrics",
            "touch official test before freeze",
            "promote current internal candidate-pool metrics to paper results",
            "enable p_rel/p_obs claims",
        ],
    })
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "official_protocol_steps.csv", steps)
    write_csv(args.output_dir / "official_split_inventory.csv", split_rows)
    write_csv(args.output_dir / "source_candidate_contract.csv", source_rows)
    write_csv(args.output_dir / "family_eval_scope.csv", family_scope_rows)
    write_csv(args.output_dir / "metric_contract.csv", metric_rows)
    write_csv(args.output_dir / "baseline_control_contract.csv", baseline_rows)
    write_csv(args.output_dir / "promotion_gates.csv", gate_rows)
    write_report(
        args.output_dir / "report.md",
        summary=summary,
        split_rows=split_rows,
        steps=steps,
        source_rows=source_rows,
        metric_rows=metric_rows,
        gate_rows=gate_rows,
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if validation_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
