#!/usr/bin/env python3
"""Freeze the attachment-deferred verifier-policy contract.

This G2 step defines future `satisfied` / `violated` / `uncertain` rules for
attachment-deferred relations. It does not apply those rules to source
predictions, does not fit a calibrator, does not emit p_geom_valid, and does
not compute metrics.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_attachment_deferred_verifier_policy_v1"
STATUS = "attachment_deferred_verifier_policy_ready_no_decisions_no_metrics"
TARGET_FAMILY = "attachment_deferred"
NEXT_GATE = "G3_attachment_calibration_counterfactual_generation"
PREDICATE_LABELS = ["attached to", "hanging on", "connected to"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def threshold_plan() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "threshold_origin": "predeclared_policy_defaults_from_G1c_evidence_contract_not_heldout_metric_tuned",
        "calibration_status": "not_fitted",
        "common": {
            "near_contact_threshold_m": 0.05,
            "uncertain_contact_band_m": [0.05, 0.15],
            "clear_far_distance_m": 0.30,
            "min_near_contact_points_for_satisfied": 3,
            "min_contact_patch_score_for_satisfied": 0.20,
            "min_floor_clearance_for_hanging_m": 0.10,
            "max_support_explanation_score_without_contradiction": 0.30,
            "min_support_explanation_score_for_contradiction": 0.60,
        },
        "non_tunable_before_G3": [
            "near_contact_threshold_m",
            "clear_far_distance_m",
            "surface_type_allowlist_by_subtype",
            "normal_class_allowlist_by_subtype",
        ],
        "may_be_calibrated_in_G3": [
            "decision-to-probability mapping",
            "uncertain band width",
            "family-specific operating point",
        ],
    }


def reason_codes() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "satisfied": [
            "near_contact_points_present",
            "contact_patch_score_sufficient",
            "surface_type_matches_subtype",
            "surface_normal_matches_subtype",
            "hanging_gravity_cue_present",
            "no_strong_contradictory_support",
            "connected_adjacent_contact",
        ],
        "violated": [
            "clear_far_from_attachment_surface",
            "no_near_contact_points",
            "surface_type_contradicts_predicate",
            "surface_normal_contradicts_predicate",
            "floor_or_table_support_contradicts_hanging",
            "hanging_gravity_cue_absent",
            "connected_pair_far_apart",
        ],
        "uncertain": [
            "missing_point_or_normal_evidence",
            "distance_in_uncertain_band",
            "ambiguous_functional_attachment",
            "ambiguous_draped_or_occluded_hanging",
            "ambiguous_functional_connection",
            "class_prior_only_not_allowed_as_proof",
            "possible_occluded_connector_or_fastener",
            "surface_type_unknown",
            "thin_or_sparse_object_points",
        ],
        "hard_guardrails": [
            "class_pair_prior_may_never_be_used_as_proof",
            "unknown_surface_type_defaults_to_uncertain_unless_connected_contact_is_direct",
            "ambiguous_subtype_defaults_to_uncertain",
            "violated_requires_clear_negative_geometry_not_absence_of_semantic_plausibility",
        ],
    }


def decision_schema() -> dict[str, Any]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "H001 attachment-deferred future verifier decision row",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "policy_name",
            "policy_version",
            "row_id",
            "source_name",
            "scan_id",
            "subgraph_id",
            "subject_id",
            "object_id",
            "predicate_label",
            "predicate_family",
            "subtype_hint",
            "verification_status",
            "reason_codes",
            "evidence_requirements_met",
            "uncertain_by_design",
            "notes",
        ],
        "properties": {
            "schema_version": {"const": "h001_attachment_deferred_verifier_decision_v1"},
            "policy_name": {"const": "attachment_deferred_conservative_v1"},
            "policy_version": {"const": SCHEMA_VERSION},
            "row_id": {"type": "string"},
            "source_name": {"type": "string"},
            "scan_id": {"type": "string"},
            "subgraph_id": {"type": "string"},
            "subject_id": {"type": ["integer", "string"]},
            "object_id": {"type": ["integer", "string"]},
            "predicate_label": {"enum": PREDICATE_LABELS},
            "predicate_family": {"const": TARGET_FAMILY},
            "subtype_hint": {"type": "string"},
            "verification_status": {"enum": ["satisfied", "violated", "uncertain"]},
            "reason_codes": {"type": "array", "items": {"type": "string"}},
            "evidence_requirements_met": {"type": "array", "items": {"type": "string"}},
            "uncertain_by_design": {"type": "boolean"},
            "notes": {"type": "array", "items": {"type": "string"}},
        },
        "forbidden_fields": [
            "p_geom_valid",
            "recall_credit",
            "reranked_score",
            "rank",
            "topk",
            "metric",
        ],
    }


def subtype_rules() -> dict[str, Any]:
    return {
        "attached_to_vertical_or_overhead_surface": {
            "predicate_label": "attached to",
            "satisfied_if_all": [
                "extractor_status == ready",
                "surface_type in {wall, ceiling, fixture, furniture, object_part}",
                "normal_class in {vertical, horizontal_down, slanted}",
                "min_point_distance_m <= near_contact_threshold_m",
                "near_contact_point_count >= min_near_contact_points_for_satisfied or contact_patch_score >= min_contact_patch_score_for_satisfied",
            ],
            "violated_if_all": [
                "surface_type in {floor}",
                "min_point_distance_m >= clear_far_distance_m",
                "near_contact_point_count == 0",
                "class_pair_prior != plausible",
            ],
            "otherwise": "uncertain",
            "notes": [
                "Floor attachment can be annotation-dependent, so floor alone is not enough for violation.",
                "Class prior is context only and cannot satisfy the rule.",
            ],
        },
        "attached_to_furniture_or_fixture": {
            "predicate_label": "attached to",
            "satisfied_if_all": [
                "extractor_status == ready",
                "surface_type in {furniture, fixture, object_part}",
                "min_point_distance_m <= near_contact_threshold_m",
                "near_contact_point_count >= min_near_contact_points_for_satisfied or contact_patch_score >= min_contact_patch_score_for_satisfied",
            ],
            "violated_if_all": [
                "min_point_distance_m >= clear_far_distance_m",
                "near_contact_point_count == 0",
                "surface_type in {floor, unknown}",
                "class_pair_prior != plausible",
            ],
            "otherwise": "uncertain",
            "notes": [
                "Functional attachments without visible contact remain uncertain.",
            ],
        },
        "ambiguous_functional_attachment": {
            "predicate_label": "attached to",
            "satisfied_if_all": [],
            "violated_if_all": [
                "min_point_distance_m >= clear_far_distance_m",
                "near_contact_point_count == 0",
                "surface_type in {floor, unknown}",
                "class_pair_prior == implausible",
            ],
            "otherwise": "uncertain",
            "notes": [
                "Ambiguous functional attachment defaults to uncertain because hidden fasteners, occlusion, and annotation wording can dominate visible geometry.",
            ],
        },
        "hanging_from_vertical_surface": {
            "predicate_label": "hanging on",
            "satisfied_if_all": [
                "extractor_status == ready",
                "surface_type in {wall, fixture, furniture, object_part}",
                "normal_class in {vertical, slanted}",
                "min_point_distance_m <= near_contact_threshold_m",
                "near_contact_point_count >= min_near_contact_points_for_satisfied or contact_patch_score >= min_contact_patch_score_for_satisfied",
                "floor_clearance_m >= min_floor_clearance_for_hanging_m",
                "support_explanation_score <= max_support_explanation_score_without_contradiction",
            ],
            "violated_if_any_clear": [
                [
                    "surface_type == floor",
                    "normal_class == horizontal_up",
                    "hanging_geometry_score <= 0.20",
                ],
                [
                    "floor_or_table_supported == true",
                    "support_explanation_score >= min_support_explanation_score_for_contradiction",
                    "hanging_geometry_score <= 0.20",
                ],
                [
                    "min_point_distance_m >= clear_far_distance_m",
                    "near_contact_point_count == 0",
                ],
            ],
            "otherwise": "uncertain",
            "notes": [
                "Draped and occluded hanging cases should remain uncertain unless negative geometry is clear.",
            ],
        },
        "hanging_from_overhead_or_fixture": {
            "predicate_label": "hanging on",
            "satisfied_if_all": [
                "extractor_status == ready",
                "surface_type in {ceiling, fixture, object_part}",
                "normal_class in {horizontal_down, vertical, slanted}",
                "min_point_distance_m <= near_contact_threshold_m",
                "floor_clearance_m >= min_floor_clearance_for_hanging_m",
                "support_explanation_score <= max_support_explanation_score_without_contradiction",
            ],
            "violated_if_any_clear": [
                [
                    "floor_or_table_supported == true",
                    "support_explanation_score >= min_support_explanation_score_for_contradiction",
                    "hanging_geometry_score <= 0.20",
                ],
                [
                    "min_point_distance_m >= clear_far_distance_m",
                    "near_contact_point_count == 0",
                    "surface_type not in {ceiling, fixture, object_part}",
                ],
            ],
            "otherwise": "uncertain",
            "notes": [
                "Thin wires or hooks may be missing in the segmented point cloud.",
            ],
        },
        "ambiguous_draped_or_occluded_hanging": {
            "predicate_label": "hanging on",
            "satisfied_if_all": [],
            "violated_if_any_clear": [
                [
                    "surface_type == floor",
                    "normal_class == horizontal_up",
                    "hanging_geometry_score <= 0.20",
                ],
                [
                    "min_point_distance_m >= clear_far_distance_m",
                    "near_contact_point_count == 0",
                    "floor_clearance_m < min_floor_clearance_for_hanging_m",
                ],
            ],
            "otherwise": "uncertain",
            "notes": [
                "This subtype is intentionally uncertain-biased.",
            ],
        },
        "connected_adjacent_or_contiguous": {
            "predicate_label": "connected to",
            "satisfied_if_all": [
                "extractor_status == ready",
                "min_point_distance_m <= near_contact_threshold_m",
                "near_contact_point_count >= min_near_contact_points_for_satisfied or contact_patch_score >= min_contact_patch_score_for_satisfied",
            ],
            "violated_if_all": [
                "min_point_distance_m >= clear_far_distance_m",
                "near_contact_point_count == 0",
            ],
            "otherwise": "uncertain",
            "notes": [
                "Connected-to may be a hidden cable, pipe, or object part; direct contact satisfies but absence of visible contact must be conservative.",
            ],
        },
        "connected_by_fixture_or_part": {
            "predicate_label": "connected to",
            "satisfied_if_all": [
                "surface_type in {fixture, furniture, object_part}",
                "min_point_distance_m <= near_contact_threshold_m",
                "near_contact_point_count >= min_near_contact_points_for_satisfied",
            ],
            "violated_if_all": [
                "min_point_distance_m >= clear_far_distance_m",
                "near_contact_point_count == 0",
                "surface_type in {floor, unknown}",
            ],
            "otherwise": "uncertain",
            "notes": [
                "Intermediate parts may not be segmented.",
            ],
        },
        "ambiguous_functional_connection": {
            "predicate_label": "connected to",
            "satisfied_if_all": [],
            "violated_if_all": [
                "min_point_distance_m >= clear_far_distance_m",
                "near_contact_point_count == 0",
                "class_pair_prior != plausible",
            ],
            "otherwise": "uncertain",
            "notes": [
                "Functional connection defaults to uncertain until stronger visual or part evidence exists.",
            ],
        },
    }


def verifier_policy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "policy_name": "attachment_deferred_conservative_v1",
        "predicate_family": TARGET_FAMILY,
        "predicate_labels": PREDICATE_LABELS,
        "design_principles": [
            "High-precision violation: only clear negative geometry can produce violated.",
            "Uncertain is the default for ambiguous functional, occluded, sparse, or class-prior-only evidence.",
            "Class affordance/context is never proof.",
            "No source metrics or held-out tuning are allowed in this policy-freeze step.",
            "Exact predicate-label recall remains required for future metrics.",
        ],
        "global_preconditions": [
            {
                "if": "extractor_status != ready or missing point/normal evidence",
                "then": "uncertain",
                "reason_codes": ["missing_point_or_normal_evidence"],
            },
            {
                "if": "surface_type == unknown and subtype is not connected_adjacent_or_contiguous with direct contact",
                "then": "uncertain",
                "reason_codes": ["surface_type_unknown"],
            },
            {
                "if": "affordance_context.allowed_as_proof != false",
                "then": "invalid_policy_input",
                "reason_codes": ["class_prior_only_not_allowed_as_proof"],
            },
        ],
        "threshold_plan": threshold_plan()["common"],
        "subtype_rules": subtype_rules(),
    }


def calibration_plan() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "planned_not_run",
        "next_gate": NEXT_GATE,
        "required_before_source_metrics": [
            "train-dev positive/counterfactual generation",
            "policy implementation smoke on non-held-out rows",
            "GT-positive/counterfactual verifier evaluation",
            "threshold freeze before held-out source metrics",
            "wrong-pair and shuffled-geometry controls",
            "visual sanity check for attachment/hanging",
        ],
        "negative_types": [
            "wrong attachment surface",
            "far object pair",
            "wrong-pair attachment",
            "floor-support replacement for hanging",
            "gravity-inconsistent hanging",
            "shuffled geometry within same label",
        ],
        "blocked_claims_until_complete": [
            "attachment_deferred source metrics",
            "expanded H001 denominator claim",
            "functional or affordance reasoning claim",
        ],
    }


def commands_md() -> str:
    return """# Attachment Deferred Verifier Policy Commands

