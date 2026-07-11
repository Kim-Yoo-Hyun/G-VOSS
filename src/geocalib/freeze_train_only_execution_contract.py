#!/usr/bin/env python3
"""Freeze exact train-only H001 score and control execution before source inference."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--fit-manifest", type=Path, required=True)
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
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    paths = {name: resolve(root, value) for name, value in {
        "protocol": args.protocol, "models": args.models, "fit_manifest": args.fit_manifest,
    }.items()}
    out = resolve(root, args.out)
    if out.exists():
        raise FileExistsError(f"refusing_to_replace_frozen_contract:{out}")
    protocol = json.loads(paths["protocol"].read_text(encoding="utf-8"))
    models = json.loads(paths["models"].read_text(encoding="utf-8"))
    fit = json.loads(paths["fit_manifest"].read_text(encoding="utf-8"))
    evaluator = root / "src/geocalib/run_train_only_evaluation.py"
    source_config = root / "configs/h001/3dssg_full_l160_internal_dev.yaml"
    validations = {
        "protocol_frozen": protocol.get("status") == "protocol_frozen_before_strict_calibration_and_internal_dev_inference",
        "strict_fit_ready": fit.get("status") == "strict_train_only_models_ready_pre_internal_dev_source_metrics",
        "zero_final_rows_in_fit": fit.get("validations", {}).get("zero_final_validation_rows") is True,
        "strict_model_schema": models.get("schema_version") == "h001_strict_train_only_calibrators_v1",
        "family_models_exact": set(models.get("family_models", {})) == {"support_contact", "proximity", "relative_vertical"},
        "factor_models_exact": set(models.get("factor_models", {})) == {"M_T", "M_G", "M_add", "M_int"},
        "evaluator_exists": evaluator.is_file(),
        "source_config_exists": source_config.is_file(),
    }
    payload = {
        "schema_version": "h001_train_only_execution_contract_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "execution_contract_frozen_pre_internal_dev_source_inference" if all(validations.values()) else "blocked_execution_contract",
        "classification": protocol["classification"],
        "default": {
            "compatibility": "family_specific strict train-only logistic C_e",
            "score": "Z_e * C_e",
            "implementation": "semantic ranking_score multiplied by family_specific compatibility",
            "lambda": 1.0,
            "selection": "theory-driven frozen default; internal-dev may only accept or reject it",
        },
        "comparators_all_reported_no_winner_promotion": protocol["comparators_all_reported_no_winner_promotion"],
        "rank_fusions": {
            "rank_average_family": "0.5*(within-context semantic percentile + within-context family compatibility percentile)",
            "rrf_c60": "1/(60+within-context semantic rank)+1/(60+within-context family compatibility rank)",
        },
        "controls": {
            "wrong_T_on_GT_relative_vertical": "GT relative_vertical rows only; endpoints and raw G fixed; higher/lower predicate inverted; aligned interactions recomputed",
            "close_by_swap": "exact subject/object swap with predicate unchanged; absolute compatibility difference",
            "vertical_inverse_equivariance": "exact subject/object swap plus higher<->lower; absolute compatibility difference",
            "wrong_pair_geometry_continuity": "GT rows only; replace raw G by the next lexicographic directed pair in the same subgraph under a cyclic shift; keep T fixed",
            "support_contact_endpoint_swap": "prohibited; no blanket transform without exact predicate inverse and geometry rule",
        },
        "evaluation": {
            "ks": [5, 10, 20, 50, 100], "primary_k": 100,
            "internal_dev": {"contexts": 354, "gt": 2730, "bootstrap": 1000, "seed": 20260711},
            "final_validation": {"contexts": 548, "gt": 3972, "bootstrap": 1000, "seed": 20260712},
            "context_inclusion": "all contexts; GT presence never used for ranking/filtering/routing",
            "candidate_policy": "actual candidate count only; no synthetic padding",
        },
        "validations": validations,
        "hashes": {
            "protocol_sha256": sha256_file(paths["protocol"]), "models_sha256": sha256_file(paths["models"]),
            "fit_manifest_sha256": sha256_file(paths["fit_manifest"]), "evaluator_sha256": sha256_file(evaluator),
            "source_config_sha256": sha256_file(source_config),
        },
        "inputs": {name: relpath(root, path) for name, path in paths.items()},
        "docker_command": "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_execution_freeze",
    }
    write_json(out, payload)
    print(json.dumps({"status": payload["status"], "validations": validations, "out": relpath(root, out)}))
    return 0 if all(validations.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
