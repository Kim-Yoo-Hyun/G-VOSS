#!/usr/bin/env python3
"""Decide the H002 path after object/endpoint v3 target audit."""

from __future__ import annotations

import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_FILL_DIR = RGA_ROOT / "reliability_target_v3_object_endpoint_label_fill_codex_proxy_user_requested"
DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v3_object_endpoint_label_ingestion_codex_proxy_user_requested"
DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v3_object_endpoint_target_independence_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_object_endpoint_path_decision_codex_proxy_user_requested"

RELIABILITY_TARGET = "relation_reliability_v3_binary_target"
GEOMETRY_TARGET = "geometry_support_v3_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v3_binary_target"

MIN_POSTERIOR_PER_CLASS = 20
RECOMMENDED_NEXT_LABEL_ROWS = 160


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fill-dir", type=Path, default=DEFAULT_FILL_DIR)
    parser.add_argument("--ingestion-dir", type=Path, default=DEFAULT_INGESTION_DIR)
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


def needed_rows_at_rate(current_positive: int, current_total: int, target_positive: int) -> dict[str, Any]:
    rate = current_positive / current_total if current_total else 0.0
    additional_positive = max(0, target_positive - current_positive)
    if additional_positive == 0:
        additional_rows: int | str = 0
    elif rate <= 0:
        additional_rows = "inf"
    else:
        additional_rows = math.ceil(additional_positive / rate)
    return {
        "target_positive": target_positive,
        "current_positive": current_positive,
        "current_total": current_total,
        "observed_positive_rate": rate,
        "additional_positive_needed": additional_positive,
        "additional_rows_needed_at_observed_rate": additional_rows,
    }


def target_extract(audit: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for target_name in [RELIABILITY_TARGET, GEOMETRY_TARGET, USEFULNESS_TARGET]:
        decision = audit["target_decisions"][target_name]
        original = decision["original"]
        output[target_name] = {
            "status": decision["status"],
            "rows": original["rows"],
            "positive": original["positive"],
            "negative": original["negative"],
            "positive_rate": original["positive_rate"],
            "positive_sparse": original["positive_sparse"],
            "strict_slice": (decision.get("recommended_strict_slice") or {}).get("slice_name", "none")
            if decision.get("recommended_strict_slice")
            else "none",
            "diagnostic_slice": (decision.get("recommended_diagnostic_slice") or {}).get("slice_name", "none")
            if decision.get("recommended_diagnostic_slice")
            else "none",
            "risk_counts": {
                "hidden": original.get("hidden_provenance_risk_count", 0),
                "endpoint": original.get("endpoint_pattern_risk_count", 0),
                "construction": original.get("construction_risk_count", 0),
                "geometry_alignment": original.get("expected_geometry_alignment_risk_count", 0),
                "object_identity": original.get("visible_object_identity_risk_count", 0),
                "relation_surface": original.get("visible_relation_surface_risk_count", 0),
            },
        }
    return output


def build_option_matrix(rel: dict[str, Any], geom: dict[str, Any], usefulness: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "Main relation reliability target is positive-sparse and no controlled slice exists.",
        },
        {
            "option": "upgrade_combiner_now",
            "verdict": "reject",
            "reason": "The bottleneck is target definition and sampling, not posterior capacity.",
        },
        {
            "option": "use_geometry_support_as_main_target",
            "verdict": "reject_for_reliability_claim",
            "reason": (
                f"Geometry support has {geom['positive']}/{geom['negative']} mass, "
                "but geometry validity is not relation reliability."
            ),
        },
        {
            "option": "relax_reliability_to_geometry_supported",
            "verdict": "reject",
            "reason": "This collapses the H002 distinction among semantic score, geometry validity, and relation reliability.",
        },
        {
            "option": "collect_more_same_object_endpoint_labels",
            "verdict": "reject_as_primary",
            "reason": (
                f"At the observed reliability positive rate {rel['positive_rate']:.4f}, "
                "more same-distribution rows would mostly add trivial negatives."
            ),
        },
        {
            "option": "keep_geometry_support_diagnostic_only",
            "verdict": "keep",
            "reason": "Geometry-support remains useful evidence for RGA decomposition but cannot be the posterior target.",
        },
        {
            "option": "revise_v3_informative_positive_anchor_sampling",
            "verdict": "select",
            "reason": "It directly attacks the observed failure: geometry-supported rows are dominated by trivial room/surface relations.",
        },
        {
            "option": "freeze_h002_as_rga_diagnostic_only",
            "verdict": "fallback",
            "reason": "If informative anchor mining cannot create a controlled reliability target, H002 should stop as a diagnostic framework.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_now",
            "reason": "Clean reliability target is unavailable; multi-view remains audit/label evidence only.",
        },
    ]


