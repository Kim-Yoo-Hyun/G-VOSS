#!/usr/bin/env python3
"""Plan the independent visual spot-check for H001 final evidence lock."""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


SCRIPT_PATH = Path(__file__).resolve()
H001_ROOT = SCRIPT_PATH.parents[1]
REPO_ROOT = SCRIPT_PATH.parents[4]
DEFAULT_INPUT_DIR = (
    H001_ROOT
    / "artifacts"
    / "evaluation"
    / "vlsat_closed_set"
    / "hardened"
    / "human_audit"
)
DEFAULT_OUTPUT_DIR = DEFAULT_INPUT_DIR / "visual_spotcheck"
DEFAULT_SAMPLES = DEFAULT_INPUT_DIR / "samples.jsonl"
DEFAULT_STRUCTURED_LABELS = DEFAULT_INPUT_DIR / "labels.jsonl"
BUCKETS = (
    "semantic_topk_violated",
    "probabilistic_reranked_away",
    "rule_verified_removed",
    "uncertain_support_contact",
    "family_balanced_random_in_scope",
)
VISUAL_LABELS = (
    "valid_relation",
    "invalid_relation",
    "ambiguous",
    "annotation_noise",
    "scan_geometry_missing",
    "verifier_error",
    "semantic_label_too_coarse",
)
QUALITY_ISSUE_LABELS = (
    "invalid_relation",
    "semantic_label_too_coarse",
    "annotation_noise",
    "scan_geometry_missing",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-jsonl", type=Path, default=DEFAULT_SAMPLES)
    parser.add_argument("--structured-labels-jsonl", type=Path, default=DEFAULT_STRUCTURED_LABELS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--samples-per-bucket", type=int, default=10)
    parser.add_argument("--seed", type=int, default=240506)
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSONL at {path}:{line_no}") from exc
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def round_robin_by_family(rows: list[dict[str, Any]], count: int, rng: random.Random) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["predicate"]["predicate_family"]].append(row)
    for group_rows in grouped.values():
        group_rows.sort(key=lambda item: item["sample_id"])
        rng.shuffle(group_rows)
    selected: list[dict[str, Any]] = []
    families = sorted(grouped)
    while len(selected) < count and any(grouped.values()):
        for family in families:
            if grouped[family] and len(selected) < count:
                selected.append(grouped[family].pop(0))
    return selected


def select_rows(samples: list[dict[str, Any]], samples_per_bucket: int, seed: int) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    used_prediction_ids: set[str] = set()
    for bucket in BUCKETS:
        bucket_rows = [
            row
            for row in samples
            if row.get("bucket") == bucket and row.get("prediction_id") not in used_prediction_ids
        ]
        bucket_rows.sort(key=lambda item: item["sample_id"])
        chosen = round_robin_by_family(bucket_rows, samples_per_bucket, rng)
        for row in chosen:
            selected.append(row)
            used_prediction_ids.add(row["prediction_id"])
    return selected


def public_queue_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    edge = row["edge"]
    predicate = row["predicate"]
    return {
        "schema_version": "h001_visual_spotcheck_queue_v1",
        "spotcheck_id": f"visual_spotcheck:{index:03d}",
        "source_sample_id": row["sample_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subset_split_id": row["subset_split_id"],
        "relation": {
            "subject_id": edge.get("subject_id"),
            "subject_label": edge.get("subject_label"),
            "predicate_label": predicate.get("predicate_label"),
            "predicate_family": predicate.get("predicate_family"),
            "object_id": edge.get("object_id"),
            "object_label": edge.get("object_label"),
        },
        "scene_assets": row.get("scene_assets", {}),
        "review_task": (
            "Inspect the 3D scan assets and judge whether the relation is visually valid, "
            "invalid, ambiguous, annotation-noisy, geometry-missing, a verifier error, or too coarse."
        ),
        "blinding": "No Codex structured label, verifier status, bucket, score, or calibration field is included.",
    }


def reference_row(
    queue_row: dict[str, Any],
    sample: dict[str, Any],
    structured_labels: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    label = structured_labels.get(sample["sample_id"], {})
    return {
        "schema_version": "h001_visual_spotcheck_reference_v1",
        "spotcheck_id": queue_row["spotcheck_id"],
        "source_sample_id": sample["sample_id"],
        "prediction_id": sample["prediction_id"],
        "bucket": sample.get("bucket"),
        "predicate_family": sample["predicate"]["predicate_family"],
        "verification_status": sample["verification"]["verification_status"],
        "reason_codes": sample["verification"].get("reason_codes", []),
        "codex_structured_label": label.get("human_label"),
        "codex_verifier_decision_correct": label.get("verifier_decision_correct"),
        "codex_audit_source": label.get("audit_source"),
        "p_geom_valid": sample.get("calibration", {}).get("p_geom_valid"),
        "semantic_rank_in_subgraph": sample.get("semantic", {}).get("semantic_rank_in_subgraph"),
    }


def label_template_row(queue_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "h001_visual_spotcheck_label_v1",
        "spotcheck_id": queue_row["spotcheck_id"],
        "source_sample_id": queue_row["source_sample_id"],
        "audit_source": "independent_human_visual_review",
        "audit_status": "unlabeled",
        "allowed_visual_labels": list(VISUAL_LABELS),
        "visual_label": None,
        "relation_visible": None,
        "geometry_sufficient": None,
        "verifier_decision_correct": None,
        "figure_candidate": None,
        "reviewer_id": "",
        "reviewed_at": "",
        "notes": "",
    }


def write_report(path: Path, manifest: dict[str, Any]) -> None:
    lines = [
        "# Independent Visual Spot-Check Plan",
        "",
        f"Date: `{manifest['date_created']}`",
        f"Status: `{manifest['status']}`",
        "",
        "## Purpose",
        "",
        "Create a blinded, non-Codex visual review queue for final H001 evidence lock.",
        "This does not complete the independent human audit; it prepares the queue and labels template.",
        "",
        "## Files",
        "",
        "- `queue.jsonl`: blinded reviewer queue.",
        "- `labels.jsonl`: empty independent human label template.",
        "- `reference.jsonl`: private join file containing bucket, verifier, and Codex structured labels.",
        "- `manifest.json`: count and blocker summary.",
        "",
        "## Selection",
        "",
        f"- Input samples: `{manifest['inputs']['samples_jsonl']}`",
        f"- Structured labels used only for private reference: `{manifest['inputs']['structured_labels_jsonl']}`",
        f"- Samples per bucket: `{manifest['selection']['samples_per_bucket']}`",
        f"- Total selected rows: `{manifest['counts']['selected_rows']}`",
        f"- Unique scans: `{manifest['counts']['unique_scans']}`",
        "",
        "Bucket counts:",
        "",
    ]
    lines.extend(f"- `{key}`: {value}" for key, value in manifest["counts"]["by_bucket"].items())
    lines.extend(
        [
            "",
            "Family counts:",
            "",
        ]
    )
    lines.extend(f"- `{key}`: {value}" for key, value in manifest["counts"]["by_family"].items())
    lines.extend(
        [
            "",
            "## Acceptance",
            "",
            "- All selected rows should be labeled by a non-Codex reviewer before final paper-level audit claims.",
            "- The reviewer queue is blinded to verifier status, scores, buckets, and Codex structured labels.",
            f"- Quality-issue labels are: `{list(QUALITY_ISSUE_LABELS)}`.",
            "- If the independent labels contradict the structured audit, keep the caveat and do not claim audit pass.",
            "",
            "## Blockers",
            "",
        ]
    )
    lines.extend(f"- `{blocker}`" for blocker in manifest["blockers"])
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    samples = read_jsonl(args.samples_jsonl)
    structured_label_rows = read_jsonl(args.structured_labels_jsonl)
    structured_labels = {row["sample_id"]: row for row in structured_label_rows}
    selected = select_rows(samples, args.samples_per_bucket, args.seed)

    queue_rows = [public_queue_row(row, index) for index, row in enumerate(selected, start=1)]
    reference_rows = [
        reference_row(queue_row, sample, structured_labels)
        for queue_row, sample in zip(queue_rows, selected, strict=True)
    ]
    label_rows = [label_template_row(row) for row in queue_rows]

    by_bucket = Counter(row["bucket"] for row in selected)
    by_family = Counter(row["predicate"]["predicate_family"] for row in selected)
    by_structured_label = Counter(row.get("codex_structured_label") for row in reference_rows)
    unique_scans = {row["scan_id"] for row in selected}
    blockers = [f"independent_labels_missing:0/{len(label_rows)}"]

    manifest = {
        "schema_version": "h001_visual_spotcheck_plan_v1",
        "date_created": date.today().isoformat(),
        "status": "planned_unlabeled",
        "decision": "Use a blinded 50-row independent human visual spot-check before final paper-level audit claims.",
        "inputs": {
            "samples_jsonl": str(args.samples_jsonl),
            "structured_labels_jsonl": str(args.structured_labels_jsonl),
        },
        "outputs": {
            "queue_jsonl": str(args.output_dir / "queue.jsonl"),
            "labels_jsonl": str(args.output_dir / "labels.jsonl"),
            "reference_jsonl": str(args.output_dir / "reference.jsonl"),
            "manifest_json": str(args.output_dir / "manifest.json"),
            "report_md": str(args.output_dir / "report.md"),
        },
        "selection": {
            "seed": args.seed,
            "samples_per_bucket": args.samples_per_bucket,
            "buckets": list(BUCKETS),
            "policy": "deterministic_round_robin_by_bucket_and_family",
            "blind_queue": True,
        },
        "label_schema": {
            "allowed_visual_labels": list(VISUAL_LABELS),
            "quality_issue_labels": list(QUALITY_ISSUE_LABELS),
            "required_reviewer": "non-Codex human reviewer",
        },
        "counts": {
            "input_samples": len(samples),
            "selected_rows": len(selected),
            "label_template_rows": len(label_rows),
            "unique_prediction_ids": len({row["prediction_id"] for row in selected}),
            "unique_scans": len(unique_scans),
            "by_bucket": dict(sorted(by_bucket.items())),
            "by_family": dict(sorted(by_family.items())),
            "by_codex_structured_label_private_reference": {
                str(key): value for key, value in sorted(by_structured_label.items(), key=lambda item: str(item[0]))
            },
        },
        "blockers": blockers,
        "next_action": "Have a non-Codex reviewer fill labels.jsonl, then summarize agreement against reference.jsonl.",
    }

    write_jsonl(args.output_dir / "queue.jsonl", queue_rows)
    write_jsonl(args.output_dir / "reference.jsonl", reference_rows)
    write_jsonl(args.output_dir / "labels.jsonl", label_rows)
    write_json(args.output_dir / "manifest.json", manifest)
    write_report(args.output_dir / "report.md", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
