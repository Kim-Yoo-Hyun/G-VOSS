#!/usr/bin/env python3
"""Freeze the H001 source failure-analysis schema before metric inspection."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_failure_analysis_v1"
MANIFEST_SCHEMA_VERSION = "h001_open3dsg_failure_analysis_manifest_v1"
STATUS = "failure_analysis_schema_ready_no_metric_run"
SUPPORTED_RECORD_TYPES = [
    "open3dsg_failure_analysis",
    "vlsat_failure_analysis",
    "qwen_vl_failure_analysis",
]
SUPPORTED_BASELINES = ["open3dsg_ov", "vlsat_closed_set", "qwen_vl_semantic_source"]


PRIMARY_CATEGORIES: list[dict[str, Any]] = [
    {
        "category": "true_positive_supported",
        "definition": "Prediction exactly matches a GT relation and geometry is satisfied or non-contradictory.",
        "claim_use": "positive_evidence",
        "assignment_hint": "exact GT match and verification_status in satisfied/uncertain with no contradiction.",
    },
    {
        "category": "semantic_false_positive",
        "definition": "Prediction is not supported by GT for the directed pair and geometry does not provide an independent contradiction.",
        "claim_use": "model_failure",
        "assignment_hint": "no exact/family GT match and verification_status is satisfied, uncertain, unsupported, or missing_geometry.",
    },
    {
        "category": "geometry_contradiction",
        "definition": "Prediction is semantically plausible or high-ranked but violates frozen H001 geometry checks.",
        "claim_use": "main_h001_failure",
        "assignment_hint": "verification_status=violated regardless of GT match; audit may later refine plausible-unlabeled cases.",
    },
    {
        "category": "semantic_and_geometry_failure",
        "definition": "Prediction is unsupported by GT and also geometrically contradicted.",
        "claim_use": "main_h001_failure",
        "assignment_hint": "no GT match and verification_status=violated.",
    },
    {
        "category": "plausible_unlabeled",
        "definition": "Prediction lacks a GT label but geometry and visual/audit evidence suggest the relation may be valid.",
        "claim_use": "audit_caveat",
        "assignment_hint": "no GT match, verification_status=satisfied/uncertain, and audit marks relation plausible.",
    },
    {
        "category": "predicate_family_ambiguity",
        "definition": "Prediction chooses a neighboring predicate in the same family where label granularity is ambiguous.",
        "claim_use": "taxonomy_caveat",
        "assignment_hint": "family GT match without exact predicate match, e.g. higher/lower or support/contact variants.",
    },
    {
        "category": "object_pair_mismatch",
        "definition": "Prediction targets the wrong directed object pair or object identity mapping is inconsistent.",
        "claim_use": "identity_failure",
        "assignment_hint": "edge ids do not align with 3DSSG context or visual evidence points to a different object pair.",
    },
    {
        "category": "insufficient_geometry_evidence",
        "definition": "Frozen geometry verifier cannot decide because required geometry evidence is missing or too weak.",
        "claim_use": "caveat_only",
        "assignment_hint": "geometry_checkable=true but verification_status=uncertain due to missing local support/point evidence.",
    },
    {
        "category": "preprocessing_or_filtering_limitation",
        "definition": "Row is affected by known Open3DSG preprocessing/view/filter limitations rather than model semantics.",
        "claim_use": "scope_limitation",
        "assignment_hint": "subgraph/scan belongs to filtered or skipped preprocess/view coverage records.",
    },
    {
        "category": "unsupported_family_out_of_scope",
        "definition": "Predicate family is outside H001 geometry-checkable families.",
        "claim_use": "exclude_from_h001_family_claim",
        "assignment_hint": "predicate_family not in support_contact/proximity/relative_vertical.",
    },
    {
        "category": "rank_only_failure",
        "definition": "Correct relation exists but is ranked below the evaluated top-k cutoff.",
        "claim_use": "ranking_failure",
        "assignment_hint": "GT exact match exists for the pair/predicate but semantic_rank_in_subgraph is outside top-k.",
    },
    {
        "category": "model_score_calibration_failure",
        "definition": "Semantic score is poorly ordered relative to geometry/GT evidence without an identity or verifier error.",
        "claim_use": "calibration_diagnostic",
        "assignment_hint": "large semantic-vs-geometry rank disagreement not explained by GT noise or unsupported family.",
    },
    {
        "category": "adapter_or_identity_error",
        "definition": "Failure comes from raw dump conversion, id mapping, duplicate rows, or schema violation.",
        "claim_use": "exclude_until_fixed",
        "assignment_hint": "adapter validation or identity-preservation checks fail.",
    },
    {
        "category": "unknown_needs_audit",
        "definition": "Available fields are insufficient to assign a stable category.",
        "claim_use": "audit_queue",
        "assignment_hint": "use only as a temporary label before sampled audit or explicit exclusion.",
    },
]


ASSIGNMENT_PRIORITY = [
    "adapter_or_identity_error",
    "preprocessing_or_filtering_limitation",
    "unsupported_family_out_of_scope",
    "true_positive_supported",
    "semantic_and_geometry_failure",
    "geometry_contradiction",
    "predicate_family_ambiguity",
    "rank_only_failure",
    "semantic_false_positive",
    "insufficient_geometry_evidence",
    "model_score_calibration_failure",
    "plausible_unlabeled",
    "object_pair_mismatch",
    "unknown_needs_audit",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/failure_analysis"),
    )
    return parser.parse_args()


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def resolve(repo_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else repo_root / path


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            handle.write("\n")


def failure_schema() -> dict[str, Any]:
    category_values = [item["category"] for item in PRIMARY_CATEGORIES]
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_VERSION}.schema.json",
        "title": "H001 source failure-analysis row",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "record_type",
            "analysis_id",
            "source_prediction",
            "ground_truth",
            "geometry",
            "rerank_effect",
            "failure_taxonomy",
            "cross_source",
            "audit_hooks",
            "quality_flags",
            "provenance",
        ],
        "properties": {
            "schema_version": {"const": SCHEMA_VERSION},
            "record_type": {"type": "string", "enum": SUPPORTED_RECORD_TYPES},
            "analysis_id": {"type": "string", "minLength": 1},
            "source_prediction": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "prediction_id",
                    "baseline_name",
                    "baseline_run_id",
                    "scan_id",
                    "subgraph_id",
                    "subject_id",
                    "object_id",
                    "predicate_label",
                    "predicate_family",
                    "semantic_score",
                    "semantic_rank_in_subgraph",
                    "predicate_rank_for_pair",
                    "topk_membership",
                ],
                "properties": {
                    "prediction_id": {"type": "string"},
                    "baseline_name": {"type": "string", "enum": SUPPORTED_BASELINES},
                    "baseline_run_id": {"type": "string"},
                    "scan_id": {"type": "string"},
                    "subgraph_id": {"type": "string"},
                    "subject_id": {"type": ["integer", "string"]},
                    "object_id": {"type": ["integer", "string"]},
                    "subject_label": {"type": ["string", "null"]},
                    "object_label": {"type": ["string", "null"]},
                    "predicate_label": {"type": "string"},
                    "predicate_family": {"type": "string"},
                    "semantic_score": {"type": ["number", "null"]},
                    "semantic_rank_in_subgraph": {"type": ["integer", "null"]},
                    "predicate_rank_for_pair": {"type": ["integer", "null"]},
                    "topk_membership": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["top50", "top100"],
                        "properties": {
                            "top50": {"type": "boolean"},
                            "top100": {"type": "boolean"},
                        },
                    },
                },
            },
            "ground_truth": {
                "type": "object",
                "additionalProperties": False,
                "required": ["match_status", "matched_gt_ids"],
                "properties": {
                    "match_status": {
                        "type": "string",
                        "enum": [
                            "exact_match",
                            "family_match",
                            "pair_has_other_predicate",
                            "no_gt_for_pair",
                            "predicate_unlabeled_possible",
                            "not_joined",
                        ],
                    },
                    "matched_gt_ids": {"type": "array", "items": {"type": "string"}},
                    "matched_predicates": {"type": "array", "items": {"type": "string"}},
                    "in_h001_denominator": {"type": "boolean"},
                },
            },
            "geometry": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "geometry_available",
                    "geometry_checkable",
                    "verification_status",
                    "p_geom_valid",
                    "consistency_score",
                    "reason_codes",
                ],
                "properties": {
                    "geometry_available": {"type": "boolean"},
                    "geometry_checkable": {"type": "boolean"},
                    "verification_status": {
                        "type": "string",
                        "enum": ["satisfied", "violated", "uncertain", "unsupported", "missing_geometry", "join_error"],
                    },
                    "p_geom_valid": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
                    "consistency_score": {"type": ["number", "null"]},
                    "reason_codes": {"type": "array", "items": {"type": "string"}},
                    "geometry_source": {"type": ["string", "null"]},
                },
            },
            "rerank_effect": {
                "type": "object",
                "additionalProperties": False,
                "required": ["semantic_rank", "geometry_rank", "delta_rank", "topk_transition"],
                "properties": {
                    "semantic_rank": {"type": ["integer", "null"]},
                    "geometry_rank": {"type": ["integer", "null"]},
                    "delta_rank": {"type": ["integer", "null"]},
                    "topk_transition": {
                        "type": "string",
                        "enum": [
                            "promoted_into_top50",
                            "promoted_into_top100",
                            "demoted_out_of_top50",
                            "demoted_out_of_top100",
                            "stayed_in_topk",
                            "unchanged_outside_topk",
                            "filtered_by_rule",
                            "not_computed",
                        ],
                    },
                    "condition": {"type": ["string", "null"]},
                },
            },
            "failure_taxonomy": {
                "type": "object",
                "additionalProperties": False,
                "required": ["primary_category", "secondary_categories", "severity", "assignment_rule", "claim_use"],
                "properties": {
                    "primary_category": {"type": "string", "enum": category_values},
                    "secondary_categories": {"type": "array", "items": {"type": "string", "enum": category_values}},
                    "severity": {"type": "string", "enum": ["none", "low", "medium", "high", "critical"]},
                    "assignment_rule": {"type": "string"},
                    "claim_use": {
                        "type": "string",
                        "enum": [
                            "include_metric",
                            "positive_evidence",
                            "main_h001_failure",
                            "audit_queue",
                            "caveat_only",
                            "exclude_until_fixed",
                            "exclude_from_h001_family_claim",
                        ],
                    },
                },
            },
            "cross_source": {
                "type": "object",
                "additionalProperties": False,
                "required": ["vlsat_same_pair_status"],
                "properties": {
                    "vlsat_same_pair_status": {
                        "type": "string",
                        "enum": [
                            "not_joined",
                            "same_failure",
                            "open3dsg_specific_failure",
                            "vlsat_specific_failure",
                            "both_correct",
                            "pair_not_in_vlsat_source",
                            "unavailable",
                        ],
                    },
                    "vlsat_prediction_id": {"type": ["string", "null"]},
                },
            },
            "audit_hooks": {
                "type": "object",
                "additionalProperties": False,
                "required": ["needs_visual_audit", "artifact_paths"],
                "properties": {
                    "needs_visual_audit": {"type": "boolean"},
                    "artifact_paths": {
                        "type": "object",
                        "additionalProperties": {"type": ["string", "null"]},
                    },
                    "review_label": {"type": ["string", "null"]},
                    "reviewer_id": {"type": ["string", "null"]},
                },
            },
            "quality_flags": {
                "type": "object",
                "additionalProperties": False,
                "required": ["heldout_leakage_guard", "identity_preserved", "metric_eligible"],
                "properties": {
                    "heldout_leakage_guard": {"type": "boolean"},
                    "identity_preserved": {"type": "boolean"},
                    "metric_eligible": {"type": "boolean"},
                    "exclusion_reason": {"type": ["string", "null"]},
                },
            },
            "provenance": {
                "type": "object",
                "additionalProperties": False,
                "required": ["schema_locked_before_metric_inspection", "created_by", "inputs"],
                "properties": {
                    "schema_locked_before_metric_inspection": {"type": "boolean"},
                    "created_by": {"type": "string"},
                    "inputs": {"type": "object"},
                    "notes": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
    }


def taxonomy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "locked_before": "Open3DSG metric/failure inspection",
        "target_baselines": SUPPORTED_BASELINES,
        "compatibility_note": (
            "The taxonomy is unchanged; the schema now allows the same H001 diagnostic row contract "
            "to be applied to the VL-SAT closed-set source as well as Open3DSG."
        ),
        "assignment_priority": ASSIGNMENT_PRIORITY,
        "primary_categories": PRIMARY_CATEGORIES,
        "hard_rules": [
            "Do not create new primary categories after inspecting Open3DSG metric failures without bumping schema_version.",
            "Use plausible_unlabeled only with visual/audit evidence; do not use it to hide false positives.",
            "Rows with adapter_or_identity_error are excluded until fixed and cannot support method claims.",
            "Rows outside support_contact/proximity/relative_vertical are excluded from H001 family claims.",
            "Do not count preprocessing_or_filtering_limitation as an Open3DSG semantic failure.",
            "Do not use Qwen-VL outputs to assign Open3DSG failure categories.",
            "Use source-specific baseline_name/record_type fields; do not mix Open3DSG and VL-SAT rows in one metric without a source column.",
        ],
    }


def aggregation_plan() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "tables": [
            {
                "name": "source_failure_taxonomy_by_family",
                "group_by": ["predicate_family", "primary_category"],
                "metrics": ["count", "share_within_family", "top50_count", "top100_count"],
                "claim_use": "explains where geometry-consistency helps or fails for each semantic relation source.",
            },
            {
                "name": "source_geometry_status_by_category",
                "group_by": ["verification_status", "primary_category"],
                "metrics": ["count", "mean_p_geom_valid", "median_semantic_score"],
                "claim_use": "separates semantic failures from geometry contradictions and unsupported geometry.",
            },
            {
                "name": "source_rerank_transition",
                "group_by": ["topk_transition", "primary_category"],
                "metrics": ["count", "delta_R@50", "delta_R@100", "violation_delta"],
                "claim_use": "shows whether the reliability layer promotes valid rows or demotes contradicted rows.",
            },
            {
                "name": "cross_source_failure_overlap",
                "group_by": ["vlsat_same_pair_status", "primary_category"],
                "metrics": ["count", "share"],
                "claim_use": "distinguishes source-specific Open3DSG failures from repeated VL-SAT/Open3DSG weaknesses.",
            },
            {
                "name": "preprocess_and_exclusion_caveat",
                "group_by": ["exclusion_reason", "predicate_family"],
                "metrics": ["count"],
                "claim_use": "keeps filtered/preprocessing limitations visible in paper tables.",
            },
            {
                "name": "audit_queue_buckets",
                "group_by": ["primary_category", "severity", "needs_visual_audit"],
                "metrics": ["count", "sample_prediction_ids"],
                "claim_use": "defines qualitative review buckets before inspecting failure examples.",
            },
        ],
        "default_topk_cutoffs": [50, 100],
        "minimum_reported_columns": [
            "prediction_source",
            "predicate_family",
            "primary_category",
            "count",
            "share",
            "claim_use",
        ],
    }


def example_rows() -> list[dict[str, Any]]:
    base = {
        "schema_version": SCHEMA_VERSION,
        "record_type": "open3dsg_failure_analysis",
        "analysis_id": "example:open3dsg_ov:h001_validation_hardened:scan_001:1:2:supported_by",
        "source_prediction": {
            "prediction_id": "open3dsg_ov:h001_validation_hardened:scan_001_1:1:2:supported by",
            "baseline_name": "open3dsg_ov",
            "baseline_run_id": "open3dsg_repro_pending",
            "scan_id": "scan_001",
            "subgraph_id": "scan_001_1",
            "subject_id": 1,
            "object_id": 2,
            "subject_label": "chair",
            "object_label": "table",
            "predicate_label": "supported by",
            "predicate_family": "support_contact",
            "semantic_score": 0.82,
            "semantic_rank_in_subgraph": 12,
            "predicate_rank_for_pair": 1,
            "topk_membership": {"top50": True, "top100": True},
        },
        "ground_truth": {
            "match_status": "no_gt_for_pair",
            "matched_gt_ids": [],
            "matched_predicates": [],
            "in_h001_denominator": True,
        },
        "geometry": {
            "geometry_available": True,
            "geometry_checkable": True,
            "verification_status": "violated",
            "p_geom_valid": 0.03,
            "consistency_score": 0.08,
            "reason_codes": ["support_contact_no_overlap", "vertical_gap_too_large"],
            "geometry_source": "ply_points_v1+subtype_rules_v2",
        },
        "rerank_effect": {
            "semantic_rank": 12,
            "geometry_rank": 180,
            "delta_rank": 168,
            "topk_transition": "demoted_out_of_top50",
            "condition": "probabilistic_recalibrated",
        },
        "failure_taxonomy": {
            "primary_category": "semantic_and_geometry_failure",
            "secondary_categories": ["geometry_contradiction"],
            "severity": "high",
            "assignment_rule": "no GT match and verification_status=violated",
            "claim_use": "main_h001_failure",
        },
        "cross_source": {"vlsat_same_pair_status": "not_joined", "vlsat_prediction_id": None},
        "audit_hooks": {
            "needs_visual_audit": True,
            "artifact_paths": {"point_evidence": None, "crop": None, "projection": None},
            "review_label": None,
            "reviewer_id": None,
        },
        "quality_flags": {
            "heldout_leakage_guard": True,
            "identity_preserved": True,
            "metric_eligible": True,
            "exclusion_reason": None,
        },
        "provenance": {
            "schema_locked_before_metric_inspection": True,
            "created_by": "design_open3dsg_failure_analysis.py",
            "inputs": {"prediction_jsonl": "pending", "geometry_jsonl": "pending", "ground_truth_jsonl": "pending"},
            "notes": ["Example row only; not metric evidence."],
        },
    }
    unsupported = json.loads(json.dumps(base))
    unsupported["analysis_id"] = "example:open3dsg_ov:h001_validation_hardened:scan_001:1:2:attached_to"
    unsupported["source_prediction"]["predicate_label"] = "attached to"
    unsupported["source_prediction"]["predicate_family"] = "attachment_deferred"
    unsupported["geometry"]["geometry_checkable"] = False
    unsupported["geometry"]["verification_status"] = "unsupported"
    unsupported["geometry"]["p_geom_valid"] = None
    unsupported["geometry"]["consistency_score"] = None
    unsupported["geometry"]["reason_codes"] = ["predicate_family_out_of_scope:attachment_deferred"]
    unsupported["failure_taxonomy"] = {
        "primary_category": "unsupported_family_out_of_scope",
        "secondary_categories": [],
        "severity": "none",
        "assignment_rule": "predicate_family outside H001 target families",
        "claim_use": "exclude_from_h001_family_claim",
    }
    unsupported["rerank_effect"] = {
        "semantic_rank": 12,
        "geometry_rank": None,
        "delta_rank": None,
        "topk_transition": "not_computed",
        "condition": None,
    }
    unsupported["audit_hooks"]["needs_visual_audit"] = False
    unsupported["quality_flags"]["metric_eligible"] = False
    unsupported["quality_flags"]["exclusion_reason"] = "unsupported_family_out_of_scope"
    return [base, unsupported]


def validate_examples(rows: list[dict[str, Any]]) -> list[str]:
    allowed_categories = {item["category"] for item in PRIMARY_CATEGORIES}
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, 1):
        if row.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"row:{index}:bad_schema_version")
        analysis_id = row.get("analysis_id")
        if not analysis_id:
            errors.append(f"row:{index}:missing_analysis_id")
        elif analysis_id in seen_ids:
            errors.append(f"row:{index}:duplicate_analysis_id")
        seen_ids.add(str(analysis_id))
        category = row.get("failure_taxonomy", {}).get("primary_category")
        if category not in allowed_categories:
            errors.append(f"row:{index}:bad_primary_category:{category}")
        secondaries = row.get("failure_taxonomy", {}).get("secondary_categories", [])
        for secondary in secondaries:
            if secondary not in allowed_categories:
                errors.append(f"row:{index}:bad_secondary_category:{secondary}")
    return errors


def render_report(manifest: dict[str, Any], taxonomy_payload: dict[str, Any]) -> str:
    lines = [
        "# H001 Source Failure-Analysis Schema",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Scope",
        "",
        "This freezes the H001 failure-analysis row contract before source-specific metric/failure inspection.",
        "It does not run a relation source, inspect predictions, compute metrics, or assign real failure labels.",
        "The taxonomy is shared by Open3DSG and VL-SAT; each generated row still records its source-specific baseline name.",
        "",
        "## Primary Categories",
        "",
    ]
    for item in taxonomy_payload["primary_categories"]:
        lines.append(f"- `{item['category']}`: {item['definition']}")
    lines.extend(
        [
            "",
            "## Assignment Priority",
            "",
            "Categories are assigned in this fixed priority order:",
            "",
            ", ".join(f"`{item}`" for item in taxonomy_payload["assignment_priority"]),
            "",
            "## Outputs",
            "",
        ]
    )
    for name, path in manifest["outputs"].items():
        lines.append(f"- `{name}`: `{path}`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "Failure-analysis rows are diagnostic evidence only after they are generated from source-specific prediction JSONL, GT join, geometry join, and metric artifacts.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out)
    assert out_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True)

    schema_payload = failure_schema()
    taxonomy_payload = taxonomy()
    aggregation_payload = aggregation_plan()
    examples = example_rows()
    errors = validate_examples(examples)
    status = STATUS if not errors else "blocked_failure_analysis_schema_errors"
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    outputs = {
        "schema_json": relpath(repo_root, out_dir / "schema.json"),
        "taxonomy_json": relpath(repo_root, out_dir / "taxonomy.json"),
        "aggregation_plan_json": relpath(repo_root, out_dir / "aggregation_plan.json"),
        "example_jsonl": relpath(repo_root, out_dir / "example.jsonl"),
        "manifest": relpath(repo_root, out_dir / "manifest.json"),
        "report": relpath(repo_root, out_dir / "report.md"),
    }
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": created_at,
        "status": status,
        "runtime_policy": "schema_design_only_no_open3dsg_metric_run",
        "target": {
            "baseline_name": "open3dsg_ov",
            "split_name": "h001_validation_hardened",
            "predicate_families": ["support_contact", "proximity", "relative_vertical"],
        },
        "inputs": {
            "prediction_jsonl": "pending: experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl",
            "geometry_join_jsonl": "pending: Open3DSG predictions joined with H001 verifier outputs",
            "ground_truth_jsonl": "pending: H001 held-out GT export",
            "vlsat_comparison": "optional: vlsat_closed_set hardened rows",
        },
        "outputs": outputs,
        "counts": {
            "primary_categories": len(PRIMARY_CATEGORIES),
            "example_rows": len(examples),
            "aggregation_tables": len(aggregation_payload["tables"]),
        },
        "validation": {"errors": errors, "warnings": []},
        "next_action": "After Open3DSG prediction metrics exist, implement a generator that emits rows conforming to schema.json without changing taxonomy.json.",
    }

    write_json(out_dir / "schema.json", schema_payload)
    write_json(out_dir / "taxonomy.json", taxonomy_payload)
    write_json(out_dir / "aggregation_plan.json", aggregation_payload)
    write_jsonl(out_dir / "example.jsonl", examples)
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(render_report(manifest, taxonomy_payload), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
