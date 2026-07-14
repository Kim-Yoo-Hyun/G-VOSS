#!/usr/bin/env python3
"""Freeze and audit the attachment-subtype v2 design.

This stage deliberately does not fit a calibrator or compute source metrics.  It
separates predicate semantics, physical mechanism, and evidence observability,
then migrates the existing train/dev audit rows and summarizes the official
validation evidence coverage under the new routing contract.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h001_attachment_subtype_redesign_v2"
STATUS = "attachment_subtype_v2_frozen_no_refit_no_source_metrics"
PREDICATES = ("attached to", "hanging on", "connected to")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid_jsonl:{path}:{line_number}:{exc}") from exc


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
            count += 1
    return count


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def nested_counter_to_dict(value: Any) -> Any:
    if isinstance(value, Counter):
        return {str(k): nested_counter_to_dict(v) for k, v in sorted(value.items())}
    if isinstance(value, defaultdict):
        return {str(k): nested_counter_to_dict(v) for k, v in sorted(value.items())}
    if isinstance(value, dict):
        return {str(k): nested_counter_to_dict(v) for k, v in sorted(value.items())}
    return value


def evidence_snapshot(evidence: dict[str, Any]) -> dict[str, Any]:
    point = evidence.get("point_contact_evidence", {})
    surface = evidence.get("surface_evidence", {})
    gravity = evidence.get("gravity_evidence", {})
    support = evidence.get("contradictory_support_evidence", {})
    available = evidence.get("geometry_available", {})
    return {
        "extractor_status": evidence.get("extractor_status"),
        "points_available": bool(available.get("points")),
        "normals_available": bool(available.get("normals")),
        "surface_candidates_available": bool(available.get("surface_candidates")),
        "surface_type": surface.get("selected_surface_type") or "unknown",
        "surface_normal_class": surface.get("selected_surface_normal_class") or "unknown",
        "min_point_distance_m": point.get("min_point_distance_m"),
        "near_contact_point_count": point.get("near_contact_point_count"),
        "contact_patch_score": point.get("contact_patch_score"),
        "floor_clearance_m": gravity.get("floor_clearance_m"),
        "hanging_geometry_score": gravity.get("hanging_geometry_score"),
        "floor_or_table_supported": support.get("floor_or_table_supported"),
        "support_explanation_score": support.get("support_explanation_score"),
    }


def contact_observed(snapshot: dict[str, Any]) -> bool:
    distance = snapshot.get("min_point_distance_m")
    count = snapshot.get("near_contact_point_count")
    patch = snapshot.get("contact_patch_score")
    return bool(
        distance is not None
        and float(distance) <= 0.05
        and ((count is not None and int(count) >= 3) or (patch is not None and float(patch) >= 0.20))
    )


def route_evidence(evidence: dict[str, Any]) -> dict[str, str]:
    predicate = str(evidence.get("predicate_label", ""))
    snap = evidence_snapshot(evidence)
    surface = str(snap["surface_type"])
    normal = str(snap["surface_normal_class"])
    ready = (
        snap["extractor_status"] == "ready"
        and snap["points_available"]
        and snap["normals_available"]
        and snap["surface_candidates_available"]
    )

    if not ready:
        return {
            "mechanism": "unresolved",
            "observability": "insufficient_geometry",
            "applicability": "abstain",
            "route_reason": "required_point_normal_or_surface_evidence_missing",
        }

    if predicate == "attached to":
        if surface in {"wall", "ceiling"} and normal in {
            "vertical",
            "horizontal_down",
            "slanted",
        }:
            mechanism = "planar_surface_attachment"
        elif surface in {"fixture", "furniture", "object_part"}:
            mechanism = "object_or_fixture_attachment"
        else:
            return {
                "mechanism": "attachment_mechanism_unresolved",
                "observability": "mechanism_unresolved",
                "applicability": "abstain",
                "route_reason": "endpoint_surface_does_not_identify_physical_attachment_mechanism",
            }
        return {
            "mechanism": mechanism,
            "observability": "directly_observable",
            "applicability": "bidirectional_compatibility",
            "route_reason": "physical_support_surface_and_required_geometry_observed",
        }

    if predicate == "hanging on":
        if surface == "ceiling" or normal == "horizontal_down":
            mechanism = "overhead_suspension"
        elif surface in {"wall", "fixture", "furniture", "object_part"} or normal in {
            "vertical",
            "slanted",
        }:
            mechanism = "vertical_surface_suspension"
        else:
            return {
                "mechanism": "suspension_mechanism_unresolved",
                "observability": "mechanism_unresolved",
                "applicability": "abstain",
                "route_reason": "support_surface_does_not_identify_vertical_or_overhead_suspension",
            }
        return {
            "mechanism": mechanism,
            "observability": "directly_observable",
            "applicability": "bidirectional_compatibility",
            "route_reason": "suspension_surface_gravity_and_support_evidence_observed",
        }

    if predicate == "connected to":
        if contact_observed(snap):
            return {
                "mechanism": "direct_contiguous_connection",
                "observability": "positive_evidence_only",
                "applicability": "positive_compatibility_only",
                "route_reason": "direct_contact_is_positive_evidence_but_contact_absence_cannot_refute_hidden_connection",
            }
        return {
            "mechanism": "connection_mechanism_unresolved",
            "observability": "mediator_or_path_unobserved",
            "applicability": "abstain",
            "route_reason": "connection_may_be_mediated_by_unsegmented_cable_pipe_or_fixture",
        }

    return {
        "mechanism": "unresolved",
        "observability": "unsupported_predicate",
        "applicability": "abstain",
        "route_reason": "predicate_outside_frozen_attachment_scope",
    }


def taxonomy_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "design_goal": (
            "Separate predicate semantics, physical mechanism, and observability so that "
            "ambiguity is not treated as a physical subtype or a calibration label."
        ),
        "axes": {
            "predicate_semantics_T": list(PREDICATES),
            "physical_mechanism_M": {
                "attached to": [
                    "planar_surface_attachment",
                    "object_or_fixture_attachment",
                    "attachment_mechanism_unresolved",
                ],
                "hanging on": [
                    "vertical_surface_suspension",
                    "overhead_suspension",
                    "suspension_mechanism_unresolved",
                ],
                "connected to": [
                    "direct_contiguous_connection",
                    "connection_mechanism_unresolved",
                ],
            },
            "observability_Q": [
                "directly_observable",
                "positive_evidence_only",
                "mediator_or_path_unobserved",
                "mechanism_unresolved",
                "insufficient_geometry",
            ],
            "applicability_A": [
                "bidirectional_compatibility",
                "positive_compatibility_only",
                "abstain",
            ],
        },
        "compatibility_contract": {
            "bidirectional_compatibility": (
                "May provide positive and negative calibration examples after mechanism review."
            ),
            "positive_compatibility_only": (
                "May reward directly observed contact but may not infer violation from absent contact."
            ),
            "abstain": (
                "Do not create a compatibility target or demote the source score; report coverage separately."
            ),
            "neutral_fallback": "m(e)=1 for abstained rows, so S(e)=Z(e).",
            "bounded_direct_multiplier": (
                "For the development diagnostic, directly observable rows use "
                "m(e)=0.5+C(e), yielding a parameter-free [0.5,1.5] multiplier "
                "with neutral point C=0.5."
            ),
        },
        "leakage_boundary": {
            "forbidden_inputs": [
                "source_score",
                "source_rank",
                "source_id",
                "p_geom_valid from the legacy calibrator",
                "object-class-only validity shortcuts",
            ],
            "class_context_rule": (
                "Endpoint class may identify a candidate surface category for routing, but is never "
                "sufficient evidence of validity."
            ),
        },
        "promotion_boundary": {
            "current_main_claim_changed": False,
            "requires_before_refit": [
                "blind mechanism/observability review of the frozen queue",
                "train/internal-dev coverage for every promoted mechanism",
                "policy targets constructed independently of the final Violation verifier",
                "source metrics and paired family-wise confidence intervals after a new model hash",
            ],
            "connected_to_rule": (
                "Do not fit a bidirectional connected-to calibrator until the annotation ontology "
                "distinguishes direct from mediated connections."
            ),
        },
    }


def controls_payload() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "global_controls": [
            "identity-preserving same-pair geometry join",
            "wrong-pair geometry",
            "shuffled geometry within split",
            "no source score/rank input to compatibility or applicability",
            "report applicability coverage and abstention rate with Recall and Violation",
        ],
        "mechanism_controls": {
            "planar_surface_attachment": [
                "far displacement from the same support surface",
                "wrong-surface replacement",
                "surface-normal contradiction",
            ],
            "object_or_fixture_attachment": [
                "far displacement",
                "wrong-pair fixture geometry",
                "mediator-hidden case routed to abstain",
            ],
            "vertical_surface_suspension": [
                "gravity-inconsistent displacement",
                "floor/table-support replacement",
                "vertical-surface normal rotation",
            ],
            "overhead_suspension": [
                "overhead-to-floor support replacement",
                "gravity-inconsistent displacement",
                "ceiling/fixture removal or gap insertion",
            ],
            "direct_contiguous_connection": [
                "gap insertion",
                "wrong-pair geometry",
                "endpoint swap only after ontology symmetry is independently confirmed",
            ],
        },
        "forbidden_blanket_controls": {
            "endpoint_swap": (
                "No blanket endpoint swap: attached-to and hanging-on are directional, and "
                "connected-to symmetry must be confirmed from the dataset ontology first."
            )
        },
    }


def load_evidence_by_row(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for row in iter_jsonl(path):
        row_id = row.get("row_id")
        if row_id:
            rows[str(row_id)] = row
    return rows


def migrate_train_dev(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    evidence_by_row = load_evidence_by_row(root / "gt_policy_smoke/gt_evidence_rows.jsonl")
    review_by_row = {
        str(row["row_id"]): row
        for row in iter_jsonl(root / "error_visual_sanity/review_cases.jsonl")
        if row.get("row_id")
    }

    eval_rows = list(iter_jsonl(root / "gt_policy_smoke/gt_eval_rows.jsonl"))
    counterfactual_base = {
        str(row["negative_id"]): str(row["base_positive_seed_id"])
        for row in iter_jsonl(
            root / "calibration_counterfactuals/counterfactual_seeds.jsonl"
        )
    }
    positive_route: dict[str, dict[str, str]] = {}
    positive_legacy_subtype: dict[str, str] = {}
    for eval_row in eval_rows:
        if int(eval_row.get("target_geom_valid", -1)) != 1:
            continue
        decision = eval_row["decision"]
        row_id = str(decision["row_id"])
        evidence = evidence_by_row.get(row_id)
        if evidence is None:
            raise ValueError(f"missing_evidence_for_positive_eval_row:{row_id}")
        seed_id = str(eval_row["seed_id"])
        positive_route[seed_id] = route_evidence(evidence)
        positive_legacy_subtype[seed_id] = str(
            decision.get("subtype_hint", "unknown")
        )

    migrated: list[dict[str, Any]] = []
    counts: dict[str, Any] = {
        "by_predicate": Counter(),
        "by_legacy_subtype": Counter(),
        "by_mechanism": Counter(),
        "by_observability": Counter(),
        "by_applicability": Counter(),
        "by_migration_disposition": Counter(),
        "by_route_origin": Counter(),
        "by_predicate_applicability": defaultdict(Counter),
        "strict_candidate_by_split_predicate_target": defaultdict(Counter),
    }

    for eval_row in eval_rows:
        decision = eval_row["decision"]
        row_id = str(decision["row_id"])
        evidence = evidence_by_row.get(row_id)
        if evidence is None:
            raise ValueError(f"missing_evidence_for_eval_row:{row_id}")
        observed_route = route_evidence(evidence)
        target = int(eval_row.get("target_geom_valid", -1))
        base_seed_id = None
        if target == 0:
            base_seed_id = counterfactual_base.get(str(eval_row.get("seed_id")))
            if base_seed_id is None:
                raise ValueError(f"missing_counterfactual_lineage:{eval_row.get('seed_id')}")
            route = positive_route.get(base_seed_id)
            if route is None:
                raise ValueError(f"missing_positive_route:{base_seed_id}")
            route = dict(route)
            route["route_reason"] = (
                "counterfactual_inherits_physical_mechanism_and_applicability_from_base_positive;"
                + route["route_reason"]
            )
            route_origin = "base_positive_lineage"
            mechanism_source_legacy_subtype = positive_legacy_subtype.get(
                base_seed_id, "unknown"
            )
        else:
            route = observed_route
            route_origin = "positive_row_evidence"
            mechanism_source_legacy_subtype = str(
                decision.get("subtype_hint", "unknown")
            )
        review = review_by_row.get(row_id, {})
        legacy_subtype = str(decision.get("subtype_hint", "unknown"))
        case_type = str(review.get("case_type", "strict_or_unreviewed"))
        mechanism_source_ambiguous = mechanism_source_legacy_subtype.startswith(
            "ambiguous"
        )

        if route["applicability"] == "bidirectional_compatibility":
            if mechanism_source_ambiguous or case_type in {
                "false_satisfaction_counterfactual",
                "false_violation_positive",
                "uncertain_counterfactual",
                "uncertain_positive",
            }:
                disposition = "mechanism_review_required"
            else:
                disposition = "candidate_strict_calibration"
        elif route["applicability"] == "positive_compatibility_only":
            disposition = "positive_evidence_only_no_negative_target"
        else:
            disposition = "exclude_from_compatibility_fit"

        snap = evidence_snapshot(evidence)
        row = {
            "schema_version": SCHEMA_VERSION,
            "row_id": row_id,
            "seed_id": eval_row.get("seed_id"),
            "scan_id": decision.get("scan_id"),
            "subgraph_id": decision.get("subgraph_id"),
            "subject_id": decision.get("subject_id"),
            "object_id": decision.get("object_id"),
            "subject_label": evidence.get("subject_label"),
            "object_label": evidence.get("object_label"),
            "predicate_label": decision.get("predicate_label"),
            "split_role": eval_row.get("split_role"),
            "target_geom_valid": eval_row.get("target_geom_valid"),
            "counterfactual_strategy": eval_row.get("strategy"),
            "base_positive_seed_id": base_seed_id,
            "legacy_subtype": legacy_subtype,
            "legacy_verification_status": decision.get("verification_status"),
            "legacy_case_type": case_type,
            **route,
            "route_origin": route_origin,
            "observed_counterfactual_route": observed_route if target == 0 else None,
            "migration_disposition": disposition,
            "evidence_snapshot": snap,
        }
        migrated.append(row)

        predicate = str(row["predicate_label"])
        counts["by_predicate"][predicate] += 1
        counts["by_legacy_subtype"][legacy_subtype] += 1
        counts["by_mechanism"][route["mechanism"]] += 1
        counts["by_observability"][route["observability"]] += 1
        counts["by_applicability"][route["applicability"]] += 1
        counts["by_migration_disposition"][disposition] += 1
        counts["by_route_origin"][route_origin] += 1
        counts["by_predicate_applicability"][predicate][route["applicability"]] += 1
        if disposition == "candidate_strict_calibration":
            key = f"{row['split_role']}:{predicate}"
            counts["strict_candidate_by_split_predicate_target"][key][
                str(row["target_geom_valid"])
            ] += 1

    return migrated, nested_counter_to_dict(counts)


def audit_source_routes(root: Path) -> dict[str, Any]:
    shard_root = root / "full_validation_g5d/shards"
    counts: dict[str, Any] = {
        "rows": 0,
        "by_source": Counter(),
        "by_predicate": Counter(),
        "by_mechanism": Counter(),
        "by_observability": Counter(),
        "by_applicability": Counter(),
        "by_source_predicate_applicability": defaultdict(Counter),
    }
    evidence_files = sorted(shard_root.glob("*/evidence_rows.jsonl"))
    for path in evidence_files:
        for evidence in iter_jsonl(path):
            route = route_evidence(evidence)
            source = str(evidence.get("source_name", "unknown"))
            predicate = str(evidence.get("predicate_label", "unknown"))
            counts["rows"] += 1
            counts["by_source"][source] += 1
            counts["by_predicate"][predicate] += 1
            counts["by_mechanism"][route["mechanism"]] += 1
            counts["by_observability"][route["observability"]] += 1
            counts["by_applicability"][route["applicability"]] += 1
            counts["by_source_predicate_applicability"][f"{source}:{predicate}"][
                route["applicability"]
            ] += 1
    return {
        "evidence_files": len(evidence_files),
        **nested_counter_to_dict(counts),
    }


def make_review_queue(migrated: list[dict[str, Any]], limit: int = 100) -> list[dict[str, Any]]:
    priority = {
        "connected to": 0,
        "false_violation_positive": 1,
        "false_satisfaction_counterfactual": 2,
        "mechanism_review_required": 3,
        "exclude_from_compatibility_fit": 4,
    }

    def key(row: dict[str, Any]) -> tuple[Any, ...]:
        first = priority.get(str(row["predicate_label"]), 9)
        second = priority.get(str(row["legacy_case_type"]), 9)
        third = priority.get(str(row["migration_disposition"]), 9)
        return (first, second, third, str(row["scan_id"]), str(row["row_id"]))

    candidates = [
        row
        for row in migrated
        if row["migration_disposition"] != "candidate_strict_calibration"
        or row["predicate_label"] == "connected to"
    ]
    output: list[dict[str, Any]] = []
    for index, row in enumerate(sorted(candidates, key=key)[:limit], start=1):
        snap = row["evidence_snapshot"]
        output.append(
            {
                "item_id": f"attachment_v2_{index:04d}",
                "scan_id": row["scan_id"],
                "subgraph_id": row["subgraph_id"],
                "subject_id": row["subject_id"],
                "object_id": row["object_id"],
                "subject_label": row["subject_label"],
                "object_label": row["object_label"],
                "predicate_label": row["predicate_label"],
                "surface_type": snap["surface_type"],
                "surface_normal_class": snap["surface_normal_class"],
                "min_point_distance_m": snap["min_point_distance_m"],
                "near_contact_point_count": snap["near_contact_point_count"],
                "contact_patch_score": snap["contact_patch_score"],
                "floor_clearance_m": snap["floor_clearance_m"],
                "floor_or_table_supported": snap["floor_or_table_supported"],
                "mechanism_label": "",
                "observability_label": "",
                "evidence_sufficient": "",
                "confidence": "",
                "notes": "",
            }
        )
    return output


def write_review_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("empty_review_queue")
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def report_markdown(legacy: dict[str, Any]) -> str:
    train = legacy["train_dev_migration"]
    source = legacy["official_validation_route_audit"]
    return f"""# Attachment Subtype Redesign v2

