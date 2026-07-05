#!/usr/bin/env python3
"""Audit remaining relation-family coverage after the H002 candidate table plan."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_ABLATION_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis"
DEFAULT_SCOPE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze"
DEFAULT_CAPACITY_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relation_family_generalization_capacity_scan"
DEFAULT_MULTI_FAMILY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview"
)
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan"

EXPECTED_ABLATION_STATUS = "h002_compatibility_dataset_v3_ablation_and_table_plan_after_multi_family_synthesis_ready"
EXPECTED_ABLATION_NEXT = "compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan"
EXPECTED_SCOPE_STATUS = "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_ready"
EXPECTED_CAPACITY_STATUS = "h002_compatibility_dataset_v3_relation_family_generalization_capacity_scan_ready"
EXPECTED_MULTI_FAMILY_STATUS = (
    "h002_compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview_ready"
)

SCHEMA_VERSION = "h002_compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan_v1"
STATUS_READY = "h002_compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan_input_errors"
SELECTED_PATH = "select_size_relative_schema_probe_keep_horizontal_reference_frame_protocol_second"
NEXT_TODO = "compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ablation-dir", type=Path, default=DEFAULT_ABLATION_DIR)
    parser.add_argument("--scope-dir", type=Path, default=DEFAULT_SCOPE_DIR)
    parser.add_argument("--capacity-dir", type=Path, default=DEFAULT_CAPACITY_DIR)
    parser.add_argument("--multi-family-dir", type=Path, default=DEFAULT_MULTI_FAMILY_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def to_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def validate_inputs(
    ablation: dict[str, Any],
    scope: dict[str, Any],
    capacity: dict[str, Any],
    multi_family: dict[str, Any],
    all_relation_rows: list[dict[str, str]],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = {
        "ablation": (ablation, EXPECTED_ABLATION_STATUS),
        "scope": (scope, EXPECTED_SCOPE_STATUS),
        "capacity": (capacity, EXPECTED_CAPACITY_STATUS),
        "multi_family": (multi_family, EXPECTED_MULTI_FAMILY_STATUS),
    }
    for name, (summary, status) in expected.items():
        if summary.get("status") != status:
            errors.append({"input": name, "error_type": "unexpected_status", "actual": summary.get("status")})
        if summary.get("validation_errors") != 0:
            errors.append({"input": name, "error_type": "validation_errors_present", "actual": summary.get("validation_errors")})
        rows = read_jsonl(roots[name] / "validation_errors.jsonl")
        if rows:
            errors.append({"input": name, "error_type": "validation_error_rows_present", "rows": len(rows)})
        boundary = summary.get("boundary", {})
        for key in ["h001_artifacts_modified", "paper_evidence_allowed", "test_usage", "validation_usage"]:
            if key in boundary and boundary.get(key) is not False:
                errors.append({"input": name, "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if ablation.get("next_todo") != EXPECTED_ABLATION_NEXT:
        errors.append({"input": "ablation", "error_type": "unexpected_next_todo", "actual": ablation.get("next_todo")})
    families = {row.get("family") for row in all_relation_rows}
    required_families = {
        "relative_vertical",
        "support_contact",
        "proximity",
        "relative_horizontal",
        "attachment_deferred",
        "containment_in",
        "size_relative",
        "part_structural",
        "identity_symmetry",
    }
    missing = sorted(required_families - families)
    if missing:
        errors.append({"input": "all_relation_types", "error_type": "missing_required_families", "missing": missing})
    return errors


def aggregate_families(all_relation_rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "family": "",
        "predicates": [],
        "gt_total": 0,
        "queue_total": 0,
        "hl_total": 0,
        "lh_total": 0,
        "covered_predicates": 0,
        "observed_predicates": 0,
        "missing_predicates": [],
    })
    for row in all_relation_rows:
        family = row["family"]
        group = grouped[family]
        group["family"] = family
        predicate = row["predicate_label"]
        group["predicates"].append(predicate)
        group["gt_total"] += to_int(row.get("open3dsg_train_full_gt_count"))
        group["queue_total"] += to_int(row.get("h002_queue_count"))
        group["hl_total"] += to_int(row.get("h002_hl_count"))
        group["lh_total"] += to_int(row.get("h002_lh_count"))
        if row.get("in_current_h002_queue") == "True":
            group["covered_predicates"] += 1
        else:
            group["missing_predicates"].append(predicate)
        if row.get("observed_in_train_full_gt") == "True":
            group["observed_predicates"] += 1
    return grouped


def family_capacity_map(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row["family"]: row for row in rows}


def family_decision(family: str, group: dict[str, Any], capacity: dict[str, str] | None) -> dict[str, Any]:
    predicates = "; ".join(group["predicates"])
    coverage = f"{group['covered_predicates']}/{len(group['predicates'])}"
    cap_verdict = (capacity or {}).get("verdict", "")
    cap_next = (capacity or {}).get("next_action", "")

    decisions = {
        "relative_vertical": {
            "coverage_class": "covered_current_anchor",
            "paper_role": "candidate main mechanism anchor",
            "decision": "keep_current_anchor_no_new_probe_now",
            "evidence_need": "signed vertical geometry already available",
            "risk": "too clean if used alone; needs another family and held-out reproduction",
            "next_action": "retain as anchor while auditing other families",
            "priority": 3,
        },
        "support_contact": {
            "coverage_class": "covered_but_caveated",
            "paper_role": "candidate main compatibility route with caveat",
            "decision": "keep_caveated_do_not_claim_solved",
            "evidence_need": "point/contact/pose geometry plus Q_e/p_obs separation",
            "risk": "standing/lying ambiguity; supported-by superordinate overlap; near-threshold aggregate",
            "next_action": "no grouped rerun; only targeted failure or per-predicate repair if needed",
            "priority": 4,
        },
        "proximity": {
            "coverage_class": "covered_geometry_easy",
            "paper_role": "diagnostic/generality control",
            "decision": "keep_diagnostic_not_main_Ce",
            "evidence_need": "distance/scale/coverage controls",
            "risk": "distance-only or p_geom_valid-only can solve the current target",
            "next_action": "use as geometry-easy route evidence, not final compatibility proof",
            "priority": 5,
        },
        "relative_horizontal": {
            "coverage_class": "missing_high_gt_reference_frame",
            "paper_role": "future high-value family",
            "decision": "reference_frame_protocol_required_before_target",
            "evidence_need": "viewer/world/camera/reference-frame contract and horizontal geometry adapter",
            "risk": "left/right/front/behind semantics can flip with reference frame",
            "next_action": "write reference-frame protocol before materialization",
            "priority": 2,
        },
        "attachment_deferred": {
            "coverage_class": "missing_observability_heavy",
            "paper_role": "future/diagnostic observability-heavy family",
            "decision": "source_adapter_and_visual_mesh_evidence_needed",
            "evidence_need": "visual/mesh contact, multi-view visibility, attachment-point evidence, Q_e",
            "risk": "target independence and visual observability bottleneck",
            "next_action": "defer until deployable visual/mesh evidence source is defined",
            "priority": 6,
        },
        "size_relative": {
            "coverage_class": "missing_but_low_cost_geometry",
            "paper_role": "next active probe candidate",
            "decision": "select_next_schema_probe",
            "evidence_need": "object scale/volume/height/area geometry independent of predicate",
            "risk": "may become geometry-easy like vertical/proximity unless same-geometry bigger/smaller contrast is controlled",
            "next_action": "create size_relative schema/source-adapter probe plan",
            "priority": 1,
        },
        "containment_in": {
            "coverage_class": "missing_low_gt_containment",
            "paper_role": "future containment route",
            "decision": "future_schema_probe_not_immediate",
            "evidence_need": "3D containment ratio, object-in-container support, visibility/occlusion handling",
            "risk": "low GT count and annotation ambiguity",
            "next_action": "defer until size/horizontal gap is assessed",
            "priority": 7,
        },
        "part_structural": {
            "coverage_class": "missing_semantic_structural",
            "paper_role": "diagnostic/out-of-scope candidate",
            "decision": "do_not_use_as_main_geometry_compatibility_now",
            "evidence_need": "part-whole ontology and structural segmentation, not simple physical geometry",
            "risk": "can turn into semantic ontology prediction rather than geometry compatibility",
            "next_action": "keep in coverage table only",
            "priority": 8,
        },
        "identity_symmetry": {
            "coverage_class": "missing_identity_semantic",
            "paper_role": "out-of-scope or separate semantic identity task",
            "decision": "exclude_from_current_physical_compatibility_claim",
            "evidence_need": "instance identity/symmetry reasoning rather than relation-level physical compatibility",
            "risk": "not aligned with H002 predicate-geometry compatibility claim",
            "next_action": "mark out-of-scope for current H002",
            "priority": 9,
        },
        "background_none": {
            "coverage_class": "no_relation_background",
            "paper_role": "out-of-scope",
            "decision": "exclude",
            "evidence_need": "none",
            "risk": "not a relation family",
            "next_action": "ignore for H002 relation-family coverage",
            "priority": 10,
        },
    }
    base = decisions.get(family, {
        "coverage_class": "unclassified",
        "paper_role": "unknown",
        "decision": "manual_review_needed",
        "evidence_need": "unknown",
        "risk": "unknown",
        "next_action": "manual review",
        "priority": 99,
    })
    return {
        "family": family,
        "predicates": predicates,
        "gt_total": group["gt_total"],
        "queue_total": group["queue_total"],
        "hl_total": group["hl_total"],
        "lh_total": group["lh_total"],
        "covered_predicates": coverage,
        "missing_predicates": "; ".join(group["missing_predicates"]),
        "capacity_scan_verdict": cap_verdict,
        "capacity_scan_next_action": cap_next,
        **base,
    }


def predicate_gap_rows(all_relation_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in all_relation_rows:
        queue = to_int(row.get("h002_queue_count"))
        gt = to_int(row.get("open3dsg_train_full_gt_count"))
        family = row["family"]
        if queue > 0:
            coverage_status = "in_current_h002_queue"
        elif family == "relative_horizontal":
            coverage_status = "missing_reference_frame_protocol"
        elif family == "size_relative":
            coverage_status = "missing_low_cost_geometry_adapter"
        elif family == "attachment_deferred":
            coverage_status = "missing_visual_mesh_observability_adapter"
        elif family in {"part_structural", "identity_symmetry"}:
            coverage_status = "semantic_or_structural_not_immediate_main"
        elif gt > 0:
            coverage_status = "missing_source_adapter_or_schema"
        else:
            coverage_status = "not_observed_or_out_of_scope"
        rows.append({
            "predicate_label": row["predicate_label"],
            "family": family,
            "open3dsg_train_full_gt_count": gt,
            "h002_queue_count": queue,
            "h002_hl_count": to_int(row.get("h002_hl_count")),
            "h002_lh_count": to_int(row.get("h002_lh_count")),
            "in_current_h002_queue": row.get("in_current_h002_queue"),
            "observed_in_train_full_gt": row.get("observed_in_train_full_gt"),
            "coverage_status": coverage_status,
        })
    return rows


def next_probe_priority_rows(family_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected = sorted(family_rows, key=lambda row: int(row["priority"]))
    return [
        {
            "rank": idx + 1,
            "family": row["family"],
            "predicates": row["predicates"],
            "gt_total": row["gt_total"],
            "queue_total": row["queue_total"],
            "decision": row["decision"],
            "reason": row["risk"],
            "next_action": row["next_action"],
        }
        for idx, row in enumerate(selected)
    ]


def write_report(path: Path, summary: dict[str, Any], family_rows: list[dict[str, Any]]) -> None:
    next_probe = next(row for row in family_rows if row["priority"] == 1)
    horizontal = next(row for row in family_rows if row["family"] == "relative_horizontal")
    text = f"""# H002 Relation-Family Coverage Gap Audit After Ablation/Table Plan

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Decision

