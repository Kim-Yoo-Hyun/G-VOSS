#!/usr/bin/env python3
"""Develop source-scale-robust bounded fusion on observed ReplicaSSG/FROSS."""

from __future__ import annotations

import argparse
import csv
import heapq
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from run_replicassg_prospective_evaluation import (
    KS,
    finite,
    key,
    load_gt,
    probability,
    raw_numeric,
)


SCHEMA_VERSION = "h001_replicassg_development_v2_evaluation"
BASELINES = ("semantic_only", "family_product", "rank_average_family")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("/workspace"))
    parser.add_argument("--verification", type=Path, required=True)
    parser.add_argument("--ground-truth", type=Path, required=True)
    parser.add_argument("--models", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--n-bootstrap", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=20260712)
    parser.add_argument("--docker-service", default="replicassg_development_v2")
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


def percentile_ranks(items: list[dict[str, Any]], field: str) -> dict[str, float]:
    ordered = sorted(items, key=lambda item: (-float(item[field]), item["key"]))
    denominator = max(len(ordered) - 1, 1)
    return {
        item["id"]: 1.0 - index / denominator
        for index, item in enumerate(ordered)
    }


def load_candidates(path: Path, models: dict[str, Any], scans: list[str]) -> dict[str, list[dict[str, Any]]]:
    grouped = {scan: [] for scan in scans}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            scan = str(row["scan_id"])
            family = str(row["predicate"]["predicate_family"])
            if scan not in grouped or family not in {"proximity", "relative_vertical"}:
                raise ValueError("candidate_outside_development_scope")
            predicate = str(row["predicate"]["predicate_label"])
            semantic = finite((row.get("semantic") or {}).get("ranking_score"))
            if semantic is None:
                raise ValueError(f"missing_semantic:{row['prediction_id']}")
            raw = raw_numeric(row)
            compatibility = probability(models["family_models"][family], family, predicate, raw)
            grouped[scan].append({
                "id": str(row["prediction_id"]),
                "key": key(row),
                "semantic": semantic,
                "compatibility": compatibility,
                "status": row.get("verification_status"),
            })
    for scan, items in grouped.items():
        if not items:
            raise ValueError(f"empty_context:{scan}")
        semantic_pct = percentile_ranks(items, "semantic")
        compatibility_pct = percentile_ranks(items, "compatibility")
        for item in items:
            item["semantic_pct"] = semantic_pct[item["id"]]
            item["compatibility_pct"] = compatibility_pct[item["id"]]
    return grouped


def candidate_configs(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    grid = protocol["grid"]
    configs: list[dict[str, Any]] = []
    for max_displacement in grid["max_displacement"]:
        configs.append({
            "id": f"quantile_product__d{max_displacement}",
            "family": "quantile_product",
            "alpha": None,
            "tau": None,
            "max_displacement": int(max_displacement),
        })
    for family in ("bounded_raw", "bounded_quantile"):
        for alpha in grid["alpha"]:
            for tau in grid["tau"]:
                for max_displacement in grid["max_displacement"]:
                    configs.append({
                        "id": f"{family}__a{alpha:g}__t{tau:g}__d{max_displacement}",
                        "family": family,
                        "alpha": float(alpha),
                        "tau": float(tau),
                        "max_displacement": int(max_displacement),
                    })
    return configs


def raw_score(item: dict[str, Any], config: dict[str, Any]) -> float:
    family = config["family"]
    if family == "quantile_product":
        return item["semantic_pct"] * item["compatibility_pct"]
    compatibility = item["compatibility"] if family == "bounded_raw" else item["compatibility_pct"]
    penalty = config["alpha"] * max(0.0, config["tau"] - compatibility)
    return item["semantic_pct"] - penalty


def bounded_displacement_order(
    semantic_order: list[dict[str, Any]],
    config: dict[str, Any],
    max_displacement: int,
) -> list[dict[str, Any]]:
    """Decode by fusion priority while guaranteeing |new_rank-source_rank| <= B."""
    available_by_score: list[tuple[float, tuple[Any, ...], int, str, dict[str, Any]]] = []
    available_by_deadline: list[tuple[int, str, dict[str, Any]]] = []
    selected: set[str] = set()
    next_original = 0
    ranked: list[dict[str, Any]] = []
    for new_index in range(len(semantic_order)):
        furthest_admissible = min(len(semantic_order) - 1, new_index + max_displacement)
        while next_original <= furthest_admissible:
            item = semantic_order[next_original]
            heapq.heappush(
                available_by_score,
                (-raw_score(item, config), item["key"], next_original, item["id"], item),
            )
            heapq.heappush(available_by_deadline, (next_original, item["id"], item))
            next_original += 1
        while available_by_deadline and available_by_deadline[0][1] in selected:
            heapq.heappop(available_by_deadline)
        deadline_index, deadline_id, deadline_item = available_by_deadline[0]
        if deadline_index + max_displacement <= new_index:
            chosen_id, chosen = deadline_id, deadline_item
        else:
            while available_by_score and available_by_score[0][3] in selected:
                heapq.heappop(available_by_score)
            _, _, _, chosen_id, chosen = heapq.heappop(available_by_score)
        selected.add(chosen_id)
        ranked.append(chosen)
    return ranked


def rank_config(items: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, Any]]:
    semantic_order = sorted(items, key=lambda item: (-item["semantic"], item["key"]))
    max_displacement = config["max_displacement"]
    if max_displacement <= 0:
        return sorted(items, key=lambda item: (-raw_score(item, config), item["key"]))
    return bounded_displacement_order(semantic_order, config, max_displacement)


def rank_baseline(items: list[dict[str, Any]], method: str) -> list[dict[str, Any]]:
    if method == "semantic_only":
        return sorted(items, key=lambda item: (-item["semantic"], item["key"]))
    if method == "family_product":
        return sorted(items, key=lambda item: (-(item["semantic"] * item["compatibility"]), item["key"]))
    if method == "rank_average_family":
        return sorted(items, key=lambda item: (-(0.5 * (item["semantic_pct"] + item["compatibility_pct"])), item["key"]))
    raise ValueError(f"unknown_baseline:{method}")


def cell(ranked: list[dict[str, Any]], gt: set[tuple[Any, ...]], k_value: int) -> dict[str, int]:
    selected = ranked[:k_value]
    statuses = [item["status"] for item in selected if item["status"] in {"satisfied", "uncertain", "violated"}]
    return {
        "recall_num": len({item["key"] for item in selected} & gt),
        "recall_den": len(gt),
        "violation_num": sum(status == "violated" for status in statuses),
        "violation_den": len(statuses),
    }


def build_contributions(
    grouped: dict[str, list[dict[str, Any]]],
    gt: dict[str, set[tuple[Any, ...]]],
    scans: list[str],
    configs: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, list[dict[str, int]]]], dict[str, dict[str, list[dict[str, Any]]]]]:
    values: dict[str, dict[str, list[dict[str, int]]]] = {
        method: {str(k): [] for k in KS} for method in (*BASELINES, *(config["id"] for config in configs))}
    rankings: dict[str, dict[str, list[dict[str, Any]]]] = {scan: {} for scan in scans}
    for scan in scans:
        for method in BASELINES:
            ranked = rank_baseline(grouped[scan], method)
            rankings[scan][method] = ranked
            for k_value in KS:
                values[method][str(k_value)].append(cell(ranked, gt[scan], k_value))
        for config in configs:
            ranked = rank_config(grouped[scan], config)
            rankings[scan][config["id"]] = ranked
            for k_value in KS:
                values[config["id"]][str(k_value)].append(cell(ranked, gt[scan], k_value))
    return values, rankings


