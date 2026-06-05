#!/usr/bin/env python3
"""Freeze the full official validation scope before any metric rerun.

This script is a no-training, no-inference protocol gate. It records the full
official 3DSSG_subset validation denominator, current local payload/preprocess
coverage, output-path contract, and rerun command templates. It does not modify
the current 127-scan artifacts and must not be treated as metric evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "h001_full_official_validation_scope_contract_v1"
STATUS = "full_official_validation_scope_contract_ready_no_metric_execution"

PRIMARY_FAMILIES = ("support_contact", "proximity", "relative_vertical")
SUPPORT_LABELS = {"standing on", "lying on", "supported by"}
RELATIVE_VERTICAL_LABELS = {"higher than", "lower than"}
RELATIVE_HORIZONTAL_LABELS = {"left", "right", "front", "behind", "in front of"}
ATTACHMENT_LABELS = {"attached to", "hanging on", "mounted on", "connected to"}

RAW_GEOMETRY_FILES = (
    "labels.instances.annotated.v2.ply",
    "semseg.v2.json",
    "mesh.refined.0.010000.segs.v2.json",
)
VLSAT_GEOMETRY_FILES = RAW_GEOMETRY_FILES + ("labels.instances.align.annotated.v2.ply",)
OPEN3DSG_MESH_TEXTURE_FILES = (
    "mesh.refined.v2.obj",
    "mesh.refined.mtl",
    "mesh.refined_0.png",
)
SEQUENCE_SENTINELS = (
    "sequence/_info.txt",
    "sequence/frame-000000.color.jpg",
    "sequence/frame-000000.depth.pgm",
    "sequence/frame-000000.pose.txt",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--dataset-root", type=Path, default=Path("local_dataset"))
    parser.add_argument(
        "--relationships-validation",
        type=Path,
        default=Path("local_dataset/3DSSG_subset/relationships_validation.json"),
    )
    parser.add_argument(
        "--relationships-file",
        type=Path,
        default=Path("local_dataset/3DSSG_subset/relationships.txt"),
    )
    parser.add_argument(
        "--hardened-ground-truth",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/"
            "evaluation/vlsat_closed_set/hardened/ground_truth.jsonl"
        ),
    )
    parser.add_argument(
        "--hardened-scans",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/"
            "subset/h001_validation_hardened/scans.txt"
        ),
    )
    parser.add_argument(
        "--mini-scans",
        type=Path,
        default=Path(
            "hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/"
            "subset/h001_mini/scans.txt"
        ),
    )
    parser.add_argument(
        "--vlsat-hardened-root",
        type=Path,
        default=Path("local_dataset/VLSAT_staged/h001_validation_hardened/CVPR2023-VLSAT"),
    )
    parser.add_argument(
        "--open3dsg-h001-runtime-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/h001_runtime"),
    )
    parser.add_argument(
        "--open3dsg-training-repro-root",
        type=Path,
        default=Path("local_dataset/Open3DSG_staged/training_repro"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/full_validation_transition/scope_contract"),
    )
    return parser.parse_args()


def resolve(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def relpath(repo_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(repo_root.resolve()))
    except ValueError:
        return str(path)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def predicate_family(label: str) -> str:
    if label in SUPPORT_LABELS:
        return "support_contact"
    if label == "close by":
        return "proximity"
    if label in RELATIVE_VERTICAL_LABELS:
        return "relative_vertical"
    if label in RELATIVE_HORIZONTAL_LABELS:
        return "relative_horizontal"
    if label in ATTACHMENT_LABELS:
        return "attachment_deferred"
    return "unsupported_first_pass"


def validation_id(entry: dict[str, Any]) -> str:
    return f"{entry['scan']}_{int(entry['split'])}"


def file_ready(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def sequence_ready(scan_dir: Path) -> bool:
    if all(file_ready(scan_dir / sentinel) for sentinel in SEQUENCE_SENTINELS):
        return True
    return file_ready(scan_dir / "sequence.zip")


def count_ready_scans(scans: list[str], root: Path, required_files: tuple[str, ...]) -> tuple[int, list[str]]:
    missing: list[str] = []
    for scan_id in scans:
        scan_dir = root / scan_id
        if not scan_dir.is_dir() or any(not file_ready(scan_dir / name) for name in required_files):
            missing.append(scan_id)
    return len(scans) - len(missing), missing


def count_sequence_ready(scans: list[str], root: Path) -> tuple[int, list[str]]:
    missing = [scan_id for scan_id in scans if not sequence_ready(root / scan_id)]
    return len(scans) - len(missing), missing


def count_vlsat_staged(scans: list[str], staged_root: Path) -> tuple[int, list[str]]:
    staged_scan_root = staged_root / "data/3RScan"
    missing = [scan_id for scan_id in scans if not (staged_scan_root / scan_id).is_dir()]
    return len(scans) - len(missing), missing


def count_open3dsg_views(scans: list[str], runtime_root: Path) -> tuple[int, list[str]]:
    view_root = runtime_root / "output/datasets/OpenSG_3RScan/views"
    missing = [scan_id for scan_id in scans if not file_ready(view_root / f"{scan_id}_object2image.pkl")]
    return len(scans) - len(missing), missing


def count_open3dsg_preprocess(entries: list[dict[str, Any]], runtime_root: Path) -> tuple[int, list[str]]:
    pre_root = runtime_root / "output/datasets/OpenSG_3RScan/preprocessed"
    missing: list[str] = []
    for entry in entries:
        target = pre_root / str(entry["scan"]) / f"data_dict_{int(entry['split'])}.pkl"
        if not file_ready(target):
            missing.append(validation_id(entry))
    return len(entries) - len(missing), missing


def count_hardened_ground_truth(path: Path) -> dict[str, Any]:
    scans: set[str] = set()
    contexts: set[str] = set()
    gt_pairs: set[tuple[str, int, int, int]] = set()
    families: Counter[str] = Counter()
    rows = 0
    if not path.exists():
        return {
            "path": str(path),
            "exists": False,
            "scans": 0,
            "contexts": 0,
            "gt_positive_directed_pairs": 0,
            "gt_rows": 0,
            "family_counts": {},
        }
    for row in iter_jsonl(path):
        rows += 1
        scan_id = str(row["scan_id"])
        split_id = int(row["subset_split_id"])
        scans.add(scan_id)
        contexts.add(str(row.get("subgraph_id", f"{scan_id}_{split_id}")))
        gt_pairs.add((scan_id, split_id, int(row["subject_id"]), int(row["object_id"])))
        families[str(row.get("predicate_family", "missing_family"))] += 1
    return {
        "path": str(path),
        "exists": True,
        "scans": len(scans),
        "contexts": len(contexts),
        "gt_positive_directed_pairs": len(gt_pairs),
        "gt_rows": rows,
        "family_counts": dict(sorted(families.items())),
        "h001_family_gt_rows": sum(families.get(family, 0) for family in PRIMARY_FAMILIES),
    }


def relation_label_count(path: Path) -> int | None:
    labels = [line for line in read_lines(path) if line != "none"]
    return len(labels) if labels else None


def build_scope_contract(
    *,
    repo_root: Path,
    relationships_validation: Path,
    relationships_file: Path,
    hardened_ground_truth: Path,
    hardened_scans: Path,
    mini_scans: Path,
    dataset_root: Path,
    vlsat_hardened_root: Path,
    open3dsg_h001_runtime_root: Path,
    open3dsg_training_repro_root: Path,
    out: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validation = read_json(relationships_validation)
    entries = validation.get("scans", [])
    scans = sorted({str(entry["scan"]) for entry in entries})
    h001_scan_set = set(read_lines(hardened_scans))
    mini_scan_set = set(read_lines(mini_scans))

    family_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    family_label_counts: Counter[str] = Counter()
    gt_pairs: set[tuple[str, int, int, int]] = set()
    candidate_directed_pairs = 0
    context_rows: list[dict[str, Any]] = []

    for entry in entries:
        scan_id = str(entry["scan"])
        split_id = int(entry["split"])
        objects = {int(key): str(value) for key, value in entry.get("objects", {}).items()}
        candidate_directed_pairs += len(objects) * max(len(objects) - 1, 0)
        context_family_counts: Counter[str] = Counter()
        for subject_id, object_id, _rel_id, label in entry.get("relationships", []):
            label = str(label)
            family = predicate_family(label)
            family_counts[family] += 1
            label_counts[label] += 1
            family_label_counts[f"{family}::{label}"] += 1
            context_family_counts[family] += 1
            gt_pairs.add((scan_id, split_id, int(subject_id), int(object_id)))
        context_rows.append(
            {
                "scan_id": scan_id,
                "subset_split_id": split_id,
                "subgraph_id": f"{scan_id}_{split_id}",
                "object_count": len(objects),
                "candidate_directed_pairs": len(objects) * max(len(objects) - 1, 0),
                "gt_rows": len(entry.get("relationships", [])),
                "family_counts": dict(sorted(context_family_counts.items())),
                "was_in_completed_hardened_scope": scan_id in h001_scan_set,
                "was_in_h001_mini": scan_id in mini_scan_set,
            }
        )

    raw_scan_root = dataset_root / "3RScan/scans"
    raw_ready, raw_missing = count_ready_scans(scans, raw_scan_root, RAW_GEOMETRY_FILES)
    vlsat_ready, vlsat_missing = count_ready_scans(scans, raw_scan_root, VLSAT_GEOMETRY_FILES)
    mesh_ready, mesh_missing = count_ready_scans(scans, raw_scan_root, OPEN3DSG_MESH_TEXTURE_FILES)
    seq_ready, seq_missing = count_sequence_ready(scans, raw_scan_root)
    vlsat_staged_ready, vlsat_staged_missing = count_vlsat_staged(scans, vlsat_hardened_root)
    h001_views_ready, h001_views_missing = count_open3dsg_views(scans, open3dsg_h001_runtime_root)
    h001_pre_ready, h001_pre_missing = count_open3dsg_preprocess(entries, open3dsg_h001_runtime_root)
    train_views_ready, train_views_missing = count_open3dsg_views(scans, open3dsg_training_repro_root)
    train_pre_ready, train_pre_missing = count_open3dsg_preprocess(entries, open3dsg_training_repro_root)

    non_none_relation_labels = relation_label_count(relationships_file)
    expected_vlsat_rows = (
        candidate_directed_pairs * non_none_relation_labels if non_none_relation_labels is not None else None
    )
    h001_family_rows = sum(family_counts.get(family, 0) for family in PRIMARY_FAMILIES)

    output_paths = {
        "scope_contract_root": relpath(repo_root, out),
        "selected_scans": relpath(repo_root, out / "scans.txt"),
        "contexts": relpath(repo_root, out / "contexts.jsonl"),
        "vlsat_full_validation_root": "experiments/H001_geom_reliability/sources/vlsat/full_validation",
        "vlsat_runtime_root": "local_dataset/VLSAT_staged/h001_full_validation/CVPR2023-VLSAT",
        "open3dsg_full_validation_root": "experiments/H001_geom_reliability/sources/open3dsg/full_validation",
        "open3dsg_runtime_root": "local_dataset/Open3DSG_staged/h001_full_validation_runtime",
    }

    blockers: list[str] = []
    if raw_ready != len(scans):
        blockers.append(f"raw_geometry_payload_missing:{len(raw_missing)}")
    if vlsat_ready != len(scans):
        blockers.append(f"vlsat_geometry_payload_missing:{len(vlsat_missing)}")
    if mesh_ready != len(scans):
        blockers.append(f"open3dsg_mesh_texture_missing:{len(mesh_missing)}")
    if seq_ready != len(scans):
        blockers.append(f"open3dsg_sequence_missing:{len(seq_missing)}")

    warnings = [
        "scope_contract_only_no_metric_execution",
        "do_not_edit_current_127_scan_tables_by_denominator_substitution",
        "vlsat_full_validation_runtime_docker_service_must_be_added_or_documented_before_paper_metric_promotion",
        "open3dsg_full_validation_coverage_must_be_recomputed_after_preprocess_feature_raw_dump_regeneration",
    ]
    if vlsat_staged_ready != len(scans):
        warnings.append(f"existing_vlsat_hardened_staged_root_only:{vlsat_staged_ready}/{len(scans)}")
    if h001_pre_ready != len(entries):
        warnings.append(f"existing_open3dsg_h001_runtime_preprocess_only:{h001_pre_ready}/{len(entries)}")

    contract = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "created_at": now_iso(),
        "claim_boundary": {
            "paper_route": "full_official_3dssg_subset_validation_after_complete_docker_rerun",
            "current_completed_results": "127_scan_hardened_results_remain_current_evidence_until_full_validation_artifacts_exist",
            "method_provenance": (
                "Final family mapping, verifier policies, counterfactual construction, and p_geom_valid "
                "calibrators are train/train-dev-derived and frozen before validation source-result reporting."
            ),
            "h001_mini_role": "hypothesis_feasibility_evidence_only_not_metric_or_tuning_split",
            "blocked_claim": "current_127_scan_results_already_prove_full_official_validation_claim",
        },
        "inputs": {
            "relationships_validation": {
                "path": relpath(repo_root, relationships_validation),
                "sha256": sha256_file(relationships_validation),
            },
            "relationships_file": {
                "path": relpath(repo_root, relationships_file),
                "sha256": sha256_file(relationships_file),
                "non_none_relation_labels": non_none_relation_labels,
            },
            "completed_hardened_ground_truth": count_hardened_ground_truth(hardened_ground_truth),
        },
        "full_validation_scope": {
            "scans": len(scans),
            "contexts": len(entries),
            "gt_positive_directed_pairs": len(gt_pairs),
            "candidate_directed_pairs": candidate_directed_pairs,
            "gt_rows": sum(family_counts.values()),
            "h001_family_gt_rows": h001_family_rows,
            "h001_family_counts": {family: family_counts.get(family, 0) for family in PRIMARY_FAMILIES},
            "family_counts": dict(sorted(family_counts.items())),
            "label_counts": dict(sorted(label_counts.items())),
            "family_label_counts": dict(sorted(family_label_counts.items())),
            "expected_vlsat_prediction_rows_all_non_none_predicates": expected_vlsat_rows,
        },
        "local_readiness": {
            "raw_3rscan_geometry": {
                "ready_scans": raw_ready,
                "target_scans": len(scans),
                "required_files": list(RAW_GEOMETRY_FILES),
                "missing_scans": raw_missing[:50],
                "missing_scan_count": len(raw_missing),
            },
            "vlsat_raw_geometry": {
                "ready_scans": vlsat_ready,
                "target_scans": len(scans),
                "required_files": list(VLSAT_GEOMETRY_FILES),
                "missing_scans": vlsat_missing[:50],
                "missing_scan_count": len(vlsat_missing),
            },
            "open3dsg_mesh_texture": {
                "ready_scans": mesh_ready,
                "target_scans": len(scans),
                "required_files": list(OPEN3DSG_MESH_TEXTURE_FILES),
                "missing_scans": mesh_missing[:50],
                "missing_scan_count": len(mesh_missing),
            },
            "open3dsg_sequence": {
                "ready_scans": seq_ready,
                "target_scans": len(scans),
                "missing_scans": seq_missing[:50],
                "missing_scan_count": len(seq_missing),
            },
            "existing_vlsat_hardened_staged_root": {
                "ready_scans": vlsat_staged_ready,
                "target_scans": len(scans),
                "path": relpath(repo_root, vlsat_hardened_root),
                "missing_scans": vlsat_staged_missing[:50],
                "missing_scan_count": len(vlsat_staged_missing),
            },
            "existing_open3dsg_h001_runtime": {
                "view_ready_scans": h001_views_ready,
                "view_target_scans": len(scans),
                "preprocess_ready_contexts": h001_pre_ready,
                "preprocess_target_contexts": len(entries),
                "missing_view_scans": h001_views_missing[:50],
                "missing_preprocess_contexts": h001_pre_missing[:50],
                "missing_preprocess_context_count": len(h001_pre_missing),
            },
            "existing_open3dsg_training_repro": {
                "view_ready_scans": train_views_ready,
                "view_target_scans": len(scans),
                "preprocess_ready_contexts": train_pre_ready,
                "preprocess_target_contexts": len(entries),
                "missing_view_scans": train_views_missing[:50],
                "missing_preprocess_contexts": train_pre_missing[:50],
                "missing_preprocess_context_count": len(train_pre_missing),
            },
        },
        "output_path_contract": output_paths,
        "promotion_gates": [
            "regenerate_vlsat_full_validation_staging_and_raw_dump_under_full_validation_paths",
            "export_vlsat_full_validation_predictions_and_ground_truth_jsonl",
            "run_geometry_join_with_frozen_train_dev_calibrators",
            "run_vlsat_metrics_controls_gt_eval_bootstrap_ci_and_report",
            "decide_open3dsg_checkpoint_route_after_non_avg_retry_or_explicit_waiver",
            "regenerate_open3dsg_full_validation_payload_views_preprocess_features_raw_dump",
            "run_open3dsg_identity_adapter_geometry_metrics_bootstrap_failure_rows_caveats",
            "update_paper_tables_only_after_all_source_specific_caveats_are_known",
        ],
        "blockers": blockers,
        "warnings": warnings,
    }
    return contract, context_rows


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def command_markdown(contract: dict[str, Any]) -> str:
    paths = contract["output_path_contract"]
    selected_scans = paths["selected_scans"]
    vlsat_root = paths["vlsat_full_validation_root"]
    vlsat_runtime = paths["vlsat_runtime_root"]
    open_root = paths["open3dsg_full_validation_root"]
    open_runtime = paths["open3dsg_runtime_root"]
    return f"""# Full Official Validation Commands

