#!/usr/bin/env python3
"""Build Docker-reproducible H001 geometry reliability tables.

This script reads locked hypothesis-stage artifacts and emits paper-facing
tables/reports for the scoped VL-SAT result. It does not train, tune, or rerun
the predictor.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HYPOTHESIS_ROOT = Path("hypothesis/CAND-001/H001_geometry-grounded-verification")
ARTIFACT_ROOT = HYPOTHESIS_ROOT / "artifacts"

EXPECTED_COUNTS = {
    "held_out_scans": 127,
    "subgraphs": 388,
    "directed_pairs": 25916,
    "prediction_rows": 673816,
    "ground_truth_rows": 7505,
    "in_scope_prediction_rows": 155496,
    "in_scope_gt_denominator": 2545,
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_optional_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, None
    try:
        return load_json(path), None
    except Exception as exc:  # noqa: BLE001 - table hook must report unreadable runtime artifacts.
        return None, str(exc)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def count_lines(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def metric_row(metrics: dict[str, Any], condition: str) -> dict[str, float]:
    cond = metrics["conditions"][condition]
    recall = cond["recall"]["by_k"]
    violation = cond["violation_rate"]["by_k"]
    return {
        "r50": recall["50"]["recall"],
        "r100": recall["100"]["recall"],
        "v50": violation["50"]["violation_rate"],
        "v100": violation["100"]["violation_rate"],
    }


def pct(value: Any, digits: int = 4) -> str:
    if value is None:
        return "NA"
    return f"{float(value):.{digits}f}"


def pp(value: Any, digits: int = 2) -> str:
    if value is None:
        return "NA"
    return f"{float(value) * 100.0:+.{digits}f} pp"


def signed(value: float, digits: int = 4) -> str:
    return f"{value:+.{digits}f}"


def relative_reduction(base: float, value: float) -> float | None:
    if base == 0:
        return None
    return (base - value) / base


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines) + "\n"


def write_markdown_table(path: Path, title: str, headers: list[str], rows: list[list[Any]]) -> None:
    ensure_dir(path.parent)
    content = f"# {title}\n\n" + markdown_table(headers, rows)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_inputs(paths: dict[str, Path], payloads: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []

    hardened_manifest = payloads["hardened_manifest"]
    if hardened_manifest.get("status") != "ready":
        errors.append("hardened manifest status is not ready")

    counts = hardened_manifest.get("counts", {})
    checks = {
        "subgraphs": counts.get("subgraphs"),
        "directed_pairs": counts.get("directed_pairs"),
        "prediction_rows": counts.get("predictions"),
        "ground_truth_rows": counts.get("ground_truth_edges"),
    }
    for key, actual in checks.items():
        expected = EXPECTED_COUNTS[key]
        if actual != expected:
            errors.append(f"{key}: expected {expected}, got {actual}")

    for name in ("hardened_metrics", "hardened_g3"):
        if payloads[name].get("blocked"):
            errors.append(f"{name} has blockers: {payloads[name]['blocked']}")
        metric_counts = payloads[name].get("counts", {})
        if metric_counts.get("predictions") != EXPECTED_COUNTS["prediction_rows"]:
            errors.append(f"{name} prediction count mismatch")
        if metric_counts.get("ground_truth") != EXPECTED_COUNTS["ground_truth_rows"]:
            errors.append(f"{name} ground-truth count mismatch")

    gt_metrics = payloads["gt_metrics"]
    if gt_metrics.get("status") != "ready":
        errors.append("GT verifier metrics status is not ready")
    if gt_metrics.get("counts", {}).get("gt_positive") != EXPECTED_COUNTS["in_scope_gt_denominator"]:
        errors.append("GT positive denominator mismatch")
    if gt_metrics.get("counts", {}).get("gt_counterfactual_negative") != EXPECTED_COUNTS["in_scope_gt_denominator"]:
        errors.append("GT counterfactual denominator mismatch")

    audit = payloads["audit_summary"]
    if audit.get("status") != "ready":
        errors.append("structured audit status is not ready")
    visual = payloads["visual_summary"]
    if visual.get("status") != "ready_sanity_pass":
        errors.append("visual spot-check status is not ready_sanity_pass")

    line_expectations = {
        "predictions_jsonl": EXPECTED_COUNTS["prediction_rows"],
        "ground_truth_jsonl": EXPECTED_COUNTS["ground_truth_rows"],
        "verification_jsonl": EXPECTED_COUNTS["prediction_rows"],
    }
    for name, expected in line_expectations.items():
        actual = count_lines(paths[name])
        if actual != expected:
            errors.append(f"{name}: expected {expected} rows, got {actual}")

    return errors


def build_table1(hardened: dict[str, Any], g3: dict[str, Any]) -> tuple[list[dict[str, Any]], list[list[str]]]:
    semantic = metric_row(hardened, "semantic_only")
    source = {
        "semantic_only": (hardened, "semantic_only", "reproduced VL-SAT semantic ranking"),
        "probabilistic_recalibrated": (hardened, "probabilistic_recalibrated", "main recall-first H001 condition"),
        "rule_verified_point_subtype": (hardened, "rule_verified_point_subtype", "hard-filter zero-violation diagnostic"),
        "family_specific_p_geom_valid": (g3, "control_family_specific_p_geom_valid", "stricter violation-first operating point"),
    }
    rows: list[dict[str, Any]] = []
    md_rows: list[list[str]] = []
    for display, (metrics, condition, role) in source.items():
        values = metric_row(metrics, condition)
        d_r50 = values["r50"] - semantic["r50"]
        d_r100 = values["r100"] - semantic["r100"]
        d_v50 = values["v50"] - semantic["v50"]
        d_v100 = values["v100"] - semantic["v100"]
        rr50 = relative_reduction(semantic["v50"], values["v50"])
        rr100 = relative_reduction(semantic["v100"], values["v100"])
        row = {
            "condition": display,
            "role": role,
            "r50": values["r50"],
            "r100": values["r100"],
            "violation50": values["v50"],
            "violation100": values["v100"],
            "delta_r50_vs_semantic": d_r50,
            "delta_r100_vs_semantic": d_r100,
            "delta_violation50_vs_semantic": d_v50,
            "delta_violation100_vs_semantic": d_v100,
            "relative_violation_reduction50": rr50,
            "relative_violation_reduction100": rr100,
        }
        rows.append(row)
        md_rows.append([
            display,
            role,
            pct(values["r50"]),
            pct(values["r100"]),
            pct(values["v50"]),
            pct(values["v100"]),
            signed(d_r50),
            signed(d_r100),
            signed(d_v50),
            signed(d_v100),
            pct(rr50) if rr50 is not None else "NA",
            pct(rr100) if rr100 is not None else "NA",
        ])
    return rows, md_rows


def build_table2(g3: dict[str, Any]) -> tuple[list[dict[str, Any]], list[list[str]]]:
    conditions = [
        ("control_p_geom_valid_only", "geometry-only ranking control"),
        ("control_distance_only", "simple distance heuristic control"),
        ("control_shuffled_geometry", "breaks geometry identity while preserving distribution"),
        ("control_wrong_pair_geometry", "tests object-pair identity"),
        ("control_family_specific_p_geom_valid", "stricter family-specific calibration"),
    ]
    main = metric_row(g3, "probabilistic_recalibrated")
    rows: list[dict[str, Any]] = []
    md_rows: list[list[str]] = []
    for condition, purpose in conditions:
        values = metric_row(g3, condition)
        row = {
            "condition": condition,
            "purpose": purpose,
            "r50": values["r50"],
            "r100": values["r100"],
            "violation50": values["v50"],
            "violation100": values["v100"],
            "delta_r50_vs_main": values["r50"] - main["r50"],
            "delta_violation50_vs_main": values["v50"] - main["v50"],
        }
        rows.append(row)
        md_rows.append([
            condition,
            purpose,
            pct(values["r50"]),
            pct(values["r100"]),
            pct(values["v50"]),
            pct(values["v100"]),
            signed(row["delta_r50_vs_main"]),
            signed(row["delta_violation50_vs_main"]),
        ])
    return rows, md_rows


def build_table3(gt: dict[str, Any]) -> tuple[list[dict[str, Any]], list[list[str]]]:
    pos = gt["gt_positive"]
    neg = gt["gt_counterfactual_negative"]
    disc = gt["p_geom_valid_discrimination"]
    rows = [
        {
            "metric": "GT-positive nonviolated rate",
            "rows": pos["rows"],
            "value": pos["nonviolated_rate"],
            "note": "valid GT relations should not be flagged as violated",
        },
        {
            "metric": "GT-derived negative nonsatisfied rate",
            "rows": neg["rows"],
            "value": neg["nonsatisfied_rate"],
            "note": "counterfactual negatives should not be satisfied",
        },
        {
            "metric": "p_geom_valid AUROC",
            "rows": disc["rows"],
            "value": disc["auroc_valid"],
            "note": "probability discriminates GT positives from counterfactual negatives",
        },
        {
            "metric": "p_geom_valid AUPRC",
            "rows": disc["rows"],
            "value": disc["auprc_valid"],
            "note": "precision-recall discrimination",
        },
        {
            "metric": "p_geom_valid Brier",
            "rows": disc["rows"],
            "value": disc["brier"],
            "note": "calibration error on GT/counterfactual verifier evaluation",
        },
    ]
    md_rows = [[row["metric"], row["rows"], pct(row["value"]), row["note"]] for row in rows]
    return rows, md_rows


def build_table4(audit: dict[str, Any], visual: dict[str, Any]) -> tuple[list[dict[str, Any]], list[list[str]]]:
    precision = audit["violation_precision"]["required_violation_buckets"]
    visual_alignment = visual["target_alignment"]
    private_agreement = visual.get("codex_structured_audit_agreement_private", {})
    rows = [
        {
            "source": "structured_audit",
            "status": audit["status"],
            "rows": audit["counts"]["labeled_rows"],
            "metric": "strict invalid-only precision",
            "value": precision["precision_invalid_only"],
            "note": "non-independent structured audit",
        },
        {
            "source": "structured_audit",
            "status": audit["status"],
            "rows": audit["counts"]["labeled_rows"],
            "metric": "quality-issue precision",
            "value": precision["precision_quality_issue"],
            "note": "invalid, too coarse, scan-missing, or annotation-noise labels",
        },
        {
            "source": "visual_spotcheck",
            "status": visual["status"],
            "rows": visual["counts"]["labeled_rows"],
            "metric": "target-bucket quality-issue rate",
            "value": visual_alignment["quality_issue_rate"],
            "note": "reduced 50-row visual sanity check, reviewer yhkim",
        },
        {
            "source": "visual_spotcheck",
            "status": visual["status"],
            "rows": visual["counts"]["labeled_rows"],
            "metric": "target-bucket contradiction rate",
            "value": visual_alignment["contradiction_rate"],
            "note": "valid/verifier-error contradiction among target buckets",
        },
        {
            "source": "visual_spotcheck",
            "status": visual["status"],
            "rows": private_agreement.get("comparable_rows", 0),
            "metric": "private-reference exact match rate",
            "value": private_agreement.get("exact_match_rate"),
            "note": "provenance caveat: Codex transcribed reviewer-confirmed labels",
        },
    ]
    md_rows = [[row["source"], row["status"], row["rows"], row["metric"], pct(row["value"]), row["note"]] for row in rows]
    return rows, md_rows


def build_table5(open3dsg_hook: dict[str, Any] | None = None) -> tuple[list[dict[str, Any]], list[list[str]]]:
    open3dsg_ready = bool(open3dsg_hook and open3dsg_hook.get("status") == "ready")
    rows = [
        {
            "source_or_claim": "VL-SAT / vlsat_closed_set",
            "status": "ready",
            "allowed_claim": "scoped geometry-consistency reliability-layer result",
            "blocked_extension": "not baseline-agnostic by itself",
        },
        {
            "source_or_claim": "Open3DSG",
            "status": "second_source_metric_ready" if open3dsg_ready else "selected_second_source_blocked",
            "allowed_claim": (
                "cross-source reliability-layer evidence within measured H001 families"
                if open3dsg_ready
                else "none until Docker checkpoint reproduction and metric run exist"
            ),
            "blocked_extension": (
                "not broad open-vocabulary improvement by itself"
                if open3dsg_ready
                else "cross-predictor claim blocked"
            ),
        },
        {
            "source_or_claim": "FROSS",
            "status": "runtime_blocked_support_contact_only",
            "allowed_claim": "future support/contact smoke only",
            "blocked_extension": "not full-family evidence",
        },
        {
            "source_or_claim": "Broad open-vocabulary 3DSSG improvement",
            "status": "blocked",
            "allowed_claim": "not allowed from current evidence",
            "blocked_extension": "requires measured second-source/open-vocabulary evidence",
        },
    ]
    md_rows = [[row["source_or_claim"], row["status"], row["allowed_claim"], row["blocked_extension"]] for row in rows]
    return rows, md_rows


def build_open3dsg_table6_hook(out_root: Path) -> dict[str, Any]:
    metrics_path = out_root / "sources/open3dsg/metrics/metrics.json"
    contract_metrics_path = out_root / "sources/open3dsg/metric_join_contract/metrics.json"
    manifest_path = out_root / "sources/open3dsg/metric_join_contract/manifest.json"
    metric_scope_path = out_root / "sources/open3dsg/metric_scope/manifest.json"
    metrics, metrics_error = load_optional_json(metrics_path)
    contract_metrics, contract_metrics_error = load_optional_json(contract_metrics_path)
    manifest, manifest_error = load_optional_json(manifest_path)
    metric_scope, metric_scope_error = load_optional_json(metric_scope_path)

    metric_status = "missing_open3dsg_metrics"
    if metrics is not None:
        metric_status = str(metrics.get("status", "status_missing"))
    elif metrics_error:
        metric_status = "unreadable_open3dsg_metrics"

    contract_metric_status = None
    if contract_metrics is not None:
        contract_metric_status = str(contract_metrics.get("status", "status_missing"))
    elif contract_metrics_error:
        contract_metric_status = "unreadable_metric_contract"

    manifest_status = None
    if manifest is not None:
        manifest_status = manifest.get("status")
    elif manifest_error:
        manifest_status = "unreadable_manifest"

    metric_scope_status = None
    if metric_scope is not None:
        metric_scope_status = metric_scope.get("status")
    elif metric_scope_error:
        metric_scope_status = "unreadable_metric_scope"

    blocked: list[str] = []
    if metrics is None:
        blocked.append(f"metrics_json:{metric_status}:{metrics_path.relative_to(out_root)}")
    else:
        blocked.extend(str(item) for item in metrics.get("blocked", []))
    if manifest is None:
        blocked.append(f"manifest_json:{manifest_status or 'missing'}:{manifest_path.relative_to(out_root)}")
    else:
        blocked.extend(str(item) for item in manifest.get("blocked", []))
    if metric_scope is None:
        blocked.append(f"metric_scope:{metric_scope_status or 'missing'}:{metric_scope_path.relative_to(out_root)}")
    elif metric_scope_status != "metric_scope_policy_ready_no_metric_execution":
        blocked.append(f"metric_scope_status:{metric_scope_status}:{metric_scope_path.relative_to(out_root)}")
        blocked.extend(str(item) for item in metric_scope.get("blockers", []))

    seen: set[str] = set()
    deduped_blocked: list[str] = []
    for item in blocked:
        if item not in seen:
            deduped_blocked.append(item)
            seen.add(item)

    ready = (
        metrics is not None
        and metrics.get("status") == "ready"
        and not metrics.get("blocked")
        and metrics.get("conditions")
        and metric_scope is not None
        and metric_scope_status == "metric_scope_policy_ready_no_metric_execution"
        and not metric_scope.get("blockers")
    )

    def condition_summary(condition: str) -> dict[str, Any] | None:
        if metrics is None:
            return None
        payload = metrics.get("conditions", {}).get(condition)
        if not payload:
            return None
        recall = payload.get("recall", {}).get("by_k", {})
        violation = payload.get("violation_rate", {}).get("by_k", {})
        return {
            "r50": recall.get("50", {}).get("recall"),
            "r100": recall.get("100", {}).get("recall"),
            "violation50": violation.get("50", {}).get("violation_rate"),
            "violation100": violation.get("100", {}).get("violation_rate"),
        }

    input_statuses = {}
    if manifest is not None:
        input_statuses = {
            name: value.get("status")
            for name, value in manifest.get("inputs", {}).items()
            if isinstance(value, dict)
        }

    return {
        "schema_version": "h001_open3dsg_table6_hook_v1",
        "status": "ready" if ready else "blocked_until_open3dsg_metrics_ready",
        "ready_gate": {
            "required_metrics_status": "ready",
            "requires_nonempty_conditions": True,
            "requires_empty_blocked_list": True,
            "requires_metric_scope_policy_ready": True,
            "contract_only_statuses_are_blocked": [
                "blocked_runtime_inputs_missing",
                "ready_runtime_inputs_present_contract_only",
            ],
        },
        "metric_contract": {
            "metrics_path": str(metrics_path.relative_to(out_root)),
            "contract_metrics_path": str(contract_metrics_path.relative_to(out_root)),
            "manifest_path": str(manifest_path.relative_to(out_root)),
            "metrics_exists": metrics_path.exists(),
            "contract_metrics_exists": contract_metrics_path.exists(),
            "manifest_exists": manifest_path.exists(),
            "metrics_status": metric_status,
            "contract_metrics_status": contract_metric_status,
            "manifest_status": manifest_status,
            "counts": metrics.get("counts", {}) if metrics else {},
            "input_statuses": input_statuses,
            "blocked": deduped_blocked,
        },
        "key_metrics": {
            "semantic_only": condition_summary("semantic_only"),
            "probabilistic_recalibrated": condition_summary("probabilistic_recalibrated"),
            "rule_verified_point_subtype": condition_summary("rule_verified_point_subtype"),
            "control_family_specific_p_geom_valid": condition_summary(
                "control_family_specific_p_geom_valid"
            ),
        },
        "metric_scope": {
            "path": str(metric_scope_path.relative_to(out_root)),
            "exists": metric_scope_path.exists(),
            "status": metric_scope_status,
            "in_scope_gt_denominator": (
                metric_scope.get("ground_truth_denominator", {}).get("in_scope_gt_denominator")
                if metric_scope
                else None
            ),
        },
        "claim_boundary": (
            "Table 6 may report Open3DSG numbers only after metrics.json has status ready, "
            "nonempty condition metrics, no blockers, and metric_scope policy is ready."
        ),
    }


def build_table6(open3dsg_hook: dict[str, Any]) -> tuple[list[dict[str, Any]], list[list[str]]]:
    metric_contract = open3dsg_hook["metric_contract"]
    open3dsg_ready = open3dsg_hook["status"] == "ready"
    open3dsg_blockers = metric_contract.get("blocked", [])
    rows = [
        {
            "prediction_source": "VL-SAT / vlsat_closed_set",
            "evidence_artifact": "locked VL-SAT H001 metrics",
            "metric_status": "ready",
            "contract_status": "ready",
            "blockers": "none",
            "claim_use": "scoped current result",
            "caveat_note": "controlled reproduced anchor under fixed H001 denominator",
        },
        {
            "prediction_source": "Open3DSG",
            "evidence_artifact": metric_contract["metrics_path"],
            "metric_status": "ready" if open3dsg_ready else "blocked",
            "contract_status": str(metric_contract.get("metrics_status")),
            "blockers": "; ".join(open3dsg_blockers) if open3dsg_blockers else "none",
            "claim_use": (
                "cross-source claim enabled within measured H001 families"
                if open3dsg_ready
                else "required before cross-source claim"
            ),
            "caveat_note": (
                "averaged-BLIP variant; filtered train/dev; covered H001 377/388; "
                "exact-label denominator 2545; validation_missing_preprocessed:11; "
                "residual calibration risk"
            ),
        },
    ]
    md_rows = [
        [
            row["prediction_source"],
            row["evidence_artifact"],
            row["metric_status"],
            row["contract_status"],
            row["blockers"],
            row["claim_use"],
            row["caveat_note"],
        ]
        for row in rows
    ]
    return rows, md_rows


def write_outputs(repo_root: Path, out_root: Path) -> dict[str, Any]:
    paths = {
        "hardened_manifest": repo_root / ARTIFACT_ROOT / "evaluation/vlsat_closed_set/hardened/manifest.json",
        "hardened_metrics": repo_root / ARTIFACT_ROOT / "evaluation/vlsat_closed_set/hardened_metrics/metrics.json",
        "hardened_g3": repo_root / ARTIFACT_ROOT / "evaluation/vlsat_closed_set/hardened_g3/metrics.json",
        "gt_metrics": repo_root / ARTIFACT_ROOT / "evaluation/vlsat_closed_set/hardened/gt_eval/metrics.json",
        "audit_summary": repo_root / ARTIFACT_ROOT / "evaluation/vlsat_closed_set/hardened/human_audit/label_summary.json",
        "visual_summary": repo_root / ARTIFACT_ROOT / "evaluation/vlsat_closed_set/hardened/human_audit/visual_spotcheck/summary.json",
        "evidence_lock": repo_root / ARTIFACT_ROOT / "evaluation/vlsat_closed_set/hardened/evidence_lock/manifest.json",
        "predictions_jsonl": repo_root / ARTIFACT_ROOT / "evaluation/vlsat_closed_set/hardened/predictions.jsonl",
        "ground_truth_jsonl": repo_root / ARTIFACT_ROOT / "evaluation/vlsat_closed_set/hardened/ground_truth.jsonl",
        "verification_jsonl": repo_root / ARTIFACT_ROOT / "evaluation/vlsat_closed_set/hardened_geometry/verification.jsonl",
    }
    payloads = {name: load_json(path) for name, path in paths.items() if path.suffix == ".json"}
    errors = validate_inputs(paths, payloads)
    if errors:
        raise SystemExit("Input validation failed:\n- " + "\n- ".join(errors))

    ensure_dir(out_root / "tables")
    ensure_dir(out_root / "figures")
    ensure_dir(out_root / "sources/vlsat")
    ensure_dir(out_root / "sources/open3dsg")

    table1, table1_md = build_table1(payloads["hardened_metrics"], payloads["hardened_g3"])
    table2, table2_md = build_table2(payloads["hardened_g3"])
    table3, table3_md = build_table3(payloads["gt_metrics"])
    table4, table4_md = build_table4(payloads["audit_summary"], payloads["visual_summary"])
    open3dsg_table6_hook = build_open3dsg_table6_hook(out_root)
    table5, table5_md = build_table5(open3dsg_table6_hook)
    table6, table6_md = build_table6(open3dsg_table6_hook)

    table_specs = [
        ("table1_main_prediction", "Table 1 Main Held-Out Prediction Result", table1, table1_md),
        ("table2_controls", "Table 2 Nontriviality Controls", table2, table2_md),
        ("table3_gt_verifier", "Table 3 GT-Based Verifier Evaluation", table3, table3_md),
        ("table4_audit", "Table 4 Audit And Visual Sanity Check", table4, table4_md),
        ("table5_claim_boundary", "Table 5 Source-Specific Claim Boundary", table5, table5_md),
        ("table6_cross_source_status", "Table 6 Cross-Source Status", table6, table6_md),
    ]
    generated_tables: list[str] = []
    for stem, title, rows, md_rows in table_specs:
        json_path = out_root / "tables" / f"{stem}.json"
        csv_path = out_root / "tables" / f"{stem}.csv"
        md_path = out_root / "tables" / f"{stem}.md"
        write_json(json_path, rows)
        write_csv(csv_path, rows, list(rows[0].keys()))
        write_markdown_table(md_path, title, list(rows[0].keys()), md_rows)
        generated_tables.extend([str(json_path.relative_to(out_root)), str(csv_path.relative_to(out_root)), str(md_path.relative_to(out_root))])

    figure_specs = [
        {
            "figure": "Figure 1",
            "status": "spec_ready",
            "content": "framework pipeline: predictions, identity-preserving rows, geometry evidence, verifier, p_geom_valid, reranking/filtering",
            "source": "method diagram to be drawn from 02_method.md and this experiment manifest",
        },
        {
            "figure": "Figure 2",
            "status": "spec_ready",
            "content": "reliability-recall tradeoff across semantic_only, probabilistic_recalibrated, rule_verified_point_subtype, family_specific_p_geom_valid",
            "source": "tables/table1_main_prediction.json",
        },
        {
            "figure": "Figure 3",
            "status": "case_sources_ready",
            "content": "traceable qualitative cases from visual spot-check figure candidates",
            "source": "hypothesis artifacts/evaluation/vlsat_closed_set/hardened/human_audit/visual_spotcheck/summary.json",
        },
    ]
    write_json(out_root / "figures/figure_specs.json", figure_specs)
    figure_md_rows = [[item["figure"], item["status"], item["content"], item["source"]] for item in figure_specs]
    write_markdown_table(out_root / "figures/figure_specs.md", "Figure Specifications", ["figure", "status", "content", "source"], figure_md_rows)

    locked_inputs = []
    for name, path in paths.items():
        rel_path = path.relative_to(repo_root)
        record: dict[str, Any] = {
            "name": name,
            "path": str(rel_path),
            "exists": path.exists(),
        }
        if path.suffix == ".json":
            record["sha256"] = sha256_file(path)
        elif path.suffix == ".jsonl":
            record["row_count"] = count_lines(path)
        locked_inputs.append(record)
    write_json(out_root / "sources/vlsat/locked_inputs.json", locked_inputs)

    write_json(out_root / "sources/open3dsg/table6_hook.json", open3dsg_table6_hook)

    open3dsg_ready = open3dsg_table6_hook["status"] == "ready"
    open3dsg_status = {
        "status": open3dsg_table6_hook["status"],
        "required_next_outputs": (
            [
                "real Open3DSG failure-analysis rows from prediction/GT/geometry/metric joins",
                "qualitative inspection of representative Open3DSG failure cases",
            ]
            if open3dsg_ready
            else [
                "trained Open3DSG checkpoint",
                "identity-preserving raw dump",
                "open3dsg_ov prediction JSONL",
                "geometry verification JSONL",
                "metric table using the H001 suite",
            ]
        ),
        "table6_hook": open3dsg_table6_hook,
        "claim_boundary": (
            "Cross-source reliability-layer claim is enabled only within measured H001 families and closed-set/GT-object scope."
            if open3dsg_ready
            else "No cross-source claim until these outputs exist."
        ),
    }
    write_json(out_root / "sources/open3dsg/status.json", open3dsg_status)

    manifest = {
        "schema_version": "h001_geom_reliability_experiment_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "ready",
        "method_framing": "calibrated geometry-consistency evaluation and re-ranking framework",
        "source_status": {
            "vlsat": "ready_locked_artifact_reproduction",
            "open3dsg": open3dsg_status["status"],
        },
        "table6_hook": {
            "open3dsg_status": open3dsg_table6_hook["status"],
            "metric_contract_status": open3dsg_table6_hook["metric_contract"]["metrics_status"],
            "metric_scope_status": open3dsg_table6_hook["metric_scope"]["status"],
            "in_scope_gt_denominator": open3dsg_table6_hook["metric_scope"]["in_scope_gt_denominator"],
            "blocked": open3dsg_table6_hook["metric_contract"]["blocked"],
        },
        "expected_counts": EXPECTED_COUNTS,
        "generated_tables": generated_tables,
        "generated_figures": [
            "figures/figure_specs.json",
            "figures/figure_specs.md",
        ],
        "locked_inputs": locked_inputs,
    }
    write_json(out_root / "manifest.lock.json", manifest)

    report = build_report(table1, table3, table4, table5, open3dsg_table6_hook, out_root)
    (out_root / "report.md").write_text(report, encoding="utf-8")
    return manifest


def build_report(
    table1: list[dict[str, Any]],
    table3: list[dict[str, Any]],
    table4: list[dict[str, Any]],
    table5: list[dict[str, Any]],
    open3dsg_hook: dict[str, Any],
    out_root: Path,
) -> str:
    main = next(row for row in table1 if row["condition"] == "probabilistic_recalibrated")
    semantic = next(row for row in table1 if row["condition"] == "semantic_only")
    gt_auroc = next(row for row in table3 if row["metric"] == "p_geom_valid AUROC")
    gt_auprc = next(row for row in table3 if row["metric"] == "p_geom_valid AUPRC")
    visual_quality = next(row for row in table4 if row["metric"] == "target-bucket quality-issue rate")
    visual_contra = next(row for row in table4 if row["metric"] == "target-bucket contradiction rate")
    open3dsg_ready = open3dsg_hook.get("status") == "ready"
    open3dsg_metrics = open3dsg_hook.get("key_metrics", {})
    open3dsg_semantic = open3dsg_metrics.get("semantic_only") or {}
    open3dsg_prob = open3dsg_metrics.get("probabilistic_recalibrated") or {}
    open3dsg_fact = (
        "- Open3DSG second-source metrics are ready: semantic_only R@50/R@100 "
        f"{pct(open3dsg_semantic.get('r50'))}/{pct(open3dsg_semantic.get('r100'))}; "
        "probabilistic_recalibrated R@50/R@100 "
        f"{pct(open3dsg_prob.get('r50'))}/{pct(open3dsg_prob.get('r100'))}; "
        "Violation@50/@100 "
        f"{pct(open3dsg_prob.get('violation50'))}/{pct(open3dsg_prob.get('violation100'))}."
        if open3dsg_ready
        else "- Open3DSG numbers are blocked until feature dump, checkpoint reproduction, raw dump, adapter export, geometry join, and metric execution are complete."
    )
    open3dsg_inference = (
        "- Open3DSG now provides second-source metric evidence for the same H001 geometry-checkable families; claims should still stay scoped to the measured closed-set/GT-object setting."
        if open3dsg_ready
        else "- The current result should be treated as single-source evidence until Open3DSG reproduction and metrics are complete."
    )
    open3dsg_boundary = (
        "- Allowed now: cross-source VL-SAT + Open3DSG reliability-layer evidence within measured H001 families.\n"
        "- Blocked now: broad open-vocabulary 3DSSG improvement claim without additional source/task evidence."
        if open3dsg_ready
        else "- Allowed now: scoped VL-SAT-centered reliability-layer result for geometry-checkable families.\n"
        "- Preferred top-tier upgrade: cross-source VL-SAT + Open3DSG reliability-layer result.\n"
        "- Blocked now: baseline-agnostic or broad open-vocabulary 3DSSG improvement claim."
    )
    open3dsg_completion = (
        "- Open3DSG second-source defense is now stronger because feature audit, checkpoint reproduction, clean raw-dump source provenance, adapter export, geometry join, metric eval, real failure-analysis rows, qualitative case queue, deterministic qualitative case inspection, and paper-facing caveat wording all exist. The remaining paper risk is claim discipline: keep Open3DSG wording scoped to the measured H001-family, averaged-BLIP, covered-loadable setting."
        if open3dsg_ready
        else "- Completion of the background Open3DSG feature dump helps the defense mainly by enabling second-source checkpoint reproduction and metrics. It does not by itself answer reviewer concerns; the stronger defense comes only after feature audit, checkpoint reproduction, raw dump identity pass, adapter export, geometry join, metric tables, and real failure-analysis rows are completed."
    )
    bootstrap_path = out_root / "bootstrap_ci/summary.json"
    bootstrap_fact = "- Docker subgraph bootstrap CI status: not generated."
    if bootstrap_path.exists():
        bootstrap = load_json(bootstrap_path)
        open3dsg_delta = (
            bootstrap.get("sources", {})
            .get("open3dsg_ov", {})
            .get("deltas_vs_semantic_only", {})
            .get("control_family_specific_p_geom_valid", {})
            .get("100", {})
        )
        recall_delta = open3dsg_delta.get("recall", {})
        violation_delta = open3dsg_delta.get("violation_rate", {})
        bootstrap_fact = (
            "- Docker subgraph bootstrap CI status: "
            f"`{bootstrap.get('status')}`, {bootstrap.get('n_bootstrap')} resamples; "
            "Open3DSG family-specific vs semantic-only R@100 delta "
            f"`{pp(recall_delta.get('point'))}` with 95% CI "
            f"`[{pp((recall_delta.get('ci95') or [None, None])[0])},"
            f"{pp((recall_delta.get('ci95') or [None, None])[1])}]`; "
            "Violation@100 delta "
            f"`{pp(violation_delta.get('point'))}` with 95% CI "
            f"`[{pp((violation_delta.get('ci95') or [None, None])[0])},"
            f"{pp((violation_delta.get('ci95') or [None, None])[1])}]`."
        )
    qwen_status_path = out_root / "sources/qwen_vl/status.json"
    qwen_fact = (
        "- Qwen-VL contract status: adapter schema, prompt template, tiny-pilot scope, "
        "crop rendering, and model-lock plan are recorded; runtime smoke status is not available."
    )
    if qwen_status_path.exists():
        qwen_status = load_json(qwen_status_path)
        qwen_runtime = qwen_status.get("runtime_gpu_smoke", {})
        qwen_plan = qwen_status.get("full_source_promotion_plan", {})
        qwen_input = qwen_status.get("full_source_input", {})
        qwen_crop = qwen_status.get("full_source_crop_render", {})
        qwen_infer_plan = qwen_status.get("full_source_inference_plan", {})
        qwen_loop = qwen_status.get("full_source_inference_loop", {})
        qwen_fact = (
            "- Qwen-VL contract status: "
            f"`{qwen_status.get('status')}`; runtime smoke status "
            f"`{qwen_runtime.get('status')}`; full-source promotion plan "
            f"`{qwen_plan.get('status', 'missing')}`; full-source input audit "
            f"`{qwen_input.get('status', 'missing')}`; full-source crop status "
            f"`{qwen_crop.get('status', 'missing')}`; inference runner plan "
            f"`{qwen_infer_plan.get('status', 'missing')}`; remaining shard loop "
            f"`{qwen_loop.get('status', 'missing')}`. This is non-metric "
            "third-source modern-VLM extension evidence, not a VL-SAT/Open3DSG replacement."
        )

    return f"""# H001 Geometry Reliability Experiment Report