def aggregate(cells: list[dict[str, int]], indices: list[int] | np.ndarray) -> dict[str, float | int | None]:
    chosen = [cells[int(index)] for index in indices]
    result: dict[str, float | int | None] = {}
    for metric in ("recall", "violation"):
        numerator = sum(item[f"{metric}_num"] for item in chosen)
        denominator = sum(item[f"{metric}_den"] for item in chosen)
        result[metric] = numerator / denominator if denominator else None
        result[f"{metric}_num"] = numerator
        result[f"{metric}_den"] = denominator
    return result


def objective(
    values: dict[str, dict[str, list[dict[str, int]]]],
    config_id: str,
    indices: list[int],
) -> tuple[Any, ...]:
    current = aggregate(values[config_id]["100"], indices)
    semantic = aggregate(values["semantic_only"]["100"], indices)
    delta_recall = float(current["recall"] - semantic["recall"])
    feasible = delta_recall >= -0.01
    low_k_violation = np.mean([
        aggregate(values[config_id][str(k_value)], indices)["violation"]
        for k_value in (10, 50)
    ])
    return (
        0 if feasible else 1,
        0.0 if feasible else -delta_recall,
        float(current["violation"]),
        -float(current["recall"]),
        float(low_k_violation),
        config_id,
    )


def percentile_ci(values: np.ndarray) -> list[float | None]:
    finite_values = values[np.isfinite(values)]
    if not len(finite_values):
        return [None, None]
    return [float(value) for value in np.percentile(finite_values, (2.5, 97.5))]


