#!/usr/bin/env python3
"""Synthesize the blocker after the H002 v23 hanging-on positive-anchor capacity scan."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_CAPACITY_DIR = RGA_ROOT / "reliability_target_v23_hanging_on_positive_anchor_capacity_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v23_hanging_on_positive_anchor_blocker_synthesis"

EXPECTED_CAPACITY_STATUS = (
    "h002_reliability_target_v23_hanging_on_positive_anchor_capacity_scan_"
    "blocked_no_matched_positive_anchor_capacity"
)
EXPECTED_CAPACITY_NEXT = "reliability_target_v23_hanging_on_positive_anchor_blocker_synthesis"

STATUS_READY = "h002_reliability_target_v23_hanging_on_positive_anchor_blocker_synthesis_ready_for_path_decision"
STATUS_ERROR = "h002_reliability_target_v23_hanging_on_positive_anchor_blocker_synthesis_validation_errors"
NEXT_TODO_READY = "reliability_target_v23_hanging_on_positive_anchor_path_decision_after_blocker_synthesis"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path) -> str:
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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def validate_capacity(summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_CAPACITY_STATUS:
        errors.append({"error_type": "unexpected_capacity_status", "expected": EXPECTED_CAPACITY_STATUS, "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_CAPACITY_NEXT:
        errors.append({"error_type": "unexpected_capacity_next", "expected": EXPECTED_CAPACITY_NEXT, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "capacity_validation_errors_present", "actual": summary.get("validation_errors")})
    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "multi_view_as_model_input",
        "mesh_as_model_input",
        "fills_new_labels",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "capacity_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def build_blocker(capacity: dict[str, Any]) -> dict[str, Any]:
    counts = capacity["counts"]
    decision = capacity["decision"]
    selected = decision["selected_spec"]
    strict = decision["strict_geometry_spec"]
    preview = capacity["selection_preview_summary"]
    return {
        "schema_version": "h002_v23_hanging_on_positive_anchor_blocker_synthesis_v1",
        "root_cause": "matched_cell_diversity_blocker_not_row_count_blocker",
        "short_explanation": (
            "Full train contains enough positive-anchor proxy rows and hard-negative rows, "
            "but the controlled target collapses into too few matched cells once affordance, "
            "rank, and coverage are jointly controlled."
        ),
        "capacity_facts": {
            "primary_rows": capacity["primary_rows"],
            "positive_anchor_cell_rows": counts["positive_anchor_cell"].get("True", 0),
            "positive_anchor_proxy_rows": counts["v23_proxy_role"].get("positive_anchor_proxy", 0),
            "hard_negative_proxy_rows": counts["v23_proxy_role"].get("hard_negative_proxy", 0),
            "selected_spec": selected["spec_name"],
            "selected_spec_mixed_groups": selected["mixed_groups"],
            "selected_spec_balanced_proxy_row_capacity": selected["balanced_proxy_row_capacity"],
            "strict_geometry_mixed_groups": strict["mixed_groups"],
            "strict_geometry_balanced_proxy_row_capacity": strict["balanced_proxy_row_capacity"],
            "preview_rows_after_caps": preview["selected_rows"],
            "failed_checks": decision["failed_checks"],
        },
        "why_candidate_mining_is_blocked": [
            "The selected route has only 5 mixed positive/negative cells, below the predeclared 30-cell gate.",
            "A 232-row capped preview is possible, but it would be drawn from a small number of strata and would not prove target independence.",
            "Exact subject/object or visible-pair alternatives have more mixed groups, but those fields are precisely the shortcut axes H002 has repeatedly found unsafe.",
            "The strict geometry-exact route has only 40 balanced proxy rows, so it is too small for the intended reliability target.",
        ],
        "path_options_for_next_decision": [
            {
                "option": "freeze_v23_positive_anchor_as_diagnostic_negative_evidence",
                "verdict": "recommended",
                "reason": "It preserves the finding that attachment-deferred/hanging-on has real positive cells but insufficient controlled contrast for a main posterior target.",
            },
            {
                "option": "relax_to_subject_object_or_visible_pair_mixed_groups",
                "verdict": "not_recommended_for_main_target",
                "reason": "It would likely reintroduce subject/object/endpoint shortcuts, so it can only be diagnostic.",
            },
            {
                "option": "expand_affordance_taxonomy_and_rescan",
                "verdict": "low_priority",
                "reason": "The bottleneck is controlled mixed-cell diversity, not the absence of positive-anchor rows. More labels may increase row count but may not solve independence.",
            },
            {
                "option": "move_attachment_deferred_to_future_work_or_appendix",
                "verdict": "recommended_if_main_target_needed_now",
                "reason": "Current evidence supports attachment as an important but difficult relation family; it is not yet a clean posterior-smoke target.",
            },
            {
                "option": "return_to_general_RGA_target_design_with_relation_family_diagnostics",
                "verdict": "recommended",
                "reason": "H002 can keep semantic/geometry/reliability factorization as the main claim while reporting relation-family-specific target-construction failures as evidence.",
            },
        ],
        "claim_boundary_update": {
            "h002_not_falsified": True,
            "posterior_smoke_allowed": False,
            "attachment_deferred_main_target_ready": False,
            "diagnostic_value": (
                "This stage strengthens the target-construction argument: a relation family can have semantically plausible and geometrically plausible rows, "
                "yet still fail as a factorized posterior target if positive/reject labels are concentrated in shortcut-prone strata."
            ),
        },
    }


def build_report(summary: dict[str, Any]) -> str:
    blocker = summary["blocker_synthesis"]
    facts = blocker["capacity_facts"]
    lines = [
        "# V79 Hanging-On Positive-Anchor Blocker Synthesis",
        "",
        "## Purpose",
        "",
        "Synthesize why the v23 positive-anchor capacity scan does not unlock candidate mining.",
        "This is an interpretation artifact only: no labels, no posterior smoke, no validation/test rows.",
        "",
        "## Decision",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        f"root_cause = {blocker['root_cause']}",
        "```",
        "",
        "## Key Counts",
        "",
        "```text",
        f"primary_rows = {facts['primary_rows']}",
        f"positive_anchor_cell_rows = {facts['positive_anchor_cell_rows']}",
        f"positive_anchor_proxy_rows = {facts['positive_anchor_proxy_rows']}",
        f"hard_negative_proxy_rows = {facts['hard_negative_proxy_rows']}",
        f"selected_spec_mixed_groups = {facts['selected_spec_mixed_groups']}",
        f"selected_spec_balanced_proxy_row_capacity = {facts['selected_spec_balanced_proxy_row_capacity']}",
        f"strict_geometry_mixed_groups = {facts['strict_geometry_mixed_groups']}",
        f"strict_geometry_balanced_proxy_row_capacity = {facts['strict_geometry_balanced_proxy_row_capacity']}",
        f"preview_rows_after_caps = {facts['preview_rows_after_caps']}",
        f"failed_checks = {', '.join(facts['failed_checks'])}",
        "```",
        "",
        "## Interpretation",
        "",
        blocker["short_explanation"],
        "",
        "Candidate mining remains blocked because the issue is not raw row count. The issue is that the target would be dominated by too few controlled strata. Relaxing to exact subject/object or visible endpoint-pair groups would increase apparent capacity, but that uses the same shortcut axes that previous H002 audits identified as unsafe.",
        "",
        "## Recommended Next Decision",
        "",
        "Freeze v23 as diagnostic negative target-construction evidence unless the next path decision explicitly accepts a diagnostic-only branch. Do not proceed to labels or posterior smoke from this target.",
        "",
        "## Boundary",
        "",
        "- Train-only H002 hypothesis artifact.",
        "- No validation/test rows were used.",
        "- No H001 artifact was modified.",
        "- No new label was created.",
        "- Multi-view and mesh remain audit/confirmation evidence only.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    capacity_dir = as_abs(args.capacity_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    capacity = read_json(capacity_dir / "summary.json")
    validation_errors = validate_capacity(capacity)
    blocker = build_blocker(capacity)

    status = STATUS_ERROR if validation_errors else STATUS_READY
    next_todo = EXPECTED_CAPACITY_NEXT if validation_errors else NEXT_TODO_READY
    summary = {
        "schema_version": "h002_reliability_target_v23_hanging_on_positive_anchor_blocker_synthesis_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "split": "train_only",
        "blocker_synthesis": blocker,
        "boundary": {
            "validation_usage": False,
            "test_usage": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "fills_new_labels": False,
        },
        "inputs": {
            "capacity_summary": rel_path(capacity_dir / "summary.json"),
            "capacity_report": rel_path(capacity_dir / "report.md"),
        },
        "outputs": {
            "summary": rel_path(output_dir / "summary.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
            "blocker_synthesis": rel_path(output_dir / "blocker_synthesis.json"),
            "report": rel_path(output_dir / "report.md"),
        },
    }
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "blocker_synthesis.json", blocker)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    (output_dir / "report.md").write_text(build_report(summary), encoding="utf-8")

    print(f"status={status}")
    print(f"next_todo={next_todo}")
    print(f"validation_errors={len(validation_errors)}")
    print(f"root_cause={blocker['root_cause']}")
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
