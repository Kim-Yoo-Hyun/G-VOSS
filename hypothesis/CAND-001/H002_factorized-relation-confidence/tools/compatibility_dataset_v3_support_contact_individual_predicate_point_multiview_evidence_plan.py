#!/usr/bin/env python3
"""Plan point/multiview evidence for support/contact individual predicates."""

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

DEFAULT_FAILURE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis"
)
DEFAULT_CANDIDATE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization"
)
DEFAULT_SMOKE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner"
)
DEFAULT_SOURCE_INVENTORY_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_support_contact_visual_mesh_source_inventory"
)
DEFAULT_SCAN_ROOT = REPO_ROOT / "local_dataset/3RScan/scans"
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan"
)

EXPECTED_FAILURE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_failure_analysis_ready_select_point_multiview_evidence_plan"
)
EXPECTED_FAILURE_NEXT = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan"
EXPECTED_CANDIDATE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_candidate_materialization_ready_for_schema_shortcut_audit"
)
EXPECTED_SMOKE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_sanitized_view_smoke_runner_diagnostic_only_failed_controls"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan_ready_for_source_inventory"
)
STATUS_ERROR = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_evidence_plan_input_errors"
)
SELECTED_PATH = "g_q_separated_audit_first_point_multiview_source_inventory"
NEXT_TODO = "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_source_inventory"

MAIN_PREDICATES = ["standing on", "lying on"]
DIAGNOSTIC_PREDICATES = ["supported by"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--failure-dir", type=Path, default=DEFAULT_FAILURE_DIR)
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE_DIR)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE_DIR)
    parser.add_argument("--source-inventory-dir", type=Path, default=DEFAULT_SOURCE_INVENTORY_DIR)
    parser.add_argument("--scan-root", type=Path, default=DEFAULT_SCAN_ROOT)
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


def load_summary(path: Path, label: str, errors: list[dict[str, Any]]) -> dict[str, Any]:
    if not path.exists():
        errors.append({"input": label, "error_type": "missing_summary", "path": rel_path(path)})
        return {}
    return read_json(path)


def validate_inputs(
    failure_summary: dict[str, Any],
    candidate_summary: dict[str, Any],
    smoke_summary: dict[str, Any],
    source_inventory_summary: dict[str, Any],
    failure_errors: list[dict[str, Any]],
    candidate_errors: list[dict[str, Any]],
    smoke_errors: list[dict[str, Any]],
    source_errors: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    expected = [
        ("failure_summary", failure_summary, EXPECTED_FAILURE_STATUS),
        ("candidate_summary", candidate_summary, EXPECTED_CANDIDATE_STATUS),
        ("smoke_summary", smoke_summary, EXPECTED_SMOKE_STATUS),
    ]
    for label, summary, status in expected:
        if summary.get("status") != status:
            errors.append(
                {
                    "input": label,
                    "error_type": "unexpected_status",
                    "actual": summary.get("status"),
                    "expected": status,
                }
            )
        if summary.get("validation_errors") != 0:
            errors.append(
                {
                    "input": label,
                    "error_type": "validation_errors_present",
                    "actual": summary.get("validation_errors"),
                }
            )
    if failure_summary.get("next_todo") != EXPECTED_FAILURE_NEXT:
        errors.append(
            {
                "input": "failure_summary",
                "error_type": "unexpected_next_todo",
                "actual": failure_summary.get("next_todo"),
                "expected": EXPECTED_FAILURE_NEXT,
            }
        )
    for label, rows in [
        ("failure_validation_errors", failure_errors),
        ("candidate_validation_errors", candidate_errors),
        ("smoke_validation_errors", smoke_errors),
        ("source_inventory_validation_errors", source_errors),
    ]:
        if rows:
            errors.append({"input": label, "error_type": "validation_error_rows_present", "rows": len(rows)})

    boundary_sources = [
        ("candidate_summary", candidate_summary),
        ("smoke_summary", smoke_summary),
        ("source_inventory_summary", source_inventory_summary),
    ]
    for label, summary in boundary_sources:
        boundary = summary.get("boundary", {})
        for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "runs_learned_smoke", "trains_new_model"]:
            if key in boundary and boundary.get(key) is not False:
                errors.append(
                    {
                        "input": label,
                        "error_type": "boundary_not_false",
                        "key": key,
                        "actual": boundary.get(key),
                    }
                )
    return errors