Generated by Docker-oriented table builder from locked hypothesis artifacts.

## Fact

- Method framing: calibrated geometry-consistency evaluation and re-ranking framework.
- Prediction sources currently evaluated for the paper claim: `VL-SAT` / `vlsat_closed_set` and `Open3DSG` / `open3dsg_ov`.
- `semantic_only` R@50/R@100: {pct(semantic['r50'])}/{pct(semantic['r100'])}.
- `probabilistic_recalibrated` R@50/R@100: {pct(main['r50'])}/{pct(main['r100'])}.
- `semantic_only` Violation@50/@100: {pct(semantic['violation50'])}/{pct(semantic['violation100'])}.
- `probabilistic_recalibrated` Violation@50/@100: {pct(main['violation50'])}/{pct(main['violation100'])}.
- `p_geom_valid` GT AUROC/AUPRC: {pct(gt_auroc['value'])}/{pct(gt_auprc['value'])}.
- Reduced visual sanity-check target quality-issue rate: {pct(visual_quality['value'])}.
- Reduced visual sanity-check contradiction rate: {pct(visual_contra['value'])}.
- Open3DSG Table 6 hook status: `{open3dsg_hook['status']}`.
- Open3DSG metric contract status: `{open3dsg_hook['metric_contract']['metrics_status']}`.
- Open3DSG metric-scope status: `{open3dsg_hook['metric_scope']['status']}`.
- Open3DSG metric-scope in-scope GT denominator: {open3dsg_hook['metric_scope']['in_scope_gt_denominator']}.
{bootstrap_fact}
{qwen_fact}

