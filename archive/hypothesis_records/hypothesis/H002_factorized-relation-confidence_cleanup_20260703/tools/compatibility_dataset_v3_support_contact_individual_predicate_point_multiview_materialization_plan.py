#!/usr/bin/env python3
"""Plan G_e/Q_e materialization for support/contact individual predicates."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SOURCE_INVENTORY_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory"
)
DEFAULT_CANDIDATE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan"
)

EXPECTED_SOURCE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory_ready_for_materialization_plan"
)
EXPECTED_SOURCE_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan"

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan_ready"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization_plan_input_errors"
)
SELECTED_PATH = "plan_gq_separated_materialization_with_controls"
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization"

MAIN_PREDICATES = {"standing on", "lying on"}
DIAGNOSTIC_PREDICATES = {"supported by"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path | None) -> str:
    if path is None:
        return ""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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
                fields.append(key)
                seen.add(key)
    if not fields:
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    source_summary: dict[str, Any],
    source_errors: list[dict[str, Any]],
    inventory_rows: list[dict[str, Any]],
    source_manifest: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if source_summary.get("status") != EXPECTED_SOURCE_STATUS:
        errors.append(
            {
                "input": "source_inventory_summary",
                "error_type": "unexpected_status",
                "actual": source_summary.get("status"),
                "expected": EXPECTED_SOURCE_STATUS,
            }
        )
    if source_summary.get("next_todo") != EXPECTED_SOURCE_NEXT:
        errors.append(
            {
                "input": "source_inventory_summary",
                "error_type": "unexpected_next_todo",
                "actual": source_summary.get("next_todo"),
                "expected": EXPECTED_SOURCE_NEXT,
            }
        )
    if source_summary.get("validation_errors") != 0:
        errors.append(
            {
                "input": "source_inventory_summary",
                "error_type": "validation_errors_present",
                "actual": source_summary.get("validation_errors"),
            }
        )
    if source_errors:
        errors.append({"input": "source_validation_errors", "error_type": "rows_present", "rows": len(source_errors)})
    if len(inventory_rows) != 800:
        errors.append({"input": "inventory_rows", "error_type": "unexpected_row_count", "actual": len(inventory_rows), "expected": 800})
    if len(source_manifest) != len(inventory_rows):
        errors.append(
            {
                "input": "source_manifest",
                "error_type": "row_count_mismatch",
                "actual": len(source_manifest),
                "expected": len(inventory_rows),
            }
        )
    if len(candidate_rows) != 800:
        errors.append({"input": "candidate_rows", "error_type": "unexpected_row_count", "actual": len(candidate_rows), "expected": 800})
    boundary = source_summary.get("boundary", {})
    for key in [
        "validation_usage",
        "test_usage",
        "h001_artifacts_modified",
        "runs_learned_smoke",
        "trains_new_model",
        "paper_evidence_allowed",
        "visual_model_input_allowed",
    ]:
        if boundary.get(key) is not False:
            errors.append(
                {
                    "input": "source_inventory_summary",
                    "error_type": "boundary_not_false",
                    "key": key,
                    "actual": boundary.get(key),
                }
            )
    inv = source_summary.get("inventory_summary", {})
    if float(inv.get("g_e_point_mesh_ready_rate", 0.0) or 0.0) < 0.95:
        errors.append({"input": "source_inventory_summary", "error_type": "g_e_readiness_below_gate", "actual": inv.get("g_e_point_mesh_ready_rate")})
    if int(inv.get("q_e_state_count", 0) or 0) < 3:
        errors.append({"input": "source_inventory_summary", "error_type": "q_e_state_count_below_gate", "actual": inv.get("q_e_state_count")})
    return errors


def feature_blocks() -> list[dict[str, Any]]:
    return [
        {
            "block": "T_e",
            "factor": "semantic_content",
            "materialize_now": True,
            "model_input_scope": "C_e and diagnostic baselines",
            "fields": "predicate_text; predicate_family; subject_class_text; object_class_text",
            "source": "candidate model-safe row",
            "forbidden": "source score/rank; GT match; geometry status",
        },
        {
            "block": "G_e_obb_baseline",
            "factor": "geometry_evidence",
            "materialize_now": True,
            "model_input_scope": "baseline and ablation",
            "fields": "current semseg OBB pose/contact numeric features",
            "source": "current candidate model_safe_view G_e_mesh_pose_contact",
            "forbidden": "predicate label; source score/rank; target label",
        },
        {
            "block": "G_e_point_pose",
            "factor": "geometry_evidence",
            "materialize_now": True,
            "model_input_scope": "main G_e candidate",
            "fields": "point counts; PCA axes; uprightness; horizontalness; extent ratios; bottom/top band stats",
            "source": "labels.instances.align.annotated.v2.ply; semseg.v2.json",
            "forbidden": "predicate label; source score/rank; target label; hidden construction fields",
        },
        {
            "block": "G_e_contact_patch",
            "factor": "geometry_evidence",
            "materialize_now": True,
            "model_input_scope": "main G_e candidate",
            "fields": "surface gap histogram; near-contact point count; bottom support overlap; local support normal stats; contact patch area proxy",
            "source": "aligned instance PLY; mesh.refined.v2.obj; mesh segmentation",
            "forbidden": "predicate label; source score/rank; target label; visual label",
        },
        {
            "block": "Q_e_observability",
            "factor": "evidence_quality",
            "materialize_now": True,
            "model_input_scope": "p_obs and TGQ diagnostic, not relation truth by itself",
            "fields": "point availability; segment count; crop count; co-visible view count; crop quality score; missing/conflict flags; q_e_state_plan",
            "source": "source inventory; multi_view file metadata; mesh/point availability",
            "forbidden": "relation correctness; candidate role as input; GT match status; source rank as quality proxy",
        },
        {
            "block": "V_mv_audit_manifest",
            "factor": "audit_or_optional_later_visual",
            "materialize_now": True,
            "model_input_scope": "audit/Q_e first only",
            "fields": "subject/object crop paths; co-visible view ids; crop metadata; packet path",
            "source": "multi_view directory and sequence assets",
            "forbidden": "learned visual embedding before wrong-view/shuffled-view controls",
        },
        {
            "block": "Z_e_safe",
            "factor": "source_confidence",
            "materialize_now": "optional_manifest_only",
            "model_input_scope": "final p_rel ablation only, excluded from C_e",
            "fields": "source score; rank band; source id",
            "source": "hidden manifest/source metadata",
            "forbidden": "C_e compatibility head input",
        },
    ]


def model_views() -> list[dict[str, Any]]:
    return [
        {
            "view": "T_only",
            "feature_blocks": "T_e",
            "purpose": "semantic-only baseline",
            "allowed_for_C_e": True,
            "visual_input": False,
        },
        {
            "view": "G_obb_only",
            "feature_blocks": "G_e_obb_baseline",
            "purpose": "current OBB-only diagnostic baseline",
            "allowed_for_C_e": True,
            "visual_input": False,
        },
        {
            "view": "G_point_pose_only",
            "feature_blocks": "G_e_point_pose",
            "purpose": "point-pose geometry-only ablation",
            "allowed_for_C_e": True,
            "visual_input": False,
        },
        {
            "view": "G_contact_patch_only",
            "feature_blocks": "G_e_contact_patch",
            "purpose": "mesh/contact geometry-only ablation",
            "allowed_for_C_e": True,
            "visual_input": False,
        },
        {
            "view": "G_point_mesh_full",
            "feature_blocks": "G_e_point_pose + G_e_contact_patch",
            "purpose": "new geometry-only evidence baseline",
            "allowed_for_C_e": True,
            "visual_input": False,
        },
        {
            "view": "T_plus_G_point_mesh",
            "feature_blocks": "T_e + G_e_point_pose + G_e_contact_patch",
            "purpose": "main C_e compatibility view",
            "allowed_for_C_e": True,
            "visual_input": False,
        },
        {
            "view": "T_plus_G_plus_Q",
            "feature_blocks": "T_e + G_e_point_pose + G_e_contact_patch + Q_e_observability",
            "purpose": "observability-aware diagnostic; Q_e should not directly define truth",
            "allowed_for_C_e": "diagnostic",
            "visual_input": "metadata_only",
        },
        {
            "view": "Z_plus_C_plus_Q_later",
            "feature_blocks": "Z_e_safe + C_e_output + Q_e_observability",
            "purpose": "later p_rel/p_obs decision, not this materialization",
            "allowed_for_C_e": False,
            "visual_input": False,
        },
    ]


def controls() -> list[dict[str, Any]]:
    return [
        {
            "control": "obb_only_baseline",
            "required_after_materialization": True,
            "definition": "reuse current OBB features without point/contact features",
            "expected": "new point/mesh C_e should beat this to justify evidence expansion",
        },
        {
            "control": "point_only_ablation",
            "required_after_materialization": True,
            "definition": "use point-pose features without mesh/contact patch features",
            "expected": "identifies whether pose alone explains standing/lying",
        },
        {
            "control": "mesh_contact_only_ablation",
            "required_after_materialization": True,
            "definition": "use contact patch and support surface features without point-pose features",
            "expected": "identifies whether contact alone explains standing/lying",
        },
        {
            "control": "wrong_pair_geometry",
            "required_after_materialization": True,
            "definition": "replace G_e with geometry from another object pair matched by predicate/family where possible",
            "expected": "C_e should degrade clearly",
        },
        {
            "control": "shuffled_geometry_global",
            "required_after_materialization": True,
            "definition": "shuffle G_e across all rows",
            "expected": "C_e should degrade toward chance",
        },
        {
            "control": "shuffled_geometry_within_predicate",
            "required_after_materialization": True,
            "definition": "shuffle G_e within each predicate",
            "expected": "tests paired-geometry dependence beyond predicate shortcut",
        },
        {
            "control": "wrong_view",
            "required_after_materialization": True,
            "definition": "replace multiview metadata/packet with another row's view metadata before any visual feature is used",
            "expected": "visual/Q_e contribution should degrade if view evidence matters",
        },
        {
            "control": "shuffled_view",
            "required_after_materialization": True,
            "definition": "shuffle view metadata within predicate or class-pair",
            "expected": "prevents multiview shortcut claims without paired view evidence",
        },
        {
            "control": "class_pair_rank_source_probe",
            "required_after_materialization": True,
            "definition": "predict labels from predicate, class pair, rank band, and source metadata only",
            "expected": "must not explain the target better than the main C_e view",
        },
    ]


def blocked_fields() -> list[dict[str, Any]]:
    blocked = [
        ("scan_id", "source_manifest", "identity/provenance, not model input"),
        ("subgraph_id", "source_manifest", "identity/provenance, not model input"),
        ("subject_id", "source_manifest", "instance id shortcut risk"),
        ("object_id", "source_manifest", "instance id shortcut risk"),
        ("source path", "source_manifest", "scan/source identity leakage"),
        ("candidate_role", "hidden_manifest", "constructed target role"),
        ("label_match_status", "hidden_manifest", "GT construction proxy"),
        ("queue_kind", "hidden_manifest", "HL/LH construction proxy"),
        ("machine_hint", "hidden_manifest", "label-construction hint"),
        ("matched_gt_ids", "hidden_manifest", "GT leakage"),
        ("matched_predicates", "hidden_manifest", "GT predicate leakage"),
        ("geometry_status", "hidden_manifest", "construction geometry status"),
        ("p_geom_valid", "hidden_manifest", "H001 baseline/teacher only, not C_e input"),
        ("semantic_rank", "hidden_manifest", "Z_e only; excluded from C_e"),
        ("semantic_score", "hidden_manifest", "Z_e only; excluded from C_e"),
        ("review label", "future audit", "label-only field"),
        ("learned visual embedding", "future visual encoder", "blocked until wrong-view/shuffled-view controls pass"),
    ]
    return [{"field": field, "source": source, "reason": reason, "model_safe": False} for field, source, reason in blocked]


def output_schema() -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_output_schema",
        "planned_files": {
            "model_safe_view.jsonl": {
                "description": "rows with T_e, G_e_obb_baseline, G_e_point_pose, G_e_contact_patch, Q_e_observability, labels",
                "model_input_allowed": True,
            },
            "source_manifest.jsonl": {
                "description": "hidden source paths and scan/object ids for reproducibility",
                "model_input_allowed": False,
            },
            "visual_audit_manifest.jsonl": {
                "description": "multiview crop metadata and packet paths for audit/Q_e",
                "model_input_allowed": "metadata-only Q_e after controls; no learned image embeddings",
            },
            "control_manifest.jsonl": {
                "description": "wrong-pair, shuffled-geometry, wrong-view, and shuffled-view pairings",
                "model_input_allowed": "control-only",
            },
            "feature_stats.json": {
                "description": "finite/missing/range statistics by feature block",
                "model_input_allowed": False,
            },
            "validation_errors.jsonl": {
                "description": "materialization validation errors",
                "model_input_allowed": False,
            },
        },
        "model_safe_feature_blocks": {
            "T_e": ["predicate_text", "predicate_family", "subject_class_text", "object_class_text"],
            "G_e_obb_baseline": "current OBB pose/contact numeric fields",
            "G_e_point_pose": "point-derived pose/orientation numeric fields",
            "G_e_contact_patch": "local support/contact numeric fields",
            "Q_e_observability": "availability, quality, view-count, and q-state fields",
        },
        "label_blocks": {
            "C_e": "main compatibility label for standing/lying rows",
            "p_obs": "observable/limited/uncertain plan, not relation truth",
            "p_rel": "existing accept/reject/diagnostic label, not used to build G_e",
        },
    }


def runner_contract() -> dict[str, Any]:
    return {
        "schema_version": f"{SCHEMA_VERSION}_runner_contract",
        "next_todo": NEXT_TODO,
        "input_files": [
            "source_inventory/inventory_rows.jsonl",
            "source_inventory/source_manifest.jsonl",
            "candidate_materialization/model_safe_view.jsonl",
            "candidate_materialization/hidden_manifest.jsonl",
        ],
        "output_root": "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_materialization/",
        "must_not_do": [
            "train learned model",
            "use validation/test rows",
            "write to H001 artifacts",
            "use multiview learned embedding",
            "put scan/source paths into model_safe_view",
        ],
        "must_do": [
            "emit model_safe_view.jsonl",
            "emit source_manifest.jsonl",
            "emit visual_audit_manifest.jsonl",
            "emit control_manifest.jsonl",
            "emit feature_stats.json",
            "emit validation_errors.jsonl",
            "validate finite numeric features",
            "validate G_e contains no predicate/source/label fields",
            "validate Q_e contains no correctness labels",
        ],
    }


def scope_rows(inventory_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in inventory_rows:
        groups[str(row.get("predicate_label"))].append(row)
    rows: list[dict[str, Any]] = []
    for predicate, items in sorted(groups.items()):
        q_counts = Counter(str(row.get("q_e_state_plan")) for row in items)
        role = "main" if predicate in MAIN_PREDICATES else "diagnostic"
        rows.append(
            {
                "predicate_label": predicate,
                "role": role,
                "rows": len(items),
                "q_e_state_counts": json.dumps(dict(sorted(q_counts.items())), sort_keys=True),
                "materialize_g_e": True,
                "materialize_q_e": True,
                "include_in_primary_smoke": predicate in MAIN_PREDICATES,
            }
        )
    return rows


def build_summary_counts(inventory_rows: list[dict[str, Any]]) -> dict[str, Any]:
    q_counts = Counter(str(row.get("q_e_state_plan")) for row in inventory_rows)
    pred_counts = Counter(str(row.get("predicate_label")) for row in inventory_rows)
    role_counts = Counter(str(row.get("predicate_role")) for row in inventory_rows)
    return {
        "rows": len(inventory_rows),
        "predicate_counts": dict(sorted(pred_counts.items())),
        "predicate_role_counts": dict(sorted(role_counts.items())),
        "q_e_state_counts": dict(sorted(q_counts.items())),
        "q_e_state_count": len(q_counts),
        "main_rows": sum(count for predicate, count in pred_counts.items() if predicate in MAIN_PREDICATES),
        "diagnostic_rows": sum(count for predicate, count in pred_counts.items() if predicate in DIAGNOSTIC_PREDICATES),
    }


def render_report(summary: dict[str, Any]) -> str:
    counts = summary["planned_scope"]
    return f"""# H002 Support/Contact Individual Predicate Point/Multiview Materialization Plan

