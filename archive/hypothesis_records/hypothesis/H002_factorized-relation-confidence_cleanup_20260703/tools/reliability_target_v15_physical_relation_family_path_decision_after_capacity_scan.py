#!/usr/bin/env python3
"""Decide the H002 path after the v15 physical relation-family capacity scan."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_CAPACITY_DIR = RGA_ROOT / "reliability_target_v15_physical_relation_family_capacity_scan"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v15_physical_relation_family_path_decision_after_capacity_scan"

EXPECTED_CAPACITY_STATUS = "h002_reliability_target_v15_physical_relation_family_capacity_scan_blocked_capacity_or_mixed_strata"
EXPECTED_CAPACITY_NEXT = "reliability_target_v15_physical_relation_family_path_decision_after_capacity_scan"

STATUS = "h002_reliability_target_v15_physical_relation_family_path_decision_select_cross_stratum_support_contact_contrast"
SELECTED_PATH = "reject_same_witness_select_v16_cross_stratum_support_contact_contrast"
NEXT_TODO = "reliability_target_v16_cross_stratum_support_contact_contrast_plan"


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
        errors.append({"error_type": "unexpected_capacity_next_todo", "expected": EXPECTED_CAPACITY_NEXT, "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "capacity_validation_errors_present", "actual": summary.get("validation_errors")})

    boundary = summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "fills_new_labels",
        "ingests_existing_labels",
        "trains_new_posterior",
        "posterior_smoke_allowed",
        "paper_evidence_allowed",
        "h001_artifacts_modified",
        "rga_redefined_as_lh_only",
        "multi_view_as_model_input",
        "hidden_fields_as_model_input",
    ]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "capacity_boundary_violation", "key": key, "actual": boundary.get(key)})

    decision = summary.get("capacity_decision", {})
    checks = decision.get("checks", {})
    required_true = [
        "support_contact_primary_rows_available",
        "support_contact_primary_candidate_rows_after_caps",
        "relative_vertical_max_rows",
        "forbidden_visible_field_hits",
        "selection_deficits_empty",
    ]
    for key in required_true:
        if checks.get(key) is not True:
            errors.append({"error_type": "unexpected_capacity_check_failure", "key": key, "actual": checks.get(key)})
    if checks.get("minimum_mixed_witness_strata_before_label_fill") is not False:
        errors.append(
            {
                "error_type": "mixed_witness_gate_expected_to_fail",
                "expected": False,
                "actual": checks.get("minimum_mixed_witness_strata_before_label_fill"),
            }
        )
    if decision.get("support_contact_mixed_witness_strata") != 0:
        errors.append({"error_type": "unexpected_mixed_witness_count", "expected": 0, "actual": decision.get("support_contact_mixed_witness_strata")})
    if decision.get("support_contact_rows_after_caps", 0) < 200:
        errors.append({"error_type": "support_contact_capped_capacity_too_low", "expected_at_least": 200, "actual": decision.get("support_contact_rows_after_caps")})

    return errors


def build_option_matrix(capacity: dict[str, Any]) -> list[dict[str, str]]:
    decision = capacity["capacity_decision"]
    return [
        {
            "option": "run_posterior_smoke_now",
            "verdict": "reject",
            "reason": "No v15 label target exists and the capacity scan explicitly blocks label-sheet creation before path decision.",
        },
        {
            "option": "mine_v15_preview_as_label_sheet",
            "verdict": "reject",
            "reason": "The preview has enough rows but is all LH/satisfied; it would collapse into a geometry-status or bucket shortcut rather than a reliability target.",
        },
        {
            "option": "add_more_support_contact_rows",
            "verdict": "reject",
            "reason": f"Row count is not the blocker: support/contact has {decision['support_contact_rows_available']} eligible rows and {decision['support_contact_rows_after_caps']} after caps.",
        },
        {
            "option": "relax_same_witness_matching_only",
            "verdict": "reject_as_underspecified",
            "reason": "A simple relaxation would remove the failed gate without adding a replacement independence control, recreating the shortcut risk seen in v14.",
        },
        {
            "option": "keep_same_witness_hl_lh_matching",
            "verdict": "reject",
            "reason": "Same-witness HL/LH matching is structurally inconsistent with the RGA mismatch definition: HL and LH are supposed to differ in geometry status or geometry evidence.",
        },
        {
            "option": "freeze_support_contact_and_switch_to_attachment_now",
            "verdict": "defer",
            "reason": "Attachment remains a strong future probe, but support/contact capacity is sufficient; the failed assumption is the matching rule, not the family itself.",
        },
        {
            "option": "select_controlled_cross_stratum_support_contact_contrast",
            "verdict": "select",
            "reason": "This preserves H002's bidirectional mismatch thesis by treating HL and LH as different disagreement states while controlling predicate, endpoint, scan/object distribution, rank/source bands, coverage, and reason families.",
        },
    ]


def build_selected_plan(capacity: dict[str, Any]) -> dict[str, Any]:
    decision = capacity["capacity_decision"]
    selection = capacity["selection_summary"]
    return {
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "posterior_smoke_allowed": False,
        "capacity_snapshot": {
            "eligible_target_rows": capacity["counts"]["eligible_target_rows"],
            "support_contact_rows_available": decision["support_contact_rows_available"],
            "support_contact_rows_after_caps": decision["support_contact_rows_after_caps"],
            "support_contact_mixed_witness_strata": decision["support_contact_mixed_witness_strata"],
            "standing_on_capacity_after_hard_filter": decision["standing_on_capacity_after_hard_filter"],
            "standing_on_selected_after_caps": decision["standing_on_selected_after_caps"],
            "relative_vertical_selected_after_caps": decision["relative_vertical_selected_after_caps"],
            "selection_preview_rows": selection["selected_total"],
            "selection_deficits": selection["deficits"],
            "selected_by_queue": selection["selected_by_queue"],
            "selected_by_geometry_status": selection["selected_by_geometry_status"],
        },
        "core_reasoning": [
            "H002 targets semantic-geometry disagreement, so HL and LH should be contrasted as different disagreement states.",
            "Requiring HL and LH to share the same geometry witness bucket is over-constraining because the geometry axis is part of what defines the mismatch.",
            "The capacity scan shows the family is viable in count, but the same-witness gate is not viable.",
            "The next target repair must replace same-witness matching with explicit cross-stratum controls, not remove controls entirely.",
        ],
        "v16_route": {
            "name": "controlled_cross_stratum_support_contact_contrast",
            "goal": "Construct a train-only reliability target where HL and LH are allowed to occupy different RGA/witness states, while non-causal shortcuts are controlled and audited.",
            "primary_family": "support_contact",
            "primary_predicates": ["lying on"],
            "secondary_predicates": ["standing on"],
            "control_family": "relative_vertical",
            "deferred_family": "attachment_deferred",
            "why_lying_on_primary": "lying-on has both HL and LH eligible rows after hard filtering; standing-on has no eligible HL rows and should be diversity/control unless a path-specific plan proves otherwise.",
            "contrast_unit": "cross_stratum_pair_or_block",
            "contrast_definition": [
                "one side samples semantic-high / geometry-low or geometry-contradicted support-contact evidence",
                "the other side samples semantic-low / geometry-high or geometry-supported support-contact evidence",
                "the two sides do not need the same geometry status, p_geom bin, or reason signature",
                "the two sides must be matched or capped on predicate, endpoint type, object distribution, scan/subgraph distribution, coverage state, source/rank bands, and reason-family families",
            ],
        },
        "required_controls": {
            "must_control_or_audit": [
                "predicate_label",
                "source_queue_kind",
                "semantic_rank_band",
                "scan_id distribution",
                "subgraph distribution",
                "subject_object_label_pair distribution",
                "endpoint_generic_state",
                "coverage_state",
                "reason_family",
                "p_geom_bin",
                "geometry_status",
            ],
            "visible_label_surface": [
                "do not expose queue kind, hidden rank band, geometry_status, p_geom_valid, machine hint, label_match_status, or quota cell",
                "show factor-separated, non-template evidence summaries only after candidate mining defines the packet surface",
            ],
            "target_independence_required_after_label_fill": [
                "shortcut probes using queue kind only",
                "geometry-status-only probe",
                "p-geom-bin-only probe",
                "predicate/rank/source-bucket probe",
                "scan/object/pair identity probe",
                "reason-family-only probe",
                "same-family/same-rank-band controlled slice audit",
            ],
        },
        "rejected_shortcuts": [
            "do not label HL as reject and LH as accept by construction",
            "do not use geometry_support as the primary target",
            "do not make rank_band or queue_kind visible to label fill",
            "do not use multi-view as deployable input in this branch",
            "do not run posterior until label ingestion and target-independence pass",
        ],
        "attachment_policy": {
            "status": "deferred_backup_schema_probe",
            "reason": "Attachment is promising, especially with multi-view audit, but it should not replace support/contact until the corrected cross-stratum route is tested or explicitly blocked.",
        },
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    plan = summary["selected_plan"]
    snap = plan["capacity_snapshot"]
    lines = [
        "# H002 V15 Capacity Path Decision",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"next_todo = {summary['next_todo']}",
        f"posterior_smoke_allowed = {summary['boundary']['posterior_smoke_allowed']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Capacity Finding",
        "",
        "```text",
        f"support_contact_rows_available = {snap['support_contact_rows_available']}",
        f"support_contact_rows_after_caps = {snap['support_contact_rows_after_caps']}",
        f"support_contact_mixed_witness_strata = {snap['support_contact_mixed_witness_strata']}",
        f"selection_preview_rows = {snap['selection_preview_rows']}",
        f"selected_by_queue = {snap['selected_by_queue']}",
        f"selected_by_geometry_status = {snap['selected_by_geometry_status']}",
        "```",
        "",
        "## Decision",
        "",
        "Select controlled cross-stratum support/contact contrast.",
        "",
        "Same-witness HL/LH matching is rejected because H002 is explicitly about contrasting different semantic-geometry disagreement states.",
        "Requiring those states to share the same geometry witness bucket makes the target nearly impossible under the current RGA construction.",
        "",
        "## Next Route",
        "",
        "```text",
        "controlled_cross_stratum_support_contact_contrast",
        "```",
        "",
        "The next stage should define a v16 plan before candidate mining. It must specify cross-stratum block construction,",
        "visible label-surface rules, and target-independence probes before any new label sheet is generated.",
        "",
        "## Boundary",
        "",
        "This is train-only path-decision evidence. It is not a label sheet, posterior performance evidence, validation/test evidence, or paper-level benchmark evidence.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    capacity_dir = as_abs(args.capacity_dir)
    output_dir = as_abs(args.output_dir)

    capacity = read_json(capacity_dir / "summary.json")
    errors = validate_capacity(capacity)
    options = build_option_matrix(capacity)
    selected = build_selected_plan(capacity)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(output_dir / "option_matrix.jsonl", options)
    write_json(output_dir / "selected_plan.json", selected)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)

    summary = {
        "schema_version": "h002_reliability_target_v15_physical_relation_family_path_decision_after_capacity_scan_v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": STATUS if not errors else "blocked_validation_errors",
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "ingests_existing_labels": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "rga_redefined_as_lh_only": False,
            "multi_view_as_model_input": False,
            "hidden_fields_as_model_input": False,
        },
        "input_paths": {
            "capacity_summary": rel_path(capacity_dir / "summary.json"),
            "capacity_report": rel_path(capacity_dir / "report.md"),
            "quota_feasibility": rel_path(capacity_dir / "quota_feasibility.csv"),
            "mixed_witness_strata": rel_path(capacity_dir / "mixed_witness_strata_top.csv"),
        },
        "output_dir": rel_path(output_dir),
        "output_paths": {
            "summary": rel_path(output_dir / "summary.json"),
            "report": rel_path(output_dir / "report.md"),
            "option_matrix": rel_path(output_dir / "option_matrix.jsonl"),
            "selected_plan": rel_path(output_dir / "selected_plan.json"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "option_verdicts": {row["option"]: row["verdict"] for row in options},
        "selected_plan": selected,
        "interpretation": (
            "H002 should continue through a controlled cross-stratum support/contact contrast. "
            "The family has enough rows, but same-witness HL/LH matching is conceptually too strict because HL/LH are different semantic-geometry states."
        ),
    }

    write_json(output_dir / "summary.json", summary)
    write_report(output_dir / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"selected_path={summary['selected_path']}")
    print(f"next_todo={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")
    print(f"output_dir={summary['output_dir']}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
