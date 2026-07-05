#!/usr/bin/env python3
"""Plan the H002 size-relative schema/source-adapter probe."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_COVERAGE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan"
DEFAULT_SCOPE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze"
DEFAULT_3DSSG_ROOT = REPO_ROOT / "local_dataset/3DSSG"
DEFAULT_3RSCAN_ROOT = REPO_ROOT / "local_dataset/3RScan"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit"

EXPECTED_COVERAGE_STATUS = "h002_compatibility_dataset_v3_relation_family_coverage_gap_audit_after_ablation_table_plan_ready"
EXPECTED_COVERAGE_NEXT = "compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit"
EXPECTED_SCOPE_STATUS = "h002_compatibility_dataset_v3_scope_synthesis_after_support_contact_visual_mesh_diagnostic_freeze_ready"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit_v1"
STATUS_READY = "h002_compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_size_relative_schema_probe_plan_after_coverage_gap_audit_input_errors"
SELECTED_PATH = "size_relative_source_inventory_with_semseg_obb_scale_features"
NEXT_TODO = "compatibility_dataset_v3_size_relative_source_inventory_after_schema_probe_plan"

SIZE_PREDICATES = {"bigger than", "smaller than"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage-dir", type=Path, default=DEFAULT_COVERAGE_DIR)
    parser.add_argument("--scope-dir", type=Path, default=DEFAULT_SCOPE_DIR)
    parser.add_argument("--threedssg-root", type=Path, default=DEFAULT_3DSSG_ROOT)
    parser.add_argument("--threerscan-root", type=Path, default=DEFAULT_3RSCAN_ROOT)
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
    coverage: dict[str, Any],
    scope: dict[str, Any],
    family_gap: list[dict[str, str]],
    predicate_gap: list[dict[str, str]],
    roots: dict[str, Path],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if coverage.get("status") != EXPECTED_COVERAGE_STATUS:
        errors.append({"input": "coverage", "error_type": "unexpected_status", "actual": coverage.get("status")})
    if coverage.get("next_todo") != EXPECTED_COVERAGE_NEXT:
        errors.append({"input": "coverage", "error_type": "unexpected_next_todo", "actual": coverage.get("next_todo")})
    if coverage.get("validation_errors") != 0:
        errors.append({"input": "coverage", "error_type": "validation_errors_present", "actual": coverage.get("validation_errors")})
    if read_jsonl(roots["coverage"] / "validation_errors.jsonl"):
        errors.append({"input": "coverage", "error_type": "validation_error_rows_present"})
    if scope.get("status") != EXPECTED_SCOPE_STATUS:
        errors.append({"input": "scope", "error_type": "unexpected_status", "actual": scope.get("status")})
    if scope.get("validation_errors") != 0:
        errors.append({"input": "scope", "error_type": "validation_errors_present", "actual": scope.get("validation_errors")})
    if read_jsonl(roots["scope"] / "validation_errors.jsonl"):
        errors.append({"input": "scope", "error_type": "validation_error_rows_present"})
    for summary_name, summary in [("coverage", coverage), ("scope", scope)]:
        boundary = summary.get("boundary", {})
        for key in ["h001_artifacts_modified", "paper_evidence_allowed", "test_usage", "validation_usage"]:
            if key in boundary and boundary.get(key) is not False:
                errors.append({"input": summary_name, "error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})

    size_family = next((row for row in family_gap if row.get("family") == "size_relative"), None)
    if not size_family:
        errors.append({"input": "family_gap", "error_type": "missing_size_relative"})
    else:
        if size_family.get("decision") != "select_next_schema_probe":
            errors.append({"input": "family_gap", "error_type": "size_relative_not_selected", "actual": size_family.get("decision")})
        if to_int(size_family.get("gt_total")) < 1000:
            errors.append({"input": "family_gap", "error_type": "size_relative_gt_too_small", "actual": size_family.get("gt_total")})
    predicates = {row.get("predicate_label"): row for row in predicate_gap if row.get("family") == "size_relative"}
    if set(predicates) != SIZE_PREDICATES:
        errors.append({"input": "predicate_gap", "error_type": "unexpected_size_predicates", "actual": sorted(predicates)})
    for pred, row in predicates.items():
        if row.get("observed_in_train_full_gt") != "True":
            errors.append({"input": "predicate_gap", "error_type": "predicate_not_observed", "predicate": pred})
        if to_int(row.get("h002_queue_count")) != 0:
            errors.append({"input": "predicate_gap", "error_type": "predicate_already_in_queue", "predicate": pred})
    return errors


def source_adapter_plan(threedssg_root: Path, threerscan_root: Path) -> list[dict[str, Any]]:
    return [
        {
            "source_id": "3dssg_relationship_gt",
            "path": rel_path(threedssg_root / "relationships.json"),
            "required": True,
            "exists_now": (threedssg_root / "relationships.json").exists(),
            "role": "find exact `bigger than` / `smaller than` GT anchors and scan/object ids",
            "fields_needed": "scan_id; subject_id; object_id; predicate_label",
            "model_input_allowed": False,
            "notes": "GT relation labels are target/audit source, not model features.",
        },
        {
            "source_id": "3dssg_classes_and_relationships",
            "path": rel_path(threedssg_root),
            "required": True,
            "exists_now": threedssg_root.exists(),
            "role": "map relation and object class ids to text labels",
            "fields_needed": "classes.txt; relationships.txt; objects.json",
            "model_input_allowed": False,
            "notes": "Used by adapter/provenance; object class text can enter T_e only after leakage controls.",
        },
        {
            "source_id": "3rscan_semseg_obb",
            "path": rel_path(threerscan_root / "scans"),
            "required": True,
            "exists_now": (threerscan_root / "scans").exists(),
            "role": "extract object OBB axes, centroids, labels, and object ids",
            "fields_needed": "semseg.v2.json: segGroups[].obb.axesLengths; centroid; normalizedAxes",
            "model_input_allowed": True,
            "notes": "`G_e_size` derives from object geometry only and must exclude predicate/source/GT labels.",
        },
        {
            "source_id": "3rscan_instance_ply_optional",
            "path": rel_path(threerscan_root / "scans"),
            "required": False,
            "exists_now": (threerscan_root / "scans").exists(),
            "role": "optional point-level extent/robustness check when OBB is missing or unstable",
            "fields_needed": "labels.instances.align.annotated.v2.ply objectId point extents",
            "model_input_allowed": True,
            "notes": "Use only as optional robustness axis after OBB coverage is known.",
        },
    ]


def geometry_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "block": "G_e_size",
            "field": "subject_volume",
            "definition": "product of subject OBB axes lengths",
            "predicate_independent": True,
            "use": "absolute subject size evidence",
            "risk": "large room/wall/floor objects can dominate; class and structural-object filters needed",
        },
        {
            "block": "G_e_size",
            "field": "object_volume",
            "definition": "product of object OBB axes lengths",
            "predicate_independent": True,
            "use": "absolute object size evidence",
            "risk": "same as subject_volume",
        },
        {
            "block": "G_e_size",
            "field": "log_volume_ratio_subject_over_object",
            "definition": "log((subject_volume + eps) / (object_volume + eps))",
            "predicate_independent": True,
            "use": "directed pair size relation shared by bigger/smaller predicate-flip rows",
            "risk": "too easy for geometry-only unless same-G predicate-flip rows are included",
        },
        {
            "block": "G_e_size",
            "field": "log_max_extent_ratio_subject_over_object",
            "definition": "log(max(subject_axes) / max(object_axes))",
            "predicate_independent": True,
            "use": "robust scale signal for elongated objects",
            "risk": "thin/long objects may invert volume-based ordering",
        },
        {
            "block": "G_e_size",
            "field": "log_footprint_area_ratio_subject_over_object",
            "definition": "log((subject_axis_x * subject_axis_y) / (object_axis_x * object_axis_y)) after sorting horizontal axes",
            "predicate_independent": True,
            "use": "floor-area-like size signal",
            "risk": "requires stable gravity/horizontal axis convention",
        },
        {
            "block": "G_e_size",
            "field": "log_height_ratio_subject_over_object",
            "definition": "log(subject_vertical_extent / object_vertical_extent)",
            "predicate_independent": True,
            "use": "height-specific size evidence",
            "risk": "height is not always semantic size; use as ablation",
        },
        {
            "block": "G_e_size",
            "field": "size_evidence_margin",
            "definition": "max absolute log-ratio across approved size measures or calibrated aggregate margin",
            "predicate_independent": True,
            "use": "Q_e ambiguity/abstain support",
            "risk": "do not use margin as target label without recording proxy nature",
        },
        {
            "block": "Q_e_size",
            "field": "obb_available_pair",
            "definition": "both subject and object have valid nonzero OBB axes",
            "predicate_independent": True,
            "use": "p_obs / abstain",
            "risk": "Q_e is observability, not relation truth",
        },
        {
            "block": "Q_e_size",
            "field": "ambiguous_size_band",
            "definition": "absolute size ratio below threshold band",
            "predicate_independent": True,
            "use": "abstain or low-confidence rows",
            "risk": "threshold must be frozen before labels/materialization",
        },
    ]


def target_construction_rows() -> list[dict[str, Any]]:
    return [
        {
            "target_component": "positive_anchor",
            "definition": "exact GT `bigger than` / `smaller than` relation from 3DSSG/Open3DSG train-side relation file",
            "allowed_for_main": True,
            "requirements": "both endpoint OBBs available; non-structural objects preferred; size margin outside ambiguous band",
            "leakage_control": "GT label hidden from model; source/GT match field hidden",
        },
        {
            "target_component": "predicate_flip_counterfactual",
            "definition": "for the same subject/object geometry, generate the opposite predicate row as a hard negative",
            "allowed_for_main": True,
            "requirements": "same endpoint pair, identical G_e, only T_e predicate changes",
            "leakage_control": "construction flag hidden; group split keeps paired rows together",
        },
        {
            "target_component": "same_geometry_two_predicate_group",
            "definition": "group contains exactly two rows: `bigger than` and `smaller than` over identical directed pair geometry",
            "allowed_for_main": True,
            "requirements": "one compatible and one incompatible row under frozen size direction",
            "leakage_control": "geometry-only model must see identical G_e for both labels, forcing T_e x G_e interaction",
        },
        {
            "target_component": "ambiguous_band_rows",
            "definition": "pairs with small or conflicting size ratios",
            "allowed_for_main": False,
            "requirements": "reserved for Q_e/p_obs or diagnostic abstain",
            "leakage_control": "do not force accept/reject labels in ambiguity band",
        },
        {
            "target_component": "no_gt_pairs",
            "definition": "object pairs without exact size relation annotation",
            "allowed_for_main": False,
            "requirements": "can be diagnostic only unless independently audited",
            "leakage_control": "do not treat all no-GT rows as false because size relations may be incomplete",
        },
    ]


def control_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate_id": "S1",
            "name": "same-G predicate flip",
            "requirement": "every main contrast group has identical G_e for bigger/smaller rows and different T_e predicate only",
            "blocks_materialization": True,
        },
        {
            "gate_id": "S2",
            "name": "geometry-only collapse check",
            "requirement": "G_e-only baseline should be near chance on same-G predicate-flip labels",
            "blocks_promotion": True,
        },
        {
            "gate_id": "S3",
            "name": "plain concat baseline",
            "requirement": "`T_e + G_e` plain concat is reported separately from interaction C_e",
            "blocks_promotion": True,
        },
        {
            "gate_id": "S4",
            "name": "class-pair shortcut",
            "requirement": "subject/object class-pair only probe must not solve the target",
            "blocks_promotion": True,
        },
        {
            "gate_id": "S5",
            "name": "source/GT leakage",
            "requirement": "exact_match, generated_flip, GT predicate, and construction fields are hidden from model-safe rows",
            "blocks_materialization": True,
        },
        {
            "gate_id": "S6",
            "name": "ambiguous band abstain",
            "requirement": "near-equal size pairs are labeled uncertain/Q_e, not forced into binary reliability",
            "blocks_promotion": True,
        },
        {
            "gate_id": "S7",
            "name": "structural object filter",
            "requirement": "room, wall, floor, ceiling, and whole-scene structural objects are excluded or reported separately",
            "blocks_materialization": False,
        },
        {
            "gate_id": "S8",
            "name": "scan/endpoint grouped split",
            "requirement": "paired counterfactual rows stay in the same group; no endpoint leakage across folds",
            "blocks_promotion": True,
        },
    ]


def model_view_rows() -> list[dict[str, Any]]:
    return [
        {
            "view": "T_only",
            "allowed_blocks": "T_e predicate text/label; object class text if enabled",
            "purpose": "semantic-only baseline",
            "must_exclude": "source score; GT label; construction flag",
        },
        {
            "view": "G_only",
            "allowed_blocks": "G_e_size only",
            "purpose": "geometry-only collapse check",
            "must_exclude": "predicate; source score; GT label; construction flag",
        },
        {
            "view": "TG_concat",
            "allowed_blocks": "T_e + G_e_size",
            "purpose": "plain fusion baseline",
            "must_exclude": "Z_e for C_e test",
        },
        {
            "view": "C_e_interaction",
            "allowed_blocks": "T_e x G_e_size interaction",
            "purpose": "main compatibility mechanism",
            "must_exclude": "Z_e; GT label; construction flag",
        },
        {
            "view": "C_e_plus_Q",
            "allowed_blocks": "T_e x G_e_size + Q_e_size",
            "purpose": "selective decision / p_obs diagnostic",
            "must_exclude": "Q_e as truth label",
        },
        {
            "view": "final_p_rel_later",
            "allowed_blocks": "C_e + Q_e + optional Z_e",
            "purpose": "future final reliability head after C_e is established",
            "must_exclude": "not allowed in the first C_e schema probe",
        },
    ]


def next_runner_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Scan 3DSSG/Open3DSG train-side size-relative GT anchors and 3RScan semseg OBB availability before materialization.",
        "must_measure": [
            "bigger/smaller GT anchor counts",
            "scan/object id join rate against semseg.v2.json",
            "pair OBB availability",
            "size-ratio margin distribution",
            "ambiguous-band row count",
            "class-pair and structural-object mass",
            "same-G predicate-flip capacity",
        ],
        "must_not_do": [
            "do not materialize model rows yet",
            "do not use validation/test",
            "do not treat no-GT pairs as false",
            "do not put source/GT/construction labels in model-safe G_e",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    text = f"""# H002 Size-Relative Schema Probe Plan After Coverage Gap Audit

