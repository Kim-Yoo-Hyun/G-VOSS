#!/usr/bin/env python3
"""Review size-relative smoke result and freeze its H002 claim position."""

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
    / "artifacts/compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_size_relative_smoke_result_review_after_runner"
)

EXPECTED_RUNNER_STATUS = (
    "h002_compatibility_dataset_v3_size_relative_sanitized_view_smoke_runner_after_plan_passed_controls"
)
EXPECTED_RUNNER_NEXT = "compatibility_dataset_v3_size_relative_smoke_result_review_after_runner"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_size_relative_smoke_result_review_after_runner_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_size_relative_smoke_result_review_after_runner_ready_for_multi_family_synthesis_update"
)
STATUS_ERRORS = "h002_compatibility_dataset_v3_size_relative_smoke_result_review_after_runner_input_errors"
SELECTED_PATH = "promote_size_relative_as_main_compatibility_route_evidence_keep_calibration_caveat"
NEXT_TODO = "compatibility_dataset_v3_multi_family_claim_synthesis_after_size_relative"


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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
                seen.add(key)
                fields.append(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def metric_map(rows: list[dict[str, str]]) -> dict[str, dict[str, float | str]]:
    mapped: dict[str, dict[str, float | str]] = {}
    for row in rows:
        name = row.get("model", "")
        if not name:
            continue
        values: dict[str, float | str] = {}
        for key, value in row.items():
            if key == "model":
                continue
            try:
                values[key] = float(value)
            except (TypeError, ValueError):
                values[key] = value
        mapped[name] = values
    return mapped


def auroc(metrics: dict[str, dict[str, float | str]], model: str) -> float | None:
    value = metrics.get(model, {}).get("auroc")
    return float(value) if isinstance(value, (int, float)) else None


def validate_inputs(
    runner_summary: dict[str, Any],
    gate_summary: dict[str, Any],
    metrics: dict[str, dict[str, float | str]],
    validation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if runner_summary.get("status") != EXPECTED_RUNNER_STATUS:
        errors.append({"error_type": "unexpected_runner_status", "actual": runner_summary.get("status")})
    if runner_summary.get("next_todo") != EXPECTED_RUNNER_NEXT:
        errors.append({"error_type": "unexpected_runner_next_todo", "actual": runner_summary.get("next_todo")})
    if runner_summary.get("validation_errors") != 0:
        errors.append({"error_type": "runner_validation_errors", "actual": runner_summary.get("validation_errors")})
    if validation_rows:
        errors.append({"error_type": "runner_validation_error_rows_present", "rows": len(validation_rows)})
    if gate_summary.get("overall_pass") is not True:
        errors.append({"error_type": "runner_gate_not_passed", "gate_summary": gate_summary})

    for gate_name, gate in gate_summary.items():
        if (
            gate_name.startswith("gate_")
            and isinstance(gate, dict)
            and "pass" in gate
            and gate.get("pass") is not True
        ):
            errors.append({"error_type": "failed_gate", "gate": gate_name, "data": gate})

    boundary = runner_summary.get("boundary", {})
    for key in ["h001_artifacts_modified", "paper_evidence_allowed", "q_e_used_as_truth", "test_usage", "validation_usage"]:
        if boundary.get(key) is not False:
            errors.append({"error_type": "boundary_not_false", "key": key, "actual": boundary.get(key)})
    if boundary.get("split") != "train_only_grouped_cv_smoke":
        errors.append({"error_type": "unexpected_split", "actual": boundary.get("split")})
    if boundary.get("source_score_used") is not False:
        errors.append({"error_type": "source_score_used_in_size_relative_smoke"})

    required_models = [
        "M1_semantic_only_T",
        "M2_geometry_only_G_size",
        "M3_TG_concat_no_interaction",
        "M4_TG_size_interaction",
        "C1_wrong_T_same_G",
        "C2_shuffled_G_global",
        "C3_shuffled_G_within_predicate",
        "C4_sign_flipped_G_control",
        "S2_geometry_exact_tuple_shortcut",
    ]
    for model in required_models:
        if model not in metrics:
            errors.append({"error_type": "missing_metric_model", "model": model})

    primary = auroc(metrics, "M4_TG_size_interaction")
    semantic = auroc(metrics, "M1_semantic_only_T")
    geometry = auroc(metrics, "M2_geometry_only_G_size")
    concat = auroc(metrics, "M3_TG_concat_no_interaction")
    wrong_t = auroc(metrics, "C1_wrong_T_same_G")
    shuffle_global = auroc(metrics, "C2_shuffled_G_global")
    shuffle_within = auroc(metrics, "C3_shuffled_G_within_predicate")
    sign_flip = auroc(metrics, "C4_sign_flipped_G_control")

    if primary is None or primary < 0.95:
        errors.append({"error_type": "primary_tg_interaction_below_review_gate", "actual": primary})
    if max(v for v in [semantic, geometry, concat] if v is not None) > 0.60:
        errors.append(
            {
                "error_type": "single_or_concat_baseline_too_high",
                "semantic": semantic,
                "geometry": geometry,
                "concat": concat,
            }
        )
    if wrong_t is None or wrong_t > 0.60:
        errors.append({"error_type": "wrong_t_control_not_collapsed", "actual": wrong_t})
    if shuffle_global is None or shuffle_within is None or max(shuffle_global, shuffle_within) > 0.60:
        errors.append(
            {
                "error_type": "shuffled_g_control_not_near_chance",
                "global": shuffle_global,
                "within_predicate": shuffle_within,
            }
        )
    if sign_flip is None or sign_flip > 0.60:
        errors.append({"error_type": "sign_flip_control_not_collapsed", "actual": sign_flip})
    return errors


def route_position(metrics: dict[str, dict[str, float | str]]) -> list[dict[str, Any]]:
    primary = auroc(metrics, "M4_TG_size_interaction")
    semantic = auroc(metrics, "M1_semantic_only_T")
    geometry = auroc(metrics, "M2_geometry_only_G_size")
    concat = auroc(metrics, "M3_TG_concat_no_interaction")
    wrong_t = auroc(metrics, "C1_wrong_T_same_G")
    shuffle_global = auroc(metrics, "C2_shuffled_G_global")
    shuffle_within = auroc(metrics, "C3_shuffled_G_within_predicate")
    sign_flip = auroc(metrics, "C4_sign_flipped_G_control")
    return [
        {
            "relation_family": "size_relative",
            "predicates": "bigger than / smaller than",
            "route_role": "main_compatibility_route_mechanism_evidence",
            "status": "passed_train_only_controls",
            "evidence": (
                f"T_e only={semantic:.4f}, G_e_size only={geometry:.4f}, concat={concat:.4f}, "
                f"T_e x G_e_size={primary:.4f}, wrong-T={wrong_t:.5f}, "
                f"shuffled-G={shuffle_global:.4f}/{shuffle_within:.4f}, sign-flip={sign_flip:.5f}"
            ),
            "claim": "same geometry evidence must be interpreted differently by predicate semantics",
            "not_claim": "calibrated relation reliability probability or held-out paper result",
        },
        {
            "relation_family": "relative_vertical",
            "predicates": "higher than / lower than",
            "route_role": "clean_compatibility_route_prior_evidence",
            "status": "already_passed_previous_v3_review",
            "evidence": "same-G predicate-flip target previously accepted as scoped C_e proof",
            "claim": "relative-direction geometry requires predicate-conditioned sign interpretation",
            "not_claim": "all relation-family generalization",
        },
        {
            "relation_family": "support_contact",
            "predicates": "standing on / lying on",
            "route_role": "challenging_compatibility_route_evidence_with_caveat",
            "status": "near_threshold_but_useful",
            "evidence": "point/contact plus predicate interaction outperforms semantic-only and geometry-only; ambiguity remains",
            "claim": "support/contact needs predicate-geometry interaction, not fixed fusion",
            "not_claim": "fully solved support/contact reliability",
        },
        {
            "relation_family": "proximity",
            "predicates": "close by",
            "route_role": "geometry_easy_control_diagnostic",
            "status": "diagnostic_only",
            "evidence": "distance/rule baselines solve the current target",
            "claim": "some relation families should route to geometry-only controls",
            "not_claim": "learned compatibility target",
        },
    ]


def claim_boundary(metrics: dict[str, dict[str, float | str]]) -> list[dict[str, Any]]:
    primary = metrics["M4_TG_size_interaction"]
    return [
        {
            "claim_area": "C_e mechanism",
            "allowed": True,
            "statement": "`size_relative` supports predicate-geometry compatibility because only the interaction model succeeds.",
            "evidence": f"AUROC={float(primary['auroc']):.4f}; controls passed.",
        },
        {
            "claim_area": "geometry-only scoring",
            "allowed": False,
            "statement": "The result should not be described as a geometry-only score improvement.",
            "evidence": "G_e_size only AUROC is 0.5000.",
        },
        {
            "claim_area": "plain semantic + geometry concatenation",
            "allowed": False,
            "statement": "Plain concatenation is not enough for this target.",
            "evidence": "T_e+G_e no-interaction AUROC is 0.4707.",
        },
        {
            "claim_area": "calibrated reliability probability",
            "allowed": False,
            "statement": "Do not claim calibrated p_rel or p_obs from this smoke.",
            "evidence": f"Primary ECE={float(primary['ece_10']):.4f}; runner is a ranking/decision smoke.",
        },
        {
            "claim_area": "paper-level result",
            "allowed": False,
            "statement": "Do not use this as paper-level evidence until Docker and held-out protocol are defined.",
            "evidence": "Boundary is train-only grouped-CV smoke; validation/test usage is false.",
        },
        {
            "claim_area": "relation-family generality",
            "allowed": "partial",
            "statement": "Use as one route in a multi-family synthesis, not as a universal relation reliability claim.",
            "evidence": "size_relative is a clean physical family; support/contact and attachment remain harder.",
        },
    ]


def reviewer_risks() -> list[dict[str, Any]]:
    return [
        {
            "risk": "target_too_deterministic",
            "severity": "medium",
            "why_it_matters": "bigger/smaller can look like a constructed sign rule.",
            "mitigation": "Frame as mechanism/control evidence for C_e; rely on same-G predicate flip, single-factor failures, wrong-T, shuffled-G, and sign-flip controls.",
        },
        {
            "risk": "not_calibrated_probability",
            "severity": "high_if_overclaimed",
            "why_it_matters": "AUROC is strong but ECE is high.",
            "mitigation": "State that this is compatibility ranking/decision evidence only; calibration requires a separate p_rel/p_obs stage.",
        },
        {
            "risk": "train_only_artifact",
            "severity": "medium",
            "why_it_matters": "Hypothesis-stage grouped CV is not paper-level reproducibility.",
            "mitigation": "Keep paper_evidence_allowed=false until Docker, held-out split, and artifact provenance are promoted.",
        },
        {
            "risk": "family_specific_success",
            "severity": "medium",
            "why_it_matters": "Reviewer may ask whether only size-relative and vertical relations work.",
            "mitigation": "Integrate size-relative as one route among relative_vertical, support_contact, proximity diagnostics, and future attachment/visual routes.",
        },
    ]


def next_steps() -> list[dict[str, Any]]:
    return [
        {
            "order": 1,
            "next_todo": NEXT_TODO,
            "action": "Update multi-family synthesis to include size_relative as a passed compatibility-route evidence row.",
            "blocked": False,
        },
        {
            "order": 2,
            "next_todo": "compatibility_dataset_v3_ablation_table_update_after_size_relative",
            "action": "Prepare a hypothesis-stage ablation table view across relative_vertical, support_contact, close_by, and size_relative.",
            "blocked": "until multi-family synthesis is updated",
        },
        {
            "order": 3,
            "next_todo": "docker_promotion_plan_for_h002_only_if_user_confirms",
            "action": "Define paper-level reproduction only after the family-route claim is frozen.",
            "blocked": "requires user decision and experiment-root planning",
        },
    ]


def write_report(
    path: Path,
    summary: dict[str, Any],
    metrics: dict[str, dict[str, float | str]],
    route_rows: list[dict[str, Any]],
    boundary_rows: list[dict[str, Any]],
) -> None:
    primary = metrics["M4_TG_size_interaction"]
    lines = [
        "# Size-Relative Smoke Result Review After Runner",
        "",
        f"Created: {summary['created_at_utc']}",
        "",
        "## Decision",
        "",
        "`size_relative`는 H002의 `main compatibility-route mechanism evidence`로 배치한다.",
        "다만 이 결과는 train-only grouped-CV smoke이며, calibrated reliability probability나 paper-level result는 아니다.",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Key Numbers",
        "",
        "```text",
        f"M1_semantic_only_T AUROC = {metrics['M1_semantic_only_T']['auroc']:.4f}",
        f"M2_geometry_only_G_size AUROC = {metrics['M2_geometry_only_G_size']['auroc']:.4f}",
        f"M3_TG_concat_no_interaction AUROC = {metrics['M3_TG_concat_no_interaction']['auroc']:.4f}",
        f"M4_TG_size_interaction AUROC = {primary['auroc']:.4f}",
        f"M4_TG_size_interaction ECE = {primary['ece_10']:.4f}",
        f"C1_wrong_T_same_G AUROC = {metrics['C1_wrong_T_same_G']['auroc']:.5f}",
        f"C2/C3 shuffled-G AUROC = {metrics['C2_shuffled_G_global']['auroc']:.4f} / {metrics['C3_shuffled_G_within_predicate']['auroc']:.4f}",
        f"C4_sign_flipped_G_control AUROC = {metrics['C4_sign_flipped_G_control']['auroc']:.5f}",
        "```",
        "",
        "## Interpretation",
        "",
        "- `T_e` 단독과 `G_e_size` 단독은 target을 풀지 못했다.",
        "- 단순 concat도 실패했으므로, 이 family에서는 명시적 `T_e x G_e` interaction이 필요하다.",
        "- wrong-T와 sign-flipped-G는 거의 완전히 반전되고, shuffled-G는 chance 근처로 무너졌다.",
        "- 따라서 이 결과는 `C_e = compatibility(T_e, G_e)`의 메커니즘 증거로 강하다.",
        "- 단, ECE가 높으므로 `p_rel` calibration 또는 posterior probability claim은 별도 단계가 필요하다.",
        "",
        "## Route Position",
        "",
    ]
    for row in route_rows:
        lines.extend(
            [
                f"- `{row['relation_family']}`: {row['route_role']} / {row['status']}",
                f"  - claim: {row['claim']}",
                f"  - not claim: {row['not_claim']}",
            ]
        )
    lines.extend(["", "## Claim Boundary", ""])
    for row in boundary_rows:
        lines.append(f"- {row['claim_area']}: allowed={row['allowed']} / {row['statement']}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    runner_dir = args.runner_dir
    output_dir = args.output_dir

    runner_summary = read_json(runner_dir / "summary.json")
    gate_summary = read_json(runner_dir / "gate_summary.json")
    metrics_rows = read_csv(runner_dir / "metrics_table.csv")
    metrics = metric_map(metrics_rows)
    runner_validation = read_jsonl(runner_dir / "validation_errors.jsonl")

    errors = validate_inputs(runner_summary, gate_summary, metrics, runner_validation)
    route_rows = route_position(metrics) if not errors else []
    boundary_rows = claim_boundary(metrics) if not errors else []
    risk_rows = reviewer_risks()
    next_rows = next_steps()

    status = STATUS_ERRORS if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "validation_errors": len(errors),
        "input_paths": {
            "runner_dir": rel_path(runner_dir),
            "runner_summary": rel_path(runner_dir / "summary.json"),
            "runner_gate_summary": rel_path(runner_dir / "gate_summary.json"),
            "runner_metrics_table": rel_path(runner_dir / "metrics_table.csv"),
        },
        "output_paths": {
            "artifact_root": rel_path(output_dir),
            "summary": rel_path(output_dir / "summary.json"),
            "review_decision": rel_path(output_dir / "review_decision.json"),
            "route_position": rel_path(output_dir / "route_position.csv"),
            "claim_boundary": rel_path(output_dir / "claim_boundary.csv"),
            "reviewer_risks": rel_path(output_dir / "reviewer_risks.csv"),
            "next_steps": rel_path(output_dir / "next_steps.csv"),
            "report": rel_path(output_dir / "report.md"),
            "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
        },
        "runner_snapshot": {
            "rows": runner_summary.get("counts", {}).get("rows"),
            "positive": runner_summary.get("counts", {}).get("positive"),
            "negative": runner_summary.get("counts", {}).get("negative"),
            "groups": runner_summary.get("counts", {}).get("groups"),
            "primary_model": runner_summary.get("primary_model"),
            "primary_auroc": auroc(metrics, "M4_TG_size_interaction"),
            "semantic_only_auroc": auroc(metrics, "M1_semantic_only_T"),
            "geometry_only_auroc": auroc(metrics, "M2_geometry_only_G_size"),
            "concat_auroc": auroc(metrics, "M3_TG_concat_no_interaction"),
            "wrong_t_auroc": auroc(metrics, "C1_wrong_T_same_G"),
            "shuffled_g_global_auroc": auroc(metrics, "C2_shuffled_G_global"),
            "shuffled_g_within_predicate_auroc": auroc(metrics, "C3_shuffled_G_within_predicate"),
            "sign_flipped_g_auroc": auroc(metrics, "C4_sign_flipped_G_control"),
            "ece_10": metrics.get("M4_TG_size_interaction", {}).get("ece_10"),
        },
        "boundary": {
            "h001_artifacts_modified": False,
            "paper_evidence_allowed": False,
            "test_usage": False,
            "validation_usage": False,
            "calibrated_probability_claim_allowed": False,
            "relation_family_generality_claim_allowed": "partial_only",
            "split": "train_only_grouped_cv_smoke",
        },
    }
    review_decision = {
        "selected_path": summary["selected_path"],
        "decision": "use_size_relative_as_main_C_e_mechanism_evidence" if not errors else "blocked",
        "allowed_claim": (
            "size-relative relations show that predicate semantics must condition geometry evidence: "
            "the same G_e_size supports either bigger-than or smaller-than depending on T_e."
        )
        if not errors
        else None,
        "blocked_claims": [
            "calibrated p_rel / p_obs probability",
            "paper-level performance result",
            "geometry-only relation reliability",
            "universal all-family generalization",
        ],
        "why_next": "multi-family synthesis must be updated before table planning or Docker promotion",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", summary)
    write_json(output_dir / "review_decision.json", review_decision)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_csv(output_dir / "route_position.csv", route_rows)
    write_csv(output_dir / "claim_boundary.csv", boundary_rows)
    write_csv(output_dir / "reviewer_risks.csv", risk_rows)
    write_csv(output_dir / "next_steps.csv", next_rows)
    if not errors:
        write_report(output_dir / "report.md", summary, metrics, route_rows, boundary_rows)
    else:
        (output_dir / "report.md").write_text(
            "# Size-Relative Smoke Result Review After Runner\n\nInput validation failed; see `validation_errors.jsonl`.\n",
            encoding="utf-8",
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
