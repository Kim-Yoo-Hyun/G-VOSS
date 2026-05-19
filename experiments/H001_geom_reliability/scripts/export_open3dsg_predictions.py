#!/usr/bin/env python3
"""Export Open3DSG raw relation dumps to the H001 prediction JSONL contract."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PREDICTION_SCHEMA_VERSION = "h001_prediction_v1"
MANIFEST_SCHEMA_VERSION = "h001_open3dsg_prediction_adapter_manifest_v1"
RAW_SCHEMA_VERSION = "h001_open3dsg_raw_dump_v1"
BASELINE_NAME = "open3dsg_ov"
ADAPTER_NAME = "open3dsg_to_h001_predictions"
ADAPTER_VERSION = "v1"
TASK_MODE = "predcls_relation_gt_objects"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--raw-dump-jsonl", type=Path)
    parser.add_argument(
        "--subset-json",
        type=Path,
        default=Path("local_dataset/3DSSG_subset/relationships_validation.json"),
    )
    parser.add_argument(
        "--relationships-file",
        type=Path,
        default=Path("local_dataset/3DSSG_subset/relationships.txt"),
    )
    parser.add_argument(
        "--selected-scans",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/subset/"
            "h001_validation_hardened/scans.txt"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("experiments/H001_geom_reliability/sources/open3dsg/adapter"),
    )
    parser.add_argument("--split-name", default="h001_validation_hardened")
    parser.add_argument("--baseline-run-id", default="open3dsg_repro_pending")
    parser.add_argument("--contract-only", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
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


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSONL at {path}:{line_no}") from exc
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True))
            handle.write("\n")


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_selected_scans(path: Path | None) -> set[str] | None:
    if path is None or not path.exists():
        return None
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


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


def finite_score(value: Any) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(score):
        return None
    return score


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


def convert_rows(
    raw_rows: list[dict[str, Any]],
    contexts: dict[str, dict[str, Any]],
    relationship_ids: dict[str, int],
    split_name: str,
    baseline_run_id: str,
) -> tuple[list[dict[str, Any]], list[str], list[str], dict[str, int]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []
    stats: Counter[str] = Counter()
    for raw_index, raw in enumerate(raw_rows):
        if raw.get("schema_version") != RAW_SCHEMA_VERSION:
            errors.append(f"bad_raw_schema:{raw_index}:{raw.get('schema_version')}")
            continue
        if raw.get("record_type") != "open3dsg_raw_prediction":
            errors.append(f"bad_raw_record_type:{raw_index}:{raw.get('record_type')}")
            continue
        subgraph_id = str(raw.get("subgraph_id") or f"{raw.get('scan_id')}_{raw.get('subset_split_id')}")
        context = contexts.get(subgraph_id)
        if context is None:
            errors.append(f"raw_subgraph_not_in_h001_scope:{subgraph_id}")
            continue
        edge = edge_payload(raw)
        try:
            subject_id = int(edge["subject_id"])
            object_id = int(edge["object_id"])
        except (TypeError, ValueError):
            errors.append(f"bad_edge_instance_ids:{subgraph_id}:{raw_index}")
            continue
        if subject_id == object_id:
            warnings.append(f"same_endpoint_skipped:{subgraph_id}:{subject_id}")
            stats["same_endpoint_skipped"] += 1
            continue
        objects = context["objects"]
        if subject_id not in objects or object_id not in objects:
            warnings.append(f"raw_edge_outside_h001_context_filtered:{subgraph_id}:{subject_id}:{object_id}")
            stats["raw_rows_filtered_outside_h001_context"] += 1
            continue
        for entry in score_entries(raw):
            predicate_label = str(entry.get("predicate_label"))
            score = finite_score(entry.get("score"))
            if score is None:
                errors.append(f"bad_score:{subgraph_id}:{subject_id}:{object_id}:{predicate_label}")
                continue
            raw_predicate_id = entry.get("raw_3dssg_predicate_id") or relationship_ids.get(predicate_label)
            pid = make_prediction_id(split_name, subgraph_id, subject_id, object_id, predicate_label)
            rows.append(
                {
                    "schema_version": PREDICTION_SCHEMA_VERSION,
                    "record_type": "prediction",
                    "prediction_id": pid,
                    "baseline_name": BASELINE_NAME,
                    "baseline_run_id": raw.get("baseline_run_id") or baseline_run_id,
                    "split_name": split_name,
                    "subset_source": "local_dataset/3DSSG_subset/relationships_validation.json",
                    "scan_id": context["scan_id"],
                    "subset_split_id": context["subset_split_id"],
                    "subgraph_id": subgraph_id,
                    "task_mode": TASK_MODE,
                    "edge": {
                        "edge_index": raw.get("edge_index", raw_index),
                        "edge_source": "open3dsg_raw_dump",
                        "subject_id": subject_id,
                        "object_id": object_id,
                        "subject_node_index": edge["subject_node_index"],
                        "object_node_index": edge["object_node_index"],
                        "subject_label": edge["subject_label"] or objects.get(subject_id),
                        "object_label": edge["object_label"] or objects.get(object_id),
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
            )
    assign_ranks(rows)
    errors.extend(validate_rows(rows))
    return rows, warnings, errors, dict(stats)


def assign_ranks(rows: list[dict[str, Any]]) -> None:
    by_pair: dict[tuple[str, int, int], list[dict[str, Any]]] = defaultdict(list)
    by_subgraph: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_pair[(row["subgraph_id"], row["edge"]["subject_id"], row["edge"]["object_id"])].append(row)
        by_subgraph[row["subgraph_id"]].append(row)
    for group in by_pair.values():
        group.sort(key=lambda row: (-float(row["scores"]["ranking_score"]), row["predicate"]["predicate_label"]))
        for rank, row in enumerate(group, 1):
            row["ranks"]["predicate_rank_for_pair"] = rank
    for group in by_subgraph.values():
        group.sort(
            key=lambda row: (
                -float(row["scores"]["ranking_score"]),
                int(row["edge"]["subject_id"]),
                int(row["edge"]["object_id"]),
                row["predicate"]["predicate_label"],
            )
        )
        for rank, row in enumerate(group, 1):
            row["ranks"]["semantic_rank_in_subgraph"] = rank


def validate_rows(rows: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    duplicate_ids = [pid for pid, count in Counter(row["prediction_id"] for row in rows).items() if count > 1]
    if duplicate_ids:
        errors.append(f"duplicate_prediction_ids:{duplicate_ids[:10]}")
    for row in rows:
        if row["scores"]["ranking_score"] is None:
            errors.append(f"missing_ranking_score:{row['prediction_id']}")
        if row["ranks"]["semantic_rank_in_subgraph"] is None:
            errors.append(f"missing_semantic_rank:{row['prediction_id']}")
    return errors


def raw_schema_example() -> dict[str, Any]:
    return {
        "schema_version": RAW_SCHEMA_VERSION,
        "record_type": "open3dsg_raw_prediction",
        "baseline_run_id": "open3dsg_repro_<checkpoint_id>",
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
                "raw_3dssg_predicate_id": 3,
                "open3dsg_predicate_index": 2,
            }
        ],
    }


def make_smoke_raw_rows(
    contexts: dict[str, dict[str, Any]],
    relationship_ids: dict[str, int],
    baseline_run_id: str,
) -> list[dict[str, Any]]:
    if not contexts:
        return []
    context = contexts[sorted(contexts)[0]]
    object_ids = sorted(context["objects"])
    if len(object_ids) < 2:
        return []
    subject_id, object_id = object_ids[:2]
    predicate_labels = [label for label in ("standing on", "close by") if label in relationship_ids]
    if not predicate_labels:
        predicate_labels = sorted(relationship_ids)[:2]
    return [
        {
            "schema_version": RAW_SCHEMA_VERSION,
            "record_type": "open3dsg_raw_prediction",
            "baseline_run_id": baseline_run_id,
            "scan_id": context["scan_id"],
            "subset_split_id": context["subset_split_id"],
            "subgraph_id": context["subgraph_id"],
            "edge_index": 0,
            "edge": {
                "subject_id": subject_id,
                "object_id": object_id,
                "subject_node_index": 0,
                "object_node_index": 1,
                "subject_label": context["objects"][subject_id],
                "object_label": context["objects"][object_id],
            },
            "predicate_scores": [
                {
                    "predicate_label": label,
                    "score": 1.0 - (index * 0.1),
                    "score_type": "adapter_smoke_score",
                    "raw_3dssg_predicate_id": relationship_ids.get(label),
                    "open3dsg_predicate_index": relationship_ids.get(label),
                    "predicate_vocab": "3DSSG_subset_smoke",
                }
                for index, label in enumerate(predicate_labels)
            ],
        }
    ]


def make_report(manifest: dict[str, Any]) -> str:
    filtered_outside_context = manifest["counts"].get("raw_rows_filtered_outside_h001_context", 0)
    lines = [
        "# Open3DSG Prediction Adapter",
        "",
        f"Created at: `{manifest['created_at']}`",
        f"Status: `{manifest['status']}`",
        f"Raw dump: `{manifest['inputs']['raw_dump_jsonl']}`",
        f"Smoke test: `{manifest['inputs']['smoke_test']}`",
        "",
        "## Outputs",
        "",
        f"- predictions: `{manifest['outputs'].get('predictions_jsonl')}`",
        f"- raw smoke: `{manifest['outputs'].get('raw_smoke_jsonl')}`",
        f"- raw schema example: `{manifest['outputs']['raw_schema_example']}`",
        f"- manifest: `manifest.json`",
        "",
        "## Counts",
        "",
        f"- contexts: `{manifest['counts']['contexts']}`",
        f"- raw rows: `{manifest['counts']['raw_rows']}`",
        f"- raw rows filtered outside H001 context: `{filtered_outside_context}`",
        f"- prediction rows: `{manifest['counts']['prediction_rows']}`",
        f"- errors: `{len(manifest['validation']['errors'])}`",
        f"- warnings: `{len(manifest['validation']['warnings'])}`",
        "",
        "## Claim Boundary",
        "",
        "This artifact fixes the Open3DSG-to-H001 prediction contract only. Raw rows outside the fixed H001 object context are filtered and counted before metric execution. It is not second-source metric evidence until predictions are joined with geometry and evaluated.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    raw_path = resolve(repo_root, args.raw_dump_jsonl)
    subset_path = resolve(repo_root, args.subset_json)
    relationships_path = resolve(repo_root, args.relationships_file)
    selected_scans_path = resolve(repo_root, args.selected_scans)
    output_dir = resolve(repo_root, args.output_dir)
    assert output_dir is not None
    output_dir.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    warnings: list[str] = []
    contexts: dict[str, dict[str, Any]] = {}
    relationship_ids: dict[str, int] = {}
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    conversion_stats: dict[str, int] = {}

    if subset_path is None or not subset_path.exists():
        errors.append(f"missing_subset_json:{relpath(repo_root, subset_path)}")
    else:
        selected_scans = load_selected_scans(selected_scans_path)
        contexts = build_contexts(load_json(subset_path), selected_scans)

    if relationships_path is None or not relationships_path.exists():
        errors.append(f"missing_relationships_file:{relpath(repo_root, relationships_path)}")
    else:
        relationship_ids = {label: index for index, label in enumerate(read_lines(relationships_path))}

    raw_missing = raw_path is None or not raw_path.exists()
    if args.smoke_test and not args.contract_only:
        raw_rows = make_smoke_raw_rows(contexts, relationship_ids, args.baseline_run_id)
        if raw_rows:
            raw_path = output_dir / "raw_smoke.jsonl"
            write_jsonl(raw_path, raw_rows)
            raw_missing = False
        else:
            errors.append("smoke_raw_generation_failed:no_context_with_two_objects")
    if args.contract_only or raw_missing:
        status = "adapter_contract_ready_raw_dump_missing" if not errors else "blocked_contract_input_missing"
    else:
        if not raw_rows:
            raw_rows = load_jsonl(raw_path)
        rows, warnings, conversion_errors, conversion_stats = convert_rows(
            raw_rows, contexts, relationship_ids, args.split_name, args.baseline_run_id
        )
        errors.extend(conversion_errors)
        write_jsonl(output_dir / "predictions.jsonl", rows)
        status = "ready" if not errors else "blocked_conversion_errors"

    write_json(output_dir / "raw_schema_example.json", raw_schema_example())
    next_action = (
        "Run Open3DSG metric/join with the adapter predictions, GT denominator, and geometry decisions."
        if status == "ready"
        else "Run Open3DSG identity-preserving raw dump, then rerun this adapter without --contract-only."
    )
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "baseline_name": BASELINE_NAME,
        "adapter": {"name": ADAPTER_NAME, "version": ADAPTER_VERSION},
        "inputs": {
            "raw_dump_jsonl": relpath(repo_root, raw_path),
            "smoke_test": bool(args.smoke_test),
            "subset_json": relpath(repo_root, subset_path),
            "relationships_file": relpath(repo_root, relationships_path),
            "selected_scans": relpath(repo_root, selected_scans_path),
        },
        "outputs": {
            "predictions_jsonl": relpath(repo_root, output_dir / "predictions.jsonl") if rows else None,
            "raw_schema_example": relpath(repo_root, output_dir / "raw_schema_example.json"),
            "raw_smoke_jsonl": relpath(repo_root, output_dir / "raw_smoke.jsonl")
            if args.smoke_test and raw_rows
            else None,
        },
        "counts": {
            "contexts": len(contexts),
            "raw_rows": len(raw_rows),
            "prediction_rows": len(rows),
            "raw_rows_filtered_outside_h001_context": conversion_stats.get(
                "raw_rows_filtered_outside_h001_context", 0
            ),
            "same_endpoint_skipped": conversion_stats.get("same_endpoint_skipped", 0),
        },
        "validation": {"errors": errors, "warnings": warnings},
        "next_action": next_action,
    }
    write_json(output_dir / "manifest.json", manifest)
    (output_dir / "report.md").write_text(make_report(manifest), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(repo_root, output_dir)}, sort_keys=True))
    return 0 if status in {"ready", "adapter_contract_ready_raw_dump_missing"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