def scan_asset_row(scan_root: Path, scan_id: str) -> dict[str, bool]:
    scan_dir = scan_root / scan_id
    return {
        "scan_dir_available": scan_dir.is_dir(),
        "aligned_point_ply_available": (scan_dir / "labels.instances.align.annotated.v2.ply").exists(),
        "semseg_available": (scan_dir / "semseg.v2.json").exists(),
        "mesh_obj_available": (scan_dir / "mesh.refined.v2.obj").exists(),
        "mesh_seg_available": (scan_dir / "mesh.refined.0.010000.segs.v2.json").exists(),
        "sequence_zip_available": (scan_dir / "sequence.zip").exists(),
    }


def asset_readiness(hidden_rows: list[dict[str, Any]], scan_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    scan_cache: dict[str, dict[str, bool]] = {}
    rows: list[dict[str, Any]] = []
    counters = Counter()
    by_predicate: dict[str, Counter[str]] = defaultdict(Counter)

    for row in hidden_rows:
        scan_id = str(row.get("scan_id", ""))
        predicate = str(row.get("predicate_label", "unknown"))
        if scan_id not in scan_cache:
            scan_cache[scan_id] = scan_asset_row(scan_root, scan_id)
        assets = scan_cache[scan_id]
        point_ready = assets["aligned_point_ply_available"] and assets["semseg_available"]
        mesh_ready = assets["mesh_obj_available"] and assets["mesh_seg_available"]
        multiview_ready = assets["sequence_zip_available"]
        all_ready = point_ready and mesh_ready and multiview_ready
        counters["rows"] += 1
        counters["point_ready_rows"] += int(point_ready)
        counters["mesh_ready_rows"] += int(mesh_ready)
        counters["multiview_ready_rows"] += int(multiview_ready)
        counters["all_ready_rows"] += int(all_ready)
        by_predicate[predicate]["rows"] += 1
        by_predicate[predicate]["point_ready_rows"] += int(point_ready)
        by_predicate[predicate]["mesh_ready_rows"] += int(mesh_ready)
        by_predicate[predicate]["multiview_ready_rows"] += int(multiview_ready)
        by_predicate[predicate]["all_ready_rows"] += int(all_ready)
        if not all_ready:
            rows.append(
                {
                    "row_id": row.get("row_id"),
                    "scan_id": scan_id,
                    "predicate_label": predicate,
                    "point_ready": point_ready,
                    "mesh_ready": mesh_ready,
                    "multiview_ready": multiview_ready,
                    **assets,
                }
            )

    summary = {
        "scan_root": rel_path(scan_root),
        "candidate_rows": counters["rows"],
        "unique_scans": len(scan_cache),
        "point_ready_rows": counters["point_ready_rows"],
        "mesh_ready_rows": counters["mesh_ready_rows"],
        "multiview_ready_rows": counters["multiview_ready_rows"],
        "all_ready_rows": counters["all_ready_rows"],
        "point_ready_rate": counters["point_ready_rows"] / counters["rows"] if counters["rows"] else 0.0,
        "mesh_ready_rate": counters["mesh_ready_rows"] / counters["rows"] if counters["rows"] else 0.0,
        "multiview_ready_rate": counters["multiview_ready_rows"] / counters["rows"] if counters["rows"] else 0.0,
        "all_ready_rate": counters["all_ready_rows"] / counters["rows"] if counters["rows"] else 0.0,
        "by_predicate": {
            predicate: {
                "rows": values["rows"],
                "point_ready_rows": values["point_ready_rows"],
                "mesh_ready_rows": values["mesh_ready_rows"],
                "multiview_ready_rows": values["multiview_ready_rows"],
                "all_ready_rows": values["all_ready_rows"],
                "point_ready_rate": values["point_ready_rows"] / values["rows"] if values["rows"] else 0.0,
                "mesh_ready_rate": values["mesh_ready_rows"] / values["rows"] if values["rows"] else 0.0,
                "multiview_ready_rate": values["multiview_ready_rows"] / values["rows"] if values["rows"] else 0.0,
                "all_ready_rate": values["all_ready_rows"] / values["rows"] if values["rows"] else 0.0,
            }
            for predicate, values in sorted(by_predicate.items())
        },
    }
    return summary, rows


def predicate_route_rows() -> list[dict[str, Any]]:
    return [
        {
            "predicate": "standing on",
            "role": "main_candidate",
            "route": "upright_pose_bottom_contact_support_below",
            "required_G_e": "subject uprightness; bottom contact band; support surface below; support normal verticality; local point/mesh contact patch",
            "required_Q_e": "point density near bottom band; mesh/semseg completeness; same-frame visibility optional for audit; occlusion/conflict flag",
            "multiview_policy": "audit_and_Q_e_first_not_learned_visual_input",
            "promotion_condition": "TG interaction improves over G-only and T-only under class-pair/rank/source controls; Q_e not constant",
        },
        {
            "predicate": "lying on",
            "role": "main_candidate",
            "route": "horizontal_pose_large_or_elongated_contact",
            "required_G_e": "subject horizontalness; major-axis pose; broad contact area; support surface overlap; low vertical extent ratio",
            "required_Q_e": "point support for elongated footprint; mesh contact patch quality; same-frame crop confirms pose/contact only for audit first",
            "multiview_policy": "audit_and_Q_e_first_not_learned_visual_input",
            "promotion_condition": "TG interaction separates lying-on accept from standing-like/support-only negatives without label-match leakage",
        },
        {
            "predicate": "supported by",
            "role": "diagnostic_only",
            "route": "broad_support_superordinate_or_ambiguous",
            "required_G_e": "support surface below; vertical support plausibility; coarse contact/overlap",
            "required_Q_e": "ambiguity flag; superordinate-boundary flag; evidence insufficiency flag",
            "multiview_policy": "audit_label_quality_and_boundary_check_only",
            "promotion_condition": "not promoted to main binary target until subtype boundary is separable from standing/lying labels",
        },
    ]


def factor_boundary_rows() -> list[dict[str, Any]]:
    return [
        {
            "factor": "G_e_point_mesh",
            "meaning": "predicate-independent object-pair geometry evidence",
            "allowed_inputs": "instance point crop; mesh contact patch; normals; point density; local support surface statistics",
            "forbidden_inputs": "predicate label; source score; rank; GT match status; audit accept/reject label; visual language score",
            "immediate_use": "controlled feature materialization after source inventory",
        },
        {
            "factor": "Q_e_observability",
            "meaning": "whether the evidence is sufficient to decide",
            "allowed_inputs": "point availability; mesh completeness; contact patch point count; view count; crop quality; occlusion/conflict/missing flags",
            "forbidden_inputs": "relation correctness label; hidden construction bucket; source rank as quality proxy",
            "immediate_use": "materialize before learned smoke; must be non-constant",
        },
        {
            "factor": "V_mv_e",
            "meaning": "optional visual/multiview evidence",
            "allowed_inputs": "co-visible crops and pair contact sheets after audit/source controls",
            "forbidden_inputs": "direct learned visual encoder features in the next immediate stage",
            "immediate_use": "audit packet and Q_e confirmation first; deployable feature only after shortcut audit",
        },
        {
            "factor": "T_e",
            "meaning": "semantic content",
            "allowed_inputs": "predicate text; predicate family; subject/object class text",
            "forbidden_inputs": "source score/rank; GT label; geometry status",
            "immediate_use": "unchanged from current smoke contract",
        },
        {
            "factor": "Z_e",
            "meaning": "source confidence",
            "allowed_inputs": "source score; rank; source id",
            "forbidden_inputs": "compatibility head C_e input",
            "immediate_use": "kept for final reliability ablation, not C_e",
        },
    ]


def feature_schema_rows() -> list[dict[str, Any]]:
    return [
        {
            "feature_group": "point_pair_crop",
            "factor": "G_e",
            "priority": "primary",
            "fields": "subject/object/union normalized point sets; role mask; local coordinates; optional normals/RGB if already available",
            "why": "OBB averages hide pose/contact cues needed for standing-vs-lying.",
            "next_stage": "source_inventory_then_small_materialization_probe",
        },
        {
            "feature_group": "local_contact_patch",
            "factor": "G_e",
            "priority": "primary",
            "fields": "min-gap histogram; near-contact point count; bottom-band overlap; contact patch area; support surface normal distribution",
            "why": "support/contact should be explained by surface-level contact, not only center distance or box overlap.",
            "next_stage": "derive deterministic numeric features before neural point encoder",
        },
        {
            "feature_group": "pose_orientation",
            "factor": "G_e",
            "priority": "primary",
            "fields": "PCA axis gravity alignment; uprightness; horizontalness; extent ratios; bottom/top band geometry",
            "why": "standing on and lying on differ mainly in subject pose under similar support geometry.",
            "next_stage": "replace or extend current OBB pose proxies with point-based pose statistics",
        },
        {
            "feature_group": "multiview_visibility",
            "factor": "Q_e",
            "priority": "audit_first",
            "fields": "co-visible frame count; subject/object visibility; pair crop quality; occlusion flag; frame disagreement",
            "why": "visual evidence should first explain whether the relation is decidable, not silently become a shortcut.",
            "next_stage": "packet/source inventory; no visual encoder in immediate smoke",
        },
        {
            "feature_group": "mesh_completeness",
            "factor": "Q_e",
            "priority": "primary",
            "fields": "instance point count; mesh segment availability; contact-band point count; missing/partial object flags",
            "why": "Q_e was constant in OBB-only smoke, so the next materialization must create non-constant observability fields.",
            "next_stage": "required before p_obs or abstain smoke",
        },
    ]


def leakage_policy_rows() -> list[dict[str, Any]]:
    return [
        {
            "risk": "visual_feature_shortcut",
            "trigger": "learned visual encoder sees object texture/class cues before target independence is controlled",
            "control": "use multiview first for audit packet and Q_e fields; introduce visual feature only after wrong-view/shuffled-view controls",
        },
        {
            "risk": "label_match_leakage",
            "trigger": "exact_match/family_match construction fields explain accept/reject",
            "control": "keep label_match_status, candidate_role, queue_kind, machine_hint, GT ids hidden-only",
        },
        {
            "risk": "class_pair_shortcut",
            "trigger": "object class pair predicts predicate subtype",
            "control": "require class-pair/rank/source balance and report per-class-pair error slices",
        },
        {
            "risk": "distance_or_obb_rule_dominance",
            "trigger": "single rule or scalar geometry solves target",
            "control": "run G-only, OBB-only, point-only, and corrupted geometry controls separately",
        },
        {
            "risk": "supported_by_boundary_blur",
            "trigger": "superordinate support label collapses standing/lying differences",
            "control": "keep supported by diagnostic-only until subtype boundary is audited",
        },
    ]


def promotion_gate_rows() -> list[dict[str, Any]]:
    return [
        {
            "gate": "source_inventory_ready",
            "minimum": ">=95% candidate rows have point, mesh, and sequence asset availability or explicit missing reason",
            "blocks_if_failed": "point/multiview materialization",
        },
        {
            "gate": "q_e_non_constant",
            "minimum": "Q_e has at least 3 meaningful states: sufficient, limited, missing/conflict",
            "blocks_if_failed": "p_obs or abstain claim",
        },
        {
            "gate": "feature_boundary_clean",
            "minimum": "G_e contains no predicate/source/label fields; Q_e contains no correctness label",
            "blocks_if_failed": "factorized claim",
        },
        {
            "gate": "controlled_smoke_improvement",
            "minimum": "T_e+G_e or C_e AUROC >= 0.70 and improves over T-only/G-only/OBB-only under grouped CV",
            "blocks_if_failed": "support/contact main claim",
        },
        {
            "gate": "corruption_controls",
            "minimum": "wrong-pair geometry, shuffled geometry, wrong-view, shuffled-view controls degrade clearly",
            "blocks_if_failed": "geometry/visual evidence claim",
        },
    ]


def top_error_rows(error_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pair = Counter()
    by_predicate = Counter()
    by_type = Counter()
    for row in error_rows:
        by_pair[str(row.get("class_pair", "unknown"))] += 1
        by_predicate[str(row.get("predicate", "unknown"))] += 1
        by_type[str(row.get("error_type", "unknown"))] += 1
    rows: list[dict[str, Any]] = []
    for key, value in by_pair.most_common(10):
        rows.append({"axis": "class_pair", "value": key, "error_count": value})
    for key, value in by_predicate.most_common():
        rows.append({"axis": "predicate", "value": key, "error_count": value})
    for key, value in by_type.most_common():
        rows.append({"axis": "error_type", "value": key, "error_count": value})
    return rows


def render_report(
    summary: dict[str, Any],
    asset_summary: dict[str, Any],
    failure_summary: dict[str, Any],
) -> str:
    return f"""# H002 Support/Contact Individual Predicate Point/Multiview Evidence Plan

## Status

```text
artifact_root = {summary['output_paths']['artifact_root']}
status = {summary['status']}
selected_path = {summary['selected_path']}
validation_errors = {summary['validation_errors']}
next_todo = {summary['next_todo']}
```

## Why This Plan Exists

The OBB-only individual-predicate smoke produced a real but weak interaction signal:

```text
M4 interaction AUROC = {failure_summary.get('runner_snapshot', {}).get('primary_auroc', 'unknown')}
errors = {failure_summary.get('failure_profile', {}).get('errors', 'unknown')}
false_positive / false_negative = {failure_summary.get('failure_profile', {}).get('false_positive', 'unknown')} / {failure_summary.get('failure_profile', {}).get('false_negative', 'unknown')}
```

The conclusion is not to add a stronger combiner first. The bottleneck is that
semseg OBB geometry does not expose enough point/contact/pose/observability evidence
for `standing on` versus `lying on`.

## Factor Boundary

The next branch must keep `G_e` and `Q_e` separate:

- `G_e`: predicate-independent geometry evidence from point/mesh/contact/pose.
- `Q_e`: whether that evidence is sufficient to decide.
- multiview crops: audit and `Q_e` support first, not immediate learned visual input.
- `T_e`: predicate/object semantic content only.
- `Z_e`: source confidence only, excluded from `C_e`.

## Relation-Specific Routes

```text
standing on  -> upright pose + bottom contact + support surface below
lying on     -> horizontal pose + broad or elongated contact
supported by -> broad support/superordinate diagnostic, not main binary target
```

## Asset Readiness

```text
candidate_rows = {asset_summary['candidate_rows']}
unique_scans = {asset_summary['unique_scans']}
point_ready_rows = {asset_summary['point_ready_rows']}
mesh_ready_rows = {asset_summary['mesh_ready_rows']}
multiview_ready_rows = {asset_summary['multiview_ready_rows']}
all_ready_rows = {asset_summary['all_ready_rows']}
```

The next step should run a source inventory over these rows and decide whether the
existing train-only candidates can support point-pair crops, contact-patch features,
and multiview audit packets.

## Immediate Decision

Selected path:

```text
{summary['selected_path']}
```

This means:

- keep the current OBB-only result diagnostic;
- do not lower the `0.70` gate;
- do not add visual encoder features yet;
- first materialize a clean point/multiview source inventory and `G_e/Q_e` schema;
- keep `supported by` diagnostic-only until the subtype boundary is clearer.

## Next

```text
{summary['next_todo']}
```
"""


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    input_errors: list[dict[str, Any]] = []
    failure_summary = load_summary(args.failure_dir / "summary.json", "failure_summary", input_errors)
    candidate_summary = load_summary(args.candidate_dir / "summary.json", "candidate_summary", input_errors)
    smoke_summary = load_summary(args.smoke_dir / "summary.json", "smoke_summary", input_errors)
    source_inventory_summary = load_summary(
        args.source_inventory_dir / "summary.json", "support_contact_visual_mesh_source_inventory", input_errors
    )

    failure_validation_errors = read_jsonl(args.failure_dir / "validation_errors.jsonl")
    candidate_validation_errors = read_jsonl(args.candidate_dir / "validation_errors.jsonl")
    smoke_validation_errors = read_jsonl(args.smoke_dir / "validation_errors.jsonl")
    source_validation_errors = read_jsonl(args.source_inventory_dir / "validation_errors.jsonl")
    hidden_rows = read_jsonl(args.candidate_dir / "hidden_manifest.jsonl")
    hard_error_rows = read_jsonl(args.failure_dir / "hard_error_cases.jsonl")

    if not hidden_rows:
        input_errors.append(
            {
                "input": "candidate_hidden_manifest",
                "error_type": "missing_or_empty",
                "path": rel_path(args.candidate_dir / "hidden_manifest.jsonl"),
            }
        )

    input_errors.extend(
        validate_inputs(
            failure_summary,
            candidate_summary,
            smoke_summary,
            source_inventory_summary,
            failure_validation_errors,
            candidate_validation_errors,
            smoke_validation_errors,
            source_validation_errors,
        )
    )

    asset_summary, missing_asset_rows = asset_readiness(hidden_rows, args.scan_root)

    status = STATUS_ERROR if input_errors else STATUS_READY
    validation_errors = list(input_errors)
    if asset_summary["candidate_rows"] and asset_summary["all_ready_rate"] < 0.95:
        validation_errors.append(
            {
                "error_type": "asset_readiness_below_plan_gate",
                "all_ready_rate": asset_summary["all_ready_rate"],
                "minimum": 0.95,
                "note": "This blocks materialization, not the plan document itself.",
            }
        )
    if not validation_errors and status == STATUS_READY:
        selected_path = SELECTED_PATH
    else:
        selected_path = "input_errors_need_fix_before_source_inventory"

    predicate_counts = Counter(str(row.get("predicate_label", "unknown")) for row in hidden_rows)
    main_rows = sum(predicate_counts[predicate] for predicate in MAIN_PREDICATES)
    diagnostic_rows = sum(predicate_counts[predicate] for predicate in DIAGNOSTIC_PREDICATES)

    output_paths = {
        "artifact_root": rel_path(args.output_dir),
        "summary": rel_path(args.output_dir / "summary.json"),
        "report": rel_path(args.output_dir / "report.md"),
        "predicate_evidence_routes": rel_path(args.output_dir / "predicate_evidence_routes.csv"),
        "factor_boundary": rel_path(args.output_dir / "factor_boundary.csv"),
        "feature_schema": rel_path(args.output_dir / "feature_schema.csv"),
        "leakage_control_policy": rel_path(args.output_dir / "leakage_control_policy.csv"),
        "promotion_gates": rel_path(args.output_dir / "promotion_gates.csv"),
        "asset_readiness": rel_path(args.output_dir / "asset_readiness.json"),
        "asset_readiness_by_predicate": rel_path(args.output_dir / "asset_readiness_by_predicate.csv"),
        "missing_asset_rows": rel_path(args.output_dir / "missing_asset_rows.jsonl"),
        "error_focus": rel_path(args.output_dir / "error_focus.csv"),
        "source_inventory_contract": rel_path(args.output_dir / "source_inventory_contract.json"),
        "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
    }

    source_inventory_contract = {
        "schema_version": f"{SCHEMA_VERSION}_source_inventory_contract",
        "next_todo": NEXT_TODO,
        "input_candidate_rows": rel_path(args.candidate_dir / "hidden_manifest.jsonl"),
        "scan_root": rel_path(args.scan_root),
        "required_asset_checks": [
            "labels.instances.align.annotated.v2.ply",
            "semseg.v2.json",
            "mesh.refined.v2.obj",
            "mesh.refined.0.010000.segs.v2.json",
            "sequence.zip",
        ],
        "required_outputs": [
            "point_pair_crop_readiness",
            "contact_patch_feature_readiness",
            "multiview_packet_readiness",
            "q_e_state_distribution_plan",
            "unsupported_or_missing_reason_rows",
        ],
        "model_input_policy": {
            "point_mesh_numeric_G_e": "allowed_after_inventory_and_schema_shortcut_audit",
            "multiview_visual_feature": "audit_and_Q_e_first_only",
            "human_review_label": "label_only_never_input",
            "source_score_rank": "Z_e_only_not_C_e",
        },
    }

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": NEXT_TODO if status == STATUS_READY else "fix_input_errors_before_point_multiview_source_inventory",
        "validation_errors": len(validation_errors),
        "boundary": {
            "split": "train_only_plan",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "materializes_candidate_rows": False,
            "materializes_point_crops": False,
            "materializes_multiview_crops": False,
            "runs_learned_smoke": False,
            "trains_new_model": False,
            "paper_evidence_allowed": False,
        },
        "input_paths": {
            "failure_summary": rel_path(args.failure_dir / "summary.json"),
            "candidate_summary": rel_path(args.candidate_dir / "summary.json"),
            "hidden_manifest": rel_path(args.candidate_dir / "hidden_manifest.jsonl"),
            "smoke_summary": rel_path(args.smoke_dir / "summary.json"),
            "support_contact_visual_mesh_source_inventory": rel_path(args.source_inventory_dir / "summary.json"),
            "scan_root": rel_path(args.scan_root),
        },
        "candidate_scope": {
            "total_candidate_rows": len(hidden_rows),
            "main_predicates": MAIN_PREDICATES,
            "diagnostic_predicates": DIAGNOSTIC_PREDICATES,
            "main_rows": main_rows,
            "diagnostic_rows": diagnostic_rows,
            "predicate_counts": dict(sorted(predicate_counts.items())),
        },
        "failure_basis": {
            "obb_only_current_status": "diagnostic_freeze",
            "primary_auc": failure_summary.get("runner_snapshot", {}).get("primary_auroc"),
            "geometry_only_auc": failure_summary.get("runner_snapshot", {}).get("geometry_only_auroc"),
            "semantic_only_auc": failure_summary.get("runner_snapshot", {}).get("semantic_only_auroc"),
            "errors": failure_summary.get("failure_profile", {}).get("errors"),
            "false_positive": failure_summary.get("failure_profile", {}).get("false_positive"),
            "false_negative": failure_summary.get("failure_profile", {}).get("false_negative"),
            "q_e_problem": "constant_mesh_true_point_false_view_false_in_current_smoke",
        },
        "asset_readiness": asset_summary,
        "plan_decision": {
            "do_not_add_stronger_combiner_first": True,
            "do_not_use_multiview_as_learned_input_immediately": True,
            "separate_g_e_and_q_e": True,
            "supported_by_policy": "diagnostic_only_until_boundary_audit",
            "source_inventory_required_before_materialization": True,
        },
        "output_paths": output_paths,
    }

    write_json(args.output_dir / "summary.json", summary)
    write_json(args.output_dir / "asset_readiness.json", asset_summary)
    write_json(args.output_dir / "source_inventory_contract.json", source_inventory_contract)
    write_jsonl(args.output_dir / "missing_asset_rows.jsonl", missing_asset_rows[:200])
    write_jsonl(args.output_dir / "validation_errors.jsonl", validation_errors)
    write_csv(args.output_dir / "predicate_evidence_routes.csv", predicate_route_rows())
    write_csv(args.output_dir / "factor_boundary.csv", factor_boundary_rows())
    write_csv(args.output_dir / "feature_schema.csv", feature_schema_rows())
    write_csv(args.output_dir / "leakage_control_policy.csv", leakage_policy_rows())
    write_csv(args.output_dir / "promotion_gates.csv", promotion_gate_rows())
    write_csv(args.output_dir / "error_focus.csv", top_error_rows(hard_error_rows))
    write_csv(
        args.output_dir / "asset_readiness_by_predicate.csv",
        [
            {"predicate": predicate, **values}
            for predicate, values in asset_summary.get("by_predicate", {}).items()
        ],
    )
    (args.output_dir / "report.md").write_text(
        render_report(summary, asset_summary, failure_summary), encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
