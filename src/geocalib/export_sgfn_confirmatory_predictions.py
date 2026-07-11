#!/usr/bin/env python3
"""Project full-scan SGFN scores into frozen H001 subgraphs by pair identity."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FAMILY = {
    "standing on": "support_contact",
    "lying on": "support_contact",
    "supported by": "support_contact",
    "close by": "proximity",
    "higher than": "relative_vertical",
    "lower than": "relative_vertical",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--subset", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-id", default="sgfn_official_full_l160")
    parser.add_argument("--baseline-run-id", default="sgfn_target_v3_confirmatory")
    parser.add_argument("--prediction-split-id", default="official_test")
    parser.add_argument("--raw-schema", default="h001_sgfn_raw_scan_scores_v1")
    parser.add_argument("--split-name", default="official_test_h001_projection")
    parser.add_argument("--edge-source", default="sgfn_full_directed_graph")
    parser.add_argument("--predicate-vocab", default="SGFN_full_l160_sorted_26_no_none")
    parser.add_argument("--predicate-index-field", default="sgfn_predicate_index")
    parser.add_argument("--adapter-name", default="sgfn_full_scan_to_h001_subgraph")
    parser.add_argument("--manifest-schema", default="h001_sgfn_adapter_manifest_v1")
    parser.add_argument("--ready-status", default="sgfn_adapter_ready")
    parser.add_argument("--docker-service", default="sgfn_adapter_export")
    parser.add_argument("--expected-raw-scans", type=int, default=157)
    parser.add_argument("--expected-contexts", type=int, default=548)
    parser.add_argument("--expected-gt-denominator", type=int, default=3972)
    parser.add_argument("--in-scope-only", action="store_true")
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


def read_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def predicate_family(label: str) -> str:
    if label in FAMILY:
        return FAMILY[label]
    if label in {"left", "right", "front", "behind", "in front of"}:
        return "relative_horizontal"
    if label in {"attached to", "hanging on", "connected to"}:
        return "attachment_deferred"
    return "unsupported_first_pass"


def assign_ranks(rows: list[dict[str, Any]]) -> None:
    by_pair: dict[tuple[str, int, int], list[dict[str, Any]]] = defaultdict(list)
    by_subgraph: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (row["subgraph_id"], row["edge"]["subject_id"], row["edge"]["object_id"])
        by_pair[key].append(row)
        by_subgraph[row["subgraph_id"]].append(row)
    for group in by_pair.values():
        group.sort(key=lambda row: (-row["scores"]["ranking_score"], row["predicate"]["predicate_label"]))
        for rank, row in enumerate(group, 1):
            row["ranks"]["predicate_rank_for_pair"] = rank
    for group in by_subgraph.values():
        group.sort(
            key=lambda row: (
                -row["scores"]["ranking_score"],
                row["edge"]["subject_id"],
                row["edge"]["object_id"],
                row["predicate"]["predicate_label"],
            )
        )
        for rank, row in enumerate(group, 1):
            row["ranks"]["semantic_rank_in_subgraph"] = rank


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    raw_path, subset_path = resolve(root, args.raw), resolve(root, args.subset)
    gt_path, out = resolve(root, args.ground_truth), resolve(root, args.out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")
    subset = json.loads(subset_path.read_text(encoding="utf-8"))
    raw_relationship_names = (
        root / "local_dataset/3DSSG_subset/relationships.txt"
    ).read_text(encoding="utf-8").splitlines()
    raw_relationship_id = {
        label: index for index, label in enumerate(raw_relationship_names)
    }
    contexts_by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in subset["scans"]:
        contexts_by_scan[str(entry["scan"])].append(
            {
                "scan_id": str(entry["scan"]),
                "split": int(entry["split"]),
                "subgraph_id": f"{entry['scan']}_{int(entry['split'])}",
                "objects": {int(key): str(value) for key, value in entry["objects"].items()},
            }
        )
    predictions: list[dict[str, Any]] = []
    raw_scans: set[str] = set()
    covered_contexts: set[str] = set()
    covered_pairs: set[tuple[str, int, int]] = set()
    relation_names_seen: set[tuple[str, ...]] = set()
    for raw in read_jsonl(raw_path):
        if raw.get("schema_version") != args.raw_schema:
            raise ValueError(f"bad_raw_schema:{raw.get('schema_version')}")
        scan_id = str(raw["scan_id"])
        raw_scans.add(scan_id)
        relation_names = [str(value) for value in raw["relation_names"]]
        relation_names_seen.add(tuple(relation_names))
        node_ids = [int(value) for value in raw["node_instance_ids"]]
        edge_indices = raw["edge_indices"]
        scores = raw["rel_scores"]
        if len(edge_indices) != len(scores):
            raise ValueError(f"raw_edge_score_length_mismatch:{scan_id}")
        pair_scores: dict[tuple[int, int], tuple[int, list[float]]] = {}
        for edge_offset, (edge, score_row) in enumerate(zip(edge_indices, scores)):
            subject = node_ids[int(edge[0])]
            obj = node_ids[int(edge[1])]
            if len(score_row) != len(relation_names):
                raise ValueError(f"raw_score_width_mismatch:{scan_id}:{edge_offset}")
            pair_scores[(subject, obj)] = (edge_offset, [float(value) for value in score_row])
        for context in contexts_by_scan.get(scan_id, []):
            objects = context["objects"]
            emitted = 0
            for (subject, obj), (edge_offset, score_row) in pair_scores.items():
                if subject not in objects or obj not in objects:
                    continue
                covered_pairs.add((context["subgraph_id"], subject, obj))
                for predicate_index, (label, score) in enumerate(zip(relation_names, score_row)):
                    if args.in_scope_only and label not in FAMILY:
                        continue
                    pid = (
                        f"{args.source_id}:{args.prediction_split_id}:{scan_id}:{context['split']}:"
                        f"{subject}:{obj}:{label}"
                    )
                    predictions.append(
                        {
                            "schema_version": "h001_prediction_v1",
                            "record_type": "prediction",
                            "prediction_id": pid,
                            "baseline_name": args.source_id,
                            "baseline_run_id": args.baseline_run_id,
                            "split_name": args.split_name,
                            "subset_source": relpath(root, subset_path),
                            "scan_id": scan_id,
                            "subset_split_id": context["split"],
                            "subgraph_id": context["subgraph_id"],
                            "task_mode": "predcls_relation",
                            "edge": {
                                "edge_index": edge_offset,
                                "edge_source": args.edge_source,
                                "subject_id": subject,
                                "object_id": obj,
                                "subject_node_index": int(edge_indices[edge_offset][0]),
                                "object_node_index": int(edge_indices[edge_offset][1]),
                                "subject_label": objects[subject],
                                "object_label": objects[obj],
                                "subject_label_source": "3DSSG_subset",
                                "object_label_source": "3DSSG_subset",
                            },
                            "predicate": {
                                "predicate_label": label,
                                "predicate_family": predicate_family(label),
                                "raw_3dssg_predicate_id": raw_relationship_id[label],
                                "vlsat_predicate_index": raw_relationship_id[label] - 1,
                                args.predicate_index_field: predicate_index,
                                "predicate_vocab": args.predicate_vocab,
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
                                "name": args.adapter_name,
                                "version": "v1",
                                "coverage_policy": "no_missing_edge_synthesis",
                            },
                        }
                    )
                    emitted += 1
            if emitted:
                covered_contexts.add(context["subgraph_id"])
    if len(relation_names_seen) != 1:
        raise ValueError(f"relation_vocab_not_constant:{len(relation_names_seen)}")
    assign_ranks(predictions)
    relation_names = list(next(iter(relation_names_seen)))
    expected_contexts = {
        f"{entry['scan']}_{int(entry['split'])}" for entry in subset["scans"]
    }
    expected_pairs = {
        (f"{entry['scan']}_{int(entry['split'])}", int(subject), int(obj))
        for entry in subset["scans"]
        for subject in entry["objects"]
        for obj in entry["objects"]
        if int(subject) != int(obj)
    }
    gt_rows = list(read_jsonl(gt_path))
    scoped_gt = [row for row in gt_rows if row["predicate_family"] in set(FAMILY.values())]
    covered_gt = [
        row
        for row in scoped_gt
        if (row["subgraph_id"], int(row["subject_id"]), int(row["object_id"])) in covered_pairs
    ]
    duplicate_ids = [key for key, count in Counter(row["prediction_id"] for row in predictions).items() if count > 1]
    validations = {
        "raw_scan_count_expected": len(raw_scans) == args.expected_raw_scans,
        "relation_vocab_26_no_none": len(relation_names) == 26 and "none" not in relation_names,
        "relation_vocab_exactly_matches_3dssg_26": set(relation_names) == set(raw_relationship_names) - {"none"},
        "no_duplicate_prediction_ids": not duplicate_ids,
        "all_scores_in_unit_interval": all(0.0 <= row["scores"]["predicate_score"] <= 1.0 for row in predictions),
        "every_prediction_endpoint_in_subgraph": True,
        "target_context_count_expected": len(expected_contexts) == args.expected_contexts,
        "ground_truth_denominator_expected": len(scoped_gt) == args.expected_gt_denominator,
        "prediction_count_matches_scope": len(predictions) == len(covered_pairs) * (len(FAMILY) if args.in_scope_only else 26),
    }
    out.mkdir(parents=True, exist_ok=True)
    pred_path = out / "predictions.jsonl"
    with pred_path.open("w", encoding="utf-8") as handle:
        for row in predictions:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    missing_contexts = sorted(expected_contexts - covered_contexts)
    missing_pairs = sorted(expected_pairs - covered_pairs)
    with (out / "missing_pairs.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["subgraph_id", "subject_id", "object_id"])
        writer.writerows(missing_pairs)
    manifest = {
        "schema_version": args.manifest_schema,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": args.ready_status if all(validations.values()) else "blocked_scenegraphfusion_adapter_validation",
        "counts": {
            "raw_scans": len(raw_scans),
            "target_contexts": len(expected_contexts),
            "covered_contexts": len(covered_contexts),
            "missing_contexts": len(missing_contexts),
            "target_directed_pairs": len(expected_pairs),
            "covered_directed_pairs": len(covered_pairs),
            "missing_directed_pairs": len(missing_pairs),
            "prediction_rows": len(predictions),
            "in_scope_prediction_rows": sum(row["predicate"]["predicate_family"] in set(FAMILY.values()) for row in predictions),
            "global_in_scope_gt_rows": len(scoped_gt),
            "covered_in_scope_gt_rows": len(covered_gt),
            "missing_in_scope_gt_rows": len(scoped_gt) - len(covered_gt),
        },
        "coverage": {
            "context_rate": len(covered_contexts) / len(expected_contexts),
            "pair_rate": len(covered_pairs) / len(expected_pairs),
            "in_scope_gt_rate": len(covered_gt) / len(scoped_gt),
            "missing_source_edges_synthesized": 0,
            "in_scope_only_export": args.in_scope_only,
        },
        "validations": validations,
        "inputs": {
            "raw": {"path": relpath(root, raw_path), "sha256": sha256_file(raw_path)},
            "subset": {"path": relpath(root, subset_path), "sha256": sha256_file(subset_path)},
            "ground_truth": {"path": relpath(root, gt_path), "sha256": sha256_file(gt_path)},
        },
        "outputs": {
            "predictions": {"path": relpath(root, pred_path), "sha256": sha256_file(pred_path)},
            "missing_pairs": relpath(root, out / "missing_pairs.csv"),
        },
        "docker_command": f"env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm {args.docker_service}",
    }
    write_path = out / "manifest.json"
    write_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "counts": manifest["counts"], "out": relpath(root, out)}))
    return 0 if manifest["status"] == args.ready_status else 2


if __name__ == "__main__":
    raise SystemExit(main())
