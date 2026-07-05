#!/usr/bin/env python3
"""Plan the H002 v24 RGA benchmark and target-identifiability reframing."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_V80_DIR = RGA_ROOT / "reliability_target_v23_hanging_on_positive_anchor_path_decision_after_blocker_synthesis"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v24_rga_benchmark_reframing_plan"

EXPECTED_V80_STATUS = (
    "h002_reliability_target_v23_hanging_on_positive_anchor_path_decision_"
    "freeze_diagnostic_select_v24_rga_reframing"
)
EXPECTED_V80_NEXT = "reliability_target_v24_rga_benchmark_reframing_plan"

STATUS = "h002_reliability_target_v24_rga_benchmark_reframing_plan_ready_for_failure_taxonomy_materialization"
STATUS_ERROR = "h002_reliability_target_v24_rga_benchmark_reframing_plan_validation_errors"
NEXT_TODO = "reliability_target_v24_rga_failure_taxonomy_materialization"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v80-dir", type=Path, default=DEFAULT_V80_DIR)
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


def validate_v80(v80: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if v80.get("status") != EXPECTED_V80_STATUS:
        errors.append({"error_type": "unexpected_v80_status", "expected": EXPECTED_V80_STATUS, "actual": v80.get("status")})
    if v80.get("next_todo") != EXPECTED_V80_NEXT:
        errors.append({"error_type": "unexpected_v80_next", "expected": EXPECTED_V80_NEXT, "actual": v80.get("next_todo")})
    if v80.get("validation_errors") != 0:
        errors.append({"error_type": "v80_validation_errors_present", "actual": v80.get("validation_errors")})
    path = v80.get("path_decision", {})
    if path.get("claim_boundary", {}).get("factorized_posterior_claim_allowed") is not False:
        errors.append({"error_type": "posterior_claim_unexpectedly_allowed", "actual": path.get("claim_boundary", {}).get("factorized_posterior_claim_allowed")})
    if path.get("selected_next_todo") != EXPECTED_V80_NEXT:
        errors.append({"error_type": "unexpected_selected_next_todo", "expected": EXPECTED_V80_NEXT, "actual": path.get("selected_next_todo")})
    review = v80.get("direction_review", {})
    if review.get("verdict", {}).get("conceptual_direction") != "valid_and_worth_preserving":
        errors.append({"error_type": "unexpected_conceptual_direction", "actual": review.get("verdict", {}).get("conceptual_direction")})
    if review.get("verdict", {}).get("current_operational_route") != "not_ready_for_posterior_method_claim":
        errors.append({"error_type": "unexpected_operational_route", "actual": review.get("verdict", {}).get("current_operational_route")})
    boundary = v80.get("boundary", {})
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
            errors.append({"error_type": "v80_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def build_failure_taxonomy(v80: dict[str, Any]) -> dict[str, Any]:
    historical = v80["direction_review"]["historical_blockers"]
    return {
        "schema_version": "h002_v24_rga_failure_taxonomy_plan_v1",
        "purpose": "Consolidate relation-family-specific H002 blockers before any posterior method claim.",
        "families": [
            {
                "family": "proximity",
                "predicates": ["close by"],
                "observed_pattern": "LH-only capacity under current RGA queues; visible-only reliability target remains shortcut-prone.",
                "primary_blockers": [
                    "object-pair/block shortcut risk",
                    "no bidirectional HL/LH target under current queue",
                    "incomplete GT makes no-GT reliable cases ambiguous",
                ],
                "benchmark_role": "generality diagnostic for low-semantic/high-geometry mismatch and annotation sparsity.",
            },
            {
                "family": "support_contact",
                "predicates": ["standing on", "lying on", "supported by"],
                "observed_pattern": "Raw row capacity exists, but HL/LH and geometry_status become entangled.",
                "primary_blockers": [
                    "geometry-status shortcut",
                    "positive-sparse reliability labels after audit",
                    "same-witness matching too restrictive",
                ],
                "benchmark_role": "main diagnostic for physical witness validity and shortcut-safe support/contact target construction.",
            },
            {
                "family": "relative_vertical",
                "predicates": ["higher than", "lower than"],
                "observed_pattern": "Geometry is comparatively easy to compute, so it works better as a control family than a main reliability target.",
                "primary_blockers": [
                    "too geometry-determined for proving factorized reliability",
                    "useful as a sanity/control axis rather than a hard posterior target",
                ],
                "benchmark_role": "control family for geometry witness sanity, rank/semantic interaction, and audit calibration.",
            },
            {
                "family": "attachment_deferred",
                "predicates": ["attached to", "hanging on", "connected to"],
                "observed_pattern": "Typed geometric witness can be joined, but visual/mesh audit labels are reject-heavy or concentrated in few cells.",
                "primary_blockers": [
                    "functional/attachment ambiguity from OBB-only geometry",
                    "positive reliability sparsity after visual/mesh audit",
                    "matched-cell diversity blocker for positive-anchor route",
                    "connected-to requires functional evidence beyond simple contact",
                ],
                "benchmark_role": "diagnostic family for when geometry-only witnesses are insufficient and audit evidence is required.",
            },
            {
                "family": "relative_horizontal_deferred",
                "predicates": ["left", "right", "front", "behind"],
                "observed_pattern": "Deferred; likely viewpoint/frame-dependent and should not be added before RGA benchmark schema is fixed.",
                "primary_blockers": [
                    "coordinate frame ambiguity",
                    "viewpoint dependence",
                    "not yet scanned in the current H002 route",
                ],
                "benchmark_role": "future generality family after core RGA schema stabilizes.",
            },
        ],
        "historical_blockers_from_v80": historical,
    }


def build_benchmark_plan(v80: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h002_v24_rga_benchmark_reframing_plan_v1",
        "problem_statement": (
            "Evaluate relation candidates by explicitly separating source semantic plausibility, relation-specific geometric validity, "
            "coverage/uncertainty, and audit reliability, and by auditing whether any learned reliability target is identifiable "
            "beyond construction shortcuts."
        ),
        "core_claim_boundary": {
            "allowed_now": [
                "RGA exposes semantic-geometry mismatch states and target-construction blockers.",
                "Relation families show different failure mechanisms under the same source candidate pool.",
                "Posterior modeling must be gated by target-identifiability checks.",
            ],
            "blocked_now": [
                "factorized posterior improves relation reliability",
                "current labels are a paper-level human benchmark",
                "multi-view or mesh is a deployable model input",
                "attachment_deferred is solved as a main target",
            ],
        },
        "benchmark_units": {
            "row_unit": "relation candidate edge e=(subject,predicate,object)",
            "scope_keys": ["source", "split", "scan_id", "subgraph_id", "directed_pair_id", "predicate_family", "predicate_label"],
            "hidden_sampling_keys": ["rank_band", "queue_kind", "geometry_bucket", "strict_group", "proxy_role"],
            "visible_audit_keys": ["subject_label", "predicate_label", "object_label", "geometry_or_visual_evidence_summary"],
        },
        "rga_axes": {
            "semantic_axis": ["source_score_or_rank", "rank_band", "source_relation_family", "semantic_prior_bucket"],
            "geometry_axis": ["predicate_family", "witness_status", "p_geom_valid_or_residual", "geometry_bucket"],
            "coverage_axis": ["raw_geometry_join_state", "view_or_mesh_availability", "evidence_tier"],
            "uncertainty_axis": ["missing_evidence", "functional_ambiguity", "thin_structure_or_boundary", "annotation_sparsity"],
            "audit_axis": ["accept_reliable", "reject_unreliable", "abstain_uncertain", "gt_match_auxiliary"],
            "identifiability_axis": ["shortcut_probe", "mixed_cell_capacity", "class_mass", "controlled_slice_status"],
        },
        "benchmark_tasks": [
            {
                "task": "RGA state assignment",
                "goal": "Assign semantic-geometry agreement/mismatch states per edge without treating them as final reliability labels.",
                "outputs": ["RGA-HL", "RGA-LH", "agreement_high_high", "agreement_low_low", "uncertain", "missing_or_unsupported"],
            },
            {
                "task": "relation-family witness audit",
                "goal": "Report which relation families have reliable geometric witnesses and which require visual/mesh confirmation.",
                "outputs": ["family_witness_coverage", "family_invalid_rate_proxy", "coverage_uncertainty_rate"],
            },
            {
                "task": "target-identifiability audit",
                "goal": "Test whether a candidate reliability target requires factorized evidence rather than shortcuts.",
                "outputs": ["class_mass_pass", "mixed_cell_capacity", "shortcut_probe_risk", "strict_clear_slice_count"],
            },
            {
                "task": "failure taxonomy",
                "goal": "Categorize failure mechanisms by relation family before claiming a posterior method.",
                "outputs": ["family_blocker_table", "failure_mode_counts", "recommended_next_source"],
            },
            {
                "task": "posterior gate",
                "goal": "Allow posterior smoke only when target-identifiability gates pass.",
                "outputs": ["posterior_allowed_boolean", "required_baselines", "required_controls"],
            },
        ],
        "metrics": [
            "RGA-HL rate by relation family",
            "RGA-LH rate by relation family",
            "semantic-geometry agreement matrix",
            "geometry witness coverage",
            "coverage/uncertainty rate",
            "mixed-cell capacity under controlled strata",
            "shortcut-probe risk count",
            "class-mass balance",
            "GT/reliability mismatch table",
            "family-specific blocker taxonomy",
        ],
        "posterior_gate": {
            "minimum_binary_rows": 160,
            "minimum_positive_rows": 60,
            "minimum_negative_rows": 60,
            "strict_clear_slice_count_min": 1,
            "mixed_cell_count_min": 30,
            "shortcut_probe_must_pass": True,
            "validation_or_test_allowed": False,
            "multi_view_as_model_input_allowed": False,
        },
    }


def build_target_identifiability_contract() -> dict[str, Any]:
    return {
        "schema_version": "h002_v24_target_identifiability_contract_v1",
        "definition": (
            "A reliability target is identifiable for factorized posterior smoke only if the target cannot be explained "
            "by a single construction shortcut such as predicate, endpoint, object label, source rank, geometry status, "
            "or packet/source availability."
        ),
        "must_pass_before_posterior": [
            "class mass gate",
            "controlled mixed-cell gate",
            "shortcut-probe gate",
            "hidden-field leakage gate",
            "train-only provenance gate",
            "audit-label independence gate",
        ],
        "known_shortcut_axes": [
            "predicate_label",
            "subject_label",
            "object_label",
            "visible_endpoint_pair",
            "scan_id",
            "subgraph_id",
            "rank_band",
            "machine_hint",
            "geometry_status",
            "p_geom_valid_bin",
            "proxy_role",
            "strict_group",
            "evidence_tier",
            "packet_availability",
        ],
        "posterior_allowed_only_if": {
            "labels_are_locked_before_hidden_join": True,
            "hidden_fields_not_visible_to_reviewer": True,
            "validation_or_test_usage": False,
            "shortcut_probe_pass": True,
            "class_mass_pass": True,
            "controlled_slice_pass": True,
        },
        "recommended_annotation_design": [
            "sample target strata first",
            "hide all construction fields from annotators",
            "include visual/mesh evidence only as audit evidence, not model input",
            "use accept/reject/abstain labels",
            "record GT match as auxiliary metadata after label lock",
            "compute target-independence before any model run",
        ],
    }


def build_report(summary: dict[str, Any]) -> str:
    plan = summary["benchmark_plan"]
    taxonomy = summary["failure_taxonomy"]
    contract = summary["target_identifiability_contract"]
    lines = [
        "# V81 RGA Benchmark Reframing Plan",
        "",
        "## Purpose",
        "",
        "Reframe H002 from immediate posterior-target mining into an RGA benchmark and target-identifiability framework.",
        "This step creates no labels and runs no posterior model.",
        "",
        "## Decision",
        "",
        "```text",
        f"status = {summary['status']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "posterior_smoke_allowed = false",
        "```",
        "",
        "## Benchmark Problem",
        "",
        plan["problem_statement"],
        "",
        "## Relation-Family Taxonomy",
        "",
    ]
    for family in taxonomy["families"]:
        lines.append(f"- `{family['family']}`: {family['observed_pattern']} Benchmark role: {family['benchmark_role']}")
    lines.extend(
        [
            "",
            "## Benchmark Tasks",
            "",
        ]
    )
    for task in plan["benchmark_tasks"]:
        lines.append(f"- `{task['task']}`: {task['goal']}")
    lines.extend(
        [
            "",
            "## Posterior Gate",
            "",
            "Posterior smoke remains blocked until the target-identifiability contract passes.",
            "",
            "Required gates:",
        ]
    )
    lines.extend(f"- {item}" for item in contract["must_pass_before_posterior"])
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "Materialize the relation-family failure taxonomy from existing artifacts and prepare benchmark-facing tables.",
            "",
            "## Boundary",
            "",
            "- Train-only H002 hypothesis artifact.",
            "- No validation/test rows were used.",
            "- No H001 artifact was modified.",
            "- No new labels were created.",
            "- No posterior was trained or evaluated.",
            "- Multi-view and mesh remain audit/confirmation evidence only.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_benchmark_schema_md(plan: dict[str, Any], contract: dict[str, Any]) -> str:
    lines = [
        "# RGA Benchmark Schema Plan",
        "",
        "## Unit",
        "",
        f"Row unit: `{plan['benchmark_units']['row_unit']}`.",
        "",
        "## Axes",
        "",
    ]
    for axis, fields in plan["rga_axes"].items():
        lines.append(f"- `{axis}`: {', '.join(fields)}")
    lines.extend(
        [
            "",
            "## Metrics",
            "",
        ]
    )
    lines.extend(f"- {metric}" for metric in plan["metrics"])
    lines.extend(
        [
            "",
            "## Posterior Gate",
            "",
        ]
    )
    for key, value in plan["posterior_gate"].items():
        lines.append(f"- `{key}` = {value}")
    lines.extend(
        [
            "",
            "## Known Shortcut Axes",
            "",
        ]
    )
    lines.extend(f"- `{axis}`" for axis in contract["known_shortcut_axes"])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    v80_dir = as_abs(args.v80_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    v80 = read_json(v80_dir / "summary.json")
    validation_errors = validate_v80(v80)
    failure_taxonomy = build_failure_taxonomy(v80)
    benchmark_plan = build_benchmark_plan(v80)
    target_contract = build_target_identifiability_contract()

    status = STATUS_ERROR if validation_errors else STATUS
    next_todo = EXPECTED_V80_NEXT if validation_errors else NEXT_TODO
    summary = {
        "schema_version": "h002_reliability_target_v24_rga_benchmark_reframing_plan_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "split": "train_only",
        "benchmark_plan": benchmark_plan,
        "failure_taxonomy": failure_taxonomy,
        "target_identifiability_contract": target_contract,
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
            "v80_summary": rel_path(v80_dir / "summary.json"),
            "v80_report": rel_path(v80_dir / "report.md"),
            "v80_direction_review": rel_path(v80_dir / "direction_review.md"),
        },
        "outputs": {
            "summary": rel_path(output_dir / "summary.json"),
            "benchmark_plan": rel_path(output_dir / "rga_benchmark_plan.json"),
            "failure_taxonomy": rel_path(output_dir / "failure_taxonomy.json"),
            "target_identifiability_contract": rel_path(output_dir / "target_identifiability_contract.json"),
            "benchmark_schema": rel_path(output_dir / "benchmark_schema.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
            "report": rel_path(output_dir / "report.md"),
        },
    }

    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "rga_benchmark_plan.json", benchmark_plan)
    write_json(output_dir / "failure_taxonomy.json", failure_taxonomy)
    write_json(output_dir / "target_identifiability_contract.json", target_contract)
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    (output_dir / "benchmark_schema.md").write_text(build_benchmark_schema_md(benchmark_plan, target_contract), encoding="utf-8")
    (output_dir / "report.md").write_text(build_report(summary), encoding="utf-8")

    print(f"status={status}")
    print(f"next_todo={next_todo}")
    print(f"validation_errors={len(validation_errors)}")
    print("posterior_smoke_allowed=false")
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