Status: `{contract['status']}`

Run from the repository root. These commands are a frozen protocol template, not
completed metric evidence. Use `tmux` and timestamped logs for long jobs.

## Scope Contract

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm full_validation_scope_contract'
```

Expected files:

- `{paths['scope_contract_root']}/manifest.json`
- `{paths['scope_contract_root']}/scope_contract.json`
- `{paths['scope_contract_root']}/scans.txt`
- `{paths['scope_contract_root']}/contexts.jsonl`
- `{paths['scope_contract_root']}/commands.md`
- `{paths['scope_contract_root']}/report.md`

## VL-SAT Full Validation Route

The existing host-side H001 scripts can express the route, but paper promotion
requires a Dockerized VL-SAT runtime service or a documented Docker-compatible
background job with the same input/output contract.

```bash
python hypothesis/CAND-001/H001_geometry-grounded-verification/tools/stage_vlsat.py \\
  --selected-scans {selected_scans} \\
  --artifact-dir experiments/H001_geom_reliability/sources/vlsat/full_validation/stage \\
  --generated-subset-root experiments/H001_geom_reliability/sources/vlsat/full_validation/stage/generated/3DSSG_subset \\
  --staged-root {vlsat_runtime} \\
  --link-mode symlink \\
  --overwrite

python hypothesis/CAND-001/H001_geometry-grounded-verification/tools/run_vlsat_dump.py \\
  --staged-root {vlsat_runtime} \\
  --selected-scans {selected_scans} \\
  --output-dir {vlsat_root}/raw \\
  --baseline-run-id vlsat_full_official_validation_frozen_v1