The previous table plan is a candidate ablation contract, not a final main table.
Before paper-level promotion, H002 must show which relation families are covered,
which are diagnostic, and which require new source adapters or geometry evidence schemas.

## Coverage Summary

Current H002 queue covers only a subset of Open3DSG/3DSSG relation types:

- covered/current: `relative_vertical`, `support_contact`, `proximity`
- missing but high-value: `relative_horizontal`
- missing but low-cost geometry probe: `size_relative`
- missing observability-heavy: `attachment_deferred`
- future/deferred: `containment_in`
- diagnostic/out-of-scope for current physical compatibility: `part_structural`, `identity_symmetry`

## Selected Next Probe

```text
family = {next_probe['family']}
predicates = {next_probe['predicates']}
decision = {next_probe['decision']}
next_action = {next_probe['next_action']}
```

Rationale: `size_relative` gives a new physical relation family with a simple geometry-only
evidence schema, while still allowing a predicate-pair compatibility test (`bigger than` vs
`smaller than`). It is lower-cost than horizontal relations because it does not require a
reference-frame convention.

## High-Value Gap

```text
family = {horizontal['family']}
predicates = {horizontal['predicates']}
gt_total = {horizontal['gt_total']}
decision = {horizontal['decision']}
```

`relative_horizontal` has the largest GT mass, but it should not be mined before a reference-frame
protocol is defined.

