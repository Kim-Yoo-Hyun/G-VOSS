#!/usr/bin/env python3
"""Generate Open3DSG failure-analysis rows from the locked H001 schema."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_failure_analysis_v1"
MANIFEST_SCHEMA_VERSION = "h001_open3dsg_failure_analysis_generator_manifest_v1"
SUMMARY_SCHEMA_VERSION = "h001_open3dsg_failure_analysis_summary_v1"
RECORD_TYPE = "open3dsg_failure_analysis"
BASELINE_NAME = "open3dsg_ov"
TARGET_FAMILIES = {"support_contact", "proximity", "relative_vertical"}
SMOKE_STATUS = "failure_analysis_generator_smoke_ready_no_metric_inspection"
BLOCKED_STATUS = "blocked_runtime_inputs_missing"


CLAIM_USE_BY_CATEGORY = {
    "true_positive_supported": "positive_evidence",
    "semantic_false_positive": "include_metric",
    "geometry_contradiction": "main_h001_failure",
    "semantic_and_geometry_failure": "main_h001_failure",
    "plausible_unlabeled": "caveat_only",
    "predicate_family_ambiguity": "caveat_only",
    "object_pair_mismatch": "exclude_until_fixed",
    "insufficient_geometry_evidence": "caveat_only",
    "preprocessing_or_filtering_limitation": "caveat_only",
    "unsupported_family_out_of_scope": "exclude_from_h001_family_claim",
    "rank_only_failure": "include_metric",
    "model_score_calibration_failure": "include_metric",
    "adapter_or_identity_error": "exclude_until_fixed",
    "unknown_needs_audit": "audit_queue",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/failure_analysis"),
    )
    parser.add_argument(
        "--predictions-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/adapter/predictions.jsonl"),
    )
    parser.add_argument(
        "--geometry-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl"),
    )
    parser.add_argument(
        "--ground-truth-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/ground_truth/ground_truth.jsonl"),
    )
    parser.add_argument(
        "--metrics-json",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/metrics/metrics.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/failure_analysis_generator_smoke"),
    )
    parser.add_argument("--split-name", default="h001_validation_hardened")
    parser.add_argument("--baseline-run-id", default="open3dsg_failure_generator_smoke")
    parser.add_argument("--smoke-test", action="store_true")
    return parser.parse_args()


def resolve(repo_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            handle.write("\n")


def json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    return False


def validate_schema(value: Any, schema: dict[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    expected_type = schema.get("type")
    if expected_type is not None:
        expected = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(type_matches(value, item) for item in expected):
            errors.append(f"{path}: expected {expected}, got {json_type(value)}")
            return errors

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}, got {value!r}")

    if isinstance(value, str) and "minLength" in schema and len(value) < int(schema["minLength"]):
        errors.append(f"{path}: string shorter than minLength {schema['minLength']}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and float(value) < float(schema["minimum"]):
            errors.append(f"{path}: below minimum {schema['minimum']}")
        if "maximum" in schema and float(value) > float(schema["maximum"]):
            errors.append(f"{path}: above maximum {schema['maximum']}")

    if isinstance(value, list) and "items" in schema:
        for index, item in enumerate(value):
            errors.extend(validate_schema(item, schema["items"], f"{path}[{index}]"))

    if isinstance(value, dict):
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                errors.append(f"{path}.{key}: missing required field")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in properties:
                    errors.append(f"{path}.{key}: additional property not allowed")
        for key, item in value.items():
            if key in properties:
                errors.extend(validate_schema(item, properties[key], f"{path}.{key}"))
    return errors


def taxonomy_categories(taxonomy: dict[str, Any]) -> set[str]:
    return {str(item["category"]) for item in taxonomy.get("primary_categories", [])}


def smoke_fixtures(split_name: str, baseline_run_id: str) -> list[dict[str, Any]]:
    base = {
        "baseline_name": BASELINE_NAME,
        "baseline_run_id": baseline_run_id,
        "split_name": split_name,
        "scan_id": "smoke_scan_001",
        "subgraph_id": "smoke_scan_001_0",
        "subject_id": 1,
        "object_id": 2,
        "subject_label": "chair",
        "object_label": "table",
        "semantic_score": 0.82,
        "semantic_rank_in_subgraph": 12,
        "predicate_rank_for_pair": 1,
        "matched_gt_ids": [],
        "matched_predicates": [],
        "in_h001_denominator": True,
        "geometry_source": "ply_points_v1+subtype_rules_v2",
        "geometry_available": True,
        "geometry_checkable": True,
        "vlsat_same_pair_status": "not_joined",
        "vlsat_prediction_id": None,
        "heldout_leakage_guard": True,
        "identity_preserved": True,
        "metric_eligible": True,
        "preprocessing_limitation": False,
    }
    fixtures = [
        {
            **base,
            "label": "semantic_and_geometry_failure",
            "predicate_label": "supported by",
            "predicate_family": "support_contact",
            "match_status": "no_gt_for_pair",
            "verification_status": "violated",
            "p_geom_valid": 0.03,
            "consistency_score": 0.08,
            "reason_codes": ["support_contact_no_overlap", "vertical_gap_too_large"],
            "semantic_rank": 12,
            "geometry_rank": 180,
            "delta_rank": 168,
            "topk_transition": "demoted_out_of_top50",
        },
        {
            **base,
            "label": "true_positive_supported",
            "scan_id": "smoke_scan_002",
            "subgraph_id": "smoke_scan_002_0",
            "subject_id": 3,
            "object_id": 4,
            "subject_label": "box",
            "object_label": "shelf",
            "predicate_label": "close by",
            "predicate_family": "proximity",
            "match_status": "exact_match",
            "matched_gt_ids": ["gt:smoke_scan_002_0:3:4:close by"],
            "matched_predicates": ["close by"],
            "verification_status": "satisfied",
            "p_geom_valid": 0.94,
            "consistency_score": 0.91,
            "reason_codes": ["near_distance_threshold_passed"],
            "semantic_rank_in_subgraph": 6,
            "semantic_rank": 6,
            "geometry_rank": 5,
            "delta_rank": -1,
            "topk_transition": "stayed_in_topk",
        },
        {
            **base,
            "label": "unsupported_family_out_of_scope",
            "scan_id": "smoke_scan_003",
            "subgraph_id": "smoke_scan_003_0",
            "subject_id": 5,
            "object_id": 6,
            "subject_label": "lamp",
            "object_label": "ceiling",
            "predicate_label": "attached to",
            "predicate_family": "attachment_deferred",
            "match_status": "no_gt_for_pair",
            "verification_status": "unsupported",
            "p_geom_valid": None,
            "consistency_score": None,
            "reason_codes": ["predicate_family_out_of_scope:attachment_deferred"],
            "geometry_checkable": False,
            "semantic_rank": 9,
            "geometry_rank": None,
            "delta_rank": None,
            "topk_transition": "not_computed",
            "metric_eligible": False,
        },
        {
            **base,
            "label": "adapter_or_identity_error",
            "scan_id": "smoke_scan_004",
            "subgraph_id": "smoke_scan_004_0",
            "subject_id": 7,
            "object_id": 8,
            "subject_label": "monitor",
            "object_label": "desk",
            "predicate_label": "higher than",
            "predicate_family": "relative_vertical",
            "match_status": "not_joined",
            "verification_status": "join_error",
            "p_geom_valid": None,
            "consistency_score": None,
            "reason_codes": ["object_id_missing_in_subgraph"],
            "geometry_available": False,
            "geometry_checkable": False,
            "semantic_rank": 18,
            "geometry_rank": None,
            "delta_rank": None,
            "topk_transition": "not_computed",
            "identity_preserved": False,
            "metric_eligible": False,
        },
        {
            **base,
            "label": "predicate_family_ambiguity",
            "scan_id": "smoke_scan_005",
            "subgraph_id": "smoke_scan_005_0",
            "subject_id": 9,
            "object_id": 10,
            "subject_label": "picture",
            "object_label": "cabinet",
            "predicate_label": "higher than",
            "predicate_family": "relative_vertical",
            "match_status": "family_match",
            "matched_gt_ids": ["gt:smoke_scan_005_0:9:10:lower than"],
            "matched_predicates": ["lower than"],
            "verification_status": "satisfied",
            "p_geom_valid": 0.88,
            "consistency_score": 0.86,
            "reason_codes": ["vertical_order_noncontradictory_family_match"],
            "semantic_rank": 21,
            "geometry_rank": 19,
            "delta_rank": -2,
            "topk_transition": "stayed_in_topk",
        },
        {
            **base,
            "label": "rank_only_failure",
            "scan_id": "smoke_scan_006",
            "subgraph_id": "smoke_scan_006_0",
            "subject_id": 11,
            "object_id": 12,
            "subject_label": "plant",
            "object_label": "floor",
            "predicate_label": "standing on",
            "predicate_family": "support_contact",
            "match_status": "exact_match",
            "matched_gt_ids": ["gt:smoke_scan_006_0:11:12:standing on"],
            "matched_predicates": ["standing on"],
            "verification_status": "satisfied",
            "p_geom_valid": 0.9,
            "consistency_score": 0.87,
            "reason_codes": ["support_contact_overlap_passed"],
            "semantic_score": 0.17,
            "semantic_rank_in_subgraph": 138,
            "predicate_rank_for_pair": 3,
            "semantic_rank": 138,
            "geometry_rank": 34,
            "delta_rank": -104,
            "topk_transition": "promoted_into_top50",
        },
    ]
    return fixtures


def assign_category(fixture: dict[str, Any]) -> tuple[str, str, list[str], str, str]:
    family = str(fixture["predicate_family"])
    match_status = str(fixture["match_status"])
    verification_status = str(fixture["verification_status"])
    if not fixture.get("identity_preserved", True):
        return (
            "adapter_or_identity_error",
            "critical",
            [],
            "identity_preserved=false or join failed",
            "open3dsg raw/adapted ids require repair before metric use",
        )
    if fixture.get("preprocessing_limitation", False):
        return (
            "preprocessing_or_filtering_limitation",
            "medium",
            [],
            "row affected by known preprocessing/filter limitation",
            "known preprocessing limitation controls metric eligibility",
        )
    if family not in TARGET_FAMILIES:
        return (
            "unsupported_family_out_of_scope",
            "none",
            [],
            "predicate_family outside H001 target families",
            "unsupported predicate family excluded from H001 family claim",
        )
    if match_status == "exact_match" and fixture.get("semantic_rank_in_subgraph") not in (None, ""):
        if int(fixture["semantic_rank_in_subgraph"]) > 100:
            return (
                "rank_only_failure",
                "low",
                [],
                "exact GT match exists but semantic rank is outside top100",
                "correct relation exists below evaluated semantic top-k",
            )
    if match_status == "exact_match" and verification_status in {"satisfied", "uncertain"}:
        return (
            "true_positive_supported",
            "none",
            [],
            "exact GT match and geometry is not contradicted",
            "positive evidence for metric sanity",
        )
    if match_status == "no_gt_for_pair" and verification_status == "violated":
        return (
            "semantic_and_geometry_failure",
            "high",
            ["geometry_contradiction"],
            "no GT match and verification_status=violated",
            "main H001 failure bucket",
        )
    if verification_status == "violated":
        return (
            "geometry_contradiction",
            "high",
            [],
            "verification_status=violated",
            "geometry contradicts the predicted relation",
        )
    if match_status == "family_match":
        return (
            "predicate_family_ambiguity",
            "medium",
            [],
            "family GT match without exact predicate match",
            "predicate granularity caveat",
        )
    if verification_status in {"uncertain", "missing_geometry"}:
        return (
            "insufficient_geometry_evidence",
            "medium",
            [],
            "geometry evidence is insufficient for a stable decision",
            "geometry evidence caveat",
        )
    if match_status in {"no_gt_for_pair", "pair_has_other_predicate"}:
        return (
            "semantic_false_positive",
            "medium",
            [],
            "prediction is unsupported by GT and not geometrically contradicted",
            "semantic false positive diagnostic",
        )
    return (
        "unknown_needs_audit",
        "medium",
        [],
        "available fields do not match a higher-priority rule",
        "requires sampled audit before claim use",
    )


def build_row(fixture: dict[str, Any]) -> dict[str, Any]:
    category, severity, secondaries, assignment_rule, note = assign_category(fixture)
    predicate_label = str(fixture["predicate_label"])
    prediction_id = (
        f"{BASELINE_NAME}:{fixture['split_name']}:{fixture['subgraph_id']}:"
        f"{fixture['subject_id']}:{fixture['object_id']}:{predicate_label}"
    )
    semantic_rank = fixture.get("semantic_rank_in_subgraph")
    top50 = isinstance(semantic_rank, int) and semantic_rank <= 50
    top100 = isinstance(semantic_rank, int) and semantic_rank <= 100
    metric_eligible = bool(fixture.get("metric_eligible", True))
    exclusion_reason = None
    if not metric_eligible:
        exclusion_reason = category
    needs_visual_audit = category in {
        "semantic_and_geometry_failure",
        "geometry_contradiction",
        "plausible_unlabeled",
        "unknown_needs_audit",
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": RECORD_TYPE,
        "analysis_id": f"smoke:{prediction_id.replace(' ', '_')}",
        "source_prediction": {
            "prediction_id": prediction_id,
            "baseline_name": BASELINE_NAME,
            "baseline_run_id": str(fixture["baseline_run_id"]),
            "scan_id": str(fixture["scan_id"]),
            "subgraph_id": str(fixture["subgraph_id"]),
            "subject_id": fixture["subject_id"],
            "object_id": fixture["object_id"],
            "subject_label": fixture.get("subject_label"),
            "object_label": fixture.get("object_label"),
            "predicate_label": predicate_label,
            "predicate_family": str(fixture["predicate_family"]),
            "semantic_score": fixture.get("semantic_score"),
            "semantic_rank_in_subgraph": semantic_rank,
            "predicate_rank_for_pair": fixture.get("predicate_rank_for_pair"),
            "topk_membership": {"top50": top50, "top100": top100},
        },
        "ground_truth": {
            "match_status": str(fixture["match_status"]),
            "matched_gt_ids": [str(item) for item in fixture.get("matched_gt_ids", [])],
            "matched_predicates": [str(item) for item in fixture.get("matched_predicates", [])],
            "in_h001_denominator": bool(fixture.get("in_h001_denominator", True)),
        },
        "geometry": {
            "geometry_available": bool(fixture["geometry_available"]),
            "geometry_checkable": bool(fixture["geometry_checkable"]),
            "verification_status": str(fixture["verification_status"]),
            "p_geom_valid": fixture.get("p_geom_valid"),
            "consistency_score": fixture.get("consistency_score"),
            "reason_codes": [str(item) for item in fixture.get("reason_codes", [])],
            "geometry_source": fixture.get("geometry_source"),
        },
        "rerank_effect": {
            "semantic_rank": fixture.get("semantic_rank"),
            "geometry_rank": fixture.get("geometry_rank"),
            "delta_rank": fixture.get("delta_rank"),
            "topk_transition": str(fixture["topk_transition"]),
            "condition": "probabilistic_recalibrated" if fixture.get("geometry_rank") is not None else None,
        },
        "failure_taxonomy": {
            "primary_category": category,
            "secondary_categories": secondaries,
            "severity": severity,
            "assignment_rule": assignment_rule,
            "claim_use": CLAIM_USE_BY_CATEGORY[category],
        },
        "cross_source": {
            "vlsat_same_pair_status": str(fixture["vlsat_same_pair_status"]),
            "vlsat_prediction_id": fixture.get("vlsat_prediction_id"),
        },
        "audit_hooks": {
            "needs_visual_audit": needs_visual_audit,
            "artifact_paths": {"point_evidence": None, "crop": None, "projection": None},
            "review_label": None,
            "reviewer_id": None,
        },
        "quality_flags": {
            "heldout_leakage_guard": bool(fixture["heldout_leakage_guard"]),
            "identity_preserved": bool(fixture["identity_preserved"]),
            "metric_eligible": metric_eligible,
            "exclusion_reason": exclusion_reason,
        },
        "provenance": {
            "schema_locked_before_metric_inspection": True,
            "created_by": "generate_open3dsg_failure_analysis.py",
            "inputs": {
                "prediction_jsonl": "synthetic_smoke_fixture",
                "geometry_jsonl": "synthetic_smoke_fixture",
                "ground_truth_jsonl": "synthetic_smoke_fixture",
            },
            "notes": [
                "Synthetic smoke row only; not metric evidence.",
                note,
            ],
        },
    }


def validate_rows(rows: list[dict[str, Any]], schema: dict[str, Any], taxonomy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    categories = taxonomy_categories(taxonomy)
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, 1):
        errors.extend(validate_schema(row, schema, f"row[{index}]"))
        analysis_id = str(row.get("analysis_id", ""))
        if not analysis_id:
            errors.append(f"row[{index}]: missing analysis_id")
        elif analysis_id in seen_ids:
            errors.append(f"row[{index}]: duplicate analysis_id {analysis_id}")
        seen_ids.add(analysis_id)
        category = row.get("failure_taxonomy", {}).get("primary_category")
        if category not in categories:
            errors.append(f"row[{index}]: primary_category not in locked taxonomy: {category}")
        for secondary in row.get("failure_taxonomy", {}).get("secondary_categories", []):
            if secondary not in categories:
                errors.append(f"row[{index}]: secondary_category not in locked taxonomy: {secondary}")
    return errors


def summarize(rows: list[dict[str, Any]], status: str) -> dict[str, Any]:
    by_primary = Counter(row["failure_taxonomy"]["primary_category"] for row in rows)
    by_claim = Counter(row["failure_taxonomy"]["claim_use"] for row in rows)
    by_family = Counter(row["source_prediction"]["predicate_family"] for row in rows)
    by_transition = Counter(row["rerank_effect"]["topk_transition"] for row in rows)
    audit_count = sum(1 for row in rows if row["audit_hooks"]["needs_visual_audit"])
    eligible_count = sum(1 for row in rows if row["quality_flags"]["metric_eligible"])
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "status": status,
        "source": "synthetic_smoke_fixtures",
        "row_count": len(rows),
        "metric_eligible_count": eligible_count,
        "visual_audit_queue_count": audit_count,
        "by_primary_category": dict(sorted(by_primary.items())),
        "by_claim_use": dict(sorted(by_claim.items())),
        "by_predicate_family": dict(sorted(by_family.items())),
        "by_topk_transition": dict(sorted(by_transition.items())),
    }


def blocked_outputs(
    repo_root: Path,
    out_dir: Path,
    schema_dir: Path,
    input_paths: dict[str, Path],
    errors: list[str],
    created_at: str,
    status: str = BLOCKED_STATUS,
) -> None:
    outputs = {
        "rows_jsonl": relpath(repo_root, out_dir / "rows.jsonl"),
        "summary_json": relpath(repo_root, out_dir / "summary.json"),
        "manifest_json": relpath(repo_root, out_dir / "manifest.json"),
        "report_md": relpath(repo_root, out_dir / "report.md"),
    }
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": created_at,
        "status": status,
        "mode": "runtime_generation",
        "runtime_policy": "do_not_generate_real_rows_until prediction, GT, geometry, and metric artifacts exist",
        "schema_dir": relpath(repo_root, schema_dir),
        "inputs": {name: relpath(repo_root, path) for name, path in input_paths.items()},
        "missing_inputs": errors if status == BLOCKED_STATUS else [],
        "outputs": outputs,
        "validation": {"errors": errors, "warnings": []},
        "next_action": "Complete Open3DSG prediction JSONL, GT join, geometry join, and metric outputs before real row generation.",
    }
    write_jsonl(out_dir / "rows.jsonl", [])
    write_json(out_dir / "summary.json", summarize([], status))
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(render_report(manifest, summarize([], status)), encoding="utf-8")


def render_report(manifest: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG Failure-Analysis Row Generator",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        f"Mode: `{manifest['mode']}`",
        "",
        "## Scope",
        "",
        "This validates the row-generation contract against the locked Open3DSG failure-analysis schema.",
    ]
    if manifest["mode"] == "synthetic_smoke":
        lines.extend(
            [
                "Rows are synthetic smoke fixtures only and must not be used as metric evidence.",
                "The generator does not inspect Open3DSG metric failures.",
            ]
        )
    else:
        lines.append("Real generation is blocked until all runtime inputs exist.")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- rows: `{summary['row_count']}`",
            f"- metric eligible rows: `{summary['metric_eligible_count']}`",
            f"- visual audit queue rows: `{summary['visual_audit_queue_count']}`",
            "",
            "## Primary Categories",
            "",
        ]
    )
    for category, count in summary["by_primary_category"].items():
        lines.append(f"- `{category}`: {count}")
    lines.extend(["", "## Outputs", ""])
    for name, path in manifest["outputs"].items():
        lines.append(f"- `{name}`: `{path}`")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "These rows are contract/implementation smoke evidence only until regenerated from a reproduced Open3DSG checkpoint, identity-preserving raw dump, H001 prediction JSONL, geometry join, and metric run.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    schema_dir = resolve(repo_root, args.schema_dir)
    out_dir = resolve(repo_root, args.out)
    assert schema_dir is not None
    assert out_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    schema_path = schema_dir / "schema.json"
    taxonomy_path = schema_dir / "taxonomy.json"
    if not schema_path.exists() or not taxonomy_path.exists():
        errors = [f"missing_schema_artifact:{relpath(repo_root, path)}" for path in [schema_path, taxonomy_path] if not path.exists()]
        manifest = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "created_at": created_at,
            "status": "blocked_locked_schema_missing",
            "mode": "synthetic_smoke" if args.smoke_test else "runtime_generation",
            "runtime_policy": "locked schema/taxonomy must exist before row generation",
            "outputs": {
                "manifest_json": relpath(repo_root, out_dir / "manifest.json"),
                "report_md": relpath(repo_root, out_dir / "report.md"),
            },
            "validation": {"errors": errors, "warnings": []},
        }
        write_json(out_dir / "manifest.json", manifest)
        write_json(out_dir / "summary.json", summarize([], manifest["status"]))
        (out_dir / "report.md").write_text(render_report(manifest, summarize([], manifest["status"])), encoding="utf-8")
        print(json.dumps({"status": manifest["status"], "errors": errors}, sort_keys=True))
        return 1

    schema = load_json(schema_path)
    taxonomy = load_json(taxonomy_path)
    input_paths = {
        "predictions_jsonl": resolve(repo_root, args.predictions_jsonl),
        "geometry_jsonl": resolve(repo_root, args.geometry_jsonl),
        "ground_truth_jsonl": resolve(repo_root, args.ground_truth_jsonl),
        "metrics_json": resolve(repo_root, args.metrics_json),
    }
    assert all(path is not None for path in input_paths.values())
    resolved_inputs = {name: path for name, path in input_paths.items() if path is not None}

    if not args.smoke_test:
        missing_inputs = [f"missing_input:{name}:{relpath(repo_root, path)}" for name, path in resolved_inputs.items() if not path.exists()]
        if missing_inputs:
            blocked_outputs(repo_root, out_dir, schema_dir, resolved_inputs, missing_inputs, created_at)
            print(json.dumps({"status": BLOCKED_STATUS, "missing_inputs": missing_inputs}, sort_keys=True))
            return 1
        status = "blocked_real_generation_not_implemented"
        errors = ["real_generation_requires_explicit_join_contract_freeze_after_open3dsg_metrics_exist"]
        blocked_outputs(repo_root, out_dir, schema_dir, resolved_inputs, errors, created_at, status=status)
        print(json.dumps({"status": status, "errors": errors}, sort_keys=True))
        return 1

    rows = [build_row(fixture) for fixture in smoke_fixtures(args.split_name, args.baseline_run_id)]
    errors = validate_rows(rows, schema, taxonomy)
    status = SMOKE_STATUS if not errors else "blocked_failure_analysis_generator_smoke_validation_errors"
    summary = summarize(rows, status)
    outputs = {
        "rows_jsonl": relpath(repo_root, out_dir / "rows.jsonl"),
        "summary_json": relpath(repo_root, out_dir / "summary.json"),
        "manifest_json": relpath(repo_root, out_dir / "manifest.json"),
        "report_md": relpath(repo_root, out_dir / "report.md"),
    }
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": created_at,
        "status": status,
        "mode": "synthetic_smoke",
        "runtime_policy": "synthetic smoke only; no Open3DSG metric/failure inspection",
        "schema_dir": relpath(repo_root, schema_dir),
        "inputs": {
            "schema_json": relpath(repo_root, schema_path),
            "taxonomy_json": relpath(repo_root, taxonomy_path),
            "prediction_jsonl": "synthetic_smoke_fixture",
            "geometry_jsonl": "synthetic_smoke_fixture",
            "ground_truth_jsonl": "synthetic_smoke_fixture",
            "metrics_json": "not_read",
        },
        "outputs": outputs,
        "counts": {
            "rows": len(rows),
            "locked_primary_categories": len(taxonomy_categories(taxonomy)),
            "smoke_primary_categories": len(summary["by_primary_category"]),
        },
        "summary": summary,
        "validation": {"errors": errors, "warnings": []},
        "next_action": "After Open3DSG prediction JSONL, GT join, geometry join, and metric outputs exist, replace synthetic fixtures with real joins without changing taxonomy.json.",
    }
    write_jsonl(out_dir / "rows.jsonl", rows)
    write_json(out_dir / "summary.json", summary)
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(render_report(manifest, summary), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, out_dir), "rows": len(rows)}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