def build_failure_matrix(fill: dict[str, Any], audit_extract: dict[str, Any]) -> list[dict[str, Any]]:
    axis = fill["counts"]
    rel = audit_extract[RELIABILITY_TARGET]
    geom = audit_extract[GEOMETRY_TARGET]
    usefulness = audit_extract[USEFULNESS_TARGET]
    return [
        {
            "element": "relation_reliability_target",
            "observed": f"{rel['rows']} rows, {rel['positive']} positive, {rel['negative']} negative",
            "problem": "positive_sparse_main_target",
            "why_it_blocks_posterior": "A posterior can score well by learning the negative-majority target.",
            "required_fix": "Do not run posterior until reliability target has enough positives and a controlled slice.",
        },
        {
            "element": "geometry_support_vs_reliability_gap",
            "observed": {
                "geometry_supports_predicate": axis["geometry_support_v3"].get("supports_predicate", 0),
                "relation_reliable": axis["relation_reliability_v3"].get("reliable", 0),
            },
            "problem": "geometry_support_is_not_reliability",
            "why_it_blocks_posterior": "Replacing reliability with geometry support would turn H002 into a geometry-only verifier.",
            "required_fix": "Keep geometry support as an evidence factor and diagnostic target only.",
        },
        {
            "element": "trivial_relation_dominance",
            "observed": {
                "unreliable_trivial": axis["relation_reliability_v3"].get("unreliable_trivial", 0),
                "trivial_dense_or_room_structure": axis["relation_usefulness_v3"].get(
                    "trivial_dense_or_room_structure", 0
                ),
            },
            "problem": "supported_predicates_are_mostly_trivial",
            "why_it_blocks_posterior": "The target rewards detecting dense room/surface triviality rather than relation reliability.",
            "required_fix": "Mine informative positive anchors and cap room-structure endpoints.",
        },
        {
            "element": "relation_usefulness_target",
            "observed": f"{usefulness['rows']} rows, {usefulness['positive']} positive, {usefulness['negative']} negative",
            "problem": "usefulness_is_also_positive_sparse",
            "why_it_blocks_posterior": "Usefulness cannot currently rescue reliability because it has too few positive informative rows.",
            "required_fix": "Use usefulness as a mining/control axis before deriving a binary posterior target.",
        },
        {
            "element": "geometry_support_target",
            "observed": f"{geom['rows']} rows, {geom['positive']} positive, {geom['negative']} negative",
            "problem": "mass_available_but_not_controlled",
            "why_it_blocks_posterior": "Geometry support has mass but still lacks strict/diagnostic controlled slices.",
            "required_fix": "Report as RGA decomposition evidence, not as a main posterior target.",
        },
        {
            "element": "object_endpoint_control",
            "observed": "object/endpoint-controlled sampling still produced only 8 reliable positives",
            "problem": "object_endpoint_control_is_necessary_but_not_sufficient",
            "why_it_blocks_posterior": "The remaining failure is relation informativeness, not only endpoint/object shortcut.",
            "required_fix": "Retain object/endpoint controls while adding informative-anchor constraints.",
        },
        {
            "element": "label_source",
            "observed": "user-requested Codex proxy labels",
            "problem": "not_independent_human_evidence",
            "why_it_blocks_posterior": "Hypothesis-stage proxy labels can guide design but cannot support paper-level posterior claims.",
            "required_fix": "Keep outputs diagnostic until independent labels or a stronger audit protocol exists.",
        },
    ]


