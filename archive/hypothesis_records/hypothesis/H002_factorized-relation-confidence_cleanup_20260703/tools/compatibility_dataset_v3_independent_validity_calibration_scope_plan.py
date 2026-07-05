#!/usr/bin/env python3
"""Plan H002 calibration and family-scope route after the repaired C_e smoke review."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_REVIEW_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review"
)
DEFAULT_RUNNER_DIR = (
    H2_ROOT
    / "artifacts/compatibility_dataset_v3_independent_validity_stratum_repair_sanitized_view_smoke_runner"
)
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_independent_validity_calibration_scope_plan"

EXPECTED_REVIEW_STATUS = (
    "h002_compatibility_dataset_v3_independent_validity_stratum_repair_smoke_result_review_accept_Ce_select_calibration_scope_plan"
)
EXPECTED_REVIEW_NEXT = "compatibility_dataset_v3_independent_validity_calibration_scope_plan"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_independent_validity_calibration_scope_plan_v1"
STATUS_READY = (
    "h002_compatibility_dataset_v3_independent_validity_calibration_scope_plan_select_support_contact_balancing"
)
STATUS_ERRORS = "h002_compatibility_dataset_v3_independent_validity_calibration_scope_plan_input_errors"
SELECTED_PATH = "calibration_metric_audit_passed_select_support_contact_family_balancing"
NEXT_TODO = "compatibility_dataset_v3_independent_validity_support_contact_balancing_plan"

PRIMARY_MODEL = "M6_TG_compatibility_interaction"
FULL_MODEL = "M7_factorized_TZGQ"
CALIBRATION_ECE_MAX = 0.07
SUPPORT_CONTACT_PRIMARY_MIN_ROWS = 400


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-dir", type=Path, default=DEFAULT_REVIEW_DIR)
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
                fields.append(key)
                seen.add(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def clamp_prob(score: float) -> float:
    return max(1e-6, min(1.0 - 1e-6, score))


def calibration_metrics(labels: list[int], scores: list[float], bins: int = 10) -> dict[str, Any]:
    n = len(labels)
    if n == 0:
        return {
            "n": 0,
            "positive": 0,
            "negative": 0,
            "brier": None,
            "nll": None,
            "probability_ece_10": None,
            "confidence_ece_10": None,
            "mean_positive_score": None,
            "mean_negative_score": None,
            "bin_rows": [],
        }
    brier = sum((score - label) ** 2 for label, score in zip(labels, scores)) / n
    nll = -sum(
        label * math.log(clamp_prob(score)) + (1 - label) * math.log(clamp_prob(1.0 - score))
        for label, score in zip(labels, scores)
    ) / n

    prob_ece = 0.0
    conf_ece = 0.0
    bin_rows: list[dict[str, Any]] = []
    for idx in range(bins):
        lo = idx / bins
        hi = (idx + 1) / bins
        indices = [
            row_idx
            for row_idx, score in enumerate(scores)
            if (lo <= score < hi) or (idx == bins - 1 and lo <= score <= hi)
        ]
        if not indices:
            continue
        mean_score = sum(scores[row_idx] for row_idx in indices) / len(indices)
        positive_rate = sum(labels[row_idx] for row_idx in indices) / len(indices)
        probability_gap = abs(mean_score - positive_rate)
        prob_ece += (len(indices) / n) * probability_gap

        confidences = [max(scores[row_idx], 1.0 - scores[row_idx]) for row_idx in indices]
        correctness = [
            1.0 if (scores[row_idx] >= 0.5) == bool(labels[row_idx]) else 0.0
            for row_idx in indices
        ]
        mean_confidence = sum(confidences) / len(confidences)
        accuracy = sum(correctness) / len(correctness)
        confidence_gap = abs(mean_confidence - accuracy)
        conf_ece += (len(indices) / n) * confidence_gap

        bin_rows.append(
            {
                "bin": idx,
                "lo": lo,
                "hi": hi,
                "rows": len(indices),
                "mean_score": mean_score,
                "positive_rate": positive_rate,
                "probability_gap": probability_gap,
                "mean_confidence": mean_confidence,
                "accuracy": accuracy,
                "confidence_gap": confidence_gap,
            }
        )

    positives = [score for label, score in zip(labels, scores) if label == 1]
    negatives = [score for label, score in zip(labels, scores) if label == 0]
    return {
        "n": n,
        "positive": sum(labels),
        "negative": n - sum(labels),
        "brier": brier,
        "nll": nll,
        "probability_ece_10": prob_ece,
        "confidence_ece_10": conf_ece,
        "mean_positive_score": sum(positives) / len(positives) if positives else None,
        "mean_negative_score": sum(negatives) / len(negatives) if negatives else None,
        "min_score": min(scores),
        "max_score": max(scores),
        "bin_rows": bin_rows,
    }


def flatten_calibration_rows(prediction_rows: list[dict[str, Any]], runner_summary: dict[str, Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for model in [
        "M2_source_only_Z",
        "M4_geometry_only_G",
        PRIMARY_MODEL,
        FULL_MODEL,
    ]:
        labels = [int(row["label"]) for row in prediction_rows]
        scores = [float(row[model]) for row in prediction_rows]
        metric = calibration_metrics(labels, scores)
        legacy = runner_summary.get("key_metrics", {}).get(model, {})
        output.append(
            {
                "slice": "all",
                "model": model,
                "rows": metric["n"],
                "positive": metric["positive"],
                "negative": metric["negative"],
                "auroc": legacy.get("auroc"),
                "legacy_runner_ece_10": legacy.get("ece_10"),
                "legacy_ece_interpretation": "threshold_correctness_ece_not_binary_probability_calibration",
                "probability_ece_10": metric["probability_ece_10"],
                "confidence_ece_10": metric["confidence_ece_10"],
                "brier": metric["brier"],
                "nll": metric["nll"],
                "mean_positive_score": metric["mean_positive_score"],
                "mean_negative_score": metric["mean_negative_score"],
                "calibration_gate_pass": (
                    metric["probability_ece_10"] is not None and metric["probability_ece_10"] <= CALIBRATION_ECE_MAX
                ),
            }
        )
        for family in sorted({str(row["family"]) for row in prediction_rows}):
            family_rows = [row for row in prediction_rows if str(row["family"]) == family]
            family_labels = [int(row["label"]) for row in family_rows]
            family_scores = [float(row[model]) for row in family_rows]
            family_metric = calibration_metrics(family_labels, family_scores)
            output.append(
                {
                    "slice": f"family::{family}",
                    "model": model,
                    "rows": family_metric["n"],
                    "positive": family_metric["positive"],
                    "negative": family_metric["negative"],
                    "auroc": None,
                    "legacy_runner_ece_10": None,
                    "legacy_ece_interpretation": "not_reported_for_family_slice",
                    "probability_ece_10": family_metric["probability_ece_10"],
                    "confidence_ece_10": family_metric["confidence_ece_10"],
                    "brier": family_metric["brier"],
                    "nll": family_metric["nll"],
                    "mean_positive_score": family_metric["mean_positive_score"],
                    "mean_negative_score": family_metric["mean_negative_score"],
                    "calibration_gate_pass": (
                        family_metric["probability_ece_10"] is not None
                        and family_metric["probability_ece_10"] <= CALIBRATION_ECE_MAX
                    ),
                }
            )
    return output


def validate(review_summary: dict[str, Any], runner_summary: dict[str, Any], prediction_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if review_summary.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error_type": "unexpected_review_status", "actual": review_summary.get("status")})
    if review_summary.get("next_todo") != EXPECTED_REVIEW_NEXT:
        errors.append({"error_type": "unexpected_review_next", "actual": review_summary.get("next_todo")})
    if review_summary.get("validation_errors") != 0:
        errors.append({"error_type": "review_validation_errors", "actual": review_summary.get("validation_errors")})
    if runner_summary.get("validation_errors") != 0:
        errors.append({"error_type": "runner_validation_errors", "actual": runner_summary.get("validation_errors")})
    if len(prediction_rows) != 1600:
        errors.append({"error_type": "unexpected_prediction_rows", "actual": len(prediction_rows)})
    counts = Counter(row.get("family") for row in prediction_rows)
    if counts.get("relative_vertical") != 1512:
        errors.append({"error_type": "unexpected_relative_vertical_rows", "actual": counts.get("relative_vertical")})
    if counts.get("support_contact_pose_conditioned") != 88:
        errors.append({"error_type": "unexpected_support_contact_rows", "actual": counts.get("support_contact_pose_conditioned")})
    if review_summary.get("boundary", {}).get("h001_artifacts_modified") is not False:
        errors.append({"error_type": "h001_boundary_not_false"})
    return errors


def route_rows(calibration_rows: list[dict[str, Any]], review_summary: dict[str, Any]) -> list[dict[str, Any]]:
    primary = next(row for row in calibration_rows if row["slice"] == "all" and row["model"] == PRIMARY_MODEL)
    support = review_summary.get("mechanism_result", {}).get("family_slice", {}).get("support_contact_pose_conditioned", {})
    return [
        {
            "route": "calibration_repair_first",
            "verdict": "not_selected_as_immediate_next",
            "evidence": (
                f"legacy runner ECE={primary['legacy_runner_ece_10']}, but probability-ECE={primary['probability_ece_10']} "
                f"and Brier={primary['brier']}."
            ),
            "reason": "The apparent high ECE is mainly a metric-definition issue. A calibration metric fix is required, but global C_e calibration is not the dominant blocker.",
            "next_action": "fix/report calibration metric definitions when running the next smoke; do not claim p_rel yet",
        },
        {
            "route": "support_contact_family_balancing_first",
            "verdict": "selected",
            "evidence": (
                f"support/contact rows={support.get('rows')}, M6 AUROC={support.get('primary_auroc')}, "
                f"wrong-predicate AUROC={support.get('wrong_predicate_auroc')}."
            ),
            "reason": "The current evidence is relative-vertical dominant; support/contact is the closest physical family needed for generality and reliability framing.",
            "next_action": NEXT_TODO,
        },
        {
            "route": "docker_paper_promotion_now",
            "verdict": "blocked",
            "evidence": "All current H002 evidence is train-only hypothesis-stage and family-imbalanced.",
            "reason": "Docker promotion before family/scope repair would only reproduce a scoped C_e smoke, not a paper-level reliability experiment.",
            "next_action": "defer_until_support_contact_balancing_and_calibration_metric_fix",
        },
        {
            "route": "larger_architecture_or_combiner_now",
            "verdict": "reject",
            "evidence": "M6 and M7 are already near-perfect globally.",
            "reason": "The next bottleneck is evidence scope, not model capacity.",
            "next_action": "avoid transformer/MoE until support/contact target and held-out design exist",
        },
        {
            "route": "calibrated_p_rel_claim_now",
            "verdict": "reject",
            "evidence": "The current target is C_e compatibility, not final p_rel/p_obs reliability.",
            "reason": "Even with proper C_e calibration, p_rel requires observable reliability labels or a deployable selective-decision target.",
            "next_action": "keep p_rel/p_obs blocked",
        },
    ]


def scope_rows(review_summary: dict[str, Any], calibration_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mech = review_summary.get("mechanism_result", {})
    primary_cal = next(row for row in calibration_rows if row["slice"] == "all" and row["model"] == PRIMARY_MODEL)
    support = mech.get("family_slice", {}).get("support_contact_pose_conditioned", {})
    relative = mech.get("family_slice", {}).get("relative_vertical", {})
    return [
        {
            "axis": "calibration_metric",
            "status": "metric_definition_repaired_in_plan",
            "evidence": f"legacy ECE {primary_cal['legacy_runner_ece_10']} vs probability-ECE {primary_cal['probability_ece_10']}",
            "decision": "legacy runner ECE must not be used as a calibrated-posterior blocker by itself",
            "claim_allowed": "C_e ranking plus provisional probability-calibration diagnostic",
            "claim_blocked": "calibrated p_rel posterior",
        },
        {
            "axis": "relative_vertical_scope",
            "status": "primary_supported",
            "evidence": f"rows={relative.get('rows')}, M6 AUROC={relative.get('primary_auroc')}",
            "decision": "retain as core C_e mechanism proof",
            "claim_allowed": "predicate-conditioned vertical compatibility",
            "claim_blocked": "all-family reliability",
        },
        {
            "axis": "support_contact_scope",
            "status": "insufficient_for_primary_claim",
            "evidence": f"rows={support.get('rows')}, M6 AUROC={support.get('primary_auroc')}, wrong-predicate AUROC={support.get('wrong_predicate_auroc')}",
            "decision": "selected next target repair/balancing axis",
            "claim_allowed": "diagnostic signal only",
            "claim_blocked": "support/contact independent-validity generality",
        },
        {
            "axis": "paper_promotion",
            "status": "blocked",
            "evidence": "train-only hypothesis runner, no validation/test and no Docker H002 experiment root",
            "decision": "do not promote",
            "claim_allowed": "none",
            "claim_blocked": "paper-level H002 experiment",
        },
    ]


def next_plan() -> dict[str, Any]:
    return {
        "next_todo": NEXT_TODO,
        "objective": "Create a support/contact-focused independent-validity balancing plan before any paper or p_rel claim.",
        "why_next": [
            "Global C_e discrimination is strong.",
            "The high legacy ECE was a metric-definition issue, not enough to justify calibration-repair-first.",
            "The main unresolved blocker is family scope: relative_vertical dominates the current target.",
            "Support/contact is the closest physical family needed to test whether C_e generalizes beyond vertical order.",
        ],
        "required_design": [
            "Use train-only rows only.",
            "Target support/contact primary rows at or above 400 if capacity allows.",
            "Keep source score Z_e outside C_e compatibility features.",
            "Use raw geometry/mesh-pose-contact evidence, not p_geom_valid or geometry_status.",
            "Report semantic/source, geometry-only, plain T+G, C_e interaction, full factorized, shuffled-G, and wrong-predicate controls.",
            "Use corrected probability-ECE and Brier for calibration diagnostics.",
            "Keep p_rel/p_obs and paper claims blocked until a held-out/Docker protocol exists.",
        ],
        "candidate_next_artifacts": [
            "support_contact_capacity_or_inventory",
            "support_contact_balanced_materialization_plan",
            "support_contact_schema_shortcut_audit",
            "support_contact_smoke_plan_with_corrected_calibration_metrics",
        ],
    }


def write_report(
    path: Path,
    summary: dict[str, Any],
    calibration_rows: list[dict[str, Any]],
    routes: list[dict[str, Any]],
    scope: list[dict[str, Any]],
) -> None:
    primary = next(row for row in calibration_rows if row["slice"] == "all" and row["model"] == PRIMARY_MODEL)
    full = next(row for row in calibration_rows if row["slice"] == "all" and row["model"] == FULL_MODEL)
    selected = next(row for row in routes if row["verdict"] == "selected")
    lines = [
        "# Compatibility Dataset V3 Independent Validity Calibration Scope Plan",
        "",
        "Artifact root:",
        "",
        "```text",
        "artifacts/compatibility_dataset_v3_independent_validity_calibration_scope_plan/",
        "```",
        "",
        "Status:",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_path = {summary['selected_path']}",
        f"validation_errors = {summary['validation_errors']}",
        f"next_todo = {summary['next_todo']}",
        "```",
        "",
        "## Calibration Metric Audit",
        "",
        "The previous runner's `ECE-10` is not a valid binary probability-calibration gate because it",
        "compares threshold correctness with the raw positive-class score. Recomputing standard",
        "bin-wise probability ECE changes the interpretation:",
        "",
        f"- `{PRIMARY_MODEL}` legacy ECE: `{primary['legacy_runner_ece_10']}`",
        f"- `{PRIMARY_MODEL}` probability ECE: `{primary['probability_ece_10']}`",
        f"- `{PRIMARY_MODEL}` Brier: `{primary['brier']}`",
        f"- `{FULL_MODEL}` probability ECE: `{full['probability_ece_10']}`",
        "",
        "This does not allow a calibrated `p_rel` claim, because the current target is still `C_e`",
        "compatibility and the evidence is train-only. It only means calibration repair is not the",
        "first blocker.",
        "",
        "## Selected Route",
        "",
        f"`{selected['route']}`",
        "",
        selected["reason"],
        "",
        "## Scope Decisions",
        "",
    ]
    for row in scope:
        lines.append(f"- `{row['axis']}`: {row['decision']}")
    lines.extend(
        [
            "",
            "## Blocked",
            "",
            "- calibrated `p_rel` / `p_obs` posterior;",
            "- paper-level H002 experiment;",
            "- all-family 3DSSG reliability;",
            "- larger architecture as the next step.",
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


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    review_summary = read_json(args.review_dir / "summary.json")
    runner_summary = read_json(args.runner_dir / "summary.json")
    predictions = read_jsonl(args.runner_dir / "predictions.jsonl")
    errors = validate(review_summary, runner_summary, predictions)
    calibration_rows = flatten_calibration_rows(predictions, runner_summary)
    routes = route_rows(calibration_rows, review_summary)
    scope = scope_rows(review_summary, calibration_rows)
    plan = next_plan()

    summary = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": STATUS_ERRORS if errors else STATUS_READY,
        "selected_path": None if errors else SELECTED_PATH,
        "next_todo": None if errors else NEXT_TODO,
        "review_root": rel_path(args.review_dir),
        "runner_root": rel_path(args.runner_dir),
        "output_root": rel_path(args.output_dir),
        "validation_errors": len(errors),
        "calibration_ece_max": CALIBRATION_ECE_MAX,
        "support_contact_primary_min_rows": SUPPORT_CONTACT_PRIMARY_MIN_ROWS,
        "calibration_metric_audit": {
            "legacy_runner_ece_valid_for_binary_probability_calibration": False,
            "proper_probability_ece_required": True,
            "primary_model": next(row for row in calibration_rows if row["slice"] == "all" and row["model"] == PRIMARY_MODEL),
            "full_model": next(row for row in calibration_rows if row["slice"] == "all" and row["model"] == FULL_MODEL),
        },
        "selected_route": next(row for row in routes if row["verdict"] == "selected"),
        "claim_boundary": {
            "allowed_now": "train-only C_e discrimination/ranking evidence",
            "blocked": [
                "calibrated p_rel/p_obs posterior",
                "paper-level evidence",
                "held-out performance",
                "support/contact primary generality",
                "all-family 3DSSG reliability",
            ],
            "calibration_update": (
                "Legacy ECE is downgraded to a helper-definition artifact; corrected probability-ECE should be used going forward."
            ),
        },
        "paper_evidence_allowed": False,
        "boundary": {
            "split": "train_internal_grouped_cv",
            "validation_usage": False,
            "test_usage": False,
            "h001_artifacts_modified": False,
            "paper_promotion_allowed": False,
            "calibrated_p_rel_claim_allowed": False,
        },
        "output_paths": {
            "summary": rel_path(args.output_dir / "summary.json"),
            "calibration_metric_audit": rel_path(args.output_dir / "calibration_metric_audit.csv"),
            "route_decision": rel_path(args.output_dir / "route_decision.csv"),
            "scope_decision": rel_path(args.output_dir / "scope_decision.csv"),
            "next_plan": rel_path(args.output_dir / "next_plan.json"),
            "report": rel_path(args.output_dir / "report.md"),
            "validation_errors": rel_path(args.output_dir / "validation_errors.jsonl"),
        },
    }

    write_json(args.output_dir / "summary.json", summary)
    write_csv(args.output_dir / "calibration_metric_audit.csv", calibration_rows)
    write_jsonl(args.output_dir / "calibration_metric_audit.jsonl", calibration_rows)
    write_csv(args.output_dir / "route_decision.csv", routes)
    write_jsonl(args.output_dir / "route_decision.jsonl", routes)
    write_csv(args.output_dir / "scope_decision.csv", scope)
    write_jsonl(args.output_dir / "scope_decision.jsonl", scope)
    write_json(args.output_dir / "next_plan.json", plan)
    write_jsonl(args.output_dir / "validation_errors.jsonl", errors)
    write_report(args.output_dir / "report.md", summary, calibration_rows, routes, scope)

    primary = summary["calibration_metric_audit"]["primary_model"]
    print(
        "status={status} selected={selected} legacy_ece={legacy} probability_ece={prob} next={next_todo}".format(
            status=summary["status"],
            selected=summary["selected_path"],
            legacy=primary["legacy_runner_ece_10"],
            prob=primary["probability_ece_10"],
            next_todo=summary["next_todo"],
        )
    )


if __name__ == "__main__":
    main()
