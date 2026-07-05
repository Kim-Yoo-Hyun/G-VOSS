#!/usr/bin/env python3
"""Stream Open3DSG full-train raw dumps into the H001 prediction contract."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PREDICTION_SCHEMA_VERSION = "h001_prediction_v1"
MANIFEST_SCHEMA_VERSION = "h002_full_train_adapter_export_v1"
RAW_SCHEMA_VERSION = "h001_open3dsg_raw_dump_v1"
BASELINE_NAME = "open3dsg_ov"
ADAPTER_NAME = "open3dsg_to_h001_predictions_streaming"
ADAPTER_VERSION = "v1"
TASK_MODE = "predcls_relation_gt_objects"


DEFAULT_ROOT = Path("hypothesis/CAND-001/H002_factorized-relation-confidence")
DEFAULT_SCOPE = DEFAULT_ROOT / "artifacts/train_rga_full/open3dsg_train_full"


class IssueCollector:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.counts: Counter[str] = Counter()
        self.samples: list[str] = []

    def add(self, key: str, message: str) -> None:
        self.counts[key] += 1
        if len(self.samples) < self.limit:
            self.samples.append(message)

    @property
    def total(self) -> int:
        return sum(self.counts.values())

    def payload(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "counts": dict(sorted(self.counts.items())),
            "sample_limit": self.limit,
            "samples": self.samples,
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--raw-dump-jsonl",
        type=Path,
        default=DEFAULT_SCOPE / "raw_dump/raw.dedup.jsonl",
    )
    parser.add_argument(
        "--subset-json",
        type=Path,
        default=DEFAULT_SCOPE / "source_contract/relationships_train_full.json",
    )
    parser.add_argument(
        "--relationships-file",
        type=Path,
        default=Path("local_dataset/3DSSG_subset/relationships.txt"),
    )
    parser.add_argument(
        "--selected-scans",
        type=Path,
        default=DEFAULT_SCOPE / "source_contract/selected_scans.txt",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_SCOPE / "adapter",
    )
    parser.add_argument("--split-name", default="h002_train_open3dsg_full")
    parser.add_argument("--baseline-run-id", default="open3dsg_train_full_epoch13_step13104")
    parser.add_argument("--issue-sample-limit", type=int, default=100)
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
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_selected_scans(path: Path | None) -> set[str] | None:
    if path is None or not path.exists():
        return None
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def build_contexts(subset: dict[str, Any], selected_scans: set[str] | None) -> dict[str, dict[str, Any]]:
    contexts: dict[str, dict[str, Any]] = {}
    for entry in subset.get("scans", []):
        scan_id = str(entry["scan"])
        if selected_scans is not None and scan_id not in selected_scans:
            continue
        split_id = int(entry["split"])
        subgraph_id = f"{scan_id}_{split_id}"
        contexts[subgraph_id] = {
            "scan_id": scan_id,
            "subset_split_id": split_id,
            "subgraph_id": subgraph_id,
            "objects": {int(key): str(value) for key, value in entry.get("objects", {}).items()},
        }
    return contexts


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


def finite_score(value: Any) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(score):
        return None
    return score


def parse_split_value(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        pass
    if len(text) == 1 and text.lower() in "abcdef":
        return int(text, 16)
    return None


def normalize_raw_identity(raw: dict[str, Any]) -> tuple[str, int, str] | None:
    raw_scan = raw.get("scan_id")
    raw_split = parse_split_value(raw.get("subset_split_id"))
    if raw_scan is None:
        return None
    scan_id = str(raw_scan)
    if raw_split is None:
        base, sep, suffix = scan_id.rpartition("-")
        parsed_suffix = parse_split_value(suffix) if sep else None
        if parsed_suffix is not None and base:
            scan_id = base
            raw_split = parsed_suffix
    if raw_split is None:
        return None
    return scan_id, raw_split, f"{scan_id}_{raw_split}"


def score_entries(raw: dict[str, Any]) -> list[dict[str, Any]]:
    entries = raw.get("predicate_scores")
    if isinstance(entries, dict):
        return [
            {"predicate_label": str(label), "score": score}
            for label, score in entries.items()
            if str(label) != "none"
        ]
    if isinstance(entries, list):
        return [entry for entry in entries if str(entry.get("predicate_label")) != "none"]
    return []


def edge_payload(raw: dict[str, Any]) -> dict[str, Any]:
    edge = raw.get("edge") if isinstance(raw.get("edge"), dict) else {}
    return {
        "subject_id": edge.get("subject_id", raw.get("subject_id")),
        "object_id": edge.get("object_id", raw.get("object_id")),
        "subject_node_index": edge.get("subject_node_index", raw.get("subject_node_index")),
        "object_node_index": edge.get("object_node_index", raw.get("object_node_index")),
        "subject_label": edge.get("subject_label", raw.get("subject_label")),
        "object_label": edge.get("object_label", raw.get("object_label")),
    }


def make_prediction_id(
    split_name: str,
    subgraph_id: str,
    subject_id: int,
    object_id: int,
    predicate_label: str,
) -> str:
    return f"{BASELINE_NAME}:{split_name}:{subgraph_id}:{subject_id}:{object_id}:{predicate_label}"


def make_prediction(
    raw: dict[str, Any],
    entry: dict[str, Any],
    context: dict[str, Any],
    relationship_ids: dict[str, int],
    split_name: str,
    baseline_run_id: str,
    subset_source: str,
    raw_index: int,
    score: float,
) -> dict[str, Any]:
    edge = edge_payload(raw)
    subject_id = int(edge["subject_id"])
    object_id = int(edge["object_id"])
    predicate_label = str(entry.get("predicate_label"))
    raw_predicate_id = entry.get("raw_3dssg_predicate_id") or relationship_ids.get(predicate_label)
    return {
        "schema_version": PREDICTION_SCHEMA_VERSION,
        "record_type": "prediction",
        "prediction_id": make_prediction_id(split_name, context["subgraph_id"], subject_id, object_id, predicate_label),
        "baseline_name": BASELINE_NAME,
        "baseline_run_id": raw.get("baseline_run_id") or baseline_run_id,
        "split_name": split_name,
        "subset_source": subset_source,
        "scan_id": context["scan_id"],
        "subset_split_id": context["subset_split_id"],
        "subgraph_id": context["subgraph_id"],
        "task_mode": TASK_MODE,
        "edge": {
            "edge_index": raw.get("edge_index", raw_index),
            "edge_source": "open3dsg_raw_dump",
            "subject_id": subject_id,
            "object_id": object_id,
            "subject_node_index": edge["subject_node_index"],
            "object_node_index": edge["object_node_index"],
            "subject_label": edge["subject_label"] or context["objects"].get(subject_id),
            "object_label": edge["object_label"] or context["objects"].get(object_id),
            "subject_label_source": "Open3DSG_raw_or_3DSSG_subset",
            "object_label_source": "Open3DSG_raw_or_3DSSG_subset",
        },
        "predicate": {
            "predicate_label": predicate_label,
            "predicate_family": predicate_family(predicate_label),
            "raw_3dssg_predicate_id": raw_predicate_id,
            "open3dsg_predicate_index": entry.get("open3dsg_predicate_index"),
            "predicate_vocab": entry.get("predicate_vocab", "Open3DSG_or_3DSSG_subset"),
        },
        "scores": {
            "predicate_score": score,
            "predicate_score_type": entry.get("score_type", "open3dsg_relation_score"),
            "subject_score": raw.get("subject_score"),
            "object_score": raw.get("object_score"),
            "triplet_score": entry.get("triplet_score"),
            "ranking_score": score,
            "ranking_score_type": "predicate_score",
        },
        "ranks": {"predicate_rank_for_pair": None, "semantic_rank_in_subgraph": None},
        "adapter": {
            "name": ADAPTER_NAME,
            "version": ADAPTER_VERSION,
            "raw_schema_version": RAW_SCHEMA_VERSION,
        },
    }


def assign_ranks(rows: list[dict[str, Any]]) -> None:
    by_pair: dict[tuple[str, int, int], list[dict[str, Any]]] = {}
    for row in rows:
        key = (row["subgraph_id"], row["edge"]["subject_id"], row["edge"]["object_id"])
        by_pair.setdefault(key, []).append(row)
    for group in by_pair.values():
        group.sort(key=lambda row: (-float(row["scores"]["ranking_score"]), row["predicate"]["predicate_label"]))
        for rank, row in enumerate(group, 1):
            row["ranks"]["predicate_rank_for_pair"] = rank
    rows.sort(
        key=lambda row: (
            -float(row["scores"]["ranking_score"]),
            int(row["edge"]["subject_id"]),
            int(row["edge"]["object_id"]),
            row["predicate"]["predicate_label"],
        )
    )
    for rank, row in enumerate(rows, 1):
        row["ranks"]["semantic_rank_in_subgraph"] = rank


def convert_subgraph(
    raw_group: list[dict[str, Any]],
    contexts: dict[str, dict[str, Any]],
    relationship_ids: dict[str, int],
    split_name: str,
    baseline_run_id: str,
    subset_source: str,
    raw_start_index: int,
    errors: IssueCollector,
    warnings: IssueCollector,
    stats: Counter[str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for offset, raw in enumerate(raw_group):
        raw_index = raw_start_index + offset
        stats["raw_rows"] += 1
        if raw.get("schema_version") != RAW_SCHEMA_VERSION:
            errors.add("bad_raw_schema", f"bad_raw_schema:{raw_index}:{raw.get('schema_version')}")
            continue
        if raw.get("record_type") != "open3dsg_raw_prediction":
            errors.add("bad_raw_record_type", f"bad_raw_record_type:{raw_index}:{raw.get('record_type')}")
            continue
        normalized_identity = normalize_raw_identity(raw)
        if normalized_identity is None:
            errors.add("bad_raw_identity", f"bad_raw_identity:{raw_index}:{raw.get('scan_id')}:{raw.get('subset_split_id')}")
            continue
        _scan_id, _subset_split_id, subgraph_id = normalized_identity
        context = contexts.get(subgraph_id)
        if context is None:
            errors.add("raw_subgraph_not_in_scope", f"raw_subgraph_not_in_scope:{subgraph_id}")
            continue
        edge = edge_payload(raw)
        try:
            subject_id = int(edge["subject_id"])
            object_id = int(edge["object_id"])
        except (TypeError, ValueError):
            errors.add("bad_edge_instance_ids", f"bad_edge_instance_ids:{subgraph_id}:{raw_index}")
            continue
        if subject_id == object_id:
            warnings.add("same_endpoint_skipped", f"same_endpoint_skipped:{subgraph_id}:{subject_id}")
            stats["same_endpoint_skipped"] += 1
            continue
        objects = context["objects"]
        if subject_id not in objects or object_id not in objects:
            warnings.add("raw_edge_outside_context_filtered", f"raw_edge_outside_context_filtered:{subgraph_id}:{subject_id}:{object_id}")
            stats["raw_rows_filtered_outside_context"] += 1
            continue
        for entry in score_entries(raw):
            predicate_label = str(entry.get("predicate_label"))
            score = finite_score(entry.get("score"))
            if score is None:
                errors.add("bad_score", f"bad_score:{subgraph_id}:{subject_id}:{object_id}:{predicate_label}")
                continue
            row = make_prediction(
                raw,
                entry,
                context,
                relationship_ids,
                split_name,
                baseline_run_id,
                subset_source,
                raw_index,
                score,
            )
            rows.append(row)
            stats[f"family:{row['predicate']['predicate_family']}"] += 1

    duplicate_ids = [pid for pid, count in Counter(row["prediction_id"] for row in rows).items() if count > 1]
    for pid in duplicate_ids[:20]:
        errors.add("duplicate_prediction_id", f"duplicate_prediction_id:{pid}")
    assign_ranks(rows)
    stats["prediction_rows"] += len(rows)
    return rows


def raw_schema_example() -> dict[str, Any]:
    return {
        "schema_version": RAW_SCHEMA_VERSION,
        "record_type": "open3dsg_raw_prediction",
        "baseline_run_id": "open3dsg_train_full_epoch13_step13104",
        "scan_id": "<3RScan scan id>",
        "subset_split_id": 1,
        "subgraph_id": "<scan_id>_<subset_split_id>",
        "edge_index": 0,
        "edge": {
            "subject_id": 1,
            "object_id": 2,
            "subject_node_index": 0,
            "object_node_index": 1,
            "subject_label": "floor",
            "object_label": "wall",
        },
        "predicate_scores": [
            {
                "predicate_label": "standing on",
                "score": 0.72,
                "score_type": "open3dsg_relation_score",
                "raw_3dssg_predicate_id": 15,
                "open3dsg_predicate_index": 15,
            }
        ],
    }


def make_report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    return "\n".join(
        [
            "# H002 Full Train Adapter Export",
            "",
            f"Created at: `{manifest['created_at']}`",
            f"Status: `{manifest['status']}`",
            "",
            "## Inputs",
            "",
            f"- raw dump: `{manifest['inputs']['raw_dump_jsonl']}`",
            f"- subset: `{manifest['inputs']['subset_json']}`",
            f"- selected scans: `{manifest['inputs']['selected_scans']}`",
            "",
            "## Outputs",
            "",
            f"- predictions: `{manifest['outputs']['predictions_jsonl']}`",
            f"- manifest: `{manifest['outputs']['manifest']}`",
            "",
            "## Counts",
            "",
            f"- contexts: `{counts['contexts']}`",
            f"- raw rows: `{counts['raw_rows']}`",
            f"- prediction rows: `{counts['prediction_rows']}`",
            f"- subgraphs written: `{counts['subgraphs_written']}`",
            f"- same endpoint skipped: `{counts['same_endpoint_skipped']}`",
            f"- outside-context rows filtered: `{counts['raw_rows_filtered_outside_context']}`",
            f"- errors: `{manifest['validation']['errors']['total']}`",
            f"- warnings: `{manifest['validation']['warnings']['total']}`",
            "",
            "## Boundary",
            "",
            "This is a train-origin semantic source export for H002 hypothesis-stage RGA construction. It is not validation/test evidence and it is not paper-level evidence until geometry join, target construction, controls, and Docker reproducibility gates are satisfied.",
            "",
        ]
    )


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    raw_path = resolve(repo_root, args.raw_dump_jsonl)
    subset_path = resolve(repo_root, args.subset_json)
    relationships_path = resolve(repo_root, args.relationships_file)
    selected_scans_path = resolve(repo_root, args.selected_scans)
    output_dir = resolve(repo_root, args.output_dir)
    assert raw_path is not None
    assert subset_path is not None
    assert relationships_path is not None
    assert output_dir is not None

    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = output_dir / "predictions.jsonl"
    tmp_predictions_path = output_dir / "predictions.jsonl.tmp"
    manifest_path = output_dir / "manifest.json"
    report_path = output_dir / "report.md"

    errors = IssueCollector(args.issue_sample_limit)
    warnings = IssueCollector(args.issue_sample_limit)
    stats: Counter[str] = Counter()

    selected_scans = load_selected_scans(selected_scans_path)
    contexts = build_contexts(load_json(subset_path), selected_scans)
    relationship_ids = {label: index for index, label in enumerate(read_lines(relationships_path))}
    subset_source = relpath(repo_root, subset_path) or str(subset_path)

    seen_subgraphs: set[str] = set()
    current_subgraph: str | None = None
    current_group: list[dict[str, Any]] = []
    current_group_start = 0

    def flush_group(handle: Any) -> None:
        nonlocal current_group
        if not current_group:
            return
        rows = convert_subgraph(
            current_group,
            contexts,
            relationship_ids,
            args.split_name,
            args.baseline_run_id,
            subset_source,
            current_group_start,
            errors,
            warnings,
            stats,
        )
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")
        if rows:
            stats["subgraphs_written"] += 1
        current_group = []

    raw_line_index = 0
    with raw_path.open("r", encoding="utf-8") as raw_handle, tmp_predictions_path.open("w", encoding="utf-8") as out_handle:
        for line_no, line in enumerate(raw_handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {raw_path}:{line_no}") from exc
            subgraph_id = raw.get("subgraph_id")
            if subgraph_id != current_subgraph:
                flush_group(out_handle)
                if current_subgraph is not None:
                    seen_subgraphs.add(current_subgraph)
                if subgraph_id in seen_subgraphs:
                    errors.add("noncontiguous_subgraph", f"noncontiguous_subgraph:{subgraph_id}:line:{line_no}")
                current_subgraph = str(subgraph_id)
                current_group_start = raw_line_index
            current_group.append(raw)
            raw_line_index += 1
        flush_group(out_handle)
        if current_subgraph is not None:
            seen_subgraphs.add(current_subgraph)

    tmp_predictions_path.replace(predictions_path)

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": utc_now(),
        "status": "ready" if errors.total == 0 else "blocked_conversion_errors",
        "baseline_name": BASELINE_NAME,
        "adapter": {"name": ADAPTER_NAME, "version": ADAPTER_VERSION},
        "inputs": {
            "raw_dump_jsonl": relpath(repo_root, raw_path),
            "subset_json": relpath(repo_root, subset_path),
            "relationships_file": relpath(repo_root, relationships_path),
            "selected_scans": relpath(repo_root, selected_scans_path),
        },
        "outputs": {
            "predictions_jsonl": relpath(repo_root, predictions_path),
            "raw_schema_example": relpath(repo_root, output_dir / "raw_schema_example.json"),
            "manifest": relpath(repo_root, manifest_path),
            "report": relpath(repo_root, report_path),
        },
        "counts": {
            "contexts": len(contexts),
            "relationship_labels": len(relationship_ids),
            "raw_rows": stats["raw_rows"],
            "prediction_rows": stats["prediction_rows"],
            "subgraphs_written": stats["subgraphs_written"],
            "same_endpoint_skipped": stats["same_endpoint_skipped"],
            "raw_rows_filtered_outside_context": stats["raw_rows_filtered_outside_context"],
            "family_prediction_rows": {
                key.replace("family:", ""): value
                for key, value in sorted(stats.items())
                if key.startswith("family:")
            },
        },
        "validation": {"errors": errors.payload(), "warnings": warnings.payload()},
        "claim_boundary": (
            "Train-origin full Open3DSG semantic source export for H002 hypothesis-stage RGA only. "
            "Validation/test rows are not used."
        ),
        "next_action": "Join adapter predictions with train-origin geometry evidence and build full-train RGA rows.",
    }
    write_json(output_dir / "raw_schema_example.json", raw_schema_example())
    write_json(manifest_path, manifest)
    report_path.write_text(make_report(manifest), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "raw_rows": manifest["counts"]["raw_rows"],
                "prediction_rows": manifest["counts"]["prediction_rows"],
                "out": relpath(repo_root, output_dir),
            },
            sort_keys=True,
        )
    )
    return 0 if manifest["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
