#!/usr/bin/env python3
"""Review Open3DSG raw-dump provenance and row equivalence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_open3dsg_raw_provenance_review_v1"
STATUS_READY = "open3dsg_raw_provenance_review_ready"
STATUS_BLOCKED = "open3dsg_raw_provenance_review_blocked"
SCORE_TOLERANCE = 1e-9
RAW_METADATA_KEYS = {"baseline_run_id", "checkpoint_path", "model_source_stage"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument(
        "--mode",
        choices=("full_validation_clean_exit", "h001_covered_recovery_sensitivity"),
        required=True,
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/raw_provenance_review"),
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


def read_json(path: Path) -> Any | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_text(path: Path) -> str | None:
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace").strip()


def parse_exit_code(text: str | None) -> int | None:
    if text is None:
        return None
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def line_count(path: Path) -> int | None:
    if not path.is_file():
        return None
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def file_summary(repo_root: Path, path: Path) -> dict[str, Any]:
    return {
        "path": relpath(repo_root, path),
        "exists": path.is_file(),
        "bytes": path.stat().st_size if path.is_file() else None,
        "lines": line_count(path),
        "sha256": sha256_file(path),
    }


def stream_summary(repo_root: Path, path: Path) -> dict[str, Any]:
    data = read_json(path)
    return {
        "path": relpath(repo_root, path),
        "exists": path.is_file(),
        "status": data.get("status") if isinstance(data, dict) else None,
        "rows_written": data.get("rows_written") if isinstance(data, dict) else None,
        "completed_batches": data.get("completed_batches") if isinstance(data, dict) else None,
        "total_batches": data.get("total_batches") if isinstance(data, dict) else None,
        "dropped_partial_rows": data.get("dropped_partial_rows") if isinstance(data, dict) else None,
        "invalid_partial_rows": data.get("invalid_partial_rows") if isinstance(data, dict) else None,
    }


def exit_summary(repo_root: Path, path: Path) -> dict[str, Any]:
    text = read_text(path)
    return {
        "path": relpath(repo_root, path),
        "exists": path.is_file(),
        "raw_text": text,
        "exit_code": parse_exit_code(text),
    }


def log_summary(repo_root: Path, path: Path) -> dict[str, Any]:
    patterns = {
        "finalized": re.compile(r"raw dump stream finalized"),
        "returning_cleanly": re.compile(r"returning cleanly"),
        "traceback": re.compile(r"Traceback"),
        "exception": re.compile(r"Exception|exception"),
        "killed": re.compile(r"Killed|killed"),
        "oom": re.compile(r"out of memory|OutOfMemory|container oom|CUDA out of memory", re.I),
    }
    counts = {key: 0 for key in patterns}
    last_matches: dict[str, str | None] = {key: None for key in patterns}
    line_total = 0
    if path.is_file():
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line_total += 1
                stripped = line.strip()
                for key, pattern in patterns.items():
                    if pattern.search(stripped):
                        counts[key] += 1
                        last_matches[key] = stripped[-500:]
    return {
        "path": relpath(repo_root, path),
        "exists": path.is_file(),
        "lines": line_total if path.is_file() else None,
        "pattern_counts": counts,
        "last_matches": last_matches,
    }


def row_identity(row: dict[str, Any]) -> str:
    edge = row.get("edge", {})
    return "|".join(
        str(value)
        for value in (
            row.get("scan_id"),
            row.get("subset_split_id"),
            row.get("subgraph_id"),
            edge.get("subject_id"),
            edge.get("object_id"),
        )
    )


def normalized_row(row: dict[str, Any]) -> dict[str, Any]:
    kept = {key: value for key, value in row.items() if key not in RAW_METADATA_KEYS}
    scores = kept.get("predicate_scores", [])
    if isinstance(scores, list):
        kept["predicate_scores"] = sorted(
            scores,
            key=lambda item: (
                item.get("raw_3dssg_predicate_id"),
                item.get("open3dsg_predicate_index"),
                item.get("predicate_label"),
            ),
        )
    return kept


def row_digest(row: dict[str, Any]) -> str:
    payload = json.dumps(normalized_row(row), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def score_map(row: dict[str, Any]) -> dict[str, float]:
    scores: dict[str, float] = {}
    for item in row.get("predicate_scores", []):
        label = item.get("predicate_label")
        score = item.get("score")
        if label is not None and score is not None:
            scores[str(label)] = float(score)
    return scores


def raw_index(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "exists": False,
            "row_count": None,
            "invalid_json_lines": None,
            "normalized_counter": Counter(),
            "identity_counter": Counter(),
            "scores_by_key": {},
            "schema_versions": Counter(),
            "record_types": Counter(),
            "baseline_run_ids": Counter(),
            "model_source_stages": Counter(),
        }
    normalized_counter: Counter[str] = Counter()
    identity_counter: Counter[str] = Counter()
    scores_by_key: dict[str, dict[str, float]] = {}
    schema_versions: Counter[str] = Counter()
    record_types: Counter[str] = Counter()
    baseline_run_ids: Counter[str] = Counter()
    model_source_stages: Counter[str] = Counter()
    invalid = 0
    row_count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                invalid += 1
                continue
            row_count += 1
            key = row_identity(row)
            normalized_counter[row_digest(row)] += 1
            identity_counter[key] += 1
            if identity_counter[key] == 1:
                scores_by_key[key] = score_map(row)
            schema_versions[str(row.get("schema_version"))] += 1
            record_types[str(row.get("record_type"))] += 1
            baseline_run_ids[str(row.get("baseline_run_id"))] += 1
            model_source_stages[str(row.get("model_source_stage"))] += 1
    return {
        "exists": True,
        "row_count": row_count,
        "invalid_json_lines": invalid,
        "normalized_counter": normalized_counter,
        "identity_counter": identity_counter,
        "scores_by_key": scores_by_key,
        "schema_versions": schema_versions,
        "record_types": record_types,
        "baseline_run_ids": baseline_run_ids,
        "model_source_stages": model_source_stages,
    }


def counter_delta(left: Counter[str], right: Counter[str], limit: int = 5) -> list[dict[str, Any]]:
    delta = left - right
    return [{"digest": key, "count": value} for key, value in delta.most_common(limit)]


def compare_raw_jsonl(repo_root: Path, left: Path, right: Path) -> dict[str, Any]:
    left_file = file_summary(repo_root, left)
    right_file = file_summary(repo_root, right)
    if not left.is_file() or not right.is_file():
        return {
            "left": left_file,
            "right": right_file,
            "status": "not_evaluable_missing_file",
            "byte_equal": False,
            "normalized_payload_equal": False,
            "identity_key_set_equal": False,
            "score_payload_equal_for_unique_keys": False,
        }

    left_index = raw_index(left)
    right_index = raw_index(right)
    normalized_equal = left_index["normalized_counter"] == right_index["normalized_counter"]
    identity_equal = left_index["identity_counter"] == right_index["identity_counter"]
    duplicate_left = sum(1 for value in left_index["identity_counter"].values() if value > 1)
    duplicate_right = sum(1 for value in right_index["identity_counter"].values() if value > 1)

    max_abs_delta = 0.0
    score_mismatch_count = 0
    missing_score_keys = 0
    score_equal = identity_equal and duplicate_left == 0 and duplicate_right == 0
    if score_equal:
        for key, left_scores in left_index["scores_by_key"].items():
            right_scores = right_index["scores_by_key"].get(key)
            if right_scores is None:
                missing_score_keys += 1
                score_equal = False
                continue
            if set(left_scores) != set(right_scores):
                score_mismatch_count += 1
                score_equal = False
                continue
            for label, left_score in left_scores.items():
                delta = abs(left_score - right_scores[label])
                max_abs_delta = max(max_abs_delta, delta)
                if delta > SCORE_TOLERANCE:
                    score_mismatch_count += 1
                    score_equal = False
                    break

    byte_equal = left_file["sha256"] == right_file["sha256"]
    status = (
        "row_equivalent"
        if normalized_equal and identity_equal and score_equal
        else "row_equivalence_mismatch"
    )
    return {
        "left": left_file,
        "right": right_file,
        "status": status,
        "byte_equal": byte_equal,
        "metadata_diff_only": bool(not byte_equal and normalized_equal and score_equal),
        "normalized_payload_equal": normalized_equal,
        "identity_key_multiset_equal": identity_equal,
        "score_payload_equal_for_unique_keys": score_equal,
        "score_tolerance": SCORE_TOLERANCE,
        "max_abs_score_delta": max_abs_delta,
        "score_mismatch_count": score_mismatch_count,
        "missing_score_keys": missing_score_keys,
        "duplicate_identity_keys": {"left": duplicate_left, "right": duplicate_right},
        "row_counts": {"left": left_index["row_count"], "right": right_index["row_count"]},
        "invalid_json_lines": {
            "left": left_index["invalid_json_lines"],
            "right": right_index["invalid_json_lines"],
        },
        "schema_versions": {
            "left": dict(left_index["schema_versions"]),
            "right": dict(right_index["schema_versions"]),
        },
        "record_types": {
            "left": dict(left_index["record_types"]),
            "right": dict(right_index["record_types"]),
        },
        "baseline_run_ids": {
            "left": dict(left_index["baseline_run_ids"]),
            "right": dict(right_index["baseline_run_ids"]),
        },
        "model_source_stages": {
            "left": dict(left_index["model_source_stages"]),
            "right": dict(right_index["model_source_stages"]),
        },
        "normalized_only_in_left_sample": counter_delta(
            left_index["normalized_counter"], right_index["normalized_counter"]
        ),
        "normalized_only_in_right_sample": counter_delta(
            right_index["normalized_counter"], left_index["normalized_counter"]
        ),
    }


def metric_value(metrics: dict[str, Any] | None, condition: str, block: str, k: int, key: str) -> float | None:
    if not metrics:
        return None
    value = (
        metrics.get("conditions", {})
        .get(condition, {})
        .get(block, {})
        .get("by_k", {})
        .get(str(k), {})
        .get(key)
    )
    return None if value is None else float(value)


def metric_row(metrics: dict[str, Any] | None, condition: str) -> dict[str, float | None]:
    return {
        "R@50": metric_value(metrics, condition, "recall", 50, "recall"),
        "R@100": metric_value(metrics, condition, "recall", 100, "recall"),
        "Violation@50": metric_value(metrics, condition, "violation_rate", 50, "violation_rate"),
        "Violation@100": metric_value(metrics, condition, "violation_rate", 100, "violation_rate"),
    }


def build_full_validation_payload(repo_root: Path) -> dict[str, Any]:
    root = repo_root / "experiments/H001_geom_reliability/sources/open3dsg/full_validation"
    recovery = root / "recovery_relaxed_views_min2"
    retry = root / "raw_dump_exit0_retry_20260605_000241"
    retry_candidates = sorted(root.glob("raw_dump_exit0_retry_*"))

    unmodified_log = repo_root / "logs/open3dsg_full_validation_raw_20260604_222446.log"
    unmodified_exit = repo_root / "logs/open3dsg_full_validation_raw_20260604_222446.exit"
    recovery_log_candidates = sorted(repo_root.glob("logs/h001_open3dsg_fullval_recovery_raw_*.log"))
    recovery_exit_candidates = sorted(repo_root.glob("logs/h001_open3dsg_fullval_recovery_raw_*.exit"))
    recovery_log = recovery_log_candidates[-1] if recovery_log_candidates else Path("")
    recovery_exit = recovery_exit_candidates[-1] if recovery_exit_candidates else Path("")

    retry_compare = compare_raw_jsonl(repo_root, root / "raw_dump/raw.jsonl", retry / "raw.jsonl")
    retry_status = "not_evaluable_retry_artifact_missing"
    if retry.is_dir() and (retry / "raw.jsonl").is_file():
        retry_status = retry_compare["status"]

    blockers: list[str] = []
    if retry_status == "row_equivalence_mismatch":
        blockers.append("retry_raw_equivalence_mismatch")
    if retry_status == "not_evaluable_retry_artifact_missing":
        blockers.append("retry_artifact_missing_no_clean_exit_replacement")

    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now(),
        "mode": "full_validation_clean_exit",
        "status": STATUS_READY,
        "claim_boundary": (
            "This review concerns provenance polish for the unmodified 533/548 "
            "Open3DSG full-validation branch. The paper-facing primary Open3DSG "
            "route remains the 548/548 recovery branch, whose raw dump already "
            "has clean-exit provenance."
        ),
        "inputs": {
            "unmodified_root": relpath(repo_root, root),
            "primary_recovery_root": relpath(repo_root, recovery),
            "expected_retry_root": relpath(repo_root, retry),
            "existing_retry_candidates": [relpath(repo_root, path) for path in retry_candidates],
        },
        "unmodified_source_route": {
            "coverage": "533/548",
            "role": "public-source/as-is sensitivity branch",
            "raw": file_summary(repo_root, root / "raw_dump/raw.jsonl"),
            "stream": stream_summary(repo_root, root / "raw_dump/stream_manifest.json"),
            "identity_status": (read_json(root / "raw_dump_identity/manifest.json") or {}).get("status"),
            "process_exit": exit_summary(repo_root, unmodified_exit),
            "log": log_summary(repo_root, unmodified_log),
        },
        "primary_recovery_route": {
            "coverage": "548/548",
            "role": "paper-facing primary Open3DSG full-validation route",
            "raw": file_summary(repo_root, recovery / "raw_dump/raw.jsonl"),
            "stream": stream_summary(repo_root, recovery / "raw_dump/stream_manifest.json"),
            "identity_status": (read_json(recovery / "raw_dump_identity/manifest.json") or {}).get("status"),
            "process_exit": exit_summary(repo_root, recovery_exit),
            "log": log_summary(repo_root, recovery_log),
        },
        "retry_equivalence": {
            "expected_retry_root": relpath(repo_root, retry),
            "retry_root_exists": retry.is_dir(),
            "retry_raw_exists": (retry / "raw.jsonl").is_file(),
            "status": retry_status,
            "comparison": retry_compare,
        },
        "decision": {
            "reduce_unmodified_process_137_caveat": retry_status == "row_equivalent",
            "paper_main_result_changed": False,
            "recommended_wording": (
                "Keep the unmodified 533/548 branch as sensitivity evidence with "
                "post-finalization exit-137 caveat. Use the 548/548 recovery branch "
                "as the main Open3DSG full-validation result with its recovery-policy caveat."
            ),
        },
        "blockers": blockers,
    }


def build_h001_r2_payload(repo_root: Path) -> dict[str, Any]:
    root = repo_root / "experiments/H001_geom_reliability/sources/open3dsg/h001_covered_recovery"
    canonical = root / "raw_dump/raw.jsonl"
    clean1 = root / "raw_dump_clean_return_20260606_003130/raw.jsonl"
    clean2 = root / "raw_dump_clean_return_retry2_20260606_021154/raw.jsonl"
    metrics = read_json(root / "metrics/metrics.json")
    table_report = read_json(root / "table_caveats/manifest.json")

    comparisons = {
        "canonical_vs_clean_return": compare_raw_jsonl(repo_root, canonical, clean1),
        "canonical_vs_clean_return_retry2": compare_raw_jsonl(repo_root, canonical, clean2),
    }
    blockers = [
        name
        for name, result in comparisons.items()
        if result["status"] != "row_equivalent"
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now(),
        "mode": "h001_covered_recovery_sensitivity",
        "status": STATUS_READY if not blockers else STATUS_BLOCKED,
        "claim_boundary": (
            "This is an appendix/sensitivity branch for the historical 127-scan "
            "H001 covered scope. It is not the paper-facing full-validation main route."
        ),
        "inputs": {
            "r2_root": relpath(repo_root, root),
            "canonical_raw": relpath(repo_root, canonical),
            "clean_return_raw": relpath(repo_root, clean1),
            "clean_return_retry2_raw": relpath(repo_root, clean2),
        },
        "coverage": {
            "preprocess": "388/388",
            "features": "388/388",
            "canonical_stream": stream_summary(repo_root, root / "raw_dump/stream_manifest.json"),
            "clean_return_stream": stream_summary(
                repo_root, root / "raw_dump_clean_return_20260606_003130/stream_manifest.json"
            ),
            "clean_return_retry2_stream": stream_summary(
                repo_root, root / "raw_dump_clean_return_retry2_20260606_021154/stream_manifest.json"
            ),
            "canonical_raw_identity_status": (read_json(root / "raw_dump_identity/manifest.json") or {}).get("status"),
            "downstream_table_status": (table_report or {}).get("status"),
        },
        "process_exits": {
            "clean_return": exit_summary(
                repo_root, repo_root / "logs/open3dsg_h001_r2_raw_clean_return_20260606_003130.exit"
            ),
            "clean_return_retry2": exit_summary(
                repo_root, repo_root / "logs/open3dsg_h001_r2_raw_clean_return_retry2_20260606_021154.exit"
            ),
        },
        "logs": {
            "clean_return": log_summary(
                repo_root, repo_root / "logs/open3dsg_h001_r2_raw_clean_return_20260606_003130.log"
            ),
            "clean_return_retry2": log_summary(
                repo_root, repo_root / "logs/open3dsg_h001_r2_raw_clean_return_retry2_20260606_021154.log"
            ),
        },
        "raw_equivalence": comparisons,
        "metrics": {
            "semantic_only": metric_row(metrics, "semantic_only"),
            "probabilistic_recalibrated": metric_row(metrics, "probabilistic_recalibrated"),
            "rule_verified_point_subtype": metric_row(metrics, "rule_verified_point_subtype"),
            "control_family_specific_p_geom_valid": metric_row(metrics, "control_family_specific_p_geom_valid"),
        },
        "decision": {
            "appendix_sensitivity_ready": not blockers
            and (table_report or {}).get("status") == "open3dsg_h001_covered_recovery_sensitivity_ready",
            "paper_main_result_changed": False,
            "recommended_wording": (
                "Use R2 as appendix robustness evidence: the old 377/388 historical "
                "scope caveat does not drive the Open3DSG trend. Do not use it to "
                "replace the current full-validation 548/548 recovery main route."
            ),
            "raw_dump_only_runner_needed_now": False,
        },
        "blockers": blockers,
    }


def render_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Open3DSG Raw Provenance Review",
        "",
        f"Status: `{payload['status']}`",
        f"Mode: `{payload['mode']}`",
        f"Created at: `{payload['created_at_utc']}`",
        "",
        "## Claim Boundary",
        "",
        payload["claim_boundary"],
        "",
    ]
    if payload["mode"] == "full_validation_clean_exit":
        retry = payload["retry_equivalence"]
        lines.extend(
            [
                "## Full-Validation Clean-Exit Review",
                "",
                f"- unmodified route coverage: `{payload['unmodified_source_route']['coverage']}`",
                f"- unmodified raw rows: `{payload['unmodified_source_route']['raw']['lines']}`",
                f"- unmodified process exit: `{payload['unmodified_source_route']['process_exit']['exit_code']}`",
                f"- primary recovery coverage: `{payload['primary_recovery_route']['coverage']}`",
                f"- primary recovery raw rows: `{payload['primary_recovery_route']['raw']['lines']}`",
                f"- retry artifact status: `{retry['status']}`",
                f"- reduce unmodified exit-137 caveat: `{payload['decision']['reduce_unmodified_process_137_caveat']}`",
                "",
                "## Decision",
                "",
                payload["decision"]["recommended_wording"],
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## H001 Covered-Recovery Sensitivity",
                "",
                f"- preprocess coverage: `{payload['coverage']['preprocess']}`",
                f"- feature coverage: `{payload['coverage']['features']}`",
                f"- canonical raw rows: `{payload['coverage']['canonical_stream']['rows_written']}`",
                f"- clean-return retry2 raw rows: `{payload['coverage']['clean_return_retry2_stream']['rows_written']}`",
                f"- clean-return retry2 process exit: `{payload['process_exits']['clean_return_retry2']['exit_code']}`",
                f"- canonical vs clean-return retry2 equivalence: `{payload['raw_equivalence']['canonical_vs_clean_return_retry2']['status']}`",
                f"- downstream table status: `{payload['coverage']['downstream_table_status']}`",
                "",
                "## Metric Snapshot",
                "",
                "| condition | R@50 | R@100 | V@50 | V@100 |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for condition, row in payload["metrics"].items():
            lines.append(
                f"| {condition} | {fmt(row['R@50'])} | {fmt(row['R@100'])} | "
                f"{fmt(row['Violation@50'])} | {fmt(row['Violation@100'])} |"
            )
        lines.extend(["", "## Decision", "", payload["decision"]["recommended_wording"], ""])
    if payload.get("blockers"):
        lines.extend(["## Blockers", ""])
        lines.extend(f"- `{item}`" for item in payload["blockers"])
        lines.append("")
    return "\n".join(lines)


def fmt(value: float | None) -> str:
    return "NA" if value is None else f"{value:.4f}"


def render_commands(mode: str) -> str:
    service = (
        "open3dsg_full_validation_raw_clean_exit_review"
        if mode == "full_validation_clean_exit"
        else "open3dsg_h001_covered_recovery_provenance_review"
    )
    return "\n".join(
        [
            "# Raw Provenance Review Commands",
            "",
            "Run from the repository root:",
            "",
            "```bash",
            f"env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm {service}",
            "```",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out_dir = resolve(repo_root, args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.mode == "full_validation_clean_exit":
        payload = build_full_validation_payload(repo_root)
    else:
        payload = build_h001_r2_payload(repo_root)
    write_json(out_dir / "manifest.json", payload)
    if args.mode == "h001_covered_recovery_sensitivity":
        write_json(out_dir / "raw_equivalence.json", payload["raw_equivalence"])
    (out_dir / "report.md").write_text(render_report(payload), encoding="utf-8")
    (out_dir / "commands.md").write_text(render_commands(args.mode), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "out": relpath(repo_root, out_dir)}, sort_keys=True))
    return 0 if payload["status"] == STATUS_READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
