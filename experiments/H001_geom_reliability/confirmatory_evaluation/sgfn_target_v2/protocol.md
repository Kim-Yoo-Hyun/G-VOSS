# SGFN Confirmatory Target v2: Pre-Inference Split Erratum

Frozen at UTC: `2026-07-10T06:58:36.974999+00:00`  
Status: `target_v2_frozen_pre_checkpoint_audit_pre_inference`

## Erratum

Target v1 named `files/cvpr/validation_scans.txt` while also locking projection
into the existing 548 H001 evaluation subgraphs. A pre-inference identity audit
showed these two sets have zero overlap. The 548 H001 subgraphs contain
`157` unique scans and exactly equal the official SGFN
`files/cvpr/test_scans.txt` set (`157` / `157`),
whereas overlap with `validation_scans.txt` is `0`.

This v2 contract corrects only the source split name and scan-list input. It was
frozen after checkpoint bytes were downloaded but before the archive was opened
or audited, before model construction/inference, and before any SGFN score or
H001 metric existed. Target v1 remains preserved as the failed preflight record.

## Immutable target

- Source/model/checkpoint: unchanged (`sgfn_official_full_l160`).
- Source-native inference split: official `files/cvpr/test_scans.txt`.
- Projection target: the already frozen 548 H001 evaluation subgraphs.
- H001 exact-label denominator: 3,972 in-scope GT rows.
- Missing source edges: never synthesized; coverage reported explicitly.

## Locked analysis (unchanged from v1)

- Main: `semantic_score * p_geom_valid_family`.
- Comparators: semantic-only, pooled calibration, family geometry-only,
  rank-average fusion, Reciprocal Rank Fusion (`c=60`).
- Families: `support_contact`, `proximity`, `relative_vertical`.
- K: `{5,10,20,50,100}`; primary K=100.
- Bootstrap: 1,000 H001-subgraph resamples, seed `20260710`.
- Validity gate: paired delta V@100 95% CI upper bound `< 0`.
- Recall guardrail: paired delta R@100 95% CI lower bound `> -0.01`.

No checkpoint, score, family, K, fusion, denominator, or missing-edge policy may
be changed after this point. All results must be reported regardless of direction.
