#!/usr/bin/env python3
"""Mine mixed-strata positive-anchor candidates for H002 attachment audit."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

PLAN_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_mining_plan_v1"
V18_ROWS = (
    H2_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/rga/"
    / "reliability_target_v18_attachment_deferred_candidate_mining/selected_candidates_internal.jsonl"
)
V20_ROWS = (
    H2_ROOT
    / "artifacts/train_rga_full/open3dsg_train_full/rga/"
    / "reliability_target_v20_attachment_deferred_endpoint_balanced_counterfactual_capacity_scan/preview_internal_400.jsonl"
)
OUT_DIR = H2_ROOT / "artifacts/attachment_independent_positive_anchor_candidate_mining_v1"

SCHEMA_VERSION = "h002_attachment_independent_positive_anchor_candidate_mining_v1"
EXPECTED_PLAN_STATUS = "h002_attachment_independent_positive_anchor_mining_plan_v1_ready"
EXPECTED_PLAN_NEXT = "attachment_independent_positive_anchor_candidate_mining_v1"
STATUS_READY = "h002_attachment_independent_positive_anchor_candidate_mining_v1_ready_mixed_strata"
STATUS_ERROR = "h002_attachment_independent_positive_anchor_candidate_mining_v1_errors"
NEXT_TODO = "attachment_independent_positive_anchor_packet_materialization_v1"

ROLE_POSITIVE = "primary_positive_anchor_proxy"
ROLE_NEGATIVE = "primary_hard_negative_proxy"
ROLE_UNCERTAIN = "primary_uncertain_buffer"
ROLE_CONNECTED_NEAR = "connected_near_or_overlap_diagnostic"
ROLE_CONNECTED_FAR = "connected_far_or_functional_ambiguous_diagnostic"

TARGET_ROWS = 560
PRIMARY_BINARY_TARGET = 480
DIAGNOSTIC_TARGET = 80

QUOTAS = {
    "Q1_hanging_on_positive_anchor": 120,
    "Q2_hanging_on_hard_negative": 120,
    "Q3_attached_to_structural_positive_anchor": 120,
    "Q4_attached_to_hard_negative": 120,
    "Q5_connected_near_or_overlap_diagnostic": 40,
    "Q5_connected_far_or_functional_ambiguous_diagnostic": 40,
    "Q6_primary_uncertain_buffer": 13,
}

VISIBLE_FIELDS = [
    "candidate_id",
    "packet_request_id",
    "subject_label",
    "predicate_label",
    "object_label",
    "reviewer_visible_relation_text",
    "packet_status_expected",
    "review_relation_reliability",
    "review_geometry_support",
    "review_endpoint_identity",
    "review_coverage",
    "review_uncertainty",
    "review_notes",
]

FORBIDDEN_VISIBLE_PATTERNS = [
    "source",
    "rank",
    "proxy",
    "cell",
    "machine",
    "geometry_status",
    "prior",
    "gt",
    "label_match",
    "score",
    "hidden",
]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen: set[str] = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def norm(value: Any) -> str:
    return str(value or "").strip().lower()


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def stable_int(value: str) -> int:
    return int(stable_hash(value)[:12], 16)


def coarse_family(label: Any) -> str:
    text = norm(label)
    if text in {"wall", "floor", "ceiling"}:
        return f"structural_{text}"
    if any(token in text for token in ["cabinet", "shelf", "rack", "wardrobe", "cupboard", "drawer"]):
        return "storage_or_anchor"
    if any(token in text for token in ["chair", "sofa", "bench", "stool", "bed"]):
        return "furniture_body"
    if any(token in text for token in ["table", "desk", "counter"]):
        return "table_or_work_surface"
    if any(token in text for token in ["picture", "mirror", "board", "tv", "screen", "frame"]):
        return "wall_mounted_flat_object"
    if any(token in text for token in ["curtain", "blind", "clothes", "towel", "pillow", "blanket"]):
        return "soft_or_hanging_object"
    if any(token in text for token in ["lamp", "light", "cable", "wire", "pipe", "radiator", "heater"]):
        return "device_connector_or_fixture"
    if any(token in text for token in ["plant", "vase", "decoration", "box", "basket", "book"]):
        return "movable_object"
    return "other_object"


def proxy_role(row: dict[str, Any]) -> str:
    predicate = row["predicate_label"]
    cell = str(row.get("cell_id_hidden") or "")
    if predicate == "connected to":
        if cell.startswith("C1"):
            return ROLE_CONNECTED_NEAR
        if cell.startswith("C2"):
            return ROLE_CONNECTED_FAR
        return "connected_uncertain_diagnostic"
    if row.get("proxy_role") in {ROLE_POSITIVE, ROLE_NEGATIVE}:
        return str(row["proxy_role"])
    provisional = row.get("provisional_status_hidden")
    if provisional == "supported_candidate":
        return ROLE_POSITIVE
    if provisional == "contradicted_candidate":
        return ROLE_NEGATIVE
    if provisional == "uncertain_candidate":
        return ROLE_UNCERTAIN
    return str(provisional or "unknown_role")


def query_id(predicate: str, role: str) -> str | None:
    if predicate == "hanging on" and role == ROLE_POSITIVE:
        return "Q1_hanging_on_positive_anchor"
    if predicate == "hanging on" and role == ROLE_NEGATIVE:
        return "Q2_hanging_on_hard_negative"
    if predicate == "attached to" and role == ROLE_POSITIVE:
        return "Q3_attached_to_structural_positive_anchor"
    if predicate == "attached to" and role == ROLE_NEGATIVE:
        return "Q4_attached_to_hard_negative"
    if predicate == "connected to" and role == ROLE_CONNECTED_NEAR:
        return "Q5_connected_near_or_overlap_diagnostic"
    if predicate == "connected to" and role == ROLE_CONNECTED_FAR:
        return "Q5_connected_far_or_functional_ambiguous_diagnostic"
    if predicate in {"attached to", "hanging on"} and role == ROLE_UNCERTAIN:
        return "Q6_primary_uncertain_buffer"
    return None


def coverage_tier(row: dict[str, Any]) -> str:
    return "coverage_uncertain_or_conflicted" if row.get("uncertainty_flags") else "coverage_clean_numeric_geometry"


def contact_bucket(row: dict[str, Any]) -> str:
    if row.get("near_contact") or row.get("loose_near_contact") or row.get("projected_overlap_support"):
        return "contact_or_overlap_like"
    if row.get("far_separated"):
        return "far_no_contact"
    return "mid_or_unknown_contact"


def normalized_candidate(row: dict[str, Any]) -> dict[str, Any]:
    prediction_id = str(row.get("prediction_id") or "")
    predicate = norm(row.get("predicate_label"))
    subject_label = norm(row.get("subject_label"))
    object_label = norm(row.get("object_label"))
    role = proxy_role({**row, "predicate_label": predicate})
    qid = query_id(predicate, role)
    subject_family = row.get("subject_family") or coarse_family(subject_label)
    object_family = row.get("object_family") or coarse_family(object_label)
    candidate_id = "h2pa_" + stable_hash(prediction_id)[:12]
    rank_band = row.get("rank_band_hidden")
    out = {
        "candidate_id": candidate_id,
        "packet_request_id": "asset_" + stable_hash("packet|" + prediction_id)[:12],
        "prediction_id": prediction_id,
        "scan_id": row.get("scan_id"),
        "subgraph_id": row.get("subgraph_id"),
        "directed_pair_id": row.get("directed_pair_id"),
        "subject_id": row.get("subject_id"),
        "object_id": row.get("object_id"),
        "subject_label": subject_label,
        "predicate_label": predicate,
        "object_label": object_label,
        "visible_endpoint_pair": row.get("visible_endpoint_pair") or f"{subject_label}|{object_label}",
        "subject_family": subject_family,
        "object_family": object_family,
        "object_family_pair": row.get("object_family_pair") or f"{subject_family}|{object_family}",
        "selection_proxy_role_hidden": role,
        "query_id": qid,
        "rank_band_hidden": rank_band,
        "semantic_rank_hidden": row.get("semantic_rank_hidden"),
        "semantic_score_norm_hidden": row.get("semantic_score_norm_hidden"),
        "cell_id_hidden": row.get("cell_id_hidden"),
        "provisional_status_hidden": row.get("provisional_status_hidden"),
        "anchor_bucket_hidden": row.get("anchor_bucket_hidden"),
        "label_match_status_hidden": row.get("label_match_status_hidden"),
        "matched_predicates_hidden": row.get("matched_predicates_hidden"),
        "source_artifacts_hidden": sorted(row.get("_source_artifacts", [])),
        "capacity_evidence_tier_hidden": row.get("capacity_evidence_tier"),
        "near_contact": bool(row.get("near_contact")),
        "loose_near_contact": bool(row.get("loose_near_contact")),
        "far_separated": bool(row.get("far_separated")),
        "projected_overlap_support": bool(row.get("projected_overlap_support")),
        "uncertainty_flags": row.get("uncertainty_flags") or [],
        "coverage_tier": coverage_tier(row),
        "contact_bucket": contact_bucket(row),
        "hash_order": stable_int(prediction_id),
    }
    out["mixed_endpoint_family_rank_coverage_key"] = "|".join(
        [
            out["predicate_label"],
            out["object_family_pair"],
            str(out["rank_band_hidden"]),
            out["coverage_tier"],
        ]
    )
    out["visible_pair_key"] = f"{out['predicate_label']}|{out['visible_endpoint_pair']}"
    out["same_scene_family_rank_key"] = "|".join(
        [out["predicate_label"], str(out["scan_id"]), out["object_family_pair"], str(out["rank_band_hidden"])]
    )
    return out


def load_seed_pool() -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source_name, path in [("v18_attachment_candidate_mining", V18_ROWS), ("v20_attachment_preview_400", V20_ROWS)]:
        for raw in read_jsonl(path):
            prediction_id = str(raw.get("prediction_id") or "")
            if not prediction_id:
                continue
            target = merged.setdefault(prediction_id, {"_source_artifacts": []})
            target["_source_artifacts"].append(source_name)
            for key, value in raw.items():
                current = target.get(key)
                if key not in target or current is None or current == "" or current == []:
                    target[key] = value
    rows = [normalized_candidate(row) for row in merged.values()]
    rows = [row for row in rows if row["query_id"] is not None]
    rows.sort(key=lambda row: row["hash_order"])
    return rows


def selected_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "selected_rows": len(rows),
        "query_counts": dict(Counter(row["query_id"] for row in rows)),
        "predicate_counts": dict(Counter(row["predicate_label"] for row in rows)),
        "role_counts": dict(Counter(row["selection_proxy_role_hidden"] for row in rows)),
        "rank_band_by_role": {
            f"{role}|{rank}": count
            for (role, rank), count in sorted(
                Counter((row["selection_proxy_role_hidden"], str(row["rank_band_hidden"])) for row in rows).items()
            )
        },
        "unique_scans": len({row["scan_id"] for row in rows}),
        "unique_subgraphs": len({row["subgraph_id"] for row in rows}),
        "unique_visible_endpoint_pairs": len({row["visible_endpoint_pair"] for row in rows}),
    }


def init_selection_state() -> dict[str, Any]:
    return {
        "rows": [],
        "ids": set(),
        "query_counts": Counter(),
        "scan_counts": Counter(),
        "visible_pair_counts": Counter(),
        "route_counts": Counter(),
        "skip_reasons": Counter(),
    }


def can_add(row: dict[str, Any], state: dict[str, Any]) -> str | None:
    qid = row["query_id"]
    if qid is None:
        return "unsupported_query"
    if row["prediction_id"] in state["ids"]:
        return "duplicate_prediction_id"
    if state["query_counts"][qid] >= QUOTAS.get(qid, 0):
        return "query_quota_full"
    if state["scan_counts"][str(row["scan_id"])] >= 24:
        return "scan_cap"
    if state["visible_pair_counts"][row["visible_endpoint_pair"]] >= 8:
        return "visible_pair_cap"
    return None


def add_row(row: dict[str, Any], state: dict[str, Any], route: str, contrast_pair_id: str = "") -> bool:
    reason = can_add(row, state)
    if reason is not None:
        state["skip_reasons"][f"{route}:{reason}"] += 1
        return False
    row = {**row, "selection_route": route, "contrast_pair_id_hidden": contrast_pair_id}
    state["rows"].append(row)
    state["ids"].add(row["prediction_id"])
    state["query_counts"][row["query_id"]] += 1
    state["scan_counts"][str(row["scan_id"])] += 1
    state["visible_pair_counts"][row["visible_endpoint_pair"]] += 1
    state["route_counts"][route] += 1
    return True


def group_rows(rows: list[dict[str, Any]], fields: tuple[str, ...]) -> dict[tuple[Any, ...], dict[str, list[dict[str, Any]]]]:
    groups: dict[tuple[Any, ...], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["predicate_label"] not in {"attached to", "hanging on"}:
            continue
        if row["selection_proxy_role_hidden"] not in {ROLE_POSITIVE, ROLE_NEGATIVE}:
            continue
        key = tuple([row["predicate_label"], *[row.get(field) for field in fields]])
        groups[key][row["selection_proxy_role_hidden"]].append(row)
    for role_rows in groups.values():
        for values in role_rows.values():
            values.sort(key=lambda item: item["hash_order"])
    return groups


def consume_mixed_groups(
    rows: list[dict[str, Any]],
    state: dict[str, Any],
    fields: tuple[str, ...],
    route: str,
) -> None:
    groups = group_rows(rows, fields)
    ordered = sorted(
        groups.items(),
        key=lambda item: (
            -min(len(item[1].get(ROLE_POSITIVE, [])), len(item[1].get(ROLE_NEGATIVE, []))),
            str(item[0]),
        ),
    )
    for key, role_rows in ordered:
        positives = role_rows.get(ROLE_POSITIVE, [])
        negatives = role_rows.get(ROLE_NEGATIVE, [])
        for idx, (positive, negative) in enumerate(zip(positives, negatives)):
            pair_id = "ctr_" + stable_hash(route + "|" + repr(key) + "|" + str(idx))[:12]
            add_row(positive, state, route, pair_id)
            add_row(negative, state, route, pair_id)


def mine_candidates(seed_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    state = init_selection_state()

    consume_mixed_groups(seed_rows, state, ("object_family_pair", "rank_band_hidden", "coverage_tier"), "mixed_endpoint_family_rank_coverage")
    consume_mixed_groups(seed_rows, state, ("object_family_pair", "rank_band_hidden"), "mixed_endpoint_family_rank")
    consume_mixed_groups(seed_rows, state, ("visible_endpoint_pair",), "mixed_visible_pair")
    consume_mixed_groups(seed_rows, state, ("scan_id", "object_family_pair", "rank_band_hidden"), "mixed_same_scene_family_rank")

    for row in sorted(seed_rows, key=lambda item: item["hash_order"]):
        if row["query_id"] == "Q6_primary_uncertain_buffer":
            continue
        add_row(row, state, "global_hash_fill_after_mixed_strata")

    for row in sorted(seed_rows, key=lambda item: item["hash_order"]):
        if len(state["rows"]) >= TARGET_ROWS:
            break
        if row["query_id"] == "Q6_primary_uncertain_buffer":
            add_row(row, state, "primary_uncertain_capacity_buffer")

    rows = state["rows"]
    rows.sort(key=lambda row: (row["query_id"], row["selection_route"], row["hash_order"]))
    pair_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        if row["contrast_pair_id_hidden"]:
            pair_counts[row["contrast_pair_id_hidden"]][row["selection_proxy_role_hidden"]] += 1
    complete_pairs = sum(1 for counter in pair_counts.values() if counter[ROLE_POSITIVE] > 0 and counter[ROLE_NEGATIVE] > 0)

    selection = {
        "target_rows": TARGET_ROWS,
        "selected_rows": len(rows),
        "primary_binary_target": PRIMARY_BINARY_TARGET,
        "primary_binary_selected": sum(
            1
            for row in rows
            if row["predicate_label"] in {"attached to", "hanging on"}
            and row["selection_proxy_role_hidden"] in {ROLE_POSITIVE, ROLE_NEGATIVE}
        ),
        "primary_uncertain_buffer_selected": sum(1 for row in rows if row["query_id"] == "Q6_primary_uncertain_buffer"),
        "diagnostic_selected": sum(1 for row in rows if row["predicate_label"] == "connected to"),
        "query_counts": dict(state["query_counts"]),
        "route_counts": dict(state["route_counts"]),
        "skip_reasons": dict(state["skip_reasons"]),
        "contrast_pair_count": len(pair_counts),
        "complete_positive_negative_contrast_pairs": complete_pairs,
    }
    return rows, selection


def mixed_strata_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = [
        ("endpoint_family_rank_coverage", ["predicate_label", "object_family_pair", "rank_band_hidden", "coverage_tier"]),
        ("endpoint_family_rank", ["predicate_label", "object_family_pair", "rank_band_hidden"]),
        ("visible_pair", ["predicate_label", "visible_endpoint_pair"]),
        ("rank_band", ["predicate_label", "rank_band_hidden"]),
        ("same_scene", ["predicate_label", "scan_id"]),
        ("same_scene_endpoint_family_rank", ["predicate_label", "scan_id", "object_family_pair", "rank_band_hidden"]),
    ]
    out: list[dict[str, Any]] = []
    primary = [
        row
        for row in rows
        if row["predicate_label"] in {"attached to", "hanging on"}
        and row["selection_proxy_role_hidden"] in {ROLE_POSITIVE, ROLE_NEGATIVE}
    ]
    for spec_name, fields in specs:
        grouped: dict[tuple[Any, ...], Counter[str]] = defaultdict(Counter)
        for row in primary:
            grouped[tuple(row.get(field) for field in fields)][row["selection_proxy_role_hidden"]] += 1
        mixed = {key: counter for key, counter in grouped.items() if counter[ROLE_POSITIVE] and counter[ROLE_NEGATIVE]}
        out.append(
            {
                "stratum": spec_name,
                "groups": len(grouped),
                "mixed_groups": len(mixed),
                "balanced_rows": sum(2 * min(counter[ROLE_POSITIVE], counter[ROLE_NEGATIVE]) for counter in mixed.values()),
                "top_mixed_examples": json.dumps(
                    [
                        {"key": list(key), "positive": counter[ROLE_POSITIVE], "negative": counter[ROLE_NEGATIVE]}
                        for key, counter in sorted(
                            mixed.items(),
                            key=lambda item: (-min(item[1][ROLE_POSITIVE], item[1][ROLE_NEGATIVE]), str(item[0])),
                        )[:8]
                    ],
                    ensure_ascii=False,
                ),
            }
        )
    return out


def visible_rows(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    for row in rows:
        output.append(
            {
                "candidate_id": row["candidate_id"],
                "packet_request_id": row["packet_request_id"],
                "subject_label": row["subject_label"],
                "predicate_label": row["predicate_label"],
                "object_label": row["object_label"],
                "reviewer_visible_relation_text": f"{row['subject_label']} {row['predicate_label']} {row['object_label']}",
                "packet_status_expected": "needs_packet_materialization",
                "review_relation_reliability": "",
                "review_geometry_support": "",
                "review_endpoint_identity": "",
                "review_coverage": "",
                "review_uncertainty": "",
                "review_notes": "",
            }
        )
    return output


def hidden_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hidden: list[dict[str, Any]] = []
    for row in rows:
        hidden.append(
            {
                "candidate_id": row["candidate_id"],
                "packet_request_id": row["packet_request_id"],
                "prediction_id": row["prediction_id"],
                "scan_id": row["scan_id"],
                "subgraph_id": row["subgraph_id"],
                "directed_pair_id": row["directed_pair_id"],
                "subject_id": row["subject_id"],
                "object_id": row["object_id"],
                "query_id": row["query_id"],
                "selection_route": row["selection_route"],
                "contrast_pair_id_hidden": row["contrast_pair_id_hidden"],
                "selection_proxy_role_hidden": row["selection_proxy_role_hidden"],
                "rank_band_hidden": row["rank_band_hidden"],
                "semantic_rank_hidden": row["semantic_rank_hidden"],
                "semantic_score_norm_hidden": row["semantic_score_norm_hidden"],
                "cell_id_hidden": row["cell_id_hidden"],
                "provisional_status_hidden": row["provisional_status_hidden"],
                "anchor_bucket_hidden": row["anchor_bucket_hidden"],
                "label_match_status_hidden": row["label_match_status_hidden"],
                "matched_predicates_hidden": row["matched_predicates_hidden"],
                "capacity_evidence_tier_hidden": row["capacity_evidence_tier_hidden"],
                "source_artifacts_hidden": row["source_artifacts_hidden"],
                "mixed_endpoint_family_rank_coverage_key": row["mixed_endpoint_family_rank_coverage_key"],
                "visible_pair_key": row["visible_pair_key"],
                "same_scene_family_rank_key": row["same_scene_family_rank_key"],
            }
        )
    return hidden


def asset_request_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "asset_request_id": row["packet_request_id"],
            "candidate_id": row["candidate_id"],
            "scan_id": row["scan_id"],
            "subgraph_id": row["subgraph_id"],
            "subject_id": row["subject_id"],
            "object_id": row["object_id"],
            "subject_label": row["subject_label"],
            "predicate_label": row["predicate_label"],
            "object_label": row["object_label"],
            "requested_packet_components": [
                "subject_crop",
                "object_crop",
                "pair_context_sheet",
                "mesh_or_contact_context",
            ],
            "packet_materialization_status": "pending",
        }
        for row in rows
    ]


def sanitized_candidate_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    safe: list[dict[str, Any]] = []
    for row in rows:
        safe.append(
            {
                "candidate_id": row["candidate_id"],
                "packet_request_id": row["packet_request_id"],
                "split": "train",
                "T_e": {
                    "subject_label": row["subject_label"],
                    "predicate_label": row["predicate_label"],
                    "object_label": row["object_label"],
                    "subject_family": row["subject_family"],
                    "object_family": row["object_family"],
                },
                "G_e_seed": {
                    "near_contact": row["near_contact"],
                    "loose_near_contact": row["loose_near_contact"],
                    "far_separated": row["far_separated"],
                    "projected_overlap_support": row["projected_overlap_support"],
                    "contact_bucket": row["contact_bucket"],
                },
                "Q_e_seed": {
                    "coverage_tier": row["coverage_tier"],
                    "uncertainty_flags": row["uncertainty_flags"],
                    "packet_status_expected": "needs_packet_materialization",
                },
                "selection_public": {
                    "query_id": row["query_id"],
                    "packet_required": True,
                    "label_fields_blank": True,
                },
            }
        )
    return safe


def validate(plan: dict[str, Any], rows: list[dict[str, Any]], visible: list[dict[str, str]]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if plan.get("status") != EXPECTED_PLAN_STATUS:
        errors.append({"error_type": "unexpected_plan_status", "actual": plan.get("status")})
    if plan.get("next_todo") != EXPECTED_PLAN_NEXT:
        errors.append({"error_type": "unexpected_plan_next", "actual": plan.get("next_todo")})
    if plan.get("validation_errors") != 0:
        errors.append({"error_type": "plan_validation_errors_present", "actual": plan.get("validation_errors")})
    if len(rows) != TARGET_ROWS:
        errors.append({"error_type": "selected_row_count_mismatch", "expected": TARGET_ROWS, "actual": len(rows)})
    ids = [row["prediction_id"] for row in rows]
    if len(ids) != len(set(ids)):
        errors.append({"error_type": "duplicate_prediction_ids"})
    visible_header = set(visible[0].keys() if visible else [])
    for field in visible_header:
        lowered = field.lower()
        for pattern in FORBIDDEN_VISIBLE_PATTERNS:
            if pattern in lowered:
                errors.append({"error_type": "hidden_pattern_in_visible_header", "field": field, "pattern": pattern})
    hidden_values = ["source", "rank", "proxy", "cell_id", "score", "label_match"]
    for row in visible:
        text = " ".join(str(value).lower() for value in row.values())
        for value in hidden_values:
            if value in text:
                errors.append({"error_type": "hidden_value_in_visible_row", "candidate_id": row["candidate_id"], "value": value})
                break
    return errors


def write_report(path: Path, summary: dict[str, Any]) -> None:
    selection = summary["selection"]
    lines = [
        "# H002 Attachment Independent Positive Anchor Candidate Mining V1",
        "",
        f"Created at: `{summary['created_at_utc']}`",
        "",
        "## Status",
        "",
        "```text",
        f"status = {summary['status']}",
        f"selected_rows = {selection['selected_rows']}",
        f"primary_binary_selected = {selection['primary_binary_selected']}",
        f"primary_uncertain_buffer_selected = {selection['primary_uncertain_buffer_selected']}",
        f"diagnostic_selected = {selection['diagnostic_selected']}",
        f"complete_positive_negative_contrast_pairs = {selection['complete_positive_negative_contrast_pairs']}",
        f"next_todo = {summary['next_todo']}",
        f"validation_errors = {summary['validation_errors']}",
        "```",
        "",
        "## Interpretation",
        "",
        "This mining step does not simply collect more positive rows. It first selects positive anchors with matched hard negatives inside mixed strata, then fills remaining capacity by deterministic hash order without using source score as a selection criterion.",
        "",
        "The 560-row sheet contains 467 primary binary seed rows, 13 primary uncertain buffer rows, and 80 connected-to diagnostic rows. The 13-row buffer exists because the already materialized v18/v20 seed pools contain 467 unique attached/hanging positive-or-negative rows after de-duplication, not the full requested 480.",
        "",
        "## Query Counts",
        "",
        "```text",
    ]
    for key, value in sorted(selection["query_counts"].items()):
        lines.append(f"{key} = {value}")
    lines.extend(
        [
            "```",
            "",
            "## Mixed-Strata Principle",
            "",
            "| Positive anchor | Required contrast | Implementation |",
            "| --- | --- | --- |",
            "| clear hanging on accept | similar object pair with no actual contact | `Q1` paired with `Q2` inside endpoint-family/rank/coverage or visible-pair strata |",
            "| clear attached to accept | close but not attached | `Q3` paired with `Q4` inside the same mixed strata |",
            "| wall-object accept | wall-object reject | tracked through visible-pair and endpoint-family mixed groups |",
            "| high-rank accept | high-rank reject | rank band is a control axis, not a selection score |",
            "| visible accept | visible reject | packet materialization is requested for both sides of each contrast |",
            "| same-scene accept | same or similar scene reject | same-scene mixed strata are reported separately |",
            "",
            "## Boundary",
            "",
            "- train split only;",
            "- no posterior training;",
            "- no validation/test usage;",
            "- multi-view/mesh is still audit evidence, not model input;",
            "- source score/rank/proxy/cell/prior label fields are hidden from the review template;",
            "- `connected to` remains diagnostic-only.",
            "",
            "## Next",
            "",
            f"`{summary['next_todo']}`",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    plan = read_json(PLAN_DIR / "summary.json")
    seed_rows = load_seed_pool()
    selected, selection = mine_candidates(seed_rows)
    visible = visible_rows(selected)
    hidden = hidden_rows(selected)
    asset_requests = asset_request_rows(selected)
    safe_rows = sanitized_candidate_rows(selected)
    strata = mixed_strata_summary(selected)
    validation_errors = validate(plan, selected, visible)

    status = STATUS_ERROR if validation_errors else STATUS_READY
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "mixed_strata_candidate_mining_before_packet_materialization",
        "next_todo": NEXT_TODO if not validation_errors else EXPECTED_PLAN_NEXT,
        "validation_errors": len(validation_errors),
        "seed_pool": {
            "input_paths": {
                "v18_selected_candidates": rel_path(V18_ROWS),
                "v20_preview_400": rel_path(V20_ROWS),
            },
            "seed_rows_after_dedup": len(seed_rows),
            "seed_counts": selected_counts(seed_rows),
        },
        "selection": selection,
        "selected_counts": selected_counts(selected),
        "mixed_strata_summary": strata,
        "boundary": {
            "split": "train_only",
            "validation_usage": False,
            "test_usage": False,
            "fills_new_labels": False,
            "materializes_packets": False,
            "trains_new_posterior": False,
            "posterior_smoke_allowed": False,
            "paper_evidence_allowed": False,
            "h001_artifacts_modified": False,
            "multi_view_as_model_input": False,
            "mesh_as_model_input": False,
            "source_score_or_rank_used_for_selection": False,
            "source_score_or_rank_hidden_from_labeler": True,
        },
        "output_paths": {
            "summary": rel_path(OUT_DIR / "summary.json"),
            "report": rel_path(OUT_DIR / "report.md"),
            "candidate_rows": rel_path(OUT_DIR / "candidate_rows.jsonl"),
            "candidate_rows_internal": rel_path(OUT_DIR / "candidate_rows_internal.jsonl"),
            "hidden_manifest": rel_path(OUT_DIR / "hidden_manifest.jsonl"),
            "visible_review_template": rel_path(OUT_DIR / "visible_review_template.csv"),
            "asset_request_manifest": rel_path(OUT_DIR / "asset_request_manifest.jsonl"),
            "mixed_strata_summary": rel_path(OUT_DIR / "mixed_strata_summary.csv"),
            "validation_errors": rel_path(OUT_DIR / "validation_errors.jsonl"),
        },
    }

    write_json(OUT_DIR / "summary.json", summary)
    write_jsonl(OUT_DIR / "candidate_rows.jsonl", safe_rows)
    write_jsonl(OUT_DIR / "candidate_rows_internal.jsonl", selected)
    write_jsonl(OUT_DIR / "hidden_manifest.jsonl", hidden)
    write_csv(OUT_DIR / "visible_review_template.csv", visible, VISIBLE_FIELDS)
    write_jsonl(OUT_DIR / "asset_request_manifest.jsonl", asset_requests)
    write_csv(OUT_DIR / "mixed_strata_summary.csv", strata)
    write_jsonl(OUT_DIR / "validation_errors.jsonl", validation_errors)
    write_report(OUT_DIR / "report.md", summary)

    print(f"status={summary['status']}")
    print(f"selected_rows={selection['selected_rows']}")
    print(f"primary_binary_selected={selection['primary_binary_selected']}")
    print(f"primary_uncertain_buffer_selected={selection['primary_uncertain_buffer_selected']}")
    print(f"diagnostic_selected={selection['diagnostic_selected']}")
    print(f"complete_positive_negative_contrast_pairs={selection['complete_positive_negative_contrast_pairs']}")
    print(f"next={summary['next_todo']}")
    print(f"validation_errors={summary['validation_errors']}")


if __name__ == "__main__":
    main()