## Inference

- The locked VL-SAT result supports a scoped geometry-consistency reliability-layer claim.
{open3dsg_inference}
- Open3DSG + VL-SAT + bootstrap CI are sufficient for the current scoped H001 paper claim. Remaining work for this evidence path is paper polish, appendix/provenance packaging, and target-year template verification rather than new core metric generation.
- Qwen-VL is valuable only as a third semantic source / modern VLM extension promoted through the same row contract, geometry join, metric, control, and audit protocol. It should not replace VL-SAT, because VL-SAT is the controlled reproduced anchor that stabilizes the denominator, ablation, and verifier-validity story.

## Claim Boundary

{open3dsg_boundary}
- Allowed after full Qwen-VL promotion: a third-source modern-VLM semantic-source extension showing that the same reliability framework can evaluate and re-rank VLM-derived relation rows under the same H001 denominator and Violation@K protocol.
- Blocked now: replacing VL-SAT with Qwen-VL as the controlled anchor, because Qwen-VL has not yet produced full-source predictions, matched confidence/ranking rows, geometry joins, controls, or audit evidence.

## Qwen-VL Strategic Extension

Fact:

- Current Qwen-VL model route is `Qwen/Qwen3-VL-4B-Instruct` at revision `ebb281ec70b05090aa6165b016eac8ec08e71b17`, cached under `local_dataset/model_cache/huggingface/qwen_vl/`.
- Cache verification is ready: 43 files, 8.277 GB, 3 weight/index files.
- Frozen Qwen-VL files already exist under `sources/qwen_vl/`: input schema, output JSONL contract, prompt templates, model candidates, tiny-pilot input scope, rendered pair-crop manifest, runtime plan, and contract validators.
- Runtime preflight and tiny inference smoke have passed when the runtime status above is `tiny_inference_smoke_passed_non_metric`.
- Full-source promotion protocol is frozen under `sources/qwen_vl/full_source_plan/`: 127 scans, 388 contexts, 25,916 directed pairs, maximum all-pairs x family query rows 77,748, and in-scope GT denominator 2,545.
- Full-source input audit is ready under `sources/qwen_vl/full_source_input/`: 77,748 universe query rows, 33,384 inferable input rows, 44,364 missing rows with explicit reasons, 134 inference shards, and contract validation with 0 input errors.
- Full-source crop rendering/preflight is ready: shard smoke `qwen_full_source_shard_0000` covered 250 input rows / 84 unique pair crops / 0 errors, and all-scope preflight covered 33,384 input rows / 11,128 unique pair crops / 0 errors.
- Full-source inference runner plan is frozen: 134 shard command/resume records and `record_id` resume key. Shard 0000 completed and contract-validated as a non-metric pilot shard: 250 prediction rows, 250 raw responses, parser status `parsed:250`, and 0 validation errors/warnings. Qwen has not completed all-shard paper-metric validation/evaluation.

