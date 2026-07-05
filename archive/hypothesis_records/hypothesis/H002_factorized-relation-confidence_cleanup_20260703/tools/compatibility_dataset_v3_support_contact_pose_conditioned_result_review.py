#!/usr/bin/env python3
"""Review the passed support/contact pose-conditioned smoke result."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_RUNNER_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_result_review"
)

EXPECTED_RUNNER_STATUS = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner_passed_controls"
)
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_support_contact_pose_conditioned_result_review"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_result_review_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_support_contact_pose_conditioned_result_review_accept_scoped_Ce_select_multi_family_synthesis"
)
STATUS_ERRORS = "h002_compatibility_dataset_v3_support_contact_pose_conditioned_result_review_input_errors"
SELECTED_PATH = "accept_support_contact_Ce_mechanism_proof_select_multi_family_result_synthesis"
NEXT_TODO = "compatibility_dataset_v3_multi_family_result_synthesis_plan"

PRIMARY_MODEL = "M5b_compatibility_TG_pose_interaction"


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
                fields.append(key)
                seen.add(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
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
    if counts.get("predicate_counts") != {"lying on": 200, "standing on": 200}:
        errors.append({"error_type": "unexpected_predicate_counts", "counts": counts})

    gates = summary.get("gates", {})
    if gates.get("overall_pass") is not True:
        errors.append({"error_type": "runner_gates_not_passed", "gates": gates})
    for key in [
        "gate_data_integrity",
        "gate_shortcut_baselines_near_chance",
        "gate_primary_compatibility_success",
        "gate_interaction_over_plain_concat",
        "gate_wrong_T_same_G_degradation",
        "gate_shuffled_G_degradation",
        "gate_paired_score_margin",
    ]:
        if gates.get(key, {}).get("pass") is not True:
            errors.append({"error_type": "required_gate_failed", "gate": key, "actual": gates.get(key)})

    boundary = summary.get("boundary", {})
    for key in ["validation_usage", "test_usage", "h001_artifacts_modified", "raw_candidate_rows_used_as_model_input"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if summary.get("paper_evidence_allowed") is not False:
        errors.append({"error_type": "paper_evidence_unexpectedly_allowed"})

    m5b = metric(summary, PRIMARY_MODEL)
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


def mechanism_summary(summary: dict[str, Any]) -> dict[str, Any]:
    gates = summary.get("gates", {})
    return {
        "accepted": True,
        "family": "support_contact_pose_conditioned",
        "primary_model": PRIMARY_MODEL,
        "primary_auroc": metric(summary, PRIMARY_MODEL),
        "source_only_auroc": metric(summary, "M1_source_only_Z_safe"),
        "semantic_only_auroc": metric(summary, "M2_semantic_only_T"),
        "geometry_only_auroc": metric(summary, "M4_geometry_only_G"),
        "plain_concat_auroc": metric(summary, "M5a_compatibility_TG_concat"),
        "factorized_ablation_auroc": metric(summary, "M6_factorized_sanitized_TZGQ_pose_interaction"),
        "wrong_t_auroc": metric(summary, "C1_wrong_T_same_G_control"),
        "shuffled_g_global_auroc": metric(summary, "C2_shuffled_G_global_control"),
        "shuffled_g_within_predicate_auroc": metric(summary, "C3_shuffled_G_within_predicate_control"),
        "paired_score_margin": gates.get("gate_paired_score_margin"),
        "counts": summary.get("counts", {}),
    }


def route_rows(summary: dict[str, Any]) -> list[dict[str, Any]]:
    mech = mechanism_summary(summary)
    return [
        {
            "route": "accept_support_contact_as_scoped_Ce_mechanism_proof",
            "verdict": "selected",
            "evidence": f"M5b AUROC {mech['primary_auroc']}, G-only {mech['geometry_only_auroc']}, concat {mech['plain_concat_auroc']}, wrong-T {mech['wrong_t_auroc']}, shuffled-G {mech['shuffled_g_global_auroc']}/{mech['shuffled_g_within_predicate_auroc']}.",
            "reason": "Same support/contact G_e becomes compatible or incompatible depending on lying/standing T_e, while single-factor shortcuts stay near chance.",
            "next_action": "retain_as_second_scoped_Ce_mechanism_result",
        },
        {
            "route": "treat_as_dataset_artifact_only",
            "verdict": "reject_but_keep_caveat",
            "evidence": "Wrong-T and shuffled-G controls pass; raw hidden construction fields are excluded.",
            "reason": "The result is not mere metadata leakage, but the label is still a controlled geometry-derived compatibility target rather than independent human reliability.",
            "next_action": "record_constructed_target_caveat",
        },
        {
            "route": "promote_to_broad_relation_reliability_now",
            "verdict": "reject",
            "evidence": "The result tests C_e for lying/standing support/contact compatibility, not p_rel/p_obs final reliability.",
            "reason": "Human/GT relation reliability and observability targets are not evaluated here.",
            "next_action": "do_not_claim_broad_reliability",
        },
        {
            "route": "promote_to_paper_evidence_now",
            "verdict": "defer",
            "evidence": "This is train-only hypothesis smoke and not Docker-reproduced paper experiment.",
            "reason": "Paper promotion needs frozen multi-family scope, external validity target, and Docker reproduction.",
            "next_action": "synthesize_multi_family_claim_boundary_first",
        },
        {
            "route": "merge_with_relative_vertical_as_multi_family_Ce_evidence",
            "verdict": "selected_next",
            "evidence": "Both relative_vertical and support_contact now have controlled same-G/same-family C_e smoke evidence.",
            "reason": "Before adding more families, H002 needs a coherent multi-family claim boundary and risk table.",
            "next_action": NEXT_TODO,
        },
        {
            "route": "run_attachment_or_proximity_next",
            "verdict": "defer",
            "evidence": "Attachment remains observability/visual-mesh limited; proximity risks collapsing into distance-only verification.",
            "reason": "Adding another family before synthesis may produce more artifacts without clarifying the claim.",
            "next_action": "reconsider_after_multi_family_synthesis",
        },
    ]


def family_rows() -> list[dict[str, Any]]:
    return [
        {
            "family": "relative_vertical",
            "current_status": "passed_scoped_Ce_mechanism",
            "predicates": "higher than; lower than",
            "evidence_available": "signed vertical OBB geometry",
            "decision": "retain_as_first_Ce_mechanism_result",
            "risk": "clean/easy same-G target; not broad reliability",
            "next_requirement": "include in multi-family synthesis with support/contact",
        },
        {
            "family": "support_contact_pose_conditioned",
            "current_status": "passed_scoped_Ce_mechanism",
            "predicates": "lying on; standing on",
            "evidence_available": "pose/orientation/contact/overlap/gap semseg features plus optional point contact",
            "decision": "retain_as_second_Ce_mechanism_result",
            "risk": "constructed geometry-derived label; independent human reliability not yet tested",
            "next_requirement": "include in multi-family synthesis and document constructed-target caveat",
        },
        {
            "family": "support_contact_superordinate",
            "current_status": "diagnostic_only",
            "predicates": "supported by",
            "evidence_available": "same support/contact features",
            "decision": "do_not_use_as_primary_negative",
            "risk": "superordinate overlap with standing/lying support states",
            "next_requirement": "keep as taxonomy/diagnostic relation",
        },
        {
            "family": "attachment_like",
            "current_status": "deferred_hard_family",
            "predicates": "attached to; hanging on; connected to",
            "evidence_available": "requires stronger visual/mesh/contact evidence",
            "decision": "defer",
            "risk": "target-independence and observability bottlenecks",
            "next_requirement": "use after visual/mesh evidence axis is deployable",
        },
        {
            "family": "proximity",
            "current_status": "future_generality",
            "predicates": "close by",
            "evidence_available": "distance geometry",
            "decision": "defer",
            "risk": "collapses to distance verifier rather than predicate-conditioned C_e",
            "next_requirement": "use only after multi-family claim boundary is stable",
        },
        {
            "family": "relative_horizontal",
            "current_status": "deferred",
            "predicates": "left; right; front; behind",
            "evidence_available": "requires frame/reference contract",
            "decision": "defer",
            "risk": "coordinate/reference-frame ambiguity",
            "next_requirement": "define frame semantics first",
        },
    ]


def caveat_rows() -> list[dict[str, Any]]:
    return [
        {
            "caveat": "constructed_target",
            "severity": "high",
            "description": "Labels are generated from a controlled pose-conditioned compatibility rule, not independent human relation reliability.",
            "mitigation": "Claim only C_e mechanism proof; require human/GT reliability target before p_rel claim.",
        },
        {
            "caveat": "too_clean_auc",
            "severity": "medium",
            "description": "M5b AUROC 1.0 may indicate an intentionally clean target rather than deployable robustness.",
            "mitigation": "Use as mechanism proof and add harder external/held-out family checks later.",
        },
        {
            "caveat": "calibration_not_established",
            "severity": "medium",
            "description": "Current ECE helper is diagnostic and not a calibrated probability proof.",
            "mitigation": "Run calibration-specific analysis only after target scope is frozen.",
        },
        {
            "caveat": "paper_evidence_not_yet",
            "severity": "high",
            "description": "The smoke is train-only and not Docker-reproduced.",
            "mitigation": "Do not use as paper table evidence until promoted into Docker experiment protocol.",
        },
    ]


def next_plan_contract() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "purpose": "Synthesize relative_vertical and support_contact C_e results into one claim boundary before adding more relation families.",
        "inputs": [
            "artifacts/compatibility_dataset_v3_sanitized_view_smoke_runner/summary.json",
            "artifacts/compatibility_dataset_v3_support_contact_pose_conditioned_sanitized_view_smoke_runner/summary.json",
        ],
        "required_questions": [
            "What common mechanism is shared by relative_vertical and support_contact C_e results?",
            "What claim is allowed without independent human/GT reliability labels?",
            "Is H002 now a multi-family C_e representation claim or still two isolated diagnostic targets?",
            "Which evidence factors are family-specific versus shared?",
            "What controls must be reproduced in Docker before paper promotion?",
            "Do we need one more family before a top-tier method claim, or should the next step target external validity?",
        ],
        "do_not_do_next": [
            "Do not claim final p_rel/p_obs reliability.",
            "Do not treat train-only smoke as paper evidence.",
            "Do not add attachment/proximity before writing the multi-family claim boundary.",
            "Do not hide that support/contact labels are controlled compatibility labels.",
        ],
        "success_condition": [
            "one concise allowed-claim statement",
            "family-by-family evidence table",
            "explicit reviewer risk table",
            "decision on next family versus external validation",
            "Docker promotion prerequisites",
        ],
    }


def build_decision(summary: dict[str, Any], errors: list[dict[str, Any]]) -> dict[str, Any]:
    status = STATUS_READY if not errors else STATUS_ERRORS
    next_todo = NEXT_TODO if not errors else "fix_support_contact_pose_conditioned_result_review_inputs"
    selected_path = SELECTED_PATH if not errors else "fix_inputs_before_decision"
    return {
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "runs_new_learned_smoke": False,
            "split": "train_only_result_review",
            "test_usage": False,
            "trains_new_model": False,
            "validation_usage": False,
        },
        "caveat_table": caveat_rows(),
        "claim_decision": {
            "allowed_claim": "scoped predicate-geometry compatibility mechanism for support/contact pose-conditioned relations",
            "blocked_claims": [
                "broad relation reliability",
                "final p_rel / p_obs decision quality",
                "human-audited relation reliability performance",
                "all 3DSSG relation-family generality",
                "paper-level Docker-reproduced result",
            ],
            "why": "The target is clean and controls pass, but it is a controlled C_e compatibility target rather than independent relation reliability ground truth.",
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "family_table": family_rows(),
        "mechanism_result": mechanism_summary(summary),
        "next_plan_contract": next_plan_contract(),
        "next_todo": next_todo,
        "route_table": route_rows(summary),
        "runner_root": rel_path(DEFAULT_RUNNER_DIR),
        "runner_status": summary.get("status"),
        "schema_version": SCHEMA_VERSION,
        "selected_path": selected_path,
        "status": status,
        "validation_errors": len(errors),
    }


def build_report(decision: dict[str, Any]) -> str:
    mech = decision["mechanism_result"]
    lines = [
        "# H002 Support/Contact Pose-Conditioned Result Review",
        "",
        "## Status",
        "",
        "```text",
        f"status = {decision['status']}",
        f"selected_path = {decision['selected_path']}",
        f"validation_errors = {decision['validation_errors']}",
        f"next_todo = {decision['next_todo']}",
        "```",
        "",
        "## Result Review",
        "",
        "```text",
        f"family = {mech['family']}",
        f"primary_model = {mech['primary_model']}",
        f"primary_auroc = {mech['primary_auroc']}",
        f"source_only_auroc = {mech['source_only_auroc']}",
        f"semantic_only_auroc = {mech['semantic_only_auroc']}",
        f"geometry_only_auroc = {mech['geometry_only_auroc']}",
        f"plain_concat_auroc = {mech['plain_concat_auroc']}",
        f"wrong_t_auroc = {mech['wrong_t_auroc']}",
        f"shuffled_g_global_auroc = {mech['shuffled_g_global_auroc']}",
        f"shuffled_g_within_predicate_auroc = {mech['shuffled_g_within_predicate_auroc']}",
        f"paired_score_margin = {mech['paired_score_margin']}",
        "```",
        "",
        "The support/contact smoke is accepted as a scoped `C_e` mechanism proof. It shows that",
        "the same predicate-independent support/contact `G_e` can become compatible or incompatible",
        "depending on `lying on` versus `standing on` semantic content `T_e`, while source-only,",
        "semantic-only, geometry-only, object-pair-only, quality-only, and plain-concat baselines",
        "remain near chance.",
        "",
        "This is not broad relation reliability. The target is a controlled compatibility target,",
        "not an independent human reliability label.",
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
            "## Caveats",
            "",
            "| Caveat | Severity | Mitigation |",
            "| --- | --- | --- |",
        ]
    )
    for row in decision["caveat_table"]:
        lines.append(f"| `{row['caveat']}` | `{row['severity']}` | {row['mitigation']} |")
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
            "| Family | Status | Decision | Next Requirement |",
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
            "The next step should synthesize relative-vertical and support/contact evidence before adding",
            "another family or making a paper-level claim.",
            "",
            "Required questions:",
            "",
        ]
    )
    for question in decision["next_plan_contract"]["required_questions"]:
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


def main() -> int:
    args = parse_args()
    runner_summary = read_json(args.runner_dir / "summary.json")
    validation_rows = read_jsonl(args.runner_dir / "validation_errors.jsonl")
    errors = validate_runner(runner_summary, validation_rows)
    decision = build_decision(runner_summary, errors)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", decision)
    write_json(
        output_dir / "path_decision.json",
        {
            "allowed_claim": decision["claim_decision"]["allowed_claim"],
            "blocked_claims": decision["claim_decision"]["blocked_claims"],
            "next_plan_contract": decision["next_plan_contract"],
            "next_todo": decision["next_todo"],
            "selected_path": decision["selected_path"],
        },
    )
    write_csv(output_dir / "route_table.csv", decision["route_table"])
    write_csv(output_dir / "family_table.csv", decision["family_table"])
    write_csv(output_dir / "caveat_table.csv", decision["caveat_table"])
    write_json(output_dir / "next_plan_contract.json", decision["next_plan_contract"])
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    (output_dir / "report.md").write_text(build_report(decision), encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
