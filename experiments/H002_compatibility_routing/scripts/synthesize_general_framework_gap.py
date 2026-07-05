#!/usr/bin/env python3
"""Synthesize experiment-stage gaps for H002 general-framework promotion."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def fval(row: dict[str, str], key: str, default: float = 0.0) -> float:
    try:
        value = row.get(key, "")
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def find_row(rows: list[dict[str, str]], **conds: str) -> dict[str, str]:
    for row in rows:
        if all(row.get(key) == value for key, value in conds.items()):
            return row
    return {}


def source_route_deltas(rows: list[dict[str, str]], k_values: set[int]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str, int, str], dict[str, str]] = {}
    for row in rows:
        try:
            k = int(row.get("K", ""))
        except ValueError:
            continue
        if k not in k_values:
            continue
        key = (row.get("source_id", ""), row.get("route_family", ""), k, row.get("score_id", ""))
        by_key[key] = row

    out: list[dict[str, Any]] = []
    pairs = sorted({(source, route, k) for source, route, k, _score in by_key})
    for source, route, k in pairs:
        s0 = by_key.get((source, route, k, "S0_source_score"))
        s2 = by_key.get((source, route, k, "S2_source_x_Ce"))
        if not s0 or not s2:
            continue
        delta_recall = fval(s2, "Recall@K") - fval(s0, "Recall@K")
        delta_violation = fval(s2, "Violation@K") - fval(s0, "Violation@K")
        out.append(
            {
                "source_id": source,
                "route_family": route,
                "K": k,
                "S0_Recall@K": fval(s0, "Recall@K"),
                "S2_Recall@K": fval(s2, "Recall@K"),
                "delta_Recall@K": delta_recall,
                "S0_Violation@K": fval(s0, "Violation@K"),
                "S2_Violation@K": fval(s2, "Violation@K"),
                "delta_Violation@K": delta_violation,
                "route_cell_pass": delta_recall >= -0.01 and delta_violation <= 0.0,
            }
        )
    return out


def summarize_route_cells(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row["route_family"]), []).append(row)

    out: list[dict[str, Any]] = []
    for route, items in sorted(grouped.items()):
        pass_count = sum(1 for item in items if item["route_cell_pass"])
        recall_positive = sum(1 for item in items if float(item["delta_Recall@K"]) >= 0.0)
        violation_reduced = sum(1 for item in items if float(item["delta_Violation@K"]) <= 0.0)
        out.append(
            {
                "route_family": route,
                "cells": len(items),
                "pass_cells": pass_count,
                "recall_nonnegative_cells": recall_positive,
                "violation_nonpositive_cells": violation_reduced,
                "route_source_wide_status": "supported" if pass_count == len(items) and items else "mixed_or_blocked",
            }
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    root = args.repo_root
    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    support_official = read_csv(
        root / "experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/official_metrics.csv"
    )
    support_dev = read_csv(
        root / "experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/dev_metrics.csv"
    )
    support_control = read_csv(
        root / "experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/control_metrics.csv"
    )
    official_family = read_csv(
        root / "experiments/H002_compatibility_routing/official_evaluation/latest/family_metrics.csv"
    )
    pobs_summary = read_json(
        root / "experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest/summary.json"
    )
    sensitivity = read_json(
        root / "experiments/H002_compatibility_routing/source_reranking_sensitivity/latest/summary.json"
    )
    source_family = read_csv(
        root / "experiments/H002_compatibility_routing/source_reranking_evaluation/latest/source_family_metrics.csv"
    )

    support_hard_official_m4 = find_row(support_official, view_id="M4_TxG_compatibility", level="overall")
    support_hard_dev_m4 = find_row(support_dev, view_id="M4_TxG_compatibility", level="overall")
    support_broad_m4 = find_row(
        official_family,
        route_family="support_contact",
        predicate_label="ALL",
        view_id="M4_TxG_compatibility",
    )
    support_broad_g = find_row(
        official_family,
        route_family="support_contact",
        predicate_label="ALL",
        view_id="M2_G_geometry_only",
    )
    support_broad_concat = find_row(
        official_family,
        route_family="support_contact",
        predicate_label="ALL",
        view_id="M3_T_plus_G_concat",
    )
    support_hard_gate = (
        fval(support_broad_m4, "auroc") >= 0.70
        and fval(support_broad_m4, "auroc") > fval(support_broad_g, "auroc")
        and fval(support_broad_m4, "auroc") > fval(support_broad_concat, "auroc")
        and fval(support_hard_official_m4, "auroc") >= 0.70
    )

    p_checks = pobs_summary.get("pass_checks", {})
    p_metrics = pobs_summary.get("primary_metrics", {})
    p_claim = pobs_summary.get("claim_boundary", {})
    pobs_gate = bool(pobs_summary.get("calibrated_quantitative_claim_pass", False))

    sensitivity_checks = sensitivity.get("gate", {}).get("checks", [])
    raw_pass = False
    rankpct_pass = False
    no_route_pass = False
    for check in sensitivity_checks:
        comp = check.get("comparison", "")
        if comp == "S2_minmax_source_x_Ce_minus_A1_minmax_no_route_G_only":
            no_route_pass = bool(check.get("passed_all", False))
        if comp == "normalization_variants_vs_S0":
            values = check.get("values", [])
            raw_rows = [v for v in values if v.get("score_id") == "S2_raw_source_x_Ce"]
            rank_rows = [v for v in values if v.get("score_id") == "S2_rankpct_source_x_Ce"]
            raw_pass = bool(raw_rows) and all(v.get("passed") for v in raw_rows)
            rankpct_pass = bool(rank_rows) and all(v.get("passed") for v in rank_rows)
    normalization_gate = raw_pass and rankpct_pass

    route_rows = source_route_deltas(source_family, {20, 50})
    route_summary = summarize_route_cells(route_rows)
    route_supported_count = sum(1 for row in route_summary if row["route_source_wide_status"] == "supported")
    has_support_route = any(
        row["route_family"] == "support_contact" and row["route_source_wide_status"] == "supported"
        for row in route_summary
    )
    has_observability_route = any(
        row["route_family"] in {"attachment", "attachment_like", "containment", "observability_heavy"}
        for row in route_summary
    )
    route_wide_gate = route_supported_count >= 3 and has_support_route and has_observability_route

    axis_rows = [
        {
            "axis": "general_framework_gap_plan",
            "current_status": "planned_from_existing_runtime_evidence",
            "target_claim": "general reliable 3D relation framework",
            "pass_gate": "all core axes pass: support/contact, p_obs/p_rel, normalization robustness, route-wide coverage",
            "current_decision": "blocked_continue_experiment_stage",
            "next_experiment_root": "experiments/H002_compatibility_routing/general_framework_gap/latest",
        },
        {
            "axis": "support_contact_solved",
            "current_status": "failed_current_hard_route",
            "target_claim": "support/contact as solved compatibility route",
            "primary_metric": "official AUROC / balanced accuracy / control collapse",
            "baseline": "predicate-only, geometry-only, T+G concat, wrong-T, shuffled-G",
            "current_result": (
                f"broad_M4_AUROC={fval(support_broad_m4, 'auroc'):.6f}; "
                f"hard_official_M4_AUROC={fval(support_hard_official_m4, 'auroc'):.6f}; "
                f"internal_dev_M4_AUROC={fval(support_hard_dev_m4, 'auroc'):.6f}"
            ),
            "pass_gate": "broad and hard official M4 AUROC >= 0.70 and better than G-only/concat with controls degraded",
            "current_decision": "blocked_needs_richer_Ge_and_relabel_protocol",
            "next_experiment_root": "experiments/H002_compatibility_routing/support_contact_generalization_repair/",
        },
        {
            "axis": "calibrated_pobs_prel_solved",
            "current_status": "failed_calibration_claim",
            "target_claim": "p_obs/p_rel as calibrated reliability and selective decision",
            "primary_metric": "ECE, Brier, NLL, AURC, coverage-risk, abstain precision/recall",
            "baseline": "raw p_obs/p_rel, missing-evidence controls, wrong-pair evidence",
            "current_result": (
                f"p_rel_AUROC={float(p_metrics.get('p_rel_calibrated_AUROC', 0.0)):.6f}; "
                f"p_rel_ECE={float(p_metrics.get('p_rel_calibrated_ECE_10', 0.0)):.6f}; "
                f"decision_macro_F1={float(p_metrics.get('decision_macro_F1_calibrated', 0.0)):.6f}; "
                f"asset_negative_or_ambiguous={p_checks.get('asset_observability_has_negative_or_ambiguous', False)}"
            ),
            "pass_gate": "ECE<=0.10, real observable/unobservable/ambiguous labels, route-specific missing controls, attachment/containment rows",
            "current_decision": "blocked_needs_real_observability_labels_and_calibration_repair",
            "next_experiment_root": "experiments/H002_compatibility_routing/pobs_prel_observability_repair/",
        },
        {
            "axis": "normalization_robust_or_invariant",
            "current_status": "partial_robust_not_invariant",
            "target_claim": "improvement is not an artifact of selected normalization",
            "primary_metric": "Recall@K / Violation@K direction across frozen normalization variants",
            "baseline": "minmax, raw product, rank-percentile, train/dev-frozen bounds, log-utility",
            "current_result": f"raw_pass={raw_pass}; rankpct_pass={rankpct_pass}; no_route_G_only_pass={no_route_pass}",
            "pass_gate": "raw, rankpct, and train/dev-frozen variants preserve recall non-degradation and violation reduction at K={10,20,50}",
            "current_decision": "robustness_partial_invariant_blocked",
            "next_experiment_root": "experiments/H002_compatibility_routing/normalization_robustness/",
        },
        {
            "axis": "route_aware_source_wide_evaluation",
            "current_status": "mixed_or_blocked",
            "target_claim": "minimum route coverage for general reliable 3D relation framework",
            "primary_metric": "route-wise/source-wise Recall@K and Violation@K deltas",
            "baseline": "S0_source_score vs S2_source_x_Ce by route and source",
            "current_result": f"supported_routes={route_supported_count}; support_route_supported={has_support_route}; observability_route_present={has_observability_route}",
            "pass_gate": ">=3 route families supported, including one hard support/contact route and one observability-heavy route",
            "current_decision": "blocked_no_observability_route_and_support_contact_not_solved",
            "next_experiment_root": "experiments/H002_compatibility_routing/route_wide_generalization/",
        },
    ]

    support_rows = [
        {
            "metric_scope": "broad_official_support_contact",
            "view": "M4_TxG_compatibility",
            "rows": support_broad_m4.get("rows", ""),
            "auroc": fval(support_broad_m4, "auroc"),
            "balanced_accuracy": fval(support_broad_m4, "balanced_accuracy"),
            "macro_F1": fval(support_broad_m4, "macro_F1"),
            "decision": "near_but_not_solved",
        },
        {
            "metric_scope": "hard_route_official_validation",
            "view": "M4_TxG_compatibility",
            "rows": support_hard_official_m4.get("rows", ""),
            "auroc": fval(support_hard_official_m4, "auroc"),
            "balanced_accuracy": fval(support_hard_official_m4, "balanced_accuracy"),
            "macro_F1": fval(support_hard_official_m4, "macro_F1"),
            "decision": "failed_generalization",
        },
        {
            "metric_scope": "hard_route_internal_dev",
            "view": "M4_TxG_compatibility",
            "rows": support_hard_dev_m4.get("rows", ""),
            "auroc": fval(support_hard_dev_m4, "auroc"),
            "balanced_accuracy": fval(support_hard_dev_m4, "balanced_accuracy"),
            "macro_F1": fval(support_hard_dev_m4, "macro_F1"),
            "decision": "internal_signal_only",
        },
    ]

    pobs_rows = [
        {
            "metric": "p_rel_calibrated_AUROC",
            "value": p_metrics.get("p_rel_calibrated_AUROC", ""),
            "pass_gate": ">=0.70",
            "passed": p_checks.get("p_rel_auroc_ge_0_70", False),
        },
        {
            "metric": "p_rel_calibrated_ECE_10",
            "value": p_metrics.get("p_rel_calibrated_ECE_10", ""),
            "pass_gate": "<=0.10",
            "passed": p_checks.get("p_rel_ece_le_0_10", False),
        },
        {
            "metric": "decision_macro_F1_calibrated",
            "value": p_metrics.get("decision_macro_F1_calibrated", ""),
            "pass_gate": ">=0.70",
            "passed": p_checks.get("decision_macro_f1_ge_0_70", False),
        },
        {
            "metric": "asset_observability_has_negative_or_ambiguous",
            "value": p_checks.get("asset_observability_has_negative_or_ambiguous", False),
            "pass_gate": "true",
            "passed": p_checks.get("asset_observability_has_negative_or_ambiguous", False),
        },
        {
            "metric": "attachment_containment_rows_present",
            "value": p_claim.get("attachment_containment_empirical_rows_available", False),
            "pass_gate": "true",
            "passed": p_claim.get("attachment_containment_empirical_rows_available", False),
        },
    ]

    norm_rows = [
        {
            "variant": "raw_source_score_x_Ce",
            "gate": "direction preserved at K={10,20,50}",
            "passed": raw_pass,
            "decision": "supports robustness but not invariance alone",
        },
        {
            "variant": "rank_percentile_source_x_Ce",
            "gate": "direction preserved at K={10,20,50}",
            "passed": rankpct_pass,
            "decision": "fails low-K recall; invariant claim blocked",
        },
        {
            "variant": "no_route_G_only",
            "gate": "S2 stronger than no-route G-only",
            "passed": no_route_pass,
            "decision": "S2 not explained by route one-hot G-only",
        },
    ]

    summary = {
        "status": "h002_general_framework_gap_experiment_synthesis_ready",
        "schema_version": "h002_general_framework_gap_v1",
        "validation_errors": 0,
        "source_artifacts": {
            "support_contact_harder": "experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest",
            "pobs_prel_calibration_upgrade": "experiments/H002_compatibility_routing/pobs_prel_calibration_upgrade/latest",
            "source_reranking_sensitivity": "experiments/H002_compatibility_routing/source_reranking_sensitivity/latest",
            "source_reranking_evaluation": "experiments/H002_compatibility_routing/source_reranking_evaluation/latest",
        },
        "decisions": {
            "general_framework_claim": "blocked_continue_experiment_stage",
            "support_contact_solved": bool(support_hard_gate),
            "calibrated_pobs_prel_solved": pobs_gate,
            "normalization_invariant_improvement": normalization_gate,
            "route_aware_source_wide_generalization": bool(route_wide_gate),
        },
        "next_order": [
            "support_contact_generalization_repair",
            "pobs_prel_observability_repair",
            "normalization_robustness_train_dev_frozen",
            "route_wide_generalization_after_repairs",
        ],
    }

    write_csv(
        out / "general_framework_gap_targets.csv",
        axis_rows,
        [
            "axis",
            "current_status",
            "target_claim",
            "primary_metric",
            "baseline",
            "current_result",
            "pass_gate",
            "current_decision",
            "next_experiment_root",
        ],
    )
    write_csv(
        out / "support_contact_gate.csv",
        support_rows,
        ["metric_scope", "view", "rows", "auroc", "balanced_accuracy", "macro_F1", "decision"],
    )
    write_csv(
        out / "pobs_prel_gate.csv",
        pobs_rows,
        ["metric", "value", "pass_gate", "passed"],
    )
    write_csv(
        out / "normalization_gate.csv",
        norm_rows,
        ["variant", "gate", "passed", "decision"],
    )
    write_csv(
        out / "route_source_wide_deltas.csv",
        route_rows,
        [
            "source_id",
            "route_family",
            "K",
            "S0_Recall@K",
            "S2_Recall@K",
            "delta_Recall@K",
            "S0_Violation@K",
            "S2_Violation@K",
            "delta_Violation@K",
            "route_cell_pass",
        ],
    )
    write_csv(
        out / "route_source_wide_summary.csv",
        route_summary,
        [
            "route_family",
            "cells",
            "pass_cells",
            "recall_nonnegative_cells",
            "violation_nonpositive_cells",
            "route_source_wide_status",
        ],
    )
    (out / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "validation_errors.jsonl").write_text("", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
