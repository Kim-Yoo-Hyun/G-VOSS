#!/usr/bin/env python3
"""Freeze a blinded, probability-sampled physical-validity audit for H001.

The public review sheets expose relation text and raw visual/point evidence but
never source identity, ranks, scores, verifier outputs, or sampling strata.  A
private sidecar keeps those fields and the inclusion probabilities required for
design-weighted Human Violation@K estimates.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import Image, ImageDraw


SCHEMA_VERSION = "h001_physical_validity_audit_v1"
FAMILIES = ("support_contact", "proximity", "relative_vertical")
KS = (5, 10, 20, 50, 100)
CONDITIONS = ("semantic_only", "family_conditional_risk")
RANKING_CONTEXTS = ("global_in_scope", "within_family")
LABELS = ("physically_valid", "physically_invalid", "ambiguous", "unobservable")
CONFIDENCE = ("high", "medium", "low")
REASON_CODES = (
    "contact_or_support_missing",
    "distance_inconsistent",
    "vertical_order_inconsistent",
    "predicate_semantically_underspecified",
    "segmentation_or_reconstruction_issue",
    "occlusion_or_insufficient_evidence",
    "other",
)

SOURCE_SPECS = {
    "vlsat_closed_set": {
        "predictions": "experiments/H001_geom_reliability/sources/vlsat/full_validation/adapter/predictions.jsonl",
        "verification": "experiments/H001_geom_reliability/sources/vlsat/full_validation/geometry/verification.jsonl",
    },
    "open3dsg_ov_recovery": {
        "predictions": "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/adapter/predictions.jsonl",
        "verification": "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/geometry/verification.jsonl",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/physical_validity_audit/frozen_v1"),
    )
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=Path("local_dataset/h001_physical_validity_audit/frozen_v1/evidence"),
    )
    parser.add_argument("--quota-per-stratum", type=int, default=4)
    parser.add_argument("--seed", type=int, default=20260710)
    parser.add_argument("--max-points-per-object", type=int, default=1800)
    parser.add_argument("--skip-evidence", action="store_true")
    return parser.parse_args()


def resolve(root: Path, path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


def stable_hash(value: str, length: int = 20) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["audit_id"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_eval_module(repo_root: Path) -> Any:
    path = repo_root / "src/geocalib/evaluate_predictions.py"
    spec = importlib.util.spec_from_file_location("h001_eval", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot_import:{path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def item_key(row: dict[str, Any]) -> str:
    edge = row["edge"]
    return ":".join(
        [
            row["scan_id"],
            str(row["subset_split_id"]),
            str(edge["subject_id"]),
            str(edge["object_id"]),
            row["predicate"]["predicate_label"],
        ]
    )


def iter_source_rows(
    repo_root: Path,
    source: str,
    spec: dict[str, str],
    evalmod: Any,
    family_model: dict[str, Any],
) -> list[dict[str, Any]]:
    prediction_path = resolve(repo_root, spec["predictions"])
    verification_path = resolve(repo_root, spec["verification"])
    rows: list[dict[str, Any]] = []
    count = 0
    with prediction_path.open("r", encoding="utf-8") as pred_handle, verification_path.open(
        "r", encoding="utf-8"
    ) as ver_handle:
        for line_no, (pred_line, ver_line) in enumerate(zip(pred_handle, ver_handle), 1):
            if not pred_line.strip() or not ver_line.strip():
                raise ValueError(f"blank_or_unaligned_jsonl:{source}:{line_no}")
            pred = json.loads(pred_line)
            ver_raw = json.loads(ver_line)
            count += 1
            if pred["prediction_id"] != ver_raw["prediction_id"]:
                raise ValueError(f"prediction_verification_mismatch:{source}:{line_no}")
            family = pred["predicate"]["predicate_family"]
            if family not in FAMILIES:
                continue
            compact = evalmod.compact_verification(ver_raw)
            semantic = evalmod.semantic_score(pred)
            p_family = evalmod.family_specific_p_geom_valid(pred, compact, family_model)
            if semantic is None or p_family is None:
                raise ValueError(f"missing_audit_score:{source}:{pred['prediction_id']}")
            edge = pred["edge"]
            rows.append(
                {
                    "item_key": item_key(pred),
                    "source": source,
                    "prediction_id": pred["prediction_id"],
                    "scan_id": pred["scan_id"],
                    "subgraph_id": pred["subgraph_id"],
                    "subset_split_id": int(pred["subset_split_id"]),
                    "subject_id": int(edge["subject_id"]),
                    "subject_label": edge.get("subject_label", "unknown"),
                    "object_id": int(edge["object_id"]),
                    "object_label": edge.get("object_label", "unknown"),
                    "predicate_label": pred["predicate"]["predicate_label"],
                    "predicate_family": family,
                    "semantic_score": float(semantic),
                    "p_geom_valid_family": float(p_family),
                    "family_conditional_risk": float(semantic) * float(p_family),
                    "verifier_status": compact.get("verification_status"),
                }
            )
        if pred_handle.readline() or ver_handle.readline():
            raise ValueError(f"prediction_verification_length_mismatch:{source}")
    print(json.dumps({"source": source, "input_rows": count, "in_scope_rows": len(rows)}))
    return rows


def assign_ranks(rows: list[dict[str, Any]]) -> None:
    by_subgraph: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_subgraph[row["subgraph_id"]].append(row)
    score_fields = {
        "semantic_only": "semantic_score",
        "family_conditional_risk": "family_conditional_risk",
    }
    for group in by_subgraph.values():
        for condition, score_field in score_fields.items():
            ranked = sorted(
                group,
                key=lambda x: (
                    -x[score_field],
                    x["subject_id"],
                    x["object_id"],
                    x["predicate_label"],
                ),
            )
            for rank, row in enumerate(ranked, 1):
                row.setdefault("ranks", {})[f"global_in_scope:{condition}"] = rank
        by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in group:
            by_family[row["predicate_family"]].append(row)
        for family_rows in by_family.values():
            for condition, score_field in score_fields.items():
                ranked = sorted(
                    family_rows,
                    key=lambda x: (
                        -x[score_field],
                        x["subject_id"],
                        x["object_id"],
                        x["predicate_label"],
                    ),
                )
                for rank, row in enumerate(ranked, 1):
                    row.setdefault("ranks", {})[f"within_family:{condition}"] = rank


def rank_band(rank: int) -> str:
    previous = 0
    for k in KS:
        if rank <= k:
            return f"{previous + 1:03d}_{k:03d}"
        previous = k
    raise ValueError(rank)


def stratum_memberships(row: dict[str, Any]) -> list[str]:
    output: list[str] = []
    for context in RANKING_CONTEXTS:
        sem_rank = int(row["ranks"][f"{context}:semantic_only"])
        main_rank = int(row["ranks"][f"{context}:family_conditional_risk"])
        sem_in = sem_rank <= max(KS)
        main_in = main_rank <= max(KS)
        if not sem_in and not main_in:
            continue
        membership = "both" if sem_in and main_in else ("semantic_only" if sem_in else "main_only")
        minimum_rank = min(sem_rank if sem_in else 10**9, main_rank if main_in else 10**9)
        output.append(
            "|".join(
                [
                    row["source"],
                    context,
                    row["predicate_family"],
                    membership,
                    rank_band(minimum_rank),
                ]
            )
        )
    return output


def load_crop_index(repo_root: Path) -> dict[tuple[str, int, int], dict[str, Any]]:
    path = repo_root / "experiments/H001_geom_reliability/sources/qwen_vl/full_validation/crops/all/records.jsonl"
    index: dict[tuple[str, int, int], dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            index[(row["subgraph_id"], int(row["subject_id"]), int(row["object_id"]))] = row
    return index


def sample_items(
    rows_by_source: dict[str, list[dict[str, Any]]], quota: int, seed: int
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    strata: dict[str, list[dict[str, Any]]] = defaultdict(list)
    all_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    item_strata: dict[str, set[str]] = defaultdict(set)
    for source_rows in rows_by_source.values():
        for row in source_rows:
            all_records[row["item_key"]].append(row)
            for stratum in stratum_memberships(row):
                strata[stratum].append(row)
                item_strata[row["item_key"]].add(stratum)

    selected_keys: set[str] = set()
    stratum_summary: dict[str, dict[str, Any]] = {}
    for stratum in sorted(strata):
        unique = {row["item_key"]: row for row in strata[stratum]}
        population = sorted(unique)
        sample_n = min(quota, len(population))
        ordered = sorted(
            population,
            key=lambda key: stable_hash(f"{seed}|{stratum}|{key}", 64),
        )
        chosen = ordered[:sample_n]
        selected_keys.update(chosen)
        stratum_summary[stratum] = {
            "population": len(population),
            "sample_n": sample_n,
            "marginal_selection_probability": sample_n / len(population),
        }

    selected: list[dict[str, Any]] = []
    for key in sorted(selected_keys, key=lambda value: stable_hash(f"audit|{seed}|{value}", 64)):
        memberships = sorted(item_strata[key])
        not_selected_probability = 1.0
        for stratum in memberships:
            not_selected_probability *= 1.0 - stratum_summary[stratum]["marginal_selection_probability"]
        inclusion_probability = 1.0 - not_selected_probability
        selected.append(
            {
                "item_key": key,
                "audit_id": f"PV-{len(selected) + 1:04d}",
                "records": all_records[key],
                "strata": memberships,
                "inclusion_probability": inclusion_probability,
                "design_weight": 1.0 / inclusion_probability,
            }
        )
    return selected, stratum_summary


def load_pair_points(path: Path, object_ids: set[int]) -> dict[int, list[tuple[float, float, float]]]:
    points: dict[int, list[tuple[float, float, float]]] = {object_id: [] for object_id in object_ids}
    properties: list[str] = []
    vertex_count = 0
    in_vertex = False
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        if handle.readline().strip() != "ply":
            raise ValueError(f"invalid_ply:{path}")
        for line in handle:
            value = line.strip()
            if value != "format ascii 1.0" and value.startswith("format"):
                raise ValueError(f"unsupported_ply:{path}:{value}")
            if value.startswith("element vertex"):
                vertex_count = int(value.split()[-1])
                in_vertex = True
            elif value.startswith("element "):
                in_vertex = False
            elif value.startswith("property") and in_vertex:
                properties.append(value.split()[-1])
            elif value == "end_header":
                break
        indices = {name: properties.index(name) for name in ("x", "y", "z", "objectId")}
        for _ in range(vertex_count):
            values = handle.readline().split()
            if not values:
                break
            object_id = int(values[indices["objectId"]])
            if object_id in points:
                points[object_id].append(
                    (
                        float(values[indices["x"]]),
                        float(values[indices["y"]]),
                        float(values[indices["z"]]),
                    )
                )
    return points


def downsample(points: list[tuple[float, float, float]], maximum: int) -> list[tuple[float, float, float]]:
    if len(points) <= maximum:
        return points
    step = len(points) / maximum
    return [points[min(int(index * step), len(points) - 1)] for index in range(maximum)]


def write_pair_ply(
    path: Path,
    subject: list[tuple[float, float, float]],
    obj: list[tuple[float, float, float]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("ply\nformat ascii 1.0\n")
        handle.write("comment subject red; object blue\n")
        handle.write(f"element vertex {len(subject) + len(obj)}\n")
        handle.write("property float x\nproperty float y\nproperty float z\n")
        handle.write("property uchar red\nproperty uchar green\nproperty uchar blue\n")
        handle.write("property uchar roleId\nend_header\n")
        for x, y, z in subject:
            handle.write(f"{x:.6f} {y:.6f} {z:.6f} 230 70 60 1\n")
        for x, y, z in obj:
            handle.write(f"{x:.6f} {y:.6f} {z:.6f} 55 115 225 2\n")


def draw_projection(
    path: Path,
    subject: list[tuple[float, float, float]],
    obj: list[tuple[float, float, float]],
    title: str,
) -> None:
    width, height = 1200, 430
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    draw.text((18, 12), title, fill=(20, 20, 20))
    draw.text((18, 31), "subject=red, object=blue; raw orthographic point projections", fill=(60, 60, 60))
    panels = [(0, 1, "XY"), (0, 2, "XZ"), (1, 2, "YZ")]
    all_points = subject + obj
    for panel_index, (axis_a, axis_b, label) in enumerate(panels):
        left = 18 + panel_index * 394
        top, panel_w, panel_h = 60, 370, 350
        draw.rectangle((left, top, left + panel_w, top + panel_h), outline=(180, 180, 180))
        draw.text((left + 8, top + 8), label, fill=(40, 40, 40))
        values_a = [point[axis_a] for point in all_points]
        values_b = [point[axis_b] for point in all_points]
        if not values_a or not values_b:
            continue
        minimum_a, maximum_a = min(values_a), max(values_a)
        minimum_b, maximum_b = min(values_b), max(values_b)
        span_a = max(maximum_a - minimum_a, 1e-6)
        span_b = max(maximum_b - minimum_b, 1e-6)
        scale = min((panel_w - 24) / span_a, (panel_h - 36) / span_b)
        offset_x = left + (panel_w - span_a * scale) / 2
        offset_y = top + (panel_h - span_b * scale) / 2
        for points, color in ((obj, (55, 115, 225)), (subject, (230, 70, 60))):
            for point in points:
                x = offset_x + (point[axis_a] - minimum_a) * scale
                y = top + panel_h - ((point[axis_b] - minimum_b) * scale + (offset_y - top))
                draw.ellipse((x - 1, y - 1, x + 1, y + 1), fill=color)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)


def materialize_evidence(
    repo_root: Path,
    evidence_root: Path,
    selected: list[dict[str, Any]],
    max_points: int,
) -> dict[str, Any]:
    by_scan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in selected:
        by_scan[item["records"][0]["scan_id"]].append(item)
    missing: list[str] = []
    for scan_index, (scan_id, items) in enumerate(sorted(by_scan.items()), 1):
        object_ids = {
            int(identifier)
            for item in items
            for identifier in (item["records"][0]["subject_id"], item["records"][0]["object_id"])
        }
        source_ply = repo_root / "local_dataset/3RScan/scans" / scan_id / "labels.instances.annotated.v2.ply"
        if not source_ply.exists():
            missing.extend(item["audit_id"] for item in items)
            continue
        points = load_pair_points(source_ply, object_ids)
        for item in items:
            record = item["records"][0]
            subject = downsample(points.get(int(record["subject_id"]), []), max_points)
            obj = downsample(points.get(int(record["object_id"]), []), max_points)
            if not subject or not obj:
                missing.append(item["audit_id"])
                continue
            ply_path = evidence_root / f"{item['audit_id']}.ply"
            projection_path = evidence_root / f"{item['audit_id']}.png"
            write_pair_ply(ply_path, subject, obj)
            draw_projection(
                projection_path,
                subject,
                obj,
                f"{record['subject_label']} --{record['predicate_label']}--> {record['object_label']}",
            )
            item["pair_ply_path"] = relpath(repo_root, ply_path)
            item["geometry_projection_path"] = relpath(repo_root, projection_path)
            item["evidence_point_counts"] = {"subject": len(subject), "object": len(obj)}
        if scan_index % 25 == 0 or scan_index == len(by_scan):
            print(json.dumps({"evidence_scans": scan_index, "total_scans": len(by_scan)}))
    return {"scans": len(by_scan), "missing_items": sorted(set(missing))}


def public_row(item: dict[str, Any], crop_index: dict[tuple[str, int, int], dict[str, Any]]) -> dict[str, Any]:
    record = item["records"][0]
    crop = crop_index.get((record["subgraph_id"], record["subject_id"], record["object_id"]), {})
    return {
        "audit_id": item["audit_id"],
        "relation": f"{record['subject_label']} --{record['predicate_label']}--> {record['object_label']}",
        "predicate_label": record["predicate_label"],
        "predicate_family": record["predicate_family"],
        "rgb_pair_crop_path": crop.get("pair_crop_path", ""),
        "geometry_projection_path": item.get("geometry_projection_path", ""),
        "pair_ply_path": item.get("pair_ply_path", ""),
        "physical_validity_label": "",
        "confidence": "",
        "primary_reason_code": "",
        "evidence_sufficient": "",
        "notes": "",
        "reviewer_id": "",
        "reviewed_at": "",
    }


def make_protocol(manifest: dict[str, Any]) -> str:
    return f"""# Independent Physical-Validity Audit Protocol

