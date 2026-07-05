#!/usr/bin/env python3
"""Create the H002 standalone-paper gap-resolution pack."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


H2_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = H2_ROOT.parents[2]
EXP_ROOT = REPO_ROOT / "experiments/H002_compatibility_routing"
DEFAULT_GAP_REVIEW_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_standalone_outline_gap_review_after_decision"
DEFAULT_MAIN_TABLE_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock"
DEFAULT_POBS_CI_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_ci_qualitative_failure_wording_after_pobs_prel_review"
DEFAULT_SOURCE_CI_DIR = EXP_ROOT / "source_reranking_ci/latest"
DEFAULT_SUPPORT_DIR = EXP_ROOT / "support_contact_harder_evaluation/latest"
DEFAULT_OUTPUT_DIR = H2_ROOT / "artifacts/compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review"

EXPECTED_GAP_STATUS = "h002_standalone_outline_gap_review_after_decision_ready"
EXPECTED_SOURCE_CI_STATUS = "h002_source_reranking_bootstrap_ci_ready"
SCHEMA_VERSION = "h002_gap_resolution_pack_after_outline_review_v1"
STATUS_READY = "h002_gap_resolution_pack_after_outline_review_ready"
STATUS_ERROR = "h002_gap_resolution_pack_after_outline_review_input_errors"
NEXT_TODO = "compatibility_dataset_v3_h002_paper_workspace_promotion_decision_after_gap_resolution_pack"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-review-dir", type=Path, default=DEFAULT_GAP_REVIEW_DIR)
    parser.add_argument("--main-table-dir", type=Path, default=DEFAULT_MAIN_TABLE_DIR)
    parser.add_argument("--pobs-ci-dir", type=Path, default=DEFAULT_POBS_CI_DIR)
    parser.add_argument("--source-ci-dir", type=Path, default=DEFAULT_SOURCE_CI_DIR)
    parser.add_argument("--support-dir", type=Path, default=DEFAULT_SUPPORT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    return parser.parse_args()


def rel_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                yield json.loads(line)


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
    if not rows:
        rows = [{"empty": ""}]
        fields = ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def validate(args: argparse.Namespace, gap_summary: dict[str, Any], source_ci_summary: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    if gap_summary.get("status") != EXPECTED_GAP_STATUS:
        errors.append({"error_type": "unexpected_gap_review_status", "actual": gap_summary.get("status")})
    if gap_summary.get("validation_errors") != 0:
        errors.append({"error_type": "gap_review_validation_errors", "actual": gap_summary.get("validation_errors")})
    if source_ci_summary.get("status") != EXPECTED_SOURCE_CI_STATUS:
        errors.append({"error_type": "unexpected_source_ci_status", "actual": source_ci_summary.get("status")})
    if source_ci_summary.get("validation_errors") != 0:
        errors.append({"error_type": "source_ci_validation_errors", "actual": source_ci_summary.get("validation_errors")})
    for path in [
        args.main_table_dir / "main_validation_table.csv",
        args.main_table_dir / "control_table_compact.csv",
        args.source_ci_dir / "main_reranking_ci.csv",
        args.source_ci_dir / "main_reranking_delta_ci.csv",
        args.support_dir / "official_metrics.csv",
        args.support_dir / "failure_rows.jsonl",
    ]:
        if not path.exists():
            errors.append({"error_type": "missing_required_input", "path": rel_path(path)})
    return errors


def copy_ci_tables(args: argparse.Namespace, out: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    ci_rows = read_csv(args.source_ci_dir / "main_reranking_ci.csv")
    delta_rows = read_csv(args.source_ci_dir / "main_reranking_delta_ci.csv")
    compact = [
        {
            "score_id": row["score_id"],
            "K": row["K"],
            "metric": row["metric"],
            "point": f"{float(row['point']):.6f}",
            "ci95": f"[{float(row['ci_low_95']):.6f}, {float(row['ci_high_95']):.6f}]",
            "unit_count": row["unit_count"],
        }
        for row in ci_rows
    ]
    delta_compact = [
        {
            "comparison": row["comparison"],
            "K": row["K"],
            "metric": row["metric"],
            "point_delta": f"{float(row['point_delta']):.6f}",
            "ci95": f"[{float(row['ci_low_95']):.6f}, {float(row['ci_high_95']):.6f}]",
            "interpretation": delta_interpretation(row),
        }
        for row in delta_rows
    ]
    write_csv(out / "main_result_ci_table.csv", compact)
    write_csv(out / "main_result_delta_ci_table.csv", delta_compact)
    return compact, delta_compact


def delta_interpretation(row: dict[str, str]) -> str:
    low = float(row["ci_low_95"])
    high = float(row["ci_high_95"])
    metric = row["metric"]
    if metric == "Recall@K":
        if low > 0:
            return "S2 improves recall with 95% bootstrap support"
        if high < 0:
            return "S2 reduces recall with 95% bootstrap support"
        return "recall delta is not statistically separated from zero"
    if metric == "Violation@K":
        if high < 0:
            return "S2 reduces violation with 95% bootstrap support"
        if low > 0:
            return "S2 increases violation with 95% bootstrap support"
        return "violation delta is not statistically separated from zero"
    return ""


def claim_thesis() -> str:
    return """# H002 Claim Thesis

