#!/usr/bin/env python3
"""Review remaining H002 experiment-stage gaps after the A1/A2 ablation review."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STAGE = "h002_experiment_stage_remaining_gap_review_after_ablation_result_review"
STATUS_READY = f"{STAGE}_ready"
ARTIFACT = f"compatibility_dataset_v3_{STAGE}"
H2 = Path("hypothesis/CAND-001/H002_factorized-relation-confidence")
EXP = Path("experiments/H002_compatibility_routing")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
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
        fields = ["empty"]
        rows = [{"empty": ""}]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def f6(value: str | float | None) -> str:
    if value in (None, ""):
        return ""
    return f"{float(value):.6f}"


def metric_lookup(rows: list[dict[str, str]], score: str, k: int) -> dict[str, str]:
    for row in rows:
        if row.get("score_id") == score and int(row.get("K", -1)) == k:
            return row
    return {}


def delta_lookup(rows: list[dict[str, str]], comparison: str, metric: str, k: int) -> dict[str, str]:
    for row in rows:
        if row.get("comparison") == comparison and row.get("metric") == metric and int(row.get("K", -1)) == k:
            return row
    return {}


def main() -> int:
    repo = Path.cwd()
    out = H2 / "artifacts" / ARTIFACT
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []

    required_json = {
        "ablation_review": H2
        / "artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation/summary.json",
        "ablation_implementation": H2
        / "artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_implementation_after_plan/summary.json",
        "schema_audit": EXP / "source_reranking_schema_audit/latest/summary.json",
        "pobs_prel_calibration": H2
        / "artifacts/compatibility_dataset_v3_pobs_prel_calibration_upgrade_result_review_after_runner/summary.json",
    }
    summaries: dict[str, dict[str, Any]] = {}
    for key, path in required_json.items():
        if not path.exists():
            errors.append({"error_type": "missing_required_summary", "key": key, "path": str(path)})
        else:
            summaries[key] = read_json(path)

    metric_dir = EXP / "source_reranking_evaluation/latest"
    ci_dir = EXP / "source_reranking_ci/latest"
    required_csv = {
        "absolute_primary_metrics": metric_dir / "absolute_primary_metrics.csv",
        "control_metrics": metric_dir / "control_metrics.csv",
        "main_delta_ci": ci_dir / "main_reranking_delta_ci.csv",
    }
    csv_rows: dict[str, list[dict[str, str]]] = {}
    for key, path in required_csv.items():
        if not path.exists():
            errors.append({"error_type": "missing_required_csv", "key": key, "path": str(path)})
        else:
            csv_rows[key] = read_csv(path)

    for key, summary in summaries.items():
        if summary.get("validation_errors") not in (0, [], None):
            errors.append({"error_type": "upstream_validation_errors", "key": key, "actual": summary.get("validation_errors")})

    absolute = csv_rows.get("absolute_primary_metrics", [])
    delta_ci = csv_rows.get("main_delta_ci", [])
    key_metrics = []
    for score in ["S0_source_score", "A1_source_x_G_only", "A2_source_x_TG_concat", "S2_source_x_Ce"]:
        row = metric_lookup(absolute, score, 20)
        if row:
            key_metrics.append(
                {
                    "scope": "primary_success_weighted",
                    "score_id": score,
                    "K": 20,
                    "Recall@K": f6(row.get("Recall@K")),
                    "Violation@K": f6(row.get("Violation@K")),
                }
            )
    for comparison in ["S2_source_x_Ce_minus_S0_source_score", "S2_source_x_Ce_minus_A1_source_x_G_only", "S2_source_x_Ce_minus_A2_source_x_TG_concat"]:
        for metric in ["Recall@K", "Violation@K"]:
            row = delta_lookup(delta_ci, comparison, metric, 20)
            if row:
                key_metrics.append(
                    {
                        "scope": "primary_success_weighted_delta_ci",
                        "score_id": comparison,
                        "K": 20,
                        "metric": metric,
                        "point_delta": f6(row.get("point_delta")),
                        "ci_low_95": f6(row.get("ci_low_95")),
                        "ci_high_95": f6(row.get("ci_high_95")),
                    }
                )

    claim_audit = [
        {
            "claim": "source confidence is not relation reliability",
            "status": "allowed_scoped",
            "evidence": "S2 beats S0 on primary comparison-route validation Recall@K/Violation@K, with CI for K=10/20/50.",
            "caveat": "Official 3DSSG validation split only; no leaderboard or official test claim.",
        },
        {
            "claim": "C_e captures predicate-geometry compatibility beyond geometry-only and plain concat",
            "status": "allowed_scoped",
            "evidence": "A1_source_x_G_only and A2_source_x_TG_concat are implemented; S2 beats both on aggregate primary comparison-route K=10/20/50.",
            "caveat": "Primary route is relative_vertical + size_relative; family-wise Recall is mixed.",
        },
        {
            "claim": "H002 is a general reliable 3D relation framework",
            "status": "framework_goal_not_completed_result",
            "evidence": "Route map exists; support/contact failure taxonomy and p_obs/p_rel boundary motivate route awareness.",
            "caveat": "Do not claim all-relation solved framework until hard/observability/semantic routes have independent evidence.",
        },
        {
            "claim": "p_obs/p_rel reliability is solved",
            "status": "blocked",
            "evidence": "Selective stress-test passed, but calibration-upgrade review has calibrated_quantitative_claim_pass=false.",
            "caveat": "p_rel calibration warning, synthetic missing-evidence controls, and missing attachment/containment rows block solved claim.",
        },
        {
            "claim": "support/contact is solved",
            "status": "blocked",
            "evidence": "Support/contact hard route transfers poorly and is retained as failure taxonomy.",
            "caveat": "Can be used to argue fixed fusion is insufficient, not as a success row.",
        },
    ]

    artifact_audit = [
        {
            "artifact": "source reranking materialization/schema audit",
            "status": "ready",
            "path": str(EXP / "source_reranking_schema_audit/latest"),
            "judgment": "blocked-field hit check passed; source/compatibility/hidden views are separated.",
        },
        {
            "artifact": "source reranking metric and CI",
            "status": "ready",
            "path": str(metric_dir),
            "judgment": "Docker runtime produced S0/S1/S2/S3/control/A1/A2 metrics and bootstrap CI.",
        },
        {
            "artifact": "A1/A2 ablation result review",
            "status": "ready",
            "path": str(H2 / "artifacts/compatibility_dataset_v3_h002_source_reranking_ablation_expansion_result_review_after_implementation"),
            "judgment": "Interpretation is fixed as aggregate primary-route support with family-wise caveat.",
        },
        {
            "artifact": "p_obs/p_rel calibration upgrade",
            "status": "boundary_ready_not_claim_ready",
            "path": str(EXP / "pobs_prel_calibration_upgrade/latest"),
            "judgment": "Framework component is allowed; calibrated quantitative result claim remains blocked.",
        },
        {
            "artifact": "H002 paper workspace",
            "status": "draft_workspace_ready",
            "path": "paper/h002_compatibility_routing/",
            "judgment": "Workspace exists, but new experiment outputs must stay in experiment review before final paper wording.",
        },
    ]

    score_process_audit = [
        {
            "step": "C_e scorer",
            "definition": "C_e = compatibility(T_e, G_e)",
            "current_implementation": "fit on internal_train; validation rows eval-only; Z_e excluded from C_e input.",
            "risk": "G_e includes route_family one-hot, so it is predicate-label-free but not route-agnostic.",
            "required_wording": "predicate/source-score-independent geometry evidence, not universal predicate-agnostic geometry.",
        },
        {
            "step": "S2 score",
            "definition": "S2 = normalized_source_score(Z_e) * normalized_C_e",
            "current_implementation": "source score per-source minmax; C_e per-source-family minmax; lambda fixed to 1 product.",
            "risk": "normalization uses evaluation candidate bounds, which is label-free but should be described and sensitivity-tested.",
            "required_wording": "frozen label-free candidate-pool normalization; no validation label tuning.",
        },
        {
            "step": "A1 geometry-only ablation",
            "definition": "A1 = normalized_source_score(Z_e) * normalized_G_only",
            "current_implementation": "G_only model uses common geometry features and route_family one-hot.",
            "risk": "If called pure geometry-only without caveat, reviewer can object.",
            "required_wording": "route-aware geometry-only ablation.",
        },
        {
            "step": "A2 concat ablation",
            "definition": "A2 = normalized_source_score(Z_e) * normalized_T_plus_G_concat",
            "current_implementation": "tests whether plain T/G concatenation explains gains.",
            "risk": "Still a simple logistic baseline, not a deep fusion SOTA.",
            "required_wording": "plain factor concatenation baseline.",
        },
        {
            "step": "Violation@K",
            "definition": "geometry-violating selected relations divided by violation-checkable selected relations",
            "current_implementation": "custom H002 metric; support_contact excluded from success aggregation.",
            "risk": "Not official 3DSSG metric; must not replace Recall@K.",
            "required_wording": "custom geometry-consistency diagnostic reported with Recall@K.",
        },
    ]

    novelty_threats = [
        {
            "threat": "RelWitness-style visual-geometric relation witnesses",
            "severity": "high",
            "primary_source": "RelWitness, arXiv:2605.20823v1, 2026",
            "why_it_threatens": "It explicitly defines relation-family visual-geometric witnesses, observability, and missing-relation audit.",
            "h002_defense": "H002 should claim source-agnostic compatibility reranking with Z_e/C_e separation and validation Recall-Violation tradeoff, not witness construction novelty.",
            "required_action": "Add side-by-side comparison: RelWitness = open-vocabulary generation/supervision; H002 = post-source reliability/reranking and factor-isolated controls.",
        },
        {
            "threat": "VL-SAT already combines 2D/language/3D semantics for 3DSSG",
            "severity": "medium",
            "primary_source": "VL-SAT, CVPR 2023 / arXiv:2303.14408",
            "why_it_threatens": "It improves 3DSSG prediction with visual-linguistic semantics and 3D geometry.",
            "h002_defense": "H002 is not a predictor replacement; it audits/reranks VL-SAT outputs and separates source score from compatibility.",
            "required_action": "Use VL-SAT as source baseline and avoid claiming a new 3DSSG predictor.",
        },
        {
            "threat": "Open3DSG open-vocabulary relation prediction",
            "severity": "medium",
            "primary_source": "Open3DSG, CVPR 2024 / arXiv:2402.12259",
            "why_it_threatens": "It predicts open-set relationships from point clouds using open-world language/model components.",
            "h002_defense": "H002 treats Open3DSG as a source and evaluates closed-vocabulary 3DSSG mapping; it does not claim open-set GT evaluation.",
            "required_action": "Keep open-vocabulary-source vs closed-vocabulary-metric wording in table captions.",
        },
        {
            "threat": "generic selective prediction / calibration",
            "severity": "medium",
            "primary_source": "SelectiveNet ICML 2019; Guo et al. ICML 2017 calibration",
            "why_it_threatens": "p_obs/p_rel, ECE, risk-coverage are known concepts.",
            "h002_defense": "Use them as reliability-interface tools, not as novelty; relation-specific Q_e and 3D relation route mapping are the domain contribution.",
            "required_action": "Do not claim calibrated reliability is solved until real observability labels and calibration pass.",
        },
        {
            "threat": "generic gated fusion / MoE / FiLM",
            "severity": "medium",
            "primary_source": "Sparsely-Gated MoE 2017; FiLM 2017",
            "why_it_threatens": "Adaptive factor routing is not novel by itself.",
            "h002_defense": "Novelty must be route-specific evidence definitions plus factor leakage controls in 3D relation reliability.",
            "required_action": "Frame router as design necessity, not contribution by itself.",
        },
        {
            "threat": "simple geometry reranking/filtering",
            "severity": "high",
            "primary_source": "methodological baseline threat",
            "why_it_threatens": "S2 product can look like source score multiplied by a geometry scalar.",
            "h002_defense": "A1 and A2 ablations show aggregate primary-route gains over route-aware geometry-only and plain concat; wrong-T/shuffled controls test alignment.",
            "required_action": "Make A1/A2/wrong-T/shuffled-G tables mandatory in main or near-main results.",
        },
    ]

    principled_problems = [
        {
            "problem": "validated relation scope is still narrow",
            "severity": "high",
            "current_state": "Main success is relative_vertical and size_relative; relative_horizontal/support/contact/proximity have caveats or non-main roles.",
            "why_it_matters": "Broad reliable 3D relation framework wording would overstate evidence.",
            "fix": "Use comparison-route claim now; add route-readiness table and put hard routes into limitation/failure taxonomy.",
        },
        {
            "problem": "G_e independence wording can be overstated",
            "severity": "medium_high",
            "current_state": "G_e excludes predicate label/source score but includes route_family one-hot in common_g_features.",
            "why_it_matters": "A reviewer can challenge predicate-independent geometry if route identity is in the geometry baseline.",
            "fix": "Rename as predicate-label/source-score-independent geometry evidence; add pure no-route G-only sensitivity if needed.",
        },
        {
            "problem": "validation candidate-bound normalization",
            "severity": "medium",
            "current_state": "source and model scores are minmax normalized per source/source-family on the eval candidate pool.",
            "why_it_matters": "It is label-free, but can be perceived as transductive or dataset-specific.",
            "fix": "Freeze wording; add sensitivity with train/dev bounds, rank-percentile normalization, and raw product/log utility.",
        },
        {
            "problem": "p_obs/p_rel calibration claim is blocked",
            "severity": "high",
            "current_state": "selective stress-test passed but calibrated_quantitative_claim_pass=false.",
            "why_it_matters": "p_obs/p_rel is in the framework; if presented as solved, claim contradicts evidence.",
            "fix": "Keep p_obs/p_rel as architecture/protocol or add real observability labels and recalibration before result claim.",
        },
        {
            "problem": "Violation@K is custom",
            "severity": "medium",
            "current_state": "Recall@K is standard-style; Violation@K is H002 geometry-consistency diagnostic.",
            "why_it_matters": "Reviewer may ask why the metric is valid and whether it hides recall tradeoff.",
            "fix": "Always report Recall@K and Violation@K together; include examples of counted violations.",
        },
        {
            "problem": "official test / SOTA boundary",
            "severity": "medium_high",
            "current_state": "3DSSG official validation GT is used; official test label/server claim is not available.",
            "why_it_matters": "Benchmark table wording can be attacked.",
            "fix": "Call it official validation split evaluation; do not use leaderboard/SOTA wording.",
        },
        {
            "problem": "support/contact fails as hard route",
            "severity": "medium_high",
            "current_state": "Hard-route result is failure taxonomy, not success.",
            "why_it_matters": "The broad route-aware framework needs hard relation evidence eventually.",
            "fix": "Use this as design-necessity evidence; future work needs richer point/mesh/contact/pose G_e and real Q_e.",
        },
    ]

    improvements = [
        {
            "priority": 1,
            "action": "Freeze paper claim to comparison-route compatibility reranking.",
            "stage": "paper_claim_boundary",
            "completion_criterion": "All paper tables/captions say validation-level comparison-route; all-relation/SOTA/support-contact-solved blocked.",
        },
        {
            "priority": 2,
            "action": "Add normalization sensitivity.",
            "stage": "experiment",
            "completion_criterion": "S2 advantage is checked under train-bound/rank-percentile/raw-log normalization or caveat is added.",
        },
        {
            "priority": 3,
            "action": "Add no-route G-only sensitivity or explicit caveat.",
            "stage": "experiment_or_wording",
            "completion_criterion": "Either route_family is removed in a G-only ablation, or paper calls A1 route-aware geometry-only.",
        },
        {
            "priority": 4,
            "action": "Generate qualitative success/failure examples for S2 vs S0/A1/A2.",
            "stage": "paper_support",
            "completion_criterion": "Examples show a retained GT/reduced violation case and a family-wise recall caveat case.",
        },
        {
            "priority": 5,
            "action": "Make related-work novelty map paper-facing.",
            "stage": "paper_support",
            "completion_criterion": "RelWitness/VL-SAT/Open3DSG/selective prediction/fusion threats have explicit comparison rows.",
        },
        {
            "priority": 6,
            "action": "Keep p_obs/p_rel as framework component unless real observability labels are added.",
            "stage": "method_boundary",
            "completion_criterion": "No calibrated p_obs/p_rel result claim; optional appendix stress-test only.",
        },
        {
            "priority": 7,
            "action": "Plan hard-route extension after current paper boundary.",
            "stage": "future_experiment",
            "completion_criterion": "support/contact or attachment gets richer G_e/Q_e with point/mesh/multiview evidence and independent labels.",
        },
    ]

    final_judgment = {
        "paper_claim_possible": True,
        "paper_claim_strength": "moderate_to_good_if_scoped",
        "standalone_top_tier_risk": "high_unless_claim_is_scoped_and_defended",
        "best_current_claim": "validation-level source reranking for geometry-checkable comparison relations using factor-isolated predicate-geometry compatibility",
        "blocked_broad_claim": "completed route-aware reliable 3D relation framework across all 3DSSG relation families",
        "promotion_decision": "hold_final_paper_promotion_until_normalization_and_wording_sensitivity_or_explicit_user_acceptance_of_scope",
    }

    report = f"""# H002 Experiment-Stage Remaining Gap Review