## Status

```text
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Decision

The next active H002 relation-family probe is `size_relative` with `bigger than` and
`smaller than`.

This step is a schema/source-adapter plan only. It does not materialize rows, train a
model, or promote H002 to paper evidence.

## Why Size Relative

- It adds a new physical relation family beyond vertical/support/proximity.
- It has train-side GT mass in the current inventory: `bigger than = 911`, `smaller than = 911`.
- Predicate-independent geometry evidence can be built from object OBB/extent/volume features.
- The same directed object-pair geometry can be paired with both predicates, making a clean
  `T_e x G_e` compatibility test possible.

## Core Schema

```text
T_e = predicate text/label and optional object class text
G_e_size = OBB/extent/volume/area/height ratios, excluding predicate and source score
Q_e_size = OBB availability and ambiguous-size-band evidence
C_e = compatibility(T_e, G_e_size), excluding Z_e
```

## Key Control

The main contrast must use same-G predicate-flip rows:

```text
same subject/object geometry
row 1: predicate = bigger than
row 2: predicate = smaller than
```

If `G_e` is identical for both rows, geometry-only should not solve the binary compatibility
target. The improvement must come from predicate-geometry interaction.

## Main Risk

Size-relative can collapse into a trivial size-threshold verifier. This is acceptable as a
diagnostic, but not enough for H002's compatibility claim. The next source inventory must
therefore measure same-G predicate-flip capacity and geometry-only shortcut risk before
materialization.

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
        "coverage": args.coverage_dir,
        "scope": args.scope_dir,
    }
    coverage_summary = read_json(args.coverage_dir / "summary.json")
    scope_summary = read_json(args.scope_dir / "summary.json")
    family_gap = read_csv(args.coverage_dir / "family_coverage_gap.csv")
    predicate_gap = read_csv(args.coverage_dir / "predicate_coverage_gap.csv")

    validation_errors = validate_inputs(coverage_summary, scope_summary, family_gap, predicate_gap, roots)

    size_predicate_rows = [
        row for row in predicate_gap if row.get("family") == "size_relative" and row.get("predicate_label") in SIZE_PREDICATES
    ]
    gt_counts = {row["predicate_label"]: to_int(row.get("open3dsg_train_full_gt_count")) for row in size_predicate_rows}

    source_rows = source_adapter_plan(args.threedssg_root, args.threerscan_root)
    geometry_rows = geometry_schema_rows()
    target_rows = target_construction_rows()
    control_rows = control_gate_rows()
    model_rows = model_view_rows()
    contract = next_runner_contract()

    if not all(row["exists_now"] for row in source_rows if row["required"]):
        missing = [row["source_id"] for row in source_rows if row["required"] and not row["exists_now"]]
        validation_errors.append({"error_type": "required_source_missing", "missing": missing})
    if set(gt_counts) != SIZE_PREDICATES or min(gt_counts.values() or [0]) < 500:
        validation_errors.append({"error_type": "size_gt_count_insufficient", "gt_counts": gt_counts})
    if not any(row["target_component"] == "predicate_flip_counterfactual" for row in target_rows):
        validation_errors.append({"error_type": "missing_predicate_flip_target"})
    if not any(row["name"] == "geometry-only collapse check" for row in control_rows):
        validation_errors.append({"error_type": "missing_geometry_only_control"})
    if not any(row["view"] == "C_e_interaction" for row in model_rows):
        validation_errors.append({"error_type": "missing_interaction_model_view"})

    status = STATUS_READY if not validation_errors else STATUS_ERRORS

    outputs = {
        "source_adapter_plan": args.output_dir / "source_adapter_plan.csv",
        "geometry_evidence_schema": args.output_dir / "geometry_evidence_schema.csv",
        "target_construction_plan": args.output_dir / "target_construction_plan.csv",
        "control_gate_table": args.output_dir / "control_gate_table.csv",
        "model_view_contract": args.output_dir / "model_view_contract.csv",
        "next_runner_contract": args.output_dir / "next_runner_contract.json",
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
        "input_paths": {
            "coverage": rel_path(args.coverage_dir),
            "scope": rel_path(args.scope_dir),
            "threedssg_root": rel_path(args.threedssg_root),
            "threerscan_root": rel_path(args.threerscan_root),
        },
        "output_paths": {key: rel_path(value) for key, value in outputs.items()},
        "boundary": {
            "split": "train_only_schema_probe_plan",
            "h001_artifacts_modified": False,
            "trains_new_model": False,
            "runs_new_learned_smoke": False,
            "materializes_rows": False,
            "paper_evidence_allowed": False,
            "validation_usage": False,
            "test_usage": False,
        },
        "size_relative_scope": {
            "family": "size_relative",
            "predicates": sorted(SIZE_PREDICATES),
            "gt_counts": gt_counts,
            "current_h002_queue_count": sum(to_int(row.get("h002_queue_count")) for row in size_predicate_rows),
            "schema_probe_goal": "test whether same-G predicate-flip size relations require T_e x G_e compatibility",
        },
        "counts": {
            "source_adapter_rows": len(source_rows),
            "geometry_schema_rows": len(geometry_rows),
            "target_construction_rows": len(target_rows),
            "control_gate_rows": len(control_rows),
            "model_view_rows": len(model_rows),
        },
        "claim_boundary": {
            "materialization_allowed_now": False,
            "paper_evidence_allowed_now": False,
            "geometry_only_success_counts_as_main_claim": False,
            "no_gt_as_negative_allowed": False,
        },
    }

    write_csv(outputs["source_adapter_plan"], source_rows)
    write_csv(outputs["geometry_evidence_schema"], geometry_rows)
    write_csv(outputs["target_construction_plan"], target_rows)
    write_csv(outputs["control_gate_table"], control_rows)
    write_csv(outputs["model_view_contract"], model_rows)
    write_json(outputs["next_runner_contract"], contract)
    write_report(outputs["report"], summary_out)
    write_json(outputs["summary"], summary_out)
    write_jsonl(outputs["validation_errors"], validation_errors)

    print(json.dumps(summary_out, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
