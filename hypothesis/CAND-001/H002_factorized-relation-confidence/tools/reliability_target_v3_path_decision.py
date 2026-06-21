#!/usr/bin/env python3
"""Decide the H002 path after reliability target v3 independence audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v3_target_independence_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_path_decision_codex_proxy_user_requested"

RELIABILITY_TARGET = "relation_reliability_v3_binary_target"
GEOMETRY_TARGET = "geometry_support_v3_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v3_binary_target"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
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


def risk_extract(original: dict[str, Any], risk_key: str) -> list[dict[str, Any]]:
    rows = []
    for item in original.get(risk_key, [])[:3]:
        rows.append(
            {
                "group_key": item.get("group_key"),
                "majority_rule_accuracy": item.get("majority_rule_accuracy"),
                "normalized_mutual_information": item.get("normalized_mutual_information"),
                "positive_rate_range": item.get("positive_rate_range"),
                "large_group_high_purity": item.get("large_group_high_purity"),
            }
        )
    return rows


def build_element_failure_matrix(audit: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = audit["target_decisions"]
    relation = decisions[RELIABILITY_TARGET]["original"]
    geometry = decisions[GEOMETRY_TARGET]["original"]
    usefulness = decisions[USEFULNESS_TARGET]["original"]
    return [
        {
            "element": "relation_reliability_v3_binary_target",
            "observed": f"{relation['rows']} rows, {relation['positive']} positive, {relation['negative']} negative",
            "problem": "positive mass exists, but no strict or diagnostic controlled slice exists",
            "why_it_blocks_posterior": "A posterior can still learn endpoint/object/construction shortcuts rather than semantic-geometry reliability.",
            "required_fix": "Build an object/endpoint-controlled label pool before feature join or posterior smoke.",
        },
        {
            "element": "visible_object_identity",
            "observed": risk_extract(relation, "top_visible_object_identity_risks"),
            "problem": "subject/object labels almost determine the reliability target in the v3 proxy sheet",
            "why_it_blocks_posterior": "Object labels are valid context, but if they explain the target alone, factorized reliability evidence is not isolated.",
            "required_fix": "Sample positive and negative candidates within matched or near-matched subject/object-label strata.",
        },
        {
            "element": "endpoint_pattern",
            "observed": risk_extract(relation, "top_endpoint_pattern_risks"),
            "problem": "endpoint flag pattern remains highly predictive",
            "why_it_blocks_posterior": "Endpoint structure can act as a hidden sampling key rather than deployable reliability evidence.",
            "required_fix": "Use endpoint pattern only as a balancing/control stratum and require both classes within multiple endpoint cells.",
        },
        {
            "element": "construction_metadata",
            "observed": risk_extract(relation, "top_construction_risks"),
            "problem": "rank/queue construction axes still correlate with the target",
            "why_it_blocks_posterior": "Performance can reflect candidate construction instead of evidence-factor combination.",
            "required_fix": "Keep score/rank/queue/expected role hidden from labelers and audit them post-label.",
        },
        {
            "element": "geometry_support_v3_binary_target",
            "observed": f"{geometry['rows']} rows, {geometry['positive']} positive, {geometry['negative']} negative",
            "problem": "geometry support has mass but is not relation reliability",
            "why_it_blocks_posterior": "Using it as the main target collapses H002 into a geometry-only verifier task.",
            "required_fix": "Keep geometry support as an evidence axis and baseline, not the final reliability target.",
        },
        {
            "element": "relation_usefulness_v3_binary_target",
            "observed": f"{usefulness['rows']} rows, {usefulness['positive']} positive, {usefulness['negative']} negative",
            "problem": "usefulness is also object-identity sensitive",
            "why_it_blocks_posterior": "Useful/trivial labels can be learned from structural object categories without checking relation evidence.",
            "required_fix": "Use usefulness as a sub-axis and control object/room-structure labels in sampling.",
        },
        {
            "element": "label_source",
            "observed": audit["boundary"].get("label_source"),
            "problem": "v3 labels are Codex proxy labels, not independent human annotation",
            "why_it_blocks_posterior": "A clean model claim needs target evidence that is not another proxy for the construction heuristic.",
            "required_fix": "After controlled sampling, collect evidence-first independent labels or explicitly keep results as diagnostic only.",
        },
    ]


def build_option_matrix() -> list[dict[str, str]]:
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "No strict or diagnostic controlled relation reliability slice exists.",
        },
        {
            "option": "upgrade_combiner_now",
            "verdict": "reject",
            "reason": "The current blocker is target independence, not combiner capacity.",
        },
        {
            "option": "use_geometry_support_as_main_target",
            "verdict": "reject_for_reliability_claim",
            "reason": "Geometry support is an evidence axis; it is not the same as relation reliability.",
        },
        {
            "option": "collect_more_same_v3_proxy_labels",
            "verdict": "reject",
            "reason": "More rows from the same label/sampling policy will likely preserve object and endpoint shortcuts.",
        },
        {
            "option": "collect_independent_labels_immediately_on_current_160",
            "verdict": "defer",
            "reason": "The current 160-row pool is not object/endpoint controlled enough; relabeling it can repeat the same shortcut.",
        },
        {
            "option": "revise_v3_object_endpoint_controlled_sampling",
            "verdict": "select",
            "reason": "It directly attacks the failure mode: reliability target can be predicted from object and endpoint strata.",
        },
        {
            "option": "freeze_as_rga_diagnostic_only",
            "verdict": "keep_as_fallback",
            "reason": "If controlled sampling still fails, H002 can remain a diagnostic RGA benchmark rather than a posterior method claim.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_now",
            "reason": "Clean target is unavailable; multi-view remains audit evidence only.",
        },
    ]


def build_next_sampling_plan(audit: dict[str, Any]) -> dict[str, Any]:
    counts = audit["input_counts"][RELIABILITY_TARGET]
    return {
        "next_todo": "reliability_target_v3_object_endpoint_controlled_plan",
        "selected_path": "revise_v3_object_endpoint_controlled_sampling",
        "purpose": "Construct a new train-only label pool where relation reliability cannot be predicted by endpoint flag or subject/object labels alone.",
        "keep_v3_axes": True,
        "label_axes": {
            "endpoint_identity_v3": ["both_valid", "subject_invalid", "object_invalid", "pair_invalid", "uncertain"],
            "pair_evaluability_v3": ["evaluable", "partially_evaluable", "not_evaluable", "uncertain"],
            "geometry_support_v3": ["supports_predicate", "contradicts_predicate", "ambiguous", "not_evaluable"],
            "relation_usefulness_v3": ["informative", "trivial_dense_or_room_structure", "ontology_mismatch", "uncertain"],
            "relation_reliability_v3": [
                "reliable",
                "unreliable_geometry",
                "unreliable_trivial",
                "unreliable_ontology",
                "uncertain",
            ],
        },
        "current_relation_target": {
            "rows": counts["rows"],
            "positive": counts["positive"],
            "negative": counts["negative"],
            "positive_rate": counts["positive_rate"],
        },
        "minimum_next_pool": {
            "target_rows": 160,
            "target_positive": 40,
            "target_negative": 40,
            "target_uncertain_or_holdout": 40,
            "reserve_rows": 40,
            "note": "Counts are planning targets; final binary target is derived only after labels and independence audit.",
        },
        "primary_controls": [
            "same or near-matched subject_label/object_label cells must contain both candidate-positive and candidate-negative rows",
            "endpoint_flag_pattern strata must contain both classes where possible",
            "predicate_family and predicate_label must not be single-class proxies",
            "rank_band, queue_kind, sampling_category, expected role, geometry_status, p_geom_valid, source score, and label_match_status stay hidden from labelers",
            "hidden construction metadata is joined only after label lock",
        ],
        "sampling_cells": [
            "subject_label x object_label x predicate_family",
            "object_label x predicate_label",
            "endpoint_flag_pattern x predicate_family",
            "rank_band x predicate_family as post-label audit only",
        ],
        "required_post_label_audit": [
            "hidden provenance risk",
            "endpoint pattern risk",
            "construction risk",
            "visible object identity risk",
            "visible relation surface risk",
            "geometry alignment risk",
            "scan/group leakage risk",
        ],
        "posterior_reopen_gate": [
            "relation reliability binary target has at least 20 positives and 20 negatives",
            "a strict or explicitly defensible diagnostic controlled slice exists",
            "object-label-only and endpoint-only probes do not dominate semantic/geometry evidence",
            "validation/test usage remains false",
        ],
        "multi_view_policy": "audit_label_evidence_only_not_model_input",
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    relation = summary["audit_extract"][RELIABILITY_TARGET]
    geometry = summary["audit_extract"][GEOMETRY_TARGET]
    usefulness = summary["audit_extract"][USEFULNESS_TARGET]
    lines = [
        "# H002 Reliability Target V3 Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage decision.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- H001 artifacts are not modified.",
        "- Multi-view remains audit/label evidence, not model input.",
        "",
        "## Status",
        "",
        f"`{summary['status']}`",
        "",
        "Selected path:",
        "",
        f"`{summary['selected_path']}`",
        "",
        "Decision:",
        "",
        summary["decision"],
        "",
        "## Audit Extract",
        "",
        "| Target | Rows | Pos | Neg | Strict Slice | Diagnostic Slice |",
        "| --- | ---: | ---: | ---: | --- | --- |",
        (
            f"| `{RELIABILITY_TARGET}` | {relation['rows']} | {relation['positive']} | {relation['negative']} | "
            f"`{relation['strict_slice']}` | `{relation['diagnostic_slice']}` |"
        ),
        (
            f"| `{GEOMETRY_TARGET}` | {geometry['rows']} | {geometry['positive']} | {geometry['negative']} | "
            f"`{geometry['strict_slice']}` | `{geometry['diagnostic_slice']}` |"
        ),
        (
            f"| `{USEFULNESS_TARGET}` | {usefulness['rows']} | {usefulness['positive']} | {usefulness['negative']} | "
            f"`{usefulness['strict_slice']}` | `{usefulness['diagnostic_slice']}` |"
        ),
        "",
        "## Element Failure Matrix",
        "",
        "| Element | Problem | Why It Blocks Posterior | Required Fix |",
        "| --- | --- | --- | --- |",
    ]
    for item in summary["element_failure_matrix"]:
        lines.append(
            f"| `{item['element']}` | {item['problem']} | {item['why_it_blocks_posterior']} | {item['required_fix']} |"
        )
    lines.extend(
        [
            "",
            "## Option Matrix",
            "",
            "| Option | Verdict | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for item in summary["option_matrix"]:
        lines.append(f"| `{item['option']}` | `{item['verdict']}` | {item['reason']} |")
    lines.extend(
        [
            "",
            "## Next Sampling Contract",
            "",
            "The next path keeps the v3 axes but changes the sampling and label contract.",
            "The core requirement is to create object/endpoint-controlled rows where both positive and negative labels can exist inside matched or near-matched subject/object strata.",
            "",
            "Primary controls:",
            "",
        ]
    )
    for item in summary["next_sampling_plan"]["primary_controls"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Posterior reopen gate:",
            "",
        ]
    )
    for item in summary["next_sampling_plan"]["posterior_reopen_gate"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Next TODO",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).isoformat()

    audit = read_json(audit_dir / "summary.json")
    decisions = audit["target_decisions"]

    audit_extract: dict[str, Any] = {}
    for target in [RELIABILITY_TARGET, GEOMETRY_TARGET, USEFULNESS_TARGET]:
        original = decisions[target]["original"]
        audit_extract[target] = {
            "rows": original["rows"],
            "positive": original["positive"],
            "negative": original["negative"],
            "positive_rate": original["positive_rate"],
            "strict_slice": decisions[target].get("recommended_strict_slice") or "none",
            "diagnostic_slice": decisions[target].get("recommended_diagnostic_slice") or "none",
            "status": decisions[target]["status"],
            "risk_counts": {
                "hidden": original.get("hidden_provenance_risk_count", 0),
                "endpoint": original.get("endpoint_pattern_risk_count", 0),
                "construction": original.get("construction_risk_count", 0),
                "geometry_alignment": original.get("expected_geometry_alignment_risk_count", 0),
                "object_identity": original.get("visible_object_identity_risk_count", 0),
                "relation_surface": original.get("visible_relation_surface_risk_count", 0),
            },
        }

    element_failure_matrix = build_element_failure_matrix(audit)
    option_matrix = build_option_matrix()
    next_sampling_plan = build_next_sampling_plan(audit)

    summary = {
        "schema_version": "h002_reliability_target_v3_path_decision_summary_v1",
        "created_at": created_at,
        "status": "h002_reliability_target_v3_path_decision_object_endpoint_controlled_sampling_first",
        "selected_path": "revise_v3_object_endpoint_controlled_sampling",
        "decision": (
            "Do not run posterior smoke or upgrade the combiner. Keep v3 multi-axis labels, "
            "but rebuild the next label pool with object/endpoint-controlled sampling because "
            "the current target can be explained by endpoint and subject/object label shortcuts."
        ),
        "posterior_allowed": False,
        "combiner_upgrade_allowed": False,
        "validation_used": False,
        "test_used": False,
        "multi_view_as_model_input": False,
        "next_todo": next_sampling_plan["next_todo"],
        "audit_input": rel_path(audit_dir / "summary.json"),
        "audit_status": audit["status"],
        "audit_decision": audit["decision"],
        "audit_extract": audit_extract,
        "element_failure_matrix": element_failure_matrix,
        "option_matrix": option_matrix,
        "next_sampling_plan": next_sampling_plan,
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "option_matrix": rel_path(output_dir / "option_matrix.json"),
            "element_failure_matrix": rel_path(output_dir / "element_failure_matrix.json"),
            "next_sampling_plan": rel_path(output_dir / "next_sampling_plan.json"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "option_matrix.json", option_matrix)
    write_json(output_dir / "element_failure_matrix.json", element_failure_matrix)
    write_json(output_dir / "next_sampling_plan.json", next_sampling_plan)
    write_report(output_dir / "report.md", summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    print(
        "status={status} selected={selected_path} posterior_allowed={posterior_allowed} "
        "validation_used={validation_used} test_used={test_used} next={next_todo}".format(**summary)
    )


if __name__ == "__main__":
    main()