python hypothesis/CAND-001/H001_geometry-grounded-verification/tools/export_predictions.py \\
  --selected-scans {selected_scans} \\
  --raw-dump-jsonl {vlsat_root}/raw/raw.jsonl \\
  --output-dir {vlsat_root}/adapter \\
  --split-name full_official_validation \\
  --baseline-run-id vlsat_full_official_validation_frozen_v1

python hypothesis/CAND-001/H001_geometry-grounded-verification/tools/join_predictions.py \\
  --predictions-jsonl {vlsat_root}/adapter/predictions.jsonl \\
  --model-json hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json \\
  --output-dir {vlsat_root}/geometry \\
  --selected-scans {selected_scans} \\
  --verification-policy point_subtype

python hypothesis/CAND-001/H001_geometry-grounded-verification/tools/evaluate_predictions.py \\
  --predictions-jsonl {vlsat_root}/adapter/predictions.jsonl \\
  --ground-truth-jsonl {vlsat_root}/adapter/ground_truth.jsonl \\
  --verification-jsonl {vlsat_root}/geometry/verification.jsonl \\
  --output-dir {vlsat_root}/metrics \\
  --rule-variants obb_only point_subtype point_subtype_no_soft_support \\
  --ablation-controls p_geom_valid_only distance_only family_specific_p_geom_valid shuffled_geometry wrong_pair_geometry \\
  --family-specific-model-json hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json