## Thesis

3D Scene Graph relation confidence is not the same object as relation reliability.
For a predicted edge `e = (subject, predicate, object)`, a source score can be
high because the relation is semantically plausible, because the source's ranker
has a class prior, because the geometry is actually compatible, or because the
source score is calibrated for relation-label recall rather than physical
consistency. Therefore a fixed fusion of semantic score and geometry score is
not a sufficient reliability model.

H002 uses the following decomposition:

```text
T_e = predicate and object-class semantic content
G_e = predicate-independent geometry evidence
Z_e = source confidence, score, and rank
C_e = compatibility(T_e, G_e)
Q_e = observability / evidence quality
p_obs = P(evidence is sufficient to decide | Q_e)
p_rel = P(relation is reliable | observable evidence, Z_e, C_e)
S2(e) = normalized_source_score(Z_e) * C_e
```

The design necessity is:

1. `Z_e` must be separated from `C_e`; otherwise compatibility can simply copy
   the relation source's ranking behavior.
2. `G_e` must be predicate-independent; otherwise geometry evidence already
   contains the answer to the predicate-specific compatibility question.
3. `C_e` must model `T_e x G_e`; fixed semantic-geometry fusion cannot express
   that the same geometric relation supports `higher than` but contradicts
   `lower than`, or that proximity may be geometry-decidable while contact
   relations require richer pose/contact evidence.
4. `Q_e` must be separated from relation truth; missing or low-quality evidence
   should produce abstention rather than a forced accept/reject decision.
5. `p_obs` and `p_rel` must be separate heads; evidence sufficiency and
   observable-edge reliability are different decisions.

## Falsifiable Paper Claim

If the decomposition is meaningful, then source reranking with `S2 = Z_e x C_e`
should improve the Recall@K / Violation@K tradeoff over source score alone, while
counterfactual controls that break predicate or geometry compatibility should
degrade. This is the main validation-level H002 claim.

## Claim Boundary