Status: `{STATUS}`

## Outcome

The legacy nine-subtype design is replaced by three independent axes:
predicate semantics, physical mechanism, and observability/applicability.
Ambiguous, occluded, and functional cases are no longer physical subtypes or
automatic calibration targets.

This stage migrates and audits the existing artifacts only. It fits no model,
changes no source ranking, computes no new source metric, and does not expand
the RelCompat3D main claim.

## Audit

- migrated train/dev rows: {legacy['train_dev_rows']}
- legacy strict rows: {legacy['legacy_strict_rows']}
- legacy strict rows with an `ambiguous_*` subtype: {legacy['legacy_ambiguous_strict_rows']}
- v2 candidate strict-calibration rows before mechanism review: {train['by_migration_disposition'].get('candidate_strict_calibration', 0)}
- rows requiring mechanism review: {train['by_migration_disposition'].get('mechanism_review_required', 0)}
- official-validation evidence rows audited: {source['rows']}
- official-validation bidirectional-compatibility coverage: {source['by_applicability'].get('bidirectional_compatibility', 0)}
- official-validation positive-only coverage: {source['by_applicability'].get('positive_compatibility_only', 0)}
- official-validation abstained rows: {source['by_applicability'].get('abstain', 0)}

## Frozen Boundary

`attached to` and `hanging on` receive mechanism-specific direct-geometry
routes. `connected to` receives positive-only direct-contact evidence until the
dataset ontology distinguishes direct from mediated connections. Unresolved or
insufficient rows abstain and use a neutral compatibility factor rather than
being treated as violations.

