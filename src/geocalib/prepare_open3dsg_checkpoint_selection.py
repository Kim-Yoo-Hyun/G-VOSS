#!/usr/bin/env python3
"""Freeze Open3DSG checkpoint provenance and selection policy."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_checkpoint_selection_v4"
STATUS_READY_MISSING = "checkpoint_selection_template_ready_checkpoint_missing"
STATUS_READY_WITH_CANDIDATES = "checkpoint_selection_template_ready_candidates_present"
STATUS_READY_SELECTED_VARIANT = "checkpoint_selection_ready_labeled_avg_blip_variant"
STATUS_READY_SELECTED_OFFICIAL = "checkpoint_selection_ready_official_non_avg_blip"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--checkpoint-dir",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/training_repro"),
    )
    parser.add_argument(
        "--feature-audit-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/dump_features/manifest.json"),
    )
    parser.add_argument(
        "--train-filter-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/train_preprocess_filter/manifest.json"),
    )
    parser.add_argument(
        "--validation-filter-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/validation_preprocess_filter/manifest.json"),
    )
    parser.add_argument(
        "--env-check-report",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/env_check.md"),
    )
    parser.add_argument(
        "--cache-preflight-manifest",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/cache_preflight/manifest.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/checkpoint_selection"),
    )
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"status": "unreadable_json"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_text_if_exists(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").strip()


def read_tail_lines_if_exists(path: Path, max_lines: int = 5) -> str | None:
    text = read_text_if_exists(path)
    if text is None:
        return None
    return "\n".join(text.splitlines()[-max_lines:])


def read_metric_series(path: Path) -> list[dict[str, int | float]]:
    text = read_text_if_exists(path)
    if text is None:
        return []
    series: list[dict[str, int | float]] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            timestamp = int(parts[0])
            value = float(parts[1])
            step = int(parts[2])
        except ValueError:
            continue
        series.append({"timestamp": timestamp, "value": value, "step": step})
    return series


def checkpoint_step(filename: str) -> int | None:
    match = re.search(r"step=(\d+)", filename)
    if not match:
        return None
    return int(match.group(1))


def matched_val_loss(filename: str, val_loss_series: list[dict[str, int | float]]) -> dict[str, int | float] | None:
    if not val_loss_series:
        return None
    step = checkpoint_step(filename)
    if step is None:
        return val_loss_series[-1] if filename == "last.ckpt" else None
    target_steps = {step, step - 1, step + 1}
    for record in val_loss_series:
        if int(record["step"]) in target_steps:
            return record
    return None


def infer_mlflow_run(path: Path, repo_root: Path) -> dict[str, Any]:
    run_root = path.parent.parent if path.parent.name == "checkpoints" else None
    if run_root is None or not (run_root / "meta.yaml").is_file():
        return {}
    params_dir = run_root / "params"
    metrics_dir = run_root / "metrics"
    val_loss_series = read_metric_series(metrics_dir / "val/loss")
    params = {
        name: read_text_if_exists(params_dir / name)
        for name in (
            "run_name",
            "epochs",
            "blip",
            "avg_blip_emb",
            "clip_model",
            "load_features",
            "mini_dataset",
            "mixed_precision",
            "accumulate_grad_batches",
        )
    }
    best_val_loss = min(val_loss_series, key=lambda item: float(item["value"])) if val_loss_series else None
    metrics = {
        "val_loss_series": val_loss_series,
        "val_loss_best": best_val_loss,
        "val_loss_last": val_loss_series[-1] if val_loss_series else None,
        "train_loss_tail": read_tail_lines_if_exists(metrics_dir / "train/loss", max_lines=5),
    }
    try:
        experiment_id = run_root.parent.name
        run_id = run_root.name
    except IndexError:
        experiment_id = None
        run_id = None
    return {
        "mlflow_run_root": relpath(repo_root, run_root),
        "mlflow_experiment_id": experiment_id,
        "mlflow_run_id": run_id,
        "mlflow_params": params,
        "mlflow_metrics": metrics,
    }


def infer_route(mlflow: dict[str, Any]) -> dict[str, Any]:
    params = mlflow.get("mlflow_params", {})
    avg_blip = params.get("avg_blip_emb") == "True"
    blip = params.get("blip") == "True"
    mini_dataset = params.get("mini_dataset") == "True"
    epochs = params.get("epochs")
    try:
        epoch_count = int(epochs) if epochs is not None else None
    except ValueError:
        epoch_count = None

    if mini_dataset:
        source_stage = "reduced_smoke"
        paper_result_eligible = False
        selection_role = "smoke_only"
    elif blip and avg_blip and epoch_count == 1:
        source_stage = "avg_blip_pilot"
        paper_result_eligible = False
        selection_role = "pilot_debug"
    elif blip and avg_blip:
        source_stage = "avg_blip_full_variant"
        paper_result_eligible = "labeled_variant_only"
        selection_role = "labeled_second_source_variant_candidate"
    elif blip and epoch_count == 1:
        source_stage = "official_non_avg_blip_pilot"
        paper_result_eligible = False
        selection_role = "pilot_debug"
    elif blip:
        source_stage = "official_non_avg_blip_full"
        paper_result_eligible = True
        selection_role = "primary_candidate"
    else:
        source_stage = "unknown"
        paper_result_eligible = "unknown_until_policy_gate_passes"
        selection_role = "needs_review"

    return {
        "source_stage": source_stage,
        "paper_result_eligible": paper_result_eligible,
        "selection_role": selection_role,
    }


def inspect_checkpoint(path: Path, repo_root: Path) -> dict[str, Any]:
    stat = path.stat()
    mlflow = infer_mlflow_run(path, repo_root)
    route = infer_route(mlflow)
    val_loss_record = matched_val_loss(path.name, mlflow.get("mlflow_metrics", {}).get("val_loss_series", []))
    return {
        "checkpoint_path": relpath(repo_root, path),
        "filename": path.name,
        "size_bytes": stat.st_size,
        "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
        "sha256": sha256_file(path),
        "training_internal_val_loss": val_loss_record,
        "selection_metric_source": (
            "mlflow val/loss from Open3DSG train-dev validation only; no H001 held-out metric, "
            "raw dump, failure taxonomy, or visual inspection used"
        )
        if val_loss_record
        else None,
        **route,
        **mlflow,
    }


def select_predeclared_checkpoint(candidates: list[dict[str, Any]]) -> dict[str, Any] | None:
    official = [candidate for candidate in candidates if candidate.get("paper_result_eligible") is True]
    if official:
        pool = official
    else:
        pool = [
            candidate
            for candidate in candidates
            if candidate.get("source_stage") == "avg_blip_full_variant"
            and candidate.get("paper_result_eligible") == "labeled_variant_only"
            and candidate.get("filename") != "last.ckpt"
        ]
    if not pool:
        return None

    def sort_key(candidate: dict[str, Any]) -> tuple[float, str]:
        val_loss = candidate.get("training_internal_val_loss")
        if isinstance(val_loss, dict) and isinstance(val_loss.get("value"), (int, float)):
            return (float(val_loss["value"]), str(candidate.get("checkpoint_path")))
        return (float("inf"), str(candidate.get("checkpoint_path")))

    selected = min(pool, key=sort_key)
    selected = dict(selected)
    selected["selection_reason"] = (
        "predeclared official full-route checkpoint selected by Open3DSG train-dev val/loss"
        if selected.get("paper_result_eligible") is True
        else "documented lower-memory avg-BLIP full variant selected by Open3DSG train-dev val/loss after non-averaged BLIP route produced no checkpoint"
    )
    selected["h001_eval_metric_seen_before_selection"] = False
    selected["selected_before_selected_route_raw_dump_or_metric"] = True
    return selected


def best_checkpoint_for_stage(candidates: list[dict[str, Any]], stage: str) -> dict[str, Any] | None:
    pool = [
        candidate
        for candidate in candidates
        if candidate.get("source_stage") == stage
        and candidate.get("filename") != "last.ckpt"
        and isinstance(candidate.get("training_internal_val_loss"), dict)
        and isinstance(candidate["training_internal_val_loss"].get("value"), (int, float))
    ]
    if not pool:
        return None
    return min(pool, key=lambda candidate: float(candidate["training_internal_val_loss"]["value"]))


def summarize_route_comparison(candidates: list[dict[str, Any]], selected: dict[str, Any] | None) -> dict[str, Any]:
    best_non_avg = best_checkpoint_for_stage(candidates, "official_non_avg_blip_full")
    best_avg = best_checkpoint_for_stage(candidates, "avg_blip_full_variant")

    comparison: dict[str, Any] = {
        "best_official_non_avg_blip_full": None,
        "best_avg_blip_full_variant": None,
        "train_dev_val_loss_delta_non_avg_minus_avg": None,
        "interpretation": [],
    }
    if best_non_avg:
        comparison["best_official_non_avg_blip_full"] = {
            "checkpoint_path": best_non_avg["checkpoint_path"],
            "val_loss": best_non_avg["training_internal_val_loss"]["value"],
            "step": best_non_avg["training_internal_val_loss"]["step"],
            "run_id": best_non_avg.get("mlflow_run_id"),
        }
    if best_avg:
        comparison["best_avg_blip_full_variant"] = {
            "checkpoint_path": best_avg["checkpoint_path"],
            "val_loss": best_avg["training_internal_val_loss"]["value"],
            "step": best_avg["training_internal_val_loss"]["step"],
            "run_id": best_avg.get("mlflow_run_id"),
        }
    if best_non_avg and best_avg:
        delta = float(best_non_avg["training_internal_val_loss"]["value"]) - float(
            best_avg["training_internal_val_loss"]["value"]
        )
        comparison["train_dev_val_loss_delta_non_avg_minus_avg"] = delta
        if delta > 0:
            comparison["interpretation"].append(
                "official non-avg BLIP route completed, but its train-dev val/loss is worse than the existing avg-BLIP variant"
            )
        else:
            comparison["interpretation"].append(
                "official non-avg BLIP route completed and is not worse than the avg-BLIP variant by train-dev val/loss"
            )
    if selected and selected.get("source_stage") == "official_non_avg_blip_full":
        comparison["interpretation"].append(
            "avg-BLIP checkpoint-route caveat can be reduced only after the full downstream H001 Open3DSG chain is regenerated under non-avg output paths"
        )
        comparison["interpretation"].append(
            "current avg-BLIP H001 metric tables remain the active paper evidence until non-avg raw dump, adapter, geometry join, metrics, CI, and caveat wording exist"
        )
    return comparison


def record_template() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "open3dsg_checkpoint_provenance",
        "required_fields": {
            "checkpoint_id": "stable id assigned before H001 held-out metric inspection",
            "checkpoint_path": "relative path under local_dataset/Open3DSG_staged/training_repro/output/checkpoints",
            "checkpoint_sha256": "sha256 of checkpoint file",
            "checkpoint_size_bytes": "file size in bytes",
            "source_stage": "pilot | full | reduced_smoke",
            "paper_result_eligible": "true only for official BLIP TopK5/scales3 full-route checkpoints",
            "labeled_variant_only": "allowed only for explicitly labeled averaged-BLIP Open3DSG variant tables",
            "selection_role": "primary | fallback | smoke_only | rejected",
            "selection_reason": "predeclared reason, not based on H001 held-out metrics",
            "created_by_command": "exact Docker command that produced the checkpoint",
            "docker_image": "image tag or image id",
            "compose_file": "compose file path",
            "open3dsg_source_path": "source snapshot path",
            "feature_run_dir": "feature directory used by training",
            "feature_audit_manifest": "feature audit manifest path and hash",
            "train_split_manifest": "filtered train split/preprocess manifest path and hash",
            "validation_split_manifest": "filtered validation split/preprocess manifest path and hash",
            "env_check_artifact": "Docker env/CUDA report path",
            "cache_preflight_artifact": "model/cache preflight manifest path",
            "training_log_path": "log path under logs/ or Open3DSG output dir",
            "training_internal_metric_source": "training/validation metric source, if used for selection",
            "h001_eval_metric_seen_before_selection": "must be false for paper-result eligibility",
            "notes": "free text for non-selection operational details",
        },
    }


def selection_policy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "policy_name": "h001_open3dsg_checkpoint_selection_policy",
        "selection_boundary": {
            "must_freeze_before": [
                "Open3DSG pilot checkpoint inspection",
                "Open3DSG full checkpoint inspection",
                "selected-route H001 raw dump generation",
                "selected-route H001 Open3DSG prediction JSONL export",
                "selected-route H001 Open3DSG metric computation",
            ],
            "forbidden_selection_signals": [
                "H001 held-out R@K",
                "H001 held-out violation rate",
                "H001 failure-analysis category distribution",
                "visual inspection of H001 held-out Open3DSG predictions",
            ],
            "allowed_selection_signals": [
                "predeclared route priority",
                "checkpoint file existence and checksum",
                "Docker preflight pass/fail",
                "official feature audit pass/fail",
                "training-internal train/validation logs that do not include H001 held-out scans",
            ],
        },
        "route_priority": [
            {
                "route": "official_full",
                "eligibility": "paper_result_eligible",
                "rule": "primary checkpoint if full route completes after official BLIP TopK5/scales3 feature audit pass",
            },
            {
                "route": "avg_blip_full_variant",
                "eligibility": "labeled_variant_only",
                "rule": "select only as an explicitly labeled averaged-BLIP Open3DSG variant after full-route training completes and the non-averaged route has no checkpoint",
            },
            {
                "route": "avg_blip_pilot",
                "eligibility": "pilot_evidence_only",
                "rule": "valid checkpoint-smoke evidence and provenance seed; not final paper-result evidence",
            },
            {
                "route": "official_pilot",
                "eligibility": "pilot_evidence_only",
                "rule": "fallback for debugging/reporting progress; not final paper result unless full route is explicitly abandoned and claim is downgraded",
            },
            {
                "route": "reduced_smoke",
                "eligibility": "smoke_only_not_paper_result",
                "rule": "may validate plumbing only; never promote to paper-result evidence",
            },
        ],
        "primary_selection_rule": (
            "Select the first policy-eligible full-route checkpoint that satisfies provenance, "
            "feature-audit, Docker preflight, and no-held-out-selection gates. If the exact "
            "non-averaged BLIP route has documented OOM failures and no checkpoint, select the "
            "best full avg-BLIP variant by Open3DSG train-dev val/loss and label every downstream "
            "table as an averaged-BLIP Open3DSG variant. Do not choose among checkpoints using "
            "H001 held-out metric results."
        ),
        "reselection_rule": (
            "Changing the primary checkpoint after H001 held-out metric inspection requires a "
            "new schema version and must be reported as a deviation."
        ),
    }


def artifact_records(repo_root: Path, paths: dict[str, Path]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for name, path in paths.items():
        record: dict[str, Any] = {
            "name": name,
            "path": relpath(repo_root, path),
            "exists": path.exists(),
        }
        if path.exists() and path.is_file():
            record["sha256"] = sha256_file(path)
        records.append(record)
    return records


def source_statuses(paths: dict[str, Path]) -> dict[str, str | None]:
    payloads = {name: load_json_if_exists(path) for name, path in paths.items() if path.suffix == ".json"}
    feature = payloads.get("feature_audit_manifest")
    train_filter = payloads.get("train_filter_manifest")
    validation_filter = payloads.get("validation_filter_manifest")
    cache = payloads.get("cache_preflight_manifest")
    return {
        "feature_audit": (
            feature.get("selected_run_audit", {}).get("status") or feature.get("status")
            if isinstance(feature, dict)
            else None
        ),
        "train_filter": train_filter.get("status") if isinstance(train_filter, dict) else None,
        "validation_filter": validation_filter.get("status") if isinstance(validation_filter, dict) else None,
        "cache_preflight": cache.get("status") if isinstance(cache, dict) else None,
    }


def build_report(payload: dict[str, Any]) -> str:
    selected = payload.get("selected_checkpoint")
    route_comparison = payload.get("route_comparison") or {}
    lines = [
        "# Open3DSG Checkpoint Selection",
        "",
        f"Status: `{payload['status']}`",
        f"Created at: `{payload['created_at']}`",
        "",
        "## Fact",
        "",
        "- The checkpoint provenance schema and selection policy use route priority, source provenance, and Open3DSG train-dev validation loss only.",
        "- For the selected route, no H001 held-out metric, failure taxonomy, or visual inspection is used for checkpoint selection.",
        "- This artifact does not train Open3DSG, inspect held-out predictions, or compute metrics.",
        "- Reduced-route checkpoints are smoke-only unless the paper claim is explicitly downgraded.",
        "",
        "## Selection Gate",
        "",
        "- Primary selection must not use H001 held-out metric results.",
        "- Full-route checkpoints have priority over pilot checkpoints.",
        "- A checkpoint can be paper-result eligible only after official feature audit, Docker preflight, provenance, and no-held-out-selection gates pass.",
        "",
        "## Current Candidates",
        "",
        f"- checkpoint dir: `{payload['checkpoint_dir']}`",
        f"- candidate checkpoints: `{payload['candidate_count']}`",
        f"- paper-result eligible candidates: `{payload['paper_result_eligible_candidate_count']}`",
        f"- labeled avg-BLIP variant candidates: `{payload['labeled_variant_candidate_count']}`",
        f"- official feature audit status: `{payload['source_statuses']['feature_audit']}`",
        f"- train filter status: `{payload['source_statuses']['train_filter']}`",
        f"- validation filter status: `{payload['source_statuses']['validation_filter']}`",
    ]
    if selected:
        val_loss = selected.get("training_internal_val_loss") or {}
        lines.extend(
            [
                "",
                "## Selected Checkpoint",
                "",
                f"- path: `{selected['checkpoint_path']}`",
                f"- source stage: `{selected['source_stage']}`",
                f"- selection role: `{selected['selection_role']}`",
                f"- selection reason: `{selected['selection_reason']}`",
                f"- train-dev val/loss: `{val_loss.get('value')}` at step `{val_loss.get('step')}`",
                "- H001 held-out metrics seen before selection: `False`",
            ]
        )
    if route_comparison:
        non_avg = route_comparison.get("best_official_non_avg_blip_full") or {}
        avg = route_comparison.get("best_avg_blip_full_variant") or {}
        lines.extend(["", "## Route Comparison", ""])
        if non_avg:
            lines.append(
                f"- best official non-avg BLIP: `{non_avg.get('checkpoint_path')}`, val/loss `{non_avg.get('val_loss')}` at step `{non_avg.get('step')}`"
            )
        if avg:
            lines.append(
                f"- best avg-BLIP variant: `{avg.get('checkpoint_path')}`, val/loss `{avg.get('val_loss')}` at step `{avg.get('step')}`"
            )
        if route_comparison.get("train_dev_val_loss_delta_non_avg_minus_avg") is not None:
            lines.append(
                f"- non-avg minus avg train-dev val/loss: `{route_comparison['train_dev_val_loss_delta_non_avg_minus_avg']}`"
            )
        for item in route_comparison.get("interpretation", []):
            lines.append(f"- {item}")
    if payload.get("claim_limitations"):
        lines.extend(["", "## Claim Limitations", ""])
        lines.extend(f"- `{limitation}`" for limitation in payload["claim_limitations"])
    if payload["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in payload["blockers"])
    lines.extend(
        [
            "",
            "## Generated Files",
            "",
            "- `selection_policy.json`",
            "- `record_template.json`",
            "- `manifest.json`",
            "- `commands.md`",
            "- `report.md`",
            "",
        ]
    )
    return "\n".join(lines)


def build_commands() -> str:
    return """# Open3DSG Checkpoint Selection Commands

