#!/usr/bin/env python3
"""Freeze the Qwen-VL full-source promotion protocol without running inference."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_qwen_vl_full_source_promotion_plan_v1"
TARGET_FAMILIES = ["support_contact", "proximity", "relative_vertical"]
PRIMARY_MODEL_ID = "Qwen/Qwen3-VL-4B-Instruct"
PRIMARY_MODEL_REVISION = "ebb281ec70b05090aa6165b016eac8ec08e71b17"
PRIMARY_MODEL_LOCAL_DIR = (
    "local_dataset/model_cache/huggingface/qwen_vl/"
    "Qwen3-VL-4B-Instruct/ebb281ec70b05090aa6165b016eac8ec08e71b17"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--qwen-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl"),
    )
    parser.add_argument(
        "--open3dsg-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg"),
    )
    parser.add_argument(
        "--bootstrap-summary",
        type=Path,
        default=Path("results/h001_geom_reliability/bootstrap_ci/summary.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/full_source_plan"),
    )
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def artifact_status(path: Path) -> str:
    payload = load_json(path)
    return str(payload.get("status", "missing"))


def qwen_status(qwen_root: Path) -> dict[str, Any]:
    status = load_json(qwen_root / "status.json")
    tiny = load_json(qwen_root / "runtime_smoke/tiny_inference/manifest.json")
    cache = load_json(qwen_root / "runtime_smoke/cache/manifest.json")
    validation = load_json(qwen_root / "runtime_smoke/tiny_inference/validation/manifest.json")
    return {
        "status_file": status.get("status", "missing"),
        "cache": cache.get("status", "missing"),
        "runtime_gpu_smoke": tiny.get("status", "missing"),
        "runtime_contract_validation": validation.get("status", "missing"),
        "tiny_attempted_rows": tiny.get("tiny_inference", {}).get("attempted_rows"),
        "tiny_output_rows": tiny.get("tiny_inference", {}).get("output_rows"),
    }


def open3dsg_scope(open3dsg_root: Path) -> dict[str, Any]:
    raw_identity = load_json(open3dsg_root / "raw_dump_identity/manifest.json")
    metric_scope = load_json(open3dsg_root / "metric_scope/manifest.json")
    metric_contract = load_json(open3dsg_root / "metric_join_contract/metrics.json")
    pairs = raw_identity.get("scope", {}).get("directed_pairs")
    denominator = metric_scope.get("ground_truth_denominator", {})
    families = sorted(denominator.get("target_family_counts", {}).keys()) or TARGET_FAMILIES
    query_upper_bound = pairs * len(TARGET_FAMILIES) if isinstance(pairs, int) else None
    return {
        "raw_identity_status": raw_identity.get("status", "missing"),
        "selected_scans": raw_identity.get("scope", {}).get("selected_scans"),
        "contexts": raw_identity.get("scope", {}).get("contexts"),
        "directed_pairs": pairs,
        "max_family_query_rows_if_all_pairs_x_families": query_upper_bound,
        "metric_scope_status": metric_scope.get("status", "missing"),
        "in_scope_gt_denominator": denominator.get("in_scope_gt_denominator"),
        "target_family_counts": denominator.get("target_family_counts"),
        "metric_contract_prediction_rows": metric_contract.get("counts", {}).get("predictions"),
        "families": families,
    }


def build_protocol(scope: dict[str, Any], qwen: dict[str, Any], bootstrap: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "role": "third_semantic_source_modern_vlm_extension",
        "claim_boundary": {
            "allowed": [
                "Show that H001 can ingest, evaluate, and geometry-rerank a modern VLM-derived semantic relation source.",
                "Report Qwen-VL as a third semantic source or appendix extension when the full Docker metric path is complete.",
            ],
            "not_allowed": [
                "Replace VL-SAT as the controlled reproduced anchor.",
                "Replace Open3DSG as the main open-vocabulary relation-source case study.",
                "Claim broad open-vocabulary 3DSSG generation improvement from smoke or subset-only evidence.",
                "Use Qwen-VL outputs as a paper metric without full candidate-universe, denominator, controls, bootstrap, and audit records.",
            ],
        },
        "current_gate": {
            "status": "protocol_frozen_no_full_metric_run",
            "completed_before_this_gate": qwen,
            "required_before_inference": [
                "Generate and audit a full-source Qwen input manifest.",
                "Verify pair crops and target object boxes for every promoted input row.",
                "Record exact row count, missing-row policy, and shard list before model inference.",
            ],
        },
        "scope_policy": {
            "primary_scope": "H001 held-out GT-object closed-set contexts used by the Open3DSG source path.",
            "families": TARGET_FAMILIES,
            "source_role": "third source; do not alter VL-SAT/Open3DSG main result tables unless Qwen reaches the same evidence standard.",
            "candidate_universe_rule": (
                "For metric promotion, do not query only GT-positive pairs. Build a complete directed-pair candidate universe "
                "inside the frozen H001 context scope, then query each target predicate family or explicitly record a lossless "
                "single-prompt alternative before inference."
            ),
            "current_identity_upper_bound": {
                "selected_scans": scope.get("selected_scans"),
                "contexts": scope.get("contexts"),
                "directed_pairs": scope.get("directed_pairs"),
                "max_family_query_rows_if_all_pairs_x_families": scope.get(
                    "max_family_query_rows_if_all_pairs_x_families"
                ),
                "in_scope_gt_denominator": scope.get("in_scope_gt_denominator"),
                "target_family_counts": scope.get("target_family_counts"),
            },
            "hard_denominator_rule": (
                "Report Qwen denominator separately if crop coverage or parsing coverage is below the Open3DSG covered-loadable scope; "
                "never silently inherit Open3DSG denominators after dropping Qwen rows."
            ),
        },
        "runtime_policy": {
            "model_id": PRIMARY_MODEL_ID,
            "model_revision": PRIMARY_MODEL_REVISION,
            "local_dir": PRIMARY_MODEL_LOCAL_DIR,
            "prompt_version": "semantic_only_v1",
            "decoding": {
                "temperature": 0.0,
                "top_p": 1.0,
                "max_new_tokens": 256,
                "seed": 20260527,
                "do_sample": False,
            },
            "sharding": {
                "required": True,
                "resume_key": "record_id",
                "recommended_shard_size_rows": 250,
                "log_policy": "one timestamped log per shard or shard loop under logs/",
                "exit_policy": "one exit file per long-running tmux/background job",
            },
            "background_task_rule": (
                "Full Qwen inference is long-running GPU work; launch in tmux/background and return to paper/reproducibility work."
            ),
        },
        "adapter_policy": {
            "input_schema": "h001_qwen_vl_input_v2",
            "output_schema": "h001_qwen_vl_prediction_v2",
            "prediction_baseline_name": "qwen_vl_semantic_source",
            "semantic_score": "Use parsed model confidence when available; otherwise use rank-derived score and record warning.",
            "abstention": [
                "answer_is_visible=false or empty predictions produces a retained row with no prediction candidates.",
                "unparseable/refused/runtime_error rows are retained for coverage reporting and produce no prediction candidates.",
                "Do not impute predictions from geometry or ground truth.",
            ],
            "non_leakage": [
                "Semantic-only Qwen prompt must not include p_geom_valid, verifier labels, GT labels, or geometry-derived pass/fail text.",
                "The geometry-aware diagnostic prompt is appendix/debug only and cannot be mixed with semantic-only metric rows.",
            ],
        },
        "evaluation_policy": {
            "must_run_before_paper_metric": [
                "qwen full-source input manifest audit",
                "Qwen Docker inference shards",
                "runtime raw-response contract validation",
                "Qwen prediction-row adapter export",
                "same H001 geometry join",
                "same R@K and Violation@K evaluator",
                "same control set where applicable",
                "subgraph bootstrap CI if Qwen appears in a result table",
                "qualitative/failure audit",
            ],
            "metrics": [
                "R@50",
                "R@100",
                "Violation@50",
                "Violation@100",
                "parser success rate",
                "abstention rate",
                "crop/input coverage",
                "geometry-join coverage",
            ],
            "conditions": [
                "qwen_vl_semantic_only",
                "qwen_vl_probabilistic_recalibrated",
                "qwen_vl_family_specific_p_geom_valid",
                "qwen_vl_rule_verified_point_subtype",
            ],
            "controls": [
                "p_geom_valid_only",
                "distance_only",
                "shuffled_geometry",
                "wrong_pair_geometry",
                "rank_only_no_self_confidence",
            ],
            "bootstrap": {
                "required_if_reported_in_table": True,
                "unit": bootstrap.get("bootstrap_unit", "subgraph_id"),
                "n_bootstrap": bootstrap.get("n_bootstrap", 1000),
                "seed": bootstrap.get("seed", 20260526),
            },
            "table_policy": (
                "If complete, report Qwen as a third-source extension table or appendix table. Main Open3DSG/VL-SAT claims remain intact."
            ),
        },
        "audit_policy": {
            "minimum_before_main_text": [
                "At least 50 deterministic qualitative checks or a justified smaller complete-case audit if fewer cases exist.",
                "Parser-failure and abstention examples.",
                "Geometry-demoted VLM semantic-plausibility failures.",
                "Crop ambiguity / object-localization failure cases.",
            ],
            "failure_taxonomy_additions": [
                "vlm_crop_ambiguity",
                "vlm_object_box_misattribution",
                "vlm_semantic_prior_overrides_geometry",
                "vlm_abstains_despite_visible_pair",
                "vlm_json_parse_or_confidence_failure",
            ],
        },
        "promotion_decision_rule": {
            "appendix_extension_ok": (
                "Full metric path completes with transparent denominator and no hidden row drops, even if performance is not better than Open3DSG."
            ),
            "main_text_extension_ok": (
                "Qwen shows the same violation-reduction pattern under bootstrap CI while preserving credible recall, and audit supports the same failure mechanism."
            ),
            "do_not_promote": [
                "Only tiny smoke results exist.",
                "Only GT-positive or manually selected rows are evaluated.",
                "Parser/crop coverage is too low to defend the denominator.",
                "Geometry reranking improves only by deleting most relation candidates without transparent recall accounting.",
            ],
        },
    }


def build_commands(repo_root: Path, out_dir: Path) -> str:
    rel_out = relpath(repo_root, out_dir)
    return f"""# Qwen-VL Full-Source Promotion Commands

