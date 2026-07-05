#!/usr/bin/env python3
"""Decide the H002 path after v4 matched-contrast target audit."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_FILL_DIR = RGA_ROOT / "reliability_target_v4_matched_contrast_label_fill_codex_proxy_user_requested"
DEFAULT_INGESTION_DIR = RGA_ROOT / "reliability_target_v4_matched_contrast_label_ingestion_codex_proxy_user_requested"
DEFAULT_AUDIT_DIR = RGA_ROOT / "reliability_target_v4_matched_contrast_target_independence_audit_codex_proxy_user_requested"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v4_matched_contrast_path_decision_codex_proxy_user_requested"

RELIABILITY_TARGET = "relation_reliability_v4_binary_target"
GEOMETRY_TARGET = "geometry_support_v4_binary_target"
USEFULNESS_TARGET = "relation_usefulness_v4_binary_target"

NEXT_TODO = "reliability_target_v5_cell_contrast_feasibility_scan"


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


def read_csv(path: Path) -> list[dict[str, Any]]:
    with as_abs(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
            "positive_sparse": original["positive_sparse"],
            "strict_slice": strict["slice_name"] if strict else "none",
            "diagnostic_slice": diagnostic["slice_name"] if diagnostic else "none",
            "risk_counts": {
                "matched_contrast_design": original.get("matched_contrast_design_risk_count", 0),
                "endpoint_object_structure": original.get("endpoint_object_structure_risk_count", 0),
                "construction": original.get("construction_risk_count", 0),
                "geometry_alignment": original.get("expected_geometry_alignment_risk_count", 0),
                "visible_object_identity": original.get("visible_object_identity_risk_count", 0),
                "visible_relation_surface": original.get("visible_relation_surface_risk_count", 0),
            },
            "top_risks": {
                "matched_contrast_design": original.get("top_matched_contrast_design_risks", [])[:3],
                "endpoint_object_structure": original.get("top_endpoint_object_structure_risks", [])[:4],
                "construction": original.get("top_construction_risks", [])[:3],
                "geometry_alignment": original.get("top_expected_geometry_alignment_risks", [])[:3],
                "visible_object_identity": original.get("top_visible_object_identity_risks", [])[:3],
                "visible_relation_surface": original.get("top_visible_relation_surface_risks", [])[:3],
            },
        }
    return output


def slice_extract(audit: dict[str, Any]) -> dict[str, Any]:
    rel_slices = [row for row in audit["slice_summaries"] if row["target_name"] == RELIABILITY_TARGET]
    by_name = {row["slice_name"]: row for row in rel_slices}
    selected = [
        "original_matched_contrast_v4",
        "matched_role_balanced_v4",
        "source_geometry_balanced_v4",
        "family_balanced_v4",
        "object_label_balanced_v4",
        "object_family_cell_balanced_v4",
        "subject_object_family_cell_balanced_v4",
        "endpoint_object_balanced_v4",
        "role_object_family_balanced_v4",
    ]
    return {
        name: {
            "rows": by_name[name]["rows"],
            "positive": by_name[name]["positive"],
            "negative": by_name[name]["negative"],
            "endpoint_object_structure_risk_count": by_name[name]["endpoint_object_structure_risk_count"],
            "construction_risk_count": by_name[name]["construction_risk_count"],
            "visible_object_identity_risk_count": by_name[name]["visible_object_identity_risk_count"],
            "strict_candidate": by_name[name]["strict_candidate"],
            "diagnostic_candidate": by_name[name]["diagnostic_candidate"],
        }
        for name in selected
        if name in by_name
    }


def pair_extract(fill_dir: Path) -> dict[str, Any]:
    rows = read_csv(fill_dir / "pair_post_label_diagnostics.csv")
    patterns = Counter(row.get("pair_label_pattern", "") for row in rows)
    direct_contrast = sum(1 for row in rows if row.get("pair_label_pattern") in {"reliable/unreliable", "unreliable/reliable"})
    both_reliable = patterns.get("reliable/reliable", 0)
    both_unreliable = patterns.get("unreliable/unreliable", 0)
    any_uncertain = sum(count for pattern, count in patterns.items() if "uncertain" in pattern)
    return {
        "pair_rows": len(rows),
        "direct_reliable_unreliable_pairs": direct_contrast,
        "both_reliable_pairs": both_reliable,
        "both_unreliable_pairs": both_unreliable,
        "any_uncertain_pairs": any_uncertain,
        "pair_label_pattern_counts": dict(sorted(patterns.items())),
    }


def build_option_matrix(audit_extract: dict[str, Any], slices: dict[str, Any], pairs: dict[str, Any]) -> list[dict[str, str]]:
    rel = audit_extract[RELIABILITY_TARGET]
    geom = audit_extract[GEOMETRY_TARGET]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "The main reliability target is balanced, but no strict or diagnostic controlled slice survives endpoint/object and visible-object shortcut audit.",
        },
        {
            "option": "expand_same_v4_matched_contrast_sampling",
            "verdict": "reject_as_primary",
            "reason": "v4 role/source/geometry balancing leaves subject/object-family shortcut intact; more rows from the same construction may scale the shortcut.",
        },
        {
            "option": "use_object_label_or_family_as_model_factor",
            "verdict": "reject_for_main_claim",
            "reason": "This would let the posterior exploit the exact shortcut the target audit exposed, rather than proving factorized reliability.",
        },
        {
            "option": "use_geometry_support_as_main_target",
            "verdict": "reject_for_reliability_claim",
            "reason": f"Geometry support is {geom['positive']}/{geom['negative']} and should remain an evidence axis; using it as the target collapses reliability back into geometry validity.",
        },
        {
            "option": "use_relation_usefulness_as_main_target",
            "verdict": "reject",
            "reason": "Relation usefulness is balanced but has the same subject/object and endpoint shortcut pattern as reliability.",
        },
        {
            "option": "use_pairwise_v4_contrast_target",
            "verdict": "reject_for_now",
            "reason": f"Only {pairs['direct_reliable_unreliable_pairs']}/{pairs['pair_rows']} v4 pairs have direct reliable/unreliable contrast.",
        },
        {
            "option": "use_subject_object_family_balanced_slice",
            "verdict": "reject_in_current_v4",
            "reason": f"The exact subject-object-family balanced slice has {slices.get('subject_object_family_cell_balanced_v4', {}).get('rows', 0)} rows.",
        },
        {
            "option": "v5_cell_contrast_feasibility_scan",
            "verdict": "select",
            "reason": "The next step must first test whether the full train pool contains enough within-cell positive/negative capacity before another label round.",
        },
        {
            "option": "freeze_h002_as_rga_diagnostic_framework",
            "verdict": "fallback",
            "reason": "If cell-contrast capacity is not available, stop forcing a posterior-learning target and keep H002 as RGA decomposition/audit framework evidence.",
        },
    ]


def build_failure_matrix(audit_extract: dict[str, Any], slices: dict[str, Any], pairs: dict[str, Any]) -> list[dict[str, Any]]:
    rel = audit_extract[RELIABILITY_TARGET]
    usefulness = audit_extract[USEFULNESS_TARGET]
    return [
        {
            "element": "matched_contrast_role",
            "observed": rel["top_risks"]["matched_contrast_design"],
            "lesson": "v4 fixed the most obvious role shortcut",
            "required_fix": "do not abandon contrast sampling; make the contrast cell stricter",
        },
        {
            "element": "subject_object_family_cell",
            "observed": rel["top_risks"]["endpoint_object_structure"][:1],
            "lesson": "the label is still determined by endpoint identity, not by general relation reliability evidence",
            "required_fix": "scan for cells where both reliable-like and unreliable-like candidates can be drawn inside the same subject/object/family cell",
        },
        {
            "element": "visible_object_identity",
            "observed": rel["top_risks"]["visible_object_identity"],
            "lesson": "a deployable model could learn object-name priors instead of factorized evidence",
            "required_fix": "make object labels a sampling/control axis, not a performance-driving model factor",
        },
        {
            "element": "subject_object_balanced_slice",
            "observed": slices.get("subject_object_family_cell_balanced_v4", {}),
            "lesson": "current v4 did not produce mixed labels within exact subject-object-family cells",
            "required_fix": "perform feasibility scan before asking for more labels",
        },
        {
            "element": "pairwise_contrast",
            "observed": pairs,
            "lesson": "direct pairwise target is too sparse in current v4 labels",
            "required_fix": "treat pairwise preference as future fallback, not the next immediate target",
        },
        {
            "element": "relation_usefulness",
            "observed": f"{usefulness['rows']} rows, {usefulness['positive']} positive, {usefulness['negative']} negative",
            "lesson": "usefulness is not a shortcut-free substitute target",
            "required_fix": "keep usefulness as an auxiliary audit/evidence axis",
        },
    ]


def build_next_plan() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "selected_path": "v5_cell_contrast_feasibility_scan",
        "claim_boundary": (
            "This is not a posterior upgrade. It is a target-construction feasibility gate required because v4 "
            "balanced labels but failed endpoint/object target independence."
        ),
        "goal": (
            "Scan the full train-only support_contact/relative_vertical pool for subject-object/family cells that "
            "can support both reliable-like and unreliable-like candidates before another label round."
        ),
        "cell_axes": [
            "predicate_family",
            "predicate_label when feasible",
            "subject_label",
            "object_label",
            "endpoint_flag_pattern_hidden",
            "subject_object_family_cell_hidden",
        ],
        "secondary_controls": [
            "rank_band_hidden",
            "source_queue_hidden",
            "geometry_status_hidden",
            "label_match_status_hidden",
            "asset_packet_source_hidden",
            "scan_id cap",
        ],
        "feasibility_gates": [
            "at least 80 candidate rows before label fill",
            "at least 40 candidate contrast pairs or equivalent balanced rows",
            "at least 10 distinct subject-object-family cells with both roles",
            "no single cell contributes more than 20 percent of selected rows",
            "support_contact and relative_vertical are both represented unless capacity proves otherwise",
            "asset packet coverage or generation path is explicit before label fill",
        ],
        "posterior_reopen_gate_after_labels": [
            "relation reliability binary target has at least 20 positives and 20 negatives",
            "subject_object_family_cell balanced slice is nonempty and diagnostic-ready",
            "endpoint/object and visible object-label risk are not sufficient to predict the target",
            "rank band, source queue, geometry status, and packet source are controlled or audited",
            "validation/test usage remains false",
        ],
        "stop_rule": (
            "If the feasibility scan cannot find enough mixed-capacity cells, freeze H002 as an RGA diagnostic "
            "framework and stop posterior smoke in this branch."
        ),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    rel = summary["audit_extract"][RELIABILITY_TARGET]
    pairs = summary["pair_extract"]
    lines = [
        "# H002 Reliability Target V4 Matched Contrast Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only path decision.",
        "- No validation/test rows are used.",
        "- No posterior is trained.",
        "- No new labels are filled.",
        "- Multi-view remains audit/label evidence only.",
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
        f"- Relation reliability target: `{rel['rows']}` rows, `{rel['positive']}` positive, `{rel['negative']}` negative.",
        "- No strict or diagnostic controlled slice exists.",
        f"- Direct reliable/unreliable pair contrast: `{pairs['direct_reliable_unreliable_pairs']}/{pairs['pair_rows']}` pairs.",
        "- The strongest target shortcut is subject/object family identity.",
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
            "| Element | Lesson | Required Fix |",
            "| --- | --- | --- |",
        ]
    )
    for row in summary["failure_matrix"]:
        lines.append(f"| `{row['element']}` | {row['lesson']} | {row['required_fix']} |")

    lines.extend(
        [
            "",
            "## Next Plan",
            "",
            f"Next TODO: `{summary['next_todo']}`",
            "",
            "Cell axes:",
        ]
    )
    for item in summary["next_plan"]["cell_axes"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "Feasibility gates:"])
    for item in summary["next_plan"]["feasibility_gates"]:
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
    slices = slice_extract(audit_summary)
    pairs = pair_extract(fill_dir)
    option_matrix = build_option_matrix(audit_extract, slices, pairs)
    failure_matrix = build_failure_matrix(audit_extract, slices, pairs)
    next_plan = build_next_plan()

    status = "h002_reliability_target_v4_matched_contrast_path_decision_select_v5_cell_contrast_feasibility"
    decision = (
        "Do not run posterior smoke or expand the same v4 sampling. v4 fixed role balance but failed "
        "subject/object-family target independence, so the next step is a train-only v5 cell-contrast "
        "feasibility scan. If that scan cannot find enough mixed-capacity cells, freeze H002 as an RGA "
        "diagnostic framework rather than forcing a posterior claim."
    )

    output_paths = {
        "summary": output_dir / "summary.json",
        "report": output_dir / "report.md",
        "option_matrix": output_dir / "option_matrix.json",
        "failure_matrix": output_dir / "failure_matrix.json",
        "next_plan": output_dir / "next_plan.json",
    }

    summary = {
        "schema_version": "h002_reliability_target_v4_matched_contrast_path_decision_summary_v1",
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
        },
        "audit_extract": audit_extract,
        "slice_extract": slices,
        "pair_extract": pairs,
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
        "status={status} selected={selected} rel={rows}/{pos}/{neg} "
        "posterior_allowed={posterior_allowed} validation_used={validation_used} "
        "test_used={test_used} next={next_todo}".format(
            status=summary["status"],
            selected=summary["selected_path"],
            rows=rel["rows"],
            pos=rel["positive"],
            neg=rel["negative"],
            posterior_allowed=summary["boundary"]["posterior_smoke_allowed"],
            validation_used=summary["boundary"]["validation_usage"],
            test_used=summary["boundary"]["test_usage"],
            next_todo=summary["next_todo"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
