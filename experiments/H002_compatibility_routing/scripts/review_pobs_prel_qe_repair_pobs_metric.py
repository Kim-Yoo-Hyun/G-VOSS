#!/usr/bin/env python3
"""Review the repaired-Q_e p_obs-only diagnostic metric for H002."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h002_pobs_prel_qe_repair_pobs_metric_review_v1"
STATUS_READY = "h002_pobs_prel_qe_repair_pobs_metric_review_ready"
STATUS_ERROR = "h002_pobs_prel_qe_repair_pobs_metric_review_errors"
EXPECTED_METRIC_STATUS = "h002_pobs_prel_qe_repair_pobs_only_metric_ready"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--metric-dir", type=Path, required=True)
    parser.add_argument("--schema-audit-dir", type=Path, required=True)
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
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


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


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def metric_by_score(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("score_id", ""): row for row in rows}


def build_report(summary: dict[str, Any]) -> str:
    m = summary["primary_metrics"]
    b = summary["baseline_metrics"]
    d = summary["decision"]
    counts = summary["row_counts"]
    lines = [
        "# p_obs Metric Review After Q_e Repair",
        "",
        "## Decision",
        "",
        "`p_obs` is not required for the current H002 main paper claim.",
        "",
        "The repaired `Q_e v2` p_obs-only smoke test passes diagnostically, but it should not be promoted as a calibrated solved p_obs/p_rel result. The current main H002 claim is the factor-isolated compatibility reranking path, not a full observability/abstention system.",
        "",
        "```text",
        f"p_obs_AUROC = {m['p_obs_auroc']:.6f}",
        f"p_obs_ECE_10 = {m['p_obs_ece_10']:.6f}",
        f"abstain_recall = {m['abstain_recall']:.6f}",
        f"direct_Qe_state_AUROC = {b['direct_qe_state_code_auroc']:.6f}",
        f"eval_rows = {counts['eval_rows']}",
        f"unobservable_missing_rows = {counts['eval_label_counts'].get('unobservable_missing_evidence', 0)}",
        f"proxy_shortcut_risk = {d['proxy_shortcut_risk']}",
        f"pobs_required_for_core_claim = {str(d['pobs_required_for_core_claim']).lower()}",
        f"pobs_main_claim_allowed = {str(d['pobs_main_claim_allowed']).lower()}",
        "```",
        "",
        "## Why It Is Not Core",
        "",
        "H002's core mechanism is:",
        "",
        "```text",
        "T_e = predicate / semantic content",
        "G_e = geometry evidence",
        "Z_e = source score / rank",
        "C_e = compatibility(T_e, G_e)",
        "S2(e) = normalized_source_score(Z_e) * C_e",
        "```",
        "",
        "This directly addresses the original problem: source confidence is a mixed signal, so relation reliability should use a factor-isolated predicate-geometry compatibility score before reranking. `p_obs` answers a different question: whether the available evidence is sufficient to make a decision at all.",
        "",
        "Therefore `p_obs` is only necessary if the paper claims an observability-aware selective decision system for attachment, containment, occlusion-heavy, or missing-evidence routes. It is not necessary for the current validation-level comparison-route source-reranking claim.",
        "",
        "## Why Promotion Is Blocked",
        "",
        "- direct `Q_e state_code` also reaches AUROC 1.0, so the learned p_obs result is strongly state/proxy-driven.",
        "- eval `Q_e v2` is audit-proxy diagnostic material, not independent visual/mesh annotation.",
        "- the missing-evidence negative slice has only 4 rows, so broad missing-evidence generalization is not validated.",
        "- this run evaluates p_obs only; it does not rerun a full p_obs/p_rel selective decision system.",
        "",
        "## Paper Boundary",
        "",
        "Use `p_obs` as optional diagnostic or future/appendix framework component. Do not make it part of the main solved claim unless independent observability labels and full selective-decision metrics later pass.",
        "",
        "## Next Step",
        "",
        f"`{d['next_todo']}`",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    metric_dir = resolve(repo_root, args.metric_dir)
    schema_audit_dir = resolve(repo_root, args.schema_audit_dir)
    out = resolve(repo_root, args.out)
    out.mkdir(parents=True, exist_ok=True)

    errors: list[dict[str, Any]] = []
    if not metric_dir.exists():
        errors.append({"error": "missing_metric_dir", "path": repo_rel(repo_root, metric_dir)})
    if not schema_audit_dir.exists():
        errors.append({"error": "missing_schema_audit_dir", "path": repo_rel(repo_root, schema_audit_dir)})

    manifest: dict[str, Any] = {}
    gate: dict[str, Any] = {}
    if not errors:
        manifest = read_json(metric_dir / "metric_manifest.json")
        gate = read_json(metric_dir / "gate_decision.json")
        if manifest.get("status") != EXPECTED_METRIC_STATUS:
            errors.append({"error": "unexpected_metric_status", "actual": manifest.get("status")})
        if manifest.get("validation_errors") != 0:
            errors.append({"error": "metric_validation_errors", "actual": manifest.get("validation_errors")})
        if gate.get("validation_errors") != 0:
            errors.append({"error": "gate_validation_errors", "actual": gate.get("validation_errors")})

    pobs_rows = read_csv(metric_dir / "pobs_metrics.csv") if not errors else []
    pobs_by_score = metric_by_score(pobs_rows)
    learned = pobs_by_score.get("p_obs_learned", {})
    direct_state = pobs_by_score.get("p_obs_qe_state_code", {})
    legacy = pobs_by_score.get("p_obs_legacy_all_sufficient", {})

    p_obs_auroc = as_float(learned.get("auroc"))
    p_obs_ece = as_float(learned.get("ECE_10"))
    p_obs_brier = as_float(learned.get("Brier"))
    p_obs_nll = as_float(learned.get("NLL"))
    abstain_recall = 1.0 - as_float(learned.get("fp"), 0.0) / max(
        1.0, as_float(learned.get("negative"), 0.0)
    )
    observable_false_abstain = as_float(learned.get("fn"), 0.0) / max(
        1.0, as_float(learned.get("positive"), 0.0)
    )
    direct_auroc = as_float(direct_state.get("auroc"))
    direct_ece = as_float(direct_state.get("ECE_10"))
    legacy_auroc = as_float(legacy.get("auroc"))
    legacy_abstain_recall = 1.0 - as_float(legacy.get("fp"), 0.0) / max(
        1.0, as_float(legacy.get("negative"), 0.0)
    )

    row_counts = manifest.get("row_counts", {})
    label_counts = row_counts.get("eval_label_counts", {})
    missing_rows = int(label_counts.get("unobservable_missing_evidence", 0))
    boundary = manifest.get("boundary", {})
    audit_proxy = as_bool(boundary.get("eval_qe_v2_uses_audit_proxy"))
    direct_state_tie = abs(p_obs_auroc - direct_auroc) <= 1e-9 and direct_auroc >= 0.99
    low_missing_coverage = missing_rows < 30
    proxy_shortcut_risk = "high" if audit_proxy or direct_state_tie else "low"

    diagnostic_pass = p_obs_auroc >= 0.70 and p_obs_ece <= 0.20 and abstain_recall >= 0.70
    pobs_required_for_core_claim = False
    pobs_main_claim_allowed = False
    pobs_optional_framework_component = True
    full_selective_rerun_now = False

    review_rows = [
        {
            "item": "p_obs_only_diagnostic_pass",
            "value": diagnostic_pass,
            "decision": "pass_as_diagnostic",
            "reason": "repaired Q_e v2 separates observable from ambiguous/missing rows",
        },
        {
            "item": "proxy_shortcut_risk",
            "value": proxy_shortcut_risk,
            "decision": "block_solved_claim",
            "reason": "direct Q_e state matches learned p_obs and eval Q_e v2 is audit-proxy material",
        },
        {
            "item": "pobs_required_for_core_claim",
            "value": pobs_required_for_core_claim,
            "decision": "exclude_from_core_claim",
            "reason": "core H002 claim is C_e source reranking, not selective observability",
        },
        {
            "item": "full_selective_decision_rerun_now",
            "value": full_selective_rerun_now,
            "decision": "do_not_run_now",
            "reason": "p_obs is not necessary for the core claim and independent observability GT is still insufficient",
        },
    ]
    claim_boundary_rows = [
        {
            "claim_component": "C_e compatibility reranking",
            "paper_position": "main_candidate",
            "allowed": True,
            "condition": "validation-level source reranking with T_e/G_e/Z_e separation and existing caveats",
        },
        {
            "claim_component": "p_obs observability head",
            "paper_position": "optional_diagnostic_or_future",
            "allowed": False,
            "condition": "not a main solved claim; reopen with independent visual/mesh observability labels",
        },
        {
            "claim_component": "p_obs/p_rel calibrated selective decision",
            "paper_position": "blocked",
            "allowed": False,
            "condition": "needs full selective rerun, calibration, independent observability labels, and missing-evidence controls",
        },
        {
            "claim_component": "general reliable 3D relation framework",
            "paper_position": "design_goal_not_completed_result",
            "allowed": False,
            "condition": "needs support/contact solved or observability-heavy route validation",
        },
    ]
    shortcut_rows = [
        {
            "check": "learned_p_obs_vs_direct_qe_state",
            "learned_value": f"{p_obs_auroc:.6f}",
            "baseline_value": f"{direct_auroc:.6f}",
            "risk": "high" if direct_state_tie else "low",
            "interpretation": "p_obs is likely learning the repaired Q_e state rather than independent observability reasoning",
        },
        {
            "check": "audit_proxy_eval_qe_v2",
            "learned_value": str(audit_proxy).lower(),
            "baseline_value": "",
            "risk": "high" if audit_proxy else "low",
            "interpretation": "eval Q_e v2 is diagnostic proxy material",
        },
        {
            "check": "missing_evidence_slice_size",
            "learned_value": str(missing_rows),
            "baseline_value": "",
            "risk": "high" if low_missing_coverage else "low",
            "interpretation": "missing-evidence generalization is under-covered",
        },
    ]
    next_rows = [
        {
            "priority": 1,
            "todo": "h002_core_claim_without_pobs_boundary_update",
            "action": "update H002 claim docs so p_obs is optional diagnostic/future, not a core solved claim",
        },
        {
            "priority": 2,
            "todo": "source_reranking_claim_strengthening",
            "action": "keep focus on C_e/source-reranking ablations, CI, qualitative cases, and route caveats",
        },
        {
            "priority": 3,
            "todo": "pobs_reopen_condition",
            "action": "only reopen p_obs/p_rel if independent visual/mesh observability labels and full selective metrics are available",
        },
    ]

    status = STATUS_ERROR if errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "validation_errors": len(errors),
        "source_artifacts": {
            "metric_dir": repo_rel(repo_root, metric_dir),
            "schema_audit_dir": repo_rel(repo_root, schema_audit_dir),
        },
        "row_counts": {
            "train_rows": int(row_counts.get("train_rows", 0)),
            "eval_rows": int(row_counts.get("eval_rows", 0)),
            "eval_label_counts": label_counts,
        },
        "primary_metrics": {
            "p_obs_auroc": p_obs_auroc,
            "p_obs_ece_10": p_obs_ece,
            "p_obs_brier": p_obs_brier,
            "p_obs_nll": p_obs_nll,
            "abstain_recall": abstain_recall,
            "observable_false_abstain_rate": observable_false_abstain,
        },
        "baseline_metrics": {
            "direct_qe_state_code_auroc": direct_auroc,
            "direct_qe_state_code_ece_10": direct_ece,
            "legacy_all_sufficient_auroc": legacy_auroc,
            "legacy_all_sufficient_abstain_recall": legacy_abstain_recall,
        },
        "diagnostic_decision": {
            "pobs_only_diagnostic_pass": diagnostic_pass,
            "direct_qe_state_tie": direct_state_tie,
            "audit_proxy_eval_qe_v2": audit_proxy,
            "low_missing_evidence_coverage": low_missing_coverage,
        },
        "decision": {
            "proxy_shortcut_risk": proxy_shortcut_risk,
            "pobs_required_for_core_claim": pobs_required_for_core_claim,
            "pobs_main_claim_allowed": pobs_main_claim_allowed,
            "pobs_optional_framework_component": pobs_optional_framework_component,
            "full_selective_decision_rerun_now": full_selective_rerun_now,
            "selected_path": "demote_pobs_to_optional_diagnostic_keep_core_claim_on_Ce_source_reranking",
            "next_todo": "h002_core_claim_without_pobs_boundary_update",
        },
        "outputs": {
            "summary": repo_rel(repo_root, out / "summary.json"),
            "review_decision": repo_rel(repo_root, out / "review_decision.csv"),
            "claim_boundary": repo_rel(repo_root, out / "claim_boundary.csv"),
            "proxy_shortcut_audit": repo_rel(repo_root, out / "proxy_shortcut_audit.csv"),
            "next_steps": repo_rel(repo_root, out / "next_steps.csv"),
            "report": repo_rel(repo_root, out / "report.md"),
            "validation_errors": repo_rel(repo_root, out / "validation_errors.jsonl"),
        },
    }

    write_json(out / "summary.json", summary)
    write_jsonl(out / "validation_errors.jsonl", errors)
    write_csv(out / "review_decision.csv", review_rows, ["item", "value", "decision", "reason"])
    write_csv(
        out / "claim_boundary.csv",
        claim_boundary_rows,
        ["claim_component", "paper_position", "allowed", "condition"],
    )
    write_csv(
        out / "proxy_shortcut_audit.csv",
        shortcut_rows,
        ["check", "learned_value", "baseline_value", "risk", "interpretation"],
    )
    write_csv(out / "next_steps.csv", next_rows, ["priority", "todo", "action"])
    (out / "report.md").write_text(build_report(summary), encoding="utf-8")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