## Purpose

This review audits the current H002 claim, artifacts, result interpretation,
score construction, process, novelty threats, principled risks, and remaining
work after the A1/A2 ablation result review.

## Final Judgment

- Paper claim possible: `{final_judgment['paper_claim_possible']}`
- Claim strength: `{final_judgment['paper_claim_strength']}`
- Best current claim: {final_judgment['best_current_claim']}
- Blocked broad claim: {final_judgment['blocked_broad_claim']}
- Promotion decision: `{final_judgment['promotion_decision']}`

The result is defensible only if it is scoped as a validation-level,
comparison-route compatibility reranking result. It is not yet a solved
all-relation reliability framework.

## Key K=20 Evidence

| Scope | Score / Comparison | Metric | Recall@K | Violation@K | Delta | 95% CI |
| --- | --- | --- | ---: | ---: | ---: | --- |
"""
    for row in key_metrics:
        if row["scope"] == "primary_success_weighted":
            report += f"| {row['scope']} | `{row['score_id']}` | K={row['K']} | {row['Recall@K']} | {row['Violation@K']} |  |  |\n"
        else:
            report += (
                f"| {row['scope']} | `{row['score_id']}` | {row['metric']} K={row['K']} |  |  | "
                f"{row['point_delta']} | [{row['ci_low_95']}, {row['ci_high_95']}] |\n"
            )

    report += """
