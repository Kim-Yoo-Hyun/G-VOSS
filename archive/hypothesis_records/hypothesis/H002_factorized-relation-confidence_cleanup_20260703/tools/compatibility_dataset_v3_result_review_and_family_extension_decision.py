#!/usr/bin/env python3
"""Decide the next H002 path after the v3 compatibility smoke passed controls."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_sanitized_view_smoke_runner"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_result_review_and_family_extension_decision"

EXPECTED_RUNNER_STATUS = "h002_compatibility_dataset_v3_sanitized_view_smoke_runner_passed_controls"
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_result_review_and_family_extension_decision"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_result_review_and_family_extension_decision_v1"
STATUS_READY = "h002_compatibility_dataset_v3_result_review_accept_mechanism_select_support_contact_probe"
STATUS_ERRORS = "h002_compatibility_dataset_v3_result_review_input_errors"
SELECTED_PATH = "accept_relative_vertical_Ce_mechanism_proof_and_probe_support_contact_evidence"
NEXT_TODO = "compatibility_dataset_v3_support_contact_evidence_probe_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner-dir", type=Path, default=DEFAULT_RUNNER_DIR)
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
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def metric(summary: dict[str, Any], model: str, key: str = "auroc") -> float | None:
    value = summary.get("key_metrics", {}).get(model, {}).get(key)
    return None if value is None else float(value)


def validate_runner(summary: dict[str, Any], validation_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_next", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "runner_validation_errors", "actual": summary.get("validation_errors")})
    if validation_rows:
        errors.append({"error_type": "runner_validation_error_rows_present", "rows": len(validation_rows)})

    counts = summary.get("counts", {})
    if counts.get("rows") != 400 or counts.get("positive") != 200 or counts.get("negative") != 200:
        errors.append({"error_type": "unexpected_counts", "counts": counts})
    if counts.get("paired_groups_with_one_positive_one_negative") != 200:
        errors.append({"error_type": "unexpected_paired_groups", "counts": counts})

    gates = summary.get("gates", {})
    if gates.get("overall_pass") is not True:
        errors.append({"error_type": "runner_gates_not_passed", "gates": gates})
    required_gate_keys = [
        "gate_data_integrity",
        "gate_shortcut_baselines_near_chance",
        "gate_primary_compatibility_success",
        "gate_interaction_over_plain_concat",
        "gate_wrong_T_same_G_degradation",
        "gate_shuffled_G_degradation",
        "gate_paired_score_drop",
    ]
    for key in required_gate_keys:
        if gates.get(key, {}).get("pass") is not True:
            errors.append({"error_type": "required_gate_failed", "gate": key, "actual": gates.get(key)})

    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "raw_candidate_rows_used_as_model_input"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if summary.get("paper_evidence_allowed") is not False:
        errors.append({"error_type": "paper_evidence_unexpectedly_allowed"})

    m5b = metric(summary, "M5b_compatibility_TG_interaction")
    m4 = metric(summary, "M4_geometry_only_G")
    m5a = metric(summary, "M5a_compatibility_TG_concat")
    c1 = metric(summary, "C1_wrong_T_same_G_control")
    c2 = metric(summary, "C2_shuffled_G_global_control")
    c3 = metric(summary, "C3_shuffled_G_within_predicate_control")
    if m5b is None or m5b < 0.90:
        errors.append({"error_type": "primary_auc_below_requirement", "actual": m5b})
    if m4 is None or m4 > 0.60:
        errors.append({"error_type": "geometry_only_not_near_chance", "actual": m4})
    if m5a is None or m5a > 0.60:
        errors.append({"error_type": "plain_concat_not_near_chance", "actual": m5a})
    if c1 is None or c1 > 0.60:
        errors.append({"error_type": "wrong_t_not_degraded", "actual": c1})
    if c2 is None or c2 > 0.60 or c3 is None or c3 > 0.60:
        errors.append({"error_type": "shuffled_g_not_near_chance", "global": c2, "within_predicate": c3})
    return errors


def route_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    m5b = metric(summary, "M5b_compatibility_TG_interaction")
    m4 = metric(summary, "M4_geometry_only_G")
    m5a = metric(summary, "M5a_compatibility_TG_concat")
    c1 = metric(summary, "C1_wrong_T_same_G_control")
    c2 = metric(summary, "C2_shuffled_G_global_control")
    c3 = metric(summary, "C3_shuffled_G_within_predicate_control")
    return [
        {
            "route": "promote_relative_vertical_as_Ce_mechanism_proof",
            "verdict": "selected_as_scoped_mechanism",
            "evidence": f"M5b AUROC {m5b}, G-only {m4}, plain concat {m5a}, wrong-T {c1}, shuffled-G {c2}/{c3}.",
            "reason": "This is the first clean evidence that T_e changes how the same predicate-independent G_e should be interpreted.",
            "next_action": "keep_as_core_Ce_smoke_result",
        },
        {
            "route": "promote_to_broad_relation_reliability_now",
            "verdict": "reject",
            "evidence": "The passed target covers only relative_vertical higher/lower under signed vertical geometry.",
            "reason": "It proves a compatibility mechanism, not final p_rel/p_obs or broad 3DSSG reliability.",
            "next_action": "do_not_claim_broad_reliability",
        },
        {
            "route": "run_paper_level_docker_experiment_now",
            "verdict": "defer",
            "evidence": "The result is still train-only and hypothesis-stage.",
            "reason": "Paper promotion should wait until family scope and deployable evaluation target are clearer.",
            "next_action": "return_after_family_extension_decision",
        },
        {
            "route": "expand_to_support_contact_immediate_smoke",
            "verdict": "reject_as_immediate",
            "evidence": "Prior v2 support/contact signal was geometry-perturbation dominated.",
            "reason": "Without role/orientation/contact-direction or visual/mesh evidence, support/contact may repeat the v2 failure.",
            "next_action": "probe_support_contact_evidence_before_smoke",
        },
        {
            "route": "expand_to_support_contact_evidence_probe",
            "verdict": "selected_next",
            "evidence": "Support/contact is the best next family for method generality, but it needs evidence-axis validation first.",
            "reason": "It tests whether H002 extends beyond vertical order while still staying physically meaningful.",
            "next_action": NEXT_TODO,
        },
        {
            "route": "expand_to_attachment_like_now",
            "verdict": "defer",
            "evidence": "Attachment positive-anchor targets repeatedly failed independence audits under current evidence.",
            "reason": "Attachment needs mesh/multi-view/visibility evidence before becoming a primary C_e target.",
            "next_action": "keep_as_Qe_and_failure_taxonomy_artifact",
        },
        {
            "route": "expand_to_proximity_now",
            "verdict": "defer",
            "evidence": "close by is mostly single-predicate distance compatibility under current evidence.",
            "reason": "It is useful for generality later, but weak for proving predicate-conditioned compatibility.",
            "next_action": "use_after multi-family C_e is stable",
        },
    ]


def family_rows() -> list[dict[str, Any]]:
    return [
        {
            "family": "relative_vertical",
            "current_status": "passed_scoped_Ce_mechanism",
            "predicates": "higher than; lower than",
            "evidence_available_now": "signed vertical OBB geometry",
            "what_v3_proved": "same G_e becomes positive or negative depending on T_e",
            "risk": "too clean/easy if used as the only method evidence",
            "decision": "retain_as_core_mechanism_proof",
            "next_requirement": "report as scoped C_e proof, not broad reliability",
        },
        {
            "family": "support_contact",
            "current_status": "best_next_extension_candidate",
            "predicates": "standing on; lying on; supported by",
            "evidence_available_now": "distance, overlap, gap, vertical geometry; role/orientation unclear",
            "what_v3_proved": "not yet tested under the same-G predicate-conditioned contract",
            "risk": "geometry-only dominance if negative rows are gap/overlap perturbations",
            "decision": "probe_evidence_before_smoke",
            "next_requirement": "check role/orientation/contact-direction/surface-normal/mesh/visual evidence availability",
        },
        {
            "family": "attachment_like",
            "current_status": "diagnostic_hard_family",
            "predicates": "attached to; hanging on; connected to",
            "evidence_available_now": "review packets and limited OBB geometry; no deployable visual/mesh factor yet",
            "what_v3_proved": "not applicable yet",
            "risk": "target-independence failure and observability bottleneck",
            "decision": "defer_as_primary",
            "next_requirement": "use for Q_e/failure taxonomy until visual/mesh evidence axis is materialized",
        },
        {
            "family": "proximity",
            "current_status": "future_generality",
            "predicates": "close by",
            "evidence_available_now": "distance geometry",
            "what_v3_proved": "not applicable as a single-predicate compatibility contrast",
            "risk": "collapses to geometry verifier rather than predicate-geometry compatibility",
            "decision": "defer",
            "next_requirement": "pair with semantic alternatives or use only as generality ablation",
        },
        {
            "family": "relative_horizontal",
            "current_status": "deferred",
            "predicates": "left; right; front; behind",
            "evidence_available_now": "requires reference-frame/viewer-frame contract",
            "what_v3_proved": "not tested",
            "risk": "frame ambiguity",
            "decision": "defer",
            "next_requirement": "define coordinate/reference-frame semantics first",
        },
    ]


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Before running another learned smoke, determine whether support/contact has enough predicate-independent evidence to build a clean C_e target.",
        "selected_family": "support_contact",
        "candidate_predicates": ["standing on", "lying on", "supported by"],
        "probe_questions": [
            "Do current artifacts expose role/orientation/contact-direction evidence beyond generic gap/overlap?",
            "Can same-G or near-G groups be formed where T_e changes validity without changing generic G_e distribution?",
            "Can geometry-only remain near chance under the candidate target?",
            "Are source score, object pair, floor/wall/ceiling, and predicate shortcuts controllable?",
            "Is multi-view/mesh evidence required before support/contact can be a fair C_e target?",
        ],
        "do_not_do_next": [
            "Do not run support/contact learned smoke directly from v2 generated counterfactual rows.",
            "Do not treat gap/overlap perturbation negatives as the primary C_e target.",
            "Do not promote v3 relative_vertical as broad relation reliability.",
            "Do not use attachment-like labels as p_rel GT yet.",
        ],
        "success_condition_for_probe": [
            "candidate target design where G_e-only is expected near chance",
            "explicit fields for role/orientation/contact direction or declared need for visual/mesh",
            "pre-smoke shortcut controls for object labels and structural objects",
            "clear decision: support/contact v3 materialization vs defer to visual/mesh evidence",
        ],
    }


def build_decision(summary: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_compatibility_dataset_v3_result_review_inputs"
    selected_path = SELECTED_PATH if not errors else "fix_inputs_before_decision"
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": selected_path,
        "next_todo": next_todo,
        "validation_errors": len(errors),
        "runner_root": rel_path(DEFAULT_RUNNER_DIR),
        "runner_status": summary.get("status"),
        "mechanism_result": {
            "accepted": not errors,
            "family": "relative_vertical",
            "primary_model": "M5b_compatibility_TG_interaction",
            "primary_auroc": metric(summary, "M5b_compatibility_TG_interaction"),
            "geometry_only_auroc": metric(summary, "M4_geometry_only_G"),
            "plain_concat_auroc": metric(summary, "M5a_compatibility_TG_concat"),
            "wrong_t_auroc": metric(summary, "C1_wrong_T_same_G_control"),
            "shuffled_g_global_auroc": metric(summary, "C2_shuffled_G_global_control"),
            "shuffled_g_within_predicate_auroc": metric(summary, "C3_shuffled_G_within_predicate_control"),
            "paired_score_drop": summary.get("gates", {}).get("gate_paired_score_drop"),
        },
        "claim_decision": {
            "allowed_claim": "scoped predicate-geometry compatibility mechanism for relative_vertical",
            "blocked_claims": [
                "broad relation reliability",
                "final p_rel/p_obs decision quality",
                "all 3DSSG relation-family generality",
                "paper-level Docker-reproduced result",
            ],
            "why": "The target is clean and passed controls, but it covers only higher/lower signed vertical compatibility.",
        },
        "selected_next_family": "support_contact",
        "next_plan_contract": next_plan_contract(),
        "route_table": route_rows(summary),
        "family_table": family_rows(),
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "trains_new_model": False,
            "h001_artifacts_modified": False,
        },
    }


def build_report(decision: dict[str, Any]) -> str:
    mech = decision["mechanism_result"]
    lines = [
        "# Compatibility Dataset V3 Result Review And Family Extension Decision",
        "",
        "## Status",
        "",
        "```text",
        f"status = {decision['status']}",
        f"selected_path = {decision['selected_path']}",
        f"next_todo = {decision['next_todo']}",
        f"validation_errors = {decision['validation_errors']}",
        "```",
        "",
        "## Result Review",
        "",
        "```text",
        f"family = {mech['family']}",
        f"primary_model = {mech['primary_model']}",
        f"primary_auroc = {mech['primary_auroc']}",
        f"geometry_only_auroc = {mech['geometry_only_auroc']}",
        f"plain_concat_auroc = {mech['plain_concat_auroc']}",
        f"wrong_t_auroc = {mech['wrong_t_auroc']}",
        f"shuffled_g_global_auroc = {mech['shuffled_g_global_auroc']}",
        f"shuffled_g_within_predicate_auroc = {mech['shuffled_g_within_predicate_auroc']}",
        f"paired_score_drop = {mech['paired_score_drop']}",
        "```",
        "",
        "The v3 smoke is accepted as a scoped `C_e` mechanism proof. It shows that the same",
        "predicate-independent `G_e` can become positive or negative depending on relation semantic",
        "content `T_e`, while source-only, semantic-only, geometry-only, and plain concatenation remain",
        "near chance.",
        "",
        "## Claim Boundary",
        "",
        f"Allowed claim: `{decision['claim_decision']['allowed_claim']}`",
        "",
        "Blocked claims:",
        "",
    ]
    for claim in decision["claim_decision"]["blocked_claims"]:
        lines.append(f"- `{claim}`")
    lines.extend(
        [
            "",
            "## Route Decision",
            "",
            "| Route | Verdict | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for row in decision["route_table"]:
        lines.append(f"| `{row['route']}` | `{row['verdict']}` | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Family Decision",
            "",
            "| Family | Current Status | Decision | Next Requirement |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in decision["family_table"]:
        lines.append(
            f"| `{row['family']}` | `{row['current_status']}` | `{row['decision']}` | {row['next_requirement']} |"
        )
    lines.extend(
        [
            "",
            "## Next Plan Contract",
            "",
            "The next step should not directly run another learned smoke. It should first probe whether",
            "`support_contact` exposes enough evidence to build a clean predicate-conditioned target.",
            "",
            "Required probe questions:",
            "",
        ]
    )
    for question in decision["next_plan_contract"]["probe_questions"]:
        lines.append(f"- {question}")
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "- Train-only H002 decision artifact.",
            "- No validation/test usage.",
            "- No new model trained in this step.",
            "- No paper-level evidence promotion.",
            "- No H001 artifact modification.",
            "",
            "## Next",
            "",
            "```text",
            decision["next_todo"],
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    runner_summary = read_json(args.runner_dir / "summary.json")
    validation_rows = read_jsonl(args.runner_dir / "validation_errors.jsonl")
    errors = validate_runner(runner_summary, validation_rows)
    decision = build_decision(runner_summary, errors)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", decision)
    write_json(output_dir / "path_decision.json", {
        "selected_path": decision["selected_path"],
        "next_todo": decision["next_todo"],
        "allowed_claim": decision["claim_decision"]["allowed_claim"],
        "blocked_claims": decision["claim_decision"]["blocked_claims"],
        "selected_next_family": decision["selected_next_family"],
        "next_plan_contract": decision["next_plan_contract"],
    })
    write_csv(output_dir / "route_table.csv", decision["route_table"])
    write_csv(output_dir / "family_table.csv", decision["family_table"])
    write_json(output_dir / "next_plan_contract.json", decision["next_plan_contract"])
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(build_report(decision), encoding="utf-8")

    print(f"status={decision['status']}")
    print(f"selected_path={decision['selected_path']}")
    print(f"next={decision['next_todo']}")
    print(f"validation_errors={decision['validation_errors']}")


if __name__ == "__main__":
    main()
