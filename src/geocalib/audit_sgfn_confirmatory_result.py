#!/usr/bin/env python3
"""Audit SGFN confirmatory outputs against the v3 frozen gates."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_ID = "sgfn_official_full_l160_confirmatory"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--coverage-audit", type=Path, required=True)
    parser.add_argument("--raw-manifest", type=Path, required=True)
    parser.add_argument("--checkpoint-audit", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    paths = {
        "metrics": resolve(root, args.metrics),
        "target": resolve(root, args.target),
        "adapter": resolve(root, args.adapter),
        "coverage_audit": resolve(root, args.coverage_audit),
        "raw_manifest": resolve(root, args.raw_manifest),
        "checkpoint_audit": resolve(root, args.checkpoint_audit),
    }
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_inputs:{missing}")
    metrics, target = load(paths["metrics"]), load(paths["target"])
    adapter, coverage_audit = load(paths["adapter"]), load(paths["coverage_audit"])
    raw, checkpoint = load(paths["raw_manifest"]), load(paths["checkpoint_audit"])
    source = metrics["sources"][SOURCE_ID]
    scope = source["overall_global"]
    semantic = scope["semantic_only"]["100"]
    main = scope["family_conditional_risk"]["100"]
    delta = scope["deltas_vs_semantic_only"]["family_conditional_risk"]["100"]
    recall_delta = delta["recall"]
    violation_delta = delta["violation_rate"]
    recall_gate = float(recall_delta["ci95"][0]) > -0.01
    validity_gate = float(violation_delta["ci95"][1]) < 0.0
    expected_conditions = {
        "semantic_only",
        "family_conditional_risk",
        "pooled_calibration",
        "geometry_only_family",
        "rank_average_fusion",
        "reciprocal_rank_fusion",
    }
    validations = {
        "target_v3_frozen": target.get("status") == "target_v3_frozen_pre_correct_checkpoint_pre_inference",
        "checkpoint_full_l160_compatible": checkpoint.get("status") == "checkpoint_compatible_full_l160",
        "raw_inference_ready": raw.get("status") == "sgfn_raw_inference_ready",
        "adapter_ready": adapter.get("status") == "sgfn_adapter_ready",
        "global_gt_denominator_3972": adapter.get("counts", {}).get("global_in_scope_gt_rows") == 3972,
        "no_missing_edge_synthesis": adapter.get("coverage", {}).get("missing_source_edges_synthesized") == 0,
        "all_nonself_pairs_covered": coverage_audit.get("validations", {}).get("no_nonself_source_pair_missing") is True,
        "eleven_self_gt_rows_retained_without_synthesis": coverage_audit.get("counts", {}).get("missing_self_relation_rows") == 11,
        "bootstrap_1000_seed_20260710": metrics.get("n_bootstrap") == 1000 and metrics.get("seed") == 20260710,
        "conditions_match_frozen_six": set(metrics.get("conditions", [])) == expected_conditions,
        "primary_k_100_present": "100" in scope["family_conditional_risk"],
    }
    family_gates: dict[str, Any] = {}
    for family, family_scope in source["within_family"].items():
        family_delta = family_scope["deltas_vs_semantic_only"]["family_conditional_risk"]["100"]
        family_gates[family] = {
            "delta_recall": family_delta["recall"],
            "delta_violation": family_delta["violation_rate"],
            "recall_guardrail_pass": float(family_delta["recall"]["ci95"][0]) > -0.01,
            "validity_gate_pass": float(family_delta["violation_rate"]["ci95"][1]) < 0.0,
        }
    strong_baselines: dict[str, Any] = {}
    for condition in ("rank_average_fusion", "reciprocal_rank_fusion"):
        values = scope[condition]["100"]
        vs_main = scope["deltas_vs_family_conditional_risk"][condition]["100"]
        same_recall_guardrail = float(vs_main["recall"]["ci95"][0]) > -0.01
        lower_violation_gate = float(vs_main["violation_rate"]["ci95"][1]) < 0.0
        strong_baselines[condition] = {
            "result": values,
            "paired_delta_vs_main": vs_main,
            "recall_guardrail_vs_main_pass": same_recall_guardrail,
            "lower_violation_vs_main_pass": lower_violation_gate,
            "joint_gate_vs_main_pass": same_recall_guardrail and lower_violation_gate,
        }
    execution_valid = all(validations.values())
    confirmatory_pass = execution_valid and recall_gate and validity_gate
    status = (
        "confirmatory_primary_gate_passed"
        if confirmatory_pass
        else "confirmatory_primary_gate_failed"
        if execution_valid
        else "blocked_confirmatory_execution_validation"
    )
    payload = {
        "schema_version": "h001_sgfn_confirmatory_decision_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_id": SOURCE_ID,
        "primary_k": 100,
        "primary_result": {
            "semantic_only": {
                "recall": semantic["recall"],
                "violation_rate": semantic["violation_rate"],
            },
            "family_conditional_risk": {
                "recall": main["recall"],
                "violation_rate": main["violation_rate"],
            },
            "paired_delta_vs_semantic": {
                "recall": recall_delta,
                "violation_rate": violation_delta,
            },
        },
        "frozen_gates": {
            "recall_guardrail": "delta_R_at_100_ci95_lower_gt_-0.01",
            "recall_guardrail_pass": recall_gate,
            "validity_gate": "delta_V_at_100_ci95_upper_lt_0",
            "validity_gate_pass": validity_gate,
            "joint_primary_gate_pass": confirmatory_pass,
        },
        "family_results": family_gates,
        "strong_baseline_results": strong_baselines,
        "execution_validations": validations,
        "coverage": adapter["coverage"],
        "counts": adapter["counts"],
        "inputs": {
            name: {"path": relpath(root, path), "sha256": sha256_file(path)}
            for name, path in paths.items()
        },
        "interpretation_boundary": {
            "exact_label_recall_is_confirmatory_for_sgfn_target_v3": execution_valid,
            "violation_is_frozen_geometry_verifier_derived": True,
            "independent_human_validity_still_required": True,
            "earlier_source_tables_remain_retrospective": True,
            "broad_sota_claim_authorized": False,
            "main_score_unique_or_dominant_claim_authorized": False,
            "strong_baseline_caveat": "rank-average fusion passes the same recall/lower-violation joint gate against the locked main score on SGFN",
        },
        "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_audit",
    }
    out = resolve(root, args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "gates": payload["frozen_gates"], "out": relpath(root, out)}))
    return 0 if execution_valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