## Claim Audit

"""
    for row in claim_audit:
        report += f"- `{row['status']}` {row['claim']}: {row['evidence']} Caveat: {row['caveat']}\n"

    report += """
## Score Construction Audit

"""
    for row in score_process_audit:
        report += f"- {row['step']}: {row['definition']}. Current: {row['current_implementation']} Risk: {row['risk']} Required wording: {row['required_wording']}\n"

    report += """
## Novelty Threats

"""
    for row in novelty_threats:
        report += f"- `{row['severity']}` {row['threat']} ({row['primary_source']}): {row['why_it_threatens']} Defense: {row['h002_defense']} Action: {row['required_action']}\n"

    report += """
## Principled Problems

"""
    for row in principled_problems:
        report += f"- `{row['severity']}` {row['problem']}: {row['current_state']} Why it matters: {row['why_it_matters']} Fix: {row['fix']}\n"

    report += """
## Additional Work

"""
    for row in improvements:
        report += f"{row['priority']}. {row['action']} Completion: {row['completion_criterion']}\n"

    report += """
## Source Notes

- RelWitness, arXiv:2605.20823v1, 2026: visual-geometric relation witnesses,
  observability, and missing-relation audit are direct novelty threats.
- VL-SAT, CVPR 2023 / arXiv:2303.14408: source model and predictor-side
  visual-linguistic/3D semantics baseline.