Run from repository root.

```bash
docker build -t h001-geom-reliability:latest -f configs/h001/Dockerfile .
env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm attachment_deferred_verifier_policy
```

Expected status:

```json
{"status": "attachment_deferred_verifier_policy_ready_no_decisions_no_metrics"}
```

This command freezes policy artifacts only. It does not apply decisions to
source predictions, fit calibration, compute metrics, or update the main paper
claim.
"""


def report_md(manifest: dict[str, Any], policy: dict[str, Any]) -> str:
    thresholds = policy["threshold_plan"]
    lines = [
        "# Attachment Deferred Verifier Policy",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Claim Boundary",
        "",
        "This is a G2 verifier-policy design artifact. It defines future",
        "`satisfied` / `violated` / `uncertain` logic but does not apply the",
        "policy to source predictions, fit calibration, compute metrics, or",
        "change the current AAAI main claim.",
        "",
        "## Inputs Checked",
        "",
    ]
    for key, value in manifest["input_status"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Conservative Threshold Defaults",
            "",
            f"- near contact: `{thresholds['near_contact_threshold_m']}` m",
            f"- uncertain contact band: `{thresholds['uncertain_contact_band_m']}` m",
            f"- clear far distance: `{thresholds['clear_far_distance_m']}` m",
            f"- min near-contact points for satisfied: `{thresholds['min_near_contact_points_for_satisfied']}`",
            f"- min contact patch score for satisfied: `{thresholds['min_contact_patch_score_for_satisfied']}`",
            "",
            "## Subtypes Covered",
            "",
        ]
    )
    for subtype, rule in policy["subtype_rules"].items():
        lines.append(f"- `{subtype}` -> `{rule['predicate_label']}`")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- Ambiguous functional subtypes default to `uncertain`.",
            "- Class affordance/context is never proof.",
            "- `violated` requires clear negative geometry, not weak semantic plausibility.",
            "- Future source metrics remain blocked until G3 calibration/counterfactual and GT verifier-evaluation gates pass.",
            "",
            "## Next Gate",
            "",
            f"`{manifest['next_gate']}`",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--point-surface-dir",
        type=Path,
        default=Path("archive/experiments/H001_geom_reliability/sources/attachment_deferred/point_surface_validation"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("archive/experiments/H001_geom_reliability/sources/attachment_deferred/verifier_policy"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    point_surface_dir = (
        args.point_surface_dir
        if args.point_surface_dir.is_absolute()
        else repo_root / args.point_surface_dir
    )
    out = args.out if args.out.is_absolute() else repo_root / args.out
    point_manifest_path = point_surface_dir / "manifest.json"
    point_summary_path = point_surface_dir / "summary.json"
    point_validation_path = point_surface_dir / "validation.json"
    for path in [point_manifest_path, point_summary_path, point_validation_path]:
        if not path.exists():
            raise FileNotFoundError(f"missing G1c artifact: {path}")

    point_manifest = read_json(point_manifest_path)
    point_summary = read_json(point_summary_path)
    point_validation = read_json(point_validation_path)
    if point_manifest.get("status") != "attachment_deferred_point_surface_validation_ready_no_verifier":
        raise ValueError(f"unexpected point/surface status:{point_manifest.get('status')}")
    if point_validation.get("status") != "passed":
        raise ValueError(f"unexpected point/surface validation status:{point_validation.get('status')}")

    policy = verifier_policy()
    thresholds = threshold_plan()
    reasons = reason_codes()
    schema = decision_schema()
    calibration = calibration_plan()
    input_status = {
        "point_surface_manifest": point_manifest.get("status"),
        "point_surface_validation": point_validation.get("status"),
        "point_surface_rows": point_summary.get("counts", {}).get("output_rows"),
        "ready_rows": point_summary.get("counts", {}).get("ready_rows"),
        "near_contact_rows": point_summary.get("counts", {}).get("near_contact_rows"),
        "forbidden_fields_present": point_validation.get("forbidden_output_fields_present", []),
    }
    blockers = [
        "policy_not_applied_to_rows",
        "calibration_not_built",
        "counterfactuals_not_generated",
        "GT_verifier_evaluation_not_run",
        "source_metrics_not_run",
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "created_at": utc_now(),
        "claim_boundary": {
            "current_main_claim_unchanged": True,
            "artifact_type": "verifier_policy_design",
            "decision_rows_emitted": False,
            "metric_evidence": False,
            "calibration_fitted": False,
            "source_predictions_scored": False,
        },
        "inputs": {
            "point_surface_manifest": relpath(repo_root, point_manifest_path),
            "point_surface_summary": relpath(repo_root, point_summary_path),
            "point_surface_validation": relpath(repo_root, point_validation_path),
        },
        "input_status": input_status,
        "outputs": {
            "verifier_policy": "verifier_policy.json",
            "decision_schema": "decision_schema.json",
            "threshold_plan": "threshold_plan.json",
            "reason_codes": "reason_codes.json",
            "calibration_plan": "calibration_plan.json",
            "commands": "commands.md",
            "report": "report.md",
        },
        "subtype_count": len(policy["subtype_rules"]),
        "next_gate": NEXT_GATE,
        "blockers": blockers,
    }

    ensure_dir(out)
    write_json(out / "verifier_policy.json", policy)
    write_json(out / "decision_schema.json", schema)
    write_json(out / "threshold_plan.json", thresholds)
    write_json(out / "reason_codes.json", reasons)
    write_json(out / "calibration_plan.json", calibration)
    write_json(out / "manifest.json", manifest)
    write_text(out / "commands.md", commands_md())
    write_text(out / "report.md", report_md(manifest, policy))
    print(json.dumps({"status": STATUS, "out": str(out), "subtypes": len(policy["subtype_rules"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
