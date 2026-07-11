#!/usr/bin/env python3
"""Freeze H001 post-hoc provenance and prospective confirmatory protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "h001_confirmatory_protocol_v1"
CHRONOLOGY = [
    {
        "event": "family_calibrator_artifact_created",
        "date": "2026-05-06",
        "evidence": "model.json created_at and source_split=train_dev_calib",
    },
    {
        "event": "family_calibrator_first_committed",
        "date": "2026-06-23T20:12:53+09:00",
        "commit": "45dc45f857f8160edc3080b6fbcb77785d4dd73d",
    },
    {
        "event": "full_validation_source_metrics_generated",
        "date": "2026-06-23",
        "evidence": "both metrics_k_sweep/metrics.json created_at fields",
    },
    {
        "event": "family_condition_reframed_from_control_to_method_candidate",
        "date": "2026-06-24T14:09:45+09:00",
        "commit": "d8a07fa91641407daf6d6778dca658e3bc4794af",
        "evidence": "H001_v2 11_family_conditional_risk_result.md introduced after source results",
    },
    {
        "event": "family_conditional_risk_promoted_to_paper_main_score",
        "date": "2026-06-25T09:38:00+09:00",
        "commit": "d4999aaa6485814b0a05267304ad5e8efda46fb6",
        "evidence": "paper/TODO/result wording explicitly promoted the condition",
    },
    {
        "event": "independent_physical_validity_audit_protocol_frozen",
        "date": "2026-07-10",
        "evidence": "physical_validity_audit/frozen_v1 manifest; labels initially empty",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/H001_geom_reliability/confirmatory_evaluation/frozen_v1"),
    )
    return parser.parse_args()


def resolve(root: Path, path: Path) -> Path:
    return path if path.is_absolute() else root / path


def relpath(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path)


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
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def protocol_text(payload: dict[str, Any]) -> str:
    return f"""# H001 Prospective Confirmatory Evaluation Protocol

Frozen at UTC: `{payload['created_at_utc']}`  
Status: `{payload['status']}`

## Provenance verdict

The family calibrator itself predates the full-validation source metrics and was
fit only on `train_dev_calib` rows without semantic scores. However,
`family_conditional_risk` was interpreted as a method candidate on 2026-06-24
and promoted to the paper main score on 2026-06-25, after the 2026-06-23
VL-SAT/Open3DSG source results were available. Therefore the existing source
metric table is valid retrospective evidence but is not labeled confirmatory.
This distinction must remain explicit in the paper and supplement.

## Locked method and hypotheses

- Main score: `semantic_score * p_geom_valid_family`.
- Comparators: `semantic_only`, pooled calibration, geometry-only family score,
  fixed rank-average fusion, and fixed Reciprocal Rank Fusion (`c=60`).
- Families: `support_contact`, `proximity`, `relative_vertical`; no family may
  be removed after confirmatory results are observed.
- K grid: `{{5,10,20,50,100}}`; K=100 is primary, lower K values are secondary.
- Primary validity hypothesis: paired `Delta Human-V@100 = V_main - V_semantic < 0`.
- Recall guardrail for a new untouched source evaluation: lower 95% paired CI
  for `Delta R@100` must exceed `-0.01` absolute.
- Primary uncertainty unit: subgraph/scene cluster bootstrap, 1,000 fixed-seed
  resamples. Family-wise and low-K results are secondary and reported in full.

## Confirmatory tracks

### C1: independent human physical validity

This track is prospectively confirmatory for physical validity because the
490-item probability sample, blinding fields, estimands, and evaluation code
were frozen while both annotator sheets were empty. Two independent annotators
and blinded adjudication are required. This track does not retroactively make
the already-seen exact-label source metrics confirmatory.

### C2: untouched source metrics

This track remains blocked until one genuinely untouched evaluation target is
selected. Re-running or repartitioning the already inspected VL-SAT,
Open3DSG-recovery, or Qwen full-validation outputs is not a fresh confirmatory
test. The selected target must be recorded here before inference and before any
main-score/family/K changes.

## No-change rule