- Open3DSG, CVPR 2024 / arXiv:2402.12259: open-vocabulary relation source;
  H002 quantitative evaluation remains closed-vocabulary 3DSSG mapping.
- SelectiveNet / calibration / MoE / FiLM: broader methods that make
  selective decision, calibration, and adaptive routing non-novel by themselves.
"""

    summary = {
        "schema_version": f"{STAGE}_v1",
        "status": STATUS_READY if not errors else f"{STAGE}_errors",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "validation_errors": len(errors),
        "final_judgment": final_judgment,
        "key_metrics": key_metrics,
        "claim_audit_rows": len(claim_audit),
        "artifact_audit_rows": len(artifact_audit),
        "score_process_audit_rows": len(score_process_audit),
        "novelty_threat_rows": len(novelty_threats),
        "principled_problem_rows": len(principled_problems),
        "improvement_rows": len(improvements),
        "outputs": {
            "report": str(out / "report.md"),
            "claim_audit": str(out / "claim_audit.csv"),
            "artifact_audit": str(out / "artifact_audit.csv"),
            "score_process_audit": str(out / "score_process_audit.csv"),
            "novelty_threats": str(out / "novelty_threats.csv"),
            "principled_problems": str(out / "principled_problems.csv"),
            "improvement_plan": str(out / "improvement_plan.csv"),
        },
        "next_todo": "h002_experiment_stage_normalization_and_no_route_geometry_sensitivity_after_gap_review",
    }

    write_csv(out / "key_metrics.csv", key_metrics)
    write_csv(out / "claim_audit.csv", claim_audit)
    write_csv(out / "artifact_audit.csv", artifact_audit)
    write_csv(out / "score_process_audit.csv", score_process_audit)
    write_csv(out / "novelty_threats.csv", novelty_threats)
    write_csv(out / "principled_problems.csv", principled_problems)
    write_csv(out / "improvement_plan.csv", improvements)
    (out / "report.md").write_text(report, encoding="utf-8")
    write_json(out / "summary.json", summary)
    write_jsonl(out / "validation_errors.jsonl", errors)

    stage_doc = H2 / f"compatibility_dataset_v3_{STAGE}.md"
    stage_doc.write_text(
        f"""# {STAGE}

Artifact:

```text
{out}
```

Status: `{summary['status']}`

Validation errors: `{summary['validation_errors']}`

Decision:

```text
best_current_claim = {final_judgment['best_current_claim']}
blocked_broad_claim = {final_judgment['blocked_broad_claim']}
promotion_decision = {final_judgment['promotion_decision']}
next_todo = {summary['next_todo']}
```

See `{out / 'report.md'}` for the full claim/artifact/score/novelty/principle review.
""",
        encoding="utf-8",
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
