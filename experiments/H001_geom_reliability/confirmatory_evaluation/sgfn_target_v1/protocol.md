# SGFN Untouched Confirmatory Source Contract

Frozen at UTC: `2026-07-10T06:53:00.164778+00:00`  
Status: `target_frozen_pre_checkpoint_pre_inference`  
Source id: `sgfn_official_full_l160`

## Selection rationale

SGFN is selected because the official 3DSSG framework exposes a 160-object,
26-relation `full_l160` configuration and a currently accessible official
checkpoint archive. It has not previously supplied H001 source metrics. SGFormer
was screened but not selected because its official repository does not contain
the documented config/checkpoint required for a reproducible untouched run.

This selection was frozen before downloading or opening the SGFN checkpoint and
before any SGFN prediction or H001 metric was produced.

## Immutable source provenance

- Official code: `https://github.com/ShunChengWu/3DSSG` at commit `4b783ecdc6caba1515b361f8a0643d0c2d568f52`.
- Source configuration: `configs/config_SGFN_full_l160.yaml`.
- Official checkpoint archive: `https://www.campar.in.tum.de/public_datasets/2023_cvpr_wusc/trained_models/SGFN_full_l20.zip`.
- Source setup: GT 3RScan instances, 160 object labels, 26 relation labels,
  multi-label relation prediction.
- Evaluation target: the official source validation scan list, mapped by scan
  and instance identity into the already frozen 548 H001 validation subgraphs.

The checkpoint archive must contain weights compatible with the full_l160
configuration. If it does not, this target becomes blocked; another checkpoint
or trained variant cannot be substituted under this protocol version.

## Adapter and denominator contract

1. Run SGFN once on its source-native full validation scans.
2. Export every available directed edge and every non-`none` relation score,
   preserving scan id and subject/object instance ids.
3. Project a full-scan edge score into each frozen H001 subgraph containing that
   directed object pair. Do not synthesize scores for source-missing edges.
4. Use the frozen H001 exact-label GT denominator of 3,972 in-scope relation
   rows. Report source scan coverage, subgraph coverage, pair coverage, and GT
   coverage separately.
5. Join geometry by the same identity key and run the locked main score without
   changing calibrator, family map, K, thresholds, or fusion definitions.

## Locked analysis

- Main: `semantic_score * p_geom_valid_family`.
- Comparators: semantic-only, pooled calibration, family geometry-only,
  rank-average fusion, and Reciprocal Rank Fusion with `c=60`.
- Families: `support_contact`, `proximity`, `relative_vertical`.
- K: `{5,10,20,50,100}`, primary K=100.
- Primary validity direction: paired delta V@100 below zero.
- Recall guardrail: paired delta R@100 95% CI lower bound above `-0.01`.
- Bootstrap: 1,000 subgraph resamples with fixed seed `20260710`.

All SGFN metrics are reported regardless of direction. Failure of the primary
gate does not permit score, family, K, checkpoint, or coverage-policy changes.

## Promotion boundary

The run is confirmatory for this source contract only if checkpoint audit,
source-native inference, adapter identity checks, geometry coverage reporting,
and paired CI all pass. It does not convert the earlier VL-SAT/Open3DSG/Qwen
tables into confirmatory evidence and does not authorize a broad SOTA claim.