No blanket endpoint swap is permitted. Attached-to and hanging-on are
directional; connected-to swap invariance is allowed only after an independent
ontology audit confirms symmetry.

## Next Gate

Complete the frozen mechanism/observability review queue, rebuild calibration
targets without legacy ambiguous-policy labels, verify nonempty train and
internal-dev support for every promoted mechanism, and only then freeze/refit a
v2 compatibility model. Source metrics remain blocked until that model hash and
its controls are frozen.
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--attachment-root",
        type=Path,
        default=Path(
            "archive/experiments/H001_geom_reliability/sources/attachment_deferred"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "archive/experiments/H001_geom_reliability/sources/attachment_deferred/subtype_redesign_v2"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    root = args.attachment_root
    if not root.is_absolute():
        root = repo_root / root
    out = args.out
    if not out.is_absolute():
        out = repo_root / out
    out.mkdir(parents=True, exist_ok=True)

    required = [
        root / "gt_policy_smoke/gt_evidence_rows.jsonl",
        root / "gt_policy_smoke/gt_eval_rows.jsonl",
        root / "calibration_counterfactuals/counterfactual_seeds.jsonl",
        root / "error_visual_sanity/review_cases.jsonl",
        root / "error_visual_sanity/summary.json",
        root / "strict_filter_freeze/summary.json",
        root / "full_validation_g5d/summary.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("missing_required_inputs:" + ",".join(missing))

    migrated, migration_counts = migrate_train_dev(root)
    source_counts = audit_source_routes(root)
    strict_summary = read_json(root / "strict_filter_freeze/summary.json")
    full_validation_summary = read_json(root / "full_validation_g5d/summary.json")
    legacy_ambiguous_strict = sum(
        int(count)
        for subtype, count in strict_summary["strict_by_subtype"].items()
        if str(subtype).startswith("ambiguous")
    )

    legacy_audit = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "diagnosis": [
            "Legacy subtype names mix physical mechanisms with ambiguity/observability states.",
            "Policy-selected ambiguous rows entered the legacy strict calibration subset.",
            "Connected-to has no strict dev rows and cannot support label-specific calibration.",
            "Near-perfect legacy strict-subset separation is not independent mechanism evidence.",
        ],
        "train_dev_rows": len(migrated),
        "legacy_strict_rows": int(strict_summary["strict_rows"]),
        "legacy_ambiguous_strict_rows": legacy_ambiguous_strict,
        "train_dev_migration": migration_counts,
        "official_validation_route_audit": source_counts,
        "official_validation_reference": {
            "expected_scored_rows": full_validation_summary["counts"]["scored_rows"],
            "validation_errors": full_validation_summary["counts"]["validation_errors"],
        },
    }

    queue = make_review_queue(migrated)
    write_json(out / "taxonomy.json", taxonomy_payload())
    write_json(out / "control_contract.json", controls_payload())
    write_json(out / "legacy_audit.json", legacy_audit)
    write_jsonl(out / "migration_rows.jsonl", migrated)
    write_review_csv(out / "mechanism_review_queue.csv", queue)
    (out / "README.md").write_text(report_markdown(legacy_audit), encoding="utf-8")
    (out / "commands.md").write_text(
        "# Commands\n\n"
        "```bash\n"
        "env UID=$(id -u) GID=$(id -g) docker compose -f configs/h001/compose.yaml "
        "run --rm attachment_subtype_redesign_v2\n"
        "```\n",
        encoding="utf-8",
    )

    validation_errors: list[str] = []
    if len(migrated) != 761:
        validation_errors.append(f"train_dev_row_count:{len(migrated)}!=761")
    if int(source_counts["rows"]) != int(full_validation_summary["counts"]["scored_rows"]):
        validation_errors.append(
            f"source_route_rows:{source_counts['rows']}!={full_validation_summary['counts']['scored_rows']}"
        )
    if legacy_ambiguous_strict != 199:
        validation_errors.append(f"legacy_ambiguous_strict:{legacy_ambiguous_strict}!=199")
    if migration_counts["by_predicate"].keys() != set(PREDICATES):
        validation_errors.append("predicate_coverage_mismatch")
    if len(queue) != 100:
        validation_errors.append(f"review_queue_rows:{len(queue)}!=100")
    if any(
        forbidden in (out / "mechanism_review_queue.csv").read_text(encoding="utf-8")
        for forbidden in ("semantic_score", "source_rank", "p_geom_valid", "target_geom_valid")
    ):
        validation_errors.append("review_queue_contains_forbidden_field")

    validation = {
        "schema_version": SCHEMA_VERSION,
        "status": "passed" if not validation_errors else "failed",
        "validation_error_count": len(validation_errors),
        "validation_errors": validation_errors,
        "checks": {
            "train_dev_rows": len(migrated),
            "official_validation_evidence_rows": source_counts["rows"],
            "legacy_ambiguous_strict_rows": legacy_ambiguous_strict,
            "review_queue_rows": len(queue),
            "blanket_endpoint_swap_forbidden": True,
            "model_fitted": False,
            "source_metrics_computed": False,
            "main_claim_changed": False,
        },
    }
    write_json(out / "validation.json", validation)

    artifact_names = [
        "README.md",
        "commands.md",
        "taxonomy.json",
        "control_contract.json",
        "legacy_audit.json",
        "migration_rows.jsonl",
        "mechanism_review_queue.csv",
        "validation.json",
    ]
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS if not validation_errors else "attachment_subtype_v2_failed_validation",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact_type": "attachment_subtype_design_and_migration_audit",
        "paper_result": False,
        "model_fitted": False,
        "source_metrics_computed": False,
        "main_claim_changed": False,
        "inputs": {str(path.relative_to(repo_root)): sha256(path) for path in required},
        "outputs": {
            name: {"sha256": sha256(out / name), "bytes": (out / name).stat().st_size}
            for name in artifact_names
        },
    }
    write_json(out / "manifest.json", manifest)

    if validation_errors:
        raise SystemExit("validation_failed:" + ",".join(validation_errors))
    print(json.dumps({"status": STATUS, "out": str(out), "validation_errors": 0}))


if __name__ == "__main__":
    main()
