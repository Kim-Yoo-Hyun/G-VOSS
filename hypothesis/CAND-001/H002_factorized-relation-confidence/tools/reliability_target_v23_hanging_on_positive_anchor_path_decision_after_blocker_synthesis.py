#!/usr/bin/env python3
"""Decide the H002 path after the v23 hanging-on positive-anchor blocker synthesis."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H002_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_full/open3dsg_train_full/rga"

DEFAULT_BLOCKER_DIR = RGA_ROOT / "reliability_target_v23_hanging_on_positive_anchor_blocker_synthesis"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "reliability_target_v23_hanging_on_positive_anchor_path_decision_after_blocker_synthesis"

EXPECTED_BLOCKER_STATUS = (
    "h002_reliability_target_v23_hanging_on_positive_anchor_blocker_synthesis_ready_for_path_decision"
)
EXPECTED_BLOCKER_NEXT = "reliability_target_v23_hanging_on_positive_anchor_path_decision_after_blocker_synthesis"

STATUS = (
    "h002_reliability_target_v23_hanging_on_positive_anchor_path_decision_"
    "freeze_diagnostic_select_v24_rga_reframing"
)
STATUS_ERROR = "h002_reliability_target_v23_hanging_on_positive_anchor_path_decision_validation_errors"
SELECTED_PATH = "freeze_v23_diagnostic_select_v24_rga_benchmark_reframing_plan"
NEXT_TODO = "reliability_target_v24_rga_benchmark_reframing_plan"


HISTORICAL_BLOCKERS = [
    {
        "stage": "v13_proximity_scene_geometry",
        "relation_scope": "close by / proximity",
        "evidence": "binary target 39/137 after scene-geometry labels; strict clear slices 0",
        "blocker": "positive sparsity plus object-pair/block shortcut risk",
        "lesson": "more visible scene/geometry context did not produce an independent reliability target",
    },
    {
        "stage": "v14_physical_relation_family",
        "relation_scope": "support_contact + relative_vertical",
        "evidence": "binary target 48/152; strict/diagnostic clear slices 0",
        "blocker": "positive sparsity and shortcut risk remained after physical-family sampling",
        "lesson": "family-balanced row mining is not enough without within-stratum accept/reject variation",
    },
    {
        "stage": "v16_cross_stratum_support_contact",
        "relation_scope": "lying on / standing on / lower than",
        "evidence": "raw quota sufficient, but lying-on HL all unsatisfied and LH all satisfied; mixed primary blocks 4",
        "blocker": "queue side became almost equivalent to geometry_status",
        "lesson": "HL/LH mismatch labels can collapse into a geometry-status shortcut",
    },
    {
        "stage": "v20_endpoint_balanced_attachment",
        "relation_scope": "attached to / hanging on / connected to",
        "evidence": "primary binary 25/182 after 320-row packet; strict/diagnostic clear slices 0",
        "blocker": "endpoint-balanced sampling still produced reject-heavy reliability labels",
        "lesson": "endpoint balance alone does not create reliability-positive mass",
    },
    {
        "stage": "v22_hanging_on_strict",
        "relation_scope": "hanging on",
        "evidence": "primary binary 9/193; full quick-probe risk 107; slice blocking risk 1666",
        "blocker": "strict proxy balance did not translate to human/audit reliability balance",
        "lesson": "proxy-balanced construction can fail once visual/mesh reliability is checked",
    },
    {
        "stage": "v23_positive_anchor",
        "relation_scope": "hanging on positive-anchor cell",
        "evidence": "positive proxy 455 and hard-negative proxy 377 exist, but selected mixed cells 5 vs required 30",
        "blocker": "matched-cell diversity blocker, not raw row-count blocker",
        "lesson": "even accept-rich affordance cells can be too concentrated for a main posterior target",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blocker-dir", type=Path, default=DEFAULT_BLOCKER_DIR)
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


def validate_blocker(blocker_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if blocker_summary.get("status") != EXPECTED_BLOCKER_STATUS:
        errors.append({"error_type": "unexpected_blocker_status", "expected": EXPECTED_BLOCKER_STATUS, "actual": blocker_summary.get("status")})
    if blocker_summary.get("next_todo") != EXPECTED_BLOCKER_NEXT:
        errors.append({"error_type": "unexpected_blocker_next", "expected": EXPECTED_BLOCKER_NEXT, "actual": blocker_summary.get("next_todo")})
    if blocker_summary.get("validation_errors") != 0:
        errors.append({"error_type": "blocker_validation_errors_present", "actual": blocker_summary.get("validation_errors")})
    root_cause = blocker_summary.get("blocker_synthesis", {}).get("root_cause")
    if root_cause != "matched_cell_diversity_blocker_not_row_count_blocker":
        errors.append({"error_type": "unexpected_root_cause", "expected": "matched_cell_diversity_blocker_not_row_count_blocker", "actual": root_cause})
    facts = blocker_summary.get("blocker_synthesis", {}).get("capacity_facts", {})
    if int(facts.get("selected_spec_mixed_groups", -1)) >= 30:
        errors.append({"error_type": "mixed_cell_gate_unexpectedly_passed", "actual": facts.get("selected_spec_mixed_groups")})
    if int(facts.get("positive_anchor_proxy_rows", 0)) < 300:
        errors.append({"error_type": "positive_anchor_row_gate_unexpectedly_failed", "actual": facts.get("positive_anchor_proxy_rows")})

    boundary = blocker_summary.get("boundary", {})
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
            errors.append({"error_type": "blocker_boundary_violation", "key": key, "actual": boundary.get(key)})
    return errors


def build_option_matrix(blocker_summary: dict[str, Any]) -> list[dict[str, Any]]:
    facts = blocker_summary["blocker_synthesis"]["capacity_facts"]
    return [
        {
            "option": "run_candidate_mining_from_v23_preview",
            "verdict": "reject",
            "reason": (
                f"The capped preview can reach {facts['preview_rows_after_caps']} rows, but the selected control spec has only "
                f"{facts['selected_spec_mixed_groups']} mixed cells. Mining labels now would create a stratum-memory target."
            ),
        },
        {
            "option": "relax_to_subject_object_or_visible_endpoint_pair",
            "verdict": "reject_for_main_target",
            "reason": "These axes increase apparent capacity but are the same shortcut axes repeatedly identified in v7-v22 audits.",
        },
        {
            "option": "expand_affordance_taxonomy_and_rescan",
            "verdict": "low_priority",
            "reason": (
                "The current blocker is not absence of hanging-like rows. The blocker is lack of controlled mixed-cell diversity. "
                "A wider taxonomy may add rows but is unlikely to solve independence without a new labeling/source design."
            ),
        },
        {
            "option": "add_multi_view_or_mesh_as_model_input_now",
            "verdict": "reject",
            "reason": "Visual/mesh evidence is useful for audit labels, but adding it as model input before target independence would amplify a construction shortcut.",
        },
        {
            "option": "try_a_stronger_factorized_combiner_now",
            "verdict": "reject",
            "reason": "The failure is upstream of the combiner. A stronger model would fit target-construction artifacts, not relation reliability.",
        },
        {
            "option": "freeze_v23_positive_anchor_as_diagnostic_evidence",
            "verdict": "select",
            "reason": "It preserves the useful negative result without weakening controls or overstating posterior evidence.",
        },
        {
            "option": "reframe_next_h002_step_as_rga_benchmark_reframing",
            "verdict": "select_next",
            "reason": "The accumulated evidence supports RGA as a diagnostic/benchmark framework before a factorized posterior method claim.",
        },
        {
            "option": "conclude_h002_direction_is_wrong",
            "verdict": "reject",
            "reason": "The repeated failures are target-identifiability failures. They do not falsify semantic score != geometry validity != relation reliability.",
        },
    ]


def build_direction_review(blocker_summary: dict[str, Any]) -> dict[str, Any]:
    facts = blocker_summary["blocker_synthesis"]["capacity_facts"]
    return {
        "verdict": {
            "conceptual_direction": "valid_and_worth_preserving",
            "current_operational_route": "not_ready_for_posterior_method_claim",
            "aaai_level_main_claim_readiness": "not_ready_as_replacement_for_h001_without_new_independent_target",
        },
        "what_is_working": [
            "The problem formulation remains principled: semantic score, geometry validity, and relation reliability are empirically separable questions.",
            "RGA has repeatedly exposed whether a candidate target is shortcut-safe before posterior smoke is run.",
            "The train-only discipline is working: validation/test evidence has not been used to tune the hypothesis route.",
            "Relation-family diagnostics are informative: proximity, support/contact, relative vertical, and attachment fail for different reasons.",
        ],
        "what_is_not_working": [
            "Current Open3DSG train-side candidate mining does not produce enough balanced, independent human/audit reliability labels.",
            "Proxy balance does not translate into reliability-label balance after visual/mesh audit.",
            "Controlled strata often become too small, while relaxed strata reintroduce object, endpoint, rank, or geometry-status shortcuts.",
            "Attachment-deferred relations need visual/mesh evidence for labeling, but that evidence cannot safely become a model input before target independence is solved.",
        ],
        "root_causes": [
            "Target identifiability is the central blocker: the target must require combining semantic and geometry factors, but current labels are often explained by one construction axis.",
            "Candidate-source bias: Open3DSG train-side candidates are not a balanced experimental design; relation source rank, predicate, object pair, and geometry status are entangled.",
            "Positive reliability labels are sparse for attachment/support candidates under strict audit.",
            "Incomplete GT means existing dataset labels cannot directly replace human/audit reliability labels.",
            "OBB/point-cloud geometric witnesses are sufficient for some support/vertical checks but weak for functional attachment such as hanging/connected relations.",
        ],
        "improvement_directions": [
            {
                "direction": "RGA benchmark first, posterior later",
                "priority": "highest",
                "rationale": "Before claiming a factorized posterior, define relation-family-specific RGA states, shortcut audits, and failure taxonomy as the benchmark contribution.",
            },
            {
                "direction": "controlled synthetic/counterfactual benchmark",
                "priority": "high",
                "rationale": "Generate balanced accept/reject cases by perturbing geometry, endpoint pairing, object pose, and predicate labels under known controls.",
            },
            {
                "direction": "independent human annotation protocol",
                "priority": "high",
                "rationale": "Sample strata first, then annotate accept/reject/abstain with hidden construction fields and multiple annotators so target independence is designed in.",
            },
            {
                "direction": "multi-view/mesh as audit confirmation",
                "priority": "medium",
                "rationale": "Use visual/mesh evidence to improve labels for attachment, but keep it separate from model input until a target passes independence gates.",
            },
            {
                "direction": "family-specific diagnostic tables",
                "priority": "medium",
                "rationale": "Report that proximity, support/contact, vertical, and attachment expose different mismatch/shortcut patterns rather than forcing one posterior target now.",
            },
            {
                "direction": "second-source relation candidates",
                "priority": "medium",
                "rationale": "A second independent relation source may reduce Open3DSG-specific candidate/rank bias and expose disagreements that are not source-construction artifacts.",
            },
            {
                "direction": "stronger combiner after target gate",
                "priority": "deferred",
                "rationale": "Product-of-experts, monotonic additive, residual, or mixture-of-experts combiners are useful only after a target requires factorized evidence.",
            },
        ],
        "current_v23_specific_evidence": facts,
        "historical_blockers": HISTORICAL_BLOCKERS,
    }


def build_path_decision(blocker_summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "selected_path": SELECTED_PATH,
        "selected_next_todo": NEXT_TODO,
        "selected_actions": [
            "Freeze v23 `hanging on` positive-anchor route as diagnostic negative target-construction evidence.",
            "Do not mine labels from the v23 preview.",
            "Do not relax to subject/object or visible endpoint-pair groups as a main posterior target.",
            "Do not add multi-view/mesh as deployable model input at this gate.",
            "Move next H002 work to RGA benchmark reframing and target-identifiability design.",
        ],
        "rejected_actions": [
            "posterior_smoke_now",
            "candidate_mining_from_v23_preview",
            "subject_object_or_visible_pair_relaxation_as_main_target",
            "stronger_combiner_before_target_independence",
            "multi_view_as_model_input_before_target_independence",
            "declaring_h002_invalid_from_v23_failure",
        ],
        "claim_boundary": {
            "h002_conceptual_claim_preserved": True,
            "factorized_posterior_claim_allowed": False,
            "attachment_deferred_main_target_ready": False,
            "paper_metric_evidence": False,
            "diagnostic_evidence_allowed": True,
        },
    }


def build_report(summary: dict[str, Any]) -> str:
    review = summary["direction_review"]
    decision = summary["path_decision"]
    v23 = review["current_v23_specific_evidence"]
    lines = [
        "# V80 Hanging-On Positive-Anchor Path Decision",
        "",
        "## Purpose",
        "",
        "Decide the path after the v23 positive-anchor blocker and review whether the current H002 direction is still scientifically sound.",
        "",
        "## Decision",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {decision['selected_path']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "posterior_smoke_allowed = false",
        "```",
        "",
        "## V23 Evidence",
        "",
        "```text",
        f"positive_anchor_proxy_rows = {v23['positive_anchor_proxy_rows']}",
        f"hard_negative_proxy_rows = {v23['hard_negative_proxy_rows']}",
        f"selected_spec_mixed_groups = {v23['selected_spec_mixed_groups']}",
        f"selected_spec_balanced_proxy_row_capacity = {v23['selected_spec_balanced_proxy_row_capacity']}",
        f"strict_geometry_balanced_proxy_row_capacity = {v23['strict_geometry_balanced_proxy_row_capacity']}",
        f"failed_checks = {', '.join(v23['failed_checks'])}",
        "```",
        "",
        "## Direction Review",
        "",
        f"Conceptual direction: `{review['verdict']['conceptual_direction']}`.",
        f"Current operational route: `{review['verdict']['current_operational_route']}`.",
        f"AAAI-level main-claim readiness: `{review['verdict']['aaai_level_main_claim_readiness']}`.",
        "",
        "The current direction is still right at the problem-definition level. The repeated failures are not evidence that semantic score, geometry validity, and relation reliability are the same quantity. They are evidence that the current Open3DSG train-side target construction cannot yet provide an independent posterior target.",
        "",
        "## What Is Going Wrong",
        "",
    ]
    lines.extend(f"- {item}" for item in review["what_is_not_working"])
    lines.extend(
        [
            "",
            "## Root Causes",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in review["root_causes"])
    lines.extend(
        [
            "",
            "## Improvement Directions",
            "",
        ]
    )
    for item in review["improvement_directions"]:
        lines.append(f"- `{item['direction']}` ({item['priority']}): {item['rationale']}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only H002 hypothesis artifact.",
            "- No validation/test rows were used.",
            "- No H001 artifact was modified.",
            "- No new label was created.",
            "- No posterior was trained or evaluated.",
            "- Multi-view and mesh remain audit/confirmation evidence only.",
        ]
    )
    return "\n".join(lines) + "\n"


def build_direction_review_md(review: dict[str, Any]) -> str:
    lines = [
        "# H002 Direction Review After V23",
        "",
        "## Short Verdict",
        "",
        "- Conceptual direction: valid and worth preserving.",
        "- Current operational route: not ready for a posterior method claim.",
        "- Main reason: target identifiability, not factor-combination weakness.",
        "",
        "## What This Means",
        "",
        "H002 should not be abandoned as a research question. The distinction `semantic score != geometry validity != relation reliability` remains principled. However, the current route of repeatedly mining Open3DSG train-side candidates and then trying to obtain a balanced reliability target is no longer the best next move.",
        "",
        "The evidence says the bottleneck is upstream: the label target is either positive-sparse, shortcut-explainable, or concentrated in too few controlled cells. A stronger posterior or SOTA combiner would not solve this; it would mostly learn the construction artifact.",
        "",
        "## Why It Is Not Working",
        "",
    ]
    lines.extend(f"- {item}" for item in review["what_is_not_working"])
    lines.extend(["", "## Historical Evidence", ""])
    for item in review["historical_blockers"]:
        lines.append(
            f"- `{item['stage']}` / {item['relation_scope']}: {item['evidence']}. "
            f"Blocker: {item['blocker']}. Lesson: {item['lesson']}."
        )
    lines.extend(["", "## Better Direction", ""])
    for item in review["improvement_directions"]:
        lines.append(f"- `{item['direction']}` ({item['priority']}): {item['rationale']}")
    lines.extend(
        [
            "",
            "## Practical Recommendation",
            "",
            "Freeze v23 as diagnostic negative evidence and reframe the next H002 step around an RGA benchmark/target-identifiability plan. Posterior smoke should remain blocked until a target is designed to require factorized evidence rather than object, endpoint, rank, or geometry-status shortcuts.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    blocker_dir = as_abs(args.blocker_dir)
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    blocker_summary = read_json(blocker_dir / "summary.json")
    validation_errors = validate_blocker(blocker_summary)
    direction_review = build_direction_review(blocker_summary)
    path_decision = build_path_decision(blocker_summary)
    option_matrix = build_option_matrix(blocker_summary)

    status = STATUS_ERROR if validation_errors else STATUS
    next_todo = EXPECTED_BLOCKER_NEXT if validation_errors else NEXT_TODO
    summary = {
        "schema_version": "h002_reliability_target_v23_hanging_on_positive_anchor_path_decision_after_blocker_synthesis_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "next_todo": next_todo,
        "validation_errors": len(validation_errors),
        "split": "train_only",
        "path_decision": path_decision,
        "option_matrix": option_matrix,
        "direction_review": direction_review,
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
            "blocker_summary": rel_path(blocker_dir / "summary.json"),
            "blocker_report": rel_path(blocker_dir / "report.md"),
        },
        "outputs": {
            "summary": rel_path(output_dir / "summary.json"),
            "path_decision": rel_path(output_dir / "path_decision.json"),
            "direction_review": rel_path(output_dir / "direction_review.json"),
            "direction_review_md": rel_path(output_dir / "direction_review.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
            "report": rel_path(output_dir / "report.md"),
        },
    }
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "path_decision.json", path_decision)
    write_json(output_dir / "direction_review.json", direction_review)
    (output_dir / "direction_review.md").write_text(build_direction_review_md(direction_review), encoding="utf-8")
    write_jsonl(output_dir / "validation_errors.jsonl", validation_errors)
    (output_dir / "report.md").write_text(build_report(summary), encoding="utf-8")

    print(f"status={status}")
    print(f"next_todo={next_todo}")
    print(f"validation_errors={len(validation_errors)}")
    print(f"selected_path={path_decision['selected_path']}")
    print(f"conceptual_direction={direction_review['verdict']['conceptual_direction']}")
    print(f"current_operational_route={direction_review['verdict']['current_operational_route']}")
    return 0 if not validation_errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