## Status

```text
artifact_root = {summary['output_paths']['artifact_root']}
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Planned Scope

```text
rows = {counts['rows']}
main_rows = {counts['main_rows']}
diagnostic_rows = {counts['diagnostic_rows']}
predicate_counts = {counts['predicate_counts']}
q_e_state_counts = {counts['q_e_state_counts']}
```

## Plan

Materialize `G_e` and `Q_e` separately:

- `G_e_obb_baseline`: current OBB-only diagnostic baseline.
- `G_e_point_pose`: point-derived pose/orientation evidence.
- `G_e_contact_patch`: local support/contact geometry evidence.
- `Q_e_observability`: evidence sufficiency, crop quality, point/mesh completeness, and missing/conflict flags.
- `V_mv_audit_manifest`: visual/multiview audit metadata only.

No learned smoke or visual encoder is allowed in this step.

## Required Controls After Materialization

- OBB-only baseline.
- Point-only ablation.
- Mesh/contact-only ablation.
- Wrong-pair geometry.
- Shuffled geometry, global and within predicate.
- Wrong-view and shuffled-view controls before visual input is used.
- Class-pair/rank/source shortcut probe.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    source_summary = read_json(args.source_inventory_dir / "summary.json") if (args.source_inventory_dir / "summary.json").exists() else {}
    source_errors = read_jsonl(args.source_inventory_dir / "validation_errors.jsonl")
    inventory_rows = read_jsonl(args.source_inventory_dir / "inventory_rows.jsonl")
    source_manifest = read_jsonl(args.source_inventory_dir / "source_manifest.jsonl")
    candidate_rows = read_jsonl(args.candidate_dir / "model_safe_view.jsonl")

    validation_errors = validate_inputs(source_summary, source_errors, inventory_rows, source_manifest, candidate_rows)
    status = STATUS_ERROR if validation_errors else STATUS_READY
    selected_path = "fix_inputs_before_gq_materialization_plan" if validation_errors else SELECTED_PATH
    next_todo = "fix_point_multiview_materialization_plan_inputs" if validation_errors else NEXT_TODO
    planned_scope = build_summary_counts(inventory_rows)

    output_paths = {
        "artifact_root": rel_path(args.output_dir),
        "summary": rel_path(args.output_dir / "summary.json"),
        "report": rel_path(args.output_dir / "report.md"),
        "feature_blocks": rel_path(args.output_dir / "feature_blocks.csv"),
        "model_views": rel_path(args.output_dir / "model_views.csv"),
        "control_plan": rel_path(args.output_dir / "control_plan.csv"),
        "blocked_fields": rel_path(args.output_dir / "blocked_fields.csv"),
        "row_scope": rel_path(args.output_dir / "row_scope.csv"),
        "output_schema": rel_path(args.output_dir / "output_schema.json"),
        "runner_contract": rel_path(args.output_dir / "runner_contract.json"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "boundary": {
            "split": "train_only_materialization_plan",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_point_crops": False,
            "materializes_multiview_crops": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
            "visual_model_input_allowed": False,
        },
        "input_paths": {
            "source_inventory_summary": rel_path(args.source_inventory_dir / "summary.json"),
            "source_inventory_rows": rel_path(args.source_inventory_dir / "inventory_rows.jsonl"),
            "source_manifest": rel_path(args.source_inventory_dir / "source_manifest.jsonl"),
            "candidate_model_safe_view": rel_path(args.candidate_dir / "model_safe_view.jsonl"),
        },
        "planned_scope": planned_scope,
        "plan_decision": {
            "materialization_allowed_next": not validation_errors,
            "learned_smoke_allowed": False,
            "visual_model_input_allowed": False,
            "multiview_audit_qe_first": True,
            "supported_by_policy": "diagnostic_only",
            "g_e_q_e_separated": True,
        },
        "output_paths": output_paths,
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "output_schema.json", output_schema())
    write_json(args.output_dir / "runner_contract.json", runner_contract())
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "feature_blocks.csv", feature_blocks())
    write_csv(args.output_dir / "model_views.csv", model_views())
    write_csv(args.output_dir / "control_plan.csv", controls())
    write_csv(args.output_dir / "blocked_fields.csv", blocked_fields())
    write_csv(args.output_dir / "row_scope.csv", scope_rows(inventory_rows))
    (args.output_dir / "report.md").write_text(render_report(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
