#!/usr/bin/env python3
"""Define the H002 v6 shortcut-controlled sampling plan."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_PATH_DECISION_DIR = RGA_ROOT / "reliability_target_v6_uncertainty_aware_path_decision_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v6_shortcut_controlled_sampling_plan_codex_proxy_user_requested"

NEXT_TODO = "reliability_target_v6_shortcut_controlled_candidate_mining"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path-decision-dir", type=Path, default=DEFAULT_PATH_DECISION_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    with as_abs(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def validate_upstream(path_decision: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected_status = "h002_reliability_target_v6_uncertainty_aware_path_decision_select_shortcut_controlled_sampling_plan"
    if path_decision.get("status") != expected_status:
        errors.append({"error_type": "unexpected_path_decision_status", "expected": expected_status, "actual": path_decision.get("status")})
    if path_decision.get("selected_path") != "v6_shortcut_controlled_sampling_plan":
        errors.append({"error_type": "unexpected_selected_path", "actual": path_decision.get("selected_path")})
    if path_decision.get("next_todo") != "reliability_target_v6_shortcut_controlled_sampling_plan":
        errors.append({"error_type": "unexpected_path_decision_next_todo", "actual": path_decision.get("next_todo")})
    if path_decision.get("posterior_smoke_allowed") is not False:
        errors.append({"error_type": "posterior_already_allowed", "actual": path_decision.get("posterior_smoke_allowed")})
    for key in ["validation_usage", "test_usage", "trains_new_posterior", "fills_new_labels", "multi_view_as_model_input", "paper_evidence_allowed", "h001_artifacts_modified"]:
        if path_decision.get("boundary", {}).get(key) is not False:
            errors.append({"error_type": "path_decision_boundary_violation", "key": key, "actual": path_decision.get("boundary", {}).get(key)})
    return errors


def target_schema() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_shortcut_controlled_target_schema_v1",
        "primary_target": "relation_reliability_state_v6",
        "primary_states": {
            "accept_reliable": "edge is reliable enough for downstream graph use under available evidence",
            "reject_unreliable": "edge should not be trusted as a relation under available evidence",
            "abstain_uncertain": "available evidence is insufficient, ambiguous, or endpoint/predicate confidence is not enough",
        },
        "auxiliary_axes": {
            "geometry_support_state_v6": ["supports", "contradicts", "ambiguous", "not_evaluable"],
            "relation_usefulness_state_v6": ["useful_nontrivial", "trivial_or_redundant", "not_a_relation", "uncertain"],
            "endpoint_identity_v6": ["clear", "uncertain", "wrong_endpoint", "not_evaluable"],
            "pair_evaluability_v6": ["evaluable", "evidence_limited", "predicate_ambiguous", "segmentation_limited", "not_evaluable"],
        },
        "not_target_labels": [
            "candidate_bucket",
            "expected_target_proxy",
            "semantic_band",
            "geometry_band",
            "object_family_cell",
            "cell/pair id",
        ],
        "target_policy": (
            "Candidate buckets may guide pre-label coverage, but the reviewer-assigned reliability state is the only "
            "primary target. Candidate buckets are audit-only and forbidden as posterior inputs."
        ),
    }


def evidence_band_policy() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_evidence_band_policy_v1",
        "semantic_bands": {
            "semantic_high": "semantic_rank <= 100 or source-normalized score in the high band for the predicate",
            "semantic_mid": "100 < semantic_rank <= 500 or middle source-normalized score band",
            "semantic_low": "semantic_rank > 500 or source-normalized low band among retained source candidates",
        },
        "geometry_bands": {
            "geometry_high": "p_geom_valid >= 0.85 or relation-family residual is clearly satisfied",
            "geometry_mid_or_ambiguous": "0.35 < p_geom_valid < 0.85 or coverage/residual is ambiguous",
            "geometry_low": "p_geom_valid <= 0.35 or relation-family residual is clearly contradicted",
            "coverage_limited": "geometry/view/mesh evidence is missing or too weak to evaluate",
        },
        "relation_family_scope": {
            "primary": ["support_contact", "relative_vertical"],
            "deferred": {
                "attachment_deferred": "future extension after base S/G/C/U target independence passes",
                "proximity": "defer for v6 base because dense relation noise and trivial adjacency can dominate labels",
            },
        },
        "deployable_posterior_inputs_after_label_gate": [
            "continuous semantic score/rank evidence",
            "continuous geometry evidence such as p_geom_valid and residuals",
            "coverage/missingness/uncertainty proxies",
            "predicate family conditioning with group-aware evaluation",
        ],
        "forbidden_posterior_inputs": [
            "candidate_bucket",
            "semantic_band or geometry_band as categorical shortcuts",
            "target labels or auxiliary review fields",
            "cell/pair/object-family ids",
            "subject/object class labels as main factors",
            "audit packet paths",
            "multi-view content before explicit future promotion",
        ],
    }


def bucket_specs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    definitions = [
        {
            "bucket": "B1_semantic_high_geometry_high",
            "semantic_band": "semantic_high",
            "geometry_band": "geometry_high",
            "diagnostic_role": "semantic_geometry_agreement_positive_coverage",
            "expected_label_distribution": "accept_reliable enriched, but not forced",
        },
        {
            "bucket": "B2_semantic_high_geometry_low",
            "semantic_band": "semantic_high",
            "geometry_band": "geometry_low",
            "diagnostic_role": "semantic_overconfidence_conflict",
            "expected_label_distribution": "reject_unreliable or abstain_uncertain enriched, but not forced",
        },
        {
            "bucket": "B3_semantic_low_geometry_high",
            "semantic_band": "semantic_low",
            "geometry_band": "geometry_high",
            "diagnostic_role": "semantic_underconfidence_geometry_support",
            "expected_label_distribution": "accept_reliable or abstain_uncertain enriched, but not forced",
        },
        {
            "bucket": "B4_ambiguous_or_coverage_limited",
            "semantic_band": "semantic_mid",
            "geometry_band": "geometry_mid_or_ambiguous_or_coverage_limited",
            "diagnostic_role": "abstention_boundary",
            "expected_label_distribution": "abstain_uncertain enriched, but not forced",
        },
    ]
    for family in ["support_contact", "relative_vertical"]:
        for item in definitions:
            row = dict(item)
            row.update(
                {
                    "predicate_family": family,
                    "target_candidate_rows": 30,
                    "minimum_candidate_rows": 20,
                    "labeler_visible": False,
                    "posterior_input_allowed": False,
                    "post_label_audit_group": True,
                }
            )
            rows.append(row)
    return rows


def cap_policy() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_sampling_cap_policy_v1",
        "target_queue_rows": 240,
        "target_rows_per_family": 120,
        "target_rows_per_family_bucket": 30,
        "caps": {
            "max_rows_per_scan": 6,
            "max_rows_per_scene_context": 4,
            "max_rows_per_subject_object_id_pair": 1,
            "max_rows_per_subject_object_label_pair": 6,
            "max_rows_per_subject_label": 18,
            "max_rows_per_object_label": 18,
            "max_rows_per_object_family_cell": 12,
            "max_rows_per_subject_object_family_cell": 8,
            "max_rows_per_predicate_label_bucket": 40,
        },
        "deduplication_keys": [
            "scan_id + scene_context_id + subject_id + object_id + predicate_label",
            "prediction_id",
        ],
        "selection_tiebreakers": [
            "higher packet readiness",
            "larger distance from semantic/geometry band boundary",
            "lower scan/object-label concentration",
            "stable hash of prediction_id",
        ],
        "forbidden_selection_tiebreakers": [
            "known v5/v6 labels",
            "expected target state after human review",
            "validation/test performance",
        ],
    }


def label_surface_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_label_surface_contract_v1",
        "visible_fields": [
            "blind_review_id",
            "review_scope",
            "scan_id",
            "scene_context_id",
            "subject_id",
            "subject_label",
            "predicate_label",
            "predicate_family",
            "object_id",
            "object_label",
            "family_question",
            "supporting_cues",
            "contradicting_cues",
            "evidence_packet_status",
            "multiview_packet",
            "pointcloud_or_mesh_packet",
            "contact_or_context_sheet",
            "reviewer_id",
            "review_round",
            "endpoint_identity_v6",
            "pair_evaluability_v6",
            "geometry_support_v6",
            "relation_usefulness_v6",
            "relation_reliability_state_v6",
            "primary_reason_v6",
            "uncertainty_reason_v6",
            "label_notes_v6",
        ],
        "hidden_manifest_only_fields": [
            "prediction_id",
            "candidate_bucket",
            "semantic_band",
            "geometry_band",
            "semantic_score_raw",
            "semantic_score_norm",
            "semantic_rank",
            "p_geom_valid",
            "geometry_residuals",
            "coverage_bucket",
            "object_family_cell",
            "subject_object_family_cell",
            "source_queue",
            "rank_band",
            "label_match_status",
            "h001_verification_status",
            "packet_source",
        ],
        "labeler_visible_forbidden_tokens": [
            "candidate_bucket",
            "expected_target",
            "semantic_score",
            "semantic_rank",
            "p_geom",
            "geometry_status",
            "rank_band",
            "source_queue",
            "cell_contrast",
            "object_family_cell",
            "label_match",
            "h001_verification",
            "gt_label",
        ],
        "multi_view_policy": (
            "Multi-view packet paths may be visible for label audit, but multi-view content remains forbidden as "
            "posterior input until base target independence passes."
        ),
    }


def audit_gate_plan() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_shortcut_controlled_audit_gate_plan_v1",
        "pre_label_gates": [
            "candidate queue uses train-only rows",
            "target queue attempts 240 rows with 30 rows per family/bucket cell",
            "subject/object/scan concentration caps are enforced",
            "label surface contains no hidden sampling or model-score fields",
            "asset-needed rows are explicitly marked for packet generation/readiness",
        ],
        "post_label_gates": [
            "all primary states meet at least 20 rows; preferred >=40 rows per state",
            "no blocking shortcut risk in cell/pair/object-family/object-label groups",
            "nontrivial controlled slice exists after grouping",
            "candidate bucket is not used as a posterior feature",
            "semantic/geometry/coverage/uncertainty features are deployable and not review labels",
            "validation/test usage remains false",
        ],
        "blocking_groups": [
            "scan_id",
            "scene_context_id",
            "subject_object_id_pair",
            "subject_object_label_pair",
            "subject_label",
            "object_label",
            "object_family_cell",
            "subject_object_family_cell",
            "predicate_family",
            "predicate_label",
            "candidate_bucket",
            "semantic_band",
            "geometry_band",
            "coverage_bucket",
            "packet_source",
        ],
        "risk_thresholds": {
            "normalized_mutual_information": 0.20,
            "majority_excess_over_baseline": 0.10,
            "max_state_rate_range": 0.70,
            "large_group_rows": 10,
            "large_group_purity": 0.95,
        },
        "posterior_reopen_conditions": [
            "primary state mass passes",
            "blocking shortcut groups pass",
            "controlled slice exists",
            "posterior input contract is label-free and deployable",
        ],
    }


def candidate_mining_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_reliability_target_v6_candidate_mining_contract_v1",
        "next_todo": NEXT_TODO,
        "input_sources": [
            "Open3DSG train-only full RGA rows",
            "deployable semantic score/rank evidence",
            "deployable p_geom_valid or relation-family geometry residual evidence",
            "existing audit packet availability metadata",
        ],
        "steps": [
            "filter to primary relation families support_contact and relative_vertical",
            "derive semantic and geometry evidence bands from deployable evidence only",
            "assign audit-only candidate buckets from semantic/geometry bands",
            "apply scan, physical-pair, object-label, and object-family caps",
            "select up to 240 candidates using stable deterministic tie-breaking",
            "write a clean label sheet and hidden post-label manifest separately",
            "write asset request rows for candidates without complete packets",
        ],
        "outputs_required_from_candidate_mining": [
            "v6_shortcut_controlled_label_sheet.tsv",
            "v6_shortcut_controlled_manifest_post_label_only.jsonl",
            "selected_candidates_internal.jsonl",
            "candidate_bucket_summary.csv",
            "cap_audit_summary.csv",
            "asset_request_plan.jsonl",
            "label_schema.json",
        ],
        "must_not_do": [
            "fill labels",
            "train posterior",
            "use validation/test rows",
            "expose candidate bucket or semantic/geometry scores to the label surface",
            "modify H001 artifacts",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    cap = summary["cap_policy"]
    lines = [
        "# H002 Reliability Target V6 Shortcut-Controlled Sampling Plan",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Split: Open3DSG train-only.",
        "- Labels: not filled.",
        "- Posterior model: not trained.",
        "- Validation/test rows: not used.",
        "- H001 artifacts: not modified.",
        "- Multi-view remains label-audit evidence only, not posterior input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "## Sampling Target",
        "",
        f"- Target queue rows: `{cap['target_queue_rows']}`",
        f"- Target rows per family: `{cap['target_rows_per_family']}`",
        f"- Target rows per family/bucket: `{cap['target_rows_per_family_bucket']}`",
        "- Primary families: `support_contact`, `relative_vertical`",
        "- Candidate buckets: semantic/geometry agreement, high-semantic/low-geometry, low-semantic/high-geometry, and ambiguous/coverage-limited.",
        "",
        "## Bucket Plan",
        "",
        "| Bucket | Family | Target Rows | Diagnostic Role |",
        "| --- | --- | ---: | --- |",
    ]
    for row in summary["bucket_specs"]:
        lines.append(
            f"| `{row['bucket']}` | `{row['predicate_family']}` | {row['target_candidate_rows']} | {row['diagnostic_role']} |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            summary["decision"],
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    path_decision_dir = as_abs(args.path_decision_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    path_decision = read_json(path_decision_dir / "summary.json")
    errors = validate_upstream(path_decision)
    buckets = bucket_specs()
    target = target_schema()
    bands = evidence_band_policy()
    caps = cap_policy()
    label_contract = label_surface_contract()
    gates = audit_gate_plan()
    mining = candidate_mining_contract()

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "sampling_plan": output_dir / "sampling_plan.json",
        "bucket_specs_json": output_dir / "bucket_specs.json",
        "bucket_specs_csv": output_dir / "bucket_specs.csv",
        "target_schema": output_dir / "target_schema.json",
        "evidence_band_policy": output_dir / "evidence_band_policy.json",
        "cap_policy": output_dir / "cap_policy.json",
        "label_surface_contract": output_dir / "label_surface_contract.json",
        "audit_gate_plan": output_dir / "audit_gate_plan.json",
        "candidate_mining_contract": output_dir / "candidate_mining_contract.json",
        "validation_errors": output_dir / "validation_errors.json",
    }

    status = "h002_reliability_target_v6_shortcut_controlled_sampling_plan_ready_for_candidate_mining"
    if errors:
        status = "h002_reliability_target_v6_shortcut_controlled_sampling_plan_validation_failed"

    decision = (
        "Use a train-only 240-row shortcut-controlled v6 candidate queue plan with equal coverage across "
        "support_contact and relative_vertical, and across four deployable semantic/geometry evidence buckets. "
        "The plan keeps the v6 reliability schema but forbids current v5 cell/pair construction, object-label "
        "shortcuts, candidate buckets, scores, and review labels as posterior inputs. The next step is candidate "
        "mining, not label fill or posterior smoke."
    )
    sampling_plan = {
        "schema_version": "h002_reliability_target_v6_shortcut_controlled_sampling_plan_v1",
        "selected_plan": "train_only_240_row_sg_bucket_balanced_queue",
        "target_schema": target,
        "evidence_band_policy": bands,
        "bucket_specs": buckets,
        "cap_policy": caps,
        "label_surface_contract": label_contract,
        "audit_gate_plan": gates,
        "candidate_mining_contract": mining,
        "path_decision_trace": {
            "upstream_status": path_decision.get("status"),
            "upstream_selected_path": path_decision.get("selected_path"),
            "upstream_blocking_risk_count": path_decision.get("audit_snapshot", {}).get("risk_summary", {}).get("blocking_risk_count"),
            "upstream_state_counts": path_decision.get("audit_snapshot", {}).get("class_mass", {}).get("state_counts"),
        },
    }

    summary = {
        "schema_version": "h002_reliability_target_v6_shortcut_controlled_sampling_plan_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "decision": decision,
        "next_todo": NEXT_TODO if not errors else "fix_v6_sampling_plan_validation_errors",
        "input_paths": {
            "path_decision_summary": rel_path(path_decision_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "fills_new_labels": False,
            "posterior_smoke_allowed": False,
            "multi_view_as_model_input": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
        },
        "sampling_plan": sampling_plan,
        "bucket_specs": buckets,
        "cap_policy": caps,
        "audit_gate_plan": gates,
        "candidate_mining_contract": mining,
        "validation_error_count": len(errors),
        "posterior_smoke_allowed": False,
    }

    write_json(output_paths["summary"], summary)
    write_report(output_paths["report"], summary)
    write_json(output_paths["sampling_plan"], sampling_plan)
    write_json(output_paths["bucket_specs_json"], buckets)
    write_csv(output_paths["bucket_specs_csv"], buckets)
    write_json(output_paths["target_schema"], target)
    write_json(output_paths["evidence_band_policy"], bands)
    write_json(output_paths["cap_policy"], caps)
    write_json(output_paths["label_surface_contract"], label_contract)
    write_json(output_paths["audit_gate_plan"], gates)
    write_json(output_paths["candidate_mining_contract"], mining)
    write_json(output_paths["validation_errors"], errors)

    return summary


def main() -> None:
    summary = run(parse_args())
    cap = summary["cap_policy"]
    print(f"status={summary['status']}")
    print("selected_plan=train_only_240_row_sg_bucket_balanced_queue")
    print(f"target_rows={cap['target_queue_rows']}")
    print(f"family_rows={cap['target_rows_per_family']}")
    print(f"family_bucket_rows={cap['target_rows_per_family_bucket']}")
    print(f"bucket_cells={len(summary['bucket_specs'])}")
    print(f"posterior_allowed={summary['posterior_smoke_allowed']}")
    print(f"validation_errors={summary['validation_error_count']}")
    print(f"next={summary['next_todo']}")


if __name__ == "__main__":
    main()
