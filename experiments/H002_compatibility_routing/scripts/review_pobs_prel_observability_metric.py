#!/usr/bin/env python3
"""Review H002 p_obs / p_rel observability diagnostic metric results."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_pobs_prel_observability_metric_review_v1"
STATUS_READY = "h002_pobs_prel_observability_metric_result_review_ready"
STATUS_ERROR = "h002_pobs_prel_observability_metric_result_review_errors"
EXPECTED_METRIC_STATUS = "h002_pobs_prel_observability_metric_ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--metric-dir", type=Path, required=True)
    parser.add_argument("--ingestion-dir", type=Path, required=True)
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


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


def fval(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        value = row.get(key, "")
        if value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def qe_alignment_rows(ingestion_dir: Path) -> list[dict[str, Any]]:
    qe_by_id = {row["candidate_id"]: row for row in read_jsonl(ingestion_dir / "model_safe_qe_view.jsonl")}
    hidden = read_jsonl(ingestion_dir / "hidden_observability_labels.jsonl")
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for label in hidden:
        q = (
            qe_by_id.get(label["candidate_id"], {})
            .get("feature_blocks", {})
            .get("Q_e", {})
            .get("Q_e_observability", {})
        )
        buckets[str(label.get("observability_label"))].append(
            {
                "q_e_state_code": q.get("q_e_state_code"),
                "q_e_state_sufficient": q.get("q_e_state_sufficient"),
                "q_e_state_uncertain": q.get("q_e_state_uncertain"),
                "q_e_state_limited": q.get("q_e_state_limited"),
            }
        )

    out: list[dict[str, Any]] = []
    for label, items in sorted(buckets.items()):
        rows = len(items)
        sufficient = sum(1 for item in items if item.get("q_e_state_sufficient") == 1)
        uncertain = sum(1 for item in items if item.get("q_e_state_uncertain") == 1)
        limited = sum(1 for item in items if item.get("q_e_state_limited") == 1)
        codes = Counter(str(item.get("q_e_state_code")) for item in items)
        out.append(
            {
                "observability_label": label,
                "rows": rows,
                "q_e_sufficient_rows": sufficient,
                "q_e_uncertain_rows": uncertain,
                "q_e_limited_rows": limited,
                "q_e_state_code_counts": dict(sorted(codes.items())),
                "feature_label_alignment": "mismatch" if label != "observable_clear" and sufficient == rows else "aligned_or_partial",
            }
        )
    return out


def build_report(summary: dict[str, Any], qe_gap: list[dict[str, Any]], repair_plan: list[dict[str, Any]]) -> str:
    metrics = summary["primary_metrics"]
    lines = [
        "# p_obs / p_rel Observability Metric Review",
        "",
        "## Decision",
        "",
        "The diagnostic rerun does not pass. `p_rel` has usable signal on user-confirmed observable rows, but `p_obs` fails to distinguish observable from ambiguous or missing evidence.",
        "",
        "```text",
        f"p_obs_AUROC = {metrics['p_obs_auroc']:.6f}",
        f"p_obs_ECE_10 = {metrics['p_obs_ece_10']:.6f}",
        f"p_rel_AUROC = {metrics['p_rel_auroc']:.6f}",
        f"p_rel_ECE_10 = {metrics['p_rel_ece_10']:.6f}",
        f"decision_macro_F1 = {metrics['decision_macro_F1']:.6f}",
        "diagnostic_metric_pass = false",
        "paper_promotion_pass = false",
        "```",
        "",
        "## Cause",
        "",
        "The failure is a `Q_e` feature/label mismatch. The hidden labels now include ambiguous and missing-evidence cases, but the model-safe `Q_e` view still marks every group as sufficient.",
        "",
        "| Label | Rows | Q_e Sufficient Rows | Alignment |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in qe_gap:
        lines.append(
            f"| {row['observability_label']} | {row['rows']} | {row['q_e_sufficient_rows']} | {row['feature_label_alignment']} |"
        )
    lines.extend(
        [
            "",
            "## Next Repair",
            "",
            "| Priority | Repair | Reason |",
            "| ---: | --- | --- |",
        ]
    )
    for row in repair_plan:
        lines.append(f"| {row['priority']} | {row['repair_item']} | {row['why_needed']} |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "`p_obs/p_rel` remains a framework component, not a solved calibrated reliability result. The next experiment should repair `Q_e` before any new p_obs/p_rel solved-claim attempt.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    metric_dir = resolve(repo_root, args.metric_dir)
    ingestion_dir = resolve(repo_root, args.ingestion_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    manifest = read_json(metric_dir / "metric_manifest.json")
    if manifest.get("status") != EXPECTED_METRIC_STATUS:
        errors.append({"error": "unexpected_metric_status", "actual": manifest.get("status")})
    if manifest.get("validation_errors") != 0:
        errors.append({"error": "metric_validation_errors", "actual": manifest.get("validation_errors")})

    pobs = read_csv(metric_dir / "pobs_metrics.csv")
    prel = read_csv(metric_dir / "prel_metrics.csv")
    decision = read_csv(metric_dir / "decision_metrics.csv")
    queue_metrics = read_csv(metric_dir / "queue_kind_metrics.csv")
    obs_metrics = read_csv(metric_dir / "observability_label_metrics.csv")
    qe_gap = qe_alignment_rows(ingestion_dir)

    pobs_row = pobs[0] if pobs else {}
    prel_row = prel[0] if prel else {}
    decision_row = decision[0] if decision else {}
    pobs_pass = fval(pobs_row, "auroc") >= 0.70
    prel_pass = fval(prel_row, "auroc") >= 0.70
    decision_pass = fval(decision_row, "macro_F1") >= 0.50
    qe_gap_present = any(row["feature_label_alignment"] == "mismatch" for row in qe_gap)

    review_rows = [
        {
            "component": "p_obs",
            "metric": "AUROC",
            "value": f"{fval(pobs_row, 'auroc'):.6f}",
            "pass": pobs_pass,
            "decision": "fail_keep_abstention_unsolved",
            "interpretation": "Q_e cannot separate observable_clear from ambiguous/missing evidence",
        },
        {
            "component": "p_rel",
            "metric": "AUROC",
            "value": f"{fval(prel_row, 'auroc'):.6f}",
            "pass": prel_pass,
            "decision": "keep_as_diagnostic_signal",
            "interpretation": "relation reliability signal exists on observable rows",
        },
        {
            "component": "selective_decision",
            "metric": "macro_F1",
            "value": f"{fval(decision_row, 'macro_F1'):.6f}",
            "pass": decision_pass,
            "decision": "fail_due_to_no_abstain_behavior",
            "interpretation": "p_obs never triggers abstain on ambiguous/missing evidence",
        },
    ]

    repair_plan = [
        {
            "priority": 1,
            "repair_item": "replace_static_Qe_state_with_audit_aligned_Qe_features",
            "why_needed": "current Q_e marks ambiguous/missing labels as sufficient",
            "expected_effect": "allow p_obs to learn abstention rather than always predict observable",
        },
        {
            "priority": 2,
            "repair_item": "add_visual_mesh_coverage_features",
            "why_needed": "observability requires view count, crop quality, mesh/contact surface availability, and occlusion signals",
            "expected_effect": "separate observable_clear from unobservable_missing_evidence",
        },
        {
            "priority": 3,
            "repair_item": "add_support_contact_pose_ambiguity_features",
            "why_needed": "most abstain rows are support/contact single-subtype ambiguity, not missing geometry",
            "expected_effect": "separate ambiguous_evidence from true observable binary rows",
        },
        {
            "priority": 4,
            "repair_item": "materialize_balanced_observability_train_rows",
            "why_needed": "current p_obs train protocol uses synthetic missing controls, while eval labels are user-confirmed ambiguity labels",
            "expected_effect": "reduce train/eval target mismatch for p_obs",
        },
        {
            "priority": 5,
            "repair_item": "rerun_pobs_only_before_full_prel_decision",
            "why_needed": "p_rel already has signal; p_obs is the bottleneck",
            "expected_effect": "avoid conflating reliability scoring with observability gating",
        },
    ]

    paper_boundary = [
        {
            "claim": "p_rel has diagnostic reliability signal on user-confirmed observable rows",
            "status": "allowed_diagnostic",
            "evidence": f"p_rel_AUROC={fval(prel_row, 'auroc'):.6f}; ECE_10={fval(prel_row, 'ECE_10'):.6f}",
        },
        {
            "claim": "p_obs / abstention is solved",
            "status": "blocked",
            "evidence": f"p_obs_AUROC={fval(pobs_row, 'auroc'):.6f}; decision_macro_F1={fval(decision_row, 'macro_F1'):.6f}",
        },
        {
            "claim": "calibrated p_obs/p_rel paper-result claim",
            "status": "blocked",
            "evidence": "diagnostic subset only; labels originated from Codex fill and p_obs failed",
        },
        {
            "claim": "Q_e repair is necessary",
            "status": "selected_next_step",
            "evidence": "all observability label groups have Q_e sufficient state in the model-safe view",
        },
    ]

    if not qe_gap_present:
        errors.append({"error": "expected_qe_gap_not_found"})

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_ERROR if errors else STATUS_READY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_artifacts": {
            "metric": repo_rel(repo_root, metric_dir),
            "ingestion": repo_rel(repo_root, ingestion_dir),
        },
        "primary_metrics": {
            "p_obs_auroc": fval(pobs_row, "auroc"),
            "p_obs_ece_10": fval(pobs_row, "ECE_10"),
            "p_rel_auroc": fval(prel_row, "auroc"),
            "p_rel_ece_10": fval(prel_row, "ECE_10"),
            "decision_macro_F1": fval(decision_row, "macro_F1"),
            "decision_accuracy": fval(decision_row, "accuracy"),
        },
        "review_decision": {
            "p_obs_status": "failed_observability_gate",
            "p_rel_status": "diagnostic_signal_present",
            "selective_decision_status": "failed_due_to_no_abstain_behavior",
            "pobs_prel_framework_component_allowed": True,
            "pobs_prel_solved_claim_allowed": False,
            "paper_promotion_pass": False,
            "selected_next_step": "qe_feature_repair_before_any_new_pobs_prel_claim",
            "next_todo": "pobs_prel_qe_repair_plan",
        },
        "validation_errors": len(errors),
        "outputs": {
            "review_decision": repo_rel(repo_root, out / "review_decision.csv"),
            "qe_feature_gap": repo_rel(repo_root, out / "qe_feature_gap.csv"),
            "repair_plan": repo_rel(repo_root, out / "qe_repair_plan.csv"),
            "paper_boundary": repo_rel(repo_root, out / "paper_boundary.csv"),
            "queue_kind_metrics": repo_rel(repo_root, out / "queue_kind_metrics.csv"),
            "observability_label_metrics": repo_rel(repo_root, out / "observability_label_metrics.csv"),
            "report": repo_rel(repo_root, out / "report.md"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
        },
    }

    write_csv(out / "review_decision.csv", review_rows, ["component", "metric", "value", "pass", "decision", "interpretation"])
    write_csv(
        out / "qe_feature_gap.csv",
        qe_gap,
        [
            "observability_label",
            "rows",
            "q_e_sufficient_rows",
            "q_e_uncertain_rows",
            "q_e_limited_rows",
            "q_e_state_code_counts",
            "feature_label_alignment",
        ],
    )
    write_csv(out / "qe_repair_plan.csv", repair_plan, ["priority", "repair_item", "why_needed", "expected_effect"])
    write_csv(out / "paper_boundary.csv", paper_boundary, ["claim", "status", "evidence"])
    write_csv(out / "queue_kind_metrics.csv", queue_metrics, list(queue_metrics[0].keys()) if queue_metrics else ["empty"])
    write_csv(out / "observability_label_metrics.csv", obs_metrics, list(obs_metrics[0].keys()) if obs_metrics else ["empty"])
    (out / "report.md").write_text(build_report(summary, qe_gap, repair_plan), encoding="utf-8")
    write_jsonl(out / "validation_errors.jsonl", errors)
    write_json(out / "summary.json", summary)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
