# SGFN Confirmatory Target v3: User-Authorized Checkpoint Erratum

Frozen at UTC: `2026-07-10T07:12:19.110148+00:00`  
Status: `target_v3_frozen_pre_correct_checkpoint_pre_inference`

## Authorization and correction

The user explicitly authorized `v3 pre-inference erratum` on 2026-07-10 KST.
Target v1 mistakenly linked `SGFN_full_l20.zip`; Docker audit established that
archive has 20-object/8-relation classifier heads and is incompatible with the
intended `config_SGFN_full_l160.yaml`. The official repository separately lists
`SGFN_full_l160.zip` for the 160-object/26-relation setup.

This correction was frozen before downloading the correct archive, before
model construction/inference, and before any SGFN prediction, geometry join, or
metric. It changes only the checkpoint URL. Target v2's split correction remains
in force: source-native inference uses official `files/cvpr/test_scans.txt`,
which exactly equals the 157 scans underlying the frozen 548 H001 subgraphs.

## Final immutable target

- Source id: `sgfn_official_full_l160`.
- Code: official 3DSSG repository at commit
  `4b783ecdc6caba1515b361f8a0643d0c2d568f52`.
- Configuration: `configs/config_SGFN_full_l160.yaml`.
- Checkpoint: `https://www.campar.in.tum.de/public_datasets/2023_cvpr_wusc/trained_models/SGFN_full_l160.zip`.
- Required compatibility: object head 160, relation head 26.
- Split: official `files/cvpr/test_scans.txt` (157 scans).
- Projection target: frozen 548 H001 subgraphs and 3,972 in-scope exact-label
  GT rows; source-missing edges are never synthesized.

## Locked analysis (unchanged)

- Main: `semantic_score * p_geom_valid_family`.
- Comparators: semantic-only, pooled calibration, family geometry-only,
  rank-average fusion, Reciprocal Rank Fusion (`c=60`).
- Families: `support_contact`, `proximity`, `relative_vertical`.
- K: `{5,10,20,50,100}`; primary K=100.
- Bootstrap: 1,000 H001-subgraph resamples, seed `20260710`.
- Validity gate: paired delta V@100 95% CI upper bound `< 0`.
- Recall guardrail: paired delta R@100 95% CI lower bound `> -0.01`.

No further checkpoint, split, score, family, K, fusion, denominator, or
missing-edge-policy change is permitted. All results must be reported.
