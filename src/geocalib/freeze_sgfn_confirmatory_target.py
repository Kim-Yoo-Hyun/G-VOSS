#!/usr/bin/env python3
"""Freeze the untouched SGFN full_l160 confirmatory source contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_sgfn_confirmatory_target_v1"
CODE_URL = "https://github.com/ShunChengWu/3DSSG"
CODE_COMMIT = "4b783ecdc6caba1515b361f8a0643d0c2d568f52"
CHECKPOINT_URL = "https://www.campar.in.tum.de/public_datasets/2023_cvpr_wusc/trained_models/SGFN_full_l20.zip"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--source-code",
        type=Path,
        default=Path("local_dataset/SceneGraphFusion_code/3DSSG"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/confirmatory_evaluation/sgfn_target_v1"),
    )
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


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def protocol(payload: dict[str, Any]) -> str:
    return f"""# SGFN Untouched Confirmatory Source Contract

Frozen at UTC: `{payload['created_at_utc']}`  
Status: `{payload['status']}`  
Source id: `sgfn_official_full_l160`

## Selection rationale

SGFN is selected because the official 3DSSG framework exposes a 160-object,
26-relation `full_l160` configuration and a currently accessible official
checkpoint archive. It has not previously supplied H001 source metrics. SGFormer
was screened but not selected because its official repository does not contain
the documented config/checkpoint required for a reproducible untouched run.

This selection was frozen before downloading or opening the SGFN checkpoint and
before any SGFN prediction or H001 metric was produced.

## Immutable source provenance

- Official code: `{CODE_URL}` at commit `{CODE_COMMIT}`.
- Source configuration: `configs/config_SGFN_full_l160.yaml`.
- Official checkpoint archive: `{CHECKPOINT_URL}`.
- Source setup: GT 3RScan instances, 160 object labels, 26 relation labels,
  multi-label relation prediction.
- Evaluation target: the official source validation scan list, mapped by scan
  and instance identity into the already frozen 548 H001 validation subgraphs.

The checkpoint archive must contain weights compatible with the full_l160
configuration. If it does not, this target becomes blocked; another checkpoint
or trained variant cannot be substituted under this protocol version.

## Adapter and denominator contract

1. Run SGFN once on its source-native full validation scans.
2. Export every available directed edge and every non-`none` relation score,
   preserving scan id and subject/object instance ids.
3. Project a full-scan edge score into each frozen H001 subgraph containing that
   directed object pair. Do not synthesize scores for source-missing edges.
4. Use the frozen H001 exact-label GT denominator of 3,972 in-scope relation
   rows. Report source scan coverage, subgraph coverage, pair coverage, and GT
   coverage separately.
5. Join geometry by the same identity key and run the locked main score without
   changing calibrator, family map, K, thresholds, or fusion definitions.

## Locked analysis

- Main: `semantic_score * p_geom_valid_family`.
- Comparators: semantic-only, pooled calibration, family geometry-only,
  rank-average fusion, and Reciprocal Rank Fusion with `c=60`.
- Families: `support_contact`, `proximity`, `relative_vertical`.
- K: `{{5,10,20,50,100}}`, primary K=100.
- Primary validity direction: paired delta V@100 below zero.
- Recall guardrail: paired delta R@100 95% CI lower bound above `-0.01`.
- Bootstrap: 1,000 subgraph resamples with fixed seed `20260710`.

All SGFN metrics are reported regardless of direction. Failure of the primary
gate does not permit score, family, K, checkpoint, or coverage-policy changes.

## Promotion boundary

