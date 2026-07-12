#!/usr/bin/env python3
"""Evaluate a Replica-developed bounded fusion on the three 3DSSG sources."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from run_replicassg_development_v2 import (
    BASELINES,
    KS,
    cell,
    percentile_ranks,
    rank_baseline,
    rank_config,
    rank_diagnostics,
    summarize_method,
)
from run_train_only_evaluation import (
    FAMILIES,
    candidate_key,
    finite,
    load_gt,
    probability,
    raw_numeric,
)


SCHEMA_VERSION = "h001_bounded_fusion_cross_source_evaluation_v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--selection-summary", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--source", action="append", required=True, help="NAME=VERIFICATION_JSONL")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260712)
    parser.add_argument("--docker-service", default="bounded_fusion_cross_source")
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_sources(root: Path, values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"invalid_source:{value}")
        name, raw_path = value.split("=", 1)
        if not name or name in result:
            raise ValueError(f"duplicate_or_empty_source:{name}")
        result[name] = resolve(root, Path(raw_path))
    return result


def load_candidates(path: Path, models: dict[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], int]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    input_rows = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            input_rows += 1
            row = json.loads(line)
            family = str(row["predicate"]["predicate_family"])
            if family not in FAMILIES:
                continue
            semantic = finite((row.get("semantic") or {}).get("ranking_score"))
            if semantic is None:
                raise ValueError(f"missing_semantic:{row['prediction_id']}")
            predicate = str(row["predicate"]["predicate_label"])
            compatibility = probability(
                models["family_models"][family],
                family,
                predicate,
                raw_numeric(row),
            )
            context = str(row["subgraph_id"])
            grouped.setdefault(context, []).append({
                "id": str(row["prediction_id"]),
                "key": candidate_key(row),
                "semantic": semantic,
                "compatibility": compatibility,
                "status": row.get("verification_status") or (row.get("verification") or {}).get("verification_status"),
            })
    for items in grouped.values():
        semantic_pct = percentile_ranks(items, "semantic")
        compatibility_pct = percentile_ranks(items, "compatibility")
        for item in items:
            item["semantic_pct"] = semantic_pct[item["id"]]
            item["compatibility_pct"] = compatibility_pct[item["id"]]
    return grouped, input_rows


def evaluate_source(
    grouped: dict[str, list[dict[str, Any]]],
    gt: dict[str, set[tuple[Any, ...]]],
    contexts: list[str],
    config: dict[str, Any],
    samples: np.ndarray,
) -> tuple[dict[str, Any], dict[str, dict[str, list[dict[str, Any]]]]]:
    methods = (*BASELINES, "bounded_selected")
    values = {method: {str(k): [] for k in KS} for method in methods}
    rankings: dict[str, dict[str, list[dict[str, Any]]]] = {context: {} for context in contexts}
    for context in contexts:
        items = grouped.get(context, [])
        for method in BASELINES:
            ranked = rank_baseline(items, method)
            rankings[context][method] = ranked
            for k_value in KS:
                values[method][str(k_value)].append(cell(ranked, gt[context], k_value))
        ranked = rank_config(items, config)
        rankings[context]["bounded_selected"] = ranked
        for k_value in KS:
            values["bounded_selected"][str(k_value)].append(cell(ranked, gt[context], k_value))
    metrics = {
        method: summarize_method(values[method], values["semantic_only"], samples)
        for method in methods
    }
    return metrics, rankings


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Replica-Developed Bounded Fusion: Cross-Source Evaluation",
        "",
        f"Selected configuration: `{report['selection']['id']}`",
        "",
        "| Source | Method | K | Recall | delta Recall | Violation | delta Violation |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for source, payload in report["sources"].items():
        for method in ("semantic_only", "family_product", "rank_average_family", "bounded_selected"):
            for k_value in (10, 50, 100):
                item = payload["metrics"][method][str(k_value)]
                lines.append(
                    f"| {source} | {method} | {k_value} | {item['recall']['point']:.5f} | "
                    f"{item['recall']['delta_vs_semantic']:+.5f} | {item['violation']['point']:.5f} | "
                    f"{item['violation']['delta_vs_semantic']:+.5f} |"
                )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    selection_path = resolve(root, args.selection_summary)
    models_path = resolve(root, args.models)
    gt_path = resolve(root, args.ground_truth)
    out = resolve(root, args.out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")
    source_paths = parse_sources(root, args.source)
    selection = json.loads(selection_path.read_text(encoding="utf-8"))
    if selection.get("classification") != "cross_dataset_transfer_stress_test_and_development_diagnostic":
        raise ValueError("selection_is_not_development_diagnostic")
    config = selection["selection"]["full_development_parameters"]
    models = json.loads(models_path.read_text(encoding="utf-8"))
    gt_bearing, _ = load_gt(gt_path)
    contexts: list[str] | None = None
    gt: dict[str, set[tuple[Any, ...]]] | None = None
    samples: np.ndarray | None = None
    rng = np.random.default_rng(args.seed)
    sources: dict[str, Any] = {}
    for name, path in source_paths.items():
        grouped, input_rows = load_candidates(path, models)
        source_contexts = sorted(grouped)
        if contexts is None:
            contexts = source_contexts
            gt = {context: gt_bearing.get(context, set()) for context in contexts}
            samples = rng.integers(0, len(contexts), size=(args.n_bootstrap, len(contexts)))
        elif source_contexts != contexts:
            raise ValueError(f"source_context_mismatch:{name}")
        assert gt is not None and samples is not None
        metrics, rankings = evaluate_source(grouped, gt, contexts, config, samples)
        sources[name] = {
            "input_rows": input_rows,
            "in_scope_rows": sum(len(items) for items in grouped.values()),
            "contexts": len(grouped),
            "metrics": metrics,
            "rank_diagnostics": {
                method: rank_diagnostics(rankings, contexts, method)
                for method in ("family_product", "rank_average_family", "bounded_selected")
            },
            "input": {"path": relpath(root, path), "sha256": sha256(path)},
        }
    assert contexts is not None and gt is not None
    validations = {
        "three_sources": len(sources) == 3,
        "contexts_548": len(contexts) == 548,
        "gt_denominator_3972": sum(len(items) for items in gt.values()) == 3972,
        "gt_free_contexts_included": sum(not gt[context] for context in contexts) == 10,
        "selection_discloses_test_specific_tuning": selection.get("test_specific_tuning") is True,
        "bootstrap_fixed": args.n_bootstrap == 1000 and args.seed == 20260712,
    }
    status = "completed_benchmark_evaluation" if all(validations.values()) else "blocked_benchmark_evaluation"
    report = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "classification": "benchmark evaluation of a ReplicaSSG-developed configuration; not prospective confirmation",
        "selection": config,
        "sources": sources,
        "validations": validations,
        "inputs": {
            "selection_summary": {"path": relpath(root, selection_path), "sha256": sha256(selection_path)},
            "models": {"path": relpath(root, models_path), "sha256": sha256(models_path)},
            "ground_truth": {"path": relpath(root, gt_path), "sha256": sha256(gt_path)},
        },
        "docker_command": f"env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml run --rm {args.docker_service}",
    }
    out.mkdir(parents=True, exist_ok=False)
    summary_json = out / "summary.json"
    summary_md = out / "summary.md"
    summary_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_md.write_text(markdown(report), encoding="utf-8")
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": report["created_at_utc"],
        "outputs": {
            "summary.json": {"path": relpath(root, summary_json), "sha256": sha256(summary_json)},
            "summary.md": {"path": relpath(root, summary_md), "sha256": sha256(summary_md)},
        },
        "docker_command": report["docker_command"],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": status,
        "selection": config,
        "k100": {
            source: payload["metrics"]["bounded_selected"]["100"]
            for source, payload in sources.items()
        },
    }, sort_keys=True))
    return 0 if all(validations.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
