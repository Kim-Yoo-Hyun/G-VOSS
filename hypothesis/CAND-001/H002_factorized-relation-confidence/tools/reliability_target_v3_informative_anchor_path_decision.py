#!/usr/bin/env python3
"""Decide the H002 path after informative-anchor v3 target audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_FILL_DIR = RGA_ROOT / "reliability_target_v3_informative_anchor_label_fill_codex_proxy_user_requested"
DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v3_informative_anchor_label_ingestion_codex_proxy_user_requested"
DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v3_informative_anchor_target_independence_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v3_informative_anchor_path_decision_codex_proxy_user_requested"

RELIABILITY_TARGET = "relation_reliability_v3_binary_target"
GEOMETRY_TARGET = "geometry_support_v3_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v3_binary_target"

NEXT_TODO = "reliability_target_v4_matched_contrast_plan"


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


def target_extract(audit: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for target_name in [RELIABILITY_TARGET, GEOMETRY_TARGET, USEFULNESS_TARGET]:
        decision = audit["target_decisions"][target_name]
        original = decision["original"]
        strict = decision.get("recommended_strict_slice")
        diagnostic = decision.get("recommended_diagnostic_slice")
        output[target_name] = {
            "status": decision["status"],
            "rows": original["rows"],
            "positive": original["positive"],
            "negative": original["negative"],
            "positive_rate": original["positive_rate"],
            "positive_sparse": original["positive_sparse"],
            "strict_slice": strict["slice_name"] if strict else "none",
            "diagnostic_slice": diagnostic["slice_name"] if diagnostic else "none",
            "risk_counts": {
                "anchor_sampling": original.get("anchor_sampling_risk_count", 0),
                "endpoint_object_structure": original.get("endpoint_object_structure_risk_count", 0),
                "construction": original.get("construction_risk_count", 0),
                "geometry_alignment": original.get("expected_geometry_alignment_risk_count", 0),
                "object_identity": original.get("visible_object_identity_risk_count", 0),
                "relation_surface": original.get("visible_relation_surface_risk_count", 0),
            },
            "top_risks": {
                "anchor_sampling": original.get("top_anchor_sampling_risks", [])[:3],
                "endpoint_object_structure": original.get("top_endpoint_object_structure_risks", [])[:4],
                "construction": original.get("top_construction_risks", [])[:3],
                "geometry_alignment": original.get("top_expected_geometry_alignment_risks", [])[:3],
                "object_identity": original.get("top_visible_object_identity_risks", [])[:3],
            },
        }
    return output


def build_option_matrix(rel: dict[str, Any], geom: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "The main reliability target has mass, but no strict or diagnostic controlled slice survives shortcut audit.",
        },
        {
            "option": "use_full_informative_anchor_target",
            "verdict": "reject",
            "reason": "Anchor category, endpoint/object structure, object labels, and rank band strongly predict the target.",
        },
        {
            "option": "use_family_or_predicate_balanced_slice",
            "verdict": "reject_for_posterior_keep_for_diagnostic",
            "reason": "Family/predicate-balanced slices keep enough rows but still carry anchor/object/endpoint shortcut risks.",
        },
        {
            "option": "use_anchor_or_endpoint_balanced_slice",
            "verdict": "reject",
            "reason": "Anchor/endpoint matching removes part of the shortcut but collapses to tiny balanced slices.",
        },
        {
            "option": "use_geometry_support_as_main_target",
            "verdict": "reject_for_reliability_claim",
            "reason": (
                f"Geometry support is {geom['positive']}/{geom['negative']}; using it as the main target would "
                "collapse relation reliability into geometry validity."
            ),
        },
        {
            "option": "collect_more_same_informative_anchor_rows",
            "verdict": "reject_as_primary",
            "reason": "More rows from the same anchor construction are likely to preserve the same hidden target shortcut.",
        },
        {
            "option": "matched_contrast_reliability_target_v4",
            "verdict": "select",
            "reason": (
                "The next target must create positive and negative candidates within the same endpoint/object/rank strata, "
                "instead of assigning positives and negatives from separate anchor categories."
            ),
        },
        {
            "option": "freeze_h002_as_rga_diagnostic_only",
            "verdict": "fallback",
            "reason": "If matched contrast still cannot produce an independent target, stop forcing the posterior claim.",
        },
        {
            "option": "add_multi_view_as_model_input_now",
            "verdict": "reject_now",
            "reason": "Multi-view before target independence would mix feature gain with target-construction shortcuts.",
        },
    ]


def build_failure_matrix(audit_extract: dict[str, Any]) -> list[dict[str, Any]]:
    rel = audit_extract[RELIABILITY_TARGET]
    geom = audit_extract[GEOMETRY_TARGET]
    usefulness = audit_extract[USEFULNESS_TARGET]
    return [
        {
            "element": "relation_reliability_target",
            "observed": f"{rel['rows']} rows, {rel['positive']} positive, {rel['negative']} negative",
            "lesson": "positive mass is now sufficient, but target independence is not",
            "required_fix": "construct positives and negatives inside matched endpoint/object/rank strata",
        },
        {
            "element": "anchor_category",
            "observed": rel["top_risks"]["anchor_sampling"],
            "lesson": "the sampling anchor behaves like a hidden label proxy",
            "required_fix": "remove anchor category as the positive/negative construction axis",
        },
        {
            "element": "endpoint_object_structure",
            "observed": rel["top_risks"]["endpoint_object_structure"],
            "lesson": "subject/object family and endpoint flags can nearly identify the target",
            "required_fix": "match or cap endpoint/object cells before label derivation",
        },
        {
            "element": "visible_object_identity",
            "observed": rel["top_risks"]["object_identity"],
            "lesson": "visible object labels remain a strong non-target shortcut",
            "required_fix": "require within-object-family positive/negative contrast where possible",
        },
        {
            "element": "rank_band",
            "observed": rel["top_risks"]["construction"],
            "lesson": "semantic rank still leaks target construction",
            "required_fix": "balance top/mid/long-tail rank bands inside contrast cells",
        },
        {
            "element": "geometry_support",
            "observed": f"{geom['rows']} rows, {geom['positive']} positive, {geom['negative']} negative",
            "lesson": "geometry support is an evidence axis, not the reliability target",
            "required_fix": "keep geometry support as factor input/diagnostic, not main label",
        },
        {
            "element": "relation_usefulness",
            "observed": f"{usefulness['rows']} rows, {usefulness['positive']} positive, {usefulness['negative']} negative",
            "lesson": "usefulness has mass but shares the same target-construction shortcut",
            "required_fix": "use usefulness as a post-label audit axis and cap trivial dense relations",
        },
    ]


def build_next_plan() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "selected_path": "revise_to_matched_contrast_reliability_target_v4",
        "why_v4": (
            "v3 fixed positive sparsity but repeatedly failed target independence. v4 changes the construction principle, "
            "not just the sample count."
        ),
        "goal": (
            "Create a train-only reliability target where positive and negative labels are compared within matched "
            "predicate, endpoint/object, and rank strata."
        ),
        "recommended_pool_size": 240,
        "minimum_labeled_pool_size": 160,
        "matching_axes": [
            "predicate_family",
            "predicate_label when enough rows exist",
            "endpoint_flag_pattern_hidden",
            "object_family_cell_hidden or endpoint_family_cell_hidden",
            "rank_band_hidden",
        ],
        "sampling_constraints": [
            "do not use anchor_category as a positive/negative bucket",
            "cap floor/wall/ceiling and room-surface endpoints per matched stratum",
            "include both support_contact and relative_vertical, but do not force label by family",
            "prefer repeated object-family cells with both likely reliable and likely unreliable candidates",
            "keep semantic score, rank, p_geom_valid, geometry_status, label_match_status, and queue hidden from labelers",
            "join hidden construction metadata only after label lock",
            "keep multi-view as audit evidence only",
        ],
        "posterior_reopen_gate": [
            "relation reliability binary target has at least 20 positives and 20 negatives",
            "a strict or explicitly defensible diagnostic controlled slice exists",
            "anchor/category shortcut risk is zero on the selected slice",
            "endpoint/object and visible object-label shortcuts are not enough to explain the target",
            "rank-band and geometry-status controls do not dominate the selected slice",
            "validation/test usage remains false",
        ],
        "fallback_stop_rule": (
            "If matched contrast v4 cannot create an independent target, freeze H002 as an RGA diagnostic/decomposition "
            "framework and do not continue posterior smoke in this branch."
        ),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    rel = summary["audit_extract"][RELIABILITY_TARGET]
    geom = summary["audit_extract"][GEOMETRY_TARGET]
    usefulness = summary["audit_extract"][USEFULNESS_TARGET]
    lines = [
        "# H002 Reliability Target V3 Informative Anchor Path Decision",
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
        "## Option Matrix",
        "",
        "| Option | Verdict | Reason |",
        "| --- | --- | --- |",
    ]
    for item in summary["option_matrix"]:
        lines.append(f"| `{item['option']}` | `{item['verdict']}` | {item['reason']} |")
    lines.extend(["", "## Failure Matrix", "", "| Element | Lesson | Required Fix |", "| --- | --- | --- |"])
    for item in summary["failure_matrix"]:
        lines.append(f"| `{item['element']}` | {item['lesson']} | {item['required_fix']} |")
    lines.extend(["", "## Next Plan", "", f"Next TODO: `{summary['next_todo']}`", "", "Matching axes:", ""])
    for item in summary["next_plan"]["matching_axes"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "Posterior reopen gate:", ""])
    for item in summary["next_plan"]["posterior_reopen_gate"]:
        lines.append(f"- {item}")
    lines.extend(["", "Fallback stop rule:", "", summary["next_plan"]["fallback_stop_rule"], ""])
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
    audit_extract = target_extract(audit)
    rel = audit_extract[RELIABILITY_TARGET]
    geom = audit_extract[GEOMETRY_TARGET]
    option_matrix = build_option_matrix(rel, geom)
    failure_matrix = build_failure_matrix(audit_extract)
    next_plan = build_next_plan()
    created_at = datetime.now(timezone.utc).isoformat()

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "failure_matrix": output_dir / "failure_matrix.json",
        "next_plan": output_dir / "next_plan.json",
    }

    summary = {
        "schema_version": "h002_reliability_target_v3_informative_anchor_path_decision_summary_v1",
        "status": "h002_reliability_target_v3_informative_anchor_path_decision_matched_contrast_v4",
        "created_at": created_at,
        "selected_path": next_plan["selected_path"],
        "decision": (
            "Do not run posterior smoke, accept the full informative-anchor target, or use geometry-support as the main "
            "target. v3 fixed positive sparsity but failed target independence, so the next step is a v4 matched-contrast "
            "target construction that compares positives and negatives inside matched endpoint/object/rank strata."
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
        "audit_extract": audit_extract,
        "option_matrix": option_matrix,
        "failure_matrix": failure_matrix,
        "next_plan": next_plan,
        "next_todo": next_plan["next_todo"],
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["option_matrix"], {"options": option_matrix})
    write_json(output_paths["failure_matrix"], {"failures": failure_matrix})
    write_json(output_paths["next_plan"], next_plan)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    rel = summary["audit_extract"][RELIABILITY_TARGET]
    print(
        "status={status} selected={selected_path} rel={rows}/{pos}/{neg} rel_status={rel_status} "
        "posterior_allowed={posterior_allowed} validation_used={validation_used} test_used={test_used} "
        "next={next_todo}".format(
            status=summary["status"],
            selected_path=summary["selected_path"],
            rows=rel["rows"],
            pos=rel["positive"],
            neg=rel["negative"],
            rel_status=rel["status"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
