#!/usr/bin/env python3
"""Plan positive-anchor mining for the independent H002 attachment target."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

REPAIR_DIR = H2_ROOT / "artifacts/attachment_independent_target_repair_plan_v1"
V20_CAPACITY_DIR = (
    H2_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/rga/"
    / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan"
)
V23_BLOCKER_DIR = (
    H2_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/rga/"
    / "reliability_target_v23_hanging_on_positive_anchor_blocker_synthesis"
)
OUT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_mining_plan_v1"

SCHEMA_VERSION = "h002_attachment_independent_positive_anchor_mining_plan_v1"
EXPECTED_REPAIR_STATUS = "h002_attachment_independent_target_repair_plan_v1_ready"
EXPECTED_REPAIR_NEXT = "attachment_independent_positive_anchor_mining_plan_v1"
EXPECTED_REPAIR_ROUTE = "new_positive_anchor_mining_with_packet_materialization"
STATUS_READY = "h002_attachment_independent_positive_anchor_mining_plan_v1_ready"
STATUS_ERROR = "h002_attachment_independent_positive_anchor_mining_plan_v1_errors"
NEXT_TODO = "attachment_independent_positive_anchor_candidate_mining_v1"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fields.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def summarize_prior_capacity(repair_summary: dict[str, Any], v20_summary: dict[str, Any] | None, v23_summary: dict[str, Any] | None) -> dict[str, Any]:
    capacity = repair_summary.get("capacity", {})
    current = capacity.get("current_200", {})
    matched = capacity.get("all_v20_matched_298", {})
    full = capacity.get("full_candidate_400_visible_rule", {})
    v20_counts = (v20_summary or {}).get("counts", {})
    v20_contrast = (v20_summary or {}).get("contrast_capacity", {})
    v23_blocker = (v23_summary or {}).get("blocker_synthesis", {})
    return {
        "current_200_primary_binary": {
            "accept_positive": current.get("accept_positive"),
            "reject_negative": current.get("reject_negative"),
            "mixed_visible_pair_groups": current.get("mixed_visible_pair_groups"),
            "mixed_predicate_visible_pair_groups": current.get("mixed_predicate_visible_pair_groups"),
        },
        "all_v20_matched_298": {
            "accept_positive": matched.get("accept_positive"),
            "reject_negative": matched.get("reject_negative"),
            "mixed_visible_pair_groups": matched.get("mixed_visible_pair_groups"),
            "mixed_predicate_visible_pair_groups": matched.get("mixed_predicate_visible_pair_groups"),
        },
        "full_candidate_400_visible_rule": {
            "accept_positive": full.get("accept_positive"),
            "reject_negative": full.get("reject_negative"),
            "mixed_visible_pair_groups": full.get("mixed_visible_pair_groups"),
            "mixed_predicate_visible_pair_groups": full.get("mixed_predicate_visible_pair_groups"),
        },
        "v20_full_train_proxy_capacity": {
            "attachment_rows": v20_counts.get("attachment_rows"),
            "primary_positive_anchor_proxy": v20_counts.get("role_counts", {}).get("primary_positive_anchor_proxy"),
            "primary_hard_negative_proxy": v20_counts.get("role_counts", {}).get("primary_hard_negative_proxy"),
            "attached_to_positive_proxy": v20_counts.get("predicate_role_counts", {}).get(
                "attached to|primary_positive_anchor_proxy"
            ),
            "hanging_on_positive_proxy": v20_counts.get("predicate_role_counts", {}).get(
                "hanging on|primary_positive_anchor_proxy"
            ),
            "object_family_mixed_groups": v20_contrast.get("object_family_summary", {}).get("mixed_groups"),
            "exact_endpoint_pair_mixed_groups": v20_contrast.get("exact_endpoint_pair_summary", {}).get("mixed_groups"),
        },
        "v23_hanging_on_blocker": {
            "root_cause": v23_blocker.get("root_cause"),
            "short_explanation": v23_blocker.get("short_explanation"),
            "selected_spec_mixed_groups": v23_blocker.get("capacity_facts", {}).get("selected_spec_mixed_groups"),
            "strict_geometry_mixed_groups": v23_blocker.get("capacity_facts", {}).get("strict_geometry_mixed_groups"),
        },
    }


def build_query_specs() -> list[dict[str, Any]]:
    return [
        {
            "query_id": "Q1_hanging_on_positive_anchor",
            "predicate": "hanging on",
            "row_role": "primary_positive_anchor_candidate",
            "requested_rows": 120,
            "minimum_audit_accept": 40,
            "target_reviewer_label": "accept_reliable",
            "subject_families": "curtain,towel,bag,backpack,clothes,jacket,blinds,picture,decoration,plant,object",
            "object_anchor_families": "wall,door,doorframe,window,blinds,curtain,rack,cabinet,shelf,ceiling",
            "geometry_pre_filter": "near_or_contact_or_vertical_attachment_plausible; not floor_support_only",
            "packet_requirement": "pair_context_sheet + subject/object crops when available + mesh/contact sheet",
            "hard_control_keys": "predicate, endpoint_family_pair, rank_band, coverage_tier, scan_cap",
            "notes": "Primary positive anchor route. The reviewer-visible evidence must support real hanging or mounted attachment, not merely semantic plausibility.",
        },
        {
            "query_id": "Q2_hanging_on_hard_negative",
            "predicate": "hanging on",
            "row_role": "matched_hard_negative_candidate",
            "requested_rows": 120,
            "minimum_audit_reject": 60,
            "target_reviewer_label": "reject_unreliable",
            "subject_families": "same_as_Q1_when_possible",
            "object_anchor_families": "same_as_Q1_when_possible",
            "geometry_pre_filter": "far_separated_or_no_visible_attachment_or_floor_support_confound",
            "packet_requirement": "same packet standard as Q1",
            "hard_control_keys": "match Q1 by endpoint_family_pair, rank_band, coverage_tier, scan_cap",
            "notes": "Hard negatives must be plausible under label semantics but unsupported by visible/mesh geometry.",
        },
        {
            "query_id": "Q3_attached_to_structural_positive_anchor",
            "predicate": "attached to",
            "row_role": "primary_positive_anchor_candidate_if_capacity_passes",
            "requested_rows": 120,
            "minimum_audit_accept": 30,
            "target_reviewer_label": "accept_reliable",
            "subject_families": "door,doorframe,window,frame,picture,cabinet,shelf,rack,radiator,mirror,monitor,tv,light,heater",
            "object_anchor_families": "wall,doorframe,ceiling,cabinet,shelf,stand",
            "geometry_pre_filter": "near_or_contact_or_structural_mount_plausible; exclude loose-near-only rows",
            "packet_requirement": "pair context and mesh/contact evidence required before label fill",
            "hard_control_keys": "predicate, endpoint_family_pair, rank_band, coverage_tier, scan_cap",
            "notes": "Attached-to is primary only if enough independently accepted positives survive audit. Otherwise keep as diagnostic.",
        },
        {
            "query_id": "Q4_attached_to_hard_negative",
            "predicate": "attached to",
            "row_role": "matched_hard_negative_candidate",
            "requested_rows": 120,
            "minimum_audit_reject": 60,
            "target_reviewer_label": "reject_unreliable",
            "subject_families": "same_as_Q3_when_possible",
            "object_anchor_families": "same_as_Q3_when_possible",
            "geometry_pre_filter": "same semantic families but no visible mount/contact; far or floor/support confound",
            "packet_requirement": "same packet standard as Q3",
            "hard_control_keys": "match Q3 by endpoint_family_pair, rank_band, coverage_tier, scan_cap",
            "notes": "Avoid making all negatives come from different object labels than positives.",
        },
        {
            "query_id": "Q5_connected_to_diagnostic_optional",
            "predicate": "connected to",
            "row_role": "diagnostic_only_unless_functional_evidence_exists",
            "requested_rows": 80,
            "minimum_audit_accept": 0,
            "target_reviewer_label": "abstain_or_diagnostic",
            "subject_families": "device,pipe,tube,cable-like,fixture-like rows if present",
            "object_anchor_families": "socket,wall,device,pipe,stand,cabinet",
            "geometry_pre_filter": "near_or_overlap is insufficient; require visible functional connection if promoted",
            "packet_requirement": "visual/mesh packet plus explicit connection evidence",
            "hard_control_keys": "diagnostic only; never used for primary p_rel until accept/reject target exists",
            "notes": "Connected-to remains diagnostic because current artifacts cannot verify functional connection reliably.",
        },
    ]


def build_contract() -> dict[str, Any]:
    return {
        "selected_route": "train_only_positive_anchor_candidate_mining_then_packet_materialization",
        "target_rows_before_audit": 560,
        "primary_requested_rows_before_audit": 480,
        "diagnostic_requested_rows_before_audit": 80,
        "post_audit_min_primary_binary_rows": 160,
        "post_audit_min_accept_positive": 60,
        "post_audit_min_reject_negative": 60,
        "post_audit_min_hanging_on_accept": 40,
        "post_audit_min_attached_to_accept_for_primary": 30,
        "post_audit_min_mixed_endpoint_family_groups": 10,
        "post_audit_min_mixed_visible_pair_groups": 3,
        "max_single_visible_pair_share": 0.10,
        "max_single_scan_share": 0.04,
        "group_split_key": "scan_id",
        "attached_to_fallback": "diagnostic_if_accept_positive_below_30",
        "hanging_on_fallback": "primary_single_predicate_smoke_if_hanging_accept_ge_40_and_controls_pass",
        "connected_to_policy": "diagnostic_only_until_functional_or_visual_connection_gt_exists",
        "posterior_smoke_gate": "rerun label_fill, ingestion, and target_independence_audit first",
    }


def build_field_boundary() -> dict[str, Any]:
    return {
        "visible_to_labeler": [
            "subject_label",
            "predicate_label",
            "object_label",
            "scan-local object ids only if needed for packet navigation",
            "subject/object/pair visual crops",
            "mesh/contact/context packet",
            "coverage or packet completeness note",
        ],
        "hidden_from_labeler": [
            "source score",
            "source rank",
            "rank band",
            "source id",
            "proxy role",
            "cell id",
            "machine hint",
            "geometry status bucket",
            "prior v20 label",
            "current visible-rule label",
            "existing GT match status",
        ],
        "allowed_model_inputs_after_audit": [
            "T_e semantic content",
            "Z_e source confidence, separated from C_e",
            "G_e predicate-independent numeric or tokenized geometry evidence",
            "Q_e evidence quality and observability",
        ],
        "forbidden_for_c_e": [
            "Z_e source confidence",
            "source rank",
            "proxy role",
            "cell id",
            "machine hint",
            "prior labels",
        ],
    }


def build_next_runner_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "expected_outputs": {
            "candidate_rows": "candidate_rows.jsonl",
            "hidden_manifest": "hidden_manifest.jsonl",
            "visible_review_template": "visible_review_template.csv",
            "asset_request_manifest": "asset_request_manifest.jsonl",
            "mining_summary": "summary.json",
            "validation_errors": "validation_errors.jsonl",
        },
        "minimum_validation_checks": [
            "all rows are train split",
            "no validation/test scan ids",
            "query_id is present for every row",
            "source/proxy/rank fields appear only in hidden manifest",
            "candidate rows have materializable subject/object/pair packet request ids",
            "per-query quotas are reported before label fill",
            "scan and visible-pair caps are enforced before packet generation",
        ],
        "blocked_actions": [
            "posterior training",
            "paper metric reporting",
            "relaxing abstain to accept",
            "using connected-to rows as primary",
            "using source score or proxy role for visible label fill",
        ],
    }


def validate_inputs(repair_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if repair_summary.get("status") != EXPECTED_REPAIR_STATUS:
        errors.append({"error_type": "unexpected_repair_status", "actual": repair_summary.get("status")})
    if repair_summary.get("next_todo") != EXPECTED_REPAIR_NEXT:
        errors.append({"error_type": "unexpected_repair_next_todo", "actual": repair_summary.get("next_todo")})
    if repair_summary.get("selected_route") != EXPECTED_REPAIR_ROUTE:
        errors.append({"error_type": "unexpected_repair_route", "actual": repair_summary.get("selected_route")})
    if repair_summary.get("validation_errors") != 0:
        errors.append({"error_type": "repair_validation_errors_present", "actual": repair_summary.get("validation_errors")})
    capacity = repair_summary.get("capacity", {}).get("current_200", {})
    if capacity.get("accept_positive", 0) >= 60:
        errors.append(
            {
                "error_type": "repair_plan_no_longer_positive_sparse",
                "actual_accept_positive": capacity.get("accept_positive"),
            }
        )
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    prior = summary["prior_capacity"]
    contract = summary["mining_contract"]
    lines = [
        "# H002 Attachment Independent Positive Anchor Mining Plan V1",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_route = {summary['selected_route']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Prior Capacity",
        "",
        "```text",
        "current_200 = "
        f"{prior['current_200_primary_binary']['accept_positive']} positive / "
        f"{prior['current_200_primary_binary']['reject_negative']} negative",
        "all_v20_matched_298 = "
        f"{prior['all_v20_matched_298']['accept_positive']} positive / "
        f"{prior['all_v20_matched_298']['reject_negative']} negative",
        "full_candidate_400_visible_rule = "
        f"{prior['full_candidate_400_visible_rule']['accept_positive']} positive / "
        f"{prior['full_candidate_400_visible_rule']['reject_negative']} negative",
        "full_candidate_400 mixed_predicate_visible_pair_groups = "
        f"{prior['full_candidate_400_visible_rule']['mixed_predicate_visible_pair_groups']}",
        "```",
        "",
        "## Decision",
        "",
        "The next step should mine new positive-anchor candidates, not train a posterior. "
        "The current target has too few independently accepted positives and too little controlled contrast.",
        "",
        "Selected route:",
        "",
        f"`{summary['selected_route']}`",
        "",
        "## Mining Contract",
        "",
        "```text",
        f"target_rows_before_audit = {contract['target_rows_before_audit']}",
        f"primary_requested_rows_before_audit = {contract['primary_requested_rows_before_audit']}",
        f"post_audit_min_primary_binary_rows = {contract['post_audit_min_primary_binary_rows']}",
        f"post_audit_min_accept_positive = {contract['post_audit_min_accept_positive']}",
        f"post_audit_min_reject_negative = {contract['post_audit_min_reject_negative']}",
        f"post_audit_min_mixed_endpoint_family_groups = {contract['post_audit_min_mixed_endpoint_family_groups']}",
        "posterior_smoke_gate = rerun label_fill, ingestion, and target_independence_audit first",
        "```",
        "",
        "## Query Specs",
        "",
        "| Query | Predicate | Role | Requested | Gate |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for spec in summary["query_specs"]:
        gate = spec.get("minimum_audit_accept") or spec.get("minimum_audit_reject") or 0
        lines.append(
            f"| `{spec['query_id']}` | `{spec['predicate']}` | `{spec['row_role']}` | "
            f"{spec['requested_rows']} | {gate} |"
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- train split only;",
            "- source score, rank, proxy role, cell id, machine hint, prior labels, and GT-match status remain hidden from label fill;",
            "- `Z_e` must not enter `C_e`; compatibility uses `T_e` and `G_e` only;",
            "- `connected to` remains diagnostic unless functional connection evidence is independently available;",
            "- `attached to` is primary only if it reaches the post-audit positive gate;",
            "- multi-view/mesh evidence is audit evidence at this stage, not deployable model input.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    repair_summary = read_json(REPAIR_DIR / "summary.json")
    v20_summary = read_json(V20_CAPACITY_DIR / "summary.json") if (V20_CAPACITY_DIR / "summary.json").exists() else None
    v23_summary = read_json(V23_BLOCKER_DIR / "summary.json") if (V23_BLOCKER_DIR / "summary.json").exists() else None

    validation_errors = validate_inputs(repair_summary)
    query_specs = build_query_specs()
    mining_contract = build_contract()
    field_boundary = build_field_boundary()
    next_runner_contract = build_next_runner_contract()

    status = STATUS_ERROR if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "selected_route": mining_contract["selected_route"],
        "decision": "mine_new_independent_accept_positive_attachment_anchors_before_posterior_smoke",
        "next_todo": NEXT_TODO if not validation_errors else EXPECTED_REPAIR_NEXT,
        "validation_errors": len(validation_errors),
        "prior_capacity": summarize_prior_capacity(repair_summary, v20_summary, v23_summary),
        "query_specs": query_specs,
        "mining_contract": mining_contract,
        "field_boundary": field_boundary,
        "next_runner_contract": next_runner_contract,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "materializes_new_candidates": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "multi_view_or_mesh_as_audit_evidence": True,
        },
        "input_paths": {
            "repair_summary": rel_path(REPAIR_DIR / "summary.json"),
            "v20_capacity_summary": rel_path(V20_CAPACITY_DIR / "summary.json") if v20_summary else None,
            "v23_blocker_summary": rel_path(V23_BLOCKER_DIR / "summary.json") if v23_summary else None,
        },
        "output_paths": {
            "summary": rel_path(OUT_DIR / "summary.json"),
            "report": rel_path(OUT_DIR / "report.md"),
            "query_specs": rel_path(OUT_DIR / "query_specs.csv"),
            "mining_protocol": rel_path(OUT_DIR / "mining_protocol.json"),
            "next_runner_contract": rel_path(OUT_DIR / "next_runner_contract.json"),
            "validation_errors": rel_path(OUT_DIR / "validation_errors.jsonl"),
        },
    }

    write_json(OUT_DIR / "summary.json", summary)
    write_csv(OUT_DIR / "query_specs.csv", query_specs)
    write_json(
        OUT_DIR / "mining_protocol.json",
        {
            "schema_version": SCHEMA_VERSION,
            "selected_route": summary["selected_route"],
            "mining_contract": mining_contract,
            "field_boundary": field_boundary,
            "query_specs": query_specs,
        },
    )
    write_json(OUT_DIR / "next_runner_contract.json", next_runner_contract)
    write_jsonl(OUT_DIR / "validation_errors.jsonl", validation_errors)
    write_report(OUT_DIR / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"selected_route={summary['selected_route']}")
    print(f"next={summary['next_todo']}")
    print(f"target_rows_before_audit={mining_contract['target_rows_before_audit']}")
    print(f"post_audit_min_accept_positive={mining_contract['post_audit_min_accept_positive']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