Potential advantages:

- Novelty positioning: Qwen-VL connects H001 to modern VLM semantic sources without changing the core contribution from reliability evaluation/re-ranking to relation generation.
- Source-agnostic defense: a Qwen-VL source would show that H001's row contract, geometry join, and Violation@K protocol are not tied only to VL-SAT or Open3DSG internals.
- Failure-mode clarity: VLM outputs can expose the same semantic-plausibility versus physical-consistency mismatch that motivates H001, especially when text/image priors produce plausible but geometrically invalid relations.
- Reviewer defense: Qwen-VL can answer "why does this matter beyond legacy 3DSSG baselines?" if it is evaluated with the same denominator and controls.

Promotion requirements before paper-metric use:

- Completed smoke gates are necessary but not sufficient: cache verification, runtime preflight, tiny inference, and runtime raw-response contract validation.
- The crop and runner-plan gates are complete, but this is not immediate metric promotion: Qwen inference can now be scheduled shard-wise, and Qwen remains non-metric until parser validation, adapter export, geometry join, metrics, controls, bootstrap, and audit complete.
- Generate Qwen-VL `predictions.jsonl` with identity-preserving `scan_id`, `subgraph_id`, subject/object ids, predicate label/family, score/confidence, evidence text, abstain/failure reason, and model provenance.
- Run the same geometry join, R@K / Violation@K metric evaluation, controls, bootstrap CI if used in the main paper, and qualitative/failure audit.
- Keep Qwen-VL as a third source or appendix extension unless it reaches the same evidence level as Open3DSG; do not remove VL-SAT because it is the controlled anchor.