Frozen at UTC: `{manifest['created_at_utc']}`  
Protocol status: `{manifest['status']}`  
Protocol version: `{SCHEMA_VERSION}`

## Estimand and scope

The primary estimand is design-weighted human `Violation@K` for
`semantic_only` and `family_conditional_risk` at K = `{{5,10,20,50,100}}`,
reported overall and by `support_contact`, `proximity`, and
`relative_vertical`. The audit covers both global in-scope ranking and
within-family ranking. `ambiguous` and `unobservable` are never silently counted
as valid; they are excluded from the binary denominator and reported as audit
coverage.

## Blinding and evidence

Annotators see only relation text, an RGB pair crop when available, raw
orthographic point projections, and a colored pair PLY (subject red, object
blue). RGB availability is reported as evidence coverage but is not an
eligibility rule because the raw 3D pair evidence is complete. Public sheets
exclude source identity, semantic score, geometry score, all ranks, verifier
status, GT membership, sampling stratum, and current method condition. The
private sidecar must not be opened by annotators before both sheets are locked.

## Labels

- `physically_valid`: the stated directed relation is supported by the visible
  reconstructed geometry and RGB evidence.
- `physically_invalid`: the evidence contradicts the stated relation.
- `ambiguous`: evidence is available but the physical interpretation is not
  sufficiently determinate.