def summarize_method(
    method_cells: dict[str, list[dict[str, int]]],
    semantic_cells: dict[str, list[dict[str, int]]],
    samples: np.ndarray,
) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for k_value in KS:
        key_value = str(k_value)
        current = aggregate(method_cells[key_value], list(range(len(method_cells[key_value]))))
        semantic = aggregate(semantic_cells[key_value], list(range(len(semantic_cells[key_value]))))
        report[key_value] = {}
        for metric in ("recall", "violation"):
            current_boot, delta_boot = [], []
            for sample in samples:
                sampled = aggregate(method_cells[key_value], sample)
                sampled_semantic = aggregate(semantic_cells[key_value], sample)
                current_boot.append(sampled[metric] if sampled[metric] is not None else np.nan)
                delta_boot.append(
                    sampled[metric] - sampled_semantic[metric]
                    if sampled[metric] is not None and sampled_semantic[metric] is not None else np.nan
                )
            report[key_value][metric] = {
                "point": current[metric],
                "ci95": percentile_ci(np.asarray(current_boot)),
                "numerator": current[f"{metric}_num"],
                "denominator": current[f"{metric}_den"],
                "delta_vs_semantic": current[metric] - semantic[metric],
                "paired_delta_ci95": percentile_ci(np.asarray(delta_boot)),
            }
    return report


def loso_selection(
    values: dict[str, dict[str, list[dict[str, int]]]],
    config_ids: list[str],
    scans: list[str],
) -> tuple[dict[str, dict[str, list[dict[str, int]]]], dict[str, str]]:
    selected_cells = {str(k): [] for k in KS}
    selected: dict[str, str] = {}
    all_indices = list(range(len(scans)))
    for heldout_index, scan in enumerate(scans):
        train_indices = [index for index in all_indices if index != heldout_index]
        winner = min(config_ids, key=lambda config_id: objective(values, config_id, train_indices))
        selected[scan] = winner
        for k_value in KS:
            selected_cells[str(k_value)].append(values[winner][str(k_value)][heldout_index])
    return {"loso_selected": selected_cells}, selected


def rank_diagnostics(
    rankings: dict[str, dict[str, list[dict[str, Any]]]],
    scans: list[str],
    method_id: str,
) -> dict[str, Any]:
    displacements: list[int] = []
    overlap: dict[str, list[float]] = {str(k): [] for k in KS}
    for scan in scans:
        semantic = rankings[scan]["semantic_only"]
        selected = rankings[scan][method_id]
        semantic_rank = {item["id"]: index for index, item in enumerate(semantic, 1)}
        selected_rank = {item["id"]: index for index, item in enumerate(selected, 1)}
        displacements.extend(selected_rank[item_id] - rank for item_id, rank in semantic_rank.items())
        for k_value in KS:
            left = {item["id"] for item in semantic[:k_value]}
            right = {item["id"] for item in selected[:k_value]}
            union = left | right
            overlap[str(k_value)].append(len(left & right) / len(union) if union else 1.0)
    array = np.asarray(displacements)
    return {
        "mean_absolute_rank_displacement": float(np.mean(np.abs(array))),
        "p95_absolute_rank_displacement": float(np.percentile(np.abs(array), 95)),
        "maximum_absolute_rank_displacement": int(np.max(np.abs(array))),
        "maximum_demotion": int(np.max(array)),
        "maximum_promotion": int(-np.min(array)),
        "mean_top_k_jaccard": {key_value: float(np.mean(items)) for key_value, items in overlap.items()},
    }