The run is confirmatory for this source contract only if checkpoint audit,
source-native inference, adapter identity checks, geometry coverage reporting,
and paired CI all pass. It does not convert the earlier VL-SAT/Open3DSG/Qwen
tables into confirmatory evidence and does not authorize a broad SOTA claim.
"""


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    code_root = resolve(root, args.source_code)
    out = resolve(root, args.out)
    base_manifest = root / "experiments/H001_geom_reliability/confirmatory_evaluation/frozen_v1/manifest.json"
    required = {
        "base_confirmatory_manifest": base_manifest,
        "source_config": code_root / "configs/config_SGFN_full_l160.yaml",
        "dataset_config": code_root / "configs/dataset/config_base_3RScan_full_l160.yaml",
        "method_config": code_root / "configs/method/config_base_SGFN.yaml",
        "validation_scans": code_root / "files/cvpr/validation_scans.txt",
        "h001_ground_truth": root / "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/ground_truth.jsonl",
        "family_model": root / "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json",
    }
    missing = [name for name, path in required.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_target_freeze_inputs:{missing}")
    head_path = code_root / ".git/HEAD"
    if not head_path.exists():
        raise FileNotFoundError(f"missing_git_head:{head_path}")
    head_value = head_path.read_text(encoding="utf-8").strip()
    if head_value.startswith("ref: "):
        ref_path = code_root / ".git" / head_value.removeprefix("ref: ")
        actual_commit = ref_path.read_text(encoding="utf-8").strip()
    else:
        actual_commit = head_value
    base = json.loads(base_manifest.read_text(encoding="utf-8"))
    validations = {
        "base_protocol_waited_for_target": base.get("confirmatory_target", {}).get("fresh_source_metric_target") is None,
        "source_code_commit_matches": actual_commit == CODE_COMMIT,
        "source_required_files_hashed_at_freeze": all(required[name].exists() for name in ("source_config", "dataset_config", "method_config", "validation_scans")),
        "checkpoint_not_downloaded_at_freeze": not (root / "local_dataset/SceneGraphFusion_checkpoints/SGFN_full_l20.zip").exists(),
        "locked_h001_scope_present": all(required[name].exists() for name in ("h001_ground_truth", "family_model")),
    }
    status = "target_frozen_pre_checkpoint_pre_inference" if all(validations.values()) else "blocked_target_freeze_validation"
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "target": {
            "source_id": "sgfn_official_full_l160",
            "method": "SGFN",
            "task": "3DSSG predicate source with GT instances",
            "code_url": CODE_URL,
            "code_commit": CODE_COMMIT,
            "checkpoint_url": CHECKPOINT_URL,
            "checkpoint_expected_http_content_length": 84830654,
            "checkpoint_compatibility_gate": "archive must contain official weights compatible with config_SGFN_full_l160.yaml",
            "source_validation_split": "official files/cvpr/validation_scans.txt",
            "adapter_target": "frozen H001 548 validation subgraphs by scan+instance pair identity",
        },
        "locked_analysis": {
            "families": ["support_contact", "proximity", "relative_vertical"],
            "ks": [5, 10, 20, 50, 100],
            "primary_k": 100,
            "main_score": "semantic_score * p_geom_valid_family",
            "comparators": ["semantic_only", "pooled_calibration", "geometry_only_family", "rank_average_fusion", "reciprocal_rank_fusion_c60"],
            "bootstrap_unit": "H001 subgraph_id",
            "n_bootstrap": 1000,
            "seed": 20260710,
            "recall_guardrail": "delta_R_at_100_ci95_lower_gt_-0.01",
            "validity_gate": "delta_V_at_100_ci95_upper_lt_0",
        },
        "coverage_policy": {
            "missing_source_edges": "not synthesized; reported as missing coverage",
            "missing_subgraphs": "retained in GT denominator with zero matching predictions",
            "reported_denominators": ["source validation scans", "H001 subgraphs", "directed pairs", "in-scope GT rows"],
            "posthoc_recovery_forbidden": True,
        },
        "validations": validations,
        "inputs": {
            name: {"path": relpath(root, path), "sha256": sha256_file(path)}
            for name, path in required.items()
        },
        "next_gates": [
            "download_and_checksum_checkpoint_archive",
            "audit_archive_for_full_l160_compatibility",
            "freeze_pinned_Docker_runtime_and_source_export_patch",
            "source_native_preflight",
            "source_inference_and_raw_export",
            "identity_preserving_H001_adapter",
            "geometry_join_metrics_and_paired_CI",
        ],
        "claim_boundary": {
            "confirmatory_for_locked_sgfn_source_only": True,
            "broad_sota_or_all_source_claim": False,
            "score_or_checkpoint_substitution_after_results": False,
        },
        "docker_command": "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm sgfn_confirmatory_target_freeze",
    }
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "manifest.json", payload)
    (out / "protocol.md").write_text(protocol(payload), encoding="utf-8")
    print(json.dumps({"status": status, "target": payload["target"]["source_id"], "out": relpath(root, out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
