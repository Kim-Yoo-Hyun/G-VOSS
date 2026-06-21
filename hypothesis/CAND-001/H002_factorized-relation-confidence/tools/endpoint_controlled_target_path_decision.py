#!/usr/bin/env python3
"""Decide the next H002 path after endpoint-controlled target audit."""

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

DEFAULT_INGESTION_DIR = RGA_ROOT / "endpoint_controlled_label_ingestion_codex_proxy_user_requested"
DEFAULT_AUDIT_DIR = RGA_ROOT / "endpoint_controlled_target_independence_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "endpoint_controlled_target_path_decision_codex_proxy_user_requested"

GEOMETRY_TARGET = "geometry_validity_endpoint_controlled_target"
RELIABILITY_TARGET = "relation_reliability_endpoint_controlled_target"

MIN_SMOKE_POSITIVES = 10
MIN_POSTERIOR_PER_CLASS = 20
RECOMMENDED_NEXT_LABEL_ROWS = 160


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def needed_rows_at_observed_rate(current_pos: int, current_total: int, target_pos: int) -> dict[str, Any]:
    if current_pos >= target_pos:
        return {
            "target_positive_count": target_pos,
            "additional_positive_needed": 0,
            "observed_positive_rate": current_pos / current_total if current_total else 0.0,
            "additional_rows_needed_at_observed_rate": 0,
        }
    positive_rate = current_pos / current_total if current_total else 0.0
    needed_pos = target_pos - current_pos
    additional_rows = math.inf if positive_rate <= 0 else math.ceil(needed_pos / positive_rate)
    return {
        "target_positive_count": target_pos,
        "additional_positive_needed": needed_pos,
        "observed_positive_rate": positive_rate,
        "additional_rows_needed_at_observed_rate": additional_rows,
    }


def build_failure_matrix(ingestion: dict[str, Any], audit: dict[str, Any]) -> list[dict[str, Any]]:
    counts = ingestion["counts"]["targets"]
    audit_counts = audit["input_counts"]
    rel_counts = counts[RELIABILITY_TARGET]
    geom_counts = counts[GEOMETRY_TARGET]
    return [
        {
            "element": "relation_reliability_binary_target",
            "observed": f"{rel_counts['positive']}/{rel_counts['negative']} positive/negative over {rel_counts['rows']} binary rows",
            "problem": "positive_sparse_target",
            "why_it_blocks_posterior": "A negative-majority baseline already reaches 0.9412; model performance would not show factorized reliability learning.",
            "required_fix": "Revise target definition and sampling to secure enough reliable-positive anchors before posterior smoke.",
        },
        {
            "element": "geometry_validity_target",
            "observed": f"{geom_counts['positive']}/{geom_counts['negative']} positive/negative over {geom_counts['rows']} binary rows",
            "problem": "diagnostic_mass_but_not_reliability_target",
            "why_it_blocks_posterior": "Geometry validity is not the same as relation reliability; using it alone collapses H002 into a geometry-only verifier target.",
            "required_fix": "Keep geometry validity as an evidence axis and baseline, but do not use it as the main relation reliability target.",
        },
        {
            "element": "endpoint_control_axis",
            "observed": "endpoint_flag_pattern_hidden remains a high-risk audit key",
            "problem": "sampling_axis_still_predictive",
            "why_it_blocks_posterior": "The sampling/control key can explain target outcomes even if it is not a deployable model input.",
            "required_fix": "Use endpoint as a balancing/control stratum only; require positive and negative labels inside multiple endpoint patterns.",
        },
        {
            "element": "construction_axis",
            "observed": "proposed_audit_role_hidden, rank_band_hidden, queue_kind_hidden remain correlated",
            "problem": "construction_shortcut_risk",
            "why_it_blocks_posterior": "A model could appear useful because the target was constructed from the same role/rank/queue logic.",
            "required_fix": "Build the next label pool from target-agnostic positive-anchor strata and audit construction axes post-label.",
        },
        {
            "element": "uncertain_and_trivial_labels",
            "observed": ingestion["axis_counts"],
            "problem": "binary_reliability_collapses_multiple_failure_reasons",
            "why_it_blocks_posterior": "Uncertain, trivial-dense, ontology-mismatch, and true reliable states are collapsed into an imbalanced binary target.",
            "required_fix": "Use a v3 multi-axis label schema before deriving a binary posterior target.",
        },
        {
            "element": "audit_target_counts",
            "observed": {
                "strict_ready_targets": audit.get("strict_ready_targets", []),
                "diagnostic_only_targets": audit.get("diagnostic_only_targets", []),
                "blocked_targets": audit.get("blocked_targets", []),
                "relation_majority_baseline": audit_counts[RELIABILITY_TARGET]["majority_baseline"],
            },
            "problem": "no_controlled_slice",
            "why_it_blocks_posterior": "Neither strict nor diagnostic controlled relation-reliability slice exists.",
            "required_fix": "Do not run posterior smoke until target independence audit clears a usable slice.",
        },
    ]