- `unobservable`: reconstruction, segmentation, crop, or occlusion prevents a
  defensible judgment.

For `standing on`/`lying on`/`supported by`, judge direct contact and support
configuration, not object-category plausibility. For `close by`, judge pairwise
distance relative to object extent and scene context. For `higher than` and
`lower than`, judge the directed vertical ordering of the instances.

## Annotation and adjudication

Two independent annotators complete `annotator_a.csv` and `annotator_b.csv` in
their separately shuffled order. They must not discuss rows during first pass.
Agreement is reported before adjudication. All disagreements, and any row with
low confidence, `ambiguous`, or `unobservable`, enter a blinded adjudication
pass. The adjudicated label is the primary analysis; single-rater results may
only be described as preliminary.

## Sampling and inference

Candidates are the union of top-100 predictions under both conditions. Fixed
strata cross source, ranking context, predicate family, condition-membership
signature, and rank band. Each nonempty stratum contributes up to
`{manifest['sampling']['quota_per_stratum']}` hash-randomized rows. Duplicate
physical relation items are labeled once. The private sidecar records each
item's union inclusion probability and Horvitz--Thompson design weight. CIs are
cluster-bootstrap intervals over subgraphs/scans with design weights retained.
Raw semantic calibration is reported with weighted Brier, AUROC, AUPRC, ECE,
and reliability bins. A monotone Platt map is fit and evaluated by five-fold
cross-fitting with complete scan groups held out; no row is scored by a map fit
using labels from the same scan.