Current command that freezes this plan:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm qwen_vl_full_source_plan'
```

Outputs:

- `{rel_out}/manifest.json`
- `{rel_out}/protocol.json`
- `{rel_out}/report.md`
- `{rel_out}/commands.md`

Future implementation order. These services are intentionally not run by this
plan and should be implemented only after the protocol is accepted:

1. `qwen_vl_full_source_input`: build the complete H001 directed-pair/family input manifest and crop audit.
2. `qwen_vl_full_source_infer`: run Qwen inference in resumable shards under `tmux`, with timestamped `logs/`.
3. `qwen_vl_full_source_validate`: validate raw responses against `h001_qwen_vl_prediction_v2`.
4. `qwen_vl_adapter_export`: convert parsed Qwen rows into H001 `predictions.jsonl`.
5. `qwen_vl_geometry_join`: run the existing H001 geometry join.
6. `qwen_vl_metric_eval`: run the existing R@K / Violation@K evaluator and controls.
7. `qwen_vl_bootstrap_ci`: run subgraph bootstrap CI if Qwen appears in a paper table.
8. `qwen_vl_failure_audit`: generate deterministic qualitative/failure cases.
"""


def build_report(manifest: dict[str, Any], protocol: dict[str, Any]) -> str:
    scope = protocol["scope_policy"]["current_identity_upper_bound"]
    lines = [
        "# Qwen-VL Full-Source Promotion Plan",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Role",
        "",
        "Qwen-VL is frozen as a third semantic source / modern VLM extension. It is not a replacement for VL-SAT or Open3DSG.",
        "",
        "## Current Evidence",
        "",
        f"- cache status: `{manifest['qwen_status']['cache']}`",
        f"- tiny runtime smoke: `{manifest['qwen_status']['runtime_gpu_smoke']}`",
        f"- runtime contract validation: `{manifest['qwen_status']['runtime_contract_validation']}`",
        f"- tiny attempted/output rows: `{manifest['qwen_status']['tiny_attempted_rows']}` / `{manifest['qwen_status']['tiny_output_rows']}`",
        "",
        "## Frozen Metric Scope",
        "",
        f"- selected scans: `{scope['selected_scans']}`",
        f"- contexts: `{scope['contexts']}`",
        f"- directed pairs: `{scope['directed_pairs']}`",
        f"- max all-pairs x family query rows: `{scope['max_family_query_rows_if_all_pairs_x_families']}`",
        f"- in-scope GT denominator: `{scope['in_scope_gt_denominator']}`",
        f"- target family counts: `{scope['target_family_counts']}`",
        "",
        "## Promotion Rule",
        "",
        "Qwen can be added as paper evidence only after full-source input audit, shard inference, parser validation, prediction export, geometry join, metrics, controls, bootstrap CI, and qualitative audit complete in Docker.",
        "",
        "Tiny smoke results remain non-metric evidence.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    qwen_root = resolve(repo_root, args.qwen_root)
    open3dsg_root = resolve(repo_root, args.open3dsg_root)
    bootstrap_path = resolve(repo_root, args.bootstrap_summary)
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    qwen = qwen_status(qwen_root)
    scope = open3dsg_scope(open3dsg_root)
    bootstrap = load_json(bootstrap_path)
    protocol = build_protocol(scope=scope, qwen=qwen, bootstrap=bootstrap)
    created_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": created_at,
        "status": "full_source_promotion_plan_frozen_no_metric_run",
        "role": protocol["role"],
        "qwen_status": qwen,
        "open3dsg_scope": scope,
        "outputs": {
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "protocol": relpath(repo_root, out_dir / "protocol.json"),
            "commands": relpath(repo_root, out_dir / "commands.md"),
            "report": relpath(repo_root, out_dir / "report.md"),
        },
        "next_required_service": "qwen_vl_full_source_input",
        "paper_metric": False,
        "replacement_for_open3dsg_anchor": False,
    }

    write_json(out_dir / "protocol.json", protocol)
    write_text(out_dir / "commands.md", build_commands(repo_root, out_dir))
    write_text(out_dir / "report.md", build_report(manifest, protocol))
    write_json(out_dir / "manifest.json", manifest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