After this freeze, new fusion variants may be exploratory appendix analyses only.
They cannot replace the locked main score on the same confirmatory target. Any
protocol deviation, evidence replacement, label-policy change, or target reuse
must be logged and the affected result relabeled exploratory.
"""


def provenance_text(payload: dict[str, Any]) -> str:
    lines = [
        "# H001 Main-Score Provenance",
        "",
        f"Frozen at UTC: `{payload['created_at_utc']}`",
        "",
        "| date | event | evidence |",
        "| --- | --- | --- |",
    ]
    for row in payload["chronology"]:
        evidence = row.get("evidence", "")
        if row.get("commit"):
            evidence = f"commit `{row['commit']}`; {evidence}".rstrip("; ")
        lines.append(f"| {row['date']} | `{row['event']}` | {evidence} |")
    lines.extend(
        [
            "",
            "## Claim boundary",
            "",
            "- Fact: calibrator fitting preceded source metric generation and used train/dev calibration rows.",
            "- Fact: paper-main selection followed observation of source metric results.",
            "- Consequence: current VL-SAT/Open3DSG main-score comparisons are retrospective, not confirmatory.",
            "- Prospective evidence: the frozen independent human audit can confirm physical-validity reduction once independent labels are complete.",
            "- Still unresolved: a fresh exact-label source-metric confirmatory target requires a user choice.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    root = args.repo_root.resolve()
    out = resolve(root, args.out)
    paths = {
        "family_model": root / "archive/hypothesis_records/hypothesis/CAND-001/H001_geometry-grounded-verification/artifacts/calibration/p_geom_valid_family/model.json",
        "vlsat_metrics": root / "experiments/H001_geom_reliability/sources/vlsat/full_validation/metrics_k_sweep/metrics.json",
        "open3dsg_metrics": root / "experiments/H001_geom_reliability/sources/open3dsg/full_validation/recovery_relaxed_views_min2/metrics_k_sweep/metrics.json",
        "audit_manifest": root / "experiments/H001_geom_reliability/physical_validity_audit/frozen_v1/manifest.json",
        "reviewer_extension_manifest": root / "experiments/H001_geom_reliability/reviewer_extension_metrics/frozen_v1/manifest.json",
    }
    missing = [relpath(root, path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing_inputs:{missing}")
    family_model = read_json(paths["family_model"])
    vlsat_metrics = read_json(paths["vlsat_metrics"])
    open3dsg_metrics = read_json(paths["open3dsg_metrics"])
    audit_manifest = read_json(paths["audit_manifest"])
    extension_manifest = read_json(paths["reviewer_extension_manifest"])
    validations = {
        "family_model_source_split_train_dev_calib": family_model.get("source_split") == "train_dev_calib",
        "family_model_created_before_source_metrics": family_model.get("created_at", "9999") < vlsat_metrics.get("created_at", "0000") and family_model.get("created_at", "9999") < open3dsg_metrics.get("created_at", "0000"),
        "source_metrics_same_locked_date": vlsat_metrics.get("created_at") == "2026-06-23" and open3dsg_metrics.get("created_at") == "2026-06-23",
        "audit_labels_initially_empty_by_status": audit_manifest.get("status") == "frozen_awaiting_independent_human_labels",
        "reviewer_extension_ready": extension_manifest.get("status") == "ready_label_free_verifier_diagnostic",
    }
    status = (
        "human_confirmatory_open_source_metric_confirmatory_requires_target"
        if all(validations.values())
        else "blocked_provenance_validation_failed"
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "chronology": CHRONOLOGY,
        "provenance_verdict": {
            "calibrator_fit_before_source_results": True,
            "main_score_selected_after_source_results": True,
            "existing_source_metrics_classification": "retrospective_exploratory_evidence",
            "independent_human_audit_classification": "prospective_confirmatory_for_physical_validity_after_two_rater_completion",
            "fresh_source_metric_confirmatory_status": "requires_user_selected_untouched_target",
        },
        "locked_protocol": {
            "main_score": "family_conditional_risk",
            "formula": "semantic_score * p_geom_valid_family",
            "comparators": [
                "semantic_only",
                "pooled_calibration",
                "geometry_only_family",
                "rank_average_fusion",
                "reciprocal_rank_fusion_c60",
            ],
            "families": ["support_contact", "proximity", "relative_vertical"],
            "ks": [5, 10, 20, 50, 100],
            "primary_k": 100,
            "primary_human_hypothesis": "paired_delta_human_violation_at_100_main_minus_semantic_below_zero",
            "source_recall_guardrail": "paired_delta_recall_at_100_ci95_lower_above_minus_0.01",
            "bootstrap_unit": "subgraph_or_scene_cluster",
            "n_bootstrap": 1000,
        },
        "confirmatory_target": {
            "human_physical_validity": "physical_validity_audit/frozen_v1",
            "fresh_source_metric_target": None,
            "blocked_reuse_targets": [
                "VL-SAT full official validation already inspected",
                "Open3DSG recovery full validation already inspected",
                "Qwen full-validation outputs already inspected",
            ],
        },
        "validations": validations,
        "inputs": {
            name: {"path": relpath(root, path), "sha256": sha256_file(path)}
            for name, path in paths.items()
        },
        "user_decision_required": {
            "decision": "select whether and where to run a fresh exact-label source-metric confirmatory evaluation",
            "recommended": "new genuinely untouched semantic source or dataset target; keep existing source tables explicitly retrospective",
            "minimum_record_before_run": [
                "target dataset/source and checkpoint",
                "untouched split identity",
                "prediction export and denominator contract",
                "compute/time budget",
                "confirmation that main score/families/K remain frozen",
            ],
        },
    }
    out.mkdir(parents=True, exist_ok=True)
    write_json(out / "manifest.json", payload)
    (out / "protocol.md").write_text(protocol_text(payload), encoding="utf-8")
    (out / "provenance.md").write_text(provenance_text(payload), encoding="utf-8")
    print(json.dumps({"status": status, "out": relpath(root, out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