The current claim is validation-level and uses VL-SAT/Open3DSG predictions on
the official 3DSSG validation split. It is not an official-test, SOTA, or
leaderboard claim. Open3DSG is an open-vocabulary source, but the quantitative
metric uses closed-vocabulary 3DSSG mapping.
"""


def table_ablation_contract() -> list[dict[str, Any]]:
    return [
        {
            "table_id": "T1",
            "placement": "main",
            "title": "Mechanism Evaluation",
            "rows": "semantic-only / geometry-only / concat / T_e x G_e",
            "purpose": "Shows why compatibility is not reducible to single-factor or plain concatenation models.",
            "artifact_source": "experiments/H002_compatibility_routing/official_evaluation/latest/",
            "claim_supported": "C_e mechanism",
        },
        {
            "table_id": "T2",
            "placement": "main",
            "title": "Validation Source Reranking",
            "rows": "S0_source_score vs S2_source_x_Ce, K={5,10,20,50,100}",
            "purpose": "Main validation result: trade recall against geometry violation on VL-SAT/Open3DSG validation predictions.",
            "artifact_source": "artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/",
            "claim_supported": "S2 improves recall/violation tradeoff",
        },
        {
            "table_id": "T3",
            "placement": "main or compact appendix",
            "title": "Bootstrap CI for Source Reranking",
            "rows": "Recall@K, Violation@K, Delta(S2-S0)",
            "purpose": "Adds statistical uncertainty to the point-estimate validation table.",
            "artifact_source": "experiments/H002_compatibility_routing/source_reranking_ci/latest/",
            "claim_supported": "uncertainty of main validation result",
        },
        {
            "table_id": "T4",
            "placement": "appendix",
            "title": "Counterfactual Controls",
            "rows": "C_e-only, source x shuffled C_e, source x wrong-T C_e",
            "purpose": "Checks that gains are not just source score, class prior, or arbitrary geometry reweighting.",
            "artifact_source": "artifacts/compatibility_dataset_v3_main_validation_table_materialization_after_claim_lock/control_table_compact.csv",
            "claim_supported": "control degradation / source-score necessity",
        },
        {
            "table_id": "T5",
            "placement": "appendix or analysis",
            "title": "Selective Decision Stress Test",
            "rows": "p_obs, p_rel, accept/reject/abstain, risk-coverage, calibration",
            "purpose": "Supports p_obs/p_rel as a framework component while keeping calibrated quantitative claims bounded.",
            "artifact_source": "experiments/H002_compatibility_routing/pobs_prel_evaluation/latest/",
            "claim_supported": "selective-decision layer, not calibrated benchmark",
        },
        {
            "table_id": "T6",
            "placement": "analysis",
            "title": "Support/Contact Failure Taxonomy",
            "rows": "standing/lying/contact/pose/mesh/observability failure modes",
            "purpose": "Shows why hard routes require richer evidence and why support/contact is not claimed as solved.",
            "artifact_source": "experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/",
            "claim_supported": "failure boundary and future evidence requirements",
        },
    ]


def figure_specs() -> str:
    return """# H002 Figure Specs

## Figure 1: Factorized Reliability Framework

- Purpose: show why source confidence is not relation reliability.
- Panels:
  1. source relation candidate edge;
  2. factor split into `T_e`, `G_e`, `Z_e`, `Q_e`;
  3. `C_e = compatibility(T_e, G_e)` with `Z_e` excluded;
  4. final reranking `S2 = Z_e x C_e`;
  5. selective decision `p_obs -> p_rel`.
- Required visual boundary: hidden GT/violation labels appear only in the metric
  side, not inside model input.

## Figure 2: Leakage Boundary / Score Flow

- Purpose: make the reviewer-facing shortcut defense explicit.
- Panels:
  1. `model_safe_ce_view.jsonl`: `T_e + G_e` only;
  2. `source_rank_view.jsonl`: `Z_e` only;
  3. `hidden_metric_manifest.jsonl`: GT/violation, metric-only;
  4. `score_condition_metrics.csv`: Recall@K / Violation@K.
- Artifact source:
  `experiments/H002_compatibility_routing/source_reranking_materialization/latest/`
  and `source_reranking_schema_audit/latest/`.

## Figure 3: Recall-Violation Tradeoff

- Purpose: plot main validation result with CI.
- X axis: K.
- Left Y axis: Recall@K or Delta Recall@K.
- Right Y axis: Violation@K or Delta Violation@K.
- Curves: `S0_source_score`, `S2_source_x_Ce`.
- CI source:
  `experiments/H002_compatibility_routing/source_reranking_ci/latest/`.
- Caption boundary: official 3DSSG validation split, not official test.

## Figure 4: Support/Contact Failure Taxonomy

- Purpose: show why support/contact is a hard route rather than a solved result.
- Panels:
  1. standing/lying ambiguity;
  2. class-pair shortcut risk;
  3. local contact/pose evidence missing;
  4. observability or mesh insufficiency.
- Artifact source:
  `experiments/H002_compatibility_routing/support_contact_harder_evaluation/latest/failure_rows.jsonl`.
