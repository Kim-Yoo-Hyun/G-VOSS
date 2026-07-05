#!/usr/bin/env python3
"""Decide the H002 path after v5 cell-contrast target audit."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_FILL_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_label_fill_codex_proxy_user_requested"
DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_label_ingestion_codex_proxy_user_requested"
DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_target_independence_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v5_cell_contrast_path_decision_codex_proxy_user_requested"

RELIABILITY_TARGET = "relation_reliability_v5_binary_target"
GEOMETRY_TARGET = "geometry_support_v5_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v5_binary_target"

NEXT_TODO = "reliability_target_v6_uncertainty_aware_target_design"


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
            "min_class": original["min_class"],
            "minority_class_sparse": original["minority_class_sparse"],
            "strict_slice": strict["slice_name"] if strict else "none",
            "diagnostic_slice": diagnostic["slice_name"] if diagnostic else "none",
            "risk_counts": {
                "cell_contrast_design": original.get("cell_contrast_design_risk_count", 0),
                "endpoint_object_structure": original.get("endpoint_object_structure_risk_count", 0),
                "construction": original.get("construction_risk_count", 0),
                "geometry_alignment": original.get("expected_geometry_alignment_risk_count", 0),
                "visible_object_identity": original.get("visible_object_identity_risk_count", 0),
                "visible_relation_surface": original.get("visible_relation_surface_risk_count", 0),
            },
            "top_risks": {
                "cell_contrast_design": original.get("top_cell_contrast_design_risks", [])[:3],
                "endpoint_object_structure": original.get("top_endpoint_object_structure_risks", [])[:4],
                "construction": original.get("top_construction_risks", [])[:3],
                "geometry_alignment": original.get("top_expected_geometry_alignment_risks", [])[:3],
                "visible_object_identity": original.get("top_visible_object_identity_risks", [])[:3],
                "visible_relation_surface": original.get("top_visible_relation_surface_risks", [])[:3],
            },
        }
    return output


def family_extract(audit: dict[str, Any]) -> dict[str, Any]:
    rel_original = audit["target_decisions"][RELIABILITY_TARGET]["original"]
    geom_original = audit["target_decisions"][GEOMETRY_TARGET]["original"]
    use_original = audit["target_decisions"][USEFULNESS_TARGET]["original"]
    return {
        "relation_reliability_by_family": rel_original["counts"]["by_family"],
        "geometry_support_by_family": geom_original["counts"]["by_family"],
        "relation_usefulness_by_family": use_original["counts"]["by_family"],
        "relation_reliability_by_predicate": rel_original["counts"]["by_predicate"],
        "geometry_support_by_predicate": geom_original["counts"]["by_predicate"],
        "relation_usefulness_by_predicate": use_original["counts"]["by_predicate"],
    }


def slice_extract(audit: dict[str, Any]) -> dict[str, Any]:
    rel_slices = [row for row in audit["slice_summaries"] if row["target_name"] == RELIABILITY_TARGET]
    by_name = {row["slice_name"]: row for row in rel_slices}
    selected = [
        "original_cell_contrast_v5",
        "cell_role_balanced_v5",
        "source_queue_balanced_v5",
        "geometry_status_balanced_v5",
        "rank_band_balanced_v5",
        "family_balanced_v5",
        "object_label_balanced_v5",
        "object_family_cell_balanced_v5",
        "subject_object_family_cell_balanced_v5",
        "cell_key_balanced_v5",
        "cell_pair_balanced_v5",
        "role_object_family_balanced_v5",
    ]
    return {
        name: {
            "rows": by_name[name]["rows"],
            "positive": by_name[name]["positive"],
            "negative": by_name[name]["negative"],
            "cell_contrast_design_risk_count": by_name[name]["cell_contrast_design_risk_count"],
            "endpoint_object_structure_risk_count": by_name[name]["endpoint_object_structure_risk_count"],
            "construction_risk_count": by_name[name]["construction_risk_count"],
            "visible_object_identity_risk_count": by_name[name]["visible_object_identity_risk_count"],
            "strict_candidate": by_name[name]["strict_candidate"],
            "diagnostic_candidate": by_name[name]["diagnostic_candidate"],
        }
        for name in selected
        if name in by_name
    }


def build_option_matrix(audit_extract: dict[str, Any], families: dict[str, Any], pair: dict[str, Any]) -> list[dict[str, str]]:
    rel = audit_extract[RELIABILITY_TARGET]
    geom = audit_extract[GEOMETRY_TARGET]
    use = audit_extract[USEFULNESS_TARGET]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "The reliability target is sparse, has no direct pair contrast, and no strict or diagnostic controlled slice survives shortcut audit.",
        },
        {
            "option": "expand_same_v5_cell_contrast_sampling",
            "verdict": "reject_as_primary",
            "reason": "v5 already balances role/source/geometry axes, but labels still collapse to pair/cell/object-family shortcuts.",
        },
        {
            "option": "use_object_label_or_family_as_model_factor",
            "verdict": "reject_for_main_claim",
            "reason": "This would feed the posterior the exact shortcut exposed by target-independence audit.",
        },
        {
            "option": "use_geometry_support_as_main_target",
            "verdict": "reject_for_reliability_claim",
            "reason": f"Geometry support is {geom['positive']}/{geom['negative']} and remains an evidence axis, not relation reliability.",
        },
        {
            "option": "use_relation_usefulness_as_main_target",
            "verdict": "reject_for_main_claim",
            "reason": f"Usefulness is also sparse at {use['positive']}/{use['negative']} and inherits the same object/cell shortcut risk.",
        },
        {
            "option": "family_specific_binary_targets",
            "verdict": "reject_for_now",
            "reason": f"Family split is too skewed for binary posterior: {families['relation_reliability_by_family']}.",
        },
        {
            "option": "direct_pair_contrast_target",
            "verdict": "reject_for_now",
            "reason": f"Current v5 has {pair['direct_reliable_unreliable_contrast_pairs']}/{pair['pair_count']} direct reliable/unreliable pair contrasts.",
        },
        {
            "option": "keep_v5_as_audit_only_artifact",
            "verdict": "select_for_current_artifact",
            "reason": "v5 is useful evidence that role/source balancing alone is insufficient, but it is not a posterior target.",
        },
        {
            "option": "v6_uncertainty_aware_target_design",
            "verdict": "select_next",
            "reason": "The binary target discards 41 uncertain rows; the next design should model uncertainty/abstention explicitly before any new label fill.",
        },
        {
            "option": "freeze_h002_as_rga_diagnostic_framework",
            "verdict": "fallback",
            "reason": "If uncertainty-aware target design still cannot pass independence checks, stop forcing posterior learning and frame H002 as RGA diagnostic/decomposition.",
        },
    ]


def build_failure_matrix(audit_extract: dict[str, Any], pair: dict[str, Any], fill_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rel = audit_extract[RELIABILITY_TARGET]
    counts = fill_summary["counts"]
    return [
        {
            "element": "binary_reliability_target",
            "observed": f"{rel['rows']} rows, {rel['positive']} positive, {rel['negative']} negative",
            "lesson": "binary-only reliability supervision is too sparse after excluding uncertain rows",
            "required_fix": "treat uncertainty as a first-class target state rather than discard it",
        },
        {
            "element": "uncertain_mass",
            "observed": f"{counts['relation_reliability_v5'].get('uncertain', 0)}/{counts['rows']} uncertain labels",
            "lesson": "the audit packets often do not support a confident binary decision",
            "required_fix": "design uncertainty-aware multiclass or abstention-aware target before another posterior attempt",
        },
        {
            "element": "pairwise_contrast",
            "observed": pair,
            "lesson": "within-pair direct reliable/unreliable contrast did not emerge from v5 labels",
            "required_fix": "do not use direct pair ranking as the immediate next target without a new feasibility proof",
        },
        {
            "element": "cell_identity",
            "observed": rel["top_risks"]["cell_contrast_design"],
            "lesson": "cell id and pair id can predict labels too well",
            "required_fix": "keep cell metadata as audit-only blocking/grouping variables",
        },
        {
            "element": "object_identity",
            "observed": rel["top_risks"]["endpoint_object_structure"] + rel["top_risks"]["visible_object_identity"],
            "lesson": "object labels and endpoint family still explain the target",
            "required_fix": "design group-aware evaluation and avoid object label as a main posterior feature",
        },
    ]


def build_next_plan() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "selected_path": "v6_uncertainty_aware_target_design",
        "claim_boundary": (
            "This is not a posterior upgrade. It is a target-design step motivated by repeated evidence that "
            "binary relation reliability targets become sparse and shortcut-prone under current sampling."
        ),
        "goal": (
            "Redefine the reliability supervision so that reliable, unreliable, and uncertain/abstain states are "
            "modeled explicitly, while geometry support and relation usefulness remain auxiliary evidence axes."
        ),
        "candidate_target_forms": [
            "multiclass reliability: reliable / unreliable / uncertain",
            "abstention-aware binary: reliable-vs-unreliable only with explicit uncertain rejection loss",
            "multi-task target: reliability state + geometry support + relation usefulness",
            "ordinal target: reliable > uncertain > unreliable only if ordering is defensible",
            "ranking target only if a new feasibility scan finds direct pair contrasts",
        ],
        "must_preserve": [
            "semantic score != geometry validity != relation reliability",
            "geometry support/usefulness are evidence axes, not replacements for reliability",
            "multi-view remains audit evidence until the base factorized target is defensible",
            "validation/test usage remains false",
            "hidden cell/pair/object-family metadata remains audit-only",
        ],
        "design_gates": [
            "derive target schema from v5 failure modes before any new labels",
            "define which fields are model inputs and which are audit/blocking variables",
            "predeclare group-aware independence checks for cell/pair/object-family shortcuts",
            "require a nontrivial controlled slice before posterior smoke",
            "decide whether v5 labels can be reused only as diagnostics or as design examples",
        ],
        "stop_rule": (
            "If uncertainty-aware target design still cannot define an independence-testable target, freeze H002 "
            "as an RGA benchmark/diagnostic framework and do not run posterior smoke in this branch."
        ),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    rel = summary["audit_extract"][RELIABILITY_TARGET]
    pair = summary["pair_diagnostics"]
    fill_counts = summary["fill_counts"]
    lines = [
        "# H002 Reliability Target V5 Cell Contrast Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only path decision.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- No new labels are filled.",
        "- Multi-view remains audit/label evidence, not posterior input.",
        "- H001 artifacts are not modified.",
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
        "## Why Not Posterior",
        "",
        f"- Relation reliability binary target: `{rel['rows']}` rows, `{rel['positive']}` positive, `{rel['negative']}` negative.",
        f"- Uncertain reliability labels: `{fill_counts['relation_reliability_v5'].get('uncertain', 0)}/{fill_counts['rows']}`.",
        f"- Direct reliable/unreliable pair contrast: `{pair['direct_reliable_unreliable_contrast_pairs']}/{pair['pair_count']}` pairs.",
        "- No strict or diagnostic controlled slice exists.",
        "- The strongest target shortcuts are cell/pair id, subject-object-family cell, and visible object labels.",
        "",
        "## Option Matrix",
        "",
        "| Option | Verdict | Reason |",
        "| --- | --- | --- |",
    ]
    for row in summary["option_matrix"]:
        lines.append(f"| `{row['option']}` | `{row['verdict']}` | {row['reason']} |")

    lines.extend(
        [
            "",
            "## Failure Matrix",
            "",
            "| Element | Observed | Lesson | Required Fix |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in summary["failure_matrix"]:
        observed = json.dumps(row["observed"], ensure_ascii=False) if not isinstance(row["observed"], str) else row["observed"]
        lines.append(f"| `{row['element']}` | {observed} | {row['lesson']} | {row['required_fix']} |")

    lines.extend(["", "## Next Plan", "", f"Next TODO: `{summary['next_todo']}`", "", "Candidate target forms:"])
    for item in summary["next_plan"]["candidate_target_forms"]:
        lines.append(f"- {item}")
    lines.extend(["", "Design gates:"])
    for item in summary["next_plan"]["design_gates"]:
        lines.append(f"- {item}")
    lines.extend(["", "Stop rule:", "", summary["next_plan"]["stop_rule"], ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    fill_dir = as_abs(args.fill_dir)
    ingestion_dir = as_abs(args.ingestion_dir)
    audit_dir = as_abs(args.audit_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fill_summary = read_json(fill_dir / "summary.json")
    ingestion_summary = read_json(ingestion_dir / "summary.json")
    audit_summary = read_json(audit_dir / "summary.json")

    audit_extract = target_extract(audit_summary)
    families = family_extract(audit_summary)
    slices = slice_extract(audit_summary)
    pair = audit_summary["pair_diagnostics"]
    option_matrix = build_option_matrix(audit_extract, families, pair)
    failure_matrix = build_failure_matrix(audit_extract, pair, fill_summary)
    next_plan = build_next_plan()

    status = "h002_reliability_target_v5_cell_contrast_path_decision_select_v6_uncertainty_aware_target_design"
    decision = (
        "Do not run posterior smoke and do not expand the same v5 binary cell-contrast target. "
        "V5 is kept as an audit-only artifact showing that role/source/geometry balancing is not enough. "
        "The next step is an uncertainty-aware v6 target design because the binary target discards most "
        "ambiguous evidence and remains sparse/shortcut-prone."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "failure_matrix": output_dir / "failure_matrix.json",
        "next_plan": output_dir / "next_plan.json",
    }

    summary = {
        "schema_version": "h002_reliability_target_v5_cell_contrast_path_decision_summary_v1",
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "selected_path": next_plan["selected_path"],
        "decision": decision,
        "next_todo": NEXT_TODO,
        "input_paths": {
            "fill_summary": rel_path(fill_dir / "summary.json"),
            "ingestion_summary": rel_path(ingestion_dir / "summary.json"),
            "audit_summary": rel_path(audit_dir / "summary.json"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {key: rel_path(value) for key, value in output_paths.items()},
        "upstream_status": {
            "fill": fill_summary.get("status"),
            "ingestion": ingestion_summary.get("status"),
            "audit": audit_summary.get("status"),
        },
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
        "fill_counts": fill_summary["counts"],
        "audit_extract": audit_extract,
        "family_extract": families,
        "slice_extract": slices,
        "pair_diagnostics": pair,
        "option_matrix": option_matrix,
        "failure_matrix": failure_matrix,
        "next_plan": next_plan,
    }

    write_json(output_paths["summary"], summary)
    write_json(output_paths["option_matrix"], option_matrix)
    write_json(output_paths["failure_matrix"], failure_matrix)
    write_json(output_paths["next_plan"], next_plan)
    write_report(output_paths["report"], summary)
    return summary


def main() -> int:
    summary = run(parse_args())
    rel = summary["audit_extract"][RELIABILITY_TARGET]
    print(
        "status={status} selected={selected} rel={rows}/{pos}/{neg} uncertain={uncertain} "
        "direct_pair_contrast={direct_pair_contrast} posterior_allowed={posterior_allowed} "
        "validation_used={validation_used} test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            selected=summary["selected_path"],
            rows=rel["rows"],
            pos=rel["positive"],
            neg=rel["negative"],
            uncertain=summary["fill_counts"]["relation_reliability_v5"].get("uncertain", 0),
            direct_pair_contrast=summary["pair_diagnostics"]["direct_reliable_unreliable_contrast_pairs"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
