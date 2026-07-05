#!/usr/bin/env python3
"""Create per-route H002 target manifests after schema freeze."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]

DEFAULT_SCHEMA_FREEZE_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review"
)
DEFAULT_OUTPUT_DIR = (
    H2_ROOT / "artifacts/compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze"
)

EXPECTED_SCHEMA_FREEZE_STATUS = (
    "h002_compatibility_dataset_v3_schema_freeze_and_promotion_protocol_after_route_coverage_review_ready"
)
EXPECTED_SCHEMA_FREEZE_NEXT = "compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze"

SCHEMA_VERSION = "h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_v1"
STATUS_READY = "h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_ready"
STATUS_ERRORS = "h002_compatibility_dataset_v3_route_specific_target_manifest_plan_after_schema_freeze_input_errors"
SELECTED_PATH = "freeze_per_route_target_manifests_select_manifest_consistency_audit"
NEXT_TODO = "compatibility_dataset_v3_route_specific_target_manifest_consistency_audit_after_plan"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema-freeze-dir", type=Path, default=DEFAULT_SCHEMA_FREEZE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    if not fields:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def validate_inputs(
    summary: dict[str, Any],
    route_rows: list[dict[str, str]],
    target_rows: list[dict[str, str]],
    schema_rows: list[dict[str, str]],
    schema_freeze_dir: Path,
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if summary.get("status") != EXPECTED_SCHEMA_FREEZE_STATUS:
        errors.append({"error_type": "unexpected_schema_freeze_status", "actual": summary.get("status")})
    if summary.get("next_todo") != EXPECTED_SCHEMA_FREEZE_NEXT:
        errors.append({"error_type": "unexpected_schema_freeze_next_todo", "actual": summary.get("next_todo")})
    if summary.get("validation_errors") != 0:
        errors.append({"error_type": "schema_freeze_validation_errors_present", "actual": summary.get("validation_errors")})
    validation_rows = read_jsonl(schema_freeze_dir / "validation_errors.jsonl")
    if validation_rows:
        errors.append({"error_type": "schema_freeze_validation_error_rows_present", "rows": len(validation_rows)})

    if len(route_rows) != 13:
        errors.append({"error_type": "unexpected_route_count", "actual": len(route_rows)})
    if len(target_rows) != len(route_rows):
        errors.append({"error_type": "target_route_count_mismatch", "routes": len(route_rows), "targets": len(target_rows)})
    required_schema_blocks = {"T_e", "Z_e", "G_e", "Q_e", "C_e", "labels", "hidden_construction"}
    observed_blocks = {row.get("block") for row in schema_rows}
    missing_blocks = sorted(required_schema_blocks - observed_blocks)
    if missing_blocks:
        errors.append({"error_type": "missing_schema_blocks", "missing": missing_blocks})

    route_by_family = {row.get("family"): row for row in route_rows}
    expected = {
        "proximity": "close by",
        "superordinate_support": "supported by",
        "attachment_observability": "attached to; hanging on; connected to",
        "identity_symmetry": "same as; same symmetry as",
        "semantic_structural": "part of; belonging to",
    }
    for family, relations in expected.items():
        if route_by_family.get(family, {}).get("relations") != relations:
            errors.append(
                {
                    "error_type": "route_redefinition_not_preserved",
                    "family": family,
                    "actual": route_by_family.get(family, {}).get("relations"),
                    "expected": relations,
                }
            )
    return errors


def route_slug(route_id: str, family: str) -> str:
    return f"{route_id.lower()}_{family}"


def route_target_manifest(route_rows: list[dict[str, str]], target_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    target_by_route = {row["route_id"]: row for row in target_rows}
    rows: list[dict[str, Any]] = []
    for row in route_rows:
        route_id = row["route_id"]
        target = target_by_route[route_id]
        family = row["family"]
        slug = route_slug(route_id, family)
        rows.append(
            {
                "route_id": route_id,
                "route_slug": slug,
                "route_type": row["route_type"],
                "family": family,
                "relations": row["relations"],
                "paper_role": row["paper_role"],
                "target_axis": target_axis(row["route_type"]),
                "label_space": label_space(row["route_type"]),
                "positive_definition": target["positive_definition"],
                "negative_definition": target["negative_definition"],
                "abstain_definition": target["abstain_definition"],
                "primary_metric": primary_metric(row["route_type"]),
                "secondary_metrics": secondary_metrics(row["route_type"]),
                "must_not_use_as_negative": must_not_use_as_negative(row["route_type"]),
                "artifact_root": f"artifacts/route_specific_targets/{slug}/",
                "model_safe_view": f"model_safe_{slug}.jsonl",
                "hidden_manifest": f"hidden_{slug}.jsonl",
                "audit_view": f"audit_{slug}.jsonl",
                "status": route_status(row["paper_role"]),
            }
        )
    return rows


def target_axis(route_type: str) -> str:
    mapping = {
        "geometry_only_learned_evaluated_route": "geometry_support",
        "predicate_geometry_interaction_route": "predicate_geometry_compatibility",
        "superordinate_support_decomposition_route": "accept_relabel_abstain",
        "observability_aware_route": "observability_then_reliability",
        "contact_orientation_feasibility_route": "contact_orientation_feasibility",
        "occlusion_coverage_feasibility_route": "occlusion_coverage_feasibility",
        "containment_feasibility_route": "containment_feasibility",
        "identity_symmetry_route": "identity_or_symmetry_compatibility",
        "semantic_structural_route": "semantic_structural_compatibility",
        "embedded_structure_feasibility_route": "embedded_structure_feasibility",
    }
    return mapping[route_type]


def label_space(route_type: str) -> str:
    mapping = {
        "geometry_only_learned_evaluated_route": "geometry_supported; geometry_unsupported; abstain",
        "predicate_geometry_interaction_route": "compatible; incompatible; abstain",
        "superordinate_support_decomposition_route": "accept_broad_support; relabel_to_subtype; reject_no_support; abstain",
        "observability_aware_route": "observable_accept; observable_reject; unobservable_abstain; functional_or_topology_uncertain",
        "contact_orientation_feasibility_route": "leaning_supported; leaning_unsupported; abstain",
        "occlusion_coverage_feasibility_route": "cover_supported; cover_unsupported; abstain",
        "containment_feasibility_route": "contained; not_contained; abstain",
        "identity_symmetry_route": "same_or_symmetric; not_same_or_not_symmetric; abstain",
        "semantic_structural_route": "structurally_supported; structurally_unsupported; abstain",
        "embedded_structure_feasibility_route": "embedded_supported; embedded_unsupported; abstain",
    }
    return mapping[route_type]


def primary_metric(route_type: str) -> str:
    mapping = {
        "geometry_only_learned_evaluated_route": "AUROC/F1 for geometry support plus coverage",
        "predicate_geometry_interaction_route": "AUROC and paired margin for C_e interaction vs controls",
        "superordinate_support_decomposition_route": "macro-F1 over accept/relabel/reject/abstain",
        "observability_aware_route": "selective risk, p_obs AUROC, accept/reject AUROC on observable rows",
        "contact_orientation_feasibility_route": "feasibility AUROC/F1 with normal/pose controls",
        "occlusion_coverage_feasibility_route": "feasibility AUROC/F1 with view/visibility controls",
        "containment_feasibility_route": "feasibility AUROC/F1 with containment/completeness controls",
        "identity_symmetry_route": "identity/symmetry verification AUROC/F1",
        "semantic_structural_route": "semantic/structural compatibility accuracy or macro-F1",
        "embedded_structure_feasibility_route": "embedded-structure feasibility AUROC/F1",
    }
    return mapping[route_type]


def secondary_metrics(route_type: str) -> str:
    mapping = {
        "geometry_only_learned_evaluated_route": "distance-bin calibration; violation rate; abstain coverage",
        "predicate_geometry_interaction_route": "wrong-T collapse; shuffled-G collapse; sign/frame/endpoint control delta",
        "superordinate_support_decomposition_route": "subtype confusion; relabel accuracy; abstain precision",
        "observability_aware_route": "no-view degradation; shuffled-view control; p_obs calibration",
        "contact_orientation_feasibility_route": "contact-only baseline delta; normal-shuffle control",
        "occlusion_coverage_feasibility_route": "overlap-only baseline delta; view-shuffle control",
        "containment_feasibility_route": "class-pair shortcut; containment-ratio bins; completeness ablation",
        "identity_symmetry_route": "class-only baseline; shape-shuffle control; duplicate leakage audit",
        "semantic_structural_route": "class/ontology baseline; structural evidence ablation",
        "embedded_structure_feasibility_route": "wall-near baseline; mesh-completeness control",
    }
    return mapping[route_type]


def must_not_use_as_negative(route_type: str) -> str:
    mapping = {
        "geometry_only_learned_evaluated_route": "no-GT rows; boundary-distance ambiguous rows",
        "predicate_geometry_interaction_route": "no-GT rows without counterfactual construction",
        "superordinate_support_decomposition_route": "standing on or lying on rows that may also be supported by",
        "observability_aware_route": "unobservable rows; functional connection ambiguous rows",
        "contact_orientation_feasibility_route": "near-contact rows without normal/pose evidence",
        "occlusion_coverage_feasibility_route": "no-view rows; occluded-but-unseen rows",
        "containment_feasibility_route": "incomplete container rows; occluded/partial scans",
        "identity_symmetry_route": "same-class nonmatched rows without shape evidence",
        "semantic_structural_route": "no-GT semantic pairs without structural audit",
        "embedded_structure_feasibility_route": "near-wall rows without cavity/mesh evidence",
    }
    return mapping[route_type]


def route_status(paper_role: str) -> str:
    if "main" in paper_role:
        return "manifest_required_for_main_mechanism"
    if "claim_control" in paper_role:
        return "manifest_required_for_claim_control"
    if "next" in paper_role:
        return "manifest_required_before_feasibility_materialization"
    return "manifest_boundary_or_future"


def route_field_manifest(route_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in route_rows:
        route_type = row["route_type"]
        route_id = row["route_id"]
        family = row["family"]
        rows.append(
            {
                "route_id": route_id,
                "family": family,
                "route_type": route_type,
                "T_e_model_safe": te_fields(route_type),
                "Z_e_model_safe": ze_fields(route_type),
                "G_e_model_safe": ge_fields(route_type),
                "Q_e_model_safe": qe_fields(route_type),
                "C_e_definition": ce_definition(route_type),
                "blocked_model_fields": "row_id; scan_id; endpoint ids; GT/audit label; hidden construction buckets; geometry_status target; source score inside C_e",
                "router_metadata_allowed": "route_type only for routing/reporting; no target label or construction key",
            }
        )
    return rows


def te_fields(route_type: str) -> str:
    if route_type == "geometry_only_learned_evaluated_route":
        return "predicate text/class only for route annotation; not needed for route score"
    if route_type == "semantic_structural_route":
        return "predicate text; relation family; subject/object class; optional ontology/part-whole text"
    if route_type == "identity_symmetry_route":
        return "identity/symmetry predicate text; subject/object class"
    return "predicate text; relation family; subject/object class"


def ze_fields(route_type: str) -> str:
    if route_type in {"contact_orientation_feasibility_route", "occlusion_coverage_feasibility_route", "containment_feasibility_route", "embedded_structure_feasibility_route"}:
        return "optional source baseline only; excluded from C_e and feasibility evidence"
    return "source score/rank allowed only for source baseline or final p_rel; excluded from C_e"


def ge_fields(route_type: str) -> str:
    mapping = {
        "geometry_only_learned_evaluated_route": "boundary distance; center distance; object scale; XY distance; coverage-normalized distance",
        "predicate_geometry_interaction_route": "signed vertical/size/horizontal/contact/pose features according to family; no predicate fields",
        "superordinate_support_decomposition_route": "contact/gap; support overlap; support direction; surface type proxy; pose/contact evidence",
        "observability_aware_route": "contact/gap; mesh contact; attachment point; topology cue; multi-view pair evidence if available",
        "contact_orientation_feasibility_route": "surface contact; normal alignment; tilt angle; lower support cue; wall/floor proximity",
        "occlusion_coverage_feasibility_route": "projected overlap; visibility reduction; depth ordering; view coverage",
        "containment_feasibility_route": "containment ratio; point-in-container ratio; OBB/mesh containment; opening/partial scan flags",
        "identity_symmetry_route": "shape descriptor; OBB size/volume; pose; symmetry axis; overlap/duplicate geometry",
        "semantic_structural_route": "optional structure/part geometry; hierarchy evidence; spatial inclusion if relevant",
        "embedded_structure_feasibility_route": "cavity/wall/mesh contact; embedded depth; surrounding structure completeness",
    }
    return mapping[route_type]


def qe_fields(route_type: str) -> str:
    mapping = {
        "geometry_only_learned_evaluated_route": "geometry coverage; boundary ambiguity; point count",
        "predicate_geometry_interaction_route": "geometry coverage; route boundary flag; frame availability for horizontal; contact evidence quality for support/contact",
        "superordinate_support_decomposition_route": "subtype ambiguity; support evidence sufficiency; surface visibility",
        "observability_aware_route": "view availability; mesh completeness; same-frame visibility; contact/attachment surface visibility; topology evidence availability",
        "contact_orientation_feasibility_route": "normal availability; pose confidence; contact visibility",
        "occlusion_coverage_feasibility_route": "view availability; object visibility; occlusion evidence quality",
        "containment_feasibility_route": "container completeness; occlusion; inside surface visibility; point coverage",
        "identity_symmetry_route": "instance segmentation quality; shape completeness; symmetry observability",
        "semantic_structural_route": "ontology evidence availability; structural annotation quality",
        "embedded_structure_feasibility_route": "mesh/cavity completeness; wall/structure visibility",
    }
    return mapping[route_type]


def ce_definition(route_type: str) -> str:
    if route_type == "geometry_only_learned_evaluated_route":
        return "C_e optional; route score is G_e sufficiency"
    if route_type == "superordinate_support_decomposition_route":
        return "C_e supports accept/relabel/abstain, not binary truth"
    if route_type == "observability_aware_route":
        return "C_e evaluated only when p_obs says evidence is observable"
    if route_type in {"identity_symmetry_route", "semantic_structural_route"}:
        return "compatibility is route-specific identity/symmetry or semantic-structural compatibility"
    return "C_e = compatibility(T_e, G_e), excluding Z_e"


def hidden_field_manifest(route_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    common = "target label; construction bucket; GT match; audit label; row identity; endpoint pair; scan id; route-specific hidden thresholds"
    for row in route_rows:
        rows.append(
            {
                "route_id": row["route_id"],
                "family": row["family"],
                "hidden_fields": hidden_fields(row["route_type"], common),
                "audit_use": audit_use(row["route_type"]),
                "forbidden_use": "model input; C_e input; route score input; hyperparameter selection without declared calibration split",
            }
        )
    return rows


def hidden_fields(route_type: str, common: str) -> str:
    extra = {
        "geometry_only_learned_evaluated_route": "distance threshold bucket; p_geom_valid rule bucket",
        "predicate_geometry_interaction_route": "predicate flip id; sign flip id; wrong-frame id; endpoint-swap id",
        "superordinate_support_decomposition_route": "subtype source; relabel decision; support taxonomy bucket",
        "observability_aware_route": "visible packet label; human/codex audit label; functional vs physical connection hint",
        "contact_orientation_feasibility_route": "tilt threshold bucket; normal-alignment bucket",
        "occlusion_coverage_feasibility_route": "view-selected occlusion bucket; visibility-threshold bucket",
        "containment_feasibility_route": "containment threshold bucket; class-pair container prior",
        "identity_symmetry_route": "duplicate-pair candidate id; symmetry construction key",
        "semantic_structural_route": "ontology prior; class-pair structural prior",
        "embedded_structure_feasibility_route": "wall/cavity construction bucket",
    }
    return f"{common}; {extra[route_type]}"


def audit_use(route_type: str) -> str:
    mapping = {
        "geometry_only_learned_evaluated_route": "distance/scale shortcut audit and boundary-case analysis",
        "predicate_geometry_interaction_route": "counterfactual pairing, wrong-T/sign/frame/endpoint control audit",
        "superordinate_support_decomposition_route": "subtype confusion, relabel/abstain audit",
        "observability_aware_route": "observability label audit and no-view/low-view controls",
        "contact_orientation_feasibility_route": "normal/pose threshold audit",
        "occlusion_coverage_feasibility_route": "view/visibility audit",
        "containment_feasibility_route": "class-pair and containment-threshold audit",
        "identity_symmetry_route": "class-only and duplicate-pair leakage audit",
        "semantic_structural_route": "ontology/class prior audit",
        "embedded_structure_feasibility_route": "mesh/cavity completeness audit",
    }
    return mapping[route_type]


def control_manifest(route_rows: list[dict[str, str]], target_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    target_by_route = {row["route_id"]: row for row in target_rows}
    rows: list[dict[str, Any]] = []
    for row in route_rows:
        target = target_by_route[row["route_id"]]
        rows.append(
            {
                "route_id": row["route_id"],
                "family": row["family"],
                "route_type": row["route_type"],
                "required_controls": target["required_controls"],
                "negative_control": negative_control(row["route_type"]),
                "shortcut_probes": shortcut_probes(row["route_type"]),
                "minimum_pass_condition": minimum_pass(row["route_type"]),
            }
        )
    return rows


def negative_control(route_type: str) -> str:
    mapping = {
        "geometry_only_learned_evaluated_route": "shuffled-G and wrong-pair geometry should degrade to chance or below route model",
        "predicate_geometry_interaction_route": "wrong-T, shuffled-G, sign/frame/endpoint controls should collapse relative to matched C_e",
        "superordinate_support_decomposition_route": "using supported-by as standing/lying negative must fail or be blocked",
        "observability_aware_route": "shuffled-view/no-view controls should lower p_obs or force abstain",
        "contact_orientation_feasibility_route": "normal shuffle or tilt removal should degrade",
        "occlusion_coverage_feasibility_route": "view shuffle or overlap-only baseline should degrade",
        "containment_feasibility_route": "class-pair-only and containment-ratio-only probes must be reported",
        "identity_symmetry_route": "class-only baseline and shape shuffle must be reported",
        "semantic_structural_route": "class/ontology-only baseline must be reported separately",
        "embedded_structure_feasibility_route": "wall-near baseline should not solve embedded relation",
    }
    return mapping[route_type]


def shortcut_probes(route_type: str) -> str:
    base = "source/rank-only; class-pair-only; scan/endpoint leakage; route metadata only"
    extra = {
        "geometry_only_learned_evaluated_route": "distance-bin-only; object-scale-only",
        "predicate_geometry_interaction_route": "predicate-only; sign-bucket-only; construction-pair id",
        "superordinate_support_decomposition_route": "subtype label prior; support-surface class prior",
        "observability_aware_route": "visibility-tier-only; packet-source-only",
        "contact_orientation_feasibility_route": "normal-availability-only; wall/floor-class prior",
        "occlusion_coverage_feasibility_route": "view-count-only; image-availability-only",
        "containment_feasibility_route": "container-class-only; containment-bucket-only",
        "identity_symmetry_route": "same-class-only; duplicate-candidate-id leakage",
        "semantic_structural_route": "class-pair/ontology-only",
        "embedded_structure_feasibility_route": "wall-near-only; cavity-availability-only",
    }
    return f"{base}; {extra[route_type]}"


def minimum_pass(route_type: str) -> str:
    if route_type == "geometry_only_learned_evaluated_route":
        return "route can be solved by G_e but must be reported as geometry-only, not interaction"
    if route_type == "predicate_geometry_interaction_route":
        return "C_e interaction beats T-only/G-only/concat and controls collapse"
    if route_type == "superordinate_support_decomposition_route":
        return "accept/relabel/abstain target is identifiable without subtype leakage"
    if route_type == "observability_aware_route":
        return "p_obs separates observable from unobservable and p_rel is evaluated only on observable rows"
    if "feasibility" in route_type:
        return "capacity/schema audit passes before any materialization"
    if route_type == "identity_symmetry_route":
        return "identity/symmetry route is kept separate unless shape controls pass"
    return "semantic/structural route remains boundary unless non-ontology evidence is formalized"


def artifact_root_plan(route_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in route_rows:
        slug = route_slug(row["route_id"], row["family"])
        root = f"artifacts/route_specific_targets/{slug}/"
        rows.append(
            {
                "route_id": row["route_id"],
                "family": row["family"],
                "artifact_root": root,
                "planned_files": (
                    "summary.json; schema.json; model_safe_rows.jsonl; hidden_manifest.jsonl; "
                    "audit_view.jsonl; control_manifest.json; split_or_group_manifest.json; report.md; validation_errors.jsonl"
                ),
                "materialization_allowed_now": False,
                "reason": "this TODO freezes manifests only; data materialization requires a follow-up route-specific plan",
            }
        )
    return rows


def promotion_priority(route_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    priority = {
        "relative_vertical": (1, "already main clean route; needs manifest normalization only"),
        "size_relative": (2, "already main clean route; keep calibration caveat"),
        "relative_horizontal": (3, "already main frame-aware route; keep reference-frame caveat"),
        "support_contact": (4, "main challenging route; caveat and Q_e controls required"),
        "proximity": (5, "convert from diagnostic/control wording to geometry-only route manifest"),
        "superordinate_support": (6, "high-value decomposition/relabel/abstain route"),
        "attachment_observability": (7, "high-value observability route but needs visual/mesh/topology schema"),
        "contact_orientation": (8, "leaning against feasibility candidate"),
        "occlusion_coverage": (9, "cover feasibility candidate"),
        "containment": (10, "containment feasibility candidate with low-count/occlusion risk"),
        "identity_symmetry": (11, "separate task candidate"),
        "semantic_structural": (12, "boundary/future route"),
        "embedded_structure": (13, "future feasibility route"),
    }
    rows: list[dict[str, Any]] = []
    for row in route_rows:
        rank, reason = priority[row["family"]]
        rows.append(
            {
                "rank": rank,
                "route_id": row["route_id"],
                "family": row["family"],
                "relations": row["relations"],
                "promotion_tier": promotion_tier(rank),
                "reason": reason,
                "next_action": next_action(row["family"]),
            }
        )
    rows.sort(key=lambda item: item["rank"])
    return rows


def promotion_tier(rank: int) -> str:
    if rank <= 4:
        return "current_main_manifest"
    if rank <= 6:
        return "claim_control_manifest"
    if rank <= 10:
        return "next_feasibility_manifest"
    return "boundary_or_future_manifest"


def next_action(family: str) -> str:
    mapping = {
        "relative_vertical": "normalize existing main-route manifest and controls",
        "size_relative": "normalize existing main-route manifest and calibration caveat",
        "relative_horizontal": "normalize frame-aware manifest with wrong-frame/endpoint controls",
        "support_contact": "normalize challenging-route manifest with Q_e and caveat",
        "proximity": "write close-by geometry-only route manifest before any rerun",
        "superordinate_support": "write supported-by decomposition/relabel/abstain manifest",
        "attachment_observability": "write observability manifest with visual/mesh/topology evidence",
        "contact_orientation": "capacity/schema audit for leaning-against",
        "occlusion_coverage": "capacity/schema audit for cover",
        "containment": "capacity/schema audit for containment relations",
        "identity_symmetry": "boundary feasibility audit for identity/symmetry",
        "semantic_structural": "boundary manifest for part/belonging relations",
        "embedded_structure": "future feasibility manifest for build-in",
    }
    return mapping[family]


def manifest_consistency_checks(
    target_manifest: list[dict[str, Any]],
    field_manifest: list[dict[str, Any]],
    hidden_manifest: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
    artifact_rows: list[dict[str, Any]],
    priority_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    route_ids = {row["route_id"] for row in target_manifest}
    for name, rows in [
        ("field_manifest", field_manifest),
        ("hidden_manifest", hidden_manifest),
        ("control_manifest", control_rows),
        ("artifact_root_plan", artifact_rows),
        ("promotion_priority", priority_rows),
    ]:
        ids = {row["route_id"] for row in rows}
        if ids != route_ids:
            errors.append({"error_type": "route_id_set_mismatch", "table": name, "missing": sorted(route_ids - ids), "extra": sorted(ids - route_ids)})
    for row in target_manifest:
        if row["route_type"] == "geometry_only_learned_evaluated_route" and "T_e x G_e" in row["primary_metric"]:
            errors.append({"error_type": "close_by_wrong_metric", "row": row})
        if row["family"] == "superordinate_support" and "binary" in row["label_space"]:
            errors.append({"error_type": "supported_by_binary_label_space", "row": row})
    return errors


def write_report(
    path: Path,
    status: str,
    validation_errors: int,
    target_manifest: list[dict[str, Any]],
    priority_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# H002 Route-Specific Target Manifest Plan After Schema Freeze",
        "",
        "## Status",
        "",
        "```text",
        f"status = {status}",
        f"selected_path = {SELECTED_PATH}",
        f"validation_errors = {validation_errors}",
        f"next_todo = {NEXT_TODO}",
        "```",
        "",
        "## Purpose",
        "",
        "This artifact turns the frozen route taxonomy into executable per-route manifest plans.",
        "It does not materialize new rows and does not run a model.",
        "",
        "## Route Target Manifests",
        "",
        "| Route | Relations | Target Axis | Label Space | Artifact Root |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in target_manifest:
        lines.append(
            f"| {row['route_type']} | {row['relations']} | {row['target_axis']} | {row['label_space']} | {row['artifact_root']} |"
        )
    lines.extend(
        [
            "",
            "## Promotion Priority",
            "",
            "| Rank | Family | Relations | Tier | Next Action |",
            "| ---: | --- | --- | --- | --- |",
        ]
    )
    for row in priority_rows:
        lines.append(
            f"| {row['rank']} | {row['family']} | {row['relations']} | {row['promotion_tier']} | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Allowed now:",
            "",
            "- route-specific target manifest planning",
            "- model-safe / hidden-field separation",
            "- per-route controls and artifact-root planning",
            "",
            "Blocked now:",
            "",
            "- data materialization",
            "- learned smoke runner",
            "- Docker/paper promotion",
            "- calibrated `p_rel` / `p_obs` claim",
            "",
            "## Next",
            "",
            "```text",
            NEXT_TODO,
            "```",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    schema_freeze_dir = args.schema_freeze_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_in = read_json(schema_freeze_dir / "summary.json")
    route_rows = read_csv(schema_freeze_dir / "route_taxonomy_freeze.csv")
    target_rows = read_csv(schema_freeze_dir / "target_definition_freeze.csv")
    schema_rows = read_csv(schema_freeze_dir / "schema_freeze_manifest.csv")
    errors = validate_inputs(summary_in, route_rows, target_rows, schema_rows, schema_freeze_dir)

    target_manifest = route_target_manifest(route_rows, target_rows)
    field_manifest = route_field_manifest(route_rows)
    hidden_manifest = hidden_field_manifest(route_rows)
    control_rows = control_manifest(route_rows, target_rows)
    artifact_rows = artifact_root_plan(route_rows)
    priority_rows = promotion_priority(route_rows)
    errors.extend(
        manifest_consistency_checks(target_manifest, field_manifest, hidden_manifest, control_rows, artifact_rows, priority_rows)
    )
    status = STATUS_ERRORS if errors else STATUS_READY

    output_paths = {
        "artifact_root": rel_path(output_dir),
        "route_target_manifest": rel_path(output_dir / "route_target_manifest.csv"),
        "route_field_manifest": rel_path(output_dir / "route_field_manifest.csv"),
        "route_hidden_manifest": rel_path(output_dir / "route_hidden_manifest.csv"),
        "route_control_manifest": rel_path(output_dir / "route_control_manifest.csv"),
        "route_artifact_root_plan": rel_path(output_dir / "route_artifact_root_plan.csv"),
        "route_promotion_priority": rel_path(output_dir / "route_promotion_priority.csv"),
        "report": rel_path(output_dir / "report.md"),
        "summary": rel_path(output_dir / "summary.json"),
        "validation_errors": rel_path(output_dir / "validation_errors.jsonl"),
    }
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "selected_path": SELECTED_PATH if not errors else "input_or_manifest_errors_fix_before_audit",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_paths": {
            "schema_freeze": rel_path(schema_freeze_dir),
        },
        "output_paths": output_paths,
        "counts": {
            "route_target_manifest_rows": len(target_manifest),
            "route_field_manifest_rows": len(field_manifest),
            "route_hidden_manifest_rows": len(hidden_manifest),
            "route_control_manifest_rows": len(control_rows),
            "route_artifact_root_rows": len(artifact_rows),
            "route_promotion_priority_rows": len(priority_rows),
        },
        "selected_next_focus": "manifest_consistency_audit_before_any_materialization",
        "route_groups": {
            "geometry_only": "close by",
            "predicate_geometry": "higher/lower; bigger/smaller; left/right/front/behind; standing/lying on",
            "superordinate_decomposition": "supported by",
            "observability_aware": "attached to; hanging on; connected to",
            "next_feasibility": "leaning against; cover; standing/lying/hanging in; inside",
            "separate_or_boundary": "same as; same symmetry as; part of; belonging to; build in",
        },
        "boundary": {
            "materializes_rows": False,
            "runs_model": False,
            "paper_evidence_allowed_now": False,
            "h001_artifacts_modified": False,
            "validation_or_test_used": False,
        },
        "next_todo": NEXT_TODO,
        "validation_errors": len(errors),
    }

    write_csv(output_dir / "route_target_manifest.csv", target_manifest)
    write_csv(output_dir / "route_field_manifest.csv", field_manifest)
    write_csv(output_dir / "route_hidden_manifest.csv", hidden_manifest)
    write_csv(output_dir / "route_control_manifest.csv", control_rows)
    write_csv(output_dir / "route_artifact_root_plan.csv", artifact_rows)
    write_csv(output_dir / "route_promotion_priority.csv", priority_rows)
    write_json(output_dir / "summary.json", summary)
    write_jsonl(output_dir / "validation_errors.jsonl", errors)
    write_report(output_dir / "report.md", status, len(errors), target_manifest, priority_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
