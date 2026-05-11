#!/usr/bin/env python3
"""Convert VL-SAT raw relation scores into H001 prediction JSONL."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_SUBSET_JSON = DEFAULT_DATASET_ROOT / "3DSSG_subset" / "relationships_validation.json"
DEFAULT_CLASSES_FILE = DEFAULT_DATASET_ROOT / "3DSSG_subset" / "classes.txt"
DEFAULT_RELATIONSHIPS_FILE = DEFAULT_DATASET_ROOT / "3DSSG_subset" / "relationships.txt"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts" / "subset" / "h001_mini" / "scans.txt"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts" / "evaluation" / "vlsat_closed_set" / "mini"

PREDICTION_SCHEMA_VERSION = "h001_prediction_v1"
GROUND_TRUTH_SCHEMA_VERSION = "h001_ground_truth_v1"
MANIFEST_SCHEMA_VERSION = "h001_prediction_manifest_v1"
ADAPTER_VERSION = "v0"
RAW_SCHEMA_VERSION = "h001_vlsat_raw_dump_v1"
BASELINE_NAME = "vlsat_closed_set"
TASK_MODE = "predcls_relation"
DEFAULT_EXPORT_POLICY = "all_non_none_predicates_per_directed_pair"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export/validate H001 vlsat_closed_set prediction JSONL."
    )
    parser.add_argument("--subset-json", type=Path, default=DEFAULT_SUBSET_JSON)
    parser.add_argument("--classes-file", type=Path, default=DEFAULT_CLASSES_FILE)
    parser.add_argument("--relationships-file", type=Path, default=DEFAULT_RELATIONSHIPS_FILE)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--raw-dump-jsonl", type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--split-name", default="mini")
    parser.add_argument("--baseline-run-id", default="vlsat_eval_pending")
    parser.add_argument(
        "--export-policy",
        choices=[DEFAULT_EXPORT_POLICY, "top_m_per_pair"],
        default=DEFAULT_EXPORT_POLICY,
    )
    parser.add_argument("--top-m-per-pair", type=int, default=3)
    parser.add_argument(
        "--ground-truth-only",
        action="store_true",
        help="Only export/validate ground_truth.jsonl shape. Does not create predictions.",
    )
    parser.add_argument("--fail-on-warnings", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}") from exc
    return records


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_lines(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_selected_scans(path: Path | None) -> set[str] | None:
    if path is None:
        return None
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


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


def subgraph_id(scan_id: str, subset_split_id: int) -> str:
    return f"{scan_id}_{subset_split_id}"


def prediction_id(
    split_name: str,
    scan_id: str,
    subset_split_id: int,
    subject_id: int,
    object_id: int,
    predicate_label: str,
) -> str:
    return (
        f"{BASELINE_NAME}:{split_name}:{scan_id}:{subset_split_id}:"
        f"{subject_id}:{object_id}:{predicate_label}"
    )


def ground_truth_id(
    split_name: str,
    scan_id: str,
    subset_split_id: int,
    subject_id: int,
    object_id: int,
    predicate_label: str,
) -> str:
    return f"gt:{split_name}:{scan_id}:{subset_split_id}:{subject_id}:{object_id}:{predicate_label}"


def build_contexts(
    subset_data: dict[str, Any],
    selected_scans: set[str] | None,
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    contexts: dict[str, dict[str, Any]] = {}
    selected_entries: list[dict[str, Any]] = []
    for entry in subset_data.get("scans", []):
        scan_id = str(entry["scan"])
        if selected_scans is not None and scan_id not in selected_scans:
            continue
        split_id = int(entry["split"])
        sid = subgraph_id(scan_id, split_id)
        objects = {int(k): str(v) for k, v in entry.get("objects", {}).items()}
        contexts[sid] = {
            "scan_id": scan_id,
            "subset_split_id": split_id,
            "subgraph_id": sid,
            "objects": objects,
            "relationships": entry.get("relationships", []),
        }
        selected_entries.append(entry)
    return contexts, selected_entries


def make_ground_truth_rows(
    contexts: dict[str, dict[str, Any]],
    relationship_id_map: dict[str, int],
    split_name: str,
    subset_source: str,
) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    seen: set[str] = set()
    for context in contexts.values():
        objects = context["objects"]
        for relation_index, rel in enumerate(context["relationships"]):
            subject_id = int(rel[0])
            object_id = int(rel[1])
            raw_id = int(rel[2])
            predicate_label = str(rel[3])
            if predicate_label == "none" or raw_id == 0:
                continue
            mapped_raw_id = relationship_id_map.get(predicate_label)
            if mapped_raw_id is None:
                warnings.append(f"gt_unknown_predicate:{context['subgraph_id']}:{predicate_label}")
                continue
            if mapped_raw_id != raw_id:
                warnings.append(
                    f"gt_raw_id_mismatch:{context['subgraph_id']}:{relation_index}:"
                    f"{predicate_label}:{raw_id}!={mapped_raw_id}"
                )
            gid = ground_truth_id(
                split_name,
                context["scan_id"],
                context["subset_split_id"],
                subject_id,
                object_id,
                predicate_label,
            )
            if gid in seen:
                warnings.append(f"duplicate_gt_id_skipped:{gid}")
                continue
            seen.add(gid)
            rows.append(
                {
                    "schema_version": GROUND_TRUTH_SCHEMA_VERSION,
                    "record_type": "ground_truth",
                    "gt_id": gid,
                    "split_name": split_name,
                    "subset_source": subset_source,
                    "scan_id": context["scan_id"],
                    "subset_split_id": context["subset_split_id"],
                    "subgraph_id": context["subgraph_id"],
                    "subject_id": subject_id,
                    "object_id": object_id,
                    "subject_label": objects.get(subject_id),
                    "object_label": objects.get(object_id),
                    "predicate_label": predicate_label,
                    "predicate_family": predicate_family(predicate_label),
                    "raw_3dssg_predicate_id": raw_id,
                    "vlsat_predicate_index": raw_id - 1,
                    "source_relation_index": relation_index,
                }
            )
    return rows, warnings


def score_entries_for_edge(
    relation_names: list[str],
    scores: list[Any],
    export_policy: str,
    top_m_per_pair: int,
) -> list[tuple[int, str, float]]:
    entries: list[tuple[int, str, float]] = []
    if len(scores) != len(relation_names):
        raise ValueError(
            f"score width mismatch: {len(scores)} scores for {len(relation_names)} relation names"
        )
    for idx, (label, score) in enumerate(zip(relation_names, scores)):
        if label == "none":
            continue
        entries.append((idx, label, float(score)))
    entries.sort(key=lambda item: (-item[2], item[1]))
    if export_policy == "top_m_per_pair":
        entries = entries[:top_m_per_pair]
    return entries


def make_prediction_rows(
    raw_records: list[dict[str, Any]],
    contexts: dict[str, dict[str, Any]],
    relationship_id_map: dict[str, int],
    split_name: str,
    subset_source: str,
    baseline_run_id: str,
    export_policy: str,
    top_m_per_pair: int,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    errors: list[str] = []

    for raw in raw_records:
        if raw.get("schema_version") != RAW_SCHEMA_VERSION:
            errors.append(f"bad_raw_schema:{raw.get('subgraph_id')}:{raw.get('schema_version')}")
            continue
        if raw.get("record_type") != "vlsat_raw_subgraph_scores":
            errors.append(f"bad_raw_record_type:{raw.get('record_type')}")
            continue
        sid = str(raw["subgraph_id"])
        context = contexts.get(sid)
        if context is None:
            errors.append(f"raw_subgraph_not_in_selected_subset:{sid}")
            continue
        relation_names = [str(label) for label in raw.get("relation_names", [])]
        if not relation_names:
            errors.append(f"raw_missing_relation_names:{sid}")
            continue
        if "none" in relation_names:
            errors.append(f"raw_relation_names_include_none:{sid}")
            continue
        node_instance_ids = [int(x) for x in raw.get("node_instance_ids", [])]
        edge_indices = raw.get("edge_indices", [])
        rel_scores = raw.get("rel_scores_3d", [])
        if len(edge_indices) != len(rel_scores):
            errors.append(f"raw_edge_score_count_mismatch:{sid}")
            continue
        objects = context["objects"]
        for edge_index, (edge, score_row) in enumerate(zip(edge_indices, rel_scores)):
            if len(edge) != 2:
                errors.append(f"bad_edge_index_shape:{sid}:{edge_index}")
                continue
            subject_node_index = int(edge[0])
            object_node_index = int(edge[1])
            try:
                subject_id = node_instance_ids[subject_node_index]
                object_id = node_instance_ids[object_node_index]
            except IndexError:
                errors.append(f"edge_node_index_out_of_range:{sid}:{edge_index}")
                continue
            if subject_id == object_id:
                warnings.append(f"same_endpoint_prediction_skipped:{sid}:{subject_id}")
                continue
            if subject_id not in objects or object_id not in objects:
                errors.append(f"prediction_object_not_in_subgraph:{sid}:{edge_index}")
                continue

            try:
                score_entries = score_entries_for_edge(
                    relation_names, score_row, export_policy, top_m_per_pair
                )
            except ValueError as exc:
                errors.append(f"{sid}:{edge_index}:{exc}")
                continue

            for vlsat_idx, predicate_label, score in score_entries:
                raw_id = relationship_id_map.get(predicate_label)
                if raw_id is None:
                    errors.append(f"prediction_unknown_predicate:{sid}:{predicate_label}")
                    continue
                expected_vlsat_idx = raw_id - 1
                if expected_vlsat_idx != vlsat_idx:
                    errors.append(
                        f"prediction_vlsat_index_mismatch:{sid}:{predicate_label}:"
                        f"{vlsat_idx}!={expected_vlsat_idx}"
                    )
                    continue
                pid = prediction_id(
                    split_name,
                    context["scan_id"],
                    context["subset_split_id"],
                    subject_id,
                    object_id,
                    predicate_label,
                )
                rows.append(
                    {
                        "schema_version": PREDICTION_SCHEMA_VERSION,
                        "record_type": "prediction",
                        "prediction_id": pid,
                        "baseline_name": BASELINE_NAME,
                        "baseline_run_id": raw.get("baseline_run_id") or baseline_run_id,
                        "split_name": split_name,
                        "subset_source": subset_source,
                        "scan_id": context["scan_id"],
                        "subset_split_id": context["subset_split_id"],
                        "subgraph_id": sid,
                        "task_mode": TASK_MODE,
                        "edge": {
                            "edge_index": edge_index,
                            "edge_source": "vlsat_edge_indices",
                            "subject_id": subject_id,
                            "object_id": object_id,
                            "subject_node_index": subject_node_index,
                            "object_node_index": object_node_index,
                            "subject_label": objects.get(subject_id),
                            "object_label": objects.get(object_id),
                            "subject_label_source": "3DSSG_subset",
                            "object_label_source": "3DSSG_subset",
                        },
                        "predicate": {
                            "predicate_label": predicate_label,
                            "predicate_family": predicate_family(predicate_label),
                            "raw_3dssg_predicate_id": raw_id,
                            "vlsat_predicate_index": expected_vlsat_idx,
                            "predicate_vocab": "3DSSG_subset_26_no_none",
                        },
                        "scores": {
                            "predicate_score": score,
                            "predicate_score_type": "sigmoid_probability",
                            "subject_score": None,
                            "object_score": None,
                            "triplet_score": None,
                            "ranking_score": score,
                            "ranking_score_type": "predicate_score",
                        },
                        "ranks": {
                            "predicate_rank_for_pair": None,
                            "semantic_rank_in_subgraph": None,
                        },
                        "adapter": {
                            "name": "vlsat_to_h001_predictions",
                            "version": ADAPTER_VERSION,
                            "export_policy": export_policy,
                        },
                    }
                )

    assign_ranks(rows)
    return rows, warnings, errors


def assign_ranks(rows: list[dict[str, Any]]) -> None:
    by_pair: dict[tuple[str, int, int], list[dict[str, Any]]] = defaultdict(list)
    by_subgraph: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_pair[
            (
                row["subgraph_id"],
                int(row["edge"]["subject_id"]),
                int(row["edge"]["object_id"]),
            )
        ].append(row)
        by_subgraph[row["subgraph_id"]].append(row)

    for group in by_pair.values():
        group.sort(
            key=lambda row: (
                -float(row["scores"]["ranking_score"]),
                row["predicate"]["predicate_label"],
            )
        )
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


def validate_predictions(
    rows: list[dict[str, Any]],
    contexts: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    ids = Counter(row["prediction_id"] for row in rows)
    duplicates = sorted(key for key, count in ids.items() if count > 1)
    if duplicates:
        errors.append(f"duplicate_prediction_ids:{duplicates[:10]}")

    ranks_by_subgraph: dict[str, set[int]] = defaultdict(set)
    for row in rows:
        pid = row["prediction_id"]
        if row["schema_version"] != PREDICTION_SCHEMA_VERSION:
            errors.append(f"bad_prediction_schema:{pid}")
        if row["baseline_name"] != BASELINE_NAME:
            errors.append(f"bad_baseline_name:{pid}")
        label = row["predicate"]["predicate_label"]
        if label == "none":
            errors.append(f"none_prediction_emitted:{pid}")
        score = row["scores"]["predicate_score"]
        if not isinstance(score, (int, float)) or not (0.0 <= float(score) <= 1.0):
            errors.append(f"bad_predicate_score:{pid}:{score}")
        if row["scores"]["ranking_score"] is None:
            errors.append(f"missing_ranking_score:{pid}")
        raw_id = row["predicate"]["raw_3dssg_predicate_id"]
        vlsat_idx = row["predicate"]["vlsat_predicate_index"]
        if vlsat_idx != raw_id - 1:
            errors.append(f"bad_vlsat_index:{pid}")
        context = contexts.get(row["subgraph_id"])
        if context is None:
            errors.append(f"prediction_missing_context:{pid}")
            continue
        subject_id = int(row["edge"]["subject_id"])
        object_id = int(row["edge"]["object_id"])
        if subject_id == object_id:
            errors.append(f"same_endpoint_prediction:{pid}")
        if subject_id not in context["objects"]:
            errors.append(f"subject_missing_from_subgraph:{pid}")
        if object_id not in context["objects"]:
            errors.append(f"object_missing_from_subgraph:{pid}")
        if not row["predicate"]["predicate_family"]:
            errors.append(f"missing_predicate_family:{pid}")
        rank = row["ranks"]["semantic_rank_in_subgraph"]
        if not isinstance(rank, int) or rank <= 0:
            errors.append(f"bad_semantic_rank:{pid}:{rank}")
        elif rank in ranks_by_subgraph[row["subgraph_id"]]:
            errors.append(f"duplicate_semantic_rank:{row['subgraph_id']}:{rank}")
        else:
            ranks_by_subgraph[row["subgraph_id"]].add(rank)

    if not rows:
        warnings.append("zero_prediction_rows")
    return errors, warnings


def validate_ground_truth(
    rows: list[dict[str, Any]],
    contexts: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    ids = Counter(row["gt_id"] for row in rows)
    duplicates = sorted(key for key, count in ids.items() if count > 1)
    if duplicates:
        errors.append(f"duplicate_gt_ids:{duplicates[:10]}")
    for row in rows:
        gid = row["gt_id"]
        if row["schema_version"] != GROUND_TRUTH_SCHEMA_VERSION:
            errors.append(f"bad_gt_schema:{gid}")
        if row["predicate_label"] == "none":
            errors.append(f"none_gt_emitted:{gid}")
        if row["vlsat_predicate_index"] != row["raw_3dssg_predicate_id"] - 1:
            errors.append(f"bad_gt_vlsat_index:{gid}")
        context = contexts.get(row["subgraph_id"])
        if context is None:
            errors.append(f"gt_missing_context:{gid}")
            continue
        if row["subject_id"] not in context["objects"]:
            errors.append(f"gt_missing_subject:{gid}")
        if row["object_id"] not in context["objects"]:
            errors.append(f"gt_missing_object:{gid}")
    if not rows:
        warnings.append("zero_ground_truth_rows")
    return errors, warnings


def count_rows(predictions: list[dict[str, Any]], ground_truth: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "subgraphs": len({row["subgraph_id"] for row in ground_truth}),
        "directed_pairs": len(
            {
                (row["subgraph_id"], row["edge"]["subject_id"], row["edge"]["object_id"])
                for row in predictions
            }
        ),
        "predictions": len(predictions),
        "ground_truth_edges": len(ground_truth),
        "predictions_by_family": dict(
            sorted(Counter(row["predicate"]["predicate_family"] for row in predictions).items())
        ),
        "ground_truth_by_family": dict(
            sorted(Counter(row["predicate_family"] for row in ground_truth).items())
        ),
    }


def make_report(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    validation = manifest["validation"]
    lines = [
        "# Prediction Export",
        "",
        f"Created at: `{manifest['created_at']}`",
        f"Baseline: `{manifest['baseline_name']}`",
        f"Split: `{manifest['split_name']}`",
        f"Status: `{manifest['status']}`",
        "",
        "## Inputs",
        "",
        f"- Subset file: `{manifest['subset_file']}`",
        f"- Raw dump file: `{manifest['raw_dump_file']}`",
        f"- Selected scans file: `{manifest['selected_scans_file']}`",
        "",
        "## Outputs",
        "",
        f"- Predictions: `{manifest['prediction_file']}`",
        f"- Ground truth: `{manifest['ground_truth_file']}`",
        f"- Manifest: `manifest.json`",
        "",
        "## Counts",
        "",
        f"- Subgraphs: `{counts['subgraphs']}`",
        f"- Directed pairs: `{counts['directed_pairs']}`",
        f"- Predictions: `{counts['predictions']}`",
        f"- Ground-truth edges: `{counts['ground_truth_edges']}`",
        "",
        "## Validation",
        "",
        f"- Passed: `{validation['passed']}`",
        f"- Errors: `{len(validation['errors'])}`",
        f"- Warnings: `{len(validation['warnings'])}`",
    ]
    if validation["errors"]:
        lines.extend(["", "### Errors", ""])
        for error in validation["errors"][:20]:
            lines.append(f"- `{error}`")
    if validation["warnings"]:
        lines.extend(["", "### Warnings", ""])
        for warning in validation["warnings"][:20]:
            lines.append(f"- `{warning}`")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This adapter preserves semantic prediction scores and H001 join identity only.",
            "It does not fit `p_geom_valid` and does not run final prediction-level evaluation.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []

    for name, path in {
        "subset_json": args.subset_json,
        "classes_file": args.classes_file,
        "relationships_file": args.relationships_file,
        "selected_scans": args.selected_scans,
    }.items():
        if path is not None and not path.exists():
            errors.append(f"missing_input:{name}:{relpath(path)}")
    if args.raw_dump_jsonl is not None and not args.raw_dump_jsonl.exists():
        errors.append(f"missing_input:raw_dump_jsonl:{relpath(args.raw_dump_jsonl)}")
    if not args.ground_truth_only and args.raw_dump_jsonl is None:
        errors.append("raw_dump_jsonl_required_unless_ground_truth_only")
    if args.export_policy == "top_m_per_pair" and args.top_m_per_pair <= 0:
        errors.append("top_m_per_pair_must_be_positive")
    if errors:
        print(json.dumps({"status": "blocked", "errors": errors}, sort_keys=True))
        return 2

    subset_data = load_json(args.subset_json)
    selected_scans = load_selected_scans(args.selected_scans)
    contexts, _ = build_contexts(subset_data, selected_scans)
    relationship_labels = read_lines(args.relationships_file)
    relationship_id_map = {label: idx for idx, label in enumerate(relationship_labels)}
    subset_source = relpath(args.subset_json)
    created_at = date.today().isoformat()

    ground_truth_rows, gt_warnings = make_ground_truth_rows(
        contexts, relationship_id_map, args.split_name, subset_source
    )
    warnings.extend(gt_warnings)

    raw_records: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
    if args.raw_dump_jsonl is not None:
        raw_records = load_jsonl(args.raw_dump_jsonl)
        prediction_rows, pred_warnings, pred_errors = make_prediction_rows(
            raw_records,
            contexts,
            relationship_id_map,
            args.split_name,
            subset_source,
            args.baseline_run_id,
            args.export_policy,
            args.top_m_per_pair,
        )
        warnings.extend(pred_warnings)
        errors.extend(pred_errors)

    pred_errors: list[str] = []
    pred_warnings: list[str] = []
    if prediction_rows or not args.ground_truth_only:
        pred_errors, pred_warnings = validate_predictions(prediction_rows, contexts)
    gt_errors, gt_warnings = validate_ground_truth(ground_truth_rows, contexts)
    if not args.ground_truth_only:
        errors.extend(pred_errors)
    warnings.extend(pred_warnings)
    errors.extend(gt_errors)
    warnings.extend(gt_warnings)

    status = "ready" if not errors and prediction_rows else "ground_truth_ready"
    if errors:
        status = "blocked"

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "baseline_name": BASELINE_NAME,
        "baseline_run_id": args.baseline_run_id,
        "split_name": args.split_name,
        "task_mode": TASK_MODE,
        "status": status,
        "prediction_file": "predictions.jsonl" if prediction_rows or not args.ground_truth_only else None,
        "ground_truth_file": "ground_truth.jsonl",
        "subset_file": subset_source,
        "class_file": relpath(args.classes_file),
        "relationship_file": relpath(args.relationships_file),
        "vlsat_relationship_file": "relations.txt",
        "selected_scans_file": relpath(args.selected_scans) if args.selected_scans else None,
        "raw_dump_file": relpath(args.raw_dump_jsonl) if args.raw_dump_jsonl else None,
        "export_policy": args.export_policy,
        "score_source": "vlsat_rel_cls_3d_sigmoid",
        "object_source": "3DSSG_subset_gt",
        "edge_source": "vlsat_edge_indices",
        "created_at": created_at,
        "counts": count_rows(prediction_rows, ground_truth_rows),
        "validation": {
            "passed": not errors and not (args.fail_on_warnings and warnings),
            "errors": errors,
            "warnings": warnings,
        },
        "notes": [
            "H001-Mini predictions are held-out/smoke validation data, not calibration train data.",
            "Do not fit p_geom_valid from this prediction export.",
            "Final prediction-level evaluation still requires geometry join and verifier/calibrator outputs.",
        ],
    }

    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "manifest.json", manifest)
        write_jsonl(args.output_dir / "ground_truth.jsonl", ground_truth_rows)
        if prediction_rows or not args.ground_truth_only:
            write_jsonl(args.output_dir / "predictions.jsonl", prediction_rows)
        (args.output_dir / "report.md").write_text(make_report(manifest), encoding="utf-8")

    print(
        json.dumps(
            {
                "status": status,
                "output_dir": relpath(args.output_dir),
                "predictions": len(prediction_rows),
                "ground_truth_edges": len(ground_truth_rows),
                "errors": len(errors),
                "warnings": len(warnings),
                "dry_run": args.dry_run,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )

    if errors or (args.fail_on_warnings and warnings):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
