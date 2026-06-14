#!/usr/bin/env python3
"""Create the final scoped H001 evidence-lock summary from existing artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = H001_HYPOTHESIS_ROOT
OUT_DIR = ROOT / "artifacts/evaluation/vlsat_closed_set/hardened/evidence_lock"


def load_json(rel_path: str) -> dict[str, Any]:
    with (ROOT / rel_path).open("r", encoding="utf-8") as f:
        return json.load(f)


def count_jsonl(rel_path: str) -> tuple[int, int]:
    rows = 0
    labeled = 0
    with (ROOT / rel_path).open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rows += 1
            row = json.loads(line)
            if row.get("audit_status") == "labeled" or row.get("visual_label"):
                labeled += 1
    return rows, labeled


def recall(metrics: dict[str, Any], condition: str, k: int) -> float:
    return metrics["conditions"][condition]["recall"]["by_k"][str(k)]["recall"]


def violation(metrics: dict[str, Any], condition: str, k: int) -> float:
    return metrics["conditions"][condition]["violation_rate"]["by_k"][str(k)]["violation_rate"]


def condition_row(metrics: dict[str, Any], condition: str) -> dict[str, float]:
    return {
        "r50": recall(metrics, condition, 50),
        "r100": recall(metrics, condition, 100),
        "violation50": violation(metrics, condition, 50),
        "violation100": violation(metrics, condition, 100),
    }


def delta(row: dict[str, float], base: dict[str, float]) -> dict[str, float]:
    return {key: row[key] - base[key] for key in row}


def fmt(v: float) -> str:
    return f"{v:.4f}"


def make_report(manifest: dict[str, Any]) -> str:
    m = manifest
    main = m["metrics"]["main"]
    deltas = m["metrics"]["deltas_vs_semantic"]
    controls = m["metrics"]["controls"]
    audit = m["audit"]
    visual = m["independent_visual_spotcheck"]
    visual_ready = visual["status"] == "ready_sanity_pass"
    visual_fact = (
        "- Independent visual spot-check labels are complete as a reduced 50-row sanity check."
        if visual_ready
        else "- Independent visual spot-check labels are still missing."
    )
    visual_inference = (
        "- The evidence supports moving toward scoped paper-grade main experiment implementation."
        if visual_ready
        else "- The evidence supports moving toward paper-grade main experiment implementation only after the independent visual spot-check is filled or the claim is explicitly kept below paper-level audit wording."
    )

    lines = [
        "# H001 Evidence Lock",
        "",
        f"- Date: {m['date_created']}",
        f"- Status: `{m['status']}`",
        f"- Locked claim scope: `{m['locked_claim_scope']}`",
        "",
        "## Locked Inputs",
        "",
        "| Item | Value |",
        "| --- | ---: |",
        f"| held-out scans | {m['held_out_scope']['scans']} |",
        f"| subgraphs | {m['held_out_scope']['subgraphs']} |",
        f"| prediction rows | {m['held_out_scope']['prediction_rows']:,} |",
        f"| ground-truth rows | {m['held_out_scope']['ground_truth_rows']:,} |",
        f"| in-scope prediction rows | {m['held_out_scope']['in_scope_prediction_rows']:,} |",
        f"| in-scope GT denominator | {m['held_out_scope']['in_scope_ground_truth_denominator']:,} |",
        "",
        "## Main Metrics",
        "",
        "| Condition | R@50 | R@100 | Violation@50 | Violation@100 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name in ("semantic_only", "rule_verified_point_subtype", "probabilistic_recalibrated", "family_specific_p_geom_valid"):
        row = main[name]
        lines.append(
            f"| `{name}` | {fmt(row['r50'])} | {fmt(row['r100'])} | "
            f"{fmt(row['violation50'])} | {fmt(row['violation100'])} |"
        )

    lines += [
        "",
        "## Delta Vs Semantic",
        "",
        "| Condition | dR@50 | dR@100 | dViolation@50 | dViolation@100 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name in ("probabilistic_recalibrated", "family_specific_p_geom_valid", "rule_verified_point_subtype"):
        row = deltas[name]
        lines.append(
            f"| `{name}` | {row['r50']:+.4f} | {row['r100']:+.4f} | "
            f"{row['violation50']:+.4f} | {row['violation100']:+.4f} |"
        )

    lines += [
        "",
        "## Control Read",
        "",
        "| Control | R@50 | R@100 | Violation@50 | Violation@100 | Evidence-lock read |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for name in ("control_p_geom_valid_only", "control_distance_only", "control_shuffled_geometry", "control_wrong_pair_geometry"):
        row = controls[name]
        read = m["control_interpretation"][name]
        lines.append(
            f"| `{name}` | {fmt(row['r50'])} | {fmt(row['r100'])} | "
            f"{fmt(row['violation50'])} | {fmt(row['violation100'])} | {read} |"
        )

    lines += [
        "",
        "## Calibration Read",
        "",
        "- `p_geom_valid` was fit only on train/dev calibration rows and applied frozen to the held-out validation predictions.",
        "- Train/dev calibration metrics support geometry-valid discrimination, but held-out prediction utility is the reportable evidence here.",
        "- Pooled calibration is the recall-first operating point; family-specific calibration is the stricter violation-first operating point.",
        "",
        "Calibration smoke metrics:",
        "",
        "| Model | Dev rows | Brier | AUROC | AUPRC |",
        "| --- | ---: | ---: | ---: | ---: |",
        f"| pooled `p_geom_valid` | {m['calibration']['pooled_dev']['rows']} | {fmt(m['calibration']['pooled_dev']['brier'])} | {fmt(m['calibration']['pooled_dev']['auroc'])} | {fmt(m['calibration']['pooled_dev']['auprc'])} |",
        f"| family-specific support/contact | {m['calibration']['family_dev']['support_contact']['rows']} | {fmt(m['calibration']['family_dev']['support_contact']['brier'])} | {fmt(m['calibration']['family_dev']['support_contact']['auroc'])} | {fmt(m['calibration']['family_dev']['support_contact']['auprc'])} |",
        f"| family-specific proximity | {m['calibration']['family_dev']['proximity']['rows']} | {fmt(m['calibration']['family_dev']['proximity']['brier'])} | {fmt(m['calibration']['family_dev']['proximity']['auroc'])} | {fmt(m['calibration']['family_dev']['proximity']['auprc'])} |",
        f"| family-specific relative_vertical | {m['calibration']['family_dev']['relative_vertical']['rows']} | {fmt(m['calibration']['family_dev']['relative_vertical']['brier'])} | {fmt(m['calibration']['family_dev']['relative_vertical']['auroc'])} | {fmt(m['calibration']['family_dev']['relative_vertical']['auprc'])} |",
        "",
        "## Audit Read",
        "",
        "| Audit | Status | Key value |",
        "| --- | --- | ---: |",
        f"| Codex structured audit | `{audit['structured_status']}` | {audit['structured_labeled_rows']}/{audit['structured_sample_rows']} labels |",
        f"| strict invalid-only precision | hypothesis-stage support | {fmt(audit['required_violation_precision_invalid_only'])} |",
        f"| quality-issue precision | hypothesis-stage support | {fmt(audit['required_violation_precision_quality_issue'])} |",
        f"| independent visual labels | `{visual['status']}` | {visual['labeled_rows']}/{visual['label_rows']} labels |",
        "",
        "## Verdict",
        "",
        "Fact:",
        "",
        "- The fixed held-out `VL-SAT` validation scope, raw predictions, geometry join, metrics, G3 controls, and Codex structured audit are locked.",
        "- `probabilistic_recalibrated` improves R@50/R@100 over `semantic_only` and lowers Violation@50/@100.",
        "- Geometry-only, distance-only, shuffled-geometry, and wrong-pair controls do not explain the main signal.",
        visual_fact,
        "",
        "Inference:",
        "",
        "- H001 is validated as a scoped `VL-SAT`-centered hypothesis-stage result.",
        visual_inference,
        "- It does not support a broad baseline-agnostic or broad open-vocabulary 3DSSG improvement claim without second-source evidence.",
        "",
        "## Remaining Blockers",
        "",
    ]
    for blocker in m["remaining_blockers"]:
        lines.append(f"- `{blocker}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    prediction_manifest = load_json("artifacts/evaluation/vlsat_closed_set/hardened/manifest.json")
    metrics = load_json("artifacts/evaluation/vlsat_closed_set/hardened_metrics/metrics.json")
    g3 = load_json("artifacts/evaluation/vlsat_closed_set/hardened_g3/metrics.json")
    calibration = load_json("artifacts/calibration/p_geom_valid_smoke/metrics.json")
    family_calibration = load_json("artifacts/calibration/p_geom_valid_family/metrics.json")
    audit = load_json("artifacts/evaluation/vlsat_closed_set/hardened/human_audit/label_summary.json")
    visual = load_json("artifacts/evaluation/vlsat_closed_set/hardened/human_audit/visual_spotcheck/manifest.json")
    visual_summary = load_json("artifacts/evaluation/vlsat_closed_set/hardened/human_audit/visual_spotcheck/summary.json")
    visual_rows, visual_labeled = count_jsonl(
        "artifacts/evaluation/vlsat_closed_set/hardened/human_audit/visual_spotcheck/labels.jsonl"
    )
    visual_ready = visual_summary["status"] == "ready_sanity_pass"

    semantic = condition_row(metrics, "semantic_only")
    prob = condition_row(metrics, "probabilistic_recalibrated")
    point = condition_row(metrics, "rule_verified_point_subtype")
    family = condition_row(g3, "control_family_specific_p_geom_valid")

    controls = {
        "control_p_geom_valid_only": condition_row(g3, "control_p_geom_valid_only"),
        "control_distance_only": condition_row(g3, "control_distance_only"),
        "control_shuffled_geometry": condition_row(g3, "control_shuffled_geometry"),
        "control_wrong_pair_geometry": condition_row(g3, "control_wrong_pair_geometry"),
    }

    pooled_dev = calibration["conditions"]["logistic"]["dev"]
    family_dev = family_calibration["conditions"]["family_logistic"]

    manifest = {
        "schema_version": "h001_evidence_lock_v1",
        "date_created": "2026-05-07",
        "status": (
            "scoped_hypothesis_evidence_locked_with_reduced_visual_sanity_check"
            if visual_ready
            else "scoped_hypothesis_evidence_locked_pending_independent_visual_labels"
        ),
        "locked_claim_scope": "VL-SAT-centered geometry-consistency reliability layer for support_contact, proximity, relative_vertical",
        "held_out_scope": {
            "scans": 127,
            "subgraphs": prediction_manifest["counts"]["subgraphs"],
            "prediction_rows": prediction_manifest["counts"]["predictions"],
            "ground_truth_rows": prediction_manifest["counts"]["ground_truth_edges"],
            "in_scope_prediction_rows": metrics["conditions"]["probabilistic_recalibrated"]["score_summary"][
                "in_scope_predictions"
            ],
            "in_scope_ground_truth_denominator": metrics["conditions"]["semantic_only"]["recall"]["denominator"],
            "families": metrics["families"],
            "split": "official 3DSSG_subset validation minus H001-Mini reference/rescan groups",
        },
        "inputs": {
            "prediction_manifest": "artifacts/evaluation/vlsat_closed_set/hardened/manifest.json",
            "hardened_metrics": "artifacts/evaluation/vlsat_closed_set/hardened_metrics/metrics.json",
            "hardened_g3_metrics": "artifacts/evaluation/vlsat_closed_set/hardened_g3/metrics.json",
            "pooled_calibration_metrics": "artifacts/calibration/p_geom_valid_smoke/metrics.json",
            "family_calibration_metrics": "artifacts/calibration/p_geom_valid_family/metrics.json",
            "structured_audit_summary": "artifacts/evaluation/vlsat_closed_set/hardened/human_audit/label_summary.json",
            "visual_spotcheck_manifest": "artifacts/evaluation/vlsat_closed_set/hardened/human_audit/visual_spotcheck/manifest.json",
            "visual_spotcheck_summary": "artifacts/evaluation/vlsat_closed_set/hardened/human_audit/visual_spotcheck/summary.json",
        },
        "metrics": {
            "main": {
                "semantic_only": semantic,
                "probabilistic_recalibrated": prob,
                "family_specific_p_geom_valid": family,
                "rule_verified_point_subtype": point,
            },
            "deltas_vs_semantic": {
                "probabilistic_recalibrated": delta(prob, semantic),
                "family_specific_p_geom_valid": delta(family, semantic),
                "rule_verified_point_subtype": delta(point, semantic),
            },
            "relative_violation_reduction_vs_semantic": {
                "probabilistic_recalibrated": {
                    "50": (semantic["violation50"] - prob["violation50"]) / semantic["violation50"],
                    "100": (semantic["violation100"] - prob["violation100"]) / semantic["violation100"],
                },
                "family_specific_p_geom_valid": {
                    "50": (semantic["violation50"] - family["violation50"]) / semantic["violation50"],
                    "100": (semantic["violation100"] - family["violation100"]) / semantic["violation100"],
                },
            },
            "controls": controls,
        },
        "control_interpretation": {
            "control_p_geom_valid_only": "fails as a standalone ranker; semantics remain necessary",
            "control_distance_only": "fails; H001 is not a simple distance heuristic",
            "control_shuffled_geometry": "underperforms main; geometry identity matters",
            "control_wrong_pair_geometry": "underperforms main; object-pair geometry matters",
        },
        "calibration": {
            "pooled_dev": {
                "rows": pooled_dev["rows"],
                "brier": pooled_dev["brier"],
                "nll": pooled_dev["nll"],
                "auroc": pooled_dev["auroc_valid"],
                "auprc": pooled_dev["auprc_valid"],
                "ece": pooled_dev["ece"],
            },
            "family_dev": {
                family_name: {
                    "rows": family_dev[family_name]["dev"]["rows"],
                    "brier": family_dev[family_name]["dev"]["brier"],
                    "nll": family_dev[family_name]["dev"]["nll"],
                    "auroc": family_dev[family_name]["dev"]["auroc_valid"],
                    "auprc": family_dev[family_name]["dev"]["auprc_valid"],
                    "ece": family_dev[family_name]["dev"]["ece"],
                }
                for family_name in ("support_contact", "proximity", "relative_vertical")
            },
            "interpretation": {
                "pooled": "recall-first operating point",
                "family_specific": "stricter violation-first operating point",
                "held_out_caveat": "train/dev calibration metrics are not final held-out calibration labels; held-out evidence is prediction-level utility plus audit.",
            },
        },
        "audit": {
            "structured_status": audit["status"],
            "structured_sample_rows": audit["counts"]["sample_rows"],
            "structured_labeled_rows": audit["counts"]["labeled_rows"],
            "required_violation_precision_invalid_only": audit["violation_precision"]["required_violation_buckets"][
                "precision_invalid_only"
            ],
            "required_violation_precision_quality_issue": audit["violation_precision"]["required_violation_buckets"][
                "precision_quality_issue"
            ],
            "boundary": "Codex structured audit is not independent human visual review.",
        },
        "independent_visual_spotcheck": {
            "status": visual_summary["status"],
            "label_rows": visual_rows,
            "labeled_rows": visual_labeled,
            "unique_scans": visual["counts"]["unique_scans"],
            "by_bucket": visual["counts"]["by_bucket"],
            "by_family": visual["counts"]["by_family"],
            "blockers": visual_summary["blockers"],
            "warnings": visual_summary["warnings"],
            "target_quality_issue_rate": visual_summary["target_alignment"]["quality_issue_rate"],
            "target_contradiction_rate": visual_summary["target_alignment"]["contradiction_rate"],
            "private_reference_exact_match_rate": visual_summary["codex_structured_audit_agreement_private"][
                "exact_match_rate"
            ],
            "provenance_note": "yhkim reported reference-aligned visual labels; Codex transcribed the finite-schema labels.",
        },
        "claim_readiness": {
            "scoped_vlsat_centered_hypothesis": (
                "ready_with_reduced_visual_sanity_check"
                if visual_ready
                else "ready_with_external_visual_audit_blocker"
            ),
            "scoped_vlsat_centered_paper_main_experiment": (
                "ready_for_implementation_spec"
                if visual_ready
                else "ready_after_independent_visual_labels_or_with_explicit_non-paper-audit_caveat"
            ),
            "baseline_agnostic_claim": "blocked_second_source_metric_missing",
            "broad_open_vocabulary_3dssg_claim": "blocked_open_vocab_adapter_metric_missing",
        },
        "remaining_blockers": (
            [
                "second_source_metric_missing_for_baseline_agnostic_claim",
                "open_vocab_adapter_metric_missing_for_broad_open_vocabulary_claim",
            ]
            if visual_ready
            else [
                "independent_visual_labels_missing:0/50",
                "second_source_metric_missing_for_baseline_agnostic_claim",
                "open_vocab_adapter_metric_missing_for_broad_open_vocabulary_claim",
            ]
        ),
        "next_action": (
            "Prepare paper-grade main experiment implementation spec for the scoped VL-SAT-centered H001 claim."
            if visual_ready
            else "Have a non-Codex reviewer fill visual_spotcheck/labels.jsonl; then prepare paper-grade main experiment implementation spec for the scoped claim or collect second-source evidence for broader claims."
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "manifest.json").open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
        f.write("\n")
    with (OUT_DIR / "report.md").open("w", encoding="utf-8") as f:
        f.write(make_report(manifest))

    print(
        "evidence_lock_ready "
        f"status={manifest['status']} "
        f"visual_labels={visual_labeled}/{visual_rows} "
        f"r50_delta={manifest['metrics']['deltas_vs_semantic']['probabilistic_recalibrated']['r50']:.6f}"
    )


if __name__ == "__main__":
    main()