## Claim Boundary

H002 should not claim all-family generality yet. The current claim remains:

```text
train-only relation-aware predicate-geometry compatibility routing hypothesis
```

The final main table remains blocked until the missing family coverage decisions and at least one
additional active family probe are resolved.

## Next

```text
{summary['next_todo']}
```
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    roots = {
        "ablation": args.ablation_dir,
        "scope": args.scope_dir,
        "capacity": args.capacity_dir,
        "multi_family": args.multi_family_dir,
    }
    ablation_summary = read_json(args.ablation_dir / "summary.json")
    scope_summary = read_json(args.scope_dir / "summary.json")
    capacity_summary = read_json(args.capacity_dir / "summary.json")
    multi_family_summary = read_json(args.multi_family_dir / "summary.json")
    all_relation_rows = read_csv(args.scope_dir / "all_relation_types.csv")
    capacity_rows = read_csv(args.capacity_dir / "family_capacity.csv")

    validation_errors = validate_inputs(
        ablation_summary,
        scope_summary,
        capacity_summary,
        multi_family_summary,
        all_relation_rows,
        roots,
    )

    capacity_by_family = family_capacity_map(capacity_rows)
    grouped = aggregate_families(all_relation_rows)
    family_rows = [
        family_decision(family, grouped[family], capacity_by_family.get(family))
        for family in sorted(grouped)
    ]
    family_rows.sort(key=lambda row: int(row["priority"]))
    predicate_rows = predicate_gap_rows(all_relation_rows)
    priority_rows = next_probe_priority_rows(family_rows)

    selected_next = priority_rows[0]
    if selected_next["family"] != "size_relative":
        validation_errors.append({"error_type": "unexpected_selected_next_family", "actual": selected_next})
    if not any(row["family"] == "relative_horizontal" and row["gt_total"] > 30000 for row in family_rows):
        validation_errors.append({"error_type": "relative_horizontal_high_value_gap_missing"})
    if not any(row["family"] == "attachment_deferred" and row["queue_total"] == 0 for row in family_rows):
        validation_errors.append({"error_type": "attachment_deferred_gap_missing"})

    status = STATUS_READY if not validation_errors else STATUS_ERRORS

    outputs = {
        "family_coverage_gap": args.output_dir / "family_coverage_gap.csv",
        "predicate_coverage_gap": args.output_dir / "predicate_coverage_gap.csv",
        "next_probe_priority": args.output_dir / "next_probe_priority.csv",
        "report": args.output_dir / "report.md",
        "summary": args.output_dir / "summary.json",
        "validation_errors": args.output_dir / "validation_errors.jsonl",
    }
    summary_out = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": SELECTED_PATH,
        "next_todo": NEXT_TODO,
        "validation_errors": len(validation_errors),
        "input_paths": {name: rel_path(path) for name, path in roots.items()},
        "output_paths": {key: rel_path(value) for key, value in outputs.items()},
        "boundary": {
            "split": "train_only_coverage_gap_audit",
            "h001_artifacts_modified": False,
            "trains_new_model": False,
            "runs_new_learned_smoke": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "validation_usage": False,
            "test_usage": False,
        },
        "counts": {
            "families": len(family_rows),
            "predicates": len(predicate_rows),
            "families_in_current_queue": sum(1 for row in family_rows if row["queue_total"] > 0),
            "families_missing_current_queue": sum(1 for row in family_rows if row["queue_total"] == 0),
            "gt_total_all_rows": sum(row["gt_total"] for row in family_rows),
            "queue_total_all_rows": sum(row["queue_total"] for row in family_rows),
        },
        "selected_next_probe": selected_next,
        "claim_boundary": {
            "candidate_tables_are_final_main_tables": False,
            "docker_promotion_allowed_now": False,
            "all_family_generality_allowed": False,
            "needed_before_final_main_table": [
                "size_relative schema/source-adapter probe",
                "relative_horizontal reference-frame protocol decision",
                "explicit diagnostic/future boundary for attachment, containment, part, and identity families",
            ],
        },
    }

    write_csv(outputs["family_coverage_gap"], family_rows)
    write_csv(outputs["predicate_coverage_gap"], predicate_rows)
    write_csv(outputs["next_probe_priority"], priority_rows)
    write_report(outputs["report"], summary_out, family_rows)
    write_json(outputs["summary"], summary_out)
    write_jsonl(outputs["validation_errors"], validation_errors)

    print(json.dumps(summary_out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