Freeze or refresh the checkpoint selection template:

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm open3dsg_checkpoint_selection'
```

Use this template after `train_pilot` or `train_full` creates checkpoints. The primary checkpoint must be recorded before any H001 held-out Open3DSG metric or failure inspection.
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out)
    checkpoint_dir = resolve(repo_root, args.checkpoint_dir)
    source_paths = {
        "feature_audit_manifest": resolve(repo_root, args.feature_audit_manifest),
        "train_filter_manifest": resolve(repo_root, args.train_filter_manifest),
        "validation_filter_manifest": resolve(repo_root, args.validation_filter_manifest),
        "env_check_report": resolve(repo_root, args.env_check_report),
        "cache_preflight_manifest": resolve(repo_root, args.cache_preflight_manifest),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    candidates = [inspect_checkpoint(path, repo_root) for path in sorted(checkpoint_dir.rglob("*.ckpt"))] if checkpoint_dir.is_dir() else []
    paper_result_eligible_count = sum(candidate.get("paper_result_eligible") is True for candidate in candidates)
    labeled_variant_count = sum(candidate.get("paper_result_eligible") == "labeled_variant_only" for candidate in candidates)
    selected_checkpoint = select_predeclared_checkpoint(candidates)
    route_comparison = summarize_route_comparison(candidates, selected_checkpoint)
    blockers: list[str] = []
    if not checkpoint_dir.is_dir():
        blockers.append(f"missing_checkpoint_dir:{relpath(repo_root, checkpoint_dir)}")
    if not candidates:
        blockers.append("no_checkpoint_candidates")
    if candidates and selected_checkpoint is None:
        blockers.append("no_selectable_checkpoint_candidates")

    statuses = source_statuses(source_paths)
    if statuses["feature_audit"] != "ready":
        blockers.append(f"official_feature_audit_not_ready:{statuses['feature_audit']}")
    if statuses["train_filter"] != "filter_applied":
        blockers.append(f"train_filter_not_applied:{statuses['train_filter']}")
    if statuses["validation_filter"] != "filter_applied":
        blockers.append(f"validation_filter_not_applied:{statuses['validation_filter']}")

    policy = selection_policy()
    template = record_template()
    claim_limitations: list[str] = []
    if selected_checkpoint and selected_checkpoint.get("paper_result_eligible") is True:
        claim_limitations.extend(
            [
                "non_avg_checkpoint_selected_no_downstream_h001_metrics_yet",
                "current_paper_tables_still_use_avg_blip_until_non_avg_downstream_chain_is_regenerated",
            ]
        )
        delta = route_comparison.get("train_dev_val_loss_delta_non_avg_minus_avg")
        if isinstance(delta, (int, float)) and delta > 0:
            claim_limitations.append("non_avg_train_dev_val_loss_worse_than_existing_avg_blip_variant")
    if paper_result_eligible_count == 0 and labeled_variant_count:
        claim_limitations.extend(
            [
                "no_exact_official_non_avg_blip_checkpoint_after_documented_oom_attempts",
                "selected_checkpoint_is_averaged_blip_open3dsg_variant_not_exact_non_avg_open3dsg",
                "downstream_table_must_label_open3dsg_source_as_avg_blip_variant",
            ]
        )
    status = STATUS_READY_MISSING
    if candidates:
        status = STATUS_READY_WITH_CANDIDATES
    if selected_checkpoint and selected_checkpoint.get("paper_result_eligible") is True and not blockers:
        status = STATUS_READY_SELECTED_OFFICIAL
    elif selected_checkpoint and selected_checkpoint.get("paper_result_eligible") == "labeled_variant_only" and not blockers:
        status = STATUS_READY_SELECTED_VARIANT
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": status,
        "checkpoint_dir": relpath(repo_root, checkpoint_dir),
        "candidate_count": len(candidates),
        "paper_result_eligible_candidate_count": paper_result_eligible_count,
        "labeled_variant_candidate_count": labeled_variant_count,
        "candidate_checkpoints": candidates,
        "selected_checkpoint": selected_checkpoint,
        "route_comparison": route_comparison,
        "source_statuses": statuses,
        "feature_audit_status": statuses["feature_audit"],
        "source_artifacts": artifact_records(repo_root, source_paths),
        "selection_policy": "selection_policy.json",
        "record_template": "record_template.json",
        "blockers": blockers,
        "claim_limitations": claim_limitations,
        "claim_boundary": (
            "This artifact freezes provenance and selection policy only. It is not Open3DSG metric "
            "evidence and it is not permission to select a checkpoint using H001 held-out metrics. "
            "If the selected checkpoint is non-avg, downstream evidence must be regenerated under "
            "separate non-avg output paths before paper wording changes. If the selected checkpoint "
            "is avg-BLIP, downstream evidence must be labeled as an averaged-BLIP Open3DSG variant."
        ),
        "next_action_after_checkpoint": (
            "Run eval_preflight with the selected checkpoint before raw dump/eval."
        ),
    }

    write_json(out_dir / "selection_policy.json", policy)
    write_json(out_dir / "record_template.json", template)
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "commands.md").write_text(build_commands(), encoding="utf-8")
    (out_dir / "report.md").write_text(build_report(manifest), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": manifest["status"],
                "candidate_count": manifest["candidate_count"],
                "selected_checkpoint": manifest["selected_checkpoint"]["checkpoint_path"] if manifest["selected_checkpoint"] else None,
                "blockers": manifest["blockers"],
                "out": relpath(repo_root, out_dir),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