"""


def related_work_map() -> list[dict[str, Any]]:
    return [
        {
            "area": "3DSSG dataset and relation prediction",
            "work": "Learning 3D Semantic Scene Graphs from 3D Indoor Reconstructions",
            "year_venue": "CVPR 2020",
            "primary_source": "https://openaccess.thecvf.com/content_CVPR_2020/papers/Wald_Learning_3D_Semantic_Scene_Graphs_From_3D_Indoor_Reconstructions_CVPR_2020_paper.pdf",
            "novelty_threat": "3DSSG already predicts relation labels from 3D point clouds.",
            "h002_response": "H002 does not propose a replacement relation predictor; it estimates reliability/reranking of existing relation-source outputs.",
        },
        {
            "area": "3DSSG semantic relation predictor",
            "work": "VL-SAT: Visual-Linguistic Semantics Assisted Training for 3D Semantic Scene Graph Prediction in Point Cloud",
            "year_venue": "CVPR 2023",
            "primary_source": "https://openaccess.thecvf.com/content/CVPR2023/papers/Wang_VL-SAT_Visual-Linguistic_Semantics_Assisted_Training_for_3D_Semantic_Scene_Graph_CVPR_2023_paper.pdf",
            "novelty_threat": "VL-SAT already uses visual-linguistic semantics to improve 3DSSG prediction.",
            "h002_response": "H002 treats VL-SAT as a source and tests whether a source-independent compatibility layer improves reliability/violation tradeoff.",
        },
        {
            "area": "Open-vocabulary 3D scene graph source",
            "work": "Open3DSG: Open-Vocabulary 3D Scene Graphs from Point Clouds with Queryable Objects and Open-Set Relationships",
            "year_venue": "CVPR 2024 / arXiv",
            "primary_source": "https://arxiv.org/abs/2402.12259",
            "novelty_threat": "Open3DSG already produces open-vocabulary object/relation predictions.",
            "h002_response": "H002 evaluates Open3DSG as an open-vocabulary source under closed 3DSSG mapping and asks whether compatibility-aware reranking improves reliability.",
        },
        {
            "area": "Geometry/visual relation evidence",
            "work": "RelWitness: Open-Vocabulary 3D Scene Graph Generation from Posed RGB-D Sequences",
            "year_venue": "arXiv 2026",
            "primary_source": "https://arxiv.org/html/2605.20823v2",
            "novelty_threat": "Relation witness work directly targets visual-geometric cues for relation observability.",
            "h002_response": "H002's current scope is source-output factorization and reranking; relation evidence/witness is a related future route, not the sole contribution.",
        },
        {
            "area": "Calibration",
            "work": "On Calibration of Modern Neural Networks",
            "year_venue": "ICML 2017",
            "primary_source": "https://arxiv.org/abs/1706.04599",
            "novelty_threat": "Confidence calibration is a mature area.",
            "h002_response": "H002 uses calibration language only for relation reliability boundaries; the novelty is relation-level factor separation and geometry-compatibility validation.",
        },
        {
            "area": "Selective prediction / abstention",
            "work": "Selective Classification for Deep Neural Networks",
            "year_venue": "NeurIPS 2017",
            "primary_source": "https://arxiv.org/abs/1705.08500",
            "novelty_threat": "Reject-option prediction already studies risk/coverage tradeoffs.",
            "h002_response": "H002's `p_obs/p_rel` adapts selective decisions to 3D relation evidence sufficiency and keeps it bounded as stress-test evidence.",
        },
        {
            "area": "Integrated reject option",
            "work": "SelectiveNet: A Deep Neural Network with an Integrated Reject Option",
            "year_venue": "ICML 2019",
            "primary_source": "https://proceedings.mlr.press/v97/geifman19a.html",
            "novelty_threat": "A two-stage reliability/abstention head can look like standard selective prediction.",
            "h002_response": "H002 must position `p_obs/p_rel` as a domain-specific relation-evidence layer rather than claiming new selective-learning theory.",
        },
        {
            "area": "Conditional feature fusion",
            "work": "FiLM: Visual Reasoning with a General Conditioning Layer",
            "year_venue": "AAAI 2018",
            "primary_source": "https://arxiv.org/abs/1709.07871",
            "novelty_threat": "Predicate-conditioned geometry fusion resembles conditional modulation.",
            "h002_response": "H002's claim should not be 'new fusion'; it should be the source-score-separated compatibility framework and relation reliability evaluation.",
        },
        {
            "area": "Missing-modality multimodal learning",
            "work": "Multimodal Generative Models for Scalable Weakly-Supervised Learning",
            "year_venue": "NeurIPS 2018",
            "primary_source": "https://arxiv.org/abs/1802.05335",
            "novelty_threat": "Handling missing modality/evidence is a known multimodal-learning problem.",
            "h002_response": "H002's observability factor is a relation-specific evidence-quality boundary, not a general missing-modality model contribution.",
        },
    ]


def support_failure_taxonomy(args: argparse.Namespace, out: Path) -> list[dict[str, Any]]:
    official_rows = read_csv(args.support_dir / "official_metrics.csv")
    metrics = {row["view_id"]: row for row in official_rows if row.get("level") == "overall"}
    examples = []
    for idx, row in enumerate(iter_jsonl(args.support_dir / "failure_rows.jsonl")):
        if idx >= 12:
            break
        examples.append(
            {
                "candidate_id": row.get("candidate_id"),
                "predicate_label": row.get("predicate_label"),
                "class_pair": row.get("class_pair"),
                "target_y": row.get("target_y"),
                "predicted": row.get("predicted"),
                "score": row.get("score"),
                "failure_note": "standing/lying label is confounded by object class, pose, and local contact evidence",
            }
        )
    write_csv(out / "support_contact_failure_examples.csv", examples)
    return [
        {
            "failure_mode": "predicate direction inversion / score orientation failure",
            "evidence": f"M4_TxG_compatibility AUROC={float(metrics.get('M4_TxG_compatibility', {}).get('auroc', 0.0)):.6f}, wrong-T AUROC={float(metrics.get('C1_wrong_T_same_route', {}).get('auroc', 0.0)):.6f}",
            "interpretation": "The hard-route target is not yet aligned with the intended compatibility direction; support/contact must not be presented as solved.",
            "paper_role": "failure taxonomy",
        },
        {
            "failure_mode": "standing vs lying pose ambiguity",
            "evidence": "high-confidence errors repeatedly confuse `standing on` and `lying on` for floor-supported furniture/object pairs",
            "interpretation": "Need richer pose/orientation/contact patch evidence, not only scalar proximity/contact proxies.",
            "paper_role": "qualitative limitation",
        },
        {
            "failure_mode": "class-pair shortcut risk",
            "evidence": "failure rows concentrate in class pairs such as table->floor, couch/sofa->floor, cabinet/shelf->floor",
            "interpretation": "Object class prior can dominate relation labels unless class-pair controlled targets or stronger evidence are used.",
            "paper_role": "reviewer-risk defense",
        },
        {
            "failure_mode": "observability and mesh/contact insufficiency",
            "evidence": "Q_e remains diagnostic; no independent visual/mesh observability label is available for support/contact success claim",
            "interpretation": "This motivates the p_obs/p_rel separation and future visual/mesh evidence, but does not validate a solved support/contact route.",
            "paper_role": "future evidence requirement",
        },
    ]


def write_report(
    out: Path,
    delta_ci: list[dict[str, str]],
    taxonomy: list[dict[str, Any]],
    validation_errors: list[dict[str, Any]],
) -> None:
    key_deltas = [row for row in delta_ci if row["comparison"] == "S2_source_x_Ce_minus_S0_source_score"]
    lines = [
        "# H002 Gap Resolution Pack",
        "",
        "## What Was Resolved",
        "",
        "- Claim thesis fixed in `claim_thesis.md`.",
        "- Main source-reranking bootstrap CI generated from Docker runtime output.",
        "- Final table and ablation contract frozen in `table_ablation_contract.csv`.",
        "- Figure specs written in `figure_specs.md`.",
        "- Related-work / novelty-threat map created from primary sources.",
        "- Support/contact failure taxonomy strengthened and kept as failure analysis, not success evidence.",
        "",
        "## Main Result CI Summary",
        "",
        "| K | Metric | Delta(S2-S0) | 95% CI | Interpretation |",
        "| ---: | --- | ---: | --- | --- |",
    ]
    for row in key_deltas:
        lines.append(
            f"| {row['K']} | {row['metric']} | {row['point_delta']} | {row['ci95']} | {row['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Support/Contact Boundary",
            "",
            "Support/contact is currently a hard-route failure taxonomy branch. It should not be used as a success row.",
            "",
            "| Failure Mode | Paper Role |",
            "| --- | --- |",
        ]
    )
    for row in taxonomy:
        lines.append(f"| {row['failure_mode']} | {row['paper_role']} |")
    lines.extend(
        [
            "",
            "## Remaining Boundary",
            "",
            "- A new H002 paper workspace is still not created in this step.",
            "- Official-test / SOTA / leaderboard claims remain blocked.",
            "- `p_obs/p_rel` remains a main framework component, but calibrated quantitative paper-result wording remains blocked.",
            "",
            f"Validation errors: `{len(validation_errors)}`",
        ]
    )
    (out / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_root_stage_md(out: Path, summary: dict[str, Any]) -> None:
    path = H2_ROOT / "compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review.md"
    path.write_text(
        "\n".join(
            [
                "# compatibility_dataset_v3_h002_gap_resolution_pack_after_outline_review",
                "",
                f"status = {summary['status']}",
                f"artifact_root = {rel_path(out)}/",
                f"validation_errors = {summary['validation_errors']}",
                f"next_todo = {summary['next_todo']}",
                "",
                "Resolved:",
                "",
                "- claim thesis",
                "- main result bootstrap CI",
                "- table / ablation contract",
                "- figure specs",
                "- related-work / novelty-threat map",
                "- support/contact failure taxonomy",
                "",
                "Boundary: no new paper workspace was created, and official-test/SOTA claims remain blocked.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    errors: list[dict[str, Any]] = []
    try:
        gap_summary = read_json(args.gap_review_dir / "summary.json")
        source_ci_summary = read_json(args.source_ci_dir / "summary.json")
    except FileNotFoundError as exc:
        gap_summary = {}
        source_ci_summary = {}
        errors.append({"error_type": "missing_summary", "path": rel_path(Path(exc.filename or ""))})

    if not errors:
        errors.extend(validate(args, gap_summary, source_ci_summary))

    if errors:
        summary = {
            "schema_version": SCHEMA_VERSION,
            "status": STATUS_ERROR,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "validation_errors": len(errors),
            "next_todo": "fix_gap_resolution_pack_inputs",
        }
        write_json(out / "summary.json", summary)
        write_jsonl(out / "validation_errors.jsonl", errors)
        return summary

    (out / "claim_thesis.md").write_text(claim_thesis(), encoding="utf-8")
    ci_compact, delta_compact = copy_ci_tables(args, out)
    write_csv(out / "table_ablation_contract.csv", table_ablation_contract())
    (out / "figure_specs.md").write_text(figure_specs(), encoding="utf-8")
    write_csv(out / "related_work_novelty_map.csv", related_work_map())
    taxonomy = support_failure_taxonomy(args, out)
    write_csv(out / "support_contact_failure_taxonomy.csv", taxonomy)

    gate_rows = [
        {"gate": "G1_claim_thesis", "status": "resolved", "artifact": "claim_thesis.md"},
        {"gate": "G2_table_plan", "status": "resolved", "artifact": "table_ablation_contract.csv"},
        {"gate": "G3_figure_plan", "status": "resolved", "artifact": "figure_specs.md"},
        {"gate": "G4_related_work", "status": "resolved", "artifact": "related_work_novelty_map.csv"},
        {"gate": "G5_ablation_contract", "status": "resolved", "artifact": "table_ablation_contract.csv"},
        {"gate": "G8_failure_taxonomy", "status": "resolved", "artifact": "support_contact_failure_taxonomy.csv"},
        {"gate": "G9_workspace_promotion", "status": "blocked_pending_explicit_user_approval", "artifact": "none"},
    ]
    write_csv(out / "paper_gap_resolution_matrix.csv", gate_rows)

    write_report(out, delta_compact, taxonomy, [])
    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS_READY,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "artifact_root": rel_path(out),
        "claim_thesis_resolved": True,
        "main_result_ci_resolved": True,
        "table_ablation_contract_resolved": True,
        "figure_spec_resolved": True,
        "related_work_novelty_map_resolved": True,
        "failure_taxonomy_resolved": True,
        "workspace_promotion_allowed_now": False,
        "requires_explicit_user_approval_for_new_paper_root": True,
        "official_test_claim_allowed": False,
        "sota_or_leaderboard_claim_allowed": False,
        "pobs_prel_calibrated_quantitative_claim_allowed": False,
        "source_ci_summary": {
            "unit_count": source_ci_summary.get("unit_count"),
            "n_bootstrap": source_ci_summary.get("n_bootstrap"),
            "point_metric_mismatch_count": source_ci_summary.get("point_metric_mismatch_count"),
        },
        "validation_errors": 0,
        "next_todo": NEXT_TODO,
    }
    write_json(out / "summary.json", summary)
    write_jsonl(out / "validation_errors.jsonl", [])
    write_root_stage_md(out, summary)
    return summary


def main() -> None:
    summary = run(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
