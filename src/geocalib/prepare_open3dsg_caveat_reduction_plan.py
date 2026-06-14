#!/usr/bin/env python3
"""Freeze the Open3DSG caveat-reduction retry plan without running heavy jobs."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h001_open3dsg_caveat_reduction_plan_v2"
STATUS_READY = "open3dsg_caveat_reduction_plan_frozen_no_execution"
ATTACHMENT_LABELS = {"attached to", "hanging on", "connected to"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/caveat_reduction_plan"),
    )
    parser.add_argument(
        "--paper-caveats",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/paper_caveats/manifest.json"),
    )
    parser.add_argument(
        "--h001-feature-audit",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/dump_features_h001_eval/manifest.json"),
    )
    parser.add_argument(
        "--checkpoint-selection",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection/manifest.json"),
    )
    parser.add_argument(
        "--attachment-denominator",
        type=Path,
        default=Path(
            "archive/experiments/H001_geom_reliability/sources/attachment_deferred/"
            "full_source_protocol/denominator_audit.json"
        ),
    )
    parser.add_argument(
        "--ground-truth-jsonl",
        type=Path,
        default=Path(
            "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/"
            "evaluation/vlsat_closed_set/hardened/ground_truth.jsonl"
        ),
    )
    parser.add_argument(
        "--open3dsg-verification-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/geometry/verification.jsonl"),
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def get(payload: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return current if current is not None else default


def missing_contexts(feature_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return get(
        feature_manifest,
        ["selected_run_audit", "split_coverage", "validation", "missing_preprocessed_sample"],
        [],
    )


def scan_id_args(rows: list[dict[str, Any]]) -> str:
    scan_ids = sorted({str(row["scan"]) for row in rows if row.get("scan")})
    return " ".join(f"--scan-id {scan_id}" for scan_id in scan_ids)


def decompose_attachment_missing(
    gt_jsonl: Path,
    open3dsg_verification_jsonl: Path,
    missing_preprocessed_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    missing_context_set = {
        (str(row.get("scan")), int(row.get("split")))
        for row in missing_preprocessed_rows
        if row.get("scan") is not None and row.get("split") is not None
    }
    source_exact: set[tuple[str, int, int, int, str]] = set()
    source_pairs: set[tuple[str, int, int, int]] = set()
    source_contexts: set[tuple[str, int]] = set()

    for row in iter_jsonl(open3dsg_verification_jsonl):
        scan_id = str(row["scan_id"])
        split_id = int(row["subset_split_id"])
        subject_id = int(row["edge"]["subject_id"])
        object_id = int(row["edge"]["object_id"])
        predicate_label = str(row["predicate"]["predicate_label"])
        source_contexts.add((scan_id, split_id))
        source_pairs.add((scan_id, split_id, subject_id, object_id))
        source_exact.add((scan_id, split_id, subject_id, object_id, predicate_label))

    total = 0
    covered = 0
    reason_counts: Counter[str] = Counter()
    label_counts: dict[str, Counter[str]] = {}
    examples: list[dict[str, Any]] = []
    for row in iter_jsonl(gt_jsonl):
        predicate_label = str(row.get("predicate_label"))
        if predicate_label not in ATTACHMENT_LABELS:
            continue
        total += 1
        key = (
            str(row["scan_id"]),
            int(row["subset_split_id"]),
            int(row["subject_id"]),
            int(row["object_id"]),
            predicate_label,
        )
        if key in source_exact:
            covered += 1
            continue
        context_key = key[:2]
        pair_key = key[:4]
        if context_key in missing_context_set or context_key not in source_contexts:
            reason = "missing_preprocessed_context"
        elif pair_key not in source_pairs:
            reason = "candidate_pair_absent"
        else:
            reason = "label_absent_for_present_pair"
        reason_counts[reason] += 1
        label_counts.setdefault(reason, Counter())[predicate_label] += 1
        if len(examples) < 10:
            examples.append(
                {
                    "reason": reason,
                    "scan_id": key[0],
                    "subset_split_id": key[1],
                    "subject_id": key[2],
                    "object_id": key[3],
                    "predicate_label": key[4],
                }
            )

    return {
        "attachment_gt_rows": total,
        "open3dsg_covered_exact_label_gt_rows": covered,
        "open3dsg_missing_exact_label_gt_rows": total - covered,
        "missing_reason_counts": dict(reason_counts),
        "missing_label_counts_by_reason": {
            reason: dict(counts) for reason, counts in sorted(label_counts.items())
        },
        "examples": examples,
        "interpretation": {
            "covered_context_retry_can_address": reason_counts.get("missing_preprocessed_context", 0),
            "covered_context_retry_cannot_address": reason_counts.get("candidate_pair_absent", 0)
            + reason_counts.get("label_absent_for_present_pair", 0),
            "note": (
                "A 388/388 covered-context retry can only recover attachment rows whose "
                "context is currently missing. Candidate-pair absence requires a different "
                "Open3DSG raw-dump/candidate-universe strategy or a source-specific denominator."
            ),
        },
    }


def command_templates(missing_rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing_scan_args = scan_id_args(missing_rows)
    return {
        "plan_service": (
            "sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f "
            "configs/h001/compose.yaml run --rm "
            "open3dsg_caveat_reduction_plan'"
        ),
        "non_avg_training_tmux_template": "\n".join(
            [
                "mkdir -p logs",
                "ts=$(date +%Y%m%d_%H%M%S)",
                "tmux new-session -d -s h001_open3dsg_train_full_nonavg_retry \\",
                "  \"cd /home/yoohyun/research && bash -lc 'set -o pipefail; \\",
                "  env UID=$(id -u) GID=$(id -g) OPEN3DSG_TRAIN_WORKERS=0 \\",
                "  OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 \\",
                "  OPEN3DSG_MIN_GPU_FREE_MB=22000 \\",
                "  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 \\",
                "  docker compose -f configs/open3dsg/compose.open3dsg.yaml \\",
                "  run --rm train_full; rc=$?; printf \"%s\\n\" \"$rc\" > logs/open3dsg_train_full_nonavg_retry_${ts}.exit; exit $rc' \\",
                "  > logs/open3dsg_train_full_nonavg_retry_${ts}.log 2>&1\"",
            ]
        ),
        "checkpoint_selection_after_non_avg": (
            "sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f "
            "configs/h001/compose.yaml run --rm "
            "open3dsg_checkpoint_selection'"
        ),
        "h001_preprocess_retry_388_template": "\n".join(
            [
                "mkdir -p logs",
                "ts=$(date +%Y%m%d_%H%M%S)",
                "tmux new-session -d -s h001_open3dsg_h001_preprocess_retry_388 \\",
                "  \"cd /home/yoohyun/research && bash -lc 'set -o pipefail; \\",
                "  env UID=$(id -u) GID=$(id -g) docker compose -f configs/open3dsg/compose.open3dsg.yaml \\",
                "  run --rm open3dsg_base bash -lc \\\"python /workspace/src/geocalib/patch_open3dsg_source.py \\",
                "  --repo-root /workspace --source-root /workspace/local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source && \\",
                "  python /workspace/src/geocalib/run_open3dsg_train_preprocess.py \\",
                "  --staged-root /workspace/local_dataset/Open3DSG_staged/h001_runtime \\",
                "  --open3dsg-source /workspace/local_dataset/Open3DSG_staged/h001_runtime/source/open3dsg_source \\",
                "  --work-source /workspace/local_dataset/Open3DSG_staged/h001_runtime/work/open3dsg_eval_source \\",
                "  --split validation --workers 1 --force --deep-inspect \\",
                "  --output-dir /workspace/experiments/H001_geom_reliability/sources/open3dsg/h001_preprocess_retry_388 "
                + missing_scan_args
                + "\\\"; rc=$?; printf \"%s\\n\" \"$rc\" > logs/open3dsg_h001_preprocess_retry_388_${ts}.exit; exit $rc' \\",
                "  > logs/open3dsg_h001_preprocess_retry_388_${ts}.log 2>&1\"",
            ]
        ),
        "h001_feature_retry_after_388_template": "\n".join(
            [
                "mkdir -p logs",
                "ts=$(date +%Y%m%d_%H%M%S)",
                "tmux new-session -d -s h001_open3dsg_dump_features_h001_eval_388_retry \\",
                "  \"cd /home/yoohyun/research && bash -lc 'set -o pipefail; \\",
                "  env UID=$(id -u) GID=$(id -g) \\",
                "  OPEN3DSG_CHECKPOINT=/workspace/local_dataset/Open3DSG_staged/training_repro/mlops/opensg/mlflow/363094050435167554/2a23a9af581b4666a207423aa6217853/checkpoints/epoch=13-step=13104.ckpt \\",
                "  OPEN3DSG_FEATURE_SHARD_ONLY_MISSING=1 OPEN3DSG_FEATURE_SHARD_MAX_NEW_IDS=11 \\",
                "  OPEN3DSG_BLIP_EMBED_CHUNK_SIZE=1 OPEN3DSG_BLIP_PROJECTOR_CHUNK_SIZE=1 \\",
                "  PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True,max_split_size_mb:64 \\",
                "  docker compose -f configs/open3dsg/compose.open3dsg.yaml \\",
                "  run --rm dump_features_h001_eval; rc=$?; printf \"%s\\n\" \"$rc\" > logs/open3dsg_dump_features_h001_eval_388_retry_${ts}.exit; exit $rc' \\",
                "  > logs/open3dsg_dump_features_h001_eval_388_retry_${ts}.log 2>&1\"",
            ]
        ),
        "h001_feature_audit_after_388": (
            "sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f "
            "configs/open3dsg/compose.open3dsg.yaml "
            "run --rm feature_audit_h001_eval'"
        ),
        "existing_downstream_rerun_chain": [
            "open3dsg_raw_dump_identity",
            "open3dsg_adapter_raw_dump",
            "open3dsg_geometry_join",
            "open3dsg_metric_eval",
            "bootstrap_ci",
            "table_builder",
            "open3dsg_paper_caveats",
        ],
    }


def build_plan(
    repo_root: Path,
    paths: dict[str, Path],
    paper_caveats: dict[str, Any],
    feature_manifest: dict[str, Any],
    checkpoint_selection: dict[str, Any],
    attachment_denominator: dict[str, Any],
    attachment_decomposition: dict[str, Any],
    out_dir: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    facts = paper_caveats.get("facts", {})
    h001_eval = facts.get("h001_eval_coverage", {})
    variant = facts.get("variant", {})
    missing_rows = missing_contexts(feature_manifest)
    commands = command_templates(missing_rows)

    retry_plan = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY,
        "created_at": utc_now(),
        "current_caveats": {
            "averaged_blip_variant": variant,
            "covered_loadable_scope": {
                "complete_feature_ids": h001_eval.get("complete_feature_ids"),
                "identity_contexts": h001_eval.get("identity_contexts"),
                "missing_preprocessed": h001_eval.get("missing_preprocessed"),
                "missing_contexts": missing_rows,
            },
            "attachment_open3dsg_coverage": attachment_denominator.get("sources", {}).get("open3dsg_ov", {}),
            "attachment_missing_decomposition": attachment_decomposition,
        },
        "retry_order": [
            {
                "id": "R1_exact_non_avg_blip_route_retry",
                "priority": 1,
                "goal": "Reduce the averaged-BLIP variant caveat for the main Open3DSG source.",
                "execution_policy": "Docker/tmux background job only; do not overwrite existing avg-BLIP result artifacts.",
                "command_template_key": "non_avg_training_tmux_template",
                "success_criteria": [
                    "train_full exits 0 without CUDA OOM",
                    "a non-avg BLIP full-route checkpoint is present under the Open3DSG mlflow/checkpoint tree",
                    "checkpoint selection can identify it without H001 held-out metrics",
                    "downstream H001 feature/raw-dump/eval artifacts use separate non-avg run ids and output paths",
                ],
                "failure_policy": [
                    "If OOM recurs after the resource-guarded retry, keep the current averaged-BLIP caveat.",
                    "Do not tune checkpoint choice on H001 held-out R@K, violation, failure rows, or visual inspection.",
                ],
                "implementation_gap_before_downstream": [
                    "Existing H001 eval feature/raw-dump compose services include --avg_blip_emb.",
                    "Before promoting a non-avg checkpoint, add dedicated non-avg H001 eval feature and raw-dump services with separate output paths.",
                ],
            },
            {
                "id": "R2_h001_covered_loadable_context_retry_388",
                "priority": 2,
                "goal": "Try to reduce the H001 covered-scope caveat from 377/388 to 388/388 contexts.",
                "execution_policy": "Target only the 11 missing-preprocessed H001 contexts first, then audit.",
                "command_template_keys": [
                    "h001_preprocess_retry_388_template",
                    "h001_feature_retry_after_388_template",
                    "h001_feature_audit_after_388",
                ],
                "success_criteria": [
                    "missing_preprocessed becomes 0 in feature_audit_h001_eval",
                    "complete feature ids become 388/388",
                    "raw-dump identity and downstream metric artifacts are regenerated with the updated scope",
                ],
                "failure_policy": [
                    "If the 11 contexts are still non-recoverable, keep 377/388 as an explicit covered-loadable caveat.",
                    "Do not infer attachment success from this retry; it only addresses missing context coverage.",
                ],
            },
            {
                "id": "R3_attachment_deferred_G5d_after_open3dsg_decision",
                "priority": 3,
                "goal": "Run attachment full-source scoring only after Open3DSG caveat-reduction decisions are resolved or explicitly waived.",
                "execution_policy": "No attachment main-claim promotion without explicit final user confirmation.",
                "expected_effect_of_R1_R2": {
                    "helps": [
                        "stronger Open3DSG source credibility",
                        "reduced averaged-BLIP caveat if R1 succeeds",
                        "possible recovery of attachment missing_preprocessed_context rows if R2 succeeds",
                    ],
                    "does_not_solve": [
                        "candidate_pair_absent attachment rows",
                        "connected-to dev absence",
                        "attachment full-source scoring, controls, bootstrap CI, and audit requirements",
                    ],
                },
            },
        ],
        "downstream_rerun_requirements": {
            "if_R1_non_avg_succeeds": [
                "add/use non-avg H001 eval feature service with no --avg_blip_emb",
                "run non-avg H001 eval feature dump into a separate feature directory",
                "run feature audit on that separate directory",
                "run raw dump into a separate raw.jsonl with baseline_run_id open3dsg_nonavg_*",
                "run raw-dump identity, adapter export, geometry join, metric eval, bootstrap CI, Table 6, paper caveats",
                "update manuscript caveats only after the new chain passes",
            ],
            "if_R2_388_succeeds": [
                "rerun H001 eval raw dump on the updated feature/context scope",
                "rerun raw-dump identity, adapter export, geometry join, metric eval, bootstrap CI, Table 6, paper caveats",
                "update covered-scope wording from 377/388 only after the regenerated artifacts pass",
            ],
            "if_both_fail_or_are_waived": [
                "retain current Open3DSG result with averaged-BLIP and 377/388 caveats",
                "continue attachment_deferred only as optional/future expansion unless the user explicitly accepts the caveats",
            ],
        },
        "commands": commands,
    }

    validation_errors: list[str] = []
    if h001_eval.get("complete_feature_ids") != 377:
        validation_errors.append("unexpected_current_complete_feature_ids")
    if h001_eval.get("identity_contexts") != 388:
        validation_errors.append("unexpected_current_identity_contexts")
    if h001_eval.get("missing_preprocessed") != 11:
        validation_errors.append("unexpected_current_missing_preprocessed")
    selected = checkpoint_selection.get("selected_checkpoint", {})
    selected_stage = selected.get("source_stage")
    active_downstream_stage = get(paper_caveats, ["facts", "variant", "source_stage"])
    if selected_stage not in {"avg_blip_full_variant", "official_non_avg_blip_full"}:
        validation_errors.append("unexpected_selected_checkpoint_stage")
    if active_downstream_stage != "avg_blip_full_variant":
        validation_errors.append("unexpected_active_downstream_variant")
    if attachment_decomposition["open3dsg_missing_exact_label_gt_rows"] != 199:
        validation_errors.append("unexpected_attachment_missing_count")

    route_comparison = checkpoint_selection.get("route_comparison", {})
    r1_status = "not_completed_or_not_selected"
    if (
        checkpoint_selection.get("status") == "checkpoint_selection_ready_official_non_avg_blip"
        and selected_stage == "official_non_avg_blip_full"
    ):
        r1_status = "completed_checkpoint_selected_no_downstream_metrics"

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY if not validation_errors else "blocked_plan_input_mismatch",
        "created_at": retry_plan["created_at"],
        "inputs": {name: relpath(repo_root, path) for name, path in paths.items()},
        "outputs": {
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "retry_plan": relpath(repo_root, out_dir / "retry_plan.json"),
            "commands": relpath(repo_root, out_dir / "commands.md"),
            "report": relpath(repo_root, out_dir / "report.md"),
        },
        "current_state_summary": {
            "active_downstream_result_variant": active_downstream_stage,
            "selected_checkpoint_route": selected_stage,
            "selected_checkpoint": selected.get("checkpoint_path"),
            "selected_checkpoint_train_dev_val_loss": get(selected, ["training_internal_val_loss", "value"]),
            "r1_non_avg_status": r1_status,
            "route_comparison": route_comparison,
            "h001_covered_contexts": f"{h001_eval.get('complete_feature_ids')}/{h001_eval.get('identity_contexts')}",
            "h001_missing_preprocessed": h001_eval.get("missing_preprocessed"),
            "attachment_open3dsg_missing_exact_label_gt_rows": attachment_decomposition[
                "open3dsg_missing_exact_label_gt_rows"
            ],
            "attachment_missing_preprocessed_context_rows": attachment_decomposition["missing_reason_counts"].get(
                "missing_preprocessed_context", 0
            ),
            "attachment_candidate_pair_absent_rows": attachment_decomposition["missing_reason_counts"].get(
                "candidate_pair_absent", 0
            ),
        },
        "claim_boundary": {
            "plan_only_no_heavy_execution": True,
            "does_not_change_current_AAAI_main_claim": True,
            "attachment_promotion_requires_user_confirmation": True,
            "non_avg_success_requires_full_downstream_regeneration": True,
            "covered_388_success_requires_full_downstream_regeneration": True,
        },
        "validation": {"errors": validation_errors},
    }
    return manifest, retry_plan


def make_commands_md(retry_plan: dict[str, Any]) -> str:
    commands = retry_plan["commands"]
    lines = [
        "# Open3DSG Caveat-Reduction Commands",
        "",
        "This is a planning artifact. Do not run these as paper-result evidence until the relevant Docker services and output paths are confirmed.",
        "",
        "## Regenerate This Plan",
        "",
        "```bash",
        commands["plan_service"],
        "```",
        "",
        "## R1 Exact Non-Averaged BLIP Training Retry",
        "",
        "```bash",
        commands["non_avg_training_tmux_template"],
        "```",
        "",
        "After completion, inspect only the log tail and exit file, then refresh checkpoint selection:",
        "",
        "```bash",
        commands["checkpoint_selection_after_non_avg"],
        "```",
        "",
        "Important: existing H001 eval feature/raw-dump services are avg-BLIP services. Add separate non-avg services and output paths before downstream metric promotion.",
        "",
        "## R2 H001 Covered-Context Retry Toward 388/388",
        "",
        "```bash",
        commands["h001_preprocess_retry_388_template"],
        "```",
        "",
        "If new preprocess outputs appear, run bounded missing-id feature generation and audit:",
        "",
        "```bash",
        commands["h001_feature_retry_after_388_template"],
        commands["h001_feature_audit_after_388"],
        "```",
        "",
        "## Downstream Chain After Any Successful Retry",
        "",
    ]
    for item in commands["existing_downstream_rerun_chain"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "Do not update manuscript caveats until the regenerated downstream artifacts pass.",
            "",
        ]
    )
    return "\n".join(lines)


def make_report(manifest: dict[str, Any], retry_plan: dict[str, Any]) -> str:
    summary = manifest["current_state_summary"]
    route_comparison = summary.get("route_comparison") or {}
    comparison_notes = route_comparison.get("interpretation", [])
    lines = [
        "# Open3DSG Caveat-Reduction Plan",
        "",
        f"Created at: `{manifest['created_at']}`",
        f"Status: `{manifest['status']}`",
        "",
        "## Current Caveats",
        "",
        f"- active downstream result variant: `{summary['active_downstream_result_variant']}`",
        f"- selected checkpoint route: `{summary['selected_checkpoint_route']}`",
        f"- selected checkpoint: `{summary['selected_checkpoint']}`",
        f"- selected checkpoint train-dev val/loss: `{summary['selected_checkpoint_train_dev_val_loss']}`",
        f"- R1 non-avg status: `{summary['r1_non_avg_status']}`",
        f"- H001 covered contexts: `{summary['h001_covered_contexts']}`",
        f"- missing preprocessed H001 contexts: `{summary['h001_missing_preprocessed']}`",
        f"- attachment Open3DSG missing exact-label GT rows: `{summary['attachment_open3dsg_missing_exact_label_gt_rows']}`",
        f"- attachment missing due to missing H001 contexts: `{summary['attachment_missing_preprocessed_context_rows']}`",
        f"- attachment missing due to absent Open3DSG candidate pairs: `{summary['attachment_candidate_pair_absent_rows']}`",
        "",
        "## Frozen Retry Order",
        "",
    ]
    for item in retry_plan["retry_order"]:
        lines.extend(
            [
                f"### {item['id']}",
                "",
                f"- priority: `{item['priority']}`",
                f"- goal: {item['goal']}",
                f"- execution policy: {item['execution_policy']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation",
            "",
            "R1 non-avg BLIP checkpoint selection reduces the route-level feasibility caveat only after downstream non-avg artifacts are regenerated.",
            "Until then, the current paper-facing Open3DSG metrics remain the active avg-BLIP result.",
            "Non-avg BLIP success and 388/388 covered-context success would strengthen Open3DSG source credibility.",
            "They do not by themselves make `attachment_deferred_G5d` successful: the 388 retry can only address the missing-preprocessed-context portion, while candidate-pair absence remains a separate denominator/source-universe issue.",
            "",
        ]
    )
    if comparison_notes:
        lines.extend(["## Route Comparison Notes", ""])
        lines.extend(f"- {note}" for note in comparison_notes)
        lines.append("")
    lines.extend(
        [
            "## Claim Boundary",
            "",
            "- This artifact is a no-execution plan.",
            "- It does not change current AAAI main-claim wording.",
            "- Attachment promotion still requires explicit final user confirmation.",
            "- Any successful retry must regenerate downstream artifacts before paper wording changes.",
            "",
        ]
    )
    if manifest["validation"]["errors"]:
        lines.extend(["## Validation Errors", ""])
        lines.extend(f"- `{error}`" for error in manifest["validation"]["errors"])
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out)
    paths = {
        "paper_caveats": resolve(repo_root, args.paper_caveats),
        "h001_feature_audit": resolve(repo_root, args.h001_feature_audit),
        "checkpoint_selection": resolve(repo_root, args.checkpoint_selection),
        "attachment_denominator": resolve(repo_root, args.attachment_denominator),
        "ground_truth_jsonl": resolve(repo_root, args.ground_truth_jsonl),
        "open3dsg_verification_jsonl": resolve(repo_root, args.open3dsg_verification_jsonl),
    }

    paper_caveats = load_json(paths["paper_caveats"])
    feature_manifest = load_json(paths["h001_feature_audit"])
    checkpoint_selection = load_json(paths["checkpoint_selection"])
    attachment_denominator = load_json(paths["attachment_denominator"])
    attachment_decomposition = decompose_attachment_missing(
        paths["ground_truth_jsonl"],
        paths["open3dsg_verification_jsonl"],
        missing_contexts(feature_manifest),
    )

    manifest, retry_plan = build_plan(
        repo_root=repo_root,
        paths=paths,
        paper_caveats=paper_caveats,
        feature_manifest=feature_manifest,
        checkpoint_selection=checkpoint_selection,
        attachment_denominator=attachment_denominator,
        attachment_decomposition=attachment_decomposition,
        out_dir=out_dir,
    )

    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "retry_plan.json", retry_plan)
    (out_dir / "commands.md").write_text(make_commands_md(retry_plan), encoding="utf-8")
    (out_dir / "report.md").write_text(make_report(manifest, retry_plan), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "validation_errors": manifest["validation"]["errors"],
                "out": relpath(repo_root, out_dir),
            },
            sort_keys=True,
        )
    )
    return 0 if not manifest["validation"]["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