## Frozen exclusions

No score tuning, threshold selection, family removal, K removal, label collapse,
or audit-row replacement is allowed after either annotator begins. Missing or
corrupt evidence remains in the accounting and is labeled `unobservable`; it is
not replaced post hoc.
"""


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    out = resolve(repo_root, args.out)
    evidence_root = resolve(repo_root, args.evidence_root)
    evalmod = load_eval_module(repo_root)
    family_model_path = (
        repo_root
        / "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json"
    )
    family_model = read_json(family_model_path)

    rows_by_source: dict[str, list[dict[str, Any]]] = {}
    for source, spec in SOURCE_SPECS.items():
        rows = iter_source_rows(repo_root, source, spec, evalmod, family_model)
        assign_ranks(rows)
        rows_by_source[source] = rows

    selected, strata = sample_items(rows_by_source, args.quota_per_stratum, args.seed)
    crop_index = load_crop_index(repo_root)
    evidence_summary = {"skipped": True, "missing_items": []}
    if not args.skip_evidence:
        evidence_summary = materialize_evidence(
            repo_root, evidence_root, selected, args.max_points_per_object
        )
        evidence_summary["skipped"] = False

    public = [public_row(item, crop_index) for item in selected]
    public_by_id = {row["audit_id"]: row for row in public}
    order_a = sorted(public_by_id, key=lambda key: stable_hash(f"A|{args.seed}|{key}", 64))
    order_b = sorted(public_by_id, key=lambda key: stable_hash(f"B|{args.seed}|{key}", 64))
    annotator_a = [public_by_id[key] for key in order_a]
    annotator_b = [public_by_id[key] for key in order_b]

    hidden: list[dict[str, Any]] = []
    for item in selected:
        hidden.append(
            {
                "schema_version": SCHEMA_VERSION,
                "audit_id": item["audit_id"],
                "item_key": item["item_key"],
                "inclusion_probability": item["inclusion_probability"],
                "design_weight": item["design_weight"],
                "strata": item["strata"],
                "source_records": item["records"],
            }
        )

    out.mkdir(parents=True, exist_ok=True)
    write_csv(out / "annotator_a.csv", annotator_a)
    write_csv(out / "annotator_b.csv", annotator_b)
    write_jsonl(out / "private_sidecar.jsonl", hidden)
    write_jsonl(out / "public_queue.jsonl", public)
    adjudication = []
    for row in public:
        adjudication.append(
            {
                "audit_id": row["audit_id"],
                "relation": row["relation"],
                "rgb_pair_crop_path": row["rgb_pair_crop_path"],
                "geometry_projection_path": row["geometry_projection_path"],
                "pair_ply_path": row["pair_ply_path"],
                "annotator_a_label": "",
                "annotator_b_label": "",
                "adjudicated_label": "",
                "adjudication_reason": "",
                "adjudicator_id": "",
                "adjudicated_at": "",
            }
        )
    write_csv(out / "adjudication.csv", adjudication)

    missing_crop = sum(1 for row in public if not row["rgb_pair_crop_path"])
    missing_projection = sum(1 for row in public if not row["geometry_projection_path"])
    blocked_public_fields = {
        "source",
        "prediction_id",
        "semantic_score",
        "p_geom_valid_family",
        "family_conditional_risk",
        "rank",
        "verifier_status",
        "sampling_stratum",
        "inclusion_probability",
        "design_weight",
    }
    public_field_hits = sorted(blocked_public_fields & set().union(*(set(row) for row in public)))
    validation_errors: list[str] = []
    if len({row["audit_id"] for row in public}) != len(public):
        validation_errors.append("duplicate_public_audit_id")
    if set(order_a) != set(order_b) or len(order_a) != len(public):
        validation_errors.append("annotator_id_set_mismatch")
    if order_a == order_b:
        validation_errors.append("annotator_orders_not_independently_shuffled")
    if public_field_hits:
        validation_errors.append(f"blocked_public_field_hits:{public_field_hits}")
    if evidence_summary.get("missing_items") or missing_projection:
        validation_errors.append("required_raw_3d_evidence_missing")
    source_counts = Counter(
        record["source"] for item in selected for record in item["records"]
    )
    family_counts = Counter(item["records"][0]["predicate_family"] for item in selected)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "frozen_awaiting_independent_human_labels"
            if not validation_errors
            else "blocked_validation_errors"
        ),
        "scope": {
            "sources": list(SOURCE_SPECS),
            "families": list(FAMILIES),
            "conditions": list(CONDITIONS),
            "ranking_contexts": list(RANKING_CONTEXTS),
            "ks": list(KS),
        },
        "sampling": {
            "seed": args.seed,
            "quota_per_stratum": args.quota_per_stratum,
            "nonempty_strata": len(strata),
            "selected_unique_items": len(selected),
            "strata": strata,
        },
        "counts": {
            "selected_unique_items": len(selected),
            "by_family": dict(sorted(family_counts.items())),
            "source_memberships": dict(sorted(source_counts.items())),
            "missing_rgb_crop": missing_crop,
            "missing_projection": missing_projection,
        },
        "evidence": {
            **evidence_summary,
            "root": relpath(repo_root, evidence_root),
            "max_points_per_object": args.max_points_per_object,
            "rgb_pair_crop_is_optional": True,
            "raw_3d_pair_evidence_is_required": True,
        },
        "allowed_labels": list(LABELS),
        "allowed_confidence": list(CONFIDENCE),
        "allowed_reason_codes": list(REASON_CODES),
        "validation": {
            "errors": validation_errors,
            "error_count": len(validation_errors),
            "gates": {
                "unique_public_ids": "duplicate_public_audit_id" not in validation_errors,
                "independent_annotator_order": "annotator_orders_not_independently_shuffled" not in validation_errors,
                "same_annotator_id_set": "annotator_id_set_mismatch" not in validation_errors,
                "blocked_public_field_hits": public_field_hits,
                "required_raw_3d_evidence_complete": "required_raw_3d_evidence_missing" not in validation_errors,
            },
        },
        "blinded_fields_excluded": [
            "source",
            "prediction_id",
            "semantic_score",
            "p_geom_valid_family",
            "family_conditional_risk",
            "rank",
            "verifier_status",
            "sampling_stratum",
            "inclusion_probability",
            "design_weight",
        ],
        "inputs": {
            "family_model": relpath(repo_root, family_model_path),
            "family_model_sha256": sha256_file(family_model_path),
            "sources": SOURCE_SPECS,
        },
        "outputs": {
            "protocol": relpath(repo_root, out / "protocol.md"),
            "manifest": relpath(repo_root, out / "manifest.json"),
            "annotator_a": relpath(repo_root, out / "annotator_a.csv"),
            "annotator_b": relpath(repo_root, out / "annotator_b.csv"),
            "adjudication": relpath(repo_root, out / "adjudication.csv"),
            "private_sidecar": relpath(repo_root, out / "private_sidecar.jsonl"),
        },
        "docker_command": (
            "UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml "
            "run --rm physical_validity_audit_freeze"
        ),
    }
    (out / "protocol.md").write_text(make_protocol(manifest), encoding="utf-8")
    write_json(out / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "selected": len(selected), "out": relpath(repo_root, out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
