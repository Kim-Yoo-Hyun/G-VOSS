#!/usr/bin/env python3
"""Evaluate H001 verifier on held-out GT positives and GT-derived negatives."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT

from export_calibration import (
    compute_features,
    load_relationship_id_map,
    load_scan_geometries,
    proximity_margin,
    support_margin,
)
from join_predictions import (
    DEFAULT_POINT_THRESHOLDS,
    G2_POLICY_NAME,
    PRIMARY_FAMILIES,
    load_point_context_cached,
    make_verification_row_g2,
)
from apply_verifier_v2 import DEFAULT_THRESHOLDS as V2_THRESHOLDS


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT
DEFAULT_DATASET_ROOT = REPO_ROOT / "local_dataset"
DEFAULT_SUBSET_JSON = DEFAULT_DATASET_ROOT / "3DSSG_subset" / "relationships_validation.json"
DEFAULT_RELATIONSHIPS_FILE = DEFAULT_DATASET_ROOT / "3DSSG_subset" / "relationships.txt"
DEFAULT_SELECTED_SCANS = H001_ROOT / "artifacts/subset/h001_validation_hardened/scans.txt"
DEFAULT_GROUND_TRUTH = H001_ROOT / "artifacts/evaluation/vlsat_closed_set/hardened/ground_truth.jsonl"
DEFAULT_MODEL = H001_ROOT / "artifacts/calibration/p_geom_valid_smoke/model.json"
DEFAULT_OUTPUT_DIR = H001_ROOT / "artifacts/evaluation/vlsat_closed_set/hardened/gt_eval"

SCHEMA_VERSION = "h001_gt_verifier_eval_v1"
MANIFEST_SCHEMA_VERSION = "h001_gt_verifier_manifest_v1"
SUPPORT_LABEL_ORDER = ("standing on", "lying on", "supported by")
RELATIVE_INVERSE = {"higher than": "lower than", "lower than": "higher than"}


@dataclass(frozen=True)
class Context:
    scan_id: str
    subset_split_id: int
    subgraph_id: str
    object_labels: dict[int, str]
    geometries: dict[int, dict[str, Any]]
    positive_edges: set[tuple[int, int, str]]
    proximity_pairs: set[frozenset[int]]
    support_pairs: set[frozenset[int]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--subset-json", type=Path, default=DEFAULT_SUBSET_JSON)
    parser.add_argument("--relationships-file", type=Path, default=DEFAULT_RELATIONSHIPS_FILE)
    parser.add_argument("--selected-scans", type=Path, default=DEFAULT_SELECTED_SCANS)
    parser.add_argument("--ground-truth-jsonl", type=Path, default=DEFAULT_GROUND_TRUTH)
    parser.add_argument("--model-json", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--verification-policy", choices=["point_subtype"], default="point_subtype")
    parser.add_argument("--point-cache-size", type=int, default=4)
    parser.add_argument("--max-negatives-per-family", type=int)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc
    return records


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")


def relpath(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_selected_scans(path: Path) -> set[str]:
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def predicate_family(label: str) -> str:
    if label in SUPPORT_LABEL_ORDER:
        return "support_contact"
    if label == "close by":
        return "proximity"
    if label in RELATIVE_INVERSE:
        return "relative_vertical"
    return "unsupported_first_pass"


def finite_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def summarize_values(values: list[float]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "max": None, "mean": None}
    return {"count": len(values), "min": min(values), "max": max(values), "mean": sum(values) / len(values)}


def load_contexts(
    *,
    subset_json: Path,
    dataset_root: Path,
    selected_scans: set[str],
) -> tuple[dict[str, Context], list[str], list[str]]:
    subset = load_json(subset_json)
    contexts: dict[str, Context] = {}
    geometry_cache: dict[str, dict[int, dict[str, Any]]] = {}
    warnings: list[str] = []
    errors: list[str] = []

    for entry in subset.get("scans", []):
        scan_id = str(entry["scan"])
        if scan_id not in selected_scans:
            continue
        split_id = int(entry["split"])
        subgraph_id = f"{scan_id}_{split_id}"
        object_labels = {int(key): str(value) for key, value in entry.get("objects", {}).items()}

        if scan_id not in geometry_cache:
            geometries, geom_warnings, geom_errors = load_scan_geometries(dataset_root, scan_id)
            geometry_cache[scan_id] = geometries
            warnings.extend(geom_warnings)
            errors.extend(geom_errors)

        positive_edges: set[tuple[int, int, str]] = set()
        proximity_pairs: set[frozenset[int]] = set()
        support_pairs: set[frozenset[int]] = set()
        for rel in entry.get("relationships", []):
            subject_id, object_id, _, label = int(rel[0]), int(rel[1]), int(rel[2]), str(rel[3])
            positive_edges.add((subject_id, object_id, label))
            family = predicate_family(label)
            if family == "proximity":
                proximity_pairs.add(frozenset((subject_id, object_id)))
            elif family == "support_contact":
                support_pairs.add(frozenset((subject_id, object_id)))

        contexts[subgraph_id] = Context(
            scan_id=scan_id,
            subset_split_id=split_id,
            subgraph_id=subgraph_id,
            object_labels=object_labels,
            geometries=geometry_cache[scan_id],
            positive_edges=positive_edges,
            proximity_pairs=proximity_pairs,
            support_pairs=support_pairs,
        )
    return contexts, warnings, errors


def features_for(context: Context, subject_id: int, object_id: int) -> tuple[dict[str, Any] | None, list[str]]:
    missing: list[str] = []
    subject = context.geometries.get(subject_id)
    obj = context.geometries.get(object_id)
    if subject is None:
        missing.append(str(subject_id))
    if obj is None:
        missing.append(str(object_id))
    if missing:
        return None, missing
    return compute_features(subject, obj), []


def prediction_like(
    *,
    candidate_id: str,
    candidate_kind: str,
    context: Context,
    subject_id: int,
    object_id: int,
    predicate_label: str,
    raw_id: int | None,
    created_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": "h001_gt_verifier_candidate_v1",
        "prediction_id": candidate_id,
        "baseline_name": "gt_based_verifier_eval",
        "baseline_run_id": "h001_gt_eval_20260506",
        "split_name": "hardened_gt_eval",
        "scan_id": context.scan_id,
        "subset_split_id": context.subset_split_id,
        "subgraph_id": context.subgraph_id,
        "edge": {
            "subject_id": subject_id,
            "object_id": object_id,
            "subject_label": context.object_labels.get(subject_id),
            "object_label": context.object_labels.get(object_id),
            "subject_label_source": "3DSSG_subset",
            "object_label_source": "3DSSG_subset",
            "edge_source": candidate_kind,
        },
        "predicate": {
            "predicate_label": predicate_label,
            "predicate_family": predicate_family(predicate_label),
            "raw_3dssg_predicate_id": raw_id,
            "vlsat_predicate_index": raw_id - 1 if raw_id and raw_id > 0 else None,
            "predicate_vocab": "3DSSG_subset_26_no_none",
        },
        "scores": {
            "predicate_score": 1.0,
            "ranking_score": 1.0,
        },
        "ranks": {},
        "provenance": {"created_at": created_at, "source": candidate_kind},
    }


def positive_candidates(
    ground_truth: list[dict[str, Any]],
    contexts: dict[str, Context],
    relationship_ids: dict[str, int],
    created_at: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for row in ground_truth:
        family = str(row["predicate_family"])
        if family not in PRIMARY_FAMILIES:
            continue
        context = contexts.get(str(row["subgraph_id"]))
        if context is None:
            continue
        label = str(row["predicate_label"])
        subject_id = int(row["subject_id"])
        object_id = int(row["object_id"])
        candidate_id = f"gtpos:hardened:{row['gt_id']}"
        candidates.append(
            {
                "candidate_id": candidate_id,
                "candidate_kind": "gt_positive",
                "expected_geometry_label": "valid",
                "counterfactual_strategy": None,
                "base_gt_id": row["gt_id"],
                "prediction": prediction_like(
                    candidate_id=candidate_id,
                    candidate_kind="gt_positive",
                    context=context,
                    subject_id=subject_id,
                    object_id=object_id,
                    predicate_label=label,
                    raw_id=relationship_ids.get(label),
                    created_at=created_at,
                ),
            }
        )
    return candidates


def far_pair_candidates(
    contexts: dict[str, Context],
    *,
    family: str,
    target_count: int,
    label_targets: dict[str, int] | None,
    relationship_ids: dict[str, int],
    created_at: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    label_targets = label_targets or {}
    label_counts: Counter[str] = Counter()
    seen_pairs: set[tuple[str, int, int, str]] = set()
    for context in sorted(contexts.values(), key=lambda c: (c.scan_id, c.subset_split_id)):
        object_ids = sorted(context.object_labels)
        for subject_id in object_ids:
            for object_id in object_ids:
                if subject_id == object_id:
                    continue
                features, missing_ids = features_for(context, subject_id, object_id)
                if missing_ids or features is None:
                    continue

                if family == "proximity":
                    if frozenset((subject_id, object_id)) in context.proximity_pairs:
                        continue
                    high_margin, _, _ = proximity_margin(features)
                    if not high_margin:
                        continue
                    labels = ("close by",)
                else:
                    if frozenset((subject_id, object_id)) in context.support_pairs:
                        continue
                    high_margin, _, _ = support_margin(features)
                    if not high_margin:
                        continue
                    labels = SUPPORT_LABEL_ORDER

                for label in labels:
                    key = (context.subgraph_id, subject_id, object_id, label)
                    if key in seen_pairs or (subject_id, object_id, label) in context.positive_edges:
                        continue
                    if family == "support_contact":
                        if label_counts[label] >= label_targets.get(label, 0):
                            continue
                        label_counts[label] += 1
                    seen_pairs.add(key)
                    candidate_id = (
                        f"gtneg:hardened:{family}:{context.scan_id}:{context.subset_split_id}:"
                        f"{subject_id}:{object_id}:{label}:{len(candidates) + 1}"
                    )
                    candidates.append(
                        {
                            "candidate_id": candidate_id,
                            "candidate_kind": "gt_counterfactual_negative",
                            "expected_geometry_label": "invalid",
                            "counterfactual_strategy": (
                                "far_nonoverlap_close_by" if family == "proximity" else "far_nonoverlap_support_contact"
                            ),
                            "base_gt_id": None,
                            "prediction": prediction_like(
                                candidate_id=candidate_id,
                                candidate_kind="gt_counterfactual_negative",
                                context=context,
                                subject_id=subject_id,
                                object_id=object_id,
                                predicate_label=label,
                                raw_id=relationship_ids.get(label),
                                created_at=created_at,
                            ),
                        }
                    )
                    if len(candidates) >= target_count:
                        return candidates
                    if family == "proximity":
                        break
    return candidates


def vertical_inverse_candidates(
    positives: list[dict[str, Any]],
    contexts: dict[str, Context],
    relationship_ids: dict[str, int],
    created_at: str,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for positive in positives:
        pred = positive["prediction"]
        label = pred["predicate"]["predicate_label"]
        inverse = RELATIVE_INVERSE.get(label)
        if inverse is None:
            continue
        context = contexts[pred["subgraph_id"]]
        subject_id = int(pred["edge"]["subject_id"])
        object_id = int(pred["edge"]["object_id"])
        if (subject_id, object_id, inverse) in context.positive_edges:
            continue
        candidate_id = f"gtneg:hardened:relative_vertical_inverse:{positive['base_gt_id']}:{inverse}"
        candidates.append(
            {
                "candidate_id": candidate_id,
                "candidate_kind": "gt_counterfactual_negative",
                "expected_geometry_label": "invalid",
                "counterfactual_strategy": "relative_vertical_inverse",
                "base_gt_id": positive["base_gt_id"],
                "prediction": prediction_like(
                    candidate_id=candidate_id,
                    candidate_kind="gt_counterfactual_negative",
                    context=context,
                    subject_id=subject_id,
                    object_id=object_id,
                    predicate_label=inverse,
                    raw_id=relationship_ids.get(inverse),
                    created_at=created_at,
                ),
            }
        )
    return candidates


def collect_support_object_ids(candidates: list[dict[str, Any]]) -> dict[str, set[int]]:
    by_scan: dict[str, set[int]] = defaultdict(set)
    for candidate in candidates:
        pred = candidate["prediction"]
        if pred["predicate"]["predicate_family"] != "support_contact":
            continue
        scan_id = pred["scan_id"]
        by_scan[scan_id].add(int(pred["edge"]["subject_id"]))
        by_scan[scan_id].add(int(pred["edge"]["object_id"]))
    return by_scan


def evaluate_candidates(
    candidates: list[dict[str, Any]],
    contexts: dict[str, Context],
    *,
    dataset_root: Path,
    model: dict[str, Any],
    model_path: Path,
    point_cache_size: int,
    created_at: str,
) -> list[dict[str, Any]]:
    support_object_ids = collect_support_object_ids(candidates)
    point_cache: OrderedDict[str, dict[str, Any]] = OrderedDict()
    rows: list[dict[str, Any]] = []

    for candidate in candidates:
        prediction = candidate["prediction"]
        context = contexts[prediction["subgraph_id"]]
        subject_id = int(prediction["edge"]["subject_id"])
        object_id = int(prediction["edge"]["object_id"])
        features, missing_ids = features_for(context, subject_id, object_id)
        point_context = None
        if prediction["predicate"]["predicate_family"] == "support_contact":
            point_context = load_point_context_cached(
                dataset_root=dataset_root,
                scan_id=context.scan_id,
                scan_object_ids=support_object_ids,
                point_cache=point_cache,
                point_cache_size=point_cache_size,
                point_thresholds=DEFAULT_POINT_THRESHOLDS,
            )
        verification = make_verification_row_g2(
            prediction,
            features=features,
            geometry_available=features is not None,
            missing_ids=missing_ids,
            model=model,
            model_path=model_path,
            created_at=created_at,
            verification_policy="point_subtype",
            point_context=point_context,
            point_thresholds=DEFAULT_POINT_THRESHOLDS,
            v2_thresholds=V2_THRESHOLDS,
        )
        rows.append(
            {
                "schema_version": SCHEMA_VERSION,
                "record_type": "gt_verifier_eval",
                "candidate_id": candidate["candidate_id"],
                "candidate_kind": candidate["candidate_kind"],
                "expected_geometry_label": candidate["expected_geometry_label"],
                "counterfactual_strategy": candidate["counterfactual_strategy"],
                "base_gt_id": candidate["base_gt_id"],
                "scan_id": prediction["scan_id"],
                "subset_split_id": prediction["subset_split_id"],
                "subgraph_id": prediction["subgraph_id"],
                "edge": prediction["edge"],
                "predicate": prediction["predicate"],
                "geometry": verification["geometry"],
                "verification": verification["verification"],
                "verification_status": verification["verification_status"],
                "verification_variants": verification.get("verification_variants"),
                "calibration": verification["calibration"],
                "quality": verification["quality"],
                "provenance": {
                    "evaluator": "evaluate_gt_verifier.py",
                    "joiner_policy": G2_POLICY_NAME,
                    "created_at": created_at,
                },
            }
        )
    return rows


def average_precision(labels: list[int], scores: list[float]) -> float | None:
    positives = sum(labels)
    if positives == 0:
        return None
    order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
    hit = 0
    total = 0.0
    for rank, idx in enumerate(order, start=1):
        if labels[idx]:
            hit += 1
            total += hit / rank
    return total / positives


def auroc(labels: list[int], scores: list[float]) -> float | None:
    positives = sum(labels)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return None
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i + 1
        while j < len(order) and scores[order[j]] == scores[order[i]]:
            j += 1
        avg_rank = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[order[k]] = avg_rank
        i = j
    pos_rank_sum = sum(ranks[i] for i, label in enumerate(labels) if label)
    return (pos_rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def discrimination(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels: list[int] = []
    scores: list[float] = []
    for row in rows:
        score = finite_float(row["calibration"].get("p_geom_valid"))
        if score is None:
            continue
        labels.append(1 if row["expected_geometry_label"] == "valid" else 0)
        scores.append(score)
    if not scores:
        return {"rows": 0, "brier": None, "auroc_valid": None, "auprc_valid": None}
    brier = sum((score - label) ** 2 for label, score in zip(labels, scores)) / len(scores)
    return {
        "rows": len(scores),
        "positives": sum(labels),
        "negatives": len(labels) - sum(labels),
        "brier": brier,
        "auroc_valid": auroc(labels, scores),
        "auprc_valid": average_precision(labels, scores),
        "mean_p_geom_valid": sum(scores) / len(scores),
    }


def summarize_kind(rows: list[dict[str, Any]], kind: str) -> dict[str, Any]:
    scoped = [row for row in rows if row["candidate_kind"] == kind]
    status_counts = Counter(row["verification_status"] for row in scoped)
    p_values = [
        score
        for row in scoped
        if (score := finite_float(row["calibration"].get("p_geom_valid"))) is not None
    ]
    total = len(scoped)
    return {
        "rows": total,
        "status_counts": dict(sorted(status_counts.items())),
        "satisfied_rate": status_counts["satisfied"] / total if total else None,
        "uncertain_rate": status_counts["uncertain"] / total if total else None,
        "violated_rate": status_counts["violated"] / total if total else None,
        "nonviolated_rate": (status_counts["satisfied"] + status_counts["uncertain"]) / total if total else None,
        "nonsatisfied_rate": (total - status_counts["satisfied"]) / total if total else None,
        "p_geom_valid": summarize_values(p_values),
        "p_geom_valid_thresholds": {
            "le_0_1": sum(1 for v in p_values if v <= 0.1) / len(p_values) if p_values else None,
            "le_0_3": sum(1 for v in p_values if v <= 0.3) / len(p_values) if p_values else None,
            "le_0_5": sum(1 for v in p_values if v <= 0.5) / len(p_values) if p_values else None,
            "ge_0_5": sum(1 for v in p_values if v >= 0.5) / len(p_values) if p_values else None,
            "ge_0_7": sum(1 for v in p_values if v >= 0.7) / len(p_values) if p_values else None,
        },
    }


def summarize_by_family(rows: list[dict[str, Any]], kind: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for family in sorted(PRIMARY_FAMILIES):
        family_rows = [
            row for row in rows
            if row["candidate_kind"] == kind and row["predicate"]["predicate_family"] == family
        ]
        result[family] = summarize_kind(family_rows, kind)
    return result


def build_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    positives = [row for row in rows if row["candidate_kind"] == "gt_positive"]
    negatives = [row for row in rows if row["candidate_kind"] == "gt_counterfactual_negative"]
    return {
        "schema_version": "h001_gt_verifier_metrics_v1",
        "status": "ready",
        "counts": {
            "rows": len(rows),
            "gt_positive": len(positives),
            "gt_counterfactual_negative": len(negatives),
            "by_kind_family": {
                kind: dict(sorted(Counter(row["predicate"]["predicate_family"] for row in rows if row["candidate_kind"] == kind).items()))
                for kind in ("gt_positive", "gt_counterfactual_negative")
            },
            "counterfactual_strategy": dict(sorted(Counter(row["counterfactual_strategy"] for row in negatives).items())),
        },
        "gt_positive": summarize_kind(rows, "gt_positive"),
        "gt_positive_by_family": summarize_by_family(rows, "gt_positive"),
        "gt_counterfactual_negative": summarize_kind(rows, "gt_counterfactual_negative"),
        "gt_counterfactual_negative_by_family": summarize_by_family(rows, "gt_counterfactual_negative"),
        "p_geom_valid_discrimination": discrimination(rows),
        "p_geom_valid_discrimination_by_family": {
            family: discrimination([row for row in rows if row["predicate"]["predicate_family"] == family])
            for family in sorted(PRIMARY_FAMILIES)
        },
    }


def fmt(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_report(manifest: dict[str, Any], metrics: dict[str, Any]) -> str:
    lines = [
        "# GT-Based Verifier Evaluation",
        "",
        f"- Date: `{manifest['created_at']}`",
        f"- Status: `{manifest['status']}`",
        f"- Output root: `{manifest['outputs']['output_dir']}`",
        "",
        "## Purpose",
        "",
        "Reduce the burden on qualitative audit by adding GT-positive consistency and GT-derived counterfactual negative checks.",
        "",
        "## Counts",
        "",
        "| Item | Count |",
        "| --- | ---: |",
        f"| GT positives | {metrics['counts']['gt_positive']} |",
        f"| counterfactual negatives | {metrics['counts']['gt_counterfactual_negative']} |",
        f"| total rows | {metrics['counts']['rows']} |",
        "",
        "## Main Summary",
        "",
        "| Split | Rows | Satisfied | Uncertain | Violated | Mean p_geom_valid |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for key, label in (("gt_positive", "GT positive"), ("gt_counterfactual_negative", "GT-derived negative")):
        row = metrics[key]
        lines.append(
            f"| {label} | {row['rows']} | {fmt(row['satisfied_rate'])} | "
            f"{fmt(row['uncertain_rate'])} | {fmt(row['violated_rate'])} | "
            f"{fmt(row['p_geom_valid']['mean'])} |"
        )
    disc = metrics["p_geom_valid_discrimination"]
    lines += [
        "",
        "## p_geom_valid Discrimination",
        "",
        "| Rows | Brier | AUROC valid | AUPRC valid |",
        "| ---: | ---: | ---: | ---: |",
        f"| {disc['rows']} | {fmt(disc['brier'])} | {fmt(disc['auroc_valid'])} | {fmt(disc['auprc_valid'])} |",
        "",
        "## Family Breakdown",
        "",
        "| Family | Positive rows | Positive nonviolated | Negative rows | Negative nonsatisfied | Family AUROC |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for family in sorted(PRIMARY_FAMILIES):
        pos = metrics["gt_positive_by_family"][family]
        neg = metrics["gt_counterfactual_negative_by_family"][family]
        fam_disc = metrics["p_geom_valid_discrimination_by_family"][family]
        lines.append(
            f"| `{family}` | {pos['rows']} | {fmt(pos['nonviolated_rate'])} | "
            f"{neg['rows']} | {fmt(neg['nonsatisfied_rate'])} | {fmt(fam_disc['auroc_valid'])} |"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "Fact:",
        "",
        "- This evaluation uses held-out GT positives and deterministic GT-derived counterfactual negatives.",
        "- It does not replace the 50-row blinded visual spot-check.",
        "",
        "Inference:",
        "",
        "- If positive nonviolated rate and p_geom_valid discrimination are high, qualitative audit can be used as a small sanity check rather than the main evidence.",
        "- Any high GT-positive violated rate should be interpreted as label noise, geometry incompleteness, or verifier over-strictness that needs qualitative review.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    created_at = datetime.now(timezone.utc).isoformat()
    selected_scans = read_selected_scans(args.selected_scans)
    relationship_ids = load_relationship_id_map(args.relationships_file)
    contexts, build_warnings, build_errors = load_contexts(
        subset_json=args.subset_json,
        dataset_root=args.dataset_root,
        selected_scans=selected_scans,
    )
    ground_truth = load_jsonl(args.ground_truth_jsonl)
    model = load_json(args.model_json)

    positives = positive_candidates(ground_truth, contexts, relationship_ids, created_at)
    positive_counts = Counter(c["prediction"]["predicate"]["predicate_family"] for c in positives)
    support_label_targets = Counter(
        c["prediction"]["predicate"]["predicate_label"]
        for c in positives
        if c["prediction"]["predicate"]["predicate_family"] == "support_contact"
    )
    target = {
        family: min(count, args.max_negatives_per_family or count)
        for family, count in positive_counts.items()
    }
    negatives = []
    negatives.extend(vertical_inverse_candidates(positives, contexts, relationship_ids, created_at)[: target.get("relative_vertical", 0)])
    negatives.extend(
        far_pair_candidates(
            contexts,
            family="proximity",
            target_count=target.get("proximity", 0),
            label_targets=None,
            relationship_ids=relationship_ids,
            created_at=created_at,
        )
    )
    negatives.extend(
        far_pair_candidates(
            contexts,
            family="support_contact",
            target_count=target.get("support_contact", 0),
            label_targets=dict(support_label_targets),
            relationship_ids=relationship_ids,
            created_at=created_at,
        )
    )

    positive_rows = evaluate_candidates(
        positives,
        contexts,
        dataset_root=args.dataset_root,
        model=model,
        model_path=args.model_json,
        point_cache_size=args.point_cache_size,
        created_at=created_at,
    )
    negative_rows = evaluate_candidates(
        negatives,
        contexts,
        dataset_root=args.dataset_root,
        model=model,
        model_path=args.model_json,
        point_cache_size=args.point_cache_size,
        created_at=created_at,
    )
    all_rows = positive_rows + negative_rows
    metrics = build_metrics(all_rows)

    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "created_at": "2026-05-06",
        "status": "ready" if not build_errors else "ready_with_context_errors",
        "inputs": {
            "dataset_root": relpath(args.dataset_root),
            "subset_json": relpath(args.subset_json),
            "selected_scans": relpath(args.selected_scans),
            "ground_truth_jsonl": relpath(args.ground_truth_jsonl),
            "model_json": relpath(args.model_json),
        },
        "parameters": {
            "verification_policy": args.verification_policy,
            "point_cache_size": args.point_cache_size,
            "max_negatives_per_family": args.max_negatives_per_family,
            "families": sorted(PRIMARY_FAMILIES),
        },
        "counts": metrics["counts"],
        "warnings": build_warnings,
        "errors": build_errors,
        "outputs": {
            "output_dir": relpath(args.output_dir),
            "gt_positive_jsonl": relpath(args.output_dir / "gt_positive.jsonl"),
            "counterfactuals_jsonl": relpath(args.output_dir / "counterfactuals.jsonl"),
            "metrics_json": relpath(args.output_dir / "metrics.json"),
            "report_md": relpath(args.output_dir / "report.md"),
            "manifest_json": relpath(args.output_dir / "manifest.json"),
        },
        "decision": "Use GT-based quantitative verifier evaluation to reduce, not remove, the need for the 50-row blinded visual spot-check.",
        "next_action": "Keep independent visual labels as a small qualitative sanity check before paper-level audit wording.",
    }

    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_jsonl(args.output_dir / "gt_positive.jsonl", positive_rows)
        write_jsonl(args.output_dir / "counterfactuals.jsonl", negative_rows)
        write_json(args.output_dir / "metrics.json", metrics)
        write_json(args.output_dir / "manifest.json", manifest)
        (args.output_dir / "report.md").write_text(render_report(manifest, metrics), encoding="utf-8")

    print(
        "gt_verifier_eval_ready "
        f"status={manifest['status']} "
        f"positives={metrics['counts']['gt_positive']} "
        f"negatives={metrics['counts']['gt_counterfactual_negative']} "
        f"auroc={fmt(metrics['p_geom_valid_discrimination']['auroc_valid'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