def build_option_matrix(rel_counts: dict[str, Any], geom_counts: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "Relation reliability is 2/32 and has no strict or diagnostic controlled slice.",
            "risk": "Would validate a negative-majority target rather than factorized reliability.",
        },
        {
            "option": "upgrade_combiner_now",
            "verdict": "reject",
            "reason": "The bottleneck is target construction and positive coverage, not combiner capacity.",
            "risk": "A stronger combiner can overfit construction artifacts more convincingly.",
        },
        {
            "option": "use_geometry_validity_as_main_target",
            "verdict": "reject_for_reliability_claim",
            "reason": f"Geometry has {geom_counts['positive']}/{geom_counts['negative']} mass, but geometry validity is not relation reliability.",
            "risk": "Would change H002 into a geometry-only verifier task.",
        },
        {
            "option": "collect_more_same_endpoint_controlled_labels",
            "verdict": "defer",
            "reason": "At the observed 0.0588 positive rate, reaching 20 positives would require hundreds of same-distribution rows.",
            "risk": "Likely repeats the positive-sparse failure unless sampling is redesigned.",
        },
        {
            "option": "relax_reliability_to_geometry_supported",
            "verdict": "reject_as_shortcut",
            "reason": "This would make relation reliability almost the same as geometry validity.",
            "risk": "It removes the H002 distinction between geometry validity and edge reliability.",
        },
        {
            "option": "revise_reliability_target_v3_and_positive_anchor_sampling",
            "verdict": "select",
            "reason": "Directly addresses the failure: binary reliability collapsed into sparse positives and mixed failure reasons.",
            "risk": "Requires another train-only label/sampling pass before posterior smoke.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_now",
            "reason": "Clean target is not available; multi-view should remain audit evidence until target independence is fixed.",
            "risk": "Feature gain and target shortcut would be inseparable.",
        },
    ]