def build_next_plan(rel: dict[str, Any]) -> dict[str, Any]:
    return {
        "next_todo": "reliability_target_v3_informative_anchor_plan",
        "selected_path": "revise_v3_informative_positive_anchor_sampling",
        "purpose": (
            "Construct a train-only label pool that preserves object/endpoint controls while "
            "actively mining non-trivial, informative reliable relation positives."
        ),
        "recommended_rows": RECOMMENDED_NEXT_LABEL_ROWS,
        "recommended_sampling_goal": {
            "informative_reliable_positive": 40,
            "geometry_contradiction_negative": 40,
            "trivial_room_surface_negative": 40,
            "uncertain_or_ontology_negative": 40,
        },
        "positive_mass_projection": {
            "posterior_minimum_per_class": MIN_POSTERIOR_PER_CLASS,
            "same_distribution_projection": needed_rows_at_rate(
                int(rel["positive"]), int(rel["rows"]), MIN_POSTERIOR_PER_CLASS
            ),
        },
        "informative_anchor_candidates": [
            "support_contact with non-room object support such as table, desk, shelf, cabinet, chair, or sofa",
            "support_contact where subject is a movable object and object is not floor, wall, or ceiling",
            "relative_vertical with object-level endpoints and meaningful vertical separation",
            "relation rows whose geometry supports the predicate and whose relation_usefulness is likely informative",
        ],
        "negative_anchor_candidates": [
            "geometry contradiction for the same predicate family",
            "trivial dense room/surface relations kept as explicit negatives but capped",
            "ontology mismatch or endpoint identity issue as separate negative/uncertain cases",
            "hard negatives inside matched subject/object or endpoint strata",
        ],
        "sampling_controls": [
            "keep subject/object label and endpoint pattern as balancing controls",
            "cap floor, wall, ceiling, room-surface, and same-label structural endpoints",
            "require support_contact and relative_vertical to each contribute positives if possible",
            "keep source score, rank, p_geom_valid, geometry_status, label_match_status, and queue hidden from labelers",
            "join hidden construction metadata only after label lock",
            "keep multi-view as audit evidence only",
        ],
        "posterior_reopen_gate": [
            "relation reliability binary target has at least 20 positives and 20 negatives",
            "strict or explicitly defensible diagnostic controlled slice exists",
            "trivial_dense_or_room_structure does not dominate the negative target alone",
            "object-label-only and endpoint-only probes do not explain the target",
            "validation/test usage remains false",
        ],
        "fallback_stop_rule": (
            "If informative-anchor mining cannot create a controlled reliability target, freeze H002 as "
            "an RGA diagnostic/decomposition framework instead of forcing a posterior method claim."
        ),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    rel = summary["audit_extract"][RELIABILITY_TARGET]
    geom = summary["audit_extract"][GEOMETRY_TARGET]
    usefulness = summary["audit_extract"][USEFULNESS_TARGET]
    counts = summary["label_axis_counts"]
    lines = [
        "# H002 Reliability Target V3 Object/Endpoint Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage path decision.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- H001 artifacts are not modified.",
        "- Multi-view remains audit/label evidence, not model input.",
        "- Current labels are user-requested Codex proxy labels, not independent human evidence.",
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
        "## Target Extract",
        "",
        "| Target | Status | Rows | Pos | Neg | Strict Slice | Diagnostic Slice |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
        (
            f"| `{RELIABILITY_TARGET}` | `{rel['status']}` | {rel['rows']} | {rel['positive']} | {rel['negative']} | "
            f"`{rel['strict_slice']}` | `{rel['diagnostic_slice']}` |"
        ),
        (
            f"| `{GEOMETRY_TARGET}` | `{geom['status']}` | {geom['rows']} | {geom['positive']} | {geom['negative']} | "
            f"`{geom['strict_slice']}` | `{geom['diagnostic_slice']}` |"
        ),
        (
            f"| `{USEFULNESS_TARGET}` | `{usefulness['status']}` | {usefulness['rows']} | {usefulness['positive']} | "
            f"{usefulness['negative']} | `{usefulness['strict_slice']}` | `{usefulness['diagnostic_slice']}` |"
        ),
        "",
        "## Key Label Axes",
        "",
        f"- `geometry_support_v3.supports_predicate`: `{counts['geometry_support_v3'].get('supports_predicate', 0)}`",
        f"- `relation_reliability_v3.reliable`: `{counts['relation_reliability_v3'].get('reliable', 0)}`",
        f"- `relation_reliability_v3.unreliable_trivial`: `{counts['relation_reliability_v3'].get('unreliable_trivial', 0)}`",
        f"- `relation_usefulness_v3.trivial_dense_or_room_structure`: `{counts['relation_usefulness_v3'].get('trivial_dense_or_room_structure', 0)}`",
        "",
        "## Option Matrix",
        "",
        "| Option | Verdict | Reason |",
        "| --- | --- | --- |",
    ]
    for item in summary["option_matrix"]:
        lines.append(f"| `{item['option']}` | `{item['verdict']}` | {item['reason']} |")
    lines.extend(
        [
            "",
            "## Failure Matrix",
            "",
            "| Element | Problem | Required Fix |",
            "| --- | --- | --- |",
        ]
    )
    for item in summary["target_failure_matrix"]:
        lines.append(f"| `{item['element']}` | `{item['problem']}` | {item['required_fix']} |")
    lines.extend(
        [
            "",
            "## Next Plan",
            "",
            f"Next TODO: `{summary['next_todo']}`",
            "",
            "Sampling goal:",
            "",
        ]
    )
    for key, value in summary["next_plan"]["recommended_sampling_goal"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "Posterior reopen gate:", ""])
    for item in summary["next_plan"]["posterior_reopen_gate"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "Fallback stop rule:",
            "",
            summary["next_plan"]["fallback_stop_rule"],
            "",
            "## Output Artifacts",
            "",
            "```text",
        ]
    )
    for output_path in summary["output_paths"].values():
        lines.append(output_path)
    lines.extend(["```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    fill_dir = as_abs(args.fill_dir)
    ingestion_dir = as_abs(args.ingestion_dir)
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fill = read_json(fill_dir / "summary.json")
    ingestion = read_json(ingestion_dir / "summary.json")
    audit = read_json(audit_dir / "summary.json")
    created_at = datetime.now(timezone.utc).isoformat()

    extract = target_extract(audit)
    rel = extract[RELIABILITY_TARGET]
    geom = extract[GEOMETRY_TARGET]
    usefulness = extract[USEFULNESS_TARGET]
    option_matrix = build_option_matrix(rel, geom, usefulness)
    failure_matrix = build_failure_matrix(fill, extract)
    next_plan = build_next_plan(rel)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "target_failure_matrix": output_dir / "target_failure_matrix.json",
        "next_plan": output_dir / "next_plan.json",
    }

    summary = {
        "schema_version": "h002_reliability_target_v3_object_endpoint_path_decision_summary_v1",
        "status": "h002_reliability_target_v3_object_endpoint_path_decision_informative_anchor_sampling",
        "created_at": created_at,
        "selected_path": next_plan["selected_path"],
        "decision": (
            "Do not run posterior smoke, upgrade the combiner, or use geometry-support as the main target. "
            "The object/endpoint-controlled attempt shows that geometry-supported rows are dominated by "
            "trivial room/surface relations, so the next step is informative positive-anchor sampling with "
            "object/endpoint controls retained."
        ),
        "input_paths": {
            "fill_summary": rel_path(fill_dir / "summary.json"),
            "ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "target_independence_audit_summary": rel_path(audit_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "posterior_trained": False,
            "posterior_smoke_allowed": False,
            "combiner_upgrade_allowed_now": False,
            "geometry_support_as_main_target": False,
            "multi_view_as_model_input": False,
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
        },
        "fill_status": fill["status"],
        "ingestion_status": ingestion["status"],
        "audit_status": audit["status"],
        "audit_decision": audit["decision"],
        "label_axis_counts": fill["counts"],
        "audit_extract": extract,
        "option_matrix": option_matrix,
        "target_failure_matrix": failure_matrix,
        "next_plan": next_plan,
        "next_todo": next_plan["next_todo"],
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["option_matrix"], {"options": option_matrix})
    write_json(output_paths["target_failure_matrix"], {"failures": failure_matrix})
    write_json(output_paths["next_plan"], next_plan)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    rel = summary["audit_extract"][RELIABILITY_TARGET]
    counts = summary["label_axis_counts"]
    print(
        "status={status} selected={selected_path} rel={rows}/{pos}/{neg} "
        "supports={supports} trivial={trivial} posterior_allowed={posterior_allowed} "
        "validation_used={validation_used} test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            selected_path=summary["selected_path"],
            rows=rel["rows"],
            pos=rel["positive"],
            neg=rel["negative"],
            supports=counts["geometry_support_v3"].get("supports_predicate", 0),
            trivial=counts["relation_reliability_v3"].get("unreliable_trivial", 0),
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