def displacement_bound_violations(
    rankings: dict[str, dict[str, list[dict[str, Any]]]],
    scans: list[str],
    configs: list[dict[str, Any]],
) -> int:
    violations = 0
    for scan in scans:
        semantic_rank = {
            item["id"]: index
            for index, item in enumerate(rankings[scan]["semantic_only"], 1)
        }
        for config in configs:
            max_displacement = config["max_displacement"]
            if max_displacement <= 0:
                continue
            current_rank = {
                item["id"]: index
                for index, item in enumerate(rankings[scan][config["id"]], 1)
            }
            violations += sum(
                abs(current_rank[item_id] - original_rank) > max_displacement
                for item_id, original_rank in semantic_rank.items()
            )
    return violations


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# ReplicaSSG/FROSS Development Diagnostic v2",
        "",
        f"Status: `{report['status']}`",
        "",
        "This result uses the observed ReplicaSSG test target for method development. It is not prospective confirmation.",
        f"The regenerated FROSS execution contains {report['source_execution']['regenerated_candidate_rows']} candidates versus "
        f"{report['source_execution']['reference_candidate_rows']} in the historical run; all rows in this table come from the same regenerated execution.",
        "",
        "| method | K | Recall | delta Recall | Violation | delta Violation |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for method in ("semantic_only", "family_product", "rank_average_family", "loso_selected", "full_development_selected"):
        summary = report["metrics"][method]
        for k_value in (10, 50, 100):
            cell_value = summary[str(k_value)]
            lines.append(
                f"| {method} | {k_value} | {cell_value['recall']['point']:.5f} | "
                f"{cell_value['recall']['delta_vs_semantic']:+.5f} | {cell_value['violation']['point']:.5f} | "
                f"{cell_value['violation']['delta_vs_semantic']:+.5f} |"
            )
    lines.extend([
        "",
        f"Full-development selected configuration: `{report['selection']['full_development']}`",
        f"LOSO diagnostic gate: `{report['diagnostic_gate']['decision']}`",
        "",
        "The LOSO row selects a configuration on ten scenes for each held-out scene. The full-development row is optimistic and is reported only as the deployment configuration chosen from this development target.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    verification = resolve(root, args.verification)
    ground_truth = resolve(root, args.ground_truth)
    models_path = resolve(root, args.models)
    protocol_path = resolve(root, args.protocol)
    out = resolve(root, args.out)
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"nonempty_output:{out}")
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol.get("classification") != "cross_dataset_transfer_stress_test_and_development_diagnostic":
        raise ValueError("development_classification_missing")
    models = json.loads(models_path.read_text(encoding="utf-8"))
    with ground_truth.open("r", encoding="utf-8") as handle:
        scans = sorted({json.loads(line)["scan_id"] for line in handle if line.strip()})
    gt, _ = load_gt(ground_truth, scans)
    grouped = load_candidates(verification, models, scans)
    configs = candidate_configs(protocol)
    config_by_id = {config["id"]: config for config in configs}
    values, rankings = build_contributions(grouped, gt, scans, configs)
    config_ids = [config["id"] for config in configs]
    full_indices = list(range(len(scans)))
    full_selected = min(config_ids, key=lambda config_id: objective(values, config_id, full_indices))
    loso_values, loso_selected = loso_selection(values, config_ids, scans)
    rng = np.random.default_rng(args.seed)
    samples = rng.integers(0, len(scans), size=(args.n_bootstrap, len(scans)))
    metrics = {
        method: summarize_method(values[method], values["semantic_only"], samples)
        for method in BASELINES
    }
    metrics["loso_selected"] = summarize_method(
        loso_values["loso_selected"], values["semantic_only"], samples
    )
    metrics["full_development_selected"] = summarize_method(
        values[full_selected], values["semantic_only"], samples
    )
    sweep_rows = []
    for config_id in config_ids:
        for k_value in KS:
            summary = aggregate(values[config_id][str(k_value)], full_indices)
            semantic = aggregate(values["semantic_only"][str(k_value)], full_indices)
            sweep_rows.append({
                **config_by_id[config_id],
                "k": k_value,
                "recall": summary["recall"],
                "delta_recall": summary["recall"] - semantic["recall"],
                "violation": summary["violation"],
                "delta_violation": summary["violation"] - semantic["violation"],
            })
    loso_primary = metrics["loso_selected"]["100"]
    recall_ci = loso_primary["recall"]["paired_delta_ci95"]
    violation_ci = loso_primary["violation"]["paired_delta_ci95"]
    diagnostic_gate = {
        "decision": "pass" if recall_ci[0] > -0.01 and violation_ci[1] < 0 else "fail",
        "rule": "LOSO paired dRecall@100 CI lower > -0.01 and paired dViolation@100 CI upper < 0",
        "recall_guardrail_pass": recall_ci[0] > -0.01,
        "violation_gate_pass": violation_ci[1] < 0,
    }
    counts = {
        "contexts": len(scans),
        "candidate_rows": sum(len(items) for items in grouped.values()),
        "gt_denominator": sum(len(items) for items in gt.values()),
        "candidate_rows_by_context": {scan: len(grouped[scan]) for scan in scans},
        "contexts_with_candidates_le_100": sum(len(items) <= 100 for items in grouped.values()),
        "grid_configurations": len(configs),
    }
    validations = {
        "classification_is_development_diagnostic": protocol["classification"] == "cross_dataset_transfer_stress_test_and_development_diagnostic",
        "test_specific_tuning_disclosed": protocol.get("test_specific_tuning") is True,
        "contexts_exactly_11": counts["contexts"] == 11,
        "candidate_rows_nonempty": counts["candidate_rows"] > 0,
        "gt_denominator_exactly_172": counts["gt_denominator"] == 172,
        "grid_configurations_exactly_355": counts["grid_configurations"] == 355,
        "displacement_bounds_hold": displacement_bound_violations(rankings, scans, configs) == 0,
        "bootstrap_is_fixed": args.n_bootstrap == 1000 and args.seed == 20260712,
    }
    status = "completed_development_diagnostic" if all(validations.values()) else "blocked_development_diagnostic"
    report = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "classification": protocol["classification"],
        "test_specific_tuning": True,
        "counts": counts,
        "source_execution": {
            "reference_candidate_rows": protocol["source_execution_policy"]["reference_candidate_rows"],
            "regenerated_candidate_rows": counts["candidate_rows"],
            "delta_from_reference": counts["candidate_rows"] - protocol["source_execution_policy"]["reference_candidate_rows"],
            "interpretation": "All evaluated conditions use the same regenerated source rows. A candidate-count difference from the historical execution is disclosed as source-execution variation, so this development result is not directly pooled with the earlier transfer table.",
        },
        "selection": {
            "full_development": full_selected,
            "full_development_parameters": config_by_id[full_selected],
            "loso_by_heldout_scene": loso_selected,
            "loso_selection_counts": dict(Counter(loso_selected.values())),
        },
        "metrics": metrics,
        "diagnostic_gate": diagnostic_gate,
        "validations": validations,
        "rank_diagnostics": {
            "full_development_selected": rank_diagnostics(rankings, scans, full_selected),
            "family_product": rank_diagnostics(rankings, scans, "family_product"),
            "rank_average_family": rank_diagnostics(rankings, scans, "rank_average_family"),
        },
        "inputs": {
            "verification": {"path": relpath(root, verification), "sha256": sha256(verification)},
            "ground_truth": {"path": relpath(root, ground_truth), "sha256": sha256(ground_truth)},
            "models": {"path": relpath(root, models_path), "sha256": sha256(models_path)},
            "protocol": {"path": relpath(root, protocol_path), "sha256": sha256(protocol_path)},
        },
        "claim_boundary": protocol["claim_boundary"],
        "docker_command": f"env UID=$(id -u) GID=$(id -g) docker compose -f configs/fross/compose.yaml run --rm {args.docker_service}",
    }
    out.mkdir(parents=True, exist_ok=False)
    summary_json = out / "summary.json"
    summary_md = out / "summary.md"
    sweep_csv = out / "sweep.csv"
    summary_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    summary_md.write_text(markdown(report), encoding="utf-8")
    with sweep_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(sweep_rows[0]))
        writer.writeheader()
        writer.writerows(sweep_rows)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": report["created_at_utc"],
        "status": report["status"],
        "classification": report["classification"],
        "outputs": {
            name: {"path": relpath(root, path), "sha256": sha256(path)}
            for name, path in {
                "summary.json": summary_json,
                "summary.md": summary_md,
                "sweep.csv": sweep_csv,
            }.items()
        },
        "docker_command": report["docker_command"],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "selection": report["selection"],
        "diagnostic_gate": diagnostic_gate,
        "primary_metrics": {method: metrics[method]["100"] for method in metrics},
    }, sort_keys=True))
    return 0 if all(validations.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