def build_v3_plan(rel_counts: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_path": "revise_reliability_target_v3_and_positive_anchor_sampling",
        "next_todo": "reliability_target_v3_positive_anchor_plan",
        "goal": "Create a v3 target/label plan that separates geometry support, relation informativeness, ontology fit, uncertainty, and final reliability before deriving any binary posterior target.",
        "target_schema_v3": {
            "geometry_support": ["supports_predicate", "contradicts_predicate", "ambiguous", "not_evaluable"],
            "relation_usefulness": ["informative", "trivial_dense_or_room_structure", "ontology_mismatch", "uncertain"],
            "relation_reliability": ["reliable", "unreliable_geometry", "unreliable_trivial", "unreliable_ontology", "uncertain"],
            "binary_derivation_rule": "Use binary reliability only after each axis has enough label mass and target-independence audit passes.",
        },
        "positive_anchor_requirements": {
            "minimum_binary_positive_for_smoke": MIN_SMOKE_POSITIVES,
            "minimum_binary_positive_for_posterior": MIN_POSTERIOR_PER_CLASS,
            "current_relation_positive": rel_counts["positive"],
            "current_relation_negative": rel_counts["negative"],
            "current_relation_positive_rate": rel_counts["positive_rate"],
            "needed_at_current_rate_for_smoke": needed_rows_at_observed_rate(
                rel_counts["positive"], rel_counts["rows"], MIN_SMOKE_POSITIVES
            ),
            "needed_at_current_rate_for_posterior": needed_rows_at_observed_rate(
                rel_counts["positive"], rel_counts["rows"], MIN_POSTERIOR_PER_CLASS
            ),
            "recommended_next_label_rows": RECOMMENDED_NEXT_LABEL_ROWS,
            "recommended_sampling_goal": {
                "reliable_positive_anchor": 40,
                "geometry_contradiction_negative": 40,
                "trivial_dense_negative": 40,
                "ontology_or_uncertain_negative": 40,
            },
        },
        "sampling_controls": [
            "balance support_contact and relative_vertical, but allow family-specific diagnosis if one family cannot produce reliable positives",
            "balance endpoint flag patterns instead of using endpoint pattern as a target proxy",
            "avoid selecting all positives from one predicate such as lying on",
            "keep source score, rank, p_geom_valid, geometry_status, endpoint pattern, queue, role, and prior labels hidden from labelers",
            "join hidden construction metadata only after label lock for audit",
            "keep multi-view as audit evidence, not model input",
        ],
        "promotion_gate": [
            "validation/test usage remains false",
            "posterior smoke allowed only if relation reliability has at least 20 positives and 20 negatives or a predeclared smaller smoke threshold with caveat",
            "target-independence audit must produce a strict or explicitly defensible controlled slice",
            "geometry-only target may be reported as diagnostic, not as relation reliability posterior evidence",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Endpoint-Controlled Target Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only hypothesis-stage decision.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- H001 artifacts are not modified.",
        "- Multi-view remains audit evidence, not model input.",
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
        "## Key Counts",
        "",
        "| Target | Rows | Pos | Neg | Majority Baseline |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for target, counts in summary["target_counts"].items():
        lines.append(
            f"| `{target}` | {counts['rows']} | {counts['positive']} | {counts['negative']} | {counts['majority_baseline']:.4f} |"
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
            "## Why Positive-Sparse Target Blocks Posterior",
            "",
            "The relation reliability target has only 2 positives and 32 negatives. A model that predicts all rows as negative already reaches 0.9412 accuracy. Therefore posterior smoke would not test semantic/geometry evidence combination.",
            "",
            "This does not mean semantic and geometry are well aligned. It means the current binary reliability target is too imbalanced and collapses too many failure reasons into the negative class.",
            "",
            "## Selected Next Plan",
            "",
            f"Next TODO: `{summary['next_todo']}`",
            "",
            "- revise reliability target v3 as a multi-axis label schema.",
            "- mine positive-anchor candidates instead of adding more same-distribution endpoint labels.",
            "- keep geometry validity as an evidence axis and diagnostic target, not the main reliability target.",
            "- keep posterior smoke blocked until positive mass and target-independence gates pass.",
            "",
            "## Output Artifacts",
            "",
            "```text",
        ]
    )
    for path_value in summary["output_paths"].values():
        lines.append(path_value)
    lines.extend(["```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    ingestion_dir = as_abs(args.ingestion_dir)
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    ingestion = read_json(ingestion_dir / "summary.json")
    audit = read_json(audit_dir / "summary.json")
    created_at = datetime.now(timezone.utc).isoformat()

    target_counts = {
        GEOMETRY_TARGET: audit["input_counts"][GEOMETRY_TARGET],
        RELIABILITY_TARGET: audit["input_counts"][RELIABILITY_TARGET],
    }
    rel_counts = target_counts[RELIABILITY_TARGET]
    geom_counts = target_counts[GEOMETRY_TARGET]

    option_matrix = build_option_matrix(rel_counts, geom_counts)
    failure_matrix = build_failure_matrix(ingestion, audit)
    v3_plan = build_v3_plan(rel_counts)

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "target_failure_matrix": output_dir / "target_failure_matrix.json",
        "v3_positive_anchor_plan": output_dir / "v3_positive_anchor_plan.json",
    }

    summary = {
        "schema_version": "h002_endpoint_controlled_target_path_decision_summary_v1",
        "status": "h002_endpoint_controlled_target_path_decision_revise_target_v3_positive_anchor_sampling",
        "created_at": created_at,
        "selected_path": v3_plan["selected_path"],
        "decision": (
            "Do not run posterior smoke or upgrade the combiner. Revise relation reliability as a v3 "
            "multi-axis target and run positive-anchor sampling because the endpoint-controlled binary "
            "target is positive-sparse and has no controlled slice."
        ),
        "input_paths": {
            "ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "target_independence_audit_summary": rel_path(audit_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(path) for key, path in output_paths.items()},
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "posterior_trained": False,
            "posterior_smoke_allowed": False,
            "combiner_upgrade_allowed_now": False,
            "multi_view_as_model_input": False,
            "h001_artifacts_modified": False,
        },
        "target_counts": target_counts,
        "audit_status": audit["status"],
        "ingestion_status": ingestion["status"],
        "strict_ready_targets": audit.get("strict_ready_targets", []),
        "diagnostic_only_targets": audit.get("diagnostic_only_targets", []),
        "blocked_targets": audit.get("blocked_targets", []),
        "option_matrix": option_matrix,
        "target_failure_matrix": failure_matrix,
        "v3_positive_anchor_plan": v3_plan,
        "next_todo": v3_plan["next_todo"],
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["option_matrix"], {"options": option_matrix})
    write_json(output_paths["target_failure_matrix"], {"failures": failure_matrix})
    write_json(output_paths["v3_positive_anchor_plan"], v3_plan)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    rel = summary["target_counts"][RELIABILITY_TARGET]
    geom = summary["target_counts"][GEOMETRY_TARGET]
    print(
        f"status={summary['status']} selected={summary['selected_path']} "
        f"relation={rel['positive']}/{rel['negative']} geometry={geom['positive']}/{geom['negative']} "
        f"posterior_allowed={summary['boundary']['posterior_smoke_allowed']} "
        f"validation_used={summary['boundary']['validation_usage']} test_used={summary['boundary']['test_usage']} "
        f"next={summary['next_todo']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
