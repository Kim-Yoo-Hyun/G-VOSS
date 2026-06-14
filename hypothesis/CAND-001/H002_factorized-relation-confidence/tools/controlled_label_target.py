#!/usr/bin/env python3
"""Create a controlled H002 label target review queue."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from annotation_audit import (
    H002_ROOT,
    find_instance_images,
    render_contact_sheet,
    repo_rel,
    safe_slug,
    scan_asset_paths,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
RGA_ROOT = H002_ROOT / "artifacts/train_rga_seed/open3dsg_train_pilot/rga"
DEFAULT_MATCH_ROWS = RGA_ROOT / "match_rows.jsonl"
DEFAULT_EXISTING_STRICT = RGA_ROOT / "multiview_audit_protocol/primary_strict_queue.jsonl"
DEFAULT_OUTPUT_DIR = RGA_ROOT / "controlled_label_target"

RANK_BANDS = ["rank_201_500", "rank_501_1000", "rank_gt1000"]
PER_BAND_PER_STRATUM = 16
STRUCTURAL_LABELS = {
    "ceiling",
    "curtain",
    "door",
    "doorframe",
    "floor",
    "room",
    "shower",
    "shower curtain",
    "wall",
    "window",
}
GENERIC_LABELS = {"item", "object", "clutter", "unknown"}

REVIEW_FIELDS = {
    "reviewer_id": "free text",
    "review_round": "integer",
    "object_pair_valid": "yes/no/uncertain",
    "predicate_visually_plausible": "yes/no/uncertain",
    "geometry_witness_correct": "yes/no/uncertain",
    "relation_informative": "yes/no/uncertain",
    "relation_trivial_or_dense": "yes/no/uncertain",
    "annotation_missing_or_sparse": "yes/no/uncertain",
    "ontology_or_granularity_issue": "yes/no/uncertain",
    "segmentation_or_instance_issue": "yes/no/uncertain",
    "final_controlled_label": (
        "reliable_promote/unreliable_dense_noise/relabel_only/"
        "invalid_pair/geometry_artifact/abstain_uncertain"
    ),
    "confidence": "high/medium/low",
    "notes": "free text",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--match-rows", type=Path, default=DEFAULT_MATCH_ROWS)
    parser.add_argument("--existing-strict", type=Path, default=DEFAULT_EXISTING_STRICT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--per-band-per-stratum", type=int, default=PER_BAND_PER_STRATUM)
    parser.add_argument("--images-per-object", type=int, default=2)
    return parser.parse_args()


def as_abs(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def rel_path(path: Path | None) -> str | None:
    if path is None:
        return None
    path = as_abs(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def iter_jsonl(path: Path):
    with as_abs(path).open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def endpoint_category(label: str) -> str:
    low = label.lower()
    if low in STRUCTURAL_LABELS:
        return "structural"
    if low in GENERIC_LABELS:
        return "generic"
    return "object"


def undirected_pair_key(row: dict[str, Any]) -> tuple[str, str, tuple[int, int], str]:
    identity = row["identity"]
    return (
        str(identity["scan_id"]),
        str(identity["subgraph_id"]),
        tuple(sorted([int(identity["subject_id"]), int(identity["object_id"])])),
        str(row["predicate"]["predicate_label"]),
    )


def existing_pair_key(row: dict[str, Any]) -> tuple[str, str, tuple[int, int], str]:
    return (
        str(row["scan_id"]),
        str(row["subgraph_id"]),
        tuple(sorted([int(row["subject_id"]), int(row["object_id"])])),
        str(row["predicate_label"]),
    )


def candidate_stratum(row: dict[str, Any]) -> tuple[str | None, str | None]:
    edge = row["edge"]
    label = row["label"]
    subject_label = str(edge["subject_label"]).lower()
    object_label = str(edge["object_label"]).lower()
    subject_category = endpoint_category(subject_label)
    object_category = endpoint_category(object_label)
    same_label = subject_label == object_label
    match_status = str(label["label_match_status"])

    if (
        match_status in {"exact_match", "pair_has_other_predicate"}
        and subject_category == "object"
        and object_category == "object"
        and not same_label
    ):
        return (
            "candidate_reliable_promote_seed",
            "annotation-supported non-structural proximity pair; final label requires human confirmation",
        )

    if match_status == "no_gt_for_pair" and (
        subject_category in {"structural", "generic"}
        or object_category in {"structural", "generic"}
        or same_label
    ):
        return (
            "candidate_unreliable_dense_noise_seed",
            "geometry-satisfied proximity with structural/generic/same-label endpoint; final label requires human confirmation",
        )

    return None, None


def row_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(row["identity"]["scan_id"]),
        int(row["semantic"]["rank_in_context"]),
        -float(row["geometry"]["p_geom_valid"] or 0.0),
        str(row["identity"]["prediction_id"]),
    )


def round_robin_sample(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    by_scan: dict[str, deque[dict[str, Any]]] = defaultdict(deque)
    for row in sorted(rows, key=row_sort_key):
        by_scan[str(row["identity"]["scan_id"])].append(row)
    selected: list[dict[str, Any]] = []
    scans = deque(sorted(by_scan))
    while scans and len(selected) < limit:
        scan = scans.popleft()
        queue = by_scan[scan]
        if queue:
            selected.append(queue.popleft())
        if queue:
            scans.append(scan)
    return selected


def normalize_match_row(
    row: dict[str, Any],
    *,
    source_queue: str,
    proposed_stratum: str,
    stratum_reason: str,
    review_id: str,
    output_dir: Path,
    images_per_object: int,
) -> dict[str, Any]:
    identity = row["identity"]
    edge = row["edge"]
    predicate = row["predicate"]
    semantic = row["semantic"]
    geometry = row["geometry"]
    label = row["label"]
    rga = row["rga"]
    subject_images, subject_count = find_instance_images(
        str(identity["scan_id"]), int(identity["subject_id"]), images_per_object
    )
    object_images, object_count = find_instance_images(
        str(identity["scan_id"]), int(identity["object_id"]), images_per_object
    )
    asset_state = (
        "subject_and_object_images"
        if subject_images and object_images
        else "missing_subject_or_object_images"
    )
    contact_sheet = None
    if subject_images and object_images:
        sheet_name = (
            f"{review_id}_{safe_slug(identity['scan_id'][:8])}_"
            f"{identity['subject_id']}_{safe_slug(predicate['predicate_label'])}_"
            f"{identity['object_id']}.jpg"
        )
        sheet_path = output_dir / "contact_sheets" / sheet_name
        render_row = {
            "source_id": row["source"]["source_id"],
            "subject_label": edge["subject_label"],
            "subject_id": identity["subject_id"],
            "predicate_label": predicate["predicate_label"],
            "object_label": edge["object_label"],
            "object_id": identity["object_id"],
            "scan_id": identity["scan_id"],
            "semantic_rank": semantic["rank_in_context"],
            "semantic_score": semantic["semantic_score_raw"],
            "p_geom_valid": geometry["p_geom_valid"],
            "match_status": label["label_match_status"],
            "matched_predicates": label["matched_predicates"],
            "previsual_label": proposed_stratum,
            "previsual_reason": stratum_reason,
        }
        render_contact_sheet(render_row, subject_images, object_images, sheet_path)
        contact_sheet = repo_rel(sheet_path)

    return {
        "schema_version": "h002_controlled_label_target_row_v0",
        "review_id": review_id,
        "source_queue": source_queue,
        "proposed_review_stratum": proposed_stratum,
        "stratum_reason": stratum_reason,
        "final_label_is_unset": True,
        "prediction_id": identity["prediction_id"],
        "scan_id": identity["scan_id"],
        "subgraph_id": identity["subgraph_id"],
        "subject_id": identity["subject_id"],
        "subject_label": edge["subject_label"],
        "subject_endpoint_category": endpoint_category(str(edge["subject_label"])),
        "predicate_label": predicate["predicate_label"],
        "predicate_family": predicate["predicate_family"],
        "object_id": identity["object_id"],
        "object_label": edge["object_label"],
        "object_endpoint_category": endpoint_category(str(edge["object_label"])),
        "same_endpoint_label": str(edge["subject_label"]).lower() == str(edge["object_label"]).lower(),
        "source_id": row["source"]["source_id"],
        "semantic_rank": semantic["rank_in_context"],
        "rank_band": rga["rank_band"],
        "semantic_score_raw": semantic["semantic_score_raw"],
        "semantic_score_norm": semantic["semantic_score_norm"],
        "geometry_status": geometry["geometry_status"],
        "p_geom_valid": geometry["p_geom_valid"],
        "consistency_score": geometry["consistency_score"],
        "geometry_residual_proxy": geometry["geometry_residual_proxy"],
        "reason_codes": geometry["reason_codes"],
        "label_match_status": label["label_match_status"],
        "matched_predicates": label["matched_predicates"],
        "bucket_top100": rga["bucket_top100"],
        "visual_assets": {
            **scan_asset_paths(str(identity["scan_id"])),
            "subject_images": [repo_rel(path) for path in subject_images],
            "object_images": [repo_rel(path) for path in object_images],
            "subject_image_count": subject_count,
            "object_image_count": object_count,
            "contact_sheet": contact_sheet,
        },
        "asset_state": asset_state,
        "review_fields": {field: None for field in REVIEW_FIELDS},
        "boundary": "candidate review row only; proposed stratum is not a label; no validation/test rows used",
    }


def normalize_existing_row(row: dict[str, Any], review_id: str) -> dict[str, Any]:
    working = str(row["working_label"])
    if working == "true_underconfidence":
        proposed = "existing_strict_reliable_seed"
    elif working == "dense_relation_noise":
        proposed = "existing_strict_dense_seed"
    else:
        proposed = "existing_strict_uncertain_seed"
    return {
        "schema_version": "h002_controlled_label_target_row_v0",
        "review_id": review_id,
        "source_queue": "existing_strict_seed",
        "proposed_review_stratum": proposed,
        "stratum_reason": "carried from current strict target; must be human-confirmed before use",
        "final_label_is_unset": True,
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "subject_endpoint_category": endpoint_category(str(row["subject_label"])),
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "object_endpoint_category": endpoint_category(str(row["object_label"])),
        "same_endpoint_label": str(row["subject_label"]).lower() == str(row["object_label"]).lower(),
        "source_id": "open3dsg_train_pilot",
        "semantic_rank": None,
        "rank_band": row["rank_bucket"],
        "semantic_score_raw": row["semantic_score_raw"],
        "semantic_score_norm": row["semantic_score_norm"],
        "geometry_status": row["geometry_status"],
        "p_geom_valid": row["p_geom_valid"],
        "consistency_score": row["consistency_score"],
        "geometry_residual_proxy": row["geometry_residual_proxy"],
        "reason_codes": [],
        "label_match_status": None,
        "matched_predicates": [],
        "bucket_top100": None,
        "visual_assets": row.get("visual_assets") or {},
        "asset_state": "subject_and_object_images"
        if (row.get("visual_assets") or {}).get("subject_images")
        and (row.get("visual_assets") or {}).get("object_images")
        else "missing_subject_or_object_images",
        "review_fields": {field: None for field in REVIEW_FIELDS},
        "boundary": "existing strict seed only; proposed stratum is not a label; no validation/test rows used",
    }


def collect_candidate_pools(
    match_rows_path: Path,
    existing_pair_keys: set[tuple[str, str, tuple[int, int], str]],
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    pools: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    seen_pairs = set(existing_pair_keys)
    for row in iter_jsonl(match_rows_path):
        predicate = row["predicate"]
        geometry = row["geometry"]
        semantic = row["semantic"]
        rga = row["rga"]
        if predicate["predicate_family"] != "proximity":
            continue
        if predicate["predicate_label"] != "close by":
            continue
        if geometry["geometry_status"] != "satisfied":
            continue
        if int(semantic["rank_in_context"]) <= 100:
            continue
        if rga["rank_band"] not in RANK_BANDS:
            continue
        pair_key = undirected_pair_key(row)
        if pair_key in seen_pairs:
            continue
        proposed, reason = candidate_stratum(row)
        if proposed is None:
            continue
        seen_pairs.add(pair_key)
        row["_proposed_review_stratum"] = proposed
        row["_stratum_reason"] = reason
        pools[(rga["rank_band"], proposed)].append(row)
    return pools


def select_mined_rows(
    pools: dict[tuple[str, str], list[dict[str, Any]]],
    per_band_per_stratum: int,
    output_dir: Path,
    images_per_object: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    selected_rows: list[dict[str, Any]] = []
    shortages: list[dict[str, Any]] = []
    idx = 1
    strata = [
        "candidate_reliable_promote_seed",
        "candidate_unreliable_dense_noise_seed",
    ]
    for band in RANK_BANDS:
        for stratum in strata:
            rows = pools.get((band, stratum), [])
            chosen = round_robin_sample(rows, per_band_per_stratum)
            if len(chosen) < per_band_per_stratum:
                shortages.append(
                    {
                        "rank_band": band,
                        "proposed_review_stratum": stratum,
                        "available": len(rows),
                        "selected": len(chosen),
                        "required": per_band_per_stratum,
                    }
                )
            for row in chosen:
                review_id = f"ctl_{idx:04d}"
                selected_rows.append(
                    normalize_match_row(
                        row,
                        source_queue="mined_controlled_proximity",
                        proposed_stratum=row["_proposed_review_stratum"],
                        stratum_reason=row["_stratum_reason"],
                        review_id=review_id,
                        output_dir=output_dir,
                        images_per_object=images_per_object,
                    )
                )
                idx += 1
    return selected_rows, shortages


def sheet_row(row: dict[str, Any]) -> dict[str, Any]:
    assets = row.get("visual_assets") or {}
    flat = {
        "review_id": row["review_id"],
        "source_queue": row["source_queue"],
        "proposed_review_stratum": row["proposed_review_stratum"],
        "stratum_reason": row["stratum_reason"],
        "prediction_id": row["prediction_id"],
        "scan_id": row["scan_id"],
        "subgraph_id": row["subgraph_id"],
        "subject_id": row["subject_id"],
        "subject_label": row["subject_label"],
        "subject_endpoint_category": row["subject_endpoint_category"],
        "predicate_label": row["predicate_label"],
        "predicate_family": row["predicate_family"],
        "object_id": row["object_id"],
        "object_label": row["object_label"],
        "object_endpoint_category": row["object_endpoint_category"],
        "same_endpoint_label": row["same_endpoint_label"],
        "semantic_rank": row["semantic_rank"],
        "rank_band": row["rank_band"],
        "semantic_score_raw": row["semantic_score_raw"],
        "semantic_score_norm": row["semantic_score_norm"],
        "geometry_status": row["geometry_status"],
        "p_geom_valid": row["p_geom_valid"],
        "label_match_status": row["label_match_status"],
        "matched_predicates": ",".join(str(item) for item in row.get("matched_predicates") or []),
        "asset_state": row["asset_state"],
        "contact_sheet": assets.get("contact_sheet"),
        "subject_image_count": assets.get("subject_image_count"),
        "object_image_count": assets.get("object_image_count"),
        "mesh_obj": assets.get("mesh_obj"),
    }
    flat.update({field: "" for field in REVIEW_FIELDS})
    return flat


def write_sheet(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "review_id",
        "source_queue",
        "proposed_review_stratum",
        "stratum_reason",
        "prediction_id",
        "scan_id",
        "subgraph_id",
        "subject_id",
        "subject_label",
        "subject_endpoint_category",
        "predicate_label",
        "predicate_family",
        "object_id",
        "object_label",
        "object_endpoint_category",
        "same_endpoint_label",
        "semantic_rank",
        "rank_band",
        "semantic_score_raw",
        "semantic_score_norm",
        "geometry_status",
        "p_geom_valid",
        "label_match_status",
        "matched_predicates",
        "asset_state",
        "contact_sheet",
        "subject_image_count",
        "object_image_count",
        "mesh_obj",
        *REVIEW_FIELDS.keys(),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow(sheet_row(row))


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "source_queue_counts": dict(Counter(row["source_queue"] for row in rows)),
        "proposed_stratum_counts": dict(Counter(row["proposed_review_stratum"] for row in rows)),
        "rank_band_counts": dict(Counter(row["rank_band"] for row in rows)),
        "rank_band_by_stratum": {
            f"{band}|{stratum}": count
            for (band, stratum), count in sorted(
                Counter((row["rank_band"], row["proposed_review_stratum"]) for row in rows).items()
            )
        },
        "family_counts": dict(Counter(row["predicate_family"] for row in rows)),
        "geometry_status_counts": dict(Counter(row["geometry_status"] for row in rows)),
        "label_match_counts": dict(Counter(str(row["label_match_status"]) for row in rows)),
        "asset_state_counts": dict(Counter(row["asset_state"] for row in rows)),
        "contact_sheet_count": sum(1 for row in rows if (row.get("visual_assets") or {}).get("contact_sheet")),
        "mesh_obj_count": sum(1 for row in rows if (row.get("visual_assets") or {}).get("mesh_obj")),
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# H002 Controlled Label Target",
        "",
        f"Created at: `{summary['created_at']}`",
        "",
        "## Boundary",
        "",
        "- Train-only candidate review queue.",
        "- No validation/test rows are used.",
        "- Proposed strata are sampling priors, not labels.",
        "- `V_mv_e` is not a model input.",
        "",
        "## Counts",
        "",
        "| Queue | Rows | Contact sheets | Mesh links |",
        "| --- | ---: | ---: | ---: |",
    ]
    for key in ["mined_controlled", "existing_strict_seed", "combined_review"]:
        counts = summary["counts"][key]
        lines.append(
            f"| `{key}` | {counts['rows']} | {counts['contact_sheet_count']} | {counts['mesh_obj_count']} |"
        )
    lines.extend(
        [
            "",
            "## Mined Controlled Queue",
            "",
            "The mined queue is balanced by rank band and proposed stratum:",
            "",
            "```json",
            json.dumps(summary["counts"]["mined_controlled"]["rank_band_by_stratum"], indent=2, sort_keys=True),
            "```",
            "",
            "Next gate: `37_controlled_label_readiness.md` after labels are filled.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = as_abs(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_rows = read_jsonl(args.existing_strict)
    existing_pair_keys = {existing_pair_key(row) for row in existing_rows}
    existing_seed = [
        normalize_existing_row(row, f"seed_{idx:04d}") for idx, row in enumerate(existing_rows, start=1)
    ]
    pools = collect_candidate_pools(args.match_rows, existing_pair_keys)
    mined_rows, shortages = select_mined_rows(
        pools,
        args.per_band_per_stratum,
        output_dir,
        args.images_per_object,
    )
    combined = existing_seed + mined_rows
    created_at = datetime.now(timezone.utc).isoformat()
    paths = {
        "summary": output_dir / "summary.json",
        "protocol": output_dir / "protocol.json",
        "mined_queue": output_dir / "mined_controlled_queue.jsonl",
        "existing_seed_queue": output_dir / "existing_strict_seed_queue.jsonl",
        "combined_queue": output_dir / "combined_review_queue.jsonl",
        "mined_sheet": output_dir / "mined_controlled_sheet.tsv",
        "combined_sheet": output_dir / "combined_review_sheet.tsv",
        "report": output_dir / "report.md",
        "contact_sheets": output_dir / "contact_sheets",
    }
    protocol = {
        "schema_version": "h002_controlled_label_target_protocol_v0",
        "selection_policy": {
            "primary_family": "proximity",
            "primary_predicate": "close by",
            "required_geometry_status": "satisfied",
            "required_semantic_rank": "> 100",
            "rank_bands": RANK_BANDS,
            "per_band_per_stratum": args.per_band_per_stratum,
            "undirected_pair_duplicate_policy": "one directed row per unordered subject/object pair; existing strict pairs excluded from mined queue",
            "candidate_reliable_seed": "exact_match or pair_has_other_predicate, non-structural endpoints, non-identical labels",
            "candidate_dense_seed": "no_gt_for_pair with structural/generic/same-label endpoint",
        },
        "review_fields": REVIEW_FIELDS,
        "claim_boundary": {
            "proposed_stratum_is_label": False,
            "human_labels_required": True,
            "validation_usage": False,
            "test_usage": False,
            "vmv_model_input_allowed": False,
            "posterior_claim_allowed": False,
        },
    }
    summary = {
        "schema_version": "h002_controlled_label_target_summary_v0",
        "status": "ready_controlled_review_queue_no_labels",
        "created_at": created_at,
        "input_paths": {
            "match_rows": rel_path(args.match_rows),
            "existing_strict": rel_path(args.existing_strict),
        },
        "output_paths": {key: rel_path(path) for key, path in paths.items()},
        "counts": {
            "mined_controlled": summarize(mined_rows),
            "existing_strict_seed": summarize(existing_seed),
            "combined_review": summarize(combined),
            "pool_available_by_band_stratum": {
                f"{band}|{stratum}": len(rows)
                for (band, stratum), rows in sorted(pools.items())
            },
            "selection_shortages": shortages,
        },
        "target_minimum_check": {
            "hypothesis_min_rows": 60,
            "hypothesis_min_per_class": 20,
            "mined_rows": len(mined_rows),
            "mined_per_candidate_class": dict(Counter(row["proposed_review_stratum"] for row in mined_rows)),
            "structurally_enough_for_review": len(mined_rows) >= 60
            and min(Counter(row["proposed_review_stratum"] for row in mined_rows).values()) >= 20,
            "requires_human_labels_before_training": True,
        },
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "paper_result": False,
            "final_labels_created": False,
            "vmv_model_input_allowed": False,
            "posterior_claim_allowed": False,
        },
        "next_gate": "37_controlled_label_readiness.md",
    }
    write_json(paths["protocol"], protocol)
    write_json(paths["summary"], summary)
    write_jsonl(paths["mined_queue"], mined_rows)
    write_jsonl(paths["existing_seed_queue"], existing_seed)
    write_jsonl(paths["combined_queue"], combined)
    write_sheet(paths["mined_sheet"], mined_rows)
    write_sheet(paths["combined_sheet"], combined)
    write_report(paths["report"], summary)
    return summary


def main() -> int:
    args = parse_args()
    summary = run(args)
    mined = summary["counts"]["mined_controlled"]
    print(
        f"status={summary['status']} mined={mined['rows']} "
        f"combined={summary['counts']['combined_review']['rows']} "
        f"sheets={mined['contact_sheet_count']} "
        f"validation_used={summary['boundary']['validation_usage']} "
        f"final_labels={summary['boundary']['final_labels_created']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