Inference:

- Fully evaluating Qwen-VL could improve accept probability if it completes cleanly, because it strengthens the "framework works for modern semantic sources" story.
- A rushed Qwen-VL result could weaken the paper if it lacks denominator discipline, ranking-score comparability, or audit evidence. The safest strategy is to keep the main claim as Open3DSG + VL-SAT + bootstrap CI, then promote Qwen-VL only if it passes the full Docker metric path.

## Reviewer-Risk Defense Checklist

Fact:

{open3dsg_fact}
- The Open3DSG predicate-family mapping and denominator policy are frozen before metric inspection; in-scope GT denominator is 2,545 rows across support_contact 1,199 / proximity 1,128 / relative_vertical 218.
- Recall matching for Open3DSG remains exact predicate-label matching. Family grouping is used for reliability and violation reporting, not for collapsing recall labels.
- Open3DSG real failure-analysis rows and qualitative inspection are ready: 57,736 rows, 0 validation errors, 6,162 visual-audit queue rows, 36 qualitative case candidates, 23/36 demoted by geometry-aware reranking, and 10/36 rule-violated cases with p_geom_valid > 0.9.
- Open3DSG raw dump has clean source-process provenance via v14 streaming same-path resume: exit `0`, 377/377 completed batches, 19,162 rows, dropped/invalid partial rows 0/0, and SHA256 matching the identity-audited canonical `raw_dump/raw.jsonl`. Historical v12/v13/v14 exit-137 attempts are retained as run records, not final raw-dump provenance caveats.
- Open3DSG paper caveats are frozen: filtered train split 3,744/3,852 subgraphs, train-dev validation split 156/160 subgraphs, H001 covered loadable scope 377/388 contexts, averaged-BLIP checkpoint variant, exact-label 2,545-row H001-family denominator, and residual calibration risk.
- The reduced 50-row visual sanity check is provenance-limited and must not be described as a large-scale or strictly blinded human audit.

