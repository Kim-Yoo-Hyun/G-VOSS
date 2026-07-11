#!/usr/bin/env python3
"""Lock the final H001 model and score hashes after internal-dev acceptance."""

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
    parser.add_argument("--execution-contract", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--internal-dev", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
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


def canonical_sha(payload: Any) -> str:
    value = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    paths = {name: resolve(root, value) for name, value in {
        "protocol": args.protocol, "execution_contract": args.execution_contract,
        "models": args.models, "internal_dev": args.internal_dev, "checkpoint": args.checkpoint,
    }.items()}
    out = resolve(root, args.out)
    if out.exists():
        raise FileExistsError(f"refusing_to_replace_final_lock:{out}")
    protocol, contract, metrics = (
        json.loads(paths[name].read_text(encoding="utf-8"))
        for name in ("protocol", "execution_contract", "internal_dev")
    )
    decision = metrics.get("default_product_decision", {}).get("decision")
    models_sha = sha256_file(paths["models"])
    evaluator = root / "src/geocalib/run_train_only_evaluation.py"
    validations = {
        "protocol_frozen": protocol.get("status") == "protocol_frozen_before_strict_calibration_and_internal_dev_inference",
        "execution_contract_frozen_pre_inference": contract.get("status") == "execution_contract_frozen_pre_internal_dev_source_inference",
        "models_unchanged_since_execution_freeze": models_sha == contract.get("hashes", {}).get("models_sha256"),
        "evaluator_unchanged_since_execution_freeze": sha256_file(evaluator) == contract.get("hashes", {}).get("evaluator_sha256"),
        "internal_dev_ready": metrics.get("status") == "internal_dev_evaluation_ready",
        "internal_dev_decision_binary": decision in {"accept", "reject"},
        "internal_dev_counts_exact": metrics.get("counts", {}).get("contexts") == 354 and metrics.get("counts", {}).get("gt_denominator") == 2730,
    }
    score_definition = {
        "method": "family_product", "formula": "semantic ranking_score * strict family-specific compatibility",
        "lambda": 1.0, "families": ["support_contact", "proximity", "relative_vertical"],
        "ks": [5, 10, 20, 50, 100], "primary_k": 100,
    }
    status_suffix = decision if decision in {"accept", "reject"} else "reject"
    payload = {
        "schema_version": "h001_train_only_final_lock_v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": f"final_method_locked_after_internal_dev_{status_suffix}" if all(validations.values()) else "blocked_final_method_lock",
        "classification": protocol["classification"],
        "internal_dev_decision": metrics.get("default_product_decision"),
        "final_evaluation_rule": "evaluate all frozen methods regardless of accept/reject; only an accepted default may support the framework claim; no repair after final results",
        "score_definition": score_definition,
        "hashes": {
            "models_sha256": models_sha, "score_definition_sha256": canonical_sha(score_definition),
            "protocol_sha256": sha256_file(paths["protocol"]), "execution_contract_sha256": sha256_file(paths["execution_contract"]),
            "internal_dev_summary_sha256": sha256_file(paths["internal_dev"]), "checkpoint_sha256": sha256_file(paths["checkpoint"]),
            "evaluator_sha256": sha256_file(evaluator),
        },
        "validations": validations,
        "inputs": {name: relpath(root, path) for name, path in paths.items()},
        "docker_command": "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm train_only_final_lock",
    }
    write_json(out, payload)
    print(json.dumps({"status": payload["status"], "internal_dev_decision": decision, "hashes": payload["hashes"], "out": relpath(root, out)}))
    return 0 if all(validations.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
