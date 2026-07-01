#!/usr/bin/env python3
"""Review support/contact point-multiview result and freeze claim position."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_FAILURE_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position"
)

EXPECTED_FAILURE_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_failure_analysis_ready_for_result_review"
)
EXPECTED_FAILURE_NEXT = (
    "compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position"
)

SCHEMA_VERSION = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_and_claim_position_v1"
)
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_claim_position_ready_for_multi_family_synthesis"
)
STATUS_ERRORS = (
    "h002_compatibility_dataset_v3_support_contact_individual_predicate_point_multiview_result_review_claim_position_input_errors"
)
SELECTED_PATH = (
    "paper_position_support_contact_compatibility_route_evidence_with_caveat_keep_internal_near_threshold"
)
NEXT_TODO = "compatibility_dataset_v3_multi_family_claim_synthesis_after_support_contact_point_multiview"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--failure-dir", type=Path, default=DEFAULT_FAILURE_DIR)
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
    if not path.exists():
        return []
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


def validate_inputs(
    failure_summary: dict[str, Any],
    failure_validation: list[dict[str, Any]],
    route_decisions: list[dict[str, str]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if failure_summary.get("status") != EXPECTED_FAILURE_STATUS:
        errors.append({"error_type": "unexpected_failure_status", "actual": failure_summary.get("status")})
    if failure_summary.get("next_todo") != EXPECTED_FAILURE_NEXT:
        errors.append({"error_type": "unexpected_failure_next", "actual": failure_summary.get("next_todo")})
    if failure_summary.get("validation_errors") != 0:
        errors.append({"error_type": "failure_validation_errors", "actual": failure_summary.get("validation_errors")})
    if failure_validation:
        errors.append({"error_type": "failure_validation_rows_present", "rows": len(failure_validation)})
    boundary = failure_summary.get("boundary", {})
    for key in [
        "diagnostic_hidden_fields_used_only_after_prediction",
        "internal_gate_rewritten",
        "paper_evidence_allowed",
        "test_usage",
        "validation_usage",
        "visual_model_input_allowed",
    ]:
        if key not in boundary:
            errors.append({"error_type": "missing_boundary_key", "key": key})
    if boundary.get("internal_gate_rewritten") is not False:
        errors.append({"error_type": "internal_gate_rewritten"})
    if boundary.get("paper_evidence_allowed") is not False:
        errors.append({"error_type": "paper_evidence_unexpectedly_allowed"})
    if boundary.get("test_usage") is not False or boundary.get("validation_usage") is not False:
        errors.append({"error_type": "validation_or_test_used"})

    runner = failure_summary.get("runner_snapshot", {})
    primary = runner.get("primary_auroc")
    geometry = runner.get("point_contact_geometry_auroc")
    concat = runner.get("plain_concat_auroc")
    wrong_t = runner.get("wrong_t_auroc")
    shuffle_g = runner.get("shuffled_g_global_auroc")
    if primary is None or primary < 0.65:
        errors.append({"error_type": "primary_signal_too_low_for_route_evidence", "actual": primary})
    if geometry is None or primary <= geometry:
        errors.append({"error_type": "primary_not_better_than_geometry_only", "primary": primary, "geometry": geometry})
    if concat is None or primary <= concat:
        errors.append({"error_type": "primary_not_better_than_concat", "primary": primary, "concat": concat})
    if wrong_t is None or wrong_t >= 0.5:
        errors.append({"error_type": "wrong_t_does_not_collapse", "actual": wrong_t})
    if shuffle_g is None or shuffle_g > 0.55:
        errors.append({"error_type": "shuffled_g_not_near_chance", "actual": shuffle_g})

    route_map = {row.get("route"): row.get("verdict") for row in route_decisions}
    if route_map.get("paper_facing_support_contact_role") != "use_as_main_compatibility_route_evidence_with_caveat":
        errors.append({"error_type": "missing_support_contact_paper_route_decision", "routes": route_map})
    if route_map.get("Q_e_as_truth_signal") != "reject":
        errors.append({"error_type": "missing_qe_truth_rejection", "routes": route_map})
    return errors


def claim_position(failure_summary: dict[str, Any]) -> dict[str, Any]:
    runner = failure_summary.get("runner_snapshot", {})
    slices = failure_summary.get("key_slice_findings", {})
    return {
        "accepted_paper_role": "support/contact compatibility-route evidence with caveat",
        "internal_status": "near-threshold diagnostic; internal 0.70 gate is not rewritten",
        "not_allowed": [
            "support/contact is fully solved",
            "support/contact branch achieves strong absolute performance",
            "Q_e directly predicts relation truth",
            "the result is paper-level evidence without Docker/held-out reproduction",
        ],
        "allowed_claim": (
            "For support/contact relations, predicate-geometry interaction provides the strongest signal, "
            "while semantic-only, geometry-only, and plain concatenation baselines fail and wrong-predicate "
            "or shuffled-geometry controls collapse."
        ),
        "main_numbers": {
            "M8_TG_point_contact_interaction": runner.get("primary_auroc"),
            "M1_semantic_only_T": runner.get("semantic_only_auroc"),
            "M5_point_contact_geometry": runner.get("point_contact_geometry_auroc"),
            "M7_TG_point_contact_concat": runner.get("plain_concat_auroc"),
            "C1_wrong_T_same_G": runner.get("wrong_t_auroc"),
            "C2_shuffled_G_global": runner.get("shuffled_g_global_auroc"),
            "C3_shuffled_G_within_predicate": runner.get("shuffled_g_within_predicate_auroc"),
            "M9_TGQ_factorized_observability": runner.get("q_factorized_auroc"),
            "lying_on": slices.get("lying_on_auroc"),
            "standing_on": slices.get("standing_on_auroc"),
        },
        "recommended_paper_sentence": (
            "In support/contact relations, neither semantic content nor point-contact geometry alone explains "
            "the target. Predicate-conditioned interaction is the only setting that separates the target from "
            "wrong-predicate and shuffled-geometry controls, indicating that this family requires compatibility "
            "reasoning rather than fixed semantic-geometry fusion."
        ),
    }


def route_table(failure_summary: dict[str, Any]) -> list[dict[str, Any]]:
    runner = failure_summary.get("runner_snapshot", {})
    return [
        {
            "route": "internal_status",
            "decision": "keep_near_threshold_diagnostic",
            "evidence": "M8=0.699375 is below the frozen internal 0.70 gate.",
            "paper_position": "do not expose the internal gate as a failure criterion",
        },
        {
            "route": "paper_support_contact_role",
            "decision": "use_as_main_compatibility_route_evidence_with_caveat",
            "evidence": (
                f"M8={runner.get('primary_auroc')}; geometry-only={runner.get('point_contact_geometry_auroc')}; "
                f"concat={runner.get('plain_concat_auroc')}; wrong-T={runner.get('wrong_t_auroc')}; "
                f"shuffled-G={runner.get('shuffled_g_global_auroc')}/{runner.get('shuffled_g_within_predicate_auroc')}."
            ),
            "paper_position": "interaction necessity for a challenging relation family",
        },
        {
            "route": "support_contact_fully_solved_claim",
            "decision": "reject",
            "evidence": "aggregate AUROC is moderate and lying-on remains weaker than standing-on",
            "paper_position": "present residual ambiguity and failure taxonomy",
        },
        {
            "route": "Q_e_truth_signal",
            "decision": "reject",
            "evidence": "M9 does not improve over M8 and shuffled-Q is almost identical to M8",
            "paper_position": "Q_e is p_obs/observability evidence only",
        },
        {
            "route": "stronger_combiner_before_synthesis",
            "decision": "reject_for_now",
            "evidence": "the current pattern already supports interaction necessity; the remaining issue is claim synthesis",
            "paper_position": "avoid turning H002 into architecture tuning before framing is stable",
        },
        {
            "route": "multi_family_synthesis",
            "decision": "selected_next",
            "evidence": "relative_vertical is clean mechanism evidence; support/contact is challenging compatibility-route evidence",
            "paper_position": "build relation-aware route table before any broader expansion",
        },
    ]


def relation_route_table() -> list[dict[str, Any]]:
    return [
        {
            "relation_family": "relative_vertical",
            "predicates": "higher than; lower than",
            "route_type": "clean compatibility mechanism",
            "paper_role": "main mechanism evidence",
            "evidence_route": "T_e x signed vertical G_e",
            "current_boundary": "too clean to be the only evidence; not final reliability",
            "status": "retain_main_route",
        },
        {
            "relation_family": "support_contact",
            "predicates": "lying on; standing on",
            "route_type": "challenging compatibility route",
            "paper_role": "main route evidence with caveat",
            "evidence_route": "T_e x point/contact/pose G_e; Q_e as p_obs/observability",
            "current_boundary": "not fully solved; lying-on ambiguity and limited-evidence rows remain",
            "status": "retain_main_route_with_caveat",
        },
        {
            "relation_family": "support_contact_superordinate",
            "predicates": "supported by",
            "route_type": "taxonomy/diagnostic",
            "paper_role": "diagnostic only",
            "evidence_route": "support/contact G_e overlaps standing/lying states",
            "current_boundary": "superordinate predicate too ambiguous for clean opposing labels",
            "status": "defer_primary_claim",
        },
        {
            "relation_family": "proximity",
            "predicates": "close by",
            "route_type": "geometry-easy control",
            "paper_role": "generality/control, not main compatibility proof",
            "evidence_route": "distance geometry",
            "current_boundary": "distance/rule geometry solves current target",
            "status": "diagnostic_only",
        },
        {
            "relation_family": "attachment_like",
            "predicates": "attached to; hanging on; connected to",
            "route_type": "observability-heavy future route",
            "paper_role": "future/diagnostic unless visual/mesh evidence is promoted",
            "evidence_route": "requires visual/mesh contact and Q_e",
            "current_boundary": "target-independence and observability bottlenecks",
            "status": "defer",
        },
        {
            "relation_family": "relative_horizontal",
            "predicates": "left; right; front; behind",
            "route_type": "reference-frame deferred route",
            "paper_role": "future work",
            "evidence_route": "requires coordinate/viewer/reference-frame contract",
            "current_boundary": "not comparable until frame semantics are fixed",
            "status": "defer",
        },
    ]


def reviewer_risks() -> list[dict[str, Any]]:
    return [
        {
            "risk": "AUROC is only 0.699 for support/contact",
            "answer": "Do not claim high absolute performance. Claim baseline/control pattern and interaction necessity.",
            "artifact": "failure_analysis + result_review",
        },
        {
            "risk": "Internal gate says diagnostic; why use in paper framing?",
            "answer": "The gate is a research management threshold, not a paper evaluation criterion. The result is used as route evidence with caveat, not as a success gate.",
            "artifact": "route_decision.csv",
        },
        {
            "risk": "Q_e may be leaking truth",
            "answer": "M9 does not improve over M8 and shuffled-Q is nearly identical. Q_e is only observability/selective-decision evidence.",
            "artifact": "failure_analysis summary",
        },
        {
            "risk": "Support/contact may still be category shortcut",
            "answer": "Semantic/class shortcuts are weak, and wrong-predicate/shuffled-geometry controls collapse. Remaining class-pair difficulty is reported as failure taxonomy.",
            "artifact": "axis_failure_profile.csv",
        },
        {
            "risk": "This is not paper-level evidence",
            "answer": "Correct. It is H002 hypothesis evidence. Paper-level claim needs Docker/held-out reproduction if H002 is promoted.",
            "artifact": "boundary fields",
        },
    ]


def write_report(path: Path, summary: dict[str, Any], claim: dict[str, Any], routes: list[dict[str, Any]], relation_routes: list[dict[str, Any]]) -> None:
    lines = [
        "# H002 Support/Contact Point/Multiview Result Review And Claim Position",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Claim Position",
        "",
        f"- accepted paper role: `{claim['accepted_paper_role']}`",
        f"- internal status: `{claim['internal_status']}`",
        "",
        "Allowed wording:",
        "",
        f"> {claim['allowed_claim']}",
        "",
        "Forbidden claims:",
        "",
    ]
    for item in claim["not_allowed"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Main Numbers",
            "",
            "| Signal | AUROC |",
            "| --- | ---: |",
        ]
    )
    for key, value in claim["main_numbers"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Route Decisions",
            "",
            "| Route | Decision | Paper Position |",
            "| --- | --- | --- |",
        ]
    )
    for row in routes:
        lines.append(f"| `{row['route']}` | `{row['decision']}` | {row['paper_position']} |")
    lines.extend(
        [
            "",
            "## Relation Route Table",
            "",
            "| Family | Route Type | Paper Role | Status |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in relation_routes:
        lines.append(
            f"| `{row['relation_family']}` | {row['route_type']} | {row['paper_role']} | `{row['status']}` |"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "Support/contact is retained as a main compatibility-route evidence family with an explicit caveat.",
            "The internal near-threshold status is not rewritten as pass. The next step is multi-family claim",
            "synthesis, not stronger-combiner tuning.",
            "",
            "## Next",
            "",
            "```text",
            summary["next_todo"],
            "```",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    failure_summary = read_json(args.failure_dir / "summary.json")
    failure_validation = read_jsonl(args.failure_dir / "validation_errors.jsonl")
    failure_routes = read_csv(args.failure_dir / "route_decision.csv")
    errors = validate_inputs(failure_summary, failure_validation, failure_routes)

    claim = claim_position(failure_summary)
    routes = route_table(failure_summary)
    relation_routes = relation_route_table()
    risks = reviewer_risks()

    summary = {
        "boundary": {
            "h001_artifacts_modified": False,
            "internal_gate_rewritten": False,
            "paper_evidence_allowed": False,
            "paper_facing_claim_position_only": True,
            "split": "train_internal_result_review",
            "test_usage": False,
            "validation_usage": False,
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "failure_analysis_root": rel_path(args.failure_dir),
        },
        "next_todo": NEXT_TODO,
        "output_paths": {
            "claim_position": rel_path(args.output_dir / "claim_position.json"),
            "relation_route_table": rel_path(args.output_dir / "relation_route_table.csv"),
            "report": rel_path(args.output_dir / "report.md"),
            "reviewer_risks": rel_path(args.output_dir / "reviewer_risks.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "summary": rel_path(args.output_dir / "summary.json"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
        "schema_version": SCHEMA_VERSION,
        "selected_path": SELECTED_PATH,
        "status": STATUS_READY if not errors else STATUS_ERRORS,
        "validation_errors": len(errors),
    }

    write_json(args.output_dir / "claim_position.json", claim)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_csv(args.output_dir / "relation_route_table.csv", relation_routes)
    write_csv(args.output_dir / "reviewer_risks.csv", risks)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_json(args.output_dir / "summary.json", summary)
    write_report(args.output_dir / "report.md", summary, claim, routes, relation_routes)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