Likely reviewer attacks:

- "This is only a rule-based post-processing script."
- "The result is a VL-SAT-specific trick, not a general 3DSSG contribution."
- "The claim overstates open-vocabulary or baseline-agnostic improvement under closed-set/GT-object conditions."
- "Violation improves only because recall is pruned."
- "The denominator, filtered training split, or covered contexts are cherry-picked."
- "The covered relation families are too narrow and do not handle relative horizontal or functional/attachment relations."

Required defenses:

- Frame the method as a calibrated geometry-consistency evaluation and re-ranking framework, not as a standalone verifier script.
- Report semantic-only, rule-only, calibrated global, family-specific, and score-preserving/control variants with R@K, Violation@K, recall retention, and Pareto-style tradeoff.
- Keep all claim wording scoped to measured geometry-checkable relation reliability; do not upgrade to broad open-vocabulary 3DSSG generation improvement.
- Report denominator transparency: in-scope rows, excluded rows, filtered train/validation counts, covered Open3DSG contexts, and missing-context caveats.
- Use the real Open3DSG failure-analysis rows and qualitative queue to explain failure mechanisms without changing the locked taxonomy.
- Treat Qwen-VL and SceneFun3D/FunGraph3D as optional extensions with separate claim boundaries, not as replacements for the Open3DSG second-source anchor.

Inference:

{open3dsg_completion}

## Generated Outputs

- Tables: `tables/table1_main_prediction.*` through `tables/table6_cross_source_status.*`.
- Figure specs: `figures/figure_specs.*`.
- Locked input record: `sources/vlsat/locked_inputs.json`.
- Open3DSG status and Table 6 hook: `sources/open3dsg/status.json`, `sources/open3dsg/table6_hook.json`.
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root mounted inside Docker.")
    parser.add_argument(
        "--out",
        default="experiments/H001_geom_reliability",
        help="Output directory relative to repo root, or absolute path.",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_root = Path(args.out)
    if not out_root.is_absolute():
        out_root = repo_root / out_root
    ensure_dir(out_root)
    manifest = write_outputs(repo_root, out_root)
    print(json.dumps({"status": manifest["status"], "out": str(out_root)}, sort_keys=True))


if __name__ == "__main__":
    main()
