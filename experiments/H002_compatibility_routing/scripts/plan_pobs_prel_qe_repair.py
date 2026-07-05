#!/usr/bin/env python3
"""Plan Q_e repair after H002 p_obs observability failure."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_pobs_prel_qe_repair_plan_v1"
STATUS_READY = "h002_pobs_prel_qe_repair_plan_ready"
STATUS_ERROR = "h002_pobs_prel_qe_repair_plan_errors"
EXPECTED_REVIEW_STATUS = "h002_pobs_prel_observability_metric_result_review_ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--review-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def repo_rel(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def build_report(summary: dict[str, Any], schema_rows: list[dict[str, Any]], gates: list[dict[str, Any]]) -> str:
    metrics = summary["source_review_metrics"]
    lines = [
        "# Q_e Repair Plan",
        "",
        "## Why This Repair Is Needed",
        "",
        "The p_obs failure is not a posterior-combination failure. It is a Q_e representation failure: the hidden labels distinguish observable, ambiguous, and missing-evidence rows, while the model-safe Q_e view still marks every label group as sufficient.",
        "",
        "```text",
        f"p_obs_AUROC = {metrics['p_obs_auroc']:.6f}",
        f"p_rel_AUROC = {metrics['p_rel_auroc']:.6f}",
        f"decision_macro_F1 = {metrics['decision_macro_F1']:.6f}",
        "```",
        "",
        "## Repaired Q_e Schema",
        "",
        "| Block | Purpose | Examples |",
        "| --- | --- | --- |",
    ]
    for row in schema_rows:
        lines.append(f"| {row['feature_block']} | {row['purpose']} | {row['example_features']} |")
    lines.extend(
        [
            "",
            "## Pass / Fail Gates",
            "",
            "| Gate | Threshold | Reason |",
            "| --- | --- | --- |",
        ]
    )
    for row in gates:
        lines.append(f"| {row['gate']} | {row['threshold']} | {row['reason']} |")
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "`pobs_prel_qe_repair_materialization` should build a repaired Q_e v2 view and a balanced p_obs train/eval protocol before any new p_obs/p_rel solved-claim attempt.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    review_dir = resolve(repo_root, args.review_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    review = read_json(review_dir / "summary.json")
    qe_gap = read_csv(review_dir / "qe_feature_gap.csv")
    review_decision = review.get("review_decision", {})
    metrics = review.get("primary_metrics", {})

    if review.get("status") != EXPECTED_REVIEW_STATUS:
        errors.append({"error": "unexpected_review_status", "actual": review.get("status")})
    if review.get("validation_errors") != 0:
        errors.append({"error": "review_validation_errors", "actual": review.get("validation_errors")})
    if review_decision.get("p_obs_status") != "failed_observability_gate":
        errors.append({"error": "p_obs_failure_not_confirmed", "actual": review_decision.get("p_obs_status")})
    if review_decision.get("selected_next_step") != "qe_feature_repair_before_any_new_pobs_prel_claim":
        errors.append({"error": "unexpected_next_step", "actual": review_decision.get("selected_next_step")})

    schema_rows = [
        {
            "feature_block": "Q_e_asset_availability",
            "purpose": "distinguish missing evidence from usable evidence",
            "allowed_inputs": "scan assets, semseg/mesh/point availability, OBB availability, contact-surface availability",
            "example_features": "has_mesh, has_point_pair_crop, has_contact_surface_proxy, subject_has_obb, object_has_obb",
            "blocked_inputs": "observability_label, decision_label, rel_label, source score, rank, p_geom_valid",
        },
        {
            "feature_block": "Q_e_visual_coverage",
            "purpose": "separate observable_clear from no-view or low-quality visual evidence",
            "allowed_inputs": "view/crop metadata and co-visibility counts",
            "example_features": "co_visible_view_count, min_crop_quality, subject_visible_ratio, object_visible_ratio, occlusion_proxy",
            "blocked_inputs": "human label, GT match, source rank",
        },
        {
            "feature_block": "Q_e_geometry_quality",
            "purpose": "measure whether geometry can support the target route decision",
            "allowed_inputs": "geometry availability and quality only, not relation correctness",
            "example_features": "geometry_feature_coverage, surface_patch_available, local_point_density_near_contact, normal_available",
            "blocked_inputs": "predicate correctness, relation accept/reject label",
        },
        {
            "feature_block": "Q_e_ambiguity",
            "purpose": "represent ambiguity even when geometry exists",
            "allowed_inputs": "route-local ambiguity proxies independent of final label",
            "example_features": "support_subtype_candidate_count, standing_lying_pose_conflict, class_pair_subtype_entropy, competing_predicate_count",
            "blocked_inputs": "abstain label, codex seed hint, hidden queue kind as model input",
        },
        {
            "feature_block": "Q_e_state_v2",
            "purpose": "replace the static sufficient-only state",
            "allowed_inputs": "computed Q_e asset/visual/geometry/ambiguity blocks",
            "example_features": "q_e_state_sufficient_v2, q_e_state_limited_v2, q_e_state_ambiguous_v2, q_e_state_missing_v2",
            "blocked_inputs": "direct copy of observability_label",
        },
    ]

    materialization_rows = [
        {
            "artifact": "model_safe_qe_v2_train.jsonl",
            "split": "internal_train",
            "role": "train p_obs only",
            "source": "existing internal rows plus repaired support/contact ambiguity proxies",
            "requirement": "balanced observable_clear / ambiguous / missing-style rows without using official eval labels",
        },
        {
            "artifact": "model_safe_qe_v2_eval.jsonl",
            "split": "official_validation_diagnostic_subset",
            "role": "evaluate p_obs repair",
            "source": "265 user-confirmed observability subset",
            "requirement": "same candidate IDs as current metric subset, but Q_e v2 states must reflect coverage/ambiguity features",
        },
        {
            "artifact": "hidden_observability_v2_labels.jsonl",
            "split": "train/eval",
            "role": "hidden labels",
            "source": "train labels from repaired protocol, eval labels from user-confirmed subset",
            "requirement": "never included in model-safe views",
        },
        {
            "artifact": "qe_v2_schema_audit/latest",
            "split": "all",
            "role": "leakage audit",
            "source": "model-safe and hidden views",
            "requirement": "blocked field hits = 0; no direct label copy in Q_e v2",
        },
    ]

    eval_rows = [
        {
            "stage": "p_obs_only_repair_smoke",
            "train": "model_safe_qe_v2_train.jsonl",
            "eval": "model_safe_qe_v2_eval.jsonl",
            "metrics": "p_obs AUROC, ECE, abstain precision/recall, coverage-risk",
            "purpose": "confirm Q_e repair before touching p_rel or final decision head",
        },
        {
            "stage": "missing_and_ambiguity_controls",
            "train": "same as p_obs_only_repair_smoke",
            "eval": "no-view, low-visibility, missing-mesh, pose-ambiguity, shuffled-view controls",
            "metrics": "p_obs drop, abstain rate, false-observable rate",
            "purpose": "ensure p_obs is not just memorizing route family",
        },
        {
            "stage": "selective_decision_rerun",
            "train": "frozen p_rel plus repaired p_obs",
            "eval": "265-row user-confirmed subset",
            "metrics": "decision macro-F1, AURC, accept/reject/abstain confusion",
            "purpose": "only after p_obs-only gate passes",
        },
    ]

    gates = [
        {
            "gate": "schema_separation",
            "threshold": "validation_errors=0 and blocked_field_hits=0",
            "reason": "Q_e v2 must not leak hidden observability labels",
        },
        {
            "gate": "qe_label_alignment",
            "threshold": "ambiguous/missing rows are not all q_e_sufficient_v2=1",
            "reason": "directly fixes the observed Q_e mismatch",
        },
        {
            "gate": "p_obs_signal",
            "threshold": "p_obs AUROC >= 0.70 on user-confirmed subset",
            "reason": "minimum evidence that observability is learnable",
        },
        {
            "gate": "abstain_behavior",
            "threshold": "ambiguous/missing abstain recall >= 0.70 and observable abstain false-positive <= 0.30",
            "reason": "p_obs must actually abstain on uncertain evidence",
        },
        {
            "gate": "calibration_sanity",
            "threshold": "p_obs ECE@10 <= 0.20 for diagnostic, <= 0.10 for paper promotion",
            "reason": "avoid claiming calibrated observability from uncalibrated scores",
        },
        {
            "gate": "paper_promotion",
            "threshold": "all diagnostic gates pass plus independently authored or clearly user-confirmed label provenance",
            "reason": "paper-level p_obs/p_rel solved claim requires more than diagnostic rerun",
        },
    ]

    implementation_steps = [
        {
            "step": 1,
            "todo": "pobs_prel_qe_repair_materialization",
            "action": "materialize Q_e v2 train/eval views with asset, visual, geometry-quality, and ambiguity blocks",
            "output_root": "experiments/H002_compatibility_routing/pobs_prel_qe_repair_materialization/latest",
        },
        {
            "step": 2,
            "todo": "pobs_prel_qe_repair_schema_audit",
            "action": "audit Q_e v2 model-safe/hidden separation and feature-label alignment",
            "output_root": "experiments/H002_compatibility_routing/pobs_prel_qe_repair_schema_audit/latest",
        },
        {
            "step": 3,
            "todo": "pobs_prel_qe_repair_pobs_only_metric",
            "action": "run p_obs-only diagnostic metric before rerunning p_rel or full selective decision",
            "output_root": "experiments/H002_compatibility_routing/pobs_prel_qe_repair_evaluation/latest",
        },
        {
            "step": 4,
            "todo": "pobs_prel_qe_repair_result_review",
            "action": "decide whether Q_e repair is sufficient for selective-decision rerun",
            "output_root": "experiments/H002_compatibility_routing/pobs_prel_qe_repair_review/latest",
        },
    ]

    paper_boundary = [
        {
            "claim": "p_rel diagnostic signal exists",
            "status": "keep_allowed",
            "condition": "report only as diagnostic, not calibrated solved result",
        },
        {
            "claim": "p_obs / abstention is solved",
            "status": "blocked_until_qe_repair_passes",
            "condition": "requires p_obs AUROC/abstain behavior gates",
        },
        {
            "claim": "p_obs/p_rel as main paper quantitative result",
            "status": "blocked",
            "condition": "requires repaired Q_e, calibrated metrics, and stronger label provenance",
        },
        {
            "claim": "H002 includes selective-decision framework",
            "status": "allowed_as_framework_component",
            "condition": "must disclose p_obs repair is ongoing",
        },
    ]

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_artifacts": {
            "metric_review": repo_rel(repo_root, review_dir),
        },
        "source_review_metrics": {
            "p_obs_auroc": float(metrics.get("p_obs_auroc", 0.0)),
            "p_obs_ece_10": float(metrics.get("p_obs_ece_10", 0.0)),
            "p_rel_auroc": float(metrics.get("p_rel_auroc", 0.0)),
            "p_rel_ece_10": float(metrics.get("p_rel_ece_10", 0.0)),
            "decision_macro_F1": float(metrics.get("decision_macro_F1", 0.0)),
        },
        "failure_cause": {
            "type": "qe_feature_label_mismatch",
            "ambiguous_rows_marked_sufficient": next((int(row["q_e_sufficient_rows"]) for row in qe_gap if row["observability_label"] == "ambiguous_evidence"), 0),
            "missing_rows_marked_sufficient": next((int(row["q_e_sufficient_rows"]) for row in qe_gap if row["observability_label"] == "unobservable_missing_evidence"), 0),
        },
        "decision": {
            "selected_path": "repair_qe_before_any_new_pobs_prel_claim",
            "pobs_prel_solved_claim_allowed": False,
            "p_rel_diagnostic_signal_allowed": True,
            "next_todo": "pobs_prel_qe_repair_materialization",
        },
        "outputs": {
            "qe_schema_v2": repo_rel(repo_root, out / "qe_schema_v2.csv"),
            "materialization_contract": repo_rel(repo_root, out / "materialization_contract.csv"),
            "evaluation_protocol": repo_rel(repo_root, out / "evaluation_protocol.csv"),
            "pass_fail_gates": repo_rel(repo_root, out / "pass_fail_gates.csv"),
            "implementation_steps": repo_rel(repo_root, out / "implementation_steps.csv"),
            "paper_boundary": repo_rel(repo_root, out / "paper_boundary.csv"),
            "report": repo_rel(repo_root, out / "report.md"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
        },
        "validation_errors": len(errors),
    }

    write_csv(out / "qe_schema_v2.csv", schema_rows, ["feature_block", "purpose", "allowed_inputs", "example_features", "blocked_inputs"])
    write_csv(out / "materialization_contract.csv", materialization_rows, ["artifact", "split", "role", "source", "requirement"])
    write_csv(out / "evaluation_protocol.csv", eval_rows, ["stage", "train", "eval", "metrics", "purpose"])
    write_csv(out / "pass_fail_gates.csv", gates, ["gate", "threshold", "reason"])
    write_csv(out / "implementation_steps.csv", implementation_steps, ["step", "todo", "action", "output_root"])
    write_csv(out / "paper_boundary.csv", paper_boundary, ["claim", "status", "condition"])
    write_jsonl(out / "validation_errors.jsonl", errors)
    write_json(out / "summary.json", summary)
    (out / "report.md").write_text(build_report(summary, schema_rows, gates), encoding="utf-8")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
