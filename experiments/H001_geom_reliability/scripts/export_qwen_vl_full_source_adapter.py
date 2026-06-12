#!/usr/bin/env python3
"""Aggregate Qwen-VL full-source shards and export H001 prediction rows."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_qwen_vl_full_source_adapter_export_v1"
AGGREGATE_STATUS = "qwen_vl_full_source_aggregate_ready"
EXPORT_STATUS = "qwen_vl_adapter_export_ready"
BASELINE_NAME = "qwen_vl_semantic_source"
DEFAULT_BASELINE_RUN_ID = "qwen3_vl_4b_full_source_semantic_v1"
DEFAULT_SPLIT_NAME = "h001_validation_hardened_qwen_inferable"
TARGET_FAMILIES = {"support_contact", "proximity", "relative_vertical"}

CANONICAL_PREDICATE_MAP = {
    "next to": "close by",
    "near": "close by",
    "close by": "close by",
    "above": "higher than",
    "higher than": "higher than",
    "under": "lower than",
    "lower than": "lower than",
    "standing on": "standing on",
    "lying on": "lying on",
    "supported by": "supported by",
    "attached to": "attached to",
    "hanging on": "hanging on",
    "connected to": "connected to",
    "part of": "part of",
    "far from": "far from",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--mode", choices=["aggregate", "export_adapter"], required=True)
    parser.add_argument(
        "--qwen-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl"),
    )
    parser.add_argument(
        "--runtime-root",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/full_source_runtime"),
    )
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/input.jsonl"),
    )
    parser.add_argument(
        "--shards-jsonl",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/full_source_input/shards.jsonl"),
    )
    parser.add_argument(
        "--validation-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/full_source_validation"),
    )
    parser.add_argument(
        "--parsed-jsonl",
        type=Path,
        default=Path(
            "experiments/H001_geom_reliability/sources/qwen_vl/full_source_validation/contract/parsed.jsonl"
        ),
    )
    parser.add_argument(
        "--ground-truth-jsonl",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/evaluation/"
            "vlsat_closed_set/hardened/ground_truth.jsonl"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/qwen_vl/adapter"),
    )
    parser.add_argument("--baseline-run-id", default=DEFAULT_BASELINE_RUN_ID)
    parser.add_argument("--split-name", default=DEFAULT_SPLIT_NAME)
    return parser.parse_args()


def resolve(repo_root: Path, path: Path | None) -> Path | None:
    if path is None:
        return None
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.rstrip("\n")
            if line.strip():
                try:
                    yield line_no, line, json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"invalid_jsonl:{path}:{line_no}") from exc


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
            handle.write("\n")


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def read_rows(path: Path) -> list[dict[str, Any]]:
    return [row for _line_no, _line, row in iter_jsonl(path)]


def read_input_rows(path: Path) -> tuple[list[tuple[str, dict[str, Any]]], dict[str, tuple[str, dict[str, Any]]]]:
    rows: list[tuple[str, dict[str, Any]]] = []
    by_id: dict[str, tuple[str, dict[str, Any]]] = {}
    for _line_no, line, row in iter_jsonl(path):
        record_id = str(row["record_id"])
        rows.append((line, row))
        by_id[record_id] = (line, row)
    return rows, by_id


def subset_split_id(subgraph_id: str) -> int:
    try:
        return int(str(subgraph_id).rsplit("_", 1)[1])
    except (IndexError, ValueError) as exc:
        raise ValueError(f"cannot_parse_subset_split_id:{subgraph_id}") from exc


def predicate_family(label: str) -> str:
    if label in {"standing on", "lying on", "supported by"}:
        return "support_contact"
    if label == "close by":
        return "proximity"
    if label in {"higher than", "lower than"}:
        return "relative_vertical"
    if label in {"left", "right", "front", "behind", "in front of"}:
        return "relative_horizontal"
    if label in {"attached to", "hanging on", "mounted on", "connected to"}:
        return "attachment_deferred"
    return "unsupported_first_pass"


def canonical_predicate(raw_label: str) -> tuple[str, str | None]:
    canonical = CANONICAL_PREDICATE_MAP.get(raw_label, raw_label)
    if canonical != raw_label:
        return canonical, f"canonicalized_predicate:{raw_label}->{canonical}"
    return canonical, None


def score_value(value: Any, rank: int) -> tuple[float, str]:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 1.0 / max(rank, 1), "qwen_rank_fallback"
    if not (0.0 <= score <= 1.0):
        return 1.0 / max(rank, 1), "qwen_rank_fallback"
    return score, "qwen_self_confidence"


def pair_index_map(input_rows: list[tuple[str, dict[str, Any]]]) -> dict[tuple[str, int, int, int], int]:
    pairs: dict[str, set[tuple[int, int, int]]] = defaultdict(set)
    for _line, row in input_rows:
        key = (
            subset_split_id(str(row["subgraph_id"])),
            int(row["subject_id"]),
            int(row["object_id"]),
        )
        pairs[str(row["subgraph_id"])].add(key)
    result: dict[tuple[str, int, int, int], int] = {}
    for subgraph_id, subgraph_pairs in pairs.items():
        for index, (split_id, subject_id, object_id) in enumerate(sorted(subgraph_pairs)):
            result[(subgraph_id, split_id, subject_id, object_id)] = index
    return result


def aggregate(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve()
    runtime_root = resolve(repo_root, args.runtime_root)
    input_jsonl = resolve(repo_root, args.input_jsonl)
    shards_jsonl = resolve(repo_root, args.shards_jsonl)
    validation_dir = resolve(repo_root, args.validation_dir)
    assert runtime_root is not None and input_jsonl is not None and shards_jsonl is not None
    assert validation_dir is not None
    validation_dir.mkdir(parents=True, exist_ok=True)

    input_rows, input_by_id = read_input_rows(input_jsonl)
    shards = read_rows(shards_jsonl)
    expected_shard_ids = [str(row["shard_id"]) for row in shards]

    raw_out = validation_dir / "raw_response.jsonl"
    runtime_pred_out = validation_dir / "runtime_predictions.jsonl"
    completed_out = validation_dir / "completed.jsonl"
    raw_rows: list[dict[str, Any]] = []
    pred_rows: list[dict[str, Any]] = []
    completed_rows: list[dict[str, Any]] = []
    manifest_errors: list[str] = []
    parser_counts: Counter[str] = Counter()

    for shard_id in expected_shard_ids:
        manifest_path = runtime_root / "manifests" / f"{shard_id}.json"
        prediction_path = runtime_root / "predictions" / f"{shard_id}.jsonl"
        raw_path = runtime_root / "raw_response" / f"{shard_id}.jsonl"
        completed_path = runtime_root / "progress" / f"{shard_id}.completed.jsonl"
        for path_name, path in {
            "manifest": manifest_path,
            "predictions": prediction_path,
            "raw_response": raw_path,
            "completed": completed_path,
        }.items():
            if not path.exists():
                manifest_errors.append(f"missing_{path_name}:{shard_id}:{relpath(repo_root, path)}")
        if manifest_path.exists():
            manifest = load_json(manifest_path)
            if manifest.get("status") != "full_source_inference_shard_complete":
                manifest_errors.append(f"bad_manifest_status:{shard_id}:{manifest.get('status')}")
        if raw_path.exists():
            raw_rows.extend(read_rows(raw_path))
        if prediction_path.exists():
            rows = read_rows(prediction_path)
            for row in rows:
                parser_counts[str(row.get("parser_status"))] += 1
            pred_rows.extend(rows)
        if completed_path.exists():
            completed_rows.extend(read_rows(completed_path))

    raw_ids = [str(row.get("record_id")) for row in raw_rows]
    pred_ids = [str(row.get("record_id")) for row in pred_rows]
    completed_ids = [str(row.get("record_id")) for row in completed_rows]
    input_ids = set(input_by_id)
    raw_id_set = set(raw_ids)
    pred_id_set = set(pred_ids)
    completed_id_set = set(completed_ids)
    duplicates = {
        "raw_response": [item for item, count in Counter(raw_ids).items() if count > 1],
        "predictions": [item for item, count in Counter(pred_ids).items() if count > 1],
        "completed": [item for item, count in Counter(completed_ids).items() if count > 1],
    }
    missing = {
        "raw_response": sorted(input_ids - raw_id_set)[:20],
        "predictions": sorted(input_ids - pred_id_set)[:20],
        "completed": sorted(input_ids - completed_id_set)[:20],
    }
    blockers = list(manifest_errors)
    for name, items in duplicates.items():
        if items:
            blockers.append(f"duplicate_{name}_record_ids:{len(items)}")
    for name, items in missing.items():
        if items:
            blockers.append(f"missing_{name}_record_ids:{len(input_ids - {'raw_response': raw_id_set, 'predictions': pred_id_set, 'completed': completed_id_set}[name])}")

    write_jsonl(raw_out, raw_rows)
    write_jsonl(runtime_pred_out, pred_rows)
    write_jsonl(completed_out, completed_rows)

    status = AGGREGATE_STATUS if not blockers else "blocked_qwen_vl_full_source_aggregate"
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "mode": "aggregate",
        "status": status,
        "inputs": {
            "input_jsonl": relpath(repo_root, input_jsonl),
            "shards_jsonl": relpath(repo_root, shards_jsonl),
            "runtime_root": relpath(repo_root, runtime_root),
        },
        "outputs": {
            "raw_response_jsonl": relpath(repo_root, raw_out),
            "runtime_predictions_jsonl": relpath(repo_root, runtime_pred_out),
            "completed_jsonl": relpath(repo_root, completed_out),
            "manifest": relpath(repo_root, validation_dir / "aggregate_manifest.json"),
            "report": relpath(repo_root, validation_dir / "aggregate_report.md"),
        },
        "counts": {
            "input_rows": len(input_rows),
            "expected_shards": len(expected_shard_ids),
            "raw_response_rows": len(raw_rows),
            "runtime_prediction_rows": len(pred_rows),
            "completed_rows": len(completed_rows),
            "parser_status": dict(sorted(parser_counts.items())),
        },
        "duplicates": {name: len(items) for name, items in duplicates.items()},
        "missing_samples": missing,
        "blockers": blockers,
        "paper_metric": False,
        "next_gate": "run_qwen_vl_full_source_validate_then_qwen_vl_adapter_export",
    }
    write_json(validation_dir / "aggregate_manifest.json", manifest)
    (validation_dir / "aggregate_report.md").write_text(render_aggregate_report(manifest), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, validation_dir)}, sort_keys=True))
    return 0 if not blockers else 1


def gt_key(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (
        str(row["scan_id"]),
        int(row["subset_split_id"]),
        int(row["subject_id"]),
        int(row["object_id"]),
        str(row["predicate_label"]),
    )


def family_key(row: dict[str, Any]) -> tuple[str, int, int, int, str]:
    return (
        str(row["scan_id"]),
        int(row["subset_split_id"]),
        int(row["subject_id"]),
        int(row["object_id"]),
        str(row["predicate_family"]),
    )


def export_adapter(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve()
    input_jsonl = resolve(repo_root, args.input_jsonl)
    parsed_jsonl = resolve(repo_root, args.parsed_jsonl)
    gt_jsonl = resolve(repo_root, args.ground_truth_jsonl)
    out_dir = resolve(repo_root, args.out)
    assert input_jsonl is not None and parsed_jsonl is not None and gt_jsonl is not None and out_dir is not None
    out_dir.mkdir(parents=True, exist_ok=True)

    input_rows, input_by_id = read_input_rows(input_jsonl)
    pairs = pair_index_map(input_rows)
    parsed_rows = read_rows(parsed_jsonl)
    gt_rows = read_rows(gt_jsonl)
    gt_out = out_dir / "ground_truth.jsonl"
    shutil.copyfile(gt_jsonl, gt_out)

    input_family_keys = {
        (
            str(row["scan_id"]),
            subset_split_id(str(row["subgraph_id"])),
            int(row["subject_id"]),
            int(row["object_id"]),
            str(row["predicate_family"]),
        )
        for _line, row in input_rows
    }
    scoped_gt = [row for row in gt_rows if row.get("predicate_family") in TARGET_FAMILIES]
    covered_gt = [row for row in scoped_gt if family_key(row) in input_family_keys]

    predictions: list[dict[str, Any]] = []
    parser_counts: Counter[str] = Counter()
    raw_predicate_counts: Counter[str] = Counter()
    canonical_counts: Counter[str] = Counter()
    family_counts: Counter[str] = Counter()
    export_warnings: list[str] = []
    skipped_counts: Counter[str] = Counter()
    dedup_keys: set[tuple[str, str]] = set()

    for row in parsed_rows:
        record_id = str(row.get("record_id"))
        parser_status = str(row.get("parser_status"))
        parser_counts[parser_status] += 1
        linked = input_by_id.get(record_id)
        if linked is None:
            skipped_counts["missing_input_record"] += 1
            export_warnings.append(f"missing_input_record:{record_id}")
            continue
        _input_line, input_row = linked
        split_id = subset_split_id(str(input_row["subgraph_id"]))
        subject_id = int(input_row["subject_id"])
        object_id = int(input_row["object_id"])
        edge_index = pairs[(str(input_row["subgraph_id"]), split_id, subject_id, object_id)]
        for pred in row.get("predictions", []):
            raw_label = str(pred.get("predicate") or "")
            raw_predicate_counts[raw_label] += 1
            canonical_label, warning = canonical_predicate(raw_label)
            family = predicate_family(canonical_label)
            canonical_counts[canonical_label] += 1
            family_counts[family] += 1
            dedup_key = (record_id, canonical_label)
            if dedup_key in dedup_keys:
                skipped_counts["duplicate_canonical_predicate"] += 1
                continue
            dedup_keys.add(dedup_key)
            rank = int(pred.get("rank") or 1)
            score, score_type = score_value(pred.get("semantic_score"), rank)
            warnings = list(row.get("warnings") or [])
            if warning:
                warnings.append(warning)
            if family not in TARGET_FAMILIES:
                warnings.append(f"predicate_family_outside_current_h001_metric:{family}")
            prediction_id = (
                f"{BASELINE_NAME}:{args.split_name}:{input_row['scan_id']}:{split_id}:"
                f"{subject_id}:{object_id}:{canonical_label}"
            )
            predictions.append(
                {
                    "schema_version": "h001_prediction_v1",
                    "record_type": "prediction",
                    "prediction_id": prediction_id,
                    "baseline_name": BASELINE_NAME,
                    "baseline_run_id": args.baseline_run_id,
                    "split_name": args.split_name,
                    "scan_id": input_row["scan_id"],
                    "subgraph_id": input_row["subgraph_id"],
                    "subset_split_id": split_id,
                    "subset_source": "local_dataset/3DSSG_subset/relationships_validation.json",
                    "task_mode": "visual_pair_relation_query",
                    "adapter": {
                        "name": "qwen_vl_to_h001_predictions",
                        "version": "v1",
                        "raw_schema_version": row.get("schema_version"),
                        "export_policy": "parsed_qwen_predictions_with_h001_canonicalization",
                        "qwen_record_id": record_id,
                        "qwen_input_predicate_family": input_row.get("predicate_family"),
                        "qwen_parser_status": parser_status,
                        "qwen_raw_predicate_label": raw_label,
                        "canonicalization_warning": warning,
                    },
                    "edge": {
                        "edge_index": edge_index,
                        "edge_source": "qwen_vl_full_source_input",
                        "subject_id": subject_id,
                        "object_id": object_id,
                        "subject_label": input_row.get("subject_label"),
                        "object_label": input_row.get("object_label"),
                        "subject_label_source": "3DSSG_subset",
                        "object_label_source": "3DSSG_subset",
                        "subject_node_index": None,
                        "object_node_index": None,
                    },
                    "predicate": {
                        "predicate_label": canonical_label,
                        "predicate_family": family,
                        "predicate_vocab": "qwen_vl_h001_canonicalized",
                        "qwen_raw_predicate_label": raw_label,
                        "raw_3dssg_predicate_id": None,
                    },
                    "scores": {
                        "predicate_score": score,
                        "predicate_score_type": score_type,
                        "ranking_score": score,
                        "ranking_score_type": "predicate_score",
                        "subject_score": None,
                        "object_score": None,
                        "triplet_score": None,
                    },
                    "ranks": {
                        "predicate_rank_for_pair": rank,
                        "semantic_rank_in_subgraph": None,
                    },
                    "qwen": {
                        "model_id": row.get("model_id"),
                        "model_revision": row.get("model_revision"),
                        "prompt_version": row.get("prompt_version"),
                        "answer_is_visible": pred.get("answer_is_visible"),
                        "rationale_short": pred.get("rationale_short"),
                        "parser_warnings": warnings,
                    },
                }
            )

    by_subgraph: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for prediction in predictions:
        by_subgraph[str(prediction["subgraph_id"])].append(prediction)
    for rows in by_subgraph.values():
        rows.sort(
            key=lambda item: (
                -float(item["scores"]["ranking_score"]),
                int(item["edge"]["subject_id"]),
                int(item["edge"]["object_id"]),
                item["predicate"]["predicate_label"],
            )
        )
        for index, prediction in enumerate(rows, 1):
            prediction["ranks"]["semantic_rank_in_subgraph"] = index

    predictions.sort(
        key=lambda item: (
            str(item["subgraph_id"]),
            int(item["ranks"]["semantic_rank_in_subgraph"]),
            item["prediction_id"],
        )
    )
    predictions_out = out_dir / "predictions.jsonl"
    write_jsonl(predictions_out, predictions)

    gt_label_counts = Counter(row["predicate_label"] for row in scoped_gt)
    gt_family_counts = Counter(row["predicate_family"] for row in scoped_gt)
    covered_gt_family_counts = Counter(row["predicate_family"] for row in covered_gt)
    exported_in_scope = [row for row in predictions if row["predicate"]["predicate_family"] in TARGET_FAMILIES]
    exported_keys = {
        (
            str(row["scan_id"]),
            int(row["subset_split_id"]),
            int(row["edge"]["subject_id"]),
            int(row["edge"]["object_id"]),
            str(row["predicate"]["predicate_label"]),
        )
        for row in exported_in_scope
    }
    gt_keys = {gt_key(row) for row in scoped_gt}

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at": utc_now(),
        "mode": "export_adapter",
        "status": EXPORT_STATUS,
        "inputs": {
            "input_jsonl": relpath(repo_root, input_jsonl),
            "parsed_jsonl": relpath(repo_root, parsed_jsonl),
            "ground_truth_jsonl": relpath(repo_root, gt_jsonl),
        },
        "outputs": {
            "predictions_jsonl": relpath(repo_root, predictions_out),
            "ground_truth_jsonl": relpath(repo_root, gt_out),
            "manifest": relpath(repo_root, out_dir / "manifest.json"),
            "report": relpath(repo_root, out_dir / "report.md"),
        },
        "counts": {
            "input_rows": len(input_rows),
            "parsed_rows": len(parsed_rows),
            "exported_predictions": len(predictions),
            "exported_in_scope_predictions": len(exported_in_scope),
            "ground_truth_rows": len(gt_rows),
            "target_family_gt_rows": len(scoped_gt),
            "target_family_gt_rows_with_qwen_input_pair_family": len(covered_gt),
            "exact_label_gt_keys_hit_by_qwen_predictions": len(gt_keys & exported_keys),
        },
        "parser_status": dict(sorted(parser_counts.items())),
        "raw_predicate_counts": dict(sorted(raw_predicate_counts.items())),
        "canonical_predicate_counts": dict(sorted(canonical_counts.items())),
        "exported_predicate_family_counts": dict(sorted(family_counts.items())),
        "target_gt_family_counts": dict(sorted(gt_family_counts.items())),
        "covered_target_gt_family_counts": dict(sorted(covered_gt_family_counts.items())),
        "skipped_counts": dict(sorted(skipped_counts.items())),
        "warnings": export_warnings[:100],
        "canonicalization_policy": {
            "next to": "close by",
            "near": "close by",
            "above": "higher than",
            "under": "lower than",
            "far from": "unsupported_first_pass because the current H001 verifier does not model far relation semantics",
            "part of": "unsupported_first_pass for current H001 metric scope",
        },
        "paper_metric": False,
        "next_gate": "qwen_vl_geometry_join",
    }
    write_json(out_dir / "manifest.json", manifest)
    (out_dir / "report.md").write_text(render_export_report(manifest), encoding="utf-8")
    print(json.dumps({"status": EXPORT_STATUS, "predictions": len(predictions)}, sort_keys=True))
    return 0


def render_aggregate_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Qwen-VL Full-Source Aggregate Report",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in manifest["counts"].items():
        lines.append(f"- {key}: `{value}`")
    if manifest["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{item}`" for item in manifest["blockers"][:100])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This aggregation only verifies completed Qwen runtime files and prepares raw responses for contract validation. It is not paper metric evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def render_export_report(manifest: dict[str, Any]) -> str:
    lines = [
        "# Qwen-VL H001 Adapter Export Report",
        "",
        f"Status: `{manifest['status']}`",
        f"Created at: `{manifest['created_at']}`",
        "",
        "## Counts",
        "",
    ]
    for key, value in manifest["counts"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Parser Status",
            "",
        ]
    )
    for key, value in manifest["parser_status"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Canonicalization Boundary",
            "",
            "The adapter maps Qwen visual-language synonyms into the existing H001 predicate vocabulary only where the current verifier semantics are aligned: `next to`/`near` -> `close by`, `above` -> `higher than`, and `under` -> `lower than`. `far from` and `part of` are exported as unsupported for the current H001 metric scope.",
            "",
            "This export is still not paper evidence until geometry join, metric/control evaluation, bootstrap CI, and failure/audit artifacts are generated.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    if args.mode == "aggregate":
        return aggregate(args)
    if args.mode == "export_adapter":
        return export_adapter(args)
    raise ValueError(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