python hypothesis/CAND-001/H001_geometry-grounded-verification/tools/evaluate_gt_verifier.py \\
  --selected-scans {selected_scans} \\
  --ground-truth-jsonl {vlsat_root}/adapter/ground_truth.jsonl \\
  --model-json hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json \\
  --output-dir {vlsat_root}/gt_eval
```

## Open3DSG Full Validation Route

Use separate runtime/output paths. Do not overwrite the current H001
`377/388` averaged-BLIP artifacts.

```bash
sg docker -c 'env UID=$(id -u) GID=$(id -g) docker compose -f experiments/H001_geom_reliability/compose.yaml run --rm open3dsg_full_validation_payload'
```

Planned output root:

- `{open_root}/payload`
- `{open_root}/views`
- `{open_root}/preprocess`
- `{open_root}/features`
- `{open_root}/raw_dump`
- `{open_root}/raw_dump_identity`
- `{open_root}/adapter`
- `{open_root}/geometry`
- `{open_root}/metrics`
- `{open_root}/bootstrap_ci`
- `{open_root}/failure_rows`
- `{open_root}/paper_caveats`

Planned runtime root: `{open_runtime}`.

Checkpoint rule: use the selected non-avg checkpoint only if R1 completes and
checkpoint selection is refreshed before downstream evaluation; otherwise keep
the averaged-BLIP caveat.
"""


def report_markdown(contract: dict[str, Any]) -> str:
    full = contract["full_validation_scope"]
    ready = contract["local_readiness"]
    completed = contract["inputs"]["completed_hardened_ground_truth"]
    family_rows = [[family, full["family_counts"].get(family, 0)] for family in sorted(full["family_counts"])]
    h001_rows = [[family, full["h001_family_counts"].get(family, 0)] for family in PRIMARY_FAMILIES]
    readiness_rows = [
        ["raw 3RScan geometry", f"{ready['raw_3rscan_geometry']['ready_scans']}/{ready['raw_3rscan_geometry']['target_scans']} scans"],
        ["VL-SAT raw geometry", f"{ready['vlsat_raw_geometry']['ready_scans']}/{ready['vlsat_raw_geometry']['target_scans']} scans"],
        ["Open3DSG mesh/texture", f"{ready['open3dsg_mesh_texture']['ready_scans']}/{ready['open3dsg_mesh_texture']['target_scans']} scans"],
        ["Open3DSG sequence", f"{ready['open3dsg_sequence']['ready_scans']}/{ready['open3dsg_sequence']['target_scans']} scans"],
        ["existing VL-SAT hardened staged root", f"{ready['existing_vlsat_hardened_staged_root']['ready_scans']}/{ready['existing_vlsat_hardened_staged_root']['target_scans']} scans"],
        ["existing Open3DSG h001 runtime views", f"{ready['existing_open3dsg_h001_runtime']['view_ready_scans']}/{ready['existing_open3dsg_h001_runtime']['view_target_scans']} scans"],
        ["existing Open3DSG h001 runtime preprocess", f"{ready['existing_open3dsg_h001_runtime']['preprocess_ready_contexts']}/{ready['existing_open3dsg_h001_runtime']['preprocess_target_contexts']} contexts"],
        ["existing Open3DSG training_repro views", f"{ready['existing_open3dsg_training_repro']['view_ready_scans']}/{ready['existing_open3dsg_training_repro']['view_target_scans']} scans"],
        ["existing Open3DSG training_repro preprocess", f"{ready['existing_open3dsg_training_repro']['preprocess_ready_contexts']}/{ready['existing_open3dsg_training_repro']['preprocess_target_contexts']} contexts"],
    ]
    lines = [
        "# Full Official Validation Scope Contract",
        "",
        f"Status: `{contract['status']}`",
        f"Created at: `{contract['created_at']}`",
        "",
        "## Boundary",
        "",
        "- This is a protocol-freeze artifact, not metric evidence.",
        "- The current 127-scan results remain current evidence until full-validation artifacts are regenerated.",
        "- H001-Mini is hypothesis/feasibility evidence only.",
        "- Final method design, verifier policy, counterfactuals, and `p_geom_valid` calibration are train/train-dev-derived.",
        "",
        "## Scope",
        "",
        markdown_table(
            ["Item", "Count"],
            [
                ["completed hardened scans", completed.get("scans", 0)],
                ["completed hardened contexts", completed.get("contexts", 0)],
                ["completed hardened GT rows", completed.get("gt_rows", 0)],
                ["completed hardened H001-family GT rows", completed.get("h001_family_gt_rows", 0)],
                ["full validation scans", full["scans"]],
                ["full validation contexts", full["contexts"]],
                ["full validation GT-positive directed pairs", full["gt_positive_directed_pairs"]],
                ["full validation candidate directed pairs", full["candidate_directed_pairs"]],
                ["full validation GT rows", full["gt_rows"]],
                ["full validation H001-family GT rows", full["h001_family_gt_rows"]],
                ["expected VL-SAT prediction rows", full["expected_vlsat_prediction_rows_all_non_none_predicates"]],
            ],
        ),
        "",
        "## H001 Family Counts",
        "",
        markdown_table(["Family", "GT rows"], h001_rows),
        "",
        "## All Family Counts",
        "",
        markdown_table(["Family", "GT rows"], family_rows),
        "",
        "## Local Readiness",
        "",
        markdown_table(["Item", "Ready"], readiness_rows),
        "",
        "## Promotion Gates",
        "",
    ]
    lines.extend(f"- `{gate}`" for gate in contract["promotion_gates"])
    if contract["blockers"]:
        lines.extend(["", "## Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in contract["blockers"])
    if contract["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- `{warning}`" for warning in contract["warnings"])
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    dataset_root = resolve(repo_root, args.dataset_root)
    out = resolve(repo_root, args.out)
    relationships_validation = resolve(repo_root, args.relationships_validation)
    relationships_file = resolve(repo_root, args.relationships_file)
    hardened_ground_truth = resolve(repo_root, args.hardened_ground_truth)
    hardened_scans = resolve(repo_root, args.hardened_scans)
    mini_scans = resolve(repo_root, args.mini_scans)
    vlsat_hardened_root = resolve(repo_root, args.vlsat_hardened_root)
    open3dsg_h001_runtime_root = resolve(repo_root, args.open3dsg_h001_runtime_root)
    open3dsg_training_repro_root = resolve(repo_root, args.open3dsg_training_repro_root)

    required = [
        relationships_validation,
        relationships_file,
        hardened_ground_truth,
        hardened_scans,
        mini_scans,
    ]
    missing = [relpath(repo_root, path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing required full-validation contract inputs: " + ", ".join(missing))

    contract, context_rows = build_scope_contract(
        repo_root=repo_root,
        relationships_validation=relationships_validation,
        relationships_file=relationships_file,
        hardened_ground_truth=hardened_ground_truth,
        hardened_scans=hardened_scans,
        mini_scans=mini_scans,
        dataset_root=dataset_root,
        vlsat_hardened_root=vlsat_hardened_root,
        open3dsg_h001_runtime_root=open3dsg_h001_runtime_root,
        open3dsg_training_repro_root=open3dsg_training_repro_root,
        out=out,
    )

    scans = sorted({row["scan_id"] for row in context_rows})
    write_text(out / "scans.txt", "\n".join(scans) + "\n")
    write_jsonl(out / "contexts.jsonl", context_rows)
    write_json(out / "scope_contract.json", contract)
    write_json(out / "manifest.json", contract)
    write_text(out / "commands.md", command_markdown(contract))
    write_text(out / "report.md", report_markdown(contract))

    print(
        json.dumps(
            {
                "status": contract["status"],
                "out": relpath(repo_root, out),
                "scans": contract["full_validation_scope"]["scans"],
                "contexts": contract["full_validation_scope"]["contexts"],
                "gt_rows": contract["full_validation_scope"]["gt_rows"],
                "h001_family_gt_rows": contract["full_validation_scope"]["h001_family_gt_rows"],
                "blockers": contract["blockers"],
                "warnings": contract["warnings"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
