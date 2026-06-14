#!/usr/bin/env python3
"""Generate the H001 G4 human-audit queue.

The script samples compact, label-ready examples from hardened VL-SAT
prediction rows and their geometry-verification rows. It intentionally does
not assign human labels.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import random
from collections import Counter, defaultdict
from datetime import date
from itertools import zip_longest
from pathlib import Path
from typing import Any

from paths import H001_HYPOTHESIS_ROOT


SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
H001_ROOT = H001_HYPOTHESIS_ROOT
DEFAULT_PREDICTIONS = (
    H001_ROOT
    / "artifacts"
    / "evaluation"
    / "vlsat_closed_set"
    / "hardened"
    / "predictions.jsonl"
)
DEFAULT_VERIFICATION = (
    H001_ROOT
    / "artifacts"
    / "evaluation"
    / "vlsat_closed_set"
    / "hardened_geometry"
    / "verification.jsonl"
)
DEFAULT_OUTPUT_DIR = (
    H001_ROOT
    / "artifacts"
    / "evaluation"
    / "vlsat_closed_set"
    / "hardened"
    / "human_audit"
)
DEFAULT_STAGED_SCAN_ROOT = (
    REPO_ROOT
    / "local_dataset"
    / "VLSAT_staged"
    / "h001_validation_hardened"
    / "CVPR2023-VLSAT"
    / "data"
    / "3RScan"
)
DEFAULT_SOURCE_SCAN_ROOT = REPO_ROOT / "local_dataset" / "3RScan" / "scans"
DEFAULT_FAMILIES = ("support_contact", "proximity", "relative_vertical")
DEFAULT_LABELS = (
    "valid_relation",
    "invalid_relation",
    "ambiguous",
    "annotation_noise",
    "scan_geometry_missing",
    "verifier_error",
    "semantic_label_too_coarse",
)
BUCKETS = (
    "semantic_topk_violated",
    "probabilistic_reranked_away",
    "rule_verified_removed",
    "uncertain_support_contact",
    "family_balanced_random_in_scope",
)
GEOMETRY_FEATURES = (
    "distance_3d",
    "distance_xy",
    "normalized_distance_3d",
    "normalized_distance_xy",
    "center_delta_z",
    "normalized_center_delta_z",
    "projected_iou_xy",
    "projected_subject_overlap_ratio",
    "projected_object_overlap_ratio",
    "vertical_gap_subject_on_object",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate H001 G4 human-audit samples.")
    parser.add_argument("--predictions-jsonl", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--verification-jsonl", type=Path, default=DEFAULT_VERIFICATION)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--staged-scan-root", type=Path, default=DEFAULT_STAGED_SCAN_ROOT)
    parser.add_argument("--source-scan-root", type=Path, default=DEFAULT_SOURCE_SCAN_ROOT)
    parser.add_argument("--families", nargs="+", default=list(DEFAULT_FAMILIES))
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--candidate-k", type=int, default=100)
    parser.add_argument("--samples-per-bucket", type=int, default=50)
    parser.add_argument("--seed", type=int, default=1701)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def relpath(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def load_json_line(line: str, path: Path, line_no: int) -> dict[str, Any]:
    try:
        return json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSONL at {path}:{line_no}") from exc


def write_json(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            f.write("\n")


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


def semantic_score(row: dict[str, Any]) -> float | None:
    scores = row.get("scores") or {}
    score = finite_float(scores.get("ranking_score"))
    if score is None:
        score = finite_float(scores.get("predicate_score"))
    return score


def p_geom_valid(row: dict[str, Any]) -> float | None:
    return finite_float((row.get("calibration") or {}).get("p_geom_valid"))


def compact_features(row: dict[str, Any]) -> dict[str, float]:
    source = ((row.get("geometry") or {}).get("features") or {})
    output: dict[str, float] = {}
    for key in GEOMETRY_FEATURES:
        value = finite_float(source.get(key))
        if value is not None:
            output[key] = value
    return output


def scan_assets(scan_id: str, staged_root: Path, source_root: Path) -> dict[str, Any]:
    staged_dir = staged_root / scan_id
    source_dir = source_root / scan_id
    candidates = {
        "staged_scan_dir": staged_dir,
        "source_scan_dir": source_dir,
        "aligned_ply": source_dir / "labels.instances.align.annotated.v2.ply",
        "annotated_ply": source_dir / "labels.instances.annotated.v2.ply",
        "semseg": source_dir / "semseg.v2.json",
        "segments": source_dir / "mesh.refined.0.010000.segs.v2.json",
        "sequence_zip": source_dir / "sequence.zip",
        "multi_view_dir": staged_dir / "multi_view",
    }
    return {
        name: relpath(path)
        for name, path in candidates.items()
        if path.exists() or name.endswith("_dir")
    }


def compact_candidate(
    prediction: dict[str, Any],
    verification: dict[str, Any],
    staged_root: Path,
    source_root: Path,
) -> dict[str, Any]:
    score = semantic_score(prediction)
    p_valid = p_geom_valid(verification)
    probabilistic_score = score * p_valid if score is not None and p_valid is not None else None
    verification_block = verification.get("verification") or {}
    edge = prediction.get("edge") or {}
    predicate = prediction.get("predicate") or {}
    ranks = prediction.get("ranks") or {}
    scan_id = prediction["scan_id"]
    return {
        "prediction_id": prediction["prediction_id"],
        "scan_id": scan_id,
        "subgraph_id": prediction["subgraph_id"],
        "subset_split_id": int(prediction["subset_split_id"]),
        "edge": {
            "subject_id": edge.get("subject_id"),
            "subject_label": edge.get("subject_label"),
            "object_id": edge.get("object_id"),
            "object_label": edge.get("object_label"),
        },
        "predicate": {
            "predicate_label": predicate.get("predicate_label"),
            "predicate_family": predicate.get("predicate_family"),
        },
        "semantic": {
            "ranking_score": score,
            "predicate_score": finite_float((prediction.get("scores") or {}).get("predicate_score")),
            "semantic_rank_in_subgraph": ranks.get("semantic_rank_in_subgraph"),
            "predicate_rank_for_pair": ranks.get("predicate_rank_for_pair"),
        },
        "calibration": {
            "p_geom_valid": p_valid,
            "p_geom_invalid": finite_float((verification.get("calibration") or {}).get("p_geom_invalid")),
            "p_final_product": finite_float((verification.get("calibration") or {}).get("p_final_product")),
            "probabilistic_score": probabilistic_score,
        },
        "verification": {
            "verification_status": verification.get("verification_status"),
            "consistency_score": finite_float(verification.get("consistency_score")),
            "reason_codes": list(verification_block.get("reason_codes") or []),
            "geometry_source": verification_block.get("geometry_source"),
            "support_subtype": verification_block.get("support_subtype"),
            "subtype_reason_codes": list(verification_block.get("subtype_reason_codes") or []),
            "point_evidence_available": verification_block.get("point_evidence_available"),
            "support_points_under_subject_count": verification_block.get(
                "support_points_under_subject_count"
            ),
            "subject_point_count": verification_block.get("subject_point_count"),
            "object_point_count": verification_block.get("object_point_count"),
        },
        "geometry_features": compact_features(verification),
        "quality": verification.get("quality") or {},
        "scene_assets": scan_assets(scan_id, staged_root, source_root),
    }


def heap_push(
    grouped: dict[str, list[tuple[float, int, str, dict[str, Any]]]],
    group_key: str,
    score: float | None,
    rank: Any,
    record: dict[str, Any],
    limit: int,
) -> None:
    if score is None:
        return
    try:
        rank_value = int(rank)
    except (TypeError, ValueError):
        rank_value = 10**9
    item = (score, -rank_value, record["prediction_id"], record)
    heap = grouped[group_key]
    if len(heap) < limit:
        heapq.heappush(heap, item)
    elif item > heap[0]:
        heapq.heapreplace(heap, item)


def top_records(
    grouped: dict[str, list[tuple[float, int, str, dict[str, Any]]]],
    limit: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for heap in grouped.values():
        rows.extend(item[3] for item in sorted(heap, reverse=True)[:limit])
    return rows


def dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        prediction_id = row["prediction_id"]
        if prediction_id in seen:
            continue
        seen.add(prediction_id)
        output.append(row)
    return output


def sample_id(bucket: str, index: int, prediction_id: str) -> str:
    suffix = hashlib.sha1(prediction_id.encode("utf-8")).hexdigest()[:10]
    return f"{bucket}:{index:03d}:{suffix}"


def sort_priority(row: dict[str, Any]) -> tuple[float, float, str]:
    semantic = finite_float(row["semantic"].get("ranking_score")) or 0.0
    p_valid = finite_float(row["calibration"].get("p_geom_valid"))
    invalid_weight = 1.0 - p_valid if p_valid is not None else 0.0
    return (semantic * (1.0 + invalid_weight), semantic, row["prediction_id"])


def select_bucket(
    bucket: str,
    candidates: list[dict[str, Any]],
    count: int,
    families: list[str],
    seed: int,
    used_ids: set[str],
    family_balanced: bool = True,
    randomize: bool = False,
) -> list[dict[str, Any]]:
    rng = random.Random(f"{seed}:{bucket}")
    unique = dedupe(candidates)
    eligible = [row for row in unique if row["prediction_id"] not in used_ids]
    fallback = [row for row in unique if row["prediction_id"] in used_ids]

    def ordered(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = list(rows)
        if randomize:
            rng.shuffle(rows)
            return rows
        rows.sort(key=sort_priority, reverse=True)
        return rows

    selected: list[dict[str, Any]] = []
    if family_balanced:
        by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in eligible:
            by_family[row["predicate"]["predicate_family"]].append(row)
        active_families = [family for family in families if by_family.get(family)]
        if active_families:
            base = count // len(active_families)
            extra = count % len(active_families)
            for index, family in enumerate(active_families):
                quota = base + (1 if index < extra else 0)
                selected.extend(ordered(by_family[family])[:quota])
    else:
        selected.extend(ordered(eligible)[:count])

    selected_ids = {row["prediction_id"] for row in selected}
    if len(selected) < count:
        remaining = [
            row
            for row in ordered(eligible)
            if row["prediction_id"] not in selected_ids
        ]
        selected.extend(remaining[: count - len(selected)])
        selected_ids = {row["prediction_id"] for row in selected}
    if len(selected) < count:
        duplicate_fill = [
            row
            for row in ordered(fallback)
            if row["prediction_id"] not in selected_ids
        ]
        selected.extend(duplicate_fill[: count - len(selected)])
    return selected[:count]


def attach_sample_metadata(
    bucket: str,
    rows: list[dict[str, Any]],
    used_before_bucket: set[str],
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    output = []
    for index, row in enumerate(rows, 1):
        prediction_id = row["prediction_id"]
        annotated = {
            "schema_version": "h001_human_audit_sample_v1",
            "sample_id": sample_id(bucket, index, prediction_id),
            "bucket": bucket,
            "audit_status": "unlabeled",
            "duplicate_case": prediction_id in used_before_bucket,
            "selection_context": {
                "top_k": args.top_k,
                "candidate_k": args.candidate_k,
                "samples_per_bucket": args.samples_per_bucket,
                "seed": args.seed,
                "selected_policy": "deterministic_family_balanced_sample",
            },
            "allowed_human_labels": list(DEFAULT_LABELS),
        }
        annotated.update(row)
        output.append(annotated)
    return output


def labels_from_samples(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labels = []
    for sample in samples:
        labels.append(
            {
                "schema_version": "h001_human_audit_label_v1",
                "sample_id": sample["sample_id"],
                "prediction_id": sample["prediction_id"],
                "bucket": sample["bucket"],
                "scan_id": sample["scan_id"],
                "predicate_family": sample["predicate"]["predicate_family"],
                "predicate_label": sample["predicate"]["predicate_label"],
                "audit_status": "unlabeled",
                "human_label": None,
                "relation_visible": None,
                "geometry_sufficient": None,
                "verifier_decision_correct": None,
                "figure_candidate": None,
                "reviewer_id": None,
                "reviewed_at": None,
                "notes": None,
                "allowed_human_labels": list(DEFAULT_LABELS),
            }
        )
    return labels


def summarize_bucket(rows: list[dict[str, Any]], available_count: int) -> dict[str, Any]:
    return {
        "available": available_count,
        "selected": len(rows),
        "duplicate_cases": sum(1 for row in rows if row.get("duplicate_case")),
        "by_family": dict(
            sorted(Counter(row["predicate"]["predicate_family"] for row in rows).items())
        ),
        "by_status": dict(
            sorted(Counter(row["verification"]["verification_status"] for row in rows).items())
        ),
    }


def make_report(manifest: dict[str, Any], summary: dict[str, Any]) -> str:
    lines = [
        "# Human Audit Queue",
        "",
        f"Created at: `{manifest['created_at']}`",
        f"Status: `{manifest['status']}`",
        f"Families: `{', '.join(manifest['families'])}`",
        f"Top-k audit cutoff: `{manifest['parameters']['top_k']}`",
        f"Candidate cutoff: `{manifest['parameters']['candidate_k']}`",
        "",
        "## Buckets",
        "",
        "| Bucket | Available | Selected | Duplicates | Family counts | Status counts |",
        "| --- | ---: | ---: | ---: | --- | --- |",
    ]
    for bucket in BUCKETS:
        data = summary["buckets"][bucket]
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{bucket}`",
                    str(data["available"]),
                    str(data["selected"]),
                    str(data["duplicate_cases"]),
                    f"`{data['by_family']}`",
                    f"`{data['by_status']}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Label Schema",
            "",
            "Allowed `human_label` values:",
            "",
        ]
    )
    for label in DEFAULT_LABELS:
        lines.append(f"- `{label}`")
    lines.extend(
        [
            "",
            "The generated `labels.jsonl` is intentionally unlabeled. Human reviewers",
            "should fill `human_label`, visibility/sufficiency fields, and notes before",
            "any G4 pass/fail claim is made.",
            "",
            "## Outputs",
            "",
        ]
    )
    for name, path in manifest["outputs"].items():
        lines.append(f"- {name}: `{path}`")
    if manifest.get("errors"):
        lines.extend(["", "## Errors", ""])
        for error in manifest["errors"]:
            lines.append(f"- `{error}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    if args.candidate_k < args.top_k:
        errors.append("candidate_k_must_be_at_least_top_k")
    for name, path in {
        "predictions_jsonl": args.predictions_jsonl,
        "verification_jsonl": args.verification_jsonl,
    }.items():
        if not path.exists():
            errors.append(f"missing_input:{name}:{relpath(path)}")
    if errors:
        print(json.dumps({"status": "blocked", "errors": errors}, sort_keys=True))
        return 2

    families = list(args.families)
    family_set = set(families)
    semantic_heaps: dict[str, list[tuple[float, int, str, dict[str, Any]]]] = defaultdict(list)
    probabilistic_heaps: dict[str, list[tuple[float, int, str, dict[str, Any]]]] = defaultdict(list)
    counts: Counter[str] = Counter()
    by_family_status: Counter[tuple[str, str]] = Counter()

    with args.predictions_jsonl.open("r", encoding="utf-8") as pred_file, args.verification_jsonl.open(
        "r", encoding="utf-8"
    ) as ver_file:
        for line_no, pair in enumerate(zip_longest(pred_file, ver_file), 1):
            pred_line, ver_line = pair
            if pred_line is None or ver_line is None:
                errors.append("prediction_verification_row_count_mismatch")
                break
            prediction = load_json_line(pred_line, args.predictions_jsonl, line_no)
            verification = load_json_line(ver_line, args.verification_jsonl, line_no)
            if prediction["prediction_id"] != verification["prediction_id"]:
                errors.append(f"prediction_verification_id_mismatch:{line_no}")
                break
            family = prediction["predicate"]["predicate_family"]
            counts["prediction_rows"] += 1
            if family not in family_set:
                continue
            counts["in_scope_rows"] += 1
            status = str(verification.get("verification_status"))
            by_family_status[(family, status)] += 1
            record = compact_candidate(
                prediction,
                verification,
                args.staged_scan_root,
                args.source_scan_root,
            )
            rank = record["semantic"].get("semantic_rank_in_subgraph")
            heap_push(
                semantic_heaps,
                record["subgraph_id"],
                record["semantic"].get("ranking_score"),
                rank,
                record,
                args.candidate_k,
            )
            heap_push(
                probabilistic_heaps,
                record["subgraph_id"],
                record["calibration"].get("probabilistic_score"),
                rank,
                record,
                args.candidate_k,
            )

    semantic_top = top_records(semantic_heaps, args.top_k)
    semantic_candidates = top_records(semantic_heaps, args.candidate_k)
    probabilistic_top = top_records(probabilistic_heaps, args.top_k)
    probabilistic_candidates = top_records(probabilistic_heaps, args.candidate_k)
    probabilistic_top_ids = {row["prediction_id"] for row in probabilistic_top}
    probabilistic_candidate_ids = {row["prediction_id"] for row in probabilistic_candidates}

    bucket_candidates = {
        "semantic_topk_violated": [
            row
            for row in semantic_top
            if row["verification"]["verification_status"] == "violated"
        ],
        "probabilistic_reranked_away": [
            row
            for row in semantic_top
            if row["verification"]["verification_status"] == "violated"
            and row["prediction_id"] not in probabilistic_top_ids
        ]
        + [
            row
            for row in semantic_candidates
            if row["verification"]["verification_status"] == "violated"
            and row["prediction_id"] not in probabilistic_candidate_ids
        ],
        "rule_verified_removed": [
            row
            for row in semantic_candidates
            if row["verification"]["verification_status"] == "violated"
        ],
        "uncertain_support_contact": [
            row
            for row in semantic_candidates
            if row["predicate"]["predicate_family"] == "support_contact"
            and row["verification"]["verification_status"] == "uncertain"
        ],
        "family_balanced_random_in_scope": semantic_candidates,
    }

    samples: list[dict[str, Any]] = []
    selected_case_ids: set[str] = set()
    bucket_rows: dict[str, list[dict[str, Any]]] = {}
    for bucket in BUCKETS:
        selected = select_bucket(
            bucket,
            bucket_candidates[bucket],
            args.samples_per_bucket,
            families,
            args.seed,
            selected_case_ids,
            family_balanced=bucket != "uncertain_support_contact",
            randomize=bucket == "family_balanced_random_in_scope",
        )
        used_before = set(selected_case_ids)
        selected_case_ids.update(row["prediction_id"] for row in selected)
        annotated = attach_sample_metadata(bucket, selected, used_before, args)
        bucket_rows[bucket] = annotated
        samples.extend(annotated)

    labels = labels_from_samples(samples)
    figure_candidates = [
        row
        for row in samples
        if row["bucket"]
        in {
            "semantic_topk_violated",
            "probabilistic_reranked_away",
            "uncertain_support_contact",
        }
    ][:24]

    summary = {
        "schema_version": "h001_human_audit_summary_v1",
        "counts": {
            "prediction_rows": counts["prediction_rows"],
            "in_scope_rows": counts["in_scope_rows"],
            "semantic_top_records": len(semantic_top),
            "semantic_candidate_records": len(semantic_candidates),
            "probabilistic_top_records": len(probabilistic_top),
            "probabilistic_candidate_records": len(probabilistic_candidates),
            "sample_rows": len(samples),
            "unique_prediction_ids": len({row["prediction_id"] for row in samples}),
        },
        "in_scope_by_family_status": {
            family: {
                status: by_family_status.get((family, status), 0)
                for status in ("satisfied", "uncertain", "violated")
            }
            for family in families
        },
        "buckets": {
            bucket: summarize_bucket(bucket_rows[bucket], len(dedupe(bucket_candidates[bucket])))
            for bucket in BUCKETS
        },
    }
    ready = all(
        summary["buckets"][bucket]["selected"] >= args.samples_per_bucket for bucket in BUCKETS
    )
    status = "ready" if ready and not errors else "partial_ready"
    manifest = {
        "schema_version": "h001_human_audit_manifest_v1",
        "created_at": date.today().isoformat(),
        "status": status,
        "families": families,
        "inputs": {
            "predictions_jsonl": relpath(args.predictions_jsonl),
            "verification_jsonl": relpath(args.verification_jsonl),
            "staged_scan_root": relpath(args.staged_scan_root),
            "source_scan_root": relpath(args.source_scan_root),
        },
        "parameters": {
            "top_k": args.top_k,
            "candidate_k": args.candidate_k,
            "samples_per_bucket": args.samples_per_bucket,
            "seed": args.seed,
            "bucket_order": list(BUCKETS),
        },
        "outputs": {
            "manifest_json": relpath(args.output_dir / "manifest.json"),
            "summary_json": relpath(args.output_dir / "summary.json"),
            "samples_jsonl": relpath(args.output_dir / "samples.jsonl"),
            "labels_jsonl": relpath(args.output_dir / "labels.jsonl"),
            "figure_candidates_jsonl": relpath(args.output_dir / "figure_candidates.jsonl"),
            "report_md": relpath(args.output_dir / "report.md"),
        },
        "notes": [
            "Generated labels are unlabeled templates; G4 is not passed until human labels are filled and summarized.",
            "Samples minimize duplicate prediction ids across buckets; duplicates are marked when fallback was needed.",
        ],
        "errors": errors,
    }

    if not args.dry_run:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        write_json(args.output_dir / "manifest.json", manifest)
        write_json(args.output_dir / "summary.json", summary)
        write_jsonl(args.output_dir / "samples.jsonl", samples)
        write_jsonl(args.output_dir / "labels.jsonl", labels)
        write_jsonl(args.output_dir / "figure_candidates.jsonl", figure_candidates)
        (args.output_dir / "report.md").write_text(
            make_report(manifest, summary), encoding="utf-8"
        )

    print(
        json.dumps(
            {
                "status": status,
                "dry_run": args.dry_run,
                "sample_rows": len(samples),
                "unique_prediction_ids": summary["counts"]["unique_prediction_ids"],
                "buckets_ready": {
                    bucket: summary["buckets"][bucket]["selected"]
                    for bucket in BUCKETS
                },
                "output_dir": relpath(args.output_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if status == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
