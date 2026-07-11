#!/usr/bin/env python3
"""Audit fresh-source execution and the pre-frozen joint framework gate."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_ID = "3dssg_official_full_l160_confirmatory"
FRAMEWORK_SCORES = ("family_conditional_risk", "rank_average_fusion")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--annotations", type=Path, required=True)
    parser.add_argument("--official-scans", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    paths = {name: resolve(root, value) for name, value in {
        "metrics": args.metrics,
        "target": args.target,
        "checkpoint": args.checkpoint,
        "raw": args.raw,
        "adapter": args.adapter,
        "coverage": args.coverage,
        "annotations": args.annotations,
        "official_scans": args.official_scans,
    }.items()}
    missing = [name for name, path in paths.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_audit_inputs:{missing}")
    data = {
        name: load(path)
        for name, path in paths.items()
        if name != "official_scans"
    }
    metrics = data["metrics"]
    annotation_scans = {
        str(row["scan"])
        for row in data["annotations"]["scans"]
    }
    official_scans = {
        line.strip()
        for line in paths["official_scans"].read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    scope = metrics["sources"][SOURCE_ID]["overall_global"]
    score_results: dict[str, Any] = {}
    for score in FRAMEWORK_SCORES:
        delta = scope["deltas_vs_semantic_only"][score]["100"]
        recall_pass = float(delta["recall"]["ci95"][0]) > -0.01
        violation_pass = float(delta["violation_rate"]["ci95"][1]) < 0.0
        score_results[score] = {
            "semantic_only": scope["semantic_only"]["100"],
            "score": scope[score]["100"],
            "paired_delta_vs_semantic": delta,
            "recall_guardrail_pass": recall_pass,
            "validity_gate_pass": violation_pass,
            "joint_gate_pass": recall_pass and violation_pass,
        }
    expected_conditions = {
        "semantic_only", "family_conditional_risk", "pooled_calibration",
        "geometry_only_family", "rank_average_fusion", "reciprocal_rank_fusion",
    }
    validations = {
        "target_frozen_before_download_and_inference": data["target"].get("status") == "target_frozen_pre_checkpoint_download_pre_inference",
        "checkpoint_staged": data["checkpoint"].get("status") == "3dssg_checkpoint_staged",
        "raw_inference_ready": data["raw"].get("status") == "3dssg_raw_inference_ready",
        "source_method_sgpn": data["raw"].get("source_method") == "sgpn",
        "adapter_ready": data["adapter"].get("status") == "3dssg_adapter_ready",
        "all_548_contexts_in_evaluation": data["adapter"].get("counts", {}).get("target_contexts") == 548,
        "official_validation_annotations_exactly_match_source_split_157": annotation_scans == official_scans and len(official_scans) == 157,
        "gt_denominator_3972": data["adapter"].get("counts", {}).get("global_in_scope_gt_rows") == 3972,
        "no_missing_edge_synthesis": data["adapter"].get("coverage", {}).get("missing_source_edges_synthesized") == 0,
        "all_nonself_pairs_covered": data["coverage"].get("validations", {}).get("no_nonself_source_pair_missing") is True,
        "eleven_self_gt_retained_without_synthesis": data["coverage"].get("counts", {}).get("missing_self_relation_rows") == 11,
        "locked_bootstrap": metrics.get("n_bootstrap") == 1000 and metrics.get("seed") == 20260710,
        "locked_conditions": set(metrics.get("conditions", [])) == expected_conditions,
    }
    execution_valid = all(validations.values())
    joint_framework_gate = execution_valid and all(value["joint_gate_pass"] for value in score_results.values())
    status = (
        "confirmatory_joint_framework_gate_passed" if joint_framework_gate
        else "confirmatory_joint_framework_gate_failed" if execution_valid
        else "blocked_confirmatory_execution_validation"
    )
    payload = {
        "schema_version": "h001_3dssg_confirmatory_decision_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "source_id": SOURCE_ID,
        "primary_k": 100,
        "score_results": score_results,
        "joint_framework_gate_pass": joint_framework_gate,
        "execution_validations": validations,
        "family_results": {
            family: {
                score: scope_family["deltas_vs_semantic_only"][score]["100"]
                for score in FRAMEWORK_SCORES
            }
            for family, scope_family in metrics["sources"][SOURCE_ID]["within_family"].items()
        },
        "interpretation_boundary": {
            "fresh_semantic_source_confirmatory": execution_valid,
            "fresh_dataset_confirmatory": False,
            "violation_is_frozen_verifier_derived": True,
            "independent_human_validity_for_this_source_available": False,
            "broad_sota_claim_authorized": False,
            "unique_formula_claim_authorized": False,
        },
        "inputs": {name: {"path": relpath(root, path), "sha256": sha256_file(path)} for name, path in paths.items()},
        "docker_command": "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm 3dssg_confirmatory_audit",
    }
    out = resolve(root, args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "joint_framework_gate_pass": joint_framework_gate, "score_results": score_results}))
    return 0 if execution_valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
